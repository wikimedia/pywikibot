# -*- coding: utf-8  -*-
"""
This module offers a wide variety of page generators.

A page generator is an
object that is iterable (see http://legacy.python.org/dev/peps/pep-0255/ ) and
that yields page objects on which other scripts can then work.

Pagegenerators.py cannot be run as script. For testing purposes listpages.py can
be used instead, to print page titles to standard output.

These parameters are supported to specify which pages titles to print:

&params;
"""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import codecs
import datetime
import itertools
import re
import sys
import time

import pywikibot
from pywikibot import date, config, i18n
from pywikibot.tools import (
    deprecated,
    deprecated_args,
    DequeGenerator,
    intersect_generators,
)
from pywikibot.comms import http
import pywikibot.data.wikidataquery as wdquery

if sys.version_info[0] > 2:
    basestring = (str, )

_logger = "pagegenerators"

# ported from version 1 for backwards-compatibility
# most of these functions just wrap a Site or Page method that returns
# a generator

parameterHelp = u"""\

-cat              Work on all pages which are in a specific category.
                  Argument can also be given as "-cat:categoryname" or
                  as "-cat:categoryname|fromtitle" (using # instead of |
                  is also allowed in this one and the following)

-catr             Like -cat, but also recursively includes pages in
                  subcategories, sub-subcategories etc. of the
                  given category.
                  Argument can also be given as "-catr:categoryname" or
                  as "-catr:categoryname|fromtitle".

-subcats          Work on all subcategories of a specific category.
                  Argument can also be given as "-subcats:categoryname" or
                  as "-subcats:categoryname|fromtitle".

-subcatsr         Like -subcats, but also includes sub-subcategories etc. of
                  the given category.
                  Argument can also be given as "-subcatsr:categoryname" or
                  as "-subcatsr:categoryname|fromtitle".

-uncat            Work on all pages which are not categorised.

-uncatcat         Work on all categories which are not categorised.

-uncatfiles       Work on all files which are not categorised.

-file             Read a list of pages to treat from the named text file.
                  Page titles in the file may be either enclosed with
                  [[brackets]], or be separated by new lines.
                  Argument can also be given as "-file:filename".

-filelinks        Work on all pages that use a certain image/media file.
                  Argument can also be given as "-filelinks:filename".

-search           Work on all pages that are found in a MediaWiki search
                  across all namespaces.

-<logevent>log    Work on articles that were on a specified special:log.
                  You have options for every type of logs given by the
                 <logevent> parameter which could be one of the following:
                      block, protect, rights, delete, upload, move, import,
                      patrol, merge, suppress, review, stable, gblblock,
                      renameuser, globalauth, gblrights, abusefilter, newusers
                  Examples:
                  -movelog gives 500 pages from move log (should be redirects)
                  -deletelog:10 gives 10 pages from deletion log
                  -protect:Dummy gives 500 pages from protect by user Dummy
                  -patrol:Dummy;20 gives 20 pages patroled by user Dummy
                  In some cases this must be written as -patrol:"Dummy;20"

-namespaces       Filter the page generator to only yield pages in the
-namespace        specified namespaces. Separate multiple namespace
-ns               numbers with commas. Example "-ns:0,2,4"
                  If used with -newpages, -namepace/ns must be provided
                  before -newpages.
                  If used with -recentchanges, efficiency is improved if
                  -namepace/ns is provided before -recentchanges.

-interwiki        Work on the given page and all equivalent pages in other
                  languages. This can, for example, be used to fight
                  multi-site spamming.
                  Attention: this will cause the bot to modify
                  pages on several wiki sites, this is not well tested,
                  so check your edits!

-limit:n          When used with any other argument that specifies a set
                  of pages, work on no more than n pages in total.

-links            Work on all pages that are linked from a certain page.
                  Argument can also be given as "-links:linkingpagetitle".

-imagesused       Work on all images that contained on a certain page.
                  Argument can also be given as "-imagesused:linkingpagetitle".

-newimages        Work on the 100 newest images. If given as -newimages:x,
                  will work on the x newest images.

-newpages         Work on the most recent new pages. If given as -newpages:x,
                  will work on the x newest pages.

-recentchanges    Work on the pages with the most recent changes. If
                  given as -recentchanges:x, will work on the x most recently
                  changed pages.

-ref              Work on all pages that link to a certain page.
                  Argument can also be given as "-ref:referredpagetitle".

-start            Specifies that the robot should go alphabetically through
                  all pages on the home wiki, starting at the named page.
                  Argument can also be given as "-start:pagetitle".

                  You can also include a namespace. For example,
                  "-start:Template:!" will make the bot work on all pages
                  in the template namespace.

-prefixindex      Work on pages commencing with a common prefix.

-step:n           When used with any other argument that specifies a set
                  of pages, only retrieve n pages at a time from the wiki
                  server.

-titleregex       Work on titles that match the given regular expression.

-transcludes      Work on all pages that use a certain template.
                  Argument can also be given as "-transcludes:Title".

-unusedfiles      Work on all description pages of images/media files that are
                  not used anywhere.
                  Argument can be given as "-unusedfiles:n" where
                  n is the maximum number of articles to work on.

-lonelypages      Work on all articles that are not linked from any other
                  article.
                  Argument can be given as "-lonelypages:n" where
                  n is the maximum number of articles to work on.

-unwatched        Work on all articles that are not watched by anyone.
                  Argument can be given as "-unwatched:n" where
                  n is the maximum number of articles to work on.

-usercontribs     Work on all articles that were edited by a certain user.
                  (Example : -usercontribs:DumZiBoT)

-weblink          Work on all articles that contain an external link to
                  a given URL; may be given as "-weblink:url"

-withoutinterwiki Work on all pages that don't have interlanguage links.
                  Argument can be given as "-withoutinterwiki:n" where
                  n is the total to fetch.

-mysqlquery       Takes a Mysql query string like
                  "SELECT page_namespace, page_title, FROM page
                  WHERE page_namespace = 0" and works on the resulting pages.

-wikidataquery    Takes a WikidataQuery query string like claim[31:12280]
                  and works on the resulting pages.

-random           Work on random pages returned by [[Special:Random]].
                  Can also be given as "-random:n" where n is the number
                  of pages to be returned, otherwise the default is 10 pages.

-randomredirect   Work on random redirect pages returned by
                  [[Special:RandomRedirect]]. Can also be given as
                  "-randomredirect:n" where n is the number of pages to be
                  returned, else 10 pages are returned.

-untagged         Work on image pages that don't have any license template on a
                  site given in the format "<language>.<project>.org, e.g.
                  "ja.wikipedia.org" or "commons.wikimedia.org".
                  Using an external Toolserver tool.

-google           Work on all pages that are found in a Google search.
                  You need a Google Web API license key. Note that Google
                  doesn't give out license keys anymore. See google_key in
                  config.py for instructions.
                  Argument can also be given as "-google:searchstring".

-yahoo            Work on all pages that are found in a Yahoo search.
                  Depends on python module pYsearch.  See yahoo_appid in
                  config.py for instructions.

-page             Work on a single page. Argument can also be given as
                  "-page:pagetitle", and supplied multiple times for
                  multiple pages.

-grep             A regular expression that needs to match the article
                  otherwise the page won't be returned.
                  Multiple -grep:regexpr can be provided and the page will
                  be returned if content is matched by any of the regexpr
                  provided.
                  Case insensitive regular expressions will be used and
                  dot matches any character, including a newline.

-intersect        Work on the intersection of all the provided generators.
"""

