#!/usr/bin/env python3
#
# (C) Pywikibot team, 2004-2026
#
# Distributed under the terms of the MIT license.
#
"""This bot will make direct text replacements.

It will retrieve information on which pages might need changes either from
an XML dump or a text file, or only change a single page.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-mysqlquery       Retrieve information from a local database mirror.
                  If no query specified, bot searches for pages with
                  given replacements.

-xml              Retrieve information from a local XML dump
                  (pages-articles or pages-meta-current, see
                  https://dumps.wikimedia.org). Argument can also
                  be given as "-xml:filename".

-regex            Make replacements using regular expressions. If this argument
                  isn't given, the bot will make simple text replacements.

-nocase           Use case insensitive regular expressions.

-dotall           Make the dot match any character at all, including a newline.
                  Without this flag, '.' will match anything except a newline.

-multiline        '^' and '$' will now match begin and end of each line.

-xmlstart         (Only works with -xml) Skip all articles in the XML dump
                  before the one specified (may also be given as
                  -xmlstart:Article).

-addcat:cat_name  Adds "cat_name" category to every altered page.

-excepttitle:XYZ  Skip pages with titles that contain XYZ. If the -regex
                  argument is given, XYZ will be regarded as a regular
                  expression.

-requiretitle:XYZ Only do pages with titles that contain XYZ. If the -regex
                  argument is given, XYZ will be regarded as a regular
                  expression.

-excepttext:XYZ   Skip pages which contain the text XYZ. If the -regex
                  argument is given, XYZ will be regarded as a regular
                  expression.

-exceptinside:XYZ Skip occurrences of the to-be-replaced text which lie
                  within XYZ. If the -regex argument is given, XYZ will be
                  regarded as a regular expression.

-exceptinsidetag:XYZ Skip occurrences of the to-be-replaced text which lie
                  within an XYZ tag.

-summary:XYZ      Set the summary message text for the edit to XYZ, bypassing
                  the predefined message texts with original and replacements
                  inserted. To add the replacements to your summary use the
                  %(description)s placeholder, for example:
                  -summary:"Bot operated replacement: %(description)s"
                  Can't be used with -automaticsummary.

-automaticsummary Uses an automatic summary for all replacements which don't
                  have a summary defined. Can't be used with -summary.

-sleep:123        If you use -fix you can check multiple regex at the same time
                  in every page. This can lead to a great waste of CPU because
                  the bot will check every regex without waiting using all the
                  resources. This will slow it down between a regex and another
                  in order not to waste too much CPU.

-fix:XYZ          Perform one of the predefined replacements tasks, which are
                  given in the dictionary 'fixes' defined inside the files
                  fixes.py and user-fixes.py.

&fixes-help;

-manualinput      Request manual replacements via the command line input even
                  if replacements are already defined. If this option is set
                  (or no replacements are defined via -fix or the arguments)
                  it'll ask for additional replacements at start.

-pairsfile        Lines from the given file name(s) will be read as replacement
                  arguments. i.e. a file containing lines "a" and "b", used as:

                      python pwb.py replace -page:X -pairsfile:file c d

                  will replace 'a' with 'b' and 'c' with 'd'.

-always           Don't prompt you for each replacement

-quiet            Don't prompt a message if a page keeps unchanged

-nopreload        Do not preload pages. Useful if disabled on a wiki.

-recursive        Recurse replacement as long as possible. Be careful, this
                  might lead to an infinite loop.

-allowoverlap     When occurrences of the pattern overlap, replace all of them.
                  Be careful, this might lead to an infinite loop.

-fullsummary      Use one large summary for all command line replacements.


*Replacement parameters*
    Replacement parameters are pairs of arguments given to the script.
    The First argument is the old text to be replaced, the second
    argument is the new text. If the ``-regex`` argument is given, the
    first argument will be regarded as a regular expression, and the
    second argument might contain expressions like ``\1`` or ``\\g<name>``.
    The second parameter can also be specified as empty string, usually
    ``""``. It is possible to introduce more than one pair of
    replacement parameters.

.. admonition:: **Empty string arguments with PowerShell**
   :class: attention

   Using PowerShell as command shell removes empty strings during
   PowerShell's command line parsing. To enable empty strings with
   PowerShell you have either to escape quotation marks with gravis
   symbols in front of them like ```"`"`` or to disable command line
   parsing with ``--%`` symbol for all following command parts like
   :samp:`python pwb replace --% -start:! foo ""` which disables parsing
   for all replace options and arguments following this delimiter and
   enables empty strings.

Examples
--------

If you want to change templates from the old syntax, e.g.
``{{msg:Stub}}``, to the new syntax, e.g. ``{{Stub}}``, download an XML
dump file (pages-articles) from https://dumps.wikimedia.org, then use
this command:

    python pwb.py replace -xml -regex "{{msg:(.*?)}}" "{{\1}}"

If you have a dump called ``foobar.xml`` and want to fix typos in
articles, e.g. Errror -> Error, use this:

    python pwb.py replace -xml:foobar.xml "Errror" "Error" -namespace:0

If you want to do more than one replacement at a time, use this:

    python pwb.py replace -xml:foobar.xml "Errror" "Error" "Faail" "Fail" \\
    -namespace:0

If you have a page called 'John Doe' and want to fix the format of ISBNs,
use:

    python pwb.py replace -page:John_Doe -fix:isbn

This command will change 'referer' to 'referrer', but not in pages which
talk about HTTP, where the typo has become part of the standard:

    python pwb.py replace referer referrer -file:typos.txt -excepttext:HTTP


.. seealso:: :mod:`scripts.template` to modify or remove templates.
.. Please type "python pwb.py replace -help | more" if you can't read
   the top of the help.
"""
from __future__ import annotations

