# -*- coding: utf-8 -*-
"""
This module offers a wide variety of page generators.

A page generator is an
object that is iterable (see http://legacy.python.org/dev/peps/pep-0255/ ) and
that yields page objects on which other scripts can then work.

Pagegenerators.py cannot be run as script. For testing purposes listpages.py
can be used instead, to print page titles to standard output.

These parameters are supported to specify which pages titles to print:

&params;
"""
#
# (C) Pywikibot team, 2008-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import calendar
import codecs
import datetime
import itertools
import json
import re
import sys

from datetime import timedelta
from functools import partial
from requests.exceptions import ReadTimeout
from warnings import warn

import pywikibot

from pywikibot.tools import (
    deprecated,
    deprecated_args,
    DequeGenerator,
    filter_unique,
    intersect_generators,
    issue_deprecation_warning,
    IteratorNextMixin,
    itergroup,
    ModuleDeprecationWrapper,
    redirect_func,
)

from pywikibot import date, config, i18n, xmlreader
from pywikibot.bot import ShowingListOption
from pywikibot.comms import http
from pywikibot.exceptions import (
    ArgumentDeprecationWarning,
    ServerError,
    UnknownExtension,
)
from pywikibot.proofreadpage import ProofreadPage
from pywikibot.tools import PY2, UnicodeType

if not PY2:
    from itertools import zip_longest
else:
    from itertools import izip_longest as zip_longest

_logger = 'pagegenerators'

# ported from version 1 for backwards-compatibility
# most of these functions just wrap a Site or Page method that returns
# a generator

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
                    WHERE page_namespace = 0" and treats
                    the resulting pages. See
                    https://www.mediawiki.org/wiki/Manual:Pywikibot/MySQL
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
                    see https://www.mediawiki.org/wiki/API:Querypage.
                    (tip: use -limit:n to fetch only n pages).

                    -querypage shows special pages available.


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

                    If used with -newpages/-random/-randomredirect/linter
                    generators, -namespace/ns must be provided before
                    -newpages/-random/-randomredirect/linter.
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


