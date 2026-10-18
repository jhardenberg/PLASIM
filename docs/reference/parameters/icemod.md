# Sea ice: `icemod_nl`

File: `icemod_namelist`. Read by `iceini` in
{repo}`plasim/src/icemod.f90`. Its local timing/output settings are
separate from same-named atmosphere and ocean parameters.

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default before input | Meaning and interactions |
| --- | --- | --- | --- |
| `nice` | integer; selector | 1 | 1 evolves ice; 0 replaces thickness/compactness with climatological values and diagnoses the associated heat correction. |
| `nsnow` | integer; switch | 1 | 1 enables snow accumulation/melt on ice. |
| `ntskin` | integer; switch | 1 | 1 computes skin temperature; the alternate path uses the climatological setting. |
| `nfluko` | integer; selector | 0 | Prognostic-ice correction: 0 none; 1 interpolated prescribed `xflxice`; 2 calculated Newtonian correction using `taunc`. Climatological ice diagnoses correction separately. |
| `taunc` | real; fixed Earth days | 0 | Newtonian-correction timescale, converted by multiplication by 86400. Choose a positive timescale for the relaxation mode; zero is not an automatic physical tuning. |
| `xmind` | real; m | 0.1 | Minimum ice-thickness scale used by ice thickness/compactness calculations. |
| `xmaxd` | real; m | 9 | Maximum ice thickness; positive values activate the limit and its heat redistribution, negative values remove it. |
| `thicec` | real; fraction | 0.5 | Threshold used to turn initial compactness into the binary selected ice mask. Prognostic compactness remains a distinct diagnostic. |
| `ncpl_ice_ocean` | integer; step-counter interval | 1 | Ocean call when `mod(nstep,ncpl_ice_ocean)=0`; averages accumulated ice-to-ocean fluxes. The counter is the shared model step counter, not an independent count of ocean calls. Use positive intervals consistent with atmosphere–ice coupling. |
| `ntspd` | integer; steps/solar day | Inherited from atmosphere | Copied from the caller before the read (declaration 32). Determines local `xdt=solar_day/ntspd`; overriding it changes local physics timing, not the caller's actual call schedule. |
| `nperpetual_ice` | integer; climatological day | 0 | Zero follows dated interpolation; positive values select a fixed climatological day for ice forcing, independently of atmospheric `nperpetual`. |
| `newsurf` | integer; switch | 0 | On restart, 1 rereads ice/SST surface climatologies; otherwise saved climatologies are restored. |
| `nout` | integer; step-counter interval | Inherited steps/day | Declaration 0 is replaced by inherited `ntspd` before the read. Positive intervals control `iceout`; use the atmosphere's master `noutput` to disable output. |
| `nprint` | integer; debug selector | 0 | Extra printouts; several point diagnostics specifically use value 2. |
| `nprhor` | integer; horizontal grid index | 0 | Point selected for the associated debug printouts. |
| `nentropy` | integer; switch | 0 | Positive allocates/calculates ice entropy diagnostics and enables code 797 output. |
| `naout` | integer; array count | 0 | Allocates additional diagnostic fields and emits dynamic codes `750+ja`; requires compatible producing code, not just a positive count. |
```

Prescribed flux correction requires the corresponding fourteen-slot surface
field. The standard `NOUT` default is assigned **before** the namelist read;
an explicit zero is not subsequently repaired into a daily interval.
See {doc}`../output` for state versus interval-mean fields and budget signs.
Source checks: `iceini`, `icestep`, `iceget`, `mkice`, `mkicec`, correction
routines, output, and ice–ocean exchange.
