# -*- coding: utf-8 -*-
"""Character based helper functions(not wiki-dependent)."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import re
import sys


if sys.version_info[0] > 2:
    unicode = str


# All characters in the Cf category. When testing each Unicode codepoint it
# takes longer especially when working with UCS2. The codepoints also
# differ between Python versions which can be avoided by this static list.
_category_cf = (
    '\U000000AD\U00000600\U00000601\U00000602\U00000603\U00000604\U00000605'
    '\U0000061C\U000006DD\U0000070F\U000008E2\U0000180E\U0000200B\U0000200C'
    '\U0000200D\U0000200E\U0000200F\U0000202A\U0000202B\U0000202C\U0000202D'
    '\U0000202E\U00002060\U00002061\U00002062\U00002063\U00002064\U00002066'
    '\U00002067\U00002068\U00002069\U0000206A\U0000206B\U0000206C\U0000206D'
    '\U0000206E\U0000206F\U0000FEFF\U0000FFF9\U0000FFFA\U0000FFFB\U000110BD'
    '\U000110CD\U0001BCA0\U0001BCA1\U0001BCA2\U0001BCA3\U0001D173\U0001D174'
    '\U0001D175\U0001D176\U0001D177\U0001D178\U0001D179\U0001D17A\U000E0001'
    '\U000E0020\U000E0021\U000E0022\U000E0023\U000E0024\U000E0025\U000E0026'
    '\U000E0027\U000E0028\U000E0029\U000E002A\U000E002B\U000E002C\U000E002D'
    '\U000E002E\U000E002F\U000E0030\U000E0031\U000E0032\U000E0033\U000E0034'
    '\U000E0035\U000E0036\U000E0037\U000E0038\U000E0039\U000E003A\U000E003B'
    '\U000E003C\U000E003D\U000E003E\U000E003F\U000E0040\U000E0041\U000E0042'
    '\U000E0043\U000E0044\U000E0045\U000E0046\U000E0047\U000E0048\U000E0049'
    '\U000E004A\U000E004B\U000E004C\U000E004D\U000E004E\U000E004F\U000E0050'
    '\U000E0051\U000E0052\U000E0053\U000E0054\U000E0055\U000E0056\U000E0057'
    '\U000E0058\U000E0059\U000E005A\U000E005B\U000E005C\U000E005D\U000E005E'
    '\U000E005F\U000E0060\U000E0061\U000E0062\U000E0063\U000E0064\U000E0065'
    '\U000E0066\U000E0067\U000E0068\U000E0069\U000E006A\U000E006B\U000E006C'
    '\U000E006D\U000E006E\U000E006F\U000E0070\U000E0071\U000E0072\U000E0073'
    '\U000E0074\U000E0075\U000E0076\U000E0077\U000E0078\U000E0079\U000E007A'
    '\U000E007B\U000E007C\U000E007D\U000E007E\U000E007F')

# This is a set of all invisible characters
# At the moment we've only added the characters from the Cf category
_invisible_chars = frozenset(_category_cf)

invisible_regex = re.compile('[' + _category_cf + ']')


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
