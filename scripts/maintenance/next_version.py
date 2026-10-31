#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Replace ``next`` in version directives with the release version.

This script allows ``next`` in documentation version directives to
target the upcoming release of the current branch::

    .. version-added:: next
    .. version-changed:: next
    .. version-deprecated:: next
    .. version-removed:: next

.. version-added:: 11.10
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pywikibot


DIRECTIVE_RE = re.compile(
    r'(version-(?:added|changed|removed|deprecated):: )next\b'
)

ROOT = Path(__file__).resolve().parents[2]


def get_version() -> str:
    """Return the current release version."""
    version = pywikibot.__version__
    match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)(.*)', version)
    if not match:
        raise ValueError(f'Invalid version: {version!r}')

    major, minor, patch, suffix = match.groups()
    if int(patch):
        return f'{major}.{minor}.{patch}'

    return f'{major}.{minor}'


def fix_file(path: Path, version: str) -> int:
    """Replace ``next`` in version directives and return the change count."""
    if path == Path(__file__).resolve():  # exclude this script
        return 0

    text = path.read_text(encoding='utf-8')
    updated, count = DIRECTIVE_RE.subn(r'\g<1>' + version, text)

    if count:
        path.write_text(updated, encoding='utf-8')
        pywikibot.info(
            f'Updated {path.relative_to(ROOT)} ({count} replacements)')

    return count


def main(*args: str) -> None:
    """Update version directives throughout the repository."""
    if not args:
        args = sys.argv[1:]
        sys.argv = [sys.argv[0]]

    for arg in args:
        if arg in ('-h', '-help', '--help'):
            pywikibot.show_help()
            return

    version = get_version()

    paths = list(ROOT.glob('*.py'))
    for directory in ('pywikibot', 'tests', 'scripts', 'docs'):
        paths.extend((ROOT / directory).rglob('*.py'))

    total = sum(fix_file(path, version) for path in paths)
    pywikibot.info(f'Updated {total} version directives to {version}.')


if __name__ == '__main__':
    main()
