"""
Unit tests for the MRI processing module.

Run with:
    pytest tests/test_mri.py -v
"""

import numpy as np
import pytest

from mri_denoising.reconstruction_fft import kspace_to_image, get_magnitude, get_phase
from mri_denoising.coil_combination import combine_coils_rss
from mri_denoising.butterworth_filter import (
    butterworth_lowpass_filter,
    apply_butterworth_filter,
)
from mri_denoising.denoising_filters import (
    apply_gaussian_filter,
    apply_mean_filter,
    apply_median_filter,
    apply_bilateral_filter,
)
from mri_denoising.coil_combination import normalise_coil_by_noise, combine_coils_rss_snr
from mri_denoising.load_kspace import identify_coil_dimension


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def synthetic_kspace() -> np.ndarray:
    """64×64 synthetic complex k-space with reproducible random values."""
    rng = np.random.default_rng(42)
    real = rng.standard_normal((64, 64))
    imag = rng.standard_normal((64, 64))
    return (real + 1j * imag).astype(np.complex128)


@pytest.fixture(scope="module")
def synthetic_multi_coil(synthetic_kspace) -> np.ndarray:
    """3 coils stacked on axis 0, shape (3, 64, 64)."""
    return np.stack(
        [synthetic_kspace * (i + 1) for i in range(3)],
        axis=0,
    )


@pytest.fixture(scope="module")
def test_image() -> np.ndarray:
    """64×64 real-valued image in [0, 1] for denoising tests."""
    rng = np.random.default_rng(42)
    return rng.random((64, 64)).astype(np.float64)


# ---------------------------------------------------------------------------
# FFT reconstruction
# ---------------------------------------------------------------------------

class TestFFTReconstruction:
    def test_output_shape(self, synthetic_kspace):
        image = kspace_to_image(synthetic_kspace)
        assert image.shape == synthetic_kspace.shape

    def test_output_is_complex(self, synthetic_kspace):
        image = kspace_to_image(synthetic_kspace)
        assert np.iscomplexobj(image)

    def test_magnitude_non_negative(self, synthetic_kspace):
        image = kspace_to_image(synthetic_kspace)
        assert np.all(get_magnitude(image) >= 0)

    def test_phase_within_range(self, synthetic_kspace):
        image = kspace_to_image(synthetic_kspace)
        phase = get_phase(image)
        assert phase.min() >= -np.pi - 1e-10
        assert phase.max() <= np.pi + 1e-10

    def test_roundtrip_consistency(self, synthetic_kspace):
        """ifft2(kspace) → fft2 should recover the original kspace exactly."""
        image = kspace_to_image(synthetic_kspace)
        recovered = np.fft.fft2(image)
        np.testing.assert_allclose(
            np.abs(recovered), np.abs(synthetic_kspace), atol=1e-8
        )


# ---------------------------------------------------------------------------
# Coil combination
# ---------------------------------------------------------------------------

class TestCoilCombination:
    def test_rss_output_shape(self, synthetic_multi_coil):
        combined = combine_coils_rss(synthetic_multi_coil, coil_axis=0)
        assert combined.shape == (64, 64)

    def test_rss_non_negative(self, synthetic_multi_coil):
        combined = combine_coils_rss(synthetic_multi_coil, coil_axis=0)
        assert np.all(combined >= 0)

    def test_rss_formula_correctness(self):
        """Verify RSS against hand-computed values."""
        coil1 = np.array([[3.0, 0.0]])
        coil2 = np.array([[4.0, 0.0]])
        coils = np.stack([coil1, coil2], axis=0)  # shape (2, 1, 2)
        combined = combine_coils_rss(coils, coil_axis=0)
        np.testing.assert_allclose(combined, [[5.0, 0.0]])

    def test_rss_larger_than_any_single_coil(self, synthetic_multi_coil):
        combined = combine_coils_rss(synthetic_multi_coil, coil_axis=0)
        for i in range(synthetic_multi_coil.shape[0]):
            coil_mag = np.abs(synthetic_multi_coil[i])
            assert np.all(combined >= coil_mag - 1e-10)

    def test_snr_normalise_reduces_scale(self):
        """SNR normalisation divides by noise std, reducing magnitude."""
        rng = np.random.default_rng(0)
        img = rng.random((64, 64)) * 100
        normalised = normalise_coil_by_noise(img, noise_rows=3)
        # After normalisation, values should be smaller (divided by std > 1)
        assert normalised.max() < img.max()

    def test_rss_snr_shape(self, synthetic_multi_coil):
        mags = np.abs(synthetic_multi_coil)
        combined = combine_coils_rss_snr(mags, coil_axis=0, noise_rows=3)
        assert combined.shape == (64, 64)

    def test_rss_snr_non_negative(self, synthetic_multi_coil):
        mags = np.abs(synthetic_multi_coil)
        combined = combine_coils_rss_snr(mags, coil_axis=0)
        assert np.all(combined >= 0)


