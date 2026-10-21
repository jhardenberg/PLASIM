# Deep ocean: LSG `param`

File: `input`, group `param`. Read by `inipar` in
{repo}`lsg/src/lsgmod.f90`. This is the real coupled LSG implementation,
not a promise that older standalone LSG controls retain their historical
effect. The included grid has `IEN=72`, `JEN=76`, and `KEN=22`.

## Integration, forcing, and geometry

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default before input | Meaning and interactions |
| --- | --- | --- | --- |
| `nsmix` | integer; selector | 3 | Upper-ocean mixing/forcing selection, checked in range 1–3. The current step path calls `mixg` for 3; historical alternatives `mix`/`mixatt` are not a validated interchangeable setup here. |
| `nsve` | integer; selector | 2 | Barotropic-velocity solution method; `inipar` accepts only 2 in this implementation. |
| `nsflu` | integer; selector | 2 | Flux selection, checked in range 0–2. `readbou` assigns freshwater flux when nonzero; 1 also opens `heaflu`. The combination `nsmix=2,nsflu=1` prints an unsupported-selection message. |
| `nscoup` | integer; legacy selector | 1 | Reset from declaration 0 to 1 before input. Historical coupled/uncoupled selector; current `readbou` explicitly obtains PlaSim fields and file fields and blends them with `cplpar` factors. Zero does not produce a standalone run by itself. |
| `dt` | real(kind=8); s internally | 86400 declaration; overwritten | Accepted input is replaced after reading by `ndcoup*86400`; the coupling interval from PlaSim is authoritative. The old positive-days/negative-seconds comment does not describe the active coupled assignment. |
| `kiterm` | integer; subcycles/LSG step | 4; shipped file 8 | Advection–diffusion subcycling count, with substep `dt/kiterm`; use a positive count consistent with stability requirements. |
| `grad1` | real(kind=8); degrees | 5 | Grid-spacing parameter copied into `grad` and used by `inigr`. It does not recompile dimensions or remap supplied topography/restarts. |
| `phinor` | real(kind=8); degrees, historical | 93.75 | Accepted/echoed northern-latitude parameter, but the current source has no subsequent use of this variable in grid construction. |
| `du` | real(kind=8) array(KEN+1); m | 22-level list below | Vertical depth coordinates used to derive layer geometry, not a list of layer thicknesses. Must match compiled levels and compatible ocean state/topography. |
| `bblthick` | real(kind=8); m | 300 | Reference bottom-boundary-layer thickness. The BBL calculation caps cross-sectional area at `bblthick*dl(JEN/2)`, compared with local `layer_thickness*dl(j)`; the resulting local thickness cap depends on grid spacing. |
| `naqua` | integer; geometry switch | 0 | Nonzero selects alternative aquaplanet-related topography/strait branches. Does not automatically generate all compatible ocean datasets. |
| `exper` | character(2); retained identifier | `xy` | Accepted/echoed two-character experiment identifier; no subsequent active use appears in the current ocean source. |
```

For the included 22-level build, the default 23 depth values are:

```text
25, 75, 125, 175, 225, 275, 350, 450, 550, 650, 750, 850,
950, 1100, 1300, 1500, 1800, 2250, 2750, 3500, 4500, 5500, 6500
```

## Output, matrix refresh, and retained controls

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default before input | Meaning and interactions |
| --- | --- | --- | --- |
| `ntcont` | integer; LSG steps | 1 | Control-diagnostic interval in the ocean step routine; used as a modulo divisor, so must be positive. |
| `ntout` | integer; LSG steps | No initialized default; shipped file 3 | Service output interval (`outpostsrv`). Supply a positive value explicitly; do not rely on a compiler's value for an uninitialized module variable. |
| `ntback` | integer; LSG steps | 120; shipped file 360 | Interval for writing the matrix-recomputation switch `mat76.sw`. Despite its historical name, the active coupled path does not perform a full runtime backup at this interval. |
| `ntaver` | integer; legacy interval | 1 | Accepted averaging interval; the `aver` call is commented out in the current step path. Does not activate monthly averaging of output. |
| `ntsurf` | integer; retained interval | 1; shipped file 3 | Accepted/echoed setting with no subsequent active use in this ocean source. |
| `newst` | integer; legacy step count | 120 | Historical standalone run length. The current coupled model advances when PlaSim calls `lsgstep`; this input does not set PlaSim's stopping time. |
| `iyear` | integer; legacy stopping year | 10 | Local `inipar` input retained from standalone run control; not used to stop the current coupled invocation. |
| `idate` | integer; legacy stopping date | −1230 | Historical `-MMDD` stopping date; likewise not the coupled stopping control. |
| `ndiagfl` | integer; switch | 0 | 1 enables the extra diagnostic-field branch in ocean diagnostics. |
| `nprint` | integer; debug switch | 0 | Extra ocean debugging output. |
| `npri` | integer; i index | 1 | Selected longitude index for point diagnostics. |
| `nprj` | integer; j index | 1 | Selected latitude index for point diagnostics. |
| `nprk` | integer; level index | 1 | Selected vertical index for point diagnostics. |
```

Use positive divisors for active output/matrix intervals. Output records
and a matrix-refresh request are distinct from saving a restart at the end
of the atmospheric segment. Keep matching atmospheric/ocean restarts and
matrix provenance; see {doc}`../../user/restarts`.

## Vertical diffusion profile

`set_quick` uses `A(z)=astar+arange*atan(lambda*(z-zstar))`. Negative
sentinels choose a compiled-level-dependent preset, not zero diffusion.

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Declaration → KEN=22 preset | Meaning and interactions |
| --- | --- | --- | --- |
| `astar` | real(kind=8); m²/s | −1 → 0.8714e−4 | Diffusivity at reference depth. KEN=11 fallback is 1.80e−4. |
| `arange` | real(kind=8); m²/s | −1 → 0.2843e−4 | Amplitude multiplying the arctangent. KEN=11 fallback is 1.01e−4. |
| `zstar` | real(kind=8); m | −1 → 2500 | Reference depth. KEN=11 fallback is 3000. |
| `lambda` | real(kind=8); 1/m | −1 → 4.5e−3 | Depth-transition rate. KEN=11 fallback is 3.4e−3. |
```

Source checks cover declarations, `inipar`, `inigr`, `set_quick`, BBL,
`readbou`, and active step/output calls. The shipped `lsg/dat/input` changes
four settings as noted above; preserve the actual copied file with each run.
