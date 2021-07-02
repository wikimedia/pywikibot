#!/usr/bin/python
"""

This bot applies to Wikisource sites to upload text.

Text is uploaded to pages in Page ns, for a specified Index.
Text to be stored, if the page is not-existing, is preloaded from the file used
to create the Index page, making the upload feature independent from the format
of the file, as long as it is supported by the MW ProofreadPage extension.

As alternative, if '-ocr' option is selected,
https://phetools.toolforge.org/ OCR tool will be used to get text.
In this case, also already existing pages with quality value 'Not Proofread'
can be treated. '-force' will override existing page in this case.

TODO: update params + handle quality level

The following parameters are supported:

    -index:...  name of the index page.

    -pages:<start>-<end>,...<start>-<end>,<start>-<end>
                Page range to upload;
                optional, start=1, end=djvu file number of images.
                Page ranges can be specified as:

                | A-B -> pages A until B
                | A-  -> pages A until number of images
                | A   -> just page A
                | -B  -> pages 1 until B

    -showdiff:  show difference between current text and new text when
                saving the page.

    -ocr:       use OCR tools hosted on https://toolforge.org.
                By default no OCR is done, i.e. only not-(yet)-existing
                pages in Page ns will be treated and text will be fetched
                via preload.
                If -ocr is provided, default OCR method is:
                 - https://phetools.toolforge.org/
                If ocr:googleOCR is given, OCR method is:
                 - https://ws-google-ocr.toolforge.org/

    -threads:n  number of threads used to fetch OCR from OCR tools.
                default is 5; valid only if '-ocr' is selected.

    -force:     overwrite existing pages;
                default is False; valid only if '-ocr' is selected.

    -summary:   custom edit summary.
                Use quotes if edit summary contains spaces.

    -always     don't bother asking to confirm any of the changes.
"""
#
# (C) Pywikibot team, 2016-2021
#
# Distributed under the terms of the MIT license.
#
import collections
import itertools
import queue
import threading
import time

import pywikibot
from pywikibot import i18n
from pywikibot.bot import SingleSiteBot
from pywikibot.exceptions import Error
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
        Initializer.

        If OCR is requested, spawns worker threads, and, if no "force" option
        is set, filter for existing pages.

        Queues are used for communication to/from threads.
        A PriorityQueue is used to process pages in the same order as
        they are generated.

        :param generator: page generator
        :type generator: generator
        """
        self.available_options.update({
            'showdiff': False,
            'force': False,
            'ocr': False,
            'summary': 'Bot: uploading text',
            'threads': 5
        })
        super().__init__(**kwargs)
        self.generator = generator

        # Get edit summary message if it's empty.
        if not self.opt.summary:
            self.opt.summary = i18n.twtranslate(self.site, 'djvutext-creating')

        if self.opt.ocr:
            self._num_threads = self.opt.threads
            self._queue_in = queue.Queue()
            self._queue_out = queue.PriorityQueue()

            # If not "-force", no reason to get OCR for existing pages
            # and to process them in Bot.run().
            if not self.opt.force:
                self.generator = (p for p in self.generator if not p.exists())
            self._spawn_ocr_threads()

    def _spawn_ocr_threads(self):
        """Spawn threads for _ocr_worker workers."""
        for i in range(self._num_threads):
            worker = threading.Thread(target=self._ocr_worker, daemon=True)
            worker.start()

        self._pages = collections.OrderedDict()
        for idx, p in enumerate(self.generator):
            self._pages.setdefault(p, idx)
        self.generator = (p for p in self._pages)  # recreate gen for run()

        for p, idx in self._pages.items():
            self._queue_in.put((p, idx))  # idx to preserve order later

    def _ocr_worker(self):
        """Fetch OCR content from ocr_tool and queue it."""
        while True:
            page, idx = self._queue_in.get()
            try:
                text_body = page.ocr(ocr_tool=self.opt.ocr)
            except ValueError as e:
                pywikibot.error(e)
                text_body = None  # Sentinel: signal exception to self.treat()

            self._queue_out.put((idx, text_body))
            self._queue_in.task_done()

    def _get_ocr(self, page):
        """Get OCR content for page from PriorityQueue."""
        # blocks until OCR for expected idx is available
        expected_idx = self._pages.get(page)
        while True:
            if self._queue_out.empty():
                time.sleep(0.2)  # some pause
                continue
            idx, text_body = self._queue_out.queue[0]  # peek first element
            if idx == expected_idx:
                idx, text_body = self._queue_out.get()
                return text_body

    def treat(self, page):
        """Process one ProofreadPage page.

        :param page: page to be treated.
        :type page: ProofreadPage
        :raises pywikibot.exceptions.Error: Page must be a ProofreadPage object
        """
        if not isinstance(page, ProofreadPage):
            raise Error('Page {} must be a ProofreadPage object.'
                        .format(page))

        old_text = page.text if page.exists() else ''
        if self.opt.ocr:
            _body = self._get_ocr(page)
            if _body is None:
                pywikibot.output('No OCR found. Skipping {}'
                                 .format(page.title(as_link=True)))
                return

            page.body = _body

        if page.exists() and not (self.opt.ocr and self.opt.force):
            pywikibot.output('Page {} already exists, not adding!'
                             .format(page))
        else:
            self.userPut(page, old_text, page.text, summary=self.opt.summary,
                         show_diff=self.opt.showdiff)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
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
            options['ocr'] = value or 'phetools'
        elif arg == '-threads':
            options['threads'] = int(value)
        elif arg == '-force':
            options['force'] = True
        elif arg == '-always':
            options['always'] = True
        else:
            pywikibot.output('Unknown argument ' + arg)

    # index is mandatory.
    if not index:
        pywikibot.bot.suggest_help(missing_parameters=['-index'])
        return

    # '-force' can be used with '-ocr' only.
    if 'force' in options and 'ocr' not in options:
        pywikibot.error("'-force' can be used with '-ocr' option only.")
        return

    site = pywikibot.Site()
    if not site.has_extension('ProofreadPage'):
        pywikibot.error('Site {} must have ProofreadPage extension.'
                        .format(site))
        return

    index = IndexPage(site, index)

    if not index.exists():
        pywikibot.error("Page {} doesn't exist.".format(index))
        return

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
                             filter_ql=[1], content=True)
        gen_list.append(gen)

    gen = itertools.chain(*gen_list)

    pywikibot.output('\nUploading text to {}\n'
                     .format(index.title(as_link=True)))

    bot = UploadTextBot(gen, site=index.site, **options)
    bot.run()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        pywikibot.error('Fatal error:', exc_info=True)
