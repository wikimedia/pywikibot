#!/usr/bin/env python3
"""
This script fixes links that contain common spelling mistakes.

This is only possible on wikis that have a template for these misspellings.

Command line options:

   -always:XY  instead of asking the user what to do, always perform the same
               action. For example, XY can be "r0", "u" or "2". Be careful with
               this option, and check the changes made by the bot. Note that
               some choices for XY don't make sense and will result in a loop,
               e.g. "l" or "m".

   -main       only check pages in the main namespace, not in the Talk,
               Project, User, etc. namespaces.

   -start:XY   goes through all misspellings in the category on your wiki
               that is defined (to the bot) as the category containing
               misspelling pages, starting at XY. If the -start argument is not
               given, it starts at the beginning.
"""
#
# (C) Pywikibot team, 2007-2022
#
# Distributed under the terms of the MIT license.
#
from itertools import chain
from typing import Generator

import pywikibot
from pywikibot import i18n, pagegenerators
from scripts.solve_disambiguation import DisambiguationRobot as BaseDisambigBot


HELP_MSG = """\n
misspelling.py does not support site {site}.

Help Pywikibot team to provide support for your wiki by submitting
a bug to:
https://phabricator.wikimedia.org/maniphest/task/edit/form/1/?tags=pywikibot-core
with category containing misspelling pages or a template for
these misspellings.\n"""


class MisspellingRobot(BaseDisambigBot):

    """Spelling bot."""

    misspelling_templates = {
        'wikipedia:de': ('Falschschreibung', 'Obsolete Schreibung'),
    }

    # Optional: if there is a category, one can use the -start parameter
    misspelling_categories = ('Q8644265', 'Q9195708')
    update_options = {'start': None}

    @property
    def generator(self) -> Generator[pywikibot.Page, None, None]:
        """Generator to retrieve misspelling pages or misspelling redirects."""
        templates = self.misspelling_templates.get(self.site.sitename)
        categories = [cat for cat in (self.site.page_from_repository(item)
                                      for item in self.misspelling_categories)
                      if cat is not None]

        if templates:
            pywikibot.info('<<yellow>>Working on templates...')
            if isinstance(templates, str):
                templates = (templates, )

            generators = (
                pywikibot.Page(self.site, template_name, ns=10).getReferences(
                    follow_redirects=False,
                    only_template_inclusion=True)
                for template_name in templates
            )

            if self.opt.start:
                pywikibot.info(
                    '-start parameter is not supported on this wiki\n'
                    'because templates are used for misspellings.')
        elif categories:
            pywikibot.info('<<yellow>>Working on categories...')
            generators = (
                pagegenerators.CategorizedPageGenerator(
                    cat, recurse=True, start=self.opt.start
                )
                for cat in categories
            )

        else:
            pywikibot.info(HELP_MSG.format(site=self.site))
            return

        yield from pagegenerators.PreloadingGenerator(chain(*generators))

    def findAlternatives(self, page) -> bool:
        """
        Append link target to a list of alternative links.

        Overrides the BaseDisambigBot method.

        :return: True if alternate link was appended
        """
        if page.isRedirectPage():
            self.opt.pos.append(page.getRedirectTarget().title())
            return True

        sitename = page.site.sitename
        templates = self.misspelling_templates.get(sitename)
        if templates is None:
            return False

        if isinstance(templates, str):
            templates = (templates, )

        for template, params in page.templatesWithParams():
            if template.title(with_ns=False) in templates:
                # The correct spelling is in the last parameter.
                correct_spelling = params[-1]
                # On de.wikipedia, there are some cases where the
                # misspelling is ambiguous, see for example:
                # https://de.wikipedia.org/wiki/Buthan
                for match in self.linkR.finditer(correct_spelling):
                    self.opt.pos.append(match['title'])

                if not self.opt.pos:
                    # There were no links in the parameter, so there is
                    # only one correct spelling.
                    self.opt.pos.append(correct_spelling)
                return True
        return False

    def setSummaryMessage(self, page, *args, **kwargs) -> None:
        """
        Setup the summary message.

        Overrides the BaseDisambigBot method.
        """
        # TODO: setSummaryMessage() in solve_disambiguation now has parameters
        # new_targets and unlink. Make use of these here.
        self.summary = i18n.twtranslate(self.site, 'misspelling-fixing',
                                        {'page': page.title()})


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    for arg in pywikibot.handle_args(args):
        opt, _, value = arg.partition(':')
        if not opt.startswith('-'):
            continue
        opt = opt[1:]
        if opt == 'always':
            # the option that's always selected when the bot wonders
            # what to do with a link. If it's None, the user is prompted
            # (default behaviour).
            options[opt] = value
        elif opt == 'start':
            options[opt] = value or pywikibot.input(
                'At which page do you want to start?')
        elif opt == 'main':
            options[opt] = True

    bot = MisspellingRobot(**options)
    bot.run()


if __name__ == '__main__':
    main()
