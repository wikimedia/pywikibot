# -*- coding: utf-8  -*-
"""Tests for deprecation tools."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from pywikibot.tools import deprecated, deprecate_arg
from tests.aspects import unittest, DeprecationTestCase


@deprecated()
def deprecated_func(foo=None):
    """Deprecated function."""
    return foo


@deprecated
def deprecated_func2(foo=None):
    """Deprecated function."""
    return foo


@deprecated()
def deprecated_func_bad_args(self):
    """Deprecated function with arg 'self'."""
    return self


@deprecate_arg('bah', 'foo')
def deprecated_func_arg(foo=None):
    """Deprecated function with arg 'self'."""
    return foo


class DeprecatedMethodClass(object):

    """Class with methods deprecated."""

    @classmethod
    @deprecated()
    def class_method(cls, foo=None):
        return foo

    @staticmethod
    @deprecated()
    def static_method(foo=None):
        return foo

    @deprecated()
    def instance_method(self, foo=None):
        self.foo = foo
        return foo

    @deprecated
    def instance_method2(self, foo=None):
        self.foo = foo
        return foo

    def undecorated_method(self, foo=None):
        return foo

    @deprecate_arg('bah', 'foo')
    def deprecated_instance_method_arg(self, foo=None):
        self.foo = foo
        return foo

    @deprecate_arg('bah', 'foo')
    @deprecate_arg('bah2', 'foo2')
    def deprecated_instance_method_args(self, foo, foo2):
        self.foo = foo
        self.foo2 = foo2
        return (foo, foo2)

    @deprecated()
    @deprecate_arg('bah', 'foo')
    def deprecated_instance_method_and_arg(self, foo):
        self.foo = foo
        return foo

    @deprecate_arg('bah', 'foo')
    @deprecated()
    def deprecated_instance_method_and_arg2(self, foo):
        self.foo = foo
        return foo


@deprecated()
class DeprecatedClassNoInit(object):

    """Deprecated class."""

    pass


@deprecated()
class DeprecatedClass(object):

    """Deprecated class."""

    def __init__(self, foo=None):
        self.foo = foo


class DeprecatorTestCase(DeprecationTestCase):

    """Test cases for deprecation tools."""

    net = False

    @unittest.expectedFailure
    def test_deprecated_function_zero_arg(self):
        """Test @deprecated with functions, with zero arguments."""
        rv = deprecated_func()
        self.assertEqual(rv, None)
        self.assertDeprecation('deprecated_func is DEPRECATED.')

    def test_deprecated_function(self):
        """Test @deprecated with functions."""
        rv = deprecated_func('a')
        self.assertEqual(rv, 'a')
        self.assertDeprecation('str.deprecated_func is DEPRECATED.')

        DeprecatorTestCase._reset_messages()

        rv = deprecated_func(1)
        self.assertEqual(rv, 1)
        self.assertDeprecation('int.deprecated_func is DEPRECATED.')

    @unittest.expectedFailure
    def test_deprecated_function2(self):
        """Test @deprecated with functions."""
        rv = deprecated_func2('a')
        self.assertEqual(rv, 'a')
        self.assertDeprecation('str.deprecated_func is DEPRECATED.')

        DeprecatorTestCase._reset_messages()

        rv = deprecated_func2(1)
        self.assertEqual(rv, 1)
        self.assertDeprecation('int.deprecated_func is DEPRECATED.')

    def test_deprecated_function_bad_args(self):
        """Test weakness in @deprecated."""
        rv = deprecated_func_bad_args(None)
        self.assertEqual(rv, None)
        self.assertDeprecation('NoneType.deprecated_func_bad_args is DEPRECATED.')

        DeprecatorTestCase._reset_messages()

        rv = deprecated_func_bad_args('a')
        self.assertEqual(rv, 'a')
        self.assertDeprecation('str.deprecated_func_bad_args is DEPRECATED.')

        DeprecatorTestCase._reset_messages()

        rv = deprecated_func_bad_args(1)
        self.assertEqual(rv, 1)
        self.assertDeprecation('int.deprecated_func_bad_args is DEPRECATED.')

    def test_deprecated_instance_method(self):
        f = DeprecatedMethodClass()

        rv = f.instance_method()
        self.assertEqual(rv, None)
        self.assertEqual(f.foo, None)
        self.assertDeprecation('DeprecatedMethodClass.instance_method is DEPRECATED.')

        DeprecatorTestCase._reset_messages()

        rv = f.instance_method('a')
        self.assertEqual(rv, 'a')
        self.assertEqual(f.foo, 'a')
        self.assertDeprecation('DeprecatedMethodClass.instance_method is DEPRECATED.')

        DeprecatorTestCase._reset_messages()

        rv = f.instance_method(1)
        self.assertEqual(rv, 1)
        self.assertEqual(f.foo, 1)
        self.assertDeprecation('DeprecatedMethodClass.instance_method is DEPRECATED.')

    @unittest.expectedFailure
    def test_deprecated_instance_method2(self):
        f = DeprecatedMethodClass()

        rv = f.instance_method2()
        self.assertEqual(rv, None)
        self.assertEqual(f.foo, None)
        self.assertDeprecation('DeprecatedMethodClass.instance_method2 is DEPRECATED.')

    def test_deprecated_class_method(self):
        """Test @deprecated with class methods."""
        rv = DeprecatedMethodClass.class_method()
        self.assertEqual(rv, None)
        self.assertDeprecation('type.class_method is DEPRECATED.')

        DeprecatorTestCase._reset_messages()

        rv = DeprecatedMethodClass.class_method('a')
        self.assertEqual(rv, 'a')
        self.assertDeprecation('type.class_method is DEPRECATED.')

        DeprecatorTestCase._reset_messages()

        rv = DeprecatedMethodClass.class_method(1)
        self.assertEqual(rv, 1)
        self.assertDeprecation('type.class_method is DEPRECATED.')

    @unittest.expectedFailure
    def test_deprecated_static_method_zero_args(self):
        """Test @deprecated with static methods, with zero arguments."""
        rv = DeprecatedMethodClass.static_method()
        # raises: IndexError: tuple index out of range
        # because args[0] is used even if args is empty
        self.assertEqual(rv, None)
        self.assertDeprecation('DeprecatedMethodClass.static_method is DEPRECATED.')

    def test_deprecated_static_method(self):
        """Test @deprecated with static methods."""
        rv = DeprecatedMethodClass.static_method('a')
        self.assertEqual(rv, 'a')
        self.assertDeprecation('str.static_method is DEPRECATED.')

        DeprecatorTestCase._reset_messages()

        rv = DeprecatedMethodClass.static_method(1)
        self.assertEqual(rv, 1)
        self.assertDeprecation('int.static_method is DEPRECATED.')

    @unittest.expectedFailure
    def test_deprecate_class_zero_arg(self):
        """Test @deprecated with classes, without arguments."""
        df = DeprecatedClassNoInit()
        # raises: IndexError: tuple index out of range
        # because args[0] is used even if args is empty
        self.assertEqual(df.__doc__, 'Deprecated class.')
        self.assertDeprecation('DeprecatedClassNoInit is DEPRECATED.')

        DeprecatorTestCase._reset_messages()

        df = DeprecatedClass()
        self.assertEqual(df.foo, None)
        self.assertDeprecation('DeprecatedClass is DEPRECATED.')

    def test_deprecate_class(self):
        """Test @deprecated with classes."""
        df = DeprecatedClass('a')
        self.assertEqual(df.foo, 'a')
        self.assertDeprecation('str.DeprecatedClass is DEPRECATED.')

    def test_deprecated_function_arg(self):
        """Test @deprecate_arg with function arguments."""
        rv = deprecated_func_arg()
        self.assertEqual(rv, None)
        self.assertNoDeprecation()

        rv = deprecated_func_arg('a')
        self.assertEqual(rv, 'a')
        self.assertNoDeprecation()

        rv = deprecated_func_arg(bah='b')
        self.assertEqual(rv, 'b')
        self.assertDeprecation('bah argument of deprecated_func_arg is deprecated; use foo instead.')

        DeprecatorTestCase._reset_messages()

        rv = deprecated_func_arg(foo=1)
        self.assertEqual(rv, 1)
        self.assertNoDeprecation()

    def test_deprecated_instance_method_zero_arg(self):
        """Test @deprecate_arg with classes, without arguments."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_arg()
        self.assertEqual(rv, None)
        self.assertEqual(f.foo, None)
        self.assertNoDeprecation()

    def test_deprecated_instance_method_arg(self):
        """Test @deprecate_arg with instance methods."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_arg('a')
        self.assertEqual(rv, 'a')
        self.assertEqual(f.foo, 'a')
        self.assertNoDeprecation()

        rv = f.deprecated_instance_method_arg(bah='b')
        self.assertEqual(rv, 'b')
        self.assertEqual(f.foo, 'b')
        self.assertDeprecation(
            'bah argument of deprecated_instance_method_arg is deprecated; use foo instead.')

        DeprecatorTestCase._reset_messages()

        rv = f.deprecated_instance_method_arg(foo=1)
        self.assertEqual(rv, 1)
        self.assertEqual(f.foo, 1)
        self.assertNoDeprecation()

    def test_deprecated_instance_method_args(self):
        """Test @deprecate_arg with instance methods and two args."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_args('a', 'b')
        self.assertEqual(rv, ('a', 'b'))
        self.assertNoDeprecation()

        rv = f.deprecated_instance_method_args(bah='b', bah2='c')
        self.assertEqual(rv, ('b', 'c'))
        self.assertDeprecation(
            'bah argument of deprecated_instance_method_args is deprecated; use foo instead.')
        self.assertDeprecation(
            'bah2 argument of deprecated_instance_method_args is deprecated; use foo2 instead.')

        DeprecatorTestCase._reset_messages()

        rv = f.deprecated_instance_method_args(foo='b', bah2='c')
        self.assertEqual(rv, ('b', 'c'))
        self.assertNoDeprecation(
            'bah argument of deprecated_instance_method_args is deprecated; use foo instead.')
        self.assertDeprecation(
            'bah2 argument of deprecated_instance_method_args is deprecated; use foo2 instead.')

        DeprecatorTestCase._reset_messages()

        rv = f.deprecated_instance_method_args(foo2='c', bah='b')
        self.assertEqual(rv, ('b', 'c'))
        self.assertDeprecation(
            'bah argument of deprecated_instance_method_args is deprecated; use foo instead.')
        self.assertNoDeprecation(
            'bah2 argument of deprecated_instance_method_args is deprecated; use foo2 instead.')

        DeprecatorTestCase._reset_messages()

        rv = f.deprecated_instance_method_args(foo=1, foo2=2)
        self.assertEqual(rv, (1, 2))
        self.assertNoDeprecation()

    def test_deprecated_instance_method_and_arg(self):
        """Test @deprecate_arg and @deprecated with instance methods."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_and_arg('a')
        self.assertEqual(rv, 'a')
        self.assertEqual(f.foo, 'a')
        self.assertDeprecation(
            'DeprecatedMethodClass.deprecated_instance_method_and_arg is DEPRECATED.')
        self.assertNoDeprecation(
            'bah argument of deprecated_instance_method_and_arg is deprecated; use foo instead.')

        DeprecatorTestCase._reset_messages()

        rv = f.deprecated_instance_method_and_arg(bah='b')
        self.assertEqual(rv, 'b')
        self.assertEqual(f.foo, 'b')
        self.assertDeprecation(
            'DeprecatedMethodClass.deprecated_instance_method_and_arg is DEPRECATED.')
        self.assertDeprecation(
            'bah argument of deprecated_instance_method_and_arg is deprecated; use foo instead.')

        DeprecatorTestCase._reset_messages()

        rv = f.deprecated_instance_method_and_arg(foo=1)
        self.assertEqual(rv, 1)
        self.assertEqual(f.foo, 1)
        self.assertDeprecation(
            'DeprecatedMethodClass.deprecated_instance_method_and_arg is DEPRECATED.')
        self.assertNoDeprecation(
            'bah argument of deprecated_instance_method_and_arg is deprecated; use foo instead.')

    def test_deprecated_instance_method_and_arg2(self):
        """Test @deprecate_arg and @deprecated with instance methods."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_and_arg2('a')
        self.assertEqual(rv, 'a')
        self.assertEqual(f.foo, 'a')
        self.assertDeprecation(
            'DeprecatedMethodClass.deprecated_instance_method_and_arg2 is DEPRECATED.')
        self.assertNoDeprecation(
            'bah argument of deprecated_instance_method_and_arg2 is deprecated; use foo instead.')

        DeprecatorTestCase._reset_messages()

        rv = f.deprecated_instance_method_and_arg2(bah='b')
        self.assertEqual(rv, 'b')
        self.assertEqual(f.foo, 'b')
        self.assertDeprecation(
            'DeprecatedMethodClass.deprecated_instance_method_and_arg2 is DEPRECATED.')
        self.assertDeprecation(
            'bah argument of deprecated_instance_method_and_arg2 is deprecated; use foo instead.')

        DeprecatorTestCase._reset_messages()

        rv = f.deprecated_instance_method_and_arg2(foo=1)
        self.assertEqual(rv, 1)
        self.assertEqual(f.foo, 1)
        self.assertDeprecation(
            'DeprecatedMethodClass.deprecated_instance_method_and_arg2 is DEPRECATED.')
        self.assertNoDeprecation(
            'bah argument of deprecated_instance_method_and_arg2 is deprecated; use foo instead.')


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
