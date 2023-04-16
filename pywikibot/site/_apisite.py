"""Objects representing API interface to MediaWiki site."""
#
# (C) Pywikibot team, 2008-2023
#
# Distributed under the terms of the MIT license.
#
import datetime
import re
import time
import typing
from collections import OrderedDict, defaultdict, namedtuple
from contextlib import suppress
from textwrap import fill
from typing import Any, Iterable, Optional, Type, TypeVar, Union

import pywikibot
from pywikibot import login
from pywikibot.backports import DefaultDict, Dict, List, Match
from pywikibot.backports import OrderedDict as OrderedDictType
from pywikibot.backports import Pattern, Set, Tuple, removesuffix
from pywikibot.comms import http
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
)
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
    TextExtractsMixin,
    ThanksFlowMixin,
    ThanksMixin,
    UrlShortenerMixin,
    WikibaseClientMixin,
)
from pywikibot.site._generators import GeneratorsMixin
from pywikibot.site._interwikimap import _InterwikiMap
from pywikibot.site._namespace import Namespace, NamespaceArgType
from pywikibot.site._siteinfo import Siteinfo
from pywikibot.site._tokenwallet import TokenWallet
from pywikibot.site._upload import Uploader
from pywikibot.tools import (
    MediaWikiVersion,
    cached,
    deprecated,
    issue_deprecation_warning,
    merge_unique_dicts,
    normalize_username,
)


__all__ = ('APISite', )
_mw_msg_cache: DefaultDict[str, Dict[str, str]] = defaultdict(dict)


