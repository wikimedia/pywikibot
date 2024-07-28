#!/usr/bin/env python3
"""This script transfers pages from a source wiki to a target wiki.

It uses :api:`Import` and it is also able to copy the full edit history.

The following parameters are supported:

-interwikisource:        The interwiki code of the source wiki.

-fullhistory:            Include all versions of the page.

-includealltemplates:    All templates and transcluded pages will
                         be copied (dangerous).

-assignknownusers:       If user exists on target wiki, assign the
                         editions to them

-correspondingnamespace: The number of the corresponding namespace.

-rootpage:               Import as subpages of ...

-summary:                Log entry import summary.

-tags:                   Change tags to apply to the entry in the import
                         log and to the null revision on the imported
                         pages.

-overwrite:              Existing pages are skipped by default.
                         Use this option to overwrite pages.

-target                  Use page generator of the target site
                         This also affects the correspondingnamespace.

.. warning:: Internal links are *not* repaired!

Pages to work on can be specified using any of:

&params;

Examples
--------

Transfer all pages in category "Query service" from the English
Wikipedia to the home Wikipedia, adding "Wikipedia:Import enwp/" as
prefix:

    python pwb.py transwikiimport -interwikisource:en -cat:"Query service" \
-prefix:"Wikipedia:Import enwp/" -fullhistory -assignknownusers

Copy the template "Query service" from the English Wikipedia to the home
Wiktionary:

    python pwb.py transferbot -interwikisource:w:en \
-page:"Template:Query service" -fullhistory -assignknownusers

Copy 10 wanted templates of the home Wikipedia from English Wikipedia to
the home Wikipedia:

    python pwb.py transferbot -interwikisource:en -wantedtemplates:10 \
-target -fullhistory -assignknownusers


Advices
-------

The module gives access to all parameters of the API (and special page)
and is compatible to the :mod:`scripts.transferbot` script.
However for most scenarios the parameters ``-overwrite``, ``-target`` and
``-includealltemplates`` should be avoided; by default they are set to
False.

The correspondingnamespace is used only if the namespaces on both wikis
do not correspond one with another.

Correspondingnamespace and rootpage are mutually exclusive.

Target and rootpage are mutually exclusive. (This combination does not
seem to be feasible.)

If the target page already exists, the target page will be overwritten
if ``-overwrite`` is set or skipped otherwise.

The list of pages to be imported can be generated outside of the pywikbot:

    for i in {1..10} ; do python3 pwb.py transwikiimport \
-interwikisource:mul -page:"Page:How to become famous.djvu/$i" \
-fullhistory -assignknownusers ; done

*The pages *``Page:How to become famous.djvu/1``*,
*``Page:How to become famous.djvu/2``* ..
*``Page:How to become famous.djvu/10``* will be copied from wikisource
(mul) to the home-wikisource, all versions will be imported and the
usernames will be identified (existing pages will be skipped).*

Or generated using the usual pywikibot generators:

    python3 pwb.py transwikiimport -interwikisource:mul \
-prefixindex:"Page:How to become famous.djvu" -fullhistory \
-assignknownusers -summary:"Book copied from oldwiki."

*All pages like *``Page:How to become famous.djvu``*... will be copied
from wikisource (mul) to the home-wikisource, all versions will be
imported and the usernames will be identified (existing pages will be
skipped).*

The global option ``-simulate`` disables the import and the bot prints
the names of the pages that would be imported. Since the import of pages
is a quite exceptionell process and potentially dangerous it should be
made carefully and tested in advance.

The ``-simulate`` option can help to find out which pages would be moved
and what would be the target of the import. However it does not print
the titles of the transcluded pages (e.g. templates) if
``-includealltemplates`` is set.

This option is quite *dangerous*. If the title of an existing page on
home wiki clashes with the title of one of the linked pages it would be
*overritten*. The histories would be merged. (If the imported version is
newer.) Even if ``-overwrite`` is not set the linked page *can be
overwritten*.


Hints
-----

The list of wikis that can be used as a interwiki source is defined in
the variable ``$wgImportSources``. It can be viewed on the
``Special:Import`` page.


Rights
------

For transwikiimport script and even to access the ``Special:Import``
page the appropriate flag on the account must be set, usually
administrator, transwiki importer or importer.

.. versionadded:: 8.2
"""
#
# (C) Pywikibot team, 2023-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import suggest_help
from pywikibot.data import api


docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


