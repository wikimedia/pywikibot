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

You can also run over a set of items on the repo without coordinates and
try to import them from any connected page. To do this, you have to
explicitly provide the repo as the site using -lang and -family arguments.
Example:

    python pwb.py coordinate_import -lang:wikidata -family:wikidata \
        -namespace:0 -querypage:Deadendpages


The following command line parameters are supported:

-create           Create items for pages without one.

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
from pywikibot.exceptions import CoordinateGlobeUnknownException

docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class CoordImportRobot(WikidataBot):

    """A bot to import coordinates to Wikidata."""

    use_from_page = None

    def __init__(self, generator, **kwargs):
        """
        Initializer.

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
        return None

    def item_has_coordinates(self, item):
        """
        Check if the item has coordinates.

        @return: whether the item has coordinates
        @rtype: bool
        """
        claims = item.get().get('claims')
        if self.prop in claims:
            pywikibot.output('Item {} already contains coordinates ({})'
                             .format(item.title(), self.prop))
            return True

        prop = self.has_coord_qualifier(claims)
        if prop:
            pywikibot.output('Item {} already contains coordinates'
                             ' ({}) as qualifier for {}'
                             .format(item.title(), self.prop, prop))
            return True
        return False

    def treat_page_and_item(self, page, item):
        """Treat page/item."""
        if self.item_has_coordinates(item):
            return
        if page is None:
            # running over items, search in linked pages
            for page in item.iterlinks():
                if page.site.has_extension('GeoData'):
                    if self.try_import_coordinates_from_page(page, item):
                        break
            return

        self.try_import_coordinates_from_page(page, item)

    def try_import_coordinates_from_page(self, page, item):
        """
        Try import coordinate from the given page to the given item.

        @return: whether any coordinates were found and the import
            was successful
        @rtype: bool
        """
        coordinate = page.coordinates(primary_only=True)
        if not coordinate:
            return False

        newclaim = pywikibot.Claim(self.repo, self.prop)
        newclaim.setTarget(coordinate)
        source = self.getSource(page.site)
        if source:
            newclaim.addSource(source)
        pywikibot.output('Adding {}, {} to {}'.format(
            coordinate.lat, coordinate.lon, item.title()))
        # todo: handle exceptions using self.user_add_claim
        try:
            item.addClaim(newclaim)
        except CoordinateGlobeUnknownException as e:
            pywikibot.output('Skipping unsupported globe: {}'.format(e.args))
            return False
        else:
            return True


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

    create_new = False
    for arg in local_args:
        if generator_factory.handleArg(arg):
            continue
        if arg == '-create':
            create_new = True

    # xxx: this preloading preloads neither coordinates nor Wikibase items
    # but preloads wikitext which we don't need
    generator = generator_factory.getCombinedGenerator(preload=True)

    if generator:
        coordbot = CoordImportRobot(generator, create=create_new)
        coordbot.run()
        return True
    else:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False


if __name__ == '__main__':
    main()
