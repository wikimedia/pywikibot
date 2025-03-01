"""Functions for manipulating wiki-text."""
#
# (C) Pywikibot team, 2008-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import itertools
import re
from collections import OrderedDict
from collections.abc import Sequence
from contextlib import closing, suppress
from html.parser import HTMLParser
from typing import NamedTuple

import pywikibot
from pywikibot.backports import Callable, Container, Iterable, Match
from pywikibot.backports import OrderedDict as OrderedDictType
from pywikibot.backports import Pattern
from pywikibot.backports import Sequence as SequenceType
from pywikibot.backports import pairwise
from pywikibot.exceptions import InvalidTitleError, SiteDefinitionError
from pywikibot.family import Family
from pywikibot.time import TZoneFixedOffset
from pywikibot.tools import (
    deprecated,
    deprecated_args,
    first_lower,
    first_upper,
)
from pywikibot.userinterfaces.transliteration import NON_LATIN_DIGITS


try:
    import wikitextparser
except ImportError:
    import mwparserfromhell as wikitextparser


# cache for replaceExcept to avoid recompile or regexes each call
_regex_cache: dict[str, Pattern[str]] = {}

# The regex below collects nested templates, providing simpler
# identification of templates used at the top-level of wikitext.
# It doesn't match {{{1|...}}}, however it also does not match templates
# with a numerical name. e.g. {{1|..}}. It will correctly match {{{x}} as
# being {{x}} with leading '{' left in the wikitext.
# Prefix msg: is not included in the 'name' group, but all others are
# included for backwards compatibility with TEMP_REGEX.
# Only parser functions using # are excluded.
# When more than two levels of templates are found, this regex will
# capture from the beginning of the first {{ to the end of the last }},
# with wikitext between templates as part of the parameters of the first
# template in the wikitext.
# This ensures it fallsback to a safe mode for replaceExcept, as it
# ensures that any replacement will not occur within template text.
NESTED_TEMPLATE_REGEX = re.compile(r"""
{{\s*(?:msg:\s*)?
  (?P<name>[^{\|#0-9][^{\|#]*?)\s*
  (?:\|(?P<params> [^{]*?
          (({{{[^{}]+?}}}
            |{{[^{}]+?}}
            |{[^{}]*?}
          ) [^{]*?
        )*?
    )?
  )?
}}
|
(?P<unhandled_depth>{{\s*[^{\|#0-9][^{\|#]*?\s* [^{]* {{ .* }})
""", re.VERBOSE | re.DOTALL)

# The following regex supports wikilinks anywhere after the first pipe
# and correctly matches the end of the file link if the wikilink contains
# [[ or ]].
# The namespace names must be substituted into this regex.
# e.g. FILE_LINK_REGEX % 'File'
# or FILE_LINK_REGEX % '|'.join(site.namespaces[6])
FILE_LINK_REGEX = r"""
    \[\[\s*
    (?:%s)  # namespace aliases
    \s*:
    (?=(?P<filename>
        [^]|]*
    ))(?P=filename)
    (
        \|
        (
            (
                (?=(?P<inner_link>
                    \[\[.*?\]\]
                ))(?P=inner_link)
            )?
            (?=(?P<other_chars>
                [^\[\]]*
            ))(?P=other_chars)
        |
            (?=(?P<not_wikilink>
                \[[^]]*\]
            ))(?P=not_wikilink)
        )*?
    )??
    \]\]
"""

# Used in TimeStripper. When a timestamp-like line has longer gaps
# than this between year, month, etc in it, then the line will not be
# considered to contain a timestamp.
TIMESTAMP_GAP_LIMIT = 10


def to_local_digits(phrase: str | int, lang: str) -> str:
    """Change Latin digits based on language to localized version.

    Be aware that this function only works for several languages, and that it
    returns an unchanged string if an unsupported language is given.

    .. versionchanged:: 7.5
       always return a string even `phrase` is an int.

    :param phrase: The phrase to convert to localized numerical
    :param lang: language code
    :return: The localized version
    """
    digits = NON_LATIN_DIGITS.get(lang)
    phrase = str(phrase)
    if digits:
        trans = str.maketrans('0123456789', digits)
        phrase = phrase.translate(trans)
    return phrase


def to_latin_digits(phrase: str,
                    langs: SequenceType[str] | str | None = None) -> str:
    """Change non-latin digits to latin digits.

    .. versionadded:: 7.0

    :param phrase: The phrase to convert to latin numerical.
    :param langs: Language codes. If langs parameter is None, use all
        known languages to convert.
    :return: The string with latin digits
    """
    if langs is None:
        langs = NON_LATIN_DIGITS.keys()
    elif isinstance(langs, str):
        langs = [langs]

    digits = [NON_LATIN_DIGITS[key] for key in langs
              if key in NON_LATIN_DIGITS]
    if digits:
        trans = str.maketrans(''.join(digits), '0123456789' * len(digits))
        phrase = phrase.translate(trans)
    return phrase


def case_escape(case: str, string: str, *, underscore: bool = False) -> str:
    """Return an escaped regex pattern which depends on 'first-letter' case.

    .. versionadded:: 7.0
    .. versionchanged:: 8.4
       Added the optional *underscore* parameter.

    :param case: if `case` is 'first-letter', the regex contains an
        inline re.IGNORECASE flag for the first letter
    :param underscore: if True, expand the regex to detect spaces and
        underscores which are interchangeable and collapsible
    """
    if case == 'first-letter':
        pattern = f'(?i:{string[:1]}){re.escape(string[1:])}'
    else:
        pattern = re.escape(string)
    if underscore:
        pattern = re.sub(r'_|\\ ', '[_ ]+', pattern)
    return pattern


class MultiTemplateMatchBuilder:

    """Build template matcher."""

    def __init__(self, site) -> None:
        """Initializer."""
        self.site = site

    def pattern(self, template, flags=re.DOTALL):
        """Return a compiled regex to match template."""
        # TODO: add ability to also match contents within the template
        # TODO: add option for template to be None to match any template
        # TODO: merge regex with NESTED_TEMPLATE_REGEX
        namespace = self.site.namespaces[10]
        if isinstance(template, pywikibot.Page):
            if template.namespace() != 10:
                raise ValueError(f'{template} is not a template Page object')

            old = template.title(with_ns=False)
        elif isinstance(template, str):
            old = template
        else:
            raise ValueError(f'{template!r} is not a valid template')

        pattern = case_escape(namespace.case, old)
        # namespaces may be any mixed case
        namespaces = [ignore_case(ns) for ns in namespace]
        namespaces.append(ignore_case('msg'))
        pattern = re.sub(r'_|\\ ', r'[_ ]', pattern)
        templateRegexP = (
            r'{{\s*(%(namespace)s:)?%(pattern)s'
            r'(?P<parameters>\s*\|[^{]+?'
            r'((({{{[^{}]+?}}}|{{[^{}]+?}}|{[^{}]*?})[^{]*?)*?)?'
            r'|)\s*}}'
        ) % {'namespace': ':|'.join(namespaces), 'pattern': pattern}
        templateRegex = re.compile(templateRegexP, flags)
        return templateRegex

    def search_any_predicate(self, templates):
        """Return a predicate that matches any template."""
        predicates = [self.pattern(template).search for template in templates]
        return lambda text: any(predicate(text) for predicate in predicates)


def ignore_case(string: str) -> str:
    """Return a case-insensitive pattern for the string.

    .. versionchanged:: 7.2
       `_ignore_case` becomes a public method
    """
    return ''.join(
        f'[{c}{s}]' if c != s else c
        for s, c in zip(string, string.swapcase()))


def _tag_pattern(tag_name: str) -> str:
    """Return a tag pattern for the given tag name."""
    return (
        rf'<{ignore_case(tag_name)}(?:>|\s+[^>]*(?<!/)>)'  # start tag
        r'[\s\S]*?'  # contents
        rf'</{ignore_case(tag_name)}\s*>'  # end tag
    )


def _tag_regex(tag_name: str):
    """Return a compiled tag regex for the given tag name."""
    return re.compile(_tag_pattern(tag_name))


