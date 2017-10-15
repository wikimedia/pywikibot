# -*- coding: utf-8 -*-
"""Title translate module."""
#
# (C) Rob W.W. Hooft, 2003
# (C) Yuri Astrakhan, 2005
# (C) Pywikibot team, 2003-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#
import re

import pywikibot
import pywikibot.date as date

from pywikibot import config
from pywikibot.tools import deprecated_args


@deprecated_args(family=None)
def translate(page=None, hints=None, auto=True, removebrackets=False,
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

    if site is None and page:
        site = page.site

    if hints:
        for h in hints:
            if ':' not in h:
                # argument given as -hint:xy where xy is a language code
                codes = h
                newname = ''
            else:
                codes, newname = h.split(':', 1)
            if newname == '':
                # if given as -hint:xy or -hint:xy:, assume that there should
                # be a page in language xy with the same title as the page
                # we're currently working on ...
                if page is None:
                    continue
                newname = page.title(withNamespace=False)
                # ... unless we do want brackets
                if removebrackets:
                    newname = re.sub(re.compile(r"\W*?\(.*?\)\W*?",
                                                re.UNICODE), u" ", newname)
            try:
                number = int(codes)
                codes = site.family.languages_by_size[:number]
            except ValueError:
                if codes == 'all':
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
                                           defaultNamespace=ns)
                        result.add(x)
                else:
                    if config.verbose_output:
                        pywikibot.output(u"Ignoring unknown language code %s"
                                         % newcode)

    # Autotranslate dates into all other languages, the rest will come from
    # existing interwiki links.
    if auto and page:
        # search inside all dictionaries for this link
        sitelang = page.site.code
        dictName, value = date.getAutoFormat(sitelang, page.title())
        if dictName:
            pywikibot.output(
                u'TitleTranslate: %s was recognized as %s with value %d'
                % (page.title(), dictName, value))
            for entryLang, entry in date.formats[dictName].items():
                if entryLang not in site.languages():
                    continue
                if entryLang != sitelang:
                    newname = entry(value)
                    x = pywikibot.Link(
                        newname,
                        pywikibot.Site(code=entryLang,
                                       fam=site.family))
                    result.add(x)
    return list(result)
