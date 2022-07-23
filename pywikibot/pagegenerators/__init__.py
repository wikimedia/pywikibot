"""
This module offers a wide variety of page generators.

A page generator is an object that is iterable (see :pep:`255`) and
that yields page objects on which other scripts can then work.

Most of these functions just wrap a Site or Page method that returns a
generator. For testing purposes listpages.py can be used, to print page
titles to standard output.

These parameters are supported to specify which pages titles to print:

&params;
"""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
from typing import Any, Optional

import pywikibot
from pywikibot.backports import Callable, Dict, Iterable, Iterator, List, Set
from pywikibot.pagegenerators._factory import GeneratorFactory
from pywikibot.pagegenerators._filters import (
    CategoryFilterPageGenerator,
    EdittimeFilterPageGenerator,
    ItemClaimFilterPageGenerator,
    NamespaceFilterPageGenerator,
    PageTitleFilterPageGenerator,
    QualityFilterPageGenerator,
    RedirectFilterPageGenerator,
    RegexBodyFilterPageGenerator,
    RegexFilterPageGenerator,
    SubpageFilterGenerator,
    UserEditFilterGenerator,
    WikibaseItemFilterPageGenerator,
)
from pywikibot.pagegenerators._generators import (
    AllpagesPageGenerator,
    AncientPagesPageGenerator,
    CategorizedPageGenerator,
    DayPageGenerator,
    DeadendPagesPageGenerator,
    FileLinksGenerator,
    GoogleSearchPageGenerator,
    ImagesPageGenerator,
    InterwikiPageGenerator,
    LanguageLinksPageGenerator,
    LinkedPageGenerator,
    LinksearchPageGenerator,
    LiveRCPageGenerator,
    LogeventsPageGenerator,
    LonelyPagesPageGenerator,
    LongPagesPageGenerator,
    MySQLPageGenerator,
    NewimagesPageGenerator,
    NewpagesPageGenerator,
    page_with_property_generator,
    PagesFromPageidGenerator,
    PagesFromTitlesGenerator,
    PetScanPageGenerator,
    PrefixingPageGenerator,
    RandomPageGenerator,
    RandomRedirectPageGenerator,
    RecentChangesPageGenerator,
    SearchPageGenerator,
    ShortPagesPageGenerator,
    SubCategoriesPageGenerator,
    TextIOPageGenerator,
    UnCategorizedCategoryGenerator,
    UnCategorizedImageGenerator,
    UnCategorizedPageGenerator,
    UnCategorizedTemplateGenerator,
    UnconnectedPageGenerator,
    UnusedFilesGenerator,
    UnwatchedPagesPageGenerator,
    UserContributionsGenerator,
    WantedPagesPageGenerator,
    WikibaseItemGenerator,
    WikibaseSearchItemPageGenerator,
    WikidataPageFromItemGenerator,
    WikidataSPARQLPageGenerator,
    WithoutInterwikiPageGenerator,
    XMLDumpOldPageGenerator,
    XMLDumpPageGenerator,
    YearPageGenerator,
)
from pywikibot.tools.collections import DequeGenerator

__all__ = (
    'GeneratorFactory',

    'CategoryFilterPageGenerator',
    'EdittimeFilterPageGenerator',
    'ItemClaimFilterPageGenerator',
    'NamespaceFilterPageGenerator',
    'PageTitleFilterPageGenerator',
    'QualityFilterPageGenerator',
    'RedirectFilterPageGenerator',
    'RegexBodyFilterPageGenerator',
    'RegexFilterPageGenerator',
    'SubpageFilterGenerator',
    'UserEditFilterGenerator',
    'WikibaseItemFilterPageGenerator',

    'AllpagesPageGenerator',
    'AncientPagesPageGenerator',
    'CategorizedPageGenerator',
    'DayPageGenerator',
    'DeadendPagesPageGenerator',
    'FileLinksGenerator',
    'GoogleSearchPageGenerator',
    'ImagesPageGenerator',
    'InterwikiPageGenerator',
    'LanguageLinksPageGenerator',
    'LinkedPageGenerator',
    'LinksearchPageGenerator',
    'LiveRCPageGenerator',
    'LogeventsPageGenerator',
    'LonelyPagesPageGenerator',
    'LongPagesPageGenerator',
    'MySQLPageGenerator',
    'NewimagesPageGenerator',
    'NewpagesPageGenerator',
    'page_with_property_generator',
    'PagesFromPageidGenerator',
    'PagesFromTitlesGenerator',
    'PetScanPageGenerator',
    'PrefixingPageGenerator',
    'RandomPageGenerator',
    'RandomRedirectPageGenerator',
    'RecentChangesPageGenerator',
    'SearchPageGenerator',
    'ShortPagesPageGenerator',
    'SubCategoriesPageGenerator',
    'TextIOPageGenerator',
    'UnCategorizedCategoryGenerator',
    'UnCategorizedImageGenerator',
    'UnCategorizedPageGenerator',
    'UnCategorizedTemplateGenerator',
    'UnconnectedPageGenerator',
    'UnusedFilesGenerator',
    'UnwatchedPagesPageGenerator',
    'UserContributionsGenerator',
    'WantedPagesPageGenerator',
    'WikibaseItemGenerator',
    'WikibaseSearchItemPageGenerator',
    'WikidataPageFromItemGenerator',
    'WikidataSPARQLPageGenerator',
    'WithoutInterwikiPageGenerator',
    'XMLDumpOldPageGenerator',
    'XMLDumpPageGenerator',
    'YearPageGenerator',
)


