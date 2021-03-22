"""Choices for input_choice."""
#
# (C) Pywikibot team, 2015-2021
#
# Distributed under the terms of the MIT license.
#
import re

from abc import ABC, abstractmethod
from textwrap import fill
from typing import Optional

import pywikibot

from pywikibot.tools import (
    deprecated,
    deprecated_args,
    issue_deprecation_warning,
)


class Option(ABC):

    """
    A basic option for input_choice.

    The following methods need to be implemented:
    * format(default=None)
    * result(value)
    * test(value)

    The methods ``test`` and ``handled`` are in such a relationship that
    when ``handled`` returns itself that ``test`` must return True for
    that value. So if ``test`` returns False ``handled`` may not return
    itself but it may return not None.

    Also ``result`` only returns a sensible value when ``test`` returns
    True for the same value.
    """

    def __init__(self, stop=True) -> None:
        """Initializer."""
        self._stop = stop

    @staticmethod
    def formatted(text: str, options, default=None) -> str:
        """
        Create a text with the options formatted into it.

        :param text: Text into which options are to be formatted
        :param options: Option instances to be formatted
        :type options: Iterable
        :return: Text with the options formatted into it
        """
        formatted_options = []
        for option in options:
            formatted_options.append(option.format(default=default))
        # remove color highlights before fill function
        text = '{} ({})'.format(text, ', '.join(formatted_options))
        pattern = '\03{[a-z]+}'
        highlights = re.findall(pattern, text)
        return fill(re.sub(pattern, '{}', text), width=77).format(*highlights)

    @property
    def stop(self) -> bool:
        """Return whether this option stops asking."""
        return self._stop

    def handled(self, value):
        """
        Return the Option object that applies to the given value.

        If this Option object doesn't know which applies it returns None.
        """
        if self.test(value):
            return self
        return None

    def format(self, default=None):
        """Return a formatted string for that option."""
        raise NotImplementedError()

    def test(self, value):
        """Return True whether this option applies."""
        raise NotImplementedError()

    @abstractmethod
    def result(self, value):
        """Return the actual value which is associated by the given one.

        *New in version 6.2:* *result()* is an abstract method and must
        be defined in subclasses
        """
        raise NotImplementedError()


class OutputOption(Option):

    """An option that never stops and can output on each question.

    :Note: OutputOption must have a an "out" property which returns a
        string for output method.
    """

    before_question = False

    @property
    def stop(self):
        """Never stop asking."""
        return False

    def result(self, value):
        """Just return None."""
        return None

    @property
    def out(self) -> str:
        """String to be used when selected and possibly before the question.

        :Note: This method is used by ui.input_choice instead of output().

        *New in version 6.2.*
        """
        return ''

    def output(self):
        """Output string when selected and possibly before the question.

        :Note: This method should never be overridden.
        """
        pywikibot.output(self.out)


class StandardOption(Option):

    """An option with a description and shortcut and returning the shortcut."""

    def __init__(self, option: str, shortcut: str, **kwargs):
        """
        Initializer.

        :param option: option string
        :param shortcut: Shortcut of the option
        """
        super().__init__(**kwargs)
        self.option = option
        self.shortcut = shortcut.lower()

    def format(self, default=None) -> str:
        """Return a formatted string for that option."""
        index = self.option.lower().find(self.shortcut)
        shortcut = self.shortcut
        if self.shortcut == default:
            shortcut = self.shortcut.upper()
        if index >= 0:
            return '{}[{}]{}'.format(
                self.option[:index], shortcut,
                self.option[index + len(self.shortcut):])
        return '{} [{}]'.format(self.option, shortcut)

    def result(self, value):
        """Return the lowercased shortcut."""
        return self.shortcut

    def test(self, value) -> bool:
        """Return True whether this option applies."""
        return (self.shortcut.lower() == value.lower()
                or self.option.lower() == value.lower())


class OutputProxyOption(OutputOption, StandardOption):

    """An option which calls out property of the given output class."""

    def __init__(self, option, shortcut, output, **kwargs):
        """Create a new option for the given sequence."""
        super().__init__(option, shortcut, **kwargs)
        self._outputter = output

    @property
    def out(self) -> str:
        """Return te contents."""
        if not hasattr(self._outputter, 'out'):
            issue_deprecation_warning('{} without "out" property'
                                      .format(self.__class__.__name__),
                                      warning_class=FutureWarning,
                                      since='6.2.0')
            return self._outputter.output()
        return self._outputter.out


