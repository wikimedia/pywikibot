# -*- coding: utf-8  -*-
"""
Objects representing MediaWiki sites (wikis) and families (groups of wikis
on the same topic in different languages).
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'

import pywikibot
from pywikibot.throttle import Throttle
from pywikibot.data import api
from exceptions import *
import config

import logging
import os
import sys
import threading


class PageInUse(pywikibot.Error):
    """Page cannot be reserved for writing due to existing lock."""


def Family(fam=None, fatal=True):
    """Import the named family.

    @param fam: family name (if omitted, uses the configured default)
    @type fam: str
    @param fatal: if True, the bot will stop running if the given family is
        unknown. If False, it will only raise a ValueError exception.
    @param fatal: bool
    @return: a Family instance configured for the named family.

    """
    if fam == None:
        fam = pywikibot.default_family
    try:
        # first try the built-in families
        exec "import pywikibot.families.%s_family as myfamily" % fam
    except ImportError:
        # next see if user has defined a local family module
        try:
            sys.path.append(pywikibot.config.datafilepath('families'))
            exec "import %s_family as myfamily" % fam
        except ImportError:
            if fatal:
                output(u"""\
Error importing the %s family. This probably means the family
does not exist. Also check your configuration file."""
                           % fam)
                import traceback
                traceback.print_stack()
                sys.exit(1)
            else:
                raise ValueError("Family %s does not exist" % repr(fam))
    return myfamily.Family()


class BaseSite(object):
    """Site methods that are independent of the communication interface."""
    # to implement a specific interface, define a Site class that inherits
    # from this
    def __init__(self, code, fam=None, user=None):
        """
        @param code: the site's language code
        @type code: str
        @param fam: wiki family name (optional)
        @type fam: str or Family
        @param user: bot user name (optional)
        @type user: str

        """
        self._lang = code.lower()
        if isinstance(fam, basestring) or fam is None:
            self._family = Family(fam, fatal=False)
        else:
            self._family = fam

        # if we got an outdated language code, use the new one instead.
        if self._family.obsolete.has_key(self._lang):
            if self._family.obsolete[self._lang] is not None:
                self._lang = self._family.obsolete[self._lang]
            else:
                # no such language anymore
                raise NoSuchSite("Language %s in family %s is obsolete"
                                 % (self._lang, self._family.name))
        if self._lang not in self.languages():
            if self._lang == 'zh-classic' and 'zh-classical' in self.languages():
                self._lang = 'zh-classical'
                # database hack (database is varchar[10] -> zh-classical
                # is cut to zh-classic.
            else:
                raise NoSuchSite("Language %s does not exist in family %s"
                                 % (self._lang, self._family.name))

        self._username = user

        # following are for use with lock_page and unlock_page methods
        self._pagemutex = threading.Lock()
        self._locked_pages = []

    @property
    def throttle(self):
        """Return this Site's throttle.  Initialize a new one if needed."""
        if not hasattr(self, "_throttle"):
            self._throttle = Throttle(self, multiplydelay=True, verbosedelay=True)
            self.getsiteinfo()
            try:
                self.login(False)
            except pywikibot.NoUsername:
                pass
        return self._throttle

    def family(self):
        """Return the associated Family object."""
        return self._family

    def language(self):
        """Return the site's language code."""
        # N.B. this code does not always identify a language as such, but
        #      may identify a wiki that is part of any family grouping
        # FIXME: need to separate language (for L18N purposes) from code
        return self._lang

    def user(self):
        """Return the currently-logged in bot user, or None."""
        if self.logged_in():
            return self._username
        return None

    def __getattr__(self, attr):
        """Calls to methods not defined in this object are passed to Family."""
        if hasattr(self.__class__, attr):
            return self.__class__.attr
        try:
            method = getattr(self.family(), attr)
            f = lambda *args, **kwargs: \
                       method(self.language(), *args, **kwargs)
            if hasattr(method, "__doc__"):
                f.__doc__ = method.__doc__
            return f
        except AttributeError:
            raise AttributeError("%s instance has no attribute '%s'"
                                 % (self.__class__.__name__, attr)  )

    def sitename(self):
        """Return string representing this Site's name and language."""
        return self.family().name+':'+self.language()

    __str__ = sitename

    def __repr__(self):
        return 'Site("%s", "%s")' % (self.language(), self.family().name)

    def __hash__(self):
        return hash(repr(self))

    def linktrail(self):
        """Return regex for trailing chars displayed as part of a link."""
        return self.family().linktrail(self.language())

    def languages(self):
        """Return list of all valid language codes for this site's Family."""
        return self.family().langs.keys()

    def getNamespaceIndex(self, namespace):
        """Given a namespace name, return its int index, or None if invalid."""
        for ns in self._namespaces:
            if namespace.lower() in [name.lower()
                                     for name in self._namespaces[ns]]:
                return ns
        return None

    def namespaces(self):
        """Return dict of valid namespaces on this wiki."""
        return self._namespaces

    def normalize_namespace(self, value):
        """Return canonical local form of namespace name.

        @param value: A namespace name
        @type value: unicode

        """
        index = self.getNamespaceIndex(value)
        return self.namespace(index)

    # alias for backwards-compatibility
    normalizeNamespace = normalize_namespace

    def redirect(self, default=True):
        """Return the localized redirect tag for the site.

        If default is True, falls back to 'REDIRECT' if the site has no
        special redirect tag.

        """
        if default:
            if self.language() == 'ar':
                # It won't work with REDIRECT[[]] but it work with the local,
                # if problems, try to find a work around. FixMe!
                return self.family().redirect.get(self.language(), [u"تحويل"])[0]
            else:
                return self.family().redirect.get(self.language(), [u"REDIRECT"])[0]
        else:
            return self.family().redirect.get(self.language(), None)

    def lock_page(self, page, block=True):
        """Lock page for writing.  Must be called before writing any page.

        We don't want different threads trying to write to the same page
        at the same time, even to different sections.

        @param page: the page to be locked
        @type page: pywikibot.Page
        @param block: if true, wait until the page is available to be locked;
            otherwise, raise an exception if page can't be locked

        """
        self._pagemutex.acquire()
        try:
            while page in self._locked_pages:
                if not block:
                    raise PageInUse
                time.sleep(.25)
            self._locked_pages.append(page.title(withSection=False))
        finally:
            self._pagemutex.release()

    def unlock_page(self, page):
        """Unlock page.  Call as soon as a write operation has completed.

        @param page: the page to be locked
        @type page: pywikibot.Page

        """
        self._pagemutex.acquire()
        try:
            self._locked_pages.remove(page.title(withSection=False))
        finally:
            self._pagemutex.release()


class APISite(BaseSite):
    """API interface to MediaWiki site.

    Do not use directly; use pywikibot.Site function.

    """
