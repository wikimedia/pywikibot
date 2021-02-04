# -*- coding: utf-8 -*-
"""Library module representing MediaWiki sites (wikis)."""
#
# (C) Pywikibot team, 2021
#
# Distributed under the terms of the MIT license.
#
from pywikibot.site._apisite import APISite, ClosedSite, DataSite
from pywikibot.site._basesite import BaseSite, PageInUse, RemovedSite
from pywikibot.site._namespace import Namespace, NamespacesDict
from pywikibot.site._siteinfo import Siteinfo
from pywikibot.site._tokenwallet import TokenWallet

__all__ = ('APISite', 'BaseSite', 'ClosedSite', 'DataSite', 'RemovedSite',
           'Namespace', 'NamespacesDict', 'PageInUse', 'Siteinfo',
           'TokenWallet')

_logger = 'wiki.site'
