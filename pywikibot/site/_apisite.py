"""Objects representing API interface to MediaWiki site."""
#
# (C) Pywikibot team, 2008-2021
#
# Distributed under the terms of the MIT license.
#
import datetime
import heapq
import itertools
import mimetypes
import os
import re
import time
import typing

from collections import defaultdict, namedtuple, OrderedDict
from collections.abc import Iterable
from contextlib import suppress
from itertools import zip_longest
from textwrap import fill
from typing import Any, Optional, Union
from warnings import warn

import pywikibot
import pywikibot.family

from pywikibot.backports import Dict, List
from pywikibot.comms.http import get_authentication
from pywikibot.data import api
from pywikibot.exceptions import (
    ArticleExistsConflict,
    CaptchaError,
    CascadeLockedPage,
    CircularRedirect,
    EditConflict,
    Error,
    InconsistentTitleReceived,
    InterwikiRedirectPage,
    IsNotRedirectPage,
    LockedNoPage,
    LockedPage,
    NoCreateError,
    NoPage,
    NoUsername,
    PageCreatedConflict,
    PageDeletedConflict,
    PageRelatedError,
    PageSaveRelatedError,
    SiteDefinitionError,
    SpamblacklistError,
    TitleblacklistError,
    UserRightsError,
    UnknownExtension,
)
from pywikibot.login import LoginStatus as _LoginStatus
from pywikibot.site._basesite import BaseSite
from pywikibot.site._decorators import need_right, need_version
from pywikibot.site._extensions import (
    EchoMixin,
    FlowMixin,
    GeoDataMixin,
    GlobalUsageMixin,
    LinterMixin,
    PageImagesMixin,
    ProofreadPageMixin,
    ThanksFlowMixin,
    ThanksMixin,
    UrlShortenerMixin,
    WikibaseClientMixin,
)
from pywikibot.site._interwikimap import _InterwikiMap
from pywikibot.site._namespace import Namespace
from pywikibot.site._siteinfo import Siteinfo
from pywikibot.site._tokenwallet import TokenWallet
from pywikibot.tools import (
    compute_file_hash,
    deprecated,
    deprecate_arg,
    deprecated_args,
    filter_unique,
    is_IP,
    issue_deprecation_warning,
    itergroup,
    MediaWikiVersion,
    merge_unique_dicts,
    normalize_username,
    remove_last_args,
)


__all__ = ('APISite', )
_logger = 'wiki.apisite'


_mw_msg_cache = defaultdict(dict)


