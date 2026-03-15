"""
Unit tests for the CT reconstruction module.

Run with:
    pytest tests/test_ct.py -v
"""

import numpy as np
import pytest

from ct_reconstruction.phantom import load_shepp_logan
from ct_reconstruction.forward_projection import compute_sinogram, make_angles
from ct_reconstruction.noise_models import add_poisson_noise, add_gaussian_noise
from ct_reconstruction.reconstruction_fbp import reconstruct_fbp
from ct_reconstruction.reconstruction_iterative import reconstruct_sirt, reconstruct_os_sart
from ct_reconstruction.evaluation_metrics import compute_mse, compute_psnr, compute_ssim
from ct_reconstruction.filters import validate_filter, AVAILABLE_FILTERS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def small_phantom() -> np.ndarray:
    """64×64 Shepp-Logan phantom for fast test runs."""
    return load_shepp_logan(size=64)


@pytest.fixture(scope="module")
def sinogram_and_angles(small_phantom) -> tuple[np.ndarray, np.ndarray]:
    angles = make_angles(45)
    sinogram = compute_sinogram(small_phantom, angles)
    return sinogram, angles


# ---------------------------------------------------------------------------
# Phantom
# ---------------------------------------------------------------------------

class TestPhantom:
    def test_shape(self, small_phantom):
        assert small_phantom.shape == (64, 64)

    def test_value_range(self, small_phantom):
        assert small_phantom.min() >= 0.0
        assert small_phantom.max() <= 1.0

    def test_dtype(self, small_phantom):
        assert small_phantom.dtype == np.float64


# ---------------------------------------------------------------------------
# Forward projection
# ---------------------------------------------------------------------------

class TestForwardProjection:
    def test_sinogram_columns_match_angles(self, small_phantom):
        angles = make_angles(45)
        sinogram = compute_sinogram(small_phantom, angles)
        assert sinogram.shape[1] == 45

    def test_make_angles_length(self):
        angles = make_angles(180)
        assert len(angles) == 180

    def test_make_angles_start(self):
        angles = make_angles(10)
        assert angles[0] == pytest.approx(0.0)

    def test_make_angles_range(self):
        angles = make_angles(10, max_angle=120.0)
        assert angles[-1] < 120.0  # endpoint=False

    def test_sinogram_non_negative(self, sinogram_and_angles):
        sinogram, _ = sinogram_and_angles
        assert sinogram.min() >= 0.0


# ---------------------------------------------------------------------------
# Noise models
# ---------------------------------------------------------------------------

class TestNoiseModels:
    def test_poisson_changes_values(self, sinogram_and_angles):
        sinogram, _ = sinogram_and_angles
        np.random.seed(42)
        noisy = add_poisson_noise(sinogram, I0=1e5)
        assert not np.allclose(noisy, sinogram)

    def test_poisson_shape_preserved(self, sinogram_and_angles):
        sinogram, _ = sinogram_and_angles
        noisy = add_poisson_noise(sinogram, I0=1e5)
        assert noisy.shape == sinogram.shape

    def test_gaussian_changes_values(self, sinogram_and_angles):
        sinogram, _ = sinogram_and_angles
        np.random.seed(42)
        noisy = add_gaussian_noise(sinogram, sigma=0.05)
        assert not np.allclose(noisy, sinogram)

    def test_gaussian_shape_preserved(self, sinogram_and_angles):
        sinogram, _ = sinogram_and_angles
        noisy = add_gaussian_noise(sinogram, sigma=0.05)
        assert noisy.shape == sinogram.shape

    def test_low_dose_noisier_than_high_dose(self, sinogram_and_angles):
        sinogram, _ = sinogram_and_angles
        np.random.seed(42)
        noisy_low = add_poisson_noise(sinogram, I0=1e2)
        np.random.seed(42)
        noisy_high = add_poisson_noise(sinogram, I0=1e5)
        assert np.std(noisy_low - sinogram) > np.std(noisy_high - sinogram)


# ---------------------------------------------------------------------------
# FBP reconstruction
# ---------------------------------------------------------------------------

class TestFBP:
    def test_output_shape_matches_phantom(self, sinogram_and_angles, small_phantom):
        sinogram, angles = sinogram_and_angles
        recon = reconstruct_fbp(sinogram, angles)
        assert recon.shape == small_phantom.shape

    def test_ramp_filter_reasonable_mse(self, sinogram_and_angles, small_phantom):
        sinogram, angles = sinogram_and_angles
        recon = reconstruct_fbp(sinogram, angles, filter_name="ramp")
        assert compute_mse(small_phantom, recon) < 0.5

    @pytest.mark.parametrize("filt", ["ramp", "shepp-logan", "cosine"])
    def test_all_filters_produce_output(self, sinogram_and_angles, filt):
        sinogram, angles = sinogram_and_angles
        recon = reconstruct_fbp(sinogram, angles, filter_name=filt)
        assert recon.ndim == 2


# ---------------------------------------------------------------------------
# Iterative reconstruction
# ---------------------------------------------------------------------------

class TestIterativeReconstruction:
    def test_sirt_output_shape(self, sinogram_and_angles, small_phantom):
        sinogram, angles = sinogram_and_angles
        recon = reconstruct_sirt(sinogram, angles, gamma=0.001, n_iterations=5)
        assert recon.shape == small_phantom.shape

    def test_sirt_non_negative(self, sinogram_and_angles):
        sinogram, angles = sinogram_and_angles
        recon = reconstruct_sirt(sinogram, angles, gamma=0.001, n_iterations=5)
        assert recon.min() >= 0.0

    def test_os_sart_output_shape(self, sinogram_and_angles, small_phantom):
        sinogram, angles = sinogram_and_angles
        recon = reconstruct_os_sart(sinogram, angles, n_iterations=2, n_subsets=5)
        assert recon.shape == small_phantom.shape

    def test_os_sart_non_negative(self, sinogram_and_angles):
        sinogram, angles = sinogram_and_angles
        recon = reconstruct_os_sart(sinogram, angles, n_iterations=2, n_subsets=5)
        assert recon.min() >= 0.0


# ---------------------------------------------------------------------------
# Evaluation metrics
# ---------------------------------------------------------------------------

class TestMetrics:
    def test_mse_identical_images(self, small_phantom):
        assert compute_mse(small_phantom, small_phantom) == pytest.approx(0.0)

    def test_mse_positive_for_different_images(self, small_phantom):
        noisy = small_phantom + 0.1
        assert compute_mse(small_phantom, noisy) > 0.0

    def test_psnr_identical_images_high(self, small_phantom):
        assert compute_psnr(small_phantom, small_phantom) > 100.0

    def test_ssim_identical_images(self, small_phantom):
        assert compute_ssim(small_phantom, small_phantom) == pytest.approx(1.0, abs=1e-5)

    def test_ssim_range(self, small_phantom):
        noisy = small_phantom + np.random.normal(0, 0.1, small_phantom.shape)
        val = compute_ssim(small_phantom, noisy)
        assert -1.0 <= val <= 1.0


# ---------------------------------------------------------------------------
# Filter validation
# ---------------------------------------------------------------------------

class TestFilters:
    def test_valid_filter_accepted(self):
        assert validate_filter("ramp") == "ramp"

    def test_case_insensitive(self):
        assert validate_filter("RAMP") == "ramp"

    def test_invalid_filter_raises(self):
        with pytest.raises(ValueError):
            validate_filter("unknown_filter")

    def test_all_available_filters_valid(self):
        for filt in AVAILABLE_FILTERS:
            assert validate_filter(filt) == filt
