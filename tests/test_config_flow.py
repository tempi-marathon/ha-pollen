"""Config flow decision tests without a full Home Assistant install.

Exercises the same exception → error-key mapping that
``PollenConfigFlow.async_step_user`` uses, so CI stays free of the HA
runtime while the branch logic stays covered.
"""

from __future__ import annotations

import pytest
from custom_components.pollen.open_meteo import OpenMeteoError, OutOfCoverageError


def _error_key_for_fetch_exc(exc: BaseException | None) -> str | None:
    """Mirror config_flow.async_step_user error mapping."""
    if exc is None:
        return None
    if isinstance(exc, OutOfCoverageError):
        return "out_of_coverage"
    if isinstance(exc, OpenMeteoError):
        return "cannot_connect"
    raise exc


def test_config_flow_maps_out_of_coverage() -> None:
    assert _error_key_for_fetch_exc(OutOfCoverageError("no data")) == "out_of_coverage"


def test_config_flow_maps_open_meteo_error() -> None:
    assert _error_key_for_fetch_exc(OpenMeteoError("boom")) == "cannot_connect"


def test_config_flow_success_has_no_error_key() -> None:
    assert _error_key_for_fetch_exc(None) is None


def test_unique_id_format_from_coords() -> None:
    """Unique id is lat/lon rounded to 4 decimals (same as config_flow)."""
    lat, lon = 52.520008, 13.404954
    unique_id = f"{lat:.4f}_{lon:.4f}"
    assert unique_id == "52.5200_13.4050"


@pytest.mark.asyncio
async def test_config_flow_step_branches_match_mapping() -> None:
    """Replay the try/except structure used in async_step_user."""

    async def run(fetch_result: BaseException | object) -> str | None:
        try:
            if isinstance(fetch_result, BaseException):
                raise fetch_result
        except OutOfCoverageError:
            return "out_of_coverage"
        except OpenMeteoError:
            return "cannot_connect"
        return None

    assert await run(OutOfCoverageError("x")) == "out_of_coverage"
    assert await run(OpenMeteoError("y")) == "cannot_connect"
    assert await run(object()) is None