docuReplacements = {'&params;': parameterHelp}

# if a bot uses GeneratorFactory, the module should include the line
#   docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}
# and include the marker &params; in the module's docstring
#
# We manually include it so the parameters show up in the auto-generated
# module documentation:

__doc__ = __doc__.replace("&params;", parameterHelp)


class GeneratorFactory(object):

    """Process command line arguments and return appropriate page generator.

    This factory is responsible for processing command line arguments
    that are used by many scripts and that determine which pages to work on.
    """

    def __init__(self, site=None):
        """
        Constructor.

        @param site: Site for generator results.
        @type site: L{pywikibot.site.BaseSite}
        """
        self.gens = []
        self.namespaces = []
        self.step = None
        self.limit = None
        self.articlefilter_list = []
        self.intersect = False
        self._site = site

    @property
    def site(self):
        """
        Generator site.

        @return: Site given to constructor, otherwise the default Site.
        @rtype: L{pywikibot.site.BaseSite}
        """
        if not self._site:
            self._site = pywikibot.Site()
        return self._site

    def getCombinedGenerator(self, gen=None):
        """Return the combination of all accumulated generators.

        Only call this after all arguments have been parsed.
        """
        if gen:
            self.gens.insert(0, gen)

        for i in range(len(self.gens)):
            if isinstance(self.gens[i], pywikibot.data.api.QueryGenerator):
                if self.namespaces:
                    self.gens[i].set_namespace(self.namespaces)
                if self.step:
                    self.gens[i].set_query_increment(self.step)
                if self.limit:
                    self.gens[i].set_maximum_items(self.limit)
            else:
                if self.namespaces:
                    self.gens[i] = NamespaceFilterPageGenerator(self.gens[i],
                                                                self.namespaces)
                if self.limit:
                    self.gens[i] = itertools.islice(self.gens[i], self.limit)
        if len(self.gens) == 0:
            return None
        elif len(self.gens) == 1:
            gensList = self.gens[0]
            dupfiltergen = gensList
            if self.intersect:
                pywikibot.input(u'Only one generator. '
                                u'Param "-intersect" has no meaning or effect.')
        else:
            if self.intersect:
                gensList = intersect_generators(self.gens)
                # By definition no duplicates are possible.
                dupfiltergen = gensList
            else:
                gensList = CombinedPageGenerator(self.gens)
                dupfiltergen = DuplicateFilterPageGenerator(gensList)

        if self.articlefilter_list:
            return RegexBodyFilterPageGenerator(
                PreloadingGenerator(dupfiltergen), self.articlefilter_list)
        else:
            return dupfiltergen

    def getCategoryGen(self, arg, recurse=False, content=False,
                       gen_func=None):
        """Return generator based on Category defined by arg and gen_func."""
        categoryname = arg.partition(':')[2]
        if not categoryname:
            categoryname = i18n.input('pywikibot-enter-category-name')
        categoryname = categoryname.replace('#', '|')

        categoryname, sep, startfrom = categoryname.partition('|')
        if not startfrom:
            startfrom = None

        # Insert Category: before category name to avoid parsing problems in
        # Link.parse() when categoryname contains ":";
        # Part before ":" might be interpreted as an interwiki prefix
        prefix = categoryname.split(":", 1)[0]  # whole word if ":" not present
        if prefix not in self.site.namespaces[14]:
            categoryname = u'{0}:{1}'.format(self.site.namespace(14),
                                             categoryname)
        cat = pywikibot.Category(pywikibot.Link(categoryname,
                                                defaultNamespace=14))

        return gen_func(cat,
                        start=startfrom,
                        recurse=recurse,
                        content=content)

    def handleArg(self, arg):
        """Parse one argument at a time.

        If it is recognized as an argument that specifies a generator, a
        generator is created and added to the accumulation list, and the
        function returns true.  Otherwise, it returns false, so that caller
        can try parsing the argument. Call getCombinedGenerator() after all
        arguments have been parsed to get the final output generator.

        """
        gen = None
        if arg.startswith('-filelinks'):
            fileLinksPageTitle = arg[11:]
            if not fileLinksPageTitle:
                fileLinksPageTitle = i18n.input(
                    'pywikibot-enter-file-links-processing')
            if fileLinksPageTitle.startswith(self.site.namespace(6)
                                             + ":"):
                fileLinksPage = pywikibot.FilePage(self.site,
                                                   fileLinksPageTitle)
            else:
                fileLinksPage = pywikibot.FilePage(self.site,
                                                   'Image:' +
                                                   fileLinksPageTitle)
            gen = FileLinksGenerator(fileLinksPage)
        elif arg.startswith('-unusedfiles'):
            if len(arg) == 12:
                gen = UnusedFilesGenerator(site=self.site)
            else:
                gen = UnusedFilesGenerator(total=int(arg[13:]), site=self.site)
        elif arg.startswith('-lonelypages'):
            if len(arg) == 12:
                gen = LonelyPagesPageGenerator(site=self.site)
            else:
                gen = LonelyPagesPageGenerator(total=int(arg[13:]),
                                               site=self.site)
        elif arg.startswith('-unwatched'):
            if len(arg) == 10:
                gen = UnwatchedPagesPageGenerator(site=self.site)
            else:
                gen = UnwatchedPagesPageGenerator(total=int(arg[11:]),
                                                  site=self.site)
        elif arg.startswith('-usercontribs'):
            gen = UserContributionsGenerator(arg[14:])
        elif arg.startswith('-withoutinterwiki'):
            if len(arg) == 17:
                gen = WithoutInterwikiPageGenerator(site=self.site)
            else:
                gen = WithoutInterwikiPageGenerator(total=int(arg[18:]),
                                                    site=self.site)
        elif arg.startswith('-interwiki'):
            title = arg[11:]
            if not title:
                title = i18n.input('pywikibot-enter-page-processing')
            page = pywikibot.Page(pywikibot.Link(title,
                                                 self.site))
            gen = InterwikiPageGenerator(page)
        elif arg.startswith('-randomredirect'):
            if len(arg) == 15:
                gen = RandomRedirectPageGenerator(site=self.site)
            else:
                gen = RandomRedirectPageGenerator(total=int(arg[16:]),
                                                  site=self.site)
        elif arg.startswith('-random'):
            if len(arg) == 7:
                gen = RandomPageGenerator(site=self.site)
            else:
                gen = RandomPageGenerator(total=int(arg[8:]), site=self.site)
        elif arg.startswith('-recentchanges'):
            if len(arg) >= 15:
                gen = RecentChangesPageGenerator(namespaces=self.namespaces,
                                                 total=int(arg[15:]),
                                                 site=self.site)
            else:
                gen = RecentChangesPageGenerator(namespaces=self.namespaces,
                                                 total=60,
                                                 site=self.site)
            gen = DuplicateFilterPageGenerator(gen)
        elif arg.startswith('-file'):
            textfilename = arg[6:]
            if not textfilename:
                textfilename = pywikibot.input(
                    u'Please enter the local file name:')
            gen = TextfilePageGenerator(textfilename, site=self.site)
        elif arg.startswith('-namespace') or arg.startswith('-ns'):
            value = None
            if arg.startswith('-ns:'):
                value = arg[len('-ns:'):]
            elif arg.startswith('-namespace:'):
                value = arg[len('-namespace:'):]
            elif arg.startswith('-namespaces:'):
                value = arg[len('-namespaces:'):]
            if not value:
                value = pywikibot.input(
                    u'What namespace are you filtering on?')
            try:
                self.namespaces.extend(
                    [int(ns) for ns in value.split(",")]
                )
            except ValueError:
                pywikibot.output(u'Invalid namespaces argument: %s' % value)
                return False
            return True
        elif arg.startswith('-step'):
            if len(arg) == len('-step'):
                self.step = int(pywikibot.input("What is the step value?"))
            else:
                self.step = int(arg[len('-step:'):])
            return True
        elif arg.startswith('-limit'):
            if len(arg) == len('-limit'):
                self.limit = int(pywikibot.input("What is the limit value?"))
            else:
                self.limit = int(arg[len('-limit:'):])
            return True
        elif arg.startswith('-catr'):
            gen = self.getCategoryGen(arg, recurse=True,
                                      gen_func=CategorizedPageGenerator)
        elif arg.startswith('-category'):
            gen = self.getCategoryGen(arg, gen_func=CategorizedPageGenerator)
        elif arg.startswith('-cat'):
            gen = self.getCategoryGen(arg, gen_func=CategorizedPageGenerator)
        elif arg.startswith('-subcatsr'):
            gen = self.getCategoryGen(arg, recurse=True,
                                      gen_func=SubCategoriesPageGenerator)
        elif arg.startswith('-subcats'):
            gen = self.getCategoryGen(arg,
                                      gen_func=SubCategoriesPageGenerator)
        elif arg.startswith('-page'):
            if len(arg) == len('-page'):
                gen = [pywikibot.Page(
                    pywikibot.Link(
                        pywikibot.input(
                            u'What page do you want to use?'),
                        self.site)
                )]
            else:
                gen = [pywikibot.Page(pywikibot.Link(arg[len('-page:'):],
                                                     self.site)
                                      )]
        elif arg.startswith('-uncatfiles'):
            gen = UnCategorizedImageGenerator(site=self.site)
        elif arg.startswith('-uncatcat'):
            gen = UnCategorizedCategoryGenerator(site=self.site)
        elif arg.startswith('-uncat'):
            gen = UnCategorizedPageGenerator(site=self.site)
        elif arg.startswith('-ref'):
            referredPageTitle = arg[5:]
            if not referredPageTitle:
                referredPageTitle = pywikibot.input(
                    u'Links to which page should be processed?')
            referredPage = pywikibot.Page(pywikibot.Link(referredPageTitle,
                                                         self.site))
            gen = ReferringPageGenerator(referredPage)
        elif arg.startswith('-links'):
            linkingPageTitle = arg[7:]
            if not linkingPageTitle:
                linkingPageTitle = pywikibot.input(
                    u'Links from which page should be processed?')
            linkingPage = pywikibot.Page(pywikibot.Link(linkingPageTitle,
                                                        self.site))
            gen = LinkedPageGenerator(linkingPage)
        elif arg.startswith('-weblink'):
            url = arg[9:]
            if not url:
                url = pywikibot.input(
                    u'Pages with which weblink should be processed?')
            gen = LinksearchPageGenerator(url, site=self.site)
        elif arg.startswith('-transcludes'):
            transclusionPageTitle = arg[len('-transcludes:'):]
            if not transclusionPageTitle:
                transclusionPageTitle = pywikibot.input(
                    u'Pages that transclude which page should be processed?')
            transclusionPage = pywikibot.Page(
                pywikibot.Link(transclusionPageTitle,
                               defaultNamespace=10,
                               source=self.site))
            gen = ReferringPageGenerator(transclusionPage,
                                         onlyTemplateInclusion=True)
        elif arg.startswith('-start'):
            firstPageTitle = arg[7:]
            if not firstPageTitle:
                firstPageTitle = pywikibot.input(
                    u'At which page do you want to start?')
            firstpagelink = pywikibot.Link(firstPageTitle,
                                           self.site)
            namespace = firstpagelink.namespace
            firstPageTitle = firstpagelink.title
            gen = AllpagesPageGenerator(firstPageTitle, namespace,
                                        includeredirects=False,
                                        site=self.site)
        elif arg.startswith('-prefixindex'):
            prefix = arg[13:]
            namespace = None
            if not prefix:
                prefix = pywikibot.input(
                    u'What page names are you looking for?')
            gen = PrefixingPageGenerator(prefix=prefix, site=self.site)
        elif arg.startswith('-newimages'):
            limit = arg[11:] or pywikibot.input(
                u'How many images do you want to load?')
            gen = NewimagesPageGenerator(total=int(limit), site=self.site)
        elif arg.startswith('-newpages'):
            # partial workaround for bug 67249
            # to use -namespace/ns with -newpages, -ns must be given
            # before -newpages
            # otherwise default namespace is 0
            namespaces = self.namespaces or 0
            total = 60
            if len(arg) >= 10:
                total = int(arg[10:])
            gen = NewpagesPageGenerator(namespaces=namespaces,
                                        total=total,
                                        site=self.site)
        elif arg.startswith('-imagesused'):
            imagelinkstitle = arg[len('-imagesused:'):]
            if not imagelinkstitle:
                imagelinkstitle = pywikibot.input(
                    u'Images on which page should be processed?')
            imagelinksPage = pywikibot.Page(pywikibot.Link(imagelinkstitle,
                                                           self.site))
            gen = ImagesPageGenerator(imagelinksPage)
        elif arg.startswith('-search'):
            mediawikiQuery = arg[8:]
            if not mediawikiQuery:
                mediawikiQuery = pywikibot.input(
                    u'What do you want to search for?')
            # In order to be useful, all namespaces are required
            gen = SearchPageGenerator(mediawikiQuery,
                                      namespaces=[], site=self.site)
        elif arg.startswith('-google'):
            gen = GoogleSearchPageGenerator(arg[8:])
        elif arg.startswith('-titleregex'):
            if len(arg) == 11:
                regex = pywikibot.input(u'What page names are you looking for?')
            else:
                regex = arg[12:]
            gen = RegexFilterPageGenerator(self.site.allpages(), regex)
        elif arg.startswith('-grep'):
            if len(arg) == 5:
                self.articlefilter_list.append(pywikibot.input(
                    u'Which pattern do you want to grep?'))
            else:
                self.articlefilter_list.append(arg[6:])
            return True
        elif arg.startswith('-yahoo'):
            gen = YahooSearchPageGenerator(arg[7:], site=self.site)
        elif arg.startswith('-untagged'):
            gen = UntaggedPageGenerator(arg[10:], site=self.site)
        elif arg.startswith('-wikidataquery'):
            query = arg[len('-wikidataquery:'):]
            if not query:
                query = pywikibot.input(
                    u'WikidataQuery string:')
            gen = WikidataQueryPageGenerator(query, site=self.site)
        elif arg.startswith('-mysqlquery'):
            query = arg[len('-mysqlquery:'):]
            if not query:
                query = pywikibot.input(
                    u'Mysql query string:')
            gen = MySQLPageGenerator(query, site=self.site)
        elif arg.startswith('-intersect'):
            self.intersect = True
            return True
        elif arg.startswith('-'):
            mode, log, user = arg.partition('log')
            # exclude -log, -nolog
            if log == 'log' and mode not in ['-', '-no']:
                total = 500
                if not user:
                    user = None
                else:
                    try:
                        total = int(user[1:])
                        user = None
                    except ValueError:
                        user = user[1:]
                        result = user.split(';')
                        user = result[0]
                        try:
                            total = int(result[1])
                        except (ValueError, IndexError):
                            pywikibot.error(
                                u'Value specified after ";" not an int.')
                            return False
                    # TODO: Check if mode[1:] is one of the allowed log types
                gen = LogeventsPageGenerator(mode[1:], user, total=total)

        if gen:
            self.gens.append(gen)
            return True
        else:
            return False


