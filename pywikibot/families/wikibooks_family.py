# -*- coding: utf-8  -*-
"""Family module for Wikibooks."""
from __future__ import unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikibooks
class Family(family.WikimediaFamily):

    """Family class for Wikibooks."""

    closed_wikis = [
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Afar_Wikibooks
        'aa',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Akan_Wikibooks
        'ak',
        # https://als.wikipedia.org/wiki/Wikipedia:Stammtisch/Archiv_2008-1#Afterwards.2C_closure_and_deletion_of_Wiktionary.2C_Wikibooks_and_Wikiquote_sites
        'als',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Assamese_Wikibooks
        'as',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Asturianu_Wikibooks
        'ast',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Aymar_Wikibooks
        'ay',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bashkir_Wikibooks
        'ba',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bislama_Wikibooks
        'bi',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bambara_Wikibooks
        'bm',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tibetan_Wikibooks
        'bo',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Chamorro_Wikibooks
        'ch',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Corsu_Wikibooks
        'co',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gaeilge_Wikibooks
        'ga',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gothic_Wikibooks
        'got',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Guarani_Wikibooks
        'gn',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gujarati_Wikibooks
        'gu',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kannada_Wikibooks
        'kn',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kashmiri_Wikibooks
        'ks',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_L%C3%ABtzebuergesch_Wikibooks
        'lb',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Lingala_Wikibooks
        'ln',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Latvian_Wikibooks
        'lv',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Maori_Wikibooks
        'mi',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Mongolian_Wikibooks
        'mn',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Burmese_Wikibooks
        'my',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nauruan_Wikibooks
        'na',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nahuatl_Wikibooks
        'nah',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Plattd%C3%BC%C3%BCtsch_Wikibooks
        'nds',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Pashto_Wikibooks
        'ps',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Quechua_Wikibooks
        'qu',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Rumantsch_Wikibooks
        'rm',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Sami_Wikibooks
        'se',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Simple_English_Wikibooks_(3)
        'simple',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Basa_Sunda_Wikibooks_(2)
        'su',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Swahili_Wikibooks
        'sw',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Turkmen_Wikibooks
        'tk',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Uyghur_Wikibooks
        'ug',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Volap%C3%BCk_Wikibooks
        'vo',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Walon_Wikibooks
        'wa',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Xhosa_Wikibooks
        'xh',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Yoruba_Wikibooks
        'yo',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Zhuang_Wikibooks
        'za',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Zulu_Wikibooks
        'zu',
    ]

    removed_wikis = [
        'tokipona',
    ]

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'wikibooks'

        self.languages_by_size = [
            'en', 'de', 'fr', 'hu', 'ja', 'it', 'es', 'pt', 'nl', 'pl', 'he',
            'vi', 'ca', 'id', 'sq', 'fi', 'ru', 'fa', 'cs', 'zh', 'sv', 'hr',
            'tr', 'ro', 'sr', 'ar', 'no', 'th', 'ko', 'gl', 'da', 'ta', 'mk',
            'az', 'tl', 'is', 'ka', 'lt', 'tt', 'uk', 'eo', 'bg', 'sk', 'sl',
            'el', 'hy', 'ms', 'sa', 'si', 'li', 'la', 'ml', 'ur', 'bn', 'ang',
            'ia', 'cv', 'et', 'hi', 'km', 'mr', 'eu', 'oc', 'kk', 'fy', 'ne',
            'ie', 'te', 'af', 'tg', 'ky', 'bs', 'pa', 'be', 'mg', 'cy',
            'zh-min-nan', 'ku', 'uz',
        ]

        self.langs = dict([(lang, '%s.wikibooks.org' % lang)
                           for lang in self.languages_by_size])

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
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

    def shared_data_repository(self, code, transcluded=False):
        """Return the shared data repository for this family."""
        return ('wikidata', 'wikidata')
