# -*- coding: utf-8  -*-
"""Module containing various formatting related utilities."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import math

from pywikibot.logging import output


class SequenceOutputter(object):

    """
    A class formatting a list of items.

    It is possible to customize the appearance by changing C{format_string}
    which is used by C{str.format} with C{index}, C{width} and C{item}. Each
    line is joined by the separator and the complete text is surrounded by the
    prefix and the suffix. All three are by default a new line. The index starts
    at 1 and for the width it's using the width of the sequence's length written
    as a decimal number. So a length of 100 will result in a with of 3 and a
    length of 99 in a width of 2.

    It is iterating over C{self.sequence} to generate the text. That sequence
    can be any iterator but the result is better when it has an order.
    """

    format_string = '  {index:>{width}} - {item}'
    separator = '\n'
    prefix = '\n'
    suffix = '\n'

    def __init__(self, sequence):
        """Create a new instance with a reference to the sequence."""
        super(SequenceOutputter, self).__init__()
        self.sequence = sequence

    def format_list(self):
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

    def output(self):
        """Output the text of the current sequence."""
        output(self.format_list())
