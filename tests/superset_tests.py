#!/usr/bin/env python3
"""Tests for superset module.

.. versionadded:: 9.2
"""
#
# (C) Pywikibot team, 2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress

import pywikibot
from pywikibot.data.superset import SupersetQuery
from pywikibot.exceptions import NoUsernameError
from pywikibot.pagegenerators import SupersetPageGenerator
from tests.aspects import TestCase


class TestSupersetWithoutAuth(TestCase):
    """Test Superset without auth."""

    family = 'meta'
    code = 'meta'

    def test_init(self):
        """Test init validation functions."""
        # Test initial database_id parameter in wrong format
        site = self.get_site()

        superset = SupersetQuery(schema_name='fiwiki_p')
        self.assertIsInstance(superset, SupersetQuery)

        msg = 'Only one of schema_name and site parameters can be defined'
        with self.assertRaisesRegex(TypeError, msg):
            superset = SupersetQuery(schema_name='enwiki_p',
                                     site=site)

        msg = 'database_id should be integer'
        with self.assertRaisesRegex(TypeError, msg):
            superset = SupersetQuery(schema_name='enwiki_p',
                                     database_id='foo')


class TestSupersetWithAuth(TestCase):
    """Test Superset with auth."""

    login = True
    family = 'meta'
    code = 'meta'

    def test_login_and_oauth_permisson(self):
        """Superset login and queries."""
        sql = 'SELECT page_id, page_title FROM page LIMIT 2;'
        site = self.get_site()

        # Test login and initial site parameters
        superset = SupersetQuery(site=site)
        try:
            superset.login()
        except NoUsernameError:
            self.skipTest('Oauth permission is missing.')
        except ConnectionError as e:
            self.skipTest(e)

        self.assertTrue(site.logged_in())
        self.assertTrue(superset.connected)
        rows = superset.query(sql)
        self.assertLength(rows, 2)

        # Test initial schema_name parameter
        superset = SupersetQuery(schema_name='fiwiki_p')
        rows = superset.query(sql)
        self.assertLength(rows, 2)

        # Test initial schema_name and database_id parameters
        superset = SupersetQuery(schema_name='enwiki_p', database_id=1)
        rows = superset.query(sql)
        self.assertLength(rows, 2)

        # Test get_database_id_by_schema_name()
        database_id = superset.get_database_id_by_schema_name('fiwiki_p')
        self.assertEqual(database_id, 2)

        # Test incorrect initial schema_name parameter
        superset = SupersetQuery(schema_name='foowiki_p')
        msg = 'Schema "foowiki_p" not found in https://superset.wmcloud.org.'
        with self.assertRaisesRegex(KeyError, msg):
            rows = superset.query(sql)

        # Test incorrect initial database_id parameter
        # superset.wmcloud.org fails with 500 server error
        # so this is expected to be changed when server side
        # is updated

        superset = SupersetQuery(schema_name='enwiki_p', database_id=2)
        with self.assertRaises(RuntimeError):
            rows = superset.query(sql)

        # Test overriding database_id in query
        rows = superset.query(sql, database_id=1)
        self.assertLength(rows, 2)

        # Test overriding schema_name in query
        rows = superset.query(sql, schema_name='fiwiki_p')
        self.assertLength(rows, 2)

        # Test overriding schema using site
        testsite = pywikibot.Site('fi', 'wikipedia')
        rows = superset.query(sql, site=testsite)
        self.assertLength(rows, 2)

        # Test that overriding both schema_name and site fails
        msg = 'Only one of schema_name and site parameters can be defined'
        with self.assertRaisesRegex(TypeError, msg):
            rows = superset.query(sql, schema_name='fiwiki_p', site=site)

    def test_superset_generators(self):
        """Superset generator."""
        site = self.get_site()
        query = 'SELECT page_id FROM page LIMIT 2'
        gen = SupersetPageGenerator(query, site=site)
        for page in gen:
            t = str(page)
            self.assertTrue(t)

        query = 'SELECT page_title, page_namespace FROM page LIMIT 2'
        gen = SupersetPageGenerator(query, site=site)
        for page in gen:
            t = str(page)
            self.assertTrue(t)

        query = 'SELECT page_namespace, page_title FROM page LIMIT 2'
        gen = SupersetPageGenerator(query, schema_name='fiwiki_p')
        for page in gen:
            t = str(page)
            self.assertTrue(t)

        query = ('SELECT * FROM ('
                 'SELECT gil_wiki AS page_wikidb, gil_page AS page_id '
                 'FROM globalimagelinks GROUP BY gil_wiki '
                 ') AS t LIMIT 2')
        gen = SupersetPageGenerator(query, schema_name='commonswiki_p')
        for page in gen:
            t = str(page)
            self.assertTrue(t)

        query = ('SELECT * FROM ( '
                 'SELECT gil_wiki AS page_wikidb, '
                 'gil_page_namespace_id AS page_namespace, '
                 'gil_page_title AS page_title '
                 'FROM globalimagelinks GROUP BY gil_wiki '
                 ') AS t LIMIT 2')
        gen = SupersetPageGenerator(query, schema_name='commonswiki_p')
        for page in gen:
            t = str(page)
            self.assertTrue(t)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