import re
from collections.abc import Generator, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pywikibot
from pywikibot import editor, fixes, i18n, pagegenerators, textlib
from pywikibot.backports import batched
from pywikibot.bot import ExistingPageBot, SingleSiteBot
from pywikibot.exceptions import InvalidPageError, NoPageError
from pywikibot.tools import chars


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
    '&fixes-help;': fixes.parameter_help,
}


def precompile_exceptions(exceptions, use_regex, flags) -> None:
    """Compile the exceptions with the given flags."""
    if not exceptions:
        return
    for exceptionCategory in [
            'title', 'require-title', 'text-contains', 'inside']:
        if exceptionCategory in exceptions:
            patterns = exceptions[exceptionCategory]
            if isinstance(patterns, str):
                patterns = [patterns]
            if not use_regex:
                patterns = [re.escape(pattern) for pattern in patterns]
            patterns = [re.compile(pattern, flags) for pattern in patterns]
            exceptions[exceptionCategory] = patterns


def _get_text_exceptions(exceptions):
    """Get exceptions on text (inside exceptions)."""
    return exceptions.get('inside-tags', []) + exceptions.get('inside', [])


class ReplacementBase:

    """The replacement instructions."""

    def __init__(
        self,
        old,
        new,
        edit_summary=None,
        default_summary=True
    ) -> None:
        """Create a basic replacement instance."""
        self.old = old
        self.old_regex = None
        self.new = new
        self._edit_summary = edit_summary
        self.default_summary = default_summary

    @property
    def edit_summary(self) -> str:
        """Return the edit summary for this fix."""
        return self._edit_summary

    @property
    def description(self) -> str:
        """Description of the changes that this replacement applies.

        This description is used as the default summary of the
        replacement. If you do not specify an edit summary on the
        command line or in some other way, whenever you apply this
        replacement to a page and submit the changes to the MediaWiki
        server, the edit summary includes the descriptions of each
        replacement that you applied to the page.
        """
        return f'-{self.old} +{self.new}'

    @property
    def container(self) -> None:
        """Container object which contains this replacement.

        A container object is an object that groups one or more
        replacements together and provides some properties that are
        common to all of them. For example, containers may define a
        common name for a group of replacements, or a common edit
        summary.

        Container objects must have a "name" attribute.
        """
        return None

    def _compile(self, use_regex, flags) -> None:
        """Compile the search text without modifying the flags."""
        # This does not update use_regex and flags depending on this instance
        if not use_regex:
            self.old_regex = re.escape(self.old)
        else:
            self.old_regex = self.old
        self.old_regex = re.compile(self.old_regex, flags)

    def compile(self, use_regex, flags) -> None:
        """Compile the search text."""
        # Set the regular expression flags
        if self.case_insensitive is False:
            flags &= ~re.IGNORECASE
        elif self.case_insensitive:
            flags |= re.IGNORECASE

        if self.use_regex is not None:
            use_regex = self.use_regex  # this replacement overrides it
        self._compile(use_regex, flags)


class Replacement(ReplacementBase):

    """A single replacement with its own data."""

    def __init__(self, old, new, use_regex=None, exceptions=None,
                 case_insensitive=None, edit_summary=None,
                 default_summary=True) -> None:
        """Create a single replacement entry unrelated to a fix."""
        super().__init__(old, new, edit_summary, default_summary)
        self._use_regex = use_regex
        self.exceptions = exceptions
        self._case_insensitive = case_insensitive

    @classmethod
    def from_compiled(cls, old_regex, new, **kwargs):
        """Create instance from already compiled regex."""
        if kwargs.get('use_regex', True) is not True:
            raise ValueError('The use_regex parameter can only be True.')
        repl = cls(old_regex.pattern, new, **kwargs)
        repl.old_regex = old_regex
        return repl

    @property
    def case_insensitive(self):
        """Return whether the search text is case insensitive."""
        return self._case_insensitive

    @property
    def use_regex(self):
        """Return whether the search text is using regex."""
        return self._use_regex

    def _compile(self, use_regex, flags) -> None:
        """Compile the search regex and exceptions."""
        super()._compile(use_regex, flags)
        precompile_exceptions(self.exceptions, use_regex, flags)

    def get_inside_exceptions(self):
        """Get exceptions on text (inside exceptions)."""
        return _get_text_exceptions(self.exceptions or {})


