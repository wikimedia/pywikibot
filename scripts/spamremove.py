#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to remove links that are being or have been spammed.

Usage:

spamremove.py www.spammedsite.com

It will use Special:Linksearch to find the pages on the wiki that link to
that site, then for each page make a proposed change consisting of removing
all the lines where that url occurs. You can choose to:
* accept the changes as proposed
* edit the page yourself to remove the offending link
* not change the page in question

Command line options:
-always           Do not ask, but remove the lines automatically. Be very
                  careful in using this option!

-namespace:       Filters the search to a given namespace. If this is specified
                  multiple times it will search all given namespaces

"""
#
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

#

import pywikibot
from pywikibot import i18n
from pywikibot.editor import TextEditor


def main(*args):
    """
    Process command line arguments and perform task.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    always = False
    namespaces = []
    spamSite = ''
    for arg in pywikibot.handle_args(args):
        if arg == "-always":
            always = True
        elif arg.startswith('-namespace:'):
            try:
                namespaces.append(int(arg[len('-namespace:'):]))
            except ValueError:
                namespaces.append(arg[len('-namespace:'):])
        else:
            spamSite = arg

    if not spamSite:
        pywikibot.showHelp()
        pywikibot.output(u"No spam site specified.")
        return

    mysite = pywikibot.Site()
    pages = mysite.exturlusage(spamSite, namespaces=namespaces, content=True)

    summary = i18n.twtranslate(mysite, 'spamremove-remove',
                               {'url': spamSite})
    for i, p in enumerate(pages, 1):
        text = p.text
        if spamSite not in text:
            continue
        # Show the title of the page we're working on.
        # Highlight the title in purple.
        pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                         % p.title())
        lines = text.split('\n')
        newpage = []
        lastok = ""
        for line in lines:
            if spamSite in line:
                if lastok:
                    pywikibot.output(lastok)
                pywikibot.output('\03{lightred}%s\03{default}' % line)
                lastok = None
            else:
                newpage.append(line)
                if line.strip():
                    if lastok is None:
                        pywikibot.output(line)
                    lastok = line
        if always:
            answer = "y"
        else:
            answer = pywikibot.input_choice(
                u'\nDelete the red lines?',
                [('yes', 'y'), ('no', 'n'), ('edit', 'e')],
                'n', automatic_quit=False)
        if answer == "n":
            continue
        elif answer == "e":
            editor = TextEditor()
            newtext = editor.edit(text, highlight=spamSite,
                                  jumpIndex=text.find(spamSite))
        else:
            newtext = "\n".join(newpage)
        if newtext != text:
            p.text = newtext
            p.save(summary)
    else:
        if "i" not in locals():
            pywikibot.output('No page found.')
        elif i == 1:
            pywikibot.output('1 pages done.')
        else:
            pywikibot.output('%d pages done.' % i)


if __name__ == '__main__':
    main()
