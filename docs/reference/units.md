# Dimensions, constants, and terminology

The User's Guide's appendix A mixes constants, state variables, and symbols
used in derivations. For this practical manual, use the current code's
dimensions and planet presets; the separate scientific Reference Manual is
not being migrated.

| Name | Current definition/use |
| --- | --- |
| `NLAT`, `NLON` | Global atmospheric latitude/longitude counts; `NLON=2*NLAT`. |
| `NLEV` | Compiled atmospheric level count. |
| `NPRO` | Compiled atmospheric process count. |
| `NLPP` | Latitudes per process, `NLAT/NPRO`. |
| `NHOR` | Local horizontal points, `NLON*NLPP`. |
| `NUGP` | Global horizontal points, `NLON*NLAT`. |
| `NTRU` | Triangular spectral truncation, `(NLON-1)/3`. |
| `NRSP` | Real spectral coefficients, `(NTRU+1)*(NTRU+2)`. |
| `NCSP` | Complex spectral coefficient count, `NRSP/2`. |
| `NSPP`, `NESP` | Per-process spectral allocation and padded global allocation. |
| `NROOT`, `mypid` | Root rank (0) and current MPI rank. |

T21 therefore has `NLAT=32`, `NLON=64`, `NTRU=21`, and `NRSP=506`.
The spectral coefficient index is not a latitude/longitude coordinate.

Physical constants such as gravity, radius, dry gas constant, solar day,
and surface pressure are planet-dependent inputs; their current direct
Earth presets are in {doc}`../user/planets`. The old appendix's rounded
radius/gravity values should not replace the values saved with an experiment.
Other shared constants include `RV=461.51` J/(kg K) and `ACPV=1870`
J/(kg K) in `plasimmod.f90`; module-local ice/ocean constants can differ in
purpose and must not be substituted by name alone.

Common distinctions throughout this manual:

- **Solar day**, **sidereal day**, **fixed Earth day**, and **calendar day**
  are not universal synonyms in planetary configurations.
- **Sigma/model level** and **pressure level** are different vertical
  representations. burn7's requested `hPa` values are hectopascals, while
  some Service headers/metadata use pascals.
- **Flux**, **interval mean**, **accumulated total**, and **state** require
  separate interpretation; see {doc}`output`.
- **Source default**, **planet preset**, **MoSt value**, **surface field**,
  and **restart value** describe different stages of initialization.
- **Spectral output**, **Gaussian grid**, and **regular latitude grid** are
  different representations even when they describe the same physical field.

Source: dimension and constant definitions in
{repo}`plasim/src/plasimmod.f90`, planet initialization, and the output and
postprocessor interfaces linked from the surrounding reference chapters.
