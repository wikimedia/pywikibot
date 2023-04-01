"""Various i18n functions.

Helper functions for both the internal localization system and for
TranslateWiki-based translations.

By default messages are assumed to reside in a package called
'scripts.i18n'. In pywikibot 3+, that package is not packaged with
pywikibot, and pywikibot 3+ does not have a hard dependency on any i18n
messages. However, there are three user input questions in pagegenerators
which will use i18n messages if they can be loaded.

The default message location may be changed by calling
:py:obj:`set_message_package` with a package name. The package must contain an
__init__.py, and a message bundle called 'pywikibot' containing messages.
See :py:obj:`twtranslate` for more information on the messages.
"""
#
# (C) Pywikibot team, 2004-2023
#
# Distributed under the terms of the MIT license.
#
import json
import os
import pkgutil
import re
from collections import abc, defaultdict
from contextlib import suppress
from pathlib import Path
from textwrap import fill
from typing import Optional, Union

import pywikibot
from pywikibot import __url__, config
from pywikibot.backports import (
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    Mapping,
    Match,
    Sequence,
    cache,
    removesuffix,
)
from pywikibot.plural import plural_rule


STR_OR_SITE_TYPE = Union[str, 'pywikibot.site.BaseSite']

PLURAL_PATTERN = r'{{PLURAL:(?:%\()?([^\)]*?)(?:\)d)?\|(.*?)}}'

# Package name for the translation messages. The messages data must loaded
# relative to that package name. In the top of this package should be
# directories named after for each script/message bundle, and each directory
# should contain JSON files called <lang>.json
_messages_package_name = 'scripts.i18n'
# Flag to indicate whether translation messages are available
_messages_available = None

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
    'ary': 'arc',
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

_GROUP_NAME_TO_FALLBACKS: Dict[str, List[str]] = {
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
        'cdo', 'zh', 'zh-hans', 'zh-tw', 'zh-cn', 'zh-classical', 'lzh']
}


def set_messages_package(package_name: str) -> None:
    """Set the package name where i18n messages are located."""
    global _messages_package_name
    global _messages_available
    _messages_package_name = package_name
    _messages_available = None


def messages_available() -> bool:
    """
    Return False if there are no i18n messages available.

    To determine if messages are available, it looks for the package name
    set using :py:obj:`set_messages_package` for a message bundle called
    ``pywikibot`` containing messages.

    >>> from pywikibot import i18n
    >>> i18n.messages_available()
    True
    >>> old_package = i18n._messages_package_name  # save the old package name
    >>> i18n.set_messages_package('foo')
    >>> i18n.messages_available()
    False
    >>> i18n.set_messages_package(old_package)
    >>> i18n.messages_available()
    True
    """
    global _messages_available
    if _messages_available is not None:
        return _messages_available

    try:
        mod = __import__(_messages_package_name, fromlist=['__path__'])
    except ImportError:
        _messages_available = False
        return False

    _messages_available = bool(os.listdir(next(iter(mod.__path__))))
    return _messages_available


def _altlang(lang: str) -> List[str]:
    """Define fallback languages for particular languages.

    If no translation is available to a specified language, translate() will
    try each of the specified fallback languages, in order, until it finds
    one with a translation, with 'en' and '_default' as a last resort.

    For example, if for language 'xx', you want the preference of languages
    to be: xx > fr > ru > en, you let this method return ['fr', 'ru'].

    This code is used by other translating methods below.

    :param lang: The language code
    :return: language codes
    """
    return _GROUP_NAME_TO_FALLBACKS[_LANG_TO_GROUP_NAME[lang]]


@cache
def _get_bundle(lang: str, dirname: str) -> Dict[str, str]:
    """Return json data of certain bundle if exists.

    For internal use, don't use it directly.

    .. versionadded:: 7.0
    """
    filename = f'{dirname}/{lang}.json'
    try:
        data = pkgutil.get_data(_messages_package_name, filename)
        assert data is not None
        trans_text = data.decode('utf-8')
    except OSError:  # file open can cause several exceptions
        return {}

    return json.loads(trans_text)


def _get_translation(lang: str, twtitle: str) -> Optional[str]:
    """
    Return message of certain twtitle if exists.

    For internal use, don't use it directly.
    """
    message_bundle = twtitle.split('-')[0]
    transdict = _get_bundle(lang, message_bundle)
    return transdict.get(twtitle)


