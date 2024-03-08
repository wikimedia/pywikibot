"""Classes and functions for working with the Echo extension."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from typing import Any

import pywikibot


class Notification:

    """A notification issued by the Echo extension."""

    def __init__(self, site: pywikibot.site.BaseSite) -> None:
        """Initialize an empty Notification object."""
        self.site = site

        self.event_id: int | None = None
        self.type = None
        self.category = None
        self.timestamp = None
        self.page = None
        self.agent = None
        self.read: bool | None = None
        self.content = None
        self.revid = None

    @classmethod
    def fromJSON(cls,  # noqa: N802
                 site: pywikibot.site.BaseSite,
                 data: dict[str, Any]) -> Notification:
        """Construct a Notification object from our API's JSON data."""
        notif = cls(site)

        notif.event_id = int(data['id'])
        notif.type = data['type']
        notif.category = data['category']
        notif.timestamp = pywikibot.Timestamp.fromtimestampformat(
            data['timestamp']['mw'])

        try:
            notif.page = pywikibot.Page(site, data['title']['full'])
        except KeyError:
            notif.page = None

        try:
            notif.agent = pywikibot.User(site, data['agent']['name'])
        except KeyError:
            notif.agent = None

        try:
            notif.read = pywikibot.Timestamp.fromtimestampformat(data['read'])
        except KeyError:
            notif.read = False

        notif.content = data.get('*')
        notif.revid = data.get('revid')
        return notif

    def mark_as_read(self) -> bool:
        """Mark the notification as read."""
        return self.site.notifications_mark_read(list=self.id)
