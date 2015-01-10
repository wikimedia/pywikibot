# -*- coding: utf-8  -*-
"""Test valid templates."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import re
from tests.aspects import unittest, MetaTestCaseClass, TestCase
import pywikibot
from pywikibot import i18n


PACKAGES = (
    'redirect-broken-redirect-template',  # speedy deletion template
    'archivebot-archiveheader',  # archive header template
)


class TestValidTemplateMeta(MetaTestCaseClass):

    """Test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        # this comment is to avoid senseless flake8 warning

        def test_method(msg, code):

            def test_template(self):
                """Test validity of template."""
                if msg:
                    # check whether the message contains a template
                    template = re.findall(u'.*?{{(.*?)[|}]', msg)
                    self.assertTrue(template)

                    if template:
                        # check whether site is valid
                        site = pywikibot.Site('en', 'wikipedia')
                        self.assertTrue(code in site.languages())

                        # check whether template exists
                        title = template[0]
                        site = pywikibot.Site(code, 'wikipedia')
                        page = pywikibot.Page(site, title, ns=10)
                        self.assertTrue(page.exists())

            return test_template

        # create test methods for package messages processed by unittest
        for package in PACKAGES:
            for lang in i18n.twget_keys(package):
                template_msg = i18n.twtranslate(lang, package, fallback=False)
                if template_msg is None:
                    continue
                test_name = "test_%s_%s" % (package.replace('-', '_'), lang)
                dct[test_name] = test_method(template_msg, lang)
        return type.__new__(cls, name, bases, dct)


class TestValidTemplate(TestCase):

    """Test cases for date library processed by unittest."""

    __metaclass__ = TestValidTemplateMeta
    net = True  # magic flag tells jenkins to not run the test.


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
