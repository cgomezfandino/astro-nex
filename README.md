# Astro-Nex

Astro-Nex is an astrological chart application implementing the API/Huber method.
**API here stands for Astrologisch-Psychologisches Institut** (founded by Bruno and Louise Huber),
not a web API — it refers to a specific school of psychological astrology that uses age-point
progression and house emphasis in chart interpretation. This project is a modernized rewrite of
the original Astro-Nex 1.2.3 (Python 2 / GTK 2), targeting Python 3.12+ and GTK 3 on macOS
Apple Silicon and Linux.

## Project status

**Phase 1 — Python 3 + GTK 3 vertical slice: complete (v0.1.0).**

The end-to-end pipeline works on macOS (Apple Silicon) and Linux: enter birth data →
compute the Huber chart → draw the radix wheel on screen → export PNG/PDF. Ephemeris
calculations are verified to match the original Python‑2 engine within `1e-4°` via golden
reference data (52 tests passing). See [docs/ROADMAP.md](docs/ROADMAP.md) for what's next
(age point, pixel‑faithful visual, advanced dialogs, API) and [CHANGELOG.md](CHANGELOG.md).

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
astronex
```

GTK 3 is required at the system level (macOS: `brew install gtk+3 pygobject3 gobject-introspection`).

Run the test suite with `pytest`.

## Architecture

Clean layering so the calculation core has no GUI dependency and is reusable for a future API:

| Layer | Responsibility |
|-------|----------------|
| `core/` | ephemeris (pyswisseph), dates/timezones, Huber chart model — no GTK, no cairo |
| `render/` | cairo radix‑wheel renderer + Astro‑Nex symbol font glyphs |
| `surfaces/` | PNG and PDF export |
| `gui/` | thin GTK 3 application shell |

## Documentation

- [Design spec](docs/specs/2026-06-26-astro-nex-py3-gtk3-modernization-design.md)
- [Implementation plan](docs/plans/2026-06-26-astro-nex-py3-gtk3-vertical-slice.md)
- [Roadmap](docs/ROADMAP.md) · [Changelog](CHANGELOG.md)

## License & credits

GPLv3 (required: this work uses the [Swiss Ephemeris](https://www.astro.com/swisseph/) via
`pyswisseph` under its GPL option). Original Astro-Nex by **José Antonio Rodríguez**
(`jar@eideia.net`); see [NOTICE](NOTICE). This is a Python 3 / GTK 3 modernization that
preserves the original calculation behavior.