def AllpagesPageGenerator(start='!', namespace=0, includeredirects=True,
                          site=None, step=None, total=None, content=False):
    """
    Iterate Page objects for all titles in a single namespace.

    If includeredirects is False, redirects are not included. If
    includeredirects equals the string 'only', only redirects are added.

    @param step: Maximum number of pages to retrieve per API query
    @type step: int
    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param content: If True, load current version of each page (default False)
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}

    """
    if site is None:
        site = pywikibot.Site()
    if includeredirects:
        if includeredirects == 'only':
            filterredir = True
        else:
            filterredir = None
    else:
        filterredir = False
    return site.allpages(start=start, namespace=namespace,
                         filterredir=filterredir, step=step, total=total,
                         content=content)


def PrefixingPageGenerator(prefix, namespace=None, includeredirects=True,
                           site=None, step=None, total=None, content=False):
    """
    Prefixed Page generator.

    @param step: Maximum number of pages to retrieve per API query
    @type step: int
    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param content: If True, load current version of each page (default False)
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    prefixlink = pywikibot.Link(prefix, site)
    if namespace is None:
        namespace = prefixlink.namespace
    title = prefixlink.title
    if includeredirects:
        if includeredirects == 'only':
            filterredir = True
        else:
            filterredir = None
    else:
        filterredir = False
    return site.allpages(prefix=title, namespace=namespace,
                         filterredir=filterredir, step=step, total=total,
                         content=content)


@deprecated_args(number="total", mode="logtype", repeat=None)
def LogeventsPageGenerator(logtype=None, user=None, site=None,
                           namespace=0, total=None):
    """
    Generate Pages for specified modes of logevents.

    @param logtype: Mode of logs to retrieve
    @type logtype: basestring
    @param user: User of logs retrieved
    @type user: basestring
    @param site: Site for generator results
    @type site: L{pywikibot.site.BaseSite}
    @param namespace: Namespace to retrieve logs from
    @type namespace: int
    @param total: Maximum number of pages to retrieve in total
    @type total: int
    """
    if site is None:
        site = pywikibot.Site()
    for entry in site.logevents(total=total, logtype=logtype,
                                user=user, namespace=namespace):
        yield entry.title()


@deprecated("LogeventsPageGenerator")
@deprecated_args(number="total", mode="logtype", repeat=None)
def LogpagesPageGenerator(total=500, logtype='', user=None,
                          site=None, namespace=[]):
    """
    Generate Pages for specified modes of logevents.

    This is the backwards compatible one.
    See LogeventsPageGenerator

    @param mode: Mode of logs to retrieve
    @type mode: basestring
    @param user: User of logs retrieved
    @type user: basestring
    @param site: Site for generator results
    @type site: L{pywikibot.site.BaseSite}
    @param namespace: Namespace to retrieve logs from
    @type namespace: int
    @param total: Maximum number of pages to retrieve in total
    @type total: int
    """
    return LogeventsPageGenerator(total=total, logtype=logtype, user=user,
                                  site=site, namespace=namespace)


@deprecated_args(number="total", namespace="namespaces", repeat=None)
def NewpagesPageGenerator(get_redirect=False, site=None,
                          namespaces=[0, ], step=None, total=None):
    """
    Iterate Page objects for all new titles in a single namespace.

    @param step: Maximum number of pages to retrieve per API query
    @type step: int
    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    # API does not (yet) have a newpages function, so this tries to duplicate
    # it by filtering the recentchanges output
    # defaults to namespace 0 because that's how Special:Newpages defaults
    if site is None:
        site = pywikibot.Site()
    for item in site.recentchanges(showRedirects=get_redirect,
                                   changetype="new", namespaces=namespaces,
                                   step=step, total=total):
        yield pywikibot.Page(pywikibot.Link(item["title"], site))


