"""Family module for OpenStreetMap wiki."""
#
# (C) Pywikibot team, 2009-2023
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


# The project wiki of OpenStreetMap (OSM).
class Family(family.SingleSiteFamily):

    """Family class for OpenStreetMap wiki."""

    name = 'osm'
    domain = 'wiki.openstreetmap.org'
    code = 'en'

    # Templates that indicate a category redirect
    # Redirects to these templates are automatically included
    category_redirect_templates = {
        'en': ('Category redirect',),
    }

    # A list of disambiguation template names in different languages
    disambiguationTemplates = {  # noqa: N815
        'en': ('Disambig',),
    }

    # A dict with the name of the category containing disambiguation
    # pages for the various languages. Only one category per language,
    # and without the namespace
    disambcatname = {
        'en': 'Disambiguation',
    }

    # Subpages for documentation
    doc_subpages = {
        'en': ('/doc',),
    }

    # Templates that indicate an edit should be avoided
    edit_restricted_templates = {
        'en': ('In Bearbeitung',),
    }
