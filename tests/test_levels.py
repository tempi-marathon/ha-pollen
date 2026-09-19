"""Tests for pollen severity levels."""

from custom_components.pollen.levels import (
    LEVEL_HIGH,
    LEVEL_LOW,
    LEVEL_MEDIUM,
    LEVEL_NONE,
    level_for_grains,
    level_label,
)


def test_grass_thresholds() -> None:
    # onset 3, peak 50 → mid 26.5
    assert level_for_grains("grass", 0) == LEVEL_NONE
    assert level_for_grains("grass", 2.9) == LEVEL_NONE
    assert level_for_grains("grass", 3) == LEVEL_LOW
    assert level_for_grains("grass", 26.4) == LEVEL_LOW
    assert level_for_grains("grass", 26.5) == LEVEL_MEDIUM
    assert level_for_grains("grass", 49.9) == LEVEL_MEDIUM
    assert level_for_grains("grass", 50) == LEVEL_HIGH


def test_birch_thresholds() -> None:
    # onset 20, peak 100 → mid 60
    assert level_for_grains("birch", 19.9) == LEVEL_NONE
    assert level_for_grains("birch", 20) == LEVEL_LOW
    assert level_for_grains("birch", 59.9) == LEVEL_LOW
    assert level_for_grains("birch", 60) == LEVEL_MEDIUM
    assert level_for_grains("birch", 100) == LEVEL_HIGH


def test_ragweed_thresholds() -> None:
    # onset 5, peak 20 → mid 12.5
    assert level_for_grains("ragweed", 4.9) == LEVEL_NONE
    assert level_for_grains("ragweed", 5) == LEVEL_LOW
    assert level_for_grains("ragweed", 12.4) == LEVEL_LOW
    assert level_for_grains("ragweed", 12.5) == LEVEL_MEDIUM
    assert level_for_grains("ragweed", 20) == LEVEL_HIGH


def test_unknown_species_and_none() -> None:
    assert level_for_grains("oak", 100) is None
    assert level_for_grains("grass", None) is None
    assert level_label(None) is None
    assert level_label(LEVEL_LOW) == "low"
    assert level_label(LEVEL_MEDIUM) == "medium"
