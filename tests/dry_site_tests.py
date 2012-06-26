import pywikibot

class DrySite(pywikibot.site.APISite):
    @property
    def userinfo(self):
        return self._userinfo

def test_logged_in():
    x = DrySite('en')
    
    x._userinfo = {'name': None, 'groups': []}
    x._username = ['normal_user', 'sysop_user']

    assert not x.logged_in(True)
    assert not x.logged_in(False)
    
    x._userinfo['name'] = 'normal_user'
    assert not x.logged_in(True)
    assert x.logged_in(False)    
    
    x._userinfo['name'] = 'sysop_user'
    x._userinfo['groups'] = ['sysop']
    assert x.logged_in(True)
    assert not x.logged_in(False)

class SiteMock(object):
    last_login = None
    last_fn_called = False

    def login(self, as_sysop):
        self.last_login = 'sysop' if as_sysop else 'user'

    def inner_fn(self, *args, **kwargs):
        self.last_fn_called = (args, kwargs)
        return (args, kwargs)

def test_must_be_user():
    x = SiteMock()
    wrapped_inner = pywikibot.site.must_be(group='user')(x.inner_fn)
    assert(wrapped_inner(x,1,2,3,a='a', b='b') == ((x,1,2,3), {'a': 'a', 'b': 'b'}))
    assert(x.last_fn_called == ((x,1,2,3), {'a': 'a', 'b': 'b'}))
    assert(x.last_login == 'user')

def test_must_be_sysop():
    x = SiteMock()
    wrapped_inner = pywikibot.site.must_be(group='sysop')(x.inner_fn)
    assert(wrapped_inner(x,1,2,3,a='a', b='b') == ((x,1,2,3), {'a': 'a', 'b': 'b'}))
    assert(x.last_fn_called == ((x,1,2,3), {'a': 'a', 'b': 'b'}))
    assert(x.last_login == 'sysop')


