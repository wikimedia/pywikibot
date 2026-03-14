#!/usr/bin/env python3
#
# (C) Pywikibot team, 2018-2026
#
# Distributed under the terms of the MIT license.
#
"""Script that forms part of pwb_tests."""
from __future__ import annotations

import pywikibot


def main() -> None:
    """Print umlauts."""
    pywikibot.info('Häuser')
    print('Häuser')


if __name__ == '__main__':
    main()