def RecentChangesPageGenerator(start=None, end=None, reverse=False,
                               namespaces=None, pagelist=None,
                               changetype=None, showMinor=None,
                               showBot=None, showAnon=None,
                               showRedirects=None, showPatrolled=None,
                               topOnly=False, step=None, total=None,
                               user=None, excludeuser=None, site=None):
    """
    Generate pages that are in the recent changes list.

    @param start: Timestamp to start listing from
    @type start: pywikibot.Timestamp
    @param end: Timestamp to end listing at
    @type end: pywikibot.Timestamp
    @param reverse: if True, start with oldest changes (default: newest)
    @type reverse: bool
    @param pagelist: iterate changes to pages in this list only
    @param pagelist: list of Pages
    @param changetype: only iterate changes of this type ("edit" for
        edits to existing pages, "new" for new pages, "log" for log
        entries)
    @type changetype: basestring
    @param showMinor: if True, only list minor edits; if False, only list
        non-minor edits; if None, list all
    @type showMinor: bool or None
    @param showBot: if True, only list bot edits; if False, only list
        non-bot edits; if None, list all
    @type showBot: bool or None
    @param showAnon: if True, only list anon edits; if False, only list
        non-anon edits; if None, list all
    @type showAnon: bool or None
    @param showRedirects: if True, only list edits to redirect pages; if
        False, only list edits to non-redirect pages; if None, list all
    @type showRedirects: bool or None
    @param showPatrolled: if True, only list patrolled edits; if False,
        only list non-patrolled edits; if None, list all
    @type showPatrolled: bool or None
    @param topOnly: if True, only list changes that are the latest revision
        (default False)
    @type topOnly: bool
    @param user: if not None, only list edits by this user or users
    @type user: basestring|list
    @param excludeuser: if not None, exclude edits by this user or users
    @type excludeuser: basestring|list
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}

    """
    if site is None:
        site = pywikibot.Site()
    for item in site.recentchanges(start=start, end=end, reverse=reverse,
                                   namespaces=namespaces, pagelist=pagelist,
                                   changetype=changetype, showMinor=showMinor,
                                   showBot=showBot, showAnon=showAnon,
                                   showRedirects=showRedirects,
                                   showPatrolled=showPatrolled,
                                   topOnly=topOnly, step=step, total=total,
                                   user=user, excludeuser=excludeuser):
        yield pywikibot.Page(pywikibot.Link(item["title"], site))


def FileLinksGenerator(referredFilePage, step=None, total=None, content=False):
    """Yield Pages on which the file referredFilePage is displayed."""
    return referredFilePage.usingPages(step=step, total=total, content=content)


def ImagesPageGenerator(pageWithImages, step=None, total=None, content=False):
    """Yield FilePages displayed on pageWithImages."""
    return pageWithImages.imagelinks(step=step, total=total, content=content)


def InterwikiPageGenerator(page):
    """Iterate over all interwiki (non-language) links on a page."""
    for link in page.interwiki():
        yield pywikibot.Page(link)


def LanguageLinksPageGenerator(page, step=None, total=None):
    """Iterate over all interwiki language links on a page."""
    for link in page.iterlanglinks(step=step, total=total):
        yield pywikibot.Page(link)


def ReferringPageGenerator(referredPage, followRedirects=False,
                           withTemplateInclusion=True,
                           onlyTemplateInclusion=False,
                           step=None, total=None, content=False):
    """Yield all pages referring to a specific page."""
    return referredPage.getReferences(
        follow_redirects=followRedirects,
        withTemplateInclusion=withTemplateInclusion,
        onlyTemplateInclusion=onlyTemplateInclusion,
        step=step, total=total, content=content)


