#!/usr/bin/env python3
"""Script to log the bot in to a wiki account.

Suggestion is to make a special account to use for bot use only. Make
sure this bot account is well known on your home wiki before using.

The following parameters are supported:

-all         Try to log in on all sites where a username is defined in
             user config file (user-config.py).

-logout      Log out of the current site. Combine with ``-all`` to log
             out of all sites, or with :ref:`global options` ``-family``,
             ``-lang`` or ``-site`` to log out of a specific site.

-oauth       Generate OAuth authentication information.

             .. note:: Need to copy OAuth tokens to your user config
                file manually. -logout is not compatible with -oauth.

-autocreate  Auto-create an account using unified login when necessary.

             .. note:: the global account must exist already before
                using this.

-async       Run the bot in parallel tasks, only useful together with
             ``-all`` option

.. hint:: Use :ref:`global options` ``-code``, ``-family`` or ``-site``
   to determine the site to login/logout.

If not given as parameter, the script will ask for your username and
password (password entry will be hidden), log in to your home wiki using
this combination, and store the resulting cookies (containing your
password hash, so keep it secured!) in a file in the data subdirectory.

All scripts in this library will be looking for this cookie file and
will use the login information if it is present.

To log out, throw away the ``*.lwp`` file that is created in the data
subdirectory.

.. versionchanged:: 7.4
   moved to :mod:`pywikibot.scripts` folder
"""
#
# (C) Pywikibot team, 2003-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import datetime
from contextlib import nullcontext, suppress

import pywikibot
from pywikibot import config
from pywikibot.exceptions import NoUsernameError, SiteDefinitionError
from pywikibot.login import OauthLoginManager
from pywikibot.tools.threading import BoundedPoolExecutor


def _get_consumer_token(site) -> tuple[str, str]:
    key_msg = f'OAuth consumer key on {site.code}:{site.family}'
    key = pywikibot.input(key_msg)
    secret_msg = f'OAuth consumer secret for consumer {key}'
    secret = pywikibot.input(secret_msg, password=True)
    return key, secret


def _oauth_login(site) -> None:
    consumer_key, consumer_secret = _get_consumer_token(site)
    login_manager = OauthLoginManager(consumer_secret, site, consumer_key)
    login_manager.login()
    identity = login_manager.identity
    if identity is None:
        pywikibot.error(f'Invalid OAuth info for {site}.')
    elif site.username() != identity['username']:
        pywikibot.error(
            'Logged in on {site} via OAuth as {wrong}, but expect as {right}'
            .format(site=site,
                    wrong=identity['username'], right=site.username()))
    else:
        oauth_token = login_manager.consumer_token + login_manager.access_token
        pywikibot.info(
            f'Logged in on {site} as {site.username()} via OAuth consumer '
            f'{consumer_key}\nNOTE: To use OAuth, you need to copy the'
            ' following line to your user config file:\n'
            f'authenticate[{site.hostname()!r}] = {oauth_token}'
        )


def login_one_site(code, family, oauth, logout, autocreate):
    """Login on one site."""
    try:
        site = pywikibot.Site(code, family)
    except SiteDefinitionError:
        pywikibot.error(f'{family}:{code} is not a valid site, '
                        'please remove it from your user-config')
        return

    if oauth:
        _oauth_login(site)
        return

    if logout:
        site.logout()
    else:
        try:
            site.login(autocreate=autocreate)
        except NoUsernameError as e:
            pywikibot.error(e)

    user = site.user()
    if user:
        pywikibot.info(f'Logged in on {site} as {user}.')
    elif logout:
        pywikibot.info(f'Logged out of {site}.')
    else:
        pywikibot.info(f'Not logged in on {site}.')


def main(*args: str) -> None:
    """Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    logall = False
    logout = False
    oauth = False
    autocreate = False
    asynchronous = False
    unknown_args = []
    for arg in pywikibot.handle_args(args):
        if arg == '-all':
            logall = True
        elif arg == '-logout':
            logout = True
        elif arg == '-oauth':
            oauth = True
        elif arg == '-autocreate':
            autocreate = True
        elif arg == '-async':
            asynchronous = True
        else:
            unknown_args.append(arg)

    if pywikibot.bot.suggest_help(unknown_parameters=unknown_args):
        return

    if logall:
        namedict = config.usernames
    else:
        site = pywikibot.Site()
        namedict = {site.family.name: {site.code: None}}

    params = oauth, logout, autocreate
    context = (nullcontext(),
               BoundedPoolExecutor('ThreadPoolExecutor'))[asynchronous]
    with context as executor:
        for family_name in namedict:
            for lang in namedict[family_name]:
                if asynchronous:
                    executor.submit(login_one_site, lang, family_name, *params)
                else:
                    login_one_site(lang, family_name, *params)


if __name__ == '__main__':
    start = datetime.datetime.now()
    with suppress(KeyboardInterrupt):
        main()
    pywikibot.info('\nExecution time: '
                   f'{(datetime.datetime.now() - start).seconds} seconds')
