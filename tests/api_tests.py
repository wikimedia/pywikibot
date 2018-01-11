# -*- coding: utf-8 -*-
"""API test module."""
#
# (C) Pywikibot team, 2007-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import datetime
import types

import pywikibot.data.api as api
import pywikibot.family
import pywikibot.login
import pywikibot.page
import pywikibot.site

from pywikibot.throttle import Throttle
from pywikibot.tools import (
    MediaWikiVersion,
    PY2,
    UnicodeType,
)

from tests.aspects import (
    unittest,
    TestCase,
    DefaultSiteTestCase,
    DefaultDrySiteTestCase,
)
from tests.utils import allowed_failure, FakeLoginManager, PatchedHttp

if not PY2:
    from urllib.parse import unquote_to_bytes
else:
    from urllib import unquote_plus as unquote_to_bytes


class TestAPIMWException(DefaultSiteTestCase):

    """Test raising an APIMWException."""

    data = {'error': {'code': 'internal_api_error_fake',
                      'info': 'Fake error message'},
            'servedby': 'unittest',
            }

    def _dummy_request(self, **kwargs):
        self.assertIn('body', kwargs)
        self.assertIn('uri', kwargs)
        self.assertIn('site', kwargs)
        if kwargs['body'] is None:
            # use uri and remove script path
            parameters = kwargs['uri']
            prefix = kwargs['site'].scriptpath() + '/api.php?'
            self.assertEqual(prefix, parameters[:len(prefix)])
            parameters = parameters[len(prefix):]
        else:
            parameters = kwargs['body']
        parameters = parameters.encode('ascii')  # it should be bytes anyway
        # Extract parameter data from the body, it's ugly but allows us
        # to verify that we actually test the right request
        parameters = [p.split(b'=', 1) for p in parameters.split(b'&')]
        keys = [p[0].decode('ascii') for p in parameters]
        values = [unquote_to_bytes(p[1]) for p in parameters]
        values = [v.decode(kwargs['site'].encoding()) for v in values]
        values = [v.replace('+', ' ') for v in values]
        values = [set(v.split('|')) for v in values]
        parameters = dict(zip(keys, values))

        if 'fake' not in parameters:
            return False  # do an actual request
        if self.assert_parameters:
            for param, value in self.assert_parameters.items():
                self.assertIn(param, parameters)
                if value is not None:
                    if isinstance(value, UnicodeType):
                        value = value.split('|')
                    self.assertLessEqual(set(value), parameters[param])
        return self.data

    def test_API_error(self):
        """Test a static request."""
        req = api.Request(site=self.site, parameters={'action': 'query',
                                                      'fake': True})
        with PatchedHttp(api, self.data):
            self.assertRaises(api.APIMWException, req.submit)

    def test_API_error_encoding_ASCII(self):
        """Test a Page instance as parameter using ASCII chars."""
        page = pywikibot.page.Page(self.site, 'ASCII')
        req = api.Request(site=self.site, parameters={'action': 'query',
                                                      'fake': True,
                                                      'titles': page})
        self.assert_parameters = {'fake': ''}
        with PatchedHttp(api, self._dummy_request):
            self.assertRaises(api.APIMWException, req.submit)

    def test_API_error_encoding_Unicode(self):
        """Test a Page instance as parameter using non-ASCII chars."""
        page = pywikibot.page.Page(self.site, 'Ümlä  üt')
        req = api.Request(site=self.site, parameters={'action': 'query',
                                                      'fake': True,
                                                      'titles': page})
        self.assert_parameters = {'fake': ''}
        with PatchedHttp(api, self._dummy_request):
            self.assertRaises(api.APIMWException, req.submit)


class TestApiFunctions(DefaultSiteTestCase):

    """API Request object test class."""

    def testObjectCreation(self):
        """Test api.Request() constructor with implicit site creation."""
        req = api.Request(parameters={'action': 'test', 'foo': '',
                                      'bar': 'test'})
        self.assertTrue(req)
        self.assertEqual(req.site, self.get_site())


