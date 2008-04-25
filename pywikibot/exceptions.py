# -*- coding: utf-8  -*-
"""
Exception classes used throughout the framework.
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'


# TODO: These are copied from wikipedia.py; not certain that all of them
# will be needed in the rewrite.

class Error(Exception):
    """Wikipedia error"""

class NoUsername(Error):
    """Username is not in user-config.py"""

class NoPage(Error):
    """Page does not exist"""

class NoSuchSite(Error):
    """Site does not exist"""

class IsRedirectPage(Error):
    """Page is a redirect page"""

class IsNotRedirectPage(Error):
    """Page is not a redirect page"""

class CircularRedirect(Error):
    """Page is a circular redirect

    Exception argument is the redirect target; this may be the same title
    as this page or a different title (in which case the target page directly
    or indirectly redirects back to this one)

    """

class LockedPage(Error):
    """Page is locked"""

class SectionError(Error):
    """The section specified by # does not exist"""

class PageNotSaved(Error):
    """Saving the page has failed"""

class EditConflict(PageNotSaved):
    """There has been an edit conflict while uploading the page"""

class SpamfilterError(PageNotSaved):
    """Saving the page has failed because the MediaWiki spam filter detected a blacklisted URL."""
    def __init__(self, arg):
        self.url = arg
        self.args = arg,

class ServerError(Error):
    """Got unexpected server response"""

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

