"""Page filter generators provided by the pagegenerators module."""
#
# (C) Pywikibot team, 2008-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import datetime
import re
from functools import partial
from typing import TYPE_CHECKING, NamedTuple

import pywikibot
from pywikibot import config
from pywikibot.backports import Generator, Iterable, Pattern, Sequence
from pywikibot.exceptions import NoPageError
from pywikibot.proofreadpage import ProofreadPage
from pywikibot.tools.itertools import filter_unique


if TYPE_CHECKING:
    from pywikibot.site import BaseSite, Namespace

    PRELOAD_SITE_TYPE = dict[pywikibot.site.BaseSite,
                             list[pywikibot.page.BasePage]]
    PATTERN_STR_OR_SEQ_TYPE = (
        str
        | Pattern[str]
        | Sequence[str]
        | Sequence[Pattern[str]]
    )


# This is the function that will be used to de-duplicate page iterators.
_filter_unique_pages = partial(
    filter_unique, key=lambda page: '{}:{}:{}'.format(*page._cmpkey()))


def _output_if(predicate: bool, msg: str) -> None:
    if predicate:
        pywikibot.info(msg)


def NamespaceFilterPageGenerator(
    generator: Iterable[pywikibot.page.BasePage],
    namespaces: frozenset[Namespace]
    | str
    | Namespace
    | Sequence[str | Namespace],
    site: BaseSite | None = None,
) -> Generator[pywikibot.page.BasePage, None, None]:
    """A generator yielding pages from another generator in given namespaces.

    If a site is provided, the namespaces are validated using the namespaces
    of that site, otherwise the namespaces are validated using the default
    site.

    .. note:: API-based generators that have a "namespaces" parameter
       perform namespace filtering more efficiently than this generator.

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


def PageTitleFilterPageGenerator(
    generator: Iterable[pywikibot.page.BasePage],
    ignore_list: dict[str, dict[str, str]],
) -> Generator[pywikibot.page.BasePage, None, None]:
    """Yield only those pages are not listed in the ignore list.

    :param ignore_list: family names are mapped to dictionaries in which
        language codes are mapped to lists of page titles. Each title must
        be a valid regex as they are compared using :py:obj:`re.search`.
    """
    def is_ignored(page: pywikibot.page.BasePage) -> bool:
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
            pywikibot.info(f'Ignoring page {page.title()}')


def RedirectFilterPageGenerator(
    generator: Iterable[pywikibot.page.BasePage],
    no_redirects: bool = True,
    show_filtered: bool = False,
) -> Generator[pywikibot.page.BasePage, None, None]:
    """Yield pages from another generator that are redirects or not.

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
            pywikibot.info(fmt.format(what=what, page=page))


class ItemClaimFilter:

    """Item claim filter."""

    page_classes = {
        True: pywikibot.PropertyPage,
        False: pywikibot.ItemPage,
    }

    @classmethod
    def __filter_match(cls,
                       page: pywikibot.page.WikibasePage,
                       prop: str,
                       claim: str,
                       qualifiers: dict[str, str]) -> bool:
        """Return true if the page contains the claim given.

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

        def match_qualifiers(page_claim: pywikibot.page.Claim,
                             qualifiers: dict[str, str]) -> bool:
            return all(page_claim.has_qualifier(prop, val)
                       for prop, val in qualifiers.items())

        page_claims = page.get()['claims'].get(prop, [])
        return any(
            p_cl.target_equals(claim) and match_qualifiers(p_cl, qualifiers)
            for p_cl in page_claims)

    @classmethod
    def filter(
        cls,
        generator: Iterable[pywikibot.page.WikibasePage],
        prop: str,
        claim: str,
        qualifiers: dict[str, str] | None = None,
        negate: bool = False,
    ) -> Generator[pywikibot.page.WikibasePage, None, None]:
        """Yield all ItemPages which contain certain claim in a property.

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


def SubpageFilterGenerator(generator: Iterable[pywikibot.page.BasePage],
                           max_depth: int = 0,
                           show_filtered: bool = False
                           ) -> Generator[pywikibot.page.BasePage, None, None]:
    """Generator which filters out subpages based on depth.

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
        elif show_filtered:
            pywikibot.info(
                f'Page {page} is a subpage that is too deep. Skipping.')


class RegexFilter:

    """Regex filter."""

    @classmethod
    def __filter_match(cls, regex: Sequence[Pattern[str]],
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
    def __precompile(cls, regex: PATTERN_STR_OR_SEQ_TYPE,
                     flag: int) -> list[Pattern[str]]:
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
    def titlefilter(cls,
                    generator: Iterable[pywikibot.page.BasePage],
                    regex: PATTERN_STR_OR_SEQ_TYPE,
                    quantifier: str = 'any',
                    ignore_namespace: bool = True
                    ) -> Generator[pywikibot.page.BasePage, None, None]:
        """Yield pages from another generator whose title matches regex.

        Uses regex option re.IGNORECASE depending on the quantifier parameter.

        If ignore_namespace is False, the whole page title is compared.

        .. note:: if you want to check for a match at the beginning of
           the title, you have to start the regex with "^"

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
        reg = cls.__precompile(regex, re.IGNORECASE)
        for page in generator:
            title = page.title(with_ns=not ignore_namespace)
            if cls.__filter_match(reg, title, quantifier):
                yield page

    @classmethod
    def contentfilter(cls,
                      generator: Iterable[pywikibot.page.BasePage],
                      regex: PATTERN_STR_OR_SEQ_TYPE,
                      quantifier: str = 'any'
                      ) -> Generator[pywikibot.page.BasePage, None, None]:
        """Yield pages from another generator whose body matches regex.

        Uses regex option re.IGNORECASE depending on the quantifier parameter.

        For parameters see titlefilter above.
        """
        reg = cls.__precompile(regex, re.IGNORECASE | re.DOTALL)
        return (page for page in generator
                if cls.__filter_match(reg, page.text, quantifier))


