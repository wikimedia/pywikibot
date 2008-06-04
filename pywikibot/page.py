# -*- coding: utf-8  -*-
"""
Objects representing various types of MediaWiki pages.
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'

import pywikibot
import pywikibot.site

import htmlentitydefs
import logging
import re
import sys
import unicodedata
import urllib

reNamespace = re.compile("^(.+?) *: *(.*)$")


class Page(object):
    """Page: A MediaWiki page

    This object only implements internally methods that do not require
    reading from or writing to the wiki.  All other methods are delegated
    to the Site object. 

    """
    def __init__(self, source, title=u"", ns=0, insite=None,
                 defaultNamespace=None):
        """Instantiate a Page object.

        Three calling formats are supported:

          - If the first argument is a Page, create a copy of that object.
            This can be used to convert an existing Page into a subclass
            object, such as Category or ImagePage.
          - If the first argument is a Site, create a Page on that Site
            using the second argument as the title (may include a section),
            and the third as the namespace number. The namespace number is
            mandatory, even if the title includes the namespace prefix. This
            is the preferred syntax when using an already-normalized title
            obtained from api.php or a database dump.  WARNING: may produce
            invalid objects if page title isn't in normal form!
          - If the first argument is a Link, create a Page from that link.
            This is the preferred syntax when using a title scraped from
            wikitext, URLs, or another non-normalized source.

        @param source: the source of the page
        @type source: Link, Page (or subclass), or Site
        @param title: normalized title of the page; required if source is a
            Site, ignored otherwise
        @type title: unicode
        @param ns: namespace number; required if source is a Site, ignored
            otherwise
        @type ns: int
        @param insite: DEPRECATED (use Link instead)
        @param defaultNamespace: DEPRECATED (use Link instead)

        """
        if insite is not None:
            logging.debug(
                "The 'insite' option in Page constructor is deprecated.")
        if defaultNamespace is not None:
            logging.debug(
            "The 'defaultNamespace' option in Page constructor is deprecated.")
        if isinstance(source, pywikibot.site.BaseSite):
            self._site = source
            if ns not in source.namespaces():
                raise pywikibot.Error(
                      "Invalid namespace '%i' for site %s."
                      % (ns, source.sitename()))
            self._ns = ns
            if ns and not title.startswith(source.namespace(ns)+u":"):
                title = source.namespace(ns) + u":" + title
            elif not ns and u":" in title:
                pos = title.index(u':')
                nsindex = source.getNamespaceIndex(title[ :pos])
                if nsindex:
                    self._ns = nsindex
            if u"#" in title:
                title, self._section = title.split(u"#", 1)
            else:
                self._section = None
            if not title:
                raise pywikibot.Error(
                      "Page object cannot be created from Site without title.")
            self._title = title
        elif isinstance(source, Page): 
            # copy all of source's attributes to this object
            self.__dict__ = source.__dict__
        elif isinstance(source, Link):
            self._site = source.site
            self._section = source.section
            self._ns = source.namespace
            self._title = source.title
            # reassemble the canonical title from components
            if self._ns:
                self._title = "%s:%s" % (self.site().namespace(self._ns),
                                         self._title)
        else:
            raise pywikibot.Error(
                  "Invalid argument type '%s' in Page constructor: %s"
                  % (type(source), source))
        if self._section is not None:
            self._title = self._title + "#" + self._section
        self._revisions = {}

    def site(self):
        """Return the Site object for the wiki on which this Page resides."""
        return self._site

    def namespace(self):
        """Return the number of the namespace of the page."""
        return self._ns

    def title(self, underscore=False, savetitle=False, withNamespace=True,
              withSection=True, asUrl=False, asLink=False,
              allowInterwiki=True, forceInterwiki=False, textlink=False):
        """Return the title of this Page, as a Unicode string.

        @param underscore: if true, replace all ' ' characters with '_'
        @param savetitle: if true, try to quote all non-ASCII characters.
            (DEPRECATED: use asURL instead)
        @param withNamespace: if false, omit the namespace prefix
        @param withSection: if false, omit the section
        @param asUrl: if true, quote title as if in an URL
        @param asLink: if true, return the title in the form of a wikilink
        @param allowInterwiki: (only used if asLink is true) if true, format
            the link as an interwiki link if necessary
        @param forceInterwiki: (only used if asLink is true) if true, always
            format the link as an interwiki link
        @param textlink: (only used if asLink is true) if true, place a ':'
            before Category: and Image: links

        """
        title = self._title
        if not withNamespace and self._ns != 0:
            title = title.split(u':', 1)[1]
        if not withSection and self._section:
            title = title.split(u'#', 1)[0]
        if underscore or asUrl:
            title = title.replace(u' ', u'_')
        if savetitle:
            logging.debug(
              u"Page.title(savetitle=...) is deprecated.")
        if savetitle or asUrl:
            encodedTitle = title.encode(self.site().encoding())
            title = urllib.quote(encodedTitle)
        if asLink:
            if forceInterwiki or (allowInterwiki and
                    (self.site().family != pywikibot.default_family
                     or self.site().code != pywikibot.default_code)):
                if self.site().family != pywikibot.default_family \
                        and self.site().family.name != self.site().code:
                    return u'[[%s:%s:%s]]' % (self.site().family.name,
                                              self.site().code,
                                              self._title)
                else:
                    return u'[[%s:%s]]' % (self.site().code,
                                           self._title)
            elif textlink and (self.isImage() or self.isCategory()):
                    return u'[[:%s]]' % title
            else:
                return u'[[%s]]' % title
        return title

    def section(self, underscore = False):
        """Return the name of the section this Page refers to.

        The section is the part of the title following a '#' character, if
        any. If no section is present, return None.

        @param underscore: unused, but maintained for backwards compatibility

        """
        if underscore:
            logging.debug(
                u"Page.section(underscore=...) is deprecated.")
        if self._section:
            return self._section
        else:
            return None

    def __str__(self):
        """Return a console representation of the pagelink."""
        return self.title(asLink=True, forceInterwiki=True).encode(sys.stderr.encoding)

    def __unicode__(self):
        return self.title(asLink=True, forceInterwiki=True)

    def __repr__(self):
        """Return a more complete string representation."""
        return u"%s(%s)" % (self.__class__.__name__, self.title())

    def __cmp__(self, other):
        """Test for equality and inequality of Page objects.

        Page objects are "equal" if and only if they are on the same site
        and have the same normalized title, including section if any.

        """
        if not isinstance(other, Page):
            # especially, return -1 if other is None
            return -1
        if not self.site() == other.site():
            return cmp(self.site(), other.site())
        owntitle = self.title()
        othertitle = other.title()
        return cmp(owntitle, othertitle)

    def __hash__(self):
        # Pseudo method that makes it possible to store Page objects as keys
        # in hash-tables. This relies on the fact that the string
        # representation of an instance can not change after the construction.
        return hash(unicode(self))

    def autoFormat(self):
        """Return L{date.autoFormat} dictName and value, if any.

        Value can be a year, date, etc., and dictName is 'YearBC',
        'Year_December', or another dictionary name. Please note that two
        entries may have exactly the same autoFormat, but be in two
        different namespaces, as some sites have categories with the
        same names. Regular titles return (None, None).

        """
        if not hasattr(self, '_autoFormat'):
            from pywikibot import date
            self._autoFormat = date.getAutoFormat(
                                        self.site().code,
                                        self.title(withNamespace=False)
                                    )
        return self._autoFormat

    def isAutoTitle(self):
        """Return True if title of this Page is in the autoFormat dictionary."""
        return self.autoFormat()[0] is not None

    def get(self, force=False, get_redirect=False, throttle=None,
            sysop=False, nofollow_redirects=None, change_edit_time=None):
        """Return the wiki-text of the page.

        This will retrieve the page from the server if it has not been
        retrieved yet, or if force is True. This can raise the following
        exceptions that should be caught by the calling code:

          - NoPage: The page does not exist
          - IsRedirectPage: The page is a redirect. The argument of the
                exception is the title of the page it redirects to.
          - SectionError: The section does not exist on a page with a #
                link

        @param force: reload all page attributes, including errors.
        @param get_redirect: return the redirect text, do not follow the
            redirect, do not raise an exception.
        @param sysop: if the user has a sysop account, use it to retrieve
            this page
        @param throttle: DEPRECATED and unused
        @param nofollow_redirects: DEPRECATED and unused
        @param change_edit_time: DEPRECATED and unused

        """
        if throttle is not None:
            logging.debug("Page.get(throttle) option is deprecated.")
        if nofollow_redirects is not None:
            logging.debug("Page.get(nofollow_redirects) option is deprecated.")
        if change_edit_time is not None:
            logging.debug("Page.get(change_edit_time) option is deprecated.")
        if force:
            # When forcing, we retry the page no matter what. Old exceptions
            # do not apply any more.
            for attr in ['_redirarg', '_getexception']:
                if hasattr(self, attr):
                    delattr(self,attr)
        else:
            # Make sure we re-raise an exception we got on an earlier attempt
            if hasattr(self, '_redirarg') and not get_redirect:
                raise pywikibot.IsRedirectPage, self._redirarg
            elif hasattr(self, '_getexception'):
                raise self._getexception
        if force or not hasattr(self, "_revid") \
                 or not self._revid in self._revisions:
            self.site().loadrevisions(self, getText=True, sysop=sysop)
            # TODO: Exception handling for no-page, redirects, etc.

        return self._revisions[self._revid].text

    def getOldVersion(self, oldid, force=False, get_redirect=False,
                      throttle=None, sysop=False, nofollow_redirects=None,
                      change_edit_time=None):
        """Return text of an old revision of this page; same options as get().

        @param oldid: The revid of the revision desired.

        """
        if throttle is not None:
            logging.debug(
                "Page.getOldVersion(throttle) option is deprecated.")
        if nofollow_redirects is not None:
            logging.debug(
                "Page.getOldVersion(nofollow_redirects) option is deprecated.")
        if change_edit_time is not None:
            logging.debug(
                "Page.getOldVersion(change_edit_time) option is deprecated.")
        if force or not oldid in self._revisions:
            self.site().loadrevisions(self, getText=True, ids=oldid,
                                     sysop=sysop)
        # TODO: what about redirects, errors?
        return self._revisions[oldid].text

    def permalink(self):
        """Return the permalink URL for current revision of this page."""
        return "%s://%s/%sindex.php?title=%s&oldid=%s" \
               % (self.site().protocol(),
                  self.site().hostname(),
                  self.site().script_path(),
                  self.title(asUrl=True),
                  self.latestRevision())

    def latestRevision(self):
        """Return the current revision id for this page."""
        if not hasattr(self, '_revid'):
            self.site().loadrevisions(self)
        return self._revid

    def _textgetter(self):
        """Return the current (edited) wikitext, loading it if necessary."""
        if not hasattr(self, '_text'):
            try:
                self._text = self.get()
            except pywikibot.NoPage:
                # TODO: what other exceptions might be returned?
                self._text = u""
        return self._text

    def _textsetter(self, value):
        """Update the edited wikitext"""
        self._text = unicode(value)

    def _cleartext(self):
        """Delete the edited wikitext"""
        if hasattr(self, "_text"):
            del self._text

    text = property(_textgetter, _textsetter, _cleartext,
                    "The edited wikitext (unicode) of this Page")

    def userName(self):
        """Return name or IP address of last user to edit page."""
        return self._revisions[self.latestRevision()].user

    def isIpEdit(self):
        """Return True if last editor was unregistered."""
        return self._revisions[self.latestRevision()].anon

    def editTime(self):
        """Return timestamp (in MediaWiki format) of last revision to page."""
        return self._revisions[self.latestRevision()].timestamp

    def previousRevision(self):
        """Return the revision id for the previous revision of this Page."""
        vh = self.getVersionHistory(revCount=2)
        return vh[1][0]

    def exists(self):
        """Return True if page exists on the wiki, even if it's a redirect.

        If the title includes a section, return False if this section isn't
        found.

        """
        return self.site().page_exists(self)

    def isRedirectPage(self):
        """Return True if this is a redirect, False if not or not existing."""
        return self.site().page_isredirect(self)

    def isEmpty(self):
        """Return True if the page text has less than 4 characters.

        Character count ignores language links and category links.
        Can raise the same exceptions as get().

        """
        txt = self.get()
        txt = pywikibot.removeLanguageLinks(txt, site = self.site())
        txt = pywikibot.removeCategoryLinks(txt, site = self.site())
        if len(txt) < 4:
            return True
        else:
            return False

    def isTalkPage(self):
        """Return True if this page is in any talk namespace."""
        ns = self.namespace()
        return ns >= 0 and ns % 2 == 1

    def toggleTalkPage(self):
        """Return other member of the article-talk page pair for this Page.

        If self is a talk page, returns the associated content page;
        otherwise, returns the associated talk page.
        Returns None if self is a special page.

        """
        ns = self.namespace()
        if ns < 0: # Special page
            return None
        if self.isTalkPage():
            if self.namespace() == 1:
                return Page(self.site(), self.title(withNamespace=False))
            else:
                return Page(self.site(),
                            self.site().namespace(ns - 1) + ':'
                              + self.title(withNamespace=False))
        else:
            return Page(self.site(),
                        self.site().namespace(ns + 1) + ':'
                          + self.title(withNamespace=False))

    def isCategory(self):
        """Return True if the page is a Category, False otherwise."""
        return self.namespace() == 14

    def isImage(self):
        """Return True if this is an image description page, False otherwise."""
        return self.namespace() == 6

    def isDisambig(self):
        """Return True if this is a disambiguation page, False otherwise.

        Relies on the presence of specific templates, identified in the Family
        file, to identify disambiguation pages.

        """
        if not hasattr(self, '_isDisambig'):
            locdis = self.site().family.disambig(self.site().code)
            for template in self.templates():
                tn = template.title(withNamespace=False)
                if tn in locdis:
                    _isDisambig = True
                    break
            else:
                _isDisambig = False
        return _isDisambig

    def getReferences(self, follow_redirects=True, withTemplateInclusion=True,
                      onlyTemplateInclusion=False, redirectsOnly=False,
                      namespaces=None):
        """Return an iterator all pages that refer to or embed the page.

        If you need a full list of referring pages, use 
        C{pages = list(s.getReferences())}

        @param follow_redirects: if True, also iterate pages that link to a
            redirect pointing to the page.
        @param withTemplateInclusion: if True, also iterate pages where self
            is used as a template.
        @param onlyTemplateInclusion: if True, only iterate pages where self
            is used as a template.
        @param redirectsOnly: if True, only iterate redirects to self.
        @param namespaces: only iterate pages in these namespaces

        """
        # N.B.: this method intentionally overlaps with backlinks() and
        # embeddedin(). Depending on the interface, it may be more efficient
        # to implement those methods in the site interface and then combine
        # the results for this method, or to implement this method and then
        # split up the results for the others. 
        return self.site().pagereferences(
                           self, follow_redirects, redirectsOnly,
                           withTemplateInclusion, onlyTemplateInclusion,
                           namespaces)

    def backlinks(self, followRedirects=True, filterRedirects=None,
                  namespaces=None):
        """Return an iterator for pages that link to this page.

        @param followRedirects: if True, also iterate pages that link to a
            redirect pointing to the page.
        @param filterRedirects: if True, only iterate redirects; if False,
            omit redirects; if None, do not filter
        @param namespaces: only iterate pages in these namespaces

        """
        return self.site().pagebacklinks(self, followRedirects, filterRedirects,
                                         namespaces)

    def embeddedin(self, filter_redirects=None, namespaces=None):
        """Return an iterator for pages that embed this page as a template.

        @param filterRedirects: if True, only iterate redirects; if False,
            omit redirects; if None, do not filter
        @param namespaces: only iterate pages in these namespaces

        """
        return self.site().page_embeddedin(self, filter_redirects, namespaces)

    def canBeEdited(self):
        """Return bool indicating whether this page can be edited.

        This returns True if and only if:
          - page is unprotected, and bot has an account for this site, or
          - page is protected, and bot has a sysop account for this site.

        """
        return self.site().page_can_be_edited(self)

    def botMayEdit(self):
        """Return True if this page allows bots to edit it.

        This will be True if the page doesn't contain {{bots}} or
        {{nobots}}, or it contains them and the active bot is allowed to
        edit this page. (This method is only useful on those sites that
        recognize the bot-exclusion protocol; on other sites, it will always
        return True.)

        The framework enforces this restriction by default. It is possible
        to override this by setting ignore_bot_templates=True in
        user_config.py, or using page.put(force=True).

        """ # TODO: move this to Site object?
        if config.ignore_bot_templates: #Check the "master ignore switch"
            return True
        try:
            templates = self.templatesWithParams();
        except (pywikibot.NoPage,
                pywikibot.IsRedirectPage,
                pywikibot.SectionError):
            return True
        for template in templates:
            title = template[0].title(withNamespace=False)
            if title == 'Nobots':
                return False
            elif title == 'Bots':
                if len(template[1]) == 0:
                    return True
                else:
                    (ttype, bots) = template[1][0].split('=', 1)
                    bots = bots.split(',')
                    if ttype == 'allow':
                        if 'all' in bots or username in bots:
                            return True
                        else:
                            return False
                    if ttype == 'deny':
                        if 'all' in bots or username in bots:
                            return False
                        else:
                            return True
        # no restricting template found
        return True

    def put(self, newtext, comment=None, watchArticle=None, minorEdit=True,
            force=False):
        """Save the page with the contents of the first argument as the text.

        @param newtext: The complete text of the revised page.
        @type newtext: unicode
        @param comment: The edit summary for the modification (optional,
            but most wikis strongly encourage its use)
        @type comment: unicode
        @param watchArticle: if True, add or if False, remove this Page
            to/from bot user's watchlist; if None, leave watchlist status
            unchanged
        @type watchArticle: bool or None
        @param minorEdit: if True, mark this edit as minor
        @type minorEdit: bool
        @param force: if True, ignore botMayEdit() setting
        @type force: bool

        """
        return self.site().put(self, newtext, comment, watchArticle,
                               minorEdit, force)

    def put_async(self, newtext,
                  comment=None, watchArticle=None, minorEdit=True, force=False,
                  callback=None):
        """Put page on queue to be saved to wiki asynchronously.

        Asynchronous version of put (takes the same arguments), which places
        pages on a queue to be saved by a daemon thread. All arguments are
        the same as for .put(), except:

        @param callback: a callable object that will be called after the
            page put operation. This object must take two arguments: (1) a
            Page object, and (2) an exception instance, which will be None
            if the page was saved successfully. The callback is intended for
            use by bots that need to keep track of which saves were
            successful.

        """
        return self.site().put(self, newtext, comment, watchArticle,
                               minorEdit, force, callback, async=True)

    def linkedPages(self):
        """Iterate Pages that this Page links to.

        Only returns pages from "normal" internal links. Image and category
        links are omitted unless prefixed with ":"; embedded templates are
        omitted (but links within them are returned); all interwiki and
        external links are omitted.

        @return: a generator that yields Page objects.

        """
        return self.site().pagelinks(self)

    def interwiki(self):
        """Iterate interwiki links in the page text.

        @return: a generator that yields Link objects.

        """
        return self.site().pageinterwiki(self)

    def langlinks(self):
        """Iterate all interlanguage links on this page.

        Note that the links yielded by this method will be a subset of
        the results of self.interwiki().

        @return: a generator that yields Link objects.

        """
        return self.site().pagelanglinks(self)

    def imagelinks(self, followRedirects=None, loose=None):
        """Iterate ImagePage objects for images displayed on this Page.

        @param followRedirects: DEPRECATED and ignored
        @param loose: DEPRECATED and ignored
        @return: a generator that yields ImagePage objects.

        """
        if followRedirects is not None:
            logging.debug(
                u"Page.imagelinks(followRedirects) option is deprecated.")
        if loose is not None:
            logging.debug(
                u"Page.imagelinks(loose) option is deprecated.")
        return self.site().pageimages(self)

    def templates(self):
        """Iterate Page objects for templates used on this Page.

        Template parameters are ignored.  This method only returns embedded
        templates, not template pages that happen to be referenced through
        a normal link.

        """
        return self.site().pagetemplates(self)

    def templatesWithParams(self):
        """Iterate templates used on this Page.

        @return: a generator that yields a tuple for each use of a template
        in the page, with the template Page as the first entry and a list of
        parameters as the second entry.

        """
        return self.site().templates_with_params(self)

    def categories(self, nofollow_redirects=None, withSortKey=False):
        """Iterate categories that the article is in.

        @param nofollow_redirects: DEPRECATED and ignored
        @param withSortKey: if True, include the sort key in each Category.
        @return: a generator that yields Category objects.

        """
        # follow_redirects makes no sense here because category membership
        # doesn't follow redirects
        if nofollow_redirects is not None:
            logging.debug(
                u"Page.categories(nofollow_redirects) option is deprecated.")
        return self.site().pagecategories(self, withSortKey=withSortKey)

    def extlinks(self):
        """Iterate all external URLs (not interwiki links) from this page.

        @return: a generator that yields unicode objects containing URLs.

        """
        return self.site().page_extlinks(self)

    def getRedirectTarget(self):
        """Return a Page object for the target this Page redirects to.

        If this page is not a redirect page, will raise an IsNotRedirectPage
        exception. This method also can raise a NoPage exception.

        """
        if not self.isRedirectPage():
            raise pywikibot.IsNotRedirectPage
        if not isinstance(self._redir, Page):
            self.site().getredirtarget(self)
        return self._redir

    def getVersionHistory(self, forceReload=False, reverseOrder=False,
                          getAll=False, revCount=500):
        """Load the version history page and return history information.

        Return value is a list of tuples, where each tuple represents one
        edit and is built of revision id, edit date/time, user name, and
        edit summary. Starts with the most current revision, unless
        reverseOrder is True. Defaults to getting the first revCount edits,
        unless getAll is True.

        """
        if getAll:
            limit = None
        else:
            limit = revCount
        return self.site().loadrevisions(self, getText=False,
                                        rvdir=not reverseOrder, limit=limit)

    def getVersionHistoryTable(self, forceReload=False, reverseOrder=False,
                               getAll=False, revCount=500):
        """Return the version history as a wiki table."""
        result = '{| border="1"\n'
        result += '! oldid || date/time || username || edit summary\n'
        for oldid, time, username, summary \
                in self.getVersionHistory(forceReload=forceReload,
                                          reverseOrder=reverseOrder,
                                          getAll=getAll, revCount=revCount):
            result += '|----\n'
            result += '| %s || %s || %s || <nowiki>%s</nowiki>\n'\
                      % (oldid, time, username, summary)
        result += '|}\n'
        return result

    def fullVersionHistory(self):
        """Iterate all previous versions including wikitext.

        @return: A generator that yields tuples consisting of revision ID,
            edit date/time, user name and content
        """
        return self.site().loadrevisions(self, withText=True)

    def contributingUsers(self):
        """Return a set of usernames (or IPs) of users who edited this page."""
        edits = self.getVersionHistory()
        users = set([edit[2] for edit in edits])
        return users

    def move(self, newtitle, reason=None, movetalkpage=True, sysop=False,
             throttle=None, deleteAndMove=False, safe=True):
        """Move this page to a new title.

        @param newtitle: The new page title.
        @param reason: The edit summary for the move.
        @param movetalkpage: If true, move this page's talk page (if it exists)
        @param sysop: Try to move using sysop account, if available
        @param throttle: DEPRECATED
        @param deleteAndMove: if move succeeds, delete the old page
            (requires sysop privileges)
        @param safe: If false, attempt to delete existing page at newtitle
            (if there is one) and then move this page to that title

        """
        if throttle is not None:
            logging.debug(
                u"Page.move: throttle option is deprecated.")
        if reason is None:
            logging.info(u'Moving %s to [[%s]].'
                             % (self.title(asLink=True), newtitle))
            reason = pywikibot.input(u'Please enter a reason for the move:')
        return self.site().move(self, newtitle, reason,
                                movetalkpage=movetalkpage, sysop=sysop,
                                deleteAndMove=deleteAndMove, safe=safe)

    def delete(self, reason=None, prompt=True, throttle=None, mark=False):
        """Deletes the page from the wiki. Requires administrator status.

        @param reason: The edit summary for the deletion.
        @param prompt: If true, prompt user for confirmation before deleting.
        @param mark: if true, and user does not have sysop rights, place a
            speedy-deletion request on the page instead.

        """
        if throttle is not None:
            logging.debug(
                u"Page.delete: throttle option is deprecated.")
        if reason is None:
            logging.info(u'Deleting %s.' % (self.title(asLink=True)))
            reason = pywikibot.input(u'Please enter a reason for the deletion:')
        answer = u'y'
        if prompt and not hasattr(self.site(), '_noDeletePrompt'):
            answer = pywikibot.inputChoice(u'Do you want to delete %s?'
                        % self.title(asLink = True, forceInterwiki = True),
                                           ['Yes', 'No', 'All'],
                                           ['Y', 'N', 'A'],
                                           'N')
            if answer in ['a', 'A']:
                answer = 'y'
                self.site()._noDeletePrompt = True
        if answer in ['y', 'Y']:
            return self.site().delete(self, reason, mark=mark)

    def loadDeletedRevisions(self):
        """Retrieve all deleted revisions for this Page from Special/Undelete.

        Stores all revisions' timestamps, dates, editors and comments in
        self._deletedRevs attribute.

        @return: list of timestamps (which can be used to retrieve revisions
            later on).

        """
        return self.site().loadDeletedRevisions(self)

    def getDeletedRevision(self, timestamp, retrieveText=False):
        """Return a particular deleted revision by timestamp.

        @return: a list of [date, editor, comment, text, restoration
            marker]. text will be None, unless retrieveText is True (or has
            been retrieved earlier). If timestamp is not found, returns
            None.

        """
        return self.site().getDeletedRevision(self, timestamp,
                                              getText=retrieveText)

    def markDeletedRevision(self, timestamp, undelete=True):
        """Mark the revision identified by timestamp for undeletion.

        @param undelete: if False, mark the revision to remain deleted.

        """
        if self._deletedRevs == None:
            self.loadDeletedRevisions()
        if not self._deletedRevs.has_key(timestamp):
            #TODO: Throw an exception?
            return None
        self._deletedRevs[timestamp][4] = undelete
        self._deletedRevsModified = True

    def undelete(self, comment=None, throttle=None):
        """Undelete revisions based on the markers set by previous calls.

        If no calls have been made since loadDeletedRevisions(), everything
        will be restored.

        Simplest case::
            Page(...).undelete('This will restore all revisions')

        More complex::
            pg = Page(...)
            revs = pg.loadDeletedRevsions()
            for rev in revs:
                if ... #decide whether to undelete a revision
                    pg.markDeletedRevision(rev) #mark for undeletion
            pg.undelete('This will restore only selected revisions.')

        @param comment: The undeletion edit summary.
        @param throttle: DEPRECATED

        """
        if throttle is not None:
            logging.debug(
                u"Page.undelete: throttle option is deprecated.")
        if comment is None:
            logging.info(u'Preparing to undelete %s.'
                             % (self.title(asLink=True)))
            comment = pywikibot.input(
                        u'Please enter a reason for the undeletion:')
        return self.site().undelete(self, comment)

    def protect(self, edit='sysop', move='sysop', unprotect=False,
                reason=None, prompt=True, throttle=None):
        """(Un)protect a wiki page. Requires administrator status.

        Valid protection levels (in MediaWiki 1.12) are '' (equivalent to
        'none'), 'autoconfirmed', and 'sysop'.

        @param edit: Level of edit protection
        @param move: Level of move protection
        @param unprotect: If true, unprotect the page (equivalent to setting
            all protection levels to '')
        @param reason: Edit summary.
        @param prompt: If true, ask user for confirmation.
        @param throttle: DEPRECATED

        """
        if throttle is not None:
            logging.debug(
                u"Page.protect: throttle option is deprecated.")
        if reason is None:
            if unprotect:
                un = u'un'
            else:
                un = u''
            logging.info(u'Preparing to %sprotect %s.'
                             % (un, self.title(asLink=True)))
            reason = pywikibot.input(u'Please enter a reason for the action:')
        if unprotect:
            edit = move = ""
        answer = 'y'
        if prompt and not hasattr(self.site(), '_noProtectPrompt'):
            answer = pywikibot.inputChoice(
                        u'Do you want to change the protection level of %s?'
                          % self.title(asLink=True, forceInterwiki = True),
                        ['Yes', 'No', 'All'], ['Y', 'N', 'A'], 'N')
            if answer in ['a', 'A']:
                answer = 'y'
                self.site()._noProtectPrompt = True
        if answer in ['y', 'Y']:
            return self.site().protect(self, edit, move, reason)

######## DEPRECATED METHODS ########

    def encoding(self):
        """Return the character encoding used on this Page's wiki Site.

        DEPRECATED: use Site.encoding() instead

        """
        logging.debug(u"Page.encoding() is deprecated; use Site.encoding().")
        return self.site().encoding()

    def titleWithoutNamespace(self, underscore=False):
        """Return title of Page without namespace and without section.

        DEPRECATED: use self.title(withNamespace=False) instead.

        """
        logging.debug(
            u"Page.titleWithoutNamespace() method is deprecated.")
        return self.title(underscore=underscore, withNamespace=False,
                          withSection=False)

    def sectionFreeTitle(self, underscore=False):
        """Return the title of this Page, without the section (if any).

        DEPRECATED: use self.title(withSection=False) instead.

        """
        logging.debug(
            u"Page.sectionFreeTitle() method is deprecated.")
        return self.title(underscore=underscore, withSection=False)

    def aslink(self, forceInterwiki=False, textlink=False, noInterwiki=False):
        """Return a string representation in the form of a wikilink.

        DEPRECATED: use self.title(asLink=True) instead.

        """
        logging.debug(u"Page.aslink() method is deprecated.")
        return self.title(asLink=True, forceInterwiki=forceInterwiki,
                          allowInterwiki=not noInterwiki, textlink=textlink)

    def urlname(self):
        """Return the Page title encoded for use in an URL.

        DEPRECATED: use self.title(asUrl=True) instead.

        """
        logging.debug(u"Page.urlname() method is deprecated.")
        return self.title(asUrl=True)

####### DISABLED METHODS (warnings provided) ######
    # these methods are easily replaced by editing the page's text using
    # textlib methods and then using put() on the result.

    def removeImage(self, image, put=False, summary=None, safe=True):
        """Old method to remove all instances of an image from page."""
        logging.warning(u"Page.removeImage() is no longer supported.")

    def replaceImage(self, image, replacement=None, put=False, summary=None,
                     safe=True):
        """Old method to replace all instances of an image with another."""
        logging.warning(u"Page.replaceImage() is no longer supported.")


class ImagePage(Page):
    """A subclass of Page representing an image descriptor wiki page.

    Supports the same interface as Page, with the following added methods:

    getImagePageHtml          : Download image page and return raw HTML text.
    fileURL                   : Return the URL for the image described on this
                                page.
    fileIsOnCommons           : Return True if image stored on Wikimedia
                                Commons.
    fileIsShared              : Return True if image stored on Wikitravel
                                shared repository.
    getFileMd5Sum             : Return image file's MD5 checksum.
    getFileVersionHistory     : Return the image file's version history.
    getFileVersionHistoryTable: Return the version history in the form of a
                                wiki table.
    usingPages                : Iterate Pages on which the image is displayed.

    """
    def __init__(self, source, title=u"", insite=None):
        Page.__init__(self, source, title, 6)
        if self.namespace() != 6:
            raise ValueError(u"'%s' is not in the image namespace!" % title)

    def getImagePageHtml(self):
        """
        Download the image page, and return the HTML, as a unicode string.

        Caches the HTML code, so that if you run this method twice on the
        same ImagePage object, the page will only be downloaded once.
        """
        if not hasattr(self, '_imagePageHtml'):
            from pywikibot.data import http
            path = "%s/index.php?title=%s" \
                   % (self.site().scriptpath(), self.title(asUrl=True))
            self._imagePageHtml = http.request(self.site(), path)
        return self._imagePageHtml

    def fileUrl(self):
        """Return the URL for the image described on this page."""
        # TODO add scaling option?
        if not hasattr(self, '_imageinfo'):
            self._imageinfo = self.site().getimageinfo(self)
        return self._imageinfo['url']

    def fileIsOnCommons(self):
        """Return True if the image is stored on Wikimedia Commons"""
        return self.fileUrl().startswith(
            'http://upload.wikimedia.org/wikipedia/commons/')

    def fileIsShared(self):
        """Return True if image is stored on any known shared repository."""
        # as of now, the only known repositories are commons and wikitravel
        if 'wikitravel_shared' in self.site().shared_image_repository():
            return self.fileUrl().startswith(
                u'http://wikitravel.org/upload/shared/')
        return self.fileIsOnCommons()

    def getFileMd5Sum(self):
        """Return image file's MD5 checksum."""
        logging.debug(
            "ImagePage.getFileMd5Sum() is deprecated; use getFileSHA1Sum().")
