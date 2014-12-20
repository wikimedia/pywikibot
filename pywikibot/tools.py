# -*- coding: utf-8  -*-
"""Miscellaneous helper functions (not wiki-dependent)."""
#
# (C) Pywikibot team, 2008
#
# Distributed under the terms of the MIT license.
#
from __future__ import print_function
__version__ = '$Id$'

import sys
import threading
import time
import inspect
import re
import collections
from distutils.version import Version

if sys.version_info[0] > 2:
    import queue as Queue
    basestring = (str,)
else:
    import Queue


# These variables are functions debug(str) and warning(str)
# which are initially the builtin print function.
# They exist here as the deprecators in this module rely only on them.
# pywikibot updates these function variables in bot.init_handlers()
debug = warning = print


def empty_iterator():
    # http://stackoverflow.com/a/13243870/473890
    """An iterator which does nothing."""
    return
    yield


class UnicodeMixin(object):

    """Mixin class to add __str__ method in Python 2 or 3."""

    if sys.version_info[0] > 2:
        def __str__(self):
            return self.__unicode__()
    else:
        def __str__(self):
            return self.__unicode__().encode('utf8')


# From http://python3porting.com/preparing.html
class ComparableMixin(object):

    """Mixin class to allow comparing to other objects which are comparable."""

    def __lt__(self, other):
        return other >= self._cmpkey()

    def __le__(self, other):
        return other > self._cmpkey()

    def __eq__(self, other):
        return other == self._cmpkey()

    def __ge__(self, other):
        return other < self._cmpkey()

    def __gt__(self, other):
        return other <= self._cmpkey()

    def __ne__(self, other):
        return other != self._cmpkey()


def concat_options(message, line_length, options):
    indent = len(message) + 2
    line_length -= indent
    option_msg = u''
    option_line = u''
    for option in options:
        if option_line:
            option_line += ', '
        # +1 for ','
        if len(option_line) + len(option) + 1 > line_length:
            if option_msg:
                option_msg += '\n' + ' ' * indent
            option_msg += option_line[:-1]  # remove space
            option_line = ''
        option_line += option
    if option_line:
        if option_msg:
            option_msg += '\n' + ' ' * indent
        option_msg += option_line
    return u'{0} ({1}):'.format(message, option_msg)


class MediaWikiVersion(Version):

    """Version object to allow comparing 'wmf' versions with normal ones."""

    MEDIAWIKI_VERSION = re.compile(r'(\d+(?:\.\d+)*)(?:wmf(\d+))?')

    def parse(self, vstring):
        version_match = MediaWikiVersion.MEDIAWIKI_VERSION.match(vstring)
        if not version_match:
            raise ValueError('Invalid version number')
        components = [int(n) for n in version_match.group(1).split('.')]
        self.wmf_version = None
        if version_match.group(2):  # wmf version
            self.wmf_version = int(version_match.group(2))
        self.version = tuple(components)

    def __str__(self):
        """Return version number with optional "wmf" suffix."""
        vstring = '.'.join(str(v) for v in self.version)
        if self.wmf_version:
            vstring += 'wmf{0}'.format(self.wmf_version)
        return vstring

    def _cmp(self, other):
        if isinstance(other, basestring):
            other = MediaWikiVersion(other)

        if self.version > other.version:
            return 1
        if self.version < other.version:
            return -1
        if self.wmf_version and other.wmf_version:
            if self.wmf_version > other.wmf_version:
                return 1
            if self.wmf_version < other.wmf_version:
                return -1
            return 0
        elif other.wmf_version:
            return 1
        elif self.wmf_version:
            return -1
        else:
            return 0

    if sys.version_info[0] == 2:
        __cmp__ = _cmp


