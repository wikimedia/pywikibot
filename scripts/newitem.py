#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script creates new items on Wikidata based on certain criteria.

* When was the (Wikipedia) page created?
* When was the last edit on the page?
* Does the page contain interwiki's?

This script understands various command-line arguments:

-lastedit         The minimum number of days that has passed since the page was
                  last edited.

-pageage          The minimum number of days that has passed since the page was
                  created.

-touch            Do a null edit on every page which has a wikibase item.

"""
#
# (C) Multichill, 2014
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import pywikibot
from pywikibot import pagegenerators, WikidataBot
from datetime import timedelta


class NewItemRobot(WikidataBot):

    """A bot to create new items."""

    def __init__(self, generator, **kwargs):
        """Only accepts options defined in availableOptions."""
        self.availableOptions.update({
            'lastedit': 7,
            'pageage': 21,
            'touch': False,
        })

        super(NewItemRobot, self).__init__(**kwargs)
        self.generator = pagegenerators.PreloadingGenerator(generator)
        self.pageAge = self.getOption('pageage')
        self.lastEdit = self.getOption('lastedit')
        self.pageAgeBefore = self.repo.getcurrenttime() - timedelta(days=self.pageAge)
        self.lastEditBefore = self.repo.getcurrenttime() - timedelta(days=self.lastEdit)
        self.treat_missing_item = True
        pywikibot.output('Page age is set to %s days so only pages created'
                         '\nbefore %s will be considered.'
                         % (self.pageAge, self.pageAgeBefore.isoformat()))
        pywikibot.output('Last edit is set to %s days so only pages last edited'
                         '\nbefore %s will be considered.'
                         % (self.lastEdit, self.lastEditBefore.isoformat()))

    def treat(self, page, item):
        """Treat page/item."""
        if item and item.exists():
            pywikibot.output(u'%s already has an item: %s.' % (page, item))
            if self.getOption('touch'):
                pywikibot.output(u'Doing a null edit on the page.')
                page.put(page.text)
            return

        self.current_page = page

        if page.isRedirectPage():
            pywikibot.output(u'%s is a redirect page. Skipping.' % page)
            return
        if page.editTime() > self.lastEditBefore:
            pywikibot.output(
                u'Last edit on %s was on %s.\nToo recent. Skipping.'
                % (page, page.editTime().isoformat()))
            return

        if page.oldest_revision.timestamp > self.pageAgeBefore:
            pywikibot.output(
                u'Page creation of %s on %s is too recent. Skipping.'
                % (page, page.editTime().isoformat()))
            return

        if page.langlinks():
            # FIXME: Implement this
            pywikibot.output(
                "Found language links (interwiki links).\n"
                "Haven't implemented that yet so skipping.")
            return

        # FIXME: i18n
        summary = (u'Bot: New item with sitelink from %s'
                   % page.title(asLink=True, insite=self.repo))

        data = {'sitelinks':
                {page.site.dbName():
                 {'site': page.site.dbName(),
                  'title': page.title()}
                 },
                'labels':
                {page.site.lang:
                 {'language': page.site.lang,
                  'value': page.title()}
                 }
                }

        pywikibot.output(summary)

        item = pywikibot.ItemPage(page.site.data_repository())
        item.editEntity(data, summary=summary)
        # And do a null edit to force update
        page.put(page.text)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pagegenerators.GeneratorFactory()

    options = {}
    for arg in local_args:
        if (
                arg.startswith('-pageage:') or
                arg.startswith('-lastedit:')):
            key, val = arg.split(':', 1)
            options[key[1:]] = int(val)
        elif gen.handleArg(arg):
            pass
        else:
            options[arg[1:].lower()] = True

    generator = gen.getCombinedGenerator()
    if not generator:
        pywikibot.showHelp()
        return

    bot = NewItemRobot(generator, **options)
    bot.run()

if __name__ == "__main__":
    main()
