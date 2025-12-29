"""Classes and functions for working with the Echo extension."""
#
# (C) Pywikibot team, 2014-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pywikibot


@dataclass(eq=False)
class Notification:

    """A notification issued by the Echo extension.

    .. versionchanged:: 3.0.20190204
       The ``id`` attribute was renamed to ``event_id``, and its type
       changed from ``str`` to ``int``.

    .. deprecated:: 3.0.20190204
       The ``id`` attribute was retained temporarily for backward
       compatibility, but is deprecated and scheduled for removal.

    .. versionremoved:: 7.0
       The ``id`` attribute was removed.

    .. versionchanged:: 10.3
       The class is now defined using the ``@dataclass`` decorator to
       simplify internal initialization and improve maintainability.
    """

    site: pywikibot.site.BaseSite

    def __post_init__(self) -> None:
        """Initialize attributes for an empty Notification object.

        .. versionadded: 10.3
        """
        self.event_id: int | None = None
        self.type = None
        self.category = None
        self.timestamp: pywikibot.Timestamp | None = None
        self.page: pywikibot.Page | None = None
        self.agent: pywikibot.User | None = None
        self.read: pywikibot.Timestamp | bool | None = None
        self.content = None
        self.revid = None

    @classmethod
    def fromJSON(cls,  # noqa: N802
                 site: pywikibot.site.BaseSite,
                 data: dict[str, Any]) -> Notification:
        """Construct a Notification object from API JSON data.

        :param site: The pywikibot site object.
        :param data: The JSON data dictionary representing a
            notification.
        :return: An instance of Notification.
        """
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
        """Mark the notification as read.

        :return: True if the notification was successfully marked as
            read, else False.
        """
        if self.event_id is None:
            return False

        return self.site.notifications_mark_read(**{'list': self.event_id})
