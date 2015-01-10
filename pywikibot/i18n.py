# -*- coding: utf-8  -*-
"""
Various i18n functions.

Helper functions for both the internal translation system
and for TranslateWiki-based translations.
"""
#
# (C) Pywikibot team, 2004-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import sys
import re
import locale
from pywikibot import Error
from .plural import plural_rules
import pywikibot
from . import config2 as config

if sys.version_info[0] > 2:
    basestring = (str, )

PLURAL_PATTERN = '{{PLURAL:(?:%\()?([^\)]*?)(?:\)d)?\|(.*?)}}'

# Package name for the translation messages
messages_package_name = 'scripts.i18n'


def _altlang(code):
    """Define fallback languages for particular languages.

    If no translation is available to a specified language, translate() will
    try each of the specified fallback languages, in order, until it finds
    one with a translation, with 'en' and '_default' as a last resort.

    For example, if for language 'xx', you want the preference of languages
    to be: xx > fr > ru > en, you let this method return ['fr', 'ru'].

    This code is used by other translating methods below.

    @param code: The language code
    @type code: string
    @return: language codes
    @rtype: list of str
    """
    # Akan
    if code in ['ak', 'tw']:
        return ['ak', 'tw']
    # Amharic
    if code in ['aa', 'ti']:
        return ['am']
    # Arab
    if code in ['arc', 'arz', 'so']:
        return ['ar']
    if code == 'kab':
        return ['ar', 'fr']
    # Bulgarian
    if code in ['cu', 'mk']:
        return ['bg', 'sr', 'sh']
    # Czech
    if code in ['cs', 'sk']:
        return ['cs', 'sk']
    # German
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
    if code == 'sli':
        return ['de', 'pl']
    if code == 'rm':
        return ['de', 'it']
    if code == 'stq':
        return ['nds', 'de']
    # Greek
    if code in ['grc', 'pnt']:
        return ['el']
    # Esperanto
    if code in ['io', 'nov']:
        return ['eo']
    # Spanish
    if code in ['an', 'arn', 'ast', 'ay', 'ca', 'ext', 'lad', 'nah', 'nv', 'qu',
                'yua']:
        return ['es']
    if code in ['gl', 'gn']:
        return ['es', 'pt']
    if code == 'eu':
        return ['es', 'fr']
    if code == 'cbk-zam':
        return ['es', 'tl']
    # Estonian
    if code == 'fiu-vro':
        return ['et']
    if code == 'liv':
        return ['et', 'lv']
    # Persian (Farsi)
    if code == 'ps':
        return ['fa']
    if code in ['glk', 'mzn']:
        return ['glk', 'mzn', 'fa', 'ar']
    # Finnish
    if code == 'vep':
        return ['fi', 'ru']
    if code == 'fit':
        return ['fi', 'sv']
    # French
    if code in ['bm', 'br', 'ht', 'kg', 'ln', 'mg', 'nrm', 'pcd',
                'rw', 'sg', 'ty', 'wa']:
        return ['fr']
    if code == 'oc':
        return ['fr', 'ca', 'es']
    if code in ['co', 'frp']:
        return ['fr', 'it']
    # Hindi
    if code in ['sa']:
        return ['hi']
    if code in ['ne', 'new']:
        return ['ne', 'new', 'hi']
    # Indonesian and Malay
    if code in ['ace', 'bug', 'bjn', 'id', 'jv', 'ms', 'su']:
        return ['id', 'ms', 'jv']
    if code == 'map-bms':
        return ['jv', 'id', 'ms']
    # Inuit languages
    if code in ['ik', 'iu']:
        return ['iu', 'kl']
    if code == 'kl':
        return ['da', 'iu', 'no']
    # Italian
    if code in ['eml', 'fur', 'lij', 'lmo', 'nap', 'pms', 'roa-tara', 'sc',
                'scn', 'vec']:
        return ['it']
    # Lithuanian
    if code in ['bat-smg']:
        return ['lt']
    # Latvian
    if code == 'ltg':
        return ['lv']
    # Dutch
    if code in ['af', 'fy', 'li', 'pap', 'srn', 'vls', 'zea']:
        return ['nl']
    if code == ['nds-nl']:
        return ['nds', 'nl']
    # Polish
    if code in ['csb', 'szl']:
        return ['pl']
    # Portuguese
    if code in ['fab', 'mwl', 'tet']:
        return ['pt']
    # Romanian
    if code in ['mo', 'roa-rup']:
        return ['ro']
    # Russian and Belarusian
    if code in ['ab', 'av', 'ba', 'bxr', 'ce', 'cv', 'inh', 'kk', 'koi', 'krc',
                'kv', 'ky', 'lbe', 'lez', 'mdf', 'mhr', 'mn', 'mrj', 'myv',
                'os', 'sah', 'tg', 'udm', 'uk', 'xal']:
        return ['ru']
    if code in ['kbd', 'ady']:
        return ['kbd', 'ady', 'ru']
    if code == 'tt':
        return ['tt-cyrl', 'ru']
    if code in ['be', 'be-x-old']:
        return ['be', 'be-x-old', 'ru']
    if code == 'kaa':
        return ['uz', 'ru']
    # Serbocroatian
    if code in ['bs', 'hr', 'sh']:
        return ['sh', 'hr', 'bs', 'sr', 'sr-el']
    if code == 'sr':
        return ['sr-el', 'sh', 'hr', 'bs']
    # Tagalog
    if code in ['bcl', 'ceb', 'ilo', 'pag', 'pam', 'war']:
        return ['tl']
    # Turkish and Kurdish
    if code in ['diq', 'ku']:
        return ['ku', 'ku-latn', 'tr']
    if code == 'gag':
        return ['tr']
    if code == 'ckb':
        return ['ku']
    # Ukrainian
    if code in ['crh', 'rue']:
        return ['uk', 'ru']
    # Chinese
    if code in ['minnan', 'zh', 'zh-classical', 'zh-min-nan', 'zh-tw',
                'zh-hans', 'zh-hant']:
        return ['zh', 'zh-tw', 'zh-cn', 'zh-classical']
    if code in ['cdo', 'gan', 'hak', 'ii', 'wuu', 'za', 'zh-cdo',
                'zh-classical', 'zh-cn', 'zh-yue']:
        return ['zh', 'zh-cn', 'zh-tw', 'zh-classical']
    # Scandinavian languages
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
    # Other languages
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
    if code in ['kj', 'ng']:
        return ['kj', 'ng']
    if code in ['meu', 'hmo']:
        return ['meu', 'hmo']
    if code == ['as']:
        return ['bn']
    # Default value
    return []


