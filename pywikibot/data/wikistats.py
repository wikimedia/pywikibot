# -*- coding: utf-8  -*-
"""Objects representing WikiStats API."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
from __future__ import unicode_literals

import sys

from io import BytesIO, StringIO

import pywikibot

if sys.version_info[0] > 2:
    import csv
else:
    try:
        import unicodecsv as csv
    except ImportError:
        pywikibot.warning(
            'WikiStats: unicodecsv package required for using csv in Python 2;'
            ' falling back to using the larger XML datasets.')
        csv = None

from pywikibot.comms import http


class WikiStats(object):

    """
    Light wrapper around WikiStats data, caching responses and data.

    The methods accept a Pywikibot family name as the WikiStats table name,
    mapping the names before calling the WikiStats API.
    """

    FAMILY_MAPPING = {
        'anarchopedia': 'anarchopedias',
        'wikipedia':    'wikipedias',
        'wikiquote':    'wikiquotes',
        'wikisource':   'wikisources',
        'wiktionary':   'wiktionaries',
    }

    MISC_SITES_TABLE = 'mediawikis'

    WMF_MULTILANG_TABLES = set([
        'wikipedias', 'wiktionaries', 'wikisources', 'wikinews',
        'wikibooks', 'wikiquotes', 'wikivoyage', 'wikiversity',
    ])

    OTHER_MULTILANG_TABLES = set([
        'uncyclomedia',
        'anarchopedias',
        'rodovid',
        'wikifur',
        'wikitravel',
        'scoutwiki',
        'opensuse',
        'metapedias',
        'lxde',
        'pardus',
        'gentoo',
    ])

    OTHER_TABLES = set([
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
    ])

    ALL_TABLES = (set([MISC_SITES_TABLE]) | WMF_MULTILANG_TABLES |
                  OTHER_MULTILANG_TABLES | OTHER_TABLES)

    ALL_KEYS = set(FAMILY_MAPPING.keys()) | ALL_TABLES

    def __init__(self, url='https://wikistats.wmflabs.org/'):
        """Constructor."""
        self.url = url
        self._raw = {}
        self._data = {}

    def fetch(self, table, format="xml"):
        """
        Fetch data from WikiStats.

        @param table: table of data to fetch
        @type table: basestring
        @param format: Format of data to use
        @type format: 'xml' or 'csv'.
        @rtype: bytes
        """
        URL = self.url + '/api.php?action=dump&table=%s&format=%s'

        if table not in self.ALL_KEYS:
            pywikibot.warning('WikiStats unknown table %s' % table)

        if table in self.FAMILY_MAPPING:
            table = self.FAMILY_MAPPING[table]

        r = http.fetch(URL % (table, format))
        return r.raw

    def raw_cached(self, table, format):
        """
        Cache raw data.

        @param table: table of data to fetch
        @type table: basestring
        @param format: Format of data to use
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

    def csv(self, table):
        """
        Fetch and parse CSV for a table.

        @param table: table of data to fetch
        @type table: basestring
        @rtype: list
        """
        if table in self._data.setdefault('csv', {}):
            return self._data['csv'][table]

        data = self.raw_cached(table, 'csv')

        if sys.version_info[0] > 2:
            f = StringIO(data.decode('utf8'))
        else:
            f = BytesIO(data)

        reader = csv.DictReader(f)

        data = [site for site in reader]

        self._data['csv'][table] = data

        return data

    def xml(self, table):
        """
        Fetch and parse XML for a table.

        @param table: table of data to fetch
        @type table: basestring
        @rtype: list
        """
        if table in self._data.setdefault('xml', {}):
            return self._data['xml'][table]

        from xml.etree import cElementTree

        data = self.raw_cached(table, 'xml')

        f = BytesIO(data)
        tree = cElementTree.parse(f)

        data = []

        for row in tree.findall('row'):
            site = {}

            for field in row.findall('field'):
                site[field.get('name')] = field.text

            data.append(site)

        self._data['xml'][table] = data

        return data

    def get(self, table, format=None):
        """
        Get a list of a table of data using format.

        @param table: table of data to fetch
        @type table: basestring
        @param format: Format of data to use
        @type format: 'xml' or 'csv', or None to autoselect.
        @rtype: list
        """
        if csv or format == 'csv':
            data = self.csv(table)
        else:
            data = self.xml(table)
        return data

    def get_dict(self, table, format=None):
        """
        Get dictionary of a table of data using format.

        @param table: table of data to fetch
        @type table: basestring
        @param format: Format of data to use
        @type format: 'xml' or 'csv', or None to autoselect.
        @rtype: dict
        """
        return dict((data['prefix'], data)
                    for data in self.get(table, format))

    def sorted(self, table, key):
        """
        Reverse numerical sort of data.

        @param table: name of table of data
        @param key: numerical key, such as id, total, good
        """
        return sorted(self.get(table),
                      key=lambda d: int(d[key]),
                      reverse=True)

    def languages_by_size(self, table):
        """Return ordered list of languages by size from WikiStats."""
        # This assumes they appear in order of size in the WikiStats dump.
        return [d['prefix'] for d in self.get(table)]
