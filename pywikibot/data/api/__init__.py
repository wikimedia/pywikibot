"""Interface to MediaWiki's api.php."""
#
# (C) Pywikibot team, 2014-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from email.generator import BytesGenerator
from email.mime.multipart import MIMEMultipart as MIMEMultipartOrig
from io import BytesIO

from pywikibot.comms import http
from pywikibot.data.api._generators import (
    APIGenerator,
    APIGeneratorBase,
    ListGenerator,
    LogEntryListGenerator,
    PageGenerator,
    PropertyGenerator,
    QueryGenerator,
    update_page,
)
from pywikibot.data.api._optionset import OptionSet
from pywikibot.data.api._paraminfo import ParamInfo
from pywikibot.data.api._requests import CachedRequest, Request, encode_url
from pywikibot.family import SubdomainFamily
from pywikibot.tools import ModuleDeprecationWrapper


__all__ = (
    'APIGeneratorBase',
    'APIGenerator',
    'CachedRequest',
    'ListGenerator',
    'LogEntryListGenerator',
    'OptionSet',
    'PageGenerator',
    'ParamInfo',
    'PropertyGenerator',
    'QueryGenerator',
    'Request',
    'encode_url',
    'update_page',
)


def _invalidate_superior_cookies(family) -> None:
    """Clear cookies for site's second level domain.

    The http module takes care of all the cookie stuff.
    This is a workaround for requests bug, see :phab:`T224712`
    and https://github.com/psf/requests/issues/5411
    for more details.
    """
    if isinstance(family, SubdomainFamily):
        for cookie in http.cookie_jar:
            if family.domain == cookie.domain:  # type: ignore[attr-defined]
                http.cookie_jar.clear(cookie.domain, cookie.path, cookie.name)


# Bug: T113120, T228841
# Subclassing necessary to fix bug of the email package in Python 3:
# see https://github.com/python/cpython/issues/63086
# The following solution might be removed if the bug is fixed for
# Python versions which are supported by PWB

class CTEBinaryBytesGenerator(BytesGenerator):

    """Workaround for bug in python 3 email handling of CTE binary."""

    def _handle_text(self, msg) -> None:
        if msg['content-transfer-encoding'] == 'binary':
            self._fp.write(  # type: ignore[attr-defined]
                msg.get_payload(decode=True))
        else:
            super()._handle_text(msg)  # type: ignore[misc]

    _writeBody = _handle_text  # noqa: N815


class CTEBinaryMIMEMultipart(MIMEMultipartOrig):

    """Workaround for bug in python 3 email handling of CTE binary."""

    def as_bytes(self, unixfrom: bool = False, policy=None):
        """Return unmodified binary payload."""
        policy = self.policy if policy is None else policy
        fp = BytesIO()
        g = CTEBinaryBytesGenerator(fp, policy=policy)
        g.flatten(self, unixfrom=unixfrom)
        return fp.getvalue()


MIMEMultipart = CTEBinaryMIMEMultipart

wrapper = ModuleDeprecationWrapper(__name__)
wrapper.add_deprecated_attr(
    'LoginManager',
    replacement_name='pywikibot.login.ClientLoginManager',
    since='8.0.0')
