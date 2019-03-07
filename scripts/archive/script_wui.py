#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A script to run Pywikibot shell with Lua support from wiki page.

@deprecated: This method is not supported anymore. Use
    U{PAWS<https://www.mediawiki.org/wiki/Manual:Pywikibot/PAWS>}
    instead.

This script runs in the background and tracks changes in the predefined
wiki page for shell – WikiUserInterface (WUI). When a change
is recorded, the contents of the page is interpreted as Pywikibot shell
commands and executed.

The predefined wiki page for crontab sets the shell page contents to
a specified revision in the specified interval.

USAGE

It needs Lua or LuaJIT installed and also external PyPI packages
crontab, irc and lupa in order to run properly. Some code might
get compiled on-the-fly, so a GNU compiler along with library
header files is needed too.

You will need to create the following pages on your wiki.

- User:{username}/script_wui-crontab.css
    This page specifies the commands to execute, one command per line.
    See [[de:Benutzer:DrTrigon/DrTrigonBot/script_wui-shell.css]]
    for example.
- User:{username}/script_wui-shell.css
    This page specifies the schedule to execute specific page revision.
    The following format can be used: revision, timestamp
    See [[de:Benutzer:DrTrigon/DrTrigonBot/script_wui-crontab.css]]
    for example.

Tips for writing code in Wikipedia:

 # patches to keep code running
 builtin_raw_input = __builtin__.raw_input
 # overwrite 'raw_input' to run bot non-blocking and simulation mode
 __builtin__.raw_input = lambda: 'n'

 # backup sys.argv; not recommended, if possible manipulate
 # pywikibot.config instead
 sys_argv = copy.deepcopy( sys.argv )

@todo: Simulationen werden ausgeführt und das Resultat mit eindeutiger
    Id (rev-id) auf Ausgabeseite geschrieben, damit kann der Befehl
    (durch Angabe der Sim-Id) ausgeführt werden -> crontab (!)
    [ shell (rev-id) -> output mit shell rev-id ]
    [ shell rev-id (eindeutige job/task-config bzw. script) -> crontab ]
@todo: Bei jeder Botbearbeitung wird der Name des Auftraggebers vermerkt
"""
#
# (C) Dr. Trigon, 2012-2014
# (C) Pywikibot team, 2013-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import datetime
import gc
import logging
import re
import sys
import threading
import traceback

from io import StringIO

try:
    from lupa import LuaRuntime
    lua = LuaRuntime(unpack_returned_tuples=True)
except ImportError:
    lua = None

# The 'crontab' PyPI package versions 0.20 and 0.20.1 installs
# a package called 'tests' which conflicts with our test suite.
# The patch to fix this has been released in version 0.20.2.
try:
    import crontab
except ImportError:
    crontab = None

import pywikibot
# pywikibot.botirc depends on 'irc' PyPI package
import pywikibot.botirc
from pywikibot.tools.formatter import color_format
from pywikibot.tools import PY2

if not PY2:
    import _thread as thread
else:
    import thread

try:
    import resource
except ImportError:
    resource = None

bot_config = {
    'BotName': '{username}',

    'ConfCSSshell': 'User:{username}/script_wui-shell.css',
    'ConfCSScrontab': 'User:{username}/script_wui-crontab.css',
    'ConfCSSoutput': 'User:{username}/Simulation',

    'CRONMaxDelay': 5 * 60.0,  # check all ~5 minutes

    # forbidden parameters
    # (at the moment none, but consider e.g. '-always' or allow it with
    # '-simulate' only!)
}

__simulate = True
__sys_argv = []


class ScriptWUIBot(pywikibot.botirc.IRCBot):

    """WikiUserInterface bot."""

    def __init__(self, *arg):
        """Initializer."""
        pywikibot.output(color_format(
            '{lightgreen}* Initialization of bot{default}'))

        pywikibot.botirc.IRCBot.__init__(self, *arg)

        # init environment with minimal changes (try to do as less as possible)
        # - Lua -
        if lua:
            pywikibot.output('** Redirecting Lua print in order to catch it')
            lua.execute('__print = print')
            lua.execute('print = python.eval("pywikibot.output")')
            # It may be useful in debugging to install the 'print' builtin
            # as the 'print' function in lua. To do this:
            # lua.execute('print = python.builtins.print')

        # init constants
        templ = pywikibot.Page(self.site, bot_config['ConfCSSshell'])
        cron = pywikibot.Page(self.site, bot_config['ConfCSScrontab'])

        self.templ = templ.title()
        self.cron = cron.title()
        self.refs = {self.templ: templ,
                     self.cron: cron,
                     }
        pywikibot.output('** Pre-loading all relevant page contents')
        for item in self.refs:
            # First check if page is protected, reject any data if not
            parts = self.refs[item].title().lower().rsplit('.')
            if len(parts) == 1 or parts[1] not in ['css', 'js']:
                raise ValueError('{0} config {1} = {2} is not a secure page; '
                                 'it should be a css or js userpage which are '
                                 'automatically semi-protected.'
                                 .format(self.__class__.__name__, item,
                                         self.refs[item]))
            try:
                self.refs[item].get(force=True)  # load all page contents
            except pywikibot.NoPage:
                pywikibot.error("The configuration page {0} doesn't exists"
                                .format(self.refs[item].title(as_link=True)))
                raise
        # init background timer
        pywikibot.output('** Starting crontab background timer thread')
        self.on_timer()

    def on_pubmsg(self, c, e):
        match = self.re_edit.match(e.arguments[0])
        if not match:
            return
        user = match.group('user')
        if user == bot_config['BotName']:
            return
        # test actual page against (template incl.) list
        page = match.group('page')
        if page in self.refs:
            pywikibot.output('RELOAD: ' + page)
            self.refs[page].get(force=True)  # re-load (refresh) page content
        if page == self.templ:
            pywikibot.output('SHELL: ' + page)
            self.do_check(page)

    def on_timer(self):
        self.t = threading.Timer(bot_config['CRONMaxDelay'], self.on_timer)
        self.t.start()

        self.do_check_CronJobs()

    def do_check_CronJobs(self):
        # check cron/date (changes of self.refs are tracked (and reload) in
        # on_pubmsg)
        page = self.refs[self.templ]
        ctab = self.refs[self.cron].get()
        # extract 'rev' and 'timestmp' from 'crontab' page text ...

        # hacky/ugly/cheap
        for line in ctab.splitlines():
            (rev, timestmp) = [item.strip() for item in line[1:].split(',')]

            # [min] [hour] [day of month] [month] [day of week]
            # (date supported only, thus [min] and [hour] dropped)
            if not crontab:
                pywikibot.error(
                    '"crontab" library is needed to run the script properly.')
                return None
            entry = crontab.CronTab(timestmp)
            # find the delay from current minute
            # (does not return 0.0 - but next)
            now = datetime.datetime.now().replace(second=0, microsecond=0)
            delay = entry.next(
                now - datetime.timedelta(microseconds=1))

            if (delay <= bot_config['CRONMaxDelay']):
                pywikibot.output('CRONTAB: %s / %s / %s' %
                                 (page, rev, timestmp))
                self.do_check(page.title(), int(rev))

    def do_check(self, page_title, rev=None, params=None):
        # Create two threads as follows
        # (simple 'thread' for more sophisticated code use 'threading')
        try:
            thread.start_new_thread(main_script, (self.refs[page_title], rev,
                                                  params))
        except Exception:
            # (done according to subster.py from compat and submitted in
            # pywikibot/data/api.py)
            # TODO: is this error handling here needed at all??!?

            # secure traceback print (from api.py submit)
            pywikibot.exception(tb=True)
            pywikibot.warning('Unable to start thread')

            wiki_logger(traceback.format_exc(), self.refs[page_title], rev)


# Define a function for the thread

def main_script(page, rev=None, params=NotImplemented):
    """Main thread."""
    # http://opensourcehacker.com/2011/02/23/temporarily-capturing-python-logging-output-to-a-string-buffer/

    # safety; default mode is safe (no writing)
    pywikibot.config.simulate = True

    pywikibot.output('--- ' * 20)

    buffer = StringIO()
    rootLogger = logging.getLogger()

    logHandler = logging.StreamHandler(buffer)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logHandler.setFormatter(formatter)
    rootLogger.addHandler(logHandler)

    sys.stdout = buffer
    sys.stderr = buffer

    # all output to logging and stdout/stderr is caught BUT NOT lua output (!)
    if rev is None:
        code = page.get()               # shell; "on demand"
    else:
        code = page.getOldVersion(rev)  # crontab; scheduled
    try:
        exec(code)
    except Exception:
        # (done according to subster.py from compat and submitted in
        # pywikibot/data/api.py)

        # secure traceback print (from api.py submit)
        pywikibot.exception(tb=True)

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    # Remove our handler
    rootLogger.removeHandler(logHandler)

    logHandler.flush()
    buffer.flush()

    pywikibot.output('--- ' * 20)

    # safety; restore settings
    pywikibot.config.simulate = __simulate
    sys.argv = __sys_argv
    if resource:
        pywikibot.output(
            'environment: garbage; %s / memory; %s / members; %s' % (
                gc.collect(),
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                * resource.getpagesize(),
                len(dir())))
    else:
        pywikibot.output(
            'environment: garbage; %s / members; %s' % (
                gc.collect(), len(dir())))
    # 'len(dir())' is equivalent to 'len(inspect.getmembers(__main__))'

    # append result to output page
    if rev is None:
        wiki_logger(buffer.getvalue(), page, rev)


def wiki_logger(buffer, page, rev=None):
    """Log to wiki."""
    buffer = re.sub(r'\03\{(.*?)\}(.*?)\03\{default\}', r'\g<2>', buffer)
    if rev is None:
        rev = page.latestRevision()
        link = page.permalink(oldid=rev)
    # append to page
    outpage = pywikibot.Page(pywikibot.Site(), bot_config['ConfCSSoutput'])
    text = outpage.text
    outpage.put(
        text + ('\n== Simulation vom %s mit [%s code:%s] =='
                '\n<pre>\n%s</pre>\n\n')
        % (pywikibot.Timestamp.now().isoformat(' '), link, rev, buffer))
#        summary=pywikibot.translate(self.site.lang, bot_config['msg']))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    global __simulate, __sys_argv

    unknown_args = pywikibot.handle_args(args)
    if unknown_args:
        pywikibot.bot.suggest_help(unknown_parameters=unknown_args)
        return False

    __simulate = pywikibot.config.simulate
    __sys_argv = sys.argv

    site = pywikibot.Site()
    site.login()
    chan = '#' + site.code + '.' + site.family.name

    bot_user_name = pywikibot.config.usernames[pywikibot.config.family][
        pywikibot.config.mylang]
    for key, value in bot_config.items():
        if hasattr(value, 'format'):
            bot_config[key] = value.format(username=bot_user_name)

    bot = ScriptWUIBot(site, chan, site.user() + '_WUI', 'irc.wikimedia.org')
    try:
        bot.start()
    except BaseException:
        bot.t.cancel()
        raise
    return True


if __name__ == '__main__':
    main()
