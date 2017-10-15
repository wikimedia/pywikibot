#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to log the bot in to a wiki account.

Suggestion is to make a special account to use for bot use only. Make
sure this bot account is well known on your home wiki before using.

Parameters:

   -family:FF
   -lang:LL     Log in to the LL language of the FF family.
                Example: -family:wiktionary -lang:fr will log you in at
                fr.wiktionary.org.

   -all         Try to log in on all sites where a username is defined in
                user-config.py.

   -logout      Log out of the curren site. Combine with -all to log out of
                all sites, or with -family and -lang to log out of a specific
                site.

   -force       Ignores if the user is already logged in, and tries to log in.

   -pass        Useful in combination with -all when you have accounts for
                several sites and use the same password for all of them.
                Asks you for the password, then logs in on all given sites.

   -pass:XXXX   Uses XXXX as password. Be careful if you use this
                parameter because your password will be shown on your
                screen, and will probably be saved in your command line
                history. This is NOT RECOMMENDED for use on computers
                where others have either physical or remote access.
                Use -pass instead.

   -sysop       Log in with your sysop account.

   -oauth       Generate OAuth authentication information.
                NOTE: Need to copy OAuth tokens to your user-config.py
                manually. -logout, -pass, -force, -pass:XXXX and -sysop are not
                compatible with -oauth.

If not given as parameter, the script will ask for your username and
password (password entry will be hidden), log in to your home wiki using
this combination, and store the resulting cookies (containing your password
hash, so keep it secured!) in a file in the data subdirectory.

All scripts in this library will be looking for this cookie file and will
use the login information if it is present.

To log out, throw away the *.lwp file that is created in the data
subdirectory.
"""
#
# (C) Rob W.W. Hooft, 2003
# (C) Pywikibot team, 2003-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from os.path import join

import pywikibot

from pywikibot import config

from pywikibot.exceptions import SiteDefinitionError
from pywikibot.login import OauthLoginManager


def _get_consumer_token(site):
    key_msg = 'OAuth consumer key on {0}:{1}'.format(site.code, site.family)
    key = pywikibot.input(key_msg)
    secret_msg = 'OAuth consumer secret for consumer {0}'.format(key)
    secret = pywikibot.input(secret_msg, password=True)
    return key, secret


def _oauth_login(site):
    consumer_key, consumer_secret = _get_consumer_token(site)
    login_manager = OauthLoginManager(consumer_secret, False, site,
                                      consumer_key)
    login_manager.login()
    identity = login_manager.identity
    if identity is None:
        pywikibot.error('Invalid OAuth info for %(site)s.' %
                        {'site': site})
    elif site.username() != identity['username']:
        pywikibot.error('Logged in on %(site)s via OAuth as %(wrong)s, '
                        'but expect as %(right)s'
                        % {'site': site,
                           'wrong': identity['username'],
                           'right': site.username()})
    else:
        oauth_token = login_manager.consumer_token + login_manager.access_token
        pywikibot.output('Logged in on %(site)s as %(username)s'
                         'via OAuth consumer %(consumer)s'
                         % {'site': site,
                            'username': site.username(sysop=False),
                            'consumer': consumer_key})
        pywikibot.output('NOTE: To use OAuth, you need to copy the '
                         'following line to your user-config.py:')
        pywikibot.output('authenticate[\'%(hostname)s\'] = %(oauth_token)s' %
                         {'hostname': site.hostname(),
                          'oauth_token': oauth_token})


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    password = None
    sysop = False
    logall = False
    logout = False
    oauth = False
    unknown_args = []
    for arg in pywikibot.handle_args(args):
        if arg.startswith("-pass"):
            if len(arg) == 5:
                password = pywikibot.input(
                    'Password for all accounts (no characters will be shown):',
                    password=True)
            else:
                password = arg[6:]
        elif arg == "-sysop":
            sysop = True
        elif arg == "-all":
            logall = True
        elif arg == "-force":
            pywikibot.output(u"To force a re-login, please delete the revelant "
                             u"lines from '%s' (or the entire file) and try again." %
                             join(config.base_dir, 'pywikibot.lwp'))
        elif arg == "-logout":
            logout = True
        elif arg == '-oauth':
            oauth = True
        else:
            unknown_args += [arg]

    if unknown_args:
        pywikibot.bot.suggest_help(unknown_parameters=unknown_args)
        return False

    if password is not None:
        pywikibot.warning('The -pass argument is not implemented yet. See: '
                          'https://phabricator.wikimedia.org/T102477')

    if logall:
        if sysop and not oauth:
            namedict = config.sysopnames
        else:
            namedict = config.usernames
    else:
        site = pywikibot.Site()
        namedict = {site.family.name: {site.code: None}}
    for familyName in namedict:
        for lang in namedict[familyName]:
            try:
                site = pywikibot.Site(code=lang, fam=familyName)
                if oauth:
                    _oauth_login(site)
                    continue
                if logout:
                    site.logout()
                else:
                    site.login(sysop)
                user = site.user()
                if user:
                    pywikibot.output(
                        'Logged in on {0} as {1}.'.format(site, user))
                else:
                    if logout:
                        pywikibot.output('Logged out of {0}.'.format(site))
                    else:
                        pywikibot.output(
                            'Not logged in on {0}.'.format(site))
            except SiteDefinitionError:
                pywikibot.output(u'%s.%s is not a valid site, please remove it'
                                 u' from your config' % (lang, familyName))


if __name__ == "__main__":
    main()
