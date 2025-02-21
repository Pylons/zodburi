from unittest import mock

import pytest

import zodburi


@pytest.mark.parametrize("source, expected", [
    ("42", 42),
    ("42kb", 42 * 1024),
    ("42KB", 42 * 1024),
    ("42mb", 42 * 1024 * 1024),
    ("42MB", 42 * 1024 * 1024),
    ("42gb", 42 * 1024 * 1024 * 1024),
    ("42GB", 42 * 1024 * 1024 * 1024),
])
def test__parse_bytes(source, expected):
    assert zodburi._parse_bytes(source) == expected


def _expected_dbkw(**kw):
    dbkw = zodburi._DEFAULT_DBKW.copy()
    dbkw.update(kw)
    return dbkw


@pytest.mark.parametrize("kw, expected", [
    ({}, _expected_dbkw()),
    ({"database_name": "foo"}, _expected_dbkw(database_name="foo")),
    ({"connection_pool_size": "123"}, _expected_dbkw(pool_size=123)),
    ({"connection_pool_timeout": "45"}, _expected_dbkw(pool_timeout=45)),
    ({"connection_cache_size": "678"}, _expected_dbkw(cache_size=678)),
    (
        {"connection_cache_size_bytes": "678Kb"},
        _expected_dbkw(cache_size_bytes=678 * 1024)
    ),
    (
        {"connection_historical_pool_size": "123"},
        _expected_dbkw(historical_pool_size=123)
    ),
    (
        {"connection_historical_cache_size": "678"},
        _expected_dbkw(historical_cache_size=678)
    ),
    (
        {"connection_historical_cache_size_bytes": "678Mb"},
        _expected_dbkw(historical_cache_size_bytes=678 * 1024 * 1024)
    ),
    (
        {"connection_historical_timeout": "45"},
        _expected_dbkw(historical_timeout=45)
    ),
    (
        {"connection_large_record_size": "1234Kb"},
        _expected_dbkw(large_record_size=1234 * 1024)
    ),
])
def test__get_dbkw(kw, expected):
    assert zodburi._get_dbkw(kw) == expected


def test__get_dbkw_w_invalid():
    with pytest.raises(zodburi.UnknownDatabaseKeywords):
        zodburi._get_dbkw({"bogus": "value"})


def test_resolve_uri_w_bogus_scheme():
    bogus = "bogus:never/gonna/happen?really=1"

    with pytest.raises(zodburi.NoResolverForScheme):
        zodburi.resolve_uri(bogus)


def test_resolve_uri_w_valid_scheme():
    valid = "memory://storagename"
    expected_factory = object()
    expected_kw = {"database_name": "foo"}

    with mock.patch("zodburi._get_uri_factory_and_dbkw") as gufad:
        gufad.return_value = (expected_factory, expected_kw)
        factory, dbkw = zodburi.resolve_uri(valid)

    assert factory is expected_factory
    assert dbkw == _expected_dbkw(database_name="foo")
