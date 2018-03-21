#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Program to (re)categorize images at commons.

The program uses commonshelper for category suggestions.
It takes the suggestions and the current categories. Put the categories through
some filters and adds the result.

The following command line parameters are supported:

-onlyfilter     Don't use Commonsense to get categories, just filter the
                current categories

-onlyuncat      Only work on uncategorized images. Will prevent the bot from
                working on an image multiple times.

-hint           Give Commonsense a hint.
                For example -hint:li.wikipedia.org

-onlyhint       Give Commonsense a hint. And only work on this hint.
                Syntax is the same as -hint. Some special hints are possible:
                _20 : Work on the top 20 wikipedia's
                _80 : Work on the top 80 wikipedia's
                wps : Work on all wikipedia's

"""
#
# (C) Multichill, 2008-2011
# (C) Pywikibot team, 2008-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import re
import socket
import sys
import time
import xml.etree.ElementTree

import pywikibot

from pywikibot import pagegenerators, textlib
from pywikibot.comms.http import fetch
from pywikibot.tools import deprecated

if sys.version_info[0] > 2:
    from urllib.parse import urlencode
else:
    from urllib import urlencode


category_blacklist = []
countries = []

search_wikis = u'_20'
hint_wiki = u''


def initLists():
    """Get the list of countries & the blacklist from Commons."""
    global category_blacklist
    global countries

    blacklistPage = pywikibot.Page(pywikibot.Site(u'commons', u'commons'),
                                   u'User:Multichill/Category_blacklist')
    for cat in blacklistPage.linkedPages():
        category_blacklist.append(cat.title(withNamespace=False))

    countryPage = pywikibot.Page(pywikibot.Site(u'commons', u'commons'),
                                 u'User:Multichill/Countries')
    for country in countryPage.linkedPages():
        countries.append(country.title(withNamespace=False))
    return


def categorizeImages(generator, onlyFilter, onlyUncat):
    """Loop over all images in generator and try to categorize them.

    Get category suggestions from CommonSense.

    """
    for page in generator:
        if page.exists() and (page.namespace() == 6) and \
           (not page.isRedirectPage()):
            imagepage = pywikibot.FilePage(page.site, page.title())
            pywikibot.output(u'Working on ' + imagepage.title())

            if onlyUncat and not(u'Uncategorized' in imagepage.templates()):
                pywikibot.output(u'No Uncategorized template found')
            else:
                currentCats = getCurrentCats(imagepage)
                if onlyFilter:
                    commonshelperCats = []
                    usage = []
                    galleries = []
                else:
                    (commonshelperCats, usage, galleries) = getCommonshelperCats(imagepage)
                newcats = applyAllFilters(commonshelperCats + currentCats)

                if len(newcats) > 0 and not(set(currentCats) == set(newcats)):
                    for cat in newcats:
                        pywikibot.output(u' Found new cat: ' + cat)
                    saveImagePage(imagepage, newcats, usage, galleries,
                                  onlyFilter)


def getCurrentCats(imagepage):
    """Get the categories currently on the image."""
    result = []
    for cat in imagepage.categories():
        result.append(cat.title(withNamespace=False))
    return list(set(result))


def getCommonshelperCats(imagepage):
    """Get category suggestions from CommonSense.

    @rtype: list of unicode

    """
    commonshelperCats = []
    usage = []
    galleries = []

    global search_wikis
    global hint_wiki
    site = imagepage.site
    lang = site.code
    family = site.family.name
    if lang == u'commons' and family == u'commons':
        parameters = urlencode(
            {'i': imagepage.title(withNamespace=False).encode('utf-8'),
             'r': 'on',
             'go-clean': 'Find+Categories',
             'p': search_wikis,
             'cl': hint_wiki})
    elif family == u'wikipedia':
        parameters = urlencode(
            {'i': imagepage.title(withNamespace=False).encode('utf-8'),
             'r': 'on',
             'go-move': 'Find+Categories',
             'p': search_wikis,
             'cl': hint_wiki,
             'w': lang})
    else:
        # Cant handle other sites atm
        return [], [], []

    commonsenseRe = re.compile(
        r'^#COMMONSENSE(.*)#USAGE(\s)+\((?P<usagenum>(\d)+)\)\s(?P<usage>(.*))\s'
        r'#KEYWORDS(\s)+\((?P<keywords>(\d)+)\)(.*)'
        r'#CATEGORIES(\s)+\((?P<catnum>(\d)+)\)\s(?P<cats>(.*))\s'
        r'#GALLERIES(\s)+\((?P<galnum>(\d)+)\)\s(?P<gals>(.*))\s(.*)#EOF$',
        re.MULTILINE + re.DOTALL)

    gotInfo = False
    matches = None
    maxtries = 10
    tries = 0
    while not gotInfo:
        try:
            if tries < maxtries:
                tries += 1
                commonsHelperPage = fetch(
                    "https://toolserver.org/~daniel/WikiSense/CommonSense.php?%s" % parameters)
                matches = commonsenseRe.search(
                    commonsHelperPage.text)
                gotInfo = True
            else:
                break
        except IOError:
            pywikibot.output(u'Got an IOError, let\'s try again')
        except socket.timeout:
            pywikibot.output(u'Got a timeout, let\'s try again')

    if matches and gotInfo:
        if matches.group('usagenum') > 0:
            used = matches.group('usage').splitlines()
            for use in used:
                usage = usage + getUsage(use)
        if matches.group('catnum') > 0:
            cats = matches.group('cats').splitlines()
            for cat in cats:
                commonshelperCats.append(cat.replace('_', ' '))
                pywikibot.output(u'category : ' + cat)
        if matches.group('galnum') > 0:
            gals = matches.group('gals').splitlines()
            for gal in gals:
                galleries.append(gal.replace('_', ' '))
                pywikibot.output(u'gallery : ' + gal)
    commonshelperCats = list(set(commonshelperCats))
    galleries = list(set(galleries))
    for (lang, project, article) in usage:
        pywikibot.output(lang + project + article)
    return commonshelperCats, usage, galleries


def getOpenStreetMapCats(latitude, longitude):
    """Get a list of location categories based on the OSM nomatim tool."""
    result = []
    locationList = getOpenStreetMap(latitude, longitude)
    for i in range(0, len(locationList)):
        pywikibot.log(u'Working on %r' % locationList[i])
        if i <= len(locationList) - 3:
            category = getCategoryByName(name=locationList[i],
                                         parent=locationList[i + 1],
                                         grandparent=locationList[i + 2])
        elif i == len(locationList) - 2:
            category = getCategoryByName(name=locationList[i],
                                         parent=locationList[i + 1])
        else:
            category = getCategoryByName(name=locationList[i])
        if category and not category == u'':
            result.append(category)
    return result


def getOpenStreetMap(latitude, longitude):
    """
    Get the result from https://nominatim.openstreetmap.org/reverse .

    @rtype: list of tuples
    """
    result = []
    gotInfo = False
    parameters = urlencode({'lat': latitude, 'lon': longitude, 'accept-language': 'en'})
    while not gotInfo:
        try:
            page = fetch('https://nominatim.openstreetmap.org/reverse?format=xml&%s' % parameters)
            et = xml.etree.ElementTree.fromstring(page.text)
            gotInfo = True
        except IOError:
            pywikibot.output(u'Got an IOError, let\'s try again')
            time.sleep(30)
        except socket.timeout:
            pywikibot.output(u'Got a timeout, let\'s try again')
            time.sleep(30)
    validParts = [u'hamlet', u'village', u'city', u'county', u'country']
    invalidParts = [u'path', u'road', u'suburb', u'state', u'country_code']
    addressparts = et.find('addressparts')

    for addresspart in addressparts.getchildren():
        if addresspart.tag in validParts:
            result.append(addresspart.text)
        elif addresspart.tag in invalidParts:
            pywikibot.output(u'Dropping %s, %s' % (addresspart.tag, addresspart.text))
        else:
            pywikibot.warning('%s, %s is not in addressparts lists'
                              % (addresspart.tag, addresspart.text))
    return result


def getCategoryByName(name, parent=u'', grandparent=u''):
    """Get category by name."""
    if not parent == u'':
        workname = name.strip() + u',_' + parent.strip()
        workcat = pywikibot.Category(pywikibot.Site(u'commons', u'commons'), workname)
        if workcat.exists():
            return workname
    if not grandparent == u'':
        workname = name.strip() + u',_' + grandparent.strip()
        workcat = pywikibot.Category(pywikibot.Site(u'commons', u'commons'), workname)
        if workcat.exists():
            return workname
    workname = name.strip()
    workcat = pywikibot.Category(pywikibot.Site(u'commons', u'commons'), workname)
    if workcat.exists():
        return workname
    return u''


def getUsage(use):
    """Parse the Commonsense output to get the usage."""
    result = []
    lang = ''
    project = ''
    article = ''
    usageRe = re.compile(
        r'^(?P<lang>([\w-]+))\.(?P<project>([\w]+))\.org:(?P<articles>\s(.*))')
    matches = usageRe.search(use)
    if matches:
        if matches.group('lang'):
            lang = matches.group('lang')
        if matches.group('project'):
            project = matches.group('project')
        if matches.group('articles'):
            articles = matches.group('articles')
    for article in articles.split():
        result.append((lang, project, article))
    return result


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
        if (not pywikibot.Page(pywikibot.Site(u'commons', u'commons'),
                               cat, ns=14).isDisambig()):
            result.append(cat)
    return result


def followRedirects(categories):
    """If a category is a redirect, replace the category with the target."""
    result = []
    for cat in categories:
        categoryPage = pywikibot.Page(pywikibot.Site(u'commons', u'commons'),
                                      cat, ns=14)
        if categoryPage.isCategoryRedirect():
            result.append(
                categoryPage.getCategoryRedirectTarget().title(
                    withNamespace=False))
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
        if cat.endswith(u'by country'):
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
                pywikibot.Site(u'commons', u'commons'), u'Category:' + bc)
            for subcategory in category.subcategories():
                for country in listCountries:
                    if subcategory.title(withNamespace=False).endswith(country):
                        result.append(subcategory.title(withNamespace=False))
    return list(set(result))


@deprecated
def filterParents(categories):
    """
    Remove all parent categories from the set to prevent overcategorization.

    DEPRECATED: Toolserver script isn't available anymore (T78462).
    This method is kept for compatibility and may be restored sometime by a new
    implementation.
    """
    return categories


def saveImagePage(imagepage, newcats, usage, galleries, onlyFilter):
    """Remove the old categories and add the new categories to the image."""
    newtext = textlib.removeCategoryLinks(imagepage.text, imagepage.site)
    if not onlyFilter:
        newtext = removeTemplates(newtext)
        newtext = newtext + getCheckCategoriesTemplate(usage, galleries,
                                                       len(newcats))
    newtext += u'\n'
    for category in newcats:
        newtext = newtext + u'[[Category:' + category + u']]\n'
    if onlyFilter:
        comment = u'Filtering categories'
    else:
        comment = ('Image is categorized by a bot using data from '
                   '[[Commons:Tools#CommonSense|CommonSense]]')
    pywikibot.showDiff(imagepage.text, newtext)
    imagepage.text = newtext
    imagepage.save(comment)
    return


def removeTemplates(oldtext=u''):
    """Remove {{Uncategorized}} and {{Check categories}} templates."""
    result = re.sub(
        r'{{\s*([Uu]ncat(egori[sz]ed( image)?)?|[Nn]ocat|[Nn]eedscategory)[^}]*}}',
        u'', oldtext)
    result = re.sub(u'<!-- Remove this line once you have added categories -->',
                    u'', result)
    result = re.sub(r'\{\{\s*[Cc]heck categories[^}]*\}\}', u'', result)
    return result


def getCheckCategoriesTemplate(usage, galleries, ncats):
    """Build the check categories template with all parameters."""
    result = ('{{Check categories|year={{subst:CURRENTYEAR}}|month={{subst:'
              'CURRENTMONTHNAME}}|day={{subst:CURRENTDAY}}\n')
    usageCounter = 1
    for (lang, project, article) in usage:
        result += u'|lang%d=%s' % (usageCounter, lang)
        result += u'|wiki%d=%s' % (usageCounter, project)
        result += u'|article%d=%s' % (usageCounter, article)
        result += u'\n'
        usageCounter += 1
    galleryCounter = 1
    for gallery in galleries:
        result += u'|gallery%d=%s' % (galleryCounter, gallery.replace('_', ' ')) + u'\n'
        galleryCounter += 1
    result += u'|ncats=%d\n' % ncats
    result += u'}}\n'
    return result


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    generator = None
    onlyFilter = False
    onlyUncat = False

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    global search_wikis
    global hint_wiki

    for arg in local_args:
        if arg == '-onlyfilter':
            onlyFilter = True
        elif arg == '-onlyuncat':
            onlyUncat = True
        elif arg.startswith('-hint:'):
            hint_wiki = arg[len('-hint:'):]
        elif arg.startswith('-onlyhint'):
            search_wikis = arg[len('-onlyhint:'):]
        else:
            genFactory.handleArg(arg)

    generator = genFactory.getCombinedGenerator()
    if not generator:
        site = pywikibot.Site(u'commons', u'commons')
        generator = pagegenerators.CategorizedPageGenerator(
            pywikibot.Category(site, u'Category:Media needing categories'),
            recurse=True)

    initLists()
    categorizeImages(generator, onlyFilter, onlyUncat)
    pywikibot.output(u'All done')


if __name__ == "__main__":
    main()
