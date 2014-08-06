# -*- coding: utf-8  -*-
"""
User-interface related functions for building bots
"""
#
# (C) Pywikibot team, 2008-2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

# Note: the intention is to develop this module (at some point) into a Bot
# class definition that can be subclassed to create new, functional bot
# scripts, instead of writing each one from scratch.


import logging
import logging.handlers
# all output goes thru python std library "logging" module

import os
import sys
import re
import json
import datetime

_logger = "bot"

# logging levels
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
STDOUT = 16
VERBOSE = 18
INPUT = 25

import pywikibot
from pywikibot import config
from pywikibot import version

if sys.version_info[0] > 2:
    unicode = str

# User interface initialization
# search for user interface module in the 'userinterfaces' subdirectory
uiModule = __import__("pywikibot.userinterfaces.%s_interface"
                      % config.userinterface,
                      fromlist=['UI'])
ui = uiModule.UI()
pywikibot.argvu = ui.argvu()


# Logging module configuration
class RotatingFileHandler(logging.handlers.RotatingFileHandler):

    def doRollover(self):
        """
        Modified naming system for logging files.

        Overwrites the default Rollover renaming by inserting the count number
        between file name root and extension. If backupCount is >= 1, the system
        will successively create new files with the same pathname as the base
        file, but with inserting ".1", ".2" etc. in front of the filename
        suffix. For example, with a backupCount of 5 and a base file name of
        "app.log", you would get "app.log", "app.1.log", "app.2.log", ...
        through to "app.5.log". The file being written to is always "app.log" -
        when it gets filled up, it is closed and renamed to "app.1.log", and if
        files "app.1.log", "app.2.log" etc. already exist, then they are
        renamed to "app.2.log", "app.3.log" etc. respectively.
        If backupCount is >= 1 do not rotate but create new numbered filenames.
        The newest file has the highest number except some older numbered files
        where deleted and the bot was restarted. In this case the ordering
        starts from the lowest available (unused) number.

        """
        if self.stream:
            self.stream.close()
            self.stream = None
        root, ext = os.path.splitext(self.baseFilename)
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = "%s.%d%s" % (root, i, ext)
                dfn = "%s.%d%s" % (root, i + 1, ext)
                if os.path.exists(sfn):
                    #print "%s -> %s" % (sfn, dfn)
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = "%s.1%s" % (root, ext)
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
            #print "%s -> %s" % (self.baseFilename, dfn)
        elif self.backupCount == -1:
            if not hasattr(self, '_lastNo'):
                self._lastNo = 1
            while True:
                fn = "%s.%d%s" % (root, self._lastNo, ext)
                self._lastNo += 1
                if not os.path.exists(fn):
                    break
            os.rename(self.baseFilename, fn)
        self.mode = 'w'
        self.stream = self._open()

    def format(self, record):
        """Strip trailing newlines before outputting text to file."""
        text = logging.handlers.RotatingFileHandler.format(self, record)
        return text.rstrip("\r\n")


class LoggingFormatter(logging.Formatter):

    """Format LogRecords for output to file.

    This formatter *ignores* the 'newline' key of the LogRecord, because
    every record written to a file must end with a newline, regardless of
    whether the output to the user's console does.

    """

    def formatException(self, ei):
        r"""
        Convert exception trace to unicode if necessary.

        Make sure that the exception trace is converted to unicode:
            * our pywikibot.Error traces are encoded in our
              console encoding, which is needed for plainly printing them.
            * but when it comes to logging using logging.exception,
              the Python logging module will try to use these traces,
              and it will fail if they are console encoded strings.

        Formatter.formatException also strips the trailing \n, which we need.
        """
        strExc = logging.Formatter.formatException(self, ei)

        if isinstance(strExc, str):
            return strExc.decode(config.console_encoding) + '\n'
        else:
            return strExc + '\n'


# Initialize the handlers and formatters for the logging system.
#
# This relies on the global variable 'ui' which is a UserInterface object
# defined in the 'userinterface' subpackage.
#
# The UserInterface object must define its own init_handlers() method
# which takes the root logger as its only argument, and which adds to that
# logger whatever handlers and formatters are needed to process output and
# display it to the user.  The default (terminal) interface sends level
# STDOUT to sys.stdout (as all interfaces should) and sends all other
# levels to sys.stderr; levels WARNING and above are labeled with the
# level name.
#
# UserInterface objects must also define methods input(), inputChoice(),
# editText(), and askForCaptcha(), all of which are documented in
# userinterfaces/terminal_interface.py

