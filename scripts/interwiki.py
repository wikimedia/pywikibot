#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Script to check language links for general pages. This works by downloading the
page, and using existing translations plus hints from the command line to
download the equivalent pages from other languages. All of such pages are
downloaded as well and checked for interwiki links recursively until there are
no more links that are encountered. A rationalization process then selects the
right interwiki links, and if this is unambiguous, the interwiki links in the
original page will be automatically updated and the modified page uploaded.

These command-line arguments can be used to specify which pages to work on:

&pagegenerators_help;

    -days:         Like -years, but runs through all date pages. Stops at
                   Dec 31.  If the argument is given in the form -days:X,
                   it will start at month no. X through Dec 31. If the
                   argument is simply given as -days, it will run from
                   Jan 1 through Dec 31.  E.g. for -days:9 it will run
                   from Sep 1 through Dec 31.

    -years:        run on all year pages in numerical order. Stop at year 2050.
                   If the argument is given in the form -years:XYZ, it
                   will run from [[XYZ]] through [[2050]]. If XYZ is a
                   negative value, it is interpreted as a year BC. If the
                   argument is simply given as -years, it will run from 1
                   through 2050.

                   This implies -noredirect.

    -new:          Work on the 100 newest pages. If given as -new:x, will work
                   on the x newest pages.
                   When multiple -namespace parameters are given, x pages are
                   inspected, and only the ones in the selected name spaces are
                   processed. Use -namespace:all for all namespaces. Without
                   -namespace, only article pages are processed.

                   This implies -noredirect.

    -restore:      restore a set of "dumped" pages the robot was working on
                   when it terminated. The dump file will be subsequently
                   removed.

    -restore:all   restore a set of "dumped" pages of all dumpfiles to a given
                   family remaining in the "interwiki-dumps" directory. All
                   these dump files will be subsequently removed. If restoring
                   process interrupts again, it saves all unprocessed pages in
                   one new dump file of the given site.

    -continue:     like restore, but after having gone through the dumped pages,
                   continue alphabetically starting at the last of the dumped
                   pages. The dump file will be subsequently removed.

    -warnfile:     used as -warnfile:filename, reads all warnings from the
                   given file that apply to the home wiki language,
                   and read the rest of the warning as a hint. Then
                   treats all the mentioned pages. A quicker way to
                   implement warnfile suggestions without verifying them
                   against the live wiki is using the warnfile.py
                   script.

Additionaly, these arguments can be used to restrict the bot to certain pages:

    -namespace:n   Number or name of namespace to process. The parameter can be
                   used multiple times. It works in combination with all other
                   parameters, except for the -start parameter. If you e.g.
                   want to iterate over all categories starting at M, use
                   -start:Category:M.

    -number:       used as -number:#, specifies that the robot should process
                   that amount of pages and then stop. This is only useful in
                   combination with -start. The default is not to stop.

    -until:        used as -until:title, specifies that the robot should
                   process pages in wiki default sort order up to, and
                   including, "title" and then stop. This is only useful in
                   combination with -start. The default is not to stop.
                   Note: do not specify a namespace, even if -start has one.

    -bracket       only work on pages that have (in the home language)
                   parenthesis in their title. All other pages are skipped.
                   (note: without ending colon)

    -skipfile:     used as -skipfile:filename, skip all links mentioned in
                   the given file. This does not work with -number!

    -skipauto      use to skip all pages that can be translated automatically,
                   like dates, centuries, months, etc.
                   (note: without ending colon)

    -lack:         used as -lack:xx with xx a language code: only work on pages
                   without links to language xx. You can also add a number nn
                   like -lack:xx:nn, so that the bot only works on pages with
                   at least nn interwiki links (the default value for nn is 1).

These arguments control miscellanous bot behaviour:

    -quiet         Use this option to get less output
                   (note: without ending colon)

    -async         Put page on queue to be saved to wiki asynchronously. This
                   enables loading pages during saving throtteling and gives a
                   better performance.
                   NOTE: For post-processing it always assumes that saving the
                   the pages was sucessful.
                   (note: without ending colon)

    -summary:      Set an additional action summary message for the edit. This
                   could be used for further explainings of the bot action.
                   This will only be used in non-autonomous mode.

    -hintsonly     The bot does not ask for a page to work on, even if none of
                   the above page sources was specified.  This will make the
                   first existing page of -hint or -hinfile slip in as the start
                   page, determining properties like namespace, disambiguation
                   state, and so on.  When no existing page is found in the
                   hints, the bot does nothing.
                   Hitting return without input on the "Which page to check:"
                   prompt has the same effect as using -hintsonly.
                   Options like -back, -same or -wiktionary are in effect only
                   after a page has been found to work on.
                   (note: without ending colon)

These arguments are useful to provide hints to the bot:

    -hint:         used as -hint:de:Anweisung to give the robot a hint
                   where to start looking for translations. If no text
                   is given after the second ':', the name of the page
                   itself is used as the title for the hint, unless the
                   -hintnobracket command line option (see there) is also
                   selected.

                   There are some special hints, trying a number of languages
                   at once:
                      * all:       All languages with at least ca. 100 articles.
                      * 10:        The 10 largest languages (sites with most
                                   articles). Analogous for any other natural
                                   number.
                      * arab:      All languages using the Arabic alphabet.
                      * cyril:     All languages that use the Cyrillic alphabet.
                      * chinese:   All Chinese dialects.
                      * latin:     All languages using the Latin script.
                      * scand:     All Scandinavian languages.

                   Names of families that forward their interlanguage links
                   to the wiki family being worked upon can be used (with
                   -family=wikipedia only), they are:
                      * commons:   Interlanguage links of Mediawiki Commons.
                      * incubator: Links in pages on the Mediawiki Incubator.
                      * meta:      Interlanguage links of named pages on Meta.
                      * species:   Interlanguage links of the wikispecies wiki.
                      * strategy:  Links in pages on Wikimedias strategy wiki.
                      * test:      Take interwiki links from Test Wikipedia

                   Languages, groups and families having the same page title
                   can be combined, as  -hint:5,scand,sr,pt,commons:New_York

    -hintfile:     similar to -hint, except that hints are taken from the given
                   file, enclosed in [[]] each, instead of the command line.

    -askhints:     for each page one or more hints are asked. See hint: above
                   for the format, one can for example give "en:something" or
                   "20:" as hint.

    -repository    Include data repository

    -same          looks over all 'serious' languages for the same title.
                   -same is equivalent to -hint:all:
                   (note: without ending colon)

    -wiktionary:   similar to -same, but will ONLY accept names that are
                   identical to the original. Also, if the title is not
                   capitalized, it will only go through other wikis without
                   automatic capitalization.

    -untranslated: works normally on pages with at least one interlanguage
                   link; asks for hints for pages that have none.

    -untranslatedonly: same as -untranslated, but pages which already have a
                   translation are skipped. Hint: do NOT use this in
                   combination with -start without a -number limit, because
                   you will go through the whole alphabet before any queries
                   are performed!

    -showpage      when asking for hints, show the first bit of the text
                   of the page always, rather than doing so only when being
                   asked for (by typing '?'). Only useful in combination
                   with a hint-asking option like -untranslated, -askhints
                   or -untranslatedonly.
                   (note: without ending colon)

    -noauto        Do not use the automatic translation feature for years and
                   dates, only use found links and hints.
                   (note: without ending colon)

    -hintnobracket used to make the robot strip everything in brackets,
                   and surrounding spaces from the page name, before it is
                   used in a -hint:xy: where the page name has been left out,
                   or -hint:all:, -hint:10:, etc. without a name, or
                   an -askhint reply, where only a language is given.

These arguments define how much user confirmation is required:

    -autonomous    run automatically, do not ask any questions. If a question
    -auto          to an operator is needed, write the name of the page
                   to autonomous_problems.dat and continue on the next page.
                   (note: without ending colon)

    -confirm       ask for confirmation before any page is changed on the
                   live wiki. Without this argument, additions and
                   unambiguous modifications are made without confirmation.
                   (note: without ending colon)

    -force         do not ask permission to make "controversial" changes,
                   like removing a language because none of the found
                   alternatives actually exists.
                   (note: without ending colon)

    -cleanup       like -force but only removes interwiki links to non-existent
                   or empty pages.

    -select        ask for each link whether it should be included before
                   changing any page. This is useful if you want to remove
                   invalid interwiki links and if you do multiple hints of
                   which some might be correct and others incorrect. Combining
                   -select and -confirm is possible, but seems like overkill.
                   (note: without ending colon)

These arguments specify in which way the bot should follow interwiki links:

    -noredirect    do not follow redirects nor category redirects.
                   (note: without ending colon)

    -initialredirect  work on its target if a redirect or category redirect is
                   entered on the command line or by a generator (note: without
                   ending colon). It is recommended to use this option with the
                   -movelog pagegenerator.

    -neverlink:    used as -neverlink:xx where xx is a language code:
                   Disregard any links found to language xx. You can also
                   specify a list of languages to disregard, separated by
                   commas.

    -ignore:       used as -ignore:xx:aaa where xx is a language code, and
                   aaa is a page title to be ignored.

    -ignorefile:   similar to -ignore, except that the pages are taken from
                   the given file instead of the command line.

    -localright    do not follow interwiki links from other pages than the
                   starting page. (Warning! Should be used very sparingly,
                   only when you are sure you have first gotten the interwiki
                   links on the starting page exactly right).
                   (note: without ending colon)

    -hintsareright do not follow interwiki links to sites for which hints
                   on existing pages are given. Note that, hints given
                   interactively, via the -askhint command line option,
                   are only effective once they have been entered, thus
                   interwiki links on the starting page are followed
                   regardess of hints given when prompted.
                   (Warning! Should be used with caution!)
                   (note: without ending colon)

    -back          only work on pages that have no backlink from any other
                   language; if a backlink is found, all work on the page
                   will be halted.  (note: without ending colon)

The following arguments are only important for users who have accounts for
multiple languages, and specify on which sites the bot should modify pages:

    -localonly     only work on the local wiki, not on other wikis in the
                   family I have a login at. (note: without ending colon)

    -limittwo      only update two pages - one in the local wiki (if logged-in)
                   and one in the top available one.
                   For example, if the local page has links to de and fr,
                   this option will make sure that only the local site and
                   the de: (larger) sites are updated. This option is useful
                   to quickly set two way links without updating all of the
                   wiki families sites.
                   (note: without ending colon)

    -whenneeded    works like limittwo, but other languages are changed in the
                   following cases:
                   * If there are no interwiki links at all on the page
                   * If an interwiki link must be removed
                   * If an interwiki link must be changed and there has been
                     a conflict for this page
                   Optionally, -whenneeded can be given an additional number
                   (for example -whenneeded:3), in which case other languages
                   will be changed if there are that number or more links to
                   change or add. (note: without ending colon)

