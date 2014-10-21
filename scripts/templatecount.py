#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This script will display the list of pages transcluding a given list of templates.

It can also be used to simply count the number of pages (rather than
listing each individually).

Syntax: python templatecount.py command [arguments]

Command line options:

-count        Counts the number of times each template (passed in as an
              argument) is transcluded.

-list         Gives the list of all of the pages transcluding the templates
              (rather than just counting them).

-namespace:   Filters the search to a given namespace.  If this is specified
              multiple times it will search all given namespaces

Examples:

Counts how many times {{ref}} and {{note}} are transcluded in articles.

     python templatecount.py -count -namespace:0 ref note

Lists all the category pages that transclude {{cfd}} and {{cfdu}}.

     python templatecount.py -list -namespace:14 cfd cfdu

"""
#
# (C) Pywikibot team, 2006-2014
# (C) xqt, 2009-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import datetime
import pywikibot
from pywikibot import pagegenerators

templates = ['ref', 'note', 'ref label', 'note label', 'reflist']


class TemplateCountRobot:

    """Template count bot."""

    @staticmethod
    def countTemplates(templates, namespaces):
        templateDict = TemplateCountRobot.template_dict(templates, namespaces)
        pywikibot.output(u'\nNumber of transclusions per template',
                         toStdout=True)
        pywikibot.output(u'-' * 36, toStdout=True)
        total = 0
        for key in templateDict:
            count = len(templateDict[key])
            pywikibot.output(u'%-10s: %5d' % (key, count),
                             toStdout=True)
            total += count
        pywikibot.output(u'TOTAL     : %5d' % total, toStdout=True)
        pywikibot.output(u'Report generated on %s'
                         % datetime.datetime.utcnow().isoformat(),
                         toStdout=True)

    @staticmethod
    def listTemplates(templates, namespaces):
        templateDict = TemplateCountRobot.template_dict(templates, namespaces)
        pywikibot.output(u'\nList of pages transcluding templates:',
                         toStdout=True)
        for key in templates:
            pywikibot.output(u'* %s' % key)
        pywikibot.output(u'-' * 36, toStdout=True)
        total = 0
        for key in templateDict:
            for page in templateDict[key]:
                pywikibot.output(page.title(), toStdout=True)
                total += 1
        pywikibot.output(u'Total page count: %d' % total)
        pywikibot.output(u'Report generated on %s'
                         % datetime.datetime.utcnow().isoformat(),
                         toStdout=True)

    @staticmethod
    def template_dict(templates, namespaces):
        gen = TemplateCountRobot.template_dict_generator(templates, namespaces)
        templateDict = {}
        for template, transcludingArray in gen:
            templateDict[template] = transcludingArray
        return templateDict

    @staticmethod
    def template_dict_generator(templates, namespaces):
        mysite = pywikibot.Site()
        # The names of the templates are the keys, and lists of pages
        # transcluding templates are the values.
        mytpl = mysite.getNamespaceIndex(mysite.template_namespace())
        for template in templates:
            transcludingArray = []
            gen = pagegenerators.ReferringPageGenerator(
                pywikibot.Page(mysite, template, ns=mytpl),
                onlyTemplateInclusion=True)
            if namespaces:
                gen = pagegenerators.NamespaceFilterPageGenerator(gen, namespaces)
            for page in gen:
                transcludingArray.append(page)
            yield template, transcludingArray


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    operation = None
    argsList = []
    namespaces = []

    for arg in pywikibot.handle_args(args):
        if arg in ('-count', '-list'):
            operation = arg[1:]
        elif arg.startswith('-namespace:'):
            try:
                namespaces.append(int(arg[len('-namespace:'):]))
            except ValueError:
                namespaces.append(arg[len('-namespace:'):])
        else:
            argsList.append(arg)

    if not operation:
        pywikibot.showHelp('templatecount')
        return

    robot = TemplateCountRobot()
    if not argsList:
        argsList = templates

    if 'reflist' in argsList:
        pywikibot.output(
            u'NOTE: it will take a long time to count "reflist".')
        choice = pywikibot.inputChoice(
            u'Proceed anyway?', ['yes', 'no', 'skip'], ['y', 'n', 's'], 'y')
        if choice == 's':
            argsList.remove('reflist')
        elif choice == 'n':
            return

    if operation == "count":
        robot.countTemplates(argsList, namespaces)
    elif operation == "list":
        robot.listTemplates(argsList, namespaces)

if __name__ == "__main__":
    main()
