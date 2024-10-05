#!/usr/bin/env python3
"""FilePage tests."""
#
# (C) Pywikibot team, 2014-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import os
import re
import unittest
from contextlib import suppress
from itertools import chain

import pywikibot
from pywikibot import pagegenerators
from pywikibot.exceptions import (
    Error,
    NoPageError,
    NoWikibaseEntityError,
    PageRelatedError,
)
from tests import join_images_path
from tests.aspects import TestCase


class TestSharedFiles(TestCase):

    """Test file_is_shared, exists, fileUrl/get_file_url with shared files."""

    sites = {
        'enwiki': {
            'family': 'wikipedia',
            'code': 'en',
        },
        'itwiki': {
            'family': 'wikipedia',
            'code': 'it',
        },
        'testwiki': {
            'family': 'wikipedia',
            'code': 'test',
        },
        'commons': {
            'family': 'commons',
            'code': 'commons',
        },
    }

    cached = True

    def test_shared_only(self):
        """Test file_is_shared() on file page with shared file only."""
        title = 'File:Sepp Maier 1.JPG'

        commons = self.get_site('commons')
        itwp = self.get_site('itwiki')
        itwp_file = pywikibot.FilePage(itwp, title)
        commons_file = pywikibot.FilePage(commons, title)

        self.assertFalse(itwp_file.exists())
        self.assertTrue(commons_file.exists())

        self.assertTrue(itwp_file.file_is_shared())
        self.assertFalse(itwp_file.file_is_used)
        self.assertTrue(commons_file.file_is_shared())
        self.assertTrue(commons_file.file_is_used)
        self.assertTrue(commons_file.get_file_url())

        for using in commons_file.using_pages():
            self.assertIsInstance(using, pywikibot.Page)

        self.assertIn('/wikipedia/commons/', itwp_file.get_file_url())
        with self.assertRaisesRegex(
                NoPageError,
                rf'Page \[\[(wikipedia:|)it:{title}\]\] doesn\'t exist.'):
            itwp_file.get()

    def test_local_only(self):
        """Test file_is_shared() on file page with local file only."""
        title = 'File:Untitled (Three Forms), stainless steel sculpture by ' \
                '--James Rosati--, 1975-1976, --Honolulu Academy of Arts--.JPG'

        commons = self.get_site('commons')
        enwp = self.get_site('enwiki')
        enwp_file = pywikibot.FilePage(enwp, title)
        for using in enwp_file.using_pages():
            self.assertIsInstance(using, pywikibot.Page)

        commons_file = pywikibot.FilePage(commons, title)

        self.assertTrue(enwp_file.latest_file_info.url)
        self.assertTrue(enwp_file.exists())
        self.assertFalse(commons_file.exists())

        self.assertFalse(enwp_file.file_is_shared())
        self.assertFalse(commons_file.file_is_shared())

        page_doesnt_exist_exc_regex = re.escape(
            f"Page [[commons:{title}]] doesn't exist.")

        with self.assertRaisesRegex(
                NoPageError,
                page_doesnt_exist_exc_regex):
            commons_file.get_file_url()

        with self.assertRaisesRegex(
                NoPageError,
                page_doesnt_exist_exc_regex):
            commons_file.get()

    def test_on_both(self):
        """Test file_is_shared() on file page with local and shared file."""
        title = 'Pywikibot MW gear icon.svg'

        commons = self.get_site('commons')
        testwp = self.get_site('testwiki')
        testwp_file = pywikibot.FilePage(testwp, title)
        for using in testwp_file.using_pages():
            self.assertIsInstance(using, pywikibot.Page)

        commons_file = pywikibot.FilePage(commons, title)

        self.assertTrue(testwp_file.get_file_url())
        self.assertTrue(testwp_file.exists())
        self.assertTrue(commons_file.exists())

        self.assertFalse(testwp_file.file_is_shared())
        self.assertTrue(testwp_file.file_is_used)
        self.assertTrue(commons_file.file_is_shared())
        self.assertTrue(commons_file.file_is_used)

    def test_non_file_local(self):
        """Test file page, without local file, existing on the local wiki."""
        title = 'File:Sepp Maier 1.JPG'

        commons = self.get_site('commons')
        testwp = self.get_site('testwiki')
        testwp_file = pywikibot.FilePage(testwp, title)

        self.assertTrue(testwp_file.latest_file_info.url)
        self.assertTrue(testwp_file.exists())
        self.assertTrue(testwp_file.file_is_shared())

        commons_file = pywikibot.FilePage(commons, title)
        self.assertEqual(testwp_file.get_file_url(),
                         commons_file.get_file_url())