class GeneratorFactory(object):

    """Process command line arguments and return appropriate page generator.

    This factory is responsible for processing command line arguments
    that are used by many scripts and that determine which pages to work on.
    """

    def __init__(self, site=None, positional_arg_name=None):
        """
        Initializer.

        @param site: Site for generator results.
        @type site: L{pywikibot.site.BaseSite}
        @param positional_arg_name: generator to use for positional args,
            which do not begin with a hyphen
        @type positional_arg_name: basestring
        """
        self.gens = []
        self._namespaces = []
        self.limit = None
        self.qualityfilter_list = []
        self.articlefilter_list = []
        self.titlefilter_list = []
        self.titlenotfilter_list = []
        self.claimfilter_list = []
        self.catfilter_list = []
        self.intersect = False
        self.subpage_max_depth = None
        self._site = site
        self._positional_arg_name = positional_arg_name
        self._sparql = None
        self.nopreload = False

    @property
    def site(self):
        """
        Generator site.

        The generator site should not be accessed until after the global
        arguments have been handled, otherwise the default Site may be changed
        by global arguments, which will cause this cached value to be stale.

        @return: Site given to initializer, otherwise the default Site at the
            time this property is first accessed.
        @rtype: L{pywikibot.site.BaseSite}
        """
        if not self._site:
            self._site = pywikibot.Site()
        return self._site

    @property
    def namespaces(self):
        """
        List of Namespace parameters.

        Converts int or string namespaces to Namespace objects and
        change the storage to immutable once it has been accessed.

        The resolving and validation of namespace command line arguments
        is performed in this method, as it depends on the site property
        which is lazy loaded to avoid being cached before the global
        arguments are handled.

        @return: namespaces selected using arguments
        @rtype: list of Namespace
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if isinstance(self._namespaces, list):
            self._namespaces = frozenset(
                self.site.namespaces.resolve(self._namespaces))
        return self._namespaces

    def getCombinedGenerator(self, gen=None, preload=False):
        """Return the combination of all accumulated generators.

        Only call this after all arguments have been parsed.

        @param gen: Another generator to be combined with
        @type gen: iterator
        @param preload: preload pages using PreloadingGenerator
            unless self.nopreload is True
        @type preload: bool
        """
        if gen:
            self.gens.insert(0, gen)

        for i in range(len(self.gens)):
            if self.namespaces:
                if (isinstance(self.gens[i], pywikibot.data.api.QueryGenerator)
                        and self.gens[i].support_namespace()):
                    self.gens[i].set_namespace(self.namespaces)
                # QueryGenerator does not support namespace param.
                else:
                    self.gens[i] = NamespaceFilterPageGenerator(
                        self.gens[i], self.namespaces, self.site)

            if self.limit:
                try:
                    self.gens[i].set_maximum_items(self.limit)
                except AttributeError:
                    self.gens[i] = itertools.islice(self.gens[i], self.limit)

        if not self.gens:
            if any((self.titlefilter_list,
                    self.titlenotfilter_list,
                    self.articlefilter_list,
                    self.claimfilter_list,
                    self.catfilter_list,
                    self.qualityfilter_list,
                    self.subpage_max_depth is not None)):
                pywikibot.warning('filter(s) specified but no generators.')
            return None

        elif len(self.gens) == 1:
            dupfiltergen = self.gens[0]
            if hasattr(self, '_single_gen_filter_unique'):
                dupfiltergen = _filter_unique_pages(dupfiltergen)
            if self.intersect:
                pywikibot.warning(
                    '"-intersect" ignored as only one generator is specified.')
        elif self.intersect:
            # By definition no duplicates are possible.
            dupfiltergen = intersect_generators(self.gens)
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
                dupfiltergen, self.catfilter_list, self.site)

        if (preload or self.articlefilter_list) and not self.nopreload:
            if isinstance(dupfiltergen, DequeGenerator):
                dupfiltergen = DequePreloadingGenerator(dupfiltergen)
            else:
                dupfiltergen = PreloadingGenerator(dupfiltergen)

        if self.articlefilter_list:
            dupfiltergen = RegexBodyFilterPageGenerator(
                dupfiltergen, self.articlefilter_list)

        return dupfiltergen

    @deprecated_args(arg='category')
    def getCategory(self, category):
        """
        Return Category and start as defined by category.

        @param category: category name with start parameter
        @type category: str
        @rtype: tuple
        """
        if category and category.startswith('-'):
            categoryname = category.partition(':')[2]
            issue_deprecation_warning(
                'The usage of "{0}" as actual parameter of '
                'pagegenerators.getCategory'.format(category),
                categoryname, depth=3,
                warning_class=ArgumentDeprecationWarning,
                since='20141019')
        else:
            categoryname = category

        if not categoryname:
            categoryname = i18n.input(
                'pywikibot-enter-category-name',
                fallback_prompt='Please enter the category name:')
        categoryname = categoryname.replace('#', '|')

        categoryname, sep, startfrom = categoryname.partition('|')
        if not startfrom:
            startfrom = None

        # Insert Category: before category name to avoid parsing problems in
        # Link.parse() when categoryname contains ":";
        # Part before ":" might be interpreted as an interwiki prefix
        prefix = categoryname.split(':', 1)[0]  # whole word if ":" not present
        if prefix not in self.site.namespaces[14]:
            categoryname = '{0}:{1}'.format(
                self.site.namespace(14), categoryname)
        cat = pywikibot.Category(pywikibot.Link(categoryname,
                                                source=self.site,
                                                default_namespace=14))
        return cat, startfrom

    @deprecated_args(arg='category')
    def getCategoryGen(self, category, recurse=False, content=False,
                       gen_func=None):
        """
        Return generator based on Category defined by category and gen_func.

        @param category: category name with start parameter
        @type category: str
        @rtype: generator
        """
        cat, startfrom = self.getCategory(category)

        return gen_func(cat,
                        start=startfrom,
                        recurse=recurse,
                        content=content)

    @staticmethod
    def _parse_log_events(logtype, user=None, start=None, end=None):
        """
        Parse the -logevent argument information.

        @param logtype: A valid logtype
        @type logtype: str
        @param user: A username associated to the log events. Ignored if
            empty string or None.
        @type user: str
        @param start: Timestamp to start listing from. For backward
            compatibility, this can also be the total amount of pages
            that should be returned. It is taken as 'total' if the value does
            not have 8 digits.
        @type start: str convertible to Timestamp in the format YYYYMMDD. If
            the length is not 8: for backward compatibility to use this as
            'total', it can also be a str (castable to int) or int (positive).
        @param end: Timestamp to end listing at
        @type end: str convertible to Timestamp in the format YYYYMMDD
        @return: The generator or None if invalid 'total' value.
        @rtype: LogeventsPageGenerator
        """
        total = None
        start = start or None  # because start might be an empty string
        if isinstance(start, UnicodeType) and len(start) == 8:
            start = pywikibot.Timestamp.strptime(start, '%Y%m%d')
        elif start is not None:
            try:
                total = int(start)
                if total <= 0:
                    raise ValueError
            except ValueError:
                pywikibot.error('Total number of log ({0}) events must be a '
                                'positive int.'.format(total))
                return None
            start = None

        if end is not None:
            if start is None:
                pywikibot.error('End cannot be given if start is not given.')
                return None
            end = pywikibot.Timestamp.strptime(end, '%Y%m%d')

        # 'user or None', because user might be an empty string when
        # 'foo,,bar' was used.
        return LogeventsPageGenerator(logtype, user or None, total=total,
                                      start=start, end=end)

    def _handle_filelinks(self, value):
        """Handle `-filelinks` argument."""
        if not value:
            value = i18n.input(
                'pywikibot-enter-file-links-processing',
                fallback_prompt='Links to which file page should be '
                                'processed?')
        if not value.startswith(self.site.namespace(6) + ':'):
            value = 'Image:' + value
        page = pywikibot.FilePage(self.site, value)
        return FileLinksGenerator(page)

    def _handle_linter(self, value):
        """Handle `-linter` argument."""
        if not self.site.has_extension('Linter'):
            raise UnknownExtension(
                '-linter needs a site with Linter extension.')
        cats = self.site.siteinfo.get('linter')  # Get linter categories.
        valid_cats = [c for _list in cats.values() for c in _list]

        value = '' if value is None else value
        cat, sep, lint_from = value.partition('/')
        if not lint_from:
            lint_from = None

        if cat == 'show':  # Display categories of lint errors.
            _i = ' ' * 4
            txt = 'Available categories of lint errors:\n'
            for prio, _list in cats.items():
                txt += '{indent}{prio}\n'.format(indent=_i, prio=prio)
                for c in _list:
                    txt += '{indent}{cat}\n'.format(indent=2 * _i, cat=c)
            pywikibot.output('%s' % txt)
            sys.exit(0)

        if not cat:
            lint_cats = valid_cats
        elif cat in ['low', 'medium', 'high']:
            lint_cats = cats[cat]
        else:
            lint_cats = cat.split(',')
            for lint_cat in lint_cats:
                if lint_cat not in valid_cats:
                    raise ValueError('Invalid category of lint errors: %s'
                                     % cat)

        return self.site.linter_pages(
            lint_categories='|'.join(lint_cats), namespaces=self.namespaces,
            lint_from=lint_from)

    def _handle_querypage(self, value):
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
                    '({highmax} for bots).\n'.format(**limit))
            pywikibot.output('%s' % txt)
            sys.exit(0)

        return self.site.querypage(value)

    def _handle_unusedfiles(self, value):
        """Handle `-unusedfiles` argument."""
        return UnusedFilesGenerator(total=_int_none(value), site=self.site)

    def _handle_lonelypages(self, value):
        """Handle `-lonelypages` argument."""
        return LonelyPagesPageGenerator(total=_int_none(value), site=self.site)

    def _handle_unwatched(self, value):
        """Handle `-unwatched` argument."""
        return UnwatchedPagesPageGenerator(
            total=_int_none(value), site=self.site)

    def _handle_wantedpages(self, value):
        """Handle `-wantedpages` argument."""
        return self.site.wantedpages(total=_int_none(value))

    def _handle_wantedfiles(self, value):
        """Handle `-wantedfiles` argument."""
        return self.site.wantedfiles(total=_int_none(value))

    def _handle_wantedtemplates(self, value):
        """Handle `-wantedtemplates` argument."""
        return self.site.wantedtemplates(total=_int_none(value))

    def _handle_wantedcategories(self, value):
        """Handle `-wantedcategories` argument."""
        return self.site.wantedcategories(total=_int_none(value))

    def _handle_property(self, value):
        """Handle `-property` argument."""
        if not value:
            question = 'Which property name to be used?'
            value = pywikibot.input(question + ' (List [?])')
            pnames = self.site.get_property_names()
            # also use the default by <enter> key
            if value in '?' or value not in pnames:
                prefix, value = pywikibot.input_choice(
                    question, ShowingListOption(pnames))
        return page_with_property_generator(value, site=self.site)

    def _handle_usercontribs(self, value):
        """Handle `-usercontribs` argument."""
        self._single_gen_filter_unique = True
        return UserContributionsGenerator(
            value, site=self.site, _filter_unique=None)

    def _handle_withoutinterwiki(self, value):
        """Handle `-withoutinterwiki` argument."""
        return WithoutInterwikiPageGenerator(
            total=_int_none(value), site=self.site)

    def _handle_interwiki(self, value):
        """Handle `-interwiki` argument."""
        if not value:
            value = i18n.input(
                'pywikibot-enter-page-processing',
                fallback_prompt='Which page should be processed?')
        page = pywikibot.Page(pywikibot.Link(value, self.site))
        return InterwikiPageGenerator(page)

    def _handle_randomredirect(self, value):
        """Handle `-randomredirect` argument."""
        # partial workaround for bug T119940
        # to use -namespace/ns with -randomredirect, -ns must be given
        # before -randomredirect
        # otherwise default namespace is 0
        namespaces = self.namespaces or 0
        return RandomRedirectPageGenerator(
            total=_int_none(value), site=self.site, namespaces=namespaces)

    def _handle_random(self, value):
        """Handle `-random` argument."""
        # partial workaround for bug T119940
        # to use -namespace/ns with -random, -ns must be given
        # before -random
        # otherwise default namespace is 0
        namespaces = self.namespaces or 0
        return RandomPageGenerator(
            total=_int_none(value), site=self.site, namespaces=namespaces)

    def _handle_recentchanges(self, value):
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
        elif len(params) == 2:
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

    def _handle_liverecentchanges(self, value):
        """Handle `-liverecentchanges` argument."""
        self.nopreload = True
        return LiveRCPageGenerator(site=self.site, total=_int_none(value))

    def _handle_file(self, value):
        """Handle `-file` argument."""
        if not value:
            value = pywikibot.input('Please enter the local file name:')
        return TextfilePageGenerator(value, site=self.site)

    def _handle_namespaces(self, value):
        """Handle `-namespaces` argument."""
        if isinstance(self._namespaces, frozenset):
            warn('Cannot handle arg -namespaces as namespaces can not '
                 'be altered after a generator is created.',
                 ArgumentDeprecationWarning, 3)
            return True
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

    def _handle_limit(self, value):
        """Handle `-limit` argument."""
        if not value:
            value = pywikibot.input('What is the limit value?')
        self.limit = _int_none(value)
        return True

    def _handle_category(self, value):
        """Handle `-category` argument."""
        return self.getCategoryGen(
            value, recurse=False, gen_func=CategorizedPageGenerator)

    _handle_cat = _handle_category

    def _handle_catr(self, value):
        """Handle `-catr` argument."""
        return self.getCategoryGen(
            value, recurse=True, gen_func=CategorizedPageGenerator)

    def _handle_subcats(self, value):
        """Handle `-subcats` argument."""
        return self.getCategoryGen(
            value, recurse=False, gen_func=SubCategoriesPageGenerator)

    def _handle_subcatsr(self, value):
        """Handle `-subcatsr` argument."""
        return self.getCategoryGen(
            value, recurse=True, gen_func=SubCategoriesPageGenerator)

    def _handle_catfilter(self, value):
        """Handle `-catfilter` argument."""
        cat, _ = self.getCategory(value)
        self.catfilter_list.append(cat)
        return True

    def _handle_page(self, value):
        """Handle `-page` argument."""
        if not value:
            value = pywikibot.input('What page do you want to use?')
        return [pywikibot.Page(pywikibot.Link(value, self.site))]

    def _handle_pageid(self, value):
        """Handle `-pageid` argument."""
        if not value:
            value = pywikibot.input('What pageid do you want to use?')
        return PagesFromPageidGenerator(value, site=self.site)

    def _handle_uncatfiles(self, value):
        """Handle `-uncatfiles` argument."""
        return UnCategorizedImageGenerator(site=self.site)

    def _handle_uncatcat(self, value):
        """Handle `-uncatcat` argument."""
        return UnCategorizedCategoryGenerator(site=self.site)

    def _handle_uncat(self, value):
        """Handle `-uncat` argument."""
        return UnCategorizedPageGenerator(site=self.site)

    def _handle_ref(self, value):
        """Handle `-ref` argument."""
        if not value:
            value = pywikibot.input(
                'Links to which page should be processed?')
        page = pywikibot.Page(pywikibot.Link(value, self.site))
        return ReferringPageGenerator(page)

    def _handle_links(self, value):
        """Handle `-links` argument."""
        if not value:
            value = pywikibot.input(
                'Links from which page should be processed?')
        page = pywikibot.Page(pywikibot.Link(value, self.site))
        return LinkedPageGenerator(page)

    def _handle_weblink(self, value):
        """Handle `-weblink` argument."""
        if not value:
            value = pywikibot.input(
                'Pages with which weblink should be processed?')
        # If url is * we make it None in order to search for every page
        # with any URL.
        if value == '*':
            value = None
        return LinksearchPageGenerator(value, site=self.site)

    def _handle_transcludes(self, value):
        """Handle `-transcludes` argument."""
        if not value:
            value = pywikibot.input(
                'Pages that transclude which page should be processed?')
        page = pywikibot.Page(pywikibot.Link(value,
                                             default_namespace=10,
                                             source=self.site))
        return ReferringPageGenerator(page, onlyTemplateInclusion=True)

    def _handle_start(self, value):
        """Handle `-start` argument."""
        if not value:
            value = '!'
        firstpagelink = pywikibot.Link(value, self.site)
        return self.site.allpages(
            start=firstpagelink.title, namespace=firstpagelink.namespace,
            filterredir=False)

    def _handle_prefixindex(self, value):
        """Handle `-prefixindex` argument."""
        if not value:
            value = pywikibot.input('What page names are you looking for?')
        return PrefixingPageGenerator(prefix=value, site=self.site)

    def _handle_newimages(self, value):
        """Handle `-newimages` argument."""
        return NewimagesPageGenerator(total=_int_none(value), site=self.site)

    def _handle_newpages(self, value):
        """Handle `-newpages` argument."""
        # partial workaround for bug T69249
        # to use -namespace/ns with -newpages, -ns must be given
        # before -newpages
        # otherwise default namespace is 0
        namespaces = self.namespaces or 0
        return NewpagesPageGenerator(
            namespaces=namespaces, total=_int_none(value), site=self.site)

    def _handle_unconnectedpages(self, value):
        """Handle `-unconnectedpages` argument."""
        return self.site.unconnected_pages(total=_int_none(value))

    def _handle_imagesused(self, value):
        """Handle `-imagesused` argument."""
        if not value:
            value = pywikibot.input(
                'Images on which page should be processed?')
        page = pywikibot.Page(pywikibot.Link(value, self.site))
        return ImagesPageGenerator(page)

    def _handle_searchitem(self, value):
        """Handle `-searchitem` argument."""
        if not value:
            value = pywikibot.input('Text to look for:')
        params = value.split(':')
        value = params[-1]
        lang = params[0] if len(params) == 2 else None
        return WikibaseSearchItemPageGenerator(
            value, language=lang, site=self.site)

    def _handle_search(self, value):
        """Handle `-search` argument."""
        if not value:
            value = pywikibot.input('What do you want to search for?')
        # In order to be useful, all namespaces are required
        return SearchPageGenerator(value, namespaces=[], site=self.site)

    @staticmethod
    def _handle_google(value):
        """Handle `-google` argument."""
        return GoogleSearchPageGenerator(value)

    def _handle_titleregex(self, value):
        """Handle `-titleregex` argument."""
        if not value:
            value = pywikibot.input(
                'What page names are you looking for?')
        self.titlefilter_list.append(value)
        return True

    def _handle_titleregexnot(self, value):
        """Handle `-titleregexnot` argument."""
        if not value:
            value = pywikibot.input(
                'All pages except which ones?')
        self.titlenotfilter_list.append(value)
        return True

    def _handle_grep(self, value):
        """Handle `-grep` argument."""
        if not value:
            value = pywikibot.input('Which pattern do you want to grep?')
        self.articlefilter_list.append(value)
        return True

    def _handle_ql(self, value):
        """Handle `-ql` argument."""
        if not self.site.has_extension('ProofreadPage'):
            raise UnknownExtension(
                'Ql filtering needs a site with ProofreadPage extension.')
        value = [int(_) for _ in value.split(',')]
        if min(value) < 0 or max(value) > 4:  # Invalid input ql.
            valid_ql = [
                '{0}: {1}'.format(*i)
                for i in self.site.proofread_levels.items()]
            valid_ql = ', '.join(valid_ql)
            pywikibot.warning('Acceptable values for -ql are:\n    %s'
                              % valid_ql)
        self.qualityfilter_list = value
        return True

    def _handle_onlyif(self, value):
        """Handle `-onlyif` argument."""
        return self._onlyif_onlyifnot_handler(value, False)

    def _handle_onlyifnot(self, value):
        """Handle `-onlyifnot` argument."""
        return self._onlyif_onlyifnot_handler(value, True)

    def _onlyif_onlyifnot_handler(self, value, ifnot):
        """Handle `-onlyif` and `-onlyifnot` arguments."""
        if not value:
            value = pywikibot.input('Which claim do you want to filter?')
        p = re.compile(r'(?<!\\),')  # Match "," only if there no "\" before
        temp = []  # Array to store split argument
        for arg in p.split(value):
            temp.append(arg.replace(r'\,', ',').split('='))
        self.claimfilter_list.append(
            (temp[0][0], temp[0][1], dict(temp[1:]), ifnot))
        return True

    @staticmethod
    def _handle_yahoo(value):
        """Handle `-yahoo` argument."""
        issue_deprecation_warning('-yahoo', depth=3,
                                  warning_class=ArgumentDeprecationWarning,
                                  since='20181125')

    @staticmethod
    def _handle_untagged(value):
        """Handle `-untagged` argument."""
        issue_deprecation_warning('-untagged', depth=3,
                                  warning_class=ArgumentDeprecationWarning,
                                  since='20161116')

    @staticmethod
    def _handle_wikidataquery(value):
        """Handle `-wikidataquery` argument."""
        issue_deprecation_warning('-wikidataquery', depth=3,
                                  warning_class=ArgumentDeprecationWarning,
                                  since='20170520')

    def _handle_sparqlendpoint(self, value):
        """Handle `-sparqlendpoint` argument."""
        if not value:
            value = pywikibot.input('SPARQL endpoint:')
        self._sparql = value

    def _handle_sparql(self, value):
        """Handle `-sparql` argument."""
        if not value:
            value = pywikibot.input('SPARQL query:')
        return WikidataSPARQLPageGenerator(
            value, site=self.site, endpoint=self._sparql)

    def _handle_mysqlquery(self, value):
        """Handle `-mysqlquery` argument."""
        if not value:
            value = pywikibot.input('Mysql query string:')
        return MySQLPageGenerator(value, site=self.site)

    def _handle_intersect(self, value):
        """Handle `-intersect` argument."""
        self.intersect = True
        return True

    def _handle_subpage(self, value):
        """Handle `-subpage` argument."""
        if not value:
            value = pywikibot.input(
                'Maximum subpage depth:')
        self.subpage_max_depth = int(value)
        return True

    def _handle_logevents(self, value):
        """Handle `-logevents` argument."""
        params = value.split(',')
        if params[0] not in self.site.logtypes:
            raise NotImplementedError(
                'Invalid -logevents parameter "{0}"'.format(params[0]))
        return self._parse_log_events(*params)

    def handleArg(self, arg):
        """Parse one argument at a time.

        If it is recognized as an argument that specifies a generator, a
        generator is created and added to the accumulation list, and the
        function returns true. Otherwise, it returns false, so that caller
        can try parsing the argument. Call getCombinedGenerator() after all
        arguments have been parsed to get the final output generator.

        @param arg: Pywikibot argument consisting of -name:value
        @type arg: basestring
        @return: True if the argument supplied was recognised by the factory
        @rtype: bool
        """
        if not arg.startswith('-') and self._positional_arg_name:
            value = arg
            arg = '-' + self._positional_arg_name
        else:
            arg, sep, value = arg.partition(':')

        if value == '':
            value = None

        try:
            handler = getattr(self, '_handle_' + arg[1:], None)
        except UnicodeEncodeError:
            # getattr() on py2 does implicit unicode -> str
            return False
        if handler:
            handler_result = handler(value)
            if isinstance(handler_result, bool):
                return handler_result
            if handler_result:
                self.gens.append(handler_result)
                return True
        return False


def _int_none(v):
    """Return None if v is None or '' else return int(v)."""
    return v if (v is None or v == '') else int(v)


@deprecated('Site.allpages()', since='20180512')
@deprecated_args(step=None)
def AllpagesPageGenerator(start='!', namespace=0, includeredirects=True,
                          site=None, total=None, content=False):
    """
    Iterate Page objects for all titles in a single namespace.

    If includeredirects is False, redirects are not included. If
    includeredirects equals the string 'only', only redirects are added.

    @param total: Maximum number of pages to retrieve in total
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
                         filterredir=filterredir, total=total, content=content)


