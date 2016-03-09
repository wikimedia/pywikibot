# -*- coding: utf-8  -*-
"""SPARQL Query interface."""
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import json
import sys
if sys.version_info[0] > 2:
    from urllib.parse import quote
else:
    from urllib2 import quote

from pywikibot.comms import http

WIKIDATA = 'http://query.wikidata.org/sparql'
DEFAULT_HEADERS = {'cache-control': 'no-cache',
                   'Accept': 'application/sparql-results+json'}


class SparqlQuery(object):
    """
    SPARQL Query class.

    This class allows to run SPARQL queries against any SPARQL endpoint.
    """

    def __init__(self, endpoint=WIKIDATA, entity_url='http://www.wikidata.org/entity/'):
        """
        Create endpoint.

        @param endpoint: SPARQL endpoint URL, by default Wikidata query endpoint
        """
        self.endpoint = endpoint
        self.last_response = None
        self.entity_url = entity_url

    def get_last_response(self):
        """
        Return last received response.

        @return: Response object from last request or None
        """
        return self.last_response

    def select(self, query, full_data=False, headers=DEFAULT_HEADERS):
        """
        Run SPARQL query and return the result.

        The response is assumed to be in format defined by:
        https://www.w3.org/TR/2013/REC-sparql11-results-json-20130321/

        @param query: Query text
        @type query: string
        @param full_data: Whether return full data objects or only values
        @type full_data: bool
        @return: List of query results or None if query failed
        """
        data = self.query(query, headers=headers)
        if data and 'results' in data:
            result = []
            qvars = data['head']['vars']
            for row in data['results']['bindings']:
                values = {}
                for var in qvars:
                    if full_data:
                        if row[var]['type'] not in VALUE_TYPES:
                            raise ValueError('Unknown type: %s' % row[var]['type'])
                        valtype = VALUE_TYPES[row[var]['type']]
                        values[var] = valtype(row[var], entity_url=self.entity_url)
                    else:
                        values[var] = row[var]['value']
                result.append(values)
            return result
        else:
            return None

    def query(self, query, headers=DEFAULT_HEADERS):
        """
        Run SPARQL query and return parsed JSON result.

        @param query: Query text
        @type query: string
        """
        url = '%s?query=%s' % (self.endpoint, quote(query))
        self.last_response = http.fetch(url, headers=headers)
        if not self.last_response.content:
            return None
        try:
            return json.loads(self.last_response.content)
        except ValueError:
            return None

    def ask(self, query, headers=DEFAULT_HEADERS):
        """
        Run SPARQL ASK query and return boolean result.

        @param query: Query text
        @type query: string
        @rtype: bool
        """
        data = self.query(query, headers=headers)
        return data['boolean']

    def get_items(self, query, item_name='item'):
        """
        Retrieve set of items which satisfy given query.

        Items are returned as Wikibase IDs.

        @param query: Query string. Must contain ?{item_name} as one of the projected values.
        @param item_name: Name of the value to extract
        @return: Set of item ids, e.g. Q1234
        @rtype: set
        """
        res = self.select(query, full_data=True)
        if res:
            return set([r[item_name].getID() for r in res])
        return set()


class URI(object):
    """Representation of URI result type."""

    def __init__(self, data, entity_url, **kwargs):
        """
        Create URI object.

        @type data: dict
        """
        self.value = data.get('value')
        self.entity_url = entity_url

    def getID(self):
        """
        Get ID of Wikibase object identified by the URI.

        @return: ID of Wikibase object, e.g. Q1234
        """
        urllen = len(self.entity_url)
        if self.value.startswith(self.entity_url):
            return self.value[urllen:]
        else:
            return None

    def __str__(self):
        return self.value

    def __repr__(self):
        return '<' + self.value + '>'


class Literal(object):
    """Representation of RDF literal result type."""

    def __init__(self, data, **kwargs):
        """
        Create Literal object.

        @type data: dict
        """
        self.type = data.get('datatype')
        self.language = data.get('xml:lang')
        self.value = data.get('value')

    def __str__(self):
        return self.value

    def __repr__(self):
        if self.type:
            return self.value + '^^' + self.type
        if self.language:
            return self.value + '@' + self.language
        return self.value


class Bnode(object):
    """Representation of blank node."""

    def __init__(self, data, **kwargs):
        """
        Create Bnode.

        @type data: dict
        """
        self.value = data['value']

    def __str__(self):
        return self.value

    def __repr__(self):
        return "_:" + self.value

VALUE_TYPES = {'uri': URI, 'literal': Literal, 'bnode': Bnode}
