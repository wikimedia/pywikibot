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
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import pywikibot

import itertools
import Queue
import re
import sys
import threading


# ported from version 1 for backwards-compatibility
# most of these functions just wrap a Site or Page method that returns
# a generator

parameterHelp = """\
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

-yahoo            Work on all pages that are found in a Yahoo search.
                  Depends on python module pYsearch.  See yahoo_appid in
                  config.py for instructions.

-search           Work on all pages that are found in a MediaWiki search
                  across all namespaces.

-google           Work on all pages that are found in a Google search.
                  You need a Google Web API license key. Note that Google
                  doesn't give out license keys anymore. See google_key in
                  config.py for instructions.
                  Argument can also be given as "-google:searchstring".

-interwiki        Work on the given page and all equivalent pages in other
                  languages. This can, for example, be used to fight
                  multi-site spamming.
                  Attention: this will cause the bot to modify
                  pages on several wiki sites, this is not well tested,
                  so check your edits!

-links            Work on all pages that are linked from a certain page.
                  Argument can also be given as "-links:linkingpagetitle".

-new              Work on the 60 newest pages. If given as -new:x, will work
                  on the x newest pages.

-imagelinks       Work on all images that are linked from a certain page.
                  Argument can also be given as "-imagelinks:linkingpagetitle".

-newimages        Work on the 100 newest images. If given as -newimages:x,
                  will work on the x newest images.

-ref              Work on all pages that link to a certain page.
                  Argument can also be given as "-ref:referredpagetitle".

-start            Specifies that the robot should go alphabetically through
                  all pages on the home wiki, starting at the named page.
                  Argument can also be given as "-start:pagetitle".

                  You can also include a namespace. For example,
                  "-start:Template:!" will make the bot work on all pages
                  in the template namespace.

-prefixindex      Work on pages commencing with a common prefix.

-regex            Obsolete, use -titleregex

-titleregex       Work on titles that match the given regular expression.

-transcludes      Work on all pages that use a certain template.
                  Argument can also be given as "-transcludes:Template:Title".

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
"""

docuReplacements = {'&params;': parameterHelp}

# if a bot uses GeneratorFactory, the module should include the line
#   docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}
# and include the marker &params; in the module's docstring


class GeneratorFactory(object):
    """Process command line arguments and return appropriate page generator."""

    def setCategoryGen(self, arg, length, recurse = False):
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

        cat = pywikibot.Category(pywikibot.Link('Category:%s' % categoryname))
        return CategorizedPageGenerator(cat, start=startfrom, recurse=recurse)

    def setSubCategoriesGen(self, arg, length, recurse=False):
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

        cat = pywikibot.Category(pywikibot.Link('Category:%s' % categoryname))
        return SubCategoriesPageGenerator(cat, start=startfrom, recurse=recurse)

    def handleArg(self, arg):
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
            page = pywikibot.Page(pywikibot.Site(), title)
            gen = InterwikiPageGenerator(page)
        elif arg.startswith('-file'):
            textfilename = arg[6:]
            if not textfilename:
                textfilename = pywikibot.input(
                    u'Please enter the local file name:')
            gen = TextfilePageGenerator(textfilename)
        elif arg.startswith('-catr'):
            gen = self.setCategoryGen(arg, 5, recurse = True)
        elif arg.startswith('-cat'):
            gen = self.setCategoryGen(arg, 4)
        elif arg.startswith('-subcatsr'):
            gen = self.setSubCategoriesGen(arg, 9, recurse = True)
        elif arg.startswith('-subcats'):
            gen = self.setSubCategoriesGen(arg, 8)
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
            referredPage = pywikibot.Page(pywikibot.Site(), referredPageTitle)
            gen = ReferringPageGenerator(referredPage)
        elif arg.startswith('-links'):
            linkingPageTitle = arg[7:]
            if not linkingPageTitle:
                linkingPageTitle = pywikibot.input(
                    u'Links from which page should be processed?')
            linkingPage = pywikibot.Page(pywikibot.Site(), linkingPageTitle)
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
            transclusionPage = pywikibot.Page(pywikibot.Site(),
                                    'Template:%s' % transclusionPageTitle)
            gen = ReferringPageGenerator(transclusionPage,
                                         onlyTemplateInclusion=True)
        elif arg.startswith('-start'):
            if arg.startswith('-startxml'):
                pywikibot.output(u'-startxml : wrong parameter')
                raise ValueError
            firstPageTitle = arg[7:]
            if not firstPageTitle:
                firstPageTitle = pywikibot.input(
                    u'At which page do you want to start?')
            namespace = pywikibot.Page(pywikibot.Site(),
                                       firstPageTitle).namespace()
            firstPageTitle = pywikibot.Page(pywikibot.link(firstPageTitle)
                                           ).titleWithoutNamespace()
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
            gen = NewimagesPageGenerator(number=int(limit))
        elif arg.startswith('-new'):
            if len(arg) >=5:
              gen = NewpagesPageGenerator(number=int(arg[5:]))
            else:
              gen = NewpagesPageGenerator(number=60)
        elif arg.startswith('-imagelinks'):
            imagelinkstitle = arg[len('-imagelinks:'):]
            if not imagelinkstitle:
                imagelinkstitle = pywikibot.input(
                    u'Images on which page should be processed?')
            imagelinksPage = pywikibot.Page(pywikibot.Link(imagelinkstitle))
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
            return None
        # make sure all yielded pages are unique
        gen = DuplicateFilterPageGenerator(gen)
        return gen


