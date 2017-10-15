#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Library to log the bot in to a wiki account."""
#
# (C) Rob W.W. Hooft, 2003
# (C) Pywikibot team, 2003-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#
import codecs
import os
import webbrowser

from pywikibot.tools import file_mode_checker

from warnings import warn

try:
    import mwoauth
except ImportError as e:
    mwoauth = e

import pywikibot

from pywikibot import config
from pywikibot.exceptions import NoUsername
from pywikibot.tools import deprecated_args, normalize_username, PY2

if not PY2:
    unicode = basestring = str


class OAuthImpossible(ImportError):

    """OAuth authentication is not possible on your system."""


class _PasswordFileWarning(UserWarning):

    """The format of password file is incorrect."""

    pass


_logger = "wiki.login"


# On some wikis you are only allowed to run a bot if there is a link to
# the bot's user page in a specific list.
# If bots are listed in a template, the templates name must be given as
# second parameter, otherwise it must be None
botList = {
    'wikipedia': {
        'simple': [u'Wikipedia:Bots', '/links']
    },
}


class LoginManager(object):

    """Site login manager."""

    @deprecated_args(username="user", verbose=None)
    def __init__(self, password=None, sysop=False, site=None, user=None):
        """
        Constructor.

        All parameters default to defaults in user-config.

        @param site: Site object to log into
        @type site: BaseSite
        @param user: username to use.
            If user is None, the username is loaded from config.usernames.
        @type user: basestring
        @param password: password to use
        @type password: basestring
        @param sysop: login as sysop account.
            The sysop username is loaded from config.sysopnames.
        @type sysop: bool

        @raises NoUsername: No username is configured for the requested site.
        """
        if site is not None:
            self.site = site
        else:
            self.site = pywikibot.Site()
        if user:
            self.username = user
        elif sysop:
            config_names = config.sysopnames
            family_sysopnames = (
                config_names[self.site.family.name] or config_names['*']
            )
            self.username = family_sysopnames.get(self.site.code, None)
            try:
                self.username = self.username or family_sysopnames['*']
            except KeyError:
                raise NoUsername(u"""\
ERROR: Sysop username for %(fam_name)s:%(wiki_code)s is undefined.
If you have a sysop account for that site, please add a line to user-config.py:

sysopnames['%(fam_name)s']['%(wiki_code)s'] = 'myUsername'"""
                                 % {'fam_name': self.site.family.name,
                                    'wiki_code': self.site.code})
        else:
            config_names = config.usernames
            family_usernames = (
                config_names[self.site.family.name] or config_names['*']
            )
            self.username = family_usernames.get(self.site.code, None)
            try:
                self.username = self.username or family_usernames['*']
            except KeyError:
                raise NoUsername(u"""\
ERROR: Username for %(fam_name)s:%(wiki_code)s is undefined.
If you have an account for that site, please add a line to user-config.py:

usernames['%(fam_name)s']['%(wiki_code)s'] = 'myUsername'"""
                                 % {'fam_name': self.site.family.name,
                                    'wiki_code': self.site.code})
        self.password = password
        self.login_name = self.username
        if getattr(config, 'password_file', ''):
            self.readPassword()

    def check_user_exists(self):
        """
        Check that the username exists on the site.

        @raises NoUsername: Username doesnt exist in user list.
        """
        # convert any Special:BotPassword usernames to main account equivalent
        main_username = self.username
        if '@' in self.username:
            warn(
                'When using BotPasswords it is recommended that you store your '
                'login credentials in a password_file instead. '
                'See https://www.mediawiki.org/wiki/Manual:Pywikibot/BotPasswords '
                'for instructions and more information.')
            main_username = self.username.partition('@')[0]

        try:
            data = self.site.allusers(start=main_username, total=1)
            user = next(iter(data))
        except pywikibot.data.api.APIError as e:
            if e.code == 'readapidenied':
                pywikibot.warning('Could not check user %s exists on %s'
                                  % (main_username, self.site))
                return
            else:
                raise

        if user['name'] != main_username:
            # Report the same error as server error code NotExists
            raise NoUsername('Username \'%s\' does not exist on %s'
                             % (main_username, self.site))

    def botAllowed(self):
        """
        Check whether the bot is listed on a specific page.

        This allows bots to comply with the policy on the respective wiki.
        """
        if self.site.family.name in botList \
                and self.site.code in botList[self.site.family.name]:
            botListPageTitle, botTemplate = botList[
                self.site.family.name][self.site.code]
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

    def getCookie(self, remember=True, captcha=None):
        """
        Login to the site.

        @param remember: Remember login (default: True)
        @type remember: bool
        @param captchaId: A dictionary containing the captcha id and answer,
            if any

        @return: cookie data if successful, None otherwise.
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
        (code, family, username, password),
        (family, username, password) or
        (username, password)
        to set a default password for an username. The last matching entry will
        be used, so default usernames should occur above specific usernames.

        For BotPasswords the password should be given as a BotPassword object.

        The file must be either encoded in ASCII or UTF-8.

        Example:

        (u"my_username", u"my_default_password")
        (u"my_sysop_user", u"my_sysop_password")
        (u"wikipedia", u"my_wikipedia_user", u"my_wikipedia_pass")
        (u"en", u"wikipedia", u"my_en_wikipedia_user", u"my_en_wikipedia_pass")
        (u"my_username", BotPassword(u"my_BotPassword_suffix", u"my_BotPassword_password"))
        """
        # Set path to password file relative to the user_config
        # but fall back on absolute path for backwards compatibility
        password_file = os.path.join(config.base_dir, config.password_file)
        if not os.path.isfile(password_file):
            password_file = config.password_file

        # We fix password file permission first.
        file_mode_checker(password_file, mode=config.private_files_permission)

        with codecs.open(password_file, encoding='utf-8') as f:
            lines = f.readlines()
        line_nr = len(lines) + 1
        for line in reversed(lines):
            line_nr -= 1
            if not line.strip():
                continue
            try:
                entry = eval(line)
            except SyntaxError:
                entry = None
            if type(entry) is not tuple:
                warn('Invalid tuple in line {0}'.format(line_nr),
                     _PasswordFileWarning)
                continue
            if not 2 <= len(entry) <= 4:
                warn('The length of tuple in line {0} should be 2 to 4 ({1} '
                     'given)'.format(line_nr, entry), _PasswordFileWarning)
                continue

            code, family, username, password = (
                self.site.code, self.site.family.name)[:4 - len(entry)] + entry
            if (normalize_username(username) == self.username and
                    family == self.site.family.name and
                    code == self.site.code):
                if isinstance(password, basestring):
                    self.password = password
                    break
                elif isinstance(password, BotPassword):
                    self.password = password.password
                    self.login_name = password.login_name(self.username)
                    break
                else:
                    warn('Invalid password format', _PasswordFileWarning)

    def login(self, retry=False):
        """
        Attempt to log into the server.

        @param retry: infinitely retry if the API returns an unknown error
        @type retry: bool

        @raises NoUsername: Username is not recognised by the site.
        """
        if not self.password:
            # First check that the username exists,
            # to avoid asking for a password that will not work.
            self.check_user_exists()

            # As we don't want the password to appear on the screen, we set
            # password = True
            self.password = pywikibot.input(
                u'Password for user %(name)s on %(site)s (no characters will '
                u'be shown):' % {'name': self.login_name, 'site': self.site},
                password=True)

        pywikibot.output(u"Logging in to %(site)s as %(name)s"
                         % {'name': self.login_name, 'site': self.site})
        try:
            cookiedata = self.getCookie()
        except pywikibot.data.api.APIError as e:
            pywikibot.error(u"Login failed (%s)." % e.code)
            if e.code == 'NotExists':
                raise NoUsername(u"Username '%s' does not exist on %s"
                                 % (self.login_name, self.site))
            elif e.code == 'Illegal':
                raise NoUsername(u"Username '%s' is invalid on %s"
                                 % (self.login_name, self.site))
            elif e.code == 'readapidenied':
                raise NoUsername(
                    'Username "{0}" does not have read permissions on '
                    '{1}'.format(self.login_name, self.site))
            elif e.code == 'Failed':
                raise NoUsername(
                    'Username "{0}" does not have read permissions on '
                    '{1}\n.{2}'.format(self.login_name, self.site, e.info))
            # TODO: investigate other unhandled API codes (bug T75539)
            if retry:
                self.password = None
                return self.login(retry=True)
            else:
                return False
        self.storecookiedata(cookiedata)
        pywikibot.log(u"Should be logged in now")
