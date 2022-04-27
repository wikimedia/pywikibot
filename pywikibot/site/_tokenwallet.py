"""Objects representing api tokens."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import debug
from pywikibot.exceptions import Error


class TokenWallet:

    """Container for tokens."""

    def __init__(self, site) -> None:
        """Initializer.

        :type site: pywikibot.site.APISite
        """
        self.site = site
        self._tokens = {}
        self.failed_cache = set()  # cache unavailable tokens.

    def load_tokens(self, types, all: bool = False) -> None:
        """
        Preload one or multiple tokens.

        :param types: the types of token.
        :type types: iterable
        :param all: load all available tokens, if None only if it can be done
            in one request.
        """
        if self.site.user() is None:
            self.site.login()

        self._tokens.setdefault(self.site.user(), {}).update(
            self.site.get_tokens(types, all=all))

        # Preload all only the first time.
        # When all=True types is extended in site.get_tokens().
        # Keys not recognised as tokens, are cached so they are not requested
        # any longer.
        if all is not False:
            for key in types:
                if key not in self._tokens[self.site.user()]:
                    self.failed_cache.add((self.site.user(), key))

    def __getitem__(self, key):
        """Get token value for the given key."""
        if self.site.user() is None:
            self.site.login()

        user_tokens = self._tokens.setdefault(self.site.user(), {})
        # always preload all for users without tokens
        failed_cache_key = (self.site.user(), key)

        # redirect old tokens to be compatible with older MW version
        # https://www.mediawiki.org/wiki/MediaWiki_1.37/Deprecation_of_legacy_API_token_parameters
        if self.site.mw_version >= '1.24wmf19' \
           and key in {'edit', 'delete', 'protect', 'move', 'block', 'unblock',
                       'email', 'import', 'options'}:
            debug('Token {!r} was replaced by {!r}'.format(key, 'csrf'))
            key = 'csrf'

        try:
            key = self.site.validate_tokens([key])[0]
        except IndexError:
            raise Error(
                "Requested token '{}' is invalid on {} wiki."
                .format(key, self.site))

        if (key not in user_tokens
                and failed_cache_key not in self.failed_cache):
            self.load_tokens([key], all=False if user_tokens else None)

        if key in user_tokens:
            return user_tokens[key]
        # token not allowed for self.site.user() on self.site
        self.failed_cache.add(failed_cache_key)
        # to be changed back to a plain KeyError?
        raise Error(
            "Action '{}' is not allowed for user {} on {} wiki."
            .format(key, self.site.user(), self.site))

    def __contains__(self, key) -> bool:
        """Return True if the given token name is cached."""
        return key in self._tokens.setdefault(self.site.user(), {})

    def __str__(self) -> str:
        """Return a str representation of the internal tokens dictionary."""
        return self._tokens.__str__()

    def __repr__(self) -> str:
        """Return a representation of the internal tokens dictionary."""
        return self._tokens.__repr__()
