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


def _get_dbkw(kw):
    dbkw = {
        'cache_size': 10000,
        'pool_size': 7,
        'database_name': 'unnamed',
    }
    if 'connection_cache_size' in kw:
        dbkw['cache_size'] = int(kw.pop('connection_cache_size'))
    if 'connection_pool_size' in kw:
        dbkw['pool_size'] = int(kw.pop('connection_pool_size'))
    if 'database_name' in kw:
        dbkw['database_name'] = kw.pop('database_name')

    if kw:
        raise KeyError('Unrecognized database keyword(s): %s' % ', '.join(kw))

    return dbkw
