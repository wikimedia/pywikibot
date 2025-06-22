#!/usr/bin/env python
"""Pre-commit hook to set the leftmost copyright year."""
#
# (C) Pywikibot team, 2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path


PATTERN = re.compile(
    r'(?m)^(# \([Cc©]\) Pywikibot [Tt]eam, 20\d{2})(-20\d{2})?$'
)


def get_patched_files():
    """Return the PatchSet for the latest commit."""
    out = subprocess.run(['git', 'diff', '--unified=0'],
                         stdout=subprocess.PIPE,
                         check=True, encoding='utf-8', text=True).stdout
    return {Path(path) for path in re.findall(r'(?m)^\+\+\+ b/(.+)$', out)
            if path.endswith('.py')}


def check_file(path: Path, year: int, files: set(Path)) -> bool:
    """Check for copyright string and fix it if necessary.

    Update copyright string for changed files.
    """
    text = path.read_text(encoding='utf-8')
    if len(text) < 100:
        return True

    m = PATTERN.search(text)
    if not m:
        return False

    if path in files and not m[0].endswith(str(year)):
        text = PATTERN.sub(f'{m[1]}-{year}', text)
        path.write_text(text, encoding='utf-8')
        print(f'Fixing copyright in {path}')  # noqa: T201

    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Test that test filenames contains a valid copyright."""
    failed = False
    year = date.today().year
    files = get_patched_files()

    for filename in sys.argv[1:]:
        path = Path(filename)

        if not check_file(path, year, files):
            print(f'Missing or invalid copyright in: {path}')  # noqa: T201
            failed = True

    return (0, 1)[failed]


if __name__ == '__main__':
    sys.exit(main(sys.argv))
