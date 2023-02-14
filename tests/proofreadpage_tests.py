#!/usr/bin/env python3
"""Tests for the proofreadpage module."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import difflib
import json
import unittest
from contextlib import suppress

import pywikibot
from pywikibot.data import api
from pywikibot.exceptions import UnknownExtensionError
from pywikibot.proofreadpage import (
    IndexPage,
    PagesTagParser,
    ProofreadPage,
    TagAttr,
)
from pywikibot.tools import has_module
from tests import unittest_print
from tests.aspects import TestCase, require_modules
from tests.basepage import (
    BasePageLoadRevisionsCachingTestBase,
    BasePageMethodsTestBase,
)
from tests.utils import skipping


class TestPagesTagParser(TestCase):
    """Test TagAttr class."""

    net = False

    def test_tag_attr_int(self):
        """Test TagAttr for int values."""
        attr = TagAttr('to', 3)
        self.assertEqual(repr(attr), "TagAttr('to', 3)")
        self.assertEqual(str(attr), 'to=3')
        self.assertEqual(attr.attr, 'to')
        self.assertEqual(attr.value, 3)

    def test_tag_attr_srt_int(self):
        """Test TagAttr for str values that can be converted to int."""
        attr = TagAttr('to', '3')
        self.assertEqual(repr(attr), "TagAttr('to', '3')")
        self.assertEqual(str(attr), 'to=3')
        self.assertEqual(attr.attr, 'to')
        self.assertEqual(attr.value, 3)

        attr.value = '"3"'
        self.assertEqual(str(attr), 'to="3"')
        self.assertEqual(repr(attr), """TagAttr('to', '"3"')""")
        self.assertEqual(attr.value, 3)

    def test_tag_attr_str(self):
        """Test TagAttr for str value."""
        attr = TagAttr('fromsection', 'A123')
        self.assertEqual(repr(attr), "TagAttr('fromsection', 'A123')")
        self.assertEqual(str(attr), 'fromsection=A123')
        self.assertEqual(attr.attr, 'fromsection')
        self.assertEqual(attr.value, 'A123')

        attr.value = '"A123"'
        self.assertEqual(repr(attr), """TagAttr('fromsection', '"A123"')""")
        self.assertEqual(str(attr), 'fromsection="A123"')
        self.assertEqual(attr.value, 'A123')

        attr.value = "'A123'"
        self.assertEqual(repr(attr), """TagAttr('fromsection', "'A123'")""")
        self.assertEqual(str(attr), "fromsection='A123'")
        self.assertEqual(attr.value, 'A123')

    def test_tag_attr_exceptions(self):
        """Test TagAttr for Exceptions."""
        self.assertRaises(ValueError, TagAttr, 'fromsection', 'A123"')
        self.assertRaises(TypeError, TagAttr, 'fromsection', 3.0)

    def test_pages_tag_parser(self):
        """Test PagesTagParser."""
        tp = PagesTagParser('Text: <pages />')
        self.assertEqual(repr(tp), "PagesTagParser('<pages />')")

        text = 'Text: <pages from="first" to="last" />'
        tp = PagesTagParser(text)
        self.assertEqual(
            repr(tp), """PagesTagParser('<pages from="first" to="last" />')""")
        self.assertEqual(tp.ffrom, 'first')
        self.assertEqual(tp.to, 'last')

        tp.index = '"Index.pdf"'
        self.assertEqual(tp.index, 'Index.pdf')

        tp.ffrom, tp.to = 1, '"3"'
        self.assertEqual(tp.ffrom, 1)
        self.assertEqual(tp.to, 3)
        self.assertEqual(str(tp), '<pages index="Index.pdf" from=1 to="3" />')

        del tp.index
        self.assertNotIn('index', tp)

        tp.to = "'3'"
        self.assertEqual(str(tp), """<pages from=1 to='3' />""")

        tp.step = 3
        self.assertEqual(str(tp), """<pages from=1 to='3' step=3 />""")
        self.assertIn('step', tp)

    def test_pages_tag_parser_exceptions(self):
        """Test PagesTagParser Exceptions."""
        text = """Text: <pages index="Index.pdf />"""
        self.assertRaises(ValueError, PagesTagParser, text)

        text = """Text: <pages index="Index.pdf' />"""
        self.assertRaises(ValueError, PagesTagParser, text)

        text = """Text: <pages index="Index.pdf from=C" />"""
        self.assertRaises(ValueError, PagesTagParser, text)


