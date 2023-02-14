#!/usr/bin/env python3
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
# (C) Pywikibot team, 2004-2022
#
# Distributed under the terms of the MIT license.
#
import codecs
import os
import re

import pywikibot
from pywikibot import config, i18n
from pywikibot.backports import Iterator, Tuple
from pywikibot.bot import CurrentPageBot, OptionHandler, SingleSiteBot
from pywikibot.pagegenerators import PreloadingGenerator
from pywikibot.tools.collections import GeneratorWrapper


CTX_ATTR = '_content_ctx'


class NoTitleError(Exception):

    """No title found."""

    def __init__(self, offset) -> None:
        """Initializer."""
        self.offset = offset


class PageFromFileRobot(SingleSiteBot, CurrentPageBot):

    """
    Responsible for writing pages to the wiki.

    Titles and contents are given by a PageFromFileReader.

    """

    update_options = {
        'force': False,
        'append': None,
        'summary': '',
        'minor': False,
        'autosummary': False,
        'nocontent': '',
        'redirect': True,
        'showdiff': False,
    }

    def treat_page(self) -> None:
        """Upload page content."""
        page = self.current_page
        title = page.title()
        # save the content retrieved from generator
        contents = getattr(page, CTX_ATTR)

        if self.opt.summary:
            comment = self.opt.summary
        else:
            comment = i18n.twtranslate(self.site, 'pagefromfile-msg')

        comment_top = comment + ' - ' + i18n.twtranslate(
            self.site, 'pagefromfile-msg_top')
        comment_bottom = comment + ' - ' + i18n.twtranslate(
            self.site, 'pagefromfile-msg_bottom')
        comment_force = '{} *** {} ***'.format(
            comment, i18n.twtranslate(self.site, 'pagefromfile-msg_force'))

        if page.exists():
            if not self.opt.redirect and page.isRedirectPage():
                pywikibot.info(f'Page {title} is redirect, skipping!')
                return
            pagecontents = page.text
            nocontent = self.opt.nocontent
            if (nocontent
                    and (nocontent in pagecontents
                         or nocontent.lower() in pagecontents)):
                pywikibot.info(f'Page has {nocontent} so it is skipped')
                return
            if self.opt.append:
                separator = self.opt.append[1]
                if separator == r'\n':
                    separator = '\n'
                if self.opt.append[0] == 'top':
                    above, below = contents, pagecontents
                    comment = comment_top
                else:
                    above, below = pagecontents, contents
                    comment = comment_bottom
                pywikibot.info(f'Page {title} already exists, appending on '
                               f'{self.opt.append[0]}!')
                contents = above + separator + below
            elif self.opt.force:
                pywikibot.info(f'Page {title} already exists, ***overwriting!')
                comment = comment_force
            else:
                pywikibot.info(f'Page {title} already exists, not adding!')
                return
        else:
            if self.opt.autosummary:
                comment = config.default_edit_summary = ''

        self.put_current(contents, summary=comment,
                         minor=self.opt.minor,
                         show_diff=self.opt.showdiff)


class PageFromFileReader(OptionHandler, GeneratorWrapper):

    """Generator class, responsible for reading the file.

    .. versionchanged:: 7.6
       subclassed from :class:`pywikibot.tools.collections.GeneratorWrapper`
    """

    # Adapt these to the file you are using. 'begin' and
    # 'end' are the beginning and end of each entry. Take text that
    # should be included and does not occur elsewhere in the text.

    # TODO: make config variables for these.
    available_options = {
        'begin': '{{-start-}}',
        'end': '{{-stop-}}',
        'titlestart': "'''",
        'titleend': "'''",
        'include': False,
        'notitle': False,
        'textonly': False,
        'title': None,
    }

    def __init__(self, filename, site=None, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        self.filename = filename
        self.site = site or pywikibot.Site()
        self.page_regex, self.title_regex = self._make_regexes()

    def _make_regexes(self):
        """Make regex from options."""
        if self.opt.textonly:
            pattern = '^(.*)$'
        else:
            pattern = (re.escape(self.opt.begin) + '(.*?)'
                       + re.escape(self.opt.end))
        page_regex = re.compile(pattern, re.DOTALL)
        title_regex = re.compile(
            re.escape(self.opt.titlestart) + '(.*?)'
            + re.escape(self.opt.titleend))
        return page_regex, title_regex

    @property
    def generator(self) -> Iterator[pywikibot.Page]:
        """Read file and yield a page with content from file.

        content is stored as a page attribute defined by CTX_ATTR.

        .. versionchanged:: 7.6
           changed from iterator method to generator property
        """
        pywikibot.info(f"\n\nReading '{self.filename}'...")
        try:
            with codecs.open(self.filename, 'r',
                             encoding=config.textfile_encoding) as f:
                text = f.read()

        except OSError as e:
            pywikibot.error(e)
            return

        length = 0
        while text:
            try:
                length, title, contents = self.find_page(text)
            except TypeError:
                if not length:
                    pywikibot.info('\nStart or end marker not found.')
                else:
                    pywikibot.info('End of file.')
                break

            except NoTitleError as err:
                pywikibot.info('\nNo title found - skipping a page.')
                text = text[err.offset:]
            else:
                page = pywikibot.Page(self.site, title)
                setattr(page, CTX_ATTR, contents.strip())
                yield page
                text = text[length:]

    def find_page(self, text) -> Tuple[int, str, str]:
        """Find page to work on."""
        location = self.page_regex.search(text)
        if self.opt.include:
            contents = location[0]
        else:
            contents = location[1]

        title = self.opt.title
        if not title:
            try:
                title = self.title_regex.search(contents)[1]
                if self.opt.notitle:
                    # Remove title (to allow creation of redirects)
                    contents = self.title_regex.sub('', contents, count=1)
            except TypeError:
                raise NoTitleError(location.end())

        return location.end(), title, contents


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    filename = 'dict.txt'
    options = {}
    r_options = {}

    for arg in pywikibot.handle_args(args):
        arg, _, value = arg.partition(':')
        option = arg.partition('-')[2]
        # reader options
        if option in ('begin', 'end', 'titlestart', 'titleend', 'title'):
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
            pywikibot.info(f'Disregarding unknown argument {arg}.')

    options['always'] = 'showdiff' not in options

    # Check if self.file name exists. If not, ask for a new filename.
    # User can quit.
    failed_filename = False
    while not os.path.isfile(filename):
        pywikibot.info(f"\nFile '{filename}' does not exist. ")
        _input = pywikibot.input(
            'Please enter the file name [q to quit]:')
        if _input == 'q':
            failed_filename = True
            break
        filename = _input

    # show help text from the top of this file if reader failed
    # or User quit.
    if failed_filename:
        pywikibot.bot.suggest_help(missing_parameters=['-file'])
    else:
        site = pywikibot.Site()
        reader = PageFromFileReader(filename, site=site, **r_options)
        reader = PreloadingGenerator(reader)
        bot = PageFromFileRobot(generator=reader, site=site, **options)
        bot.run()


if __name__ == '__main__':
    main()
