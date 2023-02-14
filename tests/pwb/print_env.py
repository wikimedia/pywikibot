#!/usr/bin/env python3
"""Script that forms part of pwb_tests."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import os
import sys

from pywikibot.tools import first_upper


def main() -> None:
    """Print environment variables."""
    _pwb_dir = os.path.abspath(os.path.join(
        os.path.split(__file__)[0], '..', '..'))
    _pwb_dir = first_upper(_pwb_dir)

    print('os.environ:')
    for k, v in sorted(os.environ.items()):
        # Don't leak the password into logs
        if k == 'USER_PASSWORD':
            continue
        # This only appears in subprocesses
        if k == 'PYWIKIBOT_DIR_PWB':
            continue
        print(f'{k}: {v}')

    print('sys.path:')
    for path in sys.path:
        if path == '' or path.startswith('.'):
            continue
        # Normalise DOS drive letter
        path = first_upper(path)
        if path.startswith(_pwb_dir):
            continue
        print(path)


if __name__ == '__main__':
    main()
