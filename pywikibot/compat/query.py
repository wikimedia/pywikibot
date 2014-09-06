import pywikibot
from pywikibot.data import api
from pywikibot.tools import deprecated, deprecate_arg

import sys
if sys.version_info[0] > 2:
    import io as StringIO
else:
    import StringIO


@deprecated("pywikibot.data.api.Request")
@deprecate_arg("useAPI", None)
@deprecate_arg("retryCount", None)
@deprecate_arg("encodeTitle", None)
def GetData(request, site=None, back_response=False):
    if site:
        request['site'] = site

    req = api.Request(**request)
    result = req.submit()

    if back_response:
        pywikibot.warning(u"back_response is no longer supported; an empty "
                          u"response object will be returned")
        res_dummy = StringIO.StringIO()
        res_dummy.__dict__.update({u'code': 0, u'msg': u''})
        return res_dummy, result
    return result
