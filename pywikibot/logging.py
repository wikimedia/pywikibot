"""User output/logging functions.

Six output functions are defined. Each requires a ``msg`` argument
All of these functions generate a message to the log file if
logging is enabled (`-log` or `-debug` command line arguments).

The functions :func:`info` (alias :func:`output`), :func:`stdout`,
:func:`warning` and :func:`error` all display a message to the user
through the logger object; the only difference is the priority level,
which can be used by the application layer to alter the display. The
:func:`stdout` function should be used only for data that is the
"result" of a script, as opposed to information messages to the user.

The function :func:`log` by default does not display a message to the
user, but this can be altered by using the `-verbose` command line
option.

The function :func:`debug` only logs its messages, they are never
displayed on the user console. :func:`debug()` takes a required second
argument, which is a string indicating the debugging layer.
"""
#
# (C) Pywikibot team, 2010-2022
#
# Distributed under the terms of the MIT license.
#
import logging
import os
import sys

# logging levels
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from typing import Any

from pywikibot.backports import Callable, List
from pywikibot.tools import deprecated_args, issue_deprecation_warning


STDOUT = 16  #:
VERBOSE = 18  #:
INPUT = 25  #:
"""Three additional logging levels which are implemented beside
:const:`CRITICAL`, :const:`DEBUG`, :const:`ERROR`, :const:`INFO` and
:const:`WARNING`.

.. seealso:: :python:`Python Logging Levels<logging.html#logging-levels>`
"""

_init_routines = []  # type: List[Callable[[], Any]]
_inited_routines = set()


def add_init_routine(routine: Callable[[], Any]) -> None:
    """Add a routine to be run as soon as possible."""
    _init_routines.append(routine)


def _init() -> None:
    """Init any routines which have not already been called."""
    for init_routine in _init_routines:
        found = init_routine in _inited_routines  # prevent infinite loop
        _inited_routines.add(init_routine)
        if not found:
            init_routine()

    # Clear the list of routines to be inited
    _init_routines[:] = []  # the global variable is used with slice operator


# Note: The frame must be updated if this decorator is removed
@deprecated_args(text='msg')  # since 7.2
def logoutput(msg: Any,
              *args: Any,
              level: int = INFO,
              **kwargs: Any) -> None:
    """Format output and send to the logging module.

    Helper function used by all the user-output convenience functions.
    It can be used to implement your own high-level output function with
    a different logging level.

    `msg` can contain special sequences to create colored output. These
    consist of the color name in angle bracket, e. g. <<lightpurple>>.
    <<default>> resets the color.

    Other keyword arguments are passed unchanged to the logger; so far,
    the only argument that is useful is ``exc_info=True``, which causes
    the log message to include an exception traceback.

    :param msg: The message to be printed.
    :param args: Not used yet; prevents positional arguments except `msg`.
    :param level: The logging level; supported by :func:`logoutput` only.
    :keyword newline: If newline is True (default), a line feed will be
        added after printing the msg.
    :type newline: bool
    :keyword layer: Suffix of the logger name separated by dot. By
        default no suffix is used.
    :type layer: str
    :keyword decoder: If msg is bytes, this decoder is used to decode.
        Default is 'utf-8', fallback is 'iso8859-1'
    :type decoder: str
    :param kwargs: For the other keyword arguments refer
        :python:`Logger.debug()<library/logging.html#logging.Logger.debug>`
        and :pyhow:`logging-cookbook`
    """
    # invoke any init routines
    if _init_routines:
        _init()

    # cleanup positional args
    if level == ERROR:
        keys = ('decoder', 'newline', 'exc_info')
    elif level == DEBUG:
        keys = ('layer', 'decoder', 'newline')
    else:
        keys = ('decoder', 'newline')
    for i, arg in enumerate(args):
        key = keys[i]
        issue_deprecation_warning(
            'Positional argument {} ({})'.format(i + 1, arg),
            'keyword argument "{}={}"'.format(key, arg),
            since='7.2.0')
        if key in kwargs:
            warning('{!r} is given as keyword argument {!r} already; ignoring '
                    '{!r}'.format(key, arg, kwargs[key]))
        else:
            kwargs[key] = arg

    # frame 0 is logoutput() in this module,
    # frame 1 is the deprecation wrapper of this function
    # frame 2 is the convenience function (output(), etc.)
    # frame 3 is the deprecation wrapper the convenience function
    # frame 4 is whatever called the convenience function
    newline = kwargs.pop('newline', True)
    frame = sys._getframe(4)
    module = os.path.basename(frame.f_code.co_filename)
    context = {'caller_name': frame.f_code.co_name,
               'caller_file': module,
               'caller_line': frame.f_lineno,
               'newline': ('\n' if newline else '')}
    context.update(kwargs.pop('extra', {}))

    decoder = kwargs.pop('decoder', 'utf-8')
    if isinstance(msg, bytes):
        try:
            msg = msg.decode(decoder)
        except UnicodeDecodeError:
            msg = msg.decode('iso8859-1')

    layer = kwargs.pop('layer', '')
    logger = logging.getLogger(('pywiki.' + layer).strip('.'))
    logger.log(level, msg, extra=context, **kwargs)


