#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""This script reviews or unreviews pages using FlaggedRevs extension.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-review           Review a page revision using FlaggedRevs (default action).

-unreview         Unreview (unapprove) the stable revision of a page using
                  FlaggedRevs.

-pending          Generate pages with pending changes from the FlaggedRevs
                  extension. This is the default generator when reviewing.

-unreviewed       Generate unreviewed pages from the FlaggedRevs extension.

-revid:REVID      Specify the revision ID to review or unreview. If not given,
                  the latest revision is reviewed or the current stable
                  revision is unreviewed.

-flag:FLAG        Set the review flag value (integer).

-refresh          Reload revision and flagged information from the live site.

-summary:REASON   Set the comment / summary for the review or unreview action.

-always           Don't prompt for confirmation, just review or unreview.

**Usage:**

    python pwb.py review [options] [pagegenerators]

**Examples:**

Review pages with pending changes:

    python pwb.py review -pending

Review a specific page:

    python pwb.py review -page:Sandbox

Review a specific revision of a page without prompting:

    python pwb.py review -page:Sandbox -revid:12345 -always

Unreview the stable revision of a page:

    python pwb.py review -unreview -page:Sandbox

Review unreviewed pages with a summary:

    python pwb.py review -unreviewed -summary:"Reviewed latest version"

