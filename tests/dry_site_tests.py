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
    assert x.logged_in(False)