def _create_default_regexes() -> None:
    """Fill (and possibly overwrite) ``_regex_cache`` with default regexes.

    The following keys are provided: ``category``, ``comment``, ``file``,
    ``header``, ``hyperlink``, ``interwiki``, ``invoke``, ``link``,
    ``pagelist``, ``property``, ``startcolon``, ``startspace``, ``table``,
    ``template``.

    :meta public:
    """
    _regex_cache.update({
        # categories
        'category': (r'\[\[ *(?:%s)\s*:.*?\]\]',
                     lambda site: '|'.join(site.namespaces[14])),
        'comment': re.compile(r'<!--[\s\S]*?-->'),
        # files
        'file': (FILE_LINK_REGEX, lambda site: '|'.join(site.namespaces[6])),
        # section headers
        'header': re.compile(
            r'(?:(?<=\n)|\A)(?:<!--[\s\S]*?-->)*'
            r'(=(?:[^\n]|<!--[\s\S]*?-->)+=)'
            r' *(?:<!--[\s\S]*?--> *)*(?=\n|\Z)'),
        # external links
        'hyperlink': compileLinkR(),
        # also finds links to foreign sites with preleading ":"
        'interwiki': (
            r'\[\[:?(%s)\s?:[^\]]*\]\]\s*',
            lambda site: '|'.join(
                ignore_case(i) for i in site.validLanguageLinks()
                + list(site.family.obsolete.keys()))),
        # Module invocations (currently only Lua)
        'invoke': (
            r'\{\{\s*\#(?:%s):[\s\S]*?\}\}',
            lambda site: '|'.join(
                ignore_case(mw) for mw in site.getmagicwords('invoke'))),
        # this matches internal wikilinks, but also interwiki, categories, and
        # images.
        'link': re.compile(r'\[\[[^\]|]*(\|[^\]]*)?\]\]'),
        # pagelist tag (used in Proofread extension).
        'pagelist': re.compile(r'<{}[\s\S]*?/>'
                               .format(ignore_case('pagelist'))),
        # Wikibase property inclusions
        'property': (
            r'\{\{\s*\#(?:%s):\s*[Pp]\d+.*?\}\}',
            lambda site: '|'.join(
                ignore_case(mw) for mw in site.getmagicwords('property'))),
        # lines that start with a colon or more will be indented
        'startcolon': re.compile(r'(?:(?<=\n)|\A):(.*?)(?=\n|\Z)'),
        # lines that start with a space are shown in a monospace font and
        # have whitespace preserved.
        'startspace': re.compile(r'(?:(?<=\n)|\A) (.*?)(?=\n|\Z)'),
        # tables often have whitespace that is used to improve wiki
        # source code readability.
        # TODO: handle nested tables.
        'table': re.compile(
            r'(?:(?<=\n)|\A){\|[\S\s]*?\n\|}|%s' % _tag_pattern('table')),
        'template': NESTED_TEMPLATE_REGEX,
    })


def get_regexes(
    keys: str | Iterable[str],
    site: pywikibot.site.BaseSite | None = None
) -> list[Pattern[str]]:
    """Fetch compiled regexes.

    .. versionchanged:: 8.2
       ``_get_regexes`` becomes a public function.
       *keys* may be a single string; *site* is optional.

    :param keys: a single key or an iterable of keys whose regex pattern
        should be given
    :param site: a BaseSite object needed for ``category``, ``file``,
        ``interwiki``, ``invoke`` and ``property`` keys
    :raises ValueError: site cannot be None.
    """
    if not _regex_cache:
        _create_default_regexes()

    if isinstance(keys, str):
        keys = [keys]

    result = []
    for exc in keys:
        if not isinstance(exc, str):
            # assume it's a regular expression
            result.append(exc)
            continue

        # assume the string is a reference to a standard regex above,
        # which may not yet have a site specific re compiled.
        if exc not in _regex_cache:
            # nowiki, noinclude, includeonly, timeline, math and other
            # extensions
            _regex_cache[exc] = _tag_regex(exc)
            result.append(_regex_cache[exc])
        elif not isinstance(_regex_cache[exc], tuple):
            result.append(_regex_cache[exc])
        else:
            if not site and exc in ('interwiki', 'property', 'invoke',
                                    'category', 'file'):
                raise ValueError(f'site cannot be None for the {exc!r} regex')

            if (exc, site) not in _regex_cache:
                re_text, re_var = _regex_cache[exc]
                _regex_cache[(exc, site)] = re.compile(
                    re_text % re_var(site), re.VERBOSE)

            result.append(_regex_cache[(exc, site)])

        # handle aliases
        if exc == 'source':
            result.append(_tag_regex('syntaxhighlight'))
        elif exc == 'syntaxhighlight':
            result.append(_tag_regex('source'))
        elif exc == 'chem':
            result.append(_tag_regex('ce'))
        elif exc == 'math':
            result.append(_tag_regex('chem'))
            result.append(_tag_regex('ce'))

    return result


def replaceExcept(text: str,
                  old: str | Pattern[str],
                  new: str | Callable[[Match[str]], str],
                  exceptions: SequenceType[str | Pattern[str]],
                  caseInsensitive: bool = False,
                  allowoverlap: bool = False,
                  marker: str = '',
                  site: pywikibot.site.BaseSite | None = None,
                  count: int = 0) -> str:
    """Return text with *old* replaced by *new*, ignoring specified text types.

    Skip occurrences of *old* within *exceptions*; e.g. within nowiki
    tags or HTML comments. If *caseInsensitive* is true, then use case
    insensitive regex matching. If *allowoverlap* is true, overlapping
    occurrences are all replaced

    .. caution:: Watch out when using *allowoverlap*, it might lead to
       infinite loops!

    :param text: text to be modified
    :param old: a compiled or uncompiled regular expression
    :param new: a string (which can contain regular expression
        references), or a function which takes a match object as
        parameter. See parameter *repl* of ``re.sub()``.
    :param exceptions: a list of strings or already compiled regex
        objects which signal what to leave out. List of strings might be
        like ``['math', 'table', 'template']`` for example.
    :param marker: a string that will be added to the last replacement;
        if nothing is changed, it is added at the end
    :param count: how many replacements to do at most. See parameter
        *count* of ``re.sub()``.
    """
    # if we got a string, compile it as a regular expression
    if isinstance(old, str):
        old = re.compile(old, flags=re.IGNORECASE if caseInsensitive else 0)

    # early termination if not relevant
    if not old.search(text):
        return text + marker

    dontTouchRegexes = get_regexes(exceptions, site)

    index = 0
    replaced = 0
    markerpos = len(text)
    while not count or replaced < count:
        if index > len(text):
            break

        match = old.search(text, index)
        if not match:
            # nothing left to replace
            break

        # check which exception will occur next.
        nextExceptionMatch = None
        for dontTouchR in dontTouchRegexes:
            excMatch = dontTouchR.search(text, index)
            if excMatch and (
                    nextExceptionMatch is None
                    or excMatch.start() < nextExceptionMatch.start()):
                nextExceptionMatch = excMatch

        if nextExceptionMatch is not None \
                and nextExceptionMatch.start() <= match.start():
            # an HTML comment or text in nowiki tags stands before the next
            # valid match. Skip.
            index = nextExceptionMatch.end()
            continue

        # We found a valid match. Replace it.
        if callable(new):
            # the parameter new can be a function which takes the match
            # as a parameter.
            replacement = new(match)
        else:
            # it is not a function, but a string.

            # it is a little hack to make \n work. It would be better
            # to fix it previously, but better than nothing.
            new = new.replace('\\n', '\n')

            # We cannot just insert the new string, as it may contain regex
            # group references such as \2 or \g<name>.
            # On the other hand, this approach does not work because it
            # can't handle lookahead or lookbehind (see bug T123185).
            # So we have to process the group references manually.
            replacement = ''

            group_regex = re.compile(r'\\(\d+)|\\g<(.+?)>')
            last = 0
            for group_match in group_regex.finditer(new):
                group_id = group_match[1] or group_match[2]
                with suppress(ValueError):
                    group_id = int(group_id)

                try:
                    replacement += new[last:group_match.start()]
                    replacement += match[group_id] or ''
                except IndexError:
                    raise IndexError(f'Invalid group reference: {group_id}\n'
                                     f'Groups found: {match.groups()}')
                last = group_match.end()
            replacement += new[last:]

        text = text[:match.start()] + replacement + text[match.end():]

        # continue the search on the remaining text
        if allowoverlap:
            index = match.start() + 1
        else:
            index = match.start() + len(replacement)

        if not match.group():
            # When the regex allows to match nothing, shift by one char
            index += 1

        markerpos = match.start() + len(replacement)
        replaced += 1

    return text[:markerpos] + marker + text[markerpos:]


def removeDisabledParts(text: str,
                        tags: Iterable | None = None,
                        include: Container | None = None,
                        site: pywikibot.site.BaseSite | None = None
                        ) -> str:
    """Return text without portions where wiki markup is disabled.

    Parts that will be removed by default are:

    * HTML comments
    * nowiki tags
    * pre tags
    * includeonly tags
    * source and syntaxhighlight tags

    .. versionchanged:: 7.0
       the order of removals will correspond to the tags argument
       if provided as an ordered collection (list, tuple)

    :param tags: The exact set of parts which should be removed using
        keywords from :func:`get_regexes`.
    :param include: Or, in alternative, default parts that shall not
        be removed.
    :param site: Site to be used for site-dependent regexes. Default
        disabled parts listed above do not need it.
    :return: text stripped from disabled parts.
    """
    if not tags:
        tags = ['comment', 'includeonly', 'nowiki', 'pre', 'syntaxhighlight']
    # avoid set(tags) because sets are internally ordered using the hash
    # which for strings is salted per Python process => the output of
    # this function would likely be different per script run because
    # the replacements would be done in different order and the disabled
    # parts may overlap and suppress each other
    # see https://docs.python.org/3/reference/datamodel.html#object.__hash__
    # ("Note" at the end of the section)
    if include:
        tags = [tag for tag in tags if tag not in include]
    regexes = get_regexes(tags, site)
    for regex in regexes:
        text = regex.sub('', text)
    return text


def removeHTMLParts(text: str, keeptags: list[str] | None = None) -> str:
    """Return text without portions where HTML markup is disabled.

    Parts that can/will be removed are HTML tags and all wiki tags. The
    exact set of parts which should NOT be removed can be passed as the
    *keeptags* parameter, which defaults to
    ``['tt', 'nowiki', 'small', 'sup']``.

    **Example:**

    >>> removeHTMLParts('<div><b><ref><tt>Hi all!</tt></ref></b></div>')
    '<tt>Hi all!</tt>'

    .. seealso:: :class:`_GetDataHTML`
    """
    # TODO: try to merge with 'removeDisabledParts()' above into one generic
    # function
    parser = _GetDataHTML()
    if keeptags is None:
        keeptags = ['tt', 'nowiki', 'small', 'sup']
    with closing(parser):
        parser.keeptags = keeptags
        parser.feed(text)
    return parser.textdata


