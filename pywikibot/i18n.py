# -*- coding: utf-8 -*-
"""
Various i18n functions.

Helper functions for both the internal translation system
and for TranslateWiki-based translations.

By default messages are assumed to reside in a package called
'scripts.i18n'. In pywikibot 3.0, that package is not packaged
with pywikibot, and pywikibot 3.0 does not have a hard dependency
on any i18n messages. However, there are three user input questions
in pagegenerators which will use i18 messages if they can be loaded.

The default message location may be changed by calling
L{set_message_package} with a package name. The package must contain
an __init__.py, and a message bundle called 'pywikibot' containing
messages. See L{twntranslate} for more information on the messages.
"""
#
# (C) Pywikibot team, 2004-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import json
import os
import pkgutil
import re

from collections import defaultdict, Mapping
from warnings import warn

import pywikibot

from pywikibot import __url__
from pywikibot import config2 as config
from pywikibot.exceptions import Error
from pywikibot.plural import plural_rules
from pywikibot.tools import (
    deprecated, deprecated_args, issue_deprecation_warning, StringTypes)

PLURAL_PATTERN = r'{{PLURAL:(?:%\()?([^\)]*?)(?:\)d)?\|(.*?)}}'

# Package name for the translation messages. The messages data must loaded
# relative to that package name. In the top of this package should be
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
        mod = __import__(_messages_package_name, fromlist=[str('__path__')])
    except ImportError:
        _messages_available = False
        return False

    if not os.listdir(next(iter(mod.__path__))):
        _messages_available = False
        return False

    _messages_available = True
    return True


