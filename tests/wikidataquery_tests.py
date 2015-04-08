# -*- coding: utf-8  -*-
"""Test cases for the WikidataQuery query syntax and API."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#


import pywikibot.data.wikidataquery as query
from tests.aspects import unittest, WikidataTestCase, TestCase

import pywikibot
from pywikibot.page import ItemPage, PropertyPage, Claim

import os
import time


class TestDryApiFunctions(TestCase):

    """Test WikiDataQuery API functions."""

    net = False

    def testQueries(self):
        """
        Test Queries and check whether they're behaving correctly.

        Check that we produce the expected query strings and that
        invalid inputs are rejected correctly
        """
        q = query.HasClaim(99)
        self.assertEqual(str(q), "claim[99]")

        q = query.HasClaim(99, 100)
        self.assertEqual(str(q), "claim[99:100]")

        q = query.HasClaim(99, [100])
        self.assertEqual(str(q), "claim[99:100]")

        q = query.HasClaim(99, [100, 101])
        self.assertEqual(str(q), "claim[99:100,101]")

        q = query.NoClaim(99, [100, 101])
        self.assertEqual(str(q), "noclaim[99:100,101]")

        q = query.StringClaim(99, "Hello")
        self.assertEqual(str(q), 'string[99:"Hello"]')

        q = query.StringClaim(99, ["Hello"])
        self.assertEqual(str(q), 'string[99:"Hello"]')

        q = query.StringClaim(99, ["Hello", "world"])
        self.assertEqual(str(q), 'string[99:"Hello","world"]')

        self.assertRaises(TypeError, lambda: query.StringClaim(99, 2))

        q = query.Tree(92, [1], 2)
        self.assertEqual(str(q), 'tree[92][1][2]')

        # missing third arg
        q = query.Tree(92, 1)
        self.assertEqual(str(q), 'tree[92][1][]')

        # missing second arg
        q = query.Tree(92, reverse=3)
        self.assertEqual(str(q), 'tree[92][][3]')

        q = query.Tree([92, 93], 1, [2, 7])
        self.assertEqual(str(q), 'tree[92,93][1][2,7]')

        # bad tree arg types
        self.assertRaises(TypeError, lambda: query.Tree(99, "hello"))

        q = query.Link("enwiki")
        self.assertEqual(str(q), 'link[enwiki]')

        q = query.NoLink(["enwiki", "frwiki"])
        self.assertEqual(str(q), 'nolink[enwiki,frwiki]')

        # bad link arg types
        self.assertRaises(TypeError, lambda: query.Link(99))
        self.assertRaises(TypeError, lambda: query.Link([99]))

        # HasClaim with tree as arg
        q = query.HasClaim(99, query.Tree(1, 2, 3))
        self.assertEqual(str(q), "claim[99:(tree[1][2][3])]")

        q = query.HasClaim(99, query.Tree(1, [2, 5], [3, 90]))
        self.assertEqual(str(q), "claim[99:(tree[1][2,5][3,90])]")


class TestLiveApiFunctions(WikidataTestCase):

    """Test WikiDataQuery API functions."""

    cached = True

    def testQueriesWDStructures(self):
        """Test queries using Wikibase page structures like ItemPage."""
        q = query.HasClaim(PropertyPage(self.repo, "P99"))
        self.assertEqual(str(q), "claim[99]")

        q = query.HasClaim(PropertyPage(self.repo, "P99"),
                           ItemPage(self.repo, "Q100"))
        self.assertEqual(str(q), "claim[99:100]")

        q = query.HasClaim(99, [100, PropertyPage(self.repo, "P101")])
        self.assertEqual(str(q), "claim[99:100,101]")

        q = query.StringClaim(PropertyPage(self.repo, "P99"), "Hello")
        self.assertEqual(str(q), 'string[99:"Hello"]')

        q = query.Tree(ItemPage(self.repo, "Q92"), [1], 2)
        self.assertEqual(str(q), 'tree[92][1][2]')

        q = query.Tree(ItemPage(self.repo, "Q92"), [PropertyPage(self.repo, "P101")], 2)
        self.assertEqual(str(q), 'tree[92][101][2]')

        self.assertRaises(TypeError, lambda: query.Tree(PropertyPage(self.repo, "P92"),
                                                        [PropertyPage(self.repo, "P101")],
                                                        2))

        c = pywikibot.Coordinate(50, 60)
        q = query.Around(PropertyPage(self.repo, "P625"), c, 23.4)
        self.assertEqual(str(q), 'around[625,50,60,23.4]')

        begin = pywikibot.WbTime(site=self.repo, year=1999)
        end = pywikibot.WbTime(site=self.repo, year=2010, hour=1)

        # note no second comma
        q = query.Between(PropertyPage(self.repo, "P569"), begin)
        self.assertEqual(str(q), 'between[569,+00000001999-01-01T00:00:00Z]')

        q = query.Between(PropertyPage(self.repo, "P569"), end=end)
        self.assertEqual(str(q), 'between[569,,+00000002010-01-01T01:00:00Z]')

        q = query.Between(569, begin, end)
        self.assertEqual(str(q), 'between[569,+00000001999-01-01T00:00:00Z,+00000002010-01-01T01:00:00Z]')

        # try negative year
        begin = pywikibot.WbTime(site=self.repo, year=-44)
        q = query.Between(569, begin, end)
        self.assertEqual(str(q), 'between[569,-00000000044-01-01T00:00:00Z,+00000002010-01-01T01:00:00Z]')

    def testQueriesDirectFromClaim(self):
        """Test construction of the right Query from a page.Claim."""
        claim = Claim(self.repo, 'P17')
        claim.setTarget(pywikibot.ItemPage(self.repo, 'Q35'))

        q = query.fromClaim(claim)
        self.assertEqual(str(q), 'claim[17:35]')

        claim = Claim(self.repo, 'P268')
        claim.setTarget('somestring')

        q = query.fromClaim(claim)
        self.assertEqual(str(q), 'string[268:"somestring"]')

    def testQuerySets(self):
        """Test that we can join queries together correctly."""
        # construct via queries
        qs = query.HasClaim(99, 100).AND(query.HasClaim(99, 101))

        self.assertEqual(str(qs), 'claim[99:100] AND claim[99:101]')

        self.assertEqual(repr(qs), 'QuerySet(claim[99:100] AND claim[99:101])')

        qs = query.HasClaim(99, 100).AND(query.HasClaim(99, 101)).AND(query.HasClaim(95))

        self.assertEqual(str(qs), 'claim[99:100] AND claim[99:101] AND claim[95]')

        # construct via queries
        qs = query.HasClaim(99, 100).AND([query.HasClaim(99, 101), query.HasClaim(95)])

        self.assertEqual(str(qs), 'claim[99:100] AND claim[99:101] AND claim[95]')

        qs = query.HasClaim(99, 100).OR([query.HasClaim(99, 101), query.HasClaim(95)])

        self.assertEqual(str(qs), 'claim[99:100] OR claim[99:101] OR claim[95]')

        q1 = query.HasClaim(99, 100)
        q2 = query.HasClaim(99, 101)

        # different joiners get explicit grouping parens (the api also allows
        # implicit, but we don't do that)
        qs1 = q1.AND(q2)
        qs2 = q1.OR(qs1).AND(query.HasClaim(98))

        self.assertEqual(str(qs2), '(claim[99:100] OR (claim[99:100] AND claim[99:101])) AND claim[98]')

        # if the joiners are the same, no need to group
        qs1 = q1.AND(q2)
        qs2 = q1.AND(qs1).AND(query.HasClaim(98))

        self.assertEqual(str(qs2), 'claim[99:100] AND claim[99:100] AND claim[99:101] AND claim[98]')

        qs1 = query.HasClaim(100).AND(query.HasClaim(101))
        qs2 = qs1.OR(query.HasClaim(102))

        self.assertEqual(str(qs2), '(claim[100] AND claim[101]) OR claim[102]')

        qs = query.Link("enwiki").AND(query.NoLink("dewiki"))

        self.assertEqual(str(qs), 'link[enwiki] AND nolink[dewiki]')

    def testQueryApiSyntax(self):
        """Test that we can generate the API query correctly."""
        w = query.WikidataQuery("http://example.com")

        qs = w.getQueryString(query.Link("enwiki"))
        self.assertEqual(qs, "q=link%5Benwiki%5D")

        self.assertEqual(w.getUrl(qs), "http://example.com/api?q=link%5Benwiki%5D")

        # check labels and props work OK
        qs = w.getQueryString(query.Link("enwiki"), ['en', 'fr'], ['prop'])
        self.assertEqual(qs, "q=link%5Benwiki%5D&labels=en,fr&props=prop")


class TestApiSlowFunctions(TestCase):

    """Test slow WikiDataQuery API functions."""

    sites = {
        'wdq': {
            'hostname': 'wdq.wmflabs.org',
        },
    }

    def testQueryApiGetter(self):
        """Test that we can actually retreive data and that caching works."""
        w = query.WikidataQuery(cacheMaxAge=0)

        # this query doesn't return any items, save a bit of bandwidth!
        q = query.HasClaim(105).AND([query.NoClaim(225), query.HasClaim(100)])

        # check that the cache file is created
        cacheFile = w.getCacheFilename(w.getQueryString(q, [], []))

        # remove existing cache file
        try:
            os.remove(cacheFile)
        except OSError:
            pass

        data = w.query(q)

        self.assertFalse(os.path.exists(cacheFile))

        w = query.WikidataQuery(cacheMaxAge=0.1)

        data = w.query(q)

        self.assertTrue(os.path.exists(cacheFile))

        self.assertIn('status', data)
        self.assertIn('items', data)

        t1 = time.time()
        data = w.query(q)
        t2 = time.time()

        # check that the cache access is fast
        self.assertLess(t2 - t1, 0.2)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
