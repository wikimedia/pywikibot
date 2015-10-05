# -*- coding: utf-8  -*-
"""
Objects representing objects used with ProofreadPage Extension.

The extension is supported by MW 1.21+.

This module includes objects:
* ProofreadPage(Page)
* FullHeader

"""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import json
import re

try:
    from bs4 import BeautifulSoup
except ImportError as e:
    BeautifulSoup = e

import pywikibot


class FullHeader(object):

    """Header of a ProofreadPage object."""

    p_header = re.compile(
        r'<pagequality level="(?P<ql>\d)" user="(?P<user>.*?)" />'
        r'<div class="pagetext">(?P<header>.*)',
        re.DOTALL)

    _template = ('<pagequality level="{0.ql}" user="{0.user}" />'
                 '<div class="pagetext">{0.header}\n\n\n')

    def __init__(self, text=None):
        """Constructor."""
        self._text = text or ''

        m = self.p_header.search(self._text)
        if m:
            self.ql = int(m.group('ql'))
            self.user = m.group('user')
            self.header = m.group('header')
        else:
            self.ql = ProofreadPage.NOT_PROOFREAD
            self.user = ''
            self.header = ''

    def __str__(self):
        """Return a string representation."""
        return self._template.format(self)


class ProofreadPage(pywikibot.Page):

    """ProofreadPage page used in Mediawiki ProofreadPage extension."""

    WITHOUT_TEXT = 0
    NOT_PROOFREAD = 1
    PROBLEMATIC = 2
    PROOFREAD = 3
    VALIDATED = 4

    open_tag = '<noinclude>'
    close_tag = '</noinclude>'
    p_open = re.compile(r'<noinclude>')
    p_close = re.compile(r'(</div>|\n\n\n)?</noinclude>')

    def __init__(self, source, title=''):
        """Instantiate a ProofreadPage object.

        Raises UnknownExtension if source Site has no ProofreadPage Extension.
        """
        if not isinstance(source, pywikibot.site.BaseSite):
            site = source.site
        else:
            site = source
        ns = site.proofread_page_ns
        super(ProofreadPage, self).__init__(source, title, ns=ns)
        if self.namespace() != site.proofread_page_ns:
            raise ValueError('Page %s must belong to %s namespace'
                             % (self.title(), ns))

    def decompose(fn):
        """Decorator.

        Decompose text if needed and recompose text.
        """
        def wrapper(obj, *args, **kwargs):
            if not hasattr(obj, '_full_header'):
                obj._decompose_page()
            _res = fn(obj, *args, **kwargs)
            obj._compose_page()
            return _res
        return wrapper

    @property
    @decompose
    def ql(self):
        """Return page quality level."""
        return self._full_header.ql

    @ql.setter
    @decompose
    def ql(self, value):
        """Set page quality level."""
        if value not in self.site.proofread_levels:
            raise ValueError('Not valid QL value: %s (legal values: %s)'
                             % (value, self.site.proofread_levels))
        # TODO: add logic to validate ql value change, considering
        # site.proofread_levels.
        self._full_header.ql = value

    @property
    @decompose
    def user(self):
        """Return user in page header."""
        return self._full_header.user

    @user.setter
    @decompose
    def user(self, value):
        """Set user in page header."""
        self._full_header.user = value

    @property
    @decompose
    def status(self):
        """Return Proofread Page status."""
        try:
            return self.site.proofread_levels[self.ql]
        except KeyError:
            pywikibot.warning('Not valid status set for %s: quality level = %s'
                              % (self.title(asLink=True), self.ql))
            return None

    def without_text(self):
        """Set Page QL to "Without text"."""
        self.ql = self.WITHOUT_TEXT

    def problematic(self):
        """Set Page QL to "Problematic"."""
        self.ql = self.PROBLEMATIC

    def not_proofread(self):
        """Set Page QL to "Not Proofread"."""
        self.ql = self.NOT_PROOFREAD

    def proofread(self):
        """Set Page QL to "Proofread"."""
        # TODO: check should be made to be consistent with Proofread Extension
        self.ql = self.PROOFREAD

    def validate(self):
        """Set Page QL to "Validated"."""
        # TODO: check should be made to be consistent with Proofread Extension
        self.ql = self.VALIDATED

    @property
    @decompose
    def header(self):
        """Return editable part of Page header."""
        return self._full_header.header

    @header.setter
    @decompose
    def header(self, value):
        """Set editable part of Page header."""
        self._full_header.header = value

    @property
    @decompose
    def body(self):
        """Return Page body."""
        return self._body

    @body.setter
    @decompose
    def body(self, value):
        """Set Page body."""
        self._body = value

    @property
    @decompose
    def footer(self):
        """Return Page footer."""
        return self._footer

    @footer.setter
    @decompose
    def footer(self, value):
        """Set Page footer."""
        self._footer = value

    def _create_empty_page(self):
        """Create empty page."""
        self._full_header = FullHeader()
        self._body = ''
        self._footer = ''
        self.user = self.site.username()  # Fill user field in empty header.
        self._compose_page()

    @property
    def text(self):
        """Override text property.

        Preload text returned by EditFormPreloadText to preload non-existing
        pages.
        """
        # Text is already cached.
        if hasattr(self, '_text'):
            return self._text
        # If page does not exist, preload it.
        if self.exists():
            # If page exists, load it.
            super(ProofreadPage, self).text
        else:
            self._text = self.preloadText()
            self.user = self.site.username()  # Fill user field in empty header.
        return self._text

    @text.setter
    def text(self, value):
        """Update current text.

        Mainly for use within the class, called by other methods.
        Use self.header, self.body and self.footer to set page content,

        @param value: New value or None
        @param value: basestring

        Raises:
        exception Error:   the page is not formatted according to ProofreadPage
                           extension.
        """
        self._text = value
        if self._text:
            self._decompose_page()
        else:
            self._create_empty_page()

    @text.deleter
    def text(self):
        """Delete current text."""
        if hasattr(self, '_text'):
            del self._text

    def _decompose_page(self):
        """Split Proofread Page text in header, body and footer.

        Raises:
        exception Error:   the page is not formatted according to ProofreadPage
                           extension.
        """
        # Property force page text loading.
        if not (hasattr(self, '_text') or self.text):
            self._create_empty_page()
            return

        open_queue = list(self.p_open.finditer(self._text))
        close_queue = list(self.p_close.finditer(self._text))

        len_oq = len(open_queue)
        len_cq = len(close_queue)
        if (len_oq != len_cq) or (len_oq < 2 or len_cq < 2):
            raise pywikibot.Error('ProofreadPage %s: invalid format'
                                  % self.title(asLink=True))

        f_open, f_close = open_queue[0], close_queue[0]
        self._full_header = FullHeader(self._text[f_open.end():f_close.start()])

        l_open, l_close = open_queue[-1], close_queue[-1]
        self._footer = self._text[l_open.end():l_close.start()]

        self._body = self._text[f_close.end():l_open.start()]

    def _compose_page(self):
        """Compose Proofread Page text from header, body and footer."""
        fmt = ('{0.open_tag}{0._full_header}{0.close_tag}'
               '{0._body}'
               '{0.open_tag}{0._footer}</div>{0.close_tag}')
        self._text = fmt.format(self)
        return self._text

    def _page_to_json(self):
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

    def save(self, *args, **kwargs):  # See Page.save().
        """Save page content after recomposing the page."""
        summary = kwargs.pop('summary', '')
        summary = self.pre_summary + summary
        # Save using contentformat='application/json'.
        kwargs['contentformat'] = 'application/json'
        kwargs['contentmodel'] = 'proofread-page'
        text = self._page_to_json()
        super(ProofreadPage, self).save(*args, text=text, summary=summary,
                                        **kwargs)

    @property
    def pre_summary(self):
        """Return trailing part of edit summary.

        The edit summary shall be appended to pre_summary to highlight
        Status in the edit summary on wiki.
        """
        return '/* {0.status} */ '.format(self)


