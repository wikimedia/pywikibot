#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Family module for Beta Wikipedia."""
from __future__ import annotations

from pywikibot import family


class Family(family.BetaSubdomainFamily):

    """Family class for Beta Wikipedia."""

    name = 'betawikipedia'

    closed_wikis = ['aa']

    test_codes = [
        'ar', 'bn', 'ca', 'crh', 'cs', 'de', 'en', 'eo', 'es', 'fa', 'fr',
        'he', 'hi', 'ja', 'ko', 'nl', 'ru', 'simple', 'sq', 'sr', 'sv',
        'test', 'test2', 'uk', 'vi', 'zh'
    ]