parameterHelp = """\
GENERATOR OPTIONS
=================

-cat                Work on all pages which are in a specific category.
                    Argument can also be given as "-cat:categoryname" or
                    as "-cat:categoryname|fromtitle" (using # instead of |
                    is also allowed in this one and the following)

-catr               Like -cat, but also recursively includes pages in
                    subcategories, sub-subcategories etc. of the
                    given category.
                    Argument can also be given as "-catr:categoryname" or
                    as "-catr:categoryname|fromtitle".

-subcats            Work on all subcategories of a specific category.
                    Argument can also be given as "-subcats:categoryname" or
                    as "-subcats:categoryname|fromtitle".

-subcatsr           Like -subcats, but also includes sub-subcategories etc. of
                    the given category.
                    Argument can also be given as "-subcatsr:categoryname" or
                    as "-subcatsr:categoryname|fromtitle".

-uncat              Work on all pages which are not categorised.

-uncatcat           Work on all categories which are not categorised.

-uncatfiles         Work on all files which are not categorised.

-file               Read a list of pages to treat from the named text file.
                    Page titles in the file may be either enclosed with
                    [[brackets]], or be separated by new lines.
                    Argument can also be given as "-file:filename".

-filelinks          Work on all pages that use a certain image/media file.
                    Argument can also be given as "-filelinks:filename".

-search             Work on all pages that are found in a MediaWiki search
                    across all namespaces.

-logevents          Work on articles that were on a specified Special:Log.
                    The value may be a comma separated list of these values::

                        logevent,username,start,end

                    or for backward compatibility::

                        logevent,username,total

                    .. note:: 'start' is the most recent date and log
                       events are iterated from present to past. If
                       'start' is not provided, it means 'now'; if 'end'
                       is not provided, it means 'since the beginning'.

                    To use the default value, use an empty string.
                    You have options for every type of logs given by the
                    log event parameter which could be one of the following::

                        spamblacklist, titleblacklist, gblblock, renameuser,
                        globalauth, gblrights, gblrename, abusefilter,
                        massmessage, thanks, usermerge, block, protect, rights,
                        delete, upload, move, import, patrol, merge, suppress,
                        tag, managetags, contentmodel, review, stable,
                        timedmediahandler, newusers

                    It uses the default number of pages 10.

                    Examples:

                    -logevents:move gives pages from move log (usually
                    redirects)
                    -logevents:delete,,20 gives 20 pages from deletion log
                    -logevents:protect,Usr gives pages from protect log by user
                    Usr
                    -logevents:patrol,Usr,20 gives 20 patrolled pages by Usr
                    -logevents:upload,,20121231,20100101 gives upload pages
                    in the 2010s, 2011s, and 2012s
                    -logevents:review,,20121231 gives review pages since the
                    beginning till the 31 Dec 2012
                    -logevents:review,Usr,20121231 gives review pages by user
                    Usr since the beginning till the 31 Dec 2012

                    In some cases it must be given as -logevents:"move,Usr,20"

-interwiki          Work on the given page and all equivalent pages in other
                    languages. This can, for example, be used to fight
                    multi-site spamming.
                    Attention: this will cause the bot to modify
                    pages on several wiki sites, this is not well tested,
                    so check your edits!

-links              Work on all pages that are linked from a certain page.
                    Argument can also be given as "-links:linkingpagetitle".

-liverecentchanges  Work on pages from the live recent changes feed. If used as
                    -liverecentchanges:x, work on x recent changes.

-imagesused         Work on all images that contained on a certain page.
                    Can also be given as "-imagesused:linkingpagetitle".

-newimages          Work on the most recent new images. If given as
                    -newimages:x, will work on x newest images.

-newpages           Work on the most recent new pages. If given as -newpages:x,
                    will work on x newest pages.

-recentchanges      Work on the pages with the most recent changes. If
                    given as -recentchanges:x, will work on the x most recently
                    changed pages. If given as -recentchanges:offset,duration
                    it will work on pages changed from 'offset' minutes with
                    'duration' minutes of timespan. rctags are supported too.
                    The rctag must be the very first parameter part.

                    Examples:

                    -recentchanges:20 gives the 20 most recently changed pages
                    -recentchanges:120,70 will give pages with 120 offset
                    minutes and 70 minutes of timespan
                    -recentchanges:visualeditor,10 gives the 10 most recently
                    changed pages marked with 'visualeditor'
                    -recentchanges:"mobile edit,60,35" will retrieve pages
                    marked with 'mobile edit' for the given offset and timespan

-unconnectedpages   Work on the most recent unconnected pages to the Wikibase
                    repository. Given as -unconnectedpages:x, will work on the
                    x most recent unconnected pages.

-ref                Work on all pages that link to a certain page.
                    Argument can also be given as "-ref:referredpagetitle".

-start              Specifies that the robot should go alphabetically through
                    all pages on the home wiki, starting at the named page.
                    Argument can also be given as "-start:pagetitle".

                    You can also include a namespace. For example,
                    "-start:Template:!" will make the bot work on all pages
                    in the template namespace.

                    default value is start:!

-prefixindex        Work on pages commencing with a common prefix.

-transcludes        Work on all pages that use a certain template.
                    Argument can also be given as "-transcludes:Title".

-unusedfiles        Work on all description pages of images/media files that
                    are not used anywhere.
                    Argument can be given as "-unusedfiles:n" where
                    n is the maximum number of articles to work on.

-lonelypages        Work on all articles that are not linked from any other
                    article.
                    Argument can be given as "-lonelypages:n" where
                    n is the maximum number of articles to work on.

-unwatched          Work on all articles that are not watched by anyone.
                    Argument can be given as "-unwatched:n" where
                    n is the maximum number of articles to work on.

-property:name      Work on all pages with a given property name from
                    Special:PagesWithProp.

-usercontribs       Work on all articles that were edited by a certain user.
                    (Example : -usercontribs:DumZiBoT)

-weblink            Work on all articles that contain an external link to
                    a given URL; may be given as "-weblink:url"

-withoutinterwiki   Work on all pages that don't have interlanguage links.
                    Argument can be given as "-withoutinterwiki:n" where
                    n is the total to fetch.

-mysqlquery         Takes a MySQL query string like
                    "SELECT page_namespace, page_title FROM page
                    WHERE page_namespace = 0"
                    and treats the resulting pages. See :manpage:`MySQL`
                    for more details.

-sparql             Takes a SPARQL SELECT query string including ?item
                    and works on the resulting pages.

-sparqlendpoint     Specify SPARQL endpoint URL (optional).
                    (Example: -sparqlendpoint:http://myserver.com/sparql)

-searchitem         Takes a search string and works on Wikibase pages that
                    contain it.
                    Argument can be given as "-searchitem:text", where text
                    is the string to look for, or "-searchitem:lang:text",
                    where lang is the language to search items in.

-wantedpages        Work on pages that are linked, but do not exist;
                    may be given as "-wantedpages:n" where n is the maximum
                    number of articles to work on.

-wantedcategories   Work on categories that are used, but do not exist;
                    may be given as "-wantedcategories:n" where n is the
                    maximum number of categories to work on.

-wantedfiles        Work on files that are used, but do not exist;
                    may be given as "-wantedfiles:n" where n is the maximum
                    number of files to work on.

-wantedtemplates    Work on templates that are used, but do not exist;
                    may be given as "-wantedtemplates:n" where n is the
                    maximum number of templates to work on.

-random             Work on random pages returned by [[Special:Random]].
                    Can also be given as "-random:n" where n is the number
                    of pages to be returned.

-randomredirect     Work on random redirect pages returned by
                    [[Special:RandomRedirect]]. Can also be given as
                    "-randomredirect:n" where n is the number of pages to be
                    returned.

-google             Work on all pages that are found in a Google search.
                    You need a Google Web API license key. Note that Google
                    doesn't give out license keys anymore. See google_key in
                    config.py for instructions.
                    Argument can also be given as "-google:searchstring".

-page               Work on a single page. Argument can also be given as
                    "-page:pagetitle", and supplied multiple times for
                    multiple pages.

-pageid             Work on a single pageid. Argument can also be given as
                    "-pageid:pageid1,pageid2,." or
                    "-pageid:'pageid1|pageid2|..'"
                    and supplied multiple times for multiple pages.

-linter             Work on pages that contain lint errors. Extension Linter
                    must be available on the site.
                    -linter select all categories.
                    -linter:high, -linter:medium or -linter:low select all
                    categories for that prio.
                    Single categories can be selected with commas as in
                    -linter:cat1,cat2,cat3

                    Adding '/int' identifies Lint ID to start querying from:
                    e.g. -linter:high/10000

                    -linter:show just shows available categories.

-querypage:name     Work on pages provided by a QueryPage-based special page,
                    see :api:`Querypage`.
                    (tip: use -limit:n to fetch only n pages).

                    -querypage shows special pages available.

-url                Read a list of pages to treat from the provided URL.
                    The URL must return text in the same format as expected for
                    the -file argument, e.g. page titles separated by newlines
                    or enclosed in brackets.


FILTER OPTIONS
==============

-catfilter          Filter the page generator to only yield pages in the
                    specified category. See -cat generator for argument format.

-grep               A regular expression that needs to match the article
                    otherwise the page won't be returned.
                    Multiple -grep:regexpr can be provided and the page will
                    be returned if content is matched by any of the regexpr
                    provided.
                    Case insensitive regular expressions will be used and
                    dot matches any character, including a newline.

-grepnot            Like -grep, but return the page only if the regular
                    expression does not match.

-intersect          Work on the intersection of all the provided generators.

-limit              When used with any other argument -limit:n specifies a set
                    of pages, work on no more than n pages in total.

-namespaces         Filter the page generator to only yield pages in the
-namespace          specified namespaces. Separate multiple namespace
-ns                 numbers or names with commas.

                    Examples::

                    -ns:0,2,4
                    -ns:Help,MediaWiki

                    You may use a preleading "not" to exclude the namespace.

                    Examples::

                    -ns:not:2,3
                    -ns:not:Help,File

                    If used with -newpages/-random/-randomredirect/-linter
                    generators, -namespace/ns must be provided before
                    -newpages/-random/-randomredirect/-linter.
                    If used with -recentchanges generator, efficiency is
                    improved if -namespace is provided before -recentchanges.

                    If used with -start generator, -namespace/ns shall contain
                    only one value.

-onlyif             A claim the page needs to contain, otherwise the item won't
                    be returned.
                    The format is property=value,qualifier=value. Multiple (or
                    none) qualifiers can be passed, separated by commas.

                    Examples:

                    .. code-block:: shell

                       P1=Q2 (property P1 must contain value Q2),
                       P3=Q4,P5=Q6,P6=Q7 (property P3 with value Q4 and
                       qualifiers: P5 with value Q6 and P6 with value Q7).

                    Value can be page ID, coordinate in format:
                    latitude,longitude[,precision] (all values are in decimal
                    degrees), year, or plain string.

                    The argument can be provided multiple times and the item
                    page will be returned only if all claims are present.
                    Argument can be also given as "-onlyif:expression".

-onlyifnot          A claim the page must not contain, otherwise the
                    item won't be returned. For usage and examples, see
                    `-onlyif` above.

-ql                 Filter pages based on page quality.
                    This is only applicable if contentmodel equals
                    'proofread-page', otherwise has no effects.
                    Valid values are in range 0-4.
                    Multiple values can be comma-separated.

-subpage            -subpage:n filters pages to only those that have depth n
                    i.e. a depth of 0 filters out all pages that are subpages,
                    and a depth of 1 filters out all pages that are subpages of
                    subpages.


-titleregex         A regular expression that needs to match the article title
                    otherwise the page won't be returned.
                    Multiple -titleregex:regexpr can be provided and the page
                    will be returned if title is matched by any of the regexpr
                    provided.
                    Case insensitive regular expressions will be used and
                    dot matches any character.

-titleregexnot      Like -titleregex, but return the page only if the regular
                    expression does not match.
"""  # noqa: N816

