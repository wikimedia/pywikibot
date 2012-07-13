# -*- coding: utf-8  -*-
"""This module offers a wide variety of page generators. A page generator is an
object that is iterable (see http://www.python.org/dev/peps/pep-0255/ ) and
that yields page objects on which other scripts can then work.

In general, there is no need to run this script directly. It can, however,
be run for testing purposes. It will then print the page titles to standard
output.

These parameters are supported to specify which pages titles to print:

&params;
"""
#
# (C) Pywikipedia bot team, 2008-2010
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import pywikibot
from pywikibot import config
from pywikibot import deprecate_arg

import itertools
import Queue
import re
import sys
import codecs


# ported from version 1 for backwards-compatibility
# most of these functions just wrap a Site or Page method that returns
# a generator

parameterHelp = u"""\
-cat              Work on all pages which are in a specific category.
                  Argument can also be given as "-cat:categoryname" or
                  as "-cat:categoryname|fromtitle".

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
                  Page titles in the file must be enclosed with [[brackets]].
                  Argument can also be given as "-file:filename".

-filelinks        Work on all pages that use a certain image/media file.
                  Argument can also be given as "-filelinks:filename".

-search           Work on all pages that are found in a MediaWiki search
                  across all namespaces.

-namespace        Filter the page generator to only yield pages in the
-ns               specified namespaces.  Separate multiple namespace
                  numbers with commas. Example "-ns:0,2,4"

-interwiki        Work on the given page and all equivalent pages in other
                  languages. This can, for example, be used to fight
                  multi-site spamming.
                  Attention: this will cause the bot to modify
                  pages on several wiki sites, this is not well tested,
                  so check your edits!

-limit:n          When used with any other argument that specifies a set
                  of pages, work on no more than n pages in total

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
                  server

-titleregex       Work on titles that match the given regular expression.

-transcludes      Work on all pages that use a certain template.
                  Argument can also be given as "-transcludes:Title".

-unusedfiles      Work on all description pages of images/media files that are
                  not used anywhere.
                  Argument can be given as "-unusedfiles:n" where
                  n is the maximum number of articles to work on.

-unwatched        Work on all articles that are not watched by anyone.
                  Argument can be given as "-unwatched:n" where
                  n is the maximum number of articles to work on.

-usercontribs     Work on all articles that were edited by a certain user :
                  Example : -usercontribs:DumZiBoT

-weblink          Work on all articles that contain an external link to
                  a given URL; may be given as "-weblink:url"

-withoutinterwiki Work on all pages that don't have interlanguage links.
                  Argument can be given as "-withoutinterwiki:n" where
                  n is some number (??).

-google           Work on all pages that are found in a Google search.
                  You need a Google Web API license key. Note that Google
                  doesn't give out license keys anymore. See google_key in
                  config.py for instructions.
                  Argument can also be given as "-google:searchstring".

-yahoo            Work on all pages that are found in a Yahoo search.
                  Depends on python module pYsearch.  See yahoo_appid in
                  config.py for instructions.

-page             Work on a single page. Argument can also be given as
                  "-page:pagetitle".
"""

docuReplacements = {'&params;': parameterHelp}

# if a bot uses GeneratorFactory, the module should include the line
#   docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}
# and include the marker &params; in the module's docstring