#        # Show a warning according to the local bot policy
#   FIXME: disabled due to recursion; need to move this to the Site object after
#   login
#        if not self.botAllowed():
#            logger.error(
#                u"Username '%(name)s' is not listed on [[%(page)s]]."
#                 % {'name': self.username,
#                    'page': botList[self.site.family.name][self.site.code]})
#            logger.error(
# "Please make sure you are allowed to use the robot before actually using it!")
#            return False
        return True

    def showCaptchaWindow(self, url):
        """Open a window to show the captcha for the given URL."""
        pass


class BotPassword(object):

    """BotPassword object for storage in password file."""

    def __init__(self, suffix, password):
        """
        Constructor.

        BotPassword function by using a separate password paired with a suffixed
        username of the form <username>@<suffix>.

        @param suffix: Suffix of the login name
        @type suffix: basestring
        @param password: bot password
        @type password: basestring

        @raises _PasswordFileWarning: suffix improperly specified
        """
        if '@' in suffix:
            warn('The BotPassword entry should only include the suffix',
                 _PasswordFileWarning)
        self.suffix = suffix
        self.password = password

    def login_name(self, username):
        """
        Construct the login name from the username and suffix.

        @param user: username (without suffix)
        @type user: basestring
        @rtype: basestring
        """
        return '{0}@{1}'.format(username, self.suffix)


