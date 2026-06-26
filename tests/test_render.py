import cairo
from astronex.core.chart import Chart
from astronex.render.wheel import draw_radix


def _chart():
    ch = Chart()
    ch.calc((1985, 6, 15, 7.5), loc=(51.5074, -0.1278), epheflag=4)
    return ch


def test_draw_radix_produces_nonblank_surface(tmp_path):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 600, 600)
    cr = cairo.Context(surface)
    draw_radix(cr, _chart(), size=600)
    out = tmp_path / "wheel.png"
    surface.write_to_png(str(out))
    data = bytes(surface.get_data())
    assert any(b != 0 for b in data)  # something was drawn


def test_draw_radix_runs_without_chart_data():
    # must not crash on an empty/uncalculated chart (defensive)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 200)
    cr = cairo.Context(surface)
    ch = Chart()
    # uncalculated chart has empty planets/houses; draw_radix should no-op or guard
    draw_radix(cr, ch, size=200)
