#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Script to determine the Pywikibot version (tag, revision and date)."""
#
# (C) Merlijn 'valhallasw' van Deen, 2007-2008
# (C) xqt, 2010-2016
# (C) Pywikibot team, 2007-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import codecs
import os
import sys

import pywikibot

from pywikibot.version import getversion

try:
    import requests
except ImportError:
    class DummyRequests(object):

        """Fake requests instance."""

        __version__ = 'n/a'

    requests = DummyRequests()

WMF_CACERT = 'MIIDxTCCAq2gAwIBAgIQAqxcJmoLQJuPC3nyrkYldzANBgkqhkiG9w0BAQUFADBs'


def check_environ(environ_name):
    """Print environment variable."""
    pywikibot.output('{0}: {1}'.format(environ_name, os.environ.get(environ_name, 'Not set')))


def main(*args):
    """Print pywikibot version and important settings."""
    pywikibot.output('Pywikibot: %s' % getversion())
    pywikibot.output('Release version: %s' % pywikibot.__release__)
    pywikibot.output('requests version: %s' % requests.__version__)

    has_wikimedia_cert = False
    if (not hasattr(requests, 'certs') or
            not hasattr(requests.certs, 'where') or
            not callable(requests.certs.where)):
        pywikibot.output('  cacerts: not defined')
    elif not os.path.isfile(requests.certs.where()):
        pywikibot.output('  cacerts: %s (missing)' % requests.certs.where())
    else:
        pywikibot.output('  cacerts: %s' % requests.certs.where())

        with codecs.open(requests.certs.where(), 'r', 'utf-8') as cert_file:
            text = cert_file.read()
            if WMF_CACERT in text:
                has_wikimedia_cert = True
        pywikibot.output(u'    certificate test: %s'
                         % ('ok' if has_wikimedia_cert else 'not ok'))
    if not has_wikimedia_cert:
        pywikibot.output(
            '  Please reinstall requests!')

    pywikibot.output('Python: %s' % sys.version)

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

if __name__ == '__main__':
    main()
