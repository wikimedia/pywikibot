#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Display the list of pages transcluding a given list of templates.

It can also be used to simply count the number of pages (rather than
listing each individually).

Syntax:

    python pwb.py templatecount options templates

Command line options:

-count        Counts the number of times each template (passed in as an
              argument) is transcluded.

-list         Gives the list of all of the pages transcluding the templates
              (rather than just counting them).

-namespace:   Filters the search to a given namespace. If this is specified
              multiple times it will search all given namespaces

Examples
--------

Counts how many times {{ref}} and {{note}} are transcluded in articles:

    python pwb.py templatecount -count -namespace:0 ref note

Lists all the category pages that transclude {{cfd}} and {{cfdu}}:

    python pwb.py templatecount -list -namespace:14 cfd cfdu

"""
#
# (C) Pywikibot team, 2006-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import datetime

import pywikibot

templates = ['ref', 'note', 'ref label', 'note label', 'reflist']


class TemplateCountRobot(object):

    """Template count bot."""

    @classmethod
    def countTemplates(cls, templates, namespaces):
        """
        Display number of transclusions for a list of templates.

        Displays the number of transcluded page in the given 'namespaces' for
        each template given by 'templates' list.

        @param templates: list of template names
        @type templates: list
        @param namespaces: list of namespace numbers
        @type namespaces: list
        """
        format = '{0:<10}: {1:>5}'
        template_dict = cls.template_dict(templates, namespaces)
        pywikibot.stdout('\nNumber of transclusions per template')
        pywikibot.stdout('-' * 36)
        total = 0
        for key in template_dict:
            count = len(template_dict[key])
            pywikibot.stdout(format.format(key, count))
            total += count
        pywikibot.stdout(format.format('TOTAL', total))
        pywikibot.stdout('Report generated on {}'
                         .format(datetime.datetime.utcnow().isoformat()))

    @classmethod
    def listTemplates(cls, templates, namespaces):
        """
        Display transcluded pages for a list of templates.

        Displays each transcluded page in the given 'namespaces' for
        each template given by 'templates' list.

        @param templates: list of template names
        @type templates: list
        @param namespaces: list of namespace numbers
        @type namespaces: list
        """
        template_dict = cls.template_dict(templates, namespaces)
        pywikibot.stdout('\nList of pages transcluding templates:')
        for key in templates:
            pywikibot.output('* ' + key)
        pywikibot.stdout('-' * 36)
        total = 0
        for key in template_dict:
            for page in template_dict[key]:
                pywikibot.stdout(page.title())
                total += 1
        pywikibot.output('Total page count: {}'.format(total))
        pywikibot.stdout('Report generated on {}'
                         .format(datetime.datetime.utcnow().isoformat()))

    @classmethod
    def template_dict(cls, templates, namespaces):
        """
        Create a dict of templates and its transcluded pages.

        The names of the templates are the keys, and lists of pages
        transcluding templates in the given namespaces are the values.

        @param templates: list of template names
        @type templates: list
        @param namespaces: list of namespace numbers
        @type namespaces: list

        @rtype: dict
        """
        return dict(cls.template_dict_generator(templates, namespaces))

    @staticmethod
    def template_dict_generator(templates, namespaces):
        """
        Yield transclusions of each template in 'templates'.

        For each template in 'templates', yield a tuple
        (template, transclusions), where 'transclusions' is a list of all pages
        in 'namespaces' where the template has been transcluded.

        @param templates: list of template names
        @type templates: list
        @param namespaces: list of namespace numbers
        @type namespaces: list

        @rtype: generator
        """
        mysite = pywikibot.Site()
        mytpl = mysite.namespaces.TEMPLATE
        for template in templates:
            transcluding_array = []
            gen = pywikibot.Page(mysite, template, ns=mytpl).getReferences(
                namespaces=namespaces, only_template_inclusion=True)
            for page in gen:
                transcluding_array.append(page)
            yield template, transcluding_array


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    operation = None
    args_list = []
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
            args_list.append(arg)

    if not operation:
        pywikibot.bot.suggest_help(missing_parameters=['operation'])
        return

    robot = TemplateCountRobot()
    if not args_list:
        args_list = templates

    if 'reflist' in args_list:
        pywikibot.output(
            'NOTE: it will take a long time to count "reflist".')
        choice = pywikibot.input_choice(
            'Proceed anyway?',
            [('yes', 'y'), ('no', 'n'), ('skip', 's')], 'y',
            automatic_quit=False)
        if choice == 's':
            args_list.remove('reflist')
        elif choice == 'n':
            return

    if operation == 'count':
        robot.countTemplates(args_list, namespaces)
    elif operation == 'list':
        robot.listTemplates(args_list, namespaces)


if __name__ == '__main__':
    main()
