"""Family module for Wikimedia Commons."""
#
# (C) Pywikibot team, 2005-2023
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


class Family(family.WikimediaFamily, family.DefaultWikibaseFamily):

    """Family class for Wikimedia Commons.

    .. versionchanged:: 6.5
       :meth:`family.WikibaseFamily.interface` was changed  to
       :class:`DataSite<pywikibot.site._datasite.DataSite>` to enable
       structured data.
    """

    name = 'commons'

    langs = {
        'commons': 'commons.wikimedia.org',
        'test': 'test-commons.wikimedia.org',
        'beta': 'commons.wikimedia.beta.wmflabs.org'
    }

    # Sites we want to edit but not count as real languages
    test_codes = ['test', 'beta']

    interwiki_forward = 'wikipedia'

    # Templates that indicate a category redirect
    # Redirects to these templates are automatically included
    category_redirect_templates = {
        '_default': (
            'Category redirect',
            'Synonym taxon category redirect',
            'Invalid taxon category redirect',
            'Monotypic taxon category redirect',
            'Endashcatredirect',
        ),
    }

    # Subpages for documentation.
    doc_subpages = {
        '_default': (('/doc', ), ['commons']),
    }

    def entity_sources(self, code):
        if code == 'commons':
            return {
                'item': ('wikidata', 'wikidata'),
                'property': ('wikidata', 'wikidata'),
            }
        if code in ('test', 'beta'):
            return {
                'item': (code, 'wikidata'),
                'property': (code, 'wikidata'),
            }

        return {}  # default
