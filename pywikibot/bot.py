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
import os.path
import sys
import pywikibot
from pywikibot import config2 as config


# logging levels

from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
STDOUT = 16
VERBOSE = 18
INPUT = 25


def output(text, decoder=None, newline=True, toStdout=False, level=INFO):
    if toStdout:
        level = STDOUT
    logging.getLogger().log(level, text)


def input(prompt, password=False):
    logging.getLogger().log(INPUT, prompt)
    if password:
        import getpass
        return getpass.getpass("")
    return raw_input()


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


def _decodeArg(arg):
    if sys.platform=='win32':
        if config.console_encoding == 'cp850':
            # Western Windows versions give parameters encoded as windows-1252
            # even though the console encoding is cp850.
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
    for arg in args:
        arg = _decodeArg(arg)
        if arg == '-help':
            showHelp()
            sys.exit(0)
        elif arg.startswith('-family:'):
            config.family = arg[8:]
        elif arg.startswith('-lang:'):
            config.mylang = arg[6:]
        elif arg.startswith("-user:"):
            username = arg[6:]
        elif arg.startswith('-putthrottle:'):
            config.put_throttle = int(arg[13:])
        elif arg.startswith('-pt:'):
            config.put_throttle = int(arg[4:])
        elif arg == '-log':
            if moduleName not in config.log:
                config.log.append(moduleName)
        elif arg.startswith('-log:'):
            if moduleName not in config.log:
                config.log.append(moduleName)
            config.logfilename = arg[5:]
        elif arg == '-nolog':
            if moduleName in config.log:
                config.log.remove(moduleName)
        elif arg == "-debug":
            if moduleName not in config.log:
                config.log.append(moduleName)
            config.debug_log = True
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

    # initialize logging system for terminal-based bots

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
    # send output to the pywikibot.output() function which will route it
    # to the logging module.

    logging.addLevelName(VERBOSE, "VERBOSE")
        # for messages to be displayed on terminal at "verbose" setting
        # use INFO for messages to be displayed even on non-verbose setting
    logging.addLevelName(STDOUT, "STDOUT")
        # for messages to be displayed to stdout
    logging.addLevelName(INPUT, "INPUT")
        # for prompts requiring user response

    root_logger = logging.getLogger()
    # default handler for VERBOSE and INFO levels
    default_handler = root_logger.handlers[0]
    root_logger.setLevel(DEBUG) # all records go to logger

    # configure default handler for VERBOSE, INFO, and INPUT levels
    if config.verbose_output:
        default_handler.setLevel(VERBOSE)
    else:
        default_handler.setLevel(INFO)
    default_handler.addFilter(MaxLevelFilter(INPUT))
    default_handler.setFormatter(logging.Formatter(fmt="%(message)s"))

    # if user has enabled file logging, configure file handler
    if moduleName in config.log or '*' in config.log:
        if config.logfilename:
            logfile = config.datafilepath(config.logfilename)
        else:
            logfile = config.datafilepath("%s-bot.log" % moduleName)
        file_handler = logging.handlers.RotatingFileHandler(
                            filename=logfile, maxBytes=2 << 20, backupCount=5)
        if config.debug_log:
            file_handler.setLevel(DEBUG)
        else:
            file_handler.setLevel(VERBOSE)
        form = logging.Formatter(
                   fmt="%(asctime)s %(filename)-18s:%(lineno)-4d "
                       "%(levelname)-8s %(message)s",
                   datefmt="%Y-%m-%d %H:%M:%S"
               )
        file_handler.setFormatter(form)
        root_logger.addHandler(file_handler)

    # handler for level STDOUT
    output_handler = logging.StreamHandler(strm=sys.stdout)
    output_handler.setLevel(STDOUT)
    output_handler.addFilter(MaxLevelFilter(STDOUT))
    root_logger.addHandler(output_handler)

    # handler for levels WARNING and higher
    warning_handler = logging.StreamHandler() # uses sys.stderr
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(
            logging.Formatter(fmt="%(levelname)s: %(message)s"))
    root_logger.addHandler(warning_handler)

    if config.verbose_output:
        import re
        ver = pywikibot.__version__ # probably can be improved on
        m = re.search(r"\$Id: .* (\d+ \d+-\d+-\d+ \d+:\d+:\d+Z) .*\$", ver)
        pywikibot.output(u'Pywikipediabot r%s' % m.group(1))
        pywikibot.output(u'Python %s' % sys.version)

    root_logger.debug("handleArgs() completed.")
    return nonGlobalArgs


def showHelp(name=""):
    # argument, if given, is ignored
    modname = calledModuleName()
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

-debug            Enable the logfile and include extensive debugging data.

-putthrottle:n    Set the minimum time (in seconds) the bot will wait between
-pt:n             saving pages.

-verbose          Have the bot provide additional output that may be useful in
-v                debugging.
''' % modname
    try:
        exec('import %s as module' % modname)
        helpText = module.__doc__.decode('utf-8')
        if hasattr(module, 'docuReplacements'):
            for key, value in module.docuReplacements.iteritems():
                helpText = helpText.replace(key, value.strip('\n\r'))
        pywikibot.output(helpText)
    except:
        if modname:
            pywikibot.output(u'Sorry, no help available for %s' % modname)
        logging.exception('showHelp:')
    pywikibot.output(globalHelp)