@deprecated_args(step=None)
def PrefixingPageGenerator(prefix, namespace=None, includeredirects=True,
                           site=None, total=None, content=False):
    """
    Prefixed Page generator.

    @param prefix: The prefix of the pages.
    @type prefix: str
    @param namespace: Namespace to retrieve pages from
    @type namespace: Namespace or int
    @param includeredirects: If includeredirects is None, False or an empty
        string, redirects will not be found. If includeredirects equals the
        string 'only', only redirects will be found. Otherwise redirects will
        be included.
    @type includeredirects: None, bool, str
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param content: If True, load current version of each page (default False)
    @type content: bool
    @return: a generator that yields Page objects
    @rtype: generator
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
                         filterredir=filterredir, total=total, content=content)


@deprecated_args(number='total', mode='logtype', repeat=None)
def LogeventsPageGenerator(logtype=None, user=None, site=None, namespace=None,
                           total=None, start=None, end=None, reverse=False):
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
    @param start: Timestamp to start listing from
    @type start: pywikibot.Timestamp
    @param end: Timestamp to end listing at
    @type end: pywikibot.Timestamp
    @param reverse: if True, start with oldest changes (default: newest)
    @type reverse: bool
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
                              'failed to load page for %r; skipping'
                              % entry.data)
            pywikibot.exception(e)


@deprecated('LogeventsPageGenerator', since='20141210')
@deprecated_args(number='total', mode='logtype', repeat=None)
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


@deprecated_args(number='total', step=None, namespace='namespaces',
                 repeat=None, get_redirect=None)
def NewpagesPageGenerator(site=None, namespaces=[0], total=None):
    """
    Iterate Page objects for all new titles in a single namespace.

    @param total: Maxmium number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    # API does not (yet) have a newpages function, so this tries to duplicate
    # it by filtering the recentchanges output
    # defaults to namespace 0 because that's how Special:Newpages defaults
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.newpages(namespaces=namespaces,
                                              total=total, returndict=True))


