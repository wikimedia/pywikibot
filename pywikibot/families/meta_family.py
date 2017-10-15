# -*- coding: utf-8 -*-
"""Family module for Meta Wiki."""
#
# (C) Pywikibot team, 2005-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The meta wikimedia family
class Family(family.WikimediaOrgFamily):

    """Family class for Meta Wiki."""

    name = 'meta'

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()

        self.interwiki_forward = 'wikipedia'
        self.cross_allowed = ['meta', ]

        self.category_redirect_templates = {
            'meta': (
                'Category redirect',
            ),
        }

        # Subpages for documentation.
        self.doc_subpages = {
            '_default': (('/doc',), ['meta']),
        }
