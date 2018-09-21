#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
Bot to upload pages from a text file.

This bot takes its input from the UTF-8 text file that contains
a number of pages to be put on the wiki. The pages should all have
the same beginning and ending text (which may not overlap).
The beginning and ending text is not uploaded with the page content
by default.

As a pagename is by default taken the first text block
from the page content marked in bold (wrapped between ''' and ''').
If you expect the page title not to be present in the text
or marked by different markers, use -titlestart, -titleend,
and -notitle parameters.

Specific arguments:

-file:xxx       The filename we are getting our material from,
                the default value is "dict.txt"
-begin:xxx      The text that marks the beginning of a page,
                the default value is "{{-start-}}"
-end:xxx        The text that marks the end of the page,
                the default value is "{{-stop-}}"
-include        Include the beginning and end markers to the page
-textonly       Text is given without markers. Only one page text is given.
                -begin and -end options are ignored.
-titlestart:xxx The text used in place of ''' for identifying
                the beginning of a page title
-titleend:xxx   The text used in place of ''' for identifying
                the end of the page title
-notitle        Do not include the page title, including titlestart
                and titleend, to the page. Can be used to specify unique
                page title above the page content
-title:xxx      The page title is given directly. Ignores -titlestart,
                -titleend and -notitle options
-nocontent:xxx  If the existing page contains specified statement,
                the page is skipped from editing
-noredirect     Do not upload on redirect pages
-summary:xxx    The text used as an edit summary for the upload.
                If the page exists, standard messages for prepending,
                appending, or replacement are appended after it
-autosummary    Use MediaWiki's autosummary when creating a new page,
                overrides -summary
-minor          Set the minor edit flag on page edits
-showdiff       Show difference between current page and page to upload,
                also forces the bot to ask for confirmation
                on every edit

If the page to be uploaded already exists, it is skipped by default.
But you can override this behavior if you want to:

-appendtop      Add the text to the top of the existing page
-appendbottom   Add the text to the bottom of the existing page
-force          Overwrite the existing page

