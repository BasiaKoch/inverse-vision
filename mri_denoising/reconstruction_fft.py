"""
MRI image reconstruction from k-space via the inverse Fourier transform.

The standard reconstruction is a direct 2D inverse FFT:

    image = np.fft.ifft2(kspace)

"""

import numpy as np


def kspace_to_image(kspace_2d: np.ndarray) -> np.ndarray:
    """
    Reconstruct a complex MRI image from 2D k-space data.

    Applies np.fft.ifft2 directly, matching the course practical solution.
    The k-space is expected in NumPy FFT convention (DC at index [0, 0]).
    """
    return np.fft.ifft2(kspace_2d)


def kspace_to_image_centred(kspace_2d: np.ndarray) -> np.ndarray:
    """
    Reconstruct from k-space where the DC component is at the centre.

    Use this variant when k-space has been fftshift-ed (bright centre),
    for example after Butterworth filtering or when loading data stored
    in centred convention.

    """
    return np.fft.ifft2(np.fft.ifftshift(kspace_2d))


def get_magnitude(image: np.ndarray) -> np.ndarray:
    """
    Compute the magnitude (absolute value) of a complex image.
    """
    return np.abs(image)


def get_phase(image: np.ndarray) -> np.ndarray:
    """
    Compute the phase of a complex image.

    """
    return np.angle(image)
