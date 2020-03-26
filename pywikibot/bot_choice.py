# -*- coding: utf-8 -*-
"""Choices for input_choice."""
#
# (C) Pywikibot team, 2015-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import re
from textwrap import fill

import pywikibot


class Option(object):

    """
    A basic option for input_choice.

    The following methods need to be implemented:
    * format(default=None)
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
        """Initializer."""
        self._stop = stop

    @staticmethod
    def formatted(text, options, default=None):
        """
        Create a text with the options formatted into it.

        @param text: Text into which options are to be formatted
        @type text: str
        @param options: Option instances to be formatted
        @type options: Iterable
        @return: Text with the options formatted into it
        @rtype: str
        """
        formatted_options = []
        for option in options:
            formatted_options.append(option.format(default=default))
        # remove color highlights before fill function
        text = '{0} ({1})'.format(text, ', '.join(formatted_options))
        pattern = '\03{[a-z]+}'
        highlights = re.findall(pattern, text)
        return fill(re.sub(pattern, '{}', text), width=77).format(*highlights)

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

    def format(self, default=None):
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
        """Output a string when selected and possibly before the question."""
        raise NotImplementedError()


class StandardOption(Option):

    """An option with a description and shortcut and returning the shortcut."""

    def __init__(self, option, shortcut, **kwargs):
        """
        Initializer.

        @param option: option string
        @type option: str
        @param shortcut: Shortcut of the option
        @type shortcut: str
        """
        super(StandardOption, self).__init__(**kwargs)
        self.option = option
        self.shortcut = shortcut.lower()

    def format(self, default=None):
        """Return a formatted string for that option."""
        index = self.option.lower().find(self.shortcut)
        shortcut = self.shortcut
        if self.shortcut == default:
            shortcut = self.shortcut.upper()
        if index >= 0:
            return '{0}[{1}]{2}'.format(
                self.option[:index], shortcut,
                self.option[index + len(self.shortcut):])
        else:
            return '{0} [{1}]'.format(self.option, shortcut)

    def result(self, value):
        """Return the lowercased shortcut."""
        return self.shortcut

    def test(self, value):
        """Return True whether this option applies."""
        return (self.shortcut.lower() == value.lower()
                or self.option.lower() == value.lower())


class OutputProxyOption(OutputOption, StandardOption):

    """An option which calls output of the given output class."""

    def __init__(self, option, shortcut, output, **kwargs):
        """Create a new option for the given sequence."""
        super(OutputProxyOption, self).__init__(option, shortcut, **kwargs)
        self._outputter = output

    def output(self):
        """Output the contents."""
        self._outputter.output()


class NestedOption(OutputOption, StandardOption):

    """
    An option containing other options.

    It will return True in test if this option applies but False if a sub
    option applies while handle returns the sub option.
    """

    def __init__(self, option, shortcut, description, options):
        """Initializer."""
        super(NestedOption, self).__init__(option, shortcut, stop=False)
        self.description = description
        self.options = options

    def format(self, default=None):
        """Return a formatted string for that option."""
        self._output = Option.formatted(self.description, self.options)
        return super(NestedOption, self).format(default=default)

    def handled(self, value):
        """Return itself if it applies or the applying sub option."""
        for option in self.options:
            handled = option.handled(value)
            if handled is not None:
                return handled
        else:
            return super(NestedOption, self).handled(value)

    def output(self):
        """Output the suboptions."""
        pywikibot.output(self._output)


class ContextOption(OutputOption, StandardOption):

    """An option to show more and more context."""

    def __init__(
        self, option, shortcut, text, context, delta=100, start=0, end=0
    ):
        """Initializer."""
        super(ContextOption, self).__init__(option, shortcut, stop=False)
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


class Choice(StandardOption):

    """A simple choice consisting of a option, shortcut and handler."""

    def __init__(self, option, shortcut, replacer):
        """Initializer."""
        super(Choice, self).__init__(option, shortcut)
        self._replacer = replacer

    @property
    def replacer(self):
        """The replacer."""
        return self._replacer

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
        super(StaticChoice, self).__init__(option, shortcut, None)
        self._result = result

    def handle(self):
        """Return the predefined value."""
        return self._result


class LinkChoice(Choice):

    """A choice returning a mix of the link new and current link."""

    def __init__(self, option, shortcut, replacer, replace_section,
                 replace_label):
        """Initializer."""
        super(LinkChoice, self).__init__(option, shortcut, replacer)
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
                    kwargs['label'] += '#' + \
                                       self.replacer.current_groups['section']
            else:
                kwargs['label'] = self.replacer.current_link.anchor
        return pywikibot.Link.create_separated(
            self.replacer._new.canonical_title(), self.replacer._new.site,
            **kwargs)


class AlwaysChoice(Choice):

    """Add an option to always apply the default."""

    def __init__(self, replacer, option='always', shortcut='a'):
        """Initializer."""
        super(AlwaysChoice, self).__init__(option, shortcut, replacer)
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
        super(IntegerOption, self).__init__(**kwargs)
        if not ((minimum is None or isinstance(minimum, int))
                and (maximum is None or isinstance(maximum, int))):
            raise ValueError(
                'The minimum and maximum parameters must be int or None.')
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError('The minimum must be lower than the maximum.')
        self._min = minimum
        self._max = maximum
        self.prefix = prefix

    def test(self, value):
        """Return whether the value is an int and in the specified range."""
        try:
            value = self.parse(value)
        except ValueError:
            return False
        else:
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

    def format(self, default=None):
        """Return a formatted string showing the range."""
        if default is not None and self.test(default):
            value = self.parse(default)
            default = '[{0}]'.format(value)
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
            default = '-{0}-'.format(default) if default else '-'
            if self.minimum == self.maximum:
                rng = minimum
            else:
                rng = minimum + default + maximum
        else:
            rng = 'any' + default
        return '{0}<number> [{1}]'.format(self.prefix, rng)

    def parse(self, value):
        """Return integer from value with prefix removed."""
        if value.lower().startswith(self.prefix.lower()):
            return int(value[len(self.prefix):])
        else:
            raise ValueError('Value does not start with prefix')

    def result(self, value):
        """Return the value converted into int."""
        return (self.prefix, self.parse(value))


class ListOption(IntegerOption):

    """An option to select something from a list."""

    def __init__(self, sequence, prefix='', **kwargs):
        """Initializer."""
        self._list = sequence
        try:
            super(ListOption, self).__init__(1, self.maximum, prefix, **kwargs)
        except ValueError:
            raise ValueError('The sequence is empty.')
        del self._max

    def format(self, default=None):
        """Return a string showing the range."""
        if not self._list:
            raise ValueError('The sequence is empty.')
        else:
            return super(ListOption, self).format(default=default)

    @property
    def maximum(self):
        """Return the maximum value."""
        return len(self._list)

    def result(self, value):
        """Return a tuple with the prefix and selected value."""
        return (self.prefix, self._list[self.parse(value) - 1])


class ShowingListOption(ListOption, OutputOption):

    """An option to show a list and select an item."""

    before_question = True

    def __init__(self, sequence, prefix='', pre=None, post=None, **kwargs):
        """Initializer.

        @param pre: Additional comment printed before the list.
        @type pre: str
        @param post: Additional comment printed after the list.
        @type post: str
        """
        super(ShowingListOption, self).__init__(sequence, prefix, **kwargs)
        self.pre = pre
        self.post = post

    @property
    def stop(self):
        """Return whether this option stops asking."""
        return self._stop

    def output(self):
        """Output the enumerated list."""
        if self.pre is not None:
            pywikibot.output(self.pre)
        width = len(str(self.maximum))
        for i, item in enumerate(self._list, self.minimum):
            pywikibot.output('{:>{width}} - {}'.format(i, item, width=width))
        if self.post is not None:
            pywikibot.output(self.post)


class MultipleChoiceList(ListOption):

    """An option to select multiple items from a list."""

    def test(self, value):
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
        return (self.prefix, result)


class ShowingMultipleChoiceList(ShowingListOption, MultipleChoiceList):

    """An option to show a list and select multiple items."""

    pass


class HighlightContextOption(ContextOption):

    """Show the original region highlighted."""

    def output_range(self, start, end):
        """Show normal context with a red center region."""
        pywikibot.output(self.text[start:self.start] + '\03{lightred}'
                         + self.text[self.start:self.end] + '\03{default}'
                         + self.text[self.end:end])


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
