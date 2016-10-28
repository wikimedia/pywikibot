# -*- coding: utf-8 -*-
"""Family module for Wikinews."""
#
# (C) Pywikibot team, 2005-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikinews
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikinews."""

    name = 'wikinews'

    closed_wikis = [
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Hungarian_Wikinews
        'hu',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Dutch_Wikinews
        'nl',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Sindhi_Wikinews
        'sd',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Thai_Wikinews
        'th',
    ]

    def __init__(self):
        """Constructor."""
        self.languages_by_size = [
            'sr', 'en', 'fr', 'de', 'ru', 'pl', 'pt', 'es', 'it', 'zh', 'cs',
            'ca', 'ta', 'el', 'ar', 'sv', 'fa', 'ro', 'uk', 'tr', 'ja', 'sq',
            'no', 'eo', 'fi', 'bs', 'he', 'ko', 'bg',
        ]

        super(Family, self).__init__()

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = ['ca', 'cs', 'en', 'fa', 'ko', ]

        # TODO:
        # Change site_tests.py when wikinews will have doc_subpage.