# Note: The logoutput frame must be updated if this decorator is removed
@deprecated_args(text='msg')  # since 7.2
def info(msg: Any = '', *args: Any, **kwargs: Any) -> None:
    """Output a message to the user with level :const:`INFO`.

    ``msg`` will be sent to stderr via :mod:`pywikibot.userinterfaces`.
    It may be omitted and a newline is printed in that case.
    The arguments are interpreted as for :func:`logoutput`.

    .. versionadded:: 7.2
       was renamed from :func:`output`.

    .. seealso::
       :python:`Logger.info()<library/logging.html#logging.Logger.info>`
    """
    logoutput(msg, *args, **kwargs)


output = info
"""Synonym for :func:`info` for backward compatibility. The arguments
are interpreted as for :func:`logoutput`.

.. versionchanged:: 7.2
   was renamed to :func:`info`; `text`was renamed to `msg`; `msg`
   paramerer may be omitted; only keyword arguments are allowed except
   for `msg`.
.. seealso::
   :python:`Logger.info()<library/logging.html#logging.Logger.info>`
"""


# Note: The logoutput frame must be updated if this decorator is removed
@deprecated_args(text='msg')  # since 7.2
def stdout(msg: Any = '', *args: Any, **kwargs: Any) -> None:
    """Output script results to the user with level :const:`STDOUT`.

    ``msg`` will be sent to standard output (stdout) via
    :mod:`pywikibot.userinterfaces`, so that it can be piped to another
    process. All other functions will send to stderr.
    `msg` may be omitted and a newline is printed in that case.

    The arguments are interpreted as for :func:`logoutput`.

    .. versionchanged:: 7.2
       `text`was renamed to `msg`; `msg` parameter may be omitted;
       only keyword arguments are allowed except for `msg`.
    .. seealso::
       - :python:`Logger.log()<library/logging.html#logging.Logger.log>`
       - https://en.wikipedia.org/wiki/Pipeline_%28Unix%29
    """
    logoutput(msg, *args, level=STDOUT, **kwargs)


# Note: The logoutput frame must be updated if this decorator is removed
@deprecated_args(text='msg')  # since 7.2
def warning(msg: Any, *args: Any, **kwargs: Any) -> None:
    """Output a warning message to the user with level :const:`WARNING`.

    ``msg`` will be sent to stderr via :mod:`pywikibot.userinterfaces`.
    The arguments are interpreted as for :func:`logoutput`.

    .. versionchanged:: 7.2
       `text`was renamed to `msg`; only keyword arguments are allowed
       except for `msg`.
    .. seealso::
       :python:`Logger.warning()<library/logging.html#logging.Logger.warning>`
    """
    logoutput(msg, *args, level=WARNING, **kwargs)


