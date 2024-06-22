#!/usr/bin/env python3
"""Script to determine the Pywikibot version (tag, revision and date).

The following option is supported:

-nouser  do not print usernames; otherwise they are printed for each
         registered family

.. versionchanged:: 7.0
   version script was moved to the framework scripts folder
.. versionadded:: 9.1.2
   the *-nouser* option.
"""
#
# (C) Pywikibot team, 2007-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import codecs
import os
import sys

import pywikibot
from pywikibot.version import getversion


class DummyModule:

    """Fake module instance."""

    __version__ = 'n/a'


try:
    import packaging
except ImportError:
    packaging = DummyModule()

try:
    import mwparserfromhell
except ImportError:
    mwparserfromhell = DummyModule()

try:
    import wikitextparser
except ImportError:
    wikitextparser = DummyModule()

try:
    import requests
except ImportError:
    requests = DummyModule()


WMF_CACERT = 'MIIDxTCCAq2gAwIBAgIQAqxcJmoLQJuPC3nyrkYldzANBgkqhkiG9w0BAQUFADBs'


def main(*args: str) -> None:
    """Print pywikibot version and important settings.

    .. versionchanged:: 9.1.2
       usernames are not printed with ``-nouser`` option.
    """
    pywikibot.info('Pywikibot: ' + getversion())
    pywikibot.info('Release version: ' + pywikibot.__version__)
    pywikibot.info('packaging version: ' + packaging.__version__)
    pywikibot.info('mwparserfromhell version: ' + mwparserfromhell.__version__)
    pywikibot.info('wikitextparser version: ' + wikitextparser.__version__)
    pywikibot.info('requests version: ' + requests.__version__)

    has_wikimedia_cert = False
    if (not hasattr(requests, 'certs')
            or not hasattr(requests.certs, 'where')
            or not callable(requests.certs.where)):
        pywikibot.info('  cacerts: not defined')
    elif not os.path.isfile(requests.certs.where()):
        pywikibot.info(f'  cacerts: {requests.certs.where()} (missing)')
    else:
        pywikibot.info('  cacerts: ' + requests.certs.where())

        with codecs.open(requests.certs.where(), 'r', 'utf-8') as cert_file:
            text = cert_file.read()
            if WMF_CACERT in text:
                has_wikimedia_cert = True
        pywikibot.info('    certificate test: {}'
                       .format('ok' if has_wikimedia_cert else 'not ok'))
    if not has_wikimedia_cert:
        pywikibot.info('  Please reinstall requests!')

    pywikibot.info('Python: ' + sys.version)

    # check environment settings
    settings = {key for key in os.environ if key.startswith('PYWIKIBOT')}
    settings.update(['PYWIKIBOT_DIR', 'PYWIKIBOT_DIR_PWB',
                     'PYWIKIBOT_NO_USER_CONFIG'])
    for environ_name in sorted(settings):
        pywikibot.info(
            '{}: {}'.format(environ_name,
                            os.environ.get(environ_name, 'Not set') or "''"))

    pywikibot.info('Config base dir: ' + pywikibot.config.base_dir)

    if '-nouser' in sys.argv:
        usernames_items = {}
    else:
        usernames_items = pywikibot.config.usernames.items()
    for family, usernames in usernames_items:
        if not usernames:
            continue
        pywikibot.info(f"Usernames for family '{family}':")
        for lang, username in usernames.items():
            pywikibot.info(f'\t{lang}: {username}')


if __name__ == '__main__':
    main()
