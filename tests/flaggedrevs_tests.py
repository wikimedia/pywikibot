#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Unit tests for Page.stable_revision."""
from __future__ import annotations

import unittest
from contextlib import suppress
from unittest.mock import MagicMock, patch

import pywikibot
from pywikibot.exceptions import (
    APIError,
    UnknownExtensionError,
    UserRightsError,
)
from pywikibot.page import Revision
from tests.aspects import PatchingTestCase, TestCase


class TestPageStableRevision(TestCase):

    """Test Page.stable_revision with full mocking."""

    family = 'wikipedia'
    code = 'fi'
    dry = True

    def setUp(self) -> None:
        """Test setup."""
        super().setUp()
        self.page = pywikibot.Page(self.site, 'TestPage')
        self.page.exists = MagicMock(return_value=True)

    def _mock_response(self, data: dict | list[dict]) -> dict:
        """Helper: build API response for action=query&prop=flagged."""
        return {
            'query': {
                'pages': data if isinstance(data, list) else [data]
            }
        }

    @patch('pywikibot.site._apisite.APISite.has_extension')
    def test_stable_revision_flaggedrevs_disabled(self, mock_has_ext):
        """FlaggedRevs not enabled → return None."""
        mock_has_ext.return_value = False

        with self.assertRaisesRegex(
            UnknownExtensionError,
            'Method "stable_revid" is not implemented without the extension '
            'FlaggedRevs'
        ):
            self.page.stable_revision

    @patch('pywikibot.site._apisite.APISite.simple_request')
    @patch('pywikibot.site._apisite.APISite.has_extension')
    def test_stable_revision_no_flagged_data(self, mock_has_ext, mock_req):
        """API returns no 'flagged' key → return None."""
        mock_has_ext.return_value = True
        mock_req.return_value.submit.return_value = self._mock_response(
            {'pageid': 1, 'ns': 0, 'title': 'TestPage'}
        )

        result = self.page.stable_revision
        self.assertIsNone(result)

    @patch('pywikibot.site._apisite.APISite.simple_request')
    @patch('pywikibot.site._apisite.APISite.has_extension')
    def test_stable_revision_no_stable_revid(self, mock_has_ext, mock_req):
        """'flagged' exists but no 'stable_revid' → return None."""
        mock_has_ext.return_value = True
        mock_req.return_value.submit.return_value = self._mock_response(
            {
                'pageid': 1,
                'title': 'TestPage',
                'flagged': {'level': 1}
            }
        )

        result = self.page.stable_revision
        self.assertIsNone(result)

    @patch('pywikibot.site._apisite.APISite.simple_request')
    @patch('pywikibot.site._apisite.APISite.has_extension')
    def test_stable_revision_success(self, mock_has_ext, mock_req):
        """Valid stable_revid → return Revision with content."""
        mock_has_ext.return_value = True

        # Mock get_revision to return a real-looking Revision
        mock_rev = MagicMock(spec=Revision)
        mock_rev.revid = 12345
        mock_rev.text = 'Stable content'
        mock_rev.user = 'Reviewer'
        mock_rev.timestamp = pywikibot.Timestamp(2025, 1, 1)

        with patch.object(self.page,
                          'get_revision',
                          return_value=mock_rev):
            mock_req.return_value.submit.return_value = self._mock_response(
                {
                    'pageid': 1,
                    'title': 'TestPage',
                    'flagged': {
                        'stable_revid': 12345,
                        'level': 2,
                        'pending_since': '2025-01-01T00:00:00Z'
                    }
                }
            )

            result = self.page.stable_revision

            self.assertEqual(result, mock_rev)
            self.assertEqual(result.revid, 12345)
            self.assertIn('Stable content', result.text)

    @patch('pywikibot.site._apisite.APISite.simple_request')
    @patch('pywikibot.site._apisite.APISite.has_extension')
    def test_stable_revision_multiple_pages(self, mock_has_ext, mock_req):
        """Multiple pages in response → still find correct one."""
        mock_has_ext.return_value = True

        # Mock get_revision to return a Revision with revid=999
        mock_rev = MagicMock(spec=Revision)
        mock_rev.revid = 999
        mock_rev.text = 'Other stable content'

        with patch.object(self.page, 'get_revision', return_value=mock_rev):
            mock_req.return_value.submit.return_value = self._mock_response([
                {
                    'pageid': 1,
                    'title': 'TestPage',
                    'flagged': {'stable_revid': 999}
                },
                {
                    'pageid': 2,
                    'title': 'OtherPage',
                    'flagged': {'stable_revid': 888}
                }
            ])

            result = self.page.stable_revision
            self.assertEqual(result.revid, 999)


