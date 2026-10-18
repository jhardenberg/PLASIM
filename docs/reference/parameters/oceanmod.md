# Mixed-layer ocean: `oceanmod_nl`

File: `oceanmod_namelist`. Read by `oceanini` in
{repo}`plasim/src/oceanmod.f90`. `NLEV_OCE=1` is compiled in this source;
array inputs cannot create more layers. The real deep ocean has separate
{doc}`cpl` and {doc}`lsg` inputs.

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default before input | Meaning and interactions |
| --- | --- | --- | --- |
| `nocean` | integer; selector | 1 | Positive uses computed mixed-layer SST; 0 replaces SST by climatology and diagnoses the required correction. |
| `dlayer` | real array(NLEV_OCE); m | 50 | Layer thickness, used to initialize spatial mixed-layer depth. With this build supply one layer. |
| `vdiffkl` | real array(NLEV_OCE); m²/s | 1e−4 | Layer vertical diffusivities, thickness-weighted to interfaces when multiple layers are compiled. No internal vertical interface exists in the current one-layer setup. |
| `nhdiff` | integer; switch | 0 | Positive enables horizontal ocean heat diffusion in `mksst`. Different meaning from atmospheric `nhdiff`. |
| `hdiffk` | real array(NLEV_OCE); m²/s | 1e5 | Horizontal heat diffusivity, used globally when `nshdiff=0`, otherwise in the northern half. Requires `nhdiff>0`. |
| `hdiffk2` | real array(NLEV_OCE); m²/s | 1e4 | Southern-half diffusivity when `nshdiff` is nonzero. |
| `nshdiff` | integer; selector | 0 | 0 uses the same horizontal diffusivity everywhere; nonzero selects separate north/south values. |
| `nfluko` | integer; selector | 0 | Computed-ocean correction: 0 none; 1 reads/interpolates `yfsst`; 2 computes Newtonian correction from climatology and `taunc`. |
| `taunc` | real; fixed Earth days | 0 | SST relaxation timescale for Newtonian correction; converted with 86400 seconds/day. Supply positive input when selecting that mode. |
| `nlsg` | integer; coupling mode | 0 | 0 no LSG; 1 sends mixed-layer SST and receives deep-ocean heat feedback; 2 uses heat-flux coupling and replaces SST from LSG. Requires real coupled modules, compatible LSG data, and a 360-day calendar. |
| `naomod` | integer; atmospheric step interval | 320 | Interval passed to the LSG coupler. `clsgini` derives integer days as `naomod/atmospheric_ntspd`; select a positive whole number of days consistent with the calling schedule. At 32 steps/day the default is ten days. |
| `ntspd` | integer; steps/solar day | Inherited from ice interface | Copied from the caller before reading (declaration 32); determines `dtmix`. A local override does not change the atmospheric step counter or ocean call frequency. |
| `nperpetual_ocean` | integer; climatological day | 0 | Zero follows dated SST/correction interpolation; positive fixes its climatological day. |
| `newsurf` | integer; switch | 0 | On restart, 1 reads new SST climatology; otherwise uses restored climatology. |
| `nout` | integer; step-counter interval | Inherited steps/day | Declaration 0 is replaced before the namelist read. Controls ocean output/accumulator reset; use a positive interval and atmospheric `noutput` for the master output switch. |
| `ndiag` | integer; retained interval | 480 | Accepted, echoed, and broadcast. The current ocean source has no calculation/output branch using this interval; it does not replace `nout`. |
| `nprint` | integer; debug selector | 0 | Additional ocean diagnostics; several point printouts use value 2. |
| `nprhor` | integer; horizontal grid index | 0 | Point selected for associated debugging. |
| `nentropy` | integer; switch | 0 | Positive enables additional ocean entropy diagnostics. |
```

Input `VDIFFK` from the legacy appendix is now `VDIFFKL`; `vdiffk` is
the derived interface array. Flux correction, prescribed SST, and LSG
coupling are separate selections and can interact. Do not infer coupling
from the executable's filename alone. Source checks cover `oceanini`,
`oceanstep`, `mksst`, `hdiffo`, climatology/correction readers, and `clsgini`.
