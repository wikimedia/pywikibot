# -*- coding: utf-8  -*-
"""
Robot which runs python framework scripts as (sub-)bot and provides a
WikiUserInterface (WUI) with Lua support for bot operators.

This script needs external libraries (see imports and comments there)
in order to run properly. Most of them can be checked-out at:
    http://svn.toolserver.org/svnroot/drtrigon/
(some code might get compiled on-the-fly, so a GNU compiler along
with library header files is needed too)

The following parameters are supported:

&params;

All other parameters will be ignored.

Syntax example:
    python script_wui.py -dir:.
        Default operating mode.
"""
## @package script_wui
#  @brief   Script WikiUserInterface (WUI) Robot
#
#  @copyright Dr. Trigon, 2012
#
#  @section FRAMEWORK
#
#  Python wikipedia robot framework, DrTrigonBot.
#  @see http://pywikipediabot.sourceforge.net/
#  @see http://de.wikipedia.org/wiki/Benutzer:DrTrigonBot
#
#  @section LICENSE
#
#  Distributed under the terms of the MIT license.
#  @see http://de.wikipedia.org/wiki/MIT-Lizenz
#
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
#  @todo Simulationen werden ausgeführt und das Resultat mit eindeutiger
#        Id (rev-id) auf Ausgabeseite geschrieben, damit kann der Befehl
#        (durch Angabe der Sim-Id) ausgeführt werden -> crontab (!)
#        [ shell (rev-id) -> output mit shell rev-id ]
#        [ shell rev-id (als eindeutige job/task-config bzw. script) -> crontab ]
#  @todo Bei jeder Botbearbeitung wird der Name des Auftraggebers vermerkt
#  @todo (may be queue_security needed later in order to allow other 'super-users' too...)
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
#  Writing code in Wikipedia:
#
#  # patches to keep code running
#  builtin_raw_input = __builtin__.raw_input
#  __builtin__.raw_input = lambda: 'n'     # overwrite 'raw_input' to run bot non-blocking and simulation mode
#
#  # backup sys.argv; depreciated: if possible manipulate pywikibot.config instead
#  sys_argv = copy.deepcopy( sys.argv )
#
#  ...
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
#
__version__       = '$Id$'
__framework_rev__ = '11445'  # check: http://de.wikipedia.org/wiki/Hilfe:MediaWiki/Versionen
__release_ver__   = '1.5.%i' # increase minor (1.x) at re-merges with framework
#


import datetime, time
import thread, threading
import sys, os, traceback, gc, resource
import re

# http://labix.org/lunatic-python
try:
    import lua                  # install f15 packages: 'lua', 'lunatic-python'
except ImportError:
    import dtbext._lua as lua   # TS/labs (debian/ubuntu)
import dtbext.crontab

import pywikibot
import pywikibot.botirc
from pywikibot import version


bot_config = {    'BotName':    pywikibot.config.usernames[pywikibot.config.family][pywikibot.config.mylang],

            # protected !!! ('CSS' or other semi-protected page is essential here)
            'ConfCSSshell':     u'User:DrTrigon/DrTrigonBot/script_wui-shell.css',    # u'User:DrTrigonBot/Simon sagt' ?
            'ConfCSScrontab':   u'User:DrTrigon/DrTrigonBot/script_wui-crontab.css',

            # (may be protected but not that important... 'CSS' is not needed here !!!)
            'ConfCSSoutput':    u'User:DrTrigonBot/Simulation',

            'CRONMaxDelay':     5*60.0,       # check all ~5 minutes

#        'queue_security':       ([u'DrTrigon', u'DrTrigonBot'], u'Bot: exec'),
#        'queue_security':       ([u'DrTrigon'], u'Bot: exec'),

        # supported and allowed bot scripts
        # (at the moment all)

        # forbidden parameters
        # (at the moment none, but consider e.g. '-always' or allow it with '-simulate' only!)
}

__simulate = True
__sys_argv = []


