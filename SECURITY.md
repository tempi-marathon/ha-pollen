# Security Policy

## Supported versions

Security fixes are applied to the latest release on `main`. Older tagged releases are not backported unless noted otherwise.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Prefer one of these options:

1. **[GitHub private vulnerability reporting](https://github.com/tempi-marathon/ha-pollen/security/advisories/new)** (preferred)
2. Contact the maintainer via GitHub: [@tempi-marathon](https://github.com/tempi-marathon)

Include a short description, steps to reproduce, and the affected version or commit if you can.

I’ll look into reports as soon as I can and follow up when there’s a fix or decision.

## Scope

This is a Home Assistant custom integration distributed via HACS. Please report security issues in **this** repository’s code. Problems in Home Assistant, HACS, or Open-Meteo belong upstream unless this integration mishandles their data.

In-scope examples:

- How the config flow and coordinator call the Open-Meteo Air Quality API
- Parsing of untrusted JSON into sensor state and attributes
- Secrets handling (this integration requires no API key today)
- Supply-chain issues in this repo’s GitHub Actions workflows

Out of scope: Home Assistant core, HACS itself, and Open-Meteo / CAMS data quality.

## Distribution integrity

HACS installs the integration source from this repository (no separate frontend bundle). Tag releases from a clean `main` after CI (hassfest, HACS validate, pytest) has passed, and prefer SHA-pinned GitHub Actions.
