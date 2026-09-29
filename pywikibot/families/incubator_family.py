#
# (C) Pywikibot team, 2006-2026
#
# Distributed under the terms of the MIT license.
#
"""Family module for Incubator Wiki."""
from __future__ import annotations

from pywikibot import family


# The Wikimedia Incubator family
class Family(family.WikimediaFamily):

    """Family class for Incubator Wiki.

    .. version-changed:: 11.8
       beta site code was added.
    """

    name = 'incubator'

    langs = {
        'incubator': 'incubator.wikimedia.org',
        'beta': 'incubator.wikimedia.beta.wmcloud.org',
    }

    test_codes = ['beta']
    interwiki_forward = 'wikipedia'
