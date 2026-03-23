"""
Save all report figures for Exercises 2.1 and 2.2.
Run from the notebooks/ directory:
    ../.venv/bin/python save_ex21_ex22_figures.py

Exercise 2.1 figures saved to: report_figures/exercise_2_1/
    kspace_magnitude_all_coils.png   — log-scaled k-space magnitude, all 6 coils
    magnitude_phase_coil0.png        — magnitude + phase from coil 0
    magnitude_all_coils.png          — reconstructed magnitude, all 6 coils
    rss_combined.png                 — RSS combined image

Exercise 2.2 figures saved to: report_figures/exercise_2_2/
    part_a_comparison_coil0.png      — 4-panel coil-0 comparison (original + 3 methods)
    part_a_all_coils_median.png      — median filter, all 6 coils
    part_a_all_coils_gaussian.png    — Gaussian filter, all 6 coils
    part_a_all_coils_bilateral.png   — bilateral filter, all 6 coils
    part_b_kspace_filter.png         — Butterworth mask + original + filtered k-space
    part_b_magnitude_phase.png       — 2x2 magnitude/phase before and after Butterworth
    part_c_combined.png              — RSS original / median-denoised / difference
    part_c_all_methods.png           — RSS original + all three denoising methods compared
"""

import sys, os
sys.path.insert(0, "..")

import numpy as np
import matplotlib.pyplot as plt

from mri_denoising.reconstruction_fft import kspace_to_image_centred
from mri_denoising.coil_combination import combine_coils_rss
from mri_denoising.denoising_filters import (
    apply_gaussian_filter,
    apply_bilateral_filter,
    apply_median_filter,
)
from mri_denoising.butterworth_filter import butterworth_lowpass_filter

plt.rcParams["figure.dpi"] = 150