def QualityFilterPageGenerator(
    generator: Iterable[pywikibot.page.BasePage],
    quality: list[int],
) -> Generator[pywikibot.page.BasePage, None, None]:
    """Wrap a generator to filter pages according to quality levels.

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


def CategoryFilterPageGenerator(
    generator: Iterable[pywikibot.page.BasePage],
    category_list: Sequence[pywikibot.page.Category],
) -> Generator[pywikibot.page.BasePage, None, None]:
    """Wrap a generator to filter pages by categories specified.

    :param generator: A generator object
    :param category_list: categories used to filter generated pages
    """
    for page in generator:
        if all(x in page.categories() for x in category_list):
            yield page


# name the generator methods
RegexFilterPageGenerator = RegexFilter.titlefilter
RegexBodyFilterPageGenerator = RegexFilter.contentfilter


class _Edit(NamedTuple):
    do_edit: datetime.datetime | None
    edit_start: datetime.datetime | None
    edit_end: datetime.datetime | None


def EdittimeFilterPageGenerator(
    generator: Iterable[pywikibot.page.BasePage],
    last_edit_start: datetime.datetime | None = None,
    last_edit_end: datetime.datetime | None = None,
    first_edit_start: datetime.datetime | None = None,
    first_edit_end: datetime.datetime | None = None,
    show_filtered: bool = False,
) -> Generator[pywikibot.page.BasePage, None, None]:
    """Wrap a generator to filter pages outside last or first edit range.

    :param generator: A generator object
    :param last_edit_start: Only yield pages last edited after this time
    :param last_edit_end: Only yield pages last edited before this time
    :param first_edit_start: Only yield pages first edited after this time
    :param first_edit_end: Only yield pages first edited before this time
    :param show_filtered: Output a message for each page not yielded
    """
    def to_be_yielded(edit: _Edit,
                      page: pywikibot.page.BasePage,
                      rev: pywikibot.page.Revision,
                      show_filtered: bool) -> bool:
        if not edit.do_edit:
            return True

        edit_time = rev.timestamp  # type: ignore[attr-defined]

        msg = (f'{type(edit).__name__} edit on {page} was on '
               f'{edit_time.isoformat()}.\nToo {{when}}. Skipping.')

        if edit_time < edit.edit_start:
            _output_if(show_filtered, msg.format(when='old'))
            return False

        if edit_time > edit.edit_end:
            _output_if(show_filtered, msg.format(when='recent'))
            return False

        return True

    latest_edit = _Edit(last_edit_start or last_edit_end,
                        last_edit_start or datetime.datetime.min,
                        last_edit_end or datetime.datetime.max)

    first_edit = _Edit(first_edit_start or first_edit_end,
                       first_edit_start or datetime.datetime.min,
                       first_edit_end or datetime.datetime.max)

    for page in generator or []:
        yield_for_last = to_be_yielded(latest_edit, page,
                                       page.latest_revision, show_filtered)
        yield_for_first = to_be_yielded(first_edit, page, page.oldest_revision,
                                        show_filtered)

        if yield_for_last and yield_for_first:
            yield page


def UserEditFilterGenerator(
    generator: Iterable[pywikibot.page.BasePage],
    username: str,
    timestamp: str | datetime.datetime | None = None,
    skip: bool = False,
    max_revision_depth: int | None = None,
    show_filtered: bool = False
) -> Generator[pywikibot.page.BasePage, None, None]:
    """Generator which will yield Pages modified by username.

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
    if timestamp is None:
        ts = None
    else:
        ts = pywikibot.Timestamp.set_timestamp(timestamp)

    for page in generator:
        contribs = page.contributors(total=max_revision_depth, endtime=ts)
        if bool(contribs[username]) is not bool(skip):  # xor operation
            yield page
        elif show_filtered:
            pywikibot.info(f'Skipping {page.title(as_link=True)}')


def WikibaseItemFilterPageGenerator(
    generator: Iterable[pywikibot.page.BasePage],
    has_item: bool = True,
    show_filtered: bool = False,
) -> Generator[pywikibot.page.BasePage, None, None]:
    """A wrapper generator used to exclude if page has a Wikibase item or not.

    :param generator: Generator to wrap.
    :param has_item: Exclude pages without an item if True, or only
        include pages without an item if False
    :param show_filtered: Output a message for each page not yielded
    :return: Wrapped generator
    """
    why = "doesn't" if has_item else 'has'
    msg = f'{{page}} {why} a wikidata item. Skipping.'

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