def CategorizedPageGenerator(category, recurse=False, start=None,
                             step=None, total=None, content=False):
    """Yield all pages in a specific category.

    If recurse is True, pages in subcategories are included as well; if
    recurse is an int, only subcategories to that depth will be included
    (e.g., recurse=2 will get pages in subcats and sub-subcats, but will
    not go any further).

    If start is a string value, only pages whose sortkey comes after start
    alphabetically are included.

    If content is True (default is False), the current page text of each
    retrieved page will be downloaded.

    """
    kwargs = dict(recurse=recurse, step=step, total=total,
                  content=content)
    if start:
        kwargs['sortby'] = 'sortkey'
        kwargs['startsort'] = start
    for a in category.articles(**kwargs):
        yield a


def SubCategoriesPageGenerator(category, recurse=False, start=None,
                               step=None, total=None, content=False):
    """Yield all subcategories in a specific category.

    If recurse is True, pages in subcategories are included as well; if
    recurse is an int, only subcategories to that depth will be included
    (e.g., recurse=2 will get pages in subcats and sub-subcats, but will
    not go any further).

    If start is a string value, only categories whose sortkey comes after
    start alphabetically are included.

    If content is True (default is False), the current page text of each
    category description page will be downloaded.

    """
    # TODO: page generator could be modified to use cmstartsortkey ...
    for s in category.subcategories(recurse=recurse, step=step,
                                    total=total, content=content):
        if start is None or s.title(withNamespace=False) >= start:
            yield s


def LinkedPageGenerator(linkingPage, step=None, total=None, content=False):
    """Yield all pages linked from a specific page."""
    return linkingPage.linkedPages(step=step, total=total, content=content)


def TextfilePageGenerator(filename=None, site=None):
    """Iterate pages from a list in a text file.

    The file must contain page links between double-square-brackets or, in
    alternative, separated by newlines. The generator will yield each
    corresponding Page object.

    @param filename: the name of the file that should be read. If no name is
                     given, the generator prompts the user.
    @type filename: unicode
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}

    """
    if filename is None:
        filename = pywikibot.input(u'Please enter the filename:')
    if site is None:
        site = pywikibot.Site()
    f = codecs.open(filename, 'r', config.textfile_encoding)
    linkmatch = None
    for linkmatch in pywikibot.link_regex.finditer(f.read()):
        # If the link is in interwiki format, the Page object may reside
        # on a different Site than the default.
        # This makes it possible to work on different wikis using a single
        # text file, but also could be dangerous because you might
        # inadvertently change pages on another wiki!
        yield pywikibot.Page(pywikibot.Link(linkmatch.group("title"), site))
    if linkmatch is None:
        f.seek(0)
        for title in f:
            title = title.strip()
            if '|' in title:
                title = title[:title.index('|')]
            if title:
                yield pywikibot.Page(site, title)
    f.close()


