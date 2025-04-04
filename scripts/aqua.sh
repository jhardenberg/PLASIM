DIR=/work/users/jost/plasim/src/scripts/
# Script to create boundary conditions for an acquaplanet

function help {
  echo "Create boundary conditions for an acquaplanet"
  echo "Usage: aqua.sh [OPTIONS] temp sic eq"
  echo "   temp : average surface temperature"
  echo "   sic  : sea-ice cover (0 or 1)"
  echo "   eq   : equatorial continent (set to const) up to latitude lat"
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

temp=$1
sic=$2
eq=$3

if [ "$eq" != "" ] &&  [ "$eq" != "0" ]; then
   CONT="-c 1 -e $eq"
else
   CONT=""
fi

if [ "$grid" = "t42" ] || [ "$grid" = "T42" ]; then
   tres="N064"
else
   tres="N032"
fi

$DIR/makesra -g $grid 9.80665 129  > ${tres}_surf_0129.sra # surface geopotential
$DIR/makesra -g $grid -m 14 $temp 169  > ${tres}_surf_0169.sra # surface temperature
$DIR/makesra -g $grid $CONT 0. 172  > ${tres}_surf_0172.sra # lsm
$DIR/makesra -g $grid 2.0 173 > ${tres}_surf_0173.sra # lsm DZ0LAND=2.0 in land_namelist
$DIR/makesra -g $grid -m 14 0.17 174  > ${tres}_surf_0174.sra # background albedo ALBLAND in land_namelist
$DIR/makesra -g $grid 0.36 199  > ${tres}_surf_0199.sra # forest cover
$DIR/makesra -g $grid 2.0 200  > ${tres}_surf_0200.sra # vegetation cover
$DIR/makesra -g $grid -m 14 $sic 210  > ${tres}_surf_0210.sra # sea-ice cover
$DIR/makesra -g $grid -m 14 $sic 211  > ${tres}_surf_0211.sra # sea-ice thickness
$DIR/makesra -g $grid 0.28 212  > ${tres}_surf_0212.sra # forest cover
$DIR/makesra -g $grid 0.5 229  > ${tres}_surf_0229.sra # bucket size WSMAX=0.5 in land_namelist
$DIR/makesra -g $grid 0. 232  > ${tres}_surf_0232.sra # lsm DZGLAC=-1 in land_namelist