class TestProofreadPageInvalidSite(TestCase):

    """Test ProofreadPage class."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def test_invalid_site_source(self):
        """Test ProofreadPage from invalid Site as source."""
        with self.assertRaises(UnknownExtensionError):
            ProofreadPage(self.site, 'title')


class TestBasePageMethodsProofreadPage(BasePageMethodsTestBase):

    """Test behavior of ProofreadPage methods inherited from BasePage."""

    family = 'wikisource'
    code = 'en'

    def setUp(self):
        """Set up test case."""
        self._page = ProofreadPage(
            self.site, 'Page:Popular Science Monthly Volume 1.djvu/12')
        super().setUp()

    def test_basepage_methods(self):
        """Test ProofreadPage methods inherited from superclass BasePage."""
        self._test_invoke()
        self._test_return_datatypes()


class TestLoadRevisionsCachingProofreadPage(
        BasePageLoadRevisionsCachingTestBase):

    """Test site.loadrevisions() caching."""

    family = 'wikisource'
    code = 'en'

    def setUp(self):
        """Set up test case."""
        self._page = ProofreadPage(
            self.site, 'Page:Popular Science Monthly Volume 1.djvu/12')
        super().setUp()

    def test_page_text(self):
        """Test site.loadrevisions() with Page.text."""
        self._test_page_text()

    @property
    def custom_text(self):
        """Return a dummy text for testing."""
        cls_pagetext, div = TestProofreadPageValidSite.class_pagetext_fmt[True]
        return TestProofreadPageValidSite.fmt.format(
            user=self.site.username(), class_pagetext=cls_pagetext,
            references='<references/>', div_end=div)


class TestProofreadPageParseTitle(TestCase):

    """Test ProofreadPage._parse_title() function."""

    cached = True

    # Use sites to run  parametrized tests.
    sites = {
        '1': {
            'family': 'wikisource', 'code': 'en',
            'title': 'Page:Test.djvu/12',
            'tuple': ('Test.djvu', 'djvu', 12),
        },
        '2': {
            'family': 'wikisource', 'code': 'en',
            'title': 'Page:Test djvu/12',
            'tuple': ('Test djvu', '', 12),
        },
        '3': {
            'family': 'wikisource', 'code': 'en',
            'title': 'Page:Test.jpg/12',
            'tuple': ('Test.jpg', 'jpg', 12),
        },
        '4': {
            'family': 'wikisource', 'code': 'en',
            'title': 'Page:Test jpg/12',
            'tuple': ('Test jpg', '', 12),
        },
        '5': {
            'family': 'wikisource', 'code': 'en',
            'title': 'Page:Test.jpg',
            'tuple': ('Test.jpg', 'jpg', None),
        },
        '6': {
            'family': 'wikisource', 'code': 'en',
            'title': 'Page:Test jpg',
            'tuple': ('Test jpg', '', None),
        },
    }

    def test_parse_title(self, key):
        """Test ProofreadPage_parse_title() function."""
        data = self.sites[key]
        title = data['title']
        base, base_ext, num = data['tuple']
        page = ProofreadPage(self.site, title)
        self.assertEqual(page._base, base)
        self.assertEqual(page._base_ext, base_ext)
        self.assertEqual(page._num, num)


class TestProofreadPageValidSite(TestCase):

    """Test ProofreadPage class."""

    family = 'wikisource'
    code = 'en'

    cached = True

    valid = {
        'title': 'Page:Popular Science Monthly Volume 1.djvu/12',
        'index': 'Index:Popular Science Monthly Volume 1.djvu',
        'ql': 4,
        'user': 'T. Mazzei',
        'header': "{{rh|2|''THE POPULAR SCIENCE MONTHLY.''}}",
        'footer': '\n{{smallrefs}}',
        'url_image': ('https://upload.wikimedia.org/wikipedia/commons/'
                      'thumb/a/ac/Popular_Science_Monthly_Volume_1.djvu/'
                      'page12-1024px-Popular_Science_Monthly_Volume_1.djvu'
                      '.jpg'),
    }

    valid_redlink = {
        'title': 'Page:Pywikibot test page 3.jpg',
        'url_image': ('https://upload.wikimedia.org/wikisource/en/3/37/'
                      'Pywikibot_test_page_3.jpg'),
    }

    existing_invalid = {
        'title': 'Main Page',
    }

    existing_unlinked = {
        'title': 'Page:Pywikibot unlinked test page',
    }

    not_existing_invalid = {
        'title': 'User:cannot_exists',
        'title1': 'User:Popular Science Monthly Volume 1.djvu/12'
    }

    div_in_footer = {
        'title': 'Page:Pywikibot unlinked test page',
    }

    class_pagetext_fmt = {
        True: ('<div class="pagetext">\n\n\n', '</div>'),
        False: ('', ''),
    }

    fmt = ('<noinclude><pagequality level="1" user="{user}" />'
           '{class_pagetext}</noinclude>'
           '<noinclude>{references}{div_end}</noinclude>')

    def test_valid_site_source(self):
        """Test ProofreadPage from valid Site as source."""
        page = ProofreadPage(self.site, 'Page:dummy test page')
        self.assertEqual(page.namespace(), self.site.proofread_page_ns)

    def test_invalid_existing_page_source(self):
        """Test ProofreadPage from invalid existing Page as source."""
        source = pywikibot.Page(self.site, self.existing_invalid['title'])
        with self.assertRaises(ValueError):
            ProofreadPage(source)

    def test_invalid_not_existing_page_source(self):
        """Test ProofreadPage from invalid not existing Page as source."""
        # namespace is forced
        source = pywikibot.Page(self.site,
                                self.not_existing_invalid['title'])
        fixed_source = pywikibot.Page(self.site,
                                      source.title(with_ns=False),
                                      ns=self.site.proofread_page_ns)
        page = ProofreadPage(fixed_source)
        self.assertEqual(page.title(), fixed_source.title())

    def test_invalid_not_existing_page_source_wrong_ns(self):
        """Test ProofreadPage from Page not existing in non-Page ns."""
        source = pywikibot.Page(self.site,
                                self.not_existing_invalid['title1'])
        with self.assertRaises(ValueError):
            ProofreadPage(source)

    def test_invalid_link_source(self):
        """Test ProofreadPage from invalid Link as source."""
        source = pywikibot.Link(self.not_existing_invalid['title'],
                                source=self.site)
        with self.assertRaises(ValueError):
            ProofreadPage(source)

    def test_valid_link_source(self):
        """Test ProofreadPage from valid Link as source."""
        source = pywikibot.Link(
            self.valid['title'],
            source=self.site,
            default_namespace=self.site.proofread_page_ns)
        page = ProofreadPage(source)
        self.assertEqual(page.title(with_ns=False), source.title)
        self.assertEqual(page.namespace(), source.namespace)

    def test_valid_parsing(self):
        """Test ProofreadPage page parsing functions."""
        page = ProofreadPage(self.site, self.valid['title'])
        self.assertEqual(page.ql, self.valid['ql'])
        self.assertEqual(page.user, self.valid['user'])
        self.assertEqual(page.header, self.valid['header'])
        self.assertEqual(page.footer, self.valid['footer'])

    def test_div_in_footer(self):
        """Test ProofreadPage page parsing functions."""
        page = ProofreadPage(self.site, self.div_in_footer['title'])
        self.assertTrue(page.footer.endswith('</div>'))

    def test_decompose_recompose_text(self):
        """Test ProofreadPage page decomposing/composing text."""
        page = ProofreadPage(self.site, self.valid['title'])
        plain_text = pywikibot.Page(self.site, self.valid['title']).text
        assert page.text
        self.assertEqual(plain_text, page.text)

    def test_preload_from_not_existing_page(self):
        """Test ProofreadPage page decomposing/composing text."""
        page = ProofreadPage(self.site, 'Page:dummy test page')
        # Fetch page text to instantiate page._full_header, in order to allow
        # for proper test result preparation.
        page.text
        class_pagetext, div = self.class_pagetext_fmt[
            page._full_header._has_div]
        self.assertEqual(page.text,
                         self.fmt.format(user=self.site.username(),
                                         class_pagetext=class_pagetext,
                                         references='<references/>',
                                         div_end=div))

    def test_preload_from_empty_text(self):
        """Test ProofreadPage page decomposing/composing text."""
        page = ProofreadPage(self.site, 'Page:dummy test page')
        page.text = ''
        class_pagetext, div = self.class_pagetext_fmt[
            page._full_header._has_div]
        self.assertEqual(page.text,
                         self.fmt.format(user=self.site.username(),
                                         class_pagetext=class_pagetext,
                                         references='',
                                         div_end=div))

    def test_json_format(self):
        """Test conversion to json format."""
        page = ProofreadPage(self.site, self.valid['title'])

        rvargs = {'rvprop': 'ids|flags|timestamp|user|comment|content',
                  'rvcontentformat': 'application/json',
                  'titles': page,
                  }

        rvgen = self.site._generator(api.PropertyGenerator,
                                     type_arg='info|revisions',
                                     total=1, **rvargs)
        rvgen.set_maximum_items(-1)  # suppress use of rvlimit parameter

        try:
            pagedict = next(rvgen)
            loaded_text = pagedict.get('revisions')[0].get('*')
        except (StopIteration, TypeError, KeyError, ValueError, IndexError):
            loaded_text = ''

        page_text = page._page_to_json()
        self.assertEqual(json.loads(page_text), json.loads(loaded_text))

    @require_modules('bs4')
    def test_url_image(self):
        """Test fetching of url image of the scan of ProofreadPage."""
        page = ProofreadPage(self.site, self.valid['title'])
        self.assertEqual(page.url_image, self.valid['url_image'])

        page = ProofreadPage(self.site, self.existing_unlinked['title'])
        # test Exception in property.
        with self.assertRaises(ValueError):
            page.url_image

        page = ProofreadPage(self.site, self.valid_redlink['title'])
        with skipping(ValueError, msg='T181913, T114318'):
            self.assertEqual(page.url_image, self.valid_redlink['url_image'])


class TestPageQuality(TestCase):

    """Test page quality."""

    family = 'wikisource'
    code = 'en'

    cached = True

    def test_applicable_quality_level(self):
        """Test Page.quality_level when applicable."""
        site = self.get_site()
        title = 'Page:Popular Science Monthly Volume 49.djvu/1'
        page = ProofreadPage(site, title)
        self.assertEqual(page.content_model, 'proofread-page')
        self.assertEqual(page.quality_level, 0)


class BS4TestCase(TestCase):

    """Run tests which needs bs4 beeing installed."""

    @classmethod
    def setUpClass(cls):
        """Check whether bs4 module is installed already."""
        if not has_module('bs4'):
            unittest_print(
                'all tests ({module}.{name})\n{doc}.. '
                .format(module=__name__, doc=cls.__doc__, name=cls.__name__),
                end='\n')
            cls.skipTest(cls, 'bs4 not installed')
        super().setUpClass()


class TestPageOCR(BS4TestCase):

    """Test page ocr functions."""

    family = 'wikisource'
    code = 'en'

    cached = True

    data = {'title': 'Page:Popular Science Monthly Volume 1.djvu/10',
            'hocr': (False, 'ENTERED, according to Act of Congress, in the '
                            'year 1872,\nBY D. APPLETON & CO.,\nIn the Ofﬁce '
                            'of the Librarian of Congress, at '
                            'Washington.\n\n'),
            'ocr': (False, 'EsTEnen, according to Act of Congress, in the '
                           'year 1872,\nBy D. APPLETON & CO.,\nIn the '
                           'Office of the Librarian of Congress, at '
                           'Washington.\n\u000c'),
            'wmfOCR': (False, 'Estee, according to Act of Congress, in the '
                              'year 1872,\n'
                              'By D. APPLETON & CO.,\n'
                              'In the Office of the Librarian of Congress, '
                              'at Washington.'),
            'googleOCR': (False, 'ENTERED, according to Act of Congress, in '
                                 'the year 1572,\nBY D. APPLETON & CO.\n'
                                 'In the Office of the Librarian of '
                                 'Congress, at Washington.\n4 334\n'),
            }

    def setUp(self):
        """Test setUp."""
        site = self.get_site()
        title = self.data['title']
        self.page = ProofreadPage(site, title)
        super().setUp()

    def test_ocr_exceptions(self):
        """Test page.ocr() exceptions."""
        with self.assertRaises(TypeError):
            self.page.ocr(ocr_tool='dummy')

    def test_do_hocr(self):
        """Test page._do_hocr()."""
        error, text = self.page._do_hocr()
        if error:
            self.skipTest(text)
        ref_error, ref_text = self.data['hocr']
        self.assertEqual(error, ref_error)
        s = difflib.SequenceMatcher(None, text, ref_text)
        self.assertGreater(s.ratio(), 0.9)

    def test_do_ocr_phetools(self):
        """Test page._do_ocr(ocr_tool='phetools')."""
        error, text = self.page._do_ocr(ocr_tool='phetools')
        ref_error, ref_text = self.data['ocr']
        if error:
            self.skipTest(text)
        self.assertEqual(error, ref_error)
        s = difflib.SequenceMatcher(None, text, ref_text)
        self.assertGreater(s.ratio(), 0.9)

    def test_do_ocr_wmfocr(self):
        """Test page._do_ocr(ocr_tool='wmfOCR')."""
        error, text = self.page._do_ocr(ocr_tool='wmfOCR')
        if error:
            self.skipTest(text)
        ref_error, ref_text = self.data['wmfOCR']
        self.assertEqual(error, ref_error)
        s = difflib.SequenceMatcher(None, text, ref_text)
        self.assertGreater(s.ratio(), 0.9)

    def test_do_ocr_googleocr(self):
        """Test page._do_ocr(ocr_tool='googleOCR')."""
        error, text = self.page._do_ocr(ocr_tool='googleOCR')
        if error:
            self.skipTest(text)
        ref_error, ref_text = self.data['googleOCR']
        self.assertEqual(error, ref_error)
        s = difflib.SequenceMatcher(None, text, ref_text)
        self.assertGreater(s.ratio(), 0.9)

    def test_ocr_wmfocr(self):
        """Test page.ocr(ocr_tool='wmfOCR')."""
        try:
            text = self.page.ocr(ocr_tool='wmfOCR')
        except Exception as exc:
            self.assertIsInstance(exc, ValueError)
        else:
            _error, ref_text = self.data['wmfOCR']
            s = difflib.SequenceMatcher(None, text, ref_text)
            self.assertGreater(s.ratio(), 0.9)


class TestProofreadPageIndexProperty(BS4TestCase):

    """Test ProofreadPage index property."""

    family = 'wikisource'
    code = 'en'

    cached = True

    valid = {
        'title': 'Page:Popular Science Monthly Volume 1.djvu/12',
        'index': 'Index:Popular Science Monthly Volume 1.djvu',
    }

    existing_multilinked = {
        'title': 'Page:Pywikibot test page.djvu/1',
        'index_1': 'Index:Pywikibot test page.djvu',
        'index_2': 'Index:Pywikibot test page 2',
    }

    existing_unlinked = {
        'title': 'Page:Pywikibot unlinked test page',
    }

    def test_index(self):
        """Test index property."""
        # Page with Index.
        page = ProofreadPage(self.site, self.valid['title'])
        index_page = IndexPage(self.site, self.valid['index'])

        # Test property.
        self.assertEqual(page.index, index_page)

        # Test deleter
        del page.index
        self.assertFalse(hasattr(page, '_index'))
        # Test setter with wrong type.
        with self.assertRaises(TypeError):
            page.index = 'invalid index'
        # Test setter with correct type.
        page.index = index_page
        self.assertEqual(page.index, index_page)

        # Page without Index.
        page = ProofreadPage(self.site, self.existing_multilinked['title'])
        index_page_1 = IndexPage(self.site,
                                 self.existing_multilinked['index_1'])
        index_page_2 = IndexPage(self.site,
                                 self.existing_multilinked['index_2'])
        self.assertEqual(page.index, index_page_1)
        self.assertNotEqual(page.index, index_page_2)
        self.assertEqual(page._index, (index_page_1, [index_page_2]))

        # Page without Index.
        page = ProofreadPage(self.site, self.existing_unlinked['title'])
        self.assertIsNone(page.index)
        self.assertEqual(page._index, (None, []))


class TestIndexPageInvalidSite(BS4TestCase):

    """Test IndexPage class."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def test_invalid_site_source(self):
        """Test IndexPage from invalid Site as source."""
        with self.assertRaises(UnknownExtensionError):
            IndexPage(self.site, 'title')


