#!/usr/bin/env python3
"""Script that forms part of pwb_tests."""
#
# (C) Pywikibot team, 2013-2022
#
# Distributed under the terms of the MIT license.
#
import os.path


def main() -> None:
    """Print locals()."""
    for k, v in sorted(locals().copy().items()):
        # Skip a few items that Python 3 adds and are not emulated in pwb.
        if k in ['__cached__', '__loader__', '__spec__', '__annotations__']:
            continue
        if k == '__file__':
            print('__file__: ' + os.path.join('.', os.path.relpath(__file__)))
        else:
            print(f'{k}: {v}')


if __name__ == '__main__':
    main()
