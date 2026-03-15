"""
k-space data loading utilities.

The MRI dataset (knee.npy) is a 3D complex array of shape
(n_coils, rows, cols) = (6, 280, 280).
"""

import numpy as np
from pathlib import Path


def load_kspace(path: str | Path) -> np.ndarray:
    """
    Load complex k-space data from a .npy file.

    Parameters
    ----------
    path : str or Path
        Path to the .npy k-space file (e.g. 'knee.npy').

    Returns
    -------
    np.ndarray
        Complex k-space array. For knee.npy the shape is
        (6, 280, 280) with coils on axis 0.
    """
    return np.load(str(path))


def identify_coil_dimension(kspace: np.ndarray) -> int:
    """
    Identify which axis corresponds to the coil dimension.

    Assumes the coil axis is the one with the smallest size
    (e.g. 6 coils vs 280 spatial pixels).

    Parameters
    ----------
    kspace : np.ndarray
        k-space data array.

    Returns
    -------
    int
        Axis index of the coil dimension.
    """
    return int(np.argmin(kspace.shape))
