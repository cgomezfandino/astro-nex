"""Smoke tests for the aspect geometry classes (render/aspects.py).

These verify each shape draws without crashing and produces non-blank output.
The geometry is pure cairo; visual fidelity is checked separately (human
comparison vs the legacy). There is no golden for pixels.
"""
import cairo
import pytest

from astronex.render.aspects import (
    ConjunctioAspect,
    UnilateralAspect,
    GoodwillAspect,
    AgePointAspect,
    FususAspect,
)


def _surface():
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 400)
    cr = cairo.Context(surface)
    cr.translate(200, 200)
    return cr, surface


def _sample_aspects():
    # Two planet pairs at known longitudes with orb factors + colours.
    return [
        {"p1": 30.0, "p2": 150.0, "f1": 0.5, "f2": 0.6, "col": (0.2, 0.4, 0.8)},
        {"p1": 90.0, "p2": 270.0, "f1": 0.3, "f2": 0.4, "col": (0.8, 0.2, 0.3)},
    ]


def _ink_present(surface):
    return any(b != 0 for b in bytes(surface.get_data()))


def test_fusus_aspect_draws():
    cr, surface = _surface()
    FususAspect().draw(cr, 150, _sample_aspects())
    assert _ink_present(surface)


def test_goodwill_aspect_draws():
    cr, surface = _surface()
    GoodwillAspect(baseline=2.0).draw(cr, 150, _sample_aspects())
    assert _ink_present(surface)


def test_unilateral_aspect_draws():
    cr, surface = _surface()
    UnilateralAspect(baseline=2.0).draw(cr, 150, _sample_aspects())
    assert _ink_present(surface)


def test_conjunctio_aspect_draws():
    cr, surface = _surface()
    ConjunctioAspect().draw(cr, 150, _sample_aspects(), filter=False)
    assert _ink_present(surface)


def test_agepoint_aspect_draws():
    cr, surface = _surface()
    asps = [{"p1": 30.0, "f": 0.5, "col": (0.1, 0.6, 0.2)},
            {"p1": 210.0, "f": 0.7, "col": (0.6, 0.1, 0.5)}]
    AgePointAspect().draw(cr, 150, asps, pe=120.0)
    assert _ink_present(surface)


def test_conjunctio_handles_zero_distance():
    # Same-chart case: p1 == p2 must not divide by zero.
    cr, surface = _surface()
    asps = [{"p1": 30.0, "p2": 30.0, "f1": 0.5, "f2": 0.5, "col": (0.5, 0.5, 0.5)}]
    ConjunctioAspect().draw(cr, 150, asps, filter=False)  # must not raise
