# The simulation GUI

MoSt configures and builds an experiment. The **simulation GUI** displays
and controls a running model. They are different programs/interfaces:
`most.x -c` suppresses the MoSt window, while **Run with GUI** controls the
model's GUI build and `NGUI` setting.

Enable the simulation GUI through MoSt when you want interactive diagnostics
and have an available X11 display. It is optional for batch experiments.
The old guide's statement that every Unix/Linux system already has X11 is
not a current installation assumption: provide the headers/libraries for
the build and a working display for interactive use.

## Configuration files

MoSt copies `plasim/dat/GUI.cfg` to the run directory (or the LSG layout for
an LSG setup). The GUI reads `GUI.cfg`, then applies `GUI_last_used.cfg` if
present. The latter saves a run's window layout. Multi-instance layouts
use the corresponding suffixed names.

To make a saved layout the default for future preparations, preserve the
original `plasim/dat/GUI.cfg` and replace it with the saved layout. To
customize only one prepared experiment, edit that run's configuration files.
A saved `GUI_last_used.cfg` can override changes made only to `GUI.cfg`.

An individual window block looks like this:

```text
[Window 00]
Array:CSU
Plot:ISOCS
Palette:U
Title:Zonal Wind [m/s]
Geometry: 529 299 2 3
```

| Item | Meaning in the current reader |
| --- | --- |
| `Array:` | Name of a model field actually sent through the GUI interface. |
| `Plot:` | Rendering type, selected by its exact name. |
| `Palette:` | Named colour palette; `AUTO` selects the automatic palette. |
| `Title:` | Window title; use the correct quantity and display units. |
| `Geometry:` | Width, height, left, top in pixels. |
| `Projection:` | Projection selected from the GUI's supported projection names. |
| `Inactive:` | Saved geometry for a disabled window. |

The reader also handles scalar and parameter blocks. Use the checked-in
`GUI.cfg`, `GUI_LSG.cfg`, and `GUI_sounding.cfg` as templates rather than
inventing field names. Window configuration cannot create an array that
the model never sends.

## Fields and plot types

| Field name | Current interface use |
| --- | --- |
| `CSU`, `CSV`, `CST` | Zonal-mean wind/temperature cross sections. |
| `SPAN` | Surface-pressure spherical-harmonic display. |
| `GU`, `GV`, `GP` | Wind and surface-pressure fields. |
| `SCALAR` | Scalars used by time-series and table displays. |
| `GUCOL`, `GVCOL`, `GTCOL` | Wind/temperature profiles at the selected longitude. |
| `DQCOL`, `DCCCOL` | Humidity/cloud profile displays. |
| `DTDTCOL`, `DQDTCOL` | Temperature/humidity tendencies sent by today's model. |

Display scaling is part of the GUI interface. For example, `guigtcol`
subtracts `TMELT` from temperature, while `DQCOL` is multiplied by 1000.
Do not infer stored output units from a GUI label or displayed magnitude.

Current plot names include `ISOHOR` (horizontal), `ISOCS` (cross section),
`ISOHOV` (Hovmöller), `ISOTS` (time series), `ISOTAB` (table), `ISOSH`
(spectral amplitudes), `ISOLON` (longitude/height), `ISOCOL` (column history),
and the tracer/rotating/map types `ISOTRA`, `ISOROT`, `MAPHOR`, `MAPTRA`.
Current palette names include `AUTO`, `U`, `V`, `T`, `P`, `Q`, `MARST`,
`AMPLI`, `VEG`, `OCET`, `OCES`, `DCC`, and `DTDT`.

Plot interactions depend on picture type. Use the configuration and GUI
controls for the selected representation; the historical screenshots are
not a record of every current window or field. Interactive parameters in
`guistep_plasim` include CO₂, solar constant, selected longitude, and
synchronization settings. Record any interactive intervention with the
experiment rather than treating it as an unchanged namelist run.

The old guide's PUMA orography/mode-editing recipes are not instructions
for this PlaSim-only checkout. Use the boundary-data workflow for PlaSim.

## Sources checked

User's Guide chapter 4 and §7.2 compared with `ReadConfig`, `initgui`, and
the plot/palette registries in {repo}`plasim/src/pumax.c`,
{repo}`plasim/src/guimod.f90`, model GUI calls in `plasim.f90`, and the
checked-in layouts. This is a source-verified interface description;
interactive X11 operation was not exercised during this migration.
