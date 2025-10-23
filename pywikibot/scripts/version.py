#!/usr/bin/env python3
"""Script to determine the Pywikibot version (tag, revision and date).

The following option is supported:

-nouser  do not print usernames; otherwise they are printed for each
         registered family

.. versionchanged:: 7.0
   version script was moved to the framework scripts folder.
.. versionadded:: 9.1.2
   the *-nouser* option was added.
.. versionchanged:: 10.6
   The User-Agent string is now printed for the default site. To print
   it for another site, call the ``pwb`` wrapper with the global option,
   e.g.:

       pwb -site:wikipedia:test version

   .. note::
      The shown UA reflects the default config settings. It might differ
      if a user-agent is passed via the *headers* parameter to
      :func:`comms.http.request`, :func:`comms.http.fetch` or to
      :class:`comms.eventstreams.EventStreams`. It can also differ if
      :func:`comms.http.fetch` is used with *use_fake_user_agent* set to
      ``True`` or to a custom UA string, or if
      *fake_user_agent_exceptions* is defined in the :mod:`config` file.
"""
#
# (C) Pywikibot team, 2007-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import os
import sys
from pathlib import Path

import pywikibot
from pywikibot.comms.http import user_agent
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
    else:
        cert = Path(requests.certs.where())
        # is_symlink() required for Python 3.12 and below.
        # Otherwise follow_symlinks=True could be used in is_file().
        if not cert.is_file() or cert.is_symlink():
            pywikibot.info(f'  cacerts: {cert.name} (missing)')
        else:
            pywikibot.info(f'  cacerts: {cert}')
            text = cert.read_text(encoding='utf-8')
            if WMF_CACERT in text:
                has_wikimedia_cert = True
            pywikibot.info('    certificate test: {}'
                           .format('ok' if has_wikimedia_cert else 'not ok'))

    if not has_wikimedia_cert:
        pywikibot.info('  Please reinstall requests!')

    pywikibot.info('Python: ' + sys.version)
    pywikibot.info('User-Agent: ' + user_agent(pywikibot.Site()))

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
