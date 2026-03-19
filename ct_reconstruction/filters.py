"""
FBP filter names and validation for CT reconstruction.

Lists the filters supported by ``skimage.transform.iradon`` and
provides a normalisation/validation helper used by the experiment
scripts and tests to catch configuration errors early.
"""

from __future__ import annotations

#: All filter names accepted by ``skimage.transform.iradon``.
AVAILABLE_FILTERS: tuple[str, ...] = (
    "ramp",
    "shepp-logan",
    "cosine",
    "hamming",
    "hann",
)


def validate_filter(name: str) -> str:
    """
    Normalise and validate an FBP filter name.

    Accepts any case variant (e.g. ``"RAMP"``, ``"Ramp"``).

    Parameters
    ----------
    name : str
        Filter name to validate.

    Returns
    -------
    str
        Lower-cased, validated filter name ready to pass to
        ``reconstruct_fbp``.

    Raises
    ------
    ValueError
        If ``name`` is not in :data:`AVAILABLE_FILTERS`.
    """
    normalised = name.lower()
    if normalised not in AVAILABLE_FILTERS:
        raise ValueError(
            f"Unknown filter '{name}'. " f"Available filters: {', '.join(AVAILABLE_FILTERS)}"
        )
    return normalised
