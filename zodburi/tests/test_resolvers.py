import mock
import unittest

class Base:

    def test_interpret_kwargs_noargs(self):
        resolver = self._makeOne()
        kwargs = resolver.interpret_kwargs({})
        self.assertEqual(kwargs, ({}, {}))

    def test_bytesize_args(self):
        resolver = self._makeOne()
        names = sorted(resolver._bytesize_args)
        kwargs = {}
        for name in names:
            kwargs[name] = '10MB'
        args = resolver.interpret_kwargs(kwargs)[0]
        keys = args.keys()
        self.assertEqual(sorted(keys), names)
        for name, value in args.items():
            self.assertEqual(value, 10*1024*1024)

    def test_int_args(self):
        resolver = self._makeOne()
        names = sorted(resolver._int_args)
        kwargs = {}
        for name in names:
            kwargs[name] = '10'
        args = resolver.interpret_kwargs(kwargs)[0]
        keys = sorted(args.keys())
        self.assertEqual(sorted(keys), sorted(names))
        for name, value in args.items():
            self.assertEqual(value, 10)

    def test_string_args(self):
        resolver = self._makeOne()
        names = sorted(resolver._string_args)
        kwargs = {}
        for name in names:
            kwargs[name] = 'string'
        args = resolver.interpret_kwargs(kwargs)[0]
        keys = args.keys()
        self.assertEqual(sorted(keys), names)
        for name, value in args.items():
            self.assertEqual(value, 'string')

    def test_float_args(self):
        resolver = self._makeOne()
        resolver._float_args = ('pi', 'PI')
        names = sorted(resolver._float_args)
        kwargs = {}
        for name in names:
            kwargs[name] = '3.14'
        args = resolver.interpret_kwargs(kwargs)[0]
        keys = args.keys()
        self.assertEqual(sorted(keys), names)
        for name, value in args.items():
            self.assertEqual(value, 3.14)

    def test_tuple_args(self):
        resolver = self._makeOne()
        resolver._tuple_args = ('foo', 'bar')
        names = sorted(resolver._tuple_args)
        kwargs = {}
        for name in names:
            kwargs[name] = 'first,second,third'
        args = resolver.interpret_kwargs(kwargs)[0]
        keys = args.keys()
        self.assertEqual(sorted(keys), names)
        for name, value in args.items():
            self.assertEqual(value, ('first', 'second', 'third'))

