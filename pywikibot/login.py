"""Library to log the bot in to a wiki account."""
#
# (C) Pywikibot team, 2003-2022
#
# Distributed under the terms of the MIT license.
#
import codecs
import os
import webbrowser
from enum import IntEnum
from typing import Any, Optional
from warnings import warn

import pywikibot
from pywikibot import __url__, config
from pywikibot.backports import Dict, Tuple
from pywikibot.comms import http
from pywikibot.exceptions import APIError, NoUsernameError
from pywikibot.tools import file_mode_checker, normalize_username


try:
    import mwoauth
except ImportError as e:
    mwoauth = e


class _PasswordFileWarning(UserWarning):

    """The format of password file is incorrect."""


# On some wikis you are only allowed to run a bot if there is a link to
# the bot's user page in a specific list.
# If bots are listed in a template, the templates name must be given as
# second parameter, otherwise it must be None
botList = {
    'wikipedia': {
        'simple': ['Wikipedia:Bots', '/links']
    },
}


class LoginStatus(IntEnum):

    """
    Enum for Login statuses.

    >>> LoginStatus.NOT_ATTEMPTED
    LoginStatus(-3)
    >>> LoginStatus.IN_PROGRESS.value
    -2
    >>> LoginStatus.NOT_LOGGED_IN.name
    'NOT_LOGGED_IN'
    >>> int(LoginStatus.AS_USER)
    0
    >>> LoginStatus(-3).name
    'NOT_ATTEMPTED'
    >>> LoginStatus(0).name
    'AS_USER'
    """

    NOT_ATTEMPTED = -3
    IN_PROGRESS = -2
    NOT_LOGGED_IN = -1
    AS_USER = 0

    def __repr__(self) -> str:
        """Return internal representation."""
        return 'LoginStatus({})'.format(self)