class TestIndexPageValidSite(BS4TestCase):

    """Test IndexPage class."""

    family = 'wikisource'
    code = 'en'

    cached = True

    valid_index_title = 'Index:Popular Science Monthly Volume 1.djvu'
    existing_invalid_title = 'Main Page'
    not_existing_invalid_title = 'User:cannot_exists'

    def test_valid_site_as_source(self):
        """Test IndexPage from valid Site as source."""
        page = IndexPage(self.site, 'Index:dummy test page')
        self.assertEqual(page.namespace(), self.site.proofread_index_ns)

    def test_invalid_existing_page_as_source(self):
        """Test IndexPage from invalid existing Page as source."""
        source = pywikibot.Page(self.site, self.existing_invalid_title)
        with self.assertRaises(ValueError):
            IndexPage(source)

    def test_invalid_not_existing_page_as_source(self):
        """Test IndexPage from Page not existing in non-Page ns as source."""
        source = pywikibot.Page(self.site,
                                self.not_existing_invalid_title)
        with self.assertRaises(ValueError):
            IndexPage(source)

    def test_invalid_link_as_source(self):
        """Test IndexPage from invalid Link as source."""
        source = pywikibot.Link(self.not_existing_invalid_title,
                                source=self.site)
        with self.assertRaises(ValueError):
            IndexPage(source)

    def test_valid_link_as_source(self):
        """Test IndexPage from valid Link as source."""
        source = pywikibot.Link(self.valid_index_title,
                                source=self.site,
                                default_namespace=self.site.proofread_page_ns)
        page = IndexPage(source)
        self.assertEqual(page.title(with_ns=False), source.title)
        self.assertEqual(page.namespace(), source.namespace)