docuReplacements = {'&params;': parameterHelp}  # noqa: N816

PRELOAD_SITE_TYPE = Dict[pywikibot.site.BaseSite, List[pywikibot.page.Page]]

# if a bot uses GeneratorFactory, the module should include the line
#   docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}
# and include the marker &params; in the module's docstring
#
# We manually include it so the parameters show up in the auto-generated
# module documentation:

__doc__ = __doc__.replace('&params;', parameterHelp)


def PageClassGenerator(generator: Iterable['pywikibot.page.Page']
                       ) -> Iterator['pywikibot.page.Page']:
    """
    Yield pages from another generator as Page subclass objects.

    The page class type depends on the page namespace.
    Objects may be Category, FilePage, Userpage or Page.
    """
    for page in generator:
        if page.namespace() == page.site.namespaces.USER:
            yield pywikibot.User(page)
        elif page.namespace() == page.site.namespaces.FILE:
            yield pywikibot.FilePage(page)
        elif page.namespace() == page.site.namespaces.CATEGORY:
            yield pywikibot.Category(page)
        else:
            yield page


def PageWithTalkPageGenerator(generator: Iterable['pywikibot.page.Page'],
                              return_talk_only: bool = False
                              ) -> Iterator['pywikibot.page.Page']:
    """Yield pages and associated talk pages from another generator.

    Only yields talk pages if the original generator yields a non-talk page,
    and does not check if the talk page in fact exists.

    """
    for page in generator:
        if not return_talk_only or page.isTalkPage():
            yield page
        if not page.isTalkPage():
            yield page.toggleTalkPage()


