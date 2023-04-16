"""
Objects used with ProofreadPage Extension.

This module includes objects:

* ProofreadPage(Page)
* FullHeader
* IndexPage(Page)


OCR support of page scans via:
- https://phetools.toolforge.org/hocr_cgi.py
- https://phetools.toolforge.org/ocr.php
- inspired by https://en.wikisource.org/wiki/MediaWiki:Gadget-ocr.js

- Wikimedia OCR
- see: https://www.mediawiki.org/wiki/Help:Extension:Wikisource/Wikimedia_OCR

- https://ocr.wmcloud.org/
- inspired by https://wikisource.org/wiki/MediaWiki:GoogleOCR.js
- see also: https://wikisource.org/wiki/Wikisource:Google_OCR

"""
#
# (C) Pywikibot team, 2015-2023
#
# Distributed under the terms of the MIT license.
#
import collections.abc
import json
import re
import time
from functools import partial
from http import HTTPStatus
from typing import Any, Optional, Union
from urllib.parse import unquote
from weakref import WeakKeyDictionary

from requests.exceptions import ReadTimeout

import pywikibot
from pywikibot import textlib
from pywikibot.backports import (
    Callable,
    Dict,
    Iterable,
    List,
    Sequence,
    Set,
    Tuple,
    pairwise,
)
from pywikibot.comms import http
from pywikibot.data.api import ListGenerator, Request
from pywikibot.exceptions import Error, InvalidTitleError, OtherPageSaveError
from pywikibot.page import PageSourceType
from pywikibot.tools import cached


try:
    from bs4 import BeautifulSoup
except ImportError as e:
    BeautifulSoup = e

    def _bs4_soup(*args: Any, **kwargs: Any) -> None:
        """Raise BeautifulSoup when called, if bs4 is not available."""
        raise BeautifulSoup
else:
    from bs4 import FeatureNotFound
    try:
        BeautifulSoup('', 'lxml')
    except FeatureNotFound:
        _bs4_soup = partial(BeautifulSoup, features='html.parser')
    else:
        _bs4_soup = partial(BeautifulSoup, features='lxml')


PagesFromLabelType = Dict[str, Set['pywikibot.page.Page']]
_IndexType = Tuple[Optional['IndexPage'], List['IndexPage']]


class TagAttr:
    """Tag attribute of <pages />.

    Represent a single attribute. It is used internally in
    :class:`PagesTagParser` and shall not be used stand-alone.

    It manages string formatting output and conversion str <--> int and
    quotes. Input value can only be str or int and shall have quotes or
    nothing.

    >>> a = TagAttr('to', 3.0)
    Traceback (most recent call last):
      ...
    TypeError: value=3.0 must be str or int.

    >>> a = TagAttr('to', 'A123"')
    Traceback (most recent call last):
      ...
    ValueError: value=A123" has wrong quotes.

    >>> a = TagAttr('to', 3)
    >>> a
    TagAttr('to', 3)
    >>> str(a)
    'to=3'
    >>> a.attr
    'to'
    >>> a.value
    3

    >>> a = TagAttr('to', '3')
    >>> a
    TagAttr('to', '3')
    >>> str(a)
    'to=3'
    >>> a.attr
    'to'
    >>> a.value
    3

    >>> a = TagAttr('to', '"3"')
    >>> a
    TagAttr('to', '"3"')
    >>> str(a)
    'to="3"'
    >>> a.value
    3

    >>> a = TagAttr('to', "'3'")
    >>> a
    TagAttr('to', "'3'")
    >>> str(a)
    "to='3'"
    >>> a.value
    3

    >>> a = TagAttr('to', 'A123')
    >>> a
    TagAttr('to', 'A123')
    >>> str(a)
    'to=A123'
    >>> a.value
    'A123'

    .. versionadded:: 8.0
    """

    def __init__(self, attr, value):
        """Initializer."""
        self.attr = attr
        self._value = self._convert(value)

    def _convert(self, value):
        """Handle conversion from str to int and quotes."""
        if not isinstance(value, (str, int)):
            raise TypeError(f'value={value} must be str or int.')

        self._orig_value = value

        if isinstance(value, str):
            if (value.startswith('"') != value.endswith('"')
                    or value.startswith("'") != value.endswith("'")):
                raise ValueError(f'value={value} has wrong quotes.')
            value = value.strip('"\'')
            value = int(value) if value.isdigit() else value

        return value

    @property
    def value(self):
        """Attribute value."""
        return self._value

    @value.setter
    def value(self, value):
        self._value = self._convert(value)

    def __str__(self):
        attr = 'from' if self.attr == 'ffrom' else self.attr
        return f'{attr}={self._orig_value}'

    def __repr__(self):
        attr = 'from' if self.attr == 'ffrom' else self.attr
        return f"{self.__class__.__name__}('{attr}', {repr(self._orig_value)})"


class TagAttrDesc:
    """A descriptor tag.

    .. versionadded:: 8.0
    """

    def __init__(self):
        """Initializer."""
        self.attrs = WeakKeyDictionary()

    def __set_name__(self, owner, name):
        self.public_name = name

    def __get__(self, obj, objtype=None):
        attr = self.attrs.get(obj)
        return attr.value if attr is not None else None

    def __set__(self, obj, value):
        attr = self.attrs.get(obj)
        if attr is not None:
            attr.value = value
        else:
            self.attrs[obj] = TagAttr(self.public_name, value)

    def __delete__(self, obj):
        self.attrs.pop(obj, None)