.. version-added:: 12.0
"""
from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    ConfigParserBot,
    CurrentPageBot,
    SingleSiteBot,
    suggest_help,
)
from pywikibot.data import api
from pywikibot.exceptions import (
    APIError,
    UnexpectedAPIDataError,
    UnknownExtensionError,
    UserRightsError,
)


if TYPE_CHECKING:
    from collections.abc import Iterable


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


def pending_pages_generator(
    site: pywikibot.site.APISite,
    total: int | None = None,
) -> Iterable[pywikibot.Page]:
    """Yield pages with pending changes from FlaggedRevs.

    Attempts to use Special:PendingChanges / Special:Oldreviewedpages
    via :meth:`pywikibot.site.APISite.querypage` if supported, falling
    back to the FlaggedRevs ``oldreviewedpages`` generator API module.

    :param site: The APISite object.
    :param total: Maximum number of pages to return.
    """
    for name in ('Pendingchanges', 'PendingChanges', 'Oldreviewedpages'):
        try:
            return site.querypage(name, total=total)
        except ValueError:
            continue

    return api.PageGenerator('oldreviewedpages', site=site, total=total)


def unreviewed_pages_generator(
    site: pywikibot.site.APISite,
    total: int | None = None,
) -> Iterable[pywikibot.Page]:
    """Yield unreviewed pages from FlaggedRevs.

    Attempts to use Special:UnreviewedPages via
    :meth:`pywikibot.site.APISite.querypage` if supported, falling
    back to the FlaggedRevs ``unreviewedpages`` generator API module.

    :param site: The APISite object.
    :param total: Maximum number of pages to return.
    """
    for name in ('Unreviewedpages', 'UnreviewedPages'):
        try:
            return site.querypage(name, total=total)
        except ValueError:
            continue

    return api.PageGenerator('unreviewedpages', site=site, total=total)


class ReviewBot(SingleSiteBot, ConfigParserBot, CurrentPageBot):

    """Bot to review and unreview pages with FlaggedRevs."""

    update_options = {
        'summary': None,
        'revid': None,
        'flag': None,
        'refresh': False,
        'unreview': False,
    }

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        if self.opt.revid is not None:
            try:
                self.opt.revid = int(self.opt.revid)
            except ValueError as e:
                raise ValueError(
                    f'Invalid -revid option: {self.opt.revid}') from e
        if self.opt.flag is not None:
            try:
                self.opt.flag = int(self.opt.flag)
            except ValueError as e:
                raise ValueError(
                    f'Invalid -flag option: {self.opt.flag}') from e

    def setup(self) -> None:
        """Check whether FlaggedRevs is available on the site."""
        super().setup()
        if not self.site.has_extension('FlaggedRevs'):
            raise UnknownExtensionError(
                f'FlaggedRevs extension is not enabled on {self.site}.')

    def treat_page(self) -> None:
        """Process the current page."""
        page = self.current_page
        if not page.exists():
            pywikibot.warning(
                f'Page {page.title(as_link=True)} does not exist, skipping.')
            return

        is_unreview = self.opt.unreview
        action = 'unreview' if is_unreview else 'review'

        if self.opt.refresh and self.opt.revid is None:
            with suppress(AttributeError):
                if is_unreview:
                    del page.stable_revision_id
                else:
                    del page.latest_revision_id

        if self.opt.revid is not None:
            revid = self.opt.revid
        elif is_unreview:
            revid = page.stable_revision_id
            if revid is None:
                pywikibot.info(
                    f'Page {page.title(as_link=True)} has no stable revision '
                    'to unreview, skipping.')
                return
        else:
            revid = page.latest_revision_id
            if revid is None:
                pywikibot.info(
                    f'Page {page.title(as_link=True)} has no revisions '
                    'to review, skipping.')
                return

        question = (f'Do you want to {action} {page.title(as_link=True)} '
                    f'(revision {revid})?')
        if not self.user_confirm(question):
            return

        try:
            if is_unreview:
                page.unreview(
                    summary=self.opt.summary,
                    revid=revid,
                    refresh=self.opt.refresh,
                )
                self.counter['unreviewed'] += 1
                pywikibot.info(
                    f'Unreviewed {page.title(as_link=True)} (revid {revid})')
            else:
                page.review(
                    summary=self.opt.summary,
                    revid=revid,
                    flag=self.opt.flag,
                    refresh=self.opt.refresh,
                )
                self.counter['reviewed'] += 1
                pywikibot.info(
                    f'Reviewed {page.title(as_link=True)} (revid {revid})')
        except (APIError, UnexpectedAPIDataError, UserRightsError,
                ValueError) as e:
            pywikibot.error(
                f'Failed to {action} {page.title(as_link=True)}: {e}')


def main(*args: str) -> None:
    """Process command line arguments and invoke bot.

    :param args: Command line arguments.
    """
    options = {}
    gen_mode = None
    has_review = False
    has_unreview = False
    has_pending = False
    has_unreviewed = False

    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = gen_factory.handle_args(local_args)

    for arg in local_args:
        opt, _, value = arg.partition(':')
        if opt == '-review':
            has_review = True
            options['unreview'] = False
        elif opt == '-unreview':
            has_unreview = True
            options['unreview'] = True
        elif opt in ('-always', '-refresh'):
            options[opt[1:]] = True
        elif opt == '-revid':
            if not value:
                value = pywikibot.input('Please enter a revision ID:')
            try:
                options['revid'] = int(value)
            except ValueError:
                pywikibot.error(f'Invalid revid parameter: "{value}"')
                return
        elif opt == '-flag':
            if not value:
                value = pywikibot.input('Please enter a flag value:')
            try:
                options['flag'] = int(value)
            except ValueError:
                pywikibot.error(f'Invalid flag parameter: "{value}"')
                return
        elif opt == '-summary':
            options['summary'] = value or pywikibot.input(
                'Please enter a review summary:')
        elif opt == '-pending':
            has_pending = True
        elif opt == '-unreviewed':
            has_unreviewed = True
        else:
            suggest_help(unknown_parameters=[arg])
            return

    if has_review and has_unreview:
        pywikibot.error(
            'The -review and -unreview options cannot be used together.')
        return

    if has_pending and has_unreviewed:
        pywikibot.error(
            'The -pending and -unreviewed options cannot be used together.')
        return

    if has_pending:
        gen_mode = 'pending'
    elif has_unreviewed:
        gen_mode = 'unreviewed'

    site = pywikibot.Site()
    if not site.has_extension('FlaggedRevs'):
        pywikibot.error(
            f'FlaggedRevs extension is not enabled on {site}.')
        return

    gen = None
    if gen_mode == 'pending':
        gen = pending_pages_generator(site)
    elif gen_mode == 'unreviewed':
        gen = unreviewed_pages_generator(site)

    generator = gen_factory.getCombinedGenerator(gen=gen)
    if not generator:
        if options.get('unreview'):
            suggest_help(missing_generator=True)
            return
        generator = gen_factory.getCombinedGenerator(
            gen=pending_pages_generator(site))

    bot = ReviewBot(generator=generator, site=site, **options)
    try:
        bot.run()
    except UnknownExtensionError as e:
        pywikibot.error(str(e))


if __name__ == '__main__':
    main()