class LoginManager:

    """Site login manager."""

    def __init__(self, password: Optional[str] = None,
                 site: Optional['pywikibot.site.BaseSite'] = None,
                 user: Optional[str] = None) -> None:
        """
        Initializer.

        All parameters default to defaults in user-config.

        :param site: Site object to log into
        :param user: username to use.
            If user is None, the username is loaded from config.usernames.
        :param password: password to use

        :raises pywikibot.exceptions.NoUsernameError: No username is configured
            for the requested site.
        """
        site = self.site = site or pywikibot.Site()
        if not user:
            config_names = config.usernames

            code_to_usr = config_names[site.family.name] or config_names['*']
            try:
                user = code_to_usr.get(site.code) or code_to_usr['*']
            except KeyError:
                raise NoUsernameError(
                    'ERROR: '
                    'username for {site.family.name}:{site.code} is undefined.'
                    '\nIf you have a username for that site, please add a '
                    'line to user config file (user_config.py) as follows:\n'
                    "usernames['{site.family.name}']['{site.code}'] = "
                    "'myUsername'".format(site=site))
        self.password = password
        self.login_name = self.username = user
        if getattr(config, 'password_file', ''):
            self.readPassword()

    def check_user_exists(self) -> None:
        """
        Check that the username exists on the site.

        .. seealso:: :api:`Users`

        :raises pywikibot.exceptions.NoUsernameError: Username doesn't exist in
            user list.
        """
        # convert any Special:BotPassword usernames to main account equivalent
        main_username = self.username
        if '@' in self.username:
            warn(
                'When using BotPasswords it is recommended that you store '
                'your login credentials in a password_file instead. See '
                '{}/BotPasswords for instructions and more information.'
                .format(__url__))
            main_username = self.username.partition('@')[0]

        try:
            data = self.site.allusers(start=main_username, total=1)
            user = next(data)
        except APIError as e:
            if e.code == 'readapidenied':
                pywikibot.warning("Could not check user '{}' exists on {}"
                                  .format(main_username, self.site))
                return
            raise

        if user['name'] != main_username:
            # Report the same error as server error code NotExists
            raise NoUsernameError("Username '{}' does not exist on {}"
                                  .format(main_username, self.site))

    def botAllowed(self) -> bool:
        """
        Check whether the bot is listed on a specific page.

        This allows bots to comply with the policy on the respective wiki.
        """
        code, fam = self.site.code, self.site.family.name
        if code in botList.get(fam, []):
            botlist_pagetitle, bot_template_title = botList[fam][code]
            botlist_page = pywikibot.Page(self.site, botlist_pagetitle)
            if bot_template_title:
                for template, params in botlist_page.templatesWithParams():
                    if (template.title() == bot_template_title
                            and params[0] == self.username):
                        return True
            else:
                for linked_page in botlist_page.linkedPages():
                    if linked_page.title(with_ns=False) == self.username:
                        return True
            return False

        # No bot policies on other sites
        return True

    def login_to_site(self) -> None:
        """Login to the site."""
        # THIS IS OVERRIDDEN IN data/api.py
        raise NotImplementedError

    def storecookiedata(self) -> None:
        """Store cookie data."""
        http.cookie_jar.save(ignore_discard=True)

    def readPassword(self) -> None:
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

        Example::

         ('my_username', 'my_default_password')
         ('wikipedia', 'my_wikipedia_user', 'my_wikipedia_pass')
         ('en', 'wikipedia', 'my_en_wikipedia_user', 'my_en_wikipedia_pass')
         ('my_username', BotPassword(
          'my_BotPassword_suffix', 'my_BotPassword_password'))
        """
        # Set path to password file relative to the user_config
        # but fall back on absolute path for backwards compatibility
        assert config.base_dir is not None and config.password_file is not None
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
            if not line.strip() or line.startswith('#'):
                continue

            try:
                entry = eval(line)
            except SyntaxError:
                entry = None

            if not isinstance(entry, tuple):
                warn('Invalid tuple in line {}'.format(line_nr),
                     _PasswordFileWarning)
                continue

            if not 2 <= len(entry) <= 4:
                warn('The length of tuple in line {} should be 2 to 4 ({} '
                     'given)'.format(line_nr, entry), _PasswordFileWarning)
                continue

            code, family, username, password = (
                self.site.code, self.site.family.name)[:4 - len(entry)] + entry
            if (normalize_username(username) == self.username
                    and family == self.site.family.name
                    and code == self.site.code):
                if isinstance(password, str):
                    self.password = password
                    break

                if isinstance(password, BotPassword):
                    self.password = password.password
                    self.login_name = password.login_name(self.username)
                    break

                warn('Invalid password format', _PasswordFileWarning)

    _api_error = {
        'NotExists': 'does not exist',
        'Illegal': 'is invalid',
        'readapidenied': 'does not have read permissions',
        'Failed': 'does not have read permissions',
        'FAIL': 'does not have read permissions',
    }

    def login(self, retry: bool = False, autocreate: bool = False) -> bool:
        """
        Attempt to log into the server.

        .. seealso:: :api:`Login`

        :param retry: infinitely retry if the API returns an unknown error
        :param autocreate: if true, allow auto-creation of the account
                           using unified login

        :raises pywikibot.exceptions.NoUsernameError: Username is not
            recognised by the site.
        """
        if not self.password:
            # First check that the username exists,
            # to avoid asking for a password that will not work.
            if not autocreate:
                self.check_user_exists()

            # As we don't want the password to appear on the screen, we set
            # password = True
            self.password = pywikibot.input(
                'Password for user {name} on {site} (no characters will be '
                'shown):'.format(name=self.login_name, site=self.site),
                password=True)

        pywikibot.output('Logging in to {site} as {name}'
                         .format(name=self.login_name, site=self.site))
        try:
            self.login_to_site()
        except APIError as e:
            error_code = e.code
            pywikibot.error('Login failed ({}).'.format(error_code))
            if error_code in self._api_error:
                error_msg = 'Username "{}" {} on {}'.format(
                    self.login_name, self._api_error[error_code], self.site)
                if error_code in ('Failed', 'FAIL'):
                    error_msg += '\n.{}'.format(e.info)
                raise NoUsernameError(error_msg)

            # TODO: investigate other unhandled API codes (bug T75539)
            if retry:
                self.password = None
                return self.login(retry=False)

        else:
            self.storecookiedata()
            pywikibot.log('Should be logged in now')
            return True

        return False


class BotPassword:

    """BotPassword object for storage in password file."""

    def __init__(self, suffix: str, password: str) -> None:
        """
        Initializer.

        BotPassword function by using a separate password paired with a
        suffixed username of the form <username>@<suffix>.

        :param suffix: Suffix of the login name
        :param password: bot password

        :raises _PasswordFileWarning: suffix improperly specified
        """
        if '@' in suffix:
            warn('The BotPassword entry should only include the suffix',
                 _PasswordFileWarning)
        self.suffix = suffix
        self.password = password

    def login_name(self, username: str) -> str:
        """
        Construct the login name from the username and suffix.

        :param user: username (without suffix)
        """
        return '{}@{}'.format(username, self.suffix)


class OauthLoginManager(LoginManager):

    """Site login manager using OAuth."""

    # NOTE: Currently OauthLoginManager use mwoauth directly to complete OAuth
    # authentication process

    def __init__(self, password: Optional[str] = None,
                 site: Optional['pywikibot.site.BaseSite'] = None,
                 user: Optional[str] = None) -> None:
        """
        Initializer.

        All parameters default to defaults in user-config.

        :param site: Site object to log into
        :param user: consumer key
        :param password: consumer secret

        :raises pywikibot.exceptions.NoUsernameError: No username is configured
            for the requested site.
        :raises ImportError: mwoauth isn't installed
        """
        if isinstance(mwoauth, ImportError):
            raise ImportError('mwoauth is not installed: {}.'.format(mwoauth))
        assert password is not None and user is not None
        super().__init__(password=None, site=site, user=None)
        if self.password:
            pywikibot.warn('Password exists in password file for {login.site}:'
                           '{login.username}. Password is unnecessary and '
                           'should be removed if OAuth enabled.'
                           .format(login=self))
        self._consumer_token = (user, password)
        self._access_token = None  # type: Optional[Tuple[str, str]]

    def login(self, retry: bool = False, force: bool = False) -> bool:
        """
        Attempt to log into the server.

        .. seealso:: :api:`Login`

        :param retry: infinitely retry if exception occurs during
            authentication.
        :param force: force to re-authenticate
        """
        if self.access_token is None or force:
            pywikibot.output(
                'Logging in to {site} via OAuth consumer {key}'
                .format(key=self.consumer_token[0], site=self.site))
            consumer_token = mwoauth.ConsumerToken(*self.consumer_token)
            handshaker = mwoauth.Handshaker(
                self.site.base_url(self.site.path()), consumer_token)
            try:
                redirect, request_token = handshaker.initiate()
                pywikibot.stdout('Authenticate via web browser..')
                webbrowser.open(redirect)
                pywikibot.stdout('If your web browser does not open '
                                 'automatically, please point it to: {}'
                                 .format(redirect))
                request_qs = pywikibot.input('Response query string: ')
                access_token = handshaker.complete(request_token, request_qs)
                self._access_token = (access_token.key, access_token.secret)
                return True
            except Exception as e:
                pywikibot.error(e)
                if retry:
                    return self.login(retry=True, force=force)
                return False
        else:
            pywikibot.output('Logged in to {site} via consumer {key}'
                             .format(key=self.consumer_token[0],
                                     site=self.site))
            return True

    @property
    def consumer_token(self) -> Tuple[str, str]:
        """
        Return OAuth consumer key token and secret token.

        .. seealso:: :api:`Tokens`
        """
        return self._consumer_token

    @property
    def access_token(self) -> Optional[Tuple[str, str]]:
        """
        Return OAuth access key token and secret token.

        .. seealso:: :api:`Tokens`
        """
        return self._access_token

    @property
    def identity(self) -> Optional[Dict[str, Any]]:
        """Get identifying information about a user via an authorized token."""
        if self.access_token is None:
            pywikibot.error('Access token not set')
            return None

        consumer_token = mwoauth.ConsumerToken(*self.consumer_token)
        access_token = mwoauth.AccessToken(*self.access_token)
        try:
            identity = mwoauth.identify(self.site.base_url(self.site.path()),
                                        consumer_token, access_token)
            return identity
        except Exception as e:
            pywikibot.error(e)
            return None
