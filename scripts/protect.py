#!/usr/bin/python
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

-expiry:          Supply a custom protection expiry, which defaults to
                  indefinite. Any string understandable by MediaWiki, including
                  relative and absolute, is acceptable. See:
                  https://www.mediawiki.org/wiki/API:Protect#Parameters

-unprotect        Acts like "default:all"

-default:         Sets the default protection level (default 'sysop'). If no
                  level is defined it doesn't change unspecified levels.

-[type]:[level]   Set [type] protection level to [level]

Usual values for [level] are: sysop, autoconfirmed, all; further levels may be
provided by some wikis.

For all protection types (edit, move, etc.) it chooses the default protection
level. This is "sysop" or "all" if -unprotect was selected. If multiple
parameters -unprotect or -default are used, only the last occurrence
is applied.

Usage:

    python pwb.py protect <OPTIONS>

Examples
--------

Protect everything in the category 'To protect' prompting:

    python pwb.py protect -cat:"To protect"

Unprotect all pages listed in text file 'unprotect.txt' without prompting:

    python pwb.py protect -file:unprotect.txt -unprotect -always
"""
#
# Created by modifying delete.py
#
# (C) Pywikibot team, 2008-2020
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import CurrentPageBot, SingleSiteBot


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class ProtectionRobot(SingleSiteBot, CurrentPageBot):

    """This bot allows protection of pages en masse."""

    def __init__(self, generator, protections, **kwargs):
        """
        Create a new ProtectionRobot.

        :param generator: the page generator
        :type generator: generator
        :param protections: protections as a dict with "type": "level"
        :type protections: dict
        :param kwargs: additional arguments directly feed to super().__init__()
        """
        self.available_options.update({
            'summary': None,
            'expiry': None,
        })
        super().__init__(**kwargs)
        self.generator = generator
        self.protections = protections

    def treat_page(self):
        """Run the bot's action on each page.

        treat_page treats every page given by the generator and applies
        the protections using this method.
        """
        if not self.user_confirm(
                'Do you want to change the protection level of {}?'
                .format(self.current_page.title(as_link=True,
                                                force_interwiki=True))):
            return

        applicable = self.current_page.applicable_protections()
        protections = dict(
            prot for prot in self.protections.items() if prot[0] in applicable)
        self.current_page.protect(reason=self.opt.summary,
                                  expiry=self.opt.expiry,
                                  protections=protections)


def check_protection_level(operation, level, levels, default=None):
    """Check if the protection level is valid or ask if necessary.

    :return: a valid protection level
    :rtype: str
    """
    if level in levels:
        return level

    # ask for a valid level
    levels = sorted(levels)  # sort to be deterministic
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

    choice = pywikibot.input_choice('Choose a protection level to {}:'
                                    .format(operation),
                                    zip(levels, first_char),
                                    default=default_char)

    return levels[first_char.index(choice)]


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    options = {}
    message_properties = {}
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
    site = pywikibot.Site()

    generator_type = None
    protection_levels = site.protection_levels()
    if '' in protection_levels:
        protection_levels.add('all')

    protection_types = site.protection_types()
    gen_factory = pagegenerators.GeneratorFactory()
    for arg in local_args:
        option, sep, value = arg.partition(':')
        if not option.startswith('-'):
            continue

        option = option[1:]
        if option == 'always':
            options[option] = True
        elif option == 'summary':
            options[option] = value or None
        elif option == 'expiry':
            options[option] = value or pywikibot.input(
                'Enter a protection expiry:')
        elif option == 'unprotect':
            default_level = 'all'
        elif option == 'default':
            default_level = value if sep else 'sysop'
        elif option in protection_types and value:
            protections[option] = value
        else:
            if not gen_factory.handle_arg(arg):
                raise ValueError('Unknown parameter "{}"'.format(arg))
            if value:
                message_properties.update({'cat': value, 'page': value})
            if 'summary' not in options:
                generator_type = option

    if generator_type in default_summaries:
        message_type = default_summaries[generator_type]
        if message_type == 'simple' or message_properties:
            if default_level == 'all':
                options['summary'] = i18n.twtranslate(
                    site, 'unprotect-{}'.format(message_type),
                    message_properties)
            else:
                options['summary'] = i18n.twtranslate(
                    site, 'protect-{}'.format(message_type),
                    message_properties)

    generator = gen_factory.getCombinedGenerator()
    # We are just protecting pages, so we have no need of using a preloading
    # page generator to actually get the text of those pages.
    if generator:
        default_level = check_protection_level('Default level',
                                               default_level,
                                               protection_levels)
        # set the default value for all
        # None (not the string 'none') will be ignored by Site.protect()
        combined_protections = {p_type: default_level
                                for p_type in protection_types}
        for p_type, level in protections.items():
            level = check_protection_level(p_type, level, protection_levels,
                                           default_level)
            # '' is equivalent to 'all'
            if level in ('none', ''):
                level = 'all'
            combined_protections[p_type] = level
        if not options.get('summary'):
            options['summary'] = pywikibot.input(
                'Enter a reason for the protection change:')
        bot = ProtectionRobot(generator, combined_protections, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