class TranslationError(Error):

    """Raised when no correct translation could be found."""

    pass


def _extract_plural(code, message, parameters):
    """Check for the plural variants in message and replace them.

    @param message: the message to be replaced
    @type message: unicode string
    @param parameters: plural parameters passed from other methods
    @type parameters: int, basestring, tuple, list, dict

    """
    plural_items = re.findall(PLURAL_PATTERN, message)
    if plural_items:  # we found PLURAL patterns, process it
        if len(plural_items) > 1 and isinstance(parameters, (tuple, list)) and \
           len(plural_items) != len(parameters):
            raise ValueError("Length of parameter does not match PLURAL "
                             "occurrences.")
        i = 0
        for selector, variants in plural_items:
            if isinstance(parameters, dict):
                num = int(parameters[selector])
            elif isinstance(parameters, basestring):
                num = int(parameters)
            elif isinstance(parameters, (tuple, list)):
                num = int(parameters[i])
                i += 1
            else:
                num = parameters
            # TODO: check against plural_rules[code]['nplurals']
            try:
                index = plural_rules[code]['plural'](num)
            except KeyError:
                index = plural_rules['_default']['plural'](num)
            except TypeError:
                # we got an int, not a function
                index = plural_rules[code]['plural']
            repl = variants.split('|')[index]
            message = re.sub(PLURAL_PATTERN, repl, message, count=1)
    return message