class ThreadedGenerator(threading.Thread):
    """Look-ahead generator class.

    Runs a generator in a separate thread and queues the results; can
    be called like a regular generator.

    Subclasses should override self.generator, _not_ self.run

    Important: the generator thread will stop itself if the generator's
    internal queue is exhausted; but, if the calling program does not use
    all the generated values, it must call the generator's stop() method to
    stop the background thread.  Example usage:

    >>> gen = ThreadedGenerator(target=foo)
    >>> try:
    ...     for data in gen:
    ...         do_work(data)
    ... finally:
    ...     gen.stop()

    """ #NOT CURRENTLY USED: Intended for future development

    def __init__(self, group=None, target=None, name="GeneratorThread",
                 args=(), kwargs=None, qsize=65536):
        """Constructor.  Takes same keyword arguments as threading.Thread.

        target must be a generator function (or other callable that returns
        an iterable object).

        @param qsize: The size of the lookahead queue. The larger the qsize,
        the more values will be computed in advance of use (which can eat
        up memory and processor time).
        @type qsize: int

        """
        if kwargs is None:
            kwargs = {}
        if target:
            self.generator = target
        if not hasattr(self, "generator"):
            raise RuntimeError("No generator for ThreadedGenerator to run.")
        self.args, self.kwargs = args, kwargs
        threading.Thread.__init__(self, group=group, name=name)
        self.queue = Queue.Queue(qsize)
        self.finished = threading.Event()

    def __iter__(self):
        """Iterate results from the queue."""
        if not self.isAlive() and not self.finished.isSet():
            self.start()
        # if there is an item in the queue, yield it, otherwise wait
        while not self.finished.isSet():
            try:
                yield self.queue.get(True, 0.25)
            except Queue.Empty:
                pass
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        """Stop the background thread."""
##        if not self.finished.isSet():
##            pywikibot.output("DEBUG: signalling %s to stop." % self)
        self.finished.set()

    def run(self):
        """Run the generator and store the results on the queue."""
        self.__gen = self.generator(*self.args, **self.kwargs)
        for result in self.__gen:
            while True:
                if self.finished.isSet():
##                    pywikibot.output("DEBUG: %s received stop signal." % self)
                    return
                try:
                    self.queue.put_nowait(result)
                except Queue.Full:
                    time.sleep(0.25)
                    continue
                break
        # wait for queue to be emptied, then kill the thread
        while not self.finished.isSet() and not self.queue.empty():
            time.sleep(0.25)
        self.stop()
##        pywikibot.output("DEBUG: %s stopped because generator exhausted." % self)


