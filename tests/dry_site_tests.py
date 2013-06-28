import pywikibot
import unittest


class DrySite(pywikibot.site.APISite):
    @property
    def userinfo(self):
        return self._userinfo


class TestDrySite(unittest.TestCase):
    def test_logged_in(self):
        x = DrySite('en')

        x._userinfo = {'name': None, 'groups': []}
        x._username = ['normal_user', 'sysop_user']

        self.assertFalse(x.logged_in(True))
        self.assertFalse(x.logged_in(False))

        x._userinfo['name'] = 'normal_user'
        self.assertFalse(x.logged_in(True))
        self.assertTrue(x.logged_in(False))

        x._userinfo['name'] = 'sysop_user'
        x._userinfo['groups'] = ['sysop']
        self.assertTrue(x.logged_in(True))
        self.assertFalse(x.logged_in(False))


class SiteMock(object):
    last_login = None
    last_fn_called = False

    def login(self, as_sysop):
        self.last_login = 'sysop' if as_sysop else 'user'

    def inner_fn(self, *args, **kwargs):
        self.last_fn_called = (args, kwargs)
        return args, kwargs


class TestSiteMock(unittest.TestCase):
    def test_must_be_user(self):
        x = SiteMock()
        wrapped_inner = pywikibot.site.must_be(group='user')(x.inner_fn)
        self.assertEqual(wrapped_inner(x,1,2,3,a='a', b='b'), ((x,1,2,3), {'a': 'a', 'b': 'b'}))
        self.assertEqual(x.last_fn_called, ((x,1,2,3), {'a': 'a', 'b': 'b'}))
        self.assertEqual(x.last_login, 'user')

    def test_must_be_sysop(self):
        x = SiteMock()
        wrapped_inner = pywikibot.site.must_be(group='sysop')(x.inner_fn)
        self.assertEqual(wrapped_inner(x,1,2,3,a='a', b='b'), ((x,1,2,3), {'a': 'a', 'b': 'b'}))
        self.assertEqual(x.last_fn_called, ((x,1,2,3), {'a': 'a', 'b': 'b'}))
        self.assertEqual(x.last_login, 'sysop')

if __name__ == '__main__':
    unittest.main()
