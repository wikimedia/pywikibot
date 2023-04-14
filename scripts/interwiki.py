#!/usr/bin/env python3
"""
Script to check language links for general pages.

Uses existing translations of a page, plus hints from the command line, to
download the equivalent pages from other languages. All of such pages are
downloaded as well and checked for interwiki links recursively until there are
no more links that are encountered. A rationalization process then selects the
right interwiki links, and if this is unambiguous, the interwiki links in the
original page will be automatically updated and the modified page uploaded.

These command-line arguments can be used to specify which pages to work on:

    -days:         Like -years, but runs through all date pages. Stops at
                   Dec 31. If the argument is given in the form -days:X,
                   it will start at month no. X through Dec 31. If the
                   argument is simply given as -days, it will run from
                   Jan 1 through Dec 31. E.g. for -days:9 it will run
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

    -restore:      restore a set of "dumped" pages the bot was working on
                   when it terminated. The dump file will be subsequently
                   removed.

    -restore:all   restore a set of "dumped" pages of all dumpfiles to a given
                   family remaining in the "interwiki-dumps" directory. All
                   these dump files will be subsequently removed. If restoring
                   process interrupts again, it saves all unprocessed pages in
                   one new dump file of the given site.

    -continue:     like restore, but after having gone through the dumped
                   pages, continue alphabetically starting at the last of the
                   dumped pages. The dump file will be subsequently removed.

&params;

Additionally, these arguments can be used to restrict the bot to certain pages:

    -namespace:n   Number or name of namespace to process. The parameter can be
                   used multiple times. It works in combination with all other
                   parameters, except for the -start parameter. If you e.g.
                   want to iterate over all categories starting at M, use
                   -start:Category:M.

    -number:       used as -number:#, specifies that the bot should process
                   that amount of pages and then stop. This is only useful in
                   combination with -start. The default is not to stop.

    -until:        used as -until:title, specifies that the bot should
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

These arguments control miscellaneous bot behaviour:

    -quiet         Use this option to get less output
                   (note: without ending colon)

    -async         Put page on queue to be saved to wiki asynchronously. This
                   enables loading pages during saving throttling and gives a
                   better performance.
                   NOTE: For post-processing it always assumes that saving the
                   the pages was successful.
                   (note: without ending colon)

    -summary:      Set an additional action summary message for the edit. This
                   could be used for further explainings of the bot action.
                   This will only be used in non-autonomous mode.

    -hintsonly     The bot does not ask for a page to work on, even if none of
                   the above page sources was specified. This will make the
                   first existing page of -hint or -hinfile slip in as start
                   page, determining properties like namespace, disambiguation
                   state, and so on. When no existing page is found in the
                   hints, the bot does nothing.
                   Hitting return without input on the "Which page to check:"
                   prompt has the same effect as using -hintsonly.
                   Options like -back, -same or -wiktionary are in effect only
                   after a page has been found to work on.
                   (note: without ending colon)

These arguments are useful to provide hints to the bot:

    -hint:         used as -hint:de:Anweisung to give the bot a hint
                   where to start looking for translations. If no text
                   is given after the second ':', the name of the page
                   itself is used as the title for the hint, unless the
                   -hintnobracket command line option (see there) is also
                   selected.

                   There are some special hints, trying a number of languages
                   at once:

                      * all:       All languages with at least ca. 100 articles
                      * 10:        The 10 largest languages (sites with most
                                   articles). Analogous for any other natural
                                   number
                      * arab:      All languages using the Arabic alphabet
                      * cyril:     All languages that use the Cyrillic alphabet
                      * chinese:   All Chinese dialects
                      * latin:     All languages using the Latin script
                      * scand:     All Scandinavian languages

                   Names of families that forward their interlanguage links
                   to the wiki family being worked upon can be used, they are:

                      * commons:   Interlanguage links of Wikimedia Commons
                      * incubator: Links in pages on the Wikimedia Incubator
                      * meta:      Interlanguage links of named pages on Meta
                      * species:   Interlanguage links of the Wikispecies wiki
                      * strategy:  Links in pages on Wikimedia Strategy wiki
                      * test:      Take interwiki links from Test Wikipedia
                      * wikimania: Interwiki links of Wikimania

                   Languages, groups and families having the same page title
                   can be combined, as -hint:5,scand,sr,pt,commons:New_York

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

    -hintnobracket used to make the bot strip everything in last brackets,
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

Some configuration option can be used to change the working of this bot:

 interwiki_min_subjects: the minimum amount of subjects that should be
                     processed at the same time.

 interwiki_backlink: if set to True, all problems in foreign wikis will
                     be reported

 interwiki_shownew:  should interwiki.py display every new link it discovers?

 interwiki_graph:    output a graph PNG file on conflicts? You need pydot for
                     this: https://pypi.org/project/pydot/

 interwiki_graph_format: the file format for interwiki graphs

 without_interwiki:  save file with local articles without interwikis

All these options can be changed through the user configuration file.

If interwiki.py is terminated before it is finished, it will write a dump file
to the interwiki-dumps subdirectory. The program will read it if invoked with
the "-restore" or "-continue" option, and finish all the subjects in that list.
After finishing the dump file will be deleted. To run the interwiki-bot on all
pages on a language, run it with option "-start:!", and if it takes so long
that you have to break it off, use "-continue" next time.

"""
#
# (C) Pywikibot team, 2003-2023
#
# Distributed under the terms of the MIT license.
#
import codecs
import os
import re
import sys
from collections import Counter, defaultdict
from contextlib import suppress
from textwrap import fill
from typing import Optional

import pywikibot
from pywikibot import (
    config,
    i18n,
    interwiki_graph,
    pagegenerators,
    textlib,
    titletranslate,
)
from pywikibot.backports import Iterable
from pywikibot.bot import ListOption, OptionHandler, StandardOption
from pywikibot.cosmetic_changes import moved_links
from pywikibot.exceptions import (
    EditConflictError,
    Error,
    InvalidTitleError,
    LockedPageError,
    NoCreateError,
    NoPageError,
    NoUsernameError,
    PageSaveRelatedError,
    ServerError,
    SiteDefinitionError,
    SpamblacklistError,
    UnknownSiteError,
)
from pywikibot.tools import first_upper
from pywikibot.tools.collections import SizedKeyCollection


docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class SaveError(Error):

    """An attempt to save a page with changed interwiki has failed."""


class LinkMustBeRemoved(SaveError):

    """An interwiki link has to be removed manually.

    An interwiki link has to be removed, but this can't be done because
    of user preferences or because the user chose not to change the page.
    """


class GiveUpOnPage(Error):

    """User chose not to work on this page and its linked pages any more."""


# A list of template names in different languages.
# Pages which contain these shouldn't be changed.
ignoreTemplates = {
    '_default': ['delete'],
    'ar': ['تحرر', 'تحويل لين'],
    'ary': ['كاتبدل دابا'],
    'arz': ['بتتطور'],
    'cs': ['Pracuje_se'],
    'de': ['inuse', 'in use', 'in bearbeitung', 'inbearbeitung',
           'löschen', 'sla',
           'löschantrag', 'löschantragstext',
           'falschschreibung',
           'obsolete schreibung', 'veraltete schreibweise'],
    'en': ['inuse', 'softredirect'],
    'fa': ['در دست ویرایش ۲', 'حذف سریع'],
    'pdc': ['lösche'],
    'zh': ['inuse'],
}


