# -*- coding: utf-8 -*-
"""Title translate module."""
#
# (C) Pywikibot team, 2003-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import pywikibot
from pywikibot import date

from pywikibot import config
from pywikibot.tools import deprecated_args


@deprecated_args(family=None)
def translate(page=None, hints=(), auto=True, removebrackets=False,
              site=None):
    """
    Return a list of links to pages on other sites based on hints.

    Entries for single page titles list those pages. Page titles for entries
    such as "all:" or "xyz:" or "20:" are first built from the page title of
    'page' and then listed. When 'removebrackets' is True, a trailing pair of
    brackets and the text between them is removed from the page title.
    If 'auto' is true, known year and date page titles are autotranslated
    to all known target languages and inserted into the list.
    """
    result = set()

    assert page or site

    if site is None:
        site = page.site

    for h in hints:
        # argument may be given as -hint:xy where xy is a language code
        codes, _, newname = h.partition(':')
        if not newname:
            # if given as -hint:xy or -hint:xy:, assume that there should
            # be a page in language xy with the same title as the page
            # we're currently working on ...
            if page is None:
                continue
            newname = page.title(with_ns=False,
                                 without_brackets=removebrackets)
        if codes.isdigit():
            codes = site.family.languages_by_size[:int(codes)]
        elif codes == 'all':
            codes = site.family.languages_by_size
        elif codes in site.family.language_groups:
            codes = site.family.language_groups[codes]
        else:
            codes = codes.split(',')

        for newcode in codes:
            if newcode in site.languages():
                if newcode != site.code:
                    ns = page.namespace() if page else 0
                    x = pywikibot.Link(newname,
                                       site.getSite(code=newcode),
                                       default_namespace=ns)
                    result.add(x)
            elif config.verbose_output:
                pywikibot.output('Ignoring unknown language code {}'
                                 .format(newcode))

    # Autotranslate dates into all other languages, the rest will come from
    # existing interwiki links.
    if auto and page:
        # search inside all dictionaries for this link
        sitelang = page.site.lang
        dict_name, value = date.getAutoFormat(sitelang, page.title())
        if dict_name:
            pywikibot.output(
                'TitleTranslate: %s was recognized as %s with value %d'
                % (page.title(), dict_name, value))
            for entry_lang, entry in date.formats[dict_name].items():
                if entry_lang not in site.languages():
                    continue
                if entry_lang != sitelang:
                    newname = entry(value)
                    x = pywikibot.Link(
                        newname,
                        pywikibot.Site(code=entry_lang,
                                       fam=site.family))
                    result.add(x)
    return list(result)
