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
__version__ = '$Id$'
#

import pywikibot
from pywikibot import pagegenerators
from datetime import timedelta


class NewItemRobot(pywikibot.Bot):
    """ A bot to create new items """

    def __init__(self, generator, **kwargs):
        """Only accepts options defined in availableOptions."""
        self.availableOptions.update({
            'lastedit': 7,
            'pageage': 21,
            'touch': False,
        })

        super(NewItemRobot, self).__init__(**kwargs)
        self.generator = pagegenerators.PreloadingGenerator(generator)
        self.repo = pywikibot.Site().data_repository()
        self.pageAge = self.getOption('pageage')
        self.lastEdit = self.getOption('lastedit')
        self.pageAgeBefore = self.repo.getcurrenttime() - timedelta(days=self.pageAge)
        self.lastEditBefore = self.repo.getcurrenttime() - timedelta(days=self.lastEdit)

    def run(self):
        """ Start the bot. """
        pywikibot.output('Page age is set to %s days so only pages created'
                         '\nbefore %s will be considered.'
                         % (self.pageAge, self.pageAgeBefore.isoformat()))
        pywikibot.output('Last edit is set to %s days so only pages last edited'
                         '\nbefore %s will be considered.'
                         % (self.lastEdit, self.lastEditBefore.isoformat()))

        for page in self.generator:
            pywikibot.output('Processing %s' % page)
            if not page.exists():
                pywikibot.output(u'%s does not exist anymore. Skipping...'
                                 % page)
                continue
            item = pywikibot.ItemPage.fromPage(page)
            if item.exists():
                pywikibot.output(u'%s already has an item: %s.' % (page, item))
                if self.getOption('touch'):
                    pywikibot.output(u'Doing a null edit on the page.')
                    page.put(page.text)
            elif page.isRedirectPage():
                pywikibot.output(u'%s is a redirect page. Skipping.' % page)
            elif page.editTime() > self.lastEditBefore:
                pywikibot.output(
                    u'Last edit on %s was on %s.\nToo recent. Skipping.'
                    % (page, page.editTime().isoformat()))
            else:
                (revId, revTimestamp, revUser,
                 revComment) = page.getVersionHistory(reverseOrder=True,
                                                      total=1)[0]
                if revTimestamp > self.pageAgeBefore:
                    pywikibot.output(
                        u'Page creation of %s on %s is too recent. Skipping.'
                        % (page, page.editTime().isoformat()))
                elif page.langlinks():
                    # FIXME: Implement this
                    pywikibot.output(
                        "Found language links (interwiki links).\n"
                        "Haven't implemented that yet so skipping.")
                else:
                    # FIXME: i18n
                    summary = (u'Bot: New item with sitelink from %s'
                               % page.title(asLink=True, insite=self.repo))

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
                    page.put(page.text)


def main():
    # Process global args and prepare generator args parser
    local_args = pywikibot.handleArgs()
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
