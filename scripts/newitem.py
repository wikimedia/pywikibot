#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script creates new items on Wikidata based on certain criteria.

* When was the (Wikipedia) page created?
* When was the last edit on the page?
* Does the page contain interwikis?

This script understands various command-line arguments:

-lastedit         The minimum number of days that has passed since the page was
                  last edited.

-pageage          The minimum number of days that has passed since the page was
                  created.

-touch            Do a null edit on every page which has a wikibase item.
                  Be careful, this option can trigger edit rates or captchas
                  if your account is not autoconfirmed.

"""
#
# (C) Multichill, 2014
# (C) Pywikibot team, 2014-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from datetime import timedelta
from textwrap import fill

import pywikibot
from pywikibot import pagegenerators, WikidataBot
from pywikibot.exceptions import (LockedPage, NoCreateError, NoPage,
                                  PageNotSaved)


class NewItemRobot(WikidataBot):

    """A bot to create new items."""

    treat_missing_item = True

    def __init__(self, generator, **kwargs):
        """Only accepts options defined in availableOptions."""
        self.availableOptions.update({
            'always': True,
            'lastedit': 7,
            'pageage': 21,
            'touch': 'newly',  # Can be False, newly (pages linked to newly
                               # created items) or True (touch all pages)
        })

        super(NewItemRobot, self).__init__(**kwargs)
        self.generator = generator
        self.pageAge = self.getOption('pageage')
        self.lastEdit = self.getOption('lastedit')
        self.pageAgeBefore = self.repo.getcurrenttime() - timedelta(
            days=self.pageAge)
        self.lastEditBefore = self.repo.getcurrenttime() - timedelta(
            days=self.lastEdit)
        pywikibot.output('Page age is set to {0} days so only pages created'
                         '\nbefore {1} will be considered.'
                         .format(self.pageAge, self.pageAgeBefore.isoformat()))
        pywikibot.output(
            'Last edit is set to {0} days so only pages last edited'
            '\nbefore {1} will be considered.'.format(
                self.lastEdit, self.lastEditBefore.isoformat()))

    @staticmethod
    def _touch_page(page):
        try:
            pywikibot.output('Doing a null edit on the page.')
            page.touch()
        except (NoCreateError, NoPage):
            pywikibot.error('Page {0} does not exist.'.format(
                page.title(as_link=True)))
        except LockedPage:
            pywikibot.error('Page {0} is locked.'.format(
                page.title(as_link=True)))
        except PageNotSaved:
            pywikibot.error('Page {0} not saved.'.format(
                page.title(as_link=True)))

    def _callback(self, page, exc):
        if exc is None and self.getOption('touch'):
            self._touch_page(page)

    def treat_page_and_item(self, page, item):
        """Treat page/item."""
        if item and item.exists():
            pywikibot.output('{0} already has an item: {1}.'
                             .format(page, item))
            if self.getOption('touch') is True:
                self._touch_page(page)
            return

        if page.isRedirectPage():
            pywikibot.output('{0} is a redirect page. Skipping.'.format(page))
            return
        if page.editTime() > self.lastEditBefore:
            pywikibot.output(
                'Last edit on {0} was on {1}.\nToo recent. Skipping.'
                .format(page, page.editTime().isoformat()))
            return

        if page.oldest_revision.timestamp > self.pageAgeBefore:
            pywikibot.output(
                'Page creation of {0} on {1} is too recent. Skipping.'
                .format(page, page.editTime().isoformat()))
            return
        if page.isCategoryRedirect():
            pywikibot.output('{0} is a category redirect. Skipping.'
                             .format(page))
            return

        if page.langlinks():
            # FIXME: Implement this
            pywikibot.output(
                'Found language links (interwiki links).\n'
                "Haven't implemented that yet so skipping.")
            return

        self.create_item_for_page(
            page, callback=lambda _, exc: self._callback(page, exc))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pagegenerators.GeneratorFactory()

    options = {}
    for arg in local_args:
        if arg.startswith(('-pageage:', '-lastedit:')):
            key, val = arg.split(':', 1)
            options[key[1:]] = int(val)
        elif gen.handleArg(arg):
            pass
        else:
            options[arg[1:].lower()] = True

    generator = gen.getCombinedGenerator(preload=True)
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return

    bot = NewItemRobot(generator, **options)
    user = pywikibot.User(bot.site, bot.site.username())
    if bot.getOption('touch') == 'newly' \
            and 'autoconfirmed' not in user.groups():
        pywikibot.warning(fill(
            'You are logged in as {}, an account that is '
            'not in the autoconfirmed group on {}. Script '
            'will not touch pages linked to newly created '
            'items to avoid triggering edit rates or '
            'captchas. Use -touch param to force this.'
            .format(user.username, bot.site.sitename)))
        bot.options['touch'] = False
    bot.run()


if __name__ == '__main__':
    main()
