"""Family module for Meta Wiki."""
#
# (C) Pywikibot team, 2005-2026
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


class Family(family.WikimediaFamily):

    """Family class for Meta Wiki.

    .. versionchanged:: 11.0
       beta site code was added.
    """

    name = 'meta'

    langs = {
        'meta': 'meta.wikimedia.org',
        'beta': 'meta.wikimedia.beta.wmcloud.org',
    }
    # Sites we want to edit but not count as real languages
    test_codes = ['beta']
    interwiki_forward = 'wikipedia'
    cross_allowed = ['meta']

    # Templates that indicate a category redirect
    # Redirects to these templates are automatically included
    category_redirect_templates = {
        '_default': (
            'Category redirect',
        ),
    }

    # Subpages for documentation.
    doc_subpages = {
        '_default': (('/doc',), ['meta']),
    }
