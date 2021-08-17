"""Classes and functions for working with the Echo extension."""
#
# (C) Pywikibot team, 2014-2020
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from typing import Any, Optional
from pywikibot.backports import Dict
from pywikibot.tools import deprecated

# TODO: replace these after T286867

NOTIFICATION_CLASS_TYPE = Any  # Type['Notification']


class Notification:

    """A notification issued by the Echo extension."""

    def __init__(self, site: 'pywikibot.site.BaseSite') -> None:
        """Initialize an empty Notification object."""
        self.site = site

        self.event_id = None  # type: Optional[int]
        self.type = None
        self.category = None
        self.timestamp = None
        self.page = None
        self.agent = None
        self.read = None  # type: Optional[bool]
        self.content = None
        self.revid = None

    @classmethod
    def fromJSON(cls: NOTIFICATION_CLASS_TYPE,  # noqa: N802
                 site: 'pywikibot.site.BaseSite',
                 data: Dict[str, Any]) -> 'Notification':
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

        notif.content = data.get('*', None)
        notif.revid = data.get('revid', None)
        return notif

    @property  # type: ignore[misc]
    @deprecated('event_id', since='20190106')
    def id(self) -> str:
        """DEPRECATED: Return notification id as unicode."""
        return str(self.event_id)

    def mark_as_read(self) -> bool:
        """Mark the notification as read."""
        return self.site.notifications_mark_read(list=self.id)
