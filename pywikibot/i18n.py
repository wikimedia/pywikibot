# -*- coding: utf-8  -*-
""" Various i18n functions, both for the internal translation system
    and for TranslateWiki-based translations
"""
#
# (C) Pywikipedia bot team, 2004-2011
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import re
from pywikibot import Error
from plural import plural_rules

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
    if code == 'lb':
        return ['de', 'fr']
    if code == 'als':
        return ['gsw', 'de']
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
    #Latvian
    if code == 'ltg':
        return ['lv']
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
    if code in ['ab', 'av', 'ba', 'bxr', 'ce', 'cv', 'kbd', 'kk', 'koi', 'ky',
                'lbe', 'mdf', 'mhr', 'mrj', 'myv', 'os', 'rue', 'sah', 'tg',
                'udm', 'uk', 'xal']:
        return ['ru']
    if code == 'tt':
        return ['tt-cyrl', 'ru']
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
        return ['ku', 'ku-latn', 'tr']
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
    if code == 'xmf':
        return ['ka']
    if code in ['nso', 'st']:
        return ['st', 'nso']
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
    if hasattr(code, 'lang'):
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

    code_needed = False
    # If a site is given instead of a code, use its language
    if hasattr(code, 'lang'):
        lang = code.lang
    # check whether we need the language code back
    elif type(code) == list:
        lang = code.pop()
        code_needed = True
    else:
        lang = code

    # There are two possible failure modes: the translation dict might not have
    # the language altogether, or a specific key could be untranslated. Both
    # modes are caught with the KeyError.

    trans = None
    try:
        trans = transdict[lang][twtitle]
    except KeyError:
        # try alternative languages and English
        for alt in _altlang(lang) + ['en']:
            try:
                trans = transdict[alt][twtitle]
                if code_needed:
                    lang = alt
                break
            except KeyError:
                continue
        if not trans:
            raise TranslationError("No English translation has been defined for TranslateWiki key %r" % twtitle)
    # send the language code back via the given list
    if code_needed:
        code.append(lang)
    if parameters:
        return trans % parameters
    else:
        return trans

# Maybe this function should be merged with twtranslate
def twntranslate(code, twtitle, parameters=None):
    """ First implementation of plural support for translations based on the
    TW title twtitle, which corresponds to a page on TW.

    @param code The language code
    @param twtitle The TranslateWiki string title, in <package>-<key> format
    @param parameters For passing parameters.

    Support is implemented like in MediaWiki extension. If the tw message
    contains a plural tag inside which looks like
    {{PLURAL:<number>|<variant1>|<variant2>[|<variantn>]}}
    it takes that variant calculated by the plural_func depending on the number
    value. At the moment, we have only one plural_func = x: x!= 1 yet. Multiple
    PLURAL tags are not supported (yet).

    Examples:
    If we had a test dictionary in test.py like
    msg = {
        'de': {
            'test-changing': u'Bot: Ändere %(num)d {{PLURAL:num|Seite|Seiten}}.',
        },
        'en': {
            # number value as format sting is allowed
            'test-changing': u'Bot: Changing %(num)s {{PLURAL:%(num)d|page|pages}}.',
        },
        'nl': {
            # format sting inside PLURAL tag is allowed
            'test-changing': u'Bot: Endrer {{PLURAL:num|1 pagina|%(num)d pagina\'s}}.',
        },
        'fr': {
            # additional sting inside or outside PLURAL tag is allowed
            'test-changing': u'Robot: Changer %(descr)s {{PLURAL:num|une page|un peu pages}}.',
        },
    }
    #use a number
    >>> i18n.twntranslate('en', 'test-changing', 0) % {'num': 'no'}
    Bot: Changing no pages.
    #use a string
    >>> i18n.twntranslate('en', 'test-changing', '1') % {'num': 'one'}
    Bot: Changing one page.
    #use a dictionary
    >>> i18n.twntranslate('en', 'test-changing', {'num':2})
    Bot: Changing 2 pages.
    #use additional format strings
    >>> i18n.twntranslate('fr', 'test-changing', {'num':1, 'descr':'seulement'})
    Bot: Changer seulement une pages.
    #use format strings also outside
    >>> i18n.twntranslate('fr', 'test-changing', 0) % {'descr':'seulement'}
    Bot: Changer seulement un peu pages.

    The translations are retrieved from i18n.<package>, based on the callers
    import table.
    """
    PATTERN = '{{PLURAL:(?:%\()?([^\)]*?)(?:\)d)?\|(.*?)}}'
    param = None
    if type(parameters) == dict:
        param = parameters
    # If a site is given instead of a code, use its language
    if hasattr(code, 'lang'):
        code = code.lang
    # we send the code via list and get the alternate code back
    code = [code]
    trans = twtranslate(code, twtitle, None)
    try:
        selector, variants = re.search(PATTERN, trans).groups()
    # No PLURAL tag found: nothing to replace
    except AttributeError:
        pass
    else:
        if type(parameters) == dict:
            num = param[selector]
        elif type(parameters) == basestring:
            num = int(parameters)
        else:
            num = parameters
        # get the alternate language code modified by twtranslate
        lang = code.pop()
        # we only need the lang or _default, not a _altlang code
        # maybe we should implement this to i18n.translate()
        try:
            plural_func = plural_rules[lang]['plural']
        except KeyError:
            plural_func = plural_rules['_default']['plural']
        # TODO: check against plural_rules[lang]['nplurals']
        repl = variants.split('|')[plural_func(num)]
        trans = re.sub(PATTERN, repl, trans)
    if param:
        try:
            return trans % param
        except KeyError:
            pass
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
    # If a site is given instead of a code, use its language
    if hasattr(code, 'lang'):
        code = code.lang
    return code in transdict and twtitle in transdict[code]
