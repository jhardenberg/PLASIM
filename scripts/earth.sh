DIR=/work/users/jost/plasim/src/scripts/
# Script to initialize planet with specified surface temperatures and sea ice
temp=$1
sic=$2
# Script to create boundary conditions for an extremely hot or cold earth
$DIR/makesra -m 14 $temp 169  > N032_surf_0169.sra # surface temperature
$DIR/makesra -m 14 $sic 210  > N032_surf_0210.sra # sea-ice cover
$DIR/makesra -m 14 $sic 211  > N032_surf_0211.sra # sea-ice thickness

