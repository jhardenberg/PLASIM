#!/bin/bash
exp=ex00
var=alb
year0=31
year1=60

BURN=/work/users/jost/plasim/planets/scripts/burn.sh
mkdir -p post
cd post
for (( y=$year0; y<=$year1; y++))
do
    yy=$(printf "%03d" $y)
    echo $yy
    $BURN ../$exp.$yy $var.${yy}.nc $var
done
rm -f $var.nc tempzonall.nc
cdo cat $var.???.nc $var.nc
for m in 3 4 5 6 7 8 9 10 11 12 1 2
do 
   cdo zonmean -selmon,$m -ymonmean $var.nc tempzon.nc
   cdo cat tempzon.nc tempzonall.nc
done
cdo outputtab,date,lat,value tempzonall.nc > temp.txt
cdo outputtab,date,lat,value -zonmean -timmean $var.nc > ${exp}_${var}_year.txt

awk 'BEGIN{n=0; m=1; dx=1./12.}{if(n==0) {print $0;n=n+1} else {print n*dx " " $2 " " $3; if(m==32){n=n+1;m=1}else {m=m+1}} }'< temp.txt > ${exp}_${var}_mean.txt
