# -*- coding: utf-8 -*-
"""Choices for input_choice."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import pywikibot


class Option(object):

    """
    A basic option for input_choice.

    The following methods need to be implemented:
    * format(default)
    * result(value)
    * test(value)

    The methods C{test} and C{handled} are in such a relationship that when
    C{handled} returns itself that C{test} must return True for that value. So
    if C{test} returns False C{handled} may not return itself but it may return
    not None.

    Also C{result} only returns a sensible value when C{test} returns True for
    the same value.
    """

    def __init__(self, stop=True):
        """Constructor."""
        super(Option, self).__init__()
        self._stop = stop

    @staticmethod
    def formatted(text, options, default):
        """Create a text with the options formatted into it."""
        formatted_options = []
        for option in options:
            formatted_options.append(option.format(default))
        return '{0} ({1})'.format(text, ', '.join(formatted_options))

    @property
    def stop(self):
        """Return whether this option stops asking."""
        return self._stop

    def handled(self, value):
        """
        Return the Option object that applies to the given value.

        If this Option object doesn't know which applies it returns None.
        """
        if self.test(value):
            return self
        else:
            return None

    def format(self, default):
        """Return a formatted string for that option."""
        raise NotImplementedError()

    def result(self, value):
        """Return the actual value which is associated by the given one."""
        raise NotImplementedError()

    def test(self, value):
        """Return True whether this option applies."""
        raise NotImplementedError()


class OutputOption(Option):

    """An option that never stops and can output on each question."""

    before_question = False

    @property
    def stop(self):
        """Never stop asking."""
        return False

    def result(self, value):
        """Just output the value."""
        self.output()

    def output(self):
        """Output a string when selected and possibily before the question."""
        raise NotImplementedError()


class StandardOption(Option):

    """An option with a description and shortcut and returning the shortcut."""

    def __init__(self, option, shortcut, stop=True):
        """Constructor."""
        super(StandardOption, self).__init__(stop)
        self.option = option
        self.shortcut = shortcut.lower()

    def format(self, default):
        """Return a formatted string for that option."""
        index = self.option.lower().find(self.shortcut)
        shortcut = self.shortcut
        if self.shortcut == default:
            shortcut = self.shortcut.upper()
        if index >= 0:
            return '{0}[{1}]{2}'.format(self.option[:index], shortcut,
                                         self.option[index + len(self.shortcut):])
        else:
            return '{0} [{1}]'.format(self.option, shortcut)

    def result(self, value):
        """Return the lowercased shortcut."""
        return self.shortcut

    def test(self, value):
        """Return True whether this option applies."""
        return (self.shortcut.lower() == value.lower() or
                self.option.lower() == value.lower())


class NestedOption(OutputOption, StandardOption):

    """
    An option containing other options.

    It will return True in test if this option applies but False if a sub
    option applies while handle returns the sub option.
    """

    def __init__(self, option, shortcut, description, options):
        """Constructor."""
        super(NestedOption, self).__init__(option, shortcut, False)
        self.description = description
        self.options = options

    def format(self, default):
        """Return a formatted string for that option."""
        self._output = Option.formatted(self.description, self.options, default)
        return super(NestedOption, self).format(default)

    def handled(self, value):
        """Return itself if it applies or the appling sub option."""
        for option in self.options:
            handled = option.handled(value)
            if handled is not None:
                return handled
        else:
            return super(NestedOption, self).handled(value)

    def output(self):
        """Output the suboptions."""
        pywikibot.output(self._output)


class IntegerOption(Option):

    """An option allowing a range of integers."""

    def __init__(self, minimum=1, maximum=None, prefix=''):
        """Constructor."""
        super(IntegerOption, self).__init__()
        if minimum is not None and maximum is not None and minimum >= maximum:
            raise ValueError('The minimum must be lower than the maximum.')
        self.minimum = minimum
        self.maximum = maximum
        self.prefix = prefix

    def test(self, value):
        """Return whether the value is an int and in the specified range."""
        if not value.lower().startswith(self.prefix.lower()):
            return False
        try:
            value = self.parse(value)
        except ValueError:
            return False
        else:
            return ((self.minimum is None or value >= self.minimum) and
                    (self.maximum is None or value <= self.maximum))

    def format(self, default):
        """Return a formatted string showing the range."""
        if self.minimum is not None or self.maximum is not None:
            _min = '' if self.minimum is None else str(self.minimum)
            _max = '' if self.maximum is None else str(self.maximum)
            rng = _min + '-' + _max
        else:
            rng = 'any'
        return self.prefix + '<number> [' + rng + ']'

    def parse(self, value):
        """Return integer from value with prefix removed."""
        if value.lower().startswith(self.prefix.lower()):
            return int(value[len(self.prefix):])
        else:
            raise ValueError('Value does not start with prefix')

    def result(self, value):
        """Return the value converted into int."""
        return (self.prefix, self.parse(value))


class ContextOption(OutputOption, StandardOption):

    """An option to show more and more context."""

    def __init__(self, option, shortcut, text, context, delta=100, start=0, end=0):
        """Constructor."""
        super(ContextOption, self).__init__(option, shortcut, False)
        self.text = text
        self.context = context
        self.delta = delta
        self.start = start
        self.end = end

    def result(self, value):
        """Add the delta to the context and output it."""
        self.context += self.delta
        super(ContextOption, self).result(value)

    def output(self):
        """Output the context."""
        start = max(0, self.start - self.context)
        end = min(len(self.text), self.end + self.context)
        self.output_range(start, end)

    def output_range(self, start_context, end_context):
        """Output a section from the text."""
        pywikibot.output(self.text[start_context:end_context])


class ListOption(Option):

    """An option to select something from a list."""

    def __init__(self, sequence, prefix):
        """Constructor."""
        super(ListOption, self).__init__()
        self._list = sequence
        self._prefix = prefix

    def format(self, default):
        """Return a string showing the range."""
        return '<number> [0-{0}]'.format(len(self._list) - 1)

    def test(self, value):
        """Test if the value is an int and in range."""
        try:
            value = int(value)
        except ValueError:
            return False
        else:
            return 0 <= value < len(self._list)

    def result(self, value):
        """Return a tuple with the prefix and selected value."""
        return (self._prefix, self._list[int(value)])


class HighlightContextOption(ContextOption):

    """Show the original region highlighted."""

    def output_range(self, start, end):
        """Show normal context with a red center region."""
        pywikibot.output(self.text[start:self.start] + '\03{lightred}' +
                         self.text[self.start:self.end] + '\03{default}' +
                         self.text[self.end:end])


class ChoiceException(StandardOption, Exception):

    """A choice for input_choice which result in this exception."""

    def result(self, value):
        """Return itself to raise the exception."""
        return self


class QuitKeyboardInterrupt(ChoiceException, KeyboardInterrupt):

    """The user has cancelled processing at a prompt."""

    def __init__(self):
        """Constructor using the 'quit' ('q') in input_choice."""
        super(QuitKeyboardInterrupt, self).__init__('quit', 'q')
