"""
Visualisation utilities for k-space and MRI images.

All plot functions return matplotlib Figure objects so they can be
shown interactively in notebooks or saved to disk in scripts.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure


def plot_kspace_magnitude(
    kspace: np.ndarray,
    coil_axis: int = 0,
    title_prefix: str = "Coil",
) -> Figure:
    """
    Plot the log-magnitude of k-space for every coil.

    Uses ``np.log1p(|kspace|)`` so that both weak and strong frequency
    components are visible simultaneously.

    Parameters
    ----------
    kspace : np.ndarray
        k-space data with coils stacked along coil_axis.
        For knee.npy: shape (6, 280, 280), coil_axis=0.
    coil_axis : int
        Axis corresponding to the coil dimension.
    title_prefix : str
        Prefix string for each subplot title.

    Returns
    -------
    matplotlib.figure.Figure
        Figure with one subplot per coil.
    """
    n_coils = kspace.shape[coil_axis]
    fig, axes = plt.subplots(1, n_coils, figsize=(3 * n_coils, 3))
    if n_coils == 1:
        axes = [axes]

    for i, ax in enumerate(axes):
        coil_kspace = np.take(kspace, i, axis=coil_axis)
        magnitude = np.log1p(np.abs(coil_kspace))
        ax.imshow(magnitude, cmap="gray", origin="upper")
        ax.set_title(f"{title_prefix} {i + 1}")
        ax.axis("off")

    fig.suptitle("k-space log-magnitude")
    fig.tight_layout()
    return fig


def plot_magnitude_images(
    images: np.ndarray,
    coil_axis: int = 0,
    title_prefix: str = "Coil",
) -> Figure:
    """
    Plot the magnitude of reconstructed images for every coil.

    Parameters
    ----------
    images : np.ndarray
        Complex or real coil images, coils along coil_axis.
    coil_axis : int
        Axis corresponding to the coil dimension.
    title_prefix : str
        Prefix for subplot titles.

    Returns
    -------
    matplotlib.figure.Figure
    """
    n_coils = images.shape[coil_axis]
    fig, axes = plt.subplots(1, n_coils, figsize=(3 * n_coils, 3))
    if n_coils == 1:
        axes = [axes]

    for i, ax in enumerate(axes):
        coil_img = np.take(images, i, axis=coil_axis)
        ax.imshow(np.abs(coil_img), cmap="gray", origin="upper")
        ax.set_title(f"{title_prefix} {i + 1}")
        ax.axis("off")

    fig.suptitle("Magnitude images (per coil)")
    fig.tight_layout()
    return fig


def plot_magnitude_and_phase(image: np.ndarray, title: str = "") -> Figure:
    """
    Plot magnitude and phase of a single complex MRI image side by side.

    Parameters
    ----------
    image : np.ndarray
        2D complex image, shape (rows, cols).
    title : str
        Overall figure title.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))

    ax1.imshow(np.abs(image), cmap="gray", origin="upper")
    ax1.set_title("Magnitude")
    ax1.axis("off")

    ax2.imshow(np.angle(image), cmap="hsv", origin="upper")
    ax2.set_title("Phase")
    ax2.axis("off")

    if title:
        fig.suptitle(title)
    fig.tight_layout()
    return fig
