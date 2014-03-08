#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script creates new items on Wikidata based on certain criteria.
* When was the (Wikipedia) page created?
* When was the last edit on the page?
* Does the page contain interwiki's?

"""
#
# (C) Multichill, 2014
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import json
import pywikibot
from pywikibot import pagegenerators
from datetime import datetime
from datetime import timedelta


class NewItemRobot:
    """
    A bot to create new items
    """
    def __init__(self, generator, pageAge, lastEdit):
        """
        Arguments:
            * generator    - A generator that yields Page objects.
            * pageAge      - The minimum number of days that has passed since the page was created
            * lastEdit     - The minimum number of days that has passed since the page was last edited

        """
        self.generator = pagegenerators.PreloadingGenerator(generator)
        self.repo = pywikibot.Site().data_repository()
        self.pageAge = pageAge
        self.pageAgeBefore = self.repo.getcurrenttime() - timedelta(days=self.pageAge)
        self.lastEdit = lastEdit
        self.lastEditBefore = self.repo.getcurrenttime() - timedelta(days=self.lastEdit)

    def run(self):
        """
        Starts the robot.
        """
        pywikibot.output('Page age is set to %s days so only pages created before %s will be considered.' % (self.pageAge, self.pageAgeBefore.isoformat()))
        pywikibot.output('Last edit is set to %s days so only pages last edited before %s will be considered.' % (self.lastEdit, self.lastEditBefore.isoformat()))

        for page in self.generator:
            pywikibot.output('Processing %s' % page)
            item = pywikibot.ItemPage.fromPage(page)
            if item.exists():
                pywikibot.output('%s already has an item: %s. Doing a null edit on the page.' % (page, item))
                page.put(page.get())
            elif page.isRedirectPage():
                pywikibot.output('%s is a redirect page. Skipping.' % page)
            elif page.editTime() > self.lastEditBefore:
                pywikibot.output('Last edit on %s was on %s. Too recent. Skipping.' % (page, page.editTime().isoformat()))
            else:
                (revId, revTimestamp, revUser, revComment) = page.getVersionHistory(reverseOrder=True, total=1)[0]
                if revTimestamp > self.pageAgeBefore:
                    pywikibot.output('Page creation of %s on %s is too recent. Skipping.' % (page, page.editTime().isoformat()))
                elif page.langlinks():
                    # FIXME: Implement this
                    pywikibot.output('Found language links (interwiki links). Haven\'t implemented that yet so skipping.')
                else:
                    # FIXME: i18n
                    summary = u'Bot: New item with sitelink from %s' % (page.title(asLink=True, insite=self.repo), )

                    data = {'sitelinks':
                            {item.getdbName(page.site):
                             {'site': item.getdbName(page.site),
                              'title': page.title()}
                             },
                            'labels':
                            {page.site.lang:
                             {'language': page.site.lang,
                              'value': page.title()}
                             }
                            }
                    pywikibot.output(summary)
                    item.editEntity(data, summary=summary)
                    # And do a null edit to force update
                    page.put(page.get())


def main():
    pageAge = 21
    lastEdit = 7

    gen = pagegenerators.GeneratorFactory()

    for arg in pywikibot.handleArgs():
        if arg.startswith('-pageage:'):
            pageAge = int(arg[9:])
        elif arg.startswith('-lastedit:'):
            lastEdit = int(arg[10:])
        if gen.handleArg(arg):
            continue

    generator = gen.getCombinedGenerator()
    if not generator:
        # FIXME: Should throw some help
        return

    bot = NewItemRobot(generator, pageAge, lastEdit)
    bot.run()

if __name__ == "__main__":
    main()
