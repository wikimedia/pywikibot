#
# (C) Pywikibot team, 2008-2026
#
# Distributed under the terms of the MIT license.
#
"""Object representing page revision."""
from __future__ import annotations

import hashlib
from contextlib import suppress
from typing import Any

from pywikibot import Timestamp
from pywikibot.tools.collections import DataRecord


__all__ = ('Revision', )


class Revision(DataRecord):

    """A structure holding information about a single revision of a Page.

    Each data item can be accessed either by its key or as an attribute
    with the attribute name equal to the key e.g.:

    >>> r = Revision(comment='Sample for Revision access')
    >>> r.comment == r['comment']
    True
    >>> r.comment
    'Sample for Revision access'

    .. seealso::

       - :api:`Revisions`
       - :api:`Alldeletedrevisions`
    """

    @staticmethod
    def normalize(data: dict[str, Any]) -> None:
        """Upcast dictionary values."""
        with suppress(KeyError):  # enable doctest
            data['timestamp'] = Timestamp.fromISOformat(data['timestamp'])

        data.update(anon='anon' in data)
        data.update(minor='minor' in data)
        data.update(userhidden='userhidden' in data)
        data.update(commenthidden='commenthidden' in data)

        data.setdefault('comment', '')
        data.setdefault('user', '')

        if 'slots' in data:  # mw 1.32+
            mainslot = data['slots'].get('main', {})
            data['text'] = mainslot.get('*')
            data['contentmodel'] = mainslot.get('contentmodel')
        else:
            data['slots'] = None
            data['text'] = data.get('*')

        data.setdefault('sha1')
        if data['sha1'] is None and data['text'] is not None:
            data['sha1'] = hashlib.sha1(
                data['text'].encode('utf8')).hexdigest()

    def __missing__(self, key: str, /):
        """Provide backward compatibility for exceptions."""
        raise AttributeError(
            f'{type(self).__name__!r} object has no attribute {key!r}'
        )
