# -*- coding: utf-8  -*-
"""
Print a list of pages, as defined by page generator parameters

These parameters are supported to specify which pages titles to print:

-format  Defines the output format.
         Default: "{num:4d} {page.title}" (  10 PageTitle)

         Other suggestions:
         "# {page}" (# [[PageTitle]])

&params;
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
    fmt = "{num:4d} {page.title}"
    genFactory = GeneratorFactory()
    for arg in pywikibot.handleArgs(*args):
        if arg.startswith("-format:"):
            fmt = arg[len("-format:"):]
        genFactory.handleArg(arg)
    gen = genFactory.getCombinedGenerator()
    if gen:
        for i, page in enumerate(gen):
            pywikibot.stdout(fmt.format(num=i, page=page))
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    main()
