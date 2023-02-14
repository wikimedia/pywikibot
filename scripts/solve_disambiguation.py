#!/usr/bin/env python3
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

   -main       only check pages in the main namespace, not in the Talk,
               Project, User, etc. namespaces.

   -first      Uses only the first link of every line on the disambiguation
               page that begins with an asterisk. Useful if the page is full
               of irrelevant links that are not subject to disambiguation.
               You won't get all af them as options, just the first on each
               line. For a moderated example see
               https://en.wikipedia.org/wiki/Szerdahely
               A really exotic one is
               https://hu.wikipedia.org/wiki/Brabant_(egyértelműsítő lap)

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
# (C) Pywikibot team, 2003-2022
#
# Distributed under the terms of the MIT license.
#
import codecs
import os
import re
from contextlib import suppress
from itertools import chain
from typing import Generator, Optional

import pywikibot
from pywikibot import config
from pywikibot import editor as editarticle
from pywikibot import i18n, pagegenerators
from pywikibot.backports import List
from pywikibot.bot import (
    HighlightContextOption,
    ListOption,
    OutputProxyOption,
    SingleSiteBot,
    StandardOption,
)
from pywikibot.exceptions import (
    Error,
    IsNotRedirectPageError,
    IsRedirectPageError,
    LockedPageError,
    NoPageError,
    PageSaveRelatedError,
)
from pywikibot.tools import first_lower, first_upper, issue_deprecation_warning
from pywikibot.tools.formatter import SequenceOutputter


# Disambiguation Needed template
dn_template = {
    'ar': '{{بحاجة لتوضيح}}',
    'arz': '{{Disambiguation needed}}',
    'en': '{{dn}}',
    'fr': '{{Lien vers un homonyme}}',
}

