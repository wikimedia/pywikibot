#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Bot to create redirects based on name order.

By default it creates a "Surnames, Given Names" redirect
version of a given page where title consists of 2 or 3 titlecased words.

Command-line arguments:

&params;

-surnames_last    Creates a "Given Names Surnames" redirect version of a
                  given page where title is "Surnames, Given Names".

Example: "python pwb.py surnames_redirects -start:B"
"""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from difflib import SequenceMatcher

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import FollowRedirectPageBot, ExistingPageBot

docuReplacements = {'&params;': pagegenerators.parameterHelp}


class SurnamesBot(ExistingPageBot, FollowRedirectPageBot):

    """Surnames Bot."""

    def __init__(self, generator, **kwargs):
        """Constructor.

        Parameters:
            @param generator: The page generator that determines on
                              which pages to work.
            @kwarg surnames-last: Redirect "Surnames, Given Names" to
                                  "Given Names Surnames".
        """
        self.availableOptions.update({
            'surnames_last': False,
        })

        super(SurnamesBot, self).__init__(generator=generator, **kwargs)

    def treat_page(self):
        """Suggest redirects by reordering names in titles."""
        if self.current_page.isRedirectPage():
            return

        page_t = self.current_page.title()
        split_title = page_t.split(' (')
        name = split_title[0]
        site = self.current_page.site

        possible_names = []
        if self.getOption('surnames_last'):
            name_parts = name.split(', ')
            if len(name_parts) == 2 and len(name.split(' ')) <= 3:
                possible_names.append(name_parts[1] + ' ' + name_parts[0])
        else:
            words = name.split()
            if len(words) == 2 and name == name.title():
                possible_names.append(words[1] + ', ' + words[0])
            elif len(words) == 3:
                # title may have at most one non-titlecased word
                if len(SequenceMatcher(None, name,
                   name.title()).get_matching_blocks()) <= 3:
                    possible_names.append(words[1] + ' ' +
                                          words[2] + ', ' +
                                          words[0])
                    possible_names.append(words[2] + ', ' +
                                          words[0] + ' ' +
                                          words[1])

        for possible_name in possible_names:
            # append disambiguation inside parenthesis if there is one
            if len(split_title) == 2:
                possible_name += ' (' + split_title[1]

            new_page = pywikibot.Page(site, possible_name)
            if new_page.exists():
                pywikibot.output('%s already exists, skipping...'
                                 % new_page.title(asLink=True))
            else:
                pywikibot.output('%s doesn\'t exist'
                                 % new_page.title(asLink=True))
                choice = pywikibot.input_yn(
                    'Do you want to create a redirect?')
                if choice:
                    comment = i18n.twtranslate(
                        site,
                        'capitalize_redirects-create-redirect',
                        {'to': page_t})
                    new_page.set_redirect_target(self.current_page,
                                                 create=True, summary=comment)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    options = {}

    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-surnames_last':
            options['surnames_last'] = True
        else:
            genFactory.handleArg(arg)

    gen = genFactory.getCombinedGenerator()
    if gen:
        bot = SurnamesBot(gen, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == "__main__":
    main()
