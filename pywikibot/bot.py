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
    for arg in args:
        arg = _decodeArg(arg)
        if arg == '-help':
            showHelp(moduleName)
            sys.exit(0)
        elif arg.startswith('-family:'):
            config.family = arg[8:]
        elif arg.startswith('-lang:'):
            config.code = arg[6:]
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
            config.log.debug_log = True
        elif arg == '-verbose' or arg == "-v":
            pywikibot.output(u'Pywikipediabot %s' % (version.getversion()))
            pywikibot.output(u'Python %s' % (sys.version))
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

    # initialize logging system for terminal-based bots

    logging.addLevelName(18, "VERBOSE") # for messages to be displayed on 
                                        # terminal at "verbose" setting
                                        # use INFO for messages to be displayed
                                        # even on non-verbose setting
    logging.addLevelName(24, "STDOUT")  # for messages to be displayed to stdout
    logging.addLevelName(26, "INPUT")   # for prompts requiring user response

    logging.basicConfig()               # initializes root logger
    root_logger = logging.getLogger()
    if config.verbose_output:
        root_logger.setLevel("VERBOSE")
    else:
        root_logger.setLevel(logging.INFO)
    if moduleName in config.log:
        if config.logfilename:
            logfile = config.datafilepath(config.logfilename)
        else:
            logfile = config.datafilepath("%s.log" % moduleName)
        file_handler = logging.handlers.RotatingFileHandler(
                            filename=logfile, maxBytes=2 << 20, backupCount=5)
        if config.debug_log:
            file_handler.setLevel(logging.DEBUG)
        else:
            file_handler.setLevel("VERBOSE")
        logging.addHandler(file_handler)

    return nonGlobalArgs


def showHelp(name=""):
    # argument, if given, is ignored
    module = calledModuleName()
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

-daemonize:xyz    Immediately returns control to the terminal and redirects
                  stdout and stderr to xyz (only use for bots that require
                  no input from stdin).

-help             Shows this help text.

-log              Enable the logfile. Logs will be stored in the logs
                  subdirectory.

-log:xyz          Enable the logfile, using xyz as the filename.

-nolog            Disable the logfile (if it is enabled by default).

-putthrottle:n    Set the minimum time (in seconds) the bot will wait between
-pt:n             saving pages.

-verbose          Have the bot provide additional output that may be useful in
-v                debugging.
'''
    try:
        exec('import %s as module' % module)
        helpText = module.__doc__.decode('utf-8')
        if hasattr(module, 'docuReplacements'):
            for key, value in module.docuReplacements.iteritems():
                helpText = helpText.replace(key, value.strip('\n\r'))
        pywikibot.output(helpText)
    except:
        if module:
            pywikibot.output(u'Sorry, no help available for %s' % module)
        logging.exception('showHelp:')
    pywikibot.output(globalHelp)
