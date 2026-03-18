"""Regenerate only recon_I0_1e5.png using already-saved reconstruction data."""
import sys, os, pickle
sys.path.insert(0, "..")

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from skimage.transform import radon, iradon
from skimage.metrics import structural_similarity
from ct_reconstruction.phantom import load_ct_image

plt.rcParams["figure.dpi"] = 150
np.random.seed(42)

SAVE_DIR = "report_figures/exercise_1_2"

# ── Re-run only the parts needed for Figure 2 ─────────────────────────────
def circular_mask(shape):
    h, w = shape
    cy, cx = h / 2.0, w / 2.0
    yy, xx = np.ogrid[:h, :w]
    r = min(h, w) / 2.0
    return (yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2

phantom = load_ct_image("../CT_exercise_1.png", size=256).astype(np.float64)
mask = circular_mask(phantom.shape)
phantom[~mask] = 0.0

def simulate_noisy_sinogram(sinogram, I0, sigma=0.05, rng=None):
    if rng is None: rng = np.random.default_rng()
    p_max = sinogram.max()
    if p_max == 0: return sinogram.copy()
    p_norm  = sinogram / p_max
    I       = I0 * np.exp(-p_norm)
    I_gauss = I + rng.normal(0.0, sigma, size=sinogram.shape)
    I_gauss = np.clip(I_gauss, 1e-8, None)
    I_noisy = rng.poisson(I_gauss).astype(np.float64)
    I_noisy = np.clip(I_noisy, 1, None)
    return -np.log(I_noisy / I0) * p_max

def reconstruct_fbp(sinogram, theta, output_size):
    return iradon(sinogram, theta=theta, filter_name="ramp",
                  circle=True, output_size=output_size)

def reconstruct_gd(sinogram, theta, output_size, gamma=0.001, n_iter=200):
    x = np.zeros((output_size, output_size), dtype=np.float64)
    for _ in range(n_iter):
        residual = radon(x, theta=theta, circle=True) - sinogram
        grad     = iradon(residual, theta=theta, filter_name=None,
                          circle=True, output_size=output_size)
        x = np.clip(x - gamma * grad, 0.0, None)
    return x

max_angles = [180, 120, 40]
I0_show    = 1e5
N_VIEWS    = 360
sigma      = 0.05
rng        = np.random.default_rng(42)

# Only reconstruct at I0=1e5 (skip 1e3 and 1e2 to save time)
# Must use same rng sequence as original — advance past 1e3/1e2 sinograms
# to reproduce exact noisy sinogram at I0=1e5
# Easiest: just regenerate all sinograms then only reconstruct I0=1e5
print("Building sinograms...")
noisy_sinos  = {}
recon_results = {}
for max_angle in max_angles:
    theta = np.linspace(0, max_angle, N_VIEWS, endpoint=False)
    sino_clean = radon(phantom, theta=theta, circle=True)
    noisy_sinos[max_angle] = {}
    for I0 in [1e5, 1e3, 1e2]:
        noisy_sinos[max_angle][I0] = {
            "theta": theta,
            "sino":  simulate_noisy_sinogram(sino_clean, I0=I0, sigma=sigma, rng=rng),
        }

print("Reconstructing I0=1e5 only...")
for max_angle in max_angles:
    theta = noisy_sinos[max_angle][I0_show]["theta"]
    sino  = noisy_sinos[max_angle][I0_show]["sino"]
    fbp = reconstruct_fbp(sino, theta, phantom.shape[0])
    gd  = reconstruct_gd(sino,  theta, phantom.shape[0])
    recon_results[max_angle] = {"fbp": fbp, "gd": gd}
    print(f"  {max_angle}° done")

# ── FIGURE 2 ──────────────────────────────────────────────────────────────
print("Saving Figure 2...")
gray_cm = plt.cm.gray.copy();    gray_cm.set_bad("white")
err_cm  = plt.cm.inferno.copy(); err_cm.set_bad("white")
def masked(img): return np.ma.masked_where(~mask, img)

all_imgs = [phantom] + [recon_results[ma][k] for ma in max_angles for k in ("fbp","gd")]
all_errs = [np.abs(phantom - recon_results[ma][k]) for ma in max_angles for k in ("fbp","gd")]
img_vmin, img_vmax = np.percentile(
    np.concatenate([v[mask].ravel() for v in all_imgs]), [1, 99])
err_vmax = float(np.percentile(
    np.concatenate([v[mask].ravel() for v in all_errs]), 99.5))

fig = plt.figure(figsize=(12, 8), constrained_layout=True)
gs  = gridspec.GridSpec(3, 5, figure=fig, width_ratios=[1,1,1,1,0.05])
col_titles = ["FBP", "FBP error", "GD", "GD error"]
err_im = None
first_col_axes = []

for ri, ma in enumerate(max_angles):
    fbp = recon_results[ma]["fbp"]
    gd  = recon_results[ma]["gd"]
    panels = [
        (masked(fbp),                 gray_cm, img_vmin, img_vmax),
        (masked(np.abs(phantom-fbp)), err_cm,  0,        err_vmax),
        (masked(gd),                  gray_cm, img_vmin, img_vmax),
        (masked(np.abs(phantom-gd)),  err_cm,  0,        err_vmax),
    ]
    for ci, (img, cmap, vmin, vmax) in enumerate(panels):
        ax = fig.add_subplot(gs[ri, ci])
        im = ax.imshow(img, cmap=cmap, vmin=vmin, vmax=vmax, interpolation="none")
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_facecolor("white")
        for sp in ax.spines.values(): sp.set_visible(False)
        if ri == 0:
            ax.set_title(col_titles[ci], fontsize=10, fontweight="semibold")
        if ci == 0:
            first_col_axes.append(ax)
        if ci in (1, 3):
            err_im = im

for ax0, ma in zip(first_col_axes, max_angles):
    ax0.text(-0.22, 0.5, f"{ma}°",
             transform=ax0.transAxes,
             ha="right", va="center", fontsize=11, fontweight="semibold")

cax = fig.add_subplot(gs[:, 4])
fig.colorbar(err_im, cax=cax, extend="max").set_label("Absolute error", fontsize=9)
fig.suptitle(f"Limited-angle reconstructions — $I_0$={I0_show:.0e}, 360 views",
             fontsize=11, fontweight="semibold")
fig.savefig(f"{SAVE_DIR}/recon_I0_1e5.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"Saved {SAVE_DIR}/recon_I0_1e5.png")
