# -*- coding: utf-8  -*-
"""
Exception and warning classes used throughout the framework.

Error: Base class, all exceptions should the subclass of this class.
  - NoUsername: Username is not in user-config.py, or it is invalid.
  - UserBlocked: Username or IP has been blocked
  - AutoblockUser: requested action on a virtual autoblock user not valid
  - UserRightsError: insufficient rights for requested action
  - BadTitle: Server responded with BadTitle
  - InvalidTitle: Invalid page title
  - CaptchaError: Captcha is asked and config.solve_captcha == False
  - Server504Error: Server timed out with HTTP 504 code
  - PageNotFound: Page not found (deprecated)
  - i18n.TranslationError: i18n/l10n message not available
  - UnknownExtension: Extension is not defined for this site

SiteDefinitionError: Site loading problem
  - UnknownSite: Site does not exist in Family
  - UnknownFamily: Family is not registered

PageRelatedError: any exception which is caused by an operation on a Page.
  - NoPage: Page does not exist
  - IsRedirectPage: Page is a redirect page
  - IsNotRedirectPage: Page is not a redirect page
  - CircularRedirect: Page is a circular redirect
  - InterwikiRedirectPage: Page is a redirect to another site
  - SectionError: The section specified by # does not exist
  - NotEmailableError: The target user has disabled email

PageSaveRelatedError: page exceptions within the save operation on a Page
(alias: PageNotSaved).
  - SpamfilterError: MediaWiki spam filter detected a blacklisted URL
  - OtherPageSaveError: misc. other save related exception.
  - LockedPage: Page is locked
      - LockedNoPage: Title is locked against creation
      - CascadeLockedPage: Page is locked due to cascading protection
  - EditConflict: Edit conflict while uploading the page
      - PageDeletedConflict: Page was deleted since being retrieved
      - PageCreatedConflict: Page was created by another user
      - ArticleExistsConflict: Page article already exists
  - NoCreateError: parameter nocreate not allow page creation

ServerError: a problem with the server.
  - FatalServerError: A fatal/non-recoverable server error

WikiBaseError: any issue specific to Wikibase.
  - CoordinateGlobeUnknownException: globe is not implemented yet.
  - EntityTypeUnknownException: entity type is not available on the site.

DeprecationWarning: old functionality replaced by new functionality

PendingDeprecationWarning: problematic code which has not yet been
    fully deprecated, possibly because a replacement is not available

RuntimeWarning: problems developers should have fixed, and users need to
    be aware of its status.
  - tools._NotImplementedWarning: do not use
  - NotImplementedWarning: functionality not implemented

UserWarning: warnings targetted at users
  - config2._ConfigurationDeprecationWarning: user configuration file problems
  - login._PasswordFileWarning: password file problems
  - ArgumentDeprecationWarning: command line argument problems
  - FamilyMaintenanceWarning: missing information in family definition
"""
#
# (C) Pywikibot team, 2008
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import sys

from pywikibot.tools import UnicodeMixin, _NotImplementedWarning

if sys.version_info[0] > 2:
    unicode = str


class NotImplementedWarning(_NotImplementedWarning):

    """Feature that is no longer implemented."""

    pass


class ArgumentDeprecationWarning(UserWarning):

    """Command line argument that is no longer supported."""

    pass


class FamilyMaintenanceWarning(UserWarning):

    """Family class is missing definitions."""

    pass


class Error(UnicodeMixin, Exception):  # noqa

    """Pywikibot error"""

    # NOTE: UnicodeMixin must be the first object Error class is derived from.
    def __init__(self, arg):
        """Constructor."""
        self.unicode = arg

    def __unicode__(self):
        """Return a unicode string representation."""
        return self.unicode


class PageRelatedError(Error):

    """
    Abstract Exception, used when the exception concerns a particular Page.

    This class should be used when the Exception concerns a particular
    Page, and when a generic message can be written once for all.
    """

    # Preformatted UNICODE message where the page title will be inserted
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
        """Return the page related to the exception."""
        return self.page


class PageSaveRelatedError(PageRelatedError):  # noqa

    """Saving the page has failed"""

    message = u"Page %s was not saved."

    # This property maintains backwards compatibility with
    # the old PageNotSaved which inherited from Error
    # (not PageRelatedError) and exposed the normal 'args'
    # which could be printed
    @property
    def args(self):
        """Expose args."""
        return unicode(self)


class OtherPageSaveError(PageSaveRelatedError):

    """Saving the page has failed due to uncatchable error."""

    message = "Edit to page %(title)s failed:\n%(reason)s"

    def __init__(self, page, reason):
        """Constructor.

        @param reason: Details of the problem
        @type reason: Exception or basestring
        """
        self.reason = reason
        super(OtherPageSaveError, self).__init__(page)

    @property
    def args(self):
        """Expose args."""
        return unicode(self.reason)


class NoUsername(Error):

    """Username is not in user-config.py."""

    pass


class NoPage(PageRelatedError):  # noqa

    """Page does not exist"""

    message = u"Page %s doesn't exist."

    pass


class SiteDefinitionError(Error):  # noqa

    """Site does not exist"""

    pass


# The name 'NoSuchSite' was used for all site related issues,
# and it used message "Site does not exist".
# These are retain for backwards compatibility with scripts.
NoSuchSite = SiteDefinitionError


class UnknownSite(SiteDefinitionError):  # noqa

    """Site does not exist in Family"""

    pass


class UnknownFamily(SiteDefinitionError):  # noqa

    """Family is not registered"""

    pass


