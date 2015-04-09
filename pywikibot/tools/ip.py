# -*- coding: utf-8  -*-
"""IP address tools module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
# Note that this module _must_ not import future.unicode_literals
# otherwise it will not be able to detect the defective ipaddress module.
from __future__ import unicode_literals

__version__ = '$Id$'

import re
import sys

from warnings import warn

from pywikibot.tools import LazyRegex

try:
    from ipaddress import ip_address
    if sys.version_info[0] < 3:
        # This backport fails many tests
        # https://pypi.python.org/pypi/py2-ipaddress
        # It accepts u'1111' as a valid IP address.
        try:
            ip_address(u'1111')
            ip_address = None
            raise ImportError('ipaddress backport is broken')
        except ValueError:
            pass

        # This backport only fails a few tests if given a unicode object
        # https://pypi.python.org/pypi/ipaddress
        # However while it rejects u'1111', it will consider '1111' valid
        try:
            ip_address(b'1111')
            warn('ipaddress backport is defective; patching.', ImportWarning)
            orig_ip_address = ip_address
            # force all input to be a unicode object so it validates correctly

            def ip_address(IP):
                """Safe ip_address."""
                return orig_ip_address(unicode(IP))  # noqa
        except ValueError:
            # This means ipaddress has correctly determined '1111' is invalid
            pass
except ImportError as e:
    warn('Importing ipaddress.ip_address failed: %s' % e,
         ImportWarning)

    def ip_address(IP):
        """Fake ip_address method."""
        warn('ipaddress backport not available.', DeprecationWarning)
        if ip_regexp.match(IP) is None:
            raise ValueError('Invalid IP address')

    # The following flag is used by the unit tests
    ip_address.__fake__ = True

# deprecated IP detector
ip_regexp = LazyRegex()
ip_regexp.flags = re.IGNORECASE
ip_regexp.raw = (
    r'^(?:(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|'
    r'(((?=(?=(.*?(::)))\3(?!.+\4)))\4?|[\dA-F]{1,4}:)'
    r'([\dA-F]{1,4}(\4|:\b)|\2){5}'
    r'(([\dA-F]{1,4}(\4|:\b|$)|\2){2}|'
    r'(((2[0-4]|1\d|[1-9])?\d|25[0-5])\.?\b){4}))\Z')


def is_IP(IP):
    """
    Verify the IP address provided is valid.

    No logging is performed.  Use ip_address instead to catch errors.

    @param IP: IP address
    @type IP: unicode
    @rtype: bool
    """
    try:
        ip_address(IP)
        return True
    except ValueError:
        return False
