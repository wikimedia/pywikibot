#!/usr/bin/env python3
#
# (C) Pywikibot team, 2025-2026
#
# Distributed under the terms of the MIT license.
#
"""Script to remove tracking URL query parameters from external URLs.

These command line parameters can be used to specify which pages to work
on:

&params;

Furthermore, the following command line parameters are supported:

-always           Don't prompt for each removal

.. version-added:: 10.3
"""
from __future__ import annotations

import re
import urllib

import mwparserfromhell

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import AutomaticTWSummaryBot, ExistingPageBot, SingleSiteBot
from pywikibot.tools import THREADING_FREE


docuReplacements = {  # noqa: N816
    '&params;': pagegenerators.parameterHelp,
}

if THREADING_FREE:
    # The C tokenizer is not safe without the GIL (T435717).
    mwparserfromhell.parser.use_c = False

KNOWN_TRACKER_PARAMS = [
    'utm_.+',  # universal
    'fbclid',  # Facebook
    'gad_.+',  # Google
    'gclid',  # Google
    '[gw]braid',  # Google
    'li_fat_id',  # LinkedIn
    'mc_.+',  # Mailchimp
    'pk_.+',  # Matomo / Piwik
    'msclkid',  # Microsoft
    'epik',  # Pinterest
    'scid',  # Snapchat
    'ttclid',  # TikTok
    'twclid',  # Twitter / X
    'vero_.+',  # Vero
    'wprov',  # Wikimedia / MediaWiki
    '_openstat',  # Yandex
    'yclid',  # Yandex
    'si',  # YouTube, Spotify
]

KNOWN_TRACKER_REGEX = re.compile(rf'({"|".join(KNOWN_TRACKER_PARAMS)})')

# Archive hosts whose query strings must be preserved (T410853).
ARCHIVE_HOSTS = (
    'web.archive.org',
    'archive.is',
    'archive.ph',
    'archive.today',
)


def is_archive_url(url: urllib.parse.ParseResult) -> bool:
    """Return True if *url* points to a known web-archive host.

    Matches netloc exactly or as a subdomain of an archive host
    (case-insensitive). Also treats Internet Archive Wayback Machine
    paths under ``/web/`` on archive.org hosts as archives.

    .. version-added:: 11.8
    """
    netloc = (url.netloc or '').lower()
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    for host in ARCHIVE_HOSTS:
        if netloc == host or netloc.endswith('.' + host):
            return True
    # Wayback Machine style paths on archive.org (optional path check)
    if netloc == 'archive.org' or netloc.endswith('.archive.org'):
        path = url.path or ''
        if path.startswith('/web/') or '/web/' in path:
            return True
    return False


class TrackingParamRemoverBot(
    SingleSiteBot,
    AutomaticTWSummaryBot,
    ExistingPageBot
):

    """Bot to remove tracking URL parameters."""

    summary_key = 'tracking_param_remover-removing'

    @staticmethod
    def remove_tracking_params(url: urllib.parse.ParseResult) -> str:
        """Remove tracking query parameters if they are present.

        Tracking parameters on archive URLs are left unchanged so that
        archived snapshots remain functional (T410853).

        :param url: The URL to check
        :returns: URL as string
        """
        if is_archive_url(url):
            return urllib.parse.urlunparse(url)

        filtered_params = []

        tracker_present = False
        for k, v in urllib.parse.parse_qsl(url.query, keep_blank_values=True):
            if KNOWN_TRACKER_REGEX.fullmatch(k):
                tracker_present = True
            else:
                filtered_params.append((k, v))

        if not tracker_present:
            # Return the original URL if no tracker parameters were present
            return urllib.parse.urlunparse(url)

        new_query = urllib.parse.urlencode(filtered_params)
        return urllib.parse.urlunparse(url._replace(query=new_query))

    def treat_page(self) -> None:
        """Treat a page."""
        wikicode = mwparserfromhell.parse(self.current_page.text)

        for link in wikicode.ifilter_external_links():
            parsed_url = urllib.parse.urlparse(str(link.url))
            if not parsed_url.query:
                continue
            tracking_params_removed = self.remove_tracking_params(parsed_url)
            if urllib.parse.urlunparse(parsed_url) == tracking_params_removed:
                # Continue if no parameters were removed
                continue
            wikicode.replace(link.url, tracking_params_removed)

        self.put_current(wikicode)


def main(*args: str) -> None:
    """Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    script_args = gen_factory.handle_args(local_args)

    for arg in script_args:
        opt, _, value = arg.partition(':')
        if opt == '-always':
            options['always'] = True

    site = pywikibot.Site()

    gen = gen_factory.getCombinedGenerator(preload=True)
    bot = TrackingParamRemoverBot(generator=gen, **options)
    site.login()
    bot.run()


if __name__ == '__main__':
    main()