# FIXME: MD5 might be performed on incomplete file due to server disconnection
# (see bug #1795683).
        import md5, urllib
        f = urllib.urlopen(self.fileUrl())
        # TODO: check whether this needs a User-Agent header added
        md5Checksum = md5.new(f.read()).hexdigest()
        f.close()
        return md5Checksum

    def getFileSHA1Sum(self):
        """Return image file's SHA1 checksum."""
        if not hasattr(self, '_imageinfo'):
            self._imageinfo = self.site().getimageinfo(self)
        return self._imageinfo['sha1']

    def getFileVersionHistory(self):
        """Return the image file's version history.

        @return: An iterator yielding tuples containing (timestamp,
            username, resolution, filesize, comment).

        """
        #TODO; return value may need to change
        return self.site().getimageinfo(self, history=True)

    def getFileVersionHistoryTable(self):
        """Return the version history in the form of a wiki table."""
        lines = []
        #TODO: if getFileVersionHistory changes, make sure this follows it
        for (datetime, username, resolution, size, comment) \
                in self.getFileVersionHistory():
            lines.append('| %s || %s || %s || %s || <nowiki>%s</nowiki>' \
                         % (datetime, username, resolution, size, comment))
        return u'{| border="1"\n! date/time || username || resolution || size || edit summary\n|----\n' + u'\n|----\n'.join(lines) + '\n|}'

    def usingPages(self):
        """Yield Pages on which the image is displayed."""
        return self.site().getimageusage(self)

