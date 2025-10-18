#!/usr/bin/env python3
"""Tests for the eventstreams module."""
#
# (C) Pywikibot team, 2017-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import json
import re
import unittest
from contextlib import suppress
from unittest import mock

from pywikibot import Site, config
from pywikibot.comms.eventstreams import EventSource, EventStreams
from pywikibot.family import WikimediaFamily
from tests.aspects import DefaultSiteTestCase, TestCase, require_modules
from tests.utils import skipping


@mock.patch('pywikibot.comms.eventstreams.EventSource', new=mock.MagicMock())
class TestEventStreamsUrlTests(TestCase):

    """Url tests for eventstreams module."""

    sites = {
        'de-wp': {
            'family': 'wikipedia',
            'code': 'de',
            'hostname': 'de.wikipedia.org',
        },
        'en-wq': {
            'family': 'wikiquote',
            'code': 'en',
            'hostname': 'en.wikiquote.org',
        },
    }

    def test_url_parameter(self, key) -> None:
        """Test EventStreams with given url."""
        e = EventStreams(url=self.sites[key]['hostname'])
        self.assertEqual(e._url, self.sites[key]['hostname'])
        self.assertEqual(e._url, e.url)
        self.assertEqual(e._url, e.sse_kwargs.get('url'))
        self.assertIsNone(e._total)
        self.assertIsNone(e._streams)
        self.assertRegex(
            repr(e),
            rf"^EventStreams\(url={self.sites[key]['hostname']!r}, "
            r"headers={'user-agent': '[^']+'}\)$"
        )

    def test_url_from_site(self, key) -> None:
        """Test EventStreams with url from site."""
        site = self.get_site(key)
        streams = 'recentchange'
        e = EventStreams(site=site, streams=streams)
        self.assertEqual(
            e._url, 'https://stream.wikimedia.org/v2/stream/' + streams)
        self.assertEqual(e._url, e.url)
        self.assertEqual(e._url, e.sse_kwargs.get('url'))
        self.assertIsNone(e._total)
        self.assertEqual(e._streams, streams)
        site_repr = re.escape(f'site={site!r}, ') if site != Site() else ''
        self.assertRegex(
            repr(e),
            r"^EventStreams\(headers={'user-agent': '[^']+'}, "
            rf'{site_repr}streams={streams!r}\)$'
        )


@mock.patch('pywikibot.comms.eventstreams.EventSource', new=mock.MagicMock())
class TestEventStreamsStreamsTests(DefaultSiteTestCase):

    """Stream tests for eventstreams module."""

    def setUp(self) -> None:
        """Set up tests."""
        super().setUp()
        site = self.get_site()
        fam = site.family
        if not isinstance(fam, WikimediaFamily):
            self.skipTest(
                f"Family '{fam}' of site '{site}' is not a WikimediaFamily.")

    def test_url_with_streams(self) -> None:
        """Test EventStreams with url from default site."""
        streams = 'recentchange'
        e = EventStreams(streams=streams)
        self.assertEqual(
            e._url, 'https://stream.wikimedia.org/v2/stream/' + streams)
        self.assertEqual(e._url, e.url)
        self.assertEqual(e._url, e.sse_kwargs.get('url'))
        self.assertIsNone(e._total)
        self.assertEqual(e._streams, streams)

    def test_multiple_streams(self) -> None:
        """Test EventStreams with multiple streams."""
        streams = ('page-create', 'page-move', 'page-delete')
        e = EventStreams(streams=streams)
        combined_streams = ','.join(streams)
        self.assertEqual(
            e._url,
            'https://stream.wikimedia.org/v2/stream/' + combined_streams)
        self.assertEqual(e._url, e.url)
        self.assertEqual(e._url, e.sse_kwargs.get('url'))
        self.assertEqual(e._streams, combined_streams)

    def test_url_missing_streams(self) -> None:
        """Test EventStreams with url from site with missing streams."""
        with self.assertRaises(NotImplementedError):
            EventStreams()


class TestEventStreamsSettingTests(TestCase):

    """Setting tests for eventstreams module."""

    dry = True

    def setUp(self) -> None:
        """Set up unit test."""
        super().setUp()
        with mock.patch('pywikibot.comms.eventstreams.EventSource'):
            self.es = EventStreams(url='dummy url')

    def test_maximum_items(self) -> None:
        """Test EventStreams total value."""
        total = 4711
        self.es.set_maximum_items(total)
        self.assertEqual(self.es._total, total)

    def test_timeout_setting(self) -> None:
        """Test EventStreams timeout value."""
        self.assertEqual(self.es.sse_kwargs.get('timeout'),
                         config.socket_timeout)

    def test_filter_function_settings(self) -> None:
        """Test EventStreams filter function settings."""
        def foo() -> bool:
            """Dummy function."""
            return True  # pragma: no cover

        self.es.register_filter(foo)
        self.assertEqual(self.es.filter['all'][0], foo)
        self.assertEqual(self.es.filter['any'], [])
        self.assertEqual(self.es.filter['none'], [])

        self.es.register_filter(foo, ftype='none')
        self.assertEqual(self.es.filter['all'][0], foo)
        self.assertEqual(self.es.filter['any'], [])
        self.assertEqual(self.es.filter['none'][0], foo)

        self.es.register_filter(foo, ftype='any')
        self.assertEqual(self.es.filter['all'][0], foo)
        self.assertEqual(self.es.filter['any'][0], foo)
        self.assertEqual(self.es.filter['none'][0], foo)

    def test_filter_function_settings_fail(self) -> None:
        """Test EventStreams failing filter function settings."""
        with self.assertRaises(TypeError):
            self.es.register_filter('test')

    def test_filter_settings(self) -> None:
        """Test EventStreams filter settings."""
        self.es.register_filter(foo='bar')
        self.assertTrue(callable(self.es.filter['all'][0]))
        self.es.register_filter(bar='baz')
        self.assertLength(self.es.filter['all'], 2)


