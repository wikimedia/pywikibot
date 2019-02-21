#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to help a human solve disambiguations by presenting a set of options.

Specify the disambiguation page on the command line.

The program will pick up the page, and look for all alternative links,
and show them with a number adjacent to them. It will then automatically
loop over all pages referring to the disambiguation page,
and show 30 characters of context on each side of the reference to help you
make the decision between the alternatives. It will ask you to type the
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

   -first      Uses only the first link of every line on the disambiguation
               page that begins with an asterisk. Useful if the page is full
               of irrelevant links that are not subject to disambiguation.
               You won't get all af them as options, just the first on each
               line. For a moderated example see
               http://en.wikipedia.org/wiki/Szerdahely
               A really exotic one is
               http://hu.wikipedia.org/wiki/Brabant_(egyértelműsítő lap)

   -start:XY   goes through all disambiguation pages in the category on your
               wiki that is defined (to the bot) as the category containing
               disambiguation pages, starting at XY. If only '-start' or
               '-start:' is given, it starts at the beginning.

   -min:XX     (XX being a number) only work on disambiguation pages for which
               at least XX are to be worked on.

To complete a move of a page, one can use:

    python pwb.py solve_disambiguation -just -pos:New_Name Old_Name

"""
#
# (C) Rob W.W. Hooft, 2003
# (C) Daniel Herding, 2004
# (C) Andre Engels, 2003-2004
# (C) WikiWichtel, 2004
# (C) Pywikibot team, 2003-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import codecs
from itertools import chain
import os
import re

import pywikibot
from pywikibot import editor as editarticle
from pywikibot.tools import first_lower, first_upper as firstcap
from pywikibot import pagegenerators, config, i18n
from pywikibot.bot import (
    SingleSiteBot,
    StandardOption, HighlightContextOption, ListOption, OutputProxyOption,
)
from pywikibot.tools.formatter import SequenceOutputter

# Disambiguation Needed template
dn_template = {
    'en': '{{dn}}',
    'fr': '{{Lien vers un homonyme}}',
}

# disambiguation page name format for "primary topic" disambiguations
# (Begriffsklärungen nach Modell 2)
primary_topic_format = {
    'ar': '%s_(توضيح)',
    'ca': '%s_(desambiguació)',
    'cs': '%s_(rozcestník)',
    'de': '%s_(Begriffsklärung)',
    'en': '%s_(disambiguation)',
    'fa': '%s_(ابهام‌زدایی)',
    'fi': '%s_(täsmennyssivu)',
    'hu': '%s_(egyértelműsítő lap)',
    'ia': '%s_(disambiguation)',
    'it': '%s_(disambigua)',
    'lt': '%s_(reikšmės)',
    'kk': '%s_(айрық)',
    'ko': '%s_(동음이의)',
    'nl': '%s_(doorverwijspagina)',
    'no': '%s_(peker)',
    'pl': '%s_(ujednoznacznienie)',
    'pt': '%s_(desambiguação)',
    'pfl': '%s_BKL',
    'he': '%s_(פירושונים)',
    'ru': '%s_(значения)',
    'sr': '%s_(вишезначна одредница)',
    'sv': '%s_(olika betydelser)',
    'uk': '%s_(значення)',
    'ur': '%s_(ضد ابہام)',
}

# List pages that will be ignored if they got a link to a disambiguation
# page. An example is a page listing disambiguations articles.
# Special chars should be encoded with unicode (\x##) and space used
# instead of _

ignore_title = {
    'wikipedia': {
        'ar': [
            'تصنيف:صفحات توضيح',
        ],
        'ca': [
            'Viquipèdia:Enllaços incorrectes a pàgines de desambiguació',
            'Viquipèdia:Registre de pàgines de desambiguació òrfenes',
            '.*Discussió:.+',
            '.*Usuari:.+',
            '.+/[aA]rxiu.*',
        ],
        'cs': [
            'Wikipedie:Chybějící interwiki/.+',
            'Wikipedie:Rozcestníky',
            'Wikipedie diskuse:Rozcestníky',
            'Wikipedie:Seznam nejvíce odkazovaných rozcestníků',
            'Wikipedie:Seznam rozcestníků/první typ',
            'Wikipedie:Seznam rozcestníků/druhý typ',
            'Wikipedista:Zirland/okres',
        ],
        'da': [
            'Wikipedia:Links til sider med flertydige titler'
        ],
        'de': [
            '.+/[aA]rchiv.*',
            '.+/Baustelle.*',
            '.+/Index',
            '.+/Spielwiese',
            '.+/[tT]est.*',
            '.*Diskussion:.+',
            'Benutzer:.+/[Ll]og.*',
            'Benutzer:C.Löser/.+',
            'Benutzer:Katharina/Begriffsklärungen',
            'Benutzer:Kirschblut/.+buchstabenkürzel',
            'Benutzer:Mathias Schindler/.+',
            'Benutzer:Noisper/Dingliste/[A-Z]',
            'Benutzer:Professor Einstein.*',
            'Benutzer:Sebbot/.+',
            'Benutzer:SirJective/.+',
            'Benutzer:Srbauer.*',
            'Benutzer:SteEis.',
            'Benutzer:Steindy.*',
            'Benutzer:SrbBot.*',
            'Benutzer:PortalBot/.+',
            'Benutzer:Xqbot/.+',
            'Lehnwort',
            'Liste griechischer Wortstämme in deutschen Fremdwörtern',
            'Liste von Gräzismen',
            'Portal:Abkürzungen/.+',
            'Portal:Astronomie/Moves',
            'Portal:Astronomie/Index/.+',
            'Portal:Hund',
            'Portal:Hund/Beobachtungsliste',
            'Portal:Marxismus',
            'Portal:Täuferbewegung/Seitenindex',
            'Wikipedia:Administratoren/Anfragen',
            'Wikipedia:Archiv/.+',
            'Wikipedia:Artikelwünsche/Ding-Liste/[A-Z]',
            'Wikipedia:Begriffsklärung.*',
            'Wikipedia:Bots/.+',
            'Wikipedia:Interwiki-Konflikte',
            'Wikipedia:ISBN-Suche',
            'Wikipedia:Liste mathematischer Themen/BKS',
            'Wikipedia:Liste mathematischer Themen/Redirects',
            'Wikipedia:Meinungsbilder/.+',
            'Wikipedia:Löschkandidaten/.+',
            'Wikipedia:WikiProjekt Altertumswissenschaft/.+',
            'Wikipedia:WikiProjekt Verwaiste Seiten/Begriffsklärungen',
            'Wikipedia:Qualitätssicherung/.+',
            'Vorlage:Infobox Weltraum',
            'Vorlage:Navigationsleiste Raumfahrt',
        ],
        'en': [
            'Wikipedia:Links to disambiguating pages',
            'Wikipedia:Disambiguation pages with links',
            'Wikipedia:Multiple-place names \\([A-Z]\\)',
            'Wikipedia:Non-unique personal name',
            "User:Jerzy/Disambiguation Pages i've Editted",
            'User:Gareth Owen/inprogress',
            'TLAs from [A-Z][A-Z][A-Z] to [A-Z][A-Z][A-Z]',
            'List of all two-letter combinations',
            'User:Daniel Quinlan/redirects.+',
            'User:Oliver Pereira/stuff',
            'Wikipedia:French Wikipedia language links',
            'Wikipedia:Polish language links',
            'Wikipedia:Undisambiguated abbreviations/.+',
            'List of acronyms and initialisms',
            'Wikipedia:Usemod article histories',
            'User:Pizza Puzzle/stuff',
            'List of generic names of political parties',
            'Talk:List of initialisms/marked',
            'Talk:List of initialisms/sorted',
            'Talk:Programming language',
            'Talk:SAMPA/To do',
            "Wikipedia:Outline of Roget's Thesaurus",
            'User:Wik/Articles',
            'User:Egil/Sandbox',
            'Wikipedia talk:Make only links relevant to the context',
            'Wikipedia:Common words, searching for which is not possible',
        ],
        'fa': [
            'ویکی‌پدیا:فهرست صفحات ابهام‌زدایی',
        ],
        'fi': [
            'Wikipedia:Luettelo täsmennyssivuista',
            'Wikipedia:Luettelo (täsmennyssivuista)',
            'Wikipedia:Täsmennyssivu',
        ],
        'fr': [
            'Wikipédia:Liens aux pages d’homonymie',
            'Wikipédia:Homonymie',
            'Wikipédia:Homonymie/Homonymes dynastiques',
            'Wikipédia:Prise de décision, noms des membres '
            'de dynasties/liste des dynastiens',
            'Liste de toutes les combinaisons de deux lettres',
            'Wikipédia:Log d’upload/.*',
            'Sigles de trois lettres de [A-Z]AA à [A-Z]ZZ',
            'Wikipédia:Pages sans interwiki,.'
        ],
        'fy': [
            'Wikipedy:Fangnet',
        ],
        'hu': [
            # hu:Wikipédia:Kocsmafal (egyéb)#Hol nem kell egyértelműsíteni?
            # 2012-02-08
            'Wikipédia:(?!Sportműhely/Eddigi cikkeink).*',
            '.*\\(egyértelműsítő lap\\)$',
            '.*[Vv]ita:.*',
            'Szerkesztő:[^/]+$',
        ],
        'ia': [
            'Categoria:Disambiguation',
            'Wikipedia:.+',
            'Usator:.+',
            'Discussion Usator:.+',
        ],
        'it': [
            'Aiuto:Disambigua/Disorfanamento',
            'Discussioni utente:.+',
            'Utente:Civvì/disorfanamento',
        ],
        'kk': [
            'Санат:Айрықты бет',
        ],
        'ko': [
            '위키백과:(동음이의) 문서의 목록',
            '위키백과:동음이의어 문서의 목록',
        ],
        'lt': [
            'Wikipedia:Rodomi nukreipiamieji straipsniai',
        ],
        'nl': [
            'Gebruiker:.*',
            'Overleg gebruiker:.+[aA]rchief.*',
            'Overleg gebruiker:Pven',
            'Portaal:.+[aA]rchief.*',
            'Wikipedia:Humor en onzin.*',
            "Wikipedia:Links naar doorverwijspagina's/Winkeldochters.*",
            "Wikipedia:Project aanmelding bij startpagina's",
            "Wikipedia:Wikiproject Roemeense gemeenten/Doorverwijspagina's",
            'Categorie:Doorverwijspagina',
            'Lijst van Nederlandse namen van pausen',
            'Overleg Wikipedia:Discussie spelling 2005',
            'Overleg Wikipedia:Doorverwijspagina',
            'Overleg Wikipedia:Logboek.*',
            'Wikipedia:Logboek.*',
            'Overleg gebruiker:Sybren/test.*',
            'Overleg gebruiker:([0-9][0-9]?[0-9]?\\.){3}[0-9][0-9]?[0-9]?',
            'Overleg:Lage Landen (staatkunde)',
            'Wikipedia:.*[aA]rchief.*',
            'Wikipedia:Doorverwijspagina',
            'Wikipedia:Lijst van alle tweeletter-combinaties',
            'Wikipedia:Onderhoudspagina',
            'Wikipedia:Ongelijke redirects',
            'Wikipedia:Protection log',
            'Wikipedia:Te verwijderen.*',
            'Wikipedia:Top 1000 van meest bekeken artikelen',
            'Wikipedia:Wikipedianen met een encyclopedisch artikel',
            'Wikipedia:Woorden die niet als zoekterm gebruikt kunnen worden',
            'Overleg gebruiker:Taka(/.*)?',
            "Wikipedia:Links naar doorverwijspagina's/Artikelen",
            'Wikipedia:Wikiproject/Redirects/.*',
            'Wikipedia:Wikiproject/Muziek/Overzicht/.*',
            "Wikipedia:Wikiproject/Roemeense gemeenten/Doorverwijspagina's",
            'Overleg Wikipedia:Wikiproject/Redirects.*',
            "Wikipedia:Links naar doorverwijspagina's/Amsterdamconstructie",
        ],
        'pl': [
            'Wikipedysta:.+',
            'Dyskusja.+:.+',
        ],
        'pt': [
            'Usuário:.+',
            'Usuário Discussão:.+',
            'Discussão:.+',
            'Lista de combinações de duas letras',
            'Wikipedia:Lista de páginas de desambiguação.+',
            'Wikipedia:Páginas para eliminar/.+',
        ],
        'ru': [
            'Категория:Disambig',
            'Википедия:Страницы разрешения неоднозначностей',
            'Википедия:Вики-уборка/Статьи без языковых ссылок',
            'Википедия:Страницы с пометкой «(значения)»',
            'Список общерусских фамилий',
        ],
        'sr': [
            'Википедија:Вишезначна одредница',
        ],
        'ur': [
            'زمرہ:ضد ابہام صفحات',
        ],
    },
    'memoryalpha': {
        'en': [
            'Memory Alpha:Links to disambiguating pages'
        ],
        'de': [
            'Memory Alpha:Liste der Wortklärungsseiten'
        ],
    },
}


def correctcap(link, text):
    """Return the link capitalized/uncapitalized according to the text.

    @param link: link page
    @type link: pywikibot.Page
    @param text: the wikitext that is supposed to refer to the link
    @type text: str
    @return: uncapitalized title of the link if the text links to the link
        with an uncapitalized title, else capitalized
    @rtype: str

    """
    linkupper = link.title()
    linklower = first_lower(linkupper)
    if '[[%s]]' % linklower in text or '[[%s|' % linklower in text:
        return linklower
    else:
        return linkupper


class ReferringPageGeneratorWithIgnore(object):

    """Referring Page generator, with an ignore manager."""

    def __init__(self, disambPage, primary=False, minimum=0, main_only=False):
        """Initializer.

        @type disambPage: pywikibot.Page
        @type primary: bool
        @type minimum: int
        @type main_only: bool
        @rtype: None

        """
        self.disambPage = disambPage
        # if run with the -primary argument, enable the ignore manager
        self.primaryIgnoreManager = PrimaryIgnoreManager(disambPage,
                                                         enabled=primary)
        self.minimum = minimum
        self.main_only = main_only

    def __iter__(self):
        """Yield pages."""
        # TODO: start yielding before all referring pages have been found
        refs = list(self.disambPage.getReferences(
            with_template_inclusion=False,
            namespaces=0 if self.main_only else None))
        pywikibot.output('Found {0} references.'.format(len(refs)))
        # Remove ignorables
        if self.disambPage.site.family.name in ignore_title and \
           self.disambPage.site.lang in ignore_title[
               self.disambPage.site.family.name]:
            for ig in ignore_title[self.disambPage.site.family.name
                                   ][self.disambPage.site.lang]:
                for i in range(len(refs) - 1, -1, -1):
                    if re.match(ig, refs[i].title()):
                        pywikibot.log('Ignoring page ' + refs[i].title())
                        del refs[i]
                    elif self.primaryIgnoreManager.isIgnored(refs[i]):
                        del refs[i]
        if len(refs) < self.minimum:
            pywikibot.output('Found only {0} pages to work on; skipping.'
                             .format(len(refs)))
            return
        pywikibot.output('Will work on {} pages.'.format(len(refs)))
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
        """Initializer.

        @type disambPage: pywikibot.Page
        @type enabled: bool
        @rtype: None

        """
        self.disambPage = disambPage
        self.enabled = enabled
        self.ignorelist = set()

        folder = config.datafilepath('disambiguations')
        if os.path.exists(folder):
            self._read_ignorelist(folder)

    def _read_ignorelist(self, folder):
        """Read pages to be ignored from file.

        @type folder: str
        @rtype: None

        """
        filename = os.path.join(
            folder, self.disambPage.title(as_filename=True) + '.txt')
        try:
            # The file is stored in the disambiguation/ subdir.
            # Create if necessary.
            with codecs.open(filename, 'r', 'utf-8') as f:
                for line in f:
                    # remove trailing newlines and carriage returns
                    line = line.rstrip('\r\n')
                    # skip empty lines
                    if line:
                        self.ignorelist.add(line)
        except IOError:
            pass

    def isIgnored(self, refPage):
        """Return if refPage is to be ignored.

        @type refPage: pywikibot.Page
        @rtype: bool

        """
        return self.enabled and refPage.title(as_url=True) in self.ignorelist

    def ignore(self, refPage):
        """Write page to ignorelist.

        @type refPage: pywikibot.Page
        @rtype: None

        """
        if self.enabled:
            # Skip this occurrence next time.
            filename = config.datafilepath(
                'disambiguations',
                self.disambPage.title(as_url=True) + '.txt')
            try:
                # Open file for appending. If none exists, create a new one.
                with codecs.open(filename, 'a', 'utf-8') as f:
                    f.write(refPage.title(as_url=True) + '\n')
            except IOError:
                pass


class AddAlternativeOption(OutputProxyOption):

    """Add a new alternative."""

    def result(self, value):
        """Add the alternative and then list them."""
        newAlternative = pywikibot.input('New alternative:')
        self._outputter.sequence.append(newAlternative)
        super(AddAlternativeOption, self).result(value)


class EditOption(StandardOption):

    """Edit the text."""

    def __init__(self, option, shortcut, text, start, title):
        """Initializer.

        @type option: str
        @type shortcut: str
        @type text: str
        @type start: int
        @type title: str
        @rtype: None

        """
        super(EditOption, self).__init__(option, shortcut)
        self._text = text
        self._start = start
        self._title = title

    @property
    def stop(self):
        """Return whether if user didn't press cancel and changed it.

        @rtype: bool

        """
        return self.new_text and self.new_text != self._text

    def result(self, value):
        """Open a text editor and let the user change it."""
        editor = editarticle.TextEditor()
        self.new_text = editor.edit(self._text, jumpIndex=self._start,
                                    highlight=self._title)
        return super(EditOption, self).result(value)


class ShowPageOption(StandardOption):

    """Show the page's contents in an editor."""

    def __init__(self, option, shortcut, start, page):
        """Initializer."""
        super(ShowPageOption, self).__init__(option, shortcut, stop=False)
        self._start = start
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        self._page = page

    def result(self, value):
        """Open a text editor and show the text."""
        editor = editarticle.TextEditor()
        editor.edit(self._page.text,
                    jumpIndex=self._start,
                    highlight=self._page.title())


