"""Base for terminal user interfaces."""
#
# (C) Pywikibot team, 2003-2022
#
# Distributed under the terms of the MIT license.
#
import getpass
import logging
import re
import sys
import threading
from typing import Any, Optional, Union

import pywikibot
from pywikibot import config
from pywikibot.backports import Iterable, Sequence, Tuple
from pywikibot.bot_choice import (
    ChoiceException,
    Option,
    OutputOption,
    QuitKeyboardInterrupt,
    StandardOption,
)
from pywikibot.logging import INFO, INPUT, STDOUT, VERBOSE, WARNING
from pywikibot.tools import issue_deprecation_warning
from pywikibot.tools.threading import RLock
from pywikibot.userinterfaces import transliteration
from pywikibot.userinterfaces._interface_base import ABUIC


transliterator = transliteration.transliterator(config.console_encoding)

#: Colors supported by Pywikibot
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

_color_pat = '((:?{0});?(:?{0})?)'.format('|'.join(colors + ['previous']))
old_colorTagR = re.compile(f'\03{{{_color_pat}}}')
new_colorTagR = re.compile(f'<<{_color_pat}>>')


class UI(ABUIC):

    """Base for terminal user interfaces.

    .. versionchanged:: 6.2:
       subclassed from
       :py:obj:`userinterfaces._interface_base.ABUIC`
    """

    split_col_pat = re.compile(r'(\w+);?(\w+)?')

    def __init__(self) -> None:
        """
        Initialize the UI.

        This caches the std-streams locally so any attempts to
        monkey-patch the streams later will not work.

        .. versionchanged:: 7.1
           memorize original streams
        """
        # for Windows GUI they can be None under some conditions
        self.stdin = sys.__stdin__ or sys.stdin
        self.stdout = sys.__stdout__ or sys.stdout
        self.stderr = sys.__stderr__ or sys.stderr

        self.argv = sys.argv
        self.encoding = config.console_encoding
        self.transliteration_target = config.transliteration_target
        self.cache = []
        self.lock = RLock()

    def init_handlers(
        self,
        root_logger,
        default_stream: str = 'stderr'
    ) -> None:
        """Initialize the handlers for user output.

        This method initializes handler(s) for output levels VERBOSE (if
        enabled by config.verbose_output), INFO, STDOUT, WARNING, ERROR,
        and CRITICAL. STDOUT writes its output to sys.stdout; all the
        others write theirs to sys.stderr.

        """
        if default_stream == 'stdout':
            default_stream = self.stdout
        elif default_stream == 'stderr':
            default_stream = self.stderr

        # default handler for display to terminal
        default_handler = TerminalHandler(self, stream=default_stream)
        if config.verbose_output:
            default_handler.setLevel(VERBOSE)
        else:
            default_handler.setLevel(INFO)
        # this handler ignores levels above INPUT
        default_handler.addFilter(MaxLevelFilter(INPUT))
        default_handler.setFormatter(
            logging.Formatter(fmt='%(message)s%(newline)s'))
        root_logger.addHandler(default_handler)

        # handler for level STDOUT
        output_handler = TerminalHandler(self, stream=self.stdout)
        output_handler.setLevel(STDOUT)
        output_handler.addFilter(MaxLevelFilter(STDOUT))
        output_handler.setFormatter(
            logging.Formatter(fmt='%(message)s%(newline)s'))
        root_logger.addHandler(output_handler)

        # handler for levels WARNING and higher
        warning_handler = TerminalHandler(self, stream=self.stderr)
        warning_handler.setLevel(WARNING)
        warning_handler.setFormatter(
            logging.Formatter(fmt='%(levelname)s: %(message)s%(newline)s'))
        root_logger.addHandler(warning_handler)

        warnings_logger = logging.getLogger('py.warnings')
        warnings_logger.addHandler(warning_handler)

    def encounter_color(self, color, target_stream):
        """Abstract method to handle the next color encountered."""
        raise NotImplementedError('The {} class does not support '
                                  'colors.'.format(self.__class__.__name__))

    @classmethod
    def divide_color(cls, color):
        """
        Split color label in a tuple.

        Received color is a string like 'fg_color;bg_color' or 'fg_color'.
        Returned values are (fg_color, bg_color) or (fg_color, None).

        """
        return cls.split_col_pat.search(color).groups()

    def _write(self, text: str, target_stream) -> None:
        """Write the text to the target stream.

        sys.stderr and sys.stdout are frozen upon initialization to
        original streams (which are stored in the sys module as
        `sys.__stderr__` and `sys.__stdout__`). This works fine except
        when using `redirect_stderr` or `redirect_stdout` context
        managers, where values of global `sys.stderr` and `sys.stdout`
        are temporarily changed to a redirecting `StringIO` stream, in
        which case writing to the frozen streams (which are still set to
        `sys.__stderr__` / `sys.__stdout__`) will not write to the
        redirecting stream as expected. So, we check the target stream
        against the frozen streams, and then write to the (potentially
        redirected) `sys.stderr` or `sys.stdout` stream.

        .. versionchanged:: 7.1
           instead of writing to `target_stream`, dispatch to
           `sys.stderr` or `sys.stdout`.
        """
        if target_stream == self.stderr:
            sys.stderr.write(text)
        elif target_stream == self.stdout:
            sys.stdout.write(text)
        else:  # pragma: no cover
            try:
                out, err = self.stdout.name, self.stderr.name
            except AttributeError:
                out, err = self.stdout, self.stderr
            raise OSError(
                'Target stream {} is neither stdin ({}) nor stderr ({})'
                .format(target_stream.name, out, err))

    def support_color(self, target_stream) -> bool:
        """Return whether the target stream does support colors."""
        return False

    def _print(self, text, target_stream) -> None:
        """Write the text to the target stream handling the colors."""
        colorized = (config.colorized_output
                     and self.support_color(target_stream))
        colored_line = False
        # Color tags might be cascaded, e.g. because of transliteration.
        # Therefore we need this stack.
        color_stack = ['default']
        old_parts = old_colorTagR.split(text)
        new_parts = new_colorTagR.split(text)
        if min(len(old_parts), len(new_parts)) > 1:
            raise ValueError('Old color format must not be mixed with new '
                             'color format. Found:\n'
                             + text.replace('\03', '\\03'))
        if len(old_parts) > 1:
            issue_deprecation_warning(
                'old color format variant like \03{color}',
                'new color format like <<color>>',
                since='7.3.0')
            text_parts = old_parts
        else:
            text_parts = new_parts
        text_parts += ['default']
        # match.split() includes every regex group; for each matched color
        # fg_col:b_col, fg_col and bg_col are added to the resulting list.
        len_text_parts = len(text_parts[::4])
        for index, (text, next_color) in enumerate(zip(text_parts[::4],
                                                       text_parts[1::4])):
            current_color = color_stack[-1]
            if next_color == 'previous':
                if len(color_stack) > 1:  # keep the last element in the stack
                    color_stack.pop()
                next_color = color_stack[-1]
            else:
                color_stack.append(next_color)

            if current_color != next_color:
                colored_line = True
            if colored_line and not colorized:
                if '\n' in text:  # Normal end of line
                    text = text.replace('\n', ' ***\n', 1)
                    colored_line = False
                elif index == len_text_parts - 1:  # Or end of text
                    text += ' ***'
                    colored_line = False

            # print the text up to the tag.
            self._write(text, target_stream)

            if current_color != next_color and colorized:
                # set the new color, but only if they change
                # flush first to enable color change on Windows (T283808)
                target_stream.flush()
                self.encounter_color(color_stack[-1], target_stream)

        # finally flush stream to show the text, required for Windows (T303373)
        target_stream.flush()

    def output(self, text, targetStream=None) -> None:
        """Forward text to cache and flush if output is not locked.

        All input methods locks the output to a stream but collect them
        in cache. They will be printed with next unlocked output call or
        at termination time.

        .. versionchanged:: 7.0
           Forward text to cache and flush if output is not locked.
        """
        self.cache_output(text, targetStream=targetStream)
        if not self.lock.locked():
            self.flush()

    def flush(self) -> None:
        """Output cached text.

        .. versionadded:: 7.0
        """
        with self.lock:
            for args, kwargs in self.cache:
                self.stream_output(*args, **kwargs)
            self.cache.clear()

    def cache_output(self, *args, **kwargs) -> None:
        """Put text to cache.

        .. versionadded:: 7.0
        """
        with self.lock:
            self.cache.append((args, kwargs))

    def stream_output(self, text, targetStream=None) -> None:
        """Output text to a stream.

        If a character can't be displayed in the encoding used by the user's
        terminal, it will be replaced with a question mark or by a
        transliteration.

        .. versionadded:: 7.0
           ``UI.output()`` was renamed to ``UI.stream_output()``
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
                codecedText = codecedText.encode(
                    self.transliteration_target,
                    'replace').decode(self.transliteration_target)
            transliteratedText = ''
            # Note: A transliteration replacement might be longer than the
            # original character, e.g. ч is transliterated to ch.
            prev = '-'
            for i, char in enumerate(codecedText):
                # work on characters that couldn't be encoded, but not on
                # original question marks.
                if char == '?' and text[i] != '?':
                    try:
                        transliterated = transliterator.transliterate(
                            text[i], default='?', prev=prev, next=text[i + 1])
                    except IndexError:
                        transliterated = transliterator.transliterate(
                            text[i], default='?', prev=prev, next=' ')
                    # transliteration was successful. The replacement
                    # could consist of multiple letters.
                    # mark the transliterated letters in yellow.
                    transliteratedText = ''.join((transliteratedText,
                                                  '<<lightyellow>>',
                                                  transliterated,
                                                  '<<previous>>'))
                    # memorize if we replaced a single letter by multiple
                    # letters.
                    if transliterated:
                        prev = transliterated[-1]
                else:
                    # no need to try to transliterate.
                    transliteratedText += char
                    prev = char
            text = transliteratedText

        if not targetStream:
            targetStream = self.stderr

        self._print(text, targetStream)

    def _raw_input(self):
        # May be overridden by subclass
        return input()

    def input(self, question: str,
              password: bool = False,
              default: Optional[str] = '',
              force: bool = False) -> str:
        """
        Ask the user a question and return the answer.

        Works like raw_input(), but returns a unicode string instead of ASCII.

        Unlike raw_input, this function automatically adds a colon and space
        after the question if they are not already present. Also recognises
        a trailing question mark.

        :param question: The question, without trailing whitespace.
        :param password: if True, hides the user's input (for password entry).
        :param default: The default answer if none was entered. None to require
            an answer.
        :param force: Automatically use the default
        """
        assert not password or not default

        question = question.strip()
        end_marker = question[-1]
        if end_marker in (':', '?'):
            question = question[:-1]
        else:
            end_marker = ':'

        if default:
            question += f' (default: {default})'
        question += end_marker

        # lock stream output
        with self.lock:
            if force:
                self.stream_output(question + '\n')
                return default

            # sound the terminal bell to notify the user
            if config.ring_bell:
                sys.stdout.write('\07')

            # TODO: make sure this is logged as well
            while True:
                self.stream_output(question + ' ')
                text = self._input_reraise_cntl_c(password)

                if text is None:
                    continue

                if text:
                    return text

                if default is not None:
                    return default

    def _input_reraise_cntl_c(self, password):
        """Input and decode, and re-raise Control-C."""
        try:
            if password:
                # Python 3 requires that stderr gets flushed, otherwise is the
                # message only visible after the query.
                self.stderr.flush()
                text = getpass.getpass('')
            else:
                text = self._raw_input()
        except KeyboardInterrupt:
            raise QuitKeyboardInterrupt()
        except UnicodeDecodeError:
            return None  # wrong terminal encoding, T258143
        return text

    def input_choice(self, question: str,
                     options: Union[
                         Iterable[Union[Tuple[str, str],
                                        'pywikibot.bot_choice.Option']],
                         'pywikibot.bot_choice.Option'],
                     default: Optional[str] = None,
                     return_shortcut: bool = True,
                     automatic_quit: bool = True,
                     force: bool = False) -> Any:
        """
        Ask the user and returns a value from the options.

        Depending on the options setting return_shortcut to False may not be
        sensible when the option supports multiple values as it'll return an
        ambiguous index.

        :param question: The question, without trailing whitespace.
        :param options: Iterable of all available options. Each entry contains
            the full length answer and a shortcut of only one character.
            Alternatively they may be Option (or subclass) instances or
            ChoiceException instances which have a full option and shortcut
            and will be raised if selected.
        :param default: The default answer if no was entered. None to require
            an answer.
        :param return_shortcut: Whether the shortcut or the index in the option
            should be returned.
        :param automatic_quit: Adds the option 'Quit' ('q') if True and throws
            a :py:obj:`QuitKeyboardInterrupt` if selected.
        :param force: Automatically use the default
        :return: If return_shortcut the shortcut of options or the value of
            default (if it's not None). Otherwise the index of the answer in
            options. If default is not a shortcut, it'll return -1.
        """
        def output_option(option, before_question) -> None:
            """Print an OutputOption before or after question."""
            if isinstance(option, OutputOption) \
               and option.before_question is before_question:
                self.stream_output(option.out + '\n')

        if force and default is None:
            raise ValueError('With no default option it cannot be forced')
        if isinstance(options, Option):
            options = [options]
        else:  # make a copy
            options = list(options)
        if not options:
            raise ValueError('No options are given.')
        if automatic_quit:
            options += [QuitKeyboardInterrupt()]
        if default:
            default = default.lower()
        for i, option in enumerate(options):
            if not isinstance(option, Option):
                if len(option) != 2:
                    raise ValueError('Option #{} does not consist of an '
                                     'option and shortcut.'.format(i))
                options[i] = StandardOption(*option)
            # TODO: Test for uniquity

        handled = False

        # lock stream output
        with self.lock:
            while not handled:
                for option in options:
                    output_option(option, before_question=True)
                output = Option.formatted(question, options, default)
                if force:
                    self.stream_output(output + '\n')
                    answer = default
                else:
                    answer = self.input(output) or default
                # something entered or default is defined
                if answer:
                    for index, option in enumerate(options):
                        if option.handled(answer):
                            answer = option.result(answer)
                            output_option(option, before_question=False)
                            handled = option.stop
                            break

        if isinstance(answer, ChoiceException):
            raise answer
        if not return_shortcut:
            return index
        return answer

    def input_list_choice(self, question: str, answers: Sequence[Any],
                          default: Union[int, str, None] = None,
                          force: bool = False) -> Any:
        """Ask the user to select one entry from a list of entries.

        :param question: The question, without trailing whitespace.
        :param answers: A sequence of options to be choosen.
        :param default: The default answer if no was entered. None to require
            an answer.
        :param force: Automatically use the default.
        :return: Return a single Sequence entry.
        """
        # lock stream output
        with self.lock:
            if not force:
                line_template = '{{0: >{}}}: {{1}}\n'.format(
                    len(str(len(answers))))
                for i, entry in enumerate(answers, start=1):
                    self.stream_output(line_template.format(i, entry))

            while True:
                choice = self.input(question, default=default, force=force)

                try:
                    choice = int(choice) - 1
                except (TypeError, ValueError):
                    if choice in answers:
                        return choice
                    choice = -1

                # User typed choice number
                if 0 <= choice < len(answers):
                    return answers[choice]

                if force:
                    raise ValueError(
                        'Invalid value "{}" for default during force.'
                        .format(default))

                self.stream_output('Error: Invalid response\n')

    @staticmethod
    def editText(text: str,
                 jumpIndex: Optional[int] = None,
                 highlight: Optional[str] = None) -> Optional[str]:
        """Return the text as edited by the user.

        Uses a Tkinter edit box because we don't have a console editor

        :param text: the text to be edited
        :param jumpIndex: position at which to put the caret
        :param highlight: each occurrence of this substring will be highlighted
        :return: the modified text, or None if the user didn't save the text
            file in his text editor
        """
        try:
            from pywikibot.userinterfaces import gui
        except ImportError as e:
            pywikibot.warning(f'Could not load GUI modules: {e}')
            return text
        editor = gui.EditBoxWindow()
        return editor.edit(text, jumpIndex=jumpIndex, highlight=highlight)


class TerminalHandler(logging.StreamHandler):

    """A handler class that writes logging records to a terminal.

    This class does not close the stream, as sys.stdout or sys.stderr
    may be (and usually will be) used.

    Slightly modified version of the StreamHandler class that ships with
    logging module, plus code for colorization of output.
    """

    # create a class-level lock that can be shared by all instances
    sharedlock = threading.RLock()

    def __init__(self, UI, stream=None) -> None:
        """Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        super().__init__(stream=stream)
        self.UI = UI

    def createLock(self) -> None:
        """Acquire a thread lock for serializing access to the underlying I/O.

        Replace Handler's instance-specific lock with the shared
        class lock to ensure that only one instance of this handler can
        write to the console at a time.
        """
        self.lock = TerminalHandler.sharedlock

    def emit(self, record) -> None:
        """Emit the record formatted to the output."""
        self.flush()
        if record.name == 'py.warnings':
            # Each warning appears twice
            # the second time it has a 'message'
            if 'message' in record.__dict__:
                return

            record.__dict__.setdefault('newline', '\n')

        msg = self.format(record)
        self.UI.output(msg, targetStream=self.stream)


class MaxLevelFilter(logging.Filter):

    """Filter that only passes records at or below a specific level.

    (setting handler level only passes records at or *above* a specified level,
    so this provides the opposite functionality)

    """

    def __init__(self, level=None) -> None:
        """Initializer."""
        self.level = level

    def filter(self, record):
        """Return true if the level is below or equal to the set level."""
        if self.level:
            return record.levelno <= self.level
        return True
