# -*- coding: utf-8 -*-
"""
WARNING: THIS MODULE EXISTS SOLELY TO PROVIDE BACKWARDS-COMPATIBILITY.

IT MAY BE REMOVED SOON.

Deprecated user-interface related functions for building bots.

@note: the script requires the irc library
"""
#
# (C) Balasyum, 2008
# (C) Pywikibot team, 2008-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import re

import pywikibot
from pywikibot.tools import ModuleDeprecationWrapper

try:
    from irc.bot import SingleServerIRCBot
except ImportError as e:
    ircbot_import_error = e

    class SingleServerIRCBot(object):

        """Fake SingleServerIRCBot."""

        def __init__(*args, **kwargs):
            """Report import exception."""
            raise ircbot_import_error


_logger = 'botirc'
__all__ = ('IRCBot',)


class IRCBot(pywikibot.Bot, SingleServerIRCBot):

    """
    A generic IRC Bot to be subclassed.

    A Bot that displays the ordinal number of the new articles being created
    visible on the Recent Changes list. The Bot doesn't make any edits, no
    account needed.
    """

    # Bot configuration.
    # Only the keys of the dict can be passed as keyword arguments
    # The values are the default values
    availableOptions = {}  # noqa: N815

    def __init__(self, site, channel, nickname, server, port=6667, **kwargs):
        """Initializer."""
        pywikibot.Bot.__init__(self, **kwargs)
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.site = site
        self.other_ns = re.compile(
            '\x0314\\[\\[\x0307(%s)'
            % '|'.join(item.custom_name for item in site.namespaces.values()
                       if item != 0))
        self.api_url = (
            self.site.apipath()
            + '?action=query&meta=siteinfo&siprop=statistics&format=xml')
        self.api_found = re.compile(r'articles="(.*?)"')
        self.re_edit = re.compile(
            r'^C14\[\[^C07(?P<page>.+?)^C14\]\]^C4 (?P<flags>.*?)^C10 ^C02'
            r'(?P<url>.+?)^C ^C5\*^C ^C03(?P<user>.+?)^C ^C5\*^C \(?^B?'
            r'(?P<bytes>[+-]?\d+?)^B?\) ^C10(?P<summary>.*)^C'
            .replace('^B', '\002').replace('^C', '\003').replace('^U', '\037'))

    def on_nicknameinuse(self, c, e):
        """Provide an alternative nickname."""
        c.nick(c.get_nickname() + '_')

    def on_welcome(self, c, e):
        """Join channel."""
        c.join(self.channel)

    def on_privmsg(self, c, e):
        """Ignore private message."""
        pass

    def on_pubmsg(self, c, e):
        """Respond to public message."""
        match = self.re_edit.match(e.arguments()[0])
        if not match:
            return
        if not ('N' in match.group('flags')):
            return
        try:
            msg = e.arguments()[0].decode('utf-8')
        except UnicodeDecodeError:
            return
        if self.other_ns.match(msg):
            return
        name = msg[8:msg.find('14', 9)]
        text = pywikibot.comms.http.request(self.site, self.api_url)
        entry = self.api_found.findall(text)
        page = pywikibot.Page(self.site, name)
        try:
            page.get()
        except pywikibot.NoPage:
            return
        except pywikibot.IsRedirectPage:
            return
        pywikibot.output(str((entry[0], name)))

    def on_dccmsg(self, c, e):
        """Ignore DCC message."""
        pass

    def on_dccchat(self, c, e):
        """Ignore DCC chat."""
        pass

    def do_command(self, e, cmd):
        """Ignore command request."""
        pass

    def on_quit(self, e, cmd):
        """Ignore quit request."""
        pass


wrapper = ModuleDeprecationWrapper(__name__)
wrapper._add_deprecated_attr(
    'IRCBot',
    replacement_name=('irc.bot.SingleServerIRCBot from irc library '
                      'or EventStreams'),
    since='20190509',
    future_warning=True)