def AllpagesPageGenerator(start ='!', namespace=None, includeredirects=True,
                          site=None):
    """
    Using the Allpages special page, retrieve all articles' titles, and yield
    page objects.
    If includeredirects is False, redirects are not included. If
    includeredirects equals the string 'only', only redirects are added.
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
                         filterredir=filterredir)


def PrefixingPageGenerator(prefix, namespace=None, includeredirects=True,
                           site=None):
    if site is None:
        site = pywikibot.Site()
    page = pywikibot.Page(site, prefix)
    if namespace is None:
        namespace = page.namespace()
    title = page.titleWithoutNamespace()
    if includeredirects:
        if includeredirects == 'only':
            filterredir = True
        else:
            filterredir = None
    else:
        filterredir = False
    return site.allpages(prefix=title, namespace=namespace,
                         filterredir=filterredir)


def NewpagesPageGenerator(number=100, get_redirect=False, repeat=False,
                          site=None):
    # API does not (yet) have a newpages function, so this tries to duplicate
    # it by filtering the recentchanges output
    # defaults to namespace 0 because that's how Special:Newpages defaults
    if site is None:
        site = pywikibot.Site()
    return site.recentchanges(limit=number, showredirects=get_redirect,
                              changetype="new", namespaces=0)


def FileLinksGenerator(referredImagePage):
    return referredImagePage.usingPages()


def ImagesPageGenerator(pageWithImages):
    return pageWithImages.imagelinks()


def InterwikiPageGenerator(page):
    """Iterator over all interwiki (non-language) links on a page."""
    for link in page.interwiki():
        yield pywikibot.Page(link)


def LanguageLinksPageGenerator(page):
    """Iterator over all interwiki language links on a page."""
    for link in page.langlinks():
        yield pywikibot.Page(link)


def ReferringPageGenerator(referredPage, followRedirects=False,
                           withTemplateInclusion=True,
                           onlyTemplateInclusion=False):
    '''Yields all pages referring to a specific page.'''
    return referredPage.getReferences(
                follow_redirects=followRedirects,
                withTemplateInclusion=withTemplateInclusion,
                onlyTemplateInclusion=onlyTemplateInclusion)


def CategorizedPageGenerator(category, recurse=False, start=None):
    '''Yield all pages in a specific category.

    If recurse is True, pages in subcategories are included as well; if
    recurse is an int, only subcategories to that depth will be included
    (e.g., recurse=2 will get pages in subcats and sub-subcats, but will
    not go any further).
    If start is a string value, only pages whose sortkey comes after start
    alphabetically are included.

    ''' # TODO: page generator could be modified to use cmstartsortkey ...
    for a in category.articles(recurse=recurse):
        if start is None or a.title(withNamespace=False) >= start:
            yield a


def SubCategoriesPageGenerator(category, recurse=False, start=None):
    '''Yields all subcategories in a specific category.

    If recurse is True, pages in subcategories are included as well; if
    recurse is an int, only subcategories to that depth will be included
    (e.g., recurse=2 will get pages in subcats and sub-subcats, but will
    not go any further).
    If start is a string value, only categories whose sortkey comes after
    start alphabetically are included.

    ''' # TODO: page generator could be modified to use cmstartsortkey ...
    for s in category.subcategories(recurse=recurse):
        if start is None or s.title(withNamespace=False) >= start:
            yield s


def LinkedPageGenerator(linkingPage):
    """Yields all pages linked from a specific page."""
    return linkingPage.linkedPages()


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


def UserContributionsGenerator(username, number=250, namespaces=None,
                               site=None):
    """Yields number unique pages edited by user:username
    namespaces : list of namespace numbers to fetch contribs from

    """
    if site is None:
        site = pywikibot.Site()
    return site.usercontribs(user=username, limit=number, namespaces=namespaces)


def NamespaceFilterPageGenerator(generator, namespaces, site=None):
    """
    Wraps around another generator. Yields only those pages that are in one
    of the given namespaces.

    The namespace list can contain both integers (namespace numbers) and
    strings/unicode strings (namespace names).

    """
    if site is None:
        site = pywikibot.Site()
    # convert namespace names to namespace numbers
    for i in xrange(len(namespaces)):
        ns = namespaces[i]
        if isinstance(ns, basestring):
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
            seenPages[page] = None
            yield page


def RegexFilterPageGenerator(generator, regex):
    """Yield pages from another generator whose titles match regex."""
    reg = re.compile(regex, re.I)
    for page in generator:
        if reg.match(page.titleWithoutNamespace()):
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
    """
    Wraps around another generator. Yields the same pages, but for non-talk
    pages, it also includes associated talk pages.
    This generator does not check if the talk page in fact exists.
    """
    for page in generator:
        yield page
        if not page.isTalkPage():
            yield page.toggleTalkPage()


def PreloadingGenerator(generator, pageNumber=60, lookahead=10):
    """Yield preloaded pages taken from another generator."""

    # pages may be on more than one site, for example if an interwiki
    # generator is used, so use a separate preloader for each site
    sites = {}
    # build a list of pages for each site found in the iterator
    for page in generator:
        sites.setdefault(page.site(), []).append(page)
    return itertools.chain(*(site.preloadpages(sites[site], pageNumber)
                             for site in sites))


#TODO below

def UnusedFilesGenerator(number=100, repeat=False, site=None, extension=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.unusedfiles(number=number, repeat=repeat,
                                 extension=extension):
        yield pywikibot.ImagePage(page.site(), page.title())

def WithoutInterwikiPageGenerator(number=100, repeat=False, site=None):
    if site is None:
        site = pywikibot.Site()
    for page in site.withoutinterwiki(number=number, repeat=repeat):
        yield page

def UnCategorizedCategoryGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedcategories(number=number, repeat=repeat):
        yield page

def UnCategorizedImageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page in site.uncategorizedimages(number=number, repeat=repeat):
        yield page

def NewimagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page in site.newimages(number, repeat=repeat):
        yield page[0]

def UnCategorizedPageGenerator(number = 100, repeat = False, site = None):
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
    for page in site.ancientpages(number=number, repeat=repeat):
        yield page[0]

def DeadendPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page in site.deadendpages(number=number, repeat=repeat):
        yield page

def LongPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page in site.longpages(number=number, repeat=repeat):
        yield page[0]

def ShortPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = pywikibot.Site()
    for page in site.shortpages(number=number, repeat=repeat):
        yield page[0]

def LinksearchPageGenerator(link, step=500, site=None):
    """Yields all pages that include a specified link, according to
    [[Special:Linksearch]].

    """
    if site is None:
        site = pywikibot.Site()
    for page in site.linksearch(link, limit=step):
        yield page

def SearchPageGenerator(query, number = 100, namespaces = None, site = None):
    """
    Provides a list of results using the internal MediaWiki search engine
    """
    if site is None:
        site = pywikibot.Site()
    for page in site.search(query, number=number, namespaces = namespaces):
        yield page[0]

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
        base = 'http://%s%s' % (self.site.hostname(), self.site.nice_get_address(''))
        for url in self.queryYahoo(localQuery):
            if url[:len(base)] == base:
                title = url[len(base):]
                page = pywikibot.Page(self.site, title)
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
        while not estimatedTotalResultsCount or offset < estimatedTotalResultsCount:
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
        base = 'http://%s%s' % (self.site.hostname(), self.site.nice_get_address(''))
        for url in self.queryGoogle(localQuery):
            if url[:len(base)] == base:
                title = url[len(base):]
                page = pywikibot.Page(self.site, title)
                # Google contains links in the format http://de.wikipedia.org/wiki/en:Foobar
                if page.site() == self.site:
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
            yield pywikibot.Page(site, current_year)

def DayPageGenerator(startMonth = 1, endMonth = 12, site = None):
    if site is None:
        site = pywikibot.Site()
    fd = date.FormatDate(site)
    firstPage = pywikibot.Page(site, fd(startMonth, 1))
    pywikibot.output(u"Starting with %s" % firstPage.aslink())
    for month in xrange(startMonth, endMonth+1):
        for day in xrange(1, date.getNumberOfDaysInMonth(month)+1):
            yield pywikibot.Page(site, fd(month, day))


if __name__ == "__main__":
    try:
        gen = None
        genFactory = GeneratorFactory()
        for arg in pywikibot.handleArgs():
            generator = genFactory.handleArg(arg)
            if generator:
                gen = generator
        if gen:
            for page in gen:
                pywikibot.output(page.title(), toStdout = True)
        else:
            pywikibot.showHelp()
    finally:
        pywikibot.stopme()
