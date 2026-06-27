import json
from datetime import datetime
from pathlib import Path
import pytest

from astronex.core import ephemeris as pysw
from astronex.core.directions import solar_rev, sec_prog
from astronex.core.utils import strdate_to_date

GOLDEN = json.loads(
    (Path(__file__).parent / "golden" / "directions.json").read_text()
)


# Tolerance for the golden JD comparison. The legacy golden was produced with
# the original Moshier engine (_pysw.so, Py2/32-bit); the port uses modern
# pyswisseph. The port converges *better* (sun(jd) ~= natal to ~1e-7 deg) while
# the legacy result carries a ~1.8e-4 deg solar residual, yielding a uniform
# ~2e-4 day (~17 s) JD difference. This is an ephemeris-engine gap, not a port
# bug, so we assert the port is at least that close to the golden AND -- more
# importantly -- that it actually solves the problem (sun ~= natal).
JD_MOTOR_TOLERANCE = 3e-4   # days (~26 s); see note above
SUN_ROOT_TOLERANCE = 1e-4   # degrees


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_solar_rev_matches_golden(c):
    jd = solar_rev(
        c["natal_sun_lon"],
        c["target_year"],
        c["birth_month"],
        c["birth_day"],
        epheflag=4,
    )
    assert abs(jd - c["jd_solrev"]) < JD_MOTOR_TOLERANCE


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_solar_rev_actually_returns_the_natal_sun(c):
    # Primary physical assertion: at the returned JD the Sun equals the natal
    # Sun. This is the real correctness criterion; the golden JD above only
    # guards against gross divergence.
    jd = solar_rev(
        c["natal_sun_lon"],
        c["target_year"],
        c["birth_month"],
        c["birth_day"],
        epheflag=4,
    )
    _s, sun_now, _e = pysw.calc(jd, 0, 4)
    assert abs(sun_now - c["natal_sun_lon"]) < SUN_ROOT_TOLERANCE


def _natal_dt(c):
    # legacy strdate_to_date returns a naive UTC datetime
    return strdate_to_date(c["natal_dt_iso"])


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_sec_prog_matches_golden(c):
    progdt = sec_prog(_natal_dt(c), c["target_year"], sec_alltimes=False)
    expected = datetime.strptime(c["progdt"], "%Y-%m-%d %H:%M:%S")
    assert abs((progdt - expected).total_seconds()) < 60


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_sec_prog_alltimes_matches_golden(c):
    now_dt = datetime.strptime(c["now_dt"][:19], "%Y-%m-%dT%H:%M:%S")
    progdt = sec_prog(
        _natal_dt(c), c["target_year"], sec_alltimes=True, now_dt=now_dt
    )
    expected = datetime.strptime(c["progdt_alltimes"], "%Y-%m-%d %H:%M:%S")
    assert abs((progdt - expected).total_seconds()) < 60
