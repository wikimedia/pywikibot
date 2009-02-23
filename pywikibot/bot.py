# -*- coding: utf-8  -*-
"""
User-interface related functions for building bots
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

# Note: the intention is to develop this module (at some point) into a Bot
# class definition that can be subclassed to create new, functional bot
# scripts, instead of writing each one from scratch.


import logging, logging.handlers
       # all output goes thru python std library "logging" module
import os.path
import sys

# logging levels
logger = logging.getLogger("bot")

from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
STDOUT = 16
VERBOSE = 18
INPUT = 25

import pywikibot
from pywikibot import config


class MaxLevelFilter(logging.Filter):
    """Filter that only passes records at or below a specific level.

    (setting handler level only passes records at or *above* a specified level,
    so this provides the opposite functionality)

    """
    def __init__(self, level=None):
        self.level = level

    def filter(self, record):
        if self.level:
            return record.levelno <= self.level
        else:
            return True


class TerminalHandler(logging.Handler):
    """
    A handler class that writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout or sys.stderr may be used.

    Slightly modified version of the StreamHandler class that ships with
    logging module.
    
    """
    def __init__(self, strm=None):
        """
        Initialize the handler.

        If strm is not specified, sys.stderr is used.
        """
        logging.Handler.__init__(self)
        if strm is None:
            strm = sys.stderr
        self.stream = strm
        self.formatter = None

    def flush(self):
        """
        Flush the stream.
        """
        self.stream.flush()

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record. The
        record is then written to the stream. If exception information is
        present, it is formatted using traceback.print_exception and
        appended to the stream.
        """
        try:
            msg = self.format(record)
            fs = "%s"
            if isinstance(msg, str):
                self.stream.write(fs % msg)
            else:
                try:
                    self.stream.write(fs % msg.encode(config.console_encoding,
                                                      "xmlcharrefreplace"))
                except UnicodeError:
                    self.stream.write(fs % msg.encode("ascii",
                                                      "xmlcharrefreplace"))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)



# User interface initialization
# search for user interface module in the 'userinterfaces' subdirectory
exec ("import pywikibot.userinterfaces.%s_interface as uiModule"
      % config.userinterface)
ui = uiModule.UI()

def output(text, decoder=None, newline=True, toStdout=False, level=INFO):
    """Output a message to the user via the userinterface.

    Works like print, but uses the encoding used by the user's console
    (console_encoding in the configuration file) instead of ASCII.
    If decoder is None, text should be a unicode string. Otherwise it
    should be encoded in the given encoding.

    If newline is True, a linebreak will be added after printing the text.

    If toStdout is True, the text will be sent to standard output,
    so that it can be piped to another process. All other text will
    be sent to stderr. See: http://en.wikipedia.org/wiki/Pipeline_%28Unix%29

    text can contain special sequences to create colored output. These
    consist of the escape character \03 and the color name in curly braces,
    e. g. \03{lightpurple}. \03{default} resets the color.

    @param level: output level for logging module; use VERBOSE for optional
        messages, INPUT for prompts requiring user reponse (not yet fully
        implemented)

    """
    # make sure logging system has been initialized
    root = logging.getLogger()
    if root.level == 30: # init_handlers sets this level
        init_handlers()

    if decoder:
        text = unicode(text, decoder)
    elif not isinstance(text, unicode):
##        import traceback
##        pywikibot.output(
##            u"Non-unicode (%s) passed to wikipedia.output without decoder!\n"
##             % type(text),
##            level=VERBOSE
##        )
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
    if newline:
        text += u'\n'
    if toStdout:
        level = STDOUT
    ui.output(text, level=level)

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
    root = logging.getLogger()
    if root.level == 30: # init_handlers sets this level
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
    root = logging.getLogger()
    if root.level == 30: # init_handlers sets this level
        init_handlers()

    data = ui.inputChoice(question, answers, hotkeys, default).lower()
    return data


