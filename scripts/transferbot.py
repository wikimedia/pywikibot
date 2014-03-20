#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
This script transfers pages from a source wiki to a target wiki. It also
copies edit history to a subpage.

-tolang:          The target site code.

-tosite:          The target site family.

-prefix:          Page prefix on the new site.

-overwrite:       Existing pages are skipped by default. Use his option to
                  overwrite pages.

Internal links are *not* repaired!

Pages to work on can be specified using any of:

&params;

Example commands:

# Transfer all pages in category "Query service" from the Toolserver wiki to
# wikitech, adding Nova_Resource:Tools/Tools/ as prefix
transferbot.py -v -family:toolserver -tofamily:wikitech -cat:"Query service" -prefix:Nova_Resource:Tools/Tools/

# Copy the template "Query service" from the Toolserver wiki to wikitech
transferbot.py -v -family:toolserver -tofamily:wikitech -page:"Template:Query service"

"""

#
# (C) Merlijn van Deen, 2014
# (C) pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import pywikibot
from pywikibot import pagegenerators

docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}


def main():
    tohandle = pywikibot.handleArgs()

    fromsite = pywikibot.getSite()
    tolang = fromsite.code
    tofamily = fromsite.family.name
    prefix = ''
    overwrite = False
    gen_args = []

    genFactory = pagegenerators.GeneratorFactory()

    for arg in tohandle:
        if genFactory.handleArg(arg):
            gen_args.append(arg)
            continue
        if arg.startswith('-tofamily'):
            tofamily = arg[len('-tofamily:'):]
        elif arg.startswith('-tolang'):
            tolang = arg[len('-tolang:'):]
        elif arg.startswith('-prefix'):
            prefix = arg[len('-prefix:'):]
        elif arg == "-overwrite":
            overwrite = True

    tosite = pywikibot.Site(tolang, tofamily)
    if fromsite == tosite:
        raise Exception('Target site not different from source site')

    gen = genFactory.getCombinedGenerator()
    if not gen:
        raise Exception('Target pages not specified')

    gen_args = ' '.join(gen_args)
    pywikibot.output(u"""
    Page transfer configuration
    ---------------------------
    Source: %(fromsite)r
    Target: %(tosite)r

    Pages to transfer: %(gen_args)s

    Prefix for transferred pages: %(prefix)s
    """ % locals())

    for page in gen:
        summary = "Moved page from %s" % page.title(asLink=True)
        targetpage = pywikibot.Page(tosite, prefix + page.title())
        edithistpage = pywikibot.Page(tosite, prefix + page.title()
                                      + "/edithistory")

        if targetpage.exists() and not overwrite:
            pywikibot.output(
                u"Skipped %s (target page %s exists)" % (
                    page.title(asLink=True),
                    targetpage.title(asLink=True)
                )
            )
            continue

        pywikibot.output(u"Moving %s to %s..."
                         % (page.title(asLink=True),
                            targetpage.title(asLink=True)))

        pywikibot.log("Getting page text.")
        text = page.get(get_redirect=True)
        text += "<noinclude>\n\n<small>This page was moved from %s. It's edit history can be viewed at %s</small></noinclude>" % (
                page.title(asLink=True, insite=targetpage.site),
                edithistpage.title(asLink=True, insite=targetpage.site))

        pywikibot.log("Getting edit history.")
        historytable = page.getVersionHistoryTable()

        pywikibot.log("Putting page text.")
        targetpage.put(text, comment=summary)

        pywikibot.log("Putting edit history.")
        edithistpage.put(historytable, comment=summary)


if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
