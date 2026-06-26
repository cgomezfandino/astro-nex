from datetime import datetime
from zoneinfo import ZoneInfo
from astronex.core.nexdate import NeXDate
from astronex.core.chart import Chart
from astronex.surfaces.png import export_png
from astronex.surfaces.pdf import export_pdf


def test_full_pipeline(tmp_path):
    nd = NeXDate(datetime(1969, 7, 20, 20, 17), tz=ZoneInfo("Europe/Paris"))
    ch = Chart()
    ch.calc(nd.dateforcalc(), loc=(48.8566, 2.3522), epheflag=4)
    assert len(ch.planets) == 11
    assert len(ch.houses) == 12
    export_png(ch, str(tmp_path / "e.png"))
    export_pdf(ch, str(tmp_path / "e.pdf"))
    assert (tmp_path / "e.png").stat().st_size > 1000
    assert (tmp_path / "e.pdf").read_bytes().startswith(b"%PDF")


def test_main_importable():
    # main() must be importable without a display (GUI import is deferred inside it)
    from astronex.__main__ import main
    assert callable(main)
