"""
Iterative reconstruction algorithms for CT.

Implements two gradient-descent-based methods:
  - SIRT  : Simultaneous Iterative Reconstruction Technique — uses all
            projections in each update step (standard gradient descent).
  - OS-SART: Ordered Subsets SART — splits projections into mini-batches
            and updates after each batch, accelerating convergence.

Both methods use implicit forward (radon) and back (iradon without filter)
projection operators from scikit-image to avoid storing large matrices.
"""

import numpy as np
from skimage.transform import radon, iradon


def reconstruct_sirt(
    sinogram: np.ndarray,
    angles: np.ndarray,
    gamma: float = 0.001,
    n_iterations: int = 50,
) -> np.ndarray:
    """
    Reconstruct a CT image using SIRT (gradient descent).

    Update rule per iteration:
        x_{k+1} = clip( x_k - gamma * A^T (A x_k - b), 0 )

    A is evaluated via radon() and A^T via iradon() without the ramp filter.

    Parameters
    ----------
    sinogram : np.ndarray
        Measured sinogram (attenuation values), shape (detectors, angles).
    angles : np.ndarray
        Projection angles in degrees.
    gamma : float
        Gradient descent step size (learning rate). Typical value: 0.001.
    n_iterations : int
        Number of gradient-descent iterations.

    Returns
    -------
    np.ndarray
        Reconstructed 2D image after n_iterations steps.
    """
    n = sinogram.shape[0]
    x = np.zeros((n, n), dtype=np.float64)

    for _ in range(n_iterations):
        # Forward project current estimate
        Ax = radon(x, theta=angles, circle=True)
        # Residual in sinogram (measurement) space
        residual = Ax - sinogram
        # Backproject residual — transpose of the forward operator
        gradient = iradon(residual, theta=angles, filter_name=None, circle=True)
        # Gradient descent step with non-negativity constraint
        x = np.clip(x - gamma * gradient, 0, None)

    return x


def reconstruct_os_sart(
    sinogram: np.ndarray,
    angles: np.ndarray,
    gamma: float = 0.001,
    n_iterations: int = 10,
    n_subsets: int = 10,
) -> np.ndarray:
    """
    Reconstruct a CT image using OS-SART (Ordered Subsets SART).

    Splits projection angles into n_subsets mini-batches and performs a
    gradient-descent update after each mini-batch. This gives n_subsets
    updates per epoch, accelerating convergence compared to SIRT.

    Parameters
    ----------
    sinogram : np.ndarray
        Measured sinogram, shape (detectors, angles).
    angles : np.ndarray
        Projection angles in degrees.
    gamma : float
        Step size per subset update.
    n_iterations : int
        Number of full epochs (passes over all subsets).
    n_subsets : int
        Number of ordered subsets to split the projections into.

    Returns
    -------
    np.ndarray
        Reconstructed 2D image.
    """
    n = sinogram.shape[0]
    x = np.zeros((n, n), dtype=np.float64)

    # Pre-compute subset index splits
    subset_indices = np.array_split(np.arange(len(angles)), n_subsets)

    for _ in range(n_iterations):
        for idx in subset_indices:
            sub_angles = angles[idx]
            sub_sinogram = sinogram[:, idx]

            Ax = radon(x, theta=sub_angles, circle=True)
            residual = Ax - sub_sinogram
            gradient = iradon(residual, theta=sub_angles, filter_name=None, circle=True)
            x = np.clip(x - gamma * gradient, 0, None)

    return x
