#!/usr/bin/python
"""
A helper script to update scripts and replace deprecated parts.

This also convert compat 1.0 scripts to the new core framework.

NOTE: Please be aware that this script is not able to convert your codes
completely. It may support you with some automatic replacements and it gives
some warnings and hints for converting. Please refer to the converting guide
README-conversion.txt in the core framework folder and check your codes
finally.

The scripts asks for the .py file and converts it to
<scriptname>-new.py in the same directory. The following option is supported:

-warnonly  Do not convert the source but show warning messages. This is good
           to check already merged scripts.

usage

to convert a script and show warnings about deprecated methods:

    python pwb.py update_script <scriptname>

to show warnings about deprecated methods:

    python pwb.py update_script <scriptname> -warnonly
"""
#
# (C) Pywikibot team, 2014-2021
#
# Distributed under the terms of the MIT license.
#
import codecs
import os
import re
import sys

import pywikibot


# be careful with replacement order!
replacements = (
    #############################
    # compat 2 core replacements
    #############################
    # doc strings
    ('#\r?\n__version__.*\r?\n',
     '#\n'
     '# Automatically ported from compat branch by update_script.py script\n'),
    ('Pywikipedia bot team', 'Pywikibot team'),
    # importing changes
    ('import wikipedia(?: as pywikibot)?', 'import pywikibot'),
    ('(?<!from pywikibot )import (config|pagegenerators)',
     r'from pywikibot import \1'),
    # remove deprecated libs
    ('(?:from pywikibot.compat )?import query', ''),
    ('import catlib\r?\n', ''),
    ('import userlib\r?\n', ''),
    # change wikipedia to pywikibot, exclude URLs
    (r'(?<!\.)wikipedia\.', 'pywikibot.'),
    # site instance call
    (r'pywikibot\.getSite\s*\(\s*', 'pywikibot.Site('),
    # lang is different from code. We should use code in core
    (r'([Ss])ite\.lang(?:uage\(\))?', r'\1ite.code'),
    # change compat library classes to pywikibot intrinsic classes
    (r'catlib\.Category\s*\(\s*', 'pywikibot.Category('),
    (r'catlib\.change_category\s*\((\s*)(?P<article>.+?),\s*(?P<oldcat>.+?),',
     r'\g<article>.change_category(\1\g<oldcat>,'),
    (r'userlib\.User\s*\(\s*', 'pywikibot.User('),
    # change ImagePage to FilePage
    (r'pywikibot\.ImagePage\s*\(\s*', 'pywikibot.FilePage('),
    # deprecated title methods
    (r'\.urlname\s*\(\s*\)', '.title(as_url=True)'),
    (r'\.urlname\s*\(\s*(?:withNamespace\s*=\s*)?(True|False)+\s*\)',
     r'.title(as_url=True, with_ns=\1)'),
    (r'\.titleWithoutNamespace\s*\(\s*\)', '.title(with_ns=False)'),
    (r'\.sectionFreeTitle\s*\(\s*\)', '.title(with_section=False)'),
    (r'\.aslink\s*\(\s*\)', '.title(as_link=True)'),
    # other deprecated methods
    (r'(?<!site)\.encoding\s*\(\s*\)', '.site.encoding()'),
    (r'\.newimages\s*\(\)', ".logevents(logtype='upload')"),
    (r'\.newimages\s*\(([^)])', r".logevents(logtype='upload', \1"),
    (r'\.getRestrictions\s*\(', '.protection('),
    # new core methods and properties
    (r'\.get\s*\(\s*get_redirect\s*=\s*True\s*\)', '.text'),
    (r'(?:pywikibot|wikipedia)\.verbose', 'config.verbose_output'),
    # stopme() is done by the framework itself
    (r'(\s*)try\:\s*\r?\n\s+main\(\)\s*\r?\n\s*finally\:\s*\r?\n'
     r'\s+pywikibot\.stopme\(\)',
     r'\1main()'),
)