class ThreadedGenerator(threading.Thread):

    """Look-ahead generator class.

    Runs a generator in a separate thread and queues the results; can
    be called like a regular generator.

    Subclasses should override self.generator, I{not} self.run

    Important: the generator thread will stop itself if the generator's
    internal queue is exhausted; but, if the calling program does not use
    all the generated values, it must call the generator's stop() method to
    stop the background thread.  Example usage:

    >>> gen = ThreadedGenerator(target=range, args=(20,))
    >>> try:
    ...     data = list(gen)
    ... finally:
    ...     gen.stop()
    >>> data
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

    """

    def __init__(self, group=None, target=None, name="GeneratorThread",
                 args=(), kwargs=None, qsize=65536):
        """Constructor.  Takes same keyword arguments as threading.Thread.

        target must be a generator function (or other callable that returns
        an iterable object).

        @param qsize: The size of the lookahead queue. The larger the qsize,
        the more values will be computed in advance of use (which can eat
        up memory and processor time).
        @type qsize: int

        """
        if kwargs is None:
            kwargs = {}
        if target:
            self.generator = target
        if not hasattr(self, "generator"):
            raise RuntimeError("No generator for ThreadedGenerator to run.")
        self.args, self.kwargs = args, kwargs
        threading.Thread.__init__(self, group=group, name=name)
        self.queue = Queue.Queue(qsize)
        self.finished = threading.Event()

    def __iter__(self):
        """Iterate results from the queue."""
        if not self.isAlive() and not self.finished.isSet():
            self.start()
        # if there is an item in the queue, yield it, otherwise wait
        while not self.finished.isSet():
            try:
                yield self.queue.get(True, 0.25)
            except Queue.Empty:
                pass
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        """Stop the background thread."""
        self.finished.set()

    def run(self):
        """Run the generator and store the results on the queue."""
        iterable = any([hasattr(self.generator, key)
                        for key in ['__iter__', '__getitem__']])
        if iterable and not self.args and not self.kwargs:
            self.__gen = self.generator
        else:
            self.__gen = self.generator(*self.args, **self.kwargs)
        for result in self.__gen:
            while True:
                if self.finished.isSet():
                    return
                try:
                    self.queue.put_nowait(result)
                except Queue.Full:
                    time.sleep(0.25)
                    continue
                break
        # wait for queue to be emptied, then kill the thread
        while not self.finished.isSet() and not self.queue.empty():
            time.sleep(0.25)
        self.stop()


def itergroup(iterable, size):
    """Make an iterator that returns lists of (up to) size items from iterable.

    Example:

    >>> i = itergroup(range(25), 10)
    >>> print(next(i))
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    >>> print(next(i))
    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    >>> print(next(i))
    [20, 21, 22, 23, 24]
    >>> print(next(i))
    Traceback (most recent call last):
     ...
    StopIteration

    """
    group = []
    for item in iterable:
        group.append(item)
        if len(group) == size:
            yield group
            group = []
    if group:
        yield group


class ThreadList(list):

    """A simple threadpool class to limit the number of simultaneous threads.

    Any threading.Thread object can be added to the pool using the append()
    method.  If the maximum number of simultaneous threads has not been reached,
    the Thread object will be started immediately; if not, the append() call
    will block until the thread is able to start.

    >>> pool = ThreadList(limit=10)
    >>> def work():
    ...     time.sleep(1)
    ...
    >>> for x in range(20):
    ...     pool.append(threading.Thread(target=work))
    ...

    """

    _logger = "threadlist"

    def __init__(self, limit=128, *args):
        """Constructor."""
        self.limit = limit
        super(ThreadList, self).__init__(*args)
        for item in self:
            if not isinstance(threading.Thread, item):
                raise TypeError("Cannot add '%s' to ThreadList" % type(item))

    def active_count(self):
        """Return the number of alive threads, and delete all non-alive ones."""
        count = 0
        for item in self[:]:
            if item.isAlive():
                count += 1
            else:
                self.remove(item)
        return count

    def append(self, thd):
        """Add a thread to the pool and start it."""
        if not isinstance(thd, threading.Thread):
            raise TypeError("Cannot append '%s' to ThreadList" % type(thd))
        while self.active_count() >= self.limit:
            time.sleep(2)
        super(ThreadList, self).append(thd)
        thd.start()

    def stop_all(self):
        """Stop all threads the pool."""
        if self:
            debug(u'EARLY QUIT: Threads: %d' % len(self), ThreadList._logger)
        for thd in self:
            thd.stop()
            debug(u'EARLY QUIT: Queue size left in %s: %s'
                  % (thd, thd.queue.qsize()), ThreadList._logger)