class TestFilePage(TestCase):

    """Test FilePage.latest_revision_info.

    These tests cover exceptions for all properties and methods
    in FilePage that rely on site.loadimageinfo.

    """

    family = 'wikipedia'
    code = 'test'

    file_name = 'File:Albert Einstein Head.jpg'

    cached = True

    def test_file_info_with_no_page(self):
        """FilePage:latest_file_info raises NoPageError for missing pages."""
        site = self.get_site()
        image = pywikibot.FilePage(site, 'File:NoPage.jpg')
        self.assertFalse(image.exists())

        with self.assertRaisesRegex(
                NoPageError,
                (r'Page \[\[(wikipedia\:|)test:File:NoPage\.jpg\]\] '
                 r"doesn't exist\.")):
            image = image.latest_file_info

    def test_file_info_with_no_file(self):
        """FilePage:latest_file_info raises PagerelatedError if no file."""
        site = self.get_site()
        image = pywikibot.FilePage(site, 'File:Test with no image.png')
        self.assertTrue(image.exists())
        with self.assertRaisesRegex(
                PageRelatedError,
                (r'loadimageinfo: Query on '
                 r'\[\[(wikipedia\:|)test:File:Test with no image\.png\]\]'
                 r' returned no imageinfo')):
            image = image.latest_file_info


class TestFilePageCommons(TestCase):

    """Test methods of the FilePage class on Commons."""

    family = 'commons'
    code = 'commons'
    cached = True

    def test_globalusage(self, key):
        """Test globalusage generator."""
        page = pywikibot.FilePage(self.site, 'File:Example.jpg')
        gen = page.globalusage(total=3)
        pages = list(gen)
        self.assertLength(pages, 3)
        for p in pages:
            self.assertIsInstance(p, pywikibot.Page)
            self.assertNotEqual(p.site, self.site)


class TestFilePageLatestFileInfo(TestCase):

    """Test FilePage.latest_file_info.

    These tests cover properties and methods in FilePage that rely
    on site.loadimageinfo.

    """

    family = 'commons'
    code = 'commons'

    file_name = 'File:Albert Einstein Head.jpg'

    cached = True

    def setUp(self):
        """Create File page."""
        super().setUp()
        self.image = pywikibot.FilePage(self.site, self.file_name)

    def test_lazyload_metadata(self):
        """Test metadata lazy load."""
        self.assertTrue(self.image.exists())

        rev = self.image.latest_file_info
        self.assertIsNone(rev._metadata)
        self.assertIsNotNone(rev.metadata)

    def test_get_file_url(self):
        """Get File url."""
        self.assertTrue(self.image.exists())
        self.assertEqual(self.image.get_file_url(),
                         'https://upload.wikimedia.org/wikipedia/commons/'
                         'd/d3/Albert_Einstein_Head.jpg')
        self.assertEqual(self.image.latest_file_info.url,
                         'https://upload.wikimedia.org/wikipedia/commons/'
                         'd/d3/Albert_Einstein_Head.jpg')

    def test_get_file_url_thumburl_from_width(self):
        """Get File thumburl from width."""
        self.assertTrue(self.image.exists())
        # url_param has no precedence over height/width.
        self.assertEqual(
            self.image.get_file_url(url_width=100, url_param='1000px'),
            'https://upload.wikimedia.org/wikipedia/commons/thumb/'
            'd/d3/Albert_Einstein_Head.jpg/100px-Albert_Einstein_Head.jpg')
        self.assertEqual(self.image.latest_file_info.thumbwidth, 100)
        self.assertEqual(self.image.latest_file_info.thumbheight, 133)

    def test_get_file_url_thumburl_from_height(self):
        """Get File thumburl from height."""
        self.assertTrue(self.image.exists())
        # url_param has no precedence over height/width.
        self.assertEqual(
            self.image.get_file_url(url_height=100, url_param='1000px'),
            'https://upload.wikimedia.org/wikipedia/commons/thumb/'
            'd/d3/Albert_Einstein_Head.jpg/75px-Albert_Einstein_Head.jpg')
        self.assertEqual(self.image.latest_file_info.thumbwidth, 75)
        self.assertEqual(self.image.latest_file_info.thumbheight, 100)

    def test_get_file_url_thumburl_from_url_param(self):
        """Get File thumburl from height."""
        self.assertTrue(self.image.exists())
        # url_param has no precedence over height/width.
        self.assertEqual(
            self.image.get_file_url(url_param='100px'),
            'https://upload.wikimedia.org/wikipedia/commons/thumb/'
            'd/d3/Albert_Einstein_Head.jpg/100px-Albert_Einstein_Head.jpg')
        self.assertEqual(self.image.latest_file_info.thumbwidth, 100)
        self.assertEqual(self.image.latest_file_info.thumbheight, 133)


