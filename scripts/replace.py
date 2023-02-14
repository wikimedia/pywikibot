#!/usr/bin/env python3
r"""
This bot will make direct text replacements.

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

other:            First argument is the old text, second argument is the new
                  text. If the -regex argument is given, the first argument
                  will be regarded as a regular expression, and the second
                  argument might contain expressions like \1 or \g<name>.
                  It is possible to introduce more than one pair of old text
                  and replacement.

Examples
--------

If you want to change templates from the old syntax, e.g. {{msg:Stub}}, to the
new syntax, e.g. {{Stub}}, download an XML dump file (pages-articles) from
https://dumps.wikimedia.org, then use this command:

    python pwb.py replace -xml -regex "{{msg:(.*?)}}" "{{\1}}"

If you have a dump called foobar.xml and want to fix typos in articles, e.g.
Errror -> Error, use this:

    python pwb.py replace -xml:foobar.xml "Errror" "Error" -namespace:0

If you want to do more than one replacement at a time, use this:

    python pwb.py replace -xml:foobar.xml "Errror" "Error" "Faail" "Fail" \
        -namespace:0

If you have a page called 'John Doe' and want to fix the format of ISBNs, use:

    python pwb.py replace -page:John_Doe -fix:isbn

This command will change 'referer' to 'referrer', but not in pages which
talk about HTTP, where the typo has become part of the standard:

    python pwb.py replace referer referrer -file:typos.txt -excepttext:HTTP

Please type "python pwb.py replace -help | more" if you can't read
the top of the help.
"""
#
# (C) Pywikibot team, 2004-2022
#
# Distributed under the terms of the MIT license.
#
import re
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path
from typing import Any, Optional

