"""EAACI / CAMS-aligned pollen severity levels (grains/m³ → none/low/medium/high).

Boundary convention: a value equal to a threshold belongs to the higher
level (>=). Below onset → none; onset ≤ x < mid → low; mid ≤ x < peak →
medium; >= peak → high.

``mid`` is the midpoint between onset and peak for each species.

Thresholds for the six Open-Meteo / CAMS species follow the EAACI / CAMS
brackets used by Climate-ADAPT and refined per-species where published
evidence exists (same onset/peak numbers as the open PollenWatch analytics
table for these six species).
"""

from __future__ import annotations

from typing import Final

LEVEL_NONE: Final = 0
LEVEL_LOW: Final = 1
LEVEL_MEDIUM: Final = 2
LEVEL_HIGH: Final = 3

LEVEL_LABELS: Final[dict[int, str]] = {
    LEVEL_NONE: "none",
    LEVEL_LOW: "low",
    LEVEL_MEDIUM: "medium",
    LEVEL_HIGH: "high",
}

# (onset, peak) grains/m³ — mid is derived as (onset + peak) / 2
_THRESHOLDS: Final[dict[str, tuple[float, float]]] = {
    "birch": (20.0, 100.0),
    "alder": (45.0, 80.0),
    "olive": (10.0, 200.0),
    "mugwort": (3.0, 50.0),
    "ragweed": (5.0, 20.0),
    "grass": (3.0, 50.0),
}


def level_for_grains(species: str, grains: float | None) -> int | None:
    """Map grains/m³ to 0/1/2/3, or None when value/species is unknown."""
    if grains is None:
        return None
    bounds = _THRESHOLDS.get(species)
    if bounds is None:
        return None
    onset, peak = bounds
    mid = (onset + peak) / 2.0
    if grains >= peak:
        return LEVEL_HIGH
    if grains >= mid:
        return LEVEL_MEDIUM
    if grains >= onset:
        return LEVEL_LOW
    return LEVEL_NONE


def level_label(level: int | None) -> str | None:
    """Human-readable level label."""
    if level is None:
        return None
    return LEVEL_LABELS.get(level)
