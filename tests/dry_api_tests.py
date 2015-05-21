# -*- coding: utf-8  -*-
"""API tests which do not interact with a site."""
#
# (C) Pywikibot team, 2012-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import os
import datetime

import pywikibot
from pywikibot.data.api import (
    CachedRequest,
    ParamInfo,
    Request,
    QueryGenerator,
)
from pywikibot.family import Family

from tests import _images_dir
from tests.utils import DummySiteinfo
from tests.aspects import (
    unittest, TestCase, DefaultDrySiteTestCase, SiteAttributeTestCase,
)


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
        super(DryCachedRequestTests, self).setUp()
        self.parms = {'site': self.basesite,
                      'action': 'query',
                      'meta': 'userinfo'}
        self.req = CachedRequest(expiry=1, **self.parms)
        self.expreq = CachedRequest(expiry=0, **self.parms)
        self.diffreq = CachedRequest(expiry=1, site=self.basesite, action='query', meta='siteinfo')
        self.diffsite = CachedRequest(expiry=1, site=self.altsite, action='query', meta='userinfo')

    def test_expiry_formats(self):
        self.assertEqual(self.req.expiry, CachedRequest(datetime.timedelta(days=1), **self.parms).expiry)

    def test_expired(self):
        self.assertFalse(self.req._expired(datetime.datetime.now()))
        self.assertTrue(self.req._expired(datetime.datetime.now() - datetime.timedelta(days=2)))

    def test_get_cache_dir(self):
        retval = self.req._get_cache_dir()
        self.assertIn('apicache', retval)

    def test_create_file_name(self):
        self.assertEqual(self.req._create_file_name(), self.req._create_file_name())
        self.assertEqual(self.req._create_file_name(), self.expreq._create_file_name())
        self.assertNotEqual(self.req._create_file_name(), self.diffreq._create_file_name())

    def test_cachefile_path(self):
        self.assertEqual(self.req._cachefile_path(), self.req._cachefile_path())
        self.assertEqual(self.req._cachefile_path(), self.expreq._cachefile_path())
        self.assertNotEqual(self.req._cachefile_path(), self.diffreq._cachefile_path())
        self.assertNotEqual(self.req._cachefile_path(), self.diffsite._cachefile_path())


class MockCachedRequestKeyTests(TestCase):

    """Test CachedRequest using moke site objects."""

    net = False

    def setUp(self):
        class MockFamily(Family):

            @property
            def name(self):
                return 'mock'

        class MockSite(pywikibot.site.APISite):

            _loginstatus = pywikibot.site.LoginStatus.NOT_ATTEMPTED

            _namespaces = {2: ['User']}

            def __init__(self):
                self._user = 'anon'
                pywikibot.site.BaseSite.__init__(self, 'mock', MockFamily())
                self._siteinfo = DummySiteinfo({'case': 'first-letter'})

            def version(self):
                return '1.13'  # pre 1.14

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
                return "MockSite()"

            def __getattr__(self, attr):
                raise Exception("Attribute %r not defined" % attr)

        self.mocksite = MockSite()
        super(MockCachedRequestKeyTests, self).setUp()

    def test_cachefile_path_different_users(self):
        req = CachedRequest(expiry=1, site=self.mocksite,
                            action='query', meta='siteinfo')
        anonpath = req._cachefile_path()

        self.mocksite._userinfo = {'name': u'MyUser'}
        self.mocksite._loginstatus = 0
        req = CachedRequest(expiry=1, site=self.mocksite,
                            action='query', meta='siteinfo')
        userpath = req._cachefile_path()

        self.assertNotEqual(anonpath, userpath)

        self.mocksite._userinfo = {'name': u'MySysop'}
        self.mocksite._loginstatus = 1
        req = CachedRequest(expiry=1, site=self.mocksite,
                            action='query', meta='siteinfo')
        sysoppath = req._cachefile_path()

        self.assertNotEqual(anonpath, sysoppath)
        self.assertNotEqual(userpath, sysoppath)

    def test_unicode(self):
        self.mocksite._userinfo = {'name': u'محمد الفلسطيني'}
        self.mocksite._loginstatus = 0

        req = CachedRequest(expiry=1, site=self.mocksite,
                            action='query', meta='siteinfo')
        en_user_path = req._cachefile_path()

        self.mocksite._namespaces = {2: [u'مستخدم']}

        req = CachedRequest(expiry=1, site=self.mocksite,
                            action='query', meta='siteinfo')

        expect = (u'MockSite()User(User:محمد الفلسطيني)' +
                  "[('action', 'query'), ('meta', 'siteinfo')]")

        self.assertEqual(repr(req._uniquedescriptionstr()), repr(expect))

        self.assertEqual(req._uniquedescriptionstr().encode('utf-8'),
                         expect.encode('utf-8'))

        ar_user_path = req._cachefile_path()

        self.assertEqual(en_user_path, ar_user_path)