def translate(code, xdict, parameters=None, fallback=False):
    """Return the most appropriate translation from a translation dict.

    Given a language code and a dictionary, returns the dictionary's value for
    key 'code' if this key exists; otherwise tries to return a value for an
    alternative language that is most applicable to use on the wiki in
    language 'code' except fallback is False.

    The language itself is always checked first, then languages that
    have been defined to be alternatives, and finally English. If none of
    the options gives result, we just take the first language in the
    list.

    For PLURAL support have a look at the twntranslate method

    @param code: The language code
    @type code: string or Site object
    @param xdict: dictionary with language codes as keys or extended dictionary
                  with family names as keys containing language dictionaries or
                  a single (unicode) string. May contain PLURAL tags as
                  described in twntranslate
    @type xdict: dict, string, unicode
    @param parameters: For passing (plural) parameters
    @type parameters: dict, string, unicode, int
    @param fallback: Try an alternate language code
    @type fallback: boolean

    """
    family = pywikibot.config.family
    # If a site is given instead of a code, use its language
    if hasattr(code, 'code'):
        family = code.family.name
        code = code.code

    # Check whether xdict has multiple projects
    if isinstance(xdict, dict):
        if family in xdict:
            xdict = xdict[family]
        elif 'wikipedia' in xdict:
            xdict = xdict['wikipedia']

    # Get the translated string
    trans = None
    if not isinstance(xdict, dict):
        trans = xdict
    elif code in xdict:
        trans = xdict[code]
    elif fallback:
        for alt in _altlang(code) + ['_default', 'en']:
            if alt in xdict:
                trans = xdict[alt]
                code = alt
                break
        else:
            trans = list(xdict.values())[0]
            code = list(xdict.keys())[0]
    if trans is None:
        return  # return None if we have no translation found
    if parameters is None:
        return trans

    # else we check for PLURAL variants
    trans = _extract_plural(code, trans, parameters)
    if parameters:
        try:
            return trans % parameters
        except (KeyError, TypeError):
            # parameter is for PLURAL variants only, don't change the string
            pass
    return trans


def twtranslate(code, twtitle, parameters=None, fallback=True):
    """
    Translate a message.

    The translations are retrieved from i18n.<package>, based on the callers
    import table.

    fallback parameter must be True for i18n and False for L10N or testing
    purposes.

    @param code: The language code
    @param twtitle: The TranslateWiki string title, in <package>-<key> format
    @param parameters: For passing parameters.
    @param fallback: Try an alternate language code
    @type fallback: boolean
    """
    package = twtitle.split("-")[0]
    transdict = getattr(__import__(messages_package_name, fromlist=[package]),
                        package).msg

    code_needed = False
    # If a site is given instead of a code, use its language
    if hasattr(code, 'code'):
        lang = code.code
    # check whether we need the language code back
    elif isinstance(code, list):
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
        if fallback:
            for alt in _altlang(lang) + ['en']:
                try:
                    trans = transdict[alt][twtitle]
                    if code_needed:
                        lang = alt
                    break
                except KeyError:
                    continue
            if trans is None:
                raise TranslationError(
                    "No English translation has been defined "
                    "for TranslateWiki key %r" % twtitle)
    # send the language code back via the given list
    if code_needed:
        code.append(lang)
    if parameters:
        return trans % parameters
    else:
        return trans


