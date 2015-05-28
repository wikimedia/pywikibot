#!/usr/bin/python
# -*- coding: utf-8 -*-
u"""
Script to help a human solve disambiguations by presenting a set of options.

Specify the disambiguation page on the command line.

The program will pick up the page, and look for all alternative links,
and show them with a number adjacent to them.  It will then automatically
loop over all pages referring to the disambiguation page,
and show 30 characters of context on each side of the reference to help you
make the decision between the alternatives.  It will ask you to type the
number of the appropriate replacement, and perform the change.

It is possible to choose to replace only the link (just type the number) or
replace both link and link-text (type 'r' followed by the number).

Multiple references in one page will be scanned in order, but typing 'n'
(next) on any one of them will leave the complete page unchanged. To leave
only some reference unchanged, use the 's' (skip) option.

Command line options:

   -pos:XXXX   adds XXXX as an alternative disambiguation

   -just       only use the alternatives given on the command line, do not
               read the page for other possibilities

   -dnskip     Skip links already marked with a disambiguation-needed
               template (e.g., {{dn}})

   -primary    "primary topic" disambiguation (Begriffsklärung nach Modell 2).
               That's titles where one topic is much more important, the
               disambiguation page is saved somewhere else, and the important
               topic gets the nice name.

   -primary:XY like the above, but use XY as the only alternative, instead of
               searching for alternatives in [[Keyword (disambiguation)]].
               Note: this is the same as -primary -just -pos:XY

   -file:XYZ   reads a list of pages from a text file. XYZ is the name of the
               file from which the list is taken. If XYZ is not given, the
               user is asked for a filename. Page titles should be inside
               [[double brackets]]. The -pos parameter won't work if -file
               is used.

   -always:XY  instead of asking the user what to do, always perform the same
               action. For example, XY can be "r0", "u" or "2". Be careful with
               this option, and check the changes made by the bot. Note that
               some choices for XY don't make sense and will result in a loop,
               e.g. "l" or "m".

   -main       only check pages in the main namespace, not in the talk,
               wikipedia, user, etc. namespaces.

   -start:XY   goes through all disambiguation pages in the category on your
               wiki that is defined (to the bot) as the category containing
               disambiguation pages, starting at XY. If only '-start' or
               '-start:' is given, it starts at the beginning.

   -min:XX     (XX being a number) only work on disambiguation pages for which
               at least XX are to be worked on.

To complete a move of a page, one can use:

    python solve_disambiguation.py -just -pos:New_Name Old_Name

"""
#
# (C) Rob W.W. Hooft, 2003
# (C) Daniel Herding, 2004
# (C) Andre Engels, 2003-2004
# (C) WikiWichtel, 2004
# (C) Pywikibot team, 2003-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import codecs
import itertools
import re

import pywikibot
from pywikibot import editor as editarticle
from pywikibot.tools import concat_options, first_lower, first_upper as firstcap
from pywikibot import pagegenerators, config, i18n
from pywikibot.bot import Bot, QuitKeyboardInterrupt

# Disambiguation Needed template
dn_template = {
    'en': u'{{dn}}',
    'fr': u'{{Lien vers un homonyme}}',
}

# disambiguation page name format for "primary topic" disambiguations
# (Begriffsklärungen nach Modell 2)
primary_topic_format = {
    'ar': u'%s_(توضيح)',
    'ca': u'%s_(desambiguació)',
    'cs': u'%s_(rozcestník)',
    'de': u'%s_(Begriffsklärung)',
    'en': u'%s_(disambiguation)',
    'fa': u'%s_(ابهام‌زدایی)',
    'fi': u'%s_(täsmennyssivu)',
    'hu': u'%s_(egyértelműsítő lap)',
    'ia': u'%s_(disambiguation)',
    'it': u'%s_(disambigua)',
    'lt': u'%s_(reikšmės)',
    'kk': u'%s_(айрық)',
    'ko': u'%s_(동음이의)',
    'nl': u'%s_(doorverwijspagina)',
    'no': u'%s_(peker)',
    'pl': u'%s_(ujednoznacznienie)',
    'pt': u'%s_(desambiguação)',
    'pfl': u'%s_BKL',
    'he': u'%s_(פירושונים)',
    'ru': u'%s_(значения)',
    'sr': u'%s_(вишезначна одредница)',
    'sv': u'%s_(olika betydelser)',
    'uk': u'%s_(значення)',
}

# List pages that will be ignored if they got a link to a disambiguation
# page. An example is a page listing disambiguations articles.
# Special chars should be encoded with unicode (\x##) and space used
# instead of _

