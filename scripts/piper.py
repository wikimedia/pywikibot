#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot uses external filtering programs for munging text.

For example:

    python pwb.py piper -filter:"tr A-Z a-z" -page:Wikipedia:Sandbox

Would lower case the article with tr(1).

Muliple -filter commands can be specified:

    python pwb.py piper -filter:cat -filter:"tr A-Z a-z" -filter:"tr a-z A-Z" \
        -page:Wikipedia:Sandbox


Would pipe the article text through cat(1) (NOOP) and then lower case
it with tr(1) and upper case it again with tr(1)

The following parameters are supported:

&params;

    -always        Always commit changes without asking you to accept them

    -filter:       Filter the article text through this program, can be
                   given multiple times to filter through multiple programs in
                   the order which they are given
"""
#
# (C) Pywikibot team, 2008-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import os
import pipes
import tempfile

import pywikibot

from pywikibot import pagegenerators
from pywikibot.bot import (MultipleSitesBot, ExistingPageBot,
                           NoRedirectPageBot, AutomaticTWSummaryBot)
from pywikibot.tools import UnicodeType

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class PiperBot(MultipleSitesBot, ExistingPageBot, NoRedirectPageBot,
               AutomaticTWSummaryBot):

    """Bot for munging text using external filtering programs."""

    summary_key = 'piper-edit-summary'

    def __init__(self, generator, **kwargs):
        """
        Constructor.

        @param generator: The page generator that determines on which pages
            to work on.
        @type generator: generator
        """
        self.availableOptions.update({
            'filters': [],
        })
        super(PiperBot, self).__init__(generator=generator, **kwargs)

    @property
    def summary_parameters(self):
        """Return the filter parameter."""
        return {'filters': ', '.join(self.getOption('filters'))}

    def pipe(self, program, text):
        """Pipe a given text through a given program.

        @return: processed text after piping
        @rtype: unicode
        """
        if not isinstance(text, str):  # py2-py3 compatibility
            text = text.encode('utf-8')
        pipe = pipes.Template()
        pipe.append(str(program), '--')  # py2-py3 compatibility

        # Create a temporary filename to save the piped stuff to
        tempFilename = '%s.%s' % (tempfile.mktemp(), 'txt')
        with pipe.open(tempFilename, 'w') as file:
            file.write(text)

        # Now retrieve the munged text
        with open(tempFilename, 'r') as file:
            unicode_text = file.read()
        if not isinstance(unicode_text, UnicodeType):  # py2-py3 compatibility
            unicode_text = unicode_text.decode('utf-8')

        # clean up
        os.unlink(tempFilename)
        return unicode_text

    def treat_page(self):
        """Load the given page, do some changes, and save it."""
        # Load the page
        text = self.current_page.text

        # Munge!
        for program in self.getOption('filters'):
            text = self.pipe(program, text)

        # only save if something was changed
        self.put_current(text)


def main(*args):
    """Create and run a PiperBot instance from the given command arguments."""
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()
    # The program to pipe stuff through
    filters = []
    options = {}

    # Parse command line arguments
    for arg in local_args:
        option, sep, value = arg.partition(':')
        if option == '-filter':
            filters.append(value)
        elif option == '-always':
            options['always'] = True
        else:
            # check if a standard argument like
            # -start:XYZ or -ref:Asdf was given.
            genFactory.handleArg(arg)

    options['filters'] = filters

    gen = genFactory.getCombinedGenerator(preload=True)
    if gen:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        bot = PiperBot(gen, **options)
        bot.run()
        return True
    else:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False


if __name__ == '__main__':
    main()
