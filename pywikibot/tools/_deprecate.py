"""Module providing deprecation decorators.

Decorator functions without parameters are _invoked_ differently from
decorator functions with function syntax. For example, @deprecated causes
a different invocation to @deprecated().

The former is invoked with the decorated function as args[0].
The latter is invoked with the decorator arguments as ``*args`` &
``**kwargs``, and it must return a callable which will be invoked with
the decorated function as args[0].

The follow deprecators may support both syntax, e.g. @deprecated and
@deprecated() both work. In order to achieve that, the code inspects
args[0] to see if it callable. Therefore, a decorator must not accept
only one arg, and that arg be a callable, as it will be detected as
a deprecator without any arguments.

.. versionchanged:: 6.4
   deprecation decorators moved to _deprecate submodule
"""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import collections
import inspect
import re
import sys
import types
from contextlib import suppress
from importlib import import_module
from inspect import getfullargspec
from typing import Any, Optional
from warnings import warn


class _NotImplementedWarning(RuntimeWarning):

    """Feature that is no longer implemented.

    .. versionadded:: 3.0
    """


def add_decorated_full_name(obj, stacklevel: int = 1) -> None:
    """Extract full object name, including class, and store in __full_name__.

    This must be done on all decorators that are chained together, otherwise
    the second decorator will have the wrong full name.

    :param obj: An object being decorated
    :type obj: object
    :param stacklevel: level to use
    """
    if hasattr(obj, '__full_name__'):
        return
    # The current frame is add_decorated_full_name
    # The next frame is the decorator
    # The next frame is the object being decorated
    frame = sys._getframe(stacklevel + 1)
    class_name = frame.f_code.co_name
    if class_name and class_name != '<module>':
        obj.__full_name__ = '{}.{}.{}'.format(obj.__module__,
                                              class_name, obj.__name__)
    else:
        obj.__full_name__ = '{}.{}'.format(obj.__module__, obj.__name__)


def manage_wrapping(wrapper, obj) -> None:
    """Add attributes to wrapper and wrapped functions.

    .. versionadded:: 3.0
    """
    wrapper.__doc__ = obj.__doc__
    wrapper.__name__ = obj.__name__
    wrapper.__module__ = obj.__module__
    wrapper.__signature__ = inspect.signature(obj)

    if not hasattr(obj, '__full_name__'):
        add_decorated_full_name(obj, 2)
    wrapper.__full_name__ = obj.__full_name__

    # Use the previous wrappers depth, if it exists
    wrapper.__depth__ = getattr(obj, '__depth__', 0) + 1

    # Obtain the wrapped object from the previous wrapper
    wrapped = getattr(obj, '__wrapped__', obj)
    wrapper.__wrapped__ = wrapped

    # Increment the number of wrappers
    if hasattr(wrapped, '__wrappers__'):
        wrapped.__wrappers__ += 1
    else:
        wrapped.__wrappers__ = 1


def get_wrapper_depth(wrapper):
    """Return depth of wrapper function.

    .. versionadded:: 3.0
    """
    return wrapper.__wrapped__.__wrappers__ + (1 - wrapper.__depth__)


def add_full_name(obj):
    """
    A decorator to add __full_name__ to the function being decorated.

    This should be done for all decorators used in pywikibot, as any
    decorator that does not add __full_name__ will prevent other
    decorators in the same chain from being able to obtain it.

    This can be used to monkey-patch decorators in other modules.
    e.g.
    <xyz>.foo = add_full_name(<xyz>.foo)

    :param obj: The function to decorate
    :type obj: callable
    :return: decorating function
    :rtype: function
    """
    def outer_wrapper(*outer_args, **outer_kwargs):
        """Outer wrapper.

        The outer wrapper may be the replacement function if the decorated
        decorator was called without arguments, or the replacement decorator
        if the decorated decorator was called without arguments.

        :param outer_args: args
        :param outer_kwargs: kwargs
        """
        def inner_wrapper(*args, **kwargs):
            """Replacement function.

            If the decorator supported arguments, they are in outer_args,
            and this wrapper is used to process the args which belong to
            the function that the decorated decorator was decorating.

            :param args: args passed to the decorated function.
            :param kwargs: kwargs passed to the decorated function.
            """
            add_decorated_full_name(args[0])
            return obj(*outer_args, **outer_kwargs)(*args, **kwargs)

        inner_wrapper.__doc__ = obj.__doc__
        inner_wrapper.__name__ = obj.__name__
        inner_wrapper.__module__ = obj.__module__
        inner_wrapper.__signature__ = inspect.signature(obj)

        # The decorator being decorated may have args, so both
        # syntax need to be supported.
        if (len(outer_args) == 1 and not outer_kwargs
                and callable(outer_args[0])):
            add_decorated_full_name(outer_args[0])
            return obj(outer_args[0])
        return inner_wrapper

    if not __debug__:
        return obj

    return outer_wrapper


