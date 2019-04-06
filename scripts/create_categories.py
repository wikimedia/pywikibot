#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
Program to batch create categories.

The program expects a generator of page titles to be used as
suffix for creating new categories with a different base.

The following command line parameters are supported:

-always         Don't ask, just do the edit.

-parent         The name of the parent category.

-basename       The base to be used for the new category names.

Example:

    python pwb.py create_categories \
        -lang:commons \
        -family:commons \
        -links:User:Multichill/Wallonia \
        -parent:"Cultural heritage monuments in Wallonia" \
        -basename:"Cultural heritage monuments in"

The page 'User:Multichill/Wallonia' on commons contains
page links like [[Category:Hensies]], causing this script
to create [[Category:Cultural heritage monuments in Hensies]].

"""
#
# (C) Multichill, 2011
# (C) xqt, 2011-2019
# (c) Pywikibot team, 2013-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import pywikibot
from pywikibot import pagegenerators, Bot


class CreateCategoriesBot(Bot):

    """Category creator bot."""

    def __init__(self, generator, parent, basename, **kwargs):
        """Initializer."""
        super(CreateCategoriesBot, self).__init__(**kwargs)
        self.generator = generator
        self.parent = parent
        self.basename = basename
        self.comment = 'Creating new category'

    def treat(self, page):
        """Create category in commons for that page."""
        title = page.title(with_ns=False)

        newpage = pywikibot.Category(pywikibot.Site('commons', 'commons'),
                                     '{} {}'.format(self.basename, title))
        newtext = ('[[Category:%(parent)s|%(title)s]]\n'
                   '[[Category:%(title)s]]\n'
                   % {'parent': self.parent, 'title': title})

        if not newpage.exists():
            pywikibot.output(newpage.title())
            self.userPut(newpage, '', newtext, summary=self.comment,
                         ignore_save_related_errors=True,
                         ignore_server_errors=True)
        else:
            pywikibot.output('{} already exists, skipping'
                             .format(newpage.title()))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    parent = None
    basename = None
    options = {}

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-always':
            options['always'] = True
        elif arg.startswith('-parent:'):
            parent = arg[len('-parent:'):].strip()
        elif arg.startswith('-basename'):
            basename = arg[len('-basename:'):].strip()
        else:
            gen_factory.handleArg(arg)

    missing = set()
    if not parent:
        missing.add('-parent')
    if not basename:
        missing.add('-basename')

    generator = gen_factory.getCombinedGenerator()
    if generator and missing:
        bot = CreateCategoriesBot(generator, parent, basename, **options)
        bot.run()
        pywikibot.output('All done')
        return True
    else:
        pywikibot.bot.suggest_help(missing_parameters=missing,
                                   missing_generator=not generator)
        return False


if __name__ == '__main__':
    main()
