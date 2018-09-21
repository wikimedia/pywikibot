# -*- coding: utf-8 -*-
"""Family module for Meta Wiki."""
#
# (C) Pywikibot team, 2005-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family


# The meta wikimedia family
class Family(family.WikimediaOrgFamily):

    """Family class for Meta Wiki."""

    name = 'meta'

    interwiki_forward = 'wikipedia'
    cross_allowed = ['meta', ]

    category_redirect_templates = {
        'meta': (
            'Category redirect',
        ),
    }

    # Subpages for documentation.
    doc_subpages = {
        '_default': (('/doc',), ['meta']),
    }
