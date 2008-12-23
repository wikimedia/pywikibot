# -*- coding: utf-8 -*-
#
# (C) Pywikipedia bot team, 2003-2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


import traceback, re, sys
import logging
import pywikibot
from pywikibot import config
from pywikibot.userinterfaces import transliteration


try:
    import ctypes
    ctypes_found = True
except ImportError:
    ctypes_found = False


def getDefaultTextColorInWindows():
    """
    This method determines the default text color and saves its color
    code inside the variable windowsColors['default'].

    Based on MIT-licensed code by Andre Burgaud published at
    http://starship.python.net/crew/theller/wiki/ColorConsole
    """
    if sys.platform != 'win32' or not ctypes_found:
        return -1
    SHORT = ctypes.c_short
    WORD = ctypes.c_ushort

    # wincon.h
    class COORD(ctypes.Structure):
        _fields_ = [
            ("X", SHORT),
            ("Y", SHORT)
        ]

    class SMALL_RECT(ctypes.Structure):
        _fields_ = [
            ("Left", SHORT),
            ("Top", SHORT),
            ("Right", SHORT),
            ("Bottom", SHORT)
        ]

    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", WORD),
            ("srWindow", SMALL_RECT),
            ("dwMaximumWindowSize", COORD)
        ]

    std_out_handle = ctypes.windll.kernel32.GetStdHandle(-11)
    csbi = CONSOLE_SCREEN_BUFFER_INFO()
    ctypes.windll.kernel32.GetConsoleScreenBufferInfo(std_out_handle, ctypes.byref(csbi))
    return (csbi.wAttributes & 0x000f)

# TODO: other colors:
         #0 = Black
         #1 = Blue
         #2 = Green
         #3 = Aqua
         #4 = Red
         #5 = Purple
         #6 = Yellow
         #7 = White
         #8 = Gray
         #9 = Light Blue
        #10 = Light Green
        #11 = Light Aqua
        #12 = Light Red
        #13 = Light Purple
        #14 = Light Yellow
        #15 = Bright White

unixColors = {
    'default':     chr(27) + '[0m',     # Unix end tag to switch back to default
    'lightblue':   chr(27) + '[94;1m',  # Light Blue start tag
    'lightgreen':  chr(27) + '[92;1m',  # Light Green start tag
    'lightaqua':   chr(27) + '[36;1m',  # Light Aqua start tag
    'lightred':    chr(27) + '[91;1m',  # Light Red start tag
    'lightpurple': chr(27) + '[35;1m',  # Light Purple start tag
    'lightyellow': chr(27) + '[33;1m',  # Light Yellow start tag
}

windowsColors = {
    'default':     7,
    'black':       0,
    'blue':        1,
    'green':       2,
    'aqua':        3,
    'red':         4,
    'purple':      5,
    'yellow':      6,
    'lightgray':   7,
    'gray':        8,
    'lightblue':   9,
    'lightgreen':  10,
    'lightaqua':   11,
    'lightred':    12,
    'lightpurple': 13,
    'lightyellow': 14,
    'white':       15,
}

colorTagR = re.compile('\03{(?P<name>%s)}' % '|'.join(windowsColors.keys()))

