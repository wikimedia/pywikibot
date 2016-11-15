# -*- coding: utf-8 -*-
"""Tests for the Namespace class."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from collections import Iterable

from pywikibot.site import Namespace, NamespacesDict
from pywikibot.tools import (
    PY2,
    StringTypes as basestring,
    UnicodeType as unicode,
)

from tests.aspects import unittest, TestCase, AutoDeprecationTestCase

# Default namespaces which should work in any MW wiki
_base_builtin_ns = {
    'Media': -2,
    'Special': -1,
    '': 0,
    'Talk': 1,
    'User': 2,
    'User talk': 3,
    'Project': 4,
    'Project talk': 5,
    'MediaWiki': 8,
    'MediaWiki talk': 9,
    'Template': 10,
    'Template talk': 11,
    'Help': 12,
    'Help talk': 13,
    'Category': 14,
    'Category talk': 15,
}
image_builtin_ns = dict(_base_builtin_ns)
image_builtin_ns['Image'] = 6
image_builtin_ns['Image talk'] = 7
file_builtin_ns = dict(_base_builtin_ns)
file_builtin_ns['File'] = 6
file_builtin_ns['File talk'] = 7
builtin_ns = dict(list(image_builtin_ns.items()) + list(file_builtin_ns.items()))


def builtin_NamespacesDict():
    """Return a NamespacesDict of the builtin namespaces."""
    return NamespacesDict(Namespace.builtin_namespaces())


class TestNamespaceObject(TestCase):

    """Test cases for Namespace class."""

    net = False

    def testNamespaceTypes(self):
        """Test cases for methods manipulating Namespace names."""
        ns = Namespace.builtin_namespaces(use_image_name=False)

        self.assertIsInstance(ns, dict)
        self.assertTrue(all(x in ns for x in range(0, 16)))

        self.assertTrue(all(isinstance(key, int)
                            for key in ns))
        self.assertTrue(all(isinstance(val, Iterable)
                            for val in ns.values()))
        self.assertTrue(all(isinstance(name, basestring)
                            for val in ns.values()
                            for name in val))

        # Use a namespace object as a dict key
        self.assertEqual(ns[ns[6]], ns[6])

    def testNamespaceConstructor(self):
        """Test Namespace constructor."""
        kwargs = {u'case': u'first-letter'}
        y = Namespace(id=6, custom_name=u'dummy', canonical_name=u'File',
                      aliases=[u'Image', u'Immagine'], **kwargs)

        self.assertEqual(y.id, 6)
        self.assertEqual(y.custom_name, u'dummy')
        self.assertEqual(y.canonical_name, u'File')

        self.assertNotEqual(y.custom_name, u'Dummy')
        self.assertNotEqual(y.canonical_name, u'file')

        self.assertIn(u'Image', y.aliases)
        self.assertIn(u'Immagine', y.aliases)

        self.assertEqual(len(y), 4)
        self.assertEqual(list(y), ['dummy', u'File', u'Image', u'Immagine'])
        self.assertEqual(y.case, u'first-letter')

    def testNamespaceNameCase(self):
        """Namespace names are always case-insensitive."""
        kwargs = {u'case': u'first-letter'}
        y = Namespace(id=6, custom_name=u'dummy', canonical_name=u'File',
                      aliases=[u'Image', u'Immagine'], **kwargs)
        self.assertIn(u'dummy', y)
        self.assertIn(u'Dummy', y)
        self.assertIn(u'file', y)
        self.assertIn(u'File', y)
        self.assertIn(u'image', y)
        self.assertIn(u'Image', y)
        self.assertIn(u'immagine', y)
        self.assertIn(u'Immagine', y)

    def testNamespaceToString(self):
        """Test Namespace __str__ and __unicode__."""
        ns = Namespace.builtin_namespaces(use_image_name=False)

        self.assertEqual(str(ns[0]), ':')
        self.assertEqual(str(ns[1]), 'Talk:')
        self.assertEqual(str(ns[6]), ':File:')

        self.assertEqual(unicode(ns[0]), u':')
        self.assertEqual(unicode(ns[1]), u'Talk:')
        self.assertEqual(unicode(ns[6]), u':File:')

        kwargs = {u'case': u'first-letter'}
        y = Namespace(id=6, custom_name=u'ملف', canonical_name=u'File',
                      aliases=[u'Image', u'Immagine'], **kwargs)

        self.assertEqual(str(y), ':File:')
        if PY2:
            self.assertEqual(unicode(y), u':ملف:')
        self.assertEqual(y.canonical_prefix(), ':File:')
        self.assertEqual(y.custom_prefix(), u':ملف:')

    def testNamespaceCompare(self):
        """Test Namespace comparisons."""
        a = Namespace(id=0, canonical_name=u'')

        self.assertEqual(a, 0)
        self.assertEqual(a, '')
        self.assertFalse(a < 0)
        self.assertFalse(a > 0)
        self.assertNotEqual(a, None)

        self.assertGreater(a, -1)

        x = Namespace(id=6, custom_name=u'dummy', canonical_name=u'File',
                      aliases=[u'Image', u'Immagine'])
        y = Namespace(id=6, custom_name=u'ملف', canonical_name=u'File',
                      aliases=[u'Image', u'Immagine'])
        z = Namespace(id=7, custom_name=u'dummy 7', canonical_name=u'File',
                      aliases=[u'Image', u'Immagine'])

        self.assertEqual(x, x)
        self.assertEqual(x, y)
        self.assertNotEqual(x, a)
        self.assertNotEqual(x, z)

        self.assertEqual(x, 6)
        self.assertEqual(x, u'dummy')
        self.assertEqual(x, u'Dummy')
        self.assertEqual(x, u'file')
        self.assertEqual(x, u'File')
        self.assertEqual(x, u':File')
        self.assertEqual(x, u':File:')
        self.assertEqual(x, u'File:')
        self.assertEqual(x, u'image')
        self.assertEqual(x, u'Image')

        self.assertFalse(x < 6)
        self.assertFalse(x > 6)

        self.assertEqual(y, u'ملف')

        self.assertLess(a, x)
        self.assertLess(x, z)
        self.assertLessEqual(a, x)
        self.assertGreater(x, a)
        self.assertGreater(x, 0)
        self.assertGreater(z, x)
        self.assertGreaterEqual(x, a)
        self.assertGreaterEqual(y, x)

        self.assertIn(6, [x, y, z])
        self.assertNotIn(8, [x, y, z])

    def testNamespaceNormalizeName(self):
        """Test Namespace.normalize_name."""
        self.assertEqual(Namespace.normalize_name(u'File'), u'File')
        self.assertEqual(Namespace.normalize_name(u':File'), u'File')
        self.assertEqual(Namespace.normalize_name(u'File:'), u'File')
        self.assertEqual(Namespace.normalize_name(u':File:'), u'File')

        self.assertEqual(Namespace.normalize_name(u''), u'')

        self.assertEqual(Namespace.normalize_name(u':'), False)
        self.assertEqual(Namespace.normalize_name(u'::'), False)
        self.assertEqual(Namespace.normalize_name(u':::'), False)
        self.assertEqual(Namespace.normalize_name(u':File::'), False)
        self.assertEqual(Namespace.normalize_name(u'::File:'), False)
        self.assertEqual(Namespace.normalize_name(u'::File::'), False)

    def test_repr(self):
        """Test Namespace.__repr__."""
        a = Namespace(id=0, canonical_name=u'Foo')
        s = repr(a)
        r = "Namespace(id=0, custom_name=%r, canonical_name=%r, aliases=[])" \
            % (unicode('Foo'), unicode('Foo'))
        self.assertEqual(s, r)

        a.defaultcontentmodel = 'bar'
        s = repr(a)
        r = ('Namespace(id=0, custom_name=%r, canonical_name=%r, aliases=[], '
             'defaultcontentmodel=%r)' %
             (unicode('Foo'), unicode('Foo'), unicode('bar')))
        self.assertEqual(s, r)

        a.case = 'upper'
        s = repr(a)
        r = ('Namespace(id=0, custom_name=%r, canonical_name=%r, aliases=[], '
             'case=%r, defaultcontentmodel=%r)' %
             (unicode('Foo'), unicode('Foo'), unicode('upper'), unicode('bar')))
        self.assertEqual(s, r)

        b = eval(repr(a))
        self.assertEqual(a, b)


class TestNamespaceDictDeprecated(AutoDeprecationTestCase):

    """Test static/classmethods in Namespace replaced by NamespacesDict."""

    net = False

    def test_resolve_equal(self):
        """Test Namespace.resolve success."""
        namespaces = Namespace.builtin_namespaces(use_image_name=False)
        main_ns = namespaces[0]
        file_ns = namespaces[6]
        special_ns = namespaces[-1]

        self.assertEqual(Namespace.resolve([6]), [file_ns])
        self.assertEqual(Namespace.resolve(['File']), [file_ns])
        self.assertEqual(Namespace.resolve(['6']), [file_ns])
        self.assertEqual(Namespace.resolve([file_ns]), [file_ns])

        self.assertEqual(Namespace.resolve([file_ns, special_ns]),
                         [file_ns, special_ns])
        self.assertEqual(Namespace.resolve([file_ns, file_ns]),
                         [file_ns, file_ns])

        self.assertEqual(Namespace.resolve(6), [file_ns])
        self.assertEqual(Namespace.resolve('File'), [file_ns])
        self.assertEqual(Namespace.resolve('6'), [file_ns])
        self.assertEqual(Namespace.resolve(file_ns), [file_ns])

        self.assertEqual(Namespace.resolve(0), [main_ns])
        self.assertEqual(Namespace.resolve('0'), [main_ns])

        self.assertEqual(Namespace.resolve(-1), [special_ns])
        self.assertEqual(Namespace.resolve('-1'), [special_ns])

        self.assertEqual(Namespace.resolve('File:'), [file_ns])
        self.assertEqual(Namespace.resolve(':File'), [file_ns])
        self.assertEqual(Namespace.resolve(':File:'), [file_ns])

        self.assertEqual(Namespace.resolve('Image:'), [file_ns])
        self.assertEqual(Namespace.resolve(':Image'), [file_ns])
        self.assertEqual(Namespace.resolve(':Image:'), [file_ns])

    def test_resolve_exceptions(self):
        """Test Namespace.resolve failure."""
        self.assertRaises(TypeError, Namespace.resolve, [True])
        self.assertRaises(TypeError, Namespace.resolve, [False])
        self.assertRaises(TypeError, Namespace.resolve, [None])
        self.assertRaises(TypeError, Namespace.resolve, True)
        self.assertRaises(TypeError, Namespace.resolve, False)
        self.assertRaises(TypeError, Namespace.resolve, None)

        self.assertRaises(KeyError, Namespace.resolve, -10)
        self.assertRaises(KeyError, Namespace.resolve, '-10')
        self.assertRaises(KeyError, Namespace.resolve, 'foo')
        self.assertRaises(KeyError, Namespace.resolve, ['foo'])

        self.assertRaisesRegex(KeyError,
                               r'Namespace identifier\(s\) not recognised: -10',
                               Namespace.resolve, [-10, 0])
        self.assertRaisesRegex(KeyError,
                               r'Namespace identifier\(s\) not recognised: foo',
                               Namespace.resolve, [0, 'foo'])
        self.assertRaisesRegex(KeyError,
                               r'Namespace identifier\(s\) not recognised: -10,-11',
                               Namespace.resolve, [-10, 0, -11])

    def test_lookup_name(self):
        """Test Namespace.lookup_name."""
        file_nses = Namespace.builtin_namespaces(use_image_name=False)
        image_nses = Namespace.builtin_namespaces(use_image_name=True)

        for name, ns_id in builtin_ns.items():
            file_ns = Namespace.lookup_name(name, file_nses)
            self.assertIsInstance(file_ns, Namespace)
            image_ns = Namespace.lookup_name(name, image_nses)
            self.assertIsInstance(image_ns, Namespace)
            with self.disable_assert_capture():
                self.assertEqual(file_ns.id, ns_id)
                self.assertEqual(image_ns.id, ns_id)


class TestNamespaceCollections(TestCase):

    """Test how Namespace interact when in collections."""

    net = False

    def test_set(self):
        """Test converting sequence of Namespace to a set."""
        namespaces = Namespace.builtin_namespaces(use_image_name=False)

        self.assertTrue(all(isinstance(x, int) for x in namespaces))
        self.assertTrue(all(isinstance(x, int) for x in namespaces.keys()))
        self.assertTrue(all(isinstance(x, Namespace)
                            for x in namespaces.values()))

        namespaces_set = set(namespaces)

        self.assertEqual(len(namespaces), len(namespaces_set))
        self.assertTrue(all(isinstance(x, int) for x in namespaces_set))

    def test_set_minus(self):
        """Test performing set minus operation on set of Namespace objects."""
        namespaces = Namespace.builtin_namespaces(use_image_name=False)

        excluded_namespaces = set([-1, -2])

        positive_namespaces = set(namespaces) - excluded_namespaces

        self.assertEqual(len(namespaces),
                         len(positive_namespaces) + len(excluded_namespaces))


class TestNamespacesDictLookupName(TestCase):

    """Test NamespacesDict.lookup_name and lookup_normalized_name."""

    net = False

    def test_lookup_name(self):
        """Test lookup_name."""
        namespaces = builtin_NamespacesDict()
        self.assertIs(namespaces.lookup_name('project'), namespaces[4])
        self.assertIs(namespaces.lookup_name('PROJECT'), namespaces[4])
        self.assertIs(namespaces.lookup_name('Project'), namespaces[4])
        self.assertIs(namespaces.lookup_name('Project:'), namespaces[4])

    def test_lookup_normalized_name(self):
        """Test lookup_normalized_name."""
        namespaces = builtin_NamespacesDict()
        self.assertIs(namespaces.lookup_normalized_name('project'),
                      namespaces[4])
        self.assertIsNone(namespaces.lookup_normalized_name('PROJECT'))
        self.assertIsNone(namespaces.lookup_normalized_name('Project'))
        self.assertIsNone(namespaces.lookup_normalized_name('Project:'))


class TestNamespacesDictGetItem(TestCase):

    """Test NamespacesDict.__getitem__."""

    net = False

    def test_ids(self):
        """Test lookup by canonical namespace id."""
        namespaces = builtin_NamespacesDict()
        for namespace in namespaces.values():
            self.assertEqual(namespace, namespaces[namespace.id])

    def test_namespace(self):
        """Test lookup by Namespace object."""
        namespaces = builtin_NamespacesDict()
        for namespace in namespaces.values():
            self.assertEqual(namespace, namespaces[namespace])

    def test_invalid_id(self):
        """Test lookup by invalid id."""
        namespaces = builtin_NamespacesDict()
        lower = min(namespaces.keys()) - 1
        higher = max(namespaces.keys()) + 1
        self.assertRaises(KeyError, namespaces.__getitem__, lower)
        self.assertRaises(KeyError, namespaces.__getitem__, higher)

    def test_canonical_name(self):
        """Test lookup by canonical namespace name."""
        namespaces = builtin_NamespacesDict()
        for namespace in namespaces.values():
            self.assertEqual(namespace, namespaces[namespace.canonical_name])
            self.assertEqual(namespace,
                             namespaces[namespace.canonical_name.upper()])

    def test_canonical_attr(self):
        """Test attribute lookup by canonical namespace name."""
        namespaces = builtin_NamespacesDict()
        self.assertEqual(namespaces[0], namespaces.MAIN)
        self.assertEqual(namespaces[1], namespaces.TALK)

        for namespace in namespaces.values():
            if namespace.id == 0:
                continue
            attr = namespace.canonical_name.upper()
            self.assertEqual(namespace, getattr(namespaces, attr))

    def test_all(self):
        """Test lookup by any namespace name."""
        namespaces = builtin_NamespacesDict()
        for namespace in namespaces.values():
            for name in namespace:
                self.assertEqual(namespace, namespaces[name.upper()])

    def test_invalid_name(self):
        """Test lookup by invalid name."""
        namespaces = builtin_NamespacesDict()
        self.assertRaises(KeyError, namespaces.__getitem__, 'FOO')
        # '|' is not permitted in namespace names
        self.assertRaises(KeyError, namespaces.__getitem__, '|')


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
