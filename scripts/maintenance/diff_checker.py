#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Check that the latest commit diff follows the guidelines.

Currently the script checks the following code style issues:
    - Line lengths: Newly added lines longer than 79 chars are not allowed.
    - Unicode literal notations: They are not allowed since we instead import
        unicode_literals from __future__.

See [[Manual:Pywikibot/Development/Guidelines]] for more info.

Todo: The following rules can be added in the future:
    - For any changes or new lines use single quotes for strings, or double
        quotes  if the string contains a single quote. But keep older code
        unchanged.
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

from re import compile as re_compile, IGNORECASE, VERBOSE
from subprocess import check_output

from unidiff import PatchSet


# Regexp for a line that is allowed to be longer than the limit.
# It does not make sense to break long URLs.
# https://github.com/PyCQA/pylint/blob/d42e74bb9428f895f36808d30bd8a1fe31e28f63/pylintrc#L145
IGNORABLE_LONG_LINE = re_compile(r'\s*(# )?<?https?://\S+>?$').match
# The U_PREFIX regex cannot be 100% accurate without tokenizing the whole
# module, but thee accuracy of this simple regex should be enough for our
# purposes.
U_PREFIX = re_compile(
    r'''
        (.*?)\b
        (?=
            ur?
            (?=
                ['"]{3}
                |
                # to reduce the false positive possibilities like  's t u',
                # check that the non-triple-quoted strings are closed  on the
                # same line.
                '[^']*'
                |
                "[^"]*"
            )
        )
        (?<!['"])
    ''',
    IGNORECASE | VERBOSE
).match


def get_latest_patchset():
    """Return the PatchSet for the latest commit."""
    # regex from https://github.com/PyCQA/pylint/blob/master/pylintrc
    output = check_output(
        ['git', 'diff', '-U0', '@~..@'], universal_newlines=True)
    return PatchSet.from_string(output)


def print_error(path, line_no, col_no, error):
    """Print the error."""
    print('{0}:{1}:{2}: {3}'.format(path, line_no, col_no, error))


def check(latest_patchset):
    """Check that the added/modified lines do not violate the guideline.

    @return: True if line added/modified OK. False otherwise.
    @rtype: bool
    """
    error = False
    for patched_file in latest_patchset:
        target_file = patched_file.target_file
        if not (target_file.endswith('.py') or patched_file.is_removed_file):
            continue
        for hunk in patched_file:
            for line in hunk:
                if not line.is_added:
                    continue
                line_val = line.value
                # Check line length
                if len(line_val) > 80 and not IGNORABLE_LONG_LINE(line_val):
                    print_error(
                        target_file, line.target_line_no, len(line_val),
                        'newly-added/modified line longer than 79 characters',
                    )
                    error = True
                # Check that u-prefix is not used
                u_match = U_PREFIX(line_val)
                if u_match:
                    print_error(
                        target_file, line.target_line_no, u_match.end() + 1,
                        'newly-added/modified line with u\"" prefixed string '
                        'literal',
                    )
                    error = True
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
