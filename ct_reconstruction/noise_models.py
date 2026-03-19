"""
Noise models for CT sinogram simulation.

Two noise sources are modelled:
  - Poisson noise  : photon counting statistics (Beer-Lambert model)
  - Gaussian noise : electronic detector noise
"""

import numpy as np


def add_poisson_noise(sinogram: np.ndarray, I0: float) -> np.ndarray:
    """
    Add Poisson noise to a sinogram via the Beer-Lambert model.

    The sinogram is first normalised to [0, 1] before applying Beer-Lambert,
    as the Radon transform of a phantom produces large line-integral values
    (e.g. 0–50) that make exp(-sinogram) effectively zero for most rays,
    causing unrealistic clipping. This matches the hint in Practical 2, Q3a:

        "you may want to normalize the sinogram before applying the Beer law,
         as the units are too large due to our simple simulation"

    Steps:
        p_norm      = sinogram / sinogram.max()              # normalise to [0, 1]
        intensity   = I0 * exp(-p_norm)                     # Beer-Lambert
        counts_noisy ~ Poisson(intensity)                   # photon noise
        p_noisy     = -log(counts_noisy / I0) * sinogram.max()  # back to original scale

    Parameters
    ----------
    sinogram : np.ndarray
        Clean sinogram (line-integral attenuation values),
        shape (detectors, angles).
    I0 : float
        Incident photon count. Lower values produce more noise.

    Returns
    -------
    np.ndarray
        Noisy sinogram in attenuation domain, same shape as input.
    """
    p_max = sinogram.max()
    if p_max == 0:
        return sinogram.copy()
    # Normalise so Beer-Lambert operates in a physically sensible range
    p_norm = sinogram / p_max
    # Convert attenuation to expected photon counts
    intensity = I0 * np.exp(-p_norm)
    # Sample Poisson-distributed photon counts
    counts_noisy = np.random.poisson(intensity).astype(np.float64)
    # Clip to avoid log(0) singularity
    counts_noisy = np.clip(counts_noisy, 1, None)
    # Convert back to attenuation domain and restore original scale
    return -np.log(counts_noisy / I0) * p_max


def add_gaussian_noise(sinogram: np.ndarray, sigma: float = 0.05) -> np.ndarray:
    """
    Add zero-mean Gaussian noise to a sinogram.

    Simulates additive electronic detector noise:
        p_noisy = p + N(0, sigma)

    Parameters
    ----------
    sinogram : np.ndarray
        Input sinogram, shape (detectors, angles).
    sigma : float
        Standard deviation of the Gaussian noise.

    Returns
    -------
    np.ndarray
        Noisy sinogram, same shape as input.
    """
    noise = np.random.normal(0.0, sigma, size=sinogram.shape)
    return sinogram + noise
