DIR=/work/users/jost/plasim/src/scripts/
# Script to initialize planet with specified surface temperatures and sea ice

function help {
  echo "Initialize planet with specified surface temperatures and sea ice"
  echo "Usage: earth.sh [OPTIONS] temp sic"
  echo "   temp : average surface temperature"
  echo "   sic  : sea-ice cover (0 or 1)"
  echo ""
  echo "Options:"
  echo "  -g grid       grid (t21/t42, default t21)"
  echo "  -h            print this help"
  exit 1
}

grid="t21"
while getopts "g:h" OPTION; do
    case $OPTION in
    g) grid=$OPTARG ;;
    h) help ;;
    esac
done
shift $((OPTIND-1))

if [ $# -lt 2 ]; then
   help
fi

if [ "$grid" = "t42" ] || [ "$grid" = "T42" ]; then
   tres="N064"
else
   tres="N032"
fi

temp=$1
sic=$2
# Script to create boundary conditions for an extremely hot or cold earth
$DIR/makesra -g $grid -m 14 $temp 169 > ${tres}_surf_0169.sra # surface temperature
$DIR/makesra -g $grid -m 14 $sic 210 > ${tres}_surf_0210.sra # sea-ice cover
$DIR/makesra -g $grid -m 14 $sic 211 > ${tres}_surf_0211.sra # sea-ice thickness