def init_handlers():
    """Initialize logging system for terminal-based bots"""

    # All user output is routed through the logging module.
    # Each type of output is handled by an appropriate handler object.
    # This structure is used to permit eventual development of other
    # user interfaces (GUIs) without modifying the core bot code.
    # The following output levels are defined:
    #    DEBUG - only for file logging; debugging messages
    #    STDOUT - output that must be sent to sys.stdout (for bots that may
    #             have their output redirected to a file or other destination)
    #    VERBOSE - optional progress information for display to user
    #    INFO - normal (non-optional) progress information for display to user
    #    INPUT - prompts requiring user response
    #    WARN - user warning messages
    #    ERROR - user error messages
    #    CRITICAL - fatal error messages
    # Accordingly, do ''not'' use print statements in bot code; instead,
    # use pywikibot.output function.

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

    root_logger = logging.getLogger()
    root_logger.handlers = [] # get rid of default handler
    root_logger.setLevel(DEBUG+1) # all records except DEBUG go to logger

    # configure default handler for VERBOSE and INFO levels
    default_handler = TerminalHandler(strm=sys.stderr)
    if config.verbose_output:
        default_handler.setLevel(VERBOSE)
    else:
        default_handler.setLevel(INFO)
    default_handler.addFilter(MaxLevelFilter(INPUT))
    default_handler.setFormatter(logging.Formatter(fmt="%(message)s"))
    root_logger.addHandler(default_handler)

    # if user has enabled file logging, configure file handler
    if moduleName in config.log or '*' in config.log:
        if config.logfilename:
            logfile = config.datafilepath(config.logfilename)
        else:
            logfile = config.datafilepath("%s-bot.log" % moduleName)
        file_handler = logging.handlers.RotatingFileHandler(
                            filename=logfile, maxBytes=2 << 20, backupCount=5)
        
        file_handler.setLevel(DEBUG)
        form = logging.Formatter(
                   fmt="%(asctime)s %(filename)18s, %(lineno)d: "
                       "%(levelname)-8s %(message)s",
                   datefmt="%Y-%m-%d %H:%M:%S"
               )
        file_handler.setFormatter(form)
        root_logger.addHandler(file_handler)
        for component in config.debug_log:
            debuglogger = logging.getLogger(component)
            debuglogger.setLevel(DEBUG)
            debuglogger.addHandler(file_handler)

    # handler for level STDOUT
    output_handler = TerminalHandler(strm=sys.stdout)
    output_handler.setLevel(STDOUT)
    output_handler.addFilter(MaxLevelFilter(STDOUT))
    output_handler.setFormatter(logging.Formatter(fmt="%(message)s"))
    root_logger.addHandler(output_handler)

    # handler for levels WARNING and higher
    warning_handler = TerminalHandler(strm=sys.stderr)
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(
            logging.Formatter(fmt="%(levelname)s: %(message)s"))
    root_logger.addHandler(warning_handler)


# Command line parsing and help

def calledModuleName():
    """Return the name of the module calling this function.

    This is required because the -help option loads the module's docstring
    and because the module name will be used for the filename of the log.

    """
    # get commandline arguments
    called = sys.argv[0].strip()
    if ".py" in called:  # could end with .pyc, .pyw, etc. on some platforms
        called = called[ : called.rindex(".py")]
    return os.path.basename(called)

def _decodeArg(arg):
    if sys.platform=='win32':
        if config.console_encoding in ("cp437", 'cp850'):
            # Western Windows versions give parameters encoded as windows-1252
            # even though the console encoding is cp850 or cp437.
            return unicode(arg, 'windows-1252')
        elif config.console_encoding == 'cp852':
            # Central/Eastern European Windows versions give parameters encoded
            # as windows-1250 even though the console encoding is cp852.
            return unicode(arg, 'windows-1250')
        else:
            return unicode(arg, config.console_encoding)
    else:
        # Linux uses the same encoding for both.
        # I don't know how non-Western Windows versions behave.
        return unicode(arg, config.console_encoding)

