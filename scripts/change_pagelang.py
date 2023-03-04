#!/usr/bin/env python3
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

.. note:: This script is a
   :py:obj:`ConfigParserBot <bot.ConfigParserBot>`. All options
   can be set within a settings file which is scripts.ini by default.
"""
#
# (C) Pywikibot team, 2018-2022
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import ConfigParserBot, SingleSiteBot


docuReplacements = {  # noqa: N816
    '&params;': pagegenerators.parameterHelp,
}


class ChangeLangBot(ConfigParserBot, SingleSiteBot):

    """Change page language bot.

    .. versionchanged:: 7.0
       ChangeLangBot is a ConfigParserBot
    """

    update_options = {
        'never': False,
        'setlang': '',
    }

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        assert not (self.opt.always and self.opt.never), \
            'Either "always" or "never" must be set but not both'

    def changelang(self, page) -> None:
        """Set page language.

        :param page: The page to update and save
        :type page: pywikibot.page.BasePage
        """
        parameters = {'action': 'setpagelanguage',
                      'title': page.title(),
                      'lang': self.opt.setlang,
                      'token': self.site.tokens['csrf']}
        r = self.site.simple_request(**parameters)
        r.submit()
        pywikibot.info(f'<<lightpurple>>{page}<<default>>: Setting '
                       f'page language to <<green>>{self.opt.setlang}')

    def treat(self, page) -> None:
        """Treat a page.

        :param page: The page to treat
        :type page: pywikibot.page.BasePage
        """
        # Current content language of the page and site language
        parameters = {'action': 'query',
                      'prop': 'info',
                      'titles': page.title(),
                      'meta': 'siteinfo'}
        r = self.site.simple_request(**parameters)
        langcheck = r.submit()['query']

        currentlang = ''
        for k in langcheck['pages']:
            currentlang = langcheck['pages'][k]['pagelanguage']
        sitelang = langcheck['general']['lang']

        if self.opt.setlang == currentlang:
            pywikibot.info(
                f'<<lightpurple>>{page}<<default>>: This page is already set '
                f'to <<green>>{self.opt.setlang}<<default>>; skipping.')
        elif currentlang == sitelang or self.opt.always:
            self.changelang(page)
        elif self.opt.never:
            pywikibot.info(
                f'<<lightpurple>>{page}<<default>>: This page already has a '
                f'different content language '
                f'<<yellow>>{currentlang}<<default>> set; skipping.')
        else:
            pywikibot.info('\n\n>>> <<lightpurple>>{}<<default>> <<<'
                           .format(page.title()))
            choice = pywikibot.input_choice(
                f'The content language for this page is already set to '
                f'<<yellow>>{currentlang}<<default>>, which is different from '
                f'the default ({sitelang}). Change it to'
                f'<<green>>{self.opt.setlang}<<default>> anyway?',
                [('Always', 'a'), ('Yes', 'y'), ('No', 'n'), ('Never', 'v')],
                default='Y')
            if choice == 'a':
                self.opt.always = True
            elif choice == 'v':
                self.opt.never = True
            if choice in 'ay':
                self.changelang(page)
            else:
                pywikibot.info('Skipping ...\n')


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
