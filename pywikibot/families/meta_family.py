"""Family module for Meta Wiki."""
#
# (C) Pywikibot team, 2005-2020
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Wikimedia Meta-Wiki family
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
