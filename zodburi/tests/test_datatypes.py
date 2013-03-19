import unittest

_marker = object()
class SuffixMultiplierTests(unittest.TestCase):

    def _getTargetClass(self):
        from zodburi.datatypes import SuffixMultiplier
        return SuffixMultiplier

    def _makeOne(self, d=None, default=_marker):
        if d is None:
            d = {}
        if default is _marker:
            return self._getTargetClass()(d)
        return self._getTargetClass()(d, default)

    def test_ctor_simple(self):
        sm = self._makeOne()
        self.assertEqual(sm._d, {})
        self.assertEqual(sm._default, 1)
        self.assertEqual(sm._keysz, None)

    def test_ctor_w_explicit_default(self):
        sm = self._makeOne(default=3)
        self.assertEqual(sm._default, 3)

    def test_ctor_w_normal_suffixes(self):
        SFX = {'aaa': 2, 'bbb': 3}
        sm = self._makeOne(SFX)
        self.assertEqual(sm._d, SFX)
        self.assertEqual(sm._default, 1)
        self.assertEqual(sm._keysz, 3)

    def test_ctor_w_mismatched_suffixes(self):
        SFX = {'aaa': 2, 'bbbb': 3}
        self.assertRaises(ValueError, self._makeOne, SFX)

    def test___call____miss(self):
        SFX = {'aaa': 2, 'bbb': 3}
        sm = self._makeOne(SFX)
        self.assertEqual(sm('14'), 14)

    def test___call____hit(self):
        SFX = {'aaa': 2, 'bbb': 3}
        sm = self._makeOne(SFX)
        self.assertEqual(sm('14bbb'), 42)


class Test_convert_bytesize(unittest.TestCase):

    def _callFUT(self, value):
        from zodburi.datatypes import convert_bytesize
        return convert_bytesize(value)

    def test_hit(self):
        self.assertEqual(self._callFUT('14kb'), 14 * 1024)
        self.assertEqual(self._callFUT('14mb'), 14 * 1024 * 1024)
        self.assertEqual(self._callFUT('14gb'), 14 * 1024 * 1024 * 1024)

    def test_miss(self):
        self.assertEqual(self._callFUT('14'), 14)


class Test_convert_int(unittest.TestCase):

    def _callFUT(self, value):
        from zodburi.datatypes import convert_int
        return convert_int(value)

    def test_hit_falsetypes(self):
        from zodburi.datatypes import FALSETYPES
        for v in FALSETYPES:
            self.assertEqual(self._callFUT(v), 0)
            self.assertEqual(self._callFUT(v.title()), 0)

    def test_hit_truetypes(self):
        from zodburi.datatypes import TRUETYPES
        for v in TRUETYPES:
            self.assertEqual(self._callFUT(v), 1)
            self.assertEqual(self._callFUT(v.title()), 1)

    def test_hit_normal(self):
        self.assertEqual(self._callFUT('14'), 14)

    def test_miss(self):
        self.assertRaises(ValueError, self._callFUT, 'notanint')


class Test_convert_tuple(unittest.TestCase):

    def _callFUT(self, value):
        from zodburi.datatypes import convert_tuple
        return convert_tuple(value)

    def test_empty(self):
        self.assertEqual(self._callFUT(''), ('',))

    def test_wo_commas(self):
        self.assertEqual(self._callFUT('abc'), ('abc',))

    def test_w_commas(self):
        self.assertEqual(self._callFUT('abc,def'), ('abc', 'def'))