class _GetDataHTML(HTMLParser):

    """HTML parser which removes html tags except they are listed in keeptags.

    The parser is used by :func:`removeHTMLParts` similar to this:

    .. code-block:: python

       from contextlib import closing
       from pywikibot.textlib import _GetDataHTML
       with closing(_GetDataHTML()) as parser:
           parser.keeptags = ['html']
           parser.feed('<html><head><title>Test</title></head>'
                       '<body><h1><!-- Parse --> me!</h1></body></html>')
           print(parser.textdata)

    The result is:

    .. code-block:: html

       <html>Test me!</html>

    .. versionchanged:: 9.2
       This class is no longer a context manager;
       :pylib:`contextlib.closing()<contextlib#contextlib.closing>`
       should be used instead.

    .. seealso::
       - :pylib:`html.parser`
       - :pylib:`contextlib#contextlib.closing`

    :meta public:
    """

    textdata = ''
    keeptags: list[str] = []

    def handle_data(self, data) -> None:
        """Add data to text."""
        self.textdata += data

    def handle_starttag(self, tag, attrs) -> None:
        """Add start tag to text if tag should be kept."""
        if tag in self.keeptags:
            self.textdata += f'<{tag}>'

    def handle_endtag(self, tag) -> None:
        """Add end tag to text if tag should be kept."""
        if tag in self.keeptags:
            self.textdata += f'</{tag}>'


def isDisabled(text: str, index: int, tags=None) -> bool:
    """Return True if text[index] is disabled, e.g. by a comment or nowiki tag.

    For the tags parameter, see :py:obj:`removeDisabledParts`.
    """
    # Find a marker that is not already in the text.
    marker = findmarker(text)
    text = text[:index] + marker + text[index:]
    text = removeDisabledParts(text, tags)
    return marker not in text


def findmarker(text: str, startwith: str = '@@',
               append: str | None = None) -> str:
    """Find a string which is not part of text."""
    if not append:
        append = '@'
    mymarker = startwith
    while mymarker in text:
        mymarker += append
    return mymarker


def expandmarker(text: str, marker: str = '', separator: str = '') -> str:
    """Return a marker expanded whitespace and the separator.

    It searches for the first occurrence of the marker and gets the combination
    of the separator and whitespace directly before it.

    :param text: the text which will be searched.
    :param marker: the marker to be searched.
    :param separator: the separator string allowed before the marker. If empty
        it won't include whitespace too.
    :return: the marker with the separator and whitespace from the text in
        front of it. It'll be just the marker if the separator is empty.
    """
    # set to remove any number of separator occurrences plus arbitrary
    # whitespace before, after, and between them,
    # by allowing to include them into marker.
    if separator:
        firstinmarker = text.find(marker)
        firstinseparator = firstinmarker
        lenseparator = len(separator)
        striploopcontinue = True
        while firstinseparator > 0 and striploopcontinue:
            striploopcontinue = False
            if (firstinseparator >= lenseparator
                and separator == text[firstinseparator
                                      - lenseparator:firstinseparator]):
                firstinseparator -= lenseparator
                striploopcontinue = True
            elif text[firstinseparator - 1] < ' ':
                firstinseparator -= 1
                striploopcontinue = True
        marker = text[firstinseparator:firstinmarker] + marker
    return marker


def replace_links(text: str, replace, site: pywikibot.site.BaseSite) -> str:
    """Replace wikilinks selectively.

    The text is searched for a link and on each link it replaces the text
    depending on the result for that link. If the result is just None it skips
    that link. When it's False it unlinks it and just inserts the label. When
    it is a Link instance it'll use the target, section and label from that
    Link instance. If it's a Page instance it'll use just the target from the
    replacement and the section and label from the original link.

    If it's a string and the replacement was a sequence it converts it into a
    Page instance. If the replacement is done via a callable it'll use it like
    unlinking and directly replace the link with the text itself.

    If either the section or label should be used the replacement can be a
    function which returns a Link instance and copies the value which should
    remaining.

    .. versionchanged:: 7.0
       `site` parameter is mandatory

    :param text: the text in which to replace links
    :param replace: either a callable which reacts like described above.
        The callable must accept four parameters link, text, groups, rng and
        allows for user interaction. The groups are a dict containing 'title',
        'section', 'label' and 'linktrail' and the rng are the start and end
        position of the link. The 'label' in groups contains everything after
        the first pipe which might contain additional data which is used in
        File namespace for example.
        Alternatively it can be a sequence containing two items where the first
        must be a Link or Page and the second has almost the same meaning as
        the result by the callable. It'll convert that into a callable where
        the first item (the Link or Page) has to be equal to the found link and
        in that case it will apply the second value from the sequence.
    :type replace: sequence of pywikibot.Page/pywikibot.Link/str or
        callable
    :param site: a Site object to use. It should match the origin or
        target site of the text
    :raises TypeError: missing positional argument 'site'
    :raises ValueError: Wrong site type
    :raises ValueError: Wrong replacement number
    :raises ValueError: Wrong replacement types
    """
    def to_link(source):
        """Return the link from source when it's a Page otherwise itself."""
        if isinstance(source, pywikibot.Page):
            return source._link
        if isinstance(source, str):
            return pywikibot.Link(source, site)
        return source

    def replace_callable(link, text, groups, rng):
        if replace_list[0] == link:
            return replace_list[1]
        return None

    def check_classes(replacement):
        """Normalize the replacement into a list."""
        if not isinstance(replacement, (pywikibot.Page, pywikibot.Link)):
            raise ValueError('The replacement must be None, False, a'
                             ' sequence, a Link or a str but is '
                             f'"{type(replacement)}"')

    def title_section(link) -> str:
        title = link.title
        if link.section:
            title += '#' + link.section
        return title

    if not isinstance(site, pywikibot.site.BaseSite):
        raise ValueError('The "site" argument must be a BaseSite not '
                         f'{type(site).__name__}.')

    if isinstance(replace, Sequence):
        if len(replace) != 2:
            raise ValueError('When used as a sequence, the "replace" '
                             'argument must contain exactly 2 items.')
        replace_list = [to_link(replace[0]), replace[1]]
        if not isinstance(replace_list[0], pywikibot.Link):
            raise ValueError(
                'The original value must be either str, Link or Page but is '
                f'"{type(replace_list[0])}"')
        if replace_list[1] is not False and replace_list[1] is not None:
            if isinstance(replace_list[1], str):
                replace_list[1] = pywikibot.Page(site, replace_list[1])
            check_classes(replace_list[0])
        replace = replace_callable

    linktrail = site.linktrail()
    link_pattern = re.compile(
        r'\[\[(?P<title>.*?)(#(?P<section>.*?))?(\|(?P<label>.*?))?\]\]'
        rf'(?P<linktrail>{linktrail})'
    )
    extended_label_pattern = re.compile(fr'(.*?\]\])({linktrail})')
    linktrail = re.compile(linktrail)
    curpos = 0
    # This loop will run until we have finished the current page
    while True:
        m = link_pattern.search(text, pos=curpos)
        if not m:
            break

        m_title = m['title'].strip()

        # Ignore links to sections of the same page
        if not m_title:
            curpos = m.end()
            continue

        # Ignore interwiki links
        if site.isInterwikiLink(m_title) and not m_title.startswith(':'):
            curpos = m.end()
            continue

        groups = m.groupdict()
        if groups['label'] and '[[' in groups['label']:
            # TODO: Work on the link within the label too
            # A link within a link, extend the label to the ]] after it
            extended_match = extended_label_pattern.search(text, pos=m.end())
            if not extended_match:
                # TODO: Unclosed link label, what happens there?
                curpos = m.end()
                continue
            groups['label'] += groups['linktrail'] + extended_match[1]
            groups['linktrail'] = extended_match[2]
            end = extended_match.end()
        else:
            end = m.end()

        start = m.start()
        # Since this point the m variable shouldn't be used as it may not
        # contain all contents
        del m

        try:
            link = pywikibot.Link.create_separated(
                groups['title'], site, section=groups['section'],
                label=groups['label'])
        except (SiteDefinitionError, InvalidTitleError):
            # unrecognized iw prefix or invalid title
            curpos = end
            continue

        # Check whether the link found should be replaced.
        # Either None, False or tuple(Link, bool)
        new_link = replace(link, text, groups.copy(), (start, end))
        if new_link is None:
            curpos = end
            continue

        # The link looks like this:
        # [[page_title|new_label]]new_linktrail
        page_title = groups['title']
        new_label = groups['label']

        if not new_label:
            # or like this: [[page_title]]new_linktrail
            new_label = page_title
            # remove preleading ":" from the link text
            if new_label[0] == ':':
                new_label = new_label[1:]

        new_linktrail = groups['linktrail']
        if new_linktrail:
            new_label += new_linktrail

        if new_link is False:
            # unlink - we remove the section if there's any
            assert isinstance(new_label, str), 'link text must be str.'
            new_link = new_label

        if isinstance(new_link, str):
            text = text[:start] + new_link + text[end:]
            # Make sure that next time around we will not find this same hit.
            curpos = start + len(new_link)
            continue

        if isinstance(new_link, bytes):
            raise ValueError('The result must be str and not bytes.')

        # Verify that it's either Link, Page or str
        check_classes(new_link)
        # Use section and label if it's a Link and not otherwise
        if isinstance(new_link, pywikibot.Link):
            is_link = True
        else:
            new_link = new_link._link
            is_link = False

        new_title = new_link.canonical_title()
        # Make correct langlink if needed
        if new_link.site != site:
            new_title = ':' + new_link.site.code + ':' + new_title

        if is_link:
            # Use link's label
            new_label = new_link.anchor
            must_piped = new_label is not None
            new_section = new_link.section
        else:
            must_piped = True
            new_section = groups['section']

        if new_section:
            new_title += '#' + new_section

        if new_label is None:
            new_label = new_title

        # Parse the link text and check if it points to the same page
        parsed_new_label = pywikibot.Link(new_label, new_link.site)
        try:
            parsed_new_label.parse()
        except InvalidTitleError:
            pass
        else:
            parsed_link_title = title_section(parsed_new_label)
            new_link_title = title_section(new_link)
            # compare title, but only with parts if linktrail works
            if not linktrail.sub('',
                                 parsed_link_title[len(new_link_title):]):
                # TODO: This must also compare everything that was used as a
                #       prefix (in case insensitive)
                must_piped = (
                    not parsed_link_title.startswith(new_link_title)
                    or parsed_new_label.namespace != new_link.namespace)

        if must_piped:
            new_text = f'[[{new_title}|{new_label}]]'
        else:
            new_text = (f'[[{new_label[:len(new_title)]}]]'
                        f'{new_label[len(new_title):]}')

        text = text[:start] + new_text + text[end:]
        # Make sure that next time around we will not find this same hit.
        curpos = start + len(new_text)
    return text


