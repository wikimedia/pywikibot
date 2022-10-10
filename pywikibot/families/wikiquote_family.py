"""Family module for Wikiquote."""
#
# (C) Pywikibot team, 2005-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Wikimedia family that is known as Wikiquote
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikiquote."""

    name = 'wikiquote'

    closed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/closed.dblist
        'am', 'ang', 'ast', 'bm', 'co', 'cr', 'ga', 'kk', 'kr', 'ks', 'kw',
        'lb', 'na', 'nds', 'qu', 'simple', 'tk', 'tt', 'ug', 'vo', 'za',
        'zh-min-nan',
    ]

    removed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/deleted.dblist
        'als', 'tokipona',
    ]

    languages_by_size = [
        'it', 'en', 'pl', 'ru', 'cs', 'et', 'pt', 'fa', 'uk', 'de', 'fr', 'he',
        'es', 'eo', 'tr', 'sk', 'bs', 'ca', 'az', 'fi', 'sl', 'zh', 'lt', 'ar',
        'bg', 'hy', 'hr', 'sr', 'el', 'su', 'nn', 'id', 'sv', 'li', 'hu', 'ko',
        'nl', 'sah', 'ja', 'la', 'ta', 'gl', 'gu', 'ur', 'be', 'te', 'vi',
        'cy', 'no', 'ml', 'sq', 'hi', 'kn', 'eu', 'ro', 'ku', 'uz', 'ka', 'da',
        'sa', 'is', 'br', 'mr', 'af', 'th', 'wo', 'ky', 'ig', 'bcl', 'tl',
        'bn',
    ]

    category_redirect_templates = {
        '_default': (),
        'ar': ('تحويل تصنيف',),
        'en': ('Category redirect',),
        'ro': ('Redirect categorie',),
        'sq': ('Kategori e zhvendosur',),
        'uk': ('Categoryredirect',),
    }

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'af', 'ar', 'az', 'be', 'bg', 'br', 'bs', 'ca', 'cs', 'cy', 'da', 'el',
        'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fr', 'gl', 'gu', 'he', 'hi', 'hu',
        'hy', 'id', 'is', 'it', 'ja', 'ka', 'kn', 'ko', 'ku', 'ky', 'la', 'li',
        'lt', 'ml', 'mr', 'nl', 'nn', 'no', 'pt', 'ro', 'ru', 'sa', 'sah',
        'sk', 'sl', 'sq', 'sr', 'su', 'sv', 'ta', 'te', 'th', 'tr', 'uk', 'ur',
        'uz', 'vi', 'wo', 'zh',
    ]

    # Subpages for documentation.
    # TODO: List is incomplete, to be completed for missing languages.
    doc_subpages = {
        '_default': (('/doc', ),
                     ['en']
                     ),
        'ar': ('/شرح', '/doc'),
        'sr': ('/док', ),
    }

    def encodings(self, code):
        """
        Return a list of historical encodings for a specific language.

        :param code: site code
        """
        # Historic compatibility
        if code == 'pl':
            return 'utf-8', 'iso8859-2'
        if code == 'ru':
            return 'utf-8', 'iso8859-5'
        return super().encodings(code)
