"""Family module for Vikidia."""
#
# (C) Pywikibot team, 2010-2023
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


class Family(family.SubdomainFamily):

    """Family class for Vikidia."""

    name = 'vikidia'
    domain = 'vikidia.org'

    codes = [
        'ca', 'de', 'el', 'en', 'es', 'eu', 'fr', 'hy', 'it', 'oc', 'pt', 'ru',
        'scn',
    ]

    # Sites we want to edit but not count as real languages
    test_codes = ['central', 'test']
