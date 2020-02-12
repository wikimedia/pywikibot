# -*- coding: utf-8 -*-
"""Tests for isbn script."""
#
# (C) Pywikibot team, 2014-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import pywikibot

try:
    from stdnum.exceptions import ValidationError as StdNumValidationError
except ImportError:
    StdNumValidationError = None

from pywikibot import Bot, Claim, ItemPage
from pywikibot.cosmetic_changes import CosmeticChangesToolkit, CANCEL_MATCH
from pywikibot.tools import has_module

from scripts.isbn import (
    InvalidIsbnException as IsbnExc,
    hyphenateIsbnNumbers, convertIsbn10toIsbn13,
    main
)

from tests.aspects import (
    unittest, TestCase, DefaultDrySiteTestCase,
    WikibaseTestCase, ScriptMainTestCase,
)
from tests.bot_tests import TWNBotTestCase
from tests.utils import empty_sites

if StdNumValidationError:
    AnyIsbnValidationException = (StdNumValidationError, IsbnExc)
else:
    AnyIsbnValidationException = IsbnExc


class TestCosmeticChangesISBN(DefaultDrySiteTestCase):

    """Test CosmeticChanges ISBN fix."""

    def test_valid_isbn(self):
        """Test ISBN."""
        cc = CosmeticChangesToolkit(self.site, namespace=0)

        text = cc.fix_ISBN(' ISBN 097522980x ')
        self.assertEqual(text, ' ISBN 0-9752298-0-X ')

        text = cc.fix_ISBN(' ISBN 9780975229804 ')
        self.assertEqual(text, ' ISBN 978-0-9752298-0-4 ')

        text = cc.fix_ISBN(' ISBN 9783955390631 ')
        self.assertEqual(text, ' ISBN 978-3-95539-063-1 ')

        text = cc.fix_ISBN(' ISBN 9791091447034 ')
        self.assertEqual(text, ' ISBN 979-10-91447-03-4 ')

    def test_invalid_isbn(self):
        """Test that it'll fail when the ISBN is invalid."""
        cc = CosmeticChangesToolkit(self.site, namespace=0)

        # Invalid characters
        self.assertRaises(AnyIsbnValidationException,
                          cc.fix_ISBN, 'ISBN 0975229LOL')
        # Invalid checksum
        self.assertRaises(AnyIsbnValidationException,
                          cc.fix_ISBN, 'ISBN 0975229801')
        # Invalid length
        self.assertRaises(AnyIsbnValidationException,
                          cc.fix_ISBN, 'ISBN 09752298')
        # X in the middle
        self.assertRaises(AnyIsbnValidationException,
                          cc.fix_ISBN, 'ISBN 09752X9801')

    def test_ignore_invalid_isbn(self):
        """Test fixing ISBN numbers with an invalid ISBN."""
        cc = CosmeticChangesToolkit(self.site, namespace=0,
                                    ignore=CANCEL_MATCH)

        text = cc.fix_ISBN(' ISBN 0975229LOL ISBN 9780975229804 ')
        self.assertEqual(text, ' ISBN 0975229LOL ISBN 978-0-9752298-0-4 ')


class TestIsbn(TestCase):

    """Test ISBN-related classes and helper functions."""

    net = False

    def test_general(self):
        """Test things that apply both to ISBN10 and ISBN13."""
        # hyphenateIsbnNumbers
        self.assertEqual(hyphenateIsbnNumbers('ISBN 097522980x'),
                         'ISBN 0-9752298-0-X')
        self.assertEqual(hyphenateIsbnNumbers('ISBN 0975229801'),
                         'ISBN 0975229801')  # Invalid ISBN - no changes

        # convertIsbn10toIsbn13
        self.assertEqual(convertIsbn10toIsbn13('ISBN 0-9752298-0-X'),
                         'ISBN 978-0-9752298-0-4')
        self.assertEqual(convertIsbn10toIsbn13('ISBN 0-9752298-0-1'),
                         'ISBN 0-9752298-0-1')  # Invalid ISBN - no changes
        # Should not fail for ISBN13
        self.assertEqual(
            convertIsbn10toIsbn13('ISBN 978-0-7869-3669-4'),
            'ISBN 978-0-7869-3669-4'
        )

    @unittest.expectedFailure  # T144288
    def test_general_failing(self):
        """Test things that apply both to ISBN10 and ISBN13.

        This test fails due to outdated libraries.
        """
        # hyphenateIsbnNumbers
        self.assertEqual(hyphenateIsbnNumbers('ISBN 9791091447089'),
                         'ISBN 979-10-91447-08-9')
        # convertIsbn10toIsbn13
        self.assertEqual(convertIsbn10toIsbn13('ISBN 10-91447-08-X'),
                         'ISBN 979-10-91447-08-9')


