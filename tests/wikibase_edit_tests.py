# -*- coding: utf-8 -*-
"""
Tests for editing Wikibase items.

Tests which should fail should instead be in the TestWikibaseSaveTest
class in edit_failiure_tests.py
"""
#
# (C) Pywikibot team, 2014-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import time

import pywikibot
from pywikibot.tools import MediaWikiVersion

from tests.aspects import unittest, WikibaseTestCase


class TestWikibaseWriteGeneral(WikibaseTestCase):

    """Run general wikibase write tests."""

    family = 'wikidata'
    code = 'test'

    user = True
    write = True

    def test_label_set(self):
        """Test setting an English label."""
        testsite = self.get_repo()
        item = pywikibot.ItemPage(testsite, 'Q68')
        self.assertIsInstance(item, pywikibot.ItemPage)
        self.assertEqual(item.getID(), 'Q68')
        item.editLabels({'en': 'Test123'})
        item.get(force=True)
        self.assertEqual(item.labels['en'], 'Test123')

    def test_label_remove(self):
        """Test adding a Farsi and English label and removing the Farsi one."""
        testsite = self.get_repo()
        item = pywikibot.ItemPage(testsite, 'Q68')
        # These two should be additive
        item.editLabels({'en': 'Test123'})
        item.editLabels({'fa': 'Test123'})
        item.get(force=True)
        self.assertIn('en', item.labels.keys())
        self.assertIn('fa', item.labels.keys())

        # This should remove the 'fa' label
        item.editLabels({'en': 'Test123', 'fa': ''})

        # Check 'fa' label is removed
        item = pywikibot.ItemPage(testsite, 'Q68')
        item.get()
        self.assertNotIn('fa', item.labels.keys())

    def test_alias_set(self):
        """Test setting an English alias."""
        testsite = self.get_repo()
        ts = str(time.time())
        item = pywikibot.ItemPage(testsite, 'Q68')
        item.editAliases({'en': [ts]})

    def test_add_claim_with_qualifier(self):
        """Test adding a claim with a qualifier to an item and a property."""
        testsite = self.get_repo()
        item = pywikibot.ItemPage(testsite, 'Q68')
        item.get()
        if 'P115' in item.claims:
            item.removeClaims(item.claims['P115'])

        claim = pywikibot.page.Claim(testsite, 'P115', datatype='wikibase-item')
        target = pywikibot.ItemPage(testsite, 'Q271')
        claim.setTarget(target)

        item.addClaim(claim)

        item.get(force=True)

        end_date = pywikibot.page.Claim(testsite, 'P88', isQualifier=True)
        end_date.setTarget(pywikibot.WbTime(year=2012))
        item.claims['P115'][0].addQualifier(end_date)

        # Testing all again but this time in properties
        item = pywikibot.PropertyPage(testsite, 'P115')
        item.get()
        if 'P115' in item.claims:
            to_remove = []
            for claim in item.claims['P115']:
                to_remove.append({'id': claim.toJSON()['id'], 'remove': ''})
            item.editEntity({'claims': to_remove})

        claim = pywikibot.page.Claim(testsite, 'P115', datatype='wikibase-item')
        target = pywikibot.ItemPage(testsite, 'Q271')
        claim.setTarget(target)
        item.editEntity({'claims': [claim.toJSON()]})

        item.get(force=True)

        end_date = pywikibot.page.Claim(testsite, 'P88', isQualifier=True)
        end_date.setTarget(pywikibot.WbTime(year=2012))
        item.claims['P115'][0].addQualifier(end_date)

    def test_edit_entity_new_item(self):
        """Test creating a new item using C{ItemPage.editEntity}."""
        testsite = self.get_repo()
        ts = str(time.time())
        data = {
            'labels': {
                'en': {
                    'language': 'en',
                    'value': 'Pywikibot test new item',
                }
            },
            'descriptions': {
                'en': {
                    'language': 'en',
                    'value': 'Pywikibot test new item - ' + ts,
                }
            }
        }
        item = pywikibot.ItemPage(testsite)
        item.editEntity(data)

    def test_edit_entity_new_linked_item(self):
        """Test linking a page using a new item."""
        ts = str(time.time())

        # Create a new page, which is unlinked
        site = self.get_site()
        title = 'Wikidata:Test ' + ts
        page = pywikibot.Page(site, title)
        page.text = ts
        page.save()

        data = {
            'labels': {
                'en': {
                    'language': 'en',
                    'value': 'Pywikibot test new linked item',
                }
            },
            'sitelinks': {
                page.site.dbName(): {
                    'site': page.site.dbName(),
                    'title': page.title()
                }
            },
        }

        repo = self.get_repo()
        item = pywikibot.ItemPage(repo)
        self.assertEqual(item._defined_by(), dict())
        item.editEntity(data)

    def test_set_redirect_target(self):
        """Test set_redirect_target method."""
        testsite = self.get_repo()
        item = pywikibot.ItemPage(testsite, 'Q1107')
        target_id = 'Q68'
        if not item.isRedirectPage():
            item.editEntity(data={}, clear=True)
        elif item.getRedirectTarget().getID() == 'Q68':
            target_id = 'Q67'
        target_item = pywikibot.ItemPage(testsite, target_id)
        item.set_redirect_target(target_id, force=True)
        self.assertTrue(item.isRedirectPage())
        new_item = pywikibot.ItemPage(testsite, item.getID())
        self.assertTrue(new_item.isRedirectPage())
        self.assertEqual(new_item.getRedirectTarget(), target_item)


