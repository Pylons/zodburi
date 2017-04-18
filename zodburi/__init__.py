import re
from pkg_resources import iter_entry_points


def resolve_uri(uri):
    """
    Returns a tuple, (factory, dbkw) where factory is a no-arg callable which
    returns a storage matching the spec defined in the uri.  dbkw is a dict of
    keyword arguments that may be passed to ZODB.DB.DB.
    """
    scheme = uri[:uri.find(':')]
    for ep in iter_entry_points('zodburi.resolvers'):
        if ep.name == scheme:
            resolver = ep.load()
            factory, dbkw = resolver(uri)
            return factory, _get_dbkw(dbkw)
    else:
        raise KeyError('No resolver found for uri: %s' % uri)

connection_parameters = '''
  pool_size pool_timeout cache_size cache_size_bytes
  historical_pool_size historical_cache_size historical_cache_size_bytes
  historical_timeout large_record_size
  '''.strip().split()

bytes_parameters = (
    'cache_size_bytes', 'historical_cache_size_bytes', 'large_record_size')

parameters = dict(database_name = 'database_name')
for parameter in connection_parameters:
    parameters['connection_' + parameter] = parameter

has_units = re.compile('\s*(\d+)\s*([kmg])b\s*$').match
units = dict(k=1<<10, m=1<<20, g=1<<30)
def _parse_bytes(s):
    m = has_units(s.lower())
    if m:
        v, uname = m.group(1, 2)
        return int(v) * units[uname]
    else:
        return int(s)

def _get_dbkw(kw):
    dbkw = {
        'cache_size': 10000,
        'pool_size': 7,
        'database_name': 'unnamed',
    }
    for parameter in parameters:
        if parameter in kw:
            v = kw.pop(parameter)
            if parameter.startswith('connection_'):
                if not isinstance(v, int):
                    if parameters[parameter] in bytes_parameters:
                        v = _parse_bytes(v)
                    else:
                        v = int(v)
            dbkw[parameters[parameter]] = v

    if kw:
        raise KeyError('Unrecognized database keyword(s): %s' % ', '.join(kw))

    return dbkw