# some warnings which must be changed manually
warnings = (
    #############################
    # compat 2 core warnings
    #############################
    ('pywikibot.setAction(',
     'setAction() no longer works; you must pass an explicit edit summary\n'
     'message to save() or put()'),
    ('.removeImage(',
     'Page.removeImage() is deprecated and does not work at core'),
    ('.replaceImage(',
     'Page.replaceImage() is deprecated and does not work at core'),
    ('.getVersionHistory(',
     'Page.getVersionHistory() was removed. Use Page.revisions() instead.'),
    ('.fullVersionHistory(',
     'Page.fullVersionHistory() was removed. Use Page.revisions() instead.'),
    ('.contributions(',
     'User.contributions() returns a pywikibot.Timestamp object instead of a\n'
     'MediaWiki one'),
    ('.getFileMd5Sum(',
     'FilePage.getFileMd5Sum() is deprecated should be replaced by '
     'FilePage.latest_file_info.sha1'),
    (' wikipedia.',
     '"wikipedia" library has been changed to "pywikibot".'),
    ('from wikipedia import',
     '"wikipedia" library has been changed to "pywikibot". Please find the\n'
     'right way to import your object.'),
    ('from pywikibot.compat import',
     'compat module has been removed. Please refer README-conversion.txt for\n'
     'core implementation.'),
    ('query.GetData(',
     'query.GetData() should be replaced by pywikibot.data.api.Request or\n'
     'by a direct site request'),
    ('.verbose',
     'verbose_output need "from pywikibot import config" first'),
    ('templates(',
     'returns a list of templage page objects, not a list of template titles.'
     '\nPlease refer README-conversion.txt and the documentation.'),
    ('templatesWithParams(',
     'the first item of each template info is a Page object of the template,\n'
     'not the title. '
     'Please refer README-conversion.txt and the documentation.'),
    ('linkedPages(',
     'returns a PageGenerator of page objects of link targets, not a list\n'
     'of link target strings. Please refer README-conversion.txt\n'
     'and the documentation.'),
)


class ConvertBot:

    """Script conversion bot."""

    def __init__(self, filename=None, warnonly=False):
        """Initializer."""
        self.source = filename
        self.warnonly = warnonly

    def run(self):
        """Run the bot."""
        self.get_source()
        self.get_dest()
        if not self.warnonly:
            self.convert()
        self.warning()

    def get_source(self):
        """Get source script."""
        while True:
            if self.source is None:
                self.source = pywikibot.input(
                    'Please input the .py file to convert '
                    '(no input to leave):')
            if not self.source:
                sys.exit()
            if not self.source.endswith('.py'):
                self.source += '.py'
            if os.path.exists(self.source):
                break
            self.source = os.path.join('scripts', self.source)
            if os.path.exists(self.source):
                break
            pywikibot.output('{} does not exist. Please retry.'
                             .format(self.source))
            self.source = None

    def get_dest(self):
        """Ask for destination script name."""
        self.dest = '{}-new.{}'.format(*self.source.rsplit('.', 1))
        if not self.warnonly and not pywikibot.input_yn(
                'Destination file is {}.'.format(self.dest),
                default=True, automatic_quit=False):
            pywikibot.output('Quitting...')
            sys.exit()

    def convert(self):
        """Convert script."""
        with codecs.open(self.source, 'r', 'utf-8') as f:
            text = f.read()
        for r in replacements:
            text = re.sub(r[0], r[1], text)
        with codecs.open(self.dest, 'w', 'utf-8') as g:
            g.write(text)

    def warning(self):
        """Show warnings and hints."""
        filename = self.source if self.warnonly else self.dest
        with codecs.open(filename, 'r', 'utf-8') as g:
            lines = enumerate(g.readlines(), start=1)
            for i, line in lines:
                for w in warnings:
                    if w[0] in line:
                        pywikibot.warning(
                            'line {}: {}>>> {}\n'.format(i, line, w[1]))


def main():
    """Process command line arguments and invoke bot."""
    filename = None
    warnonly = False

    # Parse command line arguments for -help option
    for arg in pywikibot.handle_args():
        if arg.startswith('-warnonly'):
            warnonly = True
        elif not arg.startswith('-'):
            filename = arg
        else:
            pywikibot.warning(arg + ' is not supported')
    bot = ConvertBot(filename, warnonly)
    bot.run()


if __name__ == '__main__':
    pywikibot.stopme()  # we do not work on any site
    main()
