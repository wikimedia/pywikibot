#!/usr/bin/env python3
"""API tests which do not interact with a site."""
#
# (C) Pywikibot team, 2012-2023
#
# Distributed under the terms of the MIT license.
#
import datetime
from pathlib import Path
from unittest.mock import patch

import pywikibot
from pywikibot.data.api import (
    CachedRequest,
    ParamInfo,
    QueryGenerator,
    Request,
)
from pywikibot.exceptions import Error
from pywikibot.family import Family
from pywikibot.login import LoginStatus
from pywikibot.tools import PYTHON_VERSION, suppress_warnings
from tests import join_images_path
from tests.aspects import (
    DefaultDrySiteTestCase,
    SiteAttributeTestCase,
    TestCase,
    unittest,
)
from tests.utils import DummySiteinfo


class DryCachedRequestTests(SiteAttributeTestCase):

    """Test CachedRequest using real site objects."""

    sites = {
        'basesite': {
            'family': 'wikipedia',
            'code': 'en',
        },
        'altsite': {
            'family': 'wikipedia',
            'code': 'de',
        },
    }

    dry = True

    def setUp(self):
        """Initialize the fake requests."""
        super().setUp()
        self.parms = {'action': 'query',
                      'meta': 'userinfo'}
        self.req = CachedRequest(expiry=1, site=self.basesite,
                                 parameters=self.parms)
        self.expreq = CachedRequest(expiry=0, site=self.basesite,
                                    parameters=self.parms)
        self.diffreq = CachedRequest(
            expiry=1, site=self.basesite,
            parameters={'action': 'query', 'meta': 'siteinfo'})
        self.diffsite = CachedRequest(
            expiry=1, site=self.altsite,
            parameters={'action': 'query', 'meta': 'userinfo'})

        with suppress_warnings('Instead of using kwargs ', DeprecationWarning):
            self.deprecated_explicit = CachedRequest(
                expiry=1, site=self.basesite, action='query', meta='userinfo')
            self.deprecated_asterisks = CachedRequest(
                expiry=1, site=self.basesite, **self.parms)

    def test_expiry_formats(self):
        """Test using a timedelta as expiry."""
        self.assertEqual(self.req.expiry,
                         CachedRequest(datetime.timedelta(days=1),
                                       site=self.basesite,
                                       parameters=self.parms).expiry)

    def test_expired(self):
        """Test if the request is expired."""
        now = datetime.datetime.utcnow()
        self.assertFalse(self.req._expired(now))
        self.assertTrue(
            self.req._expired(now - datetime.timedelta(days=2)),
            msg=f'\nreq.expiry: {self.req.expiry}, now: {now}')

    def test_parameter_types(self):
        """Test _uniquedescriptionstr is identical using different ways."""
        # This test is done as create_file_name and cachefile_path only use
        # the hashed name which is not very helpful
        self.assertEqual(self.req._uniquedescriptionstr(),
                         self.req._uniquedescriptionstr())
        self.assertEqual(self.req._uniquedescriptionstr(),
                         self.expreq._uniquedescriptionstr())
        self.assertEqual(self.req._uniquedescriptionstr(),
                         self.deprecated_explicit._uniquedescriptionstr())
        self.assertEqual(self.req._uniquedescriptionstr(),
                         self.deprecated_asterisks._uniquedescriptionstr())
        self.assertNotEqual(self.req._uniquedescriptionstr(),
                            self.diffreq._uniquedescriptionstr())
        self.assertNotEqual(self.req._uniquedescriptionstr(),
                            self.diffsite._uniquedescriptionstr())

    def test_get_cache_dir(self):
        """Test that 'apicache' is in the cache dir."""
        retval = self.req._get_cache_dir()
        self.assertIsInstance(retval, Path)
        self.assertIn(f'apicache-py{PYTHON_VERSION[0]:d}', retval.parts)

    def test_create_file_name(self):
        """Test the file names for the cache."""
        self.assertEqual(self.req._create_file_name(),
                         self.req._create_file_name())
        self.assertEqual(self.req._create_file_name(),
                         self.expreq._create_file_name())
        self.assertEqual(self.req._create_file_name(),
                         self.deprecated_explicit._create_file_name())
        self.assertEqual(self.req._create_file_name(),
                         self.deprecated_asterisks._create_file_name())
        self.assertNotEqual(self.req._create_file_name(),
                            self.diffreq._create_file_name())

    def test_cachefile_path(self):
        """Test the file paths for the cache."""
        self.assertEqual(self.req._cachefile_path(),
                         self.req._cachefile_path())
        self.assertEqual(self.req._cachefile_path(),
                         self.expreq._cachefile_path())
        self.assertEqual(self.req._cachefile_path(),
                         self.deprecated_explicit._cachefile_path())
        self.assertEqual(self.req._cachefile_path(),
                         self.deprecated_asterisks._cachefile_path())
        self.assertNotEqual(self.req._cachefile_path(),
                            self.diffreq._cachefile_path())
        self.assertNotEqual(self.req._cachefile_path(),
                            self.diffsite._cachefile_path())


