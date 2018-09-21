# -*- coding: utf-8 -*-
"""Wikibase data type classes."""
#
# (C) Pywikibot team, 2013-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import json

from pywikibot.tools import StringTypes


class WbRepresentation(object):

    """Abstract class for Wikibase representations."""

    def __init__(self):
        """Constructor."""
        raise NotImplementedError

    def toWikibase(self):
        """Convert representation to JSON for the Wikibase API."""
        raise NotImplementedError

    @classmethod
    def fromWikibase(cls, json):
        """Create a representation object based on JSON from Wikibase API."""
        raise NotImplementedError

    def __str__(self):
        return json.dumps(self.toWikibase(), indent=4, sort_keys=True,
                          separators=(',', ': '))

    def __repr__(self):
        assert isinstance(self._items, tuple)
        assert all(isinstance(item, StringTypes) for item in self._items)

        values = ((attr, getattr(self, attr)) for attr in self._items)
        attrs = ', '.join('{0}={1}'.format(attr, value)
                          for attr, value in values)
        return '{0}({1})'.format(self.__class__.__name__, attrs)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.toWikibase() == other.toWikibase()
        return NotImplemented

    def __hash__(self):
        return hash(frozenset(self.toWikibase().items()))

    def __ne__(self, other):
        return not self.__eq__(other)
