#!/usr/bin/env python3
#
# (C) Pywikibot team, 2012-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests against a fake Site object."""
from __future__ import annotations

import unittest
from unittest.mock import patch

import pywikibot
from pywikibot.comms.http import user_agent, user_agent_username
from pywikibot.data.api import Request
from pywikibot.exceptions import (
    APIError,
    UnexpectedAPIDataError,
    UnknownExtensionError,
)
from pywikibot.tools import suppress_warnings
from tests.aspects import DefaultSiteTestCase, TestCase
from tests.utils import DrySite


class TestDrySite(DefaultSiteTestCase):

    """Tests against a fake Site object."""

    dry = True

    def test_mediawiki_messages_generator(self) -> None:
        """Test fetching uncached messages from a one-shot iterable."""
        cache = {'zz-test': {'cached': 'cached value'}}
        response = ({'name': 'missing', 'content': 'missing value'},)
        with patch.dict('pywikibot.site._apisite._mw_msg_cache', cache,
                        clear=True), \
                patch('pywikibot.site._apisite.api.QueryGenerator',
                      return_value=response) as query:
            keys = (key for key in ('cached', 'missing'))
            result = self.site.mediawiki_messages(keys, lang='zz-test')

        self.assertEqual(list(result.items()), [
            ('cached', 'cached value'),
            ('missing', 'missing value'),
        ])
        query.assert_called_once_with(
            site=self.site,
            parameters={
                'meta': 'allmessages',
                'ammessages': ['missing'],
                'amlang': 'zz-test',
                'formatversion': 2,
            },
        )

    def test_logged_in(self) -> None:
        """Test logged_in() method."""
        x = self.get_site()
        x._userinfo = {'name': None, 'groups': [], 'id': 1}
        x._username = 'user'

        with self.subTest(variant='name: None'):
            self.assertFalse(x.logged_in())

        x._userinfo['name'] = 'user'
        with self.subTest(variant='name: user'):
            self.assertTrue(x.logged_in())

        x._userinfo['name'] = 'otheruser'
        with self.subTest(variant='name: otheruseer'):
            self.assertFalse(x.logged_in())

        x._userinfo['id'] = 0
        x._userinfo['name'] = 'user'
        with self.subTest(variant='id: 0'):
            self.assertFalse(x.logged_in())

        x._userinfo['id'] = 1
        with self.subTest(variant='id: 1'):
            self.assertTrue(x.logged_in())

        x._userinfo['anon'] = ''
        with self.subTest(variant='anon'):
            self.assertFalse(x.logged_in())

        del x._userinfo['anon']
        x._userinfo['groups'] = ['sysop']
        with self.subTest(variant='sysop'):
            self.assertTrue(x.logged_in())

    def test_user_agent(self) -> None:
        """Test different variants of user agents."""
        x = self.get_site()

        x._userinfo = {'name': 'foo'}
        x._username = 'foo'

        self.assertEqual('Pywikibot/' + pywikibot.__version__,
                         user_agent(x, format_string='{pwb}'))

        # {family} {lang} and {code} are replaced with {site}
        # since Pywikibot 11.0
        for format_string in ('{family}', '{code}', '{lang}'):
            with suppress_warnings(f'{format_string} value for user_agent',
                                   category=FutureWarning):
                self.assertEqual(x.sitename,
                                 user_agent(x, format_string=format_string))

        self.assertEqual(x.username(),
                         user_agent(x, format_string='{username}'))

        x._userinfo = {'name': '!'}
        x._username = '!'

        self.assertEqual('!', user_agent(x, format_string='{username}'))

        x._userinfo = {'name': 'foo bar'}
        x._username = 'foo bar'

        self.assertEqual('foo_bar', user_agent(x, format_string='{username}'))

        old_config = '{script}/{version} Pywikibot/6.0 (User:{username})'

        script_value = (pywikibot.calledModuleName() + '/'
                        + pywikibot.version.getversiondict()['rev'])

        # {version} is replaced with {revision} since Pywikibot 11.0
        with suppress_warnings('{version} value for user_agent',
                               category=FutureWarning):
            self.assertEqual(script_value + ' Pywikibot/6.0 (User:foo_bar)',
                             user_agent(x, format_string=old_config))

        x._userinfo = {'name': '⁂'}
        x._username = '⁂'

        self.assertEqual('%E2%81%82',
                         user_agent(x, format_string='{username}'))

        x._userinfo = {'name': '127.0.0.1'}
        x._username = None

        # user_agent_username() may set ua_username from environment variable
        ua_user = user_agent_username()
        self.assertEqual(f'Foo {ua_user}'.strip(),
                         user_agent(x, format_string='Foo {username}'))

        if self.site.sitename.startswith('wiki') and len(self.site.code) == 2:
            res = f'Foo ({x}; User:{ua_user})' if ua_user else f'Foo ({x})'
        else:
            full_url = self.site.base_url(f'wiki/User:{ua_user}')
            res = f'Foo ({full_url})' if ua_user else 'Foo'

        self.assertEqual(
            res, user_agent(x, format_string='Foo ({script_comments})'))