def add_text(text: str, add: str, *, site=None) -> str:
    """Add text to a page content above categories and interwiki.

    .. versionadded:: 6.4

    :param text: The page content to add text to.
    :param add: Text to add.
    :param site: The site that the text is coming from. Required for
        reorder of categories and interlanguage links. Te default site
        is used otherwise.
    :type site: pywikibot.Site
    """
    # Translating the \\n (e.g. from command line) into binary \n
    add = add.replace('\\n', '\n')

    # Getting the categories
    categories_inside = getCategoryLinks(text, site)
    # Deleting the categories
    text = removeCategoryLinks(text, site)
    # Getting the interwiki
    interwiki_inside = getLanguageLinks(text, site)
    # Removing the interwiki
    text = removeLanguageLinks(text, site)

    # Adding the text
    text += '\n' + add
    # Reputting the categories
    text = replaceCategoryLinks(text, categories_inside, site, add_only=True)
    # Adding the interwiki
    return replaceLanguageLinks(text, interwiki_inside, site)


# -------------------------------
# Functions dealing with sections
# -------------------------------

#: Head pattern
HEAD_PATTERN = re.compile(r'(={1,6}).+\1', re.DOTALL)
TITLE_PATTERN = re.compile("'{3}([^']+)'{3}")


class _Heading(NamedTuple):
    text: str
    start: int
    end: int


class Section(NamedTuple):

    """A namedtuple as part of :class:`Content` describing a page section.

    .. versionchanged:: 8.2
       ``_Section`` becomes a public class.
    """

    title: str  #: section title including equal signs
    content: str  #: section content

    @property
    def level(self) -> int:
        """Return the section level.

        .. versionadded:: 8.2
        """
        m = HEAD_PATTERN.match(self.title)
        return len(m[1])

    @property
    def heading(self) -> str:
        """Return the section title without equal signs.

        .. versionadded:: 8.2
        """
        level = self.level
        return self.title[level:-level].strip()


class Content(NamedTuple):

    """A namedtuple as result of :func:`extract_sections` holding page content.

    .. versionchanged:: 8.2
       ``_Content`` becomes a public class.
    """

    header: str  #: the page header
    sections: list[Section]  #: the page sections
    footer: str  #: the page footer

    @property
    def title(self) -> str:
        """Return the first main title found on the page.

        The first main title is anything enclosed within triple quotes.

        .. versionadded:: 8.2
        """
        m = TITLE_PATTERN.search(self.header)
        return m[1].strip() if m else ''


def _extract_headings(text: str) -> list[_Heading]:
    """Return _Heading objects."""
    headings = []
    heading_regex = get_regexes('header')[0]
    for match in heading_regex.finditer(text):
        start, end = match.span(1)
        if not isDisabled(text, start) and not isDisabled(text, end):
            headings.append(_Heading(match[1], start, end))
    return headings


def _extract_sections(text: str, headings) -> list[Section]:
    """Return a list of :class:`Section` objects."""
    sections = []
    if headings:
        # Assign them their contents
        for heading, next_heading in pairwise(headings):
            content = text[heading.end:next_heading.start]
            sections.append(Section(heading.text, content))
        last = headings[-1]
        sections.append(Section(last.text, text[last.end:]))

    return sections


def extract_sections(
    text: str,
    site: pywikibot.site.BaseSite | None = None,
) -> Content:
    """Return section headings and contents found in text.

    The returned namedtuple :class:`Content` contains the text parsed
    into *header*, *sections* and *footer* parts. The main title found
    in the header which is the first text enclosed with ''' like
    '''page title''' can be given by the *title* property.

    The header part is a string containing text part above the first
    heading.

    The sections part is a list of :class:`Section` namedtuples, each
    tuple containing a string with section title (including equal signs),
    and a string with the section content. In addition the section
    heading (the title without equal signs) can be given by the *heading*
    property. Also the section level can be found by the *level*
    property which is the number of the equal signs around the section
    heading.

    The footer part is also a string containing text part after the last
    section.

    **Examples:**

    >>> text = \"\"\"
    ... '''this''' is a Python module.
    ...
    ... == History of this ==
    ... This set of principles was posted in 1999...
    ...
    ... == Usage of this ==
    ... Enter "import this" for usage...
    ...
    ... === Details ===
    ... The Zen of Python...
    ...
    ... [[Category:Programming principles]]
    ... \"\"\"
    >>> site = pywikibot.Site('wikipedia:en')
    >>> result = extract_sections(text, site)
    >>> result.header.strip()
    "'''this''' is a Python module."
    >>> result.sections[0].title
    '== History of this =='
    >>> result.sections[1].content.strip()
    'Enter "import this" for usage...'
    >>> result.sections[2].heading
    'Details'
    >>> result.sections[2].level
    3
    >>> result.footer.strip()
    '[[Category:Programming principles]]'
    >>> result.title
    'this'

    .. note:: sections and text from templates are not extracted but
       embedded as plain text.
    .. versionadded:: 3.0
    .. versionchanged:: 8.2
       The :class:`Content` and :class:`Section` class have additional
       properties.

    :return: The parsed namedtuple.
    """  # noqa: D300, D301
    headings = _extract_headings(text)
    sections = _extract_sections(text, headings)
    # Find header and footer contents
    header = text[:headings[0].start] if headings else text
    cat_regex, interwiki_regex = get_regexes(['category', 'interwiki'], site)
    langlink_pattern = interwiki_regex.pattern.replace(':?', '')
    last_section_content = sections[-1].content if sections else header
    footer = re.search(fr'({langlink_pattern}|{cat_regex.pattern}|\s)*\Z',
                       last_section_content).group().lstrip()

    if footer:
        if sections:
            sections[-1] = Section(
                sections[-1].title, last_section_content[:-len(footer)])
        else:
            header = header[:-len(footer)]

    return Content(header, sections, footer)


# -----------------------------------------------
# Functions dealing with interwiki language links
# -----------------------------------------------
# Note - MediaWiki supports several kinds of interwiki links; two kinds are
#        inter-language links. We deal here with those kinds only.
#        A family has by definition only one kind of inter-language links:
#        1 - inter-language links inside the own family.
#            They go to a corresponding page in another language in the same
#            family, such as from 'en.wikipedia' to 'pt.wikipedia', or from
#            'es.wiktionary' to 'ar.wiktionary'.
#            Families with this kind have several language-specific sites.
#            They have their interwiki_forward attribute set to None
#        2 - language links forwarding to another family.
#            They go to a corresponding page in another family, such as from
#            'commons' to 'zh.wikipedia, or from 'incubator' to 'en.wikipedia'.
#            Families having those have one member only, and do not have
#            language-specific sites. The name of the target family of their
#            inter-language links is kept in their interwiki_forward attribute.
#        These functions only deal with links of these two kinds only. They
#        do not find or change links of other kinds, nor any that are formatted
#        as in-line interwiki links (e.g., "[[:es:Artículo]]".

