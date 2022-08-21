"""Object representing a Wiki user."""
#
# (C) Pywikibot team, 2009-2022
#
# Distributed under the terms of the MIT license.
#
from typing import Optional

import pywikibot
from pywikibot.backports import Iterable, Tuple
from pywikibot.exceptions import (
    APIError,
    AutoblockUserError,
    NotEmailableError,
    UserRightsError,
)
from pywikibot.page._links import Link
from pywikibot.page._pages import Page
from pywikibot.page._revision import Revision
from pywikibot.tools import deprecated, is_ip_address


__all__ = ('User', )


class User(Page):

    """
    A class that represents a Wiki user.

    This class also represents the Wiki page User:<username>
    """

    def __init__(self, source, title: str = '') -> None:
        """
        Initializer for a User object.

        All parameters are the same as for Page() Initializer.
        """
        self._isAutoblock = True
        if title.startswith('#'):
            title = title[1:]
        elif ':#' in title:
            title = title.replace(':#', ':')
        else:
            self._isAutoblock = False
        super().__init__(source, title, ns=2)
        if self.namespace() != 2:
            raise ValueError("'{}' is not in the user namespace!"
                             .format(self.title()))
        if self._isAutoblock:
            # This user is probably being queried for purpose of lifting
            # an autoblock.
            pywikibot.output(
                'This is an autoblock ID, you can only use to unblock it.')

    @property
    def username(self) -> str:
        """
        The username.

        Convenience method that returns the title of the page with
        namespace prefix omitted, which is the username.
        """
        if self._isAutoblock:
            return '#' + self.title(with_ns=False)
        return self.title(with_ns=False)

    def isRegistered(self, force: bool = False) -> bool:  # noqa: N802
        """
        Determine if the user is registered on the site.

        It is possible to have a page named User:xyz and not have
        a corresponding user with username xyz.

        The page does not need to exist for this method to return
        True.

        :param force: if True, forces reloading the data from API
        """
        # T135828: the registration timestamp may be None but the key exists
        return (not self.isAnonymous()
                and 'registration' in self.getprops(force))

    def isAnonymous(self) -> bool:  # noqa: N802
        """Determine if the user is editing as an IP address."""
        return is_ip_address(self.username)

    def getprops(self, force: bool = False) -> dict:
        """
        Return a properties about the user.

        :param force: if True, forces reloading the data from API
        """
        if force and hasattr(self, '_userprops'):
            del self._userprops
        if not hasattr(self, '_userprops'):
            self._userprops = list(self.site.users([self.username, ]))[0]
            if self.isAnonymous():
                r = list(self.site.blocks(iprange=self.username, total=1))
                if r:
                    self._userprops['blockedby'] = r[0]['by']
                    self._userprops['blockreason'] = r[0]['reason']
        return self._userprops

    def registration(self,
                     force: bool = False) -> Optional[pywikibot.Timestamp]:
        """
        Fetch registration date for this user.

        :param force: if True, forces reloading the data from API
        """
        if not self.isAnonymous():
            reg = self.getprops(force).get('registration')
            if reg:
                return pywikibot.Timestamp.fromISOformat(reg)
        return None

    def editCount(self, force: bool = False) -> int:  # noqa: N802
        """
        Return edit count for a registered user.

        Always returns 0 for 'anonymous' users.

        :param force: if True, forces reloading the data from API
        """
        return self.getprops(force).get('editcount', 0)

    def is_blocked(self, force: bool = False) -> bool:
        """Determine whether the user is currently blocked.

        .. versionchanged:: 7.0
           renamed from :meth:`isBlocked` method,
           can also detect range blocks.

        :param force: if True, forces reloading the data from API
        """
        return 'blockedby' in self.getprops(force)

    @deprecated('is_blocked', since='7.0.0')
    def isBlocked(self, force: bool = False) -> bool:  # noqa: N802
        """Determine whether the user is currently blocked.

        .. deprecated:: 7.0
           use :meth:`is_blocked` instead

        :param force: if True, forces reloading the data from API
        """
        return self.is_blocked(force)

    def is_locked(self, force: bool = False) -> bool:
        """Determine whether the user is currently locked globally.

        .. versionadded:: 7.0

        :param force: if True, forces reloading the data from API
        """
        return self.site.is_locked(self.username, force)

    def isEmailable(self, force: bool = False) -> bool:  # noqa: N802
        """
        Determine whether emails may be send to this user through MediaWiki.

        :param force: if True, forces reloading the data from API
        """
        return not self.isAnonymous() and 'emailable' in self.getprops(force)

    def groups(self, force: bool = False) -> list:
        """
        Return a list of groups to which this user belongs.

        The list of groups may be empty.

        :param force: if True, forces reloading the data from API
        :return: groups property
        """
        return self.getprops(force).get('groups', [])

    def gender(self, force: bool = False) -> str:
        """Return the gender of the user.

        :param force: if True, forces reloading the data from API
        :return: return 'male', 'female', or 'unknown'
        """
        if self.isAnonymous():
            return 'unknown'
        return self.getprops(force).get('gender', 'unknown')

    def rights(self, force: bool = False) -> list:
        """Return user rights.

        :param force: if True, forces reloading the data from API
        :return: return user rights
        """
        return self.getprops(force).get('rights', [])

    def getUserPage(self, subpage: str = '') -> Page:  # noqa: N802
        """
        Return a Page object relative to this user's main page.

        :param subpage: subpage part to be appended to the main
                            page title (optional)
        :return: Page object of user page or user subpage
        """
        if self._isAutoblock:
            # This user is probably being queried for purpose of lifting
            # an autoblock, so has no user pages per se.
            raise AutoblockUserError(
                'This is an autoblock ID, you can only use to unblock it.')
        if subpage:
            subpage = '/' + subpage
        return Page(Link(self.title() + subpage, self.site))

    def getUserTalkPage(self, subpage: str = '') -> Page:  # noqa: N802
        """
        Return a Page object relative to this user's main talk page.

        :param subpage: subpage part to be appended to the main
                            talk page title (optional)
        :return: Page object of user talk page or user talk subpage
        """
        if self._isAutoblock:
            # This user is probably being queried for purpose of lifting
            # an autoblock, so has no user talk pages per se.
            raise AutoblockUserError(
                'This is an autoblock ID, you can only use to unblock it.')
        if subpage:
            subpage = '/' + subpage
        return Page(Link(self.username + subpage,
                         self.site, default_namespace=3))

    def send_email(self, subject: str, text: str, ccme: bool = False) -> bool:
        """
        Send an email to this user via MediaWiki's email interface.

        :param subject: the subject header of the mail
        :param text: mail body
        :param ccme: if True, sends a copy of this email to the bot
        :raises NotEmailableError: the user of this User is not emailable
        :raises UserRightsError: logged in user does not have 'sendemail' right
        :return: operation successful indicator
        """
        if not self.isEmailable():
            raise NotEmailableError(self)

        if not self.site.has_right('sendemail'):
            raise UserRightsError("You don't have permission to send mail")

        params = {
            'action': 'emailuser',
            'target': self.username,
            'token': self.site.tokens['email'],
            'subject': subject,
            'text': text,
        }
        if ccme:
            params['ccme'] = 1
        mailrequest = self.site.simple_request(**params)
        maildata = mailrequest.submit()

        if 'emailuser' in maildata \
           and maildata['emailuser']['result'] == 'Success':
            return True
        return False

    def block(self, *args, **kwargs):
        """
        Block user.

        Refer :py:obj:`APISite.blockuser` method for parameters.

        :return: None
        """
        try:
            self.site.blockuser(self, *args, **kwargs)
        except APIError as err:
            if err.code == 'invalidrange':
                raise ValueError('{} is not a valid IP range.'
                                 .format(self.username))

            raise err

    def unblock(self, reason: Optional[str] = None) -> None:
        """
        Remove the block for the user.

        :param reason: Reason for the unblock.
        """
        self.site.unblockuser(self, reason)

    def logevents(self, **kwargs):
        """Yield user activities.

        :keyword logtype: only iterate entries of this type
            (see mediawiki api documentation for available types)
        :type logtype: str
        :keyword page: only iterate entries affecting this page
        :type page: Page or str
        :keyword namespace: namespace to retrieve logevents from
        :type namespace: int or Namespace
        :keyword start: only iterate entries from and after this Timestamp
        :type start: Timestamp or ISO date string
        :keyword end: only iterate entries up to and through this Timestamp
        :type end: Timestamp or ISO date string
        :keyword reverse: if True, iterate oldest entries first
            (default: newest)
        :type reverse: bool
        :keyword tag: only iterate entries tagged with this tag
        :type tag: str
        :keyword total: maximum number of events to iterate
        :type total: int
        :rtype: iterable
        """
        return self.site.logevents(user=self.username, **kwargs)

    @property
    def last_event(self):
        """Return last user activity.

        :return: last user log entry
        :rtype: LogEntry or None
        """
        return next(self.logevents(total=1), None)

    def contributions(self, total: int = 500, **kwargs) -> tuple:
        """
        Yield tuples describing this user edits.

        Each tuple is composed of a pywikibot.Page object,
        the revision id (int), the edit timestamp (as a pywikibot.Timestamp
        object), and the comment (str).
        Pages returned are not guaranteed to be unique.

        :param total: limit result to this number of pages
        :keyword start: Iterate contributions starting at this Timestamp
        :keyword end: Iterate contributions ending at this Timestamp
        :keyword reverse: Iterate oldest contributions first (default: newest)
        :keyword namespaces: only iterate pages in these namespaces
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :keyword showMinor: if True, iterate only minor edits; if False and
            not None, iterate only non-minor edits (default: iterate both)
        :keyword top_only: if True, iterate only edits which are the latest
            revision (default: False)
        :return: tuple of pywikibot.Page, revid, pywikibot.Timestamp, comment
        """
        for contrib in self.site.usercontribs(
                user=self.username, total=total, **kwargs):
            ts = pywikibot.Timestamp.fromISOformat(contrib['timestamp'])
            yield (Page(self.site, contrib['title'], contrib['ns']),
                   contrib['revid'],
                   ts,
                   contrib.get('comment'))

    @property
    def first_edit(
        self
    ) -> Optional[Tuple[Page, int, pywikibot.Timestamp, str]]:
        """Return first user contribution.

        :return: first user contribution entry
        :return: tuple of pywikibot.Page, revid, pywikibot.Timestamp, comment
        """
        return next(self.contributions(reverse=True, total=1), None)

    @property
    def last_edit(
        self
    ) -> Optional[Tuple[Page, int, pywikibot.Timestamp, str]]:
        """Return last user contribution.

        :return: last user contribution entry
        :return: tuple of pywikibot.Page, revid, pywikibot.Timestamp, comment
        """
        return next(self.contributions(total=1), None)

    def deleted_contributions(
        self, *, total: int = 500, **kwargs
    ) -> Iterable[Tuple[Page, Revision]]:
        """Yield tuples describing this user's deleted edits.

        .. versionadded:: 5.5

        :param total: Limit results to this number of pages
        :keyword start: Iterate contributions starting at this Timestamp
        :keyword end: Iterate contributions ending at this Timestamp
        :keyword reverse: Iterate oldest contributions first (default: newest)
        :keyword namespaces: Only iterate pages in these namespaces
        """
        for data in self.site.alldeletedrevisions(user=self.username,
                                                  total=total, **kwargs):
            page = Page(self.site, data['title'], data['ns'])
            for contrib in data['revisions']:
                yield page, Revision(**contrib)

    def uploadedImages(self, total: int = 10):  # noqa: N802
        """
        Yield tuples describing files uploaded by this user.

        Each tuple is composed of a pywikibot.Page, the timestamp (str in
        ISO8601 format), comment (str) and a bool for pageid > 0.
        Pages returned are not guaranteed to be unique.

        :param total: limit result to this number of pages
        """
        if not self.isRegistered():
            return
        for item in self.logevents(logtype='upload', total=total):
            yield (item.page(),
                   str(item.timestamp()),
                   item.comment(),
                   item.pageid() > 0)

    @property
    def is_thankable(self) -> bool:
        """
        Determine if the user has thanks notifications enabled.

        .. note::
           This doesn't accurately determine if thanks is enabled for user.
           Privacy of thanks preferences is under discussion, please see
           :phab:`T57401#2216861` and :phab:`T120753#1863894`.
        """
        return self.isRegistered() and 'bot' not in self.groups()