class NestedOption(OutputOption, StandardOption):

    """
    An option containing other options.

    It will return True in test if this option applies but False if a sub
    option applies while handle returns the sub option.
    """

    def __init__(self, option, shortcut, description, options):
        """Initializer."""
        super().__init__(option, shortcut, stop=False)
        self.description = description
        self.options = options

    def format(self, default=None):
        """Return a formatted string for that option."""
        self._output = Option.formatted(self.description, self.options)
        return super().format(default=default)

    def handled(self, value):
        """Return itself if it applies or the applying sub option."""
        for option in self.options:
            handled = option.handled(value)
            if handled is not None:
                return handled

        return super().handled(value)

    @property
    def out(self):
        """Output of suboptions."""
        return self._output


class ContextOption(OutputOption, StandardOption):

    """An option to show more and more context."""

    def __init__(
        self, option, shortcut, text, context, delta=100, start=0, end=0
    ):
        """Initializer."""
        super().__init__(option, shortcut, stop=False)
        self.text = text
        self.context = context
        self.delta = delta
        self.start = start
        self.end = end

    def result(self, value):
        """Add the delta to the context and output it."""
        self.context += self.delta
        super().result(value)

    @property
    def out(self):
        """Output section of the text."""
        start = max(0, self.start - self.context)
        end = min(len(self.text), self.end + self.context)
        return self.text[start:end]

    @deprecated_args(start_context='start', end_context='end')
    @deprecated('pywikibot.output(ContextOption.out)', since='6.2.0',
                future_warning=True)
    def output_range(self, start, end):
        """DEPRECATED. Output a section from the text."""
        pywikibot.output(self.text[start:end])


class Choice(StandardOption):

    """A simple choice consisting of an option, shortcut and handler."""

    def __init__(self, option, shortcut, replacer):
        """Initializer."""
        super().__init__(option, shortcut)
        self._replacer = replacer

    @property
    def replacer(self):
        """The replacer."""
        return self._replacer

    @abstractmethod
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
        super().__init__(option, shortcut, None)
        self._result = result

    def handle(self):
        """Return the predefined value."""
        return self._result


class LinkChoice(Choice):

    """A choice returning a mix of the link new and current link."""

    def __init__(self, option, shortcut, replacer, replace_section,
                 replace_label):
        """Initializer."""
        super().__init__(option, shortcut, replacer)
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
                    kwargs['label'] += '#' \
                        + self.replacer.current_groups['section']
            else:
                kwargs['label'] = self.replacer.current_link.anchor
        return pywikibot.Link.create_separated(
            self.replacer._new.canonical_title(), self.replacer._new.site,
            **kwargs)


class AlwaysChoice(Choice):

    """Add an option to always apply the default."""

    def __init__(self, replacer, option='always', shortcut='a'):
        """Initializer."""
        super().__init__(option, shortcut, replacer)
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


class IntegerOption(Option):

    """An option allowing a range of integers."""

    def __init__(self, minimum=1, maximum=None, prefix='', **kwargs):
        """Initializer."""
        super().__init__(**kwargs)
        if not ((minimum is None or isinstance(minimum, int))
                and (maximum is None or isinstance(maximum, int))):
            raise ValueError(
                'The minimum and maximum parameters must be int or None.')
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError('The minimum must be lower than the maximum.')
        self._min = minimum
        self._max = maximum
        self.prefix = prefix

    def test(self, value) -> bool:
        """Return whether the value is an int and in the specified range."""
        try:
            value = self.parse(value)
        except ValueError:
            return False

        return ((self.minimum is None or value >= self.minimum)
                and (self.maximum is None or value <= self.maximum))

    @property
    def minimum(self):
        """Return the lower bound of the range of allowed values."""
        return self._min

    @property
    def maximum(self):
        """Return the upper bound of the range of allowed values."""
        return self._max

    def format(self, default=None) -> str:
        """Return a formatted string showing the range."""
        if default is not None and self.test(default):
            value = self.parse(default)
            default = '[{}]'.format(value)
        else:
            value = None
            default = ''
        if self.minimum is not None or self.maximum is not None:
            if default and value == self.minimum:
                minimum = default
                default = ''
            else:
                minimum = '' if self.minimum is None else str(self.minimum)
            if default and value == self.maximum:
                maximum = default
                default = ''
            else:
                maximum = '' if self.maximum is None else str(self.maximum)
            default = '-{}-'.format(default) if default else '-'
            if self.minimum == self.maximum:
                rng = minimum
            else:
                rng = minimum + default + maximum
        else:
            rng = 'any' + default
        return '{}<number> [{}]'.format(self.prefix, rng)

    def parse(self, value) -> int:
        """Return integer from value with prefix removed."""
        if value.lower().startswith(self.prefix.lower()):
            return int(value[len(self.prefix):])
        raise ValueError('Value does not start with prefix')

    def result(self, value):
        """Return the value converted into int."""
        return self.prefix, self.parse(value)


