# -*- coding: utf-8  -*-
"""Family module for Wikiquote."""
from __future__ import absolute_import, unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikiquote
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikiquote."""

    name = 'wikiquote'

    closed_wikis = [
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Alemannic_Wikiquote
        'als',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Old_English_Wikiquote
        'ang',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Asturianu_Wikiquote
        'ast',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bambara_Wikiquote
        'bm',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Corsu_Wikiquote
        'co',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nehiyaw_Wikiquote
        'cr',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gaeilge_Wikiquote
        'ga',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kazakh_Wikiquote
        'kk',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kanuri_Wikiquote
        'kr',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kashmiri_Wikiquote
        'ks',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kernewek_Wikiquote
        'kw',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Luxembourgish_Wikiquote
        'lb',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nauruan_Wikiquote
        'na',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Low_Saxon_Wikiquote
        'nds',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Quechua_Wikiquote
        'qu',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Simple_English_Wikiquote_(3)
        'simple',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Turkmen_Wikiquote
        'tk',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tatar_Wikiquote
        'tt',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Oyghurque_Wikiquote
        'ug',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Volapuk_Wikiquote
        'vo',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Zhuang_Wikiquote
        'za',
    ]

    removed_wikis = [
        'tokipona',
    ]

    def __init__(self):
        """Constructor."""
        self.languages_by_size = [
            'en', 'it', 'pl', 'ru', 'de', 'cs', 'pt', 'es', 'fr', 'sk', 'fa',
            'bs', 'uk', 'tr', 'lt', 'bg', 'he', 'ca', 'sl', 'eo', 'el', 'nn',
            'id', 'zh', 'hr', 'hy', 'th', 'hu', 'li', 'nl', 'su', 'ko', 'ja',
            'sv', 'ur', 'te', 'ar', 'fi', 'cy', 'az', 'la', 'no', 'gl', 'ml',
            'et', 'ku', 'kn', 'sr', 'eu', 'ro', 'ta', 'ka', 'da', 'sa', 'is',
            'gu', 'vi', 'be', 'hi', 'sq', 'mr', 'br', 'uz', 'af', 'zh-min-nan',
            'am', 'wo', 'ky',
        ]

        super(Family, self).__init__()

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'af', 'am', 'ar', 'az', 'be', 'bg', 'br', 'bs', 'ca', 'cs', 'da',
            'el', 'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fr', 'gl', 'he', 'hi',
            'hu', 'hy', 'id', 'is', 'it', 'ja', 'ka', 'kn', 'ku', 'ky', 'la',
            'li', 'lt', 'ml', 'mr', 'nl', 'nn', 'no', 'pt', 'ro', 'ru', 'sk',
            'sl', 'sq', 'sr', 'su', 'sv', 'ta', 'te', 'tr', 'uk', 'uz', 'vi',
            'wo', 'zh',
        ]

        # Subpages for documentation.
        # TODO: List is incomplete, to be completed for missing languages.
        self.doc_subpages = {
            '_default': ((u'/doc', ),
                         ['en']
                         ),
        }

    def code2encodings(self, code):
        """
        Return a list of historical encodings for a specific language.

        @param code: site code
        """
        # Historic compatibility
        if code == 'pl':
            return 'utf-8', 'iso8859-2'
        if code == 'ru':
            return 'utf-8', 'iso8859-5'
        return self.code2encoding(code),