@deprecated_args(nobots=None, step=None)
def RecentChangesPageGenerator(start=None, end=None, reverse=False,
                               namespaces=None, pagelist=None,
                               changetype=None, showMinor=None,
                               showBot=None, showAnon=None,
                               showRedirects=None, showPatrolled=None,
                               topOnly=False, total=None,
                               user=None, excludeuser=None, site=None,
                               tag=None, _filter_unique=None):
    """
    Generate pages that are in the recent changes list, including duplicates.

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
    @param tag: a recent changes tag
    @type tag: str
    """
    if site is None:
        site = pywikibot.Site()

    gen = site.recentchanges(start=start, end=end, reverse=reverse,
                             namespaces=namespaces, pagelist=pagelist,
                             changetype=changetype, minor=showMinor,
                             bot=showBot, anon=showAnon,
                             redirect=showRedirects,
                             patrolled=showPatrolled,
                             top_only=topOnly, total=total,
                             user=user, excludeuser=excludeuser, tag=tag)

    gen.request['rcprop'] = 'title'
    gen = (pywikibot.Page(site, x['title'])
           for x in gen if x['type'] != 'log' or 'title' in x)

    if _filter_unique:
        gen = _filter_unique(gen)
    return gen


@deprecated('site.unconnected_pages()', since='20180512')
@deprecated_args(step=None)
def UnconnectedPageGenerator(site=None, total=None):
    """
    Iterate Page objects for all unconnected pages to a Wikibase repository.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.APISite}
    """
    if site is None:
        site = pywikibot.Site()
    if not site.data_repository():
        raise ValueError('The given site does not have Wikibase repository.')
    return site.unconnected_pages(total=total)


@deprecated_args(referredImagePage='referredFilePage', step=None)
def FileLinksGenerator(referredFilePage, total=None, content=False):
    """Yield Pages on which the file referredFilePage is displayed."""
    return referredFilePage.usingPages(total=total, content=content)


@deprecated_args(step=None)
def ImagesPageGenerator(pageWithImages, total=None, content=False):
    """Yield FilePages displayed on pageWithImages."""
    return pageWithImages.imagelinks(total=total, content=content)


def InterwikiPageGenerator(page):
    """Iterate over all interwiki (non-language) links on a page."""
    return (pywikibot.Page(link) for link in page.interwiki())


@deprecated_args(step=None)
def LanguageLinksPageGenerator(page, total=None):
    """Iterate over all interwiki language links on a page."""
    return (pywikibot.Page(link) for link in page.iterlanglinks(total=total))


@deprecated_args(step=None)
def ReferringPageGenerator(referredPage, followRedirects=False,
                           withTemplateInclusion=True,
                           onlyTemplateInclusion=False,
                           total=None, content=False):
    """Yield all pages referring to a specific page."""
    return referredPage.getReferences(
        follow_redirects=followRedirects,
        with_template_inclusion=withTemplateInclusion,
        only_template_inclusion=onlyTemplateInclusion,
        total=total, content=content)