import pywikibot
from pywikibot import editor, fixes, i18n, pagegenerators, textlib
from pywikibot.backports import Dict, Generator, List, Pattern, Tuple
from pywikibot.bot import ExistingPageBot, SingleSiteBot
from pywikibot.exceptions import InvalidPageError, NoPageError
from pywikibot.tools import chars
from pywikibot.tools.itertools import itergroup


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

        This description is used as the default summary of the replacement. If
        you do not specify an edit summary on the command line or in some other
        way, whenever you apply this replacement to a page and submit the
        changes to the MediaWiki server, the edit summary includes the
        descriptions of each replacement that you applied to the page.
        """
        return f'-{self.old} +{self.new}'

    @property
    def container(self):
        """Container object which contains this replacement.

        A container object is an object that groups one or more replacements
        together and provides some properties that are common to all of them.
        For example, containers may define a common name for a group of
        replacements, or a common edit summary.

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

    """A single replacement with it's own data."""

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

    """
    A list of replacements which all share some properties.

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

        A container object is an object that groups one or more replacements
        together and provides some properties that are common to all of them.
        For example, containers may define a common name for a group of
        replacements, or a common edit summary.

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

    """
    Iterator that will yield Pages that might contain text to replace.

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
                 replacements: List[Tuple[Any, str]],
                 exceptions: Dict[str, Any],
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
                    pywikibot.info(
                        'To resume, use "-xmlstart:{}" on the command line.'
                        .format(entry.title))

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
            dictionary in textlib._create_default_regexes() or must be
            accepted by textlib._get_regexes().

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
                 replacements: List[Tuple[Any, str]],
                 exceptions: Optional[Dict[str, Any]] = None,
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
                    raise ValueError('Replacement number {} does not have '
                                     'exactly two elements: {}'.format(
                                         i, replacement))
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

    def isTextExcepted(self, original_text) -> bool:
        """Return True iff one of the exceptions applies for the given text."""
        if 'text-contains' in self.exceptions:
            return any(exc.search(original_text)
                       for exc in self.exceptions['text-contains'])
        return False

    def apply_replacements(self, original_text, applied, page=None):
        """
        Apply all replacements to the given text.

        :rtype: str, set
        """
        if page is None:
            pywikibot.warn(
                'You must pass the target page as the "page" parameter to '
                'apply_replacements().', DeprecationWarning, stacklevel=2)
        new_text = original_text
        exceptions = _get_text_exceptions(self.exceptions)
        skipped_containers = set()
        for replacement in self.replacements:
            if self.opt.sleep:
                pywikibot.sleep(self.opt.sleep)
            if (replacement.container
                    and replacement.container.name in skipped_containers):
                continue
            if page is not None and self.isTitleExcepted(
                    page.title(), replacement.exceptions):
                if replacement.container:
                    pywikibot.info(
                        'Skipping fix "{}" on {} because the title is on '
                        'the exceptions list.'.format(
                            replacement.container.name,
                            page.title(as_link=True)))
                    skipped_containers.add(replacement.container.name)
                else:
                    pywikibot.info(
                        'Skipping unnamed replacement ({}) on {} because '
                        'the title is on the exceptions list.'.format(
                            replacement.description, page.title(as_link=True)))
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

    def skip_page(self, page):
        """Check whether treat should be skipped for the page."""
        if super().skip_page(page):
            return True

        if self.isTitleExcepted(page.title()):
            pywikibot.warning(
                'Skipping {} because the title is on the exceptions list.'
                .format(page))
            return True

        if not page.has_permission():
            pywikibot.warning(f"You can't edit page {page}")
            return True

        return False

    def treat(self, page) -> None:
        """Work on each page retrieved from generator."""
        try:
            original_text = page.text
        except InvalidPageError as e:
            pywikibot.error(e)
            return
        applied = set()
        new_text = original_text
        last_text = None
        context = 0
        while True:
            if self.isTextExcepted(new_text):
                pywikibot.info(f'Skipping {page} because it contains text '
                               f'that is on the exceptions list.')
                return

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
                    new_text = textlib.replaceCategoryLinks(new_text,
                                                            cats,
                                                            site=page.site)
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
                    if choice == 'l':
                        # prevent changes from being applied again
                        last_text = new_text
                continue
            if choice == 'b':
                pywikibot.bot.open_webbrowser(page)
                try:
                    original_text = page.get(get_redirect=True, force=True)
                except NoPageError:
                    pywikibot.info('Page {} has been deleted.'
                                   .format(page.title()))
                    break
                new_text = original_text
                last_text = None
                continue
            if choice == 'a':
                self.opt.always = True
            if choice == 'y':
                self.save(page, original_text, new_text, applied,
                          show_diff=False, asynchronous=True)

            # choice must be 'N'
            break

        if self.opt.always and new_text != original_text:
            self.save(page, original_text, new_text, applied,
                      show_diff=False, asynchronous=False)

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
    pattern = pattern.replace("'", '\\' + "'")
    return pattern


EXC_KEYS = {
    '-excepttitle': 'title',
    '-requiretitle:': 'require-title',
    '-excepttext': 'text-contains',
    '-exceptinside': 'inside',
    '-exceptinsidetag': 'inside-tags'
}
"""Dictionary to convert exceptions command line options to exceptions keys.

    .. versionadded:: 7.0
"""


