# -*- coding: utf-8 -*-
#
# (C) Pywikipedia bot team, 2003-2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import transliteration
import traceback, re, sys
import pywikibot as wikipedia
from pywikibot import config
from pywikibot.bot import DEBUG, VERBOSE, INFO, STDOUT, INPUT, WARNING
import logging

transliterator = transliteration.transliterator(config.console_encoding)

colors = [
    'default',
    'black',
    'blue',
    'green',
    'aqua',
    'red',
    'purple',
    'yellow',
    'lightgray',
    'gray',
    'lightblue',
    'lightgreen',
    'lightaqua',
    'lightred',
    'lightpurple',
    'lightyellow',
    'white',
]

colorTagR = re.compile('\03{(?P<name>%s)}' % '|'.join(colors))


class UI:
    def __init__(self):
        self.stdin  = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.encoding = config.console_encoding
        self.transliteration_target = config.transliteration_target
        
        self.stderr = sys.stderr
        self.stdout = sys.stdout
        
    def init_handlers(self, root_logger, default_stream='stderr'):
        """Initialize the handlers for user output.

        This method initializes handler(s) for output levels VERBOSE (if
        enabled by config.verbose_output), INFO, STDOUT, WARNING, ERROR,
        and CRITICAL.  STDOUT writes its output to sys.stdout; all the
        others write theirs to sys.stderr.

        """

        if default_stream == 'stdout':
            default_stream = self.stdout
        elif default_stream == 'stderr':
            default_stream = self.stderr

        # default handler for display to terminal
        default_handler = TerminalHandler(self, strm=default_stream)
        if config.verbose_output:
            default_handler.setLevel(VERBOSE)
        else:
            default_handler.setLevel(INFO)
        # this handler ignores levels above INPUT
        default_handler.addFilter(MaxLevelFilter(INPUT))
        default_handler.setFormatter(
            TerminalFormatter(fmt="%(message)s%(newline)s"))
        root_logger.addHandler(default_handler)

        # handler for level STDOUT
        output_handler = TerminalHandler(self, strm=self.stdout)
        output_handler.setLevel(STDOUT)
        output_handler.addFilter(MaxLevelFilter(STDOUT))
        output_handler.setFormatter(
            TerminalFormatter(fmt="%(message)s%(newline)s"))
        root_logger.addHandler(output_handler)

        # handler for levels WARNING and higher
        warning_handler = TerminalHandler(self, strm=self.stderr)
        warning_handler.setLevel(logging.WARNING)
        warning_handler.setFormatter(
            TerminalFormatter(fmt="%(levelname)s: %(message)s%(newline)s"))
        root_logger.addHandler(warning_handler)

    def printNonColorized(self, text, targetStream):
        # We add *** after the text as a whole if anything needed to be colorized.
        lines = text.split('\n')
        for i,line in enumerate(lines):
            if i > 0:
                line = "\n" + line
            line, count = colorTagR.subn('', line)
            if count > 0:
                line += ' ***'
            targetStream.write(line.encode(self.encoding, 'replace'))

    printColorized = printNonColorized
        
    def _print(self, text, targetStream):
        if config.colorized_output:
            self.printColorized(text, targetStream)
        else:
            self.printNonColorized(text, targetStream)    

    def output(self, text, toStdout=False, targetStream=None):
        """
        If a character can't be displayed in the encoding used by the user's
        terminal, it will be replaced with a question mark or by a
        transliteration.
        
        """
        if config.transliterate:
            # Encode our unicode string in the encoding used by the user's
            # console, and decode it back to unicode. Then we can see which
            # characters can't be represented in the console encoding.
            # We need to take min(console_encoding, transliteration_target)
            # the first is what the terminal is capable of
            # the second is how unicode-y the user would like the output
            codecedText = text.encode(self.encoding,
                                      'replace').decode(self.encoding)
            if self.transliteration_target:
                codecedText = codecedText.encode(self.transliteration_target,
                                                 'replace').decode(self.transliteration_target)
            transliteratedText = ''
            # Note: A transliteration replacement might be longer than the
            # original character, e.g. ч is transliterated to ch.
            prev = "-"
            for i in xrange(len(codecedText)):
                # work on characters that couldn't be encoded, but not on
                # original question marks.
                if codecedText[i] == '?' and text[i] != u'?':
                    try:
                        transliterated = transliterator.transliterate(
                            text[i], default='?', prev=prev, next=text[i+1])
                    except IndexError:
                        transliterated = transliterator.transliterate(
                            text[i], default = '?', prev=prev, next=' ')
                    # transliteration was successful. The replacement
                    # could consist of multiple letters.
                    # mark the transliterated letters in yellow.
                    transliteratedText += '\03{lightyellow}%s\03{default}' \
                                          % transliterated
                    transLength = len(transliterated)
                    # memorize if we replaced a single letter by multiple
                    # letters.
                    if len(transliterated) > 0:
                        prev = transliterated[-1]
                else:
                    # no need to try to transliterate.
                    transliteratedText += codecedText[i]
                    prev = codecedText[i]
            text = transliteratedText
        
        if not targetStream:
            if toStdout:
                targetStream = self.stdout
            else:
                targetStream = self.stderr
            
        self._print(text, targetStream)

    def _raw_input(self):
        return raw_input()
        
    def input(self, question, password = False):
        """
        Ask the user a question and return the answer.

        Works like raw_input(), but returns a unicode string instead of ASCII.

        Unlike raw_input, this function automatically adds a space after the
        question.

        """

        # sound the terminal bell to notify the user
        if config.ring_bell:
            sys.stdout.write('\07')
        # TODO: make sure this is logged as well
        self.output(question + ' ')
        if password:
            import getpass
            text = getpass.getpass('')
        else:
            text = self._raw_input()
        text = unicode(text, self.encoding)
        return text

    def inputChoice(self, question, options, hotkeys, default=None):
        """
        Ask the user a question with a predefined list of acceptable answers.
        """
        options = options[:] # we don't want to edit the passed parameter
        for i in range(len(options)):
            option = options[i]
            hotkey = hotkeys[i]
            # try to mark a part of the option name as the hotkey
            m = re.search('[%s%s]' % (hotkey.lower(), hotkey.upper()), option)
            if hotkey == default:
                caseHotkey = hotkey.upper()
            else:
                caseHotkey = hotkey
            if m:
                pos = m.start()
                options[i] = '%s[%s]%s' % (option[:pos], caseHotkey,
                                           option[pos+1:])
            else:
                options[i] = '%s [%s]' % (option, caseHotkey)
        # loop until the user entered a valid choice
        while True:
            prompt = '%s (%s)' % (question, ', '.join(options))
            answer = self.input(prompt)
            if answer.lower() in hotkeys or answer.upper() in hotkeys:
                return answer
            elif default and answer=='':  # empty string entered
                return default

    def editText(self, text, jumpIndex=None, highlight=None):
        """Return the text as edited by the user.

        Uses a Tkinter edit box because we don't have a console editor

        Parameters:
            * text      - a Unicode string
            * jumpIndex - an integer: position at which to put the caret
            * highlight - a substring; each occurence will be highlighted

        """
        try:
            import gui
        except ImportError, e:
            print 'Could not load GUI modules: %s' % e
            return text
        editor = gui.EditBoxWindow()
        return editor.edit(text, jumpIndex=jumpIndex, highlight=highlight)

    def askForCaptcha(self, url):
        """Show the user a CAPTCHA image and return the answer."""
        try:
            import webbrowser
            wikipedia.output(u'Opening CAPTCHA in your web browser...')
            if webbrowser.open(url):
                return wikipedia.input(
                    u'What is the solution of the CAPTCHA that is shown in '
                    u'your web browser?')
            else:
                raise
        except:
            wikipedia.output(u'Error in opening web browser: %s'
                             % sys.exc_info()[0])
            wikipedia.output(
                u'Please copy this url to your web browser and open it:\n %s'
                % url)
            return wikipedia.input(
                u'What is the solution of the CAPTCHA at this url ?')

class TerminalHandler(logging.Handler):
    """A handler class that writes logging records, appropriately formatted, to
    a stream connected to a terminal. This class does not close the stream,
    as sys.stdout or sys.stderr may be (and usually will be) used.

    Slightly modified version of the StreamHandler class that ships with
    logging module, plus code for colorization of output.

    """

    # create a class-level lock that can be shared by all instances
    import threading
    sharedlock = threading.RLock()

    def __init__(self, UI, strm=None):
        """Initialize the handler.

        If strm is not specified, sys.stderr is used.

        """
        logging.Handler.__init__(self)
        # replace Handler's instance-specific lock with the shared class lock
        # to ensure that only one instance of this handler can write to
        # the console at a time
        self.lock = TerminalHandler.sharedlock
        if strm is None:
            strm = sys.stderr
        self.stream = strm
        self.formatter = None
        self.UI = UI

    def flush(self):
        """Flush the stream. """
        self.stream.flush()

    def emit(self, record):
        text = self.format(record)
        return self.UI.output(text, targetStream = self.stream)


class TerminalFormatter(logging.Formatter):
    pass


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