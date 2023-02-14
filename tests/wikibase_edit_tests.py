#!/usr/bin/env python3
"""
Tests for editing Wikibase items.

Tests which should fail should instead be in the TestWikibaseSaveTest
class in edit_failiure_tests.py
"""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import time
import unittest
from contextlib import suppress

import pywikibot
from tests.aspects import WikibaseTestCase


class TestWikibaseWriteGeneral(WikibaseTestCase):

    """Run general wikibase write tests."""

    family = 'wikidata'
    code = 'test'

    login = True
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

        claim = pywikibot.page.Claim(
            testsite, 'P115', datatype='wikibase-item')
        target = pywikibot.ItemPage(testsite, 'Q271')
        claim.setTarget(target)

        item.addClaim(claim)

        item.get(force=True)

        end_date = pywikibot.page.Claim(testsite, 'P88', is_qualifier=True)
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

        claim = pywikibot.page.Claim(
            testsite, 'P115', datatype='wikibase-item')
        target = pywikibot.ItemPage(testsite, 'Q271')
        claim.setTarget(target)
        item.editEntity({'claims': [claim.toJSON()]})

        item.get(force=True)

        end_date = pywikibot.page.Claim(testsite, 'P88', is_qualifier=True)
        end_date.setTarget(pywikibot.WbTime(year=2012))
        item.claims['P115'][0].addQualifier(end_date)

    def test_edit_entity_new_item(self):
        """Test creating a new item using ``ItemPage.editEntity``."""
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

    def test_edit_entity_propogation(self):
        """Test that ``ItemPage.editEntity`` propagates changes to claims."""
        testsite = self.get_repo()
        item = pywikibot.ItemPage(testsite)
        claim = pywikibot.Claim(testsite, 'P97339')
        claim.setTarget('test')
        qual = pywikibot.Claim(testsite, 'P97339')
        qual.setTarget('test')
        ref = pywikibot.Claim(testsite, 'P97339')
        ref.setTarget('test')
        claim.addQualifier(qual)
        claim.addSource(ref)
        item.editEntity()
        self.assertIsNotNone(claim.snak)
        self.assertIsNotNone(qual.hash)
        self.assertIsNotNone(ref.hash)
        self.assertSame(claim.on_item, item)
        self.assertSame(qual.on_item, item)
        self.assertSame(ref.on_item, item)
        qual = pywikibot.Claim(testsite, 'P97339')
        qual.setTarget('test')
        ref = pywikibot.Claim(testsite, 'P97339')
        ref.setTarget('test')
        claim.qualifiers[qual.id].append(qual)
        claim.sources[0][ref.id].append(ref)
        item.editEntity()
        self.assertIsNotNone(qual.hash)
        self.assertIsNotNone(ref.hash)
        self.assertSame(qual.on_item, item)
        self.assertSame(ref.on_item, item)

    def test_edit_entity_new_property(self):
        """Test creating a new property using ``PropertyPage.editEntity``."""
        testsite = self.get_repo()
        ts = str(time.time())
        data = {
            'labels': {
                'en': {
                    'language': 'en',
                    'value': 'Pywikibot test new property',
                }
            },
            'descriptions': {
                'en': {
                    'language': 'en',
                    'value': 'Pywikibot test new property - ' + ts,
                }
            }
        }
        prop = pywikibot.PropertyPage(testsite, datatype='string')
        prop.editEntity(data)

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
        self.assertEqual(item._defined_by(), {})
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

    login = True
    write = True

    @staticmethod
    def _clean_item(repo, prop: str):
        """
        Return an item without any existing claims of the given property.

        :param repo: repository to fetch item from
        :type repo: pywikibot.site.DataSite
        :param prop: P-value of the property to scrub
        :return: scrubbed item
        :rtype: pywikibot.ItemPage
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
        claim = pywikibot.page.Claim(
            testsite, 'P271', datatype='monolingualtext')
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
        if testsite.mw_version < '1.29.0-wmf.2':
            self.skipTest('Wiki version must be 1.29.0-wmf.2 or newer to '
                          'support unbound uncertainties.')

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
        if testsite.mw_version < '1.29.0-wmf.2':
            self.skipTest('Wiki version must be 1.29.0-wmf.2 or newer to '
                          'support unbound uncertainties.')

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
        if testsite.mw_version < '1.28-wmf.23':
            self.skipTest('Wiki version must be 1.28-wmf.23 or newer to '
                          'expose wikibase-conceptbaseuri.')

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
        """Attempt adding an external identifier claim with valid input."""
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
        commons_site = pywikibot.Site('commons')
        page = pywikibot.Page(commons_site, 'Data:Lyngby Hovedgade.map')
        target = pywikibot.WbGeoShape(page)
        claim.setTarget(target)
        item.addClaim(claim)

        # confirm new claim
        item.get(force=True)
        claim = item.claims['P27199'][0]
        self.assertEqual(claim.getTarget(), target)

    def test_WbTabularData_edit(self):
        """Attempt adding a tabular-data with valid input."""
        # Clean the slate in preparation for test.
        testsite = self.get_repo()
        item = self._clean_item(testsite, 'P30175')

        # set new claim
        claim = pywikibot.page.Claim(
            testsite, 'P30175', datatype='tabular-data')
        commons_site = pywikibot.Site('commons')
        page = pywikibot.Page(commons_site, 'Data:Bea.gov/GDP by state.tab')
        target = pywikibot.WbGeoShape(page)
        claim.setTarget(target)
        item.addClaim(claim)

        # confirm new claim
        item.get(force=True)
        claim = item.claims['P30175'][0]
        self.assertEqual(claim.getTarget(), target)

    def test_musical_notation_edit(self):
        """Attempt adding a musical notation claim with valid input."""
        testsite = self.get_repo()
        item = self._clean_item(testsite, 'P88936')

        # set new claim
        claim = pywikibot.page.Claim(
            testsite, 'P88936', datatype='musical-notation')
        target = "\relative c' { c d e f | g2 g | a4 a a a | g1 |})"
        claim.setTarget(target)
        item.addClaim(claim)

        # confirm new claim
        item.get(force=True)
        claim = item.claims['P88936'][0]
        self.assertEqual(claim.getTarget(), target)


class TestWikibaseRemoveQualifier(WikibaseTestCase):

    """Run wikibase write tests to remove qualifiers."""

    family = 'wikidata'
    code = 'test'

    login = True
    write = True

    def setUp(self):
        """Add a claim with two qualifiers."""
        super().setUp()
        testsite = self.get_repo()
        item = pywikibot.ItemPage(testsite, 'Q68')
        item.get()
        # Create claim with qualifier
        if 'P115' in item.claims:
            item.removeClaims(item.claims['P115'])

        claim = pywikibot.page.Claim(
            testsite, 'P115', datatype='wikibase-item')
        target = pywikibot.ItemPage(testsite, 'Q271')
        claim.setTarget(target)
        item.addClaim(claim)

        item.get(force=True)

        qual_1 = pywikibot.page.Claim(testsite, 'P88', is_qualifier=True)
        qual_1.setTarget(pywikibot.WbTime(year=2012))
        item.claims['P115'][0].addQualifier(qual_1)

        qual_2 = pywikibot.page.Claim(testsite, 'P580', is_qualifier=True)
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
        qual_3 = claim.qualifiers['P580'][0]
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
        qual_3 = claim.qualifiers['P580'][0]
        qual_4 = claim.qualifiers['P88'][0]
        claim.removeQualifiers([qual_3, qual_4])

        # Check P580 and P88 qualifiers are removed
        item = pywikibot.ItemPage(testsite, 'Q68')
        item.get(force=True)
        claim = item.claims['P115'][0]
        self.assertNotIn('P580', claim.qualifiers.keys())
        self.assertNotIn('P88', claim.qualifiers.keys())


class TestWikibaseDataSiteWbsetActions(WikibaseTestCase):

    """Run general wikibase write tests."""

    family = 'wikidata'
    code = 'test'

    login = True
    write = True

    def setUp(self):
        """Setup tests."""
        self.testsite = self.get_repo()
        self.item = pywikibot.ItemPage(self.testsite, 'Q68')
        badge = pywikibot.ItemPage(self.testsite, 'Q608')
        self.sitelink = pywikibot.page.SiteLink('Test page',
                                                site='enwikisource',
                                                badges=[badge])
        super().setUp()

    def tearDown(self):
        """Tear down tests."""
        self.item = None
        self.sitelink = None
        super().tearDown()

    def test_wbsetlabel_set_from_id(self):
        """Test setting an Italian label using id."""
        self.assertEqual(self.item.getID(), 'Q68')
        self.testsite.wbsetlabel('Q68', {'language': 'it', 'value': 'Test123'})
        self.item.get(force=True)
        self.assertEqual(self.item.labels['it'], 'Test123')

    def test_wbsetlabel_remove_from_item(self):
        """Test removing an Italian label using item."""
        self.assertEqual(self.item.getID(), 'Q68')
        self.testsite.wbsetlabel(self.item, {'language': 'it', 'value': ''})
        # Check 'it' label is removed
        self.item.get(force=True)
        self.assertNotIn('it', self.item.labels.keys())

    def test_wbsetsitelink_set_remove(self):
        """Test setting a sitelink using id."""
        self.assertEqual(self.item.getID(), 'Q68')
        # add sitelink
        self.testsite.wbsetsitelink(
            'Q68',
            {'linksite': 'enwikisource',
             'linktitle': 'Test page',
             'badges': 'Q608'
             })
        self.item.get(force=True)
        self.assertEqual(self.item.sitelinks['enwikisource'], self.sitelink)
        # remove sitelink
        self.testsite.wbsetsitelink(self.item, {'linksite': 'enwikisource'})
        self.item.get(force=True)
        self.assertIsNone(self.item.sitelinks.get('enwikisource'))


class TestWikibaseAddClaimToExisting(WikibaseTestCase):

    """Run wikibase write tests for claims."""

    family = 'wikidata'
    code = 'test'

    login = True
    write = True

    @staticmethod
    def _clean_item_temp(repo, prop: str):
        """
        Return an item without any existing claims of the given property.

        :param repo: repository to fetch item from
        :type repo: pywikibot.site.DataSite
        :param prop: P-value of the property to scrub
        :return: scrubbed item
        :rtype: pywikibot.ItemPage
        """
        item = pywikibot.ItemPage(repo, 'Q68')
        item.get()
        if prop in item.claims:
            item.removeClaims(item.claims[prop])
        item.get(force=True)
        return item

    def test_multiple_changes(self):
        """Make multiple changes with EditEntity."""
        testsite = self.get_repo()
        prop = 'P95931'
        item = self._clean_item_temp(testsite, prop)

        # set initial claim
        claim0 = pywikibot.page.Claim(testsite, prop)
        target0 = 'treccid0'
        claim0.setTarget(target0)
        item.claims[prop] = [claim0]
        item.editEntity(summary='Set initial claim')

        # confirm initial claim
        item.get(force=True)
        claim1 = item.claims[prop][0]
        self.assertEqual(claim1.getTarget(), target0)

        # set second claim
        claim1 = pywikibot.page.Claim(testsite, prop)
        target1 = 'treccid1'
        claim1.setTarget(target1)
        item.claims[prop].append(claim1)
        item.editEntity(summary='Set second claim')

        # confirm two claims
        item.get(force=True)
        claim0 = item.claims[prop][0]
        self.assertEqual(claim0.getTarget(), target0)
        claim1 = item.claims[prop][1]
        self.assertEqual(claim1.getTarget(), target1)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
