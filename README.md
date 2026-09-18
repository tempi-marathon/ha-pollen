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

One device per config entry. Seven sensors:

| Entity | Name | State | Attributes |
| --- | --- | --- | --- |
| `sensor.pollen_overall` | Overall | `none` / `low` / `high` | `provider`, `species`, `unit`, `level`, `level_label`, `dominant_species`, `forecast_hourly`, `forecast_daily`, `attribution` |
| `sensor.pollen_alder` | Alder | grains/m³ | `provider`, `species`, `unit`, `level`, `level_label`, `forecast_hourly`, `forecast_daily`, `attribution` |
| `sensor.pollen_birch` | Birch | grains/m³ | same as alder |
| `sensor.pollen_grass` | Grass | grains/m³ | same as alder |
| `sensor.pollen_mugwort` | Mugwort | grains/m³ | same as alder |
| `sensor.pollen_olive` | Olive | grains/m³ | same as alder |
| `sensor.pollen_ragweed` | Ragweed | grains/m³ | same as alder |

Attribute contract (provider-neutral for a future US source):

- `provider` — `open_meteo`
- `species` — `overall` \| `alder` \| `birch` \| `grass` \| `mugwort` \| `olive` \| `ragweed`
- `unit` — `level` (overall) or `grains_m3` (species)
- `level` / `level_label` — `0\|1\|2` and `none\|low\|high`
- `dominant_species` — overall only; highest active species key, or `null` when none
- `forecast_hourly` — `[{ "t": "<iso>", "value": number\|null }, …]` full horizon (~4 days)
- `forecast_daily` — `[{ "date": "YYYY-MM-DD", "value": number }, …]` daily peaks
- `attribution` — Open-Meteo / CAMS credit string

## Works with Veðurkort

[Veðurkort Weather Card](https://github.com/tempi-marathon/vedurkort-weather-card) can show a pollen chip/detail sheet by pointing `pollen_device` at this integration’s device.

## Attribution

Data provided by [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0). Generated using Copernicus Atmosphere Monitoring Service information.

The HACS / Home Assistant brand icon (`custom_components/pollen/brand/icon.png`) is a static export of the **pollen-grass** icon from [Meteocons](https://meteocons.com/) by [Bas Milius](https://github.com/basmilius/meteocons) (MIT).

## License

MIT — see [LICENSE](LICENSE).