class OauthLoginManager(LoginManager):

    """Site login manager using OAuth."""

    # NOTE: Currently OauthLoginManager use mwoauth directly to complete OAuth
    # authentication process

    def __init__(self, password=None, sysop=False, site=None, user=None):
        """
        Constructor.

        All parameters default to defaults in user-config.

        @param site: Site object to log into
        @type site: BaseSite
        @param user: consumer key
        @type user: basestring
        @param password: consumer secret
        @type password: basestring
        @param sysop: login as sysop account.
            The sysop username is loaded from config.sysopnames.
        @type sysop: bool

        @raises NoUsername: No username is configured for the requested site.
        @raises OAuthImpossible: mwoauth isn't installed
        """
        if isinstance(mwoauth, ImportError):
            raise OAuthImpossible('mwoauth is not installed: %s.' % mwoauth)
        assert password is not None and user is not None
        assert sysop is False
        super(OauthLoginManager, self).__init__(None, False, site, None)
        if self.password:
            pywikibot.warn('Password exists in password file for %s:%s.'
                           'Password is unnecessary and should be removed '
                           'when OAuth enabled.' % (self.site, self.username))
        self._consumer_token = (user, password)
        self._access_token = None

    def login(self, retry=False, force=False):
        """
        Attempt to log into the server.

        @param retry: infinitely retry if exception occurs during authentication.
        @type retry: bool
        @param force: force to re-authenticate
        @type force: bool
        """
        if self.access_token is None or force:
            pywikibot.output('Logging in to %(site)s via OAuth consumer %(key)s'
                             % {'key': self.consumer_token[0],
                                'site': self.site})
            consumer_token = mwoauth.ConsumerToken(self.consumer_token[0],
                                                   self.consumer_token[1])
            handshaker = mwoauth.Handshaker(
                self.site.base_url(self.site.path()), consumer_token)
            try:
                redirect, request_token = handshaker.initiate()
                pywikibot.stdout('Authenticate via web browser..')
                webbrowser.open(redirect)
                pywikibot.stdout('If your web browser does not open '
                                 'automatically, please point it to: %s'
                                 % redirect)
                request_qs = pywikibot.input('Response query string: ')
                access_token = handshaker.complete(request_token,
                                                   request_qs)
                self._access_token = (access_token.key, access_token.secret)
            except Exception as e:
                pywikibot.error(e)
                if retry:
                    self.login(retry=True, force=force)
        else:
            pywikibot.output('Logged in to %(site)s via consumer %(key)s'
                             % {'key': self.consumer_token[0],
                                'site': self.site})

    @property
    def consumer_token(self):
        """
        Return OAuth consumer key token and secret token.

        @rtype: tuple of two str
        """
        return self._consumer_token

    @property
    def access_token(self):
        """
        Return OAuth access key token and secret token.

        @rtype: tuple of two str
        """
        return self._access_token

    @property
    def identity(self):
        """
        Get identifying information about a user via an authorized token.

        @rtype: None or dict
        """
        if self.access_token is None:
            pywikibot.error('Access token not set')
            return None
        consumer_token = mwoauth.ConsumerToken(self.consumer_token[0],
                                               self.consumer_token[1])
        access_token = mwoauth.AccessToken(self.access_token[0],
                                           self.access_token[1])
        try:
            identity = mwoauth.identify(self.site.base_url(self.site.path()),
                                        consumer_token, access_token)
            return identity
        except Exception as e:
            pywikibot.error(e)
            return None
