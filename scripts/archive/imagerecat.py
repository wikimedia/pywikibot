#!/usr/bin/python
"""
Program to re-categorize images at commons.

The program uses read the current categories, put the categories through
some filters and adds the result.

The following command line parameters are supported:

-onlyuncat      Only work on uncategorized images. Will prevent the bot from
                working on an image multiple times.
"""
#
# (C) Pywikibot team, 2008-2020
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import pagegenerators, textlib


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
    countries found, add it. The ...by country categories remain in the set.
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

    country_tuple = tuple(listCountries)
    for bc in listByCountry:
        category = pywikibot.Category(
            pywikibot.Site('commons', 'commons'), 'Category:' + bc)
        for subcategory in category.subcategories():
            if subcategory.title(with_ns=False).endswith(country_tuple):
                result.append(subcategory.title(with_ns=False))
    return list(set(result))


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


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    onlyUncat = False

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    site = pywikibot.Site('commons', 'commons')
    genFactory = pagegenerators.GeneratorFactory(site=site)

    for arg in local_args:
        if arg == '-onlyuncat':
            onlyUncat = True
        else:
            genFactory.handle_arg(arg)

    generator = genFactory.getCombinedGenerator()
    if not generator:
        generator = pagegenerators.CategorizedPageGenerator(
            pywikibot.Category(site, 'Media needing categories'), recurse=True)

    initLists()
    categorizeImages(generator, onlyUncat)
    pywikibot.output('All done')


if __name__ == '__main__':
    main()
