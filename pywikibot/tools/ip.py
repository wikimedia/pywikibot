# -*- coding: utf-8 -*-
"""IP address tools module."""
#
# (C) Pywikibot team, 2014-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import re

from distutils.version import StrictVersion
from warnings import warn

from pywikibot.tools import DeprecatedRegex, PY2, UnicodeType

_ipaddress_e = _ipaddr_e = _ipaddr_version = None

try:
    from ipaddress import ip_address
except ImportError as e:
    _ipaddress_e = e
    ip_address = None

if not ip_address or PY2:
    try:
        from ipaddr import __version__ as _ipaddr_version
    except ImportError as e:
        _ipaddr_e = e
    else:
        _ipaddr_version = StrictVersion(_ipaddr_version)
        if _ipaddr_version >= StrictVersion('2.1.10'):
            from ipaddr import IPAddress as ip_address  # noqa: N813
        else:
            _ipaddr_e = ImportError('ipaddr %s is broken.' % _ipaddr_version)

if ip_address and ip_address.__module__ == 'ipaddress':
    if PY2:
        # This backport fails many tests
        # https://pypi.org/project/py2-ipaddress
        # It accepts u'1111' as a valid IP address.
        try:
            ip_address('1111')
            ip_address = None
            raise ImportError('ipaddress backport is broken; install ipaddr')
        except ValueError:
            pass

        # This backport only fails a few tests if given a unicode object
        # https://pypi.org/project/ipaddress
        # However while it rejects u'1111', it will consider '1111' valid
        try:
            ip_address(b'1111')
            warn('ipaddress backport is defective; patching; install ipaddr',
                 ImportWarning)
            orig_ip_address = ip_address
            # force all input to be a unicode object so it validates correctly

            def ip_address_patched(IP):
                """Safe ip_address."""
                return orig_ip_address(UnicodeType(IP))

            ip_address = ip_address_patched
        except ValueError:
            # This means ipaddress has correctly determined '1111' is invalid
            pass
elif not ip_address:
    warn('Importing ipaddr.IPAddress failed: %s\n'
         'Importing ipaddress.ip_address failed: %s\n'
         'Please install ipaddr 2.1.10+ or ipaddress.'
         % (_ipaddr_e, _ipaddress_e), ImportWarning)

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
    'page.ip_regexp', 'tools.ip.is_IP', since='20150212')


def is_IP(IP):
    """
    Verify the IP address provided is valid.

    No logging is performed. Use ip_address instead to catch errors.

    @param IP: IP address
    @type IP: str
    @rtype: bool
    """
    try:
        ip_address(IP)
        return True
    except ValueError:
        return False
