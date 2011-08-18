import os
import cgi
from cStringIO import StringIO
import urlparse

from zodburi.datatypes import byte_size
from zodburi.datatypes import FALSETYPES
from zodburi.datatypes import TRUETYPES

from ZODB.FileStorage.FileStorage import FileStorage
from ZODB.DemoStorage import DemoStorage
from ZODB.MappingStorage import MappingStorage
from ZODB.blob import BlobStorage
from ZODB.DB import DB
import ZConfig

def interpret_int_args(argnames, kw):
    newkw = {}

    # boolean values are also treated as integers
    for name in argnames:
        value = kw.get(name)
        if value is not None:
            value = value.lower()
            if value in FALSETYPES:
                value = 0
            if value in TRUETYPES:
                value = 1
            value = int(value)
            newkw[name] = value

    return newkw

def interpret_string_args(argnames, kw):
    newkw = {}
    # strings
    for name in argnames:
        value = kw.get(name)
        if value is not None:
            newkw[name] = value
    return newkw

def interpret_bytesize_args(argnames, kw):
    newkw = {}

    # suffix multiplied
    for name in argnames:
        value = kw.get(name)
        if value is not None:
            newkw[name] = byte_size(value)

    return newkw

class Resolver(object):
    def interpret_kwargs(self, kw):
        new = {}
        newkw = interpret_int_args(self._int_args, kw)
        new.update(newkw)
        newkw = interpret_string_args(self._string_args, kw)
        new.update(newkw)
        newkw = interpret_bytesize_args(self._bytesize_args, kw)
        new.update(newkw)
        return new

class MappingStorageURIResolver(Resolver):
    _int_args = ('connection_cache_size', 'connection_pool_size')
    _string_args = ('database_name',)
    _bytesize_args = ()
    def __call__(self, uri):
        prefix, rest = uri.split('memory://', 1)
        result = rest.split('?', 1)
        if len(result) == 1:
            name = result[0]
            query = ''
        else:
            name, query = result
        kw = dict(cgi.parse_qsl(query))
        kw = self.interpret_kwargs(kw)
        dbkw = get_dbkw(kw)
        args = (name,)
        dbitems = dbkw.items()
        dbitems.sort()
        key = (args, tuple(dbitems))
        def factory():
            storage = MappingStorage(*args)
            return DB(storage, **dbkw)
        return key, args, kw, factory

class FileStorageURIResolver(Resolver):
    # XXX missing: blob_dir, packer, pack_keep_old, pack_gc, stop
    _int_args = ('create', 'read_only', 'demostorage', 'connection_cache_size',
                 'connection_pool_size')
    _string_args = ('blobstorage_dir', 'blobstorage_layout', 'database_name')
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
        kw = dict(cgi.parse_qsl(query))
        kw = self.interpret_kwargs(kw)
        dbkw = get_dbkw(kw)
        items = kw.items()
        items.sort()
        args = (path,)
        dbitems = dbkw.items()
        dbitems.sort()
        key = (args, tuple(items), tuple(dbitems))
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
                demostorage = DemoStorage(base=blobstorage)
                return DB(demostorage, **dbkw)
        elif blobstorage_dir:
            def factory():
                filestorage = FileStorage(*args, **kw)
                blobstorage = BlobStorage(blobstorage_dir, filestorage,
                                          layout=blobstorage_layout)
                return DB(blobstorage, **dbkw)
        elif demostorage:
            def factory():
                filestorage = FileStorage(*args, **kw)
                demostorage = DemoStorage(base=filestorage)
                return DB(demostorage, **dbkw)
        else:
            def factory():
                filestorage = FileStorage(*args, **kw)
                return DB(filestorage, **dbkw)

        return key, args, kw, factory

class ClientStorageURIResolver(Resolver):
    _int_args = ('debug', 'min_disconnect_poll', 'max_disconnect_poll',
                 'wait_for_server_on_startup', 'wait', 'wait_timeout',
                 'read_only', 'read_only_fallback', 'shared_blob_dir',
                 'demostorage', 'connection_cache_size',
                 'connection_pool_size')
    _string_args = ('storage', 'name', 'client', 'var', 'username',
                    'password', 'realm', 'blob_dir', 'database_name')
    _bytesize_args = ('cache_size', )

    def __call__(self, uri):
        # urlparse doesnt understand zeo URLs so force to something that doesn't break
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
        kw = self.interpret_kwargs(kw)
        dbkw = get_dbkw(kw)
        items = kw.items()
        items.sort()
        dbitems = dbkw.items()
        dbitems.sort()
        key = (args, tuple(items), tuple(dbitems))
        if 'demostorage' in kw:
            kw.pop('demostorage')
            def factory():
                from ZEO.ClientStorage import ClientStorage
                from ZODB.DB import DB
                from ZODB.DemoStorage import DemoStorage
                demostorage = DemoStorage(base=ClientStorage(*args, **kw))
                return DB(demostorage, **dbkw) #pragma NO COVERAGE
        else:
            def factory():
                from ZEO.ClientStorage import ClientStorage
                from ZODB.DB import DB
                clientstorage = ClientStorage(*args, **kw)
                return DB(clientstorage, **dbkw) #pragma NO COVERAGE
        return key, args, kw, factory

def get_dbkw(kw):
    dbkw = {}
    dbkw['cache_size'] = 10000
    dbkw['pool_size'] = 7
    dbkw['database_name'] = 'unnamed'
    if 'connection_cache_size' in kw:
        dbkw['cache_size'] = int(kw.pop('connection_cache_size'))
    if 'connection_pool_size' in kw:
        dbkw['pool_size'] = int(kw.pop('connection_pool_size'))
    if 'database_name' in kw:
        dbkw['database_name'] = kw.pop('database_name')

    return dbkw


class ZConfigURIResolver(object):

    schema_xml_template = """
    <schema>
        <import package="ZODB"/>
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
        for database in config.databases:
            if not frag:
                # use the first defined in the file
                break
            elif frag == database.name:
                # match found
                break
        else:
            raise KeyError("No database named %s found" % frag)
        return (path, frag), (), {}, database.open


RESOLVERS = {
    'zeo':ClientStorageURIResolver(),
    'file':FileStorageURIResolver(),
    'zconfig':ZConfigURIResolver(),
    'memory':MappingStorageURIResolver(),
    }