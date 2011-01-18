# -*- coding: utf-8  -*-
""" Various i18n functions, both for the internal translation system
    and for TranslateWiki-based translations
"""
#
# (C) Pywikipedia bot team, 2004-2011
#
# Distributed under the terms of the MIT license.
#

from pywikibot import Error

# Languages to use for comment text after the actual language but before
# en:. For example, if for language 'xx', you want the preference of
# languages to be:
# xx:, then fr:, then ru:, then en:
# you let altlang return ['fr','ru'].
# This code is used by translate() and twtranslate() below.

def _altlang(code):
    """Define fallback languages for particular languages.

    If no translation is available to a specified language, translate() will
    try each of the specified fallback languages, in order, until it finds
    one with a translation, with 'en' and '_default' as a last resort.
    
    For example, if for language 'xx', you want the preference of languages
    to be: xx > fr > ru > en, you let altlang return ['fr', 'ru'].
    """
    #Amharic
    if code in ['aa', 'om']:
        return ['am']
    #Arab
    if code in ['arc', 'arz']:
        return ['ar']
    if code == 'kab':
        return ['ar', 'fr']
    #Bulgarian
    if code in ['cu', 'mk']:
        return ['bg', 'sr', 'sh']
    #Czech
    if code in ['cs', 'sk']:
        return ['cs', 'sk']
    #German
    if code in ['bar', 'frr', 'ksh', 'pdc', 'pfl']:
        return ['de']
    if code in ['als', 'lb']:
        return ['de', 'fr']
    if code == 'nds':
        return ['nds-nl', 'de']
    if code in ['dsb', 'hsb']:
        return ['hsb', 'dsb', 'de']
    if code == 'rm':
        return ['de', 'it']
    if code =='stq':
        return ['nds', 'de']
    #Greek
    if code == 'pnt':
        return ['el']
    #Esperanto
    if code in ['io', 'nov']:
        return ['eo']
    #Spanish
    if code in ['an', 'ast', 'ay', 'ca', 'ext', 'lad', 'nah', 'nv', 'qu']:
        return ['es']
    if code in ['gl', 'gn']:
        return ['es', 'pt']
    if code == ['eu']:
        return ['es', 'fr']
    if code in ['bcl', 'cbk-zam', 'ceb', 'ilo', 'pag', 'pam', 'tl', 'war']:
        return ['es', 'tl']
    #Estonian
    if code == 'fiu-vro':
        return ['et']
    #Persian (Farsi)
    if code in ['glk', 'mzn']:
        return ['ar']
    #French
    if code in ['bm', 'br', 'ht', 'kab', 'kg', 'ln', 'mg', 'nrm', 'oc',
                'pcd', 'rw', 'sg', 'ty', 'wa']:
        return ['fr']
    if code == 'co':
        return ['fr', 'it']
    #Hindi
    if code in ['bh', 'pi', 'sa']:
        return ['hi']
    if code in ['ne', 'new']:
        return ['ne', 'new', 'hi']
    #Indonesian and Malay
    if code in ['ace', 'bug', 'bjn', 'id', 'jv', 'ms', 'su']:
        return ['id', 'ms', 'jv']
    if code == 'map-bms':
        return ['jv', 'id', 'ms']
    #Inuit languages
    if code in ['ik', 'iu']:
        return ['iu', 'kl']
    if code == 'kl':
        return ['iu', 'da', 'no']
    #Italian
    if code in ['eml', 'fur', 'lij', 'lmo', 'nap', 'pms', 'roa-tara', 'sc',
                'scn', 'vec']:
        return ['it']
    if code == 'frp':
        return ['it', 'fr']
    #Lithuanian
    if code in ['bat-smg', 'ltg']:
        return ['lt']
    #Dutch
    if code in ['fy', 'li', 'pap', 'srn', 'vls', 'zea']:
        return ['nl']
    if code == ['nds-nl']:
        return ['nds', 'nl']
    #Polish
    if code in ['csb', 'szl']:
        return ['pl']
    #Portuguese
    if code in ['fab', 'mwl', 'tet']:
        return ['pt']
    #Romanian
    if code in ['mo', 'roa-rup']:
        return ['ro']
    #Russian and Belarusian
    if code in ['ab', 'av', 'ba', 'bxr', 'ce', 'cv', 'kk', 'koi', 'ky', 'lbe',
                'mdf', 'mhr', 'mrj', 'myv', 'os', 'sah', 'tg', 'tt', 'udm',
                'uk', 'xal']:
        return ['ru']
    if code in ['be', 'be-x-old']:
        return ['be', 'be-x-old', 'ru']
    if code == 'kaa':
        return ['uz', 'ru']
    #Serbocroatian
    if code in ['bs', 'hr', 'sh',]:
        return ['sh', 'hr', 'bs', 'sr', 'sr-el']
    if code == 'sr':
        return ['sr-el', 'sh', 'hr', 'bs']
    #Turkish and Kurdish
    if code in ['diq', 'ku']:
        return ['ku', 'tr']
    if code == 'gag':
        return ['tr']
    if code == 'ckb':
        return ['ku', 'ar']
    #Chinese
    if code in ['minnan', 'zh', 'zh-classical', 'zh-min-nan', 'zh-tw',
                'zh-hans', 'zh-hant']:
        return ['zh', 'zh-tw', 'zh-cn', 'zh-classical']
    if code in ['cdo', 'gan', 'hak', 'ii', 'wuu', 'za', 'zh-cdo',
                'zh-classical', 'zh-cn', 'zh-yue']:
        return ['zh', 'zh-cn', 'zh-tw', 'zh-classical']
    #Scandinavian languages
    if code in ['da', 'sv']:
        return ['da', 'no', 'nb', 'sv', 'nn']
    if code in ['fo', 'is']:
        return ['da', 'no', 'nb', 'nn', 'sv']
    if code == 'nn':
        return ['no', 'nb', 'sv', 'da']
    if code in ['nb', 'no']:
        return ['no', 'nb', 'da', 'nn', 'sv']
    if code == 'se':
        return ['sv', 'no', 'nb', 'nn', 'fi']
    #Other languages
    if code in ['bi', 'tpi']:
        return ['bi', 'tpi']
    if code == 'yi':
        return ['he', 'de']
    if code in ['ia', 'ie']:
        return ['ia', 'la', 'it', 'fr', 'es']
    #Default value
    return []

