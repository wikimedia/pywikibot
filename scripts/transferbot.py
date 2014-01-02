#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
This script transfers pages from a source wiki to a target wiki. It also
copies edit history to a subpage.

Target site can be specified with -tofamily and -tolang
Source site can be specified with -fromfamily and -fromlang
Page prefix on the new site can be specified with -prefix

Existing pages are skipped by default. Pass -overwrite to overwrite pages.

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
#
# Distributed under the terms of the MIT license.
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
    tofamily = None
    prefix = ''
    template = None
    overwrite = False

    genFactory = pagegenerators.GeneratorFactory()

    for arg in tohandle:
        if genFactory.handleArg(arg):
            continue
        if arg.startswith('-tofamily'):
            tofamily = arg[len('-tofamily:'):]
        elif arg.startswith('-tolang'):
            tolang = arg[len('-tolang:'):]
        elif arg.startswith('-prefix'):
            prefix = arg[len('-prefix:'):]
        elif arg.startswith('-template'):
            prefix = arg[len('-template:'):]
        elif arg == "-overwrite":
            overwrite = True

    gen = genFactory.getCombinedGenerator()

    if not tofamily:
        raise Exception('Target family not specified')

    from pywikibot import config

    # we change the config family to make sure we get sensible backlinks
    # i.e. [[wikipedia:en:pagename]] instead of [[pagename]]
    # this should really be fixed in Page.title() (bug #59223)
    # we can't do this before, as the pagegenerator would work on the
    # incorrect site...
    config.mylang = tolang
    config.family = tofamily

    tosite = pywikibot.Site()

    if not gen:
        raise Exception('Target pages not specified')

    pywikibot.output(u"""
    Page transfer configuration
    ---------------------------
    Source: %(fromsite)r
    Target: %(tosite)r

    Pages to transfer: %(gen)r

    Prefix for transferred pages: %(prefix)s
    """ % locals())

    for page in gen:
        summary = "Moved page from %s" % page.title(asLink=True)
        targetpage = pywikibot.Page(tosite, prefix + page.title())
        edithistpage = pywikibot.Page(tosite, prefix + page.title() + "/edithistory")

        if targetpage.exists() and not overwrite:
            pywikibot.output(
                u"Skipped %s (target page %s exists)" % (
                    page.title(asLink=True),
                    targetpage.title(asLink=True)
                )
            )
            continue

        pywikibot.output(u"Moving %s to %s..." % (page.title(asLink=True), targetpage.title(asLink=True)))

        pywikibot.log("Getting page text.")
        text = page.get(get_redirect=True)
        text += "<noinclude>\n\n<small>This page was moved from %s. It's edit history can be viewed at %s</small></noinclude>" % (
                page.title(asLink=True), edithistpage.title(asLink=True))

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
