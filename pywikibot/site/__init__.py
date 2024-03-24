"""Library module representing MediaWiki sites (wikis)."""
#
# (C) Pywikibot team, 2021-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations


# to prevent ImportError exception due to circular imports
from pywikibot.site._namespace import Namespace, NamespacesDict  # isort: split

from pywikibot.site._apisite import APISite
from pywikibot.site._basesite import BaseSite
from pywikibot.site._datasite import DataSite
from pywikibot.site._namespace import NamespaceArgType  # noqa: F401
from pywikibot.site._obsoletesites import ClosedSite, RemovedSite
from pywikibot.site._siteinfo import Siteinfo
from pywikibot.site._tokenwallet import TokenWallet


__all__ = ('APISite', 'BaseSite', 'ClosedSite', 'DataSite', 'RemovedSite',
           'Namespace', 'NamespacesDict', 'Siteinfo', 'TokenWallet')

# iiprop file information to get, used in several places
_IIPROP = (
    'timestamp', 'user', 'comment', 'url', 'size', 'sha1', 'mime', 'mediatype',
    'archivename', 'bitdepth',
)