class ListOption(IntegerOption):

    """An option to select something from a list."""

    def __init__(self, sequence, prefix='', **kwargs):
        """Initializer."""
        self._list = sequence
        try:
            super().__init__(1, self.maximum, prefix, **kwargs)
        except ValueError:
            raise ValueError('The sequence is empty.')
        del self._max

    def format(self, default=None):
        """Return a string showing the range."""
        if not self._list:
            raise ValueError('The sequence is empty.')

        return super().format(default=default)

    @property
    def maximum(self) -> int:
        """Return the maximum value."""
        return len(self._list)

    def result(self, value):
        """Return a tuple with the prefix and selected value."""
        return self.prefix, self._list[self.parse(value) - 1]


class ShowingListOption(ListOption, OutputOption):

    """An option to show a list and select an item.

    *New in version 3.0.*
    """

    before_question = True

    def __init__(self, sequence, prefix='', pre: Optional[str] = None,
                 post: Optional[str] = None, **kwargs):
        """Initializer.

        :param pre: Additional comment printed before the list.
        :param post: Additional comment printed after the list.
        """
        super().__init__(sequence, prefix, **kwargs)
        self.pre = pre
        self.post = post

    @property
    def stop(self):
        """Return whether this option stops asking."""
        return self._stop

    @property
    def out(self):
        """Output text of the enumerated list."""
        text = ''
        if self.pre is not None:
            text = self.pre + '\n'
        width = len(str(self.maximum))
        for i, item in enumerate(self._list, self.minimum):
            text += '{:>{width}} - {}\n'.format(i, item, width=width)
        if self.post is not None:
            text += self.post + '\n'
        return text


class MultipleChoiceList(ListOption):

    """An option to select multiple items from a list.

    *New in version 3.0.*
    """

    def test(self, value) -> bool:
        """Return whether the values are int and in the specified range."""
        try:
            values = [self.parse(val) for val in value.split(',')]
        except ValueError:
            return False

        for val in values:
            if self.minimum is not None and val < self.minimum:
                break
            if self.maximum is not None and val > self.maximum:
                break
        else:
            return True

        return False

    def result(self, value):
        """Return a tuple with the prefix and selected values as a list."""
        values = (self.parse(val) for val in value.split(','))
        result = [self._list[val - 1] for val in values]
        return self.prefix, result


class ShowingMultipleChoiceList(ShowingListOption, MultipleChoiceList):

    """An option to show a list and select multiple items.

    *New in version 3.0.*
    """


class HighlightContextOption(ContextOption):

    """Show the original region highlighted."""

    color = 'lightred'

    @property
    def out(self):
        """Highlighted output section of the text."""
        start = max(0, self.start - self.context)
        end = min(len(self.text), self.end + self.context)
        color_format = pywikibot.tools.formatter.color_format
        return color_format('{}{%(color)s}{}{default}{}'
                            % {'color': self.color},
                            self.text[start:self.start],
                            self.text[self.start:self.end],
                            self.text[self.end:end])

    @deprecated('pywikibot.output(HighlightContextOption.out)',
                since='6.2.0', future_warning=True)
    def output_range(self, start, end):
        """DEPRECATED. Show normal context with a highlighted center region."""
        color_format = pywikibot.tools.formatter.color_format
        text = color_format('{}{%(color)s}{}{default}{}'
                            % {'color': self.color},
                            self.text[start:self.start],
                            self.text[self.start:self.end],
                            self.text[self.end:end])
        pywikibot.output(text)


class UnhandledAnswer(Exception):

    """The given answer didn't suffice."""

    def __int__(self, stop=False):
        """Initializer."""
        self.stop = stop


class ChoiceException(StandardOption, Exception):

    """A choice for input_choice which result in this exception."""

    def result(self, value):
        """Return itself to raise the exception."""
        return self


class QuitKeyboardInterrupt(ChoiceException, KeyboardInterrupt):

    """The user has cancelled processing at a prompt."""

    def __init__(self):
        """Constructor using the 'quit' ('q') in input_choice."""
        super().__init__('quit', 'q')