def getLanguageLinks(
    text: str,
    insite=None,
    template_subpage: bool = False
) -> dict[pywikibot.site.BaseSite, pywikibot.Page]:
    """Return a dict of inter-language links found in text.

    The returned dict uses the site as keys and Page objects as values.
    It does not contain its own site.

    Do not call this routine directly, use
    :meth:`page.BasePage.interwiki` method instead.
    """
    if insite is None:
        insite = pywikibot.Site()
    fam = insite.family
    # when interwiki links forward to another family, retrieve pages & other
    # infos there
    if fam.interwiki_forward:
        fam = Family.load(fam.interwiki_forward)
    result: dict[pywikibot.site.BaseSite, pywikibot.Page] = {}
    # Ignore interwiki links within nowiki tags, includeonly tags, pre tags,
    # and HTML comments
    include = []
    if template_subpage:
        include = ['includeonly']
    text = removeDisabledParts(text, include=include)

    # This regular expression will find every link that is possibly an
    # interwiki link.
    # NOTE: language codes are case-insensitive and only consist of basic latin
    # letters and hyphens.
    # TODO: currently, we do not have any, but BCP 47 allows digits, and
    #       underscores.
    # TODO: There is no semantic difference between hyphens and
    #       underscores -> fold them.
    interwikiR = re.compile(r'\[\[([a-zA-Z\-]+)\s?:([^\[\]\n]*)\]\]')
    for lang, pagetitle in interwikiR.findall(text):
        lang = lang.lower()
        # Check if it really is in fact an interwiki link to a known
        # language, or if it's e.g. a category tag or an internal link
        lang = fam.obsolete.get(lang, lang)
        if lang in fam.langs:
            if '|' in pagetitle:
                # ignore text after the pipe
                pagetitle = pagetitle[:pagetitle.index('|')]
            # we want the actual page objects rather than the titles
            site = pywikibot.Site(code=lang, fam=fam)
            # skip language links to its own site
            if site == insite:
                continue
            previous_key_count = len(result)
            page = pywikibot.Page(site, pagetitle)
            try:
                result[page.site] = page  # need to trigger page._link.parse()
            except InvalidTitleError:
                pywikibot.info(f'[getLanguageLinks] Text contains invalid '
                               f'interwiki link [[{lang}:{pagetitle}]].')
                continue
            if previous_key_count == len(result):
                pywikibot.warning(f'[getLanguageLinks] 2 or more interwiki '
                                  f'links point to site {site}.')
    return result


def removeLanguageLinks(text: str, site=None, marker: str = '') -> str:
    """Return text with all inter-language links removed.

    If a link to an unknown language is encountered, a warning
    is printed.

    :param text: The text that needs to be modified.
    :param site: The site that the text is coming from.
    :type site: pywikibot.Site
    :param marker: If defined, marker is placed after the last language
        link, or at the end of text if there are no language links.
    :return: The modified text.
    """
    if site is None:
        site = pywikibot.Site()
    # This regular expression will find every interwiki link, plus trailing
    # whitespace.
    languages = '|'.join(site.validLanguageLinks()
                         + list(site.family.obsolete.keys()))
    if not languages:
        return text
    interwikiR = re.compile(rf'\[\[({languages})\s?:[^\[\]\n]*\]\][\s]*',
                            re.IGNORECASE)
    text = replaceExcept(text, interwikiR, '',
                         ['comment', 'math', 'nowiki', 'pre',
                          'syntaxhighlight'],
                         marker=marker,
                         site=site)
    return text.strip()


def removeLanguageLinksAndSeparator(text: str, site=None, marker: str = '',
                                    separator: str = '') -> str:
    """Return text with inter-language links and preceding separators removed.

    If a link to an unknown language is encountered, a warning
    is printed.

    :param text: The text that needs to be modified.
    :param site: The site that the text is coming from.
    :type site: pywikibot.Site
    :param marker: If defined, marker is placed after the last language
        link, or at the end of text if there are no language links.
    :param separator: The separator string that will be removed
        if followed by the language links.
    :return: The modified text
    """
    if separator:
        mymarker = findmarker(text, '@L@')
        newtext = removeLanguageLinks(text, site, mymarker)
        mymarker = expandmarker(newtext, mymarker, separator)
        return newtext.replace(mymarker, marker)
    return removeLanguageLinks(text, site, marker)


@deprecated_args(addOnly='add_only')  # since 8.0
def replaceLanguageLinks(oldtext: str,
                         new: dict,
                         site: pywikibot.site.BaseSite | None = None,
                         add_only: bool = False,
                         template: bool = False,
                         template_subpage: bool = False) -> str:
    """Replace inter-language links in the text with a new set of links.

    :param oldtext: The text that needs to be modified.
    :param new: A dict with the Site objects as keys, and Page or Link
        objects as values (i.e., just like the dict returned by
        :func:`getLanguageLinks` function).
    :param site: The site that the text is from.
    :param add_only: If True, do not remove old language links, only add
        new ones.
    :param template: Indicates if text belongs to a template page or not.
    :param template_subpage: Indicates if text belongs to a template sub-page
        or not.
    :return: The modified text.
    """
    # Find a marker that is not already in the text.
    marker = findmarker(oldtext)
    if site is None:
        site = pywikibot.Site()
    separator = site.family.interwiki_text_separator
    cseparator = site.family.category_text_separator
    separatorstripped = separator.strip()
    cseparatorstripped = cseparator.strip()
    if add_only:
        s2 = oldtext
    else:
        s2 = removeLanguageLinksAndSeparator(oldtext, site=site, marker=marker,
                                             separator=separatorstripped)
    s = interwikiFormat(new, insite=site)
    if not s:
        newtext = s2.replace(marker, '')
    elif site.code in site.family.interwiki_attop \
            or '<!-- interwiki at top -->' in oldtext:
        # do not add separator if interwiki links are on one line
        newtext = s + ('' if site.code in site.family.interwiki_on_one_line
                       else separator) + s2.replace(marker, '').strip()
    else:
        # calculate what was after the language links on the page
        firstafter = s2.find(marker)
        if firstafter < 0:
            firstafter = len(s2)
        else:
            firstafter += len(marker)

        # Any text in 'after' part that means we should keep it after?
        if '</noinclude>' in s2[firstafter:]:
            if separatorstripped:
                s = separator + s
            newtext = (s2[:firstafter].replace(marker, '')
                       + s + s2[firstafter:])
        elif site.code in site.family.categories_last:
            cats = getCategoryLinks(s2, site=site)
            s2 = removeCategoryLinksAndSeparator(
                s2.replace(marker, cseparatorstripped).strip(), site) \
                + separator + s
            newtext = replaceCategoryLinks(s2, cats, site=site, add_only=True)
        # for Wikitravel's language links position.
        # (not supported by rewrite - no API)
        elif site.family.name == 'wikitravel':
            s = separator + s + separator
            newtext = (s2[:firstafter].replace(marker, '')
                       + s + s2[firstafter:])
        elif template or template_subpage:
            if template_subpage:
                includeOn = '<includeonly>'
                includeOff = '</includeonly>'
            else:
                includeOn = '<noinclude>'
                includeOff = '</noinclude>'
                separator = ''
            # Do we have a noinclude at the end of the template?
            parts = s2.split(includeOff)
            lastpart = parts[-1]
            if re.match(fr'\s*{marker}', lastpart):
                # Put the langlinks back into the noinclude's
                regexp = re.compile(fr'{includeOff}\s*{marker}')
                # replace via lambda due to T330021
                newtext = regexp.sub(lambda m: s + includeOff, s2)
            else:
                # Put the langlinks at the end, inside noinclude's
                newtext = (s2.replace(marker, '').strip()
                           + separator
                           + f'{includeOn}\n{s}{includeOff}\n')
        else:
            newtext = s2.replace(marker, '').strip() + separator + s

    # special parts above interwiki
    above_interwiki = []

    if site.sitename == 'wikipedia:nn':
        comment = re.compile(
            r'<!--interwiki \(no(\/nb)?, *sv, *da first; then other languages '
            r'alphabetically by name\)-->')
        above_interwiki.append(comment)

    if site.family.name == 'wikipedia' and site.code in ('ba', 'crh', 'krc'):
        comment = re.compile(r'<!-- [Ii]nterwikis -->')
        above_interwiki.append(comment)

    if above_interwiki:
        interwiki = get_regexes('interwiki', site)[0]
        first_interwiki = interwiki.search(newtext)
        for reg in above_interwiki:
            special = reg.search(newtext)
            if special and not isDisabled(newtext, special.start()):
                newtext = (newtext[:special.start()].strip()
                           + newtext[special.end():])
                newtext = (newtext[:first_interwiki.start()].strip()
                           + special.group() + '\n'
                           + newtext[first_interwiki.start():])

    return newtext.strip()


def interwikiFormat(links: dict, insite=None) -> str:
    """Convert interwiki link dict into a wikitext string.

    :param links: interwiki links to be formatted
    :type links: dict with the Site objects as keys, and Page
        or Link objects as values.
    :param insite: site the interwiki links will be formatted for
        (defaulting to the current site).
    :type insite: BaseSite
    :return: string including wiki links formatted for inclusion
        in insite
    """
    if not links:
        return ''

    if insite is None:
        insite = pywikibot.Site()

    ar = interwikiSort(list(links.keys()), insite)
    s = []
    for site in ar:
        if isinstance(links[site], pywikibot.Link):
            links[site] = pywikibot.Page(links[site])
        if not isinstance(links[site], pywikibot.Page):
            raise ValueError('links dict must contain Page or Link objects')

        title = links[site].title(as_link=True, force_interwiki=True,
                                  insite=insite)
        link = title.replace('[[:', '[[')
        s.append(link)

    sep = ' ' if insite.code in insite.family.interwiki_on_one_line else '\n'
    return sep.join(s) + '\n'


