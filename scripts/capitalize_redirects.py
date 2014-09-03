#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
Bot to create capitalized redirects where the first character of the first
word is uppercase and the remaining characters and words are lowercase.

Command-line arguments:

&params;

-always           Don't prompt to make changes, just do them.

-titlecase        creates a titlecased redirect version of a given page
                  where all words of the title start with an uppercase
                  character and the remaining characters are lowercase.

Example: "python capitalize_redirects.py -start:B -always"
"""
#
# (C) Yrithinnd, 2006
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
# Originally derived from:
#    http://en.wikipedia.org/wiki/User:Drinibot/CapitalizationRedirects
#
# Automatically converted from compat branch by compat2core.py script
#
__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n, pagegenerators, Bot

docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class CapitalizeBot(Bot):
    def __init__(self, generator, **kwargs):
        self.availableOptions.update({
            'titlecase': False,
        })

        super(CapitalizeBot, self).__init__(**kwargs)
        self.generator = generator

    def treat(self, page):
        if not page.exists():
            return
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        page_t = page.title()
        self.current_page = page
        if self.getOption('titlecase'):
            page_cap = pywikibot.Page(page.site, page_t.title())
        else:
            page_cap = pywikibot.Page(page.site, page_t.capitalize())
        if page_cap.exists():
            pywikibot.output(u'%s already exists, skipping...\n'
                             % page_cap.title(asLink=True))
        else:
            pywikibot.output(u'%s doesn\'t exist'
                             % page_cap.title(asLink=True))
            if not self.getOption('always'):
                choice = pywikibot.inputChoice(
                    u'Do you want to create a redirect?',
                    ['Yes', 'No', 'All', 'Quit'], ['y', 'N', 'a', 'q'], 'N')
                if choice == 'a':
                    self.options['always'] = True
                elif choice == 'q':
                    self.quit()
            if self.getOption('always') or choice == 'y':
                comment = i18n.twtranslate(
                    page.site,
                    'capitalize_redirects-create-redirect',
                    {'to': page_t})
                page_cap.text = u"#%s %s" % (page.site.redirect(),
                                             page.title(asLink=True,
                                                        textlink=True))
                try:
                    page_cap.save(comment)
                except:
                    pywikibot.output(u"An error occurred, skipping...")


def main():
    options = {}

    local_args = pywikibot.handleArgs()
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-always':
            options['always'] = True
        elif arg == '-titlecase':
            options['titlecase'] = True
        else:
            genFactory.handleArg(arg)

    gen = genFactory.getCombinedGenerator()
    if gen:
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        bot = CapitalizeBot(preloadingGen, **options)
        bot.run()
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    main()
