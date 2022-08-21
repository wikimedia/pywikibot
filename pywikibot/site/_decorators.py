"""Decorators used by site models."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
from typing import Optional

from pywikibot.exceptions import UnknownExtensionError, UserRightsError
from pywikibot.tools import MediaWikiVersion, manage_wrapping


def must_be(group: Optional[str] = None):
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
                    raise UserRightsError(
                        'Site {} has been closed. Only steward '
                        'can perform requested action.'
                        .format(self.sitename))

            elif not self.has_group(grp):
                raise UserRightsError('User "{}" is not part of the required '
                                      'user group "{}"'
                                      .format(self.user(), grp))

            return fn(self, *args, **kwargs)

        if not __debug__:
            return fn

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
                    'Method "{}" is not implemented without the extension {}'
                    .format(fn.__name__, extension))
            return fn(self, *args, **kwargs)

        if not __debug__:
            return fn

        manage_wrapping(callee, fn)
        return callee

    return decorator


def need_right(right: Optional[str] = None):
    """Decorator to require a certain user right when method is called.

    :param right: The right the logged in user should have.
    :return: method decorator
    :raises UserRightsError: user has insufficient rights.
    """
    def decorator(fn):
        def callee(self, *args, **kwargs):
            if self.obsolete:
                if not self.has_group('steward'):
                    raise UserRightsError(
                        'Site {} has been closed. Only stewards '
                        'can perform the requested action.'
                        .format(self.sitename))

            elif right is not None and not self.has_right(right):
                raise UserRightsError('User "{}" does not have required '
                                      'user right "{}"'
                                      .format(self.user(), right))
            return fn(self, *args, **kwargs)

        if not __debug__:
            return fn

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
                    'Method or function "{}"\n'
                    "isn't implemented in MediaWiki version < {}"
                    .format(fn.__name__, version))
            return fn(self, *args, **kwargs)

        if not __debug__:
            return fn

        manage_wrapping(callee, fn)

        return callee
    return decorator
