import json
from pathlib import Path
import pytest
from astronex.core import ephemeris as e

GOLDEN = json.loads((Path(__file__).parent / "golden" / "ephemeris.json").read_text())

@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_julday_matches(c):
    assert abs(e.julday(c["jd_y"], c["jd_m"], c["jd_d"], c["jd_h"]) - c["jd"]) < 1e-6

@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_planets_match_golden(c):
    got = e.planets(c["jd"], 4)
    assert len(got) == len(c["planets"])
    for g, ref in zip(got, c["planets"]):
        assert abs(g - ref) < 1e-4

@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_houses_match_golden(c):
    got = list(e.houses(c["jd"], c["lat"], c["lon"]))
    assert len(got) == len(c["houses"])
    for g, ref in zip(got, c["houses"]):
        assert abs(g - ref) < 1e-4

@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_calc_ut_with_speed_matches_golden(c):
    jd = c["jd"]
    k = 0
    for i in range(12):
        if i == 10:          # legacy skips body 10 (same as planets/with_speed generation)
            continue
        status, lon, spd, err = e.calc_ut_with_speed(jd, i, 4)
        ref_lon, ref_spd = c["with_speed"][k]
        assert abs(lon - ref_lon) < 1e-4
        assert abs(spd - ref_spd) < 1e-4
        k += 1

@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_local_houses_matches_golden(c):
    if c.get("local_houses") is None:
        pytest.skip("no local_houses in golden record")
    got = list(e.local_houses(c["jd"], c["lon"], c["lat"], 4))
    assert len(got) == len(c["local_houses"])
    for g, ref in zip(got, c["local_houses"]):
        assert abs(g - ref) < 1e-4
