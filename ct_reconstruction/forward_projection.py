"""
Forward projection (Radon transform) for CT sinogram generation.

The Radon transform computes line integrals through an image at
specified projection angles, simulating the X-ray acquisition process.
"""

import numpy as np
from skimage.transform import radon


def compute_sinogram(image: np.ndarray, angles: np.ndarray) -> np.ndarray:
    """
    Compute the CT sinogram via the Radon transform.

    Parameters
    ----------
    image : np.ndarray
        2D input phantom image, shape (N, N).
    angles : np.ndarray
        1D array of projection angles in degrees.

    Returns
    -------
    np.ndarray
        Sinogram array of shape (num_detectors, len(angles)).
    """
    return radon(image, theta=angles, circle=True)


def make_angles(num_projections: int, max_angle: float = 180.0) -> np.ndarray:
    """
    Generate evenly spaced projection angles from 0 to max_angle.

    Parameters
    ----------
    num_projections : int
        Total number of projection angles.
    max_angle : float
        Angular range in degrees (not included as endpoint).

    Returns
    -------
    np.ndarray
        1D array of angles in degrees, length num_projections.
    """
    return np.linspace(0.0, max_angle, num=num_projections, endpoint=False)
