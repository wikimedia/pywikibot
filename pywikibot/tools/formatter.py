"""Module containing various formatting related utilities."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import math
import re

from pywikibot.logging import output
from pywikibot.tools import deprecated
from pywikibot.userinterfaces import terminal_interface_base


class SequenceOutputter:

    """A class formatting a list of items.

    It is possible to customize the appearance by changing
    ``format_string`` which is used by ``str.format`` with ``index``,
    ``width`` and ``item``. Each line is joined by the separator and the
    complete text is surrounded by the prefix and the suffix. All three
    are by default a new line. The index starts at 1 and for the width
    it's using the width of the sequence's length written as a decimal
    number. So a length of 100 will result in a with of 3 and a length
    of 99 in a width of 2.

    It is iterating over ``self.sequence`` to generate the text. That
    sequence can be any iterator but the result is better when it has
    an order.
    """

    format_string = '  {index:>{width}} - {item}'
    separator = '\n'
    prefix = '\n'
    suffix = '\n'

    def __init__(self, sequence) -> None:
        """Create a new instance with a reference to the sequence."""
        super().__init__()
        self.sequence = sequence

    @deprecated('out', since='6.2.0')
    def format_list(self):
        """DEPRECATED: Create the text with one item on each line."""
        return self.out

    @property
    def out(self):
        """Create the text with one item on each line."""
        if self.sequence:
            # Width is only defined when the length is greater 0
            width = int(math.log10(len(self.sequence))) + 1
            content = self.separator.join(
                self.format_string.format(index=i, item=item, width=width)
                for i, item in enumerate(self.sequence, start=1))
        else:
            content = ''
        return self.prefix + content + self.suffix

    def output(self) -> None:
        """Output the text of the current sequence."""
        output(self.out)


@deprecated('New color format pattern like <<color>>colored text<<default>>',
            since='7.2.0')
def color_format(text: str, *args, **kwargs) -> str:
    r"""
    Do ``str.format`` without having to worry about colors.

    It is automatically adding \03 in front of color fields so it's
    unnecessary to add them manually. Any other \03 in the text is
    disallowed.

    You may use a variant {color} by assigning a valid color to a named
    parameter color.

    .. deprecated:: 7.2
       new color format pattern like <<color>>colored text<<default>>
       may be used instead.

    :param text: The format template string
    :return: The formatted string
    :raises ValueError: Wrong format string or wrong keywords
    """
    colors = set(terminal_interface_base.colors)
    # Dot.product of colors to create all possible combinations of foreground
    # and background colors.
    colors |= {'{};{}'.format(c1, c2) for c1 in colors for c2 in colors}
    col_pat = '|'.join(colors)
    text = re.sub('(?:\03)?{{({})}}'.format(col_pat), r'<<\1>>', text)
    replace_color = kwargs.get('color')
    if replace_color in colors:
        text = text.replace('{color}', '<<{}>>'.format(replace_color))
    if '\03' in text:
        raise ValueError('\\03 pattern found in color format')
    intersect = colors.intersection(kwargs)  # kwargs use colors
    if intersect:
        raise ValueError('Keyword argument(s) use valid color(s): '
                         + '", "'.join(intersect))
    try:
        text = text.format(*args, **kwargs)
    except KeyError as e:
        if str(e).strip("'") in colors:
            raise ValueError(
                'Color field "{}" in "{}" uses conversion information or '
                'format spec'.format(e, text))
        raise
    return text
