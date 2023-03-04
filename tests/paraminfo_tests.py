#!/usr/bin/env python3
"""Test confirming paraminfo contains expected values."""
#
# (C) Pywikibot team, 2015-2023
#
# Distributed under the terms of the MIT license.
#
from pywikibot.family import WikimediaFamily
from pywikibot.page import Claim, Property
from pywikibot.site import DataSite
from tests.aspects import (
    DefaultSiteTestCase,
    DefaultWikibaseClientTestCase,
    TestCaseBase,
    WikimediaDefaultSiteTestCase,
    unittest,
)
from tests.utils import skipping


class KnownTypesTestBase(TestCaseBase):

    """Base class for paraminfo checks."""

    def _get_param_values(self, site, module, parameter):
        """Perform check that a parameter matches the expected list."""
        with skipping(
            ValueError,
                msg=f'Paraminfo for {module} could not be loaded'):
            param = site._paraminfo.parameter(module, parameter)

        if not param or 'type' not in param:
            raise unittest.SkipTest(
                f'No defined values for {module}.{parameter}')
        return param['type']

    def _check_param_values(self, site, module, parameter, expected):
        """Check that a parameter matches the expected list exactly."""
        values = self._get_param_values(site, module, parameter)
        self.assertCountEqual(expected, values)

    def _check_param_subset(self, site, module, parameter, expected):
        """Check that a parameter contains all entries in expected list."""
        values = self._get_param_values(site, module, parameter)
        self.assertLessEqual(set(expected), set(values))

    def _check_param_superset(self, site, module, parameter, expected):
        """Check that a parameter only contains entries in expected list."""
        values = self._get_param_values(site, module, parameter)
        exp = set(expected)
        val = set(values)
        if not exp.issuperset(val):
            diff = val - exp
            self.fail('Unexpected param{} {} in values'
                      .format('s' if len(diff) > 1 else '', diff))


class MediaWikiKnownTypesTestCase(KnownTypesTestBase,
                                  DefaultSiteTestCase):

    """Verify MediaWiki types using paraminfo."""

    def test_api_format(self):
        """Test api format."""
        known = ['json', 'xml']
        self._check_param_subset(self.site, 'main', 'format', known)

    def test_assert_user(self):
        """Test assert type."""
        known = ['user', 'bot']
        self._check_param_subset(self.site, 'main', 'assert', known)

    def test_feed_format(self):
        """Test feed format."""
        known = ['rss', 'atom']

        if self.site.has_extension('GoogleNewsSitemap'):
            known.append('sitemap')

        self._check_param_values(
            self.site, 'feedwatchlist', 'feedformat', known)

    def test_watchlist_show_flags(self):
        """Test watchlist show flags."""
        types = ['minor', 'bot', 'anon', 'patrolled']
        if self.site.mw_version >= '1.24':
            types.append('unread')

        known = types + [f'!{item}' for item in types]

        self._check_param_subset(self.site, 'query+watchlist', 'show', known)

    def test_watchlist_type(self):
        """Test watchlist type."""
        known = ['edit', 'external', 'new', 'log']

        mw_ver = self.site.mw_version

        if mw_ver.version >= (1, 27) \
           and (mw_ver >= '1.27.0-wmf.4' or mw_ver.suffix == 'alpha'):
            known.append('categorize')

        self._check_param_values(self.site, 'query+watchlist', 'type', known)

    def test_watchlist_modification_flag(self):
        """Test watchlist modification flag."""
        known = ['watch', 'unwatch', 'preferences', 'nochange']

        self._check_param_values(self.site, 'edit', 'watchlist', known)
        self._check_param_values(self.site, 'delete', 'watchlist', known)
        self._check_param_values(self.site, 'move', 'watchlist', known)
        self._check_param_values(self.site, 'protect', 'watchlist', known)
        self._check_param_values(self.site, 'rollback', 'watchlist', known)
        self._check_param_values(self.site, 'undelete', 'watchlist', known)

        known = ['watch', 'preferences', 'nochange']
        self._check_param_values(self.site, 'upload', 'watchlist', known)

    def test_content_format(self):
        """Test content format."""
        base = [
            'application/json',
            'text/x-wiki',
            'text/javascript',
            'text/css',
            'text/plain',
        ]
        if self.site.mw_version >= '1.36.0-wmf.2':
            base.extend([
                'application/octet-stream',
                'application/unknown',
                'application/x-binary',
                'text/unknown',
                'unknown/unknown',
            ])
        if isinstance(self.site, DataSite):
            # It is not clear when this format has been added, see T129281.
            base.append('application/vnd.php.serialized')
        extensions = {e['name'] for e in self.site.siteinfo['extensions']}
        if 'CollaborationKit' in extensions:
            base.append('text/x-collabkit')

        for module in ('edit', 'parse'):
            args = self.site, module, 'contentformat', base
            with self.subTest(module=module):
                self._check_param_values(*args)

    def test_content_model(self):
        """Test content model."""
        base = [
            'wikitext',
            'javascript',
            'css',
            'text',
        ]
        wmf = [
            'MassMessageListContent',
            'SecurePoll',
            'Scribunto',
            'JsonSchema',
        ]
        if self.site.mw_version >= '1.24':
            base.append('json')

        self._check_param_subset(self.site, 'edit', 'contentmodel', base)
        self._check_param_subset(self.site, 'parse', 'contentmodel', base)

        if isinstance(self.site.family, WikimediaFamily):
            self._check_param_subset(self.site, 'parse', 'contentmodel', wmf)

    def test_revision_deletion_type(self):
        """Test revision deletion type."""
        known = ['revision', 'archive', 'oldimage', 'filearchive', 'logging']

        self._check_param_values(self.site, 'revisiondelete', 'type', known)

    def test_revision_deletion_what(self):
        """Test revision deletion part."""
        known = ['content', 'comment', 'user']

        self._check_param_values(self.site, 'revisiondelete', 'hide', known)

    def test_revision_deletion_level(self):
        """Test revision deletion level."""
        known = ['yes', 'no', 'nochange']

        self._check_param_values(
            self.site, 'revisiondelete', 'suppress', known)


