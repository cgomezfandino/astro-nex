import json
from datetime import datetime
from pathlib import Path
import pytest

from astronex.core.age_point import (
    get_cycles,
    house_time_lapsus,
    age_point_longitude,
)

GOLDEN = json.loads(
    (Path(__file__).parent / "golden" / "age_point.json").read_text()
)

# The Age Point pointer is pure arithmetic on house longitudes + age. The golden
# fed the SAME houses to the legacy, so the output must match EXACTLY.
TOL = 1e-9


def _birth_dt(c):
    # Parse the full natal datetime incl. time-of-day -- the lapsus boundaries
    # carry the natal clock time, so the pointer fraction depends on it.
    return datetime.strptime(c["birth_date_iso"][:19], "%Y-%m-%dT%H:%M:%S")


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_get_cycles(c):
    now_dt = datetime(c["now_year"], 7, 1, 12, 0, 0)
    assert get_cycles(_birth_dt(c).year, now_dt.year) == c["cycles"]


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_age_point_longitude_radix(c):
    now_dt = datetime(c["now_year"], 7, 1, 12, 0, 0)
    pe = age_point_longitude(c["houses"], _birth_dt(c), now_dt, c["cycles"], kind="radix")
    assert abs(pe - c["pe_radix"]) < TOL


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_age_point_longitude_nodal(c):
    now_dt = datetime(c["now_year"], 7, 1, 12, 0, 0)
    pe = age_point_longitude(
        c["houses"], _birth_dt(c), now_dt, c["cycles"], kind="nodal",
        node_lon=c["node_lon"])
    assert abs(pe - c["pe_nodal"]) < TOL


def test_age_point_at_birth_is_ascendant():
    # At age ~0 the radix pointer should be at the Ascendant (houses[0]).
    from astronex.core.chart import Chart
    ch = Chart(); ch.calc((1985, 6, 15, 7.5), loc=(51.5074, -0.1278), epheflag=4)
    birth = datetime(1985, 6, 15, 7, 30)
    pe = age_point_longitude(ch.houses, birth, birth, 0, kind="radix")
    assert abs(pe - ch.houses[0]) < 1.0  # ~0 days in -> near ASC


def test_house_time_lapsus_is_six_years():
    birth = datetime(1985, 6, 15, 8, 30)
    t = house_time_lapsus(birth, house=0)
    # house 0 spans 6 years
    assert t["lapsus"].days >= 365 * 6 - 2 and t["lapsus"].days <= 366 * 6 + 2
    assert t["begin"] == birth