# Maybe this function should be merged with twtranslate
def twntranslate(code, twtitle, parameters=None):
    r"""Translate a message with plural support.

    Support is implemented like in MediaWiki extension. If the TranslateWiki
    message contains a plural tag inside which looks like::

        {{PLURAL:<number>|<variant1>|<variant2>[|<variantn>]}}

    it takes that variant calculated by the plural_rules depending on the number
    value. Multiple plurals are allowed.

    As an examples, if we had a test dictionary in test.py like::

        msg = {
            'en': {
                # number value as format string is allowed
                'test-plural': u'Bot: Changing %(num)s {{PLURAL:%(num)d|page|pages}}.',
            },
            'nl': {
                # format string inside PLURAL tag is allowed
                'test-plural': u'Bot: Pas {{PLURAL:num|1 pagina|%(num)d pagina\'s}} aan.',
            },
            'fr': {
                # additional string inside or outside PLURAL tag is allowed
                'test-plural': u'Robot: Changer %(descr)s {{PLURAL:num|une page|quelques pages}}.',
            },
        }

    >>> from pywikibot import i18n
    >>> i18n.messages_package_name = 'tests.i18n'
    >>> # use a number
    >>> str(i18n.twntranslate('en', 'test-plural', 0) % {'num': 'no'})
    'Bot: Changing no pages.'
    >>> # use a string
    >>> str(i18n.twntranslate('en', 'test-plural', '1') % {'num': 'one'})
    'Bot: Changing one page.'
    >>> # use a dictionary
    >>> str(i18n.twntranslate('en', 'test-plural', {'num':2}))
    'Bot: Changing 2 pages.'
    >>> # use additional format strings
    >>> str(i18n.twntranslate('fr', 'test-plural', {'num': 1, 'descr': 'seulement'}))
    'Robot: Changer seulement une page.'
    >>> # use format strings also outside
    >>> str(i18n.twntranslate('fr', 'test-plural', 10) % {'descr': 'seulement'})
    'Robot: Changer seulement quelques pages.'
    >>> i18n.messages_package_name = 'scripts.i18n'

    The translations are retrieved from i18n.<package>, based on the callers
    import table.

    @param code: The language code
    @param twtitle: The TranslateWiki string title, in <package>-<key> format
    @param parameters: For passing (plural) parameters.

    """
    # If a site is given instead of a code, use its language
    if hasattr(code, 'code'):
        code = code.code
    # we send the code via list and get the alternate code back
    code = [code]
    trans = twtranslate(code, twtitle)
    # get the alternate language code modified by twtranslate
    lang = code.pop()
    # check for PLURAL variants
    trans = _extract_plural(lang, trans, parameters)
    # we always have a dict for replacement of translatewiki messages
    if parameters and isinstance(parameters, dict):
        try:
            return trans % parameters
        except KeyError:
            # parameter is for PLURAL variants only, don't change the string
            pass
    return trans


def twhas_key(code, twtitle):
    """
    Check if a message has a translation in the specified language code.

    The translations are retrieved from i18n.<package>, based on the callers
    import table.

    No code fallback is made.

    @param code: The language code
    @param twtitle: The TranslateWiki string title, in <package>-<key> format
    """
    package = twtitle.split("-")[0]
    transdict = getattr(__import__(messages_package_name, fromlist=[package]),
                        package).msg
    # If a site is given instead of a code, use its language
    if hasattr(code, 'code'):
        code = code.code
    return code in transdict and twtitle in transdict[code]


def twget_keys(twtitle):
    """
    Return all language codes for a special message.

    @param twtitle: The TranslateWiki string title, in <package>-<key> format
    """
    package = twtitle.split("-")[0]
    transdict = getattr(__import__(messages_package_name, fromlist=[package]),
                        package).msg
    return (lang for lang in sorted(transdict.keys()) if lang != 'qqq')


def input(twtitle, parameters=None, password=False):
    """
    Ask the user a question, return the user's answer.

    The prompt message is retrieved via L{twtranslate} and either uses the
    config variable 'userinterface_lang' or the default locale as the language
    code.

    @param twtitle: The TranslateWiki string title, in <package>-<key> format
    @param parameters: The values which will be applied to the translated text
    @param password: Hides the user's input (for password entry)
    @rtype: unicode string
    """
    code = config.userinterface_lang or \
           locale.getdefaultlocale()[0].split('_')[0]
    trans = twtranslate(code, twtitle, parameters)
    return pywikibot.input(trans, password)
