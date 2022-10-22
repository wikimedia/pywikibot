"""pwb caller script to invoke the :mod:`pywikibot.scripts.wrapper` script.

.. versionadded:: 8.0
"""
#
# (C) Pywikibot team, 2022
#
# Distributed under the terms of the MIT license.
#
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
    from pywikibot.scripts import wrapper
    wrapper.main()


if __name__ == '__main__':
    sys.exit(main())