It is possible to define a separator after the 'append' modes which
is added between the existing and the new text. For example
a parameter -appendtop:foo would add 'foo' between them. A new line
can be added between them by specifying '\n' as a value.
"""
#
# (C) Andre Engels, 2004
# (C) Pywikibot team, 2005-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import codecs
import os
import re

from warnings import warn

import pywikibot

from pywikibot import config, i18n
from pywikibot.bot import SingleSiteBot, CurrentPageBot
from pywikibot.bot import OptionHandler
from pywikibot.exceptions import ArgumentDeprecationWarning


class NoTitle(Exception):

    """No title found."""

    def __init__(self, offset):
        """Initializer."""
        self.offset = offset


class PageFromFileRobot(SingleSiteBot, CurrentPageBot):

    """
    Responsible for writing pages to the wiki.

    Titles and contents are given by a PageFromFileReader.

    """

    def __init__(self, **kwargs):
        """Initializer."""
        self.availableOptions.update({
            'always': True,
            'force': False,
            'append': None,
            'summary': None,
            'minor': False,
            'autosummary': False,
            'nocontent': '',
            'redirect': True,
            'showdiff': False,
        })

        super(PageFromFileRobot, self).__init__(**kwargs)
        self.availableOptions.update(
            {'always': False if self.getOption('showdiff') else True})

    def init_page(self, item):
        """Get the tuple and return the page object to be processed."""
        title, content = item
        page = pywikibot.Page(self.site, title)
        page.text = content.strip()
        return super(PageFromFileRobot, self).init_page(page)

    def treat_page(self):
        """Upload page content."""
        page = self.current_page
        title = page.title()
        # save the content retrieved from generator
        contents = page.text
        # delete page's text to get it from live wiki
        del page.text

        if self.getOption('summary'):
            comment = self.getOption('summary')
        else:
            comment = i18n.twtranslate(self.site, 'pagefromfile-msg')

        comment_top = comment + " - " + i18n.twtranslate(
            self.site, 'pagefromfile-msg_top')
        comment_bottom = comment + " - " + i18n.twtranslate(
            self.site, 'pagefromfile-msg_bottom')
        comment_force = "%s *** %s ***" % (
            comment, i18n.twtranslate(self.site, 'pagefromfile-msg_force'))

        if page.exists():
            if not self.getOption('redirect') and page.isRedirectPage():
                pywikibot.output(u"Page %s is redirect, skipping!" % title)
                return
            pagecontents = page.text
            nocontent = self.getOption('nocontent')
            if nocontent and (
                    nocontent in pagecontents or
                    nocontent.lower() in pagecontents):
                pywikibot.output('Page has %s so it is skipped' % nocontent)
                return
            if self.getOption('append'):
                separator = self.getOption('append')[1]
                if separator == r'\n':
                    separator = '\n'
                if self.getOption('append')[0] == 'top':
                    above, below = contents, pagecontents
                    comment = comment_top
                else:
                    above, below = pagecontents, contents
                    comment = comment_bottom
                pywikibot.output('Page {0} already exists, appending on {1}!'
                                 .format(title, self.getOption('append')[0]))
                contents = above + separator + below
            elif self.getOption('force'):
                pywikibot.output(u"Page %s already exists, ***overwriting!"
                                 % title)
                comment = comment_force
            else:
                pywikibot.output('Page %s already exists, not adding!' % title)
                return
        else:
            if self.getOption('autosummary'):
                comment = config.default_edit_summary = ''

        self.put_current(contents, summary=comment,
                         minor=self.getOption('minor'),
                         show_diff=self.getOption('showdiff'))


class PageFromFileReader(OptionHandler):

    """Generator class, responsible for reading the file."""

    # Adapt these to the file you are using. 'begin' and
    # 'end' are the beginning and end of each entry. Take text that
    # should be included and does not occur elsewhere in the text.

    # TODO: make config variables for these.
    availableOptions = {
        'begin': '{{-start-}}',
        'end': '{{-stop-}}',
        'titlestart': "'''",
        'titleend': "'''",
        'include': False,
        'notitle': False,
        'textonly': False,
        'title': None,
    }

    def __init__(self, filename, **kwargs):
        """Initializer.

        Check if self.file name exists. If not, ask for a new filename.
        User can quit.

        """
        super(PageFromFileReader, self).__init__(**kwargs)
        self.filename = filename
        self.pageStartMarker = self.getOption('begin')
        self.pageEndMarker = self.getOption('end')
        self.titleStartMarker = self.getOption('titlestart')
        self.titleEndMarker = self.getOption('titleend')
        self.include = self.getOption('include')
        self.notitle = self.getOption('notitle')

    def __iter__(self):
        """Read file and yield a tuple of page title and content."""
        pywikibot.output('\n\nReading \'%s\'...' % self.filename)
        try:
            with codecs.open(self.filename, 'r',
                             encoding=config.textfile_encoding) as f:
                text = f.read()

        except IOError:
            pywikibot.exception()
            return

        position = 0
        length = 0
        while True:
            try:
                length, title, contents = self.findpage(text[position:])
            except AttributeError:
                if not length:
                    pywikibot.output(u'\nStart or end marker not found.')
                else:
                    pywikibot.output(u'End of file.')
                break
            except NoTitle as err:
                pywikibot.output(u'\nNo title found - skipping a page.')
                position += err.offset
                continue
            if length == 0:
                break
            position += length
            yield title, contents

    def findpage(self, text):
        """Find page to work on."""
        if self.getOption('textonly'):
            pattern = '^(.*)$'
        else:
            pattern = (re.escape(self.pageStartMarker) + '(.*?)'
                       + re.escape(self.pageEndMarker))
        page_regex = re.compile(pattern, re.DOTALL)
        title_regex = re.compile(
            re.escape(self.titleStartMarker) + '(.*?)'
            + re.escape(self.titleEndMarker))
        location = page_regex.search(text)
        if self.include:
            contents = location.group()
        else:
            contents = location.group(1)

        title = self.getOption('title')
        if not title:
            try:
                title = title_regex.search(contents).group(1)
                if self.notitle:
                    # Remove title (to allow creation of redirects)
                    contents = title_regex.sub('', contents, count=1)
            except AttributeError:
                raise NoTitle(location.end())

        return location.end(), title, contents


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: unicode
    """
    filename = "dict.txt"
    options = {}
    r_options = {}

    for arg in pywikibot.handle_args(args):
        arg, sep, value = arg.partition(':')
        option = arg.partition('-')[2]
        # reader options
        if option == 'start':
            r_options['begin'] = value
            warn('-start param (text that marks the beginning) of a page has '
                 'been deprecated in favor of begin; make sure to use the '
                 'updated param.', ArgumentDeprecationWarning)
        elif option in ('begin', 'end', 'titlestart', 'titleend', 'title'):
            r_options[option] = value
        elif option == 'file':
            filename = value
        elif option in ('include', 'notitle', 'textonly'):
            r_options[option] = True
        # bot options
        elif option == 'appendbottom':
            options['append'] = ('bottom', value)
        elif option == 'appendtop':
            options['append'] = ('top', value)
        elif option in ('force', 'minor', 'autosummary', 'showdiff'):
            options[option] = True
        elif option == 'noredirect':
            options['redirect'] = False
        elif option in ('nocontent', 'summary'):
            options[option] = value
        else:
            pywikibot.output(u"Disregarding unknown argument %s." % arg)

    failed_filename = False
    while not os.path.isfile(filename):
        pywikibot.output('\nFile \'%s\' does not exist. ' % filename)
        _input = pywikibot.input(
            'Please enter the file name [q to quit]:')
        if _input == 'q':
            failed_filename = True
            break
        else:
            filename = _input

    # show help text from the top of this file if reader failed
    # or User quit.
    if failed_filename:
        pywikibot.bot.suggest_help(missing_parameters=['-file'])
        return False
    else:
        reader = PageFromFileReader(filename, **r_options)
        bot = PageFromFileRobot(generator=reader, **options)
        bot.run()


if __name__ == "__main__":
    main()