class ReplacementList(list):

    """A list of replacements which all share some properties.

    The shared properties are:
    * use_regex
    * exceptions
    * case_insensitive

    Each entry in this list should be a ReplacementListEntry. The exceptions
    are compiled only once.
    """

    def __init__(self, use_regex, exceptions, case_insensitive, edit_summary,
                 name) -> None:
        """Create a fix list which can contain multiple replacements."""
        super().__init__()
        self.use_regex = use_regex
        self._exceptions = exceptions
        self.exceptions = None
        self.case_insensitive = case_insensitive
        self.edit_summary = edit_summary
        self.name = name

    def _compile_exceptions(self, use_regex, flags) -> None:
        """Compile the exceptions if not already done."""
        if not self.exceptions and self._exceptions is not None:
            self.exceptions = dict(self._exceptions)
            precompile_exceptions(self.exceptions, use_regex, flags)


class ReplacementListEntry(ReplacementBase):

    """A replacement entry for ReplacementList."""

    def __init__(self, old, new, fix_set, edit_summary=None,
                 default_summary=True) -> None:
        """Create a replacement entry inside a fix set."""
        super().__init__(old, new, edit_summary, default_summary)
        self.fix_set = fix_set

    @property
    def case_insensitive(self):
        """Return whether the fix set is case insensitive."""
        return self.fix_set.case_insensitive

    @property
    def use_regex(self):
        """Return whether the fix set is using regex."""
        return self.fix_set.use_regex

    @property
    def exceptions(self):
        """Return the exceptions of the fix set."""
        return self.fix_set.exceptions

    @property
    def edit_summary(self):
        """Return this entry's edit summary or the fix's summary."""
        if self._edit_summary is None:
            return self.fix_set.edit_summary
        return self._edit_summary

    @property
    def container(self):
        """Container object which contains this replacement.

        A container object is an object that groups one or more
        replacements together and provides some properties that are
        common to all of them. For example, containers may define a
        common name for a group of replacements, or a common edit
        summary.

        Container objects must have a "name" attribute.
        """
        return self.fix_set

    def _compile(self, use_regex, flags) -> None:
        """Compile the search regex and the fix's exceptions."""
        super()._compile(use_regex, flags)
        self.fix_set._compile_exceptions(use_regex, flags)

    def get_inside_exceptions(self):
        """Get exceptions on text (inside exceptions)."""
        return _get_text_exceptions(self.fix_set.exceptions or {})


class XmlDumpReplacePageGenerator:

    """Iterator that will yield Pages that might contain text to replace.

    These pages will be retrieved from a local XML dump file.

    :param xmlFilename: The dump's path, either absolute or relative
    :param xmlStart: Skip all articles in the dump before this one
    :param replacements: A list of 2-tuples of original text (as a
        compiled regular expression) and replacement text (as a string).
    :param exceptions: A dictionary which defines when to ignore an
        occurrence. See docu of the ReplaceRobot initializer below.
    :type exceptions: dict
    """

    def __init__(self,
                 xmlFilename: str,
                 xmlStart: str,
                 replacements: list[tuple[Any, str]],
                 exceptions: dict[str, Any],
                 site) -> None:
        """Initializer."""
        self.xmlFilename = xmlFilename
        self.replacements = replacements
        self.exceptions = exceptions
        self.xmlStart = xmlStart
        self.skipping = bool(xmlStart)

        self.excsInside = []
        if 'inside-tags' in self.exceptions:
            self.excsInside += self.exceptions['inside-tags']
        if 'inside' in self.exceptions:
            self.excsInside += self.exceptions['inside']
        from pywikibot import xmlreader
        if site:
            self.site = site
        else:
            self.site = pywikibot.Site()
        dump = xmlreader.XmlDump(self.xmlFilename, on_error=pywikibot.error)
        self.parser = dump.parse()

    def __iter__(self):
        """Iterator method."""
        try:
            for entry in self.parser:
                if self.skipping:
                    if entry.title != self.xmlStart:
                        continue
                    self.skipping = False
                if self.isTitleExcepted(entry.title) \
                        or self.isTextExcepted(entry.text):
                    continue
                new_text = entry.text
                for replacement in self.replacements:
                    # This doesn't do an actual replacement but just
                    # checks if at least one does apply
                    new_text = textlib.replaceExcept(
                        new_text, replacement.old_regex, replacement.new,
                        self.excsInside + replacement.get_inside_exceptions(),
                        site=self.site)
                if new_text != entry.text:
                    yield pywikibot.Page(self.site, entry.title)

        except KeyboardInterrupt:
            with suppress(NameError):
                if not self.skipping:
                    pywikibot.info(f'To resume, use "-xmlstart:{entry.title}"'
                                   ' on the command line.')

    def isTitleExcepted(self, title) -> bool:
        """Return True if one of the exceptions applies for the given title."""
        if 'title' in self.exceptions:
            for exc in self.exceptions['title']:
                if exc.search(title):
                    return True
        if 'require-title' in self.exceptions:
            for req in self.exceptions['require-title']:
                if not req.search(title):  # if not all requirements are met:
                    return True

        return False

    def isTextExcepted(self, text) -> bool:
        """Return True if one of the exceptions applies for the given text."""
        if 'text-contains' in self.exceptions:
            return any(exc.search(text)
                       for exc in self.exceptions['text-contains'])
        return False


