# Roadmap

Astro-Nex is a modernization of the GPLv3 Astro-Nex 1.2.3 created by **José Antonio
Rodríguez (1960–2022)** ([astro-nex.net](https://astro-nex.net/)) — a chart program for the
Bruno & Louise Huber (API — *Astrologisch-Psychologisches Institut*) method. This work and
its future improvements are maintained in his honor and memory.

## Phase 1 — Python 3 + GTK 3 vertical slice ✅ DONE (v0.1.0)

Runs natively on macOS/Linux: birth data → Huber chart → radix wheel on screen → PNG/PDF
export. Clean `core` / `render` / `surfaces` / `gui` layering. Calculations verified against
the original engine (≤ `1e-4°`) via golden data generated from the legacy app in Docker.

## Phase 2 — Feature parity & community release (in progress)

Bring the app toward the original's capabilities and prepare it as a community project.
Split into sub-milestones (2A–2E); see the GitHub milestones board for issues.

### Phase 2A — Data foundations ✅ DONE

- **`config.py`** (#13), **`state.py`** (#12), **`zodiac.py`** (#14),
  **`countries.py`** (#15), **`database.py`** (#11): the data/state layer ported
  to Py3 (TDD, 125 tests). `Current` singleton completes once `NeXDate` lands in 2B.

### Phase 2B — Calculation engine (next)

- **Age point** (Huber *Lebensuhr* / age progression): port the calculation and draw the
  age-point spiral. The single most distinctive Huber feature.
- **Directions**: solar revolution & secondary progressions.
- **Chart types**: Nodal, House, Local, Soul/Causal, Dharma, Prof, Transits, UR-Nodal.
- **Historical-DST timezones** (`tz_sup`): correct handling of pre-standard-time births.

### Phase 2C — Drawing engine
- **Pixel-faithful rendering**: coredraw, aspects, datasheets, diagrams, planetogram,
  biograph, paarwabe (Huber waves). Parity checked against the Docker original.

### Phase 2D — Full GUI
- **Advanced dialogs**: couples/synastry, cycles, transits, PDF batch, plagram, saved-chart
  database — porting the remaining GTK 2 dialogs to GTK 3.
- **GUI input validation**: error dialogs instead of crashes on malformed input.

### Phase 2E — macOS packaging
- **CI**: GitHub Actions running `pytest` on macOS + Linux.
- **Packaging**: `Astro-Nex.app` (autocontained, spec
  `docs/superpowers/specs/2026-06-27-macos-app-bundling-design.md`) + `.dmg`/signing
  (#10, requires Apple Developer ID).

## Phase 3 — Astro Soul Center integration

Wrap the GUI-free `core/` in a service API for the Astro Soul Center product.

- HTTP/JSON API over the chart core (the core was designed GUI-free for exactly this).
- **Licensing note**: exposing Swiss Ephemeris as a network service can trigger AGPL
  obligations on modern Swiss Ephemeris versions — release the service under (A)GPL or obtain
  the commercial Astrodienst license before going live.
- Concurrency note: `core/chart.py`'s module-level `orbs` is intentionally mutable for the
  config-override path; thread orb tables per request before exposing it concurrently.
