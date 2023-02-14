#!/usr/bin/env python3
r"""
Append text to the top or bottom of a page.

By default this adds the text to the bottom above the categories and interwiki.

Use the following command line parameters to specify what to add:

-text             Text to append. "\n" are interpreted as newlines.

-textfile         Path to a file with text to append

-summary          Change summary to use

-up               Append text to the top of the page rather than the bottom

-create           Create the page if necessary. Note that talk pages are
                  created already without of this option.

-createonly       Only create the page but do not edit existing ones

-always           If used, the bot won't ask if it should add the specified
                  text

-major            If used, the edit will be saved without the "minor edit" flag

-talkpage         Put the text onto the talk page instead
-talk

-excepturl        Skip pages with a url that matches this regular expression

-noreorder        Place the text beneath the categories and interwiki

Furthermore, the following can be used to specify which pages to process...

&params;

Examples
--------

1. Append 'hello world' to the bottom of the sandbox:

    python pwb.py add_text -page:Wikipedia:Sandbox \
        -summary:"Bot: pywikibot practice" -text:"hello world"

2. Add a template to the top of the pages with 'category:catname':

    python pwb.py add_text -cat:catname -summary:"Bot: Adding a template" \
        -text:"{{Something}}" -except:"\{\{([Tt]emplate:|)[Ss]omething" -up

3. Command used on it.wikipedia to put the template in the page without any
   category:

    python pwb.py add_text -except:"\{\{([Tt]emplate:|)[Cc]ategorizzare" \
        -text:"{{Categorizzare}}" -excepturl:"class='catlinks'>" -uncat \
        -summary:"Bot: Aggiungo template Categorizzare"
"""
#
# (C) Pywikibot team, 2007-2022
#
# Distributed under the terms of the MIT license.
#
import codecs
import re
from typing import Union

import pywikibot
from pywikibot import config, pagegenerators, textlib
from pywikibot.backports import Dict, Sequence
from pywikibot.bot import AutomaticTWSummaryBot, ExistingPageBot


ARGS_TYPE = Dict[str, Union[bool, str]]
DEFAULT_ARGS: ARGS_TYPE = {
    'text': '',
    'textfile': '',
    'summary': '',
    'up': False,
    'create': False,
    'createonly': False,
    'always': False,
    'minor': True,
    'talk_page': False,
    'reorder': True,
    'regex_skip_url': '',
}

ARG_PROMPT = {
    '-text': 'What text do you want to add?',
    '-textfile': 'Which text file do you want to append to the page?',
    '-summary': 'What summary do you want to use?',
    '-excepturl': 'What url pattern should we skip?',
}

docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class AddTextBot(AutomaticTWSummaryBot, ExistingPageBot):

    """A bot which adds a text to a page."""

    use_redirects = False
    summary_key = 'add_text-adding'
    update_options = DEFAULT_ARGS

    @property
    def summary_parameters(self):
        """Return a dictionary of all parameters for i18n.

        Line breaks are replaced by dash.
        """
        text = re.sub(r'\r?\n', ' - ', self.opt.text[:200])
        return {'adding': text}

    def setup(self) -> None:
        """Read text to be added from file."""
        if self.opt.textfile:
            with codecs.open(self.opt.textfile, 'r',
                             config.textfile_encoding) as f:
                self.opt.text = f.read()
        else:
            # Translating the \\n into binary \n if given from command line
            self.opt.text = self.opt.text.replace('\\n', '\n')

        if self.opt.talk_page:
            self.generator = pagegenerators.PageWithTalkPageGenerator(
                self.generator, return_talk_only=True)

    def skip_page(self, page):
        """Skip if -exceptUrl matches or page does not exists."""
        if page.exists():
            if self.opt.createonly:
                pywikibot.warning('Skipping because {page} already exists'
                                  .format(page=page))
                return True

            if self.opt.regex_skip_url:
                url = page.full_url()
                result = re.findall(self.opt.regex_skip_url,
                                    page.site.getUrl(url))

                if result:
                    pywikibot.warning(
                        'Skipping {page} because -excepturl matches {result}.'
                        .format(page=page, result=result))
                    return True

        elif page.isTalkPage():
            pywikibot.info(f"{page} doesn't exist, creating it!")
            return False

        elif self.opt.create or self.opt.createonly:
            return False

        return super().skip_page(page)

    def treat_page(self) -> None:
        """Add text to the page."""
        text = self.current_page.text

        if self.opt.up:
            text = self.opt.text + '\n' + text
        elif not self.opt.reorder:
            text += '\n' + self.opt.text
        else:
            text = textlib.add_text(text, self.opt.text,
                                    site=self.current_page.site)

        self.put_current(text, summary=self.opt.summary, minor=self.opt.minor)


def main(*argv: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param argv: Command line arguments
    """
    generator_factory = pagegenerators.GeneratorFactory()

    try:
        options = parse(argv, generator_factory)
    except ValueError as exc:
        pywikibot.bot.suggest_help(additional_text=str(exc))
        return

    generator = generator_factory.getCombinedGenerator()
    if pywikibot.bot.suggest_help(missing_generator=not generator):
        return

    bot = AddTextBot(generator=generator, **options)
    bot.run()


def parse(argv: Sequence[str],
          generator_factory: pagegenerators.GeneratorFactory
          ) -> ARGS_TYPE:
    """
    Parses our arguments and provide a dictionary with their values.

    :param argv: input arguments to be parsed
    :param generator_factory: factory that will determine what pages to
        process
    :return: dictionary with our parsed arguments
    :raise ValueError: if we receive invalid arguments
    """
    args = dict(DEFAULT_ARGS)
    argv = pywikibot.handle_args(argv)
    argv = generator_factory.handle_args(argv)

    for arg in argv:
        option, _, value = arg.partition(':')

        if not value and option in ARG_PROMPT:
            value = pywikibot.input(ARG_PROMPT[option])

        if option in ('-text', '-textfile', '-summary'):
            args[option[1:]] = value
        elif option in ('-up', '-always', '-create', '-createonly'):
            args[option[1:]] = True
        elif option in ('-talk', '-talkpage'):
            args['talk_page'] = True
        elif option == '-noreorder':
            args['reorder'] = False
        elif option == '-excepturl':
            args['regex_skip_url'] = value
        elif option == '-major':
            args['minor'] = False
        else:
            raise ValueError(f"Argument '{option}' is unrecognized")

    if not args['text'] and not args['textfile']:
        raise ValueError("Either the '-text' or '-textfile' is required")

    if args['text'] and args['textfile']:
        raise ValueError("'-text' and '-textfile' cannot both be used")

    return args


if __name__ == '__main__':
    main()