class ReplaceRobot(SingleSiteBot, ExistingPageBot):

    """A bot that can do text replacements.

    :param generator: generator that yields Page objects
    :type generator: generator
    :param replacements: a list of Replacement instances or sequences of
        length 2 with the original text (as a compiled regular expression)
        and replacement text (as a string).
    :param exceptions: a dictionary which defines when not to change an
        occurrence. This dictionary can have these keys:

        title
            A list of regular expressions. All pages with titles that
            are matched by one of these regular expressions are skipped.
        text-contains
            A list of regular expressions. All pages with text that
            contains a part which is matched by one of these regular
            expressions are skipped.
        inside
            A list of regular expressions. All occurrences are skipped which
            lie within a text region which is matched by one of these
            regular expressions.
        inside-tags
            A list of strings. These strings must be keys from the
            dictionary in :func:`textlib._create_default_regexes` or must be
            accepted by :func:`textlib.get_regexes`.

    :keyword allowoverlap: when matches overlap, all of them are replaced.
    :type allowoverlap: bool
    :keyword recursive: Recurse replacement as long as possible.
    :type recursive: bool
    :keyword addcat: category to be added to every page touched
    :type addcat: pywikibot.Category or str or None
    :keyword sleep: slow down between processing multiple regexes
    :type sleep: int
    :keyword summary: Set the summary message text bypassing the default
    :type summary: str
    :keyword always: the user won't be prompted before changes are made
    :type keyword: bool
    :keyword site: Site the bot is working on.

    .. warning::
       - Be careful with `recursive` parameter, this might lead to an
         infinite loop.
       - `site` parameter should be passed to constructor.
         Otherwise the bot takes the current site and warns the operator
         about the missing site
    """

    def __init__(self, generator,
                 replacements: list[tuple[Any, str]],
                 exceptions: dict[str, Any] | None = None,
                 **kwargs) -> None:
        """Initializer."""
        self.available_options.update({
            'addcat': None,
            'allowoverlap': False,
            'quiet': False,
            'recursive': False,
            'sleep': 0.0,
            'summary': None,
        })
        super().__init__(generator=generator, **kwargs)

        for i, replacement in enumerate(replacements):
            if isinstance(replacement, Sequence):
                if len(replacement) != 2:
                    raise ValueError(f'Replacement number {i} does not have '
                                     f'exactly two elements: {replacement}')
                # Replacement assumes it gets strings but it's already compiled
                replacements[i] = Replacement.from_compiled(replacement[0],
                                                            replacement[1])
        self.replacements = replacements
        self.exceptions = exceptions or {}

        if self.opt.addcat and isinstance(self.opt.addcat, str):
            self.opt.addcat = pywikibot.Category(self.site, self.opt.addcat)

    def isTitleExcepted(self, title, exceptions=None) -> bool:
        """Return True if one of the exceptions applies for the given title."""
        if exceptions is None:
            exceptions = self.exceptions
        if 'title' in exceptions:
            for exc in exceptions['title']:
                if exc.search(title):
                    return True
        if 'require-title' in exceptions:
            for req in exceptions['require-title']:
                if not req.search(title):
                    return True
        return False

    def isTextExcepted(self, text, exceptions=None) -> bool:
        """Return True iff one of the exceptions applies for the given text."""
        if exceptions is None:
            exceptions = self.exceptions

        if 'text-contains' in exceptions:
            return any(exc.search(text) for exc in exceptions['text-contains'])

        return False

    def apply_replacements(self, original_text, applied, page) -> str:
        """Apply all replacements to the given text."""
        new_text = original_text
        exceptions = _get_text_exceptions(self.exceptions)
        skipped_containers = set()
        for replacement in self.replacements:
            if self.opt.sleep:
                pywikibot.sleep(self.opt.sleep)
            if (replacement.container
                    and replacement.container.name in skipped_containers):
                continue

            if self.isTitleExcepted(page.title(), replacement.exceptions):
                if replacement.container:
                    pywikibot.info(
                        f'Skipping fix "{replacement.container.name}" on '
                        f'{page.title(as_link=True)} because the title is on '
                        'the exceptions list.'
                    )
                    skipped_containers.add(replacement.container.name)
                else:
                    pywikibot.info(
                        'Skipping unnamed replacement '
                        f'({replacement.description}) on '
                        f'{page.title(as_link=True)} because the title is on'
                        ' the exceptions list.'
                    )
                continue

            if self.isTextExcepted(original_text, replacement.exceptions):
                continue

            old_text = new_text
            new_text = textlib.replaceExcept(
                new_text, replacement.old_regex, replacement.new,
                exceptions + replacement.get_inside_exceptions(),
                allowoverlap=self.opt.allowoverlap, site=self.site)
            if old_text != new_text:
                applied.add(replacement)

        return new_text

    def generate_summary(self, applied_replacements):
        """Generate a summary message for the replacements."""
        # all replacements which are merged into the default message
        default_summaries = set()
        # all message parts
        summary_messages = set()
        for replacement in applied_replacements:
            if replacement.edit_summary:
                summary_messages.add(replacement.edit_summary)
            elif replacement.default_summary:
                default_summaries.add((replacement.old, replacement.new))

        summary_messages = sorted(summary_messages)
        if default_summaries:
            if self.opt.summary:
                msg = self.opt.summary
            else:
                msg = i18n.twtranslate(self.site, 'replace-replacing')
            comma = self.site.mediawiki_message('comma-separator')
            default_summary = comma.join(
                '-{} +{}'.format(*default_summary)
                for default_summary in default_summaries)
            desc = {'description': f' ({default_summary})'}
            summary_messages.insert(0, msg % desc)

        semicolon = self.site.mediawiki_message('semicolon-separator')
        return semicolon.join(summary_messages)

    def skip_page(self, page) -> bool:
        """Check whether treat should be skipped for the page."""
        if super().skip_page(page):
            return True

        if self.isTitleExcepted(page.title()):
            pywikibot.warning(
                f'Skipping {page} because the title is on the exceptions list.'
            )
            return True

        if not page.has_permission():
            pywikibot.warning(f"You can't edit page {page}")
            return True

        return False

    def treat(self, page) -> None:
        """Work on each page retrieved from generator.

        .. version-changed:: 10.1
           After the browser call, the script affects the possibly
           changed text.
        """
        try:
            original_text = page.text
        except InvalidPageError as e:
            pywikibot.error(e)
            return

        if self.isTextExcepted(original_text):
            pywikibot.info(f'Skipping {page} because it contains text '
                           f'that is on the exceptions list.')
            return

        applied = set()
        new_text = original_text
        last_text = None
        while new_text != last_text:
            last_text = new_text
            new_text = self.apply_replacements(last_text, applied, page)
            if not self.opt.recursive:
                break

        if new_text == original_text:
            if not self.opt.quiet:
                pywikibot.info(f'No changes were necessary in {page}')
            return

        if self.opt.addcat:
            # Fetch only categories in wikitext, otherwise the others
            # will be explicitly added.
            cats = textlib.getCategoryLinks(new_text, site=page.site)
            if self.opt.addcat not in cats:
                cats.append(self.opt.addcat)
                new_text = textlib.replaceCategoryLinks(new_text, cats,
                                                        site=page.site)

        context = 0
        while True:
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            self.current_page = page
            pywikibot.showDiff(original_text, new_text, context=context)
            if self.opt.always:
                break

            choice = pywikibot.input_choice(
                'Do you want to accept these changes?',
                [('Yes', 'y'), ('No', 'n'), ('Edit original', 'e'),
                 ('edit Latest', 'l'), ('open in Browser', 'b'),
                 ('More context', 'm'), ('All', 'a')],
                default='N')

            if choice == 'm':
                context = context * 3 if context else 3
                continue

            if choice in ('e', 'l'):
                text_editor = editor.TextEditor()
                edit_text = original_text if choice == 'e' else new_text
                as_edited = text_editor.edit(edit_text)
                # if user didn't press Cancel
                if as_edited and as_edited != new_text:
                    new_text = as_edited
                continue

            if choice == 'b':
                # open in browser and leave
                pywikibot.bot.open_webbrowser(page)
                try:
                    page.get(get_redirect=True, force=True)
                except NoPageError:
                    pywikibot.info(f'Page {page.title()} has been deleted.')
                else:
                    self.treat(page)
                return

            if choice == 'n':
                return

            if choice == 'a':
                self.opt.always = True

            # break if choice is 'y' or 'a' to save
            break

        self.save(page, original_text, new_text, applied, show_diff=False,
                  asynchronous=not self.opt.always)

    def save(self, page, oldtext, newtext, applied, **kwargs) -> None:
        """Save the given page."""
        self.userPut(page, oldtext, newtext,
                     summary=self.generate_summary(applied),
                     ignore_save_related_errors=True, **kwargs)

    def user_confirm(self, question) -> bool:
        """Always return True due to our own input choice."""
        return True


