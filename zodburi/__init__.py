from importlib.metadata import entry_points
import re

CONNECTION_PARAMETERS = (
    "pool_size",
    "pool_timeout",
    "cache_size",
    "cache_size_bytes",
    "historical_pool_size",
    "historical_cache_size",
    "historical_cache_size_bytes",
    "historical_timeout",
    "large_record_size",
)

BYTES_PARAMETERS = (
    "cache_size_bytes",
    "historical_cache_size_bytes",
    "large_record_size"
)

PARAMETERS = dict(
    [("database_name", "database_name")] +
    [(f"connection_{parm}", parm) for parm in CONNECTION_PARAMETERS]
)

HAS_UNITS_RE = re.compile(r"\s*(\d+)\s*([kmg])b\s*$")
UNITS = dict(k=1<<10, m=1<<20, g=1<<30)


_DEFAULT_DBKW = {
    "cache_size": 10000,
    "pool_size": 7,
    "database_name": "unnamed",
}


class NoResolverForScheme(KeyError):
    def __init__(self, uri):
        self.uri = uri
        super().__init__(f"No resolver found for uri: {uri}")


class UnknownDatabaseKeywords(KeyError):
    def __init__(self, kw):
        self.kw = kw
        super().__init__(
            f"Unrecognized database keyword(s): {', '.join(kw)}"
        )


def resolve_uri(uri):
    """
    Returns a tuple, (factory, dbkw) where factory is a no-arg callable which
    returns a storage matching the spec defined in the uri.  dbkw is a dict of
    keyword arguments that may be passed to ZODB.DB.DB.
    """
    factory, dbkw = _get_uri_factory_and_dbkw(uri)
    return factory, _get_dbkw(dbkw)


def _get_uri_factory_and_dbkw(uri):
    """Return factory and original raw dbkw for a URI."""
    scheme = uri[:uri.find(":")]
    try:
        resolver_eps = entry_points(group="zodburi.resolvers")
    except TypeError:  # pragma: NO COVER Python < 3.10
        resolver_eps = entry_points()["zodburi.resolvers"]

    for ep in resolver_eps:
        if ep.name == scheme:
            resolver = ep.load()
            factory, dbkw = resolver(uri)
            return factory, dbkw
    else:
        raise NoResolverForScheme(uri)


_resolve_uri = _get_uri_factory_and_dbkw  # pragma: noqa  BBB alias


def _parse_bytes(s):
    m = HAS_UNITS_RE.match(s.lower())

    if m:
        v, uname = m.group(1, 2)
        return int(v) * UNITS[uname]
    else:
        return int(s)


def _get_dbkw(kw):
    dbkw = _DEFAULT_DBKW.copy()

    for parameter in PARAMETERS:
        if parameter in kw:
            v = kw.pop(parameter)
            if parameter.startswith("connection_"):
                if not isinstance(v, int):
                    if PARAMETERS[parameter] in BYTES_PARAMETERS:
                        v = _parse_bytes(v)
                    else:
                        v = int(v)
            dbkw[PARAMETERS[parameter]] = v

    if kw:
        raise UnknownDatabaseKeywords(kw)

    return dbkw