class TestDryApiFunctions(DefaultDrySiteTestCase):

    """API Request object test class."""

    def testObjectCreation(self):
        """Test api.Request() constructor."""
        mysite = self.get_site()
        req = api.Request(site=mysite, parameters={'action': 'test', 'foo': '',
                                                   'bar': 'test'})
        self.assertTrue(req)
        self.assertEqual(req.site, mysite)
        self.assertIn("foo", req._params)
        self.assertEqual(req["bar"], ["test"])
        # test item assignment
        req["one"] = "1"
        self.assertEqual(req._params['one'], ["1"])
        # test compliance with dict interface
        # req.keys() should contain "action", "foo", "bar", "one"
        self.assertEqual(len(req.keys()), 4)
        self.assertIn("test", req._encoded_items().values())
        for item in req.items():
            self.assertEqual(len(item), 2, item)

    def test_mixed_mode(self):
        """Test if parameters is used with kwargs."""
        req1 = api.Request(site=self.site, action='test', parameters='foo')
        self.assertIn('parameters', req1._params)

        req2 = api.Request(site=self.site, parameters={'action': 'test',
                                                       'parameters': 'foo'})
        self.assertEqual(req2['parameters'], ['foo'])
        self.assertEqual(req1._params, req2._params)


class TestParamInfo(DefaultSiteTestCase):

    """Test ParamInfo."""

    def test_init(self):
        """Test common initialization."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertEqual(len(pi), 0)
        pi._init()

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)
        if MediaWikiVersion(self.site.version()) >= MediaWikiVersion("1.12"):
            self.assertEqual(len(pi),
                             len(pi.preloaded_modules))

        self.assertIn('info', pi.query_modules)
        self.assertIn('login', pi._action_modules)

    def test_init_query_first(self):
        """Test init where it first adds query and then main."""
        def patched_generate_submodules(modules):
            # Change the query such that query is handled before main
            modules = set(modules)
            if 'main' in modules:
                assert 'query' in modules
                modules.discard('main')
                modules = list(modules) + ['main']
            else:
                assert 'query' not in modules
            original_generate_submodules(modules)
        pi = api.ParamInfo(self.site, set(['query', 'main']))
        self.assertEqual(len(pi), 0)
        original_generate_submodules = pi._generate_submodules
        pi._generate_submodules = patched_generate_submodules
        pi._init()
        self.assertIn('main', pi._paraminfo)
        self.assertIn('query', pi._paraminfo)

    def test_init_pageset(self):
        """Test initializing with only the pageset."""
        site = self.get_site()
        self.assertNotIn('query', api.ParamInfo.init_modules)
        pi = api.ParamInfo(site, set(['pageset']))
        self.assertNotIn('query', api.ParamInfo.init_modules)
        self.assertEqual(len(pi), 0)
        pi._init()

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)
        self.assertIn('pageset', pi._paraminfo)

        if MediaWikiVersion(self.site.version()) < MediaWikiVersion("1.12"):
            return

        if 'query' in pi.preloaded_modules:
            self.assertIn('query', pi._paraminfo)
            self.assertEqual(len(pi), 4)
        else:
            self.assertNotIn('query', pi._paraminfo)
            self.assertEqual(len(pi), 3)

        self.assertEqual(len(pi),
                         len(pi.preloaded_modules))

        if MediaWikiVersion(site.version()) >= MediaWikiVersion("1.21"):
            # 'generator' was added to 'pageset' in 1.21
            generators_param = pi.parameter('pageset', 'generator')
            self.assertGreater(len(generators_param['type']), 1)

    def test_generators(self):
        """Test requesting the generator parameter."""
        site = self.get_site()
        pi = api.ParamInfo(site, set(['pageset', 'query']))
        self.assertEqual(len(pi), 0)
        pi._init()

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)
        self.assertIn('pageset', pi._paraminfo)
        self.assertIn('query', pi._paraminfo)

        if MediaWikiVersion(site.version()) >= MediaWikiVersion("1.21"):
            # 'generator' was added to 'pageset' in 1.21
            pageset_generators_param = pi.parameter('pageset', 'generator')
            query_generators_param = pi.parameter('query', 'generator')

            self.assertEqual(pageset_generators_param, query_generators_param)

    def test_with_module_info(self):
        """Test requesting the module info."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertEqual(len(pi), 0)
        pi.fetch(['info'])
        self.assertIn('query+info', pi._paraminfo)

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)
        if MediaWikiVersion(self.site.version()) >= MediaWikiVersion("1.12"):
            self.assertEqual(len(pi),
                             1 + len(pi.preloaded_modules))

        self.assertEqual(pi['info']['prefix'], 'in')

        param = pi.parameter('info', 'prop')
        self.assertIsInstance(param, dict)

        self.assertEqual(param['name'], 'prop')
        self.assertNotIn('deprecated', param)

        self.assertIsInstance(param['type'], list)

        if MediaWikiVersion(self.site.version()) < MediaWikiVersion("1.12"):
            return

        self.assertIn('protection', param['type'])

    def test_with_module_revisions(self):
        """Test requesting the module revisions."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertEqual(len(pi), 0)
        pi.fetch(['revisions'])
        self.assertIn('query+revisions', pi._paraminfo)

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)
        if MediaWikiVersion(self.site.version()) >= MediaWikiVersion("1.12"):
            self.assertEqual(len(pi),
                             1 + len(pi.preloaded_modules))

        self.assertEqual(pi['revisions']['prefix'], 'rv')

        param = pi.parameter('revisions', 'prop')
        self.assertIsInstance(param, dict)

        self.assertEqual(param['name'], 'prop')
        self.assertNotIn('deprecated', param)

        self.assertIsInstance(param['type'], list)

        if MediaWikiVersion(self.site.version()) < MediaWikiVersion("1.12"):
            return

        self.assertIn('user', param['type'])

    def test_multiple_modules(self):
        """Test requesting multiple modules in one fetch."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertEqual(len(pi), 0)
        pi.fetch(['info', 'revisions'])
        self.assertIn('query+info', pi._paraminfo)
        self.assertIn('query+revisions', pi._paraminfo)

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)

        if MediaWikiVersion(self.site.version()) < MediaWikiVersion("1.12"):
            return

        self.assertEqual(len(pi),
                         2 + len(pi.preloaded_modules))

    def test_with_invalid_module(self):
        """Test requesting different kind of invalid modules."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertEqual(len(pi), 0)
        pi.fetch('foobar')
        self.assertNotIn('foobar', pi._paraminfo)

        self.assertRaises(KeyError, pi.__getitem__, 'foobar')
        self.assertRaises(KeyError, pi.__getitem__, 'foobar+foobar')

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)

        if MediaWikiVersion(self.site.version()) < MediaWikiVersion("1.12"):
            return

        self.assertEqual(len(pi),
                         len(pi.preloaded_modules))

    def test_submodules(self):
        """Test another module apart from query having submodules."""
        pi = api.ParamInfo(self.site)
        self.assertFalse(pi._modules)
        pi.fetch(['query'])
        self.assertIn('query', pi._modules)
        self.assertIsInstance(pi._modules['query'], frozenset)
        self.assertIn('revisions', pi._modules['query'])
        self.assertEqual(pi.submodules('query'), pi.query_modules)
        for mod in pi.submodules('query', True):
            self.assertEqual(mod[:6], 'query+')
            self.assertEqual(mod[6:], pi[mod]['name'])
            self.assertEqual(mod, pi[mod]['path'])

        self.assertRaises(KeyError, pi.__getitem__, 'query+foobar')
        self.assertRaises(KeyError, pi.submodules, 'edit')

    def test_query_modules_with_limits(self):
        """Test query_modules_with_limits property."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertIn('revisions', pi.query_modules_with_limits)
        self.assertNotIn('info', pi.query_modules_with_limits)

    def test_modules(self):
        """Test v1.8 modules exist."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertIn('revisions', pi.modules)
        self.assertIn('help', pi.modules)
        self.assertIn('allpages', pi.modules)
        for mod in pi.modules:
            self.assertNotIn('+', mod)

    def test_module_paths(self):
        """Test module paths use the complete paths."""
        pi = api.ParamInfo(self.site)
        self.assertIn('help', pi.module_paths)
        self.assertNotIn('revisions', pi.module_paths)
        self.assertIn('query+revisions', pi.module_paths)
        self.assertNotIn('allpages', pi.module_paths)
        self.assertIn('query+allpages', pi.module_paths)

    def test_prefixes(self):
        """Test v1.8 module prefixes exist."""
        site = self.get_site()
        pi = api.ParamInfo(site)
        self.assertIn('revisions', pi.prefixes)
        self.assertIn('login', pi.prefixes)
        self.assertIn('allpages', pi.prefixes)

    def test_prefix_map(self):
        """Test module prefixes use the path."""
        pi = api.ParamInfo(self.site)
        self.assertIn('query+revisions', pi.prefix_map)
        self.assertIn('login', pi.prefix_map)
        self.assertIn('query+allpages', pi.prefix_map)
        for mod in pi.prefix_map:
            self.assertEqual(mod, pi[mod]['path'])

    def test_attributes(self):
        """Test attributes method."""
        pi = api.ParamInfo(self.site)
        attributes = pi.attributes('mustbeposted')
        self.assertIn('edit', attributes)
        for mod, value in attributes.items():
            self.assertEqual(mod, pi[mod]['path'])
            self.assertEqual(value, '')

    def test_old_mode(self):
        """Test the old mode explicitly."""
        site = self.get_site()
        pi = api.ParamInfo(site, modules_only_mode=False)
        pi.fetch(['info'])
        self.assertIn('query+info', pi._paraminfo)

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)

        if MediaWikiVersion(self.site.version()) >= MediaWikiVersion("1.12"):
            self.assertEqual(len(pi),
                             1 + len(pi.preloaded_modules))

        self.assertIn('revisions', pi.prefixes)

    def test_new_mode(self):
        """Test the new modules-only mode explicitly."""
        site = self.get_site()
        if MediaWikiVersion(site.version()) < MediaWikiVersion('1.25wmf4'):
            raise unittest.SkipTest(
                "version %s doesn't support the new paraminfo api"
                % site.version())
        pi = api.ParamInfo(site, modules_only_mode=True)
        pi.fetch(['info'])
        self.assertIn('query+info', pi._paraminfo)

        self.assertIn('main', pi._paraminfo)
        self.assertIn('paraminfo', pi._paraminfo)

        self.assertEqual(len(pi),
                         1 + len(pi.preloaded_modules))

        self.assertIn('revisions', pi.prefixes)


class TestOtherSubmodule(TestCase):

    """Test handling multiple different modules having submodules."""

    family = 'mediawiki'
    code = 'mediawiki'

    def test_other_submodule(self):
        """Test another module apart from query having submodules."""
        pi = api.ParamInfo(self.site)
        self.assertFalse(pi._modules)
        pi.fetch(['query'])
        self.assertNotIn('flow', pi._modules)
        pi.fetch(['flow'])
        self.assertIn('flow', pi._modules)
        other_modules = set()
        for modules in pi._modules.values():
            self.assertIsInstance(modules, frozenset)
            other_modules |= modules

        other_modules -= pi.action_modules
        other_modules -= pi.query_modules
        self.assertLessEqual(other_modules & pi.submodules('flow'),
                             pi.submodules('flow'))
        self.assertFalse(other_modules & pi.modules)


class TestParaminfoModules(DefaultSiteTestCase):

    """Test loading all paraminfo modules."""

    vcr = True

    def test_action_modules(self):
        """Test loading all action modules."""
        self.site._paraminfo.fetch(self.site._paraminfo.action_modules)

    def test_query_modules(self):
        """Test loading all query modules."""
        self.site._paraminfo.fetch(self.site._paraminfo.query_modules)


class TestOptionSet(TestCase):

    """OptionSet class test class."""

    family = 'wikipedia'
    code = 'en'

    def test_non_lazy_load(self):
        """Test OptionSet with initialised site."""
        options = api.OptionSet(self.get_site(), 'recentchanges', 'show')
        self.assertRaises(KeyError, options.__setitem__, 'invalid_name', True)
        self.assertRaises(ValueError, options.__setitem__, 'anon', 'invalid_value')
        options['anon'] = True
        self.assertCountEqual(['anon'], options._enabled)
        self.assertEqual(set(), options._disabled)
        self.assertEqual(1, len(options))
        self.assertEqual(['anon'], list(options))
        self.assertEqual(['anon'], list(options.api_iter()))
        options['bot'] = False
        self.assertCountEqual(['anon'], options._enabled)
        self.assertCountEqual(['bot'], options._disabled)
        self.assertEqual(2, len(options))
        self.assertEqual(['anon', 'bot'], list(options))
        self.assertEqual(['anon', '!bot'], list(options.api_iter()))
        options.clear()
        self.assertEqual(set(), options._enabled)
        self.assertEqual(set(), options._disabled)
        self.assertEqual(0, len(options))
        self.assertEqual([], list(options))
        self.assertEqual([], list(options.api_iter()))

    def test_lazy_load(self):
        """Test OptionSet with delayed site initialisation."""
        options = api.OptionSet()
        options['invalid_name'] = True
        options['anon'] = True
        self.assertIn('invalid_name', options._enabled)
        self.assertEqual(2, len(options))
        self.assertRaises(KeyError, options._set_site, self.get_site(),
                          'recentchanges', 'show')
        self.assertEqual(2, len(options))
        options._set_site(self.get_site(), 'recentchanges', 'show', True)
        self.assertEqual(1, len(options))
        self.assertRaises(TypeError, options._set_site, self.get_site(),
                          'recentchanges', 'show')


class TestDryOptionSet(DefaultDrySiteTestCase):

    """OptionSet class test class."""

    def test_mutable_mapping(self):
        """Test keys, values and items from MutableMapping."""
        options = api.OptionSet()
        options['a'] = True
        options['b'] = False
        options['c'] = None
        self.assertCountEqual(['a', 'b'], list(options.keys()))
        self.assertCountEqual([True, False], list(options.values()))
        self.assertEqual(set(), set(options.values()) - set([True, False]))
        self.assertCountEqual([('a', True), ('b', False)], list(options.items()))


class TestDryPageGenerator(TestCase):

    """Dry API PageGenerator object test class."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    # api.py sorts 'pages' using the string key, which is not a
    # numeric comparison.
    titles = ("Broadcaster (definition)", "Wiktionary", "Broadcaster.com",
              "Wikipedia:Disambiguation")

    def setUp(self):
        """Set up test case."""
        super(TestDryPageGenerator, self).setUp()
        mysite = self.get_site()
        self.gen = api.PageGenerator(site=mysite,
                                     generator="links",
                                     titles="User:R'n'B")
        # following test data is copied from an actual api.php response,
        # but that query no longer matches this dataset.
        # http://en.wikipedia.org/w/api.php?action=query&generator=links&titles=User:R%27n%27B
        self.gen.request.submit = types.MethodType(lambda self: {
            "query": {"pages": {"296589": {"pageid": 296589,
                                           "ns": 0,
                                           "title": "Broadcaster.com"
                                           },
                                "13918157": {"pageid": 13918157,
                                             "ns": 0,
                                             "title": "Broadcaster (definition)"
                                             },
                                "156658": {"pageid": 156658,
                                           "ns": 0,
                                           "title": "Wiktionary"
                                           },
                                "47757": {"pageid": 47757,
                                          "ns": 4,
                                          "title": "Wikipedia:Disambiguation"
                                          }
                                }
                      }
        }, self.gen.request)

        # On a dry site, the namespace objects only have canonical names.
        # Add custom_name for this site namespace, to match the live site.
        if 'Wikipedia' not in self.site.namespaces:
            self.site.namespaces[4].custom_name = 'Wikipedia'
            self.site.namespaces._namespace_names['wikipedia'] = self.site.namespaces[4]

    def test_results(self):
        """Test that PageGenerator yields pages with expected attributes."""
        self.assertPagelistTitles(self.gen, self.titles)

    def test_initial_limit(self):
        """Test the default limit."""
        self.assertEqual(self.gen.limit, None)  # limit is initally None

    def test_set_limit_as_number(self):
        """Test setting the limit using an int."""
        for i in range(-2, 4):
            self.gen.set_maximum_items(i)
            self.assertEqual(self.gen.limit, i)

    def test_set_limit_as_string(self):
        """Test setting the limit using an int cast into a string."""
        for i in range(-2, 4):
            self.gen.set_maximum_items(str(i))
            self.assertEqual(self.gen.limit, i)

    def test_set_limit_not_number(self):
        """Test setting the limit to not a number."""
        with self.assertRaisesRegex(
                ValueError,
                r"invalid literal for int\(\) with base 10: 'test'"):
            self.gen.set_maximum_items('test')

    def test_limit_equal_total(self):
        """Test that PageGenerator yields the requested amount of pages."""
        self.gen.set_maximum_items(4)
        self.assertPagelistTitles(self.gen, self.titles)

    def test_limit_one(self):
        """Test that PageGenerator yields the requested amount of pages."""
        self.gen.set_maximum_items(1)
        self.assertPagelistTitles(self.gen, self.titles[0:1])

    def test_limit_zero(self):
        """Test that a limit of zero is the same as limit None."""
        self.gen.set_maximum_items(0)
        self.assertPagelistTitles(self.gen, self.titles)

    def test_limit_omit(self):
        """Test that limit omitted is the same as limit None."""
        self.gen.set_maximum_items(-1)
        self.assertPagelistTitles(self.gen, self.titles)

    def test_namespace(self):
        """Test PageGenerator set_namespace."""
        self.assertRaises(AssertionError, self.gen.set_namespace, 0)
        self.assertRaises(AssertionError, self.gen.set_namespace, 1)
        self.assertRaises(AssertionError, self.gen.set_namespace, None)