def intersect_generators(genlist):
    """
    Intersect generators listed in genlist.

    Yield items only if they are yielded by all generators in genlist.
    Threads (via ThreadedGenerator) are used in order to run generators
    in parallel, so that items can be yielded before generators are
    exhausted.

    Threads are stopped when they are either exhausted or Ctrl-C is pressed.
    Quitting before all generators are finished is attempted if
    there is no more chance of finding an item in all queues.

    @param genlist: list of page generators
    @type genlist: list
    """
    _logger = ""

    # Item is cached to check that it is found n_gen
    # times before being yielded.
    cache = collections.defaultdict(set)
    n_gen = len(genlist)

    # Class to keep track of alive threads.
    # Start new threads and remove completed threads.
    thrlist = ThreadList()

    for source in genlist:
        threaded_gen = ThreadedGenerator(name=repr(source), target=source)
        thrlist.append(threaded_gen)
        debug("INTERSECT: thread started: %r" % threaded_gen, _logger)

    while True:
        # Get items from queues in a round-robin way.
        for t in thrlist:
            try:
                # TODO: evaluate if True and timeout is necessary.
                item = t.queue.get(True, 0.1)

                # Cache entry is a set of tuples (item, thread).
                # Duplicates from same thread are not counted twice.
                cache[item].add((item, t))
                if len(cache[item]) == n_gen:
                    yield item
                    # Remove item from cache.
                    # No chance of seeing it again (see later: early stop).
                    cache.pop(item)

                active = thrlist.active_count()
                max_cache = n_gen
                if cache.values():
                    max_cache = max(len(v) for v in cache.values())
                # No. of active threads is not enough to reach n_gen.
                # We can quit even if some thread is still active.
                # There could be an item in all generators which has not yet
                # appeared from any generator. Only when we have lost one
                # generator, then we can bail out early based on seen items.
                if active < n_gen and n_gen - max_cache > active:
                    thrlist.stop_all()
                    return
            except Queue.Empty:
                pass
            except KeyboardInterrupt:
                thrlist.stop_all()
            finally:
                # All threads are done.
                if thrlist.active_count() == 0:
                    return


class CombinedError(KeyError, IndexError):

    """An error that gets caught by both KeyError and IndexError."""


class EmptyDefault(str, collections.Mapping):

    """
    A default for a not existing siteinfo property.

    It should be chosen if there is no better default known. It acts like an
    empty collections, so it can be iterated through it savely if treated as a
    list, tuple, set or dictionary. It is also basically an empty string.

    Accessing a value via __getitem__ will result in an combined KeyError and
    IndexError.
    """

    def __init__(self):
        """Initialise the default as an empty string."""
        str.__init__(self)

    def _empty_iter(self):
        """An iterator which does nothing and drops the argument."""
        return empty_iterator()

    def __getitem__(self, key):
        """Raise always a L{CombinedError}."""
        raise CombinedError(key)

    iteritems = itervalues = iterkeys = __iter__ = _empty_iter


EMPTY_DEFAULT = EmptyDefault()


class SelfCallMixin(object):

    """Return self when called."""

    def __call__(self):
        """Do nothing and just return itself."""
        return self


class SelfCallDict(SelfCallMixin, dict):

    """Dict with SelfCallMixin."""


class SelfCallString(SelfCallMixin, str):

    """Unicode string with SelfCallMixin."""


class DequeGenerator(collections.deque):

    """A generator that allows items to be added during generating."""

    def __iter__(self):
        """Return the object which will be iterated."""
        return self

    def next(self):
        """Python 3 iterator method."""
        if len(self):
            return self.popleft()
        else:
            raise StopIteration

    def __next__(self):
        """Python 3 iterator method."""
        return self.next()


# Decorators
#
# Decorator functions without parameters are _invoked_ differently from
# decorator functions with function syntax.  For example, @deprecated causes
# a different invocation to @deprecated().

# The former is invoked with the decorated function as args[0].
# The latter is invoked with the decorator arguments as *args & **kwargs,
# and it must return a callable which will be invoked with the decorated
# function as args[0].

# The follow deprecators may support both syntax, e.g. @deprecated and
# @deprecated() both work.  In order to achieve that, the code inspects
# args[0] to see if it callable.  Therefore, a decorator must not accept
# only one arg, and that arg be a callable, as it will be detected as
# a deprecator without any arguments.


def signature(obj):
    """
    Safely return function Signature object (PEP 362).

    inspect.signature was introduced in 3.3, however backports are available.
    In Python 3.3, it does not support all types of callables, and should
    not be relied upon.  Python 3.4 works correctly.

    Any exception calling inspect.signature is ignored and None is returned.

    @param obj: Function to inspect
    @rtype obj: callable
    @rtype: inpect.Signature or None
    """
    try:
        return inspect.signature(obj)
    except (AttributeError, ValueError):
        return None


