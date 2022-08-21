"""Options and Choices for :py:meth:`pywikibot.input_choice`."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import re
from abc import ABC, abstractmethod
from textwrap import fill
from typing import Any, Optional

import pywikibot
from pywikibot.backports import Iterable, Sequence
from pywikibot.tools import deprecated, issue_deprecation_warning


class Option(ABC):

    """
    A basic option for input_choice.

    The following methods need to be implemented:

    - format(default=None)
    - result(value)
    - test(value)

    The methods ``test`` and ``handled`` are in such a relationship that
    when ``handled`` returns itself that ``test`` must return True for
    that value. So if ``test`` returns False ``handled`` may not return
    itself but it may return not None.

    Also ``result`` only returns a sensible value when ``test`` returns
    True for the same value.
    """

    def __init__(self, stop: bool = True) -> None:
        """Initializer."""
        self._stop = stop

    @staticmethod
    def formatted(text: str, options: Iterable['Option'],
                  default: Optional[str] = None) -> str:
        """
        Create a text with the options formatted into it.

        This static method is used by :py:meth:`pywikibot.input_choice`.
        It calls :py:obj:`format` for all *options* to combine the
        question for :py:meth:`pywikibot.input`.

        :param text: Text into which options are to be formatted
        :param options: Option instances to be formatted
        :param default: filler for any option's 'default' placeholder

        :return: Text with the options formatted into it
        """
        formatted_options = []
        for option in options:
            formatted_options.append(option.format(default=default))
        # remove color highlights before fill function
        text = '{} ({})'.format(text, ', '.join(formatted_options))
        pattern = '<<[a-z]+>>'
        highlights = re.findall(pattern, text)
        return fill(re.sub(pattern, '{}', text), width=77).format(*highlights)

    @property
    def stop(self) -> bool:
        """Return whether this option stops asking."""
        return self._stop

    def handled(self, value: str) -> Optional['Option']:
        """
        Return the Option object that applies to the given value.

        If this Option object doesn't know which applies it returns None.
        """
        return self if self.test(value) else None

    def format(self, default: Optional[str] = None) -> str:
        """Return a formatted string for that option."""
        raise NotImplementedError()

    def test(self, value: str) -> bool:
        """Return True whether this option applies."""
        raise NotImplementedError()

    @abstractmethod
    def result(self, value: str) -> Any:
        """Return the actual value which is associated by the given one.

        .. versionadded:: 6.2
           *result()* is an abstract method and must be defined in
           subclasses
        """
        raise NotImplementedError()


class OutputOption(Option):

    """An option that never stops and can output on each question.

    :py:meth:`pywikibot.input_choice` uses before_question attribute to
    decide whether to output before or after the question.

    .. note:: OutputOption must have an :py:obj:`out` property which
       returns a string for
       :py:meth:`userinterface output()
       <userinterfaces._interface_base.ABUIC.output>`
       method.
    """

    #: Place output before or after the question
    before_question = False  # type: bool

    @property
    def stop(self) -> bool:
        """Never stop asking."""
        return False

    def result(self, value: str) -> Any:
        """Just return None."""
        return None

    @property
    def out(self) -> str:
        """String to be used when selected before or after the question.

        .. note:: This method is used by :meth:`ui.input_choice
           <userinterfaces._interface_base.ABUIC.input_choice>`
           instead of deprecated :meth:`output`.

        .. versionadded:: 6.2
        """
        return ''

    @deprecated('pywikibot.output(OutputOption.out)', since='6.5')
    def output(self) -> None:
        """Output string.

        .. deprecated:: 6.5
           This method was replaced by :attr:`out` property and is no
           no longer used by the
           :py:mod:`userinterfaces <pywikibot.userinterfaces>` system.
        """
        pywikibot.output(self.out)


class StandardOption(Option):

    """An option with a description and shortcut and returning the shortcut."""

    def __init__(self, option: str, shortcut: str, **kwargs: Any) -> None:
        """
        Initializer.

        :param option: option string
        :param shortcut: Shortcut of the option
        """
        super().__init__(**kwargs)
        self.option = option
        self.shortcut = shortcut.lower()

    def format(self, default: Optional[str] = None) -> str:
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

    def result(self, value: str) -> Any:
        """Return the lowercased shortcut."""
        return self.shortcut

    def test(self, value: str) -> bool:
        """Return True whether this option applies."""
        return (self.shortcut.lower() == value.lower()
                or self.option.lower() == value.lower())


class OutputProxyOption(OutputOption, StandardOption):

    """An option which calls out property of the given output class."""

    def __init__(self, option: str, shortcut: str, output: OutputOption,
                 **kwargs: Any) -> None:
        """Create a new option for the given sequence."""
        super().__init__(option, shortcut, **kwargs)
        self._outputter = output

    @property
    def out(self) -> str:
        """Return the contents."""
        if not hasattr(self._outputter, 'out'):  # pragma: no cover
            issue_deprecation_warning('{} without "out" property'
                                      .format(self.__class__.__name__),
                                      since='6.2.0')
            self._outputter.output()
            return ''
        return self._outputter.out


class NestedOption(OutputOption, StandardOption):

    """
    An option containing other options.

    It will return True in test if this option applies but False if a sub
    option applies while handle returns the sub option.
    """

    def __init__(self, option: str, shortcut: str, description: str,
                 options: Iterable[Option]) -> None:
        """Initializer."""
        super().__init__(option, shortcut, stop=False)
        self.description = description
        self.options = options

    def format(self, default: Optional[str] = None) -> str:
        """Return a formatted string for that option."""
        self._output = Option.formatted(self.description, self.options)
        return super().format(default=default)

    def handled(self, value: str) -> Optional[Option]:
        """Return itself if it applies or the applying sub option."""
        for option in self.options:
            handled = option.handled(value)
            if handled is not None:
                return handled

        return super().handled(value)

    @property
    def out(self) -> str:
        """Output of suboptions."""
        return self._output


class ContextOption(OutputOption, StandardOption):

    """An option to show more and more context."""

    def __init__(self, option: str, shortcut: str, text: str, context: int,
                 delta: int = 100, start: int = 0, end: int = 0) -> None:
        """Initializer."""
        super().__init__(option, shortcut, stop=False)
        self.text = text
        self.context = context
        self.delta = delta
        self.start = start
        self.end = end

    def result(self, value: str) -> Any:
        """Add the delta to the context."""
        self.context += self.delta
        return None

    @property
    def out(self) -> str:
        """Output section of the text."""
        start = max(0, self.start - self.context)
        end = min(len(self.text), self.end + self.context)
        return self.text[start:end]

    @deprecated('pywikibot.output(ContextOption.out)', since='6.2.0')
    def output_range(self, start: int, end: int) -> None:
        """DEPRECATED. Output a section from the text."""
        pywikibot.output(self.text[start:end])


class Choice(StandardOption):

    """A simple choice consisting of an option, shortcut and handler."""

    def __init__(
        self,
        option: str,
        shortcut: str,
        replacer: Optional['pywikibot.bot.InteractiveReplace']
    ) -> None:
        """Initializer."""
        super().__init__(option, shortcut)
        self._replacer = replacer

    @property
    def replacer(self) -> Optional['pywikibot.bot.InteractiveReplace']:
        """The replacer."""
        return self._replacer

    @abstractmethod
    def handle(self) -> Any:
        """Handle this choice. Must be implemented."""
        raise NotImplementedError()

    def handle_link(self) -> bool:
        """The current link will be handled by this choice."""
        return False


class StaticChoice(Choice):

    """A static choice which just returns the given value."""

    def __init__(self, option: str, shortcut: str, result: Any) -> None:
        """Create instance with replacer set to None."""
        super().__init__(option, shortcut, None)
        self._result = result

    def handle(self) -> Any:
        """Return the predefined value."""
        return self._result


class LinkChoice(Choice):

    """A choice returning a mix of the link new and current link."""

    def __init__(
        self,
        option: str,
        shortcut: str,
        replacer: Optional['pywikibot.bot.InteractiveReplace'],
        replace_section: bool,
        replace_label: bool
    ) -> None:
        """Initializer."""
        super().__init__(option, shortcut, replacer)
        self._section = replace_section
        self._label = replace_label

    def handle(self) -> Any:
        """Handle by either applying the new section or label."""
        if not self.replacer:
            raise ValueError('LinkChoice requires a replacer')

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

    def __init__(self, replacer: Optional['pywikibot.bot.InteractiveReplace'],
                 option: str = 'always', shortcut: str = 'a') -> None:
        """Initializer."""
        super().__init__(option, shortcut, replacer)
        self.always = False

    def handle(self) -> Any:
        """Handle the custom shortcut."""
        self.always = True
        return self.answer

    def handle_link(self) -> bool:
        """Directly return answer whether it's applying it always."""
        return self.always

    @property
    def answer(self) -> Any:
        """Get the actual default answer instructing the replacement."""
        if not self.replacer:
            raise ValueError('AlwaysChoice requires a replacer')

        return self.replacer.handle_answer(self.replacer._default)