class Category(Page):
    """A page in the Category: namespace"""

    def __init__(self, source, title=u"", insite=None, sortKey=None):
        """All parameters are the same as for Page() constructor, except:

        @param sortKey: DEPRECATED (use .aslink() method instead)

        """
        if sortKey is not None:
            logging.debug(
                "The 'sortKey' option in Category constructor is deprecated.")
        Page.__init__(self, source, title, 14)
        if self.namespace() != 14:
            raise ValueError(u"'%s' is not in the category namespace!"
                             % title)

    def aslink(self, sortKey=u'', forceInterwiki=None, textlink=None,
               noInterwiki=None):
        """Return a link to place a page in this Category.

        Use this only to generate a "true" category link, not for interwikis
        or text links to category pages.

        Parameters are deprecated and preserved for backwards-compatibility,
        except:

        @param sortKey: The sort key for the article to be placed in this
            Category; if omitted, default sort key is used.
        @type sortKey: (optional) unicode

        """
        if forceInterwiki is not None \
                or textlink is not None or noInterwiki is not None:
            logging.debug("All arguments to Category.aslink() are deprecated.")
        if sortKey:
            titleWithSortKey = '%s|%s' % (self.title(withSection=False),
                                          self.sortKey)
        else:
            titleWithSortKey = self.title(withSection=False)
        return '[[%s]]' % titleWithSortKey

    def subcategories(self, recurse=False):
        """Iterate all subcategories of the current category.

        @param recurse: if not False or 0, also iterate subcategories of
            subcategories. If an int, limit recursion to this number of
            levels. (Example: recurse=1 will iterate direct subcats and
            first-level sub-sub-cats, but no deeper.)
        @type recurse: int or bool

        """
        if not isinstance(recurse, bool) and recurse:
            recurse = recurse - 1
        if not hasattr(self, "_subcats"):
            self._subcats = []
            for member in self.site().categorymembers(self, namespaces=[14]):
                subcat = Category(self.site(), member.title())
                self._subcats.append(subcat)
                yield subcat
                if recurse:
                    for item in subcat.subcategories(recurse):
                        yield item
        else:
            for subcat in self._subcats:
                yield subcat
                if recurse:
                    for item in subcat.subcategories(recurse):
                        yield item

    def articles(self, recurse=False, startFrom=None):
        """
        Yields all articles in the current category.

        @param recurse: if not False or 0, also iterate articles in
            subcategories. If an int, limit recursion to this number of
            levels. (Example: recurse=1 will iterate articles in first-level
            subcats, but no deeper.)
        @type recurse: int or bool

        """
        namespaces = [x for x in self.site().namespaces().keys()
                      if x>=0 and x!=14]
        for member in self.site().categorymembers(self,
                                                     namespaces=namespaces):
            yield member
        if recurse:
            if not isinstance(recurse, bool) and recurse:
                recurse = recurse - 1
            for subcat in self.subcategories():
                for article in subcat.articles(recurse):
                    yield article

    def isEmptyCategory(self):
        """Return True if category has no members (including subcategories)."""
        for member in self.site().categorymembers(self, limit=1):
            return False
        return True

    def copyTo(self, catname):
        """
        Copy text of category page to a new page.  Does not move contents.

        @param catname: New category title (without namespace)
        @return: True if copying was successful, False if target page
            already existed.

        """
        # This seems far too specialized to be in the top-level framework
        catname = self.site().category_namespace() + ':' + catname
        targetCat = Category(self.site(), catname)
        if targetCat.exists():
            logging.warn('Target page %s already exists!'
                             % targetCat.title())
            return False
        else:
            logging.info('Moving text from %s to %s.'
                             % (self.title(), targetCat.title()))
            authors = ', '.join(self.contributingUsers())
            creationSummary = pywikibot.translate(
                                  self.site(), msg_created_for_renaming
                              ) % (self.title(), authors)
            targetCat.put(self.get(), creationSummary)
            return True

    def copyAndKeep(self, catname, cfdTemplates):
        """Copy partial category page text (not contents) to a new title.

        Like copyTo above, except this removes a list of templates (like
        deletion templates) that appear in the old category text.  It also
        removes all text between the two HTML comments BEGIN CFD TEMPLATE
        and END CFD TEMPLATE. (This is to deal with CFD templates that are
        substituted.)

        Returns true if copying was successful, false if target page already
        existed.

        @param catname: New category title (without namespace)
        @param cfdTemplates: A list (or iterator) of templates to be removed
            from the page text
        @return: True if copying was successful, False if target page
            already existed.

        """
        # I don't see why we need this as part of the framework either
        catname = self.site().category_namespace() + ':' + catname
        targetCat = Category(self.site(), catname)
        if targetCat.exists():
            logging.warn('Target page %s already exists!'
                             % targetCat.title())
            return False
        else:
            logging.info('Moving text from %s to %s.'
                             % (self.title(), targetCat.title()))
            authors = ', '.join(self.contributingUsers())
            creationSummary = pywikibot.translate(
                                  self.site(), msg_created_for_renaming
                              ) % (self.title(), authors)
            newtext = self.get()
        for regexName in cfdTemplates:
            matchcfd = re.compile(r"{{%s.*?}}" % regexName, re.IGNORECASE)
            newtext = matchcfd.sub('',newtext)
            matchcomment = re.compile(
                        r"<!--BEGIN CFD TEMPLATE-->.*?<!--END CFD TEMPLATE-->",
                                      re.IGNORECASE | re.MULTILINE | re.DOTALL)
            newtext = matchcomment.sub('', newtext)
            pos = 0
            while (newtext[pos:pos+1] == "\n"):
                pos = pos + 1
            newtext = newtext[pos:]
            targetCat.put(newtext, creationSummary)
            return True

