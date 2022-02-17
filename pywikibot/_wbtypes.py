"""Wikibase data type classes."""
#
# (C) Pywikibot team, 2013-2022
#
# Distributed under the terms of the MIT license.
#
import abc
import json
from typing import TYPE_CHECKING, Any, Optional

from pywikibot.backports import Dict


if TYPE_CHECKING:
    from pywikibot.site import DataSite


class WbRepresentation(abc.ABC):

    """Abstract class for Wikibase representations."""

    @abc.abstractmethod
    def __init__(self) -> None:
        """Constructor."""
        raise NotImplementedError

    @abc.abstractmethod
    def toWikibase(self) -> Any:
        """Convert representation to JSON for the Wikibase API."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def fromWikibase(
        cls,
        data: Dict[str, Any],
        site: Optional['DataSite'] = None
    ) -> 'WbRepresentation':
        """Create a representation object based on JSON from Wikibase API."""
        raise NotImplementedError

    def __str__(self) -> str:
        return json.dumps(self.toWikibase(), indent=4, sort_keys=True,
                          separators=(',', ': '))

    def __repr__(self) -> str:
        assert isinstance(self._items, tuple)
        assert all(isinstance(item, str) for item in self._items)

        values = ((attr, getattr(self, attr)) for attr in self._items)
        attrs = ', '.join('{}={}'.format(attr, value)
                          for attr, value in values)
        return '{}({})'.format(self.__class__.__name__, attrs)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.toWikibase() == other.toWikibase()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(frozenset(self.toWikibase().items()))

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
