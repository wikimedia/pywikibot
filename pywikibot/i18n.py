# -*- coding: utf-8  -*-
"""
Various i18n functions.

Helper functions for both the internal translation system
and for TranslateWiki-based translations.

By default messages are assumed to reside in a package called
'scripts.i18n'.  In pywikibot 2.0, that package is not packaged
with pywikibot, and pywikibot 2.0 does not have a hard dependency
on any i18n messages.  However, there are three user input questions
in pagegenerators which will use i18 messages if they can be loaded.

The default message location may be changed by calling
L{set_message_package} with a package name.  The package must contain
an __init__.py, and a message bundle called 'pywikibot' containing
messages.  See L{twntranslate} for more information on the messages.
"""
#
# (C) Pywikibot team, 2004-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import sys
import re
import locale
import json
import os
import pkgutil

from collections import defaultdict

from pywikibot import Error
from .plural import plural_rules

import pywikibot

from . import config2 as config

if sys.version_info[0] > 2:
    basestring = (str, )

PLURAL_PATTERN = r'{{PLURAL:(?:%\()?([^\)]*?)(?:\)d)?\|(.*?)}}'

# Package name for the translation messages.  The messages data must loaded
# relative to that package name.  In the top of this package should be
# directories named after for each script/message bundle, and each directory
# should contain JSON files called <lang>.json
_messages_package_name = 'scripts.i18n'
# Flag to indicate whether translation messages are available
_messages_available = None

# Cache of translated messages
_cache = defaultdict(dict)


def set_messages_package(package_name):
    """Set the package name where i18n messages are located."""
    global _messages_package_name
    global _messages_available
    _messages_package_name = package_name
    _messages_available = None


def messages_available():
    """
    Return False if there are no i18n messages available.

    To determine if messages are available, it looks for the package name
    set using L{set_messages_package} for a message bundle called 'pywikibot'
    containing messages.

    @rtype: bool
    """
    global _messages_available
    if _messages_available is not None:
        return _messages_available
    try:
        __import__(_messages_package_name)
    except ImportError:
        _messages_available = False
        return False

    _messages_available = True
    return True


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
    if code in ['als', 'gsw']:
        return ['als', 'gsw', 'de']
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
    if code in ['fiu-vro', 'vro']:
        return ['fiu-vro', 'vro', 'et']
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
    if code in ['bh', 'bho']:
        return ['bh', 'bho']
    # Indonesian and Malay
    if code in ['ace', 'bug', 'bjn', 'id', 'jv', 'ms', 'su']:
        return ['id', 'ms', 'jv']
    if code == 'map-bms':
        return ['jv', 'id', 'ms']
    # Inuit languages
    if code in ['ik', 'iu']:
        return ['iu', 'kl']
    if code == 'kl':
        return ['da', 'iu', 'no', 'nb']
    # Italian
    if code in ['eml', 'fur', 'lij', 'lmo', 'nap', 'pms', 'roa-tara', 'sc',
                'scn', 'vec']:
        return ['it']
    # Lithuanian
    if code in ['bat-smg', 'sgs']:
        return ['bat-smg', 'sgs', 'lt']
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
    if code in ['roa-rup', 'rup']:
        return ['roa-rup', 'rup', 'ro']
    if code == 'mo':
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
    if code in ['be', 'be-x-old', 'be-tarask']:
        return ['be', 'be-x-old', 'be-tarask', 'ru']
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
    if code in ['crh', 'crh-latn']:
        return ['crh', 'crh-latn', 'uk', 'ru']
    if code in ['rue']:
        return ['uk', 'ru']
    # Chinese
    if code in ['zh-classical', 'lzh', 'minnan', 'zh-min-nan', 'nan', 'zh-tw',
                'zh', 'zh-hans']:
        return ['zh', 'zh-hans', 'zh-tw', 'zh-cn', 'zh-classical', 'lzh']
    if code in ['cdo', 'gan', 'hak', 'ii', 'wuu', 'za', 'zh-classical', 'lzh',
                'zh-cn', 'zh-yue', 'yue']:
        return ['zh', 'zh-hans' 'zh-cn', 'zh-tw', 'zh-classical', 'lzh']
    # Scandinavian languages
    if code in ['da', 'sv']:
        return ['da', 'no', 'nb', 'sv', 'nn']
    if code in ['fo', 'is']:
        return ['da', 'no', 'nb', 'nn', 'sv']
    if code == 'nn':
        return ['no', 'nb', 'sv', 'da']
    if code in ['no', 'nb']:
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


class TranslationError(Error, ImportError):

    """Raised when no correct translation could be found."""

    # Inherits from ImportError, as this exception is now used
    # where previously an ImportError would have been raised,
    # and may have been caught by scripts as such.

    pass


def _get_translation(lang, twtitle):
    """
    Return message of certain twtitle if exists.

    For internal use, don't use it directly.
    """
    if twtitle in _cache[lang]:
        return _cache[lang][twtitle]
    message_bundle = twtitle.split('-')[0]
    trans_text = None
    filename = '%s/%s.json' % (message_bundle, lang)
    try:
        trans_text = pkgutil.get_data(
            _messages_package_name, filename).decode('utf-8')
    except (OSError, IOError):  # file open can cause several exceptions
        _cache[lang][twtitle] = None
        return
    transdict = json.loads(trans_text)
    _cache[lang].update(transdict)
    try:
        return transdict[twtitle]
    except KeyError:
        return


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