class InterwikiBotConfig:

    """Container class for interwikibot's settings."""

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
    lacklanguage = None
    minlinks = 0
    quiet = False
    restore_all = False
    asynchronous = False
    summary = ''
    repository = False

    def note(self, text: str) -> None:
        """Output a notification message with.

        The text will be printed only if conf.quiet isn't set.
        :param text: text to be shown
        """
        if not self.quiet:
            pywikibot.info('NOTE: ' + text)

    def readOptions(self, option: str) -> bool:
        """Read all commandline parameters for the global container."""
        arg, _, value = option.partition(':')
        if not arg.startswith('-'):
            return False

        arg = arg[1:]
        if arg == 'noauto':
            self.auto = False
        elif arg == 'hint':
            self.hints.append(value)
        elif arg == 'hintfile':
            hintfilename = value or pywikibot.input(
                'Please enter the hint filename:')
            # hint or title ends either before | or before ]]
            R = re.compile(r'\[\[(.+?)(?:\]\]|\|)')
            with codecs.open(hintfilename, 'r', config.textfile_encoding) as f:
                self.hints += R.findall(f.read())
        elif arg == 'wiktionary':
            self.same = 'wiktionary'
            # Don't use auto-translation in -wiktionary mode
            # where page titles must be the same
            self.auto = False
        elif arg == 'untranslatedonly':
            self.untranslated = True
            self.untranslatedonly = True
        elif arg == 'askhints':
            self.untranslated = True
            self.untranslatedonly = False
            self.askhints = True
        elif arg in ('autonomous', 'auto'):
            self.autonomous = True
        elif arg == 'noredirect':
            self.followredirect = False
        elif arg == 'limittwo':
            self.limittwo = True
            self.strictlimittwo = True
        elif arg == 'whenneeded':
            self.limittwo = True
            self.strictlimittwo = False
            if value.isdigit():
                self.needlimit = int(value)
        elif arg == 'skipfile':
            skip_page_gen = pagegenerators.TextIOPageGenerator(value)
            self.skip.update(skip_page_gen)
            del skip_page_gen
        elif arg == 'neverlink':
            self.neverlink += value.split(',')
        elif arg == 'ignore':
            self.ignore += [pywikibot.Page(pywikibot.Site(), p)
                            for p in value.split(',')]
        elif arg == 'ignorefile':
            ignore_page_gen = pagegenerators.TextIOPageGenerator(value)
            self.ignore.update(ignore_page_gen)
            del ignore_page_gen
        elif arg == 'showpage':
            self.showtextlink += self.showtextlinkadd
        elif arg == 'graph':
            # override configuration
            config.interwiki_graph = True
        elif arg == 'bracket':
            self.parenthesesonly = True
        elif arg == 'localright':
            self.followinterwiki = False
        elif arg == 'array' and value.isdigit():
            self.minsubjects = int(value)
        elif arg == 'query' and value.isdigit():
            self.maxquerysize = int(value)
        elif arg == 'back':
            self.nobackonly = True
        elif arg == 'async':
            self.asynchronous = True
        elif arg == 'summary':
            self.summary = value or pywikibot.input(
                'What summary do you want to use?')
        elif arg == 'lack':
            self.lacklanguage, _, minlinks = value.partition(':')
            self.minlinks = int(minlinks or 1)
        elif arg in ('cleanup', 'confirm', 'force', 'hintnobracket',
                     'hintsareright', 'initialredirect', 'localonly', 'quiet',
                     'repository', 'same', 'select', 'skipauto',
                     'untranslated'):
            assert hasattr(self, arg)
            assert value == ''
            setattr(self, arg, True)
        else:
            return False
        return True


