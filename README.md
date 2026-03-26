# Data Science in Medical Imaging — Coursework

MPhil in Data Intensive Science · Coursework Minor A2
University of Cambridge · Submission: 23:59 Wednesday 1 April 2026

---

## What this repository implements

| Module | Topic | Notebook |
|--------|-------|----------|
| 1 | CT tomographic reconstruction (dose reduction, limited-angle, FBP filters, iterative methods) | `notebooks/exercise_1.1.ipynb`, `notebooks/exercise_1.2.ipynb`, `notebooks/exercise_1.3.ipynb` |
| 2 | MRI k-space visualisation, reconstruction, and denoising | `notebooks/exercise_2.1_2.2.ipynb` |
| 3 | Image segmentation literature review | Written report only — no AI |

---

## Module 1 — CT Tomographic Reconstruction

### Algorithms

**Forward projection** uses the Radon transform (`skimage.transform.radon`) to generate sinograms from a Shepp-Logan phantom or a CT chest image.

**Noise model** applies Poisson noise in the transmission domain (Beer-Lambert model) followed by additive Gaussian detector noise:
```
I = I₀ exp(−p),   I_noisy ~ Poisson(I + N(0,σ²)),   p_noisy = −log(I_noisy / I₀)
```

**Filtered Backprojection (FBP)** reconstructs via `skimage.transform.iradon` with a selectable ramp filter (Ram-Lak, Shepp-Logan, Cosine, Hamming, Hann).

**Gradient Descent (SIRT-style)** iteratively minimises the sinogram residual:
```
x_{k+1} = x_k − γ · Aᵀ(Ax_k − b)
```
running for up to 200 iterations with `γ = 0.001`.

**Subset GD (OS-SART-style)** splits the 360 projections into S = 10 ordered subsets and performs one update per subset per epoch, yielding S updates per epoch.

### Key results

Exercise 1.1 evaluates dose levels I₀ ∈ {10⁵, 10³, 10²} and projection counts {360, 90, 20}:

| Condition | FBP PSNR | GD PSNR |
|-----------|----------|---------|
| I₀=10⁵, 360 views | **38.8 dB** | 32.8 dB |
| I₀=10³, 360 views | 22.4 dB | **30.1 dB** |
| I₀=10², 360 views | 12.3 dB | **23.5 dB** |
| I₀=10², 20 views  | −0.4 dB | **17.0 dB** |

FBP wins only at maximum dose and full sampling; GD is substantially more robust to both noise and undersampling.

Exercise 1.2 tests angular ranges {180°, 120°, 40°} at fixed 360 projections. The missing-wedge artefact (Fourier Slice Theorem) causes directional elongation at 40°. GD retains 19.3 dB vs FBP's 13.8 dB at I₀=10⁵.

Exercise 1.3 compares FBP filters at I₀=10², 360 views: ramp 12.3 dB, Shepp-Logan 14.2 dB, Hamming 20.0 dB. The early-convergence study shows subset GD reaches the 100-epoch full-batch solution quality in only 10 epochs when the per-subset step size is kept at `γ = 0.001`.

---

## Module 2 — MRI k-Space and Denoising

### Dataset

`knee.npy` — complex MRI k-space from a knee acquisition.
Shape `(6, 280, 280)`, dtype `complex128`. Axis 0 is the coil dimension (6 receiver elements); axes 1–2 are the 280 × 280 spatial k-space grid. The DC component is stored at the **array centre** (confirmed by locating the maximum |k| in each coil: all within 1.4 px of centre).

### Reconstruction (Exercise 2.1)

Because the data are centred, reconstruction uses `ifft2(ifftshift(k))` — `ifftshift` moves DC from the array centre to index `[0,0]` before the inverse transform. Plain `ifft2` without the shift would produce a quadrant-swapped image.

**Root-sum-of-squares (RSS) coil combination:**
```
I_RSS(x,y) = sqrt( sum_c |I_c(x,y)|² ),   N_c = 6
```
The RSS image provides more uniform spatial coverage than any individual coil.

### Denoising (Exercise 2.2)

**Image-space methods** are applied to the reconstructed coil magnitude images `|I_c|`:

| Method | Parameters | Background std (coil 0) |
|--------|-----------|------------------------|
| Original | — | 0.052 |
| Median filter | 3 × 3 window | 0.033 |
| Gaussian filter | σ = 1.0 px | 0.028 |
| Bilateral filter | σ_spatial = 3.0 px, σ_color = 0.05 | 0.029 |