ignore_title = {
    'wikipedia': {
        'ar': [
            u'تصنيف:صفحات توضيح',
        ],
        'ca': [
            u'Viquipèdia:Enllaços incorrectes a pàgines de desambiguació',
            u'Viquipèdia:Registre de pàgines de desambiguació òrfenes',
            u'.*Discussió:.+',
            u'.*Usuari:.+',
            u'.+/[aA]rxiu.*',
        ],
        'cs': [
            u'Wikipedie:Chybějící interwiki/.+',
            u'Wikipedie:Rozcestníky',
            u'Wikipedie diskuse:Rozcestníky',
            u'Wikipedie:Seznam nejvíce odkazovaných rozcestníků',
            u'Wikipedie:Seznam rozcestníků/první typ',
            u'Wikipedie:Seznam rozcestníků/druhý typ',
            u'Wikipedista:Zirland/okres',
        ],
        'da': [
            u'Wikipedia:Links til sider med flertydige titler'
        ],
        'de': [
            u'.+/[aA]rchiv.*',
            u'.+/Baustelle.*',
            u'.+/Index',
            u'.+/Spielwiese',
            u'.+/[tT]est.*',
            u'.*Diskussion:.+',
            u'Benutzer:.+/[Ll]og.*',
            u'Benutzer:C.Löser/.+',
            u'Benutzer:Katharina/Begriffsklärungen',
            u'Benutzer:Kirschblut/.+buchstabenkürzel',
            u'Benutzer:Mathias Schindler/.+',
            u'Benutzer:Noisper/Dingliste/[A-Z]',
            u'Benutzer:Professor Einstein.*',
            u'Benutzer:Sebbot/.+',
            u'Benutzer:SirJective/.+',
            u'Benutzer:Srbauer.*',
            u'Benutzer:SteEis.',
            u'Benutzer:Steindy.*',
            u'Benutzer:SrbBot.*',
            u'Benutzer:PortalBot/.+',
            u'Benutzer:Xqbot/.+',
            u'Lehnwort',
            u'Liste griechischer Wortstämme in deutschen Fremdwörtern',
            u'Liste von Gräzismen',
            u'Portal:Abkürzungen/.+',
            u'Portal:Astronomie/Moves',
            u'Portal:Astronomie/Index/.+',
            u'Portal:Hund',
            u'Portal:Hund/Beobachtungsliste',
            u'Portal:Marxismus',
            u'Portal:Täuferbewegung/Seitenindex',
            u'Wikipedia:Administratoren/Anfragen',
            u'Wikipedia:Archiv/.+',
            u'Wikipedia:Artikelwünsche/Ding-Liste/[A-Z]',
            u'Wikipedia:Begriffsklärung.*',
            u'Wikipedia:Bots/.+',
            u'Wikipedia:Interwiki-Konflikte',
            u'Wikipedia:ISBN-Suche',
            u'Wikipedia:Liste mathematischer Themen/BKS',
            u'Wikipedia:Liste mathematischer Themen/Redirects',
            u'Wikipedia:Meinungsbilder/.+',
            u'Wikipedia:Löschkandidaten/.+',
            u'Wikipedia:WikiProjekt Altertumswissenschaft/.+',
            u'Wikipedia:WikiProjekt Verwaiste Seiten/Begriffsklärungen',
            u'Wikipedia:Qualitätssicherung/.+',
            u'Vorlage:Infobox Weltraum',
            u'Vorlage:Navigationsleiste Raumfahrt',
        ],
        'en': [
            u'Wikipedia:Links to disambiguating pages',
            u'Wikipedia:Disambiguation pages with links',
            u'Wikipedia:Multiple-place names \\([A-Z]\\)',
            u'Wikipedia:Non-unique personal name',
            u"User:Jerzy/Disambiguation Pages i've Editted",
            u'User:Gareth Owen/inprogress',
            u'TLAs from [A-Z][A-Z][A-Z] to [A-Z][A-Z][A-Z]',
            u'List of all two-letter combinations',
            u'User:Daniel Quinlan/redirects.+',
            u'User:Oliver Pereira/stuff',
            u'Wikipedia:French Wikipedia language links',
            u'Wikipedia:Polish language links',
            u'Wikipedia:Undisambiguated abbreviations/.+',
            u'List of acronyms and initialisms',
            u'Wikipedia:Usemod article histories',
            u'User:Pizza Puzzle/stuff',
            u'List of generic names of political parties',
            u'Talk:List of initialisms/marked',
            u'Talk:List of initialisms/sorted',
            u'Talk:Programming language',
            u'Talk:SAMPA/To do',
            u"Wikipedia:Outline of Roget's Thesaurus",
            u'User:Wik/Articles',
            u'User:Egil/Sandbox',
            u'Wikipedia talk:Make only links relevant to the context',
            u'Wikipedia:Common words, searching for which is not possible',
        ],
        'fa': [
            u'ویکی‌پدیا:فهرست صفحات ابهام‌زدایی',
        ],
        'fi': [
            u'Wikipedia:Luettelo täsmennyssivuista',
            u'Wikipedia:Luettelo (täsmennyssivuista)',
            u'Wikipedia:Täsmennyssivu',
        ],
        'fr': [
            u'Wikipédia:Liens aux pages d’homonymie',
            u'Wikipédia:Homonymie',
            u'Wikipédia:Homonymie/Homonymes dynastiques',
            u'Wikipédia:Prise de décision, noms des membres de dynasties/liste des dynastiens',
            u'Liste de toutes les combinaisons de deux lettres',
            u'Wikipédia:Log d’upload/.*',
            u'Sigles de trois lettres de [A-Z]AA à [A-Z]ZZ',
            u'Wikipédia:Pages sans interwiki,.'
        ],
        'fy': [
            u'Wikipedy:Fangnet',
        ],
        'hu': [
            # hu:Wikipédia:Kocsmafal (egyéb)#Hol nem kell egyértelműsíteni?
            # 2012-02-08
            u'Wikipédia:(?!Sportműhely/Eddigi cikkeink).*',
            u'.*\\(egyértelműsítő lap\\)$',
            u'.*[Vv]ita:.*',
            u'Szerkesztő:[^/]+$',
        ],
        'ia': [
            u'Categoria:Disambiguation',
            u'Wikipedia:.+',
            u'Usator:.+',
            u'Discussion Usator:.+',
        ],
        'it': [
            u'Aiuto:Disambigua/Disorfanamento',
            u'Discussioni utente:.+',
            u'Utente:Civvì/disorfanamento',
        ],
        'kk': [
            u'Санат:Айрықты бет',
        ],
        'ko': [
            u'위키백과:(동음이의) 문서의 목록',
            u'위키백과:동음이의어 문서의 목록',
        ],
        'lt': [
            u'Wikipedia:Rodomi nukreipiamieji straipsniai',
        ],
        'nl': [
            u"Gebruiker:.*",
            u"Overleg gebruiker:.+[aA]rchief.*",
            u"Overleg gebruiker:Pven",
            u"Portaal:.+[aA]rchief.*",
            u"Wikipedia:Humor en onzin.*",
            u"Wikipedia:Links naar doorverwijspagina's/Winkeldochters.*",
            u"Wikipedia:Project aanmelding bij startpagina's",
            u"Wikipedia:Wikiproject Roemeense gemeenten/Doorverwijspagina's",
            u'Categorie:Doorverwijspagina',
            u'Lijst van Nederlandse namen van pausen',
            u'Overleg Wikipedia:Discussie spelling 2005',
            u'Overleg Wikipedia:Doorverwijspagina',
            u'Overleg Wikipedia:Logboek.*',
            u'Wikipedia:Logboek.*',
            u'Overleg gebruiker:Sybren/test.*',
            u'Overleg gebruiker:([0-9][0-9]?[0-9]?\\.){3}[0-9][0-9]?[0-9]?',
            u'Overleg:Lage Landen (staatkunde)',
            u'Wikipedia:.*[aA]rchief.*',
            u'Wikipedia:Doorverwijspagina',
            u'Wikipedia:Lijst van alle tweeletter-combinaties',
            u'Wikipedia:Onderhoudspagina',
            u'Wikipedia:Ongelijke redirects',
            u'Wikipedia:Protection log',
            u'Wikipedia:Te verwijderen.*',
            u'Wikipedia:Top 1000 van meest bekeken artikelen',
            u'Wikipedia:Wikipedianen met een encyclopedisch artikel',
            u'Wikipedia:Woorden die niet als zoekterm gebruikt kunnen worden',
            u'Overleg gebruiker:Taka(/.*)?',
            u"Wikipedia:Links naar doorverwijspagina's/Artikelen",
        ],
        'pl': [
            u'Wikipedysta:.+',
            u'Dyskusja.+:.+',
        ],
        'pt': [
            u'Usuário:.+',
            u'Usuário Discussão:.+',
            u'Discussão:.+',
            u'Lista de combinações de duas letras',
            u'Wikipedia:Lista de páginas de desambiguação.+',
            u'Wikipedia:Páginas para eliminar/.+',
        ],
        'ru': [
            u'Категория:Disambig',
            u'Википедия:Страницы разрешения неоднозначностей',
            u'Википедия:Вики-уборка/Статьи без языковых ссылок',
            u'Википедия:Страницы с пометкой «(значения)»',
            u'Список общерусских фамилий',
        ],
    },
    'memoryalpha': {
        'en': [
            u'Memory Alpha:Links to disambiguating pages'
        ],
        'de': [
            u'Memory Alpha:Liste der Wortklärungsseiten'
        ],
    },
}


