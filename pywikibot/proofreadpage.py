# -*- coding: utf-8  -*-
"""
Objects representing objects used with ProofreadPage Extensions.

This module includes objects:
* ProofreadPage(Page)
* FullHeader

"""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import re

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
        self.text = text or ''

        m = self.p_header.search(self.text)
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
        # If page does not exist, preload it
        if not self.exists():
            self._text = self.preloadText()
        # If page exists, load it
        super(ProofreadPage, self).text
        return self._text

    @text.setter
    def text(self, value):
        """Update the current text.

        Mainly for use within the class, called by other methods.

        @param value: New value or None
        @param value: basestring

        Raises:
        exception Error:   the page is not formatted according to ProofreadPage
                           extension.
        """
        self._text = value
        self._decompose_page()
        if not self._text:
            self._create_empty_page()

    def _decompose_page(self):
        """Split Proofread Page text in header, body and footer.

        Raises:
        exception Error:   the page is not formatted according to ProofreadPage
                           extension.
        """
        if not self.text:
            self._create_empty_page()
            return

        open_queue = list(self.p_open.finditer(self.text))
        close_queue = list(self.p_close.finditer(self.text))

        len_oq = len(open_queue)
        len_cq = len(close_queue)
        if (len_oq != len_cq) or (len_oq < 2 or len_cq < 2):
            raise pywikibot.Error('ProofreadPage %s: invalid format'
                                  % self.title(asLink=True))

        f_open, f_close = open_queue[0], close_queue[0]
        self._full_header = FullHeader(self.text[f_open.end():f_close.start()])

        l_open, l_close = open_queue[-1], close_queue[-1]
        self._footer = self.text[l_open.end():l_close.start()]

        self._body = self.text[f_close.end():l_open.start()]

    def _compose_page(self):
        """Compose Proofread Page text from header, body and footer."""
        fmt = ('{0.open_tag}{0._full_header}{0.close_tag}'
               '{0._body}'
               '{0.open_tag}{0._footer}</div>{0.close_tag}')
        self.text = fmt.format(self)
        return self.text

    def save(self, *args, **kwargs):  # see Page.save()
        """Save page content after recomposing the page."""
        self._compose_page()
        summary = kwargs.pop('summary', '')
        summary = self.pre_summary + summary
        super(ProofreadPage, self).save(*args, summary=summary, **kwargs)

    @property
    def pre_summary(self):
        """Return trailing part of edit summary.

        The edit summary shall be appended to pre_summary to highlight
        Status in the edit summary on wiki.
        """
        return '/* {0.status} */ '.format(self)