The following arguments influence how many pages the bot works on at once:

    -array:        The number of pages the bot tries to be working on at once.
                   If the number of pages loaded is lower than this number,
                   a new set of pages is loaded from the starting wiki. The
                   default is 100, but can be changed in the config variable
                   interwiki_min_subjects

    -query:        The maximum number of pages that the bot will load at once.
                   Default value is 50.

Some configuration option can be used to change the working of this robot:

interwiki_min_subjects: the minimum amount of subjects that should be processed
                    at the same time.

interwiki_backlink: if set to True, all problems in foreign wikis will
                    be reported

interwiki_shownew:  should interwiki.py display every new link it discovers?

interwiki_graph:    output a graph PNG file on conflicts? You need pydot for
                    this: http://dkbza.org/pydot.html

interwiki_graph_format: the file format for interwiki graphs

without_interwiki:  save file with local articles without interwikis

All these options can be changed through the user-config.py configuration file.

If interwiki.py is terminated before it is finished, it will write a dump file
to the interwiki-dumps subdirectory. The program will read it if invoked with
the "-restore" or "-continue" option, and finish all the subjects in that list.
After finishing the dump file will be deleted. To run the interwiki-bot on all
pages on a language, run it with option "-start:!", and if it takes so long
that you have to break it off, use "-continue" next time.