class PagesTagParser(collections.abc.Container):
    """Parser for tag ``<pages />``.

    .. seealso::
       https://www.mediawiki.org/wiki/Help:Extension:ProofreadPage/Pages_tag

    Parse text and extract the first ``<pages ... />`` tag.
    Individual attributes will be accessible with dot notation.

    >>> tp = PagesTagParser('<pages />')
    >>> tp
    PagesTagParser('<pages />')

    >>> tp = PagesTagParser(
    ... 'Text: <pages index="Index.pdf" from="first" to="last" />')
    >>> tp
    PagesTagParser('<pages index="Index.pdf" from="first" to="last" />')

    Attributes can be modified via dot notation. If an attribute is a
    number, it is converted to int.

    .. note:: ``from`` is represented as ``ffrom`` due to conflict with
       keyword.

    >>> tp.ffrom = 1; tp.to = '"3"'
    >>> tp.ffrom
    1
    >>> tp.to
    3

    Quotes are stripped in the value and added back in the str
    representation.

    .. note:: Quotes are not mandatory.

    >>> tp
    PagesTagParser('<pages index="Index.pdf" from=1 to="3" />')

    Attributes can be added via dot notation. Order is fixed (same order
    as attribute definition in the class).

    >>> tp.fromsection = '"A"'
    >>> tp.fromsection
    'A'
    >>> tp
    PagesTagParser('<pages index="Index.pdf" from=1 to="3" fromsection="A" />')

    Attributes can be deleted.
    >>> del tp.fromsection
    >>> tp
    PagesTagParser('<pages index="Index.pdf" from=1 to="3" />')

    Attribute presence can be checked.
    >>> 'to' in tp
    True

    >>> 'step' in tp
    False

    .. versionadded:: 8.0
    .. versionchanged:: 8.1
       *text* parameter is defaulted to ``'<pages />'``.
    """

    pat_tag = re.compile(r'<pages (?P<attrs>[^/]*?)/>')
    tokens = (
        'index',
        'from',
        'to',
        'include',
        'exclude',
        'step',
        'header',
        'fromsection',
        'tosection',
        'onlysection',
    )
    tokens = '(' + '=|'.join(tokens) + '=)'
    pat_attr = re.compile(tokens)

    index = TagAttrDesc()
    ffrom = TagAttrDesc()
    to = TagAttrDesc()
    include = TagAttrDesc()
    exclude = TagAttrDesc()
    step = TagAttrDesc()
    header = TagAttrDesc()
    fromsection = TagAttrDesc()
    tosection = TagAttrDesc()
    onlysection = TagAttrDesc()

    def __init__(self, text='<pages />'):
        """Initializer."""
        m = self.pat_tag.search(text)
        if m is None:
            raise ValueError(f'Invalid text={text}')

        tag = m['attrs']
        matches = list(self.pat_attr.finditer(tag))
        positions = [m.span()[0] for m in matches] + [len(tag)]

        for begin, end in pairwise(positions):
            attribute = tag[begin:end - 1]
            attr, _, value = attribute.partition('=')
            if attr == 'from':
                attr = 'f' + attr
            setattr(self, attr, value)

    @classmethod
    def get_descriptors(cls):
        """Get TagAttrDesc descriptors."""
        res = {k: v for k, v in cls.__dict__.items()
               if isinstance(v, TagAttrDesc)}
        return res

    def __contains__(self, attr):
        return getattr(self, attr) is not None

    def __str__(self):
        descriptors = self.get_descriptors().items()
        attrs = [v.attrs.get(self) for k, v in descriptors
                 if v.attrs.get(self) is not None]
        attrs = ' '.join(str(attr) for attr in attrs)
        return f'<pages {attrs} />' if attrs else '<pages />'

    def __repr__(self):
        return f"{self.__class__.__name__}('{self}')"


def decompose(fn: Callable) -> Callable:  # type: ignore
    """Decorator for ProofreadPage.

    Decompose text if needed and recompose text.
    """
    def wrapper(self: 'ProofreadPage', *args: Any, **kwargs: Any) -> Any:
        if not hasattr(self, '_full_header'):
            self._decompose_page()
        _res = fn(self, *args, **kwargs)
        self._compose_page()
        return _res

    return wrapper


def check_if_cached(fn: Callable) -> Callable:  # type: ignore
    """Decorator for IndexPage to ensure data is cached."""
    def wrapper(self: 'IndexPage', *args: Any, **kwargs: Any) -> Any:
        if self._cached is False:
            self._get_page_mappings()
        return fn(self, *args, **kwargs)

    return wrapper


class FullHeader:

    """Header of a ProofreadPage object."""

    p_header = re.compile(
        r'<pagequality level="(?P<ql>\d)" user="(?P<user>.*?)" />'
        r'(?P<has_div><div class="pagetext">)?(?P<header>.*)',
        re.DOTALL)

    TEMPLATE_V1 = ('<pagequality level="{0.ql}" user="{0.user}" />'
                   '<div class="pagetext">{0.header}\n\n\n')
    TEMPLATE_V2 = ('<pagequality level="{0.ql}" user="{0.user}" />'
                   '{0.header}')

    def __init__(self, text: Optional[str] = None) -> None:
        """Initializer."""
        self._text = text or ''
        self._has_div = True

        m = self.p_header.search(self._text)
        if m:
            self.ql = int(m['ql'])
            self.user = m['user']
            self.header = m['header']
            if not m['has_div']:
                self._has_div = False
        else:
            self.ql = ProofreadPage.NOT_PROOFREAD
            self.user = ''
            self.header = ''

    def __str__(self) -> str:
        """Return a string representation."""
        if self._has_div:
            return FullHeader.TEMPLATE_V1.format(self)
        return FullHeader.TEMPLATE_V2.format(self)


