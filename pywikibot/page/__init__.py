"""Interface of various types of MediaWiki pages."""
#
# (C) Pywikibot team, 2022-2023
#
# Distributed under the terms of the MIT license.
#
from typing import Union

from pywikibot.page._basepage import BasePage
from pywikibot.page._category import Category
from pywikibot.page._filepage import FileInfo, FilePage
from pywikibot.page._links import BaseLink, Link, SiteLink, html2unicode
from pywikibot.page._page import Page
from pywikibot.page._revision import Revision
from pywikibot.page._user import User
from pywikibot.page._wikibase import (
    Claim,
    ItemPage,
    LexemeForm,
    LexemePage,
    LexemeSense,
    MediaInfo,
    Property,
    PropertyPage,
    WikibaseEntity,
    WikibasePage,
)
from pywikibot.site import BaseSite as _BaseSite
from pywikibot.tools import deprecated, issue_deprecation_warning
from pywikibot.tools.chars import url2string as _url2string


__all__ = (
    'BaseLink',
    'Link',
    'SiteLink',
    'BasePage',
    'Page',
    'FilePage',
    'Category',
    'User',
    'WikibasePage',
    'ItemPage',
    'LexemePage',
    'LexemeForm',
    'LexemeSense',
    'PropertyPage',
    'Property',
    'Claim',
    'FileInfo',
    'WikibaseEntity',
    'MediaInfo',
    'Revision',
    'html2unicode',
    'url2unicode',
)

PageSourceType = Union[
    BaseLink,
    _BaseSite,
    Page,
]


@deprecated('pywikibot.tools.chars.url2string', since='6.2.0')
def url2unicode(title: str, encodings='utf-8') -> str:
    """Convert URL-encoded text to unicode using several encoding.

    Uses the first encoding that doesn't cause an error.

    .. deprecated:: 6.2
       Use :func:`tools.chars.url2string` instead.

    :param title: URL-encoded character data to convert
    :param encodings: Encodings to attempt to use during conversion.
    :type encodings: str, list or Site

    :raise UnicodeError: Could not convert using any encoding.
    """
    if isinstance(encodings, _BaseSite):
        # use all possible encodings from Site object
        encodings = encodings.encodings()
        issue_deprecation_warning(
            'Passing BaseSite object to encodings parameter',
            'BaseSite.encodings()',
            depth=1,
            since='6.2.0'
        )

    return _url2string(title, encodings)
