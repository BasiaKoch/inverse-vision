"""
Phantom generation for CT reconstruction experiments.

Provides helpers to load the standard Shepp-Logan phantom and
load a real CT image from a PNG file.
"""

from pathlib import Path

import numpy as np
from skimage.color import rgb2gray
from skimage.data import shepp_logan_phantom
from skimage.io import imread
from skimage.transform import resize


def load_shepp_logan(size: int | None = None) -> np.ndarray:
    """
    Load the Shepp-Logan phantom, optionally resizing it.

    Parameters
    ----------
    size : int or None
        Optional side length of the output square image in pixels.
        If None, preserve the original phantom size.

    Returns
    -------
    np.ndarray
        2D phantom image with values in [0, 1].
    """
    phantom = shepp_logan_phantom()
    if size is not None and phantom.shape != (size, size):
        phantom = resize(phantom, (size, size), anti_aliasing=True)
    return phantom.astype(np.float64)


def load_ct_image(path: str | Path, size: int | None = None) -> np.ndarray:
    """
    Load a CT image from a PNG file, normalise it to [0, 1],
    and optionally resize it.

    Parameters
    ----------
    path : str or Path
        Path to the CT image file.
    size : int or None
        Optional output image side length in pixels.
        If None, preserve the original image size.

    Returns
    -------
    np.ndarray
        2D normalised CT image.
    """
    image = imread(str(path))
    if image.ndim == 3:
        # Drop alpha channel if present (RGBA → RGB) before converting to grayscale
        if image.shape[2] == 4:
            image = image[:, :, :3]
        image = rgb2gray(image)
    image = image.astype(np.float64)
    # Normalise to [0, 1]
    img_min, img_max = image.min(), image.max()
    if img_max > img_min:
        image = (image - img_min) / (img_max - img_min)
    if size is not None and image.shape != (size, size):
        image = resize(image, (size, size), anti_aliasing=True)
    return image