# Note: The logoutput frame must be updated if this decorator is removed
@deprecated_args(text='msg')  # since 7.2
def error(msg: Any, *args: Any, **kwargs: Any) -> None:
    """Output an error message to the user with level :const:`ERROR`.

    ``msg`` will be sent to stderr via :mod:`pywikibot.userinterfaces`.
    The arguments are interpreted as for :func:`logoutput`.

    .. versionchanged:: 7.2
       `text`was renamed to `msg`; only keyword arguments are allowed
       except for `msg`.
    .. seealso::
       :python:`Logger.error()<library/logging.html#logging.Logger.error>`
    """
    logoutput(msg, *args, level=ERROR, **kwargs)


# Note: The logoutput frame must be updated if this decorator is removed
@deprecated_args(text='msg')  # since 7.2
def log(msg: Any, *args: Any, **kwargs: Any) -> None:
    """Output a record to the log file with level :const:`VERBOSE`.

    The arguments are interpreted as for :func:`logoutput`.

    .. versionchanged:: 7.2
       `text`was renamed to `msg`; only keyword arguments are allowed
       except for `msg`.
    .. seealso::
       :python:`Logger.log()<library/logging.html#logging.Logger.log>`
    """
    logoutput(msg, *args, level=VERBOSE, **kwargs)


# Note: The logoutput frame must be updated if this decorator is removed
@deprecated_args(text='msg')  # since 7.2
def critical(msg: Any, *args: Any, **kwargs: Any) -> None:
    """Output a critical record to the user with level :const:`CRITICAL`.

    ``msg`` will be sent to stderr via :mod:`pywikibot.userinterfaces`.
    The arguments are interpreted as for :func:`logoutput`.

    .. versionchanged:: 7.2
       `text`was renamed to `msg`; only keyword arguments are allowed
       except for `msg`.
    .. seealso::
       :python:`Logger.critical()
       <library/logging.html#logging.Logger.critical>`
    """
    logoutput(msg, *args, level=CRITICAL, **kwargs)


# Note: The logoutput frame must be updated if this decorator is removed
@deprecated_args(text='msg')  # since 7.2
def debug(msg: Any, *args: Any, **kwargs: Any) -> None:
    """Output a debug record to the log file with level :const:`DEBUG`.

    The arguments are interpreted as for :func:`logoutput`.

    .. versionchanged:: 7.2
       `layer` parameter is optional; `text`was renamed to `msg`;
       only keyword arguments are allowed except for `msg`.
    .. seealso::
       :python:`Logger.debug()<library/logging.html#logging.Logger.debug>`
    """
    logoutput(msg, *args, level=DEBUG, **kwargs)


# Note: The logoutput frame must be updated if this decorator is removed
@deprecated_args(tb='exc_info')  # since 7.2
def exception(msg: Any = None, *args: Any,
              exc_info: bool = True, **kwargs: Any) -> None:
    """Output an error traceback to the user with level :const:`ERROR`.

    Use directly after an 'except' statement::

        ...
        except Exception:
            pywikibot.exception()
        ...

    or alternatively::

        ...
        except Exception as e:
            pywikibot.exception(e)
        ...

    With `exc_info=False` this function works like :func:`error` except
    that the `msg` parameter may be omitted.
    This function should only be called from an Exception handler.
    ``msg`` will be sent to stderr via :mod:`pywikibot.userinterfaces`.
    The arguments are interpreted as for :func:`logoutput`.

    .. versionchanged:: 7.2
       only keyword arguments are allowed except for `msg`;
       `exc_info` keyword is to be used instead of `tb`.
    .. versionchanged:: 7.3
       `exc_info` is True by default
    .. seealso::
       :python:`Logger.exception()
       <library/logging.html#logging.Logger.exception>`

    The arguments are interpreted as for :meth:`output`.
    """
    if msg is None:
        exc_type, value, _tb = sys.exc_info()
        msg = str(value)
        if not exc_info:
            msg += ' ({})'.format(exc_type.__name__)
    assert msg is not None
    error(msg, *args, exc_info=exc_info, **kwargs)
