"""
Run CT reconstruction experiments (Exercises 1.1, 1.2, 1.3).

Iterates over dose levels, projection counts, and angular ranges from
configs/ct_experiments.yaml. For each combination, reconstructs with
FBP (multiple filters), SIRT, and OS-SART. Saves images and metrics.

Usage
-----
    python experiments/run_ct_experiments.py
    python experiments/run_ct_experiments.py --config configs/ct_experiments.yaml
    python experiments/run_ct_experiments.py --phantom CT_exercise_1.png
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yaml
from tqdm import tqdm

from ct_reconstruction.phantom import load_shepp_logan, load_ct_image
from ct_reconstruction.sinogram import simulate_sinogram
from ct_reconstruction.reconstruction_fbp import reconstruct_fbp
from ct_reconstruction.reconstruction_iterative import reconstruct_sirt, reconstruct_os_sart
from ct_reconstruction.filters import validate_filter
from ct_reconstruction.evaluation_metrics import compute_all_metrics


def load_config(config_path: str) -> dict:
    """Load YAML configuration file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def save_image(image: np.ndarray, path: Path, title: str = "") -> None:
    """Save a grayscale 2D image as PNG with optional title."""
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(image, cmap="gray")
    ax.set_title(title, fontsize=9)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def run_dose_experiments(
    phantom: np.ndarray,
    config: dict,
    images_dir: Path,
    records: list,
) -> None:
    """
    Exercise 1.1: vary dose level (I0) and projection count.

    Reconstructs each (I0, n_proj) combination with FBP (all configured
    filters), SIRT, and OS-SART. Appends metric dictionaries to records.
    """
    fbp_filters = config["reconstruction"]["fbp_filters"]
    gamma = config["reconstruction"]["iterative"]["gamma"]
    n_iter = config["reconstruction"]["iterative"]["max_iterations"]
    n_subsets = config["reconstruction"]["iterative"]["os_sart_n_subsets"]
    gaussian_sigma = config["noise"]["gaussian_sigma"]

    for I0 in tqdm(config["dose_levels"], desc="Exercise 1.1 — dose levels"):
        for n_proj in config["projection_counts"]:
            tag = f"I0={I0:.0e}_proj={n_proj}"
            sinogram, angles = simulate_sinogram(
                phantom,
                num_projections=n_proj,
                max_angle=180.0,
                I0=I0,
                gaussian_sigma=gaussian_sigma,
            )

            for filt in fbp_filters:
                filt_v = validate_filter(filt)
                recon = reconstruct_fbp(sinogram, angles, filter_name=filt_v)
                metrics = compute_all_metrics(phantom, recon)
                records.append(
                    {"experiment": "dose", "method": f"FBP-{filt}", "I0": I0,
                     "n_proj": n_proj, "angle_range": 180, **metrics}
                )
                save_image(
                    recon, images_dir / f"dose_fbp_{filt}_{tag}.png",
                    title=f"FBP ({filt}) | {tag}",
                )

            recon_sirt = reconstruct_sirt(
                sinogram, angles, gamma=gamma, n_iterations=n_iter
            )
            metrics = compute_all_metrics(phantom, recon_sirt)
            records.append(
                {"experiment": "dose", "method": "SIRT", "I0": I0,
                 "n_proj": n_proj, "angle_range": 180, **metrics}
            )
            save_image(recon_sirt, images_dir / f"dose_sirt_{tag}.png",
                       title=f"SIRT | {tag}")

            recon_ossart = reconstruct_os_sart(
                sinogram, angles, gamma=gamma, n_iterations=10, n_subsets=n_subsets
            )
            metrics = compute_all_metrics(phantom, recon_ossart)
            records.append(
                {"experiment": "dose", "method": "OS-SART", "I0": I0,
                 "n_proj": n_proj, "angle_range": 180, **metrics}
            )
            save_image(recon_ossart, images_dir / f"dose_ossart_{tag}.png",
                       title=f"OS-SART | {tag}")


def run_limited_angle_experiments(
    phantom: np.ndarray,
    config: dict,
    images_dir: Path,
    records: list,
) -> None:
    """
    Exercise 1.2: limited-angle tomography.

    Uses the lowest dose level and 90 projections, but varies the
    angular range: 180°, 120°, 40°.
    """
    I0 = config["dose_levels"][0]  # high dose for clean comparison
    n_proj = 90
    gaussian_sigma = config["noise"]["gaussian_sigma"]
    gamma = config["reconstruction"]["iterative"]["gamma"]
    n_iter = config["reconstruction"]["iterative"]["max_iterations"]

    for angle_range in tqdm(config["angular_ranges"], desc="Exercise 1.2 — limited angle"):
        tag = f"angle={angle_range}"
        sinogram, angles = simulate_sinogram(
            phantom,
            num_projections=n_proj,
            max_angle=float(angle_range),
            I0=I0,
            gaussian_sigma=gaussian_sigma,
        )

        recon_fbp = reconstruct_fbp(sinogram, angles, filter_name="ramp")
        metrics = compute_all_metrics(phantom, recon_fbp)
        records.append(
            {"experiment": "limited_angle", "method": "FBP-ramp", "I0": I0,
             "n_proj": n_proj, "angle_range": angle_range, **metrics}
        )
        save_image(recon_fbp, images_dir / f"limited_fbp_{tag}.png",
                   title=f"FBP (ramp) | {tag}")

        recon_sirt = reconstruct_sirt(
            sinogram, angles, gamma=gamma, n_iterations=n_iter
        )
        metrics = compute_all_metrics(phantom, recon_sirt)
        records.append(
            {"experiment": "limited_angle", "method": "SIRT", "I0": I0,
             "n_proj": n_proj, "angle_range": angle_range, **metrics}
        )
        save_image(recon_sirt, images_dir / f"limited_sirt_{tag}.png",
                   title=f"SIRT | {tag}")


def main():
    parser = argparse.ArgumentParser(description="Run CT reconstruction experiments")
    parser.add_argument(
        "--config", default="configs/ct_experiments.yaml",
        help="Path to YAML config file",
    )
    parser.add_argument(
        "--phantom", default=None,
        help="Path to a CT PNG image (default: use Shepp-Logan phantom)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    np.random.seed(config.get("random_seed", 42))

    results_dir = Path("results/ct_reconstruction")
    images_dir = results_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Load phantom
    size = config["phantom"]["size"]
    if args.phantom:
        phantom = load_ct_image(args.phantom, size=size)
        print(f"Loaded CT image from: {args.phantom}")
    else:
        phantom = load_shepp_logan(size=size)
        print("Using Shepp-Logan phantom")

    save_image(phantom, images_dir / "phantom.png", title="Phantom")

    records: list[dict] = []
    run_dose_experiments(phantom, config, images_dir, records)
    run_limited_angle_experiments(phantom, config, images_dir, records)

    df = pd.DataFrame(records)
    metrics_path = results_dir / "metrics.csv"
    df.to_csv(metrics_path, index=False)
    print(f"\nMetrics saved to {metrics_path}")
    print(df.groupby(["experiment", "method"])[["mse", "psnr", "ssim"]].mean().round(4))


if __name__ == "__main__":
    main()
