#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This bot implements a blocking review process for de-wiki first.

For other sites this bot script must be changed.

This script is run by [[de:User:xqt]]. It should
not be run by other users without prior contact.

The following parameters are supported:

-

"""
#
# (C) xqt, 2010-2014
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n


class BlockreviewBot:

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
        'de': u'Bot: Administrator [[Benutzer:%(admin)s|%(admin)s]] für Sperrprüfung benachrichtigt',
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

    def __init__(self, dry=False):
        """
        Constructor.

        @param generator: The page generator that determines on which pages
                          to work on.
        @param dry:       If True, doesn't do any real changes, but only shows
                          what would have been changed.
        """
        self.site = pywikibot.Site()
        self.dry = dry
        self.info = None
        self.parts = None

    def run(self):
        # TODO: change the generator for template to the included category
        try:
            genPage = pywikibot.Page(self.site,
                                     self.unblock_tpl[self.site.code],
                                     ns=10)
        except KeyError:
            pywikibot.error(u'Language "%s" not supported by this bot.'
                            % self.site.code)
        else:
            for page in genPage.getReferences(follow_redirects=False,
                                              withTemplateInclusion=True,
                                              onlyTemplateInclusion=True):
                if page.namespace() == 3:
                    self.treat(page)
                else:
                    pywikibot.output(u'Ignoring %s, user namespace required'
                                     % page.title(asLink=True))

    def treat(self, userPage):
        """Load the given page, does some changes, and saves it."""
        talkText = self.load(userPage)
        if not talkText:
            # sanity check. No talk page found.
            return
        unblock_tpl = self.unblock_tpl[self.site.code]
        project_name = self.project_name[self.site.code]
        user = pywikibot.User(self.site, userPage.title(withNamespace=False))
        # saveAdmin = saveProject = False
        talkComment = None
        for templates in userPage.templatesWithParams():
            if templates[0].title() == unblock_tpl:
                self.getInfo(user)
                # Step 1
                # a new template is set on blocked users talk page.
                # Notify the blocking admin
                if templates[1] == [] or templates[1][0] == u'1':
                    if self.info['action'] == 'block' or user.isBlocked():
                        if self.site.sitename() == 'wikipedia:de':
                            admin = pywikibot.User(self.site, self.info['user'])
                            adminPage = admin.getUserTalkPage()
                            adminText = adminPage.get()
                            note = i18n.translate(self.site.code,
                                                  self.note_admin,
                                                  self.parts)
                            comment = i18n.translate(self.site.code,
                                                     self.msg_admin,
                                                     self.parts)
                            adminText += note
                            self.save(adminText, adminPage, comment, False)
                        # test for pt-wiki
                        # just print all sysops talk pages
                        elif self.site.sitename() == 'wikipedia:pt':
                            from pywikibot import pagegenerators as pg
                            gen = pg.PreloadingGenerator(self.SysopGenerator())
                            for sysop in gen:
                                print(sysop.title())

                        talkText = talkText.replace(u'{{%s}}' % unblock_tpl,
                                                    u'{{%s|2}}' % unblock_tpl)
                        talkText = talkText.replace(u'{{%s|1}}' % unblock_tpl,
                                                    u'{{%s|2}}' % unblock_tpl)
                        talkComment = i18n.translate(self.site.code,
                                                     self.msg_user
                                                     % self.parts)

                        # some test stuff
                        if self.site().user() == u'Xqbot':
                            testPage = pywikibot.Page(self.site,
                                                      'Benutzer:Xqt/Test')
                            test = testPage.get()
                            test += note
                            self.save(test, testPage,
                                      '[[WP:BA#SPP-Bot|SPPB-Test]]')
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
                        self.save(projText, project, comment, botflag=False)
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
            self.save(talkText, userPage, talkComment)

    def getInfo(self, user):
        if not self.info:
            self.info = next(self.site.logpages(
                1, mode='block', title=user.getUserPage().title(), dump=True))
            self.parts = {
                'admin':    self.info['user'],
                'user':     self.info['title'],
                'usertalk': user.getUserTalkPage().title(),
                'section':  u'Sperrprüfung',
                'time':     self.info['timestamp'],
                'duration': self.info['block']['duration'],
                'comment':  self.info['comment'],
            }

    def SysopGenerator(self):
        for user in self.site.allusers(group='sysop'):
            # exclude sysop bots
            if 'bot' not in user['groups']:
                # yield the sysop talkpage
                yield pywikibot.Page(self.site, user['name'], ns=3)

    def load(self, page):
        """Load the given page and return the page text."""
        try:
            # Load the page
            text = page.get()
        except pywikibot.NoPage:
            pywikibot.output(u"Page %s does not exist; skipping."
                             % page.title(asLink=True))
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"Page %s is a redirect; skipping."
                             % page.title(asLink=True))
        else:
            return text

    def save(self, text, page, comment, minorEdit=True, botflag=True):
        if text != page.text:
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                             % page.title())
            # show what was changed
            pywikibot.showDiff(page.get(), text)
            pywikibot.output(u'Comment: %s' % comment)
            if not self.dry:
                if pywikibot.input_yn(
                        u'Do you want to accept these changes?',
                        default=False, automatic_quit=False):
                    page.text = text
                    try:
                        # Save the page
                        page.save(summary=comment, minorEdit=minorEdit,
                                  botflag=botflag)
                    except pywikibot.LockedPage:
                        pywikibot.output(u"Page %s is locked; skipping."
                                         % page.title(asLink=True))
                    except pywikibot.EditConflict:
                        pywikibot.output(
                            u'Skipping %s because of edit conflict'
                            % (page.title()))
                    except pywikibot.SpamfilterError as error:
                        pywikibot.output(
                            u'Cannot change %s because of spam blacklist entry '
                            u'%s' % (page.title(), error.url))
                    else:
                        return True


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    show = False

    # Parse command line arguments
    if pywikibot.handle_args(args):
        show = True

    if not show:
        bot = BlockreviewBot()
        bot.run()
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    main()
