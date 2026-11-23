#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for scripts/review.py."""
from __future__ import annotations

import unittest
from contextlib import ExitStack, suppress
from datetime import timedelta
from unittest.mock import MagicMock, PropertyMock, patch

import pywikibot
from pywikibot.exceptions import (
    APIError,
    ApiNotAvailableError,
    ApiTimeoutError,
    InvalidTitleError,
    ServerError,
    UnknownExtensionError,
    UserRightsError,
)
from pywikibot.time import Timestamp
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


class TestReviewBotAuto(PatchingTestCase):

    """Test automated revision review by trusted users in ReviewBot."""

    family = 'wikipedia'
    code = 'test'
    dry = True

    def setUp(self) -> None:
        """Create test fixtures."""
        super().setUp()
        self.patch(self.site, 'has_extension',
                   lambda ext: ext == 'FlaggedRevs')
        self.patch(pywikibot, 'Site', lambda *args, **kwargs: self.site)
        self.patch(pywikibot.Page, 'get_revision',
                   lambda p, oldid, **kwargs: self._make_rev(
                       oldid, 'OldEditor'))
        self.page = pywikibot.Page(self.site, 'AutoTestPage')
        self.page.exists = MagicMock(return_value=True)

    @staticmethod
    def _make_rev(revid: int, user: str | None,
                  timestamp: Timestamp | None = None) -> MagicMock:
        """Create a mock Revision."""
        rev = MagicMock()
        rev.revid = revid
        rev.user = user
        if timestamp is not None:
            rev.timestamp = timestamp
        else:
            rev.timestamp = Timestamp(2026, 1, 1, 0, 0, 0) + timedelta(
                seconds=revid)
        return rev

    def _mock_user_rights(self, trusted_users_rights: dict[str, list[str]]):
        """Mock pywikibot.User to return configured rights."""
        def fake_user(site, username):
            user = MagicMock()
            user.username = username
            user.isAnonymous = MagicMock(return_value=False)
            rights = trusted_users_rights.get(username, [])
            user.rights = MagicMock(return_value=rights)
            return user

        return patch('pywikibot.User', side_effect=fake_user)

    def _run_auto(
        self,
        revs=None,
        *,
        stable_revid: int | None = 100,
        latest_revid: int | None = 102,
        stable_exc: Exception | None = None,
        latest_exc: Exception | None = None,
        user_rights: dict[str, list[str]] | None = None,
        **bot_kwargs,
    ) -> tuple[ReviewBot, MagicMock]:
        """Run ReviewBot -auto treat_page() with common revision patches."""
        if revs is not None:
            self.page.revisions = MagicMock(return_value=revs)

        def _patch_prop(attr: str, value: int | None, exc: Exception | None):
            if exc is not None:
                return patch.object(
                    pywikibot.Page, attr,
                    new=property(lambda p: (_ for _ in ()).throw(exc)))
            return patch.object(
                pywikibot.Page, attr,
                new_callable=PropertyMock(return_value=value))

        with ExitStack() as stack:
            stack.enter_context(
                _patch_prop('stable_revision_id', stable_revid, stable_exc))
            stack.enter_context(
                _patch_prop('latest_revision_id', latest_revid, latest_exc))
            mock_review = stack.enter_context(
                patch.object(self.page, 'review'))
            if user_rights is not None:
                stack.enter_context(self._mock_user_rights(user_rights))

            bot = ReviewBot(site=self.site, auto=True, always=True,
                            **bot_kwargs)
            bot.current_page = self.page
            bot.treat_page()
            return bot, mock_review

    def _assert_reviewed(
        self,
        bot: ReviewBot,
        mock_review: MagicMock,
        revid: int | None,
    ) -> None:
        """Assert whether a revision was reviewed and counted."""
        if revid is None:
            mock_review.assert_not_called()
            self.assertEqual(bot.counter['reviewed'], 0)
        else:
            mock_review.assert_called_once_with(
                summary=None,
                revid=revid,
                flag=None,
                refresh=False,
            )
            self.assertEqual(bot.counter['reviewed'], 1)

    def test_auto_mutually_exclusive_options(self) -> None:
        """Test -auto cannot be combined with -unreview or -revid."""
        for kwargs in ({'unreview': True}, {'revid': 123}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(
                    ValueError, 'cannot be used together'):
                ReviewBot(site=self.site, auto=True, **kwargs)

    def test_auto_revision_selection_sequences(self) -> None:
        """Test trusted/untrusted revision sequences select eligible edit."""
        cases = [
            (
                'trusted_followed_by_untrusted',
                [
                    (103, 'Noob'),
                    (102, 'Trusted2'),
                    (101, 'Trusted1'),
                    (100, 'OldEditor'),
                ],
                103,
                {'Trusted1': ['autoreview'], 'Trusted2': ['autoreview'],
                 'Noob': []},
                102,
                (103,),
                False,
            ),
            (
                'all_trusted',
                [
                    (103, 'Trusted3'),
                    (102, 'Trusted2'),
                    (101, 'Trusted1'),
                    (100, 'OldEditor'),
                ],
                103,
                {'Trusted1': ['autoreview'], 'Trusted2': ['autoreview'],
                 'Trusted3': ['autoreview']},
                103,
                (),
                False,
            ),
            (
                'first_outstanding_untrusted',
                [
                    (102, 'TrustedUser'),
                    (101, 'Noob'),
                    (100, 'OldEditor'),
                ],
                102,
                {'TrustedUser': ['autoreview'], 'Noob': []},
                None,
                (101, 102),
                False,
            ),
            (
                'interleaved_untrusted_never_reviewed',
                [
                    (104, 'Noob2'),
                    (103, 'Trusted1'),
                    (102, 'Noob1'),
                    (101, 'Trusted0'),
                    (100, 'OldEditor'),
                ],
                104,
                {'Trusted0': ['autoreview'], 'Trusted1': ['autoreview'],
                 'Noob1': [], 'Noob2': []},
                101,
                (102, 104),
                True,
            ),
        ]
        for case in cases:
            name, spec, latest, rights, expected, untrusted, check_log = case
            with self.subTest(case=name), patch('pywikibot.info') as mock_info:
                revs = [self._make_rev(rid, user) for rid, user in spec]
                bot, mock_review = self._run_auto(
                    iter(revs), latest_revid=latest, user_rights=rights)
                self._assert_reviewed(bot, mock_review, expected)
                for call_args in mock_review.call_args_list:
                    self.assertNotIn(
                        call_args.kwargs.get('revid'), untrusted)
                if check_log:
                    self.assertTrue(
                        any('Untrusted edit encountered on' in str(call)
                            and '102' in str(call)
                            for call in mock_info.call_args_list))

    def test_auto_trusted_via_autoreview_right(self) -> None:
        """Test trusted user discovered via autoreview right and cache."""
        revs = [
            self._make_rev(101, 'AutoReviewUser'),
            self._make_rev(100, 'OldEditor'),
        ]
        mock_user_instance = MagicMock()
        mock_user_instance.isAnonymous = MagicMock(return_value=False)
        mock_user_instance.rights = MagicMock(return_value=['autoreview'])

        with patch('pywikibot.User',
                   return_value=mock_user_instance) as mock_user_cls:
            bot, mock_review = self._run_auto(iter(revs), latest_revid=101)

            self._assert_reviewed(bot, mock_review, 101)
            mock_user_cls.assert_called_once_with(
                self.site, 'AutoReviewUser')

            # Querying again should use cache and not instantiate User
            self.assertTrue(bot.is_trusted_user('AutoReviewUser'))
            self.assertEqual(mock_user_cls.call_count, 1)

    def test_auto_explicitly_configured_trusted_username(self) -> None:
        """Test an explicitly configured trusted username without API query."""
        revs = [
            self._make_rev(101, 'CustomBot'),
            self._make_rev(100, 'OldEditor'),
        ]
        with patch('pywikibot.User') as mock_user_cls:
            bot, mock_review = self._run_auto(
                iter(revs), latest_revid=101, trusted=['CustomBot'])

            mock_user_cls.assert_not_called()
            self._assert_reviewed(bot, mock_review, 101)

    def test_auto_no_eligible_revisions_after_stable(self) -> None:
        """Test page skipped when no revisions exist after stable revision."""
        with patch('pywikibot.info') as mock_info:
            bot, mock_review = self._run_auto(latest_revid=100)

            self._assert_reviewed(bot, mock_review, None)
            mock_info.assert_called_with(
                f'Page {self.page.title(as_link=True)} has no unreviewed '
                'revisions (latest revision 100 is already stable), skipping.')

    def test_auto_multiple_pages_processed(self) -> None:
        """Test generator processing multiple pages with cached user rights."""
        pages = []
        rev_specs = [
            ('Page1', [(102, 'CommonBot'), (101, 'CommonBot'),
                       (100, 'OldEditor')]),
            ('Page2', [(201, 'Noob'), (200, 'OldEditor')]),
            ('Page3', [(302, 'CommonBot'), (301, 'CommonBot'),
                       (300, 'OldEditor')]),
        ]
        for title, spec in rev_specs:
            page = pywikibot.Page(self.site, title)
            page.exists = MagicMock(return_value=True)
            page.revisions = MagicMock(return_value=iter(
                [self._make_rev(rid, user) for rid, user in spec]))
            pages.append(page)

        stable_map = {'Page1': 100, 'Page2': 200, 'Page3': 300}
        latest_map = {'Page1': 102, 'Page2': 201, 'Page3': 302}

        with (
            patch.object(
                pywikibot.Page, 'stable_revision_id',
                new=property(lambda p: stable_map[p.title()])),
            patch.object(
                pywikibot.Page, 'latest_revision_id',
                new=property(lambda p: latest_map[p.title()])),
            patch.object(pages[0], 'review') as mock_rev1,
            patch.object(pages[1], 'review') as mock_rev2,
            patch.object(pages[2], 'review') as mock_rev3,
            self._mock_user_rights({'CommonBot': ['autoreview'], 'Noob': []}),
        ):
            bot = ReviewBot(site=self.site, generator=pages,
                            auto=True, always=True)
            bot.run()

            mock_rev1.assert_called_once_with(
                summary=None, revid=102, flag=None, refresh=False)
            mock_rev2.assert_not_called()
            mock_rev3.assert_called_once_with(
                summary=None, revid=302, flag=None, refresh=False)
            self.assertEqual(bot.counter['reviewed'], 2)

    def test_auto_stable_revid_not_found_in_history(self) -> None:
        """Test warning when stable_revision_id is not found in history."""
        revs = [self._make_rev(102, 'User1'), self._make_rev(101, 'User2')]
        mock_get_rev = MagicMock(return_value=self._make_rev(100, 'OldEditor'))
        self.page.get_revision = mock_get_rev

        with patch('pywikibot.warning') as mock_warning:
            bot, mock_review = self._run_auto(iter(revs))

            mock_get_rev.assert_called_once_with(100, content=False)
            self._assert_reviewed(bot, mock_review, None)
            mock_warning.assert_called_once()
            self.assertIn('not found in history', mock_warning.call_args[0][0])

    def test_auto_missing_or_hidden_user(self) -> None:
        """Test revision with missing or hidden user stops inspection."""
        revs = [
            self._make_rev(102, 'TrustedUser'),
            self._make_rev(101, None),
            self._make_rev(100, 'OldEditor'),
        ]
        with patch('pywikibot.info') as mock_info:
            bot, mock_review = self._run_auto(iter(revs))

            self._assert_reviewed(bot, mock_review, None)
            self.assertTrue(any('missing or hidden user' in str(call)
                                for call in mock_info.call_args_list))

    def test_auto_revision_metadata_errors(self) -> None:
        """Test metadata API errors reading stable or latest revid."""
        cases = [
            ('stable_revision_id',
             {'stable_exc': ApiTimeoutError('Timeout fetching stable revid')}),
            ('latest_revision_id',
             {'latest_exc': ApiNotAvailableError(
                 'API endpoint unavailable')}),
        ]
        for label, exc_kwargs in cases:
            with self.subTest(attr=label), \
                 patch('pywikibot.error') as mock_error:
                bot, mock_review = self._run_auto(**exc_kwargs)
                self._assert_reviewed(bot, mock_review, None)
                mock_error.assert_called_once()
                self.assertIn('Failed to load revision metadata',
                              mock_error.call_args[0][0])

    def test_auto_revisions_load_errors(self) -> None:
        """Test API and network errors loading or iterating revisions."""
        def iter_timeout():
            yield self._make_rev(102, 'TrustedUser')
            raise ApiTimeoutError('Timeout reading revision history')

        cases = [
            ('APIError',
             lambda: MagicMock(
                 side_effect=APIError('internal_api_error', 'History error'))),
            ('ApiNotAvailableError',
             lambda: MagicMock(
                 side_effect=ApiNotAvailableError(
                     'History endpoint unavailable'))),
            ('ServerError',
             lambda: MagicMock(side_effect=ServerError('Server error 500'))),
            ('ApiTimeoutError',
             lambda: MagicMock(return_value=iter_timeout())),
        ]
        for label, make_revs_mock in cases:
            with self.subTest(error=label), \
                 patch('pywikibot.error') as mock_error:
                self.page.revisions = make_revs_mock()
                bot, mock_review = self._run_auto()
                self._assert_reviewed(bot, mock_review, None)
                mock_error.assert_called_once()
                self.assertIn('Failed to load revisions',
                              mock_error.call_args[0][0])

    def test_auto_user_rights_errors_fail_closed(self) -> None:
        """Test failures querying user rights fail closed on first edit."""
        def make_rights_error_patch(exc: Exception):
            mock_user = MagicMock()
            mock_user.isAnonymous.return_value = False
            mock_user.rights.side_effect = exc
            return patch('pywikibot.User', return_value=mock_user)

        cases = [
            ('APIError', 'ProblemUser',
             make_rights_error_patch(APIError('rights_fail', 'API failed'))),
            ('ApiNotAvailableError', 'UnavailUser',
             make_rights_error_patch(
                 ApiNotAvailableError('User rights API unavailable'))),
            ('InvalidTitleError', '[[Invalid|User]]',
             patch('pywikibot.User',
                   side_effect=InvalidTitleError('Invalid username'))),
        ]
        for label, username, user_patch in cases:
            with self.subTest(error=label), \
                 user_patch, \
                 patch('pywikibot.warning') as mock_warning:
                revs = [
                    self._make_rev(101, username),
                    self._make_rev(100, 'OldEditor'),
                ]
                bot, mock_review = self._run_auto(iter(revs), latest_revid=101)
                self._assert_reviewed(bot, mock_review, None)
                mock_warning.assert_called_once()
                self.assertIn('Could not determine rights',
                              mock_warning.call_args[0][0])

    def test_auto_user_rights_timeout_prior_trusted_reviewed(self) -> None:
        """Test ApiTimeoutError on user rights reviews prior eligible edit."""
        revs = [
            self._make_rev(103, 'User3'),
            self._make_rev(102, 'TimeoutUser'),
            self._make_rev(101, 'TrustedUser'),
            self._make_rev(100, 'OldEditor'),
        ]

        def fake_user(site, username):
            user = MagicMock()
            user.username = username
            user.isAnonymous = MagicMock(return_value=False)
            if username == 'TimeoutUser':
                user.rights = MagicMock(
                    side_effect=ApiTimeoutError('Timeout querying rights'))
            else:
                user.rights = MagicMock(return_value=['autoreview'])
            return user

        with patch('pywikibot.User', side_effect=fake_user), \
             patch('pywikibot.warning') as mock_warning:
            bot, mock_review = self._run_auto(iter(revs), latest_revid=103)

            # Rev 101 (trusted) must be reviewed; Rev 102 and 103 must not
            self._assert_reviewed(bot, mock_review, 101)
            mock_warning.assert_called_once()
            self.assertIn('Could not determine rights',
                          mock_warning.call_args[0][0])

    def test_auto_anonymous_ip_user_rejected(self) -> None:
        """Test that anonymous/IP editor is rejected and not reviewed."""
        revs = [
            self._make_rev(101, '192.0.2.1'),
            self._make_rev(100, 'OldEditor'),
        ]
        mock_user = MagicMock()
        mock_user.isAnonymous.return_value = True

        with patch('pywikibot.User', return_value=mock_user), \
             patch('pywikibot.info') as mock_info:
            bot, mock_review = self._run_auto(iter(revs), latest_revid=101)

            self._assert_reviewed(bot, mock_review, None)
            mock_user.isAnonymous.assert_called_once()
            self.assertTrue(any('Untrusted edit encountered' in str(call)
                                for call in mock_info.call_args_list))

    def test_auto_stable_revid_none(self) -> None:
        """Test unreviewed pages (stable_revid=None) with and without block."""
        cases = [
            (
                'all_trusted_reviews_latest',
                [(103, 'Trusted3'), (102, 'Trusted2'), (101, 'Trusted1')],
                {'Trusted1': ['autoreview'], 'Trusted2': ['autoreview'],
                 'Trusted3': ['autoreview']},
                103,
                False,
            ),
            (
                'untrusted_stops_at_last_trusted',
                [(103, 'Trusted3'), (102, 'Untrusted'), (101, 'Trusted1')],
                {'Trusted1': ['autoreview'], 'Untrusted': [],
                 'Trusted3': ['autoreview']},
                101,
                True,
            ),
        ]
        for name, spec, rights, expected, check_log in cases:
            with self.subTest(case=name), patch('pywikibot.info') as mock_info:
                revs = [self._make_rev(rid, user) for rid, user in spec]
                bot, mock_review = self._run_auto(
                    iter(revs),
                    stable_revid=None,
                    latest_revid=103,
                    user_rights=rights,
                )
                self._assert_reviewed(bot, mock_review, expected)
                if check_log:
                    self.assertTrue(
                        any('Untrusted edit encountered' in str(call)
                            for call in mock_info.call_args_list))

    def test_auto_latest_revid_none(self) -> None:
        """Test latest_revision_id=None logs info and skips page."""
        with patch('pywikibot.info') as mock_info:
            bot, mock_review = self._run_auto(
                stable_revid=None, latest_revid=None)

            self._assert_reviewed(bot, mock_review, None)
            self.assertTrue(any('has no revisions to review' in str(call)
                                for call in mock_info.call_args_list))

    def test_auto_same_second_ordering(self) -> None:
        """Test same-second revision ordering resolves boundary cases."""
        t = Timestamp(2026, 1, 1, 12, 0, 0)
        t_plus_1 = t + timedelta(seconds=1)
        rev98 = self._make_rev(98, 'Editor98', timestamp=t)
        rev99 = self._make_rev(99, 'PriorEditor', timestamp=t)
        rev100 = self._make_rev(100, 'OldEditor', timestamp=t)
        rev101 = self._make_rev(101, 'Trusted1', timestamp=t)
        rev102 = self._make_rev(102, 'Trusted2', timestamp=t)
        rev101_next = self._make_rev(101, 'Trusted1', timestamp=t_plus_1)
        rights = {'Trusted1': ['autoreview'], 'Trusted2': ['autoreview']}

        cases = [
            ('unordered_generator', [rev100, rev102, rev101], 102, 102),
            ('stable_middle_in_group', [rev99, rev100, rev101], 101, 101),
            ('stable_at_end_of_group',
             [rev101_next, rev100, rev99, rev98], 101, 101),
            ('stable_at_beginning_of_group',
             [rev102, rev101, rev100], 102, 102),
        ]
        for name, revs, latest, expected in cases:
            with self.subTest(case=name):
                self.page.get_revision = MagicMock(return_value=rev100)
                bot, mock_review = self._run_auto(
                    list(revs), latest_revid=latest, user_rights=rights)
                self._assert_reviewed(bot, mock_review, expected)

    def test_auto_prepopulated_revision_cache(self) -> None:
        """Test pre-populated revision cache does not alter selection."""
        t = Timestamp(2026, 1, 1, 12, 0, 0)
        rev100 = self._make_rev(100, 'OldEditor', timestamp=t)
        rev101 = self._make_rev(101, 'Trusted1', timestamp=t)
        rev102 = self._make_rev(102, 'Trusted2', timestamp=t)

        # Pre-populate page._revisions with 100 first, simulating get_revision
        # caching stable revision before loadrevisions adds 102 and 101.
        self.page._revisions = {100: rev100, 102: rev102, 101: rev101}
        # In dry mode, mock site.loadrevisions so real BasePage.revisions runs
        self.page.site.loadrevisions = MagicMock()
        if 'revisions' in self.page.__dict__:
            del self.page.__dict__['revisions']
        self.page.get_revision = MagicMock(return_value=rev100)

        # Real BasePage.revisions yields [100, 102, 101] due to cache
        # insertion order; secondary sort corrects this to [102, 101, 100].
        bot, mock_review = self._run_auto(
            user_rights={'Trusted1': ['autoreview'],
                         'Trusted2': ['autoreview']})
        self._assert_reviewed(bot, mock_review, 102)

    def test_auto_stable_get_revision_api_error_fails_closed(self) -> None:
        """Test API error retrieving stable revision fails closed."""
        self.page.get_revision = MagicMock(
            side_effect=ApiTimeoutError('Timeout fetching stable revision'))

        with patch('pywikibot.error') as mock_error:
            bot, mock_review = self._run_auto()

            self._assert_reviewed(bot, mock_review, None)
            mock_error.assert_called_once()
            self.assertIn('Failed to load stable revision',
                          mock_error.call_args[0][0])

    def test_main_auto_mutually_exclusive_options(self) -> None:
        """Test main() exits when -auto conflicts with -unreview/-revid."""
        for option in ('-unreview', '-revid:123'):
            with self.subTest(option=option), \
                 patch('pywikibot.error') as mock_error:
                main('-auto', option)
                mock_error.assert_called_once()
                self.assertIn('cannot be used together',
                              mock_error.call_args[0][0])

    def test_main_auto_and_trusted_options(self) -> None:
        """Test main() parses -auto and comma-separated -trusted users."""
        cases = [
            (('-auto', '-always'), None),
            (('-trusted:User1,User2', '-always'), ['User1', 'User2']),
        ]
        for args, expected_trusted in cases:
            with self.subTest(args=args), \
                 patch('scripts.review.pending_pages_generator',
                       return_value=[self.page]), \
                 patch('scripts.review.ReviewBot') as mock_bot:
                main(*args)
                mock_bot.assert_called_once()
                self.assertTrue(mock_bot.call_args.kwargs.get('auto'))
                self.assertEqual(
                    mock_bot.call_args.kwargs.get('trusted'),
                    expected_trusted)

    def test_main_trusted_empty_fails(self) -> None:
        """Test main() with empty -trusted parameter logs error and exits."""
        with patch('pywikibot.input', return_value=''), \
             patch('pywikibot.error') as mock_error:
            main('-trusted:')
            mock_error.assert_called_once()
            self.assertIn('No trusted users specified',
                          mock_error.call_args[0][0])


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