#### DEPRECATED METHODS ####
    def subcategoriesList(self, recurse=False):
        """DEPRECATED: Equivalent to list(self.subcategories(...))"""
        logging.debug("Category.subcategoriesList() method is deprecated.")
        return sorted(list(set(self.subcategories(recurse))))

    def articlesList(self, recurse=False):
        """DEPRECATED: equivalent to list(self.articles(...))"""
        logging.debug("Category.articlesList() method is deprecated.")
        return sorted(list(set(self.articles(recurse))))

    def supercategories(self):
        """DEPRECATED: equivalent to self.categories()"""
        logging.debug("Category.supercategories() method is deprecated.")
        return self.categories()

    def supercategoriesList(self):
        """DEPRECATED: equivalent to list(self.categories(...))"""
        logging.debug("Category.articlesList() method is deprecated.")
        return sorted(list(set(self.categories())))


class Revision(object):
    """A structure holding information about a single revision of a Page."""
    def __init__(self, revid, timestamp, user, anon=False, comment=u"",
                 text=None, minor=False):
        """All parameters correspond to object attributes (e.g., revid
        parameter is stored as self.revid)

        @param revid: Revision id number
        @type revid: int
        @param text: Revision wikitext.
        @type text: unicode, or None if text not yet retrieved
        @param timestamp: Revision time stamp (in MediaWiki text format)
        @type timestamp: unicode
        @param user: user who edited this revision
        @type user: unicode
        @param anon: user is unregistered
        @type anon: bool
        @param comment: edit comment text
        @type comment: unicode
        @param minor: edit flagged as minor
        @type minor: bool

        """
        self.revid = revid
        self.text = text
        self.timestamp = timestamp
        self.user = user
        self.anon = anon
        self.comment = comment
        self.minor = minor


