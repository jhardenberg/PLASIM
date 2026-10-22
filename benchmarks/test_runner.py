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


class BenchmarkMatrixTests(unittest.TestCase):
    def test_default_matrix_and_classic_radiation(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            with patch.object(sys, 'argv', ['run.py', '--output', str(directory / 'out')]):
                args = run.arguments()
            self.assertEqual(args.resolutions, ['T21', 'T42'])
            self.assertEqual(args.cases, ['mixed', 'lsg'])
            self.assertEqual(args.ranks, [1])
            self.assertEqual(args.warmups, 0)
            for resolution in args.resolutions:
                for case in args.cases:
                    with self.subTest(resolution=resolution, case=case):
                        configs = run.prepare(args, directory / f'{resolution}-{case}', resolution, case)
                        self.assertRegex(configs['radmod_namelist'], r'\bnstartemp=0\b')
                        self.assertRegex(configs['plasim_namelist'],
                                         r'\bntspd=' + str({'T21': 32, 'T31': 48, 'T42': 72}[resolution]) + r'\b')
                        self.assertRegex(configs['oceanmod_namelist'],
                                         r'\bnlsg=' + ('1' if case == 'lsg' else '0') + r'\b')

    def test_t31_selection_inputs_and_coupling_cadence(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            for coupling_days in (1, 10):
                args = run.arguments(['--output', str(directory / 'out'),
                                      '--resolutions', 'T31', '--no-configure',
                                      '--coupling-days', str(coupling_days)])
                self.assertEqual(args.resolutions, ['T31'])
                for case in args.cases:
                    with self.subTest(coupling_days=coupling_days, case=case):
                        target = directory / f'{case}-{coupling_days}'
                        configs = run.prepare(args, target, 'T31', case)
                        mask = 'N048_surf_0172.sra'
                        self.assertEqual((target / mask).read_bytes(),
                                         (run.ROOT / 'plasim/dat/T31' / mask).read_bytes())
                        self.assertRegex(configs['radmod_namelist'], r'\bnstartemp=0\b')
                        if case == 'lsg':
                            self.assertRegex(configs['oceanmod_namelist'],
                                             rf'\bnaomod={48 * coupling_days}\b')
                        else:
                            self.assertRegex(configs['oceanmod_namelist'], r'\bnlsg=0\b')

    def test_t31_mpi_rank_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            argv = ['--output', str(Path(directory) / 'out'), '--resolutions', 'T31',
                    '--max-cores', '32', '--no-configure']
            args = run.arguments(argv + ['--ranks', '1', '2', '4', '8', '16'])
            self.assertEqual(args.ranks, [1, 2, 4, 8, 16])
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    run.arguments(argv + ['--ranks', '32'])
            self.assertEqual(caught.exception.code, 2)
            self.assertFalse((Path(directory) / 'out').exists())

    def test_spectral_cases_are_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'unused'
            for case in ('mixed-spectral', 'lsg-spectral'):
                with self.subTest(case=case), patch.object(sys, 'argv',
                        ['run.py', '--output', str(output), '--cases', case]), \
                        contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        run.arguments()
                    self.assertEqual(caught.exception.code, 2)
                    self.assertFalse(output.exists())

    def test_old_spectral_results_can_still_be_summarized(self):
        report = ComparisonTests().report()
        case = report['cases'][0]
        case.update(name='T21-mixed-spectral-p1', case='mixed-spectral')
        with contextlib.redirect_stdout(io.StringIO()):
            rows = compare.summary(report)
        self.assertEqual(rows[0]['name'], 'T21-mixed-spectral-p1')


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

    def test_interrupt_stops_active_process(self):
        with tempfile.TemporaryDirectory() as directory:
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

            def interrupt():
                self.assertTrue(started.wait(5))
                raise KeyboardInterrupt()

            begin = time.monotonic()
            with self.assertRaises(KeyboardInterrupt):
                run.schedule([(1, sleeper), (1, interrupt)], 2, True, control)
            self.assertLess(time.monotonic() - begin, 10)
            self.assertTrue(control.cancelled)
            self.assertFalse(control.processes)
            with self.assertRaisesRegex(RuntimeError, 'cancelled'):
                control.start([sys.executable, '-c', 'pass'])

    def test_job_failure_allows_remaining_jobs_to_finish(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            control = run.ExecutionControl()
            started = threading.Event()
            completed = []

            def active_job():
                started.set()
                run.execute([sys.executable, '-c', 'import time; time.sleep(0.1)'],
                            directory, directory / 'active.log', os.environ.copy(), 10, control)
                completed.append('active')

            def failing_job():
                self.assertTrue(started.wait(5))
                raise RuntimeError('Command timed out after 3600s')

            def pending_job():
                completed.append('pending')

            errors = run.schedule([(1, active_job), (1, failing_job), (2, pending_job)],
                                  2, True, control)
            self.assertEqual(len(errors), 1)
            self.assertIn('timed out', str(errors[0]))
            self.assertCountEqual(completed, ['active', 'pending'])
            self.assertFalse(control.cancelled)
            self.assertFalse(control.processes)

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

    def test_parallel_summary_warns_and_displays_mpi_scaling(self):
        report = self.report()
        mpi = copy.deepcopy(report['cases'][0])
        mpi.update(name='T21-mixed-p2', ranks=2)
        mpi['samples'][0]['wall_seconds'] = 0.5
        report['cases'].append(mpi)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            rows = compare.summary(report)
        self.assertIn('WARNING: concurrent benchmark cases', stream.getvalue())
        self.assertIn('2.000x', stream.getvalue())
        self.assertNotIn('n/a', stream.getvalue())
        self.assertEqual(rows[1]['efficiency_percent'], 100)
        self.assertTrue(rows[1]['concurrent_run'])
        self.assertTrue(rows[1]['concurrent_serial_baseline'])

    def test_partial_report_comparison_omits_unmeasured_cases(self):
        baseline = self.report()
        baseline['settings']['parallel'] = False
        second = copy.deepcopy(baseline['cases'][0])
        second['name'] = 'T42-mixed-p1'
        baseline['cases'].append(second)
        candidate = copy.deepcopy(baseline)
        candidate.update(status='partial', error='T42-mixed-p1: RuntimeError: Command timed out')
        candidate['cases'][1]['status'] = 'failed'
        candidate['cases'][1]['samples'] = [dict(warmup=True, wall_seconds=10, state={'fields': {}}, timers={})]
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            rows = compare.compare(baseline, candidate, False)
        self.assertEqual([r['case'] for r in rows], ['T21-mixed-p1'])
        self.assertIn('Skipping cases without measured samples: T42-mixed-p1', stream.getvalue())


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
                                     launcher=[] if ranks == 1 else ['mpiexec', '--bind-to', 'none'],
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

    def test_concurrent_runs_keep_ratios_and_warn(self):
        for serial_parallel, mpi_parallel in ((False, False), (True, False), (False, True), (True, True)):
            with self.subTest(serial_parallel=serial_parallel, mpi_parallel=mpi_parallel):
                reports = [self.report(1, 80, serial_parallel), self.report(2, 40, mpi_parallel)]
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    rows = compare.summarize(reports)
                self.assertEqual(rows[1]['speedup'], 2)
                self.assertEqual(rows[1]['efficiency_percent'], 100)
                self.assertEqual(rows[1]['concurrent_run'], mpi_parallel)
                self.assertEqual(rows[1]['concurrent_serial_baseline'], serial_parallel)
                self.assertEqual('WARNING: concurrent benchmark cases' in stream.getvalue(),
                                 serial_parallel or mpi_parallel)

    def test_missing_serial_baseline_keeps_scaling_unavailable(self):
        rows = self.summarize([self.report(2, 40)])
        self.assertIsNone(rows[0]['speedup'])
        self.assertIsNone(rows[0]['efficiency_percent'])

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
                self.assertEqual(rows[1]['speedup'], 2)
                self.assertEqual(rows[1]['efficiency_percent'], 100)
                self.assertTrue(rows[1]['configuration_differences'])

    def test_checks_launcher_between_separate_mpi_files(self):
        reports = [self.report(1, 80), self.report(2, 40), self.report(4, 25)]
        reports[2]['environment']['launcher'] = ['mpiexec', '--bind-to', 'core']
        with self.assertRaisesRegex(ValueError, 'MPI compiler/launcher'):
            self.summarize(reports)

    def test_duplicates_are_not_silently_pooled(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.summarize([self.report(1, 80), self.report(1, 70)])

    def test_cli_multi_summary_export_and_existing_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            serial, mpi, output = [directory / name for name in ('serial.json', 'mpi.json', 'summary.json')]
            serial.write_text(compare.json.dumps(self.report(1, 80, True)))
            mpi.write_text(compare.json.dumps(self.report(2, 40, True)))
            args = ['compare.py', '--summary', str(serial), str(mpi), '--output', str(output)]
            with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
                compare.main()
            exported = compare.json.loads(output.read_text())
            self.assertEqual(exported['kind'], 'benchmark_summary')
            self.assertEqual(exported['cases'][1]['efficiency_percent'], 100)
            self.assertTrue(exported['cases'][1]['concurrent_run'])
            self.assertTrue(exported['cases'][1]['concurrent_serial_baseline'])
            self.assertEqual(exported['reports'], [str(serial), str(mpi)])
            # Without --summary, two inputs with matching ranks still mean source-revision comparison.
            with patch.object(sys, 'argv', ['compare.py', str(serial), str(serial)]), \
                    contextlib.redirect_stdout(io.StringIO()):
                compare.main()

    def test_partial_or_failed_mpi_report_loads_and_summarizes(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            serial_path, mpi_path, empty_path = [directory / name for name in ('serial.json', 'mpi.json', 'empty.json')]
            serial = self.report(1, 80)
            mpi = self.report(2, 40)
            failed_case = copy.deepcopy(mpi['cases'][0])
            failed_case.update(name='T42-mixed-p2', resolution='T42', samples=[])
            warmup_only = copy.deepcopy(mpi['cases'][0])
            warmup_only.update(name='T42-lsg-p2', resolution='T42', case='lsg',
                               samples=[dict(warmup=True, wall_seconds=100, state={'fields': {}}, timers={})])
            mpi['cases'].extend([failed_case, warmup_only])
            mpi.update(status='failed', error='RuntimeError: Command timed out after 3600s')
            serial_path.write_text(compare.json.dumps(serial))
            mpi_path.write_text(compare.json.dumps(mpi))
            stream = io.StringIO()
            # Two disjoint-rank files without --summary automatically produce a combined summary.
            with patch.object(sys, 'argv', ['compare.py', str(serial_path), str(mpi_path)]), \
                    contextlib.redirect_stdout(stream):
                compare.main()
            self.assertIn('Skipping cases without measured samples: T42-mixed-p2, T42-lsg-p2', stream.getvalue())
            self.assertIn('2.000x', stream.getvalue())
            empty = copy.deepcopy(mpi)
            empty['cases'] = [failed_case, warmup_only]
            empty_path.write_text(compare.json.dumps(empty))
            with self.assertRaisesRegex(ValueError, 'No completed measured samples'):
                compare.load(empty_path)


class ContinuationTests(unittest.TestCase):
    def test_continue_skips_completed_runs_and_rejects_changed_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            output = directory / 'bench-out'
            executed = []
            built = []
            fail_once = {('T21-lsg-p1', 'sample-03'), ('T42-mixed-p1', 'warmup-01')}

            def fake_build(args, work, out, resolution, lsg, ranks, env):
                key = (resolution, lsg, ranks)
                built.append(key)
                exe = work / f'plasim-{resolution}-{lsg}-{ranks}.x'
                exe.write_text('binary')
                return exe, {'seconds': 0.1, 'sha256': 'exe-sha', 'name': f'{resolution}-{lsg}-{ranks}'}

            def fake_execute(command, cwd, log, env, timeout, control=None):
                case_name = log.parent.name
                label = log.name.removesuffix('.stdout.log')
                executed.append((case_name, label))
                log.write_text('ok\n')
                (cwd / 'plasim_diag').write_text('Total CPU time : 1.0\n')
                if (case_name, label) in fail_once:
                    fail_once.remove((case_name, label))
                    raise RuntimeError(f'Command timed out in {case_name}/{label}')
                return 2.0

            def fake_state(run_dir, resolution, days, lsg, coupling_days, diag):
                return {'nstep': 100, 'fields': {'st': {'count': 1, 'min': 280.0, 'max': 280.0,
                                                        'mean': 280.0, 'sha256': 'field-sha'}}}

            base_argv = ['run.py', '--output', str(output), '--work-dir', str(directory),
                         '--resolutions', 'T21', 'T42', '--cases', 'mixed', 'lsg',
                         '--ranks', '1', '--warmups', '1', '--repeats', '2', '--days', '10',
                         '--max-cores', '2']
            with patch.object(sys, 'argv', base_argv), \
                    patch.object(run, 'build', side_effect=fake_build), \
                    patch.object(run, 'execute', side_effect=fake_execute), \
                    patch.object(run, 'state_summary', side_effect=fake_state), \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, 'Command timed out'):
                    run.main()

            first_report = compare.json.loads((output / 'results.json').read_text())
            self.assertEqual(first_report['status'], 'partial')
            self.assertEqual([c['status'] for c in first_report['cases']], ['complete', 'failed', 'failed', 'complete'])
            self.assertEqual([len(c['samples']) for c in first_report['cases']], [3, 2, 0, 3])

            # Refuses to continue if any setting or case selection differs, leaving results.json untouched.
            before_bytes = (output / 'results.json').read_text()
            for extra in (['--days', '20'], ['--repeats', '3'], ['--fflags=-O2'],
                          ['--parallel'], ['--max-cores', '4'], ['--cases', 'mixed']):
                with self.subTest(extra=extra), \
                        patch.object(sys, 'argv', [*base_argv, *extra]), \
                        contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(RuntimeError, 'Cannot continue .* with different settings'):
                        run.main()
                    self.assertEqual((output / 'results.json').read_text(), before_bytes)

            # Continuing with identical settings skips completed cases and already-recorded samples.
            executed.clear()
            built.clear()
            stream = io.StringIO()
            with patch.object(sys, 'argv', base_argv), \
                    patch.object(run, 'build', side_effect=fake_build), \
                    patch.object(run, 'execute', side_effect=fake_execute), \
                    patch.object(run, 'state_summary', side_effect=fake_state), \
                    contextlib.redirect_stdout(stream):
                run.main()

            text = stream.getvalue()
            self.assertIn('Continuing existing benchmark report', text)
            self.assertIn('Skipping T21-mixed-p1: already complete (2 measured sample(s))', text)
            self.assertIn('Skipping T21-lsg-p1: warmup-01 already recorded', text)
            self.assertIn('Skipping T21-lsg-p1: sample-02 already recorded', text)
            self.assertEqual(executed, [
                ('T21-lsg-p1', 'sample-03'),
                ('T42-mixed-p1', 'warmup-01'),
                ('T42-mixed-p1', 'sample-02'),
                ('T42-mixed-p1', 'sample-03'),
            ])
            final_report = compare.json.loads((output / 'results.json').read_text())
            self.assertEqual(final_report['status'], 'complete')
            self.assertNotIn('error', final_report)
            self.assertEqual([c['status'] for c in final_report['cases']], ['complete', 'complete', 'complete', 'complete'])
            self.assertEqual([len(c['samples']) for c in final_report['cases']], [3, 3, 3, 3])

            # Re-running an already complete report skips all builds and runs.
            executed.clear()
            built.clear()
            with patch.object(sys, 'argv', base_argv), \
                    patch.object(run, 'build', side_effect=fake_build), \
                    patch.object(run, 'execute', side_effect=fake_execute), \
                    patch.object(run, 'state_summary', side_effect=fake_state), \
                    contextlib.redirect_stdout(io.StringIO()):
                run.main()
            self.assertEqual(built, [])
            self.assertEqual(executed, [])

            # Existing directory without results.json is still rejected.
            non_report_dir = directory / 'existing-without-json'
            non_report_dir.mkdir()
            with patch.object(sys, 'argv', [*base_argv[:2], str(non_report_dir), *base_argv[3:]]), \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(FileExistsError):
                    run.main()


class ConfigureOptionsTests(unittest.TestCase):
    def test_parse_make_vars(self):
        text = """
        # Comment line
        MOST_F90 = gfortran # trailing comment
        MOST_F90_OPTS = -O3 -funroll-loops
        MOST_CC = "cc"
        EMPTY =
        """
        parsed = run.parse_make_vars(text)
        self.assertEqual(parsed["MOST_F90"], "gfortran")
        self.assertEqual(parsed["MOST_F90_OPTS"], "-O3 -funroll-loops")
        self.assertEqual(parsed["MOST_CC"], "cc")
        self.assertEqual(parsed["EMPTY"], "")

    def test_load_configured_options(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "most_compiler").write_text(
                "MOST_F90 = gfortran\n"
                "MOST_F90_OPTS = -O3 -funroll-loops -march=native\n"
                "MOST_CC = clang\n"
                "MOST_CC_OPTS = -O3 -I /usr/X11/include -I/usr/local/include\n"
            )
            (directory / "most_compiler_mpi").write_text(
                "MOST_F90 = mpifort\n"
                "MOST_F90_OPTS = -O3 -funroll-loops\n"
            )
            opts = run.load_configured_options(directory)
            self.assertEqual(opts["fc"], "gfortran")
            self.assertEqual(opts["fflags"], "-O3 -funroll-loops -march=native")
            self.assertEqual(opts["cc"], "clang")
            self.assertEqual(opts["cflags"], "-O3")
            self.assertEqual(opts["mpifc"], "mpifort")
            self.assertEqual(opts["mpifflags"], "-O3 -funroll-loops")

    def test_probe_configure_runs_in_isolation(self):
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as work_dir:
            src = Path(src_dir)
            work = Path(work_dir)
            mock_configure = (
                "#!/bin/sh\n"
                "echo 'MOST_F90 = fake-f90' > most_compiler\n"
                "echo 'MOST_F90_OPTS = -O-test' >> most_compiler\n"
                "echo 'MOST_CC = fake-cc' >> most_compiler\n"
                "echo 'MOST_CC_OPTS = -O3' >> most_compiler\n"
                "echo 'MOST_F90 = fake-mpif90' > most_compiler_mpi\n"
                "echo 'MOST_F90_OPTS = -O-mpi' >> most_compiler_mpi\n"
            )
            (src / "configure.sh").write_text(mock_configure)
            (src / "makecheck").write_text("#!/bin/sh\n")

            opts = run.probe_configure(src, work)
            self.assertEqual(opts["fc"], "fake-f90")
            self.assertEqual(opts["fflags"], "-O-test")
            self.assertEqual(opts["cc"], "fake-cc")
            self.assertEqual(opts["mpifc"], "fake-mpif90")
            self.assertEqual(opts["mpifflags"], "-O-mpi")

            self.assertFalse((src / "most_compiler").exists())
            self.assertFalse((src / "most_compiler_mpi").exists())

    def test_arguments_auto_detection_and_inhibition(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "out"
            fake_opts = {
                "fc": "my-fc", "fflags": "-O-my-f",
                "cc": "my-cc", "cflags": "-O-my-c",
                "mpifc": "my-mpifc", "mpifflags": "-O-my-mpif",
            }
            with patch.object(run, "probe_configure", return_value=fake_opts) as mock_probe:
                args = run.arguments(["--output", str(out)])
                self.assertTrue(mock_probe.called)
                self.assertEqual(args.fc, "my-fc")
                self.assertEqual(args.fflags, "-O-my-f")
                self.assertEqual(args.cc, "my-cc")
                self.assertEqual(args.cflags, "-O-my-c")
                self.assertEqual(args.mpifc, "my-mpifc")
                self.assertEqual(args.mpifflags, "-O-my-mpif")

            intel_opts = {"fc": "ifx", "fflags": "-O3 -fp-model precise", "precision_flags": "-r8"}
            with patch.object(run, "probe_configure", return_value=intel_opts):
                args = run.arguments(["--output", str(out)])
                self.assertEqual(args.fc, "ifx")
                self.assertEqual(args.precision_flags, "-r8")

            with patch.object(run, "probe_configure", return_value={}), \
                    patch.object(run, "load_configured_options", return_value={}):
                args_intel = run.arguments(["--output", str(out), "--fc", "ifx", "--no-configure"])
                self.assertEqual(args_intel.precision_flags, "-r8")
                args_gnu = run.arguments(["--output", str(out), "--fc", "gfortran", "--no-configure"])
                self.assertEqual(args_gnu.precision_flags, "-fdefault-real-8")

            with patch.object(run, "probe_configure") as mock_probe, \
                    patch.object(run, "load_configured_options", return_value=fake_opts) as mock_load:
                args = run.arguments(["--output", str(out), "--no-configure"])
                self.assertFalse(mock_probe.called)
                self.assertTrue(mock_load.called)
                self.assertEqual(args.fc, "my-fc")

            with patch.object(run, "probe_configure", return_value=fake_opts):
                args = run.arguments([
                    "--output", str(out),
                    "--fc", "custom-f90",
                    "--fflags=-O1",
                    "--mpifflags=-O2",
                ])
                self.assertEqual(args.fc, "custom-f90")
                self.assertEqual(args.fflags, "-O1")
                self.assertEqual(args.mpifflags, "-O2")
                self.assertEqual(args.cc, "my-cc")

            with patch.object(run, "probe_configure") as mock_probe, \
                    patch.object(run, "load_configured_options") as mock_load:
                args = run.arguments([
                    "--output", str(out),
                    "--fc", "custom-f90", "--fflags=-O1",
                    "--cc", "custom-cc", "--cflags=-O0",
                    "--ranks", "1",
                ])
                self.assertFalse(mock_probe.called)
                self.assertFalse(mock_load.called)
                self.assertEqual(args.fc, "custom-f90")
                self.assertEqual(args.launcher, ["mpiexec", "--bind-to", "none"])

            args_custom_launcher = run.arguments(["--output", str(out), "--launcher", "mpiexec", "--no-configure"])
            self.assertEqual(args_custom_launcher.launcher, ["mpiexec"])

            args_single = run.arguments(["--output", str(out), "--single-precision", "--no-configure"])
            self.assertEqual(args_single.precision_flags, "")

            args_none = run.arguments(["--output", str(out), "--precision-flags", "none", "--no-configure"])
            self.assertEqual(args_none.precision_flags, "")

            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    run.arguments(["--output", str(out), "--single-precision", "--precision-flags", "-r8"])

    def test_mpifflags_continuation_and_comparison(self):
        baseline = ComparisonTests().report()
        baseline["settings"]["fflags"] = "-O3 -funroll-loops"
        baseline["settings"]["mpifflags"] = "-O3 -funroll-loops"

        current = copy.deepcopy(baseline)
        current["source"] = {"model_sha256": "dummy"}
        baseline["source"] = {"model_sha256": "dummy"}
        diffs = run.continuation_differences(baseline, current, ["T21-mixed-p1"])
        self.assertEqual(diffs, [])

        legacy_baseline = copy.deepcopy(baseline)
        del legacy_baseline["settings"]["mpifflags"]
        diffs_legacy = run.continuation_differences(legacy_baseline, current, ["T21-mixed-p1"])
        self.assertNotIn("setting mpifflags", str(diffs_legacy))

        candidate = copy.deepcopy(baseline)
        candidate["settings"]["mpifflags"] = "-O2"
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                compare.compare(baseline, candidate, allow_mismatch=False)
            rows = compare.compare(baseline, candidate, allow_mismatch=True)
        self.assertTrue(any("mpifflags" in d for d in rows[0]["configuration_differences"]))

    def test_compiler_family_detection_and_toolchain_validation(self):
        self.assertEqual(run.detect_compiler_family("ifx"), "intel")
        self.assertEqual(run.detect_compiler_family("/opt/intel/bin/mpiifort"), "intel")
        self.assertEqual(run.detect_compiler_family("gfortran"), "gnu")
        self.assertEqual(run.detect_compiler_family("/usr/bin/gfortran"), "gnu")
        self.assertEqual(run.detect_compiler_family(""), "unknown")

        # Intel MPI wrapper wrapping gfortran (both via -show and via --version banner)
        with patch.object(run, "capture") as mock_cap:
            mock_cap.side_effect = lambda cmd: (
                "gfortran -I/opt/intel/oneapi/mpi/include" if cmd[1] == "-show" else ""
            )
            self.assertEqual(run.detect_compiler_family("/usr/bin/mpifort"), "gnu")

        with patch.object(run, "capture") as mock_cap:
            def fake_capture(cmd):
                if cmd[1] in ("-show", "-showme:command", "-showme"):
                    raise RuntimeError("no show")
                return "Intel(R) MPI Library for Linux* OS\nGNU Fortran (Ubuntu 11.4.0) 11.4.0\n"
            mock_cap.side_effect = fake_capture
            self.assertEqual(run.detect_compiler_family("/usr/bin/mpifort"), "gnu")

        class MockArgs:
            ranks = [1, 2]
            fc = "ifx"
            mpifc = "gfortran"
            allow_mixed_compilers = False

        # Mismatched toolchain raises RuntimeError by default
        with self.assertRaises(RuntimeError) as ctx:
            run.validate_compiler_toolchain(MockArgs())
        self.assertIn("Inconsistent compiler toolchain detected", str(ctx.exception))

        # --allow-mixed-compilers permits it with warning
        MockArgs.allow_mixed_compilers = True
        with contextlib.redirect_stderr(io.StringIO()):
            run.validate_compiler_toolchain(MockArgs())

        # Matching toolchains pass without error
        MockArgs.allow_mixed_compilers = False
        MockArgs.mpifc = "mpiifort"
        run.validate_compiler_toolchain(MockArgs())

        # Rank 1 only skips check even if mpifc differs
        MockArgs.ranks = [1]
        MockArgs.mpifc = "gfortran"
        run.validate_compiler_toolchain(MockArgs())

    def test_format_compiler_info_and_summary_display(self):
        report = {
            "suite_sha256": "fake_suite",
            "source": {"model_sha256": "fake_model"},
            "environment": {
                "tools": {
                    "fc": {"path": "/opt/intel/bin/ifx"},
                    "mpifc": {"path": "/opt/intel/bin/mpiifort"},
                    "cc": {"path": "/usr/bin/gcc"},
                    "make": {"path": "/usr/bin/make"},
                    "launcher": {"path": "/usr/bin/mpiexec"},
                },
                "launcher": ["mpiexec", "--bind-to", "none"],
            },
            "settings": {
                "days": 120, "warmups": 0, "coupling_days": 10, "io": "minimal", "timers": True,
                "fflags": "-O3 -fp-model precise",
                "mpifflags": "-O3 -fp-model precise",
                "cflags": "-O3",
                "precision_flags": "-r8",
            },
            "cases": [
                {"name": "T21-mixed-p1", "resolution": "T21", "case": "mixed", "ranks": 1,
                 "input_sha256": "in1", "samples": [{"wall_seconds": 1.0, "warmup": False, "state": {"fields": {}}, "timers": {}}]},
                {"name": "T21-mixed-p2", "resolution": "T21", "case": "mixed", "ranks": 2,
                 "input_sha256": "in1", "samples": [{"wall_seconds": 0.5, "warmup": False, "state": {"fields": {}}, "timers": {}}]},
            ]
        }
        lines = compare.format_compiler_info(report)
        self.assertIn("Fortran: /opt/intel/bin/ifx (-O3 -fp-model precise -r8)", lines)
        self.assertIn("MPI Fortran: /opt/intel/bin/mpiifort (-O3 -fp-model precise -r8)", lines)
        self.assertIn("C compiler: /usr/bin/gcc (-O3)", lines)

        # In summarize()
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            compare.summarize([report])
        output = stream.getvalue()
        self.assertIn("Fortran: /opt/intel/bin/ifx (-O3 -fp-model precise -r8)", output)
        self.assertIn("MPI Fortran: /opt/intel/bin/mpiifort (-O3 -fp-model precise -r8)", output)

        # In compare()
        stream_cmp = io.StringIO()
        with contextlib.redirect_stdout(stream_cmp):
            compare.compare(report, report, allow_mismatch=False)
        output_cmp = stream_cmp.getvalue()
        self.assertIn("Compiler:", output_cmp)
        self.assertIn("Fortran: /opt/intel/bin/ifx (-O3 -fp-model precise -r8)", output_cmp)

        # Single precision display
        single_report = copy.deepcopy(report)
        single_report["settings"]["precision_flags"] = ""
        single_lines = compare.format_compiler_info(single_report)
        self.assertIn("Fortran: /opt/intel/bin/ifx (-O3 -fp-model precise [single precision])", single_lines)


if __name__ == '__main__':
    unittest.main()