class UnknownExtension(Error, NotImplementedError):

    """Extension is not defined."""

    pass


class IsRedirectPage(PageRelatedError):  # noqa

    """Page is a redirect page"""

    message = u"Page %s is a redirect page."

    pass


class IsNotRedirectPage(PageRelatedError):  # noqa

    """Page is not a redirect page"""

    message = u"Page %s is not a redirect page."

    pass


class CircularRedirect(PageRelatedError):

    """Page is a circular redirect.

    Exception argument is the redirect target; this may be the same title
    as this page or a different title (in which case the target page directly
    or indirectly redirects back to this one)

    """

    message = u"Page %s is a circular redirect."


class InterwikiRedirectPage(PageRelatedError):

    """
    Page is a redirect to another site.

    This is considered invalid in Pywikibot. See Bug 73184.

    """

    message = (u"Page redirects to a page on another Site.\n"
               u"Page: %(page)s\n"
               u"Target page: %(target_page)s on %(target_site)s.")

    def __init__(self, page, target_page):
        """Constructor.

        @param target_page: Target page of the redirect.
        @type reason: Page
        """
        self.target_page = target_page
        self.target_site = target_page.site
        super(InterwikiRedirectPage, self).__init__(page)


class InvalidTitle(Error):  # noqa

    """Invalid page title"""

    pass


class LockedPage(PageSaveRelatedError):  # noqa

    """Page is locked"""

    message = u"Page %s is locked."

    pass


class LockedNoPage(LockedPage):  # noqa

    """Title is locked against creation"""

    message = u"Page %s does not exist and is locked preventing creation."

    pass


class CascadeLockedPage(LockedPage):  # noqa

    """Page is locked due to cascading protection"""

    message = u"Page %s is locked due to cascading protection."

    pass


class SectionError(Error):  # noqa

    """The section specified by # does not exist"""

    pass


PageNotSaved = PageSaveRelatedError


class NoCreateError(PageSaveRelatedError):

    """Parameter nocreate doesn't allow page creation."""

    message = u"Page %s could not be created due to parameter nocreate"

    pass


class EditConflict(PageSaveRelatedError):  # noqa

    """There has been an edit conflict while uploading the page"""

    message = u"Page %s could not be saved due to an edit conflict"

    pass


class PageDeletedConflict(EditConflict):  # noqa

    """Page was deleted since being retrieved"""

    message = u"Page %s has been deleted since last retrieved."

    pass


class PageCreatedConflict(EditConflict):  # noqa

    """Page was created by another user"""

    message = u"Page %s has been created since last retrieved."

    pass


class ArticleExistsConflict(EditConflict):

    """Page already exists."""

    message = u"Destination article %s already exists and is not a redirect to the source article"

    pass


class SpamfilterError(PageSaveRelatedError):

    """Page save failed because MediaWiki detected a blacklisted spam URL."""

    message = "Edit to page %(title)s rejected by spam filter due to content:\n%(url)s"

    def __init__(self, page, url):
        """Constructor."""
        self.url = url
        super(SpamfilterError, self).__init__(page)


class ServerError(Error):  # noqa

    """Got unexpected server response"""

    pass


class FatalServerError(ServerError):

    """A fatal server error will not be corrected by resending the request."""

    pass


class Server504Error(Error):  # noqa

    """Server timed out with HTTP 504 code"""

    pass


class Server414Error(Error):

    """Server returned with HTTP 414 code."""

    pass


class BadTitle(Error):

    """Server responded with BadTitle."""

# UserBlocked exceptions should in general not be caught. If the bot has
# been blocked, the bot operator should address the reason for the block
# before continuing.

    pass


class UserBlocked(Error):  # noqa

    """Your username or IP has been blocked"""

    pass


class CaptchaError(Error):

    """Captcha is asked and config.solve_captcha == False."""

    pass


class AutoblockUser(Error):

    """Requested action on a virtual autoblock user not valid.

    The class AutoblockUserError is an exception that is raised whenever
    an action is requested on a virtual autoblock user that's not available
    for him (i.e. roughly everything except unblock).
    """

    pass


class UserRightsError(Error):

    """Insufficient user rights to perform an action."""

    pass


class NotEmailableError(PageRelatedError):

    """This user is not emailable."""

    message = "%s is not emailable."

    pass


class WikiBaseError(Error):

    """Wikibase related error."""

    pass


class CoordinateGlobeUnknownException(WikiBaseError, NotImplementedError):

    """This globe is not implemented yet in either WikiBase or pywikibot."""

    pass


class EntityTypeUnknownException(WikiBaseError):

    """The requested entity type is not recognised on this site."""

    pass


import pywikibot.data.api
import pywikibot.tools


@pywikibot.tools.deprecated
class DeprecatedPageNotFoundError(Error):

    """Page not found (deprecated)."""

    pass


@pywikibot.tools.deprecated
class _EmailUserError(UserRightsError, NotEmailableError):

    """Email related error."""

    pass


wrapper = pywikibot.tools.ModuleDeprecationWrapper(__name__)
wrapper._add_deprecated_attr('UploadWarning', pywikibot.data.api.UploadWarning)
wrapper._add_deprecated_attr('PageNotFound', DeprecatedPageNotFoundError,
                             warning_message='{0}.{1} is deprecated, and no '
                                             'longer used by pywikibot; use '
                                             'http.fetch() instead.')
wrapper._add_deprecated_attr(
    'UserActionRefuse', _EmailUserError,
    warning_message='UserActionRefuse is deprecated; '
                    'use UserRightsError and/or NotEmailableError')
