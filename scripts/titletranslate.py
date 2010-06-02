# -*- coding: utf-8  -*-
#
# (C) Rob W.W. Hooft, 2003
# (C) Yuri Astrakhan, 2005
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#
import re

import pywikibot, time
import pywikibot.date as date

def translate(page, hints = None, auto = True, removebrackets = False):
    """
    Please comment your source code! --Daniel

    Does some magic stuff. Returns a list of Links.
    """
    result = []
    site = page.site
    if hints:
        for h in hints:
            if h.find(':') == -1:
                # argument given as -hint:xy where xy is a language code
                codes = h
                newname = ''
            else:
                codes, newname = h.split(':', 1)
            if newname == '':
                # if given as -hint:xy or -hint:xy:, assume that there should
                # be a page in language xy with the same title as the page
                # we're currently working on ...
                ns = page.namespace()
                if ns:
                    newname = u'%s:%s' % (site.family.namespace('_default', ns), page.title(withNamespace=False))
                else:
                    # article in the main namespace
                    newname = page.title()
                # ... unless we do want brackets
                if removebrackets:
                    newname = re.sub(re.compile(ur"\W*?\(.*?\)\W*?", re.UNICODE), u" ", newname)
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
                        x = pywikibot.Link(site.getSite(code=newcode), newname)
                        if x not in result:
                            result.append(x)
                else:
                    if pywikibot.verbose:
                        pywikibot.output(u"Ignoring unknown language code %s"%newcode)

    # Autotranslate dates into all other languages, the rest will come from existing interwiki links.
    if auto:
        # search inside all dictionaries for this link
        dictName, value = date.getAutoFormat( page.site.code, page.title() )
        if dictName:
            if not (dictName == 'yearsBC' and date.maxyearBC.has_key(page.site.code) and value > date.maxyearBC[page.site.code]) or (dictName == 'yearsAD' and date.maxyearAD.has_key(page.site.code) and value > date.maxyearAD[page.site.code]):
                pywikibot.output(u'TitleTranslate: %s was recognized as %s with value %d' % (page.title(),dictName,value))
                for entryLang, entry in date.formats[dictName].iteritems():
                    if entryLang != page.site.code:
                        if dictName == 'yearsBC' and date.maxyearBC.has_key(entryLang) and value > date.maxyearBC[entryLang]:
                            pass
                        elif dictName == 'yearsAD' and date.maxyearAD.has_key(entryLang) and value > date.maxyearAD[entryLang]:
                            pass
            else:
                            newname = entry(value)
                            x = pywikibot.Link( newname, pywikibot.getSite(code=entryLang, fam=site.family) )
                            if x not in result:
                                result.append(x) # add new page
    return result

bcDateErrors = [u'[[ko:%d년]]']

def appendFormatedDates( result, dictName, value ):
    for code, func in date.formats[dictName].iteritems():
        result.append( u'[[%s:%s]]' % (code,func(value)) )

def getPoisonedLinks(pl):
    """Returns a list of known corrupted links that should be removed if seen
    """
    result = []

    pywikibot.output( u'getting poisoned links for %s' % pl.title() )

    dictName, value = date.getAutoFormat( pl.site.code, pl.title() )
    if dictName is not None:
        pywikibot.output( u'date found in %s' % dictName )

        # errors in year BC
        if dictName in date.bcFormats:
            for fmt in bcDateErrors:
                result.append( fmt % value )

        # i guess this is like friday the 13th for the years
        if value == 398 and dictName == 'yearsBC':
            appendFormatedDates( result, dictName, 399 )

        if dictName == 'yearsBC':
            appendFormatedDates( result, 'decadesBC', value )
            appendFormatedDates( result, 'yearsAD', value )

        if dictName == 'yearsAD':
            appendFormatedDates( result, 'decadesAD', value )
            appendFormatedDates( result, 'yearsBC', value )

        if dictName == 'centuriesBC':
            appendFormatedDates( result, 'decadesBC', value*100+1 )

        if dictName == 'centuriesAD':
            appendFormatedDates( result, 'decadesAD', value*100+1 )

    return result