class IntegerOption(Option):

    """An option allowing a range of integers."""

    def __init__(self, minimum: int = 1, maximum: Optional[int] = None,
                 prefix: str = '', **kwargs: Any) -> None:
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

    def test(self, value: str) -> bool:
        """Return whether the value is an int and in the specified range."""
        try:
            int_value = self.parse(value)
        except ValueError:
            return False

        return ((self.minimum is None or int_value >= self.minimum)
                and (self.maximum is None or int_value <= self.maximum))

    @property
    def minimum(self) -> int:
        """Return the lower bound of the range of allowed values."""
        return self._min

    @property
    def maximum(self) -> Optional[int]:
        """Return the upper bound of the range of allowed values."""
        return self._max

    def format(self, default: Optional[str] = None) -> str:
        """Return a formatted string showing the range."""
        value = None  # type: Optional[int]

        if default is not None and self.test(default):
            value = self.parse(default)
            default = '[{}]'.format(value)
        else:
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

    def parse(self, value: str) -> int:
        """Return integer from value with prefix removed."""
        if value.lower().startswith(self.prefix.lower()):
            return int(value[len(self.prefix):])
        raise ValueError('Value does not start with prefix')

    def result(self, value: str) -> Any:
        """Return a tuple with the prefix and value converted into an int."""
        return self.prefix, self.parse(value)


