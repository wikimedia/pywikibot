#!/usr/bin/python
"""
This script changes the content language of pages.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-setlang          What language the pages should be set to

-always           If a language is already set for a page, always change it
                  to the one set in -setlang.

-never            If a language is already set for a page, never change it to
                  the one set in -setlang (keep the current language).
"""
#
# (C) Pywikibot team, 2018-2021
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import SingleSiteBot
from pywikibot.tools.formatter import color_format


docuReplacements = {  # noqa: N816
    '&params;': pagegenerators.parameterHelp,
}


class ChangeLangBot(SingleSiteBot):

    """Change page language bot."""

    update_options = {
        'never': False,
        'setlang': '',
    }

    def __init__(self, **kwargs):
        """Initializer."""
        super().__init__(**kwargs)
        assert not (self.opt.always and self.opt.never), \
            'Either "always" or "never" must be set but not both'

    def changelang(self, page):
        """Set page language.

        :param page: The page to update and save
        :type page: pywikibot.page.BasePage
        """
        token = self.site.get_tokens(['csrf']).get('csrf')
        parameters = {'action': 'setpagelanguage',
                      'title': page.title(),
                      'lang': self.opt.setlang,
                      'token': token}
        r = self.site._simple_request(**parameters)
        r.submit()
        pywikibot.output(color_format(
            '{lightpurple}{0}{default}: Setting '
            'page language to {green}{1}{default}',
            page.title(as_link=True), self.opt.setlang))

    def treat(self, page):
        """Treat a page.

        :param page: The page to treat
        :type page: pywikibot.page.BasePage
        """
        # Current content language of the page and site language
        parameters = {'action': 'query',
                      'prop': 'info',
                      'titles': page.title(),
                      'meta': 'siteinfo'}
        r = self.site._simple_request(**parameters)
        langcheck = r.submit()['query']

        currentlang = ''
        for k in langcheck['pages']:
            currentlang = langcheck['pages'][k]['pagelanguage']
        sitelang = langcheck['general']['lang']

        if self.opt.setlang == currentlang:
            pywikibot.output(color_format(
                '{lightpurple}{0}{default}: This page is already set to '
                '{green}{1}{default}; skipping.',
                page.title(as_link=True), self.opt.setlang))
        elif currentlang == sitelang or self.opt.always:
            self.changelang(page)
        elif self.opt.never:
            pywikibot.output(color_format(
                '{lightpurple}{0}{default}: This page already has a '
                'different content language {yellow}{1}{default} set; '
                'skipping.', page.title(as_link=True), currentlang))
        else:
            pywikibot.output(color_format(
                '\n\n>>> {lightpurple}{0}{default} <<<', page.title()))
            choice = pywikibot.input_choice(color_format(
                'The content language for this page is already set to '
                '{yellow}{0}{default}, which is different from the '
                'default ({1}). Change it to {green}{2}{default} anyway?',
                currentlang, sitelang, self.opt.setlang),
                [('Always', 'a'), ('Yes', 'y'), ('No', 'n'),
                 ('Never', 'v')], default='Y')
            if choice == 'a':
                self.opt.always = True
            elif choice == 'v':
                self.opt.never = True
            if choice in 'ay':
                self.changelang(page)
            else:
                pywikibot.output('Skipping ...\n')


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        opt, _, value = arg.partition(':')
        if opt == '-setlang':
            options[opt[1:]] = value
        elif arg in ('-always', '-never'):
            options[opt[1:]] = True
        else:
            gen_factory.handle_arg(arg)

    if not options.get('setlang'):
        pywikibot.error('No -setlang parameter given.')
        return

    site = pywikibot.Site()
    specialpages = site.siteinfo['specialpagealiases']
    specialpagelist = {item['realname'] for item in specialpages}
    allowedlanguages = site._paraminfo.parameter(module='setpagelanguage',
                                                 param_name='lang')['type']
    # Check if the special page PageLanguage is enabled on the wiki
    # If it is not, page languages can't be set, and there's no point in
    # running the bot any further
    if 'PageLanguage' not in specialpagelist:
        pywikibot.error("This site doesn't allow changing the "
                        'content languages of pages; aborting.')
        return
    # Check if the account has the right to change page content language
    # If it doesn't, there's no point in running the bot any further.
    if 'pagelang' not in site.userinfo['rights']:
        pywikibot.error("Your account doesn't have sufficient "
                        'rights to change the content language of pages; '
                        "aborting.\n\nYou must have the 'pagelang' right "
                        'in order to use this script.')
        return

    # Check if the language you are trying to set is allowed.
    if options['setlang'] not in allowedlanguages:
        pywikibot.error('"{}" is not in the list of allowed language codes; '
                        'aborting.\n\n The following is the list of allowed '
                        'languages. Using "default" will unset any set '
                        'language and use the default language for the wiki '
                        'instead.\n\n'.format(options['setlang'])
                        + ', '.join(allowedlanguages))
        return

    gen = gen_factory.getCombinedGenerator(preload=True)
    if gen:
        bot = ChangeLangBot(generator=gen, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
