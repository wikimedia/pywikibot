"""Decorators used by site models."""
#
# (C) Pywikibot team, 2008-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import os
from textwrap import fill

from pywikibot.exceptions import UnknownExtensionError, UserRightsError
from pywikibot.tools import MediaWikiVersion, manage_wrapping


CLOSED_WIKI_MSG = (
    'Site {site} has been closed. Only steward can perform requested action.'
)


def must_be(group: str | None = None):
    """Decorator to require a certain user status when method is called.

    :param group: The group the logged in user should belong to.
                  This parameter can be overridden by
                  keyword argument 'as_group'.
    :return: method decorator
    :raises UserRightsError: user is not part of the required user group.
    """
    def decorator(fn):
        def callee(self, *args, **kwargs):
            grp = kwargs.pop('as_group', group)
            if self.obsolete:
                if not self.has_group('steward'):
                    raise UserRightsError(CLOSED_WIKI_MSG.format(site=self))

            elif not self.has_group(grp):
                raise UserRightsError(f'User "{self.user()}" is not part of '
                                      f'the required user group "{grp}"')

            return fn(self, *args, **kwargs)

        manage_wrapping(callee, fn)
        return callee

    return decorator


def need_extension(extension: str):
    """Decorator to require a certain MediaWiki extension.

    :param extension: the MediaWiki extension required
    :return: a decorator to make sure the requirement is satisfied when
        the decorated function is called.
    """
    def decorator(fn):
        def callee(self, *args, **kwargs):
            if not self.has_extension(extension):
                raise UnknownExtensionError(
                    f'Method "{fn.__name__}" is not implemented without the '
                    f'extension {extension}')
            return fn(self, *args, **kwargs)

        manage_wrapping(callee, fn)
        return callee

    return decorator


def need_right(right: str | None = None):
    """Decorator to require a certain user right when method is called.

    :param right: The right the logged in user should have.
    :return: method decorator
    :raises UserRightsError: user has insufficient rights.
    """
    def decorator(fn):
        def callee(self, *args, **kwargs):
            if self.obsolete:
                if not self.has_group('steward'):
                    raise UserRightsError(CLOSED_WIKI_MSG.format(site=self))

            elif right is not None and not self.has_right(right):
                if os.environ.get('PYWIKIBOT_TEST_RUNNING', '0') == '1':
                    rights = ' but:\n' + fill(
                        str(sorted(self.userinfo['rights'])),
                        width=76, break_on_hyphens=False)
                else:
                    rights = '.'
                raise UserRightsError(
                    f'User "{self.user()}" does not have required user right '
                    f'"{right}" on site {self}{rights}')
            return fn(self, *args, **kwargs)

        manage_wrapping(callee, fn)
        return callee

    return decorator


def need_version(version: str):
    """Decorator to require a certain MediaWiki version number.

    :param version: the mw version number required
    :return: a decorator to make sure the requirement is satisfied when
        the decorated function is called.
    """
    def decorator(fn):
        def callee(self, *args, **kwargs):
            if MediaWikiVersion(self.version()) < MediaWikiVersion(version):
                raise NotImplementedError(
                    f'Method or function "{fn.__name__}"\n'
                    f"isn't implemented in MediaWiki version < {version}")
            return fn(self, *args, **kwargs)

        manage_wrapping(callee, fn)

        return callee
    return decorator
