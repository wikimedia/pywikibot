"""Logging functions."""
#
# (C) Pywikibot team, 2010-2021
#
# Distributed under the terms of the MIT license.
#
import logging
import os
import sys

# logging levels
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from typing import Optional


STDOUT = 16
VERBOSE = 18
INPUT = 25

_init_routines = []
_inited_routines = set()


def add_init_routine(routine):
    """Add a routine to be run as soon as possible."""
    _init_routines.append(routine)


def _init():
    """Init any routines which have not already been called."""
    for init_routine in _init_routines:
        found = init_routine in _inited_routines  # prevent infinite loop
        _inited_routines.add(init_routine)
        if not found:
            init_routine()

    # Clear the list of routines to be inited
    _init_routines[:] = []  # the global variable is used with slice operator


# User output/logging functions

# Six output functions are defined. Each requires a string argument
# All of these functions generate a message to the log file if
# logging is enabled ("-log" or "-debug" command line arguments).

# The functions output(), stdout(), warning(), and error() all display a
# message to the user through the logger object; the only difference is the
# priority level, which can be used by the application layer to alter the
# display. The stdout() function should be used only for data that is
# the "result" of a script, as opposed to information messages to the
# user.

# The function log() by default does not display a message to the user, but
# this can be altered by using the "-verbose" command line option.

# The function debug() only logs its messages, they are never displayed on
# the user console. debug() takes a required second argument, which is a
# string indicating the debugging layer.


def logoutput(text, decoder=None, newline=True, _level=INFO, _logger='',
              **kwargs):
    """Format output and send to the logging module.

    Helper function used by all the user-output convenience functions.

    """
    if _logger:
        logger = logging.getLogger('pywiki.' + _logger)
    else:
        logger = logging.getLogger('pywiki')

    # invoke any init routines
    if _init_routines:
        _init()

    # frame 0 is logoutput() in this module,
    # frame 1 is the convenience function (output(), etc.)
    # frame 2 is whatever called the convenience function
    frame = sys._getframe(2)

    module = os.path.basename(frame.f_code.co_filename)
    context = {'caller_name': frame.f_code.co_name,
               'caller_file': module,
               'caller_line': frame.f_lineno,
               'newline': ('\n' if newline else '')}

    if decoder:
        text = text.decode(decoder)
    elif isinstance(text, bytes):
        try:
            text = text.decode('utf-8')
        except UnicodeDecodeError:
            text = text.decode('iso8859-1')
    else:
        # looks like text is a non-text object.
        # Maybe it has a __str__ builtin ?
        # (allows to print Page, Site...)
        text = str(text)

    logger.log(_level, text, extra=context, **kwargs)


def output(text, decoder=None, newline=True, **kwargs):
    r"""Output a message to the user via the userinterface.

    Works like print, but uses the encoding used by the user's console
    (console_encoding in the configuration file) instead of ASCII.

    If decoder is None, text should be a unicode string. Otherwise it
    should be encoded in the given encoding.

    If newline is True, a line feed will be added after printing the text.

    text can contain special sequences to create colored output. These
    consist of the escape character \03 and the color name in curly braces,
    e. g. \03{lightpurple}. \03{default} resets the color. By using the
    color_format method from pywikibot.tools.formatter, the escape character
    may be omitted.

    Other keyword arguments are passed unchanged to the logger; so far, the
    only argument that is useful is "exc_info=True", which causes the
    log message to include an exception traceback.
    """
    logoutput(text, decoder, newline, INFO, **kwargs)


def stdout(text, decoder=None, newline=True, **kwargs):
    """Output script results to the user via the userinterface.

    The text will be sent to standard output, so that it can be piped to
    another process. All other text will be sent to stderr.
    See: https://en.wikipedia.org/wiki/Pipeline_%28Unix%29

    :param text: the message printed via stdout logger to the user.
    :param decoder: If None, text should be a unicode string else it should
        be encoded in the given encoding.
    :param newline: If True, a line feed will be added after printing the text.
    :param kwargs: The keyword arguments can be found in the python doc:
        https://docs.python.org/3/howto/logging-cookbook.html
    """
    logoutput(text, decoder, newline, STDOUT, **kwargs)


def warning(text: str, decoder: Optional[str] = None,
            newline: bool = True, **kwargs):
    """Output a warning message to the user via the userinterface.

    :param text: the message the user wants to display.
    :param decoder: If None, text should be a unicode string else it
        should be encoded in the given encoding.
    :param newline: If True, a line feed will be added after printing the text.
    :param kwargs: The keyword arguments can be found in the python doc:
        https://docs.python.org/3/howto/logging-cookbook.html
    """
    logoutput(text, decoder, newline, WARNING, **kwargs)


def error(text, decoder=None, newline=True, **kwargs):
    """Output an error message to the user via the userinterface.

    :param text: the message containing the error which occurred.
    :param decoder: If None, text should be a unicode string else it should
        be encoded in the given encoding.
    :param newline: If True, a line feed will be added after printing the text.
    :param kwargs: The keyword arguments can be found in the python doc:
        https://docs.python.org/3/howto/logging-cookbook.html
    """
    logoutput(text, decoder, newline, ERROR, **kwargs)


def log(text, decoder=None, newline=True, **kwargs):
    """Output a record to the log file.

    :param text: the message which is to be logged to the log file.
    :param decoder: If None, text should be a unicode string else it should
        be encoded in the given encoding.
    :param newline: If True, a line feed will be added after printing the text.
    :param kwargs: The keyword arguments can be found in the python doc:
        https://docs.python.org/3/howto/logging-cookbook.html
    """
    logoutput(text, decoder, newline, VERBOSE, **kwargs)


def critical(text, decoder=None, newline=True, **kwargs):
    """Output a critical record to the user via the userinterface.

    :param text: the critical message which is to be displayed to the user.
    :param decoder: If None, text should be a unicode string else it should
        be encoded in the given encoding.
    :param newline: If True, a line feed will be added after printing the text.
    :param kwargs: The keyword arguments can be found in the python doc:
        https://docs.python.org/3/howto/logging-cookbook.html
    """
    logoutput(text, decoder, newline, CRITICAL, **kwargs)


def debug(text, layer, decoder=None, newline=True, **kwargs):
    """Output a debug record to the log file.

    :param text: the message of the debug record to be logged to the log file.
    :param decoder: If None, text should be a unicode string else it should
        be encoded in the given encoding.
    :param newline: If True, a line feed will be added after printing the text.
    :param kwargs: The keyword arguments can be found in the python doc:
        https://docs.python.org/3/howto/logging-cookbook.html
    :param layer: The name of the logger that text will be sent to.
    """
    logoutput(text, decoder, newline, DEBUG, layer, **kwargs)


def exception(msg=None, decoder=None, newline=True, tb=False, **kwargs):
    """Output an error traceback to the user via the userinterface.

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

    This function should only be called from an Exception handler.

    :param msg: If not None,contains the description of the exception occurred.
    :param decoder: If None, text should be a unicode string else it should
        be encoded in the given encoding.
    :param newline: If True, a line feed will be added after printing the text.
    :param kwargs: The keyword arguments can be found in the python doc:
        https://docs.python.org/3/howto/logging-cookbook.html
    :param tb: Set to True in order to output traceback also.
    """
    if isinstance(msg, BaseException):
        exc_info = 1
    else:
        exc_info = sys.exc_info()
        msg = '{}: {}'.format(repr(exc_info[1]).split('(')[0],
                              str(exc_info[1]).strip())
    if tb:
        kwargs['exc_info'] = exc_info
    logoutput(msg, decoder, newline, ERROR, **kwargs)
