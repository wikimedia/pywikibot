#!/usr/bin/env python3
"""
Script to handle interwiki links based on Wikibase.

This script connects pages to Wikibase items using language links on the page.
If multiple language links are present, and they are connected to different
items, the bot skips. After connecting the page to an item, language links
can be removed from the page.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-always           If used, the bot won't ask if it should add the specified
                  text

-clean            Clean pages.

-create           Create items.

-merge            Merge items.

-summary:         Use your own edit summary for cleaning the page.

.. note:: This script is a
   :py:obj:`ConfigParserBot <bot.ConfigParserBot>`. All options
   can be set within a settings file which is scripts.ini by default.
"""

# (C) Pywikibot team, 2015-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import pywikibot
import pywikibot.i18n
import pywikibot.textlib
from pywikibot import info, pagegenerators, warning
from pywikibot.bot import ConfigParserBot, ExistingPageBot, SingleSiteBot
from pywikibot.exceptions import APIError, NoPageError


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

# Allowed namespaces. main, project, template, category
NAMESPACES = (0, 4, 10, 14)

# TODO: Some templates on pages, like csd, inuse and afd templates,
# should cause the bot to skip the page, see T134497


class IWBot(ConfigParserBot, ExistingPageBot, SingleSiteBot):

    """The bot for interwiki.

    .. versionchanged:: 7.0
       IWBot is a ConfigParserBot
    """

    update_options = {
        'clean': False,
        'create': False,
        'merge': False,
        'summary': '',
        'ignore_ns': False,  # used by interwikidata_tests only
    }

    def __init__(self, **kwargs) -> None:
        """Initialize the bot."""
        super().__init__(**kwargs)
        if not self.site.has_data_repository:
            raise ValueError(
                f'{self.site} does not have a data repository, use '
                'interwiki.py instead.')

        self.repo = self.site.data_repository()
        if not self.opt.summary:
            self.opt.summary = pywikibot.i18n.twtranslate(
                self.site, 'interwikidata-clean-summary')

    def treat_page(self) -> None:
        """Check page."""
        page = self.current_page
        if (page.namespace() not in NAMESPACES and not self.opt.ignore_ns):
            info(f'{page} is not in allowed namespaces, skipping')
            return

        self.iwlangs = pywikibot.textlib.getLanguageLinks(
            page.text, insite=page.site)
        if not self.iwlangs:
            info(f'No interlanguagelinks on {page}')
            return

        try:
            item = pywikibot.ItemPage.fromPage(page)
        except NoPageError:
            item = None

        if item is None:
            item = self.try_to_add()
            if self.opt.create and item is None:
                item = self.create_item()
        else:
            if self.opt.merge:
                item = self.try_to_merge(item)

        if item and self.opt.clean:
            self.current_item = item
            self.clean_page()

    def create_item(self) -> pywikibot.ItemPage:
        """Create item in repo for current_page."""
        data = {
            'sitelinks': {
                self.site.dbName(): {
                    'site': self.site.dbName(),
                    'title': self.current_page.title()
                }
            },
            'labels': {
                self.site.lang: {
                    'language': self.site.lang,
                    'value': self.current_page.title()
                }
            }
        }
        for site, page in self.iwlangs.items():
            if not page.exists():
                continue
            dbname = site.dbName()
            title = page.title()
            data['sitelinks'][dbname] = {'site': dbname, 'title': title}
            data['labels'][site.lang] = {'language': site.lang, 'value': title}
        summary = ('Bot: New item with sitelink(s) from '
                   + self.current_page.title(as_link=True, insite=self.repo))

        item = pywikibot.ItemPage(self.repo)
        item.editEntity(data, new='item', summary=summary)
        info(f'Created item {item.getID()}')
        return item

    def handle_complicated(self) -> bool:
        """
        Handle pages when they have interwiki conflict.

        When this method returns True it means conflict has resolved
        and it's okay to clean old interwiki links.
        This method should change self.current_item and fix conflicts.
        Change it in subclasses.
        """
        return False

    def clean_page(self) -> None:
        """Clean interwiki links from the page."""
        if not self.iwlangs:
            return

        dbnames = [iw_site.dbName() for iw_site in self.iwlangs]
        if set(dbnames) - set(self.current_item.sitelinks.keys()) \
           and not self.handle_complicated():
            warning('Interwiki conflict in '
                    f'{self.current_page.title(as_link=True)}, skipping...')
            return

        info('Cleaning up the page')
        new_text = pywikibot.textlib.removeLanguageLinks(
            self.current_page.text, site=self.current_page.site)
        self.put_current(new_text, summary=self.opt.summary)

    def get_items(self) -> set[pywikibot.ItemPage]:
        """Return all items of pages linked through the interwiki."""
        wd_data = set()
        for iw_page in self.iwlangs.values():
            if not iw_page.exists():
                warning(f'Interwiki {iw_page.title(as_link=True)} does not'
                        ' exist, skipping...')
                continue
            try:
                wd_data.add(pywikibot.ItemPage.fromPage(iw_page))
            except NoPageError:
                info(f'Interwiki {iw_page} does not have an item')
        return wd_data

    def try_to_add(self) -> pywikibot.ItemPage | bool | None:
        """Add current page in repo."""
        wd_data = self.get_items()
        if not wd_data:
            # will create a new item with interwiki
            return None

        if len(wd_data) > 1:
            warning('Interwiki conflict in '
                    f'{self.current_page.title(as_link=True)}, skipping...')
            return False

        item = list(wd_data).pop()
        if self.current_page.site.dbName() in item.sitelinks:
            warning(f'Interwiki conflict in {item}, skipping...')
            return False

        info('Adding link to ' + item.title())
        item.setSitelink(self.current_page, summary='Added ' + (
            self.current_page.title(as_link=True, insite=item.site)))
        return item

    def try_to_merge(self, item) -> pywikibot.ItemPage | bool | None:
        """Merge two items."""
        wd_data = self.get_items()
        if not wd_data:
            # todo: add links to item
            return None

        if len(wd_data) > 1:
            warning(f'Interwiki conflict in {self.current_page}, skipping...')
            return False

        target_item = list(wd_data).pop()
        try:
            item.mergeInto(target_item)
        except APIError:
            # warning already printed by the API
            return False

        target_item.get(force=True)
        return target_item


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = gen_factory.handle_args(local_args)

    options = {}
    for arg in local_args:
        option, _, value = arg.partition(':')
        if option.startswith('-'):
            option = option[1:]
        else:
            continue

        if option == 'summary':
            options[option] = value
        else:
            options[option] = True

    site = pywikibot.Site()

    generator = gen_factory.getCombinedGenerator(preload=True)
    bot = IWBot(generator=generator, site=site, **options)
    bot.run()


if __name__ == '__main__':
    main()
