#!/usr/bin/python
"""
This script reports and fixes invalid ISBN numbers.

Additionally, it can convert all ISBN-10 codes to the ISBN-13 format, and
correct the ISBN format by placing hyphens.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-to13             Converts all ISBN-10 codes to ISBN-13.
                  NOTE: This needn't be done, as MediaWiki still supports
                  (and will keep supporting) ISBN-10, and all libraries and
                  bookstores will most likely do so as well.

-format           Corrects the hyphenation.
                  NOTE: This is in here for testing purposes only. Usually
                  it's not worth to create an edit for such a minor issue.
                  The recommended way of doing this is enabling
                  cosmetic_changes, so that these changes are made on-the-fly
                  to all pages that are modified.

-always           Don't prompt you for each replacement.

-prop-isbn-10     Sets ISBN-10 property ID, so it's not tried to be found
                  automatically.
                  The usage is as follows: -prop-isbn-10:propid

-prop-isbn-13     Sets ISBN-13 property ID. The format and purpose is the
                  same as in -prop-isbn-10.

"""
#
# (C) Pywikibot team, 2009-2020
#
# Distributed under the terms of the MIT license.
#
import re
from contextlib import suppress
from functools import partial

import pywikibot
from pywikibot import Bot, WikidataBot, i18n, pagegenerators, textlib
from pywikibot.exceptions import (
    EditConflictError,
    Error,
    IsRedirectPageError,
    LockedPageError,
    NoPageError,
    SpamblacklistError,
)
from pywikibot.tools import has_module


try:
    import stdnum.isbn
except ImportError:
    with suppress(ImportError):
        import isbnlib

docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}


class InvalidIsbnException(Error):

    """Invalid ISBN."""


def is_valid(isbn):
    """Check whether an ISBN 10 or 13 is valid."""
    # isbnlib marks any ISBN10 with lowercase 'X' as invalid
    isbn = isbn.upper()
    try:
        stdnum.isbn
    except NameError:
        pass
    else:
        try:
            stdnum.isbn.validate(isbn)
        except (stdnum.isbn.InvalidFormat,
                stdnum.isbn.InvalidChecksum,
                stdnum.isbn.InvalidLength) as e:
            raise InvalidIsbnException(str(e))
        return True

    try:
        isbnlib
    except NameError:
        pass
    else:
        if isbnlib.notisbn(isbn):
            raise InvalidIsbnException('Invalid ISBN found')
        return True

    raise NotImplementedError(
        'ISBN functionality not available. Install stdnum package.')


def _hyphenateIsbnNumber(match):
    """Helper function to deal with a single ISBN."""
    isbn = match.group('code')
    isbn = isbn.upper()
    try:
        is_valid(isbn)
    except InvalidIsbnException:
        return isbn

    try:
        stdnum.isbn
    except NameError:
        pass
    else:
        return stdnum.isbn.format(isbn)


hyphenateIsbnNumbers = partial(textlib.reformat_ISBNs,
                               match_func=_hyphenateIsbnNumber)


def _isbn10toIsbn13(match):
    """Helper function to deal with a single ISBN."""
    isbn = match.group('code')
    isbn = isbn.upper()
    try:
        is_valid(isbn)
    except InvalidIsbnException:
        # don't change
        return isbn

    try:
        stdnum.isbn
    except NameError:
        pass
    else:
        return stdnum.isbn.to_isbn13(isbn)

    try:
        isbnlib
    except NameError:
        pass
    else:
        # remove hyphenation, otherwise isbnlib.to_isbn13() returns None
        i = isbnlib.canonical(isbn)
        if i == isbn:
            i13 = isbnlib.to_isbn13(i)
            return i13
        # add removed hyphenation
        i13 = isbnlib.to_isbn13(i)
        i13h = hyphenateIsbnNumbers('ISBN ' + i13)
        return i13h[5:]


def convertIsbn10toIsbn13(text):
    """Helper function to convert ISBN 10 to ISBN 13."""
    isbnR = re.compile(r'(?<=ISBN )(?P<code>[\d\-]+[Xx]?)')
    text = isbnR.sub(_isbn10toIsbn13, text)
    return text


class IsbnBot(Bot):

    """ISBN bot."""

    def __init__(self, **kwargs):
        """Initializer."""
        self.available_options.update({
            'to13': False,
            'format': False,
        })
        super().__init__(**kwargs)

        self.isbnR = re.compile(r'(?<=ISBN )(?P<code>[\d\-]+[Xx]?)')
        self.comment = i18n.twtranslate(self.site, 'isbn-formatting')

    def treat(self, page):
        """Treat a page."""
        try:
            old_text = page.get()
            for match in self.isbnR.finditer(old_text):
                isbn = match.group('code')
                try:
                    is_valid(isbn)
                except InvalidIsbnException as e:
                    pywikibot.output(e)

            new_text = old_text
            if self.opt.to13:
                new_text = self.isbnR.sub(_isbn10toIsbn13, new_text)

            if self.opt.format:
                new_text = self.isbnR.sub(_hyphenateIsbnNumber, new_text)
            try:
                self.userPut(page, page.text, new_text, summary=self.comment)
            except EditConflictError:
                pywikibot.output('Skipping {} because of edit conflict'
                                 .format(page.title()))
            except SpamblacklistError as e:
                pywikibot.output(
                    'Cannot change {} because of blacklist entry {1}'
                    .format(page.title(), e.url))
            except LockedPageError:
                pywikibot.output('Skipping {} (locked page)'
                                 .format(page.title()))
        except NoPageError:
            pywikibot.output('Page {} does not exist'
                             .format(page.title(as_link=True)))
        except IsRedirectPageError:
            pywikibot.output('Page {} is a redirect; skipping.'
                             .format(page.title(as_link=True)))


