"""API login Interface."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import datetime
import re
from typing import Optional

import pywikibot
from pywikibot import login
from pywikibot.backports import Dict
from pywikibot.login import LoginStatus

__all__ = ['LoginManager']


class LoginManager(login.LoginManager):

    """Supply login_to_site method to use API interface."""

    # API login parameters mapping
    mapping = {
        'user': ('lgname', 'username'),
        'password': ('lgpassword', 'password'),
        'ldap': ('lgdomain', 'domain'),
        'token': ('lgtoken', 'logintoken'),
        'result': ('result', 'status'),
        'success': ('Success', 'PASS'),
        'fail': ('Failed', 'FAIL'),
        'reason': ('reason', 'message')
    }

    def keyword(self, key):
        """Get API keyword from mapping."""
        return self.mapping[key][self.action != 'login']

    def _login_parameters(self, *, botpassword: bool = False
                          ) -> Dict[str, str]:
        """Return login parameters."""
        # Since MW 1.27 only for bot passwords.
        self.action = 'login'
        if not botpassword:
            # get token using meta=tokens if supported
            token = self.get_login_token()
            if token:
                # Standard login request since MW 1.27
                self.action = 'clientlogin'

        # prepare default login parameters
        parameters = {'action': self.action,
                      self.keyword('user'): self.login_name,
                      self.keyword('password'): self.password}

        if self.action == 'clientlogin':
            # clientlogin requires non-empty loginreturnurl
            parameters['loginreturnurl'] = 'https://example.com'
            parameters['rememberMe'] = '1'
            parameters['logintoken'] = token

        if self.site.family.ldapDomain:
            parameters[self.keyword('ldap')] = self.site.family.ldapDomain

        return parameters

    def login_to_site(self) -> None:
        """Login to the site.

        Note, this doesn't do anything with cookies. The http module
        takes care of all the cookie stuff. Throws exception on failure.
        """
        self.below_mw_1_27 = False
        if hasattr(self, '_waituntil') \
           and datetime.datetime.now() < self._waituntil:
            diff = self._waituntil - datetime.datetime.now()
            pywikibot.warning(
                'Too many tries, waiting {} seconds before retrying.'
                .format(diff.seconds))
            pywikibot.sleep(diff.seconds)

        self.site._loginstatus = LoginStatus.IN_PROGRESS

        # Bot passwords username contains @,
        # otherwise @ is not allowed in usernames.
        # @ in bot password is deprecated,
        # but we don't want to break bots using it.
        parameters = self._login_parameters(
            botpassword='@' in self.login_name or '@' in self.password)

        # base login request
        login_request = self.site._request(use_get=False,
                                           parameters=parameters)
        while True:
            # try to login
            try:
                login_result = login_request.submit()
            except pywikibot.exceptions.APIError as e:  # pragma: no cover
                login_result = {'error': e.__dict__}

            # clientlogin response can be clientlogin or error
            if self.action in login_result:
                response = login_result[self.action]
                result_key = self.keyword('result')
            elif 'error' in login_result:
                response = login_result['error']
                result_key = 'code'
            else:
                raise RuntimeError('Unexpected API login response key.')

            status = response[result_key]
            fail_reason = response.get(self.keyword('reason'), '')
            if status == self.keyword('success'):
                return

            if status in ('NeedToken', 'WrongToken', 'badtoken'):
                token = response.get('token')
                if token and self.below_mw_1_27:  # pragma: no cover
                    # fetched token using action=login
                    login_request['lgtoken'] = token
                    pywikibot.log('Received login token, proceed with login.')
                else:
                    # if incorrect login token was used,
                    # force relogin and generate fresh one
                    pywikibot.error('Received incorrect login token. '
                                    'Forcing re-login.')
                    # invalidate superior wiki cookies (T224712)
                    pywikibot.data.api._invalidate_superior_cookies(
                        self.site.family)
                    login_request[
                        self.keyword('token')] = self.get_login_token()
                continue

            # messagecode was introduced with 1.29.0-wmf.14
            # but older wikis are still supported
            login_throttled = response.get('messagecode') == 'login-throttled'

            if (status == 'Throttled' or status == self.keyword('fail')
                    and (login_throttled or 'wait' in fail_reason)):
                wait = response.get('wait')
                if wait:
                    delta = datetime.timedelta(seconds=int(wait))
                else:
                    match = re.search(r'(\d+) (seconds|minutes)', fail_reason)
                    if match:
                        delta = datetime.timedelta(
                            **{match.group(2): int(match.group(1))})
                    else:
                        delta = datetime.timedelta()
                self._waituntil = datetime.datetime.now() + delta

            break

        if 'error' in login_result:
            raise pywikibot.exceptions.APIError(**response)

        raise pywikibot.exceptions.APIError(code=status, info=fail_reason)

    def get_login_token(self) -> Optional[str]:
        """Fetch login token for MediaWiki 1.27+.

        :return: login token
        """
        login_token_request = self.site._request(
            use_get=False,
            parameters={'action': 'query', 'meta': 'tokens', 'type': 'login'},
        )
        login_token_result = login_token_request.submit()
        # check if we have to use old implementation of mw < 1.27
        if 'query' in login_token_result:
            return login_token_result['query']['tokens'].get('logintoken')

        self.below_mw_1_27 = True  # pragma: no cover
        return None
