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
