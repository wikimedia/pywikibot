"""**Pywikibot Exceptions** and warning classes.

This module contains all exception and warning classes used throughout
the framework::

    Exception
     +-- Error
          +-- AutoblockUser
          +-- CaptchaError
          +-- InvalidTitle
          +-- NoUsername
          +-- PageRelatedError
          |    +-- CircularRedirect
          |    +-- InterwikiRedirectPage
          |    +-- IsNotRedirectPage
          |    +-- IsRedirectPage
          |    +-- NoMoveTarget
          |    +-- NoPage
          |    +-- NotEmailableError
          |    +-- PageLoadRelatedError
          |    |    +-- InconsistentTitleReceived
          |    +-- PageSaveRelatedError
          |    |    +-- EditConflict
          |    |    |    +-- ArticleExistsConflict
          |    |    |    +-- PageCreatedConflict
          |    |    |    +-- PageDeletedConflict
          |    |    +-- LockedPage
          |    |    |    +-- LockedNoPage
          |    |    |    +-- CascadeLockedPage
          |    |    +-- NoCreateError
          |    |    +-- OtherPageSaveError
          |    |    +-- SpamblacklistError
          |    |    +-- TitleblacklistError
          |    +-- UnsupportedPage
          +-- SectionError
          +-- ServerError
          |    +-- FatalServerError
          |    +-- Server414Error
          |    +-- Server504Error
          +-- SiteDefinitionError
          |    +-- UnknownFamily
          |    +-- UnknownSite
          +-- TimeoutError
          |    +-- MaxlagTimeoutError
          +-- UserRightsError
          |    +-- HiddenKeyError (KeyError)
          +-- UnknownExtension (NotImplementedError)
          +-- WikiBaseError
               +-- CoordinateGlobeUnknownException (NotimplementedError)
               +-- EntityTypeUnknownException
               +-- NoWikibaseEntity

    UserWarning
     +-- ArgumentDeprecationWarning (FutureWarning)
     +-- FamilyMaintenanceWarning

    RuntimeWarning
     +-- NotImplementedWarning


Error: Base class, all exceptions should the subclass of this class.

  - NoUsername: Username is not in user-config.py, or it is invalid.
  - AutoblockUser: requested action on a virtual autoblock user not valid
  - UserRightsError: insufficient rights for requested action
  - InvalidTitle: Invalid page title
  - CaptchaError: Captcha is asked and config.solve_captcha == False
  - i18n.TranslationError: i18n/l10n message not available
  - UnknownExtension: Extension is not defined for this site
  - SectionError: The section specified by # does not exist

SiteDefinitionError: Site loading problem

  - UnknownSite: Site does not exist in Family
  - UnknownFamily: Family is not registered

PageRelatedError: any exception which is caused by an operation on a Page.

  - NoPage: Page does not exist
  - UnsupportedPage: Page is not supported due to a namespace restriction
  - IsRedirectPage: Page is a redirect page
  - IsNotRedirectPage: Page is not a redirect page
  - CircularRedirect: Page is a circular redirect
  - InterwikiRedirectPage: Page is a redirect to another site
  - NotEmailableError: The target user has disabled email
  - NoMoveTarget: An expected move target page does not exist

PageLoadRelatedError: any exception which happens while loading a Page.
  - InconsistentTitleReceived: Page receives a title inconsistent with query

PageSaveRelatedError: page exceptions within the save operation on a Page

  - SpamblacklistError: MediaWiki spam filter detected a blacklisted URL
  - TitleblacklistError: MediaWiki detected a blacklisted page title
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
  - Server414Error: Server timed out with HTTP 414 code
  - Server504Error: Server timed out with HTTP 504 code

WikiBaseError: any issue specific to Wikibase.

  - NoWikibaseEntity: entity doesn't exist
  - CoordinateGlobeUnknownException: globe is not implemented yet.
  - EntityTypeUnknownException: entity type is not available on the site.

TimeoutError: request failed with a timeout

  - MaxlagTimeoutError: request failed with a maxlag timeout

DeprecationWarning: old functionality replaced by new functionality

PendingDeprecationWarning: problematic code which has not yet been
fully deprecated, possibly because a replacement is not available

RuntimeWarning: problems developers should have fixed, and users need to
be aware of its status.

  - tools._NotImplementedWarning: do not use
  - NotImplementedWarning: functionality not implemented

UserWarning: warnings targeted at users

  - config2._ConfigurationDeprecationWarning: user configuration file problems
  - login._PasswordFileWarning: password file problems
  - ArgumentDeprecationWarning: command line argument problems
  - FamilyMaintenanceWarning: missing information in family definition
"""
#
# (C) Pywikibot team, 2008-2021
#
# Distributed under the terms of the MIT license.
#
import re