class TestFlaggedRevsReview(PatchingTestCase):

    """Test site.review() with flagged revisions."""

    family = 'wikipedia'
    code = 'fi'
    dry = True

    def setUp(self):
        """Set up Test and patches."""
        super().setUp()
        self.token = '123ABC+\\'

        self.mock_req = MagicMock()
        self.patch(
            pywikibot.site._apisite.APISite,
            'simple_request',
            self.mock_req,
        )
        self.submit = self.mock_req.return_value.submit

        self.patch(
            pywikibot.site._tokenwallet.TokenWallet,
            '__getitem__',
            lambda *_: self.token,
        )

        self.patch(
            pywikibot.site._apisite.APISite,
            'has_extension',
            lambda *_: True,
        )

        self.patch(
            pywikibot.site._apisite.APISite,
            'has_right',
            lambda *_: True,
        )

        self.patch(
            self.site,
            '_paraminfo',
            {
                'review': {
                    'parameters': [
                        {'name': 'comment'},
                        {'name': 'flag_accuracy'},
                    ]
                }
            },
        )

    def _mock_success(self, revid: int, **extra):
        return {
            'review': {
                'revid': revid,
                'result': 'Success',
                **extra
            }
        }

    def test_review_basic(self) -> None:
        """Review a revision without any flags (simple approval)."""
        revid = 12345
        self.submit.return_value = self._mock_success(revid)
        self.site.review_revision(revid=revid, comment='unit test')

        self.mock_req.assert_called_once_with(
            action='review',
            token=self.token,
            revid=revid,
            comment='unit test',
            formatversion=2,
        )

    def test_review_unapprove(self) -> None:
        """Un-approve a previously approved revision."""
        revid = 12347
        self.submit.return_value = self._mock_success(revid)

        self.site.review_revision(
            revid=revid,
            comment='unit test unapprove',
            unapprove=True
        )

        self.mock_req.assert_called_once_with(
            action='review',
            token=self.token,
            revid=revid,
            comment='unit test unapprove',
            unapprove='1',
            formatversion=2,
        )

    def test_review_missing_token(self) -> None:
        """Calling review() without a token raises ``notoken``."""
        self.site.tokens.clear()
        self.submit.side_effect = APIError(
            code='notoken',
            info='No CSRF token',
            other={},
        )

        with self.assertRaises(APIError) as cm:
            self.site.review_revision(revid=999)

        self.assertEqual(cm.exception.code, 'notoken')

    def test_review_insufficient_rights(self) -> None:
        """User without ``review`` right gets ``permissiondenied``."""
        self.submit.side_effect = APIError(
            code='permissiondenied',
            info="You don't have permission to review revisions.",
            other={},
        )

        with self.assertRaises(APIError) as cm:
            self.site.review_revision(revid=888)

        self.assertEqual(cm.exception.code, 'permissiondenied')

    def test_review_defaults(self) -> None:
        """Calling review() with only revid and token is allowed."""
        revid = 12348
        self.submit.return_value = self._mock_success(revid)
        self.site.review_revision(revid=revid)

        self.mock_req.assert_called_once_with(
            action='review',
            token=self.token,
            revid=revid,
            comment=None,
            formatversion=2,
        )


class TestBasePageReview(TestCase):

    """Test review and unreview methods."""

    family = 'wikipedia'
    code = 'test2'
    cache = True

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()
        cls.flagged = pywikibot.Page(cls.site, 'BTP')
        cls.unflagged = pywikibot.Page(cls.site, 'UBTP')

    def test_revision_ids(self):
        """Test revision ids."""
        self.assertEqual(self.flagged.stable_revision_id,
                         self.flagged.latest_revision_id)
        self.assertIsNotNone(self.unflagged.latest_revision_id)
        self.assertIsNone(self.unflagged.stable_revision_id)

    def test_review_check_revisions(self):
        """Test exceptions."""
        with self.assertRaisesRegex(
            ValueError,
            r'Revision 4711 does not belong to \[\[test2:BTP\]\]'
        ):
            self.flagged.review(revid=4711)
        with self.assertRaisesRegex(ValueError, "Invalid revision id '0815'"):
            self.flagged.review(revid='0815')
        with self.assertRaisesRegex(ValueError, 'Invalid revision id True'):
            self.flagged.review(revid=True)
        with self.assertRaisesRegex(ValueError, 'Invalid revision id 3.14159'):
            self.flagged.review(revid=3.14159)
        with self.assertRaisesRegex(ValueError, 'Invalid revision id -273'):
            self.flagged.review(revid=-273)

    def test_review(self):
        """Test review calls without site.review_revision."""
        with self.assertRaisesRegex(
            UserRightsError,
            r'User ".+" does not have required user right "review" on site'
        ):
            self.flagged.review()
        self.assertNotHasAttr(self.flagged, '_stable_revision_id')

        with self.assertRaisesRegex(
            UserRightsError,
            r'User ".+" does not have required user right "review" on site'
        ):
            self.unflagged.review()
        self.assertNotHasAttr(self.flagged, '_stable_revision_id')

    def test_unreview(self):
        """Test unreview calls without site.review_revision."""
        self.assertIsNone(self.unflagged.unreview())
        self.assertHasAttr(self.unflagged, '_stable_revision_id')
        self.assertIsNone(self.unflagged.unreview(refresh=True))
        self.assertHasAttr(self.unflagged, '_stable_revision_id')

        with self.assertRaisesRegex(
            UserRightsError,
            r'User ".+" does not have required user right "review" on site'
        ):
            self.flagged.unreview()
        self.assertHasAttr(self.flagged, '_stable_revision_id')

        with self.assertRaisesRegex(
            UserRightsError,
            r'User ".+" does not have required user right "review" on site'
        ):
            self.flagged.unreview(refresh=True)
        self.assertHasAttr(self.flagged, '_stable_revision_id')

    def test_review_calls_site(self):
        """Test review calls site.review_revision."""
        revid = self.unflagged.latest_revision_id

        with patch.object(
            self.site,
            'review_revision',
            return_value=None,
        ) as review_revision:
            self.unflagged.review()

        review_revision.assert_called_once_with(
            revid,
            summary=None,
            flag=None,
        )
        self.assertNotHasAttr(self.unflagged, '_stable_revision_id')

    def test_unreview_calls_site(self):
        """Test unreview calls site.review_revision."""
        revid = self.flagged.stable_revision_id

        with patch.object(
            self.site,
            'review_revision',
            return_value=None,
        ) as review_revision:
            self.flagged.unreview()

        review_revision.assert_called_once_with(
            revid,
            summary=None,
            unapprove=True,
        )
        self.assertNotHasAttr(self.flagged, '_stable_revision_id')


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
