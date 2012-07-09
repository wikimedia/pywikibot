#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Library to log the robot in to a wiki account.
"""
#
# (C) Rob W.W. Hooft, 2003
# (C) Pywikipedia bot team, 2003-2012
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import logging
import pywikibot
from pywikibot import config, deprecate_arg
from pywikibot.exceptions import NoSuchSite, NoUsername

_logger = "wiki.login"


# On some wikis you are only allowed to run a bot if there is a link to
# the bot's user page in a specific list.
# If bots are listed in a template, the templates name must be given as
# second parameter, otherwise it must be None
botList = {
    'wikipedia': {
        'en': [u'Wikipedia:Bots/Status/active bots', 'BotS'],
        'simple': [u'Wikipedia:Bots', '/links']
    },
    'gentoo': {
        'en': [u'Help:Bots', None],
    }
}


class LoginManager:
    @deprecate_arg("username", "user")
    @deprecate_arg("verbose", None)
    def __init__(self, password=None, sysop=False, site=None, user=None):
        if site is not None:
            self.site = site
        else:
            self.site = pywikibot.Site()
        if user:
            self.username = user
        elif sysop:
            try:
                self.username = config.sysopnames\
                                [self.site.family.name][self.site.code]
            except KeyError:
                raise NoUsername(
u"""ERROR: Sysop username for %(fam_name)s:%(wiki_code)s is undefined.
If you have a sysop account for that site, please add a line to user-config.py:

sysopnames['%(fam_name)s']['%(wiki_code)s'] = 'myUsername'"""
                                  % {'fam_name': self.site.family.name,
                                     'wiki_code': self.site.code})
        else:
            try:
                self.username = config.usernames\
                                [self.site.family.name][self.site.code]
            except:
                raise NoUsername(
u"""ERROR: Username for %(fam_name)s:%(wiki_code)s is undefined.
If you have an account for that site, please add a line to user-config.py:

usernames['%(fam_name)s']['%(wiki_code)s'] = 'myUsername'"""
                                  % {'fam_name': self.site.family.name,
                                     'wiki_code': self.site.code})
        self.password = password
        if getattr(config, 'password_file', ''):
            self.readPassword()

    def botAllowed(self):
        """
        Checks whether the bot is listed on a specific page to comply with
        the policy on the respective wiki.
        """
        if self.site.family.name in botList \
                and self.site.code in botList[self.site.family.name]:
            botListPageTitle, botTemplate = botList[self.site.family.name][self.site.code]
            botListPage = pywikibot.Page(self.site, botListPageTitle)
            if botTemplate:
                for template in botListPage.templatesWithParams():
                    if template[0] == botTemplate \
                       and template[1][0] == self.username:
                        return True
            else:
                for linkedPage in botListPage.linkedPages():
                    if linkedPage.title(withNamespace=False) == self.username:
                        return True
            return False
        else:
            # No bot policies on other sites
            return True

    def getCookie(self, remember=True, captcha = None):
        """
        Login to the site.

        remember    Remember login (default: True)
        captchaId   A dictionary containing the captcha id and answer, if any

        Returns cookie data if succesful, None otherwise.
        """
        # NOT IMPLEMENTED - see data/api.py for implementation

    def storecookiedata(self, data):
        """
        Store cookie data.

        The argument data is the raw data, as returned by getCookie().

        Returns nothing.
        """
        # THIS IS OVERRIDDEN IN data/api.py
        filename = config.datafilepath('pywikibot.lwp')
        pywikibot.debug(u"Storing cookies to %s" % filename,
                        _logger)
        f = open(filename, 'w')
        f.write(data)
        f.close()

    def readPassword(self):
        """
        Read passwords from a file.

        DO NOT FORGET TO REMOVE READ ACCESS FOR OTHER USERS!!!
        Use chmod 600 password-file.
        All lines below should be valid Python tuples in the form
        (code, family, username, password) or (username, password)
        to set a default password for an username. Default usernames
        should occur above specific usernames.

        Example:

        ("my_username", "my_default_password")
        ("my_sysop_user", "my_sysop_password")
        ("en", "wikipedia", "my_en_user", "my_en_pass")
        """
        password_f = open(config.password_file)
        for line in password_f:
            if not line.strip(): continue
            entry = eval(line)
            if len(entry) == 2:   #for default userinfo
                if entry[0] == self.username: self.password = entry[1]
            elif len(entry) == 4: #for userinfo included code and family
                if entry[0] == self.site.code and \
                  entry[1] == self.site.family.name and \
                  entry[2] == self.username:
                    self.password = entry[3]
        password_f.close()

    def login(self, retry = False):
        if not self.password:
            # As we don't want the password to appear on the screen, we set
            # password = True
            self.password = pywikibot.input(
                                u'Password for user %(name)s on %(site)s:'
                                % {'name': self.username, 'site': self.site},
                                password = True)

#        self.password = self.password.encode(self.site.encoding())

        pywikibot.output(u"Logging in to %(site)s as %(name)s"
                         % {'name': self.username, 'site': self.site})
        try:
            cookiedata = self.getCookie()
        except pywikibot.data.api.APIError, e:
            pywikibot.error(u"Login failed (%s)." % e.code)
            if retry:
                self.password = None
                return self.login(retry = True)
            else:
                return False
        self.storecookiedata(cookiedata)
        pywikibot.log(u"Should be logged in now")
##        # Show a warning according to the local bot policy
##   FIXME: disabled due to recursion; need to move this to the Site object after
##   login
##        if not self.botAllowed():
##            logger.error(
##                u"Username '%(name)s' is not listed on [[%(page)s]]."
##                 % {'name': self.username,
##                    'page': botList[self.site.family.name][self.site.code]})
##            logger.error(
##"Please make sure you are allowed to use the robot before actually using it!")
##            return False
        return True

    def showCaptchaWindow(self, url):
        pass