##    Site methods from version 1.0 (as these are implemented in this file,
##     or declared deprecated/obsolete, they will be removed from this list)
##########
##    validLanguageLinks: A list of language codes that can be used in interwiki
##        links.
##
##    messages: return True if there are new messages on the site
##    cookies: return user's cookies as a string
##
##    getUrl: retrieve an URL from the site
##    urlEncode: Encode a query to be sent using an http POST request.
##    postForm: Post form data to an address at this site.
##    postData: Post encoded form data to an http address at this site.
##
##    redirect: Return the localized redirect tag for the site.
##    redirectRegex: Return compiled regular expression matching on redirect
##                   pages.
##    mediawiki_message: Retrieve the text of a specified MediaWiki message
##    has_mediawiki_message: True if this site defines specified MediaWiki
##                           message
##
##    shared_image_repository: Return tuple of image repositories used by this
##        site.
##    category_on_one_line: Return True if this site wants all category links
##        on one line.
##    interwiki_putfirst: Return list of language codes for ordering of
##        interwiki links.
##    linkto(title): Return string in the form of a wikilink to 'title'
##    isInterwikiLink(s): Return True if 's' is in the form of an interwiki
##                        link.
##    getSite(lang): Return Site object for wiki in same family, language
##                   'lang'.
##    version: Return MediaWiki version string from Family file.
##    versionnumber: Return int identifying the MediaWiki version.
##    live_version: Return version number read from Special:Version.
##    checkCharset(charset): Warn if charset doesn't match family file.
##
##    linktrail: Return regex for trailing chars displayed as part of a link.
##    disambcategory: Category in which disambiguation pages are listed.
##
##    Methods that yield Page objects derived from a wiki's Special: pages
##    (note, some methods yield other information in a tuple along with the
##    Pages; see method docs for details) --
##
##        search(query): query results from Special:Search
##        allpages(): Special:Allpages
##        prefixindex(): Special:Prefixindex
##        newpages(): Special:Newpages
##        newimages(): Special:Log&type=upload
##        longpages(): Special:Longpages
##        shortpages(): Special:Shortpages
##        categories(): Special:Categories (yields Category objects)
##        deadendpages(): Special:Deadendpages
##        ancientpages(): Special:Ancientpages
##        lonelypages(): Special:Lonelypages
##        unwatchedpages(): Special:Unwatchedpages (sysop accounts only)
##        uncategorizedcategories(): Special:Uncategorizedcategories (yields
##            Category objects)
##        uncategorizedpages(): Special:Uncategorizedpages
##        uncategorizedimages(): Special:Uncategorizedimages (yields
##            ImagePage objects)
##        unusedcategories(): Special:Unusuedcategories (yields Category)
##        unusedfiles(): Special:Unusedimages (yields ImagePage)
##        withoutinterwiki: Special:Withoutinterwiki
##        linksearch: Special:Linksearch

    def __init__(self, code, fam=None, user=None):
        BaseSite.__init__(self, code, fam, user)
        self._namespaces = {
            # these are the MediaWiki built-in names, which always work
            # localized names are loaded later upon accessing the wiki
            # namespace prefixes are always case-insensitive, but the
            # canonical forms are capitalized
            -2: [u"Media"],
            -1: [u"Special"],
             0: [u""],
             1: [u"Talk"],
             2: [u"User"],
             3: [u"User talk"],
             4: [u"Project"],
             5: [u"Project talk"],
             6: [u"Image"],
             7: [u"Image talk"],
             8: [u"MediaWiki"],
             9: [u"MediaWiki talk"],
            10: [u"Template"],
            11: [u"Template talk"],
            12: [u"Help"],
            13: [u"Help talk"],
            14: [u"Category"],
            15: [u"Category talk"],
            }
        self.sitelock = threading.Lock()
        return

