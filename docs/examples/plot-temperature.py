"""Plot the first near-surface temperature field from converted PlaSim output."""

import sys

import matplotlib.pyplot as plt
import xarray as xr

input_file, output_file = sys.argv[1:]

with xr.open_dataset(input_file) as ds:
    temperature = ds["tas"].isel(time=0).squeeze(drop=True)
    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    temperature.plot.pcolormesh(
        ax=ax, x="lon", y="lat", cmap="viridis",
        cbar_kwargs={"label": f"2 m air temperature ({temperature.attrs['units']})"},
    )
    ax.set(
        title="2 m air temperature — first output time",
        xlabel="Longitude (degrees east)", ylabel="Latitude (degrees north)",
    )
    fig.savefig(output_file, dpi=150)
    plt.close(fig)
