#!/usr/bin/env bash
# Two-day serial T21/L10 Earth run; retain a fresh workspace for inspection.
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
for program in gfortran cc make; do
    if ! command -v "$program" >/dev/null 2>&1; then
        echo "Required program not found: $program" >&2
        exit 1
    fi
done

work=$(mktemp -d "${TMPDIR:-/tmp}/plasim-headless.XXXXXX")
echo "Workspace: $work"
mkdir "$work/build" "$work/run"
cp "$repo"/plasim/src/* "$work/build/"
cp "$work/build/resmod_def.f90" "$work/build/resmod.f90"
cp "$work/build/make_plasim" "$work/build/makefile"

(
    cd "$work/build"
    make -j1 plasim.x \
        MOST_CC=cc MOST_CC_OPTS=-O0 \
        MOST_F90=gfortran MOST_F90_OPTS=-O0 MOST_PREC=-fdefault-real-8 \
        MPIMOD=mpimod_stub GUIMOD=guimod_stub PUMAX=pumax_stub GUILIB= \
        PLAMOD=p_earth OCEAN=lsgmod_stub OCEANCOUP=cpl_stub
)

cp "$repo"/plasim/dat/T21/* "$work/run/"
for module in fluxmod icemod landmod miscmod oceanmod planet radmod rainmod seamod surfmod vegmod; do
    printf '&%s_nl\n/\n' "$module" > "$work/run/${module}_namelist"
done
cat > "$work/run/plasim_namelist" <<'EOF'
&plasim_nl
 n_start_year=2000, n_days_per_year=360,
 n_run_years=0, n_run_months=0, n_run_days=2, n_run_steps=0,
 mpstep=45, kick=0, ngui=0, seed=8*1
/
EOF
cat > "$work/run/planet_namelist" <<'EOF'
&planet_nl
 nfixorb=1
/
EOF

(
    cd "$work/run"
    "$work/build/plasim.x"
    if [ -f Abort_Message ]; then
        cat Abort_Message >&2
        exit 1
    fi
    for output in plasim_diag plasim_output plasim_status; do
        if [ ! -s "$output" ]; then
            echo "Missing or empty output: $output" >&2
            exit 1
        fi
    done
)
echo "Completed two-day run. Inspect $work/run/plasim_diag"