def PagesFromTitlesGenerator(iterable, site=None):
    """
    Generate pages from the titles (unicode strings) yielded by iterable.

    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for title in iterable:
        if not isinstance(title, basestring):
            break
        yield pywikibot.Page(pywikibot.Link(title, site))


@deprecated_args(number="total")
def UserContributionsGenerator(username, namespaces=None, site=None,
                               step=None, total=None):
    """Yield unique pages edited by user:username.

    @param step: Maximum number of pages to retrieve per API query
    @type step: int
    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param namespaces: list of namespace numbers to fetch contribs from
    @type namespaces: list of int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}

    """
    if site is None:
        site = pywikibot.Site()
    return DuplicateFilterPageGenerator(
        pywikibot.Page(pywikibot.Link(contrib["title"], source=site))
        for contrib in site.usercontribs(user=username, namespaces=namespaces,
                                         step=step, total=total)
    )


def NamespaceFilterPageGenerator(generator, namespaces, site=None):
    """
    A generator yielding pages from another generator in given namespaces.

    The namespace list can contain both integers (namespace numbers) and
    strings/unicode strings (namespace names).

    NOTE: API-based generators that have a "namespaces" parameter perform
    namespace filtering more efficiently than this generator.

    @param namespaces: list of namespace numbers to limit results
    @type namespaces: list of int
    @param site: Site for generator results, only needed if
        namespaces contains namespace names.
    @type site: L{pywikibot.site.BaseSite}
    """
    if isinstance(namespaces, (int, basestring)):
        namespaces = [namespaces]
    # convert namespace names to namespace numbers
    for i in range(len(namespaces)):
        ns = namespaces[i]
        if isinstance(ns, basestring):
            try:
                # namespace might be given as str representation of int
                index = int(ns)
            except ValueError:
                # FIXME: deprecate providing strings as namespaces
                if site is None:
                    site = pywikibot.Site()
                index = site.getNamespaceIndex(ns)
                if index is None:
                    raise ValueError(u'Unknown namespace: %s' % ns)
            namespaces[i] = index
    for page in generator:
        if page.namespace() in namespaces:
            yield page


@deprecated_args(ignoreList='ignore_list')
def PageTitleFilterPageGenerator(generator, ignore_list):
    """
    Yield only those pages are not listed in the ignore list.

    @param ignore_list: family names are mapped to dictionaries in which
        language codes are mapped to lists of page titles. Each title must
        be a valid regex as they are compared using L{re.search}.
    @type ignore_list: dict

    """
    def is_ignored(page):
        if page.site.code in ignore_list.get(page.site.family.name, {}):
            for ig in ignore_list[page.site.family.name][page.site.code]:
                if re.search(ig, page.title()):
                    return True
        return False

    for page in generator:
        if is_ignored(page):
            if config.verbose_output:
                pywikibot.output('Ignoring page %s' % page.title())
        else:
            yield page


def RedirectFilterPageGenerator(generator, no_redirects=True,
                                show_filtered=False):
    """
    Yield pages from another generator that are redirects or not.

    @param no_redirects: Exclude redirects if True, else only include
        redirects.
    @param no_redirects: bool
    @param show_filtered: Output a message for each page not yielded
    @type show_filtered: bool
    """
    for page in generator or []:
        if no_redirects:
            if not page.isRedirectPage():
                yield page
            elif show_filtered:
                pywikibot.output(u'%s is a redirect page. Skipping.' % page)

        else:
            if page.isRedirectPage():
                yield page
            elif show_filtered:
                pywikibot.output(u'%s is not a redirect page. Skipping.'
                                 % page)


def DuplicateFilterPageGenerator(generator):
    """Yield all unique pages from another generator, omitting duplicates."""
    seenPages = {}
    for page in generator:
        if page not in seenPages:
            seenPages[page] = True
            yield page


class RegexFilter(object):

    """Regex filter."""

    @classmethod
    def __filter_match(cls, regex, string, quantifier):
        """Return True if string matches precompiled regex list.

        @param quantifier: a qualifer
        @type quantifier: str of 'all', 'any' or 'none'
        @rtype: bool
        """
        if quantifier == 'all':
            match = all(r.search(string) for r in regex)
        else:
            match = any(r.search(string) for r in regex)
        return (quantifier == 'none') ^ match

    @classmethod
    def __precompile(cls, regex, flag):
        """Precompile the regex list if needed."""
        # Enable multiple regexes
        if not isinstance(regex, list):
            regex = [regex]
        # Test if regex is already compiled.
        # We assume that all list componets have the same type
        if isinstance(regex[0], basestring):
            regex = [re.compile(r, flag) for r in regex]
        return regex

    @classmethod
    @deprecated_args(inverse="quantifier")
    def titlefilter(cls, generator, regex, quantifier='any',
                    ignore_namespace=True):
        """ Yield pages from another generator whose title matches regex.

        Uses regex option re.IGNORECASE depending on the quantifier parameter.

        If ignore_namespace is False, the whole page title is compared.
        NOTE: if you want to check for a match at the beginning of the title,
        you have to start the regex with "^"

        @param generator: another generator
        @type generator: any generator or iterator
        @param regex: a regex which should match the page title
        @type regex: a single regex string or a list of regex strings or a
            compiled regex or a list of compiled regexes
        @param quantifier: must be one of the following values:
            'all' - yields page if title is matched by all regexes
            'any' - yields page if title is matched by any regexes
            'none' - yields page if title is NOT matched by any regexes
        @type quantifier: string of ('all', 'any', 'none')
        @param ignore_namespace: ignore the namespace when matching the title
        @type ignore_namespace: bool
        @return: return a page depending on the matching parameters

        """
        # for backwards compatibility with compat for inverse parameter
        if quantifier is False:
            quantifier = 'any'
        elif quantifier is True:
            quantifier = 'none'
        reg = cls.__precompile(regex, re.I)
        for page in generator:
            title = page.title(withNamespace=not ignore_namespace)
            if cls.__filter_match(reg, title, quantifier):
                yield page

    @classmethod
    def contentfilter(cls, generator, regex, quantifier='any'):
        """Yield pages from another generator whose body matches regex.

        Uses regex option re.IGNORECASE depending on the quantifier parameter.

        For parameters see titlefilter above.

        """
        reg = cls.__precompile(regex, re.IGNORECASE | re.DOTALL)
        return (page for page in generator
                if cls.__filter_match(reg, page.text, quantifier))

# name the generator methods
RegexFilterPageGenerator = RegexFilter.titlefilter
RegexBodyFilterPageGenerator = RegexFilter.contentfilter


@deprecated_args(begintime='last_edit_start', endtime='last_edit_end')
def EdittimeFilterPageGenerator(generator,
                                last_edit_start=None,
                                last_edit_end=None,
                                first_edit_start=None,
                                first_edit_end=None,
                                show_filtered=False):
    """
    Wrap a generator to filter pages outside last or first edit range.

    @param generator: A generator object
    @param last_edit_start: Only yield pages last edited after this time
    @type last_edit_start: datetime
    @param last_edit_end: Only yield pages last edited before this time
    @type last_edit_end: datetime
    @param first_edit_start: Only yield pages first edited after this time
    @type first_edit_start: datetime
    @param first_edit_end: Only yield pages first edited before this time
    @type first_edit_end: datetime
    @param show_filtered: Output a message for each page not yielded
    @type show_filtered: bool

    """
    do_last_edit = last_edit_start or last_edit_end
    do_first_edit = first_edit_start or first_edit_end

    last_edit_start = last_edit_start or datetime.datetime.min
    last_edit_end = last_edit_end or datetime.datetime.max
    first_edit_start = first_edit_start or datetime.datetime.min
    first_edit_end = first_edit_end or datetime.datetime.max

    for page in generator or []:
        if do_last_edit:
            last_edit = page.editTime()

            if last_edit < last_edit_start:
                if show_filtered:
                    pywikibot.output(
                        u'Last edit on %s was on %s.\nToo old. Skipping.'
                        % (page, last_edit.isoformat()))
                continue

            if last_edit > last_edit_end:
                if show_filtered:
                    pywikibot.output(
                        u'Last edit on %s was on %s.\nToo recent. Skipping.'
                        % (page, last_edit.isoformat()))
                continue

        if do_first_edit:
            first_edit = page.oldest_revision.timestamp

            if first_edit < first_edit_start:
                if show_filtered:
                    pywikibot.output(
                        u'First edit on %s was on %s.\nToo old. Skipping.'
                        % (page, first_edit.isoformat()))

            if first_edit > first_edit_end:
                if show_filtered:
                    pywikibot.output(
                        u'First edit on %s was on %s.\nToo recent. Skipping.'
                        % (page, first_edit.isoformat()))
                continue

        yield page


def CombinedPageGenerator(generators):
    """Yield from each iterable until exhausted, then proceed with the next."""
    return itertools.chain(*generators)


def CategoryGenerator(generator):
    """Yield pages from another generator as Category objects.

    Makes sense only if it is ascertained that only categories are being
    retrieved.

    """
    for page in generator:
        yield pywikibot.Category(page)


def FileGenerator(generator):
    """
    Yield pages from another generator as FilePage objects.

    Makes sense only if it is ascertained
    that only images are being retrieved.
    """
    for page in generator:
        yield pywikibot.FilePage(page)


ImageGenerator = FileGenerator


def PageWithTalkPageGenerator(generator):
    """Yield pages and associated talk pages from another generator.

    Only yields talk pages if the original generator yields a non-talk page,
    and does not check if the talk page in fact exists.

    """
    for page in generator:
        yield page
        if not page.isTalkPage():
            yield page.toggleTalkPage()


def RepeatingGenerator(generator, key_func=lambda x: x, sleep_duration=60,
                       total=None, **kwargs):
    """Yield items in live time.

    The provided generator must support parameter 'start', 'end',
    'reverse', and 'total' such as site.recentchanges(), site.logevents().

    To fetch revisions in recentchanges in live time::

        gen = RepeatingGenerator(site.recentchanges, lambda x: x['revid'])

    To fetch new pages in live time::

        gen = RepeatingGenerator(site.newpages, lambda x: x[0])

    Note that other parameters not listed below will be passed
    to the generator function. Parameter 'reverse', 'start', 'end'
    will always be discarded to prevent the generator yielding items
    in wrong order.

    @param generator: a function returning a generator that will be queried
    @param key_func: a function returning key that will be used to detect
        duplicate entry
    @param sleep_duration: duration between each query
    @param total: if it is a positive number, iterate no more than this
        number of items in total. Otherwise, iterate forever
    @type total: int or None
    @return: a generator yielding items in ascending order by time
    """
    kwargs.pop('reverse', None)  # always get newest item first
    kwargs.pop('start', None)  # don't set start time
    kwargs.pop('end', None)  # don't set stop time

    seen = set()
    while total is None or len(seen) < total:
        def filtered_generator():
            for item in generator(total=None if seen else 1, **kwargs):
                key = key_func(item)
                if key not in seen:
                    seen.add(key)
                    yield item
                    if len(seen) == total:
                        return
                else:
                    break
            time.sleep(sleep_duration)
        for item in list(filtered_generator())[::-1]:
            yield item


@deprecated_args(pageNumber="step", lookahead=None)
def PreloadingGenerator(generator, step=50):
    """
    Yield preloaded pages taken from another generator.

    @param generator: pages to iterate over
    @param step: how many pages to preload at once
    @type step: int
    """
    # pages may be on more than one site, for example if an interwiki
    # generator is used, so use a separate preloader for each site
    sites = {}
    # build a list of pages for each site found in the iterator
    for page in generator:
        site = page.site
        sites.setdefault(site, []).append(page)
        if len(sites[site]) >= step:
            # if this site is at the step, process it
            group = sites[site]
            sites[site] = []
            for i in site.preloadpages(group, step):
                yield i
    for site in sites:
        if sites[site]:
            # process any leftover sites that never reached the step
            for i in site.preloadpages(sites[site], step):
                yield i


def DequePreloadingGenerator(generator, step=50):
    """Preload generator of type DequeGenerator."""
    assert(isinstance(generator, DequeGenerator))

    while True:
        page_count = min(len(generator), step)
        if not page_count:
            raise StopIteration

        for page in PreloadingGenerator(generator, page_count):
            yield page


def PreloadingItemGenerator(generator, step=50):
    """
    Yield preloaded pages taken from another generator.

    Function basically is copied from above, but for ItemPage's

    @param generator: pages to iterate over
    @param step: how many pages to preload at once
    @type step: int
    """
    sites = {}
    for page in generator:
        if not isinstance(page, pywikibot.page.WikibasePage):
            datasite = page.site.data_repository()
            if page.namespace() != datasite.item_namespace:
                pywikibot.output(
                    u'PreloadingItemGenerator skipping %s as it is not in %s'
                    % (page, datasite.item_namespace))
                continue

            page = pywikibot.ItemPage(datasite, page.title())

        site = page.site
        sites.setdefault(site, []).append(page)
        if len(sites[site]) >= step:
            # if this site is at the step, process it
            group = sites[site]
            sites[site] = []
            for i in site.preloaditempages(group, step):
                yield i
    for site in sites:
        if sites[site]:
            # process any leftover sites that never reached the step
            for i in site.preloaditempages(sites[site], step):
                yield i


@deprecated_args(number="total")
def NewimagesPageGenerator(step=None, total=None, site=None):
    """
    New file generator.

    @param step: Maximum number of pages to retrieve per API query
    @type step: int
    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for entry in site.logevents(logtype="upload", step=step, total=total):
        # entry is an UploadEntry object
        # entry.title() returns a Page object
        yield entry.title()