_handlers_initialized = False


def init_handlers(strm=None):
    """Initialize logging system for terminal-based bots.

    This function must be called before using pywikibot.output(); and must
    be called again if the destination stream is changed.

    @param strm: Output stream. If None, re-uses the last stream if one
        was defined, otherwise uses sys.stderr

    Note: this function is called by handleArgs(), so it should normally
    not need to be called explicitly

    All user output is routed through the logging module.
    Each type of output is handled by an appropriate handler object.
    This structure is used to permit eventual development of other
    user interfaces (GUIs) without modifying the core bot code.
    The following output levels are defined:
       DEBUG - only for file logging; debugging messages
       STDOUT - output that must be sent to sys.stdout (for bots that may
                have their output redirected to a file or other destination)
       VERBOSE - optional progress information for display to user
       INFO - normal (non-optional) progress information for display to user
       INPUT - prompts requiring user response
       WARN - user warning messages
       ERROR - user error messages
       CRITICAL - fatal error messages
    Accordingly, do ''not'' use print statements in bot code; instead,
    use pywikibot.output function.
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
    if hasattr(root_logger, 'captureWarnings'):
        root_logger.captureWarnings(True)  # introduced in Python >= 2.7
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

    _handlers_initialized = True

    writelogheader()


def writelogheader():
    """
    Save additional version, system and status info to the log file in use.

    This may help the user to track errors or report bugs.
    """
    # if site not available it's too early to print a header (work-a-round)
    try:
        site = pywikibot.Site()
    except AttributeError:
        return

    log(u'=== Pywikibot framework v2.0 -- Logging header ===')

    # script call
    log(u'COMMAND: %s' % unicode(sys.argv))

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
        log(u'SYSTEM: %s' % unicode(os.uname()))

    all_modules = sys.modules.keys()

    # These are the main dependencies of pywikibot.
    check_package_list = ['httplib2', 'mwparserfromhell']

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
    for item in list(all_modules):
        ver = version.getfileversion('%s.py' % item.replace('.', '/'))
        if ver:
            log(u'  %s' % ver)

    if config.log_pywiki_repo_version:
        log(u'PYWIKI REPO VERSION: %s' % unicode(version.getversion_onlinerepo()))

    log(u'SITE VERSION: %s' % unicode(site.live_version()))

    # messages on bot discussion page?
    if site.logged_in():
        if site.messages():
            messagestate = 'unanswered'
        else:
            messagestate = 'none'
    else:
        messagestate = 'unknown (not logged in)'
    log(u'MESSAGES: %s' % messagestate)

    log(u'=== ' * 14)


# User output/logging functions

# Six output functions are defined. Each requires a unicode or string
# argument.  All of these functions generate a message to the log file if
# logging is enabled ("-log" or "-debug" command line arguments).

# The functions output(), stdout(), warning(), and error() all display a
# message to the user through the logger object; the only difference is the
# priority level,  which can be used by the application layer to alter the
# display. The stdout() function should be used only for data that is
# the "result" of a script, as opposed to information messages to the
# user.

# The function log() by default does not display a message to the user, but
# this can be altered by using the "-verbose" command line option.

# The function debug() only logs its messages, they are never displayed on
# the user console. debug() takes a required second argument, which is a
# string indicating the debugging layer.

def logoutput(text, decoder=None, newline=True, _level=INFO, _logger="",
              **kwargs):
    """Format output and send to the logging module.

    Helper function used by all the user-output convenience functions.

    """
    if _logger:
        logger = logging.getLogger("pywiki." + _logger)
    else:
        logger = logging.getLogger("pywiki")

    # make sure logging system has been initialized
    if not _handlers_initialized:
        init_handlers()

    # frame 0 is logoutput() in this module,
    # frame 1 is the convenience function (output(), etc.)
    # frame 2 is whatever called the convenience function
    frame = sys._getframe(2)

    module = os.path.basename(frame.f_code.co_filename)
    context = {'caller_name': frame.f_code.co_name,
               'caller_file': module,
               'caller_line': frame.f_lineno,
               'newline': ("\n" if newline else "")}

    if decoder:
        text = unicode(text, decoder)
    elif not isinstance(text, unicode):
        if not isinstance(text, str):
            # looks like text is a non-text object.
            # Maybe it has a __unicode__ builtin ?
            # (allows to print Page, Site...)
            text = unicode(text)
        else:
            try:
                text = unicode(text, 'utf-8')
            except UnicodeDecodeError:
                text = unicode(text, 'iso8859-1')

    logger.log(_level, text, extra=context, **kwargs)


def output(text, decoder=None, newline=True, toStdout=False, **kwargs):
    r"""Output a message to the user via the userinterface.

    Works like print, but uses the encoding used by the user's console
    (console_encoding in the configuration file) instead of ASCII.

    If decoder is None, text should be a unicode string. Otherwise it
    should be encoded in the given encoding.

    If newline is True, a line feed will be added after printing the text.

    If toStdout is True, the text will be sent to standard output,
    so that it can be piped to another process. All other text will
    be sent to stderr. See: https://en.wikipedia.org/wiki/Pipeline_%28Unix%29

    text can contain special sequences to create colored output. These
    consist of the escape character \03 and the color name in curly braces,
    e. g. \03{lightpurple}. \03{default} resets the color.

    Other keyword arguments are passed unchanged to the logger; so far, the
    only argument that is useful is "exc_info=True", which causes the
    log message to include an exception traceback.

    """
    if toStdout:  # maintained for backwards-compatibity only
        logoutput(text, decoder, newline, STDOUT, **kwargs)
    else:
        logoutput(text, decoder, newline, INFO, **kwargs)


def stdout(text, decoder=None, newline=True, **kwargs):
    """Output script results to the user via the userinterface."""
    logoutput(text, decoder, newline, STDOUT, **kwargs)


def warning(text, decoder=None, newline=True, **kwargs):
    """Output a warning message to the user via the userinterface."""
    logoutput(text, decoder, newline, WARNING, **kwargs)


def error(text, decoder=None, newline=True, **kwargs):
    """Output an error message to the user via the userinterface."""
    logoutput(text, decoder, newline, ERROR, **kwargs)


def log(text, decoder=None, newline=True, **kwargs):
    """Output a record to the log file."""
    logoutput(text, decoder, newline, VERBOSE, **kwargs)


def critical(text, decoder=None, newline=True, **kwargs):
    """Output a critical record to the log file."""
    logoutput(text, decoder, newline, CRITICAL, **kwargs)


def debug(text, layer, decoder=None, newline=True, **kwargs):
    """Output a debug record to the log file.

    @param layer: The name of the logger that text will be sent to.
    """
    logoutput(text, decoder, newline, DEBUG, layer, **kwargs)


def exception(msg=None, decoder=None, newline=True, tb=False, **kwargs):
    """Output an error traceback to the user via the userinterface.

    @param tb: Set to True in order to output traceback also.

    Use directly after an 'except' statement:
      ...
      except:
          pywikibot.exception()
      ...
    or alternatively:
      ...
      except Exception, e:
          pywikibot.exception(e)
      ...
    """
    if isinstance(msg, BaseException):
        exc_info = 1
    else:
        exc_info = sys.exc_info()
        msg = u'%s: %s' % (repr(exc_info[1]).split('(')[0],
                           unicode(exc_info[1]).strip())
    if tb:
        kwargs['exc_info'] = exc_info
    logoutput(msg, decoder, newline, ERROR, **kwargs)


# User input functions


def input(question, password=False):
    """Ask the user a question, return the user's answer.

    Parameters:
    * question - a unicode string that will be shown to the user. Don't add a
                 space after the question mark/colon, this method will do this
                 for you.
    * password - if True, hides the user's input (for password entry).

    Returns a unicode string.

    """
    # make sure logging system has been initialized
    if not _handlers_initialized:
        init_handlers()

    data = ui.input(question, password)
    return data


def inputChoice(question, answers, hotkeys, default=None):
    """Ask the user a question with several options, return the user's choice.

    The user's input will be case-insensitive, so the hotkeys should be
    distinctive case-insensitively.

    Parameters:
    * question - a unicode string that will be shown to the user. Don't add a
                 space after the question mark, this method will do this
                 for you.
    * answers  - a list of strings that represent the options.
    * hotkeys  - a list of one-letter strings, one for each answer.
    * default  - an element of hotkeys, or None. The default choice that will
                 be returned when the user just presses Enter.

    Returns a one-letter string in lowercase.

    """
    # make sure logging system has been initialized
    if not _handlers_initialized:
        init_handlers()

    data = ui.inputChoice(question, answers, hotkeys, default).lower()
    return data


# Command line parsing and help
def calledModuleName():
    """Return the name of the module calling this function.

    This is required because the -help option loads the module's docstring
    and because the module name will be used for the filename of the log.

    """
    # get commandline arguments
    called = pywikibot.argvu[0].strip()
    if ".py" in called:  # could end with .pyc, .pyw, etc. on some platforms
        # clip off the '.py?' filename extension
        called = called[:called.rindex('.py')]
    return os.path.basename(called)


def handleArgs(*args):
    """Handle standard command line arguments, return the rest as a list.

    Takes the command line arguments as Unicode strings, processes all
    global parameters such as -lang or -log. Returns a list of all arguments
    that are not global. This makes sure that global arguments are applied
    first, regardless of the order in which the arguments were given.

    args may be passed as an argument, thereby overriding sys.argv

    """
    # get commandline arguments if necessary
    if not args:
        # it's the version in pywikibot.__init__ that is changed by scripts,
        # not the one in pywikibot.bot.
        args = pywikibot.argvu[1:]
    # get the name of the module calling this function. This is
    # required because the -help option loads the module's docstring and because
    # the module name will be used for the filename of the log.
    moduleName = calledModuleName()
    if not moduleName:
        moduleName = "terminal-interface"
    nonGlobalArgs = []
    username = None
    do_help = False
    for arg in args:
        if arg == '-help':
            do_help = True
        elif arg.startswith('-family:'):
            config.family = arg[len("-family:"):]
        elif arg.startswith('-lang:'):
            config.mylang = arg[len("-lang:"):]
        elif arg.startswith("-user:"):
            username = arg[len("-user:"):]
        elif arg.startswith('-putthrottle:'):
            config.put_throttle = int(arg[len("-putthrottle:"):])
        elif arg.startswith('-pt:'):
            config.put_throttle = int(arg[len("-pt:"):])
        elif arg == '-log':
            if moduleName not in config.log:
                config.log.append(moduleName)
        elif arg.startswith('-log:'):
            if moduleName not in config.log:
                config.log.append(moduleName)
            config.logfilename = arg[len("-log:"):]
        elif arg == '-nolog':
            if moduleName in config.log:
                config.log.remove(moduleName)
        elif arg in ('-cosmeticchanges', '-cc'):
            config.cosmetic_changes = not config.cosmetic_changes
            output(u'NOTE: option cosmetic_changes is %s\n'
                   % config.cosmetic_changes)
        elif arg == '-simulate':
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
        elif arg == '-debug':
            if moduleName not in config.log:
                config.log.append(moduleName)
            if "" not in config.debug_log:
                config.debug_log.append("")
        elif arg.startswith("-debug:"):
            if moduleName not in config.log:
                config.log.append(moduleName)
            component = arg[len("-debug:"):]
            if component not in config.debug_log:
                config.debug_log.append(component)
        elif arg in ('-verbose', '-v'):
            config.verbose_output += 1
        elif arg == '-daemonize':
            import daemonize
            daemonize.daemonize()
        elif arg.startswith('-daemonize:'):
            import daemonize
            daemonize.daemonize(redirect_std=arg[len('-daemonize:'):])
        else:
            # the argument depends on numerical config settings
            # e.g. -maxlag:
            try:
                _arg, _val = arg[1:].split(':')
                # explicitly check for int (so bool doesn't match)
                if not isinstance(getattr(config, _arg), int):
                    raise TypeError
                setattr(config, _arg, int(_val))
            except (ValueError, TypeError, AttributeError):
                # argument not global -> specific bot script will take care
                nonGlobalArgs.append(arg)

    if username:
        config.usernames[config.family][config.mylang] = username

    init_handlers()

    if config.verbose_output:
        # Please don't change the regular expression here unless you really
        # have to - some git versions (like 1.7.0.4) seem to treat lines
        # containing just `$Id:` as if they were ident lines (see
        # gitattributes(5)) leading to unwanted behaviour like automatic
        # replacement with `$Id$`
        # or `$Id$`.
        m = re.search(r"\$Id"
                      r": (\w+) \$", pywikibot.__version__)
        if m:
            pywikibot.output(u'Pywikibot r%s' % m.group(1))
        else:
            # Version ID not availlable on SVN repository.
            # Maybe these informations should be imported from version.py
            pywikibot.output(u'Pywikibot SVN repository')
        pywikibot.output(u'Python %s' % sys.version)

    if do_help:
        showHelp()
        sys.exit(0)
    pywikibot.debug(u"handleArgs() completed.", _logger)
    return nonGlobalArgs


def showHelp(module_name=None):
    if not module_name:
        module_name = calledModuleName()
    if not module_name:
        try:
            module_name = sys.modules['__main__'].main.__module__
        except NameError:
            module_name = "no_module"

    globalHelp = u'''
Global arguments available for all bots:

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
                  stdout and stderr to xyz (only use for bots that require
                  no input from stdin).

-help             Show this help text.

-log              Enable the log file, using the default filename
                  '%s-bot.log'
                  Logs will be stored in the logs subdirectory.

-log:xyz          Enable the log file, using 'xyz' as the filename.

-nolog            Disable the log file (if it is enabled by default).

-maxlag           Sets a new maxlag parameter to a number of seconds. Defer bot
                  edits during periods of database server lag. Default is set by
                  config.py

-putthrottle:n    Set the minimum time (in seconds) the bot will wait between
-pt:n             saving pages.
-put_throttle:n

-debug:item       Enable the log file and include extensive debugging data
-debug            for component "item" (for all components if the second form
                  is used).

-verbose          Have the bot provide additional console output that may be
-v                useful in debugging.

-cosmeticchanges  Toggles the cosmetic_changes setting made in config.py or
-cc               user_config.py to its inverse and overrules it. All other
                  settings and restrictions are untouched.

-simulate         Disables writing to the server. Useful for testing and
                  debugging of new code (if given, doesn't do any real
                  changes, but only shows what would have been changed).

-<config var>:n   You may use all given numeric config variables as option and
                  modify it with command line.

''' % module_name
    try:
        module = __import__('%s' % module_name)
        helpText = module.__doc__.decode('utf-8')
        if hasattr(module, 'docuReplacements'):
            for key, value in module.docuReplacements.items():
                helpText = helpText.replace(key, value.strip('\n\r'))
        pywikibot.stdout(helpText)  # output to STDOUT
    except Exception:
        if module_name:
            pywikibot.stdout(u'Sorry, no help available for %s' % module_name)
        pywikibot.log('showHelp:', exc_info=True)
    pywikibot.stdout(globalHelp)


class Bot(object):

    """
    Generic Bot to be subclassed
    """

    # Bot configuration.
    # Only the keys of the dict can be passed as init options
    # The values are the default values
    # Extend this in subclasses!
    availableOptions = {
        'always': False,  # ask for confirmation when putting a page?
    }

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
        # contains the options overriden from defaults
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

        @param option: key defined in Bot.availableOptions
        """
        try:
            return self.options.get(option, self.availableOptions[option])
        except KeyError:
            raise pywikibot.Error(u'%s is not a valid bot option.' % option)

    def userPut(self, page, oldtext, newtext, **kwargs):
        """
        Print differences, ask user for confirmation,
        and puts the page if needed.

        Option used:
            * 'always'
        """
        if oldtext == newtext:
            pywikibot.output(u'No changes were needed on %s'
                             % page.title(asLink=True))
            return

        pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                         % page.title())
        pywikibot.showDiff(oldtext, newtext)

        choice = 'a'
        if not self.getOption('always'):
            choice = pywikibot.inputChoice(
                u'Do you want to accept these changes?',
                ['Yes', 'No', 'All'],
                ['y', 'N', 'a'],
                'N'
            )
            if choice == 'a':
                # Remember the choice
                self.options['always'] = True

        if 'async' not in kwargs:
            kwargs['async'] = (choice == 'a')

        if choice != 'n':
            page.text = newtext
            page.save(**kwargs)


class WikidataBot:

    """
    Generic Wikidata Bot to be subclassed.

    Used in claimit.py, coordinate_import.py and harvest_template.py
    """

    def cacheSources(self):
        """
        Fetch the sources from the list on Wikidata.

        It is stored internally and reused by getSource()
        """
        page = pywikibot.Page(self.repo, u'List of wikis/python', ns=4)
        self.source_values = json.loads(page.get())
        for family_code, family in self.source_values.iteritems():
            for source_lang in family:
                self.source_values[family_code][source_lang] = pywikibot.ItemPage(self.repo,
                                                                                  family[source_lang])

    def getSource(self, site):
        """
        Create a Claim usable as a source for Wikibase statements.

        @param site: site that is the source of assertions.
        @type site: Site

        @return: Claim
        """
        if site.family.name in self.source_values and site.code in self.source_values[site.family.name]:
            source = pywikibot.Claim(self.repo, 'P143')
            source.setTarget(self.source_values.get(site.family.name).get(site.code))
            return source
