"""
Radon transform-based forward projection for CT sinogram generation.

Wraps ``skimage.transform.radon`` with a consistent interface used
throughout the CT module.
"""

import numpy as np
from skimage.transform import radon


def make_angles(num_projections: int, max_angle: float = 180.0) -> np.ndarray:
    """
    Generate evenly-spaced projection angles over [0, max_angle).

    Uses ``endpoint=False`` so that 0° and ``max_angle`` are not both
    included (avoids duplicate projections in full-rotation scans).

    Parameters
    ----------
    num_projections : int
        Number of projection angles to generate.
    max_angle : float
        Total angular range in degrees. Default is 180°.

    Returns
    -------
    np.ndarray
        1-D array of angles in degrees, shape (num_projections,).
    """
    return np.linspace(0.0, max_angle, num_projections, endpoint=False)


def compute_sinogram(image: np.ndarray, angles: np.ndarray) -> np.ndarray:
    """
    Compute the CT sinogram of an image via the Radon transform.

    Parameters
    ----------
    image : np.ndarray
        2D input phantom or CT image, shape (N, N).
        Values represent linear attenuation coefficients.
    angles : np.ndarray
        Projection angles in degrees, shape (num_projections,).

    Returns
    -------
    np.ndarray
        Sinogram array, shape (detectors, num_projections).
        Each column is one projection (line integral) at the
        corresponding angle.
    """
    return radon(image, theta=angles, circle=True)
