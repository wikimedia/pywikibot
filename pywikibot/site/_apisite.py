"""Objects representing API interface to MediaWiki site."""
#
# (C) Pywikibot team, 2008-2021
#
# Distributed under the terms of the MIT license.
#
import datetime
import mimetypes
import os
import re
import time
import typing
from collections import OrderedDict, defaultdict, namedtuple
from collections.abc import Iterable
from contextlib import suppress
from textwrap import fill
from typing import Optional, Union
from warnings import warn

import pywikibot
import pywikibot.family
from pywikibot.backports import List
from pywikibot.comms.http import get_authentication
from pywikibot.data import api
from pywikibot.exceptions import (
    AbuseFilterDisallowedError,
    APIError,
    ArticleExistsConflictError,
    CaptchaError,
    CascadeLockedPageError,
    CircularRedirectError,
    EditConflictError,
    Error,
    InconsistentTitleError,
    InterwikiRedirectPageError,
    IsNotRedirectPageError,
    LockedNoPageError,
    LockedPageError,
    NoCreateError,
    NoPageError,
    NoUsernameError,
    PageCreatedConflictError,
    PageDeletedConflictError,
    PageRelatedError,
    PageSaveRelatedError,
    SiteDefinitionError,
    SpamblacklistError,
    TitleblacklistError,
    UnknownExtensionError,
    UploadError,
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
from pywikibot.site._generators import GeneratorsMixin
from pywikibot.site._interwikimap import _InterwikiMap
from pywikibot.site._namespace import Namespace
from pywikibot.site._siteinfo import Siteinfo
from pywikibot.site._tokenwallet import TokenWallet
from pywikibot.tools import (
    MediaWikiVersion,
    compute_file_hash,
    deprecate_arg,
    deprecated,
    deprecated_args,
    issue_deprecation_warning,
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
    GeneratorsMixin,
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

    """API interface to MediaWiki site.

    Do not instantiate directly; use :py:obj:`pywikibot.Site` function.
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

        :raises pywikibot.exceptions.SiteDefinitionError: if the url given in
            the interwiki table doesn't match any of the existing families.
        :raises KeyError: if the prefix is not an interwiki prefix.
        """
        return self._interwikimap[prefix].site

    def interwiki_prefix(self, site):
        """
        Return the interwiki prefixes going to that site.

        The interwiki prefixes are ordered first by length (shortest first)
        and then alphabetically. :py:obj:`interwiki(prefix)` is not
        guaranteed to equal ``site`` (i.e. the parameter passed to this
        function).

        :param site: The targeted site, which might be it's own.
        :type site: :py:obj:`BaseSite`
        :return: The interwiki prefixes
        :rtype: list (guaranteed to be not empty)
        :raises KeyError: if there is no interwiki prefix for that site.
        """
        assert site is not None, 'Site must not be None'
        prefixes = set()
        for url in site._interwiki_urls():
            prefixes.update(self._interwikimap.get_by_url(url))
        if not prefixes:
            raise KeyError(
                "There is no interwiki prefix to '{}'".format(site))
        return sorted(prefixes, key=lambda p: (len(p), p))

    def local_interwiki(self, prefix):
        """
        Return whether the interwiki prefix is local.

        A local interwiki prefix is handled by the target site like a normal
        link. So if that link also contains an interwiki link it does follow
        it as long as it's a local link.

        :raises pywikibot.exceptions.SiteDefinitionError: if the url given in
            the interwiki table doesn't match any of the existing families.
        :raises KeyError: if the prefix is not an interwiki prefix.
        """
        return self._interwikimap[prefix].local

    @classmethod
    def fromDBName(cls, dbname, site=None):  # noqa: N802
        """
        Create a site from a database name using the sitematrix.

        :param dbname: database name
        :type dbname: str
        :param site: Site to load sitematrix from. (Default meta.wikimedia.org)
        :type site: pywikibot.site.APISite
        :return: site object for the database name
        :rtype: pywikibot.site.APISite
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
        raise ValueError('Cannot parse a site out of {}.'.format(dbname))

    @deprecated_args(step=True)
    def _generator(self, gen_class, type_arg: Optional[str] = None,
                   namespaces=None, total: Optional[int] = None, **args):
        """Convenience method that returns an API generator.

        All generic keyword arguments are passed as MW API parameter
        except for 'g_content' which is passed as a normal parameter to
        the generator's Initializer.

        :param gen_class: the type of generator to construct (must be
            a subclass of pywikibot.data.api._RequestWrapper)
        :param type_arg: query type argument to be passed to generator's
            constructor unchanged (not all types require this)
        :param namespaces: if not None, limit the query to namespaces in
            this list
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param total: if not None, limit the generator to yielding this
            many items in total
        :return: iterable with parameters set
        :rtype: _RequestWrapper
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
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

        :rtype: bool
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

        :rtype: bool
        """
        auth_token = get_authentication(self.base_url(''))
        return auth_token is not None and len(auth_token) == 4

    def login(self, autocreate: bool = False, user: Optional[str] = None):
        """
        Log the user in if not already logged in.

        :param autocreate: if true, allow auto-creation of the account
            using unified login
        :param user: bot user name. Overrides the username set by
            BaseSite initializer parameter or user-config.py setting

        :raises pywikibot.exceptions.NoUsernameError: Username is not
            recognised by the site.
        :see: https://www.mediawiki.org/wiki/API:Login
        """
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
        except APIError:
            pass
        except NoUsernameError as e:
            if not autocreate:
                raise e

        if self.is_oauth_token_available():
            if self.userinfo['name'] == self.username():
                error_msg = ('Logging in on {} via OAuth failed'
                             .format(self))
            elif self.username() is None:
                error_msg = ('No username has been defined in your '
                             'user-config.py: you have to add in this '
                             'file the following line:\n'
                             'usernames[{family!r}][{lang!r}]= {username!r}'
                             .format(family=self.family,
                                     lang=self.lang,
                                     username=self.userinfo['name']))
            else:
                error_msg = ('Logged in on {site} via OAuth as {wrong}, but '
                             'expect as {right}'
                             .format(site=self,
                                     wrong=self.userinfo['name'],
                                     right=self.username()))

            raise NoUsernameError(error_msg)

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
        https://www.mediawiki.org/wiki/API:Logout

        :raises APIError: Logout is not available when OAuth enabled.
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

        https://www.mediawiki.org/wiki/API:Userinfo
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

    @remove_last_args(['sysop'])
    def is_blocked(self):
        """
        Return True when logged in user is blocked.

        To check whether a user can perform an action,
        the method has_right should be used.
        https://www.mediawiki.org/wiki/API:Userinfo

        :rtype: bool
        """
        return 'blockinfo' in self.userinfo

    def get_searched_namespaces(self, force=False):
        """
        Retrieve the default searched namespaces for the user.

        If no user is logged in, it returns the namespaces used by default.
        Otherwise it returns the user preferences. It caches the last result
        and returns it, if the username or login status hasn't changed.

        :param force: Whether the cache should be discarded.
        :return: The namespaces which are searched by default.
        :rtype: ``set`` of :py:obj:`Namespace`
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
                and self._useroptions['searchNs{}'.format(ns.id)]
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

        :param msg_prefix: The calling method name
        :type msg_prefix: str
        :param start: The start value to compare
        :param end: The end value to compare
        :param reverse: The reverse option
        :type reverse: bool
        :param is_ts: When comparing timestamps (with is_ts=True) the start
            is usually greater than end. Comparing titles this is vice versa.
        :type is_ts: bool
        :raises AssertionError: start/end values are in wrong order
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
        https://www.mediawiki.org/wiki/API:Userinfo

        :param right: a specific right to be validated
        :type right: str
        """
        return right.lower() in self.userinfo['rights']

    @remove_last_args(['sysop'])
    def has_group(self, group):
        """Return true if and only if the user is a member of specified group.

        Possible values of 'group' may vary depending on wiki settings,
        but will usually include bot.
        https://www.mediawiki.org/wiki/API:Userinfo
        """
        return group.lower() in self.userinfo['groups']

    @remove_last_args(['sysop'])
    def messages(self):
        """Return true if the user has new messages, and false otherwise."""
        return 'messages' in self.userinfo

    def mediawiki_messages(self, keys, lang: Optional[str] = None):
        """Fetch the text of a set of MediaWiki messages.

        The returned dict uses each key to store the associated message.

        :see: https://www.mediawiki.org/wiki/API:Allmessages

        :param keys: MediaWiki messages to fetch
        :type keys: iterable of str
        :param lang: a language code, default is self.lang
        :rtype: OrderedDict
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

            return result

        return OrderedDict((key, _mw_msg_cache[amlang][key]) for key in keys)

    @deprecated_args(forceReload=True)
    def mediawiki_message(self, key, lang=None) -> str:
        """Fetch the text for a MediaWiki message.

        :param key: name of MediaWiki message
        :type key: str
        :param lang: a language code, default is self.lang
        :type lang: str or None
        """
        return self.mediawiki_messages([key], lang=lang)[key]

    def has_mediawiki_message(self, key, lang=None):
        """Determine if the site defines a MediaWiki message.

        :param key: name of MediaWiki message
        :type key: str
        :param lang: a language code, default is self.lang
        :type lang: str or None

        :rtype: bool
        """
        return self.has_all_mediawiki_messages([key], lang=lang)

    def has_all_mediawiki_messages(self, keys, lang=None):
        """Confirm that the site defines a set of MediaWiki messages.

        :param keys: names of MediaWiki messages
        :type keys: iterable of str
        :param lang: a language code, default is self.lang
        :type lang: str or None

        :rtype: bool
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

        :return: list of tuples (month name, abbreviation)
        :rtype: list
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

        :param args: text to be expanded
        """
        needed_mw_messages = ('and', 'comma-separator', 'word-separator')
        if not args:
            return ''

        try:
            msgs = self.mediawiki_messages(needed_mw_messages)
        except KeyError:
            raise NotImplementedError(
                'MediaWiki messages missing: {}'.format(needed_mw_messages))

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

        :param text: text to be expanded
        :type text: str
        :param title: page title without section
        :type title: str
        :param includecomments: if True do not strip comments
        :type includecomments: bool
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

        It calls :py:obj:`server_time` first so it queries the server to
        get the current server time.

        :return: the server time
        :rtype: str (as 'yyyymmddhhmmss')
        """
        return self.server_time().totimestampformat()

    def server_time(self):
        """
        Return a Timestamp object representing the current server time.

        It uses the 'time' property of the siteinfo 'general'. It'll force a
        reload before returning the time.

        :return: the current server time
        :rtype: :py:obj:`Timestamp`
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
        return [word]

    @remove_last_args(('default', ))
    def redirect(self):
        """Return the localized #REDIRECT keyword."""
        # return the magic word without the preceding '#' character
        return self.getmagicwords('redirect')[0].lstrip('#')

    @deprecated('redirect_regex', since='20210103')
    def redirectRegex(self):  # noqa: N802
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
                    'Broken namespace alias "{}" (id: {}) on {}'.format(
                        item['*'], ns, self))
            else:
                if item['*'] not in namespace:
                    namespace.aliases.append(item['*'])

        return _namespaces

    def has_extension(self, name):
        """Determine whether extension `name` is loaded.

        :param name: The extension to check for, case sensitive
        :type name: str
        :return: If the extension is loaded
        :rtype: bool
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

    def dbName(self):  # noqa: N802
        """Return this site's internal id."""
        return self.siteinfo['wikiid']

    @property
    def lang(self):
        """Return the code for the language of this Site."""
        return self.siteinfo['lang']

    def version(self) -> str:
        """Return live project version number as a string.

        Use :py:obj:`pywikibot.site.mw_version` to compare MediaWiki versions.
        """
        try:
            version = self.siteinfo.get('generator', expiry=1).split(' ')[1]
        except APIError:
            msg = 'You have no API read permissions.'
            if not self.logged_in():
                msg += ' Seems you are not logged in.'
            pywikibot.error(msg)
            raise

        if MediaWikiVersion(version) < '1.23':
            raise RuntimeError(
                'Pywikibot "{}" does not support MediaWiki "{}".\n'
                'Use Pywikibot prior to "6.0" branch instead.'
                .format(pywikibot.__version__, version))
        return version

    @property
    def mw_version(self):
        """Return self.version() as a MediaWikiVersion object.

        Cache the result for 24 hours.
        :rtype: MediaWikiVersion
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

    def image_repository(self):
        """Return Site object for image repository e.g. commons."""
        code, fam = self.shared_image_repository()
        if bool(code or fam):
            return pywikibot.Site(code, fam, self.username())

        return None

    def data_repository(self):
        """
        Return the data repository connected to this site.

        :return: The data repository if one is connected or None otherwise.
        :rtype: pywikibot.site.DataSite or None
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
                pywikibot.warning('Site "{}" supports wikibase at "{}", but '
                                  'creation failed: {}.'.format(self, url, e))
                return None
        else:
            assert 'warnings' in data
            return None

    def is_image_repository(self):
        """Return True if Site object is the image repository."""
        return self is self.image_repository()

    def is_data_repository(self):
        """Return True if its data repository is itself."""
        # fixme: this was an identity check
        return self == self.data_repository()

    def page_from_repository(self, item):
        """
        Return a Page for this site object specified by Wikibase item.

        :param item: id number of item, "Q###",
        :type item: str
        :return: Page, or Category object given by Wikibase item number
            for this site object.
        :rtype: pywikibot.Page or None

        :raises pywikibot.exceptions.UnknownExtensionError: site has no
            Wikibase extension
        :raises NotimplementedError: method not implemented for a Wikibase site
        """
        if not self.has_data_repository:
            raise UnknownExtensionError(
                'Wikibase is not implemented for {}.'.format(self))
        if self.is_data_repository():
            raise NotImplementedError(
                'page_from_repository method is not implemented for '
                'Wikibase {}.'.format(self))
        repo = self.data_repository()
        dp = pywikibot.ItemPage(repo, item)
        try:
            page_title = dp.getSitelink(self)
        except NoPageError:
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

        :param num: Namespace constant.
        :type num: int
        :param all: If True return a Namespace object. Otherwise
            return the namespace name.
        :return: local name or Namespace object
        :rtype: str or Namespace
        """
        if all:
            return self.namespaces[num]
        return self.namespaces[num][0]

    def _update_page(self, page, query, verify_imageinfo: bool = False):
        """Update page attributes.

        :param page: page object to be updated
        :param query: a api.QueryGenerator
        :param verify_imageinfo: if given, every pageitem is checked
            whether 'imageinfo' is missing. In that case an exception
            is raised.

        :raises NoPageError: 'missing' key is found in pageitem
        :raises PageRelatedError: 'imageinfo' is missing in pageitem
        """
        for pageitem in query:
            if not self.sametitle(pageitem['title'],
                                  page.title(with_section=False)):
                raise InconsistentTitleError(page, pageitem['title'])
            api.update_page(page, pageitem, query.props)

            if verify_imageinfo and 'imageinfo' not in pageitem:
                if 'missing' in pageitem:
                    raise NoPageError(page)
                raise PageRelatedError(
                    page, 'loadimageinfo: Query on {} returned no imageinfo')

    def loadpageinfo(self, page, preload=False):
        """Load page info from api and store in page attributes.

        :see: https://www.mediawiki.org/wiki/API:Info
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
        [1] https://www.mediawiki.org/wiki/API:Imageinfo

        Parameters validation and error handling left to the API call.

        :param history: if true, return the image's version history
        :param url_width: see iiurlwidth in [1]
        :param url_height: see iiurlheigth in [1]
        :param url_param: see iiurlparam in [1]

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

        :param page: a pywikibot.Page object
        :type page: pywikibot.Page
        :param action: a valid restriction type like 'edit', 'move'
        :type action: str
        :rtype: bool

        :raises ValueError: invalid action parameter
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

        :param page: page to search redirects for
        :type page: pywikibot.page.BasePage
        :return: redirect target of page
        :rtype: pywikibot.Page

        :raises pywikibot.exceptions.IsNotRedirectPageError: page is not a
            redirect
        :raises RuntimeError: no redirects found
        :raises pywikibot.exceptions.CircularRedirectError: page is a circular
            redirect
        :raises pywikibot.exceptions.InterwikiRedirectPageError: the redirect
            target is on another site
        """
        if not self.page_isredirect(page):
            raise IsNotRedirectPageError(page)
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
        target_title = '{title}{section}'.format_map(redirmap[title])

        if self.sametitle(title, target_title):
            raise CircularRedirectError(page)

        if 'pages' not in result['query']:
            # No "pages" element might indicate a circular redirect
            # Check that a "to" link is also a "from" link in redirmap
            for _from, _to in redirmap.items():
                if _to['title'] in redirmap:
                    raise CircularRedirectError(page)

            target = pywikibot.Page(source=page.site, title=target_title)
            # Check if target is on another site.
            if target.site != page.site:
                raise InterwikiRedirectPageError(page, target)
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

    def validate_tokens(self, types: List[str]) -> List[str]:
        """Validate if requested tokens are acceptable.

        Valid tokens depend on mw version.
        """
        query = 'tokens' if self.mw_version < '1.24wmf19' else 'query+tokens'
        token_types = self._paraminfo.parameter(query, 'type')['type']
        return [token for token in types if token in token_types]

    def get_tokens(self, types: List[str], all: bool = False) -> dict:
        """Preload one or multiple tokens.

        For MediaWiki version 1.23, only one token can be retrieved at once.
        For MediaWiki versions since 1.24wmfXXX a new token
        system was introduced which reduced the amount of tokens available.
        Most of them were merged into the 'csrf' token. If the token type in
        the parameter is not known it will default to the 'csrf' token.

        The other token types available are:
         - createaccount
         - deleteglobalaccount
         - login
         - patrol
         - rollback
         - setglobalaccountstatus
         - userrights
         - watch

        :see: https://www.mediawiki.org/wiki/API:Tokens

        :param types: the types of token (e.g., "edit", "move", "delete");
            see API documentation for full list of types
        :param all: load all available tokens, if None only if it can be done
            in one request.

        return: a dict with retrieved valid tokens.
        """
        def warn_handler(mod, text):
            """Filter warnings for not available tokens."""
            return re.match(
                r'Action \'\w+\' is not allowed for the current user', text)

        user_tokens = {}
        if self.mw_version < '1.24wmf19':
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

    # TODO: expand support to other parameters of action=parse?
    def get_parsed_page(self, page):
        """Retrieve parsed text of the page using action=parse.

        :see: https://www.mediawiki.org/wiki/API:Parse
        """
        req = self._simple_request(action='parse', page=page)
        data = req.submit()
        assert 'parse' in data, "API parse response lacks 'parse' key"
        assert 'text' in data['parse'], "API parse response lacks 'text' key"
        parsed_text = data['parse']['text']['*']
        return parsed_text

    def getcategoryinfo(self, category):
        """Retrieve data on contents of category.

        :see: https://www.mediawiki.org/wiki/API:Categoryinfo
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

    def isBot(self, username):  # noqa: N802
        """Return True is username is a bot user."""
        return username in (userdata['name'] for userdata in self.botusers())

    @property
    def logtypes(self):
        """Return a set of log types available on current site."""
        return set(filter(None, self._paraminfo.parameter(
            'query+logevents', 'type')['type']))

    @need_right('deleterevision')
    def deleterevs(self, targettype: str, ids, *,
                   hide=None, show=None, reason='', target=None):
        """Delete or undelete specified page revisions, file versions or logs.

        :see: https://www.mediawiki.org/wiki/API:Revisiondelete

        If more than one target id is provided, the same action is taken for
        all of them.

        *New in version 6.0.*

        :param targettype: Type of target. One of "archive", "filearchive",
            "logging", "oldimage", "revision".
        :param ids: Identifiers for the revision, log, file version or archive.
        :type ids: int, str, or list of int or str
        :param hide: What to delete. Can be "comment", "content", "user" or a
            combination of them in pipe-separate form such as "comment|user".
        :type hide: str or list of str
        :param show: What to undelete. Can be "comment", "content", "user" or
            a combination of them in pipe-separate form such as "comment|user".
        :type show: str or list of str
        :param reason: Deletion reason.
        :param target: Page object or page title, if required for the type.
        """
        if isinstance(target, pywikibot.Page):
            page = target
            target = page.title()
        elif target:
            page = pywikibot.Page(self, target)

        token = self.tokens['delete']
        params = {
            'action': 'revisiondelete',
            'token': token,
            'type': targettype,
            'ids': ids,
            'hide': hide,
            'show': show,
            'target': target,
            'reason': reason}

        req = self._simple_request(**params)

        if target:
            self.lock_page(page)

        try:
            req.submit()
        except APIError as err:
            errdata = {
                'site': self,
                'title': target,
                'user': self.user(),
            }
            if err.code in self._dl_errors:
                raise Error(
                    self._dl_errors[err.code].format_map(errdata)
                ) from None
            pywikibot.debug("revdelete: Unexpected error code '{}' received."
                            .format(err.code),
                            _logger)
            raise
        else:
            if target:
                page.clear_cache()
        finally:
            if target:
                self.unlock_page(page)

    # Catalog of editpage error codes, for use in generating messages.
    # The block at the bottom are page related errors.
    _ep_errors = {
        'noapiwrite': 'API editing not enabled on {site} wiki',
        'writeapidenied':
            'User {user} is not authorized to edit on {site} wiki',
        'cantcreate':
            'User {user} not authorized to create new pages on {site} '
            'wiki',
        'cantcreate-anon':
            'Bot is not logged in, and anon users are not authorized to '
            'create new pages on {site} wiki',
        'noimageredirect-anon':
            'Bot is not logged in, and anon users are not authorized to '
            'create image redirects on {site} wiki',
        'noimageredirect': 'User {user} not authorized to create image '
                           'redirects on {site} wiki',
        'filtered': '{info}',
        'contenttoobig': '{info}',
        'noedit-anon': 'Bot is not logged in, and anon users are not '
                       'authorized to edit on {site} wiki',
        'noedit':
            'User {user} not authorized to edit pages on {site} wiki',
        'missingtitle': NoCreateError,
        'editconflict': EditConflictError,
        'articleexists': PageCreatedConflictError,
        'pagedeleted': PageDeletedConflictError,
        'protectedpage': LockedPageError,
        'protectedtitle': LockedNoPageError,
        'cascadeprotected': CascadeLockedPageError,
        'titleblacklist-forbidden': TitleblacklistError,
        'spamblacklist': SpamblacklistError,
        'abusefilter-disallowed': AbuseFilterDisallowedError,
    }
    _ep_text_overrides = {'appendtext', 'prependtext', 'undo'}

    @need_right('edit')
    def editpage(self, page, summary=None, minor=True, notminor=False,
                 bot=True, recreate=True, createonly=False, nocreate=False,
                 watch=None, **kwargs) -> bool:
        """Submit an edit to be saved to the wiki.

        :see: https://www.mediawiki.org/wiki/API:Edit

        :param page: The Page to be saved.
            By default its .text property will be used
            as the new text to be saved to the wiki
        :param summary: the edit summary
        :param minor: if True (default), mark edit as minor
        :param notminor: if True, override account preferences to mark edit
            as non-minor
        :param recreate: if True (default), create new page even if this
            title has previously been deleted
        :param createonly: if True, raise an error if this title already
            exists on the wiki
        :param nocreate: if True, raise an error if the page does not exist
        :param watch: Specify how the watchlist is affected by this edit, set
            to one of "watch", "unwatch", "preferences", "nochange":
            * watch: add the page to the watchlist
            * unwatch: remove the page from the watchlist
            * preferences: use the preference settings (default)
            * nochange: don't change the watchlist
        :param bot: if True, mark edit with bot flag
        :keyword text: Overrides Page.text
        :type text: str
        :keyword section: Edit an existing numbered section or
            a new section ('new')
        :type section: int or str
        :keyword prependtext: Prepend text. Overrides Page.text
        :type text: str
        :keyword appendtext: Append text. Overrides Page.text.
        :type text: str
        :keyword undo: Revision id to undo. Overrides Page.text
        :type undo: int
        :return: True if edit succeeded, False if it failed
        :raises pywikibot.exceptions.Error: No text to be saved
        :raises pywikibot.exceptions.NoPageError: recreate is disabled and page
            does not exist
        :raises pywikibot.exceptions.CaptchaError: config.solve_captcha is
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
            except NoPageError:
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
            pywikibot.warning("editpage: Invalid watch value '{}' ignored."
                              .format(watch))
        req = self._simple_request(**params)

        self.lock_page(page)
        try:
            while True:
                try:
                    result = req.submit()
                    pywikibot.debug('editpage response: {}'.format(result),
                                    _logger)
                except APIError as err:
                    if err.code.endswith('anon') and self.logged_in():
                        pywikibot.debug(
                            "editpage: received '{}' even though bot is "
                            'logged in'.format(err.code),
                            _logger)
                    if err.code == 'abusefilter-warning':
                        pywikibot.warning('{info}\nRetrying.'
                                          .format(info=err.info))
                        continue
                    if err.code in self._ep_errors:
                        exception = self._ep_errors[err.code]
                        if isinstance(exception, str):
                            errdata = {
                                'site': self,
                                'title': page.title(with_section=False),
                                'user': self.user(),
                                'info': err.info
                            }
                            raise Error(
                                exception.format_map(errdata)
                            ) from None
                        if issubclass(exception, AbuseFilterDisallowedError):
                            errdata = {
                                'info': err.info,
                                'other': err.other,
                            }
                            raise exception(page, **errdata) from None
                        if issubclass(exception, SpamblacklistError):
                            urls = ', '.join(err.other[err.code]['matches'])
                            raise exception(page, url=urls) from None
                        raise exception(page) from None
                    pywikibot.debug(
                        "editpage: Unexpected error code '{}' received."
                        .format(err.code),
                        _logger)
                    raise
                assert 'edit' in result and 'result' in result['edit'], result

                if result['edit']['result'] == 'Success':
                    if 'nochange' in result['edit']:
                        # null edit, page not changed
                        pywikibot.log('Page [[{}]] saved without any changes.'
                                      .format(page.title()))
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
                            webbrowser.open('{}://{}{}'
                                            .format(self.protocol(),
                                                    self.hostname(),
                                                    captcha['url']))
                            req['captchaword'] = pywikibot.input(
                                'Please view CAPTCHA in your browser, '
                                'then type answer here:')
                            continue

                        pywikibot.error(
                            'editpage: unknown CAPTCHA response {}, '
                            'page not saved'
                            .format(captcha))
                        return False

                    if 'spamblacklist' in result['edit']:
                        raise SpamblacklistError(
                            page, result['edit']['spamblacklist']) from None

                    if 'code' in result['edit'] and 'info' in result['edit']:
                        pywikibot.error(
                            'editpage: {}\n{}, '
                            .format(result['edit']['code'],
                                    result['edit']['info']))
                        return False

                    pywikibot.error('editpage: unknown failure reason {}'
                                    .format(str(result)))
                    return False

                pywikibot.error(
                    "editpage: Unknown result code '{}' received; "
                    'page not saved'.format(result['edit']['result']))
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

        :see: https://www.mediawiki.org/wiki/API:Mergehistory

        Revisions dating up to the given timestamp in the source will be
        moved into the destination page history. History merge fails if
        the timestamps of source and dest revisions overlap (all source
        revisions must be dated before the earliest dest revision).

        :param source: Source page from which revisions will be merged
        :type source: pywikibot.Page
        :param dest: Destination page to which revisions will be merged
        :type dest: pywikibot.Page
        :param timestamp: Revisions from this page dating up to this timestamp
            will be merged into the destination page (if not given or False,
            all revisions will be merged)
        :type timestamp: pywikibot.Timestamp
        :param reason: Optional reason for the history merge
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
            raise NoPageError(source,
                              'Cannot merge revisions from source {source} '
                              'because it does not exist on {site}'
                              .format_map(errdata))
        if not dest.exists():
            raise NoPageError(dest,
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
        except APIError as err:
            if err.code in self._mh_errors:
                on_error = self._mh_errors[err.code]
                raise Error(on_error.format_map(errdata)) from None

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
        'noapiwrite': 'API editing not enabled on {site} wiki',
        'writeapidenied':
            'User {user} is not authorized to edit on {site} wiki',
        'nosuppress':
            'User {user} is not authorized to move pages without '
            'creating redirects',
        'cantmove-anon':
            'Bot is not logged in, and anon users are not authorized to '
            'move pages on {site} wiki',
        'cantmove':
            'User {user} is not authorized to move pages on {site} wiki',
        'immobilenamespace':
            'Pages in {oldnamespace} namespace cannot be moved on {site} '
            'wiki',
        'articleexists': OnErrorExc(exception=ArticleExistsConflictError,
                                    on_new_page=True),
        # "protectedpage" can happen in both directions.
        'protectedpage': OnErrorExc(exception=LockedPageError,
                                    on_new_page=None),
        'protectedtitle': OnErrorExc(exception=LockedNoPageError,
                                     on_new_page=True),
        'nonfilenamespace':
            'Cannot move a file to {newnamespace} namespace on {site} '
            'wiki',
        'filetypemismatch':
            '[[{newtitle}]] file extension does not match content of '
            '[[{oldtitle}]]',
        'missingtitle': "{oldtitle} doesn't exist",
    }

    @need_right('move')
    def movepage(self, page, newtitle: str, summary, movetalk=True,
                 noredirect=False):
        """Move a Page to a new title.

        :see: https://www.mediawiki.org/wiki/API:Move

        :param page: the Page to be moved (must exist)
        :param newtitle: the new title for the Page
        :param summary: edit summary (required!)
        :param movetalk: if True (default), also move the talk page if possible
        :param noredirect: if True, suppress creation of a redirect from the
            old title to the new one
        :return: Page object with the new title
        :rtype: pywikibot.Page
        """
        oldtitle = page.title(with_section=False)
        newlink = pywikibot.Link(newtitle, self)
        newpage = pywikibot.Page(newlink)
        if newlink.namespace:
            newtitle = self.namespace(newlink.namespace) + ':' + newlink.title
        else:
            newtitle = newlink.title
        if oldtitle == newtitle:
            raise Error('Cannot move page {} to its own title.'
                        .format(oldtitle))
        if not page.exists():
            raise NoPageError(page,
                              'Cannot move page {page} because it '
                              'does not exist on {site}.')
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
            pywikibot.debug('movepage response: {}'.format(result),
                            _logger)
        except APIError as err:
            if err.code.endswith('anon') and self.logged_in():
                pywikibot.debug(
                    "movepage: received '{}' even though bot is logged in"
                    .format(err.code),
                    _logger)
            if err.code in self._mv_errors:
                on_error = self._mv_errors[err.code]
                if hasattr(on_error, 'exception'):
                    # LockedPageError can be raised both if "from" or "to" page
                    # are locked for the user.
                    # Both pages locked is not considered
                    # (a double failure has low probability)
                    if issubclass(on_error.exception, LockedPageError):
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
                    raise on_error.exception(failed_page) from None

                errdata = {
                    'site': self,
                    'oldtitle': oldtitle,
                    'oldnamespace': self.namespace(page.namespace()),
                    'newtitle': newtitle,
                    'newnamespace': self.namespace(newlink.namespace),
                    'user': self.user(),
                }

                raise Error(on_error.format_map(errdata)) from None

            pywikibot.debug("movepage: Unexpected error code '{}' received."
                            .format(err.code),
                            _logger)
            raise
        finally:
            self.unlock_page(page)
        if 'move' not in result:
            pywikibot.error('movepage: {}'.format(result))
            raise Error('movepage: unexpected response')
        # TODO: Check for talkmove-error messages
        if 'talkmove-error-code' in result['move']:
            pywikibot.warning(
                'movepage: Talk page {} not moved'
                .format(page.toggleTalkPage().title(as_link=True)))
        return pywikibot.Page(page, newtitle)

    # catalog of rollback errors for use in error messages
    _rb_errors = {
        'noapiwrite': 'API editing not enabled on {site} wiki',
        'writeapidenied': 'User {user} not allowed to edit through the API',
        'alreadyrolled':
            'Page [[{title}]] already rolled back; action aborted.',
    }  # other errors shouldn't arise because we check for those errors

    @need_right('rollback')
    def rollbackpage(self, page, **kwargs):
        """Roll back page to version before last user's edits.

        :see: https://www.mediawiki.org/wiki/API:Rollback

        The keyword arguments are those supported by the rollback API.

        As a precaution against errors, this method will fail unless
        the page history contains at least two revisions, and at least
        one that is not by the same user who made the last edit.

        :param page: the Page to be rolled back (must exist)
        :keyword user: the last user to be rollbacked;
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
        except APIError as err:
            errdata = {
                'site': self,
                'title': page.title(with_section=False),
                'user': self.user(),
            }
            if err.code in self._rb_errors:
                raise Error(
                    self._rb_errors[err.code].format_map(errdata)
                ) from None
            pywikibot.debug("rollback: Unexpected error code '{}' received."
                            .format(err.code),
                            _logger)
            raise
        finally:
            self.unlock_page(page)

    # catalog of delete errors for use in error messages
    _dl_errors = {
        'noapiwrite': 'API editing not enabled on {site} wiki',
        'writeapidenied': 'User {user} not allowed to edit through the API',
        'permissiondenied': 'User {user} not authorized to (un)delete '
                            'pages on {site} wiki.',
        'cantdelete':
            'Could not delete [[{title}]]. Maybe it was deleted already.',
        'cantundelete': 'Could not undelete [[{title}]]. '
                        'Revision may not exist or was already undeleted.',
        'nodeleteablefile': 'No such old version of file',
        'missingtitle': "[[{title}]] doesn't exist.",
    }  # other errors shouldn't occur because of pre-submission checks

    @need_right('delete')
    def delete(self, page, reason: str, *, oldimage: Optional[str] = None):
        """Delete a page or a specific old version of a file from the wiki.

        Requires appropriate privileges.

        :see: https://www.mediawiki.org/wiki/API:Delete
        Page to be deleted can be given either as Page object or as pageid.
        To delete a specific version of an image the oldimage identifier
        must be provided.

        *Renamed in version 6.1.*

        *New in version 6.1:* keyword only parameter *oldimage* was added.

        :param page: Page to be deleted or its pageid.
        :type page: :py:obj:`pywikibot.page.BasePage` or, for pageid,
            int or str
        :param reason: Deletion reason.
        :param oldimage: oldimage id of the file version to be deleted.
            If a BasePage object is given with page parameter, it has to
            be a FilePage.
        :raises TypeError, ValueError: page has wrong type/value.
        """
        if oldimage and isinstance(page, pywikibot.page.BasePage) \
           and not isinstance(page, pywikibot.FilePage):
            raise TypeError("'page' must be a FilePage not a '{}'"
                            .format(page.__class__.__name__))

        token = self.tokens['delete']
        params = {
            'action': 'delete',
            'token': token,
            'reason': reason,
            'oldimage': oldimage,
        }

        if isinstance(page, pywikibot.page.BasePage):
            params['title'] = page
            msg = page.title(with_section=False)
        else:
            pageid = int(page)
            params['pageid'] = pageid
            msg = pageid

        req = self._simple_request(**params)
        self.lock_page(page)
        try:
            req.submit()
        except APIError as err:
            errdata = {
                'site': self,
                'title': msg,
                'user': self.user(),
            }
            if err.code in self._dl_errors:
                raise Error(
                    self._dl_errors[err.code].format_map(errdata)
                ) from None
            pywikibot.debug('delete: Unexpected error code {!r} received.'
                            .format(err.code),
                            _logger)
            raise
        else:
            page.clear_cache()
        finally:
            self.unlock_page(page)

    @deprecate_arg('summary', 'reason')
    @deprecated('delete()', since='20210330')
    def deletepage(self, page, reason: str):
        """Delete page from the wiki. Requires appropriate privilege level.

        :see: https://www.mediawiki.org/wiki/API:Delete
        Page to be deleted can be given either as Page object or as pageid.

        :param page: Page to be deleted or its pageid.
        :type page: :py:obj:`pywikibot.page.BasePage` or, for pageid,
            int or str
        :param reason: Deletion reason.
        :raises TypeError, ValueError: page has wrong type/value.
        """
        self.delete(page, reason)

    @deprecated('delete() with oldimage keyword parameter', since='20210330')
    def deleteoldimage(self, page, oldimage: str, reason: str):
        """Delete a specific version of a file. Requires appropriate privileges.

        :see: https://www.mediawiki.org/wiki/API:Delete
        The oldimage identifier for the specific version of the image must be
        provided.

        :param page: Page to be deleted or its pageid
        :type page: FilePage or, in case of pageid, int or str
        :param oldimage: oldimageid of the file version to be deleted.
        :param reason: Deletion reason.
        :raises TypeError, ValueError: page has wrong type/value.
        """
        self.delete(page, reason, oldimage=oldimage)

    @need_right('undelete')
    def undelete(self, page, reason: str, *, revisions=None, fileids=None):
        """Undelete page from the wiki. Requires appropriate privilege level.

        :see: https://www.mediawiki.org/wiki/API:Undelete

        *Renamed in version 6.1.*

        *New in version 6.1:* *fileids* parameter was added.

        *Changed in verson 6.1:* keyword argument required for *revisions*.

        :param page: Page to be deleted.
        :type page: pywikibot.BasePage
        :param reason: Undeletion reason.
        :param revisions: List of timestamps to restore.
            If None, restores all revisions.
        :type revisions: list
        :param fileids: List of fileids to restore.
        :type fileids: list
        """
        token = self.tokens['delete']
        params = {
            'action': 'undelete',
            'title': page,
            'reason': reason,
            'token': token,
            'timestamps': revisions,
            'fileids': fileids,
        }

        req = self._simple_request(**params)
        self.lock_page(page)
        try:
            req.submit()
        except APIError as err:
            errdata = {
                'site': self,
                'title': page.title(with_section=False),
                'user': self.user(),
            }
            if err.code in self._dl_errors:
                raise Error(
                    self._dl_errors[err.code].format_map(errdata)
                ) from None
            pywikibot.debug('undelete: Unexpected error code {!r} received.'
                            .format(err.code),
                            _logger)
            raise
        finally:
            self.unlock_page(page)

    @deprecate_arg('summary', 'reason')
    @deprecated('undelete()', since='20210330')
    def undelete_page(self, page, reason: str, revisions=None):
        """DEPRECATED. Undelete page from the wiki.

        :see: https://www.mediawiki.org/wiki/API:Undelete

        :param page: Page to be deleted.
        :type page: pywikibot.BasePage
        :param revisions: List of timestamps to restore.
            If None, restores all revisions.
        :type revisions: list
        :param reason: Undeletion reason.
        """
        self.undelete(page, reason, revisions=revisions)

    @deprecated('undelete() with fileids parameter', since='20210330')
    def undelete_file_versions(self, page, reason: str, fileids=None):
        """DEPRECATED. Undelete page from the wiki.

        :see: https://www.mediawiki.org/wiki/API:Undelete

        :param page: Page to be deleted.
        :type page: pywikibot.BasePage
        :param reason: Undeletion reason.
        :param fileids: List of fileids to restore.
        :type fileids: list
        """
        self.undelete(page, reason, fileids=fileids)

    _protect_errors = {
        'noapiwrite': 'API editing not enabled on {site} wiki',
        'writeapidenied': 'User {user} not allowed to edit through the API',
        'permissiondenied':
            'User {user} not authorized to protect pages on {site} wiki.',
        'cantedit':
            "User {user} can't protect this page because user {user} "
            "can't edit it.",
        'protect-invalidlevel': 'Invalid protection level'
    }

    def protection_types(self):
        """
        Return the protection types available on this site.

        :return: protection types available
        :rtype: set of str instances
        :see: :py:obj:`Siteinfo._get_default()`
        """
        return set(self.siteinfo.get('restrictions')['types'])

    def protection_levels(self):
        """
        Return the protection levels available on this site.

        :return: protection types available
        :rtype: set of str instances
        :see: :py:obj:`Siteinfo._get_default()`
        """
        # implemented in b73b5883d486db0e9278ef16733551f28d9e096d
        return set(self.siteinfo.get('restrictions')['levels'])

    @need_right('protect')
    @deprecate_arg('summary', 'reason')
    def protect(self, page, protections: dict,
                reason: str, expiry=None, **kwargs):
        """(Un)protect a wiki page. Requires administrator status.

        :see: https://www.mediawiki.org/wiki/API:Protect

        :param protections: A dict mapping type of protection to protection
            level of that type. Valid restriction types are 'edit', 'create',
            'move' and 'upload'. Valid restriction levels are '' (equivalent
            to 'none' or 'all'), 'autoconfirmed', and 'sysop'.
            If None is given, however, that protection will be skipped.
        :param reason: Reason for the action
        :param expiry: When the block should expire. This expiry will be
            applied to all protections. If None, 'infinite', 'indefinite',
            'never', or '' is given, there is no expiry.
        :type expiry: pywikibot.Timestamp, string in GNU timestamp format
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
        except APIError as err:
            errdata = {
                'site': self,
                'user': self.user(),
            }
            if err.code in self._protect_errors:
                raise Error(
                    self._protect_errors[err.code].format_map(errdata)
                ) from None
            pywikibot.debug("protect: Unexpected error code '{}' received."
                            .format(err.code),
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

    @need_right('block')
    def blockuser(self, user, expiry, reason: str, anononly=True,
                  nocreate=True, autoblock=True, noemail=False,
                  reblock=False, allowusertalk=False):
        """
        Block a user for certain amount of time and for a certain reason.

        :see: https://www.mediawiki.org/wiki/API:Block

        :param user: The username/IP to be blocked without a namespace.
        :type user: :py:obj:`pywikibot.User`
        :param expiry: The length or date/time when the block expires. If
            'never', 'infinite', 'indefinite' it never does. If the value is
            given as a str it's parsed by php's strtotime function:

                https://www.php.net/manual/en/function.strtotime.php

            The relative format is described there:

                https://www.php.net/manual/en/datetime.formats.relative.php

            It is recommended to not use a str if possible to be
            independent of the API.
        :type expiry: Timestamp/datetime (absolute),
            str (relative/absolute) or False ('never')
        :param reason: The reason for the block.
        :param anononly: Disable anonymous edits for this IP.
        :type anononly: boolean
        :param nocreate: Prevent account creation.
        :type nocreate: boolean
        :param autoblock: Automatically block the last used IP address and all
            subsequent IP addresses from which this account logs in.
        :type autoblock: boolean
        :param noemail: Prevent user from sending email through the wiki.
        :type noemail: boolean
        :param reblock: If the user is already blocked, overwrite the existing
            block.
        :type reblock: boolean
        :param allowusertalk: Whether the user can edit their talk page while
            blocked.
        :type allowusertalk: boolean
        :return: The data retrieved from the API request.
        :rtype: dict
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

        :see: https://www.mediawiki.org/wiki/API:Block

        :param user: The username/IP without a namespace.
        :type user: :py:obj:`pywikibot.User`
        :param reason: Reason for the unblock.
        """
        req = self._simple_request(action='unblock',
                                   user=user.username,
                                   token=self.tokens['block'],
                                   reason=reason)

        data = req.submit()
        return data

    @need_right('editmywatchlist')
    def watch(self, pages, unwatch: bool = False) -> bool:
        """Add or remove pages from watchlist.

        :see: https://www.mediawiki.org/wiki/API:Watch

        :param pages: A single page or a sequence of pages.
        :type pages: A page object, a page-title string, or sequence of them.
            Also accepts a single pipe-separated string like 'title1|title2'.
        :param unwatch: If True, remove pages from watchlist;
            if False add them (default).
        :return: True if API returned expected response; False otherwise
        :raises KeyError: 'watch' isn't in API response
        """
        parameters = {
            'action': 'watch',
            'titles': pages,
            'token': self.tokens['watch'],
            'unwatch': unwatch,
        }
        req = self._simple_request(**parameters)
        results = req.submit()
        unwatch = 'unwatched' if unwatch else 'watched'
        return all(unwatch in r for r in results['watch'])

    @need_right('purge')
    def purgepages(self, pages, forcelinkupdate: bool = False,
                   forcerecursivelinkupdate: bool = False,
                   converttitles: bool = False, redirects: bool = False
                   ) -> bool:
        """
        Purge the server's cache for one or multiple pages.

        :param pages: list of Page objects
        :param redirects: Automatically resolve redirects.
        :type redirects: bool
        :param converttitles: Convert titles to other variants if necessary.
            Only works if the wiki's content language supports variant
            conversion.
        :param forcelinkupdate: Update the links tables.
        :param forcerecursivelinkupdate: Update the links table, and update the
            links tables for any page that uses this page as a template.
        :return: True if API returned expected response; False otherwise
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
                'purgepages: Unexpected API response:\n{}'.format(result))
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
        except APIError as error:
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

        :see: https://www.mediawiki.org/wiki/API:Stashimageinfo
        """
        props = props or False
        req = self._simple_request(
            action='query', prop='stashimageinfo', siifilekey=file_key,
            siiprop=props)
        return req.submit()['query']['stashimageinfo'][0]

    @deprecate_arg('imagepage', 'filepage')
    @need_right('upload')
    def upload(self, filepage, *,
               source_filename: Optional[str] = None,
               source_url: Optional[str] = None,
               comment: Optional[str] = None,
               text: Optional[str] = None,
               watch: bool = False,
               ignore_warnings=False,
               chunk_size: int = 0,
               asynchronous: bool = False,
               _file_key: Optional[str] = None,
               _offset: Union[bool, int] = 0,
               _verify_stash: Optional[bool] = None,
               report_success: Optional[bool] = None) -> bool:
        """
        Upload a file to the wiki.

        :see: https://www.mediawiki.org/wiki/API:Upload

        Either source_filename or source_url, but not both, must be provided.

        *Changed in version 6.0:* keyword arguments required for all
        parameters except *filepage*.

        *Changed in version 6.2:* asynchronous upload is used if
        *asynchronous* parameter is set.

        :param filepage: a FilePage object from which the wiki-name of the
            file will be obtained.
        :param source_filename: path to the file to be uploaded
        :param source_url: URL of the file to be uploaded
        :param comment: Edit summary; if this is not provided, then
            filepage.text will be used. An empty summary is not permitted.
            This may also serve as the initial page text (see below).
        :param text: Initial page text; if this is not set, then
            filepage.text will be used, or comment.
        :param watch: If true, add filepage to the bot user's watchlist
        :param ignore_warnings: It may be a static boolean, a callable
            returning a boolean or an iterable. The callable gets a list of
            UploadError instances and the iterable should contain the warning
            codes for which an equivalent callable would return True if all
            UploadError codes are in thet list. If the result is False it'll
            not continue uploading the file and otherwise disable any warning
            and reattempt to upload the file. NOTE: If report_success is True
            or None it'll raise an UploadError exception if the static
            boolean is False.
        :type ignore_warnings: bool or callable or iterable of str
        :param chunk_size: The chunk size in bytes for chunked uploading (see
            https://www.mediawiki.org/wiki/API:Upload#Chunked_uploading).
            It will only upload in chunks, if the chunk size is positive
            but lower than the file size.
        :param asynchronous: Make potentially large file operations
            asynchronous on the server side when possible.
        :param _file_key: Reuses an already uploaded file using the filekey. If
            None (default) it will upload the file.
        :param _offset: When file_key is not None this can be an integer to
            continue a previously canceled chunked upload. If False it treats
            that as a finished upload. If True it requests the stash info from
            the server to determine the offset. By default starts at 0.
        :param _verify_stash: Requests the SHA1 and file size uploaded and
            compares it to the local file. Also verifies that _offset is
            matching the file size if the _offset is an int. If _offset is
            False if verifies that the file size match with the local file. If
            None it'll verifies the stash when a file key and offset is given.
        :param report_success: If the upload was successful it'll print a
            success message and if ignore_warnings is set to False it'll
            raise an UploadError if a warning occurred. If it's None
            (default) it'll be True if ignore_warnings is a bool and False
            otherwise. If it's True or None ignore_warnings must be a bool.
        :return: It returns True if the upload was successful and False
            otherwise.
        """
        def create_warnings_list(response):
            return [
                UploadError(
                    warning,
                    upload_warnings.get(warning, '{msg}').format(msg=data),
                    _file_key, response['offset'])
                for warning, data in response['warnings'].items()]

        upload_warnings = {
            # map API warning codes to user error messages
            # {msg} will be replaced by message string from API response
            'duplicate-archive':
                'The file is a duplicate of a deleted file {msg}.',
            'was-deleted': 'The file {msg} was previously deleted.',
            'emptyfile': 'File {msg} is empty.',
            'exists': 'File {msg} already exists.',
            'duplicate': 'Uploaded file is a duplicate of {msg}.',
            'badfilename': 'Target filename is invalid.',
            'filetype-unwanted-type': 'File {msg} type is unwanted type.',
            'exists-normalized': 'File exists with different extension as '
                                 '"{msg}".',
            'bad-prefix': 'Target filename has a bad prefix {msg}.',
            'page-exists':
                'Target filename exists but with a different file {msg}.',

            # API-returned message string will be timestamps, not much use here
            'nochange': 'The upload is an exact duplicate of the current '
                        'version of this file.',
            'duplicateversions': 'The upload is an exact duplicate of older '
                                 'version(s) of this file.',
        }

        # An offset != 0 doesn't make sense without a file key
        assert(_offset == 0 or _file_key is not None)
        # check for required parameters
        if source_filename and source_url:
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
                raise ValueError("File '{}' does not exist."
                                 .format(source_filename))

        if source_filename and _file_key:
            assert offset is False or file_size is not None
            if _verify_stash is None:
                _verify_stash = True
            if (offset is not False and offset is not True
                    and offset > file_size):
                raise ValueError(
                    'For the file key "{}" the offset was set to {} '
                    'while the file is only {} bytes large.'.format(
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
                        'For the file key "{}" the server reported a size '
                        '{} while the file size is {}'
                        .format(_file_key, stash_info['size'], file_size))
            elif offset is not False and offset != stash_info['size']:
                raise ValueError(
                    'For the file key "{}" the server reported a size {} '
                    'while the offset was {}'.format(
                        _file_key, stash_info['size'], offset))

            if _verify_stash:
                # The SHA1 was also requested so calculate and compare it
                assert 'sha1' in stash_info, \
                    'sha1 not in stash info: {}'.format(stash_info)
                sha1 = compute_file_hash(source_filename, bytes_to_read=offset)
                if sha1 != stash_info['sha1']:
                    raise ValueError(
                        'The SHA1 of {} bytes of the stashed "{}" is {} '
                        'while the local file is {}'.format(
                            offset, _file_key, stash_info['sha1'], sha1))

        assert offset is not True
        if _file_key and file_size is None:
            assert offset is False

        if _file_key and offset is False or offset == file_size:
            pywikibot.log('Reused already upload file using '
                          'filekey "{}"'.format(_file_key))
            # TODO: Use sessionkey instead of filekey if necessary
            final_request = self._request(
                parameters={
                    'action': 'upload',
                    'token': token,
                    'filename': file_page_title,
                    'comment': comment,
                    'text': text,
                    'async': asynchronous,
                    'filekey': _file_key
                })

        elif source_filename:
            # TODO: Dummy value to allow also Unicode names, see bug T75661
            mime_filename = 'FAKE-NAME'
            # upload local file
            throttle = True
            filesize = os.path.getsize(source_filename)
            chunked_upload = 0 < chunk_size < filesize
            with open(source_filename, 'rb') as f:
                final_request = self._request(
                    throttle=throttle, parameters={
                        'action': 'upload', 'token': token, 'text': text,
                        'filename': file_page_title, 'comment': comment})
                if chunked_upload:
                    if offset > 0:
                        pywikibot.log('Continuing upload from byte {}'
                                      .format(offset))
                    poll = False
                    while True:

                        if poll:
                            # run a poll; not possible in first iteration
                            assert _file_key
                            req = self._simple_request(
                                action='upload',
                                token=token,
                                filekey=_file_key,
                                checkstatus=True)
                        else:
                            f.seek(offset)
                            chunk = f.read(chunk_size)
                            # workaround (hack) for T132676
                            # append another '\r' so that one is the payload
                            # and the second is used for newline when mangled
                            # by email package.
                            if (len(chunk) < chunk_size
                                    or (offset + len(chunk)) == filesize
                                    and chunk[-1] == b'\r'[0]):
                                chunk += b'\r'

                            mime_params = {
                                'chunk': (chunk,
                                          ('application', 'octet-stream'),
                                          {'filename': mime_filename})
                            }
                            req = self._request(
                                throttle=throttle,
                                mime=mime_params,
                                parameters={
                                    'action': 'upload',
                                    'token': token,
                                    'stash': True,
                                    'filesize': filesize,
                                    'offset': offset,
                                    'filename': file_page_title,
                                    'async': asynchronous,
                                    'ignorewarnings': ignore_all_warnings})

                            if _file_key:
                                req['filekey'] = _file_key

                        try:
                            data = req.submit()['upload']
                            self._uploaddisabled = False
                        except APIError as error:
                            # TODO: catch and process foreseeable errors
                            if error.code == 'uploaddisabled':
                                self._uploaddisabled = True
                            elif error.code == 'stashfailed' \
                                    and 'offset' in error.other:
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
                                        'Old offset: {}; Returned '
                                        'offset: {}; Chunk size: {}'
                                        .format(offset, new_offset,
                                                len(chunk)))
                                    pywikibot.warning('Attempting to correct '
                                                      'automatically from '
                                                      'offset mismatch error.')
                                    offset = new_offset
                                    continue
                            raise error
                        if 'nochange' in data:  # in simulation mode
                            break

                        # Polls may not contain file key in response
                        _file_key = data.get('filekey', _file_key)
                        if data['result'] == 'Warning':
                            assert('warnings' in data
                                   and not ignore_all_warnings)
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
                                            filepage,
                                            source_filename=source_filename,
                                            source_url=source_url,
                                            comment=comment,
                                            text=text,
                                            watch=watch,
                                            ignore_warnings=True,
                                            chunk_size=chunk_size,
                                            _file_key=None,
                                            _offset=0,
                                            report_success=False
                                        )

                                    ignore_warnings = True
                                    ignore_all_warnings = True
                                    offset = data['offset']
                                    continue
                                return False
                            result = data
                            result.setdefault('offset', 0)
                            break

                        if data['result'] == 'Continue':
                            throttle = False
                            if 'offset' in data:
                                new_offset = int(data['offset'])
                                if offset + len(chunk) != new_offset:
                                    pywikibot.log('Old offset: {0}; Returned '
                                                  'offset: {1}; Chunk size: '
                                                  '{2}'.format(offset,
                                                               new_offset,
                                                               len(chunk)))
                                    pywikibot.warning('Unexpected offset.')
                                offset = new_offset
                            else:
                                pywikibot.warning('Offset was not supplied.')
                                offset += len(chunk)
                        elif data['result'] == 'Poll':
                            poll = True
                            pywikibot.log('Waiting for server to '
                                          'assemble chunks.')
                        elif data['result'] == 'Success':  # finished
                            pywikibot.log('Finished uploading last chunk.')
                            final_request['filekey'] = _file_key
                            final_request['async'] = asynchronous
                            break
                        else:
                            raise Error(
                                'Unrecognized result: %s' % data['result'])

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
                    "User '{}' is not authorized to upload by URL on site {}."
                    .format(self.user(), self))
            final_request = self._simple_request(
                action='upload', filename=file_page_title,
                url=source_url, comment=comment, text=text, token=token)

        while True:
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

            if 'result' not in result:
                raise Error('Upload: unrecognized response: {}'.format(result))

            if result['result'] == 'Warning':
                assert 'warnings' in result and not ignore_all_warnings
                if 'filekey' in result:
                    _file_key = result['filekey']
                elif 'sessionkey' in result:
                    # TODO: Probably needs to be reflected in the API call
                    # above
                    _file_key = result['sessionkey']
                    pywikibot.warning('Using sessionkey instead of filekey.')
                else:
                    _file_key = None
                    pywikibot.warning('No filekey defined.')

                if not report_success:
                    result.setdefault('offset', True)
                    if ignore_warnings(create_warnings_list(result)):
                        return self.upload(
                            filepage, source_filename=source_filename,
                            source_url=source_url, comment=comment,
                            text=text, watch=watch, ignore_warnings=True,
                            chunk_size=chunk_size, asynchronous=asynchronous,
                            _file_key=_file_key, _offset=result['offset'],
                            report_success=False)
                    return False

                warn('When ignore_warnings=False in APISite.upload will '
                     'change from raising an UploadWarning into behaving like '
                     'being a callable returning False.',
                     DeprecationWarning, 3)
                if len(result['warnings']) > 1:
                    warn('The upload returned {} warnings: {}'
                         .format(len(result['warnings']),
                                 ', '.join(result['warnings'])),
                         UserWarning, 3)
                warning = list(result['warnings'].keys())[0]
                message = result['warnings'][warning]
                raise UploadError(warning,
                                  upload_warnings[warning]
                                  .format(msg=message),
                                  file_key=_file_key,
                                  offset=result.get('offset', False))

            if result['result'] == 'Poll':
                # Polling is meaningless without a file key
                assert _file_key
                pywikibot.log('Waiting for upload to be published.')
                result = None
                final_request = self._simple_request(
                    action='upload',
                    token=token,
                    filekey=_file_key,
                    checkstatus=True)
                continue

            if result['result'] == 'Success':
                if report_success:
                    pywikibot.output('Upload successful.')
                # If we receive a nochange, that would mean we're in simulation
                # mode, don't attempt to access imageinfo
                if 'nochange' not in result:
                    filepage._load_file_revisions([result['imageinfo']])
                return True

            raise Error('Unrecognized result: %s' % data['result'])

    def get_property_names(self, force: bool = False):
        """
        Get property names for pages_with_property().

        :see: https://www.mediawiki.org/wiki/API:Pagepropnames

        :param force: force to retrieve userinfo ignoring cache
        """
        if force or not hasattr(self, '_property_names'):
            ppngen = self._generator(api.ListGenerator, 'pagepropnames')
            self._property_names = [pn['propname'] for pn in ppngen]
        return self._property_names

    def compare(self, old, diff):
        """
        Corresponding method to the 'action=compare' API action.

        :see: https://www.mediawiki.org/wiki/API:Compare

        See: https://en.wikipedia.org/w/api.php?action=help&modules=compare
        Use pywikibot.diff's html_comparator() method to parse result.
        :param old: starting revision ID, title, Page, or Revision
        :type old: int, str, pywikibot.Page, or pywikibot.Page.Revision
        :param diff: ending revision ID, title, Page, or Revision
        :type diff: int, str, pywikibot.Page, or pywikibot.Page.Revision
        :return: Returns an HTML string of a diff between two revisions.
        :rtype: str
        """
        # check old and diff types
        def get_param(item):
            if isinstance(item, str):
                return 'title', item
            if isinstance(item, pywikibot.Page):
                return 'title', item.title()
            if isinstance(item, int):
                return 'rev', item
            if isinstance(item, pywikibot.page.Revision):
                return 'rev', item.revid
            return None

        old = get_param(old)
        if not old:
            raise TypeError('old parameter is of invalid type')
        diff = get_param(diff)
        if not diff:
            raise TypeError('diff parameter is of invalid type')

        params = {'action': 'compare',
                  'from{}'.format(old[0]): old[1],
                  'to{}'.format(diff[0]): diff[1]}

        req = self._simple_request(**params)
        data = req.submit()
        comparison = data['compare']['*']
        return comparison
