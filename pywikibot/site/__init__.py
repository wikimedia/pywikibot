"""Library module representing MediaWiki sites (wikis)."""
#
# (C) Pywikibot team, 2021-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot.site._apisite import APISite
from pywikibot.site._basesite import BaseSite
from pywikibot.site._datasite import DataSite
from pywikibot.site._namespace import NamespaceArgType  # noqa: F401
from pywikibot.site._namespace import Namespace, NamespacesDict
from pywikibot.site._obsoletesites import ClosedSite, RemovedSite
from pywikibot.site._siteinfo import Siteinfo
from pywikibot.site._tokenwallet import TokenWallet


__all__ = ('APISite', 'BaseSite', 'ClosedSite', 'DataSite', 'RemovedSite',
           'Namespace', 'NamespacesDict', 'Siteinfo', 'TokenWallet')