# ---------------------------------------------------------------------------
# Butterworth filter
# ---------------------------------------------------------------------------

class TestButterworthFilter:
    def test_mask_shape(self):
        H = butterworth_lowpass_filter((64, 64), D0=30, n=2)
        assert H.shape == (64, 64)

    def test_mask_values_in_range(self):
        H = butterworth_lowpass_filter((64, 64), D0=30, n=2)
        assert H.min() > 0.0
        assert H.max() <= 1.0

    def test_centre_is_one(self):
        """DC component at centre should pass through unattenuated."""
        H = butterworth_lowpass_filter((64, 64), D0=30, n=2)
        assert H[32, 32] == pytest.approx(1.0)

    def test_higher_order_steeper_rolloff(self):
        H2 = butterworth_lowpass_filter((64, 64), D0=20, n=2)
        H8 = butterworth_lowpass_filter((64, 64), D0=20, n=8)
        # Away from centre, higher order filter should attenuate more
        assert H8[0, 0] < H2[0, 0]

    def test_apply_filter_shape_preserved(self, synthetic_kspace):
        filtered = apply_butterworth_filter(synthetic_kspace, D0=30, n=2)
        assert filtered.shape == synthetic_kspace.shape

    def test_apply_filter_is_complex(self, synthetic_kspace):
        filtered = apply_butterworth_filter(synthetic_kspace, D0=30, n=2)
        assert np.iscomplexobj(filtered)

    def test_low_cutoff_reduces_energy(self, synthetic_kspace):
        """Aggressive low-pass filter should reduce total k-space energy."""
        filtered = apply_butterworth_filter(synthetic_kspace, D0=5, n=4)
        assert np.sum(np.abs(filtered) ** 2) < np.sum(np.abs(synthetic_kspace) ** 2)


# ---------------------------------------------------------------------------
# Denoising filters
# ---------------------------------------------------------------------------

class TestDenoisingFilters:
    def test_gaussian_shape(self, test_image):
        result = apply_gaussian_filter(test_image, sigma=1.0)
        assert result.shape == test_image.shape

    def test_mean_shape(self, test_image):
        result = apply_mean_filter(test_image, size=3)
        assert result.shape == test_image.shape

    def test_median_shape(self, test_image):
        result = apply_median_filter(test_image, size=3)
        assert result.shape == test_image.shape

    def test_median_removes_salt_and_pepper(self, test_image):
        """Median filter should suppress isolated spike noise."""
        corrupted = test_image.copy()
        corrupted[32, 32] = 1e6  # single spike
        result = apply_median_filter(corrupted, size=3)
        assert result[32, 32] < 1e6

    def test_median_reduces_std(self, test_image):
        result = apply_median_filter(test_image, size=5)
        assert result.std() < test_image.std()

    def test_bilateral_shape(self, test_image):
        result = apply_bilateral_filter(test_image)
        assert result.shape == test_image.shape

    def test_gaussian_reduces_std(self, test_image):
        """Gaussian smoothing should reduce pixel variance."""
        result = apply_gaussian_filter(test_image, sigma=3.0)
        assert result.std() < test_image.std()

    def test_mean_reduces_std(self, test_image):
        result = apply_mean_filter(test_image, size=5)
        assert result.std() < test_image.std()

    def test_bilateral_preserves_range(self, test_image):
        result = apply_bilateral_filter(test_image)
        assert result.min() >= test_image.min() - 1e-6
        assert result.max() <= test_image.max() + 1e-6


# ---------------------------------------------------------------------------
# Coil dimension identification
# ---------------------------------------------------------------------------

class TestCoilDimension:
    def test_identifies_smallest_axis(self):
        kspace = np.zeros((6, 280, 280), dtype=complex)
        assert identify_coil_dimension(kspace) == 0

    def test_last_axis(self):
        kspace = np.zeros((280, 280, 6), dtype=complex)
        assert identify_coil_dimension(kspace) == 2
