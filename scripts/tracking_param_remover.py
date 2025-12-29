#!/usr/bin/env python3
"""Script to remove tracking URL query parameters from external URLs.

These command line parameters can be used to specify which pages to work
on:

&params;

Furthermore, the following command line parameters are supported:

-always           Don't prompt for each removal

.. versionadded:: 10.3
"""
#
# (C) Pywikibot team, 2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import re
import urllib

import mwparserfromhell

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import AutomaticTWSummaryBot, ExistingPageBot, SingleSiteBot


docuReplacements = {  # noqa: N816
    '&params;': pagegenerators.parameterHelp,
}

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

        :param url: The URL to check
        :returns: URL as string
        """
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

        new_url = urllib.parse.urlunparse(url._replace(query=new_query))

        return new_url

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
