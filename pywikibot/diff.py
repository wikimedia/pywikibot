# -*- coding: utf-8  -*-
"""Diff module."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'


import difflib
import sys

from collections import Sequence
if sys.version_info[0] > 2:
    from itertools import zip_longest
else:
    from itertools import izip_longest as zip_longest

try:
    from bs4 import BeautifulSoup
except ImportError as bserror:
    BeautifulSoup = False

import pywikibot
from pywikibot.backports import format_range_unified  # introduced in 2.7.2
from pywikibot.tools import deprecated_args


class Hunk(object):

    """One change hunk between a and b.

    Note: parts of this code are taken from by difflib.get_grouped_opcodes().

    """

    APPR = 1
    NOT_APPR = -1
    PENDING = 0

    def __init__(self, a, b, grouped_opcode):
        """
        Constructor.

        @param a: sequence of lines
        @param b: sequence of lines
        @param grouped_opcode: list of 5-tuples describing how to turn a into b.
            it has the same format as returned by difflib.get_opcodes().

        """
        self.a = a
        self.b = b
        self.group = grouped_opcode
        self.header = u''
        self.colors = {
            '+': 'lightgreen',
            '-': 'lightred',
        }

        self.diff = list(self.create_diff())
        self.diff_plain_text = u''.join(self.diff)
        self.diff_text = u''.join(self.format_diff())

        first, last = self.group[0], self.group[-1]
        self.a_rng = (first[1], last[2])
        self.b_rng = (first[3], last[4])

        self.header = self.get_header()
        self.diff_plain_text = u'%s\n%s' % (self.header, self.diff_plain_text)
        self.diff_text = u'%s' % self.diff_text

        self.reviewed = self.PENDING

    def get_header(self):
        """Provide header of unified diff."""
        return self.get_header_text(self.a_rng, self.b_rng) + '\n'

    @staticmethod
    def get_header_text(a_rng, b_rng, affix='@@'):
        """Provide header for any ranges."""
        a_rng = format_range_unified(*a_rng)
        b_rng = format_range_unified(*b_rng)
        return '{0} -{1} +{2} {0}'.format(affix, a_rng, b_rng)

    def create_diff(self):
        """Generator of diff text for this hunk, without formatting."""
        # make sure each line ends with '\n' to prevent
        # behaviour like http://bugs.python.org/issue2142
        def check_line(l):
            if not l.endswith('\n'):
                return l + '\n'
            return l

        for tag, i1, i2, j1, j2 in self.group:
            # equal/delete/insert add additional space after the sign as it's
            # what difflib.ndiff does do too.
            if tag == 'equal':
                for line in self.a[i1:i2]:
                    yield '  ' + check_line(line)
            if tag in ('delete'):
                for line in self.a[i1:i2]:
                    yield '- ' + check_line(line)
            if tag in ('insert'):
                for line in self.b[j1:j2]:
                    yield '+ ' + check_line(line)
            if tag in ('replace'):
                for line in difflib.ndiff(self.a[i1:i2], self.b[j1:j2]):
                    yield check_line(line)

    def format_diff(self):
        """Color diff lines."""
        diff = iter(self.diff)

        l1, l2 = '', next(diff)
        for line in diff:
            l1, l2 = l2, line
            # do not show lines starting with '?'.
            if l1.startswith('?'):
                continue
            if l2.startswith('?'):
                yield self.color_line(l1, l2)
            else:
                yield self.color_line(l1)

        # handle last line
        if not l2.startswith('?'):
            yield self.color_line(l2)

    def color_line(self, line, line_ref=None):
        """Color line characters.

        If line_ref is None, the whole line is colored.
        If line_ref[i] is not blank, line[i] is colored.
        Color depends if line starts with +/-.

        line: string
        line_ref: string.

        """
        color = line[0]

        if line_ref is None:
            if color in self.colors:
                colored_line = '\03{%s}%s\03{default}' % (self.colors[color], line)
                return colored_line
            else:
                return line

        colored_line = u''
        color_closed = True
        for char, char_ref in zip_longest(line, line_ref.strip(), fillvalue=' '):
            char_tagged = char
            if color_closed:
                if char_ref != ' ':
                    char_tagged = '\03{%s}%s' % (self.colors[color], char)
                    color_closed = False
            else:
                if char_ref == ' ':
                    char_tagged = '\03{default}%s' % char
                    color_closed = True
            colored_line += char_tagged

        if not color_closed:
            colored_line += '\03{default}'

        return colored_line

    def apply(self):
        """Turn a into b for this hunk."""
        return self.b[self.b_rng[0]:self.b_rng[1]]

    def __str__(self):
        """Return the diff as plain text."""
        return u''.join(self.diff_plain_text)

    def __repr__(self):
        """Return a reconstructable representation."""
        # TODO
        return '%s(a, b, %s)' \
               % (self.__class__.__name__, self.group)


class _SuperHunk(Sequence):

    def __init__(self, hunks):
        self._hunks = hunks
        self.a_rng = (self._hunks[0].a_rng[0], self._hunks[-1].a_rng[1])
        self.b_rng = (self._hunks[0].b_rng[0], self._hunks[-1].b_rng[1])
        self.pre_context = self._hunks[0].pre_context
        self.post_context = self._hunks[0].post_context

    def __getitem__(self, idx):
        return self._hunks[idx]

    def __len__(self):
        return len(self._hunks)


class PatchManager(object):

    """Apply patches to text_a to obtain a new text.

    If all hunks are approved, text_b will be obtained.
    """

    @deprecated_args(n='context')
    def __init__(self, text_a, text_b, context=0, by_letter=False):
        """Constructor.

        @param text_a: base text
        @type text_a: basestring
        @param text_b: target text
        @type text_b: basestring
        @param context: number of lines which are context
        @type context: int
        @param by_letter: if text_a and text_b are single lines, comparison can be done
            letter by letter.
        @type by_letter: bool
        """
        if '\n' in text_a or '\n' in text_b:
            self.a = text_a.splitlines(1)
            self.b = text_b.splitlines(1)
        else:
            if by_letter:
                self.a = text_a
                self.b = text_b
            else:
                self.a = text_a.splitlines(1)
                self.b = text_b.splitlines(1)

        # groups and hunk have same order (one hunk correspond to one group).
        s = difflib.SequenceMatcher(None, self.a, self.b)
        self.groups = list(s.get_grouped_opcodes(0))
        self.hunks = []
        previous_hunk = None
        for group in self.groups:
            hunk = Hunk(self.a, self.b, group)
            self.hunks.append(hunk)
            hunk.pre_context = hunk.a_rng[0]
            if previous_hunk:
                hunk.pre_context -= previous_hunk.a_rng[1]
                previous_hunk.post_context = hunk.pre_context
            previous_hunk = hunk
        if self.hunks:
            self.hunks[-1].post_context = len(self.a) - self.hunks[-1].a_rng[1]
        # blocks are a superset of hunk, as include also parts not
        # included in any hunk.
        self.blocks = self.get_blocks()
        self.context = context
        self._super_hunks = self._generate_super_hunks()

    def get_blocks(self):
        """Return list with blocks of indexes which compose a and, where applicable, b.

        Format of each block::

            [-1, (i1, i2), (-1, -1)] -> block a[i1:i2] does not change from a to b
                then is there is no corresponding hunk.
            [hunk index, (i1, i2), (j1, j2)] -> block a[i1:i2] becomes b[j1:j2]
        """
        blocks = []
        i2 = 0
        for hunk_idx, group in enumerate(self.groups):

            first, last = group[0], group[-1]
            i1, prev_i2, i2 = first[1], i2, last[2]

            # there is a section of unchanged text before this hunk.
            if prev_i2 < i1:
                rng = (-1, (prev_i2, i1), (-1, -1))
                blocks.append(rng)

            rng = (hunk_idx, (first[1], last[2]), (first[3], last[4]))
            blocks.append(rng)

        # there is a section of unchanged text at the end of a, b.
        if i2 < len(self.a):
            rng = (-1, (i2, len(self.a)), (-1, -1))
            blocks.append(rng)

        return blocks

    def print_hunks(self):
        """Print the headers and diff texts of all hunks to the output."""
        if self.hunks:
            pywikibot.output('\n'.join(self._generate_diff(super_hunk)
                                       for super_hunk in self._super_hunks))

    def _generate_super_hunks(self, hunks=None):
        if hunks is None:
            hunks = self.hunks
        if self.context:
            # Determine if two hunks are connected by self.context
            super_hunk = []
            super_hunks = [super_hunk]
            for hunk in hunks:
                # self.context * 2, because if self.context is 2 the hunks would be
                # directly adjacent when 4 lines in between and for anything
                # below 4 they share lines.
                # not super_hunk == first hunk as any other super_hunk is
                # created with one hunk
                if (not super_hunk or
                        hunk.pre_context <= self.context * 2):
                    # previous hunk has shared/adjacent self.context lines
                    super_hunk += [hunk]
                else:
                    super_hunk = [hunk]
                    super_hunks += [super_hunk]
        else:
            super_hunks = [[hunk] for hunk in hunks]
        return [_SuperHunk(sh) for sh in super_hunks]

    def _get_context_range(self, super_hunk):
        """Dynamically determine context range for a super hunk."""
        return ((super_hunk.a_rng[0] - min(super_hunk.pre_context, self.context),
                 super_hunk.a_rng[1] + min(super_hunk.post_context, self.context)),
                (super_hunk.b_rng[0] - min(super_hunk.pre_context, self.context),
                 super_hunk.b_rng[1] + min(super_hunk.post_context, self.context)))

    def _generate_diff(self, hunks):
        """Generate a diff text for the given hunks."""
        def extend_context(start, end):
            """Add context lines."""
            return ''.join('  {0}\n'.format(line.rstrip())
                           for line in self.a[start:end])

        context_range = self._get_context_range(hunks)

        output = ('\03{aqua}' +
                  Hunk.get_header_text(*context_range) + '\03{default}\n' +
                  extend_context(context_range[0][0], hunks[0].a_rng[0]))
        previous_hunk = None
        for hunk in hunks:
            if previous_hunk:
                output += extend_context(previous_hunk.a_rng[1], hunk.a_rng[0])
            previous_hunk = hunk
            output += hunk.diff_text
        return output + extend_context(hunks[-1].a_rng[1], context_range[0][1])

    def review_hunks(self):
        """Review hunks."""
        help_msg = ['y -> accept this hunk',
                    'n -> do not accept this hunk',
                    's -> do not accept this hunk and stop reviewing',
                    'a -> accept this hunk and all other pending',
                    'r -> review later',
                    'h -> help',
                    ]

        question = 'Accept this hunk?'
        answers = [('yes', 'y'), ('no', 'n'), ('stop', 's'), ('all', 'a'),
                   ('review', 'r'), ('help', 'h')]
        actions = {'y': Hunk.APPR,
                   'n': Hunk.NOT_APPR,
                   's': Hunk.NOT_APPR,
                   'a': Hunk.APPR,
                   'r': Hunk.PENDING,
                   }

        pending = [h for h in self.hunks if h.reviewed == h.PENDING]

        while pending:

            hunk = pending.pop(0)

            pywikibot.output(self._generate_diff(_SuperHunk([hunk])))
            choice = pywikibot.input_choice(question, answers, default='r',
                                            automatic_quit=False)

            if choice in actions.keys():
                hunk.reviewed = actions[choice]
            if choice == 's':
                while pending:
                    hunk = pending.pop(0)
                    hunk.reviewed = hunk.NOT_APPR
                break
            elif choice == 'a':
                while pending:
                    hunk = pending.pop(0)
                    hunk.reviewed = hunk.APPR
                break
            elif choice == 'h':
                pywikibot.output(u'\03{purple}%s\03{default}' % u'\n'.join(help_msg))
                pending.insert(0, hunk)
            elif choice == 'r':
                pending.append(hunk)

        return

    def apply(self):
        """Apply changes. If there are undecided changes, ask to review."""
        if any(h.reviewed == h.PENDING for h in self.hunks):
            pywikibot.output("There are unreviewed hunks.\n"
                             "Please review them before proceeding.\n")
            self.review_hunks()

        l_text = []
        for hunk_idx, (i1, i2), (j1, j2) in self.blocks:
            # unchanged text.
            if hunk_idx < 0:
                l_text.extend(self.a[i1:i2])
            # changed text; check if hunk is approved.
            else:
                hunk = self.hunks[hunk_idx]
                if hunk.reviewed == hunk.APPR:
                    l_text.extend(self.b[j1:j2])
                else:
                    l_text.extend(self.a[i1:i2])

        # Make a sanity check in case all are approved.
        if all(h.reviewed == h.APPR for h in self.hunks):
            assert u''.join(l_text) == u''.join(self.b)
        return l_text


def cherry_pick(oldtext, newtext, n=0, by_letter=False):
    """Propose a list of changes for approval.

    Text with approved changes will be returned.
    n: int, line of context as defined in difflib.get_grouped_opcodes().
    by_letter: if text_a and text_b are single lines, comparison can be done

    """
    patch = PatchManager(oldtext, newtext, n=n, by_letter=by_letter)
    pywikibot.output('\03{{lightpurple}}\n{0:*^50}\03{{default}}\n'.format('  ALL CHANGES  '))

    for hunk in patch.hunks:
        pywikibot.output(hunk.diff_text)
    pywikibot.output('\03{{lightpurple}}\n{0:*^50}\03{{default}}\n'.format('  REVIEW CHANGES  '))

    text_list = patch.apply()
    pywikibot.output('\03{{lightpurple}}\n{0:*^50}\03{{default}}\n'.format('  APPROVED CHANGES  '))

    if any(hunk.reviewed == hunk.APPR for hunk in patch.hunks):
        for hunk in patch.hunks:
            if hunk.reviewed == hunk.APPR:
                pywikibot.output(hunk.diff_text)
    else:
        pywikibot.output('\03{{lightpurple}}{0:^50}\03{{default}}'.format('None.'))

    text = ''.join(text_list)

    return text


def html_comparator(compare_string):
    """List of added and deleted contexts from 'action=compare' html string.

    This function is useful when combineds with site.py's "compare" method.
    Site.compare() returns HTML that is useful for displaying on a page.
    Here we use BeautifulSoup to get the un-HTML-ify the context of changes.
    Finally we present the added and deleted contexts.
    @param compare_string: HTML string from mediawiki API
    @type compare_string: str
    @return: deleted and added list of contexts
    @rtype: dict
    """
    # check if BeautifulSoup imported
    if not BeautifulSoup:
        raise bserror  # should have been raised and stored earlier.

    comparands = {'deleted-context': [], 'added-context': []}
    soup = BeautifulSoup(compare_string)
    for change_type, css_class in (('deleted-context', 'diff-deletedline'), ('added-context', 'diff-addedline')):
        crutons = soup.find_all('td', class_=css_class)
        for cruton in crutons:
            cruton_string = ''.join(cruton.strings)
            comparands[change_type].append(cruton_string)
    return comparands
