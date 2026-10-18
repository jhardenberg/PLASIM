# Column-oriented experiments and soundings

The old User's Guide chapter 7 describes a `COLUMN=1` macro in an `INP`
namelist. Today's `plasim_nl` does **not** accept `COLUMN` or `YMODE`.
Do not copy that old setup directly into a current run.

## Controls present in the current model

The accepted individual controls include:

| Control | Current location | Effect verified in code |
| --- | --- | --- |
| `nadv` | `plasim_nl` | Controls the advective/dynamical tendency branches in the spectral integration. |
| `nhordif` | `plasim_nl` | Controls horizontal diffusion; initialization also zeros the associated damping/restoration settings when it is zero. |
| `kick` | `plasim_nl` | Selects the initial perturbation; zero suppresses the noise initialization. |
| `zumin` | `fluxmod_nl` | Minimum wind speed in surface exchange, in m/s. |
| `sellon` | `plasim_nl` | One-based longitude index used for sounding fields. |

The old column recipe combined `KICK=0`, `NADV=0`, and `NHORDIF=0` at low
resolution. These remain individual model controls, but their availability
does not establish that every combination is an independently validated
single-column model. Select appropriate compiled resolution, forcing, and
boundary data and compare the actual tendency paths for your experiment.

T1 boundary datasets are included under `plasim/dat/T1`. MoSt's standard
T21/T31/T42 choices and the ordinary boundary-data workflow should not be
confused with a fully tested low-resolution column recipe. The historical
years-per-day performance claim is omitted: it is tied to an old machine
and is not a benchmark for today's implementation.

## Soundings in a full model run

Sounding displays also work as diagnostics of the full model; disabling
horizontal processes is not required merely to inspect a profile. The
`GUI_sounding.cfg` layout and `ISOCOL` picture type provide templates.
The model sends profiles at the selected `SELLON` longitude through
`GUCOL`, `GVCOL`, `GTCOL`, `DQCOL`, `DCCCOL`, and tendency arrays.

`SELLON` is a grid index in the namelist, not longitude in degrees. The GUI
exposes the corresponding degree value and converts it back to an index.
Temperature and humidity displays have explicit scaling in `guimod.f90`;
use the display's units rather than assuming they match raw output records.
See {doc}`gui` for configuration-file precedence.

## Sources checked

User's Guide chapter 7 compared with the current `plasim_nl` declaration,
`readnl`, `spectrala`/`spectrald`, `guigvcol`/`guigtcol`/`guid3dcol`,
`change_sellon`, and `GUI_sounding.cfg`. This is a source-based migration;
a standalone column experiment and interactive sounding controls were not
runtime-validated in this documentation change.