def prepareRegexForMySQL(pattern: str) -> str:
    """Convert regex to MySQL syntax."""
    pattern = pattern.replace(r'\s', '[:space:]')
    pattern = pattern.replace(r'\d', '[:digit:]')
    pattern = pattern.replace(r'\w', '[:alnum:]')
    return pattern.replace("'", '\\' + "'")


EXC_KEYS = {
    '-excepttitle': 'title',
    '-requiretitle': 'require-title',
    '-excepttext': 'text-contains',
    '-exceptinside': 'inside',
    '-exceptinsidetag': 'inside-tags'
}
"""Dictionary to convert exceptions command line options to exceptions keys.

.. version-added:: 7.0
"""


@dataclass
class _ReplaceConfig:

    """Configuration parsed from the command line."""

    bot_options: dict[str, Any]
    replacement_args: list[str]
    fix_names: list[str]
    exceptions: dict[str, list[str]]
    edit_summary: str | bool
    preload: bool
    regex: bool
    flags: int
    xml_filename: str | None
    xml_start: str | None
    sql_query: str | None


_SCRIPT_OPTION_VALUES = {
    '-regex': ('regex', True),
    '-manualinput': ('manual_input', True),
    '-nopreload': ('preload', False),
}
_BOT_VALUE_OPTIONS = {
    '-sleep': ('sleep', float),
    '-addcat': ('addcat', str),
}
_REGEX_FLAGS = {
    '-nocase': re.IGNORECASE,
    '-dotall': re.DOTALL,
    '-multiline': re.MULTILINE,
}


