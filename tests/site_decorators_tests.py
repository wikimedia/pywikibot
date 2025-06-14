#!/usr/bin/env python3
"""Tests against a fake Site object."""
#
# (C) Pywikibot team, 2012-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest

from pywikibot.exceptions import UserRightsError
from pywikibot.site._decorators import must_be, need_right, need_version
from pywikibot.tools import deprecated
from tests.aspects import DeprecationTestCase, TestCase


class DecoratorTestsBase(TestCase):

    """Base class for decorator tests."""

    net = False

    # Implemented without setUpClass(cls) and global variables as objects
    # were not completely disposed and recreated but retained 'memory'
    def setUp(self) -> None:
        """Creating fake variables to appear as a site."""
        self.code = 'test'
        self.family = lambda: None
        self.family.name = 'test'
        self.sitename = self.family.name + ':' + self.code
        self._logged_in_as = None
        self.obsolete = False
        super().setUp()
        self.version = lambda: '1.27'  # lowest supported release

    def user(self):
        """Fake the logged in user."""
        return self._logged_in_as


class TestMustBe(DecoratorTestsBase):

    """Test cases for the must_be decorator."""

    def setUp(self) -> None:
        """Creating fake variables to appear as a site."""
        self._userinfo = []
        super().setUp()

    def login(self, group) -> None:
        """Fake the log in as required user group."""
        self._logged_in_as = group
        self._userinfo = [group]

    def has_group(self, group):
        """Fake the groups user belongs to."""
        return group in self._userinfo

    def test_mock_in_test(self) -> None:
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

    def test_must_be_steward(self) -> None:
        """Test a function which requires a sysop."""
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.login('steward')
        retval = self.call_this_steward_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)

    def test_must_be_sysop(self) -> None:
        """Test a function which requires a sysop."""
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.login('sysop')
        retval = self.call_this_sysop_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)
        with self.assertRaises(UserRightsError):
            self.call_this_steward_req_function(args, kwargs)

    def test_must_be_user(self) -> None:
        """Test a function which requires a user."""
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.login('user')
        retval = self.call_this_user_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)
        with self.assertRaises(UserRightsError):
            self.call_this_sysop_req_function(args, kwargs)

    def test_override_usertype(self) -> None:
        """Test overriding the required group."""
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.login('sysop')
        retval = self.call_this_user_req_function(
            *args, as_group='sysop', **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)

    def test_obsolete_site(self) -> None:
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


class TestNeedRight(DecoratorTestsBase):

    """Test cases for the must_be decorator."""

    # Implemented without setUpClass(cls) and global variables as objects
    # were not completely disposed and recreated but retained 'memory'
    def setUp(self) -> None:
        """Creating fake variables to appear as a site."""
        self.userinfo = {'rights': []}
        super().setUp()

    def login(self, group, right) -> None:
        """Fake the log in as required user group."""
        self._logged_in_as = group
        self.userinfo['rights'] = [right]

    def has_right(self, right):
        """Fake the groups user belongs to."""
        return right in self.userinfo['rights']

    @need_right('edit')
    def call_this_edit_req_function(self, *args, **kwargs):
        """Require a sysop to function."""
        return args, kwargs

    @need_right('move')
    def call_this_move_req_function(self, *args, **kwargs):
        """Require a sysop to function."""
        return args, kwargs

    def test_need_right_edit(self) -> None:
        """Test a function which requires a sysop."""
        args = (1, 2, 'a', 'b')
        kwargs = {'i': 'j', 'k': 'l'}
        self.login('user', 'edit')
        retval = self.call_this_edit_req_function(*args, **kwargs)
        self.assertEqual(retval[0], args)
        self.assertEqual(retval[1], kwargs)

    def test_need_right_move(self) -> None:
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
    def setUp(self) -> None:
        """Set up test method."""
        super().setUp()
        self.version = lambda: '1.23'

    @need_version('1.24')
    def too_new(self) -> bool:
        """Method which is to new."""
        return True

    @need_version('1.23')
    def old_enough(self) -> bool:
        """Method which is as new as the server."""
        return True

    @need_version('1.22')
    def older(self) -> bool:
        """Method which is old enough."""
        return True

    @need_version('1.24')
    @deprecated
    def deprecated_unavailable_method(self) -> bool:
        """Method which is to new and then deprecated."""
        return True

    @deprecated
    @need_version('1.24')
    def deprecated_unavailable_method2(self) -> bool:
        """Method which is deprecated first and then to new."""
        return True

    @need_version('1.22')
    @deprecated
    def deprecated_available_method(self) -> bool:
        """Method which is old enough and then deprecated."""
        return True

    @deprecated
    @need_version('1.22')
    def deprecated_available_method2(self) -> bool:
        """Method which is deprecated first and then old enough."""
        return True

    def test_need_version(self) -> None:
        """Test need_version when the version is new, exact or old enough."""
        with self.assertRaises(NotImplementedError):
            self.too_new()
        self.assertTrue(self.old_enough())
        self.assertTrue(self.older())

    def test_need_version_fail_with_deprecated(self) -> None:
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

    def test_need_version_success_with_deprecated(self) -> None:
        """Test order of combined version check and deprecation warning."""
        self.deprecated_available_method()
        self.assertOneDeprecationParts(
            __name__ + '.TestNeedVersion.deprecated_available_method')

        self.deprecated_available_method2()
        self.assertOneDeprecationParts(
            __name__ + '.TestNeedVersion.deprecated_available_method2')


if __name__ == '__main__':
    unittest.main()
