# Changelog

_In memory of José Antonio Rodríguez (1960–2022), creator of Astro-Nex — maintained in his honor._

All notable changes to this project are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-06-26 — Phase 1: Python 3 + GTK 3 vertical slice

First modernized release. Ports the legacy Astro-Nex 1.2.3 (Python 2 / PyGTK 2 /
Linux-only Swiss Ephemeris `.so`) to Python 3.12+ and GTK 3, running natively on macOS
(Apple Silicon) and Linux.

### Added
- **`core/`** (no GTK, no cairo): `ephemeris` (Swiss Ephemeris via `pyswisseph`,
  re-implementing the legacy `pysw` interface), `nexdate`/`timezones` (stdlib `zoneinfo`),
  `chart` (radix subset of the Huber model), `utils`, `constants`.
- **`render/`**: clean cairo radix-wheel renderer (`draw_radix`) drawing the sign ring,
  house cusps, planets and aspect lines, with Astro-Nex symbol-font glyphs.
- **`surfaces/`**: PNG and PDF export reusing the renderer.
- **`gui/`**: thin GTK 3 application (`python -m astronex`) — birth-data form, on-screen
  chart view, PNG/PDF export.
- **Golden verification harness** (`tools/original-docker/`): runs the original Python-2
  engine in Docker to generate reference charts; the modernized core is tested against them.
- **52 tests** (`pytest`), GPLv3 license + NOTICE crediting the original author.

### Verified
- Planet longitudes and house cusps match the original engine within `1e-4°` across four
  reference charts (1969–2000, both hemispheres, E/W longitudes).

### Deferred (tracked as issues — see ROADMAP)
Age point (Huber *Lebensuhr*), pixel-faithful original visual (colour zones, low points,
aspect colouring), advanced dialogs (couples/cycles/transits/PDF-batch/database), GUI input
validation, historical-DST handling, packaging, and a service API.
