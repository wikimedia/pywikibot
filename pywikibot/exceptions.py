# -*- coding: utf-8  -*-
"""
Exception classes used throughout the framework.
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


from pywikibot import config

# TODO: These are copied from wikipedia.py; not certain that all of them
# will be needed in the rewrite.

class Error(Exception):
    """Wikipedia error"""
    def __init__(self, arg):
        self.unicode = arg
        try:
            self.string = arg.encode(config.console_encoding, "xmlcharrefreplace")
        except (AttributeError, TypeError):
            self.string = arg.encode("ascii", "xmlcharrefreplace")
    def __str__(self):
        return self.string
    def __unicode__(self):
        return self.unicode

class PageRelatedError(Error):
    """Abstract Exception, used when the Exception concerns a particular
    Page, and when a generic message can be written once for all"""
    # Preformated UNICODE message where the page title will be inserted
    # Override this in subclasses.
    # u"Oh noes! Page %s is too funky, we should not delete it ;("
    message = None
    def __init__(self, page):
        """
        @param page
        @type page: Page object
        """
        if self.message is None:
            raise Error("PageRelatedError is abstract. Can't instantiate it!")
        super(PageRelatedError, self).__init__(self.message % page)
        self._page = page

    def getPage(self):
        return self._page

class NoUsername(Error):
    """Username is not in user-config.py"""

class NoPage(PageRelatedError):
    """Page does not exist"""
    message = u"Page %s doesn't exist."

class NoSuchSite(Error):
    """Site does not exist"""

class IsRedirectPage(PageRelatedError):
    """Page is a redirect page"""
    message = u"Page %s is a redirect page."

class IsNotRedirectPage(PageRelatedError):
    """Page is not a redirect page"""
    message = u"Page %s is not a redirect page."

class CircularRedirect(Error):
    """Page is a circular redirect

    Exception argument is the redirect target; this may be the same title
    as this page or a different title (in which case the target page directly
    or indirectly redirects back to this one)

    """

class InvalidTitle(Error):
    """Invalid page title"""

class LockedPage(PageRelatedError):
    """Page is locked"""
    message = u"Page %s is locked."

class SectionError(Error):
    """The section specified by # does not exist"""

class PageNotSaved(Error):
    """Saving the page has failed"""

class EditConflict(PageNotSaved):
    """There has been an edit conflict while uploading the page"""

class SpamfilterError(PageNotSaved):
    """Saving the page has failed because the MediaWiki spam filter detected a blacklisted URL."""
    def __init__(self, arg):
        super(SpamfilterError, self).__init__(u'MediaWiki spam filter has been triggered')
        self.url = arg
        self.args = arg,

class ServerError(Error):
    """Got unexpected server response"""

class Server504Error(Error):
    """Server timed out with http 504 code"""

class BadTitle(Error):
    """Server responded with BadTitle."""

# UserBlocked exceptions should in general not be caught. If the bot has
# been blocked, the bot operator should address the reason for the block
# before continuing.
class UserBlocked(Error):
    """Your username or IP has been blocked"""

class PageNotFound(Error):
    """Page not found in list"""

class CaptchaError(Error):
    """Captcha is asked and config.solve_captcha == False."""

class UploadWarning(Error):
    """Upload failed with a warning message (passed as the argument)."""

class AutoblockUser(Error):
    """
    The class AutoblockUserError is an exception that is raised whenever
    an action is requested on a virtual autoblock user that's not available
    for him (i.e. roughly everything except unblock).
    """
class UserActionRefuse(Error):
    pass