def correctcap(link, text):
    # If text links to a page with title link uncapitalized, uncapitalize link,
    # otherwise capitalize it
    linkupper = link.title()
    linklower = first_lower(linkupper)
    if "[[%s]]" % linklower in text or "[[%s|" % linklower in text:
        return linklower
    else:
        return linkupper


class ReferringPageGeneratorWithIgnore:

    """Referring Page generator, with an ignore manager."""

    def __init__(self, disambPage, primary=False, minimum=0):
        self.disambPage = disambPage
        # if run with the -primary argument, enable the ignore manager
        self.primaryIgnoreManager = PrimaryIgnoreManager(disambPage,
                                                         enabled=primary)
        self.minimum = minimum

    def __iter__(self):
        # TODO: start yielding before all referring pages have been found
        refs = [page for page in
                self.disambPage.getReferences(follow_redirects=False,
                                              withTemplateInclusion=False)]
        pywikibot.output(u"Found %d references." % len(refs))
        # Remove ignorables
        if self.disambPage.site.family.name in ignore_title and \
           self.disambPage.site.lang in ignore_title[self.disambPage.site.family.name]:
            for ig in ignore_title[self.disambPage.site.family.name
                                   ][self.disambPage.site.lang]:
                for i in range(len(refs) - 1, -1, -1):
                    if re.match(ig, refs[i].title()):
                        pywikibot.log(u'Ignoring page %s'
                                      % refs[i].title())
                        del refs[i]
                    elif self.primaryIgnoreManager.isIgnored(refs[i]):
                        del refs[i]
        if len(refs) < self.minimum:
            pywikibot.output(u"Found only %d pages to work on; skipping."
                             % len(refs))
            return
        pywikibot.output(u"Will work on %d pages." % len(refs))
        for ref in refs:
            yield ref


