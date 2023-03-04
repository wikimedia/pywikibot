#!/usr/bin/env python3
"""pwb caller script to invoke the :mod:`pywikibot.scripts.wrapper` script.

.. versionadded:: 8.0
"""
#
# (C) Pywikibot team, 2022
#
# Distributed under the terms of the MIT license.
#
import runpy
import sys

VERSIONS_REQUIRED_MESSAGE = """
Pywikibot is not available on:
{version}

This version of Pywikibot only supports Python 3.6.1+.
"""


def python_is_supported():
    """Check that Python is supported."""
    return sys.version_info[:3] >= (3, 6, 1)


if not python_is_supported():  # pragma: no cover
    sys.exit(VERSIONS_REQUIRED_MESSAGE.format(version=sys.version))


def main():
    """Entry point for :func:`tests.utils.execute_pwb`."""
    from pathlib import Path
    path = Path(__file__).parent / 'pywikibot' / 'scripts' / 'wrapper.py'
    runpy.run_path(str(path), run_name='__main__')


if __name__ == '__main__':
    sys.exit(main())