class TestBasePageMethodsIndexPage(BS4TestCase, BasePageMethodsTestBase):

    """Test behavior of ProofreadPage methods inherited from BasePage."""

    family = 'wikisource'
    code = 'en'

    def setUp(self):
        """Set up test case."""
        self._page = IndexPage(
            self.site, 'Index:Popular Science Monthly Volume 1.djvu')
        super().setUp()

    def test_basepage_methods(self):
        """Test IndexPage methods inherited from superclass BasePage."""
        self._test_invoke()
        self._test_return_datatypes()


class TestLoadRevisionsCachingIndexPage(BS4TestCase,
                                        BasePageLoadRevisionsCachingTestBase):

    """Test site.loadrevisions() caching."""

    family = 'wikisource'
    code = 'en'

    def setUp(self):
        """Set up test case."""
        self._page = IndexPage(
            self.site, 'Index:Popular Science Monthly Volume 1.djvu')
        super().setUp()

    def test_page_text(self):
        """Test site.loadrevisions() with Page.text."""
        self._test_page_text()

    @property
    def custom_text(self):
        """Return a dummy text for testing."""
        cls_pagetext, div = TestProofreadPageValidSite.class_pagetext_fmt[True]
        return TestProofreadPageValidSite.fmt.format(
            user=self.site.username(), class_pagetext=cls_pagetext,
            references='<references/>', div_end=div)


