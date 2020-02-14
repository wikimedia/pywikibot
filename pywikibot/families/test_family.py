# -*- coding: utf-8 -*-
"""Family module for test.wikipedia.org."""
#
# (C) Pywikibot team, 2007-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot.families.wikipedia_family import Family  # noqa: F401
from pywikibot.tools import issue_deprecation_warning

issue_deprecation_warning(
    'test_family', 'wikipedia_family', since='20190718',
    warning_class=FutureWarning)
# Also remove the ``if fam == 'test':`` condition in pywikibot.__init__.py
# and `` == 'test':`` condition in tests.family_tests.py
# whenever this module is removed.
