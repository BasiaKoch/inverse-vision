"""
Image quality evaluation metrics for CT reconstruction.

Three standard metrics are implemented:
  - MSE   : Mean Squared Error (lower is better)
  - PSNR  : Peak Signal-to-Noise Ratio in dB (higher is better)
  - SSIM  : Structural Similarity Index (1.0 = identical)
"""

import numpy as np
from skimage.metrics import structural_similarity


def compute_mse(reference: np.ndarray, reconstruction: np.ndarray) -> float:
    """
    Compute the Mean Squared Error between two images.

    Parameters
    ----------
    reference : np.ndarray
        Ground-truth image.
    reconstruction : np.ndarray
        Reconstructed image to evaluate. Must have the same shape as
        ``reference``.

    Returns
    -------
    float
        Mean squared error (non-negative). Zero indicates identical images.
    """
    return float(np.mean((reference.astype(np.float64) - reconstruction.astype(np.float64)) ** 2))


def compute_psnr(reference: np.ndarray, reconstruction: np.ndarray) -> float:
    """
    Compute the Peak Signal-to-Noise Ratio in decibels.

    PSNR is defined as:
        PSNR = 10 * log10(data_range^2 / MSE)

    where ``data_range`` is the range of the reference image
    (``max - min``). Returns ``inf`` when MSE is zero (identical images).

    Parameters
    ----------
    reference : np.ndarray
        Ground-truth image.
    reconstruction : np.ndarray
        Reconstructed image to evaluate.

    Returns
    -------
    float
        PSNR in dB.
    """
    ref = reference.astype(np.float64)
    rec = reconstruction.astype(np.float64)
    mse = float(np.mean((ref - rec) ** 2))
    if mse == 0.0:
        return float("inf")
    data_range = ref.max() - ref.min()
    if data_range == 0.0:
        return float("inf")
    return 10.0 * np.log10(data_range**2 / mse)


def compute_ssim(reference: np.ndarray, reconstruction: np.ndarray) -> float:
    """
    Compute the Structural Similarity Index (SSIM).

    Uses ``skimage.metrics.structural_similarity`` with the data range
    set to the range of the reference image.

    Parameters
    ----------
    reference : np.ndarray
        Ground-truth image.
    reconstruction : np.ndarray
        Reconstructed image to evaluate.

    Returns
    -------
    float
        SSIM score in [-1, 1]. A value of 1.0 means the images are
        identical in structure, luminance, and contrast.
    """
    ref = reference.astype(np.float64)
    rec = reconstruction.astype(np.float64)
    data_range = ref.max() - ref.min()
    return float(structural_similarity(ref, rec, data_range=data_range))