class MockCachedRequestKeyTests(TestCase):

    """Test CachedRequest using moke site objects."""

    net = False

    def setUp(self):
        """Create a mock family and site."""
        class MockFamily(Family):

            @property
            def name(self):
                return 'mock'

        class MockSite(pywikibot.site.APISite):

            _loginstatus = LoginStatus.NOT_ATTEMPTED

            _namespaces = {2: ['User']}

            def __init__(self):
                self._user = 'anon'
                pywikibot.site.BaseSite.__init__(self, 'mock', MockFamily())
                self._siteinfo = DummySiteinfo({'case': 'first-letter'})

            def version(self):
                return '1.27'  # lowest supported release

            def protocol(self):
                return 'http'

            def languages(self):
                return ['mock']

            def user(self):
                return self._user

            def encoding(self):
                return 'utf-8'

            def encodings(self):
                return []

            @property
            def siteinfo(self):
                return self._siteinfo

            def __repr__(self):
                return 'MockSite()'

            def __getattr__(self, attr):
                raise Exception(f'Attribute {attr!r} not defined')

        self.mocksite = MockSite()
        super().setUp()

    def test_cachefile_path_different_users(self):
        """Test and compare file paths when different usernames are used."""
        req = CachedRequest(expiry=1, site=self.mocksite,
                            parameters={'action': 'query', 'meta': 'siteinfo'})
        anonpath = req._cachefile_path()

        self.mocksite._userinfo = {'name': 'MyUser'}
        self.mocksite._loginstatus = LoginStatus.AS_USER
        req = CachedRequest(expiry=1, site=self.mocksite,
                            parameters={'action': 'query', 'meta': 'siteinfo'})
        userpath = req._cachefile_path()

        self.assertNotEqual(anonpath, userpath)

        self.mocksite._userinfo = {'name': 'MyOtherUser'}
        self.mocksite._loginstatus = LoginStatus.AS_USER
        req = CachedRequest(expiry=1, site=self.mocksite,
                            parameters={'action': 'query', 'meta': 'siteinfo'})
        otherpath = req._cachefile_path()

        self.assertNotEqual(anonpath, otherpath)
        self.assertNotEqual(userpath, otherpath)

    def test_unicode(self):
        """Test caching with Unicode content."""
        self.mocksite._userinfo = {'name': 'محمد الفلسطيني'}
        self.mocksite._loginstatus = LoginStatus.AS_USER

        req = CachedRequest(expiry=1, site=self.mocksite,
                            parameters={'action': 'query', 'meta': 'siteinfo'})
        en_user_path = req._cachefile_path()

        self.mocksite._namespaces = {2: ['مستخدم']}

        req = CachedRequest(expiry=1, site=self.mocksite,
                            parameters={'action': 'query', 'meta': 'siteinfo'})

        expect = ('MockSite()User(User:محمد الفلسطيني)'
                  + "[('action', 'query'), ('meta', 'siteinfo')]")

        self.assertEqual(repr(req._uniquedescriptionstr()), repr(expect))

        self.assertEqual(req._uniquedescriptionstr().encode('utf-8'),
                         expect.encode('utf-8'))

        ar_user_path = req._cachefile_path()

        self.assertEqual(en_user_path, ar_user_path)