def handle_exceptions(*args: str) -> tuple[list[str], dict[str, list[str]]]:
    """Handle exceptions args to ignore pages which contain certain texts.

    .. version-added:: 7.0
    """
    exceptions = {key: [] for key in EXC_KEYS.values()}
    local_args = []
    for argument in args:
        arg, _, value = argument.partition(':')
        if arg in EXC_KEYS:
            exceptions[EXC_KEYS[arg]].append(value)
        else:
            local_args.append(argument)
    return local_args, exceptions


def handle_pairsfile(filename: str) -> list[str] | None:
    """Handle -pairsfile argument.

    .. version-added:: 7.0
    .. version-changed:: 9.2
       replacement patterns are printed if they are incomplete.
    """
    if not filename:
        filename = pywikibot.input(
            'Please enter the filename to read replacements from:')

    try:
        # use utf-8-sig to ignore BOM
        content = Path(filename).read_text(encoding='utf-8-sig')
        if not content:
            raise OSError(f'{filename} is empty.')
    except OSError as e:
        pywikibot.error(f'Error loading {filename}: {e}')
        return None

    replacements = content.splitlines()
    if len(replacements) % 2:
        pywikibot.error(f'{filename} contains an incomplete pattern '
                        f'replacement pair:\n{replacements}')
        return None

    return replacements


def handle_manual() -> list[str]:
    """Handle manual input.

    .. version-added:: 7.0
    """
    pairs = []
    old = pywikibot.input('Please enter the text that should be replaced:')
    while old:
        new = pywikibot.input('Please enter the new text:')
        pairs += [old, new]
        old = pywikibot.input(
            'Please enter another text that should be replaced,\n'
            'or press Enter to start:')
    return pairs


def handle_sql(sql: str,
               replacements: list[re.Pattern],
               exceptions: list[re.Pattern]) -> Generator:
    """Handle default sql query.

    .. version-added:: 7.0
    """
    if not sql:
        where_clause = 'WHERE ({})'.format(' OR '.join(
            f"old_text RLIKE '{prepareRegexForMySQL(repl.old_regex.pattern)}'"

            for repl in replacements))

        if exceptions:
            except_clause = 'AND NOT ({})'.format(' OR '.join(
                f"old_text RLIKE '{prepareRegexForMySQL(exc.pattern)}'"

                for exc in exceptions))
        else:
            except_clause = ''

        sql = f"""
SELECT page_namespace, page_title
FROM page
JOIN text ON (page_id = old_id)
{where_clause}
{except_clause}
LIMIT 200"""

    return pagegenerators.MySQLPageGenerator(sql)


