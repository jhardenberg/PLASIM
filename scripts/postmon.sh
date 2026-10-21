#!/bin/bash
# Extracts main variables from PlaSim output and computes monthly means
# Set POSTDIR and INDIR, or SCRATCH and WORK for the historical layout.
set -e
set -o pipefail

VARS2D="ps psl tas tasmin tasmax ts uas vas evspsbl pr prc prl prsn mrros mrso tsl rsdt rsut rlut rsds rsus rlds rlus hfls hfss clt prw huss snd snm tauu tauv sit sic"
VARS3D="hus hur zg ta ua va wa wap cl clw"
VARSEXTRA="rst rls prl sndc stf mld"
VARSFX="orog lsm"
export PLEVS=${PLEVS:-"20,30,50,70,100,150,200,250,300,400,500,600,700,850,925,1000"}

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
BURNSH=${BURNSH:-"$script_dir/burn.sh"}

if [ $# -ne 3 ] || [[ ! $2 =~ ^[0-9]+$ || ! $3 =~ ^[0-9]+$ ]]; then
    echo "Usage: postmon.sh exp year1 year2" >&2
    exit 2
fi

exp=$1
y1=$((10#$2))
y2=$((10#$3))
fn=MOST
if (( y1 > y2 )); then
    echo "year1 must not exceed year2" >&2
    exit 2
fi

POSTDIR=${POSTDIR:-"${SCRATCH:?Set POSTDIR or SCRATCH}/plasim/exps/$exp/post"}
INDIR=${INDIR:-"${WORK:?Set INDIR or WORK}/plasim/plasim/exps/$exp"}
for program in "$BURNSH" cdo; do
    if ! command -v "$program" >/dev/null 2>&1; then
        echo "Required command not found: $program" >&2
        exit 127
    fi
done
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/plasim-postmon.XXXXXX")
trap 'rm -rf -- "$work_dir"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

mkdir -p "$POSTDIR/fx"
y1f=$(printf "%03d" "$y1")
for var in $VARSFX; do
    echo "Processing $var (fixed)"
    "$BURNSH" "$INDIR/$fn.$y1f" "$work_dir/extracted.nc" "$var"
    cdo -s seltimestep,1 "$work_dir/extracted.nc" "$POSTDIR/fx/${exp}_${var}.nc"
done

for var in $VARS2D $VARS3D $VARSEXTRA; do
    for (( y=y1; y<=y2; y++ )); do
        yf=$(printf "%03d" "$y")
        echo "Processing $var year $yf"
        mkdir -p "$POSTDIR/$yf"
        "$BURNSH" "$INDIR/$fn.$yf" "$work_dir/extracted.nc" "$var"
        cdo -s monmean "$work_dir/extracted.nc" "$POSTDIR/$yf/${exp}_${yf}_${var}.nc"
    done
done