# ANYTHING BELOW THIS POINT IS NOT YET IMPLEMENTED IN __init__()
        self._mediawiki_messages = {}
        self.nocapitalize = self._lang in self.family().nocapitalize
        self._userData = [False, False]
        self._userName = [None, None]
        self._isLoggedIn = [None, None]
        self._isBlocked = [None, None]
        self._messages = [None, None]
        self._rights = [None, None]
        self._token = [None, None]
        self._cookies = [None, None]
        # Calculating valid languages took quite long, so we calculate it once
        # in initialization instead of each time it is used.
        self._validlanguages = []
        for language in self.languages():
            if not language[:1].upper() + language[1:] in self.namespaces():
                self._validlanguages.append(language)

    def logged_in(self, sysop=False):
        """Return True if logged in with specified privileges, otherwise False.

        @param sysop: if True, require sysop privileges.

        """
        if not hasattr(self, '_userinfo'):
            return False
        if self._userinfo['name'] != self._username:
            return False
        return (not sysop) or 'sysop' in self._userinfo['groups']

    def loggedInAs(self, sysop = False):
        """Return the current username if logged in, otherwise return None.

        DEPRECATED (use .user() method instead)
        Checks if we're logged in by loading a page and looking for the login
        link. We assume that we're not being logged out during a bot run, so
        loading the test page is only required once.

        """
        logging.debug("Site.loggedInAs() method is deprecated.")
        return self.logged_in(sysop) and self.user()

    def login(self, sysop=False):
        """Log the user in if not already logged in."""
        if not self.logged_in(sysop):
            loginMan = api.LoginManager(site=self, sysop=sysop)
            if loginMan.login(retry = True):
                self._username = loginMan.username
                if hasattr(self, "_userinfo"):
                    del self._userinfo
                self.getuserinfo()

    forceLogin = login  # alias for backward-compatibility

    def getuserinfo(self):
        """Retrieve userinfo from site and store in _userinfo attribute.

        self._userinfo will be a dict with the following keys and values:

          - id: user id (numeric str)
          - name: username (if user is logged in)
          - anon: present if user is not logged in
          - groups: list of groups (could be empty)
          - rights: list of rights (could be empty)
          - message: present if user has a new message on talk page
          - blockinfo: present if user is blocked (dict)

        """
        if not hasattr(self, "_userinfo") or "rights" not in self._userinfo:
            uirequest = api.Request(
                                site=self,
                                action="query",
                                meta="userinfo",
                                uiprop="blockinfo|hasmsg|groups|rights"
                            )
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'userinfo' in uidata['query'], \
                   "API userinfo response lacks 'userinfo' key"
            self._userinfo = uidata['query']['userinfo']
        return self._userinfo

    def getsiteinfo(self):
        """Retrieve siteinfo from site and store in _siteinfo attribute."""
        if not hasattr(self, "_siteinfo"):
            sirequest = api.Request(
                                site=self,
                                action="query",
                                meta="siteinfo",
                                siprop="general|namespaces|namespacealiases"
                            )
            try:
                sidata = sirequest.submit()
            except api.APIError:
                # hack for older sites that don't support 1.12 properties
                # probably should delete if we're not going to support pre-1.12
                sirequest = api.Request(
                                    site=self,
                                    action="query",
                                    meta="siteinfo",
                                    siprop="general|namespaces"
                                )
                sidata = sirequest.submit()

            assert 'query' in sidata, \
                   "API siteinfo response lacks 'query' key"
            sidata = sidata['query']
            assert 'general' in sidata, \
                   "API siteinfo response lacks 'general' key"
            assert 'namespaces' in sidata, \
                   "API siteinfo response lacks 'namespaces' key"
            self._siteinfo = sidata['general']
            nsdata = sidata['namespaces']
            for nskey in nsdata:
                ns = int(nskey)
                if ns in self._namespaces:
                    if nsdata[nskey]["*"] in self._namespaces[ns]:
                        continue
                    # this is the preferred form so it goes at front of list
                    self._namespaces[ns].insert(0, nsdata[nskey]["*"])
                else:
                    self._namespaces[ns] = [nsdata[nskey]["*"]]
            if 'namespacealiases' in sidata:
                aliasdata = sidata['namespacealiases']
                for item in aliasdata:
                    # this is a less preferred form so it goes at the end
                    self._namespaces[int(item['id'])].append(item["*"])
        return self._siteinfo

    def case(self):
        return self.getsiteinfo()['case']

    def namespaces(self):
        """Return dict of valid namespaces on this wiki."""
        self.getsiteinfo()
        return self._namespaces

    def namespace(self, num, all=False):
        """Return string containing local name of namespace 'num'.

        If optional argument 'all' is true, return a list of all recognized
        values for this namespace.

        """
        self.getsiteinfo()
        if all:
            return self._namespaces[num]
        return self._namespaces[num][0]

    def getpageinfo(self, page):
        """Load page info from api and save in page attributes"""
        title = page.title(withSection=False)
        query = api.PropertyGenerator(
                    "info",
                    inprop="protection|talkid|subjectid",
                    titles=title.encode(self.encoding()))
        for pageitem in query:
            if pageitem['title'] != title:
                raise Error(
                    u"getpageinfo: Query on %s returned data on '%s'"
                    % (page, pageitem['title']))
            api.update_page(page, pageitem)

    def page_exists(self, page):
        """Return True if and only if page is an existing page on site."""
        if not hasattr(page, "_pageid"):
            self.getpageinfo(page)
        return page._pageid > 0
   
    def page_restrictions(self, page):
        """Returns a dictionary reflecting page protections"""
        if not self.page_exists(page):
            raise NoPage(u'No page %s.' % page)
        # page_exists called getpageinfo which set protection levels
        return page._protection

    def page_can_be_edited(self, page):
        """
        Returns True if and only if:
          - page is unprotected, and bot has an account for this site, or
          - page is protected, and bot has a sysop account for this site.

        """
        rest = self.page_restrictions(page)
        sysop_protected = rest.has_key('edit') and rest['edit'][0] == 'sysop'
        try:
            api.LoginManager(site=self, sysop=sysop_protected)
        except NoUsername:
            return False
        return True

    def page_isredirect(self, page):
        """Return True if and only if page is a redirect."""
        if not hasattr(page, "_redir"):
            self.getpageinfo(page)
        return bool(page._redir)

    def getredirtarget(self, page):
        """Return Page object for the redirect target of page."""
        if not hasattr(page, "_redir"):
            self.getpageinfo(page)
        if not page._redir:
            raise pywikibot.IsNotRedirectPage
        title = page.title(withSection=False)
        query = api.Request(site=self, action="query", property="info",
                            inprop="protection|talkid|subjectid",
                            titles=title.encode(self.encoding()),
                            redirects="")
        result = query.submit()
        if "query" not in result or "redirects" not in result["query"]:
            raise RuntimeError(
                "getredirtarget: No 'redirects' found for page %s."
                % title)
        redirmap = dict((item['from'], item['to'])
                            for item in result['query']['redirects'])
        if title not in redirmap:
            raise RuntimeError(
                "getredirtarget: 'redirects' contains no key for page %s."
                % title)
        if "pages" not in result['query']:
            # no "pages" element indicates a circular redirect
            raise pywikibot.CircularRedirect(redirmap[title])
        for pagedata in result['query']['pages'].values():
            # there should be only one value in 'pages', and it is the target
            if pagedata['title'] not in redirmap.values():
                raise RuntimeError(
                    "getredirtarget: target page '%s' not found in 'redirects'"
                    % pagedata['title'])
            target = pywikibot.Page(self, pagedata['title'], pagedata['ns'])
            api.update_page(target, pagedata)
            page._redir = target

    # following group of methods map more-or-less directly to API queries

    def getbacklinks(self, page, followRedirects=False, filterRedirects=None,
                     namespaces=None):
        """Iterate all pages that link to the given page.

        @param page: The Page to get links to.
        @param followRedirects: Also return links to redirects pointing to
            the given page.
        @param filterRedirects: If True, only return redirects to the given
            page. If False, only return non-redirect links. If None, return
            both (no filtering).
        @param namespaces: If present, only return links from the namespaces
            in this list.

        """
        bltitle = page.title(withSection=False).encode(self.encoding())
        blgen = api.PageGenerator("backlinks", gbltitle=bltitle)
        if namespaces is not None:
            blgen.request["gblnamespace"] = u"|".join(unicode(ns)
                                                      for ns in namespaces)
        if filterRedirects is not None:
            blgen.request["gblfilterredir"] = filterRedirects and "redirects"\
                                                              or "nonredirects"
        if followRedirects:
            blgen.request["gblredirect"] = ""
        return blgen

    def getembeddedin(self, page, filterRedirects=None, namespaces=None):
        """Iterate all pages that embedded the given page as a template.

        @param page: The Page to get inclusions for.
        @param filterRedirects: If True, only return redirects that embed
            the given page. If False, only return non-redirect links. If
            None, return both (no filtering).
        @param namespaces: If present, only return links from the namespaces
            in this list.

        """
        eititle = page.title(withSection=False).encode(self.encoding())
        eigen = api.PageGenerator("embeddedin", geititle=eititle)
        if namespaces is not None:
            eigen.request["geinamespace"] = u"|".join(unicode(ns)
                                                      for ns in namespaces)
        if filterRedirects is not None:
            eigen.request["geifilterredir"] = filterRedirects and "redirects"\
                                                              or "nonredirects"
        return eigen

    def getreferences(self, page, followRedirects, filterRedirects,
                      withTemplateInclusion, onlyTemplateInclusion):
        """Convenience method combining getbacklinks and getembeddedin."""
        if onlyTemplateInclusion:
            return self.getembeddedin(page)
        if not withTemplateInclusion:
            return self.getbacklinks(page, follow_redirects)
        import itertools
        return itertools.chain(self.getbacklinks(
                                    page, followRedirects, filterRedirects),
                               self.getembeddedin(page, filterRedirects)
                              )

    def getlinks(self, page, namespaces=None):
        """Iterate internal wikilinks contained (or transcluded) on page."""
        plgen = api.PageGenerator("links")
        if hasattr(page, "_pageid"):
            plgen.request['pageids'] = str(page._pageid)
        else:
            pltitle = page.title(withSection=False).encode(self.encoding())
            plgen.request['titles'] = pltitle
        if namespaces is not None:
            plgen.request["gplnamespace"] = u"|".join(unicode(ns)
                                                      for ns in namespaces)
        return plgen

    def getcategories(self, page, withSortKey=False):
        """Iterate categories to which page belongs."""
        # Sortkey doesn't work with generator; FIXME or deprecate
        clgen = api.CategoryPageGenerator("categories")
        if hasattr(page, "_pageid"):
            clgen.request['pageids'] = str(page._pageid)
        else:
            cltitle = page.title(withSection=False).encode(self.encoding())
            clgen.request['titles'] = cltitle
        return clgen

    def getimages(self, page):
        """Iterate images used (not just linked) on the page."""
        imtitle = page.title(withSection=False).encode(self.encoding())
        imgen = api.ImagePageGenerator("images", titles=imtitle)
        return imgen

    def gettemplates(self, page, namespaces=None):
        """Iterate templates transcluded (not just linked) on the page."""
        tltitle = page.title(withSection=False).encode(self.encoding())
        tlgen = api.PageGenerator("templates", titles=tltitle)
        if namespaces is not None:
            tlgen.request["gtlnamespace"] = u"|".join(unicode(ns)
                                                      for ns in namespaces)
        return tlgen

    def getcategorymembers(self, category, namespaces=None):
        """Iterate members of specified category.

        @param category: The Category to iterate.
        @param namespaces: If present, only return category members from
            these namespaces. For example, use namespaces=[14] to yield
            subcategories, use namespaces=[6] to yield image files, etc. Note,
            however, that the iterated values are always Page objects, even
            if in the Category or Image namespace.
        @type namespaces: list of ints

        """
        if category.namespace() != 14:
            raise ValueError(
                u"Cannot get category members of non-Category page '%s'"
                % category.title())
        cmtitle = category.title(withSection=False).encode(self.encoding())
        cmgen = api.PageGenerator(u"categorymembers", gcmtitle=cmtitle,
                                  gcmprop="ids|title|sortkey")
        if namespaces is not None:
            cmgen.request[u"gcmnamespace"] = u"|".join(unicode(ns)
                                                      for ns in namespaces)
        return cmgen

    def getrevisions(self, page=None, getText=False, revids=None,
                     limit=None, startid=None, endid=None, starttime=None,
                     endtime=None, rvdir=None, user=None, excludeuser=None,
                     section=None, sysop=False):
        """Retrieve and store revision information.

        By default, retrieves the last (current) revision of the page,
        I{unless} any of the optional parameters revids, startid, endid,
        starttime, endtime, rvdir, user, excludeuser, or limit are
        specified. Unless noted below, all parameters not specified
        default to False.

        If rvdir is False or not specified, startid must be greater than
        endid if both are specified; likewise, starttime must be greater
        than endtime. If rvdir is True, these relationships are reversed.

        @param page: retrieve revisions of this Page (required unless ids
            is specified)
        @param getText: if True, retrieve the wiki-text of each revision;
            otherwise, only retrieve the revision metadata (default)
        @param section: if specified, retrieve only this section of the text
            (getText must be True); section must be given by number (top of
            the article is section 0), not name
        @type section: int
        @param revids: retrieve only the specified revision ids (required
            unless page is specified)
        @type revids: list of ints
        @param limit: Retrieve no more than this number of revisions
        @type limit: int
        @param startid: retrieve revisions starting with this revid
        @param endid: stop upon retrieving this revid
        @param starttime: retrieve revisions starting at this timestamp
        @param endtime: stop upon reaching this timestamp
        @param rvdir: if false, retrieve newest revisions first (default);
            if true, retrieve earliest first
        @param user: retrieve only revisions authored by this user
        @param excludeuser: retrieve all revisions not authored by this user
        @param sysop: if True, switch to sysop account (if available) to
            retrieve this page

        """
        latest = (revids is None and
                  startid is None and
                  endid is None and
                  starttime is None and
                  endtime is None and
                  rvdir is None and
                  user is None and
                  excludeuser is None and
                  limit is None)  # if True, we are retrieving current revision

        # check for invalid argument combinations
        if page is None and revids is None:
            raise ValueError(
                "getrevisions:  either page or revids argument required")
        if (startid is not None or endid is not None) and \
                (starttime is not None or endtime is not None):
            raise ValueError(
                "getrevisions: startid/endid combined with starttime/endtime")
        if starttime is not None and endtime is not None:
            if rvdir and starttime >= endtime:
                raise ValueError(
                    "getrevisions: starttime > endtime with rvdir=True")
            if (not rvdir) and endtime >= starttime:
                raise ValueError(
                    "getrevisions: endtime > starttime with rvdir=False")
        if startid is not None and endid is not None:
            if rvdir and startid >= endid:
                raise ValueError(
                    "getrevisions: startid > endid with rvdir=True")
            if (not rvdir) and endid >= startid:
                raise ValueError(
                    "getrevisions: endid > startid with rvdir=False")

        # assemble API request
        if revids is None:
            rvtitle = page.title(withSection=False).encode(self.encoding())
            rvgen = api.PropertyGenerator(u"revisions", titles=rvtitle)
        else:
            ids = u"|".join(unicode(r) for r in revids)
            rvgen = api.PropertyGenerator(u"revisions", revids=ids)
        if getText:
            rvgen.request[u"rvprop"] = \
                    u"ids|flags|timestamp|user|comment|content"
            if section is not None:
                rvgen.request[u"rvsection"] = unicode(section)
        if limit:
            rvgen.request[u"rvlimit"] = unicode(limit)
        if rvdir:
            rvgen.request[u"rvdir"] = u"newer"
        elif rvdir is not None:
            rvgen.request[u"rvdir"] = u"older"
        if startid:
            rvgen.request[u"rvstartid"] = startid
        if endid:
            rvgen.request[u"rvendid"] = endid
        if starttime:
            rvgen.request[u"rvstart"] = starttime
        if endtime:
            rvgen.request[u"rvend"] = endtime
        if user:
            rvgen.request[u"rvuser"] = user
        elif excludeuser:
            rvgen.request[u"rvexcludeuser"] = excludeuser
        # TODO if sysop: something
        for pagedata in rvgen:
            if page is not None:
                if pagedata['title'] != page.title(withSection=False):
                    raise Error(
                        u"getrevisions: Query on %s returned data on '%s'"
                        % (page, pagedata['title']))
            else:
                page = Page(self, pagedata['title'])
            api.update_page(page, pagedata)

            for rev in pagedata['revisions']:
                revision = pywikibot.page.Revision(
                                            revid=rev['revid'],
                                            timestamp=rev['timestamp'],
                                            user=rev['user'],
                                            anon=rev.has_key('anon'),
                                            comment=rev.get('comment',  u''),
                                            minor=rev.has_key('minor'),
                                            text=rev.get('*', None)
                                          )
                page._revisions[revision.revid] = revision
                if latest:
                    page._revid = revision.revid

    def getinterwiki(self, page):
        # TODO
        raise NotImplementedError

    def getlanglinks(self, page):
        """Iterate all interlanguage links on page, yielding Link objects."""
        lltitle = page.title(withSection=False)
        llquery = api.PropertyGenerator("langlinks",
                                        titles=lltitle.encode(self.encoding())
                                       )
        for pageitem in llquery:
            if pageitem['title'] != lltitle:
                raise Error(
                    u"getlanglinks: Query on %s returned data on '%s'"
                    % (page, pageitem['title']))
            for linkdata in pageitem['langlinks']:
                yield pywikibot.Link(linkdata['*'],
                                     source=pywikibot.Site(linkdata['lang']))

    def getextlinks(self, page):
        """Iterate all external links on page, yielding URL strings."""
        eltitle = page.title(withSection=False)
        elquery = api.PropertyGenerator("extlinks",
                                        titles=eltitle.encode(self.encoding())
                                       )
        for pageitem in elquery:
            if pageitem['title'] != eltitle:
                raise RuntimeError(
                    "getlanglinks: Query on %s returned data on '%s'"
                    % (page, pageitem['title']))
            for linkdata in pageitem['extlinks']:
                yield linkdata['*']