def _build_msg_string(instead: str, since: str) -> str:
    """Build a deprecation warning message format string.

    .. versionadded:: 3.0

    .. versionchanged:: 7.0
       `since`parameter must be a release number, not a timestamp.

    :param instead: suggested replacement for the deprecated object
    :param since: a version string string when the method was deprecated
    """
    if since and '.' not in since:
        raise ValueError('{} is not a valid release number'.format(since))

    if instead:
        msg = '{{0}} is deprecated{since}; use {{1}} instead.'
    else:
        msg = '{{0}} is deprecated{since}.'
    return msg.format(since=' since release ' + since if since else '')


def issue_deprecation_warning(name: str, instead: str = '', depth: int = 2,
                              warning_class=None, since: str = '') -> None:
    """Issue a deprecation warning.

    .. versionchanged:: 7.0
       `since` parameter must be a release number, not a timestamp.

    :param name: the name of the deprecated object
    :param instead: suggested replacement for the deprecated object
    :param depth: depth + 1 will be used as stacklevel for the warnings
    :param warning_class: a warning class (category) to be used, defaults to
        FutureWarning
    :type warning_class: type
    :param since: a version string string when the method was deprecated
    """
    msg = _build_msg_string(instead, since)
    if warning_class is None:
        warning_class = (FutureWarning
                         if instead else _NotImplementedWarning)
    warn(msg.format(name, instead), warning_class, depth + 1)


@add_full_name
def deprecated(*args, **kwargs):
    """Decorator to output a deprecation warning.

    .. versionchanged:: 7.0
       `since` keyword must be a release number, not a timestamp.

    :keyword instead: if provided, will be used to specify the replacement
    :type instead: str
    :keyword since: a version string string when the method was deprecated
    :type since: str
    :keyword future_warning: if True a FutureWarning will be thrown,
        otherwise it provides a DeprecationWarning
    :type future_warning: bool
    """
    def decorator(obj):
        """Outer wrapper.

        The outer wrapper is used to create the decorating wrapper.

        :param obj: function being wrapped
        :type obj: object
        """
        def wrapper(*args, **kwargs):
            """Replacement function.

            :param args: args passed to the decorated function.
            :param kwargs: kwargs passed to the decorated function.
            :return: the value returned by the decorated function
            :rtype: any
            """
            name = obj.__full_name__
            depth = get_wrapper_depth(wrapper) + 1
            issue_deprecation_warning(
                name, instead, depth, since=since,
                warning_class=None if future_warning else DeprecationWarning)
            return obj(*args, **kwargs)

        def add_docstring(wrapper) -> None:
            """Add a Deprecated notice to the docstring."""
            deprecation_notice = 'Deprecated'
            if instead:
                deprecation_notice += '; use ' + instead + ' instead'
            deprecation_notice += '.\n\n'
            if wrapper.__doc__:  # Append old docstring after the notice
                wrapper.__doc__ = deprecation_notice + wrapper.__doc__
            else:
                wrapper.__doc__ = deprecation_notice

        if not __debug__:
            return obj

        manage_wrapping(wrapper, obj)

        # Regular expression to find existing deprecation notices
        deprecated_notice = re.compile(r'(^|\s)DEPRECATED[.:;,]',
                                       re.IGNORECASE)

        # Add the deprecation notice to the docstring if not present
        if not wrapper.__doc__:
            add_docstring(wrapper)
        else:
            if not deprecated_notice.search(wrapper.__doc__):
                add_docstring(wrapper)
            else:
                # Get docstring up to :params so deprecation notices for
                # parameters don't disrupt it
                trim_params = re.compile(r'^.*?((?=:param)|$)', re.DOTALL)
                trimmed_doc = trim_params.match(wrapper.__doc__).group(0)

                if not deprecated_notice.search(trimmed_doc):  # No notice
                    add_docstring(wrapper)

        return wrapper

    since = kwargs.pop('since', '')
    future_warning = kwargs.pop('future_warning', True)
    without_parameters = len(args) == 1 and not kwargs and callable(args[0])
    if 'instead' in kwargs:
        instead = kwargs['instead']
    elif not without_parameters and len(args) == 1:
        instead = args[0]
    else:
        instead = False

    # When called as @deprecated, return a replacement function
    if without_parameters:
        if not __debug__:
            return args[0]

        return decorator(args[0])

    # Otherwise return a decorator, which returns a replacement function
    return decorator


