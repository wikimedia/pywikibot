#!/usr/bin/env python3
"""Tests for deprecation tools."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot.tools import (
    add_full_name,
    deprecate_arg,
    deprecated,
    deprecated_args,
    remove_last_args,
)
from tests.aspects import DeprecationTestCase


@add_full_name
def noop(foo=None):
    """Dummy decorator."""
    def decorator(obj):
        def wrapper(*args, **kwargs):
            raise Exception(obj.__full_name__)
        return wrapper
    return decorator


@add_full_name
def noop2():
    """Dummy decorator."""
    def decorator(obj):
        def wrapper(*args, **kwargs):
            raise Exception(obj.__full_name__)
        return wrapper
    return decorator


@noop()
def decorated_func():
    """Test dummy decorator."""


@noop(foo='bar')
def decorated_func2():
    """Test dummy decorator."""


@noop('baz')
def decorated_func3():
    """Test dummy decorator."""


class DecoratorFullNameTestCase(DeprecationTestCase):

    """Class with methods deprecated."""

    net = False

    def test_add_full_name_decorator(self):
        """Test add_decorated_full_name() method."""
        with self.assertRaisesRegex(Exception,
                                    __name__ + '.decorated_func'):
            decorated_func()
        with self.assertRaisesRegex(Exception,
                                    __name__ + '.decorated_func2'):
            decorated_func2()
        with self.assertRaisesRegex(Exception,
                                    __name__ + '.decorated_func3'):
            decorated_func3()


@deprecated()
def deprecated_func(foo=None):
    """Deprecated function."""
    return foo


@deprecated()
def deprecated_func_docstring(foo=None):
    """DEPRECATED. Deprecated function."""
    return foo


@deprecated
def deprecated_func2(foo=None):
    """Deprecated function."""
    return foo


@deprecated
def deprecated_func2_docstring(foo=None):
    """DEPRECATED, don't use this. Deprecated function."""
    return foo


@deprecated(instead='baz')
def deprecated_func_instead(foo=None):
    """Deprecated function."""
    return foo


@deprecated(instead='baz')
def deprecated_func_instead_docstring(foo=None):
    """DEPRECATED, don't use this. Deprecated function."""
    return foo


@deprecated()
def deprecated_func_bad_args(self):
    """Deprecated function with arg 'self'."""
    return self


@deprecate_arg('bah', 'foo')
def deprecated_func_arg(foo=None):
    """Deprecated arg 'bah'."""
    return foo


@deprecated
def deprecated_func_docstring_arg(foo=None):
    """:param foo: Foo. DEPRECATED."""
    return foo


@deprecated
def deprecated_func_docstring_arg2(foo=None):
    """
    DEPRECATED.

    :param foo: Foo. DEPRECATED.
    """
    return foo


@deprecated_args(bah='foo')
def deprecated_func_arg2(foo=None):
    """Test deprecated_args with one rename."""
    return foo


@deprecated_args(bah='foo', silent=False, loud=True, old=None)
def deprecated_func_arg3(foo=None):
    """Test deprecated_args with three drops and one rename."""
    return foo


@remove_last_args(['foo', 'bar'])
def deprecated_all():
    """Test remove_last_args with all args removed."""
    return None


@remove_last_args(['bar'])
def deprecated_all2(foo):
    """Test remove_last_args with one arg removed."""
    return foo


