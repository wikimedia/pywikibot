#!/usr/bin/python
"""
This bot searches for selflinks and allows removing them.

The following parameters are supported:

-always           Unlink always but don't prompt you for each replacement.
                  ATTENTION: Use this with care!

These command line parameters can be used to specify which pages to work on:

&params;
"""
#
# (C) Pywikibot team, 2006-2020
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot.bot import Choice, MultipleSitesBot
from pywikibot.pagegenerators import GeneratorFactory, parameterHelp
from pywikibot.specialbots import BaseUnlinkBot


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': parameterHelp}  # noqa: N816


class _BoldChoice(Choice):

    """A choice to make the title bold."""

    def __init__(self, page, replacer):
        super().__init__('make bold', 'b', replacer)
        self._page = page

    def handle(self):
        return "'''{}'''".format(self._page.title(with_section=False))


class SelflinkBot(MultipleSitesBot, BaseUnlinkBot):

    """Self-link removal bot."""

    summary_key = 'selflink-remove'

    def __init__(self, generator, **kwargs):
        """Initializer."""
        super().__init__(**kwargs)
        self.generator = generator

    def _create_callback(self):
        """Create callback and add a choice to make the link bold."""
        callback = super()._create_callback()
        callback.additional_choices += [_BoldChoice(self.current_page,
                                                    callback)]
        return callback

    def treat_page(self):
        """Unlink all links pointing to the current page."""
        # Inside image maps, don't touch selflinks, as they're used
        # to create tooltip labels. See for example:
        # https://de.wikipedia.org/w/index.php?diff=next&oldid=35721641
        if '<imagemap>' in self.current_page.text:
            pywikibot.output(
                'Skipping page {} because it contains an image map.'
                .format(self.current_page.title(as_link=True)))
            return
        self.unlink(self.current_page)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen_factory = GeneratorFactory()
    bot_args = {}

    for arg in local_args:
        if arg == '-always':
            bot_args['always'] = True
        else:
            gen_factory.handle_arg(arg)

    gen = gen_factory.getCombinedGenerator(preload=True)
    if not gen:
        pywikibot.bot.suggest_help(missing_generator=True)
        return

    bot = SelflinkBot(gen, **bot_args)
    bot.run()


if __name__ == '__main__':
    main()
