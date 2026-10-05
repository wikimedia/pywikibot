#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for scripts/review.py."""
from __future__ import annotations

import unittest
from contextlib import suppress
from unittest.mock import MagicMock, PropertyMock, patch

import pywikibot
from pywikibot.exceptions import (
    APIError,
    UnknownExtensionError,
    UserRightsError,
)
from scripts.review import (
    ReviewBot,
    main,
    pending_pages_generator,
    unreviewed_pages_generator,
)
from tests.aspects import PatchingTestCase


class TestReviewBot(PatchingTestCase):

    """Test the ReviewBot class and operations."""

    family = 'wikipedia'
    code = 'test'
    dry = True

    def setUp(self) -> None:
        """Create test fixtures."""
        super().setUp()
        self.patch(self.site, 'has_extension',
                   lambda ext: ext == 'FlaggedRevs')
        self.page = pywikibot.Page(self.site, 'TestPage')
        self.page.exists = MagicMock(return_value=True)

    def test_setup_flaggedrevs_disabled(self) -> None:
        """Test setup() raises UnknownExtensionError if FlaggedRevs missing."""
        self.patch(self.site, 'has_extension', lambda *_: False)
        bot = ReviewBot(site=self.site, generator=[self.page])
        with self.assertRaisesRegex(UnknownExtensionError, 'not enabled'):
            bot.setup()

    def test_invalid_revid_option(self) -> None:
        """Test that invalid -revid option raises ValueError."""
        with self.assertRaisesRegex(ValueError, 'Invalid -revid option'):
            ReviewBot(site=self.site, revid='not_an_int')

    def test_invalid_flag_option(self) -> None:
        """Test that invalid -flag option raises ValueError."""
        with self.assertRaisesRegex(ValueError, 'Invalid -flag option'):
            ReviewBot(site=self.site, flag='not_an_int')

    def test_review_default(self) -> None:
        """Test review operation with default latest revision."""
        with patch.object(pywikibot.Page, 'latest_revision_id',
                          new_callable=PropertyMock(return_value=999)), \
             patch.object(self.page, 'review') as mock_review:
            bot = ReviewBot(site=self.site, always=True)
            bot.current_page = self.page
            bot.treat_page()
            mock_review.assert_called_once_with(
                summary=None,
                revid=999,
                flag=None,
                refresh=False,
            )
            self.assertEqual(bot.counter['reviewed'], 1)

    def test_unreview_default(self) -> None:
        """Test unreview operation with stable revision."""
        with patch.object(pywikibot.Page, 'stable_revision_id',
                          new_callable=PropertyMock(return_value=555)), \
             patch.object(self.page, 'unreview') as mock_unreview:
            bot = ReviewBot(site=self.site, unreview=True, always=True)
            bot.current_page = self.page
            bot.treat_page()
            mock_unreview.assert_called_once_with(
                summary=None,
                revid=555,
                refresh=False,
            )
            self.assertEqual(bot.counter['unreviewed'], 1)

    def test_review_with_options(self) -> None:
        """Test review operation with custom options."""
        with patch.object(self.page, 'review') as mock_review:
            bot = ReviewBot(
                site=self.site,
                always=True,
                revid=12345,
                flag=2,
                summary='Reviewed unit test',
                refresh=True,
            )
            bot.current_page = self.page
            bot.treat_page()
            mock_review.assert_called_once_with(
                summary='Reviewed unit test',
                revid=12345,
                flag=2,
                refresh=True,
            )
            self.assertEqual(bot.counter['reviewed'], 1)

    def test_unreview_with_options(self) -> None:
        """Test unreview operation with custom options."""
        with patch.object(self.page, 'unreview') as mock_unreview:
            bot = ReviewBot(
                site=self.site,
                unreview=True,
                always=True,
                revid=54321,
                summary='Unreviewed unit test',
                refresh=True,
            )
            bot.current_page = self.page
            bot.treat_page()
            mock_unreview.assert_called_once_with(
                summary='Unreviewed unit test',
                revid=54321,
                refresh=True,
            )
            self.assertEqual(bot.counter['unreviewed'], 1)

    def test_unreview_no_stable_revision(self) -> None:
        """Test unreview skips page when no stable revision exists."""
        with patch.object(pywikibot.Page, 'stable_revision_id',
                          new_callable=PropertyMock(return_value=None)), \
             patch.object(self.page, 'unreview') as mock_unreview:
            bot = ReviewBot(site=self.site, unreview=True, always=True)
            bot.current_page = self.page
            bot.treat_page()
            mock_unreview.assert_not_called()
            self.assertEqual(bot.counter['unreviewed'], 0)

    def test_review_no_revisions(self) -> None:
        """Test review skips page when latest_revision_id is None."""
        with patch.object(pywikibot.Page, 'latest_revision_id',
                          new_callable=PropertyMock(return_value=None)), \
             patch.object(self.page, 'review') as mock_review, \
             patch('pywikibot.info') as mock_info:
            bot = ReviewBot(site=self.site, always=True)
            bot.current_page = self.page
            bot.treat_page()
            mock_review.assert_not_called()
            self.assertEqual(bot.counter['reviewed'], 0)
            mock_info.assert_called_once()
            self.assertIn('has no revisions to review',
                          mock_info.call_args[0][0])

    def test_review_refresh_clears_stale_cache(self) -> None:
        """Test -refresh invalidates cached revision ID before prompt/log."""
        self.page._revid = 100

        def fake_loadrevisions(page, **kwargs):
            page._revid = 200

        self.site.loadrevisions = MagicMock(side_effect=fake_loadrevisions)

        with patch.object(self.page, 'review') as mock_review, \
             patch('pywikibot.info') as mock_info:
            bot = ReviewBot(site=self.site, refresh=True, always=True)
            bot.current_page = self.page
            bot.treat_page()

            mock_review.assert_called_once_with(
                summary=None,
                revid=200,
                flag=None,
                refresh=True,
            )
            self.assertEqual(bot.counter['reviewed'], 1)
            mock_info.assert_called_with(
                f'Reviewed {self.page.title(as_link=True)} (revid 200)')

    def test_review_no_refresh_retains_cached_revision(self) -> None:
        """Test that without -refresh, cached revision ID is retained."""
        self.page._revid = 100
        self.site.loadrevisions = MagicMock()

        with patch.object(self.page, 'review') as mock_review, \
             patch('pywikibot.info') as mock_info:
            bot = ReviewBot(site=self.site, refresh=False, always=True)
            bot.current_page = self.page
            bot.treat_page()

            self.site.loadrevisions.assert_not_called()
            mock_review.assert_called_once_with(
                summary=None,
                revid=100,
                flag=None,
                refresh=False,
            )
            self.assertEqual(bot.counter['reviewed'], 1)
            mock_info.assert_called_with(
                f'Reviewed {self.page.title(as_link=True)} (revid 100)')

    def test_unreview_refresh_clears_stale_cache(self) -> None:
        """Test -refresh invalidates cached stable revision ID for unreview."""
        self.page._stable_revision_id = 111

        def fake_stable_revid(page):
            return 222

        self.site.stable_revid = MagicMock(side_effect=fake_stable_revid)

        with patch.object(self.page, 'unreview') as mock_unreview, \
             patch('pywikibot.info') as mock_info:
            bot = ReviewBot(site=self.site, unreview=True, refresh=True,
                            always=True)
            bot.current_page = self.page
            bot.treat_page()

            mock_unreview.assert_called_once_with(
                summary=None,
                revid=222,
                refresh=True,
            )
            self.assertEqual(bot.counter['unreviewed'], 1)
            mock_info.assert_called_with(
                f'Unreviewed {self.page.title(as_link=True)} (revid 222)')

    def test_unreview_no_refresh_retains_cached_revision(self) -> None:
        """Test that without -refresh, cached stable revision is retained."""
        self.page._stable_revision_id = 111
        self.site.stable_revid = MagicMock()

        with patch.object(self.page, 'unreview') as mock_unreview, \
             patch('pywikibot.info') as mock_info:
            bot = ReviewBot(site=self.site, unreview=True, refresh=False,
                            always=True)
            bot.current_page = self.page
            bot.treat_page()

            self.site.stable_revid.assert_not_called()
            mock_unreview.assert_called_once_with(
                summary=None,
                revid=111,
                refresh=False,
            )
            self.assertEqual(bot.counter['unreviewed'], 1)
            mock_info.assert_called_with(
                f'Unreviewed {self.page.title(as_link=True)} (revid 111)')

    def test_nonexistent_page_skipped(self) -> None:
        """Test that nonexistent pages are skipped."""
        self.page.exists.return_value = False
        with patch.object(self.page, 'review') as mock_review:
            bot = ReviewBot(site=self.site, always=True)
            bot.current_page = self.page
            bot.treat_page()
            mock_review.assert_not_called()
            self.assertEqual(bot.counter['reviewed'], 0)

    def test_confirmation_declined(self) -> None:
        """Test declining confirmation prompt skips the page."""
        with patch.object(pywikibot.Page, 'latest_revision_id',
                          new_callable=PropertyMock(return_value=999)), \
             patch.object(self.page, 'review') as mock_review, \
             patch('pywikibot.input_choice', return_value='n'):
            bot = ReviewBot(site=self.site, always=False)
            bot.current_page = self.page
            bot.treat_page()
            mock_review.assert_not_called()
            self.assertEqual(bot.counter['reviewed'], 0)

    def test_confirmation_accepted(self) -> None:
        """Test accepting confirmation prompt performs the action."""
        with patch.object(pywikibot.Page, 'latest_revision_id',
                          new_callable=PropertyMock(return_value=999)), \
             patch.object(self.page, 'review') as mock_review, \
             patch('pywikibot.input_choice', return_value='y'):
            bot = ReviewBot(site=self.site, always=False)
            bot.current_page = self.page
            bot.treat_page()
            mock_review.assert_called_once_with(
                summary=None,
                revid=999,
                flag=None,
                refresh=False,
            )
            self.assertEqual(bot.counter['reviewed'], 1)

    def test_error_handling(self) -> None:
        """Test that APIError and UserRightsError are handled gracefully."""
        with patch.object(pywikibot.Page, 'latest_revision_id',
                          new_callable=PropertyMock(return_value=999)), \
             patch.object(self.page, 'review',
                          side_effect=APIError('err', 'msg')), \
             patch('pywikibot.error') as mock_error:
            bot = ReviewBot(site=self.site, always=True)
            bot.current_page = self.page
            bot.treat_page()
            mock_error.assert_called_once()
            self.assertEqual(bot.counter['reviewed'], 0)

        rights_err = UserRightsError('Insufficient rights')
        with patch.object(pywikibot.Page, 'latest_revision_id',
                          new_callable=PropertyMock(return_value=999)), \
             patch.object(self.page, 'review', side_effect=rights_err), \
             patch('pywikibot.error') as mock_error:
            bot = ReviewBot(site=self.site, always=True)
            bot.current_page = self.page
            bot.treat_page()
            mock_error.assert_called_once()
            self.assertEqual(bot.counter['reviewed'], 0)


