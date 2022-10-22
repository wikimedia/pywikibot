"""pwb caller script to invoke the :mod:`pywikibot.scripts.wrapper` script.

.. versionadded:: 8.0
"""
#
# (C) Pywikibot team, 2022
#
# Distributed under the terms of the MIT license.
#
import sys

from pywikibot.scripts.wrapper import main

if __name__ == '__main__':
    sys.exit(main())
