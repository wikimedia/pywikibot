# -*- coding: utf-8  -*-
"""
Tests for the site module.
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'


import unittest
import pywikibot

mysite = pywikibot.Site("en", "wikipedia")


class TestSiteObject(unittest.TestCase):
    """Test cases for Site methods."""
    def testBaseMethods(self):
        """Test cases for BaseSite methods"""
        self.assertEqual(mysite.family(), pywikibot.site.Family("wikipedia"))
        self.assertEqual(mysite.language(), "en")
        self.assert_(isinstance(mysite.user(), (basestring, type(None))))
        self.assertEqual(mysite.sitename(), "wikipedia:en")
        self.assertEqual(mysite.ns_normalize("project"), "Wikipedia")
        self.assertEqual(mysite.redirect(), "REDIRECT")


if __name__ == '__main__':
    try:
        try:
            unittest.main()
        except SystemExit:
            pass
    finally:
        pywikibot.stopme()
