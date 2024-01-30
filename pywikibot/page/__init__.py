"""Interface of various types of MediaWiki pages."""
#
# (C) Pywikibot team, 2022-2023
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

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
)

PageSourceType = Union[
    BaseLink,
    BasePage,
    _BaseSite,
]
