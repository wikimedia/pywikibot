# -*- coding: utf-8  -*-
"""Family module for Wikibooks."""
from __future__ import absolute_import, unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikibooks
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikibooks."""

    name = 'wikibooks'

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
        self.languages_by_size = [
            'en', 'de', 'hu', 'fr', 'ja', 'it', 'es', 'pt', 'nl', 'pl', 'vi',
            'he', 'ca', 'id', 'fi', 'sq', 'fa', 'ru', 'cs', 'zh', 'az', 'sv',
            'th', 'hr', 'tr', 'sr', 'ar', 'no', 'ko', 'gl', 'da', 'ta', 'ro',
            'mk', 'tl', 'is', 'uk', 'ka', 'lt', 'tt', 'sa', 'eo', 'sk', 'bg',
            'el', 'hy', 'si', 'ms', 'sl', 'bn', 'hi', 'li', 'la', 'ur', 'ml',
            'ang', 'ia', 'cv', 'et', 'km', 'mr', 'eu', 'oc', 'kk', 'ne', 'fy',
            'pa', 'ie', 'te', 'af', 'tg', 'ku', 'ky', 'bs', 'be', 'mg', 'cy',
            'zh-min-nan', 'uz',
        ]

        super(Family, self).__init__()

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'af', 'ang', 'ca', 'fa', 'fy', 'it', 'nl', 'ru', 'th', 'zh',
        ]

        # Subpages for documentation.
        # TODO: List is incomplete, to be completed for missing languages.
        self.doc_subpages = {
            '_default': ((u'/doc', ),
                         ['en']
                         ),
        }
