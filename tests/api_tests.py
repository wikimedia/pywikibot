#!/usr/bin/env python3
"""API test module."""
#
# (C) Pywikibot team, 2007-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import datetime
import types
import unittest
from collections import defaultdict
from contextlib import suppress
from typing import NoReturn
from unittest.mock import patch

import pywikibot.family
import pywikibot.site
from pywikibot.data import api
from pywikibot.exceptions import APIError, NoUsernameError
from pywikibot.throttle import Throttle
from pywikibot.tools import suppress_warnings
from tests.aspects import DefaultDrySiteTestCase, DefaultSiteTestCase, TestCase
from tests.utils import FakeLoginManager


class TestApiFunctions(DefaultSiteTestCase):

    """API Request object test class."""

    @suppress_warnings(r'Request\(\) invoked without a site', RuntimeWarning)
    def testObjectCreation(self) -> None:
        """Test api.Request() constructor with implicit site creation."""
        req = api.Request(parameters={'action': 'test', 'foo': '',
                                      'bar': 'test'})
        self.assertTrue(req)
        self.assertEqual(req.site, self.get_site())


class TestDryApiFunctions(DefaultDrySiteTestCase):

    """API Request object test class."""

    def testObjectCreation(self) -> None:
        """Test api.Request() constructor."""
        mysite = self.get_site()
        req = api.Request(site=mysite, parameters={'action': 'test', 'foo': '',
                                                   'bar': 'test'})
        self.assertTrue(req)
        self.assertEqual(req.site, mysite)
        self.assertIn('foo', req._params)
        self.assertEqual(req['bar'], ['test'])
        # test item assignment
        req['one'] = '1'
        self.assertEqual(req._params['one'], ['1'])
        # test compliance with dict interface
        # req.keys() should contain 'action', 'foo', 'bar', 'one'
        self.assertLength(req.keys(), 4)
        self.assertIn('test', req._encoded_items().values())
        for item in req.items():
            self.assertLength(item, 2)

    @suppress_warnings(
        'Instead of using kwargs |Both kwargs and parameters are set',
        DeprecationWarning)
    def test_mixed_mode(self) -> None:
        """Test if parameters is used with kwargs."""
        req1 = api.Request(site=self.site, action='test', parameters='foo')
        self.assertIn('parameters', req1._params)

        req2 = api.Request(site=self.site, parameters={'action': 'test',
                                                       'parameters': 'foo'})
        self.assertEqual(req2['parameters'], ['foo'])
        self.assertEqual(req1._params, req2._params)


