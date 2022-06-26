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
import calendar
import codecs
import datetime
import io
import itertools
import re
import sys
from collections import abc, namedtuple
from datetime import timedelta
from functools import partial
from http import HTTPStatus
from itertools import zip_longest
from typing import Any, Optional, Union
from urllib.parse import urlparse

from requests.exceptions import ReadTimeout

import pywikibot
from pywikibot import config, date, i18n, xmlreader
from pywikibot.backports import (
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    List,
    Pattern,
    Sequence,
    Set,
    Tuple,
    Type,
)
from pywikibot.bot import ShowingListOption
from pywikibot.comms import http
from pywikibot.data import api
from pywikibot.exceptions import (
    APIError,
    NoPageError,
    ServerError,
    UnknownExtensionError,
)
from pywikibot.proofreadpage import ProofreadPage
from pywikibot.tools import (
    deprecated,
    DequeGenerator,
    filter_unique,
    intersect_generators,
    itergroup,
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
                    The value may be a comma separated list of these values:

                        logevent,username,start,end

                    or for backward compatibility:

                        logevent,username,total

                    Note: 'start' is the most recent date and log events are
                    iterated from present to past. If 'start'' is not provided,
                    it means 'now'; if 'end' is not provided, it means 'since
                    the beginning'.

                    To use the default value, use an empty string.
                    You have options for every type of logs given by the
                    log event parameter which could be one of the following:

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
                    (Example : -sparqlendpoint:http://myserver.com/sparql)

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

                    Examples:

                    -ns:0,2,4
                    -ns:Help,MediaWiki

                    You may use a preleading "not" to exclude the namespace.

                    Examples:

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

                    P1=Q2 (property P1 must contain value Q2),
                    P3=Q4,P5=Q6,P6=Q7 (property P3 with value Q4 and
                    qualifiers: P5 with value Q6 and P6 with value Q7).
                    Value can be page ID, coordinate in format:
                    latitude,longitude[,precision] (all values are in decimal
                    degrees), year, or plain string.
                    The argument can be provided multiple times and the item
                    page will be returned only if all claims are present.
                    Argument can be also given as "-onlyif:expression".

-onlyifnot          A claim the page must not contain, otherwise the item won't
                    be returned.
                    For usage and examples, see -onlyif above.

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
"""

docuReplacements = {'&params;': parameterHelp}  # noqa: N816

HANDLER_RETURN_TYPE = Union[None, bool, Iterable['pywikibot.page.BasePage']]
PRELOAD_SITE_TYPE = Dict[pywikibot.site.BaseSite, List[pywikibot.page.Page]]

GEN_FACTORY_NAMESPACE_TYPE = Union[List[str],
                                   FrozenSet['pywikibot.site.Namespace']]
GEN_FACTORY_CLAIM_TYPE = List[Tuple[str, str, Dict[str, str], bool]]

OPT_SITE_TYPE = Optional['pywikibot.site.BaseSite']
OPT_TIMESTAMP_TYPE = Optional['pywikibot.Timestamp']
OPT_GENERATOR_TYPE = Optional[Iterable['pywikibot.page.Page']]

NAMESPACE_OR_INT_TYPE = Union[int, 'pywikibot.site.Namespace']
NAMESPACE_OR_STR_TYPE = Union[str, 'pywikibot.site.Namespace']

ITEM_CLAIM_FILTER_CLASS = Type['ItemClaimFilter']
REGEX_FILTER_CLASS = Type['RegexFilter']

PATTERN_STR_OR_SEQ_TYPE = Union[str, Pattern[str],
                                Sequence[str], Sequence[Pattern[str]]]

# if a bot uses GeneratorFactory, the module should include the line
#   docuReplacements = {'&params;': pywikibot.pagegenerators.parameterHelp}
# and include the marker &params; in the module's docstring
#
# We manually include it so the parameters show up in the auto-generated
# module documentation:

__doc__ = __doc__.replace('&params;', parameterHelp)


# This is the function that will be used to de-duplicate page iterators.
_filter_unique_pages = partial(
    filter_unique, key=lambda page: '{}:{}:{}'.format(*page._cmpkey()))


def _output_if(predicate: bool, msg: str) -> None:
    if predicate:
        pywikibot.output(msg)


class GeneratorFactory:

    """Process command line arguments and return appropriate page generator.

    This factory is responsible for processing command line arguments
    that are used by many scripts and that determine which pages to work on.

    .. note:: GeneratorFactory must be instantiated after global
       arguments are parsed except if site parameter is given.
    """

    def __init__(self, site: OPT_SITE_TYPE = None,
                 positional_arg_name: Optional[str] = None,
                 enabled_options: Optional[Iterable[str]] = None,
                 disabled_options: Optional[Iterable[str]] = None) -> None:
        """
        Initializer.

        :param site: Site for generator results
        :param positional_arg_name: generator to use for positional args,
            which do not begin with a hyphen
        :param enabled_options: only enable options given by this Iterable.
            This is priorized over disabled_options
        :param disabled_options: disable these given options and let them
            be handled by scripts options handler
        """
        self.gens = []  # type: List[Iterable['pywikibot.page.Page']]
        self._namespaces = []  # type: GEN_FACTORY_NAMESPACE_TYPE
        self.limit = None  # type: Optional[int]
        self.qualityfilter_list = []  # type: List[int]
        self.articlefilter_list = []  # type: List[str]
        self.articlenotfilter_list = []  # type: List[str]
        self.titlefilter_list = []  # type: List[str]
        self.titlenotfilter_list = []  # type: List[str]
        self.claimfilter_list = []  # type: GEN_FACTORY_CLAIM_TYPE
        self.catfilter_list = []  # type: List['pywikibot.Category']
        self.intersect = False
        self.subpage_max_depth = None  # type: Optional[int]
        self._site = site
        self._positional_arg_name = positional_arg_name
        self._sparql = None  # type: Optional[str]
        self.nopreload = False
        self._validate_options(enabled_options, disabled_options)

        self.is_preloading = None  # type: Optional[bool]
        """Return whether Page objects are preloaded. You may use this
        instance variable after :meth:`getCombinedGenerator` is called
        e.g.::

            gen_factory = GeneratorFactory()
            print(gen_factory.is_preloading)  # None
            gen = gen_factory.getCombinedGenerator()
            print(gen_factory.is_preloading)  # True or False

        Otherwise the value is undefined and gives None.

        .. versionadded:: 7.3
        """

    def _validate_options(self,
                          enable: Optional[Iterable[str]],
                          disable: Optional[Iterable[str]]) -> None:
        """Validate option restrictions."""
        msg = '{!r} is not a valid pagegenerators option to be '
        enable = enable or []
        disable = disable or []
        self.enabled_options = set(enable)
        self.disabled_options = set(disable)
        for opt in enable:
            if not hasattr(self, '_handle_' + opt):
                pywikibot.warning((msg + 'enabled').format(opt))
                self.enabled_options.remove(opt)
        for opt in disable:
            if not hasattr(self, '_handle_' + opt):
                pywikibot.warning((msg + 'disabled').format(opt))
                self.disabled_options.remove(opt)
        if self.enabled_options and self.disabled_options:
            pywikibot.warning('Ignoring disabled option because enabled '
                              'options are set.')
            self.disabled_options = set()

    @property
    def site(self) -> 'pywikibot.site.BaseSite':
        """
        Generator site.

        The generator site should not be accessed until after the global
        arguments have been handled, otherwise the default Site may be changed
        by global arguments, which will cause this cached value to be stale.

        :return: Site given to initializer, otherwise the default Site at the
            time this property is first accessed.
        """
        if self._site is None:
            self._site = pywikibot.Site()

        return self._site

    @property
    def namespaces(self) -> FrozenSet['pywikibot.site.Namespace']:
        """
        List of Namespace parameters.

        Converts int or string namespaces to Namespace objects and
        change the storage to immutable once it has been accessed.

        The resolving and validation of namespace command line arguments
        is performed in this method, as it depends on the site property
        which is lazy loaded to avoid being cached before the global
        arguments are handled.

        :return: namespaces selected using arguments
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if isinstance(self._namespaces, list):
            self._namespaces = frozenset(
                self.site.namespaces.resolve(self._namespaces))
        return self._namespaces

    def getCombinedGenerator(self,
                             gen: OPT_GENERATOR_TYPE = None,
                             preload: bool = False) -> OPT_GENERATOR_TYPE:
        """Return the combination of all accumulated generators.

        Only call this after all arguments have been parsed.

        .. versionchanged:: 7.3
           set the instance variable :attr:`is_preloading` to True or False.

        :param gen: Another generator to be combined with
        :param preload: preload pages using PreloadingGenerator
            unless self.nopreload is True
        """
        if gen:
            self.gens.insert(0, gen)

        for i, gen_item in enumerate(self.gens):
            if self.namespaces:
                if (isinstance(gen_item, api.QueryGenerator)
                        and gen_item.support_namespace()):
                    gen_item.set_namespace(self.namespaces)
                # QueryGenerator does not support namespace param.
                else:
                    self.gens[i] = NamespaceFilterPageGenerator(
                        gen_item, self.namespaces, self.site)

            if self.limit:
                try:
                    gen_item.set_maximum_items(self.limit)  # type: ignore[attr-defined]  # noqa: E501
                except AttributeError:
                    self.gens[i] = itertools.islice(gen_item, self.limit)

        if not self.gens:
            if any((self.titlefilter_list,
                    self.titlenotfilter_list,
                    self.articlefilter_list,
                    self.articlenotfilter_list,
                    self.claimfilter_list,
                    self.catfilter_list,
                    self.qualityfilter_list,
                    self.subpage_max_depth is not None)):
                pywikibot.warning('filter(s) specified but no generators.')
            return None

        if len(self.gens) == 1:
            dupfiltergen = self.gens[0]
            if hasattr(self, '_single_gen_filter_unique'):
                dupfiltergen = _filter_unique_pages(dupfiltergen)
            if self.intersect:
                pywikibot.warning(
                    '"-intersect" ignored as only one generator is specified.')
        elif self.intersect:
            # By definition no duplicates are possible.
            dupfiltergen = intersect_generators(*self.gens)
        else:
            dupfiltergen = _filter_unique_pages(itertools.chain(*self.gens))

        # Add on subpage filter generator
        if self.subpage_max_depth is not None:
            dupfiltergen = SubpageFilterGenerator(
                dupfiltergen, self.subpage_max_depth)

        if self.claimfilter_list:
            for claim in self.claimfilter_list:
                dupfiltergen = ItemClaimFilterPageGenerator(dupfiltergen,
                                                            claim[0], claim[1],
                                                            claim[2], claim[3])

        if self.qualityfilter_list:
            dupfiltergen = QualityFilterPageGenerator(
                dupfiltergen, self.qualityfilter_list)

        if self.titlefilter_list:
            dupfiltergen = RegexFilterPageGenerator(
                dupfiltergen, self.titlefilter_list)

        if self.titlenotfilter_list:
            dupfiltergen = RegexFilterPageGenerator(
                dupfiltergen, self.titlenotfilter_list, 'none')

        if self.catfilter_list:
            dupfiltergen = CategoryFilterPageGenerator(
                dupfiltergen, self.catfilter_list)

        self.is_preloading = not self.nopreload and bool(
            preload or self.articlefilter_list or self.articlenotfilter_list)

        if self.is_preloading:
            if isinstance(dupfiltergen, DequeGenerator):
                dupfiltergen = DequePreloadingGenerator(dupfiltergen)
            else:
                dupfiltergen = PreloadingGenerator(dupfiltergen)

        if self.articlefilter_list:
            dupfiltergen = RegexBodyFilterPageGenerator(
                dupfiltergen, self.articlefilter_list)

        if self.articlenotfilter_list:
            dupfiltergen = RegexBodyFilterPageGenerator(
                dupfiltergen, self.articlenotfilter_list, 'none')

        return dupfiltergen

    def getCategory(self, category: str
                    ) -> Tuple['pywikibot.Category', Optional[str]]:
        """
        Return Category and start as defined by category.

        :param category: category name with start parameter
        """
        if not category:
            category = i18n.input('pywikibot-enter-category-name')
        category = category.replace('#', '|')

        startfrom = None  # type: Optional[str]
        category, _, startfrom = category.partition('|')

        if not startfrom:
            startfrom = None

        # Insert "Category:" before category name to avoid parsing problems in
        # Link.parse() when categoryname contains ":";
        # Part before ":" might be interpreted as an interwiki prefix
        prefix = category.split(':', 1)[0]  # whole word if ":" not present
        if prefix not in self.site.namespaces[14]:
            category = '{}:{}'.format(
                self.site.namespace(14), category)
        cat = pywikibot.Category(pywikibot.Link(category,
                                                source=self.site,
                                                default_namespace=14))
        return cat, startfrom

    def getCategoryGen(self, category: str,
                       recurse: Union[int, bool] = False,
                       content: bool = False,
                       gen_func: Optional[Callable] = None) -> Any:
        """
        Return generator based on Category defined by category and gen_func.

        :param category: category name with start parameter
        :param recurse: if not False or 0, also iterate articles in
            subcategories. If an int, limit recursion to this number of
            levels. (Example: recurse=1 will iterate articles in first-level
            subcats, but no deeper.)
        :param content: if True, retrieve the content of the current version
            of each page (default False)
        """
        if gen_func is None:
            raise ValueError('getCategoryGen requires a gen_func argument')

        cat, startfrom = self.getCategory(category)

        return gen_func(cat,
                        start=startfrom,
                        recurse=recurse,
                        content=content)

    @staticmethod
    def _parse_log_events(logtype: str,
                          user: Optional[str] = None,
                          start: Optional[str] = None,
                          end: Optional[str] = None
                          ) -> Optional[Iterator['pywikibot.page.Page']]:
        """
        Parse the -logevent argument information.

        :param logtype: A valid logtype
        :param user: A username associated to the log events. Ignored if
            empty string or None.
        :param start: Timestamp to start listing from. This must be
            convertible into Timestamp matching '%Y%m%d%H%M%S'.
            For backward compatibility if the value does not have 8
            digits, this can also be a str (castable to int), used as
            the total amount of pages that should be returned.
        :param end: Timestamp to end listing at. This must be
            convertible into a Timestamp matching '%Y%m%d%H%M%S'.
        :return: The generator or None if invalid 'start/total' or 'end' value.
        """
        def parse_start(start: Optional[str]
                        ) -> Tuple[Optional[str], Optional[int]]:
            """Parse start and return (start, total)."""
            if start is None:
                return None, None

            if len(start) >= 8:
                return pywikibot.Timestamp.fromtimestampformat(start), None

            return None, int(start)

        start = start or None  # because start might be an empty string
        try:
            start, total = parse_start(start)
            assert total is None or total > 0
        except ValueError as err:
            pywikibot.error(
                '{}. Start parameter has wrong format!'.format(err))
            return None
        except AssertionError:
            pywikibot.error('Total number of log ({}) events must be a '
                            'positive int.'.format(start))
            return None

        try:
            end = pywikibot.Timestamp.fromtimestampformat(end)
        except ValueError as err:
            pywikibot.error(
                '{}. End parameter has wrong format!'.format(err))
            return None
        except TypeError:  # end is None
            pass

        if start or end:
            pywikibot.output('Fetching log events in range: {} - {}.'
                             .format(end or 'beginning of time',
                                     start or 'now'))

        # 'user or None', because user might be an empty string when
        # 'foo,,bar' was used.
        return LogeventsPageGenerator(logtype, user or None, total=total,
                                      start=start, end=end)

    def _handle_filelinks(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-filelinks` argument."""
        if not value:
            value = i18n.input('pywikibot-enter-file-links-processing')
        if not value.startswith(self.site.namespace(6) + ':'):
            value = 'Image:' + value
        file_page = pywikibot.FilePage(self.site, value)
        return file_page.using_pages()

    def _handle_linter(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-linter` argument."""
        if not self.site.has_extension('Linter'):
            raise UnknownExtensionError(
                '-linter needs a site with Linter extension.')
        cats = self.site.siteinfo.get('linter')  # Get linter categories.
        valid_cats = [c for _list in cats.values() for c in _list]

        value = value or ''
        lint_from = None  # type: Optional[str]
        cat, _, lint_from = value.partition('/')
        lint_from = lint_from or None

        def show_available_categories(cats: Dict[
                                      str, Sequence['pywikibot.Category']]
                                      ) -> None:
            _i = ' ' * 4
            _2i = 2 * _i
            txt = 'Available categories of lint errors:\n'
            for prio, _list in cats.items():
                txt += '{indent}{prio}\n'.format(indent=_i, prio=prio)
                txt += ''.join(
                    '{indent}{cat}\n'.format(indent=_2i, cat=c) for c in _list)
            pywikibot.output(txt)

        if cat == 'show':  # Display categories of lint errors.
            show_available_categories(cats)
            sys.exit(0)

        if not cat:
            lint_cats = valid_cats
        elif cat in ['low', 'medium', 'high']:
            lint_cats = cats[cat]
        else:
            lint_cats = cat.split(',')
            assert set(lint_cats) <= set(valid_cats), \
                'Invalid category of lint errors: {}'.format(cat)

        return self.site.linter_pages(
            lint_categories='|'.join(lint_cats), namespaces=self.namespaces,
            lint_from=lint_from)

    def _handle_querypage(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-querypage` argument."""
        if value is None:  # Display special pages.
            pages = self.site._paraminfo.parameter('query+querypage',
                                                   'page')
            pages = sorted(pages['type'])
            limit = self.site._paraminfo.parameter('query+querypage',
                                                   'limit')

            max_w = max(len(p) for p in pages[::2]) + 4
            txt = 'Available special pages:\n'
            for a, b in zip_longest(pages[::2], pages[1::2], fillvalue=''):
                txt += '    {a:<{max_w}}{b}\n'.format(a=a, b=b, max_w=max_w)
            txt += ('\nMaximum number of pages to return is {max} '
                    '({highmax} for bots).\n'.format_map(limit))
            pywikibot.output(txt)
            sys.exit(0)

        return self.site.querypage(value)

    def _handle_url(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-url` argument."""
        if not value:
            value = pywikibot.input('Please enter the URL:')
        return TextIOPageGenerator(value, site=self.site)

    def _handle_unusedfiles(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-unusedfiles` argument."""
        return self.site.unusedfiles(total=_int_none(value))

    def _handle_lonelypages(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-lonelypages` argument."""
        return self.site.lonelypages(total=_int_none(value))

    def _handle_unwatched(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-unwatched` argument."""
        return self.site.unwatchedpage(total=_int_none(value))

    def _handle_wantedpages(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-wantedpages` argument."""
        return self.site.wantedpages(total=_int_none(value))

    def _handle_wantedfiles(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-wantedfiles` argument."""
        return self.site.wantedfiles(total=_int_none(value))

    def _handle_wantedtemplates(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-wantedtemplates` argument."""
        return self.site.wantedtemplates(total=_int_none(value))

    def _handle_wantedcategories(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-wantedcategories` argument."""
        return self.site.wantedcategories(total=_int_none(value))

    def _handle_property(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-property` argument."""
        if not value:
            question = 'Which property name to be used?'
            value = pywikibot.input(question + ' (List [?])')
            pnames = self.site.get_property_names()
            # also use the default by <enter> key
            if value == '?' or value not in pnames:
                _, value = pywikibot.input_choice(question,
                                                  ShowingListOption(pnames))
        return self.site.pages_with_property(value)

    def _handle_usercontribs(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-usercontribs` argument."""
        self._single_gen_filter_unique = True
        return UserContributionsGenerator(
            value, site=self.site, _filter_unique=None)

    def _handle_withoutinterwiki(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-withoutinterwiki` argument."""
        return self.site.withoutinterwiki(total=_int_none(value))

    def _handle_interwiki(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-interwiki` argument."""
        if not value:
            value = i18n.input('pywikibot-enter-page-processing')
        page = pywikibot.Page(pywikibot.Link(value, self.site))
        return LanguageLinksPageGenerator(page)

    def _handle_randomredirect(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-randomredirect` argument."""
        # partial workaround for bug T119940
        # to use -namespace/ns with -randomredirect, -ns must be given
        # before -randomredirect
        # otherwise default namespace is 0
        namespaces = self.namespaces or 0
        return self.site.randompages(total=_int_none(value),
                                     namespaces=namespaces, redirects=True)

    def _handle_random(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-random` argument."""
        # partial workaround for bug T119940
        # to use -namespace/ns with -random, -ns must be given
        # before -random
        # otherwise default namespace is 0
        namespaces = self.namespaces or 0
        return self.site.randompages(total=_int_none(value),
                                     namespaces=namespaces)

    def _handle_recentchanges(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-recentchanges` argument."""
        rcstart = None
        rcend = None
        rctag = None
        total = None
        params = value.split(',') if value else []
        if params and not params[0].isdigit():
            rctag = params.pop(0)
        if len(params) > 2:
            raise ValueError('More than two parameters passed.')
        if len(params) == 2:
            offset = float(params[0])
            duration = float(params[1])
            if offset < 0 or duration < 0:
                raise ValueError('Negative valued parameters passed.')
            ts_time = self.site.server_time()
            rcstart = ts_time - timedelta(minutes=offset)
            rcend = rcstart - timedelta(minutes=duration)
        elif len(params) == 1:
            total = int(params[0])
        self._single_gen_filter_unique = True
        return RecentChangesPageGenerator(
            namespaces=self.namespaces, total=total, start=rcstart, end=rcend,
            site=self.site, tag=rctag)

    def _handle_liverecentchanges(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-liverecentchanges` argument."""
        self.nopreload = True
        return LiveRCPageGenerator(site=self.site, total=_int_none(value))

    def _handle_file(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-file` argument."""
        if not value:
            value = pywikibot.input('Please enter the local file name:')
        return TextIOPageGenerator(value, site=self.site)

    def _handle_namespaces(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-namespaces` argument."""
        if isinstance(self._namespaces, frozenset):
            raise RuntimeError('-namespace/ns option must be provided before '
                               '-newpages/-random/-randomredirect/-linter')
        if not value:
            value = pywikibot.input('What namespace are you filtering on?')
        NOT_KEY = 'not:'
        if value.startswith(NOT_KEY):
            value = value[len(NOT_KEY):]
            resolve = self.site.namespaces.resolve
            not_ns = set(resolve(value.split(',')))
            if not self._namespaces:
                self._namespaces = list(
                    set(self.site.namespaces.values()) - not_ns)
            else:
                self._namespaces = list(
                    set(resolve(self._namespaces)) - not_ns)
        else:
            self._namespaces += value.split(',')
        return True

    _handle_ns = _handle_namespaces
    _handle_namespace = _handle_namespaces

    def _handle_limit(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-limit` argument."""
        if not value:
            value = pywikibot.input('What is the limit value?')
        self.limit = _int_none(value)
        return True

    def _handle_category(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-category` argument."""
        return self.getCategoryGen(
            value, recurse=False, gen_func=CategorizedPageGenerator)

    _handle_cat = _handle_category

    def _handle_catr(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-catr` argument."""
        return self.getCategoryGen(
            value, recurse=True, gen_func=CategorizedPageGenerator)

    def _handle_subcats(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-subcats` argument."""
        return self.getCategoryGen(
            value, recurse=False, gen_func=SubCategoriesPageGenerator)

    def _handle_subcatsr(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-subcatsr` argument."""
        return self.getCategoryGen(
            value, recurse=True, gen_func=SubCategoriesPageGenerator)

    def _handle_catfilter(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-catfilter` argument."""
        cat, _ = self.getCategory(value)
        self.catfilter_list.append(cat)
        return True

    def _handle_page(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-page` argument."""
        if not value:
            value = pywikibot.input('What page do you want to use?')
        return [pywikibot.Page(pywikibot.Link(value, self.site))]

    def _handle_pageid(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-pageid` argument."""
        if not value:
            value = pywikibot.input('What pageid do you want to use?')
        return self.site.load_pages_from_pageids(value)

    def _handle_uncatfiles(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-uncatfiles` argument."""
        return self.site.uncategorizedimages()

    def _handle_uncatcat(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-uncatcat` argument."""
        return self.site.uncategorizedcategories()

    def _handle_uncat(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-uncat` argument."""
        return self.site.uncategorizedpages()

    def _handle_ref(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-ref` argument."""
        if not value:
            value = pywikibot.input(
                'Links to which page should be processed?')
        page = pywikibot.Page(pywikibot.Link(value, self.site))
        return page.getReferences()

    def _handle_links(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-links` argument."""
        if not value:
            value = pywikibot.input(
                'Links from which page should be processed?')
        page = pywikibot.Page(pywikibot.Link(value, self.site))
        return page.linkedPages()

    def _handle_weblink(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-weblink` argument."""
        if not value:
            value = pywikibot.input(
                'Pages with which weblink should be processed?')
        return self.site.exturlusage(value)

    def _handle_transcludes(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-transcludes` argument."""
        if not value:
            value = pywikibot.input(
                'Pages that transclude which page should be processed?')
        page = pywikibot.Page(pywikibot.Link(value,
                                             default_namespace=10,
                                             source=self.site))
        return page.getReferences(only_template_inclusion=True)

    def _handle_start(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-start` argument."""
        if not value:
            value = '!'
        firstpagelink = pywikibot.Link(value, self.site)
        return self.site.allpages(
            start=firstpagelink.title, namespace=firstpagelink.namespace,
            filterredir=False)

    def _handle_prefixindex(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-prefixindex` argument."""
        if not value:
            value = pywikibot.input('What page names are you looking for?')
        return PrefixingPageGenerator(prefix=value, site=self.site)

    def _handle_newimages(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-newimages` argument."""
        return NewimagesPageGenerator(total=_int_none(value), site=self.site)

    def _handle_newpages(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-newpages` argument."""
        # partial workaround for bug T69249
        # to use -namespace/ns with -newpages, -ns must be given
        # before -newpages
        # otherwise default namespace is 0
        namespaces = self.namespaces or 0
        return NewpagesPageGenerator(
            namespaces=namespaces, total=_int_none(value), site=self.site)

    def _handle_unconnectedpages(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-unconnectedpages` argument."""
        return self.site.unconnected_pages(total=_int_none(value))

    def _handle_imagesused(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-imagesused` argument."""
        if not value:
            value = pywikibot.input(
                'Images on which page should be processed?')
        page = pywikibot.Page(pywikibot.Link(value, self.site))
        return page.imagelinks()

    def _handle_searchitem(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-searchitem` argument."""
        if not value:
            value = pywikibot.input('Text to look for:')
        params = value.split(':')
        value = params[-1]
        lang = params[0] if len(params) == 2 else None
        return WikibaseSearchItemPageGenerator(
            value, language=lang, site=self.site)

    def _handle_search(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-search` argument."""
        if not value:
            value = pywikibot.input('What do you want to search for?')
        # In order to be useful, all namespaces are required
        return self.site.search(value, namespaces=[])

    @staticmethod
    def _handle_google(value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-google` argument."""
        return GoogleSearchPageGenerator(value)

    def _handle_titleregex(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-titleregex` argument."""
        if not value:
            value = pywikibot.input(
                'What page names are you looking for?')
        self.titlefilter_list.append(value)
        return True

    def _handle_titleregexnot(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-titleregexnot` argument."""
        if not value:
            value = pywikibot.input(
                'All pages except which ones?')
        self.titlenotfilter_list.append(value)
        return True

    def _handle_grep(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-grep` argument."""
        if not value:
            value = pywikibot.input('Which pattern do you want to grep?')
        self.articlefilter_list.append(value)
        return True

    def _handle_grepnot(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-grepnot` argument."""
        if not value:
            value = pywikibot.input('Which pattern do you want to skip?')
        self.articlenotfilter_list.append(value)
        return True

    def _handle_ql(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-ql` argument."""
        if not self.site.has_extension('ProofreadPage'):
            raise UnknownExtensionError(
                'Ql filtering needs a site with ProofreadPage extension.')
        int_values = [int(_) for _ in value.split(',')]
        if min(int_values) < 0 or max(int_values) > 4:  # Invalid input ql.
            valid_ql_list = [
                '{}: {}'.format(*i)
                for i in self.site.proofread_levels.items()]
            valid_ql = ', '.join(valid_ql_list)
            pywikibot.warning('Acceptable values for -ql are:\n    {}'
                              .format(valid_ql))
        self.qualityfilter_list = int_values
        return True

    def _handle_onlyif(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-onlyif` argument."""
        return self._onlyif_onlyifnot_handler(value, False)

    def _handle_onlyifnot(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-onlyifnot` argument."""
        return self._onlyif_onlyifnot_handler(value, True)

    def _onlyif_onlyifnot_handler(self, value: str, ifnot: bool
                                  ) -> HANDLER_RETURN_TYPE:
        """Handle `-onlyif` and `-onlyifnot` arguments."""
        if not value:
            value = pywikibot.input('Which claim do you want to filter?')
        p = re.compile(r'(?<!\\),')  # Match "," only if there no "\" before
        temp = []  # Array to store split argument
        for arg in p.split(value):
            key, value = arg.replace(r'\,', ',').split('=', 1)
            temp.append((key, value))
        self.claimfilter_list.append(
            (temp[0][0], temp[0][1], dict(temp[1:]), ifnot))
        return True

    def _handle_sparqlendpoint(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-sparqlendpoint` argument."""
        if not value:
            value = pywikibot.input('SPARQL endpoint:')
        self._sparql = value
        return True

    def _handle_sparql(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-sparql` argument."""
        if not value:
            value = pywikibot.input('SPARQL query:')
        return WikidataSPARQLPageGenerator(
            value, site=self.site, endpoint=self._sparql)

    def _handle_mysqlquery(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-mysqlquery` argument."""
        if not value:
            value = pywikibot.input('Mysql query string:')
        return MySQLPageGenerator(value, site=self.site)

    def _handle_intersect(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-intersect` argument."""
        self.intersect = True
        return True

    def _handle_subpage(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-subpage` argument."""
        if not value:
            value = pywikibot.input(
                'Maximum subpage depth:')
        self.subpage_max_depth = int(value)
        return True

    def _handle_logevents(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-logevents` argument."""
        params = value.split(',')
        if params[0] not in self.site.logtypes:
            raise NotImplementedError(
                'Invalid -logevents parameter "{}"'.format(params[0]))
        return self._parse_log_events(*params)

    def handle_args(self, args: Iterable[str]) -> List[str]:
        """Handle command line arguments and return the rest as a list.

        .. versionadded:: 6.0
        .. versionchanged:: 7.3
           Prioritize -namespaces options to solve problems with several
           generators like -newpages/-random/-randomredirect/-linter
        """
        ordered_args = [arg for arg in args
                        if arg.startswith(('-ns', '-namespace'))]
        ordered_args += [arg for arg in args
                         if not arg.startswith(('-ns', '-namespace'))]
        return [arg for arg in ordered_args if not self.handle_arg(arg)]

    def handle_arg(self, arg: str) -> bool:
        """Parse one argument at a time.

        If it is recognized as an argument that specifies a generator, a
        generator is created and added to the accumulation list, and the
        function returns true. Otherwise, it returns false, so that caller
        can try parsing the argument. Call getCombinedGenerator() after all
        arguments have been parsed to get the final output generator.

        .. versionadded:: 6.0
           renamed from ``handleArg``

        :param arg: Pywikibot argument consisting of -name:value
        :return: True if the argument supplied was recognised by the factory
        """
        value = None  # type: Optional[str]

        if not arg.startswith('-') and self._positional_arg_name:
            value = arg
            arg = '-' + self._positional_arg_name
        else:
            arg, _, value = arg.partition(':')

        if not value:
            value = None

        opt = arg[1:]
        if opt in self.disabled_options:
            return False

        if self.enabled_options and opt not in self.enabled_options:
            return False

        handler = getattr(self, '_handle_' + opt, None)
        if not handler:
            return False

        handler_result = handler(value)
        if isinstance(handler_result, bool):
            return handler_result
        if handler_result:
            self.gens.append(handler_result)
            return True

        return False


def _int_none(v: Optional[str]) -> Optional[int]:
    """Return None if v is None or '' else return int(v)."""
    return None if not v else int(v)


def AllpagesPageGenerator(
    start: str = '!',
    namespace: int = 0,
    includeredirects: Union[str, bool] = True,
    site: OPT_SITE_TYPE = None,
    total: Optional[int] = None, content: bool = False
) -> Iterable['pywikibot.page.Page']:
    """Iterate Page objects for all titles in a single namespace.

    If includeredirects is False, redirects are not included. If
    includeredirects equals the string 'only', only redirects are added.

    :param total: Maximum number of pages to retrieve in total
    :param content: If True, load current version of each page (default False)
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()

    filterredir = None  # type: Optional[bool]
    if not includeredirects:
        filterredir = False
    elif includeredirects == 'only':
        filterredir = True

    return site.allpages(start=start, namespace=namespace,
                         filterredir=filterredir, total=total, content=content)


def PrefixingPageGenerator(prefix: str,
                           namespace: NAMESPACE_OR_INT_TYPE = None,
                           includeredirects: Union[None, bool, str] = True,
                           site: OPT_SITE_TYPE = None,
                           total: Optional[int] = None,
                           content: bool = False
                           ) -> Iterable['pywikibot.page.Page']:
    """
    Prefixed Page generator.

    :param prefix: The prefix of the pages.
    :param namespace: Namespace to retrieve pages from
    :param includeredirects: If includeredirects is None, False or an empty
        string, redirects will not be found. If includeredirects equals the
        string 'only', only redirects will be found. Otherwise redirects will
        be included.
    :param site: Site for generator results.
    :param total: Maximum number of pages to retrieve in total
    :param content: If True, load current version of each page (default False)
    :return: a generator that yields Page objects
    """
    if site is None:
        site = pywikibot.Site()

    prefixlink = pywikibot.Link(prefix, site)
    if namespace is None:
        namespace = prefixlink.namespace
    title = prefixlink.title

    filterredir = None  # type: Optional[bool]
    if not includeredirects:
        filterredir = False
    elif includeredirects == 'only':
        filterredir = True

    return site.allpages(prefix=title, namespace=namespace,
                         filterredir=filterredir, total=total, content=content)


def LogeventsPageGenerator(logtype: Optional[str] = None,
                           user: Optional[str] = None,
                           site: OPT_SITE_TYPE = None,
                           namespace: Optional[int] = None,
                           total: Optional[int] = None,
                           start: OPT_TIMESTAMP_TYPE = None,
                           end: OPT_TIMESTAMP_TYPE = None,
                           reverse: bool = False
                           ) -> Iterator['pywikibot.page.Page']:
    """
    Generate Pages for specified modes of logevents.

    :param logtype: Mode of logs to retrieve
    :param user: User of logs retrieved
    :param site: Site for generator results
    :param namespace: Namespace to retrieve logs from
    :param total: Maximum number of pages to retrieve in total
    :param start: Timestamp to start listing from
    :param end: Timestamp to end listing at
    :param reverse: if True, start with oldest changes (default: newest)
    """
    if site is None:
        site = pywikibot.Site()
    for entry in site.logevents(total=total, logtype=logtype, user=user,
                                namespace=namespace, start=start, end=end,
                                reverse=reverse):
        try:
            yield entry.page()
        except KeyError as e:
            pywikibot.warning('LogeventsPageGenerator: '
                              'failed to load page for {!r}; skipping'
                              .format(entry.data))
            pywikibot.error(e)


def NewpagesPageGenerator(site: OPT_SITE_TYPE = None,
                          namespaces: Tuple[int] = (0, ),
                          total: Optional[int] = None
                          ) -> Iterator['pywikibot.page.Page']:
    """
    Iterate Page objects for all new titles in a single namespace.

    :param site: Site for generator results.
    :param namespace: namespace to retrieve pages from
    :param total: Maxmium number of pages to retrieve in total
    """
    # API does not (yet) have a newpages function, so this tries to duplicate
    # it by filtering the recentchanges output
    # defaults to namespace 0 because that's how Special:Newpages defaults
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.newpages(namespaces=namespaces,
                                              total=total, returndict=True))


def RecentChangesPageGenerator(site: OPT_SITE_TYPE = None,
                               _filter_unique: Optional[Callable[
                                   [Iterable['pywikibot.page.Page']],
                                   Iterable['pywikibot.page.Page']]] = None,
                               **kwargs: Any
                               ) -> Iterable['pywikibot.page.Page']:
    """
    Generate pages that are in the recent changes list, including duplicates.

    For parameters refer pywikibot.site.recentchanges

    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()

    gen = site.recentchanges(**kwargs)
    gen.request['rcprop'] = 'title'
    gen = (pywikibot.Page(site, rc['title'])
           for rc in gen if rc['type'] != 'log' or 'title' in rc)

    if _filter_unique:
        gen = _filter_unique(gen)
    return gen


def UnconnectedPageGenerator(
    site: OPT_SITE_TYPE = None,
    total: Optional[int] = None
) -> Iterable['pywikibot.page.Page']:
    """Iterate Page objects for all unconnected pages to a Wikibase repository.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    if not site.data_repository():
        raise ValueError('The given site does not have Wikibase repository.')
    return site.unconnected_pages(total=total)


def FileLinksGenerator(
    referredFilePage: 'pywikibot.page.FilePage',
    total: Optional[int] = None,
    content: bool = False
) -> Iterable['pywikibot.page.Page']:
    """Yield Pages on which referredFilePage file is displayed."""
    return referredFilePage.using_pages(total=total, content=content)


def ImagesPageGenerator(
    pageWithImages: 'pywikibot.page.Page',
    total: Optional[int] = None,
    content: bool = False
) -> Iterable['pywikibot.page.Page']:
    """Yield FilePages displayed on pageWithImages."""
    return pageWithImages.imagelinks(total=total, content=content)


def InterwikiPageGenerator(page: 'pywikibot.page.Page'
                           ) -> Iterable['pywikibot.page.Page']:
    """Iterate over all interwiki (non-language) links on a page."""
    return (pywikibot.Page(link) for link in page.interwiki())


def LanguageLinksPageGenerator(page: 'pywikibot.page.Page',
                               total: Optional[int] = None
                               ) -> Iterable['pywikibot.page.Page']:
    """Iterate over all interwiki language links on a page."""
    return (pywikibot.Page(link) for link in page.iterlanglinks(total=total))


def CategorizedPageGenerator(category: pywikibot.page.Category,
                             recurse: Union[int, bool] = False,
                             start: Optional[str] = None,
                             total: Optional[int] = None,
                             content: bool = False,
                             namespaces: Optional[Sequence[int]] = None
                             ) -> Iterable['pywikibot.page.Page']:
    """Yield all pages in a specific category.

    :param recurse: if not False or 0, also iterate articles in
        subcategories. If an int, limit recursion to this number of
        levels. (Example: recurse=1 will iterate articles in first-level
        subcats, but no deeper.)
    :param start: if provided, only generate pages >= this title
        lexically
    :param total: iterate no more than this number of pages in
        total (at all levels)
    :param content: if True, retrieve the content of the current version
        of each page (default False)
    """
    kwargs = {
        'content': content,
        'namespaces': namespaces,
        'recurse': recurse,
        'startprefix': start,
        'total': total,
    }
    yield from category.articles(**kwargs)


def SubCategoriesPageGenerator(category: 'pywikibot.page.Category',
                               recurse: Union[int, bool] = False,
                               start: Optional[str] = None,
                               total: Optional[int] = None,
                               content: bool = False
                               ) -> Iterable['pywikibot.page.Page']:
    """Yield all subcategories in a specific category.

    :param recurse: if not False or 0, also iterate articles in
        subcategories. If an int, limit recursion to this number of
        levels. (Example: recurse=1 will iterate articles in first-level
        subcats, but no deeper.)
    :param start: if provided, only generate pages >= this title
        lexically
    :param total: iterate no more than this number of pages in
        total (at all levels)
    :param content: if True, retrieve the content of the current version
        of each page (default False)
    """
    # TODO: page generator could be modified to use cmstartsortkey ...
    for s in category.subcategories(recurse=recurse,
                                    total=total, content=content):
        if start is None or s.title(with_ns=False) >= start:
            yield s


def LinkedPageGenerator(
    linkingPage: 'pywikibot.page.Page',
    total: Optional[int] = None,
    content: bool = False
) -> Iterable['pywikibot.page.Page']:
    """Yield all pages linked from a specific page.

    See :py:obj:`pywikibot.page.BasePage.linkedPages` for details.

    :param linkingPage: the page that links to the pages we want
    :param total: the total number of pages to iterate
    :param content: if True, retrieve the current content of each linked page
    :return: a generator that yields Page objects of pages linked to
        linkingPage
    """
    return linkingPage.linkedPages(total=total, content=content)


def _yield_titles(f: Union[codecs.StreamReaderWriter, io.StringIO],
                  site: pywikibot.site.BaseSite
                  ) -> Iterable['pywikibot.page.Page']:
    """Yield page titles from a text stream.

    :param f: text stream object
    :param site: Site for generator results.
    :return: a generator that yields Page objects of pages with titles in text
        stream
    """
    linkmatch = None
    for linkmatch in pywikibot.link_regex.finditer(f.read()):
        # If the link is in interwiki format, the Page object may reside
        # on a different Site than the default.
        # This makes it possible to work on different wikis using a single
        # text file, but also could be dangerous because you might
        # inadvertently change pages on another wiki!
        yield pywikibot.Page(pywikibot.Link(linkmatch.group('title'),
                                            site))
    if linkmatch is not None:
        return

    f.seek(0)
    for title in f:
        title = title.strip()
        if '|' in title:
            title = title[:title.index('|')]
        if title:
            yield pywikibot.Page(site, title)


def TextIOPageGenerator(source: Optional[str] = None,
                        site: OPT_SITE_TYPE = None
                        ) -> Iterable['pywikibot.page.Page']:
    """Iterate pages from a list in a text file or on a webpage.

    The text source must contain page links between double-square-brackets or,
    alternatively, separated by newlines. The generator will yield each
    corresponding Page object.

    :param source: the file path or URL that should be read. If no name is
                     given, the generator prompts the user.
    :param site: Site for generator results.
    """
    if source is None:
        source = pywikibot.input('Please enter the filename / URL:')
    if site is None:
        site = pywikibot.Site()
    # If source cannot be parsed as an HTTP URL, treat as local file
    if not urlparse(source).netloc:
        with codecs.open(source, 'r', config.textfile_encoding) as local_file:
            yield from _yield_titles(local_file, site)
    # Else, fetch page (page should return text in same format as that expected
    # in filename, i.e. pages separated by newlines or pages enclosed in double
    # brackets
    else:
        with io.StringIO(http.fetch(source).text) as f:
            yield from _yield_titles(f, site)


def PagesFromTitlesGenerator(iterable: Iterable[str],
                             site: OPT_SITE_TYPE = None
                             ) -> Iterable['pywikibot.page.Page']:
    """
    Generate pages from the titles (strings) yielded by iterable.

    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    for title in iterable:
        if not isinstance(title, str):
            break
        yield pywikibot.Page(pywikibot.Link(title, site))


def PagesFromPageidGenerator(
    pageids: Iterable[str],
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Return a page generator from pageids.

    Pages are iterated in the same order than in the underlying pageids.
    Pageids are filtered and only one page is returned in case of
    duplicate pageid.

    :param pageids: an iterable that returns pageids, or a comma-separated
                    string of pageids (e.g. '945097,1483753,956608')
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()

    return site.load_pages_from_pageids(pageids)


def UserContributionsGenerator(username: str,
                               namespaces: Optional[List[int]] = None,
                               site: OPT_SITE_TYPE = None,
                               total: Optional[int] = None,
                               _filter_unique: Optional[Callable[
                                   [Iterable['pywikibot.page.Page']],
                                   Iterable['pywikibot.page.Page']]] =
                               _filter_unique_pages
                               ) -> Iterator['pywikibot.page.Page']:
    """Yield unique pages edited by user:username.

    :param total: Maximum number of pages to retrieve in total
    :param namespaces: list of namespace numbers to fetch contribs from
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()

    user = pywikibot.User(site, username)
    if not (user.isAnonymous() or user.isRegistered()):
        pywikibot.warning('User "{}" does not exist on site "{}".'
                          .format(user.username, site))

    gen = (contrib[0] for contrib in user.contributions(
        namespaces=namespaces, total=total))
    if _filter_unique:
        return _filter_unique(gen)
    return gen


def NamespaceFilterPageGenerator(generator: Iterable['pywikibot.page.Page'],
                                 namespaces: Union[
                                     FrozenSet['pywikibot.site.Namespace'],
                                     NAMESPACE_OR_STR_TYPE,
                                     Sequence[NAMESPACE_OR_STR_TYPE]],
                                 site: OPT_SITE_TYPE = None
                                 ) -> Iterator['pywikibot.page.Page']:
    """
    A generator yielding pages from another generator in given namespaces.

    If a site is provided, the namespaces are validated using the namespaces
    of that site, otherwise the namespaces are validated using the default
    site.

    NOTE: API-based generators that have a "namespaces" parameter perform
    namespace filtering more efficiently than this generator.

    :param namespaces: list of namespace identifiers to limit results
    :param site: Site for generator results; mandatory if
        namespaces contains namespace names. Defaults to the default site.
    :raises KeyError: a namespace identifier was not resolved
    :raises TypeError: a namespace identifier has an inappropriate
        type such as NoneType or bool, or more than one namespace
        if the API module does not support multiple namespaces
    """
    # As site was only required if the namespaces contain strings, don't
    # attempt to use the config selected site unless the initial attempt
    # at resolving the namespaces fails.
    if site is None:
        site = pywikibot.Site()
    try:
        namespaces = site.namespaces.resolve(namespaces)
    except KeyError as e:
        pywikibot.log('Failed resolving namespaces:')
        pywikibot.error(e)
        raise

    return (page for page in generator if page.namespace() in namespaces)


def PageTitleFilterPageGenerator(generator: Iterable['pywikibot.page.Page'],
                                 ignore_list: Dict[str, Dict[str, str]]
                                 ) -> Iterator['pywikibot.page.Page']:
    """
    Yield only those pages are not listed in the ignore list.

    :param ignore_list: family names are mapped to dictionaries in which
        language codes are mapped to lists of page titles. Each title must
        be a valid regex as they are compared using :py:obj:`re.search`.
    """
    def is_ignored(page: 'pywikibot.page.Page') -> bool:
        try:
            site_ig_list = ignore_list[page.site.family.name][page.site.code]
        except KeyError:
            return False
        return any(re.search(ig, page.title()) for ig in site_ig_list)

    for page in generator:
        if not is_ignored(page):
            yield page
            continue

        if config.verbose_output:
            pywikibot.output('Ignoring page {}'.format(page.title()))


def RedirectFilterPageGenerator(generator: Iterable['pywikibot.page.Page'],
                                no_redirects: bool = True,
                                show_filtered: bool = False
                                ) -> Iterator['pywikibot.page.Page']:
    """
    Yield pages from another generator that are redirects or not.

    :param no_redirects: Exclude redirects if True, else only include
        redirects.
    :param show_filtered: Output a message for each page not yielded
    """
    fmt = '{page} is {what} redirect page. Skipping.'
    what = 'a' if no_redirects else 'not a'

    for page in generator or []:
        is_redirect = page.isRedirectPage()
        if bool(no_redirects) != bool(is_redirect):  # xor
            yield page
            continue

        if show_filtered:
            pywikibot.output(fmt.format(what=what, page=page))


class ItemClaimFilter:

    """Item claim filter."""

    page_classes = {
        True: pywikibot.PropertyPage,
        False: pywikibot.ItemPage,
    }

    @classmethod
    def __filter_match(cls: ITEM_CLAIM_FILTER_CLASS,
                       page: 'pywikibot.page.BasePage',
                       prop: str,
                       claim: str,
                       qualifiers: Dict[str, str]) -> bool:
        """
        Return true if the page contains the claim given.

        :param page: the page to check
        :return: true if page contains the claim, false otherwise
        """
        if not isinstance(page, pywikibot.page.WikibasePage):  # T175151
            try:
                assert page.site.property_namespace
                assert page.site.item_namespace
                key = page.namespace() == page.site.property_namespace
                page_cls = cls.page_classes[key]
                page = page_cls(page.site, page.title(with_ns=False))
            except (AttributeError, AssertionError):
                try:
                    page = pywikibot.ItemPage.fromPage(page)
                except NoPageError:
                    return False

        def match_qualifiers(page_claim: 'pywikibot.page.Claim',
                             qualifiers: Dict[str, str]) -> bool:
            return all(page_claim.has_qualifier(prop, val)
                       for prop, val in qualifiers.items())

        page_claims = page.get()['claims'].get(prop, [])
        return any(
            p_cl.target_equals(claim) and match_qualifiers(p_cl, qualifiers)
            for p_cl in page_claims)

    @classmethod
    def filter(cls: ITEM_CLAIM_FILTER_CLASS,
               generator: Iterable['pywikibot.page.Page'],
               prop: str,
               claim: str,
               qualifiers: Optional[Dict[str, str]] = None,
               negate: bool = False) -> Iterator['pywikibot.page.Page']:
        """
        Yield all ItemPages which contain certain claim in a property.

        :param prop: property id to check
        :param claim: value of the property to check. Can be exact value (for
            instance, ItemPage instance) or a string (e.g. 'Q37470').
        :param qualifiers: dict of qualifiers that must be present, or None if
            qualifiers are irrelevant
        :param negate: true if pages that do *not* contain specified claim
            should be yielded, false otherwise
        """
        qualifiers = qualifiers or {}
        for page in generator:
            if cls.__filter_match(page, prop, claim, qualifiers) is not negate:
                yield page


# name the generator methods
ItemClaimFilterPageGenerator = ItemClaimFilter.filter


def SubpageFilterGenerator(generator: Iterable['pywikibot.page.Page'],
                           max_depth: int = 0,
                           show_filtered: bool = False
                           ) -> Iterable['pywikibot.page.Page']:
    """
    Generator which filters out subpages based on depth.

    It looks at the namespace of each page and checks if that namespace has
    subpages enabled. If so, pages with forward slashes ('/') are excluded.

    :param generator: A generator object
    :param max_depth: Max depth of subpages to yield, at least zero
    :param show_filtered: Output a message for each page not yielded
    """
    assert max_depth >= 0, 'Max subpage depth must be at least 0'

    for page in generator:
        if page.depth <= max_depth:
            yield page
        else:
            if show_filtered:
                pywikibot.output(
                    'Page {} is a subpage that is too deep. Skipping.'
                    .format(page))


class RegexFilter:

    """Regex filter."""

    @classmethod
    def __filter_match(cls: REGEX_FILTER_CLASS, regex: Sequence[Pattern[str]],
                       string: str, quantifier: str) -> bool:
        """Return True if string matches precompiled regex list.

        :param quantifier: a qualifier
        """
        if quantifier == 'all':
            match = all(r.search(string) for r in regex)
        else:
            match = any(r.search(string) for r in regex)
        return (quantifier == 'none') ^ match

    @classmethod
    def __precompile(cls: REGEX_FILTER_CLASS, regex: PATTERN_STR_OR_SEQ_TYPE,
                     flag: int) -> List[Pattern[str]]:
        """Precompile the regex list if needed."""
        if isinstance(regex, list):
            regex_list = regex
        elif isinstance(regex, tuple):
            regex_list = list(regex)
        else:
            regex_list = [regex]

        for i, item in enumerate(regex_list):
            if isinstance(item, str):
                regex_list[i] = re.compile(item, flag)

        return regex_list

    @classmethod
    def titlefilter(cls: REGEX_FILTER_CLASS,
                    generator: Iterable['pywikibot.page.Page'],
                    regex: PATTERN_STR_OR_SEQ_TYPE,
                    quantifier: str = 'any',
                    ignore_namespace: bool = True
                    ) -> Iterator['pywikibot.page.Page']:
        """Yield pages from another generator whose title matches regex.

        Uses regex option re.IGNORECASE depending on the quantifier parameter.

        If ignore_namespace is False, the whole page title is compared.
        NOTE: if you want to check for a match at the beginning of the title,
        you have to start the regex with "^"

        :param generator: another generator
        :param regex: a regex which should match the page title
        :param quantifier: must be one of the following values:
            'all' - yields page if title is matched by all regexes
            'any' - yields page if title is matched by any regexes
            'none' - yields page if title is NOT matched by any regexes
        :param ignore_namespace: ignore the namespace when matching the title
        :return: return a page depending on the matching parameters
        """
        # for backwards compatibility with compat for inverse parameter
        if quantifier is False:
            quantifier = 'any'
        elif quantifier is True:
            quantifier = 'none'
        reg = cls.__precompile(regex, re.I)
        for page in generator:
            title = page.title(with_ns=not ignore_namespace)
            if cls.__filter_match(reg, title, quantifier):
                yield page

    @classmethod
    def contentfilter(cls: REGEX_FILTER_CLASS,
                      generator: Iterable['pywikibot.page.Page'],
                      regex: PATTERN_STR_OR_SEQ_TYPE,
                      quantifier: str = 'any'
                      ) -> Iterator['pywikibot.page.Page']:
        """Yield pages from another generator whose body matches regex.

        Uses regex option re.IGNORECASE depending on the quantifier parameter.

        For parameters see titlefilter above.
        """
        reg = cls.__precompile(regex, re.IGNORECASE | re.DOTALL)
        return (page for page in generator
                if cls.__filter_match(reg, page.text, quantifier))


def QualityFilterPageGenerator(generator: Iterable['pywikibot.page.Page'],
                               quality: List[int]
                               ) -> Iterator['pywikibot.page.Page']:
    """
    Wrap a generator to filter pages according to quality levels.

    This is possible only for pages with content_model 'proofread-page'.
    In all the other cases, no filter is applied.

    :param generator: A generator object
    :param quality: proofread-page quality levels (valid range 0-4)
    """
    for page in generator:
        if page.namespace() == page.site.proofread_page_ns:
            page = ProofreadPage(page)
            if page.quality_level in quality:
                yield page
        else:
            yield page


def CategoryFilterPageGenerator(generator: Iterable['pywikibot.page.Page'],
                                category_list:
                                    Sequence['pywikibot.page.Category']
                                ) -> Iterator['pywikibot.page.Page']:
    """
    Wrap a generator to filter pages by categories specified.

    :param generator: A generator object
    :param category_list: categories used to filter generated pages
    """
    for page in generator:
        if all(x in page.categories() for x in category_list):
            yield page


# name the generator methods
RegexFilterPageGenerator = RegexFilter.titlefilter
RegexBodyFilterPageGenerator = RegexFilter.contentfilter


def EdittimeFilterPageGenerator(
    generator: Iterable['pywikibot.page.Page'],
    last_edit_start: Optional[datetime.datetime] = None,
    last_edit_end: Optional[datetime.datetime] = None,
    first_edit_start: Optional[datetime.datetime] = None,
    first_edit_end: Optional[datetime.datetime] = None,
    show_filtered: bool = False
) -> Iterator['pywikibot.page.Page']:
    """
    Wrap a generator to filter pages outside last or first edit range.

    :param generator: A generator object
    :param last_edit_start: Only yield pages last edited after this time
    :param last_edit_end: Only yield pages last edited before this time
    :param first_edit_start: Only yield pages first edited after this time
    :param first_edit_end: Only yield pages first edited before this time
    :param show_filtered: Output a message for each page not yielded
    """
    Edit = namedtuple('Edit', ['do_edit', 'edit_start', 'edit_end'])

    def to_be_yielded(edit: Edit,
                      page: 'pywikibot.page.Page',
                      rev: 'pywikibot.page.Revision',
                      show_filtered: bool) -> bool:
        if not edit.do_edit:
            return True

        edit_time = rev.timestamp  # type: ignore[attr-defined]

        msg = '{prefix} edit on {page} was on {time}.\n' \
              'Too {{when}}. Skipping.' \
              .format(prefix=type(edit).__name__,
                      page=page,
                      time=edit_time.isoformat())

        if edit_time < edit.edit_start:
            _output_if(show_filtered, msg.format(when='old'))
            return False

        if edit_time > edit.edit_end:
            _output_if(show_filtered, msg.format(when='recent'))
            return False

        return True

    latest_edit = Edit(last_edit_start or last_edit_end,
                       last_edit_start or datetime.datetime.min,
                       last_edit_end or datetime.datetime.max)

    first_edit = Edit(first_edit_start or first_edit_end,
                      first_edit_start or datetime.datetime.min,
                      first_edit_end or datetime.datetime.max)

    for page in generator or []:
        yield_for_last = to_be_yielded(latest_edit, page,
                                       page.latest_revision, show_filtered)
        yield_for_first = to_be_yielded(first_edit, page, page.oldest_revision,
                                        show_filtered)

        if yield_for_last and yield_for_first:
            yield page


def UserEditFilterGenerator(generator: Iterable['pywikibot.page.Page'],
                            username: str,
                            timestamp: Union[None, str,
                                             datetime.datetime] = None,
                            skip: bool = False,
                            max_revision_depth: Optional[int] = None,
                            show_filtered: bool = False
                            ) -> Iterator['pywikibot.page.Page']:
    """
    Generator which will yield Pages modified by username.

    It only looks at the last editors given by max_revision_depth.
    If timestamp is set in MediaWiki format JJJJMMDDhhmmss, older edits are
    ignored.
    If skip is set, pages edited by the given user are ignored otherwise only
    pages edited by this user are given back.

    :param generator: A generator object
    :param username: user name which edited the page
    :param timestamp: ignore edits which are older than this timestamp
    :param skip: Ignore pages edited by the given user
    :param max_revision_depth: It only looks at the last editors given by
        max_revision_depth
    :param show_filtered: Output a message for each page not yielded
    """
    if isinstance(timestamp, str):
        ts = pywikibot.Timestamp.fromtimestampformat(timestamp)
    else:
        ts = timestamp

    for page in generator:
        contribs = page.contributors(total=max_revision_depth, endtime=ts)
        if bool(contribs[username]) is not bool(skip):  # xor operation
            yield page
        elif show_filtered:
            pywikibot.output('Skipping {}'.format(page.title(as_link=True)))


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


def NewimagesPageGenerator(total: Optional[int] = None,
                           site: OPT_SITE_TYPE = None
                           ) -> Iterator['pywikibot.page.Page']:
    """
    New file generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return (entry.page()
            for entry in site.logevents(logtype='upload', total=total))


def WikibaseItemGenerator(gen: Iterable['pywikibot.page.Page']
                          ) -> Iterator['pywikibot.page.ItemPage']:
    """
    A wrapper generator used to yield Wikibase items of another generator.

    :param gen: Generator to wrap.
    :return: Wrapped generator
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


def WikibaseItemFilterPageGenerator(generator: Iterable['pywikibot.page.Page'],
                                    has_item: bool = True,
                                    show_filtered: bool = False
                                    ) -> Iterator['pywikibot.page.Page']:
    """
    A wrapper generator used to exclude if page has a Wikibase item or not.

    :param generator: Generator to wrap.
    :param has_item: Exclude pages without an item if True, or only
        include pages without an item if False
    :param show_filtered: Output a message for each page not yielded
    :return: Wrapped generator
    """
    why = "doesn't" if has_item else 'has'
    msg = '{{page}} {why} a wikidata item. Skipping.'.format(why=why)

    for page in generator or []:
        try:
            page_item = pywikibot.ItemPage.fromPage(page, lazy_load=False)
        except NoPageError:
            page_item = None

        to_be_skipped = bool(page_item) != has_item
        if to_be_skipped:
            _output_if(show_filtered, msg.format(page=page))
            continue

        yield page


def AncientPagesPageGenerator(
    total: int = 100,
    site: OPT_SITE_TYPE = None
) -> Iterator['pywikibot.page.Page']:
    """
    Ancient page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.ancientpages(total=total))


def UnusedFilesGenerator(
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.FilePage']:
    """Unused files generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.unusedfiles(total=total)


def WithoutInterwikiPageGenerator(
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Page lacking interwikis generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.withoutinterwiki(total=total)


def UnCategorizedCategoryGenerator(
    total: Optional[int] = 100,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.Category']:
    """Uncategorized category generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedcategories(total=total)


def UnCategorizedImageGenerator(
    total: int = 100,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.FilePage']:
    """Uncategorized file generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedimages(total=total)


def UnCategorizedPageGenerator(
    total: int = 100,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Uncategorized page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedpages(total=total)


def UnCategorizedTemplateGenerator(
    total: int = 100,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Uncategorized template generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedtemplates(total=total)


def LonelyPagesPageGenerator(
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Lonely page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.lonelypages(total=total)


def UnwatchedPagesPageGenerator(
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Unwatched page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.unwatchedpages(total=total)


def page_with_property_generator(
    name: str,
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Special:PagesWithProperty page generator.

    :param name: Property name of pages to be retrieved
    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.pages_with_property(name, total=total)


def WantedPagesPageGenerator(
    total: int = 100,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Wanted page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.wantedpages(total=total)


def DeadendPagesPageGenerator(
    total: int = 100,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Dead-end page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.deadendpages(total=total)


def LongPagesPageGenerator(total: int = 100,
                           site: OPT_SITE_TYPE = None
                           ) -> Iterator['pywikibot.page.Page']:
    """
    Long page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.longpages(total=total))


def ShortPagesPageGenerator(total: int = 100,
                            site: OPT_SITE_TYPE = None
                            ) -> Iterator['pywikibot.page.Page']:
    """
    Short page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.shortpages(total=total))


def RandomPageGenerator(
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None,
    namespaces: Optional[Sequence[NAMESPACE_OR_STR_TYPE]] = None
) -> Iterable['pywikibot.page.Page']:
    """Random page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.randompages(total=total, namespaces=namespaces)


def RandomRedirectPageGenerator(
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None,
    namespaces: Optional[
        Sequence[NAMESPACE_OR_STR_TYPE]] = None
) -> Iterable['pywikibot.page.Page']:
    """Random redirect generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.randompages(total=total, namespaces=namespaces,
                            redirects=True)


def LinksearchPageGenerator(
    url: str,
    namespaces: Optional[List[int]] = None,
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None,
    protocol: Optional[str] = None
) -> Iterable['pywikibot.page.Page']:
    """Yield all pages that link to a certain URL.

    :param url: The URL to search for (with ot without the protocol prefix);
            this may include a '*' as a wildcard, only at the start of the
            hostname
    :param namespaces: list of namespace numbers to fetch contribs from
    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results
    :param protocol: Protocol to search for, likely http or https, http by
        default. Full list shown on Special:LinkSearch wikipage
    """
    if site is None:
        site = pywikibot.Site()
    return site.exturlusage(url, namespaces=namespaces, protocol=protocol,
                            total=total, content=False)


def SearchPageGenerator(
    query: str,
    total: Optional[int] = None,
    namespaces: Optional[Sequence[NAMESPACE_OR_STR_TYPE]] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Yield pages from the MediaWiki internal search engine.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.search(query, total=total, namespaces=namespaces)


def LiveRCPageGenerator(site: OPT_SITE_TYPE = None,
                        total: Optional[int] = None
                        ) -> Iterator['pywikibot.page.Page']:
    """
    Yield pages from a socket.io RC stream.

    Generates pages based on the EventStreams Server-Sent-Event (SSE) recent
    changes stream.
    The Page objects will have an extra property ._rcinfo containing the
    literal rc data. This can be used to e.g. filter only new pages. See
    `pywikibot.comms.eventstreams.rc_listener` for details on the .rcinfo
    format.

    :param site: site to return recent changes for
    :param total: the maximum number of changes to return
    """
    if site is None:
        site = pywikibot.Site()

    from pywikibot.comms.eventstreams import site_rc_listener

    for entry in site_rc_listener(site, total=total):
        # The title in a log entry may have been suppressed
        if 'title' not in entry and entry['type'] == 'log':
            continue
        page = pywikibot.Page(site, entry['title'], entry['namespace'])
        page._rcinfo = entry
        yield page


# following classes just ported from version 1 without revision; not tested


class GoogleSearchPageGenerator(Iterable['pywikibot.page.Page']):
    """
    Page generator using Google search results.

    To use this generator, you need to install the package 'google':

        :py:obj:`https://pypi.org/project/google`

    This package has been available since 2010, hosted on GitHub
    since 2012, and provided by PyPI since 2013.

    As there are concerns about Google's Terms of Service, this
    generator prints a warning for each query.
    """

    def __init__(self, query: Optional[str] = None,
                 site: OPT_SITE_TYPE = None) -> None:
        """
        Initializer.

        :param site: Site for generator results.
        """
        self.query = query or pywikibot.input('Please enter the search query:')
        if site is None:
            site = pywikibot.Site()
        self.site = site
        self._google_query = None

    def queryGoogle(self, query: str) -> Iterator[Any]:
        """
        Perform a query using python package 'google'.

        The terms of service as at June 2014 give two conditions that
        may apply to use of search:

            1. Don't access [Google Services] using a method other than
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
            pywikibot.error('generator GoogleSearchPageGenerator '
                            "depends on package 'google'.\n"
                            'To install, please run: pip install google.')
            sys.exit(1)
        pywikibot.warning('Please read http://www.google.com/accounts/TOS')
        yield from google.search(query)

    def __iter__(self):
        """Iterate results.

        Google contains links in the format:
        https://de.wikipedia.org/wiki/en:Foobar
        """
        # restrict query to local site
        localQuery = '{} site:{}'.format(self.query, self.site.hostname())
        base = 'http://{}{}'.format(self.site.hostname(),
                                    self.site.articlepath)
        pattern = base.replace('{}', '(.+)')
        for url in self.queryGoogle(localQuery):
            m = re.search(pattern, url)
            if m:
                page = pywikibot.Page(pywikibot.Link(m.group(1), self.site))
                if page.site == self.site:
                    yield page


def MySQLPageGenerator(query: str, site: OPT_SITE_TYPE = None,
                       verbose: Optional[bool] = None
                       ) -> Iterator['pywikibot.page.Page']:
    """
    Yield a list of pages based on a MySQL query.

    The query should return two columns, page namespace and page title pairs
    from some table. An example query that yields all ns0 pages might look
    like::

        SELECT
         page_namespace,
         page_title
        FROM page
        WHERE page_namespace = 0;

    .. seealso:: :manpage:`MySQL`

    :param query: MySQL query to execute
    :param site: Site object
    :param verbose: if True, print query to be executed;
        if None, config.verbose_output will be used.
    :return: generator which yields pywikibot.Page
    """
    from pywikibot.data import mysql

    if site is None:
        site = pywikibot.Site()

    row_gen = mysql.mysql_query(query,
                                dbname=site.dbName(),
                                verbose=verbose)

    for row in row_gen:
        namespace_number, page_name = row
        page_name = page_name.decode(site.encoding())
        page = pywikibot.Page(site, page_name, ns=int(namespace_number))
        yield page


class XMLDumpPageGenerator(abc.Iterator):  # type: ignore[type-arg]
    """Xml generator that yields Page objects.

    .. versionadded:: 7.2
       the `content` parameter

    :param filename: filename of XML dump
    :param start: skip entries below that value
    :param namespaces: namespace filter
    :param site: current site for the generator
    :param text_predicate: a callable with entry.text as parameter and boolean
        as result to indicate the generator should return the page or not
    :param content: If True, assign old page content to Page.text

    :ivar skipping: True if start parameter is given, else False
    :ivar parser: holds the xmlreader.XmlDump parse method
    """

    def __init__(self, filename: str, start: Optional[str] = None,
                 namespaces: Union[
                     None, NAMESPACE_OR_STR_TYPE,
                     Sequence[NAMESPACE_OR_STR_TYPE]] = None,
                 site: OPT_SITE_TYPE = None,
                 text_predicate: Optional[Callable[[str], bool]] = None,
                 content=False) -> None:
        """Initializer."""
        self.text_predicate = text_predicate
        self.content = content
        self.skipping = bool(start)

        self.start = None  # type: Optional[str]
        if start is not None and self.skipping:
            self.start = start.replace('_', ' ')

        self.site = site or pywikibot.Site()
        if not namespaces:
            self.namespaces = self.site.namespaces
        else:
            self.namespaces = self.site.namespaces.resolve(namespaces)
        dump = xmlreader.XmlDump(filename, on_error=pywikibot.error)
        self.parser = dump.parse()

    def __next__(self) -> 'pywikibot.page.Page':
        """Get next Page."""
        while True:
            entry = next(self.parser)
            if self.skipping:
                if entry.title < self.start:
                    continue
                self.skipping = False
            page = pywikibot.Page(self.site, entry.title)
            if page.namespace() not in self.namespaces:
                continue
            if not self.text_predicate or self.text_predicate(entry.text):
                if self.content:
                    page.text = entry.text
                return page


@deprecated('XMLDumpPageGenerator with content=True parameter', since='7.2.0')
class XMLDumpOldPageGenerator(XMLDumpPageGenerator):

    """Xml generator that yields Page objects with old text loaded.

    .. deprecated:: 7.2
       :class:`XMLDumpPageGenerator` with `content` parameter should be
       used instead
    """

    def __init__(self, *args, **kwargs):
        """Initializer."""
        super().__init__(*args, **kwargs, content=True)


def YearPageGenerator(start: int = 1, end: int = 2050,
                      site: OPT_SITE_TYPE = None
                      ) -> Iterator['pywikibot.page.Page']:
    """
    Year page generator.

    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    pywikibot.output('Starting with year {}'.format(start))
    for i in range(start, end + 1):
        if i % 100 == 0:
            pywikibot.output('Preparing {}...'.format(i))
        # There is no year 0
        if i != 0:
            current_year = date.formatYear(site.lang, i)
            yield pywikibot.Page(pywikibot.Link(current_year, site))


def DayPageGenerator(start_month: int = 1, end_month: int = 12,
                     site: OPT_SITE_TYPE = None, year: int = 2000
                     ) -> Iterator['pywikibot.page.Page']:
    """
    Day page generator.

    :param site: Site for generator results.
    :param year: considering leap year.
    """
    if site is None:
        site = pywikibot.Site()
    lang = site.lang
    firstPage = pywikibot.Page(site, date.format_date(start_month, 1, lang))
    pywikibot.output('Starting with {}'.format(firstPage.title(as_link=True)))
    for month in range(start_month, end_month + 1):
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            yield pywikibot.Page(
                pywikibot.Link(date.format_date(month, day, lang), site))


def WikidataPageFromItemGenerator(gen: Iterable['pywikibot.page.ItemPage'],
                                  site: 'pywikibot.site.BaseSite'
                                  ) -> Iterator['pywikibot.page.Page']:
    """Generate pages from site based on sitelinks of item pages.

    :param gen: generator of :py:obj:`pywikibot.ItemPage`
    :param site: Site for generator results.
    """
    repo = site.data_repository()
    for sublist in itergroup(gen, 50):
        req = {'ids': [item.id for item in sublist],
               'sitefilter': site.dbName(),
               'action': 'wbgetentities',
               'props': 'sitelinks'}

        wbrequest = repo.simple_request(**req)
        wbdata = wbrequest.submit()
        entities = (item for item in wbdata['entities'].values() if
                    'sitelinks' in item and site.dbName() in item['sitelinks'])
        sitelinks = (item['sitelinks'][site.dbName()]['title']
                     for item in entities)
        for sitelink in sitelinks:
            yield pywikibot.Page(site, sitelink)


def WikidataSPARQLPageGenerator(query: str,
                                site: OPT_SITE_TYPE = None,
                                item_name: str = 'item',
                                endpoint: Optional[str] = None,
                                entity_url: Optional[str] = None,
                                result_type: Any = set
                                ) -> Iterator['pywikibot.page.Page']:
    """Generate pages that result from the given SPARQL query.

    :param query: the SPARQL query string.
    :param site: Site for generator results.
    :param item_name: name of the item in the SPARQL query
    :param endpoint: SPARQL endpoint URL
    :param entity_url: URL prefix for any entities returned in a query.
    :param result_type: type of the iterable in which
             SPARQL results are stored (default set)
    """
    from pywikibot.data import sparql

    if site is None:
        site = pywikibot.Site()
    repo = site.data_repository()
    dependencies = {'endpoint': endpoint, 'entity_url': entity_url}
    if not endpoint or not entity_url:
        dependencies['repo'] = repo
    query_object = sparql.SparqlQuery(**dependencies)  # type: ignore[arg-type]
    data = query_object.get_items(query,
                                  item_name=item_name,
                                  result_type=result_type)
    entities = (repo.get_entity_for_entity_id(entity) for entity in data)
    if isinstance(site, pywikibot.site.DataSite):
        return entities

    return WikidataPageFromItemGenerator(entities, site)


def WikibaseSearchItemPageGenerator(text: str,
                                    language: Optional[str] = None,
                                    total: Optional[int] = None,
                                    site: OPT_SITE_TYPE = None
                                    ) -> Iterator['pywikibot.page.ItemPage']:
    """
    Generate pages that contain the provided text.

    :param text: Text to look for.
    :param language: Code of the language to search in. If not specified,
        value from pywikibot.config.data_lang is used.
    :param total: Maximum number of pages to retrieve in total, or None in
        case of no limit.
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    if language is None:
        language = site.lang
    repo = site.data_repository()

    data = repo.search_entities(text, language, total=total)
    return (pywikibot.ItemPage(repo, item['id']) for item in data)


class PetScanPageGenerator:
    """Queries PetScan to generate pages.

    .. seealso:: https://petscan.wmflabs.org/
    .. versionadded:: 3.0
    """

    def __init__(self, categories: Sequence[str],
                 subset_combination: bool = True,
                 namespaces: Optional[Sequence[NAMESPACE_OR_STR_TYPE]] = None,
                 site: OPT_SITE_TYPE = None,
                 extra_options: Optional[Dict[Any, Any]] = None) -> None:
        """
        Initializer.

        :param categories: List of category names to retrieve pages from
        :param subset_combination: Combination mode.
            If True, returns the intersection of the results of the categories,
            else returns the union of the results of the categories
        :param namespaces: List of namespaces to search in
            (default is None, meaning all namespaces)
        :param site: Site to operate on
            (default is the default site from the user config)
        :param extra_options: Dictionary of extra options to use (optional)
        """
        if site is None:
            site = pywikibot.Site()

        self.site = site
        self.opts = self.buildQuery(categories, subset_combination,
                                    namespaces, extra_options)

    def buildQuery(self, categories: Sequence[str], subset_combination: bool,
                   namespaces: Optional[Sequence[NAMESPACE_OR_STR_TYPE]],
                   extra_options: Optional[Dict[Any, Any]]) -> Dict[str, Any]:
        """
        Get the querystring options to query PetScan.

        :param categories: List of categories (as strings)
        :param subset_combination: Combination mode.
            If True, returns the intersection of the results of the categories,
            else returns the union of the results of the categories
        :param namespaces: List of namespaces to search in
        :param extra_options: Dictionary of extra options to use
        :return: Dictionary of querystring parameters to use in the query
        """
        extra_options = extra_options or {}

        query = {
            'language': self.site.code,
            'project': self.site.hostname().split('.')[-2],
            'combination': 'subset' if subset_combination else 'union',
            'categories': '\r\n'.join(categories),
            'format': 'json',
            'doit': ''
        }

        if namespaces:
            for namespace in namespaces:
                query['ns[{}]'.format(int(namespace))] = 1

        query_final = query.copy()
        query_final.update(extra_options)

        return query_final

    def query(self) -> Iterator[Dict[str, Any]]:
        """Query PetScan.

        .. versionchanged:: 7.4
           raises :class:`APIError` if query returns an error message.

        :raises ServerError: Either ReadTimeout or server status error
        :raises APIError: error response from petscan
        """
        url = 'https://petscan.wmflabs.org'

        try:
            req = http.fetch(url, params=self.opts)
        except ReadTimeout:
            raise ServerError('received ReadTimeout from {}'.format(url))

        server_err = HTTPStatus.INTERNAL_SERVER_ERROR
        if server_err <= req.status_code < server_err + 100:
            raise ServerError(
                'received {} status from {}'.format(req.status_code, req.url))

        data = req.json()
        if 'error' in data:
            raise APIError('Petscan', data['error'], **self.opts)

        raw_pages = data['*'][0]['a']['*']
        yield from raw_pages

    def __iter__(self) -> Iterator['pywikibot.page.Page']:
        for raw_page in self.query():
            page = pywikibot.Page(self.site, raw_page['title'],
                                  int(raw_page['namespace']))
            yield page
