#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test IP module/regex."""
#
# (C) Pywikibot team, 2012-2015
#
# Distributed under the terms of the MIT license.
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from distutils.version import StrictVersion

from pywikibot.tools import ip

from tests import unittest_print
from tests.aspects import unittest, TestCase, DeprecationTestCase
from tests.utils import expected_failure_if


class TestIPBase(TestCase):

    """Unit test class base for IP matching."""

    net = False

    def setUp(self):
        """Set up test."""
        self.total = 0
        self.fail = 0
        self.errors = []
        super(TestIPBase, self).setUp()

    def tearDown(self):
        """Tear down test."""
        super(TestIPBase, self).tearDown()
        if not self.fail:
            unittest_print('{0} tests done'.format(self.total))
        else:
            unittest_print(
                '{0} of {1} tests failed:\n{2}'.format(
                    self.fail, self.total, '\n'.join(self.errors)))

    def ipv6test(self, result, IP):
        """Perform one IP test."""
        self.total += 1
        try:
            self.assertEqual(result, self._do_ip_test(IP))
        except AssertionError:
            self.fail += 1
            self.errors.append(
                '"%s" match should be %s - not OK'
                % (IP, result))

    def _run_tests(self):
        """Test various IP."""
        # test from http://download.dartware.com/thirdparty/test-ipv6-regex.pl
        self.ipv6test(False, "")  # empty string
        self.ipv6test(True, "::1")  # loopback, compressed, non-routable
        self.ipv6test(True, "::")  # unspecified, compressed, non-routable
        self.ipv6test(True, "0:0:0:0:0:0:0:1")  # loopback, full
        self.ipv6test(True, "0:0:0:0:0:0:0:0")  # unspecified, full
        self.ipv6test(True, "2001:DB8:0:0:8:800:200C:417A")  # unicast, full
        self.ipv6test(True, "FF01:0:0:0:0:0:0:101")  # multicast, full
        self.ipv6test(True, "2001:DB8::8:800:200C:417A")  # unicast, compressed
        self.ipv6test(True, "FF01::101")  # multicast, compressed
        self.ipv6test(False, "2001:DB8:0:0:8:800:200C:417A:221")  # unicast, full
        self.ipv6test(False, "FF01::101::2")  # multicast, compressed
        self.ipv6test(True, "fe80::217:f2ff:fe07:ed62")

        self.ipv6test(True, "2001:0000:1234:0000:0000:C1C0:ABCD:0876")
        self.ipv6test(True, "3ffe:0b00:0000:0000:0001:0000:0000:000a")
        self.ipv6test(True, "FF02:0000:0000:0000:0000:0000:0000:0001")
        self.ipv6test(True, "0000:0000:0000:0000:0000:0000:0000:0001")
        self.ipv6test(True, "0000:0000:0000:0000:0000:0000:0000:0000")
        self.ipv6test(False, " 2001:0000:1234:0000:0000:C1C0:ABCD:0876")  # leading space
        self.ipv6test(False, "2001:0000:1234:0000:0000:C1C0:ABCD:0876 ")  # trailing space
        # leading and trailing space
        self.ipv6test(False, ' 2001:0000:1234:0000:0000:C1C0:ABCD:0876 ')
        # junk after valid address
        self.ipv6test(False, '2001:0000:1234:0000:0000:C1C0:ABCD:0876  0')
        self.ipv6test(False, "2001:0000:1234: 0000:0000:C1C0:ABCD:0876")  # internal space

        self.ipv6test(False, "3ffe:0b00:0000:0001:0000:0000:000a")  # seven segments
        self.ipv6test(False, "FF02:0000:0000:0000:0000:0000:0000:0000:0001")  # nine segments
        self.ipv6test(False, "3ffe:b00::1::a")  # double "::"
        self.ipv6test(False, "::1111:2222:3333:4444:5555:6666::")  # double "::"
        self.ipv6test(True, "2::10")
        self.ipv6test(True, "ff02::1")
        self.ipv6test(True, "fe80::")
        self.ipv6test(True, "2002::")
        self.ipv6test(True, "2001:db8::")
        self.ipv6test(True, "2001:0db8:1234::")
        self.ipv6test(True, "::ffff:0:0")
        self.ipv6test(True, "::1")
        self.ipv6test(True, "1:2:3:4:5:6:7:8")
        self.ipv6test(True, "1:2:3:4:5:6::8")
        self.ipv6test(True, "1:2:3:4:5::8")
        self.ipv6test(True, "1:2:3:4::8")
        self.ipv6test(True, "1:2:3::8")
        self.ipv6test(True, "1:2::8")
        self.ipv6test(True, "1::8")
        self.ipv6test(True, "1::2:3:4:5:6:7")
        self.ipv6test(True, "1::2:3:4:5:6")
        self.ipv6test(True, "1::2:3:4:5")
        self.ipv6test(True, "1::2:3:4")
        self.ipv6test(True, "1::2:3")
        self.ipv6test(True, "1::8")
        self.ipv6test(True, "::2:3:4:5:6:7:8")
        self.ipv6test(True, "::2:3:4:5:6:7")
        self.ipv6test(True, "::2:3:4:5:6")
        self.ipv6test(True, "::2:3:4:5")
        self.ipv6test(True, "::2:3:4")
        self.ipv6test(True, "::2:3")
        self.ipv6test(True, "::8")
        self.ipv6test(True, "1:2:3:4:5:6::")
        self.ipv6test(True, "1:2:3:4:5::")
        self.ipv6test(True, "1:2:3:4::")
        self.ipv6test(True, "1:2:3::")
        self.ipv6test(True, "1:2::")
        self.ipv6test(True, "1::")
        self.ipv6test(True, "1:2:3:4:5::7:8")
        self.ipv6test(False, "1:2:3::4:5::7:8")  # Double "::"
        self.ipv6test(False, "12345::6:7:8")
        self.ipv6test(True, "1:2:3:4::7:8")
        self.ipv6test(True, "1:2:3::7:8")
        self.ipv6test(True, "1:2::7:8")
        self.ipv6test(True, "1::7:8")

        # IPv4 addresses as dotted-quads
        self.ipv6test(True, "1:2:3:4:5:6:1.2.3.4")
        self.ipv6test(True, "1:2:3:4:5::1.2.3.4")
        self.ipv6test(True, "1:2:3:4::1.2.3.4")
        self.ipv6test(True, "1:2:3::1.2.3.4")
        self.ipv6test(True, "1:2::1.2.3.4")
        self.ipv6test(True, "1::1.2.3.4")
        self.ipv6test(True, "1:2:3:4::5:1.2.3.4")
        self.ipv6test(True, "1:2:3::5:1.2.3.4")
        self.ipv6test(True, "1:2::5:1.2.3.4")
        self.ipv6test(True, "1::5:1.2.3.4")
        self.ipv6test(True, "1::5:11.22.33.44")
        self.ipv6test(False, "1::5:400.2.3.4")
        self.ipv6test(False, "1::5:260.2.3.4")
        self.ipv6test(False, "1::5:256.2.3.4")
        self.ipv6test(False, "1::5:1.256.3.4")
        self.ipv6test(False, "1::5:1.2.256.4")
        self.ipv6test(False, "1::5:1.2.3.256")
        self.ipv6test(False, "1::5:300.2.3.4")
        self.ipv6test(False, "1::5:1.300.3.4")
        self.ipv6test(False, "1::5:1.2.300.4")
        self.ipv6test(False, "1::5:1.2.3.300")
        self.ipv6test(False, "1::5:900.2.3.4")
        self.ipv6test(False, "1::5:1.900.3.4")
        self.ipv6test(False, "1::5:1.2.900.4")
        self.ipv6test(False, "1::5:1.2.3.900")
        self.ipv6test(False, "1::5:300.300.300.300")
        self.ipv6test(False, "1::5:3000.30.30.30")
        self.ipv6test(False, "1::400.2.3.4")
        self.ipv6test(False, "1::260.2.3.4")
        self.ipv6test(False, "1::256.2.3.4")
        self.ipv6test(False, "1::1.256.3.4")
        self.ipv6test(False, "1::1.2.256.4")
        self.ipv6test(False, "1::1.2.3.256")
        self.ipv6test(False, "1::300.2.3.4")
        self.ipv6test(False, "1::1.300.3.4")
        self.ipv6test(False, "1::1.2.300.4")
        self.ipv6test(False, "1::1.2.3.300")
        self.ipv6test(False, "1::900.2.3.4")
        self.ipv6test(False, "1::1.900.3.4")
        self.ipv6test(False, "1::1.2.900.4")
        self.ipv6test(False, "1::1.2.3.900")
        self.ipv6test(False, "1::300.300.300.300")
        self.ipv6test(False, "1::3000.30.30.30")
        self.ipv6test(False, "::400.2.3.4")
        self.ipv6test(False, "::260.2.3.4")
        self.ipv6test(False, "::256.2.3.4")
        self.ipv6test(False, "::1.256.3.4")
        self.ipv6test(False, "::1.2.256.4")
        self.ipv6test(False, "::1.2.3.256")
        self.ipv6test(False, "::300.2.3.4")
        self.ipv6test(False, "::1.300.3.4")
        self.ipv6test(False, "::1.2.300.4")
        self.ipv6test(False, "::1.2.3.300")
        self.ipv6test(False, "::900.2.3.4")
        self.ipv6test(False, "::1.900.3.4")
        self.ipv6test(False, "::1.2.900.4")
        self.ipv6test(False, "::1.2.3.900")
        self.ipv6test(False, "::300.300.300.300")
        self.ipv6test(False, "::3000.30.30.30")
        self.ipv6test(True, "fe80::217:f2ff:254.7.237.98")
        self.ipv6test(True, "::ffff:192.168.1.26")
        self.ipv6test(False, "2001:1:1:1:1:1:255Z255X255Y255")  # garbage instead of "." in IPv4
        self.ipv6test(False, "::ffff:192x168.1.26")  # ditto
        self.ipv6test(True, "::ffff:192.168.1.1")
        # IPv4-compatible IPv6 address, full, deprecated
        self.ipv6test(True, '0:0:0:0:0:0:13.1.68.3')
        self.ipv6test(True, "0:0:0:0:0:FFFF:129.144.52.38")  # IPv4-mapped IPv6 address, full
        self.ipv6test(True, "::13.1.68.3")  # IPv4-compatible IPv6 address, compressed, deprecated
        self.ipv6test(True, "::FFFF:129.144.52.38")  # IPv4-mapped IPv6 address, compressed
        self.ipv6test(True, "fe80:0:0:0:204:61ff:254.157.241.86")
        self.ipv6test(True, "fe80::204:61ff:254.157.241.86")
        self.ipv6test(True, "::ffff:12.34.56.78")
        self.ipv6test(False, "::ffff:2.3.4")
        self.ipv6test(False, "::ffff:257.1.2.3")

        self.ipv6test(False, "1.2.3.4:1111:2222:3333:4444::5555")  # Aeron
        self.ipv6test(False, "1.2.3.4:1111:2222:3333::5555")
        self.ipv6test(False, "1.2.3.4:1111:2222::5555")
        self.ipv6test(False, "1.2.3.4:1111::5555")
        self.ipv6test(False, "1.2.3.4::5555")
        self.ipv6test(False, "1.2.3.4::")

        # Testing IPv4 addresses represented as dotted-quads
        # Leading zero's in IPv4 addresses not allowed: some systems treat the
        # leading "0" in ".086" as the start of an octal number
        # Update: The BNF in RFC-3986 explicitly defines the dec-octet
        # (for IPv4 addresses) not to have a leading zero
        self.ipv6test(False, "fe80:0000:0000:0000:0204:61ff:254.157.241.086")
        self.ipv6test(True, "::ffff:192.0.2.128")   # but this is OK, since there's a single digit
        self.ipv6test(False, "XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:1.2.3.4")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:256.256.256.256")

        # Subnet mask not accepted
        self.ipv6test(False, "2001:0DB8:0000:CD30:0000:0000:0000:0000/60")  # full, with prefix
        self.ipv6test(False, "2001:0DB8::CD30:0:0:0:0/60")  # compressed, with prefix
        self.ipv6test(False, "2001:0DB8:0:CD30::/60")  # compressed, with prefix #2
        self.ipv6test(False, "::/128")  # compressed, unspecified address type, non-routable
        self.ipv6test(False, "::1/128")  # compressed, loopback address type, non-routable
        self.ipv6test(False, "FF00::/8")  # compressed, multicast address type
        self.ipv6test(False, "FE80::/10")  # compressed, link-local unicast, non-routable
        self.ipv6test(False, "FEC0::/10")  # compressed, site-local unicast, deprecated
        self.ipv6test(False, "124.15.6.89/60")  # standard IPv4, prefix not allowed

        self.ipv6test(True, "fe80:0000:0000:0000:0204:61ff:fe9d:f156")
        self.ipv6test(True, "fe80:0:0:0:204:61ff:fe9d:f156")
        self.ipv6test(True, "fe80::204:61ff:fe9d:f156")
        self.ipv6test(True, "::1")
        self.ipv6test(True, "fe80::")
        self.ipv6test(True, "fe80::1")
        self.ipv6test(False, ":")
        self.ipv6test(True, "::ffff:c000:280")

        # Aeron supplied these test cases
        self.ipv6test(False, "1111:2222:3333:4444::5555:")
        self.ipv6test(False, "1111:2222:3333::5555:")
        self.ipv6test(False, "1111:2222::5555:")
        self.ipv6test(False, "1111::5555:")
        self.ipv6test(False, "::5555:")
        self.ipv6test(False, ":::")
        self.ipv6test(False, "1111:")
        self.ipv6test(False, ":")

        self.ipv6test(False, ":1111:2222:3333:4444::5555")
        self.ipv6test(False, ":1111:2222:3333::5555")
        self.ipv6test(False, ":1111:2222::5555")
        self.ipv6test(False, ":1111::5555")
        self.ipv6test(False, ":::5555")
        self.ipv6test(False, ":::")

        # Additional test cases
        # from https://rt.cpan.org/Public/Bug/Display.html?id=50693

        self.ipv6test(True, "2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        self.ipv6test(True, "2001:db8:85a3:0:0:8a2e:370:7334")
        self.ipv6test(True, "2001:db8:85a3::8a2e:370:7334")
        self.ipv6test(True, "2001:0db8:0000:0000:0000:0000:1428:57ab")
        self.ipv6test(True, "2001:0db8:0000:0000:0000::1428:57ab")
        self.ipv6test(True, "2001:0db8:0:0:0:0:1428:57ab")
        self.ipv6test(True, "2001:0db8:0:0::1428:57ab")
        self.ipv6test(True, "2001:0db8::1428:57ab")
        self.ipv6test(True, "2001:db8::1428:57ab")
        self.ipv6test(True, "0000:0000:0000:0000:0000:0000:0000:0001")
        self.ipv6test(True, "::1")
        self.ipv6test(True, "::ffff:0c22:384e")
        self.ipv6test(True, "2001:0db8:1234:0000:0000:0000:0000:0000")
        self.ipv6test(True, "2001:0db8:1234:ffff:ffff:ffff:ffff:ffff")
        self.ipv6test(True, "2001:db8:a::123")
        self.ipv6test(True, "fe80::")

        self.ipv6test(False, "123")
        self.ipv6test(False, "ldkfj")
        self.ipv6test(False, "2001::FFD3::57ab")
        self.ipv6test(False, "2001:db8:85a3::8a2e:37023:7334")
        self.ipv6test(False, "2001:db8:85a3::8a2e:370k:7334")
        self.ipv6test(False, "1:2:3:4:5:6:7:8:9")
        self.ipv6test(False, "1::2::3")
        self.ipv6test(False, "1:::3:4:5")
        self.ipv6test(False, "1:2:3::4:5:6:7:8:9")

        # New from Aeron
        self.ipv6test(True, "1111:2222:3333:4444:5555:6666:7777:8888")
        self.ipv6test(True, "1111:2222:3333:4444:5555:6666:7777::")
        self.ipv6test(True, "1111:2222:3333:4444:5555:6666::")
        self.ipv6test(True, "1111:2222:3333:4444:5555::")
        self.ipv6test(True, "1111:2222:3333:4444::")
        self.ipv6test(True, "1111:2222:3333::")
        self.ipv6test(True, "1111:2222::")
        self.ipv6test(True, "1111::")
        # self.ipv6test(True, "::")     #duplicate
        self.ipv6test(True, "1111:2222:3333:4444:5555:6666::8888")
        self.ipv6test(True, "1111:2222:3333:4444:5555::8888")
        self.ipv6test(True, "1111:2222:3333:4444::8888")
        self.ipv6test(True, "1111:2222:3333::8888")
        self.ipv6test(True, "1111:2222::8888")
        self.ipv6test(True, "1111::8888")
        self.ipv6test(True, "::8888")
        self.ipv6test(True, "1111:2222:3333:4444:5555::7777:8888")
        self.ipv6test(True, "1111:2222:3333:4444::7777:8888")
        self.ipv6test(True, "1111:2222:3333::7777:8888")
        self.ipv6test(True, "1111:2222::7777:8888")
        self.ipv6test(True, "1111::7777:8888")
        self.ipv6test(True, "::7777:8888")
        self.ipv6test(True, "1111:2222:3333:4444::6666:7777:8888")
        self.ipv6test(True, "1111:2222:3333::6666:7777:8888")
        self.ipv6test(True, "1111:2222::6666:7777:8888")
        self.ipv6test(True, "1111::6666:7777:8888")
        self.ipv6test(True, "::6666:7777:8888")
        self.ipv6test(True, "1111:2222:3333::5555:6666:7777:8888")
        self.ipv6test(True, "1111:2222::5555:6666:7777:8888")
        self.ipv6test(True, "1111::5555:6666:7777:8888")
        self.ipv6test(True, "::5555:6666:7777:8888")
        self.ipv6test(True, "1111:2222::4444:5555:6666:7777:8888")
        self.ipv6test(True, "1111::4444:5555:6666:7777:8888")
        self.ipv6test(True, "::4444:5555:6666:7777:8888")
        self.ipv6test(True, "1111::3333:4444:5555:6666:7777:8888")
        self.ipv6test(True, "::3333:4444:5555:6666:7777:8888")
        self.ipv6test(True, "::2222:3333:4444:5555:6666:7777:8888")
        self.ipv6test(True, "1111:2222:3333:4444:5555:6666:123.123.123.123")
        self.ipv6test(True, "1111:2222:3333:4444:5555::123.123.123.123")
        self.ipv6test(True, "1111:2222:3333:4444::123.123.123.123")
        self.ipv6test(True, "1111:2222:3333::123.123.123.123")
        self.ipv6test(True, "1111:2222::123.123.123.123")
        self.ipv6test(True, "1111::123.123.123.123")
        self.ipv6test(True, "::123.123.123.123")
        self.ipv6test(True, "1111:2222:3333:4444::6666:123.123.123.123")
        self.ipv6test(True, "1111:2222:3333::6666:123.123.123.123")
        self.ipv6test(True, "1111:2222::6666:123.123.123.123")
        self.ipv6test(True, "1111::6666:123.123.123.123")
        self.ipv6test(True, "::6666:123.123.123.123")
        self.ipv6test(True, "1111:2222:3333::5555:6666:123.123.123.123")
        self.ipv6test(True, "1111:2222::5555:6666:123.123.123.123")
        self.ipv6test(True, "1111::5555:6666:123.123.123.123")
        self.ipv6test(True, "::5555:6666:123.123.123.123")
        self.ipv6test(True, "1111:2222::4444:5555:6666:123.123.123.123")
        self.ipv6test(True, "1111::4444:5555:6666:123.123.123.123")
        self.ipv6test(True, "::4444:5555:6666:123.123.123.123")
        self.ipv6test(True, "1111::3333:4444:5555:6666:123.123.123.123")
        self.ipv6test(True, "::2222:3333:4444:5555:6666:123.123.123.123")

        # Playing with combinations of "0" and "::"
        # NB: these are all sytactically correct, but are bad form
        #   because "0" adjacent to "::" should be combined into "::"
        self.ipv6test(True, "::0:0:0:0:0:0:0")
        self.ipv6test(True, "::0:0:0:0:0:0")
        self.ipv6test(True, "::0:0:0:0:0")
        self.ipv6test(True, "::0:0:0:0")
        self.ipv6test(True, "::0:0:0")
        self.ipv6test(True, "::0:0")
        self.ipv6test(True, "::0")
        self.ipv6test(True, "0:0:0:0:0:0:0::")
        self.ipv6test(True, "0:0:0:0:0:0::")
        self.ipv6test(True, "0:0:0:0:0::")
        self.ipv6test(True, "0:0:0:0::")
        self.ipv6test(True, "0:0:0::")
        self.ipv6test(True, "0:0::")
        self.ipv6test(True, "0::")

        # New invalid from Aeron
        # Invalid data
        self.ipv6test(False, "XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX")

        # Too many components
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:7777:8888:9999")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:7777:8888::")
        self.ipv6test(False, "::2222:3333:4444:5555:6666:7777:8888:9999")

        # Too few components
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:7777")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666")
        self.ipv6test(False, "1111:2222:3333:4444:5555")
        self.ipv6test(False, "1111:2222:3333:4444")
        self.ipv6test(False, "1111:2222:3333")
        self.ipv6test(False, "1111:2222")
        self.ipv6test(False, "1111")

        # Missing :
        self.ipv6test(False, "11112222:3333:4444:5555:6666:7777:8888")
        self.ipv6test(False, "1111:22223333:4444:5555:6666:7777:8888")
        self.ipv6test(False, "1111:2222:33334444:5555:6666:7777:8888")
        self.ipv6test(False, "1111:2222:3333:44445555:6666:7777:8888")
        self.ipv6test(False, "1111:2222:3333:4444:55556666:7777:8888")
        self.ipv6test(False, "1111:2222:3333:4444:5555:66667777:8888")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:77778888")

        # Missing : intended for ::
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:7777:8888:")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:7777:")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:")
        self.ipv6test(False, "1111:2222:3333:4444:5555:")
        self.ipv6test(False, "1111:2222:3333:4444:")
        self.ipv6test(False, "1111:2222:3333:")
        self.ipv6test(False, "1111:2222:")
        self.ipv6test(False, "1111:")
        self.ipv6test(False, ":")
        self.ipv6test(False, ":8888")
        self.ipv6test(False, ":7777:8888")
        self.ipv6test(False, ":6666:7777:8888")
        self.ipv6test(False, ":5555:6666:7777:8888")
        self.ipv6test(False, ":4444:5555:6666:7777:8888")
        self.ipv6test(False, ":3333:4444:5555:6666:7777:8888")
        self.ipv6test(False, ":2222:3333:4444:5555:6666:7777:8888")
        self.ipv6test(False, ":1111:2222:3333:4444:5555:6666:7777:8888")

        # :::
        self.ipv6test(False, ":::2222:3333:4444:5555:6666:7777:8888")
        self.ipv6test(False, "1111:::3333:4444:5555:6666:7777:8888")
        self.ipv6test(False, "1111:2222:::4444:5555:6666:7777:8888")
        self.ipv6test(False, "1111:2222:3333:::5555:6666:7777:8888")
        self.ipv6test(False, "1111:2222:3333:4444:::6666:7777:8888")
        self.ipv6test(False, "1111:2222:3333:4444:5555:::7777:8888")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:::8888")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:7777:::")

        # Double ::")
        self.ipv6test(False, "::2222::4444:5555:6666:7777:8888")
        self.ipv6test(False, "::2222:3333::5555:6666:7777:8888")
        self.ipv6test(False, "::2222:3333:4444::6666:7777:8888")
        self.ipv6test(False, "::2222:3333:4444:5555::7777:8888")
        self.ipv6test(False, "::2222:3333:4444:5555:7777::8888")
        self.ipv6test(False, "::2222:3333:4444:5555:7777:8888::")

        self.ipv6test(False, "1111::3333::5555:6666:7777:8888")
        self.ipv6test(False, "1111::3333:4444::6666:7777:8888")
        self.ipv6test(False, "1111::3333:4444:5555::7777:8888")
        self.ipv6test(False, "1111::3333:4444:5555:6666::8888")
        self.ipv6test(False, "1111::3333:4444:5555:6666:7777::")

        self.ipv6test(False, "1111:2222::4444::6666:7777:8888")
        self.ipv6test(False, "1111:2222::4444:5555::7777:8888")
        self.ipv6test(False, "1111:2222::4444:5555:6666::8888")
        self.ipv6test(False, "1111:2222::4444:5555:6666:7777::")

        self.ipv6test(False, "1111:2222:3333::5555::7777:8888")
        self.ipv6test(False, "1111:2222:3333::5555:6666::8888")
        self.ipv6test(False, "1111:2222:3333::5555:6666:7777::")

        self.ipv6test(False, "1111:2222:3333:4444::6666::8888")
        self.ipv6test(False, "1111:2222:3333:4444::6666:7777::")

        self.ipv6test(False, "1111:2222:3333:4444:5555::7777::")

        # Too many components"
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:7777:8888:1.2.3.4")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:7777:1.2.3.4")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666::1.2.3.4")
        self.ipv6test(False, "::2222:3333:4444:5555:6666:7777:1.2.3.4")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:1.2.3.4.5")

        # Too few components
        self.ipv6test(False, "1111:2222:3333:4444:5555:1.2.3.4")
        self.ipv6test(False, "1111:2222:3333:4444:1.2.3.4")
        self.ipv6test(False, "1111:2222:3333:1.2.3.4")
        self.ipv6test(False, "1111:2222:1.2.3.4")
        self.ipv6test(False, "1111:1.2.3.4")

        # Missing :
        self.ipv6test(False, "11112222:3333:4444:5555:6666:1.2.3.4")
        self.ipv6test(False, "1111:22223333:4444:5555:6666:1.2.3.4")
        self.ipv6test(False, "1111:2222:33334444:5555:6666:1.2.3.4")
        self.ipv6test(False, "1111:2222:3333:44445555:6666:1.2.3.4")
        self.ipv6test(False, "1111:2222:3333:4444:55556666:1.2.3.4")
        self.ipv6test(False, "1111:2222:3333:4444:5555:66661.2.3.4")

        # Missing .
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:255255.255.255")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:255.255255.255")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:255.255.255255")

        # Missing : intended for ::
        self.ipv6test(False, ":1.2.3.4")
        self.ipv6test(False, ":6666:1.2.3.4")
        self.ipv6test(False, ":5555:6666:1.2.3.4")
        self.ipv6test(False, ":4444:5555:6666:1.2.3.4")
        self.ipv6test(False, ":3333:4444:5555:6666:1.2.3.4")
        self.ipv6test(False, ":2222:3333:4444:5555:6666:1.2.3.4")
        self.ipv6test(False, ":1111:2222:3333:4444:5555:6666:1.2.3.4")

        # :::
        self.ipv6test(False, ":::2222:3333:4444:5555:6666:1.2.3.4")
        self.ipv6test(False, "1111:::3333:4444:5555:6666:1.2.3.4")
        self.ipv6test(False, "1111:2222:::4444:5555:6666:1.2.3.4")
        self.ipv6test(False, "1111:2222:3333:::5555:6666:1.2.3.4")
        self.ipv6test(False, "1111:2222:3333:4444:::6666:1.2.3.4")
        self.ipv6test(False, "1111:2222:3333:4444:5555:::1.2.3.4")

        # Double ::
        self.ipv6test(False, "::2222::4444:5555:6666:1.2.3.4")
        self.ipv6test(False, "::2222:3333::5555:6666:1.2.3.4")
        self.ipv6test(False, "::2222:3333:4444::6666:1.2.3.4")
        self.ipv6test(False, "::2222:3333:4444:5555::1.2.3.4")

        self.ipv6test(False, "1111::3333::5555:6666:1.2.3.4")
        self.ipv6test(False, "1111::3333:4444::6666:1.2.3.4")
        self.ipv6test(False, "1111::3333:4444:5555::1.2.3.4")

        self.ipv6test(False, "1111:2222::4444::6666:1.2.3.4")
        self.ipv6test(False, "1111:2222::4444:5555::1.2.3.4")

        self.ipv6test(False, "1111:2222:3333::5555::1.2.3.4")

        # Missing parts
        self.ipv6test(False, "::.")
        self.ipv6test(False, "::..")
        self.ipv6test(False, "::...")
        self.ipv6test(False, "::1...")
        self.ipv6test(False, "::1.2..")
        self.ipv6test(False, "::1.2.3.")
        self.ipv6test(False, "::.2..")
        self.ipv6test(False, "::.2.3.")
        self.ipv6test(False, "::.2.3.4")
        self.ipv6test(False, "::..3.")
        self.ipv6test(False, "::..3.4")
        self.ipv6test(False, "::...4")

        # Extra : in front
        self.ipv6test(False, ":1111:2222:3333:4444:5555:6666:7777::")
        self.ipv6test(False, ":1111:2222:3333:4444:5555:6666::")
        self.ipv6test(False, ":1111:2222:3333:4444:5555::")
        self.ipv6test(False, ":1111:2222:3333:4444::")
        self.ipv6test(False, ":1111:2222:3333::")
        self.ipv6test(False, ":1111:2222::")
        self.ipv6test(False, ":1111::")
        self.ipv6test(False, ":::")
        self.ipv6test(False, ":1111:2222:3333:4444:5555:6666::8888")
        self.ipv6test(False, ":1111:2222:3333:4444:5555::8888")
        self.ipv6test(False, ":1111:2222:3333:4444::8888")
        self.ipv6test(False, ":1111:2222:3333::8888")
        self.ipv6test(False, ":1111:2222::8888")
        self.ipv6test(False, ":1111::8888")
        self.ipv6test(False, ":::8888")
        self.ipv6test(False, ":1111:2222:3333:4444:5555::7777:8888")
        self.ipv6test(False, ":1111:2222:3333:4444::7777:8888")
        self.ipv6test(False, ":1111:2222:3333::7777:8888")
        self.ipv6test(False, ":1111:2222::7777:8888")
        self.ipv6test(False, ":1111::7777:8888")
        self.ipv6test(False, ":::7777:8888")
        self.ipv6test(False, ":1111:2222:3333:4444::6666:7777:8888")
        self.ipv6test(False, ":1111:2222:3333::6666:7777:8888")
        self.ipv6test(False, ":1111:2222::6666:7777:8888")
        self.ipv6test(False, ":1111::6666:7777:8888")
        self.ipv6test(False, ":::6666:7777:8888")
        self.ipv6test(False, ":1111:2222:3333::5555:6666:7777:8888")
        self.ipv6test(False, ":1111:2222::5555:6666:7777:8888")
        self.ipv6test(False, ":1111::5555:6666:7777:8888")
        self.ipv6test(False, ":::5555:6666:7777:8888")
        self.ipv6test(False, ":1111:2222::4444:5555:6666:7777:8888")
        self.ipv6test(False, ":1111::4444:5555:6666:7777:8888")
        self.ipv6test(False, ":::4444:5555:6666:7777:8888")
        self.ipv6test(False, ":1111::3333:4444:5555:6666:7777:8888")
        self.ipv6test(False, ":::3333:4444:5555:6666:7777:8888")
        self.ipv6test(False, ":::2222:3333:4444:5555:6666:7777:8888")
        self.ipv6test(False, ":1111:2222:3333:4444:5555:6666:1.2.3.4")
        self.ipv6test(False, ":1111:2222:3333:4444:5555::1.2.3.4")
        self.ipv6test(False, ":1111:2222:3333:4444::1.2.3.4")
        self.ipv6test(False, ":1111:2222:3333::1.2.3.4")
        self.ipv6test(False, ":1111:2222::1.2.3.4")
        self.ipv6test(False, ":1111::1.2.3.4")
        self.ipv6test(False, ":::1.2.3.4")
        self.ipv6test(False, ":1111:2222:3333:4444::6666:1.2.3.4")
        self.ipv6test(False, ":1111:2222:3333::6666:1.2.3.4")
        self.ipv6test(False, ":1111:2222::6666:1.2.3.4")
        self.ipv6test(False, ":1111::6666:1.2.3.4")
        self.ipv6test(False, ":::6666:1.2.3.4")
        self.ipv6test(False, ":1111:2222:3333::5555:6666:1.2.3.4")
        self.ipv6test(False, ":1111:2222::5555:6666:1.2.3.4")
        self.ipv6test(False, ":1111::5555:6666:1.2.3.4")
        self.ipv6test(False, ":::5555:6666:1.2.3.4")
        self.ipv6test(False, ":1111:2222::4444:5555:6666:1.2.3.4")
        self.ipv6test(False, ":1111::4444:5555:6666:1.2.3.4")
        self.ipv6test(False, ":::4444:5555:6666:1.2.3.4")
        self.ipv6test(False, ":1111::3333:4444:5555:6666:1.2.3.4")
        self.ipv6test(False, ":::2222:3333:4444:5555:6666:1.2.3.4")

        # Extra : at end
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:7777:::")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:::")
        self.ipv6test(False, "1111:2222:3333:4444:5555:::")
        self.ipv6test(False, "1111:2222:3333:4444:::")
        self.ipv6test(False, "1111:2222:3333:::")
        self.ipv6test(False, "1111:2222:::")
        self.ipv6test(False, "1111:::")
        self.ipv6test(False, ":::")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666::8888:")
        self.ipv6test(False, "1111:2222:3333:4444:5555::8888:")
        self.ipv6test(False, "1111:2222:3333:4444::8888:")
        self.ipv6test(False, "1111:2222:3333::8888:")
        self.ipv6test(False, "1111:2222::8888:")
        self.ipv6test(False, "1111::8888:")
        self.ipv6test(False, "::8888:")
        self.ipv6test(False, "1111:2222:3333:4444:5555::7777:8888:")
        self.ipv6test(False, "1111:2222:3333:4444::7777:8888:")
        self.ipv6test(False, "1111:2222:3333::7777:8888:")
        self.ipv6test(False, "1111:2222::7777:8888:")
        self.ipv6test(False, "1111::7777:8888:")
        self.ipv6test(False, "::7777:8888:")
        self.ipv6test(False, "1111:2222:3333:4444::6666:7777:8888:")
        self.ipv6test(False, "1111:2222:3333::6666:7777:8888:")
        self.ipv6test(False, "1111:2222::6666:7777:8888:")
        self.ipv6test(False, "1111::6666:7777:8888:")
        self.ipv6test(False, "::6666:7777:8888:")
        self.ipv6test(False, "1111:2222:3333::5555:6666:7777:8888:")
        self.ipv6test(False, "1111:2222::5555:6666:7777:8888:")
        self.ipv6test(False, "1111::5555:6666:7777:8888:")
        self.ipv6test(False, "::5555:6666:7777:8888:")
        self.ipv6test(False, "1111:2222::4444:5555:6666:7777:8888:")
        self.ipv6test(False, "1111::4444:5555:6666:7777:8888:")
        self.ipv6test(False, "::4444:5555:6666:7777:8888:")
        self.ipv6test(False, "1111::3333:4444:5555:6666:7777:8888:")
        self.ipv6test(False, "::3333:4444:5555:6666:7777:8888:")
        self.ipv6test(False, "::2222:3333:4444:5555:6666:7777:8888:")

        # Additional cases:
        # http://crisp.tweakblogs.net/blog/2031/ipv6-validation-%28and-caveats%29.html
        self.ipv6test(True, "0:a:b:c:d:e:f::")
        # syntactically correct, but bad form (::0:... could be combined)
        self.ipv6test(True, '::0:a:b:c:d:e:f')
        self.ipv6test(True, "a:b:c:d:e:f:0::")
        self.ipv6test(False, "':10.0.0.1")

    def _test_T76286_failures(self):
        """Test known bugs in the ipaddress module."""
        # The following fail with the ipaddress module. See T76286
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:00.00.00.00")
        self.ipv6test(False, "1111:2222:3333:4444:5555:6666:000.000.000.000")

    def _test_T105443_failures(self):
        """Test known bugs with ipaddr v2.1.10."""
        self.ipv6test(False, "02001:0000:1234:0000:0000:C1C0:ABCD:0876")  # extra 0 not allowed!
        self.ipv6test(False, "2001:0000:1234:0000:00001:C1C0:ABCD:0876")  # extra 0 not allowed!


