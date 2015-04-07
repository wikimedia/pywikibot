# -*- coding: utf-8  -*-
"""Tests against a fake Site object."""
#
# (C) Pywikibot team, 2012-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import pywikibot
from pywikibot.tools import deprecated
from pywikibot.site import must_be, need_version
from pywikibot.comms.http import user_agent
from pywikibot.exceptions import UnknownSite

from tests.aspects import (
    unittest,
    DefaultDrySiteTestCase,
    DebugOnlyTestCase,
    DeprecationTestCase,
)


class TestDrySite(DefaultDrySiteTestCase):

    """Tests against a fake Site object."""

    dry = True

    def test_logged_in(self):
        x = self.get_site()

        x._userinfo = {'name': None, 'groups': []}
        x._username = ['normal_user', 'sysop_user']

        self.assertFalse(x.logged_in(True))
        self.assertFalse(x.logged_in(False))

        x._userinfo['name'] = 'normal_user'
        self.assertFalse(x.logged_in(True))
        self.assertTrue(x.logged_in(False))

        x._userinfo['name'] = 'sysop_user'
        x._userinfo['groups'] = ['sysop']
        self.assertTrue(x.logged_in(True))
        self.assertFalse(x.logged_in(False))

    def test_user_agent(self):
        x = self.get_site()

        x._userinfo = {'name': 'foo'}
        x._username = ('foo', None)

        self.assertEqual('Pywikibot/' + pywikibot.__release__,
                         user_agent(x, format_string='{pwb}'))

        self.assertEqual(x.family.name,
                         user_agent(x, format_string='{family}'))
        self.assertEqual(x.code,
                         user_agent(x, format_string='{lang}'))
        self.assertEqual(x.family.name + ' ' + x.code,
                         user_agent(x, format_string='{family} {lang}'))

        self.assertEqual(x.username(),
                         user_agent(x, format_string='{username}'))

        x._userinfo = {'name': u'!'}
        x._username = (u'!', None)

        self.assertEqual('!', user_agent(x, format_string='{username}'))

        x._userinfo = {'name': u'foo bar'}
        x._username = (u'foo bar', None)

        self.assertEqual('foo_bar', user_agent(x, format_string='{username}'))

        old_config = '{script}/{version} Pywikibot/2.0 (User:{username})'

        pywikibot.version.getversiondict()
        script_value = pywikibot.calledModuleName() + '/' + pywikibot.version.cache['rev']

        self.assertEqual(script_value + ' Pywikibot/2.0 (User:foo_bar)',
                         user_agent(x, format_string=old_config))

        x._userinfo = {'name': u'⁂'}
        x._username = (u'⁂', None)

        self.assertEqual('%E2%81%82',
                         user_agent(x, format_string='{username}'))

        x._userinfo = {'name': u'127.0.0.1'}
        x._username = (None, None)

        self.assertEqual('Foo', user_agent(x, format_string='Foo {username}'))
        self.assertEqual('Foo (' + x.family.name + ':' + x.code + ')',
                         user_agent(x, format_string='Foo ({script_comments})'))


class TestMustBe(DebugOnlyTestCase):

    """Test cases for the must_be decorator."""

    net = False

    # Implemented without setUpClass(cls) and global variables as objects
    # were not completely disposed and recreated but retained 'memory'
    def setUp(self):
        self.code = 'test'
        self.family = lambda: None
        self.family.name = 'test'
        self._logged_in_as = None
        self.obsolete = False
        super(TestMustBe, self).setUp()
        self.version = lambda: '1.13'  # pre 1.14

    def login(self, sysop):
        # mock call
        self._logged_in_as = 'sysop' if sysop else 'user'

    def testMockInTest(self):
        self.assertEqual(self._logged_in_as, None)
        self.login(True)
        self.assertEqual(self._logged_in_as, 'sysop')

    testMockInTestReset = testMockInTest

    @must_be('sysop')
    def call_this_sysop_req_function(self, *args, **kwargs):
        return args, kwargs

    @must_be('user')
    def call_this_user_req_function(self, *args, **kwargs):
        return args, kwargs

    def testMustBeSysop(self):
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        retval = self.call_this_sysop_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)
        self.assertEqual(self._logged_in_as, 'sysop')

    def testMustBeUser(self):
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        retval = self.call_this_user_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)
        self.assertEqual(self._logged_in_as, 'user')

    def testOverrideUserType(self):
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        retval = self.call_this_user_req_function(*args, as_group='sysop', **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)
        self.assertEqual(self._logged_in_as, 'sysop')

    def testObsoleteSite(self):
        self.obsolete = True
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.assertRaises(UnknownSite, self.call_this_user_req_function, args, kwargs)


class TestNeedVersion(DeprecationTestCase):

    """Test cases for the need_version decorator."""

    net = False

    # Implemented without setUpClass(cls) and global variables as objects
    # were not completely disposed and recreated but retained 'memory'
    def setUp(self):
        super(TestNeedVersion, self).setUp()
        self.version = lambda: "1.13"

    @need_version("1.14")
    def too_new(self):
        return True

    @need_version("1.13")
    def old_enough(self):
        return True

    @need_version("1.12")
    def older(self):
        return True

    @need_version("1.14")
    @deprecated
    def deprecated_unavailable_method(self):
        return True

    @deprecated
    @need_version("1.14")
    def deprecated_unavailable_method2(self):
        return True

    @need_version("1.12")
    @deprecated
    def deprecated_available_method(self):
        return True

    @deprecated
    @need_version("1.12")
    def deprecated_available_method2(self):
        return True

    def test_need_version(self):
        self.assertRaises(NotImplementedError, self.too_new)
        self.assertTrue(self.old_enough())
        self.assertTrue(self.older())

    def test_need_version_fail_with_deprecated(self):
        """Test order of combined version check and deprecation warning."""
        # As assertRaisesRegex calls the method, unittest is the module
        # invoking the method instead of this test module.
        self._do_test_warning_filename = False

        # FIXME: The deprecation message should be:
        #   __name__ + '.TestNeedVersion.deprecated_unavailable_method
        # The outermost decorator is the version check, so no deprecation message.
        self.assertRaisesRegex(
            NotImplementedError,
            'deprecated_unavailable_method',
            self.deprecated_unavailable_method)
        self.assertNoDeprecation()

        # The deprecator is first, but the version check still raises exception.
        self.assertRaisesRegex(
            NotImplementedError,
            'deprecated_unavailable_method2',
            self.deprecated_unavailable_method2)
        self.assertDeprecation(
            __name__ + '.TestNeedVersion.deprecated_unavailable_method2 is deprecated.')

    def test_need_version_success_with_deprecated(self):
        """Test order of combined version check and deprecation warning."""
        self.deprecated_available_method()
        self.assertDeprecation(
            __name__ + '.TestNeedVersion.deprecated_available_method is deprecated.')

        self._reset_messages()

        self.deprecated_available_method2()
        self.assertDeprecation(
            __name__ + '.TestNeedVersion.deprecated_available_method2 is deprecated.')


if __name__ == '__main__':
    unittest.main()
