"""
High-level sinogram simulation combining forward projection and noise.

This module provides a single convenience function that wraps
forward_projection and noise_models for common experiment workflows.
"""

import numpy as np

from ct_reconstruction.forward_projection import compute_sinogram, make_angles
from ct_reconstruction.noise_models import add_poisson_noise, add_gaussian_noise


def simulate_sinogram(
    image: np.ndarray,
    num_projections: int = 360,
    max_angle: float = 180.0,
    I0: float | None = None,
    gaussian_sigma: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Simulate a CT sinogram with optional Poisson and Gaussian noise.

    Parameters
    ----------
    image : np.ndarray
        Input phantom image, shape (N, N).
    num_projections : int
        Number of projection angles.
    max_angle : float
        Angular range in degrees.
    I0 : float or None
        Source intensity for Poisson noise simulation. If None,
        no Poisson noise is added.
    gaussian_sigma : float or None
        Standard deviation for additive Gaussian noise. If None,
        no Gaussian noise is added.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        (sinogram, angles) — the (possibly noisy) sinogram and the
        projection angles used (degrees), shapes (detectors, angles)
        and (num_projections,).
    """
    angles = make_angles(num_projections, max_angle)
    sinogram = compute_sinogram(image, angles)

    if I0 is not None:
        sinogram = add_poisson_noise(sinogram, I0)

    if gaussian_sigma is not None:
        sinogram = add_gaussian_noise(sinogram, gaussian_sigma)

    return sinogram, angles