class DeprecatedMethodClass:

    """Class with methods deprecated."""

    @classmethod
    @deprecated()
    def class_method(cls, foo=None):
        """Deprecated class method."""
        return foo

    @staticmethod
    @deprecated()
    def static_method(foo=None):
        """Deprecated static method."""
        return foo

    @deprecated()
    def instance_method(self, foo=None):
        """Deprecated instance method."""
        self.foo = foo
        return foo

    @deprecated
    def instance_method2(self, foo=None):
        """Another deprecated instance method."""
        self.foo = foo
        return foo

    def undecorated_method(self, foo=None):
        """Not deprecated instance method."""
        return foo

    @deprecate_arg('bah', 'foo')
    def deprecated_instance_method_arg(self, foo=None):
        """Instance method with deprecated parameters."""
        self.foo = foo
        return foo

    @deprecate_arg('bah', 'foo')
    @deprecate_arg('bah2', 'foo2')
    @deprecate_arg('bah3', 'foo3')
    @deprecate_arg('bah4', 'foo4')
    def deprecated_instance_method_args(self, foo, foo2, foo3=None, foo4=None):
        """Method with many decorators to verify wrapping depth formula."""
        self.foo = foo
        self.foo2 = foo2
        return (foo, foo2)

    @deprecated_args(bah='foo', bah2='foo2')
    def deprecated_instance_method_args_multi(self, foo, foo2):
        """Instance method with multiple deprecated parameters."""
        self.foo = foo
        self.foo2 = foo2
        return (foo, foo2)

    @deprecated()
    @deprecate_arg('bah', 'foo')
    def deprecated_instance_method_and_arg(self, foo):
        """Deprecated instance method with deprecated parameters."""
        self.foo = foo
        return foo

    @deprecate_arg('bah', 'foo')
    @deprecated()
    def deprecated_instance_method_and_arg2(self, foo):
        """Deprecating decorators in reverse order."""
        self.foo = foo
        return foo

    @remove_last_args(['foo', 'bar'])
    def deprecated_all(self):
        """Deprecating positional parameters."""
        return None

    @remove_last_args(['bar'])
    def deprecated_all2(self, foo):
        """Deprecating last positional parameter."""
        return foo


@deprecated()
class DeprecatedClassNoInit:

    """Deprecated class."""


@deprecated()
class DeprecatedClass:

    """Deprecated class."""

    def __init__(self, foo=None):
        """Initializer."""
        self.foo = foo