class TestPropertyGenerator(TestCase):

    """API PropertyGenerator object test class."""

    family = 'wikipedia'
    code = 'en'

    def test_info(self):
        """Test PropertyGenerator with prop 'info'."""
        mainpage = self.get_mainpage()
        links = list(self.site.pagelinks(mainpage, total=10))
        titles = [l.title(withSection=False)
                  for l in links]
        gen = api.PropertyGenerator(site=self.site,
                                    prop="info",
                                    titles='|'.join(titles))

        count = 0
        for pagedata in gen:
            self.assertIsInstance(pagedata, dict)
            self.assertIn('pageid', pagedata)
            self.assertIn('lastrevid', pagedata)
            count += 1
        self.assertEqual(len(links), count)

    def test_one_continuation(self):
        """Test PropertyGenerator with prop 'revisions'."""
        mainpage = self.get_mainpage()
        links = list(self.site.pagelinks(mainpage, total=10))
        titles = [l.title(withSection=False)
                  for l in links]
        gen = api.PropertyGenerator(site=self.site,
                                    prop="revisions",
                                    titles='|'.join(titles))
        gen.set_maximum_items(-1)  # suppress use of "rvlimit" parameter

        count = 0
        for pagedata in gen:
            self.assertIsInstance(pagedata, dict)
            self.assertIn('pageid', pagedata)
            self.assertIn('revisions', pagedata)
            self.assertIn('revid', pagedata['revisions'][0])
            count += 1
        self.assertEqual(len(links), count)

    def test_two_continuations(self):
        """Test PropertyGenerator with prop 'revisions' and 'coordinates'."""
        mainpage = self.get_mainpage()
        links = list(self.site.pagelinks(mainpage, total=10))
        titles = [l.title(withSection=False)
                  for l in links]
        gen = api.PropertyGenerator(site=self.site,
                                    prop="revisions|coordinates",
                                    titles='|'.join(titles))
        gen.set_maximum_items(-1)  # suppress use of "rvlimit" parameter

        count = 0
        for pagedata in gen:
            self.assertIsInstance(pagedata, dict)
            self.assertIn('pageid', pagedata)
            self.assertIn('revisions', pagedata)
            self.assertIn('revid', pagedata['revisions'][0])
            count += 1
        self.assertEqual(len(links), count)

    @allowed_failure
    def test_many_continuations_limited(self):
        """Test PropertyGenerator with many limited props."""
        mainpage = self.get_mainpage()
        links = list(self.site.pagelinks(mainpage, total=30))
        titles = [l.title(withSection=False)
                  for l in links]
        gen = api.PropertyGenerator(site=self.site,
                                    prop="revisions|info|categoryinfo|langlinks|templates",
                                    rvprop="ids|flags|timestamp|user|comment|content",
                                    titles='|'.join(titles))

        # An APIError is raised if set_maximum_items is not called.
        gen.set_maximum_items(-1)  # suppress use of "rvlimit" parameter
        # Force the generator into continuation mode
        gen.set_query_increment(5)

        count = 0
        for pagedata in gen:
            self.assertIsInstance(pagedata, dict)
            self.assertIn('pageid', pagedata)
            count += 1
        self.assertEqual(len(links), count)
        # FIXME: AssertionError: 30 != 6150

    @allowed_failure
    def test_two_continuations_limited(self):
        """Test PropertyGenerator with many limited props and continuations."""
        # FIXME: test fails
        mainpage = self.get_mainpage()
        links = list(self.site.pagelinks(mainpage, total=30))
        titles = [l.title(withSection=False)
                  for l in links]
        gen = api.PropertyGenerator(site=self.site,
                                    prop="info|categoryinfo|langlinks|templates",
                                    titles='|'.join(titles))
        # Force the generator into continuation mode
        gen.set_query_increment(5)

        count = 0
        for pagedata in gen:
            self.assertIsInstance(pagedata, dict)
            self.assertIn('pageid', pagedata)
            count += 1
        self.assertEqual(len(links), count)
        # FIXME: AssertionError: 30 != 11550

    # FIXME: test disabled as it takes longer than 10 minutes
    def _test_two_continuations_limited_long_test(self):
        """Long duration test, with total & step that are a real scenario."""
        mainpage = self.get_mainpage()
        links = list(mainpage.backlinks(total=300))
        titles = [l.title(withSection=False)
                  for l in links]
        gen = api.PropertyGenerator(site=self.site,
                                    prop="info|categoryinfo|langlinks|templates",
                                    titles='|'.join(titles))
        # Force the generator into continuation mode
        gen.set_query_increment(50)

        count = 0
        for pagedata in gen:
            self.assertIsInstance(pagedata, dict)
            self.assertIn('pageid', pagedata)
            count += 1
        self.assertEqual(len(links), count)