Background std is measured from four 20 × 20 corner ROIs — a smoothing proxy, not a physical SNR. Central-region mean is preserved by all three filters (< 0.4% change), confirming no signal suppression in the anatomy.

Gaussian gives the strongest uniform smoothing. On the final RSS-combined images, Gaussian-then-RSS gives the lowest corner-ROI background standard deviation, median-then-RSS gives a milder reduction, and bilateral-then-RSS retains a higher mean gradient but does not reduce this background proxy relative to the original RSS image. These are descriptive image statistics rather than ground-truth quality metrics.

**Butterworth k-space filter** (Exercise 2.2, Part b) applied to the original noisy k-space of coil 0:
```
H(u,v) = 1 / (1 + (D(u,v) / D₀)^{2n}),   D₀ = 30 px,   n = 2
```
where `u, v` are pixel offsets from the k-space centre. The mask is multiplied directly with the centred k-space (no additional shift needed); reconstruction then uses `ifft2(ifftshift(·))`. The filter passes H = 1.0 at the centre, H = 0.5 at D = 30 px, and H ≈ 0.0005 at the corners. Unlike image-space methods, the filter operates on the complex signal before magnitude formation, so both magnitude and phase of the reconstruction are affected.

**Denoise-then-combine** (Exercise 2.2, Part c): each of the three image-space methods is applied to all six coil magnitude images independently before RSS combination, keeping the per-coil noise suppression separate from the nonlinear combination step.

---

## Repository structure

```
.
├── ct_reconstruction/          # Module 1 — CT support library
│   └── phantom.py              # Shepp-Logan phantom and CT image loader
│
├── mri_denoising/              # Module 2 — MRI support library
│   ├── load_kspace.py          # Load knee.npy; identify coil dimension
│   ├── reconstruction_fft.py   # ifft2 and ifft2(ifftshift·) reconstruction
│   ├── coil_combination.py     # RSS and SNR-normalised RSS combination
│   ├── denoising_filters.py    # Gaussian, mean, median, bilateral filters
│   ├── butterworth_filter.py   # Butterworth low-pass k-space mask
│   └── kspace_visualization.py # k-space and image plotting helpers
│
├── tests/
│   └── test_mri.py             # 30 unit tests for the MRI module
│
├── notebooks/                  # Exercise notebooks, export scripts, and report_figures/
│
├── .github/workflows/ci.yml    # GitHub Actions CI (lint + test)
├── pyproject.toml              # Project metadata and tool configuration
├── requirements.txt            # Pinned runtime dependencies
├── requirements-notebooks.txt  # Jupyter/notebook extras
├── Dockerfile                  # Reproducible container environment
├── report.txt                  # Coursework report source
├── CONTRIBUTING.md
└── LICENSE
```

---

## Installation

### Option 1 — local Python environment

```bash
python3.10 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -e .
```

Optional notebook support:

```bash
pip install -r requirements-notebooks.txt
```

### Option 2 — Docker

```bash
docker build -t medical-imaging .
docker run --rm medical-imaging pytest tests/ -v   # run test suite
docker run --rm -it medical-imaging bash           # interactive shell
```

---

## Running the notebooks

```bash
pip install -r requirements-notebooks.txt
jupyter lab
```

Open the relevant notebook under `notebooks/`. Report figures are stored under `notebooks/report_figures/`.

For reproducible report-figure export, helper scripts are provided:

```bash
cd notebooks
../.venv/bin/python save_ex11_figures.py
../.venv/bin/python save_ex12_figures.py
../.venv/bin/python save_ex21_ex22_figures.py
```

Exercise 1.3 and Exercise 2.1/2.2 also include in-notebook figure-saving helpers that write under `notebooks/report_figures/` when the relevant cells are run.

---

## Running the tests

```bash
pytest tests/ -v                          # all 30 MRI tests
pytest tests/ --cov=mri_denoising --cov-report=term-missing
```

---

## Reproducibility

All notebooks set `np.random.seed(42)`. Results are fully deterministic given the same Python and library versions.

Verified with: Python 3.10.5 · numpy 2.2.6 · scipy 1.15.3 · scikit-image 0.25.2 · matplotlib 3.10.8

---

## Data files

| File | Description |
|------|-------------|
| `knee.npy` | Multi-coil MRI k-space, shape (6, 280, 280), complex128, DC centred |
| `CT_exercise_1.png` | CT chest image used in Module 1 experiments |

---

## Module 3 note

All written content in `report.txt` for the literature-review section is original student work. Generative AI was not used for that section per the coursework specification.
