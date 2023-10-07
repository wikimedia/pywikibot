"""Family module for Wikidata."""
#
# (C) Pywikibot team, 2012-2023
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import config, family


class Family(family.WikimediaFamily, family.DefaultWikibaseFamily):

    """Family class for Wikidata."""

    name = 'wikidata'

    langs = {
        'wikidata': 'www.wikidata.org',
        'test': 'test.wikidata.org',
        'beta': 'wikidata.beta.wmflabs.org',
    }

    # Sites we want to edit but not count as real languages
    test_codes = ['test', 'beta']

    interwiki_forward = 'wikipedia'

    category_redirect_templates = {
        'wikidata': (
            'Category redirect',
        ),
    }

    # Subpages for documentation.
    doc_subpages = {
        '_default': (('/doc', ), ['wikidata']),
    }

    # Disable cosmetic changes
    config.cosmetic_changes_disable.update({
        'wikidata': ('wikidata', 'test', 'beta')
    })
