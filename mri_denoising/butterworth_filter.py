"""
Butterworth low-pass filter in k-space for MRI frequency-domain denoising.

The Butterworth filter attenuates high-frequency components of k-space
(corresponding to fine detail and noise) while preserving the low-frequency
content (image contrast and coarse structure).

Filter definition (centred, Exercise 2.2 specification):
    H(u,v) = 1 / (1 + (D(u,v) / D0)^(2n))

where D(u,v) is the distance from the k-space centre and D0 is the
cutoff radius. Requires that k-space has a bright central intensity
(i.e. the DC component is at the centre, as in a post-fftshift array).
"""

import numpy as np


def butterworth_lowpass_filter(
    shape: tuple[int, int],
    D0: int = 30,
    n: int = 2,
) -> np.ndarray:
    """
    Generate a 2D Butterworth low-pass filter mask.

    The mask is centred so that (0, 0) corresponds to the DC component
    at the centre of a fftshift-ed k-space array.

    Parameters
    ----------
    shape : tuple[int, int]
        Shape (rows, cols) of the filter mask.
    D0 : int
        Cutoff frequency in pixels from the centre.
        Smaller D0 → more aggressive low-pass filtering.
    n : int
        Filter order. Higher n → steeper roll-off (closer to ideal).

    Returns
    -------
    np.ndarray
        Real-valued 2D filter mask, shape (rows, cols), values in (0, 1].
        The centre pixel equals 1.0 (DC fully passed).
    """
    P, Q = shape[0], shape[1]
    u = np.arange(P) - P // 2
    v = np.arange(Q) - Q // 2
    U, V = np.meshgrid(u, v, indexing="ij")
    D = np.sqrt(U**2 + V**2)
    H = 1 / (1 + (D / D0) ** (2 * n))
    return H


def apply_butterworth_filter(
    kspace_2d: np.ndarray,
    D0: int = 30,
    n: int = 2,
) -> np.ndarray:
    """
    Apply a Butterworth low-pass filter to a 2D k-space array.

    The coursework specification states the k-space must have a bright
    central intensity before the filter is applied. The steps are:

      1. ``fftshift``  — move DC from [0,0] to the centre (if not already).
      2. Multiply by the centred Butterworth mask H.
      3. ``ifftshift`` — restore DC to [0,0] (NumPy ifft2 convention).

    The result can be passed directly to ``np.fft.ifft2`` (or
    ``kspace_to_image``), consistent with the direct-ifft2 approach
    used throughout the module.

    Parameters
    ----------
    kspace_2d : np.ndarray
        2D complex k-space data, shape (rows, cols).
        DC component should be at [0,0] (NumPy FFT convention).
    D0 : int
        Butterworth cutoff radius in pixels from the k-space centre.
    n : int
        Butterworth filter order.

    Returns
    -------
    np.ndarray
        Filtered k-space in NumPy convention (DC at [0,0]), ready for
        ``np.fft.ifft2``.
    """
    H = butterworth_lowpass_filter(kspace_2d.shape, D0=D0, n=n)
    # Shift DC to centre → multiply by H → shift DC back to [0,0]
    kspace_shifted = np.fft.fftshift(kspace_2d)
    filtered_shifted = kspace_shifted * H
    return np.fft.ifftshift(filtered_shifted)
