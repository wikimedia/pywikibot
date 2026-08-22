#
# (C) Pywikibot team, 2025-2026
#
# Distributed under the terms of the MIT license.
#
"""Citoid Query interface.

.. version-added:: 10.6
"""
from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from typing import Any

from pywikibot.comms import http
from pywikibot.exceptions import ApiNotAvailableError, CitoidError
from pywikibot.site import BaseSite


VALID_FORMAT = [
    'mediawiki', 'wikibase', 'zotero', 'bibtex', 'mediawiki-basefields'
]


@dataclass(eq=False)
class CitoidClient:

    """Citoid client class.

    This class allows to call the Citoid API used in production.
    """

    site: BaseSite

    def get_citation(
        self,
        response_format: str,
        ref_url: str
    ) -> dict[str, Any]:
        """Get a citation from the citoid service.

        .. version-changed:: 11.7
           Raise :exc:`CitoidError` if the Citoid service returns an
           error with the response dict.

        :param response_format: Return format, e.g. 'bibtex', 'wikibase',
            etc.
        :param ref_url: The URL to get the citation for.
        :return: A dictionary with the citation data.
        :raises ApiNotAvailableError: Citoid endpoint not configured for
            the given site.
        :raises CitoidError: Raised with the error returned by the
            Citoid service.
        :raises ValueError: Invalid format for *response_format*.
        """
        if response_format not in VALID_FORMAT:
            raise ValueError(f'Invalid format {response_format}, '
                             f'must be one of {VALID_FORMAT}')
        if (not hasattr(self.site.family, 'citoid_endpoint')
                or not self.site.family.citoid_endpoint):
            raise ApiNotAvailableError(
                f'Citoid endpoint not configured for {self.site.family.name}')
        base_url = self.site.family.citoid_endpoint
        ref_url = urllib.parse.quote(ref_url, safe='')
        api_url = urllib.parse.urljoin(base_url,
                                       f'{response_format}/{ref_url}')
        data = http.request(self.site, api_url).json()

        if 'error' in data:
            raise CitoidError(data['error'])

        return data