class Link(object):
    """A Mediawiki link (local or interwiki)

    Has the following attributes:

      - site:  The Site object for the wiki linked to
      - namespace: The namespace of the page linked to (int)
      - title: The title of the page linked to (unicode); does not include
        namespace or section
      - section: The section of the page linked to (unicode or None); this
        contains any text following a '#' character in the title
      - anchor: The anchor text (unicode or None); this contains any text
        following a '|' character inside the link

    """
    illegal_titles_pattern = re.compile(
        # Matching titles will be held as illegal.
            u'''[^ %!\"$&'()*,\\-.\\/0-9:;=?@A-Z\\\\^_`a-z~\u0080-\uFFFF+]'''
            # URL percent encoding sequences interfere with the ability
            # to round-trip titles -- you can't link to them consistently.
            u'|%[0-9A-Fa-f]{2}' 
            # XML/HTML character references produce similar issues.
            u'|&[A-Za-z0-9\x80-\xff]+;'
            u'|&#[0-9]+;'
            u'|&#x[0-9A-Fa-f]+;'
        )

    def __init__(self, text, source=None, defaultNamespace=0):
        """Parse text into a Link object.

        @param text: the link text (everything appearing between [[ and ]]
            on a wiki page)
        @type text: unicode
        @param source: the Site on which the link was found (not necessarily
            the site to which the link refers)
        @type source: Site
        @param defaultNamespace: a namespace to use if the link does not
            contain one (defaults to 0)
        @type defaultNamespace: int

        """
        # First remove the anchor, which is stored unchanged, if there is one
        if u"|" in text:
            text, self.anchor = text.split(u"|", 1)
        else:
            self.anchor = None

        if source is None:
            source = pywikibot.Site()
        self.source = self.site = source

        # Clean up the name, it can come from anywhere.
        # Convert HTML entities to unicode
        t = html2unicode(text)

        # Convert URL-encoded characters to unicode
        t = url2unicode(t, site=self.site)

        # Normalize unicode string to a NFC (composed) format to allow proper
        # string comparisons. According to
        # http://svn.wikimedia.org/viewvc/mediawiki/branches/REL1_6/phase3/includes/normal/UtfNormal.php?view=markup
        # the mediawiki code normalizes everything to NFC, not NFKC (which
        # might result in information loss).
        t = unicodedata.normalize('NFC', t)

        # This code was adapted from Title.php : secureAndSplit()
        #
        if u'\ufffd' in t:
            raise pywikibot.Error("Title contains illegal char (\\uFFFD)")
        self.namespace = defaultNamespace

        # Replace underscores by spaces
        t = t.replace(u"_", u" ")
        # replace multiple spaces and underscores with a single space
        while u"  " in t: t = t.replace(u"  ", u" ")
        # Strip spaces at both ends
        t = t.strip(" ")
        # Remove left-to-right and right-to-left markers.
        t = t.replace(u"\u200e", u"").replace(u"\u200f", u"")

        firstPass = True
        while u":" in t:
            # Initial colon indicates main namespace rather than default
            if t.startswith(u":"):
                self.namespace = 0
                # remove the colon but continue processing
                # remove any subsequent whitespace
                t = t.lstrip(u":").lstrip(u" ")
                continue

            fam = self.site.family
            prefix = t[ :t.index(u":")].lower()
            ns = self.site.getNamespaceIndex(prefix)
            if ns:
                # Ordinary namespace
                t = t[t.index(u":"): ].lstrip(u":").lstrip(u" ")
                self.namespace = ns
                break
            if prefix in fam.langs.keys()\
                   or prefix in fam.get_known_families(site=self.site):
                # looks like an interwiki link
                if not firstPass:
                    # Can't make a local interwiki link to an interwiki link.
                    raise pywikibot.Error(
                          "Improperly formatted interwiki link '%s'"
                          % text)
                t = t[t.index(u":"): ].lstrip(u":").lstrip(u" ")
                if prefix in fam.langs.keys():
                    newsite = pywikibot.Site(prefix, fam)
                else:
                    otherlang = self.site.code
                    familyName = fam.get_known_families(site=self.site)[prefix]
                    if familyName in ['commons', 'meta']:
                        otherlang = familyName
                    try:
                        newsite = pywikibot.Site(otherlang, familyName)
                    except ValueError:
                        raise pywikibot.Error("""\
%s is not a local page on %s, and the %s family is
not supported by PyWikiBot!"""
                              % (title, self.site(), familyName))

                # Redundant interwiki prefix to the local wiki
                if newsite == self.site:
                    if not t:
                        # Can't have an empty self-link
                        raise pywikibot.Error(
                              "Invalid link title: '%s'" % text)
                    firstPass = False
                    continue
                self.site = newsite
            else:
                break   # text before : doesn't match any known prefix

        if u"#" in t:
            t, sec = t.split(u'#', 1)
            t, self.section = t.rstrip(), sec.lstrip()
        else:
            self.section = None

        # Reject illegal characters.
        m = Link.illegal_titles_pattern.search(t)
        if m:
            raise pywikibot.Error(
                  u"Invalid title: contains illegal char(s) '%s'" % m.group(0))

        # Pages with "/./" or "/../" appearing in the URLs will
        # often be unreachable due to the way web browsers deal
        #* with 'relative' URLs. Forbid them explicitly.

        if u'.' in t and (
                t == u'.' or t == u'..'
                or t.startswith(u"./")
                or t.startswith(u"../")
                or u"/./" in t
                or u"/../" in t
                or t.endswith(u"/.")
                or t.endswith(u"/..")
        ):
            raise pywikibot.Error(
                  "Invalid title (contains . / combinations): '%s'"
                        % text)

        # Magic tilde sequences? Nu-uh!
        if u"~~~" in t:
            raise pywikibot.Error("Invalid title (contains ~~~): '%s'" % text)

        if self.namespace != -1 and len(t) > 255:
            raise pywikibot.Error("Invalid title (over 255 bytes): '%s'" % t)

        if self.site.case() == 'first-letter':
            t = t[:1].upper() + t[1:]

        # Can't make a link to a namespace alone...
        # "empty" local links can only be self-links
        # with a fragment identifier.
        if not t and self.site == self.source and self.namespace != 0:
            raise ValueError("Invalid link (no page title): '%s'" % text)

        self.title = t


