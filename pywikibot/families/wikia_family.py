# -*- coding: utf-8 -*-
"""Family module for Wikia."""
#
# (C) Pywikibot team, 2008-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family
from pywikibot.tools import deprecated


# The Wikia Search family
# user-config.py: usernames['wikia']['wikia'] = 'User name'
class Family(family.SingleSiteFamily, family.WikiaFamily):

    """Family class for Wikia."""

    name = u'wikia'
    domain = 'www.wikia.com'

    @deprecated('APISite.version()')
    def version(self, code):
        """Return the version for this family."""
        return '1.19.24'

    def apipath(self, code):
        """Return the path to api.php for this family."""
        return '/api.php'
