"""
Run MRI denoising experiments (Exercises 2.1 and 2.2).

Loads knee.npy k-space data, reconstructs all coils, combines them
with RSS, applies spatial-domain denoising filters and Butterworth
k-space filtering, and saves all output images.

Usage
-----
    python experiments/run_mri_experiments.py
    python experiments/run_mri_experiments.py --kspace knee.npy
    python experiments/run_mri_experiments.py --config configs/mri_denoising.yaml
"""

import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import yaml

from mri_denoising.load_kspace import load_kspace, identify_coil_dimension
from mri_denoising.reconstruction_fft import kspace_to_image, get_magnitude, get_phase
from mri_denoising.coil_combination import combine_coils_rss
from mri_denoising.kspace_visualization import (
    plot_kspace_magnitude,
    plot_magnitude_images,
    plot_magnitude_and_phase,
)
from mri_denoising.denoising_filters import (
    apply_gaussian_filter,
    apply_mean_filter,
    apply_bilateral_filter,
)
from mri_denoising.butterworth_filter import apply_butterworth_filter


def load_config(path: str) -> dict:
    """Load YAML configuration file."""
    with open(path) as f:
        return yaml.safe_load(f)


def save_fig(fig: plt.Figure, path: Path) -> None:
    """Save a matplotlib figure and close it."""
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def run_mri_experiments(
    config: dict,
    kspace_path: Path,
    results_dir: Path,
) -> None:
    np.random.seed(config.get("random_seed", 42))

    images_dir = results_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Exercise 2.1 — Visualisation and k-space inspection                 #
    # ------------------------------------------------------------------ #
    kspace = load_kspace(kspace_path)
    coil_axis = identify_coil_dimension(kspace)
    n_coils = kspace.shape[coil_axis]
    print(f"k-space shape: {kspace.shape} | coil axis: {coil_axis} | n_coils: {n_coils}")

    # Plot k-space log-magnitude for every coil
    fig = plot_kspace_magnitude(kspace, coil_axis=coil_axis)
    save_fig(fig, images_dir / "kspace_magnitude_all_coils.png")

    # Reconstruct all coils
    coil_images = np.stack(
        [kspace_to_image(np.take(kspace, i, axis=coil_axis)) for i in range(n_coils)],
        axis=0,  # stack on axis 0 → shape (n_coils, rows, cols)
    )

    # Magnitude and phase for coil 0
    fig = plot_magnitude_and_phase(coil_images[0], title="Coil 1 — magnitude & phase")
    save_fig(fig, images_dir / "coil1_magnitude_phase.png")

    # Magnitude images for all coils
    fig = plot_magnitude_images(coil_images, coil_axis=0)
    save_fig(fig, images_dir / "all_coils_magnitude.png")

    # RSS coil combination
    combined = combine_coils_rss(coil_images, coil_axis=0)
    plt.imsave(str(images_dir / "combined_rss.png"), combined, cmap="gray")
    print(f"Combined image shape: {combined.shape}")

    # ------------------------------------------------------------------ #
    # Exercise 2.2 — Spatial-domain denoising                             #
    # ------------------------------------------------------------------ #
    filter_map = {
        "gaussian": lambda img: apply_gaussian_filter(img, sigma=config["gaussian"]["sigma"]),
        "mean": lambda img: apply_mean_filter(img, size=config["mean"]["size"]),
        "bilateral": lambda img: apply_bilateral_filter(
            img,
            sigma_color=config["bilateral"]["sigma_color"],
            sigma_spatial=config["bilateral"]["sigma_spatial"],
        ),
    }

    for filt_name in config["filters"]:
        if filt_name not in filter_map:
            print(f"Filter '{filt_name}' not implemented, skipping.")
            continue

        # Apply filter to combined RSS image
        denoised_combined = filter_map[filt_name](combined)
        plt.imsave(
            str(images_dir / f"combined_denoised_{filt_name}.png"),
            denoised_combined,
            cmap="gray",
        )

        # Apply filter to all coils and show result
        denoised_coils = np.stack(
            [filter_map[filt_name](get_magnitude(coil_images[i])) for i in range(n_coils)],
            axis=0,
        )
        fig = plot_magnitude_images(denoised_coils, coil_axis=0,
                                    title_prefix=f"{filt_name} coil")
        save_fig(fig, images_dir / f"all_coils_denoised_{filt_name}.png")

    # ------------------------------------------------------------------ #
    # Exercise 2.2 — Butterworth k-space filter (coil 0)                  #
    # ------------------------------------------------------------------ #
    coil0_kspace = np.take(kspace, 0, axis=coil_axis)
    filtered_kspace = apply_butterworth_filter(
        coil0_kspace,
        D0=config["butterworth"]["cutoff"],
        n=config["butterworth"]["order"],
    )
    filtered_img = kspace_to_image(filtered_kspace)

    fig = plot_magnitude_and_phase(filtered_img, title="Coil 1 — Butterworth filtered")
    save_fig(fig, images_dir / "coil1_butterworth_magnitude_phase.png")

    print(f"\nAll MRI results saved to {results_dir}")


def main():
    parser = argparse.ArgumentParser(description="Run MRI denoising experiments")
    parser.add_argument("--config", default="configs/mri_denoising.yaml")
    parser.add_argument("--kspace", default="knee.npy")
    args = parser.parse_args()

    config = load_config(args.config)
    run_mri_experiments(config, Path(args.kspace), Path("results/mri_denoising"))


if __name__ == "__main__":
    main()
