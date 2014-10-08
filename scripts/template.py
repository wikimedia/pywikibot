#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Very simple script to replace a template with another one.

It also converts the old MediaWiki boilerplate format to the new template format.

Syntax: python template.py [-remove] [xml[:filename]] oldTemplate [newTemplate]

Specify the template on the command line. The program will pick up the template
page, and look for all pages using it. It will then automatically loop over
them, and replace the template.

Command line options:

-remove      Remove every occurence of the template from every article

-subst       Resolves the template by putting its text directly into the
             article. This is done by changing {{...}} or {{msg:...}} into
             {{subst:...}}

-assubst     Replaces the first argument as old template with the second
             argument as new template but substitutes it like -subst does.
             Using both options -remove and -subst in the same command line has
             the same effect.

-xml         retrieve information from a local dump
             (https://download.wikimedia.org). If this argument isn't given,
             info will be loaded from the maintenance page of the live wiki.
             argument can also be given as "-xml:filename.xml".

-user:       Only process pages edited by a given user

-skipuser:   Only process pages not edited by a given user

-timestamp:  (With -user or -skipuser). Only check for a user where his edit is
             not older than the given timestamp. Timestamp must be writen in
             MediaWiki timestamp format which is "%Y%m%d%H%M%S"
             If this parameter is missed, all edits are checked but this is
             restricted to the last 100 edits.

-summary:    Lets you pick a custom edit summary.  Use quotes if edit summary
             contains spaces.

-always      Don't bother asking to confirm any of the changes, Just Do It.

-category:   Appends the given category to every page that is edited.  This is
             useful when a category is being broken out from a template
             parameter or when templates are being upmerged but more information
             must be preserved.

other:       First argument is the old template name, second one is the new
             name.

             If you want to address a template which has spaces, put quotation
             marks around it, or use underscores.

Examples:

If you have a template called [[Template:Cities in Washington]] and want to
change it to [[Template:Cities in Washington state]], start

    python template.py "Cities in Washington" "Cities in Washington state"

Move the page [[Template:Cities in Washington]] manually afterwards.


If you have a template called [[Template:test]] and want to substitute it only
on pages in the User: and User talk: namespaces, do:

    python template.py test -subst -namespace:2 -namespace:3

Note that -namespace: is a global Pywikibot parameter


This next example substitutes the template lived with a supplied edit summary.
It only performs substitutions in main article namespace and doesn't prompt to
start replacing. Note that -putthrottle: is a global Pywikibot parameter.

    python template.py -putthrottle:30 -namespace:0 lived -subst -always
        -summary:"BOT: Substituting {{lived}}, see [[WP:SUBST]]."


This next example removes the templates {{cfr}}, {{cfru}}, and {{cfr-speedy}}
from five category pages as given:

    python template.py cfr cfru cfr-speedy -remove -always
        -page:"Category:Mountain monuments and memorials" -page:"Category:Indian family names"
        -page:"Category:Tennis tournaments in Belgium" -page:"Category:Tennis tournaments in Germany"
        -page:"Category:Episcopal cathedrals in the United States"
        -summary:"Removing Cfd templates from category pages that survived."


This next example substitutes templates test1, test2, and space test on all
pages:

    python template.py test1 test2 "space test" -subst -always

"""
#
# (C) Daniel Herding, 2004
# (C) Rob W.W. Hooft, 2003-2005
# (C) xqt, 2009-2014
# (C) Pywikibot team, 2004-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re
import pywikibot
from pywikibot import i18n, pagegenerators, xmlreader, Bot
from scripts import replace


def UserEditFilterGenerator(generator, username, timestamp=None, skip=False):
    """
    Generator which will yield Pages modified by username.

    It only looks at the last 100 editors.
    If timestamp is set in MediaWiki format JJJJMMDDhhmmss, older edits are
    ignored
    If skip is set, pages edited by the given user are ignored otherwise only
    pages edited by this user are given back

    """
    if timestamp:
        ts = pywikibot.Timestamp.fromtimestampformat(timestamp)
    for page in generator:
        editors = page.getLatestEditors(limit=100)
        found = False
        for ed in editors:
            uts = pywikibot.Timestamp.fromISOformat(ed['timestamp'])
            if not timestamp or uts >= ts:
                if username == ed['user']:
                    found = True
                    break
            else:
                break
        if found and not skip or not found and skip:
            yield page
        else:
            pywikibot.output(u'Skipping %s' % page.title(asLink=True))


class XmlDumpTemplatePageGenerator:

    """
    Generator which yield Pages that transclude a template.

    These pages will be retrieved from a local XML dump file
    (cur table), and may not still transclude the template.
    """

    def __init__(self, templates, xmlfilename):
        """
        Constructor.

        Arguments:
            * templateNames - A list of Page object representing the searched
                              templates
            * xmlfilename   - The dump's path, either absolute or relative

        """
        self.templates = templates
        self.xmlfilename = xmlfilename

    def __iter__(self):
        """Yield page objects until the entire XML dump has been read."""
        mysite = pywikibot.Site()
        dump = xmlreader.XmlDump(self.xmlfilename)
        # regular expression to find the original template.
        # {{vfd}} does the same thing as {{Vfd}}, so both will be found.
        # The old syntax, {{msg:vfd}}, will also be found.
        # TODO: check site.nocapitalize()
        templatePatterns = []
        for template in self.templates:
            templatePattern = template.title(withNamespace=False)
            if not pywikibot.Site().nocapitalize:
                templatePattern = '[%s%s]%s' % (templatePattern[0].upper(),
                                                templatePattern[0].lower(),
                                                templatePattern[1:])
            templatePattern = re.sub(' ', '[_ ]', templatePattern)
            templatePatterns.append(templatePattern)
        templateRegex = re.compile(
            r'\{\{ *([mM][sS][gG]:)?(?:%s) *(?P<parameters>\|[^}]+|) *}}'
            % '|'.join(templatePatterns))
        for entry in dump.parse():
            if templateRegex.search(entry.text):
                page = pywikibot.Page(mysite, entry.title)
                yield page


class TemplateRobot(Bot):

    """This bot will replace, remove or subst all occurences of a template."""

    def __init__(self, generator, templates, **kwargs):
        """
        Constructor.

        @param generator: the pages to work on
        @type  generator: iterable
        @param replacements: a dictionary which maps old template names to
            their replacements. If remove or subst is True, it maps the
            names of the templates that should be removed/resolved to None.
        @type  replacements: dict
        """
        self.availableOptions.update({
            'subst': False,
            'remove': False,
            'summary': None,
            'addedCat': None,
        })
        super(TemplateRobot, self).__init__(**kwargs)

        self.generator = generator
        self.templates = templates
        site = pywikibot.Site()
        if self.getOption('addedCat'):
            self.options['addedCat'] = pywikibot.Category(site, self.getOption('addedCat'))

        comma = site.mediawiki_message('comma-separator')

        # get edit summary message if it's empty
        if not self.getOption('summary'):
            params = {'list': comma.join(self.templates.keys()),
                      'num': len(self.templates)}
            if self.getOption('remove'):
                self.options['summary'] = i18n.twntranslate(
                    site, 'template-removing', params)
            elif self.getOption('subst'):
                self.options['summary'] = i18n.twntranslate(
                    site, 'template-substituting', params)
            else:
                self.options['summary'] = i18n.twntranslate(
                    site, 'template-changing', params)

    def run(self):
        """Start the robot's action."""
        # regular expression to find the original template.
        # {{vfd}} does the same thing as {{Vfd}}, so both will be found.
        # The old syntax, {{msg:vfd}}, will also be found.
        # The group 'parameters' will either match the parameters, or an
        # empty string if there are none.

        replacements = []
        exceptions = {}
        site = pywikibot.Site()
        for old, new in self.templates.items():
            namespaces = list(site.namespace(10, all=True))
            if not site.nocapitalize:
                pattern = '[' + \
                          re.escape(old[0].upper()) + \
                          re.escape(old[0].lower()) + \
                          ']' + re.escape(old[1:])
            else:
                pattern = re.escape(old)
            pattern = re.sub(r'_|\\ ', r'[_ ]', pattern)
            templateRegex = re.compile(r'\{\{ *(' + ':|'.join(namespaces) +
                                       r':|[mM][sS][gG]:)?' + pattern +
                                       r'(?P<parameters>\s*\|.+?|) *}}',
                                       re.DOTALL)

            if self.getOption('subst') and self.getOption('remove'):
                replacements.append((templateRegex,
                                     '{{subst:%s\g<parameters>}}' % new))
                exceptions['inside-tags'] = ['ref', 'gallery']
            elif self.getOption('subst'):
                replacements.append((templateRegex,
                                     '{{subst:%s\g<parameters>}}' % old))
                exceptions['inside-tags'] = ['ref', 'gallery']
            elif self.getOption('remove'):
                replacements.append((templateRegex, ''))
            else:
                template = pywikibot.Page(site, new, ns=10)
                if not template.exists():
                    pywikibot.warning(u'Template "%s" does not exist.' % new)
                    choice = pywikibot.inputChoice(
                        u'Do you want to proceed anyway?',
                        ['Yes', 'No'], ['y', 'N'], 'N')
                    if choice == 'n':
                        continue
                replacements.append((templateRegex,
                                     '{{%s\g<parameters>}}' % new))

        replaceBot = replace.ReplaceRobot(self.generator, replacements,
                                          exceptions, acceptall=self.getOption('always'),
                                          addedCat=self.getOption('addedCat'),
                                          summary=self.getOption('summary'))
        replaceBot.run()


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
        elif arg.startswith('-category:'):
            options['addedCat'] = arg[len('-category:'):]
        elif arg.startswith('-summary:'):
            options['summary'] = arg[len('-summary:'):]
        elif arg.startswith('-user:'):
            user = arg[len('-user:'):]
        elif arg.startswith('-skipuser:'):
            user = arg[len('-skipuser:'):]
            skip = True
        elif arg.startswith('-timestamp:'):
            timestamp = arg[len('-timestamp:'):]
        else:
            if not genFactory.handleArg(arg):
                templateNames.append(
                    pywikibot.Page(pywikibot.Site(), arg,
                                   ns=10
                                   ).title(withNamespace=False))

    if not templateNames:
        pywikibot.showHelp()
        return

    if options.get('subst', False) ^ options.get('remove', False):
        for templateName in templateNames:
            templates[templateName] = None
    else:
        try:
            for i in range(0, len(templateNames), 2):
                templates[templateNames[i]] = templateNames[i + 1]
        except IndexError:
            pywikibot.output(
u'Unless using solely -subst or -remove, you must give an even number of template names.')
            return

    oldTemplates = []
    for templateName in templates.keys():
        oldTemplate = pywikibot.Page(pywikibot.Site(), templateName,
                                     ns=10)
        oldTemplates.append(oldTemplate)

    if xmlfilename:
        gen = XmlDumpTemplatePageGenerator(oldTemplates, xmlfilename)
    else:
        gen = genFactory.getCombinedGenerator()
    if not gen:
        gens = [
            pagegenerators.ReferringPageGenerator(t, onlyTemplateInclusion=True)
            for t in oldTemplates
        ]
        gen = pagegenerators.CombinedPageGenerator(gens)
        gen = pagegenerators.DuplicateFilterPageGenerator(gen)
    if user:
        gen = UserEditFilterGenerator(gen, user, timestamp, skip)

    if not genFactory.gens:
        # make sure that proper namespace filtering etc. is handled
        gen = genFactory.getCombinedGenerator(gen)

    preloadingGen = pagegenerators.PreloadingGenerator(gen)

    bot = TemplateRobot(preloadingGen, templates, **options)
    bot.run()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pywikibot.error("Fatal error:", exc_info=True)
