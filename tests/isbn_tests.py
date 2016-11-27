# -*- coding: utf-8 -*-
"""Tests for isbn script."""
#
# (C) Pywikibot team, 2014-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot

__version__ = '$Id$'

try:
    from stdnum.exceptions import ValidationError as StdNumValidationError
except ImportError:
    StdNumValidationError = None

from pywikibot import Bot, Claim, ItemPage
from pywikibot.cosmetic_changes import CosmeticChangesToolkit, CANCEL_MATCH

from scripts.isbn import (
    ISBN10, ISBN13, InvalidIsbnException as IsbnExc,
    getIsbn, hyphenateIsbnNumbers, convertIsbn10toIsbn13,
    main
)

from tests.aspects import (
    unittest, TestCase, DefaultDrySiteTestCase,
    WikibaseTestCase, ScriptMainTestCase,
)
from tests.bot_tests import TWNBotTestCase

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
        cc = CosmeticChangesToolkit(self.site, namespace=0, ignore=CANCEL_MATCH)

        text = cc.fix_ISBN(' ISBN 0975229LOL ISBN 9780975229804 ')
        self.assertEqual(text, ' ISBN 0975229LOL ISBN 978-0-9752298-0-4 ')


class TestIsbn(TestCase):

    """Test ISBN-related classes and helper functions."""

    net = False

    def test_isbn10(self):
        """Test ISBN10."""
        # Test general features
        isbn = ISBN10('097522980x')
        isbn.format()
        self.assertEqual(isbn.code, '0-9752298-0-X')
        self.assertEqual(isbn.digits(),
                         ['0', '9', '7', '5', '2', '2', '9', '8', '0', 'X'])

        # Converting to ISBN13
        isbn13 = isbn.toISBN13()
        self.assertEqual(isbn13.code, '978-0-9752298-0-4')

        # Errors
        self.assertRaises(IsbnExc, ISBN10, '0975229LOL')  # Invalid characters
        self.assertRaises(IsbnExc, ISBN10, '0975229801')  # Invalid checksum
        self.assertRaises(IsbnExc, ISBN10, '09752298')  # Invalid length
        self.assertRaises(IsbnExc, ISBN10, '09752X9801')  # X in the middle

    def test_isbn13(self):
        """Test ISBN13."""
        # Test general features
        isbn = ISBN13('9783161484100')
        isbn.format()
        self.assertEqual(isbn.code, '978-3-16-148410-0')
        self.assertEqual(isbn.digits(),
                         [9, 7, 8, 3, 1, 6, 1, 4, 8, 4, 1, 0, 0])
        isbn = ISBN13('978809027341', checksumMissing=True)
        self.assertEqual(isbn.code, '9788090273412')

        # Errors
        self.assertRaises(IsbnExc, ISBN13, '9783161484LOL')  # Invalid chars
        self.assertRaises(IsbnExc, ISBN13, '9783161484105')  # Invalid checksum
        self.assertRaises(IsbnExc, ISBN13, '9783161484')  # Invalid length

    def test_general(self):
        """Test things that apply both to ISBN10 and ISBN13."""
        # getIsbn
        self.assertIsInstance(getIsbn('097522980x'), ISBN10)
        self.assertIsInstance(getIsbn('9783161484100'), ISBN13)
        self.assertRaisesRegex(IsbnExc,
                               'ISBN-13: The ISBN 097522 is not 13 digits '
                               'long. / ISBN-10: The ISBN 097522 is not 10 '
                               'digits long.', getIsbn, '097522')

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

        # Errors
        isbn = ISBN10('9492098059')
        self.assertRaisesRegex(IsbnExc,
                               'ISBN 9492098059: group number unknown.',
                               isbn.format)
        isbn = ISBN10('9095012042')
        self.assertRaisesRegex(IsbnExc,
                               'ISBN 9095012042: publisher number unknown.',
                               isbn.format)


class TestIsbnBot(ScriptMainTestCase):

    """Test isbnbot with non-write patching (if the testpage exists)."""

    family = 'test'
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


class TestIsbnWikibaseBot(ScriptMainTestCase, WikibaseTestCase, TWNBotTestCase):

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
                    if ('ISBN-10' in prop_page.labels.values() and
                            claim.getTarget() == '097522980x'):
                        return
            raise unittest.SkipTest(
                u'%s: "ISBN-10" property was not found in '
                u'"IsbnWikibaseBotUnitTest" item page' % cls.__name__)
        raise unittest.SkipTest(
            u'%s: "IsbnWikibaseBotUnitTest" item page was not found'
            % cls.__name__)

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

    def test_isbn(self):
        """Test using the bot and wikibase."""
        main('-page:' + self.test_page_qid, '-always', '-format')
        self.assertEqual(self.setTarget_value, '0-9752298-0-X')
        main('-page:' + self.test_page_qid, '-always', '-to13')
        self.assertTrue(self.setTarget_value, '978-0975229804')


def setTarget_dummy(self, value):
    """Avoid that setTarget writes."""
    TestIsbnWikibaseBot.setTarget_value = value
    TestIsbnWikibaseBot._original_setTarget(self, value)


def editEntity_dummy(self, data=None, **kwargs):
    """Avoid that editEntity writes."""
    pass

if __name__ == '__main__':  # pragma: no cover
    unittest.main()
