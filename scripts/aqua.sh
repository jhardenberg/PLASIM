DIR=/work/users/jost/plasim/src/scripts/
# Script to create boundary conditions for an acquaplanet
temp=$1
sic=$2
eq=$3
if [ "$eq" != "" ] &&  [ "$eq" != "0" ]; then
   CONT="-c 1 -e $eq"
else
   CONT=""
fi
$DIR/makesra 9.80665 129  > N032_surf_0129.sra # surface geopotential
$DIR/makesra -m 14 $temp 169  > N032_surf_0169.sra # surface temperature
$DIR/makesra $CONT 0. 172  > N032_surf_0172.sra # lsm
$DIR/makesra 2.0 173 > N032_surf_0173.sra # lsm DZ0LAND=2.0 in land_namelist
$DIR/makesra -m 14 0.17 174  > N032_surf_0174.sra # background albedo ALBLAND in land_namelist
$DIR/makesra 0.36 199  > N032_surf_0199.sra # forest cover
$DIR/makesra 2.0 200  > N032_surf_0200.sra # vegetation cover
$DIR/makesra -m 14 $sic 210  > N032_surf_0210.sra # sea-ice cover
$DIR/makesra -m 14 $sic 211  > N032_surf_0211.sra # sea-ice thickness
$DIR/makesra 0.28 212  > N032_surf_0212.sra # forest cover
$DIR/makesra 0.5 229  > N032_surf_0229.sra # bucket size WSMAX=0.5 in land_namelist
$DIR/makesra 0. 232  > N032_surf_0232.sra # lsm DZGLAC=-1 in land_namelist