def deprecate_arg(old_arg: str, new_arg):
    """Decorator to declare old_arg deprecated and replace it with new_arg.

    Usage:

        @deprecate_arg('foo', 'bar')
        def my_function(bar='baz'): pass
        # replaces 'foo' keyword by 'bar' used by my_function

        @deprecare_arg('foo', None)
        def my_function(): pass
        # ignores 'foo' keyword no longer used by my_function

    deprecated_args decorator should be used in favour of this
    deprecate_arg decorator but it is held to deprecate args which become
    a reserved word in future Python releases and to prevent syntax errors.

    :param old_arg: old keyword
    :param new_arg: new keyword
    :type new_arg: str or None or bool
    """
    return deprecated_args(**{old_arg: new_arg})


def deprecated_args(**arg_pairs):
    """Decorator to declare multiple args deprecated.

    Usage:

        @deprecated_args(foo='bar', baz=None)
        def my_function(bar='baz'): pass
        # replaces 'foo' keyword by 'bar' and ignores 'baz' keyword

    :param arg_pairs: Each entry points to the new argument name. If an
        argument is to be removed, the value may be one of the following:
        - None: shows a DeprecationWarning
        - False: shows a PendingDeprecationWarning
        - True: shows a FutureWarning (only once)
        - empty string: no warning is printed
    """
    def decorator(obj):
        """Outer wrapper.

        The outer wrapper is used to create the decorating wrapper.

        :param obj: function being wrapped
        :type obj: object
        """
        def wrapper(*__args, **__kw):
            """Replacement function.

            :param __args: args passed to the decorated function
            :param __kw: kwargs passed to the decorated function
            :return: the value returned by the decorated function
            :rtype: any
            """
            name = obj.__full_name__
            depth = get_wrapper_depth(wrapper) + 1
            for old_arg, new_arg in arg_pairs.items():
                output_args = {
                    'name': name,
                    'old_arg': old_arg,
                    'new_arg': new_arg,
                }
                if old_arg not in __kw:
                    continue

                if new_arg not in [True, False, None, '']:
                    if new_arg in __kw:
                        warn('{new_arg} argument of {name} '
                             'replaces {old_arg}; cannot use both.'
                             .format_map(output_args),
                             RuntimeWarning, depth)
                    else:
                        # If the value is positionally given this will
                        # cause a TypeError, which is intentional
                        warn('{old_arg} argument of {name} '
                             'is deprecated; use {new_arg} instead.'
                             .format_map(output_args),
                             FutureWarning, depth)
                        __kw[new_arg] = __kw[old_arg]
                elif new_arg == '':
                    pass
                else:
                    if new_arg is False:
                        cls = PendingDeprecationWarning
                    elif new_arg is True:
                        cls = FutureWarning
                    else:  # new_arg is None
                        cls = DeprecationWarning
                    warn('{old_arg} argument of {name} is deprecated.'
                         .format_map(output_args),
                         cls, depth)
                del __kw[old_arg]

            return obj(*__args, **__kw)

        if not __debug__:
            return obj

        manage_wrapping(wrapper, obj)

        if wrapper.__signature__:
            # Build a new signature with deprecated args added.
            params = collections.OrderedDict()
            for param in wrapper.__signature__.parameters.values():
                params[param.name] = param.replace()
            for old_arg, new_arg in arg_pairs.items():
                params[old_arg] = inspect.Parameter(
                    old_arg, kind=inspect._POSITIONAL_OR_KEYWORD,
                    default='[deprecated name of {}]'.format(new_arg)
                    if new_arg not in [True, False, None, '']
                    else NotImplemented)
            params = collections.OrderedDict(sorted(params.items(),
                                                    key=lambda x: x[1].kind))
            wrapper.__signature__ = inspect.Signature()
            wrapper.__signature__._parameters = params

        return wrapper
    return decorator


