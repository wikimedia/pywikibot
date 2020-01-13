#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to determine the Pywikibot version (tag, revision and date)."""
#
# (C) Merlijn 'valhallasw' van Deen, 2007-2008
# (C) xqt, 2010-2020
# (C) Pywikibot team, 2007-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import codecs
import os
import sys

import pywikibot

from pywikibot.version import getversion, get_toolforge_hostname

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
    pywikibot.output('{0}: {1}'.format(environ_name,
                                       os.environ.get(environ_name,
                                                      'Not set')))


def main(*args):
    """Print pywikibot version and important settings."""
    pywikibot.output('Pywikibot: ' + getversion())
    pywikibot.output('Release version: ' + pywikibot.__version__)
    pywikibot.output('requests version: ' + requests.__version__)

    has_wikimedia_cert = False
    if (not hasattr(requests, 'certs')
            or not hasattr(requests.certs, 'where')
            or not callable(requests.certs.where)):
        pywikibot.output('  cacerts: not defined')
    elif not os.path.isfile(requests.certs.where()):
        pywikibot.output('  cacerts: {} (missing)'.format(
            requests.certs.where()))
    else:
        pywikibot.output('  cacerts: ' + requests.certs.where())

        with codecs.open(requests.certs.where(), 'r', 'utf-8') as cert_file:
            text = cert_file.read()
            if WMF_CACERT in text:
                has_wikimedia_cert = True
        pywikibot.output('    certificate test: {}'
                         .format(('ok' if has_wikimedia_cert else 'not ok')))
    if not has_wikimedia_cert:
        pywikibot.output('  Please reinstall requests!')

    pywikibot.output('Python: ' + sys.version)

    toolforge_env_hostname = get_toolforge_hostname()
    if toolforge_env_hostname:
        pywikibot.output('Toolforge hostname: ' + toolforge_env_hostname)

    check_environ('PYWIKIBOT_DIR')
    check_environ('PYWIKIBOT_DIR_PWB')
    check_environ('PYWIKIBOT_NO_USER_CONFIG')
    pywikibot.output('Config base dir: ' + pywikibot.config2.base_dir)
    for family, usernames in pywikibot.config2.usernames.items():
        if not usernames:
            continue
        pywikibot.output('Usernames for family "{0}":'.format(family))
        for lang, username in usernames.items():
            pywikibot.output('\t{0}: {1}'.format(lang, username))


if __name__ == '__main__':
    main()