def _parse_args(
    args: Sequence[str],
    generator_factory: pagegenerators.GeneratorFactory,
) -> _ReplaceConfig | None:
    """Parse command-line arguments for the replace script."""
    bot_options = {}
    edit_summary = ''
    replacement_args = []
    file_replacements: list[str] | None = []
    fix_names = []
    sql_query: str | None = None
    flags = 0
    script_options = {
        'regex': False,
        'manual_input': False,
        'preload': True,
    }
    xml_options = {
        '-xml': (
            'xml_filename', i18n.input, 'pywikibot-enter-xml-filename'),
        '-xmlstart': (
            'xml_start', pywikibot.input,
            'Please enter the dumped article to start with:'),
    }
    xml_values: dict[str, str | None] = {
        'xml_filename': None,
        'xml_start': None,
    }

    local_args = pywikibot.handle_args(args)
    local_args = generator_factory.handle_args(local_args)
    local_args, exceptions = handle_exceptions(*local_args)

    for arg in local_args:
        option, _, value = arg.partition(':')
        if option in _SCRIPT_OPTION_VALUES:
            name, option_value = _SCRIPT_OPTION_VALUES[option]
            script_options[name] = option_value
        elif option in xml_options:
            name, input_function, prompt = xml_options[option]
            xml_values[name] = value or input_function(prompt)
        elif option == '-mysqlquery':
            sql_query = value
        elif option == '-fix':
            fix_names.append(value)
        elif option in _BOT_VALUE_OPTIONS:
            name, converter = _BOT_VALUE_OPTIONS[option]
            bot_options[name] = converter(value)
        elif option in ('-allowoverlap', '-always', '-quiet', '-recursive'):
            bot_options[option[1:]] = True
        elif option in _REGEX_FLAGS:
            flags |= _REGEX_FLAGS[option]
        elif option == '-summary':
            edit_summary = value
        elif option == '-automaticsummary':
            edit_summary = True
        elif option == '-pairsfile':
            file_replacements = handle_pairsfile(value)
        else:
            replacement_args.append(arg)

    if file_replacements is None:
        return None

    if len(replacement_args) % 2:
        pywikibot.error('Incomplete command line pattern replacement pair:\n'
                        f'{replacement_args}')
        return None

    replacement_args += file_replacements
    if (not (replacement_args or fix_names)
            or script_options['manual_input']):
        replacement_args += handle_manual()

    return _ReplaceConfig(
        bot_options=bot_options,
        replacement_args=replacement_args,
        fix_names=fix_names,
        exceptions=exceptions,
        edit_summary=edit_summary,
        preload=script_options['preload'],
        regex=script_options['regex'],
        flags=flags,
        xml_filename=xml_values['xml_filename'],
        xml_start=xml_values['xml_start'],
        sql_query=sql_query,
    )


def _build_commandline_replacements(
    replacement_args: list[str],
    site,
    edit_summary: str | bool,
) -> tuple[list[Replacement], str | None]:
    """Create replacements and an example summary from command-line pairs."""
    replacements = []
    single_summary = None
    automatic_summary = not edit_summary or edit_summary is True

    for old, new in batched(replacement_args, 2):
        replacement = Replacement(old, new)
        if automatic_summary and not single_summary:
            single_summary = i18n.twtranslate(
                site,
                'replace-replacing',
                {'description': f' (-{replacement.old} +{replacement.new})'}
            )
        replacements.append(replacement)

    return replacements, single_summary


def _get_fix(fix_name: str) -> dict[str, Any] | None:
    """Return a validated predefined fix or ``None`` on error."""
    try:
        fix = fixes.fixes[fix_name]
    except KeyError:
        pywikibot.info('Available predefined fixes are: {}'
                       .format(', '.join(fixes.fixes.keys())))
        if not fixes.user_fixes_loaded:
            pywikibot.info(f'The user fixes file could not be found: '
                           f'{fixes.filename}')
        return None

    if not isinstance(fix, dict):
        pywikibot.error(
            f'fixes[{fix_name!r}] is a {type(fix).__name__}, not a dict')
        if type(fix) is tuple:
            pywikibot.info('Maybe a trailing comma in your user-fixes.py?')
        pywikibot.debug(fix)
        return None

    return fix


def _get_fix_summary(fix: dict[str, Any], site) -> str | None:
    """Return the translated summary for a predefined fix."""
    if 'msg' not in fix:
        return None
    if isinstance(fix['msg'], str):
        return i18n.twtranslate(site, str(fix['msg']))
    return i18n.translate(site, fix['msg'], fallback=True)


def _build_fix_set(
    fix_name: str,
    fix: dict[str, Any],
    set_summary: str | None,
) -> tuple[ReplacementList, list[str]]:
    """Create a replacement set and collect its missing summaries."""
    replacement_set = ReplacementList(
        fix.get('regex'),
        fix.get('exceptions'),
        fix.get('nocase'),
        set_summary,
        name=fix_name,
    )
    missing_summaries = []

    for index, replacement in enumerate(fix['replacements'], start=1):
        summary = None if len(replacement) < 3 else replacement[2]
        if not set_summary and not summary:
            missing_summaries.append(
                f'"{fix_name}" (replacement #{index})')
        if chars.contains_invisible(replacement[0]):
            pywikibot.warning(
                'The old string '
                f'"{chars.replace_invisible(replacement[0])}"'
                ' contains formatting characters like U+200E'
            )
        if (not callable(replacement[1])
                and chars.contains_invisible(replacement[1])):
            pywikibot.warning(
                'The new string '
                f'"{chars.replace_invisible(replacement[1])}"'
                ' contains formatting characters like U+200E')
        replacement_set.append(ReplacementListEntry(
            old=replacement[0],
            new=replacement[1],
            fix_set=replacement_set,
            edit_summary=summary,
        ))

    return replacement_set, missing_summaries


