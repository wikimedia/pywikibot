# -*- coding: utf-8 -*-
"""
User-interface related functions for building bots.

This module supports several different bot classes which could be used in
conjunction. Each bot should subclass at least one of these four classes:

* L{BaseBot}: Basic bot class in case where the site is handled differently,
  like working on two sites in parallel.

* L{SingleSiteBot}: Bot class which should only be run on a single site. They
  usually store site specific content and thus can't be easily run when the
  generator returns a page on another site. It has a property C{site} which
  can also be changed. If the generator returns a page of a different site
  it'll skip that page.

* L{MultipleSitesBot}: Bot class which supports to be run on multiple sites
  without the need to manually initialize it every time. It is not possible to
  set the C{site} property and it's deprecated to request it. Instead site of
  the current page should be used. And out of C{run} that sit isn't defined.

* L{Bot}: The previous base class which should be avoided. This class is mainly
  used for bots which work with wikibase or together with an image repository.

Additionally there is the L{CurrentPageBot} class which automatically sets the
current page to the page treated. It is recommended to use this class and to
use C{treat_page} instead of C{treat} and C{put_current} instead of C{userPut}.
It by default subclasses the C{BaseBot} class.

With L{CurrentPageBot} it's possible to subclass one of the following classes
to filter the pages which are ultimately handled by C{treat_page}:

* L{ExistingPageBot}: Only handle pages which do exist.
* L{CreatingPageBot}: Only handle pages which do not exist.
* L{RedirectPageBot}: Only handle pages which are redirect pages.
* L{NoRedirectPageBot}: Only handle pages which are not redirect pages.
* L{FollowRedirectPageBot}: If the generator returns a redirect page it'll
  follow the redirect and instead work on the redirected class.

It is possible to combine filters by subclassing multiple of them. They are
new-style classes so when a class is first subclassing L{ExistingPageBot} and
then L{FollowRedirectPageBot} it will also work on pages which do not exist
when a redirect pointed to that. If the order is inversed it'll first follow
them and then check whether they exist.

Additionally there is the L{AutomaticTWSummaryBot} which subclasses
L{CurrentPageBot} and automatically defines the summary when C{put_current} is
used.
"""
#
# (C) Pywikibot team, 2008-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

# Note: the intention is to develop this module (at some point) into a Bot
# class definition that can be subclassed to create new, functional bot
# scripts, instead of writing each one from scratch.

__all__ = (
    'CRITICAL', 'ERROR', 'INFO', 'WARNING', 'DEBUG', 'INPUT', 'STDOUT',
    'VERBOSE', 'critical', 'debug', 'error', 'exception', 'log', 'warning',
    'output', 'stdout', 'LoggingFormatter', 'RotatingFileHandler',
    'init_handlers', 'writelogheader',
    'input', 'input_choice', 'input_yn', 'inputChoice', 'input_list_choice',
    'Option', 'StandardOption', 'NestedOption', 'IntegerOption',
    'ContextOption', 'ListOption', 'OutputProxyOption',
    'HighlightContextOption', 'ChoiceException', 'UnhandledAnswer',
    'Choice', 'AlwaysChoice',
    'QuitKeyboardInterrupt',
    'InteractiveReplace',
    'calledModuleName', 'handle_args', 'handleArgs',
    'showHelp', 'suggest_help',
    'writeToCommandLogFile', 'open_webbrowser',
    'OptionHandler',
    'BaseBot', 'Bot', 'SingleSiteBot', 'MultipleSitesBot',
    'CurrentPageBot', 'AutomaticTWSummaryBot',
    'ExistingPageBot', 'FollowRedirectPageBot', 'CreatingPageBot',
    'RedirectPageBot', 'NoRedirectPageBot',
    'WikidataBot',
)

# Note: all output goes thru python std library "logging" module

import codecs
import datetime
import json
import logging
import logging.handlers
import os
import sys
import time
import warnings
from warnings import warn
import webbrowser

import pywikibot
from pywikibot import config2 as config
from pywikibot import daemonize
from pywikibot import i18n
from pywikibot import version
from pywikibot.bot_choice import (
    Option, StandardOption, NestedOption, IntegerOption, ContextOption,
    ListOption, OutputProxyOption, HighlightContextOption,
    ChoiceException, QuitKeyboardInterrupt,
)
from pywikibot.logging import (
    CRITICAL, ERROR, INFO, WARNING,
)
from pywikibot.logging import DEBUG, INPUT, STDOUT, VERBOSE
from pywikibot.logging import (
    add_init_routine,
    debug, error, exception, log, output, stdout, warning,
)
from pywikibot.logging import critical
from pywikibot.tools import (
    deprecated, deprecate_arg, deprecated_args, PY2,
)
from pywikibot.tools._logging import (
    LoggingFormatter as _LoggingFormatter,
    RotatingFileHandler,
)
from pywikibot.tools.formatter import color_format


_logger = 'bot'

if not PY2:
    unicode = str

# User interface initialization
# search for user interface module in the 'userinterfaces' subdirectory
uiModule = __import__("pywikibot.userinterfaces.%s_interface"
                      % config.userinterface,
                      fromlist=['UI'])
ui = uiModule.UI()
pywikibot.argvu = ui.argvu()


# It's not possible to use pywikibot.exceptions.PageRelatedError as that is
# importing pywikibot.data.api which then needs pywikibot.bot
class SkipPageError(Exception):

    """Skipped page in run."""

    message = 'Page "{0}" skipped due to {1}.'

    def __init__(self, page, reason):
        """Constructor."""
        super(SkipPageError, self).__init__(self.message.format(page, reason))
        self.reason = reason
        self.page = page


class UnhandledAnswer(Exception):

    """The given answer didn't suffice."""

    def __init__(self, stop=False):
        """Constructor."""
        self.stop = stop


class LoggingFormatter(_LoggingFormatter):

    """Logging formatter that uses config.console_encoding."""

    def __init__(self, fmt=None, datefmt=None):
        """Constructor setting underlying encoding to console_encoding."""
        _LoggingFormatter.__init__(self, fmt, datefmt, config.console_encoding)


# Initialize the handlers and formatters for the logging system.
#
# This relies on the global variable 'ui' which is a UserInterface object
# defined in the 'userinterface' subpackage.
#
# The UserInterface object must define its own init_handlers() method
# which takes the root logger as its only argument, and which adds to that
# logger whatever handlers and formatters are needed to process output and
# display it to the user. The default (terminal) interface sends level
# STDOUT to sys.stdout (as all interfaces should) and sends all other
# levels to sys.stderr; levels WARNING and above are labeled with the
# level name.
#
# UserInterface objects must also define methods input(), input_choice(),
# and editText(), all of which are documented in
# userinterfaces/terminal_interface.py

_handlers_initialized = False


