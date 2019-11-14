#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This script transfers pages from a source wiki to a target wiki.

It also copies edit history to a subpage.

The following parameters are supported:

-tolang:          The target site code.

-tofamily:        The target site family.

-prefix:          Page prefix on the new site.

-overwrite:       Existing pages are skipped by default. Use this option to
                  overwrite pages.

Internal links are *not* repaired!

Pages to work on can be specified using any of:

&params;

Examples
--------

Transfer all pages in category "Query service" from the English Wikipedia to
the Arabic Wiktionary, adding "Wiktionary:Import enwp/" as prefix:

    python pwb.py transferbot -family:wikipedia -lang:en -cat:"Query service" \
        -tofamily:wiktionary -tolang:ar -prefix:"Wiktionary:Import enwp/"

Copy the template "Query service" from the English Wikipedia to the
Arabic Wiktionary:

    python pwb.py transferbot -family:wikipedia -lang:en \
        -tofamily:wiktionary -tolang:ar -page:"Template:Query service"

"""
#
# (C) Merlijn van Deen, 2014
# (C) Pywikibot team, 2014-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import pywikibot
from pywikibot.bot import suggest_help
from pywikibot import pagegenerators

docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    local_args = pywikibot.handle_args(args)

    fromsite = pywikibot.Site()
    tolang = fromsite.code
    tofamily = fromsite.family.name
    prefix = ''
    overwrite = False
    gen_args = []

    gen_factory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if gen_factory.handleArg(arg):
            gen_args.append(arg)
            continue
        if arg.startswith('-tofamily'):
            tofamily = arg[len('-tofamily:'):]
        elif arg.startswith('-tolang'):
            tolang = arg[len('-tolang:'):]
        elif arg.startswith('-prefix'):
            prefix = arg[len('-prefix:'):]
        elif arg == '-overwrite':
            overwrite = True

    gen = gen_factory.getCombinedGenerator()

    tosite = pywikibot.Site(tolang, tofamily)
    additional_text = ('Target site not different from source site.'
                       if fromsite == tosite else '')

    if additional_text or not gen:
        suggest_help(missing_generator=not gen,
                     additional_text=additional_text)
        return

    gen_args = ' '.join(gen_args)
    pywikibot.output("""
    Page transfer configuration
    ---------------------------
    Source: %(fromsite)r
    Target: %(tosite)r

    Generator of pages to transfer: %(gen_args)s

    Prefix for transferred pages: %(prefix)s
    """ % {'fromsite': fromsite, 'tosite': tosite,
           'gen_args': gen_args, 'prefix': prefix if prefix else '(none)'})

    for page in gen:
        target_title = (prefix + page.namespace().canonical_prefix()
                        + page.title(with_ns=False))
        targetpage = pywikibot.Page(tosite, target_title)
        edithistpage = pywikibot.Page(tosite, target_title + '/edithistory')

        if targetpage.exists():
            if not overwrite:
                pywikibot.warning(
                    'Skipped {0} (target page {1} exists)'.format(
                        page.title(as_link=True, force_interwiki=True),
                        targetpage.title(as_link=True)
                    )
                )
                continue
            if not targetpage.botMayEdit():
                pywikibot.warning(
                    'Target page {0} is not editable by bots'.format(
                        targetpage.title(as_link=True)
                    )
                )
                continue

        if not page.exists():
            pywikibot.warning(
                "Page {0} doesn't exist".format(
                    page.title(as_link=True)
                )
            )
            continue

        pywikibot.output('Moving {0} to {1}...'
                         .format(page.title(as_link=True,
                                            force_interwiki=True),
                                 targetpage.title(as_link=True)))

        pywikibot.log('Getting page text.')
        text = page.get(get_redirect=True)
        source_link = page.title(as_link=True, insite=targetpage.site)
        text += ('<noinclude>\n\n<small>This page was moved from {0}. Its '
                 'edit history can be viewed at {1}</small></noinclude>'
                 .format(source_link,
                         edithistpage.title(as_link=True,
                                            insite=targetpage.site)))

        pywikibot.log('Getting edit history.')
        historytable = page.getVersionHistoryTable()

        pywikibot.log('Putting edit history.')
        summary = 'Moved page from {source}'.format(source=source_link)
        edithistpage.put(historytable, summary=summary)

        pywikibot.log('Putting page text.')
        edithist_link = ' ([[{target}/edithistory|history]])'.format(
            target=targetpage.title()
            if not targetpage.namespace().subpages else '')
        summary += edithist_link
        targetpage.put(text, summary=summary)


if __name__ == '__main__':
    main()
