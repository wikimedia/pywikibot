"""User-interface related functions for building bots.

This module supports several different bot classes which could be used in
conjunction. Each bot should subclass at least one of these four classes:

* :class:`BaseBot`: Basic bot class in case where the site is handled
  differently, like working on multiple sites in parallel. No site
  attribute is provided. Instead site of the current page should be used.
  This class should normally not be used directly.

* :class:`SingleSiteBot`: Bot class which should only be run on a single
  site. They usually store site specific content and thus can't be
  easily run when the generator returns a page on another site. It has a
  property ``site`` which can also be changed. If the generator returns
  a page of a different site it'll skip that page.

* :class:`MultipleSitesBot`: An alias of :class:`BaseBot`. Should not
  be used if any other bot class is used.

* :class:`ConfigParserBot`: Bot class which supports reading options
  from a ``scripts.ini`` configuration file. That file consists of
  sections, led by a ``[section]`` header and followed by
  ``option: value`` or ``option=value`` entries. The section is the
  script name without .py suffix. All options identified must be
  predefined in available_options dictionary.

* :class:`Bot`: The previous base class which should be avoided. This
  class is mainly used for bots which work with Wikibase or together
  with an image repository.

Additionally there is the :py:obj:`CurrentPageBot` class which
automatically sets the current page to the page treated. It is
recommended to use this class and to use ``treat_page`` instead of
``treat`` and ``put_current`` instead of ``userPut``. It by default
subclasses the ``BaseBot`` class.

With :class:`CurrentPageBot` it's possible to subclass one of the
following classes to filter the pages which are ultimately handled by
:meth:`CurrentPageBot.treat_page`:

* :class:`ExistingPageBot`: Only handle pages which do exist.
* :class:`CreatingPageBot`: Only handle pages which do not exist.
* :class:`FollowRedirectPageBot`: If the generator returns a redirect
  page it'll follow the redirect and instead work on the redirected
  class.

It is possible to combine filters by subclassing multiple of them. They
are new-style classes so when a class is first subclassing
:class:`ExistingPageBot` and then :class:`FollowRedirectPageBot` it
will also work on pages which do not exist when a redirect pointed to
that. If the order is inversed it'll first follow them and then check
whether they exist.

Additionally there is the :class:`AutomaticTWSummaryBot` which
subclasses :class:`CurrentPageBot` and automatically defines the summary
when :meth:`put_current` is used.

.. deprecated:: 9.2
   The functions
   :func:`critical()<pywikibot.logging.critical>`
   :func:`debug()<pywikibot.logging.debug>`
   :func:`error()<pywikibot.logging.error>`
   :func:`exception()<pywikibot.logging.exception>`
   :func:`log()<pywikibot.logging.log>`
   :func:`output()<pywikibot.logging.output>`
   :func:`stdout()<pywikibot.logging.stdout>` and
   :func:`warning()<pywikibot.logging.warning>`
   as well as the constants
   ``CRITICAL``, ``DEBUG``, ``ERROR``, ``INFO``,
   :attr:`INPUT<pywikibot.logging.INPUT>`
   :attr:`STDOUT<pywikibot.logging.STDOUT>`
   :attr:`VERBOSE<pywikibot.logging.VERBOSE>`
   and ``WARNING`` imported from :mod:`logging` module are deprecated
   within this module. Import them directly. These functions can also be
   used as :mod:`pywikibot` members.

.. versionremoved:: 10.0
   The bot classes :class:`RedirectPageBot` and
   :class:`NoRedirectPageBot` are deprecated. Use
   :attr:`use_redirects<BaseBot.use_redirects>` attribute instead.
"""
#
# (C) Pywikibot team, 2008-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations


__all__ = (
    'LoggingFormatter',
    'set_interface', 'init_handlers', 'writelogheader',
    'input', 'input_choice', 'input_yn', 'input_list_choice', 'ui',
    'Option', 'StandardOption', 'NestedOption', 'IntegerOption',
    'ContextOption', 'ListOption', 'ShowingListOption', 'MultipleChoiceList',
    'ShowingMultipleChoiceList', 'OutputProxyOption',
    'HighlightContextOption', 'ChoiceException', 'UnhandledAnswer',
    'Choice', 'StaticChoice', 'LinkChoice', 'AlwaysChoice',
    'QuitKeyboardInterrupt',
    'InteractiveReplace',
    'calledModuleName', 'handle_args',
    'show_help', 'suggest_help',
    'writeToCommandLogFile', 'open_webbrowser',
    'OptionHandler',
    'BaseBot', 'Bot', 'ConfigParserBot', 'SingleSiteBot', 'MultipleSitesBot',
    'CurrentPageBot', 'AutomaticTWSummaryBot',
    'ExistingPageBot', 'FollowRedirectPageBot', 'CreatingPageBot',
    'WikidataBot',
)

import atexit
import codecs
import configparser
import json
import logging
import logging.handlers
import os
import re
import sys
import time
import warnings
import webbrowser
from collections import Counter
from collections.abc import Container, Generator
from contextlib import closing
from functools import wraps
from importlib import import_module
from pathlib import Path
from textwrap import fill
from typing import TYPE_CHECKING, Any

import pywikibot
import pywikibot.logging as pwb_logging
from pywikibot import config, daemonize, i18n, version
from pywikibot.backports import Callable, Dict, Iterable, Sequence
from pywikibot.bot_choice import (
    AlwaysChoice,
    Choice,
    ChoiceException,
    ContextOption,
    HighlightContextOption,
    IntegerOption,
    InteractiveReplace,
    LinkChoice,
    ListOption,
    MultipleChoiceList,
    NestedOption,
    Option,
    OutputProxyOption,
    QuitKeyboardInterrupt,
    ShowingListOption,
    ShowingMultipleChoiceList,
    StandardOption,
    StaticChoice,
    UnhandledAnswer,
)
from pywikibot.exceptions import (
    EditConflictError,
    Error,
    LockedPageError,
    NoPageError,
    PageSaveRelatedError,
    ServerError,
    SpamblacklistError,
    UnknownFamilyError,
    UnknownSiteError,
    VersionParseError,
    WikiBaseError,
)

# the constants are
from pywikibot.logging import (  # noqa: F401
    CRITICAL,
    DEBUG,
    ERROR,
    INFO,
    INPUT,
    STDOUT,
    VERBOSE,
    WARNING,
    add_init_routine,
)
from pywikibot.logging import debug as _debug
from pywikibot.logging import error as _error
from pywikibot.logging import exception as _exception
from pywikibot.logging import log as _log
from pywikibot.logging import stdout as _stdout
from pywikibot.logging import warning as _warning
from pywikibot.throttle import Throttle
from pywikibot.tools import redirect_func, strtobool
from pywikibot.tools._logging import LoggingFormatter


if TYPE_CHECKING:
    from pywikibot.site import BaseSite

    AnswerType = Iterable[tuple[str, str] | Option] | Option

_GLOBAL_HELP = """
GLOBAL OPTIONS
==============
(Global arguments available for all bots)

-dir:PATH         Read the bot's configuration data from directory given
                  by PATH, instead of from the default directory.

-config:xyn       The user config filename. Default is user-config.py.

-lang:xx          Set the language of the wiki you want to work on,
                  overriding the configuration in user config file.
                  xx should be the site code.

-family:xyz       Set the family of the wiki you want to work on, e.g.
                  wikipedia, wiktionary, wikivoyage, ... This will
                  override the configuration in user config file.

-site:xyz:xx      Set the wiki site you want to work on, e.g.
                  wikipedia:test, wiktionary:de, wikivoyage:en, ... This
                  will override the configuration in user config file.

-user:xyz         Log in as user 'xyz' instead of the default username.

-daemonize:xyz    Immediately return control to the terminal and redirect
                  stdout and stderr to file xyz.
                  (only use for bots that require no input from stdin).

-help             Show this help text.

-log              Enable the log file, using the default filename
                  '{}-bot.log'
                  Logs will be stored in the logs subdirectory.

-log:xyz          Enable the log file, using 'xyz' as the filename.

-nolog            Disable the log file (if it is enabled by default).
                  Also disable command.log.

-maxlag           Sets a new maxlag parameter to a number of seconds.
                  Defer bot edits during periods of database server lag.
                  Default is set by config.py

-putthrottle:n    Set the minimum time (in seconds) the bot will wait
-pt:n             between saving pages.
-put_throttle:n

-debug:item       Enable the log file and include extensive debugging
-debug            data for component "item" (for all components if the
                  second form is used).

-verbose          Have the bot provide additional console output that may be
-v                useful in debugging.

-cosmeticchanges  Toggles the cosmetic_changes setting made in config.py
-cc               or user config file to its inverse and overrules it.
                  All other settings and restrictions are untouched. The
                  setting may also be given directly like `-cc:True`;
                  accepted values for the option are `1`, `yes`, `true`,
                  `on`, `y`, `t` for True and `0`, `no`, `false`, `off`,
                  `n`, `f` for False. Values are case-insensitive.

-simulate         Disables writing to the server. Useful for testing and
                  debugging of new code (if given, doesn't do any real
                  changes, but only shows what would have been changed).
                  An integer or float value may be given to simulate a
                  processing time; the bot just waits for given seconds.

-<config var>:n   You may use all given numeric config variables as
                  option and modify it with command line.

"""