DEFAULT_FALLBACK = ('_default', )


def translate(code, xdict, parameters=None, fallback=False):
    """Return the most appropriate translation from a translation dict.

    Given a language code and a dictionary, returns the dictionary's value for
    key 'code' if this key exists; otherwise tries to return a value for an
    alternative language that is most applicable to use on the wiki in
    language 'code' except fallback is False.

    The language itself is always checked first, then languages that
    have been defined to be alternatives, and finally English. If none of
    the options gives result, we just take the one language from xdict which may
    not be always the same. When fallback is iterable it'll return None if no
    code applies (instead of returning one).

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
    @param fallback: Try an alternate language code. If it's iterable it'll
        also try those entries and choose the first match.
    @type fallback: boolean or iterable
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
    if not isinstance(xdict, dict):
        trans = xdict
    elif not xdict:
        trans = None
    else:
        codes = [code]
        if fallback is True:
            codes += _altlang(code) + ['_default', 'en']
        elif fallback is not False:
            codes += list(fallback)
        for code in codes:
            if code in xdict:
                trans = xdict[code]
                break
        else:
            if fallback is not True:
                # this shouldn't simply return "any one" code but when fallback
                # was True before 65518573d2b0, it did just that. When False it
                # did just return None. It's now also returning None in the new
                # iterable mode.
                return
            code = list(xdict.keys())[0]
            trans = xdict[code]
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

    The translations are retrieved from json files in messages_package_name.

    fallback parameter must be True for i18n and False for L10N or testing
    purposes.

    @param code: The language code
    @param twtitle: The TranslateWiki string title, in <package>-<key> format
    @param parameters: For passing parameters.
    @param fallback: Try an alternate language code
    @type fallback: boolean
    """
    if not messages_available():
        raise TranslationError(
            'Unable to load messages package %s for bundle %s'
            '\nIt can happen due to lack of i18n submodule or files. '
            'Read https://mediawiki.org/wiki/PWB/i18n'
            % (_messages_package_name, twtitle))

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
    langs = [lang]
    if fallback:
        langs += _altlang(lang) + ['en']
    for alt in langs:
        trans = _get_translation(alt, twtitle)
        if trans:
            break
    else:
        raise TranslationError(
            'No English translation has been defined for TranslateWiki key'
            ' %r\nIt can happen due to lack of i18n submodule or files. '
            'Read https://mediawiki.org/wiki/PWB/i18n' % twtitle)
    # send the language code back via the given list
    if code_needed:
        code.append(alt)
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

    As an examples, if we had several json dictionaries in test folder like:

    en.json:

      {
          "test-plural": "Bot: Changing %(num)s {{PLURAL:%(num)d|page|pages}}.",
      }

    fr.json:

      {
          "test-plural": "Robot: Changer %(descr)s {{PLURAL:num|une page|quelques pages}}.",
      }

    and so on.

    >>> from pywikibot import i18n
    >>> i18n.set_messages_package('tests.i18n')
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
    # If a site is given instead of a code, use its language
    if hasattr(code, 'code'):
        code = code.code
    transdict = _get_translation(code, twtitle)
    if transdict is None:
        return False
    return True


def twget_keys(twtitle):
    """
    Return all language codes for a special message.

    @param twtitle: The TranslateWiki string title, in <package>-<key> format
    """
    # obtain the directory containing all the json files for this package
    package = twtitle.split("-")[0]
    mod = __import__(_messages_package_name, fromlist=[str('__file__')])
    pathname = os.path.join(os.path.dirname(mod.__file__), package)

    # build a list of languages in that directory
    langs = [filename.partition('.')[0]
             for filename in sorted(os.listdir(pathname))
             if filename.endswith('.json')]

    # exclude languages does not have this specific message in that package
    # i.e. an incomplete set of translated messages.
    return [lang for lang in langs
            if lang != 'qqq' and
            _get_translation(lang, twtitle)]


def input(twtitle, parameters=None, password=False, fallback_prompt=None):
    """
    Ask the user a question, return the user's answer.

    The prompt message is retrieved via L{twtranslate} and either uses the
    config variable 'userinterface_lang' or the default locale as the language
    code.

    @param twtitle: The TranslateWiki string title, in <package>-<key> format
    @param parameters: The values which will be applied to the translated text
    @param password: Hides the user's input (for password entry)
    @param fallback_prompt: The English prompt if i18n is not available.
    @rtype: unicode string
    """
    if not messages_available():
        if not fallback_prompt:
            raise TranslationError(
                'Unable to load messages package %s for bundle %s'
                % (_messages_package_name, twtitle))
        else:
            prompt = fallback_prompt
    else:
        code = config.userinterface_lang or \
            locale.getdefaultlocale()[0].split('_')[0]

        prompt = twtranslate(code, twtitle, parameters)
    return pywikibot.input(prompt, password)
