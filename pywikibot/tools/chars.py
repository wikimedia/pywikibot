"""Character based helper functions (not wiki-dependent)."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import re
import sys
from contextlib import suppress
from typing import Union
from urllib.parse import unquote_to_bytes

from pywikibot.backports import List, Tuple
from pywikibot.tools._unidata import _category_cf


# This is a set of all invisible characters
# At the moment we've only added the characters from the Cf category
_invisible_chars = _category_cf

INVISIBLE_REGEX = re.compile('[{}]'.format(''.join(_invisible_chars)))


def contains_invisible(text):
    """Return True if the text contain any of the invisible characters."""
    return any(char in _invisible_chars for char in text)


def replace_invisible(text):
    """Replace invisible characters by '<codepoint>'."""
    def replace(match) -> str:
        match = match.group()
        if sys.maxunicode < 0x10ffff and len(match) == 2:
            mask = (1 << 10) - 1
            assert ord(match[0]) & ~mask == 0xd800
            assert ord(match[1]) & ~mask == 0xdc00
            codepoint = (ord(match[0]) & mask) << 10 | (ord(match[1]) & mask)
        else:
            codepoint = ord(match)
        return '<{:x}>'.format(codepoint)

    return INVISIBLE_REGEX.sub(replace, text)


def string_to_ascii_html(string: str) -> str:
    """Convert unicode chars of str to HTML entities if chars are not ASCII.

    :param string: String to update
    """
    html = []
    for c in string:
        cord = ord(c)
        if 31 < cord < 127:
            html.append(c)
        else:
            html.append('&#{};'.format(cord))
    return ''.join(html)


def string2html(string: str, encoding: str) -> str:
    """Convert unicode string to requested HTML encoding.

    Attempt to encode the string into the desired format; if that work
    return it unchanged. Otherwise encode the non-ASCII characters into
    HTML &#; entities.

    :param string: String to update
    :param encoding: Encoding to use
    """
    with suppress(UnicodeError):
        string.encode(encoding)
        return string

    return string_to_ascii_html(string)


def url2string(
    title: str,
    encodings: Union[str, List[str], Tuple[str, ...]] = 'utf-8'
) -> str:
    """Convert URL-encoded text to unicode using several encoding.

    Uses the first encoding that doesn't cause an error.

    :param title: URL-encoded character data to convert
    :param encodings: Encodings to attempt to use during conversion.

    :raise UnicodeError: Could not convert using any encoding.
    """
    if isinstance(encodings, str):
        encodings = [encodings]

    first_exception = None
    for enc in encodings:
        try:
            t = title.encode(enc)
            t = unquote_to_bytes(t)
        except UnicodeError as e:
            if not first_exception:
                first_exception = e
        else:
            return t.decode(enc)

    # Couldn't convert, raise the first exception
    raise first_exception
