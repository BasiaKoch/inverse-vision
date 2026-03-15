"""
Image quality evaluation metrics for CT reconstruction comparison.

Implements MSE, PSNR, and SSIM, all consistent with the skimage API.
"""

import numpy as np
from skimage.metrics import structural_similarity as _ssim
from skimage.metrics import peak_signal_noise_ratio as _psnr


def compute_mse(reference: np.ndarray, reconstructed: np.ndarray) -> float:
    """
    Compute Mean Squared Error (MSE).

    Parameters
    ----------
    reference : np.ndarray
        Ground-truth image.
    reconstructed : np.ndarray
        Reconstructed image (same shape as reference).

    Returns
    -------
    float
        MSE value. Lower is better.
    """
    return float(np.mean((reference - reconstructed) ** 2))


def compute_psnr(reference: np.ndarray, reconstructed: np.ndarray) -> float:
    """
    Compute Peak Signal-to-Noise Ratio (PSNR) in dB.

    PSNR = 10 * log10(MAX^2 / MSE), where MAX is the data range
    of the reference image.

    Parameters
    ----------
    reference : np.ndarray
        Ground-truth image.
    reconstructed : np.ndarray
        Reconstructed image (same shape as reference).

    Returns
    -------
    float
        PSNR in dB. Higher is better.
    """
    data_range = float(reference.max() - reference.min())
    return float(_psnr(reference, reconstructed, data_range=data_range))


def compute_ssim(reference: np.ndarray, reconstructed: np.ndarray) -> float:
    """
    Compute Structural Similarity Index (SSIM).

    SSIM measures perceptual similarity combining luminance, contrast,
    and structure components.

    Parameters
    ----------
    reference : np.ndarray
        Ground-truth image.
    reconstructed : np.ndarray
        Reconstructed image (same shape as reference).

    Returns
    -------
    float
        SSIM value in [-1, 1]. Higher is better; 1 = identical images.
    """
    data_range = float(reference.max() - reference.min())
    return float(_ssim(reference, reconstructed, data_range=data_range))


def compute_all_metrics(
    reference: np.ndarray, reconstructed: np.ndarray
) -> dict[str, float]:
    """
    Compute MSE, PSNR, and SSIM in a single call.

    Parameters
    ----------
    reference : np.ndarray
        Ground-truth image.
    reconstructed : np.ndarray
        Reconstructed image.

    Returns
    -------
    dict[str, float]
        Dictionary with keys 'mse', 'psnr', 'ssim'.
    """
    return {
        "mse": compute_mse(reference, reconstructed),
        "psnr": compute_psnr(reference, reconstructed),
        "ssim": compute_ssim(reference, reconstructed),
    }
