# -*- coding: utf-8 -*-
"""SPARQL Query interface."""
#
# (C) Pywikibot team, 2016-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import json

from requests.exceptions import Timeout

from pywikibot import config, warning, Site, sleep
from pywikibot.comms import http
from pywikibot.tools import UnicodeMixin, PY2, py2_encode_utf_8
from pywikibot.exceptions import Error, TimeoutError

if not PY2:
    from urllib.parse import quote
else:
    from urllib2 import quote


DEFAULT_HEADERS = {'cache-control': 'no-cache',
                   'Accept': 'application/sparql-results+json'}


class SparqlQuery(object):
    """
    SPARQL Query class.

    This class allows to run SPARQL queries against any SPARQL endpoint.
    """

    def __init__(self, endpoint=None, entity_url=None, repo=None,
                 max_retries=None, retry_wait=None):
        """
        Create endpoint.

        @param endpoint: SPARQL endpoint URL
        @type endpoint: str
        @param entity_url: URL prefix for any entities returned in a query.
        @type entity_url: str
        @param repo: The Wikibase site which we want to run queries on. If
            provided this overrides any value in endpoint and entity_url.
            Defaults to Wikidata.
        @type repo: pywikibot.site.DataSite
        @param max_retries: (optional) Maximum number of times to retry after
               errors, defaults to config.max_retries.
        @type max_retries: int
        @param retry_wait: (optional) Minimum time in seconds to wait after an
               error, defaults to config.retry_wait seconds (doubles each retry
               until config.retry_max is reached).
        @type retry_wait: float
        """
        # default to Wikidata
        if not repo and not endpoint:
            repo = Site('wikidata', 'wikidata')

        if repo:
            try:
                self.endpoint = repo.sparql_endpoint
                self.entity_url = repo.concept_base_uri
            except NotImplementedError:
                raise NotImplementedError(
                    'Wiki version must be 1.28-wmf.23 or newer to '
                    'automatically extract the sparql endpoint. '
                    'Please provide the endpoint and entity_url '
                    'parameters instead of a repo.')
            if not self.endpoint:
                raise Error('The site {0} does not provide a sparql endpoint.'
                            .format(repo))
        else:
            if not entity_url:
                raise Error('If initialised with an endpoint the entity_url '
                            'must be provided.')
            self.endpoint = endpoint
            self.entity_url = entity_url

        self.last_response = None

        if max_retries is None:
            self.max_retries = config.max_retries
        else:
            self.max_retries = max_retries
        if retry_wait is None:
            self.retry_wait = config.retry_wait
        else:
            self.retry_wait = retry_wait

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
        @type query: str
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
                    if var not in row:
                        # var is not available (OPTIONAL is probably used)
                        values[var] = None
                    elif full_data:
                        if row[var]['type'] not in VALUE_TYPES:
                            raise ValueError('Unknown type: {}'
                                             .format(row[var]['type']))
                        valtype = VALUE_TYPES[row[var]['type']]
                        values[var] = valtype(row[var],
                                              entity_url=self.entity_url)
                    else:
                        values[var] = row[var]['value']
                result.append(values)
            return result
        return None

    def query(self, query, headers=DEFAULT_HEADERS):
        """
        Run SPARQL query and return parsed JSON result.

        @param query: Query text
        @type query: str
        """
        url = '{0}?query={1}'.format(self.endpoint, quote(query))
        while True:
            try:
                self.last_response = http.fetch(url, headers=headers)
            except Timeout:
                self.wait()
                continue
            if not self.last_response.text:
                return None
            try:
                return json.loads(self.last_response.text)
            except ValueError:
                return None

    def wait(self):
        """Determine how long to wait after a failed request."""
        self.max_retries -= 1
        if self.max_retries < 0:
            raise TimeoutError('Maximum retries attempted without success.')
        warning('Waiting {0} seconds before retrying.'.format(self.retry_wait))
        sleep(self.retry_wait)
        # double the next wait, but do not exceed config.retry_max seconds
        self.retry_wait = min(config.retry_max, self.retry_wait * 2)

    def ask(self, query, headers=DEFAULT_HEADERS):
        """
        Run SPARQL ASK query and return boolean result.

        @param query: Query text
        @type query: str
        @rtype: bool
        """
        data = self.query(query, headers=headers)
        return data['boolean']

    def get_items(self, query, item_name='item', result_type=set):
        """
        Retrieve items which satisfy given query.

        Items are returned as Wikibase IDs.

        @param query: Query string. Must contain ?{item_name} as one of the
            projected values.
        @param item_name: Name of the value to extract
        @param result_type: type of the iterable in which
              SPARQL results are stored (default set)
        @type result_type: iterable
        @return: item ids, e.g. Q1234
        @rtype: same as result_type
        """
        res = self.select(query, full_data=True)
        if res:
            return result_type(r[item_name].getID() for r in res)
        return result_type()


class SparqlNode(UnicodeMixin):
    """Base class for SPARQL nodes."""

    def __init__(self, value):
        """Create a SparqlNode."""
        self.value = value

    def __unicode__(self):
        return self.value


class URI(SparqlNode):
    """Representation of URI result type."""

    def __init__(self, data, entity_url, **kwargs):
        """
        Create URI object.

        @type data: dict
        """
        super(URI, self).__init__(data.get('value'))
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

    @py2_encode_utf_8
    def __repr__(self):
        return '<' + self.value + '>'


class Literal(SparqlNode):
    """Representation of RDF literal result type."""

    def __init__(self, data, **kwargs):
        """
        Create Literal object.

        @type data: dict
        """
        super(Literal, self).__init__(data.get('value'))
        self.type = data.get('datatype')
        self.language = data.get('xml:lang')

    @py2_encode_utf_8
    def __repr__(self):
        if self.type:
            return self.value + '^^' + self.type
        if self.language:
            return self.value + '@' + self.language
        return self.value


class Bnode(SparqlNode):
    """Representation of blank node."""

    def __init__(self, data, **kwargs):
        """
        Create Bnode.

        @type data: dict
        """
        super(Bnode, self).__init__(data.get('value'))

    @py2_encode_utf_8
    def __repr__(self):
        return '_:' + self.value


VALUE_TYPES = {'uri': URI, 'literal': Literal, 'bnode': Bnode}
