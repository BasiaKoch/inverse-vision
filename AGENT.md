# AGENT.md
# Medical Imaging Coursework – Agent Operating Guide

This document defines the operational rules for AI agents or contributors working on this repository.

The goal of the project is to implement algorithms and experiments for **medical image reconstruction, MRI denoising, and segmentation analysis** as defined in the coursework specification.

Agents must strictly follow the rules in this document to ensure correctness, reproducibility, and high-quality software engineering practices.

---

# 1. Project Overview

This repository implements three modules:

## Module 1 – CT Tomographic Reconstruction
Focus areas:
- Radon transform (forward projection)
- Sinogram simulation
- Noise modelling (Poisson + Gaussian)
- Reconstruction algorithms
- Dose reduction experiments
- Limited-angle tomography
- Filtered Backprojection (FBP)
- Iterative reconstruction (SIRT / OS-SART)

## Module 2 – MRI Image Denoising
Focus areas:
- k-space visualization
- Fourier reconstruction
- multi-coil MRI processing
- coil combination
- spatial-domain denoising
- frequency-domain filtering

## Module 3 – Segmentation Literature Review
Focus areas:
- analysis of classical segmentation methods
- analysis of ML/DL segmentation methods
- methodological comparison
- proposal of improved approach

IMPORTANT:
Agents **must not generate content for Module 3 automatically**, as generative AI is not allowed for that exercise.

---

# 2. Repository Structure

Agents must maintain the following structure.


medical-imaging-coursework/

README.md
AGENT.md

configs/
ct_experiments.yaml
mri_denoising.yaml

ct_reconstruction/
phantom.py
forward_projection.py
sinogram.py
noise_models.py
reconstruction_fbp.py
reconstruction_iterative.py
filters.py
evaluation_metrics.py

mri_denoising/
load_kspace.py
kspace_visualization.py
reconstruction_fft.py
coil_combination.py
denoising_filters.py
butterworth_filter.py

segmentation_review/
paper_analysis.md

experiments/
run_ct_experiments.py
run_mri_experiments.py

tests/
test_ct.py
test_mri.py

report/
coursework_report.pdf


Agents must not create unnecessary files.

---

# 3. Environment Setup

The codebase must run with the following environment.

Python version:

= Python 3.10


Required libraries:


numpy
scipy
scikit-image
matplotlib
pandas
pytest
tqdm


Optional (advanced experiments):


torch
opencv-python
pywavelets


Agents must ensure the repository includes:


requirements.txt


---

# 4. Coding Standards

Agents must follow these rules.

### Style
- PEP8 compliant
- modular functions
- clear naming
- no hard-coded paths

### Documentation
Every function must include a docstring:


Parameters
Returns
Description


Example:

```python
def simulate_sinogram(image, angles):
    """
    Generate CT sinogram using Radon transform.

    Parameters
    ----------
    image : ndarray
        Input phantom image

    angles : ndarray
        Projection angles

    Returns
    -------
    ndarray
        Generated sinogram
    """
Reproducibility

All experiments must set seeds:

np.random.seed(42)
5. Experiment Configuration

Agents must use YAML configuration files for experiments.

Example:

configs/ct_experiments.yaml

dose_levels:
  - 1e5
  - 1e3
  - 1e2

projection_counts:
  - 360
  - 90
  - 20

noise:
  gaussian_sigma: 0.05

MRI configuration:

configs/mri_denoising.yaml

filters:
  - gaussian
  - bilateral
  - mean

butterworth:
  cutoff: 30
  order: 2

Agents must load configuration dynamically.

6. Module 1 – CT Reconstruction
6.1 Phantom Generation

Use the Shepp-Logan phantom from scikit-image.

from skimage.data import shepp_logan_phantom

Resize if needed using:

skimage.transform.resize
6.2 Forward Projection (Radon Transform)

Compute sinograms using:

skimage.transform.radon

Inputs:

image

projection angles

Output:

sinogram

Angles must be configurable.

Example:

theta = np.linspace(0, 180, num_projections)
6.3 Noise Simulation

Two noise sources must be implemented.

Poisson Noise (Photon Noise)

Simulate photon detection:

I = I0 * exp(-sinogram)
I_noisy = Poisson(I)

Convert back to absorption domain:

p = -log(I_noisy / I0)
Gaussian Noise

Detector electronic noise:

noise ~ N(0, σ)

Add to sinogram.

6.4 Reconstruction Algorithms
Filtered Backprojection

Use:

skimage.transform.iradon

Filters to support:

Ram-Lak
Shepp-Logan
Cosine

Agents must allow switching filters via configuration.

Iterative Reconstruction (SIRT)

Implement update rule:

x_{k+1} = x_k − γ Aᵀ(Ax − b)

Where:

γ ≈ 0.001

Stop after configurable number of iterations.

OS-SART

Split projections into batches.

Update image after each batch.

This accelerates convergence compared to SIRT.

7. Module 1 Experiments

Agents must evaluate:

Dose levels:

I0 = 1e5
I0 = 1e3
I0 = 1e2

Projection counts:

360
90
20

Limited-angle tomography:

180°
120°
40°

For each experiment compute:

MSE
PSNR
SSIM

Save reconstruction images.

8. Module 2 – MRI Processing
8.1 Load k-space

Load dataset:

kspace = np.load("kspace.npy")

Identify coil dimension.

8.2 Visualization

Plot magnitude:

np.log1p(abs(kspace))
8.3 Image Reconstruction

Apply inverse FFT:

image = np.fft.ifft2(kspace)

Compute:

magnitude
phase
8.4 Coil Combination

Use Root Sum of Squares (RSS):

combined = sqrt(sum(|coil_image|^2))
8.5 Image-Space Denoising

Implement at least three filters:

Gaussian filter
Mean filter
Bilateral filter
Wavelet denoising (optional)

Evaluate visually and numerically.

8.6 k-space Filtering

Apply Butterworth low-pass filter.

Definition:

H = 1 / (1 + (D/D0)^(2n))

Steps:

generate frequency mask

multiply with k-space

inverse FFT

Compare with spatial filtering.

9. Evaluation Metrics

Implement functions for:

MSE
PSNR
SSIM

Example:

from skimage.metrics import structural_similarity
10. Experiment Logging

Agents must store results in:

results/

Include:

images
metrics.csv
plots

Example structure:

results/
   ct_reconstruction/
   mri_denoising/
11. Visualization Requirements

All experiments must produce plots.

Examples:

phantom image
sinogram
reconstructed images
noise comparisons
MRI magnitude images
denoising comparisons

Use:

matplotlib
12. Testing

Agents must implement unit tests.

Test coverage must include:

radon transform wrapper
noise simulation
reconstruction outputs
MRI FFT reconstruction
coil combination

Use:

pytest
13. Reproducibility Rules

Agents must ensure:

fixed random seeds
config-based experiments
deterministic pipelines
14. Performance Considerations

Avoid:

explicit large matrices for Radon operator

Instead compute operators implicitly using library functions.

15. Key Concepts Agents Must Understand

CT Imaging:

Radon transform
sinogram
Beer-Lambert law
filtered backprojection
iterative reconstruction
regularization

MRI Imaging:

k-space
Fourier transform
coil combination
frequency filtering

Image Processing:

noise models
denoising filters
image quality metrics
16. Deliverables

The repository must contain:

clean Python code
experiment scripts
figures
unit tests
documentation
coursework report

All results must be reproducible from code.

End of Agent Instructions