def interwikiSort(sites, insite=None):
    """Sort sites according to local interwiki sort logic."""
    if not sites:
        return []

    if insite is None:
        insite = pywikibot.Site()

    sites.sort()
    putfirst = insite.interwiki_putfirst()
    if putfirst:
        # In this case I might have to change the order
        firstsites = []
        validlanglinks = insite.validLanguageLinks()
        for code in putfirst:
            if code in validlanglinks:
                site = insite.getSite(code=code)
                if site in sites:
                    del sites[sites.index(site)]
                    firstsites.append(site)
        sites = firstsites + sites
    return sites


# -------------------------------------
# Functions dealing with category links
# -------------------------------------

def getCategoryLinks(text: str, site=None,
                     include: list[str] | None = None,
                     expand_text: bool = False) -> list[pywikibot.Category]:
    """Return a list of category links found in text.

    :param include: list of tags which should not be removed by
        removeDisabledParts() and where CategoryLinks can be searched.
    :return: all category links found
    """
    result = []
    if site is None:
        site = pywikibot.Site()
    # Ignore category links within nowiki tags, pre tags, includeonly tags,
    # and HTML comments
    text = removeDisabledParts(text, include=include or [])
    catNamespace = '|'.join(site.namespaces.CATEGORY)
    R = re.compile(
        rf'\[\[\s*(?P<namespace>{catNamespace})\s*:\s*(?P<rest>.+?)\]\]', re.I
    )
    for match in R.finditer(text):
        match_rest = match['rest']
        if expand_text and '{{' in match_rest:
            rest = site.expand_text(match_rest)
        else:
            rest = match_rest
        if '|' in rest:
            title, sortKey = rest.split('|', 1)
        else:
            title, sortKey = rest, None
        try:
            cat = pywikibot.Category(site,
                                     f"{match['namespace']}:{title}",
                                     sort_key=sortKey)
        except InvalidTitleError:
            # Category title extracted contains invalid characters
            # Likely due to on-the-fly category name creation, see T154309
            pywikibot.warning(f'Invalid category title extracted: {title}')
        else:
            result.append(cat)

    return result


def removeCategoryLinks(text: str, site=None, marker: str = '') -> str:
    """Return text with all category links removed.

    :param text: The text that needs to be modified.
    :param site: The site that the text is coming from.
    :type site: pywikibot.Site
    :param marker: If defined, marker is placed after the last category
        link, or at the end of text if there are no category links.
    :return: The modified text.
    """
    # This regular expression will find every link that is possibly an
    # interwiki link, plus trailing whitespace. The language code is grouped.
    # NOTE: This assumes that language codes only consist of non-capital
    # ASCII letters and hyphens.
    if site is None:
        site = pywikibot.Site()
    catNamespace = '|'.join(site.namespaces.CATEGORY)
    categoryR = re.compile(rf'\[\[\s*({catNamespace})\s*:.*?\]\]\s*', re.I)
    text = replaceExcept(text, categoryR, '',
                         ['comment', 'includeonly', 'math', 'nowiki', 'pre',
                          'syntaxhighlight'],
                         marker=marker,
                         site=site)
    if marker:
        # avoid having multiple linefeeds at the end of the text
        text = re.sub(fr'\s*{re.escape(marker)}', '\n' + marker,
                      text.strip())
    return text.strip()


def removeCategoryLinksAndSeparator(text: str, site=None, marker: str = '',
                                    separator: str = '') -> str:
    """Return text with category links and preceding separators removed.

    :param text: The text that needs to be modified.
    :param site: The site that the text is coming from.
    :type site: pywikibot.Site
    :param marker: If defined, marker is placed after the last category
        link, or at the end of text if there are no category links.
    :param separator: The separator string that will be removed
        if followed by the category links.
    :return: The modified text
    """
    if site is None:
        site = pywikibot.Site()
    if separator:
        mymarker = findmarker(text, '@C@')
        newtext = removeCategoryLinks(text, site, mymarker)
        mymarker = expandmarker(newtext, mymarker, separator)
        return newtext.replace(mymarker, marker)
    return removeCategoryLinks(text, site, marker)


def replaceCategoryInPlace(oldtext, oldcat, newcat, site=None,
                           add_only: bool = False) -> str:
    """Replace old category with new one and return the modified text.

    :param oldtext: Content of the old category
    :param oldcat: pywikibot.Category object of the old category
    :param newcat: pywikibot.Category object of the new category
    :param add_only: If add_only is True, the old category won't
        be replaced and the category given will be added after it.
    :return: the modified text
    """
    if site is None:
        site = pywikibot.Site()

    catNamespace = '|'.join(site.namespaces.CATEGORY)
    title = oldcat.title(with_ns=False)
    if not title:
        return oldtext

    # title might contain regex special characters
    title = case_escape(site.namespaces[14].case, title, underscore=True)
    categoryR = re.compile(
        rf'\[\[\s*({catNamespace})\s*:\s*{title}[\s\u200e\u200f]*'
        r'((?:\|[^]]+)?\]\])', re.IGNORECASE)
    categoryRN = re.compile(
        rf'^[^\S\n]*\[\[\s*({catNamespace})\s*:\s*{title}[\s\u200e\u200f]*'
        r'((?:\|[^]]+)?\]\])[^\S\n]*\n', re.IGNORECASE | re.MULTILINE)
    exceptions = ['comment', 'math', 'nowiki', 'pre', 'syntaxhighlight']
    if newcat is None:
        # First go through and try the more restrictive regex that removes
        # an entire line, if the category is the only thing on that line (this
        # prevents blank lines left over in category lists following a removal)
        text = replaceExcept(oldtext, categoryRN, '',
                             exceptions, site=site)
        text = replaceExcept(text, categoryR, '',
                             exceptions, site=site)
    elif add_only:
        text = replaceExcept(
            oldtext, categoryR,
            f'{oldcat.title(as_link=True, allow_interwiki=False)}\n'
            f'{newcat.title(as_link=True, allow_interwiki=False)}',
            exceptions, site=site
        )
    else:
        text = replaceExcept(
            oldtext, categoryR,
            f'[[{site.namespace(14)}:{newcat.title(with_ns=False)}\\2',
            exceptions, site=site
        )
    return text


@deprecated_args(addOnly='add_only')  # since 8.0
def replaceCategoryLinks(oldtext: str,
                         new: Iterable,
                         site: pywikibot.site.BaseSite | None = None,
                         add_only: bool = False) -> str:
    """Replace all existing category links with new category links.

    :param oldtext: The text that needs to be replaced.
    :param new: Should be a list of Category objects or strings
        which can be either the raw name or ``[[Category:..]]``.
    :param site: The site that the text is from.
    :param add_only: If add_only is True, the old category won't be
        deleted and the category(s) given will be added (and they won't
        replace anything).
    :return: The modified text.
    """
    # Find a marker that is not already in the text.
    marker = findmarker(oldtext)
    if site is None:
        site = pywikibot.Site()
    if re.search(r'\{\{ *(' + r'|'.join(site.getmagicwords('defaultsort'))
                 + r')', oldtext, flags=re.IGNORECASE):
        separator = '\n'
    else:
        separator = site.family.category_text_separator
    iseparator = site.family.interwiki_text_separator
    separatorstripped = separator.strip()
    iseparatorstripped = iseparator.strip()
    if add_only:
        cats_removed_text = oldtext
    else:
        cats_removed_text = removeCategoryLinksAndSeparator(
            oldtext, site=site, marker=marker, separator=separatorstripped)
    new_cats = categoryFormat(new, insite=site)
    if not new_cats:
        newtext = cats_removed_text.replace(marker, '')
    elif site.code in site.family.category_attop:
        newtext = new_cats + separator + cats_removed_text
    else:
        # calculate what was after the categories links on the page
        firstafter = cats_removed_text.find(marker)
        if firstafter < 0:
            firstafter = len(cats_removed_text)
        else:
            firstafter += len(marker)
        # Is there text in the 'after' part that means we should keep it
        # after?
        if '</noinclude>' in cats_removed_text[firstafter:]:
            if separatorstripped:
                new_cats = separator + new_cats
            newtext = (cats_removed_text[:firstafter].replace(marker, '')
                       + new_cats + cats_removed_text[firstafter:])
        elif site.code in site.family.categories_last:
            newtext = (cats_removed_text.replace(marker, '').strip()
                       + separator + new_cats)
        else:
            interwiki = getLanguageLinks(cats_removed_text, insite=site)
            langs_removed_text = removeLanguageLinksAndSeparator(
                cats_removed_text.replace(marker, ''), site, '',
                iseparatorstripped) + separator + new_cats
            newtext = replaceLanguageLinks(
                langs_removed_text, interwiki, site, add_only=True)

    # special parts under categories
    under_categories = []

    if site.sitename == 'wikipedia:de':
        personendaten = re.compile(r'\{\{ *Personendaten.*?\}\}',
                                   re.IGNORECASE | re.DOTALL)
        under_categories.append(personendaten)

    if site.sitename == 'wikipedia:yi':
        stub = re.compile(r'\{\{.*?שטומף *\}\}', re.IGNORECASE)
        under_categories.append(stub)

    if site.family.name == 'wikipedia' and site.code in ('simple', 'en'):
        stub = re.compile(r'\{\{.*?stub *\}\}', re.IGNORECASE)
        under_categories.append(stub)

    if under_categories:
        category = get_regexes('category', site)[0]
        last_category = list(category.finditer(newtext))[-1]
        for reg in under_categories:
            special = reg.search(newtext)
            if special and not isDisabled(newtext, special.start()):
                newtext = (newtext[:special.start()].strip()
                           + newtext[special.end():])
                newtext = (newtext[:last_category.end()].strip() + '\n' * 2
                           + special.group() + newtext[last_category.end():])

    return newtext.strip()


