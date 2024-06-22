#!/usr/bin/env python3
"""Bot to add images to Wikidata items.

The image is extracted from the page_props. For this to be available the
PageImages extension
(https://www.mediawiki.org/wiki/Extension:PageImages) needs to be
installed.

The following options are provided:

-always    Don't prompt to make changes, just do them.
-property  The property to add. Should be of type commonsMedia.

Usage:

    python pwb.py illustrate_wikidata <some generator>

&params;
"""
#
# (C) Pywikibot team, 2013-2024
#
# Distributed under the terms of MIT license.
#
from __future__ import annotations

import pywikibot
from pywikibot import WikidataBot, pagegenerators


docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class IllustrateRobot(WikidataBot):

    """A bot to add Wikidata image claims."""

    update_options = {
        'property': 'P18',
    }

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        self.cacheSources()

        claim = pywikibot.Claim(self.repo, self.opt.property)
        if claim.type != 'commonsMedia':
            raise ValueError(f'{self.opt.property} is of type {claim.type},'
                             ' should be commonsMedia')

    def treat_page_and_item(self, page, item) -> None:
        """Treat a page / item."""
        pywikibot.info('Found ' + item.title())
        imagename = page.properties().get('page_image_free')

        if not imagename:
            return

        claims = item.get().get('claims')
        if self.opt.property in claims:
            pywikibot.info(f'Item {item.title()} already contains image '
                           f'({self.opt.property})')
            return

        newclaim = pywikibot.Claim(self.repo, self.opt.property)
        commonssite = pywikibot.Site('commons')
        imagelink = pywikibot.Link(imagename, source=commonssite,
                                   default_namespace=6)
        image = pywikibot.FilePage(imagelink)
        if image.isRedirectPage():
            image = pywikibot.FilePage(image.getRedirectTarget())

        if not image.exists():
            pywikibot.info(f"{image} doesn't exist so I can't link to it")
            return

        newclaim.setTarget(image)
        # A generator might yield pages from multiple sites
        self.user_add_claim(item, newclaim, page.site)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    generator_factory = pagegenerators.GeneratorFactory()

    options = {}

    for arg in local_args:
        opt, _, value = arg.partition(':')
        if opt == '-property':
            options['property'] = value or pywikibot.input(
                'Please enter the property you want to add:')
        elif opt == '-always':
            options[opt[1:]] = True
        else:
            generator_factory.handle_arg(arg)

    options['generator'] = generator_factory.getCombinedGenerator(preload=True)
    bot = IllustrateRobot(**options)
    bot.run()


if __name__ == '__main__':
    main()
