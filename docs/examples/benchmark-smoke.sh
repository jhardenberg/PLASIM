#!/usr/bin/env bash
# Optional execution check; one sample per case is not a performance study.
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/plasim-benchmark-smoke.XXXXXX")
echo "Results and logs: $work/results"
python3 "$repo/benchmarks/run.py" --source "$repo" \
    --output "$work/results" --resolutions T21 --cases mixed lsg \
    --days 10 --repeats 1
python3 "$repo/benchmarks/compare.py" "$work/results"
