"""
Generate and save report figures for Exercise 1.1.
Run from the notebooks/ directory:
    ../.venv/bin/python save_ex11_figures.py

Figures saved:
  report_figures/exercise_1_1/recon_I0_1e5.png    — high-dose reconstruction grid
  report_figures/exercise_1_1/recon_I0_1e3.png    — medium-dose reconstruction grid
  report_figures/exercise_1_1/recon_I0_1e2.png    — low-dose reconstruction grid
  report_figures/exercise_1_1/metrics_heatmap.png  — PSNR/SSIM heatmap across all 9 conditions
  report_figures/exercise_1_1/gd_convergence.png   — GD convergence curves (residual + image MSE)
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

SAVE_DIR = "report_figures/exercise_1_1"
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

# ── Noise / reconstruction / metrics (identical to notebook) ──────────────
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

def reconstruct_gd(sinogram, theta, output_size, gamma=0.001, n_iter=200,
                   log_convergence=False):
    x = np.zeros((output_size, output_size), dtype=np.float64)
    residual_losses, image_mse_losses = [], []
    for _ in range(n_iter):
        residual = radon(x, theta=theta, circle=True) - sinogram
        if log_convergence:
            rel = float(np.sqrt(np.mean(residual ** 2) * sinogram.size)
                        / (np.linalg.norm(sinogram) + 1e-12))
            residual_losses.append(rel)
        grad = iradon(residual, theta=theta, filter_name=None,
                      circle=True, output_size=output_size)
        x = x - gamma * grad
    if log_convergence:
        return x, residual_losses
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
I0_list    = [1e5, 1e3, 1e2]
n_angles_list = [360, 90, 20]
sigma      = 0.05
rng        = np.random.default_rng(42)

print("Building sinograms and running reconstructions...")
recon_results = {}
for I0 in I0_list:
    recon_results[I0] = {}
    for n_angles in n_angles_list:
        theta = np.linspace(0.0, 180.0, n_angles, endpoint=False)
        sino_clean = radon(phantom, theta=theta, circle=True)
        sino_noisy = simulate_noisy_sinogram(sino_clean, I0=I0, sigma=sigma, rng=rng)
        fbp = reconstruct_fbp(sino_noisy, theta, phantom.shape[0])
        gd  = reconstruct_gd(sino_noisy,  theta, phantom.shape[0])
        recon_results[I0][n_angles] = {
            "fbp": fbp, "gd": gd,
            "fbp_m": compute_metrics(phantom, fbp, mask),
            "gd_m":  compute_metrics(phantom, gd,  mask),
        }
        fbp_p = recon_results[I0][n_angles]["fbp_m"]["PSNR"]
        gd_p  = recon_results[I0][n_angles]["gd_m"]["PSNR"]
        print(f"  I0={I0:.0e}  {n_angles:3d} views  FBP {fbp_p:.1f}dB  GD {gd_p:.1f}dB")

# ── FIGURE 1: Reconstruction grids for each of the three dose levels ──────
print("Saving Figure 1: reconstruction comparisons for all dose levels...")
gray_cm = plt.cm.gray.copy();    gray_cm.set_bad("white")
err_cm  = plt.cm.inferno.copy(); err_cm.set_bad("white")
def masked(img): return np.ma.masked_where(~mask, img)

# Shared intensity scale across ALL 27 reconstructions (for comparability)
all_imgs_global = [phantom] + [recon_results[I0][n][k]
                                for I0 in I0_list
                                for n in n_angles_list
                                for k in ("fbp", "gd")]
img_vmin, img_vmax = np.percentile(
    np.concatenate([v[mask].ravel() for v in all_imgs_global]), [1, 99])

I0_labels = {1e5: "1e5", 1e3: "1e3", 1e2: "1e2"}
I0_titles  = {1e5: r"High dose — $I_0=10^5$",
              1e3: r"Medium dose — $I_0=10^3$",
              1e2: r"Low dose — $I_0=10^2$"}

for I0_show in I0_list:
    all_errs = [np.abs(phantom - recon_results[I0_show][n][k])
                for n in n_angles_list for k in ("fbp", "gd")]
    err_vmax = float(np.percentile(
        np.concatenate([v[mask].ravel() for v in all_errs]), 99.5))

    fig = plt.figure(figsize=(12, 8), constrained_layout=True)
    gs  = gridspec.GridSpec(3, 5, figure=fig, width_ratios=[1,1,1,1,0.05])
    col_titles = ["FBP", "FBP error", "GD", "GD error"]
    err_im = None
    first_col_axes = []

    for ri, n_angles in enumerate(n_angles_list):
        fbp   = recon_results[I0_show][n_angles]["fbp"]
        gd    = recon_results[I0_show][n_angles]["gd"]
        fbp_m = recon_results[I0_show][n_angles]["fbp_m"]
        gd_m  = recon_results[I0_show][n_angles]["gd_m"]
        panels = [
            (masked(fbp),                 gray_cm, img_vmin, img_vmax),
            (masked(np.abs(phantom-fbp)), err_cm,  0,        err_vmax),
            (masked(gd),                  gray_cm, img_vmin, img_vmax),
            (masked(np.abs(phantom-gd)),  err_cm,  0,        err_vmax),
        ]
        for ci, (img, cmap, vmin, vmax) in enumerate(panels):
            ax = fig.add_subplot(gs[ri, ci])
            ax.imshow(img, cmap=cmap, vmin=vmin, vmax=vmax, interpolation="none")
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_facecolor("white")
            for sp in ax.spines.values(): sp.set_visible(False)
            if ri == 0:
                ax.set_title(col_titles[ci], fontsize=10, fontweight="semibold")
            if ci == 0:
                ax.text(0.98, 0.02, f"PSNR {fbp_m['PSNR']:.1f} dB",
                        transform=ax.transAxes, ha="right", va="bottom",
                        fontsize=7.5, color="white",
                        bbox=dict(facecolor="black", alpha=0.45, pad=1.5, linewidth=0))
                first_col_axes.append(ax)
            if ci == 2:
                ax.text(0.98, 0.02, f"PSNR {gd_m['PSNR']:.1f} dB",
                        transform=ax.transAxes, ha="right", va="bottom",
                        fontsize=7.5, color="white",
                        bbox=dict(facecolor="black", alpha=0.45, pad=1.5, linewidth=0))
            if ci in (1, 3):
                err_im = ax.images[-1]

    for ax0, n in zip(first_col_axes, n_angles_list):
        ax0.text(-0.22, 0.5, f"{n} views",
                 transform=ax0.transAxes,
                 ha="right", va="center", fontsize=10, fontweight="semibold")

    cax = fig.add_subplot(gs[:, 4])
    fig.colorbar(err_im, cax=cax, extend="max").set_label("Absolute error", fontsize=9)
    fig.suptitle(
        f"{I0_titles[I0_show]}, Gaussian+Poisson noise ($\\sigma$=0.05)",
        fontsize=11, fontweight="semibold")
    fname = f"{SAVE_DIR}/recon_I0_{I0_labels[I0_show]}.png"
    fig.savefig(fname, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {fname}")

# ── FIGURE 2: PSNR heatmap — all 9 conditions, FBP and GD side by side ────
print("Saving Figure 2: PSNR/SSIM heatmap...")
import matplotlib.colors as mcolors

methods   = ["FBP", "GD"]
psnr_grid = {m: np.zeros((3, 3)) for m in methods}
ssim_grid = {m: np.zeros((3, 3)) for m in methods}
for ri, I0 in enumerate(I0_list):
    for ci, n in enumerate(n_angles_list):
        psnr_grid["FBP"][ri, ci] = recon_results[I0][n]["fbp_m"]["PSNR"]
        psnr_grid["GD"][ri, ci]  = recon_results[I0][n]["gd_m"]["PSNR"]
        ssim_grid["FBP"][ri, ci] = recon_results[I0][n]["fbp_m"]["SSIM"]
        ssim_grid["GD"][ri, ci]  = recon_results[I0][n]["gd_m"]["SSIM"]

xlabels = ["360", "90", "20"]
ylabels = ["$10^5$", "$10^3$", "$10^2$"]

fig, axes = plt.subplots(2, 2, figsize=(9, 6), constrained_layout=True)
vmin_p, vmax_p = -1, 40
vmin_s, vmax_s =  0,  1

for col, method in enumerate(methods):
    # PSNR
    ax = axes[0, col]
    im = ax.imshow(psnr_grid[method], cmap="RdYlGn",
                   vmin=vmin_p, vmax=vmax_p, aspect="auto")
    ax.set_xticks(range(3)); ax.set_xticklabels(xlabels)
    ax.set_yticks(range(3)); ax.set_yticklabels(ylabels)
    ax.set_xlabel("Number of views"); ax.set_ylabel("$I_0$ (photons)")
    ax.set_title(f"{method} — PSNR (dB)", fontweight="semibold")
    for ri in range(3):
        for ci in range(3):
            v = psnr_grid[method][ri, ci]
            ax.text(ci, ri, f"{v:.1f}", ha="center", va="center",
                    fontsize=9, fontweight="bold",
                    color="white" if v < 15 else "black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    # SSIM
    ax = axes[1, col]
    im = ax.imshow(ssim_grid[method], cmap="RdYlGn",
                   vmin=vmin_s, vmax=vmax_s, aspect="auto")
    ax.set_xticks(range(3)); ax.set_xticklabels(xlabels)
    ax.set_yticks(range(3)); ax.set_yticklabels(ylabels)
    ax.set_xlabel("Number of views"); ax.set_ylabel("$I_0$ (photons)")
    ax.set_title(f"{method} — SSIM", fontweight="semibold")
    for ri in range(3):
        for ci in range(3):
            v = ssim_grid[method][ri, ci]
            ax.text(ci, ri, f"{v:.3f}", ha="center", va="center",
                    fontsize=9, fontweight="bold",
                    color="white" if v < 0.4 else "black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

fig.suptitle("PSNR and SSIM across all 9 dose/view conditions",
             fontsize=12, fontweight="semibold")
fig.savefig(f"{SAVE_DIR}/metrics_heatmap.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"  Saved {SAVE_DIR}/metrics_heatmap.png")

# ── FIGURE 3: GD convergence curves — all 9 conditions ────────────────────
print("Saving Figure 3: GD convergence curves...")

# Re-run GD with convergence logging (same RNG seed → same noisy sinograms)
rng_conv = np.random.default_rng(42)
conv_results = {}
for I0 in I0_list:
    conv_results[I0] = {}
    for n_angles in n_angles_list:
        theta = np.linspace(0.0, 180.0, n_angles, endpoint=False)
        sino_clean = radon(phantom, theta=theta, circle=True)
        sino_noisy = simulate_noisy_sinogram(sino_clean, I0=I0, sigma=sigma, rng=rng_conv)
        _, rel_res = reconstruct_gd(sino_noisy, theta, phantom.shape[0],
                                    log_convergence=True)
        # image MSE from the stored reconstruction
        gd_img = recon_results[I0][n_angles]["gd"]
        img_mse_series = None  # not tracked here; omit from plot
        conv_results[I0][n_angles] = {"rel_res": rel_res}

ordered_I0     = sorted(I0_list, reverse=True)
ordered_angles = sorted(n_angles_list, reverse=True)

fig, axes = plt.subplots(len(ordered_I0), len(ordered_angles),
                         figsize=(15, 10), sharex=True)
iters = np.arange(1, 201)

for i, I0 in enumerate(ordered_I0):
    for j, n_angles in enumerate(ordered_angles):
        ax = axes[i, j]
        rel_res = conv_results[I0][n_angles]["rel_res"]
        ax.semilogy(iters, rel_res, color="tab:blue", linewidth=1.8,
                    label="Rel. residual")
        ax.set_title(f"$I_0$={I0:.0e}, {n_angles} views", fontsize=9)
        ax.set_xlabel("Iteration", fontsize=8)
        if j == 0:
            ax.set_ylabel("Relative residual", fontsize=8)
        ax.grid(True, which="both", alpha=0.3)
        ax.tick_params(labelsize=7)

fig.suptitle(
    r"GD convergence — relative residual $\|Ax^k{-}b\|_2/\|b\|_2$"
    + f"\n(200 iterations, $\\gamma=0.001$, Gaussian+Poisson noise, $\\sigma=0.05$)",
    fontsize=11, fontweight="semibold")
plt.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig(f"{SAVE_DIR}/gd_convergence.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"  Saved {SAVE_DIR}/gd_convergence.png")

print("\nDone.")