class GeneratorFactory(object):
    """Process command line arguments and return appropriate page generator.
    This factory is responsible for processing command line arguments
    that are used by many scripts and that determine which pages to work on.
    """
    def __init__(self):
        self.gens = []
        self.namespaces = []
        self.step = None
        self.limit = None


    def getCombinedGenerator(self):
        """Return the combination of all accumulated generators.

        Only call this after all arguments have been parsed.
        """
        namespaces = [int(n) for n in self.namespaces]
        for i in xrange(len(self.gens)):
            if isinstance(self.gens[i], pywikibot.data.api.QueryGenerator):
                if self.namespaces:
                    self.gens[i].set_namespace(namespaces)
                if self.step:
                    self.gens[i].set_query_increment(self.step)
                if self.limit:
                    self.gens[i].set_maximum_items(self.limit)
            else:
                if self.namespaces:
                    self.gens[i] = NamespaceFilterPageGenerator(
                                       self.gens[i], namespaces)
                if self.limit:
                    self.gens[i] = itertools.islice(self.gens[i], self.limit)
        if len(self.gens) == 0:
            return None
        elif len(self.gens) == 1:
            gensList = self.gens[0]
        else:
            gensList = CombinedPageGenerator(self.gens)
        return DuplicateFilterPageGenerator(gensList)

    def getCategoryGen(self, arg, length, recurse=False, content=False):
        if len(arg) == length:
            categoryname = pywikibot.input(u'Please enter the category name:')
        else:
            categoryname = arg[length + 1:]

        ind = categoryname.find('|')
        startfrom = None
        if ind > 0:
            startfrom = categoryname[ind + 1:]
            categoryname = categoryname[:ind]

        cat = pywikibot.Category(pywikibot.Link(categoryname,
                                                defaultNamespace=14))
        # Link constructor automatically prepends localized namespace
        # if not included in user's input
        return CategorizedPageGenerator(cat,
               start=startfrom, recurse=recurse, content=content)

    def setSubCategoriesGen(self, arg, length, recurse=False, content=False):
        if len(arg) == length:
            categoryname = pywikibot.input(u'Please enter the category name:')
        else:
            categoryname = arg[length + 1:]

        ind = categoryname.find('|')
        if ind > 0:
            startfrom = categoryname[ind + 1:]
            categoryname = categoryname[:ind]
        else:
            startfrom = None

        cat = pywikibot.Category(pywikibot.Link(categoryname,
                                                defaultNamespace=14))
        return SubCategoriesPageGenerator(cat,
               start=startfrom, recurse=recurse, content=content)

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
                fileLinksPageTitle = pywikibot.input(
                    u'Links to which image page should be processed?')
            if fileLinksPageTitle.startswith(pywikibot.Site().namespace(6)
                                             + ":"):
                fileLinksPage = pywikibot.ImagePage(pywikibot.Site(),
                                                    fileLinksPageTitle)
            else:
                fileLinksPage = pywikibot.ImagePage(pywikibot.Site(),
                                                    'Image:' +
                                                    fileLinksPageTitle)
            gen = FileLinksGenerator(fileLinksPage)
        elif arg.startswith('-unusedfiles'):
            if len(arg) == 12:
                gen = UnusedFilesGenerator()
            else:
                gen = UnusedFilesGenerator(number = int(arg[13:]))
        elif arg.startswith('-unwatched'):
            if len(arg) == 10:
                gen = UnwatchedPagesPageGenerator()
            else:
                gen = UnwatchedPagesPageGenerator(number = int(arg[11:]))
        elif arg.startswith('-usercontribs'):
            gen = UserContributionsGenerator(arg[14:])
        elif arg.startswith('-withoutinterwiki'):
            if len(arg) == 17:
                gen = WithoutInterwikiPageGenerator()
            else:
                gen = WithoutInterwikiPageGenerator(number = int(arg[18:]))
        elif arg.startswith('-interwiki'):
            title = arg[11:]
            if not title:
                title = pywikibot.input(u'Which page should be processed?')
            page = pywikibot.Page(pywikibot.Link(title,
                                                 pywikibot.Site()))
            gen = InterwikiPageGenerator(page)
        elif arg.startswith('-recentchanges'):
            if len(arg) >= 15:
                gen = RecentChangesPageGenerator(total=int(arg[15:]))
            else:
                gen = RecentChangesPageGenerator(total=60)
            gen = DuplicateFilterPageGenerator(gen)
        elif arg.startswith('-file'):
            textfilename = arg[6:]
            if not textfilename:
                textfilename = pywikibot.input(
                    u'Please enter the local file name:')
            gen = TextfilePageGenerator(textfilename)
        elif arg.startswith('-namespace'):
            if len(arg) == len('-namespace'):
                self.namespaces.append(
                    pywikibot.input(u'What namespace are you filtering on?'))
            else:
                self.namespaces.extend(arg[len('-namespace:'):].split(","))
            return True
        elif arg.startswith('-ns'):
            if len(arg) == len('-ns'):
                self.namespaces.append(
                    pywikibot.input(u'What namespace are you filtering on?'))
            else:
                self.namespaces.extend(arg[len('-ns:'):].split(","))
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
            gen = self.getCategoryGen(arg, len('-catr'), recurse = True)
        elif arg.startswith('-category'):
            gen = self.getCategoryGen(arg, len('-category'))
        elif arg.startswith('-cat'):
            gen = self.getCategoryGen(arg, len('-cat'))
        elif arg.startswith('-subcatsr'):
            gen = self.setSubCategoriesGen(arg, 9, recurse = True)
        elif arg.startswith('-subcats'):
            gen = self.setSubCategoriesGen(arg, 8)
        elif arg.startswith('-page'):
            if len(arg) == len('-page'):
                gen = [pywikibot.Page(
                           pywikibot.Link(
                               pywikibot.input(
                                   u'What page do you want to use?'),
                               pywikibot.getSite())
                           )]
            else:
                gen = [pywikibot.Page(pywikibot.Link(arg[len('-page:'):],
                                                     pywikibot.getSite())
                                      )]
        elif arg.startswith('-uncatfiles'):
            gen = UnCategorizedImageGenerator()
        elif arg.startswith('-uncatcat'):
            gen = UnCategorizedCategoryGenerator()
        elif arg.startswith('-uncat'):
            gen = UnCategorizedPageGenerator()
        elif arg.startswith('-ref'):
            referredPageTitle = arg[5:]
            if not referredPageTitle:
                referredPageTitle = pywikibot.input(
                    u'Links to which page should be processed?')
            referredPage = pywikibot.Page(pywikibot.Link(referredPageTitle,
                                                         pywikibot.Site()))
            gen = ReferringPageGenerator(referredPage)
        elif arg.startswith('-links'):
            linkingPageTitle = arg[7:]
            if not linkingPageTitle:
                linkingPageTitle = pywikibot.input(
                    u'Links from which page should be processed?')
            linkingPage = pywikibot.Page(pywikibot.Link(linkingPageTitle,
                                                        pywikibot.Site()))
            gen = LinkedPageGenerator(linkingPage)
        elif arg.startswith('-weblink'):
            url = arg[9:]
            if not url:
                url = pywikibot.input(
                    u'Pages with which weblink should be processed?')
            gen = LinksearchPageGenerator(url)
        elif arg.startswith('-transcludes'):
            transclusionPageTitle = arg[len('-transcludes:'):]
            if not transclusionPageTitle:
                transclusionPageTitle = pywikibot.input(
                    u'Pages that transclude which page should be processed?')
            transclusionPage = pywikibot.Page(
                                   pywikibot.Link(transclusionPageTitle,
                                                  defaultNamespace=10,
                                                  source=pywikibot.Site()))
            gen = ReferringPageGenerator(transclusionPage,
                                         onlyTemplateInclusion=True)
        elif arg.startswith('-start'):
            firstPageTitle = arg[7:]
            if not firstPageTitle:
                firstPageTitle = pywikibot.input(
                    u'At which page do you want to start?')
            firstpagelink = pywikibot.Link(firstPageTitle,
                                           pywikibot.Site())
            namespace = firstpagelink.namespace
            firstPageTitle = firstpagelink.title
            gen = AllpagesPageGenerator(firstPageTitle, namespace,
                                        includeredirects=False)
        elif arg.startswith('-prefixindex'):
            prefix = arg[13:]
            namespace = None
            if not prefix:
                prefix = pywikibot.input(
                    u'What page names are you looking for?')
            gen = PrefixingPageGenerator(prefix=prefix)
        elif arg.startswith('-newimages'):
            limit = arg[11:] or pywikibot.input(
                u'How many images do you want to load?')
            gen = NewimagesPageGenerator(total=int(limit))
        elif arg.startswith('-newpages'):
            if len(arg) >= 10:
              gen = NewpagesPageGenerator(total=int(arg[10:]))
            else:
              gen = NewpagesPageGenerator(total=60)
        elif arg.startswith('-imagesused'):
            imagelinkstitle = arg[len('-imagesused:'):]
            if not imagelinkstitle:
                imagelinkstitle = pywikibot.input(
                    u'Images on which page should be processed?')
            imagelinksPage = pywikibot.Page(pywikibot.Link(imagelinkstitle,
                                                           pywikibot.Site()))
            gen = ImagesPageGenerator(imagelinksPage)
        elif arg.startswith('-search'):
            mediawikiQuery = arg[8:]
            if not mediawikiQuery:
                mediawikiQuery = pywikibot.input(
                    u'What do you want to search for?')
            # In order to be useful, all namespaces are required
            gen = SearchPageGenerator(mediawikiQuery, namespaces = [])
        elif arg.startswith('-google'):
            gen = GoogleSearchPageGenerator(arg[8:])
        elif arg.startswith('-titleregex'):
            if len(arg) == 6:
                regex = pywikibot.input(
                    u'What page names are you looking for?')
            else:
                regex = arg[7:]
            gen = RegexFilterPageGenerator(pywikibot.Site().allpages(), regex)
        elif arg.startswith('-yahoo'):
            gen = YahooSearchPageGenerator(arg[7:])
        else:
            pass
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
    @param total: Maxmum number of pages to retrieve in total
    @param content: If True, load current version of each page (default False)

    """
    if site is None:
        site = pywikibot.getSite()
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


@deprecate_arg("number", "total")
@deprecate_arg("namespace", "namespaces")
@deprecate_arg("repeat", None)
def NewpagesPageGenerator(get_redirect=False, repeat=False, site=None,
                          namespaces=[0,], step=None, total=None):
    """
    Iterate Page objects for all new titles in a single namespace.
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
                               step=None, total=None, site=None):
    """Generate pages that are in the recent changes list.

    @param start: Timestamp to start listing from
    @param end: Timestamp to end listing at
    @param reverse: if True, start with oldest changes (default: newest)
    @param limit: iterate no more than this number of entries
    @param pagelist: iterate changes to pages in this list only
    @param pagelist: list of Pages
    @param changetype: only iterate changes of this type ("edit" for
        edits to existing pages, "new" for new pages, "log" for log
        entries)
    @param showMinor: if True, only list minor edits; if False (and not
        None), only list non-minor edits
    @param showBot: if True, only list bot edits; if False (and not
        None), only list non-bot edits
    @param showAnon: if True, only list anon edits; if False (and not
        None), only list non-anon edits
    @param showRedirects: if True, only list edits to redirect pages; if
        False (and not None), only list edits to non-redirect pages
    @param showPatrolled: if True, only list patrolled edits; if False
        (and not None), only list non-patrolled edits

    """
    if site is None:
        site = pywikibot.Site()
    for item in site.recentchanges(start=start, end=end, reverse=reverse,
                                   namespaces=namespaces, pagelist=pagelist,
                                   changetype=changetype, showMinor=showMinor,
                                   showBot=showBot, showAnon=showAnon,
                                   showRedirects=showRedirects,
                                   showPatrolled=showPatrolled,
                                   step=step, total=total):
        yield pywikibot.Page(pywikibot.Link(item["title"], site))