def categoryFormat(categories, insite=None) -> str:
    """Return a string containing links to all categories in a list.

    :param categories: A list of Category or Page objects or strings which can
        be either the raw name, [[Category:..]] or [[cat_localised_ns:...]].
    :type categories: iterable
    :param insite: Used to to localise the category namespace.
    :type insite: pywikibot.Site
    :return: String of categories
    """
    if not categories:
        return ''

    if insite is None:
        insite = pywikibot.Site()

    catLinks = []
    for category in categories:
        if isinstance(category, str):
            category, separator, sortKey = category.strip('[]').partition('|')
            sortKey = sortKey if separator else None
            # whole word if no ":" is present
            prefix = category.split(':', 1)[0]
            if prefix not in insite.namespaces[14]:
                category = f'{insite.namespace(14)}:{category}'
            category = pywikibot.Category(pywikibot.Link(category,
                                                         insite,
                                                         default_namespace=14),
                                          sort_key=sortKey)
        # Make sure a category is casted from Page to Category.
        elif not isinstance(category, pywikibot.Category):
            category = pywikibot.Category(category)
        link = category.aslink()
        catLinks.append(link)

    sep = ' ' if insite.category_on_one_line() else '\n'
    # Some people don't like the categories sorted
    # catLinks.sort()
    return sep.join(catLinks) + '\n'


# -------------------------------------
# Functions dealing with external links
# -------------------------------------

def compileLinkR(withoutBracketed: bool = False, onlyBracketed: bool = False):
    """Return a regex that matches external links."""
    # RFC 2396 says that URLs may only contain certain characters.
    # For this regex we also accept non-allowed characters, so that the bot
    # will later show these links as broken ('Non-ASCII Characters in URL').
    # Note: While allowing dots inside URLs, MediaWiki will regard
    # dots at the end of the URL as not part of that URL.
    # The same applies to comma, colon and some other characters.
    notAtEnd = r'\]\s\.:;,<>"\|\)}'
    # So characters inside the URL can be anything except whitespace,
    # closing squared brackets, quotation marks, greater than and less
    # than, and the last character also can't be parenthesis or another
    # character disallowed by MediaWiki.
    notInside = r'\]\s<>"'
    # The first half of this regular expression is required because '' is
    # not allowed inside links. For example, in this wiki text:
    #       ''Please see https://www.example.org.''
    # .'' shouldn't be considered as part of the link.
    regex = rf'(?P<url>http[s]?://[^{notInside}]*?[^{notAtEnd}]' \
            rf'(?=[{notAtEnd}]*\'\')|http[s]?://[^{notInside}]*' \
            rf'[^{notAtEnd}])'

    if withoutBracketed:
        regex = r'(?<!\[)' + regex
    elif onlyBracketed:
        regex = r'\[' + regex
    return re.compile(regex)


# --------------------------------
# Functions dealing with templates
# --------------------------------

def extract_templates_and_params(
    text: str,
    remove_disabled_parts: bool = False,
    strip: bool = False,
) -> list[tuple[str, OrderedDictType[str, str]]]:
    """Return a list of templates found in text.

    Return value is a list of tuples. There is one tuple for each use of a
    template in the page, with the template title as the first entry and a
    dict of parameters as the second entry. Parameters are indexed by
    strings; as in MediaWiki, an unnamed parameter is given a parameter name
    with an integer value corresponding to its position among the unnamed
    parameters, and if this results multiple parameters with the same name
    only the last value provided will be returned.

    This uses the package :py:obj:`mwparserfromhell` or
    :py:obj:`wikitextparser` as MediaWiki markup parser.
    ``mwparserfromhell`` is installed by default.

    There are minor differences between the two implementations.

    The parser packages preserves whitespace in parameter names and
    values.

    If there are multiple numbered parameters in the wikitext for the
    same position, MediaWiki will only use the last parameter value.
    e.g. `{{a| foo | 2 <!-- --> = bar | baz }}` is `{{a|1=foo|2=baz}}`
    To replicate that behaviour, enable both `remove_disabled_parts`
    and `strip` parameters.

    :param text: The wikitext from which templates are extracted
    :param remove_disabled_parts: If enabled, remove disabled wikitext
        such as comments and pre.
    :param strip: If enabled, strip arguments and values of templates.
    :return: list of template name and params

    .. versionchanged:: 6.1
       *wikitextparser* package is supported; either *wikitextparser* or
       *mwparserfromhell* is strictly recommended.
    """
    def explicit(param):
        try:
            attr = param.showkey
        except AttributeError:
            attr = not param.positional
        return attr

    if remove_disabled_parts:
        text = removeDisabledParts(text)

    parser_name = wikitextparser.__name__
    pywikibot.debug(f'Using {parser_name!r} wikitext parser')

    result = []
    parsed = wikitextparser.parse(text)
    if parser_name == 'wikitextparser':
        templates = parsed.templates
        arguments = 'arguments'
    else:
        templates = parsed.ifilter_templates(
            matches=lambda x: not x.name.lstrip().startswith('#'),
            recursive=True)
        arguments = 'params'

    for template in templates:
        params = OrderedDict()
        for param in getattr(template, arguments):
            value = str(param.value)  # mwpfh needs upcast to str

            if strip:
                key = param.name.strip()
                if explicit(param):
                    value = param.value.strip()
                else:
                    value = str(param.value)
            else:
                key = str(param.name)

            params[key] = value

        result.append((template.name.strip(), params))
    return result


def extract_templates_and_params_regex_simple(text: str):
    """Extract top-level templates with params using only a simple regex.

    This function uses only a single regex, and returns
    an entry for each template called at the top-level of the wikitext.
    Nested templates are included in the argument values of the top-level
    template.

    This method will incorrectly split arguments when an
    argument value contains a '|', such as {{template|a={{b|c}} }}.

    :param text: The wikitext from which templates are extracted
    :return: list of template name and params
    :rtype: list of tuple of name and OrderedDict
    """
    result = []

    for match in NESTED_TEMPLATE_REGEX.finditer(text):
        name, params = match[1], match[2]

        # Special case for {{a}}
        params = [] if params is None else params.split('|')

        numbered_param_identifiers = itertools.count(1)

        params = OrderedDict(
            arg.split('=', 1)
            if '=' in arg
            else (str(next(numbered_param_identifiers)), arg)
            for arg in params)

        result.append((name, params))

    return result


def glue_template_and_params(template_and_params) -> str:
    """Return wiki text of template glued from params.

    You can use items from extract_templates_and_params here to get
    an equivalent template wiki text (it may happen that the order
    of the params changes).
    """
    template, params = template_and_params
    text = ''
    for items in params.items():
        text += '|{}={}\n'.format(*items)

    return f'{{{{{template}\n{text}}}}}'


# --------------------------
# Page parsing functionality
# --------------------------

def does_text_contain_section(pagetext: str, section: str) -> bool:
    """Determine whether the page text contains the given section title.

    It does not care whether a section string may contain spaces or
    underlines. Both will match.

    If a section parameter contains an internal link, it will match the
    section with or without a preceding colon which is required for a
    text link e.g. for categories and files.

    :param pagetext: The wikitext of a page
    :param section: a section of a page including wikitext markups
    """
    # match preceding colon for text links
    section = re.sub(r'\\\[\\\[(\\?:)?', r'\[\[\:?', re.escape(section))
    # match underscores and white spaces
    section = re.sub(r'\\?[ _]', '[ _]', section)
    m = re.search(f"=+[ ']*{section}[ ']*=+", pagetext)
    return bool(m)


def reformat_ISBNs(text: str, match_func) -> str:
    """Reformat ISBNs.

    :param text: text containing ISBNs
    :param match_func: function to reformat matched ISBNs
    :type match_func: callable
    :return: reformatted text
    """
    isbnR = re.compile(r'(?<=ISBN )(?P<code>[\d\-]+[\dXx])')
    return isbnR.sub(match_func, text)


# ---------------------------------------
# Time parsing functionality (Archivebot)
# ---------------------------------------

TIMEGROUPS = ('time', 'tzinfo', 'year', 'month', 'day', 'hour', 'minute')


class TimeStripperPatterns(NamedTuple):

    """Hold precompiled timestamp patterns for :class:`TimeStripper`.

    Attribute order is important to avoid mismatch when searching.

    .. versionadded:: 8.0
    """

    time: Pattern[str]
    tzinfo: Pattern[str]
    year: Pattern[str]
    month: Pattern[str]
    day: Pattern[str]


