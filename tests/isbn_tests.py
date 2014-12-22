# -*- coding: utf-8  -*-
"""Tests for isbn script."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
import pywikibot

__version__ = '$Id$'

from scripts.isbn import ISBN10, ISBN13, InvalidIsbnException as IsbnExc, \
    getIsbn, hyphenateIsbnNumbers, convertIsbn10toIsbn13, main
from tests.aspects import TestCase, unittest
from pywikibot import Bot


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

        # Errors
        isbn = ISBN10('9492098059')
        self.assertRaisesRegex(IsbnExc,
                               'ISBN 9492098059: group number unknown.',
                               isbn.format)
        isbn = ISBN10('9095012042')
        self.assertRaisesRegex(IsbnExc,
                               'ISBN 9095012042: publisher number unknown.',
                               isbn.format)


class TestIsbnBot(TestCase):

    """Test isbnbot with non-write patching (if the testpage exists)."""

    family = 'test'
    code = 'test'

    user = True
    write = True

    def setUp(self):
        self._original_userPut = Bot.userPut
        Bot.userPut = userPut_dummy
        super(TestIsbnBot, self).setUp()

    def tearDown(self):
        Bot.userPut = self._original_userPut
        super(TestIsbnBot, self).tearDown()

    def test_isbn(self):
        site = self.get_site()
        p1 = pywikibot.Page(site, 'User:M4tx/IsbnTest')
        # Create the page if it does not exist
        if not p1.exists() or p1.text != 'ISBN 097522980x':
            p1.text = 'ISBN 097522980x'
            p1.save('unit test', botflag=True)
        main('-page:User:M4tx/IsbnTest', '-always', '-format', '-to13')
        self.assertEqual(self.newtext, 'ISBN 978-0-9752298-0-4')


def userPut_dummy(self, page, oldtext, newtext, **kwargs):
    TestIsbnBot.newtext = newtext


if __name__ == "__main__":
    unittest.main()
