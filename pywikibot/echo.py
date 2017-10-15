# -*- coding: utf-8 -*-
"""Classes and functions for working with the Echo extension."""
#
# (C) Pywikibot team, 2014-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot


class Notification(object):

    """A notification issued by the Echo extension."""

    def __init__(self, site):
        """Construct an empty Notification object."""
        self.site = site

    @classmethod
    def fromJSON(cls, site, data):
        """
        Construct a Notification object from JSON data returned by the API.

        @rtype: Notification
        """
        notif = cls(site)

        notif.id = data['id']  # TODO: use numeric id ?
        notif.type = data['type']
        notif.category = data['category']
        notif.timestamp = pywikibot.Timestamp.fromtimestampformat(data['timestamp']['mw'])

        if 'title' in data and 'full' in data['title']:
            notif.page = pywikibot.Page(site, data['title']['full'])
        else:
            notif.page = None

        if 'agent' in data and 'name' in data['agent']:
            notif.agent = pywikibot.User(site, data['agent']['name'])
        else:
            notif.agent = None

        if 'read' in data:
            notif.read = pywikibot.Timestamp.fromtimestampformat(data['read'])
        else:
            notif.read = False

        notif.content = data.get('*', None)
        notif.revid = data.get('revid', None)

        return notif

    def mark_as_read(self):
        """Mark the notification as read."""
        return self.site.notifications_mark_read(list=self.id)
