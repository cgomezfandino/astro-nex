import json
from pathlib import Path
import pytest
from astronex.core.chart import Chart

GOLDEN = json.loads((Path(__file__).parent / "golden" / "ephemeris.json").read_text())

def _chart(c):
    ch = Chart()
    ch.calc((c["jd_y"], c["jd_m"], c["jd_d"], c["jd_h"]), loc=(c["lat"], c["lon"]), epheflag=4)
    return ch

@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_chart_planet_longitudes(c):
    ch = _chart(c)
    assert len(ch.planets) == len(c["planets"])
    for got, ref in zip(ch.planets, c["planets"]):
        assert abs(got - ref) < 1e-4

@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_chart_houses(c):
    ch = _chart(c)
    assert len(ch.houses) == len(c["houses"])
    for got, ref in zip(ch.houses, c["houses"]):
        assert abs(got - ref) < 1e-4

@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_chart_sun_sign(c):
    ch = _chart(c)
    assert ch.which_sign(ch.planets[0])["name"] == int(c["planets"][0] // 30) % 12

@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_which_house_valid(c):
    ch = _chart(c)
    h = ch.which_house(ch.planets[0])
    assert h is None or h in range(12)

@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_aspects_smoke(c):
    ch = _chart(c)
    asp = ch.aspects()
    assert isinstance(asp, list)
    for a in asp:
        assert set(["p1", "p2", "a", "f1", "f2"]).issubset(a.keys())
