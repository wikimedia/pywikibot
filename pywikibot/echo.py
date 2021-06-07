"""Classes and functions for working with the Echo extension."""
#
# (C) Pywikibot team, 2014-2020
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot.tools import deprecated


class Notification:

    """A notification issued by the Echo extension."""

    def __init__(self, site):
        """Initialize an empty Notification object."""
        self.site = site

    @classmethod
    def fromJSON(cls, site, data):  # noqa: N802
        """
        Construct a Notification object from JSON data returned by the API.

        :rtype: Notification
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

        notif.content = data.get('*', None)
        notif.revid = data.get('revid', None)
        return notif

    @property
    @deprecated('event_id', since='20190106')
    def id(self):
        """
        DEPRECATED: Return notification id as unicode.

        :rtype: str
        """
        return str(self.event_id)

    def mark_as_read(self):
        """Mark the notification as read."""
        return self.site.notifications_mark_read(list=self.id)
