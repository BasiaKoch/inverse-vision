"""
Filter utilities for FBP reconstruction.

Provides a validated list of ramp filters supported by scikit-image's
iradon and a helper to validate user-supplied filter names.
"""

AVAILABLE_FILTERS: list[str] = ["ramp", "shepp-logan", "cosine", "hamming", "hann"]

FILTER_DESCRIPTIONS: dict[str, str] = {
    "ramp": "Ram-Lak — ideal high-pass ramp; sharpest but most noise-sensitive.",
    "shepp-logan": "Shepp-Logan — ramp multiplied by sinc; reduces high-frequency amplification.",
    "cosine": "Cosine — smoother roll-off than Shepp-Logan; good balance of sharpness/noise.",
    "hamming": "Hamming — strong noise suppression; slightly blurred edges.",
    "hann": "Hann — strongest smoothing; lowest noise, least sharp.",
}


def validate_filter(filter_name: str) -> str:
    """
    Validate and normalise a filter name for use with iradon.

    Parameters
    ----------
    filter_name : str
        Requested filter name (case-insensitive, underscores allowed).

    Returns
    -------
    str
        Validated filter name in the format expected by skimage.

    Raises
    ------
    ValueError
        If filter_name is not in AVAILABLE_FILTERS.
    """
    normalised = filter_name.lower().replace("_", "-")
    if normalised not in AVAILABLE_FILTERS:
        raise ValueError(
            f"Unknown filter '{filter_name}'. "
            f"Available filters: {AVAILABLE_FILTERS}"
        )
    return normalised
