#!/usr/bin/env python3
"""Derive an LSG-consistent atmospheric land-sea mask (Code 172 .sra) for PlaSim.

Adapts PlaSim's default fractional/binarized surface land-sea mask
(Nnnn_surf_0172.sra) to ensure topological and numerical consistency with the
LSG ocean model bathymetry (topogr) and grid when running coupled simulations.

Automated derivation (default):
  1. Binarizes the atmospheric mask at 0.5.
  2. Closes uncoupled atmospheric ocean cells (kmiss_a -> 0): cells where LSG
     has zero ocean depth (e.g. Baltic Sea, Red Sea, Caspian Sea, Hudson Bay,
     Ross/Weddell shelves) are converted to land.
  3. Enforces isthmus closures: closes open seaways (e.g. Panama) where LSG has
     a continuous land barrier.
  4. Opens essential strait/channel vector points (kmiss_v -> 0): opens cells at
     the Strait of Gibraltar and northern Greenland margin so that wind stress
     directly forces ocean circulation without requiring artificial extrapolation.
  5. Leaves remaining coastal ocean scalar points to standard coupler
     extrapolation (cfill), preserving natural atmospheric continental outlines.

Requires Python 3 standard library only (no external dependencies).
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path


def legendre_gauss_latitudes(n: int) -> tuple[list[float], list[float]]:
    """Compute Gaussian latitudes (from North to South) and Gauss weights."""
    roots: list[float] = []
    weights: list[float] = []
    for i in range(1, n + 1):
        x = math.cos(math.pi * (i - 0.25) / (n + 0.5))
        for _ in range(100):
            p0, p1 = 1.0, x
            for j in range(2, n + 1):
                p0, p1 = p1, ((2 * j - 1) * x * p1 - (j - 1) * p0) / j
            pp = n * (p0 - x * p1) / (1.0 - x * x)
            dx = p1 / pp
            x -= dx
            if abs(dx) < 1e-15:
                break
        w = 2.0 * (1.0 - x * x) / (n * p0) ** 2
        roots.append(x)
        weights.append(w)
    return roots, weights


def build_plasim_grid(nxa: int, nya: int):
    """Construct PlaSim Gaussian grid coordinates and bounding boundaries."""
    roots, weights = legendre_gauss_latitudes(nya)
    zpi = 2.0 * math.asin(1.0)
    zdxa = 2.0 * zpi / nxa

    xa = [[zdxa * i for _ in range(nya)] for i in range(nxa)]
    ya = [[math.asin(roots[j]) for j in range(nya)] for _ in range(nxa)]

    xa1 = [[0.0 for _ in range(nya)] for _ in range(nxa)]
    xa2 = [[0.0 for _ in range(nya)] for _ in range(nxa)]
    for i in range(1, nxa):
        for j in range(nya):
            xa1[i][j] = 0.5 * (xa[i][j] + xa[i - 1][j])
    for j in range(nya):
        xa1[0][j] = xa1[1][j] - zdxa

    for i in range(nxa - 1):
        for j in range(nya):
            xa2[i][j] = 0.5 * (xa[i][j] + xa[i + 1][j])
    for j in range(nya):
        xa2[nxa - 1][j] = xa2[nxa - 2][j] + zdxa

    sum_w = sum(weights)
    zgw = [2.0 * w / sum_w for w in weights]

    ya1 = [[0.0 for _ in range(nya)] for _ in range(nxa)]
    ya2 = [[0.0 for _ in range(nya)] for _ in range(nxa)]

    zsinm = math.sin(zpi * 0.5)
    for i in range(nxa):
        ya1[i][0] = math.asin(zsinm)

    for j in range(1, nya):
        zsin = zsinm - zgw[j - 1]
        zsin = max(-1.0, min(1.0, zsin))
        val = math.asin(zsin)
        for i in range(nxa):
            ya1[i][j] = val
            ya2[i][j - 1] = val
        zsinm = zsin
    for i in range(nxa):
        ya2[i][nya - 1] = -zpi * 0.5

    agw = [[0.0 for _ in range(nya)] for _ in range(nxa)]
    for j in range(nya):
        for i in range(nxa):
            agw[i][j] = zdxa * abs(math.sin(ya1[i][j]) - math.sin(ya2[i][j]))

    return xa, ya, xa1, xa2, ya1, ya2, agw


def cmklonlate(nlon: int = 72, nlat: int = 72):
    """Compute geographic longitudes and latitudes for LSG Arakawa E-grid."""
    delta = 360.0 / nlon
    pi = 2.0 * math.asin(1.0)

    y = [[0.0 for _ in range(nlat)] for _ in range(nlon)]
    for j in range(nlat):
        jf = j + 1
        yval = 90.0 / nlat - 180.0 * (jf - nlat / 2.0) / nlat
        for i in range(nlon):
            y[i][j] = yval

    rlonlimit = 180.0 - delta / 100.0
    x = [[0.0 for _ in range(nlat)] for _ in range(nlon)]
    for j in range(nlat):
        jf = j + 1
        for i in range(nlon):
            i_f = i + 1
            xval = (((i_f - (jf / 2.0)) / (nlon / 2.0)) * 180.0) - delta
            if xval > rlonlimit:
                xval = -(360.0 - xval)
            if xval < -rlonlimit:
                xval = -xval
            x[i][j] = xval

    for j in range(nlat):
        for i in range(nlon):
            x[i][j] = x[i][j] * pi / 180.0
            y[i][j] = y[i][j] * pi / 180.0
    return x, y


def build_lsg_grid(nxo: int = 72, nyo: int = 72):
    """Construct LSG ocean grid coordinates, vector shifts, and boundaries."""
    pi = 2.0 * math.asin(1.0)
    xos, yo = cmklonlate(nxo, nyo)
    xov = [[xos[i][j] + pi / nxo for j in range(nyo)] for i in range(nxo)]

    for j in range(nyo):
        for i in range(nxo):
            if xos[i][j] < 0.0:
                xos[i][j] += 2.0 * pi
            if xov[i][j] < 0.0:
                xov[i][j] += 2.0 * pi

    zdxo = 2.0 * pi / nxo
    xos1 = [[xos[i][j] - 0.5 * zdxo for j in range(nyo)] for i in range(nxo)]
    xos2 = [[xos[i][j] + 0.5 * zdxo for j in range(nyo)] for i in range(nxo)]
    xov1 = [[xov[i][j] - 0.5 * zdxo for j in range(nyo)] for i in range(nxo)]
    xov2 = [[xov[i][j] + 0.5 * zdxo for j in range(nyo)] for i in range(nxo)]

    zdyo = pi / nyo
    yo1 = [[yo[i][j] - zdyo * 0.5 for j in range(nyo)] for i in range(nxo)]
    yo2 = [[yo[i][j] + zdyo * 0.5 for j in range(nyo)] for i in range(nxo)]

    ogw = [[0.0 for _ in range(nyo)] for _ in range(nxo)]
    for j in range(nyo):
        for i in range(nxo):
            ogw[i][j] = zdxo * abs(math.sin(yo1[i][j]) - math.sin(yo2[i][j]))

    return xos, yo, xov, xos1, xos2, xov1, xov2, yo1, yo2, ogw


def read_lsg_topogr(filename: Path | str):
    """Read LSG topogr file and compute scalar (oslms) and vector (oslmv) wet masks."""
    with open(filename, encoding="ascii") as f:
        lines = [line.strip("\n") for line in f]

    depth_vals: list[float] = []
    for line in lines[5:]:
        for k in range(0, len(line), 8):
            s = line[k : k + 8].strip()
            if s:
                depth_vals.append(float(s))

    ien, jen = 72, 76
    depth = [[0.0 for _ in range(jen)] for _ in range(ien)]
    idx = 0
    for j in range(jen):
        for i in range(ien):
            depth[i][j] = depth_vals[idx]
            idx += 1

    for j in range(jen):
        for i in range(ien):
            if j < 3 or j >= jen - 2:
                depth[i][j] = 0.0

    depp = [[0.0 for _ in range(jen)] for _ in range(ien)]
    for j in range(2, jen - 2):
        for i in range(ien):
            il = i - 1 if i > 0 else ien - 1
            d_ij = depth[i][j]
            d_ilj = depth[il][j]
            d_iljm1 = depth[il][j - 1]
            d_ijp1 = depth[i][j + 1]
            if d_ij > 0 or d_ilj > 0 or d_iljm1 > 0 or d_ijp1 > 0:
                tmp = max(d_ij, d_ilj, d_iljm1, d_ijp1)
            else:
                tmp = min(d_ij, d_ilj, d_iljm1, d_ijp1)
            if tmp < 0:
                tmp = 0.0
            depp[i][j] = tmp

    # Extract active rows j=3..74 (0-indexed 2..73) for 72x72 interior
    oslms = [[1.0 if depp[i][j] > 0 else 0.0 for j in range(2, 74)] for i in range(ien)]
    oslmv = [[1.0 if depth[i][j] > 0 else 0.0 for j in range(2, 74)] for i in range(ien)]
    return oslms, oslmv


def read_sra(filename: Path | str) -> tuple[list[int], list[list[float]], int, int]:
    """Read formatted PlaSim .sra file and return header, 2D array, nxa, nya."""
    with open(filename, encoding="ascii") as f:
        lines = f.readlines()
    header = [int(x) for x in lines[0].split()]
    nxa, nya = header[4], header[5]

    vals: list[float] = []
    for line in lines[1:]:
        vals.extend([float(x) for x in line.split()])

    if len(vals) != nxa * nya:
        raise ValueError(
            f"Expected {nxa * nya} data points in {filename}, found {len(vals)}"
        )

    # Stored row-major in file: latitude row j, then longitude i
    arr = [[0.0 for _ in range(nya)] for _ in range(nxa)]
    for j in range(nya):
        for i in range(nxa):
            arr[i][j] = vals[j * nxa + i]
    return header, arr, nxa, nya


def write_sra(filename: Path | str, header: list[int], arr: list[list[float]], nxa: int, nya: int) -> None:
    """Write 2D field into formatted Service .sra file matching PlaSim/LSG convention."""
    with open(filename, "w", encoding="ascii") as f:
        f.write(
            f"{header[0]:10d}{header[1]:10d}{header[2]:10d}{header[3]:10d}"
            f"{nxa:10d}{nya:10d}{header[6]:10d}{header[7]:10d}\n"
        )
        row_vals: list[float] = []
        for j in range(nya):
            for i in range(nxa):
                row_vals.append(arr[i][j])
        for k in range(0, len(row_vals), 4):
            chunk = row_vals[k : k + 4]
            line = "  " + "  ".join(f"{x:14.6E}" for x in chunk) + "\n"
            f.write(line)


def cinter(fi, slmi, slmo, xi1, xi2, yi1, yi2, xo1, xo2, yo1, yo2, nxi: int, nyo_dim: int, nyi: int, nxo_dim: int):
    """Area-weighted interpolation matching cinter in plasim/src/cpl.f90."""
    pi = math.pi
    zerr = -999.0
    kmiss = 0
    miss_points: list[tuple[int, int]] = []
    fo = [[0.0 for _ in range(nyo_dim)] for _ in range(nxo_dim)]

    for jo in range(nyo_dim):
        for io in range(nxo_dim):
            zgw = 0.0
            zf = 0.0
            y1_o = min(yo1[io][jo], yo2[io][jo])
            y2_o = max(yo1[io][jo], yo2[io][jo])

            for ji in range(nyi):
                y1_i = min(yi1[0][ji], yi2[0][ji])
                y2_i = max(yi1[0][ji], yi2[0][ji])

                if not (y1_o <= y2_i and y2_o >= y1_i):
                    continue

                lat_int = abs(math.sin(min(y2_o, y2_i)) - math.sin(max(y1_o, y1_i)))
                if lat_int <= 0:
                    continue

                for ii in range(nxi):
                    if slmi[ii][ji] <= 0:
                        continue

                    xol = xo1[io][jo]
                    xor = xo2[io][jo]
                    xil = xi1[ii][ji]
                    xir = xi2[ii][ji]

                    if abs(xol - xil) > pi:
                        if xol > xil:
                            xor -= 2 * pi
                            xol -= 2 * pi
                        else:
                            xir -= 2 * pi
                            xil -= 2 * pi

                    ox1 = max(xol, xil)
                    ox2 = min(xor, xir)
                    if ox2 > ox1:
                        w = (ox2 - ox1) * lat_int
                        zf += w * fi[ii][ji]
                        zgw += w

            if zgw > 0:
                fo[io][jo] = zf / zgw
            else:
                if slmo[io][jo] > 0.5:
                    kmiss += 1
                    miss_points.append((io, jo))
                fo[io][jo] = 0.0
    return fo, kmiss, miss_points


def evaluate_coupling(mask: list[list[float]], oslms, oslmv, xa1, xa2, ya1, ya2, xos1, xos2, xov1, xov2, yo1, yo2, nxa: int, nya: int):
    """Compute coupler diagnostic counts kmiss_a, kmiss_v, kmiss_s."""
    aslm = [[1.0 - mask[i][j] for j in range(nya)] for i in range(nxa)]
    zduma = [[1.0] * nya for _ in range(nxa)]
    zdumo = [[1.0] * 72 for _ in range(72)]

    zslmaos, _, _ = cinter(aslm, zduma, zdumo, xa1, xa2, ya1, ya2, xos1, xos2, yo1, yo2, nxa, 72, nya, 72)
    k_s = sum(1 for j in range(72) for i in range(72) if zslmaos[i][j] < 1e-9 and oslms[i][j] > 0.5)

    zslmaov, _, _ = cinter(aslm, zduma, zdumo, xa1, xa2, ya1, ya2, xov1, xov2, yo1, yo2, nxa, 72, nya, 72)
    k_v = sum(1 for j in range(72) for i in range(72) if zslmaov[i][j] < 1e-9 and oslmv[i][j] > 0.5)

    zslmoa, _, _ = cinter(oslms, zdumo, zduma, xos1, xos2, yo1, yo2, xa1, xa2, ya1, ya2, 72, nya, 72, nxa)
    k_a = sum(1 for j in range(nya) for i in range(nxa) if zslmoa[i][j] < 1e-9 and aslm[i][j] > 0.5)

    n_ocean = sum(sum(1 for val in col if val <= 0.5) for col in mask)
    return k_a, k_v, k_s, n_ocean


def derive_mask(input_sra: Path, topogr: Path, strategy: str = "B"):
    """Derive an LSG-consistent atmospheric land-sea mask."""
    header, pls_raw, nxa, nya = read_sra(input_sra)
    xa, ya, xa1, xa2, ya1, ya2, _ = build_plasim_grid(nxa, nya)
    _, _, _, xos1, xos2, xov1, xov2, yo1, yo2, _ = build_lsg_grid(72, 72)
    oslms, oslmv = read_lsg_topogr(topogr)

    # 1. Binarize input mask (dls > 0.5 -> 1.0 land, <= 0.5 -> 0.0 ocean)
    mask = [[1.0 if pls_raw[i][j] > 0.5 else 0.0 for j in range(nya)] for i in range(nxa)]

    # 2. Compute LSG ocean coverage on atmospheric grid
    zduma = [[1.0] * nya for _ in range(nxa)]
    zdumo = [[1.0] * 72 for _ in range(72)]
    zslmoa, _, _ = cinter(oslms, zdumo, zduma, xos1, xos2, yo1, yo2, xa1, xa2, ya1, ya2, 72, nya, 72, nxa)

    # 3. Close uncoupled atmospheric ocean cells (kmiss_a -> 0)
    for j in range(nya):
        for i in range(nxa):
            if zslmoa[i][j] < 1e-9:
                mask[i][j] = 1.0

    if strategy == "A":
        # Strategy A: open all cells where LSG has dominant ocean
        for j in range(nya):
            for i in range(nxa):
                if zslmoa[i][j] > 0.9:
                    mask[i][j] = 0.0

    elif strategy == "B":
        # 1. Panama isthmus closure (geographic corridor 7N-11N, 276E-283E)
        for j in range(nya):
            lat = math.degrees(ya[0][j])
            if 7.0 <= lat <= 11.0:
                for i in range(nxa):
                    lon = math.degrees(xa[i][j])
                    if 276.0 <= lon <= 283.0 and zslmoa[i][j] < 0.5:
                        mask[i][j] = 1.0

        # 2. Automated minimal vector point coverage (kmiss_v -> 0)
        # Checks each active LSG ocean vector point; if uncoupled, opens the
        # overlapping atmospheric cell with the highest LSG ocean coverage.
        aslm = [[1.0 - mask[i][j] for j in range(nya)] for i in range(nxa)]
        zslmaov, _, _ = cinter(aslm, zduma, zdumo, xa1, xa2, ya1, ya2, xov1, xov2, yo1, yo2, nxa, 72, nya, 72)

        pi = math.pi
        for jo in range(72):
            for io in range(72):
                if zslmaov[io][jo] < 1e-9 and oslmv[io][jo] > 0.5:
                    y1_o = min(yo1[io][jo], yo2[io][jo])
                    y2_o = max(yo1[io][jo], yo2[io][jo])
                    best_cell = None
                    best_score = -1.0
                    for ja in range(nya):
                        y1_a = min(ya1[0][ja], ya2[0][ja])
                        y2_a = max(ya1[0][ja], ya2[0][ja])
                        if not (y1_o <= y2_a and y2_o >= y1_a):
                            continue
                        for ia in range(nxa):
                            xol, xor = xov1[io][jo], xov2[io][jo]
                            xil, xir = xa1[ia][ja], xa2[ia][ja]
                            if abs(xol - xil) > pi:
                                if xol > xil:
                                    xor -= 2 * pi
                                    xol -= 2 * pi
                                else:
                                    xir -= 2 * pi
                                    xil -= 2 * pi
                            if max(xol, xil) < min(xor, xir):
                                if zslmoa[ia][ja] > best_score:
                                    best_score = zslmoa[ia][ja]
                                    best_cell = (ia, ja)
                    if best_cell is not None:
                        mask[best_cell[0]][best_cell[1]] = 0.0

    return header, mask, nxa, nya, (xa1, xa2, ya1, ya2, xos1, xos2, xov1, xov2, yo1, yo2, oslms, oslmv)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Derive an LSG-consistent atmospheric land-sea mask (Code 172 .sra) for PlaSim."
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=Path("plasim/dat/T42/N064_surf_0172.sra"),
        help="Input PlaSim land-sea mask .sra (default: plasim/dat/T42/N064_surf_0172.sra)",
    )
    parser.add_argument(
        "-t", "--topogr",
        type=Path,
        default=Path("lsg/dat/topogr"),
        help="LSG bathymetry file (default: lsg/dat/topogr)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output adapted .sra file (default: lsg/dat/N<nya>_surf_0172.sra)",
    )
    parser.add_argument(
        "-s", "--strategy",
        choices=["B", "A"],
        default="B",
        help="Adaptation strategy: 'B' (minimal T21-style, default) or 'A' (extrapolation-free)",
    )
    parser.add_argument(
        "-c", "--check",
        action="store_true",
        help="Evaluate and print coupler diagnostics (kmiss_a, kmiss_v, kmiss_s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform adaptation and checks without writing the output file",
    )

    args = parser.parse_args()

    if not args.input.is_file():
        sys.stderr.write(f"Error: input file '{args.input}' not found.\n")
        return 1
    if not args.topogr.is_file():
        sys.stderr.write(f"Error: topography file '{args.topogr}' not found.\n")
        return 1

    print(f"Reading input mask: {args.input}")
    print(f"Reading LSG bathymetry: {args.topogr}")
    print(f"Applying Strategy {args.strategy}...")

    header, mask, nxa, nya, grid_data = derive_mask(args.input, args.topogr, args.strategy)
    xa1, xa2, ya1, ya2, xos1, xos2, xov1, xov2, yo1, yo2, oslms, oslmv = grid_data

    # Header code 172
    out_header = [172, 0, 100, -1, nxa, nya, 0, 0]

    # Evaluate diagnostics
    k_a, k_v, k_s, n_ocean = evaluate_coupling(
        mask, oslms, oslmv, xa1, xa2, ya1, ya2, xos1, xos2, xov1, xov2, yo1, yo2, nxa, nya
    )

    print("\n--- Coupler Diagnostics for Resulting Mask ---")
    print(f"Atmospheric ocean cells:        {n_ocean} / {nxa * nya}")
    print(f"Missing atm ocean points (kmiss_a): {k_a}  (must be 0)")
    print(f"Missing ocean vectors (kmiss_v):    {k_v}  (must be 0)")
    print(f"Extrapolated ocean scalars (kmiss_s): {k_s}")

    if not args.dry_run:
        output_path = args.output or Path(f"lsg/dat/N{nya:03d}_surf_0172.sra")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_sra(output_path, out_header, mask, nxa, nya)
        print(f"\nSuccessfully wrote adapted land-sea mask to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
