"""
Filtered Backprojection (FBP) reconstruction for CT.

FBP applies a ramp-like filter in Fourier space before backprojecting,
compensating for the low-frequency bias inherent in plain backprojection.
Supported filters: 'ramp' (Ram-Lak), 'shepp-logan', 'cosine',
'hamming', 'hann'.
"""

import numpy as np
from skimage.transform import iradon


def reconstruct_fbp(
    sinogram: np.ndarray,
    angles: np.ndarray,
    filter_name: str = "ramp",
) -> np.ndarray:
    """
    Reconstruct a CT image from a sinogram using Filtered Backprojection.

    Parameters
    ----------
    sinogram : np.ndarray
        Sinogram array, shape (detectors, num_angles).
    angles : np.ndarray
        Projection angles in degrees, length must equal sinogram columns.
    filter_name : str
        Ramp filter to apply before backprojection.
        Options: 'ramp', 'shepp-logan', 'cosine', 'hamming', 'hann'.

    Returns
    -------
    np.ndarray
        Reconstructed 2D image, shape approximately (detectors, detectors).
    """
    return iradon(sinogram, theta=angles, filter_name=filter_name, circle=True)
