# Pollen

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=white)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-18BCF2?style=for-the-badge&logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

Home Assistant custom integration for **pollen levels and forecasts**.

v1 uses the [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) (CAMS European pollen). No API key. Coverage is **Europe only**.

## Features

- Six species sensors: alder, birch, grass, mugwort, olive, ragweed (grains/m³)
- One **Overall** sensor: `none` / `low` / `high` plus dominant species
- Full hourly forecast (~4 days) and daily peaks on every sensor as attributes
- Config flow with location (defaults to Home Assistant home)
- Refuses setup outside CAMS coverage (all pollen fields `null`)

## Install (HACS)

Installable through [HACS](https://hacs.xyz/) as a **custom repository** (category: **Integration**).

1. HACS → Integrations → ⋮ → **Custom repositories**
2. Add `https://github.com/tempi-marathon/ha-pollen` (category: Integration)
3. Download **Pollen**, restart Home Assistant
4. Settings → Devices & services → **Add Integration** → **Pollen**

## Entities

One device per config entry. Example entities:

| Entity | State | Useful attributes |
| --- | --- | --- |
| `sensor.pollen_overall` | `none` / `low` / `high` | `level`, `dominant_species`, `forecast_hourly`, `forecast_daily` |
| `sensor.pollen_grass` | grains/m³ | `level_label`, `forecast_hourly`, `forecast_daily` |
| … | … | same for alder, birch, mugwort, olive, ragweed |

Attribute contract (provider-neutral for a future US source):

- `provider` — `open_meteo`
- `species` — canonical key or `overall`
- `unit` — `grains_m3` or `level`
- `level` / `level_label` — `0|1|2` and `none|low|high`
- `forecast_hourly` — `[{ "t": "<iso>", "value": number|null }, …]` full horizon
- `forecast_daily` — `[{ "date": "YYYY-MM-DD", "value": number }, …]`

## Works with Veðurkort

[Veðurkort Weather Card](https://github.com/tempi-marathon/vedurkort-weather-card) can show a pollen chip/detail sheet by pointing `pollen_device` at this integration’s device.

## Attribution

Data provided by [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0). Generated using Copernicus Atmosphere Monitoring Service information.

## License

MIT — see [LICENSE](LICENSE).
