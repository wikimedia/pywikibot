#!/usr/bin/python
"""
Include Commons template in home wiki.

This bot functions mainly in the en.wikipedia, because it
compares the names of articles and category in English
language (standard language in Commons). If the name of
an article in Commons will not be in English but with
redirect, this also functions.

Syntax:

    python pwb.py commons_link [action] [pagegenerator]

where action can be one of these

 * pages      : Run over articles, include {{commons}}
 * categories : Run over categories, include {{commonscat}}

and pagegenerator can be one of these:

&params;
"""
#
# (C) Pywikibot team, 2006-2021
#
# Distributed under the terms of the MIT license.
#
# Ported by Geoffrey "GEOFBOT" Mon for Google Code-In 2013
# User:Sn1per
#
import re

import pywikibot
from pywikibot import Bot, i18n, pagegenerators, textlib
from pywikibot.backports import Tuple
from pywikibot.exceptions import (
    EditConflictError,
    IsRedirectPageError,
    LockedPageError,
    NoPageError,
)


docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class CommonsLinkBot(Bot):

    """Commons linking bot."""

    def __init__(self, generator, **kwargs):
        """Initializer."""
        self.available_options.update({
            'action': None,
        })
        super().__init__(**kwargs)

        self.generator = generator
        self.findTemplate = re.compile(r'\{\{[Ss]isterlinks')
        self.findTemplate2 = re.compile(r'\{\{[Cc]ommonscat')
        self.findTemplate3 = re.compile(r'\{\{[Cc]ommons')

    def run(self):
        """Run the bot."""
        if not all((self.opt.action, self.generator)):
            return
        catmode = (self.opt.action == 'categories')
        for page in self.generator:
            try:
                self.current_page = page
                commons = page.site.image_repository()
                commonspage = getattr(pywikibot,
                                      ('Page', 'Category')[catmode]
                                      )(commons, page.title())
                try:
                    commonspage.get(get_redirect=True)
                    pagetitle = commonspage.title(with_ns=not catmode)
                    if page.title() == pagetitle:
                        old_text = page.get()
                        text = old_text

                        # for Commons/Commonscat template
                        s = self.findTemplate.search(text)
                        s2 = getattr(self, 'findTemplate{}'.format(
                            (2, 3)[catmode]).search(text))
                        if s or s2:
                            pywikibot.output('** Already done.')
                        else:
                            cats = textlib.getCategoryLinks(text,
                                                            site=page.site)
                            text = textlib.replaceCategoryLinks(
                                '%s{{commons%s|%s}}'
                                % (text, ('', 'cat')[catmode], pagetitle),
                                cats, site=page.site)
                            comment = i18n.twtranslate(
                                page.site, 'commons_link{}-template-added'
                                .format(('', '-cat')[catmode]))
                            try:
                                self.userPut(page, old_text, text,
                                             summary=comment)
                            except EditConflictError:
                                pywikibot.output(
                                    'Skipping {} because of edit conflict'
                                    .format(page.title()))

                except NoPageError:
                    pywikibot.output('{} does not exist in Commons'
                                     .format(page.__class__.__name__))

            except NoPageError:
                pywikibot.output('Page {} does not exist'
                                 .format(page.title()))
            except IsRedirectPageError:
                pywikibot.output('Page {} is a redirect; skipping.'
                                 .format(page.title()))
            except LockedPageError:
                pywikibot.output('Page {} is locked'.format(page.title()))


def main(*args: Tuple[str, ...]):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}

    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg in ('pages', 'categories'):
            options['action'] = arg
        elif arg == '-always':
            options['always'] = True
        else:
            gen_factory.handle_arg(arg)

    gen = gen_factory.getCombinedGenerator(preload=True)
    if pywikibot.bot.suggest_help(missing_action='action' not in options,
                                  missing_generator=not gen):
        return

    bot = CommonsLinkBot(gen, **options)
    bot.run()


if __name__ == '__main__':
    main()