class UI:
    def __init__(self):
        pass

    def printColorizedInUnix(self, text, level):
        lastColor = None
        for key, value in unixColors.iteritems():
            text = text.replace('\03{%s}' % key, value)
        # just to be sure, reset the color
        text += unixColors['default']
        logging.log(level, text)

    def printColorizedInWindows(self, text, level):
        """
        This only works in Python 2.5 or higher.
        """
        if ctypes_found:
            std_out_handle = ctypes.windll.kernel32.GetStdHandle(-11)
            # Color tags might be cascaded, e.g. because of transliteration.
            # Therefore we need this stack.
            colorStack = []
            tagM = True
            while tagM:
                tagM = colorTagR.search(text)
                if tagM:
                    # print the text up to the tag.
                    logging.log(level, text[:tagM.start()])
                    newColor = tagM.group('name')
                    if newColor == 'default':
                        if len(colorStack) > 0:
                            colorStack.pop()
                            if len(colorStack) > 0:
                                lastColor = colorStack[-1]
                            else:
                                lastColor = 'default'
                            ctypes.windll.kernel32.SetConsoleTextAttribute(std_out_handle, windowsColors[lastColor])
                    else:
                        colorStack.append(newColor)
                        # set the new color
                        ctypes.windll.kernel32.SetConsoleTextAttribute(std_out_handle, windowsColors[newColor])
                    text = text[tagM.end():]
            # print the rest of the text
            logging.log(level, text)
            # just to be sure, reset the color
            ctypes.windll.kernel32.SetConsoleTextAttribute(std_out_handle, windowsColors['default'])
        else:
            # ctypes is only available since Python 2.5, and we won't
            # try to colorize without it. Instead we add *** after the text as a whole
            # if anything needed to be colorized.
            lines = text.split('\n')
            for line in lines:
                line, count = colorTagR.subn('', line)
                if count > 0:
                    line += '***'
                line += '\n'
                logging.log(level, line)

    def printColorized(self, text, level):
        if config.colorized_output:
            if sys.platform == 'win32':
                self.printColorizedInWindows(text, level)
            else:
                self.printColorizedInUnix(text, level)
        else:
            logging.log(level, text)

    def output(self, text, level=logging.INFO):
        """
        If a character can't be displayed in the encoding used by the user's
        terminal, it will be replaced with a question mark or by a
        transliteration.
        """
        if config.transliterate:
            # Encode our unicode string in the encoding used by the user's console,
            # and decode it back to unicode. Then we can see which characters
            # can't be represented in the console encoding.
            codecedText = text.encode(config.console_encoding, 'replace').decode(config.console_encoding)
            transliteratedText = ''
            # Note: A transliteration replacement might be longer than the original
            # character, e.g. ч is transliterated to ch.
            prev = "-"
            for i in xrange(len(codecedText)):
                # work on characters that couldn't be encoded, but not on
                # original question marks.
                if codecedText[i] == '?' and text[i] != u'?':
                    try:
                        transliterated = transliteration.trans(text[i], default = '?', prev = prev, next = text[i+1])
                    except IndexError:
                        transliterated = transliteration.trans(text[i], default = '?', prev = prev, next = ' ')
                    # transliteration was successful. The replacement
                    # could consist of multiple letters.
                    # mark the transliterated letters in yellow.
                    transliteratedText += '\03{lightyellow}%s\03{default}' % transliterated
                    transLength = len(transliterated)
                    # memorize if we replaced a single letter by multiple letters.
                    if len(transliterated) > 0:
                        prev = transliterated[-1]
                else:
                    # no need to try to transliterate.
                    transliteratedText += codecedText[i]
                    prev = codecedText[i]
            text = transliteratedText

        self.printColorized(text, level)

    def input(self, question, password = False):
        """
        Works like raw_input(), but returns a unicode string instead of ASCII.

        Unlike raw_input, this function automatically adds a space after the
        question.
        """

        # sound the terminal bell to notify the user
        if config.ring_bell:
            sys.stdout.write('\07')
        self.output(question + ' ', level=pywikibot.INPUT)
        if password:
            import getpass
            text = getpass.getpass('')
        else:
            text = raw_input()
        text = unicode(text, config.console_encoding)
        return text

    def inputChoice(self, question, options, hotkeys, default=None):
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
                options[i] = '%s[%s]%s' % (option[:pos], caseHotkey, option[pos+1:])
            else:
                options[i] = '%s [%s]' % (option, caseHotkey)
        # loop until the user entered a valid choice
        while True:
            prompt = '%s (%s)' % (question, ', '.join(options))
            answer = self.input(prompt)
            if answer.lower() in hotkeys or answer.upper() in hotkeys:
                return answer
            elif default and answer=='':		# empty string entered
                return default

    def editText(self, text, jumpIndex = None, highlight = None):
        """
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
        try:
            import webbrowser
            wikipedia.output(u'Opening CAPTCHA in your web browser...')
            webbrowser.open(url)
            return wikipedia.input(u'What is the solution of the CAPTCHA that is shown in your web browser?')
        except:
            wikipedia.output(u'Error in opening web browser: %s' % sys.exc_info()[0])
            return wikipedia.input(u'What is the solution of the CAPTCHA at %s ?' % url)
