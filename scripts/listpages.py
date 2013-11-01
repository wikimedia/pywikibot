# -*- coding: utf-8  -*-
"""
Print a list of pages, as defined by page generator parameterd

These parameters are supported to specify which pages titles to print:

&params;
"""
#
# (C) Pywikipedia bot team, 2008-2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import pywikibot
from pywikibot.pagegenerators import GeneratorFactory, parameterHelp

docuReplacements = {'&params;': parameterHelp}


def main(*args):
    try:
        gen = None
        genFactory = GeneratorFactory()
        for arg in pywikibot.handleArgs(*args):
            genFactory.handleArg(arg)
        gen = genFactory.getCombinedGenerator()
        if gen:
            i = 0
            for page in gen:
                i += 1
                pywikibot.stdout("%4d: %s" % (i, page.title()))
        else:
            pywikibot.showHelp()
    except Exception:
        pywikibot.error("Fatal error", exc_info=True)
    finally:
        pywikibot.stopme()

if __name__ == "__main__":
    main()
