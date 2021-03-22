#!/usr/bin/python
"""
Script to remove links that are being or have been spammed.

Usage:

    python pwb.py spamremove www.spammedsite.com

It will use Special:Linksearch to find the pages on the wiki that link to
that site, then for each page make a proposed change consisting of removing
all the lines where that url occurs. You can choose to

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
# (C) Pywikibot team, 2007-2020
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    ExistingPageBot,
    NoRedirectPageBot,
    SingleSiteBot,
)
from pywikibot.editor import TextEditor
from pywikibot.tools.formatter import color_format


docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class SpamRemoveBot(SingleSiteBot, ExistingPageBot, NoRedirectPageBot,
                    AutomaticTWSummaryBot):

    """Bot to remove links that are being or have been spammed.

    :param generator: page generator with preloaded pages.
    :type generator: generator
    :param spam_external_url: an external url
    :keyword summary: summary message when given. Otherwise the default
        summary will be used
    :keyword always: Don't ask for text replacements
    :type always: bool
    """

    summary_key = 'spamremove-remove'

    def __init__(self, generator, spam_external_url: str, **kwargs):
        """Initializer."""
        self.available_options.update({
            'summary': None,
        })
        super().__init__(**kwargs)
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
        lastok = ''
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
        if self.opt.always:
            answer = 'y'
        else:
            answer = pywikibot.input_choice(
                '\nDelete the red lines?',
                [('yes', 'y'), ('no', 'n'), ('edit', 'e')],
                'n', automatic_quit=False)
        if answer == 'n':
            return
        if answer == 'e':
            editor = TextEditor()
            newtext = editor.edit(text, highlight=self.spam_external_url,
                                  jumpIndex=text.find(self.spam_external_url))
        else:
            newtext = '\n'.join(newpage)
        if newtext != text:
            self.put_current(newtext, summary=self.opt.summary)


def main(*args):
    """
    Process command line arguments and perform task.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    spam_external_url = None
    protocol = 'http'
    options = {}
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    for arg in local_args:
        if arg == '-always':
            options['always'] = True
        elif arg.startswith('-protocol:'):
            protocol = arg.partition(':')[2]
        elif arg.startswith('-summary:'):
            options['summary'] = arg.partition(':')[2]
        elif gen_factory.handle_arg(arg):
            continue
        else:
            spam_external_url = arg

    if not spam_external_url:
        pywikibot.bot.suggest_help(missing_parameters=['spam site'])
        return

    link_search = pagegenerators.LinksearchPageGenerator(spam_external_url,
                                                         protocol=protocol)
    generator = gen_factory.getCombinedGenerator(gen=link_search)
    generator = pagegenerators.PreloadingGenerator(generator)

    bot = SpamRemoveBot(generator, spam_external_url, **options)
    bot.run()


if __name__ == '__main__':
    main()