def api_query(site, params: dict[str, str]):
    """Request data from given site."""
    query = api.Request(site, parameters=params)
    datas = query.submit()
    return datas


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    local_args = pywikibot.handle_args(args)

    interwikisource = ''
    correspondingnamespace = 'all'
    rootpage = ''
    tags = ''
    summary = 'Importing page from '
    overwrite = False
    target = False
    fullhistory = False
    includealltemplates = False
    assignknownusers = False
    gen_args = []

    for arg in local_args:
        if arg.startswith('-interwikisource'):
            interwikisource = arg[len('-interwikisource:'):]
            summary += interwikisource
        elif arg.startswith('-correspondingnamespace'):
            correspondingnamespace = arg[len('-correspondingnamespace:'):]
        elif arg.startswith('-rootpage'):
            rootpage = arg[len('-rootpage:'):]
        elif arg.startswith('-tags'):
            tags = arg[len('-tags:'):]
        elif arg.startswith('-summary'):
            summary = arg[len('-summary:'):]
        elif arg == '-overwrite':
            overwrite = True
        elif arg == '-target':
            target = True
        elif arg == '-fullhistory':
            fullhistory = True
        elif arg == '-includealltemplates':
            includealltemplates = True
        elif arg == '-assignknownusers':
            assignknownusers = True
        else:
            gen_args.append(arg)

    tosite = pywikibot.Site()
    csrf = tosite.tokens['csrf']
    fromsite = pywikibot.Site().interwiki(interwikisource)
    additional_text = ('Target site not different from source site.'
                       if fromsite == tosite else '')

    gen_factory = pagegenerators.GeneratorFactory(site=tosite if target
                                                  else fromsite)
    unknown_args = [arg for arg in gen_args if not gen_factory.handle_arg(arg)]

    gen = gen_factory.getCombinedGenerator()

    if suggest_help(missing_generator=not gen,
                    additional_text=additional_text,
                    unknown_parameters=unknown_args):
        return

    gen_args = ' '.join(gen_args)
    pywikibot.info("""
    Page transfer configuration
    ---------------------------
    Source: {fromsite}
    Target: {tosite}

    Generator of pages to transfer: {gen_args}
    {target}
    Prefix for transferred pages: {rootpage}
    """.format(fromsite=fromsite, tosite=tosite, gen_args=gen_args,
               rootpage=rootpage if rootpage else '(none)',
               target='from target site\n' if target else ''))

    if correspondingnamespace != 'all' and rootpage:
        pywikibot.info('Both the correspondingnamespace and the rootpage are '
                       'set! Exiting.')
    elif target and rootpage:
        pywikibot.info('Both the target and the rootpage are set! Exiting.')
    else:
        params = {
            'action': 'import',
            'token': csrf,
            'interwikisource': interwikisource,
            'fullhistory': fullhistory,
            'assignknownusers': assignknownusers,
            'templates': includealltemplates,
            'summary': summary
        }
        if correspondingnamespace != 'all':
            params['namespace'] = correspondingnamespace
        if rootpage:
            params['rootpage'] = rootpage
        if tags:
            params['tags'] = tags

        for page in gen:
            if target:
                if correspondingnamespace == 'all':
                    fromtitle = (page.namespace().canonical_prefix()
                                 + page.title(with_ns=False))
                else:
                    fromtitle = str(
                        fromsite.namespaces[int(correspondingnamespace)]) \
                        + page.title(with_ns=False)
                targetpage = page
            else:
                fromtitle = page.title(with_ns=True)
                if correspondingnamespace == 'all':
                    totitle = (page.namespace().canonical_prefix()
                               + page.title(with_ns=False))
                else:
                    totitle = str(
                        tosite.namespaces[int(correspondingnamespace)]) \
                        + page.title(with_ns=False)
                targetpage = pywikibot.Page(tosite, totitle)

            if not overwrite:
                if targetpage.exists():
                    pywikibot.warning(
                        'Skipped '
                        f'{page.title(as_link=True, force_interwiki=True)} '
                        f'(target page {targetpage.title(as_link=True)}'
                        ' exists)'
                    )
                    continue
            else:
                if not targetpage.botMayEdit():
                    pywikibot.warning(
                        f'Target page {targetpage.title(as_link=True)} is not'
                        ' editable by bots'
                    )
                    continue

            params['interwikipage'] = fromtitle
            api_query(tosite, params)
            pywikibot.info(f'{fromtitle} →  {targetpage}')


if __name__ == '__main__':
    main()
