"""Character based helper functions (not wiki-dependent)."""
#
# (C) Pywikibot team, 2015-2020
#
# Distributed under the terms of the MIT license.
#
import sys

from pywikibot.tools._unidata import _category_cf
from pywikibot.tools import LazyRegex

# This is a set of all invisible characters
# At the moment we've only added the characters from the Cf category
_invisible_chars = _category_cf

invisible_regex = LazyRegex(lambda: '[{}]'.format(''.join(_invisible_chars)))


def contains_invisible(text):
    """Return True if the text contain any of the invisible characters."""
    return any(char in _invisible_chars for char in text)


def replace_invisible(text):
    """Replace invisible characters by '<codepoint>'."""
    def replace(match):
        match = match.group()
        if sys.maxunicode < 0x10ffff and len(match) == 2:
            mask = (1 << 10) - 1
            assert(ord(match[0]) & ~mask == 0xd800)
            assert(ord(match[1]) & ~mask == 0xdc00)
            codepoint = (ord(match[0]) & mask) << 10 | (ord(match[1]) & mask)
        else:
            codepoint = ord(match)
        return '<{0:x}>'.format(codepoint)
    return invisible_regex.sub(replace, text)