class TestReviewGenerators(PatchingTestCase):

    """Test FlaggedRevs generators."""

    family = 'wikipedia'
    code = 'test'
    dry = True

    def test_pending_pages_generator_querypage(self) -> None:
        """Test pending_pages_generator using querypage."""
        with patch.object(self.site, 'querypage', return_value=[]) as mock_qp:
            res = pending_pages_generator(self.site, total=10)
            self.assertEqual(res, [])
            mock_qp.assert_called_once_with('Pendingchanges', total=10)

    def test_pending_pages_generator_api_fallback(self) -> None:
        """Test pending_pages_generator falling back to PageGenerator."""
        with patch.object(self.site, 'querypage',
                          side_effect=ValueError('unsupported')) as mock_qp, \
             patch('scripts.review.api.PageGenerator') as mock_gen:
            pending_pages_generator(self.site, total=5)
            self.assertEqual(mock_qp.call_count, 3)
            mock_gen.assert_called_once_with(
                'oldreviewedpages', site=self.site, total=5)

    def test_pending_pages_generator_unrelated_error(self) -> None:
        """Test that pending_pages_generator does not suppress APIError."""
        with patch.object(self.site, 'querypage',
                          side_effect=APIError('unknown_error', 'err')):
            with self.assertRaises(APIError):
                pending_pages_generator(self.site)

    def test_unreviewed_pages_generator_querypage(self) -> None:
        """Test unreviewed_pages_generator using querypage."""
        with patch.object(self.site, 'querypage', return_value=[]) as mock_qp:
            res = unreviewed_pages_generator(self.site, total=10)
            self.assertEqual(res, [])
            mock_qp.assert_called_once_with('Unreviewedpages', total=10)

    def test_unreviewed_pages_generator_api_fallback(self) -> None:
        """Test unreviewed_pages_generator falling back to PageGenerator."""
        with patch.object(self.site, 'querypage',
                          side_effect=ValueError('unsupported')) as mock_qp, \
             patch('scripts.review.api.PageGenerator') as mock_gen:
            unreviewed_pages_generator(self.site, total=5)
            self.assertEqual(mock_qp.call_count, 2)
            mock_gen.assert_called_once_with(
                'unreviewedpages', site=self.site, total=5)

    def test_unreviewed_pages_generator_unrelated_error(self) -> None:
        """Test that unreviewed_pages_generator does not suppress APIError."""
        with patch.object(self.site, 'querypage',
                          side_effect=APIError('unknown_error', 'err')):
            with self.assertRaises(APIError):
                unreviewed_pages_generator(self.site)


