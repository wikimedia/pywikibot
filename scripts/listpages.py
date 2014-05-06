# -*- coding: utf-8  -*-
"""
Print a list of pages, as defined by page generator parameters.
Optionally, it also prints page content to STDOUT.

These parameters are supported to specify which pages titles to print:

&params;

-notitle          Page title is not printed.

-get              Page content is printed.

"""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import pywikibot
from pywikibot.pagegenerators import GeneratorFactory, parameterHelp

docuReplacements = {'&params;': parameterHelp}


def main(*args):
    gen = None
    notitle = False
    page_get = False

    genFactory = GeneratorFactory()
    for arg in pywikibot.handleArgs(*args):
        if arg == '-notitle':
            notitle = True
        elif arg == '-get':
            page_get = True
        else:
            genFactory.handleArg(arg)

    gen = genFactory.getCombinedGenerator()
    if gen:
        for i, page in enumerate(gen, start=1):
            if not notitle:
                pywikibot.stdout("%4d: %s" % (i, page.title()))
            if page_get:
                # TODO: catch exceptions
                pywikibot.output(page.text, toStdout=True)
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    main()
