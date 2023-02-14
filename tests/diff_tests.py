#!/usr/bin/env python3
"""Test diff module."""
#
# (C) Pywikibot team, 2016-2022
#
# Distributed under the terms of the MIT license.
from contextlib import suppress
from unittest.mock import patch

from pywikibot.diff import PatchManager, cherry_pick, html_comparator
from tests import join_html_data_path
from tests.aspects import TestCase, require_modules, unittest


@require_modules('bs4')
class TestDryHTMLComparator(TestCase):

    """Test html_comparator method with given strings as test cases."""

    net = False

    def test_added_context(self):
        """Test html_comparator's detection of added-context."""
        output = html_comparator("""
<tr>
  <td class="diff-addedline">line 1a</td>
  <td class="diff-addedline">line \n2a</td>
</tr>
<tr>
  <td class="diff-addedline"><span>line 1b</span></td>
  <td class="diff-addedline">line 2b<i><span></i></span></td>
</tr>""")
        self.assertEqual(output['added-context'],
                         ['line 1a', 'line \n2a', 'line 1b', 'line 2b'])

    def test_deleted_context(self):
        """Test html_comparator's detection of deleted-context."""
        output = html_comparator("""
<tr>
  <td class="diff-deletedline">line 1a</td>
  <td class="diff-deletedline">line \n2a</td>
</tr>
<tr>
  <td class="diff-deletedline"><span>line 1b</span></td>
  <td class="diff-deletedline">line 2b<i><span></i></span></td>
</tr>""")
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
        self.assertLength(output['added-context'], 1)
        self.assertLength(output['deleted-context'], 1)


@patch('builtins.__import__', side_effect=ImportError, autospec=True)
class TestNoBeautifulSoup(TestCase):

    """Test functions when BeautifulSoup is not installed."""

    net = False

    def test_html_comparator(self, mocked_import):
        """Test html_comparator when bs4 not installed."""
        with self.assertRaises(ImportError):
            html_comparator('')
        self.assertEqual(mocked_import.call_count, 1)
        self.assertIn('bs4', mocked_import.call_args[0])


class TestPatchManager(TestCase):

    """Test PatchManager class with given strings as test cases."""

    net = False

    # each tuple: (before, after, expected hunks
    cases = [(' test',
              '_test',
              {0: '@@ -1 +1 @@\n\n'
                  '-  test\n'
                  '? ^\n'
                  '+ _test\n'
                  '? ^\n'}),
             ('The quick brown fox jumps over the lazy dog.',
              'quick brown dog jumps quickly over the lazy fox.',
              {0: '@@ -1 +1 @@\n\n'
                  '- The quick brown fox jumps over the lazy dog.\n'
                  '? ----            ^ ^                     ^ ^\n'
                  '+ quick brown dog jumps quickly over the lazy fox.\n'
                  '?             ^ ^       ++++++++              ^ ^\n'}),
             ('spam',
              'eggs',
              {0: '@@ -1 +1 @@\n\n'
                  '- spam\n'
                  '+ eggs\n'}),
             ('Lorem\n'
              'ipsum\n'
              'dolor',
              'Quorem\n'
              'ipsum\n'
              'dolom',
              {0: '@@ -1 +1 @@\n\n'
                  '- Lorem\n'
                  '? ^\n'
                  '+ Quorem\n'
                  '? ^^\n',
               1: '@@ -3 +3 @@\n\n'
                  '- dolor\n'
                  '?     ^\n'
                  '+ dolom\n'
                  '?     ^\n'}),
             ('.foola.Pywikipediabot',
              '.foo.Pywikipediabot.foo.',
              {0: '@@ -1 +1 @@\n\n'
                  '- .foola.Pywikipediabot\n'
                  '?     --\n'
                  '+ .foo.Pywikipediabot.foo.\n'
                  '?                    +++++\n'}),
             ('{foola}Pywikipediabot',
              '{foo}Pywikipediabot{foo}',
              {0: '@@ -1 +1 @@\n\n'
                  '- {foola}Pywikipediabot\n'
                  '?     --\n'
                  '+ {foo}Pywikipediabot{foo}\n'
                  '?                    +++++\n'}),
             ('{default}Foo bar Pywikipediabot foo bar',
              '{default}Foo  bar  Pywikipediabot  foo  bar',
              {0: '@@ -1 +1 @@\n\n'
                  '- {default}Foo bar Pywikipediabot foo bar\n'
                  '+ {default}Foo  bar  Pywikipediabot  foo  bar\n'
                  '?              +   +                +    +\n'}),
             ('Pywikipediabot foo',
              'Pywikipediabot  foo',
              {0: '@@ -1 +1 @@\n\n'
                  '- Pywikipediabot foo\n'
                  '+ Pywikipediabot  foo\n'
                  '?                +\n'}),
             ('  Pywikipediabot    ',
              '   Pywikipediabot   ',
              {0: '@@ -1 +1 @@\n\n'
                  '-   Pywikipediabot    \n'
                  '?                    -\n'
                  '+    Pywikipediabot   \n'
                  '? +\n'})]

    def test_patch_manager(self):
        """Test PatchManager."""
        for case in self.cases:
            p = PatchManager(case[0], case[1])
            for key in case[2]:  # for each hunk
                with self.subTest(case=case[0].strip(), key=key):
                    self.assertEqual(p.hunks[key].diff_plain_text,
                                     case[2][key])

    def test_patch_manager_no_diff(self):
        """Test PatchManager for the same strings."""
        for context in range(2):
            p = PatchManager('Pywikibot', 'Pywikibot', context=context)
            with self.subTest(context=context):
                self.assertIsEmpty(p.hunks)