class IPRegexTestCase(TestIPBase, DeprecationTestCase):

    """Test IP regex."""

    def _do_ip_test(self, address):
        return bool(ip.ip_regexp.match(address))

    def test_regex(self):
        """Test IP regex."""
        self._run_tests()
        self._test_T76286_failures()
        self._test_T105443_failures()
        self.assertEqual(self.fail, 0)
        self.assertDeprecationParts('page.ip_regexp', 'tools.ip.is_IP')
        self.assertEqual(self.total, len(self.deprecation_messages))


class IPAddressModuleTestCase(TestIPBase):

    """Test ipaddress module."""

    def _do_ip_test(self, address):
        return ip.is_IP(address)

    @classmethod
    def setUpClass(cls):
        """Check ipaddress module is available."""
        if ip.ip_address.__name__ == 'ip_address_fake':
            raise unittest.SkipTest('module ipaddress not available')

        super(IPAddressModuleTestCase, cls).setUpClass()

    def test_ipaddress_module(self):
        """Test ipaddress module."""
        unittest_print('testing {0}'.format(ip.ip_address.__module__))
        self._run_tests()
        self.assertEqual(self.fail, 0)

    @expected_failure_if(ip.ip_address.__module__ == 'ipaddress' or
                         ip.ip_address.__name__ == 'ip_address_patched')
    def test_T76286_failures(self):
        """Test known bugs in the ipaddress module."""
        self._test_T76286_failures()
        self.assertEqual(self.fail, 0)

    @expected_failure_if(ip.ip_address.__module__ == 'ipaddr' and
                         ip._ipaddr_version == StrictVersion('2.1.10'))
    def test_T105443_failures(self):
        """Test known bugs in the ipaddr module."""
        self._test_T105443_failures()
        self.assertEqual(self.fail, 0)

if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
