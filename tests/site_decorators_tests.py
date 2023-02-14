#!/usr/bin/env python3
"""Tests against a fake Site object."""
#
# (C) Pywikibot team, 2012-2022
#
# Distributed under the terms of the MIT license.
#
import unittest

from pywikibot.exceptions import UserRightsError
from pywikibot.site._decorators import must_be, need_right, need_version
from pywikibot.tools import deprecated
from tests.aspects import DebugOnlyTestCase, DeprecationTestCase


class TestMustBe(DebugOnlyTestCase):

    """Test cases for the must_be decorator."""

    net = False

    # Implemented without setUpClass(cls) and global variables as objects
    # were not completely disposed and recreated but retained 'memory'
    def setUp(self):
        """Creating fake variables to appear as a site."""
        self.code = 'test'
        self.family = lambda: None
        self.family.name = 'test'
        self.sitename = self.family.name + ':' + self.code
        self._logged_in_as = None
        self._userinfo = []
        self.obsolete = False
        super().setUp()
        self.version = lambda: '1.23'  # lowest supported release

    def login(self, group):
        """Fake the log in as required user group."""
        self._logged_in_as = group
        self._userinfo = [group]

    def user(self):
        """Fake the logged in user."""
        return self._logged_in_as

    def has_group(self, group):
        """Fake the groups user belongs to."""
        return group in self._userinfo

    def test_mock_in_test(self):
        """Test that setUp and login work."""
        self.assertIsNone(self._logged_in_as)
        self.login('user')
        self.assertEqual(self._logged_in_as, 'user')

    # Test that setUp is actually called between each test
    test_mock_in_test_reset = test_mock_in_test

    @must_be('steward')
    def call_this_steward_req_function(self, *args, **kwargs):
        """Require a sysop to function."""
        return args, kwargs

    @must_be('sysop')
    def call_this_sysop_req_function(self, *args, **kwargs):
        """Require a sysop to function."""
        return args, kwargs

    @must_be('user')
    def call_this_user_req_function(self, *args, **kwargs):
        """Require a user to function."""
        return args, kwargs

    def test_must_be_steward(self):
        """Test a function which requires a sysop."""
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.login('steward')
        retval = self.call_this_steward_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)

    def test_must_be_sysop(self):
        """Test a function which requires a sysop."""
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.login('sysop')
        retval = self.call_this_sysop_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)
        with self.assertRaises(UserRightsError):
            self.call_this_steward_req_function(args, kwargs)

    def test_must_be_user(self):
        """Test a function which requires a user."""
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.login('user')
        retval = self.call_this_user_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)
        with self.assertRaises(UserRightsError):
            self.call_this_sysop_req_function(args, kwargs)

    def test_override_usertype(self):
        """Test overriding the required group."""
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.login('sysop')
        retval = self.call_this_user_req_function(
            *args, as_group='sysop', **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)

    def test_obsolete_site(self):
        """Test when the site is obsolete and shouldn't be edited."""
        self.obsolete = True
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.login('steward')
        retval = self.call_this_user_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)
        self.login('user')
        with self.assertRaises(UserRightsError):
            self.call_this_user_req_function(args, kwargs)


class TestNeedRight(DebugOnlyTestCase):

    """Test cases for the must_be decorator."""

    net = False

    # Implemented without setUpClass(cls) and global variables as objects
    # were not completely disposed and recreated but retained 'memory'
    def setUp(self):
        """Creating fake variables to appear as a site."""
        self.code = 'test'
        self.family = lambda: None
        self.family.name = 'test'
        self.sitename = self.family.name + ':' + self.code
        self._logged_in_as = None
        self._userinfo = []
        self.obsolete = False
        super().setUp()
        self.version = lambda: '1.23'  # lowest supported release

    def login(self, group, right):
        """Fake the log in as required user group."""
        self._logged_in_as = group
        self._userinfo = [right]

    def user(self):
        """Fake the logged in user."""
        return self._logged_in_as

    def has_right(self, right):
        """Fake the groups user belongs to."""
        return right in self._userinfo

    @need_right('edit')
    def call_this_edit_req_function(self, *args, **kwargs):
        """Require a sysop to function."""
        return args, kwargs

    @need_right('move')
    def call_this_move_req_function(self, *args, **kwargs):
        """Require a sysop to function."""
        return args, kwargs

    def test_need_right_edit(self):
        """Test a function which requires a sysop."""
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.login('user', 'edit')
        retval = self.call_this_edit_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)

    def test_need_right_move(self):
        """Test a function which requires a sysop."""
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.login('user', 'move')
        retval = self.call_this_move_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)
        with self.assertRaises(UserRightsError):
            self.call_this_edit_req_function(args, kwargs)


class TestNeedVersion(DeprecationTestCase):

    """Test cases for the need_version decorator."""

    net = False

    # Implemented without setUpClass(cls) and global variables as objects
    # were not completely disposed and recreated but retained 'memory'
    def setUp(self):
        """Set up test method."""
        super().setUp()
        self.version = lambda: '1.23'

    @need_version('1.24')
    def too_new(self):
        """Method which is to new."""
        return True

    @need_version('1.23')
    def old_enough(self):
        """Method which is as new as the server."""
        return True

    @need_version('1.22')
    def older(self):
        """Method which is old enough."""
        return True

    @need_version('1.24')
    @deprecated
    def deprecated_unavailable_method(self):
        """Method which is to new and then deprecated."""
        return True

    @deprecated
    @need_version('1.24')
    def deprecated_unavailable_method2(self):
        """Method which is deprecated first and then to new."""
        return True

    @need_version('1.22')
    @deprecated
    def deprecated_available_method(self):
        """Method which is old enough and then deprecated."""
        return True

    @deprecated
    @need_version('1.22')
    def deprecated_available_method2(self):
        """Method which is deprecated first and then old enough."""
        return True

    def test_need_version(self):
        """Test need_version when the version is new, exact or old enough."""
        with self.assertRaises(NotImplementedError):
            self.too_new()
        self.assertTrue(self.old_enough())
        self.assertTrue(self.older())

    def test_need_version_fail_with_deprecated(self):
        """Test order of combined version check and deprecation warning."""
        # FIXME: The deprecation message should be:
        #   __name__ + '.TestNeedVersion.deprecated_unavailable_method

        # The outermost decorator is the version check, so no
        # deprecation message.
        with self.assertRaisesRegex(
                NotImplementedError,
                'deprecated_unavailable_method'):
            self.deprecated_unavailable_method()
        self.assertNoDeprecation()

        # The deprecator is first, but the version check still
        # raises exception.
        with self.assertRaisesRegex(
                NotImplementedError,
                'deprecated_unavailable_method2'):
            self.deprecated_unavailable_method2()
        self.assertOneDeprecationParts(
            __name__ + '.TestNeedVersion.deprecated_unavailable_method2')

    def test_need_version_success_with_deprecated(self):
        """Test order of combined version check and deprecation warning."""
        self.deprecated_available_method()
        self.assertOneDeprecationParts(
            __name__ + '.TestNeedVersion.deprecated_available_method')

        self.deprecated_available_method2()
        self.assertOneDeprecationParts(
            __name__ + '.TestNeedVersion.deprecated_available_method2')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