class TestFilePageDownload(TestCase):

    """Test download of FilePage to local file."""

    family = 'commons'
    code = 'commons'

    cached = True

    def test_successful_download(self):
        """Test successful download."""
        page = pywikibot.FilePage(self.site, 'File:Albert Einstein.jpg')
        filename = join_images_path('Albert Einstein.jpg')
        status_code = page.download(filename)
        self.assertTrue(status_code)
        oldsize = os.stat(filename).st_size

        status_code = page.download(filename, url_height=128)
        self.assertTrue(status_code)
        size = os.stat(filename).st_size
        self.assertLess(size, oldsize)

        status_code = page.download(filename, url_width=120)
        self.assertTrue(status_code)
        size = os.stat(filename).st_size
        self.assertLess(size, oldsize)

        status_code = page.download(filename, url_param='120px')
        self.assertTrue(status_code)
        self.assertEqual(size, os.stat(filename).st_size)

        os.remove(filename)

    def test_changed_title(self):
        """Test changed title."""
        page = pywikibot.FilePage(self.site, 'Pywikibot MW gear icon.svg')
        filename = join_images_path('Pywikibot MW gear icon.svg')
        status_code = page.download(filename)
        self.assertTrue(status_code)
        self.assertTrue(os.path.exists(filename))

        status_code = page.download(filename, url_param='120px')
        self.assertTrue(status_code)
        new_filename = filename.replace('.svg', '.png')
        self.assertTrue(os.path.exists(new_filename))

        os.remove(filename)
        os.remove(new_filename)

    def test_not_existing_download(self):
        """Test not existing download."""
        page = pywikibot.FilePage(self.site,
                                  'File:notexisting_Albert Einstein.jpg')
        filename = join_images_path('Albert Einstein.jpg')

        with self.assertRaisesRegex(
                NoPageError,
                re.escape('Page [[commons:File:Notexisting Albert '
                          "Einstein.jpg]] doesn't exist.")):
            page.download(filename)


class TestFilePageDataItem(TestCase):

    """Test structured data of FilePage."""

    family = 'commons'
    code = 'commons'

    cached = True

    def test_data_item(self):
        """Test associated data item."""
        page = pywikibot.FilePage(self.site, 'File:Albert Einstein.jpg')
        item = page.data_item()
        self.assertIsInstance(item, pywikibot.MediaInfo)
        self.assertTrue(page._item is item)
        self.assertTrue(item.file is page)
        self.assertEqual('-1', item.id)
        item.get()
        self.assertEqual('M14634781', item.id)
        self.assertEqual('M14634781', item.title())
        self.assertIsInstance(
            item.labels, pywikibot.page._collections.LanguageDict)
        self.assertIsInstance(
            item.statements, pywikibot.page._collections.ClaimCollection)
        self.assertTrue(item.claims is item.statements)

        all_claims = list(chain.from_iterable(item.statements.values()))
        self.assertEqual({claim.on_item for claim in all_claims}, {item})

        claims = [claim for claim in all_claims
                  if isinstance(claim.target, pywikibot.page.WikibaseEntity)]
        self.assertEqual({str(claim.repo) for claim in claims},
                         {'wikidata:wikidata'})
        self.assertEqual({str(claim.target.repo) for claim in claims},
                         {'wikidata:wikidata'})

        del item._file
        self.assertEqual(page, item.file)

    def test_data_item_not_file(self):
        """Test data item with invalid pageid."""
        item = pywikibot.MediaInfo(self.site, 'M1')  # Main Page
        with self.assertRaises(Error):
            item.file
        with self.assertRaises(NoWikibaseEntityError):
            item.get()
        self.assertFalse(item.exists())

    def test_data_item_when_no_file_or_data_item(self):
        """Test data item associated to file that does not exist."""
        page = pywikibot.FilePage(self.site,
                                  'File:Notexisting_Albert Einstein.jpg')
        self.assertFalse(page.exists())
        item = page.data_item()
        self.assertIsInstance(item, pywikibot.MediaInfo)

        with self.assertRaises(NoWikibaseEntityError):
            item.get()
        with self.assertRaises(NoWikibaseEntityError):
            item.title()
        with self.assertRaises(NoWikibaseEntityError):
            item.labels

    def test_data_item_when_file_exist_but_without_item(self):
        """Test if data item is missing from file."""
        # Get latest uploaded files.
        gen = pagegenerators.RecentChangesPageGenerator(
            site=self.site,
            namespaces=[6],  # File namespace
            changetype='new',
            total=100
        )

        # Seek to first page without mediainfo.
        for page in gen:
            slots = page.latest_revision.slots
            if 'mediainfo' not in slots:
                break
        else:
            self.skipTest('No page found without mediainfo')

        item = page.data_item()
        self.assertIsInstance(item, pywikibot.MediaInfo)

        self.assertTrue(item.exists())
        self.assertEqual(f'M{page.pageid}', item.id)
        self.assertIsInstance(
            item.labels, pywikibot.page._collections.LanguageDict)
        self.assertIsInstance(
            item.statements,
            pywikibot.page._collections.ClaimCollection)

    def test_data_list_to_dict_workaround(self):
        """Test that T222159 workaround converts [] to {}."""
        page = pywikibot.FilePage(self.site, 'File:Albert Einstein.jpg')
        item = page.data_item()
        item.get(force=True)
        item._content['labels'] = []
        item._content['statements'] = []
        item.get()
        self.assertIsInstance(
            item.labels, pywikibot.page._collections.LanguageDict)
        self.assertIsInstance(
            item.statements, pywikibot.page._collections.ClaimCollection)