class ListOption(IntegerOption):

    """An option to select something from a list."""

    def __init__(self, sequence: Sequence[str], prefix: str = '',
                 **kwargs: Any) -> None:
        """Initializer."""
        self._list = sequence
        try:
            super().__init__(1, self.maximum, prefix, **kwargs)
        except ValueError:
            raise ValueError('The sequence is empty.')
        del self._max

    def format(self, default: Optional[str] = None) -> str:
        """Return a string showing the range."""
        if not self._list:
            raise ValueError('The sequence is empty.')

        return super().format(default=default)

    @property
    def maximum(self) -> int:
        """Return the maximum value."""
        return len(self._list)

    def result(self, value: str) -> Any:
        """Return a tuple with the prefix and selected value."""
        return self.prefix, self._list[self.parse(value) - 1]


class ShowingListOption(ListOption, OutputOption):

    """An option to show a list and select an item.

    .. versionadded:: 3.0
    """

    before_question = True

    def __init__(self, sequence: Sequence[str], prefix: str = '',
                 pre: Optional[str] = None, post: Optional[str] = None,
                 **kwargs: Any) -> None:
        """Initializer.

        :param pre: Additional comment printed before the list.
        :param post: Additional comment printed after the list.
        """
        super().__init__(sequence, prefix, **kwargs)
        self.pre = pre
        self.post = post

    @property
    def stop(self) -> bool:
        """Return whether this option stops asking."""
        return self._stop

    @property
    def out(self) -> str:
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

    .. versionadded 3.0
    """

    def test(self, value: str) -> bool:
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

    def result(self, value: str) -> Any:
        """Return a tuple with the prefix and selected values as a list."""
        values = (self.parse(val) for val in value.split(','))
        result = [self._list[val - 1] for val in values]
        return self.prefix, result


class ShowingMultipleChoiceList(ShowingListOption, MultipleChoiceList):

    """An option to show a list and select multiple items.

    .. versionadded 3.0
    """


class HighlightContextOption(ContextOption):

    """Show the original region highlighted."""

    color = 'lightred'

    @property
    def out(self) -> str:
        """Highlighted output section of the text."""
        start = max(0, self.start - self.context)
        end = min(len(self.text), self.end + self.context)
        return '{}<<{color}>>{}<<default>>{}'.format(
            self.text[start:self.start],
            self.text[self.start:self.end],
            self.text[self.end:end],
            color=self.color)

    @deprecated('pywikibot.output(HighlightContextOption.out)', since='6.2.0')
    def output_range(self, start: int, end: int) -> None:
        """Show normal context with a highlighted center region.

        .. deprecated:: 6.2
           use :attr:`out` instead.
        """
        text = '{}<<{color}>>{}<<default>>{}'.format(
            self.text[start:self.start],
            self.text[self.start:self.end],
            self.text[self.end:end],
            color=self.color)
        pywikibot.output(text)


class UnhandledAnswer(Exception):  # noqa: N818

    """The given answer didn't suffice."""

    def __int__(self, stop: bool = False) -> None:
        """Initializer."""
        self.stop = stop


class ChoiceException(StandardOption, Exception):  # noqa: N818

    """A choice for input_choice which result in this exception."""

    def result(self, value: Any) -> Any:
        """Return itself to raise the exception."""
        return self


class QuitKeyboardInterrupt(ChoiceException, KeyboardInterrupt):  # noqa: N818

    """The user has cancelled processing at a prompt."""

    def __init__(self) -> None:
        """Constructor using the 'quit' ('q') in input_choice."""
        super().__init__('quit', 'q')