def remove_last_args(arg_names):
    """
    Decorator to declare all args additionally provided deprecated.

    All positional arguments appearing after the normal arguments are marked
    deprecated. It marks also all keyword arguments present in arg_names as
    deprecated. Any arguments (positional or keyword) which are not present in
    arg_names are forwarded. For example a call with 3 parameters and the
    original function requests one and arg_names contain one name will result
    in an error, because the function got called with 2 parameters.

    The decorated function may not use ``*args`` or ``**kwargs``.

    :param arg_names: The names of all arguments.
    :type arg_names: iterable; for the most explanatory message it should
        retain the given order (so not a set for example).
    """
    def decorator(obj):
        """Outer wrapper.

        The outer wrapper is used to create the decorating wrapper.

        :param obj: function being wrapped
        :type obj: object
        """
        def wrapper(*__args, **__kw):
            """Replacement function.

            :param __args: args passed to the decorated function
            :param __kw: kwargs passed to the decorated function
            :return: the value returned by the decorated function
            :rtype: any
            """
            name = obj.__full_name__
            depth = get_wrapper_depth(wrapper) + 1
            args, varargs, kwargs, *_ = getfullargspec(wrapper.__wrapped__)
            if varargs is not None and kwargs is not None:
                raise ValueError('{} may not have * or ** args.'
                                 .format(name))
            deprecated = set(__kw) & set(arg_names)
            if len(__args) > len(args):
                deprecated.update(arg_names[:len(__args) - len(args)])
            # remove at most |arg_names| entries from the back
            new_args = tuple(__args[:max(len(args),
                                         len(__args) - len(arg_names))])
            new_kwargs = {arg: val for arg, val in __kw.items()
                          if arg not in arg_names}

            if deprecated:
                # sort them according to arg_names
                deprecated = [arg for arg in arg_names if arg in deprecated]
                warn("The trailing arguments ('{}') of {} are deprecated. "
                     "The value(s) provided for '{}' have been dropped."
                     .format("', '".join(arg_names), name,
                             "', '".join(deprecated)),
                     DeprecationWarning, depth)
            return obj(*new_args, **new_kwargs)

        manage_wrapping(wrapper, obj)

        return wrapper
    return decorator


def redirect_func(target, source_module: Optional[str] = None,
                  target_module: Optional[str] = None,
                  old_name: Optional[str] = None,
                  class_name: Optional[str] = None,
                  since: str = '',
                  future_warning: bool = True):
    """
    Return a function which can be used to redirect to 'target'.

    It also acts like marking that function deprecated and copies all
    parameters.

    .. versionchanged:: 7.0
       ``since`` parameter must be a release number, not a timestamp.

    :param target: The targeted function which is to be executed.
    :type target: callable
    :param source_module: The module of the old function. If '.' defaults
        to target_module. If 'None' (default) it tries to guess it from the
        executing function.
    :param target_module: The module of the target function. If
        'None' (default) it tries to get it from the target. Might not work
        with nested classes.
    :param old_name: The old function name. If None it uses the name of the
        new function.
    :param class_name: The name of the class. It's added to the target and
        source module (separated by a '.').
    :param since: a version string string when the method was deprecated
    :param future_warning: if True a FutureWarning will be thrown,
        otherwise it provides a DeprecationWarning
    :return: A new function which adds a warning prior to each execution.
    :rtype: callable
    """
    def call(*a, **kw):
        issue_deprecation_warning(
            old_name, new_name, since=since,
            warning_class=None if future_warning else DeprecationWarning)
        return target(*a, **kw)
    if target_module is None:
        target_module = target.__module__
    if target_module and target_module[-1] != '.':
        target_module += '.'
    if source_module == '.':
        source_module = target_module
    elif source_module and source_module[-1] != '.':
        source_module += '.'
    else:
        source_module = sys._getframe(1).f_globals['__name__'] + '.'
    if class_name:
        target_module += class_name + '.'
        source_module += class_name + '.'
    old_name = source_module + (old_name or target.__name__)
    new_name = target_module + target.__name__

    if not __debug__:
        return target

    return call