class TestIndexPageMappings(BS4TestCase):

    """Test IndexPage class."""

    sites = {
        'enws': {
            'family': 'wikisource',
            'code': 'en',
            'index': 'Index:Popular Science Monthly Volume 1.djvu',
            'num_pages': 804,
            'page': 'Page:Popular Science Monthly Volume 1.djvu/{0}',
            'get_label': [11, 11, '1'],
            'get_number': [[1, {11}],
                           ['Cvr', {1, 9, 10, 804}],
                           ],
            # 'get_page' is filled in setUpClass.
        },
        'dews': {  # dews does not use page convention name/number.
            'family': 'wikisource',
            'code': 'de',
            'index': 'Index:Musen-Almanach für das Jahr 1799',
            'num_pages': 272,
            'page': 'Seite:Schiller_Musenalmanach_1799_{0:3d}.jpg',
            'get_label': [120, 120, '120'],  # page no, title no, label
            'get_number': [[120, {120}],
                           ],
            # 'get_page' is filled in setUpClass.
        },
        'frws': {
            'family': 'wikisource',
            'code': 'fr',
            'index': 'Index:Segard - Hymnes profanes, 1894.djvu',
            'num_pages': 107,
            'page': 'Page:Segard - Hymnes profanes, 1894.djvu/{0}',
            'get_label': [11, 11, '8'],
            'get_number': [[8, {11}],
                           ['-', set(range(1, 4)) | set(range(101, 108))],
                           ],
            # 'get_page' is filled in setUpClass.
        },
    }

    cached = True

    @classmethod
    def setUpClass(cls):
        """Prepare get_page dataset for tests."""
        super().setUpClass()
        for key, site_def in cls.sites.items():
            site = cls.get_site(name=key)
            base_title = site_def['page']

            # 'get_page' has same structure as 'get_number'.
            site_def['get_page'] = []
            for label, page_numbers in site_def['get_number']:
                page_set = {ProofreadPage(site, base_title.format(i))
                            for i in page_numbers}
                site_def['get_page'].append([label, page_set])

    def test_check_if_cached(self, key):
        """Test if cache is checked and loaded properly."""
        data = self.sites[key]
        index_page = IndexPage(self.site, self.sites[key]['index'])

        num, _title_num, label = data['get_label']
        self.assertIs(index_page._cached, False)
        fetched_label = index_page.get_label_from_page_number(num)

        self.assertIs(index_page._cached, True)
        self.assertEqual(label, fetched_label)

        # Check if cache is refreshed.
        index_page._labels_from_page_number[num] = 'wrong cached value'
        self.assertEqual(index_page.get_label_from_page_number(num),
                         'wrong cached value')
        index_page._cached = False
        self.assertEqual(index_page.get_label_from_page_number(num), label)

    def test_num_pages(self, key):
        """Test num_pages property."""
        index_page = IndexPage(self.site, self.sites[key]['index'])
        self.assertEqual(index_page.num_pages, self.sites[key]['num_pages'])

    def test_get_labels(self, key):
        """Test IndexPage page get_label_from_* functions."""
        data = self.sites[key]
        num, title_num, label = data['get_label']

        index_page = IndexPage(self.site, self.sites[key]['index'])
        page_title = self.sites[key]['page'].format(title_num)
        proofread_page = ProofreadPage(self.site, page_title)

        # Get label from number.
        self.assertEqual(index_page.get_label_from_page_number(num), label)
        # Error if number does not exists.
        with self.assertRaises(KeyError):
            index_page.get_label_from_page_number(-1)

        # Get label from page.
        self.assertEqual(index_page.get_label_from_page(proofread_page), label)
        # Error if page does not exists.
        with self.assertRaises(KeyError):
            index_page.get_label_from_page(None)

    def test_get_page_and_number(self, key):
        """Test IndexPage page get_page_number functions."""
        data = self.sites[key]
        index_page = IndexPage(self.site, self.sites[key]['index'])

        # Test get_page_numbers_from_label.
        for label, num_set in data['get_number']:
            # Get set of numbers from label with label as int or str.
            self.assertEqual(index_page.get_page_number_from_label(label),
                             num_set)
            self.assertEqual(index_page.get_page_number_from_label(str(label)),
                             num_set)

        # Error if label does not exists.
        label, num_set = 'dummy label', []
        with self.assertRaises(KeyError):
            index_page.get_page_number_from_label('dummy label')

        # Test get_page_from_label.
        for label, page_set in data['get_page']:
            # Get set of pages from label with label as int or str.
            self.assertEqual(index_page.get_page_from_label(label),
                             page_set)
            self.assertEqual(index_page.get_page_from_label(str(label)),
                             page_set)

        # Error if label does not exists.
        with self.assertRaises(KeyError):
            index_page.get_page_from_label('dummy label')

        # Test get_page.
        for n in num_set:
            p = index_page.get_page(n)
            self.assertEqual(index_page.get_number(p), n)

        # Test get_number.
        for p in page_set:
            n = index_page.get_number(p)
            self.assertEqual(index_page.get_page(n), p)

    def test_page_gen(self, key):
        """Test Index page generator."""
        data = self.sites[key]
        num, title_num, _label = data['get_label']

        index_page = IndexPage(self.site, self.sites[key]['index'])
        page_title = self.sites[key]['page'].format(title_num)
        proofread_page = ProofreadPage(self.site, page_title)

        # Check start/end limits.
        with self.assertRaises(ValueError):
            index_page.page_gen(-1, 2)
        with self.assertRaises(ValueError):
            index_page.page_gen(1, -1)
        with self.assertRaises(ValueError):
            index_page.page_gen(2, 1)

        # Check quality filters.
        gen = index_page.page_gen(num, num, filter_ql=range(5))
        self.assertEqual(list(gen), [proofread_page])

        gen = index_page.page_gen(num, num, filter_ql=[0])
        self.assertEqual(list(gen), [])


