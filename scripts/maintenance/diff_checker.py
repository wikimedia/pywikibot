#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Check that the latest commit diff follows the guidelines.

Currently the script checks the following code style issues:
    - Line lengths: Newly added lines longer than 79 chars are not allowed.
    - Unicode literal notations: They are not allowed since we instead import
        unicode_literals from __future__.
    - Single-quoted strings are preferred, but when a string contains single
      quote characters, use double quotes to avoid backslashes in the string.

See [[Manual:Pywikibot/Development/Guidelines]] for more info.

Todo: The following rules can be added in the future:
    - Prefer string.format() instead of modulo operator % for string
        formatting. The modulo operator might be deprecated by a future
        python release.
"""
#
# (C) Pywikibot team, 2017-2018
#
# Distributed under the terms of the MIT license.
#

from __future__ import absolute_import, division, unicode_literals

from re import compile as re_compile, IGNORECASE
from subprocess import check_output
from sys import version_info

from unidiff import PatchSet

from pywikibot import __url__

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
    r'(?P<prefix>[bfru]*)?(?P<quote>\'+|"+)', IGNORECASE,
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


def check_quotes(match, file_path, start):
    """Check string quotes and return True if there are no errors."""
    string = match.string
    quote = match.group('quote')
    if quote == '"':
        if "'" not in string:
            print_error(
                file_path, start[0], start[1] + 1,
                "use 'single-quoted' strings "
                '(unless the string contains single quote characters)')
            return False
    elif quote == "'":
        if (
            'r' not in match.group('prefix')
            and string.count(r'\'') - int(string.endswith(r'\''))
            and '"' not in string
        ):
            print_error(
                file_path, start[0], start[1] + 1,
                r'use a "double-quoted" string to avoid \' escape sequence')
            return False
    return True


def check_tokens(file_path, line_nos):
    """Check the style of lines in the given file_path."""
    no_errors = True
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
            if 'u' in match.group('prefix'):
                no_errors = False
                print_error(
                    file_path, start[0], start[1] + 1,
                    'newly-added/modified line with u"" prefixed string '
                    'literal',
                )
            no_errors = check_quotes(match, file_path, start) and no_errors
    return no_errors


def check(latest_patchset):
    """Check that the added/modified lines do not violate the guideline.

    @return: True if there are no error, False otherwise.
    @rtype: bool
    """
    no_errors = True
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
                    no_errors = False
        if added_lines:
            no_errors = check_tokens(path, added_lines) and no_errors
    return no_errors


def main():
    """Run this script."""
    latest_patchset = get_latest_patchset()
    if not check(latest_patchset):
        raise SystemExit(
            'diff-checker failed.\n'
            'Please review <{}/Development/Guidelines#Miscellaneous> '
            'and update your patch-set accordingly.'.format(__url__)
        )


if __name__ == '__main__':
    main()