class TestGeoSearch(TestCase):

    """Test geographic searches without relying on changing map data."""

    family = 'wikipedia'
    code = 'en'
    dry = True

    def test_geosearch(self) -> None:
        """Preserve geographic records for each search input mode."""
        records = [
            {'pageid': 2, 'ns': 0, 'title': 'Nearby', 'lat': 6.46,
             'lon': 3.38, 'dist': 500.0, 'primary': True, 'country': 'NG'},
            {'pageid': 1, 'ns': 0, 'title': 'Further', 'lat': 6.47,
             'lon': 3.38, 'dist': 1500.0, 'primary': True},
        ]
        box = (6.48, 3.36, 6.43, 3.41)
        cases = (
            ({'coord': (6.455, 3.3841), 'radius': 5000},
             {'gscoord': '6.455|3.3841', 'gsradius': '5000'}),
            ({'page': 'Lagos'}, {'gspage': 'Lagos'}),
            ({'page': pywikibot.Page(self.site, 'Lagos#History')},
             {'gspage': 'Lagos'}),
            ({'bbox': box}, {'gsbbox': '6.48|3.36|6.43|3.41'}),
        )
        with (
            patch.object(self.site, 'has_extension', return_value=True),
            patch.object(Request, 'submit', autospec=True) as submit,
            patch.object(pywikibot.config, 'step', 1),
        ):
            submit.return_value = {
                'query': {'geosearch': records},
            }
            for inputs, parameters in cases:
                with self.subTest(inputs=inputs):
                    submit.reset_mock()
                    results = list(self.site.geosearch(
                        **inputs, namespaces='0|Talk', total=2))
                    self.assertEqual(results, records)
                    submit.assert_called_once()
                    request = submit.call_args.args[0]
                    self.assertEqual(request._encoded_items(), {
                        'action': 'query', 'list': 'geosearch', 'gslimit': '2',
                        'gsprop': 'type|name|dim|country|region|globe',
                        'gsnamespace': '0|1', 'formatversion': '2',
                        **parameters,
                    })

    def test_geosearch_empty_and_limits(self) -> None:
        """Handle an empty response and explicit result limits."""
        with (
            patch.object(self.site, 'has_extension', return_value=True),
            patch.object(Request, 'submit', autospec=True) as submit,
        ):
            submit.return_value = {'query': {'geosearch': []}}
            self.assertIsEmpty(list(self.site.geosearch(
                coord=(0, 0), namespaces=None, total=None)))
            parameters = submit.call_args.args[0]._encoded_items()
            self.assertEqual(parameters['gslimit'], 'max')
            self.assertEqual(parameters['gsnamespace'], '*')

            submit.reset_mock()
            self.assertIsEmpty(list(self.site.geosearch(
                coord=(0, 0), total=0)))
            submit.assert_not_called()

    def test_geosearch_errors(self) -> None:
        """Reject invalid inputs and propagate unavailable search errors."""
        with self.assertRaisesRegex(UnknownExtensionError, 'GeoData'):
            list(self.site.geosearch(coord=(0, 0)))

        cases = (
            ({}, 'exactly one'),
            ({'coord': (0, 0), 'page': 'Lagos'}, 'exactly one'),
            ({'coord': (0,)}, 'latitude and longitude'),
            ({'bbox': (0, 0)}, 'north, west, south, east'),
            ({'bbox': (1, 0, 0, 1), 'radius': 500}, 'combined with bbox'),
        )
        with (
            patch.object(self.site, 'has_extension', return_value=True),
            patch.object(Request, 'submit', autospec=True) as submit,
        ):
            for inputs, message in cases:
                with self.subTest(inputs=inputs):
                    with self.assertRaisesRegex(ValueError, message):
                        list(self.site.geosearch(**inputs))
            submit.assert_not_called()

            other_page = pywikibot.Page(
                DrySite('de', 'wikipedia', None), 'Lagos')
            submit.side_effect = Request._encoded_items
            with self.assertRaisesRegex(RuntimeError,
                                        'different from Request.site'):
                list(self.site.geosearch(page=other_page))

            submit.side_effect = APIError(
                'no-coordinates', 'The reference page has no coordinates')
            with self.assertRaisesRegex(APIError, 'no-coordinates'):
                list(self.site.geosearch(page='Lagos'))

    def test_geosearch_malformed_response(self) -> None:
        """Reject malformed responses before yielding any records."""
        responses = (
            {'query': {}},
            {'query': {'geosearch': {'unexpected': 'object'}}},
            {'query': {'geosearch': [{'title': 'Nearby'}, 'unexpected']}},
        )
        with (
            patch.object(self.site, 'has_extension', return_value=True),
            patch.object(Request, 'submit', autospec=True) as submit,
        ):
            for response in responses:
                with self.subTest(response=response):
                    submit.return_value = response
                    with self.assertRaisesRegex(UnexpectedAPIDataError,
                                                'GeoSearch response'):
                        next(self.site.geosearch(coord=(0, 0)))


if __name__ == '__main__':
    unittest.main()
