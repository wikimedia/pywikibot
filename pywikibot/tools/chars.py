"""Character based helper functions (not wiki-dependent)."""
#
# (C) Pywikibot team, 2015-2023
#
# Distributed under the terms of the MIT license.
#
import re
import sys
from contextlib import suppress
from typing import Union
from urllib.parse import unquote_to_bytes

from pywikibot.backports import Iterable
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
        return f'<{codepoint:x}>'

    return INVISIBLE_REGEX.sub(replace, text)


def string_to_ascii_html(string: str) -> str:
    """Convert unicode chars of str to HTML entities if chars are not ASCII.

    **Example:**

    >>> string_to_ascii_html('Python')
    'Python'
    >>> string_to_ascii_html("Pywikibot's API")
    "Pywikibot's API"
    >>> string_to_ascii_html('Eetße Joohunndot füür Kreůßtůß')
    'Eet&#223;e Joohunndot f&#252;&#252;r Kre&#367;&#223;t&#367;&#223;'

    :param string: String to update
    """
    html = []
    for c in string:
        cord = ord(c)
        if 31 < cord < 127:
            html.append(c)
        else:
            html.append(f'&#{cord};')
    return ''.join(html)


def string2html(string: str, encoding: str) -> str:
    """Convert unicode string to requested HTML encoding.

    Attempt to encode the string into the desired format; if that work
    return it unchanged. Otherwise encode the non-ASCII characters into
    HTML &#; entities.

    **Example:**

    >>> string2html('Referências', 'utf-8')
    'Referências'
    >>> string2html('Referências', 'ascii')
    'Refer&#234;ncias'
    >>> string2html('脚注', 'euc_jp')
    '脚注'
    >>> string2html('脚注', 'iso-8859-1')
    '&#33050;&#27880;'

    :param string: String to update
    :param encoding: Encoding to use
    """
    with suppress(UnicodeError):
        string.encode(encoding)
        return string

    return string_to_ascii_html(string)


def url2string(title: str,
               encodings: Union[str, Iterable[str]] = 'utf-8') -> str:
    """Convert URL-encoded text to unicode using several encoding.

    Uses the first encoding that doesn't cause an error.

    **Example:**

    >>> url2string('/El%20Ni%C3%B1o/')
    '/El Niño/'
    >>> url2string('/El%20Ni%C3%B1o/', 'ascii')
    Traceback (most recent call last):
    ...
    UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3 in position 6:...
    >>> url2string('/El%20Ni%C3%B1o/', ['ascii', 'utf-8'])
    '/El Niño/'

    :param title: URL-encoded character data to convert
    :param encodings: Encodings to attempt to use during conversion.

    :raise UnicodeError: Could not convert using any encoding.
    :raise LookupError: unknown encoding
    """
    if isinstance(encodings, str):
        encodings = [encodings]

    first_exception = None
    for enc in encodings:
        try:
            t = title.encode(enc)
            t = unquote_to_bytes(t)
            result = t.decode(enc)
        except UnicodeError as e:
            if not first_exception:
                first_exception = e
        else:
            return result

    # Couldn't convert, raise the first exception
    raise first_exception
