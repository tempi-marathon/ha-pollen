"""Provider-neutral pollen snapshot models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ForecastPoint:
    """One forecast sample."""

    t: str
    value: float | None


@dataclass(frozen=True, slots=True)
class DailyPeak:
    """Daily peak concentration."""

    date: str
    value: float | None


@dataclass(frozen=True, slots=True)
class SpeciesReading:
    """Current value + forecast for one species."""

    species: str
    current: float | None
    unit: str
    level: int | None
    level_label: str | None
    forecast_hourly: tuple[ForecastPoint, ...] = ()
    forecast_daily: tuple[DailyPeak, ...] = ()


@dataclass(frozen=True, slots=True)
class PollenSnapshot:
    """Full poll result for one location."""

    provider: str
    latitude: float
    longitude: float
    generated_at: str | None
    readings: dict[str, SpeciesReading] = field(default_factory=dict)
    overall_level: int | None = None
    overall_level_label: str | None = None
    dominant_species: str | None = None
    in_coverage: bool = True
    attribution: str = ""

    def overall_hourly(self) -> tuple[ForecastPoint, ...]:
        """Per-hour max grains/m³ across species (not max severity).

        Overall *state* uses severity levels (species thresholds differ).
        Overall *forecast values* stay as max raw grains so consumers such as
        Veðurkort can chart a numeric series under the existing attribute
        contract.
        """
        if not self.readings:
            return ()
        first = next(iter(self.readings.values()))
        times = [p.t for p in first.forecast_hourly]
        out: list[ForecastPoint] = []
        for i, t in enumerate(times):
            values = [
                r.forecast_hourly[i].value
                for r in self.readings.values()
                if i < len(r.forecast_hourly) and r.forecast_hourly[i].value is not None
            ]
            out.append(ForecastPoint(t=t, value=max(values) if values else None))
        return tuple(out)

    def overall_daily(self) -> tuple[DailyPeak, ...]:
        """Per-day max grains/m³ across species (same contract as overall_hourly)."""
        by_date: dict[str, list[float]] = {}
        for reading in self.readings.values():
            for peak in reading.forecast_daily:
                if peak.value is None:
                    continue
                by_date.setdefault(peak.date, []).append(peak.value)
        return tuple(
            DailyPeak(date=date, value=max(vals))
            for date, vals in sorted(by_date.items())
        )