class TestMediaInfoEditing(TestCase):

    """Test writing structured data of FilePage."""

    login = True
    write = True

    # commons.wikimedia.beta.wmflabs.org
    family = 'commons'
    code = 'beta'

    def test_edit_label(self):
        """Test label editing."""
        # Test label editing when file doesn't exists
        page = pywikibot.FilePage(self.site, 'File:123_4_DOESNT_EXISTS.jpg')
        item = page.data_item()
        error_message = "Entity '-1' doesn't exist on commons:beta"
        lang = 'fi'

        data = {}
        label = 'Edit label of missing file with editEntity and dict()'
        data.update({'labels': {lang: label}})
        with self.assertRaisesRegex(NoWikibaseEntityError, error_message):
            item.editEntity(data, summary=label)

        label = 'Edit label of missing file with editLabels and dict()'
        data = {lang: label}
        with self.assertRaisesRegex(NoWikibaseEntityError, error_message):
            item.editLabels(data, summary=label)

        # Test label editing when file exists
        page = pywikibot.FilePage(self.site, 'File:123_4.jpg')
        item = page.data_item()
        lang = 'fi'

        label = 'Edit label with editEntity and dict()'
        data = {}
        data.update({'labels': {lang: label}})
        item.editEntity(data, summary=label)
        item.get(force=True)
        self.assertEqual(item.labels['fi'], label)

        label = 'Edit label with editEntity and item'
        item.labels['fi'] = label
        item.editEntity(item.toJSON(), summary=label)
        item.get(force=True)
        self.assertEqual(item.labels['fi'], label)

        label = 'Edit label with editLabels and dict()'
        data = {lang: label}
        item.editLabels(data, summary=label)
        item.get(force=True)
        self.assertEqual(item.labels['fi'], label)

    def test_edit_claims(self):
        """Test addClaim and removeClaim editing."""
        wikidata_site = pywikibot.Site('beta', 'wikidata')

        # Create claim

        property_id = 'P766'  # date of publication
        new_claim = pywikibot.Claim(wikidata_site, 'P766')
        new_claim_value = pywikibot.WbTime(2024, 1, 1)
        new_claim.setTarget(new_claim_value)

        # Test adding claim to non-existing file
        page = pywikibot.FilePage(self.site, 'File:123_4_DOESNT_EXISTS.jpg')
        item = page.data_item()

        # Insert claim to non-existing file
        with self.assertRaises(NoWikibaseEntityError):
            item.addClaim(new_claim)

        # Insert claim using site object to non-existing file
        with self.assertRaises(NoWikibaseEntityError):
            self.site.addClaim(item, new_claim)

        # Test adding claim existing file
        page = pywikibot.FilePage(self.site, 'File:123_4.jpg')
        item = page.data_item()

        # Test adding claim using MediaInfo.addClaim()
        item.addClaim(new_claim)

        # Test that claim can be found
        claim_found = False
        item.get(force=True)
        for statement in item.statements.get(property_id):
            value = statement.getTarget()
            if value == new_claim_value:
                claim_found = True
                summary = f'Removing {property_id} with {value}'
                item.removeClaims(statement, summary=summary)

        self.assertTrue(claim_found)

        # Test that the claim was removed

        claim_found = False
        item.get(force=True)
        for statement in item.statements.get(property_id, []):
            value = statement.getTarget()
            if value == new_claim_value:
                claim_found = True

        self.assertFalse(claim_found)

        # Add claim using site object
        self.site.addClaim(item, new_claim)

        # Test that the claim can be found and remove it using site object

        claim_found = False
        item.get(force=True)
        for statement in item.statements.get(property_id):
            value = statement.getTarget()
            remove_statements = []
            if value == new_claim_value:
                remove_statements.append(statement)
                claim_found = True

        self.assertTrue(claim_found)

        # Note removeClaims() parameter needs to be array
        summary = f'Removing {property_id} with {value} using site object'
        self.site.removeClaims(remove_statements, summary=summary)

        # Test that the claims were actually removed

        claim_found = False
        item.get(force=True)
        for statement in item.statements.get(property_id, []):
            value = statement.getTarget()
            if value == new_claim_value:
                claim_found = True

        self.assertFalse(claim_found)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