def _extract_plural(lang: str, message: str, parameters: Mapping[str, int]
                    ) -> str:
    """Check for the plural variants in message and replace them.

    :param message: the message to be replaced
    :param parameters: plural parameters passed from other methods
    :return: The message with the plural instances replaced
    """
    def static_plural_value(n: int) -> int:
        plural_rule = rule['plural']
        assert not callable(plural_rule)
        return plural_rule

    def replace_plural(match: Match[str]) -> str:
        selector = match[1]
        variants = match[2]
        num = parameters[selector]
        if not isinstance(num, int):
            raise ValueError("'{}' must be a number, not a {} ({})"
                             .format(selector, num, type(num).__name__))

        plural_entries = []
        specific_entries = {}
        # A plural entry cannot start at the end of the variants list,
        # and must end with | or the end of the variants list.
        for number, plural in re.findall(
            r'(?!$)(?: *(\d+) *= *)?(.*?)(?:\||$)', variants
        ):
            if number:
                specific_entries[int(number)] = plural
            else:
                assert not specific_entries, (
                    'generic entries defined after specific in "{}"'
                    .format(variants))
                plural_entries += [plural]

        if num in specific_entries:
            return specific_entries[num]

        assert callable(plural_value)

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
        f'parameters is not Mapping but {type(parameters)}'

    rule = plural_rule(lang)

    if callable(rule['plural']):
        plural_value = rule['plural']
    else:
        assert rule['nplurals'] == 1
        plural_value = static_plural_value

    return re.sub(PLURAL_PATTERN, replace_plural, message)


class _PluralMappingAlias(abc.Mapping):

    """
    Aliasing class to allow non mappings in _extract_plural.

    That function only uses __getitem__ so this is only implemented here.
    """

    def __init__(self, source: Union[int, str, Sequence[int],
                 Mapping[str, int]]) -> None:
        self.source = source
        if isinstance(source, str):
            self.source = int(source)

        self.index = -1
        super().__init__()

    def __getitem__(self, key: str) -> int:
        self.index += 1
        if isinstance(self.source, dict):
            return int(self.source[key])

        if isinstance(self.source, (tuple, list)):
            if self.index < len(self.source):
                return int(self.source[self.index])
            raise ValueError('Length of parameter does not match PLURAL '
                             'occurrences.')
        assert isinstance(self.source, int)
        return self.source

    def __iter__(self) -> Iterator[int]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


DEFAULT_FALLBACK = ('_default', )


def translate(code: STR_OR_SITE_TYPE,
              xdict: Union[str, Mapping[str, str]],
              parameters: Optional[Mapping[str, int]] = None,
              fallback: Union[bool, Iterable[str]] = False) -> Optional[str]:
    """Return the most appropriate localization from a localization dict.

    Given a site code and a dictionary, returns the dictionary's value for
    key 'code' if this key exists; otherwise tries to return a value for an
    alternative code that is most applicable to use on the wiki in language
    'code' except fallback is False.

    The code itself is always checked first, then these codes that have
    been defined to be alternatives, and finally English.

    If fallback is False and the code is not found in the

    For PLURAL support have a look at the twtranslate method.

    :param code: The site code as string or Site object. If xdict is an
        extended dictionary the Site object should be used in favour of the
        code string. Otherwise localizations from a wrong family might be
        used.
    :param xdict: dictionary with language codes as keys or extended
        dictionary with family names as keys containing code dictionaries
        or a single string. May contain PLURAL tags as described in
        twtranslate
    :param parameters: For passing (plural) parameters
    :param fallback: Try an alternate language code. If it's iterable it'll
        also try those entries and choose the first match.
    :return: the localized string
    :raise IndexError: If the language supports and requires more plurals
        than defined for the given PLURAL pattern.
    :raise KeyError: No fallback key found if fallback is not False
    """
    family = pywikibot.config.family
    # If a site is given instead of a code, use its language
    if hasattr(code, 'code'):
        family = code.family.name
        code = code.code
    assert isinstance(code, str)

    try:
        lookup = xdict[code]
    except (KeyError, TypeError):
        # Check whether xdict has multiple projects
        if isinstance(xdict, dict) and family in xdict:
            lookup = xdict[family]
        else:
            lookup = xdict

    # Get the translated string
    if not isinstance(lookup, dict):
        trans = lookup
    elif not lookup:
        trans = None
    else:
        codes = [code]
        if fallback is True:
            codes += _altlang(code) + ['_default', 'en']
        elif fallback is not False:
            assert not isinstance(fallback, bool)
            codes.extend(fallback)
        for code in codes:
            if code in lookup:
                trans = lookup[code]
                break
        else:
            if fallback is not False:
                raise KeyError('No fallback key found in lookup dict for "{}"'
                               .format(code))
            trans = None

    if trans is None:
        if isinstance(xdict, dict) and 'wikipedia' in xdict:
            # fallback to wikipedia family
            return translate(code, xdict['wikipedia'],
                             parameters=parameters, fallback=fallback)
        return None  # return None if we have no translation found

    if parameters is None:
        return trans

    if not isinstance(parameters, Mapping):
        raise ValueError('parameters should be a mapping, not {}'
                         .format(type(parameters).__name__))

    # else we check for PLURAL variants
    trans = _extract_plural(code, trans, parameters)
    if parameters:
        # On error: parameter is for PLURAL variants only,
        # don't change the string
        with suppress(KeyError, TypeError):
            trans = trans % parameters
    return trans