_CompType = Union[int, str, 'pywikibot.page.Page', 'pywikibot.page.Revision']
_RequestWrapperT = TypeVar('_RequestWrapperT', bound='api._RequestWrapper')


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
    TextExtractsMixin,
    ThanksFlowMixin,
    ThanksMixin,
    UrlShortenerMixin,
    WikibaseClientMixin,
):

    """API interface to MediaWiki site.

    Do not instantiate directly; use :py:obj:`pywikibot.Site` function.
    """

    def __init__(
        self,
        code: str,
        fam: Union[str, 'pywikibot.family.Family', None] = None,
        user: Optional[str] = None
    ) -> None:
        """Initializer."""
        super().__init__(code, fam, user)
        self._globaluserinfo: Dict[Union[int, str], Any] = {}
        self._interwikimap = _InterwikiMap(self)
        self._msgcache: Dict[str, str] = {}
        self._paraminfo = api.ParamInfo(self)
        self._siteinfo = Siteinfo(self)
        self._tokens = TokenWallet(self)
        self._loginstatus = login.LoginStatus.NOT_ATTEMPTED
        with suppress(SiteDefinitionError):
            self.login(cookie_only=True)

    def __getstate__(self) -> Dict[str, Any]:
        """Remove TokenWallet before pickling, for security reasons."""
        state = super().__getstate__()
        del state['_tokens']
        del state['_interwikimap']
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Restore things removed in __getstate__."""
        super().__setstate__(state)
        self._interwikimap = _InterwikiMap(self)
        self._tokens = TokenWallet(self)

    def interwiki(self, prefix: str) -> BaseSite:
        """
        Return the site for a corresponding interwiki prefix.

        :raises pywikibot.exceptions.SiteDefinitionError: if the url given in
            the interwiki table doesn't match any of the existing families.
        :raises KeyError: if the prefix is not an interwiki prefix.
        """
        return self._interwikimap[prefix].site

    def interwiki_prefix(self, site: BaseSite) -> List[str]:
        """
        Return the interwiki prefixes going to that site.

        The interwiki prefixes are ordered first by length (shortest first)
        and then alphabetically. :py:obj:`interwiki(prefix)` is not
        guaranteed to equal ``site`` (i.e. the parameter passed to this
        function).

        :param site: The targeted site, which might be it's own.
        :raises KeyError: if there is no interwiki prefix for that site.
        """
        assert site is not None, 'Site must not be None'
        prefixes = set()
        for url in site._interwiki_urls():
            prefixes.update(self._interwikimap.get_by_url(url))
        if not prefixes:
            raise KeyError(
                f"There is no interwiki prefix to '{site}'")
        return sorted(prefixes, key=lambda p: (len(p), p))

    def local_interwiki(self, prefix: str) -> bool:
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
    def fromDBName(  # noqa: N802
        cls,
        dbname: str,
        site: Optional[BaseSite] = None
    ) -> BaseSite:
        """
        Create a site from a database name using the sitematrix.

        :param dbname: database name
        :param site: Site to load sitematrix from. (Default meta.wikimedia.org)
        :return: site object for the database name
        """
        # TODO this only works for some WMF sites
        if not site:
            site = pywikibot.Site('meta')
        req = site._request(expiry=datetime.timedelta(days=10),
                            parameters={'action': 'sitematrix'})
        data = req.submit()
        for key, val in data['sitematrix'].items():
            if key == 'count':
                continue
            if 'code' in val:
                lang = val['code']
                for m_site in val['site']:
                    if m_site['dbname'] == dbname:
                        if m_site['code'] == 'wiki':
                            m_site['code'] = 'wikipedia'
                        return pywikibot.Site(lang, m_site['code'])
            else:  # key == 'specials'
                for m_site in val:
                    if m_site['dbname'] == dbname:
                        url = m_site['url'] + '/w/index.php'
                        return pywikibot.Site(url=url)
        raise ValueError(f'Cannot parse a site out of {dbname}.')

    def _generator(
        self,
        gen_class: Type[_RequestWrapperT],
        type_arg: Optional[str] = None,
        namespaces: NamespaceArgType = None,
        total: Optional[int] = None,
        **args: Any
    ) -> _RequestWrapperT:
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
        :param total: if not None, limit the generator to yielding this
            many items in total
        :return: iterable with parameters set
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        req_args: Dict[str, Any] = {'site': self}
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
    def _request_class(kwargs: Dict[str, Any]) -> Type[api.Request]:
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

    def _request(self, **kwargs: Any) -> api.Request:
        """Create a request by forwarding all parameters directly."""
        if 'expiry' in kwargs and kwargs['expiry'] is None:
            del kwargs['expiry']

        return self._request_class(kwargs)(site=self, **kwargs)

    @deprecated('simple_request', since='7.1.0')
    def _simple_request(self, **kwargs: Any) -> api.Request:
        """DEPRECATED. Create a request using all kwargs as parameters."""
        return self.simple_request(**kwargs)

    def simple_request(self, **kwargs: Any) -> api.Request:
        """Create a request by defining all kwargs as parameters.

        .. versionchanged:: 7.1
           `_simple_request` becomes a public method
        """
        return self._request_class({'parameters': kwargs}).create_simple(
            self, **kwargs)

    def logged_in(self) -> bool:
        """Verify the bot is logged into the site as the expected user.

        The expected usernames are those provided as the user parameter
        at instantiation.
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

    def is_oauth_token_available(self) -> bool:
        """Check whether OAuth token is set for this site."""
        auth_token = http.get_authentication(self.base_url(''))
        return auth_token is not None and len(auth_token) == 4

    def login(
        self,
        autocreate: bool = False,
        user: Optional[str] = None,
        *,
        cookie_only: bool = False
    ) -> None:
        """Log the user in if not already logged in.

        .. versionchanged:: 8.0.0
           lazy load cookies when logging in. This was dropped in 8.0.4
        .. versionchanged:: 8.0.4
           the *cookie_only* parameter was added and cookies are loaded
           whenever the site is initialized.

        .. seealso:: :api:`Login`

        :param autocreate: if true, allow auto-creation of the account
            using unified login
        :param user: bot user name. Overrides the username set by
            BaseSite initializer parameter or user config setting
        :param cookie_only: Only try to login from cookie but do not
            force to login with username/password settings.

        :raises pywikibot.exceptions.NoUsernameError: Username is not
            recognised by the site.
        """
        # TODO: this should include an assert that loginstatus
        #       is not already IN_PROGRESS, however the
        #       login status may be left 'IN_PROGRESS' because
        #       of exceptions or if the first method of login
        #       (below) is successful. Instead, log the problem,
        #       to be increased to 'warning' level once majority
        #       of issues are resolved.
        if self._loginstatus == login.LoginStatus.IN_PROGRESS:
            pywikibot.log(
                '{!r}.login() called when a previous login was in progress.'
                .format(self))

        # There are several ways that the site may already be
        # logged in, and we do not need to hit the server again.
        # logged_in() is False if _userinfo exists, which means this
        # will have no effect for the invocation from api.py
        if self.logged_in():
            self._loginstatus = login.LoginStatus.AS_USER
            return

        # check whether a login cookie already exists for this user
        # or check user identity when OAuth enabled
        self._loginstatus = login.LoginStatus.IN_PROGRESS
        if user:
            self._username = normalize_username(user)

        # load the password for self.username from cookie file
        http.cookie_jar.load(self.username(), ignore_discard=True)

        try:
            del self.userinfo  # force reload
            if self.userinfo['name'] == self.user():
                self._loginstatus = login.LoginStatus.AS_USER
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
                             'user config file: you have to add in this '
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

        if not cookie_only:
            login_manager = login.ClientLoginManager(site=self,
                                                     user=self.username())
            if login_manager.login(retry=True, autocreate=autocreate):
                self._username = login_manager.username
                del self.userinfo  # force reloading

                # load userinfo
                if self.userinfo['name'] == self.username():
                    self._loginstatus = login.LoginStatus.AS_USER
                    return

                pywikibot.error(
                    f"{self.userinfo['name']} != {self.username()} after "
                    f'{type(self).__name__}.login() and successful '
                    f'{type(login_manager).__name__}.login()')

        self._loginstatus = login.LoginStatus.NOT_LOGGED_IN  # failure

    def _relogin(self) -> None:
        """Force a login sequence without logging out, using the current user.

        This is an internal function which is used to re-login when
        the internal login state does not match the state we receive
        from the site.
        """
        del self.userinfo
        self._loginstatus = login.LoginStatus.NOT_LOGGED_IN
        self.login()

    def logout(self) -> None:
        """
        Logout of the site and load details for the logged out user.

        Also logs out of the global account if linked to the user.

        .. seealso:: :api:`Logout`

        :raises APIError: Logout is not available when OAuth enabled.
        """
        if self.is_oauth_token_available():
            pywikibot.warning('Using OAuth suppresses logout function')

        req_params = {'action': 'logout', 'token': self.tokens['csrf']}
        uirequest = self.simple_request(**req_params)
        uirequest.submit()
        self._loginstatus = login.LoginStatus.NOT_LOGGED_IN

        # Reset tokens and user properties
        del self.userinfo
        self.tokens.clear()
        self._paraminfo = api.ParamInfo(self)

        # Clear also cookies for site's second level domain (T224712)
        api._invalidate_superior_cookies(self.family)

    @property
    def maxlimit(self) -> int:
        """Get the maximum limit of pages to be retrieved.

        .. versionadded:: 7.0
        """
        parameter = self._paraminfo.parameter('query+info', 'prop')
        assert parameter is not None
        if self.logged_in() and self.has_right('apihighlimits'):
            return int(parameter['highlimit'])

        return int(parameter['limit'])  # T78333, T161783

    @property
    def userinfo(self) -> Dict[str, Any]:
        """Retrieve userinfo from site and store in _userinfo attribute.

        To force retrieving userinfo ignoring cache, just delete this
        property.

        **Usage**

        >>> site = pywikibot.Site('test')
        >>> info = site.userinfo
        >>> info['id']  # returns 0 if no ip user
        ... # doctest: +SKIP
        0
        >>> info['name']  # username or ip
        ...
        ... # doctest: +SKIP
        '92.198.174.192'
        >>> info['groups']
        ['*']
        >>> info['rights']  # doctest: +ELLIPSIS
        ['createaccount', 'read', 'edit', 'createpage', 'createtalk', ...]
        >>> info['messages']
        False
        >>> del site.userinfo  # delete userinfo cache
        >>> 'blockinfo' in site.userinfo
        False
        >>> 'anon' in site.userinfo
        True

        **Usefull alternatives to userinfo property**

        - :meth:`has_group` to verify the group membership
        - :meth:`has_right` to verify that the user has a given right
        - :meth:`logged_in` to verify the user is loggend in to a site

        .. seealso:: :api:`Userinfo`
        .. versionchanged:: 8.0
           Use API formatversion 2.

        :return: A dict with the following keys and values:

          - id: user id (int)
          - name: username (if user is logged in)
          - anon: present if user is not logged in
          - groups: list of groups (could be empty)
          - rights: list of rights (could be empty)
          - messages: True if user has a new message on talk page (bool)
          - blockinfo: present if user is blocked (dict)

        """
        if not hasattr(self, '_userinfo'):
            uirequest = self.simple_request(
                action='query',
                meta='userinfo',
                uiprop='blockinfo|hasmsg|groups|rights|ratelimits',
                formatversion=2,
            )
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'userinfo' in uidata['query'], \
                   "API userinfo response lacks 'userinfo' key"
            self._userinfo = uidata['query']['userinfo']
            if self._loginstatus != login.LoginStatus.IN_PROGRESS \
               and ('anon' in self._userinfo or not self._userinfo.get('id')):
                pywikibot.warning('No user is logged in on site {}'
                                  .format(self))
        return self._userinfo

    @userinfo.deleter
    def userinfo(self) -> None:
        """Delete cached userinfo.

        .. versionadded:: 5.5
        """
        if hasattr(self, '_userinfo'):
            del self._userinfo

    def get_globaluserinfo(self,
                           user: Union[str, int, None] = None,
                           force: bool = False) -> Dict[str, Any]:
        """Retrieve globaluserinfo from site and cache it.

        .. versionadded:: 7.0

        :param user: The user name or user ID whose global info is
            retrieved. Defaults to the current user.
        :param force: Whether the cache should be discarded.
        :return: A dict with the following keys and values:

          - id: user id (numeric str)
          - home: dbname of home wiki
          - registration: registration date as Timestamp
          - groups: list of groups (could be empty)
          - rights: list of rights (could be empty)
          - editcount: global editcount

        :raises TypeError: Inappropriate argument type of 'user'
        """
        param: Dict[str, Union[int, str]] = {}
        if user is None:
            user = self.username()
            assert isinstance(user, str)
        elif isinstance(user, str):
            param = {'guiuser': user}
        elif isinstance(user, int):
            param = {'guiid': user}
        else:
            raise TypeError("Inappropriate argument type of 'user' ({})"
                            .format(type(user).__name__))

        if force or user not in self._globaluserinfo:
            param.update(
                action='query',
                meta='globaluserinfo',
                guiprop='groups|rights|editcount',
            )
            uirequest = self.simple_request(**param)
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'globaluserinfo' in uidata['query'], \
                   "API userinfo response lacks 'globaluserinfo' key"
            data = uidata['query']['globaluserinfo']
            if 'missing' not in data:
                ts = data['registration']
                data['registration'] = pywikibot.Timestamp.fromISOformat(ts)
            self._globaluserinfo[user] = data
        return self._globaluserinfo[user]

    @property
    def globaluserinfo(self) -> Dict[str, Any]:
        """Retrieve globaluserinfo of the current user from site.

        To get globaluserinfo for a given user or user ID use
        :meth:`get_globaluserinfo` method instead

        .. versionadded:: 3.0
        """
        return self.get_globaluserinfo()

    @globaluserinfo.deleter
    def globaluserinfo(self) -> None:
        """Delete cached globaluserinfo of current user.

        .. versionadded:: 7.0
        """
        username = self.username()
        assert username is not None
        with suppress(KeyError):
            del self._globaluserinfo[username]

    def is_blocked(self, force: bool = False) -> bool:
        """Return True when logged in user is blocked.

        To check whether a user can perform an action,
        the method has_right should be used.

        .. seealso:: :api:`Userinfo`

        .. versionadded:: 7.0
           The `force` parameter

        :param force: Whether the cache should be discarded.
        """
        if force:
            del self.userinfo
        return 'blockinfo' in self.userinfo

    def is_locked(self,
                  user: Union[str, int, None] = None,
                  force: bool = False) -> bool:
        """Return True when given user is locked globally.

        .. versionadded:: 7.0

        :param user: The user name or user ID. Defaults to the current
            user.
        :param force: Whether the cache should be discarded.
        """
        return 'locked' in self.get_globaluserinfo(user, force)

    def get_searched_namespaces(self, force: bool = False) -> Set[Namespace]:
        """
        Retrieve the default searched namespaces for the user.

        If no user is logged in, it returns the namespaces used by default.
        Otherwise it returns the user preferences. It caches the last result
        and returns it, if the username or login status hasn't changed.

        :param force: Whether the cache should be discarded.
        :return: The namespaces which are searched by default.
        """
        # TODO: Integrate into _userinfo
        if (force or not hasattr(self, '_useroptions')
                or self.user() != self._useroptions['_name']):
            uirequest = self.simple_request(
                action='query',
                meta='userinfo',
                uiprop='options'
            )
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'userinfo' in uidata['query'], \
                   "API userinfo response lacks 'userinfo' key"
            self._useroptions: Dict[str, Any] = uidata['query']['userinfo']['options']  # noqa: E501
            # To determine if user name has changed
            self._useroptions['_name'] = (
                None if 'anon' in uidata['query']['userinfo'] else
                uidata['query']['userinfo']['name'])
        return {ns for ns in self.namespaces.values() if ns.id >= 0
                and self._useroptions[f'searchNs{ns.id}']
                in ['1', True]}

    @property  # type: ignore[misc]
    @deprecated('articlepath', since='7.0.0')
    def article_path(self) -> str:
        """Get the nice article path without $1.

        .. deprecated:: 7.0
           Replaced by :py:meth:`articlepath`
        """
        return self.articlepath[:-2]

    @property
    def articlepath(self) -> str:
        """Get the nice article path with placeholder.

        .. versionadded:: 7.0
           Replaces :py:meth:`article_path`
        """
        # Assert $1 placeholder is present
        path = self.siteinfo['general']['articlepath']
        assert '$1' in path, 'articlepath must contain "$1" placeholder'
        return path.replace('$1', '{}')

    @cached
    def linktrail(self) -> str:
        """Build linktrail regex from siteinfo linktrail.

        Letters that can follow a wikilink and are regarded as part of
        this link. This depends on the linktrail setting in LanguageXx.php

        .. versionadded:: 7.3

        :return: The linktrail regex.
        """
        unresolved_linktrails = {
            'br': '(?:[a-zA-ZàâçéèêîôûäëïöüùñÇÉÂÊÎÔÛÄËÏÖÜÀÈÙÑ]'
                  "|[cC]['’]h|C['’]H)*",
            'ca': "(?:[a-zàèéíòóúç·ïü]|'(?!'))*",
            'kaa': "(?:[a-zıʼ’“»]|'(?!'))*",
        }
        linktrail = self.siteinfo['general']['linktrail']
        if linktrail == '/^()(.*)$/sD':  # empty linktrail
            return ''

        match = re.search(r'\((?:\:\?|\?\:)?\[(?P<pattern>.+?)\]'
                          r'(?P<letters>(\|.)*)\)?\+\)', linktrail)
        if not match:
            with suppress(KeyError):
                return unresolved_linktrails[self.code]
            raise KeyError(
                '"{}": No linktrail pattern extracted from "{}"'
                .format(self.code, linktrail))

        pattern = match['pattern']
        letters = match['letters']

        if r'x{' in pattern:
            pattern = re.sub(r'\\x\{([A-F0-9]{4})\}',
                             lambda match: chr(int(match[1], 16)),
                             pattern)
        if letters:
            pattern += ''.join(letters.split('|'))
        return f'[{pattern}]*'

    @staticmethod
    def assert_valid_iter_params(
        msg_prefix: str,
        start: Union[datetime.datetime, int, str],
        end: Union[datetime.datetime, int, str],
        reverse: bool,
        is_ts: bool = True
    ) -> None:
        """Validate iterating API parameters.

        :param msg_prefix: The calling method name
        :param start: The start value to compare
        :param end: The end value to compare
        :param reverse: The reverse option
        :param is_ts: When comparing timestamps (with is_ts=True) the start
            is usually greater than end. Comparing titles this is vice versa.
        :raises AssertionError: start/end values are not comparabel types or
            are in the wrong order
        """
        if not (isinstance(end, type(start)) or isinstance(start, type(end))):
            raise TypeError(
                'start ({!r}) and end ({!r}) must be comparable'
                .format(start, end)
            )
        if reverse ^ is_ts:
            low, high = end, start
            order = 'follow'
        else:
            low, high = start, end
            order = 'precede'
        msg = ('{method}: "start" must {order} "end" '
               'with reverse={reverse} and is_ts={is_ts} '
               'but "start" is "{start}" and "end" is "{end}".')
        assert low < high, fill(msg.format(  # type: ignore[operator]
            method=msg_prefix,
            order=order,
            start=start,
            end=end,
            reverse=reverse,
            is_ts=is_ts))

    def has_right(self, right: str) -> bool:
        """Return true if and only if the user has a specific right.

        Possible values of 'right' may vary depending on wiki settings.

        .. seealso:: :api:`Userinfo`

        :param right: a specific right to be validated
        """
        return right.lower() in self.userinfo['rights']

    def has_group(self, group: str) -> bool:
        """Return true if and only if the user is a member of specified group.

        Possible values of 'group' may vary depending on wiki settings,
        but will usually include bot.

        .. seealso:: :api:`Userinfo`
        """
        return group.lower() in self.userinfo['groups']

    @deprecated("userinfo['messages']", since='8.0.0')
    def messages(self) -> bool:
        """Return true if the user has new messages, and false otherwise.

        .. deprecated:: 8.0
           Replaced by :attr:`userinfo['messages']<userinfo>`.
        """
        return self.userinfo['messages']

    def mediawiki_messages(
        self,
        keys: Iterable[str],
        lang: Optional[str] = None
    ) -> OrderedDictType[str, str]:
        """Fetch the text of a set of MediaWiki messages.

        The returned dict uses each key to store the associated message.

        .. seealso:: :api:`Allmessages`

        :param keys: MediaWiki messages to fetch
        :param lang: a language code, default is self.lang
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

    def mediawiki_message(
        self,
        key: str,
        lang: Optional[str] = None
    ) -> str:
        """Fetch the text for a MediaWiki message.

        :param key: name of MediaWiki message
        :param lang: a language code, default is self.lang
        """
        return self.mediawiki_messages([key], lang=lang)[key]

    def has_mediawiki_message(
        self,
        key: str,
        lang: Optional[str] = None
    ) -> bool:
        """Determine if the site defines a MediaWiki message.

        :param key: name of MediaWiki message
        :param lang: a language code, default is self.lang
        """
        return self.has_all_mediawiki_messages([key], lang=lang)

    def has_all_mediawiki_messages(
        self,
        keys: Iterable[str],
        lang: Optional[str] = None
    ) -> bool:
        """Confirm that the site defines a set of MediaWiki messages.

        :param keys: names of MediaWiki messages
        :param lang: a language code, default is self.lang
        """
        try:
            self.mediawiki_messages(keys, lang=lang)
        except KeyError:
            return False
        return True

    @property
    def months_names(self) -> List[Tuple[str, str]]:
        """Obtain month names from the site messages.

        The list is zero-indexed, ordered by month in calendar, and should
        be in the original site language.

        :return: list of tuples (month name, abbreviation)
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

        self._months_names: List[Tuple[str, str]] = []
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
                f'MediaWiki messages missing: {needed_mw_messages}')

        args = list(args)
        concat = msgs['and'] + msgs['word-separator']
        return msgs['comma-separator'].join(
            args[:-2] + [concat.join(args[-2:])])

    def expand_text(
        self,
        text: str,
        title: Optional[str] = None,
        includecomments: Optional[bool] = None
    ) -> str:
        """Parse the given text for preprocessing and rendering.

        e.g expand templates and strip comments if includecomments
        parameter is not True. Keeps text inside
        <nowiki></nowiki> tags unchanges etc. Can be used to parse
        magic parser words like {{CURRENTTIMESTAMP}}.

        :param text: text to be expanded
        :param title: page title without section
        :param includecomments: if True do not strip comments
        """
        if not isinstance(text, str):
            raise ValueError('text must be a string')

        if not text:
            return ''

        req = self.simple_request(action='expandtemplates',
                                  text=text, prop='wikitext')
        if title is not None:
            req['title'] = title
        if includecomments is True:
            req['includecomments'] = ''

        return req.submit()['expandtemplates']['wikitext']

    def getcurrenttimestamp(self) -> str:
        """
        Return the server time as a MediaWiki timestamp string.

        It calls :py:obj:`server_time` first so it queries the server to
        get the current server time.

        :return: the server time (as 'yyyymmddhhmmss')
        """
        return self.server_time().totimestampformat()

    def server_time(self) -> 'pywikibot.Timestamp':
        """
        Return a Timestamp object representing the current server time.

        It uses the 'time' property of the siteinfo 'general'. It'll force a
        reload before returning the time.

        :return: the current server time
        """
        return pywikibot.Timestamp.fromISOformat(
            self.siteinfo.get('time', expiry=True))

    def getmagicwords(self, word: str) -> List[str]:
        """Return list of localized "word" magic words for the site."""
        if not hasattr(self, '_magicwords'):
            magicwords = self.siteinfo.get('magicwords', cache=False)
            self._magicwords = {item['name']: item['aliases']
                                for item in magicwords}

        if word in self._magicwords:
            return self._magicwords[word]
        return [word]

    def redirect(self) -> str:
        """Return the localized #REDIRECT keyword."""
        # return the magic word without the preceding '#' character
        return self.getmagicwords('redirect')[0].lstrip('#')

    @deprecated('redirect_regex', since='5.5.0')
    def redirectRegex(self) -> Pattern[str]:  # noqa: N802
        """Return a compiled regular expression matching on redirect pages."""
        return self.redirect_regex

    @property
    def redirect_regex(self) -> Pattern[str]:
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

    def pagenamecodes(self) -> List[str]:
        """Return list of localized PAGENAME tags for the site."""
        return self.getmagicwords('pagename')

    def pagename2codes(self) -> List[str]:
        """Return list of localized PAGENAMEE tags for the site."""
        return self.getmagicwords('pagenamee')

    def _build_namespaces(self) -> Dict[int, Namespace]:
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

    def has_extension(self, name: str) -> bool:
        """Determine whether extension `name` is loaded.

        :param name: The extension to check for, case sensitive
        :return: If the extension is loaded
        """
        return any('name' in ext and ext['name'] == name
                   for ext in self.siteinfo['extensions'])

    @property
    def siteinfo(self) -> Siteinfo:
        """Site information dict."""
        return self._siteinfo

    def dbName(self) -> str:  # noqa: N802
        """Return this site's internal id."""
        return self.siteinfo['wikiid']

    @property
    def lang(self) -> str:
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

        if MediaWikiVersion(version) < '1.27':
            raise RuntimeError(
                'Pywikibot "{}" does not support MediaWiki "{}".\n'
                'Use Pywikibot prior to "8.0" branch instead.'
                .format(pywikibot.__version__, version))
        return version

    @property
    def mw_version(self) -> MediaWikiVersion:
        """Return self.version() as a MediaWikiVersion object.

        Cache the result for 24 hours.
        """
        mw_ver, cache_time = getattr(self, '_mw_version_time', (None, None))
        if (
            mw_ver is None
            or cache_time is None
            or time.time() - cache_time > 60 * 60 * 24
        ):
            mw_ver = MediaWikiVersion(self.version())
            self._mw_version_time = mw_ver, time.time()
        return mw_ver

    @property
    def has_image_repository(self) -> bool:
        """Return True if site has a shared image repository like Commons."""
        code, fam = self.shared_image_repository()
        return bool(code or fam)

    @property
    def has_data_repository(self) -> bool:
        """Return True if site has a shared data repository like Wikidata."""
        return self.data_repository() is not None

    def image_repository(self) -> Optional[BaseSite]:
        """Return Site object for image repository e.g. commons."""
        code, fam = self.shared_image_repository()
        if bool(code or fam):
            return pywikibot.Site(code, fam, self.username())

        return None

    def data_repository(self) -> Optional['pywikibot.site.DataSite']:
        """
        Return the data repository connected to this site.

        :return: The data repository if one is connected or None otherwise.
        """
        def handle_warning(
            mod: str,
            warning: str
        ) -> Union[Match[str], bool, None]:
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

    def is_image_repository(self) -> bool:
        """Return True if Site object is the image repository."""
        return self is self.image_repository()

    def is_data_repository(self) -> bool:
        """Return True if its data repository is itself."""
        # fixme: this was an identity check
        return self == self.data_repository()

    def page_from_repository(
        self,
        item: str
    ) -> Optional['pywikibot.page.Page']:
        """
        Return a Page for this site object specified by Wikibase item.

        Usage:

        >>> site = pywikibot.Site('wikipedia:zh')
        >>> page = site.page_from_repository('Q131303')
        >>> page.title()
        'Hello World'

        This method is able to upcast categories:

        >>> site = pywikibot.Site('commons')
        >>> page = site.page_from_repository('Q131303')
        >>> page.title()
        'Category:Hello World'
        >>> page
        Category('Category:Hello World')

        It also works for wikibase repositories:

        >>> site = pywikibot.Site('wikidata')
        >>> page = site.page_from_repository('Q5296')
        >>> page.title()
        'Wikidata:Main Page'

        If no page exists for a given site, None is returned:

        >>> site = pywikibot.Site('wikidata')
        >>> page = site.page_from_repository('Q131303')
        >>> page is None
        True

        .. versionchanged:: 7.7
           No longer raise NotimplementedError if used with a Wikibase
           site.

        :param item: id number of item, "Q###",
        :return: Page, or Category object given by Wikibase item number
            for this site object.

        :raises pywikibot.exceptions.UnknownExtensionError: site has no
            Wikibase extension
        """
        if not self.has_data_repository:
            raise UnknownExtensionError(
                f'Wikibase is not implemented for {self}.')

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

    def nice_get_address(self, title: str) -> str:
        """Return shorter URL path to retrieve page titled 'title'."""
        # 'title' is expected to be URL-encoded already
        return self.siteinfo['articlepath'].replace('$1', title)

    def namespace(self, num: int, all: bool = False) -> Union[str, Namespace]:
        """Return string containing local name of namespace 'num'.

        If optional argument 'all' is true, return all recognized
        values for this namespace.

        :param num: Namespace constant.
        :param all: If True return a Namespace object. Otherwise
            return the namespace name.
        :return: local name or Namespace object
        """
        if all:
            return self.namespaces[num]
        return self.namespaces[num][0]

    def _update_page(
        self,
        page: 'pywikibot.page.BasePage',
        query: api.PropertyGenerator,
        verify_imageinfo: bool = False
    ) -> None:
        """Update page attributes.

        :param page: page object to be updated
        :param query: API query generator
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

    def loadpageinfo(
        self,
        page: 'pywikibot.page.BasePage',
        preload: bool = False
    ) -> None:
        """Load page info from api and store in page attributes.

        .. seealso:: :api:`Info`
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

    def loadpageprops(self, page: 'pywikibot.page.BasePage') -> None:
        """Load page props for the given page."""
        title = page.title(with_section=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg='pageprops',
                                titles=title.encode(self.encoding()),
                                )
        self._update_page(page, query)

    def loadimageinfo(
        self,
        page: 'pywikibot.page.FilePage',
        history: bool = False,
        url_width: Optional[int] = None,
        url_height: Optional[int] = None,
        url_param: Optional[str] = None
    ) -> None:
        """Load image info from api and save in page attributes.

        Parameters correspond to iiprops in:
        [1] :api:`Imageinfo`

        Parameters validation and error handling left to the API call.

        :param history: if true, return the image's version history
        :param url_width: see iiurlwidth in [1]
        :param url_height: see iiurlheigth in [1]
        :param url_param: see iiurlparam in [1]

        """
        args = {'titles': page.title(with_section=False),
                'iiurlwidth': url_width,
                'iiurlheight': url_height,
                'iiurlparam': url_param,
                'iiprop': ['timestamp', 'user', 'comment', 'url', 'size',
                           'sha1', 'mime', 'metadata', 'archivename']
                }
        if not history:
            args['total'] = 1
        query = self._generator(api.PropertyGenerator,
                                type_arg='imageinfo',
                                **args)
        self._update_page(page, query, verify_imageinfo=True)

    def page_restrictions(
        self,
        page: 'pywikibot.page.BasePage'
    ) -> Dict[str, Tuple[str, str]]:
        """Return a dictionary reflecting page protections.

        **Example:**

        >>> site = pywikibot.Site('wikipedia:test')
        >>> page = pywikibot.Page(site, 'Main Page')
        >>> site.page_restrictions(page)
        {'edit': ('sysop', 'infinity'), 'move': ('sysop', 'infinity')}

        .. seealso:: :meth:`page.BasePage.protection` (should be preferred)
        """
        if not hasattr(page, '_protection'):
            self.loadpageinfo(page)
        return page._protection

    def page_can_be_edited(
        self,
        page: 'pywikibot.page.BasePage',
        action: str = 'edit'
    ) -> bool:
        """Determine if the page can be modified.

        Return True if the bot has the permission of needed restriction level
        for the given action type.

        .. seealso:: :meth:`page.BasePage.has_permission` (should be preferred)

        :param page: a pywikibot.page.BasePage object
        :param action: a valid restriction type like 'edit', 'move'

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
        return self.has_right(prot_rights.get(restriction, restriction))

    def page_isredirect(self, page: 'pywikibot.page.BasePage') -> bool:
        """Return True if and only if page is a redirect."""
        if not hasattr(page, '_isredir'):
            page._isredir = False  # bug T56684
            self.loadpageinfo(page)
        return page._isredir

    def getredirtarget(
        self,
        page: 'pywikibot.page.BasePage'
    ) -> 'pywikibot.page.Page':
        """
        Return page object for the redirect target of page.

        :param page: page to search redirects for
        :return: redirect target of page

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
        query = self.simple_request(
            action='query',
            prop='info',
            titles=title,
            redirects=True
        )
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

    @deprecated(since='8.0.0')
    def validate_tokens(self, types: List[str]) -> List[str]:
        """Validate if requested tokens are acceptable.

        Valid tokens may depend on mw version.

        .. deprecated:: 8.0
        """
        data = self._paraminfo.parameter('query+tokens', 'type')
        assert data is not None
        return [token for token in types if token in data['type']]

    def get_tokens(self, types: List[str], *args, **kwargs) -> Dict[str, str]:
        r"""Preload one or multiple tokens.

        **Usage**

        >>> site = pywikibot.Site()
        >>> tokens = site.get_tokens([])  # get all tokens
        >>> list(tokens.keys())  # result depends on user
        ['createaccount', 'login']
        >>> tokens = site.get_tokens(['csrf', 'patrol'])
        >>> list(tokens.keys())  # doctest: +SKIP
        ['csrf', 'patrol']
        >>> token = site.get_tokens(['csrf']).get('csrf')  # get a single token
        >>> token  # doctest: +SKIP
        'a9f...0a0+\\'
        >>> token = site.get_tokens(['unknown'])  # try an invalid token
        ... # doctest: +SKIP
        ... # invalid token names shows a warnig and the key is not in result
        ...
        WARNING: API warning (tokens) of unknown format:
        ... {'warnings': 'Unrecognized value for parameter "type": foo'}
        {}

        You should not call this method directly, especially if you only
        need a specific token. Use :attr:`tokens` property instead.

        .. versionchanged:: 8.0
           ``all`` parameter is deprecated. Use an empty list for
           ``types`` instead.
        .. note:: ``args`` and ``kwargs`` are not used for deprecation
           warning only.
        .. seealso:: :api:`Tokens`

        :param types: the types of token (e.g., "csrf", "login", "patrol").
            If the list is empty all available tokens are loaded. See
            API documentation for full list of types.
        :return: a dict with retrieved valid tokens.
        """
        # deprecate 'all' parameter
        if args or kwargs:
            issue_deprecation_warning("'all' parameter",
                                      "empty list for 'types' parameter",
                                      since='8.0.0')
            load_all = kwargs.get('all', args[0] if args else False)
        else:
            load_all = False

        if not types or load_all is not False:
            pdata = self._paraminfo.parameter('query+tokens', 'type')
            assert pdata is not None
            types = pdata['type']

        req = self.simple_request(action='query', meta='tokens',
                                  type=types, formatversion=2)

        data = req.submit()
        data = data.get('query', data)

        user_tokens = {}
        if 'tokens' in data and data['tokens']:
            user_tokens = {removesuffix(key, 'token'): val
                           for key, val in data['tokens'].items()
                           if val != '+\\'}

        return user_tokens

    @property
    def tokens(self) -> 'pywikibot.site._tokenwallet.TokenWallet':
        r"""Return the TokenWallet collection.

        :class:`TokenWallet<pywikibot.site._tokenwallet.TokenWallet>`
        collection holds all available tokens. The tokens are loaded
        via :meth:`get_tokens` method with the first token request and
        is retained until the TokenWallet is cleared.

        **Usage:**

        >>> site = pywikibot.Site()
        >>> token = site.tokens['csrf']  # doctest: +SKIP
        >>> token  # doctest: +SKIP
        'df8...9e6+\\'
        >>> 'csrf' in site.tokens  # doctest: +SKIP
        ... # Check whether the token exists
        True
        >>> 'invalid' in site.tokens  # doctest: +SKIP
        False
        >>> token = site.tokens['invalid']  # doctest: +SKIP
        Traceback (most recent call last):
        ...
        KeyError: "Invalid token 'invalid' for user ...
        >>> site.tokens.clear()  # clears the internal cache
        >>> site.tokens['csrf']  # doctest: +SKIP
        ... # get a new token
        '1c8...9d3+\\'
        >>> del site.tokens  # another variant to clear the cache

        .. versionchanged:: 8.0
           ``tokens`` attribute became a property to enable deleter.
        .. warning:: A deprecation warning is shown if the token name is
           outdated, see :api:`Tokens (action)`.
        .. seealso:: :api:`Tokens` for valid token types
        """
        return self._tokens

    @tokens.deleter
    def tokens(self) -> None:
        """Deleter method to clear the TokenWallet collection."""
        self._tokens.clear()

    # TODO: expand support to other parameters of action=parse?
    def get_parsed_page(self, page: 'pywikibot.page.BasePage') -> str:
        """Retrieve parsed text of the page using action=parse.

        .. versionchanged:: 7.1
           raises KeyError instead of AssertionError

        .. seealso::
           - :api:`Parse`
           - :meth:`page.BasePage.get_parsed_page`.
        """
        req = self.simple_request(action='parse', page=page)
        data = req.submit()
        try:
            parsed_text = data['parse']['text']['*']
        except KeyError as e:
            raise KeyError(f'API parse response lacks {e} key')
        return parsed_text

    def getcategoryinfo(self, category: 'pywikibot.page.Category') -> None:
        """Retrieve data on contents of category.

        .. seealso:: :api:`Categoryinfo`
        """
        cititle = category.title(with_section=False)
        ciquery = self._generator(api.PropertyGenerator,
                                  type_arg='categoryinfo',
                                  titles=cititle.encode(self.encoding()))
        self._update_page(category, ciquery)

    def categoryinfo(
        self,
        category: 'pywikibot.page.Category'
    ) -> Dict[str, int]:
        """Retrieve data on contents of category."""
        if not hasattr(category, '_catinfo'):
            self.getcategoryinfo(category)
        if not hasattr(category, '_catinfo'):
            # a category that exists but has no contents returns no API result
            category._catinfo = {'size': 0, 'pages': 0, 'files': 0,
                                 'subcats': 0}
        return category._catinfo

    def isBot(self, username: str) -> bool:  # noqa: N802
        """Return True is username is a bot user."""
        return username in (userdata['name'] for userdata in self.botusers())

    @property
    def logtypes(self) -> Set['str']:
        """Return a set of log types available on current site."""
        data = self._paraminfo.parameter('query+logevents', 'type')
        assert data is not None
        return set(filter(None, data['type']))

    @need_right('deleterevision')
    def deleterevs(
        self,
        targettype: str,
        ids: Union[int, str, List[Union[int, str]]],
        *,
        hide: Union[str, List[str], None] = None,
        show: Union[str, List[str], None] = None,
        reason: str = '',
        target: Union['pywikibot.page.Page', str, None] = None
    ) -> None:
        """Delete or undelete specified page revisions, file versions or logs.

        .. seealso:: :api:`Revisiondelete`

        If more than one target id is provided, the same action is taken for
        all of them.

        .. versionadded:: 6.0

        :param targettype: Type of target. One of "archive", "filearchive",
            "logging", "oldimage", "revision".
        :param ids: Identifiers for the revision, log, file version or archive.
        :param hide: What to delete. Can be "comment", "content", "user" or a
            combination of them in pipe-separate form such as "comment|user".
        :param show: What to undelete. Can be "comment", "content", "user" or
            a combination of them in pipe-separate form such as "comment|user".
        :param reason: Deletion reason.
        :param target: Page object or page title, if required for the type.
        """
        if isinstance(target, pywikibot.Page):
            page = target
            target = page.title()
        elif target:
            page = pywikibot.Page(self, target)

        token = self.tokens['csrf']
        params = {
            'action': 'revisiondelete',
            'token': token,
            'type': targettype,
            'ids': ids,
            'hide': hide,
            'show': show,
            'target': target,
            'reason': reason}

        req = self.simple_request(**params)

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
                            .format(err.code))
            raise
        else:
            if target:
                page.clear_cache()
        finally:
            if target:
                self.unlock_page(page)

    # Catalog of editpage error codes, for use in generating messages.
    # The block at the bottom are page related errors.
    _ep_errors: Dict[str, Union[str, Type[PageSaveRelatedError]]] = {
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
    def editpage(
        self,
        page: 'pywikibot.page.BasePage',
        summary: Optional[str] = None,
        minor: bool = True,
        notminor: bool = False,
        bot: bool = True,
        recreate: bool = True,
        createonly: bool = False,
        nocreate: bool = False,
        watch: Optional[str] = None,
        **kwargs: Any
    ) -> bool:
        """Submit an edit to be saved to the wiki.

        .. seealso:: :api:`Edit`

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

        token = self.tokens['csrf']
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
        req = self.simple_request(**params)

        self.lock_page(page)
        try:
            while True:
                try:
                    result = req.submit()
                    pywikibot.debug(f'editpage response: {result}')
                except APIError as err:
                    if err.code.endswith('anon') and self.logged_in():
                        pywikibot.debug("editpage: received '{}' even though "
                                        'bot is logged in'.format(err.code))
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
                            raise exception(page, info=err.info) from None
                        if issubclass(exception, SpamblacklistError):
                            urls = ', '.join(err.other[err.code]['matches'])
                            raise exception(page, url=urls) from None
                        raise exception(page) from None
                    pywikibot.debug(
                        "editpage: Unexpected error code '{}' received."
                        .format(err.code))
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
                        break

                    if 'spamblacklist' in result['edit']:
                        raise SpamblacklistError(
                            page, result['edit']['spamblacklist']) from None

                    if 'code' in result['edit'] and 'info' in result['edit']:
                        pywikibot.error(
                            'editpage: {}\n{}, '
                            .format(result['edit']['code'],
                                    result['edit']['info']))
                        break

                    pywikibot.error('editpage: unknown failure reason {}'
                                    .format(str(result)))
                    break

                pywikibot.error(
                    "editpage: Unknown result code '{}' received; "
                    'page not saved'.format(result['edit']['result']))
                pywikibot.log(str(result))
                break

        finally:
            self.unlock_page(page)

        return False

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
    def merge_history(
        self,
        source: 'pywikibot.page.BasePage',
        dest: 'pywikibot.page.BasePage',
        timestamp: Optional['pywikibot.Timestamp'] = None,
        reason: Optional[str] = None
    ) -> None:
        """Merge revisions from one page into another.

        .. seealso::

           - :api:`Mergehistory`
           - :meth:`page.BasePage.merge_history` (should be preferred)

        Revisions dating up to the given timestamp in the source will be
        moved into the destination page history. History merge fails if
        the timestamps of source and dest revisions overlap (all source
        revisions must be dated before the earliest dest revision).

        :param source: Source page from which revisions will be merged
        :param dest: Destination page to which revisions will be merged
        :param timestamp: Revisions from this page dating up to this timestamp
            will be merged into the destination page (if not given or False,
            all revisions will be merged)
        :param reason: Optional reason for the history merge
        :raises APIError: unexpected APIError
        :raises Error: expected APIError or unexpected response
        :raises NoPageError: *source* or *dest* does not exist
        :raises PageSaveRelatedError: *source* is equal to *dest*
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
                page=source,
                message='Cannot merge revisions of {page} to itself'
            )

        # Send the merge API request
        token = self.tokens['csrf']
        req = self.simple_request(action='mergehistory', token=token)
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
                            .format(result=result))
        except APIError as err:
            if err.code in self._mh_errors:
                on_error = self._mh_errors[err.code]
                raise Error(on_error.format_map(errdata)) from None

            pywikibot.debug(
                "mergehistory: Unexpected error code '{code}' received"
                .format(code=err.code))
            raise
        finally:
            self.unlock_page(source)
            self.unlock_page(dest)

        if 'mergehistory' not in result:
            pywikibot.error(f'mergehistory: {result}')
            raise Error('mergehistory: unexpected response')

    # catalog of move errors for use in error messages
    _mv_errors: Dict[str, Union[str, OnErrorExc]] = {
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
    def movepage(
        self,
        page: 'pywikibot.page.BasePage',
        newtitle: str,
        summary: str,
        movetalk: bool = True,
        noredirect: bool = False,
        movesubpages: bool = True
    ) -> 'pywikibot.page.Page':
        """Move a Page to a new title.

        .. seealso:: :api:`Move`

        .. versionchanged:: 7.2
           The `movesubpages` parameter was added

        :param page: the Page to be moved (must exist)
        :param newtitle: the new title for the Page
        :param summary: edit summary (required!)
        :param movetalk: if True (default), also move the talk page if possible
        :param noredirect: if True, suppress creation of a redirect from the
            old title to the new one
        :param movesubpages: Rename subpages, if applicable.
        :return: Page object with the new title
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
        token = self.tokens['csrf']
        self.lock_page(page)
        req = self.simple_request(action='move',
                                  noredirect=noredirect,
                                  reason=summary,
                                  movetalk=movetalk,
                                  movesubpages=movesubpages,
                                  token=token,
                                  to=newtitle)
        req['from'] = oldtitle  # "from" is a python keyword
        try:
            result = req.submit()
            pywikibot.debug(f'movepage response: {result}')
        except APIError as err:
            if err.code.endswith('anon') and self.logged_in():
                pywikibot.debug(
                    "movepage: received '{}' even though bot is logged in"
                    .format(err.code))

            if err.code in self._mv_errors:
                on_error = self._mv_errors[err.code]
                if not isinstance(on_error, str):
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
                            .format(err.code))
            raise
        finally:
            self.unlock_page(page)
        if 'move' not in result:
            pywikibot.error(f'movepage: {result}')
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
    def rollbackpage(
        self,
        page: 'pywikibot.page.BasePage',
        **kwargs: Any
    ) -> None:
        """Roll back page to version before last user's edits.

        .. seealso:: :api:`Rollback`

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
        req = self.simple_request(**parameters)
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
                            .format(err.code))
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
    }  # other errors shouldn't occur because of pre-submission checks

    @need_right('delete')
    def delete(
        self,
        page: Union['pywikibot.page.BasePage', int, str],
        reason: str,
        *,
        deletetalk: bool = False,
        oldimage: Optional[str] = None
    ) -> None:
        """Delete a page or a specific old version of a file from the wiki.

        Requires appropriate privileges.

        .. seealso: :api:`Delete`

        Page to be deleted can be given either as Page object or as pageid.
        To delete a specific version of an image the oldimage identifier
        must be provided.

        .. versionadded:: 6.1
           renamed from `deletepage`

        .. versionchanged:: 6.1
           keyword only parameter `oldimage` was added.

        .. versionchanged:: 7.1
           keyword only parameter `deletetalk` was added.

        .. versionchanged:: 8.1
           raises :exc:`exceptions.NoPageError` if page does not exist.

        :param page: Page to be deleted or its pageid.
        :param reason: Deletion reason.
        :param deletetalk: Also delete the talk page, if it exists.
        :param oldimage: oldimage id of the file version to be deleted.
            If a BasePage object is given with page parameter, it has to
            be a FilePage.
        :raises TypeError, ValueError: page has wrong type/value.
        """
        if oldimage and isinstance(page, pywikibot.page.BasePage) \
           and not isinstance(page, pywikibot.FilePage):
            raise TypeError("'page' must be a FilePage not a '{}'"
                            .format(page.__class__.__name__))

        token = self.tokens['csrf']
        params = {
            'action': 'delete',
            'token': token,
            'reason': reason,
            'oldimage': oldimage,
        }

        if isinstance(page, pywikibot.page.BasePage):
            params['title'] = page
            title = page.title(with_section=False)
        else:
            params['pageid'] = int(page)
            title = str(page)

        if deletetalk:
            if self.mw_version < '1.38wmf24':
                pywikibot.warning(
                    f'deletetalk is not available on {self.mw_version}'
                )
            else:
                params['deletetalk'] = deletetalk

        req = self.simple_request(**params)
        self.lock_page(page)
        try:
            req.submit()
        except APIError as err:
            if err.code == 'missingtitle':
                raise NoPageError(page) from None

            errdata = {
                'site': self,
                'title': title,
                'user': self.user(),
            }

            if err.code in self._dl_errors:
                raise Error(
                    self._dl_errors[err.code].format_map(errdata)
                ) from None
            pywikibot.debug('delete: Unexpected error code {!r} received.'
                            .format(err.code))
            raise
        else:
            if isinstance(page, pywikibot.page.BasePage):
                page.clear_cache()
        finally:
            self.unlock_page(page)

    @need_right('undelete')
    def undelete(
        self,
        page: 'pywikibot.page.BasePage',
        reason: str,
        *,
        revisions: Optional[List[str]] = None,
        fileids: Optional[List[Union[int, str]]] = None
    ) -> None:
        """Undelete page from the wiki. Requires appropriate privilege level.

        .. seealso:: :api:`Undelete`

        .. versionadded:: 6.1
           renamed from `undelete_page`

        .. versionchanged:: 6.1
           `fileids` parameter was added,
           keyword argument required for `revisions`.

        :param page: Page to be deleted.
        :param reason: Undeletion reason.
        :param revisions: List of timestamps to restore.
            If None, restores all revisions.
        :param fileids: List of fileids to restore.
        """
        token = self.tokens['csrf']
        params = {
            'action': 'undelete',
            'title': page,
            'reason': reason,
            'token': token,
            'timestamps': revisions,
            'fileids': fileids,
        }

        req = self.simple_request(**params)
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
                            .format(err.code))
            raise
        finally:
            self.unlock_page(page)

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

    def protection_types(self) -> Set[str]:
        """
        Return the protection types available on this site.

        **Example:**

        >>> site = pywikibot.Site('wikipedia:test')
        >>> sorted(site.protection_types())
        ['create', 'edit', 'move', 'upload']

        .. seealso:: :py:obj:`Siteinfo._get_default()`

        :return: protection types available
        """
        return set(self.siteinfo.get('restrictions')['types'])

    @need_version('1.27.3')
    def protection_levels(self) -> Set[str]:
        """
        Return the protection levels available on this site.

        **Example:**

        >>> site = pywikibot.Site('wikipedia:test')
        >>> sorted(site.protection_levels())
        ['', 'autoconfirmed', ... 'sysop', 'templateeditor']

        .. seealso:: :py:obj:`Siteinfo._get_default()`

        :return: protection types available
        """
        return set(self.siteinfo.get('restrictions')['levels'])

    @need_right('protect')
    def protect(
        self,
        page: 'pywikibot.page.BasePage',
        protections: Dict[str, Optional[str]],
        reason: str,
        expiry: Union[datetime.datetime, str, None] = None,
        **kwargs: Any
    ) -> None:
        """(Un)protect a wiki page. Requires *protect* right.

        .. seealso::
           - :api:`Protect`
           - :meth:`protection_types`
           - :meth:`protection_levels`

        :param protections: A dict mapping type of protection to
            protection level of that type. Refer :meth:`protection_types`
            for valid restriction types and :meth:`protection_levels`
            for valid restriction levels. If None is given, however,
            that protection will be skipped.
        :param reason: Reason for the action
        :param expiry: When the block should expire. This expiry will be
            applied to all protections. If ``None``, ``'infinite'``,
            ``'indefinite'``, ``'never'``, or ``''`` is given, there is
            no expiry.
        """
        token = self.tokens['csrf']
        self.lock_page(page)

        protections_list = [ptype + '=' + level
                            for ptype, level in protections.items()
                            if level is not None]
        parameters = merge_unique_dicts(kwargs, action='protect', title=page,
                                        token=token,
                                        protections=protections_list,
                                        reason=reason,
                                        expiry=expiry)

        req = self.simple_request(**parameters)
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
                            .format(err.code))
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

    @need_right('block')
    def blockuser(
        self,
        user: 'pywikibot.page.User',
        expiry: Union[datetime.datetime, str, bool],
        reason: str,
        anononly: bool = True,
        nocreate: bool = True,
        autoblock: bool = True,
        noemail: bool = False,
        reblock: bool = False,
        allowusertalk: bool = False
    ) -> Dict[str, Any]:
        """
        Block a user for certain amount of time and for a certain reason.

        .. seealso:: :api:`Block`

        :param user: The username/IP to be blocked without a namespace.
        :param expiry: The length or date/time when the block expires. If
            'never', 'infinite', 'indefinite' it never does. If the value is
            given as a str it's parsed by php's strtotime function:

                https://www.php.net/manual/en/function.strtotime.php

            The relative format is described there:

                https://www.php.net/manual/en/datetime.formats.relative.php

            It is recommended to not use a str if possible to be
            independent of the API.
        :param reason: The reason for the block.
        :param anononly: Disable anonymous edits for this IP.
        :param nocreate: Prevent account creation.
        :param autoblock: Automatically block the last used IP address and all
            subsequent IP addresses from which this account logs in.
        :param noemail: Prevent user from sending email through the wiki.
        :param reblock: If the user is already blocked, overwrite the existing
            block.
        :param allowusertalk: Whether the user can edit their talk page while
            blocked.
        :return: The data retrieved from the API request.
        """
        token = self.tokens['csrf']
        if expiry is False:
            expiry = 'never'
        req = self.simple_request(action='block', user=user.username,
                                  expiry=expiry, reason=reason, token=token,
                                  anononly=anononly, nocreate=nocreate,
                                  autoblock=autoblock, noemail=noemail,
                                  reblock=reblock, allowusertalk=allowusertalk)
        return req.submit()

    @need_right('unblock')
    def unblockuser(
        self,
        user: 'pywikibot.page.User',
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remove the block for the user.

        .. seealso:: :api:`Block`

        :param user: The username/IP without a namespace.
        :param reason: Reason for the unblock.
        """
        req = self.simple_request(action='unblock',
                                  user=user.username,
                                  token=self.tokens['csrf'],
                                  reason=reason)
        return req.submit()

    @need_right('editmywatchlist')
    def watch(
        self,
        pages: Union['pywikibot.page.BasePage',
                     str,
                     List[Union['pywikibot.page.BasePage', str]]
                     ],
        unwatch: bool = False
    ) -> bool:
        """Add or remove pages from watchlist.

        .. seealso:: :api:`Watch`

        :param pages: A single page or a sequence of pages.
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
        req = self.simple_request(**parameters)
        results = req.submit()
        unwatch_s = 'unwatched' if unwatch else 'watched'
        return all(unwatch_s in r for r in results['watch'])

    @need_right('purge')
    def purgepages(
        self,
        pages: List['pywikibot.page.BasePage'],
        forcelinkupdate: bool = False,
        forcerecursivelinkupdate: bool = False,
        converttitles: bool = False,
        redirects: bool = False
    ) -> bool:
        """
        Purge the server's cache for one or multiple pages.

        :param pages: list of Page objects
        :param redirects: Automatically resolve redirects.
        :param converttitles: Convert titles to other variants if necessary.
            Only works if the wiki's content language supports variant
            conversion.
        :param forcelinkupdate: Update the links tables.
        :param forcerecursivelinkupdate: Update the links table, and update the
            links tables for any page that uses this page as a template.
        :return: True if API returned expected response; False otherwise
        """
        req = self.simple_request(action='purge', titles=list(set(pages)))
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
                f'purgepages: Unexpected API response:\n{result}')
            return False
        if not all('purged' in page for page in result):
            return False
        if forcelinkupdate or forcerecursivelinkupdate:
            return all('linkupdate' in page for page in result)
        return True

    @need_right('edit')
    def is_uploaddisabled(self) -> bool:
        """Return True if upload is disabled on site.

        **Example:**

        >>> site = pywikibot.Site('commons')
        >>> site.is_uploaddisabled()
        False
        >>> site = pywikibot.Site('wikidata')
        >>> site.is_uploaddisabled()
        True
        """
        return not self.siteinfo.get('general')['uploadsenabled']

    def stash_info(
        self,
        file_key: str,
        props: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get the stash info for a given file key.

        .. seealso:: :api:`Stashimageinfo`
        """
        props = props or None
        req = self.simple_request(action='query', prop='stashimageinfo',
                                  siifilekey=file_key, siiprop=props)
        return req.submit()['query']['stashimageinfo'][0]

    @need_right('upload')
    def upload(
        self,
        filepage: 'pywikibot.page.FilePage',
        **kwargs: Any
    ) -> bool:
        """Upload a file to the wiki.

        .. seealso:: :api:`Upload`

        Either source_filename or source_url, but not both, must be provided.

        .. versionchanged:: 6.0
           keyword arguments required for all parameters except `filepage`

        .. versionchanged:: 6.2:
           asynchronous upload is used if `asynchronous` parameter is set.

        For keyword arguments refer :class:`pywikibot.site._upload.Uploader`

        :param filepage: a FilePage object from which the wiki-name of the
            file will be obtained.
        :return: It returns True if the upload was successful and False
            otherwise.
        """
        if self.is_uploaddisabled():
            pywikibot.error(
                f'Upload error: Local file uploads are disabled on {self}.')
            return False

        return Uploader(self, filepage, **kwargs).upload()

    def get_property_names(self, force: bool = False) -> List[str]:
        """
        Get property names for pages_with_property().

        .. seealso:: :api:`Pagepropnames`

        :param force: force to retrieve userinfo ignoring cache
        """
        if force or not hasattr(self, '_property_names'):
            ppngen = self._generator(api.ListGenerator, 'pagepropnames')
            self._property_names = [pn['propname'] for pn in ppngen]
        return self._property_names

    def compare(self, old: _CompType, diff: _CompType) -> str:
        """
        Corresponding method to the 'action=compare' API action.

        .. seealso: :api:`Compare`

        See: https://en.wikipedia.org/w/api.php?action=help&modules=compare
        Use pywikibot.diff's html_comparator() method to parse result.
        :param old: starting revision ID, title, Page, or Revision
        :param diff: ending revision ID, title, Page, or Revision
        :return: Returns an HTML string of a diff between two revisions.
        """
        # check old and diff types
        def get_param(item: object) -> Optional[Tuple[str, Union[str, int]]]:
            param = None
            if isinstance(item, str):
                param = 'title', item
            elif isinstance(item, pywikibot.Page):
                param = 'title', item.title()
            elif isinstance(item, int):
                param = 'rev', item
            elif isinstance(item, pywikibot.page.Revision):
                param = 'rev', item.revid
            return param

        old_t = get_param(old)
        if not old_t:
            raise TypeError('old parameter is of invalid type')
        diff_t = get_param(diff)
        if not diff_t:
            raise TypeError('diff parameter is of invalid type')

        params = {'action': 'compare',
                  f'from{old_t[0]}': old_t[1],
                  f'to{diff_t[0]}': diff_t[1]}

        req = self.simple_request(**params)
        data = req.submit()
        return data['compare']['*']