class DryWriteAssertTests(DefaultDrySiteTestCase):

    """Test client site write assert."""

    def test_no_user(self):
        """Test Request object when not a user."""
        self.site._userinfo = {}
        with self.subTest(userinfo=self.site._userinfo), \
             self.assertRaisesRegex(Error,
                                    'API write action attempted without user'):
            Request(site=self.site, parameters={'action': 'edit'})

        self.site._userinfo = {'name': '1.2.3.4', 'groups': [], 'anon': ''}
        with self.subTest(userinfo=self.site._userinfo), \
             self.assertRaisesRegex(Error, " as IP '1.2.3.4'"):
            Request(site=self.site, parameters={'action': 'edit'})

    def test_unexpected_user(self):
        """Test Request object when username is not correct."""
        self.site._userinfo = {'name': 'other_username', 'groups': [],
                               'id': '1'}
        self.site._username = 'myusername'
        # Ignore warning: API write action by unexpected username commenced.
        with patch('pywikibot.warning'):
            Request(site=self.site, parameters={'action': 'edit'})
        self.assertNotEqual(self.site.user(), self.site.username())
        self.assertNotEqual(self.site.userinfo['name'], self.site.username())
        self.assertFalse(self.site.logged_in())

    def test_normal(self):
        """Test Request object when username is correct."""
        self.site._userinfo = {'name': 'myusername', 'groups': [], 'id': '1'}
        self.site._username = 'myusername'
        Request(site=self.site, parameters={'action': 'edit'})
        self.assertEqual(self.site.user(), self.site.username())
        self.assertTrue(self.site.logged_in())


class DryMimeTests(TestCase):

    """Test MIME request handling without a real site."""

    net = False

    def test_mime_file_payload(self):
        """Test Request._generate_mime_part loads binary as binary."""
        local_filename = join_images_path('MP_sounds.png')
        with open(local_filename, 'rb') as f:
            file_content = f.read()
        submsg = Request._generate_mime_part(
            'file', file_content, ('image', 'png'),
            {'filename': local_filename})
        self.assertEqual(file_content, submsg.get_payload(decode=True))

    def test_mime_file_container(self):
        """Test Request._build_mime_request encodes binary."""
        local_filename = join_images_path('MP_sounds.png')
        with open(local_filename, 'rb') as f:
            file_content = f.read()
        _, body = Request._build_mime_request({}, {
            'file': (file_content, ('image', 'png'),
                     {'filename': local_filename})
        })
        self.assertNotEqual(body.find(file_content), -1)