class Subject(interwiki_graph.Subject):

    """
    Class to follow the progress of a single 'subject'.

    (i.e. a page with all its translations)

    Subject is a transitive closure of the binary relation on Page:
    "has_a_langlink_pointing_to".

    A formal way to compute that closure would be:

    With P a set of pages, NL ('NextLevel') a function on sets defined as:

        `NL(P) = { target | ∃ source ∈ P, target ∈ source.langlinks() }`

    pseudocode::

        todo <- [origin]
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

    Code becomes::

        todo <- {origin.site: [origin]}
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

    def __init__(self, origin=None, hints=None, conf=None) -> None:
        """
        Initializer.

        Takes as arguments the Page on the home wiki
        plus optionally a list of hints for translation
        """
        self.conf = conf

        super().__init__(origin)

        self.repoPage = None
        # todo is a list of all pages that still need to be analyzed.
        # Mark the origin page as todo.
        self.todo = SizedKeyCollection('site')
        if origin:
            self.todo.append(origin)

        # done is a list of all pages that have been analyzed and that
        # are known to belong to this subject.
        self.done = SizedKeyCollection('site')
        # This is a list of all pages that are currently scheduled for
        # download.
        self.pending = SizedKeyCollection('site')
        if self.conf.hintsareright:
            # This is a set of sites that we got hints to
            self.hintedsites = set()
        self.translate(hints, self.conf.hintsareright)
        self.confirm = self.conf.confirm
        self.problemfound = False
        self.untranslated = None
        self.hintsAsked = False
        self.forcedStop = False
        self.workonme = True

    def getFoundDisambig(self, site):
        """
        Return the first disambiguation found.

        If we found a disambiguation on the given site while working on the
        subject, this method returns it. If several ones have been found, the
        first one will be returned.
        Otherwise, None will be returned.
        """
        for tree in [self.done, self.pending]:
            for page in tree.filter(site):
                if page.exists() and page.isDisambig():
                    return page
        return None

    def getFoundNonDisambig(self, site):
        """
        Return the first non-disambiguation found.

        If we found a non-disambiguation on the given site while working on the
        subject, this method returns it. If several ones have been found, the
        first one will be returned.
        Otherwise, None will be returned.
        """
        for tree in [self.done, self.pending]:
            for page in tree.filter(site):
                if page.exists() \
                   and not page.isDisambig() \
                   and not page.isRedirectPage() \
                   and not page.isCategoryRedirect():
                    return page
        return None

    def getFoundInCorrectNamespace(self, site):
        """
        Return the first page in the extended namespace.

        If we found a page that has the expected namespace on the given site
        while working on the subject, this method returns it. If several ones
        have been found, the first one will be returned.
        Otherwise, None will be returned.
        """
        for tree in [self.done, self.pending, self.todo]:
            for page in tree.filter(site):
                # -hintsonly: before we have an origin page, any namespace will
                # do.
                if self.origin \
                   and page.namespace() == self.origin.namespace() \
                   and page.exists() \
                   and not page.isRedirectPage() \
                   and not page.isCategoryRedirect():
                    return page
        return None

    def translate(self, hints=None, keephintedsites: bool = False) -> None:
        """Add the given translation hints to the todo list."""
        if self.conf.same and self.origin:
            if hints:
                hints += ['all:']
            else:
                hints = ['all:']

            site = self.origin.site
        else:
            site = pywikibot.Site()

        links = titletranslate.translate(
            self.origin,
            hints=hints,
            auto=self.conf.auto,
            removebrackets=self.conf.hintnobracket,
            site=site)

        for link in links:
            page = pywikibot.Page(link)
            self.todo.append(page)
            self.found_in[page] = [None]
            if keephintedsites:
                self.hintedsites.add(page.site)

    def openSites(self):
        """
        Iterator.

        Yields (site, count) pairs:
        * site is a site where we still have work to do on
        * count is the number of items in that Site that need work on
        """
        return self.todo.iter_values_len()

    def whatsNextPageBatch(self, site):
        """
        Return the next page batch.

        By calling this method, you 'promise' this instance that you will
        preload all the 'site' Pages that are in the todo list.

        This routine will return a list of pages that can be treated.
        """
        # Bug-check: Isn't there any work still in progress? We can't work on
        # different sites at a time!
        if self.pending:
            raise RuntimeError(
                "BUG: Can't start to work on {}; still working on {}"
                .format(site, self.pending))
        # Prepare a list of suitable pages
        result = []
        for page in self.todo.filter(site):
            self.pending.append(page)
            result.append(page)

        self.todo.remove_key(site)

        # If there are any, return them. Otherwise, nothing is in progress.
        return result

    def makeForcedStop(self, counter) -> None:
        """End work on the page before the normal end."""
        for site, count in self.todo.iter_values_len():
            counter.minus(site, count)
        self.todo.clear()
        self.forcedStop = True

    def addIfNew(self, page, counter, linkingPage) -> bool:
        """
        Add the pagelink given to the todo list, if it hasn't been seen yet.

        If it is added, update the counter accordingly.

        Also remembers where we found the page, regardless of whether it had
        already been found before or not.

        Returns True if the page is new.
        """
        if self.forcedStop:
            return False

        # cannot check backlink before we have an origin page
        if self.conf.nobackonly and self.origin and page == self.origin:
            try:
                pywikibot.info(f'{page} has a backlink from {linkingPage}.')
            except UnicodeDecodeError:
                pywikibot.info('Found a backlink for a page.')
            self.makeForcedStop(counter)
            return False

        if page in self.found_in:
            # not new
            self.found_in[page].append(linkingPage)
            return False

        self.found_in[page] = [linkingPage]
        self.todo.append(page)
        counter.plus(page.site)
        return True

    def skipPage(self, page, target, counter):
        """Return whether page has to be skipped."""
        return self.isIgnored(target) \
            or self.namespaceMismatch(page, target, counter) \
            or self.wiktionaryMismatch(target)

    def namespaceMismatch(self, linkingPage, linkedPage, counter) -> bool:
        """
        Check whether or not the given page has a different namespace.

        Returns True if the namespaces are different and the user
        has selected not to follow the linked page.
        """
        if linkedPage in self.found_in:
            # We have seen this page before, don't ask again.
            return False

        if self.origin and self.origin.namespace() != linkedPage.namespace():
            # Allow for a mapping between different namespaces
            crossFrom = self.origin.site.family.crossnamespace.get(
                self.origin.namespace(), {})
            crossTo = crossFrom.get(self.origin.site.lang,
                                    crossFrom.get('_default', {}))
            nsmatch = crossTo.get(linkedPage.site.lang,
                                  crossTo.get('_default', []))
            if linkedPage.namespace() in nsmatch:
                return False

            if self.conf.autonomous:
                pywikibot.info(
                    'NOTE: Ignoring link from page {} in namespace'
                    ' {} to page {} in namespace {}.'
                    .format(linkingPage, linkingPage.namespace(), linkedPage,
                            linkedPage.namespace()))
                # Fill up found_in, so that we will not write this notice
                self.found_in[linkedPage] = [linkingPage]
                return True

            preferredPage = self.getFoundInCorrectNamespace(linkedPage.site)
            if preferredPage:
                pywikibot.info(
                    'NOTE: Ignoring link from page {} in namespace {} to '
                    'page {} in namespace {} because page {} in the '
                    'correct namespace has already been found.'
                    .format(linkingPage, linkingPage.namespace(),
                            linkedPage, linkedPage.namespace(),
                            preferredPage))
                return True

            choice = pywikibot.input_choice(
                'WARNING: {} is in namespace "{}", but {} is in '
                'namespace "{}". Follow it anyway?'
                .format(self.origin, self.origin.namespace(),
                        linkedPage, linkedPage.namespace()),
                [('Yes', 'y'), ('No', 'n'),
                 ('Add an alternative', 'a'), ('give up', 'g')],
                automatic_quit=False)

            if choice != 'y':
                # Fill up found_in, so that we will not ask again
                self.found_in[linkedPage] = [linkingPage]
                if choice == 'g':
                    self.makeForcedStop(counter)
                elif choice == 'a':
                    newHint = pywikibot.input(
                        'Give the alternative for language {}, not '
                        'using a language code:'
                        .format(linkedPage.site.lang))
                    if newHint:
                        alternativePage = pywikibot.Page(
                            linkedPage.site, newHint)
                        if alternativePage:
                            # add the page that was entered by the user
                            self.addIfNew(alternativePage, counter, None)
                else:
                    pywikibot.info(
                        'NOTE: ignoring {} and its interwiki links'
                        .format(linkedPage))
                return True

        # same namespaces, no problem
        # or no origin page yet, also no problem
        return False

    def wiktionaryMismatch(self, page) -> bool:
        """Check for ignoring pages."""
        if self.origin and self.conf.same == 'wiktionary':
            if page.title().lower() != self.origin.title().lower():
                pywikibot.info(f'NOTE: Ignoring {page} for {self.origin} in '
                               f'wiktionary mode')
                return True

            if (page.title() != self.origin.title()
                and self.origin.namespace().case == 'case-sensitive'
                    and page.namespace().case == 'case-sensitive'):
                pywikibot.info(
                    'NOTE: Ignoring {} for {} in wiktionary mode because both '
                    'languages are uncapitalized.'
                    .format(page, self.origin))
                return True

        return False

    def disambigMismatch(self, page, counter):
        """
        Check whether the given page has a different disambiguation status.

        Returns a tuple (skip, alternativePage).

        skip is True if the pages have mismatching statuses and the bot
        is either in autonomous mode, or the user chose not to use the
        given page.

        alternativePage is either None, or a page that the user has
        chosen to use instead of the given page.
        """
        if not self.origin:
            return (False, None)  # any page matches til we have an origin page

        if self.conf.autonomous:
            if self.origin.isDisambig() and not page.isDisambig():
                pywikibot.info(
                    'NOTE: Ignoring link from disambiguation page {} to '
                    'non-disambiguation {}'.format(self.origin, page))
                return (True, None)

            if not self.origin.isDisambig() and page.isDisambig():
                pywikibot.info(
                    'NOTE: Ignoring link from non-disambiguation page {} to '
                    'disambiguation {}'.format(self.origin, page))
                return (True, None)

        else:
            choice = 'y'
            if self.origin.isDisambig() and not page.isDisambig():
                disambig = self.getFoundDisambig(page.site)
                if disambig:
                    pywikibot.info(
                        'NOTE: Ignoring non-disambiguation page {} for {} '
                        'because disambiguation page {} has already been '
                        'found.'
                        .format(page, self.origin, disambig))
                    return (True, None)

                choice = pywikibot.input_choice(
                    "WARNING: {} is a disambiguation page, but {} doesn't "
                    'seem to be one. Follow it anyway?'
                    .format(self.origin, page),
                    [('Yes', 'y'), ('No', 'n'),
                     ('Add an alternative', 'a'), ('give up', 'g')],
                    automatic_quit=False)

            elif not self.origin.isDisambig() and page.isDisambig():
                nondisambig = self.getFoundNonDisambig(page.site)
                if nondisambig:
                    pywikibot.info(
                        'NOTE: Ignoring disambiguation page {} for {} because '
                        'non-disambiguation page {} has already been found.'
                        .format(page, self.origin, nondisambig))
                    return (True, None)

                choice = pywikibot.input_choice(
                    "WARNING: {} doesn't seem to be a disambiguation "
                    'page, but {} is one. Follow it anyway?'
                    .format(self.origin, page),
                    [('Yes', 'y'), ('No', 'n'),
                     ('Add an alternative', 'a'), ('give up', 'g')],
                    automatic_quit=False)

            if choice == 'n':
                return (True, None)

            if choice == 'a':
                newHint = pywikibot.input(
                    f'Give the alternative for language {page.site.lang}, '
                    f'not using a language code:')
                alternativePage = pywikibot.Page(page.site, newHint)
                return (True, alternativePage)

            if choice == 'g':
                self.makeForcedStop(counter)
                return (True, None)

        # We can follow the page.
        return (False, None)

    def isIgnored(self, page) -> bool:
        """Return True if pages is to be ignored."""
        if page.site.lang in self.conf.neverlink:
            pywikibot.info(f'Skipping link {page} to an ignored language')
            return True

        if page in self.conf.ignore:
            pywikibot.info(f'Skipping link {page} to an ignored page')
            return True

        return False

    def reportInterwikilessPage(self, page) -> None:
        """Report interwikiless page."""
        self.conf.note('{} does not have any interwiki links'
                       .format(self.origin))
        if config.without_interwiki:
            with codecs.open(
                    pywikibot.config.datafilepath('without_interwiki.txt'),
                    'a', 'utf-8') as f:
                f.write(f'# {page} \n')

    def askForHints(self, counter) -> None:
        """Ask for hints to other sites."""
        if (not self.workonme  # we don't work on it anyway
            or not self.untranslated and not self.conf.askhints
            or self.hintsAsked
            or not self.origin
            or not self.origin.exists()
            or self.origin.isRedirectPage()
                or self.origin.isCategoryRedirect()):
            return

        self.hintsAsked = True
        if not self.conf.untranslated:
            return

        t = self.conf.showtextlink
        if t:
            pywikibot.info(self.origin.get()[:t])

        while True:
            newhint = pywikibot.input('Give a hint (? to see pagetext):')

            if not newhint:
                break

            if newhint == '?':
                t += self.conf.showtextlinkadd
                pywikibot.info(self.origin.get()[:t])
            elif ':' not in newhint:
                pywikibot.info(fill(
                    'Please enter a hint in the format language:pagename '
                    'or type nothing if you do not have a hint.'))
            else:
                links = titletranslate.translate(
                    self.origin,
                    hints=[newhint],
                    auto=self.conf.auto,
                    removebrackets=self.conf.hintnobracket)
                for link in links:
                    page = pywikibot.Page(link)
                    self.addIfNew(page, counter, None)
                    if self.conf.hintsareright:
                        self.hintedsites.add(page.site)

    def redir_checked(self, page, counter):
        """Check and handle redirect. Return True if check is done."""
        if page.isRedirectPage():
            redirect_target = page.getRedirectTarget()
            redir = ''
        elif page.isCategoryRedirect():
            redirect_target = page.getCategoryRedirectTarget()
            redir = 'category '
        else:
            return False

        self.conf.note('{} is {}redirect to {}'
                       .format(page, redir, redirect_target))
        if self.origin is None or page == self.origin:
            # the 1st existig page becomes the origin page, if none was
            # supplied
            if self.conf.initialredirect:
                # don't follow another redirect; it might be a self
                # loop
                if not redirect_target.isRedirectPage() \
                   and not redirect_target.isCategoryRedirect():
                    self.origin = redirect_target
                    self.todo.append(redirect_target)
                    counter.plus(redirect_target.site)
            else:
                # This is a redirect page to the origin. We don't need
                # to follow the redirection.
                # In this case we can also stop all hints!
                for site, count in self.todo.iter_values_len():
                    counter.minus(site, count)
                self.todo.clear()
        elif not self.conf.followredirect:
            self.conf.note(f'not following {redir}redirects.')
        elif page.isStaticRedirect():
            self.conf.note(f'not following static {redir}redirects.')
        elif (page.site.family == redirect_target.site.family
              and not self.skipPage(page, redirect_target, counter)
              and self.addIfNew(redirect_target, counter, page)
              and config.interwiki_shownew):
            pywikibot.info(f'{self.origin}: {page} gives new {redir}redirect '
                           f'{redirect_target}')
        return True

    def check_page(self, page, counter) -> None:
        """Check whether any iw links should be added to the todo list."""
        if not page.exists():
            self.conf.remove.append(str(page))
            self.conf.note(f'{page} does not exist. Skipping.')
            if page == self.origin:
                # The page we are working on is the page that does not
                # exist. No use in doing any work on it in that case.
                for site, count in self.todo.iter_values_len():
                    counter.minus(site, count)
                self.todo.clear()
                # In some rare cases it might be we already did check some
                # 'automatic' links
                self.done.clear()
            return

        if self.redir_checked(page, counter):
            return

        # must be behind the page.isRedirectPage() part
        # otherwise a redirect error would be raised
        if page_empty_check(page):
            self.conf.remove.append(str(page))
            self.conf.note(f'{page} is empty. Skipping.')
            if page == self.origin:
                for site, count in self.todo.iter_values_len():
                    counter.minus(site, count)
                self.todo.clear()
                self.done.clear()
                self.origin = None
            return

        if page.section():
            self.conf.note(f'{page} is a page section. Skipping.')
            return

        # Page exists, isn't a redirect, and is a plain link (no section)
        if self.origin is None:
            # the 1st existig page becomes the origin page, if none was
            # supplied
            self.origin = page

        try:
            iw = page.langlinks()
        except UnknownSiteError:
            self.conf.note(f'site {page.site} does not exist.')
            return

        (skip, alternativePage) = self.disambigMismatch(page, counter)
        if skip:
            pywikibot.info(f'NOTE: ignoring {page} and its interwiki links')
            self.done.remove(page)
            iw = ()
            if alternativePage:
                # add the page that was entered by the user
                self.addIfNew(alternativePage, counter, None)

        duplicate = None
        for p in self.done.filter(page.site):
            if p != page and p.exists() \
               and not p.isRedirectPage() and not p.isCategoryRedirect():
                duplicate = p
                break

        if self.origin == page:
            self.untranslated = not iw
            if self.conf.untranslatedonly:
                # Ignore the interwiki links.
                iw = ()
            if self.conf.lacklanguage \
               and self.conf.lacklanguage in (link.site.lang for link in iw):
                iw = ()
                self.workonme = False
            if len(iw) < self.conf.minlinks:
                iw = ()
                self.workonme = False

        elif self.conf.autonomous and duplicate and not skip:
            pywikibot.info(f'Stopping work on {self.origin} because duplicate '
                           f'pages {duplicate} and {page} are found')
            self.makeForcedStop(counter)
            try:
                with codecs.open(
                    pywikibot.config.datafilepath('autonomous_problems.dat'),
                        'a', 'utf-8') as f:
                    f.write('* {} {{Found more than one link for {}}}'
                            .format(self.origin, page.site))
                    if config.interwiki_graph and config.interwiki_graph_url:
                        filename = interwiki_graph.getFilename(
                            self.origin,
                            extension=config.interwiki_graph_formats[0])
                        f.write(' [{}{} graph]'
                                .format(config.interwiki_graph_url, filename))
                    f.write('\n')
            # FIXME: What errors are we catching here?
            except Exception:
                pywikibot.info(
                    'File autonomous_problems.dat open or corrupted! '
                    'Try again with -restore.')
                sys.exit()
            iw = ()

        for link in iw:
            linkedPage = pywikibot.Page(link)
            if self.conf.hintsareright and linkedPage.site in self.hintedsites:
                pywikibot.info(
                    'NOTE: {}: {} extra interwiki on hinted site ignored {}'
                    .format(self.origin, page, linkedPage))
                break

            if not self.skipPage(page, linkedPage, counter) \
               and (self.conf.followinterwiki or page == self.origin) \
               and self.addIfNew(linkedPage, counter, page):
                # It is new. Also verify whether it is the second on the
                # same site
                lpsite = linkedPage.site
                for prevPage in self.found_in:
                    if prevPage != linkedPage and prevPage.site == lpsite:
                        # Still, this could be "no problem" as
                        # either may be a redirect to the other.
                        # No way to find out quickly!
                        pywikibot.info(
                            'NOTE: {}: {} gives duplicate interwiki on same '
                            'site {}'.format(self.origin, page, linkedPage))
                        break
                else:
                    if config.interwiki_shownew:
                        pywikibot.info(
                            '{}: {} gives new interwiki {}'
                            .format(self.origin, page, linkedPage))
            if self.forcedStop:
                break

    def batchLoaded(self, counter) -> None:
        """
        Notify that the promised batch of pages was loaded.

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
            self.done.append(page)

            # make sure that none of the linked items is an auto item
            if self.conf.skipauto:
                dictName, year = page.autoFormat()
                if dictName is not None:
                    if self.origin:
                        pywikibot.warning(
                            '{}:{} relates to {}:{}, which is an '
                            'auto entry {}({})'
                            .format(self.origin.site.lang, self.origin,
                                    page.site.lang, page, dictName, year))

                    # Abort processing if the bot is running in autonomous mode
                    if self.conf.autonomous:
                        self.makeForcedStop(counter)

            # Register this fact at the todo-counter.
            counter.minus(page.site)

            # Now check whether any interwiki links should be added to the
            # todo list.
            self.check_page(page, counter)

        # These pages are no longer 'in progress'
        self.pending.clear()
        # Check whether we need hints and the user offered to give them
        if self.untranslated and not self.hintsAsked:
            self.reportInterwikilessPage(page)
        self.askForHints(counter)

    def isDone(self):
        """Return True if all the work for this subject has completed."""
        return not self.todo

    def problem(self, txt: str, createneed: bool = True) -> None:
        """Report a problem with the resolution of this subject."""
        pywikibot.error(txt)
        self.confirm = True
        if createneed:
            self.problemfound = True

    def whereReport(self, page, indent: int = 4) -> None:
        """Report found interlanguage links with conflicts."""
        for page2 in sorted(self.found_in[page]):
            if page2 is None:
                pywikibot.info(' ' * indent + 'Given as a hint.')
            else:
                pywikibot.info(' ' * indent + str(page2))

    def assemble(self):
        """Assemble language links."""
        # No errors have been seen so far, except....
        errorCount = self.problemfound
        # Build up a dictionary of all pages found, with the site as key.
        # Each value will be a list of pages.
        new = defaultdict(list)
        for page in self.done:
            if page.exists() and not page.isRedirectPage() \
               and not page.isCategoryRedirect():
                site = page.site
                if site.family.interwiki_forward:
                    # TODO: allow these cases to be propagated!

                    # inhibit the forwarding families pages to be updated.
                    continue

                if site != self.origin.site:
                    new[site].append(page)
                elif page != self.origin:
                    self.problem(f'Found link to {page}')
                    self.whereReport(page)
                    errorCount += 1

        # See if new{} contains any problematic values
        for site, pages in new.items():
            if len(pages) > 1:
                errorCount += 1
                self.problem(f'Found more than one link for {site}')

        if not errorCount and not self.conf.select:
            # no errors, so all lists have only one item
            return {site: pages[0] for site, pages in new.items()}

        # There are any errors.
        if config.interwiki_graph:
            graphDrawer = interwiki_graph.GraphDrawer(self)
            graphDrawer.createGraph()

        # We don't need to continue with the rest if we're in autonomous
        # mode.
        if self.conf.autonomous:
            return None

        result = {}
        # First loop over the ones that have more solutions
        for site, pages in new.items():
            if len(pages) <= 1:
                continue

            pywikibot.info('=' * 30)
            pywikibot.info(f'Links to {site}')
            for i, page2 in enumerate(pages, 1):
                pywikibot.info(f'  ({i}) Found link to {page2} in:')
                self.whereReport(page2, indent=8)

            # TODO: allow answer to repeat previous or go back after a mistake
            answer = pywikibot.input_choice(
                'Which variant should be used?',
                (ListOption(pages),
                 StandardOption('none', 'n'),
                 StandardOption('give up', 'g')))
            if answer == 'g':
                return None
            if answer != 'n':
                result[site] = answer[1]

        # Loop over the ones that have one solution, so are in principle
        # not a problem.
        acceptall = False
        for site, pages in new.items():
            if len(pages) != 1:
                continue

            if not acceptall:
                pywikibot.info('=' * 30)
                page2 = pages[0]
                pywikibot.info(f'Found link to {page2} in:')
                self.whereReport(page2, indent=4)

            # TODO: allow answer to repeat previous or go back
            # after a mistake
            answer = 'a' if acceptall else pywikibot.input_choice(
                'What should be done?',
                [('accept', 'a'), ('reject', 'r'), ('give up', 'g'),
                 ('accept all', 'l')], 'a', automatic_quit=False)

            if answer == 'l':  # accept all
                acceptall = True
                answer = 'a'

            if answer == 'a':  # accept this one
                result[site] = pages[0]
            elif answer == 'g':  # give up
                return None
            # else reject if None acceptable

        return result

    def finish(self):
        """
        Round up the subject, making any necessary changes.

        This should be called exactly once after the todo list has gone empty.

        """
        if not self.isDone():
            raise Exception('Bugcheck: finish called before done')

        if not self.workonme or not self.origin:
            return

        if self.origin.isRedirectPage() or self.origin.isCategoryRedirect():
            return

        if not self.untranslated and self.conf.untranslatedonly:
            return

        if self.forcedStop:  # autonomous with problem
            pywikibot.info(f'======Aborted processing {self.origin}======')
            return

        self.post_processing()

    def post_processing(self):
        """Some finishing processes to be done."""
        pywikibot.info(f'======Post-processing {self.origin}======')
        # Assemble list of accepted interwiki links
        new = self.assemble()
        if new is None:  # User said give up
            pywikibot.info(f'======Aborted processing {self.origin}======')
            return

        # Make sure new contains every page link, including the page we are
        # processing
        # TODO: should be move to assemble()
        # replaceLinks will skip the site it's working on.
            # TODO: make this possible as well.
        if self.origin.site not in new \
           and not self.origin.site.family.interwiki_forward:
            new[self.origin.site] = self.origin

        updatedSites = []
        # Process all languages here
        self.conf.always = False
        if self.conf.limittwo:
            self.process_limit_two(new, updatedSites)
        else:
            self.process_unlimited(new, updatedSites)

        # don't report backlinks for pages we already changed
        if config.interwiki_backlink:
            self.reportBacklinks(new, updatedSites)

    def process_limit_two(self, new, updated):
        """Post process limittwo."""
        lclSite = self.origin.site
        lclSiteDone = False
        frgnSiteDone = False

        for code in lclSite.family.languages_by_size:
            site = pywikibot.Site(code, lclSite.family)
            if not lclSiteDone and site == lclSite \
               or (not frgnSiteDone and site != lclSite and site in new):
                if site == lclSite:
                    lclSiteDone = True   # even if we fail the update
                if (site.family.name in config.usernames
                        and site.code in config.usernames[site.family.name]):
                    try:
                        if self.replaceLinks(new[site], new):
                            updated.append(site)
                        if site != lclSite:
                            frgnSiteDone = True
                    except SaveError:
                        pass
                    except GiveUpOnPage:
                        break

            elif (not self.conf.strictlimittwo
                  and site in new and site != lclSite):
                old = {}
                try:
                    for link in new[site].iterlanglinks():
                        page = pywikibot.Page(link)
                        old[page.site] = page
                except NoPageError:
                    pywikibot.error(f'{new[site]} no longer exists?')
                    continue
                *_, adding, removing, modifying = compareLanguages(
                    old, new, lclSite, self.conf.summary)
                if (removing and not self.conf.autonomous
                    or modifying and self.problemfound
                    or not old
                    or (self.conf.needlimit
                        and len(adding) + len(modifying)
                        >= self.conf.needlimit + 1)):
                    try:
                        if self.replaceLinks(new[site], new):
                            updated.append(site)
                    except (NoUsernameError, SaveError):
                        pass
                    except GiveUpOnPage:
                        break

    def process_unlimited(self, new, updated):
        """Post process unlimited."""
        for (site, page) in new.items():
            # if we have an account for this site
            if site.family.name in config.usernames \
               and site.code in config.usernames[site.family.name] \
               and not site.has_data_repository:
                # Try to do the changes
                try:
                    if self.replaceLinks(page, new):
                        # Page was changed
                        updated.append(site)
                except SaveError:
                    pass
                except GiveUpOnPage:
                    break

    def replaceLinks(self, page, newPages) -> bool:
        """Return True if saving was successful."""
        # In this case only continue on the Page we started with
        if self.conf.localonly and page != self.origin:
            raise SaveError('-localonly and page != origin')

        if page.section():
            # This is not a page, but a subpage. Do not edit it.
            pywikibot.info(
                f'Not editing {page}: not doing interwiki on subpages')
            raise SaveError('Link has a #section')

        try:
            pagetext = page.get()
        except NoPageError:
            pywikibot.info(f'Not editing {page}: page does not exist')
            raise SaveError("Page doesn't exist")

        if page_empty_check(page):
            pywikibot.info(f'Not editing {page}: page is empty')
            raise SaveError('Page is empty.')

        # clone original newPages dictionary, so that we can modify it to the
        # local page's needs
        new = newPages.copy()
        interwikis = [pywikibot.Page(link) for link in page.iterlanglinks()]

        # remove interwiki links to ignore
        for iw in re.finditer(r'<!-- *\[\[(.*?:.*?)\]\] *-->', pagetext):
            with suppress(KeyError,
                          SiteDefinitionError,
                          InvalidTitleError):
                ignorepage = pywikibot.Page(page.site, iw.groups()[0])
                if new[ignorepage.site] == ignorepage \
                   and ignorepage.site != page.site:
                    param = {'to': ignorepage, 'from': page}
                    if ignorepage not in interwikis:
                        pywikibot.info('Ignoring link to {to} for {from}'
                                       .format_map(param))
                        new.pop(ignorepage.site)
                    else:
                        pywikibot.info(
                            'NOTE: Not removing interwiki from {from} to '
                            '{to} (exists both commented and non-commented)'
                            .format_map(param))

        # sanity check - the page we are fixing must be the only one for that
        # site.
        pltmp = new[page.site]
        if pltmp != page:
            pywikibot.error(
                f'{page} is not in the list of new links! Found {pltmp}.')
            raise SaveError('BUG: sanity check failed')

        # Avoid adding an iw link back to itself
        del new[page.site]
        # Do not add interwiki links to foreign families that page.site() does
        # not forward to
        for stmp in new.keys():
            if stmp.family != page.site.family \
               and stmp.family.name != page.site.family.interwiki_forward:
                del new[stmp]

        # Put interwiki links into a map
        old = {p.site: p for p in interwikis}

        # Check what needs to get done
        mods, mcomment, adding, removing, modifying = compareLanguages(
            old, new, page.site, self.conf.summary)

        # When running in autonomous mode without -force switch, make sure we
        # don't remove any items, but allow addition of the new ones
        if self.conf.autonomous and not self.conf.force and removing:
            for rmsite in removing:
                # Sometimes sites have an erroneous link to itself as an
                # interwiki
                if rmsite == page.site:
                    continue
                rmPage = old[rmsite]
                # put it to new means don't delete it
                if (not self.conf.cleanup
                        or str(rmPage) not in self.conf.remove):
                    new[rmsite] = rmPage
                    pywikibot.warning(
                        '{} is either deleted or has a mismatching '
                        'disambiguation state.'.format(rmPage))
            # Re-Check what needs to get done
            mods, mcomment, adding, removing, modifying = compareLanguages(
                old, new, page.site, self.conf.summary)
        if not mods:
            self.conf.note(f'No changes needed on page {page}')
            return False

        pywikibot.info('<<lightpurple>>Updating links on page {}.'
                       .format(page))
        pywikibot.info(f'Changes to be made: {mods}')
        oldtext = page.get()
        template = (page.namespace() == 10)
        newtext = textlib.replaceLanguageLinks(oldtext, new,
                                               site=page.site,
                                               template=template)
        # This is for now. Later there should be different funktions for each
        # kind
        if not botMayEdit(page):
            pywikibot.info(f'SKIPPING: {page} ', newline=False)
            if template:
                msg = 'should have interwiki links on subpage.'
            else:
                msg = 'is under construction or to be deleted.'
            pywikibot.info(msg)
            return False

        if newtext == oldtext:
            return False

        pywikibot.showDiff(oldtext, newtext)

        # Determine whether we need permission to submit
        ask = False

        # Allow for special case of a self-pointing interwiki link
        if removing and removing != [page.site]:
            self.problem('Found incorrect link to {} in {}'
                         .format(', '.join(x.code for x in removing), page),
                         createneed=False)
            ask = True
        if self.conf.force or self.conf.cleanup:
            ask = False
        if self.conf.confirm and not self.conf.always:
            ask = True

        if not ask:
            # If we do not need to ask, allow
            answer = 'y'
        elif self.conf.autonomous:
            # If we cannot ask, deny permission
            answer = 'n'
        else:  # If we need to ask, do so
            answer = pywikibot.input_choice('Submit?',
                                            [('Yes', 'y'), ('No', 'n'),
                                             ('open in Browser', 'b'),
                                             ('Give up', 'g'),
                                             ('Always', 'a')],
                                            automatic_quit=False)
            if answer == 'b':
                pywikibot.bot.open_webbrowser(page)
                return True
            if answer == 'a':
                # don't ask for the rest of this subject
                self.conf.always = True
                answer = 'y'

        if answer == 'g':
            raise GiveUpOnPage('User asked us to give up')

        # If we got permission to submit, do so
        if answer != 'y':
            raise LinkMustBeRemoved(
                'Found incorrect link to {} in {}'
                .format(', '.join(x.code for x in removing), page))

        self.conf.note('Updating live wiki...')
        timeout = 60
        page.text = newtext
        while True:
            try:
                page.save(summary=mcomment,
                          asynchronous=self.conf.asynchronous,
                          nocreate=True)
            except NoCreateError as e:
                pywikibot.error(e)
                return False
            except LockedPageError:
                pywikibot.info(f'Page {page} is locked. Skipping.')
                raise SaveError('Locked')
            except EditConflictError:
                pywikibot.info(
                    'ERROR putting page: An edit conflict occurred. '
                    'Giving up.')
                raise SaveError('Edit conflict')
            except SpamblacklistError as error:
                pywikibot.info(f'ERROR putting page: {error.url} blacklisted '
                               f'by spamfilter. Giving up.')
                raise SaveError('Spam filter')
            except PageSaveRelatedError as error:
                pywikibot.info(f'ERROR putting page: {error.args}')
                raise SaveError('PageSaveRelatedError')
            except OSError as error:
                if timeout > 3600:
                    raise
                pywikibot.info(f'ERROR putting page: {error.args}')
                pywikibot.info(
                    f'Sleeping {timeout} seconds before trying again.')
                timeout *= 2
                pywikibot.sleep(timeout)
            except ServerError:
                if timeout > 3600:
                    raise
                pywikibot.info('ERROR putting page: ServerError.')
                pywikibot.info(
                    f'Sleeping {timeout} seconds before trying again.')
                timeout *= 2
                pywikibot.sleep(timeout)
            else:
                break
        return True

    @staticmethod
    def reportBacklinks(new, updatedSites) -> None:
        """
        Report missing back links. This will be called from finish() if needed.

        updatedSites is a list that contains all sites we changed, to avoid
        reporting of missing backlinks for pages we already fixed

        """
        # use sets because searching an element is faster than in lists
        expectedPages = set(new.values())
        expectedSites = set(new)

        for site in expectedSites - set(updatedSites):
            page = new[site]
            if page.section():
                continue

            try:
                linkedPages = {pywikibot.Page(link)
                               for link in page.iterlanglinks()}
            except NoPageError:
                pywikibot.warning('Page {} does no longer exist?!'
                                  .format(page))
                break

            # To speed things up, create a dictionary which maps sites
            # to pages. This assumes that there is only one interwiki
            # link per language.
            linkedPagesDict = {p.site: p for p in linkedPages}
            for expectedPage in expectedPages - linkedPages:
                if expectedPage == page:
                    continue
                try:
                    linkedPage = linkedPagesDict[expectedPage.site]
                    pywikibot.warning(
                        '{}: {} does not link to {} but to {}'
                        .format(page.site.family.name,
                                page, expectedPage, linkedPage))
                except KeyError:
                    if not expectedPage.site.is_data_repository():
                        pywikibot.warning('{}: {} does not link to {}'
                                          .format(page.site.family.name,
                                                  page, expectedPage))
            # Check for superfluous links
            for linkedPage in linkedPages:
                if linkedPage in expectedPages:
                    continue
                # Check whether there is an alternative page on
                # that language.
                # In this case, it was already reported above.
                if linkedPage.site not in expectedSites:
                    pywikibot.warning('{}: {} links to incorrect {}'
                                      .format(page.site.family.name,
                                              page, linkedPage))


