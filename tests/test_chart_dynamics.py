import json
from pathlib import Path
import pytest

from astronex.core.chart import Chart

GOLDEN = json.loads(
    (Path(__file__).parent / "golden" / "dynamics.json").read_text()
)


def _chart(c):
    ch = Chart()
    ch.planets = list(c["planets"])
    ch.houses = list(c["houses"])
    # calc_cross_points(cross=True) -> cp_time_lapsus needs self.date (ISO).
    # The golden captured with the placeholder date below.
    ch.date = "2000-01-01T00:00:00+0000UTC"
    return ch


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_signdyn(c):
    assert _chart(c).signdyn() == c["signdyn"]


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_housedyn(c):
    assert _chart(c).housedyn() == c["housedyn"]


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_dyncalc_list(c):
    assert list(_chart(c).dyncalc_list()) == c["dyncalc_list"]


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_dynstar_signs(c):
    assert _chart(c).dynstar_signs() == c["dynstar_signs"]


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_dynstar_houses(c):
    assert _chart(c).dynstar_houses() == c["dynstar_houses"]


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_dyn_span_diff(c):
    assert _chart(c).dyn_span_diff() == c["dyn_span_diff"]


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_cuad_plan(c):
    got = _chart(c).cuad_plan()
    ref = c["cuad_plan"]
    assert len(got) == 4
    for g_group, ref_group in zip(got, ref):
        assert len(g_group) == len(ref_group)
        for g, r in zip(g_group, ref_group):
            assert g["degree"] == r["degree"]
            assert g["ix"] == r["ix"]
            assert g["conflict"] == r["conflict"]


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_which_all_houses(c):
    # port returns tuples (d,i,l); golden serializes them as JSON lists.
    got = _chart(c).which_all_houses()
    for g_tup, ref_list in zip(got, c["which_all_houses"]):
        assert list(g_tup) == ref_list


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_which_all_signs(c):
    assert _chart(c).which_all_signs() == c["which_all_signs"]


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_rays_calc(c):
    assert _chart(c).rays_calc() == c["rays_calc"]


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_cross_point(c):
    assert abs(_chart(c).calc_cross_points() - c["cross_point"]) < 1e-9


@pytest.mark.parametrize("c", GOLDEN, ids=lambda c: c["name"])
def test_cross_point_full(c):
    got = _chart(c).calc_cross_points(cross=True)
    ref = c["cross_point_full"]
    assert got["cp1"] == ref["cp1"]
    assert got["cp2"] == ref["cp2"]
    assert got["dat1"] == ref["dat1"]
    assert got["dat2"] == ref["dat2"]
