#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Program to re-categorize images at commons.

The program uses read the current categories, put the categories through
some filters and adds the result.

The following command line parameters are supported:

-onlyuncat      Only work on uncategorized images. Will prevent the bot from
                working on an image multiple times.
"""
#
# (C) Multichill, 2008-2011
# (C) Pywikibot team, 2008-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import socket
import xml.etree.ElementTree

import pywikibot

from pywikibot import pagegenerators, textlib
from pywikibot.comms.http import fetch
from pywikibot.tools import deprecated, PY2

if not PY2:
    from urllib.parse import urlencode
else:
    from urllib import urlencode


category_blacklist = []
countries = []


def initLists():
    """Get the list of countries & the blacklist from Commons."""
    global category_blacklist
    global countries

    blacklistPage = pywikibot.Page(pywikibot.Site('commons', 'commons'),
                                   'User:Multichill/Category_blacklist')
    for cat in blacklistPage.linkedPages():
        category_blacklist.append(cat.title(with_ns=False))

    countryPage = pywikibot.Page(pywikibot.Site('commons', 'commons'),
                                 'User:Multichill/Countries')
    for country in countryPage.linkedPages():
        countries.append(country.title(with_ns=False))
    return


def categorizeImages(generator, onlyUncat):
    """Loop over all images in generator and try to categorize them.

    Get category suggestions from CommonSense.

    """
    for page in generator:
        if not page.exists() or page.namespace() != 6 or page.isRedirectPage():
            continue

        imagepage = pywikibot.FilePage(page.site, page.title())
        pywikibot.output('Working on ' + imagepage.title())

        if (onlyUncat and not pywikibot.Page(
                imagepage.site, 'Template:Uncategorized')
                in imagepage.templates()):
            pywikibot.output('No Uncategorized template found')
            continue

        currentCats = getCurrentCats(imagepage)
        newcats = applyAllFilters(currentCats)

        if newcats and set(currentCats) != set(newcats):
            for cat in newcats:
                pywikibot.output(' Found new cat: ' + cat)
            saveImagePage(imagepage, newcats)


def getCurrentCats(imagepage):
    """Get the categories currently on the image."""
    result = []
    for cat in imagepage.categories():
        result.append(cat.title(with_ns=False))
    return list(set(result))


def getOpenStreetMapCats(latitude, longitude):
    """Get a list of location categories based on the OSM nomatim tool."""
    result = []
    location_list = getOpenStreetMap(latitude, longitude)
    for i, location in enumerate(location_list):
        pywikibot.log('Working on {!r}'.format(location))
        if i <= len(location_list) - 3:
            category = getCategoryByName(name=location,
                                         parent=location_list[i + 1],
                                         grandparent=location_list[i + 2])
        elif i == len(location_list) - 2:
            category = getCategoryByName(name=location,
                                         parent=location_list[i + 1])
        else:
            category = getCategoryByName(name=location_list[i])
        if category and not category == '':
            result.append(category)
    return result


def getOpenStreetMap(latitude, longitude):
    """
    Get the result from https://nominatim.openstreetmap.org/reverse .

    @rtype: list of tuples
    """
    result = []
    gotInfo = False
    parameters = urlencode({'lat': latitude, 'lon': longitude,
                            'accept-language': 'en'})
    while not gotInfo:
        try:
            page = fetch(
                'https://nominatim.openstreetmap.org/reverse?format=xml&{}'
                .format(parameters))
            et = xml.etree.ElementTree.fromstring(page.text)
            gotInfo = True
        except IOError:
            pywikibot.output("Got an IOError, let's try again")
            pywikibot.sleep(30)
        except socket.timeout:
            pywikibot.output("Got a timeout, let's try again")
            pywikibot.sleep(30)
    validParts = ['hamlet', 'village', 'city', 'county', 'country']
    invalidParts = ['path', 'road', 'suburb', 'state', 'country_code']
    addressparts = et.find('addressparts')

    for addresspart in addressparts.getchildren():
        if addresspart.tag in validParts:
            result.append(addresspart.text)
        elif addresspart.tag in invalidParts:
            pywikibot.output('Dropping {}, {}'
                             .format(addresspart.tag, addresspart.text))
        else:
            pywikibot.warning('{}, {} is not in addressparts lists'
                              .format(addresspart.tag, addresspart.text))
    return result


def getCategoryByName(name, parent='', grandparent=''):
    """Get category by name."""
    if not parent == '':
        workname = name.strip() + ',_' + parent.strip()
        workcat = pywikibot.Category(pywikibot.Site('commons', 'commons'),
                                     workname)
        if workcat.exists():
            return workname
    if not grandparent == '':
        workname = name.strip() + ',_' + grandparent.strip()
        workcat = pywikibot.Category(pywikibot.Site('commons', 'commons'),
                                     workname)
        if workcat.exists():
            return workname
    workname = name.strip()
    workcat = pywikibot.Category(pywikibot.Site('commons', 'commons'),
                                 workname)
    if workcat.exists():
        return workname
    return ''


def applyAllFilters(categories):
    """Apply all filters on categories."""
    result = filterDisambiguation(categories)
    result = followRedirects(result)
    result = filterBlacklist(result)
    result = filterCountries(result)
    return result


def filterBlacklist(categories):
    """Filter out categories which are on the blacklist."""
    result = []
    for cat in categories:
        cat = cat.replace('_', ' ')
        if not (cat in category_blacklist):
            result.append(cat)
    return list(set(result))


def filterDisambiguation(categories):
    """Filter out disambiguation categories."""
    result = []
    for cat in categories:
        if (not pywikibot.Page(pywikibot.Site('commons', 'commons'),
                               cat, ns=14).isDisambig()):
            result.append(cat)
    return result


def followRedirects(categories):
    """If a category is a redirect, replace the category with the target."""
    result = []
    for cat in categories:
        categoryPage = pywikibot.Page(pywikibot.Site('commons', 'commons'),
                                      cat, ns=14)
        if categoryPage.isCategoryRedirect():
            result.append(
                categoryPage.getCategoryRedirectTarget().title(
                    with_ns=False))
        else:
            result.append(cat)
    return result


def filterCountries(categories):
    """Try to filter out ...by country categories.

    First make a list of any ...by country categories and try to find some
    countries. If a by country category has a subcategoy containing one of the
    countries found, add it. The ...by country categories remain in the set and
    should be filtered out by filterParents.

    """
    result = categories
    listByCountry = []
    listCountries = []
    for cat in categories:
        if cat.endswith('by country'):
            listByCountry.append(cat)

        # If cat contains 'by country' add it to the list
        # If cat contains the name of a country add it to the list
        else:
            for country in countries:
                if country in cat:
                    listCountries.append(country)
    if len(listByCountry) > 0:
        for bc in listByCountry:
            category = pywikibot.Category(
                pywikibot.Site('commons', 'commons'), 'Category:' + bc)
            for subcategory in category.subcategories():
                for country in listCountries:
                    if subcategory.title(with_ns=False).endswith(country):
                        result.append(subcategory.title(with_ns=False))
    return list(set(result))


@deprecated(since='20180120')
def filterParents(categories):
    """
    Remove all parent categories from the set to prevent overcategorization.

    DEPRECATED: Toolserver script isn't available anymore (T78462).
    This method is kept for compatibility and may be restored sometime by a new
    implementation.
    """
    return categories


def saveImagePage(imagepage, newcats):
    """Remove the old categories and add the new categories to the image."""
    newtext = textlib.removeCategoryLinks(imagepage.text, imagepage.site)
    newtext += '\n'

    for category in newcats:
        newtext = newtext + '[[Category:' + category + ']]\n'

    comment = 'Filtering categories'

    pywikibot.showDiff(imagepage.text, newtext)
    imagepage.text = newtext
    imagepage.save(comment)
    return


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    onlyUncat = False

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-onlyuncat':
            onlyUncat = True
        else:
            genFactory.handleArg(arg)

    generator = genFactory.getCombinedGenerator()
    if not generator:
        site = pywikibot.Site('commons', 'commons')
        generator = pagegenerators.CategorizedPageGenerator(
            pywikibot.Category(site, 'Category:Media needing categories'),
            recurse=True)

    initLists()
    categorizeImages(generator, onlyUncat)
    pywikibot.output('All done')


if __name__ == '__main__':
    main()