class TestReviewMain(PatchingTestCase):

    """Test main() CLI handling."""

    family = 'wikipedia'
    code = 'test'
    dry = True

    def setUp(self) -> None:
        """Create test fixtures."""
        super().setUp()
        self.patch(self.site, 'has_extension',
                   lambda ext: ext == 'FlaggedRevs')
        self.patch(pywikibot, 'Site', lambda *args, **kwargs: self.site)
        self.page = pywikibot.Page(self.site, 'TestPage')

    def test_main_flaggedrevs_disabled(self) -> None:
        """Test main() exits when FlaggedRevs is not enabled."""
        self.patch(self.site, 'has_extension', lambda *_: False)
        with patch('pywikibot.error') as mock_error:
            main('-page:Test')
            mock_error.assert_called_once()
            self.assertIn('not enabled', mock_error.call_args[0][0])

    def test_main_mutually_exclusive(self) -> None:
        """Test main() exits when -review and -unreview both given."""
        with patch('pywikibot.error') as mock_error:
            main('-review', '-unreview')
            mock_error.assert_called_once()
            self.assertIn('cannot be used together',
                          mock_error.call_args[0][0])

    def test_main_pending_unreviewed_mutually_exclusive(self) -> None:
        """Test main() exits when -pending and -unreviewed both given."""
        with patch('pywikibot.error') as mock_error:
            main('-pending', '-unreviewed')
            mock_error.assert_called_once()
            self.assertIn('cannot be used together',
                          mock_error.call_args[0][0])

    def test_main_pending_option(self) -> None:
        """Test main() with valid -pending option."""
        with patch('scripts.review.pending_pages_generator',
                   return_value=[self.page]) as mock_gen, \
             patch('scripts.review.ReviewBot') as mock_bot:
            main('-pending', '-always')
            mock_gen.assert_called_once_with(self.site)
            mock_bot.assert_called_once()

    def test_main_unreviewed_option(self) -> None:
        """Test main() with valid -unreviewed option."""
        with patch('scripts.review.unreviewed_pages_generator',
                   return_value=[self.page]) as mock_gen, \
             patch('scripts.review.ReviewBot') as mock_bot:
            main('-unreviewed', '-always')
            mock_gen.assert_called_once_with(self.site)
            mock_bot.assert_called_once()

    def test_main_unreview_missing_generator(self) -> None:
        """Test -unreview requires a generator."""
        with patch('scripts.review.suggest_help') as mock_suggest:
            main('-unreview')
            mock_suggest.assert_called_once_with(missing_generator=True)

    def test_main_invalid_revid(self) -> None:
        """Test main() with invalid revid."""
        with patch('pywikibot.error') as mock_error:
            main('-revid:abc')
            mock_error.assert_called_once()
            self.assertIn('Invalid revid parameter',
                          mock_error.call_args[0][0])

    def test_main_invalid_flag(self) -> None:
        """Test main() with invalid flag."""
        with patch('pywikibot.error') as mock_error:
            main('-flag:xyz')
            mock_error.assert_called_once()
            self.assertIn('Invalid flag parameter',
                          mock_error.call_args[0][0])


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