class PrimaryIgnoreManager(object):

    """
    Primary ignore manager.

    If run with the -primary argument, reads from a file which pages should
    not be worked on; these are the ones where the user pressed n last time.
    If run without the -primary argument, doesn't ignore any pages.

    """

    def __init__(self, disambPage, enabled=False):
        self.disambPage = disambPage
        self.enabled = enabled

        self.ignorelist = []
        filename = config.datafilepath(
            'disambiguations',
            self.disambPage.title(as_filename=True) + '.txt')
        try:
            # The file is stored in the disambiguation/ subdir.
            # Create if necessary.
            f = codecs.open(filename, 'r', 'utf-8')
            for line in f.readlines():
                # remove trailing newlines and carriage returns
                while line[-1] in ['\n', '\r']:
                    line = line[:-1]
                # skip empty lines
                if line != '':
                    self.ignorelist.append(line)
            f.close()
        except IOError:
            pass

    def isIgnored(self, refPage):
        return self.enabled and refPage.title(asUrl=True) in self.ignorelist

    def ignore(self, refPage):
        if self.enabled:
            # Skip this occurrence next time.
            filename = config.datafilepath(
                'disambiguations',
                self.disambPage.title(asUrl=True) + '.txt')
            try:
                # Open file for appending. If none exists yet, create a new one.
                f = codecs.open(filename, 'a', 'utf-8')
                f.write(refPage.title(asUrl=True) + '\n')
                f.close()
            except IOError:
                pass