def add_decorated_full_name(obj):
    """Extract full object name, including class, and store in __full_name__.

    This must be done on all decorators that are chained together, otherwise
    the second decorator will have the wrong full name.

    @param obj: A object being decorated
    @type obj: object
    """
    if hasattr(obj, '__full_name__'):
        return
    # The current frame is add_decorated_full_name
    # The next frame is the decorator
    # The next frame is the object being decorated
    frame = inspect.currentframe().f_back.f_back
    class_name = frame.f_code.co_name
    if class_name and class_name != '<module>':
        obj.__full_name__ = (obj.__module__ + '.' +
                             class_name + '.' +
                             obj.__name__)
    else:
        obj.__full_name__ = (obj.__module__ + '.' +
                             obj.__name__)


def add_full_name(obj):
    """
    A decorator to add __full_name__ to the function being decorated.

    This should be done for all decorators used in pywikibot, as any
    decorator that does not add __full_name__ will prevent other
    decorators in the same chain from being able to obtain it.

    This can be used to monkey-patch decorators in other modules.
    e.g.
    <xyz>.foo = add_full_name(<xyz>.foo)

    @param obj: The function to decorate
    @type obj: callable
    @return: decorating function
    @rtype: function
    """
    def outer_wrapper(*outer_args, **outer_kwargs):
        """Outer wrapper.

        The outer wrapper may be the replacement function if the decorated
        decorator was called without arguments, or the replacement decorator
        if the decorated decorator was called without arguments.

        @param outer_args: args
        @type outer_args: list
        @param outer_kwargs: kwargs
        @type: outer_kwargs: dict
        """
        def inner_wrapper(*args, **kwargs):
            """Replacement function.

            If the decorator supported arguments, they are in outer_args,
            and this wrapper is used to process the args which belong to
            the function that the decorated decorator was decorating.

            @param args: args passed to the decorated function.
            @param kwargs: kwargs passed to the decorated function.
            """
            add_decorated_full_name(args[0])
            return obj(*outer_args, **outer_kwargs)(*args, **kwargs)

        inner_wrapper.__doc__ = obj.__doc__
        inner_wrapper.__name__ = obj.__name__
        inner_wrapper.__module__ = obj.__module__
        inner_wrapper.__signature__ = signature(obj)

        # The decorator being decorated may have args, so both
        # syntax need to be supported.
        if (len(outer_args) == 1 and len(outer_kwargs) == 0 and
                callable(outer_args[0])):
            add_decorated_full_name(outer_args[0])
            return obj(outer_args[0])
        else:
            return inner_wrapper

    if not __debug__:
        return obj

    return outer_wrapper


@add_full_name
def deprecated(*args, **kwargs):
    """Decorator to output a deprecation warning.

    @kwarg instead: if provided, will be used to specify the replacement
    @type instead: string
    """
    def decorator(obj):
        """Outer wrapper.

        The outer wrapper is used to create the decorating wrapper.

        @param obj: function being wrapped
        @type obj: object
        """
        def wrapper(*args, **kwargs):
            """Replacement function.

            @param args: args passed to the decorated function.
            @type args: list
            @param kwargs: kwargs passed to the decorated function.
            @type kwargs: dict
            @return: the value returned by the decorated function
            @rtype: any
            """
            name = obj.__full_name__
            if instead:
                warning(u"%s is deprecated, use %s instead." % (name, instead))
            else:
                warning(u"%s is deprecated." % (name))
            return obj(*args, **kwargs)

        if not __debug__:
            return obj

        wrapper.__doc__ = obj.__doc__
        wrapper.__name__ = obj.__name__
        wrapper.__module__ = obj.__module__
        wrapper.__signature__ = signature(obj)
        return wrapper

    without_parameters = len(args) == 1 and len(kwargs) == 0 and callable(args[0])
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
    else:
        return decorator


def deprecate_arg(old_arg, new_arg):
    """Decorator to declare old_arg deprecated and replace it with new_arg."""
    return deprecated_args(**{old_arg: new_arg})


