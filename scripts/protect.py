#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script can be used to protect and unprotect pages en masse.

Of course, you will need an admin account on the relevant wiki.
These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-always           Don't prompt to protect pages, just do it.

-summary:         Supply a custom edit summary. Tries to generate summary from
                  the page selector. If no summary is supplied or couldn't
                  determine one from the selector it'll ask for one.

-unprotect        Acts like "default:all"

-default:         Sets the default protection level (default 'sysop'). If no
                  level is defined it doesn't change unspecified levels.

-[type]:[level]   Set [type] protection level to [level]

Usual values for [level] are: sysop, autoconfirmed, all; further levels may be
provided by some wikis.

For all protection types (edit, move, etc.) it chooses the default protection
level. This is "sysop" or "all" if -unprotect was selected. If multiple
-unprotect or -default are used, only the last occurrence is applied.

Usage: python protect.py <OPTIONS>

Examples:

Protect everything in the category 'To protect' prompting.
    python protect.py -cat:'To protect'

Unprotect all pages listed in text file 'unprotect.txt' without prompting.
    python protect.py -file:unprotect.txt -unprotect -always
"""
#
# Written by https://it.wikisource.org/wiki/Utente:Qualc1
# Created by modifying delete.py
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n, pagegenerators, Bot

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;':     pagegenerators.parameterHelp,
}


class ProtectionRobot(Bot):

    """This bot allows protection of pages en masse."""

    def __init__(self, generator, protections, **kwargs):
        """
        Create a new ProtectionRobot.

        @param generator: the page generator
        @type generator: generator
        @param protections: protections as a dict with "type": "level"
        @type protections: dict
        @param kwargs: additional arguments directly feed to Bot.__init__()
        """
        self.availableOptions.update({
            'summary': None,
        })
        super(ProtectionRobot, self).__init__(**kwargs)
        self.generator = generator
        self.protections = protections

    def treat(self, page):
        """Run the bot's action on each page.

        Bot.run() loops through everything in the page generator and applies
        the protections using this function.
        """
        self.current_page = page
        if not self.getOption('always'):
            choice = pywikibot.input_choice(
                u'Do you want to change the protection level of %s?'
                % page.title(asLink=True, forceInterwiki=True),
                [('yes', 'y'), ('No', 'n'), ('all', 'a')], 'n')
            if choice == 'n':
                return
            elif choice == 'a':
                self.options['always'] = True
        applicable = page.applicable_protections()
        protections = dict(
            prot for prot in self.protections.items() if prot[0] in applicable)
        page.protect(reason=self.getOption('summary'),
                     protections=protections)


def check_protection_level(operation, level, levels, default=None):
    """Check if the protection level is valid or ask if necessary.

    @return: a valid protection level
    @rtype: string
    """
    if level not in levels:
        first_char = []
        default_char = None
        num = 1
        for level in levels:
            for c in level:
                if c not in first_char:
                    first_char.append(c)
                    break
            else:
                first_char.append(str(num))
                num += 1
            if level == default:
                default_char = first_char[-1]
        choice = pywikibot.input_choice('Choice a protection level to %s:'
                                        % operation, zip(levels, first_char),
                                        default=default_char)

        return levels[first_char.index(choice)]
    else:
        return level


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    options = {}
    message_properties = {}
    generator = None
    protections = {}
    default_level = 'sysop'
    default_summaries = {
        'cat': 'category',
        'links': 'links',
        'ref': 'ref',
        'imageused': 'images',
        'file': 'simple',
    }

    # read command line parameters
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()
    site = pywikibot.Site()

    generator_type = None
    protection_levels = set(site.protection_levels())
    protection_types = site.protection_types()
    if '' in protection_levels:
        protection_levels.add('all')
    for arg in local_args:
        if arg == '-always':
            options['always'] = True
        elif arg.startswith('-summary'):
            if len(arg) == len('-summary'):
                # fill dummy value to prevent automatic generation
                options['summary'] = None
            else:
                options['summary'] = arg[len('-summary:'):]
        elif arg.startswith('-images'):
            pywikibot.output('\n\03{lightred}-image option is deprecated. '
                             'Please use -imagelinks instead.\03{default}\n')
            local_args.append('-imagelinks' + arg[7:])
        elif arg.startswith('-unprotect'):
            default_level = 'all'
        elif arg.startswith('-default'):
            if len(arg) == len('-default'):
                default_level = 'sysop'
            else:
                default_level = arg[len('-default:'):]
        else:
            is_p_type = False
            if arg.startswith('-'):
                delimiter = arg.find(':')
                if delimiter > 0:
                    p_type_arg = arg[1:delimiter]
                    level = arg[delimiter + 1:]
                    if p_type_arg in protection_types:
                        protections[p_type_arg] = level
                        is_p_type = True
            if not is_p_type:
                if not genFactory.handleArg(arg):
                    raise ValueError('Unknown parameter "{0}"'.format(arg))
                found = arg.find(':')
                if found:
                    message_properties.update({'cat': arg[found + 1:],
                                               'page': arg[found + 1:]})

                if 'summary' not in options:
                    generator_type = arg[1:found] if found > 0 else arg[1:]

    if generator_type in default_summaries:
        message_type = default_summaries[generator_type]
        if message_type == 'simple' or message_properties:
            if default_level == 'all':
                options['summary'] = i18n.twtranslate(
                    site, 'unprotect-{0}'.format(message_type),
                    message_properties)
            else:
                options['summary'] = i18n.twtranslate(
                    site, 'protect-{0}'.format(message_type),
                    message_properties)

    generator = genFactory.getCombinedGenerator()
    # We are just protecting pages, so we have no need of using a preloading
    # page generator to actually get the text of those pages.
    if generator:
        if default_level:
            default_level = check_protection_level('Default level',
                                                   default_level,
                                                   protection_levels)
        # set the default value for all
        # None (not the string 'none') will be ignored by Site.protect()
        combined_protections = dict([
            (p_type, default_level) for p_type in protection_types])
        for p_type, level in protections.items():
            level = check_protection_level(p_type, level, protection_levels,
                                           default_level)
            # '' is equivalent to 'all'
            if level == 'none' or level == '':
                level = 'all'
            combined_protections[p_type] = level
        if not options.get('summary'):
            options['summary'] = pywikibot.input(
                u'Enter a reason for the protection change:')
        bot = ProtectionRobot(generator, combined_protections, **options)
        bot.run()
    else:
        # Show help text from the top of this file
        pywikibot.showHelp()


if __name__ == '__main__':
    main()
