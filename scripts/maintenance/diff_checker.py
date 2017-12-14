#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Check that the latest commit diff follows the guidelines.

Currently the script only checks line lengths. Lines longer than 79 characters
should be avoided.
See [[Manual:Pywikibot/Development/Guidelines]] for more info.

Todo: The following rules can be added in the future:
    - For any changes or new lines use single quotes for strings, or double
        quotes  if the string contains a single quote. But keep older code
        unchanged.
    - Do not use a u'' prefix on strings, as it is meaningless due to
        __future__.unicode_literals. But keep older code unchanged.

"""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#

from __future__ import absolute_import, unicode_literals

from re import compile as re_compile
from subprocess import check_output

from unidiff import PatchSet


IGNORABLE_LONG_LINE = re_compile(r'^\s*(# )?<?https?://\S+>?$').search


def get_latest_patchset():
    """Return the PatchSet for the latest commit."""
    # regex from https://github.com/PyCQA/pylint/blob/master/pylintrc
    output = check_output(
        ['git', 'diff', '-U0', '@~..@'], universal_newlines=True)
    return PatchSet.from_string(output)


def check_line_lengths(latest_patchset):
    """Check that none of the added/modified lines are longer than 79 chars.

    @return: True if line lengths are OK. False otherwise.
    @rtype: bool
    """
    found_long = False
    for patched_file in latest_patchset:
        target_file = patched_file.target_file
        if not (target_file.endswith('.py') or patched_file.is_removed_file):
            continue
        for hunk in patched_file:
            for line in hunk:
                if (
                    line.is_added and len(line.value) > 80
                    and not IGNORABLE_LONG_LINE(line.value)
                ):
                    print(
                        target_file + ':' + str(line.target_line_no) + ':'
                        + str(len(line.value))
                        + ': line is too long (more than 79 characters)'
                    )
                    found_long = True
    return not found_long


def main():
    """Run this script."""
    latest_patchset = get_latest_patchset()
    if not check_line_lengths(latest_patchset):
        raise SystemExit('diff-checker failed')


if __name__ == '__main__':
    main()
