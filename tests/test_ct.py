"""
Unit tests for the CT reconstruction module.

Run with:
    pytest tests/test_ct.py -v
"""

import numpy as np
import pytest
from PIL import Image

from ct_reconstruction.phantom import load_ct_image, load_shepp_logan

# ---------------------------------------------------------------------------
# Shepp-Logan phantom
# ---------------------------------------------------------------------------


class TestLoadSheppLogan:
    def test_default_shape(self):
        """skimage default Shepp-Logan is 400×400."""
        img = load_shepp_logan()
        assert img.shape == (400, 400)

    def test_resized_shape(self):
        img = load_shepp_logan(size=128)
        assert img.shape == (128, 128)

    def test_square_output(self):
        img = load_shepp_logan(size=64)
        assert img.ndim == 2
        assert img.shape[0] == img.shape[1]

    def test_values_in_range(self):
        img = load_shepp_logan()
        assert img.min() >= 0.0
        assert img.max() <= 1.0

    def test_dtype_float64(self):
        img = load_shepp_logan()
        assert img.dtype == np.float64

    def test_none_size_preserves_original(self):
        img = load_shepp_logan(size=None)
        assert img.shape == (400, 400)

    def test_non_trivial_content(self):
        """Phantom should not be a blank image — it contains internal structures."""
        img = load_shepp_logan()
        assert img.max() > img.min()


# ---------------------------------------------------------------------------
# CT image loader
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_gray_png(tmp_path):
    """8-bit grayscale PNG with known pixel values."""
    arr = np.array([[0, 128], [255, 64]], dtype=np.uint8)
    path = tmp_path / "gray.png"
    Image.fromarray(arr, mode="L").save(path)
    return path


@pytest.fixture()
def tmp_rgb_png(tmp_path):
    """24-bit RGB PNG (3 channels)."""
    arr = np.zeros((16, 16, 3), dtype=np.uint8)
    arr[..., 0] = 200  # red channel only
    path = tmp_path / "rgb.png"
    Image.fromarray(arr, mode="RGB").save(path)
    return path


@pytest.fixture()
def tmp_rgba_png(tmp_path):
    """32-bit RGBA PNG (4 channels)."""
    arr = np.zeros((16, 16, 4), dtype=np.uint8)
    arr[..., 1] = 150  # green channel
    arr[..., 3] = 255  # fully opaque alpha
    path = tmp_path / "rgba.png"
    Image.fromarray(arr, mode="RGBA").save(path)
    return path


class TestLoadCtImage:
    def test_output_values_normalized(self, tmp_gray_png):
        """Output should lie in [0, 1]."""
        img = load_ct_image(tmp_gray_png)
        assert img.min() >= 0.0
        assert img.max() <= 1.0

    def test_dtype_float64(self, tmp_gray_png):
        img = load_ct_image(tmp_gray_png)
        assert img.dtype == np.float64

    def test_grayscale_input_shape_preserved(self, tmp_gray_png):
        img = load_ct_image(tmp_gray_png)
        assert img.shape == (2, 2)

    def test_resize(self, tmp_gray_png):
        img = load_ct_image(tmp_gray_png, size=64)
        assert img.shape == (64, 64)

    def test_rgb_converted_to_2d(self, tmp_rgb_png):
        img = load_ct_image(tmp_rgb_png)
        assert img.ndim == 2

    def test_rgba_converted_to_2d(self, tmp_rgba_png):
        """RGBA images should be stripped of alpha and converted to grayscale."""
        img = load_ct_image(tmp_rgba_png)
        assert img.ndim == 2

    def test_max_equals_one(self, tmp_gray_png):
        """Max pixel in a non-constant image should map to exactly 1.0."""
        img = load_ct_image(tmp_gray_png)
        assert img.max() == pytest.approx(1.0)

    def test_min_equals_zero(self, tmp_gray_png):
        """Min pixel in a non-constant image should map to exactly 0.0."""
        img = load_ct_image(tmp_gray_png)
        assert img.min() == pytest.approx(0.0)

    def test_accepts_string_path(self, tmp_gray_png):
        img = load_ct_image(str(tmp_gray_png))
        assert img.ndim == 2

    def test_accepts_pathlib_path(self, tmp_gray_png):
        img = load_ct_image(tmp_gray_png)
        assert img.ndim == 2
