"""Interface to Mediawiki's api.php."""
#
# (C) Pywikibot team, 2014-2023
#
# Distributed under the terms of the MIT license.
#
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
    """
    Clear cookies for site's second level domain.

    The http module takes care of all the cookie stuff.
    This is a workaround for requests bug, see :phab:`T224712`
    and https://github.com/psf/requests/issues/5411
    for more details.
    """
    if isinstance(family, SubdomainFamily):
        for cookie in http.cookie_jar:
            if family.domain == cookie.domain:
                http.cookie_jar.clear(cookie.domain, cookie.path, cookie.name)


# Bug: T113120, T228841
# Subclassing necessary to fix bug of the email package in Python 3:
# see https://bugs.python.org/issue19003
# see https://bugs.python.org/issue18886
# The following solution might be removed if the bug is fixed for
# Python versions which are supported by PWB, probably with Python 3.5

class CTEBinaryBytesGenerator(BytesGenerator):

    """Workaround for bug in python 3 email handling of CTE binary."""

    def __init__(self, *args, **kwargs) -> None:
        """Initializer."""
        super().__init__(*args, **kwargs)
        self._writeBody = self._write_body

    def _write_body(self, msg) -> None:
        if msg['content-transfer-encoding'] == 'binary':
            self._fp.write(msg.get_payload(decode=True))
        else:
            super()._handle_text(msg)


class CTEBinaryMIMEMultipart(MIMEMultipartOrig):

    """Workaround for bug in python 3 email handling of CTE binary."""

    def as_bytes(self, unixfrom: bool = False, policy=None):
        """Return unmodified binary payload."""
        policy = self.policy if policy is None else policy
        fp = BytesIO()
        g = CTEBinaryBytesGenerator(fp, mangle_from_=False, policy=policy)
        g.flatten(self, unixfrom=unixfrom)
        return fp.getvalue()


MIMEMultipart = CTEBinaryMIMEMultipart

wrapper = ModuleDeprecationWrapper(__name__)
wrapper.add_deprecated_attr(
    'LoginManager',
    replacement_name='pywikibot.login.ClientLoginManager',
    since='8.0.0')
