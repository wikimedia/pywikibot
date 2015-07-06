# -*- coding: utf-8  -*-
"""Family module for Battlestar Wiki."""
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The Battlestar Wiki family, a set of Battlestar wikis.
# http://battlestarwiki.org/
class Family(family.Family):

    """Family class for Battlestar Wiki."""

    name = 'battlestarwiki'

    languages_by_size = ['en', 'de']

    interwiki_removals = ['fr', 'zh', 'es', 'ms', 'tr', 'simple']

    langs = dict([(lang, '%s.battlestarwiki.org' % lang)
                  for lang in languages_by_size])