def _altlang(lang):
    """Define fallback languages for particular languages.

    If no translation is available to a specified language, translate() will
    try each of the specified fallback languages, in order, until it finds
    one with a translation, with 'en' and '_default' as a last resort.

    For example, if for language 'xx', you want the preference of languages
    to be: xx > fr > ru > en, you let this method return ['fr', 'ru'].

    This code is used by other translating methods below.

    @param lang: The language code
    @type lang: string
    @return: language codes
    @rtype: list of str
    """
    # Akan
    if lang in ['ak', 'tw']:
        return ['ak', 'tw']
    # Amharic
    if lang in ['aa', 'ti']:
        return ['am']
    # Arab
    if lang in ['arc', 'arz', 'so']:
        return ['ar']
    if lang == 'kab':
        return ['ar', 'fr']
    # Bulgarian
    if lang in ['cu', 'mk']:
        return ['bg', 'sr', 'sh']
    # Czech
    if lang in ['cs', 'sk']:
        return ['cs', 'sk']
    # German
    if lang in ['bar', 'frr', 'ksh', 'pdc', 'pfl']:
        return ['de']
    if lang == 'lb':
        return ['de', 'fr']
    if lang in ['als', 'gsw']:
        return ['als', 'gsw', 'de']
    if lang == 'nds':
        return ['nds-nl', 'de']
    if lang in ['dsb', 'hsb']:
        return ['hsb', 'dsb', 'de']
    if lang == 'sli':
        return ['de', 'pl']
    if lang == 'rm':
        return ['de', 'it']
    if lang == 'stq':
        return ['nds', 'de']
    # Greek
    if lang in ['grc', 'pnt']:
        return ['el']
    # Esperanto
    if lang in ['io', 'nov']:
        return ['eo']
    # Spanish
    if lang in ['an', 'arn', 'ast', 'ay', 'ext', 'lad', 'nah', 'nv', 'qu',
                'yua']:
        return ['es']
    if lang == 'ca':
        return ['oc', 'es']
    if lang in ['gl', 'gn']:
        return ['es', 'pt']
    if lang == 'eu':
        return ['es', 'fr']
    if lang == 'cbk-zam':
        return ['es', 'tl']
    # Estonian
    if lang in ['fiu-vro', 'vro']:
        return ['fiu-vro', 'vro', 'et']
    if lang == 'liv':
        return ['et', 'lv']
    # Persian (Farsi)
    if lang in ['azb', 'lrc', 'ps']:
        return ['fa']
    if lang in ['glk', 'mzn']:
        return ['glk', 'mzn', 'fa', 'ar']
    # Finnish
    if lang == 'vep':
        return ['et', 'fi', 'ru']
    if lang == 'fit':
        return ['fi', 'sv']
    if lang == 'olo':
        return ['fi']
    # French
    if lang in ['atj', 'bm', 'br', 'ff', 'ht', 'kbp', 'kg', 'ln', 'mg', 'nrm',
                'pcd', 'rw', 'sg', 'ty', 'wa', 'wo']:
        return ['fr']
    if lang == 'oc':
        return ['fr', 'ca', 'es']
    if lang in ['co', 'frp']:
        return ['fr', 'it']
    # Hindi
    if lang in ['mai', 'sa']:
        return ['hi']
    if lang in ['ne', 'new']:
        return ['ne', 'new', 'hi']
    if lang == 'dty':
        return ['ne']
    if lang in ['bh', 'bho']:
        return ['bh', 'bho']
    # Indonesian and Malay
    if lang in ['ace', 'bug', 'bjn', 'id', 'jv', 'ms', 'su']:
        return ['id', 'ms', 'jv']
    if lang == 'map-bms':
        return ['jv', 'id', 'ms']
    if lang == 'min':
        return ['id']
    # Inuit languages
    if lang in ['ik', 'iu']:
        return ['iu', 'kl']
    if lang == 'kl':
        return ['da', 'iu', 'no', 'nb']
    # Italian
    if lang in ['eml', 'fur', 'lij', 'lmo', 'nap', 'pms', 'roa-tara', 'sc',
                'scn', 'vec']:
        return ['it']
    # Lithuanian
    if lang in ['bat-smg', 'sgs']:
        return ['bat-smg', 'sgs', 'lt']
    # Latvian
    if lang == 'ltg':
        return ['lv']
    # Dutch
    if lang in ['af', 'fy', 'li', 'pap', 'srn', 'vls', 'zea']:
        return ['nl']
    if lang == 'nds-nl':
        return ['nds', 'nl']
    # Polish
    if lang in ['csb', 'szl']:
        return ['pl']
    # Portuguese
    if lang in ['fab', 'mwl', 'tet']:
        return ['pt']
    # Romanian
    if lang in ['roa-rup', 'rup']:
        return ['roa-rup', 'rup', 'ro']
    if lang in ['mo', 'rmy']:
        return ['ro']
    # Russian and Belarusian
    if lang in ['ab', 'av', 'ba', 'bxr', 'ce', 'cv', 'inh', 'kk', 'koi', 'krc',
                'kv', 'ky', 'lbe', 'lez', 'mdf', 'mhr', 'mn', 'mrj', 'myv',
                'os', 'sah', 'tg', 'tyv', 'udm', 'uk', 'xal']:
        return ['ru']
    if lang in ['kbd', 'ady']:
        return ['kbd', 'ady', 'ru']
    if lang == 'tt':
        return ['tt-cyrl', 'ru']
    if lang in ['be', 'be-tarask']:
        return ['be', 'be-tarask', 'ru']
    if lang == 'kaa':
        return ['uz', 'ru']
    # Serbocroatian
    if lang in ['bs', 'hr', 'sh']:
        return ['sh', 'hr', 'bs', 'sr', 'sr-el']
    if lang == 'sr':
        return ['sr-el', 'sh', 'hr', 'bs']
    # Tagalog
    if lang in ['bcl', 'ceb', 'ilo', 'pag', 'pam', 'war']:
        return ['tl']
    # Turkish and Kurdish
    if lang in ['diq', 'ku']:
        return ['ku', 'ku-latn', 'tr']
    if lang == 'gag':
        return ['tr']
    if lang == 'ckb':
        return ['ku']
    # Ukrainian
    if lang in ['crh', 'crh-latn']:
        return ['crh', 'crh-latn', 'uk', 'ru']
    if lang in ['rue']:
        return ['uk', 'ru']
    # Chinese
    if lang in ['zh-classical', 'lzh', 'minnan', 'nan', 'zh-tw',
                'zh', 'zh-hans']:
        return ['zh', 'zh-hans', 'zh-tw', 'zh-cn', 'zh-classical', 'lzh']
    if lang == 'zh-min-nan':
        return ['cdo', 'zh', 'zh-hans', 'zh-tw', 'zh-cn', 'zh-classical',
                'lzh']
    if lang in ['cdo', 'gan', 'hak', 'ii', 'wuu', 'za', 'zh-classical', 'lzh',
                'zh-cn', 'zh-yue', 'yue']:
        return ['zh', 'zh-hans' 'zh-cn', 'zh-tw', 'zh-classical', 'lzh']
    # Scandinavian languages
    if lang in ['da', 'sv']:
        return ['da', 'no', 'nb', 'sv', 'nn']
    if lang in ['fo', 'is']:
        return ['da', 'no', 'nb', 'nn', 'sv']
    if lang == 'nn':
        return ['no', 'nb', 'sv', 'da']
    if lang in ['no', 'nb']:
        return ['no', 'nb', 'da', 'nn', 'sv']
    if lang == 'se':
        return ['sv', 'no', 'nb', 'nn', 'fi']
    # Other languages
    if lang in ['bi', 'tpi']:
        return ['bi', 'tpi']
    if lang == 'yi':
        return ['he', 'de']
    if lang in ['ia', 'ie']:
        return ['ia', 'la', 'it', 'fr', 'es']
    if lang == 'xmf':
        return ['ka']
    if lang in ['nso', 'st']:
        return ['st', 'nso']
    if lang in ['kj', 'ng']:
        return ['kj', 'ng']
    if lang in ['meu', 'hmo']:
        return ['meu', 'hmo']
    if lang in ['as', 'bpy']:
        return ['bn']
    if lang == 'tcy':
        return ['kn']
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
    @type parameters: Mapping of str to int
    @return: The message with the plural instances replaced
    @rtype: str
    """
    def static_plural_value(n):
        return rule['plural']

    def replace_plural(match):
        selector = match.group(1)
        variants = match.group(2)
        num = parameters[selector]
        if not isinstance(num, int):
            issue_deprecation_warning(
                'type {0} for value {1} ({2})'.format(type(num), selector, num),
                'an int', 1)
            num = int(num)

        plural_entries = []
        specific_entries = {}
        # A plural entry can not start at the end of the variants list,
        # and must end with | or the end of the variants list.
        for number, plural in re.findall(r'(?!$)(?: *(\d+) *= *)?(.*?)(?:\||$)',
                                         variants):
            if number:
                specific_entries[int(number)] = plural
            else:
                assert not specific_entries, \
                    'generic entries defined after specific in "{0}"'.format(variants)
                plural_entries += [plural]

        if num in specific_entries:
            return specific_entries[num]

        index = plural_value(num)
        if rule['nplurals'] == 1:
            assert index == 0

        if index >= len(plural_entries):
            raise IndexError(
                'requested plural {0} for {1} but only {2} ("{3}") '
                'provided'.format(
                    index, selector, len(plural_entries),
                    '", "'.join(plural_entries)))
        return plural_entries[index]

    assert isinstance(parameters, Mapping), \
        'parameters is not Mapping but {0}'.format(type(parameters))
    try:
        rule = plural_rules[code]
    except KeyError:
        rule = plural_rules['_default']
    plural_value = rule['plural']
    if not callable(plural_value):
        assert rule['nplurals'] == 1
        plural_value = static_plural_value

    return re.sub(PLURAL_PATTERN, replace_plural, message)


class _PluralMappingAlias(Mapping):

    """
    Aliasing class to allow non mappings in _extract_plural.

    That function only uses __getitem__ so this is only implemented here.
    """

    def __init__(self, source):
        if isinstance(source, StringTypes):
            source = int(source)
        self.source = source
        self.index = -1
        super(_PluralMappingAlias, self).__init__()

    def __getitem__(self, key):
        self.index += 1
        if isinstance(self.source, dict):
            return int(self.source[key])
        elif isinstance(self.source, (tuple, list)):
            if self.index < len(self.source):
                return int(self.source[self.index])
            raise ValueError('Length of parameter does not match PLURAL '
                             'occurrences.')
        else:
            return self.source

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError


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

    For PLURAL support have a look at the twtranslate method.

    @param code: The language code
    @type code: string or Site object
    @param xdict: dictionary with language codes as keys or extended dictionary
                  with family names as keys containing language dictionaries or
                  a single (unicode) string. May contain PLURAL tags as
                  described in twtranslate
    @type xdict: dict, string, unicode
    @param parameters: For passing (plural) parameters
    @type parameters: dict, string, unicode, int
    @param fallback: Try an alternate language code. If it's iterable it'll
        also try those entries and choose the first match.
    @type fallback: boolean or iterable
    @raise IndexError: If the language supports and requires more plurals than
        defined for the given translation template.
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

    if not isinstance(parameters, Mapping):
        issue_deprecation_warning('parameters not being a mapping', None, 2)
        plural_parameters = _PluralMappingAlias(parameters)
    else:
        plural_parameters = parameters

    # else we check for PLURAL variants
    trans = _extract_plural(code, trans, plural_parameters)
    if parameters:
        try:
            return trans % parameters
        except (KeyError, TypeError):
            # parameter is for PLURAL variants only, don't change the string
            pass
    return trans


@deprecated_args(code='source')
def twtranslate(source, twtitle, parameters=None, fallback=True,
                only_plural=False):
    """
    Translate a message using JSON files in messages_package_name.

    fallback parameter must be True for i18n and False for L10N or testing
    purposes.

    Support for plural is implemented like in MediaWiki extension. If the
    TranslateWiki message contains a plural tag inside which looks like::

        {{PLURAL:<number>|<variant1>|<variant2>[|<variantn>]}}

    it takes that variant calculated by the plural_rules depending on the number
    value. Multiple plurals are allowed.

    As an examples, if we had several json dictionaries in test folder like:

    en.json::

      {
          "test-plural": "Bot: Changing %(num)s {{PLURAL:%(num)d|page|pages}}.",
      }

    fr.json::

      {
          "test-plural": "Robot: Changer %(descr)s {{PLURAL:num|une page|quelques pages}}.",
      }

    and so on.

    >>> from pywikibot import i18n
    >>> i18n.set_messages_package('tests.i18n')
    >>> # use a dictionary
    >>> str(i18n.twtranslate('en', 'test-plural', {'num':2}))
    'Bot: Changing 2 pages.'
    >>> # use additional format strings
    >>> str(i18n.twtranslate('fr', 'test-plural', {'num': 1, 'descr': 'seulement'}))
    'Robot: Changer seulement une page.'
    >>> # use format strings also outside
    >>> str(i18n.twtranslate('fr', 'test-plural', {'num': 10}, only_plural=True)
    ...     % {'descr': 'seulement'})
    'Robot: Changer seulement quelques pages.'

    @param source: When it's a site it's using the lang attribute and otherwise
        it is using the value directly.
    @type source: BaseSite or str
    @param twtitle: The TranslateWiki string title, in <package>-<key> format
    @param parameters: For passing parameters. It should be a mapping but for
        backwards compatibility can also be a list, tuple or a single value.
        They are also used for plural entries in which case they must be a
        Mapping and will cause a TypeError otherwise.
    @param fallback: Try an alternate language code
    @type fallback: boolean
    @param only_plural: Define whether the parameters should be only applied to
        plural instances. If this is False it will apply the parameters also
        to the resulting string. If this is True the placeholders must be
        manually applied afterwards.
    @type only_plural: bool
    @raise IndexError: If the language supports and requires more plurals than
        defined for the given translation template.
    """
    if not messages_available():
        raise TranslationError(
            'Unable to load messages package %s for bundle %s'
            '\nIt can happen due to lack of i18n submodule or files. '
            'Read %s/i18n'
            % (_messages_package_name, twtitle, __url__))

    source_needed = False
    # If a site is given instead of a lang, use its language
    if hasattr(source, 'lang'):
        lang = source.lang
    # check whether we need the language code back
    elif isinstance(source, list):
        # For backwards compatibility still support lists, when twntranslate
        # was not deprecated and needed a way to get the used language code back
        warn('The source argument should not be a list but either a BaseSite '
             'or a str/unicode.', DeprecationWarning, 2)
        lang = source.pop()
        source_needed = True
    else:
        lang = source

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
            'No %s translation has been defined for TranslateWiki key'
            ' %r\nIt can happen due to lack of i18n submodule or files. '
            'Read https://mediawiki.org/wiki/PWB/i18n'
            % ('English' if 'en' in langs else "'%s'" % lang,
               twtitle))
    # send the language code back via the given mutable list parameter
    if source_needed:
        source.append(alt)

    if '{{PLURAL:' in trans:
        # _extract_plural supports in theory non-mappings, but they are
        # deprecated
        if not isinstance(parameters, Mapping):
            raise TypeError('parameters must be a mapping.')
        trans = _extract_plural(alt, trans, parameters)

    # this is only the case when called in twntranslate, and that didn't apply
    # parameters when it wasn't a dict
    if isinstance(parameters, _PluralMappingAlias):
        # This is called due to the old twntranslate function which ignored
        # KeyError. Instead only_plural should be used.
        if isinstance(parameters.source, dict):
            try:
                trans %= parameters.source
            except KeyError:
                pass
        parameters = None

    if parameters is not None and not isinstance(parameters, Mapping):
        issue_deprecation_warning('parameters not being a Mapping', None, 2)

    if not only_plural and parameters:
        return trans % parameters
    else:
        return trans


@deprecated('twtranslate')
@deprecated_args(code='source')
def twntranslate(source, twtitle, parameters=None):
    """DEPRECATED: Get translated string for the key."""
    if parameters is not None:
        parameters = _PluralMappingAlias(parameters)
    return twtranslate(source, twtitle, parameters)


@deprecated_args(code='source')
def twhas_key(source, twtitle):
    """
    Check if a message has a translation in the specified language code.

    The translations are retrieved from i18n.<package>, based on the callers
    import table.

    No code fallback is made.

    @param source: When it's a site it's using the lang attribute and otherwise
        it is using the value directly.
    @type source: BaseSite or str
    @param twtitle: The TranslateWiki string title, in <package>-<key> format
    """
    # If a site is given instead of a code, use its language
    lang = getattr(source, 'lang', source)
    transdict = _get_translation(lang, twtitle)
    return transdict is not None


def twget_keys(twtitle):
    """
    Return all language codes for a special message.

    @param twtitle: The TranslateWiki string title, in <package>-<key> format

    @raises OSError: the package i18n can not be loaded
    """
    # obtain the directory containing all the json files for this package
    package = twtitle.split("-")[0]
    mod = __import__(_messages_package_name, fromlist=[str('__file__')])
    pathname = os.path.join(next(iter(mod.__path__)), package)

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

    The prompt message is retrieved via L{twtranslate} and uses the
    config variable 'userinterface_lang'.

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
        code = config.userinterface_lang

        prompt = twtranslate(code, twtitle, parameters)
    return pywikibot.input(prompt, password)