class TimeStripper:

    """Find timestamp in page and return it as pywikibot.Timestamp object.

    .. versionchanged:: 8.0
       *group* attribute is a set instead of a list.
       *patterns* is a :class:`TimeStripperPatterns` namedtuple instead
       of a list.

    **Example**:

    >>> site = pywikibot.Site('wikipedia:fr')
    >>> sign = 'Merci bien Xqt (d) 15 mai 2013 à 20:34 (CEST)'
    >>> ts = TimeStripper(site)
    >>> ts.timestripper(sign)  # doctest: +SKIP
    Timestamp(2013, 5, 15, 20, 34, tzinfo=TZoneFixedOffset(3600, Europe/Paris))
    """

    def __init__(self, site=None) -> None:
        """Initializer."""
        self.site = pywikibot.Site() if site is None else site

        self.origNames2monthNum = {}
        # use first_lower/first_upper for those language where month names
        # were changed: T324310, T356175
        if self.site.lang in ('hy', 'vi'):
            functions = [first_upper, first_lower]
        else:
            functions = [str]

        for n, (long, short) in enumerate(self.site.months_names, start=1):
            for func in functions:
                self.origNames2monthNum[func(long)] = n
                self.origNames2monthNum[func(short)] = n
                # in some cases month in ~~~~ might end without dot even if
                # site.months_names do not.
                if short.endswith('.'):
                    self.origNames2monthNum[func(short[:-1])] = n

        timeR = (r'(?P<time>(?P<hour>([0-1]\d|2[0-3]))[:\.h]'
                 r'(?P<minute>[0-5]\d))')
        timeznR = r'\((?P<tzinfo>[A-Z]+)\)'
        yearR = r'(?P<year>(19|20)\d\d)(?:{})?'.format('\ub144')
        # if months have 'digits' as names, they need to be
        # removed; will be handled as digits in regex, adding d+{1,2}\.?
        escaped_months = [month for month in self.origNames2monthNum if
                          not month.strip('.').isdigit()]
        # match longest names first.
        escaped_months = [re.escape(month) for
                          month in sorted(escaped_months, reverse=True)]
        # work around for cs wiki: if month are in digits, we assume
        # that format is dd. mm. (with dot and spaces optional)
        # the last one is workaround for Korean
        if any(month.isdigit() for month in self.origNames2monthNum):
            self.is_digit_month = True
            monthR = r'(?P<month>({})|(?:1[012]|0?[1-9])\.)' \
                     .format('|'.join(escaped_months))
            dayR = r'(?P<day>(3[01]|[12]\d|0?[1-9]))(?:{})' \
                   r'?\.?\s*(?:[01]?\d\.)?'.format('\uc77c')
        else:
            self.is_digit_month = False
            monthR = r'(?P<month>({}))'.format('|'.join(escaped_months))
            dayR = r'(?P<day>(3[01]|[12]\d|0?[1-9]))\.?'

        self.patterns = TimeStripperPatterns(
            re.compile(timeR),
            re.compile(timeznR),
            re.compile(yearR),
            re.compile(monthR),
            re.compile(dayR),
        )

        self._hyperlink_pat = re.compile(r'\[\s*?http[s]?://[^\]]*?\]')
        self._comment_pat = re.compile(r'<!--(.*?)-->')
        self._wikilink_pat = re.compile(
            r'\[\[(?P<link>[^\]\|]*?)(?P<anchor>\|[^\]]*)?\]\]')

        self.tzinfo = TZoneFixedOffset(self.site.siteinfo['timeoffset'],
                                       self.site.siteinfo['timezone'])

    @property
    @deprecated('patterns.time', since='8.0.0')
    def ptimeR(self):
        """Deprecated time pattern attribute.

        .. deprecated:: 8.0
           use pattern.time instead
        """
        return self.patterns.time

    @property
    @deprecated('patterns.tzinfo', since='8.0.0')
    def ptimeznR(self):
        """Deprecated tzinfo pattern attribute.

        .. deprecated:: 8.0
           use patterns.tzinfo instead
        """
        return self.patterns.tzinfo

    @property
    @deprecated('patterns.year', since='8.0.0')
    def pyearR(self):
        """Deprecated year pattern attribute.

        .. deprecated:: 8.0
           use patterns.year instead
        """
        return self.patterns.year

    @property
    @deprecated('patterns.month', since='8.0.0')
    def pmonthR(self):
        """Deprecated month pattern attribute.

        .. deprecated:: 8.0
           use patterns.month instead
        """
        return self.patterns.month

    @property
    @deprecated('patterns.day', since='8.0.0')
    def pdayR(self):
        """Deprecated day pattern attribute.

        .. deprecated:: 8.0
           use patterns.day instead
        """
        return self.patterns.day

    @property
    @deprecated('textlib.TIMEGROUPS', since='8.0.0')
    def groups(self):
        """Deprecated groups attribute.

        .. deprecated:: 8.0
           use textlib.TIMEGROUPS instead
        """
        return TIMEGROUPS

    def _last_match_and_replace(self,
                                txt: str,
                                pat) -> tuple[str, Match[str] | None]:
        """Take the rightmost match and replace with marker.

        It does so to prevent spurious earlier matches.
        """
        all_matches = list(pat.finditer(txt))
        cnt = len(all_matches)

        if not cnt:
            return (txt, None)

        m = all_matches[-1]

        def marker(m: Match[str]):
            """Replace exactly the same number of matched characters.

            Same number of chars shall be replaced, in order to be able
            to compare pos for matches reliably (absolute pos of a match
            is not altered by replacement).
            """
            return '@' * (m.end() - m.start())

        # month and day format might be identical (e.g. see bug T71315),
        # avoid to wipe out day, after month is matched. Replace all matches
        # but the last two (i.e. allow to search for dd. mm.)
        if pat != self.patterns.month:
            txt = pat.sub(marker, txt)
        elif self.is_digit_month:
            if cnt > 2:
                txt = pat.sub(marker, txt, cnt - 2)
        else:
            txt = pat.sub(marker, txt)

        return (txt, m)

    @staticmethod
    def _valid_date_dict_positions(dateDict) -> bool:
        """Check consistency of reasonable positions for groups."""
        time_pos = dateDict['time']['start']
        tzinfo_pos = dateDict['tzinfo']['start']
        date_pos = sorted(
            (dateDict['day'], dateDict['month'], dateDict['year']),
            key=lambda x: x['start'])
        min_pos, max_pos = date_pos[0]['start'], date_pos[-1]['start']
        max_gap = max(x[1]['start'] - x[0]['end']
                      for x in zip(date_pos, date_pos[1:]))

        if max_gap > TIMESTAMP_GAP_LIMIT:
            return False
        if tzinfo_pos < min_pos or tzinfo_pos < time_pos:
            return False
        if min_pos < tzinfo_pos < max_pos:
            return False
        return not min_pos < time_pos < max_pos

    def timestripper(self, line: str) -> pywikibot.Timestamp | None:
        """Find timestamp in line and convert it to time zone aware datetime.

        All the following items must be matched, otherwise None is
        returned: -. year, month, hour, time, day, minute, tzinfo

        .. versionchanged:: 7.6
           HTML parts are removed from line

        :return: A timestamp found on the given line
        """
        # Try to maintain gaps that are used in _valid_date_dict_positions()
        def censor_match(match):
            return '_' * (match.end() - match.start())

        # match date fields
        dateDict = {}

        # Analyze comments separately from rest of each line to avoid to skip
        # dates in comments, as the date matched by timestripper is the
        # rightmost one.
        most_recent = []
        for comment in self._comment_pat.finditer(line):
            # Recursion levels can be maximum two. If a comment is found, it
            # will not for sure be found in the next level.
            # Nested comments are excluded by design.
            timestamp = self.timestripper(comment[1])
            most_recent.append(timestamp)

        # Censor comments.
        line = self._comment_pat.sub(censor_match, line)

        # Censor external links.
        line = self._hyperlink_pat.sub(censor_match, line)

        for wikilink in self._wikilink_pat.finditer(line):
            # Recursion levels can be maximum two. If a link is found, it will
            # not for sure be found in the next level.
            # Nested links are excluded by design.
            link, anchor = wikilink['link'], wikilink['anchor']
            timestamp = self.timestripper(link)
            most_recent.append(timestamp)
            if anchor:
                timestamp = self.timestripper(anchor)
                most_recent.append(timestamp)

        # Censor wikilinks.
        line = self._wikilink_pat.sub(censor_match, line)

        # Remove parts that are not supposed to contain the timestamp, in order
        # to reduce false positives.
        line = removeDisabledParts(line)
        line = removeHTMLParts(line)

        line = to_latin_digits(line)
        for pat in self.patterns:
            line, match_obj = self._last_match_and_replace(line, pat)
            if match_obj:
                for group, value in match_obj.groupdict().items():
                    start, end = (match_obj.start(group), match_obj.end(group))
                    # The positions are stored for later validation
                    dateDict[group] = {
                        'value': value, 'start': start, 'end': end
                    }

        # all fields matched -> date valid
        # groups are in a reasonable order.
        if (all(g in dateDict for g in TIMEGROUPS)
                and self._valid_date_dict_positions(dateDict)):
            # remove 'time' key, now split in hour/minute and not needed
            # by datetime.
            del dateDict['time']

            # replace month name in original language with month number
            try:
                value = self.origNames2monthNum[dateDict['month']['value']]
            except KeyError:
                raise KeyError(
                    f"incorrect month name {dateDict['month']['value']!r} "
                    f'in page in site {self.site}'
                )

            dateDict['month']['value'] = value

            # convert to integers and remove the inner dict
            for k, v in dateDict.items():
                if k == 'tzinfo':
                    continue
                try:
                    dateDict[k] = int(v['value'])
                except ValueError:
                    raise ValueError(f"Value: {v['value']} could not be "
                                     f'converted for key: {k}.')

            # find timezone
            dateDict['tzinfo'] = self.tzinfo

            timestamp = pywikibot.Timestamp(**dateDict)
        else:
            timestamp = None

        most_recent.append(timestamp)

        try:
            timestamp = max(ts for ts in most_recent if ts is not None)
        except ValueError:
            timestamp = None

        return timestamp