class TestIndexPageMappingsRedlinks(BS4TestCase):

    """Test IndexPage mappings with redlinks."""

    family = 'wikisource'
    code = 'en'

    cached = True

    index_name = 'Index:Pywikibot test page.djvu'
    page_names = ['Page:Pywikibot test page.djvu/1',
                  'Page:Pywikibot test page.djvu/2',
                  ]
    missing_name = 'Page:Pywikibot test page.djvu/2'

    @classmethod
    def setUpClass(cls):
        """Prepare tests by creating page instances."""
        super().setUpClass()
        cls.index = IndexPage(cls.site, cls.index_name)
        cls.pages = [ProofreadPage(cls.site, page) for page in cls.page_names]
        cls.missing = ProofreadPage(cls.site, cls.missing_name)

    def test_index_redlink(self):
        """Test index property with redlink."""
        self.assertEqual(self.missing.index, self.index)

    def test_get_page_and_number_redlink(self):
        """Test IndexPage page get_page_number functions with redlinks."""
        for page in self.pages:
            n = self.index.get_number(page)
            self.assertEqual(self.index.get_page(n), page)

    def test_page_gen_redlink(self):
        """Test Index page generator with redlinks."""
        # Check start/end limits.
        with self.assertRaises(ValueError):
            self.index.page_gen(-1, 2)
        with self.assertRaises(ValueError):
            self.index.page_gen(1, -1)
        with self.assertRaises(ValueError):
            self.index.page_gen(2, 1)

        gen = self.index.page_gen(1, None, filter_ql=range(5))
        self.assertEqual(list(gen), self.pages)


