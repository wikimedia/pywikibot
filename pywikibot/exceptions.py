# -*- coding: utf-8  -*-
"""
Exception classes used throughout the framework.

Error: Base class, all exceptions should the subclass of this class.
  - NoUsername: Username is not in user-config.py
  - UserBlockedY: our username or IP has been blocked
  - AutoblockUser: requested action on a virtual autoblock user not valid
  - UserActionRefuse
  - NoSuchSite: Site does not exist
  - BadTitle: Server responded with BadTitle
  - InvalidTitle: Invalid page title
  - PageNotFound: Page not found in list
  - CaptchaError: Captcha is asked and config.solve_captcha == False
  - Server504Error: Server timed out with HTTP 504 code

PageRelatedError: any exception which is caused by an operation on a Page.
  - NoPage: Page does not exist
  - IsRedirectPage: Page is a redirect page
  - IsNotRedirectPage: Page is not a redirect page
  - CircularRedirect: Page is a circular redirect
  - SectionError: The section specified by # does not exist
  - LockedPage: Page is locked
      - LockedNoPage: Title is locked against creation
      - CascadeLockedPage: Page is locked due to cascading protection

PageSaveRelatedError: page exceptions within the save operation on a Page.
  (alias: PageNotSaved)
  - SpamfilterError: MediaWiki spam filter detected a blacklisted URL
  - OtherPageSaveError: misc. other save related exception.
  - EditConflict: Edit conflict while uploading the page
      - PageDeletedConflict: Page was deleted since being retrieved
      - PageCreatedConflict: Page was created by another user

ServerError: a problem with the server.
  - FatalServerError: A fatal/non-recoverable server error

WikiBaseError: any issue specific to Wikibase.
  - CoordinateGlobeUnknownException: globe is not implemented yet.

"""
#
# (C) Pywikibot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


from pywikibot.tools import UnicodeMixin

# TODO: These are copied from wikipedia.py; not certain that all of them
# will be needed in the rewrite.


class Error(UnicodeMixin, Exception):

    """Pywikibot error"""
    # NOTE: UnicodeMixin must be the first object Error class is derived from.
    def __init__(self, arg):
        self.unicode = arg

    def __unicode__(self):
        return self.unicode


class PageRelatedError(Error):

    """
    Abstract Exception, used when the exception concerns a particular Page.
    """

    # Preformated UNICODE message where the page title will be inserted
    # Override this in subclasses.
    # u"Oh noes! Page %s is too funky, we should not delete it ;("
    message = None

    def __init__(self, page, message=None):
        """
        Constructor.

        @param page: Page that caused the exception
        @type page: Page object
        """
        if message:
            self.message = message

        if self.message is None:
            raise Error("PageRelatedError is abstract. Can't instantiate it!")

        self.page = page
        self.title = page.title(asLink=True)
        self.site = page.site

        if '%(' in self.message and ')s' in self.message:
            super(PageRelatedError, self).__init__(self.message % self.__dict__)
        else:
            super(PageRelatedError, self).__init__(self.message % page)

    def getPage(self):
        return self._page


class PageSaveRelatedError(PageRelatedError):

    """Saving the page has failed"""
    message = u"Page %s was not saved."

    # This property maintains backwards compatibility with
    # the old PageNotSaved which inherited from Error
    # (not PageRelatedError) and exposed the normal 'args'
    # which could be printed
    @property
    def args(self):
        return unicode(self)


class OtherPageSaveError(PageSaveRelatedError):

    """Saving the page has failed due to uncatchable error."""
    message = "Edit to page %(title)s failed:\n%(reason)s"

    def __init__(self, page, reason):
        """ Constructor.

        @param reason: Details of the problem
        @type reason: Exception or basestring
        """
        self.reason = reason
        super(OtherPageSaveError, self).__init__(page)

    @property
    def args(self):
        return unicode(self.reason)


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


class CircularRedirect(PageRelatedError):

    """Page is a circular redirect

    Exception argument is the redirect target; this may be the same title
    as this page or a different title (in which case the target page directly
    or indirectly redirects back to this one)

    """
    message = u"Page %s is a circular redirect."


class InvalidTitle(Error):

    """Invalid page title"""


class LockedPage(PageSaveRelatedError):

    """Page is locked"""
    message = u"Page %s is locked."


class LockedNoPage(LockedPage):

    """Title is locked against creation"""
    message = u"Page %s does not exist and is locked preventing creation."


class CascadeLockedPage(LockedPage):

    """Page is locked due to cascading protection"""
    message = u"Page %s is locked due to cascading protection."


class SectionError(Error):

    """The section specified by # does not exist"""


PageNotSaved = PageSaveRelatedError


class EditConflict(PageSaveRelatedError):

    """There has been an edit conflict while uploading the page"""
    message = u"Page %s could not be saved due to an edit conflict"


class PageDeletedConflict(EditConflict):

    """Page was deleted since being retrieved"""
    message = u"Page %s has been deleted since last retrieved."


class PageCreatedConflict(EditConflict):

    """Page was created by another user"""
    message = u"Page %s has been created since last retrieved."


class SpamfilterError(PageSaveRelatedError):

    """Saving the page has failed because the MediaWiki spam filter detected a
    blacklisted URL.
    """

    message = "Edit to page %(title)s rejected by spam filter due to content:\n%(url)s"

    def __init__(self, page, url):
        self.url = url
        super(SpamfilterError, self).__init__(page)


class ServerError(Error):

    """Got unexpected server response"""


class FatalServerError(ServerError):

    """A fatal server error that's not going to be corrected by just sending
    the request again."""


class Server504Error(Error):

    """Server timed out with HTTP 504 code"""


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


class AutoblockUser(Error):

    """
    The class AutoblockUserError is an exception that is raised whenever
    an action is requested on a virtual autoblock user that's not available
    for him (i.e. roughly everything except unblock).
    """


class UserActionRefuse(Error):
    pass


class WikiBaseError(Error):
    pass


class CoordinateGlobeUnknownException(WikiBaseError, NotImplementedError):

    """ This globe is not implemented yet in either WikiBase or pywikibot """

# TODO: Warn about the deprecated usage
import pywikibot.data.api
UploadWarning = pywikibot.data.api.UploadWarning
