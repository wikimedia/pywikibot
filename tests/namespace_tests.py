# -*- coding: utf-8  -*-
"""Tests for the Namespace class."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from collections import Iterable
from pywikibot.site import Namespace
from tests.utils import NoSiteTestCase, unittest

import sys
if sys.version_info[0] > 2:
    basestring = (str, )
    unicode = str


class TestNamespaceObject(NoSiteTestCase):

    """Test cases for Namespace class."""

    # These should work in any MW wiki
    builtin_ids = {
        'Media': -2,
        'Special': -1,
        '': 0,
        'Talk': 1,
        'User': 2,
        'User talk': 3,
        'Project': 4,
        'Project talk': 5,
        'File': 6,
        'File talk': 7,
        'MediaWiki': 8,
        'MediaWiki talk': 9,
        'Template': 10,
        'Template talk': 11,
        'Help': 12,
        'Help talk': 13,
        'Category': 14,
        'Category talk': 15,
    }

    old_builtin_ids = {
        'Image': 6,
        'Image talk': 7,
    }

    all_builtin_ids = dict(list(builtin_ids.items()) + list(old_builtin_ids.items()))

    def testNamespaceTypes(self):
        """Test cases for methods manipulating namespace names."""
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

        self.assertTrue(all(isinstance(Namespace.lookup_name(b, ns), Namespace)
                            for b in self.builtin_ids))

        self.assertTrue(all(Namespace.lookup_name(b, ns).id == self.all_builtin_ids[b]
                            for b in self.all_builtin_ids))

        ns = Namespace.builtin_namespaces(use_image_name=True)

        self.assertTrue(all(isinstance(Namespace.lookup_name(b, ns), Namespace)
                            for b in self.builtin_ids))

        self.assertTrue(all(Namespace.lookup_name(b, ns).id == self.all_builtin_ids[b]
                            for b in self.all_builtin_ids))

    def testNamespaceConstructor(self):
        kwargs = {u'case': u'first-letter'}
        y = Namespace(id=6, custom_name=u'dummy', canonical_name=u'File',
                      aliases=[u'Image', u'Immagine'], **kwargs)

        self.assertEquals(y.id, 6)
        self.assertEquals(y.custom_name, u'dummy')
        self.assertEquals(y.canonical_name, u'File')

        self.assertNotEquals(y.custom_name, u'Dummy')
        self.assertNotEquals(y.canonical_name, u'file')

        self.assertIn(u'Image', y.aliases)
        self.assertIn(u'Immagine', y.aliases)

        self.assertEquals(len(y), 4)
        self.assertEquals(list(y), ['dummy', u'File', u'Image', u'Immagine'])
        self.assertEquals(y.case, u'first-letter')

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
        ns = Namespace.builtin_namespaces(use_image_name=False)

        self.assertEquals(str(ns[0]), ':')
        self.assertEquals(str(ns[1]), 'Talk:')
        self.assertEquals(str(ns[6]), ':File:')

        self.assertEquals(unicode(ns[0]), u':')
        self.assertEquals(unicode(ns[1]), u'Talk:')
        self.assertEquals(unicode(ns[6]), u':File:')

        kwargs = {u'case': u'first-letter'}
        y = Namespace(id=6, custom_name=u'ملف', canonical_name=u'File',
                      aliases=[u'Image', u'Immagine'], **kwargs)

        if sys.version_info[0] == 2:
            self.assertEquals(str(y), ':File:')
            self.assertEquals(unicode(y), u':ملف:')
        else:
            self.assertEquals(str(y), u':ملف:')

    def testNamespaceCompare(self):
        a = Namespace(id=0, canonical_name=u'')

        self.assertEquals(a, 0)
        self.assertEquals(a, '')
        self.assertEquals(a, None)

        x = Namespace(id=6, custom_name=u'dummy', canonical_name=u'File',
                      aliases=[u'Image', u'Immagine'])
        y = Namespace(id=6, custom_name=u'ملف', canonical_name=u'File',
                      aliases=[u'Image', u'Immagine'])
        z = Namespace(id=7, custom_name=u'dummy', canonical_name=u'File',
                      aliases=[u'Image', u'Immagine'])

        self.assertEquals(x, x)
        self.assertEquals(x, y)
        self.assertNotEquals(x, a)
        self.assertNotEquals(x, z)

        self.assertEquals(x, 6)
        self.assertEquals(x, u'dummy')
        self.assertEquals(x, u'Dummy')
        self.assertEquals(x, u'file')
        self.assertEquals(x, u'File')
        self.assertEquals(x, u':File')
        self.assertEquals(x, u':File:')
        self.assertEquals(x, u'File:')
        self.assertEquals(x, u'image')
        self.assertEquals(x, u'Image')

        self.assertEquals(y, u'ملف')

        # FIXME: Namespace is missing operators required for py3
        if sys.version_info[0] > 2:
            return

        self.assertTrue(a < x)
        self.assertTrue(x > a)
        self.assertTrue(z > x)

    def testNamespaceNormalizeName(self):
        self.assertEquals(Namespace.normalize_name(u'File'), u'File')
        self.assertEquals(Namespace.normalize_name(u':File'), u'File')
        self.assertEquals(Namespace.normalize_name(u'File:'), u'File')
        self.assertEquals(Namespace.normalize_name(u':File:'), u'File')

        self.assertEquals(Namespace.normalize_name(u''), u'')

        self.assertEquals(Namespace.normalize_name(u':'), False)
        self.assertEquals(Namespace.normalize_name(u'::'), False)
        self.assertEquals(Namespace.normalize_name(u':::'), False)
        self.assertEquals(Namespace.normalize_name(u':File::'), False)
        self.assertEquals(Namespace.normalize_name(u'::File:'), False)
        self.assertEquals(Namespace.normalize_name(u'::File::'), False)

    def test_repr(self):
        a = Namespace(id=0, canonical_name=u'Foo')
        s = repr(a)
        r = "Namespace(id=0, custom_name=%r, canonical_name=%r, aliases=[])" \
            % (unicode('Foo'), unicode('Foo'))
        self.assertEquals(s, r)

        a.info['defaultcontentmodel'] = 'bar'
        r = {'defaultcontentmodel': 'bar'}
        self.assertEquals(a.info, r)

        s = repr(a)
        r = "Namespace(id=0, custom_name=%r, canonical_name=%r, aliases=[], defaultcontentmodel='bar')" \
            % (unicode('Foo'), unicode('Foo'))
        self.assertEquals(s, r)

        a.info['case'] = 'upper'
        r = {'defaultcontentmodel': 'bar', 'case': 'upper'}
        self.assertEquals(a.info, r)

        s = repr(a)
        r = "Namespace(id=0, custom_name=%r, canonical_name=%r, aliases=[], case='upper', defaultcontentmodel='bar')" \
            % (unicode('Foo'), unicode('Foo'))
        self.assertEquals(s, r)

        b = eval(repr(a))
        self.assertEquals(a, b)
        self.assertEquals(a.info, b.info)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
