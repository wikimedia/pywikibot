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
messages. See L{twtranslate} for more information on the messages.
"""
#
# (C) Pywikibot team, 2004-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import json
import os
import pkgutil
import re

from collections import defaultdict
try:
    from collections.abc import Mapping
except ImportError:  # Python 2.7
    from collections import Mapping
from textwrap import fill
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


_LANG_TO_GROUP_NAME = defaultdict(str, {
    'aa': 'aa',
    'ab': 'ab',
    'ace': 'ace',
    'ady': 'kbd',
    'af': 'af',
    'ak': 'ak',
    'als': 'als',
    'an': 'an',
    'arc': 'arc',
    'arn': 'an',
    'arz': 'arc',
    'as': 'as',
    'ast': 'an',
    'atj': 'atj',
    'av': 'ab',
    'ay': 'an',
    'azb': 'azb',
    'ba': 'ab',
    'bar': 'bar',
    'bat-smg': 'bat-smg',
    'bcl': 'bcl',
    'be': 'be',
    'be-tarask': 'be',
    'bh': 'bh',
    'bho': 'bh',
    'bi': 'bi',
    'bjn': 'ace',
    'bm': 'atj',
    'bpy': 'as',
    'br': 'atj',
    'bs': 'bs',
    'bug': 'ace',
    'bxr': 'ab',
    'ca': 'ca',
    'cbk-zam': 'cbk-zam',
    'cdo': 'cdo',
    'ce': 'ab',
    'ceb': 'bcl',
    'ckb': 'ckb',
    'co': 'co',
    'crh': 'crh',
    'crh-latn': 'crh',
    'cs': 'cs',
    'csb': 'csb',
    'cu': 'cu',
    'cv': 'ab',
    'da': 'da',
    'diq': 'diq',
    'dsb': 'dsb',
    'dty': 'dty',
    'eml': 'eml',
    'eu': 'eu',
    'ext': 'an',
    'fab': 'fab',
    'ff': 'atj',
    'fit': 'fit',
    'fiu-vro': 'fiu-vro',
    'fo': 'fo',
    'frp': 'co',
    'frr': 'bar',
    'fur': 'eml',
    'fy': 'af',
    'gag': 'gag',
    'gan': 'cdo',
    'gl': 'gl',
    'glk': 'glk',
    'gn': 'gl',
    'grc': 'grc',
    'gsw': 'als',
    'hak': 'cdo',
    'hmo': 'meu',
    'hr': 'bs',
    'hsb': 'dsb',
    'ht': 'atj',
    'ia': 'ia',
    'id': 'ace',
    'ie': 'ia',
    'ii': 'cdo',
    'ik': 'ik',
    'ilo': 'bcl',
    'inh': 'ab',
    'io': 'io',
    'is': 'fo',
    'iu': 'ik',
    'jv': 'ace',
    'kaa': 'kaa',
    'kab': 'kab',
    'kbd': 'kbd',
    'kbp': 'atj',
    'kg': 'atj',
    'kj': 'kj',
    'kk': 'ab',
    'kl': 'kl',
    'koi': 'ab',
    'krc': 'ab',
    'ksh': 'bar',
    'ku': 'diq',
    'kv': 'ab',
    'ky': 'ab',
    'lad': 'an',
    'lb': 'lb',
    'lbe': 'ab',
    'lez': 'ab',
    'li': 'af',
    'lij': 'eml',
    'liv': 'liv',
    'lmo': 'eml',
    'ln': 'atj',
    'lrc': 'azb',
    'ltg': 'ltg',
    'lzh': 'zh-classical',
    'mai': 'mai',
    'map-bms': 'map-bms',
    'mdf': 'ab',
    'meu': 'meu',
    'mg': 'atj',
    'mhr': 'ab',
    'min': 'min',
    'minnan': 'zh-classical',
    'mk': 'cu',
    'mn': 'ab',
    'mo': 'mo',
    'mrj': 'ab',
    'ms': 'ace',
    'mwl': 'fab',
    'myv': 'ab',
    'mzn': 'glk',
    'nah': 'an',
    'nan': 'zh-classical',
    'nap': 'eml',
    'nb': 'no',
    'nds': 'nds',
    'nds-nl': 'nds-nl',
    'ne': 'ne',
    'new': 'ne',
    'ng': 'kj',
    'nn': 'nn',
    'no': 'no',
    'nov': 'io',
    'nrm': 'atj',
    'nso': 'nso',
    'nv': 'an',
    'oc': 'oc',
    'olo': 'olo',
    'os': 'ab',
    'pag': 'bcl',
    'pam': 'bcl',
    'pap': 'af',
    'pcd': 'atj',
    'pdc': 'bar',
    'pfl': 'bar',
    'pms': 'eml',
    'pnt': 'grc',
    'ps': 'azb',
    'pt': 'pt',
    'pt-br': 'pt',
    'qu': 'an',
    'rm': 'rm',
    'rmy': 'mo',
    'roa-rup': 'roa-rup',
    'roa-tara': 'eml',
    'rue': 'rue',
    'rup': 'roa-rup',
    'rw': 'atj',
    'sa': 'mai',
    'sah': 'ab',
    'sc': 'eml',
    'scn': 'eml',
    'se': 'se',
    'sg': 'atj',
    'sgs': 'bat-smg',
    'sh': 'bs',
    'sk': 'cs',
    'sli': 'sli',
    'so': 'arc',
    'sr': 'sr',
    'srn': 'af',
    'st': 'nso',
    'stq': 'stq',
    'su': 'ace',
    'sv': 'da',
    'szl': 'csb',
    'tcy': 'tcy',
    'tet': 'fab',
    'tg': 'ab',
    'ti': 'aa',
    'tpi': 'bi',
    'tt': 'tt',
    'tw': 'ak',
    'ty': 'atj',
    'tyv': 'ab',
    'udm': 'ab',
    'uk': 'ab',
    'vec': 'eml',
    'vep': 'vep',
    'vls': 'af',
    'vro': 'fiu-vro',
    'wa': 'atj',
    'war': 'bcl',
    'wo': 'atj',
    'wuu': 'cdo',
    'xal': 'ab',
    'xmf': 'xmf',
    'yi': 'yi',
    'yua': 'an',
    'yue': 'cdo',
    'za': 'cdo',
    'zea': 'af',
    'zh': 'zh-classical',
    'zh-classical': 'zh-classical',
    'zh-cn': 'cdo',
    'zh-hans': 'zh-classical',
    'zh-min-nan': 'zh-min-nan',
    'zh-tw': 'zh-classical',
    'zh-yue': 'cdo'})
_GROUP_NAME_TO_FALLBACKS = {
    '': [],
    'aa': ['am'],
    'ab': ['ru'],
    'ace': ['id', 'ms', 'jv'],
    'af': ['nl'],
    'ak': ['ak', 'tw'],
    'als': ['als', 'gsw', 'de'],
    'an': ['es'],
    'arc': ['ar'],
    'as': ['bn'],
    'atj': ['fr'],
    'azb': ['fa'],
    'bar': ['de'],
    'bat-smg': ['bat-smg', 'sgs', 'lt'],
    'bcl': ['tl'],
    'be': ['be', 'be-tarask', 'ru'],
    'bh': ['bh', 'bho'],
    'bi': ['bi', 'tpi'],
    'bs': ['sh', 'hr', 'bs', 'sr', 'sr-el'],
    'ca': ['oc', 'es'],
    'cbk-zam': ['es', 'tl'],
    'cdo': ['zh', 'zh-hanszh-cn', 'zh-tw', 'zh-classical', 'lzh'],
    'ckb': ['ku'],
    'co': ['fr', 'it'],
    'crh': ['crh', 'crh-latn', 'uk', 'ru'],
    'cs': ['cs', 'sk'],
    'csb': ['pl'],
    'cu': ['bg', 'sr', 'sh'],
    'da': ['da', 'no', 'nb', 'sv', 'nn'],
    'diq': ['ku', 'ku-latn', 'tr'],
    'dsb': ['hsb', 'dsb', 'de'],
    'dty': ['ne'],
    'eml': ['it'],
    'eu': ['es', 'fr'],
    'fab': ['pt'],
    'fit': ['fi', 'sv'],
    'fiu-vro': ['fiu-vro', 'vro', 'et'],
    'fo': ['da', 'no', 'nb', 'nn', 'sv'],
    'gag': ['tr'],
    'gl': ['es', 'pt'],
    'glk': ['glk', 'mzn', 'fa', 'ar'],
    'grc': ['el'],
    'ia': ['ia', 'la', 'it', 'fr', 'es'],
    'ik': ['iu', 'kl'],
    'io': ['eo'],
    'kaa': ['uz', 'ru'],
    'kab': ['ar', 'fr'],
    'kbd': ['kbd', 'ady', 'ru'],
    'kj': ['kj', 'ng'],
    'kl': ['da', 'iu', 'no', 'nb'],
    'lb': ['de', 'fr'],
    'liv': ['et', 'lv'],
    'ltg': ['lv'],
    'mai': ['hi'],
    'map-bms': ['jv', 'id', 'ms'],
    'meu': ['meu', 'hmo'],
    'min': ['id'],
    'mo': ['ro'],
    'nds': ['nds-nl', 'de'],
    'nds-nl': ['nds', 'nl'],
    'ne': ['ne', 'new', 'hi'],
    'nn': ['no', 'nb', 'sv', 'da'],
    'no': ['no', 'nb', 'da', 'nn', 'sv'],
    'nso': ['st', 'nso'],
    'oc': ['fr', 'ca', 'es'],
    'olo': ['fi'],
    'pt': ['pt', 'pt-br'],
    'rm': ['de', 'it'],
    'roa-rup': ['roa-rup', 'rup', 'ro'],
    'rue': ['uk', 'ru'],
    'se': ['sv', 'no', 'nb', 'nn', 'fi'],
    'sli': ['de', 'pl'],
    'sr': ['sr-el', 'sh', 'hr', 'bs'],
    'stq': ['nds', 'de'],
    'tcy': ['kn'],
    'tt': ['tt-cyrl', 'ru'],
    'vep': ['et', 'fi', 'ru'],
    'xmf': ['ka'],
    'yi': ['he', 'de'],
    'zh-classical': ['zh', 'zh-hans', 'zh-tw', 'zh-cn', 'zh-classical', 'lzh'],
    'zh-min-nan': [
        'cdo', 'zh', 'zh-hans', 'zh-tw', 'zh-cn', 'zh-classical', 'lzh']}


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
    @type lang: str
    @return: language codes
    @rtype: list of str
    """
    return _GROUP_NAME_TO_FALLBACKS[_LANG_TO_GROUP_NAME[lang]]


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
    filename = '%s/%s.json' % (message_bundle, lang)
    try:
        trans_text = pkgutil.get_data(
            _messages_package_name, filename).decode('utf-8')
    except (OSError, IOError):  # file open can cause several exceptions
        _cache[lang][twtitle] = None
        return None
    transdict = json.loads(trans_text)
    _cache[lang].update(transdict)
    try:
        return transdict[twtitle]
    except KeyError:
        return None