class ScriptWUIBot(pywikibot.botirc.IRCBot):
    def __init__(self, *arg):
        pywikibot.output(u'\03{lightgreen}* Initialization of bot\03{default}')

        pywikibot.botirc.IRCBot.__init__(self, *arg)

        ## modification of timezone to be in sync with wiki
        #os.environ['TZ'] = 'Europe/Amsterdam'
        #time.tzset()
        #pywikibot.output(u'Setting process TimeZone (TZ): %s' % str(time.tzname))    # ('CET', 'CEST')
        #pywikibot.output(u'')

        # init environment with minimal changes (try to do as less as possible)
        # - Lua -
        pywikibot.output(u'** Redirecting Lua print in order to catch it')
        lua.execute('__print = print')
        #lua.execute('print = python.builtins().print')
        lua.execute('print = python.globals().pywikibot.output')

        # init constants
        templ = pywikibot.Page(self.site, bot_config['ConfCSSshell'])
        cron  = pywikibot.Page(self.site, bot_config['ConfCSScrontab'])

        self.templ = templ.title()
        self.cron  = cron.title()
        self.refs  = { self.templ: templ,
                       self.cron:  cron, }
        pywikibot.output(u'** Pre-loading all relevant page contents')
        for item in self.refs:
            # security; first check if page is protected, reject any data if not
            if os.path.splitext(self.refs[item].title().lower())[1] not in ['.css', '.js']:
                raise pywikibot.UserActionRefuse(u'Page %s is not secure, e.g. semi-protected!' % self.refs[item])
            self.refs[item].get(force=True)   # load all page contents

        # init background timer
        pywikibot.output(u'** Starting crontab background timer thread')
        self.on_timer()

    def on_pubmsg(self, c, e):
        match = self.re_edit.match(e.arguments()[0])
        if not match:
            return
        #print match.groups(), match.group('page'), match.group('user')
        user = match.group('user').decode(self.site.encoding())
        if user == bot_config['BotName']:
            return
        # test actual page against (template incl.) list
        page = match.group('page').decode(self.site.encoding())
        if page in self.refs:
            pywikibot.output(u"RELOAD: %s" % page)
            self.refs[page].get(force=True)   # re-load (refresh) page content
        if page == self.templ:
            pywikibot.output(u"SHELL: %s" % page)
            self.do_check(page)

    def on_timer(self):
        self.t = threading.Timer(bot_config['CRONMaxDelay'], self.on_timer)
        self.t.start()

        self.do_check_CronJobs()

    def do_check_CronJobs(self):
        # check cron/date (changes of self.refs are tracked (and reload) in on_pubmsg)
        page    = self.refs[self.templ]
        crontab = self.refs[self.cron].get()
        # extract 'rev' and 'timestmp' from 'crontab' page text ...
        for line in crontab.splitlines():   # hacky/ugly/cheap; already better done in trunk dtbext
            (rev, timestmp) = [item.strip() for item in line[1:].split(',')]

            # [min] [hour] [day of month] [month] [day of week]
            # (date supported only, thus [min] and [hour] dropped)
            entry = dtbext.crontab.CronTab(timestmp)
            # find the delay from current minute (does not return 0.0 - but next)
            delay = entry.next(datetime.datetime.now().replace(second=0,microsecond=0)-datetime.timedelta(microseconds=1))
            #pywikibot.output(u'CRON delay for execution: %.3f (<= %i)' % (delay, bot_config['CRONMaxDelay']))
    
            if (delay <= bot_config['CRONMaxDelay']):
                pywikibot.output(u"CRONTAB: %s / %s / %s" % (page, rev, timestmp))
                self.do_check(page.title(), int(rev))

    def do_check(self, page_title, rev=None, params=None):
        # Create two threads as follows
        # (simple 'thread' for more sophisticated code use 'threading')
        try:
            thread.start_new_thread( main_script, (self.refs[page_title], rev, params) )
        except:
            # (done according to subster in trunk and submit in rewrite/.../data/api.py)
            # TODO: is this error handling here needed at all??!?
            pywikibot.exception(tb=True) # secure traceback print (from api.py submit)
            pywikibot.warning(u"Unable to start thread")

            wiki_logger(traceback.format_exc(), self.refs[page_title], rev)

