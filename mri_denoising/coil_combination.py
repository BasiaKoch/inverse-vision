"""
Multi-coil MRI coil combination methods.

Root Sum of Squares (RSS) is the standard method for combining
magnitude images from multiple receiver coils. It is robust,
assumes independent noise, and requires no coil sensitivity maps.

SNR normalisation (as used in the course practical, Q7–Q8)
-----------------------------------------------------------
Before RSS, each coil image can be normalised by the standard deviation
of a background noise region:

    coil_snr = coil_magnitude / std(noise_region)

This ensures coils with lower noise contribute proportionally more to the
combination, improving the final SNR. The combined SNR image is then:

    combined = sqrt( sum_i (coil_i / sigma_i)^2 )
"""

import numpy as np


def normalise_coil_by_noise(
    coil_magnitude: np.ndarray,
    noise_rows: int = 3,
) -> np.ndarray:
    """
    Normalise a coil magnitude image by the background noise standard deviation.

    The noise level is estimated from the first ``noise_rows`` rows of the
    image, which are typically outside the anatomy and contain only receiver
    noise. This matches the approach in the course practical (Q7):

        brain_snr = brain / np.std(brain[:3])

    Parameters
    ----------
    coil_magnitude : np.ndarray
        2D real-valued coil magnitude image, shape (rows, cols).
    noise_rows : int
        Number of rows at the top of the image used as the noise region.

    Returns
    -------
    np.ndarray
        SNR-normalised image, same shape as input.
        Units are approximately SNR (signal / noise std).
    """
    noise_std = np.std(coil_magnitude[:noise_rows])
    if noise_std == 0:
        return coil_magnitude.copy()
    return coil_magnitude / noise_std


def estimate_noise_stds(
    coil_magnitudes: np.ndarray,
    coil_axis: int = 0,
    noise_rows: int = 3,
) -> np.ndarray:
    """
    Estimate one background noise standard deviation per coil.

    Parameters
    ----------
    coil_magnitudes : np.ndarray
        Real-valued magnitude images, coils stacked along coil_axis.
    coil_axis : int
        Axis along which coils are stacked.
    noise_rows : int
        Number of rows at the image border used to estimate noise std.

    Returns
    -------
    np.ndarray
        One-dimensional array of per-coil noise standard deviations.
    """
    n_coils = coil_magnitudes.shape[coil_axis]
    return np.array(
        [
            np.std(np.take(coil_magnitudes, i, axis=coil_axis)[:noise_rows])
            for i in range(n_coils)
        ]
    )


def combine_coils_rss(coil_images: np.ndarray, coil_axis: int = 0) -> np.ndarray:
    """
    Combine multi-coil images using Root Sum of Squares (RSS).

    RSS formula:
        combined(x,y) = sqrt( sum_i |coil_i(x,y)|^2 )

    Parameters
    ----------
    coil_images : np.ndarray
        Array of coil images. May be complex or real-valued.
        The coil dimension is specified by coil_axis.
        For knee.npy reconstructed images: shape (6, 280, 280),
        use coil_axis=0.
    coil_axis : int
        Axis along which the coils are stacked.

    Returns
    -------
    np.ndarray
        Combined image. Shape is input shape with coil_axis removed.
        Values are real and non-negative.
    """
    return np.sqrt(np.sum(np.abs(coil_images) ** 2, axis=coil_axis))


def combine_coils_rss_snr(
    coil_magnitudes: np.ndarray,
    coil_axis: int = 0,
    noise_rows: int = 3,
    noise_stds: np.ndarray | None = None,
) -> np.ndarray:
    """
    SNR-normalised Root Sum of Squares coil combination.

    Normalises each coil by its background noise standard deviation before
    combining with RSS. This matches the course practical approach (Q7–Q8):

        brain_snr = brain / np.std(brain[:3])
        rss = np.sqrt(sum(brain_snr_i ** 2))

    The result has units of SNR rather than raw signal magnitude, so coils
    with lower noise floors contribute proportionally more to the combination.

    Parameters
    ----------
    coil_magnitudes : np.ndarray
        Real-valued magnitude images, coils stacked along coil_axis.
        Shape (n_coils, rows, cols) for coil_axis=0.
    coil_axis : int
        Axis along which coils are stacked.
    noise_rows : int
        Number of rows at the image border used to estimate noise std.
    noise_stds : np.ndarray | None
        Optional fixed per-coil noise standard deviations. When provided,
        these are used instead of re-estimating noise from ``coil_magnitudes``.
        This is useful when combining denoised coil images while preserving
        the original intensity scaling.

    Returns
    -------
    np.ndarray
        SNR-weighted combined image, shape (rows, cols).
    """
    n_coils = coil_magnitudes.shape[coil_axis]
    if noise_stds is None:
        noise_stds = estimate_noise_stds(
            coil_magnitudes,
            coil_axis=coil_axis,
            noise_rows=noise_rows,
        )
    else:
        noise_stds = np.asarray(noise_stds)
        if noise_stds.shape != (n_coils,):
            raise ValueError(
                f"noise_stds must have shape ({n_coils},), got {noise_stds.shape}"
            )

    normalised = np.stack(
        [
            (
                np.take(coil_magnitudes, i, axis=coil_axis) / noise_stds[i]
                if noise_stds[i] != 0
                else np.take(coil_magnitudes, i, axis=coil_axis).copy()
            )
            for i in range(n_coils)
        ],
        axis=coil_axis,
    )
    return np.sqrt(np.sum(normalised ** 2, axis=coil_axis))
