#!/usr/bin/python
# -*- coding: utf-8 -*-
"""

This bot applies to wikisource sites to upload text.

Text is uploaded to not-(yet)-existing pages in Page ns, for a specified Index.
Text to be stored, if the page is not-existing, is preloaded from the file used
to create the Index page, making the upload feature independent from the format
of the file, as long as it is supported by the MW ProofreadPage extension.

The following parameters are supported:

    -index:...     name of the index page

    -pages:<start>-<end>,...<start>-<end>,<start>-<end>
                   Page range to upload;
                   optional, start=1, end=djvu file number of images.
                   Page ranges can be specified as:
                     A-B -> pages A until B
                     A-  -> pages A until number of images
                     A   -> just page A
                     -B  -> pages 1 until B

    -summary:      custom edit summary.
                   Use quotes if edit summary contains spaces.

    -always        don't bother asking to confirm any of the changes.

"""
#
# (C) Pywikibot team, 2016-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import itertools

import pywikibot

from pywikibot import i18n

from pywikibot.bot import SingleSiteBot
from pywikibot.proofreadpage import IndexPage
from pywikibot.tools import issue_deprecation_warning


class UploadTextBot(SingleSiteBot):

    """
    A bot that uploads text-layer to Page:namespace.

    Text is fetched via preload as on Wikisource wikis, text can be preloaded
    only if a page does not exist, if an Index page is present.

    Works only on sites with Proofread Page extension installed.
    """

    def __init__(self, generator, **kwargs):
        """
        Constructor.

        @param generator: page generator
        @type generator: generator
        """
        self.availableOptions.update({
            'summary': 'Bot: uploading text'
        })
        super(UploadTextBot, self).__init__(**kwargs)
        self.generator = generator

        # TODO: create i18 files
        # Get edit summary message if it's empty.
        if not self.getOption('summary'):
            self.options['summary'] = i18n.twtranslate(
                self.site, 'djvutext-creating')

    def treat(self, page):
        """Process one page."""
        old_text = ''
        new_text = page.text

        summary = self.getOption('summary')
        if page.exists():
            pywikibot.output('Page %s already exists, not adding!' % page)
        else:
            self.userPut(page, old_text, new_text, summary=summary,
                         show_diff=self.getOption('showdiff'))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    index = None
    pages = '1-'
    options = {}

    # Parse command line arguments.
    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        arg, sep, value = arg.partition(':')
        if arg == '-index':
            index = value
        elif arg == '-pages':
            pages = value
        elif arg == '-showdiff':
            issue_deprecation_warning('The usage of -showdiff option', None, 0)
        elif arg == '-summary':
            options['summary'] = value
        elif arg == '-force':
            issue_deprecation_warning('The usage of -force option', None, 0)
        elif arg == '-always':
            options['always'] = True
        else:
            pywikibot.output('Unknown argument %s' % arg)

    # index is mandatory.
    if not index:
        pywikibot.bot.suggest_help(missing_parameters=['-index'])
        return False

    site = pywikibot.Site()
    if not site.has_extension('ProofreadPage'):
        pywikibot.error('Site %s must have ProofreadPage extension.' % site)
        return False

    index = IndexPage(site, index)

    if not index.exists():
        pywikibot.error("Page %s doesn't exist." % index)
        return False

    # Parse pages param.
    # Create a list of (start, end) tuples.
    pages = pages.split(',')
    for interval in range(len(pages)):
        start, sep, end = pages[interval].partition('-')
        start = 1 if not start else int(start)
        if not sep:
            end = start
        else:
            end = int(end) if end else index.num_pages
        pages[interval] = (start, end)

    gen_list = []
    for start, end in sorted(pages):
        gen = index.page_gen(start=start, end=end,
                             filter_ql=[1], content=False)
        gen_list.append(gen)

    gen = itertools.chain(*gen_list)

    pywikibot.output('\nUploading text to %s\n' % index.title(asLink=True))

    bot = UploadTextBot(gen, site=index.site, **options)
    bot.run()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        pywikibot.error('Fatal error:', exc_info=True)