class TestIndexPageHasValidContent(BS4TestCase):

    """Unit tests for has_valid_content()."""

    family = 'wikisource'
    code = 'en'

    index_name = 'Index:Phosphor (1888).djvu'
    valid_template = '{{%s|foo=bar}}' % IndexPage.INDEX_TEMPLATE
    other_template = '{{PoTM|bar=foobar}}'

    @classmethod
    def setUpClass(cls):
        """Prepare tests by creating an IndexPage instance."""
        super().setUpClass()
        cls.index = IndexPage(cls.site, cls.index_name)

    def test_has_valid_content_empty(self):
        """Test empty page is invalid."""
        self.index.text = ''
        self.assertFalse(self.index.has_valid_content())

    def test_has_valid_content_non_template(self):
        """Test non-template is invalid."""
        self.index.text = 'foobar'
        self.assertFalse(self.index.has_valid_content())

    def test_has_valid_content_valid(self):
        """Test correct Index template is valid."""
        self.index.text = self.valid_template
        self.assertTrue(self.index.has_valid_content())

    def test_has_valid_content_prefixed(self):
        """Test prefixing Index template is invalid."""
        self.index.text = f'pre {self.valid_template}'
        self.assertFalse(self.index.has_valid_content())

    def test_has_valid_content_postfixed(self):
        """Test postfixing Index template is invalid."""
        self.index.text = f'{self.valid_template}post'
        self.assertFalse(self.index.has_valid_content())

    def test_has_valid_content_pre_and_postfixed(self):
        """Test pre- and postfixing Index template is invalid."""
        self.index.text = f'pre{self.valid_template}post'
        self.assertFalse(self.index.has_valid_content())

    def test_has_valid_content_second_template(self):
        """Test postfixing a second template is invalid."""
        self.index.text = self.valid_template + self.other_template
        self.assertFalse(self.index.has_valid_content())

    def test_has_valid_content_wrong_template(self):
        """Test incorrect template is invalid."""
        self.index.text = self.other_template
        self.assertFalse(self.index.has_valid_content())

    def test_has_valid_content_missnamed_template(self):
        """Test nested templates is valid."""
        self.index.text = '{{%s_bar|foo=bar}}' % IndexPage.INDEX_TEMPLATE
        self.assertFalse(self.index.has_valid_content())

    def test_has_valid_content_nested_template(self):
        """Test nested templates is valid."""
        self.index.text = ('{{%s|foo=%s}}'
                           % (IndexPage.INDEX_TEMPLATE, self.other_template))
        self.assertTrue(self.index.has_valid_content())

    def test_has_valid_content_multiple_valid(self):
        """Test multiple Index templates is invalid."""
        self.index.text = self.valid_template * 2
        self.assertFalse(self.index.has_valid_content())


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
