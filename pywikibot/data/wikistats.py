# -*- coding: utf-8 -*-
"""Objects representing WikiStats API."""
#
# (C) Pywikibot team, 2014-2020
#
# Distributed under the terms of the MIT license.
from collections import defaultdict
from csv import DictReader
from io import StringIO

import pywikibot

from pywikibot.comms import http
from pywikibot.tools import deprecated, remove_last_args


class WikiStats:

    """
    Light wrapper around WikiStats data, caching responses and data.

    The methods accept a Pywikibot family name as the WikiStats table name,
    mapping the names before calling the WikiStats API.
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

    def __init__(self, url='https://wikistats.wmflabs.org/') -> None:
        """Initializer."""
        self.url = url
        self._raw = defaultdict(dict)
        self._data = {}

    @deprecated('get', since='20201017', future_warning=True)
    def fetch(self, table: str, format='xml') -> bytes:
        """
        DEPRECATED. Fetch data from WikiStats.

        @param table: table of data to fetch
        @param format: Format of data to use
        @type format: 'xml' or 'csv'.
        """
        if format == 'xml':
            path = '/{format}/{table}.{format}'
        else:
            path = '/api.php?action=dump&table={table}&format={format}'
        url = self.url + path

        if table not in self.ALL_KEYS:
            pywikibot.warning('WikiStats unknown table ' + table)

        if table in self.FAMILY_MAPPING:
            table = self.FAMILY_MAPPING[table]

        r = http.fetch(url.format(table=table, format=format))
        return r.raw

    @deprecated('get', since='20201017', future_warning=True)
    def raw_cached(self, table: str, format='csv') -> bytes:
        """
        DEPRECATED. Cache raw data.

        @param table: table of data to fetch
        @param format: format of data to use
        @type format: 'xml' or 'csv'.
        """
        if table in self._raw[format]:
            return self._raw[format][table]

        data = self.fetch(table, format)
        self._raw[format][table] = data
        return data

    @deprecated('get', since='20201017', future_warning=True)
    def csv(self, table: str) -> list:
        """
        DEPRECATED. Get a list of a table of data.

        @param table: table of data to fetch
        """
        return self.get(table)

    @deprecated('get', since='20201017', future_warning=True)
    def xml(self, table: str) -> list:
        """
        DEPRECATED. Get a list of a table of data.

        @param table: table of data to fetch
        """
        return self.get(table)

    @remove_last_args(['format'])
    def get(self, table: str) -> list:
        """Get a list of a table of data.

        @param table: table of data to fetch
        """
        if table in self._data:
            return self._data[table]

        raw = self.raw_cached(table)
        f = StringIO(raw.decode('utf8'))
        reader = DictReader(f)
        data = list(reader)
        self._data[table] = data
        return data

    @remove_last_args(['format'])
    def get_dict(self, table: str) -> dict:
        """Get dictionary of a table of data.

        @param table: table of data to fetch
        """
        return {data['prefix']: data for data in self.get(table)}

    def sorted(self, table, key) -> list:
        """
        Reverse numerical sort of data.

        @param table: name of table of data
        @param key: numerical key, such as id, total, good
        """
        return sorted(self.get(table), key=lambda d: int(d[key]), reverse=True)

    def languages_by_size(self, table: str):
        """Return ordered list of languages by size from WikiStats."""
        # This assumes they appear in order of size in the WikiStats dump.
        return [d['prefix'] for d in self.get(table)]