def FileLinksGenerator(referredImagePage, step=None, total=None, content=False):
    return referredImagePage.usingPages(step=step, total=total, content=content)


def ImagesPageGenerator(pageWithImages, step=None, total=None, content=False):
    return pageWithImages.imagelinks(step=step, total=total, content=content)


def InterwikiPageGenerator(page):
    """Iterator over all interwiki (non-language) links on a page."""
    for link in page.interwiki():
        yield pywikibot.Page(link)


def LanguageLinksPageGenerator(page, step=None, total=None):
    """Iterator over all interwiki language links on a page."""
    for link in page.iterlanglinks(step=step, total=total):
        yield pywikibot.Page(link)


def ReferringPageGenerator(referredPage, followRedirects=False,
                           withTemplateInclusion=True,
                           onlyTemplateInclusion=False,
                           step=None, total=None, content=False):
    '''Yields all pages referring to a specific page.'''
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
    # TODO: page generator could be modified to use cmstartsortkey ...
    for a in category.articles(
                      recurse=recurse, step=step, total=total, content=content):
        if start is None or a.title(withNamespace=False) >= start:
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
    for s in category.subcategories(
                      recurse=recurse, step=step, total=total, content=content):
        if start is None or s.title(withNamespace=False) >= start:
            yield s


def LinkedPageGenerator(linkingPage, step=None, total=None, content=False):
    """Yield all pages linked from a specific page."""
    return linkingPage.linkedPages(step=step, total=total, content=content)


