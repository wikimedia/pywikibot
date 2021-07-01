"""Objects representing api tokens."""
#
# (C) Pywikibot team, 2008-2020
#
# Distributed under the terms of the MIT license.
#
from pywikibot.exceptions import Error


class TokenWallet:

    """Container for tokens."""

    def __init__(self, site):
        """Initializer.

        :type site: pywikibot.site.APISite
        """
        self.site = site
        self._tokens = {}
        self.failed_cache = set()  # cache unavailable tokens.

    def load_tokens(self, types, all=False):
        """
        Preload one or multiple tokens.

        :param types: the types of token.
        :type types: iterable
        :param all: load all available tokens, if None only if it can be done
            in one request.
        :type all: bool
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

    def __contains__(self, key):
        """Return True if the given token name is cached."""
        return key in self._tokens.setdefault(self.site.user(), {})

    def __str__(self):
        """Return a str representation of the internal tokens dictionary."""
        return self._tokens.__str__()

    def __repr__(self):
        """Return a representation of the internal tokens dictionary."""
        return self._tokens.__repr__()