class InterwikiBot:

    """
    A class keeping track of a list of subjects.

    It controls which pages are queried from which languages when.
    """

    def __init__(self, conf=None) -> None:
        """Initializer."""
        self.subjects = []
        # We count how many pages still need to be loaded per site.
        # This allows us to find out from which site to retrieve pages next
        # in a way that saves bandwidth.
        # sites are keys, integers are values.
        # Modify this only via plus() and minus()!
        self.counts = Counter()
        self.pageGenerator = None
        self.generated = 0
        self.conf = conf
        self.site = pywikibot.Site()

    def add(self, page, hints=None) -> None:
        """Add a single subject to the list."""
        subj = Subject(page, hints=hints, conf=self.conf)
        self.subjects.append(subj)
        for site, count in subj.openSites():
            # Keep correct counters
            self.plus(site, count)

    def setPageGenerator(self, pageGenerator, number=None, until=None) -> None:
        """
        Add a generator of subjects.

        Once the list of subjects gets too small,
        this generator is called to produce more Pages.
        """
        self.pageGenerator = pageGenerator
        self.generateNumber = number
        self.generateUntil = until

    @property
    def dump_titles(self):
        """Return generator of titles for dump file."""
        return (s.origin.title(as_link=True) for s in self.subjects)

    def generateMore(self, number) -> None:
        """Generate more subjects.

        This is called internally when the
        list of subjects becomes too small, but only if there is a
        PageGenerator
        """
        fs = self.firstSubject()
        if fs:
            self.conf.note(f'The first unfinished subject is {fs.origin}')
        pywikibot.info(
            'NOTE: Number of pages queued is {}, trying to add {} more.'
            .format(len(self.subjects), number))
        for _ in range(number):
            for page in self.pageGenerator:
                if page in self.conf.skip:
                    pywikibot.info(f'Skipping: {page} is in the skip list')
                    continue
                if self.conf.skipauto:
                    dictName, year = page.autoFormat()
                    if dictName is not None:
                        pywikibot.info(f'Skipping: {page} is an auto entry '
                                       f'{dictName}({year})')
                        continue
                # Only yield pages that have ( ) in titles
                if self.conf.parenthesesonly and '(' not in page.title():
                    continue
                if page.isTalkPage():
                    pywikibot.info(f'Skipping: {page} is a talk page')
                    continue
                if page.namespace() == 10:
                    loc = None
                    with suppress(KeyError):
                        tmpl, loc = moved_links[page.site.code]
                        del tmpl
                    if loc is not None and loc in page.title():
                        pywikibot.info(
                            'Skipping: {} is a templates subpage'
                            .format(page.title()))
                        continue
                break
            else:  # generator stopped
                break

            if self.generateUntil:
                until = self.generateUntil
                page_namespace = (
                    page.site.namespaces[int(page.namespace())])
                if page_namespace.case == 'first-letter':
                    until = first_upper(until)
                if page.title(with_ns=False) > until:
                    break

            self.add(page, hints=self.conf.hints)
            self.generated += 1
            if self.generateNumber and self.generated >= self.generateNumber:
                break
        else:
            return
        # for loop was exited by break statement
        self.pageGenerator = None

    def firstSubject(self) -> Optional[Subject]:
        """Return the first subject that is still being worked on."""
        return self.subjects[0] if self.subjects else None

    def maxOpenSite(self):
        """
        Return the site that has the most open queries plus the number.

        If there is nothing left, return None.
        Only languages that are TODO for the first Subject are returned.
        """
        if not self.firstSubject():
            return None

        oc = dict(self.firstSubject().openSites())
        if not oc:
            # The first subject is done. This might be a recursive call made
            # because we have to wait before submitting another modification to
            # go live. Select any language from counts.
            oc = self.counts

        if self.site in oc:
            return self.site

        for site, _ in self.counts.most_common():
            if site in oc:
                return site
        return None

    def selectQuerySite(self):
        """Select the site the next query should go out for."""
        # How many home-language queries we still have?
        mycount = self.counts[self.site]
        # Do we still have enough subjects to work on for which the
        # home language has been retrieved? This is rough, because
        # some subjects may need to retrieve a second home-language page!
        if len(self.subjects) - mycount < self.conf.minsubjects:
            # Can we make more home-language queries by adding subjects?
            if self.pageGenerator and mycount < self.conf.maxquerysize:
                timeout = 60
                while timeout < 3600:
                    try:
                        self.generateMore(self.conf.maxquerysize - mycount)
                    except ServerError:
                        # Could not extract allpages special page?
                        pywikibot.error('could not retrieve more pages. '
                                        'Will try again in {} seconds'
                                        .format(timeout))
                        pywikibot.sleep(timeout)
                        timeout *= 2
                    else:
                        break
            # If we have a few, getting the home language is a good thing.
            if not self.conf.restore_all and self.counts[self.site] > 4:
                return self.site
        # If getting the home language doesn't make sense, see how many
        # foreign page queries we can find.
        return self.maxOpenSite()

    def oneQuery(self) -> bool:
        """
        Perform one step in the solution process.

        Returns True if pages could be preloaded, or false
        otherwise.
        """
        # First find the best language to work on
        site = self.selectQuerySite()
        if site is None:
            pywikibot.info('NOTE: Nothing left to do')
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
                if len(pageGroup) >= self.conf.maxquerysize:
                    # We have found enough pages to fill the bandwidth.
                    break

        if not pageGroup:
            pywikibot.info('NOTE: Nothing left to do 2')
            return False

        # Get the content of the assembled list in one blow
        gen = site.preloadpages(pageGroup, templates=True, langlinks=True,
                                pageprops=True, quiet=False)
        for _ in gen:
            # we don't want to do anything with them now. The
            # page contents will be read via the Subject class.
            pass

        # Tell all of the subjects that the promised work is done
        for subject in subjectGroup:
            subject.batchLoaded(self)
        return True

    def queryStep(self) -> None:
        """Delete the ones that are done now."""
        self.oneQuery()
        for i in range(len(self.subjects) - 1, -1, -1):
            subj = self.subjects[i]
            if subj.isDone():
                subj.finish()
                del self.subjects[i]

    def isDone(self) -> bool:
        """Check whether there is still more work to do."""
        return not self.subjects and self.pageGenerator is None

    def plus(self, site, count: int = 1) -> None:
        """Helper routine that the Subject class expects in a counter."""
        self.counts[site] += count

    def minus(self, site, count: int = 1) -> None:
        """Helper routine that the Subject class expects in a counter."""
        self.counts[site] -= count
        self.counts = +self.counts  # remove zero and negative counts

    def run(self) -> None:
        """Start the process until finished."""
        while not self.isDone():
            self.queryStep()