def handleArgs(*args):
    """Handle standard command line arguments, return the rest as a list.

    Takes the commandline arguments, converts them to Unicode, processes all
    global parameters such as -lang or -log. Returns a list of all arguments
    that are not global. This makes sure that global arguments are applied
    first, regardless of the order in which the arguments were given.

    args may be passed as an argument, thereby overriding sys.argv

    """
    # get commandline arguments if necessary
    if not args:
        args = sys.argv[1:]
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
        arg = _decodeArg(arg)
        if arg == '-help':
            do_help = True
        elif arg.startswith('-family:'):
            config.family = arg[len("-family:") : ]
        elif arg.startswith('-lang:'):
            config.mylang = arg[len("-lang:") : ]
        elif arg.startswith("-user:"):
            username = arg[len("-user:") : ]
        elif arg.startswith('-putthrottle:'):
            config.put_throttle = int(arg[len("-putthrottle:") : ])
        elif arg.startswith('-pt:'):
            config.put_throttle = int(arg[len("-pt:") : ])
        elif arg.startswith("-maxlag:"):
            config.maxlag = int(arg[len("-maxlag:") : ])
        elif arg == '-log':
            if moduleName not in config.log:
                config.log.append(moduleName)
        elif arg.startswith('-log:'):
            if moduleName not in config.log:
                config.log.append(moduleName)
            config.logfilename = arg[len("-log:") : ]
        elif arg == '-nolog':
            if moduleName in config.log:
                config.log.remove(moduleName)
        elif arg == "-debug":
            if moduleName not in config.log:
                config.log.append(moduleName)
            if "" not in config.debug_log:
                config.debug_log.append("")
        elif arg.startswith("-debug:"):
            if moduleName not in config.log:
                config.log.append(moduleName)
            component = arg[len("-debug:") : ]
            if component not in config.debug_log:
                config.debug_log.append(component)
        elif arg == '-verbose' or arg == "-v":
            config.verbose_output += 1
        elif arg == '-daemonize':
            import daemonize
            daemonize.daemonize()
        elif arg.startswith('-daemonize:'):
            import daemonize
            daemonize.daemonize(redirect_std = arg[11:])
        else:
            # the argument is not global. Let the specific bot script care
            # about it.
            nonGlobalArgs.append(arg)

    if username:
        config.usernames[config.family][config.mylang] = username

    init_handlers()

    if config.verbose_output:
        import re
        ver = pywikibot.__version__ # probably can be improved on
        m = re.search(r"\$Id: .* (\d+ \d+-\d+-\d+ \d+:\d+:\d+Z) .*\$", ver)
        pywikibot.output(u'Pywikipediabot r%s' % m.group(1))
        pywikibot.output(u'Python %s' % sys.version)

    if do_help:
        showHelp()
        sys.exit(0)
    logger.debug(u"handleArgs() completed.")
    return nonGlobalArgs


def showHelp(name=""):
    # argument, if given, is ignored
    modname = calledModuleName()
    if not modname:
        try:
            modname = sys.modules['__main__'].main.__module__
        except NameError:
            modname = "no_module"

    globalHelp =u'''\
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

-log              Enable the logfile, using the default filename
                  '%s-bot.log'

-log:xyz          Enable the logfile, using 'xyz' as the filename.

-nolog            Disable the logfile (if it is enabled by default).

-debug:item       Enable the logfile and include extensive debugging data
-debug            for component "item" (or all components if the second form
                  is used).

-putthrottle:n    Set the minimum time (in seconds) the bot will wait between
-pt:n             saving pages.

-verbose          Have the bot provide additional console output that may be
-v                useful in debugging.

''' % modname
    try:
        exec('import %s as module' % modname)
        helpText = module.__doc__.decode('utf-8')
        if hasattr(module, 'docuReplacements'):
            for key, value in module.docuReplacements.iteritems():
                helpText = helpText.replace(key, value.strip('\n\r'))
        pywikibot.output(helpText, level=pywikibot.STDOUT) # output to STDOUT
    except Exception:
        if modname:
            pywikibot.output(u'Sorry, no help available for %s' % modname,
                             level=pywikibot.STDOUT)
        logging.exception('showHelp:')
    pywikibot.output(globalHelp, level=pywikibot.STDOUT)
