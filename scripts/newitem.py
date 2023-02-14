#!/usr/bin/env python3
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

-touch            Do a null edit on every page which has a Wikibase item.
                  Be careful, this option can trigger edit rates or captchas
                  if your account is not autoconfirmed.

"""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
from datetime import timedelta
from textwrap import fill

import pywikibot
from pywikibot import pagegenerators
from pywikibot.backports import Set
from pywikibot.bot import WikidataBot
from pywikibot.exceptions import (
    LockedPageError,
    NoCreateError,
    NoPageError,
    PageSaveRelatedError,
)


DELETION_TEMPLATES = ('Q4847311', 'Q6687153', 'Q21528265')


class NewItemRobot(WikidataBot):

    """A bot to create new items."""

    use_redirect = False
    treat_missing_item = True
    update_options = {
        'always': True,
        'lastedit': 7,
        'pageage': 21,
        'touch': 'newly',  # Can be False, newly (pages linked to newly
                           # created items) or True (touch all pages)
    }

    def __init__(self, **kwargs) -> None:
        """Only accepts options defined in available_options."""
        super().__init__(**kwargs)
        self._skipping_templates = {}

    def setup(self) -> None:
        """Setup ages."""
        super().setup()

        self.pageAgeBefore = self.repo.server_time() - timedelta(
            days=self.opt.pageage)
        self.lastEditBefore = self.repo.server_time() - timedelta(
            days=self.opt.lastedit)
        pywikibot.info('Page age is set to {} days so only pages created'
                       '\nbefore {} will be considered.\n'
                       .format(self.opt.pageage,
                               self.pageAgeBefore.isoformat()))
        pywikibot.info(
            'Last edit is set to {} days so only pages last edited'
            '\nbefore {} will be considered.\n'
            .format(self.opt.lastedit, self.lastEditBefore.isoformat()))

    @staticmethod
    def _touch_page(page) -> None:
        try:
            pywikibot.info('Doing a null edit on the page.')
            page.touch()
        except (NoCreateError, NoPageError):
            pywikibot.error('Page {} does not exist.'.format(
                page.title(as_link=True)))
        except LockedPageError:
            pywikibot.error('Page {} is locked.'.format(
                page.title(as_link=True)))
        except PageSaveRelatedError as e:
            pywikibot.error(f'Page {page} not saved:\n{e.args}')

    def _callback(self, page, exc) -> None:
        if exc is None and self.opt.touch:
            self._touch_page(page)

    def get_skipping_templates(self, site) -> Set[pywikibot.Page]:
        """Get templates which leads the page to be skipped.

        If the script is used for multiple sites, hold the skipping templates
        as attribute.
        """
        if site in self._skipping_templates:
            return self._skipping_templates[site]

        skipping_templates = set()
        pywikibot.info(f'Retrieving skipping templates for site {site}...')
        for item in DELETION_TEMPLATES:
            template = site.page_from_repository(item)

            if template is None:
                continue

            skipping_templates.add(template)
            # also add redirect templates
            skipping_templates.update(
                template.getReferences(follow_redirects=False,
                                       with_template_inclusion=False,
                                       filter_redirects=True,
                                       namespaces=site.namespaces.TEMPLATE))
        self._skipping_templates[site] = skipping_templates
        return skipping_templates

    def skip_templates(self, page) -> str:
        """Check whether the page is to be skipped due to skipping template.

        :param page: treated page
        :type page: pywikibot.Page
        :return: the template which leads to skip
        """
        skipping_templates = self.get_skipping_templates(page.site)
        for template, _ in page.templatesWithParams():
            if template in skipping_templates:
                return template.title(with_ns=False)
        return ''

    def skip_page(self, page) -> bool:
        """Skip pages which are unwanted to treat."""
        if super().skip_page(page):
            return True

        if page.latest_revision.timestamp > self.lastEditBefore:
            pywikibot.info(
                f'Last edit on {page} was on {page.latest_revision.timestamp}.'
                f'\nToo recent. Skipping.')
            return True

        if page.oldest_revision.timestamp > self.pageAgeBefore:
            pywikibot.info(
                f'Page creation of {page} on {page.oldest_revision.timestamp} '
                f'is too recent. Skipping.')
            return True

        if page.isCategoryRedirect():
            pywikibot.info(f'{page} is a category redirect. Skipping.')
            return True

        if page.langlinks():
            # FIXME: Implement this
            pywikibot.info(
                f'Found language links (interwiki links) for {page}.\n'
                f"Haven't implemented that yet so skipping.")
            return True

        template = self.skip_templates(page)
        if template:
            pywikibot.info(f'{page} contains {{{{{template}}}}}. Skipping.')
            return True

        return False

    def treat_page_and_item(self, page, item) -> None:
        """Treat page/item."""
        if item and item.exists():
            pywikibot.info(f'{page} already has an item: {item}.')
            if self.opt.touch is True:
                self._touch_page(page)
            return

        self.create_item_for_page(
            page, callback=lambda _, exc: self._callback(page, exc))


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pagegenerators.GeneratorFactory()

    options = {}
    for arg in local_args:
        if arg.startswith(('-pageage:', '-lastedit:')):
            key, val = arg.split(':', 1)
            options[key[1:]] = int(val)
        elif gen.handle_arg(arg):
            pass
        else:
            options[arg[1:].lower()] = True

    generator = gen.getCombinedGenerator(preload=True)
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return

    bot = NewItemRobot(generator=generator, **options)
    if not bot.site.logged_in():
        bot.site.login()
    user = pywikibot.User(bot.site, bot.site.username())
    if bot.opt.touch == 'newly' and 'autoconfirmed' not in user.groups():
        pywikibot.warning(fill(
            f'You are logged in as {user.username}, an account that is not in '
            f'the autoconfirmed group on {bot.site.sitename}. Script will not '
            f'touch pages linked to newly created  items to avoid triggering '
            f'edit rates or captchas. Use -touch param to force this.'))
        bot.opt.touch = False
    bot.run()


if __name__ == '__main__':
    main()