class IndexPage(pywikibot.Page):

    """Index Page page used in Mediawiki ProofreadPage extension."""

    # TODO: handle not existing pages when quering labels/nubers?
    # Currently APIError is thrown.
    def __init__(self, source, title=''):
        """Instantiate a IndexPage object.

        In this class:
        page number is the number in the page title in the Page namespace, if
            the wikisource site adopts this convention (e.g. page_number is 12
            for Page:Popular Science Monthly Volume 1.djvu/12) or the sequential
            number of the pages linked from the index section in the Index page
            if the index is built via transclusion of a list of pages (e.g. like
            on de wikisource).
        page label is the label associated with a page in the Index page.

        Raises UnknownExtension if source Site has no ProofreadPage Extension.
        """
        # Check if BeautifulSoup is imported.
        if isinstance(BeautifulSoup, ImportError):
            raise BeautifulSoup

        if not isinstance(source, pywikibot.site.BaseSite):
            site = source.site
        else:
            site = source
        ns = site.proofread_index_ns
        super(IndexPage, self).__init__(source, title, ns=site.proofread_index_ns)
        if self.namespace() != site.proofread_index_ns:
            raise ValueError('Page %s must belong to %s namespace'
                             % (self.title(), ns))

        self._all_page_links = set(
            self.site.pagelinks(self, namespaces=self.site.proofread_page_ns))

        # Cache results.
        self._page_from_numbers = {}
        self._numbers_from_page = {}
        self._page_numbers_from_label = {}
        self._pages_from_label = {}
        self._labels_from_page_number = {}
        self._labels_from_page = {}

    def _get_page_mappings(self):
        """Associate label and number for each page linked to the index."""
        self._parsed_text = self._get_parsed_page()
        self._soup = BeautifulSoup(self._parsed_text, 'html.parser')
        attrs = {'class': re.compile('prp-pagequality')}

        # Search for attribute "prp-pagequality" in tags like:
        # <a class="quality1 prp-pagequality-1"
        #    href="/wiki/Page:xxx.djvu/n"
        #    title="Page:xxx.djvu/n">m
        # </a>
        # Try to purge or raise ValueError.
        if not self._soup.find_all('a', attrs=attrs):
            self.purge()
            del self._parsed_text
            self._parsed_text = self._get_parsed_page()
            self._soup = BeautifulSoup(self._parsed_text, 'html.parser')
            if not self._soup.find_all('a', attrs=attrs):
                raise ValueError(
                    'Missing class="qualityN prp-pagequality-N" in: %s.'
                    % self)

        page_cnt = 0
        for a_tag in self._soup.find_all('a', attrs=attrs):
            page_cnt += 1
            label = a_tag.text.lstrip('0')  # Label is not converted to int.
            title = a_tag.get('title')

            page = ProofreadPage(self.site, title)
            if page not in self._all_page_links:
                raise pywikibot.Error('Page %s not recognised.' % page)

            # In order to avoid to fetch other Page:title links outside
            # the Pages section of the Index page; these should hopefully be
            # the first ones, so if they start repeating, we are done.
            if page in self._labels_from_page:
                break

            # Divide page title in base title and page number.
            base_title, sep, page_number = title.rpartition('/')
            # Sanity check if WS site use page convention name/number.
            if sep == '/':
                assert page_cnt == int(page_number), (
                    'Page number %s not recognised as page %s.'
                    % (page_cnt, title))

            # Mapping: numbers <-> pages.
            self._page_from_numbers[page_cnt] = page
            self._numbers_from_page[page] = page_cnt
            # Mapping: numbers/pages as keys, labels as values.
            self._labels_from_page_number[page_cnt] = label
            self._labels_from_page[page] = label
            # Reverse mapping: labels as keys, numbers/pages as values.
            self._page_numbers_from_label.setdefault(label, set()).add(page_cnt)
            self._pages_from_label.setdefault(label, set()).add(page)

        # Sanity check: all links to Page: ns must have been considered.
        assert set(self._labels_from_page) == set(self._all_page_links)

    @property
    def num_pages(self):
        """Return total number of pages in Index.

        @return: total number of pages in Index
        @rtype: int
        """
        if not self._page_from_numbers:
            self._get_page_mappings()
        return len(self._page_from_numbers)

    def get_label_from_page(self, page):
        """Return 'page label' for page.

        There is a 1-to-1 correspondence (each page has a label).

        @param page: Page instance
        @return: page label
        @rtype: unicode string
        """
        if not self._labels_from_page:
            self._get_page_mappings()

        try:
            return self._labels_from_page[page]
        except KeyError:
            raise KeyError('Invalid Page: %s.' % page)

    def get_label_from_page_number(self, page_number):
        """Return page label from page number.

        There is a 1-to-1 correspondence (each page has a label).

        @param page_number: int
        @return: page label
        @rtype: unicode string
        """
        if not self._labels_from_page_number:
            self._get_page_mappings()

        try:
            return self._labels_from_page_number[page_number]
        except KeyError:
            raise KeyError('Page number ".../%s" not range.'
                           % page_number)

    def _get_from_label(self, mapping_dict, label):
        """Helper function to get info from label."""
        # Convert label to string if an integer is passed.
        if not mapping_dict:
            self._get_page_mappings()

        if isinstance(label, int):
            label = str(label)

        try:
            return mapping_dict[label]
        except KeyError:
            raise KeyError('No page has label: "%s".' % label)

    def get_page_number_from_label(self, label='1'):
        """Return page number from page label.

        There is a 1-to-many correspondence (a label can be the same for
        several pages).

        @return: set containing page numbers corresponding to page label.
        """
        return self._get_from_label(self._page_numbers_from_label, label)

    def get_page_from_label(self, label='1'):
        """Return page number from page label.

        There is a 1-to-many correspondence (a label can be the same for
        several pages).

        @return: set containing pages corresponding to page label.
        """
        return self._get_from_label(self._pages_from_label, label)

    def get_page_from_number(self, page_number):
        """Return a page object from page number.

        @param page_number: int
        @return: page
        @rtype: page object
        """
        if not self._page_from_numbers:
            self._get_page_mappings()

        try:
            return self._page_from_numbers[page_number]
        except KeyError:
            raise KeyError('Invalid page number: %s.' % page_number)
