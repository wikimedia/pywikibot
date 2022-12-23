"""GeneratorFactory module wich handles pagegenerators options."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import itertools
import re
import sys
from datetime import timedelta
from functools import partial
from itertools import zip_longest
from typing import Any, Optional, Union

import pywikibot
from pywikibot import i18n
from pywikibot.backports import (
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    List,
    Sequence,
    Tuple,
    removeprefix,
)
from pywikibot.bot import ShowingListOption
from pywikibot.data import api
from pywikibot.exceptions import UnknownExtensionError
from pywikibot.pagegenerators._filters import (
    CategoryFilterPageGenerator,
    ItemClaimFilterPageGenerator,
    NamespaceFilterPageGenerator,
    QualityFilterPageGenerator,
    RegexBodyFilterPageGenerator,
    RegexFilterPageGenerator,
    SubpageFilterGenerator,
)
from pywikibot.pagegenerators._generators import (
    CategorizedPageGenerator,
    GoogleSearchPageGenerator,
    LanguageLinksPageGenerator,
    LiveRCPageGenerator,
    LogeventsPageGenerator,
    MySQLPageGenerator,
    NewimagesPageGenerator,
    NewpagesPageGenerator,
    PrefixingPageGenerator,
    RecentChangesPageGenerator,
    SubCategoriesPageGenerator,
    TextIOPageGenerator,
    UserContributionsGenerator,
    WikibaseSearchItemPageGenerator,
    WikidataSPARQLPageGenerator,
)
from pywikibot.tools.collections import DequeGenerator
from pywikibot.tools.itertools import (
    filter_unique,
    intersect_generators,
    roundrobin_generators,
)


HANDLER_RETURN_TYPE = Union[None, bool, Iterable['pywikibot.page.BasePage']]
GEN_FACTORY_NAMESPACE_TYPE = Union[List[str],
                                   FrozenSet['pywikibot.site.Namespace']]
GEN_FACTORY_CLAIM_TYPE = List[Tuple[str, str, Dict[str, str], bool]]
OPT_SITE_TYPE = Optional['pywikibot.site.BaseSite']
OPT_GENERATOR_TYPE = Optional[Iterable['pywikibot.page.Page']]


# This is the function that will be used to de-duplicate page iterators.
_filter_unique_pages = partial(
    filter_unique, key=lambda page: '{}:{}:{}'.format(*page._cmpkey()))


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
        self.gens: List[Iterable['pywikibot.page.Page']] = []
        self._namespaces: GEN_FACTORY_NAMESPACE_TYPE = []
        self.limit: Optional[int] = None
        self.qualityfilter_list: List[int] = []
        self.articlefilter_list: List[str] = []
        self.articlenotfilter_list: List[str] = []
        self.titlefilter_list: List[str] = []
        self.titlenotfilter_list: List[str] = []
        self.claimfilter_list: GEN_FACTORY_CLAIM_TYPE = []
        self.catfilter_list: List['pywikibot.Category'] = []
        self.intersect = False
        self.subpage_max_depth: Optional[int] = None
        self._site = site
        self._positional_arg_name = positional_arg_name
        self._sparql: Optional[str] = None
        self.nopreload = False
        self._validate_options(enabled_options, disabled_options)

        self.is_preloading: Optional[bool] = None
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

    def getCombinedGenerator(self,  # noqa: N802
                             gen: OPT_GENERATOR_TYPE = None,
                             preload: bool = False) -> OPT_GENERATOR_TYPE:
        """Return the combination of all accumulated generators.

        Only call this after all arguments have been parsed.

        .. versionchanged:: 7.3
           set the instance variable :attr:`is_preloading` to True or False.
        .. versionchanged:: 8.0
           if ``limit`` option is set and multiple generators are given,
           pages are yieded in a :func:`roundrobin
           <tools.itertools.roundrobin_generators>` way.

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
            combine = roundrobin_generators if self.limit else itertools.chain
            dupfiltergen = _filter_unique_pages(combine(*self.gens))

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
                preloadgen = pywikibot.pagegenerators.DequePreloadingGenerator
            else:
                preloadgen = pywikibot.pagegenerators.PreloadingGenerator
            dupfiltergen = preloadgen(dupfiltergen)

        if self.articlefilter_list:
            dupfiltergen = RegexBodyFilterPageGenerator(
                dupfiltergen, self.articlefilter_list)

        if self.articlenotfilter_list:
            dupfiltergen = RegexBodyFilterPageGenerator(
                dupfiltergen, self.articlenotfilter_list, 'none')

        return dupfiltergen

    def getCategory(self, category: str  # noqa: N802
                    ) -> Tuple['pywikibot.Category', Optional[str]]:
        """
        Return Category and start as defined by category.

        :param category: category name with start parameter
        """
        if not category:
            category = i18n.input('pywikibot-enter-category-name')
        category = category.replace('#', '|')

        startfrom: Optional[str] = None
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

    def getCategoryGen(self, category: str,  # noqa: N802
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
                f'{err}. Start parameter has wrong format!')
            return None
        except AssertionError:
            pywikibot.error('Total number of log ({}) events must be a '
                            'positive int.'.format(start))
            return None

        try:
            end = pywikibot.Timestamp.fromtimestampformat(end)
        except ValueError as err:
            pywikibot.error(
                f'{err}. End parameter has wrong format!')
            return None
        except TypeError:  # end is None
            pass

        if start or end:
            pywikibot.info('Fetching log events in range: {} - {}.'
                           .format(end or 'beginning of time', start or 'now'))

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
        lint_from: Optional[str] = None
        cat, _, lint_from = value.partition('/')
        lint_from = lint_from or None

        def show_available_categories(cats: Dict[
                                      str, Sequence['pywikibot.Category']]
                                      ) -> None:
            _i = ' ' * 4
            _2i = 2 * _i
            txt = 'Available categories of lint errors:\n'
            for prio, _list in cats.items():
                txt += f'{_i}{prio}\n'
                txt += ''.join(
                    f'{_2i}{c}\n' for c in _list)
            pywikibot.info(txt)

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
                f'Invalid category of lint errors: {cat}'

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
            pywikibot.info(txt)
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
        not_key = 'not:'
        if value.startswith(not_key):
            value = removeprefix(value, not_key)
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
                f'Invalid -logevents parameter "{params[0]}"')
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
        value: Optional[str] = None

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