# Utility functions for parsing page titles

def html2unicode(text, ignore = []):
    """Return text, replacing HTML entities by equivalent unicode characters."""
    # This regular expression will match any decimal and hexadecimal entity and
    # also entities that might be named entities.
    entityR = re.compile(
        r'&(#(?P<decimal>\d+)|#x(?P<hex>[0-9a-fA-F]+)|(?P<name>[A-Za-z]+));')
    # These characters are Html-illegal, but sadly you *can* find some of
    # these and converting them to unichr(decimal) is unsuitable
    convertIllegalHtmlEntities = {
        128 : 8364, # €
        130 : 8218, # ‚
        131 : 402,  # ƒ
        132 : 8222, # „
        133 : 8230, # …
        134 : 8224, # †
        135 : 8225, # ‡
        136 : 710,  # ˆ
        137 : 8240, # ‰
        138 : 352,  # Š
        139 : 8249, # ‹
        140 : 338,  # Œ
        142 : 381,  # Ž
        145 : 8216, # ‘
        146 : 8217, # ’
        147 : 8220, # “
        148 : 8221, # ”
        149 : 8226, # •
        150 : 8211, # –
        151 : 8212, # —
        152 : 732,  # ˜
        153 : 8482, # ™
        154 : 353,  # š
        155 : 8250, # ›
        156 : 339,  # œ
        158 : 382,  # ž
        159 : 376   # Ÿ
    }
    #ensuring that illegal &#129; &#141; and &#157, which have no known values,
    #don't get converted to unichr(129), unichr(141) or unichr(157)
    ignore = set(ignore) | set([129, 141, 157])
    result = u''
    i = 0
    found = True
    while found:
        text = text[i:]
        match = entityR.search(text)
        if match:
            unicodeCodepoint = None
            if match.group('decimal'):
                unicodeCodepoint = int(match.group('decimal'))
            elif match.group('hex'):
                unicodeCodepoint = int(match.group('hex'), 16)
            elif match.group('name'):
                name = match.group('name')
                if htmlentitydefs.name2codepoint.has_key(name):
                    # We found a known HTML entity.
                    unicodeCodepoint = htmlentitydefs.name2codepoint[name]
            result += text[:match.start()]
            try:
                unicodeCodepoint=convertIllegalHtmlEntities[unicodeCodepoint]
            except KeyError:
                pass
            if unicodeCodepoint and unicodeCodepoint not in ignore and (WIDEBUILD or unicodeCodepoint < 65534):
                result += unichr(unicodeCodepoint)
            else:
                # Leave the entity unchanged
                result += text[match.start():match.end()]
            i = match.end()
        else:
            result += text
            found = False
    return result

def url2unicode(title, site, site2 = None):
    """Convert url-encoded text to unicode using site's encoding.

    If site2 is provided, try its encodings as well.  Uses the first encoding
    that doesn't cause an error.

    """
    # create a list of all possible encodings for both hint sites
    encList = [site.encoding()] + list(site.encodings())
    if site2 and site2 <> site:
        encList.append(site2.encoding())
        encList += list(site2.encodings())
    firstException = None
    # try to handle all encodings (will probably retry utf-8)
    for enc in encList:
        try:
            t = title.encode(enc)
            t = urllib.unquote(t)
            return unicode(t, enc)
        except UnicodeError, ex:
            if not firstException:
                firstException = ex
            pass
    # Couldn't convert, raise the original exception
    raise firstException