def WikibaseItemGenerator(gen):
    """
    A wrapper generator used to yield Wikibase items of another generator.

    @param gen: Generator to wrap.
    @type gen: generator
    @return: Wrapped generator
    @rtype: generator
    """
    for page in gen:
        if isinstance(page, pywikibot.ItemPage):
            yield page
        elif page.site.data_repository() == page.site:
            # These are already items, as they have a DataSite in page.site.
            # However generator is yielding Page, so convert to ItemPage.
            # FIXME: If we've already fetched content, we should retain it
            yield pywikibot.ItemPage(page.site, page.title())
        else:
            yield pywikibot.ItemPage.fromPage(page)


WikidataItemGenerator = WikibaseItemGenerator


def WikibaseItemFilterPageGenerator(generator, has_item=True,
                                    show_filtered=False):
    """
    A wrapper generator used to exclude if page has a wikibase item or not.

    @param gen: Generator to wrap.
    @type gen: generator
    @param has_item: Exclude pages without an item if True, or only
        include pages without an item if False
    @type has_item: bool
    @param show_filtered: Output a message for each page not yielded
    @type show_filtered: bool
    @return: Wrapped generator
    @rtype: generator
    """
    for page in generator or []:
        try:
            page_item = pywikibot.ItemPage.fromPage(page, lazy_load=False)
        except pywikibot.NoPage:
            page_item = None

        if page_item:
            if not has_item:
                if show_filtered:
                    pywikibot.output(
                        '%s has a wikidata item.  Skipping.' % page)
                continue
        else:
            if has_item:
                if show_filtered:
                    pywikibot.output(
                        '%s doesn\'t have a wikidata item.  Skipping.' % page)
                continue

        yield page


# TODO below
@deprecated_args(extension=None, number="total", repeat=None)
def UnusedFilesGenerator(total=100, site=None, extension=None):
    """
    Unused files generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.unusedfiles(total=total):
        yield pywikibot.FilePage(page.site, page.title())


@deprecated_args(number="total", repeat=None)
def WithoutInterwikiPageGenerator(total=100, site=None):
    """
    Page lacking interwikis generator.

    @param total: Maxmum number of pages to retrieve in total
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.withoutinterwiki(total=total):
        yield page


@deprecated_args(number="total", repeat=None)
def UnCategorizedCategoryGenerator(total=100, site=None):
    """
    Uncategorized category generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedcategories(total=total):
        yield page


@deprecated_args(number="total", repeat=None)
def UnCategorizedImageGenerator(total=100, site=None):
    """
    Uncategorized file generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedimages(total=total):
        yield page


@deprecated_args(number="total", repeat=None)
def UnCategorizedPageGenerator(total=100, site=None):
    """
    Uncategorized page generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedpages(total=total):
        yield page


def UnCategorizedTemplateGenerator(total=100, site=None):
    """
    Uncategorized template generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedtemplates(total=total):
        yield page


@deprecated_args(number="total", repeat=None)
def LonelyPagesPageGenerator(total=100, site=None):
    """
    Lonely page generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.lonelypages(total=total):
        yield page


@deprecated_args(number="total", repeat=None)
def UnwatchedPagesPageGenerator(total=100, site=None):
    """
    Unwatched page generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.unwatchedpages(total=total):
        yield page


def WantedPagesPageGenerator(total=100, site=None):
    """
    Wanted page generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.wantedpages(total=total):
        yield page


@deprecated_args(number="total", repeat=None)
def AncientPagesPageGenerator(total=100, site=None):
    """
    Ancient page generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page, timestamp in site.ancientpages(total=total):
        yield page


@deprecated_args(number="total", repeat=None)
def DeadendPagesPageGenerator(total=100, site=None):
    """
    Dead-end page generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.deadendpages(total=total):
        yield page


@deprecated_args(number="total", repeat=None)
def LongPagesPageGenerator(total=100, site=None):
    """
    Long page generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page, length in site.longpages(total=total):
        yield page


@deprecated_args(number="total", repeat=None)
def ShortPagesPageGenerator(total=100, site=None):
    """
    Short page generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page, length in site.shortpages(total=total):
        yield page


@deprecated_args(number="total")
def RandomPageGenerator(total=10, site=None):
    """
    Random page generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.randompages(total=total):
        yield page


@deprecated_args(number="total")
def RandomRedirectPageGenerator(total=10, site=None):
    """
    Random redirect generator.

    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.randompages(total=total, redirects=True):
        yield page


def LinksearchPageGenerator(link, namespaces=None, step=None, total=None,
                            site=None):
    """Yield all pages that include a specified link.

    Obtains data from [[Special:Linksearch]].

    @param step: Maximum number of pages to retrieve per API query
    @type step: int
    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.exturlusage(link, namespaces=namespaces, step=step,
                                 total=total, content=False)


def SearchPageGenerator(query, step=None, total=None, namespaces=None,
                        site=None):
    """
    Yield pages from the MediaWiki internal search engine.

    @param step: Maximum number of pages to retrieve per API query
    @type step: int
    @param total: Maxmum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.search(query, step=step, total=total,
                            namespaces=namespaces):
        yield page


def UntaggedPageGenerator(untaggedProject, limit=500, site=None):
    """
    Yield pages from defunct toolserver UntaggedImages.php.

    It was using this tool:
    https://toolserver.org/~daniel/WikiSense/UntaggedImages.php

    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    URL = "https://toolserver.org/~daniel/WikiSense/UntaggedImages.php?"
    REGEXP = r"<td valign='top' title='Name'><a href='http[s]?://.*?" \
             "\.org/w/index\.php\?title=(.*?)'>.*?</a></td>"
    lang, project = untaggedProject.split('.', 1)
    if lang == 'commons':
        wiki = 'wikifam=commons.wikimedia.org'
    else:
        wiki = 'wikilang=%s&wikifam=.%s' % (lang, project)
    link = '%s&%s&max=%d&order=img_timestamp' % (URL, wiki, limit)
    results = re.findall(REGEXP, http.request(site=None, uri=link))
    if not results:
        raise pywikibot.Error(
            u'Nothing found at %s! Try to use the tool by yourself to be sure '
            u'that it works!' % link)
    if not site:
        site = pywikibot.Site()
    else:
        for result in results:
            yield pywikibot.Page(site, result)


