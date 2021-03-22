#!/usr/bin/python
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

    -always        Always commit changes without asking you to accept them

    -filter:       Filter the article text through this program, can be
                   given multiple times to filter through multiple programs in
                   the order which they are given

The following generators and filters are supported:

&params;
"""
#
# (C) Pywikibot team, 2008-2020
#
# Distributed under the terms of the MIT license.
#
import os
import pipes
import tempfile

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    ExistingPageBot,
    MultipleSitesBot,
    NoRedirectPageBot,
)


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class PiperBot(MultipleSitesBot, ExistingPageBot, NoRedirectPageBot,
               AutomaticTWSummaryBot):

    """Bot for munging text using external filtering programs."""

    summary_key = 'piper-edit-summary'

    def __init__(self, generator, **kwargs):
        """
        Initializer.

        :param generator: The page generator that determines on which pages
            to work on.
        :type generator: generator
        """
        self.available_options.update({
            'filters': [],
        })
        super().__init__(generator=generator, **kwargs)

    @property
    def summary_parameters(self) -> dict:
        """Return the filter parameter."""
        return {'filters': ', '.join(self.opt.filters)}

    def pipe(self, program: str, text: str) -> str:
        """Pipe a given text through a given program.

        :return: processed text after piping
        """
        pipe = pipes.Template()
        pipe.append(program, '--')

        # Create a temporary filename to save the piped stuff to
        file, temp_filename = tempfile.mkstemp(suffix='.txt')
        file.close()
        with pipe.open(temp_filename, 'w') as file:
            file.write(text)

        # Now retrieve the munged text
        with open(temp_filename, 'r') as file:
            text = file.read()

        # clean up
        os.unlink(temp_filename)
        return text

    def treat_page(self):
        """Load the given page, do some changes, and save it."""
        # Load the page
        text = self.current_page.text

        # Munge!
        for program in self.opt.filters:
            text = self.pipe(program, text)

        # only save if something was changed
        self.put_current(text)


def main(*args):
    """Create and run a PiperBot instance from the given command arguments."""
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    gen_factory = pagegenerators.GeneratorFactory()
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
            gen_factory.handle_arg(arg)

    options['filters'] = filters

    gen = gen_factory.getCombinedGenerator(preload=True)
    if gen:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        bot = PiperBot(gen, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