def RepeatingGenerator(generator: Callable,  # type: ignore[type-arg]
                       key_func: Callable[[Any], Any] = lambda x: x,
                       sleep_duration: int = 60,
                       total: Optional[int] = None,
                       **kwargs: Any) -> Iterator['pywikibot.page.Page']:
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

    :param generator: a function returning a generator that will be queried
    :param key_func: a function returning key that will be used to detect
        duplicate entry
    :param sleep_duration: duration between each query
    :param total: if it is a positive number, iterate no more than this
        number of items in total. Otherwise, iterate forever
    :return: a generator yielding items in ascending order by time
    """
    kwargs.pop('reverse', None)  # always get newest item first
    kwargs.pop('start', None)  # don't set start time
    kwargs.pop('end', None)  # don't set stop time

    seen = set()  # type: Set[Any]
    while total is None or len(seen) < total:
        def filtered_generator() -> Iterable['pywikibot.page.Page']:
            for item in generator(total=None if seen else 1, **kwargs):
                key = key_func(item)
                if key not in seen:
                    seen.add(key)
                    yield item
                    if len(seen) == total:
                        return
                else:
                    break
            pywikibot.sleep(sleep_duration)

        yield from reversed(list(filtered_generator()))


def PreloadingGenerator(generator: Iterable['pywikibot.page.Page'],
                        groupsize: int = 50
                        ) -> Iterator['pywikibot.page.Page']:
    """
    Yield preloaded pages taken from another generator.

    :param generator: pages to iterate over
    :param groupsize: how many pages to preload at once
    """
    # pages may be on more than one site, for example if an interwiki
    # generator is used, so use a separate preloader for each site
    sites = {}  # type: PRELOAD_SITE_TYPE
    # build a list of pages for each site found in the iterator
    for page in generator:
        site = page.site
        sites.setdefault(site, []).append(page)

        groupsize = min(groupsize, site.maxlimit)
        if len(sites[site]) >= groupsize:
            # if this site is at the groupsize, process it
            group = sites.pop(site)
            yield from site.preloadpages(group, groupsize=groupsize)

    for site, pages in sites.items():
        # process any leftover sites that never reached the groupsize
        yield from site.preloadpages(pages, groupsize=groupsize)


def DequePreloadingGenerator(generator: Iterable['pywikibot.page.Page'],
                             groupsize: int = 50
                             ) -> Iterator['pywikibot.page.Page']:
    """Preload generator of type DequeGenerator."""
    assert isinstance(generator, DequeGenerator), \
        'generator must be a DequeGenerator object'

    while True:
        page_count = min(len(generator), groupsize)
        if not page_count:
            return

        yield from PreloadingGenerator(generator, page_count)


def PreloadingEntityGenerator(generator: Iterable['pywikibot.page.Page'],
                              groupsize: int = 50
                              ) -> Iterator['pywikibot.page.Page']:
    """
    Yield preloaded pages taken from another generator.

    Function basically is copied from above, but for Wikibase entities.

    :param generator: pages to iterate over
    :param groupsize: how many pages to preload at once
    """
    sites = {}  # type: PRELOAD_SITE_TYPE
    for page in generator:
        site = page.site
        sites.setdefault(site, []).append(page)
        if len(sites[site]) >= groupsize:
            # if this site is at the groupsize, process it
            group = sites.pop(site)
            repo = site.data_repository()
            yield from repo.preload_entities(group, groupsize)

    for site, pages in sites.items():
        # process any leftover sites that never reached the groupsize
        repo = site.data_repository()
        yield from repo.preload_entities(pages, groupsize)
