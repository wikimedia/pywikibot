#!/usr/bin/env python3
"""Test cases for the SPARQL API."""
#
# (C) Pywikibot team, 2016-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import json
import unittest
from contextlib import suppress
from unittest.mock import patch

import pywikibot
from pywikibot.data import sparql
from pywikibot.exceptions import NoUsernameError
from tests.aspects import TestCase, WikidataTestCase
from tests.utils import skipping


# See: https://www.w3.org/TR/2013/REC-sparql11-results-json-20130321/

SQL_RESPONSE_CONTAINER = """
{
  "head" : {
    "vars" : [ "cat", "d", "catLabel" ]
  },
  "results" : {
    "bindings" : [
      %s
    ]
  }
}
"""

ITEM_Q498787 = """
    {
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
    }
"""

ITEM_Q677525 = """
    {
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


class Container:

    """Simple test container for return values."""

    def __init__(self, value) -> None:
        """Create container."""
        self.text = value

    def json(self):
        """Simulate Response.json()."""  # noqa: D402
        return json.loads(self.text)


class TestSparql(WikidataTestCase):

    """Test SPARQL queries."""

    @patch.object(sparql.http, 'fetch')
    def testQuerySelect(self, mock_method) -> None:
        """Test SELECT query."""
        mock_method.return_value = Container(
            SQL_RESPONSE_CONTAINER % f'{ITEM_Q498787}, {ITEM_Q677525}')
        with skipping(pywikibot.exceptions.TimeoutError):
            q = sparql.SparqlQuery()
        res = q.select('SELECT * WHERE { ?x ?y ?z }')
        self.assertIsInstance(res, list, 'Result is not a list')
        self.assertLength(res, 2)

        self.assertEqual(
            res[0],
            {'cat': 'http://www.wikidata.org/entity/Q498787',
             'catLabel': 'Muezza', 'd': '1955-01-01T00:00:00Z'},
            'Bad result')
        self.assertEqual(
            res[1],
            {'cat': 'http://www.wikidata.org/entity/Q677525',
             'catLabel': 'Orangey', 'd': '2015-06-22T00:00:00Z'},
            'Bad result')

    @patch.object(sparql.http, 'fetch')
    def testQuerySelectFull(self, mock_method) -> None:
        """Test SELECT query with full data."""
        mock_method.return_value = Container(
            SQL_RESPONSE_CONTAINER % f'{ITEM_Q498787}, {ITEM_Q677525}')
        with skipping(pywikibot.exceptions.TimeoutError):
            q = sparql.SparqlQuery()
        res = q.select('SELECT * WHERE { ?x ?y ?z }', full_data=True)
        self.assertIsInstance(res, list, 'Result is not a list')
        self.assertLength(res, 2)

        self.assertIsInstance(res[0]['cat'], sparql.URI, 'Wrong type for URI')
        self.assertEqual(repr(res[0]['cat']),
                         '<http://www.wikidata.org/entity/Q498787>',
                         'Wrong URI representation')
        self.assertEqual(res[0]['cat'].getID(), 'Q498787', 'Wrong URI ID')

        self.assertIsInstance(res[0]['catLabel'], sparql.Literal,
                              'Wrong type for Literal')
        self.assertEqual(repr(res[0]['catLabel']), 'Muezza@en',
                         'Wrong literal representation')

        self.assertIsInstance(res[0]['d'], sparql.Literal,
                              'Wrong type for Literal')
        self.assertEqual(
            repr(res[0]['d']),
            '1955-01-01T00:00:00Z^^http://www.w3.org/2001/XMLSchema#dateTime',
            'Wrong URI representation')

    @patch.object(sparql.http, 'fetch')
    def testGetItems(self, mock_method) -> None:
        """Test item list retrieval via SPARQL."""
        mock_method.return_value = Container(
            SQL_RESPONSE_CONTAINER % (f'{ITEM_Q498787}, {ITEM_Q677525}, '
                                      f'{ITEM_Q677525}')
        )
        with skipping(pywikibot.exceptions.TimeoutError):
            q = sparql.SparqlQuery()
        res = q.get_items('SELECT * WHERE { ?x ?y ?z }', 'cat')
        self.assertEqual(res, {'Q498787', 'Q677525'})
        res = q.get_items('SELECT * WHERE { ?x ?y ?z }', 'cat',
                          result_type=list)
        self.assertEqual(res, ['Q498787', 'Q677525', 'Q677525'])

    @patch.object(sparql.http, 'fetch')
    def testQueryAsk(self, mock_method) -> None:
        """Test ASK query."""
        mock_method.return_value = Container(RESPONSE_TRUE)
        with skipping(pywikibot.exceptions.TimeoutError):
            q = sparql.SparqlQuery()

        res = q.ask('ASK { ?x ?y ?z }')
        self.assertTrue(res)

        mock_method.return_value = Container(RESPONSE_FALSE)
        res = q.ask('ASK { ?x ?y ?z }')
        self.assertFalse(res)


class TestCommonsQueryService(TestCase):

    """Test Commons Query Service auth."""

    family = 'commons'
    code = 'commons'

    def testLoginAndOauthPermission(self) -> None:
        """Commons Query Service Login and Oauth permission."""
        # Define the SPARQL query
        query = 'SELECT ?a ?b WHERE { ?a wdt:P9478 ?b } LIMIT 4'

        # Set up the SPARQL endpoint and entity URL
        # Note: https://commons-query.wikimedia.org
        # requires user to be logged in

        entity_url = 'https://commons.wikimedia.org/entity/'
        endpoint = 'https://commons-query.wikimedia.org/sparql'

        # Create a SparqlQuery object
        query_object = sparql.SparqlQuery(endpoint=endpoint,
                                          entity_url=entity_url)

        # Execute the SPARQL query and retrieve the data user not logged in
        with self.assertRaisesRegex(NoUsernameError, 'User not logged in'):
            query_object.select(query, full_data=False)


class Shared:

    """Shared test placeholder."""

    class SparqlNodeTests(TestCase):

        """Tests encoding issues."""

        net = False
        object_under_test = None

        def test_is_sparql_node(self) -> None:
            """Object should be a SparqlNode."""
            self.assertIsInstance(self.object_under_test, sparql.SparqlNode)

        def test__repr__returnsStringType(self) -> None:
            """__repr__ should return type str."""
            self.assertIsInstance(self.object_under_test.__repr__(), str)

        def test__str__returnsStringType(self) -> None:
            """__str__ should return type str."""
            self.assertIsInstance(self.object_under_test.__str__(), str)


class LiteralTests(Shared.SparqlNodeTests):

    """Tests for sparql.Literal."""

    net = False
    object_under_test = sparql.Literal(
        {'datatype': '', 'lang': 'en', 'value': 'value'})


class BnodeTests(Shared.SparqlNodeTests):

    """Tests for sparql.Bnode."""

    net = False
    object_under_test = sparql.Bnode({'value': 'Foo'})


class URITests(Shared.SparqlNodeTests):

    """Tests for sparql.URI."""

    net = False
    object_under_test = sparql.URI(
        {'value': 'http://foo.com'}, 'http://bar.com')


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
