#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This script transfers pages from a source wiki to a target wiki.

It also copies edit history to a subpage.

-tolang:          The target site code.

-tofamily:        The target site family.

-prefix:          Page prefix on the new site.

-overwrite:       Existing pages are skipped by default. Use his option to
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
from pywikibot import pagegenerators

docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class WikiTransferException(Exception):

    """Base class for exceptions from this script.

    Makes it easier for clients to catch all expected exceptions that the
    script might throw
    """

    pass


class TargetSiteMissing(WikiTransferException):

    """Thrown when the target site is the same as the source site.

    Based on the way each are initialized, this is likely to happen when the
    target site simply hasn't been specified.
    """

    pass


class TargetPagesMissing(WikiTransferException):

    """Thrown if no page range has been specified to operate on."""

    pass


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: unicode
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

    tosite = pywikibot.Site(tolang, tofamily)
    if fromsite == tosite:
        raise TargetSiteMissing('Target site not different from source site')

    gen = gen_factory.getCombinedGenerator()
    if not gen:
        raise TargetPagesMissing('Target pages not specified')

    gen_args = ' '.join(gen_args)
    pywikibot.output("""
    Page transfer configuration
    ---------------------------
    Source: %(fromsite)r
    Target: %(tosite)r

    Pages to transfer: %(gen_args)s

    Prefix for transferred pages: %(prefix)s
    """ % {'fromsite': fromsite, 'tosite': tosite,
           'gen_args': gen_args, 'prefix': prefix})

    for page in gen:
        target_title = (prefix + page.namespace().canonical_prefix()
                        + page.title(with_ns=False))
        targetpage = pywikibot.Page(tosite, target_title)
        edithistpage = pywikibot.Page(tosite, target_title + '/edithistory')
        summary = 'Moved page from {old} ([[{new}/edithistory|history]])' \
                  .format(old=page.title(as_link=True, insite=tosite),
                          new=targetpage.title() if not
                          targetpage.namespace().subpages else '')

        if targetpage.exists() and not overwrite:
            pywikibot.output(
                'Skipped {0} (target page {1} exists)'.format(
                    page.title(as_link=True),
                    targetpage.title(as_link=True)
                )
            )
            continue

        pywikibot.output('Moving {0} to {1}...'
                         .format(page.title(as_link=True),
                                 targetpage.title(as_link=True)))

        pywikibot.log('Getting page text.')
        text = page.get(get_redirect=True)
        text += ("<noinclude>\n\n<small>This page was moved from {0}. It's "
                 'edit history can be viewed at {1}</small></noinclude>'
                 .format(page.title(as_link=True, insite=targetpage.site),
                         edithistpage.title(as_link=True,
                                            insite=targetpage.site)))

        pywikibot.log('Getting edit history.')
        historytable = page.getVersionHistoryTable()

        pywikibot.log('Putting page text.')
        targetpage.put(text, summary=summary)

        pywikibot.log('Putting edit history.')
        edithistpage.put(historytable, summary=summary)


if __name__ == '__main__':
    try:
        main()
    except TargetSiteMissing:
        pywikibot.error('Need to specify a target site and/or language')
        pywikibot.error('Try running this script with -help for help/usage')
        pywikibot.exception()
    except TargetPagesMissing:
        pywikibot.error('Need to specify a page range')
        pywikibot.error('Try running this script with -help for help/usage')
        pywikibot.exception()