class APISite(
    BaseSite,
    EchoMixin,
    FlowMixin,
    GeoDataMixin,
    GlobalUsageMixin,
    LinterMixin,
    PageImagesMixin,
    ProofreadPageMixin,
    ThanksFlowMixin,
    ThanksMixin,
    UrlShortenerMixin,
    WikibaseClientMixin,
):

    """
    API interface to MediaWiki site.

    Do not instantiate directly; use pywikibot.Site function.
    """

    @remove_last_args(['sysop'])
    def __init__(self, code, fam=None, user=None):
        """Initializer."""
        super().__init__(code, fam, user)
        self._msgcache = {}
        self._loginstatus = _LoginStatus.NOT_ATTEMPTED
        self._siteinfo = Siteinfo(self)
        self._paraminfo = api.ParamInfo(self)
        self._interwikimap = _InterwikiMap(self)
        self.tokens = TokenWallet(self)

    def __getstate__(self):
        """Remove TokenWallet before pickling, for security reasons."""
        new = super().__getstate__()
        del new['tokens']
        del new['_interwikimap']
        return new

    def __setstate__(self, attrs):
        """Restore things removed in __getstate__."""
        super().__setstate__(attrs)
        self._interwikimap = _InterwikiMap(self)
        self.tokens = TokenWallet(self)

    def interwiki(self, prefix):
        """
        Return the site for a corresponding interwiki prefix.

        @raises pywikibot.exceptions.SiteDefinitionError: if the url given in
            the interwiki table doesn't match any of the existing families.
        @raises KeyError: if the prefix is not an interwiki prefix.
        """
        return self._interwikimap[prefix].site

    def interwiki_prefix(self, site):
        """
        Return the interwiki prefixes going to that site.

        The interwiki prefixes are ordered first by length (shortest first)
        and then alphabetically. L{interwiki(prefix)} is not guaranteed to
        equal C{site} (i.e. the parameter passed to this function).

        @param site: The targeted site, which might be it's own.
        @type site: L{BaseSite}
        @return: The interwiki prefixes
        @rtype: list (guaranteed to be not empty)
        @raises KeyError: if there is no interwiki prefix for that site.
        """
        assert site is not None, 'Site must not be None'
        prefixes = set()
        for url in site._interwiki_urls():
            prefixes.update(self._interwikimap.get_by_url(url))
        if not prefixes:
            raise KeyError(
                "There is no interwiki prefix to '{0}'".format(site))
        return sorted(prefixes, key=lambda p: (len(p), p))

    def local_interwiki(self, prefix):
        """
        Return whether the interwiki prefix is local.

        A local interwiki prefix is handled by the target site like a normal
        link. So if that link also contains an interwiki link it does follow
        it as long as it's a local link.

        @raises pywikibot.exceptions.SiteDefinitionError: if the url given in
            the interwiki table doesn't match any of the existing families.
        @raises KeyError: if the prefix is not an interwiki prefix.
        """
        return self._interwikimap[prefix].local

    @classmethod
    def fromDBName(cls, dbname, site=None):
        """
        Create a site from a database name using the sitematrix.

        @param dbname: database name
        @type dbname: str
        @param site: Site to load sitematrix from. (Default meta.wikimedia.org)
        @type site: pywikibot.site.APISite
        @return: site object for the database name
        @rtype: pywikibot.site.APISite
        """
        # TODO this only works for some WMF sites
        if not site:
            site = pywikibot.Site('meta', 'meta')
        req = site._request(expiry=datetime.timedelta(days=10),
                            parameters={'action': 'sitematrix'})
        data = req.submit()
        for key, val in data['sitematrix'].items():
            if key == 'count':
                continue
            if 'code' in val:
                lang = val['code']
                for site in val['site']:
                    if site['dbname'] == dbname:
                        if site['code'] == 'wiki':
                            site['code'] = 'wikipedia'
                        return pywikibot.Site(lang, site['code'])
            else:  # key == 'specials'
                for site in val:
                    if site['dbname'] == dbname:
                        return pywikibot.Site(url=site['url'] + '/w/index.php')
        raise ValueError('Cannot parse a site out of %s.' % dbname)

    @deprecated_args(step=None)
    def _generator(self, gen_class, type_arg: Optional[str] = None,
                   namespaces=None, total: Optional[int] = None, **args):
        """Convenience method that returns an API generator.

        All generic keyword arguments are passed as MW API parameter
        except for 'g_content' which is passed as a normal parameter to
        the generator's Initializer.

        @param gen_class: the type of generator to construct (must be
            a subclass of pywikibot.data.api._RequestWrapper)
        @param type_arg: query type argument to be passed to generator's
            constructor unchanged (not all types require this)
        @param namespaces: if not None, limit the query to namespaces in
            this list
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param total: if not None, limit the generator to yielding this
            many items in total
        @return: iterable with parameters set
        @rtype: _RequestWrapper
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        req_args = {'site': self}
        if 'g_content' in args:
            req_args['g_content'] = args.pop('g_content')
        if 'parameters' in args:
            req_args.update(args)
        else:
            req_args['parameters'] = args
        if type_arg is not None:
            gen = gen_class(type_arg, **req_args)
        else:
            gen = gen_class(**req_args)
        if namespaces is not None:
            gen.set_namespace(namespaces)
        gen.set_maximum_items(total)
        return gen

    @staticmethod
    def _request_class(kwargs):
        """
        Get the appropriate class.

        Inside this class kwargs use the parameters mode but QueryGenerator may
        use the old kwargs mode.
        """
        # This checks expiry in kwargs and not kwargs['parameters'] so it won't
        # create a CachedRequest when there is an expiry in an API parameter
        # and kwargs here are actually in parameters mode.
        if 'expiry' in kwargs and kwargs['expiry'] is not None:
            return api.CachedRequest
        else:
            return api.Request

    def _request(self, **kwargs):
        """Create a request by forwarding all parameters directly."""
        if 'expiry' in kwargs and kwargs['expiry'] is None:
            del kwargs['expiry']

        return self._request_class(kwargs)(site=self, **kwargs)

    def _simple_request(self, **kwargs):
        """Create a request by defining all kwargs as parameters."""
        return self._request_class({'parameters': kwargs}).create_simple(
            self, **kwargs)

    @remove_last_args(['sysop'])
    def logged_in(self):
        """Verify the bot is logged into the site as the expected user.

        The expected usernames are those provided as the user parameter
        at instantiation.

        @rtype: bool
        """
        if not hasattr(self, '_userinfo'):
            return False
        if 'anon' in self.userinfo or not self.userinfo.get('id'):
            return False

        if not self.userinfo.get('name'):
            return False

        if self.userinfo['name'] != self.username():
            return False

        return True

    def is_oauth_token_available(self):
        """
        Check whether OAuth token is set for this site.

        @rtype: bool
        """
        auth_token = get_authentication(self.base_url(''))
        return auth_token is not None and len(auth_token) == 4

    @deprecated_args(sysop=True)
    def login(self, sysop=None,
              autocreate: bool = False,
              user: Optional[str] = None):
        """
        Log the user in if not already logged in.

        @param autocreate: if true, allow auto-creation of the account
            using unified login
        @param user: bot user name. Overrides the username set by
            BaseSite initializer parameter or user-config.py setting

        @raises pywikibot.exceptions.NoUsername: Username is not recognised
            by the site.
        @see: U{https://www.mediawiki.org/wiki/API:Login}
        """
        if sysop is not None:
            issue_deprecation_warning("'sysop' parameter",
                                      warning_class=FutureWarning,
                                      since='20201230')

        # TODO: this should include an assert that loginstatus
        #       is not already IN_PROGRESS, however the
        #       login status may be left 'IN_PROGRESS' because
        #       of exceptions or if the first method of login
        #       (below) is successful. Instead, log the problem,
        #       to be increased to 'warning' level once majority
        #       of issues are resolved.
        if self._loginstatus == _LoginStatus.IN_PROGRESS:
            pywikibot.log(
                '{!r}.login() called when a previous login was in progress.'
                .format(self))

        # There are several ways that the site may already be
        # logged in, and we do not need to hit the server again.
        # logged_in() is False if _userinfo exists, which means this
        # will have no effect for the invocation from api.py
        if self.logged_in():
            self._loginstatus = _LoginStatus.AS_USER
            return

        # check whether a login cookie already exists for this user
        # or check user identity when OAuth enabled
        self._loginstatus = _LoginStatus.IN_PROGRESS
        if user:
            self._username = normalize_username(user)
        try:
            del self.userinfo  # force reload
            if self.userinfo['name'] == self.user():
                return

        # May occur if you are not logged in (no API read permissions).
        except api.APIError:
            pass
        except NoUsername as e:
            if not autocreate:
                raise e

        if self.is_oauth_token_available():
            if self.userinfo['name'] == self.username():
                raise NoUsername('Logging in on %s via OAuth failed' % self)

            if self.username() is None:
                raise NoUsername('No username has been defined in your '
                                 'user-config.py: you have to add in this '
                                 'file the following line:\n'
                                 'usernames[{family!r}][{lang!r}]'
                                 '= {username!r}'
                                 .format(family=self.family,
                                         lang=self.lang,
                                         username=self.userinfo['name']))

            raise NoUsername('Logged in on {site} via OAuth as '
                             '{wrong}, but expect as {right}'
                             .format(site=self,
                                     wrong=self.userinfo['name'],
                                     right=self.username()))

        login_manager = api.LoginManager(site=self, user=self.username())
        if login_manager.login(retry=True, autocreate=autocreate):
            self._username = login_manager.username
            del self.userinfo  # force reloading

            # load userinfo
            assert self.userinfo['name'] == self.username(), \
                '{} != {}'.format(self.userinfo['name'], self.username())

            self._loginstatus = _LoginStatus.AS_USER
        else:
            self._loginstatus = _LoginStatus.NOT_LOGGED_IN  # failure

    def _relogin(self):
        """Force a login sequence without logging out, using the current user.

        This is an internal function which is used to re-login when
        the internal login state does not match the state we receive
        from the site.
        """
        del self.userinfo
        self._loginstatus = _LoginStatus.NOT_LOGGED_IN
        self.login()

    def logout(self):
        """
        Logout of the site and load details for the logged out user.

        Also logs out of the global account if linked to the user.
        U{https://www.mediawiki.org/wiki/API:Logout}

        @raises APIError: Logout is not available when OAuth enabled.
        """
        if self.is_oauth_token_available():
            pywikibot.warning('Using OAuth suppresses logout function')
        req_params = {'action': 'logout'}
        # csrf token introduced in MW 1.24
        with suppress(Error):
            req_params['token'] = self.tokens['csrf']
        uirequest = self._simple_request(**req_params)
        uirequest.submit()
        self._loginstatus = _LoginStatus.NOT_LOGGED_IN

        # Reset tokens and user properties
        del self.userinfo
        self.tokens = TokenWallet(self)
        self._paraminfo = api.ParamInfo(self)

        # Clear also cookies for site's second level domain (T224712)
        api._invalidate_superior_cookies(self.family)

    @property
    def userinfo(self):
        """Retrieve userinfo from site and store in _userinfo attribute.

        To force retrieving userinfo ignoring cache, just delete this
        property.

        self._userinfo will be a dict with the following keys and values:

          - id: user id (numeric str)
          - name: username (if user is logged in)
          - anon: present if user is not logged in
          - groups: list of groups (could be empty)
          - rights: list of rights (could be empty)
          - message: present if user has a new message on talk page
          - blockinfo: present if user is blocked (dict)

        U{https://www.mediawiki.org/wiki/API:Userinfo}
        """
        if not hasattr(self, '_userinfo'):
            uirequest = self._simple_request(
                action='query',
                meta='userinfo',
                uiprop='blockinfo|hasmsg|groups|rights|ratelimits'
            )
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'userinfo' in uidata['query'], \
                   "API userinfo response lacks 'userinfo' key"
            self._userinfo = uidata['query']['userinfo']
            if 'anon' in self._userinfo or not self._userinfo.get('id'):
                pywikibot.warning('No user is logged in on site {}'
                                  .format(self))
        return self._userinfo

    @userinfo.deleter
    def userinfo(self):
        """Delete cached userinfo."""
        if hasattr(self, '_userinfo'):
            del self._userinfo

    @deprecated('userinfo property and userinfo deleter', since='20210110')
    def getuserinfo(self, force: bool = False) -> dict:
        """DEPRECATED. Retrieve userinfo from site.

        @param force: force to retrieve userinfo ignoring cache
        """
        if force:
            del self.userinfo
        return self.userinfo

    @property
    def globaluserinfo(self):
        """Retrieve globaluserinfo from site and cache it.

        self._globaluserinfo will be a dict with the following keys and values:

          - id: user id (numeric str)
          - home: dbname of home wiki
          - registration: registration date as Timestamp
          - groups: list of groups (could be empty)
          - rights: list of rights (could be empty)
          - editcount: global editcount
        """
        if not hasattr(self, '_globaluserinfo'):
            uirequest = self._simple_request(
                action='query',
                meta='globaluserinfo',
                guiprop='groups|rights|editcount'
            )
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'globaluserinfo' in uidata['query'], \
                   "API userinfo response lacks 'userinfo' key"
            self._globaluserinfo = uidata['query']['globaluserinfo']
            ts = self._globaluserinfo['registration']
            iso_ts = pywikibot.Timestamp.fromISOformat(ts)
            self._globaluserinfo['registration'] = iso_ts
        return self._globaluserinfo

    @deprecated('globaluserinfo property', since='20210110')
    def getglobaluserinfo(self):
        """DEPRECATED. Retrieve globaluserinfo."""
        return self.globaluserinfo

    @remove_last_args(['sysop'])
    def is_blocked(self):
        """
        Return True when logged in user is blocked.

        To check whether a user can perform an action,
        the method has_right should be used.
        U{https://www.mediawiki.org/wiki/API:Userinfo}

        @rtype: bool
        """
        return 'blockinfo' in self.userinfo

    def get_searched_namespaces(self, force=False):
        """
        Retrieve the default searched namespaces for the user.

        If no user is logged in, it returns the namespaces used by default.
        Otherwise it returns the user preferences. It caches the last result
        and returns it, if the username or login status hasn't changed.

        @param force: Whether the cache should be discarded.
        @return: The namespaces which are searched by default.
        @rtype: C{set} of L{Namespace}
        """
        # TODO: Integrate into _userinfo
        if (force or not hasattr(self, '_useroptions')
                or self.user() != self._useroptions['_name']):
            uirequest = self._simple_request(
                action='query',
                meta='userinfo',
                uiprop='options'
            )
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'userinfo' in uidata['query'], \
                   "API userinfo response lacks 'userinfo' key"
            self._useroptions = uidata['query']['userinfo']['options']
            # To determine if user name has changed
            self._useroptions['_name'] = (
                None if 'anon' in uidata['query']['userinfo'] else
                uidata['query']['userinfo']['name'])
        return {ns for ns in self.namespaces.values() if ns.id >= 0
                and self._useroptions['searchNs{0}'.format(ns.id)]
                in ['1', True]}

    @property
    def article_path(self):
        """Get the nice article path without $1."""
        # Assert and remove the trailing $1 and assert that it'll end in /
        assert self.siteinfo['general']['articlepath'].endswith('/$1'), \
            'articlepath must end with /$1'
        return self.siteinfo['general']['articlepath'][:-2]

    @staticmethod
    def assert_valid_iter_params(msg_prefix, start, end, reverse,
                                 is_ts=True):
        """Validate iterating API parameters.

        @param msg_prefix: The calling method name
        @type msg_prefix: str
        @param start: The start value to compare
        @param end: The end value to compare
        @param reverse: The reverse option
        @type reverse: bool
        @param is_ts: When comparing timestamps (with is_ts=True) the start
            is usually greater than end. Comparing titles this is vice versa.
        @type is_ts: bool
        @raises AssertionError: start/end values are in wrong order
        """
        if reverse ^ is_ts:
            low, high = end, start
            order = 'follow'
        else:
            low, high = start, end
            order = 'precede'
        msg = ('{method}: "start" must {order} "end" '
               'with reverse={reverse} and is_ts={is_ts} '
               'but "start" is "{start}" and "end" is "{end}".')
        assert low < high, fill(msg.format(method=msg_prefix, order=order,
                                           start=start, end=end,
                                           reverse=reverse, is_ts=is_ts))

    @remove_last_args(['sysop'])
    def has_right(self, right):
        """Return true if and only if the user has a specific right.

        Possible values of 'right' may vary depending on wiki settings.
        U{https://www.mediawiki.org/wiki/API:Userinfo}

        @param right: a specific right to be validated
        @type right: str
        """
        return right.lower() in self.userinfo['rights']

    @remove_last_args(['sysop'])
    def has_group(self, group):
        """Return true if and only if the user is a member of specified group.

        Possible values of 'group' may vary depending on wiki settings,
        but will usually include bot.
        U{https://www.mediawiki.org/wiki/API:Userinfo}
        """
        return group.lower() in self.userinfo['groups']

    @remove_last_args(['sysop'])
    def messages(self):
        """Return true if the user has new messages, and false otherwise."""
        return 'messages' in self.userinfo

    def mediawiki_messages(self, keys, lang=None):
        """Fetch the text of a set of MediaWiki messages.

        The returned dict uses each key to store the associated message.

        @see: U{https://www.mediawiki.org/wiki/API:Allmessages}

        @param keys: MediaWiki messages to fetch
        @type keys: iterable of str
        @param lang: a language code, default is self.lang
        @type lang: str or None

        @rtype OrderedDict
        """
        amlang = lang or self.lang
        if not all(amlang in _mw_msg_cache
                   and _key in _mw_msg_cache[amlang] for _key in keys):
            parameters = {'meta': 'allmessages',
                          'ammessages': keys,
                          'amlang': amlang,
                          }
            msg_query = api.QueryGenerator(site=self, parameters=parameters)

            for msg in msg_query:
                if 'missing' not in msg:
                    _mw_msg_cache[amlang][msg['name']] = msg['*']

            # Check requested keys
            result = OrderedDict()
            for key in keys:
                try:
                    result[key] = _mw_msg_cache[amlang][key]
                except KeyError:
                    raise KeyError("No message '{}' found for lang '{}'"
                                   .format(key, amlang))
            else:
                return result

        return OrderedDict((key, _mw_msg_cache[amlang][key]) for key in keys)

    @deprecated_args(forceReload=None)
    def mediawiki_message(self, key, lang=None) -> str:
        """Fetch the text for a MediaWiki message.

        @param key: name of MediaWiki message
        @type key: str
        @param lang: a language code, default is self.lang
        @type lang: str or None
        """
        return self.mediawiki_messages([key], lang=lang)[key]

    def has_mediawiki_message(self, key, lang=None):
        """Determine if the site defines a MediaWiki message.

        @param key: name of MediaWiki message
        @type key: str
        @param lang: a language code, default is self.lang
        @type lang: str or None

        @rtype: bool
        """
        return self.has_all_mediawiki_messages([key], lang=lang)

    def has_all_mediawiki_messages(self, keys, lang=None):
        """Confirm that the site defines a set of MediaWiki messages.

        @param keys: names of MediaWiki messages
        @type keys: iterable of str
        @param lang: a language code, default is self.lang
        @type lang: str or None

        @rtype: bool
        """
        try:
            self.mediawiki_messages(keys, lang=lang)
        except KeyError:
            return False
        return True

    @property
    def months_names(self):
        """Obtain month names from the site messages.

        The list is zero-indexed, ordered by month in calendar, and should
        be in the original site language.

        @return: list of tuples (month name, abbreviation)
        @rtype: list
        """
        if hasattr(self, '_months_names'):
            return self._months_names

        months_long = ['january', 'february', 'march',
                       'april', 'may_long', 'june',
                       'july', 'august', 'september',
                       'october', 'november', 'december']
        months_short = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                        'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        months = self.mediawiki_messages(months_long + months_short)

        self._months_names = []
        for m_l, m_s in zip(months_long, months_short):
            self._months_names.append((months[m_l], months[m_s]))

        return self._months_names

    def list_to_text(self, args: typing.Iterable[str]) -> str:
        """Convert a list of strings into human-readable text.

        The MediaWiki messages 'and' and 'word-separator' are used as separator
        between the last two arguments.
        If more than two arguments are given, other arguments are
        joined using MediaWiki message 'comma-separator'.

        @param args: text to be expanded
        """
        needed_mw_messages = ('and', 'comma-separator', 'word-separator')
        if not args:
            return ''

        try:
            msgs = self.mediawiki_messages(needed_mw_messages)
        except KeyError:
            raise NotImplementedError(
                'MediaWiki messages missing: {0}'.format(needed_mw_messages))

        args = list(args)
        concat = msgs['and'] + msgs['word-separator']
        return msgs['comma-separator'].join(
            args[:-2] + [concat.join(args[-2:])])

    @deprecated_args(string='text')
    def expand_text(self, text: str, title=None, includecomments=None) -> str:
        """Parse the given text for preprocessing and rendering.

        e.g expand templates and strip comments if includecomments
        parameter is not True. Keeps text inside
        <nowiki></nowiki> tags unchanges etc. Can be used to parse
        magic parser words like {{CURRENTTIMESTAMP}}.

        @param text: text to be expanded
        @type text: str
        @param title: page title without section
        @type title: str
        @param includecomments: if True do not strip comments
        @type includecomments: bool
        """
        if not isinstance(text, str):
            raise ValueError('text must be a string')
        if not text:
            return ''
        req = self._simple_request(action='expandtemplates', text=text)
        if title is not None:
            req['title'] = title
        if includecomments is True:
            req['includecomments'] = ''
        if self.mw_version > '1.24wmf7':
            key = 'wikitext'
            req['prop'] = key
        else:
            key = '*'
        return req.submit()['expandtemplates'][key]

    def getcurrenttimestamp(self):
        """
        Return the server time as a MediaWiki timestamp string.

        It calls L{server_time} first so it queries the server to get the
        current server time.

        @return: the server time
        @rtype: str (as 'yyyymmddhhmmss')
        """
        return self.server_time().totimestampformat()

    def server_time(self):
        """
        Return a Timestamp object representing the current server time.

        It uses the 'time' property of the siteinfo 'general'. It'll force a
        reload before returning the time.

        @return: the current server time
        @rtype: L{Timestamp}
        """
        return pywikibot.Timestamp.fromISOformat(
            self.siteinfo.get('time', expiry=True))

    def getmagicwords(self, word):
        """Return list of localized "word" magic words for the site."""
        if not hasattr(self, '_magicwords'):
            magicwords = self.siteinfo.get('magicwords', cache=False)
            self._magicwords = {item['name']: item['aliases']
                                for item in magicwords}

        if word in self._magicwords:
            return self._magicwords[word]
        else:
            return [word]

    @deprecated('expand_text', since='20150831', future_warning=True)
    def resolvemagicwords(self, wikitext):  # pragma: no cover
        """
        Replace the {{ns:xx}} marks in a wikitext with the namespace names.

        DEPRECATED.
        """
        return self.expand_text(wikitext)

    @remove_last_args(('default', ))
    def redirect(self):
        """Return the localized #REDIRECT keyword."""
        # return the magic word without the preceding '#' character
        return self.getmagicwords('redirect')[0].lstrip('#')

    @deprecated('redirect_regex', since='20210103', future_warning=True)
    def redirectRegex(self):
        """Return a compiled regular expression matching on redirect pages."""
        return self.redirect_regex

    @property
    def redirect_regex(self):
        """Return a compiled regular expression matching on redirect pages.

        Group 1 in the regex match object will be the target title.

        """
        # NOTE: this is needed, since the API can give false positives!
        try:
            keywords = {s.lstrip('#') for s in self.getmagicwords('redirect')}
            keywords.add('REDIRECT')  # just in case
            pattern = '(?:' + '|'.join(keywords) + ')'
        except KeyError:
            # no localized keyword for redirects
            pattern = None
        return super().redirectRegex(pattern)

    @remove_last_args(('default', ))
    def pagenamecodes(self):
        """Return list of localized PAGENAME tags for the site."""
        return self.getmagicwords('pagename')

    @remove_last_args(('default', ))
    def pagename2codes(self):
        """Return list of localized PAGENAMEE tags for the site."""
        return self.getmagicwords('pagenamee')

    def _build_namespaces(self):
        _namespaces = {}

        for nsdata in self.siteinfo.get('namespaces', cache=False).values():
            ns = nsdata.pop('id')
            if ns == 0:
                canonical_name = nsdata.pop('*')
                custom_name = canonical_name
            else:
                custom_name = nsdata.pop('*')
                canonical_name = nsdata.pop('canonical')

            default_case = Namespace.default_case(ns)
            if 'case' not in nsdata:
                nsdata['case'] = default_case or self.siteinfo['case']
            elif default_case is not None:
                assert default_case == nsdata['case'], \
                    'Default case is not consistent'

            namespace = Namespace(ns, canonical_name, custom_name, **nsdata)
            _namespaces[ns] = namespace

        for item in self.siteinfo.get('namespacealiases'):
            ns = int(item['id'])
            try:
                namespace = _namespaces[ns]
            except KeyError:
                pywikibot.warning(
                    'Broken namespace alias "{0}" (id: {1}) on {2}'.format(
                        item['*'], ns, self))
            else:
                if item['*'] not in namespace:
                    namespace.aliases.append(item['*'])

        return _namespaces

    def has_extension(self, name):
        """Determine whether extension `name` is loaded.

        @param name: The extension to check for, case sensitive
        @type name: str
        @return: If the extension is loaded
        @rtype: bool
        """
        extensions = self.siteinfo['extensions']
        for ext in extensions:
            if 'name' in ext and ext['name'] == name:
                return True
        return False

    @property
    def siteinfo(self):
        """Site information dict."""
        return self._siteinfo

    def dbName(self):
        """Return this site's internal id."""
        return self.siteinfo['wikiid']

    @deprecated('APISite.lang', since='20150629', future_warning=True)
    def language(self):  # pragma: no cover
        """Return the code for the language of this Site."""
        return self.lang

    @property
    def lang(self):
        """Return the code for the language of this Site."""
        return self.siteinfo['lang']

    def version(self):
        """Return live project version number as a string.

        Use L{pywikibot.site.mw_version} to compare MediaWiki versions.
        """
        try:
            version = self.siteinfo.get('generator', expiry=1).split(' ')[1]
        except pywikibot.data.api.APIError:
            msg = 'You have no API read permissions.'
            if not self.logged_in():
                msg += ' Seems you are not logged in.'
            pywikibot.error(msg)
            raise

        if MediaWikiVersion(version) < '1.23':
            warn('\n'
                 + fill('Support of MediaWiki {version} will be dropped. '
                        'It is recommended to use MediaWiki 1.23 or above. '
                        'You may use every Pywikibot 5.X for older MediaWiki '
                        'versions. See T268979 for further information.'
                        .format(version=version)), FutureWarning)

        if MediaWikiVersion(version) < '1.19':
            raise RuntimeError(
                'Pywikibot "{}" does not support MediaWiki "{}".\n'
                'Use Pywikibot prior to "5.0" or "python2" branch '
                'instead.'.format(pywikibot.__version__, version))
        return version

    @property
    def mw_version(self):
        """Return self.version() as a MediaWikiVersion object.

        Cache the result for 24 hours.
        @rtype: MediaWikiVersion
        """
        mw_ver, cache_time = getattr(self, '_mw_version_time', (None, None))
        if mw_ver is None or time.time() - cache_time > 60 * 60 * 24:
            mw_ver = MediaWikiVersion(self.version())
            self._mw_version_time = mw_ver, time.time()
        return mw_ver

    @property
    def has_image_repository(self):
        """Return True if site has a shared image repository like Commons."""
        code, fam = self.shared_image_repository()
        return bool(code or fam)

    @property
    def has_data_repository(self):
        """Return True if site has a shared data repository like Wikidata."""
        return self.data_repository() is not None

    @property
    @deprecated('has_data_repository', since='20160405', future_warning=True)
    def has_transcluded_data(self):
        """Return True if site has a shared data repository like Wikidata."""
        return self.has_data_repository

    def image_repository(self):
        """Return Site object for image repository e.g. commons."""
        code, fam = self.shared_image_repository()
        if bool(code or fam):
            return pywikibot.Site(code, fam, self.username())

        return None

    def data_repository(self):
        """
        Return the data repository connected to this site.

        @return: The data repository if one is connected or None otherwise.
        @rtype: pywikibot.site.DataSite or None
        """
        def handle_warning(mod, warning):
            return (mod == 'query' and re.match(
                r'Unrecognized value for parameter [\'"]meta[\'"]: wikibase',
                warning))

        req = self._request(
            expiry=7, parameters={'action': 'query', 'meta': 'wikibase'})
        req._warning_handler = handle_warning
        data = req.submit()
        if 'query' in data and 'wikibase' in data['query']:
            data = data['query']['wikibase']['repo']['url']
            url = data['base'] + data['scriptpath'] + '/index.php'
            try:
                return pywikibot.Site(url=url, user=self.username(),
                                      interface='DataSite')
            except SiteDefinitionError as e:
                pywikibot.warning('Site "{0}" supports wikibase at "{1}", but '
                                  'creation failed: {2}.'.format(self, url, e))
                return None
        else:
            assert 'warnings' in data
            return None

    def is_image_repository(self):
        """Return True if Site object is the image repository."""
        return self is self.image_repository()

    def is_data_repository(self):
        """Return True if its data repository is itself."""
        return self is self.data_repository()

    def page_from_repository(self, item):
        """
        Return a Page for this site object specified by wikibase item.

        @param item: id number of item, "Q###",
        @type item: str
        @return: Page, or Category object given by wikibase item number
            for this site object.
        @rtype: pywikibot.Page or None

        @raises pywikibot.exceptions.UnknownExtension: site has no wikibase
            extension
        @raises NotimplementedError: method not implemented for a wikibase site
        """
        if not self.has_data_repository:
            raise UnknownExtension(
                'Wikibase is not implemented for {0}.'.format(self))
        if self.is_data_repository():
            raise NotImplementedError(
                'page_from_repository method is not implemented for '
                'Wikibase {0}.'.format(self))
        repo = self.data_repository()
        dp = pywikibot.ItemPage(repo, item)
        try:
            page_title = dp.getSitelink(self)
        except pywikibot.NoPage:
            return None
        page = pywikibot.Page(self, page_title)
        if page.namespace() == Namespace.CATEGORY:
            page = pywikibot.Category(page)
        return page

    def nice_get_address(self, title):
        """Return shorter URL path to retrieve page titled 'title'."""
        # 'title' is expected to be URL-encoded already
        return self.siteinfo['articlepath'].replace('$1', title)

    def namespace(self, num, all=False):
        """Return string containing local name of namespace 'num'.

        If optional argument 'all' is true, return all recognized
        values for this namespace.

        @param num: Namespace constant.
        @type num: int
        @param all: If True return a Namespace object. Otherwise
            return the namespace name.
        @return: local name or Namespace object
        @rtype: str or Namespace
        """
        if all:
            return self.namespaces[num]
        return self.namespaces[num][0]

    def _update_page(self, page, query, verify_imageinfo: bool = False):
        """Update page attributes.

        @param page: page object to be updated
        @param query: a api.QueryGenerator
        @param verify_imageinfo: if given, every pageitem is checked
            whether 'imageinfo' is missing. In that case an exception
            is raised.

        @raises NoPage: 'missing' key is found in pageitem
        @raises PageRelatedError: 'imageinfo' is missing in pageitem
        """
        for pageitem in query:
            if not self.sametitle(pageitem['title'],
                                  page.title(with_section=False)):
                raise InconsistentTitleReceived(page, pageitem['title'])
            api.update_page(page, pageitem, query.props)

            if verify_imageinfo and 'imageinfo' not in pageitem:
                if 'missing' in pageitem:
                    raise NoPage(page)
                raise PageRelatedError(
                    page, 'loadimageinfo: Query on %s returned no imageinfo')

    def loadpageinfo(self, page, preload=False):
        """Load page info from api and store in page attributes.

        @see: U{https://www.mediawiki.org/wiki/API:Info}
        """
        title = page.title(with_section=False)
        inprop = 'protection'
        if preload:
            inprop += '|preload'

        query = self._generator(api.PropertyGenerator,
                                type_arg='info',
                                titles=title.encode(self.encoding()),
                                inprop=inprop)
        self._update_page(page, query)

    def loadpageprops(self, page):
        """Load page props for the given page."""
        title = page.title(with_section=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg='pageprops',
                                titles=title.encode(self.encoding()),
                                )
        self._update_page(page, query)

    def loadimageinfo(self, page, history=False,
                      url_width=None, url_height=None, url_param=None):
        """Load image info from api and save in page attributes.

        Parameters correspond to iiprops in:
        [1] U{https://www.mediawiki.org/wiki/API:Imageinfo}

        Parameters validation and error handling left to the API call.

        @param history: if true, return the image's version history
        @param url_width: see iiurlwidth in [1]
        @param url_height: see iiurlheigth in [1]
        @param url_param: see iiurlparam in [1]

        """
        title = page.title(with_section=False)
        args = {'titles': title,
                'iiurlwidth': url_width,
                'iiurlheight': url_height,
                'iiurlparam': url_param,
                }
        if not history:
            args['total'] = 1
        query = self._generator(api.PropertyGenerator,
                                type_arg='imageinfo',
                                iiprop=['timestamp', 'user', 'comment',
                                        'url', 'size', 'sha1', 'mime',
                                        'metadata', 'archivename'],
                                **args)
        self._update_page(page, query, verify_imageinfo=True)

    @deprecated('page.exists()', since='20180218')
    def page_exists(self, page):
        """Return True if and only if page is an existing page on site."""
        return page.pageid > 0

    def page_restrictions(self, page):
        """Return a dictionary reflecting page protections."""
        if not hasattr(page, '_protection'):
            self.loadpageinfo(page)
        return page._protection

    def page_can_be_edited(self, page, action='edit'):
        """Determine if the page can be modified.

        Return True if the bot has the permission of needed restriction level
        for the given action type.

        @param page: a pywikibot.Page object
        @type page: pywikibot.Page
        @param action: a valid restriction type like 'edit', 'move'
        @type action: str
        @rtype: bool

        @raises ValueError: invalid action parameter
        """
        if action not in self.siteinfo.get('restrictions')['types']:
            raise ValueError('{}.page_can_be_edited(): Invalid value "{}" for '
                             '"action" parameter'
                             .format(self.__class__.__name__, action))
        prot_rights = {
            '': action,
            'autoconfirmed': 'editsemiprotected',
            'sysop': 'editprotected',
            'steward': 'editprotected'
        }
        restriction = self.page_restrictions(page).get(action, ('', None))[0]
        user_rights = self.userinfo['rights']
        if prot_rights.get(restriction, restriction) in user_rights:
            return True
        return False

    def page_isredirect(self, page):
        """Return True if and only if page is a redirect."""
        if not hasattr(page, '_isredir'):
            page._isredir = False  # bug T56684
            self.loadpageinfo(page)
        return page._isredir

    def getredirtarget(self, page):
        """
        Return page object for the redirect target of page.

        @param page: page to search redirects for
        @type page: pywikibot.page.BasePage
        @return: redirect target of page
        @rtype: pywikibot.Page

        @raises pywikibot.exceptions.IsNotRedirectPage: page is not a redirect
        @raises RuntimeError: no redirects found
        @raises pywikibot.exceptions.CircularRedirect: page is a circular
            redirect
        @raises pywikibot.exceptions.InterwikiRedirectPage: the redirect
            target is on another site
        """
        if not self.page_isredirect(page):
            raise IsNotRedirectPage(page)
        if hasattr(page, '_redirtarget'):
            return page._redirtarget

        title = page.title(with_section=False)
        query = self._simple_request(
            action='query',
            prop='info',
            titles=title,
            redirects=True)
        result = query.submit()
        if 'query' not in result or 'redirects' not in result['query']:
            raise RuntimeError(
                "getredirtarget: No 'redirects' found for page {}."
                .format(title))

        redirmap = {item['from']: {'title': item['to'],
                                   'section': '#'
                                   + item['tofragment']
                                   if 'tofragment' in item
                                   and item['tofragment']
                                   else ''}
                    for item in result['query']['redirects']}

        # Normalize title
        for item in result['query'].get('normalized', []):
            if item['from'] == title:
                title = item['to']
                break

        if title not in redirmap:
            raise RuntimeError(
                "getredirtarget: 'redirects' contains no key for page {}."
                .format(title))
        target_title = '%(title)s%(section)s' % redirmap[title]

        if self.sametitle(title, target_title):
            raise CircularRedirect(page)

        if 'pages' not in result['query']:
            # No "pages" element might indicate a circular redirect
            # Check that a "to" link is also a "from" link in redirmap
            for _from, _to in redirmap.items():
                if _to['title'] in redirmap:
                    raise CircularRedirect(page)
            else:
                target = pywikibot.Page(source=page.site, title=target_title)

                # Check if target is on another site.
                if target.site != page.site:
                    raise InterwikiRedirectPage(page, target)
                else:
                    # Redirect to Special: & Media: pages, which do not work
                    # like redirects, but are rendered like a redirect.
                    page._redirtarget = target
                    return page._redirtarget

        pagedata = list(result['query']['pages'].values())[0]
        # There should be only one value in 'pages' (the ultimate
        # target, also in case of double redirects).
        if self.sametitle(pagedata['title'], target_title):
            # target_title is the ultimate target
            target = pywikibot.Page(self, pagedata['title'], pagedata['ns'])
            api.update_page(target, pagedata, ['info'])
        else:
            # Target is an intermediate redirect -> double redirect.
            # Do not bypass double-redirects and return the ultimate target;
            # it would be impossible to detect and fix double-redirects.
            # This handles also redirects to sections, as sametitle()
            # does not ignore sections.
            target = pywikibot.Page(self, target_title)

        # Upcast to proper Page subclass.
        ns = target.namespace()
        if ns == 2:
            target = pywikibot.User(target)
        elif ns == 6:
            target = pywikibot.FilePage(target)
        elif ns == 14:
            target = pywikibot.Category(target)
        page._redirtarget = target

        return page._redirtarget

    def load_pages_from_pageids(self, pageids):
        """
        Return a page generator from pageids.

        Pages are iterated in the same order than in the underlying pageids.

        Pageids are filtered and only one page is returned in case of
        duplicate pageids.

        @param pageids: an iterable that returns pageids (str or int),
            or a comma- or pipe-separated string of pageids
            (e.g. '945097,1483753, 956608' or '945097|483753|956608')
        """
        if not pageids:
            return
        if isinstance(pageids, str):
            pageids = pageids.replace('|', ',')
            pageids = pageids.split(',')
            pageids = [p.strip() for p in pageids]

        # Validate pageids.
        gen = (str(int(p)) for p in pageids if int(p) > 0)

        # Find out how many pages can be specified at a time.
        parameter = self._paraminfo.parameter('query+info', 'prop')
        if self.logged_in() and self.has_right('apihighlimits'):
            groupsize = int(parameter['highlimit'])
        else:
            groupsize = int(parameter['limit'])

        for sublist in itergroup(filter_unique(gen), groupsize):
            # Store the order of the input data.
            priority_dict = dict(zip(sublist, range(len(sublist))))

            prio_queue = []
            next_prio = 0
            params = {'pageids': sublist, }
            rvgen = api.PropertyGenerator('info', site=self, parameters=params)

            for pagedata in rvgen:
                title = pagedata['title']
                pageid = str(pagedata['pageid'])
                page = pywikibot.Page(pywikibot.Link(title, source=self))
                api.update_page(page, pagedata)
                priority, page = heapq.heappushpop(prio_queue,
                                                   (priority_dict[pageid],
                                                    page))
                # Smallest priority matches expected one; yield early.
                if priority == next_prio:
                    yield page
                    next_prio += 1
                else:
                    # Push onto the heap.
                    heapq.heappush(prio_queue, (priority, page))

            # Extract data in the same order of the input data.
            while prio_queue:
                priority, page = heapq.heappop(prio_queue)
                yield page

    def preloadpages(self, pagelist, *, groupsize=50, templates=False,
                     langlinks=False, pageprops=False):
        """Return a generator to a list of preloaded pages.

        Pages are iterated in the same order than in the underlying pagelist.
        In case of duplicates in a groupsize batch, return the first entry.

        @param pagelist: an iterable that returns Page objects
        @param groupsize: how many Pages to query at a time
        @type groupsize: int
        @param templates: preload pages (typically templates) transcluded in
            the provided pages
        @type templates: bool
        @param langlinks: preload all language links from the provided pages
            to other languages
        @type langlinks: bool
        @param pageprops: preload various properties defined in page content
        @type pageprops: bool

        """
        props = 'revisions|info|categoryinfo'
        if templates:
            props += '|templates'
        if langlinks:
            props += '|langlinks'
        if pageprops:
            props += '|pageprops'

        parameter = self._paraminfo.parameter('query+info', 'prop')
        if self.logged_in() and self.has_right('apihighlimits'):
            max_ids = int(parameter['highlimit'])
        else:
            max_ids = int(parameter['limit'])  # T78333, T161783

        for sublist in itergroup(pagelist, min(groupsize, max_ids)):
            # Do not use p.pageid property as it will force page loading.
            pageids = [str(p._pageid) for p in sublist
                       if hasattr(p, '_pageid') and p._pageid > 0]
            cache = {}
            # In case of duplicates, return the first entry.
            for priority, page in enumerate(sublist):
                try:
                    cache.setdefault(page.title(with_section=False),
                                     (priority, page))
                except pywikibot.InvalidTitle:
                    pywikibot.exception()

            prio_queue = []
            next_prio = 0
            rvgen = api.PropertyGenerator(props, site=self)
            rvgen.set_maximum_items(-1)  # suppress use of "rvlimit" parameter

            if len(pageids) == len(sublist) and len(set(pageids)) <= max_ids:
                # only use pageids if all pages have them
                rvgen.request['pageids'] = set(pageids)
            else:
                rvgen.request['titles'] = list(cache.keys())
            rvgen.request['rvprop'] = self._rvprops(content=True)
            pywikibot.output('Retrieving %s pages from %s.'
                             % (len(cache), self))

            for pagedata in rvgen:
                pywikibot.debug('Preloading %s' % pagedata, _logger)
                try:
                    if pagedata['title'] not in cache:
                        # API always returns a "normalized" title which is
                        # usually the same as the canonical form returned by
                        # page.title(), but sometimes not (e.g.,
                        # gender-specific localizations of "User" namespace).
                        # This checks to see if there is a normalized title in
                        # the response that corresponds to the canonical form
                        # used in the query.
                        for key in cache:
                            if self.sametitle(key, pagedata['title']):
                                cache[pagedata['title']] = cache[key]
                                break
                        else:
                            pywikibot.warning(
                                'preloadpages: Query returned unexpected '
                                "title '%s'" % pagedata['title'])
                            continue
                except KeyError:
                    pywikibot.debug("No 'title' in %s" % pagedata, _logger)
                    pywikibot.debug('pageids=%s' % pageids, _logger)
                    pywikibot.debug('titles=%s' % list(cache.keys()), _logger)
                    continue
                priority, page = cache[pagedata['title']]
                api.update_page(page, pagedata, rvgen.props)
                priority, page = heapq.heappushpop(prio_queue,
                                                   (priority, page))
                # Smallest priority matches expected one; yield.
                if priority == next_prio:
                    yield page
                    next_prio += 1
                else:
                    # Push back onto the heap.
                    heapq.heappush(prio_queue, (priority, page))

            # Empty the heap.
            while prio_queue:
                priority, page = heapq.heappop(prio_queue)
                yield page

    def validate_tokens(self, types):
        """Validate if requested tokens are acceptable.

        Valid tokens depend on mw version.
        """
        mw_ver = self.mw_version
        if mw_ver < '1.20':
            types_wiki = self._paraminfo.parameter('query+info',
                                                   'token')['type']
            types_wiki.append('patrol')
            valid_types = [token for token in types if token in types_wiki]

        elif mw_ver < '1.24wmf19':
            types_wiki = self._paraminfo.parameter('tokens',
                                                   'type')['type']
            valid_types = [token for token in types if token in types_wiki]
        else:
            types_wiki_old = self._paraminfo.parameter('query+info',
                                                       'token')['type']
            types_wiki_action = self._paraminfo.parameter('tokens',
                                                          'type')['type']
            types_wiki = self._paraminfo.parameter('query+tokens',
                                                   'type')['type']
            valid_types = [token for token in types if token in types_wiki]
            for token in types:
                if (token not in valid_types
                        and (token in types_wiki_old or token
                             in types_wiki_action)):
                    valid_types.append('csrf')
        return valid_types

    def get_tokens(self, types, all=False):
        """Preload one or multiple tokens.

        For MediaWiki version 1.19, only one token can be retrieved at once.
        For MediaWiki versions since 1.24wmfXXX a new token
        system was introduced which reduced the amount of tokens available.
        Most of them were merged into the 'csrf' token. If the token type in
        the parameter is not known it will default to the 'csrf' token.

        The other token types available are:
         - deleteglobalaccount
         - patrol (*)
         - rollback
         - setglobalaccountstatus
         - userrights
         - watch

         (*) For v1.19, the patrol token must be obtained from the query
             list recentchanges.

        @see: U{https://www.mediawiki.org/wiki/API:Tokens}

        @param types: the types of token (e.g., "edit", "move", "delete");
            see API documentation for full list of types
        @type types: iterable
        @param all: load all available tokens, if None only if it can be done
            in one request.
        @type all: bool

        return: a dict with retrieved valid tokens.
        rtype: dict
        """
        def warn_handler(mod, text):
            """Filter warnings for not available tokens."""
            return re.match(
                r'Action \'\w+\' is not allowed for the current user', text)

        user_tokens = {}
        mw_ver = self.mw_version
        if mw_ver < '1.20':
            if all:
                types_wiki = self._paraminfo.parameter('query+info',
                                                       'token')['type']
                types.extend(types_wiki)
            valid_tokens = set(self.validate_tokens(types))
            # don't request patrol
            query = api.PropertyGenerator(
                'info',
                site=self,
                parameters={
                    'intoken': valid_tokens - {'patrol'},
                    'titles': 'Dummy page'})
            query.request._warning_handler = warn_handler

            for item in query:
                pywikibot.debug(str(item), _logger)
                for tokentype in valid_tokens:
                    if (tokentype + 'token') in item:
                        user_tokens[tokentype] = item[tokentype + 'token']

            # patrol token require special handling.
            # TODO: try to catch exceptions?
            if 'patrol' in valid_tokens:
                req = self._simple_request(action='query',
                                           list='recentchanges',
                                           rctoken='patrol', rclimit=1)

                req._warning_handler = warn_handler
                data = req.submit()

                if 'query' in data:
                    data = data['query']
                if 'recentchanges' in data:
                    item = data['recentchanges'][0]
                    pywikibot.debug(str(item), _logger)
                    if 'patroltoken' in item:
                        user_tokens['patrol'] = item['patroltoken']
        else:
            if mw_ver < '1.24wmf19':
                if all is not False:
                    types_wiki = self._paraminfo.parameter('tokens',
                                                           'type')['type']
                    types.extend(types_wiki)
                req = self._simple_request(action='tokens',
                                           type=self.validate_tokens(types))
            else:
                if all is not False:
                    types_wiki = self._paraminfo.parameter('query+tokens',
                                                           'type')['type']
                    types.extend(types_wiki)

                req = self._simple_request(action='query', meta='tokens',
                                           type=self.validate_tokens(types))

            req._warning_handler = warn_handler
            data = req.submit()

            if 'query' in data:
                data = data['query']

            if 'tokens' in data and data['tokens']:
                user_tokens = {key[:-5]: val
                               for key, val in data['tokens'].items()
                               if val != '+\\'}

        return user_tokens

    @deprecated("the 'tokens' property", since='20150218', future_warning=True)
    @remove_last_args(['sysop'])
    def getPatrolToken(self):  # pragma: no cover
        """DEPRECATED: Get patrol token."""
        if self.username() != self.user():
            raise ValueError('The token for {0} was requested but only the '
                             'token for {1} can be retrieved.'.format(
                                 self.username(), self.user()))
        return self.tokens['patrol']

    # following group of methods map more-or-less directly to API queries

    @deprecated_args(
        followRedirects='follow_redirects', filterRedirects='filter_redirects')
    def pagebacklinks(self, page, *, follow_redirects=False,
                      filter_redirects=None, namespaces=None, total=None,
                      content=False):
        """Iterate all pages that link to the given page.

        @see: U{https://www.mediawiki.org/wiki/API:Backlinks}

        @param page: The Page to get links to.
        @param follow_redirects: Also return links to redirects pointing to
            the given page.
        @param filter_redirects: If True, only return redirects to the given
            page. If False, only return non-redirect links. If None, return
            both (no filtering).
        @param namespaces: If present, only return links from the namespaces
            in this list.
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param total: Maximum number of pages to retrieve in total.
        @param content: if True, load the current content of each iterated page
            (default False)
        @rtype: typing.Iterable[pywikibot.Page]
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        bltitle = page.title(with_section=False).encode(self.encoding())
        blargs = {'gbltitle': bltitle}
        if filter_redirects is not None:
            blargs['gblfilterredir'] = ('redirects' if filter_redirects
                                        else 'nonredirects')
        blgen = self._generator(api.PageGenerator, type_arg='backlinks',
                                namespaces=namespaces, total=total,
                                g_content=content, **blargs)
        if follow_redirects:
            # links identified by MediaWiki as redirects may not really be,
            # so we have to check each "redirect" page and see if it
            # really redirects to this page
            # see fixed MediaWiki bug T9304
            redirgen = self._generator(api.PageGenerator,
                                       type_arg='backlinks',
                                       gbltitle=bltitle,
                                       gblfilterredir='redirects')
            genlist = {None: blgen}
            for redir in redirgen:
                if redir == page:
                    # if a wiki contains pages whose titles contain
                    # namespace aliases that existed before those aliases
                    # were defined (example: [[WP:Sandbox]] existed as a
                    # redirect to [[Wikipedia:Sandbox]] before the WP: alias
                    # was created) they can be returned as redirects to
                    # themselves; skip these
                    continue
                if redir.getRedirectTarget() == page:
                    genlist[redir.title()] = self.pagebacklinks(
                        redir, follow_redirects=True,
                        filter_redirects=filter_redirects,
                        namespaces=namespaces,
                        content=content
                    )
            return itertools.chain(*genlist.values())
        return blgen

    @deprecated_args(step=None, filterRedirects='filter_redirects')
    def page_embeddedin(self, page, *, filter_redirects=None, namespaces=None,
                        total=None, content=False):
        """Iterate all pages that embedded the given page as a template.

        @see: U{https://www.mediawiki.org/wiki/API:Embeddedin}

        @param page: The Page to get inclusions for.
        @param filter_redirects: If True, only return redirects that embed
            the given page. If False, only return non-redirect links. If
            None, return both (no filtering).
        @param namespaces: If present, only return links from the namespaces
            in this list.
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param content: if True, load the current content of each iterated page
            (default False)
        @rtype: typing.Iterable[pywikibot.Page]
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        eiargs = {'geititle':
                  page.title(with_section=False).encode(self.encoding())}
        if filter_redirects is not None:
            eiargs['geifilterredir'] = ('redirects' if filter_redirects
                                        else 'nonredirects')
        return self._generator(api.PageGenerator, type_arg='embeddedin',
                               namespaces=namespaces, total=total,
                               g_content=content, **eiargs)

    @deprecated_args(
        step=None, followRedirects='follow_redirects',
        filterRedirects='filter_redirects',
        onlyTemplateInclusion='only_template_inclusion',
        withTemplateInclusion='with_template_inclusion')
    def pagereferences(self, page, *, follow_redirects=False,
                       filter_redirects=None, with_template_inclusion=True,
                       only_template_inclusion=False, namespaces=None,
                       total=None, content=False):
        """
        Convenience method combining pagebacklinks and page_embeddedin.

        @param namespaces: If present, only return links from the namespaces
            in this list.
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @rtype: typing.Iterable[pywikibot.Page]
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if only_template_inclusion:
            return self.page_embeddedin(page,
                                        filter_redirects=filter_redirects,
                                        namespaces=namespaces, total=total,
                                        content=content)
        if not with_template_inclusion:
            return self.pagebacklinks(page, follow_redirects=follow_redirects,
                                      filter_redirects=filter_redirects,
                                      namespaces=namespaces, total=total,
                                      content=content)
        return itertools.islice(
            itertools.chain(
                self.pagebacklinks(
                    page, follow_redirects=follow_redirects,
                    filter_redirects=filter_redirects,
                    namespaces=namespaces, content=content),
                self.page_embeddedin(
                    page, filter_redirects=filter_redirects,
                    namespaces=namespaces, content=content)
            ), total)

    @deprecated_args(step=None)
    def pagelinks(self, page, *, namespaces=None, follow_redirects=False,
                  total=None, content=False):
        """Iterate internal wikilinks contained (or transcluded) on page.

        @see: U{https://www.mediawiki.org/wiki/API:Links}

        @param namespaces: Only iterate pages in these namespaces
            (default: all)
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param follow_redirects: if True, yields the target of any redirects,
            rather than the redirect page
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        plargs = {}
        if hasattr(page, '_pageid'):
            plargs['pageids'] = str(page._pageid)
        else:
            pltitle = page.title(with_section=False).encode(self.encoding())
            plargs['titles'] = pltitle
        return self._generator(api.PageGenerator, type_arg='links',
                               namespaces=namespaces, total=total,
                               g_content=content, redirects=follow_redirects,
                               **plargs)

    # Sortkey doesn't work with generator
    @deprecated_args(withSortKey=None, step=None)
    def pagecategories(self, page, *, total=None, content=False):
        """Iterate categories to which page belongs.

        @see: U{https://www.mediawiki.org/wiki/API:Categories}

        @param content: if True, load the current content of each iterated page
            (default False); note that this means the contents of the
            category description page, not the pages contained in the category
        """
        clargs = {}
        if hasattr(page, '_pageid'):
            clargs['pageids'] = str(page._pageid)
        else:
            clargs['titles'] = page.title(
                with_section=False).encode(self.encoding())
        return self._generator(api.PageGenerator,
                               type_arg='categories', total=total,
                               g_content=content, **clargs)

    @deprecated_args(step=None)
    def pageimages(self, page, *, total=None, content=False):
        """Iterate images used (not just linked) on the page.

        @see: U{https://www.mediawiki.org/wiki/API:Images}

        @param content: if True, load the current content of each iterated page
            (default False); note that this means the content of the image
            description page, not the image itself

        """
        imtitle = page.title(with_section=False).encode(self.encoding())
        return self._generator(api.PageGenerator, type_arg='images',
                               titles=imtitle, total=total,
                               g_content=content)

    @deprecated_args(step=None)
    def pagetemplates(self, page, *, namespaces=None, total=None,
                      content=False):
        """Iterate templates transcluded (not just linked) on the page.

        @see: U{https://www.mediawiki.org/wiki/API:Templates}

        @param namespaces: Only iterate pages in these namespaces
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param content: if True, load the current content of each iterated page
            (default False)

        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        tltitle = page.title(with_section=False).encode(self.encoding())
        return self._generator(api.PageGenerator, type_arg='templates',
                               titles=tltitle, namespaces=namespaces,
                               total=total, g_content=content)

    @deprecated_args(step=None)
    def categorymembers(self, category, *, namespaces=None, sortby=None,
                        reverse=False, starttime=None, endtime=None,
                        startsort=None, endsort=None, total=None,
                        content=False, member_type=None,
                        startprefix=None, endprefix=None):
        """Iterate members of specified category.

        @see: U{https://www.mediawiki.org/wiki/API:Categorymembers}

        @param category: The Category to iterate.
        @param namespaces: If present, only return category members from
            these namespaces. To yield subcategories or files, use
            parameter member_type instead.
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param sortby: determines the order in which results are generated,
            valid values are "sortkey" (default, results ordered by category
            sort key) or "timestamp" (results ordered by time page was
            added to the category)
        @type sortby: str
        @param reverse: if True, generate results in reverse order
            (default False)
        @param starttime: if provided, only generate pages added after this
            time; not valid unless sortby="timestamp"
        @type starttime: pywikibot.Timestamp
        @param endtime: if provided, only generate pages added before this
            time; not valid unless sortby="timestamp"
        @param startsort: if provided, only generate pages that have a
            sortkey >= startsort; not valid if sortby="timestamp"
            (Deprecated in MW 1.24)
        @type startsort: str
        @param endsort: if provided, only generate pages that have a
            sortkey <= endsort; not valid if sortby="timestamp"
            (Deprecated in MW 1.24)
        @type endsort: str
        @param startprefix: if provided, only generate pages >= this title
            lexically; not valid if sortby="timestamp"; overrides "startsort"
        @type startprefix: str
        @param endprefix: if provided, only generate pages < this title
            lexically; not valid if sortby="timestamp"; overrides "endsort"
        @type endprefix: str
        @param content: if True, load the current content of each iterated page
            (default False)
        @type content: bool
        @param member_type: member type; if member_type includes 'page' and is
            used in conjunction with sortby="timestamp", the API may limit
            results to only pages in the first 50 namespaces.
        @type member_type: str or iterable of str;
            values: page, subcat, file
        @rtype: typing.Iterable[pywikibot.Page]
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if category.namespace() != 14:
            raise Error(
                "categorymembers: non-Category page '%s' specified"
                % category.title())
        cmtitle = category.title(with_section=False).encode(self.encoding())
        cmargs = {'type_arg': 'categorymembers', 'gcmtitle': cmtitle,
                  'gcmprop': 'ids|title|sortkey'}
        if sortby in ['sortkey', 'timestamp']:
            cmargs['gcmsort'] = sortby
        elif sortby:
            raise ValueError(
                "categorymembers: invalid sortby value '%s'"
                % sortby)
        if starttime and endtime and starttime > endtime:
            raise ValueError(
                'categorymembers: starttime must be before endtime')
        if startprefix and endprefix and startprefix > endprefix:
            raise ValueError(
                'categorymembers: startprefix must be less than endprefix')
        elif startsort and endsort and startsort > endsort:
            raise ValueError(
                'categorymembers: startsort must be less than endsort')

        if isinstance(member_type, str):
            member_type = {member_type}

        if member_type and sortby == 'timestamp':
            # Covert namespaces to a known type
            namespaces = set(self.namespaces.resolve(namespaces or []))

            if 'page' in member_type:
                excluded_namespaces = set()
                if 'file' not in member_type:
                    excluded_namespaces.add(6)
                if 'subcat' not in member_type:
                    excluded_namespaces.add(14)

                if namespaces:
                    if excluded_namespaces.intersection(namespaces):
                        raise ValueError(
                            'incompatible namespaces %r and member_type %r'
                            % (namespaces, member_type))
                    # All excluded namespaces are not present in `namespaces`.
                else:
                    # If the number of namespaces is greater than permitted by
                    # the API, it will issue a warning and use the namespaces
                    # up until the limit, which will usually be sufficient.
                    # TODO: QueryGenerator should detect when the number of
                    # namespaces requested is higher than available, and split
                    # the request into several batches.
                    excluded_namespaces.update([-1, -2])
                    namespaces = set(self.namespaces) - excluded_namespaces
            else:
                if 'file' in member_type:
                    namespaces.add(6)
                if 'subcat' in member_type:
                    namespaces.add(14)

            member_type = None

        if member_type:
            cmargs['gcmtype'] = member_type

        if reverse:
            cmargs['gcmdir'] = 'desc'
            # API wants start/end params in opposite order if using descending
            # sort; we take care of this reversal for the user
            (starttime, endtime) = (endtime, starttime)
            (startsort, endsort) = (endsort, startsort)
            (startprefix, endprefix) = (endprefix, startprefix)
        if starttime and sortby == 'timestamp':
            cmargs['gcmstart'] = starttime
        elif starttime:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'starttime'")
        if endtime and sortby == 'timestamp':
            cmargs['gcmend'] = endtime
        elif endtime:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'endtime'")
        if startprefix and sortby != 'timestamp':
            cmargs['gcmstartsortkeyprefix'] = startprefix
        elif startprefix:
            raise ValueError('categorymembers: invalid combination of '
                             "'sortby' and 'startprefix'")
        elif startsort and sortby != 'timestamp':
            cmargs['gcmstartsortkey'] = startsort
        elif startsort:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'startsort'")
        if endprefix and sortby != 'timestamp':
            cmargs['gcmendsortkeyprefix'] = endprefix
        elif endprefix:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'endprefix'")
        elif endsort and sortby != 'timestamp':
            cmargs['gcmendsortkey'] = endsort
        elif endsort:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'endsort'")

        return self._generator(api.PageGenerator, namespaces=namespaces,
                               total=total, g_content=content, **cmargs)

    def _rvprops(self, content=False) -> list:
        """Setup rvprop items for loadrevisions and preloadpages.

        @return: rvprop items
        """
        props = ['comment', 'ids', 'flags', 'parsedcomment', 'sha1', 'size',
                 'tags', 'timestamp', 'user', 'userid']
        if content:
            props.append('content')
        if self.mw_version >= '1.21':
            props.append('contentmodel')
        if self.mw_version >= '1.32':
            props.append('roles')
        return props

    @deprecated_args(getText='content', sysop=None)
    @remove_last_args(['rollback'])
    def loadrevisions(self, page, *, content=False, section=None, **kwargs):
        """Retrieve revision information and store it in page object.

        By default, retrieves the last (current) revision of the page,
        unless any of the optional parameters revids, startid, endid,
        starttime, endtime, rvdir, user, excludeuser, or total are
        specified. Unless noted below, all parameters not specified
        default to False.

        If rvdir is False or not specified, startid must be greater than
        endid if both are specified; likewise, starttime must be greater
        than endtime. If rvdir is True, these relationships are reversed.

        @see: U{https://www.mediawiki.org/wiki/API:Revisions}

        @param page: retrieve revisions of this Page and hold the data.
        @type page: pywikibot.Page
        @param content: if True, retrieve the wiki-text of each revision;
            otherwise, only retrieve the revision metadata (default)
        @type content: bool
        @param section: if specified, retrieve only this section of the text
            (content must be True); section must be given by number (top of
            the article is section 0), not name
        @type section: int
        @keyword revids: retrieve only the specified revision ids (raise
            Exception if any of revids does not correspond to page)
        @type revids: an int, a str or a list of ints or strings
        @keyword startid: retrieve revisions starting with this revid
        @keyword endid: stop upon retrieving this revid
        @keyword starttime: retrieve revisions starting at this Timestamp
        @keyword endtime: stop upon reaching this Timestamp
        @keyword rvdir: if false, retrieve newest revisions first (default);
            if true, retrieve oldest first
        @keyword user: retrieve only revisions authored by this user
        @keyword excludeuser: retrieve all revisions not authored by this user
        @keyword total: number of revisions to retrieve
        @raises ValueError: invalid startid/endid or starttime/endtime values
        @raises pywikibot.Error: revids belonging to a different page
        """
        latest = all(val is None for val in kwargs.values())

        revids = kwargs.get('revids')
        startid = kwargs.get('startid')
        starttime = kwargs.get('starttime')
        endid = kwargs.get('endid')
        endtime = kwargs.get('endtime')
        rvdir = kwargs.get('rvdir')
        user = kwargs.get('user')
        step = kwargs.get('step')

        # check for invalid argument combinations
        if (startid is not None or endid is not None) \
           and (starttime is not None or endtime is not None):
            raise ValueError(
                'loadrevisions: startid/endid combined with starttime/endtime')

        if starttime is not None and endtime is not None:
            if rvdir and starttime >= endtime:
                raise ValueError(
                    'loadrevisions: starttime > endtime with rvdir=True')

            if not rvdir and endtime >= starttime:
                raise ValueError(
                    'loadrevisions: endtime > starttime with rvdir=False')

        if startid is not None and endid is not None:
            if rvdir and startid >= endid:
                raise ValueError(
                    'loadrevisions: startid > endid with rvdir=True')
            if not rvdir and endid >= startid:
                raise ValueError(
                    'loadrevisions: endid > startid with rvdir=False')

        rvargs = {'type_arg': 'info|revisions'}
        rvargs['rvprop'] = self._rvprops(content=content)

        if content and section is not None:
            rvargs['rvsection'] = str(section)

        if revids is None:
            rvtitle = page.title(with_section=False).encode(self.encoding())
            rvargs['titles'] = rvtitle
        else:
            if isinstance(revids, (int, str)):
                ids = str(revids)
            else:
                ids = '|'.join(str(r) for r in revids)
            rvargs['revids'] = ids

        if rvdir:
            rvargs['rvdir'] = 'newer'
        elif rvdir is not None:
            rvargs['rvdir'] = 'older'

        if startid:
            rvargs['rvstartid'] = startid
        if endid:
            rvargs['rvendid'] = endid
        if starttime:
            rvargs['rvstart'] = starttime
        if endtime:
            rvargs['rvend'] = endtime

        if user:
            rvargs['rvuser'] = user
        else:
            rvargs['rvexcludeuser'] = kwargs.get('excludeuser')

        # assemble API request
        rvgen = self._generator(api.PropertyGenerator,
                                total=kwargs.get('total'), **rvargs)

        if step:
            rvgen.set_query_increment = step

        if latest or 'revids' in rvgen.request:
            rvgen.set_maximum_items(-1)  # suppress use of rvlimit parameter

        for pagedata in rvgen:
            if not self.sametitle(pagedata['title'],
                                  page.title(with_section=False)):
                raise InconsistentTitleReceived(page, pagedata['title'])
            if 'missing' in pagedata:
                raise NoPage(page)
            api.update_page(page, pagedata, rvgen.props)

    # TODO: expand support to other parameters of action=parse?
    def get_parsed_page(self, page):
        """Retrieve parsed text of the page using action=parse.

        @see: U{https://www.mediawiki.org/wiki/API:Parse}
        """
        req = self._simple_request(action='parse', page=page)
        data = req.submit()
        assert 'parse' in data, "API parse response lacks 'parse' key"
        assert 'text' in data['parse'], "API parse response lacks 'text' key"
        parsed_text = data['parse']['text']['*']
        return parsed_text

    @deprecated_args(step=None)
    def pagelanglinks(self, page, *, total=None, include_obsolete=False):
        """Iterate all interlanguage links on page, yielding Link objects.

        @see: U{https://www.mediawiki.org/wiki/API:Langlinks}

        @param include_obsolete: if true, yield even Link objects whose
                                 site is obsolete
        """
        lltitle = page.title(with_section=False)
        llquery = self._generator(api.PropertyGenerator,
                                  type_arg='langlinks',
                                  titles=lltitle.encode(self.encoding()),
                                  total=total)
        for pageitem in llquery:
            if not self.sametitle(pageitem['title'], lltitle):
                raise InconsistentTitleReceived(page, pageitem['title'])
            if 'langlinks' not in pageitem:
                continue
            for linkdata in pageitem['langlinks']:
                link = pywikibot.Link.langlinkUnsafe(linkdata['lang'],
                                                     linkdata['*'],
                                                     source=self)
                if link.site.obsolete and not include_obsolete:
                    continue

                yield link

    @deprecated_args(step=None)
    def page_extlinks(self, page, *, total=None):
        """Iterate all external links on page, yielding URL strings.

        @see: U{https://www.mediawiki.org/wiki/API:Extlinks}
        """
        eltitle = page.title(with_section=False)
        elquery = self._generator(api.PropertyGenerator, type_arg='extlinks',
                                  titles=eltitle.encode(self.encoding()),
                                  total=total)
        for pageitem in elquery:
            if not self.sametitle(pageitem['title'], eltitle):
                raise InconsistentTitleReceived(page, pageitem['title'])
            if 'extlinks' not in pageitem:
                continue
            for linkdata in pageitem['extlinks']:
                yield linkdata['*']

    def getcategoryinfo(self, category):
        """Retrieve data on contents of category.

        @see: U{https://www.mediawiki.org/wiki/API:Categoryinfo}
        """
        cititle = category.title(with_section=False)
        ciquery = self._generator(api.PropertyGenerator,
                                  type_arg='categoryinfo',
                                  titles=cititle.encode(self.encoding()))
        self._update_page(category, ciquery)

    def categoryinfo(self, category):
        """Retrieve data on contents of category."""
        if not hasattr(category, '_catinfo'):
            self.getcategoryinfo(category)
        if not hasattr(category, '_catinfo'):
            # a category that exists but has no contents returns no API result
            category._catinfo = {'size': 0, 'pages': 0, 'files': 0,
                                 'subcats': 0}
        return category._catinfo

    @deprecated_args(throttle=None, limit='total', step=None,
                     includeredirects='filterredir')
    def allpages(self, start='!', prefix='', namespace=0, filterredir=None,
                 filterlanglinks=None, minsize=None, maxsize=None,
                 protect_type=None, protect_level=None, reverse=False,
                 total=None, content=False):
        """Iterate pages in a single namespace.

        @see: U{https://www.mediawiki.org/wiki/API:Allpages}

        @param start: Start at this title (page need not exist).
        @param prefix: Only yield pages starting with this string.
        @param namespace: Iterate pages from this (single) namespace
        @type namespace: int or Namespace.
        @param filterredir: if True, only yield redirects; if False (and not
            None), only yield non-redirects (default: yield both)
        @param filterlanglinks: if True, only yield pages with language links;
            if False (and not None), only yield pages without language links
            (default: yield both)
        @param minsize: if present, only yield pages at least this many
            bytes in size
        @param maxsize: if present, only yield pages at most this many bytes
            in size
        @param protect_type: only yield pages that have a protection of the
            specified type
        @type protect_type: str
        @param protect_level: only yield pages that have protection at this
            level; can only be used if protect_type is specified
        @param reverse: if True, iterate in reverse Unicode lexigraphic
            order (default: iterate in forward order)
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: the namespace identifier was not resolved
        @raises TypeError: the namespace identifier has an inappropriate
            type such as bool, or an iterable with more than one namespace
        """
        # backward compatibility test
        if filterredir not in (True, False, None):
            old = filterredir
            if filterredir:
                if filterredir == 'only':
                    filterredir = True
                else:
                    filterredir = None
            else:
                filterredir = False
            warn('The value "{0!r}" for "filterredir" is deprecated; use '
                 '{1} instead.'.format(old, filterredir),
                 DeprecationWarning, 3)

        apgen = self._generator(api.PageGenerator, type_arg='allpages',
                                namespaces=namespace,
                                gapfrom=start, total=total,
                                g_content=content)
        if prefix:
            apgen.request['gapprefix'] = prefix
        if filterredir is not None:
            apgen.request['gapfilterredir'] = ('redirects' if filterredir else
                                               'nonredirects')
        if filterlanglinks is not None:
            apgen.request['gapfilterlanglinks'] = ('withlanglinks'
                                                   if filterlanglinks else
                                                   'withoutlanglinks')
        if isinstance(minsize, int):
            apgen.request['gapminsize'] = str(minsize)
        if isinstance(maxsize, int):
            apgen.request['gapmaxsize'] = str(maxsize)
        if isinstance(protect_type, str):
            apgen.request['gapprtype'] = protect_type
            if isinstance(protect_level, str):
                apgen.request['gapprlevel'] = protect_level
        if reverse:
            apgen.request['gapdir'] = 'descending'
        return apgen

    @deprecated_args(step=None)
    def alllinks(self, start='!', prefix='', namespace=0, unique=False,
                 fromids=False, total=None):
        """Iterate all links to pages (which need not exist) in one namespace.

        Note that, in practice, links that were found on pages that have
        been deleted may not have been removed from the links table, so this
        method can return false positives.

        @see: U{https://www.mediawiki.org/wiki/API:Alllinks}

        @param start: Start at this title (page need not exist).
        @param prefix: Only yield pages starting with this string.
        @param namespace: Iterate pages from this (single) namespace
        @type namespace: int or Namespace
        @param unique: If True, only iterate each link title once (default:
            iterate once for each linking page)
        @param fromids: if True, include the pageid of the page containing
            each link (default: False) as the '_fromid' attribute of the Page;
            cannot be combined with unique
        @raises KeyError: the namespace identifier was not resolved
        @raises TypeError: the namespace identifier has an inappropriate
            type such as bool, or an iterable with more than one namespace
        """
        if unique and fromids:
            raise Error('alllinks: unique and fromids cannot both be True.')
        algen = self._generator(api.ListGenerator, type_arg='alllinks',
                                namespaces=namespace, alfrom=start,
                                total=total, alunique=unique)
        if prefix:
            algen.request['alprefix'] = prefix
        if fromids:
            algen.request['alprop'] = 'title|ids'
        for link in algen:
            p = pywikibot.Page(self, link['title'], link['ns'])
            if fromids:
                p._fromid = link['fromid']
            yield p

    @deprecated_args(step=None)
    def allcategories(self, start='!', prefix='', total=None,
                      reverse=False, content=False):
        """Iterate categories used (which need not have a Category page).

        Iterator yields Category objects. Note that, in practice, links that
        were found on pages that have been deleted may not have been removed
        from the database table, so this method can return false positives.

        @see: U{https://www.mediawiki.org/wiki/API:Allcategories}

        @param start: Start at this category title (category need not exist).
        @param prefix: Only yield categories starting with this string.
        @param reverse: if True, iterate in reverse Unicode lexigraphic
            order (default: iterate in forward order)
        @param content: if True, load the current content of each iterated page
            (default False); note that this means the contents of the category
            description page, not the pages that are members of the category
        """
        acgen = self._generator(api.PageGenerator,
                                type_arg='allcategories', gacfrom=start,
                                total=total, g_content=content)
        if prefix:
            acgen.request['gacprefix'] = prefix
        if reverse:
            acgen.request['gacdir'] = 'descending'
        return acgen

    def isBot(self, username):
        """Return True is username is a bot user."""
        return username in (userdata['name'] for userdata in self.botusers())

    @deprecated_args(step=None)
    def botusers(self, total=None):
        """Iterate bot users.

        Iterated values are dicts containing 'name', 'userid', 'editcount',
        'registration', and 'groups' keys. 'groups' will be present only if
        the user is a member of at least 1 group, and will be a list of
        str; all the other values are str and should always be present.
        """
        if not hasattr(self, '_bots'):
            self._bots = {}

        if not self._bots:
            for item in self.allusers(group='bot', total=total):
                self._bots.setdefault(item['name'], item)

        yield from self._bots.values()

    @deprecated_args(step=None)
    def allusers(self, start='!', prefix='', group=None, total=None):
        """Iterate registered users, ordered by username.

        Iterated values are dicts containing 'name', 'editcount',
        'registration', and (sometimes) 'groups' keys. 'groups' will be
        present only if the user is a member of at least 1 group, and
        will be a list of str; all the other values are str and should
        always be present.

        @see: U{https://www.mediawiki.org/wiki/API:Allusers}

        @param start: start at this username (name need not exist)
        @param prefix: only iterate usernames starting with this substring
        @param group: only iterate users that are members of this group
        @type group: str
        """
        augen = self._generator(api.ListGenerator, type_arg='allusers',
                                auprop='editcount|groups|registration',
                                aufrom=start, total=total)
        if prefix:
            augen.request['auprefix'] = prefix
        if group:
            augen.request['augroup'] = group
        return augen

    @deprecated_args(step=None)
    def allimages(self, start='!', prefix='', minsize=None, maxsize=None,
                  reverse=False, sha1=None, sha1base36=None,
                  total=None, content=False):
        """Iterate all images, ordered by image title.

        Yields FilePages, but these pages need not exist on the wiki.

        @see: U{https://www.mediawiki.org/wiki/API:Allimages}

        @param start: start at this title (name need not exist)
        @param prefix: only iterate titles starting with this substring
        @param minsize: only iterate images of at least this many bytes
        @param maxsize: only iterate images of no more than this many bytes
        @param reverse: if True, iterate in reverse lexigraphic order
        @param sha1: only iterate image (it is theoretically possible there
            could be more than one) with this sha1 hash
        @param sha1base36: same as sha1 but in base 36
        @param content: if True, load the current content of each iterated page
            (default False); note that this means the content of the image
            description page, not the image itself
        """
        aigen = self._generator(api.PageGenerator,
                                type_arg='allimages', gaifrom=start,
                                total=total, g_content=content)
        if prefix:
            aigen.request['gaiprefix'] = prefix
        if isinstance(minsize, int):
            aigen.request['gaiminsize'] = str(minsize)
        if isinstance(maxsize, int):
            aigen.request['gaimaxsize'] = str(maxsize)
        if reverse:
            aigen.request['gaidir'] = 'descending'
        if sha1:
            aigen.request['gaisha1'] = sha1
        if sha1base36:
            aigen.request['gaisha1base36'] = sha1base36
        return aigen

    @deprecated_args(limit='total')  # ignore falimit setting
    def filearchive(self, start=None, end=None, reverse=False, total=None,
                    **kwargs):
        """Iterate archived files.

        Yields dict of file archive informations.

        @see: U{https://www.mediawiki.org/wiki/API:filearchive}

        @param start: start at this title (name need not exist)
        @param end: end at this title (name need not exist)
        @param reverse: if True, iterate in reverse lexigraphic order
        @param total: maximum number of pages to retrieve in total
        @keyword prefix: only iterate titles starting with this substring
        @keyword sha1: only iterate image with this sha1 hash
        @keyword sha1base36: same as sha1 but in base 36
        @keyword prop: Image information to get. Default is timestamp
        """
        if start and end:
            self.assert_valid_iter_params(
                'filearchive', start, end, reverse, is_ts=False)
        fagen = self._generator(api.ListGenerator,
                                type_arg='filearchive',
                                fafrom=start,
                                fato=end,
                                total=total)
        for k, v in kwargs.items():
            fagen.request['fa' + k] = v
        if reverse:
            fagen.request['fadir'] = 'descending'
        return fagen

    @deprecated_args(step=None)
    def blocks(self, starttime=None, endtime=None, reverse=False,
               blockids=None, users=None, iprange: Optional[str] = None,
               total: Optional[int] = None):
        """Iterate all current blocks, in order of creation.

        The iterator yields dicts containing keys corresponding to the
        block properties.

        @see: U{https://www.mediawiki.org/wiki/API:Blocks}

        @note: logevents only logs user blocks, while this method
            iterates all blocks including IP ranges.
        @note: C{iprange} parameter cannot be used together with C{users}.

        @param starttime: start iterating at this Timestamp
        @type starttime: pywikibot.Timestamp
        @param endtime: stop iterating at this Timestamp
        @type endtime: pywikibot.Timestamp
        @param reverse: if True, iterate oldest blocks first (default: newest)
        @type reverse: bool
        @param blockids: only iterate blocks with these id numbers. Numbers
            must be separated by '|' if given by a str.
        @type blockids: str, tuple or list
        @param users: only iterate blocks affecting these usernames or IPs
        @type users: str, tuple or list
        @param iprange: a single IP or an IP range. Ranges broader than
            IPv4/16 or IPv6/19 are not accepted.
        @param total: total amount of block entries
        """
        if starttime and endtime:
            self.assert_valid_iter_params('blocks', starttime, endtime,
                                          reverse)
        bkgen = self._generator(api.ListGenerator, type_arg='blocks',
                                total=total)
        bkgen.request['bkprop'] = ['id', 'user', 'by', 'timestamp', 'expiry',
                                   'reason', 'range', 'flags', 'userid']
        if starttime:
            bkgen.request['bkstart'] = starttime
        if endtime:
            bkgen.request['bkend'] = endtime
        if reverse:
            bkgen.request['bkdir'] = 'newer'
        if blockids:
            bkgen.request['bkids'] = blockids
        if users:
            if isinstance(users, str):
                users = users.split('|')
            # actual IPv6 addresses (anonymous users) are uppercase, but they
            # have never a :: in the username (so those are registered users)
            users = [user.upper() if is_IP(user) and '::' not in user else user
                     for user in users]
            bkgen.request['bkusers'] = users
        elif iprange:
            bkgen.request['bkip'] = iprange
        return bkgen

    @deprecated_args(step=None)
    def exturlusage(self, url: Optional[str] = None,
                    protocol: Optional[str] = None, namespaces=None,
                    total: Optional[int] = None, content=False):
        """Iterate Pages that contain links to the given URL.

        @see: U{https://www.mediawiki.org/wiki/API:Exturlusage}

        @param url: The URL to search for (with or without the protocol
            prefix); this may include a '*' as a wildcard, only at the start
            of the hostname
        @param namespaces: list of namespace numbers to fetch contribs from
        @type namespaces: list of int
        @param total: Maximum number of pages to retrieve in total
        @param protocol: Protocol to search for, likely http or https, http by
                default. Full list shown on Special:LinkSearch wikipage
        """
        if url is not None:
            found_protocol, _, url = url.rpartition('://')

            # If url is * we make it None in order to search for every page
            # with any URL.
            if url == '*':
                url = None

            if found_protocol:
                if protocol and protocol != found_protocol:
                    raise ValueError('Protocol was specified, but a different '
                                     'one was found in searched url')
                protocol = found_protocol

        if not protocol:
            protocol = 'http'

        return self._generator(api.PageGenerator, type_arg='exturlusage',
                               geuquery=url, geuprotocol=protocol,
                               namespaces=namespaces,
                               total=total, g_content=content)

    @deprecated_args(step=None)
    def imageusage(self, image, namespaces=None, filterredir=None,
                   total=None, content=False):
        """Iterate Pages that contain links to the given FilePage.

        @see: U{https://www.mediawiki.org/wiki/API:Imageusage}

        @param image: the image to search for (FilePage need not exist on
            the wiki)
        @type image: pywikibot.FilePage
        @param namespaces: If present, only iterate pages in these namespaces
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param filterredir: if True, only yield redirects; if False (and not
            None), only yield non-redirects (default: yield both)
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        iuargs = {'giutitle': image.title(with_section=False)}
        if filterredir is not None:
            iuargs['giufilterredir'] = ('redirects' if filterredir else
                                        'nonredirects')
        return self._generator(api.PageGenerator, type_arg='imageusage',
                               namespaces=namespaces,
                               total=total, g_content=content, **iuargs)

    @property
    def logtypes(self):
        """Return a set of log types available on current site."""
        return set(filter(None, self._paraminfo.parameter(
            'query+logevents', 'type')['type']))

    @deprecated_args(step=None)
    def logevents(self, logtype: Optional[str] = None,
                  user: Optional[str] = None, page=None,
                  namespace=None, start=None, end=None,
                  reverse: bool = False, tag: Optional[str] = None,
                  total: Optional[int] = None):
        """Iterate all log entries.

        @see: U{https://www.mediawiki.org/wiki/API:Logevents}

        @note: logevents with logtype='block' only logs user blocks whereas
            site.blocks iterates all blocks including IP ranges.

        @param logtype: only iterate entries of this type
            (see mediawiki api documentation for available types)
        @param user: only iterate entries that match this user name
        @param page: only iterate entries affecting this page
        @type page: pywikibot.Page or str
        @param namespace: namespace(s) to retrieve logevents from
        @type namespace: int or Namespace or an iterable of them
        @note: due to an API limitation, if namespace param contains multiple
            namespaces, log entries from all namespaces will be fetched from
            the API and will be filtered later during iteration.
        @param start: only iterate entries from and after this Timestamp
        @type start: Timestamp or ISO date string
        @param end: only iterate entries up to and through this Timestamp
        @type end: Timestamp or ISO date string
        @param reverse: if True, iterate oldest entries first (default: newest)
        @param tag: only iterate entries tagged with this tag
        @param total: maximum number of events to iterate
        @rtype: iterable

        @raises KeyError: the namespace identifier was not resolved
        @raises TypeError: the namespace identifier has an inappropriate
            type such as bool, or an iterable with more than one namespace
        """
        if start and end:
            self.assert_valid_iter_params('logevents', start, end, reverse)

        legen = self._generator(api.LogEntryListGenerator, type_arg=logtype,
                                total=total)
        if logtype is not None:
            legen.request['letype'] = logtype
        if user is not None:
            legen.request['leuser'] = user
        if page is not None:
            legen.request['letitle'] = page
        if start is not None:
            legen.request['lestart'] = start
        if end is not None:
            legen.request['leend'] = end
        if reverse:
            legen.request['ledir'] = 'newer'
        if namespace is not None:
            legen.set_namespace(namespace)
        if tag:
            legen.request['letag'] = tag

        return legen

    @deprecated_args(includeredirects='redirect', namespace='namespaces',
                     number='total', rcend='end', rclimit='total',
                     rcnamespace='namespaces', rcstart='start',
                     rctype='changetype', showAnon='anon', showBot='bot',
                     showMinor='minor', showPatrolled='patrolled',
                     showRedirects='redirect', topOnly='top_only')
    def recentchanges(self, *,
                      start=None,
                      end=None,
                      reverse: bool = False,
                      namespaces=None,
                      changetype: Optional[str] = None,
                      minor: Optional[bool] = None,
                      bot: Optional[bool] = None,
                      anon: Optional[bool] = None,
                      redirect: Optional[bool] = None,
                      patrolled: Optional[bool] = None,
                      top_only: bool = False,
                      total: Optional[int] = None,
                      user: Union[str, List[str], None] = None,
                      excludeuser: Union[str, List[str], None] = None,
                      tag: Optional[str] = None):
        """Iterate recent changes.

        @see: U{https://www.mediawiki.org/wiki/API:RecentChanges}

        @param start: Timestamp to start listing from
        @type start: pywikibot.Timestamp
        @param end: Timestamp to end listing at
        @type end: pywikibot.Timestamp
        @param reverse: if True, start with oldest changes (default: newest)
        @param namespaces: only iterate pages in these namespaces
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param changetype: only iterate changes of this type ("edit" for
            edits to existing pages, "new" for new pages, "log" for log
            entries)
        @param minor: if True, only list minor edits; if False, only list
            non-minor edits; if None, list all
        @param bot: if True, only list bot edits; if False, only list
            non-bot edits; if None, list all
        @param anon: if True, only list anon edits; if False, only list
            non-anon edits; if None, list all
        @param redirect: if True, only list edits to redirect pages; if
            False, only list edits to non-redirect pages; if None, list all
        @param patrolled: if True, only list patrolled edits; if False,
            only list non-patrolled edits; if None, list all
        @param top_only: if True, only list changes that are the latest
            revision (default False)
        @param user: if not None, only list edits by this user or users
        @param excludeuser: if not None, exclude edits by this user or users
        @param tag: a recent changes tag
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if start and end:
            self.assert_valid_iter_params('recentchanges', start, end, reverse)

        rcgen = self._generator(api.ListGenerator, type_arg='recentchanges',
                                rcprop='user|comment|timestamp|title|ids'
                                       '|sizes|redirect|loginfo|flags|tags',
                                namespaces=namespaces,
                                total=total, rctoponly=top_only)
        if start is not None:
            rcgen.request['rcstart'] = start
        if end is not None:
            rcgen.request['rcend'] = end
        if reverse:
            rcgen.request['rcdir'] = 'newer'
        if changetype:
            rcgen.request['rctype'] = changetype
        filters = {'minor': minor,
                   'bot': bot,
                   'anon': anon,
                   'redirect': redirect,
                   }
        if patrolled is not None and (
                self.has_right('patrol') or self.has_right('patrolmarks')):
            rcgen.request['rcprop'] += ['patrolled']
            filters['patrolled'] = patrolled
        rcgen.request['rcshow'] = api.OptionSet(self, 'recentchanges', 'show',
                                                filters)

        if user:
            rcgen.request['rcuser'] = user

        if excludeuser:
            rcgen.request['rcexcludeuser'] = excludeuser
        rcgen.request['rctag'] = tag
        return rcgen

    @deprecated_args(number='total', step=None, key='searchstring',
                     getredirects='get_redirects')
    def search(self, searchstring: str, namespaces=None, where='text',
               get_redirects=False, total=None, content=False):
        """Iterate Pages that contain the searchstring.

        Note that this may include non-existing Pages if the wiki's database
        table contains outdated entries.

        @see: U{https://www.mediawiki.org/wiki/API:Search}

        @param searchstring: the text to search for
        @param where: Where to search; value must be "text", "title" or
            "nearmatch" (many wikis do not support title or nearmatch search)
        @param namespaces: search only in these namespaces (defaults to all)
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param get_redirects: if True, include redirects in results. Since
            version MediaWiki 1.23 it will always return redirects.
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        where_types = ['nearmatch', 'text', 'title', 'titles']
        if not searchstring:
            raise Error('search: searchstring cannot be empty')
        if where not in where_types:
            raise Error("search: unrecognized 'where' value: %s" % where)
        if where in ('title', 'titles'):
            if self.has_extension('CirrusSearch'):
                # 'title' search was disabled, use intitle instead
                searchstring = 'intitle:' + searchstring
                issue_deprecation_warning(
                    "where='{0}'".format(where),
                    "searchstring='{0}'".format(searchstring),
                    since='20160224')
                where = None  # default
            else:
                if where == 'titles':
                    issue_deprecation_warning("where='titles'",
                                              "where='title'",
                                              warning_class=FutureWarning,
                                              since='20160224')
                where = 'title'
        if not namespaces and namespaces != 0:
            namespaces = [ns_id for ns_id in self.namespaces if ns_id >= 0]
        srgen = self._generator(api.PageGenerator, type_arg='search',
                                gsrsearch=searchstring, gsrwhat=where,
                                namespaces=namespaces,
                                total=total, g_content=content)
        if self.mw_version < '1.23':
            srgen.request['gsrredirects'] = get_redirects
        return srgen

    @deprecated_args(step=None, showMinor='minor')
    def usercontribs(self, user=None, userprefix=None, start=None, end=None,
                     reverse=False, namespaces=None, minor=None,
                     total: Optional[int] = None, top_only=False):
        """Iterate contributions by a particular user.

        Iterated values are in the same format as recentchanges.

        @see: U{https://www.mediawiki.org/wiki/API:Usercontribs}

        @param user: Iterate contributions by this user (name or IP)
        @param userprefix: Iterate contributions by all users whose names
            or IPs start with this substring
        @param start: Iterate contributions starting at this Timestamp
        @param end: Iterate contributions ending at this Timestamp
        @param reverse: Iterate oldest contributions first (default: newest)
        @param namespaces: only iterate pages in these namespaces
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param minor: if True, iterate only minor edits; if False and
            not None, iterate only non-minor edits (default: iterate both)
        @param total: limit result to this number of pages
        @param top_only: if True, iterate only edits which are the latest
            revision (default: False)
        @raises pywikibot.exceptions.Error: either user or userprefix must be
            non-empty
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if not (user or userprefix):
            raise Error(
                'usercontribs: either user or userprefix must be non-empty')

        if start and end:
            self.assert_valid_iter_params('usercontribs', start, end, reverse)

        ucgen = self._generator(api.ListGenerator, type_arg='usercontribs',
                                ucprop='ids|title|timestamp|comment|flags',
                                namespaces=namespaces,
                                total=total, uctoponly=top_only)
        if user:
            ucgen.request['ucuser'] = user
        if userprefix:
            ucgen.request['ucuserprefix'] = userprefix
        if start is not None:
            ucgen.request['ucstart'] = str(start)
        if end is not None:
            ucgen.request['ucend'] = str(end)
        if reverse:
            ucgen.request['ucdir'] = 'newer'
        option_set = api.OptionSet(self, 'usercontribs', 'show')
        option_set['minor'] = minor
        ucgen.request['ucshow'] = option_set
        return ucgen

    @deprecated_args(step=None, showMinor='minor', showAnon='anon',
                     showBot='bot')
    def watchlist_revs(self, start=None, end=None, reverse=False,
                       namespaces=None, minor=None, bot=None,
                       anon=None, total=None):
        """Iterate revisions to pages on the bot user's watchlist.

        Iterated values will be in same format as recentchanges.

        @see: U{https://www.mediawiki.org/wiki/API:Watchlist}

        @param start: Iterate revisions starting at this Timestamp
        @param end: Iterate revisions ending at this Timestamp
        @param reverse: Iterate oldest revisions first (default: newest)
        @param namespaces: only iterate pages in these namespaces
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param minor: if True, only list minor edits; if False (and not
            None), only list non-minor edits
        @param bot: if True, only list bot edits; if False (and not
            None), only list non-bot edits
        @param anon: if True, only list anon edits; if False (and not
            None), only list non-anon edits
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if start and end:
            self.assert_valid_iter_params(
                'watchlist_revs', start, end, reverse)

        wlgen = self._generator(
            api.ListGenerator, type_arg='watchlist',
            wlprop='user|comment|timestamp|title|ids|flags',
            wlallrev='', namespaces=namespaces, total=total)
        # TODO: allow users to ask for "patrol" as well?
        if start is not None:
            wlgen.request['wlstart'] = start
        if end is not None:
            wlgen.request['wlend'] = end
        if reverse:
            wlgen.request['wldir'] = 'newer'
        filters = {'minor': minor, 'bot': bot, 'anon': anon}
        wlgen.request['wlshow'] = api.OptionSet(self, 'watchlist', 'show',
                                                filters)
        return wlgen

    def _check_view_deleted(self, msg_prefix: str, prop: List[str]) -> None:
        """Check if the user can view deleted comments and content.

        @param msg_prefix: The calling method name
        @param prop: Requested props to check
        @raises UserRightsError: user cannot view a requested prop
        """
        err = '{}: User:{} not authorized to view '.format(msg_prefix,
                                                           self.user())
        if not self.has_right('deletedhistory'):
            if self.mw_version < '1.34':
                raise UserRightsError(err + 'deleted revisions.')
            if 'comment' in prop or 'parsedcomment' in prop:
                raise UserRightsError(err + 'comments of deleted revisions.')
        if ('content' in prop and not (self.has_right('deletedtext')
                                       or self.has_right('undelete'))):
            raise UserRightsError(err + 'deleted content.')

    @deprecated_args(step=None, get_text='content', page='titles',
                     limit='total')
    def deletedrevs(self, titles=None, start=None, end=None,
                    reverse: bool = False,
                    content=False, total=None, **kwargs):
        """Iterate deleted revisions.

        Each value returned by the iterator will be a dict containing the
        'title' and 'ns' keys for a particular Page and a 'revisions' key
        whose value is a list of revisions in the same format as
        recentchanges plus a 'content' element with key '*' if requested
        when 'content' parameter is set. For older wikis a 'token' key is
        also given with the content request.

        @see: U{https://www.mediawiki.org/wiki/API:Deletedrevisions}

        @param titles: The page titles to check for deleted revisions
        @type titles: str (multiple titles delimited with '|')
            or pywikibot.Page or typing.Iterable[pywikibot.Page]
            or typing.Iterable[str]
        @keyword revids: Get revisions by their ID

        @note either titles or revids must be set but not both

        @param start: Iterate revisions starting at this Timestamp
        @param end: Iterate revisions ending at this Timestamp
        @param reverse: Iterate oldest revisions first (default: newest)
        @param content: If True, retrieve the content of each revision
        @param total: number of revisions to retrieve
        @keyword user: List revisions by this user
        @keyword excludeuser: Exclude revisions by this user
        @keyword tag: Only list revision tagged with this tag
        @keyword prop: Which properties to get. Defaults are ids, user,
            comment, flags and timestamp
        """
        def handle_props(props):
            """Translate deletedrev props to deletedrevisions props."""
            if isinstance(props, str):
                props = props.split('|')
            if self.mw_version >= '1.25':
                return props

            old_props = []
            for item in props:
                if item == 'ids':
                    old_props += ['revid', 'parentid']
                elif item == 'flags':
                    old_props.append('minor')
                elif item != 'timestamp':
                    old_props.append(item)
                    if item == 'content' and self.mw_version < '1.24':
                        old_props.append('token')
            return old_props

        # set default properties
        prop = kwargs.pop('prop',
                          ['ids', 'user', 'comment', 'flags', 'timestamp'])
        if content:
            prop.append('content')

        if start and end:
            self.assert_valid_iter_params('deletedrevs', start, end, reverse)

        self._check_view_deleted('deletedrevs', prop)

        revids = kwargs.pop('revids', None)
        if not (bool(titles) ^ (revids is not None)):
            raise Error('deletedrevs: either "titles" or "revids" parameter '
                        'must be given.')
        if revids and self.mw_version < '1.25':
            raise NotImplementedError(
                'deletedrevs: "revid" is not implemented with MediaWiki {}'
                .format(self.mw_version))

        if self.mw_version >= '1.25':
            pre = 'drv'
            type_arg = 'deletedrevisions'
            generator = api.PropertyGenerator
        else:
            pre = 'dr'
            type_arg = 'deletedrevs'
            generator = api.ListGenerator

        gen = self._generator(generator, type_arg=type_arg,
                              titles=titles, revids=revids,
                              total=total)

        gen.request[pre + 'start'] = start
        gen.request[pre + 'end'] = end
        gen.request[pre + 'prop'] = handle_props(prop)

        # handle other parameters like user
        for k, v in kwargs.items():
            gen.request[pre + k] = v

        if reverse:
            gen.request[pre + 'dir'] = 'newer'

        if self.mw_version < '1.25':
            yield from gen

        else:
            # The dict result is different for both generators
            for data in gen:
                with suppress(KeyError):
                    data['revisions'] = data.pop('deletedrevisions')
                    yield data

    @need_version('1.25')
    def alldeletedrevisions(
        self,
        *,
        namespaces=None,
        reverse: bool = False,
        content: bool = False,
        total: Optional[int] = None,
        **kwargs
    ) -> typing.Iterable[Dict[str, Any]]:
        """
        Iterate all deleted revisions.

        @see: U{https://www.mediawiki.org/wiki/API:Alldeletedrevisions}

        @param namespaces: Only iterate pages in these namespaces
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param reverse: Iterate oldest revisions first (default: newest)
        @param content: If True, retrieve the content of each revision
        @param total: Number of revisions to retrieve
        @keyword from: Start listing at this title
        @keyword to: Stop listing at this title
        @keyword prefix: Search for all page titles that begin with this value
        @keyword excludeuser: Exclude revisions by this user
        @keyword tag: Only list revisions tagged with this tag
        @keyword user: List revisions by this user
        @keyword start: Iterate revisions starting at this Timestamp
        @keyword end: Iterate revisions ending at this Timestamp
        @keyword prop: Which properties to get. Defaults are ids, timestamp,
            flags, user, and comment (if you have the right to view).
        @type prop: List[str]
        """
        if 'start' in kwargs and 'end' in kwargs:
            self.assert_valid_iter_params('alldeletedrevisions',
                                          kwargs['start'],
                                          kwargs['end'],
                                          reverse)
        prop = kwargs.pop('prop', [])
        parameters = {'adr' + k: v for k, v in kwargs.items()}
        if not prop:
            prop = ['ids', 'timestamp', 'flags', 'user']
            if self.has_right('deletedhistory'):
                prop.append('comment')
        if content:
            prop.append('content')
        self._check_view_deleted('alldeletedrevisions', prop)
        parameters['adrprop'] = prop
        if reverse:
            parameters['adrdir'] = 'newer'
        yield from self._generator(api.ListGenerator,
                                   type_arg='alldeletedrevisions',
                                   namespaces=namespaces,
                                   total=total,
                                   parameters=parameters)

    def users(self, usernames):
        """Iterate info about a list of users by name or IP.

        @see: U{https://www.mediawiki.org/wiki/API:Users}

        @param usernames: a list of user names
        @type usernames: list, or other iterable, of str
        """
        usprop = ['blockinfo', 'gender', 'groups', 'editcount', 'registration',
                  'rights', 'emailable']
        usgen = api.ListGenerator(
            'users', site=self, parameters={
                'ususers': usernames, 'usprop': usprop})
        return usgen

    @deprecated_args(step=None)
    def randompages(self, total=None, namespaces=None,
                    redirects=False, content=False):
        """Iterate a number of random pages.

        @see: U{https://www.mediawiki.org/wiki/API:Random}

        Pages are listed in a fixed sequence, only the starting point is
        random.

        @param total: the maximum number of pages to iterate
        @param namespaces: only iterate pages in these namespaces.
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param redirects: if True, include only redirect pages in results,
            False does not include redirects and None (MW 1.26+) include both
            types. (default: False)
        @type redirects: bool or None
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        @raises AssertError: unsupported redirects parameter
        """
        mapping = {False: None, True: 'redirects', None: 'all'}
        assert redirects in mapping
        redirects = mapping[redirects]
        params = {}
        if redirects is not None:
            if self.mw_version < '1.26':
                if redirects == 'all':
                    warn("parameter redirects=None to retrieve 'all' random"
                         'page types is not supported by mw version {0}. '
                         'Using default.'.format(self.mw_version),
                         UserWarning)
                params['grnredirect'] = redirects == 'redirects'
            else:
                params['grnfilterredir'] = redirects
        return self._generator(api.PageGenerator, type_arg='random',
                               namespaces=namespaces, total=total,
                               g_content=content, **params)

    # Catalog of editpage error codes, for use in generating messages.
    # The block at the bottom are page related errors.
    _ep_errors = {
        'noapiwrite': 'API editing not enabled on %(site)s wiki',
        'writeapidenied':
            'User %(user)s is not authorized to edit on %(site)s wiki',
        'cantcreate':
            'User %(user)s not authorized to create new pages on %(site)s '
            'wiki',
        'cantcreate-anon':
            'Bot is not logged in, and anon users are not authorized to '
            'create new pages on %(site)s wiki',
        'noimageredirect-anon':
            'Bot is not logged in, and anon users are not authorized to '
            'create image redirects on %(site)s wiki',
        'noimageredirect': 'User %(user)s not authorized to create image '
                           'redirects on %(site)s wiki',
        'filtered': '%(info)s',
        'contenttoobig': '%(info)s',
        'noedit-anon': 'Bot is not logged in, and anon users are not '
                       'authorized to edit on %(site)s wiki',
        'noedit':
            'User %(user)s not authorized to edit pages on %(site)s wiki',
        'missingtitle': NoCreateError,
        'editconflict': EditConflict,
        'articleexists': PageCreatedConflict,
        'pagedeleted': PageDeletedConflict,
        'protectedpage': LockedPage,
        'protectedtitle': LockedNoPage,
        'cascadeprotected': CascadeLockedPage,
        'titleblacklist-forbidden': TitleblacklistError,
        'spamblacklist': SpamblacklistError,
    }
    _ep_text_overrides = {'appendtext', 'prependtext', 'undo'}

    @need_right('edit')
    def editpage(self, page, summary=None, minor=True, notminor=False,
                 bot=True, recreate=True, createonly=False, nocreate=False,
                 watch=None, **kwargs) -> bool:
        """Submit an edit to be saved to the wiki.

        @see: U{https://www.mediawiki.org/wiki/API:Edit}

        @param page: The Page to be saved.
            By default its .text property will be used
            as the new text to be saved to the wiki
        @param summary: the edit summary
        @param minor: if True (default), mark edit as minor
        @param notminor: if True, override account preferences to mark edit
            as non-minor
        @param recreate: if True (default), create new page even if this
            title has previously been deleted
        @param createonly: if True, raise an error if this title already
            exists on the wiki
        @param nocreate: if True, raise an error if the page does not exist
        @param watch: Specify how the watchlist is affected by this edit, set
            to one of "watch", "unwatch", "preferences", "nochange":
            * watch: add the page to the watchlist
            * unwatch: remove the page from the watchlist
            * preferences: use the preference settings (default)
            * nochange: don't change the watchlist
        @param bot: if True, mark edit with bot flag
        @kwarg text: Overrides Page.text
        @type text: str
        @kwarg section: Edit an existing numbered section or
            a new section ('new')
        @type section: int or str
        @kwarg prependtext: Prepend text. Overrides Page.text
        @type text: str
        @kwarg appendtext: Append text. Overrides Page.text.
        @type text: str
        @kwarg undo: Revision id to undo. Overrides Page.text
        @type undo: int
        @return: True if edit succeeded, False if it failed
        @raises pywikibot.exceptions.Error: No text to be saved
        @raises pywikibot.exceptions.NoPage: recreate is disabled and page does
            not exist
        @raises pywikibot.exceptions.CaptchaError: config.solve_captcha is
            False and saving the page requires solving a captcha
        """
        basetimestamp = True
        text_overrides = self._ep_text_overrides.intersection(kwargs.keys())

        if text_overrides:
            if 'text' in kwargs:
                raise ValueError('text cannot be used with any of {}'
                                 .format(', '.join(text_overrides)))
            if len(text_overrides) > 1:
                raise ValueError('Multiple text overrides used: {}'
                                 .format(', '.join(text_overrides)))
            text = None
            basetimestamp = False
        elif 'text' in kwargs:
            text = kwargs.pop('text')
            if 'section' in kwargs and kwargs['section'] == 'new':
                basetimestamp = False
        elif 'section' in kwargs:
            raise ValueError('text must be used with section')
        else:
            text = page.text
            if text is None:
                raise Error('editpage: no text to be saved')

        if basetimestamp or not recreate:
            try:
                lastrev = page.latest_revision
                basetimestamp = lastrev.timestamp
            except NoPage:
                basetimestamp = False
                if not recreate:
                    raise

        token = self.tokens['edit']
        if bot is None:
            bot = self.has_right('bot')
        params = dict(action='edit', title=page,
                      text=text, token=token, summary=summary, bot=bot,
                      recreate=recreate, createonly=createonly,
                      nocreate=nocreate, minor=minor,
                      notminor=not minor and notminor,
                      **kwargs)

        if basetimestamp and 'basetimestamp' not in kwargs:
            params['basetimestamp'] = basetimestamp

        watch_items = {'watch', 'unwatch', 'preferences', 'nochange'}
        if watch in watch_items:
            params['watchlist'] = watch
        elif watch:
            pywikibot.warning(
                "editpage: Invalid watch value '%(watch)s' ignored."
                % {'watch': watch})
        req = self._simple_request(**params)

        self.lock_page(page)
        try:
            while True:
                try:
                    result = req.submit()
                    pywikibot.debug('editpage response: %s' % result,
                                    _logger)
                except api.APIError as err:
                    if err.code.endswith('anon') and self.logged_in():
                        pywikibot.debug(
                            "editpage: received '%s' even though bot is "
                            'logged in' % err.code,
                            _logger)
                    if err.code in self._ep_errors:
                        exception = self._ep_errors[err.code]
                        if isinstance(exception, str):
                            errdata = {
                                'site': self,
                                'title': page.title(with_section=False),
                                'user': self.user(),
                                'info': err.info
                            }
                            raise Error(exception % errdata)
                        elif issubclass(exception, SpamblacklistError):
                            urls = ', '.join(err.other[err.code]['matches'])
                            raise exception(page, url=urls) from None
                        else:
                            raise exception(page)
                    pywikibot.debug(
                        "editpage: Unexpected error code '%s' received."
                        % err.code,
                        _logger)
                    raise
                assert 'edit' in result and 'result' in result['edit'], result

                if result['edit']['result'] == 'Success':
                    if 'nochange' in result['edit']:
                        # null edit, page not changed
                        pywikibot.log('Page [[%s]] saved without any changes.'
                                      % page.title())
                        return True
                    page.latest_revision_id = result['edit']['newrevid']
                    # See:
                    # https://www.mediawiki.org/wiki/API:Wikimania_2006_API_discussion#Notes
                    # not safe to assume that saved text is the same as sent
                    del page.text
                    return True

                if result['edit']['result'] == 'Failure':
                    if 'captcha' in result['edit']:
                        if not pywikibot.config.solve_captcha:
                            raise CaptchaError('captcha encountered while '
                                               'config.solve_captcha is False')
                        captcha = result['edit']['captcha']
                        req['captchaid'] = captcha['id']

                        if captcha['type'] in ['math', 'simple']:
                            req['captchaword'] = input(captcha['question'])
                            continue

                        if 'url' in captcha:
                            import webbrowser
                            webbrowser.open('%s://%s%s'
                                            % (self.protocol(),
                                               self.hostname(),
                                               captcha['url']))
                            req['captchaword'] = pywikibot.input(
                                'Please view CAPTCHA in your browser, '
                                'then type answer here:')
                            continue

                        pywikibot.error(
                            'editpage: unknown CAPTCHA response %s, '
                            'page not saved'
                            % captcha)
                        return False

                    if 'spamblacklist' in result['edit']:
                        raise SpamblacklistError(
                            page, result['edit']['spamblacklist'])

                    if 'code' in result['edit'] and 'info' in result['edit']:
                        pywikibot.error(
                            'editpage: %s\n%s, '
                            % (result['edit']['code'], result['edit']['info']))
                        return False

                    pywikibot.error('editpage: unknown failure reason %s'
                                    % str(result))
                    return False

                pywikibot.error(
                    "editpage: Unknown result code '%s' received; "
                    'page not saved' % result['edit']['result'])
                pywikibot.log(str(result))
                return False

        finally:
            self.unlock_page(page)

    OnErrorExc = namedtuple('OnErrorExc', 'exception on_new_page')

    # catalog of merge history errors for use in error messages
    _mh_errors = {
        'noapiwrite': 'API editing not enabled on {site} wiki',
        'writeapidenied':
            'User {user} is not authorized to edit on {site} wiki',
        'mergehistory-fail-invalid-source': 'Source {source} is invalid '
            '(this may be caused by an invalid page ID in the database)',
        'mergehistory-fail-invalid-dest': 'Destination {dest} is invalid '
            '(this may be caused by an invalid page ID in the database)',
        'mergehistory-fail-no-change':
            'History merge did not merge any revisions; '
            'please recheck the page and timestamp parameters',
        'mergehistory-fail-permission':
            'User {user} has insufficient permissions to merge history',
        'mergehistory-fail-timestamps-overlap':
            'Source revisions from {source} overlap or come after '
            'destination revisions of {dest}'
    }

    @need_right('mergehistory')
    @need_version('1.27.0-wmf.13')
    def merge_history(self, source, dest, timestamp=None,
                      reason: Optional[str] = None):
        """Merge revisions from one page into another.

        @see: U{https://www.mediawiki.org/wiki/API:Mergehistory}

        Revisions dating up to the given timestamp in the source will be
        moved into the destination page history. History merge fails if
        the timestamps of source and dest revisions overlap (all source
        revisions must be dated before the earliest dest revision).

        @param source: Source page from which revisions will be merged
        @type source: pywikibot.Page
        @param dest: Destination page to which revisions will be merged
        @type dest: pywikibot.Page
        @param timestamp: Revisions from this page dating up to this timestamp
            will be merged into the destination page (if not given or False,
            all revisions will be merged)
        @type timestamp: pywikibot.Timestamp
        @param reason: Optional reason for the history merge
        """
        # Data for error messages
        errdata = {
            'site': self,
            'source': source,
            'dest': dest,
            'user': self.user(),
        }

        # Check if pages exist before continuing
        if not source.exists():
            raise NoPage(source,
                         'Cannot merge revisions from source {source} because '
                         'it does not exist on {site}'
                         .format_map(errdata))
        if not dest.exists():
            raise NoPage(dest,
                         'Cannot merge revisions to destination {dest} '
                         'because it does not exist on {site}'
                         .format_map(errdata))

        if source == dest:  # Same pages
            raise PageSaveRelatedError(
                'Cannot merge revisions of {source} to itself'
                .format_map(errdata))

        # Send the merge API request
        token = self.tokens['csrf']
        req = self._simple_request(action='mergehistory',
                                   token=token)
        req['from'] = source
        req['to'] = dest
        if reason:
            req['reason'] = reason
        if timestamp:
            req['timestamp'] = timestamp

        self.lock_page(source)
        self.lock_page(dest)
        try:
            result = req.submit()
            pywikibot.debug('mergehistory response: {result}'
                            .format(result=result),
                            _logger)
        except api.APIError as err:
            if err.code in self._mh_errors:
                on_error = self._mh_errors[err.code]
                raise Error(on_error.format_map(errdata))
            else:
                pywikibot.debug(
                    "mergehistory: Unexpected error code '{code}' received"
                    .format(code=err.code),
                    _logger
                )
                raise
        finally:
            self.unlock_page(source)
            self.unlock_page(dest)

        if 'mergehistory' not in result:
            pywikibot.error('mergehistory: {error}'.format(error=result))
            raise Error('mergehistory: unexpected response')

    # catalog of move errors for use in error messages
    _mv_errors = {
        'noapiwrite': 'API editing not enabled on %(site)s wiki',
        'writeapidenied':
            'User %(user)s is not authorized to edit on %(site)s wiki',
        'nosuppress':
            'User %(user)s is not authorized to move pages without '
            'creating redirects',
        'cantmove-anon':
            'Bot is not logged in, and anon users are not authorized to '
            'move pages on %(site)s wiki',
        'cantmove':
            'User %(user)s is not authorized to move pages on %(site)s wiki',
        'immobilenamespace':
            'Pages in %(oldnamespace)s namespace cannot be moved on %(site)s '
            'wiki',
        'articleexists': OnErrorExc(exception=ArticleExistsConflict,
                                    on_new_page=True),
        # "protectedpage" can happen in both directions.
        'protectedpage': OnErrorExc(exception=LockedPage, on_new_page=None),
        'protectedtitle': OnErrorExc(exception=LockedNoPage, on_new_page=True),
        'nonfilenamespace':
            'Cannot move a file to %(newnamespace)s namespace on %(site)s '
            'wiki',
        'filetypemismatch':
            '[[%(newtitle)s]] file extension does not match content of '
            '[[%(oldtitle)s]]',
    }

    @need_right('move')
    def movepage(self, page, newtitle: str, summary, movetalk=True,
                 noredirect=False):
        """Move a Page to a new title.

        @see: U{https://www.mediawiki.org/wiki/API:Move}

        @param page: the Page to be moved (must exist)
        @param newtitle: the new title for the Page
        @param summary: edit summary (required!)
        @param movetalk: if True (default), also move the talk page if possible
        @param noredirect: if True, suppress creation of a redirect from the
            old title to the new one
        @return: Page object with the new title
        @rtype: pywikibot.Page
        """
        oldtitle = page.title(with_section=False)
        newlink = pywikibot.Link(newtitle, self)
        newpage = pywikibot.Page(newlink)
        if newlink.namespace:
            newtitle = self.namespace(newlink.namespace) + ':' + newlink.title
        else:
            newtitle = newlink.title
        if oldtitle == newtitle:
            raise Error('Cannot move page %s to its own title.'
                        % oldtitle)
        if not page.exists():
            raise NoPage(page,
                         'Cannot move page %(page)s because it '
                         'does not exist on %(site)s.')
        token = self.tokens['move']
        self.lock_page(page)
        req = self._simple_request(action='move',
                                   noredirect=noredirect,
                                   reason=summary,
                                   movetalk=movetalk,
                                   token=token,
                                   to=newtitle)
        req['from'] = oldtitle  # "from" is a python keyword
        try:
            result = req.submit()
            pywikibot.debug('movepage response: %s' % result,
                            _logger)
        except api.APIError as err:
            if err.code.endswith('anon') and self.logged_in():
                pywikibot.debug(
                    "movepage: received '%s' even though bot is logged in"
                    % err.code,
                    _logger)
            if err.code in self._mv_errors:
                on_error = self._mv_errors[err.code]
                if hasattr(on_error, 'exception'):
                    # LockedPage can be raised both if "from" or "to" page
                    # are locked for the user.
                    # Both pages locked is not considered
                    # (a double failure has low probability)
                    if issubclass(on_error.exception, LockedPage):
                        # we assume "from" is locked unless proven otherwise
                        failed_page = page
                        if newpage.exists():
                            for prot in self.page_restrictions(
                                    newpage).values():
                                if not self.has_group(prot[0]):
                                    failed_page = newpage
                                    break
                    else:
                        failed_page = newpage if on_error.on_new_page else page
                    raise on_error.exception(failed_page)
                else:
                    errdata = {
                        'site': self,
                        'oldtitle': oldtitle,
                        'oldnamespace': self.namespace(page.namespace()),
                        'newtitle': newtitle,
                        'newnamespace': self.namespace(newlink.namespace),
                        'user': self.user(),
                    }
                    raise Error(on_error % errdata)
            pywikibot.debug("movepage: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        finally:
            self.unlock_page(page)
        if 'move' not in result:
            pywikibot.error('movepage: %s' % result)
            raise Error('movepage: unexpected response')
        # TODO: Check for talkmove-error messages
        if 'talkmove-error-code' in result['move']:
            pywikibot.warning(
                'movepage: Talk page %s not moved'
                % (page.toggleTalkPage().title(as_link=True)))
        return pywikibot.Page(page, newtitle)

    # catalog of rollback errors for use in error messages
    _rb_errors = {
        'noapiwrite': 'API editing not enabled on %(site)s wiki',
        'writeapidenied': 'User %(user)s not allowed to edit through the API',
        'alreadyrolled':
            'Page [[%(title)s]] already rolled back; action aborted.',
    }  # other errors shouldn't arise because we check for those errors

    @need_right('rollback')
    def rollbackpage(self, page, **kwargs):
        """Roll back page to version before last user's edits.

        @see: U{https://www.mediawiki.org/wiki/API:Rollback}

        The keyword arguments are those supported by the rollback API.

        As a precaution against errors, this method will fail unless
        the page history contains at least two revisions, and at least
        one that is not by the same user who made the last edit.

        @param page: the Page to be rolled back (must exist)
        @keyword user: the last user to be rollbacked;
            default is page.latest_revision.user
        """
        if len(page._revisions) < 2:
            raise Error(
                'Rollback of {} aborted; load revision history first.'
                .format(page))

        user = kwargs.pop('user', page.latest_revision.user)
        for rev in sorted(page._revisions.values(), reverse=True,
                          key=lambda r: r.timestamp):
            # start with most recent revision first
            if rev.user != user:
                break
        else:
            raise Error(
                'Rollback of {} aborted; only one user in revision history.'
                .format(page))

        parameters = merge_unique_dicts(kwargs,
                                        action='rollback',
                                        title=page,
                                        token=self.tokens['rollback'],
                                        user=user)
        self.lock_page(page)
        req = self._simple_request(**parameters)
        try:
            req.submit()
        except api.APIError as err:
            errdata = {
                'site': self,
                'title': page.title(with_section=False),
                'user': self.user(),
            }
            if err.code in self._rb_errors:
                raise Error(self._rb_errors[err.code] % errdata)
            pywikibot.debug("rollback: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        finally:
            self.unlock_page(page)

    # catalog of delete errors for use in error messages
    _dl_errors = {
        'noapiwrite': 'API editing not enabled on %(site)s wiki',
        'writeapidenied': 'User %(user)s not allowed to edit through the API',
        'permissiondenied': 'User %(user)s not authorized to (un)delete '
                            'pages on %(site)s wiki.',
        'cantdelete':
            'Could not delete [[%(title)s]]. Maybe it was deleted already.',
        'cantundelete': 'Could not undelete [[%(title)s]]. '
                        'Revision may not exist or was already undeleted.'
    }  # other errors shouldn't occur because of pre-submission checks

    @need_right('delete')
    @deprecate_arg('summary', 'reason')
    def deletepage(self, page, reason: str):
        """Delete page from the wiki. Requires appropriate privilege level.

        @see: U{https://www.mediawiki.org/wiki/API:Delete}
        Page to be deleted can be given either as Page object or as pageid.

        @param page: Page to be deleted or its pageid.
        @type page: Page or, in case of pageid, int or str
        @param reason: Deletion reason.
        @raises TypeError, ValueError: page has wrong type/value.

        """
        token = self.tokens['delete']
        params = {'action': 'delete', 'token': token, 'reason': reason}

        if isinstance(page, pywikibot.Page):
            params['title'] = page
            msg = page.title(withSection=False)
        else:
            pageid = int(page)
            params['pageid'] = pageid
            msg = pageid

        req = self._simple_request(**params)
        self.lock_page(page)
        try:
            req.submit()
        except api.APIError as err:
            errdata = {
                'site': self,
                'title': msg,
                'user': self.user(),
            }
            if err.code in self._dl_errors:
                raise Error(self._dl_errors[err.code] % errdata)
            pywikibot.debug("delete: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        else:
            page.clear_cache()
        finally:
            self.unlock_page(page)

    @need_right('undelete')
    @deprecate_arg('summary', 'reason')
    def undelete_page(self, page, reason: str, revisions=None):
        """Undelete page from the wiki. Requires appropriate privilege level.

        @see: U{https://www.mediawiki.org/wiki/API:Undelete}

        @param page: Page to be deleted.
        @type page: pywikibot.BasePage
        @param revisions: List of timestamps to restore.
            If None, restores all revisions.
        @type revisions: list
        @param reason: Undeletion reason.

        """
        token = self.tokens['delete']
        self.lock_page(page)

        req = self._simple_request(action='undelete',
                                   title=page,
                                   reason=reason,
                                   token=token,
                                   timestamps=revisions)
        try:
            req.submit()
        except api.APIError as err:
            errdata = {
                'site': self,
                'title': page.title(with_section=False),
                'user': self.user(),
            }
            if err.code in self._dl_errors:
                raise Error(self._dl_errors[err.code] % errdata)
            pywikibot.debug("delete: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        finally:
            self.unlock_page(page)

    _protect_errors = {
        'noapiwrite': 'API editing not enabled on %(site)s wiki',
        'writeapidenied': 'User %(user)s not allowed to edit through the API',
        'permissiondenied':
            'User %(user)s not authorized to protect pages on %(site)s wiki.',
        'cantedit':
            "User %(user)s can't protect this page because user %(user)s "
            "can't edit it.",
        'protect-invalidlevel': 'Invalid protection level'
    }

    def protection_types(self):
        """
        Return the protection types available on this site.

        @return: protection types available
        @rtype: set of str instances
        @see: L{Siteinfo._get_default()}
        """
        return set(self.siteinfo.get('restrictions')['types'])

    def protection_levels(self):
        """
        Return the protection levels available on this site.

        @return: protection types available
        @rtype: set of str instances
        @see: L{Siteinfo._get_default()}
        """
        # implemented in b73b5883d486db0e9278ef16733551f28d9e096d
        return set(self.siteinfo.get('restrictions')['levels'])

    @need_right('protect')
    @deprecate_arg('summary', 'reason')
    def protect(self, page, protections: dict,
                reason: str, expiry=None, **kwargs):
        """(Un)protect a wiki page. Requires administrator status.

        @see: U{https://www.mediawiki.org/wiki/API:Protect}

        @param protections: A dict mapping type of protection to protection
            level of that type. Valid restriction types are 'edit', 'create',
            'move' and 'upload'. Valid restriction levels are '' (equivalent
            to 'none' or 'all'), 'autoconfirmed', and 'sysop'.
            If None is given, however, that protection will be skipped.
        @param reason: Reason for the action
        @param expiry: When the block should expire. This expiry will be
            applied to all protections. If None, 'infinite', 'indefinite',
            'never', or '' is given, there is no expiry.
        @type expiry: pywikibot.Timestamp, string in GNU timestamp format
            (including ISO 8601).
        """
        token = self.tokens['protect']
        self.lock_page(page)

        protections = [ptype + '=' + level
                       for ptype, level in protections.items()
                       if level is not None]
        parameters = merge_unique_dicts(kwargs, action='protect', title=page,
                                        token=token,
                                        protections=protections, reason=reason,
                                        expiry=expiry)

        req = self._simple_request(**parameters)
        try:
            result = req.submit()
        except api.APIError as err:
            errdata = {
                'site': self,
                'user': self.user(),
            }
            if err.code in self._protect_errors:
                raise Error(self._protect_errors[err.code] % errdata)
            pywikibot.debug("protect: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        else:
            protection = {}
            for d in result['protect']['protections']:
                expiry = d.pop('expiry')
                ptype, level = d.popitem()
                if level:
                    protection[ptype] = (level, expiry)
            page._protection = protection
        finally:
            self.unlock_page(page)

    # TODO: implement undelete

    _patrol_errors = {
        'nosuchrcid': 'There is no change with rcid %(rcid)s',
        'nosuchrevid': 'There is no change with revid %(revid)s',
        'patroldisabled': 'Patrolling is disabled on %(site)s wiki',
        'noautopatrol': 'User %(user)s has no permission to patrol its own '
                        'changes, "autopatrol" is needed',
        'notpatrollable':
            "The revision %(revid)s can't be patrolled as it's too old."
    }

    @need_right('patrol')
    @deprecated_args(token=None)
    def patrol(self, rcid=None, revid=None, revision=None):
        """Return a generator of patrolled pages.

        @see: U{https://www.mediawiki.org/wiki/API:Patrol}

        Pages to be patrolled are identified by rcid, revid or revision.
        At least one of the parameters is mandatory.
        See https://www.mediawiki.org/wiki/API:Patrol.

        @param rcid: an int/string/iterable/iterator providing rcid of pages
            to be patrolled.
        @type rcid: iterable/iterator which returns a number or string which
             contains only digits; it also supports a string (as above) or int
        @param revid: an int/string/iterable/iterator providing revid of pages
            to be patrolled.
        @type revid: iterable/iterator which returns a number or string which
             contains only digits; it also supports a string (as above) or int.
        @param revision: an Revision/iterable/iterator providing Revision
            object of pages to be patrolled.
        @type revision: iterable/iterator which returns a Revision object; it
            also supports a single Revision.
        @rtype: iterator of dict with 'rcid', 'ns' and 'title'
            of the patrolled page.

        """
        # If patrol is not enabled, attr will be set the first time a
        # request is done.
        if hasattr(self, '_patroldisabled'):
            if self._patroldisabled:
                return

        if all(_ is None for _ in [rcid, revid, revision]):
            raise Error('No rcid, revid or revision provided.')

        if isinstance(rcid, (int, str)):
            rcid = {rcid}
        if isinstance(revid, (int, str)):
            revid = {revid}
        if isinstance(revision, pywikibot.page.Revision):
            revision = {revision}

        # Handle param=None.
        rcid = rcid or set()
        revid = revid or set()
        revision = revision or set()

        # TODO: remove exception for mw < 1.22
        if (revid or revision) and self.mw_version < '1.22':
            raise NotImplementedError(
                'Support of "revid" parameter\n'
                'is not implemented in MediaWiki version < "1.22"')
        else:
            combined_revid = set(revid) | {r.revid for r in revision}

        gen = itertools.chain(
            zip_longest(rcid, [], fillvalue='rcid'),
            zip_longest(combined_revid, [], fillvalue='revid'))

        token = self.tokens['patrol']

        for idvalue, idtype in gen:
            req = self._request(parameters={'action': 'patrol',
                                            'token': token,
                                            idtype: idvalue})

            try:
                result = req.submit()
            except api.APIError as err:
                # patrol is disabled, store in attr to avoid other requests
                if err.code == 'patroldisabled':
                    self._patroldisabled = True
                    return

                errdata = {
                    'site': self,
                    'user': self.user(),
                }
                errdata[idtype] = idvalue
                if err.code in self._patrol_errors:
                    raise Error(self._patrol_errors[err.code] % errdata)
                pywikibot.debug("protect: Unexpected error code '%s' received."
                                % err.code,
                                _logger)
                raise

            yield result['patrol']

    @need_right('block')
    def blockuser(self, user, expiry, reason: str, anononly=True,
                  nocreate=True, autoblock=True, noemail=False,
                  reblock=False, allowusertalk=False):
        """
        Block a user for certain amount of time and for a certain reason.

        @see: U{https://www.mediawiki.org/wiki/API:Block}

        @param user: The username/IP to be blocked without a namespace.
        @type user: L{pywikibot.User}
        @param expiry: The length or date/time when the block expires. If
            'never', 'infinite', 'indefinite' it never does. If the value is
            given as a str it's parsed by php's strtotime function:

                U{http://php.net/manual/en/function.strtotime.php}

            The relative format is described there:

                U{http://php.net/manual/en/datetime.formats.relative.php}

            It is recommended to not use a str if possible to be
            independent of the API.
        @type expiry: Timestamp/datetime (absolute),
            str (relative/absolute) or False ('never')
        @param reason: The reason for the block.
        @param anononly: Disable anonymous edits for this IP.
        @type anononly: boolean
        @param nocreate: Prevent account creation.
        @type nocreate: boolean
        @param autoblock: Automatically block the last used IP address and all
            subsequent IP addresses from which this account logs in.
        @type autoblock: boolean
        @param noemail: Prevent user from sending email through the wiki.
        @type noemail: boolean
        @param reblock: If the user is already blocked, overwrite the existing
            block.
        @type reblock: boolean
        @param allowusertalk: Whether the user can edit their talk page while
            blocked.
        @type allowusertalk: boolean
        @return: The data retrieved from the API request.
        @rtype: dict
        """
        token = self.tokens['block']
        if expiry is False:
            expiry = 'never'
        req = self._simple_request(action='block', user=user.username,
                                   expiry=expiry, reason=reason, token=token,
                                   anononly=anononly, nocreate=nocreate,
                                   autoblock=autoblock, noemail=noemail,
                                   reblock=reblock,
                                   allowusertalk=allowusertalk)

        data = req.submit()
        return data

    @need_right('unblock')
    def unblockuser(self, user, reason: Optional[str] = None):
        """
        Remove the block for the user.

        @see: U{https://www.mediawiki.org/wiki/API:Block}

        @param user: The username/IP without a namespace.
        @type user: L{pywikibot.User}
        @param reason: Reason for the unblock.
        """
        req = self._simple_request(action='unblock',
                                   user=user.username,
                                   token=self.tokens['block'],
                                   reason=reason)

        data = req.submit()
        return data

    @need_right('editmywatchlist')
    def watch(self, pages, unwatch=False) -> bool:
        """Add or remove pages from watchlist.

        @see: U{https://www.mediawiki.org/wiki/API:Watch}

        @param pages: A single page or a sequence of pages.
        @type pages: A page object, a page-title string, or sequence of them.
            Also accepts a single pipe-separated string like 'title1|title2'.
        @param unwatch: If True, remove pages from watchlist;
            if False add them (default).
        @return: True if API returned expected response; False otherwise
        @raises KeyError: 'watch' isn't in API response

        """
        parameters = {'action': 'watch',
                      'token': self.tokens['watch'],
                      'unwatch': unwatch}
        unwatch = 'unwatched' if unwatch else 'watched'
        if self.mw_version >= '1.23':
            parameters['titles'] = pages
            req = self._simple_request(**parameters)
            results = req.submit()
            return all(unwatch in r for r in results['watch'])

        # MW version < 1.23
        if isinstance(pages, str):
            if '|' in pages:
                pages = pages.split('|')
            else:
                pages = (pages,)

        for page in pages:
            parameters['title'] = page
            req = self._simple_request(**parameters)
            result = req.submit()
            if unwatch not in result['watch']:
                return False
        return True

    @need_right('editmywatchlist')
    @deprecated('Site().watch', since='20160102', future_warning=True)
    def watchpage(self, page, unwatch=False) -> bool:
        """
        Add or remove page from watchlist.

        DEPRECATED: Use Site().watch() instead.

        @param page: A single page.
        @type page: A page object, a page-title string.
        @param unwatch: If True, remove page from watchlist;
            if False (default), add it.
        @return: True if API returned expected response; False otherwise

        """
        try:
            result = self.watch(page, unwatch)
        except KeyError:
            pywikibot.error('watchpage: Unexpected API response')
            result = False
        return result

    @need_right('purge')
    def purgepages(self, pages, forcelinkupdate: bool = False,
                   forcerecursivelinkupdate: bool = False,
                   converttitles: bool = False, redirects: bool = False
                   ) -> bool:
        """
        Purge the server's cache for one or multiple pages.

        @param pages: list of Page objects
        @param redirects: Automatically resolve redirects.
        @type redirects: bool
        @param converttitles: Convert titles to other variants if necessary.
            Only works if the wiki's content language supports variant
            conversion.
        @param forcelinkupdate: Update the links tables.
        @param forcerecursivelinkupdate: Update the links table, and update the
            links tables for any page that uses this page as a template.
        @return: True if API returned expected response; False otherwise
        """
        req = self._simple_request(action='purge', titles=list(set(pages)))
        if converttitles:
            req['converttitles'] = True
        if redirects:
            req['redirects'] = True
        if forcelinkupdate:
            req['forcelinkupdate'] = True
        if forcerecursivelinkupdate:
            req['forcerecursivelinkupdate'] = True
        result = req.submit()
        try:
            result = result['purge']
        except KeyError:
            pywikibot.error(
                'purgepages: Unexpected API response:\n%s' % result)
            return False
        if not all('purged' in page for page in result):
            return False
        if forcelinkupdate or forcerecursivelinkupdate:
            return all('linkupdate' in page for page in result)
        return True

    @need_right('edit')
    def is_uploaddisabled(self):
        """Return True if upload is disabled on site.

        When the version is at least 1.27wmf9, uses general siteinfo.
        If not called directly, it is cached by the first attempted
        upload action.

        """
        if self.mw_version >= '1.27wmf9':
            return not self._siteinfo.get('general')['uploadsenabled']

        if hasattr(self, '_uploaddisabled'):
            return self._uploaddisabled

        # attempt a fake upload; on enabled sites will fail for:
        # missingparam: One of the parameters
        #    filekey, file, url, statuskey is required
        # TODO: is there another way?
        try:
            req = self._request(throttle=False,
                                parameters={'action': 'upload',
                                            'token': self.tokens['edit']})
            req.submit()
        except api.APIError as error:
            if error.code == 'uploaddisabled':
                self._uploaddisabled = True
            elif error.code == 'missingparam':
                # If the upload module is enabled, the above dummy request
                # does not have sufficient parameters and will cause a
                # 'missingparam' error.
                self._uploaddisabled = False
            else:
                # Unexpected error
                raise
            return self._uploaddisabled
        raise RuntimeError(
            'Unexpected success of upload action without parameters.')

    def stash_info(self, file_key, props=None):
        """Get the stash info for a given file key.

        @see: U{https://www.mediawiki.org/wiki/API:Stashimageinfo}
        """
        props = props or False
        req = self._simple_request(
            action='query', prop='stashimageinfo', siifilekey=file_key,
            siiprop=props)
        return req.submit()['query']['stashimageinfo'][0]

    @deprecate_arg('imagepage', 'filepage')
    @need_right('upload')
    def upload(self, filepage, source_filename=None, source_url=None,
               comment=None, text=None, watch=False, ignore_warnings=False,
               chunk_size: int = 0, _file_key: Optional[str] = None,
               _offset=0, _verify_stash=None, report_success=None):
        """
        Upload a file to the wiki.

        @see: U{https://www.mediawiki.org/wiki/API:Upload}

        Either source_filename or source_url, but not both, must be provided.

        @param filepage: a FilePage object from which the wiki-name of the
            file will be obtained.
        @param source_filename: path to the file to be uploaded
        @param source_url: URL of the file to be uploaded
        @param comment: Edit summary; if this is not provided, then
            filepage.text will be used. An empty summary is not permitted.
            This may also serve as the initial page text (see below).
        @param text: Initial page text; if this is not set, then
            filepage.text will be used, or comment.
        @param watch: If true, add filepage to the bot user's watchlist
        @param ignore_warnings: It may be a static boolean, a callable
            returning a boolean or an iterable. The callable gets a list of
            UploadWarning instances and the iterable should contain the warning
            codes for which an equivalent callable would return True if all
            UploadWarning codes are in thet list. If the result is False it'll
            not continue uploading the file and otherwise disable any warning
            and reattempt to upload the file. NOTE: If report_success is True
            or None it'll raise an UploadWarning exception if the static
            boolean is False.
        @type ignore_warnings: bool or callable or iterable of str
        @param chunk_size: The chunk size in bytesfor chunked uploading (see
            U{https://www.mediawiki.org/wiki/API:Upload#Chunked_uploading}). It
            will only upload in chunks, if the version number is 1.20 or higher
            and the chunk size is positive but lower than the file size.
        @param _file_key: Reuses an already uploaded file using the filekey. If
            None (default) it will upload the file.
        @param _offset: When file_key is not None this can be an integer to
            continue a previously canceled chunked upload. If False it treats
            that as a finished upload. If True it requests the stash info from
            the server to determine the offset. By default starts at 0.
        @type _offset: int or bool
        @param _verify_stash: Requests the SHA1 and file size uploaded and
            compares it to the local file. Also verifies that _offset is
            matching the file size if the _offset is an int. If _offset is
            False if verifies that the file size match with the local file. If
            None it'll verifies the stash when a file key and offset is given.
        @type _verify_stash: bool or None
        @param report_success: If the upload was successful it'll print a
            success message and if ignore_warnings is set to False it'll
            raise an UploadWarning if a warning occurred. If it's None
            (default) it'll be True if ignore_warnings is a bool and False
            otherwise. If it's True or None ignore_warnings must be a bool.
        @return: It returns True if the upload was successful and False
            otherwise.
        @rtype: bool
        """
        def create_warnings_list(response):
            return [
                api.UploadWarning(
                    warning,
                    upload_warnings.get(warning, '%(msg)s') % {'msg': data},
                    _file_key, response['offset'])
                for warning, data in response['warnings'].items()]

        upload_warnings = {
            # map API warning codes to user error messages
            # %(msg)s will be replaced by message string from API response
            'duplicate-archive':
                'The file is a duplicate of a deleted file %(msg)s.',
            'was-deleted': 'The file %(msg)s was previously deleted.',
            'emptyfile': 'File %(msg)s is empty.',
            'exists': 'File %(msg)s already exists.',
            'duplicate': 'Uploaded file is a duplicate of %(msg)s.',
            'badfilename': 'Target filename is invalid.',
            'filetype-unwanted-type': 'File %(msg)s type is unwanted type.',
            'exists-normalized': 'File exists with different extension as '
                                 '"%(msg)s".',
            'bad-prefix': 'Target filename has a bad prefix %(msg)s.',
            'page-exists':
                'Target filename exists but with a different file %(msg)s.',

            # API-returned message string will be timestamps, not much use here
            'nochange': 'The upload is an exact duplicate of the current '
                        'version of this file.',
            'duplicateversions': 'The upload is an exact duplicate of older '
                                 'version(s) of this file.',
        }

        # An offset != 0 doesn't make sense without a file key
        assert(_offset == 0 or _file_key is not None)
        # check for required parameters
        if bool(source_filename) == bool(source_url):
            raise ValueError('APISite.upload: must provide either '
                             'source_filename or source_url, not both.')
        if comment is None:
            comment = filepage.text
        if not comment:
            raise ValueError('APISite.upload: cannot upload file without '
                             'a summary/description.')
        if report_success is None:
            report_success = isinstance(ignore_warnings, bool)
        if report_success is True:
            if not isinstance(ignore_warnings, bool):
                raise ValueError('report_success may only be set to True when '
                                 'ignore_warnings is a boolean')
            issue_deprecation_warning('"ignore_warnings" as a boolean and '
                                      '"report_success" is True or None',
                                      '"report_success=False" or define '
                                      '"ignore_warnings" as callable/iterable',
                                      3, since='20150823')
        if isinstance(ignore_warnings, Iterable):
            ignored_warnings = ignore_warnings

            def ignore_warnings(warnings):
                return all(w.code in ignored_warnings for w in warnings)

        ignore_all_warnings = not callable(ignore_warnings) and ignore_warnings
        if text is None:
            text = filepage.text
        if not text:
            text = comment
        token = self.tokens['edit']
        result = None
        file_page_title = filepage.title(with_ns=False)
        file_size = None
        offset = _offset
        # make sure file actually exists
        if source_filename:
            if os.path.isfile(source_filename):
                file_size = os.path.getsize(source_filename)
            elif offset is not False:
                raise ValueError("File '%s' does not exist."
                                 % source_filename)

        if source_filename and _file_key:
            assert offset is False or file_size is not None
            if _verify_stash is None:
                _verify_stash = True
            if (offset is not False and offset is not True
                    and offset > file_size):
                raise ValueError(
                    'For the file key "{0}" the offset was set to {1} '
                    'while the file is only {2} bytes large.'.format(
                        _file_key, offset, file_size))

        if _verify_stash or offset is True:
            if not _file_key:
                raise ValueError('Without a file key it cannot request the '
                                 'stash information')
            if not source_filename:
                raise ValueError('Can request stash information only when '
                                 'using a file name.')
            props = ['size']
            if _verify_stash:
                props += ['sha1']
            stash_info = self.stash_info(_file_key, props)
            if offset is True:
                offset = stash_info['size']
            elif offset is False:
                if file_size != stash_info['size']:
                    raise ValueError(
                        'For the file key "{0}" the server reported a size '
                        '{1} while the file size is {2}'
                        .format(_file_key, stash_info['size'], file_size))
            elif offset is not False and offset != stash_info['size']:
                raise ValueError(
                    'For the file key "{0}" the server reported a size {1} '
                    'while the offset was {2}'.format(
                        _file_key, stash_info['size'], offset))

            if _verify_stash:
                # The SHA1 was also requested so calculate and compare it
                assert 'sha1' in stash_info, \
                    'sha1 not in stash info: {0}'.format(stash_info)
                sha1 = compute_file_hash(source_filename, bytes_to_read=offset)
                if sha1 != stash_info['sha1']:
                    raise ValueError(
                        'The SHA1 of {0} bytes of the stashed "{1}" is {2} '
                        'while the local file is {3}'.format(
                            offset, _file_key, stash_info['sha1'], sha1))

        assert offset is not True
        if _file_key and file_size is None:
            assert offset is False

        if _file_key and offset is False or offset == file_size:
            pywikibot.log('Reused already upload file using '
                          'filekey "{0}"'.format(_file_key))
            # TODO: Use sessionkey instead of filekey if necessary
            final_request = self._simple_request(action='upload', token=token,
                                                 filename=file_page_title,
                                                 comment=comment, text=text,
                                                 filekey=_file_key)
        elif source_filename:
            # TODO: Dummy value to allow also Unicode names, see bug T75661
            mime_filename = 'FAKE-NAME'
            # upload local file
            throttle = True
            filesize = os.path.getsize(source_filename)
            chunked_upload = (
                0 < chunk_size < filesize and self.mw_version >= '1.20')
            with open(source_filename, 'rb') as f:
                final_request = self._request(
                    throttle=throttle, parameters={
                        'action': 'upload', 'token': token, 'text': text,
                        'filename': file_page_title, 'comment': comment})
                if chunked_upload:
                    if offset > 0:
                        pywikibot.log('Continuing upload from byte '
                                      '{0}'.format(offset))
                    while True:
                        f.seek(offset)
                        chunk = f.read(chunk_size)
                        # workaround (hack) for T132676
                        # append another '\r' so that one is the payload and
                        # the second is used for newline when mangled by email
                        # package.
                        if (len(chunk) < chunk_size
                                or (offset + len(chunk)) == filesize
                                and chunk[-1] == b'\r'[0]):
                            chunk += b'\r'
                        req = self._request(
                            throttle=throttle, mime=True,
                            parameters={
                                'action': 'upload',
                                'token': token,
                                'stash': True,
                                'filesize': filesize,
                                'offset': offset,
                                'filename': file_page_title,
                                'ignorewarnings': ignore_all_warnings})
                        req.mime = {
                            'chunk': (chunk,
                                      ('application', 'octet-stream'),
                                      {'filename': mime_filename})
                        }
                        if _file_key:
                            req['filekey'] = _file_key
                        try:
                            data = req.submit()['upload']
                            self._uploaddisabled = False
                        except api.APIError as error:
                            # TODO: catch and process foreseeable errors
                            if error.code == 'uploaddisabled':
                                self._uploaddisabled = True
                            elif error.code == 'stashfailed' and \
                                    'offset' in error.other:
                                # TODO: Ask MediaWiki to change this
                                # ambiguous error code.

                                new_offset = int(error.other['offset'])
                                # If the offset returned from the server
                                # (the offset it expects now) is equal to
                                # the offset we sent it, there must be
                                # something else that prevented the upload,
                                # instead of simple offset mismatch. This
                                # also prevents infinite loops when we
                                # upload the same chunk again and again,
                                # every time ApiError.
                                if offset != new_offset:
                                    pywikibot.log(
                                        'Old offset: {0}; Returned '
                                        'offset: {1}; Chunk size: '
                                        '{2}'.format(offset, new_offset,
                                                     len(chunk)))
                                    pywikibot.warning('Attempting to correct '
                                                      'automatically from '
                                                      'offset mismatch error.')
                                    offset = new_offset
                                    continue
                            raise error
                        if 'nochange' in data:  # in simulation mode
                            break
                        _file_key = data['filekey']
                        if 'warnings' in data and not ignore_all_warnings:
                            if callable(ignore_warnings):
                                restart = False
                                if 'offset' not in data:
                                    # This is a result of a warning in the
                                    # first chunk. The chunk is not actually
                                    # stashed so upload must be restarted if
                                    # the warning is allowed.
                                    # T112416 and T112405#1637544
                                    restart = True
                                    data['offset'] = True
                                if ignore_warnings(create_warnings_list(data)):
                                    # Future warnings of this run
                                    # can be ignored
                                    if restart:
                                        return self.upload(
                                            filepage, source_filename,
                                            source_url, comment, text, watch,
                                            True, chunk_size, None, 0,
                                            report_success=False)

                                    ignore_warnings = True
                                    ignore_all_warnings = True
                                    offset = data['offset']
                                    continue
                                else:
                                    return False
                            result = data
                            result.setdefault('offset', 0)
                            break
                        throttle = False
                        if 'offset' in data:
                            new_offset = int(data['offset'])
                            if offset + len(chunk) != new_offset:
                                pywikibot.log('Old offset: {0}; Returned '
                                              'offset: {1}; Chunk size: '
                                              '{2}'.format(offset, new_offset,
                                                           len(chunk)))
                                pywikibot.warning('Unexpected offset.')
                            offset = new_offset
                        else:
                            pywikibot.warning('Offset was not supplied.')
                            offset += len(chunk)
                        if data['result'] != 'Continue':  # finished
                            pywikibot.log('Finished uploading last chunk.')
                            final_request['filekey'] = _file_key
                            break
                else:  # not chunked upload
                    if _file_key:
                        final_request['filekey'] = _file_key
                    else:
                        file_contents = f.read()
                        filetype = (mimetypes.guess_type(source_filename)[0]
                                    or 'application/octet-stream')
                        final_request.mime = {
                            'file': (file_contents, filetype.split('/'),
                                     {'filename': mime_filename})
                        }
        else:
            # upload by URL
            if not self.has_right('upload_by_url'):
                raise Error(
                    "User '%s' is not authorized to upload by URL on site %s."
                    % (self.user(), self))
            final_request = self._simple_request(
                action='upload', filename=file_page_title,
                url=source_url, comment=comment, text=text, token=token)
        if not result:
            final_request['watch'] = watch
            final_request['ignorewarnings'] = ignore_all_warnings
            try:
                result = final_request.submit()
                self._uploaddisabled = False
            except api.APIError as error:
                # TODO: catch and process foreseeable errors
                if error.code == 'uploaddisabled':
                    self._uploaddisabled = True
                raise error
            result = result['upload']
            pywikibot.debug(result, _logger)

        if 'warnings' in result and not ignore_all_warnings:
            if 'filekey' in result:
                _file_key = result['filekey']
            elif 'sessionkey' in result:
                # TODO: Probably needs to be reflected in the API call above
                _file_key = result['sessionkey']
                pywikibot.warning('Using sessionkey instead of filekey.')
            else:
                _file_key = None
                pywikibot.warning('No filekey defined.')
            if not report_success:
                result.setdefault('offset', True)
                if ignore_warnings(create_warnings_list(result)):
                    return self.upload(
                        filepage, source_filename, source_url, comment, text,
                        watch, True, chunk_size, _file_key,
                        result['offset'], report_success=False)
                else:
                    return False
            warn('When ignore_warnings=False in APISite.upload will change '
                 'from raising an UploadWarning into behaving like being a '
                 'callable returning False.', DeprecationWarning, 3)
            if len(result['warnings']) > 1:
                warn('The upload returned {0} warnings: '
                     '{1}'.format(len(result['warnings']),
                                  ', '.join(result['warnings'])),
                     UserWarning, 3)
            warning = list(result['warnings'].keys())[0]
            message = result['warnings'][warning]
            raise api.UploadWarning(warning, upload_warnings[warning]
                                    % {'msg': message},
                                    file_key=_file_key,
                                    offset=result.get('offset', False))
        elif 'result' not in result:
            pywikibot.output('Upload: unrecognized response: %s' % result)
        if result['result'] == 'Success':
            if report_success:
                pywikibot.output('Upload successful.')
            # If we receive a nochange, that would mean we're in simulation
            # mode, don't attempt to access imageinfo
            if 'nochange' not in result:
                filepage._load_file_revisions([result['imageinfo']])
        return result['result'] == 'Success'

    @deprecated_args(number='total', repeat=None, namespace='namespaces',
                     rcshow=None, rc_show=None, get_redirect=None, step=None,
                     showBot='bot', showRedirects='redirect',
                     showPatrolled='patrolled')
    def newpages(self, user=None, returndict=False,
                 start=None, end=None, reverse=False, bot=False,
                 redirect=False, excludeuser=None,
                 patrolled=None, namespaces=None, total=None):
        """Yield new articles (as Page objects) from recent changes.

        Starts with the newest article and fetches the number of articles
        specified in the first argument.

        The objects yielded are dependent on parameter returndict.
        When true, it yields a tuple composed of a Page object and a dict of
        attributes.
        When false, it yields a tuple composed of the Page object,
        timestamp (str), length (int), an empty string, username or IP
        address (str), comment (str).

        @param namespaces: only iterate pages in these namespaces
        @type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        # TODO: update docstring

        # N.B. API still provides no way to access Special:Newpages content
        # directly, so we get new pages indirectly through 'recentchanges'

        gen = self.recentchanges(
            start=start, end=end, reverse=reverse,
            namespaces=namespaces, changetype='new', user=user,
            excludeuser=excludeuser, bot=bot,
            redirect=redirect, patrolled=patrolled,
            total=total
        )
        for pageitem in gen:
            newpage = pywikibot.Page(self, pageitem['title'])
            if returndict:
                yield (newpage, pageitem)
            else:
                yield (newpage, pageitem['timestamp'], pageitem['newlen'],
                       '', pageitem['user'], pageitem['comment'])

    @deprecated('APISite.logevents(logtype="upload")', since='20170619')
    @deprecated_args(lestart='start', leend='end', leuser='user', letitle=None,
                     repeat=None, number='total', step=None)
    def newfiles(self, user=None, start=None, end=None, reverse=False,
                 total=None):
        """Yield information about newly uploaded files.

        DEPRECATED: Use logevents(logtype='upload') instead.

        Yields a tuple of FilePage, Timestamp, user(str), comment(str).

        N.B. the API does not provide direct access to Special:Newimages, so
        this is derived from the "upload" log events instead.
        """
        for event in self.logevents(logtype='upload', user=user,
                                    start=start, end=end, reverse=reverse,
                                    total=total):
            filepage = event.page()
            date = event.timestamp()
            user = event.user()
            comment = event.comment() or ''
            yield (filepage, date, user, comment)

    def querypage(self, special_page, total=None):
        """Yield Page objects retrieved from Special:{special_page}.

        @see: U{https://www.mediawiki.org/wiki/API:Querypage}

        Generic function for all special pages supported by the site MW API.

        @param special_page: Special page to query
        @param total: number of pages to return
        @raise AssertionError: special_page is not supported in SpecialPages.
        """
        param = self._paraminfo.parameter('query+querypage', 'page')
        assert special_page in param['type'], (
            '{0} not in {1}'.format(special_page, param['type']))

        return self._generator(api.PageGenerator,
                               type_arg='querypage', gqppage=special_page,
                               total=total)

    @deprecated_args(number='total', step=None, repeat=None)
    def longpages(self, total=None):
        """Yield Pages and lengths from Special:Longpages.

        Yields a tuple of Page object, length(int).

        @param total: number of pages to return
        """
        lpgen = self._generator(api.ListGenerator,
                                type_arg='querypage', qppage='Longpages',
                                total=total)
        for pageitem in lpgen:
            yield (pywikibot.Page(self, pageitem['title']),
                   int(pageitem['value']))

    @deprecated_args(number='total', step=None, repeat=None)
    def shortpages(self, total=None):
        """Yield Pages and lengths from Special:Shortpages.

        Yields a tuple of Page object, length(int).

        @param total: number of pages to return
        """
        spgen = self._generator(api.ListGenerator,
                                type_arg='querypage', qppage='Shortpages',
                                total=total)
        for pageitem in spgen:
            yield (pywikibot.Page(self, pageitem['title']),
                   int(pageitem['value']))

    @deprecated_args(number='total', step=None, repeat=None)
    def deadendpages(self, total=None):
        """Yield Page objects retrieved from Special:Deadendpages.

        @param total: number of pages to return
        """
        return self.querypage('Deadendpages', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def ancientpages(self, total=None):
        """Yield Pages, datestamps from Special:Ancientpages.

        @param total: number of pages to return
        """
        apgen = self._generator(api.ListGenerator,
                                type_arg='querypage', qppage='Ancientpages',
                                total=total)
        for pageitem in apgen:
            yield (pywikibot.Page(self, pageitem['title']),
                   pywikibot.Timestamp.fromISOformat(pageitem['timestamp']))

    @deprecated_args(number='total', step=None, repeat=None)
    def lonelypages(self, total=None):
        """Yield Pages retrieved from Special:Lonelypages.

        @param total: number of pages to return
        """
        return self.querypage('Lonelypages', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def unwatchedpages(self, total=None):
        """Yield Pages from Special:Unwatchedpages (requires Admin privileges).

        @param total: number of pages to return
        """
        return self.querypage('Unwatchedpages', total)

    @deprecated_args(step=None)
    def wantedpages(self, total=None):
        """Yield Pages from Special:Wantedpages.

        @param total: number of pages to return
        """
        return self.querypage('Wantedpages', total)

    def wantedfiles(self, total=None):
        """Yield Pages from Special:Wantedfiles.

        @param total: number of pages to return
        """
        return self.querypage('Wantedfiles', total)

    def wantedtemplates(self, total=None):
        """Yield Pages from Special:Wantedtemplates.

        @param total: number of pages to return
        """
        return self.querypage('Wantedtemplates', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def wantedcategories(self, total=None):
        """Yield Pages from Special:Wantedcategories.

        @param total: number of pages to return
        """
        return self.querypage('Wantedcategories', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def uncategorizedcategories(self, total=None):
        """Yield Categories from Special:Uncategorizedcategories.

        @param total: number of pages to return
        """
        return self.querypage('Uncategorizedcategories', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def uncategorizedimages(self, total=None):
        """Yield FilePages from Special:Uncategorizedimages.

        @param total: number of pages to return
        """
        return self.querypage('Uncategorizedimages', total)

    # synonym
    uncategorizedfiles = uncategorizedimages

    @deprecated_args(number='total', step=None, repeat=None)
    def uncategorizedpages(self, total=None):
        """Yield Pages from Special:Uncategorizedpages.

        @param total: number of pages to return
        """
        return self.querypage('Uncategorizedpages', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def uncategorizedtemplates(self, total=None):
        """Yield Pages from Special:Uncategorizedtemplates.

        @param total: number of pages to return
        """
        return self.querypage('Uncategorizedtemplates', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def unusedcategories(self, total=None):
        """Yield Category objects from Special:Unusedcategories.

        @param total: number of pages to return
        """
        return self.querypage('Unusedcategories', total)

    @deprecated_args(extension=None, number='total', step=None, repeat=None)
    def unusedfiles(self, total=None):
        """Yield FilePage objects from Special:Unusedimages.

        @param total: number of pages to return
        """
        return self.querypage('Unusedimages', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def withoutinterwiki(self, total=None):
        """Yield Pages without language links from Special:Withoutinterwiki.

        @param total: number of pages to return
        """
        return self.querypage('Withoutinterwiki', total)

    @deprecated_args(step=None)
    def broken_redirects(self, total=None):
        """Yield Pages with broken redirects from Special:BrokenRedirects.

        @param total: number of pages to return
        """
        return self.querypage('BrokenRedirects', total)

    @deprecated_args(step=None)
    def double_redirects(self, total=None):
        """Yield Pages with double redirects from Special:DoubleRedirects.

        @param total: number of pages to return
        """
        return self.querypage('DoubleRedirects', total)

    @deprecated_args(step=None)
    def redirectpages(self, total=None):
        """Yield redirect pages from Special:ListRedirects.

        @param total: number of pages to return
        """
        return self.querypage('Listredirects', total)

    @deprecated_args(lvl='level')
    def protectedpages(self, namespace=0, type='edit', level=False,
                       total=None):
        """
        Return protected pages depending on protection level and type.

        For protection types which aren't 'create' it uses L{APISite.allpages},
        while it uses for 'create' the 'query+protectedtitles' module.

        @see: U{https://www.mediawiki.org/wiki/API:Protectedtitles}

        @param namespace: The searched namespace.
        @type namespace: int or Namespace or str
        @param type: The protection type to search for (default 'edit').
        @type type: str
        @param level: The protection level (like 'autoconfirmed'). If False it
            shows all protection levels.
        @type level: str or False
        @return: The pages which are protected.
        @rtype: typing.Iterable[pywikibot.Page]
        """
        namespaces = self.namespaces.resolve(namespace)
        # always assert that, so we are be sure that type could be 'create'
        assert 'create' in self.protection_types(), \
            "'create' should be a valid protection type."
        if type == 'create':
            return self._generator(
                api.PageGenerator, type_arg='protectedtitles',
                namespaces=namespaces, gptlevel=level, total=total)
        else:
            return self.allpages(namespace=namespaces[0], protect_level=level,
                                 protect_type=type, total=total)

    @need_version('1.21')
    def get_property_names(self, force=False):
        """
        Get property names for pages_with_property().

        @see: U{https://www.mediawiki.org/wiki/API:Pagepropnames}

        @param force: force to retrieve userinfo ignoring cache
        @type force: bool
        """
        if force or not hasattr(self, '_property_names'):
            ppngen = self._generator(api.ListGenerator, 'pagepropnames')
            self._property_names = [pn['propname'] for pn in ppngen]
        return self._property_names

    @need_version('1.21')
    def pages_with_property(self, propname, *, total=None):
        """Yield Page objects from Special:PagesWithProp.

        @see: U{https://www.mediawiki.org/wiki/API:Pageswithprop}

        @param propname: must be a valid property.
        @type propname: str
        @param total: number of pages to return
        @type total: int or None
        @return: return a generator of Page objects
        @rtype: iterator
        """
        if propname not in self.get_property_names():
            raise NotImplementedError(
                '"{0}" is not a valid page property'.format(propname))
        return self._generator(api.PageGenerator, type_arg='pageswithprop',
                               gpwppropname=propname, total=total)

    def compare(self, old, diff):
        """
        Corresponding method to the 'action=compare' API action.

        @see: U{https://www.mediawiki.org/wiki/API:Compare}

        See: https://en.wikipedia.org/w/api.php?action=help&modules=compare
        Use pywikibot.diff's html_comparator() method to parse result.
        @param old: starting revision ID, title, Page, or Revision
        @type old: int, str, pywikibot.Page, or pywikibot.Page.Revision
        @param diff: ending revision ID, title, Page, or Revision
        @type diff: int, str, pywikibot.Page, or pywikibot.Page.Revision
        @return: Returns an HTML string of a diff between two revisions.
        @rtype: str
        """
        # check old and diff types
        def get_param(item):
            if isinstance(item, str):
                return 'title', item
            elif isinstance(item, pywikibot.Page):
                return 'title', item.title()
            elif isinstance(item, int):
                return 'rev', item
            elif isinstance(item, pywikibot.page.Revision):
                return 'rev', item.revid
            else:
                return None

        old = get_param(old)
        if not old:
            raise TypeError('old parameter is of invalid type')
        diff = get_param(diff)
        if not diff:
            raise TypeError('diff parameter is of invalid type')

        params = {'action': 'compare',
                  'from{0}'.format(old[0]): old[1],
                  'to{0}'.format(diff[0]): diff[1]}

        req = self._simple_request(**params)
        data = req.submit()
        comparison = data['compare']['*']
        return comparison

    @deprecated_args(step=None, sysop=None)
    def watched_pages(self, force=False, total=None):
        """
        Return watchlist.

        @see: U{https://www.mediawiki.org/wiki/API:Watchlistraw}

        @param force: Reload watchlist
        @type force: bool
        @param total: if not None, limit the generator to yielding this many
            items in total
        @type total: int
        @return: list of pages in watchlist
        @rtype: list of pywikibot.Page objects
        """
        expiry = None if force else pywikibot.config.API_config_expiry
        gen = api.PageGenerator(site=self, generator='watchlistraw',
                                expiry=expiry)
        gen.set_maximum_items(total)
        return gen