class TestIsbnBot(ScriptMainTestCase):

    """Test isbnbot with non-write patching (if the testpage exists)."""

    family = 'wikipedia'
    code = 'test'

    user = True
    write = True

    def setUp(self):
        """Patch the Bot class to avoid an actual write."""
        self._original_userPut = Bot.userPut
        Bot.userPut = userPut_dummy
        super(TestIsbnBot, self).setUp()

    def tearDown(self):
        """Unpatch the Bot class."""
        Bot.userPut = self._original_userPut
        super(TestIsbnBot, self).tearDown()

    def test_isbn(self):
        """Test the ISBN bot."""
        site = self.get_site()
        p1 = pywikibot.Page(site, 'User:M4tx/IsbnTest')
        # Create the page if it does not exist
        if not p1.exists() or p1.text != 'ISBN 097522980x':
            p1.text = 'ISBN 097522980x'
            p1.save('unit test', botflag=True)
        main('-page:User:M4tx/IsbnTest', '-always', '-format', '-to13')
        self.assertEqual(self.newtext, 'ISBN 978-0-9752298-0-4')


def userPut_dummy(self, page, oldtext, newtext, **kwargs):
    """Avoid that userPut writes."""
    TestIsbnBot.newtext = newtext


class TestIsbnWikibaseBot(ScriptMainTestCase, WikibaseTestCase,
                          TWNBotTestCase):

    """Test isbnbot on Wikibase site with non-write patching."""

    family = 'wikidata'
    code = 'test'

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        super(TestIsbnWikibaseBot, cls).setUpClass()

        # Check if the unit test item page and the property both exist
        item_ns = cls.get_repo().item_namespace
        for page in cls.get_site().search('IsbnWikibaseBotUnitTest',
                                          total=1, namespaces=item_ns):
            cls.test_page_qid = page.title()
            item_page = ItemPage(cls.get_repo(), page.title())
            for pid, claims in item_page.get()['claims'].items():
                for claim in claims:
                    prop_page = pywikibot.PropertyPage(cls.get_repo(),
                                                       claim.getID())
                    prop_page.get()
                    if ('ISBN-10' in prop_page.labels.values()
                            and claim.getTarget() == '097522980x'):
                        return
            raise unittest.SkipTest(
                '{}: "ISBN-10" property was not found in '
                '"IsbnWikibaseBotUnitTest" item page'.format(cls.__name__))
        raise unittest.SkipTest(
            '{}: "IsbnWikibaseBotUnitTest" item page was not found'
            .format(cls.__name__))

    def setUp(self):
        """Patch Claim.setTarget and ItemPage.editEntity which write."""
        TestIsbnWikibaseBot._original_setTarget = Claim.setTarget
        Claim.setTarget = setTarget_dummy
        TestIsbnWikibaseBot._original_editEntity = ItemPage.editEntity
        ItemPage.editEntity = editEntity_dummy
        super(TestIsbnWikibaseBot, self).setUp()

    def tearDown(self):
        """Unpatch the dummy methods."""
        Claim.setTarget = TestIsbnWikibaseBot._original_setTarget
        ItemPage.editEntity = TestIsbnWikibaseBot._original_editEntity
        super(TestIsbnWikibaseBot, self).tearDown()

    def test_isbn_format(self):
        """Test format using the bot and wikibase."""
        with empty_sites():
            main('-page:' + self.test_page_qid, '-always', '-format')
            self.assertEqual(self.setTarget_value, '0-9752298-0-X')

    def test_isbn_to13(self):
        """Test to13 using the bot and wikibase."""
        with empty_sites():
            main('-page:' + self.test_page_qid, '-always', '-to13')
            self.assertTrue(self.setTarget_value, '978-0975229804')


def setTarget_dummy(self, value):
    """Avoid that setTarget writes."""
    TestIsbnWikibaseBot.setTarget_value = value
    TestIsbnWikibaseBot._original_setTarget(self, value)


def editEntity_dummy(self, data=None, **kwargs):
    """Avoid that editEntity writes."""
    pass


def setUpModule():  # noqa: N802
    """Skip tests if isbn libraries are missing."""
    if not (has_module('stdnum', version='1.13')
            or has_module('isbnlib', version='3.9.10')):
        raise unittest.SkipTest('neither python-stdlib nor isbnlib available.')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
