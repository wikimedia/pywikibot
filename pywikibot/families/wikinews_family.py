"""Family module for Wikinews."""
#
# (C) Pywikibot team, 2005-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Wikimedia family that is known as Wikinews
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikinews."""

    name = 'wikinews'

    closed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/closed.dblist
        'bg', 'hu', 'sd', 'th', 'tr',
    ]

    languages_by_size = [
        'ru', 'sr', 'pt', 'fr', 'en', 'pl', 'zh', 'de', 'es', 'it', 'ar', 'cs',
        'ca', 'nl', 'el', 'ta', 'li', 'sv', 'uk', 'fa', 'fi', 'ro', 'ja', 'eo',
        'sq', 'no', 'ko', 'bs', 'he',
    ]

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
        'ar', 'bg', 'bs', 'ca', 'cs', 'el', 'en', 'eo', 'fa', 'fi', 'he', 'ja',
        'ko', 'li', 'nl', 'no', 'pt', 'ro', 'sq', 'sr', 'sv', 'ta', 'tr', 'uk',
        'zh',
    ]

    # Subpages for documentation.
    # TODO: List is incomplete, to be completed for missing languages.
    doc_subpages = {
        '_default': (('/doc', ),
                     ['en', ]
                     ),
        'ar': ('/شرح', '/doc'),
        'it': ('/man', ),
        'sr': ('/док', ),
    }