from typing import Optional, Union

from pywikibot.tools import _NotImplementedWarning


class NotImplementedWarning(_NotImplementedWarning):

    """Feature that is no longer implemented."""

    pass


class ArgumentDeprecationWarning(UserWarning, FutureWarning):

    """Command line argument that is no longer supported."""

    pass


class FamilyMaintenanceWarning(UserWarning):

    """Family class is missing definitions."""

    pass


class Error(Exception):

    """Pywikibot error."""

    def __init__(self, arg: str):
        """Initializer."""
        self.unicode = arg

    def __str__(self) -> str:
        """Return a string representation."""
        return self.unicode


class PageRelatedError(Error):

    """
    Abstract Exception, used when the exception concerns a particular Page.

    This class should be used when the Exception concerns a particular
    Page, and when a generic message can be written once for all.
    """

    # Preformatted message where the page title will be inserted.
    # Override this in subclasses.
    message = ''

    def __init__(self, page, message: Optional[str] = None):
        """
        Initializer.

        @param page: Page that caused the exception
        @type page: Page object
        """
        if message:
            self.message = message

        if self.message is None:
            raise Error("PageRelatedError is abstract. Can't instantiate it!")

        self.page = page
        self.title = page.title(as_link=True)
        self.site = page.site

        if re.search(r'%\(\w+\)s', self.message):
            values = self.__dict__
        else:
            values = page
        super().__init__(self.message % values)


class PageSaveRelatedError(PageRelatedError):

    """Saving the page has failed."""

    message = 'Page %s was not saved.'


class OtherPageSaveError(PageSaveRelatedError):

    """Saving the page has failed due to uncatchable error."""

    message = 'Edit to page %(title)s failed:\n%(reason)s'

    def __init__(self, page, reason: Union[str, Exception]):
        """Initializer.

        @param reason: Details of the problem
        """
        self.reason = reason
        super().__init__(page)

    @property
    def args(self):
        """Expose args."""
        return str(self.reason)


class NoUsername(Error):

    """Username is not in user-config.py."""

    pass


class NoPage(PageRelatedError):

    """Page does not exist."""

    message = "Page %s doesn't exist."


class UnsupportedPage(PageRelatedError):

    """Unsupported page due to namespace restriction."""

    # namespaces < 0 aren't supported (T169213)
    message = 'Page %s is not supported due to namespace restriction.'


class NoMoveTarget(PageRelatedError):

    """Expected move target page not found."""

    message = 'Move target page of %s not found.'


class PageLoadRelatedError(PageRelatedError):

    """Loading the contents of a Page object has failed."""

    message = 'Page %s was not loaded.'


class InconsistentTitleReceived(PageLoadRelatedError):

    """Page receives a title inconsistent with query."""

    def __init__(self, page, actual: str):
        """Initializer.

        @param page: Page that caused the exception
        @type page: Page object
        @param actual: title obtained by query

        """
        self.message = "Query on %s returned data on '{0}'".format(actual)
        super().__init__(page)


class SiteDefinitionError(Error):

    """Site does not exist."""

    pass


class UnknownSite(SiteDefinitionError):

    """Site does not exist in Family."""

    pass


class UnknownFamily(SiteDefinitionError):

    """Family is not registered."""

    pass


class UnknownExtension(Error, NotImplementedError):

    """Extension is not defined."""

    pass


class IsRedirectPage(PageRelatedError):

    """Page is a redirect page."""

    message = 'Page %s is a redirect page.'


