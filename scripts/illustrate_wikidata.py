#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Bot to add images to Wikidata items. The image is extracted from the page_props.

For this to be available the PageImages extension
(https://www.mediawiki.org/wiki/Extension:PageImages) needs to be installed

Usage:

python illustrate_wikidata.py <some generator>

&params;
"""
#
# (C) Multichill, 2014
# (C) Pywikibot team, 2013-2014
#
# Distributed under the terms of MIT License.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import pywikibot

from pywikibot import pagegenerators, WikidataBot

docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}


class IllustrateRobot(WikidataBot):

    """A bot to add Wikidata image claims."""

    def __init__(self, generator, wdproperty=u'P18'):
        """
        Constructor.

        Arguments:
            * generator     - A generator that yields Page objects.
            * wdproperty    - The property to add. Should be of type commonsMedia

        """
        super(IllustrateRobot, self).__init__()
        self.generator = pagegenerators.PreloadingGenerator(generator)
        self.wdproperty = wdproperty
        self.cacheSources()

        claim = pywikibot.Claim(self.repo, self.wdproperty)
        if claim.type != 'commonsMedia':
            raise ValueError(u'%s is of type %s, should be commonsMedia'
                             % (self.wdproperty, claim.type))

    def treat(self, page, item):
        """Treat a page / item."""
        self.current_page = page

        pywikibot.output(u'Found %s' % item.title())
        imagename = page.properties().get('page_image')

        if not imagename:
            return

        claims = item.get().get('claims')
        if self.wdproperty in claims:
            pywikibot.output(u'Item %s already contains image (%s)' % (item.title(), self.wdproperty))
            return

        newclaim = pywikibot.Claim(self.repo, self.wdproperty)
        commonssite = pywikibot.Site("commons", "commons")
        imagelink = pywikibot.Link(imagename, source=commonssite, defaultNamespace=6)
        image = pywikibot.FilePage(imagelink)
        if image.isRedirectPage():
            image = pywikibot.FilePage(image.getRedirectTarget())

        if not image.exists():
            pywikibot.output('[[%s]] doesn\'t exist so I can\'t link to it' % (image.title(),))
            return

        newclaim.setTarget(image)
        pywikibot.output('Adding %s --> %s' % (newclaim.getID(), newclaim.getTarget()))
        item.addClaim(newclaim)

        # A generator might yield pages from multiple sites
        source = self.getSource(page.site)
        if source:
            newclaim.addSource(source, bot=True)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    generator_factory = pagegenerators.GeneratorFactory()

    wdproperty = u'P18'

    for arg in local_args:
        if arg.startswith('-property'):
            if len(arg) == 9:
                wdproperty = pywikibot.input(
                    u'Please enter the property you want to add:')
            else:
                wdproperty = arg[10:]
        else:
            generator_factory.handleArg(arg)

    generator = generator_factory.getCombinedGenerator()
    if not generator:
        pywikibot.output('I need a generator with pages to work on')
        return

    bot = IllustrateRobot(generator, wdproperty)
    bot.run()

if __name__ == "__main__":
    main()
