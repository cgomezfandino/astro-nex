from astronex.core.utils import degtodec, dectodeg, format_longitud, format_latitud

def test_dectodeg_roundtrip():
    assert dectodeg(0.0) == "00000"
    # 10 deg 30 min 00 sec -> "103000"
    assert dectodeg(10.5) == "103000"

def test_degtodec_inverse():
    assert abs(degtodec("103000") - 10.5) < 1e-9

def test_format_longitud_west():
    # legacy display form: degrees, hemisphere letter, minutes
    assert format_longitud(-3.7038) == "3W42"

def test_format_latitud_north():
    # legacy display form: degrees, hemisphere letter, minutes
    assert format_latitud(40.4168) == "40N25"