def translate(code, xdict):
    """Return the most appropriate translation from a translation dict.

    Given a language code and a dictionary, returns the dictionary's value for
    key 'code' if this key exists; otherwise tries to return a value for an
    alternative language that is most applicable to use on the Wikipedia in
    language 'code'.

    The language itself is always checked first, then languages that
    have been defined to be alternatives, and finally English. If none of
    the options gives result, we just take the first language in the
    list.

    """
    # If a site is given instead of a code, use its language
    if hasattr(code,'lang'):
        code = code.lang

    if code in xdict:
        return xdict[code]
    for alt in _altlang(code):
        if alt in xdict:
            return xdict[alt]
    if '_default' in xdict:
        return xdict['_default']
    elif 'en' in xdict:
        return xdict['en']
    return xdict.values()[0]


class TranslationError(Error):
    """ Raised when no correct translation could be found """
    pass

def twtranslate(code, twtitle, parameters=None):
    """ Uses TranslateWiki files to provide translations based on the TW title
        twtitle, which corresponds to a page on TW.

        @param code The language code
        @param twtitle The TranslateWiki string title, in <package>-<key> format
        @param parameters For passing parameters. In the future, this will
                          be used for plural support.

        The translations are retrieved from i18n.<package>, based on the callers
        import table.
    """
    package = twtitle.split("-")[0]
    transdict = getattr(__import__("i18n", fromlist=[package]), package).msg

    # There are two possible failure modes: the translation dict might not have
    # the language altogether, or a specific key could be untranslated. Both
    # modes are caught with the KeyError.
    
    trans = None
    try:
        trans = transdict[code][twtitle]
    except KeyError:
        # try alternative languages and English
        for alt in _altlang(code) + ['en']:
            try:
                trans = transdict[alt][twtitle]
                break
            except KeyError:
                continue
        if not trans:
            raise TranslationError("No English translation has been defined for TranslateWiki key %r" % twtitle)

    if parameters:
        return trans % parameters
    else:
        return trans

def twhas_key(code, twtitle):
    """ Uses TranslateWiki files to to check whether specified translation
        based on the TW title is provided. No code fallback is made.

        @param code The language code
        @param twtitle The TranslateWiki string title, in <package>-<key> format

        The translations are retrieved from i18n.<package>, based on the callers
        import table.
    """
    package = twtitle.split("-")[0]
    transdict = getattr(__import__("i18n", fromlist=[package]), package).msg
    return code in transdict and twtitle in transdict[code]