_GLOBAL_HELP_NOTE = """
GLOBAL OPTIONS
==============
For global options use -help:global or run pwb.py -help

"""

ui: pywikibot.userinterfaces._interface_base.ABUIC | None = None
"""Holds a user interface object defined in
:mod:`pywikibot.userinterfaces` subpackage.
"""


def set_interface(module_name: str) -> None:
    """Configures any bots to use the given interface module.

    Search for user interface module in the
    :mod:`pywikibot.userinterfaces` subdirectory and initialize UI.
    Calls :func:`init_handlers` to re-initialize if we were already
    initialized with another UI.

    .. versionadded:: 6.4
    """
    global ui

    ui_module = __import__(f'pywikibot.userinterfaces.{module_name}_interface',
                           fromlist=['UI'])
    ui = ui_module.UI()
    assert ui is not None
    atexit.register(ui.flush)
    pywikibot.argvu = ui.argvu()

    # re-initialize
    if _handlers_initialized:
        _handlers_initialized.clear()
        init_handlers()


_handlers_initialized = []  # we can have a script and the script wrapper


def handler_namer(name: str) -> str:
    """Modify the filename of a log file when rotating.

    RotatingFileHandler will save old log files by appending the
    extensions ``.1``, ``.2`` etc., to the filename. To keep the
    original extension, which is usually ``.log``, this function
    swaps the appended counter with the log extension:

    >>> handler_namer('add_text.log.1')
    'add_text.1.log'

    .. versionadded:: 6.5
    """
    path, qualifier = name.rsplit('.', 1)
    root, ext = os.path.splitext(path)
    return f'{root}.{qualifier}{ext}'


