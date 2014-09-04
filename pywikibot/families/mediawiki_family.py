# -*- coding: utf-8  -*-
"""Family module for MediaWiki wiki."""

__version__ = '$Id$'

from pywikibot import family


# The MediaWiki family
# user-config.py: usernames['mediawiki']['mediawiki'] = 'User name'
class Family(family.WikimediaFamily):

    """Family module for MediaWiki wiki."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'mediawiki'

        self.langs = {
            'mediawiki': 'www.mediawiki.org',
        }
