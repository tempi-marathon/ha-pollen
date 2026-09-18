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

This is a Home Assistant integration via HACS. Please report security issues in **this** repository’s code or its direct dependencies. Problems in Home Assistant, HACS, other integrations, or Open Food Facts belong upstream unless this integration mishandles their data.

In-scope examples: inventory storage, websocket/actions, the sidebar panel bundle, and how this integration talks to Home Assistant.

## Distribution integrity

HACS installs the integration from this repository. Home Assistant serves that file as the sidebar panel.

Treat that file as part of the trusted release surface: tag releases from verified CI builds, and verify the committed `dist/` artifact matches a local `npm run build` before publishing.
