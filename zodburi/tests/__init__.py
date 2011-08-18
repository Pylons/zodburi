import mock
import unittest


class TestResolveURI(unittest.TestCase):

    @mock.patch('zodburi.resolvers.MappingStorage')
    def test_it(self, MappingStorage):
        from zodburi import resolve_uri
        factory, dbkw = resolve_uri('memory://')
        factory()
        MappingStorage.assert_called_once_with('')
        self.assertEqual(dbkw, {
            'cache_size': 10000,
            'pool_size': 7,
            'database_name': 'unnamed'})

    @mock.patch('zodburi.resolvers.MappingStorage')
    def test_it_with_dbkw(self, MappingStorage):
        from zodburi import resolve_uri
        factory, dbkw = resolve_uri(
            'memory://test?connection_cache_size=1&connection_pool_size=2&'
            'database_name=dbname')
        factory()
        MappingStorage.assert_called_once_with('test')
        self.assertEqual(dbkw, {
            'cache_size': 1,
            'pool_size': 2,
            'database_name': 'dbname'})

    def test_it_cant_resolve(self):
        from zodburi import resolve_uri
        self.assertRaises(KeyError, resolve_uri, 'http://whatevs')

    def test_it_extra_kw(self):
        from zodburi import resolve_uri
        self.assertRaises(KeyError, resolve_uri, 'memory://?foo=bar')