class TestFileStorageURIResolver(Base, unittest.TestCase):

    def _getTargetClass(self):
        from zodburi.resolvers import FileStorageURIResolver
        return FileStorageURIResolver

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass()

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_bool_args(self):
        resolver = self._makeOne()
        f = resolver.interpret_kwargs
        kwargs = f({'read_only':'1'})
        self.assertEqual(kwargs[0], {'read_only':1})
        kwargs = f({'read_only':'true'})
        self.assertEqual(kwargs[0], {'read_only':1})
        kwargs = f({'read_only':'on'})
        self.assertEqual(kwargs[0], {'read_only':1})
        kwargs = f({'read_only':'off'})
        self.assertEqual(kwargs[0], {'read_only':0})
        kwargs = f({'read_only':'no'})
        self.assertEqual(kwargs[0], {'read_only':0})
        kwargs = f({'read_only':'false'})
        self.assertEqual(kwargs[0], {'read_only':0})

    @mock.patch('zodburi.resolvers.FileStorage')
    def test_call_no_qs(self, FileStorage):
        resolver = self._makeOne()
        factory, dbkw = resolver('file:///tmp/foo/bar')
        factory()
        FileStorage.assert_called_once_with('/tmp/foo/bar')

    @mock.patch('zodburi.resolvers.FileStorage')
    def test_call_abspath(self, FileStorage):
        resolver = self._makeOne()
        factory, dbkw = resolver('file:///tmp/foo/bar?read_only=true')
        factory()
        FileStorage.assert_called_once_with('/tmp/foo/bar', read_only=1)

    @mock.patch('zodburi.resolvers.FileStorage')
    def test_call_abspath_windows(self, FileStorage):
        resolver = self._makeOne()
        factory, dbkw = resolver(
            'file://C:\\foo\\bar?read_only=true')
        factory()
        FileStorage.assert_called_once_with('C:\\foo\\bar', read_only=1)

    @mock.patch('zodburi.resolvers.FileStorage')
    def test_call_normpath(self, FileStorage):
        resolver = self._makeOne()
        factory, dbkw = resolver('file:///tmp/../foo/bar?read_only=true')
        factory()
        FileStorage.assert_called_once_with('/foo/bar', read_only=1)

    def test_invoke_factory_filestorage(self):
        import os
        from ZODB.FileStorage import FileStorage
        self.assertFalse(os.path.exists(os.path.join(self.tmpdir, 'db.db')))
        resolver = self._makeOne()
        factory, dbkw = resolver('file://%s/db.db?quota=200' % self.tmpdir)
        storage = factory()
        self.assertTrue(isinstance(storage, FileStorage))
        try:
            self.assertEqual(storage._quota, 200)
            self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'db.db')))
        finally:
            storage.close()

    def test_invoke_factory_demostorage(self):
        import os
        from ZODB.DemoStorage import DemoStorage
        from ZODB.FileStorage import FileStorage
        resolver = self._makeOne()
        factory, dbkw = resolver(
            'file://%s/db.db?demostorage=true' % self.tmpdir)
        storage = factory()
        self.assertTrue(isinstance(storage, DemoStorage))
        self.assertTrue(isinstance(storage.base, FileStorage))
        try:
            self.assertEqual(dbkw, {})
            self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'db.db')))
        finally:
            storage.close()

    def test_invoke_factory_blobstorage(self):
        import os
        from ZODB.blob import BlobStorage
        from .._compat import quote as q
        DB_FILE = os.path.join(self.tmpdir, 'db.db')
        BLOB_DIR = os.path.join(self.tmpdir, 'blob')
        self.assertFalse(os.path.exists(DB_FILE))
        resolver = self._makeOne()
        factory, dbkw = resolver(
            'file://%s/db.db?quota=200'
            '&blobstorage_dir=%s/blob'
            '&blobstorage_layout=bushy' % (self.tmpdir, q(self.tmpdir)))
        storage = factory()
        self.assertTrue(isinstance(storage, BlobStorage))
        try:
            self.assertTrue(os.path.exists(DB_FILE))
            self.assertTrue(os.path.exists(BLOB_DIR))
        finally:
            storage.close()

    def test_invoke_factory_blobstorage_and_demostorage(self):
        import os
        from ZODB.DemoStorage import DemoStorage
        from .._compat import quote as q
        DB_FILE = os.path.join(self.tmpdir, 'db.db')
        BLOB_DIR = os.path.join(self.tmpdir, 'blob')
        self.assertFalse(os.path.exists(DB_FILE))
        resolver = self._makeOne()
        factory, dbkw = resolver(
            'file://%s/db.db?quota=200&demostorage=true'
            '&blobstorage_dir=%s/blob'
            '&blobstorage_layout=bushy' % (self.tmpdir, q(self.tmpdir)))
        storage = factory()
        self.assertTrue(isinstance(storage, DemoStorage))
        try:
            self.assertTrue(os.path.exists(DB_FILE))
            self.assertTrue(os.path.exists(BLOB_DIR))
        finally:
            storage.close()

    def test_dbargs(self):
        resolver = self._makeOne()
        factory, dbkw = resolver(
            ('file:///tmp/../foo/bar?connection_pool_size=1'
             '&connection_cache_size=1&database_name=dbname'))
        self.assertEqual(dbkw, {'connection_cache_size': '1',
                                'connection_pool_size': '1',
                                'database_name': 'dbname'})


