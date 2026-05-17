#!/usr/bin/env python3
#
# (C) Pywikibot team, 2013-2026
#
# Distributed under the terms of the MIT license.
#
"""Used to find expensive templates that are subject to be converted to Lua.

It counts parser functions and then orders templates by number of these
and uploads the first n titles or alternatively templates having count()>n.

Parameters:

-start            Will start from the given title (it does not have to exist).
                  Parameter may be given as "-start" or "-start:title".
                  Defaults to '!'.

-first            Returns the first n results in decreasing order of number
                  of hits (or without ordering if used with -nosort)
                  Parameter may be given as "-first" or "-first:n".

-atleast          Returns templates with at least n hits.
                  Parameter may be given as "-atleast" or "-atleast:n".

-nosort           Keeps the original order of templates. Default behaviour is
                  to sort them by decreasing order of count(parserfunctions).

-save             Saves the results. The file is in the form you may upload it
                  to a wikipage. May be given as "-save:<filename>".
                  If it exists, titles will be appended.

-upload           Specify a page in your wiki where results will be uploaded.
                  Parameter may be given as "-upload" or "-upload:title".
                  Say good-bye to previous content if existed.

Precedence of evaluation: results are first sorted in decreasing order of
templates, unless nosort is switched on. Then first n templates are taken if
first is specified, and at last atleast is evaluated. If nosort and first are
used together, the program will stop at the nth hit without scanning the rest
of the template namespace. This may be used to run it in more sessions
(continue with -start next time).

First is strict. That means if results #90-120 have the same number of parser
functions and you specify -first:100, only the first 100 will be listed (even
if atleast is used as well).

Should you specify neither first nor atleast, all templates using parser
functions will be listed.
"""
from __future__ import annotations

import re
from collections import Counter

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import ExistingPageBot, SingleSiteBot


class ParserFunctionCountBot(SingleSiteBot, ExistingPageBot):

    """Bot class used for obtaining parser function count."""

    use_redirects = False

    update_options = {
        'atleast': None,
        'first': None,
        'nosort': False,
        'save': None,
        'start': '!',
        'upload': None,
    }

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        editcomment = {
            # This will be used for uploading the list to your wiki.
            'en':
                'Bot: uploading list of templates having too many parser '
                'functions',
            'hu':
                'A túl sok parserfüggvényt használó sablonok listájának '
                'feltöltése',
        }

        # Limitations for result:
        if self.opt.first:
            try:
                self.opt.first = int(self.opt.first)
                if self.opt.first < 1:
                    self.opt.first = None
            except ValueError:
                self.opt.first = None

        if self.opt.atleast:
            try:
                self.opt.atleast = int(self.opt.atleast)
                # 1 has no effect, don't waste resources.
                if self.opt.atleast < 2:
                    self.opt.atleast = None
            except ValueError:
                self.opt.atleast = None

        lang = self.site.lang
        self.summary = editcomment.get(lang, editcomment['en'])

    @property
    def generator(self):
        """Generator."""
        gen = self.site.allpages(start=self.opt.start, namespace=10,
                                 filterredir=False, content=True)
        if self.site.doc_subpage:
            gen = pagegenerators.RegexFilterPageGenerator(
                gen, self.site.doc_subpage, quantifier='none')
        return gen

    def setup(self) -> None:
        """Setup magic words, regex and result counter."""
        pywikibot.info('Hold on, this will need some time.')
        magicwords = []
        for magic_word in self.site.siteinfo['magicwords']:
            magicwords += magic_word['aliases']
        self.regex = re.compile(r'#({}):'.format('|'.join(magicwords)), re.I)
        self.results = Counter()

    def treat(self, page) -> None:
        """Process a single template."""
        if self.counter['read'] % 100 == 0:
            # Don't let the poor user panic in front of a black screen.
            pywikibot.info('.', newline=False)

        functions = self.regex.findall(page.text)
        if functions and (self.opt.atleast is None
                          or self.opt.atleast <= len(functions)):
            self.results[page.title()] = len(functions)

        if self.opt.nosort and self.opt.first \
           and len(self.results) >= self.opt.first:
            self.stop()

    def teardown(self) -> None:
        """Final processing."""
        resultlist = '\n'.join(
            f'# [[{result[0]}]] ({result[1]})'
            for result in self.results.most_common(self.opt.first)
        )
        pywikibot.info()
        pywikibot.info(resultlist)
        pywikibot.info(f'{len(self.results)} templates were found.')

        # File operations:
        if self.opt.save:
            try:
                with open(self.opt.save, 'a', encoding='utf-8') as f:
                    f.write(resultlist)
            except OSError as e:
                pywikibot.error(e)

        if self.opt.upload:
            page = pywikibot.Page(self.site, self.opt.upload)
            self.userPut(page, page.text, resultlist,
                         ignore_save_related_errors=True,
                         summary=self.summary)


def main(*args: str) -> None:
    """Process command line arguments and invoke ParserFunctionCountBot."""
    local_args = pywikibot.handle_args(*args)
    options = {}

    # Parse command line arguments
    for arg in local_args:
        opt, _, value = arg.partition(':')
        if not opt.startswith('-'):
            continue
        opt = opt[1:]
        if opt == 'start':
            options[opt] = value or pywikibot.input(
                'From which title do you want to continue?')
        elif opt == 'save':
            options[opt] = value or pywikibot.input(
                'Please enter the filename:')
        elif opt == 'upload':
            options[opt] = value or pywikibot.input(
                'Please enter the pagename:')
        elif opt == 'first':
            options[opt] = value or pywikibot.input(
                'Please enter the max. number of templates to display:')
        elif opt == 'atleast':
            options[opt] = value or pywikibot.input(
                'Please enter the min. number of functions to display:')
        elif opt == 'nosort':
            options[opt] = True

    bot = ParserFunctionCountBot(**options)
    bot.run()


if __name__ == '__main__':
    main()