def compareLanguages(old, new, insite, summary):
    """Compare changes and setup i18n message."""
    oldiw = set(old)
    newiw = set(new)

    # sort by language code
    adding = sorted(newiw - oldiw)
    removing = sorted(oldiw - newiw)
    modifying = sorted(site for site in oldiw & newiw
                       if old[site] != new[site])

    if not summary and len(adding) + len(removing) + len(modifying) <= 3:
        # Use an extended format for the string linking to all added pages.

        def fmt(d, site):
            return str(d[site])
    else:
        # Use short format, just the language code
        def fmt(d, site):
            return site.code

    mods = mcomment = ''

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
        mcomment += summary
        comma = insite.mediawiki_message('comma-separator')

        changes = {'adding': comma.join(fmt(new, x) for x in adding),
                   'removing': comma.join(fmt(old, x) for x in removing),
                   'modifying': comma.join(fmt(new, x) for x in modifying),
                   'from': '' if not useFrom else old[modifying[0]]}
        en_changes = {'adding': ', '.join(fmt(new, x) for x in adding),
                      'removing': ', '.join(fmt(old, x) for x in removing),
                      'modifying': ', '.join(fmt(new, x) for x in modifying),
                      'from': '' if not useFrom else old[modifying[0]]}

        mcomment += i18n.twtranslate(insite, commentname, changes)
        mods = i18n.twtranslate('en', commentname, en_changes)

    return mods, mcomment, adding, removing, modifying