# following classes just ported from version 1 without revision; not tested


class YahooSearchPageGenerator:

    """
    Page generator using Yahoo! search results.

    To use this generator, you need to install the package 'pYsearch'.
    https://pypi.python.org/pypi/pYsearch

    To use this generator, install pYsearch
    """

    # values larger than 100 fail
    def __init__(self, query=None, count=100, site=None):
        """
        Constructor.

        @param site: Site for generator results.
        @type site: L{pywikibot.site.BaseSite}
        """
        self.query = query or pywikibot.input(u'Please enter the search query:')
        self.count = count
        if site is None:
            site = pywikibot.Site()
        self.site = site

    def queryYahoo(self, query):
        """ Perform a query using python package 'pYsearch'. """
        try:
            from yahoo.search.web import WebSearch
        except ImportError:
            pywikibot.error("ERROR: generator YahooSearchPageGenerator "
                            "depends on package 'pYsearch'.\n"
                            "To install, please run: pip install pYsearch")
            exit(1)

        srch = WebSearch(config.yahoo_appid, query=query, results=self.count)
        dom = srch.get_results()
        results = srch.parse_results(dom)
        for res in results:
            url = res.Url
            yield url

    def __iter__(self):
        """Iterate results."""
        # restrict query to local site
        localQuery = '%s site:%s' % (self.query, self.site.hostname())
        base = 'http://%s%s' % (self.site.hostname(),
                                self.site.nice_get_address(''))
        for url in self.queryYahoo(localQuery):
            if url[:len(base)] == base:
                title = url[len(base):]
                page = pywikibot.Page(pywikibot.Link(title, pywikibot.Site()))
                yield page


class GoogleSearchPageGenerator:

    """
    Page generator using Google search results.

    To use this generator, you need to install the package 'google'.
    https://pypi.python.org/pypi/google

    This package has been available since 2010, hosted on github
    since 2012, and provided by pypi since 2013.

    As there are concerns about Google's Terms of Service, this
    generator prints a warning for each query.
    """

    def __init__(self, query=None, site=None):
        """
        Constructor.

        @param site: Site for generator results.
        @type site: L{pywikibot.site.BaseSite}
        """
        self.query = query or pywikibot.input(u'Please enter the search query:')
        if site is None:
            site = pywikibot.Site()
        self.site = site

    def queryGoogle(self, query):
        """
        Perform a query using python package 'google'.

        The terms of service as at June 2014 give two conditions that
        may apply to use of search:
            1. Dont access [Google Services] using a method other than
               the interface and the instructions that [they] provide.
            2. Don't remove, obscure, or alter any legal notices
               displayed in or along with [Google] Services.

        Both of those issues should be managed by the package 'google',
        however Pywikibot will at least ensure the user sees the TOS
        in order to comply with the second condition.
        """
        try:
            import google
        except ImportError:
            pywikibot.error("ERROR: generator GoogleSearchPageGenerator "
                            "depends on package 'google'.\n"
                            "To install, please run: pip install google.")
            exit(1)
        pywikibot.warning('Please read http://www.google.com/accounts/TOS')
        for url in google.search(query):
            yield url

    def __iter__(self):
        """Iterate results."""
        # restrict query to local site
        localQuery = '%s site:%s' % (self.query, self.site.hostname())
        base = 'http://%s%s' % (self.site.hostname(),
                                self.site.nice_get_address(''))
        for url in self.queryGoogle(localQuery):
            if url[:len(base)] == base:
                title = url[len(base):]
                page = pywikibot.Page(pywikibot.Link(title, self.site))
                # Google contains links in the format
                # https://de.wikipedia.org/wiki/en:Foobar
                if page.site == self.site:
                    yield page


def MySQLPageGenerator(query, site=None):
    """
    Yield a list of pages based on a MySQL query.

    Each query should provide the page namespace and page title. An example
    query that yields all ns0 pages might look like::

        SELECT
         page_namespace,
         page_title,
        FROM page
        WHERE page_namespace = 0;

    Requires oursql <https://pythonhosted.org/oursql/> or
    MySQLdb <https://sourceforge.net/projects/mysql-python/>

    @param query: MySQL query to execute
    @param site: Site object
    @type site: L{pywikibot.site.BaseSite}
    @return: iterator of pywikibot.Page
    """
    try:
        import oursql as mysqldb
    except ImportError:
        import MySQLdb as mysqldb
    if site is None:
        site = pywikibot.Site()
    if config.db_connect_file is None:
        conn = mysqldb.connect(config.db_hostname, db=config.db_name_format.format(site.dbName()),
                               user=config.db_username, passwd=config.db_password)
    else:
        conn = mysqldb.connect(config.db_hostname, db=config.db_name_format.format(site.dbName()),
                               read_default_file=config.db_connect_file)

    cursor = conn.cursor()
    pywikibot.output(u'Executing query:\n%s' % query)
    query = query.encode(site.encoding())
    cursor.execute(query)
    while True:
        try:
            namespaceNumber, pageName = cursor.fetchone()
        except TypeError:
            # Limit reached or no more results
            break
        if pageName:
            namespace = site.namespace(namespaceNumber)
            pageName = pageName.decode(site.encoding())
            if namespace:
                pageTitle = '%s:%s' % (namespace, pageName)
            else:
                pageTitle = pageName
            page = pywikibot.Page(site, pageTitle)
            yield page


def YearPageGenerator(start=1, end=2050, site=None):
    """
    Year page generator.

    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    pywikibot.output(u"Starting with year %i" % start)
    for i in range(start, end + 1):
        if i % 100 == 0:
            pywikibot.output(u'Preparing %i...' % i)
        # There is no year 0
        if i != 0:
            current_year = date.formatYear(site.lang, i)
            yield pywikibot.Page(pywikibot.Link(current_year, site))


def DayPageGenerator(startMonth=1, endMonth=12, site=None):
    """
    Day page generator.

    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    fd = date.FormatDate(site)
    firstPage = pywikibot.Page(site, fd(startMonth, 1))
    pywikibot.output(u"Starting with %s" % firstPage.title(asLink=True))
    for month in range(startMonth, endMonth + 1):
        for day in range(1, date.getNumberOfDaysInMonth(month) + 1):
            yield pywikibot.Page(pywikibot.Link(fd(month, day), site))


def WikidataQueryPageGenerator(query, site=None):
    """Generate pages that result from the given WikidataQuery.

    @param query: the WikidataQuery query string.
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}

    """
    if site is None:
        site = pywikibot.Site()
    repo = site.data_repository()

    wd_queryset = wdquery.QuerySet(query)

    wd_query = wdquery.WikidataQuery(cacheMaxAge=0)
    data = wd_query.query(wd_queryset)

    pywikibot.output(u'retrieved %d items' % data[u'status'][u'items'])
    for item in data[u'items']:
        page = pywikibot.ItemPage(repo, u'Q{0}'.format(item))
        try:
            link = page.getSitelink(site)
        except pywikibot.NoPage:
            continue
        yield pywikibot.Page(pywikibot.Link(link, site))


if __name__ == "__main__":
    pywikibot.output(u'Pagegenerators cannot be run as script - are you '
                     u'looking for listpages.py?')