@deprecated_args(step=None)
def CategorizedPageGenerator(category, recurse=False, start=None,
                             total=None, content=False,
                             namespaces=None):
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
    kwargs = {
        'recurse': recurse, 'total': total,
        'content': content, 'namespaces': namespaces,
    }
    if start:
        if category.site.mw_version < '1.18':
            kwargs.pop('total', None)
            count = 0
            for article in category.articles(**kwargs):
                if article.title() >= start:
                    count += 1
                    yield article
                    if count == total:
                        return
            return
        kwargs['startprefix'] = start
    for a in category.articles(**kwargs):
        yield a


@deprecated_args(step=None)
def SubCategoriesPageGenerator(category, recurse=False, start=None,
                               total=None, content=False):
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
    for s in category.subcategories(recurse=recurse,
                                    total=total, content=content):
        if start is None or s.title(with_ns=False) >= start:
            yield s


@deprecated_args(step=None)
def LinkedPageGenerator(linkingPage, total=None, content=False):
    """Yield all pages linked from a specific page.

    See L{pywikibot.page.BasePage.linkedPages} for details.

    @param linkingPage: the page that links to the pages we want
    @type linkingPage: L{pywikibot.Page}
    @param total: the total number of pages to iterate
    @type total: int
    @param content: if True, retrieve the current content of each linked page
    @type content: bool
    @return: a generator that yields Page objects of pages linked to
        linkingPage
    @rtype: generator
    """
    return linkingPage.linkedPages(total=total, content=content)


def TextfilePageGenerator(filename=None, site=None):
    """Iterate pages from a list in a text file.

    The file must contain page links between double-square-brackets or, in
    alternative, separated by newlines. The generator will yield each
    corresponding Page object.

    @param filename: the name of the file that should be read. If no name is
                     given, the generator prompts the user.
    @type filename: str
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}

    """
    if filename is None:
        filename = pywikibot.input('Please enter the filename:')
    if site is None:
        site = pywikibot.Site()
    with codecs.open(filename, 'r', config.textfile_encoding) as f:
        linkmatch = None
        for linkmatch in pywikibot.link_regex.finditer(f.read()):
            # If the link is in interwiki format, the Page object may reside
            # on a different Site than the default.
            # This makes it possible to work on different wikis using a single
            # text file, but also could be dangerous because you might
            # inadvertently change pages on another wiki!
            yield pywikibot.Page(pywikibot.Link(linkmatch.group('title'),
                                                site))
        if linkmatch is None:
            f.seek(0)
            for title in f:
                title = title.strip()
                if '|' in title:
                    title = title[:title.index('|')]
                if title:
                    yield pywikibot.Page(site, title)


def PagesFromTitlesGenerator(iterable, site=None):
    """
    Generate pages from the titles (unicode strings) yielded by iterable.

    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    for title in iterable:
        if not isinstance(title, UnicodeType):
            break
        yield pywikibot.Page(pywikibot.Link(title, site))


def PagesFromPageidGenerator(pageids, site=None):
    """
    Return a page generator from pageids.

    Pages are iterated in the same order than in the underlying pageids.
    Pageids are filtered and only one page is returned in case of
    duplicate pageid.

    @param pageids: an iterable that returns pageids, or a comma-separated
                    string of pageids (e.g. '945097,1483753,956608')
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()

    return site.load_pages_from_pageids(pageids)


