# Humidity correction and nudging: `miscmod_nl`

File: `miscmod_namelist`. Read by `miscini` in
{repo}`plasim/src/miscmod.f90`.

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `nfixer` | integer; switch | 1 | 1 enables the negative-humidity correction in `miscstep`; 0 disables it. |
| `nudge` | integer; selector | 0 | 0 leaves temperature nudging off; 1 reads the fourteen-slot `dtnudge` climatology and relaxes the uppermost model level; 2 reads `dfnudge` and applies the climatological temperature-tendency correction. |
| `tnudget` | real; sidereal-day multiples | 10 | Relaxation timescale for `nudge=1`. `miscini` multiplies by `TWOPI/ww`, equal to the configured sidereal day, then `mknudge` divides the temperature departure by this timescale. |
```

The historical spelling `TNUDGE` is not accepted. Its old “days” label
should not be read as a universal fixed 86400-second conversion: this
module uses the rotation-derived day. Nudging data are surface-loader
fields, not additional scalar namelist inputs. Source checks: `miscini`,
`miscstep`, `mknudge`, and the flux-correction tendency path.
