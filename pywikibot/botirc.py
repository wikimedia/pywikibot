# -*- coding: utf-8  -*-
"""
User-interface related functions for building bots

Note: the script requires the Python IRC library
http://python-irclib.sourceforge.net/
"""
#
# (C) Balasyum
# (C) Pywikipedia bot team, 2008-2012
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

# Note: the intention is to develop this module (at some point) into a Bot
# class definition that can be subclassed to create new, functional bot
# scripts, instead of writing each one from scratch.


import logging, logging.handlers
       # all output goes thru python std library "logging" module
import re

from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad
from irclib import ip_quad_to_numstr

# logging levels
_logger = "botirc"

from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
STDOUT = 16
VERBOSE = 18
INPUT = 25

import pywikibot


class IRCBot(pywikibot.Bot, SingleServerIRCBot):
    """
    Generic IRC Bot to be subclassed

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
        pywikibot.Bot.__init__(self, **kwargs)
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.site = site
        self.other_ns = re.compile(
            u'14\[\[07(' + u'|'.join([item[0] for item in site.namespaces().values() if item[0]]) + u')')
        self.api_url = self.site.family.apipath(self.site.lang)
        self.api_url += '?action=query&meta=siteinfo&siprop=statistics&format=xml'
        self.api_found = re.compile(r'articles="(.*?)"')
        self.re_edit = re.compile(
            r'^C14\[\[^C07(?P<page>.+?)^C14\]\]^C4 (?P<flags>.*?)^C10 ^C02(?P<url>.+?)^C ^C5\*^C ^C03(?P<user>.+?)^C ^C5\*^C \(?^B?(?P<bytes>[+-]?\d+?)^B?\) ^C10(?P<summary>.*)^C'.replace('^B', '\002').replace('^C', '\003').replace('^U', '\037'))

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        pass

    def on_pubmsg(self, c, e):
        match = self.re_edit.match(e.arguments()[0])
        if not match:
                return
        if not ('N' in match.group('flags')):
                return
        try:
            msg = unicode(e.arguments()[0],'utf-8')
        except UnicodeDecodeError:
            return
        if self.other_ns.match(msg):
            return
        name = msg[8:msg.find(u'14',9)]
        text = pywikibot.comms.http.request(self.site, self.api_url)
        entry = self.api_found.findall(text)
        page = pywikibot.Page(self.site, name)
        try:
                text = page.get()
        except pywikibot.NoPage:
                return
        except pywikibot.IsRedirectPage:
                return
        print entry[0], name

    def on_dccmsg(self, c, e):
        pass

    def on_dccchat(self, c, e):
        pass

    def do_command(self, e, cmd):
        pass

    def on_quit(self, e, cmd):
        pass