class TestEventStreamsFilter(TestCase):

    """Filter tests for eventstreams module."""

    dry = True

    data = {'foo': True, 'bar': 'baz'}

    def setUp(self) -> None:
        """Set up unit test."""
        super().setUp()
        with mock.patch('pywikibot.comms.eventstreams.EventSource'):
            self.es = EventStreams(url='dummy url')

    def test_filter_function_all(self) -> None:
        """Test EventStreams filter all function."""
        self.es.register_filter(lambda x: True)
        self.assertTrue(self.es.streamfilter(self.data))
        self.es.register_filter(lambda x: False)
        self.assertFalse(self.es.streamfilter(self.data))

    def test_filter_function_any(self) -> None:
        """Test EventStreams filter any function."""
        self.es.register_filter(lambda x: True, ftype='any')
        self.assertTrue(self.es.streamfilter(self.data))
        self.es.register_filter(lambda x: False, ftype='any')
        self.assertTrue(self.es.streamfilter(self.data))

    def test_filter_function_none(self) -> None:
        """Test EventStreams filter none function."""
        self.es.register_filter(lambda x: False, ftype='none')
        self.assertTrue(self.es.streamfilter(self.data))
        self.es.register_filter(lambda x: True, ftype='none')
        self.assertFalse(self.es.streamfilter(self.data))

    def test_filter_false(self) -> None:
        """Test EventStreams filter with assignment of True."""
        self.es.register_filter(foo=False)
        self.assertFalse(self.es.streamfilter(self.data))

    def test_filter_true(self) -> None:
        """Test EventStreams filter with assignment of False."""
        self.es.register_filter(foo=True)
        self.assertTrue(self.es.streamfilter(self.data))

    def test_filter_value(self) -> None:
        """Test EventStreams filter with assignment of an int value."""
        self.es.register_filter(foo=10)
        self.assertFalse(self.es.streamfilter(self.data))

    def test_filter_sequence_false(self) -> None:
        """Test EventStreams filter with assignment of a sequence."""
        self.es.register_filter(bar=list('baz'))
        self.assertFalse(self.es.streamfilter(self.data))

    def test_filter_sequence_true(self) -> None:
        """Test EventStreams filter with assignment of a sequence."""
        self.es.register_filter(bar=('foo', 'bar', 'baz'))
        self.assertTrue(self.es.streamfilter(self.data))

    def test_filter_multiple(self) -> None:
        """Test EventStreams filter with multiple arguments."""
        self.es.register_filter(foo=False, bar='baz')
        self.assertFalse(self.es.streamfilter(self.data))
        self.es.filter = {'all': [], 'any': [], 'none': []}
        self.es.register_filter(foo=True, bar='baz')
        self.assertTrue(self.es.streamfilter(self.data))
        # check whether filter functions are different
        f, g = self.es.filter['all']
        c = {'foo': True}
        self.assertNotEqual(f(c), g(c))
        c = {'bar': 'baz'}
        self.assertNotEqual(f(c), g(c))

    def _test_filter(self, none_type, all_type, any_type, result) -> None:
        """Test a single fixed filter."""
        self.es.filter = {'all': [], 'any': [], 'none': []}
        self.es.register_filter(lambda x: none_type, ftype='none')
        self.es.register_filter(lambda x: all_type, ftype='all')
        if any_type is not None:
            self.es.register_filter(lambda x: any_type, ftype='any')
        self.assertEqual(
            self.es.streamfilter(self.data), result,
            'Test EventStreams filter mixed function failed for\n'
            f"'none': {none_type}, 'all': {all_type}, 'any': {any_type}\n"
            f'(expected {result}, given {not result})'
        )

    def test_filter_mixed_function(self) -> None:
        """Test EventStreams filter mixed function."""
        for none_type in (False, True):
            for all_type in (False, True):
                for any_type in (False, True, None):
                    result = none_type is False and all_type is True \
                        and (any_type is None or any_type is True)
                    self._test_filter(none_type, all_type, any_type, result)


class EventStreamsTestClass(EventStreams):

    """Test class of EventStreams."""

    def __iter__(self):
        """Iterator."""
        n = 0
        while self._total is None or n < self._total:
            if not hasattr(self, 'source'):
                self.source = EventSource(**self.sse_kwargs)
                self.source.connect()

            event = next(self.source)
            if event.type == 'message' and event.data:
                n += 1
                yield json.loads(event.data)

        self.source.close()
        del self.source


@require_modules('requests_sse')
class TestEventSource(TestCase):

    """Test sseclient.EventSource."""

    net = True

    def test_stream(self) -> None:
        """Verify that the EventSource delivers events without problems."""
        with skipping(NotImplementedError):
            self.es = EventStreamsTestClass(streams='recentchange')
        limit = 50
        self.es.set_maximum_items(limit)
        self.assertLength(list(self.es), limit)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
