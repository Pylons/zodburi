import os
import cgi
from cStringIO import StringIO
import urlparse

from ZODB.config import ZODBDatabase
from ZEO.ClientStorage import ClientStorage
from ZODB.FileStorage.FileStorage import FileStorage
from ZODB.DemoStorage import DemoStorage
from ZODB.MappingStorage import MappingStorage
from ZODB.blob import BlobStorage
import ZConfig
from relstorage.adapters.postgresql import PostgreSQLAdapter
from relstorage.options import Options
from relstorage.storage import RelStorage

from zodburi.datatypes import convert_bytesize
from zodburi.datatypes import convert_int


class Resolver(object):
    _int_args = ()
    _string_args = ()
    _bytesize_args = ()
    _float_args = ()
    _tuple_args = ()

    def interpret_kwargs(self, kw):
        unused = kw.copy()
        new = {}
        convert_string = lambda s: s
        converters = (
            convert_int,
            convert_string,
            convert_bytesize)
        args = (
            self._int_args,
            self._string_args,
            self._bytesize_args)
        for convert, arg_names in zip(converters, args):
            for arg_name in arg_names:
                value = unused.pop(arg_name, None)
                if value is not None:
                    value = convert(value)
                    new[arg_name] = value

        return new, unused


class MappingStorageURIResolver(Resolver):

    def __call__(self, uri):
        prefix, rest = uri.split('memory://', 1)
        result = rest.split('?', 1)
        if len(result) == 1:
            name = result[0]
            query = ''
        else:
            name, query = result
        kw = dict(cgi.parse_qsl(query))
        kw, unused = self.interpret_kwargs(kw)
        args = (name,)
        def factory():
            return MappingStorage(*args)
        return factory, unused


class FileStorageURIResolver(Resolver):
    # XXX missing: blob_dir, packer, pack_keep_old, pack_gc, stop
    _int_args = ('create', 'read_only', 'demostorage')
    _string_args = ('blobstorage_dir', 'blobstorage_layout')
    _bytesize_args = ('quota',)

    def __call__(self, uri):
        # we can't use urlparse.urlsplit here due to Windows filenames
        prefix, rest = uri.split('file://', 1)
        result = rest.split('?', 1)
        if len(result) == 1:
            path = result[0]
            query = ''
        else:
            path, query = result
        path = os.path.normpath(path)
        args = (path,)
        kw = dict(cgi.parse_qsl(query))
        kw, unused = self.interpret_kwargs(kw)
        demostorage = False

        if 'demostorage'in kw:
            kw.pop('demostorage')
            demostorage = True

        blobstorage_dir = None
        blobstorage_layout = 'automatic'
        if 'blobstorage_dir' in kw:
            blobstorage_dir = kw.pop('blobstorage_dir')
        if 'blobstorage_layout' in kw:
            blobstorage_layout = kw.pop('blobstorage_layout')

        if demostorage and blobstorage_dir:
            def factory():
                filestorage = FileStorage(*args, **kw)
                blobstorage = BlobStorage(blobstorage_dir, filestorage,
                                          layout=blobstorage_layout)
                return DemoStorage(base=blobstorage)
        elif blobstorage_dir:
            def factory():
                filestorage = FileStorage(*args, **kw)
                return BlobStorage(blobstorage_dir, filestorage,
                                          layout=blobstorage_layout)
        elif demostorage:
            def factory():
                filestorage = FileStorage(*args, **kw)
                return DemoStorage(base=filestorage)
        else:
            def factory():
                return FileStorage(*args, **kw)

        return factory, unused


class ClientStorageURIResolver(Resolver):
    _int_args = ('debug', 'min_disconnect_poll', 'max_disconnect_poll',
                 'wait_for_server_on_startup', 'wait', 'wait_timeout',
                 'read_only', 'read_only_fallback', 'shared_blob_dir',
                 'demostorage')
    _string_args = ('storage', 'name', 'client', 'var', 'username',
                    'password', 'realm', 'blob_dir')
    _bytesize_args = ('cache_size', )

    def __call__(self, uri):
        # urlparse doesnt understand zeo URLs so force to something that
        # doesn't break
        uri = uri.replace('zeo://', 'http://', 1)
        (scheme, netloc, path, query, frag) = urlparse.urlsplit(uri)
        if netloc:
            # TCP URL
            if ':' in netloc:
                host, port = netloc.split(':')
                port = int(port)
            else:
                host = netloc
                port = 9991
            args = ((host, port),)
        else:
            # Unix domain socket URL
            path = os.path.normpath(path)
            args = (path,)
        kw = dict(cgi.parse_qsl(query))
        kw, unused = self.interpret_kwargs(kw)
        if 'demostorage' in kw:
            kw.pop('demostorage')
            def factory():
                return DemoStorage(base=ClientStorage(*args, **kw))
        else:
            def factory():
                return ClientStorage(*args, **kw)
        return factory, unused


class ZConfigURIResolver(object):

    schema_xml_template = """
    <schema>
        <import package="ZODB"/>
        <multisection type="ZODB.storage" attribute="storages" />
        <multisection type="ZODB.database" attribute="databases" />
    </schema>
    """

    def __call__(self, uri):
        (scheme, netloc, path, query, frag) = urlparse.urlsplit(uri)
         # urlparse doesnt understand file URLs and stuffs everything into path
        (scheme, netloc, path, query, frag) = urlparse.urlsplit('http:' + path)
        path = os.path.normpath(path)
        schema_xml = self.schema_xml_template
        schema = ZConfig.loadSchemaFile(StringIO(schema_xml))
        config, handler = ZConfig.loadConfig(schema, path)
        for config_item in config.databases + config.storages:
            if not frag:
                # use the first defined in the file
                break
            elif frag == config_item.name:
                # match found
                break
        else:
            raise KeyError("No storage or database named %s found" % frag)

        if isinstance(config_item, ZODBDatabase):
            config = config_item.config
            factory = config.storage
            dbkw = {
                'connection_cache_size': config.cache_size,
                'connection_pool_size': config.pool_size,
            }
            if config.database_name:
                dbkw['database_name'] = config.database_name
        else:
            factory = config_item
            dbkw = dict(cgi.parse_qsl(query))

        return factory.open, dbkw


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


client_storage_resolver = ClientStorageURIResolver()
file_storage_resolver = FileStorageURIResolver()
zconfig_resolver = ZConfigURIResolver()
mapping_storage_resolver = MappingStorageURIResolver()
postgresql_resolver = RelStorageURIResolver(PostgreSQLAdapterHelper())