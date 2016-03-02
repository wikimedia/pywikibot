# -*- coding: utf-8  -*-
"""Test cases for the SPARQL API."""
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import sys

import pywikibot.data.sparql as sparql

from tests.aspects import unittest, TestCase

if sys.version_info[0] > 2:
    from unittest.mock import patch
else:
    from mock import patch

# See: https://www.w3.org/TR/2013/REC-sparql11-results-json-20130321/

SQL_RESPONSE = """
{
  "head" : {
    "vars" : [ "cat", "d", "catLabel" ]
  },
  "results" : {
    "bindings" : [ {
      "cat" : {
        "type" : "uri",
        "value" : "http://www.wikidata.org/entity/Q498787"
      },
      "d" : {
        "datatype" : "http://www.w3.org/2001/XMLSchema#dateTime",
        "type" : "literal",
        "value" : "1955-01-01T00:00:00Z"
      },
      "catLabel" : {
        "xml:lang" : "en",
        "type" : "literal",
        "value" : "Muezza"
      }
    }, {
      "cat" : {
        "type" : "uri",
        "value" : "http://www.wikidata.org/entity/Q677525"
      },
      "d" : {
        "datatype" : "http://www.w3.org/2001/XMLSchema#dateTime",
        "type" : "literal",
        "value" : "2015-06-22T00:00:00Z"
      },
      "catLabel" : {
        "xml:lang" : "en",
        "type" : "literal",
        "value" : "Orangey"
      }
    } ]
  }
}
"""

RESPONSE_TRUE = """
{
  "head" : { },
  "boolean" : true
}
"""

RESPONSE_FALSE = """
{
  "head" : { },
  "boolean" : false
}
"""


class TestContainer(object):
    """Simple test container for return values."""

    def __init__(self, value):
        """Create container."""
        self.content = value


class TestSparql(TestCase):
    """Test SPARQL queries."""

    net = False

    @patch.object(sparql.http, 'fetch')
    def testQuerySelect(self, mock_method):
        """Test SELECT query."""
        mock_method.return_value = TestContainer(SQL_RESPONSE)
        q = sparql.SparqlQuery()
        res = q.select('SELECT * WHERE { ?x ?y ?z }')
        self.assertIsInstance(res, list, 'Result is not a list')
        self.assertEqual(len(res), 2)

        self.assertDictEqual(res[0],
                             {'cat': 'http://www.wikidata.org/entity/Q498787',
                              'catLabel': 'Muezza', 'd': '1955-01-01T00:00:00Z'},
                             'Bad result')
        self.assertDictEqual(res[1],
                             {'cat': 'http://www.wikidata.org/entity/Q677525',
                              'catLabel': 'Orangey', 'd': '2015-06-22T00:00:00Z'},
                             'Bad result')

    @patch.object(sparql.http, 'fetch')
    def testQuerySelectFull(self, mock_method):
        """Test SELECT query with full data."""
        mock_method.return_value = TestContainer(SQL_RESPONSE)
        q = sparql.SparqlQuery()
        res = q.select('SELECT * WHERE { ?x ?y ?z }', full_data=True)
        self.assertIsInstance(res, list, 'Result is not a list')
        self.assertEqual(len(res), 2)

        self.assertIsInstance(res[0]['cat'], sparql.URI, 'Wrong type for URI')
        self.assertEqual(repr(res[0]['cat']), '<http://www.wikidata.org/entity/Q498787>',
                         'Wrong URI representation')
        self.assertEqual(res[0]['cat'].getID(), 'Q498787', 'Wrong URI ID')

        self.assertIsInstance(res[0]['catLabel'], sparql.Literal, 'Wrong type for Literal')
        self.assertEqual(repr(res[0]['catLabel']), 'Muezza@en', 'Wrong literal representation')

        self.assertIsInstance(res[0]['d'], sparql.Literal, 'Wrong type for Literal')
        self.assertEqual(repr(res[0]['d']),
                         '1955-01-01T00:00:00Z^^http://www.w3.org/2001/XMLSchema#dateTime',
                         'Wrong URI representation')

    @patch.object(sparql.http, 'fetch')
    def testGetItems(self, mock_method):
        """Test item list retrieval via SPARQL."""
        mock_method.return_value = TestContainer(SQL_RESPONSE)
        q = sparql.SparqlQuery()
        res = q.get_items('SELECT * WHERE { ?x ?y ?z }', 'cat')
        self.assertSetEqual(res, set(['Q498787', 'Q677525']))

    @patch.object(sparql.http, 'fetch')
    def testQueryAsk(self, mock_method):
        """Test ASK query."""
        mock_method.return_value = TestContainer(RESPONSE_TRUE)
        q = sparql.SparqlQuery()

        res = q.ask('ASK { ?x ?y ?z }')
        self.assertTrue(res)

        mock_method.return_value = TestContainer(RESPONSE_FALSE)
        res = q.ask('ASK { ?x ?y ?z }')
        self.assertFalse(res)

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