"""
#
# (C) Rob W.W. Hooft, 2003
# (C) Daniel Herding, 2004
# (C) Yuri Astrakhan, 2005-2006
# (C) xqt, 2009-2013
# (C) Pywikipedia bot team, 2007-2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import sys
import copy
import re
import os
import time
import codecs
import pickle
import socket
import webbrowser
import pywikibot
from pywikibot import config
from pywikibot import catlib
from pywikibot import pagegenerators
from pywikibot import i18n
from pywikibot import interwiki_graph
from pywikibot import titletranslate

docuReplacements = {
    '&pagegenerators_help;': pagegenerators.parameterHelp
}


class SaveError(pywikibot.Error):
    """
    An attempt to save a page with changed interwiki has failed.
    """


class LinkMustBeRemoved(SaveError):
    """
    An interwiki link has to be removed, but this can't be done because of user
    preferences or because the user chose not to change the page.
    """


class GiveUpOnPage(pywikibot.Error):
    """
    The user chose not to work on this page and its linked pages any more.
    """


# Subpage templates. Must be in lower case,
# whereas subpage itself must be case sensitive
moved_links = {
    'ar': ([u'documentation', u'template documentation', u'شرح', u'توثيق'],
           u'/doc'),
    'bn': (u'documentation', u'/doc'),
    'ca': (u'ús de la plantilla', u'/ús'),
    'cs': (u'dokumentace',   u'/doc'),
    'da': (u'dokumentation', u'/doc'),
    'de': (u'dokumentation', u'/Meta'),
    'dsb': ([u'dokumentacija', u'doc'], u'/Dokumentacija'),
    'en': ([u'documentation', u'template documentation', u'template doc',
            u'doc', u'documentation, template'], u'/doc'),
    'es': ([u'documentación', u'documentación de plantilla'], u'/doc'),
    'eu': (u'txantiloi dokumentazioa', u'/dok'),
    'fa': ([u'documentation', u'template documentation', u'template doc',
            u'doc', u'توضیحات', u'زیرصفحه توضیحات'], u'/doc'),
    # fi: no idea how to handle this type of subpage at :Metasivu:
    'fi': (u'mallineohje', None),
    'fr': ([u'/documentation', u'documentation', u'doc_modèle',
            u'documentation modèle', u'documentation modèle compliqué',
            u'documentation modèle en sous-page',
            u'documentation modèle compliqué en sous-page',
            u'documentation modèle utilisant les parserfunctions en sous-page',
            ],
           u'/Documentation'),
    'hsb': ([u'dokumentacija', u'doc'], u'/Dokumentacija'),
    'hu': (u'sablondokumentáció', u'/doc'),
    'id': (u'template doc',  u'/doc'),
    'ilo': (u'documentation', u'/doc'),
    'ja': (u'documentation', u'/doc'),
    'ka': (u'თარგის ინფო',   u'/ინფო'),
    'ko': (u'documentation', u'/설명문서'),
    'ms': (u'documentation', u'/doc'),
    'no': (u'dokumentasjon', u'/dok'),
    'nn': (u'dokumentasjon', u'/dok'),
    'pl': (u'dokumentacja',  u'/opis'),
    'pt': ([u'documentação', u'/doc'], u'/doc'),
    'ro': (u'documentaţie',  u'/doc'),
    'ru': (u'doc', u'/doc'),
    'simple': ([u'documentation',
                u'template documentation',
                u'template doc',
                u'doc',
                u'documentation, template'], u'/doc'),
    'sk': (u'dokumentácia', u'/Dokumentácia'),
    'sv': (u'dokumentation', u'/dok'),
    'uk': ([u'документація', u'doc', u'documentation'], u'/Документація'),
    'vi': (u'documentation', u'/doc'),
    'zh': ([u'documentation', u'doc'], u'/doc'),
}

# A list of template names in different languages.
# Pages which contain these shouldn't be changed.
ignoreTemplates = {
    '_default': [u'delete'],
    'ar': [u'قيد الاستخدام'],
    'cs': [u'Pracuje_se'],
    'de': [u'inuse', 'in use', u'in bearbeitung', u'inbearbeitung',
           u'löschen', u'sla',
           u'löschantrag', u'löschantragstext',
           u'falschschreibung',
           u'obsolete schreibung', 'veraltete schreibweise'],
    'en': [u'inuse', u'softredirect'],
    'fa': [u'در دست ویرایش ۲', u'حذف سریع'],
    'pdc': [u'lösche'],
    'zh': [u'inuse'],
}


class Global(object):
    """
    Container class for global settings.
    Use of globals outside of this is to be avoided.
    """
    autonomous = False
    confirm = False
    always = False
    select = False
    followredirect = True
    initialredirect = False
    force = False
    cleanup = False
    remove = []
    maxquerysize = 50
    same = False
    skip = set()
    skipauto = False
    untranslated = False
    untranslatedonly = False
    auto = True
    neverlink = []
    showtextlink = 0
    showtextlinkadd = 300
    localonly = False
    limittwo = False
    strictlimittwo = False
    needlimit = 0
    ignore = []
    parenthesesonly = False
    rememberno = False
    followinterwiki = True
    minsubjects = config.interwiki_min_subjects
    nobackonly = False
    askhints = False
    hintnobracket = False
    hints = []
    hintsareright = False
    contentsondisk = config.interwiki_contents_on_disk
    lacklanguage = None
    minlinks = 0
    quiet = False
    restoreAll = False
    async = False
    summary = u''
    repository = False

    def readOptions(self, arg):
        """ Read all commandline parameters for the global container """
        if arg == '-noauto':
            self.auto = False
        elif arg.startswith('-hint:'):
            self.hints.append(arg[6:])
        elif arg.startswith('-hintfile'):
            hintfilename = arg[10:]
            if (hintfilename is None) or (hintfilename == ''):
                hintfilename = pywikibot.input(
                    u'Please enter the hint filename:')
            f = codecs.open(hintfilename, 'r', config.textfile_encoding)

            # hint or title ends either before | or before ]]
            R = re.compile(ur'\[\[(.+?)(?:\]\]|\|)')
            for pageTitle in R.findall(f.read()):
                self.hints.append(pageTitle)
            f.close()
        elif arg == '-force':
            self.force = True
        elif arg == '-cleanup':
            self.cleanup = True
        elif arg == '-same':
            self.same = True
        elif arg == '-wiktionary':
            self.same = 'wiktionary'
        elif arg == '-repository':
            self.repository = True
        elif arg == '-untranslated':
            self.untranslated = True
        elif arg == '-untranslatedonly':
            self.untranslated = True
            self.untranslatedonly = True
        elif arg == '-askhints':
            self.untranslated = True
            self.untranslatedonly = False
            self.askhints = True
        elif arg == '-hintnobracket':
            self.hintnobracket = True
        elif arg == '-confirm':
            self.confirm = True
        elif arg == '-select':
            self.select = True
        elif arg == '-autonomous' or arg == '-auto':
            self.autonomous = True
        elif arg == '-noredirect':
            self.followredirect = False
        elif arg == '-initialredirect':
            self.initialredirect = True
        elif arg == '-localonly':
            self.localonly = True
        elif arg == '-limittwo':
            self.limittwo = True
            self.strictlimittwo = True
        elif arg.startswith('-whenneeded'):
            self.limittwo = True
            self.strictlimittwo = False
            try:
                self.needlimit = int(arg[12:])
            except KeyError:
                pass
            except ValueError:
                pass
        elif arg.startswith('-skipfile:'):
            skipfile = arg[10:]
            skipPageGen = pagegenerators.TextfilePageGenerator(skipfile)
            for page in skipPageGen:
                self.skip.add(page)
            del skipPageGen
        elif arg == '-skipauto':
            self.skipauto = True
        elif arg.startswith('-neverlink:'):
            self.neverlink += arg[11:].split(",")
        elif arg.startswith('-ignore:'):
            self.ignore += [pywikibot.Page(None, p) for p in arg[8:].split(",")]
        elif arg.startswith('-ignorefile:'):
            ignorefile = arg[12:]
            ignorePageGen = pagegenerators.TextfilePageGenerator(ignorefile)
            for page in ignorePageGen:
                self.ignore.append(page)
            del ignorePageGen
        elif arg == '-showpage':
            self.showtextlink += self.showtextlinkadd
        elif arg == '-graph':
            # override configuration
            config.interwiki_graph = True
        elif arg == '-bracket':
            self.parenthesesonly = True
        elif arg == '-localright':
            self.followinterwiki = False
        elif arg == '-hintsareright':
            self.hintsareright = True
        elif arg.startswith('-array:'):
            self.minsubjects = int(arg[7:])
        elif arg.startswith('-query:'):
            self.maxquerysize = int(arg[7:])
        elif arg == '-back':
            self.nobackonly = True
        elif arg == '-quiet':
            self.quiet = True
        elif arg == '-async':
            self.async = True
        elif arg.startswith('-summary'):
            if len(arg) == 8:
                self.summary = pywikibot.input(
                    u'What summary do you want to use?')
            else:
                self.summary = arg[9:]
        elif arg.startswith('-lack:'):
            remainder = arg[6:].split(':')
            self.lacklanguage = remainder[0]
            if len(remainder) > 1:
                self.minlinks = int(remainder[1])
            else:
                self.minlinks = 1
        else:
            return False
        return True


class StoredPage(pywikibot.Page):
    """
    Store the Page contents on disk to avoid sucking too much
    memory when a big number of Page objects will be loaded
    at the same time.
    """

    # Please prefix the class members names by SP
    # to avoid possible name clashes with pywikibot.Page

    # path to the shelve
    SPpath = None
    # shelve
    SPstore = None

    # attributes created by pywikibot.Page.__init__
    SPcopy = ['_editrestriction',
              '_site',
              '_namespace',
              '_section',
              '_title',
              'editRestriction',
              'moveRestriction',
              '_permalink',
              '_userName',
              '_ipedit',
              '_editTime',
              '_startTime',
              '_revisionId',
              '_deletedRevs']

    def SPdeleteStore():
        if StoredPage.SPpath:
            del StoredPage.SPstore
            os.unlink(StoredPage.SPpath)
    SPdeleteStore = staticmethod(SPdeleteStore)

    def __init__(self, page):
        for attr in StoredPage.SPcopy:
            setattr(self, attr, getattr(page, attr))

        if not StoredPage.SPpath:
            import shelve
            index = 1
            while True:
                path = config.datafilepath('cache', 'pagestore' + str(index))
                if not os.path.exists(path): break
                index += 1
            StoredPage.SPpath = path
            StoredPage.SPstore = shelve.open(path)

        self.SPkey = str(self)
        self.SPcontentSet = False

    def SPgetContents(self):
        return StoredPage.SPstore[self.SPkey]

    def SPsetContents(self, contents):
        self.SPcontentSet = True
        StoredPage.SPstore[self.SPkey] = contents

    def SPdelContents(self):
        if self.SPcontentSet:
            del StoredPage.SPstore[self.SPkey]

    _contents = property(SPgetContents, SPsetContents, SPdelContents)


class PageTree(object):
    """
    Structure to manipulate a set of pages.
    Allows filtering efficiently by Site.
    """
    def __init__(self):
        # self.tree :
        # Dictionary:
        # keys: Site
        # values: list of pages
        # All pages found within Site are kept in
        # self.tree[site]

        # While using dict values would be faster for
        # the remove() operation,
        # keeping list values is important, because
        # the order in which the pages were found matters:
        # the earlier a page is found, the closer it is to the
        # Subject.originPage. Chances are that pages found within
        # 2 interwiki distance from the originPage are more related
        # to the original topic than pages found later on, after
        # 3, 4, 5 or more interwiki hops.

        # Keeping this order is hence important to display an ordered
        # list of pages to the user when he'll be asked to resolve
        # conflicts.
        self.tree = {}
        self.size = 0

    def filter(self, site):
        """
        Iterates over pages that are in Site site
        """
        try:
            for page in self.tree[site]:
                yield page
        except KeyError:
            pass

    def __len__(self):
        return self.size

    def add(self, page):
        site = page.site
        if not site in self.tree:
            self.tree[site] = []
        self.tree[site].append(page)
        self.size += 1

    def remove(self, page):
        try:
            self.tree[page.site].remove(page)
            self.size -= 1
        except ValueError:
            pass

    def removeSite(self, site):
        """
        Removes all pages from Site site
        """
        try:
            self.size -= len(self.tree[site])
            del self.tree[site]
        except KeyError:
            pass

    def siteCounts(self):
        """
        Yields (Site, number of pages in site) pairs
        """
        for site, d in self.tree.iteritems():
            yield site, len(d)

    def __iter__(self):
        for site, plist in self.tree.iteritems():
            for page in plist:
                yield page


class Subject(object):
    """
    Class to follow the progress of a single 'subject' (i.e. a page with
    all its translations)


    Subject is a transitive closure of the binary relation on Page:
    "has_a_langlink_pointing_to".

    A formal way to compute that closure would be:

    With P a set of pages, NL ('NextLevel') a function on sets defined as:
        NL(P) = { target | ∃ source ∈ P, target ∈ source.langlinks() }
    pseudocode:
        todo <- [originPage]
        done <- []
        while todo != []:
            pending <- todo
            todo <-NL(pending) / done
            done <- NL(pending) U done
        return done


    There is, however, one limitation that is induced by implementation:
    to compute efficiently NL(P), one has to load the page contents of
    pages in P.
    (Not only the langlinks have to be parsed from each Page, but we also want
     to know if the Page is a redirect, a disambiguation, etc...)

    Because of this, the pages in pending have to be preloaded.
    However, because the pages in pending are likely to be in several sites
    we cannot "just" preload them as a batch.

    Instead of doing "pending <- todo" at each iteration, we have to elect a
    Site, and we put in pending all the pages from todo that belong to that
    Site:

    Code becomes:
        todo <- {originPage.site:[originPage]}
        done <- []
        while todo != {}:
            site <- electSite()
            pending <- todo[site]

            preloadpages(site, pending)

            todo[site] <- NL(pending) / done
            done <- NL(pending) U done
        return done

    Subject objects only operate on pages that should have been preloaded
    before. In fact, at any time:
      * todo contains new Pages that have not been loaded yet
      * done contains Pages that have been loaded, and that have been treated.
      * If batch preloadings are successful, Page._get() is never called from
        this Object.
    """

    def __init__(self, originPage=None, hints=None):
        """Constructor. Takes as arguments the Page on the home wiki
           plus optionally a list of hints for translation"""

        if globalvar.contentsondisk:
            if originPage:
                originPage = StoredPage(originPage)

        # Remember the "origin page"
        self.originPage = originPage
        self.repoPage = None
        # todo is a list of all pages that still need to be analyzed.
        # Mark the origin page as todo.
        self.todo = PageTree()
        if originPage:
            self.todo.add(originPage)

        # done is a list of all pages that have been analyzed and that
        # are known to belong to this subject.
        self.done = PageTree()
        # foundIn is a dictionary where pages are keys and lists of
        # pages are values. It stores where we found each page.
        # As we haven't yet found a page that links to the origin page, we
        # start with an empty list for it.
        if originPage:
            self.foundIn = {self.originPage: []}
        else:
            self.foundIn = {}
        # This is a list of all pages that are currently scheduled for
        # download.
        self.pending = PageTree()
        if globalvar.hintsareright:
            # This is a set of sites that we got hints to
            self.hintedsites = set()
        self.translate(hints, globalvar.hintsareright)
        self.confirm = globalvar.confirm
        self.problemfound = False
        self.untranslated = None
        self.hintsAsked = False
        self.forcedStop = False
        self.workonme = True

    def getFoundDisambig(self, site):
        """
        If we found a disambiguation on the given site while working on the
        subject, this method returns it. If several ones have been found, the
        first one will be returned.
        Otherwise, None will be returned.
        """
        for tree in [self.done, self.pending]:
            for page in tree.filter(site):
                if page.exists() and page.isDisambig():
                    return page

    def getFoundNonDisambig(self, site):
        """
        If we found a non-disambiguation on the given site while working on the
        subject, this method returns it. If several ones have been found, the
        first one will be returned.
        Otherwise, None will be returned.
        """
        for tree in [self.done, self.pending]:
            for page in tree.filter(site):
                if page.exists() and not page.isDisambig() and \
                   not page.isRedirectPage() and not page.isCategoryRedirect():
                    return page

    def getFoundInCorrectNamespace(self, site):
        """
        If we found a page that has the expected namespace on the given site
        while working on the subject, this method returns it. If several ones
        have been found, the first one will be returned.
        Otherwise, None will be returned.
        """
        for tree in [self.done, self.pending, self.todo]:
            for page in tree.filter(site):
                # -hintsonly: before we have an origin page, any namespace will
                # do.
                if self.originPage and \
                   page.namespace() == self.originPage.namespace():
                    if page.exists() and not \
                       page.isRedirectPage() and not page.isCategoryRedirect():
                        return page

    def translate(self, hints=None, keephintedsites=False):
        """Add the given translation hints to the todo list"""
        if globalvar.same and self.originPage:
            if hints:
                pages = titletranslate.translate(
                    self.originPage,
                    hints=hints + ['all:'],
                    auto=globalvar.auto,
                    removebrackets=globalvar.hintnobracket)
            else:
                pages = titletranslate.translate(
                    self.originPage,
                    hints=['all:'],
                    auto=globalvar.auto,
                    removebrackets=globalvar.hintnobracket)
        else:
            pages = titletranslate.translate(
                self.originPage,
                hints=hints,
                auto=globalvar.auto,
                removebrackets=globalvar.hintnobracket,
                site=pywikibot.getSite())
        for page in pages:
            if globalvar.contentsondisk:
                page = StoredPage(page)
            self.todo.add(page)
            self.foundIn[page] = [None]
            if keephintedsites:
                self.hintedsites.add(page.site)

    def openSites(self):
        """
        Iterator. Yields (site, count) pairs:
        * site is a site where we still have work to do on
        * count is the number of items in that Site that need work on
        """
        return self.todo.siteCounts()

    def whatsNextPageBatch(self, site):
        """
        By calling this method, you 'promise' this instance that you will
        preload all the 'site' Pages that are in the todo list.

        This routine will return a list of pages that can be treated.
        """
        # Bug-check: Isn't there any work still in progress? We can't work on
        # different sites at a time!
        if len(self.pending) > 0:
            raise "BUG: Can't start to work on %s; still working on %s" \
                  % (site, self.pending)
        # Prepare a list of suitable pages
        result = []
        for page in self.todo.filter(site):
            self.pending.add(page)
            result.append(page)

        self.todo.removeSite(site)

        # If there are any, return them. Otherwise, nothing is in progress.
        return result

    def makeForcedStop(self, counter):
        """
        Ends work on the page before the normal end.
        """
        for site, count in self.todo.siteCounts():
            counter.minus(site, count)
        self.todo = PageTree()
        self.forcedStop = True

    def addIfNew(self, page, counter, linkingPage):
        """
        Adds the pagelink given to the todo list, but only if we didn't know
        it before. If it is added, update the counter accordingly.

        Also remembers where we found the page, regardless of whether it had
        already been found before or not.

        Returns True if the page is new.
        """
        if self.forcedStop:
            return False
        # cannot check backlink before we have an origin page
        if globalvar.nobackonly and self.originPage:
            if page == self.originPage:
                try:
                    pywikibot.output(u"%s has a backlink from %s."
                                     % (page, linkingPage))
                except UnicodeDecodeError:
                    pywikibot.output(u"Found a backlink for a page.")
                self.makeForcedStop(counter)
                return False

        if page in self.foundIn:
            # not new
            self.foundIn[page].append(linkingPage)
            return False
        else:
            if globalvar.contentsondisk:
                page = StoredPage(page)
            self.foundIn[page] = [linkingPage]
            self.todo.add(page)
            counter.plus(page.site)
            return True

    def skipPage(self, page, target, counter):
        return self.isIgnored(target) or \
            self.namespaceMismatch(page, target, counter) or \
            self.wiktionaryMismatch(target)

    def namespaceMismatch(self, linkingPage, linkedPage, counter):
        """
        Checks whether or not the given page has another namespace
        than the origin page.

        Returns True if the namespaces are different and the user
        has selected not to follow the linked page.
        """
        if linkedPage in self.foundIn:
            # We have seen this page before, don't ask again.
            return False
        elif self.originPage and \
             self.originPage.namespace() != linkedPage.namespace():
            # Allow for a mapping between different namespaces
            crossFrom = self.originPage.site.family.crossnamespace.get(
                self.originPage.namespace(), {})
            crossTo = crossFrom.get(self.originPage.site.language(),
                                    crossFrom.get('_default', {}))
            nsmatch = crossTo.get(linkedPage.site.language(),
                                  crossTo.get('_default', []))
            if linkedPage.namespace() in nsmatch:
                return False
            if globalvar.autonomous:
                pywikibot.output(
u"NOTE: Ignoring link from page %s in namespace %i to page %s in namespace %i."
                    % (linkingPage, linkingPage.namespace(), linkedPage,
                       linkedPage.namespace()))
                # Fill up foundIn, so that we will not write this notice
                self.foundIn[linkedPage] = [linkingPage]
                return True
            else:
                preferredPage = self.getFoundInCorrectNamespace(linkedPage.site)
                if preferredPage:
                    pywikibot.output(
u"NOTE: Ignoring link from page %s in namespace %i to page %s in namespace %i "
u"because page %s in the correct namespace has already been found."
                        % (linkingPage, linkingPage.namespace(), linkedPage,
                           linkedPage.namespace(), preferredPage))
                    return True
                else:
                    choice = pywikibot.inputChoice(
u'WARNING: %s is in namespace %i, but %s is in namespace %i. Follow it anyway?'
                        % (self.originPage, self.originPage.namespace(),
                           linkedPage, linkedPage.namespace()),
                        ['Yes', 'No', 'Add an alternative', 'give up'],
                        ['y', 'n', 'a', 'g'])
                    if choice != 'y':
                        # Fill up foundIn, so that we will not ask again
                        self.foundIn[linkedPage] = [linkingPage]
                        if choice == 'g':
                            self.makeForcedStop(counter)
                        elif choice == 'a':
                            newHint = pywikibot.input(
                                u'Give the alternative for language %s, not '
                                u'using a language code:'
                                % linkedPage.site.language())
                            if newHint:
                                alternativePage = pywikibot.Page(
                                    linkedPage.site, newHint)
                                if alternativePage:
                                    # add the page that was entered by the user
                                    self.addIfNew(alternativePage, counter,
                                                  None)
                        else:
                            pywikibot.output(
                                u"NOTE: ignoring %s and its interwiki links"
                                % linkedPage)
                        return True
        else:
            # same namespaces, no problem
            # or no origin page yet, also no problem
            return False

    def wiktionaryMismatch(self, page):
        if self.originPage and globalvar.same == 'wiktionary':
            if page.title().lower() != self.originPage.title().lower():
                pywikibot.output(u"NOTE: Ignoring %s for %s in wiktionary mode"
                                 % (page, self.originPage))
                return True
            elif page.title() != self.originPage.title() and \
                 self.originPage.site.nocapitalize and page.site.nocapitalize:
                pywikibot.output(
                    u"NOTE: Ignoring %s for %s in wiktionary mode because both "
                    u"languages are uncapitalized."
                    % (page, self.originPage))
                return True
        return False

    def disambigMismatch(self, page, counter):
        """
        Checks whether or not the given page has the another disambiguation
        status than the origin page.

        Returns a tuple (skip, alternativePage).

        skip is True if the pages have mismatching statuses and the bot
        is either in autonomous mode, or the user chose not to use the
        given page.

        alternativePage is either None, or a page that the user has
        chosen to use instead of the given page.
        """
        if not self.originPage:
            return (False, None)  # any page matches til we have an origin page
        if globalvar.autonomous:
            if self.originPage.isDisambig() and not page.isDisambig():
                pywikibot.output(
                    u"NOTE: Ignoring link from disambiguation page %s to "
                    u"non-disambiguation %s" % (self.originPage, page))
                return (True, None)
            elif not self.originPage.isDisambig() and page.isDisambig():
                pywikibot.output(
                    u"NOTE: Ignoring link from non-disambiguation page %s to "
                    u"disambiguation %s" % (self.originPage, page))
                return (True, None)
        else:
            choice = 'y'
            if self.originPage.isDisambig() and not page.isDisambig():
                disambig = self.getFoundDisambig(page.site)
                if disambig:
                    pywikibot.output(
                        u"NOTE: Ignoring non-disambiguation page %s for %s "
                        u"because disambiguation page %s has already been "
                        u"found."
                        % (page, self.originPage, disambig))
                    return (True, None)
                else:
                    choice = pywikibot.inputChoice(
                        u"WARNING: %s is a disambiguation page, but %s doesn't "
                        u"seem to be one. Follow it anyway?"
                        % (self.originPage, page),
                        ['Yes', 'No', 'Add an alternative', 'Give up'],
                        ['y', 'n', 'a', 'g'])
            elif not self.originPage.isDisambig() and page.isDisambig():
                nondisambig = self.getFoundNonDisambig(page.site)
                if nondisambig:
                    pywikibot.output(
                        u"NOTE: Ignoring disambiguation page %s for %s because "
                        u"non-disambiguation page %s has already been found."
                        % (page, self.originPage, nondisambig))
                    return (True, None)
                else:
                    choice = pywikibot.inputChoice(
                        u'WARNING: %s doesn\'t seem to be a disambiguation '
                        u'page, but %s is one. Follow it anyway?'
                        % (self.originPage, page),
                        ['Yes', 'No', 'Add an alternative', 'Give up'],
                        ['y', 'n', 'a', 'g'])
            if choice == 'n':
                return (True, None)
            elif choice == 'a':
                newHint = pywikibot.input(
                    u'Give the alternative for language %s, not using a '
                    u'language code:' % page.site.language())
                alternativePage = pywikibot.Page(page.site, newHint)
                return (True, alternativePage)
            elif choice == 'g':
                self.makeForcedStop(counter)
                return (True, None)
        # We can follow the page.
        return (False, None)

    def isIgnored(self, page):
        if page.site.language() in globalvar.neverlink:
            pywikibot.output(u"Skipping link %s to an ignored language" % page)
            return True
        if page in globalvar.ignore:
            pywikibot.output(u"Skipping link %s to an ignored page" % page)
            return True
        return False

    def reportInterwikilessPage(self, page):
        if not globalvar.quiet:
            pywikibot.output(u"NOTE: %s does not have any interwiki links"
                             % self.originPage)
        if config.without_interwiki:
            f = codecs.open(
                pywikibot.config.datafilepath('without_interwiki.txt'),
                'a', 'utf-8')
            f.write(u"# %s \n" % page)
            f.close()

    def askForHints(self, counter):
        if not self.workonme:
            # Do not ask hints for pages that we don't work on anyway
            return
        if (self.untranslated or globalvar.askhints) and not self.hintsAsked \
           and self.originPage and self.originPage.exists() \
           and not self.originPage.isRedirectPage() and \
           not self.originPage.isCategoryRedirect():
            # Only once!
            self.hintsAsked = True
            if globalvar.untranslated:
                newhint = None
                t = globalvar.showtextlink
                if t:
                    pywikibot.output(self.originPage.get()[:t])
                # loop
                while True:
                    newhint = pywikibot.input(
                        u'Give a hint (? to see pagetext):')
                    if newhint == '?':
                        t += globalvar.showtextlinkadd
                        pywikibot.output(self.originPage.get()[:t])
                    elif newhint and not ':' in newhint:
                        pywikibot.output(
                            u'Please enter a hint in the format '
                            u'language:pagename or type nothing if you do not '
                            u'have a hint.')
                    elif not newhint:
                        break
                    else:
                        pages = titletranslate.translate(
                            self.originPage,
                            hints=[newhint],
                            auto=globalvar.auto,
                            removebrackets=globalvar.hintnobracket)
                        for page in pages:
                            self.addIfNew(page, counter, None)
                            if globalvar.hintsareright:
                                self.hintedsites.add(page.site)

    def batchLoaded(self, counter):
        """
        This is called by a worker to tell us that the promised batch of
        pages was loaded.
        In other words, all the pages in self.pending have already
        been preloaded.

        The only argument is an instance of a counter class, that has methods
        minus() and plus() to keep counts of the total work todo.

        """
        # Loop over all the pages that should have been taken care of
        for page in self.pending:
            # Mark the page as done
            self.done.add(page)

            # make sure that none of the linked items is an auto item
            if globalvar.skipauto:
                dictName, year = page.autoFormat()
                if dictName is not None:
                    if self.originPage:
                        pywikibot.output(
                            u'WARNING: %s:%s relates to %s:%s, which is an '
                            u'auto entry %s(%s)'
                            % (self.originPage.site.language(), self.originPage,
                               page.site.language(), page, dictName, year))

                    # Abort processing if the bot is running in autonomous mode.
                    if globalvar.autonomous:
                        self.makeForcedStop(counter)

            # Register this fact at the todo-counter.
            counter.minus(page.site)

            # Now check whether any interwiki links should be added to the
            # todo list.

            if not page.exists():
                globalvar.remove.append(unicode(page))
                if not globalvar.quiet:
                    pywikibot.output(u"NOTE: %s does not exist. Skipping."
                                     % page)
                if page == self.originPage:
                    # The page we are working on is the page that does not
                    # exist. No use in doing any work on it in that case.
                    for site, count in self.todo.siteCounts():
                        counter.minus(site, count)
                    self.todo = PageTree()
                    # In some rare cases it might be we already did check some
                    # 'automatic' links
                    self.done = PageTree()
                continue

            elif page.isRedirectPage() or page.isCategoryRedirect():
                if page.isRedirectPage():
                    redir = u''
                else:
                    redir = u'category '
                if page.isRedirectPage():
                    redirectTargetPage = page.getRedirectTarget()
                else:
                    redirectTargetPage = page.getCategoryRedirectTarget()
                if not globalvar.quiet:
                    pywikibot.output(u"NOTE: %s is %sredirect to %s"
                                     % (page, redir, redirectTargetPage))
                if self.originPage is None or page == self.originPage:
                    # the 1st existig page becomes the origin page, if none was
                    # supplied
                    if globalvar.initialredirect:
                        if globalvar.contentsondisk:
                            redirectTargetPage = StoredPage(redirectTargetPage)
                        # don't follow another redirect; it might be a self loop
                        if not redirectTargetPage.isRedirectPage() \
                           and not redirectTargetPage.isCategoryRedirect():
                            self.originPage = redirectTargetPage
                            self.todo.add(redirectTargetPage)
                            counter.plus(redirectTargetPage.site)
                    else:
                        # This is a redirect page to the origin. We don't need
                        # to follow the redirection.
                        # In this case we can also stop all hints!
                        for site, count in self.todo.siteCounts():
                            counter.minus(site, count)
                        self.todo = PageTree()
                elif not globalvar.followredirect:
                    if not globalvar.quiet:
                        pywikibot.output(u"NOTE: not following %sredirects."
                                         % redir)
                elif page.isStaticRedirect():
                    if not globalvar.quiet:
                        pywikibot.output(
                            u"NOTE: not following static %sredirects." % redir)
                elif page.site.family == redirectTargetPage.site.family \
                    and not self.skipPage(page, redirectTargetPage, counter):
                    if self.addIfNew(redirectTargetPage, counter, page):
                        if config.interwiki_shownew:
                            pywikibot.output(u"%s: %s gives new %sredirect %s"
                                             % (self.originPage, page, redir,
                                                redirectTargetPage))
                continue

            # must be behind the page.isRedirectPage() part
            # otherwise a redirect error would be raised
            elif page.isEmpty() and not page.isCategory():
                globalvar.remove.append(unicode(page))
                if not globalvar.quiet:
                    pywikibot.output(u"NOTE: %s is empty. Skipping." % page)
                if page == self.originPage:
                    for site, count in self.todo.siteCounts():
                        counter.minus(site, count)
                    self.todo = PageTree()
                    self.done = PageTree()
                    self.originPage = None
                continue

            elif page.section():
                if not globalvar.quiet:
                    pywikibot.output(u"NOTE: %s is a page section. Skipping."
                                     % page)
                continue

            # Page exists, isnt a redirect, and is a plain link (no section)
            if self.originPage is None:
                # the 1st existig page becomes the origin page, if none was
                # supplied
                self.originPage = page
            try:
                iw = page.langlinks()
            except pywikibot.NoSuchSite:
                if not globalvar.quiet:
                    pywikibot.output(u"NOTE: site %s does not exist."
                                     % page.site)
                continue

            (skip, alternativePage) = self.disambigMismatch(page, counter)
            if skip:
                pywikibot.output(u"NOTE: ignoring %s and its interwiki links"
                                 % page)
                self.done.remove(page)
                iw = ()
                if alternativePage:
                    # add the page that was entered by the user
                    self.addIfNew(alternativePage, counter, None)

            duplicate = None
            for p in self.done.filter(page.site):
                if p != page and p.exists() and \
                   not p.isRedirectPage() and not p.isCategoryRedirect():
                    duplicate = p
                    break

            if self.originPage == page:
                self.untranslated = (len(iw) == 0)
                if globalvar.untranslatedonly:
                    # Ignore the interwiki links.
                    iw = ()
                if globalvar.lacklanguage:
                    if globalvar.lacklanguage in [link.site.language()
                                                  for link in iw]:
                        iw = ()
                        self.workonme = False
                if len(iw) < globalvar.minlinks:
                    iw = ()
                    self.workonme = False

            elif globalvar.autonomous and duplicate and not skip:
                pywikibot.output(u"Stopping work on %s because duplicate pages"
                                 " %s and %s are found"
                                 % (self.originPage, duplicate, page))
                self.makeForcedStop(counter)
                try:
                    f = codecs.open(
                            pywikibot.config.datafilepath('autonomous_problems.dat'),
                            'a', 'utf-8')
                    f.write(u"* %s {Found more than one link for %s}"
                            % (self.originPage, page.site))
                    if config.interwiki_graph and config.interwiki_graph_url:
                        filename = interwiki_graph.getFilename(self.originPage, extension = config.interwiki_graph_formats[0])
                        f.write(u" [%s%s graph]" % (config.interwiki_graph_url, filename))
                    f.write("\n")
                    f.close()
                # FIXME: What errors are we catching here?
                # except: should be avoided!!
                except:
                   #raise
                   pywikibot.output(u'File autonomous_problems.dat open or corrupted! Try again with -restore.')
                   sys.exit()
                iw = ()
            elif page.isEmpty() and not page.isCategory():
                globalvar.remove.append(unicode(page))
                if not globalvar.quiet:
                    pywikibot.output(u"NOTE: %s is empty; ignoring it and its interwiki links"
                                     % page)
                # Ignore the interwiki links
                self.done.remove(page)
                iw = ()

            for link in iw:
                linkedPage = pywikibot.Page(link)
                if globalvar.hintsareright:
                    if linkedPage.site in self.hintedsites:
                        pywikibot.output(u"NOTE: %s: %s extra interwiki on hinted site ignored %s"
                                         % (self.originPage, page, linkedPage))
                        break
                if not self.skipPage(page, linkedPage, counter):
                    if globalvar.followinterwiki or page == self.originPage:
                        if self.addIfNew(linkedPage, counter, page):
                            # It is new. Also verify whether it is the second on the
                            # same site
                            lpsite=linkedPage.site
                            for prevPage in self.foundIn:
                                if prevPage != linkedPage and prevPage.site == lpsite:
                                    # Still, this could be "no problem" as either may be a
                                    # redirect to the other. No way to find out quickly!
                                    pywikibot.output(u"NOTE: %s: %s gives duplicate interwiki on same site %s"
                                                     % (self.originPage, page,
                                                        linkedPage))
                                    break
                            else:
                                if config.interwiki_shownew:
                                    pywikibot.output(u"%s: %s gives new interwiki %s"
                                                     % (self.originPage,
                                                        page, linkedPage))
                if self.forcedStop:
                    break
        # These pages are no longer 'in progress'
        self.pending = PageTree()
        # Check whether we need hints and the user offered to give them
        if self.untranslated and not self.hintsAsked:
            self.reportInterwikilessPage(page)
        self.askForHints(counter)

    def isDone(self):
        """Return True if all the work for this subject has completed."""
        return len(self.todo) == 0

    def problem(self, txt, createneed = True):
        """Report a problem with the resolution of this subject."""
        pywikibot.output(u"ERROR: %s" % txt)
        self.confirm = True
        if createneed:
            self.problemfound = True

    def whereReport(self, page, indent=4):
        for page2 in sorted(self.foundIn[page]):
            if page2 is None:
                pywikibot.output(u" "*indent + "Given as a hint.")
            else:
                pywikibot.output(u" "*indent + unicode(page2))


    def assemble(self):
        # No errors have been seen so far, except....
        errorCount = self.problemfound
        mysite = pywikibot.getSite()
        # Build up a dictionary of all pages found, with the site as key.
        # Each value will be a list of pages.
        new = {}
        for page in self.done:
            if page.exists() and not page.isRedirectPage() and not page.isCategoryRedirect():
                site = page.site
                if site.family.interwiki_forward:
                    #TODO: allow these cases to be propagated!
                    continue # inhibit the forwarding families pages to be updated.
                if site == self.originPage.site:
                    if page != self.originPage:
                        self.problem(u"Found link to %s" % page)
                        self.whereReport(page)
                        errorCount += 1
                else:
                    if site in new:
                        new[site].append(page)
                    else:
                        new[site] = [page]
        # See if new{} contains any problematic values
        result = {}
        for site, pages in new.iteritems():
            if len(pages) > 1:
                errorCount += 1
                self.problem(u"Found more than one link for %s" % site)

        if not errorCount and not globalvar.select:
            # no errors, so all lists have only one item
            for site, pages in new.iteritems():
                result[site] = pages[0]
            return result

        # There are any errors.
        if config.interwiki_graph:
            graphDrawer = interwiki_graph.GraphDrawer(self)
            graphDrawer.createGraph()

        # We don't need to continue with the rest if we're in autonomous
        # mode.
        if globalvar.autonomous:
            return None

        # First loop over the ones that have more solutions
        for site, pages in new.iteritems():
            if len(pages) > 1:
                pywikibot.output(u"=" * 30)
                pywikibot.output(u"Links to %s" % site)
                i = 0
                for page2 in pages:
                    i += 1
                    pywikibot.output(u"  (%d) Found link to %s in:"
                                     % (i, page2))
                    self.whereReport(page2, indent = 8)
                while True:
                    #TODO: allow answer to repeat previous or go back after a mistake
                    answer = pywikibot.input(u"Which variant should be used? (<number>, [n]one, [g]ive up) ").lower()
                    if answer:
                        if answer == 'g':
                            return None
                        elif answer == 'n':
                            # None acceptable
                            break
                        elif answer.isdigit():
                            answer = int(answer)
                            try:
                                result[site] = pages[answer - 1]
                            except IndexError:
                                # user input is out of range
                                pass
                            else:
                                break
        # Loop over the ones that have one solution, so are in principle
        # not a problem.
        acceptall = False
        for site, pages in new.iteritems():
            if len(pages) == 1:
                if not acceptall:
                    pywikibot.output(u"=" * 30)
                    page2 = pages[0]
                    pywikibot.output(u"Found link to %s in:" % page2)
                    self.whereReport(page2, indent = 4)
                while True:
                    if acceptall:
                        answer = 'a'
                    else:
                        #TODO: allow answer to repeat previous or go back after a mistake
                        answer = pywikibot.inputChoice(u'What should be done?', ['accept', 'reject', 'give up', 'accept all'], ['a', 'r', 'g', 'l'], 'a')
                    if answer == 'l':  # accept all
                        acceptall = True
                        answer = 'a'
                    if answer == 'a':  # accept this one
                        result[site] = pages[0]
                        break
                    elif answer == 'g':  # give up
                        return None
                    elif answer == 'r':  # reject
                        # None acceptable
                        break
        return result

    def finish(self):
        """Round up the subject, making any necessary changes. This method
           should be called exactly once after the todo list has gone empty.

        """

        #from clean_sandbox
        def minutesDiff(time1, time2):
            if type(time1) is long:
                time1 = str(time1)
            if type(time2) is long:
                time2 = str(time2)
            t1 = (((int(time1[0:4]) * 12 + int(time1[4:6])) * 30 +
                   int(time1[6:8])) * 24 + int(time1[8:10])) * 60 + \
                   int(time1[10:12])
            t2 = (((int(time2[0:4]) * 12 + int(time2[4:6])) * 30 +
                   int(time2[6:8])) * 24 + int(time2[8:10])) * 60 + \
                   int(time2[10:12])
            return abs(t2 - t1)

        if not self.isDone():
            raise "Bugcheck: finish called before done"
        if not self.workonme:
            return
        if self.originPage:
            if self.originPage.isRedirectPage():
                return
            if self.originPage.isCategoryRedirect():
                return
        else:
            return
        if not self.untranslated and globalvar.untranslatedonly:
            return
        if self.forcedStop: # autonomous with problem
            pywikibot.output(u"======Aborted processing %s======"
                             % self.originPage)
            return
        # The following check is not always correct and thus disabled.
        # self.done might contain no interwiki links because of the -neverlink
        # argument or because of disambiguation conflicts.
#         if len(self.done) == 1:
#             # No interwiki at all
#             return
        pywikibot.output(u"======Post-processing %s======" % self.originPage)
        # Assemble list of accepted interwiki links
        new = self.assemble()
        if new is None:  # User said give up
            pywikibot.output(u"======Aborted processing %s======"
                             % self.originPage)
            return

        # Make sure new contains every page link, including the page we are processing
        # TODO: should be move to assemble()
        # replaceLinks will skip the site it's working on.
        if self.originPage.site not in new:
            #TODO: make this possible as well.
            if not self.originPage.site.family.interwiki_forward:
                new[self.originPage.site] = self.originPage

        #self.replaceLinks(self.originPage, new, True)

        updatedSites = []
        notUpdatedSites = []
        # Process all languages here
        globalvar.always = False
        if globalvar.limittwo:
            lclSite = self.originPage.site
            lclSiteDone = False
            frgnSiteDone = False

            for siteCode in lclSite.family.languages_by_size:
                site = pywikibot.getSite(siteCode)
                if (not lclSiteDone and site == lclSite) or \
                   (not frgnSiteDone and site != lclSite and site in new):
                    if site == lclSite:
                        lclSiteDone = True   # even if we fail the update
                    if site.family.name in config.usernames and site.lang in config.usernames[site.family.name]:
                        try:
                            if self.replaceLinks(new[site], new):
                                updatedSites.append(site)
                            if site != lclSite:
                                frgnSiteDone = True
                        except SaveError:
                            notUpdatedSites.append(site)
                        except GiveUpOnPage:
                            break
                elif not globalvar.strictlimittwo and site in new \
                     and site != lclSite:
                    old = {}
                    try:
                        for link in new[site].iterlanglinks():
                            page = pywikibot.Page(link)
                            old[page.site] = page
                    except pywikibot.NoPage:
                        pywikibot.output(u"BUG>>> %s no longer exists?"
                                         % new[site])
                        continue
                    mods, mcomment, adding, removing, modifying \
                          = compareLanguages(old, new, insite=lclSite)
                    if (len(removing) > 0 and not globalvar.autonomous) or \
                       (len(modifying) > 0 and self.problemfound) or \
                       len(old) == 0 or \
                       (globalvar.needlimit and
                        len(adding) + len(modifying) >= globalvar.needlimit + 1):
                        try:
                            if self.replaceLinks(new[site], new):
                                updatedSites.append(site)
                        except SaveError:
                            notUpdatedSites.append(site)
                        except pywikibot.NoUsername:
                            pass
                        except GiveUpOnPage:
                            break
        else:
            for (site, page) in new.iteritems():
                # edit restriction for some templates on zh-wiki where
                # interlanguage keys are included by /doc subpage
                smallWikiAllowed = not (page.site.sitename() == 'wikipedia:zh'
                                        and page.namespace() == 10 and
                                        u'Country data' in page.title(withNamespace=False))
                # edit restriction on is-wiki
                # http://is.wikipedia.org/wiki/Wikipediaspjall:V%C3%A9lmenni
                # and zh-wiki for template namespace which prevents increasing the queue
                # allow edits for the same conditions as -whenneeded
                # or the last edit wasn't a bot
                # or the last edit was 1 month ago
                if smallWikiAllowed and globalvar.autonomous and \
                   (page.site.sitename() == 'wikipedia:is' or
                    page.site.sitename() == 'wikipedia:zh' and
                    page.namespace() == 10):
                    old = {}
                    try:
                        for mypage in new[page.site].interwiki():
                            old[mypage.site] = mypage
                    except pywikibot.NoPage:
                        pywikibot.output(u"BUG>>> %s no longer exists?"
                                         % new[site])
                        continue
                    mods, mcomment, adding, removing, modifying \
                          = compareLanguages(old, new, insite=site)
                    #cannot create userlib.User with IP
                    smallWikiAllowed = page.isIpEdit() or \
                                       len(removing) > 0 or len(old) == 0 or \
                                       len(adding) + len(modifying) > 2 or \
                                       len(removing) + len(modifying) == 0 and \
                                       adding == [page.site]
                    if not smallWikiAllowed:
                        import userlib
                        user = userlib.User(page.site, page.userName())
                        if not 'bot' in user.groups() \
                           and not 'bot' in page.userName().lower(): #erstmal auch keine namen mit bot
                            smallWikiAllowed = True
                        else:
                            diff = minutesDiff(page.editTime(),
                                               time.strftime("%Y%m%d%H%M%S",
                                                             time.gmtime()))
                            if diff > 30 * 24 * 60:
                                smallWikiAllowed = True
                            else:
                                pywikibot.output(
u'NOTE: number of edits are restricted at %s'
                                    % page.site.sitename())

                # if we have an account for this site
                if site.family.name in config.usernames and \
                   site.lang in config.usernames[site.family.name] and \
                   smallWikiAllowed and \
                   not site.has_transcluded_data:
                    # Try to do the changes
                    try:
                        if self.replaceLinks(page, new):
                            # Page was changed
                            updatedSites.append(site)
                    except SaveError:
                        notUpdatedSites.append(site)
                    except GiveUpOnPage:
                        break

        # disabled graph drawing for minor problems: it just takes too long
        #if notUpdatedSites != [] and config.interwiki_graph:
        #    # at least one site was not updated, save a conflict graph
        #    self.createGraph()

        # don't report backlinks for pages we already changed
        if config.interwiki_backlink:
            self.reportBacklinks(new, updatedSites)

    def clean(self):
        """
        Delete the contents that are stored on disk for this Subject.

        We cannot afford to define this in a StoredPage destructor because
        StoredPage instances can get referenced cyclicly: that would stop the
        garbage collector from destroying some of those objects.

        It's also not necessary to set these lines as a Subject destructor:
        deleting all stored content one entry by one entry when bailing out
        after a KeyboardInterrupt for example is redundant, because the
        whole storage file will be eventually removed.
        """
        if globalvar.contentsondisk:
            for page in self.foundIn:
                # foundIn can contain either Page or StoredPage objects
                # calling the destructor on _contents will delete the
                # disk records if necessary
                if hasattr(page, '_contents'):
                    del page._contents

    def replaceLinks(self, page, newPages):
        """
        Returns True if saving was successful.
        """
        if globalvar.localonly:
            # In this case only continue on the Page we started with
            if page != self.originPage:
                raise SaveError(u'-localonly and page != originPage')
        if page.section():
            # This is not a page, but a subpage. Do not edit it.
            pywikibot.output(u"Not editing %s: not doing interwiki on subpages"
                             % page)
            raise SaveError(u'Link has a #section')
        try:
            pagetext = page.get()
        except pywikibot.NoPage:
            pywikibot.output(u"Not editing %s: page does not exist" % page)
            raise SaveError(u'Page doesn\'t exist')
        if page.isEmpty() and not page.isCategory():
            pywikibot.output(u"Not editing %s: page is empty" % page)
            raise SaveError

        # clone original newPages dictionary, so that we can modify it to the
        # local page's needs
        new = newPages.copy()
        interwikis = [pywikibot.Page(l) for l in page.iterlanglinks()]

        # remove interwiki links to ignore
        for iw in re.finditer('<!-- *\[\[(.*?:.*?)\]\] *-->', pagetext):
            try:
                ignorepage = pywikibot.Page(page.site, iw.groups()[0])
            except (pywikibot.NoSuchSite, ):
                continue
            try:
                if (new[ignorepage.site] == ignorepage) and \
                   (ignorepage.site != page.site):
                    if (ignorepage not in interwikis):
                        pywikibot.output(
                            u"Ignoring link to %(to)s for %(from)s"
                            % {'to': ignorepage,
                               'from': page})
                        new.pop(ignorepage.site)
                    else:
                        pywikibot.output(
                            u"NOTE: Not removing interwiki from %(from)s to %(to)s (exists both commented and non-commented)"
                            % {'to': ignorepage,
                               'from': page})
            except KeyError:
                pass

        # sanity check - the page we are fixing must be the only one for that
        # site.
        pltmp = new[page.site]
        if pltmp != page:
            s = u"None"
            if pltmp is not None: s = pltmp
            pywikibot.output(
                u"BUG>>> %s is not in the list of new links! Found %s."
                % (page, s))
            raise SaveError(u'BUG: sanity check failed')

        # Avoid adding an iw link back to itself
        del new[page.site]
        # Do not add interwiki links to foreign families that page.site() does not forward to
        for stmp in new.keys():
            if stmp.family != page.site.family:
                if stmp.family.name != page.site.family.interwiki_forward:
                    del new[stmp]

        # Put interwiki links into a map
        old = {}
        for page2 in interwikis:
            old[page2.site] = page2

        # Check what needs to get done
        mods, mcomment, adding, removing, modifying = compareLanguages(old,
                                                                       new,
                                                                       insite=page.site)

        # When running in autonomous mode without -force switch, make sure we
        # don't remove any items, but allow addition of the new ones
        if globalvar.autonomous and not globalvar.force and len(removing) > 0:
            for rmsite in removing:
                # Sometimes sites have an erroneous link to itself as an
                # interwiki
                if rmsite == page.site:
                    continue
                rmPage = old[rmsite]
                #put it to new means don't delete it
                if not globalvar.cleanup or \
                   unicode(rmPage) not in globalvar.remove or \
                   rmPage.site.sitename() == 'wikipedia:hi' and \
                   page.site.sitename() != 'wikipedia:de': #work-arround for bug #3081100 (do not remove hi-pages)
                    new[rmsite] = rmPage
                    pywikibot.output(
                        u"WARNING: %s is either deleted or has a mismatching disambiguation state."
                        % rmPage)
            # Re-Check what needs to get done
            mods, mcomment, adding, removing, modifying = compareLanguages(old,
                                                                           new,
                                                                           insite=page.site)
        if not mods:
            if not globalvar.quiet:
                pywikibot.output(u'No changes needed on page %s' % page)
            return False

        # Show a message in purple.
        pywikibot.output(
            u"\03{lightpurple}Updating links on page %s.\03{default}" % page)
        pywikibot.output(u"Changes to be made: %s" % mods)
        oldtext = page.get()
        template = (page.namespace() == 10)
        newtext = pywikibot.replaceLanguageLinks(oldtext, new,
                                                 site=page.site,
                                                 template=template)
        # This is for now. Later there should be different funktions for each
        # kind
        if not botMayEdit(page):
            if template:
                pywikibot.output(
                    u'SKIPPING: %s should have interwiki links on subpage.'
                    % page)
            else:
                pywikibot.output(
                    u'SKIPPING: %s is under construction or to be deleted.'
                    % page)
            return False
        if newtext == oldtext:
            return False
        pywikibot.showDiff(oldtext, newtext)

        # pywikibot.output(u"NOTE: Replace %s" % page)
        # Determine whether we need permission to submit
        ask = False

        # Allow for special case of a self-pointing interwiki link
        if removing and removing != [page.site]:
            self.problem(u'Found incorrect link to %s in %s'
                         % (", ".join([x.lang for x in removing]), page),
                         createneed=False)
            ask = True
        if globalvar.force or globalvar.cleanup:
            ask = False
        if globalvar.confirm and not globalvar.always:
            ask = True
        # If we need to ask, do so
        if ask:
            if globalvar.autonomous:
                # If we cannot ask, deny permission
                answer = 'n'
            else:
                answer = pywikibot.inputChoice(u'Submit?',
                                               ['Yes', 'No', 'open in Browser',
                                                'Give up', 'Always'],
                                               ['y', 'n', 'b', 'g', 'a'])
                if answer == 'b':
                    webbrowser.open("http://%s%s" % (
                        page.site.hostname(),
                        page.site.nice_get_address(page.title())
                    ))
                    pywikibot.input(u"Press Enter when finished in browser.")
                    return True
                elif answer == 'a':
                    # don't ask for the rest of this subject
                    globalvar.always = True
                    answer = 'y'
        else:
            # If we do not need to ask, allow
            answer = 'y'
        # If we got permission to submit, do so
        if answer == 'y':
            if not globalvar.quiet:
                pywikibot.output(u"NOTE: Updating live wiki...")
            timeout=60
            while True:
                try:
                    if globalvar.async:
                        page.put_async(newtext, comment=mcomment)
                        status = 302
                    else:
                        status, reason, data = page.put(newtext, comment=mcomment)
                except pywikibot.LockedPage:
                    pywikibot.output(u'Page %s is locked. Skipping.' % page)
                    raise SaveError(u'Locked')
                except pywikibot.EditConflict:
                    pywikibot.output(
                        u'ERROR putting page: An edit conflict occurred. Giving up.')
                    raise SaveError(u'Edit conflict')
                except (pywikibot.SpamfilterError), error:
                    pywikibot.output(
                        u'ERROR putting page: %s blacklisted by spamfilter. Giving up.'
                        % (error.url,))
                    raise SaveError(u'Spam filter')
                except (pywikibot.PageNotSaved), error:
                    pywikibot.output(u'ERROR putting page: %s' % (error.args,))
                    raise SaveError(u'PageNotSaved')
                except (socket.error, IOError), error:
                    if timeout>3600:
                        raise
                    pywikibot.output(u'ERROR putting page: %s' % (error.args,))
                    pywikibot.output(u'Sleeping %i seconds before trying again.'
                                     % (timeout,))
                    timeout *= 2
                    time.sleep(timeout)
                except pywikibot.ServerError:
                    if timeout > 3600:
                        raise
                    pywikibot.output(u'ERROR putting page: ServerError.')
                    pywikibot.output(u'Sleeping %i seconds before trying again.'
                                     % (timeout,))
                    timeout *= 2
                    time.sleep(timeout)
                else:
                    break
            if str(status) == '302':
                return True
            else:
                pywikibot.output(u'%s %s' % (status, reason))
                return False
        elif answer == 'g':
            raise GiveUpOnPage(u'User asked us to give up')
        else:
            raise LinkMustBeRemoved(u'Found incorrect link to %s in %s'
                                    % (", ".join([x.lang for x in removing]),
                                       page))

    def reportBacklinks(self, new, updatedSites):
        """
        Report missing back links. This will be called from finish() if needed.

        updatedSites is a list that contains all sites we changed, to avoid
        reporting of missing backlinks for pages we already fixed

        """
        # use sets because searching an element is faster than in lists
        expectedPages = set(new.itervalues())
        expectedSites = set(new)
        try:
            for site in expectedSites - set(updatedSites):
                page = new[site]
                if not page.section():
                    try:
                        linkedPages = set(pywikibot.Page(l) for l in page.iterlanglinks())
                    except pywikibot.NoPage:
                        pywikibot.output(
                            u"WARNING: Page %s does no longer exist?!" % page)
                        break
                    # To speed things up, create a dictionary which maps sites
                    # to pages. This assumes that there is only one interwiki
                    # link per language.
                    linkedPagesDict = {}
                    for linkedPage in linkedPages:
                        linkedPagesDict[linkedPage.site] = linkedPage
                    for expectedPage in expectedPages - linkedPages:
                        if expectedPage != page:
                            try:
                                linkedPage = linkedPagesDict[expectedPage.site]
                                pywikibot.output(
                                    u"WARNING: %s: %s does not link to %s but to %s"
                                    % (page.site.family.name,
                                       page, expectedPage, linkedPage))
                            except KeyError:
                                if not expectedPage.site.is_data_repository():
                                    pywikibot.output(
                                        u"WARNING: %s: %s does not link to %s"
                                        % (page.site.family.name,
                                           page, expectedPage))
                    # Check for superfluous links
                    for linkedPage in linkedPages:
                        if linkedPage not in expectedPages:
                            # Check whether there is an alternative page on that language.
                            # In this case, it was already reported above.
                            if linkedPage.site not in expectedSites:
                                pywikibot.output(
                                    u"WARNING: %s: %s links to incorrect %s"
                                    % (page.site.family.name,
                                       page, linkedPage))
        except (socket.error, IOError):
            pywikibot.output(u'ERROR: could not report backlinks')


class InterwikiBot(object):
    """A class keeping track of a list of subjects, controlling which pages
       are queried from which languages when."""

    def __init__(self):
        """Constructor. We always start with empty lists."""
        self.subjects = []
        # We count how many pages still need to be loaded per site.
        # This allows us to find out from which site to retrieve pages next
        # in a way that saves bandwidth.
        # sites are keys, integers are values.
        # Modify this only via plus() and minus()!
        self.counts = {}
        self.pageGenerator = None
        self.generated = 0

    def add(self, page, hints=None):
        """Add a single subject to the list"""
        subj = Subject(page, hints=hints)
        self.subjects.append(subj)
        for site, count in subj.openSites():
            # Keep correct counters
            self.plus(site, count)

    def setPageGenerator(self, pageGenerator, number=None, until=None):
        """Add a generator of subjects. Once the list of subjects gets
           too small, this generator is called to produce more Pages"""
        self.pageGenerator = pageGenerator
        self.generateNumber = number
        self.generateUntil = until

    def dump(self, append=True):
        site = pywikibot.getSite()
        dumpfn = pywikibot.config.datafilepath(
                     'data',
                     'interwiki-dumps',
                     '%s-%s.pickle' % (site.family.name, site.lang))
        if append:
            mode = 'appended'
        else:
            mode = 'written'
        f = open(dumpfn, mode[0])
        titles = [s.originPage.title() for s in self.subjects]
        pickle.dump(titles, f)
        f.close()
        pywikibot.output(u'Dump %s (%s) %s.' % (site.lang, site.family.name, mode))
        return dumpfn

    def generateMore(self, number):
        """Generate more subjects. This is called internally when the
           list of subjects becomes too small, but only if there is a
           PageGenerator"""
        fs = self.firstSubject()
        if fs and (not globalvar.quiet):
            pywikibot.output(u"NOTE: The first unfinished subject is %s"
                             % fs.originPage)
        pywikibot.output(u"NOTE: Number of pages queued is %d, trying to add %d more."
                         % (len(self.subjects), number))
        for i in xrange(number):
            try:
                while True:
                    try:
                        page = self.pageGenerator.next()
                    except IOError:
                        pywikibot.output(u'IOError occured; skipping')
                        continue
                    if page in globalvar.skip:
                        pywikibot.output(u'Skipping: %s is in the skip list' % page)
                        continue
                    if globalvar.skipauto:
                        dictName, year = page.autoFormat()
                        if dictName is not None:
                            pywikibot.output(u'Skipping: %s is an auto entry %s(%s)' % (page, dictName, year))
                            continue
                    if globalvar.parenthesesonly:
                        # Only yield pages that have ( ) in titles
                        if "(" not in page.title():
                            continue
                    if page.isTalkPage():
                        pywikibot.output(u'Skipping: %s is a talk page' % page)
                        continue
                    #doesn't work: page must be preloaded for this test
                    #if page.isEmpty():
                    #    pywikibot.output(u'Skipping: %s is a empty page' % page.title())
                    #    continue
                    if page.namespace() == 10:
                        loc = None
                        try:
                            tmpl, loc = moved_links[page.site.lang]
                            del tmpl
                        except KeyError:
                            pass
                        if loc is not None and loc in page.title():
                            pywikibot.output(u'Skipping: %s is a templates subpage' % page.title())
                            continue
                    break

                if self.generateUntil:
                    until = self.generateUntil
                    if page.site.lang not in page.site.family.nocapitalize:
                        until = until[0].upper() + until[1:]
                    if page.title(withNamespace=False) > until:
                        raise StopIteration
                self.add(page, hints=globalvar.hints)
                self.generated += 1
                if self.generateNumber:
                    if self.generated >= self.generateNumber:
                        raise StopIteration
            except StopIteration:
                self.pageGenerator = None
                break

    def firstSubject(self):
        """Return the first subject that is still being worked on"""
        if self.subjects:
            return self.subjects[0]

    def maxOpenSite(self):
        """Return the site that has the most
           open queries plus the number. If there is nothing left, return
           None. Only languages that are TODO for the first Subject
           are returned."""
        max = 0
        maxlang = None
        if not self.firstSubject():
            return None
        oc = dict(self.firstSubject().openSites())
        if not oc:
            # The first subject is done. This might be a recursive call made
            # because we have to wait before submitting another modification to
            # go live. Select any language from counts.
            oc = self.counts
        if pywikibot.getSite() in oc:
            return pywikibot.getSite()
        for lang in oc:
            count = self.counts[lang]
            if count > max:
                max = count
                maxlang = lang
        return maxlang

    def selectQuerySite(self):
        """Select the site the next query should go out for."""
        # How many home-language queries we still have?
        mycount = self.counts.get(pywikibot.getSite(), 0)
        # Do we still have enough subjects to work on for which the
        # home language has been retrieved? This is rough, because
        # some subjects may need to retrieve a second home-language page!
        if len(self.subjects) - mycount < globalvar.minsubjects:
            # Can we make more home-language queries by adding subjects?
            if self.pageGenerator and mycount < globalvar.maxquerysize:
                timeout = 60
                while timeout < 3600:
                    try:
                        self.generateMore(globalvar.maxquerysize - mycount)
                    except pywikibot.ServerError:
                        # Could not extract allpages special page?
                        pywikibot.output(
                            u'ERROR: could not retrieve more pages. Will try again in %d seconds'
                            % timeout)
                        time.sleep(timeout)
                        timeout *= 2
                    else:
                        break
            # If we have a few, getting the home language is a good thing.
            if not globalvar.restoreAll:
                try:
                    if self.counts[pywikibot.getSite()] > 4:
                        return pywikibot.getSite()
                except KeyError:
                    pass
        # If getting the home language doesn't make sense, see how many
        # foreign page queries we can find.
        return self.maxOpenSite()

    def oneQuery(self):
        """
        Perform one step in the solution process.

        Returns True if pages could be preloaded, or false
        otherwise.
        """
        # First find the best language to work on
        site = self.selectQuerySite()
        if site is None:
            pywikibot.output(u"NOTE: Nothing left to do")
            return False
        # Now assemble a reasonable list of pages to get
        subjectGroup = []
        pageGroup = []
        for subject in self.subjects:
            # Promise the subject that we will work on the site.
            # We will get a list of pages we can do.
            pages = subject.whatsNextPageBatch(site)
            if pages:
                pageGroup.extend(pages)
                subjectGroup.append(subject)
                if len(pageGroup) >= globalvar.maxquerysize:
                    # We have found enough pages to fill the bandwidth.
                    break
        if len(pageGroup) == 0:
            pywikibot.output(u"NOTE: Nothing left to do 2")
            return False
        # Get the content of the assembled list in one blow
        gen = site.preloadpages(pageGroup, templates=True, langlinks=True)
        for page in gen:
            # we don't want to do anything with them now. The
            # page contents will be read via the Subject class.
            pass
        # Tell all of the subjects that the promised work is done
        for subject in subjectGroup:
            subject.batchLoaded(self)
        return True

    def queryStep(self):
        self.oneQuery()
        # Delete the ones that are done now.
        for i in xrange(len(self.subjects) - 1, -1, -1):
            subj = self.subjects[i]
            if subj.isDone():
                subj.finish()
                subj.clean()
                del self.subjects[i]

    def isDone(self):
        """Check whether there is still more work to do"""
        return len(self) == 0 and self.pageGenerator is None

    def plus(self, site, count=1):
        """This is a routine that the Subject class expects in a counter"""
        try:
            self.counts[site] += count
        except KeyError:
            self.counts[site] = count

    def minus(self, site, count=1):
        """This is a routine that the Subject class expects in a counter"""
        self.counts[site] -= count

    def run(self):
        """Start the process until finished"""
        while not self.isDone():
            self.queryStep()

    def __len__(self):
        return len(self.subjects)


def compareLanguages(old, new, insite):

    oldiw = set(old)
    newiw = set(new)

    # sort by language code
    adding = sorted(newiw - oldiw)
    removing = sorted(oldiw - newiw)
    modifying = sorted(site for site in oldiw & newiw if old[site] != new[site])

    if not globalvar.summary and \
       len(adding) + len(removing) + len(modifying) <= 3:
        # Use an extended format for the string linking to all added pages.
        fmt = lambda d, site: unicode(d[site])
    else:
        # Use short format, just the language code
        fmt = lambda d, site: site.lang

    mods = mcomment = u''

    commentname = 'interwiki'
    if adding:
        commentname += '-adding'
    if removing:
        commentname += '-removing'
    if modifying:
        commentname += '-modifying'
    if commentname == 'interwiki-modifying' and len(modifying) == 1:
        useFrom = True
        commentname += '-from'
    else:
        useFrom = False

    if adding or removing or modifying:
        #Version info marks bots without unicode error
        #This also prevents abuse filter blocking on de-wiki
##        if not pywikibot.unicode_error:
##            mcomment += u'r%s) (' % sys.version.split()[0]

        mcomment += globalvar.summary

        changes = {'adding':    ', '.join([fmt(new, x) for x in adding]),
                   'removing':  ', '.join([fmt(old, x) for x in removing]),
                   'modifying': ', '.join([fmt(new, x) for x in modifying]),
                   'from': u'' if not useFrom else old[modifying[0]]}

        mcomment += i18n.twtranslate(insite.lang, commentname) % changes
        mods = i18n.twtranslate('en', commentname) % changes

    return mods, mcomment, adding, removing, modifying

def botMayEdit (page):
    tmpl = []
    try:
        tmpl, loc = moved_links[page.site.lang]
    except KeyError:
        pass
    if type(tmpl) != list:
        tmpl = [tmpl]
    try:
        tmpl += ignoreTemplates[page.site.lang]
    except KeyError:
        pass
    tmpl += ignoreTemplates['_default']
    if tmpl != []:
        templates = page.templatesWithParams();
        for template in templates:
            if template[0].title(withNamespace=False).lower() in tmpl:
                return False
    return True


def readWarnfile(filename, bot):
    import warnfile
    reader = warnfile.WarnfileReader(filename)
    # we won't use removeHints
    (hints, removeHints) = reader.getHints()
    for page, pagelist in hints.iteritems():
        # The WarnfileReader gives us a list of pagelinks, but titletranslate.py
        # expects a list of strings, so we convert it back.
        # TODO: This is a quite ugly hack, in the future we should maybe make
        # titletranslate expect a list of pagelinks.
        hintStrings = ['%s:%s' % (hintedPage.site.language(),
                                  hintedPage.title()) for hintedPage in pagelist]
        bot.add(page, hints=hintStrings)

def main():
    singlePageTitle = []
    opthintsonly = False
    start = None
    # Which namespaces should be processed?
    # default to [] which means all namespaces will be processed
    namespaces = []
    number = None
    until = None
    warnfile = None
    # a normal PageGenerator (which doesn't give hints, only Pages)
    hintlessPageGen = None
    optContinue = False
    optRestore = False
    restoredFiles = []
    File2Restore = []
    dumpFileName = ''
    append = True
    newPages = None
    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()

    for arg in pywikibot.handleArgs():
        if globalvar.readOptions(arg):
            continue
        elif arg.startswith('-warnfile:'):
            warnfile = arg[10:]
        elif arg.startswith('-years'):
            # Look if user gave a specific year at which to start
            # Must be a natural number or negative integer.
            if len(arg) > 7 and (arg[7:].isdigit() or (arg[7] == "-" and arg[8:].isdigit())):
                startyear = int(arg[7:])
            else:
                startyear = 1
            # avoid problems where year pages link to centuries etc.
            globalvar.followredirect = False
            hintlessPageGen = pagegenerators.YearPageGenerator(startyear)
        elif arg.startswith('-days'):
            if len(arg) > 6 and arg[5] == ':' and arg[6:].isdigit():
                # Looks as if the user gave a specific month at which to start
                # Must be a natural number.
                startMonth = int(arg[6:])
            else:
                startMonth = 1
            hintlessPageGen = pagegenerators.DayPageGenerator(startMonth)
        elif arg.startswith('-new'):
            if len(arg) > 5 and arg[4] == ':' and arg[5:].isdigit():
                # Looks as if the user gave a specific number of pages
                newPages = int(arg[5:])
            else:
                newPages = 100
        elif arg.startswith('-restore'):
            globalvar.restoreAll = arg[9:].lower() == 'all'
            optRestore = not globalvar.restoreAll
        elif arg == '-continue':
            optContinue = True
        elif arg == '-hintsonly':
            opthintsonly = True
        elif arg.startswith('-namespace:'):
            try:
                namespaces.append(int(arg[11:]))
            except ValueError:
                namespaces.append(arg[11:])
        # deprecated for consistency with other scripts
        elif arg.startswith('-number:'):
            number = int(arg[8:])
        elif arg.startswith('-until:'):
            until = arg[7:]
        else:
            if not genFactory.handleArg(arg):
                singlePageTitle.append(arg)

    # Do not use additional summary with autonomous mode
    if globalvar.autonomous:
        globalvar.summary = u''
    elif globalvar.summary:
        globalvar.summary += u'; '

    site = pywikibot.getSite()
    site.login()
    # ensure that we don't try to change main page
    try:
        mainpagename = site.mediawiki_message('mainpage')
        globalvar.skip.add(pywikibot.Page(site, mainpagename))
    except pywikibot.Error:
        pywikibot.output(u'Missing main page name')

    if newPages is not None:
        if len(namespaces) == 0:
            ns = 0
        elif len(namespaces) == 1:
            ns = namespaces[0]
            if ns != 'all':
                if isinstance(ns, unicode) or isinstance(ns, str):
                    index = site.getNamespaceIndex(ns)
                    if index is None:
                        raise ValueError(u'Unknown namespace: %s' % ns)
                    ns = index
            namespaces = []
        else:
            ns = 'all'
        hintlessPageGen = pagegenerators.NewpagesPageGenerator(newPages,
                                                               namespace=ns)

    elif optRestore or optContinue or globalvar.restoreAll:
        dumpFileName = pywikibot.config.datafilepath(
                           'data',
                           'interwiki-dumps',
                           u'%s-%s.pickle'
                             % (site.family.name, site.lang))
        try:
            f = open(dumpFileName, 'r')
            dumpedTitles = pickle.load(f)
            f.close()
        except (EOFError, IOError):
            dumpedTitles = []
        pages = [pywikibot.Page(site, title) for title in dumpedTitles]

        hintlessPageGen = iter(pages)
        if optContinue:
            if pages:
                last = pages[-1]
                nextPage = last.title(withNamespace=False) + '!'
                namespace = last.namespace()
            else:
                pywikibot.output(u"Dump file is empty?! Starting at the beginning.")
                nextPage = "!"
                namespace = 0
            hintlessPageGen = pagegenerators.CombinedPageGenerator([hintlessPageGen, pagegenerators.AllpagesPageGenerator(nextPage, namespace, includeredirects = False)])

    bot = InterwikiBot()

    if not hintlessPageGen:
        hintlessPageGen = genFactory.getCombinedGenerator()
    if hintlessPageGen:
        if len(namespaces) > 0:
            hintlessPageGen = pagegenerators.NamespaceFilterPageGenerator(hintlessPageGen, namespaces)
        # we'll use iter() to create make a next() function available.
        bot.setPageGenerator(iter(hintlessPageGen), number=number, until=until)
    elif warnfile:
        # TODO: filter namespaces if -namespace parameter was used
        readWarnfile(warnfile, bot)
    else:
        singlePageTitle = ' '.join(singlePageTitle)
        if not singlePageTitle and not opthintsonly:
            singlePageTitle = pywikibot.input(u'Which page to check:')
        if singlePageTitle:
            singlePage = pywikibot.Page(pywikibot.getSite(), singlePageTitle)
        else:
            singlePage = None
        bot.add(singlePage, hints=globalvar.hints)

    try:
        append = not (optRestore or optContinue or globalvar.restoreAll)
        bot.run()
    except KeyboardInterrupt:
        dumpFileName = bot.dump(append)
    except:
        dumpFileName = bot.dump(append)
        raise
    finally:
        if globalvar.contentsondisk:
            StoredPage.SPdeleteStore()
        if dumpFileName:
            try:
                restoredFiles.remove(dumpFileName)
            except ValueError:
                pass
        for dumpFileName in restoredFiles:
            try:
                os.remove(dumpFileName)
                pywikibot.output(u'Dumpfile %s deleted' % dumpFileName.split('\\')[-1])
            except WindowsError:
                pass

#===========
globalvar = Global()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
