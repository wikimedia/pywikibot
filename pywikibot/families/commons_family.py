"""Family module for Wikimedia Commons."""
#
# (C) Pywikibot team, 2005-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Wikimedia Commons family
class Family(family.WikimediaFamily):

    """Family class for Wikimedia Commons."""

    name = 'commons'

    langs = {
        'commons': 'commons.wikimedia.org',
        'test': 'test-commons.wikimedia.org',
        'beta': 'commons.wikimedia.beta.wmflabs.org'
    }

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

    def interface(self, code) -> str:
        """Return 'DataSite' to enable structured data.

        .. versionadded 6.5
        """
        return 'DataSite'
