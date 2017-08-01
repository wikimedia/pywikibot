#!/usr/bin/python
# -*- coding: utf-8 -*-
"""

This bot applies to wikisource sites to upload text.

Text is uploaded to pages in Page ns, for a specified Index.
Text to be stored, if the page is not-existing, is preloaded from the file used
to create the Index page, making the upload feature independent from the format
of the file, as long as it is supported by the MW ProofreadPage extension.

As alternative, if '-ocr' option is selected,
https://tools.wmflabs.org/phetools OCR tool will be used to get text.
In this case, also already existing pages with quality value 'Not Proofread'
can be treated. '-force' will override existing page in this case.

The following parameters are supported:

# TODO: update params + handle quality level


    -index:...     name of the index page

    -pages:<start>-<end>,...<start>-<end>,<start>-<end>
                   Page range to upload;
                   optional, start=1, end=djvu file number of images.
                   Page ranges can be specified as:
                     A-B -> pages A until B
                     A-  -> pages A until number of images
                     A   -> just page A
                     -B  -> pages 1 until B

    -showdiff:     show difference between curent text and new text when
                   saving the page

    -ocr:          use https://tools.wmflabs.org/phetools OCR tool to get text;
                   default is False, i.e. only not-(yet)-existing pages in Page
                   ns will be treated and text will be fetched via preload.

    -force:        overwrite existing pages;
                   default is False; valid only if '-ocr' is selected.

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

import itertools

import pywikibot

from pywikibot import i18n

from pywikibot.bot import SingleSiteBot
from pywikibot.proofreadpage import IndexPage, ProofreadPage


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
            'showdiff': False,
            'force': False,
            'ocr': False,
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
        """Process one ProofreadPage page.

        @param page: page to be treated.
        @type page: ProofreadPage
        @raises: pywikibot.Error
        """
        if not isinstance(page, ProofreadPage):
            raise pywikibot.Error('Page %s must be a ProofreadPage object.'
                                  % page)

        summary = self.getOption('summary')

        if page.exists():
            old_text = page.text
        else:
            old_text = ''

        if self.getOption('ocr'):
            page.body = page.ocr()

        if (page.exists() and
                not (self.getOption('ocr') and self.getOption('force'))):
            pywikibot.output('Page %s already exists, not adding!' % page)
        else:
            self.userPut(page, old_text, page.text, summary=summary,
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
            options['showdiff'] = True
        elif arg == '-summary':
            options['summary'] = value
        elif arg == '-ocr':
            options['ocr'] = True
        elif arg == '-force':
            options['force'] = True
        elif arg == '-always':
            options['always'] = True
        else:
            pywikibot.output('Unknown argument %s' % arg)

    # index is mandatory.
    if not index:
        pywikibot.bot.suggest_help(missing_parameters=['-index'])
        return False

    # '-force' can be used with '-ocr' only.
    if 'force' in options and 'ocr' not in options:
        pywikibot.error("'-force' can be used with '-ocr' option only.")
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

    # gen yields ProofreadPage objects.
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
