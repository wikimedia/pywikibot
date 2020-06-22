#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script fixes links that contain common spelling mistakes.

This is only possible on wikis that have a template for these misspellings.

Command line options:

   -always:XY  instead of asking the user what to do, always perform the same
               action. For example, XY can be "r0", "u" or "2". Be careful with
               this option, and check the changes made by the bot. Note that
               some choices for XY don't make sense and will result in a loop,
               e.g. "l" or "m".

   -start:XY   goes through all misspellings in the category on your wiki
               that is defined (to the bot) as the category containing
               misspelling pages, starting at XY. If the -start argument is not
               given, it starts at the beginning.

   -main       only check pages in the main namespace, not in the talk,
               wikipedia, user, etc. namespaces.
"""
# (C) Pywikibot team, 2007-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from itertools import chain

import pywikibot

from pywikibot import i18n, pagegenerators

from pywikibot.tools import UnicodeType

from scripts.solve_disambiguation import DisambiguationRobot

HELP_MSG = """\n
misspelling.py does not support site {site}.

Help Pywikibot team to provide support for your wiki by submitting
a bug to:
https://phabricator.wikimedia.org/maniphest/task/edit/form/1/?tags=pywikibot-core
with category containing misspelling pages or a template for
these misspellings.\n"""


class MisspellingRobot(DisambiguationRobot):

    """Spelling bot."""

    misspellingTemplate = {
        'de': ('Falschschreibung', 'Obsolete Schreibung'),
    }

    # Optional: if there is a category, one can use the -start
    # parameter.
    misspellingCategory = {
        # da: only contains date redirects at the moment
        'da': 'Omdirigeringer af fejlstavninger',
        'de': ('Kategorie:Wikipedia:Falschschreibung',
               'Kategorie:Wikipedia:Obsolete Schreibung'),
        'en': 'Redirects from misspellings',
        'hu': 'Átirányítások hibás névről',
        'nl': 'Categorie:Wikipedia:Redirect voor spelfout',
    }

    def __init__(self, always, firstPageTitle, main_only):
        """Initializer."""
        super(MisspellingRobot, self).__init__(
            always, [], True, False, None, False, main_only)
        self.generator = self.createPageGenerator(firstPageTitle)

    def createPageGenerator(self, firstPageTitle):
        """
        Generator to retrieve misspelling pages or misspelling redirects.

        @rtype: generator
        """
        mycode = self.site.code
        if mycode in self.misspellingCategory:
            categories = self.misspellingCategory[mycode]
            if isinstance(categories, UnicodeType):
                categories = (categories, )
            generators = (
                pagegenerators.CategorizedPageGenerator(
                    pywikibot.Category(self.site, misspellingCategoryTitle),
                    recurse=True, start=firstPageTitle)
                for misspellingCategoryTitle in categories)
        elif mycode in self.misspellingTemplate:
            templates = self.misspellingTemplate[mycode]
            if isinstance(templates, UnicodeType):
                templates = (templates, )
            generators = (
                pagegenerators.ReferringPageGenerator(
                    pywikibot.Page(self.site, misspellingTemplateName, ns=10),
                    onlyTemplateInclusion=True)
                for misspellingTemplateName in templates)
            if firstPageTitle:
                pywikibot.output(
                    '-start parameter unsupported on this wiki because there '
                    'is no category for misspellings.')
        else:
            pywikibot.output(HELP_MSG.format(site=self.site))

            empty_gen = (i for i in [])
            return empty_gen
        generator = chain(*generators)
        preloadingGen = pagegenerators.PreloadingGenerator(generator)
        return preloadingGen

    def findAlternatives(self, disambPage):
        """
        Append link target to a list of alternative links.

        Overrides the DisambiguationRobot method.

        @return: True if alternate link was appended
        @rtype: bool or None
        """
        if disambPage.isRedirectPage():
            self.alternatives.append(disambPage.getRedirectTarget().title())
            return True
        if self.misspellingTemplate.get(disambPage.site.code) is not None:
            templates = self.misspellingTemplate[disambPage.site.code]
            if isinstance(templates, UnicodeType):
                templates = (templates, )
            for template, params in disambPage.templatesWithParams():
                if template.title(with_ns=False) in templates:
                    # The correct spelling is in the last parameter.
                    correctSpelling = params[-1]
                    # On de.wikipedia, there are some cases where the
                    # misspelling is ambiguous, see for example:
                    # https://de.wikipedia.org/wiki/Buthan
                    for match in self.linkR.finditer(correctSpelling):
                        self.alternatives.append(match.group('title'))

                    if not self.alternatives:
                        # There were no links in the parameter, so there is
                        # only one correct spelling.
                        self.alternatives.append(correctSpelling)
                    return True

    def setSummaryMessage(self, disambPage, *args, **kwargs):
        """
        Setup the summary message.

        Overrides the DisambiguationRobot method.
        """
        # TODO: setSummaryMessage() in solve_disambiguation now has parameters
        # new_targets and unlink. Make use of these here.
        self.comment = i18n.twtranslate(self.site, 'misspelling-fixing',
                                        {'page': disambPage.title()})


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    # the option that's always selected when the bot wonders what to do with
    # a link. If it's None, the user is prompted (default behaviour).
    always = None
    main_only = False
    firstPageTitle = None

    for arg in pywikibot.handle_args(args):
        arg, sep, value = arg.partition(':')
        if arg == '-always':
            always = value
        elif arg == '-start':
            firstPageTitle = value or pywikibot.input(
                'At which page do you want to start?')
        elif arg == '-main':
            main_only = True

    bot = MisspellingRobot(always, firstPageTitle, main_only)
    bot.run()


if __name__ == '__main__':
    main()
