# -*- coding: utf-8  -*-
"""Tests for editing Wikibase items."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import time
import pywikibot

from tests.aspects import unittest, WikibaseTestCase


class TestWikibaseWriteGeneral(WikibaseTestCase):

    """Run general wikibase write tests."""

    family = 'wikidata'
    code = 'test'

    user = True
    write = True

    def test_label_set(self):
        testsite = self.get_repo()
        item = pywikibot.ItemPage(testsite, 'Q68')
        self.assertIsInstance(item, pywikibot.ItemPage)
        self.assertEqual(item.getID(), 'Q68')
        item.editLabels({'en': 'Test123'})
        item.get(force=True)
        self.assertEqual(item.labels['en'], 'Test123')

    def test_label_remove(self):
        testsite = self.get_repo()
        item = pywikibot.ItemPage(testsite, 'Q68')
        # These two should be additive
        item.editLabels({'en': 'Test123'})
        item.editLabels({'fa': 'Test123'})
        item.get(force=True)
        self.assertTrue('en' in item.labels.keys())
        self.assertTrue('fa' in item.labels.keys())

        # This should remove the 'fa' label
        item.editLabels({'en': 'Test123', 'fa': ''})

        # Check 'fa' label is removed
        item = pywikibot.ItemPage(testsite, 'Q68')
        item.get()
        self.assertFalse('fa' in item.labels.keys())

    def test_alias_set(self):
        testsite = self.get_repo()
        ts = str(time.time())
        item = pywikibot.ItemPage(testsite, 'Q68')
        item.editAliases({'en': [ts]})

    def test_add_claim_with_qualifier(self):
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

    def test_edit_entity_new_item(self):
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


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