class AliasOption(StandardOption):

    """An option allowing multiple aliases which also select it."""

    def __init__(self, option, shortcuts, stop=True):
        """Initializer."""
        super(AliasOption, self).__init__(option, shortcuts[0], stop=stop)
        self._aliases = frozenset(s.lower() for s in shortcuts[1:])

    def test(self, value):
        """Test aliases and combine it with the original test."""
        return value.lower() in self._aliases or super(AliasOption,
                                                       self).test(value)


class DisambiguationRobot(SingleSiteBot):

    """Disambiguation bot."""

    ignore_contents = {
        'de': ('{{[Ii]nuse}}',
               '{{[Ll]öschen}}',
               ),
        'fi': ('{{[Tt]yöstetään}}',
               ),
        'kk': ('{{[Ii]nuse}}',
               '{{[Pp]rocessing}}',
               ),
        'nl': ('{{wiu2}}',
               '{{nuweg}}',
               ),
        'ru': ('{{[Ii]nuse}}',
               '{{[Pp]rocessing}}',
               ),
    }

    primary_redir_template = {
        # First letter uppercase
        'hu': 'Egyért-redir',
    }

    def __init__(self, always, alternatives, getAlternatives, dnSkip,
                 generator, primary, main_only, first_only=False, minimum=0):
        """Initializer."""
        super(DisambiguationRobot, self).__init__()
        self.always = always
        self.alternatives = alternatives
        self.getAlternatives = getAlternatives
        self.dnSkip = dnSkip
        self.generator = generator
        self.primary = primary
        self.main_only = main_only
        self.first_only = first_only
        self.minimum = minimum

        self.mysite = self.site
        self.mylang = self.mysite.lang
        self.comment = None

        self.dn_template_str = i18n.translate(self.mysite, dn_template)

        self.setupRegexes()

    def checkContents(self, text):
        """
        Check if the text matches any of the ignore regexes.

        @param text: wikitext of a page
        @type text: str
        @return: None if none of the regular expressions
            given in the dictionary at the top of this class matches
            a substring of the text, otherwise the matched substring
        @rtype: str or None
        """
        for ig in self.ignore_contents_regexes:
            match = ig.search(text)
            if match:
                return match.group()
        return None

    def makeAlternativesUnique(self):
        """Remove duplicate items from self.alternatives.

        Preserve the order of alternatives.
        @rtype: None

        """
        seen = set()
        self.alternatives = [
            i for i in self.alternatives if i not in seen and not seen.add(i)
        ]

    def setupRegexes(self):
        """Compile regular expressions."""
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
        # note: the definition of 'letter' varies from language to language.
        self.linkR = re.compile(r"""
            \[\[  (?P<title>     [^\[\]\|#]*)
                  (?P<section> \#[^\]\|]*)?
               (\|(?P<label>     [^\]]*))?  \]\]
            (?P<linktrail>{})""".format(linktrail), flags=re.X)

    @staticmethod
    def firstlinks(page):
        """Return a list of first links of every line beginning with `*`.

        When a disambpage is full of unnecessary links, this may be useful
        to sort out the relevant links. E.g. from line
        `* [[Jim Smith (smith)|Jim Smith]] ([[1832]]-[[1932]]) [[English]]`
        it returns only 'Jim Smith (smith)'
        Lines without an asterisk at the beginning will be disregarded.
        No check for page existence, it has already been done.
        """
        reg = re.compile(r'\*.*?\[\[(.*?)(?:\||\]\])')
        for line in page.text.splitlines():
            found = reg.match(line)
            if found:
                yield found.group(1)

    def firstize(self, page, links):
        """Call firstlinks and remove extra links.

        This will remove a lot of silly redundant links from overdecorated
        disambiguation pages and leave the first link of each asterisked
        line only. This must be done if -first is used in command line.
        """
        titles = {firstcap(t) for t in self.firstlinks(page)}
        links = list(links)
        for l in links[:]:  # uses a copy because of remove!
            if l.title() not in titles:
                links.remove(l)
        return links

    def treat_links(self, refPage, disambPage):
        """Resolve the links to disambPage or its redirects.

        @param disambPage: the disambiguation page or redirect we don't want
            anything to link to
        @type disambPage: pywikibot.Page
        @param refPage: a page linking to disambPage
        @type refPage: pywikibot.Page
        @return: Return whether continue with next page (True)
            or next disambig (False)
        @rtype: bool

        """
        nochange = True

        for page in chain(
            (disambPage,), disambPage.getReferences(filter_redirects=True)
        ):
            treat_result = self.treat_disamb_only(refPage, page)
            if treat_result == 'nextpage':
                return True
            if treat_result == 'nextdisambig':
                return False
            if treat_result == 'done':
                nochange = False

        if nochange:
            pywikibot.output('No changes necessary in ' + refPage.title())
        return True

    def treat_disamb_only(self, refPage, disambPage):
        """Resolve the links to disambPage but don't look for its redirects.

        @param disambPage: the disambiguation page or redirect we don't want
            anything to link to
        @type disambPage: pywikibot.Page
        @param refPage: a page linking to disambPage
        @type refPage: pywikibot.Page
        @return: "nextpage" if the user enters "n" to skip this page,
            "nochange" if the page needs no change, and
            "done" if the page is processed successfully
        @rtype: str

        """
        # TODO: break this function up into subroutines!

        self.current_page = refPage
        include = False
        unlink_counter = 0
        new_targets = []
        try:
            text = refPage.get()
            ignoreReason = self.checkContents(text)
            if ignoreReason:
                pywikibot.output(
                    '\n\nSkipping {0} because it contains {1}.\n\n'
                    .format(refPage.title(), ignoreReason))
            else:
                include = True
        except pywikibot.IsRedirectPage:
            pywikibot.output('{0} is a redirect to {1}'
                             .format(refPage.title(), disambPage.title()))
            if disambPage.isRedirectPage():
                target = self.alternatives[0]
                if pywikibot.input_yn(
                    'Do you want to make redirect {0} point to {1}?'
                    .format(refPage.title(), target),
                        default=False, automatic_quit=False):
                    redir_text = '#{0} [[{1}]]' \
                                 .format(self.mysite.redirect(), target)
                    try:
                        refPage.put(redir_text, summary=self.comment,
                                    asynchronous=True)
                    except pywikibot.PageNotSaved as error:
                        pywikibot.output('Page not saved: {0}'
                                         .format(error.args))
            else:
                choice = pywikibot.input_choice(
                    'Do you want to work on pages linking to {0}?'
                    .format(refPage.title()),
                    [('yes', 'y'), ('no', 'n'), ('change redirect', 'c')], 'n',
                    automatic_quit=False)
                if choice == 'y':
                    gen = ReferringPageGeneratorWithIgnore(
                        refPage, self.primary, main_only=self.main_only
                    )
                    preloadingGen = pagegenerators.PreloadingGenerator(gen)
                    for refPage2 in preloadingGen:
                        # run until the user selected 'quit'
                        self.treat_links(refPage2, refPage)
                elif choice == 'c':
                    text = refPage.get(get_redirect=True)
                    include = 'redirect'
        except pywikibot.NoPage:
            pywikibot.output(
                'Page [[{0}]] does not seem to exist?! Skipping.'
                .format(refPage.title()))
            include = False
        if include in (True, 'redirect'):
            # save the original text so we can show the changes later
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
                        # No changes necessary for this disambiguation title.
                        return 'nochange'
                    else:
                        # stop loop and save page
                        break
                # Ensure that next time around we will not find this same hit.
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
                    pywikibot.log('Invalid link [[%s]] in page [[%s]]'
                                  % (m.group('title'), refPage.title()))
                    continue
                n += 1
                # how many bytes should be displayed around the current link
                context = 60
                # check if there's a dn-template here already
                if (self.dnSkip and self.dn_template_str
                        and self.dn_template_str[:-2] in text[
                            m.end():m.end() + len(self.dn_template_str) + 8]):
                    continue

                edit = EditOption('edit page', 'e', text, m.start(),
                                  disambPage.title())
                context_option = HighlightContextOption(
                    'more context', 'm', text, 60, start=m.start(),
                    end=m.end())
                context_option.before_question = True

                options = [ListOption(self.alternatives, ''),
                           ListOption(self.alternatives, 'r'),
                           StandardOption('skip link', 's'),
                           edit,
                           StandardOption('next page', 'n'),
                           StandardOption('next disambig', 'g'),
                           StandardOption('unlink', 'u')]
                if self.dn_template_str:
                    # '?', '/' for old choice
                    options += [AliasOption('tag template %s' %
                                            self.dn_template_str,
                                            ['t', '?', '/'])]
                options += [context_option]
                if not edited:
                    options += [ShowPageOption('show disambiguation page', 'd',
                                               m.start(), disambPage)]
                options += [
                    OutputProxyOption('list', 'l',
                                      SequenceOutputter(self.alternatives)),
                    AddAlternativeOption('add new', 'a',
                                         SequenceOutputter(self.alternatives))]
                if edited:
                    options += [StandardOption('save in this form', 'x')]

                # TODO: Output context on each question
                answer = pywikibot.input_choice('Option', options,
                                                default=self.always,
                                                force=bool(self.always))
                if answer == 'x':
                    assert edited, 'invalid option before editing'
                    break
                elif answer == 's':
                    n -= 1  # TODO what's this for?
                    continue
                elif answer == 'e':
                    text = edit.new_text
                    edited = True
                    curpos = 0
                    continue
                elif answer == 'n':
                    # skip this page
                    if self.primary:
                        # If run with the -primary argument, skip this
                        # occurrence next time.
                        self.primaryIgnoreManager.ignore(refPage)
                    return 'nextpage'
                elif answer == 'g':
                    return 'nextdisambig'

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
                if answer == 't':
                    assert self.dn_template_str
                    # small chunk of text to search
                    search_text = text[m.end():m.end() + context]
                    # figure out where the link (and sentence) ends, put note
                    # there
                    end_of_word_match = re.search(r'\s', search_text)
                    if end_of_word_match:
                        position_split = end_of_word_match.start(0)
                    else:
                        position_split = 0
                    # insert dab needed template
                    text = (text[:m.end() + position_split]
                            + self.dn_template_str
                            + text[m.end() + position_split:])
                    dn = True
                    continue
                elif answer == 'u':
                    # unlink - we remove the section if there's any
                    text = text[:m.start()] + link_text + text[m.end():]
                    unlink_counter += 1
                    continue
                else:
                    # Check that no option from above was missed
                    assert isinstance(answer, tuple), 'only tuple answer left.'
                    assert answer[0] in ['r', ''], 'only valid tuple answers.'
                    if answer[0] == 'r':
                        # we want to throw away the original link text
                        replaceit = link_text == page_title
                    elif include == 'redirect':
                        replaceit = True
                    else:
                        replaceit = False

                    new_page_title = answer[1]
                    repPl = pywikibot.Page(pywikibot.Link(new_page_title,
                                                          disambPage.site))
                    if (new_page_title[0].isupper()
                            or link_text[0].isupper()):
                        new_page_title = repPl.title()
                    else:
                        new_page_title = repPl.title()
                        new_page_title = first_lower(new_page_title)
                    if new_page_title not in new_targets:
                        new_targets.append(new_page_title)
                    if replaceit and trailing_chars:
                        newlink = '[[{0}{1}]]{2}'.format(new_page_title,
                                                         section,
                                                         trailing_chars)
                    elif replaceit or (new_page_title == link_text
                                       and not section):
                        newlink = '[[{0}]]'.format(new_page_title)
                    # check if we can create a link with trailing characters
                    # instead of a pipelink
                    elif (
                        (len(new_page_title) <= len(link_text))
                        and (firstcap(link_text[:len(new_page_title)])
                             == firstcap(new_page_title))
                        and (self.trailR.sub(
                            '', link_text[len(new_page_title):]) == '')
                        and (not section)
                    ):
                        newlink = '[[{0}]]{1}'.format(
                            link_text[:len(new_page_title)],
                            link_text[len(new_page_title):])
                    else:
                        newlink = '[[{0}{1}|{2}]]'.format(new_page_title,
                                                          section, link_text)
                    text = text[:m.start()] + newlink + text[m.end():]
                    continue
                # Todo: This line is unreachable (T155337)
                pywikibot.output(text[max(0, m.start() - 30):m.end() + 30])
            if text == original_text:
                pywikibot.output('\nNo changes have been made:\n')
            else:
                pywikibot.output('\nThe following changes have been made:\n')
                pywikibot.showDiff(original_text, text)
                pywikibot.output('')
                # save the page
                self.setSummaryMessage(disambPage, new_targets, unlink_counter,
                                       dn)
                try:
                    refPage.put(text, summary=self.comment, asynchronous=True)
                except pywikibot.LockedPage:
                    pywikibot.output('Page not saved: page is locked')
                except pywikibot.PageNotSaved as error:
                    pywikibot.output('Page not saved: {0}'.format(error.args))
        return 'done'

    def findAlternatives(self, disambPage):
        """Extend self.alternatives using correctcap of disambPage.linkedPages.

        @param disambPage: the disambiguation page
        @type disambPage: pywikibot.Page
        @return: True if everything goes fine, False otherwise
        @rtype: bool

        """
        if disambPage.isRedirectPage() and not self.primary:
            primary = i18n.translate(disambPage.site,
                                     self.primary_redir_template)
            if primary:
                primary_page = pywikibot.Page(disambPage.site,
                                              'Template:' + primary)
            if primary and primary_page in disambPage.templates():
                baseTerm = disambPage.title()
                for template, params in disambPage.templatesWithParams():
                    if params and template == primary_page:
                        baseTerm = params[1]
                        break
                disambTitle = primary_topic_format[self.mylang] % baseTerm
                try:
                    disambPage2 = pywikibot.Page(
                        pywikibot.Link(disambTitle, self.mysite))
                    links = disambPage2.linkedPages()
                    if self.first_only:
                        links = self.firstize(disambPage2, links)
                    links = [correctcap(l, disambPage2.get()) for l in links]
                except pywikibot.NoPage:
                    pywikibot.output('No page at {0}, using redirect target.'
                                     .format(disambTitle))
                    links = disambPage.linkedPages()[:1]
                    links = [correctcap(l, disambPage.get(get_redirect=True))
                             for l in links]
                self.alternatives += links
            else:
                try:
                    target = disambPage.getRedirectTarget().title()
                    self.alternatives.append(target)
                except pywikibot.NoPage:
                    pywikibot.output('The specified page was not found.')
                    user_input = pywikibot.input("""\
Please enter the name of the page where the redirect should have pointed at,
or press enter to quit:""")
                    if user_input == '':
                        self.quit()
                    else:
                        self.alternatives.append(user_input)
                except pywikibot.IsNotRedirectPage:
                    pywikibot.output(
                        'The specified page is not a redirect. Skipping.')
                    return False
        elif self.getAlternatives:
            # not disambPage.isRedirectPage() or self.primary
            try:
                if self.primary:
                    try:
                        disambPage2 = pywikibot.Page(
                            pywikibot.Link(
                                primary_topic_format[self.mylang]
                                % disambPage.title(),
                                self.mysite))
                        links = disambPage2.linkedPages()
                        if self.first_only:
                            links = self.firstize(disambPage2, links)
                        links = [correctcap(l, disambPage2.get())
                                 for l in links]
                    except pywikibot.NoPage:
                        pywikibot.output(
                            'Page does not exist; using first '
                            'link in page {0}.'.format(disambPage.title()))
                        links = disambPage.linkedPages()[:1]
                        links = [correctcap(l, disambPage.get())
                                 for l in links]
                else:
                    try:
                        links = disambPage.linkedPages()
                        if self.first_only:
                            links = self.firstize(disambPage, links)
                        links = [correctcap(l, disambPage.get())
                                 for l in links]
                    except pywikibot.NoPage:
                        pywikibot.output('Page does not exist, skipping.')
                        return False
            except pywikibot.IsRedirectPage:
                pywikibot.output('Page is a redirect, skipping.')
                return False
            self.alternatives += links
        return True

    def setSummaryMessage(self, disambPage, new_targets=[], unlink_counter=0,
                          dn=False):
        """Setup i18n summary message."""
        # make list of new targets
        comma = self.mysite.mediawiki_message('comma-separator')
        targets = comma.join('[[{0}]]'.format(page_title)
                             for page_title in new_targets)

        if not targets:
            targets = i18n.twtranslate(self.mysite,
                                       'solve_disambiguation-unknown-page')

        # first check whether user has customized the edit comment
        if (self.mysite.family.name in config.disambiguation_comment
                and self.mylang in config.disambiguation_comment[
                    self.mysite.family.name]):
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

    def treat(self, page):
        """Work on a single disambiguation page."""
        self.primaryIgnoreManager = PrimaryIgnoreManager(
            page, enabled=self.primary)

        if not self.findAlternatives(page):
            return

        pywikibot.output('\nAlternatives for {}'.format(page))
        self.makeAlternativesUnique()
        # sort possible choices
        if config.sort_ignore_case:
            self.alternatives.sort(key=lambda x: x.lower())
        else:
            self.alternatives.sort()
        SequenceOutputter(self.alternatives).output()

        gen = ReferringPageGeneratorWithIgnore(
            page,
            self.primary,
            minimum=self.minimum,
            main_only=self.main_only
        )
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        for refPage in preloadingGen:
            if not self.primaryIgnoreManager.isIgnored(refPage):
                if not self.treat_links(refPage, page):
                    break  # next disambig

        # clear alternatives before working on next disambiguation page
        self.alternatives = []


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    # the option that's always selected when the bot wonders what to do with
    # a link. If it's None, the user is prompted (default behaviour).
    always = None
    alternatives = []
    getAlternatives = True
    dnSkip = False
    generator = None
    primary = False
    first_only = False
    main_only = False

    # For sorting the linked pages, case can be ignored
    minimum = 0

    local_args = pywikibot.handle_args(args)
    generator_factory = pagegenerators.GeneratorFactory(
        positional_arg_name='page')

    for argument in local_args:
        arg, _, value = argument.partition(':')
        if arg == '-primary':
            primary = True
            if value:
                getAlternatives = False
                alternatives.append(value)
        elif arg == '-always':
            always = value
        elif arg == '-pos':
            if not value:
                pass
            elif value.startswith(':'):
                alternatives.append(value)
            else:
                mysite = pywikibot.Site()
                page = pywikibot.Page(pywikibot.Link(value, mysite))
                if page.exists():
                    alternatives.append(page.title())
                elif pywikibot.input_yn(
                    'Possibility {0} does not actually exist. Use it anyway?'
                    .format(page.title()),
                        default=False, automatic_quit=False):
                    alternatives.append(page.title())
        elif arg == '-just':
            getAlternatives = False
        elif arg == '-dnskip':
            dnSkip = True
        elif arg == '-main':
            main_only = True
        elif arg == '-first':
            first_only = True
        elif arg == '-min':
            minimum = int(value)
        elif arg == '-start':
            try:
                generator = pagegenerators.CategorizedPageGenerator(
                    pywikibot.Site().disambcategory(),
                    start=value, namespaces=[0])
            except pywikibot.NoPage:
                pywikibot.output(
                    'Disambiguation category for your wiki is not known.')
                raise
        else:
            generator_factory.handleArg(argument)

    site = pywikibot.Site()

    generator = generator_factory.getCombinedGenerator(generator)

    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return

    site.login()

    bot = DisambiguationRobot(always, alternatives, getAlternatives, dnSkip,
                              generator, primary, main_only, first_only,
                              minimum=minimum)
    bot.run()


if __name__ == '__main__':
    main()
