# -*- coding: utf-8 -*-
"""
User-interface related functions for building bots.

Note: the script requires the Python IRC library
http://python-irclib.sourceforge.net/
"""
#
# (C) Balasyum, 2008
# (C) Pywikibot team, 2008-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

# Note: the intention is to develop this module (at some point) into a Bot
# class definition that can be subclassed to create new, functional bot
# scripts, instead of writing each one from scratch.


import re

import pywikibot

try:
    from ircbot import SingleServerIRCBot
except ImportError as e:
    ircbot_import_error = e

    class SingleServerIRCBot(object):

        """Fake SingleServerIRCBot."""

        def __init__(*args, **kwargs):
            """Report import exception."""
            raise ircbot_import_error


_logger = "botirc"


class IRCBot(pywikibot.Bot, SingleServerIRCBot):

    """
    A generic IRC Bot to be subclassed.

    A Bot that displays the ordinal number of the new articles being created
    visible on the Recent Changes list. The Bot doesn't make any edits, no
    account needed.
    """

    # Bot configuration.
    # Only the keys of the dict can be passed as init options
    # The values are the default values
    # Extend this in subclasses!
    availableOptions = {
    }

    def __init__(self, site, channel, nickname, server, port=6667, **kwargs):
        """Constructor."""
        pywikibot.Bot.__init__(self, **kwargs)
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.site = site
        self.other_ns = re.compile(
            u'\x0314\\[\\[\x0307(%s)'
            % u'|'.join(item.custom_name for item in site.namespaces.values()
                        if item != 0))
        self.api_url = self.site.apipath()
        self.api_url += '?action=query&meta=siteinfo&siprop=statistics&format=xml'
        self.api_found = re.compile(r'articles="(.*?)"')
        self.re_edit = re.compile(
            r'^C14\[\[^C07(?P<page>.+?)^C14\]\]^C4 (?P<flags>.*?)^C10 ^C02'
            r'(?P<url>.+?)^C ^C5\*^C ^C03(?P<user>.+?)^C ^C5\*^C \(?^B?'
            r'(?P<bytes>[+-]?\d+?)^B?\) ^C10(?P<summary>.*)^C'
            .replace('^B', '\002').replace('^C', '\003').replace('^U', '\037'))

    def on_nicknameinuse(self, c, e):
        """Provide an alternative nickname."""
        c.nick(c.get_nickname() + "_")

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
        name = msg[8:msg.find(u'14', 9)]
        text = pywikibot.comms.http.request(self.site, self.api_url)
        entry = self.api_found.findall(text)
        page = pywikibot.Page(self.site, name)
        try:
            text = page.get()
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