def deprecated_args(**arg_pairs):
    """
    Decorator to declare multiple args deprecated.

    @param arg_pairs: Each entry points to the new argument name. With True or
        None it drops the value and prints a warning. If False it just drops
        the value.
    """
    _logger = ""

    def decorator(obj):
        """Outer wrapper.

        The outer wrapper is used to create the decorating wrapper.

        @param obj: function being wrapped
        @type obj: object
        """
        def wrapper(*__args, **__kw):
            """Replacement function.

            @param __args: args passed to the decorated function
            @type __args: list
            @param __kwargs: kwargs passed to the decorated function
            @type __kwargs: dict
            @return: the value returned by the decorated function
            @rtype: any
            """
            name = obj.__full_name__
            for old_arg, new_arg in arg_pairs.items():
                if old_arg in __kw:
                    if new_arg not in [True, False, None]:
                        if new_arg in __kw:
                            warning(u"%(new_arg)s argument of %(name)s "
                                    "replaces %(old_arg)s; cannot use both."
                                    % locals())
                        else:
                            # If the value is positionally given this will
                            # cause a TypeError, which is intentional
                            warning(u"%(old_arg)s argument of %(name)s "
                                    "is deprecated; use %(new_arg)s instead."
                                    % locals())
                            __kw[new_arg] = __kw[old_arg]
                    elif new_arg is not False:
                        debug(u"%(old_arg)s argument of %(name)s is "
                              "deprecated." % locals(), _logger)
                    del __kw[old_arg]
            return obj(*__args, **__kw)

        if not __debug__:
            return obj

        wrapper.__doc__ = obj.__doc__
        wrapper.__name__ = obj.__name__
        wrapper.__module__ = obj.__module__
        wrapper.__signature__ = signature(obj)
        if wrapper.__signature__:
            # Build a new signature with deprecated args added.
            params = collections.OrderedDict()
            for param in wrapper.__signature__.parameters.values():
                params[param.name] = param.replace()
            for old_arg, new_arg in arg_pairs.items():
                params[old_arg] = inspect.Parameter(
                    old_arg, kind=inspect._POSITIONAL_OR_KEYWORD,
                    default='[deprecated name of ' + new_arg + ']'
                    if new_arg not in [True, False, None]
                    else NotImplemented)
            wrapper.__signature__ = inspect.Signature()
            wrapper.__signature__._parameters = params
        if not hasattr(obj, '__full_name__'):
            add_decorated_full_name(obj)
        wrapper.__full_name__ = obj.__full_name__
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

    The decorated function may not use *args or **kwargs.

    @param arg_names: The names of all arguments.
    @type arg_names: iterable; for the most explanatory message it should
        retain the given order (so not a set for example).
    """
    def decorator(obj):
        """Outer wrapper.

        The outer wrapper is used to create the decorating wrapper.

        @param obj: function being wrapped
        @type obj: object
        """
        def wrapper(*__args, **__kw):
            """Replacement function.

            @param __args: args passed to the decorated function
            @type __args: list
            @param __kwargs: kwargs passed to the decorated function
            @type __kwargs: dict
            @return: the value returned by the decorated function
            @rtype: any
            """
            name = obj.__full_name__
            args, varargs, kwargs, _ = inspect.getargspec(wrapper.__wrapped__)
            if varargs is not None and kwargs is not None:
                raise ValueError(u'{1} may not have * or ** args.'.format(
                    name))
            deprecated = set(__kw) & set(arg_names)
            if len(__args) > len(args):
                deprecated.update(arg_names[:len(__args) - len(args)])
            # remove at most |arg_names| entries from the back
            new_args = tuple(__args[:max(len(args), len(__args) - len(arg_names))])
            new_kwargs = dict((arg, val) for arg, val in __kw.items()
                              if arg not in arg_names)

            if deprecated:
                # sort them according to arg_names
                deprecated = [arg for arg in arg_names if arg in deprecated]
                warning(u"The trailing arguments ('{0}') of {1} are "
                        "deprecated. The value(s) provided for '{2}' have "
                        "been dropped.".format("', '".join(arg_names), name,
                                               "', '".join(deprecated)))
            return obj(*new_args, **new_kwargs)

        wrapper.__doc__ = obj.__doc__
        wrapper.__name__ = obj.__name__
        wrapper.__module__ = obj.__module__
        if not hasattr(obj, '__full_name__'):
            add_decorated_full_name(obj)
        wrapper.__full_name__ = obj.__full_name__
        wrapper.__wrapped__ = getattr(obj, '__wrapped__', obj)
        return wrapper
    return decorator


def redirect_func(target, source_module=None, target_module=None,
                  old_name=None, class_name=None):
    """
    Return a function which can be used to redirect to 'target'.

    It also acts like marking that function deprecated and copies all
    parameters.

    @param target: The targeted function which is to be executed.
    @type target: callable
    @param source_module: The module of the old function. If '.' defaults
        to target_module. If 'None' (default) it tries to guess it from the
        executing function.
    @type source_module: basestring
    @param target_module: The module of the target function. If
        'None' (default) it tries to get it from the target. Might not work
        with nested classes.
    @type target_module: basestring
    @param old_name: The old function name. If None it uses the name of the
        new function.
    @type old_name: basestring
    @param class_name: The name of the class. It's added to the target and
        source module (separated by a '.').
    @type class_name: basestring
    @return: A new function which adds a warning prior to each execution.
    @rtype: callable
    """
    def call(*a, **kw):
        warning(warn_message)
        return target(*a, **kw)
    if target_module is None:
        target_module = target.__module__
    if target_module and target_module[-1] != '.':
        target_module += '.'
    if source_module is '.':
        source_module = target_module
    elif source_module and source_module[-1] != '.':
        source_module += '.'
    else:
        source_module = sys._getframe(1).f_globals['__name__'] + '.'
    if class_name:
        target_module += class_name + '.'
        source_module += class_name + '.'
    warn_message = ('{source}{old} is DEPRECATED, use {target}{new} '
                    'instead.').format(new=target.__name__,
                                       old=old_name or target.__name__,
                                       target=target_module,
                                       source=source_module)

    if not __debug__:
        return target

    return call


class ModuleDeprecationWrapper(object):

    """A wrapper for a module to deprecate classes or variables of it."""

    def __init__(self, module):
        """
        Initialise the wrapper.

        It will automatically overwrite the module with this instance in
        C{sys.modules}.

        @param module: The module name or instance
        @type module: str or module
        """
        if isinstance(module, basestring):
            module = sys.modules[module]
        super(ModuleDeprecationWrapper, self).__setattr__('_deprecated', {})
        super(ModuleDeprecationWrapper, self).__setattr__('_module', module)
        super(ModuleDeprecationWrapper, self).__setattr__('__doc__', module.__doc__)

        if __debug__:
            sys.modules[module.__name__] = self

    def _add_deprecated_attr(self, name, replacement=None,
                             replacement_name=None, warning_message=None):
        """
        Add the name to the local deprecated names dict.

        @param name: The name of the deprecated class or variable. It may not
            be already deprecated.
        @type name: str
        @param replacement: The replacement value which should be returned
            instead. If the name is already an attribute of that module this
            must be None. If None it'll return the attribute of the module.
        @type replacement: any
        @param replacement_name: The name of the new replaced value. Required
            if C{replacement} is not None and it has no __name__ attribute.
        @type replacement_name: str
        @param warning_message: The warning to display, with positional
            variables: {0} = module, {1} = attribute name, {2} = replacement.
        @type warning_message: basestring
        """
        if '.' in name:
            raise ValueError('Deprecated name "{0}" may not contain '
                             '".".'.format(name))
        if name in self._deprecated:
            raise ValueError('Name "{0}" is already deprecated.'.format(name))
        if replacement is not None and hasattr(self._module, name):
            raise ValueError('Module has already an attribute named '
                             '"{0}".'.format(name))

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
            if replacement_name:
                warning_message = u"{0}.{1} is DEPRECATED, use {2} instead."
            else:
                warning_message = u"{0}.{1} is DEPRECATED."

        self._deprecated[name] = replacement_name, replacement, warning_message

    def __setattr__(self, attr, value):
        """Set the value of the wrapped module."""
        setattr(self._module, attr, value)

    def __getattr__(self, attr):
        """Return the attribute with a deprecation warning if required."""
        if attr in self._deprecated:
            warning_message = self._deprecated[attr][2]
            warning(warning_message.format(self._module.__name__,
                                           attr,
                                           self._deprecated[attr][0]))
            if self._deprecated[attr][1]:
                return self._deprecated[attr][1]
        return getattr(self._module, attr)


if __name__ == "__main__":
    def _test():
        import doctest
        doctest.testmod()
    _test()