class IsbnWikibaseBot(WikidataBot):

    """ISBN bot to be run on Wikibase sites."""

    use_from_page = None

    def __init__(self, **kwargs):
        """Initializer."""
        self.available_options.update({
            'to13': False,
            'format': False,
        })
        self.isbn_10_prop_id = kwargs.pop('prop-isbn-10', None)
        self.isbn_13_prop_id = kwargs.pop('prop-isbn-13', None)

        super().__init__(**kwargs)

        if self.isbn_10_prop_id is None:
            self.isbn_10_prop_id = self.get_property_by_name('ISBN-10')
        if self.isbn_13_prop_id is None:
            self.isbn_13_prop_id = self.get_property_by_name('ISBN-13')
        self.comment = i18n.twtranslate(self.site, 'isbn-formatting')

    def treat_page_and_item(self, page, item):
        """Treat a page."""
        change_messages = []
        item.get()
        if self.isbn_10_prop_id in item.claims:
            for claim in item.claims[self.isbn_10_prop_id]:
                isbn = claim.getTarget()
                try:
                    is_valid(isbn)
                except InvalidIsbnException as e:
                    pywikibot.output(e)
                    continue

                old_isbn = 'ISBN ' + isbn

                if self.opt.format:
                    new_isbn = hyphenateIsbnNumbers(old_isbn)

                if self.opt.to13:
                    new_isbn = convertIsbn10toIsbn13(old_isbn)

                    item.claims[claim.getID()].remove(claim)
                    claim = pywikibot.Claim(self.repo, self.isbn_13_prop_id)
                    claim.setTarget(new_isbn)
                    if self.isbn_13_prop_id in item.claims:
                        item.claims[self.isbn_13_prop_id].append(claim)
                    else:
                        item.claims[self.isbn_13_prop_id] = [claim]
                    change_messages.append('Changing {} ({}) to {} ({})'
                                           .format(self.isbn_10_prop_id,
                                                   old_isbn,
                                                   self.isbn_13_prop_id,
                                                   new_isbn))
                    continue

                if old_isbn == new_isbn:
                    continue
                # remove 'ISBN ' prefix
                assert new_isbn.startswith('ISBN '), \
                    'ISBN should start with "ISBN"'
                new_isbn = new_isbn[5:]
                claim.setTarget(new_isbn)
                change_messages.append('Changing %s (%s --> %s)' %
                                       (self.isbn_10_prop_id, old_isbn,
                                        new_isbn))

        # -format is the only option that has any effect on ISBN13
        if self.opt.format and self.isbn_13_prop_id in item.claims:
            for claim in item.claims[self.isbn_13_prop_id]:
                isbn = claim.getTarget()
                try:
                    is_valid(isbn)
                except InvalidIsbnException as e:
                    pywikibot.output(e)
                    continue

                old_isbn = 'ISBN ' + isbn
                new_isbn = hyphenateIsbnNumbers(old_isbn)
                if old_isbn == new_isbn:
                    continue
                change_messages.append(
                    'Changing {} ({} --> {})'.format(
                        self.isbn_13_prop_id, claim.getTarget(), new_isbn))
                claim.setTarget(new_isbn)

        if change_messages:
            self.current_page = item
            pywikibot.output('\n'.join(change_messages))
            self.user_edit_entity(item, summary=self.comment)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    options = {}

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    # Check whether we're running on Wikibase site or not
    # FIXME: See T85483 and run() in WikidataBot
    site = pywikibot.Site()
    data_site = site.data_repository()
    use_wikibase = (data_site is not None
                    and data_site.family == site.family
                    and data_site.code == site.code)

    for arg in local_args:
        if arg.startswith('-prop-isbn-10:'):
            options[arg[1:len('-prop-isbn-10')]] = arg[len('-prop-isbn-10:'):]
        elif arg.startswith('-prop-isbn-13:'):
            options[arg[1:len('-prop-isbn-13')]] = arg[len('-prop-isbn-13:'):]
        elif arg.startswith('-') and arg[1:] in ('always', 'to13', 'format'):
            options[arg[1:]] = True
        else:
            genFactory.handle_arg(arg)

    gen = genFactory.getCombinedGenerator(preload=True)

    deps = []
    if not (has_module('stdnum', version='1.13')
            or has_module('isbnlib', version='3.9.10')):
        deps = ["'python-stdnum >= 1.13' or 'isbnlib >= 3.9.10'"]
    if pywikibot.bot.suggest_help(missing_generator=not gen,
                                  missing_dependencies=deps):
        return

    if use_wikibase:
        bot = IsbnWikibaseBot(generator=gen, **options)
    else:
        bot = IsbnBot(generator=gen, **options)
    bot.run()


if __name__ == '__main__':
    main()
