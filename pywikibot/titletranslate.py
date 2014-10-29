# -*- coding: utf-8  -*-
"""Title translate module."""
#
# (C) Rob W.W. Hooft, 2003
# (C) Yuri Astrakhan, 2005
# (C) Pywikibot team, 2003-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#
import re

import pywikibot
import pywikibot.date as date
from pywikibot import config


def translate(page, hints=None, auto=True, removebrackets=False, site=None,
              family=None):
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
    if site is None and page:
        site = page.site
    if family is None and site:
        family = site.family
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
                ns = page.namespace()
                if ns:
                    newname = u'%s:%s' % (site.namespace(ns),
                                          page.title(withNamespace=False))
                else:
                    # article in the main namespace
                    newname = page.title()
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
                        x = pywikibot.Link(newname, site.getSite(code=newcode))
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
            if not (dictName == 'yearsBC' and
                    sitelang in date.maxyearBC and
                    value > date.maxyearBC[sitelang]) or \
                    (dictName == 'yearsAD' and
                     sitelang in date.maxyearAD and
                     value > date.maxyearAD[sitelang]):
                pywikibot.output(
                    u'TitleTranslate: %s was recognized as %s with value %d'
                    % (page.title(), dictName, value))
                for entryLang, entry in date.formats[dictName].items():
                    if entryLang != sitelang:
                        if (dictName == 'yearsBC' and
                                entryLang in date.maxyearBC and
                                value > date.maxyearBC[entryLang]):
                            pass
                        elif (dictName == 'yearsAD' and
                              entryLang in date.maxyearAD and
                              value > date.maxyearAD[entryLang]):
                            pass
                        else:
                            newname = entry(value)
                            x = pywikibot.Link(
                                newname,
                                pywikibot.Site(code=entryLang,
                                               fam=site.family))
                            result.add(x)
    return list(result)

bcDateErrors = [u'[[ko:%d년]]']


def appendFormatedDates(result, dictName, value):
    for code, func in date.formats[dictName].items():
        result.append(u'[[%s:%s]]' % (code, func(value)))


def getPoisonedLinks(pl):
    """Return a list of known corrupted links that should be removed if seen."""
    result = []
    pywikibot.output(u'getting poisoned links for %s' % pl.title())
    dictName, value = date.getAutoFormat(pl.site.code, pl.title())
    if dictName is not None:
        pywikibot.output(u'date found in %s' % dictName)
        # errors in year BC
        if dictName in date.bcFormats:
            for fmt in bcDateErrors:
                result.append(fmt % value)
        # i guess this is like friday the 13th for the years
        if value == 398 and dictName == 'yearsBC':
            appendFormatedDates(result, dictName, 399)
        if dictName == 'yearsBC':
            appendFormatedDates(result, 'decadesBC', value)
            appendFormatedDates(result, 'yearsAD', value)
        if dictName == 'yearsAD':
            appendFormatedDates(result, 'decadesAD', value)
            appendFormatedDates(result, 'yearsBC', value)
        if dictName == 'centuriesBC':
            appendFormatedDates(result, 'decadesBC', value * 100 + 1)
        if dictName == 'centuriesAD':
            appendFormatedDates(result, 'decadesAD', value * 100 + 1)
    return result
