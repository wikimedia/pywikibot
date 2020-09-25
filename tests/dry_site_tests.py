# -*- coding: utf-8 -*-
"""Tests against a fake Site object."""
#
# (C) Pywikibot team, 2012-2020
#
# Distributed under the terms of the MIT license.
#
import pywikibot

from pywikibot.comms.http import user_agent

from tests.aspects import unittest, DefaultDrySiteTestCase, DeprecationTestCase


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

        old_config = '{script}/{version} Pywikibot/2.0 (User:{username})'

        pywikibot.version.getversiondict()
        script_value = (pywikibot.calledModuleName() + '/'
                        + pywikibot.version.cache['rev'])

        self.assertEqual(script_value + ' Pywikibot/2.0 (User:foo_bar)',
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


class TestSetAction(DeprecationTestCase):

    """Test the deprecated setAction function."""

    net = False

    def setUp(self):
        """Backup the original configuration."""
        super().setUp()
        self._old_config = pywikibot.config.default_edit_summary

    def tearDown(self):
        """Restore the original configuration."""
        pywikibot.config.default_edit_summary = self._old_config
        super().tearDown()

    def test_set_action(self):
        """Test deprecated setAction function."""
        pywikibot.setAction('{0}X{0}'.format(self._old_config))
        self.assertOneDeprecation(self.INSTEAD)
        self.assertEqual(pywikibot.config.default_edit_summary,
                         '{0}X{0}'.format(self._old_config))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
