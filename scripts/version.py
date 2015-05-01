#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Script to determine the Pywikibot version (tag, revision and date)."""
#
# (C) Merlijn 'valhallasw' van Deen, 2007-2008
# (C) xqt, 2010-2014
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import sys
import os
import pywikibot
from pywikibot.version import getversion
try:
    import httplib2
except ImportError:
    httplib2 = {'__version__': 'n/a'}

WMF_CACERT = 'MIIDxTCCAq2gAwIBAgIQAqxcJmoLQJuPC3nyrkYldzANBgkqhkiG9w0BAQUFADBs'


def check_environ(environ_name):
    """Print environment variable."""
    pywikibot.output('{0}: {1}'.format(environ_name, os.environ.get(environ_name, 'Not set')))


if __name__ == '__main__':
    pywikibot.output('Pywikibot: %s' % getversion())
    pywikibot.output('Release version: %s' % pywikibot.__release__)
    pywikibot.output('httplib2 version: %s' % httplib2.__version__)

    has_wikimedia_cert = False
    if not hasattr(httplib2, 'CA_CERTS') or not httplib2.CA_CERTS:
        pywikibot.output('  cacerts: not defined')
    elif not os.path.isfile(httplib2.CA_CERTS):
        pywikibot.output('  cacerts: %s (missing)' % httplib2.CA_CERTS)
    else:
        pywikibot.output('  cacerts: %s' % httplib2.CA_CERTS)

        with open(httplib2.CA_CERTS, 'r') as cert_file:
            text = cert_file.read()
            if WMF_CACERT in text:
                has_wikimedia_cert = True
        pywikibot.output(u'    certificate test: %s'
                         % ('ok' if has_wikimedia_cert else 'not ok'))
    if not has_wikimedia_cert:
        pywikibot.output(
            '  Please reinstall httplib2 or run git submodules update!')

    pywikibot.output('Python: %s' % sys.version)
    normalize_text = u'\u092e\u093e\u0930\u094d\u0915 \u091c\u093c\u0941\u0915\u0947\u0930\u092c\u0930\u094d\u0917'

    if normalize_text != __import__('unicodedata').normalize(
            'NFC', normalize_text):
        pywikibot.output(u'  unicode test: triggers problem #3081100')
    else:
        pywikibot.output(u'  unicode test: ok')
    check_environ('PYWIKIBOT2_DIR')
    check_environ('PYWIKIBOT2_DIR_PWB')
    check_environ('PYWIKIBOT2_NO_USER_CONFIG')
    pywikibot.output('Config base dir: {0}'.format(pywikibot.config2.base_dir))
    for family, usernames in pywikibot.config2.usernames.items():
        if usernames:
            pywikibot.output('Usernames for family "{0}":'.format(family))
            for lang, username in usernames.items():
                sysop_name = pywikibot.config2.sysopnames.get(family, {}).get(lang)
                if not sysop_name:
                    sysop_name = 'no sysop configured'
                elif sysop_name == username:
                    sysop_name = 'also sysop'
                pywikibot.output('\t{0}: {1} ({2})'.format(lang, username, sysop_name))