class TestCherryPick(TestCase):

    """Test cherry_pick method."""

    net = False

    # texts used during testing
    oldtext = 'old'
    newtext = 'new'

    # output messages expected during testing
    diff_message = ('<<lightred>>- old\n<<default>><<lightgreen>>+ '
                    'new\n<<default>>')
    none_message = '<<lightpurple>>{: ^50}<<default>>'.format('None.')
    header_base = '\n<<lightpurple>>{0:*^50}<<default>>\n'
    headers = ['  ALL CHANGES  ', '  REVIEW CHANGES  ', '  APPROVED CHANGES  ']
    diff_by_letter_message = ('<<lightred>>- o\n<<default>>'
                              '<<lightred>>- l\n<<default>>'
                              '<<lightred>>- d\n<<default>>'
                              '<<lightgreen>>+ n\n<<default>>'
                              '<<lightgreen>>+ e\n<<default>>'
                              '<<lightgreen>>+ w\n<<default>>')

    def check_headers(self, mock):
        """Check if all headers were added to output."""
        for header in self.headers:
            mock.assert_any_call(self.header_base.format(header))

    @patch('pywikibot.info')
    @patch('pywikibot.userinterfaces.buffer_interface.UI.input',
           return_value='y')
    def test_accept(self, input, mock):
        """Check output of cherry_pick if changes accepted."""
        self.assertEqual(cherry_pick(self.oldtext, self.newtext), self.newtext)
        self.check_headers(mock)
        mock.assert_any_call(self.diff_message)

    @patch('pywikibot.info')
    @patch('pywikibot.userinterfaces.buffer_interface.UI.input',
           return_value='n')
    def test_reject(self, input, mock):
        """Check output of cherry_pick if changes rejected."""
        self.assertEqual(cherry_pick(self.oldtext, self.newtext), self.oldtext)
        self.check_headers(mock)
        mock.assert_any_call(self.diff_message)
        mock.assert_any_call(self.none_message)

    @patch('pywikibot.info')
    @patch('pywikibot.userinterfaces.buffer_interface.UI.input',
           return_value='q')
    def test_quit(self, input, mock):
        """Check output of cherry_pick if quit."""
        self.assertEqual(cherry_pick(self.oldtext, self.newtext), self.oldtext)
        self.check_headers(mock)
        mock.assert_any_call(self.diff_message)
        mock.assert_any_call(self.none_message)

    @patch('pywikibot.info')
    @patch('pywikibot.userinterfaces.buffer_interface.UI.input',
           return_value='y')
    def test_by_letter_accept(self, input, mock):
        """Check cherry_pick output.

        If by_letter diff is enabled and changes accepted.
        """
        self.assertEqual(cherry_pick(self.oldtext, self.newtext,
                                     by_letter=True), self.newtext)
        self.check_headers(mock)
        mock.assert_any_call(self.diff_by_letter_message)

    @patch('pywikibot.info')
    @patch('pywikibot.userinterfaces.buffer_interface.UI.input',
           return_value='q')
    def test_by_letter_quit(self, input, mock):
        """Check cherry_pick output.

        If by_letter diff is enabled and quit during review.
        """
        self.assertEqual(cherry_pick(self.oldtext, self.newtext,
                                     by_letter=True), self.oldtext)
        self.check_headers(mock)
        mock.assert_any_call(self.diff_by_letter_message)
        mock.assert_any_call(self.none_message)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
