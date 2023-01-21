"""Objects representing interwiki map of MediaWiki site."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot.backports import Set


class _IWEntry:

    """An entry of the _InterwikiMap with a lazy loading site."""

    def __init__(self, local, url, prefix=None) -> None:
        self._site = None
        self.local = local
        self.url = url
        self.prefix = prefix

    @property
    def site(self):
        if self._site is None:
            try:
                self._site = pywikibot.Site(
                    url=self.url, fam=None if self.local else self.prefix)
            except Exception as e:
                self._site = e
        return self._site


class _InterwikiMap:

    """A representation of the interwiki map of a site."""

    def __init__(self, site) -> None:
        """
        Create an empty uninitialized interwiki map for the given site.

        :param site: Given site for which interwiki map is to be created
        :type site: pywikibot.site.APISite
        """
        super().__init__()
        self._site = site
        self._map = None

    def reset(self) -> None:
        """Remove all mappings to force building a new mapping."""
        self._map = None

    @property
    def _iw_sites(self):
        """Fill the interwikimap cache with the basic entries."""
        # _iw_sites is a local cache to return an APISite instance depending
        # on the interwiki prefix of that site
        if self._map is None:
            self._map = {iw['prefix']: _IWEntry('local' in iw,
                                                iw['url'],
                                                iw['prefix'])
                         for iw in self._site.siteinfo['interwikimap']}
        return self._map

    def __getitem__(self, prefix):
        """
        Return the site, locality and url for the requested prefix.

        :param prefix: Interwiki prefix
        :type prefix: Dictionary key
        :rtype: _IWEntry
        :raises KeyError: Prefix is not a key
        :raises TypeError: Site for the prefix is of wrong type
        """
        if prefix not in self._iw_sites:
            raise KeyError(f"'{prefix}' is not an interwiki prefix.")
        if isinstance(self._iw_sites[prefix].site, pywikibot.site.BaseSite):
            return self._iw_sites[prefix]
        if isinstance(self._iw_sites[prefix].site, Exception):
            raise self._iw_sites[prefix].site
        raise TypeError('_iw_sites[{}] is wrong type: {}'
                        .format(prefix, type(self._iw_sites[prefix].site)))

    def get_by_url(self, url: str) -> Set[str]:
        """
        Return a set of prefixes applying to the URL.

        :param url: URL for the interwiki
        """
        return {prefix for prefix, iw_entry in self._iw_sites.items()
                if iw_entry.url == url}
