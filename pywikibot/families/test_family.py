# -*- coding: utf-8 -*-
"""Family module for test.wikipedia.org."""
#
# (C) Pywikibot team, 2007-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot.families.wikipedia_family import Family
from pywikibot.tools import issue_deprecation_warning

issue_deprecation_warning(
    'test_family', 'wikipedia_family', since='20190718')
# Also remove the ``if fam == 'test':`` condition in pywikibot.__init__
# whenever this module is removed.


class Family(Family):

    """Family class for test.wikipedia.org."""

    name = 'test'
