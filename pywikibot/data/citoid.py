"""Citoid Query interface.

.. versionadded:: 10.6
"""
#
# (C) Pywikibot team, 2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from typing import Any

import pywikibot
from pywikibot.comms import http
from pywikibot.exceptions import ApiNotAvailableError, Error
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

        :param response_format: Return format, e.g. 'bibtex', 'wikibase', etc.
        :param ref_url: The URL to get the citation for.
        :return: A dictionary with the citation data.
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
        try:
            json = http.request(self.site, api_url).json()
            return json
        except Error as e:
            pywikibot.log(f'Caught pywikibot error {e}')
            raise
