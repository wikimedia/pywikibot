#!/usr/bin/python
r"""
Program to batch create categories.

The program expects a generator of category titles to be used
as suffix for creating new categories with a different base.

The following command line parameters are supported:

-always         Don't ask, just do the edit.

-parent         The name of the parent category.

-basename       The base to be used for the new category names.

-overwrite:     Existing category is skipped by default. Use this option to
                overwrite a category.

Example:

    python pwb.py create_categories \
        -lang:commons \
        -family:commons \
        -links:User:Multichill/Wallonia \
        -parent:"Cultural heritage monuments in Wallonia" \
        -basename:"Cultural heritage monuments in"

The page 'User:Multichill/Wallonia' on commons contains
category links like [[Category:Hensies]], causing this script
to create [[Category:Cultural heritage monuments in Hensies]].
"""
#
# (c) Pywikibot team, 2011-2021
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import pagegenerators
from pywikibot.backports import Tuple
from pywikibot.bot import AutomaticTWSummaryBot, SingleSiteBot
from pywikibot.site import Namespace


class CreateCategoriesBot(SingleSiteBot, AutomaticTWSummaryBot):

    """Category creator bot."""

    summary_key = 'create_categories-create'

    def __init__(self, **kwargs):
        """Initializer."""
        self.available_options.update({
            'basename': None,
            'parent': None,
            'overwrite': False,
        })
        super().__init__(**kwargs)

    def init_page(self, item):
        """Create a category to be processed with the given page title."""
        page = super().init_page(item)
        title = page.title(with_ns=False)
        if page.namespace() != Namespace.CATEGORY:
            # return the page title to be skipped later within skip_page
            return title

        category = pywikibot.Category(
            page.site, '{} {}'.format(self.opt.basename, title))

        text = '[[{namespace}:{parent}|{title}]]\n{category}\n'.format(
            namespace=page.site.namespace(Namespace.CATEGORY),
            parent=self.opt.parent,
            title=title,
            category=page)
        category.text = text
        return category

    def treat_page(self):
        """Create category in local site for that page."""
        newtext = self.current_page.text
        self.current_page.text = ''
        self.put_current(newtext, ignore_server_errors=True)

    def skip_page(self, page):
        """Skip page if it is not overwritten."""
        if isinstance(page, str):
            pywikibot.warning(page + ' is not a category, skipping')
            return True
        if page.exists() and not self.opt.overwrite:
            pywikibot.warning('{} already exists, skipping'.format(page))
            return True
        return super().skip_page(page)


def main(*args: str):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        option, _, value = arg.partition(':')
        opt = option[1:]
        if arg in ('-always', '-overwrite'):
            options[opt] = True
        elif option in ('-parent', '-basename'):
            if value:
                options[opt] = value
        else:
            gen_factory.handle_arg(arg)

    missing = ['-' + arg for arg in ('basename', 'parent')
               if arg not in options]

    generator = gen_factory.getCombinedGenerator()
    if pywikibot.bot.suggest_help(missing_parameters=missing,
                                  missing_generator=not generator):
        return

    bot = CreateCategoriesBot(generator=generator, **options)
    bot.run()


if __name__ == '__main__':
    main()