def TextfilePageGenerator(filename=None, site=None):
    """Iterate pages from a list in a text file.

    The file must contain page links between double-square-brackets.  The
    generator will yield each corresponding Page object.

    @param filename: the name of the file that should be read. If no name is
                     given, the generator prompts the user.
    @param site: the default Site for which Page objects should be created

    """
    if filename is None:
        filename = pywikibot.input(u'Please enter the filename:')
    if site is None:
        site = pywikibot.Site()
    f = codecs.open(filename, 'r', config.textfile_encoding)
    for linkmatch in pywikibot.link_regex.finditer(f.read()):
        # If the link is in interwiki format, the Page object may reside
        # on a different Site than the default.
        # This makes it possible to work on different wikis using a single
        # text file, but also could be dangerous because you might
        # inadvertently change pages on another wiki!
        yield pywikibot.Page(pywikibot.Link(linkmatch.groups("title"), site))
    f.close()


def PagesFromTitlesGenerator(iterable, site=None):
    """Generate pages from the titles (unicode strings) yielded by iterable."""
    if site is None:
        site = pywikibot.Site()
    for title in iterable:
        if not isinstance(title, basestring):
            break
        yield pywikibot.Page(pywikibot.Link(title, site))


@deprecate_arg("number", "total")
def UserContributionsGenerator(username, namespaces=None, site=None,
                               step=None, total=None):
    """Yield unique pages edited by user:username

    @param namespaces: list of namespace numbers to fetch contribs from

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
    Wraps around another generator. Yields only those pages that are in one
    of the given namespaces.

    The namespace list can contain both integers (namespace numbers) and
    strings/unicode strings (namespace names).

    NOTE: API-based generators that have a "namespaces" parameter perform
    namespace filtering more efficiently than this generator.

    """
    if site is None:
        site = pywikibot.Site()
    # convert namespace names to namespace numbers
    for i in xrange(len(namespaces)):
        ns = namespaces[i]
        if isinstance(ns, basestring):
            try:
                # namespace might be given as str representation of int
                index = int(ns)
            except ValueError:
                index = site.getNamespaceIndex(ns)
                if index is None:
                    raise ValueError(u'Unknown namespace: %s' % ns)
            namespaces[i] = index
    for page in generator:
        if page.namespace() in namespaces:
            yield page