def init_handlers(strm=None):
    """Initialize logging system for terminal-based bots.

    This function must be called before using pywikibot.output(); and must
    be called again if the destination stream is changed.

    Note: this function is called by handleArgs(), so it should normally
    not need to be called explicitly

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

    Accordingly, do **not** use print statements in bot code; instead,
    use pywikibot.output function.

    @param strm: Output stream. If None, re-uses the last stream if one
        was defined, otherwise uses sys.stderr

    """
    global _handlers_initialized

    moduleName = calledModuleName()
    if not moduleName:
        moduleName = "terminal-interface"

    logging.addLevelName(VERBOSE, "VERBOSE")
    # for messages to be displayed on terminal at "verbose" setting
    # use INFO for messages to be displayed even on non-verbose setting

    logging.addLevelName(STDOUT, "STDOUT")
    # for messages to be displayed to stdout

    logging.addLevelName(INPUT, "INPUT")
    # for prompts requiring user response

    root_logger = logging.getLogger("pywiki")
    root_logger.setLevel(DEBUG + 1)  # all records except DEBUG go to logger

    warnings_logger = logging.getLogger("py.warnings")
    warnings_logger.setLevel(DEBUG)

    # If there are command line warnings options, do not override them
    if not sys.warnoptions:
        logging.captureWarnings(True)

        if config.debug_log or 'deprecation' in config.log:
            warnings.filterwarnings("always")
        elif config.verbose_output:
            warnings.filterwarnings("module")

    root_logger.handlers = []  # remove any old handlers

    # configure handler(s) for display to user interface
    ui.init_handlers(root_logger, **config.userinterface_init_kwargs)

    # if user has enabled file logging, configure file handler
    if moduleName in config.log or '*' in config.log:
        if config.logfilename:
            logfile = config.datafilepath("logs", config.logfilename)
        else:
            logfile = config.datafilepath("logs", "%s-bot.log" % moduleName)
        file_handler = RotatingFileHandler(filename=logfile,
                                           maxBytes=1024 * config.logfilesize,
                                           backupCount=config.logfilecount)

        file_handler.setLevel(DEBUG)
        form = LoggingFormatter(
            fmt="%(asctime)s %(caller_file)18s, %(caller_line)4s "
                "in %(caller_name)18s: %(levelname)-8s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(form)
        root_logger.addHandler(file_handler)
        # Turn on debugging for each component requested by user
        # or for all components if nothing was specified
        for component in config.debug_log:
            if component:
                debuglogger = logging.getLogger("pywiki." + component)
            else:
                debuglogger = logging.getLogger("pywiki")
            debuglogger.setLevel(DEBUG)
            debuglogger.addHandler(file_handler)

        warnings_logger.addHandler(file_handler)

    _handlers_initialized = True

    writelogheader()


def writelogheader():
    """
    Save additional version, system and status info to the log file in use.

    This may help the user to track errors or report bugs.
    """
    # If a http thread is not available, it's too early to print a header
    # that includes version information, which may need to query a server.
    # The http module can't be imported due to circular dependencies.
    http = sys.modules.get('pywikibot.comms.http', None)
    if not http or not hasattr(http, 'threads') or not len(http.threads):
        return

    log(u'=== Pywikibot framework v3.0 -- Logging header ===')

    # script call
    log(u'COMMAND: {0}'.format(sys.argv))

    # script call time stamp
    log(u'DATE: %s UTC' % str(datetime.datetime.utcnow()))

    # new framework release/revision? (handleArgs needs to be called first)
    try:
        log(u'VERSION: %s' %
            version.getversion(online=config.log_pywiki_repo_version).strip())
    except version.ParseError:
        exception()

    # system
    if hasattr(os, 'uname'):
        log(u'SYSTEM: {0}'.format(os.uname()))

    # config file dir
    log(u'CONFIG FILE DIR: %s' % pywikibot.config2.base_dir)

    all_modules = sys.modules.keys()

    # These are the main dependencies of pywikibot.
    check_package_list = [
        'requests',
        'mwparserfromhell',
        'unicodedata', 'unicodedata2',  # T102461
    ]

    # report all imported packages
    if config.verbose_output:
        check_package_list += all_modules

    packages = version.package_versions(check_package_list)

    log(u'PACKAGES:')
    for name in sorted(packages.keys()):
        info = packages[name]
        if 'path' not in info:
            if 'type' in info:
                info['path'] = '[' + info['type'] + ']'
            else:
                info['path'] = '[path unknown]'
        if 'ver' not in info:
            info['ver'] = '??'
        if 'err' in info:
            log(u'  %(name)s: %(err)s' % info)
        else:
            log(u'  %(name)s (%(path)s) = %(ver)s' % info)

    # imported modules
    log(u'MODULES:')
    for module in sys.modules.values():
        filename = version.get_module_filename(module)
        ver = version.get_module_version(module)
        mtime = version.get_module_mtime(module)
        if filename and ver and mtime:
            # it's explicitly using str() to bypass unicode_literals in py2
            # isoformat expects a char not a unicode in Python 2
            log(u'  {0} {1} {2}'.format(filename, ver[:7],
                                        mtime.isoformat(str(' '))))

    if config.log_pywiki_repo_version:
        log(u'PYWIKI REPO VERSION: %s' % version.getversion_onlinerepo())

    log(u'=== ' * 14)


add_init_routine(init_handlers)


# User input functions


def input(question, password=False, default='', force=False):
    """Ask the user a question, return the user's answer.

    @param question: a string that will be shown to the user. Don't add a
        space after the question mark/colon, this method will do this for you.
    @type question: unicode
    @param password: if True, hides the user's input (for password entry).
    @type password: bool
    @param default: The default answer if none was entered. None to require
        an answer.
    @type default: basestring
    @param force: Automatically use the default
    @type force: bool
    @rtype: unicode
    """
    # make sure logging system has been initialized
    if not _handlers_initialized:
        init_handlers()

    data = ui.input(question, password=password, default=default, force=force)
    return data


def input_choice(question, answers, default=None, return_shortcut=True,
                 automatic_quit=True, force=False):
    """
    Ask the user the question and return one of the valid answers.

    @param question: The question asked without trailing spaces.
    @type question: basestring
    @param answers: The valid answers each containing a full length answer and
        a shortcut. Each value must be unique.
    @type answers: iterable containing a sequence of length two or instances of
        ChoiceException
    @param default: The result if no answer was entered. It must not be in the
        valid answers and can be disabled by setting it to None. If it should
        be linked with the valid answers it must be its shortcut.
    @type default: basestring
    @param return_shortcut: Whether the shortcut or the index of the answer is
        returned.
    @type return_shortcut: bool
    @param automatic_quit: Adds the option 'Quit' ('q') and throw a
        L{QuitKeyboardInterrupt} if selected.
    @type automatic_quit: bool
    @param force: Automatically use the default
    @type force: bool
    @return: The selected answer shortcut or index. Is -1 if the default is
        selected, it does not return the shortcut and the default is not a
        valid shortcut.
    @rtype: int (if not return shortcut), basestring (otherwise)
    """
    # make sure logging system has been initialized
    if not _handlers_initialized:
        init_handlers()

    return ui.input_choice(question, answers, default, return_shortcut,
                           automatic_quit=automatic_quit, force=force)


def input_yn(question, default=None, automatic_quit=True, force=False):
    """
    Ask the user a yes/no question and return the answer as a bool.

    @param question: The question asked without trailing spaces.
    @type question: basestring
    @param default: The result if no answer was entered. It must be a bool or
        'y' or 'n' and can be disabled by setting it to None.
    @type default: basestring or bool
    @param automatic_quit: Adds the option 'Quit' ('q') and throw a
        L{QuitKeyboardInterrupt} if selected.
    @type automatic_quit: bool
    @param force: Automatically use the default
    @type force: bool
    @return: Return True if the user selected yes and False if the user
        selected no. If the default is not None it'll return True if default
        is True or 'y' and False if default is False or 'n'.
    @rtype: bool
    """
    if default not in ['y', 'Y', 'n', 'N']:
        if default:
            default = 'y'
        elif default is not None:
            default = 'n'
    assert default in ['y', 'Y', 'n', 'N', None], \
        'Default choice must be one of YyNn or default'

    return input_choice(question, [('Yes', 'y'), ('No', 'n')], default,
                        automatic_quit=automatic_quit, force=force) == 'y'


@deprecated('input_choice')
def inputChoice(question, answers, hotkeys, default=None):
    """Ask the user a question with several options, return the user's choice.

    DEPRECATED: Use L{input_choice} instead!

    The user's input will be case-insensitive, so the hotkeys should be
    distinctive case-insensitively.

    @param question: a string that will be shown to the user. Don't add a
        space after the question mark/colon, this method will do this for you.
    @type question: basestring
    @param answers: a list of strings that represent the options.
    @type answers: list of basestring
    @param hotkeys: a list of one-letter strings, one for each answer.
    @param default: an element of hotkeys, or None. The default choice that
        will be returned when the user just presses Enter.
    @return: a one-letter string in lowercase.
    @rtype: str
    """
    # make sure logging system has been initialized
    if not _handlers_initialized:
        init_handlers()

    return ui.input_choice(question=question, options=zip(answers, hotkeys),
                           default=default, return_shortcut=True,
                           automatic_quit=False)


def input_list_choice(question, answers, default=None, force=False):
    """
    Ask the user the question and return one of the valid answers.

    @param question: The question asked without trailing spaces.
    @type question: basestring
    @param answers: The valid answers each containing a full length answer.
    @type answers: Iterable of basestring
    @param default: The result if no answer was entered. It must not be in the
        valid answers and can be disabled by setting it to None.
    @type default: basestring
    @param force: Automatically use the default
    @type force: bool
    @return: The selected answer.
    @rtype: basestring
    """
    if not _handlers_initialized:
        init_handlers()

    return ui.input_list_choice(question, answers, default=default,
                                force=force)


class Choice(StandardOption):

    """A simple choice consisting of a option, shortcut and handler."""

    def __init__(self, option, shortcut, replacer):
        """Constructor."""
        super(Choice, self).__init__(option, shortcut)
        self._replacer = replacer

    @property
    def replacer(self):
        """The replacer."""
        return self._replacer

    def handle(self):
        """Handle this choice. Must be implemented."""
        raise NotImplementedError()

    def handle_link(self):
        """The current link will be handled by this choice."""
        return False


class StaticChoice(Choice):

    """A static choice which just returns the given value."""

    def __init__(self, option, shortcut, result):
        """Create instance with replacer set to None."""
        super(StaticChoice, self).__init__(option, shortcut, None)
        self._result = result

    def handle(self):
        """Return the predefined value."""
        return self._result


class LinkChoice(Choice):

    """A choice returning a mix of the link new and current link."""

    def __init__(self, option, shortcut, replacer, replace_section,
                 replace_label):
        """Constructor."""
        super(LinkChoice, self).__init__(option, shortcut, replacer)
        self._section = replace_section
        self._label = replace_label

    def handle(self):
        """Handle by either applying the new section or label."""
        kwargs = {}
        if self._section:
            kwargs['section'] = self.replacer._new.section
        else:
            kwargs['section'] = self.replacer.current_link.section
        if self._label:
            if self.replacer._new.anchor is None:
                kwargs['label'] = self.replacer._new.canonical_title()
                if self.replacer._new.section:
                    kwargs['label'] += '#' + self.replacer._new.section
            else:
                kwargs['label'] = self.replacer._new.anchor
        else:
            if self.replacer.current_link.anchor is None:
                kwargs['label'] = self.replacer.current_groups['title']
                if self.replacer.current_groups['section']:
                    kwargs['label'] += '#' + \
                                       self.replacer.current_groups['section']
            else:
                kwargs['label'] = self.replacer.current_link.anchor
        return pywikibot.Link.create_separated(
            self.replacer._new.canonical_title(), self.replacer._new.site,
            **kwargs)


class AlwaysChoice(Choice):

    """Add an option to always apply the default."""

    def __init__(self, replacer, option='always', shortcut='a'):
        """Constructor."""
        super(AlwaysChoice, self).__init__(option, shortcut, replacer)
        self.always = False

    def handle(self):
        """Handle the custom shortcut."""
        self.always = True
        return self.answer

    def handle_link(self):
        """Directly return answer whether it's applying it always."""
        return self.always

    @property
    def answer(self):
        """Get the actual default answer instructing the replacement."""
        return self.replacer.handle_answer(self.replacer._default)


class InteractiveReplace(object):

    """
    A callback class for textlib's replace_links.

    It shows various options which can be switched on and off:
    * allow_skip_link = True (skip the current link)
    * allow_unlink = True (unlink)
    * allow_replace = False (just replace target, keep section and label)
    * allow_replace_section = False (replace target and section, keep label)
    * allow_replace_label = False (replace target and label, keep section)
    * allow_replace_all = False (replace target, section and label)
    (The boolean values are the default values)

    It has also a C{context} attribute which must be a non-negative integer. If
    it is greater 0 it shows that many characters before and after the link in
    question. The C{context_delta} attribute can be defined too and adds an
    option to increase C{context} by the given amount each time the option is
    selected.

    Additional choices can be defined using the 'additional_choices' and will
    be amended to the choices defined by this class. This list is mutable and
    the Choice instance returned and created by this class are too.
    """

    def __init__(self, old_link, new_link, default=None, automatic_quit=True):
        """
        Constructor.

        @param old_link: The old link which is searched. The label and section
            are ignored.
        @type old_link: Link or Page
        @param new_link: The new link with which it should be replaced.
            Depending on the replacement mode it'll use this link's label and
            section. If False it'll unlink all and the attributes beginning
            with allow_replace are ignored.
        @type new_link: Link or Page or False
        @param default: The default answer as the shortcut
        @type default: None or str
        @param automatic_quit: Add an option to quit and raise a
            QuitKeyboardException.
        @type automatic_quit: bool
        """
        if isinstance(old_link, pywikibot.Page):
            self._old = old_link._link
        else:
            self._old = old_link
        if isinstance(new_link, pywikibot.Page):
            self._new = new_link._link
        else:
            self._new = new_link
        self._default = default
        self._quit = automatic_quit
        self._current_match = None
        self.context = 30
        self.context_delta = 0
        self.allow_skip_link = True
        self.allow_unlink = True
        self.allow_replace = False
        self.allow_replace_section = False
        self.allow_replace_label = False
        self.allow_replace_all = False
        # Use list to preserve order
        self._own_choices = [
            ('skip_link', StaticChoice('Do not change', 'n', None)),
            ('unlink', StaticChoice('Unlink', 'u', False)),
        ]
        if self._new:
            self._own_choices += [
                ('replace', LinkChoice('Change link target', 't', self,
                                       False, False)),
                ('replace_section', LinkChoice(
                    'Change link target and section', 's', self, True, False)),
                ('replace_label', LinkChoice('Change link target and label',
                                             'l', self, False, True)),
                ('replace_all', LinkChoice('Change complete link', 'c', self,
                                           True, True)),
            ]

        self.additional_choices = []

    def handle_answer(self, choice):
        """Return the result for replace_links."""
        for c in self.choices:
            if c.shortcut == choice:
                return c.handle()
        else:
            raise ValueError('Invalid choice "{0}"'.format(choice))

    def __call__(self, link, text, groups, rng):
        """Ask user how the selected link should be replaced."""
        if self._old == link:
            self._current_match = (link, text, groups, rng)
            while True:
                try:
                    answer = self.handle_link()
                except UnhandledAnswer as e:
                    if e.stop:
                        raise
                else:
                    break
            self._current_match = None  # don't reset in case of an exception
            return answer
        else:
            return None

    @property
    def choices(self):
        """Return the tuple of choices."""
        choices = []
        for name, choice in self._own_choices:
            if getattr(self, 'allow_' + name):
                choices += [choice]
        if self.context_delta > 0:
            choices += [HighlightContextOption(
                'more context', 'm', self.current_text, self.context,
                self.context_delta, *self.current_range)]
        choices += self.additional_choices
        return tuple(choices)

    def handle_link(self):
        """Handle the currently given replacement."""
        choices = self.choices
        for choice in choices:
            if isinstance(choice, Choice) and choice.handle_link():
                return choice.answer

        if self.context > 0:
            rng = self.current_range
            text = self.current_text
            # at the beginning of the link, start red color.
            # at the end of the link, reset the color to default
            pywikibot.output(text[max(0, rng[0] - self.context): rng[0]] +
                             color_format('{lightred}{0}{default}',
                                          text[rng[0]: rng[1]]) +
                             text[rng[1]: rng[1] + self.context])
            question = 'Should the link '
        else:
            question = 'Should the link {lightred}{0}{default} '

        if self._new is False:
            question += 'be unlinked?'
        else:
            question += color_format('target to {lightpurple}{0}{default}?',
                                     self._new.canonical_title())

        choice = pywikibot.input_choice(
            color_format(question, self._old.canonical_title()),
            choices, default=self._default, automatic_quit=self._quit)

        return self.handle_answer(choice)

    @property
    def current_link(self):
        """Get the current link when it's handling one currently."""
        if self._current_match is None:
            raise ValueError('No current link')
        return self._current_match[0]

    @property
    def current_text(self):
        """Get the current text when it's handling one currently."""
        if self._current_match is None:
            raise ValueError('No current text')
        return self._current_match[1]

    @property
    def current_groups(self):
        """Get the current groups when it's handling one currently."""
        if self._current_match is None:
            raise ValueError('No current groups')
        return self._current_match[2]

    @property
    def current_range(self):
        """Get the current range when it's handling one currently."""
        if self._current_match is None:
            raise ValueError('No current range')
        return self._current_match[3]


# Command line parsing and help
def calledModuleName():
    """Return the name of the module calling this function.

    This is required because the -help option loads the module's docstring
    and because the module name will be used for the filename of the log.

    @rtype: unicode
    """
    # get commandline arguments
    called = pywikibot.argvu[0].strip()
    if ".py" in called:  # could end with .pyc, .pyw, etc. on some platforms
        # clip off the '.py?' filename extension
        called = called[:called.rindex('.py')]
    return os.path.basename(called)


def handle_args(args=None, do_help=True):
    """
    Handle standard command line arguments, and return the rest as a list.

    Takes the command line arguments as Unicode strings, processes all
    global parameters such as -lang or -log, initialises the logging layer,
    which emits startup information into log at level 'verbose'.

    This makes sure that global arguments are applied first,
    regardless of the order in which the arguments were given.

    args may be passed as an argument, thereby overriding sys.argv

    @param args: Command line arguments
    @type args: list of unicode
    @param do_help: Handle parameter '-help' to show help and invoke sys.exit
    @type do_help: bool
    @return: list of arguments not recognised globally
    @rtype: list of unicode
    """
    if pywikibot._sites:
        warn('Site objects have been created before arguments were handled',
             UserWarning)

    # get commandline arguments if necessary
    if not args:
        # it's the version in pywikibot.__init__ that is changed by scripts,
        # not the one in pywikibot.bot.
        args = pywikibot.argvu[1:]
    # get the name of the module calling this function. This is
    # required because the -help option loads the module's docstring and
    # because the module name will be used for the filename of the log.
    moduleName = calledModuleName()
    if not moduleName:
        moduleName = "terminal-interface"
    nonGlobalArgs = []
    username = None
    do_help = None if do_help else False
    for arg in args:
        option, sep, value = arg.partition(':')
        if do_help is not False and option == '-help':
            do_help = True
        elif option == '-dir':
            pass
        elif option == '-family':
            config.family = value
        elif option == '-lang':
            config.mylang = value
        elif option == '-user':
            username = value
        elif option in ('-putthrottle', '-pt'):
            config.put_throttle = int(value)
        elif option == '-log':
            if moduleName not in config.log:
                config.log.append(moduleName)
            if value:
                config.logfilename = value
        elif option == '-nolog':
            config.log = []
        elif option in ('-cosmeticchanges', '-cc'):
            config.cosmetic_changes = not config.cosmetic_changes
            output(u'NOTE: option cosmetic_changes is %s\n'
                   % config.cosmetic_changes)
        elif option == '-simulate':
            config.simulate = True
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
            if moduleName not in config.log:
                config.log.append(moduleName)
            if value:
                if value not in config.debug_log:
                    config.debug_log.append(value)
            elif '' not in config.debug_log:
                config.debug_log.append("")
        elif option in ('-verbose', '-v'):
            config.verbose_output += 1
        elif option == '-daemonize':
            redirect_std = value if value else None
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
                nonGlobalArgs.append(arg)

    if username:
        config.usernames[config.family][config.mylang] = username

    init_handlers()
    writeToCommandLogFile()

    if config.verbose_output:
        pywikibot.output(u'Python %s' % sys.version)

    if do_help:
        showHelp()
        sys.exit(0)

    debug('handle_args() completed.', _logger)
    return nonGlobalArgs


@deprecated("handle_args")
def handleArgs(*args):
    """DEPRECATED. Use handle_args()."""
    return handle_args(args)


def showHelp(module_name=None):
    """Show help for the Bot."""
    if not module_name:
        module_name = calledModuleName()
    if not module_name:
        try:
            module_name = sys.modules['__main__'].main.__module__
        except NameError:
            module_name = "no_module"

    globalHelp = u'''
GLOBAL OPTIONS
==============
(Global arguments available for all bots)

-dir:PATH         Read the bot's configuration data from directory given by
                  PATH, instead of from the default directory.

-lang:xx          Set the language of the wiki you want to work on, overriding
                  the configuration in user-config.py. xx should be the
                  language code.

-family:xyz       Set the family of the wiki you want to work on, e.g.
                  wikipedia, wiktionary, wikitravel, ...
                  This will override the configuration in user-config.py.

-user:xyz         Log in as user 'xyz' instead of the default username.

-daemonize:xyz    Immediately return control to the terminal and redirect
                  stdout and stderr to file xyz.
                  (only use for bots that require no input from stdin).

-help             Show this help text.

-log              Enable the log file, using the default filename
                  '%s-bot.log'
                  Logs will be stored in the logs subdirectory.

-log:xyz          Enable the log file, using 'xyz' as the filename.

-nolog            Disable the log file (if it is enabled by default).

-maxlag           Sets a new maxlag parameter to a number of seconds. Defer bot
                  edits during periods of database server lag. Default is set
                  by config.py

-putthrottle:n    Set the minimum time (in seconds) the bot will wait between
-pt:n             saving pages.
-put_throttle:n

-debug:item       Enable the log file and include extensive debugging data
-debug            for component "item" (for all components if the second form
                  is used).

-verbose          Have the bot provide additional console output that may be
-v                useful in debugging.

-cosmeticchanges  Toggles the cosmetic_changes setting made in config.py or
-cc               user-config.py to its inverse and overrules it. All other
                  settings and restrictions are untouched.

-simulate         Disables writing to the server. Useful for testing and
                  debugging of new code (if given, doesn't do any real
                  changes, but only shows what would have been changed).

-<config var>:n   You may use all given numeric config variables as option and
                  modify it with command line.

''' % module_name
    try:
        module = __import__('%s' % module_name)
        helpText = module.__doc__
        if PY2 and isinstance(helpText, bytes):
            helpText = helpText.decode('utf-8')
        if hasattr(module, 'docuReplacements'):
            for key, value in module.docuReplacements.items():
                helpText = helpText.replace(key, value.strip('\n\r'))
        pywikibot.stdout(helpText)  # output to STDOUT
    except Exception:
        if module_name:
            pywikibot.stdout(u'Sorry, no help available for %s' % module_name)
        pywikibot.log('showHelp:', exc_info=True)
    pywikibot.stdout(globalHelp)


def suggest_help(missing_parameters=[], missing_generator=False,
                 unknown_parameters=[], exception=None,
                 missing_action=False, additional_text=''):
    """
    Output error message to use -help with additional text before it.

    @param missing_parameters: A list of parameters which are missing.
    @type missing_parameters: list of str
    @param missing_generator: Whether a generator is missing.
    @type missing_generator: bool
    @param unknown_parameters: A list of parameters which are unknown.
    @type unknown_parameters: list of str
    @param exception: An exception thrown.
    @type exception: Exception
    @param missing_action: Add an entry that no action was defined.
    @type missing_action: bool
    @param additional_text: Additional text added to the end.
    @type additional_text: str
    """
    if exception:
        additional_text = ('An error occured: "{0}"'.format(exception) +
                           additional_text)
    if missing_generator:
        additional_text = ('Unable to execute script because no generator was '
                           'defined.\n' + additional_text)
    if missing_parameters:
        additional_text = 'Missing parameter(s) "{0}"\n'.format(
            '", "'.join(missing_parameters)) + additional_text
    if missing_action:
        additional_text = 'No action defined.\n' + additional_text
    if unknown_parameters:
        additional_text = 'Unknown parameter(s) "{0}"\n'.format(
            '", "'.join(unknown_parameters)) + additional_text
    if not additional_text.endswith('\n'):
        additional_text += '\n'
    error(additional_text + 'Use -help for further information.')


def writeToCommandLogFile():
    """
    Save name of the called module along with all params to logs/commands.log.

    This can be used by user later to track errors or report bugs.
    """
    modname = calledModuleName()
    # put quotation marks around all parameters
    args = [modname] + [u'"%s"' % s for s in pywikibot.argvu[1:]]
    command_log_filename = config.datafilepath('logs', 'commands.log')
    try:
        command_log_file = codecs.open(command_log_filename, 'a', 'utf-8')
    except IOError:
        command_log_file = codecs.open(command_log_filename, 'w', 'utf-8')
    # add a timestamp in ISO 8601 formulation
    isoDate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    command_log_file.write('%s r%s Python %s '
                           % (isoDate, version.getversiondict()['rev'],
                              sys.version.split()[0]))
    s = u' '.join(args)
    command_log_file.write(s + os.linesep)
    command_log_file.close()


def open_webbrowser(page):
    """Open the web browser displaying the page and wait for input."""
    webbrowser.open(page.full_url())
    i18n.input('pywikibot-enter-finished-browser')


class OptionHandler(object):

    """Class to get and set options."""

    # Handler configuration.
    # Only the keys of the dict can be passed as init options
    # The values are the default values
    # Overwrite this in subclasses!

    availableOptions = {}

    def __init__(self, **kwargs):
        """
        Only accept options defined in availableOptions.

        @param kwargs: bot options
        @type kwargs: dict
        """
        self.setOptions(**kwargs)

    def setOptions(self, **kwargs):
        """
        Set the instance options.

        @param kwargs: options
        @type kwargs: dict
        """
        # contains the options overridden from defaults
        self.options = {}

        validOptions = set(self.availableOptions)
        receivedOptions = set(kwargs)

        for opt in receivedOptions & validOptions:
            self.options[opt] = kwargs[opt]

        for opt in receivedOptions - validOptions:
            pywikibot.warning(u'%s is not a valid option. It was ignored.'
                              % opt)

    def getOption(self, option):
        """
        Get the current value of an option.

        @param option: key defined in OptionHandler.availableOptions
        @raise Error: No valid option is given with option parameter
        """
        try:
            return self.options.get(option, self.availableOptions[option])
        except KeyError:
            raise pywikibot.Error("'{0}' is not a valid option for {1}."
                                  .format(option, self.__class__.__name__))


class BaseBot(OptionHandler):

    """
    Generic Bot to be subclassed.

    This class provides a run() method for basic processing of a
    generator one page at a time.

    If the subclass places a page generator in self.generator,
    Bot will process each page in the generator, invoking the method treat()
    which must then be implemented by subclasses.

    If the subclass does not set a generator, or does not override
    treat() or run(), NotImplementedError is raised.
    """

    # Handler configuration.
    # The values are the default values
    # Extend this in subclasses!

    availableOptions = {
        'always': False,  # By default ask for confirmation when putting a page
    }

    _current_page = None

    def __init__(self, **kwargs):
        """
        Only accept options defined in availableOptions.

        @param kwargs: bot options
        @type kwargs: dict
        """
        if 'generator' in kwargs:
            self.generator = kwargs.pop('generator')

        super(BaseBot, self).__init__(**kwargs)

        self._treat_counter = 0
        self._save_counter = 0

    @property
    def current_page(self):
        """Return the current working page as a property."""
        return self._current_page

    @current_page.setter
    def current_page(self, page):
        """Set the current working page as a property.

        When the value is actually changed, the page title is printed
        to the standard output (highlighted in purple) and logged
        with a VERBOSE level.

        This also prevents the same title from being printed twice.

        @param page: the working page
        @type page: pywikibot.Page
        """
        if page != self._current_page:
            self._current_page = page
            msg = u'Working on %r' % page.title()
            if config.colorized_output:
                log(msg)
                stdout(color_format('\n\n>>> {lightpurple}{0}{default} <<<',
                                    page.title()))
            else:
                stdout(msg)

    def user_confirm(self, question):
        """Obtain user response if bot option 'always' not enabled."""
        if self.getOption('always'):
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
            self.options['always'] = True

        return True

    @deprecate_arg('async', 'asynchronous')  # T106230
    @deprecated_args(comment='summary')
    def userPut(self, page, oldtext, newtext, **kwargs):
        """
        Save a new revision of a page, with user confirmation as required.

        Print differences, ask user for confirmation,
        and puts the page if needed.

        Option used:

        * 'always'

        Keyword args used:

        * 'asynchronous' - passed to page.save
        * 'summary' - passed to page.save
        * 'show_diff' - show changes between oldtext and newtext (enabled)
        * 'ignore_save_related_errors' - report and ignore (disabled)
        * 'ignore_server_errors' - report and ignore (disabled)

        @return: whether the page was saved successfully
        @rtype: bool
        """
        if oldtext.rstrip() == newtext.rstrip():
            pywikibot.output(u'No changes were needed on %s'
                             % page.title(asLink=True))
            return

        self.current_page = page

        show_diff = kwargs.pop('show_diff', True)

        if show_diff:
            pywikibot.showDiff(oldtext, newtext)

        if 'summary' in kwargs:
            pywikibot.output(u'Edit summary: %s' % kwargs['summary'])

        page.text = newtext
        return self._save_page(page, page.save, **kwargs)

    def _save_page(self, page, func, *args, **kwargs):
        """
        Helper function to handle page save-related option error handling.

        @param page: currently edited page
        @param func: the function to call
        @param args: passed to the function
        @param kwargs: passed to the function
        @kwarg ignore_server_errors: if True, server errors will be reported
          and ignored (default: False)
        @kwtype ignore_server_errors: bool
        @kwarg ignore_save_related_errors: if True, errors related to
        page save will be reported and ignored (default: False)
        @kwtype ignore_save_related_errors: bool
        @return: whether the page was saved successfully
        @rtype: bool
        """
        if not self.user_confirm('Do you want to accept these changes?'):
            return False

        if 'asynchronous' not in kwargs and self.getOption('always'):
            kwargs['asynchronous'] = True

        ignore_save_related_errors = kwargs.pop('ignore_save_related_errors',
                                                False)
        ignore_server_errors = kwargs.pop('ignore_server_errors', False)

        try:
            func(*args, **kwargs)
            self._save_counter += 1
        except pywikibot.PageSaveRelatedError as e:
            if not ignore_save_related_errors:
                raise
            if isinstance(e, pywikibot.EditConflict):
                pywikibot.output(u'Skipping %s because of edit conflict'
                                 % page.title())
            elif isinstance(e, pywikibot.SpamfilterError):
                pywikibot.output(
                    u'Cannot change %s because of blacklist entry %s'
                    % (page.title(), e.url))
            elif isinstance(e, pywikibot.LockedPage):
                pywikibot.output(u'Skipping %s (locked page)'
                                 % page.title())
            else:
                pywikibot.error(
                    u'Skipping %s because of a save related error: %s'
                    % (page.title(), e))
        except pywikibot.ServerError as e:
            if not ignore_server_errors:
                raise
            pywikibot.error(u'Server Error while processing %s: %s'
                            % (page.title(), e))
        else:
            return True
        return False

    def quit(self):
        """Cleanup and quit processing."""
        raise QuitKeyboardInterrupt

    def exit(self):
        """
        Cleanup and exit processing.

        Invoked when Bot.run() is finished.
        Prints treat and save counters and informs whether the script
        terminated gracefully or was halted by exception.
        May be overridden by subclasses.
        """
        pywikibot.output("\n%i pages read"
                         "\n%i pages written"
                         % (self._treat_counter, self._save_counter))
        if hasattr(self, '_start_ts'):
            delta = (pywikibot.Timestamp.now() - self._start_ts)
            seconds = int(delta.total_seconds())
            if delta.days:
                pywikibot.output("Execution time: %d days, %d seconds"
                                 % (delta.days, delta.seconds))
            else:
                pywikibot.output("Execution time: %d seconds" % delta.seconds)
            if self._treat_counter:
                pywikibot.output("Read operation time: %d seconds"
                                 % (seconds / self._treat_counter))
            if self._save_counter:
                pywikibot.output("Write operation time: %d seconds"
                                 % (seconds / self._save_counter))

        # exc_info contains exception from self.run() while terminating
        exc_info = sys.exc_info()
        if exc_info[0] is None or exc_info[0] is KeyboardInterrupt:
            pywikibot.output("Script terminated successfully.")
        else:
            pywikibot.output("Script terminated by exception:\n")
            pywikibot.exception()

    def treat(self, page):
        """Process one page (Abstract method)."""
        raise NotImplementedError('Method %s.treat() not implemented.'
                                  % self.__class__.__name__)

    def init_page(self, page):
        """Return whether treat should be executed for the page."""
        pass

    def run(self):
        """Process all pages in generator."""
        self._start_ts = pywikibot.Timestamp.now()
        if not hasattr(self, 'generator'):
            raise NotImplementedError('Variable %s.generator not set.'
                                      % self.__class__.__name__)

        maxint = 0
        if PY2:
            maxint = sys.maxint

            # Python 2 does not clear previous exceptions and method `exit`
            # relies on sys.exc_info returning exceptions occurring in `run`.
            sys.exc_clear()

        try:
            for page in self.generator:
                try:
                    self.init_page(page)
                except SkipPageError as e:
                    pywikibot.warning('Skipped "{0}" due to: {1}'.format(
                                      page, e.reason))
                    if PY2:
                        # Python 2 does not clear the exception and it may seem
                        # that the generator stopped due to an exception
                        sys.exc_clear()
                    continue

                # Process the page
                self.treat(page)

                self._treat_counter += 1
                if maxint and self._treat_counter == maxint:
                    # Warn the user that the bot may not function correctly
                    pywikibot.error(
                        '\n%s: page count reached Python 2 sys.maxint (%d).\n'
                        'Python 3 should be used to process very large batches'
                        % (self.__class__.__name__, sys.maxint))
        except QuitKeyboardInterrupt:
            pywikibot.output('\nUser quit %s bot run...' %
                             self.__class__.__name__)
        except KeyboardInterrupt:
            if config.verbose_output:
                raise
            else:
                pywikibot.output('\nKeyboardInterrupt during %s bot run...' %
                                 self.__class__.__name__)
        finally:
            self.exit()


# TODO: Deprecate Bot class as self.site may be the site of the page or may be
# a site previously defined
class Bot(BaseBot):

    """
    Generic bot subclass for multiple sites.

    If possible the MultipleSitesBot or SingleSiteBot classes should be used
    instead which specifically handle multiple or single sites.
    """

    def __init__(self, **kwargs):
        """Create a Bot instance and initalize cached sites."""
        # TODO: add warning if site is specified and generator
        # contains pages from a different site.
        self._site = kwargs.pop('site', None)
        self._sites = set([self._site] if self._site else [])

        super(Bot, self).__init__(**kwargs)

    @property
    def site(self):
        """Get the current site."""
        if not self._site:
            warning('Bot.site was not set before being retrieved.')
            self.site = pywikibot.Site()
            warning('Using the default site: %s' % self.site)
        return self._site

    @site.setter
    def site(self, site):
        """
        Set the Site that the bot is using.

        When Bot.run() is managing the generator and site property, this is
        set each time a page is on a site different from the previous page.
        """
        if not site:
            self._site = None
            return

        if site not in self._sites:
            log(u'LOADING SITE %s VERSION: %s'
                % (site, site.version()))

            self._sites.add(site)
            if len(self._sites) == 2:
                log('%s uses multiple sites' % self.__class__.__name__)
        if self._site and self._site != site:
            log('%s: changing site from %s to %s'
                % (self.__class__.__name__, self._site, site))
        self._site = site

    def run(self):
        """Check if it automatically updates the site before run."""
        # This check is to remove the possibility that the superclass changing
        # self.site causes bugs in subclasses.
        # If the subclass has set self.site before run(), it may be that the
        # bot processes pages on sites other than self.site, and therefore
        # this method cant alter self.site. To use this functionality, don't
        # set self.site in __init__, and use page.site in treat().
        self._auto_update_site = not self._site
        if not self._auto_update_site:
            warning(
                '%s.__init__ set the Bot.site property; this is only needed '
                'when the Bot accesses many sites.' % self.__class__.__name__)
        else:
            log('Bot is managing the %s.site property in run()'
                % self.__class__.__name__)
        super(Bot, self).run()

    def init_page(self, page):
        """Update site before calling treat."""
        # When in auto update mode, set the site when it changes,
        # so subclasses can hook onto changes to site.
        if (self._auto_update_site and
                (not self._site or page.site != self.site)):
            self.site = page.site


class SingleSiteBot(BaseBot):

    """
    A bot only working on one site and ignoring the others.

    If no site is given from the start it'll use the first page's site. Any
    page after the site has been defined and is not on the defined site will be
    ignored.
    """

    def __init__(self, site=True, **kwargs):
        """
        Create a SingleSiteBot instance.

        @param site: If True it'll be set to the configured site using
            pywikibot.Site.
        @type site: True or None or Site
        """
        if site is True:
            site = pywikibot.Site()
        self._site = site
        super(SingleSiteBot, self).__init__(**kwargs)

    @property
    def site(self):
        """Site that the bot is using."""
        if not self._site:
            raise ValueError('The site has not been defined yet.')
        return self._site

    @site.setter
    def site(self, value):
        """Set the current site but warns if different."""
        if self._site:
            # Warn in any case where the site is (probably) changed after
            # setting it the first time. The appropriate variant is not to use
            # self.site at all or define it once and never change it again
            if self._site == value:
                pywikibot.warning('Defined site without changing it.')
            else:
                pywikibot.warning('Changed the site from "{0}" to '
                                  '"{1}"'.format(self._site, value))
        self._site = value

    def init_page(self, page):
        """Set site if not defined and return if it's on the defined site."""
        if not self._site:
            self.site = page.site
        elif page.site != self.site:
            raise SkipPageError(page,
                                'The bot is on site "{0}" but the page on '
                                'site "{1}"'.format(self.site, page.site))


class MultipleSitesBot(BaseBot):

    """
    A bot class working on multiple sites.

    The bot should accommodate for that case and not store site specific
    information on only one site.
    """

    def __init__(self, **kwargs):
        """Constructor."""
        self._site = None
        super(MultipleSitesBot, self).__init__(**kwargs)

    @property
    @deprecated("the page's site property")
    def site(self):
        """
        Return the site if it's set and ValueError otherwise.

        The site is only defined while in treat and it is preferred to use
        the page's site instead.
        """
        if self._site is None:
            raise ValueError('Requesting the site not while in treat is not '
                             'allowed.')
        return self._site

    def run(self):
        """Reset the bot's site after run."""
        super(MultipleSitesBot, self).run()
        self._site = None

    def init_page(self, page):
        """Define the site for this page."""
        self._site = page.site


class CurrentPageBot(BaseBot):

    """
    A bot which automatically sets 'current_page' on each treat().

    This class should be always used together with either the MultipleSitesBot
    or SingleSiteBot class as there is no site management in this class.
    """

    ignore_save_related_errors = True
    ignore_server_errors = False

    def treat_page(self):
        """Process one page (Abstract method)."""
        raise NotImplementedError('Method %s.treat_page() not implemented.'
                                  % self.__class__.__name__)

    def treat(self, page):
        """Set page to current page and treat that page."""
        self.current_page = page
        self.treat_page()

    @deprecated_args(comment='summary')
    def put_current(self, new_text, ignore_save_related_errors=None,
                    ignore_server_errors=None, **kwargs):
        """
        Call L{Bot.userPut} but use the current page.

        It compares the new_text to the current page text.

        @param new_text: The new text
        @type new_text: basestring
        @param ignore_save_related_errors: Ignore save related errors and
            automatically print a message. If None uses this instances default.
        @type ignore_save_related_errors: bool or None
        @param ignore_server_errors: Ignore server errors and automatically
            print a message. If None uses this instances default.
        @type ignore_server_errors: bool or None
        @param kwargs: Additional parameters directly given to L{Bot.userPut}.
        @type kwargs: dict
        @return: whether the page was saved successfully
        @rtype: bool
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

    """
    A class which automatically defines C{summary} for C{put_current}.

    The class must defined a C{summary_key} string which contains the i18n key
    for L{pywikibot.i18n.twtranslate}. It can also override the
    C{summary_parameters} property to specify any parameters for the translated
    message.
    """

    summary_key = None  # must be defined in subclasses

    @property
    def summary_parameters(self):
        """A dictionary of all parameters for i18n."""
        return {}

    def put_current(self, *args, **kwargs):
        """Defining a summary if not already defined and then call original."""
        if not kwargs.get('summary'):
            if self.summary_key is None:
                raise ValueError('The summary_key must be set.')
            summary = i18n.twtranslate(self.current_page.site,
                                       self.summary_key,
                                       self.summary_parameters)
            pywikibot.log(
                'Use automatic summary message "{0}"'.format(summary))
            kwargs['summary'] = summary
        super(AutomaticTWSummaryBot, self).put_current(*args, **kwargs)


class ExistingPageBot(CurrentPageBot):

    """A CurrentPageBot class which only treats existing pages."""

    def treat(self, page):
        """Treat page if it exists and handle NoPage from it."""
        if not page.exists():
            pywikibot.warning('Page "{0}" does not exist on {1}.'.format(
                page.title(), page.site))
            return
        try:
            super(ExistingPageBot, self).treat(page)
        except pywikibot.NoPage as e:
            if e.page != page:
                raise
            pywikibot.warning(
                'During handling of page "{0}" on {1} a NoPage exception was '
                'raised.'.format(page.title(), page.site))


class FollowRedirectPageBot(CurrentPageBot):

    """A CurrentPageBot class which follows the redirect."""

    def treat(self, page):
        """Treat target if page is redirect and the page otherwise."""
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        super(FollowRedirectPageBot, self).treat(page)


class CreatingPageBot(CurrentPageBot):

    """A CurrentPageBot class which only treats nonexistent pages."""

    def treat(self, page):
        """Treat page if doesn't exist."""
        if page.exists():
            pywikibot.warning('Page "{0}" does already exist on {1}.'.format(
                page.title(), page.site))
            return
        super(CreatingPageBot, self).treat(page)


class RedirectPageBot(CurrentPageBot):

    """A RedirectPageBot class which only treats redirects."""

    def treat(self, page):
        """Treat only redirect pages and handle IsNotRedirectPage from it."""
        if not page.isRedirectPage():
            pywikibot.warning('Page "{0}" on {1} is skipped because it is not '
                              'a redirect'.format(page.title(), page.site))
            return
        try:
            super(RedirectPageBot, self).treat(page)
        except pywikibot.IsNotRedirectPage as e:
            if e.page != page:
                raise
            pywikibot.warning(
                'During handling of page "{0}" on {1} a IsNotRedirectPage '
                'exception was raised.'.format(page.title(), page.site))


class NoRedirectPageBot(CurrentPageBot):

    """A NoRedirectPageBot class which only treats non-redirects."""

    def treat(self, page):
        """Treat only non-redirect pages and handle IsRedirectPage from it."""
        if page.isRedirectPage():
            pywikibot.warning('Page "{0}" on {1} is skipped because it is a '
                              'redirect'.format(page.title(), page.site))
            return
        try:
            super(NoRedirectPageBot, self).treat(page)
        except pywikibot.IsRedirectPage as e:
            if e.page != page:
                raise
            pywikibot.warning(
                'During handling of page "{0}" on {1} a IsRedirectPage '
                'exception was raised.'.format(page.title(), page.site))


class WikidataBot(Bot, ExistingPageBot):

    """
    Generic Wikidata Bot to be subclassed.

    Source claims (P143) can be created for specific sites

    @cvar use_from_page: If True (default) it will apply ItemPage.fromPage
        for every item. If False it assumes that the pages are actually
        already ItemPage (page in treat_page_and_item will be None).
        If None it'll use ItemPage.fromPage when the page is not in the site's
        item namespace.

    @type use_from_page: bool, None

    @cvar treat_missing_item: Whether pages without items should be treated.
        Note that this is checked after create_missing_item.

    @type treat_missing_item: bool

    @ivar create_missing_item: If True, new items will be created if the current
        page doesn't have one. Subclasses should override this in the
        constructor with a bool value or using self.getOption.

    @type create_missing_item: bool
    """

    use_from_page = True
    treat_missing_item = False

    @deprecated_args(use_from_page=None)
    def __init__(self, **kwargs):
        """Constructor of the WikidataBot."""
        self.create_missing_item = False
        super(WikidataBot, self).__init__(**kwargs)
        self.site = pywikibot.Site()
        self.repo = self.site.data_repository()
        if self.repo is None:
            raise pywikibot.exceptions.WikiBaseError(
                '%s is not connected to a data repository' % self.site)

    def cacheSources(self):
        """
        Fetch the sources from the list on Wikidata.

        It is stored internally and reused by getSource()
        """
        page = pywikibot.Page(self.repo, u'List of wikis/python', ns=4)
        self.source_values = json.loads(page.get())
        for family_code, family in self.source_values.items():
            for source_lang in family:
                self.source_values[
                    family_code][source_lang] = pywikibot.ItemPage(
                        self.repo, family[source_lang])

    def get_property_by_name(self, property_name):
        """
        Find given property and return its ID.

        Method first uses site.search() and if the property isn't found, then
        asks user to provide the property ID.

        @param property_name: property to find
        @type property_name: str
        """
        ns = self.site.data_repository().property_namespace
        for page in self.site.search(property_name, total=1, namespaces=ns):
            page = pywikibot.PropertyPage(self.site.data_repository(),
                                          page.title())
            pywikibot.output(u"Assuming that %s property is %s." %
                             (property_name, page.id))
            return page.id
        return pywikibot.input(u'Property %s was not found. Please enter the '
                               u'property ID (e.g. P123) of it:'
                               % property_name).upper()

    def user_edit_entity(self, item, data=None, **kwargs):
        """
        Edit entity with data provided, with user confirmation as required.

        @param item: page to be edited
        @type item: ItemPage
        @param data: data to be saved, or None if the diff should be created
          automatically
        @kwarg summary: revision comment, passed to ItemPage.editEntity
        @type summary: str
        @kwarg show_diff: show changes between oldtext and newtext (default:
          True)
        @type show_diff: bool
        @kwarg ignore_server_errors: if True, server errors will be reported
          and ignored (default: False)
        @type ignore_server_errors: bool
        @kwarg ignore_save_related_errors: if True, errors related to
          page save will be reported and ignored (default: False)
        @type ignore_save_related_errors: bool
        @return: whether the item was saved successfully
        @rtype: bool
        """
        show_diff = kwargs.pop('show_diff', True)
        if show_diff:
            if data is None:
                diff = item.toJSON(diffto=(
                    item._content if hasattr(item, '_content') else None))
            else:
                diff = pywikibot.page.WikibasePage._normalizeData(data)
            pywikibot.output(json.dumps(diff, indent=4, sort_keys=True))

        if 'summary' in kwargs:
            pywikibot.output(u'Change summary: %s' % kwargs['summary'])

        # TODO PageSaveRelatedErrors should be actually raised in editEntity
        # (bug T86083)
        return self._save_page(item, item.editEntity, data, **kwargs)

    def _add_source_callback(self, claim, source, **kwargs):
        """
        Make a callback for user_add_claim.

        @return: callback to be executed after saving the claim
        @rtype: callable or None
        """
        callback = None
        sourceclaim = self.getSource(source)
        if sourceclaim:
            def callback(item, err):
                if err is None and claim.on_item is not None:
                    claim.addSource(sourceclaim, **kwargs)

        return callback

    def user_add_claim(self, item, claim, source=None, bot=True, **kwargs):
        """
        Add a claim to an item, with user confirmation as required.

        @param item: page to be edited
        @type item: pywikibot.ItemPage
        @param claim: claim to be saved
        @type claim: pywikibot.Claim
        @param source: site where the claim comes from
        @type source: pywikibot.site.APISite
        @param bot: whether to flag as bot (if possible)
        @type bot: bool
        @kwarg ignore_server_errors: if True, server errors will be reported
          and ignored (default: False)
        @type ignore_server_errors: bool
        @kwarg ignore_save_related_errors: if True, errors related to
          page save will be reported and ignored (default: False)
        @type ignore_save_related_errors: bool
        @return: whether the item was saved successfully
        @rtype: bool
        """
        self.current_page = item

        callback = None
        if source:
            callback = self._add_source_callback(claim, source, bot=bot)

        pywikibot.output('Adding %s --> %s' % (claim.getID(),
                                               claim.getTarget()))
        return self._save_page(item, item.addClaim, claim, bot=bot,
                               callback=callback, **kwargs)

    def getSource(self, site):
        """
        Create a Claim usable as a source for Wikibase statements.

        @param site: site that is the source of assertions.
        @type site: Site

        @return: pywikibot.Claim or None
        """
        source = None
        item = i18n.translate(site, self.source_values)
        if item:
            source = pywikibot.Claim(self.repo, 'P143')
            source.setTarget(item)
        return source

    def user_add_claim_unless_exists(
            self, item, claim, exists_arg='', source=None,
            logger_callback=log, **kwargs):
        """
        Decorator of L{user_add_claim}.

        Before adding a new claim, it checks if we can add it, using provided
        filters.

        @see: documentation of L{claimit.py<scripts.claimit>}
        @param exists_arg: pattern for merging existing claims with new ones
        @type exists_arg: str
        @param logger_callback: function logging the output of the method
        @type logger_callback: callable
        @return: whether the claim could be added
        @rtype: bool
        """
        # Existing claims on page of same property
        for existing in item.get().get('claims').get(claim.getID(), []):
            # If claim with same property already exists...
            if 'p' not in exists_arg:
                logger_callback(
                    'Skipping %s because claim with same property already exists'
                    % (claim.getID(),))
                log('Use -exists:p option to override this behavior')
                return False
            if not existing.target_equals(claim.getTarget()):
                continue
            # If some attribute of the claim being added
            # matches some attribute in an existing claim of
            # the same property, skip the claim, unless the
            # 'exists' argument overrides it.
            if 't' not in exists_arg:
                logger_callback(
                    'Skipping %s because claim with same target already exists'
                    % (claim.getID(),))
                log("Append 't' to -exists argument to override this behavior")
                return False
            if 'q' not in exists_arg and not existing.qualifiers:
                logger_callback(
                    'Skipping %s because claim without qualifiers already exists'
                    % (claim.getID(),))
                log("Append 'q' to -exists argument to override this behavior")
                return False
            if ('s' not in exists_arg or not source) and not existing.sources:
                logger_callback(
                    'Skipping %s because claim without source already exists'
                    % (claim.getID(),))
                log("Append 's' to -exists argument to override this behavior")
                return False
            if ('s' not in exists_arg and source and
                    any(source.getID() in ref and
                        all(snak.target_equals(source.getTarget())
                            for snak in ref[source.getID()])
                        for ref in existing.sources)):
                logger_callback(
                    'Skipping %s because claim with the same source already exists'
                    % (claim.getID(),))
                log("Append 's' to -exists argument to override this behavior")
                return False

        return self.user_add_claim(item, claim, source, **kwargs)

    def create_item_for_page(self, page, data=None, summary=None, **kwargs):
        """
        Create an ItemPage with the provided page as the sitelink.

        @param page: the page for which the item will be created
        @type page: pywikibot.Page
        @param data: additional data to be included in the new item (optional).
            Note that data created from the page have higher priority.
        @type data: dict
        @param summary: optional edit summary to replace the default one
        @type summary: str

        @return: pywikibot.ItemPage or None
        """
        if not summary:
            # FIXME: i18n
            summary = ('Bot: New item with sitelink from %s'
                       % page.title(asLink=True, insite=self.repo))

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
                'value': page.title()
            }
        })
        pywikibot.output('Creating item for %s...' % page)
        item = pywikibot.ItemPage(page.site.data_repository())
        kwargs.setdefault('show_diff', False)
        result = self.user_edit_entity(item, data, summary=summary, **kwargs)
        if result:
            return item
        else:
            return None

    def treat_page(self):
        """Treat a page."""
        page = self.current_page
        if self.use_from_page is True:
            try:
                item = pywikibot.ItemPage.fromPage(page)
            except pywikibot.NoPage:
                item = None
        else:
            if isinstance(page, pywikibot.ItemPage):
                item = page
                page = None
            else:
                # FIXME: Hack because 'is_data_repository' doesn't work if
                #        site is the APISite. See T85483
                data_site = page.site.data_repository()
                if (data_site.family == page.site.family and
                        data_site.code == page.site.code):
                    is_item = page.namespace() == data_site.item_namespace.id
                else:
                    is_item = False
                if is_item:
                    item = pywikibot.ItemPage(data_site, page.title())
                    page = None
                else:
                    try:
                        item = pywikibot.ItemPage.fromPage(page)
                    except pywikibot.NoPage:
                        item = None
                    if self.use_from_page is False:
                        pywikibot.error('{0} is not in the item namespace but '
                                        'must be an item.'.format(page))
                        return

        if not item and self.create_missing_item:
            item = self.create_item_for_page(page, asynchronous=False)

        if not item and not self.treat_missing_item:
            pywikibot.output('%s doesn\'t have a Wikidata item.' % page)
            return

        self.treat_page_and_item(page, item)

    def treat_page_and_item(self, page, item):
        """
        Treat page together with its item (if it exists).

        Must be implemented in subclasses.
        """
        raise NotImplementedError('Method %s.treat_page_and_item() not '
                                  'implemented.' % self.__class__.__name__)
