"""Diff module."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import difflib
import math
from collections import abc
from difflib import _format_range_unified  # type: ignore[attr-defined]
from itertools import zip_longest
from typing import Optional, Union

import pywikibot
from pywikibot.backports import Dict, Iterable, List, Sequence, Tuple
from pywikibot.tools import chars


class Hunk:

    """One change hunk between a and b.

    .. note:: parts of this code are taken from by
       `difflib.get_grouped_opcodes()`.

    """

    APPR = 1
    NOT_APPR = -1
    PENDING = 0

    def __init__(self, a: Union[str, Sequence[str]],
                 b: Union[str, Sequence[str]],
                 grouped_opcode: Sequence[Tuple[str, int, int, int, int]]
                 ) -> None:
        """
        Initializer.

        :param a: sequence of lines
        :param b: sequence of lines
        :param grouped_opcode: list of 5-tuples describing how to turn a into
            b. It has the same format as returned by difflib.get_opcodes().
        """
        self.a = a
        self.b = b
        self.group = grouped_opcode
        self.header = ''
        self.colors = {
            '+': 'lightgreen',
            '-': 'lightred',
        }
        self.bg_colors = {
            '+': 'lightgreen',
            '-': 'lightred',
        }

        self.diff = list(self.create_diff())
        self.diff_plain_text = ''.join(self.diff)
        self.diff_text = ''.join(self.format_diff())

        first, last = self.group[0], self.group[-1]
        self.a_rng = (first[1], last[2])
        self.b_rng = (first[3], last[4])

        self.header = self.get_header()
        self.diff_plain_text = '{hunk.header}\n{hunk.diff_plain_text}' \
                               .format(hunk=self)
        self.diff_text = str(self.diff_text)

        self.reviewed = self.PENDING

        self.pre_context = 0
        self.post_context = 0

    def get_header(self) -> str:
        """Provide header of unified diff."""
        return self.get_header_text(self.a_rng, self.b_rng) + '\n'

    @staticmethod
    def get_header_text(a_rng: Tuple[int, int], b_rng: Tuple[int, int],
                        affix: str = '@@') -> str:
        """Provide header for any ranges."""
        a_rng = _format_range_unified(*a_rng)
        b_rng = _format_range_unified(*b_rng)
        return '{0} -{1} +{2} {0}'.format(affix, a_rng, b_rng)

    def create_diff(self) -> Iterable[str]:
        """Generator of diff text for this hunk, without formatting.

        Check each line ends with line feed to prevent behaviour like
        :bug:`2142`
        """
        def check_line(line: str) -> str:
            r"""Make sure each line ends with '\n'."""
            return line if line.endswith('\n') else line + '\n'

        for tag, i1, i2, j1, j2 in self.group:
            # equal/delete/insert add additional space after the sign as it's
            # what difflib.ndiff does do too.
            if tag == 'equal':
                for line in self.a[i1:i2]:
                    yield '  ' + check_line(line)
            elif tag == 'delete':
                for line in self.a[i1:i2]:
                    yield '- ' + check_line(line)
            elif tag == 'insert':
                for line in self.b[j1:j2]:
                    yield '+ ' + check_line(line)
            elif tag == 'replace':
                for line in difflib.ndiff(self.a[i1:i2], self.b[j1:j2]):
                    yield check_line(line)

    def format_diff(self) -> Iterable[str]:
        """Color diff lines."""
        diff = iter(self.diff)

        fmt: Optional[str] = ''
        line1, line2 = '', next(diff)
        for line in diff:
            fmt, line1, line2 = line1, line2, line
            # do not show lines starting with '?'.
            if line1.startswith('?'):
                continue
            if line2.startswith('?'):
                yield self.color_line(line1, line2)
                # do not try to reuse line2 as format at next iteration
                # if already used for an added line.
                if line1.startswith('+'):
                    line2 = ''
                continue
            if line1.startswith('-'):
                # Color whole line to be removed.
                yield self.color_line(line1)
            elif line1.startswith('+'):
                # Reuse last available fmt as diff line, if possible,
                # or color whole line to be added.
                fmt = fmt if fmt.startswith('?') else ''
                fmt = fmt[:min(len(fmt), len(line1))]
                fmt = fmt if fmt else None
                yield self.color_line(line1, fmt)

        # handle last line
        # If line line2 is removed, color the whole line.
        # If line line2 is added, check if line1 is a '?-type' line, to prevent
        # the entire line line2 to be colored (see T130572).
        # The case where line2 start with '?' has been covered already.
        if line2.startswith('-'):
            # Color whole line to be removed.
            yield self.color_line(line2)
        elif line2.startswith('+'):
            # Reuse last available line1 as diff line, if possible,
            # or color whole line to be added.
            fmt = line1 if line1.startswith('?') else ''
            fmt = fmt[:min(len(fmt), len(line2))]
            fmt = fmt if fmt else None
            yield self.color_line(line2, fmt)

    def color_line(self, line: str, line_ref: Optional[str] = None) -> str:
        """Color line characters.

        If line_ref is None, the whole line is colored.
        If line_ref[i] is not blank, line[i] is colored.
        Color depends if line starts with +/-.

        line_ref: string.
        """
        color = line[0]

        if line_ref is None:
            if color in self.colors:
                colored_line = '<<{color}>>{}<<default>>'.format(
                    line, color=self.colors[color])
                return colored_line
            return line

        colored_line = ''
        color_closed = True
        for char, char_ref in zip_longest(
            line, line_ref.strip(), fillvalue=' '
        ):
            char_tagged = char
            if color_closed:
                if char_ref != ' ':
                    if char != ' ':
                        apply_color = self.colors[color]
                    else:
                        apply_color = 'default;' + self.bg_colors[color]
                    char_tagged = '<<{color}>>{}'.format(char,
                                                         color=apply_color)
                    color_closed = False
            else:
                if char_ref == ' ':
                    char_tagged = f'<<default>>{char}'
                    color_closed = True
            colored_line += char_tagged

        if not color_closed:
            colored_line += '<<default>>'

        return colored_line

    def apply(self) -> Sequence[str]:
        """Turn a into b for this hunk."""
        return self.b[self.b_rng[0]:self.b_rng[1]]

    def __str__(self) -> str:
        """Return the diff as plain text."""
        return ''.join(self.diff_plain_text)

    def __repr__(self) -> str:
        """Return a reconstructable representation."""
        # TODO
        return f'{self.__class__.__name__}(a, b, {self.group})'


class _SuperHunk(abc.Sequence):

    def __init__(self, hunks: Sequence[Hunk]) -> None:
        self._hunks = hunks
        self.a_rng = (self._hunks[0].a_rng[0], self._hunks[-1].a_rng[1])
        self.b_rng = (self._hunks[0].b_rng[0], self._hunks[-1].b_rng[1])
        self.pre_context = self._hunks[0].pre_context
        self.post_context = self._hunks[0].post_context

    def __getitem__(self, idx: int) -> Hunk:  # type: ignore[override]
        return self._hunks[idx]

    def __len__(self) -> int:
        return len(self._hunks)

    def split(self) -> List['_SuperHunk']:
        return [_SuperHunk([hunk]) for hunk in self._hunks]

    @property
    def reviewed(self) -> int:
        assert len({hunk.reviewed for hunk in self._hunks}) == 1, \
            'All hunks should have the same review status'
        return self._hunks[0].reviewed

    @reviewed.setter
    def reviewed(self, reviewed: int) -> None:
        for hunk in self._hunks:
            hunk.reviewed = reviewed


class PatchManager:

    """Apply patches to text_a to obtain a new text.

    If all hunks are approved, text_b will be obtained.
    """

    def __init__(self, text_a: str, text_b: str, context: int = 0,
                 by_letter: bool = False,
                 replace_invisible: bool = False) -> None:
        """Initializer.

        :param text_a: base text
        :param text_b: target text
        :param context: number of lines which are context
        :param by_letter: if text_a and text_b are single lines, comparison can
            be done letter by letter.
        :param replace_invisible: Replace invisible characters like U+200e with
            the charnumber in brackets (e.g. <200e>).
        """
        self.a: Union[str, List[str]] = text_a.splitlines(True)
        self.b: Union[str, List[str]] = text_b.splitlines(True)
        if by_letter and len(self.a) <= 1 and len(self.b) <= 1:
            self.a = text_a
            self.b = text_b

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
        self._replace_invisible = replace_invisible

    def get_blocks(self) -> List[Tuple[int, Tuple[int, int], Tuple[int, int]]]:
        """Return list with blocks of indexes.

        Format of each block::

            [-1, (i1, i2), (-1, -1)] -> block a[i1:i2] does not change from
                a to b then is there is no corresponding hunk.
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

    def print_hunks(self) -> None:
        """Print the headers and diff texts of all hunks to the output."""
        if self.hunks:
            pywikibot.info('\n'.join(self._generate_diff(super_hunk)
                                     for super_hunk in self._super_hunks))

    def _generate_super_hunks(self, hunks: Optional[Iterable[Hunk]] = None
                              ) -> List[_SuperHunk]:
        if hunks is None:
            hunks = self.hunks

        if not hunks:
            return []

        if self.context:
            # Determine if two hunks are connected by self.context
            super_hunk: List[Hunk] = []
            super_hunks = [super_hunk]
            for hunk in hunks:
                # self.context * 2, because if self.context is 2 the hunks
                # would be directly adjacent when 4 lines in between and for
                # anything below 4 they share lines.
                # not super_hunk == first hunk as any other super_hunk is
                # created with one hunk
                if (not super_hunk or hunk.pre_context <= self.context * 2):
                    # previous hunk has shared/adjacent self.context lines
                    super_hunk += [hunk]
                else:
                    super_hunk = [hunk]
                    super_hunks += [super_hunk]
        else:
            super_hunks = [[hunk] for hunk in hunks]
        return [_SuperHunk(sh) for sh in super_hunks]

    def _get_context_range(self, super_hunk: _SuperHunk
                           ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Dynamically determine context range for a super hunk."""
        a0, a1 = super_hunk.a_rng
        b0, b1 = super_hunk.b_rng
        return ((a0 - min(super_hunk.pre_context, self.context),
                 a1 + min(super_hunk.post_context, self.context)),
                (b0 - min(super_hunk.pre_context, self.context),
                 b1 + min(super_hunk.post_context, self.context)))

    def _generate_diff(self, hunks: _SuperHunk) -> str:
        """Generate a diff text for the given hunks."""
        def extend_context(start: int, end: int) -> str:
            """Add context lines."""
            return ''.join(f'  {line.rstrip()}\n'
                           for line in self.a[start:end])

        context_range = self._get_context_range(hunks)

        output = '<<aqua>>{}<<default>>\n{}'.format(
            Hunk.get_header_text(*context_range),
            extend_context(context_range[0][0], hunks[0].a_rng[0]))
        previous_hunk = None
        for hunk in hunks:
            if previous_hunk:
                output += extend_context(previous_hunk.a_rng[1], hunk.a_rng[0])
            previous_hunk = hunk
            output += hunk.diff_text
        output += extend_context(hunks[-1].a_rng[1], context_range[0][1])
        if self._replace_invisible:
            output = chars.replace_invisible(output)
        return output

    def review_hunks(self) -> None:
        """Review hunks."""
        def find_pending(start: int, end: int) -> Optional[int]:
            step = -1 if start > end else +1
            for pending in range(start, end, step):
                if super_hunks[pending].reviewed == Hunk.PENDING:
                    return pending
            return None

        # TODO: Missing commands (compared to git --patch): edit and search
        help_msg = {'y': 'accept this hunk',
                    'n': 'do not accept this hunk',
                    'q': 'do not accept this hunk and quit reviewing',
                    'a': 'accept this hunk and all other pending',
                    'd': 'do not apply this hunk or any of the later hunks in '
                         'the file',
                    'g': 'select a hunk to go to',
                    'j': 'leave this hunk undecided, see next undecided hunk',
                    'J': 'leave this hunk undecided, see next hunk',
                    'k': 'leave this hunk undecided, see previous undecided '
                         'hunk',
                    'K': 'leave this hunk undecided, see previous hunk',
                    's': 'split this hunk into smaller ones',
                    '?': 'help',
                    }

        super_hunks = self._generate_super_hunks(
            h for h in self.hunks if h.reviewed == Hunk.PENDING)
        position: Optional[int] = 0

        while any(any(hunk.reviewed == Hunk.PENDING for hunk in super_hunk)
                  for super_hunk in super_hunks):

            assert position is not None
            super_hunk = super_hunks[position]

            next_pending = find_pending(position + 1, len(super_hunks))
            prev_pending = find_pending(position - 1, -1)

            answers = ['y', 'n', 'q', 'a', 'd', 'g']
            if next_pending is not None:
                answers += ['j']
            if position < len(super_hunks) - 1:
                answers += ['J']
            if prev_pending is not None:
                answers += ['k']
            if position > 0:
                answers += ['K']
            if len(super_hunk) > 1:
                answers += ['s']
            answers += ['?']

            pywikibot.info(self._generate_diff(super_hunk))
            choice = pywikibot.input('Accept this hunk [{}]?'.format(
                ','.join(answers)))
            if choice not in answers:
                choice = '?'

            if choice in ['y', 'n']:
                super_hunk.reviewed = \
                    Hunk.APPR if choice == 'y' else Hunk.NOT_APPR
                if next_pending is not None:
                    position = next_pending
                else:
                    position = find_pending(0, position)
            elif choice == 'q':
                for super_hunk in super_hunks:
                    for hunk in super_hunk:
                        if hunk.reviewed == Hunk.PENDING:
                            hunk.reviewed = Hunk.NOT_APPR
            elif choice in ['a', 'd']:
                for super_hunk in super_hunks[position:]:
                    for hunk in super_hunk:
                        if hunk.reviewed == Hunk.PENDING:
                            hunk.reviewed = \
                                Hunk.APPR if choice == 'a' else Hunk.NOT_APPR
                position = find_pending(0, position)
            elif choice == 'g':
                hunk_list = []
                rng_width = 18
                for index, super_hunk in enumerate(super_hunks, start=1):
                    assert -1 <= super_hunk.reviewed <= 1, \
                        "The super hunk's review status is unknown."
                    status = ' +-'[super_hunk.reviewed]

                    if super_hunk[0].a_rng[1] - super_hunk[0].a_rng[0] > 0:
                        mode = '-'
                        first = self.a[super_hunk[0].a_rng[0]]
                    else:
                        mode = '+'
                        first = self.b[super_hunk[0].b_rng[0]]
                    hunk_list += [(status, index,
                                   Hunk.get_header_text(
                                       *self._get_context_range(super_hunk),
                                       affix=''),
                                   mode, first)]
                    rng_width = max(len(hunk_list[-1][2]), rng_width)
                line_template = ('{0}{1} {2: >'
                                 + str(int(math.log10(len(super_hunks)) + 1))
                                 + '}: {3: <' + str(rng_width) + '} {4}{5}')
                # the last entry is the first changed line which usually ends
                # with a \n (only the last may not, which is covered by the
                # if-condition following this block)
                hunk_list_str = ''.join(
                    line_template.format(
                        '*' if hunk_entry[1] == position + 1 else
                        ' ', *hunk_entry)
                    for hunk_entry in hunk_list)
                if hunk_list_str.endswith('\n'):
                    hunk_list_str = hunk_list_str[:-1]
                pywikibot.info(hunk_list_str)
                next_hunk = pywikibot.input('Go to which hunk?')
                try:
                    next_hunk_position = int(next_hunk) - 1
                except ValueError:
                    next_hunk_position = False
                if (next_hunk_position is not False
                        and 0 <= next_hunk_position < len(super_hunks)):
                    position = next_hunk_position
                elif next_hunk:  # nothing entered is silently ignored
                    pywikibot.error(
                        f'Invalid hunk number "{next_hunk}"')
            elif choice == 'j':
                assert next_pending is not None
                position = next_pending
            elif choice == 'J':
                position += 1
            elif choice == 'k':
                assert prev_pending is not None
                position = prev_pending
            elif choice == 'K':
                position -= 1
            elif choice == 's':
                super_hunks = (super_hunks[:position]
                               + super_hunks[position].split()
                               + super_hunks[position + 1:])
                pywikibot.info(
                    f'Split into {len(super_hunk._hunks)} hunks')
            else:  # choice == '?':
                pywikibot.info(
                    '<<purple>>{}<<default>>'.format('\n'.join(
                        f'{answer} -> {help_msg[answer]}'
                        for answer in answers)))

    def apply(self) -> List[str]:
        """Apply changes. If there are undecided changes, ask to review."""
        if any(h.reviewed == h.PENDING for h in self.hunks):
            pywikibot.info('There are unreviewed hunks.\n'
                           'Please review them before proceeding.\n')
            self.review_hunks()

        l_text: List[str] = []
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
            assert ''.join(l_text) == ''.join(self.b)
        return l_text


def cherry_pick(oldtext: str, newtext: str, n: int = 0,
                by_letter: bool = False) -> str:
    """Propose a list of changes for approval.

    Text with approved changes will be returned.
    n: int, line of context as defined in difflib.get_grouped_opcodes().
    by_letter: if text_a and text_b are single lines, comparison can be done

    """
    template = '{2}<<lightpurple>>{0:{1}^50}<<default>>{2}'

    patch = PatchManager(oldtext, newtext, context=n, by_letter=by_letter)
    pywikibot.info(template.format('  ALL CHANGES  ', '*', '\n'))

    for hunk in patch.hunks:
        pywikibot.info(hunk.diff_text)
    pywikibot.info(template.format('  REVIEW CHANGES  ', '*', '\n'))

    text_list = patch.apply()
    pywikibot.info(template.format('  APPROVED CHANGES  ', '*', '\n'))

    if any(hunk.reviewed == hunk.APPR for hunk in patch.hunks):
        for hunk in patch.hunks:
            if hunk.reviewed == hunk.APPR:
                pywikibot.info(hunk.diff_text)
    else:
        pywikibot.info(template.format('None.', '', ''))

    return ''.join(text_list)


def html_comparator(compare_string: str) -> Dict[str, List[str]]:
    """List of added and deleted contexts from 'action=compare' html string.

    This function is useful when combineds with site.py's "compare" method.
    Site.compare() returns HTML that is useful for displaying on a page.
    Here we use BeautifulSoup to get the un-HTML-ify the context of changes.
    Finally we present the added and deleted contexts.
    :param compare_string: HTML string from MediaWiki API
    :return: deleted and added list of contexts
    """
    from bs4 import BeautifulSoup

    comparands: Dict[str, List[str]] = {'deleted-context': [],
                                        'added-context': []}
    soup = BeautifulSoup(compare_string, 'html.parser')
    for change_type, css_class in (('deleted-context', 'diff-deletedline'),
                                   ('added-context', 'diff-addedline')):
        crutons = soup.find_all('td', class_=css_class)
        for cruton in crutons:
            cruton_string = ''.join(cruton.strings)
            comparands[change_type].append(cruton_string)
    return comparands