def RedirectFilterPageGenerator(generator):
    """Yields pages from another generator that are not redirects."""
    for page in generator:
        if not page.isRedirectPage():
            yield page


def DuplicateFilterPageGenerator(generator):
    """Yield all unique pages from another generator, omitting duplicates."""
    seenPages = {}
    for page in generator:
        if page not in seenPages:
            seenPages[page] = True
            yield page


def RegexFilterPageGenerator(generator, regex):
    """Yield pages from another generator whose titles match regex."""
    reg = re.compile(regex, re.I)
    for page in generator:
        if reg.match(page.title(withNamespace=False)):
            yield page


def CombinedPageGenerator(generators):
    return itertools.chain(*generators)


def CategoryGenerator(generator):
    """Yield pages from another generator as Category objects.

    Makes sense only if it is ascertained that only categories are being
    retrieved.

    """
    for page in generator:
        yield pywikibot.Category(page)


def PageWithTalkPageGenerator(generator):
    """Yield pages and associated talk pages from another generator.

    Only yields talk pages if the original generator yields a non-talk page,
    and does not check if the talk page in fact exists.

    """
    for page in generator:
        yield page
        if not page.isTalkPage():
            yield page.toggleTalkPage()


@deprecate_arg("pageNumber", "step")
@deprecate_arg("lookahead", None)
def PreloadingGenerator(generator, step=50):
    """Yield preloaded pages taken from another generator."""

    # pages may be on more than one site, for example if an interwiki
    # generator is used, so use a separate preloader for each site
    sites = {}
    # build a list of pages for each site found in the iterator
    for page in generator:
        site = page.site
        sites.setdefault(site, []).append(page)
        if len(sites[site]) >= step:
            group = sites[site]
            sites[site] = []
            for i in site.preloadpages(group, step):
                yield i
    for site in sites:
        if sites[site]:
            for i in site.preloadpages(sites[site], step):
                yield i


def NewimagesPageGenerator(step=None, total=None, site=None):
    if site is None:
        site = pywikibot.Site()
    for entry in site.logevents(logtype="upload", step=step, total=total):
        # entry is an UploadEntry object
        # entry.title() returns a Page object
        yield entry.title()


#TODO below

