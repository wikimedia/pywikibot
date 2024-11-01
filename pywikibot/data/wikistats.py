"""Objects representing WikiStats API."""
#
# (C) Pywikibot team, 2014-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from csv import DictReader
from io import StringIO
from typing import Any

import pywikibot
from pywikibot.comms import http


# cache the data
_data: dict[str, list[Any]] = {}


class WikiStats:

    """Light wrapper around WikiStats data, caching responses and data.

    The methods accept a Pywikibot family name as the WikiStats table name,
    mapping the names before calling the WikiStats API.

    .. versionchanged:: 9.0
       tables are cached globally instead by instances.
    """

    FAMILY_MAPPING = {
        'wikipedia': 'wikipedias',
        'wikiquote': 'wikiquotes',
        'wikisource': 'wikisources',
        'wiktionary': 'wiktionaries',
    }

    MISC_SITES_TABLE = 'mediawikis'

    WMF_MULTILANG_TABLES = {
        'wikipedias', 'wiktionaries', 'wikisources', 'wikinews',
        'wikibooks', 'wikiquotes', 'wikivoyage', 'wikiversity',
    }

    OTHER_MULTILANG_TABLES = {
        'uncyclomedia',
        'rodovid',
        'wikifur',
        'wikitravel',
        'scoutwiki',
        'opensuse',
        'metapedias',
        'lxde',
        'pardus',
        'gentoo',
    }

    OTHER_TABLES = {
        # Farms
        'wikia',
        'wikkii',
        'wikisite',
        'editthis',
        'orain',
        'shoutwiki',
        'referata',

        # Single purpose/manager sets
        'wmspecials',
        'gamepedias',
        'w3cwikis',
        'neoseeker',
        'sourceforge',
    }

    ALL_TABLES = ({MISC_SITES_TABLE} | WMF_MULTILANG_TABLES
                  | OTHER_MULTILANG_TABLES | OTHER_TABLES)

    ALL_KEYS = set(FAMILY_MAPPING.keys()) | ALL_TABLES

    def __init__(self, url: str = 'https://wikistats.wmcloud.org/') -> None:
        """Initializer."""
        self.url = url

    def get(self, table: str) -> list:
        """Get a list of a table of data.

        :param table: table of data to fetch
        """
        if table in _data:
            return _data[table]

        if table not in self.ALL_KEYS:
            pywikibot.warning('WikiStats unknown table ' + table)

        table = self.FAMILY_MAPPING.get(table, table)
        path = '/api.php?action=dump&table={table}&format=csv'
        url = self.url + path
        r = http.fetch(url.format(table=table))
        f = StringIO(r.text)
        reader = DictReader(f)
        data = list(reader)
        _data[table] = data
        return data

    def get_dict(self, table: str) -> dict:
        """Get dictionary of a table of data.

        :param table: table of data to fetch
        """
        return {data['prefix']: data for data in self.get(table)}

    def sorted(self, table: str, key: str,
               reverse: bool | None = None) -> list:
        """Reverse numerical sort of data.

        :param table: name of table of data
        :param key: data table key
        :param reverse: If set to True the sorting order is reversed.
            If None the sorting order for numeric keys are reversed whereas
            alphanumeric keys are sorted in normal way.
        :return: The sorted table
        """
        table = self.get(table)

        # take the first entry to determine the sorting key
        first_entry = table[0]
        if first_entry[key].isdigit():
            def sort_key(d): return int(d[key])
            reverse = reverse if reverse is not None else True
        else:
            def sort_key(d): return d[key]
            reverse = reverse if reverse is not None else False

        return sorted(table, key=sort_key, reverse=reverse)

    def languages_by_size(self, table: str):
        """Return ordered list of languages by size from WikiStats."""
        # This assumes they appear in order of size in the WikiStats dump.
        return [d['prefix'] for d in self.get(table)]
