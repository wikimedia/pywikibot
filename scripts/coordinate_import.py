#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
Coordinate importing script.

Usage:

    python pwb.py coordinate_import -lang:en -family:wikipedia \
        -cat:Category:Coordinates_not_on_Wikidata

This will work on all pages in the category "coordinates not on Wikidata" and
will import the coordinates on these pages to Wikidata.

The data from the "GeoData" extension
(https://www.mediawiki.org/wiki/Extension:GeoData)
is used so that extension has to be setup properly. You can look at the
[[Special:Nearby]] page on your local Wiki to see if it's populated.

You can use any typical pagegenerator to provide with a list of pages:

    python pwb.py coordinate_import -lang:it -family:wikipedia \
        -namespace:0 -transcludes:Infobox_stazione_ferroviaria

The following command line parameters are supported:

-create           Create items for pages without one.

&params;
"""
#
# (C) Multichill, 2014
# (C) Pywikibot team, 2013-2017
#
# Distributed under the terms of MIT License.
#
from __future__ import absolute_import, unicode_literals

import pywikibot
from pywikibot import pagegenerators, WikidataBot
from pywikibot.exceptions import CoordinateGlobeUnknownException

docuReplacements = {'&params;': pagegenerators.parameterHelp}


class CoordImportRobot(WikidataBot):

    """A bot to import coordinates to Wikidata."""

    def __init__(self, generator, **kwargs):
        """
        Constructor.

        @param generator: A generator that yields Page objects.
        """
        self.availableOptions['create'] = False
        super(CoordImportRobot, self).__init__(**kwargs)
        self.generator = generator
        self.cacheSources()
        self.prop = 'P625'
        self.create_missing_item = self.getOption('create')

    def has_coord_qualifier(self, claims):
        """
        Check if self.prop is used as property for a qualifier.

        @param claims: the Wikibase claims to check in
        @type claims: dict
        @return: the first property for which self.prop
            is used as qualifier, or None if any
        @return: unicode or None

        """
        for prop in claims:
            for claim in claims[prop]:
                if self.prop in claim.qualifiers:
                    return prop

    def treat_page_and_item(self, page, item):
        """Treat page/item."""
        coordinate = page.coordinates(primary_only=True)

        if not coordinate:
            return

        claims = item.get().get('claims')
        if self.prop in claims:
            pywikibot.output(u'Item %s already contains coordinates (%s)'
                             % (item.title(), self.prop))
            return

        prop = self.has_coord_qualifier(claims)
        if prop:
            pywikibot.output(u'Item %s already contains coordinates'
                             u' (%s) as qualifier for %s'
                             % (item.title(), self.prop, prop))
            return

        newclaim = pywikibot.Claim(self.repo, self.prop)
        newclaim.setTarget(coordinate)
        pywikibot.output(u'Adding %s, %s to %s' % (coordinate.lat,
                                                   coordinate.lon,
                                                   item.title()))
        try:
            item.addClaim(newclaim)

            source = self.getSource(page.site)
            if source:
                newclaim.addSource(source, bot=True)
        except CoordinateGlobeUnknownException as e:
            pywikibot.output(u'Skipping unsupported globe: %s' % e.args)


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

    create_new = False
    for arg in local_args:
        if generator_factory.handleArg(arg):
            continue
        if arg == '-create':
            create_new = True

    generator = generator_factory.getCombinedGenerator(preload=True)

    if generator:
        coordbot = CoordImportRobot(generator, create=create_new)
        coordbot.run()
        return True
    else:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False


if __name__ == "__main__":
    main()