class DeprecatorTestCase(DeprecationTestCase):

    """Test cases for deprecation tools."""

    net = False

    def test_deprecated_function_zero_arg(self):
        """Test @deprecated with functions, with zero arguments."""
        rv = deprecated_func()
        self.assertIsNone(rv)
        self.assertOneDeprecationParts(__name__ + '.deprecated_func')

    def test_deprecated_function(self):
        """Test @deprecated with functions."""
        rv = deprecated_func('a')
        self.assertEqual(rv, 'a')
        self.assertOneDeprecationParts(__name__ + '.deprecated_func')

        rv = deprecated_func(1)
        self.assertEqual(rv, 1)
        self.assertOneDeprecationParts(__name__ + '.deprecated_func')

    def test_deprecated_function2(self):
        """Test @deprecated with functions."""
        rv = deprecated_func2('a')
        self.assertEqual(rv, 'a')
        self.assertOneDeprecationParts(__name__ + '.deprecated_func2')

        rv = deprecated_func2(1)
        self.assertEqual(rv, 1)
        self.assertOneDeprecationParts(__name__ + '.deprecated_func2')

    def test_deprecated_function_instead(self):
        """Test @deprecated with functions, using instead."""
        rv = deprecated_func_instead('a')
        self.assertEqual(rv, 'a')
        self.assertOneDeprecationParts(__name__ + '.deprecated_func_instead',
                                       'baz')

    def test_deprecated_function_docstring(self):
        """Test @deprecated docstring modification."""
        testcases = [
            (deprecated_func, 'Deprecated.\n\nDeprecated function.'),
            (deprecated_func_docstring, 'DEPRECATED. Deprecated function.'),
            (deprecated_func2, 'Deprecated.\n\nDeprecated function.'),
            (deprecated_func2_docstring, "DEPRECATED, don't use this. "
             'Deprecated function.'),
            (deprecated_func_instead, 'Deprecated; use baz instead.\n\n'
             'Deprecated function.'),
            (deprecated_func_instead_docstring, "DEPRECATED, don't use "
             'this. Deprecated function.'),
            (deprecated_func_docstring_arg, 'Deprecated.\n\n'
             ':param foo: Foo. DEPRECATED.'),
            (deprecated_func_docstring_arg2, '\n    DEPRECATED.\n\n'
             '    :param foo: Foo. DEPRECATED.\n    '),
        ]
        for rv, doc in testcases:
            with self.subTest(function=rv.__name__):
                self.assertEqual(rv.__doc__, doc)

    def test_deprecated_function_bad_args(self):
        """Test @deprecated function with bad arguments."""
        rv = deprecated_func_bad_args(None)
        self.assertIsNone(rv)
        self.assertOneDeprecationParts(__name__ + '.deprecated_func_bad_args')

        rv = deprecated_func_bad_args('a')
        self.assertEqual(rv, 'a')
        self.assertOneDeprecationParts(__name__ + '.deprecated_func_bad_args')

        rv = deprecated_func_bad_args(1)
        self.assertEqual(rv, 1)
        self.assertOneDeprecationParts(__name__ + '.deprecated_func_bad_args')

        f = DeprecatedMethodClass()
        rv = deprecated_func_bad_args(f)
        self.assertEqual(rv, f)
        self.assertOneDeprecationParts(__name__ + '.deprecated_func_bad_args')

    def test_deprecated_instance_method(self):
        """Test @deprecated instance method."""
        f = DeprecatedMethodClass()

        rv = f.instance_method()
        self.assertIsNone(rv)
        self.assertIsNone(f.foo)
        self.assertOneDeprecationParts(
            __name__ + '.DeprecatedMethodClass.instance_method')

        rv = f.instance_method('a')
        self.assertEqual(rv, 'a')
        self.assertEqual(f.foo, 'a')
        self.assertOneDeprecationParts(
            __name__ + '.DeprecatedMethodClass.instance_method')

        rv = f.instance_method(1)
        self.assertEqual(rv, 1)
        self.assertEqual(f.foo, 1)
        self.assertOneDeprecationParts(
            __name__ + '.DeprecatedMethodClass.instance_method')

    def test_deprecated_instance_method2(self):
        """Test @deprecated instance method 2."""
        f = DeprecatedMethodClass()

        rv = f.instance_method2()
        self.assertIsNone(rv)
        self.assertIsNone(f.foo)
        self.assertOneDeprecationParts(
            __name__ + '.DeprecatedMethodClass.instance_method2')

    def test_deprecated_class_method(self):
        """Test @deprecated with class methods."""
        rv = DeprecatedMethodClass.class_method()
        self.assertIsNone(rv)
        self.assertOneDeprecationParts(
            __name__ + '.DeprecatedMethodClass.class_method')

        rv = DeprecatedMethodClass.class_method('a')
        self.assertEqual(rv, 'a')
        self.assertOneDeprecationParts(
            __name__ + '.DeprecatedMethodClass.class_method')

        rv = DeprecatedMethodClass.class_method(1)
        self.assertEqual(rv, 1)
        self.assertOneDeprecationParts(
            __name__ + '.DeprecatedMethodClass.class_method')

    def test_deprecated_static_method_zero_args(self):
        """Test @deprecated with static methods, with zero arguments."""
        rv = DeprecatedMethodClass.static_method()
        self.assertIsNone(rv)
        self.assertOneDeprecationParts(
            __name__ + '.DeprecatedMethodClass.static_method')

    def test_deprecated_static_method(self):
        """Test @deprecated with static methods."""
        rv = DeprecatedMethodClass.static_method('a')
        self.assertEqual(rv, 'a')
        self.assertOneDeprecationParts(
            __name__ + '.DeprecatedMethodClass.static_method')

        rv = DeprecatedMethodClass.static_method(1)
        self.assertEqual(rv, 1)
        self.assertOneDeprecationParts(
            __name__ + '.DeprecatedMethodClass.static_method')

    def test_deprecate_class_zero_arg(self):
        """Test @deprecated with classes, without arguments."""
        df = DeprecatedClassNoInit()
        self.assertEqual(df.__doc__, 'Deprecated class.')
        self.assertOneDeprecationParts(__name__ + '.DeprecatedClassNoInit')

        df = DeprecatedClass()
        self.assertIsNone(df.foo)
        self.assertOneDeprecationParts(__name__ + '.DeprecatedClass')

    def test_deprecate_class(self):
        """Test @deprecated with classes."""
        df = DeprecatedClass('a')
        self.assertEqual(df.foo, 'a')
        self.assertOneDeprecationParts(__name__ + '.DeprecatedClass')

    def test_deprecate_function_arg(self):
        """Test @deprecated function argument."""
        def tests(func):
            """Test function."""
            rv = func()
            self.assertIsNone(rv)
            self.assertNoDeprecation()

            rv = func('a')
            self.assertEqual(rv, 'a')
            self.assertNoDeprecation()

            rv = func(bah='b')
            self.assertEqual(rv, 'b')
            self.assertOneDeprecationParts(
                'bah argument of ' + __name__ + '.' + func.__name__, 'foo')

            self._reset_messages()

            rv = func(foo=1)
            self.assertEqual(rv, 1)
            self.assertNoDeprecation()

            with self.assertRaisesRegex(
                    TypeError,
                    r'deprecated_func_arg2?\(\) got multiple values for '
                    "(keyword )?argument 'foo'"):
                func('a', bah='b')

            self._reset_messages()

        tests(deprecated_func_arg)
        tests(deprecated_func_arg2)

    def test_deprecate_and_remove_function_args(self):
        """Test @deprecated and removed function argument."""
        rv = deprecated_func_arg3()
        self.assertIsNone(rv)
        self.assertNoDeprecation()

        rv = deprecated_func_arg3(2)
        self.assertEqual(rv, 2)
        self.assertNoDeprecation()

        rv = deprecated_func_arg3(foo=1, silent=42)
        self.assertEqual(rv, 1)
        self.assertDeprecationClass(PendingDeprecationWarning)
        self.assertOneDeprecationParts(
            'silent argument of ' + __name__ + '.deprecated_func_arg3')

        rv = deprecated_func_arg3(3, loud='3')
        self.assertEqual(rv, 3)
        self.assertOneDeprecationParts(
            'loud argument of ' + __name__ + '.deprecated_func_arg3')

        rv = deprecated_func_arg3(4, old='4')
        self.assertEqual(rv, 4)
        self.assertOneDeprecationParts(
            'old argument of ' + __name__ + '.deprecated_func_arg3')

    def test_function_remove_last_args(self):
        """Test @remove_last_args on functions."""
        rv = deprecated_all()
        self.assertIsNone(rv)
        self.assertNoDeprecation()

        rv = deprecated_all(foo=42)
        self.assertIsNone(rv)
        self.assertDeprecation(
            "The trailing arguments ('foo', 'bar') of {}.deprecated_all are "
            "deprecated. The value(s) provided for 'foo' have been "
            'dropped.'.format(__name__))

        self._reset_messages()

        rv = deprecated_all(42)
        self.assertIsNone(rv)
        self.assertDeprecation(
            "The trailing arguments ('foo', 'bar') of {}.deprecated_all are "
            "deprecated. The value(s) provided for 'foo' have been "
            'dropped.'.format(__name__))

        self._reset_messages()

        rv = deprecated_all(foo=42, bar=47)
        self.assertIsNone(rv)
        self.assertDeprecation(
            "The trailing arguments ('foo', 'bar') of {}.deprecated_all are "
            "deprecated. The value(s) provided for 'foo', 'bar' have been "
            'dropped.'.format(__name__))

        self._reset_messages()

        rv = deprecated_all(42, 47)
        self.assertIsNone(rv)
        self.assertDeprecation(
            "The trailing arguments ('foo', 'bar') of {}.deprecated_all are "
            "deprecated. The value(s) provided for 'foo', 'bar' have been "
            'dropped.'.format(__name__))

        self._reset_messages()

        rv = deprecated_all2(foo=42)
        self.assertEqual(rv, 42)
        self.assertNoDeprecation()

        rv = deprecated_all2(42)
        self.assertEqual(rv, 42)
        self.assertNoDeprecation()

        rv = deprecated_all2(42, bar=47)
        self.assertEqual(rv, 42)
        self.assertDeprecation(
            "The trailing arguments ('bar') of {}.deprecated_all2 are "
            "deprecated. The value(s) provided for 'bar' have been "
            'dropped.'.format(__name__))

        self._reset_messages()

    def test_method_remove_last_args(self):
        """Test @remove_last_args on functions."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_all()
        self.assertIsNone(rv)
        self.assertNoDeprecation()

        rv = f.deprecated_all(foo=42)
        self.assertIsNone(rv)
        self.assertDeprecation(
            "The trailing arguments ('foo', 'bar') of "
            '{}.DeprecatedMethodClass.deprecated_all are deprecated. '
            "The value(s) provided for 'foo' have been dropped."
            .format(__name__))

        self._reset_messages()

        rv = f.deprecated_all(42)
        self.assertIsNone(rv)
        self.assertDeprecation(
            "The trailing arguments ('foo', 'bar') of "
            '{}.DeprecatedMethodClass.deprecated_all are deprecated. '
            "The value(s) provided for 'foo' have been dropped."
            .format(__name__))

        self._reset_messages()

        rv = f.deprecated_all(foo=42, bar=47)
        self.assertIsNone(rv)
        self.assertDeprecation(
            "The trailing arguments ('foo', 'bar') of "
            '{}.DeprecatedMethodClass.deprecated_all are deprecated. The '
            "value(s) provided for 'foo', 'bar' have been dropped."
            .format(__name__))

        self._reset_messages()

        rv = f.deprecated_all(42, 47)
        self.assertIsNone(rv)
        self.assertDeprecation(
            "The trailing arguments ('foo', 'bar') of "
            '{}.DeprecatedMethodClass.deprecated_all are deprecated. The '
            "value(s) provided for 'foo', 'bar' have been dropped."
            .format(__name__))

        self._reset_messages()

        rv = f.deprecated_all2(foo=42)
        self.assertEqual(rv, 42)
        self.assertNoDeprecation()

        rv = f.deprecated_all2(42)
        self.assertEqual(rv, 42)
        self.assertNoDeprecation()

        rv = f.deprecated_all2(42, bar=47)
        self.assertEqual(rv, 42)
        self.assertDeprecation(
            "The trailing arguments ('bar') of "
            '{}.DeprecatedMethodClass.deprecated_all2 are deprecated. '
            "The value(s) provided for 'bar' have been dropped."
            .format(__name__))

    def test_remove_last_args_invalid(self):
        """Test invalid @remove_last_args on functions."""
        with self.assertRaisesRegex(
                TypeError,
                r'deprecated_all2\(\) missing 1 required positional argument: '
                r"'foo'"):
            deprecated_all2()

        with self.assertRaisesRegex(
                TypeError,
                r'deprecated_all2\(\) got an unexpected keyword argument '
                r"'hello'"):
            deprecated_all2(hello='world')

        with self.assertRaisesRegex(
                TypeError,
                r'deprecated_all2\(\) takes (exactly )?1 (positional )?'
                r'argument (but 2 were given|\(2 given\))'):
            deprecated_all2(1, 2, 3)

        f = DeprecatedMethodClass()

        with self.assertRaisesRegex(
                TypeError,
                r'deprecated_all2\(\) missing 1 required positional argument: '
                r"'foo'"):
            f.deprecated_all2()

        with self.assertRaisesRegex(
                TypeError,
                r'deprecated_all2\(\) got an unexpected keyword argument '
                r"'hello'"):
            f.deprecated_all2(hello='world')

        with self.assertRaisesRegex(
                TypeError,
                r'deprecated_all2\(\) takes (exactly )?2 (positional )?'
                r'arguments (but 3 were given|\(3 given\))'):
            f.deprecated_all2(1, 2, 3)

    def test_deprecated_instance_method_zero_arg(self):
        """Test @deprecate_arg with classes, without arguments."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_arg()
        self.assertIsNone(rv)
        self.assertIsNone(f.foo)
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
        self.assertOneDeprecationParts(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.'
            'deprecated_instance_method_arg', 'foo')

        self._reset_messages()

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
        self.assertDeprecationParts(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.'
            'deprecated_instance_method_args', 'foo')
        self.assertDeprecationParts(
            'bah2 argument of ' + __name__ + '.DeprecatedMethodClass.'
            'deprecated_instance_method_args', 'foo2')

        self._reset_messages()

        rv = f.deprecated_instance_method_args(foo='b', bah2='c')
        self.assertEqual(rv, ('b', 'c'))
        self.assertOneDeprecationParts(
            'bah2 argument of ' + __name__ + '.DeprecatedMethodClass.'
            'deprecated_instance_method_args', 'foo2')

        rv = f.deprecated_instance_method_args(foo2='c', bah='b')
        self.assertEqual(rv, ('b', 'c'))
        self.assertOneDeprecationParts(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.'
            'deprecated_instance_method_args', 'foo')

        rv = f.deprecated_instance_method_args(foo=1, foo2=2)
        self.assertEqual(rv, (1, 2))
        self.assertNoDeprecation()

    def test_deprecated_instance_method_args_multi(self):
        """Test @deprecated_args with instance methods and two args."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_args_multi('a', 'b')
        self.assertEqual(rv, ('a', 'b'))
        self.assertNoDeprecation()

        rv = f.deprecated_instance_method_args_multi(bah='b', bah2='c')
        self.assertEqual(rv, ('b', 'c'))
        self.assertDeprecationParts(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.'
            'deprecated_instance_method_args_multi', 'foo')
        self.assertDeprecationParts(
            'bah2 argument of ' + __name__ + '.DeprecatedMethodClass.'
            'deprecated_instance_method_args_multi', 'foo2')

        self._reset_messages()

        rv = f.deprecated_instance_method_args_multi(foo='b', bah2='c')
        self.assertEqual(rv, ('b', 'c'))
        self.assertOneDeprecationParts(
            'bah2 argument of ' + __name__ + '.DeprecatedMethodClass.'
            'deprecated_instance_method_args_multi', 'foo2')

        rv = f.deprecated_instance_method_args_multi(foo2='c', bah='b')
        self.assertEqual(rv, ('b', 'c'))
        self.assertOneDeprecationParts(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.'
            'deprecated_instance_method_args_multi', 'foo')

        rv = f.deprecated_instance_method_args_multi(foo=1, foo2=2)
        self.assertEqual(rv, (1, 2))
        self.assertNoDeprecation()

    def test_deprecated_instance_method_and_arg(self):
        """Test @deprecate_arg and @deprecated with instance methods."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_and_arg('a')
        self.assertEqual(rv, 'a')
        self.assertEqual(f.foo, 'a')
        self.assertOneDeprecationParts(
            __name__
            + '.DeprecatedMethodClass.deprecated_instance_method_and_arg')

        rv = f.deprecated_instance_method_and_arg(bah='b')
        self.assertEqual(rv, 'b')
        self.assertEqual(f.foo, 'b')
        self.assertDeprecationParts(
            __name__
            + '.DeprecatedMethodClass.deprecated_instance_method_and_arg')
        self.assertDeprecationParts(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.'
            'deprecated_instance_method_and_arg', 'foo')

        self._reset_messages()

        rv = f.deprecated_instance_method_and_arg(foo=1)
        self.assertEqual(rv, 1)
        self.assertEqual(f.foo, 1)
        self.assertOneDeprecationParts(
            __name__
            + '.DeprecatedMethodClass.deprecated_instance_method_and_arg')

    def test_deprecated_instance_method_and_arg2(self):
        """Test @deprecated and @deprecate_arg with instance methods."""
        f = DeprecatedMethodClass()

        rv = f.deprecated_instance_method_and_arg2('a')
        self.assertEqual(rv, 'a')
        self.assertEqual(f.foo, 'a')
        self.assertOneDeprecationParts(
            __name__
            + '.DeprecatedMethodClass.deprecated_instance_method_and_arg2')

        rv = f.deprecated_instance_method_and_arg2(bah='b')
        self.assertEqual(rv, 'b')
        self.assertEqual(f.foo, 'b')
        self.assertDeprecationParts(
            __name__
            + '.DeprecatedMethodClass.deprecated_instance_method_and_arg2')
        self.assertDeprecationParts(
            'bah argument of ' + __name__ + '.DeprecatedMethodClass.'
            'deprecated_instance_method_and_arg2', 'foo')

        self._reset_messages()

        rv = f.deprecated_instance_method_and_arg2(foo=1)
        self.assertEqual(rv, 1)
        self.assertEqual(f.foo, 1)
        self.assertOneDeprecationParts(
            __name__
            + '.DeprecatedMethodClass.deprecated_instance_method_and_arg2')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