#### METHODS NOT IMPLEMENTED YET (but may be delegated to Family object) ####
class NotImplementedYet:

    def isBlocked(self, sysop = False):
        """Check if the user is blocked."""
        try:
            text = self.getUrl(u'%saction=query&meta=userinfo&uiprop=blockinfo'
                               % self.api_address(), sysop=sysop)
            return text.find('blockedby=') > -1
        except NotImplementedError:
            return False

    def isAllowed(self, right, sysop = False):
        """Check if the user has a specific right.
        Among possible rights:
        * Actions: edit, move, delete, protect, upload
        * User levels: autoconfirmed, sysop, bot, empty string (always true)
        """
        if right == '' or right == None:
            return True
        else:
            self._load(sysop = sysop)
            index = self._userIndex(sysop)
            return right in self._rights[index]

    def messages(self, sysop = False):
        """Returns true if the user has new messages, and false otherwise."""
        self._load(sysop = sysop)
        index = self._userIndex(sysop)
        return self._messages[index]

    def cookies(self, sysop = False):
        """Return a string containing the user's current cookies."""
        self._loadCookies(sysop = sysop)
        index = self._userIndex(sysop)
        return self._cookies[index]

    def _loadCookies(self, sysop = False):
        """Retrieve session cookies for login"""
        index = self._userIndex(sysop)
        if self._cookies[index] is not None:
            return
        try:
            if sysop:
                try:
                    username = config.sysopnames[self.family().name][self.language()]
                except KeyError:
                    raise NoUsername("""\
You tried to perform an action that requires admin privileges, but you haven't
entered your sysop name in your user-config.py. Please add
sysopnames['%s']['%s']='name' to your user-config.py"""
                                     % (self.family().name, self.language()))
            else:
                username = config.usernames[self.family().name][self.language()]
        except KeyError:
            self._cookies[index] = None
            self._isLoggedIn[index] = False
        else:
            tmp = '%s-%s-%s-login.data' % (
                    self.family().name, self.language(), username)
            fn = config.datafilepath('login-data', tmp)
            if not os.path.exists(fn):
                self._cookies[index] = None
                self._isLoggedIn[index] = False
            else:
                f = open(fn)
                self._cookies[index] = '; '.join([x.strip() for x in f.readlines()])
                f.close()

    def urlEncode(self, query):
        """Encode a query so that it can be sent using an http POST request."""
        if not query:
            return None
        if hasattr(query, 'iteritems'):
            iterator = query.iteritems()
        else:
            iterator = iter(query)
        l = []
        wpEditToken = None
        for key, value in iterator:
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            key = urllib.quote(key)
            value = urllib.quote(value)
            if key == 'wpEditToken':
                wpEditToken = value
                continue
            l.append(key + '=' + value)

        # wpEditToken is explicicmy added as last value.
        # If a premature connection abort occurs while putting, the server will
        # not have received an edit token and thus refuse saving the page
        if wpEditToken != None:
            l.append('wpEditToken=' + wpEditToken)
        return '&'.join(l)

    def postForm(self, address, predata, sysop=False, useCookie=True):
        """Post http form data to the given address at this site.

        address is the absolute path without hostname.
        predata is a dict or any iterable that can be converted to a dict,
        containing keys and values for the http form.

        Return a (response, data) tuple, where response is the HTTP
        response object and data is a Unicode string containing the
        body of the response.

        """
        data = self.urlEncode(predata)
        try:
            return self.postData(address, data, sysop=sysop,
                                 useCookie=useCookie)
        except socket.error, e:
            raise ServerError(e)

    def postData(self, address, data,
                 contentType='application/x-www-form-urlencoded',
                 sysop=False, useCookie=True, compress=True):
        """Post encoded data to the given http address at this site.

        address is the absolute path without hostname.
        data is an ASCII string that has been URL-encoded.

        Returns a (response, data) tuple where response is the HTTP
        response object and data is a Unicode string containing the
        body of the response.
        """

        # TODO: add the authenticate stuff here

        if False: #self.persistent_http:
            conn = self.conn
        else:
            # Encode all of this into a HTTP request
            if self.protocol() == 'http':
                conn = httplib.HTTPConnection(self.hostname())
            elif self.protocol() == 'https':
                conn = httplib.HTTPSConnection(self.hostname())
            # otherwise, it will crash, as other protocols are not supported

        conn.putrequest('POST', address)
        conn.putheader('Content-Length', str(len(data)))
        conn.putheader('Content-type', contentType)
        conn.putheader('User-agent', useragent)
        if useCookie and self.cookies(sysop = sysop):
            conn.putheader('Cookie', self.cookies(sysop = sysop))
        if False: #self.persistent_http:
            conn.putheader('Connection', 'Keep-Alive')
        if compress:
            conn.putheader('Accept-encoding', 'gzip')
        conn.endheaders()
        conn.send(data)

        # Prepare the return values
        # Note that this can raise network exceptions which are not
        # caught here.
        try:
            response = conn.getresponse()
        except httplib.BadStatusLine:
            # Blub.
            conn.close()
            conn.connect()
            return self.postData(address, data, contentType, sysop, useCookie)

        data = response.read()

        if compress and response.getheader('Content-Encoding') == 'gzip':
            data = decompress_gzip(data)

        data = data.decode(self.encoding())
        response.close()

        if True: #not self.persistent_http:
            conn.close()

        # If a wiki page, get user data
        self._getUserData(data, sysop = sysop)

        return response, data

    def getUrl(self, path, retry = True, sysop = False, data = None, compress = True):
        """
        Low-level routine to get a URL from the wiki.

        Parameters:
            path  - The absolute path, without the hostname.
            retry - If True, retries loading the page when a network error
                    occurs.
            sysop - If True, the sysop account's cookie will be used.
            data  - An optional dict providing extra post request parameters

           Returns the HTML text of the page converted to unicode.
        """
        if False: #self.persistent_http and not data:
            self.conn.putrequest('GET', path)
            self.conn.putheader('User-agent', useragent)
            self.conn.putheader('Cookie', self.cookies(sysop = sysop))
            self.conn.putheader('Connection', 'Keep-Alive')
            if compress:
                    self.conn.putheader('Accept-encoding', 'gzip')
            self.conn.endheaders()

            # Prepare the return values
            # Note that this can raise network exceptions which are not
            # caught here.
            try:
                response = self.conn.getresponse()
            except httplib.BadStatusLine:
                # Blub.
                self.conn.close()
                self.conn.connect()
                return self.getUrl(path, retry, sysop, data, compress)

            text = response.read()
            headers = dict(response.getheaders())

        else:
            if self.hostname() in config.authenticate.keys():
                uo = authenticateURLopener
            else:
                uo = MyURLopener()
                if self.cookies(sysop = sysop):
                    uo.addheader('Cookie', self.cookies(sysop = sysop))
                if compress:
                    uo.addheader('Accept-encoding', 'gzip')

            url = '%s://%s%s' % (self.protocol(), self.hostname(), path)
            data = self.urlEncode(data)

            # Try to retrieve the page until it was successfully loaded (just in
            # case the server is down or overloaded).
            # Wait for retry_idle_time minutes (growing!) between retries.
            retry_idle_time = 1
            retrieved = False
            while not retrieved:
                try:
                    if self.hostname() in config.authenticate.keys():
                        if False: # compress:
                            request = urllib2.Request(url, data)
                            request.add_header('Accept-encoding', 'gzip')
                            opener = urllib2.build_opener()
                            f = opener.open(request)
                        else:
                            f = urllib2.urlopen(url, data)
                    else:
                        f = uo.open(url, data)
                    retrieved = True
                except KeyboardInterrupt:
                    raise
                except Exception, e:
                    if retry:
                        # We assume that the server is down. Wait some time, then try again.
                        output(u"%s" % e)
                        output(u"""\
WARNING: Could not open '%s://%s%s'. Maybe the server or
your connection is down. Retrying in %i minutes..."""
                               % (self.protocol(), self.hostname(), path,
                                  retry_idle_time))
                        time.sleep(retry_idle_time * 60)
                        # Next time wait longer, but not longer than half an hour
                        retry_idle_time *= 2
                        if retry_idle_time > 30:
                            retry_idle_time = 30
                    else:
                        raise
            text = f.read()

            headers = f.info()

        contentType = headers.get('content-type', '')
        contentEncoding = headers.get('content-encoding', '')

        # Ensure that all sent data is received
        if int(headers.get('content-length', '0')) != len(text) and 'content-length' in headers:
            output(u'Warning! len(text) does not match content-length: %s != %s' % \
                (len(text), headers.get('content-length')))
            if False: #self.persistent_http
                self.conn.close()
                self.conn.connect()
            return self.getUrl(path, retry, sysop, data, compress)

        if compress and contentEncoding == 'gzip':
            text = decompress_gzip(text)

        R = re.compile('charset=([^\'\";]+)')
        m = R.search(contentType)
        if m:
            charset = m.group(1)
        else:
            output(u"WARNING: No character set found.")
            # UTF-8 as default
            charset = 'utf-8'
        # Check if this is the charset we expected
        self.checkCharset(charset)
        # Convert HTML to Unicode
        try:
            text = unicode(text, charset, errors = 'strict')
        except UnicodeDecodeError, e:
            print e
            output(u'ERROR: Invalid characters found on %s://%s%s, replaced by \\ufffd.' % (self.protocol(), self.hostname(), path))
            # We use error='replace' in case of bad encoding.
            text = unicode(text, charset, errors = 'replace')

        # If a wiki page, get user data
        self._getUserData(text, sysop = sysop)

        return text

    def _getUserData(self, text, sysop = False):
        """
        Get the user data from a wiki page data.

        Parameters:
        * text - the page text
        * sysop - is the user a sysop?
        """
        if '<div id="globalWrapper">' not in text:
            # Not a wiki page
            return

        index = self._userIndex(sysop)

        # Check for blocks - but only if version is 1.11 (userinfo is available)
        # and the user data was not yet loaded
        if self.versionnumber() >= 11 and not self._userData[index]:
            blocked = self.isBlocked(sysop = sysop)
            if blocked and not self._isBlocked[index]:
                # Write a warning if not shown earlier
                if sysop:
                    account = 'Your sysop account'
                else:
                    account = 'Your account'
                output(u'WARNING: %s on %s is blocked. Editing using this account will stop the run.' % (account, self))
            self._isBlocked[index] = blocked

        # Check for new messages
        if '<div class="usermessage">' in text:
            if not self._messages[index]:
                # User has *new* messages
                if sysop:
                    output(u'NOTE: You have new messages in your sysop account on %s' % self)
                else:
                    output(u'NOTE: You have new messages on %s' % self)
            self._messages[index] = True
        else:
            self._messages[index] = False

        # Don't perform other checks if the data was already loaded
        if self._userData[index]:
            return

        # Search for the the user page link at the top.
        # Note that the link of anonymous users (which doesn't exist at all
        # in Wikimedia sites) has the ID pt-anonuserpage, and thus won't be
        # found here.
        userpageR = re.compile('<li id="pt-userpage"><a href=".+?">(?P<username>.+?)</a></li>')
        m = userpageR.search(text)
        if m:
            self._isLoggedIn[index] = True
            self._userName[index] = m.group('username')
        else:
            self._isLoggedIn[index] = False
            # No idea what is the user name, and it isn't important
            self._userName[index] = None

        # Check user groups, if possible (introduced in 1.10)
        groupsR = re.compile(r'var wgUserGroups = \[\"(.+)\"\];')
        m = groupsR.search(text)
        if m:
            rights = m.group(1)
            rights = rights.split('", "')
            if '*' in rights:
                rights.remove('*')
            self._rights[index] = rights
            # Warnings
            # Don't show warnings for not logged in users, they will just fail to
            # do any action
            if self._isLoggedIn[index]:
                if 'bot' not in self._rights[index]:
                    if sysop:
                        output(u'Note: Your sysop account on %s does not have a bot flag. Its edits will be visible in the recent changes.' % self)
                    else:
                        output(u'WARNING: Your account on %s does not have a bot flag. Its edits will be visible in the recent changes and it may get blocked.' % self)
                if sysop and 'sysop' not in self._rights[index]:
                    output(u'WARNING: Your sysop account on %s does not seem to have sysop rights. You may not be able to perform any sysop-restricted actions using it.' % self)
        else:
            # We don't have wgUserGroups, and can't check the rights
            self._rights[index] = []
            if self._isLoggedIn[index]:
                # Logged in user
                self._rights[index].append('user')
                # Assume bot, and thus autoconfirmed
                self._rights[index].extend(['bot', 'autoconfirmed'])
                if sysop:
                    # Assume user reported as a sysop indeed has the sysop rights
                    self._rights[index].append('sysop')
        # Assume the user has the default rights
        self._rights[index].extend(['read', 'createaccount', 'edit', 'upload', 'createpage', 'createtalk', 'move', 'upload'])
        if 'bot' in self._rights[index] or 'sysop' in self._rights[index]:
            self._rights[index].append('apihighlimits')
        if 'sysop' in self._rights[index]:
            self._rights[index].extend(['delete', 'undelete', 'block', 'protect', 'import', 'deletedhistory', 'unwatchedpages'])

        # Search for a token
        tokenR = re.compile(r"\<input type='hidden' value=\"(.*?)\" name=\"wpEditToken\"")
        tokenloc = tokenR.search(text)
        if tokenloc:
            self._token[index] = tokenloc.group(1)
            if self._rights[index] is not None:
                # In this case, token and rights are loaded - user data is now loaded
                self._userData[index] = True
        else:
            # Token not found
            # Possible reason for this is the user is blocked, don't show a
            # warning in this case, otherwise do show a warning
            # Another possible reason is that the page cannot be edited - ensure
            # there is a textarea and the tab "view source" is not shown
            if u'<textarea' in text and u'<li id="ca-viewsource"' not in text and not self._isBlocked[index]:
                # Token not found
                output(u'WARNING: Token not found on %s. You will not be able to edit any page.' % self)

    def mediawiki_message(self, key):
        """Return the MediaWiki message text for key "key" """
        global mwpage, tree
        if key.lower() not in self._mediawiki_messages.keys() \
                and not hasattr(self, "_phploaded"):
            get_throttle()
            mwpage = self.getUrl("%s?title=%s:%s&action=edit"
                     % (self.path(), urllib.quote(
                            self.namespace(8).replace(' ', '_').encode(
                                self.encoding())),
                        key))
            tree = BeautifulSoup(mwpage,
                                 convertEntities=BeautifulSoup.HTML_ENTITIES,
                                 parseOnlyThese=SoupStrainer("textarea"))
            if tree.textarea is not None and tree.textarea.string is not None:
                value = tree.textarea.string.strip()
            else:
                value = None
            if value:
                self._mediawiki_messages[key.lower()] = value
            else:
                self._mediawiki_messages[key.lower()] = None
                # Fallback in case MediaWiki: page method doesn't work
                if verbose:
                    output(
                      u"Retrieving mediawiki messages from Special:Allmessages")
                retry_idle_time = 1
                while True:
                    get_throttle()
                    phppage = self.getUrl(self.get_address("Special:Allmessages")
                                      + "&ot=php")
                    Rphpvals = re.compile(r"(?ms)'([^']*)' =&gt; '(.*?[^\\])',")
                    count = 0
                    for (phpkey, phpval) in Rphpvals.findall(phppage):
                        count += 1
                        self._mediawiki_messages[str(phpkey).lower()] = phpval
                    if count == 0:
                        # No messages could be added.
                        # We assume that the server is down.
                        # Wait some time, then try again.
                        output('WARNING: No messages found in Special:Allmessages. Maybe the server is down. Retrying in %i minutes...' % retry_idle_time)
                        time.sleep(retry_idle_time * 60)
                        # Next time wait longer, but not longer than half an hour
                        retry_idle_time *= 2
                        if retry_idle_time > 30:
                            retry_idle_time = 30
                        continue
                    break
                self._phploaded = True

        key = key.lower()
        if self._mediawiki_messages[key] is None:
            raise KeyError("MediaWiki key '%s' does not exist on %s"
                           % (key, self))
        return self._mediawiki_messages[key]

    def has_mediawiki_message(self, key):
        """Return True iff this site defines a MediaWiki message for 'key'."""
        try:
            v = self.mediawiki_message(key)
            return True
        except KeyError:
            return False

    def _load(self, sysop = False):
        """
        Loads user data.
        This is only done if we didn't do get any page yet and the information
        is requested, otherwise we should already have this data.

        Parameters:
        * sysop - Get sysop user data?
        """
        index = self._userIndex(sysop)
        if self._userData[index]:
            return

        if verbose:
            output(u'Getting information for site %s' % self)

        # Get data
        url = self.edit_address('Non-existing_page')
        text = self.getUrl(url, sysop = sysop)

        # Parse data
        self._getUserData(text, sysop = sysop)

    def search(self, query, number = 10, namespaces = None):
        """Yield search results (using Special:Search page) for query."""
        throttle = True
        path = self.search_address(urllib.quote_plus(query),
                                   n=number, ns=namespaces)
        get_throttle()
        html = self.getUrl(path)

        entryR = re.compile(ur'<li[^>]*><a href=".+?" title="(?P<title>.+?)">.+?</a>'
                              '<br />(?P<match>.*?)<span style="color[^>]*>.+?: '
                              '(?P<relevance>[0-9.]+)% - '
#                              '(?P<size>[0-9.]*) '
#                              '(?P<sizeunit>[A-Za-z]) '
#                              '\((?P<words>.+?) \w+\) - '
#                              '(?P<date>.+?)</span></li>'
                              , re.DOTALL)

        for m in entryR.finditer(html):
            page = Page(self, m.group('title'))
            match = m.group('match')
            relevance = m.group('relevance')
            #size = m.group('size')
            ## sizeunit appears to always be "KB"
            #words = m.group('words')
            #date = m.group('date')

            #print "%s - %s %s (%s words) - %s" % (relevance, size, sizeunit, words, date)

            #yield page, match, relevance, size, words, date
            yield page, match, relevance, '', '', ''

    # TODO: avoid code duplication for the following methods
    def newpages(self, number = 10, get_redirect = False, repeat = False):
        """Yield new articles (as Page objects) from Special:Newpages.

        Starts with the newest article and fetches the number of articles
        specified in the first argument. If repeat is True, it fetches
        Newpages again. If there is no new page, it blocks until there is
        one, sleeping between subsequent fetches of Newpages.

        The objects yielded are tuples composed of the Page object,
        timestamp (unicode), length (int), an empty unicode string, username
        or IP address (str), comment (unicode).

        """
        # TODO: in recent MW versions Special:Newpages takes a namespace parameter,
        #       and defaults to 0 if not specified.
        # TODO: Detection of unregistered users is broken
        # TODO: Repeat mechanism doesn't make much sense as implemented;
        #       should use both offset and limit parameters, and have an
        #       option to fetch older rather than newer pages
        seen = set()
        while True:
            path = self.newpages_address(n=number)
            # The throttling is important here, so always enabled.
            get_throttle()
            html = self.getUrl(path)

            entryR = re.compile(
'<li[^>]*>(?P<date>.+?) \S*?<a href=".+?"'
' title="(?P<title>.+?)">.+?</a>.+?[\(\[](?P<length>[\d,.]+)[^\)\]]*[\)\]]'
' .?<a href=".+?" title=".+?:(?P<username>.+?)">'
                                )
            for m in entryR.finditer(html):
                date = m.group('date')
                title = m.group('title')
                title = title.replace('&quot;', '"')
                length = int(re.sub("[,.]", "", m.group('length')))
                loggedIn = u''
                username = m.group('username')
                comment = u''

                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page, date, length, loggedIn, username, comment
            if not repeat:
                break

    def longpages(self, number = 10, repeat = False):
        """Yield Pages from Special:Longpages.

        Return values are a tuple of Page object, length(int).

        """
        #TODO: should use offset and limit parameters; 'repeat' as now
        #      implemented is fairly useless
        # this comment applies to all the XXXXpages methods following, as well
        seen = set()
        while True:
            path = self.longpages_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(ur'<li>\(<a href=".+?" title=".+?">hist</a>\) ‎<a href=".+?" title="(?P<title>.+?)">.+?</a> ‎\[(?P<length>\d+)(.+?)\]</li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                length = int(m.group('length'))
                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page, length
            if not repeat:
                break

    def shortpages(self, number = 10, repeat = False):
        """Yield Pages and lengths from Special:Shortpages."""
        throttle = True
        seen = set()
        while True:
            path = self.shortpages_address(n = number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(ur'<li>\(<a href=".+?" title=".+?">hist</a>\) ‎<a href=".+?" title="(?P<title>.+?)">.+?</a> ‎\[(?P<length>\d+)(.+?)\]</li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                length = int(m.group('length'))

                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page, length
            if not repeat:
                break

    def categories(self, number=10, repeat=False):
        """Yield Category objects from Special:Categories"""
        import catlib
        seen = set()
        while True:
            path = self.categories_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(
                '<li><a href=".+?" title="(?P<title>.+?)">.+?</a>.*?</li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                if title not in seen:
                    seen.add(title)
                    page = catlib.Category(self, title)
                    yield page
            if not repeat:
                break

    def deadendpages(self, number = 10, repeat = False):
        """Yield Page objects retrieved from Special:Deadendpages."""
        seen = set()
        while True:
            path = self.deadendpages_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(
                '<li><a href=".+?" title="(?P<title>.+?)">.+?</a></li>')
            for m in entryR.finditer(html):
                title = m.group('title')

                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page
            if not repeat:
                break

    def ancientpages(self, number = 10, repeat = False):
        """Yield Pages, datestamps from Special:Ancientpages."""
        seen = set()
        while True:
            path = self.ancientpages_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(
'<li><a href=".+?" title="(?P<title>.+?)">.+?</a> (?P<date>.+?)</li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                date = m.group('date')
                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page, date
            if not repeat:
                break

    def lonelypages(self, number = 10, repeat = False):
        """Yield Pages retrieved from Special:Lonelypages."""
        throttle = True
        seen = set()
        while True:
            path = self.lonelypages_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(
                '<li><a href=".+?" title="(?P<title>.+?)">.+?</a></li>')
            for m in entryR.finditer(html):
                title = m.group('title')

                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page
            if not repeat:
                break

    def unwatchedpages(self, number = 10, repeat = False):
        """Yield Pages from Special:Unwatchedpages (requires Admin privileges)."""
        seen = set()
        while True:
            path = self.unwatchedpages_address(n=number)
            get_throttle()
            html = self.getUrl(path, sysop = True)
            entryR = re.compile(
                '<li><a href=".+?" title="(?P<title>.+?)">.+?</a>.+?</li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page
            if not repeat:
                break

    def uncategorizedcategories(self, number = 10, repeat = False):
        """Yield Categories from Special:Uncategorizedcategories."""
        import catlib
        seen = set()
        while True:
            path = self.uncategorizedcategories_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(
                '<li><a href=".+?" title="(?P<title>.+?)">.+?</a></li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                if title not in seen:
                    seen.add(title)
                    page = catlib.Category(self, title)
                    yield page
            if not repeat:
                break

    def newimages(self, number = 10, repeat = False):
        """Yield ImagePages from Special:Log&type=upload"""

        seen = set()
        regexp = re.compile('<li[^>]*>(?P<date>.+?)\s+<a href=.*?>(?P<user>.+?)</a>\s+\(.+?</a>\).*?<a href=".*?"(?P<new> class="new")? title="(?P<image>.+?)"\s*>(?:.*?<span class="comment">(?P<comment>.*?)</span>)?', re.UNICODE)

        while True:
            path = self.log_address(number, mode = 'upload')
            get_throttle()
            html = self.getUrl(path)

            for m in regexp.finditer(html):
                image = m.group('image')

                if image not in seen:
                    seen.add(image)

                    if m.group('new'):
                        output(u"Image \'%s\' has been deleted." % image)
                        continue

                    date = m.group('date')
                    user = m.group('user')
                    comment = m.group('comment') or ''

                    yield ImagePage(self, image), date, user, comment
            if not repeat:
                break

    def uncategorizedimages(self, number = 10, repeat = False):
        """Yield ImagePages from Special:Uncategorizedimages."""
        seen = set()
        ns = self.image_namespace()
        entryR = re.compile(
            '<a href=".+?" title="(?P<title>%s:.+?)">.+?</a>' % ns)
        while True:
            path = self.uncategorizedimages_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            for m in entryR.finditer(html):
                title = m.group('title')
                if title not in seen:
                    seen.add(title)
                    page = ImagePage(self, title)
                    yield page
            if not repeat:
                break

    def uncategorizedpages(self, number = 10, repeat = False):
        """Yield Pages from Special:Uncategorizedpages."""
        seen = set()
        while True:
            path = self.uncategorizedpages_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(
                '<li><a href=".+?" title="(?P<title>.+?)">.+?</a></li>')
            for m in entryR.finditer(html):
                title = m.group('title')

                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page
            if not repeat:
                break

    def unusedcategories(self, number = 10, repeat = False):
        """Yield Category objects from Special:Unusedcategories."""
        import catlib
        seen = set()
        while True:
            path = self.unusedcategories_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile('<li><a href=".+?" title="(?P<title>.+?)">.+?</a></li>')
            for m in entryR.finditer(html):
                title = m.group('title')

                if title not in seen:
                    seen.add(title)
                    page = catlib.Category(self, title)
                    yield page
            if not repeat:
                break

    def unusedfiles(self, number = 10, repeat = False, extension = None):
        """Yield ImagePage objects from Special:Unusedimages."""
        seen = set()
        ns = self.image_namespace()
        entryR = re.compile(
            '<a href=".+?" title="(?P<title>%s:.+?)">.+?</a>' % ns)
        while True:
            path = self.unusedfiles_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            for m in entryR.finditer(html):
                fileext = None
                title = m.group('title')
                if extension:
                    fileext = title[len(title)-3:]
                if title not in seen and fileext == extension:
                    ## Check whether the media is used in a Proofread page
                    # code disabled because it slows this method down, and
                    # because it is unclear what it's supposed to do.
                    #basename = title[6:]
                    #page = Page(self, 'Page:' + basename)

                    #if not page.exists():
                    seen.add(title)
                    image = ImagePage(self, title)
                    yield image
            if not repeat:
                break

    def withoutinterwiki(self, number=10, repeat=False):
        """Yield Pages without language links from Special:Withoutinterwiki."""
        seen = set()
        while True:
            path = self.withoutinterwiki_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile('<li><a href=".+?" title="(?P<title>.+?)">.+?</a></li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page
            if not repeat:
                break

    def allpages(self, start='!', namespace=0, includeredirects=True,
                 throttle=True):
        """Yield all Pages from Special:Allpages.

        Parameters:
        start   Start at this page. By default, it starts at '!', and yields
                all pages.
        namespace Yield all pages in this namespace; defaults to 0.
                MediaWiki software will only return pages in one namespace
                at a time.

        If includeredirects is False, redirects will not be found.
        If includeredirects equals the string 'only', only redirects
        will be found. Note that this has not been tested on older
        versions of the MediaWiki code.

        It is advised not to use this directly, but to use the
        AllpagesPageGenerator from pagegenerators.py instead.

        """
        while True:
            # encode Non-ASCII characters in hexadecimal format (e.g. %F6)
            start = start.encode(self.encoding())
            start = urllib.quote(start)
            # load a list which contains a series of article names (always 480)
            path = self.allpages_address(start, namespace)
            output(u'Retrieving Allpages special page for %s from %s, namespace %i' % (repr(self), start, namespace))
            returned_html = self.getUrl(path)
            # Try to find begin and end markers
            try:
                # In 1.4, another table was added above the navigational links
                if self.versionnumber() >= 4:
                    begin_s = '</table><hr /><table'
                    end_s = '</table'
                else:
                    begin_s = '<table'
                    end_s = '</table'
                ibegin = returned_html.index(begin_s)
                iend = returned_html.index(end_s,ibegin + 3)
            except ValueError:
                raise ServerError(
"Couldn't extract allpages special page. Make sure you're using MonoBook skin.")
            # remove the irrelevant sections
            returned_html = returned_html[ibegin:iend]
            if self.versionnumber()==2:
                R = re.compile('/wiki/(.*?)\" *class=[\'\"]printable')
            elif self.versionnumber()<5:
                # Apparently the special code for redirects was added in 1.5
                R = re.compile('title ?=\"(.*?)\"')
            elif not includeredirects:
                R = re.compile('\<td(?: width="33%")?\>\<a href=\"\S*\" +title ?="(.*?)"')
            elif includeredirects == 'only':
                R = re.compile('\<td(?: width="33%")?>\<[^\<\>]*allpagesredirect\"\>\<a href=\"\S*\" +title ?="(.*?)"')
            else:
                R = re.compile('title ?=\"(.*?)\"')
            # Count the number of useful links on this page
            n = 0
            for hit in R.findall(returned_html):
                # count how many articles we found on the current page
                n = n + 1
                if self.versionnumber()==2:
                    yield Page(self, url2link(hit, site = self, insite = self))
                else:
                    yield Page(self, hit)
                # save the last hit, so that we know where to continue when we
                # finished all articles on the current page. Append a '!' so that
                # we don't yield a page twice.
                start = Page(self,hit).titleWithoutNamespace() + '!'
            # A small shortcut: if there are less than 100 pages listed on this
            # page, there is certainly no next. Probably 480 would do as well,
            # but better be safe than sorry.
            if n < 100:
                if (not includeredirects) or includeredirects == 'only':
                    # Maybe there were only so few because the rest is or is not a redirect
                    R = re.compile('title ?=\"(.*?)\"')
                    allLinks = R.findall(returned_html)
                    if len(allLinks) < 100:
                        break
                    elif n == 0:
                        # In this special case, no pages of the requested type
                        # were found, and "start" will remain and be double-encoded.
                        # Use the last page as the start of the next page.
                        start = Page(self, allLinks[-1]).titleWithoutNamespace() + '!'
                else:
                    break

    def prefixindex(self, prefix, namespace=0, includeredirects=True):
        """Yield all pages with a given prefix.

        Parameters:
        prefix   The prefix of the pages.
        namespace Namespace number; defaults to 0.
                MediaWiki software will only return pages in one namespace
                at a time.

        If includeredirects is False, redirects will not be found.
        If includeredirects equals the string 'only', only redirects
        will be found. Note that this has not been tested on older
        versions of the MediaWiki code.

        It is advised not to use this directly, but to use the
        PrefixingPageGenerator from pagegenerators.py instead.
        """
        for page in self.allpages(start = prefix, namespace = namespace, includeredirects = includeredirects):
            if page.titleWithoutNamespace().startswith(prefix):
                yield page
            else:
                break

    def linksearch(self, siteurl):
        """Yield Pages from results of Special:Linksearch for 'siteurl'."""
        if siteurl.startswith('*.'):
            siteurl = siteurl[2:]
        output(u'Querying [[Special:Linksearch]]...')
        cache = []
        for url in [siteurl, '*.' + siteurl]:
            path = self.linksearch_address(url)
            get_throttle()
            html = self.getUrl(path)
            loc = html.find('<div class="mw-spcontent">')
            if loc > -1:
                html = html[loc:]
            loc = html.find('<div class="printfooter">')
            if loc > -1:
                html = html[:loc]
            R = re.compile('title ?=\"(.*?)\"')
            for title in R.findall(html):
                if not siteurl in title:
                    # the links themselves have similar form
                    if title in cache:
                        continue
                    else:
                        cache.append(title)
                        yield Page(self, title)

    def linkto(self, title, othersite = None):
        """Return unicode string in the form of a wikilink to 'title'

        Use optional Site argument 'othersite' to generate an interwiki link.

        """
        if othersite and othersite.lang != self.language():
            return u'[[%s:%s]]' % (self.language(), title)
        else:
            return u'[[%s]]' % title

    def isInterwikiLink(self, s):
        """Return True if s is in the form of an interwiki link.

        Interwiki links have the form "foo:bar" or ":foo:bar" where foo is a
        known language code or family. Called recursively if the first part
        of the link refers to this site's own family and/or language.

        """
        s = s.strip().lstrip(":")
        if not ':' in s:
            return False
        first, rest = s.split(':',1)
        # interwiki codes are case-insensitive
        first = first.lower().strip()
        # commons: forwards interlanguage links to wikipedia:, etc.
        if self.family().interwiki_forward:
            interlangTargetFamily = Family(self.family().interwiki_forward)
        else:
            interlangTargetFamily = self.family()
        if self.getNamespaceIndex(first):
            return False
        if first in interlangTargetFamily.langs:
            if first == self.language():
                return self.isInterwikiLink(rest)
            else:
                return True
        if first in self.family().get_known_families(site = self):
            if first == self.family().name:
                return self.isInterwikiLink(rest)
            else:
                return True
        return False

    def redirectRegex(self):
        """Return a compiled regular expression matching on redirect pages.

        Group 1 in the regex match object will be the target title.

        """
        redDefault = 'redirect'
        red = 'redirect'
        if self.language() == 'ar':
            red = u"تحويل"
        try:
            if redDefault == red:
                redirKeywords = [red] + self.family().redirect[self.language()]
                redirKeywordsR = r'(?:' + '|'.join(redirKeywords) + ')'
            else:
                redirKeywords = [red] + self.family().redirect[self.language()]
                redirKeywordsR = r'(?:' + redDefault + '|'.join(redirKeywords) + ')'
        except KeyError:
            # no localized keyword for redirects
            if redDefault == red:
                redirKeywordsR = r'%s' % red
            else:
                redirKeywordsR = r'(?:%s|%s)' % (red, redDefault)
        # A redirect starts with hash (#), followed by a keyword, then
        # arbitrary stuff, then a wikilink. The wikilink may contain
        # a label, although this is not useful.
        return re.compile(r'#' + redirKeywordsR +
                                   '.*?\[\[(.*?)(?:\|.*?)?\]\]',
                          re.IGNORECASE | re.UNICODE | re.DOTALL)

    def version(self):
        """Return MediaWiki version number as a string."""
        return self.family().version(self.language())

    def versionnumber(self):
        """Return an int identifying MediaWiki version.

        Currently this is implemented as returning the minor version
        number; i.e., 'X' in version '1.X.Y'

        """
        return self.family().versionnumber(self.language())

    def live_version(self):
        """Return the 'real' version number found on [[Special:Version]]

        Return value is a tuple (int, int, str) of the major and minor
        version numbers and any other text contained in the version.

        """
        global htmldata
        if not hasattr(self, "_mw_version"):
            versionpage = self.getUrl(self.get_address("Special:Version"))
            htmldata = BeautifulSoup(versionpage, convertEntities="html")
            versionstring = htmldata.findAll(text="MediaWiki"
                                             )[1].parent.nextSibling
            m = re.match(r"^: ([0-9]+)\.([0-9]+)(.*)$", str(versionstring))
            if m:
                self._mw_version = (int(m.group(1)), int(m.group(2)),
                                        m.group(3))
            else:
                self._mw_version = self.family().version(self.language()).split(".")
        return self._mw_version

    def checkCharset(self, charset):
        """Warn if charset returned by wiki doesn't match family file."""
        if not hasattr(self,'charset'):
            self.charset = charset
        assert self.charset.lower() == charset.lower(), \
               "charset for %s changed from %s to %s" \
                   % (repr(self), self.charset, charset)
        if self.encoding().lower() != charset.lower():
            raise ValueError(
"code2encodings has wrong charset for %s. It should be %s, but is %s"
                             % (repr(self), charset, self.encoding()))

    def shared_image_repository(self):
        """Return a tuple of image repositories used by this site."""
        return self.family().shared_image_repository(self.language())

    def __cmp__(self, other):
        """Perform equality and inequality tests on Site objects."""
        if not isinstance(other, Site):
            return 1
        if self.family() == other.family:
            return cmp(self.language() ,other.lang)
        return cmp(self.family().name, other.family.name)

    def category_on_one_line(self):
        """Return True if this site wants all category links on one line."""
        return self.language() in self.family().category_on_one_line

    def interwiki_putfirst(self):
        """Return list of language codes for ordering of interwiki links."""
        return self.family().interwiki_putfirst.get(self.language(), None)

    def interwiki_putfirst_doubled(self, list_of_links):
        # TODO: is this even needed?  No family in the framework has this
        # dictionary defined!
        if self.family().interwiki_putfirst_doubled.has_key(self.language()):
            if len(list_of_links) >= self.family().interwiki_putfirst_doubled[self.language()][0]:
                list_of_links2 = []
                for lang in list_of_links:
                    list_of_links2.append(lang.language())
                list = []
                for lang in self.family().interwiki_putfirst_doubled[self.language()][1]:
                    try:
                        list.append(list_of_links[list_of_links2.index(lang)])
                    except ValueError:
                        pass
                return list
            else:
                return False
        else:
            return False

    def getSite(self, code):
        """Return Site object for language 'code' in this Family."""
        return getSite(code = code, fam = self.family(), user=self.user)

    def validLanguageLinks(self):
        """Return list of language codes that can be used in interwiki links."""
        return self._validlanguages

    def disambcategory(self):
        """Return Category in which disambig pages are listed."""
        import catlib
        try:
            return catlib.Category(self,
                    self.namespace(14)+':'+self.family().disambcatname[self.language()])
        except KeyError:
            raise NoPage(u'No page %s.' % page)

    def getToken(self, getalways = True, getagain = False, sysop = False):
        index = self._userIndex(sysop)
        if getagain or (getalways and self._token[index] is None):
            output(u'Getting a token.')
            self._load(sysop = sysop)
        if self._token[index] is not None:
            return self._token[index]
        else:
            return False

