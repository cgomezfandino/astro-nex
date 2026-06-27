from astronex.core.chart import Chart
from astronex.surfaces.png import export_png
from astronex.surfaces.pdf import export_pdf


def _chart():
    ch = Chart()
    ch.calc((2000, 12, 31, 23.25), loc=(-34.6037, -58.3816), epheflag=4)
    return ch


def test_export_png(tmp_path):
    out = tmp_path / "c.png"
    export_png(_chart(), str(out), size=800)
    assert out.exists() and out.stat().st_size > 1000


def test_export_pdf(tmp_path):
    out = tmp_path / "c.pdf"
    export_pdf(_chart(), str(out), size=800)
    assert out.exists() and out.read_bytes().startswith(b"%PDF")


def test_export_png_view_modes(tmp_path):
    for mode in ("wheel", "datasheet", "diagram"):
        out = tmp_path / ("c_%s.png" % mode)
        export_png(_chart(), str(out), kind="radix", view_mode=mode, size=600)
        assert out.exists() and out.stat().st_size > 1000, mode


def test_export_pdf_datasheet(tmp_path):
    out = tmp_path / "c_sheet.pdf"
    export_pdf(_chart(), str(out), kind="radix", view_mode="datasheet", size=600)
    assert out.exists() and out.read_bytes().startswith(b"%PDF")


def test_export_wheel_kind_soul(tmp_path):
    out = tmp_path / "c_soul.png"
    export_png(_chart(), str(out), kind="soul", view_mode="wheel", size=600)
    assert out.exists() and out.stat().st_size > 1000
