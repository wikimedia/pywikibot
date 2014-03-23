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
# (C) Multichill 2014
# (C) Pywikibot team, 2013
#
# Distributed under the terms of MIT License.
#
__version__ = '$Id$'
#
import json
import pywikibot
from pywikibot import pagegenerators


class coordImportRobot:
    """
    A bot to import coordinates to Wikidata
    """
    def __init__(self, generator):
        """
        Arguments:
            * generator    - A generator that yields Page objects.

        """
        self.generator = pagegenerators.PreloadingGenerator(generator)
        self.site = pywikibot.Site()
        self.repo = pywikibot.Site().data_repository()
        self.cacheSources()

    def getSource(self, lang):
        """
        Get the source for the specified language,
        if possible
        """
        if lang in self.source_values:
            source = pywikibot.Claim(self.repo, 'p143')
            source.setTarget(self.source_values.get(lang))
            return source

    def cacheSources(self):
        """
        Fetches the sources from the onwiki list
        and stores it internally
        """
        page = pywikibot.Page(self.repo, u'Wikidata:List of wikis/python')
        self.source_values = json.loads(page.get())
        self.source_values = self.source_values['wikipedia']
        for source_lang in self.source_values:
            self.source_values[source_lang] = pywikibot.ItemPage(self.repo,
                                                                 self.source_values[source_lang])

    def run(self):
        """
        Starts the robot.
        """
        for page in self.generator:
            pywikibot.output(u'Working on %s' % page.title())
            item = pywikibot.ItemPage.fromPage(page)

            if item.exists():
                pywikibot.output(u'Found %s' % item.title())
                coordinate = page.coordinates(primary_only=True)

                if coordinate:
                    claims = item.get().get('claims')
                    if u'P625' in claims:
                        pywikibot.output(u'Item %s already contains coordinates (P625)' % item.title())
                    else:
                        newclaim = pywikibot.Claim(self.repo, u'P625')
                        newclaim.setTarget(coordinate)
                        pywikibot.output(u'Adding %s, %s to %s' % (coordinate.lat, coordinate.lon, item.title()))
                        item.addClaim(newclaim)

                        source = self.getSource(page.site.language())
                        if source:
                            newclaim.addSource(source, bot=True)


def main():
    gen = pagegenerators.GeneratorFactory()

    for arg in pywikibot.handleArgs():
        if gen.handleArg(arg):
            continue

    generator = gen.getCombinedGenerator()

    coordbot = coordImportRobot(generator)
    coordbot.run()

if __name__ == "__main__":
    main()