DIR_21 = "report_figures/exercise_2_1"
DIR_22 = "report_figures/exercise_2_2"
os.makedirs(DIR_21, exist_ok=True)
os.makedirs(DIR_22, exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading knee.npy...")
kspace = np.load("../knee.npy")
n_coils = kspace.shape[0]
ny, nx = kspace.shape[1], kspace.shape[2]
print(f"  Shape: {kspace.shape},  dtype: {kspace.dtype}")
print(f"  |k| range: [{np.abs(kspace).min():.3f}, {np.abs(kspace).max():.1f}]")

# ── Display helper ────────────────────────────────────────────────────────────
def fliprot(img):
    """Match the practical-notebook display orientation."""
    return np.flipud(np.rot90(img))


CORNER_SIZE = 20


def background_corner_std(img, size=CORNER_SIZE):
    corners = np.concatenate([
        img[:size, :size].ravel(),
        img[:size, -size:].ravel(),
        img[-size:, :size].ravel(),
        img[-size:, -size:].ravel(),
    ])
    return float(np.std(corners))


def central_mean(img, half=40):
    cy, cx = img.shape[0] // 2, img.shape[1] // 2
    return float(np.mean(img[cy - half : cy + half, cx - half : cx + half]))


def mean_gradient_magnitude(img):
    gy, gx = np.gradient(img)
    grad = np.sqrt(gx**2 + gy**2)
    return float(np.mean(grad))

# ── Reconstruct all coils ─────────────────────────────────────────────────────
print("Reconstructing images (ifft2 of ifftshift'd k-space)...")
images = np.zeros_like(kspace)
for c in range(n_coils):
    images[c] = kspace_to_image_centred(kspace[c])

magnitude_images = np.abs(images)    # (6, 280, 280) — raw magnitude
print(f"  |image| range: [{magnitude_images.min():.4f}, {magnitude_images.max():.4f}]")

# ── RSS combination ───────────────────────────────────────────────────────────
rss = combine_coils_rss(magnitude_images)   # plain RSS of raw coil magnitudes
print(f"  RSS range: [{rss.min():.3f}, {rss.max():.3f}]")


# ═════════════════════════════════════════════════════════════════════════════
# EXERCISE 2.1 FIGURES
# ═════════════════════════════════════════════════════════════════════════════

print("\n── Exercise 2.1 figures ────────────────────────────────────────────")

# Figure 2.1 — k-space magnitude log-scaled, all 6 coils
print("Saving Figure 2.1: k-space magnitude all coils...")
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
for c, ax in enumerate(axes.ravel()):
    ax.imshow(np.log1p(np.abs(kspace[c])), cmap="gray")
    ax.set_title(f"Coil {c}  —  log(1 + |k|)", fontsize=10, fontweight="semibold")
    ax.axis("off")
plt.suptitle("k-space magnitude (log scale) — all six receiver coils",
             fontsize=12, fontweight="semibold")
plt.tight_layout()
fig.savefig(f"{DIR_21}/kspace_magnitude_all_coils.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"  → {DIR_21}/kspace_magnitude_all_coils.png")

# Figure 2.2 — Magnitude and phase from coil 0
print("Saving Figure 2.2: magnitude and phase, coil 0...")
coil_idx = 0
mag0   = magnitude_images[coil_idx]
phase0 = np.angle(images[coil_idx])

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].imshow(fliprot(mag0), cmap="gray")
axes[0].set_title("Magnitude", fontsize=12, fontweight="semibold")
axes[0].axis("off")
axes[1].imshow(fliprot(phase0), cmap="gray")
axes[1].set_title("Phase (rad, wrapped ±π)", fontsize=12, fontweight="semibold")
axes[1].axis("off")
plt.suptitle(f"Reconstructed image — coil {coil_idx}", fontsize=13, fontweight="semibold")
plt.tight_layout()
fig.savefig(f"{DIR_21}/magnitude_phase_coil0.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"  → {DIR_21}/magnitude_phase_coil0.png")

# Figure 2.3 — Magnitude images, all 6 coils
print("Saving Figure 2.3: magnitude images all coils...")
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
for c, ax in enumerate(axes.ravel()):
    ax.imshow(fliprot(magnitude_images[c]), cmap="gray")
    ax.set_title(f"Coil {c} — magnitude", fontsize=10, fontweight="semibold")
    ax.axis("off")
plt.suptitle("Reconstructed magnitude images — all six receiver coils",
             fontsize=12, fontweight="semibold")
plt.tight_layout()
fig.savefig(f"{DIR_21}/magnitude_all_coils.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"  → {DIR_21}/magnitude_all_coils.png")

# Figure 2.4 — RSS combined image
print("Saving Figure 2.4: RSS combined image...")
fig, ax = plt.subplots(figsize=(6, 6))
ax.imshow(fliprot(rss), cmap="gray")
ax.set_title("RSS combined — all 6 coils", fontsize=12, fontweight="semibold")
ax.axis("off")
plt.tight_layout()
fig.savefig(f"{DIR_21}/rss_combined.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"  → {DIR_21}/rss_combined.png")


# ═════════════════════════════════════════════════════════════════════════════
# EXERCISE 2.2 FIGURES
# ═════════════════════════════════════════════════════════════════════════════

print("\n── Exercise 2.2 figures ────────────────────────────────────────────")

# ── Image-space denoising (applied to raw coil magnitude images) ──────────────
MEDIAN_SIZE = 3
SIGMA_GAUSS = 1.0

print("  Applying median filter...")
median_denoised = np.stack(
    [apply_median_filter(magnitude_images[c], size=MEDIAN_SIZE) for c in range(n_coils)]
)
print("  Applying Gaussian filter...")
gauss_denoised = np.stack(
    [apply_gaussian_filter(magnitude_images[c], sigma=SIGMA_GAUSS) for c in range(n_coils)]
)
print("  Applying bilateral filter (may take a moment)...")
bilateral_denoised = np.stack(
    [apply_bilateral_filter(magnitude_images[c], sigma_color=0.05, sigma_spatial=3.0)
     for c in range(n_coils)]
)
print("  Denoising complete.")

# ── Figure: Part (a) — side-by-side comparison for coil 0 ────────────────────
print("Saving Part (a) — coil-0 comparison (4 panels)...")
c = 0
panels = [magnitude_images[c], median_denoised[c], gauss_denoised[c], bilateral_denoised[c]]
labels = [
    "Original magnitude",
    f"Median  {MEDIAN_SIZE}×{MEDIAN_SIZE}",
    f"Gaussian  σ={SIGMA_GAUSS}",
    "Bilateral",
]
vmin_p = 0.0
vmax_p = max(img.max() for img in panels)

fig, axes = plt.subplots(1, 4, figsize=(20, 5))
for ax, img, lbl in zip(axes, panels, labels):
    im = ax.imshow(fliprot(img), cmap="gray", vmin=vmin_p, vmax=vmax_p)
    ax.set_title(lbl, fontsize=11, fontweight="semibold")
    ax.axis("off")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
plt.suptitle(
    f"Coil {c} — image-space denoising comparison (shared intensity scale)",
    fontsize=12, fontweight="semibold",
)
plt.tight_layout()
fig.savefig(f"{DIR_22}/part_a_comparison_coil0.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"  → {DIR_22}/part_a_comparison_coil0.png")

# ── Figures: Part (a) — all 6 coils for each method ─────────────────────────
method_configs = [
    ("median",    median_denoised,    f"Median {MEDIAN_SIZE}×{MEDIAN_SIZE} — all coils"),
    ("gaussian",  gauss_denoised,     f"Gaussian σ={SIGMA_GAUSS} — all coils"),
    ("bilateral", bilateral_denoised, "Bilateral — all coils"),
]
for name, stack, title in method_configs:
    print(f"Saving Part (a) all-coils: {name}...")
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    for c, ax in enumerate(axes.ravel()):
        ax.imshow(fliprot(stack[c]), cmap="gray")
        ax.set_title(f"Coil {c}", fontsize=10, fontweight="semibold")
        ax.axis("off")
    plt.suptitle(f"{title} — coil magnitude images", fontsize=12, fontweight="semibold")
    plt.tight_layout()
    fname = f"{DIR_22}/part_a_all_coils_{name}.png"
    fig.savefig(fname, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {fname}")

# ── Butterworth filter ────────────────────────────────────────────────────────
D0       = 30
BW_ORDER = 2
coil_idx = 0

H              = butterworth_lowpass_filter(kspace[coil_idx].shape, D0=D0, n=BW_ORDER)
kspace_filtered = kspace[coil_idx] * H
image_filtered  = kspace_to_image_centred(kspace_filtered)
mag_filtered    = np.abs(image_filtered)
phase_filtered  = np.angle(image_filtered)

print(f"  Butterworth: D0={D0}px, n={BW_ORDER}")
print(f"  Filter centre: {H[ny//2, nx//2]:.4f}   corner: {H[0,0]:.6f}")

# Figure: Part (b) — Butterworth mask + original + filtered k-space
print("Saving Part (b) — Butterworth mask and k-space (3 panels)...")
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
axes[0].imshow(H, cmap="gray", vmin=0, vmax=1)
axes[0].set_title(f"Butterworth mask  (D₀={D0} px, n={BW_ORDER})",
                  fontsize=11, fontweight="semibold")
axes[0].axis("off")
axes[1].imshow(np.log1p(np.abs(kspace[coil_idx])), cmap="gray")
axes[1].set_title(f"Coil {coil_idx} — original k-space  log(1+|k|)",
                  fontsize=11, fontweight="semibold")
axes[1].axis("off")
axes[2].imshow(np.log1p(np.abs(kspace_filtered)), cmap="gray")
axes[2].set_title(f"Coil {coil_idx} — filtered k-space  log(1+|k|)",
                  fontsize=11, fontweight="semibold")
axes[2].axis("off")
plt.suptitle(
    f"Butterworth low-pass filter in k-space  (D₀={D0} px, order={BW_ORDER})",
    fontsize=12, fontweight="semibold",
)
plt.tight_layout()
fig.savefig(f"{DIR_22}/part_b_kspace_filter.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"  → {DIR_22}/part_b_kspace_filter.png")

# Figure: Part (b) — 2×2 magnitude and phase comparison (shared scales)
print("Saving Part (b) — magnitude / phase comparison (2×2)...")
phase_original = np.angle(images[coil_idx])
mag_vmax = max(magnitude_images[coil_idx].max(), mag_filtered.max())

fig, axes = plt.subplots(2, 2, figsize=(14, 12))

axes[0, 0].imshow(fliprot(magnitude_images[coil_idx]), cmap="gray", vmin=0, vmax=mag_vmax)
axes[0, 0].set_title(f"Coil {coil_idx} — original magnitude", fontsize=11, fontweight="semibold")
axes[0, 0].axis("off")

axes[0, 1].imshow(fliprot(mag_filtered), cmap="gray", vmin=0, vmax=mag_vmax)
axes[0, 1].set_title(f"Coil {coil_idx} — Butterworth magnitude", fontsize=11, fontweight="semibold")
axes[0, 1].axis("off")

axes[1, 0].imshow(fliprot(phase_original), cmap="twilight", vmin=-np.pi, vmax=np.pi)
axes[1, 0].set_title(f"Coil {coil_idx} — original phase (rad)", fontsize=11, fontweight="semibold")
axes[1, 0].axis("off")

axes[1, 1].imshow(fliprot(phase_filtered), cmap="twilight", vmin=-np.pi, vmax=np.pi)
axes[1, 1].set_title(f"Coil {coil_idx} — Butterworth phase (rad)", fontsize=11, fontweight="semibold")
axes[1, 1].axis("off")

plt.suptitle(
    f"Butterworth k-space filter — coil {coil_idx}  (D₀={D0} px, order={BW_ORDER})",
    fontsize=12, fontweight="semibold",
)
plt.tight_layout()
fig.savefig(f"{DIR_22}/part_b_magnitude_phase.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"  → {DIR_22}/part_b_magnitude_phase.png")

# ── Part (c): denoise each coil magnitude image, then combine with RSS ────────
rss_original = np.sqrt(np.sum(magnitude_images**2, axis=0))
rss_median = np.sqrt(np.sum(median_denoised**2, axis=0))
rss_gauss = np.sqrt(np.sum(gauss_denoised**2, axis=0))
rss_bilateral = np.sqrt(np.sum(bilateral_denoised**2, axis=0))

methods_rss = {
    "Original RSS": rss_original,
    "Median then RSS": rss_median,
    "Gaussian then RSS": rss_gauss,
    "Bilateral then RSS": rss_bilateral,
}

vmax_rss = rss_original.max()

# Figure 1: original vs median-denoised + difference map
print("Saving Part (c) — combined comparison (3 panels)...")
diff_map = np.abs(rss_original - rss_median)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
im0 = axes[0].imshow(fliprot(rss_original), cmap="gray", vmin=0, vmax=vmax_rss)
axes[0].set_title("RSS — original", fontsize=11, fontweight="semibold")
axes[0].axis("off")
plt.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

im1 = axes[1].imshow(fliprot(rss_median), cmap="gray", vmin=0, vmax=vmax_rss)
axes[1].set_title("RSS — median denoised then combined", fontsize=11, fontweight="semibold")
axes[1].axis("off")
plt.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

im2 = axes[2].imshow(fliprot(diff_map), cmap="hot")
axes[2].set_title("|original − median|", fontsize=11, fontweight="semibold")
axes[2].axis("off")
plt.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)

plt.suptitle(
    "Part (c): Median-filter each coil magnitude image, then combine with RSS",
    fontsize=12, fontweight="semibold",
)
plt.tight_layout()
fig.savefig(f"{DIR_22}/part_c_combined.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"  → {DIR_22}/part_c_combined.png")

print(
    "\nFinal RSS descriptive summary "
    f"(same four {CORNER_SIZE}x{CORNER_SIZE} corner ROIs and central 80x80 ROI as coil 0)"
)
print("Note: background std here is a simple denoising proxy, not a physical SNR estimate.")
print(f"{'Method':<20}  {'Background std':>14}  {'Central mean':>13}  {'Mean grad':>11}")
print("-" * 74)
for name, img in methods_rss.items():
    bg = background_corner_std(img)
    cm = central_mean(img)
    mg = mean_gradient_magnitude(img)
    print(f"{name:<20}  {bg:>14.5f}  {cm:>13.5f}  {mg:>11.5f}")

# Figure 2: all three methods on the combined image
print("Saving Part (c) — all-methods comparison (4 panels)...")
fig, axes = plt.subplots(1, 4, figsize=(24, 6))
for ax, (title, img) in zip(axes, methods_rss.items()):
    im = ax.imshow(fliprot(img), cmap="gray", vmin=0, vmax=vmax_rss)
    ax.set_title(title, fontsize=11, fontweight="semibold")
    ax.axis("off")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

plt.suptitle(
    "Part (c): RSS-combined image — all three denoising methods compared\n"
    "(all panels share the same colour scale)",
    fontsize=12, fontweight="semibold",
)
plt.tight_layout()
fig.savefig(f"{DIR_22}/part_c_all_methods.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"  → {DIR_22}/part_c_all_methods.png")

# ─────────────────────────────────────────────────────────────────────────────
print("\nDone.  All figures saved.")
print(f"\n{DIR_21}/")
for f in sorted(os.listdir(DIR_21)):
    print(f"  {f}")
print(f"\n{DIR_22}/")
for f in sorted(os.listdir(DIR_22)):
    print(f"  {f}")
