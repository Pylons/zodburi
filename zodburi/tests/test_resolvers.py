import unittest

class Base:

    def test_interpret_kwargs_noargs(self):
        resolver = self._makeOne()
        kwargs = resolver.interpret_kwargs({})
        self.assertEqual(kwargs, {})

    def test_bytesize_args(self):
        resolver = self._makeOne()
        names = list(resolver._bytesize_args)
        kwargs = {}
        for name in names:
            kwargs[name] = '10MB'
        args = resolver.interpret_kwargs(kwargs)
        keys = args.keys()
        keys.sort()
        self.assertEqual(keys, names)
        for name, value in args.items():
            self.assertEqual(value, 10*1024*1024)

    def test_int_args(self):
        resolver = self._makeOne()
        names = list(resolver._int_args)
        kwargs = {}
        for name in names:
            kwargs[name] = '10'
        args = resolver.interpret_kwargs(kwargs)
        keys = args.keys()
        keys.sort()
        self.assertEqual(sorted(keys), sorted(names))
        for name, value in args.items():
            self.assertEqual(value, 10)

    def test_string_args(self):
        resolver = self._makeOne()
        names = list(resolver._string_args)
        kwargs = {}
        for name in names:
            kwargs[name] = 'string'
        args = resolver.interpret_kwargs(kwargs)
        keys = args.keys()
        keys.sort()
        self.assertEqual(keys, names)
        for name, value in args.items():
            self.assertEqual(value, 'string')

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
        self.assertEqual(kwargs, {'read_only':1})
        kwargs = f({'read_only':'true'})
        self.assertEqual(kwargs, {'read_only':1})
        kwargs = f({'read_only':'on'})
        self.assertEqual(kwargs, {'read_only':1})
        kwargs = f({'read_only':'off'})
        self.assertEqual(kwargs, {'read_only':0})
        kwargs = f({'read_only':'no'})
        self.assertEqual(kwargs, {'read_only':0})
        kwargs = f({'read_only':'false'})
        self.assertEqual(kwargs, {'read_only':0})

    def test_call_no_qs(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('file:///tmp/foo/bar')
        self.assertEqual(args, ('/tmp/foo/bar',))
        self.assertEqual(kw, {})

    def test_call_abspath(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('file:///tmp/foo/bar?read_only=true')
        self.assertEqual(args, ('/tmp/foo/bar',))
        self.assertEqual(kw, {'read_only':1})

    def test_call_abspath_windows(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            'file://C:\\foo\\bar?read_only=true')
        self.assertEqual(args, ('C:\\foo\\bar',))
        self.assertEqual(kw, {'read_only':1})

    def test_call_normpath(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('file:///tmp/../foo/bar?read_only=true')
        self.assertEqual(args, ('/foo/bar',))
        self.assertEqual(kw, {'read_only':1})

    def test_invoke_factory_filestorage(self):
        import os
        self.assertFalse(os.path.exists(os.path.join(self.tmpdir, 'db.db')))
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            'file://%s/db.db?quota=200' % self.tmpdir)
        self.assertEqual(k,
                         (('%s/db.db' % self.tmpdir,), (('quota', 200),),
                          (('cache_size', 10000), ('database_name', 'unnamed'),
                           ('pool_size', 7)))
                         )
        factory()
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, 'db.db')))

    def test_demostorage(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            'file:///tmp/../foo/bar?demostorage=true')
        self.assertEqual(args, ('/foo/bar',))
        self.assertEqual(kw, {})

    def test_invoke_factory_demostorage(self):
        import os
        from ZODB.DemoStorage import DemoStorage
        from ZODB.FileStorage import FileStorage
        DB_FILE = os.path.join(self.tmpdir, 'db.db')
        self.assertFalse(os.path.exists(DB_FILE))
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            'file://%s/db.db?quota=200&demostorage=true' % self.tmpdir)
        self.assertEqual(k,
                         (('%s/db.db' % self.tmpdir,),
                          (('demostorage', 1),
                           ('quota', 200),
                          ),
                          (('cache_size', 10000),
                           ('database_name', 'unnamed'),
                           ('pool_size', 7)
                          ),
                         )
                        )
        db = factory()
        self.assertTrue(isinstance(db._storage, DemoStorage))
        self.assertTrue(isinstance(db._storage.base, FileStorage))
        self.assertTrue(os.path.exists(DB_FILE))

    def test_blobstorage(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            ('file:///tmp/../foo/bar'
             '?blobstorage_dir=/foo/bar&blobstorage_layout=bushy'))
        self.assertEqual(args, ('/foo/bar',))
        self.assertEqual(kw, {})

    def test_invoke_factory_blobstorage(self):
        import os
        from urllib import quote as q
        from ZODB.blob import BlobStorage
        DB_FILE = os.path.join(self.tmpdir, 'db.db')
        BLOB_DIR = os.path.join(self.tmpdir, 'blob')
        self.assertFalse(os.path.exists(DB_FILE))
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            'file://%s/db.db?quota=200'
            '&blobstorage_dir=%s/blob'
            '&blobstorage_layout=bushy' % (self.tmpdir, q(self.tmpdir)))
        self.assertEqual(k,
                         (('%s/db.db' % self.tmpdir,),
                          (('blobstorage_dir', '%s/blob' % self.tmpdir),
                           ('blobstorage_layout', 'bushy'),
                           ('quota', 200),
                          ),
                          (('cache_size', 10000),
                           ('database_name', 'unnamed'),
                           ('pool_size', 7)
                          ),
                         )
                        )
        db = factory()
        self.assertTrue(isinstance(db._storage, BlobStorage))
        self.assertTrue(os.path.exists(DB_FILE))
        self.assertTrue(os.path.exists(BLOB_DIR))

    def test_blobstorage_and_demostorage(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            ('file:///tmp/../foo/bar?demostorage=true'
             '&blobstorage_dir=/foo/bar&blobstorage_layout=bushy'))
        self.assertEqual(args, ('/foo/bar',))
        self.assertEqual(kw, {})

    def test_invoke_factory_blobstorage_and_demostorage(self):
        import os
        from urllib import quote as q
        from ZODB.DemoStorage import DemoStorage
        DB_FILE = os.path.join(self.tmpdir, 'db.db')
        BLOB_DIR = os.path.join(self.tmpdir, 'blob')
        self.assertFalse(os.path.exists(DB_FILE))
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            'file://%s/db.db?quota=200&demostorage=true'
            '&blobstorage_dir=%s/blob'
            '&blobstorage_layout=bushy' % (self.tmpdir, q(self.tmpdir)))
        self.assertEqual(k,
                         (('%s/db.db' % self.tmpdir,),
                          (('blobstorage_dir', '%s/blob' % self.tmpdir),
                           ('blobstorage_layout', 'bushy'),
                           ('demostorage', 1),
                           ('quota', 200),
                          ),
                          (('cache_size', 10000),
                           ('database_name', 'unnamed'),
                           ('pool_size', 7)
                          ),
                         )
                        )
        db = factory()
        self.assertTrue(isinstance(db._storage, DemoStorage))
        self.assertTrue(os.path.exists(DB_FILE))
        self.assertTrue(os.path.exists(BLOB_DIR))

    def test_dbargs(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            ('file:///tmp/../foo/bar?connection_pool_size=1'
             '&connection_cache_size=1&database_name=dbname'))
        self.assertEqual(k[2],
                         (('cache_size', 1), ('database_name', 'dbname'),
                          ('pool_size', 1)))


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
        self.assertEqual(kwargs, {'read_only':1})
        kwargs = f({'read_only':'true'})
        self.assertEqual(kwargs, {'read_only':1})
        kwargs = f({'read_only':'on'})
        self.assertEqual(kwargs, {'read_only':1})
        kwargs = f({'read_only':'off'})
        self.assertEqual(kwargs, {'read_only':0})
        kwargs = f({'read_only':'no'})
        self.assertEqual(kwargs, {'read_only':0})
        kwargs = f({'read_only':'false'})
        self.assertEqual(kwargs, {'read_only':0})

    def test_call_tcp_no_port(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zeo://localhost?debug=true')
        self.assertEqual(args, (('localhost', 9991),))
        self.assertEqual(kw, {'debug':1})
        self.assertEqual(k,
                         ((('localhost', 9991),), (('debug', 1),),
                          (('cache_size', 10000), ('database_name','unnamed'),
                           ('pool_size', 7))))

    def test_call_tcp(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zeo://localhost:8080?debug=true')
        self.assertEqual(args, (('localhost', 8080),))
        self.assertEqual(kw, {'debug':1})
        self.assertEqual(k,
                         ((('localhost', 8080),), (('debug', 1),),
                          (('cache_size', 10000), ('database_name','unnamed'),
                           ('pool_size', 7))))

    def test_call_unix(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zeo:///var/sock?debug=true')
        self.assertEqual(args, ('/var/sock',))
        self.assertEqual(kw, {'debug':1})
        self.assertEqual(k,
                         (('/var/sock',),
                          (('debug', 1),),
                          (('cache_size', 10000),
                           ('database_name', 'unnamed'),
                           ('pool_size', 7))))

    def test_invoke_factory(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zeo:///var/nosuchfile?wait=false')
        self.assertEqual(k, (('/var/nosuchfile',),
                             (('wait', 0),),
                             (('cache_size', 10000),
                              ('database_name', 'unnamed'), ('pool_size', 7))))
        from ZEO.ClientStorage import ClientDisconnected
        self.assertRaises(ClientDisconnected, factory)

    def test_demostorage(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zeo:///var/sock?demostorage=true')
        self.assertEqual(args, ('/var/sock',))
        self.assertEqual(kw, {})

    def test_invoke_factory_demostorage(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zeo:///var/nosuchfile?wait=false'
                                        '&demostorage=true')
        self.assertEqual(k, (('/var/nosuchfile',),
                             (('demostorage', 1),
                              ('wait', 0),),
                             (('cache_size', 10000),
                              ('database_name', 'unnamed'),
                              ('pool_size', 7),
                             ),
                            ))
        from ZEO.ClientStorage import ClientDisconnected
        self.assertRaises(ClientDisconnected, factory)

    def test_dbargs(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zeo://localhost:8080?debug=true&'
                                        'connection_pool_size=1&'
                                        'connection_cache_size=1&'
                                        'database_name=dbname')
        self.assertEqual(k[2],
                         (('cache_size', 1), ('database_name', 'dbname'),
                          ('pool_size', 1)))


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

    def test_named_database(self):
        self.tmp.write("""
        <zodb otherdb>
          <demostorage>
          </demostorage>
        </zodb>

        <zodb demodb>
          <mappingstorage>
          </mappingstorage>
        </zodb>
        """)
        self.tmp.flush()
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zconfig://%s#demodb' % self.tmp.name)
        db = factory()
        from ZODB.MappingStorage import MappingStorage
        self.assertTrue(isinstance(db._storage, MappingStorage))

    def test_anonymous_database(self):
        self.tmp.write("""
        <zodb>
          <mappingstorage>
          </mappingstorage>
        </zodb>

        <zodb demodb>
          <mappingstorage>
          </mappingstorage>
        </zodb>
        """)
        self.tmp.flush()
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zconfig://%s' % self.tmp.name)
        db = factory()
        from ZODB.MappingStorage import MappingStorage
        self.assertTrue(isinstance(db._storage, MappingStorage))

    def test_database_not_found(self):
        self.tmp.write("""
        <zodb x>
          <mappingstorage>
          </mappingstorage>
        </zodb>
        """)
        self.tmp.flush()
        resolver = self._makeOne()
        self.assertRaises(KeyError, resolver, 'zconfig://%s#y' % self.tmp.name)

class TestMappingStorageURIResolver(Base, unittest.TestCase):

    def _getTargetClass(self):
        from zodburi.resolvers import MappingStorageURIResolver
        return MappingStorageURIResolver

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass()

    def test_call_no_qs(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('memory://')
        self.assertEqual(args, ('',))
        self.assertEqual(kw, {})
        db = factory()
        from ZODB.MappingStorage import MappingStorage
        self.assertTrue(isinstance(db._storage, MappingStorage))

    def test_call_with_qs(self):
        uri='memory://storagename?connection_cache_size=100&database_name=fleeb'
        resolver = self._makeOne()
        k, args, kw, factory = resolver(uri)
        self.assertEqual(args, ('storagename',))
        self.assertEqual(kw, {})
        self.assertEqual(k,  (('storagename',),
                              (('cache_size', 100), ('database_name', 'fleeb'),
                               ('pool_size', 7))))
        db = factory()
        from ZODB.MappingStorage import MappingStorage
        self.assertTrue(isinstance(db._storage, MappingStorage))