import cgi
import urlparse
from ZODB.DemoStorage import DemoStorage
from relstorage.adapters.postgresql import PostgreSQLAdapter
from relstorage.options import Options
from relstorage.storage import RelStorage

from .resolvers import Resolver


# Not a real resolver, but we use interpret_kwargs
class PostgreSQLAdapterHelper(Resolver):
    _int_args = ('connect_timeout', )
    _string_args = ('ssl_mode', )

    def __call__(self, parsed_uri, kw):
        dsn_args = [
            ('dbname', parsed_uri.path[1:]),
            ('user', parsed_uri.username),
            ('password', parsed_uri.password),
            ('host', parsed_uri.hostname),
            ('port', parsed_uri.port)
        ]

        kw, unused = self.interpret_kwargs(kw)
        dsn_args.extend(kw.items())

        dsn = ' '.join("%s='%s'"%arg for arg in dsn_args)

        def factory(options):
            return PostgreSQLAdapter(dsn=dsn, options=options)
        return factory, unused


# The relstorage support is inspired by django-zodb.
# Oracle and mysql should be easily implementable from here
class RelStorageURIResolver(Resolver):
    _int_args = ('poll_interval', 'cache_local_mb', 'commit_lock_timeout',
                 'commit_lock_id', 'read_only', 'shared_blob_dir',
                 'keep_history', 'pack_gc', 'pack_dry_run', 'strict_tpc',
                 'create', 'demostorage',)
    _string_args = ('name', 'blob_dir', 'replica_conf', 'cache_module_name',
                    'cache_prefix', 'cache_delta_size_limit')
    _bytesize_args = ('blob_cache_size', 'blob_cache_size_check',
                      'blob_cache_chunk_size')
    _float_args = ('replica_timeout', 'pack_batch_timeout', 'pack_duty_cycle',
                   'pack_max_delay')
    _tuple_args = ('cache_servers',)

    def __init__(self, adapter_helper):
        self.adapter_helper = adapter_helper

    def __call__(self, uri):
        uri = uri.replace('postgres://', 'http://', 1)
        parsed_uri = urlparse.urlsplit(uri)
        kw = dict(cgi.parse_qsl(parsed_uri.query))

        adapter_factory, kw = self.adapter_helper(parsed_uri, kw)
        kw, unused = self.interpret_kwargs(kw)

        demostorage = kw.pop('demostorage', False)
        options = Options(**kw)

        def factory():
            adapter = adapter_factory(options)
            storage = RelStorage(adapter=adapter, options=options)
            if demostorage:
                storage = DemoStorage(base=storage)
            return storage
        return factory, unused

postgresql_resolver = RelStorageURIResolver(PostgreSQLAdapterHelper())