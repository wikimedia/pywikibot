"""Family module for Wikinews."""
#
# (C) Pywikibot team, 2005-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


# The Wikimedia family that is known as Wikinews
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikinews."""

    name = 'wikinews'

    closed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/closed.dblist
        'bg', 'hu', 'sd', 'th', 'tr',
    ]

    codes = {
        'ar', 'bs', 'ca', 'cs', 'de', 'el', 'en', 'eo', 'es', 'fa', 'fi', 'fr',
        'guw', 'he', 'it', 'ja', 'ko', 'li', 'nl', 'no', 'pl', 'pt', 'ro',
        'ru', 'shn', 'sq', 'sr', 'sv', 'ta', 'uk', 'zh',
    }

    category_redirect_templates = {
        '_default': (),
        'ar': ('تحويل تصنيف',),
        'fa': ('الگو:رده بهتر',),
        'no': ('Kategoriomdirigering',),
        'ro': ('Redirect categorie',),
        'ru': ('Category redirect',),
        'sr': ('Category redirect',),
        'tr': ('Kategori yönlendirme',),
        'zh': ('分类重定向',),
    }

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'ar', 'bs', 'ca', 'cs', 'el', 'en', 'eo', 'fa', 'fi', 'he', 'ja', 'ko',
        'li', 'nl', 'no', 'pl', 'pt', 'ro', 'sq', 'sr', 'sv', 'ta', 'tr', 'uk',
        'zh',
    ]

    # Subpages for documentation.
    # TODO: List is incomplete, to be completed for missing languages.
    doc_subpages = {
        '_default': (('/doc', ),
                     ['en']
                     ),
        'ar': ('/شرح', '/doc'),
        'it': ('/man', ),
        'sr': ('/док', ),
    }
