import unittest

import pytest

_marker = object()


def _suffix_multiplier(d=None, default=_marker):
    from zodburi.datatypes import SuffixMultiplier

    if d is None:
        d = {}

    if default is _marker:
        return SuffixMultiplier(d)

    return SuffixMultiplier(d, default)


def test_suffixmultiplier___init___w_defaults():
    sm = _suffix_multiplier()
    assert sm._d == {}
    assert sm._default == 1
    assert sm._keysz == 0


def test_suffixmultiplier___init___w_explicit_default():
    sm = _suffix_multiplier(default=3)
    assert sm._d == {}
    assert sm._default == 3
    assert sm._keysz == 0


def test_suffixmultiplier___init___w_normal_suffixes():
    SFX = {"aaa": 2, "bbb": 3}
    sm = _suffix_multiplier(SFX)
    assert sm._d == SFX
    assert sm._default == 1
    assert sm._keysz == 3


def test_suffixmultiplier___init___w_mismatched_suffixes():
    SFX = {"aaa": 2, "bbbb": 3}

    with pytest.raises(ValueError):
        _suffix_multiplier(SFX)


def test_suffixmultiplier___call____miss():
    SFX = {"aaa": 2, "bbb": 3}
    sm = _suffix_multiplier(SFX)
    assert sm("14") == 14


def test_suffixmultiplier___call___hit():
    SFX = {"aaa": 2, "bbb": 3}
    sm = _suffix_multiplier(SFX)
    assert sm("14bbb") == 42


def test_convert_bytesize_miss():
    from zodburi.datatypes import convert_bytesize

    assert convert_bytesize("14") == 14


@pytest.mark.parametrize("sized, expected", [
    ("14", 14),
    ("200", 200),
    ("14kb", 14 * 1024),
    ("14mb", 14 * 1024 * 1024),
    ("14gb", 14 * 1024 * 1024 * 1024),
])
def test_convert_bytesize_hit(sized, expected):
    from zodburi.datatypes import convert_bytesize

    assert convert_bytesize(sized) == expected


def test_convert_int_w_falsetypes():
    from zodburi.datatypes import convert_int
    from zodburi.datatypes import FALSETYPES

    for v in FALSETYPES:
        assert convert_int(v) == 0
        assert convert_int(v.title()) == 0


def test_convert_int_w_truetypes():
    from zodburi.datatypes import convert_int
    from zodburi.datatypes import TRUETYPES

    for v in TRUETYPES:
        assert convert_int(v) == 1
        assert convert_int(v.title()) == 1


def test_convert_int_w_normal():
    from zodburi.datatypes import convert_int

    assert convert_int("14") == 14


def test_convert_int_w_invalid():
    from zodburi.datatypes import convert_int

    with pytest.raises(ValueError):
        convert_int("notanint")


def test_convert_tuple_w_empty():
    from zodburi.datatypes import convert_tuple

    assert convert_tuple("") == ("",)


def test_convert_tuple_wo_commas():
    from zodburi.datatypes import convert_tuple

    assert convert_tuple("abc") == ("abc",)


def test_convert_tuple_w_commas():
    from zodburi.datatypes import convert_tuple

    assert convert_tuple("abc,def") == ("abc", "def")
