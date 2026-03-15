# Data Science in Medical Imaging — Coursework

MPhil in Data Intensive Science · Coursework Minor A2
University of Cambridge · Submission: 23:59 Wednesday 1 April 2026

---

## Project overview

This repository implements two computational modules for medical image reconstruction
and denoising, plus a written literature review:

| Module | Topic | Exercises |
|--------|-------|-----------|
| 1 | CT Tomographic Reconstruction | 1.1 Dose reduction · 1.2 Limited-angle · 1.3 Filters & iterative methods |
| 2 | MRI Image Denoising | 2.1 k-space visualisation & reconstruction · 2.2 Spatial & k-space denoising |
| 3 | Image Segmentation Literature Review | Written only — no AI assistance |

---

## Repository structure

```
.
├── ct_reconstruction/          # Module 1 — CT algorithms
│   ├── phantom.py              # Shepp-Logan phantom / load CT PNG
│   ├── forward_projection.py   # Radon transform wrapper
│   ├── sinogram.py             # Sinogram simulation (noise included)
│   ├── noise_models.py         # Poisson + Gaussian noise
│   ├── reconstruction_fbp.py   # Filtered Backprojection (FBP)
│   ├── reconstruction_iterative.py  # SIRT and OS-SART
│   ├── filters.py              # FBP filter names & validation
│   └── evaluation_metrics.py  # MSE, PSNR, SSIM
│
├── mri_denoising/              # Module 2 — MRI algorithms
│   ├── load_kspace.py          # Load knee.npy k-space data
│   ├── kspace_visualization.py # k-space and image plotting
│   ├── reconstruction_fft.py   # Inverse FFT reconstruction
│   ├── coil_combination.py     # Root Sum of Squares (RSS)
│   ├── denoising_filters.py    # Gaussian, mean, bilateral filters
│   └── butterworth_filter.py   # Butterworth low-pass k-space filter
│
├── experiments/
│   ├── run_ct_experiments.py   # Reproduce all Module 1 results
│   └── run_mri_experiments.py  # Reproduce all Module 2 results
│
├── tests/
│   ├── test_ct.py              # Unit tests for CT module
│   └── test_mri.py             # Unit tests for MRI module
│
├── notebooks/
│   ├── module1_ct_analysis.ipynb    # Interactive CT experiments
│   └── module2_mri_analysis.ipynb  # Interactive MRI experiments
│
├── configs/
│   ├── ct_experiments.yaml     # CT experiment parameters
│   └── mri_denoising.yaml      # MRI denoising parameters
│
├── segmentation_review/
│   └── paper_analysis.md       # Module 3 written analysis (no AI)
│
├── results/                    # Generated output (gitignored large files)
│   ├── ct_reconstruction/
│   └── mri_denoising/
│
├── report/                     # Final PDF report (place here)
├── requirements.txt
└── Dockerfile
```

---

## Installation

### Option 1 — local Python environment

The project has been tested in a fresh **Python 3.10** virtual environment.
The exact package versions used for the passing test run are pinned in
`requirements.txt`.

```bash
# Create and activate a virtual environment with Python 3.10
python3.10 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Upgrade packaging tools
python -m pip install --upgrade pip setuptools wheel

# Install the tested dependency set
pip install -r requirements.txt

# Make the source packages importable from the repo root
pip install -e .
```

Optional notebook support:

```bash
pip install -r requirements-notebooks.txt
```

### Option 2 — Docker (recommended for reproducibility)

```bash
docker build -t medical-imaging .
docker run --rm -v $(pwd):/app medical-imaging python experiments/run_ct_experiments.py
```

---

## Running the experiments

### Module 1 — CT reconstruction

```bash
# Using the Shepp-Logan phantom (default)
python experiments/run_ct_experiments.py

# Using the provided CT chest image
python experiments/run_ct_experiments.py --phantom CT_exercise_1.png

# Custom config
python experiments/run_ct_experiments.py --config configs/ct_experiments.yaml
```

Results are saved to `results/ct_reconstruction/`:
- `images/` — reconstruction images for every experiment
- `metrics.csv` — MSE, PSNR, SSIM for all combinations

### Module 2 — MRI denoising

```bash
python experiments/run_mri_experiments.py --kspace knee.npy
```

Results are saved to `results/mri_denoising/images/`.

---

## Running the notebooks

```bash
jupyter lab
```

Open `notebooks/module1_ct_analysis.ipynb` or `notebooks/module2_mri_analysis.ipynb`.
Install `requirements-notebooks.txt` first if you want a local Jupyter environment.

---

## Running the tests

```bash
# All tests
pytest tests/ -v

# CT tests only
pytest tests/test_ct.py -v

# MRI tests only
pytest tests/test_mri.py -v

# With coverage report
pytest tests/ --cov=ct_reconstruction --cov=mri_denoising --cov-report=term-missing
```

---

## Experiment configuration

All experiment parameters live in `configs/`. Edit these files to change:

- `ct_experiments.yaml` — dose levels, projection counts, angular ranges, noise sigma,
  filter list, SIRT/OS-SART hyperparameters, phantom size
- `mri_denoising.yaml` — denoising filter list, Gaussian sigma, Butterworth cutoff/order

---

## Reproducibility

All experiments call `np.random.seed(42)` at startup. Results are fully deterministic
given the same Python/library versions.

Recommended reproduction flow:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pytest tests -v
```

The project was verified with:

- Python 3.10.5
- numpy 2.2.6
- scipy 1.15.3
- scikit-image 0.25.2
- matplotlib 3.10.8
- pandas 2.3.3
- PyYAML 6.0.3
- tqdm 4.67.3
- pytest 9.0.2

---

## Data files

| File | Description |
|------|-------------|
| `knee.npy` | 3D MRI k-space data, shape (6, 280, 280), complex128, 6 coils |
| `CT_exercise_1.png` | CT chest image for Module 1 experiments |

---

## Notes on Module 3

`segmentation_review/paper_analysis.md` is a **template only**. All written content
must be your own original analysis. Generative AI must not be used for this module.
