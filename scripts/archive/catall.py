#!/usr/bin/python
"""
This script shows the categories on each page and lets you change them.

For each page in the target wiki

 - If the page contains no categories, you can specify a list of categories to
   add to the page.
 - If the page already contains one or more categories, you can specify a new
   list of categories to replace the current list of categories of the page.

Usage:

    python pwb.py catall [start]

If no starting name is provided, the bot starts at 'A'.

Options:

-onlynew : Only run on pages that do not yet have a category.
"""
#
# (C) Pywikibot team, 2004-2021
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import i18n, textlib
from pywikibot.backports import List, Tuple
from pywikibot.bot import QuitKeyboardInterrupt
from pywikibot.exceptions import IsRedirectPageError


def choosecats(pagetext: str) -> List[str]:
    """Choose categories.

    :param pagetext: The text of the page
    :return: chosen list which contains all the choices
    """
    chosen = []
    done = False
    length = 1000
    # TODO: → input_choice
    pywikibot.output("""Give the new categories, one per line.
Empty line: if the first, don't change. Otherwise: Ready.
-: I made a mistake, let me start over.
?: Give the text of the page with GUI.
??: Give the text of the page in console.
xx: if the first, remove all categories and add no new.
q: quit.""")
    while not done:
        choice = pywikibot.input('?')
        if choice == '':
            done = True
        elif choice == '-':
            chosen = choosecats(pagetext)
            done = True
        elif choice == '?':
            from pywikibot import editor as editarticle
            editor = editarticle.TextEditor()
            editor.edit(pagetext)
        elif choice == '??':
            pywikibot.output(pagetext[0:length])
            length = length + 500
        elif choice == 'xx' and not chosen:
            chosen = None
            done = True
        elif choice == 'q':
            raise QuitKeyboardInterrupt
        else:
            chosen.append(choice)
    return chosen


def make_categories(page, list: list, site=None):
    """Make categories.

    :param page: The page to update and save
    :type page: pywikibot.page.BasePage
    :param list: The list which contains categories
    """
    if site is None:
        site = pywikibot.Site()
    pllist = []
    for p in list:
        pllist.append(pywikibot.Page(site, 'Category:' + p))
    page.put(textlib.replaceCategoryLinks(page.get(), pllist, site=page.site),
             asynchronous=True,
             summary=i18n.twtranslate(site, 'catall-changing'))


def main(*args: str):
    """
    Process command line arguments and perform task.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    docorrections = True
    start = 'A'

    local_args = pywikibot.handle_args(args)

    for arg in local_args:
        if arg == '-onlynew':
            docorrections = False
        else:
            start = arg

    mysite = pywikibot.Site()

    for p in mysite.allpages(start=start):
        try:
            text = p.get()
        except IsRedirectPageError:
            pywikibot.output('{} is a redirect'.format(p.title()))
        else:
            pywikibot.output('========== {} =========='.format(p.title()))
            cats = p.categories()

            if not cats:
                pywikibot.output('No categories')
                pywikibot.output('-' * 40)
                newcats = choosecats(text)
                if newcats:
                    make_categories(p, newcats, mysite)
            elif docorrections:
                for c in cats:
                    pywikibot.output(c.title())
                pywikibot.output('-' * 40)
                newcats = choosecats(text)
                if newcats is None:
                    make_categories(p, [], mysite)
                elif newcats:
                    make_categories(p, newcats, mysite)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pywikibot.output('\nQuitting program...')
