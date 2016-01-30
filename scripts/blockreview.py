#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This bot implements a blocking review process for de-wiki first.

For other sites this bot script must be changed.

This script is run by [[de:User:xqt]]. It should
not be run by other users without prior contact.
"""
#
# (C) xqt, 2010-2016
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import pywikibot

from pywikibot import i18n
from pywikibot.bot import ExistingPageBot, SingleSiteBot
from pywikibot import pagegenerators as pg


class BlockreviewBot(ExistingPageBot, SingleSiteBot):

    """Block review bot."""

    # notes
    note_admin = {
        'de': u"\n\n== Sperrprüfungswunsch ==\nHallo %(admin)s,\n\n[[%(user)s]]"
              u" wünscht die Prüfung seiner/ihrer Sperre vom %(time)s über die "
              u"Dauer von %(duration)s. Kommentar war ''%(comment)s''. "
              u"Bitte äußere Dich dazu auf der [[%(usertalk)s#%(section)s|"
              u"Diskussionsseite]]. -~~~~"""
    }

    note_project = {
        'de': u"\n\n== [[%(user)s]] ==\n* gesperrt am %(time)s durch "
              u"{{Benutzer|%(admin)s}} für eine Dauer von %(duration)s.\n"
              u"* Kommentar war ''%(comment)s''.\n* [[Benutzer:%(admin)s]]"
              u" wurde [[Benutzer Diskussion:%(admin)s#Sperrprüfungswunsch|"
              u"benachrichtigt]].\n* [[%(usertalk)s#%(section)s|Link zur "
              u"Diskussion]]\n\n:<small>-~~~~</small>\n\n;Antrag entgegengenommen"
    }

    # edit summaries
    msg_admin = {
        'de': u'Bot-Benachrichtigung: Sperrprüfungswunsch von [[%(user)s]]',
    }

    msg_user = {
        'de': 'Bot: Administrator [[Benutzer:%(admin)s|%(admin)s]] für '
              'Sperrprüfung benachrichtigt',
    }

    msg_done = {
        'de': u'Bot: Sperrprüfung abgeschlossen. Benutzer ist entsperrt.',
    }

    unblock_tpl = {
        'de': u'Benutzer:TAXman/Sperrprüfungsverfahren',
        'pt': u'Predefinição:Discussão de bloqueio',
    }

    review_cat = {
        'de': u'Wikipedia:Sperrprüfung',
    }

    project_name = {
        'de': u'Benutzer:TAXman/Sperrprüfung Neu',
        'pt': u'Wikipedia:Pedidos a administradores/Discussão de bloqueio',
    }

    section_header = {
        'de': 'Sperrprüfung',
    }

    def __init__(self, **kwargs):
        """Constructor."""
        super(BlockreviewBot, self).__init__(**kwargs)
        self.info = None
        self.parts = None

    @property
    def generator(self):
        """Generator method."""
        try:
            genPage = pywikibot.Page(self.site,
                                     self.unblock_tpl[self.site.code],
                                     ns=10)
        except KeyError:
            pywikibot.error(u'Language "%s" not supported by this bot.'
                            % self.site.code)
            raise SystemExit
        return genPage.getReferences(follow_redirects=False,
                                     withTemplateInclusion=True,
                                     onlyTemplateInclusion=True,
                                     namespaces=3)

    def exit(self):
        """Finally print a comment."""
        if self._treat_counter == 0:
            pywikibot.output('Nothing left to do.')
        else:
            super(BlockreviewBot, self).exit()

    def treat_page(self):
        """Load the current page, do some changes, and save it."""
        talkText = self.current_page.text
        if not talkText:
            # sanity check. No talk page found.
            return
        unblock_tpl = self.unblock_tpl[self.site.code]
        project_name = self.project_name[self.site.code]
        user = pywikibot.User(self.site,
                              self.current_page.title(withNamespace=False))
        # saveAdmin = saveProject = False
        talkComment = None
        for templates in self.current_page.templatesWithParams():
            if templates[0].title() == unblock_tpl:
                if not self.getInfo(user):
                    pywikibot.output('No block entry found. Skipping')
                    # TODO: Notify user or delete template
                    continue
                # Step 1
                # a new template is set on blocked users talk page.
                # Notify the blocking admin
                if templates[1] == [] or templates[1][0] == u'1':
                    if self.info['action'] == 'block' or user.isBlocked():
                        if self.site.sitename == 'wikipedia:de':
                            admin = pywikibot.User(self.site,
                                                   user.getprops()['blockedby'])
                            assert admin == self.info.user(), (
                                "Blocking admin doesn't match user property")
                            adminPage = admin.getUserTalkPage()
                            adminText = adminPage.text
                            note = i18n.translate(self.site.code,
                                                  self.note_admin,
                                                  self.parts)
                            comment = i18n.translate(self.site.code,
                                                     self.msg_admin,
                                                     self.parts)
                            adminText += note
                            self.userPut(adminPage, adminPage.text, adminText,
                                         summary=comment, minorEdit=False,
                                         ignore_save_related_errors=True)
                        # test for pt-wiki
                        # just print all sysops talk pages
                        elif self.site.sitename == 'wikipedia:pt':
                            gen = pg.PreloadingGenerator(self.SysopGenerator())
                            for sysop in gen:
                                pywikibot.output(sysop.title())

                        talkText = talkText.replace(u'{{%s}}' % unblock_tpl,
                                                    u'{{%s|2}}' % unblock_tpl)
                        talkText = talkText.replace(u'{{%s|1}}' % unblock_tpl,
                                                    u'{{%s|2}}' % unblock_tpl)
                        talkComment = i18n.translate(self.site.code,
                                                     self.msg_user
                                                     % self.parts)

                        # some test stuff
                        if self.site.user() == u'Xqbot':
                            testPage = pywikibot.Page(self.site,
                                                      'Benutzer:Xqt/Test')
                            test = testPage.get()
                            test += note
                            self.userPut(testPage, testPage.text, test,
                                         summary='[[WP:BA#SPP-Bot|SPPB-Test]]',
                                         ignore_save_related_errors=True)
                    else:
                        # nicht blockiert. Fall auf DS abschließen
                        talkText = talkText.replace(u'{{%s}}' % unblock_tpl,
                                                    u'{{%s|4}}' % unblock_tpl)
                        talkText = talkText.replace(u'{{%s|1}}' % unblock_tpl,
                                                    u'{{%s|4}}' % unblock_tpl)
                        talkComment = i18n.translate(self.site.code,
                                                     self.msg_done)
                # Step 2
                # Admin has been notified.
                # Wait for 2 hours, than put a message to the project page
                elif templates[1][0] == u'2':
                    if self.info['action'] == 'block' or user.isBlocked():
                        # TODO: check whether wait time is gone
                        #       check whether this entry already esists
                        project = pywikibot.Page(self.site, project_name)
                        projText = project.get()
                        note = i18n.translate(self.site.code,
                                              self.note_project,
                                              self.parts)
                        comment = i18n.translate(self.site.code,
                                                 self.msg_admin,
                                                 self.parts)
                        projText += note
                        self.userPut(project, project.text, projText,
                                     summary=comment, botflag=False,
                                     ignore_save_related_errors=True)
                        talkText = talkText.replace(u'{{%s|2}}' % unblock_tpl,
                                                    u'{{%s|3}}' % unblock_tpl)
                        talkComment = u'Bot: [[%s|Wikipedia:Sperrprüfung]] eingetragen' \
                                      % project_name
                    else:
                        # User is unblocked. Review can be closed
                        talkText = talkText.replace(u'{{%s|2}}' % unblock_tpl,
                                                    u'{{%s|4}}' % unblock_tpl)
                        talkComment = i18n.translate(self.site.code,
                                                     self.msg_done)
                # Step 3
                # Admin is notified, central project page has a message
                # Discussion is going on
                # Check whether it can be closed
                elif templates[1][0] == u'3':
                    if self.info['action'] == 'block' or user.isBlocked():
                        pass
                    else:
                        # User is unblocked. Review can be closed
                        talkText = talkText.replace(u'{{%s|3}}' % unblock_tpl,
                                                    u'{{%s|4}}' % unblock_tpl)
                        talkComment = i18n.translate(self.site.code,
                                                     self.msg_done)
                # Step 4
                # Review is closed
                elif templates[1][0] == u'4':
                    # nothing left to do
                    pass
            else:
                # wrong template found
                pass

        # at last if there is a talk comment, users talk page must be changed
        if talkComment:
            self.put_current(talkText, summary=talkComment)

    def getInfo(self, user):
        """Get block info for a given user."""
        if not self.info:
            assert isinstance(user, pywikibot.Page), (
                'user actual parameter is not a Page object')
            for logentry in self.site.logevents('block', page=user):
                if logentry.action() in ('block', 'reblock'):
                    break
            else:
                return
            self.info = logentry
            assert logentry.page() == user, (
                "logentry.page() doesn't match given user")
            self.parts = {
                'admin':    logentry.user(),
                'user':     logentry.page().title(),
                'usertalk': user.getUserTalkPage().title(),
                'section':  i18n.translate(self.site.code,
                                           self.section_header),
                'time':     str(logentry.timestamp()),
                'duration': logentry._params['duration'],
                'comment':  logentry.comment(),
            }

    def SysopGenerator(self):
        """Iter all sysops of a site."""
        for user in self.site.allusers(group='sysop'):
            # exclude sysop bots
            if 'bot' not in user['groups']:
                # yield the sysop talkpage
                yield pywikibot.User(self.site, user['name'])


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    unknown_args = pywikibot.handle_args(args)
    if unknown_args:
        pywikibot.bot.suggest_help(unknown_parameters=unknown_args)
        return False
    else:
        bot = BlockreviewBot()
        bot.run()
        return True

if __name__ == "__main__":
    main()
