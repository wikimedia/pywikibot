# -*- coding: utf-8  -*-
"""Tests for deprecation tools."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from pywikibot.tools import deprecated
from tests.aspects import unittest, DeprecationTestCase


@deprecated()
def deprecated_func():
    """Deprecated function."""
    pass


@deprecated()
def deprecated_func_bad_args(self):
    """Deprecated function with arg 'self'."""
    pass


class DeprecatedMethodClass(object):

    """Class with methods deprecated."""

    @classmethod
    @deprecated()
    def class_method(cls):
        return cls

    @staticmethod
    @deprecated()
    def static_method(foo):
        return foo

    @deprecated()
    def instance_method(self, foo):
        self.foo = foo

    def undecorated_method(self):
        pass


@deprecated()
class DeprecatedClass(object):

    """Deprecated class."""

    pass


class DeprecatorTestCase(DeprecationTestCase):

    """Test cases for deprecation tools."""

    net = False

    def test_deprecated_function(self):
        deprecated_func()
        self.assertDeprecation(__name__ + '.deprecated_func')

    def test_deprecated_function_bad_args(self):
        deprecated_func_bad_args('a')
        self.assertDeprecation(__name__ + '.deprecated_func_bad_args')

    @unittest.expectedFailure
    def test_deprecated_function_bad_args_failure(self):
        """Test to show the weakness of @deprecated decorator."""
        f = DeprecatedMethodClass()
        deprecated_func_bad_args(f)
        self.assertDeprecation(__name__ + '.deprecated_func_bad_args')

    def test_deprecated_instance_method(self):
        f = DeprecatedMethodClass()
        f.instance_method('a')
        self.assertDeprecation(__name__ + '.DeprecatedMethodClass.instance_method')

    def test_deprecated_class_method(self):
        DeprecatedMethodClass.class_method()
        self.assertDeprecation(__name__ + '.DeprecatedMethodClass.class_method')

    def test_deprecated_static_method(self):
        DeprecatedMethodClass.static_method('a')
        self.assertDeprecation(__name__ + '.static_method')

    def test_deprecate_class(self):
        df = DeprecatedClass()
        self.assertEqual(df.__doc__, 'Deprecated class.')
        self.assertDeprecation(__name__ + '.DeprecatedClass')


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
