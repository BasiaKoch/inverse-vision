"""
Image-space denoising filters for MRI magnitude images.

Four filters are provided as required by Exercise 2.2:
  - Gaussian    : scipy.ndimage.gaussian_filter
  - Mean (uniform): scipy.ndimage.uniform_filter
  - Median      : scipy.ndimage.median_filter   (as used in the course practical)
  - Bilateral   : skimage.restoration.denoise_bilateral
"""

import numpy as np
from scipy.ndimage import gaussian_filter, median_filter, uniform_filter
from skimage.restoration import denoise_bilateral


def apply_gaussian_filter(image: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """
    Apply Gaussian smoothing to a 2D image.

    Blurs the image by convolving with a Gaussian kernel. Reduces
    high-frequency noise but blurs edges proportional to sigma.

    Parameters
    ----------
    image : np.ndarray
        2D real-valued input image.
    sigma : float
        Standard deviation of the Gaussian kernel in pixels.
        Larger values → more smoothing.

    Returns
    -------
    np.ndarray
        Smoothed image, same shape as input.
    """
    return gaussian_filter(image.astype(np.float64), sigma=sigma)


def apply_mean_filter(image: np.ndarray, size: int = 3) -> np.ndarray:
    """
    Apply a uniform (mean / box) filter to a 2D image.

    Replaces each pixel with the average of its (size × size)
    neighbourhood. Simple and fast but does not preserve edges.

    Parameters
    ----------
    image : np.ndarray
        2D real-valued input image.
    size : int
        Side length of the square averaging kernel.

    Returns
    -------
    np.ndarray
        Filtered image, same shape as input.
    """
    return uniform_filter(image.astype(np.float64), size=size)


def apply_median_filter(image: np.ndarray, size: int = 3) -> np.ndarray:
    """
    Apply a median filter to a 2D image.

    Each pixel is replaced by the median value in its (size × size)
    neighbourhood. More robust to outliers and salt-and-pepper noise
    than the mean filter because the median is insensitive to extreme values.

    This filter is used in the course practical (Q9) via
    ``scipy.ndimage.median_filter``.

    Parameters
    ----------
    image : np.ndarray
        2D real-valued input image.
    size : int
        Side length of the square kernel. Larger values → more smoothing.
        Typical values: 3 (light), 5–7 (moderate), 10+ (heavy, blurs edges).

    Returns
    -------
    np.ndarray
        Filtered image, same shape as input.
    """
    return median_filter(image.astype(np.float64), size=size)


def apply_bilateral_filter(
    image: np.ndarray,
    sigma_color: float = 0.05,
    sigma_spatial: float = 3.0,
) -> np.ndarray:
    """
    Apply a bilateral filter to a 2D image.

    The bilateral filter is edge-preserving: it weights contributions
    from neighbouring pixels by both spatial distance and intensity
    similarity, so edges are retained while flat regions are smoothed.

    Parameters
    ----------
    image : np.ndarray
        2D real-valued input image. Will be normalised to [0, 1]
        internally then restored to the original range.
    sigma_color : float
        Range (intensity) kernel width. Smaller → more edge-preserving.
    sigma_spatial : float
        Spatial kernel width in pixels.

    Returns
    -------
    np.ndarray
        Filtered image, same shape and range as input.
    """
    img = image.astype(np.float64)
    img_min, img_max = img.min(), img.max()

    # Bilateral filter expects values in [0, 1]
    if img_max > img_min:
        normalised = (img - img_min) / (img_max - img_min)
    else:
        return img.copy()

    filtered = denoise_bilateral(
        normalised,
        sigma_color=sigma_color,
        sigma_spatial=sigma_spatial,
        channel_axis=None,
    )
    # Restore original intensity range
    return filtered * (img_max - img_min) + img_min
