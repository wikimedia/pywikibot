#!/usr/bin/env python3
#
# (C) Pywikibot team, 2022-2026
#
# Distributed under the terms of the MIT license.
#
"""PWB caller script to invoke the :mod:`pywikibot.scripts.wrapper` script.

.. version-added:: 8.0
"""
import runpy
import sys


VERSIONS_REQUIRED_MESSAGE = """
Pywikibot is not available on:
{version}

This version of Pywikibot only supports Python 3.9+.
"""

DEPRECATED_PYTHON_MESSAGE = """

Python {version} will be dropped soon with Pywikibot 12.
It is recommended to use Python 3.10 or above.
See phab:T423572 for further information.
"""


def python_is_supported():
    """Check that Python is supported."""
    return sys.version_info[:3] >= (3, 9)


def python_is_deprecated():
    """Check that Python is deprecated."""
    return sys.version_info[:3] < (3, 10)


if not python_is_supported():  # pragma: no cover
    sys.exit(VERSIONS_REQUIRED_MESSAGE.format(version=sys.version))


def main() -> None:
    """Entry point for :func:`tests.utils.execute_pwb`."""
    from pathlib import Path
    path = Path(__file__).parent / 'pywikibot' / 'scripts' / 'wrapper.py'
    runpy.run_path(str(path), run_name='__main__')


if python_is_deprecated():
    import warnings
    msg = DEPRECATED_PYTHON_MESSAGE.format(
        version=sys.version.split(maxsplit=1)[0])
    warnings.warn(msg, FutureWarning)  # adjust this line no in utils.execute()
    del warnings


if __name__ == '__main__':
    sys.exit(main())