def botMayEdit(page) -> bool:
    """Test for allowed edits."""
    tmpl = []
    with suppress(KeyError):
        tmpl, _ = moved_links[page.site.code]

    if not isinstance(tmpl, list):
        tmpl = [tmpl]

    with suppress(KeyError):
        tmpl += ignoreTemplates[page.site.code]

    tmpl += ignoreTemplates['_default']
    if tmpl != []:
        templates = page.templatesWithParams()
        for template in templates:
            if template[0].title(with_ns=False).lower() in tmpl:
                return False
    return True


def page_empty_check(page) -> bool:
    """
    Return True if page should be skipped as it is almost empty.

    Pages in content namespaces are considered empty if they contain less than
    50 characters, and other pages are considered empty if they are not
    category pages and contain less than 4 characters excluding interlanguage
    links and categories.
    """
    txt = page.text
    # Check if the page is in content namespace
    if page.namespace().content:
        # Check if the page contains at least 50 characters
        return len(txt) < 50

    if not page.is_categorypage():
        txt = textlib.removeLanguageLinks(txt, site=page.site)
        txt = textlib.removeCategoryLinks(txt, site=page.site)
        return len(txt) < 4

    return False


class InterwikiDumps(OptionHandler):

    """Handle interwiki dumps."""

    available_options = {
        'do_continue': False,
        'restore_all': False
    }

    FILE_PATTERN = '{site.family.name}-{site.code}.txt'

    def __init__(self, **kwargs) -> None:
        """Initializer.

        :keyword do_continue: If true, continue alphabetically starting at the
            last of the dumped pages.
        """
        self.site = kwargs.pop('site', pywikibot.Site())
        super().__init__(**kwargs)

        self.restored_files = set()
        self._next_page = '!'
        self._next_namespace = 0
        self.path = pywikibot.config.datafilepath('data', 'interwiki-dumps')

    @property
    def next_page(self):
        """Return next page title string for continue option."""
        if self._next_page == '!':
            pywikibot.info('Dump file is empty! Starting at the beginning.')
        return self._next_page

    @property
    def next_namespace(self):
        """Return next page namespace for continue option."""
        return self._next_namespace

    def remove(self, filename: str) -> None:
        """Remove filename from restored files.

        :param filename: A filename to be removed from restored set.
        """
        with suppress(KeyError):
            self.restored_files.remove(filename)

    def get_files(self):
        """Get dump files from directory."""
        pattern = r'(?P<file>(?P<fam>[a-z]+)-(?P<code>[a-z]+)\.txt)'
        for filename in os.listdir(self.path):
            found = re.fullmatch(pattern, filename)
            if found:
                yield (found['file'],
                       pywikibot.Site(found['code'], found['fam']))

    @property
    def files(self):
        """Return file generator depending on restore_all option.

        rtype: generator
        """
        if self.opt.restore_all:
            return self.get_files()
        return iter([(self.FILE_PATTERN.format(site=self.site), self.site)])

    def read_dump(self):
        """Read the dump file.

        :rtype: generator
        """
        for tail, site in self.files:
            filename = os.path.join(self.path, tail)

            if not os.path.exists(filename):
                pywikibot.info(tail + ' does not exist.')
                continue

            pywikibot.info('Retrieving pages from dump file ' + tail)
            for page in pagegenerators.TextIOPageGenerator(filename, site):
                if site == self.site:
                    self._next_page = page.title(with_ns=False) + '!'
                    self._next_namespace = page.namespace()
                yield page

            self.restored_files.add(filename)

        if self.opt.do_continue:
            yield from self.site.allpages(start=self.next_page,
                                          namespace=self.next_namespace,
                                          filterredir=False)

    def write_dump(self, iterable: Iterable, append: bool = True) -> None:
        """Write dump file.

        :param iterable: an iterable of page titles to be dumped.
        :param append: if a dump already exits, append the page titles to it
            if True else overwrite it.
        """
        filename = os.path.join(self.path,
                                self.FILE_PATTERN.format(site=self.site))
        mode = 'appended' if append else 'written'
        with codecs.open(filename, mode[0], 'utf-8') as f:
            f.write('\r\n'.join(iterable))
            f.write('\r\n')
        pywikibot.info(
            f'Dump {self.site.code} ({self.site.family.name}) {mode}.')
        self.remove(filename)

    def delete_dumps(self) -> None:
        """Delete processed dumps."""
        for filename in self.restored_files:
            tail = os.path.split(filename)[-1]
            try:
                os.remove(filename)
            except OSError as e:
                pywikibot.error(
                    f'Cannot delete {tail} due to\n{e}\nDo it manually.')
            else:
                pywikibot.info(f'Dumpfile {tail} deleted')


