# -*- coding: utf-8 -*-
"""IP address tools module."""
#
# (C) Pywikibot team, 2014-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from distutils.version import StrictVersion

from pywikibot.tools import ModuleDeprecationWrapper

_ipaddress_e = _ipaddr_e = _ipaddr_version = None

try:
    from ipaddress import ip_address
except ImportError as e:
    _ipaddress_e = e
    ip_address = None

if not ip_address:
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

if not ip_address:
    raise ImportError('Importing ipaddr.IPAddress failed: {}\n'
                      'Importing ipaddress.ip_address failed: {}\n'
                      'Please install ipaddress.'
                      .format(_ipaddr_e, _ipaddress_e))


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


wrapper = ModuleDeprecationWrapper(__name__)
wrapper._add_deprecated_attr('is_IP',
                             replacement_name='tools.is_IP',
                             future_warning=True,
                             since='20200120')
