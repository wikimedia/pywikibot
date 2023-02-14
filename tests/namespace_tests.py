#!/usr/bin/env python3
"""Tests for the Namespace class."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
from collections.abc import Iterable
from contextlib import suppress

from pywikibot.site import Namespace, NamespacesDict
from pywikibot.site._namespace import BuiltinNamespace
from tests.aspects import TestCase, unittest


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
builtin_ns = dict(list(image_builtin_ns.items())
                  + list(file_builtin_ns.items()))


def builtin_NamespacesDict():
    """Return a NamespacesDict of the builtin namespaces."""
    return NamespacesDict(Namespace.builtin_namespaces())


class TestNamespaceObject(TestCase):

    """Test cases for Namespace class."""

    net = False

    def test_enums(self):
        """Test builtin namespace enum in Namespace."""
        self.assertEqual(BuiltinNamespace.MAIN, 0)
        self.assertEqual(Namespace.MAIN, BuiltinNamespace.MAIN)
        self.assertEqual(Namespace.MEDIA, -2)
        self.assertGreater(Namespace.MAIN, Namespace.MEDIA)
        self.assertLess(Namespace.MEDIA, Namespace.MAIN)
        self.assertEqual(Namespace.CATEGORY, 14)
        self.assertGreater(Namespace.CATEGORY, Namespace.HELP_TALK)

    def testNamespaceTypes(self):
        """Test cases for methods manipulating Namespace names."""
        ns = Namespace.builtin_namespaces()

        self.assertIsInstance(ns, dict)
        for ns_number in range(16):
            self.assertIn(ns_number, ns)
            # Use a namespace object as a dict key
            self.assertEqual(ns[ns[ns_number]], ns[ns_number])

        for key, value in ns.items():
            self.assertIsInstance(key, int)
            self.assertIsInstance(value, Iterable)
            self.assertTrue(value)
            for name in value:
                self.assertIsInstance(name, str)
            self.assertEqual(ns[ns[key]], ns[key])

    def testNamespaceConstructor(self):
        """Test Namespace constructor."""
        kwargs = {'case': 'first-letter'}
        y = Namespace(id=6, custom_name='dummy', canonical_name='File',
                      aliases=['Image', 'Immagine'], **kwargs)

        self.assertEqual(y.id, 6)
        self.assertEqual(y.custom_name, 'dummy')
        self.assertEqual(y.canonical_name, 'File')

        self.assertNotEqual(y.custom_name, 'Dummy')
        self.assertNotEqual(y.canonical_name, 'file')

        self.assertIn('Image', y.aliases)
        self.assertIn('Immagine', y.aliases)

        self.assertLength(y, 4)
        self.assertEqual(list(y), ['dummy', 'File', 'Image', 'Immagine'])
        self.assertEqual(y.case, 'first-letter')

    def testNamespaceNameCase(self):
        """Namespace names are always case-insensitive."""
        kwargs = {'case': 'first-letter'}
        y = Namespace(id=6, custom_name='dummy', canonical_name='File',
                      aliases=['Image', 'Immagine'], **kwargs)
        self.assertIn('dummy', y)
        self.assertIn('Dummy', y)
        self.assertIn('file', y)
        self.assertIn('File', y)
        self.assertIn('image', y)
        self.assertIn('Image', y)
        self.assertIn('immagine', y)
        self.assertIn('Immagine', y)

    def testNamespaceToString(self):
        """Test Namespace __str__."""
        ns = Namespace.builtin_namespaces()

        self.assertEqual(str(ns[0]), ':')
        self.assertEqual(str(ns[1]), 'Talk:')
        self.assertEqual(str(ns[6]), ':File:')

        kwargs = {'case': 'first-letter'}
        y = Namespace(id=6, custom_name='ملف', canonical_name='File',
                      aliases=['Image', 'Immagine'], **kwargs)

        self.assertEqual(str(y), ':File:')
        self.assertEqual(y.canonical_prefix(), ':File:')
        self.assertEqual(y.custom_prefix(), ':ملف:')

    def testNamespaceCompare(self):
        """Test Namespace comparisons."""
        a = Namespace(id=0, canonical_name='')

        self.assertEqual(a, 0)
        self.assertEqual(a, '')
        self.assertGreaterEqual(a, 0)
        self.assertLessEqual(a, 0)
        self.assertIsNotNone(a)

        self.assertGreater(a, -1)

        x = Namespace(id=6, custom_name='dummy', canonical_name='File',
                      aliases=['Image', 'Immagine'])
        y = Namespace(id=6, custom_name='ملف', canonical_name='File',
                      aliases=['Image', 'Immagine'])
        z = Namespace(id=7, custom_name='dummy 7', canonical_name='File',
                      aliases=['Image', 'Immagine'])

        self.assertEqual(x, x)
        self.assertEqual(x, y)
        self.assertNotEqual(x, a)
        self.assertNotEqual(x, z)

        self.assertEqual(x, 6)
        self.assertEqual(x, 'dummy')
        self.assertEqual(x, 'Dummy')
        self.assertEqual(x, 'file')
        self.assertEqual(x, 'File')
        self.assertEqual(x, ':File')
        self.assertEqual(x, ':File:')
        self.assertEqual(x, 'File:')
        self.assertEqual(x, 'image')
        self.assertEqual(x, 'Image')

        self.assertGreaterEqual(x, 6)
        self.assertLessEqual(x, 6)

        self.assertEqual(y, 'ملف')

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
        self.assertEqual(Namespace.normalize_name('File'), 'File')
        self.assertEqual(Namespace.normalize_name(':File'), 'File')
        self.assertEqual(Namespace.normalize_name('File:'), 'File')
        self.assertEqual(Namespace.normalize_name(':File:'), 'File')

        self.assertEqual(Namespace.normalize_name(''), '')

        self.assertEqual(Namespace.normalize_name(':'), False)
        self.assertEqual(Namespace.normalize_name('::'), False)
        self.assertEqual(Namespace.normalize_name(':::'), False)
        self.assertEqual(Namespace.normalize_name(':File::'), False)
        self.assertEqual(Namespace.normalize_name('::File:'), False)
        self.assertEqual(Namespace.normalize_name('::File::'), False)

    def test_repr(self):
        """Test Namespace.__repr__."""
        a = Namespace(id=0, canonical_name='Foo')
        s = repr(a)
        r = 'Namespace(id=0, custom_name={foo!r}, canonical_name={foo!r}, ' \
            'aliases=[])'.format(foo='Foo')
        self.assertEqual(s, r)

        a.defaultcontentmodel = 'bar'
        s = repr(a)
        r = ('Namespace(id=0, custom_name={foo!r}, canonical_name={foo!r}, '
             'aliases=[], defaultcontentmodel={bar!r})'
             .format(foo='Foo', bar='bar'))
        self.assertEqual(s, r)

        a.case = 'upper'
        s = repr(a)
        r = ('Namespace(id=0, custom_name={foo!r}, canonical_name={foo!r}, '
             'aliases=[], case={case!r}, defaultcontentmodel={bar!r})'
             .format(foo='Foo', case='upper', bar='bar'))
        self.assertEqual(s, r)

        b = eval(repr(a))
        self.assertEqual(a, b)


class TestNamespaceCollections(TestCase):

    """Test how Namespace interact when in collections."""

    net = False

    def test_set(self):
        """Test converting sequence of Namespace to a set."""
        namespaces = Namespace.builtin_namespaces()

        for key, value in namespaces.items():
            self.assertIsInstance(key, int)
            self.assertIsInstance(value, Namespace)

        namespaces_set = set(namespaces)
        self.assertLength(namespaces, namespaces_set)
        for key in namespaces_set:
            self.assertIsInstance(key, int)

    def test_set_minus(self):
        """Test performing set minus operation on set of Namespace objects."""
        namespaces = Namespace.builtin_namespaces()
        excluded_namespaces = {-1, -2}
        positive_namespaces = set(namespaces) - excluded_namespaces

        self.assertLength(namespaces,
                          len(positive_namespaces) + len(excluded_namespaces))


class TestNamespacesDictLookupName(TestCase):

    """Test NamespacesDict.lookup_name and lookup_normalized_name."""

    net = False

    tests = {
        4: ['project', 'PROJECT', 'Project', 'Project:'],
        5: ['project talk', 'PROJECT TALK', 'Project talk', 'Project Talk:',
            'project_talk', 'PROJECT_TALK', 'Project_talk', 'Project_Talk:'],
    }

    def setUp(self):
        """Setup namespaces dict."""
        super().setUp()
        self.namespaces = builtin_NamespacesDict()

    def test_lookup_name(self):
        """Test lookup_name and getitem."""
        for ns_id, values in self.tests.items():
            for name in values:
                with self.subTest(name=name, ns_id=ns_id):
                    # test lookup_name
                    self.assertIs(self.namespaces.lookup_name(name),
                                  self.namespaces[ns_id])
                    # test __getitem__
                    self.assertEqual(self.namespaces[name].id, ns_id)

    def test_getattr(self):
        """Test NamespacesDict.__getattr__."""
        for ns_id, values in self.tests.items():
            for name in values:
                if name.endswith(':') or ' ' in name:
                    continue  # no valid attribute but causes syntax error

                with self.subTest(name=name, ns_id=ns_id):
                    if name.isupper():
                        result = eval('self.namespaces.{name}.id'
                                      .format(name=name))
                        self.assertEqual(result, ns_id)
                    else:
                        with self.assertRaises(AttributeError):
                            exec('self.namespaces.{name}.id'
                                 .format(name=name))

    def test_lookup_normalized_name(self):
        """Test lookup_normalized_name."""
        for ns_id, values in self.tests.items():
            for name in values:
                with self.subTest(name=name, ns_id=ns_id):
                    if name.islower() and '_' not in name:
                        self.assertIs(
                            self.namespaces.lookup_normalized_name(name),
                            self.namespaces[ns_id])
                    else:
                        self.assertIsNone(
                            self.namespaces.lookup_normalized_name(name))


class TestNamespacesDictGetItem(TestCase):

    """Test NamespacesDict.__getitem__."""

    VALIDNUMBER_RE = r'-?(0|[1-9]\d*)'
    EMPTYTEXT_RE = r'\s*'

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
        with self.assertRaisesRegex(KeyError, self.VALIDNUMBER_RE):
            namespaces[lower]
        with self.assertRaisesRegex(KeyError, self.VALIDNUMBER_RE):
            namespaces[higher]

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
        with self.assertRaisesRegex(KeyError, self.EMPTYTEXT_RE):
            namespaces['FOO']
        # '|' is not permitted in namespace names
        with self.assertRaisesRegex(KeyError, self.EMPTYTEXT_RE):
            namespaces['|']


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