@deprecated_args(number='total', step=None)
def UserContributionsGenerator(username, namespaces=None, site=None,
                               total=None,
                               _filter_unique=_filter_unique_pages):
    """Yield unique pages edited by user:username.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param namespaces: list of namespace numbers to fetch contribs from
    @type namespaces: list of int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
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


def NamespaceFilterPageGenerator(generator, namespaces, site=None):
    """
    A generator yielding pages from another generator in given namespaces.

    If a site is provided, the namespaces are validated using the namespaces
    of that site, otherwise the namespaces are validated using the default
    site.

    NOTE: API-based generators that have a "namespaces" parameter perform
    namespace filtering more efficiently than this generator.

    @param namespaces: list of namespace identifiers to limit results
    @type namespaces: iterable of basestring or Namespace key,
        or a single instance of those types.
    @param site: Site for generator results; mandatory if
        namespaces contains namespace names. Defaults to the default site.
    @type site: L{pywikibot.site.BaseSite}
    @raises KeyError: a namespace identifier was not resolved
    @raises TypeError: a namespace identifier has an inappropriate
        type such as NoneType or bool, or more than one namespace
        if the API module does not support multiple namespaces
    """
    # As site was only required if the namespaces contain strings, don't
    # attempt to use the config selected site unless the initial attempt
    # at resolving the namespaces fails.
    if not site:
        site = pywikibot.Site()
    try:
        namespaces = site.namespaces.resolve(namespaces)
    except KeyError as e:
        pywikibot.log('Failed resolving namespaces:')
        pywikibot.exception(e)
        raise

    return (page for page in generator if page.namespace() in namespaces)


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
                pywikibot.output('%s is a redirect page. Skipping.' % page)

        else:
            if page.isRedirectPage():
                yield page
            elif show_filtered:
                pywikibot.output('%s is not a redirect page. Skipping.'
                                 % page)


class ItemClaimFilter(object):

    """Item claim filter."""

    @classmethod
    def __filter_match(cls, page, prop, claim, qualifiers=None):
        """
        Return true if the page contains the claim given.

        @param page: the page to check
        @return: true if page contains the claim, false otherwise
        @rtype: bool
        """
        if not isinstance(page, pywikibot.page.WikibasePage):
            if isinstance(page.site, pywikibot.site.DataSite):  # T175151
                on_repo = page.namespace() in (
                    page.site.item_namespace, page.site.property_namespace)
            else:
                on_repo = False
            if on_repo:
                if page.namespace() == page.site.property_namespace:
                    cls = pywikibot.PropertyPage
                else:
                    cls = pywikibot.ItemPage
                page = cls(page.site, page.title(with_ns=False))
            else:
                try:
                    page = pywikibot.ItemPage.fromPage(page)
                except pywikibot.NoPage:
                    return False

        for page_claim in page.get()['claims'].get(prop, []):
            if page_claim.target_equals(claim):
                if not qualifiers:
                    return True

                for prop, val in qualifiers.items():
                    if not page_claim.has_qualifier(prop, val):
                        return False
                return True
        return False

    @classmethod
    def filter(cls, generator, prop, claim, qualifiers=None, negate=False):
        """
        Yield all ItemPages which contain certain claim in a property.

        @param prop: property id to check
        @type prop: str
        @param claim: value of the property to check. Can be exact value (for
            instance, ItemPage instance) or a string (e.g. 'Q37470').
        @param qualifiers: dict of qualifiers that must be present, or None if
            qualifiers are irrelevant
        @type qualifiers: dict or None
        @param negate: true if pages that do *not* contain specified claim
            should be yielded, false otherwise
        @type negate: bool
        """
        for page in generator:
            if cls.__filter_match(page, prop, claim, qualifiers) is not negate:
                yield page


# name the generator methods
ItemClaimFilterPageGenerator = ItemClaimFilter.filter


def SubpageFilterGenerator(generator, max_depth=0, show_filtered=False):
    """
    Generator which filters out subpages based on depth.

    It looks at the namespace of each page and checks if that namespace has
    subpages enabled. If so, pages with forward slashes ('/') are excluded.

    @param generator: A generator object
    @type generator: any generator or iterator
    @param max_depth: Max depth of subpages to yield, at least zero
    @type max_depth: int
    @param show_filtered: Output a message for each page not yielded
    @type show_filtered: bool
    """
    assert max_depth >= 0, 'Max subpage depth must be at least 0'

    for page in generator:
        if page.depth <= max_depth:
            yield page
        else:
            if show_filtered:
                pywikibot.output(
                    'Page %s is a subpage that is too deep. Skipping.'
                    % page)


class RegexFilter(object):

    """Regex filter."""

    @classmethod
    def __filter_match(cls, regex, string, quantifier):
        """Return True if string matches precompiled regex list.

        @param quantifier: a qualifier
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
        # We assume that all list components have the same type
        if isinstance(regex[0], UnicodeType):
            regex = [re.compile(r, flag) for r in regex]
        return regex

    @classmethod
    @deprecated_args(inverse='quantifier')
    def titlefilter(cls, generator, regex, quantifier='any',
                    ignore_namespace=True):
        """Yield pages from another generator whose title matches regex.

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
        @type quantifier: str of ('all', 'any', 'none')
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
            title = page.title(with_ns=not ignore_namespace)
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


def QualityFilterPageGenerator(generator, quality):
    """
    Wrap a generator to filter pages according to quality levels.

    This is possible only for pages with content_model 'proofread-page'.
    In all the other cases, no filter is applied.

    @param generator: A generator object
    @param quality: proofread-page quality levels (valid range 0-4)
    @type quality: list of int

    """
    for page in generator:
        if page.namespace() == page.site.proofread_page_ns:
            page = ProofreadPage(page)
            if page.quality_level in quality:
                yield page
        else:
            yield page


def CategoryFilterPageGenerator(generator, category_list, site=None):
    """
    Wrap a generator to filter pages by categories specified.

    @param generator: A generator object
    @param category_list: categories used to filter generated pages
    @type category_list: list of category objects

    """
    if site is None:
        site = pywikibot.Site()
    for page in generator:
        if all(x in site.pagecategories(page) for x in category_list):
            yield page


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
                        'Last edit on %s was on %s.\nToo old. Skipping.'
                        % (page, last_edit.isoformat()))
                continue

            if last_edit > last_edit_end:
                if show_filtered:
                    pywikibot.output(
                        'Last edit on %s was on %s.\nToo recent. Skipping.'
                        % (page, last_edit.isoformat()))
                continue

        if do_first_edit:
            first_edit = page.oldest_revision.timestamp

            if first_edit < first_edit_start:
                if show_filtered:
                    pywikibot.output(
                        'First edit on %s was on %s.\nToo old. Skipping.'
                        % (page, first_edit.isoformat()))

            if first_edit > first_edit_end:
                if show_filtered:
                    pywikibot.output(
                        'First edit on %s was on %s.\nToo recent. Skipping.'
                        % (page, first_edit.isoformat()))
                continue

        yield page


def UserEditFilterGenerator(generator, username, timestamp=None, skip=False,
                            max_revision_depth=None, show_filtered=False):
    """
    Generator which will yield Pages modified by username.

    It only looks at the last editors given by max_revision_depth.
    If timestamp is set in MediaWiki format JJJJMMDDhhmmss, older edits are
    ignored.
    If skip is set, pages edited by the given user are ignored otherwise only
    pages edited by this user are given back.

    @param generator: A generator object
    @param username: user name which edited the page
    @type username: str
    @param timestamp: ignore edits which are older than this timestamp
    @type timestamp: datetime or str (MediaWiki format JJJJMMDDhhmmss) or None
    @param skip: Ignore pages edited by the given user
    @type skip: bool
    @param max_revision_depth: It only looks at the last editors given by
        max_revision_depth
    @type max_revision_depth: int or None
    @param show_filtered: Output a message for each page not yielded
    @type show_filtered: bool
    """
    if timestamp:
        if isinstance(timestamp, UnicodeType):
            ts = pywikibot.Timestamp.fromtimestampformat(timestamp)
        else:
            ts = timestamp
    for page in generator:
        contribs = page.contributors(total=max_revision_depth, endtime=ts)
        if bool(contribs[username]) is not bool(skip):  # xor operation
            yield page
        elif show_filtered:
            pywikibot.output('Skipping %s' % page.title(as_link=True))


@deprecated('itertools.chain(*iterables)', since='20180513')
def CombinedPageGenerator(generators):
    """Yield from each iterable until exhausted, then proceed with the next."""
    return itertools.chain(*generators)


def PageClassGenerator(generator):
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


def PageWithTalkPageGenerator(generator, return_talk_only=False):
    """Yield pages and associated talk pages from another generator.

    Only yields talk pages if the original generator yields a non-talk page,
    and does not check if the talk page in fact exists.

    """
    for page in generator:
        if not return_talk_only or page.isTalkPage():
            yield page
        if not page.isTalkPage():
            yield page.toggleTalkPage()


@deprecated('LiveRCPageGenerator or EventStreams', since='20180415')
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
            pywikibot.sleep(sleep_duration)
        for item in list(filtered_generator())[::-1]:
            yield item


@deprecated_args(pageNumber='groupsize', step='groupsize', lookahead=None)
def PreloadingGenerator(generator, groupsize=50):
    """
    Yield preloaded pages taken from another generator.

    @param generator: pages to iterate over
    @param groupsize: how many pages to preload at once
    @type groupsize: int
    """
    # pages may be on more than one site, for example if an interwiki
    # generator is used, so use a separate preloader for each site
    sites = {}
    # build a list of pages for each site found in the iterator
    for page in generator:
        site = page.site
        sites.setdefault(site, []).append(page)
        if len(sites[site]) >= groupsize:
            # if this site is at the groupsize, process it
            group = sites.pop(site)
            for i in site.preloadpages(group, groupsize):
                yield i
    for site, pages in sites.items():
        # process any leftover sites that never reached the groupsize
        for i in site.preloadpages(pages, groupsize):
            yield i


@deprecated_args(step='groupsize')
def DequePreloadingGenerator(generator, groupsize=50):
    """Preload generator of type DequeGenerator."""
    assert isinstance(generator, DequeGenerator), \
        'generator must be a DequeGenerator object'

    while True:
        page_count = min(len(generator), groupsize)
        if not page_count:
            return

        for page in PreloadingGenerator(generator, page_count):
            yield page


@deprecated_args(step='groupsize')
def PreloadingEntityGenerator(generator, groupsize=50):
    """
    Yield preloaded pages taken from another generator.

    Function basically is copied from above, but for Wikibase entities.

    @param generator: pages to iterate over
    @type generator: Iterable
    @param groupsize: how many pages to preload at once
    @type groupsize: int
    """
    sites = {}
    for page in generator:
        site = page.site
        sites.setdefault(site, []).append(page)
        if len(sites[site]) >= groupsize:
            # if this site is at the groupsize, process it
            group = sites.pop(site)
            repo = site.data_repository()
            for i in repo.preload_entities(group, groupsize):
                yield i
    for site, pages in sites.items():
        # process any leftover sites that never reached the groupsize
        repo = site.data_repository()
        for i in repo.preload_entities(pages, groupsize):
            yield i


@deprecated_args(number='total', step=None, repeat=None)
def NewimagesPageGenerator(total=None, site=None):
    """
    New file generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return (entry.page()
            for entry in site.logevents(logtype='upload', total=total))


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
                        '%s has a wikidata item. Skipping.' % page)
                continue
        else:
            if has_item:
                if show_filtered:
                    pywikibot.output(
                        "%s doesn't have a wikidata item. Skipping." % page)
                continue

        yield page


@deprecated_args(extension=None, number='total', repeat=None)
def UnusedFilesGenerator(total=None, site=None):
    """
    Unused files generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.unusedfiles(total=total)


@deprecated_args(number='total', repeat=None)
def WithoutInterwikiPageGenerator(total=None, site=None):
    """
    Page lacking interwikis generator.

    @param total: Maximum number of pages to retrieve in total
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.withoutinterwiki(total=total)


@deprecated_args(number='total', repeat=None)
def UnCategorizedCategoryGenerator(total=100, site=None):
    """
    Uncategorized category generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedcategories(total=total)


@deprecated_args(number='total', repeat=None)
def UnCategorizedImageGenerator(total=100, site=None):
    """
    Uncategorized file generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedimages(total=total)


