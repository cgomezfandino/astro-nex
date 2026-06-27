# Changelog

_In memory of José Antonio Rodríguez (1960–2022), creator of Astro-Nex — maintained in his honor._

All notable changes to this project are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased] — Phase 2B: Calculation engine

Ports the directional techniques, the chart-type transforms, and the NeXDate
surface needed to close the cycle with `Current`. All verified test-first
against golden data generated from the **original** Python 2 engine running
unmodified in Docker. **213 tests passing.**

### Added
- **`core/directions.py`** (#16): solar revolution (`solar_rev`) and secondary
  progression (`sec_prog`) as pure functions (no `boss`/GUI/`Current` mutation).
  `solar_rev` uses a clean ~40-eval bisection (replacing the legacy's 6 nested
  loops) and converges closer to the true root than the legacy Moshier engine;
  verified both by golden proximity (3e-4 day, the engine gap) and by the
  physical property `sun(jd) ≈ natal`. Includes a wraparound fix at the
  0/360 equinox boundary.
- **`core/nexdate.py`**: completed `NeXDate` with `setdt`, `set_now`,
  `set_delta`, `dateforstore` (and `getnewdt` from #16). DST-fold policy is
  `fold=0` (zoneinfo), which matches the legacy `pytz localize(is_dst=True)`.
- **`core/chart.py`** (#18): chart-type transforms verified exact (1e-9 / 1e-6)
  vs the legacy golden — Tier A (Nodal, House/Dharma sign-side, inverts,
  which_house_nodal), Tier B (`local_houses` contract), Tier D (Huber
  professional factors `pers_force` family), and the Tier C Transits contract.
- **Golden harness** (`tools/original-docker/`): `boss_stub.py` runs the legacy
  `solar_rev`/`sec_prog` headless; `dump_chart_types` exercises the Tier A/D
  transforms via a minimal Chart stub; `gen_golden.sh` regenerates all goldens
  reproducibly. Datasets extended with zone/target_year/now_dt (incl. an
  equinox case that locks the solar_rev wraparound fix).

## [Superseded] — Phase 2A: Data foundations

Ports the dependency/data layer of the original Astro-Nex to Python 3, unblocking
the full feature port (2B–2D). Developed test-first (TDD) against the bundled
real SQLite data; verified via a cross-module integration smoke test.

### Added
- **`core/config.py`** (#13): default constants, `NexConf` options object, and
  colour parsing. Replaces `gtk.gdk.color_parse` with a pure `hex_to_rgb`
  (removing GTK from the core) and `configobj` with stdlib `configparser`.
- **`core/state.py`** (#12): operation/category constant lists, `Locality`,
  `PersonInfo`, and the `Current` singleton (application-wide state). `Current`
  methods needing the not-yet-ported `NeXDate` pieces land in 2B.
- **`core/zodiac.py`** (#14): `Zodiac` glyph-path cache + colour palette, using
  `render.glyphs.set_symbol_font` (FreeType) for the real symbol glyphs.
- **`core/countries.py`** (#15): multilingual country/region data (`__builtin__`
  → `builtins`).
- **`core/database.py`** (#11): localities + charts SQLite store. `local.db`
  (279 tables, bundled in `data/`), `cursor.next()` → `next(cursor)`,
  `pathlib`. Fixed a `store_chart` named/positional placeholder bug caught by TDD.

### Tests
- 73 new tests (52 → **125 passing**); DB tests run against real locality lookups
  (Spain/Girona, California) and an ephemeral charts store.

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
