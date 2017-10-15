#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
Very simple script to replace a template with another one.

It also converts the old MediaWiki boilerplate format to the new format.

Syntax: python template.py [-remove] [xml[:filename]] oldTemplate [newTemplate]

Specify the template on the command line. The program will pick up the template
page, and look for all pages using it. It will then automatically loop over
them, and replace the template.

Command line options:

-remove      Remove every occurrence of the template from every article

-subst       Resolves the template by putting its text directly into the
             article. This is done by changing {{...}} or {{msg:...}} into
             {{subst:...}}.
             Substitution is not available inside <ref>...</ref>,
             <gallery>...</gallery>, <poem>...</poem> and <pagelist ... />
             tags.

-assubst     Replaces the first argument as old template with the second
             argument as new template but substitutes it like -subst does.
             Using both options -remove and -subst in the same command line has
             the same effect.

-xml         retrieve information from a local dump
             (https://download.wikimedia.org). If this argument isn't given,
             info will be loaded from the maintenance page of the live wiki.
             argument can also be given as "-xml:filename.xml".

-onlyuser:   Only process pages edited by a given user

-skipuser:   Only process pages not edited by a given user

-timestamp:  (With -onlyuser or -skipuser). Only check for a user where his
             edit is not older than the given timestamp. Timestamp must be
             writen in MediaWiki timestamp format which is "%Y%m%d%H%M%S".
             If this parameter is missed, all edits are checked but this is
             restricted to the last 100 edits.

-summary:    Lets you pick a custom edit summary. Use quotes if edit summary
             contains spaces.

-always      Don't bother asking to confirm any of the changes, Just Do It.

-addcat:     Appends the given category to every page that is edited. This is
             useful when a category is being broken out from a template
             parameter or when templates are being upmerged but more
             information must be preserved.

other:       First argument is the old template name, second one is the new
             name.

             If you want to address a template which has spaces, put quotation
             marks around it, or use underscores.

Examples:

If you have a template called [[Template:Cities in Washington]] and want to
change it to [[Template:Cities in Washington state]], start

    python pwb.py template "Cities in Washington" "Cities in Washington state"

Move the page [[Template:Cities in Washington]] manually afterwards.


If you have a template called [[Template:test]] and want to substitute it only
on pages in the User: and User talk: namespaces, do:

    python pwb.py template test -subst -namespace:2 -namespace:3

Note that -namespace: is a global Pywikibot parameter


This next example substitutes the template lived with a supplied edit summary.
It only performs substitutions in main article namespace and doesn't prompt to
start replacing. Note that -putthrottle: is a global Pywikibot parameter.

    python pwb.py template -putthrottle:30 -namespace:0 lived -subst -always \
        -summary:"BOT: Substituting {{lived}}, see [[WP:SUBST]]."


This next example removes the templates {{cfr}}, {{cfru}}, and {{cfr-speedy}}
from five category pages as given:

    python pwb.py template cfr cfru cfr-speedy -remove -always \
        -page:"Category:Mountain monuments and memorials" \
        -page:"Category:Indian family names" \
        -page:"Category:Tennis tournaments in Belgium" \
        -page:"Category:Tennis tournaments in Germany" \
        -page:"Category:Episcopal cathedrals in the United States" \
        -summary:"Removing Cfd templates from category pages that survived."


This next example substitutes templates test1, test2, and space test on all
user talk pages (namespace #3):

    python pwb.py template test1 test2 "space test" -subst -ns:3 -always

"""
#
# (C) Daniel Herding, 2004
# (C) Rob W.W. Hooft, 2003-2005
# (C) xqt, 2009-2017
# (C) Pywikibot team, 2004-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import re

from warnings import warn

import pywikibot

from pywikibot import i18n, pagegenerators, textlib, Bot

from pywikibot.exceptions import ArgumentDeprecationWarning
from pywikibot.pagegenerators import XMLDumpPageGenerator
from pywikibot.tools import deprecated

from scripts.replace import ReplaceRobot as ReplaceBot


@deprecated('XMLDumpPageGenerator')
class XmlDumpTemplatePageGenerator(XMLDumpPageGenerator):

    """
    Generator which yields Pages that transclude a template.

    These pages will be retrieved from a local XML dump file
    (cur table), and may not still transclude the template.
    """

    def __init__(self, templates, xmlfilename):
        """
        Constructor.

        @param templateNames: A list of Page objects representing the searched
            templates
        @type templateNames: list
        @param xmlfilename: The dump's path, either absolute or relative
        @type xmlfilename: str

        """
        self.templates = templates
        self.xmlfilename = xmlfilename
        mysite = pywikibot.Site()
        # regular expression to find the original template.
        # {{vfd}} does the same thing as {{Vfd}}, so both will be found.
        # The old syntax, {{msg:vfd}}, will also be found.
        templatePatterns = []
        for template in self.templates:
            templatePattern = template.title(withNamespace=False)
            if mysite.namespaces[10].case == 'first-letter':
                templatePattern = '[%s%s]%s' % (templatePattern[0].upper(),
                                                templatePattern[0].lower(),
                                                templatePattern[1:])
            templatePattern = re.sub(' ', '[_ ]', templatePattern)
            templatePatterns.append(templatePattern)
        templateRegex = re.compile(
            r'\{\{ *([mM][sS][gG]:)?(?:%s) *(?P<parameters>\|[^}]+|) *}}'
            % '|'.join(templatePatterns))

        super(XmlDumpTemplatePageGenerator, self).__init__(
            xmlfilename, site=mysite, text_predicate=templateRegex.search)


class TemplateRobot(ReplaceBot):

    """This bot will replace, remove or subst all occurrences of a template."""

    def __init__(self, generator, templates, **kwargs):
        """
        Constructor.

        @param generator: the pages to work on
        @type generator: iterable
        @param templates: a dictionary which maps old template names to
            their replacements. If remove or subst is True, it maps the
            names of the templates that should be removed/resolved to None.
        @type templates: dict
        """
        self.availableOptions.update({
            'subst': False,
            'remove': False,
            'summary': None,
            'addedCat': None,
        })

        Bot.__init__(self, generator=generator, **kwargs)

        self.templates = templates

        # get edit summary message if it's empty
        if not self.getOption('summary'):
            comma = self.site.mediawiki_message('comma-separator')
            params = {'list': comma.join(self.templates.keys()),
                      'num': len(self.templates)}

            if self.getOption('remove'):
                self.options['summary'] = i18n.twtranslate(
                    self.site, 'template-removing', params)
            elif self.getOption('subst'):
                self.options['summary'] = i18n.twtranslate(
                    self.site, 'template-substituting', params)
            else:
                self.options['summary'] = i18n.twtranslate(
                    self.site, 'template-changing', params)

        replacements = []
        exceptions = {}
        builder = textlib._MultiTemplateMatchBuilder(self.site)
        for old, new in self.templates.items():
            templateRegex = builder.pattern(old)

            if self.getOption('subst') and self.getOption('remove'):
                replacements.append((templateRegex,
                                     r'{{subst:%s\g<parameters>}}' % new))
                exceptions['inside-tags'] = ['ref', 'gallery', 'poem',
                                             'pagelist', ]
            elif self.getOption('subst'):
                replacements.append((templateRegex,
                                     r'{{subst:%s\g<parameters>}}' % old))
                exceptions['inside-tags'] = ['ref', 'gallery', 'poem',
                                             'pagelist', ]
            elif self.getOption('remove'):
                separate_line_regex = re.compile(
                    r'^[*#:]* *{0} *\n'.format(templateRegex.pattern),
                    re.DOTALL | re.MULTILINE)
                replacements.append((separate_line_regex, ''))

                spaced_regex = re.compile(
                    r' +{0} +'.format(templateRegex.pattern),
                    re.DOTALL)
                replacements.append((spaced_regex, ' '))

                replacements.append((templateRegex, ''))
            else:
                template = pywikibot.Page(self.site, new, ns=10)
                if not template.exists():
                    pywikibot.warning(u'Template "%s" does not exist.' % new)
                    if not pywikibot.input_yn('Do you want to proceed anyway?',
                                              default=False,
                                              automatic_quit=False):
                        continue
                replacements.append((templateRegex,
                                     r'{{%s\g<parameters>}}' % new))

        super(TemplateRobot, self).__init__(
            generator, replacements, exceptions,
            always=self.getOption('always'),
            addedCat=self.getOption('addedCat'),
            summary=self.getOption('summary'))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    templateNames = []
    templates = {}
    options = {}
    # If xmlfilename is None, references will be loaded from the live wiki.
    xmlfilename = None
    user = None
    skip = False
    timestamp = None

    # read command line parameters
    local_args = pywikibot.handle_args(args)

    # Avoid conflicts with pagegenerators.py parameters.
    if any(arg.startswith('-category:') for arg in local_args):
        warn('-category (to append a category to each edited page) has been'
             ' renamed to -addcat; make sure you are using the correct param.',
             ArgumentDeprecationWarning)

    site = pywikibot.Site()
    genFactory = pagegenerators.GeneratorFactory()
    for arg in local_args:
        if arg == '-remove':
            options['remove'] = True
        elif arg == '-subst':
            options['subst'] = True
        elif arg == '-assubst':
            options['subst'] = options['remove'] = True
        elif arg == '-always':
            options['always'] = True
        elif arg.startswith('-xml'):
            if len(arg) == 4:
                xmlfilename = pywikibot.input(
                    u'Please enter the XML dump\'s filename: ')
            else:
                xmlfilename = arg[5:]
        elif arg.startswith('-addcat:'):
            options['addedCat'] = arg[len('-addcat:'):]
        elif arg.startswith('-summary:'):
            options['summary'] = arg[len('-summary:'):]
        elif arg.startswith('-onlyuser:'):
            user = arg[len('-onlyuser:'):]
        elif arg.startswith('-skipuser:'):
            user = arg[len('-skipuser:'):]
            skip = True
        elif arg.startswith('-timestamp:'):
            timestamp = arg[len('-timestamp:'):]
        else:
            if not genFactory.handleArg(arg):
                templateName = pywikibot.Page(site, arg, ns=10)
                templateNames.append(templateName.title(withNamespace=False))

    if not templateNames:
        pywikibot.bot.suggest_help(missing_parameters=['templates'])
        return False

    if options.get('subst', False) ^ options.get('remove', False):
        for templateName in templateNames:
            templates[templateName] = None
    else:
        try:
            for i in range(0, len(templateNames), 2):
                templates[templateNames[i]] = templateNames[i + 1]
        except IndexError:
            pywikibot.output('Unless using solely -subst or -remove, '
                             'you must give an even number of template names.')
            return

    oldTemplates = []
    for templateName in templates.keys():
        oldTemplate = pywikibot.Page(site, templateName, ns=10)
        oldTemplates.append(oldTemplate)

    if xmlfilename:
        builder = textlib._MultiTemplateMatchBuilder(site)
        predicate = builder.search_any_predicate(oldTemplates)

        gen = XMLDumpPageGenerator(
            xmlfilename, site=site, text_predicate=predicate)
    else:
        gen = genFactory.getCombinedGenerator()

    if not gen:
        gens = [
            pagegenerators.ReferringPageGenerator(t,
                                                  onlyTemplateInclusion=True)
            for t in oldTemplates
        ]
        gen = pagegenerators.CombinedPageGenerator(gens)
        gen = pagegenerators.DuplicateFilterPageGenerator(gen)
    if user:
        gen = pagegenerators.UserEditFilterGenerator(gen, user, timestamp,
                                                     skip,
                                                     max_revision_depth=100,
                                                     show_filtered=True)

    if not genFactory.gens:
        # make sure that proper namespace filtering etc. is handled
        gen = genFactory.getCombinedGenerator(gen)

    if not genFactory.nopreload:
        gen = pagegenerators.PreloadingGenerator(gen)

    bot = TemplateRobot(gen, templates, site=site, **options)
    bot.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pywikibot.error("Fatal error:", exc_info=True)
