#!/usr/bin/env python3
"""Tests against a fake Site object."""
#
# (C) Pywikibot team, 2012-2022
#
# Distributed under the terms of the MIT license.
#
import unittest

import pywikibot
from pywikibot.comms.http import user_agent
from tests.aspects import DefaultDrySiteTestCase


class TestDrySite(DefaultDrySiteTestCase):

    """Tests against a fake Site object."""

    dry = True

    def test_logged_in(self):
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

    def test_user_agent(self):
        """Test different variants of user agents."""
        x = self.get_site()

        x._userinfo = {'name': 'foo'}
        x._username = 'foo'

        self.assertEqual('Pywikibot/' + pywikibot.__version__,
                         user_agent(x, format_string='{pwb}'))

        self.assertEqual(x.family.name,
                         user_agent(x, format_string='{family}'))
        self.assertEqual(x.code,
                         user_agent(x, format_string='{lang}'))
        self.assertEqual(x.family.name + ' ' + x.code,
                         user_agent(x, format_string='{family} {lang}'))

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

        self.assertEqual(script_value + ' Pywikibot/6.0 (User:foo_bar)',
                         user_agent(x, format_string=old_config))

        x._userinfo = {'name': '⁂'}
        x._username = '⁂'

        self.assertEqual('%E2%81%82',
                         user_agent(x, format_string='{username}'))

        x._userinfo = {'name': '127.0.0.1'}
        x._username = None

        self.assertEqual('Foo', user_agent(x, format_string='Foo {username}'))
        self.assertEqual('Foo (' + x.family.name + ':' + x.code + ')',
                         user_agent(x,
                                    format_string='Foo ({script_comments})'))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
