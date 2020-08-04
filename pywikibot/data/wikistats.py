# -*- coding: utf-8 -*-
"""Objects representing WikiStats API."""
#
# (C) Pywikibot team, 2014-2020
#
# Distributed under the terms of the MIT license.
import csv

from io import BytesIO, StringIO

import pywikibot
from pywikibot.comms import http


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
        self._raw = {}
        self._data = {}

    def fetch(self, table: str, format='xml'):
        """
        Fetch data from WikiStats.

        @param table: table of data to fetch
        @param format: Format of data to use
        @type format: 'xml' or 'csv'.
        @rtype: bytes
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

    def raw_cached(self, table: str, format):
        """
        Cache raw data.

        @param table: table of data to fetch
        @param format: format of data to use
        @type format: 'xml' or 'csv'.
        @rtype: bytes
        """
        if format not in self._raw:
            self._raw[format] = {}
        if table in self._raw[format]:
            return self._raw[format][table]

        data = self.fetch(table, format)

        self._raw[format][table] = data
        return data

    def csv(self, table: str):
        """
        Fetch and parse CSV for a table.

        @param table: table of data to fetch
        @rtype: list
        """
        if table in self._data.setdefault('csv', {}):
            return self._data['csv'][table]

        data = self.raw_cached(table, 'csv')

        f = StringIO(data.decode('utf8'))

        reader = csv.DictReader(f)
        data = list(reader)
        self._data['csv'][table] = data

        return data

    def xml(self, table: str):
        """
        Fetch and parse XML for a table.

        @param table: table of data to fetch
        @rtype: list
        """
        if table in self._data.setdefault('xml', {}):
            return self._data['xml'][table]

        from xml.etree import ElementTree

        data = self.raw_cached(table, 'xml')

        f = BytesIO(data)
        tree = ElementTree.parse(f)

        data = []

        for row in tree.findall('row'):
            site = {}

            for field in row.findall('field'):
                name = str(field.get('name'))
                site[name] = str(field.text)

            data.append(site)

        self._data['xml'][table] = data

        return data

    def get(self, table: str, format='csv'):
        """Get a list of a table of data.

        @param table: table of data to fetch
        @rtype: list
        """
        try:
            func = getattr(self, format)
        except AttributeError:
            raise NotImplementedError('Format "{}" is not supported'
                                      .format(format))
        return func(table)

    def get_dict(self, table: str, format='csv'):
        """Get dictionary of a table of data using format.

        @param table: table of data to fetch
        @param format: format of data to use
        @type format: 'xml' or 'csv', or None to autoselect.
        @rtype: dict
        """
        if format is None:  # old autoselect
            format = 'csv'
        return {data['prefix']: data for data in self.get(table, format)}

    def sorted(self, table, key):
        """
        Reverse numerical sort of data.

        @param table: name of table of data
        @param key: numerical key, such as id, total, good
        """
        return sorted(self.get(table),
                      key=lambda d: int(d[key]),
                      reverse=True)

    def languages_by_size(self, table: str):
        """Return ordered list of languages by size from WikiStats."""
        # This assumes they appear in order of size in the WikiStats dump.
        return [d['prefix'] for d in self.get(table)]
