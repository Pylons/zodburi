from io import BytesIO
import os

from ZConfig import loadConfig
from ZConfig import loadSchemaFile
from ZEO.ClientStorage import ClientStorage
from ZODB.blob import BlobStorage
from ZODB.config import ZODBDatabase
from ZODB.DemoStorage import DemoStorage
from ZODB.FileStorage.FileStorage import FileStorage
from ZODB.MappingStorage import MappingStorage

from zodburi.datatypes import convert_bytesize
from zodburi.datatypes import convert_int
from zodburi.datatypes import convert_tuple
from zodburi._compat import parse_qsl
from zodburi._compat import urlsplit

# Capability test for older Pythons (2.x < 2.7.4, 3.x < 3.2.4)
(scheme, netloc, path, query, frag) = urlsplit('scheme:///path/#frag')
_BROKEN_URLSPLIT = frag != 'frag'

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
        converters = [
            (convert_int, self._int_args),
            (convert_string, self._string_args),
            (convert_bytesize, self._bytesize_args),
            (float, self._float_args),
            (convert_tuple, self._tuple_args),
        ]
        for convert, arg_names in converters:
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
        kw = dict(parse_qsl(query))
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
        # we can't use urlsplit here due to Windows filenames
        prefix, rest = uri.split('file://', 1)
        result = rest.split('?', 1)
        if len(result) == 1:
            path = result[0]
            query = ''
        else:
            path, query = result
        path = os.path.normpath(path)
        args = (path,)
        kw = dict(parse_qsl(query))
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
        # urlsplit doesnt understand zeo URLs so force to something that
        # doesn't break
        uri = uri.replace('zeo://', 'http://', 1)
        (scheme, netloc, path, query, frag) = urlsplit(uri)
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
        kw = dict(parse_qsl(query))
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

    schema_xml_template = b"""
    <schema>
        <import package="ZODB"/>
        <multisection type="ZODB.storage" attribute="storages" />
        <multisection type="ZODB.database" attribute="databases" />
    </schema>
    """

    def __call__(self, uri):
        (scheme, netloc, path, query, frag) = urlsplit(uri)
        if _BROKEN_URLSPLIT: #pragma NO COVER
            # urlsplit used not to allow fragments in non-standard schemes,
            # stuffed everything into 'path'
            (scheme, netloc, path, query, frag
            ) = urlsplit('http:' + path)
        path = os.path.normpath(path)
        schema_xml = self.schema_xml_template
        schema = loadSchemaFile(BytesIO(schema_xml))
        config, handler = loadConfig(schema, path)
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
            dbkw = dict(parse_qsl(query))

        return factory.open, dbkw


client_storage_resolver = ClientStorageURIResolver()
file_storage_resolver = FileStorageURIResolver()
zconfig_resolver = ZConfigURIResolver()
mapping_storage_resolver = MappingStorageURIResolver()