class ProofreadPage(pywikibot.Page):

    """ProofreadPage page used in Mediawiki ProofreadPage extension."""

    WITHOUT_TEXT = 0
    NOT_PROOFREAD = 1
    PROBLEMATIC = 2
    PROOFREAD = 3
    VALIDATED = 4

    PROOFREAD_LEVELS = [
        WITHOUT_TEXT,
        NOT_PROOFREAD,
        PROBLEMATIC,
        PROOFREAD,
        VALIDATED,
    ]

    _FMT = ('{0.open_tag}{0._full_header}{0.close_tag}'
            '{0._body}'
            '{0.open_tag}{0._footer}%s{0.close_tag}')

    open_tag = '<noinclude>'
    close_tag = '</noinclude>'
    p_open = re.compile(r'<noinclude>')
    p_close = re.compile(r'(</div>|\n\n\n)?</noinclude>')
    p_close_no_div = re.compile('</noinclude>')  # V2 page format.

    # phetools ocr utility
    _HOCR_CMD = ('https://phetools.toolforge.org/hocr_cgi.py?'
                 'cmd=hocr&book={book}&lang={lang}&user={user}')

    _OCR_CMD = ('https://phetools.toolforge.org/ocr.php?'
                'cmd=ocr&url={url_image}&lang={lang}&user={user}')

    # Wikimedia OCR utility
    _WMFOCR_CMD = ('https://ocr.wmcloud.org/api.php?engine=tesseract&'
                   'langs[]={lang}&image={url_image}&uselang={lang}')

    # googleOCR ocr utility
    _GOCR_CMD = ('https://ocr.wmcloud.org/api.php?engine=google&'
                 'langs[]={lang}&image={url_image}')

    _MULTI_PAGE_EXT = ['djvu', 'pdf']

    _PHETOOLS = 'phetools'
    _WMFOCR = 'wmfOCR'
    _GOOGLE_OCR = 'googleOCR'
    _OCR_CMDS = {_PHETOOLS: _OCR_CMD,
                 _WMFOCR: _WMFOCR_CMD,
                 _GOOGLE_OCR: _GOCR_CMD,
                 }
    _OCR_METHODS = list(_OCR_CMDS.keys())

    def __init__(self, source: PageSourceType, title: str = '') -> None:
        """Instantiate a ProofreadPage object.

        :raise UnknownExtensionError: source Site has no ProofreadPage
            Extension.
        """
        if not isinstance(source, pywikibot.site.BaseSite):
            site = source.site
        else:
            site = source
        super().__init__(source, title)
        if self.namespace() != site.proofread_page_ns:
            raise ValueError('Page {} must belong to {} namespace'
                             .format(self.title(), site.proofread_page_ns))
        # Ensure that constants are in line with Extension values.
        level_list = list(self.site.proofread_levels)
        if level_list != self.PROOFREAD_LEVELS:
            raise ValueError('QLs do not match site values: {} != {}'
                             .format(level_list, self.PROOFREAD_LEVELS))

        self._base, self._base_ext, self._num = self._parse_title()
        self._multi_page = self._base_ext in self._MULTI_PAGE_EXT

    @property
    def _fmt(self) -> str:
        return self._FMT % ('</div>' if self._full_header._has_div else '')

    def _parse_title(self) -> Tuple[str, str, Optional[int]]:
        """Get ProofreadPage base title, base extension and page number.

        Base title is the part of title before the last '/', if any,
        or the whole title if no '/' is present.

        Extension is the extension of the base title.

        Page number is the part of title after the last '/', if any,
        or None if no '/' is present.

        E.g. for title 'Page:Popular Science Monthly Volume 1.djvu/12':
        - base = 'Popular Science Monthly Volume 1.djvu'
        - extension = 'djvu'
        - number = 12

        E.g. for title 'Page:Original Waltzing Matilda manuscript.jpg':
        - base = 'Original Waltzing Matilda manuscript.jpg'
        - extension = 'jpg'
        - number = None

        :return: (base, ext, num).
        """
        left, sep, right = self.title(with_ns=False).rpartition('/')
        num: Optional[int] = None

        if sep:
            base = left
            try:
                num = int(right)
            except ValueError:
                raise InvalidTitleError('{} contains invalid index {!r}'
                                        .format(self, right))
        else:
            base = right

        left, sep, right = base.rpartition('.')
        ext = right if sep else ''

        return base, ext, num

    @property
    def index(self) -> Optional['IndexPage']:
        """Get the Index page which contains ProofreadPage.

        If there are many Index pages link to this ProofreadPage, and
        the ProofreadPage is titled Page:<index title>/<page number>,
        the Index page with the same title will be returned.
        Otherwise None is returned in the case of multiple linked Index pages.

        To force reload, delete index and call it again.

        :return: the Index page for this ProofreadPage
        """
        if not hasattr(self, '_index'):
            index_ns = self.site.proofread_index_ns
            what_links_here = [IndexPage(page) for page in
                               set(self.getReferences(namespaces=index_ns))]

            if not what_links_here:
                self._index: _IndexType = (None, [])
            elif len(what_links_here) == 1:
                self._index = (what_links_here.pop(), [])
            else:
                self._index = (None, what_links_here)
                # Try to infer names from page titles.
                if self._num is not None:
                    for page in what_links_here:
                        if page.title(with_ns=False) == self._base:
                            what_links_here.remove(page)
                            self._index = (page, what_links_here)
                            break

        index_page, others = self._index
        if others:
            pywikibot.warning(f'{self} linked to several Index pages.')
            pywikibot.info('{}{!s}'.format(' ' * 9, [index_page] + others))

            if index_page:
                pywikibot.info(
                    '{}Selected Index: {}'.format(' ' * 9, index_page))
                pywikibot.info('{}remaining: {!s}'.format(' ' * 9, others))

        if not index_page:
            pywikibot.warning('Page {} is not linked to any Index page.'
                              .format(self))

        return index_page

    @index.setter
    def index(self, value: 'IndexPage') -> None:
        if not isinstance(value, IndexPage):
            raise TypeError('value {} must be an IndexPage object.'
                            .format(value))
        self._index = (value, [])

    @index.deleter
    def index(self) -> None:
        if hasattr(self, '_index'):
            del self._index

    @property
    def quality_level(self) -> int:
        """Return the quality level of this page when it is retrieved from API.

        This is only applicable if contentmodel equals 'proofread-page'.
        None is returned otherwise.

        This property is read-only and is applicable only when page is loaded.
        If quality level is overwritten during page processing, this property
        is no longer necessarily aligned with the new value.

        In this way, no text parsing is necessary to check quality level when
        fetching a page.
        """
        # TODO: align this value with ProofreadPage.ql

        if (self.content_model == 'proofread-page'
                and hasattr(self, '_quality')):
            return int(self._quality)  # type: ignore[attr-defined]
        return self.ql

    @property  # type: ignore[misc]
    @decompose
    def ql(self) -> int:
        """Return page quality level."""
        return self._full_header.ql

    @ql.setter  # type: ignore[misc]
    @decompose
    def ql(self, value: int) -> None:
        if value not in self.site.proofread_levels:
            raise ValueError('Not valid QL value: {} (legal values: {})'
                             .format(value, list(self.site.proofread_levels)))
        # TODO: add logic to validate ql value change, considering
        # site.proofread_levels.
        self._full_header.ql = value

    @property  # type: ignore[misc]
    @decompose
    def user(self) -> str:
        """Return user in page header."""
        return self._full_header.user

    @user.setter  # type: ignore[misc]
    @decompose
    def user(self, value: str) -> None:
        self._full_header.user = value

    @property  # type: ignore[misc]
    @decompose
    def status(self) -> Optional[str]:
        """Return Proofread Page status."""
        try:
            return self.site.proofread_levels[self.ql]
        except KeyError:
            pywikibot.warning('Not valid status set for {}: quality level = {}'
                              .format(self.title(as_link=True), self.ql))
        return None

    def without_text(self) -> None:
        """Set Page QL to "Without text"."""
        self.ql = self.WITHOUT_TEXT  # type: ignore[misc]

    def problematic(self) -> None:
        """Set Page QL to "Problematic"."""
        self.ql = self.PROBLEMATIC  # type: ignore[misc]

    def not_proofread(self) -> None:
        """Set Page QL to "Not Proofread"."""
        self.ql = self.NOT_PROOFREAD  # type: ignore[misc]

    def proofread(self) -> None:
        """Set Page QL to "Proofread"."""
        # TODO: check should be made to be consistent with Proofread Extension
        self.ql = self.PROOFREAD  # type: ignore[misc]

    def validate(self) -> None:
        """Set Page QL to "Validated"."""
        # TODO: check should be made to be consistent with Proofread Extension
        self.ql = self.VALIDATED  # type: ignore[misc]

    @property  # type: ignore[misc]
    @decompose
    def header(self) -> str:
        """Return editable part of Page header."""
        return self._full_header.header

    @header.setter  # type: ignore[misc]
    @decompose
    def header(self, value: str) -> None:
        self._full_header.header = value

    @property  # type: ignore[misc]
    @decompose
    def body(self) -> str:
        """Return Page body."""
        return self._body

    @body.setter  # type: ignore[misc]
    @decompose
    def body(self, value: str) -> None:
        self._body = value

    @property  # type: ignore[misc]
    @decompose
    def footer(self) -> str:
        """Return Page footer."""
        return self._footer

    @footer.setter  # type: ignore[misc]
    @decompose
    def footer(self, value: str) -> None:
        self._footer = value

    def _create_empty_page(self) -> None:
        """Create empty page."""
        self._full_header = FullHeader()
        self._body = ''
        self._footer = ''
        self.user = self.site.username()  # type: ignore[misc]
        self._compose_page()

    @property
    def text(self) -> str:
        """Override text property.

        Preload text returned by EditFormPreloadText to preload non-existing
        pages.
        """
        # Text is already cached.
        if getattr(self, '_text', None) is not None:
            return self._text  # type: ignore[return-value]

        if self.exists():
            # If page exists, load it.
            return super().text

        # If page does not exist, preload it.
        self._text = self.preloadText()
        self.user = self.site.username()  # type: ignore[misc]
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Update current text.

        Mainly for use within the class, called by other methods.
        Use self.header, self.body and self.footer to set page content,

        :param value: New value or None

        :raise Error: the page is not formatted according to ProofreadPage
            extension.
        """
        self._text = value
        if self._text:
            self._decompose_page()
        else:
            self._create_empty_page()

    @text.deleter
    def text(self) -> None:
        if hasattr(self, '_text'):
            del self._text

    def _decompose_page(self) -> None:
        """Split Proofread Page text in header, body and footer.

        :raise Error: the page is not formatted according to ProofreadPage
            extension.
        """
        def _assert_len(len_oq: int, len_cq: int, title: str) -> None:
            if (len_oq != len_cq) or (len_oq < 2 or len_cq < 2):
                raise Error(f'ProofreadPage {title}: invalid format')

        # Property force page text loading.
        text = self.text
        if not text:
            self._create_empty_page()
            return

        _title = self.title(as_link=True)

        open_queue = list(self.p_open.finditer(text))
        close_queue = list(self.p_close.finditer(text))
        _assert_len(len(open_queue), len(close_queue), _title)

        f_open, f_close = open_queue[0], close_queue[0]
        self._full_header = FullHeader(text[f_open.end():f_close.start()])

        # check version of page format and in case recompute last match,
        # in order not to include </div>.
        if not self._full_header._has_div:
            close_queue = list(self.p_close_no_div.finditer(text))
            _assert_len(len(open_queue), len(close_queue), _title)

        l_open, l_close = open_queue[-1], close_queue[-1]
        self._footer = text[l_open.end():l_close.start()]

        self._body = text[f_close.end():l_open.start()]

    def _compose_page(self) -> str:
        """Compose Proofread Page text from header, body and footer."""
        self._text = self._fmt.format(self)
        return self._text

    def _page_to_json(self) -> str:
        """Convert page text to json format.

        This is the format accepted by action=edit specifying
        contentformat=application/json. This format is recommended to save the
        page, as it is not subject to possible errors done in composing the
        wikitext header and footer of the page or changes in the ProofreadPage
        extension format.
        """
        page_dict = {'header': self.header,
                     'body': self.body,
                     'footer': self.footer,
                     'level': {'level': self.ql, 'user': self.user},
                     }
        # Ensure_ascii=False returns a unicode.
        return json.dumps(page_dict, ensure_ascii=False)

    def save(self, *args: Any, **kwargs: Any) -> None:  # See Page.save().
        """Save page content after recomposing the page."""
        kwargs['summary'] = self.pre_summary + kwargs.get('summary', '')
        # Save using contentformat='application/json'.
        kwargs['contentformat'] = 'application/json'
        kwargs['contentmodel'] = 'proofread-page'
        text = self._page_to_json()
        super().save(*args, text=text, **kwargs)

    @property
    def pre_summary(self) -> str:
        """Return trailing part of edit summary.

        The edit summary shall be appended to pre_summary to highlight
        Status in the edit summary on wiki.
        """
        return f'/* {self.status} */ '

    @property
    @cached
    def url_image(self) -> str:
        """Get the file url of the scan of ProofreadPage.

        :return: file url of the scan ProofreadPage or None.

        :raises Exception: in case of http errors
        :raises ImportError: if bs4 is not installed, _bs4_soup() will raise
        :raises ValueError: in case of no prp_page_image src found for scan
        """
        # wrong link fails with various possible Exceptions.
        if self.exists():
            url = self.full_url()
        else:
            path = 'w/index.php?title={}&action=edit&redlink=1'
            url = self.site.base_url(path.format(self.title(as_url=True)))

        try:
            response = http.fetch(url, charset='utf-8')
        except Exception:
            pywikibot.error(f'Error fetching HTML for {self}.')
            raise

        soup = _bs4_soup(response.text)  # type: ignore

        try:
            url_image = soup.find(class_='prp-page-image')
            # if None raises AttributeError
            url_image = url_image.find('img')
            # if None raises TypeError.
            url_image = url_image['src']
        except (TypeError, AttributeError):
            raise ValueError('No prp-page-image src found for {}.'
                             .format(self))
        else:
            url_image = 'https:' + url_image

        return url_image

    def _ocr_callback(self, cmd_uri: str,
                      parser_func: Optional[Callable[[str], str]] = None,
                      ocr_tool: Optional[str] = None
                      ) -> Tuple[bool, Union[str, Exception]]:
        """OCR callback function.

        :return: tuple (error, text [error description in case of error]).
        """
        def identity(x: Any) -> Any:
            return x

        if not cmd_uri:
            raise ValueError('Parameter cmd_uri is mandatory.')

        if parser_func is None:
            parser_func = identity

        if not callable(parser_func):
            raise TypeError('Keyword parser_func must be callable.')

        if ocr_tool not in self._OCR_METHODS:
            raise TypeError(
                "ocr_tool must be in {}, not '{}'."
                .format(self._OCR_METHODS, ocr_tool))

        # wrong link fail with Exceptions
        for retry in range(5, 30, 5):
            pywikibot.debug(f'{ocr_tool}: get URI {cmd_uri!r}')
            try:
                response = http.fetch(cmd_uri)
            except ReadTimeout as e:
                pywikibot.warning(f'ReadTimeout {cmd_uri}: {e}')
            except Exception as e:
                pywikibot.error(f'"{cmd_uri}": {e}')
                return True, e
            else:
                pywikibot.debug(f'{ocr_tool}: {response.text}')
                break

            pywikibot.warning(f'retrying in {retry} seconds ...')
            time.sleep(retry)
        else:
            return True, ReadTimeout('ReadTimeout: Could not perform OCR')

        if HTTPStatus.BAD_REQUEST <= response.status_code < 600:
            return True, f'Http response status {response.status_code}'

        data = response.json()

        if ocr_tool == self._PHETOOLS:  # phetools
            assert 'error' in data, f'Error from phetools: {data}'
            assert data['error'] in [0, 1, 2, 3], \
                f'Error from phetools: {data}'
            error, _text = bool(data['error']), data['text']
        else:  # googleOCR
            if 'error' in data:
                error, _text = True, data['error']
            else:
                error, _text = False, data['text']

        if error:
            pywikibot.error(f'OCR query {cmd_uri}: {_text}')
            return error, _text
        return error, parser_func(_text)

    def _do_hocr(self) -> Tuple[bool, Union[str, Exception]]:
        """Do hocr using https://phetools.toolforge.org/hocr_cgi.py?cmd=hocr.

        This is the main method for 'phetools'.
        Fallback method is ocr.

        :raise ImportError: if bs4 is not installed, _bs4_soup() will raise
        """
        def parse_hocr_text(txt: str) -> str:
            """Parse hocr text."""
            soup = _bs4_soup(txt)  # type: ignore

            res = []
            for _ocr_page in soup.find_all(class_='ocr_page'):
                for area in soup.find_all(class_='ocr_carea'):
                    for par in area.find_all(class_='ocr_par'):
                        for line in par.find_all(class_='ocr_line'):
                            res.append(line.get_text())
                        res.append('\n')
            return ''.join(res)

        params = {
            'book': self.title(as_url=True, with_ns=False),
            'lang': self.site.lang,
            'user': self.site.user(),
        }
        cmd_uri = self._HOCR_CMD.format_map(params)

        return self._ocr_callback(cmd_uri,
                                  parser_func=parse_hocr_text,
                                  ocr_tool=self._PHETOOLS)

    def _do_ocr(self, ocr_tool: Optional[str] = None
                ) -> Tuple[bool, Union[str, Exception]]:
        """Do ocr using specified ocr_tool method."""
        try:
            url_image = self.url_image
        except ValueError:
            error_text = f'No prp-page-image src found for {self}.'
            pywikibot.error(error_text)
            return True, error_text

        if ocr_tool is None:
            msg = 'ocr_tool required, must be among {}'
            raise TypeError(msg.format(self._OCR_METHODS))

        try:
            cmd_fmt = self._OCR_CMDS[ocr_tool]
        except KeyError:
            raise TypeError(
                "ocr_tool must be in {}, not '{}'."
                .format(self._OCR_METHODS, ocr_tool))

        params = {
            'url_image': url_image,
            'lang': self.site.lang,
            'user': self.site.user(),
        }
        cmd_uri = cmd_fmt.format_map(params)

        return self._ocr_callback(cmd_uri, ocr_tool=ocr_tool)

    def ocr(self, ocr_tool: Optional[str] = None) -> str:
        """Do OCR of ProofreadPage scan.

        The text returned by this function shall be assigned to self.body,
        otherwise the ProofreadPage format will not be maintained.

        It is the user's responsibility to reset quality level accordingly.

        :param ocr_tool: 'phetools', 'wmfOCR' or 'googleOCR';
            default is 'phetools'

        :return: OCR text for the page.

        :raise TypeError: wrong ocr_tool keyword arg.
        :raise ValueError: something went wrong with OCR process.
        """
        if ocr_tool is None:  # default value
            ocr_tool = self._PHETOOLS

        if ocr_tool not in self._OCR_METHODS:
            raise TypeError(
                "ocr_tool must be in {}, not '{}'."
                .format(self._OCR_METHODS, ocr_tool))

        # if _multi_page, try _do_hocr() first and fall back to _do_ocr()
        if ocr_tool == self._PHETOOLS and self._multi_page:
            error, text = self._do_hocr()
            if not error and isinstance(text, str):
                return text
            pywikibot.warning('{}: phetools hocr failed, falling back to ocr.'
                              .format(self))

        error, text = self._do_ocr(ocr_tool=ocr_tool)

        if not error and isinstance(text, str):
            return text
        raise ValueError(
            f'{self}: not possible to perform OCR. {text}')


class PurgeRequest(Request):

    """Subclass of Request which skips the check on write rights.

    Workaround for :phab:`T128994`.
    """  # TODO: remove once bug is fixed.

    def __init__(self, **kwargs: Any) -> None:
        """Monkeypatch action in Request initializer."""
        action = kwargs['parameters']['action']
        kwargs['parameters']['action'] = 'dummy'
        super().__init__(**kwargs)
        self.action = action
        self.update({'action': action})


class IndexPage(pywikibot.Page):

    """Index Page page used in Mediawiki ProofreadPage extension."""

    INDEX_TEMPLATE = ':MediaWiki:Proofreadpage_index_template'

    def __init__(self, source: PageSourceType, title: str = '') -> None:
        """Instantiate an IndexPage object.

        In this class:
        page number is the number in the page title in the Page namespace, if
        the wikisource site adopts this convention (e.g. page_number is 12
        for Page:Popular Science Monthly Volume 1.djvu/12) or the sequential
        number of the pages linked from the index section in the Index page
        if the index is built via transclusion of a list of pages (e.g. like
        on de wikisource).
        page label is the label associated with a page in the Index page.

        This class provides methods to get pages contained in Index page,
        and relative page numbers and labels by means of several helper
        functions.

        It also provides a generator to pages contained in Index page, with
        possibility to define range, filter by quality levels and page
        existence.

        :raise UnknownExtensionError: source Site has no ProofreadPage
            Extension.
        :raise ImportError: bs4 is not installed.
        """
        # Check if BeautifulSoup is imported.
        if isinstance(BeautifulSoup, ImportError):
            raise BeautifulSoup

        if not isinstance(source, pywikibot.site.BaseSite):
            site = source.site
        else:
            site = source
        super().__init__(source, title)
        if self.namespace() != site.proofread_index_ns:
            raise ValueError('Page {} must belong to {} namespace'
                             .format(self.title(), site.proofread_index_ns))

        self._all_page_links = {}

        for page in self._get_prp_index_pagelist():
            self._all_page_links[page.title()] = page

        self._cached = False

    def _get_prp_index_pagelist(self):
        """Get all pages in an IndexPage page list.

        .. note:: This method is called by initializer and should not be used.

        .. seealso::
           `ProofreadPage Index Pagination API
           <https://www.mediawiki.org/wiki/Extension:ProofreadPage/Index_pagination_API>`_

        :meta public:
        """
        site = self.site
        ppi_args = {}
        if hasattr(self, '_pageid'):
            ppi_args['prppiipageid'] = str(self._pageid)
        else:
            ppi_args['prppiititle'] = self.title().encode(site.encoding())

        ppi_gen = site._generator(ListGenerator, 'proofreadpagesinindex',
                                  **ppi_args)
        for item in ppi_gen:
            page = ProofreadPage(site, item['title'])
            page.page_offset = item['pageoffset']
            page.index = self
            yield page

    @staticmethod
    def _parse_redlink(href: str) -> Optional[str]:
        """Parse page title when link in Index is a redlink."""
        p_href = re.compile(
            r'/w/index\.php\?title=(.+?)&action=edit&redlink=1')
        title = p_href.search(href)
        if title:
            return title[1].replace('_', ' ')
        return None

    def save(self, *args: Any, **kwargs: Any) -> None:  # See Page.save().
        """
        Save page after validating the content.

        Trying to save any other content fails silently with a parameterless
        INDEX_TEMPLATE being saved.
        """
        if not self.has_valid_content():
            raise OtherPageSaveError(
                self, 'An IndexPage must consist only of a single call to '
                '{{%s}}.' % self.INDEX_TEMPLATE)
        kwargs['contentformat'] = 'text/x-wiki'
        kwargs['contentmodel'] = 'proofread-index'
        super().save(*args, **kwargs)

    def has_valid_content(self) -> bool:
        """Test page only contains a single call to the index template."""
        text = self.text

        if not text.startswith('{{' + self.INDEX_TEMPLATE):
            return False

        # Discard possible categories after INDEX_TEMPLATE
        categories = textlib.getCategoryLinks(text, self.site)
        for cat in categories:
            text = text.replace('\n' + cat.title(as_link=True), '')

        if not text.endswith('}}'):
            return False

        # Discard all inner templates as only top-level ones matter
        templates = textlib.extract_templates_and_params_regex_simple(text)
        if len(templates) != 1 or templates[0][0] != self.INDEX_TEMPLATE:
            # Only a single call to the INDEX_TEMPLATE is allowed
            return False

        return True

    def purge(self) -> None:  # type: ignore[override]
        """Overwrite purge method.

        Instead of a proper purge action, use PurgeRequest, which
        skips the check on write rights.
        """
        # TODO: This is a workaround for T128994. Remove once bug is fixed.

        params = {'action': 'purge', 'titles': [self.title()]}
        request = PurgeRequest(site=self.site, parameters=params)
        rawdata = request.submit()
        error_message = f'Purge action failed for {self}'
        assert 'purge' in rawdata, error_message
        assert 'purged' in rawdata['purge'][0], error_message

    def _get_page_mappings(self) -> None:
        """Associate label and number for each page linked to the index."""
        # Clean cache, if any.
        self._page_from_numbers = {}
        self._numbers_from_page: Dict[pywikibot.page.Page, int] = {}
        self._page_numbers_from_label: Dict[str, Set[int]] = {}
        self._pages_from_label: PagesFromLabelType = {}
        self._labels_from_page_number: Dict[int, str] = {}
        self._labels_from_page: Dict[pywikibot.page.Page, str] = {}
        self._soup = _bs4_soup(self.get_parsed_page(True))  # type: ignore
        # Do not search for "new" here, to avoid to skip purging if links
        # to non-existing pages are present.
        attrs = {'class': re.compile('prp-pagequality-[0-4]')}

        # Search for attribute "prp-pagequality" in tags:
        # Existing pages:
        # <a href="/wiki/Page:xxx.djvu/n"
        #    class="prp-pagequality-0 quality0" or
        #    class="prp-index-pagelist-page prp-pagequality-0 quality0"
        #    title="Page:xxx.djvu/n">m
        # </a>
        # Non-existing pages:
        # <a href="/w/index.php?title=xxx&amp;action=edit&amp;redlink=1"
        #    class="new prp-index-pagelist-page"
        #    title="Page:xxx.djvu/n (page does not exist)">m
        # </a>

        # Try to purge or raise ValueError.
        found = self._soup.find_all('a', attrs=attrs)
        attrs = {'class': re.compile('prp-pagequality-[0-4]|'
                                     'new prp-index-pagelist-page|'
                                     'prp-index-pagelist-page')
                 }
        if not found:
            self.purge()
            self._soup = _bs4_soup(self.get_parsed_page(True))  # type: ignore
            if not self._soup.find_all('a', attrs=attrs):
                raise ValueError(
                    'Missing class="qualityN prp-pagequality-N" or '
                    'class="new" in: {}.'.format(self))

        page_cnt = 0
        for a_tag in self._soup.find_all('a', attrs=attrs):
            label = a_tag.text.lstrip('0')  # Label is not converted to int.
            class_ = a_tag.get('class')
            href = a_tag.get('href')

            if 'new' in class_:
                title = self._parse_redlink(href)  # non-existing page
                if title is None:  # title not conforming to required format
                    continue
                title = unquote(title)
            else:
                title = a_tag.get('title')   # existing page

            assert title is not None

            try:
                page = self._all_page_links[title]
                page_cnt += 1
            except KeyError:
                continue

            # In order to avoid to fetch other Page:title links outside
            # the Pages section of the Index page; these should hopefully be
            # the first ones, so if they start repeating, we are done.
            if page in self._labels_from_page:
                break

            # Sanity check if WS site use page convention name/number.
            if page._num is not None:
                assert page_cnt == int(page._num), (
                    'Page number {} not recognised as page {}.'
                    .format(page_cnt, title))

            # Mapping: numbers <-> pages.
            self._page_from_numbers[page_cnt] = page
            self._numbers_from_page[page] = page_cnt
            # Mapping: numbers/pages as keys, labels as values.
            self._labels_from_page_number[page_cnt] = label
            self._labels_from_page[page] = label
            # Reverse mapping: labels as keys, numbers/pages as values.
            self._page_numbers_from_label.setdefault(
                label, set()).add(page_cnt)
            self._pages_from_label.setdefault(label, set()).add(page)

        # Sanity check: all links to Page: ns must have been considered.
        assert (set(self._labels_from_page)
                == set(self._all_page_links.values()))

        # Info cached.
        self._cached = True

    @property  # type: ignore[misc]
    @check_if_cached
    def num_pages(self) -> int:
        """Return total number of pages in Index.

        :return: total number of pages in Index
        """
        return len(self._page_from_numbers)

    def page_gen(self, start: int = 1,
                 end: Optional[int] = None,
                 filter_ql: Optional[Sequence[int]] = None,
                 only_existing: bool = False,
                 content: bool = True
                 ) -> Iterable['pywikibot.page.Page']:
        """Return a page generator which yields pages contained in Index page.

        Range is [start ... end], extremes included.

        :param start: first page, defaults to 1
        :param end: num_pages if end is None
        :param filter_ql: filters quality levels
                          if None: all but 'Without Text'.
        :param only_existing: yields only existing pages.
        :param content: preload content.
        """
        if end is None:
            end = self.num_pages

        if not 1 <= start <= end <= self.num_pages:
            raise ValueError('start={}, end={} are not in valid range (1, {})'
                             .format(start, end, self.num_pages))

        # All but 'Without Text'
        if filter_ql is None:
            filter_ql = list(self.site.proofread_levels)
            filter_ql.remove(ProofreadPage.WITHOUT_TEXT)

        gen = (self.get_page(i) for i in range(start, end + 1))
        if content:
            gen = self.site.preloadpages(gen)
        # Filter by QL.
        gen = (p for p in gen if p.ql in filter_ql)
        # Yield only existing.
        if only_existing:
            gen = (p for p in gen if p.exists())
        # Decorate and sort by page number because preloadpages does not
        # guarantee order.
        # TODO: remove if preloadpages will guarantee order.
        gen = ((self.get_number(p), p) for p in gen)
        gen = (p for n, p in sorted(gen))

        return gen

    @check_if_cached
    def get_label_from_page(self, page: 'pywikibot.page.Page') -> str:
        """Return 'page label' for page.

        There is a 1-to-1 correspondence (each page has a label).

        :param page: Page instance
        :return: page label
        """
        try:
            return self._labels_from_page[page]
        except KeyError:
            raise KeyError(f'Invalid Page: {page}.')

    @check_if_cached
    def get_label_from_page_number(self, page_number: int) -> str:
        """Return page label from page number.

        There is a 1-to-1 correspondence (each page has a label).

        :return: page label
        """
        try:
            return self._labels_from_page_number[page_number]
        except KeyError:
            raise KeyError('Page number ".../{}" not in range.'
                           .format(page_number))

    @staticmethod
    def _get_from_label(mapping_dict: Dict[str, Any],
                        label: Union[int, str]) -> Any:
        """Helper function to get info from label."""
        # Convert label to string if an integer is passed.
        if isinstance(label, int):
            label = str(label)

        try:
            return mapping_dict[label]
        except KeyError:
            raise KeyError(f'No page has label: "{label}".')

    @check_if_cached
    def get_page_number_from_label(self, label: str = '1') -> str:
        """Return page number from page label.

        There is a 1-to-many correspondence (a label can be the same for
        several pages).

        :return: set containing page numbers corresponding to page label.
        """
        return self._get_from_label(self._page_numbers_from_label, label)

    @check_if_cached
    def get_page_from_label(self, label: str = '1') -> str:
        """Return page number from page label.

        There is a 1-to-many correspondence (a label can be the same for
        several pages).

        :return: set containing pages corresponding to page label.
        """
        return self._get_from_label(self._pages_from_label, label)

    @check_if_cached
    def get_page(self, page_number: int) -> 'pywikibot.page.Page':
        """Return a page object from page number."""
        try:
            return self._page_from_numbers[page_number]
        except KeyError:
            raise KeyError(f'Invalid page number: {page_number}.')

    @check_if_cached
    def pages(self) -> List['pywikibot.page.Page']:
        """Return the list of pages in Index, sorted by page number.

        :return: list of pages
        """
        return [self._page_from_numbers[i]
                for i in range(1, self.num_pages + 1)]

    @check_if_cached
    def get_number(self, page: 'pywikibot.page.Page') -> int:
        """Return a page number from page object."""
        try:
            return self._numbers_from_page[page]
        except KeyError:
            raise KeyError(f'Invalid page: {page}.')
