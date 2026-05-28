## Adding Colormaps

MRIcroGL includes several colormaps optimized for perceptual uniformity and accessibility—they maintain consistent [luminance](https://onlinelibrary.wiley.com/doi/full/10.1111/ejn.14430) and are robust to common [color vision deficiencies](https://www.nature.com/articles/s41467-020-19160-7). Users can also add their own colormaps. When MRIcroGL launches, it loads all `.clut` files from the `/Resources/lut` folder (on macOS, this is inside the app bundle at `MRIcroGL.app/Contents/Resources/lut`).

Each `.clut` file can define up to 256 colors. For continuous colormaps, it is often better to use fewer nodes—this makes it easier to edit individual nodes through the **Color Editor** (available from the **Color** menu).

This folder provides a Python script to convert [scientific colormaps for Python](https://github.com/pyapp-kit/cmap) into MRIcroGL-compatible `.clut` files. You can browse available colormaps in the [cmap catalog](https://cmap-docs.readthedocs.io/en/stable/catalog/).

Example usage to convert the *davos* colormap:

```bash
pip install cmap
python color2clut.py davos
```

Run `python color2clut.py` without arguments to batch-convert a default set of colormaps. The optional `-t` argument sets the interpolation tolerance, letting you balance node count against color precision.