class TestWikibaseMakeClaim(WikibaseTestCase):

    """Run wikibase write tests for claims."""

    family = 'wikidata'
    code = 'test'

    user = True
    write = True

    def _clean_item(self, repo, prop):
        """
        Return an item without any existing claims of the given property.

        @param repo: repository to fetch item from
        @type: pywikibot.site.DataSite
        @param prop: P-value of the property to scrub
        @type prop: str
        @return: scrubbed item
        @rtype: pywikibot.ItemPage
        """
        item = pywikibot.ItemPage(repo, 'Q68')
        item.get()
        if prop in item.claims:
            item.removeClaims(item.claims[prop])
        item.get(force=True)
        return item

    def test_math_edit(self):
        """Attempt adding a math claim with valid input."""
        testsite = self.get_repo()
        item = self._clean_item(testsite, 'P717')

        # set new claim
        claim = pywikibot.page.Claim(testsite, 'P717', datatype='math')
        target = 'a^2 + b^2 = c^2'
        claim.setTarget(target)
        item.addClaim(claim)

        # confirm new claim
        item.get(force=True)
        claim = item.claims['P717'][0]
        self.assertEqual(claim.getTarget(), target)

    def test_WbMonolingualText_edit(self):
        """Attempt adding a monolingual text with valid input."""
        # Clean the slate in preparation for test.
        testsite = self.get_repo()
        item = self._clean_item(testsite, 'P271')

        # set new claim
        claim = pywikibot.page.Claim(testsite, 'P271', datatype='monolingualtext')
        target = pywikibot.WbMonolingualText(text='Test this!', language='en')
        claim.setTarget(target)
        item.addClaim(claim)

        # confirm new claim
        item.get(force=True)
        claim = item.claims['P271'][0]
        self.assertEqual(claim.getTarget(), target)

    def test_Coordinate_edit(self):
        """Attempt adding a Coordinate with globe set via item."""
        testsite = self.get_repo()
        item = self._clean_item(testsite, 'P20480')

        # Make sure the wiki supports wikibase-conceptbaseuri
        version = testsite.version()
        if MediaWikiVersion(version) < MediaWikiVersion('1.29.0-wmf.2'):
            raise unittest.SkipTest('Wiki version must be 1.29.0-wmf.2 or '
                                    'newer to support unbound uncertainties.')

        # set new claim
        claim = pywikibot.page.Claim(testsite, 'P20480',
                                     datatype='globe-coordinate')
        target = pywikibot.Coordinate(site=testsite, lat=12.0, lon=13.0,
                                      globe_item=item)
        claim.setTarget(target)
        item.addClaim(claim)

        # confirm new claim
        item.get(force=True)
        claim = item.claims['P20480'][0]
        self.assertEqual(claim.getTarget(), target)

    def test_WbQuantity_edit_unbound(self):
        """Attempt adding a quantity with unbound errors."""
        # Clean the slate in preparation for test.
        testsite = self.get_repo()
        item = self._clean_item(testsite, 'P69')

        # Make sure the wiki supports unbound uncertainties
        version = testsite.version()
        if MediaWikiVersion(version) < MediaWikiVersion('1.29.0-wmf.2'):
            raise unittest.SkipTest('Wiki version must be 1.29.0-wmf.2 or '
                                    'newer to support unbound uncertainties.')

        # set new claim
        claim = pywikibot.page.Claim(testsite, 'P69', datatype='quantity')
        target = pywikibot.WbQuantity(amount=1234)
        claim.setTarget(target)
        item.addClaim(claim)

        # confirm new claim
        item.get(force=True)
        claim = item.claims['P69'][0]
        self.assertEqual(claim.getTarget(), target)

    def test_WbQuantity_edit(self):
        """Attempt adding a quantity with valid input."""
        # Clean the slate in preparation for test.
        testsite = self.get_repo()
        item = self._clean_item(testsite, 'P69')

        # Make sure the wiki supports wikibase-conceptbaseuri
        version = testsite.version()
        if MediaWikiVersion(version) < MediaWikiVersion('1.28-wmf.23'):
            raise unittest.SkipTest('Wiki version must be 1.28-wmf.23 or '
                                    'newer to expose wikibase-conceptbaseuri.')

        # set new claim
        claim = pywikibot.page.Claim(testsite, 'P69', datatype='quantity')
        target = pywikibot.WbQuantity(amount=1234, error=1, unit=item)
        claim.setTarget(target)
        item.addClaim(claim)

        # confirm new claim
        item.get(force=True)
        claim = item.claims['P69'][0]
        self.assertEqual(claim.getTarget(), target)

    def test_identifier_edit(self):
        """Attempt adding a math claim with valid input."""
        testsite = self.get_repo()
        item = self._clean_item(testsite, 'P718')

        # set new claim
        claim = pywikibot.page.Claim(testsite, 'P718', datatype='external-id')
        target = 'CrazyURI123_:)'
        claim.setTarget(target)
        item.addClaim(claim)

        # confirm new claim
        item.get(force=True)
        claim = item.claims['P718'][0]
        self.assertEqual(claim.getTarget(), target)

    def test_WbGeoShape_edit(self):
        """Attempt adding a geo-shape with valid input."""
        # Clean the slate in preparation for test.
        testsite = self.get_repo()
        item = self._clean_item(testsite, 'P27199')

        # set new claim
        claim = pywikibot.page.Claim(testsite, 'P27199', datatype='geo-shape')
        commons_site = pywikibot.Site('commons', 'commons')
        page = pywikibot.Page(commons_site, 'Data:Lyngby Hovedgade.map')
        target = pywikibot.WbGeoShape(page)
        claim.setTarget(target)
        item.addClaim(claim)

        # confirm new claim
        item.get(force=True)
        claim = item.claims['P27199'][0]
        self.assertEqual(claim.getTarget(), target)


