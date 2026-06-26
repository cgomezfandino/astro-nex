# Roadmap

Astro-Nex is a modernization of José Antonio Rodríguez's GPLv3 Astro-Nex 1.2.3, a chart
program for the Bruno & Louise Huber (API — *Astrologisch-Psychologisches Institut*) method.

## Phase 1 — Python 3 + GTK 3 vertical slice ✅ DONE (v0.1.0)

Runs natively on macOS/Linux: birth data → Huber chart → radix wheel on screen → PNG/PDF
export. Clean `core` / `render` / `surfaces` / `gui` layering. Calculations verified against
the original engine (≤ `1e-4°`) via golden data generated from the legacy app in Docker.

## Phase 2 — Feature parity & community release (next)

Bring the app toward the original's capabilities and prepare it as a community project.

- **Age point** (Huber *Lebensuhr* / age progression): port the calculation and draw the
  age-point spiral. The single most distinctive Huber feature.
- **Pixel-faithful radix visual**: colour zones, low points, aspect colouring, and the exact
  geometry of the original `coredraw` rendering.
- **Advanced dialogs**: couples/synastry, cycles, transits, PDF batch, plagram, saved-chart
  database — porting the remaining GTK 2 dialogs to GTK 3.
- **GUI input validation**: error dialogs instead of crashes on malformed input.
- **Historical-DST timezones** (`tz_sup`): correct handling of pre-standard-time births.
- **CI**: GitHub Actions running `pytest` on macOS + Linux.
- **Packaging**: `.app`/`.dmg` and/or a pip-installable distribution.

## Phase 3 — Astro Soul Center integration

Wrap the GUI-free `core/` in a service API for the Astro Soul Center product.

- HTTP/JSON API over the chart core (the core was designed GUI-free for exactly this).
- **Licensing note**: exposing Swiss Ephemeris as a network service can trigger AGPL
  obligations on modern Swiss Ephemeris versions — release the service under (A)GPL or obtain
  the commercial Astrodienst license before going live.
- Concurrency note: `core/chart.py`'s module-level `orbs` is intentionally mutable for the
  config-override path; thread orb tables per request before exposing it concurrently.
