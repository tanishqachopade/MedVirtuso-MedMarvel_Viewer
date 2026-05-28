#!/usr/bin/env python3
"""
color2clut.py

Usage:
    python color2clut.py [<cmap_name>] [-o OUTDIR] [-t TOL]

If <cmap_name> is provided, create <cmap_name>.clut.
If no name is provided, convert the default list of colormap names.

Writes MRIcroGL .clut files. Alpha = round(node_intensity/2).
"""
import argparse
import os
from cmap import Colormap
import numpy as np
from typing import List, Tuple, Any

# ---------- Converter utilities (unchanged from prior working version) ----------
def color_like_to_rgb(value: Any) -> Tuple[int, int, int]:
    if isinstance(value, str):
        s = value.lstrip('#')
        if len(s) >= 6:
            r = int(s[0:2], 16)
            g = int(s[2:4], 16)
            b = int(s[4:6], 16)
            return (r, g, b)
        raise ValueError(f"Unrecognized hex string: {value}")

    if hasattr(value, "hex"):
        try:
            hx = value.hex
            if isinstance(hx, str):
                return color_like_to_rgb(hx)
        except Exception:
            pass

    if hasattr(value, "rgba"):
        try:
            rgba = value.rgba
            if rgba is not None:
                arr = np.array(rgba)
                return _numeric_array_to_rgb(arr)
        except Exception:
            pass

    try:
        s = str(value)
        if s.startswith("#") or (len(s) >= 6 and all(c in "0123456789ABCDEFabcdef#" for c in s[:7])):
            return color_like_to_rgb(s)
    except Exception:
        pass

    if isinstance(value, (tuple, list, np.ndarray)):
        arr = np.array(value)
        return _numeric_array_to_rgb(arr)

    raise ValueError(f"Cannot interpret color value: {repr(value)}")


def _numeric_array_to_rgb(arr: np.ndarray) -> Tuple[int, int, int]:
    arr = np.asarray(arr).astype(float).flatten()
    if arr.size >= 3:
        if np.all(arr[:3] <= 1.0 + 1e-8):
            rgb = np.clip(np.round(arr[:3] * 255.0), 0, 255).astype(int)
        else:
            rgb = np.clip(np.round(arr[:3]), 0, 255).astype(int)
        return (int(rgb[0]), int(rgb[1]), int(rgb[2]))
    raise ValueError(f"Numeric color must have length >=3, got {arr}")


def sample_colormap(cmap_obj, n: int = 256) -> np.ndarray:
    cols = []
    for i in range(n):
        t = i / (n - 1)
        val = cmap_obj(t)
        r, g, b = color_like_to_rgb(val)
        cols.append((r, g, b))
    return np.array(cols, dtype=int)

# ---------- reduction algorithm (unchanged) ----------
def max_error_in_interval(cols: np.ndarray, i0: int, i1: int) -> Tuple[int,int]:
    if i1 <= i0 + 1:
        return 0, -1
    c0 = cols[i0].astype(float)
    c1 = cols[i1].astype(float)
    best_err = -1
    best_idx = -1
    denom = i1 - i0
    for j in range(i0 + 1, i1):
        t = (j - i0) / denom
        interp = c0 + t * (c1 - c0)
        interp_rounded = np.round(interp).astype(int)
        actual = cols[j]
        err = np.max(np.abs(interp_rounded - actual))
        if err > best_err:
            best_err = int(err)
            best_idx = j
    return best_err, best_idx

def reduce_nodes(cols: np.ndarray, tol: int = 1) -> List[int]:
    n = cols.shape[0]
    kept = [0, n - 1]
    while True:
        global_best_err = -1
        global_best_idx = -1
        for a, b in zip(kept[:-1], kept[1:]):
            err, idx = max_error_in_interval(cols, a, b)
            if err > global_best_err:
                global_best_err = err
                global_best_idx = idx
        if global_best_err <= tol:
            break
        kept.append(global_best_idx)
        kept.sort()
    return kept

def write_clut(filename: str, kept_indices: List[int], cols: np.ndarray):
    numnodes = len(kept_indices)
    with open(filename, "w", encoding="utf-8") as f:
        f.write("[FLT]\n")
        f.write("min=0\n")
        f.write("max=255\n")
        f.write("[INT]\n")
        f.write(f"numnodes={numnodes}\n")
        f.write("[BYT]\n")
        for i, idx in enumerate(kept_indices):
            f.write(f"nodeintensity{i}={idx}\n")
        f.write("[RGBA255]\n")
        for i, idx in enumerate(kept_indices):
            r,g,b = cols[idx]
            a = int(round(idx / 2.0))
            f.write(f"nodergba{i}={r}|{g}|{b}|{a}\n")

# ---------- default list (cleaned/normalized) ----------
DEFAULT_CMAP_LIST = [
    "fake_parula", "inferno", "magma", "bordeaux", "amethyst", "gem",
    "panatel", "acton", "bamako", "batlow", "davos", "devon", "glasgow",
    "hawaii", "imola", "lipari", "nuuk", "oslo", "tokyo", "turku",
    "cubehelix", "mako", "rocket"
]
# note: I normalized 'osla'->'oslo' and removed stray semicolons in 'panatel;'.
# If your installed cmap registry uses slightly different names, the script
# will skip names that raise an error and print a message.

def process_one(name: str, outdir: str, tol: int):
    outname = os.path.join(outdir, f"{name}.clut")
    try:
        cmap = Colormap(name)
    except Exception as e:
        print(f"Skipping '{name}': cannot construct Colormap('{name}'): {e}")
        return False
    cols = sample_colormap(cmap, n=256)
    kept = reduce_nodes(cols, tol=tol)
    write_clut(outname, kept, cols)
    print(f"Wrote {outname}  (sampled=256 -> nodes={len(kept)})")
    return True

def main():
    p = argparse.ArgumentParser(description="Create MRIcroGL .clut from cmap.Colormap (single or batch)")
    p.add_argument("name", nargs="?", default=None, help="optional colormap name (e.g. davos). If omitted, process default list.")
    p.add_argument("-o", "--outdir", default=".", help="output directory for .clut files (default: current dir)")
    p.add_argument("-t", "--tol", type=int, default=2, help="max allowed per-channel interpolation error (default: 2)")
    args = p.parse_args()

    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)

    if args.name:
        ok = process_one(args.name, outdir, args.tol)
        if not ok:
            raise SystemExit(2)
    else:
        print("No name provided — processing default colormap list.")
        for nm in DEFAULT_CMAP_LIST:
            process_one(nm, outdir, args.tol)

if __name__ == "__main__":
    main()