class DryWriteAssertTests(DefaultDrySiteTestCase):

    """Test client site write assert."""

    def test_no_user(self):
        """Test Request object when not a user."""
        site = self.get_site()

        del site._userinfo
        self.assertRaisesRegex(pywikibot.Error, ' without userinfo',
                               Request, site=site, action='edit')

        # Explicitly using str as the test expects it to be str (without the
        # u-prefix) in Python 2 and this module is using unicode_literals
        site._userinfo = {'name': str('1.2.3.4'), 'groups': []}

        self.assertRaisesRegex(pywikibot.Error, " as IP '1.2.3.4'",
                               Request, site=site, action='edit')

    def test_unexpected_user(self):
        """Test Request object when username is not correct."""
        site = self.get_site()
        site._userinfo = {'name': 'other_username', 'groups': []}
        site._username[0] = 'myusername'

        Request(site=site, action='edit')

    def test_normal(self):
        """Test Request object when username is correct."""
        site = self.get_site()
        site._userinfo = {'name': 'myusername', 'groups': []}
        site._username[0] = 'myusername'

        Request(site=site, action='edit')


class DryMimeTests(TestCase):

    """Test MIME request handling without a real site."""

    net = False

    def test_mime_file_payload(self):
        """Test Request._generate_MIME_part loads binary as binary."""
        local_filename = os.path.join(_images_dir, 'MP_sounds.png')
        with open(local_filename, 'rb') as f:
            file_content = f.read()
        submsg = Request._generate_MIME_part(
            'file', file_content, ('image', 'png'),
            {'filename': local_filename})
        self.assertEqual(file_content, submsg.get_payload(decode=True))

    def test_mime_file_container(self):
        """Test Request._build_mime_request encodes binary."""
        local_filename = os.path.join(_images_dir, 'MP_sounds.png')
        with open(local_filename, 'rb') as f:
            file_content = f.read()
        body = Request._build_mime_request({}, {
            'file': (file_content, ('image', 'png'),
                     {'filename': local_filename})
        })[1]
        self.assertNotEqual(body.find(file_content), -1)


class MimeTests(DefaultDrySiteTestCase):

    """Test MIME request handling with a real site."""

    def test_upload_object(self):
        """Test Request object prepared to upload."""
        # fake write test needs the config username
        site = self.get_site()
        site._username[0] = 'myusername'
        site._userinfo = {'name': 'myusername', 'groups': []}
        req = Request(site=site, action="upload",
                      file='MP_sounds.png', mime=True,
                      filename=os.path.join(_images_dir, 'MP_sounds.png'))
        self.assertEqual(req.mime, True)


class ParamInfoDictTests(DefaultDrySiteTestCase):

    """Test extracting data from the ParamInfo."""

    prop_info_param_data = {  # data from 1.25
        "name": "info",
        "classname": "ApiQueryInfo",
        "path": "query+info",
        "group": "prop",
        "prefix": "in",
        "parameters": [
            {
                "name": "prop",
                "multi": "",
                "limit": 500,
                "lowlimit": 50,
                "highlimit": 500,
                "type": [
                    "protection",
                    "talkid",
                    "watched",
                    "watchers",
                    "notificationtimestamp",
                    "subjectid",
                    "url",
                    "readable",
                    "preload",
                    "displaytitle"
                ]
            },
            {
                "name": "token",
                "deprecated": "",
                "multi": "",
                "limit": 500,
                "lowlimit": 50,
                "highlimit": 500,
                "type": [
                    "edit",
                    "delete",
                    "protect",
                    "move",
                    "block",
                    "unblock",
                    "email",
                    "import",
                    "watch"
                ]
            },
            {
                "name": "continue",
                "type": "string"
            }
        ],
        "querytype": "prop"
    }

    edit_action_param_data = {
        'name': 'edit',
        'path': 'edit'
    }

    def setUp(self):
        """Add a real ParamInfo to the DrySite."""
        super(ParamInfoDictTests, self).setUp()
        site = self.get_site()
        site._paraminfo = ParamInfo(site)
        # Pretend that paraminfo has been loaded
        for mod in site._paraminfo.init_modules:
            site._paraminfo._paraminfo[mod] = {}
        site._paraminfo._query_modules = ['info']
        site._paraminfo._action_modules = ['edit']
        # TODO: remove access of this private member of ParamInfo
        site._paraminfo._ParamInfo__inited = True

    def test_new_format(self):
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
        qGen1 = QueryGenerator(site=self.get_site(), action="query", meta="siteinfo")
        qGen2 = QueryGenerator(site=self.get_site(), meta="siteinfo")
        self.assertCountEqual(qGen1.request._params.items(), qGen2.request._params.items())


if __name__ == '__main__':
    unittest.main()
