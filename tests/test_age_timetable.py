import json
from datetime import datetime
from pathlib import Path
import pytest

from astronex.core.age_point import (
    house_degree,
    pl_midpoints,
    calc_agep,
)

GOLDEN = json.loads(
    (Path(__file__).parent / "golden" / "age_timetable.json").read_text()
)


def _birth_dt(c):
    return datetime.strptime(c["birth_date_iso"][:19], "%Y-%m-%dT%H:%M:%S")


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_house_degree(c):
    got = house_degree(c["houses"])
    for g, ref in zip(got, c["house_degree"]):
        assert abs(g - ref) < 1e-9


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_pl_midpoints(c):
    got = pl_midpoints(c["houses"], c["plan"])
    assert len(got) == len(c["pl_midpoints"])
    for g, ref in zip(got, c["pl_midpoints"]):
        assert abs(g["degree"] - ref["degree"]) < 1e-9
        assert g["sign"] == ref["sign"]
        assert g["house"] == ref["house"]
        assert g["name"] == ref["name"]
        # golden serializes the legacy tuple as a JSON list; port keeps a tuple
        assert list(g["pair"]) == ref["pair"]


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_calc_agep_exact_order(c):
    """The full 72-year timetable, in the EXACT order the legacy produced it.

    Order matters (Py2 sort stability on equal scusp), so we compare element by
    element -- including event label, class, and date (within a day, since the
    legacy rounds dates to whole days via timedelta(days)).
    """
    got = calc_agep(c["houses"], _birth_dt(c), c["plan"])
    ref = c["age_prog"]
    assert len(got) == len(ref), (
        "%s: %d events vs %d expected" % (c["name"], len(got), len(ref)))
    for i, (g, r) in enumerate(zip(got, ref)):
        assert g["lab"] == r["lab"], (
            "%s event %d: lab %r vs %r" % (c["name"], i, g["lab"], r["lab"]))
        assert g["cl"] == r["cl"], (
            "%s event %d: cl %r vs %r" % (c["name"], i, g["cl"], r["cl"]))
        # date: compare as YYYY-MM-DD strings (legacy formats zero-padded)
        g_iso = "%s-%s-%s" % (g["year"], g["mon"], g["day"])
        r_iso = "%s-%s-%s" % (r["year"], r["mon"], r["day"])
        assert g_iso == r_iso, (
            "%s event %d (%s): date %s vs %s"
            % (c["name"], i, g["lab"], g_iso, r_iso))


def test_calc_agep_has_twelve_house_entries():
    c = GOLDEN[0]
    got = calc_agep(c["houses"], _birth_dt(c), c["plan"])
    cc = [e for e in got if e["cl"] == "txt_cp"]
    assert len(cc) == 12
