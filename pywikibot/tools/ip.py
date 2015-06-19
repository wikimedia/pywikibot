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

from pywikibot.tools import DeprecatedRegex

ipaddress_e = ipaddr_e = None

try:
    from ipaddress import ip_address
except ImportError as ipaddress_e:
    ip_address = None
    pass

if not ip_address or sys.version_info[0] < 3:
    try:
        from ipaddr import IPAddress as ip_address
        ip_address.__T76286__ = False
    except ImportError as ipaddr_e:
        pass

if ip_address and ip_address.__module__ == 'ipaddress':
    if sys.version_info[0] < 3:
        # This backport fails many tests
        # https://pypi.python.org/pypi/py2-ipaddress
        # It accepts u'1111' as a valid IP address.
        try:
            ip_address(u'1111')
            ip_address = None
            raise ImportError('ipaddress backport is broken; install ipaddr')
        except ValueError:
            pass

        # This backport only fails a few tests if given a unicode object
        # https://pypi.python.org/pypi/ipaddress
        # However while it rejects u'1111', it will consider '1111' valid
        try:
            ip_address(b'1111')
            warn('ipaddress backport is defective; patching; install ipaddr',
                 ImportWarning)
            orig_ip_address = ip_address
            # force all input to be a unicode object so it validates correctly

            def ip_address_patched(IP):
                """Safe ip_address."""
                return orig_ip_address(unicode(IP))  # noqa

            ip_address = ip_address_patched
        except ValueError:
            # This means ipaddress has correctly determined '1111' is invalid
            pass
elif not ip_address:
    warn('Importing ipaddr.IPAddress failed: %s\n'
         'Importing ipaddress.ip_address failed: %s\n'
         'Please install ipaddr.'
         % (ipaddr_e, ipaddress_e), ImportWarning)

    def ip_address_fake(IP):
        """Fake ip_address method."""
        warn('ipaddress backport not available.', DeprecationWarning)
        if ip_regexp.match(IP) is None:
            raise ValueError('Invalid IP address')

    ip_address = ip_address_fake

# deprecated IP detector
ip_regexp = DeprecatedRegex(
    r'^(?:(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|'
    r'(((?=(?=(.*?(::)))\3(?!.+\4)))\4?|[\dA-F]{1,4}:)'
    r'([\dA-F]{1,4}(\4|:\b)|\2){5}'
    r'(([\dA-F]{1,4}(\4|:\b|$)|\2){2}|'
    r'(((2[0-4]|1\d|[1-9])?\d|25[0-5])\.?\b){4}))\Z',
    re.IGNORECASE,
    'page.ip_regexp', 'tools.ip.is_IP')


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
