# -*- coding: utf-8 -*-
"""Tests for the eventstreams module."""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from types import FunctionType

from tests import mock

from pywikibot.comms.eventstreams import EventStreams
from pywikibot import config
from pywikibot.family import WikimediaFamily

from tests.aspects import unittest, TestCase, DefaultSiteTestCase


@mock.patch('pywikibot.comms.eventstreams.EventSource', new=mock.MagicMock())
class TestEventStreamsUrlTests(TestCase):

    """Url tests for eventstreams module."""

    sites = {
        'de.wp': {
            'family': 'wikipedia',
            'code': 'de',
            'hostname': 'de.wikipedia.org',
        },
        'en.wq': {
            'family': 'wikiquote',
            'code': 'en',
            'hostname': 'en.wikiquote.org',
        },
    }

    def test_url_parameter(self, key):
        """Test EventStreams with given url."""
        e = EventStreams(url=self.sites[key]['hostname'])
        self.assertEqual(e._url, self.sites[key]['hostname'])
        self.assertEqual(e._url, e.url)
        self.assertEqual(e._url, e.sse_kwargs.get('url'))
        self.assertIsNone(e._total)
        self.assertIsNone(e._stream)

    def test_url_from_site(self, key):
        """Test EventStreams with url from site."""
        site = self.get_site(key)
        stream = 'recentchanges'
        e = EventStreams(site=site, stream=stream)
        self.assertEqual(
            e._url, 'https://stream.wikimedia.org/v2/stream/' + stream)
        self.assertEqual(e._url, e.url)
        self.assertEqual(e._url, e.sse_kwargs.get('url'))
        self.assertIsNone(e._total)
        self.assertEqual(e._stream, stream)


@mock.patch('pywikibot.comms.eventstreams.EventSource', new=mock.MagicMock())
class TestEventStreamsStreamTests(DefaultSiteTestCase):

    """Stream tests for eventstreams module."""

    def test_url_with_stream(self):
        """Test EventStreams with url from default site."""
        site = self.get_site()
        fam = site.family
        if not isinstance(fam, WikimediaFamily):
            self.skipTest(
                "Family '{0}' of site '{1}' is not a WikimediaFamily."
                .format(fam, site))

        stream = 'recentchanges'
        e = EventStreams(stream=stream)
        self.assertEqual(
            e._url, 'https://stream.wikimedia.org/v2/stream/' + stream)
        self.assertEqual(e._url, e.url)
        self.assertEqual(e._url, e.sse_kwargs.get('url'))
        self.assertIsNone(e._total)
        self.assertEqual(e._stream, stream)

    def test_url_missing_stream(self):
        """Test EventStreams with url from site with missing stream."""
        with self.assertRaises(NotImplementedError):
            EventStreams()


class TestEventStreamsSettingTests(TestCase):

    """Setting tests for eventstreams module."""

    dry = True

    def setUp(self):
        """Set up unit test."""
        super(TestEventStreamsSettingTests, self).setUp()
        with mock.patch('pywikibot.comms.eventstreams.EventSource'):
            self.es = EventStreams(url='dummy url')

    def test_maximum_items(self):
        """Test EventStreams total value."""
        total = 4711
        self.es.set_maximum_items(total)
        self.assertEqual(self.es._total, total)

    def test_timeout_setting(self):
        """Test EventStreams timeout value."""
        self.assertEqual(self.es.sse_kwargs.get('timeout'),
                         config.socket_timeout)

    def test_filter_function_settings(self):
        """Test EventStreams filter function settings."""
        def foo():
            """Dummy function."""
            return True

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

    def test_filter_function_settings_fail(self):
        """Test EventStreams failing filter function settings."""
        with self.assertRaises(TypeError):
            self.es.register_filter('test')

    def test_filter_settings(self):
        """Test EventStreams filter settings."""
        self.es.register_filter(foo='bar')
        self.assertIsInstance(self.es.filter['all'][0], FunctionType)
        self.es.register_filter(bar='baz')
        self.assertEqual(len(self.es.filter['all']), 2)


class TestEventStreamsFilterTests(TestCase):

    """Filter tests for eventstreams module."""

    dry = True

    data = {'foo': True, 'bar': 'baz'}

    def setUp(self):
        """Set up unit test."""
        super(TestEventStreamsFilterTests, self).setUp()
        with mock.patch('pywikibot.comms.eventstreams.EventSource'):
            self.es = EventStreams(url='dummy url')

    def test_filter_function_all(self):
        """Test EventStreams filter all function."""
        self.es.register_filter(lambda x: True)
        self.assertTrue(self.es.streamfilter(self.data))
        self.es.register_filter(lambda x: False)
        self.assertFalse(self.es.streamfilter(self.data))

    def test_filter_function_any(self):
        """Test EventStreams filter any function."""
        self.es.register_filter(lambda x: True, ftype='any')
        self.assertTrue(self.es.streamfilter(self.data))
        self.es.register_filter(lambda x: False, ftype='any')
        self.assertTrue(self.es.streamfilter(self.data))

    def test_filter_function_none(self):
        """Test EventStreams filter none function."""
        self.es.register_filter(lambda x: False, ftype='none')
        self.assertTrue(self.es.streamfilter(self.data))
        self.es.register_filter(lambda x: True, ftype='none')
        self.assertFalse(self.es.streamfilter(self.data))

    def test_filter_false(self):
        """Test EventStreams filter with assignment of True."""
        self.es.register_filter(foo=False)
        self.assertFalse(self.es.streamfilter(self.data))

    def test_filter_true(self):
        """Test EventStreams filter with assignment of False."""
        self.es.register_filter(foo=True)
        self.assertTrue(self.es.streamfilter(self.data))

    def test_filter_value(self):
        """Test EventStreams filter with assignment of a int value."""
        self.es.register_filter(foo=10)
        self.assertFalse(self.es.streamfilter(self.data))

    def _test_filter(self, none_type, all_type, any_type, result):
        """Test a single fixed filter."""
        self.es.filter = {'all': [], 'any': [], 'none': []}
        self.es.register_filter(lambda x: none_type, ftype='none')
        self.es.register_filter(lambda x: all_type, ftype='all')
        if any_type is not None:
            self.es.register_filter(lambda x: any_type, ftype='any')
        self.assertEqual(self.es.streamfilter(self.data), result,
                         'Test EventStreams filter mixed function failed for\n'
                         "'none': {0}, 'all': {1}, 'any': {2}\n"
                         '(expected {3}, given {4})'
                         .format(none_type, all_type, any_type,
                                 result, not result))

    def test_filter_mixed_function(self):
        """Test EventStreams filter mixed function."""
        for none_type in (False, True):
            for all_type in (False, True):
                for any_type in (False, True, None):
                    if none_type is False and all_type is True and (
                            any_type is None or any_type is True):
                        result = True
                    else:
                        result = False
                    self._test_filter(none_type, all_type, any_type, result)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
