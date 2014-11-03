# -*- coding: utf-8  -*-
"""Family module for Battlestar Wiki."""

__version__ = '$Id$'

from pywikibot import family


# The Battlestar Wiki family, a set of Battlestar wikis.
# http://battlestarwiki.org/
class Family(family.Family):

    """Family class for Battlestar Wiki."""

    name = 'battlestarwiki'

    languages_by_size = ['en', 'de', 'fr', 'zh', 'es', 'ms', 'tr', 'simple']

    langs = dict([(lang, '%s.battlestarwiki.org' % lang)
                  for lang in languages_by_size])