class TestParamInfo(DefaultSiteTestCase):

    """Test ParamInfo."""

    def test_init(self) -> None:
        """Test common initialization."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertIsEmpty(pi)
        pi._init()

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)
        self.assertLength(pi, pi._preloaded_modules)

        self.assertIn('info', pi.query_modules)
        self.assertIn('login', pi._action_modules)

    def test_init_query_first(self) -> None:
        """Test init where it first adds query and then main."""
        pi = api.ParamInfo(self.site, {'query', 'main'})
        self.assertIsEmpty(pi)
        pi._init()
        self.assertIn('main', pi._paraminfo)
        self.assertIn('query', pi._paraminfo)

    def test_init_pageset(self) -> None:
        """Test initializing with deprecated pageset."""
        site = self.get_site()
        self.assertNotIn('query', api.ParamInfo.init_modules)
        pi = api.ParamInfo(site, {'pageset'})
        self.assertNotIn('query', api.ParamInfo.init_modules)
        self.assertIsEmpty(pi)
        pi._init()

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)
        self.assertNotIn('pageset', pi._paraminfo)
        self.assertIn('query', pi._paraminfo)
        self.assertLength(pi, 3)
        self.assertLength(pi._preloaded_modules, 4)
        with self.assertRaisesRegex(ValueError,
                                    "paraminfo for 'pageset' not loaded"):
            pi.parameter('pageset', 'generator')

    def test_generators(self) -> None:
        """Test requesting the generator parameter."""
        site = self.get_site()
        pi = api.ParamInfo(site, {'query'})
        self.assertIsEmpty(pi)
        pi._init()

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)
        self.assertIn('query', pi._paraminfo)

        query_generators_param = pi.parameter('query', 'generator')
        self.assertIn('submodules', query_generators_param)
        self.assertEqual(query_generators_param['submoduleparamprefix'], 'g')
        for submodule, query in query_generators_param['submodules'].items():
            self.assertEqual('query+' + submodule, query)

    def test_with_module_info(self) -> None:
        """Test requesting the module info."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertIsEmpty(pi)
        pi.fetch(['info'])
        self.assertIn('query+info', pi._paraminfo)

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)
        self.assertLength(pi, 1 + len(pi._preloaded_modules))

        self.assertEqual(pi['info']['prefix'], 'in')

        param = pi.parameter('info', 'prop')
        self.assertIsInstance(param, dict)

        self.assertEqual(param['name'], 'prop')
        self.assertNotIn('deprecated', param)

        self.assertIsInstance(param['type'], list)

        self.assertIn('protection', param['type'])

    def test_with_module_revisions(self) -> None:
        """Test requesting the module revisions."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertIsEmpty(pi)
        pi.fetch(['revisions'])
        self.assertIn('query+revisions', pi._paraminfo)

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)
        self.assertLength(pi, 1 + len(pi._preloaded_modules))

        self.assertEqual(pi['revisions']['prefix'], 'rv')

        param = pi.parameter('revisions', 'prop')
        self.assertIsInstance(param, dict)

        self.assertEqual(param['name'], 'prop')
        self.assertNotIn('deprecated', param)

        self.assertIsInstance(param['type'], list)

        self.assertIn('user', param['type'])

    def test_multiple_modules(self) -> None:
        """Test requesting multiple modules in one fetch."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertIsEmpty(pi)
        pi.fetch(['info', 'revisions'])
        self.assertIn('query+info', pi._paraminfo)
        self.assertIn('query+revisions', pi._paraminfo)

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)

        self.assertLength(pi, 2 + len(pi._preloaded_modules))

    def test_with_invalid_module(self) -> None:
        """Test requesting different kind of invalid modules."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertIsEmpty(pi)

        with patch.object(pywikibot, 'warning') as w:
            pi.fetch('foobar')
            with self.assertRaises(KeyError):
                pi.__getitem__('foobar')
            with self.assertRaises(KeyError):
                pi.__getitem__('foobar+foobar')
        # The warning message may be different with older MW versions.
        self.assertIn('API warning (paraminfo): ', w.call_args[0][0])

        self.assertNotIn('foobar', pi._paraminfo)
        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)

        self.assertLength(pi, pi._preloaded_modules)

    def test_submodules(self) -> None:
        """Test another module apart from query having submodules."""
        pi = api.ParamInfo(self.site)
        self.assertFalse(pi._modules)
        pi.fetch(['query'])
        self.assertIn('query', pi._modules)
        self.assertIsInstance(pi._modules['query'], set)
        self.assertIn('revisions', pi._modules['query'])
        self.assertEqual(pi.submodules('query'), pi.query_modules)
        for mod in pi.submodules('query', True):
            self.assertEqual(mod[:6], 'query+')
            self.assertEqual(mod[6:], pi[mod]['name'])
            self.assertEqual(mod, pi[mod]['path'])

        with patch.object(pywikibot, 'warning') as w, \
                self.assertRaises(KeyError):
            pi.__getitem__('query+foobar')

        self.assertIn('API warning (paraminfo): ', w.call_args[0][0])

        with self.assertRaises(KeyError):
            pi.submodules('edit')

    def test_module_paths(self) -> None:
        """Test module paths use the complete paths."""
        pi = api.ParamInfo(self.site)
        self.assertIn('help', pi.module_paths)
        self.assertNotIn('revisions', pi.module_paths)
        self.assertIn('query+revisions', pi.module_paths)
        self.assertNotIn('allpages', pi.module_paths)
        self.assertIn('query+allpages', pi.module_paths)

    def test_prefix_map(self) -> None:
        """Test module prefixes use the path."""
        pi = api.ParamInfo(self.site)
        self.assertIn('query+revisions', pi.prefix_map)
        self.assertIn('login', pi.prefix_map)
        self.assertIn('query+allpages', pi.prefix_map)
        for mod in pi.prefix_map:
            self.assertEqual(mod, pi[mod]['path'])

    def test_attributes(self) -> None:
        """Test attributes method."""
        pi = api.ParamInfo(self.site)
        attributes = pi.attributes('mustbeposted')
        self.assertIn('edit', attributes)
        for mod, value in attributes.items():
            self.assertEqual(mod, pi[mod]['path'])
            self.assertEqual(value, '')


class TestParaminfoModules(DefaultSiteTestCase):

    """Test loading all paraminfo modules."""

    def test_action_modules(self) -> None:
        """Test loading all action modules."""
        self.site._paraminfo.fetch(self.site._paraminfo.action_modules)

    def test_query_modules(self) -> None:
        """Test loading all query modules."""
        self.site._paraminfo.fetch(self.site._paraminfo.query_modules)


class TestOptionSet(TestCase):

    """OptionSet class test class."""

    family = 'wikipedia'
    code = 'en'

    def test_non_lazy_load(self) -> None:
        """Test OptionSet with initialised site."""
        options = api.OptionSet(self.get_site(), 'recentchanges', 'show')
        with self.assertRaises(KeyError):
            options.__setitem__('invalid_name', True)
        with self.assertRaises(ValueError):
            options.__setitem__('anon', 'invalid_value')
        options['anon'] = True
        self.assertCountEqual(['anon'], options._enabled)
        self.assertEqual(set(), options._disabled)
        self.assertLength(options, 1)
        self.assertEqual(['anon'], list(options))
        self.assertEqual(['anon'], list(options.api_iter()))
        options['bot'] = False
        self.assertCountEqual(['anon'], options._enabled)
        self.assertCountEqual(['bot'], options._disabled)
        self.assertLength(options, 2)
        self.assertEqual(['anon', 'bot'], list(options))
        self.assertEqual(['anon', '!bot'], list(options.api_iter()))
        options.clear()
        self.assertEqual(set(), options._enabled)
        self.assertEqual(set(), options._disabled)
        self.assertIsEmpty(options)
        self.assertEqual([], list(options))
        self.assertEqual([], list(options.api_iter()))

    def test_lazy_load(self) -> None:
        """Test OptionSet with delayed site initialisation."""
        options = api.OptionSet()
        options['invalid_name'] = True
        options['anon'] = True
        self.assertIn('invalid_name', options._enabled)
        self.assertLength(options, 2)
        with self.assertRaises(KeyError):
            options._set_site(self.get_site(), 'recentchanges', 'show')
        self.assertLength(options, 2)
        options._set_site(self.get_site(), 'recentchanges', 'show',
                          clear_invalid=True)
        self.assertLength(options, 1)
        with self.assertRaises(TypeError):
            options._set_site(self.get_site(), 'recentchanges', 'show')


class TestDryOptionSet(DefaultDrySiteTestCase):

    """OptionSet class test class."""

    def test_mutable_mapping(self) -> None:
        """Test keys, values and items from MutableMapping."""
        options = api.OptionSet()
        options['a'] = True
        options['b'] = False
        options['c'] = None
        self.assertCountEqual(['a', 'b'], list(options.keys()))
        self.assertCountEqual([True, False], list(options.values()))
        self.assertEqual(set(), set(options.values()) - {True, False})
        self.assertCountEqual([('a', True), ('b', False)],
                              list(options.items()))


class TestDryPageGenerator(TestCase):

    """Dry API PageGenerator object test class."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    # api.py sorts 'pages' using the string key, which is not a
    # numeric comparison.
    titles = ('Broadcaster (definition)', 'Wiktionary', 'Broadcaster.com',
              'Wikipedia:Disambiguation')

    def setUp(self) -> None:
        """Set up test case."""
        super().setUp()
        mysite = self.get_site()
        self.gen = api.PageGenerator(site=mysite,
                                     generator='links',
                                     parameters={'titles': "User:R'n'B"})
        # following test data is copied from an actual api.php response,
        # but that query no longer matches this dataset.
        # http://en.wikipedia.org/w/api.php?action=query&generator=links&titles=User:R%27n%27B
        self.gen.request.submit = types.MethodType(lambda self: {
            'query': {'pages': {'296589': {'pageid': 296589,
                                           'ns': 0,
                                           'title': 'Broadcaster.com'
                                           },
                                '13918157': {'pageid': 13918157,
                                             'ns': 0,
                                             'title': 'Broadcaster '
                                                      '(definition)'
                                             },
                                '156658': {'pageid': 156658,
                                           'ns': 0,
                                           'title': 'Wiktionary'
                                           },
                                '47757': {'pageid': 47757,
                                          'ns': 4,
                                          'title': 'Wikipedia:Disambiguation'
                                          }
                                }
                      }
        }, self.gen.request)

        # On a dry site, the namespace objects only have canonical names.
        # Add custom_name for this site namespace, to match the live site.
        if 'Wikipedia' not in self.site.namespaces:
            self.site.namespaces[4].custom_name = 'Wikipedia'
            self.site.namespaces._namespace_names['wikipedia'] = (
                self.site.namespaces[4])

    def test_results(self) -> None:
        """Test that PageGenerator yields pages with expected attributes."""
        self.assertPageTitlesEqual(self.gen, self.titles)

    def test_initial_limit(self) -> None:
        """Test the default limit."""
        self.assertIsNone(self.gen.limit)  # limit is initially None

    def test_set_limit_as_number(self) -> None:
        """Test setting the limit using an int."""
        for i in range(-2, 4):
            self.gen.set_maximum_items(i)
            self.assertEqual(self.gen.limit, i)

    def test_set_limit_as_string(self) -> None:
        """Test setting the limit using an int cast into a string."""
        for i in range(-2, 4):
            self.gen.set_maximum_items(str(i))
            self.assertEqual(self.gen.limit, i)

    def test_set_limit_not_number(self) -> None:
        """Test setting the limit to not a number."""
        with self.assertRaisesRegex(
                ValueError,
                r"invalid literal for int\(\) with base 10: 'test'"):
            self.gen.set_maximum_items('test')

    def test_limit_range(self) -> None:
        """Test that PageGenerator yields the requested amount of pages."""
        for i in range(1, 6):
            with self.subTest(amount=i):
                self.gen.set_maximum_items(i)
                self.assertPageTitlesEqual(self.gen, self.titles[:i])
                self.gen.restart()

    def test_limit_zero(self) -> None:
        """Test that a limit of zero is the same as limit None."""
        self.gen.set_maximum_items(0)
        self.assertPageTitlesEqual(self.gen, self.titles)

    def test_limit_omit(self) -> None:
        """Test that limit omitted is the same as limit None."""
        self.gen.set_maximum_items(-1)
        self.assertPageTitlesEqual(self.gen, self.titles)

    def test_namespace(self) -> None:
        """Test PageGenerator set_namespace."""
        for namespace in (0, 1, None):
            with self.subTest(namespace=namespace), \
                    self.assertRaises(AssertionError):
                self.gen.set_namespace(namespace)


