#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Script to determine the Pywikibot version (tag, revision and date). """
#
# (C) Merlijn 'valhallasw' van Deen, 2007-2008
# (C) xqt, 2010-2014
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
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

if __name__ == '__main__':
    pywikibot.output('Pywikibot: %s' % getversion())
    pywikibot.output('Release version: %s' % pywikibot.__release__)
    pywikibot.output('httplib2 version: %s' % httplib2.__version__)
    if not hasattr(httplib2, 'CA_CERTS'):
        httplib2.CA_CERTS = ''
    pywikibot.output('  cacerts: %s' % httplib2.CA_CERTS)
    has_wikimedia_cert = False
    if os.path.isfile(httplib2.CA_CERTS):
        with open(httplib2.CA_CERTS, 'r') as cert_file:
            text = cert_file.read()
            if 'MIIDxTCCAq2gAwIBAgIQAqxcJmoLQJuPC3nyrkYldzANBgkqhkiG9w0BAQUFADBs' in text:
                has_wikimedia_cert = True
    pywikibot.output(u'    certificate test: %s' % ('ok' if has_wikimedia_cert else 'not ok'))
    pywikibot.output('Python: %s' % sys.version)
    if not __import__('unicodedata').normalize('NFC', u'\u092e\u093e\u0930\u094d\u0915 \u091c\u093c\u0941\u0915\u0947\u0930\u092c\u0930\u094d\u0917') == u'\u092e\u093e\u0930\u094d\u0915 \u091c\u093c\u0941\u0915\u0947\u0930\u092c\u0930\u094d\u0917':
        pywikibot.output(u'  unicode test: triggers problem #3081100')
    else:
        pywikibot.output(u'  unicode test: ok')
