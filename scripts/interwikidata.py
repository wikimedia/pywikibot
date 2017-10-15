#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to handle interwiki links based on Wikibase.

This script connects pages to Wikibase items using language links on the page.
If multiple language links are present, and they are connected to different
items, the bot skips. After connecting the page to an item, language links
can be removed from the page.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-clean            Clean pages.

-create           Create items.

-merge            Merge items.

-summary:         Use your own edit summary for cleaning the page.
"""

# (C) Pywikibot team, 2015-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals, absolute_import

import pywikibot

from pywikibot import pagegenerators, output, warning
from pywikibot.bot import ExistingPageBot, SingleSiteBot, suggest_help

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}

# Allowed namespaces. main, project, template, category
namespaces = [0, 4, 10, 14]

# TODO: Some templates on pages, like csd, inuse and afd templates,
# should cause the bot to skip the page, see T134497


class IWBot(ExistingPageBot, SingleSiteBot):

    """The bot for interwiki."""

    def __init__(self, **kwargs):
        """Construct the bot."""
        self.availableOptions.update({
            'clean': False,
            'create': False,
            'merge': False,
            'summary': None,
            'ignore_ns': False,  # used by interwikidata_tests only
        })
        super(IWBot, self).__init__(**kwargs)
        if not self.site.has_data_repository:
            raise ValueError('{site} does not have a data repository, '
                             'use interwiki.py instead.'.format(
                                 site=self.site))
        self.repo = self.site.data_repository()
        if not self.getOption('summary'):
            self.options['summary'] = pywikibot.i18n.twtranslate(
                self.site, 'interwikidata-clean-summary')

    def treat_page(self):
        """Check page."""
        if (self.current_page.namespace() not in namespaces and
                not self.getOption('ignore_ns')):
            output('{page} is not in allowed namespaces, skipping'
                   .format(page=self.current_page.title(
                       asLink=True)))
            return False
        self.iwlangs = pywikibot.textlib.getLanguageLinks(
            self.current_page.text, insite=self.current_page.site)
        if not self.iwlangs:
            output('No interlanguagelinks on {page}'.format(
                page=self.current_page.title(asLink=True)))
            return False
        try:
            item = pywikibot.ItemPage.fromPage(self.current_page)
        except pywikibot.NoPage:
            item = None

        if item is None:
            item = self.try_to_add()
            if self.getOption('create') and item is None:
                item = self.create_item()
        else:
            if self.getOption('merge'):
                item = self.try_to_merge(item)

        if item and self.getOption('clean'):
            self.current_item = item
            self.clean_page()

    def create_item(self):
        """Create item in repo for current_page."""
        data = {'sitelinks':
                {self.site.dbName():
                 {'site': self.site.dbName(),
                  'title': self.current_page.title()}
                 },
                'labels':
                {self.site.lang:
                 {'language': self.site.lang,
                  'value': self.current_page.title()}
                 }
                }
        for site, page in self.iwlangs.items():
            if not page.exists():
                continue
            dbname = site.dbName()
            title = page.title()
            data['sitelinks'][dbname] = {'site': dbname, 'title': title}
            data['labels'][site.lang] = {'language': site.lang, 'value': title}
        summary = ('Bot: New item with sitelink(s) from %s'
                   % self.current_page.title(asLink=True, insite=self.repo))

        item = pywikibot.ItemPage(self.repo)
        item.editEntity(data, new='item', summary=summary)
        output('Created item {item}'.format(item=item.getID()))
        return item

    def handle_complicated(self):
        """
        Handle pages when they have interwiki conflict.

        When this method returns True it means conflict has resolved
        and it's okay to clean old interwiki links.
        This method should change self.current_item and fix conflicts.
        Change it in subclasses.
        """
        return False

    def clean_page(self):
        """Clean interwiki links from the page."""
        if not self.iwlangs:
            return
        dbnames = [iw_site.dbName() for iw_site in self.iwlangs]
        if set(dbnames) - set(self.current_item.sitelinks.keys()):
            if not self.handle_complicated():
                warning('Interwiki conflict in %s, skipping...' %
                        self.current_page.title(asLink=True))
                return False
        output('Cleaning up the page')
        new_text = pywikibot.textlib.removeLanguageLinks(
            self.current_page.text, site=self.current_page.site)
        self.put_current(new_text, summary=self.getOption('summary'))

    def get_items(self):
        """Return all items of pages linked through the interwiki."""
        wd_data = set()
        for iw_page in self.iwlangs.values():
            if not iw_page.exists():
                warning('Interwiki %s does not exist, skipping...' %
                        iw_page.title(asLink=True))
                continue
            try:
                wd_data.add(pywikibot.ItemPage.fromPage(iw_page))
            except pywikibot.NoPage:
                output('Interwiki %s does not have an item' %
                       iw_page.title(asLink=True))
        return wd_data

    def try_to_add(self):
        """Add current page in repo."""
        wd_data = self.get_items()
        if not wd_data:
            # will create a new item with interwiki
            return None
        if len(wd_data) > 1:
            warning('Interwiki conflict in %s, skipping...' %
                    self.current_page.title(asLink=True))
            return False
        item = list(wd_data).pop()
        if self.current_page.site.dbName() in item.sitelinks:
            warning('Interwiki conflict in %s, skipping...' %
                    item.title(asLink=True))
            return False
        output('Adding link to %s' % item.title())
        item.setSitelink(self.current_page)
        return item

    def try_to_merge(self, item):
        """Merge two items."""
        wd_data = self.get_items()
        if not wd_data:
            # todo: add links to item
            return None
        if len(wd_data) > 1:
            warning('Interwiki conflict in %s, skipping...' %
                    self.current_page.title(asLink=True))
            return False
        target_item = list(wd_data).pop()
        try:
            item.mergeInto(target_item)
        except pywikibot.data.api.APIError:
            # warning already printed by the API
            return False
        else:
            target_item.get(force=True)
            return target_item


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()
    options = {}
    for arg in local_args:
        if genFactory.handleArg(arg):
            continue
        option, sep, value = arg.partition(':')
        option = option[1:] if option.startswith('-') else None
        if option == 'summary':
            options[option] = value
        else:
            options[option] = True

    site = pywikibot.Site()

    generator = genFactory.getCombinedGenerator(preload=True)
    if generator:
        bot = IWBot(generator=generator, site=site, **options)
        bot.run()
    else:
        suggest_help(missing_generator=True)
        return False


if __name__ == '__main__':
    main()
