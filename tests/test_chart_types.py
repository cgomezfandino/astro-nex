import json
from pathlib import Path
import pytest

from astronex.core.chart import Chart

GOLDEN = json.loads(
    (Path(__file__).parent / "golden" / "chart_types.json").read_text()
)

# Tier-A chart-type methods are PURE transforms of planets/houses (no ephemeris
# call of their own), so they must match the legacy golden EXACTLY.
TOL = 1e-9


def _chart(c):
    ch = Chart()
    # bypass calc(); feed planets/houses directly (the golden captured them)
    ch.planets = list(c["planets"])
    ch.houses = list(c["houses"])
    return ch


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_nod_plan_long(c):
    got = _chart(c).nod_plan_long()
    for g, ref in zip(got, c["nod_plan"]):
        assert abs(g - ref) < TOL


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_nod_sign_long(c):
    got = _chart(c).nod_sign_long()
    for g, ref in zip(got, c["nod_sign"]):
        assert abs(g - ref) < TOL


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_nodal_cusp_degrees(c):
    got = _chart(c).nodal_cusp_degrees()
    for g, ref in zip(got, c["nodal_cusps"]):
        assert abs(g - ref) < TOL


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_house_sign_long(c):
    got = _chart(c).house_sign_long()
    for g, ref in zip(got, c["house_sign_long"]):
        assert abs(g - ref) < TOL


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_sign_sizes(c):
    got = _chart(c).sign_sizes()
    for g, ref in zip(got, c["sign_sizes"]):
        assert abs(g - ref) < TOL


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_sign_in_house(c):
    got = _chart(c).sign_in_house()
    for g, ref in zip(got, c["sign_in_house"]):
        assert g == ref


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_invert_house_plan_round_trips_house_plan_long(c):
    ch = _chart(c)
    hpl = ch.house_plan_long()
    got = ch.invert_house_plan(hpl)
    for g, ref in zip(got, c["invert_house_plan"]):
        assert abs(g - ref) < TOL


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_invert_house_sign_round_trips_house_sign_long(c):
    ch = _chart(c)
    hsl = ch.house_sign_long()
    got = ch.invert_house_sign(hsl)
    for g, ref in zip(got, c["invert_house_sign"]):
        assert abs(g - ref) < TOL


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_which_house_nodal(c):
    ch = _chart(c)
    got = [ch.which_house_nodal(p) for p in c["planets"]]
    assert got == c["which_house_nodal"]


# --- Tier B: local houses (relocated) ---

@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_calc_localhouses(c):
    from astronex.core.ephemeris import julday, local_houses
    jd = julday(c["jd_y"], c["jd_m"], c["jd_d"], c["jd_h"])
    got = list(local_houses(jd, c["lon"], c["lat"], 4))
    for g, ref in zip(got, c["local_houses"]):
        assert abs(g - ref) < 1e-4   # fresh ephemeris call -> engine tolerance


# --- Tier D: profession force (output is a 3-tuple, not longitudes) ---

@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_pers_force(c):
    got = _chart(c).pers_force()
    sun, moon, sat = got
    ref = c["pers_force"]
    assert abs(sun - ref[0]) < 1e-6
    assert abs(moon - ref[1]) < 1e-6
    assert abs(sat - ref[2]) < 1e-6