class TestDryListGenerator(TestCase):

    """Test ListGenerator."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def setUp(self):
        """Set up test case."""
        super(TestDryListGenerator, self).setUp()
        mysite = self.get_site()
        mysite._paraminfo['query+allpages'] = {
            'prefix': 'ap',
            'limit': {'max': 10},
            'namespace': {'multi': True}
        }
        mysite._paraminfo.query_modules_with_limits = set(['allpages'])
        self.gen = api.ListGenerator(listaction="allpages", site=mysite)

    def test_namespace_none(self):
        """Test ListGenerator set_namespace with None."""
        self.assertRaises(TypeError, self.gen.set_namespace, None)

    def test_namespace_zero(self):
        """Test ListGenerator set_namespace with 0."""
        self.gen.set_namespace(0)


class TestCachedRequest(DefaultSiteTestCase):

    """Test API Request caching.

    This test class does not use the forced test caching.
    This class contains test cases with requests which are mocked with VCR.
    """

    cached = False
    vcr = True

    def test_normal_use(self):
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


class TestCachedRequestNonVCR(DefaultSiteTestCase):

    """Test API Request caching (live without VCR).

    This test class does not use the forced test caching.
    This class contains test cases with requests which can't be mocked
    with VCR.
    """

    cached = False

    def test_internals(self):
        """Test the caching of CachedRequest by faking a unique request."""
        mysite = self.get_site()
        # Run tests on a missing page unique to this test run so it can
        # not be cached the first request, but will be cached after.
        now = datetime.datetime.now()
        params = {'action': 'query',
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
        self.assertGreater(req._cachetime, now)
        self.assertEqual(req._data, data)


class TestLazyLoginBase(TestCase):

    """
    Test that it tries to login when read API access is denied.

    Because there is no such family configured it creates an AutoFamily and
    BaseSite on it's own. It's testing against steward.wikimedia.org.

    These tests are split into two subclasses as only the first failed login
    behaves as expected. All subsequent logins will raise an APIError, making
    it impossible to test two scenarios with the same APISite object.
    """

    hostname = 'steward.wikimedia.org'

    @classmethod
    def setUpClass(cls):
        """Set up steward Family."""
        super(TestLazyLoginBase, cls).setUpClass()
        fam = pywikibot.family.AutoFamily(
            'steward', 'https://steward.wikimedia.org/w/api.php')
        cls.site = pywikibot.site.APISite('steward', fam)


class TestLazyLoginNotExistUsername(TestLazyLoginBase):

    """Test missing username."""

    # FIXME: due to limitations of LoginManager, it will ask the user
    # for a password even if the username does not exist, and even if
    # pywikibot is not connected to a tty. T100964

    def setUp(self):
        """Patch the LoginManager to avoid UI interaction."""
        super(TestLazyLoginNotExistUsername, self).setUp()
        self.orig_login_manager = pywikibot.data.api.LoginManager
        pywikibot.data.api.LoginManager = FakeLoginManager

    def tearDown(self):
        """Restore the original LoginManager."""
        pywikibot.data.api.LoginManager = self.orig_login_manager
        super(TestLazyLoginNotExistUsername, self).tearDown()

    def test_access_denied_notexist_username(self):
        """Test the query with a username which does not exist."""
        self.site._username = ['Not registered username', None]
        req = api.Request(site=self.site, parameters={'action': 'query'})
        self.assertRaises(pywikibot.NoUsername, req.submit)
        # FIXME: T100965
        self.assertRaises(api.APIError, req.submit)


class TestLazyLoginNoUsername(TestLazyLoginBase):

    """Test no username."""

    def test_access_denied_no_username(self):
        """Test the query without a username."""
        self.site._username = [None, None]

        # FIXME: The following prevents LoginManager
        # from loading the username from the config when the site
        # username is None. i.e. site.login(user=None) means load
        # username from the configuration.
        if 'steward' in pywikibot.config.usernames:
            del pywikibot.config.usernames['steward']

        req = api.Request(site=self.site, parameters={'action': 'query'})
        self.assertRaises(pywikibot.NoUsername, req.submit)
        # FIXME: T100965
        self.assertRaises(api.APIError, req.submit)


class TestBadTokenRecovery(TestCase):

    """Test that the request recovers from bad tokens."""

    family = 'wikipedia'
    code = 'test'

    write = True

    def test_bad_token(self):
        """Test the bad token recovery by corrupting the cache."""
        site = self.get_site()
        site.tokens._tokens.setdefault(site.user(), {})['edit'] = 'INVALID'
        page = pywikibot.Page(site, 'Pywikibot bad token test')
        page.text = ('This page is testing whether pywikibot-core rerequests '
                     'a token when a badtoken error was received.')
        page.save(summary='Bad token test')


class TestUrlEncoding(TestCase):

    """Test encode_url() function."""

    net = False

    def test_url_encoding_from_list(self):
        """Test moving 'token' parameters from a list to the end."""
        query = [('action', 'edit'), ('token', 'a'), ('supertoken', 'b'),
                 ('text', 'text')]
        expect = 'action=edit&text=text&token=a&supertoken=b'
        result = api.encode_url(query)
        self.assertEqual(result, expect)
        self.assertIsInstance(result, str)

    def test_url_encoding_from_dict(self):
        """Test moving 'token' parameters from a dict to the end."""
        # do not add other keys because dictionary is not deterministic
        query = {'supertoken': 'b', 'text': 'text'}
        expect = 'text=text&supertoken=b'
        result = api.encode_url(query)
        self.assertEqual(result, expect)
        self.assertIsInstance(result, str)

    def test_url_encoding_from_unicode(self):
        """Test encoding unicode values."""
        query = {'token': 'токен'}
        expect = 'token=%D1%82%D0%BE%D0%BA%D0%B5%D0%BD'
        result = api.encode_url(query)
        self.assertEqual(result, expect)
        self.assertIsInstance(result, str)

    def test_url_encoding_from_basestring(self):
        """Test encoding basestring values."""
        if PY2:
            query = {'token': str('test\xe2\x80\x94test'.encode('utf-8'))}
        else:
            query = {'token': 'test\xe2\x80\x94test'}
        expect = str('token=test%C3%A2%C2%80%C2%94test')
        result = api.encode_url(query)
        self.assertEqual(result, expect)
        self.assertIsInstance(result, str)

    def test_moving_special_tokens(self):
        """Test moving wpEditToken to the very end."""
        query = {'wpEditToken': 'c', 'token': 'b', 'text': 'a'}
        expect = 'text=a&token=b&wpEditToken=c'
        result = api.encode_url(query)
        self.assertEqual(result, expect)
        self.assertIsInstance(result, str)


class DummyThrottle(Throttle):

    """Dummy Throttle class."""

    def lag(self, lag):
        """Override lag method, save the lag value and exit the api loop."""
        self._lagvalue = lag  # save the lag value
        raise SystemExit  # exit the api loop


class TestLagpattern(DefaultSiteTestCase):

    """Test the lag pattern."""

    cached = False

    def test_valid_lagpattern(self):
        """Test whether api.lagpattern is valid."""
        mysite = self.get_site()
        if mysite.siteinfo['dbrepllag'][0]['lag'] == -1:
            raise unittest.SkipTest(
                '{0} is not running on a replicated database cluster.'
                .format(mysite)
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
        except api.APIError as e:
            pywikibot.warning(
                'Wrong api.lagpattern regex, cannot retrieve lag value')
            raise e
        value = mysite.throttle._lagvalue
        self.assertIsInstance(value, int)
        self.assertGreaterEqual(value, 0)

    def test_individual_patterns(self):
        """Test api.lagpattern with example patterns."""
        patterns = {
            'Waiting for 10.64.32.115: 0.14024019241333 seconds lagged': 0,
            'Waiting for hostname: 5 seconds lagged': 5,
            'Waiting for 127.0.0.1: 1.7 seconds lagged': 1
        }
        for info, time in patterns.items():
            lag = api.lagpattern.search(info)
            self.assertIsNotNone(lag)
            self.assertEqual(int(lag.group("lag")), time)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
