"""Objects representing api tokens."""
#
# (C) Pywikibot team, 2008-2023
#
# Distributed under the terms of the MIT license.
#
from collections.abc import Container
from typing import TYPE_CHECKING, Any, Optional

from pywikibot.backports import Dict, List
from pywikibot.tools import deprecated, issue_deprecation_warning


if TYPE_CHECKING:
    from pywikibot.site import APISite


class TokenWallet(Container):

    """Container for tokens.

    You should not use this container class directly; use
    :attr:`APISite.tokens<pywikibot.site._apisite.APISite.tokens>`
    instead which gives access to the site's TokenWallet instance.
    """

    def __init__(self, site: 'APISite') -> None:
        """Initializer."""
        self.site: APISite = site
        self._tokens: Dict[str, str] = {}
        self._currentuser: Optional[str] = site.user()
        # guess the needed token in update_tokens
        self._last_token_key: Optional[str] = None

    def __getitem__(self, key: str) -> str:
        """Get token value for the given key."""
        if self.site.user() is None and key != 'login':
            self.site.login()

        if self.site.user() != self._currentuser:
            self._currentuser = self.site.user()
            self.clear()

        if not self._tokens:
            self._tokens = self.site.get_tokens([])

        # Redirect old tokens which were used by outdated MediaWiki versions
        # but show a FutureWarning for this usage:
        # https://www.mediawiki.org/wiki/MediaWiki_1.37/Deprecation_of_legacy_API_token_parameters
        if key in {'edit', 'delete', 'protect', 'move', 'block', 'unblock',
                   'email', 'import', 'options'}:
            issue_deprecation_warning(
                f'Token {key!r}', "'csrf'", since='8.0.0')
            key = 'csrf'

        try:
            token = self._tokens[key]
        except KeyError:
            raise KeyError(
                f'Invalid token {key!r} for user {self._currentuser!r} on '
                f'{self.site} wiki.') from None

        self._last_token_key = key
        return token

    def __contains__(self, key) -> bool:
        """Return True if the token name is cached for the current user."""
        try:
            self[key]
        except KeyError:
            return False
        return True

    def __str__(self) -> str:
        """Return a str representation of the internal tokens dictionary."""
        return str(self._tokens)

    def __repr__(self) -> str:
        """Return a representation of the TokenWallet.

        >>> import pywikibot
        >>> site = pywikibot.Site('wikipedia:test')
        >>> repr(site.tokens)
        "TokenWallet(pywikibot.Site('wikipedia:test'))"

        .. versionchanged:: 8.0
           Provide a string which looks like a valid Python expression.
        """
        user = f', user={self._currentuser!r}' if self._currentuser else ''
        return (f'{type(self).__name__}'
                f'(pywikibot.Site({self.site.sitename!r}{user}))')

    def clear(self):
        """Clear the self._tokens cache. Tokens are reloaded when needed.

        .. versionadded:: 8.0
        """
        self._tokens.clear()

    def update_tokens(self, tokens: List[str]) -> List[str]:
        """Return a list of new tokens for a given list of tokens.

        This method can be used if a token is outdated and has to be
        renewed but the token type is unknown and we only have the old
        token. It first gets the token names from all given tokens,
        clears the cache and returns fresh new tokens of the found types.

        **Usage:**

        >>> import pywikibot
        >>> site = pywikibot.Site()
        >>> tokens = [site.tokens['csrf']]  # doctest: +SKIP
        >>> new_tokens = site.tokens.update_tokens(tokens)  # doctest: +SKIP

        .. code-block:: Python
           :caption: An example for replacing request token parameters

           r._params['token'] = r.site.tokens.update_tokens(r._params['token'])

        .. versionadded:: 8.0
        """
        # find the token types
        types = [key
                 for key, value in self._tokens.items() for token in tokens
                 if value == token] or [self._last_token_key]
        self.clear()  # clear the cache
        return [self[token_type] for token_type in types]

    @deprecated('clear()', since='8.0.0')
    def load_tokens(self, *args: Any, **kwargs: Any) -> None:
        """Clear cache to lazy load tokens when needed.

        .. deprecated:: 8.0
           Use :meth:`clear` instead.
        .. versionchanged:: 8.0
           Clear the cache instead of loading tokens. All parameters are
           ignored.
        """
        self.clear()
