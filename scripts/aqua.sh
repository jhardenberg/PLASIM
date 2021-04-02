# Script to create boundary conditions for an acquaplanet
./makesra 9.80665 129  > N032_surf_0129.sra # surface geopotential
./makesra -m 14 287.5 169  > N032_surf_0169.sra # surface temperature
./makesra 0. 172 1 > N032_surf_0172.sra # lsm
./makesra 2.0 173 1 > N032_surf_0173.sra # lsm DZ0LAND=2.0 in land_namelist
./makesra -m 14 0.17 174  > N032_surf_0174.sra # background albedo ALBLAND in land_namelist
#199 vegetation
#200 LAI ???
#212 Forest cover 1 (0.27)
./makesra -m 14 0. 210  > N032_surf_0210.sra # sea-ice cover
./makesra 0. 212 1 > N032_surf_0212.sra # forest cover
./makesra 0.5 229 1 > N032_surf_0229.sra # bucket size WSMAX=0.5 in land_namelist
#./makesra -1 232 1 > N032_surf_0232.sra # lsm DZGLAC=-1 in land_namelist

