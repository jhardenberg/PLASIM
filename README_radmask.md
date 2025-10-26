# TOA solar radiation mask

This version allows to specify a lat-lon mask applied to the incident
shortwave radiation at the top of the atmosphere. It multiplies the solar
constant locally with a factor corresponding to the value in the mask.
Thus, a mask with ones everywhere does nothing. If the mask value is 0.8
at a given grid point, then the solar constant is reduced by 20% there.

## Compilation
Compile PlaSim-LSG as usual: in the `PLASIM` directory, execute

```
./configure.sh
./most.x -c
```

## Activating the mask
In `radmod_namelist`, add a new line

```
NRADMASK = 1
```

This switches the mask on. To switch it off, set `RADMASK = 0` (default).

## Specifying the mask
The mask should be specified as a space-separated `.txt` file called `radmask.txt`.

The mask has dimensions `NLON x NLAT` for the T21 resolution (`64 x 32`).
An example of this file is stored in `plasim/dat/radmask.txt`.

Your file `radmask.txt` must be placed in the `run` folder from which the model is run.

To change the mask in a new run, simply replace the file `radmask.txt` in the run
folder. No recompilation is needed.

## Questions
Contact [r.borner@uu.nl](mailto:r.borner@uu.nl).