class TestWikibaseRemoveQualifier(WikibaseTestCase):

    """Run wikibase write tests to remove qualifiers."""

    family = 'wikidata'
    code = 'test'

    user = True
    write = True

    def setUp(self):
        """Add a claim with two qualifiers."""
        super(TestWikibaseRemoveQualifier, self).setUp()
        testsite = self.get_repo()
        item = pywikibot.ItemPage(testsite, 'Q68')
        item.get()
        # Create claim with qualifier
        if 'P115' in item.claims:
            item.removeClaims(item.claims['P115'])

        claim = pywikibot.page.Claim(testsite, 'P115', datatype='wikibase-item')
        target = pywikibot.ItemPage(testsite, 'Q271')
        claim.setTarget(target)
        item.addClaim(claim)

        item.get(force=True)

        qual_1 = pywikibot.page.Claim(testsite, 'P88', isQualifier=True)
        qual_1.setTarget(pywikibot.WbTime(year=2012))
        item.claims['P115'][0].addQualifier(qual_1)

        qual_2 = pywikibot.page.Claim(testsite, 'P580', isQualifier=True)
        qual_2.setTarget(pywikibot.ItemPage(testsite, 'Q67'))
        item.claims['P115'][0].addQualifier(qual_2)

    def test_remove_single(self):
        """Test adding a claim with two qualifiers, then removing one."""
        self.setUp()
        testsite = self.get_repo()
        item = pywikibot.ItemPage(testsite, 'Q68')
        item.get(force=True)

        # Remove qualifier
        claim = item.claims['P115'][0]
        qual_3 = claim.qualifiers[u'P580'][0]
        claim.removeQualifier(qual_3)

        # Check P580 qualifier removed but P88 qualifier remains
        item = pywikibot.ItemPage(testsite, 'Q68')
        item.get(force=True)
        claim = item.claims['P115'][0]
        self.assertNotIn('P580', claim.qualifiers.keys())
        self.assertIn('P88', claim.qualifiers.keys())

    def test_remove_multiple(self):
        """Test adding a claim with two qualifiers, then removing both."""
        self.setUp()
        testsite = self.get_repo()
        item = pywikibot.ItemPage(testsite, 'Q68')
        item.get(force=True)

        # Remove qualifiers
        item.get(force=True)
        claim = item.claims['P115'][0]
        qual_3 = claim.qualifiers[u'P580'][0]
        qual_4 = claim.qualifiers[u'P88'][0]
        claim.removeQualifiers([qual_3, qual_4])

        # Check P580 and P88 qualifiers are removed
        item = pywikibot.ItemPage(testsite, 'Q68')
        item.get(force=True)
        claim = item.claims['P115'][0]
        self.assertNotIn('P580', claim.qualifiers.keys())
        self.assertNotIn('P88', claim.qualifiers.keys())

if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