def main(*args: str) -> None:
    """Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    singlePageTitle = ''
    opthintsonly = False
    # Which namespaces should be processed?
    # default to [] which means all namespaces will be processed
    namespaces = []
    number = None
    until = None
    # a normal PageGenerator (which doesn't give hints, only Pages)
    hintlessPageGen = None
    optContinue = False
    optRestore = False
    append = True
    newPages = None

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    iwconf = InterwikiBotConfig()
    for arg in local_args:
        if iwconf.readOptions(arg):
            continue

        if arg.startswith('-years'):
            # Look if user gave a specific year at which to start
            # Must be a natural number or negative integer.
            if len(arg) > 7 and (arg[7:].isdigit()
                                 or (arg[7] == '-' and arg[8:].isdigit())):
                startyear = int(arg[7:])
            else:
                startyear = 1
            # avoid problems where year pages link to centuries etc.
            iwconf.followredirect = False
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
            iwconf.restore_all = arg[9:].lower() == 'all'
            optRestore = not iwconf.restore_all
        elif arg == '-continue':
            optContinue = True
        elif arg == '-hintsonly':
            opthintsonly = True
        elif arg.startswith('-namespace:'):
            try:
                namespaces.append(int(arg[11:]))
            except ValueError:
                namespaces.append(arg[11:])
        elif arg.startswith('-number:'):
            number = int(arg[8:])
        elif arg.startswith('-until:'):
            until = arg[7:]
        else:
            if not genFactory.handle_arg(arg) and not singlePageTitle:
                singlePageTitle = arg

    # Do not use additional summary with autonomous mode
    if iwconf.autonomous:
        iwconf.summary = ''
    elif iwconf.summary:
        iwconf.summary += '; '

    site = pywikibot.Site()
    # ensure that we don't try to change main page
    mainpagename = site.siteinfo['mainpage']
    iwconf.skip.add(pywikibot.Page(site, mainpagename))

    dump = InterwikiDumps(site=site, do_continue=optContinue,
                          restore_all=iwconf.restore_all)

    if newPages is not None:
        if not namespaces:
            ns = 0
        elif len(namespaces) == 1:
            ns = namespaces[0]
            if isinstance(ns, str) and ns != 'all':
                index = site.namespaces.lookup_name(ns)
                if index is None:
                    raise ValueError('Unknown namespace: ' + ns)
                ns = index.id
            namespaces = []
        else:
            ns = 'all'
        hintlessPageGen = pagegenerators.NewpagesPageGenerator(total=newPages,
                                                               namespaces=ns)

    elif optRestore or optContinue or iwconf.restore_all:
        hintlessPageGen = dump.read_dump()

    bot = InterwikiBot(iwconf)

    if not hintlessPageGen:
        hintlessPageGen = genFactory.getCombinedGenerator()
    if hintlessPageGen:
        if len(namespaces) > 0:
            hintlessPageGen = pagegenerators.NamespaceFilterPageGenerator(
                hintlessPageGen, namespaces, site)
        # we'll use iter() to create make a next() function available.
        bot.setPageGenerator(iter(hintlessPageGen), number=number, until=until)
    else:
        if not singlePageTitle and not opthintsonly:
            singlePageTitle = pywikibot.input('Which page to check:')
        if singlePageTitle:
            singlePage = pywikibot.Page(pywikibot.Site(), singlePageTitle)
        else:
            singlePage = None
        bot.add(singlePage, hints=iwconf.hints)

    append = not (optRestore or optContinue or iwconf.restore_all)
    try:
        bot.run()
    except KeyboardInterrupt:
        dump.write_dump(bot.dump_titles, append)
    except Exception:  # pragma: no cover
        pywikibot.exception()
        dump.write_dump(bot.dump_titles, append)
    else:
        pywikibot.info('Script terminated sucessfully.')
    finally:
        dump.delete_dumps()


if __name__ == '__main__':
    main()