class ParamInfoDictTests(DefaultDrySiteTestCase):

    """Test extracting data from the ParamInfo."""

    prop_info_param_data = {  # data from 1.25
        'name': 'info',
        'classname': 'ApiQueryInfo',
        'path': 'query+info',
        'group': 'prop',
        'prefix': 'in',
        'parameters': [
            {
                'name': 'prop',
                'multi': '',
                'limit': 500,
                'lowlimit': 50,
                'highlimit': 500,
                'type': [
                    'protection',
                    'talkid',
                    'watched',
                    'watchers',
                    'notificationtimestamp',
                    'subjectid',
                    'url',
                    'readable',
                    'preload',
                    'displaytitle'
                ]
            },
            {
                'name': 'token',
                'deprecated': '',
                'multi': '',
                'limit': 500,
                'lowlimit': 50,
                'highlimit': 500,
                'type': [
                    'edit',
                    'delete',
                    'protect',
                    'move',
                    'block',
                    'unblock',
                    'email',
                    'import',
                    'watch'
                ]
            },
            {
                'name': 'continue',
                'type': 'string'
            }
        ],
        'querytype': 'prop'
    }

    edit_action_param_data = {
        'name': 'edit',
        'path': 'edit'
    }

    def setUp(self):
        """Add a real ParamInfo to the DrySite."""
        super().setUp()
        site = self.get_site()
        site._paraminfo = ParamInfo(site)
        # Pretend that paraminfo has been loaded
        for mod in site._paraminfo.init_modules:
            site._paraminfo._paraminfo[mod] = {}
        site._paraminfo._action_modules = frozenset(['edit'])
        site._paraminfo._modules = {'query': frozenset(['info'])}

    def test_new_format(self):
        """Test using a dummy formatted in the new modules-only mode."""
        pi = self.get_site()._paraminfo
        # Set it to the new limited set of keys.
        pi.paraminfo_keys = frozenset(['modules'])

        data = pi.normalize_paraminfo({
            'paraminfo': {
                'modules': [
                    self.prop_info_param_data,
                    self.edit_action_param_data,
                ]
            }
        })

        pi._paraminfo.update(data)
        self.assertIn('edit', pi._paraminfo)
        self.assertIn('query+info', pi._paraminfo)
        self.assertIn('edit', pi)
        self.assertIn('info', pi)

    def test_old_format(self):
        """Test using a dummy formatted in the old mode."""
        pi = self.get_site()._paraminfo
        # Reset it to the complete set of possible keys defined in the class
        pi.paraminfo_keys = ParamInfo.paraminfo_keys

        data = pi.normalize_paraminfo({
            'paraminfo': {
                'querymodules': [self.prop_info_param_data],
                'modules': [self.edit_action_param_data],
            }
        })

        pi._paraminfo.update(data)
        self.assertIn('edit', pi._paraminfo)
        self.assertIn('query+info', pi._paraminfo)
        self.assertIn('edit', pi)
        self.assertIn('info', pi)

    def test_attribute(self):
        """Test using __getitem__."""
        pi = self.get_site()._paraminfo
        # Reset it to the complete set of possible keys defined in the class
        pi.paraminfo_keys = ParamInfo.paraminfo_keys

        data = pi.normalize_paraminfo({
            'paraminfo': {
                'querymodules': [self.prop_info_param_data],
            }
        })

        pi._paraminfo.update(data)

        self.assertEqual(pi._paraminfo['query+info']['querytype'], 'prop')
        self.assertEqual(pi['info']['prefix'], 'in')

    def test_parameter(self):
        """Test parameter() method."""
        pi = self.get_site()._paraminfo
        # Reset it to the complete set of possible keys defined in the class
        pi.paraminfo_keys = ParamInfo.paraminfo_keys

        data = pi.normalize_paraminfo({
            'paraminfo': {
                'querymodules': [self.prop_info_param_data],
            }
        })

        pi._paraminfo.update(data)

        param = pi.parameter('info', 'token')
        self.assertIsInstance(param, dict)

        self.assertEqual(param['name'], 'token')
        self.assertIn('deprecated', param)

        self.assertIsInstance(param['type'], list)
        self.assertIn('email', param['type'])


class QueryGenTests(DefaultDrySiteTestCase):

    """Test QueryGenerator with a real site."""

    def test_query_constructor(self):
        """Test QueryGenerator constructor."""
        q_gen1 = QueryGenerator(
            site=self.site, parameters={'action': 'query', 'meta': 'siteinfo'})
        q_gen2 = QueryGenerator(
            site=self.site, parameters={'meta': 'siteinfo'})
        self.assertCountEqual(
            q_gen1.request._params.items(), q_gen2.request._params.items())


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
