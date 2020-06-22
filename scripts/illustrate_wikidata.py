#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Bot to add images to Wikidata items.

The image is extracted from the page_props. For this to be available the
PageImages extension (https://www.mediawiki.org/wiki/Extension:PageImages)
needs to be installed

Usage:

    python pwb.py illustrate_wikidata <some generator>

&params;
"""
#
# (C) Pywikibot team, 2013-2019
#
# Distributed under the terms of MIT License.
#
from __future__ import absolute_import, division, unicode_literals

import pywikibot

from pywikibot import pagegenerators, WikidataBot

docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class IllustrateRobot(WikidataBot):

    """A bot to add Wikidata image claims."""

    def __init__(self, generator, wdproperty='P18'):
        """
        Initializer.

        @param generator: A generator that yields Page objects
        @type generator: generator
        @param wdproperty: The property to add. Should be of type commonsMedia
        @type wdproperty: str
        """
        super(IllustrateRobot, self).__init__()
        self.generator = generator
        self.wdproperty = wdproperty
        self.cacheSources()

        claim = pywikibot.Claim(self.repo, self.wdproperty)
        if claim.type != 'commonsMedia':
            raise ValueError('{} is of type {}, should be commonsMedia'
                             .format(self.wdproperty, claim.type))

    def treat_page_and_item(self, page, item):
        """Treat a page / item."""
        pywikibot.output('Found ' + item.title())
        imagename = page.properties().get('page_image_free')

        if not imagename:
            return

        claims = item.get().get('claims')
        if self.wdproperty in claims:
            pywikibot.output('Item {} already contains image ({})'
                             .format(item.title(), self.wdproperty))
            return

        newclaim = pywikibot.Claim(self.repo, self.wdproperty)
        commonssite = pywikibot.Site('commons', 'commons')
        imagelink = pywikibot.Link(imagename, source=commonssite,
                                   default_namespace=6)
        image = pywikibot.FilePage(imagelink)
        if image.isRedirectPage():
            image = pywikibot.FilePage(image.getRedirectTarget())

        if not image.exists():
            pywikibot.output("{} doesn't exist so I can't link to it"
                             .format(image.title(as_link=True)))
            return

        newclaim.setTarget(image)
        # A generator might yield pages from multiple sites
        self.user_add_claim(item, newclaim, page.site)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    generator_factory = pagegenerators.GeneratorFactory()

    wdproperty = 'P18'

    for arg in local_args:
        if arg.startswith('-property'):
            if len(arg) == 9:
                wdproperty = pywikibot.input(
                    'Please enter the property you want to add:')
            else:
                wdproperty = arg[10:]
        else:
            generator_factory.handleArg(arg)

    generator = generator_factory.getCombinedGenerator(preload=True)
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return

    bot = IllustrateRobot(generator, wdproperty)
    bot.run()


if __name__ == '__main__':
    main()
