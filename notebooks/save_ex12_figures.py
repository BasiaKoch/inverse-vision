"""
Generate and save the three report figures for Exercise 1.2.
Run from the notebooks/ directory:
    python save_ex12_figures.py
"""
import sys, os
sys.path.insert(0, "..")

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from skimage.transform import radon, iradon
from skimage.metrics import structural_similarity

from ct_reconstruction.phantom import load_ct_image

plt.rcParams["figure.dpi"] = 150
plt.rcParams["axes.titlesize"] = 9

SAVE_DIR = "report_figures/exercise_1_2"
os.makedirs(SAVE_DIR, exist_ok=True)

# ── Phantom ────────────────────────────────────────────────────────────────
def circular_mask(shape):
    h, w = shape
    cy, cx = h / 2.0, w / 2.0
    yy, xx = np.ogrid[:h, :w]
    r = min(h, w) / 2.0
    return (yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2

phantom = load_ct_image("../CT_exercise_1.png").astype(np.float64)
mask = circular_mask(phantom.shape)
phantom[~mask] = 0.0

# ── Noise / reconstruction functions (identical to notebook) ───────────────
def simulate_noisy_sinogram(sinogram, I0, sigma=0.05, rng=None):
    if rng is None:
        rng = np.random.default_rng()
    p_max = sinogram.max()
    if p_max == 0:
        return sinogram.copy()
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
        x = x - gamma * grad
    return x

def compute_metrics(reference, reconstruction, mask):
    ref = reference.astype(np.float64)
    rec = reconstruction.astype(np.float64)
    ref_v = ref[mask]; rec_v = rec[mask]
    mse = float(np.mean((ref_v - rec_v) ** 2))
    dr  = float(ref_v.max() - ref_v.min()) or 1.0
    psnr = 10.0 * np.log10(dr ** 2 / mse) if mse > 0 else np.inf
    r2 = np.zeros_like(ref); r2[mask] = ref[mask]
    r3 = np.zeros_like(rec); r3[mask] = rec[mask]
    ssim = float(structural_similarity(r2, r3, data_range=dr))
    return {"MSE": mse, "PSNR": psnr, "SSIM": ssim}

# ── Build experiment grid ──────────────────────────────────────────────────
N_VIEWS    = 360
I0_list    = [1e5, 1e3, 1e2]
max_angles = [180, 120, 40]
sigma      = 0.05
rng        = np.random.default_rng(42)

noisy_sinos = {}
recon_results = {}

for max_angle in max_angles:
    theta = np.linspace(0, max_angle, N_VIEWS, endpoint=False)
    sino_clean = radon(phantom, theta=theta, circle=True)
    noisy_sinos[max_angle] = {}
    recon_results[max_angle] = {}
    for I0 in I0_list:
        sino_noisy = simulate_noisy_sinogram(sino_clean, I0=I0, sigma=sigma, rng=rng)
        noisy_sinos[max_angle][I0] = {"theta": theta, "sino": sino_noisy}

print("Sinograms ready. Running reconstructions (this may take a few minutes)...")
for max_angle in max_angles:
    for I0 in I0_list:
        theta = noisy_sinos[max_angle][I0]["theta"]
        sino  = noisy_sinos[max_angle][I0]["sino"]
        fbp = reconstruct_fbp(sino, theta, phantom.shape[0])
        gd  = reconstruct_gd(sino,  theta, phantom.shape[0])
        recon_results[max_angle][I0] = {
            "fbp": fbp, "gd": gd,
            "fbp_m": compute_metrics(phantom, fbp, mask),
            "gd_m":  compute_metrics(phantom, gd,  mask),
        }
        print(f"  {max_angle}° I0={I0:.0e}  FBP {recon_results[max_angle][I0]['fbp_m']['PSNR']:.1f}dB  GD {recon_results[max_angle][I0]['gd_m']['PSNR']:.1f}dB")

# ── FIGURE 1: Noisy sinograms ──────────────────────────────────────────────
print("Saving Figure 1: noisy sinograms...")
fig, axes = plt.subplots(len(I0_list), len(max_angles),
                         figsize=(13, 8), constrained_layout=True)
for i, I0 in enumerate(I0_list):
    for j, ma in enumerate(max_angles):
        sino = noisy_sinos[ma][I0]["sino"]
        ax   = axes[i, j]
        vmin, vmax = np.percentile(sino, [1, 99])
        ax.imshow(sino, cmap="gray", aspect="auto", vmin=vmin, vmax=vmax)
        ax.set_title(f"{ma}°, $I_0$={I0:.0e}", fontsize=9)
        if j == 0: ax.set_ylabel(f"$I_0$={I0:.0e}", fontsize=9)
        ax.set_xlabel("Projection index", fontsize=8)
        ax.set_ylabel("Detector bin", fontsize=8)
fig.suptitle("Noisy sinograms — Gaussian+Poisson noise, 360 projections per range",
             fontsize=11, fontweight="semibold")
fig.savefig(f"{SAVE_DIR}/noisy_sinograms.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ── FIGURE 2: Reconstruction + error maps (I0=1e5) ─────────────────────────
print("Saving Figure 2: reconstruction comparison...")
gray_cm  = plt.cm.gray.copy();    gray_cm.set_bad("white")
err_cm   = plt.cm.inferno.copy(); err_cm.set_bad("white")

def masked(img): return np.ma.masked_where(~mask, img)

# Shared scales
all_imgs = [phantom] + [recon_results[ma][1e5][k] for ma in max_angles for k in ("fbp","gd")]
all_errs = [np.abs(phantom - recon_results[ma][1e5][k]) for ma in max_angles for k in ("fbp","gd")]
img_vmin, img_vmax = np.percentile(np.concatenate([v[mask].ravel() for v in all_imgs]), [1, 99])
err_vmax = float(np.percentile(np.concatenate([v[mask].ravel() for v in all_errs]), 99.5))

I0_show = 1e5
fig = plt.figure(figsize=(12, 8), constrained_layout=True)
gs  = gridspec.GridSpec(3, 5, figure=fig, width_ratios=[1,1,1,1,0.05])
col_titles = ["FBP", "FBP error", "GD", "GD error"]
err_im = None
# Store first-column axes so we can add row labels without recreating them
first_col_axes = []
for ri, ma in enumerate(max_angles):
    fbp = recon_results[ma][I0_show]["fbp"]
    gd  = recon_results[ma][I0_show]["gd"]
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
            first_col_axes.append(ax)   # save reference, do NOT recreate
        if ci in (1, 3):
            err_im = im

# Add row labels to the already-created first-column axes
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

# ── FIGURE 3: Metrics vs angular range ────────────────────────────────────
print("Saving Figure 3: metrics vs angular range...")
I0_colors = {1e5: "tab:green", 1e3: "tab:orange", 1e2: "tab:red"}
fig, axes = plt.subplots(2, 3, figsize=(13, 7), sharex=True, constrained_layout=True)
for row, method in enumerate(["FBP", "GD"]):
    key = method.lower()
    for I0, color in I0_colors.items():
        psnr_vals = [recon_results[ma][I0][f"{key}_m"]["PSNR"] for ma in max_angles]
        ssim_vals = [recon_results[ma][I0][f"{key}_m"]["SSIM"] for ma in max_angles]
        mse_vals  = [recon_results[ma][I0][f"{key}_m"]["MSE"]  for ma in max_angles]
        kw = dict(color=color, marker="o", linewidth=2, markersize=6, label=f"$I_0$={I0:.0e}")
        axes[row,0].semilogy(max_angles, mse_vals,  **kw)
        axes[row,1].plot(max_angles,    psnr_vals, **kw)
        axes[row,2].plot(max_angles,    ssim_vals, **kw)
    for col, (ylabel, title) in enumerate([
        ("MSE (log)",  f"{method} — MSE"),
        ("PSNR (dB)",  f"{method} — PSNR"),
        ("SSIM",       f"{method} — SSIM"),
    ]):
        ax = axes[row, col]
        ax.set_xticks(max_angles)
        ax.set_xticklabels([f"{a}°" for a in max_angles])
        ax.set_xlabel("Angular range"); ax.set_ylabel(ylabel)
        ax.set_title(title, fontweight="semibold")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
fig.suptitle("Metrics vs angular range — Gaussian+Poisson noise, 360 views",
             fontsize=11, fontweight="semibold")
fig.savefig(f"{SAVE_DIR}/metrics_vs_angle.png", dpi=200, bbox_inches="tight")
plt.close(fig)

print(f"\nDone. Saved to {SAVE_DIR}/")
print("  noisy_sinograms.png")
print("  recon_I0_1e5.png")
print("  metrics_vs_angle.png")