@deprecated_args(number='total', repeat=None)
def UnCategorizedPageGenerator(total=100, site=None):
    """
    Uncategorized page generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedpages(total=total)


@deprecated_args(number='total', repeat=None)
def UnCategorizedTemplateGenerator(total=100, site=None):
    """
    Uncategorized template generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedtemplates(total=total)


@deprecated_args(number='total', repeat=None)
def LonelyPagesPageGenerator(total=None, site=None):
    """
    Lonely page generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.lonelypages(total=total)


@deprecated_args(number='total', repeat=None)
def UnwatchedPagesPageGenerator(total=None, site=None):
    """
    Unwatched page generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.unwatchedpages(total=total)


def page_with_property_generator(name, total=None, site=None):
    """
    Special:PagesWithProperty page generator.

    @param name: Property name of pages to be retrieved
    @type name: str
    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.pages_with_property(name, total=total)


@deprecated('Site.wantedpages', since='20180803')
def WantedPagesPageGenerator(total=100, site=None):
    """
    Wanted page generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.wantedpages(total=total)


@deprecated_args(number='total', repeat=None)
def AncientPagesPageGenerator(total=100, site=None):
    """
    Ancient page generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.ancientpages(total=total))


@deprecated_args(number='total', repeat=None)
def DeadendPagesPageGenerator(total=100, site=None):
    """
    Dead-end page generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.deadendpages(total=total)


@deprecated_args(number='total', repeat=None)
def LongPagesPageGenerator(total=100, site=None):
    """
    Long page generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.longpages(total=total))


@deprecated_args(number='total', repeat=None)
def ShortPagesPageGenerator(total=100, site=None):
    """
    Short page generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.shortpages(total=total))


@deprecated_args(number='total')
def RandomPageGenerator(total=None, site=None, namespaces=None):
    """
    Random page generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.randompages(total=total, namespaces=namespaces)


@deprecated_args(number='total')
def RandomRedirectPageGenerator(total=None, site=None, namespaces=None):
    """
    Random redirect generator.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.randompages(total=total, namespaces=namespaces,
                            redirects=True)


@deprecated_args(link='url', euprotocol='protocol', step=None)
def LinksearchPageGenerator(url, namespaces=None, total=None,
                            site=None, protocol='http'):
    """Yield all pages that link to a certain URL, like Special:Linksearch.

    @param url: The URL to search for (without the protocol prefix);
            this may include a '*' as a wildcard, only at the start of the
            hostname
    @type url: str
    @param namespaces: list of namespace numbers to fetch contribs from
    @type namespaces: list of int
    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.exturlusage(url, namespaces=namespaces, protocol=protocol,
                            total=total, content=False)


@deprecated_args(number='total', step=None)
def SearchPageGenerator(query, total=None, namespaces=None, site=None):
    """
    Yield pages from the MediaWiki internal search engine.

    @param total: Maximum number of pages to retrieve in total
    @type total: int
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    return site.search(query, total=total, namespaces=namespaces)