# disambiguation page name format for "primary topic" disambiguations
# (Begriffsklärungen nach Modell 2)
primary_topic_format = {
    'ar': '%s_(توضيح)',
    'arz': '%s_(توضيح)',
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
        'ca': [
            'Viquipèdia:Enllaços incorrectes a pàgines de desambiguació',
            'Viquipèdia:Registre de pàgines de desambiguació òrfenes',
            '.*Discussió:.+',
            '.*Usuari:.+',
            '.+/[aA]rxiu.*',
        ],
        'cs': [
            'Wikipedie:Rozcestníky',
            'Diskuse k Wikipedii:Rozcestníky',
            'Wikipedie:Údržbové seznamy/Nejvíce odkazované rozcestníky/seznam',
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


def correctcap(link, text: str) -> str:
    """Return the link capitalized/uncapitalized according to the text.

    :param link: link page
    :type link: pywikibot.Page
    :param text: the wikitext that is supposed to refer to the link
    :return: uncapitalized title of the link if the text links to the link
        with an uncapitalized title, else capitalized
    """
    linkupper = link.title()
    linklower = first_lower(linkupper)
    if f'[[{linklower}]]' in text or f'[[{linklower}|' in text:
        return linklower
    return linkupper


class ReferringPageGeneratorWithIgnore:

    """Referring Page generator, with an ignore manager."""

    def __init__(
        self,
        page,
        primary: bool = False,
        minimum: int = 0,
        main_only: bool = False
    ) -> None:
        """Initializer.

        :type page: pywikibot.Page
        """
        self.page = page
        # if run with the -primary argument, enable the ignore manager
        self.primaryIgnoreManager = PrimaryIgnoreManager(page, enabled=primary)
        self.minimum = minimum
        self.main_only = main_only

    def __iter__(self) -> Generator[pywikibot.Page, None, None]:
        """Yield pages."""
        # TODO: start yielding before all referring pages have been found
        refs = list(self.page.getReferences(with_template_inclusion=False,
                                            namespaces=0 if self.main_only
                                            else None))
        pywikibot.info(f'Found {len(refs)} references.')
        # Remove ignorables
        site = self.page.site
        if site.family.name in ignore_title \
           and site.lang in ignore_title[site.family.name]:
            for ig in ignore_title[site.family.name][site.lang]:
                for i in range(len(refs) - 1, -1, -1):
                    if re.match(ig, refs[i].title()):
                        pywikibot.log('Ignoring page ' + refs[i].title())
                        del refs[i]
                    elif self.primaryIgnoreManager.isIgnored(refs[i]):
                        del refs[i]
        if len(refs) < self.minimum:
            pywikibot.info('Found only {} pages to work on; skipping.'
                           .format(len(refs)))
            return
        pywikibot.info(f'Will work on {len(refs)} pages.')
        yield from refs


class PrimaryIgnoreManager:

    """
    Primary ignore manager.

    If run with the -primary argument, reads from a file which pages should
    not be worked on; these are the ones where the user pressed n last time.
    If run without the -primary argument, doesn't ignore any pages.

    """

    def __init__(self, disamb_page, enabled: bool = False) -> None:
        """Initializer.

        :type disamb_page: pywikibot.Page
        """
        self.disamb_page = disamb_page
        self.enabled = enabled
        self.ignorelist = set()

        folder = config.datafilepath('disambiguations')
        if os.path.exists(folder):
            self._read_ignorelist(folder)

    def _read_ignorelist(self, folder) -> None:
        """Read pages to be ignored from file.

        :type folder: str
        """
        filename = os.path.join(
            folder, self.disamb_page.title(as_filename=True) + '.txt')

        # The file is stored in the disambiguation/ subdir.
        # Create if necessary.
        with suppress(IOError), codecs.open(filename, 'r', 'utf-8') as f:
            for line in f:
                # remove trailing newlines and carriage returns
                line = line.rstrip('\r\n')
                # skip empty lines
                if line:
                    self.ignorelist.add(line)

    def isIgnored(self, ref_page) -> bool:  # noqa: N802
        """Return if ref_page is to be ignored.

        :type ref_page: pywikibot.Page
        """
        return self.enabled and ref_page.title(as_url=True) in self.ignorelist

    def ignore(self, page_titles) -> None:
        """Write pages to ignorelist.

        :param page_titles: page titles to be ignored
        :type page_titles: iterable
        """
        # backward compatibility
        if isinstance(page_titles, pywikibot.Page):
            page_titles = [page_titles.title(as_url=True)]
        if self.enabled:
            # Skip this occurrence next time.
            filename = config.datafilepath(
                'disambiguations',
                self.disamb_page.title(as_url=True) + '.txt')

            # Open file for appending. If none exists, create a new one.
            with suppress(IOError), codecs.open(filename, 'a', 'utf-8') as f:
                f.write('\n'.join(page_titles) + '\n')


class AddAlternativeOption(OutputProxyOption):

    """Add a new alternative."""

    def result(self, value) -> None:
        """Add the alternative and then list them."""
        new_alternative = pywikibot.input('New alternative:')
        self._outputter.sequence.append(new_alternative)
        super().result(value)


class EditOption(StandardOption):

    """Edit the text."""

    def __init__(self, option, shortcut, text, start, title) -> None:
        """Initializer.

        :type option: str
        :type shortcut: str
        :type text: str
        :type start: int
        :type title: str
        """
        super().__init__(option, shortcut)
        self._text = text
        self._start = start
        self._title = title

    @property
    def stop(self) -> bool:
        """Return whether if user didn't press cancel and changed it."""
        return self.new_text and self.new_text != self._text

    def result(self, value) -> str:
        """Open a text editor and let the user change it."""
        editor = editarticle.TextEditor()
        self.new_text = editor.edit(self._text, jumpIndex=self._start,
                                    highlight=self._title)
        return super().result(value)


class ShowPageOption(StandardOption):

    """Show the page's contents in an editor."""

    def __init__(self, option, shortcut, start, page) -> None:
        """Initializer."""
        super().__init__(option, shortcut, stop=False)
        self._start = start
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        self._page = page

    def result(self, value) -> None:
        """Open a text editor and show the text."""
        editor = editarticle.TextEditor()
        editor.edit(self._page.text,
                    jumpIndex=self._start,
                    highlight=self._page.title())


class AliasOption(StandardOption):

    """An option allowing multiple aliases which also select it."""

    def __init__(self, option, shortcuts, stop: bool = True) -> None:
        """Initializer."""
        super().__init__(option, shortcuts[0], stop=stop)
        self._aliases = frozenset(s.lower() for s in shortcuts[1:])

    def test(self, value) -> bool:
        """Test aliases and combine it with the original test."""
        return value.lower() in self._aliases or super().test(value)


class DisambiguationRobot(SingleSiteBot):

    """Disambiguation Bot."""

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

    # refer -help message for complete options documentation
    disambig_options = {
        'always': None,  # always perform the same action
        'pos': [],  # add possibilities as alternative disambig
        'just': True,  # just and only use the possibilities given with command
        'dnskip': False,  # skip  already marked links
        'primary': False,  # primary topic disambig
        'main': False,  # only use main namespace
        'first': False,  # use first link only
        'min': 0,  # minimum number of pages on a disambig
    }

    # needed for argument cleanup
    available_options = disambig_options

    def __init__(self, *args, **kwargs) -> None:
        """Initializer."""
        self._clean_args(args, kwargs)
        super().__init__(**kwargs)
        self.ignores = set()
        self.summary = None
        self.dn_template_str = i18n.translate(self.site, dn_template)

    def _clean_args(self, args, kwargs) -> None:
        """Cleanup positional and keyword arguments.

        Replace positional arguments with keyword arguments.
        Replace old keywords with new keywords which are given by
        argument handling.

        This also fixes arguments which aren't currently used by
        BaseDisambigBot abstract class but was introduced for the old
        DisambiguationRobot to prevent multiple deprecation warnings.
        """
        # New keys of positional arguments
        keys = ('always', 'pos', 'just', 'dnskip', 'generator', 'primary',
                'main', 'first', 'min')

        # Keys mapping from old argument name to new keywords.
        # The ordering of dics is not safe for Python < 3.7. Therefore
        # we need a dict in addition to key above.
        keymap = {
            'alternatives': 'pos',
            'getAlternatives': 'just',
            'dnSkip': 'dnskip',
            'main_only': 'main',
            'first_only': 'first',
            'minimum': 'min',
        }

        # Replace positional arguments with keyword arguments
        for i, arg in enumerate(args):
            key = keys[i]
            issue_deprecation_warning(
                f'Positional argument {i + 1} ({arg})',
                f'keyword argument "{key}={arg}"',
                since='6.0.0')
            if key in kwargs:
                pywikibot.warning('{!r} is given as keyword argument {!r} '
                                  'already; ignoring {!r}'
                                  .format(key, arg, kwargs[key]))
            else:
                kwargs[key] = arg

        # replace old keywords to new
        for key in list(kwargs):
            if key in keymap:
                newkey = keymap[key]
                issue_deprecation_warning(
                    f'{key!r} argument of {self.__class__.__name__}',
                    repr(newkey), since='6.0.0')
                kwargs[newkey] = kwargs.pop(key)

        # Expand available_options
        # Currently scripts may have its own options set
        added_keys = []
        for key in keys:
            if key != 'generator' and key not in self.available_options:
                added_keys.append(key)
                self.available_options[key] = self.disambig_options[key]
        if added_keys:
            pywikibot.warning("""\
The following keys were added to available_options:
{options}.
Either add them to available_options setting of {classname}
bot class or use available_options.update() to use default settings from
DisambiguationRobot""".format(options=added_keys,
                              classname=self.__class__.__name__))

    def checkContents(self, text: str) -> Optional[str]:  # noqa: N802
        """
        Check if the text matches any of the ignore regexes.

        :param text: wikitext of a page
        :return: None if none of the regular expressions
            given in the dictionary at the top of this class matches
            a substring of the text, otherwise the matched substring
        """
        for ig in self.ignore_contents_regexes:
            match = ig.search(text)
            if match:
                return match.group()
        return None

    def makeAlternativesUnique(self) -> None:  # noqa: N802
        """Remove duplicate items from self.opt.pos.

        Preserve the order of alternatives.
        """
        seen = set()
        self.opt.pos = [i for i in self.opt.pos
                        if i not in seen and not seen.add(i)]

    def setup(self) -> None:
        """Compile regular expressions."""
        self.ignore_contents_regexes = []
        if self.site.lang in self.ignore_contents:
            for ig in self.ignore_contents[self.site.lang]:
                self.ignore_contents_regexes.append(re.compile(ig))

        linktrail = self.site.linktrail()
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
    def firstlinks(page) -> Generator[str, None, None]:
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
                yield found[1]

    def firstize(self, page, links) -> List[pywikibot.Page]:
        """Call firstlinks and remove extra links.

        This will remove a lot of silly redundant links from overdecorated
        disambiguation pages and leave the first link of each asterisked
        line only. This must be done if -first is used in command line.
        """
        titles = {first_upper(t) for t in self.firstlinks(page)}
        links = list(links)
        for link in links[:]:  # uses a copy because of remove!
            if link.title() not in titles:
                links.remove(link)
        return links

    def treat_links(self, ref_page, disamb_page) -> bool:
        """Resolve the links to disamb_page or its redirects.

        :param disamb_page: the disambiguation page or redirect we don't want
            anything to link to
        :type disamb_page: pywikibot.Page
        :param ref_page: a page linking to disamb_page
        :type ref_page: pywikibot.Page
        :return: Return whether continue with next page (True)
            or next disambig (False)
        """
        nochange = True

        for page in chain(
            (disamb_page,), disamb_page.getReferences(filter_redirects=True)
        ):
            treat_result = self.treat_disamb_only(ref_page, page)
            if treat_result == 'nextpage':
                return True
            if treat_result == 'nextdisambig':
                return False
            if treat_result == 'done':
                nochange = False

        if nochange:
            pywikibot.info('No changes necessary in ' + ref_page.title())
        return True

    def treat_disamb_only(self, ref_page, disamb_page) -> str:
        """Resolve the links to disamb_page but don't look for its redirects.

        :param disamb_page: the disambiguation page or redirect we don't want
            anything to link to
        :type disamb_page: pywikibot.Page
        :param ref_page: a page linking to disamb_page
        :type ref_page: pywikibot.Page
        :return: "nextpage" if the user enters "n" to skip this page,
            "nochange" if the page needs no change, and
            "done" if the page is processed successfully
        """
        # TODO: break this function up into subroutines!

        self.current_page = ref_page
        include = False
        unlink_counter = 0
        new_targets = []
        try:
            text = ref_page.get()
        except IsRedirectPageError:
            pywikibot.info('{} is a redirect to {}'
                           .format(ref_page.title(), disamb_page.title()))
            if disamb_page.isRedirectPage():
                target = self.opt.pos[0]
                if pywikibot.input_yn(
                    'Do you want to make redirect {} point to {}?'
                    .format(ref_page.title(), target),
                        default=False, automatic_quit=False):
                    redir_text = '#{} [[{}]]' \
                                 .format(self.site.redirect(), target)
                    try:
                        ref_page.put(redir_text, summary=self.summary,
                                     asynchronous=True)
                    except PageSaveRelatedError as error:
                        pywikibot.info(f'Page not saved: {error.args}')
            else:
                choice = pywikibot.input_choice(
                    'Do you want to work on pages linking to {}?'
                    .format(ref_page.title()),
                    [('yes', 'y'), ('no', 'n'), ('change redirect', 'c')], 'n',
                    automatic_quit=False)
                if choice == 'y':
                    gen = ReferringPageGeneratorWithIgnore(
                        ref_page, self.opt.primary, main_only=self.opt.main
                    )
                    gen = pagegenerators.PreloadingGenerator(gen)
                    for ref_page2 in gen:
                        # run until the user selected 'quit'
                        self.treat_links(ref_page2, ref_page)
                elif choice == 'c':
                    text = ref_page.get(get_redirect=True)
                    include = 'redirect'
        except NoPageError:
            pywikibot.info(
                'Page [[{}]] does not seem to exist?! Skipping.'
                .format(ref_page.title()))
        else:
            ignore_reason = self.checkContents(text)
            if ignore_reason:
                pywikibot.info(
                    '\n\nSkipping {} because it contains {}.\n\n'
                    .format(ref_page.title(), ignore_reason))
            else:
                include = True

        if include:
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

                    # stop loop and save page
                    break

                # Ensure that next time around we will not find this same hit.
                curpos = m.start() + 1
                try:
                    foundlink = pywikibot.Link(m['title'], disamb_page.site)
                    foundlink.parse()
                except Error:
                    continue

                # ignore interwiki links
                if foundlink.site != disamb_page.site:
                    continue

                # Check whether the link found is to disamb_page.
                try:
                    if foundlink.canonical_title() != disamb_page.title():
                        continue

                except Error:
                    # must be a broken link
                    pywikibot.log('Invalid link [[{}]] in page [[{}]]'
                                  .format(m['title'], ref_page.title()))
                    continue

                n += 1

                # how many bytes should be displayed around the current link
                context = 60

                # check if there's a dn-template here already
                if (self.opt.dnskip and self.dn_template_str
                        and self.dn_template_str[:-2] in text[
                            m.end():m.end() + len(self.dn_template_str) + 8]):
                    continue

                edit = EditOption('edit page', 'e', text, m.start(),
                                  disamb_page.title())
                context_option = HighlightContextOption(
                    'more context', 'm', text, 60, start=m.start(),
                    end=m.end())
                context_option.before_question = True

                options = [ListOption(self.opt.pos, ''),
                           ListOption(self.opt.pos, 'r'),
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
                                               m.start(), disamb_page)]

                options += [
                    OutputProxyOption('list', 'l',
                                      SequenceOutputter(self.opt.pos)),
                    AddAlternativeOption('add new', 'a',
                                         SequenceOutputter(self.opt.pos))]
                if edited:
                    options += [StandardOption('save in this form', 'x')]

                # TODO: Output context on each question
                answer = pywikibot.input_choice('Option', options,
                                                default=self.opt.always,
                                                force=bool(self.opt.always))
                if answer == 'x':
                    assert edited, 'invalid option before editing'
                    break

                if answer == 's':
                    n -= 1  # TODO what's this for?
                    continue

                if answer == 'e':
                    text = edit.new_text
                    edited = True
                    curpos = 0
                    continue

                if answer == 'n':
                    # skip this page
                    if self.opt.primary:
                        # If run with the -primary argument, skip this
                        # occurrence next time.
                        self.ignores.add(ref_page.title(as_url=True))
                    return 'nextpage'

                if answer == 'g':
                    return 'nextdisambig'

                # The link looks like this:
                # [[page_title|link_text]]trailing_chars
                page_title = m['title']
                link_text = m['label']

                if not link_text:
                    # or like this: [[page_title]]trailing_chars
                    link_text = page_title

                if m['section'] is None:
                    section = ''
                else:
                    section = m['section']

                trailing_chars = m['linktrail']
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

                if answer == 'u':
                    # unlink - we remove the section if there's any
                    text = text[:m.start()] + link_text + text[m.end():]
                    unlink_counter += 1
                    continue

                # else check that no option from above was missed
                assert isinstance(answer, tuple), 'only tuple answer left.'
                assert answer[0] in ['r', ''], 'only valid tuple answers.'

                if answer[0] == 'r':
                    # we want to throw away the original link text
                    replaceit = link_text == page_title
                else:
                    replaceit = include == 'redirect'

                new_page_title = answer[1]
                rep = pywikibot.Page(pywikibot.Link(new_page_title,
                                                    disamb_page.site))
                new_page_title = rep.title()
                if not (new_page_title[0].isupper()
                        or link_text[0].isupper()):
                    new_page_title = first_lower(new_page_title)

                if new_page_title not in new_targets:
                    new_targets.append(new_page_title)

                if replaceit and trailing_chars:
                    newlink = '[[{}{}]]{}'.format(new_page_title,
                                                  section,
                                                  trailing_chars)
                elif replaceit or (new_page_title == link_text
                                   and not section):
                    newlink = f'[[{new_page_title}]]'
                # check if we can create a link with trailing characters
                # instead of a pipelink
                elif (
                    (len(new_page_title) <= len(link_text))
                    and (first_upper(link_text[:len(new_page_title)])
                         == first_upper(new_page_title))
                    and (self.trailR.sub(
                        '', link_text[len(new_page_title):]) == '')
                    and (not section)
                ):
                    newlink = '[[{}]]{}'.format(
                        link_text[:len(new_page_title)],
                        link_text[len(new_page_title):])
                else:
                    newlink = '[[{}{}|{}]]'.format(new_page_title,
                                                   section, link_text)
                text = text[:m.start()] + newlink + text[m.end():]
                continue

            if text == original_text:
                pywikibot.info('\nNo changes have been made:\n')
            else:
                pywikibot.info('\nThe following changes have been made:\n')
                pywikibot.showDiff(original_text, text)
                pywikibot.info()
                # save the page
                self.setSummaryMessage(disamb_page, new_targets,
                                       unlink_counter, dn)
                try:
                    ref_page.put(text, summary=self.summary, asynchronous=True)
                except LockedPageError:
                    pywikibot.info('Page not saved: page is locked')
                except PageSaveRelatedError as error:
                    pywikibot.info(f'Page not saved: {error.args}')

        return 'done'

    def findAlternatives(self, page) -> bool:  # noqa: N802
        """Extend self.opt.pos using correctcap of disambPage.linkedPages.

        :param page: the disambiguation page
        :type page: pywikibot.Page
        :return: True if everything goes fine, False otherwise
        """
        if page.isRedirectPage() and not self.opt.primary:
            primary = i18n.translate(page.site,
                                     self.primary_redir_template)
            if primary:
                primary_page = pywikibot.Page(page.site,
                                              'Template:' + primary)
            if primary and primary_page in page.templates():
                baseTerm = page.title()
                for template, params in page.templatesWithParams():
                    if params and template == primary_page:
                        baseTerm = params[1]
                        break
                disambTitle = primary_topic_format[self.site.lang] % baseTerm
                try:
                    page2 = pywikibot.Page(
                        pywikibot.Link(disambTitle, self.site))
                    links = page2.linkedPages()
                    if self.opt.first:
                        links = self.firstize(page2, links)
                    links = [correctcap(link, page2.get())
                             for link in links]
                except NoPageError:
                    pywikibot.info(
                        f'No page at {disambTitle}, using redirect target.')
                    links = page.linkedPages()[:1]
                    links = [correctcap(link,
                                        page.get(get_redirect=True))
                             for link in links]
                self.opt.pos += links
            else:
                try:
                    target = page.getRedirectTarget().title()
                    self.opt.pos.append(target)
                except NoPageError:
                    pywikibot.info('The specified page was not found.')
                    user_input = pywikibot.input("""\
Please enter the name of the page where the redirect should have pointed at,
or press enter to quit:""")
                    if user_input == '':
                        self.quit()
                    else:
                        self.opt.pos.append(user_input)
                except IsNotRedirectPageError:
                    pywikibot.info(
                        'The specified page is not a redirect. Skipping.')
                    return False
        elif self.opt.just:
            # not page.isRedirectPage() or self.opt.primary
            try:
                if self.opt.primary:
                    try:
                        page2 = pywikibot.Page(
                            pywikibot.Link(
                                primary_topic_format[self.site.lang]
                                % page.title(),
                                self.site))
                        links = page2.linkedPages()
                        if self.opt.first:
                            links = self.firstize(page2, links)
                        links = [correctcap(link, page2.get())
                                 for link in links]
                    except NoPageError:
                        pywikibot.info(
                            'Page does not exist; using first '
                            'link in page {}.'.format(page.title()))
                        links = page.linkedPages()[:1]
                        links = [correctcap(link, page.get())
                                 for link in links]
                else:
                    try:
                        links = page.linkedPages()
                        if self.opt.first:
                            links = self.firstize(page, links)
                        links = [correctcap(link, page.get())
                                 for link in links]
                    except NoPageError:
                        pywikibot.info('Page does not exist, skipping.')
                        return False
            except IsRedirectPageError:
                pywikibot.info('Page is a redirect, skipping.')
                return False
            self.opt.pos += links
        return True

    def setSummaryMessage(
        self,
        page,
        new_targets=None,
        unlink_counter: int = 0,
        dn: bool = False
    ) -> None:
        """Setup i18n summary message."""
        new_targets = new_targets or []
        # make list of new targets
        comma = self.site.mediawiki_message('comma-separator')
        targets = comma.join(f'[[{page_title}]]'
                             for page_title in new_targets)

        if not targets:
            targets = i18n.twtranslate(self.site,
                                       'solve_disambiguation-unknown-page')

        # first check whether user has customized the edit comment
        if (self.site.family.name in config.disambiguation_comment
                and self.site.lang in config.disambiguation_comment[
                    self.site.family.name]):
            try:
                self.summary = i18n.translate(
                    self.site,
                    config.disambiguation_comment[self.site.family.name],
                    fallback=True) % (page.title(), targets)

            # Backwards compatibility, type error probably caused by too
            # many arguments for format string
            except TypeError:
                self.summary = i18n.translate(
                    self.site,
                    config.disambiguation_comment[self.site.family.name],
                    fallback=True) % page.title()
        elif page.isRedirectPage():
            # when working on redirects, there's another summary message
            if unlink_counter and not new_targets:
                self.summary = i18n.twtranslate(
                    self.site,
                    'solve_disambiguation-redirect-removed',
                    {'from': page.title(),
                     'count': unlink_counter})
            elif dn and not new_targets:
                self.summary = i18n.twtranslate(
                    self.site,
                    'solve_disambiguation-redirect-adding-dn-template',
                    {'from': page.title()})
            else:
                self.summary = i18n.twtranslate(
                    self.site, 'solve_disambiguation-redirect-resolved',
                    {'from': page.title(),
                     'to': targets,
                     'count': len(new_targets)})
        else:
            if unlink_counter and not new_targets:
                self.summary = i18n.twtranslate(
                    self.site, 'solve_disambiguation-links-removed',
                    {'from': page.title(),
                     'count': unlink_counter})
            elif dn and not new_targets:
                self.summary = i18n.twtranslate(
                    self.site, 'solve_disambiguation-adding-dn-template',
                    {'from': page.title()})
            else:
                self.summary = i18n.twtranslate(
                    self.site, 'solve_disambiguation-links-resolved',
                    {'from': page.title(),
                     'to': targets,
                     'count': len(new_targets)})

    def teardown(self) -> None:
        """Write ignoring pages to a file."""
        self.primaryIgnoreManager.ignore(self.ignores)

    def treat(self, page) -> None:
        """Work on a single disambiguation page."""
        self.primaryIgnoreManager = PrimaryIgnoreManager(
            page, enabled=self.opt.primary)

        if not self.findAlternatives(page):
            return

        pywikibot.info(f'\nAlternatives for {page}')
        self.makeAlternativesUnique()
        # sort possible choices
        if config.sort_ignore_case:
            self.opt.pos.sort(key=lambda x: x.lower())
        else:
            self.opt.pos.sort()
        SequenceOutputter(self.opt.pos).output()

        gen = ReferringPageGeneratorWithIgnore(
            page,
            self.opt.primary,
            minimum=self.opt.min,
            main_only=self.opt.main
        )
        gen = pagegenerators.PreloadingGenerator(gen)
        for ref_page in gen:
            if not self.primaryIgnoreManager.isIgnored(ref_page) \
               and not self.treat_links(ref_page, page):
                break  # next disambig

        # clear alternatives before working on next disambiguation page
        self.opt.pos = []


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    alternatives = []
    generator = None

    local_args = pywikibot.handle_args(args)
    site = pywikibot.Site()

    generator_factory = pagegenerators.GeneratorFactory(
        positional_arg_name='page')

    for argument in local_args:
        arg, _, value = argument.partition(':')
        if arg == '-primary':
            options['primary'] = True
            if value:
                options['just'] = False
                alternatives.append(value)
        elif arg == '-always':
            options['always'] = value or None
        elif arg == '-pos':
            if not value:
                continue
            if value.startswith(':'):
                alternatives.append(value)
            else:
                page = pywikibot.Page(pywikibot.Link(value, site))
                if page.exists() or pywikibot.input_yn(
                    'Possibility {} does not actually exist. Use it anyway?'
                    .format(page.title()), default=False,
                        automatic_quit=False):
                    alternatives.append(page.title())
        elif arg == '-just':
            options['just'] = False
        elif arg in ('-dnskip', '-main', '-first'):
            options[arg[1:]] = True
        elif arg == '-min':
            options['min'] = int(value or 0)
        elif arg == '-start':
            try:
                generator = pagegenerators.CategorizedPageGenerator(
                    pywikibot.Site().disambcategory(),
                    start=value, namespaces=[0])
            except NoPageError:
                pywikibot.info(
                    'Disambiguation category for your wiki is not known.')
                raise
        else:
            generator_factory.handle_arg(argument)

    generator = generator_factory.getCombinedGenerator(generator)
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return

    bot = DisambiguationRobot(generator=generator, pos=alternatives, **options)
    bot.run()


if __name__ == '__main__':
    main()
