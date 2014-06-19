#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This bot takes its input from a file that contains a number of
pages to be put on the wiki. The pages should all have the same
begin and end text (which may not overlap).

By default the text should have the intended title of the page
as the first text in bold (that is, between ''' and '''),
you can modify this behavior with command line options.

The default is not to include the begin and
end text in the page, if you want to include that text, use
the -include option.

Specific arguments:
-start:xxx      Specify the text that marks the beginning of a page
-end:xxx        Specify the text that marks the end of a page
-file:xxx       Give the filename we are getting our material from
-include        The beginning and end markers should be included
                in the page.
-titlestart:xxx Use xxx in place of ''' for identifying the
                beginning of page title
-titleend:xxx   Use xxx in place of ''' for identifying the
                end of page title
-notitle        do not include the title, including titlestart, and
                titleend, in the page
-nocontent      If page has this statment it dosen't append
                (example: -nocontent:"{{infobox")
-summary:xxx    Use xxx as the edit summary for the upload - if
                a page exists, standard messages are appended
                after xxx for appending, prepending, or replacement
-autosummary    Use MediaWikis autosummary when creating a new page,
                overrides -summary in this case
-minor          set minor edit flag on page edits

If the page to be uploaded already exists:
-safe           do nothing (default)
-appendtop      add the text to the top of it
-appendbottom   add the text to the bottom of it
-force          overwrite the existing page
"""
#
# (C) Andre Engels, 2004
# (C) Pywikibot team, 2005-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re
import codecs
import pywikibot
from pywikibot import config, Bot, i18n


class NoTitle(Exception):
    """No title found"""
    def __init__(self, offset):
        self.offset = offset


class PageFromFileRobot(Bot):
    """
    Responsible for writing pages to the wiki, with the titles and contents
    given by a PageFromFileReader.
    """

    def __init__(self, reader, **kwargs):
        self.availableOptions.update({
            'force': False,
            'append': None,
            'summary': None,
            'minor': False,
            'autosummary': False,
            'nocontent': '',
        })

        super(PageFromFileRobot, self).__init__(**kwargs)
        self.reader = reader

    def run(self):
        for title, contents in self.reader.run():
            self.save(title, contents)

    def save(self, title, contents):
        mysite = pywikibot.Site()

        page = pywikibot.Page(mysite, title)
        # Show the title of the page we're working on.
        # Highlight the title in purple.
        pywikibot.output(u">>> \03{lightpurple}%s\03{default} <<<"
                         % page.title())

        if self.getOption('summary'):
            comment = self.getOption('summary')
        else:
            comment = i18n.twtranslate(mysite, 'pagefromfile-msg')

        comment_top = comment + " - " + i18n.twtranslate(
            mysite, 'pagefromfile-msg_top')
        comment_bottom = comment + " - " + i18n.twtranslate(
            mysite, 'pagefromfile-msg_bottom')
        comment_force = "%s *** %s ***" % (
            comment, i18n.twtranslate(mysite, 'pagefromfile-msg_force'))

        # Remove trailing newlines (cause troubles when creating redirects)
        contents = re.sub('^[\r\n]*', '', contents)

        if page.exists():
            if self.getOption('nocontent') != u'':
                pagecontents = page.get()
                if pagecontents.find(self.getOption('nocontent')) != -1 or \
                pagecontents.find(self.getOption('nocontent').lower()) != -1:
                    pywikibot.output(u'Page has %s so it is skipped' % self.getOption('nocontent'))
                    return
            if self.getOption('append') == 'top':
                pywikibot.output(u"Page %s already exists, appending on top!"
                                     % title)
                contents = contents + page.get()
                comment = comment_top
            elif self.getOption('append') == 'bottom':
                pywikibot.output(u"Page %s already exists, appending on bottom!"
                                     % title)
                contents = page.get() + contents
                comment = comment_bottom
            elif self.getOption('force'):
                pywikibot.output(u"Page %s already exists, ***overwriting!"
                                 % title)
                comment = comment_force
            else:
                pywikibot.output(u"Page %s already exists, not adding!" % title)
                return
        else:
            if self.getOption('autosummary'):
                comment = ''
                config.default_edit_summary = ''
        try:
            page.text = contents
            page.save(comment, minor=self.getOption('minor'))
        except pywikibot.LockedPage:
            pywikibot.output(u"Page %s is locked; skipping." % title)
        except pywikibot.EditConflict:
            pywikibot.output(u'Skipping %s because of edit conflict' % title)
        except pywikibot.SpamfilterError as error:
            pywikibot.output(
                u'Cannot change %s because of spam blacklist entry %s'
                % (title, error.url))


class PageFromFileReader:
    """
    Responsible for reading the file.

    The run() method yields a (title, contents) tuple for each found page.
    """
    def __init__(self, filename, pageStartMarker, pageEndMarker,
                 titleStartMarker, titleEndMarker, include, notitle):
        self.filename = filename
        self.pageStartMarker = pageStartMarker
        self.pageEndMarker = pageEndMarker
        self.titleStartMarker = titleStartMarker
        self.titleEndMarker = titleEndMarker
        self.include = include
        self.notitle = notitle

    def run(self):
        pywikibot.output('Reading \'%s\'...' % self.filename)
        try:
            f = codecs.open(self.filename, 'r',
                            encoding=config.textfile_encoding)
        except IOError as err:
            pywikibot.output(str(err))
            return

        text = f.read()
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

            position += length
            yield title, contents

    def findpage(self, text):
        pageR = re.compile(re.escape(self.pageStartMarker) + "(.*?)" +
                           re.escape(self.pageEndMarker), re.DOTALL)
        titleR = re.compile(re.escape(self.titleStartMarker) + "(.*?)" +
                            re.escape(self.titleEndMarker))

        location = pageR.search(text)
        if self.include:
            contents = location.group()
        else:
            contents = location.group(1)
        try:
            title = titleR.search(contents).group(1)
            if self.notitle:
                # Remove title (to allow creation of redirects)
                contents = titleR.sub('', contents, count=1)
        except AttributeError:
            raise NoTitle(location.end())
        else:
            return location.end(), title, contents


def main():
    # Adapt these to the file you are using. 'pageStartMarker' and
    # 'pageEndMarker' are the beginning and end of each entry. Take text that
    # should be included and does not occur elsewhere in the text.

    # TODO: make config variables for these.
    filename = "dict.txt"
    pageStartMarker = "{{-start-}}"
    pageEndMarker = "{{-stop-}}"
    titleStartMarker = u"'''"
    titleEndMarker = u"'''"
    options = {}
    include = False
    notitle = False

    for arg in pywikibot.handleArgs():
        if arg.startswith("-start:"):
            pageStartMarker = arg[7:]
        elif arg.startswith("-end:"):
            pageEndMarker = arg[5:]
        elif arg.startswith("-file:"):
            filename = arg[6:]
        elif arg == "-include":
            include = True
        elif arg.startswith('-append') and arg[7:] in ('top', 'bottom'):
            options['append'] = arg[7:]
        elif arg == "-force":
            options['force'] = True
        elif arg == "-safe":
            options['force'] = False
            options['append'] = None
        elif arg == '-notitle':
            notitle = True
        elif arg == '-minor':
            options['minor'] = True
        elif arg.startswith('-nocontent:'):
            options['nocontent'] = arg[11:]
        elif arg.startswith("-titlestart:"):
            titleStartMarker = arg[12:]
        elif arg.startswith("-titleend:"):
            titleEndMarker = arg[10:]
        elif arg.startswith("-summary:"):
            options['summary'] = arg[9:]
        elif arg == '-autosummary':
            options['autosummary'] = True
        else:
            pywikibot.output(u"Disregarding unknown argument %s." % arg)

    reader = PageFromFileReader(filename, pageStartMarker, pageEndMarker,
                                titleStartMarker, titleEndMarker, include,
                                notitle)
    bot = PageFromFileRobot(reader, **options)
    bot.run()

if __name__ == "__main__":
    main()
