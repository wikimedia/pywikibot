#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot will make direct text replacements.

It will retrieve information on which pages might need changes either from
an XML dump or a text file, or only change a single page.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-xml              Retrieve information from a local XML dump (pages-articles
                  or pages-meta-current, see https://download.wikimedia.org).
                  Argument can also be given as "-xml:filename".

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
                  inserted.

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

-replacementfile  Lines from the given file name(s) will be read as replacement
                  arguments. i.e. a file containing lines "a" and "b", used as
                  python replace.py -page:X -replacementfile:file c d
                  will replace 'a' with 'b' and 'c' with 'd'.

-always           Don't prompt you for each replacement

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

Examples:

If you want to change templates from the old syntax, e.g. {{msg:Stub}}, to the
new syntax, e.g. {{Stub}}, download an XML dump file (pages-articles) from
https://download.wikimedia.org, then use this command:

    python replace.py -xml -regex "{{msg:(.*?)}}" "{{\1}}"

If you have a dump called foobar.xml and want to fix typos in articles, e.g.
Errror -> Error, use this:

    python replace.py -xml:foobar.xml "Errror" "Error" -namespace:0

If you want to do more than one replacement at a time, use this:
    python replace.py -xml:foobar.xml "Errror" "Error" "Faail" "Fail" -namespace:0

If you have a page called 'John Doe' and want to fix the format of ISBNs, use:

    python replace.py -page:John_Doe -fix:isbn

This command will change 'referer' to 'referrer', but not in pages which
talk about HTTP, where the typo has become part of the standard:

    python replace.py referer referrer -file:typos.txt -excepttext:HTTP

Please type "replace.py -help | more" if you can't read the top of the help.
"""
#
# (C) Daniel Herding, 2004-2012
# (C) Pywikibot team, 2004-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import codecs
import collections
import re
import time
import sys

import pywikibot

from pywikibot import i18n, textlib, pagegenerators, Bot
from pywikibot import editor as editarticle

# Imports predefined replacements tasks from fixes.py
from pywikibot import fixes

from pywikibot.tools import chars, deprecated_args

if sys.version_info[0] > 2:
    basestring = (str, )

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;':     pagegenerators.parameterHelp,
    '&fixes-help;': fixes.parameter_help,
}


def precompile_exceptions(exceptions, use_regex, flags):
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


class ReplacementBase(object):

    """The replacement instructions."""

    def __init__(self, old, new, edit_summary=None, default_summary=True):
        self.old = old
        self.old_regex = None
        self.new = new
        self._edit_summary = edit_summary
        self.default_summary = default_summary

    @property
    def edit_summary(self):
        return self._edit_summary

    def _compile(self, use_regex, flags):
        # This does not update use_regex and flags depending on this instance
        if not use_regex:
            self.old_regex = re.escape(self.old)
        else:
            self.old_regex = self.old
        self.old_regex = re.compile(self.old_regex, flags)

    def compile(self, use_regex, flags):
        # Set the regular expression flags
        flags |= re.UNICODE

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
                 default_summary=True):
        super(Replacement, self).__init__(old, new, edit_summary,
                                          default_summary)
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
        return self._case_insensitive

    @property
    def use_regex(self):
        return self._use_regex

    def _compile(self, use_regex, flags):
        super(Replacement, self)._compile(use_regex, flags)
        precompile_exceptions(self.exceptions, use_regex, flags)


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

    def __init__(self, use_regex, exceptions, case_insensitive, edit_summary):
        super(ReplacementList, self).__init__()
        self.use_regex = use_regex
        self._exceptions = exceptions
        self.exceptions = None
        self.case_insensitive = case_insensitive
        self.edit_summary = edit_summary

    def _compile_exceptions(self, use_regex, flags):
        if not self.exceptions and self._exceptions is not None:
            self.exceptions = dict(self._exceptions)
            precompile_exceptions(self.exceptions, use_regex, flags)


class ReplacementListEntry(ReplacementBase):

    """A replacement entry for ReplacementList."""

    def __init__(self, old, new, fix_set, edit_summary=None,
                 default_summary=True):
        super(ReplacementListEntry, self).__init__(old, new, edit_summary,
                                                   default_summary)
        self.fix_set = fix_set

    @property
    def case_insensitive(self):
        return self.fix_set.case_insensitive

    @property
    def use_regex(self):
        return self.fix_set.use_regex

    @property
    def exceptions(self):
        return self.fix_set.exceptions

    @property
    def edit_summary(self):
        if self._edit_summary is None:
            return self.fix_set.edit_summary
        else:
            return self._edit_summary

    def _compile(self, use_regex, flags):
        super(ReplacementListEntry, self)._compile(use_regex, flags)
        self.fix_set._compile_exceptions(use_regex, flags)


class XmlDumpReplacePageGenerator(object):

    """
    Iterator that will yield Pages that might contain text to replace.

    These pages will be retrieved from a local XML dump file.
    Arguments:
        * xmlFilename  - The dump's path, either absolute or relative
        * xmlStart     - Skip all articles in the dump before this one
        * replacements - A list of 2-tuples of original text (as a
                         compiled regular expression) and replacement
                         text (as a string).
        * exceptions   - A dictionary which defines when to ignore an
                         occurrence. See docu of the ReplaceRobot
                         constructor below.
    """

    def __init__(self, xmlFilename, xmlStart, replacements, exceptions, site):
        """Constructor."""
        self.xmlFilename = xmlFilename
        self.replacements = replacements
        self.exceptions = exceptions
        self.xmlStart = xmlStart
        self.skipping = bool(xmlStart)

        self.excsInside = []
        if "inside-tags" in self.exceptions:
            self.excsInside += self.exceptions['inside-tags']
        if "inside" in self.exceptions:
            self.excsInside += self.exceptions['inside']
        from pywikibot import xmlreader
        if site:
            self.site = site
        else:
            self.site = pywikibot.Site()
        dump = xmlreader.XmlDump(self.xmlFilename)
        self.parser = dump.parse()

    def __iter__(self):
        """Iterator method."""
        try:
            for entry in self.parser:
                if self.skipping:
                    if entry.title != self.xmlStart:
                        continue
                    self.skipping = False
                if not self.isTitleExcepted(entry.title) \
                        and not self.isTextExcepted(entry.text):
                    new_text = entry.text
                    for replacement in self.replacements:
                        # This doesn't do an actual replacement but just
                        # checks if at least one does apply
                        new_text = textlib.replaceExcept(
                            new_text, replacement.old_regex, replacement.new,
                            self.excsInside, self.site)
                    if new_text != entry.text:
                        yield pywikibot.Page(self.site, entry.title)
        except KeyboardInterrupt:
            try:
                if not self.skipping:
                    pywikibot.output(
                        u'To resume, use "-xmlstart:%s" on the command line.'
                        % entry.title)
            except NameError:
                pass

    def isTitleExcepted(self, title):
        """
        Return True iff one of the exceptions applies for the given title.

        @rtype: bool
        """
        if "title" in self.exceptions:
            for exc in self.exceptions['title']:
                if exc.search(title):
                    return True
        if "require-title" in self.exceptions:
            for req in self.exceptions['require-title']:
                if not req.search(title):  # if not all requirements are met:
                    return True

        return False

    def isTextExcepted(self, text):
        """
        Return True iff one of the exceptions applies for the given text.

        @rtype: bool
        """
        if "text-contains" in self.exceptions:
            for exc in self.exceptions['text-contains']:
                if exc.search(text):
                    return True
        return False


class ReplaceRobot(Bot):

    """A bot that can do text replacements."""

    @deprecated_args(acceptall='always')
    def __init__(self, generator, replacements, exceptions={},
                 always=False, allowoverlap=False, recursive=False,
                 addedCat=None, sleep=None, summary='', site=None, **kwargs):
        """
        Constructor.

        Arguments:
            * generator    - A generator that yields Page objects.
            * replacements - A list of Replacement instances or sequences of
                             length 2 with the  original text (as a compiled
                             regular expression) and replacement text (as a
                             string).
            * exceptions   - A dictionary which defines when not to change an
                             occurrence. See below.
            * always       - If True, the user won't be prompted before changes
                             are made.
            * allowoverlap - If True, when matches overlap, all of them are
                             replaced.
            * addedCat     - If set to a value, add this category to every page
                             touched.
                             It can be a string or a Category object.

        Structure of the exceptions dictionary:
        This dictionary can have these keys:

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
                exceptionRegexes dictionary in textlib.replaceExcept().

        """
        super(ReplaceRobot, self).__init__(generator=generator,
                                           always=always,
                                           site=site,
                                           **kwargs)

        for i, replacement in enumerate(replacements):
            if isinstance(replacement, collections.Sequence):
                if len(replacement) != 2:
                    raise ValueError('Replacement number {0} does not have '
                                     'exactly two elements: {1}'.format(
                                     i, replacement))
                # Replacement assumes it gets strings but it's already compiled
                replacements[i] = Replacement.from_compiled(replacement[0],
                                                            replacement[1])
        self.replacements = replacements
        self.exceptions = exceptions
        self.acceptall = always  # deprecated
        self.allowoverlap = allowoverlap
        self.recursive = recursive

        if addedCat:
            if isinstance(addedCat, pywikibot.Category):
                self.addedCat = addedCat
            else:
                self.addedCat = pywikibot.Category(self.site, addedCat)

        self.sleep = sleep
        self.summary = summary
        self.changed_pages = 0

    def isTitleExcepted(self, title):
        """
        Return True iff one of the exceptions applies for the given title.

        @rtype: bool
        """
        if "title" in self.exceptions:
            for exc in self.exceptions['title']:
                if exc.search(title):
                    return True
        if "require-title" in self.exceptions:
            for req in self.exceptions['require-title']:
                if not req.search(title):
                    return True
        return False

    def isTextExcepted(self, original_text):
        """
        Return True iff one of the exceptions applies for the given text.

        @rtype: bool
        """
        if "text-contains" in self.exceptions:
            for exc in self.exceptions['text-contains']:
                if exc.search(original_text):
                    return True
        return False

    def apply_replacements(self, original_text, applied):
        """
        Apply all replacements to the given text.

        @rtype: unicode, set
        """
        def get_exceptions(exceptions):
            return exceptions.get('inside-tags', []) + exceptions.get('inside', [])
        new_text = original_text
        exceptions = get_exceptions(self.exceptions)
        for replacement in self.replacements:
            if self.sleep is not None:
                time.sleep(self.sleep)
            old_text = new_text
            new_text = textlib.replaceExcept(
                new_text, replacement.old_regex, replacement.new,
                exceptions + get_exceptions(replacement.exceptions or {}),
                allowoverlap=self.allowoverlap, site=self.site)
            if old_text != new_text:
                applied.add(replacement)

        return new_text

    def doReplacements(self, original_text):
        return self.apply_replacements(original_text, set())

    def count_changes(self, page, err):  # pylint: disable=unused-argument
        """Count succesfully changed pages."""
        # This is an async put callback
        if not isinstance(err, Exception):
            self.changed_pages += 1

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
            if self.summary:
                summary_messages.insert(0, self.summary)
            else:
                comma = self.site.mediawiki_message('comma-separator')
                default_summary = comma.join(
                    u'-{0} +{1}'.format(*default_summary)
                    for default_summary in default_summaries)
                summary_messages.insert(0, i18n.twtranslate(
                    self.site, 'replace-replacing',
                    {'description': u' ({0})'.format(default_summary)}
                ))
        semicolon = self.site.mediawiki_message('semicolon-separator')
        return semicolon.join(summary_messages)

    def run(self):
        """Start the bot."""
        # Run the generator which will yield Pages which might need to be
        # changed.
        for page in self.generator:
            if self.isTitleExcepted(page.title()):
                pywikibot.output(
                    u'Skipping %s because the title is on the exceptions list.'
                    % page.title(asLink=True))
                continue
            try:
                # Load the page's text from the wiki
                original_text = page.get(get_redirect=True)
                if not page.canBeEdited():
                    pywikibot.output(u"You can't edit page %s"
                                     % page.title(asLink=True))
                    continue
            except pywikibot.NoPage:
                pywikibot.output(u'Page %s not found' % page.title(asLink=True))
                continue
            applied = set()
            new_text = original_text
            while True:
                if self.isTextExcepted(new_text):
                    pywikibot.output(u'Skipping %s because it contains text '
                                     u'that is on the exceptions list.'
                                     % page.title(asLink=True))
                    break
                last_text = None
                while new_text != last_text:
                    last_text = new_text
                    new_text = self.apply_replacements(last_text, applied)
                    if not self.recursive:
                        break
                if new_text == original_text:
                    pywikibot.output(u'No changes were necessary in %s'
                                     % page.title(asLink=True))
                    break
                if hasattr(self, 'addedCat'):
                    # Fetch only categories in wikitext, otherwise the others will
                    # be explicitly added.
                    cats = textlib.getCategoryLinks(new_text, site=page.site)
                    if self.addedCat not in cats:
                        cats.append(self.addedCat)
                        new_text = textlib.replaceCategoryLinks(new_text,
                                                                cats,
                                                                site=page.site)
                # Show the title of the page we're working on.
                # Highlight the title in purple.
                pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                                 % page.title())
                pywikibot.showDiff(original_text, new_text)
                if self.getOption('always'):
                    break
                choice = pywikibot.input_choice(
                    u'Do you want to accept these changes?',
                    [('Yes', 'y'), ('No', 'n'), ('Edit', 'e'),
                     ('open in Browser', 'b'), ('all', 'a')],
                    default='N')
                if choice == 'e':
                    editor = editarticle.TextEditor()
                    as_edited = editor.edit(original_text)
                    # if user didn't press Cancel
                    if as_edited and as_edited != new_text:
                        new_text = as_edited
                    continue
                if choice == 'b':
                    pywikibot.bot.open_webbrowser(page)
                    try:
                        original_text = page.get(get_redirect=True, force=True)
                    except pywikibot.NoPage:
                        pywikibot.output(u'Page %s has been deleted.'
                                         % page.title())
                        break
                    new_text = original_text
                    continue
                if choice == 'a':
                    self.options['always'] = True
                if choice == 'y':
                    page.put_async(new_text, self.generate_summary(applied), callback=self.count_changes)
                # choice must be 'N'
                break
            if self.getOption('always') and new_text != original_text:
                try:
                    page.put(new_text, self.generate_summary(applied), callback=self.count_changes)
                except pywikibot.EditConflict:
                    pywikibot.output(u'Skipping %s because of edit conflict'
                                     % (page.title(),))
                except pywikibot.SpamfilterError as e:
                    pywikibot.output(
                        u'Cannot change %s because of blacklist entry %s'
                        % (page.title(), e.url))
                except pywikibot.LockedPage:
                    pywikibot.output(u'Skipping %s (locked page)'
                                     % (page.title(),))
                except pywikibot.PageNotSaved as error:
                    pywikibot.output(u'Error putting page: %s'
                                     % (error.args,))


def prepareRegexForMySQL(pattern):
    """Convert regex to MySQL syntax."""
    pattern = pattern.replace(r'\s', '[:space:]')
    pattern = pattern.replace(r'\d', '[:digit:]')
    pattern = pattern.replace(r'\w', '[:alnum:]')

    pattern = pattern.replace("'", "\\" + "'")
    # pattern = pattern.replace('\\', '\\\\')
    # for char in ['[', ']', "'"]:
    #    pattern = pattern.replace(char, '\%s' % char)
    return pattern


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    add_cat = None
    gen = None
    # summary message
    edit_summary = u""
    # Array which will collect commandline parameters.
    # First element is original text, second element is replacement text.
    commandline_replacements = []
    # A list of 2-tuples of original text and replacement text.
    replacements = []
    # Don't edit pages which contain certain texts.
    exceptions = {
        'title':         [],
        'text-contains': [],
        'inside':        [],
        'inside-tags':   [],
        'require-title': [],  # using a seperate requirements dict needs some
    }                        # major refactoring of code.

    # Should the elements of 'replacements' and 'exceptions' be interpreted
    # as regular expressions?
    regex = False
    # Predefined fixes from dictionary 'fixes' (see above).
    fixes_set = []
    # the dump's path, either absolute or relative, which will be used
    # if -xml flag is present
    xmlFilename = None
    useSql = False
    # will become True when the user presses a ('yes to all') or uses the
    # -always flag.
    acceptall = False
    # Will become True if the user inputs the commandline parameter -nocase
    caseInsensitive = False
    # Will become True if the user inputs the commandline parameter -dotall
    dotall = False
    # Will become True if the user inputs the commandline parameter -multiline
    multiline = False
    # Do all hits when they overlap
    allowoverlap = False
    # Do not recurse replacement
    recursive = False
    # Between a regex and another (using -fix) sleep some time (not to waste
    # too much CPU
    sleep = None
    # Request manual replacements even if replacements are already defined
    manual_input = False
    # Replacements loaded from a file
    replacement_file = None
    replacement_file_arg_misplaced = False

    # Read commandline parameters.

    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if genFactory.handleArg(arg):
            continue
        if arg == '-regex':
            regex = True
        elif arg.startswith('-xmlstart'):
            if len(arg) == 9:
                xmlStart = pywikibot.input(
                    u'Please enter the dumped article to start with:')
            else:
                xmlStart = arg[10:]
        elif arg.startswith('-xml'):
            if len(arg) == 4:
                xmlFilename = i18n.input('pywikibot-enter-xml-filename')
            else:
                xmlFilename = arg[5:]
        elif arg == '-sql':
            useSql = True
        elif arg.startswith('-excepttitle:'):
            exceptions['title'].append(arg[13:])
        elif arg.startswith('-requiretitle:'):
            exceptions['require-title'].append(arg[14:])
        elif arg.startswith('-excepttext:'):
            exceptions['text-contains'].append(arg[12:])
        elif arg.startswith('-exceptinside:'):
            exceptions['inside'].append(arg[14:])
        elif arg.startswith('-exceptinsidetag:'):
            exceptions['inside-tags'].append(arg[17:])
        elif arg.startswith('-fix:'):
            fixes_set += [arg[5:]]
        elif arg.startswith('-sleep:'):
            sleep = float(arg[7:])
        elif arg == '-always':
            acceptall = True
        elif arg == '-recursive':
            recursive = True
        elif arg == '-nocase':
            caseInsensitive = True
        elif arg == '-dotall':
            dotall = True
        elif arg == '-multiline':
            multiline = True
        elif arg.startswith('-addcat:'):
            add_cat = arg[8:]
        elif arg.startswith('-summary:'):
            edit_summary = arg[9:]
        elif arg.startswith('-allowoverlap'):
            allowoverlap = True
        elif arg.startswith('-manualinput'):
            manual_input = True
        elif arg.startswith('-replacementfile'):
            if len(commandline_replacements) % 2:
                replacement_file_arg_misplaced = True

            if arg == '-replacementfile':
                replacement_file = pywikibot.input(
                    u'Please enter the filename to read replacements from:')
            else:
                replacement_file = arg[len('-replacementfile:'):]
        else:
            commandline_replacements.append(arg)

    site = pywikibot.Site()

    if len(commandline_replacements) % 2:
        pywikibot.error('Incomplete command line pattern replacement pair.')
        return False

    if replacement_file_arg_misplaced:
        pywikibot.error(
            '-replacementfile used between a pattern replacement pair.')
        return False

    if replacement_file:
        try:
            with codecs.open(replacement_file, 'r', 'utf-8') as f:
                # strip newlines, but not other characters
                file_replacements = f.read().splitlines()
        except (IOError, OSError) as e:
            pywikibot.error(u'Error loading {0}: {1}'.format(
                replacement_file, e))
            return False

        if len(file_replacements) % 2:
            pywikibot.error(
                '{0} contains an incomplete pattern replacement pair.'.format(
                    replacement_file))
            return False

        # Strip BOM from first line
        file_replacements[0].lstrip(u'\uFEFF')
        commandline_replacements.extend(file_replacements)

    if not(commandline_replacements or fixes_set) or manual_input:
        old = pywikibot.input(u'Please enter the text that should be replaced:')
        while old:
            new = pywikibot.input(u'Please enter the new text:')
            commandline_replacements += [old, new]
            old = pywikibot.input(
                'Please enter another text that should be replaced,'
                '\nor press Enter to start:')

    single_summary = None
    for i in range(0, len(commandline_replacements), 2):
        replacement = Replacement(commandline_replacements[i],
                                  commandline_replacements[i + 1])
        if not single_summary:
            single_summary = i18n.twtranslate(
                site, 'replace-replacing',
                {'description':
                 ' (-%s +%s)' % (replacement.old, replacement.new)}
            )
        replacements.append(replacement)

    if not edit_summary:
        if single_summary:
            pywikibot.output(u'The summary message for the command line '
                             'replacements will be something like: %s'
                             % single_summary)
        if fixes_set:
            pywikibot.output('If a summary is defined for the fix, this '
                             'default summary won\'t be applied.')
        edit_summary = pywikibot.input(
            'Press Enter to use this automatic message, or enter a '
            'description of the\nchanges your bot will make:')

    # Perform one of the predefined actions.
    for fix in fixes_set:
        try:
            fix = fixes.fixes[fix]
        except KeyError:
            pywikibot.output(u'Available predefined fixes are: %s'
                             % ', '.join(fixes.fixes.keys()))
            if not fixes.user_fixes_loaded:
                pywikibot.output('The user fixes file could not be found: '
                                 '{0}'.format(fixes.filename))
            return
        if "msg" in fix:
            if isinstance(fix['msg'], basestring):
                set_summary = i18n.twtranslate(site, str(fix['msg']))
            else:
                set_summary = i18n.translate(site, fix['msg'], fallback=True)
        else:
            set_summary = None
        replacement_set = ReplacementList(fix.get('regex'),
                                          fix.get('exceptions'),
                                          fix.get('nocase'),
                                          set_summary)
        for replacement in fix['replacements']:
            summary = None if len(replacement) < 3 else replacement[2]
            if chars.contains_invisible(replacement[0]):
                pywikibot.warning('The old string "{0}" contains formatting '
                                  'characters like U+200E'.format(
                    chars.replace_invisible(replacement[0])))
            if chars.contains_invisible(replacement[1]):
                pywikibot.warning('The new string "{0}" contains formatting '
                                  'characters like U+200E'.format(
                    chars.replace_invisible(replacement[1])))
            replacements.append(ReplacementListEntry(
                old=replacement[0],
                new=replacement[1],
                fix_set=replacement_set,
                edit_summary=summary,
            ))

    # Set the regular expression flags
    flags = re.UNICODE
    if caseInsensitive:
        flags = flags | re.IGNORECASE
    if dotall:
        flags = flags | re.DOTALL
    if multiline:
        flags = flags | re.MULTILINE

    # Pre-compile all regular expressions here to save time later
    for replacement in replacements:
        replacement.compile(regex, flags)

    precompile_exceptions(exceptions, regex, flags)

    if xmlFilename:
        try:
            xmlStart
        except NameError:
            xmlStart = None
        gen = XmlDumpReplacePageGenerator(xmlFilename, xmlStart,
                                          replacements, exceptions, site)
    elif useSql:
        whereClause = 'WHERE (%s)' % ' OR '.join(
            ["old_text RLIKE '%s'" % prepareRegexForMySQL(old_regexp.pattern)
             for (old_regexp, new_text) in replacements])
        if exceptions:
            exceptClause = 'AND NOT (%s)' % ' OR '.join(
                ["old_text RLIKE '%s'" % prepareRegexForMySQL(exc.pattern)
                 for exc in exceptions])
        else:
            exceptClause = ''
        query = u"""
SELECT page_namespace, page_title
FROM page
JOIN text ON (page_id = old_id)
%s
%s
LIMIT 200""" % (whereClause, exceptClause)
        gen = pagegenerators.MySQLPageGenerator(query)

    gen = genFactory.getCombinedGenerator(gen)

    if not gen:
        # syntax error, show help text from the top of this file
        pywikibot.showHelp('replace')
        return

    preloadingGen = pagegenerators.PreloadingGenerator(gen)
    bot = ReplaceRobot(preloadingGen, replacements, exceptions, acceptall,
                       allowoverlap, recursive, add_cat, sleep, edit_summary,
                       site)
    site.login()
    bot.run()

    # Explicitly call pywikibot.stopme().
    # It will make sure the callback is triggered before replace.py is unloaded.
    pywikibot.stopme()
    pywikibot.output(u'\n%s pages changed.' % bot.changed_pages)


if __name__ == "__main__":
    main()
