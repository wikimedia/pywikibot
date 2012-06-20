# -*- coding: utf-8 -*-
"""
Very simple script to replace a template with another one,
and to convert the old MediaWiki boilerplate format to the new template format.

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
             (http://download.wikimedia.org). If this argument isn\'t given,
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

Note that -namespace: is a global pywikipedia parameter


This next example substitutes the template lived with a supplied edit summary.
It only performs substitutions in main article namespace and doesn't prompt to
start replacing. Note that -putthrottle: is a global pywikipedia parameter.

    python template.py -putthrottle:30 -namespace:0 lived -subst -always
        -summary:"ROBOT: Substituting {{lived}}, see [[WP:SUBST]]."


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
# (C) Rob W.W. Hooft, 2003
# (C) xqt, 2009-2011
# (C) Pywikipedia team, 2004-2010
#
# Distributed under the terms of the MIT license.
#
__version__='$Id$'
#
import re, sys, string
import pywikibot
from pywikibot import i18n
from pywikibot import config, pagegenerators, catlib
from scripts import replace

def UserEditFilterGenerator(generator, username, timestamp=None, skip=False):
    """
    Generator which will yield Pages depending of user:username is an Author of
    that page (only looks at the last 100 editors).
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
            if not timestamp or uts>=ts:
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
    Generator which will yield Pages to pages that might contain the chosen
    template. These pages will be retrieved from a local XML dump file
    (cur table).
    """
    def __init__(self, templates, xmlfilename):
        """
        Arguments:
            * templateNames - A list of Page object representing the searched
                              templates
            * xmlfilename   - The dump's path, either absolute or relative
        """
        raise NotImplementedError("Sorry, no XML reader in rewrite yet.")
        self.templates = templates
        self.xmlfilename = xmlfilename

    def __iter__(self):
        """Yield page objects until the entire XML dump has been read."""
        from pywikibot import xmlreader
        mysite = pywikibot.getSite()
        dump = xmlreader.XmlDump(self.xmlfilename)
        # regular expression to find the original template.
        # {{vfd}} does the same thing as {{Vfd}}, so both will be found.
        # The old syntax, {{msg:vfd}}, will also be found.
        # TODO: check site.nocapitalize()
        templatePatterns = []
        for template in self.templates:
            templatePattern = template.titleWithoutNamespace()
            if not pywikibot.getSite().nocapitalize:
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


class TemplateRobot:
    """
    This robot will load all pages yielded by a page generator and replace or
    remove all occurences of the old template, or substitute them with the
    template's text.
    """
    def __init__(self, generator, templates, subst = False, remove = False,
                 editSummary = '', acceptAll = False, addedCat = None):
        """
        Arguments:
            * generator    - A page generator.
            * replacements - A dictionary which maps old template names to
                             their replacements. If remove or subst is True,
                             it maps the names of the templates that should be
                             removed/resolved to None.
            * remove       - True if the template should be removed.
            * subst        - True if the template should be resolved.
        """
        self.generator = generator
        self.templates = templates
        self.subst = subst
        self.remove = remove
        self.editSummary = editSummary
        self.acceptAll = acceptAll
        self.addedCat = addedCat
        site = pywikibot.Site()
        if self.addedCat:
            self.addedCat = pywikibot.Category(
                site, u'%s:%s' % (site.namespace(14), self.addedCat))

        # get edit summary message if it's empty
        if (self.editSummary==''):
            Param = {'list': (', ').join(self.templates.keys()),
                     'num' : len(self.templates)}
            if self.remove:
                self.editSummary = i18n.twntranslate(
                    site, 'template-removing', Param)
            elif self.subst:
                self.editSummary = i18n.twntranslate(
                    site, 'template-substituting', Param)
            else:
                self.editSummary = i18n.twntranslate(
                    site, 'template-changing', Param)

    def run(self):
        """
        Starts the robot's action.
        """
        # regular expression to find the original template.
        # {{vfd}} does the same thing as {{Vfd}}, so both will be found.
        # The old syntax, {{msg:vfd}}, will also be found.
        # The group 'parameters' will either match the parameters, or an
        # empty string if there are none.

        replacements = []
        exceptions = {}
        site = pywikibot.getSite()
        for old, new in self.templates.iteritems():
            namespaces = list(site.namespace(10, all=True))
            if not site.nocapitalize:
                pattern = '[' + \
                          re.escape(old[0].upper()) + \
                          re.escape(old[0].lower()) + \
                          ']' + re.escape(old[1:])
            else:
                pattern = re.escape(old)
            pattern = re.sub(r'_|\\ ', r'[_ ]', pattern)
            templateRegex = re.compile(r'\{\{ *(' + ':|'.join(namespaces) + \
                                       r':|[mM][sS][gG]:)?' + pattern + \
                                       r'(?P<parameters>\s*\|.+?|) *}}',
                                       re.DOTALL)

            if self.subst and self.remove:
                replacements.append((templateRegex,
                                     '{{subst:%s\g<parameters>}}' % new))
                exceptions['inside-tags']=['ref', 'gallery']
            elif self.subst:
                replacements.append((templateRegex,
                                     '{{subst:%s\g<parameters>}}' % old))
                exceptions['inside-tags']=['ref', 'gallery']
            elif self.remove:
                replacements.append((templateRegex, ''))
            else:
                replacements.append((templateRegex,
                                     '{{%s\g<parameters>}}' % new))

        replaceBot = replace.ReplaceRobot(self.generator, replacements,
                                          exceptions, acceptall=self.acceptAll,
                                          addedCat=self.addedCat,
                                          editSummary=self.editSummary)
        replaceBot.run()

def main(*args):
    templateNames = []
    templates = {}
    subst = False
    remove = False
    namespaces = []
    editSummary = ''
    addedCat = ''
    acceptAll = False
    genFactory = pagegenerators.GeneratorFactory()
    # If xmlfilename is None, references will be loaded from the live wiki.
    xmlfilename = None
    user = None
    skip = False
    timestamp = None
    # read command line parameters
    for arg in pywikibot.handleArgs(*args):
        if arg == '-remove':
            remove = True
        elif arg == '-subst':
            subst = True
        elif arg == '-assubst':
            subst = remove = True
        elif arg == ('-always'):
            acceptAll = True
        elif arg.startswith('-xml'):
            if len(arg) == 4:
                xmlfilename = pywikibot.input(
                    u'Please enter the XML dump\'s filename: ')
            else:
                xmlfilename = arg[5:]
        elif arg.startswith('-category:'):
            addedCat = arg[len('-category:'):]
        elif arg.startswith('-summary:'):
            editSummary = arg[len('-summary:'):]
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
                                   ns=10).title(withNamespace=False))

    if subst ^ remove:
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
    ns = pywikibot.Site().template_namespace()
    for templateName in templates.keys():
        oldTemplate = pywikibot.Page(pywikibot.Site(), templateName, ns=10)
        oldTemplates.append(oldTemplate)

    if xmlfilename:
        gen = XmlDumpTemplatePageGenerator(oldTemplates, xmlfilename)
    else:
        gen = genFactory.getCombinedGenerator()
    if not gen:
        gens = []
        gens = [pagegenerators.ReferringPageGenerator(
                    t, onlyTemplateInclusion=True) for t in oldTemplates]
        gen = pagegenerators.CombinedPageGenerator(gens)
        gen = pagegenerators.DuplicateFilterPageGenerator(gen)

    if user:
        gen = UserEditFilterGenerator(gen, user, timestamp, skip)
    preloadingGen = pagegenerators.PreloadingGenerator(gen)

    bot = TemplateRobot(preloadingGen, templates, subst, remove, editSummary,
                        acceptAll, addedCat)
    bot.run()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pywikibot.error("Fatal error:", exc_info=True)
    finally:
        pywikibot.stopme()