class TestClientStorageURIResolver(unittest.TestCase):
    def _getTargetClass(self):
        from zodburi.resolvers import ClientStorageURIResolver
        return ClientStorageURIResolver

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass()

    def test_bool_args(self):
        resolver = self._makeOne()
        f = resolver.interpret_kwargs
        kwargs = f({'read_only':'1'})
        self.assertEqual(kwargs[0], {'read_only':1})
        kwargs = f({'read_only':'true'})
        self.assertEqual(kwargs[0], {'read_only':1})
        kwargs = f({'read_only':'on'})
        self.assertEqual(kwargs[0], {'read_only':1})
        kwargs = f({'read_only':'off'})
        self.assertEqual(kwargs[0], {'read_only':0})
        kwargs = f({'read_only':'no'})
        self.assertEqual(kwargs[0], {'read_only':0})
        kwargs = f({'read_only':'false'})
        self.assertEqual(kwargs[0], {'read_only':0})

    @mock.patch('zodburi.resolvers.ClientStorage')
    def test_call_tcp_no_port(self, ClientStorage):
        resolver = self._makeOne()
        factory, dbkw = resolver('zeo://localhost?debug=true')
        factory()
        ClientStorage.assert_called_once_with(('localhost', 9991), debug=1)

    @mock.patch('zodburi.resolvers.ClientStorage')
    def test_call_tcp(self, ClientStorage):
        resolver = self._makeOne()
        factory, dbkw = resolver('zeo://localhost:8080?debug=true')
        factory()
        ClientStorage.assert_called_once_with(('localhost', 8080), debug=1)

    @mock.patch('zodburi.resolvers.ClientStorage')
    def test_call_unix(self, ClientStorage):
        resolver = self._makeOne()
        factory, dbkw = resolver('zeo:///var/sock?debug=true')
        factory()
        ClientStorage.assert_called_once_with('/var/sock', debug=1)

    @mock.patch('zodburi.resolvers.ClientStorage')
    def test_invoke_factory(self, ClientStorage):
        resolver = self._makeOne()
        factory, dbkw = resolver('zeo:///var/nosuchfile?wait=false')
        storage = factory()
        storage.close()
        ClientStorage.assert_called_once_with('/var/nosuchfile', wait=0)

    @mock.patch('zodburi.resolvers.ClientStorage')
    def test_invoke_factory_demostorage(self, ClientStorage):
        from ZODB.DemoStorage import DemoStorage
        resolver = self._makeOne()
        factory, dbkw = resolver('zeo:///var/nosuchfile?wait=false'
                                        '&demostorage=true')
        storage = factory()
        storage.close()
        self.assertTrue(isinstance(storage, DemoStorage))

    def test_dbargs(self):
        resolver = self._makeOne()
        factory, dbkw = resolver('zeo://localhost:8080?debug=true&'
                                        'connection_pool_size=1&'
                                        'connection_cache_size=1&'
                                        'database_name=dbname')
        self.assertEqual(dbkw, {'connection_pool_size': '1',
                                'connection_cache_size': '1',
                                'database_name': 'dbname'})