def UnusedFilesGenerator(number=100, repeat=False, site=None, extension=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.unusedfiles(number=number, repeat=repeat,
                                 extension=extension):
        yield pywikibot.ImagePage(page.site, page.title())

def WithoutInterwikiPageGenerator(number=100, repeat=False, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.withoutinterwiki(number=number, repeat=repeat):
        yield page

def UnCategorizedCategoryGenerator(number=100, repeat=False, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedcategories(number=number, repeat=repeat):
        yield page

def UnCategorizedImageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedimages(number=number, repeat=repeat):
        yield page

def UnCategorizedPageGenerator(number=100, repeat=False, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedpages(number=number, repeat=repeat):
        yield page

def LonelyPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page in site.lonelypages(number=number, repeat=repeat):
        yield page

def UnwatchedPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page in site.unwatchedpages(number=number, repeat=repeat):
        yield page

def AncientPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page, date in site.ancientpages(number=number, repeat=repeat):
        yield page

def DeadendPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page in site.deadendpages(number=number, repeat=repeat):
        yield page

def LongPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page, length in site.longpages(number=number, repeat=repeat):
        yield page

def ShortPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page, length in site.shortpages(number=number, repeat=repeat):
        yield page

def LinksearchPageGenerator(link, namespaces=None, step=None, total=None,
                            site=None):
    """Yields all pages that include a specified link, according to
    [[Special:Linksearch]].

    """
    if site is None:
        site = pywikibot.Site()
    for page in site.exturlusage(link, namespaces=namespaces, step=step,
                                 total=total, content=False):
        yield page

def SearchPageGenerator(query, ste=None, total=None, namespaces=None, site=None):
    """
    Provides a list of results using the internal MediaWiki search engine
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.search(query, step=step, total=total, namespaces=namespaces):
        yield page

# following classes just ported from version 1 without revision; not tested

class YahooSearchPageGenerator:
    '''
    To use this generator, install pYsearch
    '''
    def __init__(self, query = None, count = 100, site = None): # values larger than 100 fail
        self.query = query or pywikibot.input(u'Please enter the search query:')
        self.count = count
        if site is None:
            site = pywikibot.Site()
        self.site = site

    def queryYahoo(self, query):
       from yahoo.search.web import WebSearch
       srch = WebSearch(config.yahoo_appid, query=query, results=self.count)

       dom = srch.get_results()
       results = srch.parse_results(dom)
       for res in results:
           url = res.Url
           yield url

    def __iter__(self):
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
    '''
    To use this generator, you must install the pyGoogle module from
    http://pygoogle.sf.net/ and get a Google Web API license key from
    http://www.google.com/apis/index.html . The google_key must be set to your
    license key in your configuration.
    '''
    def __init__(self, query = None, site = None):
        self.query = query or pywikibot.input(u'Please enter the search query:')
        if site is None:
            site = pywikibot.Site()
        self.site = site

    #########
    # partially commented out because it is probably not in compliance with Google's "Terms of
    # service" (see 5.3, http://www.google.com/accounts/TOS?loc=US)
    def queryGoogle(self, query):
        #if config.google_key:
        if True:
            #try:
                for url in self.queryViaSoapApi(query):
                    yield url
                return
            #except ImportError:
                #pass
        # No google license key, or pygoogle not installed. Do it the ugly way.
        #for url in self.queryViaWeb(query):
        #    yield url

    def queryViaSoapApi(self, query):
        import google
        google.LICENSE_KEY = config.google_key
        offset = 0
        estimatedTotalResultsCount = None
        while not estimatedTotalResultsCount \
              or offset < estimatedTotalResultsCount:
            while (True):
                # Google often yields 502 errors.
                try:
                    pywikibot.output(u'Querying Google, offset %i' % offset)
                    data = google.doGoogleSearch(query, start = offset, filter = False)
                    break
                except KeyboardInterrupt:
                    raise
                except:
                    # SOAPpy.Errors.HTTPError or SOAP.HTTPError (502 Bad Gateway)
                    # can happen here, depending on the module used. It's not easy
                    # to catch this properly because pygoogle decides which one of
                    # the soap modules to use.
                    pywikibot.output(u"An error occured. Retrying in 10 seconds...")
                    time.sleep(10)
                    continue

            for result in data.results:
                #print 'DBG: ', result.URL
                yield result.URL
            # give an estimate of pages to work on, but only once.
            if not estimatedTotalResultsCount:
                pywikibot.output(u'Estimated total result count: %i pages.' % data.meta.estimatedTotalResultsCount)
            estimatedTotalResultsCount = data.meta.estimatedTotalResultsCount
            #print 'estimatedTotalResultsCount: ', estimatedTotalResultsCount
            offset += 10

    #########
    # commented out because it is probably not in compliance with Google's "Terms of
    # service" (see 5.3, http://www.google.com/accounts/TOS?loc=US)

    #def queryViaWeb(self, query):
        #"""
        #Google has stopped giving out API license keys, and sooner or later
        #they will probably shut down the service.
        #This is a quick and ugly solution: we just grab the search results from
        #the normal web interface.
        #"""
        #linkR = re.compile(r'<a href="([^>"]+?)" class=l>', re.IGNORECASE)
        #offset = 0

        #while True:
            #pywikibot.output("Google: Querying page %d" % (offset / 100 + 1))
            #address = "http://www.google.com/search?q=%s&num=100&hl=en&start=%d" % (urllib.quote_plus(query), offset)
            ## we fake being Firefox because Google blocks unknown browsers
            #request = urllib2.Request(address, None, {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.8) Gecko/20051128 SUSE/1.5-0.1 Firefox/1.5'})
            #urlfile = urllib2.urlopen(request)
            #page = urlfile.read()
            #urlfile.close()
            #for url in linkR.findall(page):
                #yield url
            #if "<div id=nn>" in page: # Is there a "Next" link for next page of results?
                #offset += 100  # Yes, go to next page of results.
            #else:
                #return
    #########

    def __iter__(self):
        # restrict query to local site
        localQuery = '%s site:%s' % (self.query, self.site.hostname())
        base = 'http://%s%s' % (self.site.hostname(),
                                self.site.nice_get_address(''))
        for url in self.queryGoogle(localQuery):
            if url[:len(base)] == base:
                title = url[len(base):]
                page = pywikibot.Page(pywikibot.Link(title, self.site))
                # Google contains links in the format http://de.wikipedia.org/wiki/en:Foobar
                if page.site == self.site:
                    yield page

def MySQLPageGenerator(query, site = None):
    import MySQLdb as mysqldb
    if site is None:
        site = pywikibot.Site()
    conn = mysqldb.connect(config.db_hostname, db = site.dbName(),
                           user = config.db_username,
                           passwd = config.db_password)
    cursor = conn.cursor()
    pywikibot.output(u'Executing query:\n%s' % query)
    query = query.encode(site.encoding())
    cursor.execute(query)
    while True:
        try:
            namespaceNumber, pageName = cursor.fetchone()
            print namespaceNumber, pageName
        except TypeError:
            # Limit reached or no more results
            break
        #print pageName
        if pageName:
            namespace = site.namespace(namespaceNumber)
            pageName = unicode(pageName, site.encoding())
            if namespace:
                pageTitle = '%s:%s' % (namespace, pageName)
            else:
                pageTitle = pageName
            page = pywikibot.Page(site, pageTitle)
            yield page

def YearPageGenerator(start = 1, end = 2050, site = None):
    if site is None:
        site = pywikibot.Site()
    pywikibot.output(u"Starting with year %i" % start)
    for i in xrange(start, end + 1):
        if i % 100 == 0:
            pywikibot.output(u'Preparing %i...' % i)
        # There is no year 0
        if i != 0:
            current_year = date.formatYear(site.lang, i )
            yield pywikibot.Page(pywikibot.Link(current_year, site))

def DayPageGenerator(startMonth = 1, endMonth = 12, site = None):
    if site is None:
        site = pywikibot.Site()
    fd = date.FormatDate(site)
    firstPage = pywikibot.Page(site, fd(startMonth, 1))
    pywikibot.output(u"Starting with %s" % firstPage.title(asLink=True))
    for month in xrange(startMonth, endMonth+1):
        for day in xrange(1, date.getNumberOfDaysInMonth(month)+1):
            yield pywikibot.Page(pywikibot.Link(fd(month, day), site))


def main(*args):
    try:
        gen = None
        genFactory = GeneratorFactory()
        for arg in pywikibot.handleArgs(*args):
            genFactory.handleArg(arg)
        gen = genFactory.getCombinedGenerator()
        if gen:
            for page in gen:
                pywikibot.stdout(page.title())
        else:
            pywikibot.showHelp()
    except Exception:
        pywikibot.error("Fatal error", exc_info=True)
    finally:
        pywikibot.stopme()


if __name__=="__main__":
    main()
