"""
MRI image reconstruction from k-space via the inverse Fourier transform.

The standard reconstruction is a direct 2D inverse FFT:

    image = np.fft.ifft2(kspace)

This matches the convention used in the course practicals when the input
k-space already follows NumPy FFT ordering. For the coursework dataset
(``knee.npy``), the bright low-frequency content is stored at the centre
of the array, so ``ifftshift`` is required before ``ifft2``.

fftshift note
-------------
fftshift moves the DC component to the centre of the array (for display).
Two orderings appear in the literature and are NOT equivalent:

    np.fft.fftshift(np.fft.ifft2(kspace))   # reconstruct then shift image
    np.fft.ifft2(np.fft.fftshift(kspace))   # shift k-space then reconstruct

The first is a display convenience; the second changes the reconstruction
result by introducing a linear phase ramp. This module provides both
variants explicitly: ``kspace_to_image`` for NumPy-order k-space and
``kspace_to_image_centred`` for centred k-space such as ``knee.npy``.
"""

import numpy as np


def kspace_to_image(kspace_2d: np.ndarray) -> np.ndarray:
    """
    Reconstruct a complex MRI image from 2D k-space data.

    Applies np.fft.ifft2 directly, matching the course practical solution.
    The k-space is expected in NumPy FFT convention (DC at index [0, 0]).

    Parameters
    ----------
    kspace_2d : np.ndarray
        2D complex k-space array, shape (rows, cols).

    Returns
    -------
    np.ndarray
        Complex image array, same shape as input.
    """
    return np.fft.ifft2(kspace_2d)


def kspace_to_image_centred(kspace_2d: np.ndarray) -> np.ndarray:
    """
    Reconstruct from k-space where the DC component is at the centre.

    Use this variant when k-space has been fftshift-ed (bright centre),
    for example after Butterworth filtering or when loading data stored
    in centred convention.

    Parameters
    ----------
    kspace_2d : np.ndarray
        2D complex k-space with DC at centre, shape (rows, cols).

    Returns
    -------
    np.ndarray
        Complex image array, same shape as input.
    """
    return np.fft.ifft2(np.fft.ifftshift(kspace_2d))


def get_magnitude(image: np.ndarray) -> np.ndarray:
    """
    Compute the magnitude (absolute value) of a complex image.

    Parameters
    ----------
    image : np.ndarray
        Complex or real-valued image array.

    Returns
    -------
    np.ndarray
        Real-valued magnitude array, same shape as input.
    """
    return np.abs(image)


def get_phase(image: np.ndarray) -> np.ndarray:
    """
    Compute the phase of a complex image.

    Parameters
    ----------
    image : np.ndarray
        Complex image array.

    Returns
    -------
    np.ndarray
        Phase array in radians, values in [-pi, pi].
    """
    return np.angle(image)