class TestPropertyGenerator(TestCase):

    """API PropertyGenerator object test class."""

    family = 'wikipedia'
    code = 'en'

    def test_info(self) -> None:
        """Test PropertyGenerator with prop 'info'."""
        mainpage = self.get_mainpage()
        links = list(self.site.pagelinks(mainpage, total=10))
        titles = [link.title(with_section=False) for link in links]
        gen = api.PropertyGenerator(site=self.site,
                                    prop='info',
                                    parameters={'titles': '|'.join(titles)})

        count = 0
        for count, pagedata in enumerate(gen, start=1):
            self.assertIsInstance(pagedata, dict)
            self.assertIn('pageid', pagedata)
            self.assertIn('lastrevid', pagedata)
        self.assertLength(links, count)

    def test_one_continuation(self) -> None:
        """Test PropertyGenerator with prop 'revisions'."""
        mainpage = self.get_mainpage()
        links = list(self.site.pagelinks(mainpage, total=10))
        titles = [link.title(with_section=False) for link in links]
        gen = api.PropertyGenerator(site=self.site,
                                    prop='revisions',
                                    parameters={'titles': '|'.join(titles)})
        gen.set_maximum_items(-1)  # suppress use of "rvlimit" parameter

        count = 0
        for count, pagedata in enumerate(gen, start=1):
            self.assertIsInstance(pagedata, dict)
            self.assertIn('pageid', pagedata)
            self.assertIn('revisions', pagedata)
            self.assertIn('revid', pagedata['revisions'][0])
        self.assertLength(links, count)

    def test_two_continuations(self) -> None:
        """Test PropertyGenerator with prop 'revisions' and 'coordinates'."""
        mainpage = self.get_mainpage()
        links = list(self.site.pagelinks(mainpage, total=10))
        titles = [link.title(with_section=False) for link in links]
        gen = api.PropertyGenerator(site=self.site,
                                    prop='revisions|coordinates',
                                    parameters={'titles': '|'.join(titles)})
        gen.set_maximum_items(-1)  # suppress use of "rvlimit" parameter

        count = 0
        for count, pagedata in enumerate(gen, start=1):
            self.assertIsInstance(pagedata, dict)
            self.assertIn('pageid', pagedata)
            self.assertIn('revisions', pagedata)
            self.assertIn('revid', pagedata['revisions'][0])
        self.assertLength(links, count)

    def test_many_continuations_limited(self) -> None:
        """Test PropertyGenerator with many limited props."""
        mainpage = self.get_mainpage()
        links = list(self.site.pagelinks(mainpage, total=30))
        titles = [link.title(with_section=False) for link in links]
        params = {
            'rvprop': 'ids|flags|timestamp|user|comment|content',
            'titles': '|'.join(titles)}
        if self.site.mw_version >= '1.32':
            params['rvslots'] = 'main'
        gen = api.PropertyGenerator(
            site=self.site,
            prop='revisions|info|categoryinfo|langlinks|templates',
            parameters=params)

        # An APIError is raised if set_maximum_items is not called.
        gen.set_maximum_items(-1)  # suppress use of "rvlimit" parameter
        # Force the generator into continuation mode
        gen.set_query_increment(5)

        count = 0
        for count, pagedata in enumerate(gen, start=1):
            self.assertIsInstance(pagedata, dict)
            if 'missing' in pagedata:
                self.assertNotIn('pageid', pagedata)  # pragma: no cover
            else:
                self.assertIn('pageid', pagedata)
        self.assertLength(links, count)

    def test_two_continuations_limited(self) -> None:
        """Test PropertyGenerator with many limited props and continuations."""
        total = 20
        increment = total // 4
        mainpage = self.get_mainpage()
        links = tuple(self.site.pagelinks(mainpage, total=total))
        titles = (link.title(with_section=False) for link in links)
        gen = api.PropertyGenerator(
            site=self.site,
            prop='info|categoryinfo|langlinks|templates',
            parameters={'titles': '|'.join(titles)})
        # Force the generator into continuation mode
        gen.set_query_increment(increment)

        count = 0
        for count, pagedata in enumerate(gen, start=1):
            self.assertIsInstance(pagedata, dict)
            if 'missing' in pagedata:
                self.assertNotIn('pageid', pagedata)  # pragma: no cover
            else:
                self.assertIn('pageid', pagedata)
        self.assertLength(links, count)
        self.assertGreaterEqual(total, count)
        # ensure we have enough continuations
        self.assertGreater(count, total // 2 + 1)


class TestDryQueryGeneratorNamespaceParam(TestCase):

    """Test setting of namespace param with ListGenerator.

    Generators with different characteristics are used. site._paraminfo
    is not always faithful to API, but serves the purpose here.
    """

    family = 'wikipedia'
    code = 'en'

    dry = True

    def setUp(self) -> None:
        """Set up test case."""
        super().setUp()
        self.site = self.get_site()
        self.site._paraminfo['query+querypage'] = {
            'prefix': 'qp',
            'limit': {'max': 10},
        }
        self.site._paraminfo['query+allpages'] = {
            'prefix': 'ap',
            'limit': {'max': 10},
            'namespace': {'multi': True}
        }
        self.site._paraminfo['query+alllinks'] = {
            'prefix': 'al',
            'limit': {'max': 10},
            'namespace': {'default': 0}
        }
        self.site._paraminfo['query+links'] = {
            'prefix': 'pl',
        }

    def test_namespace_for_module_with_no_limit(self) -> None:
        """Test PageGenerator set_namespace."""
        self.gen = api.PageGenerator(site=self.site,
                                     generator='links',
                                     parameters={'titles': 'test'})
        for namespace in (0, 1, None):
            with self.subTest(namespace=namespace), \
                    self.assertRaises(AssertionError):
                self.gen.set_namespace(namespace)

    @suppress_warnings(
        r'^set_namespace\(\) will be modified to raise TypeError*',
        FutureWarning)
    def test_namespace_param_is_not_settable(self) -> None:
        """Test ListGenerator support_namespace."""
        self.gen = api.ListGenerator(listaction='querypage', site=self.site)
        self.assertFalse(self.gen.support_namespace())
        self.assertFalse(self.gen.set_namespace([0, 1]))

    def test_namespace_none(self) -> None:
        """Test ListGenerator set_namespace with None."""
        self.gen = api.ListGenerator(listaction='alllinks', site=self.site)
        with self.assertRaises(TypeError):
            self.gen.set_namespace(None)

    def test_namespace_non_multi(self) -> None:
        """Test ListGenerator set_namespace when non multi."""
        self.gen = api.ListGenerator(listaction='alllinks', site=self.site)
        with self.assertRaises(TypeError):
            self.gen.set_namespace([0, 1])
        self.assertIsNone(self.gen.set_namespace(0))

    def test_namespace_multi(self) -> None:
        """Test ListGenerator set_namespace when multi."""
        self.gen = api.ListGenerator(listaction='allpages', site=self.site)
        self.assertTrue(self.gen.support_namespace())
        self.assertIsNone(self.gen.set_namespace([0, 1]))

    def test_namespace_resolve_failed(self) -> None:
        """Test ListGenerator set_namespace when resolve fails."""
        self.gen = api.ListGenerator(listaction='allpages', site=self.site)
        self.assertTrue(self.gen.support_namespace())
        with self.assertRaises(KeyError):
            self.gen.set_namespace(10000)


class TestDryListGenerator(TestCase):

    """Test ListGenerator."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def setUp(self) -> None:
        """Set up test case."""
        super().setUp()
        mysite = self.get_site()
        mysite._paraminfo['query+allpages'] = {
            'prefix': 'ap',
            'limit': {'max': 10},
            'namespace': {'multi': True}
        }
        self.gen = api.ListGenerator(listaction='allpages', site=mysite)

    def test_namespace_none(self) -> None:
        """Test ListGenerator set_namespace with None."""
        with self.assertRaises(TypeError):
            self.gen.set_namespace(None)

    def test_namespace_zero(self) -> None:
        """Test ListGenerator set_namespace with 0."""
        self.assertIsNone(self.gen.set_namespace(0))


class TestCachedRequest(DefaultSiteTestCase):

    """Test API Request caching.

    This test class does not use the forced test caching.
    """

    cached = False

    def test_normal_use(self) -> None:
        """Test the caching of CachedRequest with an ordinary request."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        # Run the cached query three times to ensure the
        # data returned is equal, and the last two have
        # the same cache time.
        params = {'action': 'query',
                  'prop': 'info',
                  'titles': mainpage.title(),
                  }
        req1 = api.CachedRequest(datetime.timedelta(minutes=10),
                                 site=mysite, parameters=params)
        data1 = req1.submit()
        req2 = api.CachedRequest(datetime.timedelta(minutes=10),
                                 site=mysite, parameters=params)
        data2 = req2.submit()
        req3 = api.CachedRequest(datetime.timedelta(minutes=10),
                                 site=mysite, parameters=params)
        data3 = req3.submit()
        self.assertEqual(data1, data2)
        self.assertEqual(data2, data3)
        self.assertIsNotNone(req2._cachetime)
        self.assertIsNotNone(req3._cachetime)
        self.assertEqual(req2._cachetime, req3._cachetime)

    def test_internals(self) -> None:
        """Test the caching of CachedRequest by faking a unique request."""
        mysite = self.get_site()
        # Run tests on a missing page unique to this test run so it can
        # not be cached the first request, but will be cached after.
        now = pywikibot.time.Timestamp.nowutc()
        params = {
            'action': 'query',
            'prop': 'info',
            'titles': 'TestCachedRequest_test_internals ' + str(now),
        }
        req = api.CachedRequest(datetime.timedelta(minutes=10),
                                site=mysite, parameters=params)
        rv = req._load_cache()
        self.assertFalse(rv)
        self.assertIsNone(req._data)
        self.assertIsNone(req._cachetime)

        data = req.submit()

        self.assertIsNotNone(req._data)
        self.assertIsNone(req._cachetime)

        rv = req._load_cache()

        self.assertTrue(rv)
        self.assertIsNotNone(req._data)
        self.assertIsNotNone(req._cachetime)
        self.assertIsNotNone(req._cachetime.tzinfo)
        self.assertEqual(req._cachetime.tzinfo, datetime.timezone.utc)
        self.assertGreater(req._cachetime, now)
        self.assertEqual(req._data, data)


class TestLazyLoginBase(TestCase):

    """Test that it tries to login when read API access is denied.

    Because there is no such family configured it creates an AutoFamily
    and BaseSite on it's own. It's testing against
    steward.wikimedia.org.

    These tests are split into two subclasses as only the first failed
    login behaves as expected. All subsequent logins will raise an
    APIError, making it impossible to test two scenarios with the same
    APISite object.
    """

    hostname = 'steward.wikimedia.org'

    @classmethod
    def setUpClass(cls) -> None:
        """Set up steward Family."""
        super().setUpClass()
        fam = pywikibot.family.AutoFamily(
            'steward', 'https://steward.wikimedia.org/w/api.php')
        cls.site = pywikibot.site.APISite('steward', fam)


class TestLazyLoginNotExistUsername(TestLazyLoginBase):

    """Test missing username."""

    # FIXME: due to limitations of LoginManager, it will ask the user
    # for a password even if the username does not exist, and even if
    # pywikibot is not connected to a tty. T100964

    def setUp(self) -> None:
        """Patch the LoginManager to avoid UI interaction."""
        super().setUp()
        self.orig_login_manager = pywikibot.login.ClientLoginManager
        pywikibot.login.ClientLoginManager = FakeLoginManager

    def tearDown(self) -> None:
        """Restore the original LoginManager."""
        pywikibot.login.ClientLoginManager = self.orig_login_manager
        super().tearDown()

    @patch.object(pywikibot, 'info')
    @patch.object(pywikibot, 'warning')
    def test_access_denied_notexist_username(self, warning, info) -> None:
        """Test the query with a username which does not exist."""
        self.site._username = 'Not registered username'
        req = api.Request(site=self.site, parameters={'action': 'query'})
        with self.assertRaises(NoUsernameError):
            req.submit()
        # FIXME: T100965
        with self.assertRaises(APIError):
            req.submit()
        warning.assert_called_with(
            'API error readapidenied: '
            'You need read permission to use this module.')
        self.assertIn(
            'Logging in to steward:steward as ', info.call_args[0][0])


class TestLazyLoginNoUsername(TestLazyLoginBase):

    """Test no username."""

    @patch.object(pywikibot, 'warning')
    @patch.object(pywikibot.config, 'usernames', defaultdict(dict))
    def test_access_denied_no_username(self, warning) -> None:
        """Test the query without a username."""
        self.site._username = None
        req = api.Request(site=self.site, parameters={'action': 'query'})
        with self.assertRaises(NoUsernameError):
            req.submit()
        # FIXME: T100965
        with self.assertRaises(APIError):
            req.submit()
        warning.assert_called_with(
            'API error readapidenied: '
            'You need read permission to use this module.')


class TestUrlEncoding(TestCase):

    """Test encode_url() function."""

    net = False

    def test_url_encoding_from_list(self) -> None:
        """Test moving 'token' parameters from a list to the end."""
        query = [('action', 'edit'), ('token', 'a'), ('supertoken', 'b'),
                 ('text', 'text')]
        expect = 'action=edit&text=text&token=a&supertoken=b'
        result = api.encode_url(query)
        self.assertEqual(result, expect)
        self.assertIsInstance(result, str)

    def test_url_encoding_from_dict(self) -> None:
        """Test moving 'token' parameters from a dict to the end."""
        # do not add other keys because dictionary is not deterministic
        query = {'supertoken': 'b', 'text': 'text'}
        expect = 'text=text&supertoken=b'
        result = api.encode_url(query)
        self.assertEqual(result, expect)
        self.assertIsInstance(result, str)

    def test_url_encoding_from_unicode(self) -> None:
        """Test encoding unicode values."""
        query = {'token': 'токен'}
        expect = 'token=%D1%82%D0%BE%D0%BA%D0%B5%D0%BD'
        result = api.encode_url(query)
        self.assertEqual(result, expect)
        self.assertIsInstance(result, str)

    def test_url_encoding_from_str(self) -> None:
        """Test encoding str values."""
        query = {'token': 'test\xe2\x80\x94test'}
        expect = 'token=test%C3%A2%C2%80%C2%94test'
        result = api.encode_url(query)
        self.assertEqual(result, expect)
        self.assertIsInstance(result, str)

    def test_moving_special_tokens(self) -> None:
        """Test moving wpEditToken to the very end."""
        query = {'wpEditToken': 'c', 'token': 'b', 'text': 'a'}
        expect = 'text=a&token=b&wpEditToken=c'
        result = api.encode_url(query)
        self.assertEqual(result, expect)
        self.assertIsInstance(result, str)


class DummyThrottle(Throttle):

    """Dummy Throttle class."""

    def lag(self, lag) -> NoReturn:
        """Override lag method, save the lag value and exit the api loop."""
        self._lagvalue = lag  # save the lag value
        raise SystemExit  # exit the api loop


class TestLagpattern(DefaultSiteTestCase):

    """Test the lag pattern."""

    cached = False

    def test_valid_lagpattern(self) -> None:
        """Test whether api lagpattern is valid."""
        mysite = self.get_site()
        if ('dbrepllag' not in mysite.siteinfo
                or mysite.siteinfo['dbrepllag'][0]['lag'] == -1):
            self.skipTest(
                f'{mysite} is not running on a replicated database cluster.'
            )
        mythrottle = DummyThrottle(mysite)
        mysite._throttle = mythrottle
        params = {'action': 'query',
                  'titles': self.get_mainpage().title(),
                  'maxlag': -1}
        req = api.Request(site=mysite, parameters=params)
        try:
            req.submit()
        except SystemExit:
            pass  # expected exception from DummyThrottle instance
        except APIError:  # pragma: no cover
            pywikibot.warning(
                'Wrong api lagpattern regex, cannot retrieve lag value')
            raise
        self.assertIsInstance(mythrottle._lagvalue, (int, float))
        self.assertGreaterEqual(mythrottle._lagvalue, 0)
        self.assertIsInstance(mythrottle.retry_after, int)
        self.assertGreaterEqual(mythrottle.retry_after, 0)

    def test_individual_patterns(self) -> None:
        """Test api lagpattern with example patterns."""
        patterns = {
            'Waiting for 10.64.32.115: 0.14024019241333 seconds lagged':
                0.14024019241333,
            'Waiting for hostname: 5 seconds lagged': 5,
            'Waiting for 127.0.0.1: 1.7 seconds lagged': 1.7
        }
        for info, time in patterns.items():
            lag = api._requests.lagpattern.search(info)
            self.assertIsNotNone(lag)
            self.assertEqual(float(lag['lag']), time)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
