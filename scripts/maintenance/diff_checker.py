#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Check that the latest commit diff follows the guidelines.

Currently the script checks the following code style issues:
    - Line lengths: Newly added lines longer than 79 chars are not allowed.
    - Unicode literal notations: They are not allowed since we instead import
        unicode_literals from __future__.
    - Any added double quoted string should contain a single quote.

See [[Manual:Pywikibot/Development/Guidelines]] for more info.

Todo: The following rules can be added in the future:
    - For any changes or new lines use single quotes for strings, or double
        quotes  if the string contains a single quote. But keep older code
        unchanged. (partially implemented)
    - Prefer string.format() instead of modulo operator % for string
        formatting. The modulo operator might be deprecated by a future
        python release.
"""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#

from __future__ import absolute_import, unicode_literals

from re import compile as re_compile, IGNORECASE
from subprocess import check_output
from sys import version_info

from unidiff import PatchSet

if version_info.major == 3:
    PY2 = False
    from tokenize import tokenize, STRING
else:
    PY2 = True
    from tokenize import generate_tokens as tokenize, STRING


# Regexp for a line that is allowed to be longer than the limit.
# It does not make sense to break long URLs.
# https://github.com/PyCQA/pylint/blob/d42e74bb9428f895f36808d30bd8a1fe31e28f63/pylintrc#L145
IGNORABLE_LONG_LINE = re_compile(r'\s*(# )?<?https?://\S+>?$').match

STRING_MATCH = re_compile(
    r'(?P<unicode_literal>u)?[bfr]*(?P<quote>\'+|"+)', IGNORECASE,
).match


def get_latest_patchset():
    """Return the PatchSet for the latest commit."""
    # regex from https://github.com/PyCQA/pylint/blob/master/pylintrc
    output = check_output(
        ['git', 'diff', '-U0', '@~..@'])
    return PatchSet.from_string(
        output.replace(b'\r\n', b'\n'), encoding='utf-8')


def print_error(path, line_no, col_no, error):
    """Print the error."""
    print('{0}:{1}:{2}: {3}'.format(path, line_no, col_no, error))


def check_tokens(file_path, line_nos):
    """Check the style of lines in the given file_path."""
    error = False
    max_line = max(line_nos)
    with open(file_path, 'rb') as f:
        token_generator = tokenize(f.readline)
        for type_, string, start, end, line_val in token_generator:
            if max_line < start[0]:
                break
            if start[0] not in line_nos or type_ != STRING:
                continue
            if PY2:
                string = string.decode('utf-8')
            match = STRING_MATCH(string)
            if match.group('unicode_literal'):
                error = True
                print_error(
                    file_path, start[0], start[1] + 1,
                    'newly-added/modified line with u"" prefixed string '
                    'literal',
                )
            if match.group('quote') == '"' and "'" not in string:
                error = True
                print_error(
                    file_path, start[0], start[1] + 1,
                    'newly-added/modified line with "double quoted string" not'
                    ' containing any single quotes; use a \'single quoted '
                    'string\' instead',
                )
    return not error


def check(latest_patchset):
    """Check that the added/modified lines do not violate the guideline.

    @return: True if line added/modified OK. False otherwise.
    @rtype: bool
    """
    error = False
    for patched_file in latest_patchset:
        path = patched_file.path
        if not (path.endswith('.py') or patched_file.is_removed_file):
            continue
        added_lines = set()
        for hunk in patched_file:
            for line in hunk:
                if not line.is_added:
                    continue
                line_no = line.target_line_no
                added_lines.add(line_no)
                line_val = line.value
                # Check line length
                if len(line_val) > 80 and not IGNORABLE_LONG_LINE(line_val):
                    print_error(
                        path, line_no, len(line_val),
                        'newly-added/modified line longer than 79 characters',
                    )
                    error = True
        if added_lines:
            error = not check_tokens(path, added_lines) or error
    return not error


def main():
    """Run this script."""
    latest_patchset = get_latest_patchset()
    if not check(latest_patchset):
        raise SystemExit(
            'diff-checker failed.\n'
            'Please review '
            '<https://www.mediawiki.org/wiki/'
            'Manual:Pywikibot/Development/Guidelines#Miscellaneous> '
            'and update your patch-set accordingly.'
        )


if __name__ == '__main__':
    main()
