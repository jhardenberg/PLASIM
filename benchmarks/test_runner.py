"""Focused benchmark-tool checks; separate from model regression discovery."""
import contextlib
import copy
import io
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import compare
import run


class SchedulerTests(unittest.TestCase):
    def exercise(self, costs, budget, parallel):
        lock = threading.Lock()
        used, peak = 0, 0
        completed = []

        def job(index, cost):
            nonlocal used, peak
            with lock:
                used += cost
                peak = max(peak, used)
                self.assertLessEqual(used, budget)
            # Release the GIL so the next eligible job can start.
            time.sleep(0.04)
            with lock:
                used -= cost
                completed.append(index)

        jobs = [(cost, lambda i=i, c=cost: job(i, c)) for i, cost in enumerate(costs)]
        run.schedule(jobs, budget, parallel, run.ExecutionControl())
        self.assertCountEqual(completed, range(len(costs)))
        self.assertEqual(used, 0)
        return peak

    def test_weighted_budget_and_parallel_overlap(self):
        # Includes a waiting full-budget MPI case and smaller fitting jobs.
        self.assertEqual(self.exercise([2, 4, 1, 1, 2], 4, True), 4)

    def test_sequential_and_single_slot(self):
        self.assertEqual(self.exercise([2, 1, 2], 4, False), 2)
        self.assertEqual(self.exercise([1, 1, 1], 1, True), 1)

    def test_invalid_cost_and_empty_queue(self):
        control = run.ExecutionControl()
        with self.assertRaises(ValueError):
            run.schedule([(4, lambda: None)], 2, True, control)
        run.schedule([], 2, True, control)

    def test_failure_and_interrupt_stop_active_process(self):
        for error in (RuntimeError('deliberate failure'), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory() as directory:
                directory = Path(directory)
                control = run.ExecutionControl()
                started = threading.Event()
                original_start = control.start

                def start(*args, **kwargs):
                    process = original_start(*args, **kwargs)
                    started.set()
                    return process

                control.start = start

                def sleeper():
                    run.execute([sys.executable, '-c', 'import time; time.sleep(60)'],
                                directory, directory / 'sleep.log', os.environ.copy(), 30, control)

                def fail():
                    self.assertTrue(started.wait(5))
                    raise error

                begin = time.monotonic()
                with self.assertRaises(type(error)):
                    run.schedule([(1, sleeper), (1, fail)], 2, True, control)
                self.assertLess(time.monotonic() - begin, 10)
                self.assertTrue(control.cancelled)
                self.assertFalse(control.processes)
                with self.assertRaisesRegex(RuntimeError, 'cancelled'):
                    control.start([sys.executable, '-c', 'pass'])

    def test_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            with self.assertRaisesRegex(RuntimeError, 'timed out'):
                run.execute([sys.executable, '-c', 'import time; time.sleep(60)'],
                            directory, directory / 'timeout.log', os.environ.copy(), 1)

    def test_cli_rejects_invalid_budgets_before_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'unused'
            for options in (['--max-cores', '0'], ['--max-cores', '1', '--ranks', '2']):
                with self.subTest(options=options), patch.object(sys, 'argv',
                        ['run.py', '--output', str(output), *options]), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        run.arguments()
                    self.assertEqual(caught.exception.code, 2)
                    self.assertFalse(output.exists())


class ComparisonTests(unittest.TestCase):
    def report(self):
        return {'suite_sha256': 'runner', 'environment': {},
                'settings': dict(days=10, warmups=1, repeats=2, coupling_days=10,
                                 io='minimal', timers=True, fflags='-O3', cflags='-O3',
                                 precision_flags='-fdefault-real-8', parallel=True, max_cores=4),
                'cases': [dict(name='T21-mixed-p1', resolution='T21', case='mixed', ranks=1,
                               input_sha256='inputs', samples=[dict(warmup=False, wall_seconds=1,
                                                                   state={'fields': {}}, timers={})])]}

    def test_comparison_checks_policy_budget_and_parallel_matrix(self):
        baseline = self.report()
        for change in ('parallel', 'max_cores', 'repeats', 'matrix'):
            candidate = copy.deepcopy(baseline)
            if change == 'matrix':
                extra = copy.deepcopy(candidate['cases'][0])
                extra['name'] = 'T42-mixed-p1'
                candidate['cases'].append(extra)
            else:
                candidate['settings'][change] = {'parallel': False, 'max_cores': 8, 'repeats': 3}[change]
            with self.subTest(change=change), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, 'Incompatible benchmark conditions'):
                    compare.compare(baseline, candidate, False)
                rows = compare.compare(baseline, candidate, True)
                self.assertTrue(rows[0]['configuration_differences'])

    def test_parallel_summary_suppresses_mpi_scaling(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            compare.summary(self.report())
        self.assertIn('isolated MPI scaling is not reported', stream.getvalue())
        self.assertIn('n/a', stream.getvalue())


class MultiReportSummaryTests(unittest.TestCase):
    def report(self, ranks, seconds, parallel=False):
        report = ComparisonTests().report()
        report.update(schema_version=1, status='complete', source={'model_sha256': 'same-model'})
        report['settings'].update(parallel=parallel, max_cores=max(1, ranks))
        tool = lambda name: {'path': '/bin/' + name, 'version': name + ' version'}
        tools = {'make': tool('make'), 'cc': tool('cc')}
        tools['fc' if ranks == 1 else 'mpifc'] = {'path': '/bin/fortran', 'version': 'GNU Fortran 15'}
        if ranks > 1:
            tools['launcher'] = tool('mpiexec')
        report['environment'] = dict(machine={'hostname': 'same-host'}, tools=tools,
                                     launcher=[] if ranks == 1 else ['mpiexec'],
                                     thread_environment={'OMP_NUM_THREADS': '1'},
                                     runtime_environment={}, workspace_storage={'parent': '/tmp'})
        case = report['cases'][0]
        case.update(name=f'T21-mixed-p{ranks}', ranks=ranks)
        sample = case['samples'][0]
        sample['wall_seconds'] = seconds
        # A deliberately slow warmup must not affect ratios or sample counts.
        case['samples'].insert(0, dict(sample, warmup=True, wall_seconds=1000))
        return report

    def summarize(self, reports, allow_mismatch=False):
        with contextlib.redirect_stdout(io.StringIO()):
            return compare.summarize(reports, allow_mismatch)

    def test_split_serial_and_mpi_reports_produce_scaling(self):
        serial = self.report(1, 80)
        mpi = self.report(2, 40)
        mpi['cases'].extend(self.report(4, 25)['cases'] + self.report(8, 20)['cases'])
        rows = self.summarize([serial, mpi])
        self.assertEqual([r['ranks'] for r in rows], [1, 2, 4, 8])
        self.assertEqual([r['speedup'] for r in rows], [1, 2, 3.2, 4])
        self.assertEqual([r['efficiency_percent'] for r in rows], [100, 100, 80, 50])
        self.assertTrue(all(r['measured_samples'] == 1 for r in rows))
        self.assertEqual(rows[-1]['source_report'], 2)

    def test_concurrent_serial_baseline_suppresses_ratios(self):
        for reports in ([self.report(1, 80, True), self.report(2, 40)],
                        [self.report(1, 80), self.report(2, 40, True)]):
            with self.subTest(parallel=[r['settings']['parallel'] for r in reports]):
                rows = self.summarize(reports)
                self.assertIsNone(rows[1]['efficiency_percent'])
                self.assertIsNone(rows[1]['speedup'])

    def test_incompatible_conditions_and_inputs_rejected(self):
        serial = self.report(1, 80)
        for change in ('source', 'input', 'days', 'machine', 'compiler'):
            mpi = self.report(2, 40)
            if change == 'source':
                mpi['source']['model_sha256'] = 'different'
            elif change == 'input':
                mpi['cases'][0]['input_sha256'] = 'different'
            elif change == 'days':
                mpi['settings']['days'] += 1
            elif change == 'machine':
                mpi['environment']['machine']['hostname'] = 'different'
            else:
                mpi['environment']['tools']['mpifc']['version'] = 'different'
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError, 'Incompatible summary conditions'):
                    self.summarize([serial, mpi])
                rows = self.summarize([serial, mpi], True)
                self.assertTrue(all(r['speedup'] is None for r in rows))

    def test_checks_launcher_between_separate_mpi_files(self):
        reports = [self.report(1, 80), self.report(2, 40), self.report(4, 25)]
        reports[2]['environment']['launcher'].append('--bind-to=none')
        with self.assertRaisesRegex(ValueError, 'MPI compiler/launcher'):
            self.summarize(reports)

    def test_duplicates_are_not_silently_pooled(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.summarize([self.report(1, 80), self.report(1, 70)])

    def test_cli_multi_summary_export_and_existing_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            serial, mpi, output = [directory / name for name in ('serial.json', 'mpi.json', 'summary.json')]
            serial.write_text(compare.json.dumps(self.report(1, 80)))
            mpi.write_text(compare.json.dumps(self.report(2, 40)))
            args = ['compare.py', '--summary', str(serial), str(mpi), '--output', str(output)]
            with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
                compare.main()
            exported = compare.json.loads(output.read_text())
            self.assertEqual(exported['kind'], 'benchmark_summary')
            self.assertEqual(exported['cases'][1]['efficiency_percent'], 100)
            self.assertEqual(exported['reports'], [str(serial), str(mpi)])
            # Without --summary, two inputs still mean source-revision comparison.
            with patch.object(sys, 'argv', ['compare.py', str(serial), str(serial)]), \
                    contextlib.redirect_stdout(io.StringIO()):
                compare.main()


if __name__ == '__main__':
    unittest.main()
