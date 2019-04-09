# -*- coding: utf-8 -*-
"""Character based helper functions (not wiki-dependent)."""
#
# (C) Pywikibot team, 2015-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import sys

from pywikibot.tools import LazyRegex


# All characters in the Cf category in a static list. When testing each Unicode
# codepoint it takes longer especially when working with UCS2. The lists also
# differ between Python versions which can be avoided by this static list.
_category_cf = frozenset([
    '\U000000ad', '\U00000600', '\U00000601', '\U00000602', '\U00000603',
    '\U00000604', '\U00000605', '\U0000061c', '\U000006dd', '\U0000070f',
    '\U000008e2', '\U0000180e', '\U0000200b', '\U0000200c', '\U0000200d',
    '\U0000200e', '\U0000200f', '\U0000202a', '\U0000202b', '\U0000202c',
    '\U0000202d', '\U0000202e', '\U00002060', '\U00002061', '\U00002062',
    '\U00002063', '\U00002064', '\U00002066', '\U00002067', '\U00002068',
    '\U00002069', '\U0000206a', '\U0000206b', '\U0000206c', '\U0000206d',
    '\U0000206e', '\U0000206f', '\U0000feff', '\U0000fff9', '\U0000fffa',
    '\U0000fffb', '\U000110bd', '\U000110cd', '\U0001bca0', '\U0001bca1',
    '\U0001bca2', '\U0001bca3', '\U0001d173', '\U0001d174', '\U0001d175',
    '\U0001d176', '\U0001d177', '\U0001d178', '\U0001d179', '\U0001d17a',
    '\U000e0001', '\U000e0020', '\U000e0021', '\U000e0022', '\U000e0023',
    '\U000e0024', '\U000e0025', '\U000e0026', '\U000e0027', '\U000e0028',
    '\U000e0029', '\U000e002a', '\U000e002b', '\U000e002c', '\U000e002d',
    '\U000e002e', '\U000e002f', '\U000e0030', '\U000e0031', '\U000e0032',
    '\U000e0033', '\U000e0034', '\U000e0035', '\U000e0036', '\U000e0037',
    '\U000e0038', '\U000e0039', '\U000e003a', '\U000e003b', '\U000e003c',
    '\U000e003d', '\U000e003e', '\U000e003f', '\U000e0040', '\U000e0041',
    '\U000e0042', '\U000e0043', '\U000e0044', '\U000e0045', '\U000e0046',
    '\U000e0047', '\U000e0048', '\U000e0049', '\U000e004a', '\U000e004b',
    '\U000e004c', '\U000e004d', '\U000e004e', '\U000e004f', '\U000e0050',
    '\U000e0051', '\U000e0052', '\U000e0053', '\U000e0054', '\U000e0055',
    '\U000e0056', '\U000e0057', '\U000e0058', '\U000e0059', '\U000e005a',
    '\U000e005b', '\U000e005c', '\U000e005d', '\U000e005e', '\U000e005f',
    '\U000e0060', '\U000e0061', '\U000e0062', '\U000e0063', '\U000e0064',
    '\U000e0065', '\U000e0066', '\U000e0067', '\U000e0068', '\U000e0069',
    '\U000e006a', '\U000e006b', '\U000e006c', '\U000e006d', '\U000e006e',
    '\U000e006f', '\U000e0070', '\U000e0071', '\U000e0072', '\U000e0073',
    '\U000e0074', '\U000e0075', '\U000e0076', '\U000e0077', '\U000e0078',
    '\U000e0079', '\U000e007a', '\U000e007b', '\U000e007c', '\U000e007d',
    '\U000e007e', '\U000e007f',
])
# This is a set of all invisible characters
# At the moment we've only added the characters from the Cf category
_invisible_chars = _category_cf

invisible_regex = LazyRegex(
    lambda: '[' + ''.join(_invisible_chars) + ']'
)


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
