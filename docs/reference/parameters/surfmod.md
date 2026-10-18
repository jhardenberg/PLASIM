# Surface initialization: `surfmod_nl`

File: `surfmod_namelist`. Read by `surfini` in
{repo}`plasim/src/surfmod.f90`. Boundary-file layout is described in
{doc}`../../user/boundary-data`.

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `nspinit` | integer; switch | 0 | If positive, initializes cold-start log surface pressure from spectral orography as `-orography/(gascon*tgr)`. Applied in the non-aquaplanet cold-start path. |
| `nsurf` | integer; legacy control | 1 | Read, echoed, and broadcast, but no active branch in the current surface module uses its value. Do not treat it as an enable/disable switch for surface physics. |
| `noromax` | integer; total wavenumber | `NTRU` | If below compiled truncation, removes spectral orography coefficients above this wavenumber at initialization. It does not change the atmospheric grid or compiled truncation. |
```

`OROSCALE` in the old surface table is not accepted by this namelist.
Aquaplanet initialization is controlled by `NAQUA` in {doc}`plasim` and
zeros land/orography on a cold start. Restart initialization follows its
saved-state path rather than rereading all cold-start fields.
