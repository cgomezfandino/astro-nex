from datetime import datetime
from zoneinfo import ZoneInfo

from astronex.core.chart import Chart
from astronex.core.directions import solar_rev
from astronex.core.ephemeris import revjul
from astronex.core.nexdate import NeXDate
from astronex.surfaces.png import export_png


def test_solar_rev_feeds_full_pipeline(tmp_path):
    # Natal: 1985-06-15 08:30 London. Project the solar return for 2025.
    nd = NeXDate(datetime(1985, 6, 15, 8, 30), tz=ZoneInfo("Europe/London"))
    natal = Chart()
    natal.calc(nd.dateforcalc(), loc=(51.5074, -0.1278), epheflag=4)

    jd = solar_rev(natal.planets[0], 2025, 6, 15, epheflag=4)
    sol = revjul(jd)  # (y, m, d, h) UT

    # Build a chart at the return moment and export it -- the whole pipeline
    # must run without error and produce a non-trivial image.
    ret = Chart()
    ret.calc(sol, loc=(51.5074, -0.1278), epheflag=4)
    out = tmp_path / "return.png"
    export_png(ret, str(out))
    assert out.exists() and out.stat().st_size > 1000