def handle_exceptions(*args: str) -> Tuple[List[str], Dict[str, str]]:
    """Handle exceptions args to ignore pages which contain certain texts.

    .. versionadded:: 7.0
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


def handle_pairsfile(filename: str) -> Optional[List[str]]:
    """Handle -pairsfile argument.

    .. versionadded:: 7.0
    """
    if not filename:
        filename = pywikibot.input(
            'Please enter the filename to read replacements from:')

    try:
        with Path(filename).open(encoding='utf-8') as f:
            replacements = f.readlines()
        if not replacements:
            raise OSError(f'{filename} is empty.')
    except OSError as e:
        pywikibot.error(f'Error loading {filename}: {e}')
        return None

    if len(replacements) % 2:
        pywikibot.error(
            f'{filename} contains an incomplete pattern replacement pair.')
        return None

    # Strip BOM from first line
    replacements[0].lstrip('\uFEFF')
    return replacements


def handle_manual() -> List[str]:
    """Handle manual input.

    .. versionadded:: 7.0
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
               replacements: List[Pattern],
               exceptions: List[Pattern]) -> Generator:
    """Handle default sql query.

    .. versionadded:: 7.0
    """
    if not sql:
        where_clause = 'WHERE ({})'.format(' OR '.join(
            "old_text RLIKE '{}'"
            .format(prepareRegexForMySQL(repl.old_regex.pattern))
            for repl in replacements))

        if exceptions:
            except_clause = 'AND NOT ({})'.format(' OR '.join(
                "old_text RLIKE '{}'"
                .format(prepareRegexForMySQL(exc.pattern))
                for exc in exceptions))
        else:
            except_clause = ''

        sql = """
SELECT page_namespace, page_title
FROM page
JOIN text ON (page_id = old_id)
{}
{}
LIMIT 200""".format(where_clause, except_clause)

    return pagegenerators.MySQLPageGenerator(sql)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    gen = None
    # summary message
    edit_summary = ''
    # Array which will collect commandline parameters.
    # First element is original text, second element is replacement text.
    preload = True  # preload pages
    commandline_replacements = []
    file_replacements = []
    # A list of 2-tuples of original text and replacement text.
    replacements = []

    # Should the elements of 'replacements' and 'exceptions' be interpreted
    # as regular expressions?
    regex = False
    # Predefined fixes from dictionary 'fixes' (see above).
    fixes_set = []
    # the dump's path, either absolute or relative, which will be used
    # if -xml flag is present
    xmlFilename = None
    xmlStart = None
    sql_query: Optional[str] = None
    # Set the default regular expression flags
    flags = 0
    # Request manual replacements even if replacements are already defined
    manual_input = False

    # Read commandline parameters.
    genFactory = pagegenerators.GeneratorFactory(
        disabled_options=['mysqlquery'])
    local_args = pywikibot.handle_args(args)
    local_args = genFactory.handle_args(local_args)
    local_args, exceptions = handle_exceptions(*local_args)

    for arg in local_args:
        opt, _, value = arg.partition(':')
        if opt == '-regex':
            regex = True
        elif opt == '-xmlstart':
            xmlStart = value or pywikibot.input(
                'Please enter the dumped article to start with:')
        elif opt == '-xml':
            xmlFilename = value or i18n.input('pywikibot-enter-xml-filename')
        elif opt == '-mysqlquery':
            sql_query = value
        elif opt == '-fix':
            fixes_set.append(value)
        elif opt == '-sleep':
            options['sleep'] = float(value)
        elif opt in ('-allowoverlap', '-always', '-quiet', '-recursive'):
            options[opt[1:]] = True
        elif opt == '-nocase':
            flags |= re.IGNORECASE
        elif opt == '-dotall':
            flags |= re.DOTALL
        elif opt == '-multiline':
            flags |= re.MULTILINE
        elif opt == '-addcat':
            options['addcat'] = value
        elif opt == '-summary':
            edit_summary = value
        elif opt == '-automaticsummary':
            edit_summary = True
        elif opt == '-manualinput':
            manual_input = True
        elif opt == '-pairsfile':
            file_replacements = handle_pairsfile(value)
        elif opt == '-nopreload':
            preload = False
        else:
            commandline_replacements.append(arg)

    if file_replacements is None:
        return

    if len(commandline_replacements) % 2:
        pywikibot.error('Incomplete command line pattern replacement pair.')
        return

    commandline_replacements += file_replacements
    if not (commandline_replacements or fixes_set) or manual_input:
        commandline_replacements += handle_manual()

    # The summary stored here won't be actually used but is only an example
    site = pywikibot.Site()
    single_summary = None
    for old, new in itergroup(commandline_replacements, 2):
        replacement = Replacement(old, new)
        if not single_summary:
            single_summary = i18n.twtranslate(
                site, 'replace-replacing',
                {'description':
                 f' (-{replacement.old} +{replacement.new})'}
            )
        replacements.append(replacement)

    # Perform one of the predefined actions.
    missing_fixes_summaries = []  # which a fixes/replacements miss a summary
    generators_given = bool(genFactory.gens)
    for fix_name in fixes_set:
        try:
            fix = fixes.fixes[fix_name]
        except KeyError:
            pywikibot.info('Available predefined fixes are: {}'
                           .format(', '.join(fixes.fixes.keys())))
            if not fixes.user_fixes_loaded:
                pywikibot.info(f'The user fixes file could not be found: '
                               f'{fixes.filename}')
            return
        if not fix['replacements']:
            pywikibot.warning(f'No replacements defined for fix {fix_name!r}')
            continue
        if 'msg' in fix:
            if isinstance(fix['msg'], str):
                set_summary = i18n.twtranslate(site, str(fix['msg']))
            else:
                set_summary = i18n.translate(site, fix['msg'], fallback=True)
        else:
            set_summary = None
        if not generators_given and 'generator' in fix:
            gen_args = fix['generator']
            if isinstance(gen_args, str):
                gen_args = [gen_args]
            for gen_arg in gen_args:
                genFactory.handle_arg(gen_arg)
        replacement_set = ReplacementList(fix.get('regex'),
                                          fix.get('exceptions'),
                                          fix.get('nocase'),
                                          set_summary,
                                          name=fix_name)
        # Whether some replacements have a summary, if so only show which
        # have none, otherwise just mention the complete fix
        missing_fix_summaries = []
        for index, replacement in enumerate(fix['replacements'], start=1):
            summary = None if len(replacement) < 3 else replacement[2]
            if not set_summary and not summary:
                missing_fix_summaries.append(
                    f'"{fix_name}" (replacement #{index})')
            if chars.contains_invisible(replacement[0]):
                pywikibot.warning('The old string "{}" contains formatting '
                                  'characters like U+200E'.format(
                                      chars.replace_invisible(replacement[0])))
            if (not callable(replacement[1])
                    and chars.contains_invisible(replacement[1])):
                pywikibot.warning('The new string "{}" contains formatting '
                                  'characters like U+200E'.format(
                                      chars.replace_invisible(replacement[1])))
            replacement_set.append(ReplacementListEntry(
                old=replacement[0],
                new=replacement[1],
                fix_set=replacement_set,
                edit_summary=summary,
            ))

        # Exceptions specified via 'fix' shall be merged to those via CLI.
        if replacement_set:
            replacements.extend(replacement_set)
            if replacement_set._exceptions is not None:
                for k, v in replacement_set._exceptions.items():
                    if k in exceptions:
                        exceptions[k] = list(set(exceptions[k]) | set(v))
                    else:
                        exceptions[k] = v

        if len(fix['replacements']) == len(missing_fix_summaries):
            missing_fixes_summaries.append(
                f'"{fix_name}" (all replacements)')
        else:
            missing_fixes_summaries += missing_fix_summaries

    if ((not edit_summary or edit_summary is True)
            and (missing_fixes_summaries or single_summary)):
        if single_summary:
            pywikibot.info('The summary message for the command line '
                           'replacements will be something like: '
                           + single_summary)
        if missing_fixes_summaries:
            pywikibot.info('The summary will not be used when the fix has '
                           'one defined but the following fix(es) do(es) '
                           'not have a summary defined: {}'
                           .format(', '.join(missing_fixes_summaries)))
        if edit_summary is not True:
            edit_summary = pywikibot.input(
                'Press Enter to use this automatic message, or enter a '
                'description of the\nchanges your bot will make:')
        else:
            edit_summary = ''

    # Pre-compile all regular expressions here to save time later
    for replacement in replacements:
        replacement.compile(regex, flags)

    precompile_exceptions(exceptions, regex, flags)

    if xmlFilename:
        gen = XmlDumpReplacePageGenerator(xmlFilename, xmlStart,
                                          replacements, exceptions, site)
    elif sql_query is not None:
        # Only -excepttext option is considered by the query. Other
        # exceptions are taken into account by the ReplaceRobot
        gen = handle_sql(sql_query, replacements, exceptions['text-contains'])

    gen = genFactory.getCombinedGenerator(gen, preload=preload)
    if pywikibot.bot.suggest_help(missing_generator=not gen):
        return

    bot = ReplaceRobot(gen, replacements, exceptions, site=site,
                       summary=edit_summary, **options)
    site.login()
    bot.run()


if __name__ == '__main__':
    main()