class ModuleDeprecationWrapper(types.ModuleType):

    """A wrapper for a module to deprecate classes or variables of it."""

    def __init__(self, module) -> None:
        """
        Initialise the wrapper.

        It will automatically overwrite the module with this instance in
        ``sys.modules``.

        :param module: The module name or instance
        :type module: str or module
        """
        if isinstance(module, (str, bytes)):
            module = sys.modules[module]
        super().__setattr__('_deprecated', {})
        super().__setattr__('_module', module)
        self.__dict__.update(module.__dict__)

        if __debug__:
            sys.modules[module.__name__] = self

    def add_deprecated_attr(self, name: str, replacement: Any = None, *,
                            replacement_name: Optional[str] = None,
                            warning_message: Optional[str] = None,
                            since: str = '',
                            future_warning: bool = True):
        """
        Add the name to the local deprecated names dict.

        .. versionchanged:: 7.0
           ``since`` parameter must be a release number, not a timestamp.

        :param name: The name of the deprecated class or variable. It may not
            be already deprecated.
        :param replacement: The replacement value which should be returned
            instead. If the name is already an attribute of that module this
            must be None. If None it'll return the attribute of the module.
        :param replacement_name: The name of the new replaced value. Required
            if ``replacement`` is not None and it has no __name__ attribute.
            If it contains a '.', it will be interpreted as a Python dotted
            object name, and evaluated when the deprecated object is needed.
        :param warning_message: The warning to display, with positional
            variables: {0} = module, {1} = attribute name, {2} = replacement.
        :param since: a version string string when the method was deprecated
        :param future_warning: if True a FutureWarning will be thrown,
            otherwise it provides a DeprecationWarning
        """
        if '.' in name:
            raise ValueError('Deprecated name "{}" may not contain '
                             '".".'.format(name))
        if name in self._deprecated:
            raise ValueError('Name "{}" is already deprecated.'.format(name))
        if replacement is not None and hasattr(self._module, name):
            raise ValueError('Module has already an attribute named '
                             '"{}".'.format(name))

        if replacement_name is None:
            if hasattr(replacement, '__name__'):
                replacement_name = replacement.__module__
                if hasattr(replacement, '__self__'):
                    replacement_name += '.'
                    replacement_name += replacement.__self__.__class__.__name__
                replacement_name += '.' + replacement.__name__
            else:
                raise TypeError('Replacement must have a __name__ attribute '
                                'or a replacement name must be set '
                                'specifically.')

        if not warning_message:
            warning_message = _build_msg_string(
                replacement_name, since).format('{0}.{1}', '{2}')
        if hasattr(self, name):
            # __getattr__ will only be invoked if self.<name> does not exist.
            delattr(self, name)
        self._deprecated[name] = (
            replacement_name, replacement, warning_message, future_warning)

    def __setattr__(self, attr, value) -> None:
        """Set the value of the wrapped module."""
        self.__dict__[attr] = value
        setattr(self._module, attr, value)

    def __getattr__(self, attr):
        """Return the attribute with a deprecation warning if required."""
        if attr in self._deprecated:
            name, repl, message, future = self._deprecated[attr]
            warning_message = message
            warn(warning_message.format(self._module.__name__, attr, name),
                 FutureWarning if future else DeprecationWarning, 2)

            if repl is not None:
                return repl

            if '.' in name:
                with suppress(Exception):
                    package_name = name.split('.', 1)[0]
                    module = import_module(package_name)
                    context = {package_name: module}
                    replacement = eval(name, context)
                    self._deprecated[attr] = (
                        name, replacement, message, future)
                    return replacement

        return getattr(self._module, attr)
