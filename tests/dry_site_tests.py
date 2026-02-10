#!/usr/bin/env python3
#
# (C) Pywikibot team, 2012-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests against a fake Site object."""

from __future__ import annotations

import unittest

import pywikibot
from pywikibot.comms.http import user_agent, user_agent_username
from pywikibot.tools import suppress_warnings
from tests.aspects import DefaultDrySiteTestCase


class TestDrySite(DefaultDrySiteTestCase):

    """Tests against a fake Site object."""

    dry = True

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


if __name__ == '__main__':
    unittest.main()