def init_handlers() -> None:
    """Initialize the handlers and formatters for the logging system.

    This relies on the global variable :attr:`ui` which is a UI object.

    .. seealso:: :mod:`pywikibot.userinterfaces`

    Calls :func:`writelogheader` after handlers are initialized.
    This function must be called before using any input/output methods;
    and must be called again if ui handler is changed. Use
    :func:`set_interface` to set the new interface which initializes it.

    .. note:: this function is called by any user input and output
       function, so it should normally not need to be called explicitly.

    All user output is routed through the logging module.
    Each type of output is handled by an appropriate handler object.
    This structure is used to permit eventual development of other
    user interfaces (GUIs) without modifying the core bot code.

    The following output levels are defined:

     - DEBUG: only for file logging; debugging messages.
     - STDOUT: output that must be sent to sys.stdout (for bots that may
       have their output redirected to a file or other destination).
     - VERBOSE: optional progress information for display to user.
     - INFO: normal (non-optional) progress information for display to user.
     - INPUT: prompts requiring user response.
     - WARN: user warning messages.
     - ERROR: user error messages.
     - CRITICAL: fatal error messages.

     .. seealso::
        * :mod:`pywikibot.logging`
        * :python:`Python Logging Levels<library/logging.html#logging-levels>`

    Accordingly, do **not** use print statements in bot code; instead,
    use :func:`pywikibot.info()<pywikibot.logging.info>` function and
    other functions from :mod:`pywikibot.logging` module.

    .. versionchanged:: 6.2
       Different logfiles are used if multiple processes of the same
       script are running.
    """
    module_name = calledModuleName()
    if not module_name:
        module_name = 'terminal-interface'

    logging.addLevelName(VERBOSE, 'VERBOSE')
    # for messages to be displayed on terminal at "verbose" setting
    # use INFO for messages to be displayed even on non-verbose setting

    logging.addLevelName(STDOUT, 'STDOUT')
    # for messages to be displayed to stdout

    logging.addLevelName(INPUT, 'INPUT')
    # for prompts requiring user response

    root_logger = logging.getLogger('pywiki')
    if root_logger.hasHandlers() and module_name in _handlers_initialized:
        return
    root_logger.setLevel(DEBUG + 1)  # all records except DEBUG go to logger

    warnings_logger = logging.getLogger('py.warnings')
    warnings_logger.setLevel(DEBUG)

    # If there are command line warnings options, do not override them
    if not sys.warnoptions:
        logging.captureWarnings(True)

        if config.debug_log or 'deprecation' in config.log:
            warnings.filterwarnings('always')
        elif config.verbose_output:
            warnings.filterwarnings('module')
        warnings.filterwarnings('once', category=FutureWarning)

    for handler in root_logger.handlers:
        handler.close()
    root_logger.handlers.clear()  # remove any old handlers
    root_logger.propagate = False  # T281643

    # configure handler(s) for display to user interface
    assert ui is not None
    ui.init_handlers(root_logger, **config.userinterface_init_kwargs)

    # if user has enabled file logging, configure file handler
    if module_name in config.log or '*' in config.log:
        # Use a dummy Throttle to get a PID.
        # This is necessary because tests may have site disabled.
        throttle = Throttle('')
        pid_int = throttle.get_pid(module_name)  # get the global PID
        pid = str(pid_int) + '-' if pid_int > 1 else ''

        if config.logfilename:
            # keep config.logfilename unchanged
            logfile = config.datafilepath('logs', config.logfilename)
        else:
            # add PID to logfle name
            logfile = config.datafilepath('logs',
                                          f'{module_name}-{pid}bot.log')

        file_handler = logging.handlers.RotatingFileHandler(
            filename=logfile,
            maxBytes=config.logfilesize << 10,
            backupCount=config.logfilecount,
            encoding='utf-8'
        )
        file_handler.namer = handler_namer

        file_handler.setLevel(DEBUG)
        form = LoggingFormatter(
            fmt='%(asctime)s %(caller_file)18s, %(caller_line)4s '
                'in %(caller_name)18s: %(levelname)-8s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(form)
        root_logger.addHandler(file_handler)
        # Turn on debugging for each component requested by user
        # or for all components if nothing was specified
        for component in config.debug_log:
            if component:
                debuglogger = logging.getLogger('pywiki.' + component)
            else:
                debuglogger = logging.getLogger('pywiki')
            debuglogger.setLevel(DEBUG)
            debuglogger.addHandler(file_handler)

        warnings_logger.addHandler(file_handler)

    _handlers_initialized.append(module_name)

    writelogheader()


def writelogheader() -> None:
    """Save additional version, system and status info to the log file in use.

    This may help the user to track errors or report bugs.

    .. versionchanged:: 9.0
       ignore milliseconds with timestamp.
    """
    _log(f'\n=== Pywikibot framework v{pywikibot.__version__} --'
         ' Logging header ===')

    # script call
    _log(f'COMMAND: {sys.argv}')

    # script call time stamp
    _log(f'DATE: {pywikibot.Timestamp.nowutc()} UTC')

    # new framework release/revision? (handle_args needs to be called first)
    try:
        _log('VERSION: {}'.format(version.getversion(
            online=config.log_pywiki_repo_version).strip()))
    except VersionParseError:
        _exception()

    # system
    if hasattr(os, 'uname'):
        _log(f'SYSTEM: {os.uname()}')

    # config file dir
    _log(f'CONFIG FILE DIR: {pywikibot.config.base_dir}')

    # These are the main dependencies of pywikibot.
    check_package_list = [
        'requests',
        'mwparserfromhell',
    ]

    # report all imported packages
    if config.verbose_output:
        check_package_list += sys.modules

    _log('PACKAGES:')
    packages = version.package_versions(check_package_list)
    for name in sorted(packages.keys()):
        info = packages[name]
        info.setdefault('path',
                        f"[{info.get('type', 'path unknown')}]")
        info.setdefault('ver', '??')
        if 'err' in info:
            _log('  {name}: {err}'.format_map(info))
        else:
            _log('  {name} ({path}) = {ver}'.format_map(info))

    # imported modules
    _log('MODULES:')
    for module in sys.modules.copy().values():
        filename = version.get_module_filename(module)
        if not filename:
            continue

        mtime = version.get_module_mtime(module).isoformat(sep=' ',
                                                           timespec='seconds')
        _log(f'  {mtime} {filename}')

    if config.log_pywiki_repo_version:
        _log(f'PYWIKI REPO VERSION: {version.getversion_onlinerepo()}')

    _log('=' * 57)


add_init_routine(init_handlers)


# User input functions

def initialize_handlers(function):
    """Make sure logging system has been initialized.

    .. versionadded:: 7.0
    """
    @wraps(function)
    def wrapper(*args, **kwargs):
        init_handlers()
        return function(*args, **kwargs)
    return wrapper


@initialize_handlers
def input(question: str,
          password: bool = False,
          default: str | None = '',
          force: bool = False) -> str:
    """Ask the user a question, return the user's answer.

    :param question: a string that will be shown to the user. Don't add a
        space after the question mark/colon, this method will do this for you.
    :param password: if True, hides the user's input (for password entry).
    :param default: The default answer if none was entered. None to require
        an answer.
    :param force: Automatically use the default
    """
    assert ui is not None
    return ui.input(question, password=password, default=default, force=force)


@initialize_handlers
def input_choice(question: str,
                 answers: AnswerType,
                 default: str | None = None,
                 return_shortcut: bool = True,
                 automatic_quit: bool = True,
                 force: bool = False) -> Any:
    """Ask the user the question and return one of the valid answers.

    .. seealso::
       * :meth:`userinterfaces._interface_base.ABUIC.input_choice`
       * :meth:`userinterfaces.buffer_interface.UI.input_choice`
       * :meth:`userinterfaces.terminal_interface_base.UI.input_choice`

    :param question: The question asked without trailing spaces.
    :param answers: The valid answers each containing a full length answer and
        a shortcut. Each value must be unique.
    :param default: The result if no answer was entered. It must not be in the
        valid answers and can be disabled by setting it to None. If it should
        be linked with the valid answers it must be its shortcut.
    :param return_shortcut: Whether the shortcut or the index of the answer is
        returned.
    :param automatic_quit: Adds the option 'Quit' ('q') and throw a
        :exc:`bot.QuitKeyboardInterrupt` if selected.
    :param force: Automatically use the *default*.
    :return: The selected answer shortcut or index. Is -1 if the default is
        selected, it does not return the shortcut and the default is not a
        valid shortcut.
    """
    assert ui is not None
    return ui.input_choice(question, answers, default, return_shortcut,
                           automatic_quit=automatic_quit, force=force)


def input_yn(question: str,
             default: bool | str | None = None,
             automatic_quit: bool = True,
             force: bool = False) -> bool:
    """Ask the user a yes/no question and return the answer as a bool.

    **Example:**

    >>> input_yn('Do you like Pywikibot?', 'y', False, force=True)
    ... # doctest: +SKIP
    Do you like Pywikibot? ([Y]es, [n]o)
    True
    >>> input_yn('More examples?', False, automatic_quit=False, force=True)
    ... # doctest: +SKIP
    Some more examples? ([y]es, [N]o)
    False

    .. seealso:: :func:`input_choice`

    :param question: The question asked without trailing spaces.
    :param default: The result if no answer was entered. It must be a
        bool or ``'y'``, ``'n'``, ``0`` or ``1`` and can be disabled by
        setting it to None.
    :param automatic_quit: Adds the option 'Quit' ('q') and throw a
        :exc:`bot.QuitKeyboardInterrupt` if selected.
    :param force: Automatically use the *default*.
    :return: Return True if the user selected yes and False if the user
        selected no. If the default is not None it'll return True if default
        is True or 'y' and False if default is False or 'n'.
    """
    if isinstance(default, bool):
        default = 'ny'[default]

    return input_choice(question, [('Yes', 'y'), ('No', 'n')],
                        default,
                        automatic_quit=automatic_quit, force=force) == 'y'


@initialize_handlers
def input_list_choice(question: str,
                      answers: AnswerType,
                      default: int | str | None = None,
                      force: bool = False) -> str:
    """Ask the user the question and return one of the valid answers.

    :param question: The question asked without trailing spaces.
    :param answers: The valid answers each containing a full length answer.
    :param default: The result if no answer was entered. It must not be in the
        valid answers and can be disabled by setting it to None.
    :param force: Automatically use the default
    :return: The selected answer.
    """
    assert ui is not None
    return ui.input_list_choice(question, answers, default=default,
                                force=force)


# Command line parsing and help
def calledModuleName() -> str:
    """Return the name of the module calling this function.

    This is required because the -help option loads the module's
    docstring and because the module name will be used for the filename
    of the log.

    .. versionchanged:: 10.0
       Detect unittest and pytest run and return the test module.
    """
    mod = pywikibot.argvu[0]

    if 'pytest' in mod:
        return 'pytest'

    if mod.endswith('unittest'):
        return 'unittest'

    return Path(mod).stem


def handle_args(args: Iterable[str] | None = None,
                do_help: bool = True) -> list[str]:
    """Handle global command line arguments and return the rest as a list.

    Takes the command line arguments as strings, processes all
    :ref:`global parameters<global options>` such as ``-lang`` or
    ``-log``, initialises the logging layer, which emits startup
    information into log at level 'verbose'. This function makes sure
    that global arguments are applied first, regardless of the order in
    which the arguments were given. ``args`` may be passed as an
    argument, thereby overriding ``sys.argv``.

    >>> local_args = pywikibot.handle_args()  # sys.argv is used
    >>> local_args  # doctest: +SKIP
    []
    >>> local_args = pywikibot.handle_args(['-simulate', '-myoption'])
    >>> local_args  # global options are handled, show the remaining
    ['-myoption']
    >>> for arg in local_args: pass  # do whatever is wanted with local_args

    .. caution::
       Global options might be introduced without warning period. It is
       up to developers to verify that global options do not interfere
       with local script options of private scripts.

    .. tip::
       Avoid using this method in your private scripts and use the
       :mod:`pwb<pywikibot.scripts.wrapper>` wrapper instead. In
       directory mode::

           python pwb.py <global options> <name_of_script> <local options>

       With installed site package::

           pwb <global options> <name_of_script> <local options>

       .. note:: the :mod:`pwb<pywikibot.scripts.wrapper>` wrapper can
          be used even if the `handle_args` method is used within the
          script.

    .. versionchanged:: 5.2
       *-site* global option was added
    .. versionchanged:: 7.1
       *-cosmetic_changes* and *-cc* may be set directly instead of
       toggling the value. Refer :func:`tools.strtobool` for valid values.
    .. versionchanged:: 7.7
       *-config* global option was added.
    .. versionchanged:: 8.0
       Short site value can be given if site code is equal to family
       like ``-site:meta``.
    .. versionchanged:: 8.1
       ``-nolog`` option also discards command.log.

    :param args: Command line arguments. If None,
        :meth:`pywikibot.argvu<userinterfaces._interface_base.ABUIC.argvu>`
        is used which is a copy of ``sys.argv``
    :param do_help: Handle parameter '-help' to show help and invoke sys.exit
    :return: list of arguments not recognised globally
    """
    if pywikibot._sites:
        warnings.warn('Site objects have been created before arguments were '
                      'handled', UserWarning)

    # get commandline arguments if necessary
    if not args:
        # it's the version in pywikibot.__init__ that is changed by scripts,
        # not the one in pywikibot.bot.
        args = pywikibot.argvu[1:]

    # get the name of the module calling this function. This is
    # required because the -help option loads the module's docstring and
    # because the module name will be used for the filename of the log.
    module_name = calledModuleName() or 'terminal-interface'
    non_global_args = []
    username = None
    commandlog = True
    do_help_val: bool | str | None = None if do_help else False
    assert args is not None
    for arg in args:
        option, _, value = arg.partition(':')
        if do_help_val is not False and option == '-help':
            do_help_val = value or True
        # these are handled by config.py
        elif option in ('-config', '-dir'):
            pass
        elif option == '-site':
            if ':' in value:
                config.family, config.mylang = value.split(':')
            else:
                config.family = config.mylang = value
        elif option == '-family':
            config.family = value
        elif option == '-lang':
            config.mylang = value
        elif option == '-user':
            username = value
        elif option in ('-putthrottle', '-pt'):
            config.put_throttle = float(value)
        elif option == '-log':
            if module_name not in config.log:
                config.log.append(module_name)
            if value:
                config.logfilename = value
        elif option == '-nolog':
            commandlog = False
            config.log = []
        elif option in ('-cosmeticchanges', '-cc'):
            config.cosmetic_changes = (strtobool(value) if value
                                       else not config.cosmetic_changes)
            pywikibot.info(f'NOTE: option cosmetic_changes is '
                           f'{config.cosmetic_changes}\n')
        elif option == '-simulate':
            config.simulate = value or True
        #
        #  DEBUG control:
        #
        #    The framework has four layers (by default, others can be added),
        #    each designated by a string --
        #
        #    1.  "comm": the communication layer (http requests, etc.)
        #    2.  "data": the raw data layer (API requests, XML dump parsing)
        #    3.  "wiki": the wiki content representation layer (Page and Site
        #         objects)
        #    4.  "bot": the application layer (user scripts should always
        #         send any debug() messages to this layer)
        #
        #    The "-debug:layer" flag sets the logger for any specified
        #    layer to the DEBUG level, causing it to output extensive debugging
        #    information. Otherwise, the default logging setting is the INFO
        #    level. "-debug" with no layer specified sets _all_ loggers to
        #    DEBUG level.
        #
        #    This method does not check the 'layer' part of the flag for
        #    validity.
        #
        #    If used, "-debug" turns on file logging, regardless of any
        #    other settings.
        #
        elif option == '-debug':
            if module_name not in config.log:
                config.log.append(module_name)
            if value not in config.debug_log:
                config.debug_log.append(value)  # may be empty string
        elif option in ('-verbose', '-v'):
            config.verbose_output += 1
        elif option == '-daemonize':
            redirect_std = value or None
            daemonize.daemonize(redirect_std=redirect_std)
        else:
            # the argument depends on numerical config settings
            # e.g. -maxlag and -step:
            try:
                _arg = option[1:]
                # explicitly check for int (so bool doesn't match)
                if not isinstance(getattr(config, _arg), int):
                    raise TypeError
                setattr(config, _arg, int(value))
            except (ValueError, TypeError, AttributeError):
                # argument not global -> specific bot script will take care
                non_global_args.append(arg)

    if username:
        config.usernames[config.family][config.mylang] = username

    init_handlers()
    if commandlog:
        writeToCommandLogFile()

    if config.verbose_output:
        pywikibot.info('Python ' + sys.version)

    if do_help_val:
        show_help(show_global=do_help_val == 'global')
        sys.exit(0)

    if calledModuleName() != 'generate_user_files':  # T261771
        try:
            pywikibot.Site()
        except (UnknownFamilyError, UnknownSiteError):
            _exception(exc_info=False)
            sys.exit(1)
        if calledModuleName() == 'wrapper':
            pywikibot._sites.clear()

    _debug('handle_args() completed.')
    return non_global_args


def show_help(module_name: str | None = None,
              show_global: bool = False) -> None:
    """Show help for the Bot.

    .. versionchanged:: 4.0
       Renamed from showHelp() to show_help().
    .. versionchanged:: 8.0
       Do not show version changes.
    """
    if not module_name:
        module_name = calledModuleName()
    if not module_name:
        try:
            main = sys.modules['__main__'].main  # type: ignore[attr-defined]
            module_name = main.__module__
            assert module_name is not None
        except NameError:
            module_name = 'no_module'

    try:
        module = import_module(module_name)
    except ModuleNotFoundError:
        if module_name:
            _stdout('Sorry, no help available for ' + module_name)
        _log('show_help:', exc_info=True)
    else:
        assert module.__doc__ is not None
        help_text = re.sub(r'^\.\. version(added|changed)::.+', '',
                           module.__doc__, flags=re.MULTILINE | re.DOTALL)
        if hasattr(module, 'docuReplacements'):
            for key, value in module.docuReplacements.items():
                help_text = help_text.replace(key, value.strip())
        _stdout(help_text)

    if show_global or module_name == 'pwb':
        _stdout(_GLOBAL_HELP.format(module_name))
    else:
        _stdout(_GLOBAL_HELP_NOTE)


def suggest_help(missing_parameters: Sequence[str] | None = None,
                 missing_generator: bool = False,
                 unknown_parameters: Sequence[str] | None = None,
                 exception: Exception | None = None,
                 missing_action: bool = False,
                 additional_text: str = '',
                 missing_dependencies: Sequence[str] | None = None) -> bool:
    """Output error message to use -help with additional text before it.

    :param missing_parameters: A list of parameters which are missing.
    :param missing_generator: Whether a generator is missing.
    :param unknown_parameters: A list of parameters which are unknown.
    :param exception: An exception thrown.
    :param missing_action: Add an entry that no action was defined.
    :param additional_text: Additional text added to the end.
    :param missing_dependencies: A list of dependencies which cannot be
        imported.
    :return: True if an error message was printed, False otherwise
    """
    messages = []
    if exception:
        messages.append(f'An error occurred: "{exception}".')
    if missing_generator:
        messages.append(
            'Unable to execute script because no generator was defined.')
    if missing_parameters:
        messages.append('Missing parameter{s} "{params}".'
                        .format(s='s' if len(missing_parameters) > 1 else '',
                                params='", "'.join(missing_parameters)))
    if missing_action:
        messages.append('No action defined.')
    if unknown_parameters:
        messages.append('Unknown parameter{s} "{params}".'
                        .format(s='s' if len(unknown_parameters) > 1 else '',
                                params='", "'.join(unknown_parameters)))
    if missing_dependencies:
        messages.append('Missing dependenc{s} "{deps}".'
                        .format(
                            s='ies' if len(missing_dependencies) > 1 else 'y',
                            deps='", "'.join(missing_dependencies)))
    if additional_text:
        messages.append(additional_text.strip())
    if messages:
        messages.append('Use -help for further information.')
        _error('\n'.join(messages))
        return True
    return False


def writeToCommandLogFile() -> None:
    """Save name of the called module along with all params to logfile.

    This can be used by user later to track errors or report bugs.
    """
    modname = calledModuleName()
    # put quotation marks around all parameters
    args = [modname] + [f'"{s}"' for s in pywikibot.argvu[1:]]
    command_log_filename = config.datafilepath('logs', 'commands.log')
    try:
        command_log_file = codecs.open(command_log_filename, 'a', 'utf-8')
    except OSError:
        command_log_file = codecs.open(command_log_filename, 'w', 'utf-8')

    with closing(command_log_file):
        # add a timestamp in ISO 8601 formulation
        iso_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        command_log_file.write('{} r{} Python {} '
                               .format(iso_date,
                                       version.getversiondict()['rev'],
                                       sys.version.split()[0]))
        command_log_file.write(' '.join(args) + os.linesep)


def open_webbrowser(page: pywikibot.page.BasePage) -> None:
    """Open the web browser displaying the page and wait for input."""
    webbrowser.open(page.full_url())
    i18n.input('pywikibot-enter-finished-browser')


class _OptionDict(Dict[str, Any]):

    """The option dict which holds the options of OptionHandler.

    .. versionadded:: 4.1
    """

    def __init__(self, classname: str, options: dict[str, Any]) -> None:
        self._classname = classname
        super().__init__(options)

    def __missing__(self, key: str) -> None:
        raise Error(f"'{key}' is not a valid option for {self._classname}.")

    def __getattr__(self, name: str) -> Any:
        """Get item from dict."""
        return self.__getitem__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set item or attribute."""
        if name != '_classname':
            self.__setitem__(name, value)
        else:
            super().__setattr__(name, value)


class OptionHandler:

    """Class to get and set options.

    How to use options of OptionHandler and its BaseBot subclasses:
    First define an available_options class attribute for your own
    option handler to define all available options:

    >>> default_options = {'foo': 'bar', 'bar': 42, 'baz': False}
    >>> class MyHandler(OptionHandler): available_options = default_options

    Or you may update the predefined setting in the class initializer.
    BaseBot predefines a 'always' options and sets it to False:

    self.available_options.update(always=True, another_option='Yes')

    Now you can instantiate an OptionHandler or BaseBot class passing
    options other than default values:

    >>> bot = MyHandler(baz=True)

    You can access bot options either as keyword item or attribute:

    >>> bot.opt.foo
    'bar'
    >>> bot.opt['bar']
    42
    >>> bot.opt.baz  # default was overridden
    True

    You can set the options in the same way:

    >>> bot.opt.bar = 4711
    >>> bot.opt['baz'] = None
    >>>

    Or you can use the option as a dict:

    >>> 'Option opt.{foo} is {bar}'.format_map(bot.opt)
    'Option opt.bar is 4711'

    .. warning:: You must not access bot options as an attribute if the
       keyword is a :python:`dict method<library/stdtypes.html#dict.clear>`.
    """

    available_options: dict[str, Any] = {}
    """ Handler configuration attribute.
    Only the keys of the dict can be passed as `__init__` options.
    The values are the default values. Overwrite this in subclasses!
    """

    def __init__(self, **kwargs: Any) -> None:
        """Only accept options defined in available_options.

        :param kwargs: bot options
        """
        self.set_options(**kwargs)

    def set_options(self, **options: Any) -> None:
        """Set the instance options."""
        valid_options = set(self.available_options)
        received_options = set(options)

        # self.opt contains all available options including defaults
        self.opt = _OptionDict(self.__class__.__name__, self.available_options)
        # update the options overridden from defaults
        self.opt.update((opt, options[opt])
                        for opt in received_options & valid_options)
        for opt in received_options - valid_options:
            _warning(f'{opt} is not a valid option. It was ignored.')


class BaseBot(OptionHandler):

    """Generic Bot to be subclassed.

    Only accepts `generator` and options defined in
    :attr:`available_options`.

    This class provides a :meth:`run` method for basic processing of a
    generator one page at a time.

    If the subclass places a page generator in :attr:`generator`, Bot
    will process each page in the generator, invoking the method
    :meth:`treat` which must then be implemented by subclasses.

    Each item processed by :meth:`treat` must be a :class:`page.BasePage`
    type. Use :meth:`init_page` to upcast the type. To enable other
    types, set :attr:`BaseBot.treat_page_type` to an appropriate type;
    your bot should derive from :class:`BaseBot` in that case and handle
    site properties.

    If the subclass does not set a generator, or does not override
    :meth:`treat` or :meth:`run`, `NotImplementedError` is raised.

    For bot options handling refer :class:`OptionHandler` class above.

    .. versionchanged:: 7.0
       A :attr:`counter` instance variable is provided.
    """

    use_disambigs: bool | None = None
    """Attribute to determine whether to use disambiguation pages. Set
    it to True to use disambigs only, set it to False to skip disambigs.
    If None both are processed.

    .. versionadded:: 7.2
    """

    use_redirects: bool | None = None
    """Attribute to determine whether to use redirect pages. Set it to
    True to use redirects only, set it to False to skip redirects. If
    None both are processed. For example to create a RedirectBot you may
    define:

    .. code-block:: python

       class MyRedirectBot(ExistingPageBot):

           '''Bot who only works on existing redirects.'''

           use_redirects = True

    .. versionadded:: 7.2
    """

    available_options = {
        'always': False,  # By default ask for confirmation when putting a page
    }

    update_options: dict[str, Any] = {}
    """`update_options` can be used to update :attr:`available_options`;
    do not use it if the bot class is to be derived but use
    `self.available_options.update(<dict>)` initializer in such case.

    .. versionadded:: 6.4
    """

    _current_page: pywikibot.page.BasePage | None = None

    def __init__(self, **kwargs: Any) -> None:
        """Initializer.

        :param kwargs: bot options
        :keyword generator: a :attr:`generator` processed by :meth:`run`
            method
        """
        if 'generator' in kwargs:
            if hasattr(self, 'generator'):
                warnings.warn(f'{type(self).__name__} has a generator'
                              ' already. Ignoring argument.')
            else:
                self.generator: Iterable = kwargs.pop('generator')

        self.available_options.update(self.update_options)
        super().__init__(**kwargs)

        self.counter: Counter = Counter()
        """Instance variable which holds counters. The default counters
        are 'read', 'write' and 'skip'. All of them are printed within
        :meth:`exit`. You can use your own counters like::

            self.counter['delete'] += 1

        .. versionadded:: 7.0
        .. versionchanged:: 7.3
           Your additional counters are also printed during :meth:`exit`
        """

        self.generator_completed: bool = False
        """
        Instance attribute which is True if the :attr:`generator` is completed.

        It gives False if the the generator processing in :meth:`run` is
        either interrupted by ``KeyboardInterrupt`` or exited by
        :exc:`QuitKeyboardInterrupt` while closing the generator i.e.
        :code:`self.generator.close()` keeps the value True.

        To check for an empty generator you may use::

            if self.generator_completed and not self.counter['read']:
                print('generator was emtpty')

        .. note:: An empty generator returns True.
        .. versionadded:: 3.0
        .. versionchanged:: 7.4
           renamed to `generator_completed` to become a public attribute.
        """

        self.treat_page_type: Any = pywikibot.page.BasePage
        """Instance variable to hold the default page type used by :meth:`run`.

        .. versionadded:: 6.1
        """

    @property
    def current_page(self) -> pywikibot.page.BasePage:
        """Return the current working page as a property."""
        assert self._current_page is not None
        return self._current_page

    @current_page.setter
    def current_page(self, page: pywikibot.page.BasePage) -> None:
        """Set the current working page as a property.

        When the value is actually changed, the page title is printed
        to the standard output (highlighted in purple) and logged
        with a VERBOSE level.

        This also prevents the same title from being printed twice.

        :param page: the working page
        """
        if page != self._current_page:
            self._current_page = page
            msg = f'Working on {page.title()!r}'
            if config.colorized_output:
                _log(msg)
                _stdout(
                    f'\n\n>>> <<lightpurple>>{page.title()}<<default>> <<<')
            else:
                _stdout(msg)

    def user_confirm(self, question: str) -> bool:
        """Obtain user response if bot option 'always' not enabled."""
        if self.opt.always:
            return True

        choice = pywikibot.input_choice(question,
                                        [('Yes', 'y'),
                                         ('No', 'N'),
                                         ('All', 'a'),
                                         ('Quit', 'q')],
                                        default='N',
                                        automatic_quit=False)

        if choice == 'n':
            return False

        if choice == 'q':
            self.quit()

        if choice == 'a':
            # Remember the choice
            self.opt.always = True

        return True

    def userPut(self, page: pywikibot.page.BasePage, oldtext: str,
                newtext: str, **kwargs: Any) -> bool:
        """Save a new revision of a page, with user confirmation as required.

        Print differences, ask user for confirmation, and puts the page
        if needed.

        Option used:

        * 'always'

        :keyword asynchronous: passed to page.save
        :keyword summary: passed to page.save
        :keyword show_diff: show changes between oldtext and newtext (enabled)
        :keyword ignore_save_related_errors: report and ignore (disabled)
        :keyword ignore_server_errors: report and ignore (disabled)
        :return: whether the page was saved successfully
        """
        if oldtext.rstrip() == newtext.rstrip():
            pywikibot.info(f'No changes were needed on {page}')
            return False

        self.current_page = page

        show_diff = kwargs.pop('show_diff', True)
        if show_diff:
            pywikibot.showDiff(oldtext, newtext)

        if 'summary' in kwargs:
            pywikibot.info(f"Edit summary: {kwargs['summary']}")

        page.text = newtext
        return self._save_page(page, page.save, **kwargs)

    def _save_page(self, page: pywikibot.page.BasePage,
                   func: Callable[..., Any], *args: Any,
                   **kwargs: Any) -> bool:
        """Helper function to handle page save-related option error handling.

        .. note:: Do no use it directly. Use :meth:`userPut` instead.

        :param page: currently edited page
        :param func: the function to call
        :param args: passed to the function
        :param kwargs: passed to the function
        :keyword ignore_server_errors: if True, server errors will be reported
            and ignored (default: False)
        :kwtype ignore_server_errors: bool
        :keyword ignore_save_related_errors: if True, errors related to
            page save will be reported and ignored (default: False)
        :kwtype ignore_save_related_errors: bool
        :return: whether the page was saved successfully

        :meta public:
        """
        if not self.user_confirm('Do you want to accept these changes?'):
            return False

        if 'asynchronous' not in kwargs and self.opt.always:
            kwargs['asynchronous'] = True

        ignore_save_related_errors = kwargs.pop('ignore_save_related_errors',
                                                False)
        ignore_server_errors = kwargs.pop('ignore_server_errors', False)

        try:
            func(*args, **kwargs)
            self.counter['write'] += 1
        except PageSaveRelatedError as e:
            if not ignore_save_related_errors:
                raise
            if isinstance(e, EditConflictError):
                pywikibot.info(
                    f'Skipping {page.title()} because of edit conflict')
            elif isinstance(e, SpamblacklistError):
                pywikibot.info(f'Cannot change {page.title()} because of '
                               f'blacklist entry {e.url}')
            elif isinstance(e, LockedPageError):
                pywikibot.info(f'Skipping {page.title()} (locked page)')
            else:
                _error(f'Skipping {page} because of a save related error: {e}')
        except ServerError as e:
            if not ignore_server_errors:
                raise
            _error(
                f'Server Error while processing {page.title()}: {e}')
        else:
            return True
        return False

    def quit(self) -> None:
        """Cleanup and quit processing."""
        raise QuitKeyboardInterrupt

    def exit(self) -> None:
        """Cleanup and exit processing.

        Invoked when :meth:`run` is finished. Waits for pending threads,
        prints counter statistics and informs whether the script
        terminated gracefully or was halted by exception.

        .. note:: Do not overwrite it by subclasses; :meth:`teardown`
           should be used instead.

        .. versionchanged:: 7.3
           Statistics are printed for all entries in :attr:`counter`
        .. versionchanged:: 9.0
           Print execution time with days, hours, minutes and seconds.
        """
        self.teardown()
        if hasattr(self, '_start_ts'):
            read_delta = pywikibot.Timestamp.now() - self._start_ts
            read_seconds = int(read_delta.total_seconds())

        # wait until pending threads finished but don't close the queue
        pywikibot.stopme()

        pywikibot.info()
        for op, count in self.counter.items():
            pywikibot.info(f"{count} {op} operation{'s' if count > 1 else ''}")

        if hasattr(self, '_start_ts'):
            write_delta = pywikibot.Timestamp.now() - self._start_ts
            write_seconds = int(write_delta.total_seconds())
            hours, remainder = divmod(write_delta.seconds, 3600)
            parts = write_delta.days, hours, *divmod(remainder, 60)
            units = ('days', 'hours', 'minutes', 'seconds')
            used = ', '.join(f'{value} {unit}'
                             for value, unit in zip(parts, units) if value)
            pywikibot.info('Execution time: ' + used)

            if self.counter['read']:
                pywikibot.info('Read operation time: {:.1f} seconds'
                               .format(read_seconds / self.counter['read']))

            for op, count in self.counter.items():
                if not count or op == 'read':
                    continue
                pywikibot.info(f'{op.capitalize()} operation time: '
                               f'{write_seconds / count:.1f} seconds')

        # exc_info contains exception from self.run() while terminating
        exc_info = sys.exc_info()
        pywikibot.info('Script terminated ', newline=False)
        if exc_info[0] is None or exc_info[0] is KeyboardInterrupt:
            pywikibot.info('successfully.')
        else:
            pywikibot.info('by exception:\n')
            _exception(exc_info=False)

    def init_page(self, item: Any) -> pywikibot.page.BasePage:
        """Initialize a generator item before treating.

        Ensure that the result of `init_page` is always a
        pywikibot.Page object or any other type given by the
        :attr:`treat_page_type` even when the generator returns
        something else.

        Also used to set the arrange the current site. This is called
        before :meth:`skip_page` and :meth:`treat`.

        :param item: any item from :attr:`generator`
        :return: return the page object to be processed further
        """
        return item

    def skip_page(self, page: pywikibot.page.BasePage) -> bool:
        """Return whether treat should be skipped for the page.

        .. versionadded:: 3.0

        .. versionchanged:: 7.2
           use :attr:`use_redirects` to handle redirects,
           use :attr:`use_disambigs` to handle disambigs

        :param page: Page object to be processed
        """
        if isinstance(self.use_redirects, bool) \
           and page.isRedirectPage() is not self.use_redirects:
            _warning(
                'Page {page} on {page.site} is skipped because it is {not_}'
                'a redirect'
                .format(page=page, not_='not ' if self.use_redirects else ''))
            return True

        if isinstance(self.use_disambigs, bool) \
           and page.isDisambig() is not self.use_disambigs:
            _warning(
                'Page {page} on {page.site} is skipped because it is {not_}'
                'a disambig'
                .format(page=page, not_='not ' if self.use_disambigs else ''))
            return True

        return False

    def treat(self, page: Any) -> None:
        """Process one page (abstract method).

        :param page: Object to be processed, usually a
            :class:`page.BasePage`. For other page types the
            :attr:`treat_page_type` must be set.
        """
        raise NotImplementedError(
            f'Method {type(self).__name__}.treat() not implemented.')

    def setup(self) -> None:
        """Some initial setup before :meth:`run` operation starts.

        This can be used for reading huge parts from life wiki or file
        operation which is more than just initialize the instance.
        Invoked by :meth:`run` before running through :attr:`generator`
        loop.

        .. versionadded:: 3.0
        """

    def teardown(self) -> None:
        """Some cleanups after :meth:`run` operation. Invoked by :meth:`exit`.

        .. versionadded:: 3.0
        """

    def run(self) -> None:
        """Process all pages in generator.

        Call :meth:`setup`, check for a valid ``Iterable`` type in
        :attr:`generator`, upcast it to a ``Generator`` type if
        necessary, process every generator`s item as follows:

        For each item call :meth:`init_page`, check whether the result
        is a :attr:`treat_page_type` type, call :meth:`skip_page` to
        determine whether to skip the current page. Otherwise call
        :meth:`treat` for each item.

        This method also adjust ``read`` and ``skip`` :attr:`counter`,
        and finally it calls :meth:`exit` when leaving the method. In
        short this method is implemented similar to this:

        .. code-block:: python

           def run(self) -> None:
               '''Process all pages in generator.'''
               self.setup()

               if not hasattr(self, 'generator'):
                   raise NotImplementedError('"generator" not set.')

               if self.generator is None;
                   print('No generator was defined')

               try:
                   for item in self.generator:
                       page = self.init_page(item)

                   if self.skip_page(page):
                       continue

                   self.treat(page)

               except(QuitKeyboardInterrupt, KeyboardInterrupt):
                   print('User canceled bot run.')

               finally:
                   self.exit()

        .. versionchanged:: 3.0
           ``skip`` counter was added.; call :meth:`setup` first.
        .. versionchanged:: 6.0
           upcast :attr:`generator` to a ``Generator`` type to enable
           ``generator.close()`` method.
        .. versionchanged:: 6.1
           Objects from :attr:`generator` may be different from
           :class:`pywikibot.Page` but the type must be registered in
           :attr:`treat_page_type`.
        .. versionchanged:: 9.2
           leave method gracefully if :attr:`generator` is None using
           :func:`suggest_help` function.

        :raise AssertionError: "page" is not a pywikibot.page.BasePage
            object
        :raise KeyboardInterrupt: KeyboardInterrupt occurred while
            :attr:`config.verbose_output` was set
        :raise NotImplementedError: :attr:`generator` is not set
        :raise TypeError: invalid generator type or page is not a
            :attr:`treat_page_type`
        """
        self._start_ts = pywikibot.Timestamp.now()
        self.setup()

        if not hasattr(self, 'generator'):
            raise NotImplementedError(
                f'Variable {type(self).__name__}.generator not set.')

        if suggest_help(missing_generator=self.generator is None):
            return

        if not isinstance(self.generator, Generator):
            gen_type = type(self.generator).__name__
            _debug(f'wrapping {gen_type} type to a Generator type')
            try:
                # to provide generator.close() method
                self.generator = (item for item in self.generator)
            except TypeError:
                raise TypeError(f'Invalid type {gen_type} for generator')

        try:
            for item in self.generator:
                # preprocessing of the page
                page = self.init_page(item)

                # validate page type
                if not isinstance(page, self.treat_page_type):
                    raise TypeError(f'"page" is not a {self.treat_page_type!r}'
                                    f' object but {type(page).__name__}.')

                if self.skip_page(page):
                    self.counter['skip'] += 1
                    continue

                # Process the page
                self.counter['read'] += 1
                self.treat(page)

            self.generator_completed = True
        except QuitKeyboardInterrupt:
            pywikibot.info(f'\nUser quit {type(self).__name__} bot run...')
        except KeyboardInterrupt:
            if config.verbose_output:
                raise

            pywikibot.info(
                f'\nKeyboardInterrupt during {type(self).__name__} bot run...')
        finally:
            self.exit()


# TODO: Deprecate Bot class as self.site may be the site of the page or may be
# a site previously defined
class Bot(BaseBot):

    """Generic bot subclass for multiple sites.

    If possible the MultipleSitesBot or SingleSiteBot classes should be used
    instead which specifically handle multiple or single sites.
    """

    def __init__(self, site: BaseSite | None = None,
                 **kwargs: Any) -> None:
        """Create a Bot instance and initialize cached sites."""
        # TODO: add warning if site is specified and generator
        # contains pages from a different site.
        self._site = site
        self._sites = set([self._site] if self._site else [])

        super().__init__(**kwargs)

    @property
    def site(self) -> BaseSite | None:
        """Get the current site."""
        if not self._site:
            _warning('Bot.site was not set before being retrieved.')
            self.site = pywikibot.Site()
            _warning(f'Using the default site: {self.site}')
        assert self._site is not None
        return self._site

    @site.setter
    def site(self, site: BaseSite | None) -> None:
        """Set the Site that the bot is using.

        When Bot.run() is managing the generator and site property, this is
        set each time a page is on a site different from the previous page.
        """
        if not site:
            self._site = None
            return

        if site not in self._sites:
            _log(f'LOADING SITE {site} VERSION: {site.mw_version}')

            self._sites.add(site)
            if len(self._sites) == 2:
                _log(f'{self.__class__.__name__} uses multiple sites')

        if self._site and self._site != site:
            _log(f'{type(self).__name__}: changing site from {self._site} '
                 f'to {site}')

        self._site = site

    def run(self) -> None:
        """Check if it automatically updates the site before run."""
        # This check is to remove the possibility that the superclass changing
        # self.site causes bugs in subclasses.
        # If the subclass has set self.site before run(), it may be that the
        # bot processes pages on sites other than self.site, and therefore
        # this method can't alter self.site. To use this functionality, don't
        # set self.site in __init__, and use page.site in treat().
        self._auto_update_site = not self._site
        if not self._auto_update_site:
            _warning(
                f'{type(self).__name__}.__init__ set the Bot.site property;'
                ' this is only needed when the Bot accesses many sites.'
            )
        else:
            _log(f'Bot is managing the {type(self).__name__}.site property in'
                 ' run()')
        super().run()

    def init_page(self, item: Any) -> pywikibot.page.BasePage:
        """Update site before calling treat."""
        # When in auto update mode, set the site when it changes,
        # so subclasses can hook onto changes to site.
        page = super().init_page(item)
        if (self._auto_update_site
                and (not self._site or page.site != self.site)):
            self.site = page.site
        return page


class SingleSiteBot(BaseBot):

    """A bot only working on one site and ignoring the others.

    If no site is given from the start it'll use the first page's site. Any
    page after the site has been defined and is not on the defined site will be
    ignored.
    """

    def __init__(self,
                 site: BaseSite | bool | None = True,
                 **kwargs: Any) -> None:
        """Create a SingleSiteBot instance.

        :param site: If True it'll be set to the configured site using
            pywikibot.Site.
        """
        if site is True:
            self._site: BaseSite | None = pywikibot.Site()
        elif site is False:
            raise ValueError("'site' must be a site, True, or None")
        else:
            self._site = site
        super().__init__(**kwargs)

    @property
    def site(self) -> BaseSite:
        """Site that the bot is using."""
        if not self._site:
            raise ValueError('The site has not been defined yet.')
        return self._site

    @site.setter
    def site(self, value: BaseSite | None) -> None:
        """Set the current site but warns if different."""
        if self._site:
            # Warn in any case where the site is (probably) changed after
            # setting it the first time. The appropriate variant is not to use
            # self.site at all or define it once and never change it again
            if self._site == value:
                _warning('Defined site without changing it.')
            else:
                _warning(f'Changed the site from "{self._site}" to "{value}"')
        self._site = value

    def init_page(self, item: Any) -> pywikibot.page.BasePage:
        """Set site if not defined."""
        page = super().init_page(item)
        if not self._site:
            self.site = page.site
        return page

    def skip_page(self, page: pywikibot.page.BasePage) -> bool:
        """Skip page if it is not on the defined site."""
        if page.site != self.site:
            _warning(fill(f'Skipped {page} due to: '
                          f'The bot is on site "{self.site}" but the page on '
                          f'site "{page.site}"'))
            return True
        return super().skip_page(page)


class MultipleSitesBot(BaseBot):

    """A bot class working on multiple sites.

    The bot should accommodate for that case and not store site specific
    information on only one site.

    .. versionchanged:: 6.2
       Site attribute has been dropped.
    """


class ConfigParserBot(BaseBot):

    """A bot class that can read options from scripts.ini file.

    All options must be predefined in available_options dictionary. The type
    of these options is responsible for the correct interpretation of the
    options type given by the .ini file. They can be interpreted as bool,
    int, float or str (default). The settings file may be like::

        [add_text]
        # edit summary for the bot.
        summary = Bot: Aggiungo template Categorizzare

        [commonscat] ; commonscat options
        always: true

    The option values are interpreted in this order:

    1. `available_options` default setting
    2. `script.ini options` settings
    3. command line arguments

    .. versionadded:: 3.0
    """

    INI = 'scripts.ini'

    def set_options(self, **kwargs: Any) -> None:
        """Read settings from scripts.ini file."""
        conf = configparser.ConfigParser(inline_comment_prefixes=[';'])
        section = calledModuleName()

        if (conf.read(self.INI) == [self.INI] and conf.has_section(section)):
            pywikibot.info(f'Reading settings from {self.INI} file.')
            options = {}
            for option, value in self.available_options.items():
                if not conf.has_option(section, option):
                    continue
                # use a convenience parser method, default to get()
                default = conf.get
                value_type = type(value).__name__
                if value_type == 'bool':
                    method = conf.getboolean
                else:
                    method = getattr(conf, 'get' + value_type, default)
                options[option] = method(section, option)
            for opt in set(conf.options(section)) - set(options):
                _warning(f'"{opt}" is not a valid option. It was ignored.')
            options.update(kwargs)
        else:
            options = kwargs

        super().set_options(**options)


class CurrentPageBot(BaseBot):

    """A bot which automatically sets 'current_page' on each treat().

    This class should be always used together with either the MultipleSitesBot
    or SingleSiteBot class as there is no site management in this class.
    """

    ignore_save_related_errors = True
    ignore_server_errors = False

    def treat_page(self) -> None:
        """Process one page (Abstract method)."""
        raise NotImplementedError(
            f'Method {type(self).__name__}.treat_page() not implemented.')

    def treat(self, page: pywikibot.page.BasePage) -> None:
        """Set page to current page and treat that page."""
        self.current_page = page
        self.treat_page()

    def put_current(self, new_text: str,
                    ignore_save_related_errors: bool | None = None,
                    ignore_server_errors: bool | None = None,
                    **kwargs: Any) -> bool:
        """Call :py:obj:`Bot.userPut` but use the current page.

        It compares the new_text to the current page text.

        :param new_text: The new text
        :param ignore_save_related_errors: Ignore save related errors and
            automatically print a message. If None uses this instances default.
        :param ignore_server_errors: Ignore server errors and automatically
            print a message. If None uses this instances default.
        :param kwargs: Additional parameters directly given to
            :py:obj:`Bot.userPut`.
        :return: whether the page was saved successfully
        """
        if ignore_save_related_errors is None:
            ignore_save_related_errors = self.ignore_save_related_errors
        if ignore_server_errors is None:
            ignore_server_errors = self.ignore_server_errors
        return self.userPut(
            self.current_page, self.current_page.text, new_text,
            ignore_save_related_errors=ignore_save_related_errors,
            ignore_server_errors=ignore_server_errors,
            **kwargs)


class AutomaticTWSummaryBot(CurrentPageBot):

    """A class which automatically defines ``summary`` for ``put_current``.

    The class must defined a ``summary_key`` string which contains the
    i18n key for :py:obj:`i18n.twtranslate`. It can also
    override the ``summary_parameters`` property to specify any
    parameters for the translated message.
    """

    #: Must be defined in subclasses.
    summary_key: str | None = None

    @property
    def summary_parameters(self) -> dict[str, str]:
        """A dictionary of all parameters for i18n."""
        if hasattr(self, '_summary_parameters'):
            return self._summary_parameters
        return {}

    @summary_parameters.setter
    def summary_parameters(self, value: dict[str, str]) -> None:
        """Set the i18n dictionary."""
        if not isinstance(value, dict):
            raise TypeError(
                f'"value" must be a dict but {type(value).__name__} was found.'
            )
        self._summary_parameters = value

    @summary_parameters.deleter
    def summary_parameters(self) -> None:
        """Delete the i18n dictionary."""
        del self._summary_parameters

    def put_current(self, *args: Any, **kwargs: Any) -> None:
        """Defining a summary if not already defined and then call original."""
        if not kwargs.get('summary'):
            if self.summary_key is None:
                raise ValueError('The summary_key must be set.')
            summary = i18n.twtranslate(self.current_page.site,
                                       self.summary_key,
                                       self.summary_parameters)
            _log(f'Use automatic summary message "{summary}"')
            kwargs['summary'] = summary
        super().put_current(*args, **kwargs)


class ExistingPageBot(CurrentPageBot):

    """A CurrentPageBot class which only treats existing pages."""

    def skip_page(self, page: pywikibot.page.BasePage) -> bool:
        """Treat page if it exists and handle NoPageError.

        .. warning:: If subclassed, call `super().skip_page()` first to
           ensure that non existent pages are filtered before other
           calls are made
        """
        if not page.exists():
            _warning(f'Page {page} does not exist on {page.site}.')
            return True
        return super().skip_page(page)


class FollowRedirectPageBot(CurrentPageBot):

    """A CurrentPageBot class which follows the redirect."""

    def treat(self, page: pywikibot.page.BasePage) -> None:
        """Treat target if page is redirect and the page otherwise."""
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        super().treat(page)


class CreatingPageBot(CurrentPageBot):

    """A CurrentPageBot class which only treats nonexistent pages."""

    def skip_page(self, page: pywikibot.page.BasePage) -> bool:
        """Treat page if doesn't exist."""
        if page.exists():
            _warning(f'Page {page} does already exist on {page.site}.')
            return True
        return super().skip_page(page)


class WikidataBot(Bot, ExistingPageBot):

    """Generic Wikidata Bot to be subclassed.

    Source claims (P143) can be created for specific sites

    :cvar use_from_page: If True (default) it will apply ItemPage.fromPage
        for every item. If False it assumes that the pages are actually
        already ItemPage (page in treat_page_and_item will be None).
        If None it'll use ItemPage.fromPage when the page is not in the site's
        item namespace.

    :type use_from_page: bool, None

    :cvar treat_missing_item: Whether pages without items should be treated.
        Note that this is checked after create_missing_item.

    :type treat_missing_item: bool

    :ivar create_missing_item: If True, new items will be created if the
        current page doesn't have one. Subclasses should override this in the
        initializer with a bool value or using self.opt attribute.

    :type create_missing_item: bool
    """

    use_from_page = True
    treat_missing_item = False

    def __init__(self, **kwargs: Any) -> None:
        """Initializer of the WikidataBot."""
        self.create_missing_item = False
        super().__init__(**kwargs)
        self.site = pywikibot.Site()
        self.repo = self.site.data_repository()
        if self.repo is None:
            raise WikiBaseError(
                f'{self.site} is not connected to a data repository')

    def cacheSources(self) -> None:
        """Fetch the sources from the list on Wikidata.

        It is stored internally and reused by getSource()
        """
        page = pywikibot.Page(self.repo, 'List of wikis/python', ns=4)
        self.source_values = json.loads(page.get())
        for family_code, family in self.source_values.items():
            for source_lang in family:
                self.source_values[
                    family_code][source_lang] = pywikibot.ItemPage(
                        self.repo, family[source_lang])

    def get_property_by_name(self, property_name: str) -> str:
        """Find given property and return its ID.

        Method first uses site.search() and if the property isn't found,
        then asks user to provide the property ID.

        :param property_name: property to find
        """
        ns = self.repo.property_namespace
        for page in self.repo.search(property_name, total=1, namespaces=ns):
            prop = pywikibot.PropertyPage(self.repo, page.title())
            pywikibot.info(
                f'Assuming that {property_name} property is {prop.id}.')
            return prop.id

        return pywikibot.input(
            f'Property {property_name} was not found. Please enter the '
            f'property ID (e.g. P123) of it:').upper()

    def user_edit_entity(self, entity: pywikibot.page.WikibasePage,
                         data: dict[str, str] | None = None,
                         ignore_save_related_errors: bool | None = None,
                         ignore_server_errors: bool | None = None,
                         **kwargs: Any) -> bool:
        """Edit entity with data provided, with user confirmation as required.

        :param entity: page to be edited
        :param data: data to be saved, or None if the diff should be created
          automatically
        :param ignore_save_related_errors: Ignore save related errors and
            automatically print a message. If None uses this instances default.
        :param ignore_server_errors: Ignore server errors and automatically
            print a message. If None uses this instances default.
        :keyword summary: revision comment, passed to ItemPage.editEntity
        :keyword show_diff: show changes between oldtext and newtext (default:
          True)
        :return: whether the item was saved successfully
        """
        if ignore_save_related_errors is None:
            ignore_save_related_errors = self.ignore_save_related_errors
        if ignore_server_errors is None:
            ignore_server_errors = self.ignore_server_errors
        show_diff = kwargs.pop('show_diff', True)
        if show_diff:
            if data is None:
                diff = entity.toJSON(diffto=getattr(entity, '_content', None))
            else:
                diff = entity._normalizeData(data)
            pywikibot.info(json.dumps(diff, indent=4, sort_keys=True))

        if 'summary' in kwargs:
            pywikibot.info(f"Change summary: {kwargs['summary']}")

        # TODO PageSaveRelatedErrors should be actually raised in editEntity
        # (bug T86083)
        return self._save_page(
            entity, entity.editEntity, data,
            ignore_save_related_errors=ignore_save_related_errors,
            ignore_server_errors=ignore_server_errors, **kwargs)

    def user_add_claim(self, item: pywikibot.page.ItemPage,
                       claim: pywikibot.page.Claim,
                       source: BaseSite | None = None,
                       bot: bool = True, **kwargs: Any) -> bool:
        """Add a claim to an item, with user confirmation as required.

        :param item: page to be edited
        :param claim: claim to be saved
        :param source: site where the claim comes from
        :param bot: whether to flag as bot (if possible)
        :keyword ignore_server_errors: if True, server errors will be reported
          and ignored (default: False)
        :keyword ignore_save_related_errors: if True, errors related to
          page save will be reported and ignored (default: False)
        :return: whether the item was saved successfully

        .. note:: calling this method sets the current_page property
           to the item which changes the site property

        .. note:: calling this method with the 'source' argument modifies
           the provided claim object in place
        """
        self.current_page = item

        if source:
            sourceclaim = self.getSource(source)
            if sourceclaim:
                claim.addSource(sourceclaim)

        pywikibot.info(f'Adding {claim.getID()} --> {claim.getTarget()}')
        return self._save_page(item, item.addClaim, claim, bot=bot, **kwargs)

    def getSource(self, site: BaseSite) -> pywikibot.page.Claim | None:
        """Create a Claim usable as a source for Wikibase statements.

        :param site: site that is the source of assertions.

        :return: pywikibot.Claim or None
        """
        source = None
        item = i18n.translate(site, self.source_values)
        if item:
            source = pywikibot.Claim(self.repo, 'P143')
            source.setTarget(item)
        return source

    def user_add_claim_unless_exists(
            self, item: pywikibot.page.ItemPage,
            claim: pywikibot.page.Claim,
            exists_arg: Container = '',
            source: BaseSite | None = None,
            logger_callback: Callable[[str], Any] = pwb_logging.log,
            **kwargs: Any) -> bool:
        """Decorator of :py:obj:`user_add_claim`.

        Before adding a new claim, it checks if we can add it, using provided
        filters.

        .. seealso:: documentation of :py:obj:`claimit.py<scripts.claimit>`

        :param exists_arg: pattern for merging existing claims with new ones
        :param logger_callback: function logging the output of the method
        :return: whether the claim could be added

        .. note:: calling this method may change the current_page property
           to the item which will also change the site property

        .. note:: calling this method with the 'source' argument modifies
           the provided claim object in place
        """
        # This code is somewhat duplicate to user_add_claim but
        # unfortunately we need the source claim here, too.
        sourceclaim = self.getSource(source) if source else None

        # Existing claims on page of same property
        claims = item.get().get('claims')
        assert claims is not None

        claim_id = claim.getID()
        for existing in claims.get(claim_id, []):
            # If claim with same property already exists...
            if 'p' not in exists_arg:
                logger_callback(
                    f'Skipping {claim_id} because claim with same property'
                    ' already exists')
                _log('Use -exists:p option to override this behavior')
                break

            if not existing.target_equals(claim.getTarget()):
                continue

            # If some attribute of the claim being added
            # matches some attribute in an existing claim of
            # the same property, skip the claim, unless the
            # 'exists' argument overrides it.
            if 't' not in exists_arg:
                logger_callback(
                    f'Skipping {claim_id} because claim with same target'
                    ' already exists')
                _log("Append 't' to -exists argument to override this "
                     'behavior')
                break

            if 'q' not in exists_arg and not existing.qualifiers:
                logger_callback(
                    f'Skipping {claim_id} because claim without qualifiers'
                    ' already exists')
                _log("Append 'q' to -exists argument to override this "
                     'behavior')
                break

            if ('s' not in exists_arg or not sourceclaim) \
               and not existing.sources:
                logger_callback(
                    f'Skipping {claim_id} because claim without source already'
                    ' exists')
                _log("Append 's' to -exists argument to override this "
                     'behavior')
                break

            # FIXME: the user may provide a better source, but we only
            # assume it's the default one
            if ('s' not in exists_arg and sourceclaim
                and any(sourceclaim.getID() in ref
                        and all(snak.target_equals(sourceclaim.getTarget())
                                for snak in ref[sourceclaim.getID()])
                        for ref in existing.sources)):
                logger_callback(
                    f'Skipping {claim_id} because claim with the same source'
                    ' already exists')
                _log("Append 's' to -exists argument to override this "
                     'behavior')
                break
        else:
            return self.user_add_claim(item, claim, source, **kwargs)

        return False

    def create_item_for_page(self, page: pywikibot.page.BasePage,
                             data: dict[str, Any] | None = None,
                             summary: str | None = None,
                             **kwargs: Any
                             ) -> pywikibot.page.ItemPage | None:
        """Create an ItemPage with the provided page as the sitelink.

        :param page: the page for which the item will be created
        :param data: additional data to be included in the new item (optional).
            Note that data created from the page have higher priority.
        :param summary: optional edit summary to replace the default one

        :return: pywikibot.ItemPage or None
        """
        if not summary:
            summary = ('Bot: New item with sitelink from '
                       f'{page.title(as_link=True, insite=self.repo)}')

        if data is None:
            data = {}
        data.setdefault('sitelinks', {}).update({
            page.site.dbName(): {
                'site': page.site.dbName(),
                'title': page.title()
            }
        })
        data.setdefault('labels', {}).update({
            page.site.lang: {
                'language': page.site.lang,
                'value': page.title(without_brackets=page.namespace() == 0)
            }
        })
        pywikibot.info(f'Creating item for {page}...')
        item = pywikibot.ItemPage(page.site.data_repository())
        kwargs.setdefault('show_diff', False)
        result = self.user_edit_entity(item, data, summary=summary, **kwargs)
        if result:
            return item
        return None

    def treat_page(self) -> None:
        """Treat a page."""
        page: pywikibot.page.BasePage | None = self.current_page
        if self.use_from_page is True:
            try:
                item = pywikibot.ItemPage.fromPage(page)
            except NoPageError:
                item = None
        elif isinstance(page, pywikibot.ItemPage):
            item = page
            page = None
        else:
            # FIXME: Hack because 'is_data_repository' doesn't work if
            #        site is the APISite. See T85483
            assert page is not None
            data_site = page.site.data_repository()
            if (data_site.family == page.site.family
                    and data_site.code == page.site.code):
                is_item = page.namespace() == data_site.item_namespace.id
            else:
                is_item = False
            if is_item:
                item = pywikibot.ItemPage(data_site, page.title())
                page = None
            else:
                try:
                    item = pywikibot.ItemPage.fromPage(page)
                except NoPageError:
                    item = None
                if self.use_from_page is False:
                    _error(f'{page} is not in the item namespace but must'
                           ' be an item.')
                    return

        assert not (page is None and item is None)

        if not item and self.create_missing_item:
            item = self.create_item_for_page(page, asynchronous=False)

        if not item and not self.treat_missing_item:
            pywikibot.info(f"{page} doesn't have a Wikidata item.")
            return

        self.treat_page_and_item(page, item)

    def treat_page_and_item(self, page: pywikibot.page.BasePage,
                            item: pywikibot.page.ItemPage) -> None:
        """Treat page together with its item (if it exists).

        Must be implemented in subclasses.
        """
        raise NotImplementedError(f'Method {type(self).__name__}.'
                                  'treat_page_and_item() not implemented.')


set_interface(config.userinterface)

critical = redirect_func(pwb_logging.critical,
                         target_module='pywikibot',
                         since='9.2.0')
debug = redirect_func(_debug,
                      target_module='pywikibot',
                      since='9.2.0')
error = redirect_func(_error,
                      target_module='pywikibot',
                      since='9.2.0')
exception = redirect_func(_exception,
                          target_module='pywikibot',
                          since='9.2.0')
log = redirect_func(_log,
                    target_module='pywikibot',
                    since='9.2.0')
output = redirect_func(pwb_logging.output,
                       target_module='pywikibot',
                       since='9.2.0')
stdout = redirect_func(_stdout,
                       target_module='pywikibot',
                       since='9.2.0')
warning = redirect_func(_warning,
                        target_module='pywikibot',
                        since='9.2.0')

# NOTE: (T286348)
# Do not use ModuleDeprecationWrapper with this module.
# pywikibot.bot.ui would be wrapped through the ModuleDeprecationWrapper
# and a cannot be changed later. Use another depecation method instead
# (until T286348 has been solved somehow different).
