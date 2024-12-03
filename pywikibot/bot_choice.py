"""Options and Choices for :py:meth:`pywikibot.input_choice`."""
#
# (C) Pywikibot team, 2015-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from textwrap import fill
from typing import TYPE_CHECKING, Any

import pywikibot
from pywikibot.backports import Iterable, Mapping, Sequence


__all__ = (
    'AlwaysChoice',
    'Choice',
    'ChoiceException',
    'ContextOption',
    'HighlightContextOption',
    'IntegerOption',
    'InteractiveReplace',
    'LinkChoice',
    'ListOption',
    'MultipleChoiceList',
    'NestedOption',
    'Option',
    'OutputProxyOption',
    'QuitKeyboardInterrupt',
    'ShowingListOption',
    'ShowingMultipleChoiceList',
    'StandardOption',
    'StaticChoice',
    'UnhandledAnswer',
)


if TYPE_CHECKING:
    from typing_extensions import Literal

    from pywikibot.page import BaseLink, Link, Page


class Option(ABC):

    """A basic option for input_choice.

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
    def formatted(text: str, options: Iterable[Option],
                  default: str | None = None) -> str:
        """Create a text with the options formatted into it.

        This static method is used by :meth:`pywikibot.input_choice`.
        It calls :py:obj:`format` for all *options* to combine the
        question for :py:meth:`pywikibot.input`.

        :param text: Text into which options are to be formatted
        :param options: Option instances to be formatted
        :param default: filler for any option's 'default' placeholder

        :return: Text with the options formatted into it
        """
        formatted_options = [option.format(default=default)
                             for option in options]
        # remove color highlights before fill function
        text = f"{text} ({', '.join(formatted_options)})"
        pattern = '<<[a-z]+>>'
        highlights = re.findall(pattern, text)
        return fill(re.sub(pattern, '{}', text), width=77).format(*highlights)

    @property
    def stop(self) -> bool:
        """Return whether this option stops asking."""
        return self._stop

    def handled(self, value: str) -> Option | None:
        """Return the Option object that applies to the given value.

        If this Option object doesn't know which applies it returns None.
        """
        return self if self.test(value) else None

    def format(self, default: str | None = None) -> str:
        """Return a formatted string for that option."""
        raise NotImplementedError

    def test(self, value: str) -> bool:
        """Return True whether this option applies."""
        raise NotImplementedError

    @abstractmethod
    def result(self, value: str) -> Any:
        """Return the actual value which is associated by the given one.

        .. versionadded:: 6.2
           *result()* is an abstract method and must be defined in
           subclasses
        """
        raise NotImplementedError


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
    before_question: bool = False

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


class StandardOption(Option):

    """An option with a description and shortcut and returning the shortcut."""

    def __init__(self, option: str, shortcut: str, **kwargs: Any) -> None:
        """Initializer.

        :param option: option string
        :param shortcut: Shortcut of the option
        """
        super().__init__(**kwargs)
        self.option = option
        self.shortcut = shortcut.lower()

    def format(self, default: str | None = None) -> str:
        """Return a formatted string for that option."""
        index = self.option.lower().find(self.shortcut)
        shortcut = self.shortcut
        if self.shortcut == default:
            shortcut = self.shortcut.upper()
        if index >= 0:
            return (f'{self.option[:index]}[{shortcut}]'
                    f'{self.option[index + len(self.shortcut):]}')
        return f'{self.option} [{shortcut}]'

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
        return self._outputter.out


class NestedOption(OutputOption, StandardOption):

    """An option containing other options.

    It will return True in test if this option applies but False if a sub
    option applies while handle returns the sub option.
    """

    def __init__(self, option: str, shortcut: str, description: str,
                 options: Iterable[Option]) -> None:
        """Initializer."""
        super().__init__(option, shortcut, stop=False)
        self.description = description
        self.options = options

    def format(self, default: str | None = None) -> str:
        """Return a formatted string for that option."""
        self._output = Option.formatted(self.description, self.options)
        return super().format(default=default)

    def handled(self, value: str) -> Option | None:
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


class Choice(StandardOption):

    """A simple choice consisting of an option, shortcut and handler."""

    def __init__(
        self,
        option: str,
        shortcut: str,
        replacer: InteractiveReplace | None
    ) -> None:
        """Initializer."""
        super().__init__(option, shortcut)
        self._replacer = replacer

    @property
    def replacer(self) -> InteractiveReplace | None:
        """The replacer."""
        return self._replacer

    @abstractmethod
    def handle(self) -> Any:
        """Handle this choice. Must be implemented."""
        raise NotImplementedError

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
        replacer: InteractiveReplace | None,
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
        elif self.replacer.current_link.anchor is None:
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

    def __init__(self, replacer: InteractiveReplace | None,
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

    def __init__(self, minimum: int = 1, maximum: int | None = None,
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
    def maximum(self) -> int | None:
        """Return the upper bound of the range of allowed values."""
        return self._max

    def format(self, default: str | None = None) -> str:
        """Return a formatted string showing the range."""
        value: int | None = None

        if default is not None and self.test(default):
            value = self.parse(default)
            default = f'[{value}]'
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
            default = f'-{default}-' if default else '-'
            if self.minimum == self.maximum:
                rng = minimum
            else:
                rng = minimum + default + maximum
        else:
            rng = 'any' + default
        return f'{self.prefix}<number> [{rng}]'

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

    def format(self, default: str | None = None) -> str:
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
                 pre: str | None = None, post: str | None = None,
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

    .. versionadded:: 3.0
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

    .. versionadded:: 3.0
    """


