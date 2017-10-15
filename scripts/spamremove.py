#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to remove links that are being or have been spammed.

Usage:

    python pwb.py spamremove www.spammedsite.com

It will use Special:Linksearch to find the pages on the wiki that link to
that site, then for each page make a proposed change consisting of removing
all the lines where that url occurs. You can choose to:
* accept the changes as proposed
* edit the page yourself to remove the offending link
* not change the page in question

Command line options:
-always           Do not ask, but remove the lines automatically. Be very
                  careful in using this option!

-protocol:        The protocol prefix (default: "http")

-summary:         A string to be used instead of the default summary

In addition, these arguments can be used to restrict changes to some pages:

&params;
"""
#
# (C) Pywikibot team, 2007-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot

from pywikibot import pagegenerators
from pywikibot.bot import (
    SingleSiteBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)
from pywikibot.editor import TextEditor
from pywikibot.tools.formatter import color_format

docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class SpamRemoveBot(SingleSiteBot, ExistingPageBot, NoRedirectPageBot,
                    AutomaticTWSummaryBot):

    """Bot to remove links that are being or have been spammed.

    @param generator: page generator with preloaded pages.
    @type generator: generator
    @param spam_external_url: an external url
    @type spam_external_url: str
    @keyword summary: summary message when given. Otherwise the default
        summary will be used
    @type summary: str
    @keyword always: Don't ask for text replacements
    @type always: bool
    """

    summary_key = 'spamremove-remove'

    def __init__(self, generator, spam_external_url, **kwargs):
        """Constructor."""
        self.availableOptions.update({
            'summary': None,
        })
        super(SpamRemoveBot, self).__init__(**kwargs)
        self.generator = generator
        self.spam_external_url = spam_external_url
        self.changed_pages = 0

    @property
    def summary_parameters(self):
        """A dictionary of all parameters for i18n."""
        return {'url': self.spam_external_url}

    def treat_page(self):
        """Process a single page."""
        text = self.current_page.text
        if self.spam_external_url not in text:
            return
        lines = text.split('\n')
        newpage = []
        lastok = ""
        for line in lines:
            if self.spam_external_url in line:
                if lastok:
                    pywikibot.output(lastok)
                pywikibot.output(color_format('{lightred}{0}{default}', line))
                lastok = None
            else:
                newpage.append(line)
                if line.strip():
                    if lastok is None:
                        pywikibot.output(line)
                    lastok = line
        if self.getOption('always'):
            answer = "y"
        else:
            answer = pywikibot.input_choice(
                u'\nDelete the red lines?',
                [('yes', 'y'), ('no', 'n'), ('edit', 'e')],
                'n', automatic_quit=False)
        if answer == "n":
            return
        elif answer == "e":
            editor = TextEditor()
            newtext = editor.edit(text, highlight=self.spam_external_url,
                                  jumpIndex=text.find(self.spam_external_url))
        else:
            newtext = "\n".join(newpage)
        if newtext != text:
            self.put_current(newtext, summary=self.getOption('summary'))


def main(*args):
    """
    Process command line arguments and perform task.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    spam_external_url = None
    protocol = 'http'
    options = {}
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()
    for arg in local_args:
        if arg == '-always':
            options['always'] = True
        elif arg.startswith('-protocol:'):
            protocol = arg.partition(':')[2]
        elif arg.startswith('-summary:'):
            options['summary'] = arg.partition(':')[2]
        elif genFactory.handleArg(arg):
            continue
        else:
            spam_external_url = arg

    if not spam_external_url:
        pywikibot.bot.suggest_help(missing_parameters=['spam site'])
        return False

    link_search = pagegenerators.LinksearchPageGenerator(spam_external_url,
                                                         protocol=protocol)
    generator = genFactory.getCombinedGenerator(gen=link_search)
    generator = pagegenerators.PreloadingGenerator(generator)

    bot = SpamRemoveBot(generator, spam_external_url, **options)
    bot.run()


if __name__ == '__main__':
    main()
