"""Module containing various formatting related utilities."""
#
# (C) Pywikibot team, 2015-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import math

from pywikibot.logging import info
from pywikibot.tools import deprecated


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

    @deprecated('pywikibot.info(SequenceOutputter.out)', since='9.0.0')
    def output(self) -> None:
        """Output the text of the current sequence.

        .. deprecated:: 9.0
           Use :func:`pywikibot.info()<pywikibot.logging.info>` with
           :attr:`out` property.
        """
        info(self.out)