def get_bot_prefix(source: STR_OR_SITE_TYPE, use_prefix: bool) -> str:
    """Get the bot prefix string like 'Bot: ' including space delimiter.

    .. note: If *source* is a str and ``config.bot_prefix`` is set to
       None, it cannot be determined whether the current user is a bot
       account. In this cas the prefix will be returned.
    .. versionadded:: 8.1

    :param source: When it's a site it's using the lang attribute and otherwise
        it is using the value directly.
    :param use_prefix: If True, return a bot prefix which depends on the
        ``config.bot_prefix`` setting.
    """
    config_prefix = config.bot_prefix_summary
    if not use_prefix or config_prefix is False:
        return ''

    if isinstance(config_prefix, str):
        return config_prefix + ' '

    try:
        prefix = twtranslate(source, 'pywikibot-bot-prefix') + ' '
    except pywikibot.exceptions.TranslationError:
        # the 'pywikibot' package is available but the message key may
        # be missing
        prefix = 'Bot: '

    if config_prefix is True \
       or not hasattr(source, 'lang') \
       or source.isBot(source.username()):
        return prefix

    return ''


def twtranslate(
    source: STR_OR_SITE_TYPE,
    twtitle: str,
    parameters: Union[Sequence[str], Mapping[str, int], None] = None,
    *,
    fallback: bool = True,
    fallback_prompt: Optional[str] = None,
    only_plural: bool = False,
    bot_prefix: bool = False
) -> Optional[str]:
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

    >>> # this code snippet is running in test environment
    >>> # ignore test message "tests: max_retries reduced from 15 to 1"
    >>> import os
    >>> os.environ['PYWIKIBOT_TEST_QUIET'] = '1'

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

    .. versionchanged:: 8.1
       the *bot_prefix* parameter was added.

    :param source: When it's a site it's using the lang attribute and otherwise
        it is using the value directly. The site object is recommended.
    :param twtitle: The TranslateWiki string title, in <package>-<key> format
    :param parameters: For passing parameters. It should be a mapping but for
        backwards compatibility can also be a list, tuple or a single value.
        They are also used for plural entries in which case they must be a
        Mapping and will cause a TypeError otherwise.
    :param fallback: Try an alternate language code
    :param fallback_prompt: The English message if i18n is not available
    :param only_plural: Define whether the parameters should be only applied to
        plural instances. If this is False it will apply the parameters also
        to the resulting string. If this is True the placeholders must be
        manually applied afterwards.
    :param bot_prefix: If True, prepend the message with a bot prefix
        which depends on the ``config.bot_prefix`` setting
    :raise IndexError: If the language supports and requires more plurals than
        defined for the given translation template.
    """
    prefix = get_bot_prefix(source, use_prefix=bot_prefix)

    if not messages_available():
        if fallback_prompt:
            if parameters and not only_plural:
                return fallback_prompt % parameters
            return fallback_prompt

        raise pywikibot.exceptions.TranslationError(
            'Unable to load messages package {} for bundle {}'
            '\nIt can happen due to lack of i18n submodule or files. '
            'See {}/i18n'
            .format(_messages_package_name, twtitle, __url__))

    # if source is a site then use its lang attribute, otherwise it's a str
    lang = getattr(source, 'lang', source)

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
        raise pywikibot.exceptions.TranslationError(fill(
            'No {} translation has been defined for TranslateWiki key "{}". '
            'It can happen due to lack of i18n submodule or files or an '
            'outdated submodule. See {}/i18n'
            .format('English' if 'en' in langs else f"'{lang}'",
                    twtitle, __url__)))

    if '{{PLURAL:' in trans:
        # _extract_plural supports in theory non-mappings, but they are
        # deprecated
        if not isinstance(parameters, Mapping):
            raise TypeError('parameters must be a mapping.')
        trans = _extract_plural(alt, trans, parameters)

    if parameters is not None and not isinstance(parameters, Mapping):
        raise ValueError('parameters should be a mapping, not {}'
                         .format(type(parameters).__name__))

    if not only_plural and parameters:
        trans = trans % parameters
    return prefix + trans


def twhas_key(source: STR_OR_SITE_TYPE, twtitle: str) -> bool:
    """
    Check if a message has a translation in the specified language code.

    The translations are retrieved from i18n.<package>, based on the callers
    import table.

    No code fallback is made.

    :param source: When it's a site it's using the lang attribute and otherwise
        it is using the value directly.
    :param twtitle: The TranslateWiki string title, in <package>-<key> format
    """
    # If a site is given instead of a code, use its language
    lang = getattr(source, 'lang', source)
    transdict = _get_translation(lang, twtitle)
    return transdict is not None


def twget_keys(twtitle: str) -> List[str]:
    """
    Return all language codes for a special message.

    :param twtitle: The TranslateWiki string title, in <package>-<key> format

    :raises OSError: the package i18n cannot be loaded
    """
    # obtain the directory containing all the json files for this package
    package = twtitle.split('-')[0]
    mod = __import__(_messages_package_name, fromlist=['__file__'])
    pathname = os.path.join(next(iter(mod.__path__)), package)

    # build a list of languages in that directory
    langs = [removesuffix(filename, '.json')
             for filename in sorted(os.listdir(pathname))
             if filename.endswith('.json')]

    # exclude languages does not have this specific message in that package
    # i.e. an incomplete set of translated messages.
    return [lang for lang in langs
            if lang != 'qqq' and _get_translation(lang, twtitle)]


def bundles(stem: bool = False) -> Generator[Union[Path, str], None, None]:
    """A generator which yields message bundle names or its path objects.

    The bundle name usually corresponds with the script name which is
    localized.

    With ``stem=True`` the bundle names are given:

    >>> from pywikibot import i18n
    >>> bundles = sorted(i18n.bundles(stem=True))
    >>> len(bundles)
    37
    >>> bundles[:4]
    ['add_text', 'archivebot', 'basic', 'blockpageschecker']
    >>> bundles[-5:]
    ['undelete', 'unprotect', 'unusedfiles', 'weblinkchecker', 'welcome']
    >>> 'pywikibot' in bundles
    True

    With ``stem=False`` we get Path objects:

    >>> path = next(i18n.bundles())
    >>> path.is_dir()
    True
    >>> path.parent.as_posix()
    'scripts/i18n'

    .. versionadded:: 7.0

    :param stem: yield the Path.stem if True and the Path object otherwise
    """
    for dirpath in Path(*_messages_package_name.split('.')).iterdir():
        if dirpath.is_dir() and not dirpath.match('*__'):  # ignore cache
            if stem:
                yield dirpath.stem
            else:
                yield dirpath


def known_languages() -> List[str]:
    """All languages we have localizations for.

    >>> from pywikibot import i18n
    >>> i18n.known_languages()[:10]
    ['ab', 'aeb', 'af', 'am', 'an', 'ang', 'anp', 'ar', 'arc', 'ary']
    >>> i18n.known_languages()[-10:]
    ['vo', 'vro', 'wa', 'war', 'xal', 'xmf', 'yi', 'yo', 'yue', 'zh']
    >>> len(i18n.known_languages())
    253

    The implementation is roughly equivalent to:

    .. code-block:: Python

       langs = set()
       for dirpath in bundles():
           for fname in dirpath.iterdir():
               if fname.suffix == '.json':
                   langs.add(fname.stem)
        return sorted(langs)

    .. versionadded:: 7.0
    """
    return sorted(
        {fname.stem for dirpath in bundles() for fname in dirpath.iterdir()
         if fname.suffix == '.json'}
    )


def input(twtitle: str,
          parameters: Optional[Mapping[str, int]] = None,
          password: bool = False,
          fallback_prompt: Optional[str] = None) -> str:
    """
    Ask the user a question, return the user's answer.

    The prompt message is retrieved via :py:obj:`twtranslate` and uses the
    config variable 'userinterface_lang'.

    :param twtitle: The TranslateWiki string title, in <package>-<key> format
    :param parameters: The values which will be applied to the translated text
    :param password: Hides the user's input (for password entry)
    :param fallback_prompt: The English prompt if i18n is not available.
    """
    if messages_available():
        code = config.userinterface_lang
        prompt = twtranslate(code, twtitle, parameters)
    elif fallback_prompt:
        prompt = fallback_prompt
    else:
        raise pywikibot.exceptions.TranslationError(
            'Unable to load messages package {} for bundle {}'
            .format(_messages_package_name, twtitle))
    return pywikibot.input(prompt, password)


if not messages_available():
    set_messages_package('pywikibot.scripts.i18n')