def LiveRCPageGenerator(site=None, total=None):
    """
    Yield pages from a socket.io RC stream.

    Generates pages based on the EventStreams Server-Sent-Event (SSE) recent
    changes stream.
    The Page objects will have an extra property ._rcinfo containing the
    literal rc data. This can be used to e.g. filter only new pages. See
    `pywikibot.comms.eventstreams.rc_listener` for details on the .rcinfo
    format.

    @param site: site to return recent changes for
    @type site: pywikibot.BaseSite
    @param total: the maximum number of changes to return
    @type total: int
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


class GoogleSearchPageGenerator(object):

    """
    Page generator using Google search results.

    To use this generator, you need to install the package 'google':

        L{https://pypi.org/project/google}

    This package has been available since 2010, hosted on github
    since 2012, and provided by pypi since 2013.

    As there are concerns about Google's Terms of Service, this
    generator prints a warning for each query.
    """

    def __init__(self, query=None, site=None):
        """
        Initializer.

        @param site: Site for generator results.
        @type site: L{pywikibot.site.BaseSite}
        """
        self.query = query or pywikibot.input('Please enter the search query:')
        if site is None:
            site = pywikibot.Site()
        self.site = site

    def queryGoogle(self, query):
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
            pywikibot.error('ERROR: generator GoogleSearchPageGenerator '
                            "depends on package 'google'.\n"
                            'To install, please run: pip install google.')
            exit(1)
        pywikibot.warning('Please read http://www.google.com/accounts/TOS')
        for url in google.search(query):
            yield url

    def __iter__(self):
        """Iterate results."""
        # restrict query to local site
        localQuery = '%s site:%s' % (self.query, self.site.hostname())
        base = 'http://%s%s' % (self.site.hostname(),
                                self.site.article_path)
        for url in self.queryGoogle(localQuery):
            if url[:len(base)] == base:
                title = url[len(base):]
                page = pywikibot.Page(pywikibot.Link(title, self.site))
                # Google contains links in the format
                # https://de.wikipedia.org/wiki/en:Foobar
                if page.site == self.site:
                    yield page


def MySQLPageGenerator(query, site=None, verbose=None):
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

    See https://www.mediawiki.org/wiki/Manual:Pywikibot/MySQL.

    @param query: MySQL query to execute
    @param site: Site object
    @type site: L{pywikibot.site.BaseSite}
    @param verbose: if True, print query to be executed;
        if None, config.verbose_output will be used.
    @type verbose: None or bool
    @return: generator which yields pywikibot.Page
    """
    from pywikibot.data import mysql

    if site is None:
        site = pywikibot.Site()

    row_gen = mysql.mysql_query(query,
                                dbname=site.dbName(),
                                encoding=site.encoding(),
                                verbose=verbose)
    for row in row_gen:
        namespaceNumber, pageName = row
        if pageName:
            # Namespace Dict only supports int
            namespace = site.namespace(int(namespaceNumber))
            pageName = pageName.decode(site.encoding())
            if namespace:
                pageTitle = '%s:%s' % (namespace, pageName)
            else:
                pageTitle = pageName
            page = pywikibot.Page(site, pageTitle)
            yield page


class XMLDumpOldPageGenerator(IteratorNextMixin):

    """
    Xml generator that yields Page objects with old text loaded.

    @param filename: filename of XML dump
    @type filename: str
    @param start: skip entries below that value
    @type start: str or None
    @param namespaces: namespace filter
    @type identifiers: iterable of basestring or Namespace key,
        or a single instance of those types
    @param site: current site for the generator
    @type site: pywikibot.Site or None
    @param text_predicate: a callable with entry.text as parameter and boolean
        as result to indicate the generator should return the page or not
    @type text_predicate: function identifier or None

    @ivar text_predicate: holds text_predicate function
    @ivar skipping: True if start parameter is given, else False
    @ivar start: holds start parameter
    @ivar namespaces: holds namespaces filter
    @ivar parser: holds the xmlreader.XmlDump parse method
    """

    @deprecated_args(xmlFilename='filename', xmlStart='start')
    def __init__(self, filename, start=None, namespaces=None, site=None,
                 text_predicate=None):
        """Initializer."""
        self.text_predicate = text_predicate

        self.skipping = bool(start)
        if self.skipping:
            self.start = start.replace('_', ' ')
        else:
            self.start = None

        self.site = site or pywikibot.Site()
        if not namespaces:
            self.namespaces = self.site.namespaces
        else:
            self.namespaces = self.site.namespaces.resolve(namespaces)

        dump = xmlreader.XmlDump(filename)
        self.parser = dump.parse()

    @property
    @deprecated('self.start', since='20160414')
    def xmlStart(self):
        """Deprecated xmlStart instance variable."""
        return self.start

    @xmlStart.setter
    @deprecated('self.start', since='20160414')
    def xmlStart(self, value):
        self.start = value

    def __next__(self):
        """Get next Page."""
        while True:
            try:
                entry = next(self.parser)
            except StopIteration:
                raise
            if self.skipping:
                if entry.title < self.start:
                    continue
                self.skipping = False
            page = pywikibot.Page(self.site, entry.title)
            if page.namespace() not in self.namespaces:
                continue
            if not self.text_predicate or self.text_predicate(entry.text):
                page.text = entry.text
                return page


class XMLDumpPageGenerator(XMLDumpOldPageGenerator):

    """Xml generator that yields Page objects without text loaded."""

    def __next__(self):
        """Get next Page from dump and remove the text."""
        page = super(XMLDumpPageGenerator, self).__next__()
        del page.text
        return page


def YearPageGenerator(start=1, end=2050, site=None):
    """
    Year page generator.

    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    pywikibot.output('Starting with year %i' % start)
    for i in range(start, end + 1):
        if i % 100 == 0:
            pywikibot.output('Preparing %i...' % i)
        # There is no year 0
        if i != 0:
            current_year = date.formatYear(site.lang, i)
            yield pywikibot.Page(pywikibot.Link(current_year, site))


@deprecated_args(startMonth='start_month', endMonth='end_month')
def DayPageGenerator(start_month=1, end_month=12, site=None, year=2000):
    """
    Day page generator.

    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    @param year: considering leap year.
    @type year: int
    """
    if site is None:
        site = pywikibot.Site()
    lang = site.lang
    firstPage = pywikibot.Page(site, date.format_date(start_month, 1, lang))
    pywikibot.output('Starting with %s' % firstPage.title(as_link=True))
    for month in range(start_month, end_month + 1):
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            yield pywikibot.Page(
                pywikibot.Link(date.format_date(month, day, lang), site))


def WikidataPageFromItemGenerator(gen, site):
    """Generate pages from site based on sitelinks of item pages.

    @param gen: generator of L{pywikibot.ItemPage}
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}

    """
    repo = site.data_repository()
    for sublist in itergroup(gen, 50):
        req = {'ids': [item.id for item in sublist],
               'sitefilter': site.dbName(),
               'action': 'wbgetentities',
               'props': 'sitelinks'}

        wbrequest = repo._simple_request(**req)
        wbdata = wbrequest.submit()
        entities = (item for item in wbdata['entities'].values() if
                    'sitelinks' in item and site.dbName() in item['sitelinks'])
        sitelinks = (item['sitelinks'][site.dbName()]['title']
                     for item in entities)
        for sitelink in sitelinks:
            yield pywikibot.Page(site, sitelink)


def WikidataSPARQLPageGenerator(query, site=None,
                                item_name='item', endpoint=None,
                                entity_url=None, result_type=set):
    """Generate pages that result from the given SPARQL query.

    @param query: the SPARQL query string.
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    @param item_name: name of the item in the SPARQL query
    @type item_name: str
    @param endpoint: SPARQL endpoint URL
    @type endpoint: str
    @param entity_url: URL prefix for any entities returned in a query.
    @type entity_url: str
    @param result_type: type of the iterable in which
             SPARQL results are stored (default set)
    @type result_type: iterable

    """
    from pywikibot.data import sparql

    if site is None:
        site = pywikibot.Site()
    repo = site.data_repository()
    dependencies = {'endpoint': endpoint, 'entity_url': entity_url}
    if not endpoint or not entity_url:
        dependencies['repo'] = repo
    query_object = sparql.SparqlQuery(**dependencies)
    data = query_object.get_items(query,
                                  item_name=item_name,
                                  result_type=result_type)
    entities = (repo.get_entity_for_entity_id(entity) for entity in data)
    if isinstance(site, pywikibot.site.DataSite):
        return entities

    return WikidataPageFromItemGenerator(entities, site)


def WikibaseSearchItemPageGenerator(
    text, language=None, total=None, site=None
):
    """
    Generate pages that contain the provided text.

    @param text: Text to look for.
    @type text: str
    @param language: Code of the language to search in. If not specified,
        value from pywikibot.config.data_lang is used.
    @type language: str
    @param total: Maximum number of pages to retrieve in total, or None in
        case of no limit.
    @type total: int or None
    @param site: Site for generator results.
    @type site: L{pywikibot.site.BaseSite}
    """
    if site is None:
        site = pywikibot.Site()
    if language is None:
        language = site.lang
    repo = site.data_repository()

    data = repo.search_entities(text, language, total=total)
    return (pywikibot.ItemPage(repo, item['id']) for item in data)


class PetScanPageGenerator(object):
    """Queries PetScan (https://petscan.wmflabs.org/) to generate pages."""

    def __init__(self, categories, subset_combination=True, namespaces=None,
                 site=None, extra_options=None):
        """
        Initializer.

        @param categories: List of categories to retrieve pages from
            (as strings)
        @param subset_combination: Combination mode.
            If True, returns the intersection of the results of the categories,
            else returns the union of the results of the categories
        @param namespaces: List of namespaces to search in
            (default is None, meaning all namespaces)
        @param site: Site to operate on
            (default is the default site from the user config)
        @param extra_options: Dictionary of extra options to use (optional)
        """
        if site is None:
            site = pywikibot.Site()

        self.site = site
        self.opts = self.buildQuery(categories, subset_combination,
                                    namespaces, extra_options)

    def buildQuery(self, categories, subset_combination, namespaces,
                   extra_options):
        """
        Get the querystring options to query PetScan.

        @param categories: List of categories (as strings)
        @param subset_combination: Combination mode.
            If True, returns the intersection of the results of the categories,
            else returns the union of the results of the categories
        @param namespaces: List of namespaces to search in
        @param extra_options: Dictionary of extra options to use
        @return: Dictionary of querystring parameters to use in the query
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
                query['ns[{0}]'.format(int(namespace))] = 1

        query_final = query.copy()
        query_final.update(extra_options)

        return query_final

    def query(self):
        """Query PetScan."""
        url = 'https://petscan.wmflabs.org'

        try:
            req = http.fetch(url, params=self.opts)
        except ReadTimeout:
            raise ServerError(
                'received ReadTimeout from {0}'.format(url))
        if 500 <= req.status < 600:
            raise ServerError(
                'received {0} status from {1}'.format(req.status, req.uri))
        j = json.loads(req.text)
        raw_pages = j['*'][0]['a']['*']
        for raw_page in raw_pages:
            yield raw_page

    def __iter__(self):
        for raw_page in self.query():
            page = pywikibot.Page(self.site, raw_page['title'],
                                  int(raw_page['namespace']))
            yield page


DuplicateFilterPageGenerator = redirect_func(
    filter_unique, old_name='DuplicateFilterPageGenerator', since='20180715')
PreloadingItemGenerator = redirect_func(PreloadingEntityGenerator,
                                        old_name='PreloadingItemGenerator',
                                        since='20170314')
# Deprecated old names available for compatibility with compat.
ImageGenerator = redirect_func(
    PageClassGenerator, old_name='ImageGenerator', since='20161017')
FileGenerator = redirect_func(
    PageClassGenerator, old_name='FileGenerator', since='20161017')
CategoryGenerator = redirect_func(
    PageClassGenerator, old_name='CategoryGenerator', since='20161017')
UnCategorizedTemplatesGenerator = redirect_func(
    UnCategorizedTemplateGenerator, old_name='UnCategorizedTemplatesGenerator',
    since='20141225')
RecentchangesPageGenerator = redirect_func(
    RecentChangesPageGenerator, old_name='RecentchangesPageGenerator',
    since='20141225')
# Deprecated old names from Pywikibot 2.0 beta1
WikidataItemGenerator = redirect_func(
    WikibaseItemGenerator, old_name='WikidataItemGenerator', since='20141225')


if __name__ == '__main__':
    pywikibot.output('Pagegenerators cannot be run as script - are you '
                     'looking for listpages.py?')

wrapper = ModuleDeprecationWrapper(__name__)
wrapper._add_deprecated_attr('YahooSearchPageGenerator', replacement_name='',
                             since='20181128')
