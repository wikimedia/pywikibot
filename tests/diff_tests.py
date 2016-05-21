#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Test diff module."""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import sys

from pywikibot.diff import html_comparator
from pywikibot.tools import PY2

from tests import join_html_data_path
from tests.aspects import TestCase, require_modules, unittest

if sys.version_info[0] > 2:
    from unittest.mock import patch
else:
    from mock import patch


@require_modules('bs4')
class TestDryHTMLComparator(TestCase):

    """Test html_comparator method with given strings as test cases."""

    net = False

    def test_added_context(self):
        """Test html_comparator's detection of added-context."""
        output = html_comparator('''
<tr>
  <td class="diff-addedline">line 1a</td>
  <td class="diff-addedline">line \n2a</td>
</tr>
<tr>
  <td class="diff-addedline"><span>line 1b</span></td>
  <td class="diff-addedline">line 2b<i><span></i></span></td>
</tr>''')
        self.assertEqual(output['added-context'],
                         ['line 1a', 'line \n2a', 'line 1b', 'line 2b'])

    def test_deleted_context(self):
        """Test html_comparator's detection of deleted-context."""
        output = html_comparator('''
<tr>
  <td class="diff-deletedline">line 1a</td>
  <td class="diff-deletedline">line \n2a</td>
</tr>
<tr>
  <td class="diff-deletedline"><span>line 1b</span></td>
  <td class="diff-deletedline">line 2b<i><span></i></span></td>
</tr>''')
        self.assertEqual(output['deleted-context'],
                         ['line 1a', 'line \n2a', 'line 1b', 'line 2b'])

    def test_run(self):
        """Test html_comparator using examples given in mw-api docs."""
        with open(join_html_data_path('diff.html')) as filed:
            diff_html = filed.read()
        output = html_comparator(diff_html)
        self.assertEqual(
            output,
            {'added-context': ['#REDIRECT [[Template:Unsigned IP]]'],
             'deleted-context': [
                '<small><span class="autosigned">\\u2014&nbsp;Preceding '
                '[[Wikipedia:Signatures|unsigned]] comment added by '
                '[[User:{{{1}}}|{{{1}}}]] ([[User talk:{{{1}}}|talk]] \\u2022 '
                '[[Special:Contributions/{{{1}}}|contribs]]) {{{2|}}}</span>'
                '</small><!-- Template:Unsigned --><noinclude>',
                '{{documentation}} <!-- add categories to the /doc page, '
                'not here --></noinclude>']})


@require_modules('bs4')
class TestHTMLComparator(TestCase):

    """Test html_comparator using api.php in en:wiki."""

    family = 'wikipedia'
    code = 'en'

    def test_wikipedia_rev_139992(self):
        """Test html_comparator with revision 139992 in en:wikipedia."""
        site = self.get_site()
        diff_html = site.compare(139992, 139993)
        output = html_comparator(diff_html)
        self.assertEqual(len(output['added-context']), 1)
        self.assertEqual(len(output['deleted-context']), 1)


@patch('{0}.__import__'.format('__builtin__' if PY2 else 'builtins'),
       side_effect=ImportError, autospec=True)
class TestNoBeautifulSoup(TestCase):

    """Test functions when BeautifulSoup is not installes."""

    net = False

    def test_html_comparator(self, mocked_import):
        """Test html_comparator when bs4 not installed."""
        self.assertRaises(ImportError, html_comparator, '')
        self.assertEqual(mocked_import.call_count, 1)
        self.assertIn('bs4', mocked_import.call_args[0])


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
