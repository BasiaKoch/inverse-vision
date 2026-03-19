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


def load_shepp_logan(size: int = 256) -> np.ndarray:
    """
    Load and resize the Shepp-Logan phantom.

    Parameters
    ----------
    size : int
        Side length of the output square image in pixels.

    Returns
    -------
    np.ndarray
        2D phantom image with values in [0, 1], shape (size, size).
    """
    phantom = shepp_logan_phantom()
    if phantom.shape[0] != size:
        phantom = resize(phantom, (size, size), anti_aliasing=True)
    return phantom.astype(np.float64)


def load_ct_image(path: str | Path, size: int = 256) -> np.ndarray:
    """
    Load a CT image from a PNG file and normalise to [0, 1].

    Parameters
    ----------
    path : str or Path
        Path to the CT image file.
    size : int
        Output image side length in pixels.

    Returns
    -------
    np.ndarray
        2D normalised CT image, shape (size, size).
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
    if image.shape != (size, size):
        image = resize(image, (size, size), anti_aliasing=True)
    return image
