#!/usr/bin/python
"""Script to determine the Pywikibot version (tag, revision and date)."""
#
# (C) Pywikibot team, 2007-2020
#
# Distributed under the terms of the MIT license.
#
import codecs
import os
import sys

import pywikibot
from pywikibot.version import get_toolforge_hostname, getversion


try:
    import requests
except ImportError:
    class DummyRequests:

        """Fake requests instance."""

        __version__ = 'n/a'

    requests = DummyRequests()

WMF_CACERT = 'MIIDxTCCAq2gAwIBAgIQAqxcJmoLQJuPC3nyrkYldzANBgkqhkiG9w0BAQUFADBs'


def main(*args) -> None:
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

    # check environment settings
    settings = {key for key in os.environ if key.startswith('PYWIKIBOT')}
    settings.update(['PYWIKIBOT_DIR', 'PYWIKIBOT_DIR_PWB',
                     'PYWIKIBOT_NO_USER_CONFIG'])
    for environ_name in sorted(settings):
        pywikibot.output('{}: {}'.format(environ_name,
                                         os.environ.get(environ_name,
                                                        'Not set')))

    pywikibot.output('Config base dir: ' + pywikibot.config.base_dir)
    for family, usernames in pywikibot.config.usernames.items():
        if not usernames:
            continue
        pywikibot.output('Usernames for family "{}":'.format(family))
        for lang, username in usernames.items():
            pywikibot.output('\t{}: {}'.format(lang, username))


if __name__ == '__main__':
    main()
