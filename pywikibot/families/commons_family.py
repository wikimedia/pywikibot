# -*- coding: utf-8 -*-
"""Family module for Wikimedia Commons."""
#
# (C) Pywikibot team, 2005-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The Wikimedia Commons family
class Family(family.WikimediaFamily):

    """Family class for Wikimedia Commons."""

    name = 'commons'

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()

        self.langs = {
            'commons': 'commons.wikimedia.org',
            'beta': 'commons.wikimedia.beta.wmflabs.org'
        }

        self.interwiki_forward = 'wikipedia'

        # Templates that indicate a category redirect
        # Redirects to these templates are automatically included
        self.category_redirect_templates = {
            '_default': (
                u'Category redirect',
                u'Synonym taxon category redirect',
                u'Invalid taxon category redirect',
                u'Monotypic taxon category redirect',
                'Endashcatredirect',
            ),
        }

        # Subpages for documentation.
        self.doc_subpages = {
            '_default': ((u'/doc', ), ['commons']),
        }
