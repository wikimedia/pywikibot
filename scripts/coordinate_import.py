#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Usage:

python coordinate_import.py -lang:en -family:wikipedia -cat:Category:Coordinates_not_on_Wikidata

This will work on all pages in the category "coordinates not on Wikidata" and will import the coordinates on these pages to Wikidata.

The data from the "GeoData" extension (https://www.mediawiki.org/wiki/Extension:GeoData) is used so that extension has to be setup properly.
You can look at the [[Special:Nearby]] page on your local Wiki to see if it's populated.

You can use any typical pagegenerator to provide with a list of pages:

python coordinate_import.py -lang:it -family:wikipedia -transcludes:Infobox_stazione_ferroviaria -namespace:0

&params;
"""
#
# (C) Multichill, 2014
# (C) Pywikibot team, 2013-2014
#
# Distributed under the terms of MIT License.
#
__version__ = '$Id$'
#
import pywikibot
from pywikibot import pagegenerators, WikidataBot
from pywikibot.exceptions import CoordinateGlobeUnknownException


class CoordImportRobot(WikidataBot):
    """
    A bot to import coordinates to Wikidata
    """
    def __init__(self, generator):
        """
        Arguments:
            * generator    - A generator that yields Page objects.

        """
        self.generator = pagegenerators.PreloadingGenerator(generator)
        self.repo = pywikibot.Site().data_repository()
        self.cacheSources()
        self.prop = 'P625'

    def has_coord_qualifier(self, claims):
        """
        Check if self.prop is used as property for a qualifier.

        @param claims: the Wikibase claims to check in
        @type  claims: dict
        @return: the first property for which self.prop
            is used as qualifier, or None if any
        @returntype: unicode or None

        """
        for prop in claims:
            for claim in claims[prop]:
                if self.prop in claim.qualifiers:
                    return prop

    def run(self):
        """Start the robot."""
        for page in self.generator:
            pywikibot.output(u'Working on %s' % page.title())
            item = pywikibot.ItemPage.fromPage(page)

            if item.exists():
                pywikibot.output(u'Found %s' % item.title())
                coordinate = page.coordinates(primary_only=True)

                if coordinate:
                    claims = item.get().get('claims')
                    if self.prop in claims:
                        pywikibot.output(u'Item %s already contains coordinates (%s)'
                                         % (item.title(), self.prop))
                    else:
                        prop = self.has_coord_qualifier(claims)
                        if prop:
                            pywikibot.output(u'Item %s already contains coordinates'
                                             u' (%s) as qualifier for %s'
                                             % (item.title(), self.prop, prop))
                        else:
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


def main():
    # Process global args and prepare generator args parser
    local_args = pywikibot.handleArgs()
    gen = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if gen.handleArg(arg):
            continue

    generator = gen.getCombinedGenerator()

    if generator:
        coordbot = CoordImportRobot(generator)
        coordbot.run()
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    main()