class SiteMatrixKnownTypesTestCase(KnownTypesTestBase,
                                   WikimediaDefaultSiteTestCase):

    """Verify Echo types using paraminfo."""

    def test_site_matrix_type(self):
        """Test site matrix type."""
        known = ['special', 'language']

        self._check_param_values(self.site, 'sitematrix', 'type', known)

    def test_site_matrix_state(self):
        """Test site matrix state."""
        known = ['closed', 'private', 'fishbowl', 'all', 'nonglobal']

        self._check_param_values(self.site, 'sitematrix', 'state', known)


class EchoKnownTypesTestCase(KnownTypesTestBase,
                             WikimediaDefaultSiteTestCase):

    """Verify Echo types using paraminfo."""

    def test_echo_types(self):
        """Test Echo notification types."""
        known = ['alert', 'message']

        self._check_param_values(self.site, 'echomarkread', 'sections', known)

        known = ['alert', 'message', 'all']

        self._check_param_values(self.site, 'echomarkseen', 'type', known)


class WikibaseKnownTypesTests(KnownTypesTestBase,
                              DefaultWikibaseClientTestCase):

    """Verify Wikibase types using paraminfo."""

    def test_entities(self):
        """Test known entities."""
        unsupported = {'form', 'lexeme', 'sense'}  # T195435
        supported = {'item', 'property'}
        known = supported | unsupported
        self._check_param_superset(
            self.repo, 'wbsearchentities', 'type', known)

    # Missing datatypes won't crash pywikibot but should be noted
    def test_datatypes(self):
        """Test that all encountered datatypes are known."""
        unsupported = {
            'wikibase-form', 'wikibase-lexeme', 'wikibase-sense',  # T194890
            'musical-notation',  # T218506
            'entity-schema',  # T245949
        }
        known = set(Property.types) | unsupported
        self._check_param_superset(
            self.repo, 'wbformatvalue', 'datatype', known)

    def test_snaktype(self):
        """Test known snak types."""
        known = Claim.SNAK_TYPES
        self._check_param_values(self.repo, 'wbcreateclaim', 'snaktype', known)

    def test_rank(self):
        """Test known ranks."""
        known = ['deprecated', 'normal', 'preferred']
        self._check_param_values(self.repo, 'wbgetclaims', 'rank', known)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
