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
        from zodburi import resolve_uri, connection_parameters, parameters
        uri = 'memory://test?database_name=dbname'
        for i, parameter in enumerate(connection_parameters):
            uri += '&connection_%s=%d' % (parameter, i)
            if parameter == 'cache_size_bytes':
                uri += 'MB'
        factory, dbkw = resolve_uri(uri)
        factory()
        MappingStorage.assert_called_once_with('test')
        expect = dict(database_name='dbname')
        for i, parameter in enumerate(connection_parameters):
            parameter = 'connection_' + parameter
            expect[parameters[parameter]] = i
            if parameter == 'connection_cache_size_bytes':
                expect[parameters[parameter]] *= 1<<20
        self.assertEqual(dbkw, expect)

    def test_it_cant_resolve(self):
        from zodburi import resolve_uri
        self.assertRaises(KeyError, resolve_uri, 'http://whatevs')

    def test_it_extra_kw(self):
        from zodburi import resolve_uri
        self.assertRaises(KeyError, resolve_uri, 'memory://?foo=bar')