class IsNotRedirectPage(PageRelatedError):

    """Page is not a redirect page."""

    message = 'Page %s is not a redirect page.'


class CircularRedirect(PageRelatedError):

    """Page is a circular redirect.

    Exception argument is the redirect target; this may be the same title
    as this page or a different title (in which case the target page directly
    or indirectly redirects back to this one)

    """

    message = 'Page %s is a circular redirect.'


class InterwikiRedirectPage(PageRelatedError):

    """
    Page is a redirect to another site.

    This is considered invalid in Pywikibot. See bug T75184.

    """

    message = ('Page redirects to a page on another Site.\n'
               'Page: %(page)s\n'
               'Target page: %(target_page)s on %(target_site)s.')

    def __init__(self, page, target_page):
        """Initializer.

        @param target_page: Target page of the redirect.
        @type target_page: Page
        """
        self.target_page = target_page
        self.target_site = target_page.site
        super().__init__(page)


class InvalidTitle(Error):

    """Invalid page title."""

    pass


class LockedPage(PageSaveRelatedError):

    """Page is locked."""

    message = 'Page %s is locked.'


class LockedNoPage(LockedPage):

    """Title is locked against creation."""

    message = 'Page %s does not exist and is locked preventing creation.'


class CascadeLockedPage(LockedPage):

    """Page is locked due to cascading protection."""

    message = 'Page %s is locked due to cascading protection.'


class SectionError(Error):

    """The section specified by # does not exist."""

    pass


class NoCreateError(PageSaveRelatedError):

    """Parameter nocreate doesn't allow page creation."""

    message = 'Page %s could not be created due to parameter nocreate'


class EditConflict(PageSaveRelatedError):

    """There has been an edit conflict while uploading the page."""

    message = 'Page %s could not be saved due to an edit conflict'


class PageDeletedConflict(EditConflict):

    """Page was deleted since being retrieved."""

    message = 'Page %s has been deleted since last retrieved.'


class PageCreatedConflict(EditConflict):

    """Page was created by another user."""

    message = 'Page %s has been created since last retrieved.'


class ArticleExistsConflict(EditConflict):

    """Page already exists."""

    message = ('Destination article %s already exists and is not a redirect '
               'to the source article')


class SpamblacklistError(PageSaveRelatedError):

    """Page save failed because MediaWiki detected a blacklisted spam URL."""

    message = ('Edit to page %(title)s rejected by spam filter due to '
               'content:\n%(url)s')

    def __init__(self, page, url):
        """Initializer."""
        self.url = url
        super().__init__(page)


class TitleblacklistError(PageSaveRelatedError):

    """Page save failed because MediaWiki detected a blacklisted page title."""

    message = 'Page %s is title-blacklisted.'


class ServerError(Error):

    """Got unexpected server response."""

    pass


class FatalServerError(ServerError):

    """A fatal server error will not be corrected by resending the request."""

    pass


class Server504Error(ServerError):

    """Server timed out with HTTP 504 code."""

    pass


class Server414Error(ServerError):

    """Server returned with HTTP 414 code."""

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


class HiddenKeyError(UserRightsError, KeyError):

    """Insufficient user rights to view the hidden key."""

    pass


class NotEmailableError(PageRelatedError):

    """This user is not emailable."""

    message = '%s is not emailable.'


class WikiBaseError(Error):

    """Wikibase related error."""

    pass


class NoWikibaseEntity(WikiBaseError):

    """This entity doesn't exist."""

    def __init__(self, entity):
        """
        Initializer.

        @param entity: Wikibase entity
        @type entity: WikibaseEntity
        """
        super().__init__("Entity '%s' doesn't exist on %s"
                         % (entity.id, entity.repo))
        self.entity = entity


class CoordinateGlobeUnknownException(WikiBaseError, NotImplementedError):

    """This globe is not implemented yet in either WikiBase or pywikibot."""

    pass


class EntityTypeUnknownException(WikiBaseError):

    """The requested entity type is not recognised on this site."""

    pass


class TimeoutError(Error):

    """Request failed with a timeout error."""

    pass


class MaxlagTimeoutError(TimeoutError):

    """Request failed with a maxlag timeout error."""

    pass