def _extract_plural(code, message, parameters):
    """Check for the plural variants in message and replace them.

    @param message: the message to be replaced
    @type message: str
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
                'type {0} for value {1} ({2})'
                .format(type(num), selector, num),
                'an int', 1, since='20151009')
            num = int(num)

        plural_entries = []
        specific_entries = {}
        # A plural entry can not start at the end of the variants list,
        # and must end with | or the end of the variants list.
        for number, plural in re.findall(
            r'(?!$)(?: *(\d+) *= *)?(.*?)(?:\||$)', variants
        ):
            if number:
                specific_entries[int(number)] = plural
            else:
                assert not specific_entries, (
                    'generic entries defined after specific in "{0}"'
                    .format(variants))
                plural_entries += [plural]

        if num in specific_entries:
            return specific_entries[num]

        index = plural_value(num)
        needed = rule['nplurals']
        if needed == 1:
            assert index == 0

        if index >= len(plural_entries):
            # take the last entry in that case, see
            # https://translatewiki.net/wiki/Plural#Plural_syntax_in_MediaWiki
            index = -1
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
    the options gives result, we just take the one language from xdict which
    may not be always the same. When fallback is iterable it'll return None if
    no code applies (instead of returning one).

    For PLURAL support have a look at the twtranslate method.

    @param code: The language code
    @type code: str or Site object
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
            if fallback is False:
                return None
            raise KeyError('No fallback key found in lookup dict for "{}"'
                           .format(code))
    if trans is None:
        return None  # return None if we have no translation found
    if parameters is None:
        return trans

    if not isinstance(parameters, Mapping):
        issue_deprecation_warning('parameters not being a mapping',
                                  since='20151008')
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
def twtranslate(
    source, twtitle, parameters=None, fallback=True, only_plural=False
):
    r"""
    Translate a message using JSON files in messages_package_name.

    fallback parameter must be True for i18n and False for L10N or testing
    purposes.

    Support for plural is implemented like in MediaWiki extension. If the
    TranslateWiki message contains a plural tag inside which looks like::

        {{PLURAL:<number>|<variant1>|<variant2>[|<variantn>]}}

    it takes that variant calculated by the plural_rules depending on the
    number value. Multiple plurals are allowed.

    As an examples, if we had several json dictionaries in test folder like:

    en.json::

      {
         "test-plural": "Bot: Changing %(num)s {{PLURAL:%(num)d|page|pages}}.",
      }

    fr.json::

      {
         "test-plural": \
         "Robot: Changer %(descr)s {{PLURAL:num|une page|quelques pages}}.",
      }

    and so on.

    >>> from pywikibot import i18n
    >>> i18n.set_messages_package('tests.i18n')
    >>> # use a dictionary
    >>> str(i18n.twtranslate('en', 'test-plural', {'num':2}))
    'Bot: Changing 2 pages.'
    >>> # use additional format strings
    >>> str(i18n.twtranslate(
    ...    'fr', 'test-plural', {'num': 1, 'descr': 'seulement'}))
    'Robot: Changer seulement une page.'
    >>> # use format strings also outside
    >>> str(i18n.twtranslate(
    ...    'fr', 'test-plural', {'num': 10}, only_plural=True
    ... ) % {'descr': 'seulement'})
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
            'See %s/i18n'
            % (_messages_package_name, twtitle, __url__))

    source_needed = False
    # If a site is given instead of a lang, use its language
    if hasattr(source, 'lang'):
        lang = source.lang
    # check whether we need the language code back
    elif isinstance(source, list):
        # For backwards compatibility still support lists, when twntranslate
        # was not deprecated and needed a way to get the used language code
        # back.
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
        raise TranslationError(fill(
            'No {} translation has been defined for TranslateWiki key "{}". '
            'It can happen due to lack of i18n submodule or files or an '
            'outdated submodule. See {}/i18n'
            .format('English' if 'en' in langs else "'{}'".format(lang),
                    twtitle, __url__)))
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
        issue_deprecation_warning('parameters not being a Mapping',
                                  since='20151008')

    if not only_plural and parameters:
        return trans % parameters
    else:
        return trans


@deprecated('twtranslate', since='20151009')
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
    package = twtitle.split('-')[0]
    mod = __import__(_messages_package_name, fromlist=[str('__file__')])
    pathname = os.path.join(next(iter(mod.__path__)), package)

    # build a list of languages in that directory
    langs = [filename.partition('.')[0]
             for filename in sorted(os.listdir(pathname))
             if filename.endswith('.json')]

    # exclude languages does not have this specific message in that package
    # i.e. an incomplete set of translated messages.
    return [lang for lang in langs
            if lang != 'qqq' and _get_translation(lang, twtitle)]


def input(twtitle, parameters=None, password=False, fallback_prompt=None):
    """
    Ask the user a question, return the user's answer.

    The prompt message is retrieved via L{twtranslate} and uses the
    config variable 'userinterface_lang'.

    @param twtitle: The TranslateWiki string title, in <package>-<key> format
    @param parameters: The values which will be applied to the translated text
    @param password: Hides the user's input (for password entry)
    @param fallback_prompt: The English prompt if i18n is not available.
    @rtype: str
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