class DisambiguationRobot(Bot):

    """Disambiguation bot."""

    ignore_contents = {
        'de': (u'{{[Ii]nuse}}',
               u'{{[Ll]öschen}}',
               ),
        'fi': (u'{{[Tt]yöstetään}}',
               ),
        'kk': (u'{{[Ii]nuse}}',
               u'{{[Pp]rocessing}}',
               ),
        'nl': (u'{{wiu2}}',
               u'{{nuweg}}',
               ),
        'ru': (u'{{[Ii]nuse}}',
               u'{{[Pp]rocessing}}',
               ),
    }

    primary_redir_template = {
        # Page.templates() format, first letter uppercase
        'hu': u'Egyért-redir',
    }

    def __init__(self, always, alternatives, getAlternatives, dnSkip, generator,
                 primary, main_only, minimum=0):
        super(DisambiguationRobot, self).__init__()
        self.always = always
        self.alternatives = alternatives
        self.getAlternatives = getAlternatives
        self.dnSkip = dnSkip
        self.generator = generator
        self.primary = primary
        self.main_only = main_only
        self.minimum = minimum

        self.mysite = pywikibot.Site()
        self.mylang = self.mysite.language()
        self.comment = None

        self.dn_template_str = i18n.translate(self.mysite, dn_template)

        self.setupRegexes()

    def checkContents(self, text):
        """
        Check if the text matches any of the ignore regexes.

        For a given text, returns False if none of the regular
        expressions given in the dictionary at the top of this class
        matches a substring of the text.
        Otherwise returns the substring which is matched by one of
        the regular expressions.
        """
        for ig in self.ignore_contents_regexes:
            match = ig.search(text)
            if match:
                return match.group()
        return None

    def makeAlternativesUnique(self):
        # remove duplicate entries stable
        unique = set(self.alternatives)
        self.alternatives = [alt for alt in self.alternatives if alt in unique]

    def listAlternatives(self):
        list = u'\n'
        for i in range(len(self.alternatives)):
            list += (u"%3i - %s\n" % (i, self.alternatives[i]))
        pywikibot.output(list)

    def setupRegexes(self):
        # compile regular expressions
        self.ignore_contents_regexes = []
        if self.mylang in self.ignore_contents:
            for ig in self.ignore_contents[self.mylang]:
                self.ignore_contents_regexes.append(re.compile(ig))

        linktrail = self.mysite.linktrail()
        self.trailR = re.compile(linktrail)
        # The regular expression which finds links. Results consist of four
        # groups:
        # group title is the target page title, that is, everything before
        # | or ].
        # group section is the page section. It'll include the # to make life
        # easier for us.
        # group label is the alternative link title, that's everything
        # between | and ].
        # group linktrail is the link trail, that's letters after ]] which
        # are part of the word.
        # note that the definition of 'letter' varies from language to language.
        self.linkR = re.compile(r'''
            \[\[  (?P<title>     [^\[\]\|#]*)
                  (?P<section> \#[^\]\|]*)?
               (\|(?P<label>     [^\]]*))?  \]\]
            (?P<linktrail>%s)''' % linktrail,
                                flags=re.X)

    def treat(self, refPage, disambPage):
        """
        Treat a page.

        Parameters:
            disambPage - The disambiguation page or redirect we don't want
                anything to link to
            refPage - A page linking to disambPage
        Returns False if the user pressed q to completely quit the program.
        Otherwise, returns True.

        """
        # TODO: break this function up into subroutines!

        include = False
        unlink_counter = 0
        new_targets = []
        try:
            text = refPage.get()
            ignoreReason = self.checkContents(text)
            if ignoreReason:
                pywikibot.output('\n\nSkipping %s because it contains %s.\n\n'
                                 % (refPage.title(), ignoreReason))
            else:
                include = True
        except pywikibot.IsRedirectPage:
            pywikibot.output(u'%s is a redirect to %s'
                             % (refPage.title(), disambPage.title()))
            if disambPage.isRedirectPage():
                target = self.alternatives[0]
                if pywikibot.input_yn(u'Do you want to make redirect %s point '
                                      'to %s?' % (refPage.title(), target),
                                      default=False, automatic_quit=False):
                    redir_text = '#%s [[%s]]' \
                                 % (self.mysite.redirect(), target)
                    try:
                        refPage.put_async(redir_text, summary=self.comment)
                    except pywikibot.PageNotSaved as error:
                        pywikibot.output(u'Page not saved: %s' % error.args)
            else:
                choice = pywikibot.input_choice(
                    u'Do you want to work on pages linking to %s?'
                    % refPage.title(),
                    [('yes', 'y'), ('no', 'n'), ('change redirect', 'c')], 'n',
                    automatic_quit=False)
                if choice == 'y':
                    gen = ReferringPageGeneratorWithIgnore(refPage,
                                                           self.primary)
                    preloadingGen = pagegenerators.PreloadingGenerator(gen)
                    for refPage2 in preloadingGen:
                        # run until the user selected 'quit'
                        if not self.treat(refPage2, refPage):
                            break
                elif choice == 'c':
                    text = refPage.get(get_redirect=True)
                    include = "redirect"
        except pywikibot.NoPage:
            pywikibot.output(
                u'Page [[%s]] does not seem to exist?! Skipping.'
                % refPage.title())
            include = False
        if include in (True, "redirect"):
            # make a backup of the original text so we can show the changes later
            original_text = text
            n = 0
            curpos = 0
            dn = False
            edited = False
            # This loop will run until we have finished the current page
            while True:
                m = self.linkR.search(text, pos=curpos)
                if not m:
                    if n == 0:
                        pywikibot.output(u"No changes necessary in %s"
                                         % refPage.title())
                        return True
                    else:
                        # stop loop and save page
                        break
                # Make sure that next time around we will not find this same hit.
                curpos = m.start() + 1
                try:
                    foundlink = pywikibot.Link(m.group('title'),
                                               disambPage.site)
                    foundlink.parse()
                except pywikibot.Error:
                    continue
                # ignore interwiki links
                if foundlink.site != disambPage.site:
                    continue
                # Check whether the link found is to disambPage.
                try:
                    if foundlink.canonical_title() != disambPage.title():
                        continue
                except pywikibot.Error:
                    # must be a broken link
                    pywikibot.log(u"Invalid link [[%s]] in page [[%s]]"
                                  % (m.group('title'), refPage.title()))
                    continue
                n += 1
                # how many bytes should be displayed around the current link
                context = 60
                # check if there's a dn-template here already
                if (self.dnSkip and self.dn_template_str and
                        self.dn_template_str[:-2] in text[m.end():m.end() +
                                                          len(self.dn_template_str) + 8]):
                    continue

                # This loop will run while the user doesn't choose an option
                # that will actually change the page
                while True:
                    self.current_page = refPage

                    if not self.always:
                        # at the beginning of the link, start red color.
                        # at the end of the link, reset the color to default
                        pywikibot.output(
                            text[max(0, m.start() - context):m.start()] +
                            '\03{lightred}' + text[m.start():m.end()] +
                            '\03{default}' + text[m.end():m.end() + context])
                        options = ['#', 'r#', '[s]kip link', '[e]dit page',
                                   '[n]ext page', '[u]nlink', '[q]uit']
                        if self.dn_template_str:
                            options.append(u'[t]ag template %s' % self.dn_template_str)
                        options.append('[m]ore context')
                        if not edited:
                            options.append('show [d]isambiguation page')
                        options += ['[l]ist', '[a]dd new']
                        if edited:
                            options += ['save in this form [x]']
                        options = concat_options('Option', 72, options)
                        choice = pywikibot.input(options)
                    else:
                        choice = self.always
                    if choice in ['a', 'A']:
                        newAlternative = pywikibot.input(u'New alternative:')
                        self.alternatives.append(newAlternative)
                        self.listAlternatives()
                    elif choice in ['e', 'E']:
                        editor = editarticle.TextEditor()
                        newText = editor.edit(text, jumpIndex=m.start(),
                                              highlight=disambPage.title())
                        # if user didn't press Cancel
                        if newText and newText != text:
                            text = newText
                            break
                    elif choice in ['d', 'D']:
                        editor = editarticle.TextEditor()
                        if disambPage.isRedirectPage():
                            disambredir = disambPage.getRedirectTarget()
                            editor.edit(
                                disambredir.get(),
                                jumpIndex=m.start(),
                                highlight=disambredir.title())
                        else:
                            editor.edit(
                                disambPage.get(),
                                jumpIndex=m.start(),
                                highlight=disambPage.title())
                    elif choice in ['l', 'L']:
                        self.listAlternatives()
                    elif choice in ['m', 'M']:
                        # show more text around the link we're working on
                        context *= 2
                    else:
                        break

                if choice in ['e', 'E']:
                    # user has edited the page and then pressed 'OK'
                    edited = True
                    curpos = 0
                    continue
                elif choice in ['n', 'N']:
                    # skip this page
                    if self.primary:
                        # If run with the -primary argument, skip this
                        # occurrence next time.
                        self.primaryIgnoreManager.ignore(refPage)
                    return True
                elif choice in ['q', 'Q']:
                    # quit the program
                    self.quit()
                elif choice in ['s', 'S']:
                    # Next link on this page
                    n -= 1
                    continue
                elif choice in ['x', 'X'] and edited:
                    # Save the page as is
                    break

                # The link looks like this:
                # [[page_title|link_text]]trailing_chars
                page_title = m.group('title')
                link_text = m.group('label')

                if not link_text:
                    # or like this: [[page_title]]trailing_chars
                    link_text = page_title
                if m.group('section') is None:
                    section = ''
                else:
                    section = m.group('section')
                trailing_chars = m.group('linktrail')
                if trailing_chars:
                    link_text += trailing_chars
                # '?', '/' for old choice
                if choice in ['t', 'T', '?', '/'] and self.dn_template_str:
                    # small chunk of text to search
                    search_text = text[m.end():m.end() + context]
                    # figure out where the link (and sentance) ends, put note
                    # there
                    end_of_word_match = re.search(r'\s', search_text)
                    if end_of_word_match:
                        position_split = end_of_word_match.start(0)
                    else:
                        position_split = 0
                    # insert dab needed template
                    text = (text[:m.end() + position_split] +
                            self.dn_template_str +
                            text[m.end() + position_split:])
                    dn = True
                    continue
                elif choice in ['u', 'U']:
                    # unlink - we remove the section if there's any
                    text = text[:m.start()] + link_text + text[m.end():]
                    unlink_counter += 1
                    continue
                else:
                    if len(choice) > 0 and choice[0] == 'r':
                        # we want to throw away the original link text
                        replaceit = link_text == page_title
                        choice = choice[1:]
                    elif include == "redirect":
                        replaceit = True
                    else:
                        replaceit = False

                    try:
                        choice = int(choice)
                    except ValueError:
                        pywikibot.output(u"Unknown option")
                        # step back to ask the user again what to do with the
                        # current link
                        curpos -= 1
                        continue
                    if choice >= len(self.alternatives) or choice < 0:
                        pywikibot.output(
                            u"Choice out of range. Please select a number "
                            u"between 0 and %i." % (len(self.alternatives) - 1))
                        # show list of possible choices
                        self.listAlternatives()
                        # step back to ask the user again what to do with the
                        # current link
                        curpos -= 1
                        continue
                    new_page_title = self.alternatives[choice]
                    repPl = pywikibot.Page(pywikibot.Link(new_page_title,
                                                          disambPage.site))
                    if (new_page_title[0].isupper() or
                            link_text[0].isupper()):
                        new_page_title = repPl.title()
                    else:
                        new_page_title = repPl.title()
                        new_page_title = first_lower(new_page_title)
                    if new_page_title not in new_targets:
                        new_targets.append(new_page_title)
                    if replaceit and trailing_chars:
                        newlink = "[[%s%s]]%s" % (new_page_title,
                                                  section,
                                                  trailing_chars)
                    elif replaceit or (new_page_title == link_text and
                                       not section):
                        newlink = "[[%s]]" % new_page_title
                    # check if we can create a link with trailing characters
                    # instead of a pipelink
                    elif (
                        (len(new_page_title) <= len(link_text)) and
                        (firstcap(link_text[:len(new_page_title)]) == firstcap(new_page_title)) and
                        (re.sub(self.trailR, '', link_text[len(new_page_title):]) == '') and
                        (not section)
                    ):
                        newlink = "[[%s]]%s" \
                                  % (link_text[:len(new_page_title)],
                                     link_text[len(new_page_title):])
                    else:
                        newlink = "[[%s%s|%s]]" \
                                  % (new_page_title, section, link_text)
                    text = text[:m.start()] + newlink + text[m.end():]
                    continue

                pywikibot.output(text[max(0, m.start() - 30):m.end() + 30])
            if text == original_text:
                pywikibot.output(u'\nNo changes have been made:\n')
            else:
                pywikibot.output(u'\nThe following changes have been made:\n')
                pywikibot.showDiff(original_text, text)
                pywikibot.output(u'')
                # save the page
                self.setSummaryMessage(disambPage, new_targets, unlink_counter,
                                       dn)
                try:
                    refPage.put_async(text, summary=self.comment)
                except pywikibot.LockedPage:
                    pywikibot.output(u'Page not saved: page is locked')
                except pywikibot.PageNotSaved as error:
                    pywikibot.output(u'Page not saved: %s' % error.args)
        return True

    def findAlternatives(self, disambPage):
        if disambPage.isRedirectPage() and not self.primary:
            if (disambPage.site.lang in self.primary_redir_template and
                    self.primary_redir_template[disambPage.site.lang]
                    in disambPage.templates(get_redirect=True)):
                baseTerm = disambPage.title()
                for template in disambPage.templatesWithParams(
                        get_redirect=True):
                    if template[0] == self.primary_redir_template[
                        disambPage.site.lang] \
                            and len(template[1]) > 0:
                        baseTerm = template[1][1]
                disambTitle = primary_topic_format[self.mylang] % baseTerm
                try:
                    disambPage2 = pywikibot.Page(
                        pywikibot.Link(disambTitle, self.mysite))
                    links = disambPage2.linkedPages()
                    links = [correctcap(l, disambPage2.get()) for l in links]
                except pywikibot.NoPage:
                    pywikibot.output(u"No page at %s, using redirect target."
                                     % disambTitle)
                    links = disambPage.linkedPages()[:1]
                    links = [correctcap(l, disambPage.get(get_redirect=True))
                             for l in links]
                self.alternatives += links
            else:
                try:
                    target = disambPage.getRedirectTarget().title()
                    self.alternatives.append(target)
                except pywikibot.NoPage:
                    pywikibot.output(u"The specified page was not found.")
                    user_input = pywikibot.input(u"""\
Please enter the name of the page where the redirect should have pointed at,
or press enter to quit:""")
                    if user_input == "":
                        self.quit()
                    else:
                        self.alternatives.append(user_input)
                except pywikibot.IsNotRedirectPage:
                    pywikibot.output(
                        u"The specified page is not a redirect. Skipping.")
                    return False
        elif self.getAlternatives:
            try:
                if self.primary:
                    try:
                        disambPage2 = pywikibot.Page(
                            pywikibot.Link(
                                primary_topic_format[self.mylang]
                                % disambPage.title(),
                                self.mysite))
                        links = disambPage2.linkedPages()
                        links = [correctcap(l, disambPage2.get())
                                 for l in links]
                    except pywikibot.NoPage:
                        pywikibot.output(
u"Page does not exist, using the first link in page %s."
                            % disambPage.title())
                        links = disambPage.linkedPages()[:1]
                        links = [correctcap(l, disambPage.get())
                                 for l in links]
                else:
                    try:
                        links = disambPage.linkedPages()
                        links = [correctcap(l, disambPage.get())
                                 for l in links]
                    except pywikibot.NoPage:
                        pywikibot.output(u"Page does not exist, skipping.")
                        return False
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"Page is a redirect, skipping.")
                return False
            self.alternatives += links
        return True

    def setSummaryMessage(self, disambPage, new_targets=[], unlink_counter=0,
                          dn=False):
        # make list of new targets
        comma = self.mysite.mediawiki_message(u"comma-separator")
        targets = comma.join(u'[[%s]]' % page_title
                             for page_title in new_targets)

        if not targets:
            targets = i18n.twtranslate(self.mysite,
                                       'solve_disambiguation-unknown-page')

        # first check whether user has customized the edit comment
        if (self.mysite.family.name in config.disambiguation_comment and
                self.mylang in config.disambiguation_comment[self.mysite.family.name]):
            try:
                self.comment = i18n.translate(
                    self.mysite,
                    config.disambiguation_comment[self.mysite.family.name],
                    fallback=True) % (disambPage.title(), targets)

            # Backwards compatibility, type error probably caused by too
            # many arguments for format string
            except TypeError:
                self.comment = i18n.translate(
                    self.mysite,
                    config.disambiguation_comment[self.mysite.family.name],
                    fallback=True) % disambPage.title()
        elif disambPage.isRedirectPage():
            # when working on redirects, there's another summary message
            if unlink_counter and not new_targets:
                self.comment = i18n.twtranslate(
                    self.mysite,
                    'solve_disambiguation-redirect-removed',
                    {'from': disambPage.title(),
                     'count': unlink_counter})
            elif dn and not new_targets:
                self.comment = i18n.twtranslate(
                    self.mysite,
                    'solve_disambiguation-redirect-adding-dn-template',
                    {'from': disambPage.title()})
            else:
                self.comment = i18n.twtranslate(
                    self.mysite, 'solve_disambiguation-redirect-resolved',
                    {'from': disambPage.title(),
                     'to': targets,
                     'count': len(new_targets)})
        else:
            if unlink_counter and not new_targets:
                self.comment = i18n.twtranslate(
                    self.mysite, 'solve_disambiguation-links-removed',
                    {'from': disambPage.title(),
                     'count': unlink_counter})
            elif dn and not new_targets:
                self.comment = i18n.twtranslate(
                    self.mysite, 'solve_disambiguation-adding-dn-template',
                    {'from': disambPage.title()})
            else:
                self.comment = i18n.twtranslate(
                    self.mysite, 'solve_disambiguation-links-resolved',
                    {'from': disambPage.title(),
                     'to': targets,
                     'count': len(new_targets)})

    def run(self):
        if self.main_only:
            if self.mysite.family.name not in ignore_title:
                ignore_title[self.mysite.family.name] = {}
            if self.mylang not in ignore_title[self.mysite.family.name]:
                ignore_title[self.mysite.family.name][self.mylang] = []

            ignore_title[self.mysite.family.name][self.mylang] += [
                '%s:' % ns for ns in itertools.chain(self.mysite.namespaces)]

        for disambPage in self.generator:
            self.primaryIgnoreManager = PrimaryIgnoreManager(
                disambPage, enabled=self.primary)

            if not self.findAlternatives(disambPage):
                continue

            pywikibot.output('\nAlternatives for %s' % disambPage)
            self.makeAlternativesUnique()
            # sort possible choices
            if config.sort_ignore_case:
                self.alternatives.sort(key=lambda x: x.lower())
            else:
                self.alternatives.sort()
            self.listAlternatives()

            gen = ReferringPageGeneratorWithIgnore(disambPage, self.primary,
                                                   minimum=self.minimum)
            preloadingGen = pagegenerators.PreloadingGenerator(gen)
            for refPage in preloadingGen:
                if not self.primaryIgnoreManager.isIgnored(refPage):
                    try:
                        self.treat(refPage, disambPage)
                    except QuitKeyboardInterrupt:
                        pywikibot.output('\nUser quit %s bot run...' %
                                         self.__class__.__name__)
                        return

            # clear alternatives before working on next disambiguation page
            self.alternatives = []


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # the option that's always selected when the bot wonders what to do with
    # a link. If it's None, the user is prompted (default behaviour).
    always = None
    alternatives = []
    getAlternatives = True
    dnSkip = False
    generator = None
    pageTitle = None
    primary = False
    main_only = False

    # For sorting the linked pages, case can be ignored
    minimum = 0

    local_args = pywikibot.handle_args(args)

    for arg in local_args:
        if arg.startswith('-primary:'):
            primary = True
            getAlternatives = False
            alternatives.append(arg[9:])
        elif arg == '-primary':
            primary = True
        elif arg.startswith('-always:'):
            always = arg[8:]
        elif arg.startswith('-file'):
            if len(arg) == 5:
                generator = pagegenerators.TextfilePageGenerator(
                    filename=None)
            else:
                generator = pagegenerators.TextfilePageGenerator(
                    filename=arg[6:])
        elif arg.startswith('-pos:'):
            if arg[5] != ':':
                mysite = pywikibot.Site()
                page = pywikibot.Page(pywikibot.Link(arg[5:], mysite))
                if page.exists():
                    alternatives.append(page.title())
                else:
                    if pywikibot.input_yn(
                            u'Possibility %s does not actually exist. Use it '
                            'anyway?' % page.title(),
                            default=False, automatic_quit=False):
                        alternatives.append(page.title())
            else:
                alternatives.append(arg[5:])
        elif arg == '-just':
            getAlternatives = False
        elif arg == '-dnskip':
            dnSkip = True
        elif arg == '-main':
            main_only = True
        elif arg.startswith('-min:'):
            minimum = int(arg[5:])
        elif arg.startswith('-start'):
            try:
                generator = pagegenerators.CategorizedPageGenerator(
                    pywikibot.Site().disambcategory(),
                    start=arg[7:], namespaces=[0])
            except pywikibot.NoPage:
                pywikibot.output("Disambiguation category for your wiki is not known.")
                raise
        elif not pageTitle:
            pageTitle = arg

    site = pywikibot.Site()

    if pageTitle:
        page = pywikibot.Page(pywikibot.Link(pageTitle, site))
        generator = iter([page])

    if not generator:
        pywikibot.showHelp()
        return

    site.login()

    bot = DisambiguationRobot(always, alternatives, getAlternatives, dnSkip,
                              generator, primary, main_only,
                              minimum=minimum)
    bot.run()


if __name__ == "__main__":
    main()