class TestZConfigURIResolver(unittest.TestCase):
    def _getTargetClass(self):
        from zodburi.resolvers import ZConfigURIResolver
        return ZConfigURIResolver

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass()

    def setUp(self):
        import tempfile
        self.tmp = tempfile.NamedTemporaryFile()

    def tearDown(self):
        self.tmp.close()

    def test_named_storage(self):
        self.tmp.write(b"""
        <demostorage foo>
        </demostorage>

        <mappingstorage bar>
        </mappingstorage>
        """)
        self.tmp.flush()
        resolver = self._makeOne()
        factory, dbkw = resolver('zconfig://%s#bar' % self.tmp.name)
        storage = factory()
        from ZODB.MappingStorage import MappingStorage
        self.assertTrue(isinstance(storage, MappingStorage), storage)

    def test_anonymous_storage(self):
        self.tmp.write(b"""
        <mappingstorage>
        </mappingstorage>

        <demostorage demo>
        </demostorage>
        """)
        self.tmp.flush()
        resolver = self._makeOne()
        factory, dbkw = resolver('zconfig://%s' % self.tmp.name)
        storage = factory()
        from ZODB.MappingStorage import MappingStorage
        self.assertTrue(isinstance(storage, MappingStorage))
        self.assertEqual(dbkw, {})

    def test_query_string_args(self):
        self.tmp.write(b"""
        <mappingstorage>
        </mappingstorage>

        <demostorage demo>
        </demostorage>
        """)
        self.tmp.flush()
        resolver = self._makeOne()
        factory, dbkw = resolver('zconfig://%s?foo=bar' % self.tmp.name)
        self.assertEqual(dbkw, {'foo': 'bar'})

    def test_storage_not_found(self):
        self.tmp.write(b"""
        <mappingstorage x>
        </mappingstorage>
        """)
        self.tmp.flush()
        resolver = self._makeOne()
        self.assertRaises(KeyError, resolver, 'zconfig://%s#y' % self.tmp.name)

    def test_anonymous_database(self):
        self.tmp.write(b"""
        <zodb>
          <mappingstorage>
          </mappingstorage>
        </zodb>
        """)
        self.tmp.flush()
        resolver = self._makeOne()
        factory, dbkw = resolver('zconfig://%s' % self.tmp.name)
        storage = factory()
        from ZODB.MappingStorage import MappingStorage
        self.assertTrue(isinstance(storage, MappingStorage))
        self.assertEqual(dbkw, {
            'connection_cache_size': 5000,
            'connection_pool_size': 7})

    def test_named_database(self):
        self.tmp.write(b"""
        <zodb x>
          <mappingstorage>
          </mappingstorage>
          database-name foo
          cache-size 20000
          pool-size 5
        </zodb>
        """)
        self.tmp.flush()
        resolver = self._makeOne()
        factory, dbkw = resolver('zconfig://%s#x' % self.tmp.name)
        storage = factory()
        from ZODB.MappingStorage import MappingStorage
        self.assertTrue(isinstance(storage, MappingStorage))
        self.assertEqual(dbkw, {
            'connection_cache_size': 20000,
            'connection_pool_size': 5,
            'database_name': 'foo'})

class TestMappingStorageURIResolver(Base, unittest.TestCase):

    def _getTargetClass(self):
        from zodburi.resolvers import MappingStorageURIResolver
        return MappingStorageURIResolver

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass()

    def test_call_no_qs(self):
        resolver = self._makeOne()
        factory, dbkw = resolver('memory://')
        self.assertEqual(dbkw, {})
        storage = factory()
        from ZODB.MappingStorage import MappingStorage
        self.assertTrue(isinstance(storage, MappingStorage))
        self.assertEqual(storage.__name__, '')

    def test_call_with_qs(self):
        uri='memory://storagename?connection_cache_size=100&database_name=fleeb'
        resolver = self._makeOne()
        factory, dbkw = resolver(uri)
        self.assertEqual(dbkw, {'connection_cache_size': '100',
                                'database_name': 'fleeb'})
        storage = factory()
        from ZODB.MappingStorage import MappingStorage
        self.assertTrue(isinstance(storage, MappingStorage))
        self.assertEqual(storage.__name__, 'storagename')


class TestEntryPoints(unittest.TestCase):

    def test_it(self):
        from pkg_resources import load_entry_point
        from zodburi import resolvers
        expected = [
            ('memory', resolvers.MappingStorageURIResolver),
            ('zeo', resolvers.ClientStorageURIResolver),
            ('file', resolvers.FileStorageURIResolver),
            ('zconfig', resolvers.ZConfigURIResolver),
        ]
        for name, cls in expected:
            target = load_entry_point('zodburi', 'zodburi.resolvers', name)
            self.assertTrue(isinstance(target, cls))