class HighlightContextOption(ContextOption):

    """Show the original region highlighted."""

    color = 'lightred'

    @property
    def out(self) -> str:
        """Highlighted output section of the text."""
        start = max(0, self.start - self.context)
        end = min(len(self.text), self.end + self.context)
        return (f'{self.text[start:self.start]}<<{self.color}>>'
                f'{self.text[self.start:self.end]}<<default>>'
                f'{self.text[self.end:end]}')


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


class InteractiveReplace:

    """A callback class for textlib's replace_links.

    It shows various options which can be switched on and off:
    * allow_skip_link = True (skip the current link)
    * allow_unlink = True (unlink)
    * allow_replace = False (just replace target, keep section and label)
    * allow_replace_section = False (replace target and section, keep label)
    * allow_replace_label = False (replace target and label, keep section)
    * allow_replace_all = False (replace target, section and label)
    (The boolean values are the default values)

    It has also a ``context`` attribute which must be a non-negative
    integer. If it is greater 0 it shows that many characters before and
    after the link in question. The ``context_delta`` attribute can be
    defined too and adds an option to increase ``context`` by the given
    amount each time the option is selected.

    Additional choices can be defined using the 'additional_choices' and will
    be amended to the choices defined by this class. This list is mutable and
    the Choice instance returned and created by this class are too.
    """

    def __init__(self,
                 old_link: Link | Page,
                 new_link: Link | Page | Literal[False],
                 default: str | None = None,
                 automatic_quit: bool = True) -> None:
        """Initializer.

        :param old_link: The old link which is searched. The label and section
            are ignored.
        :param new_link: The new link with which it should be replaced.
            Depending on the replacement mode it'll use this link's label and
            section. If False it'll unlink all and the attributes beginning
            with allow_replace are ignored.
        :param default: The default answer as the shortcut
        :param automatic_quit: Add an option to quit and raise a
            QuitKeyboardException.
        """
        if isinstance(old_link, pywikibot.Page):
            self._old = old_link._link
        else:
            self._old = old_link
        if isinstance(new_link, pywikibot.Page):
            self._new: BaseLink | Literal[False] = new_link._link
        else:
            self._new = new_link
        self._default = default
        self._quit = automatic_quit

        self._current_match: tuple[
            Link | Page,
            str,
            Mapping[str, str],
            tuple[int, int]
        ] | None = None

        self.context = 30
        self.context_delta = 0
        self.allow_skip_link = True
        self.allow_unlink = True
        self.allow_replace = False
        self.allow_replace_section = False
        self.allow_replace_label = False
        self.allow_replace_all = False
        # Use list to preserve order
        self._own_choices: list[tuple[str, StandardOption]] = [
            ('skip_link', StaticChoice('Do not change', 'n', None)),
            ('unlink', StaticChoice('Unlink', 'u', False)),
        ]
        if self._new:
            self._own_choices += [
                ('replace', LinkChoice('Change link target', 't', self,
                                       False, False)),
                ('replace_section', LinkChoice(
                    'Change link target and section', 's', self, True, False)),
                ('replace_label', LinkChoice('Change link target and label',
                                             'l', self, False, True)),
                ('replace_all', LinkChoice('Change complete link', 'c', self,
                                           True, True)),
            ]

        self.additional_choices: list[StandardOption] = []

    def handle_answer(self, choice: str) -> Any:
        """Return the result for replace_links."""
        for c in self.choices:
            if isinstance(c, Choice) and c.shortcut == choice:
                return c.handle()

        raise ValueError(f'Invalid choice "{choice}"')

    def __call__(self, link: Link | Page,
                 text: str, groups: Mapping[str, str],
                 rng: tuple[int, int]) -> Any:
        """Ask user how the selected link should be replaced."""
        if self._old == link:
            self._current_match = (link, text, groups, rng)
            while True:
                try:
                    answer = self.handle_link()
                except UnhandledAnswer as e:
                    if e.stop:
                        raise
                else:
                    break
            self._current_match = None  # don't reset in case of an exception
            return answer
        return None

    @property
    def choices(self) -> tuple[StandardOption, ...]:
        """Return the tuple of choices."""
        choices = []
        for name, choice in self._own_choices:
            if getattr(self, 'allow_' + name):
                choices += [choice]
        if self.context_delta > 0:
            choices += [HighlightContextOption(
                'more context', 'm', self.current_text, self.context,
                self.context_delta, *self.current_range)]
        choices += self.additional_choices
        return tuple(choices)

    def handle_link(self) -> Any:
        """Handle the currently given replacement."""
        choices = self.choices
        for c in choices:
            if isinstance(c, AlwaysChoice) and c.handle_link():
                return c.answer

        question = 'Should the link '
        if self.context > 0:
            rng = self.current_range
            text = self.current_text
            # at the beginning of the link, start red color.
            # at the end of the link, reset the color to default
            pywikibot.info(text[max(0, rng[0] - self.context): rng[0]]
                           + f'<<lightred>>{text[rng[0]:rng[1]]}<<default>>'
                           + text[rng[1]: rng[1] + self.context])
        else:
            question += (
                f'<<lightred>>{self._old.canonical_title()}<<default>> ')

        if self._new is False:
            question += 'be unlinked?'
        else:
            question += (f'target to <<lightpurple>>'
                         f'{self._new.canonical_title()}<<default>>?')

        choice = pywikibot.input_choice(question, choices,
                                        default=self._default,
                                        automatic_quit=self._quit)

        assert isinstance(choice, str)
        return self.handle_answer(choice)

    @property
    def current_link(self) -> Link | Page:
        """Get the current link when it's handling one currently."""
        if self._current_match is None:
            raise ValueError('No current link')
        return self._current_match[0]

    @property
    def current_text(self) -> str:
        """Get the current text when it's handling one currently."""
        if self._current_match is None:
            raise ValueError('No current text')
        return self._current_match[1]

    @property
    def current_groups(self) -> Mapping[str, str]:
        """Get the current groups when it's handling one currently."""
        if self._current_match is None:
            raise ValueError('No current groups')
        return self._current_match[2]

    @property
    def current_range(self) -> tuple[int, int]:
        """Get the current range when it's handling one currently."""
        if self._current_match is None:
            raise ValueError('No current range')
        return self._current_match[3]
