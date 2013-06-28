import datetime
import pywikibot
from pywikibot.data.api import CachedRequest

parms = {'site': pywikibot.getSite('en'),
         'action': 'query',
         'meta': 'userinfo'}

req = CachedRequest(expiry=1, **parms)
expreq = CachedRequest(expiry=0, **parms)
diffreq = CachedRequest(expiry=1, site=pywikibot.getSite('en'), action='query', meta='siteinfo')
diffsite = CachedRequest(expiry=1, site=pywikibot.getSite('de'), action='query', meta='userinfo')


def test_expiry_formats():
    import datetime
    assert(req.expiry == CachedRequest(datetime.timedelta(days=1), **parms).expiry)


def test_get_cache_dir():
    retval = req._get_cache_dir()
    assert('apicache' in retval)


def test_create_file_name():
    assert(req._create_file_name() == req._create_file_name())
    assert(req._create_file_name() == expreq._create_file_name())
    assert(req._create_file_name() != diffreq._create_file_name())


def test_cachefile_path():
    assert(req._cachefile_path() == req._cachefile_path())
    assert(req._cachefile_path() == expreq._cachefile_path())
    assert(req._cachefile_path() != diffreq._cachefile_path())
    assert(req._cachefile_path() != diffsite._cachefile_path())


def test_expired():
    assert(not req._expired(datetime.datetime.now()))
    assert(req._expired(datetime.datetime.now() - datetime.timedelta(days=2)))