# Define a function for the thread
def main_script(page, rev=None, params=None):
    # http://opensourcehacker.com/2011/02/23/temporarily-capturing-python-logging-output-to-a-string-buffer/
    # http://docs.python.org/release/2.6/library/logging.html
    from StringIO import StringIO
    import logging

    # safety; default mode is safe (no writing)
    pywikibot.config.simulate = True

    pywikibot.output(u'--- ' * 20)

    buffer = StringIO()
    rootLogger = logging.getLogger()

    logHandler = logging.StreamHandler(buffer)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logHandler.setFormatter(formatter)
    rootLogger.addHandler(logHandler)

    sys.stdout = buffer
    sys.stderr = buffer

    # all output to logging and stdout/stderr is catched BUT NOT lua output (!)
    if rev is None:
        code = page.get()               # shell; "on demand"
    else:
        code = page.getOldVersion(rev)  # crontab; scheduled
    try:
        exec( code )
    except:
        # (done according to subster in trunk and submit in rewrite/.../data/api.py)
        #exc_info = sys.exc_info()
        #tb = traceback.format_exception(exc_info[0], exc_info[1], exc_info[2])
        tb = traceback.format_exc()
        pywikibot.error(tb)    # secure traceback print (from api.py submit)

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    # Remove our handler
    rootLogger.removeHandler(logHandler)

    logHandler.flush()
    buffer.flush()

    pywikibot.output(u'--- ' * 20)

    # safety; restore settings
    pywikibot.config.simulate = __simulate
    sys.argv = __sys_argv

    pywikibot.output(u'environment: garbage; %s / memory; %s / members; %s' % (gc.collect(), resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*resource.getpagesize(), len(dir())))
    # 'len(dir())' is equivalent to 'len(inspect.getmembers(__main__))'

    # append result to output page
    if rev is None:
        wiki_logger(buffer.getvalue(), page, rev)

def wiki_logger(buffer, page, rev=None):
    # (might be a problem here for TS and SGE, output string has another encoding)
    #buffer  = buffer.decode(config.console_encoding)
    buffer = re.sub("\03\{(.*?)\}(.*?)\03\{default\}", "\g<2>", buffer)
    if rev is None:
        rev  = page.latestRevision()
        link = page.permalink(oldid=rev)
    # append to page
    outpage = pywikibot.Page(pywikibot.getSite(), bot_config['ConfCSSoutput'])
    text = outpage.get()
    outpage.put(text + u"\n== Simulation vom %s mit [%s code:%s] ==\n<pre>\n%s</pre>\n\n" % (pywikibot.Timestamp.now().isoformat(' '), link, rev, buffer))
#                comment = pywikibot.translate(self.site.lang, bot_config['msg']))

def main():
    global __simulate, __sys_argv, __release_ver__

    for arg in pywikibot.handleArgs():
        pywikibot.showHelp('script_wui')
        return

    __simulate = pywikibot.config.simulate
    __sys_argv = sys.argv

    # output version info
    __release_ver__ %= version.getversion_svn(pywikibot.config.datafilepath('..'))[1]
    pywikibot.output({'release_ver':          __release_ver__,
                      'framework_ver':        __framework_rev__,
                      'release_online_ver':   version.getversion_onlinerepo('http://svn.toolserver.org/svnroot/drtrigon/'),
                      'framework_online_ver': version.getversion_onlinerepo(),
                       })
    pywikibot.output(u'=== ' * 14)

    site = pywikibot.getSite()
    site.login()
    chan = '#' + site.language() + '.' + site.family.name
    bot = ScriptWUIBot(site, chan, site.user() + "_WUI", "irc.wikimedia.org")
    try:
        bot.start()
    except:
        bot.t.cancel()
        raise

if __name__ == "__main__":
    # run bot
    main()