def _merge_exceptions(
    replacement_set: ReplacementList,
    exceptions: dict[str, list[str]],
) -> None:
    """Merge exceptions from a predefined fix into script exceptions."""
    if replacement_set._exceptions is None:
        return

    for key, values in replacement_set._exceptions.items():
        if key in exceptions:
            exceptions[key] = list(set(exceptions[key]) | set(values))
        else:
            exceptions[key] = values


def _load_fixes(
    fix_names: list[str],
    site,
    generator_factory: pagegenerators.GeneratorFactory,
    exceptions: dict[str, list[str]],
) -> tuple[list[ReplacementListEntry], list[str]] | None:
    """Load predefined fixes and collect their missing summaries."""
    replacements = []
    missing_summaries = []
    generators_given = bool(generator_factory.gens)

    for fix_name in fix_names:
        fix = _get_fix(fix_name)
        if fix is None:
            return None
        if not fix['replacements']:
            pywikibot.warning(f'No replacements defined for fix {fix_name!r}')
            continue

        set_summary = _get_fix_summary(fix, site)
        if not generators_given and 'generator' in fix:
            generator_args = fix['generator']
            if isinstance(generator_args, str):
                generator_factory.handle_arg(generator_args)
            else:
                generator_factory.handle_args(generator_args)

        replacement_set, missing_fix_summaries = _build_fix_set(
            fix_name, fix, set_summary)
        if replacement_set:
            replacements.extend(replacement_set)
            _merge_exceptions(replacement_set, exceptions)

        if len(fix['replacements']) == len(missing_fix_summaries):
            missing_summaries.append(f'"{fix_name}" (all replacements)')
        else:
            missing_summaries += missing_fix_summaries

    return replacements, missing_summaries


def _resolve_summary(
    edit_summary: str | bool,
    single_summary: str | None,
    missing_fix_summaries: list[str],
) -> str | bool:
    """Display summary information and return the edit summary to use."""
    if ((not edit_summary or edit_summary is True)
            and (missing_fix_summaries or single_summary)):
        if single_summary:
            pywikibot.info('The summary message for the command line '
                           'replacements will be something like: '
                           + single_summary)
        if missing_fix_summaries:
            pywikibot.info('The summary will not be used when the fix has '
                           'one defined but the following fix(es) do(es) '
                           'not have a summary defined: {}'
                           .format(', '.join(missing_fix_summaries)))
        if edit_summary is not True:
            return pywikibot.input(
                'Press Enter to use this automatic message, or enter a '
                'description of the\nchanges your bot will make:')
        return ''

    return edit_summary


def _compile_replacements(
    replacements: list[ReplacementBase],
    exceptions: dict[str, Any],
    regex: bool,
    flags: int,
) -> None:
    """Compile replacements and exceptions before generator creation."""
    for replacement in replacements:
        replacement.compile(regex, flags)
    precompile_exceptions(exceptions, regex, flags)


def _build_generator(
    generator_factory: pagegenerators.GeneratorFactory,
    replacements: list[ReplacementBase],
    exceptions: dict[str, Any],
    site,
    *,
    xml_filename: str | None,
    xml_start: str | None,
    sql_query: str | None,
    preload: bool,
):
    """Create and combine the configured page generators."""
    generator = None
    if xml_filename:
        generator = XmlDumpReplacePageGenerator(
            xml_filename, xml_start, replacements, exceptions, site)
    elif sql_query is not None:
        # Only -excepttext option is considered by the query. Other
        # exceptions are taken into account by the ReplaceRobot.
        generator = handle_sql(
            sql_query, replacements, exceptions['text-contains'])

    return generator_factory.getCombinedGenerator(
        generator, preload=preload)


def main(*args: str) -> None:
    """Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    .. version-changed:: 9.2
       replacement patterns are printed if they are incomplete.

    :param args: command line arguments
    """
    generator_factory = pagegenerators.GeneratorFactory(
        disabled_options=['mysqlquery'])
    config = _parse_args(args, generator_factory)
    if config is None:
        return

    site = pywikibot.Site()
    replacements, single_summary = _build_commandline_replacements(
        config.replacement_args, site, config.edit_summary)

    fix_result = _load_fixes(
        config.fix_names, site, generator_factory, config.exceptions)
    if fix_result is None:
        return
    fix_replacements, missing_fix_summaries = fix_result
    replacements.extend(fix_replacements)

    edit_summary = _resolve_summary(
        config.edit_summary, single_summary, missing_fix_summaries)
    _compile_replacements(
        replacements, config.exceptions, config.regex, config.flags)
    generator = _build_generator(
        generator_factory,
        replacements,
        config.exceptions,
        site,
        xml_filename=config.xml_filename,
        xml_start=config.xml_start,
        sql_query=config.sql_query,
        preload=config.preload,
    )

    bot = ReplaceRobot(
        generator, replacements, config.exceptions, site=site,
        summary=edit_summary, **config.bot_options)
    site.login()
    bot.run()


if __name__ == '__main__':
    main()
