# -*- coding: utf-8  -*-
"""Family module for Wikibooks."""

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikibooks
class Family(family.WikimediaFamily):

    """Family class for Wikibooks."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'wikibooks'

        self.languages_by_size = [
            'en', 'de', 'fr', 'hu', 'ja', 'it', 'es', 'pt', 'nl', 'pl', 'he',
            'vi', 'id', 'sq', 'ca', 'fi', 'ru', 'fa', 'cs', 'zh', 'sv', 'da',
            'hr', 'tr', 'no', 'th', 'sr', 'ar', 'gl', 'ko', 'ta', 'mk', 'tl',
            'ro', 'is', 'ka', 'tt', 'lt', 'az', 'eo', 'uk', 'bg', 'sk', 'sl',
            'el', 'hy', 'ms', 'si', 'li', 'la', 'ml', 'ur', 'ang', 'ia', 'cv',
            'et', 'bn', 'km', 'hi', 'mr', 'sa', 'oc', 'kk', 'eu', 'ne', 'fy',
            'ie', 'te', 'af', 'tg', 'ky', 'bs', 'pa', 'mg', 'be', 'cy',
            'zh-min-nan', 'ku', 'uz',
        ]

        self.langs = dict([(lang, '%s.wikibooks.org' % lang)
                           for lang in self.languages_by_size])

        # Global bot allowed languages on https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'af', 'ang', 'ca', 'fa', 'fy', 'it', 'nl', 'ru', 'th', 'zh',
        ]

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are
        # put after those, in code-alphabetical order.
        self.interwiki_putfirst = {
            'en': self.alphabetic,
            'fi': self.alphabetic,
            'fr': self.alphabetic,
            'he': ['en'],
            'hu': ['en'],
            'pl': self.alphabetic,
            'simple': self.alphabetic
        }

        self.obsolete = {
            'aa': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Afar_Wikibooks
            'ak': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Akan_Wikibooks
            'als': None,  # https://als.wikipedia.org/wiki/Wikipedia:Stammtisch/Archiv_2008-1#Afterwards.2C_closure_and_deletion_of_Wiktionary.2C_Wikibooks_and_Wikiquote_sites
            'as': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Assamese_Wikibooks
            'ast': None,
            'ay': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Aymar_Wikibooks
            'ba': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bashkir_Wikibooks
            'bi': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bislama_Wikibooks
            'bm': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bambara_Wikibooks
            'bo': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tibetan_Wikibooks
            'ch': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Chamorro_Wikibooks
            'co': None,   # https://bugzilla.wikimedia.org/show_bug.cgi?id=28644
            'dk': 'da',
            'ga': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gaeilge_Wikibooks
            'got': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gothic_Wikibooks
            'gn': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Guarani_Wikibooks
            'gu': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gujarati_Wikibooks
            'jp': 'ja',
            'kn': None,   # https://bugzilla.wikimedia.org/show_bug.cgi?id=20325
            'ks': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kashmiri_Wikibooks
            'lb': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_L%C3%ABtzebuergesch_Wikibooks
            'ln': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Lingala_Wikibooks
            'lv': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Latvian_Wikibooks
            'mi': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Maori_Wikibooks
            'minnan': 'zh-min-nan',
            'mn': None,
            'my': None,
            'na': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nauruan_Wikibooks
            'nah': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nahuatl_Wikibooks
            'nb': 'no',
            'nds': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Plattd%C3%BC%C3%BCtsch_Wikibooks
            'ps': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Pashto_Wikibooks
            'qu': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Quechua_Wikibooks
            'rm': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Rumantsch_Wikibooks
            'se': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Sami_Wikibooks
            'simple': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Simple_English_Wikibooks_(3)
            'su': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Basa_Sunda_Wikibooks_(2)
            'sw': None,   # https://bugzilla.wikimedia.org/show_bug.cgi?id=25170
            'tk': None,
            'tokipona': None,
            'ug': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Uyghur_Wikibooks
            'vo': None,   # https://bugzilla.wikimedia.org/show_bug.cgi?id=37413
            'wa': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Walon_Wikibooks
            'xh': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Xhosa_Wikibooks
            'yo': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Yoruba_Wikibooks
            'za': None,   # https://bugzilla.wikimedia.org/show_bug.cgi?id=20325
            'zh-tw': 'zh',
            'zh-cn': 'zh',
            'zu': None,   # https://bugzilla.wikimedia.org/show_bug.cgi?id=25425
        }
