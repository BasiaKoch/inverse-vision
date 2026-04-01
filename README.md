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

**Noise model** first normalises each clean sinogram by its maximum value, maps
it into the transmission domain with the Beer-Lambert model, adds Gaussian
detector noise, clips to positive intensity, then applies Poisson sampling:
```
I = I₀ exp(−p_norm),   I_g = I + N(0,σ²),   I_noisy ~ Poisson(max(I_g, ε)),   p_noisy = −log(I_noisy / I₀) · p_max
```

**Filtered Backprojection (FBP)** reconstructs via `skimage.transform.iradon` with a selectable ramp filter (Ram-Lak, Shepp-Logan, Cosine, Hamming, Hann).

**Gradient Descent (Landweber-style least squares)** iteratively minimises the
least-squares data term:
```
x_{k+1} = x_k − γ · Aᵀ(Ax_k − b)
```
running for up to 200 iterations with `γ = 0.001`.

**Subset GD** splits the 360 projections into `S = 10` interleaved subsets and
performs one sequential update per subset per epoch. This is best thought of as
mini-batch / ordered-subset gradient descent rather than fully normalised
OS-SART.

### What the Notebooks Show

**Exercise 1.1** compares FBP with full-batch gradient descent across
dose levels `I₀ ∈ {10⁵, 10³, 10²}` and view counts `{360, 90, 20}`. The
notebooks and report figures show that gradient descent is consistently more
robust than FBP as dose and angular sampling are reduced, while FBP remains
competitive only in the highest-quality acquisition setting.

**Exercise 1.2** fixes the number of projections at 360 and reduces the angular
range to `{180°, 120°, 40°}`. The main effect is no longer just extra noise but
directional blur and elongation caused by the missing wedge in Fourier space.

**Exercise 1.3** has two separate implementation studies:

- Part (b) compares several FBP filters on the same low-dose example. In this
  repo, the Hamming window gives the strongest smoothing and the best scalar
  metrics on that chosen example, while the ramp filter stays sharpest and
  noisiest.
- Part (c) compares full-batch GD with subset GD. With a per-subset step
  `γ / S`, subset GD closely tracks the full-batch method; with an unscaled
  per-subset step `γ`, it converges much faster initially but becomes unstable
  later.

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

**Image-space methods** are applied to the reconstructed coil magnitude images
`|I_c|`:

| Method | Parameters | Local std (coil 0 ROI) |
|--------|-----------|------------------------|
| Original | — | 0.038 |
| Median filter | 3 × 3 window | 0.016 |
| Gaussian filter | σ = 1.0 px | 0.011 |
| Bilateral filter | σ_spatial = 3.0 px, σ_color = 0.05 | 0.004 |

The numeric comparison is deliberately simple: local standard deviation is measured on one fixed 20 × 20 low-signal ROI in representative coil 0 (rows `250:270`, cols `30:50`). This is a local smoothing proxy, not a physical SNR estimate.

Visual inspection across all coils remains the main comparison. Gaussian gives the strongest broad smoothing but also the most blur; median is more moderate; bilateral preserves boundaries better and, in the selected low-signal ROI, gives the lowest local variation. For the final RSS-combined images, the comparison is kept visual on a shared scale rather than relying on a potentially misleading single global metric.

**Butterworth k-space filter** (Exercise 2.2, Part b) applied to the original noisy k-space of coil 0:
```
H(u,v) = 1 / (1 + (D(u,v) / D₀)^{2n}),   D₀ = 30 px,   n = 2
```
where `u, v` are pixel offsets from the k-space centre. The mask is multiplied directly with the centred k-space (no additional shift needed); reconstruction then uses `ifft2(ifftshift(·))`. The filter passes H = 1.0 at the centre, H = 0.5 at D = 30 px, and H ≈ 0.0005 at the corners. Unlike image-space methods, the filter operates on the complex signal before magnitude formation, so both magnitude and phase of the reconstruction are affected.

**Denoise-then-combine** (Exercise 2.2, Part c): each of the three image-space
methods is applied to all six coil magnitude images independently before RSS
combination. The final combined image highlighted in the report uses the
bilateral filter, with the median and Gaussian pipelines retained for visual
comparison.

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
├── tests/                      # Unit tests for CT and MRI support code
├── docs/                       # Sphinx configuration and API reference
│
├── notebooks/                  # Exercise notebooks, export scripts, and report_figures/
│
├── .github/workflows/ci.yml    # GitHub Actions CI (lint + test + docs)
├── Makefile                    # Convenience targets for lint/test/docs
├── pyproject.toml              # Project metadata and tool configuration
├── requirements.txt            # Pinned runtime dependencies
├── requirements-notebooks.txt  # Jupyter/notebook extras
├── Dockerfile                  # Reproducible container environment
├── report.txt                  # LaTeX coursework report source
├── CONTRIBUTING.md
└── LICENSE
```

---

## Installation

### Option 1 — local Python environment

```bash
python3.10 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install -e .
```

Optional development, docs, and notebook support:

```bash
python -m pip install -e ".[dev]"
python -m pip install -e ".[docs]"
python -m pip install -r requirements-notebooks.txt
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
python -m pip install -r requirements-notebooks.txt
jupyter lab
```

Open the relevant notebook under `notebooks/`. Report figures are written under
`notebooks/report_figures/`.

For reproducible report-figure export, helper scripts are provided:

```bash
cd notebooks
../.venv/bin/python save_ex11_figures.py
../.venv/bin/python save_ex12_figures.py
../.venv/bin/python save_ex21_ex22_figures.py
```

Exercise 1.3 and Exercise 2.1/2.2 also include in-notebook figure-saving
helpers that write under `notebooks/report_figures/` when the relevant cells are
run.

---

## Running the tests

```bash
pytest tests/ -v                          # full CT + MRI test suite
pytest tests/ --cov=ct_reconstruction --cov=mri_denoising --cov-report=term-missing
```

Convenience targets are also provided:

```bash
make lint
make test
make coverage
```

## Building the API docs

The support-library modules use NumPy-style docstrings and can be built with
Sphinx:

```bash
python -m pip install -e ".[docs]"
make docs
```

The generated HTML documentation is written to `docs/_build/html/`.

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

## Use of AI

AI was used to support the implementation of the code in this repository, based on my own logic, design choices, and understanding of the coursework tasks. In particular, it was used to help implement functions from my planned approach, improve documentation through Markdown text and docstrings, and assist with debugging during development.

For Module 3, I found the articles myself, read them, analysed them, and wrote my own conclusions and views. AI was not used to generate the literature-review content and was only used to help check grammar.

---

## Development workflow

- Create feature branches for new work instead of committing directly to `main`.
- Install local hooks with `pre-commit install` and
  `pre-commit install --hook-type pre-push`.
- GitHub Actions validates linting, formatting, tests, and docs on pushes and
  pull requests targeting `main`.
