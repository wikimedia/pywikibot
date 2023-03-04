"""Objects representing a MediaWiki page.

Various Wikibase pages are defined in ``page._wikibase.py``,
various pages for Proofread Extensions are defined in
``pywikibot.proofreadpage``.

.. note:: `Link` objects represent a wiki-page's title, while
   :class:`pywikibot.Page` objects (defined here) represent the page
   itself, including its contents.
"""
#
# (C) Pywikibot team, 2008-2023
#
# Distributed under the terms of the MIT license.
#

import pywikibot
from pywikibot import textlib
from pywikibot.exceptions import (
    Error,
    InterwikiRedirectPageError,
    IsNotRedirectPageError,
    IsRedirectPageError,
    NoPageError,
    UnknownExtensionError,
)
from pywikibot.page._basepage import BasePage
from pywikibot.page._toolforge import WikiBlameMixin
from pywikibot.tools import cached


__all__ = ['Page']


class Page(BasePage, WikiBlameMixin):

    """Page: A MediaWiki page."""

    def __init__(self, source, title: str = '', ns=0) -> None:
        """Instantiate a Page object."""
        if isinstance(source, pywikibot.site.BaseSite) and not title:
            raise ValueError('Title must be specified and not empty '
                             'if source is a Site.')
        super().__init__(source, title, ns)

    @property
    @cached
    def raw_extracted_templates(self):
        """Extract templates and parameters.

        This method is using
        :func:`textlib.extract_templates_and_params`.
        Disabled parts and whitespace are stripped, except for
        whitespace in anonymous positional arguments.

        :rtype: list of (str, OrderedDict)
        """
        return textlib.extract_templates_and_params(self.text, True, True)

    def templatesWithParams(self):  # noqa: N802
        """Return templates used on this Page.

        The templates are extracted by :meth:`raw_extracted_templates`,
        with positional arguments placed first in order, and each named
        argument appearing as 'name=value'.

        All parameter keys and values for each template are stripped of
        whitespace.

        :return: a list of tuples with one tuple for each template invocation
            in the page, with the template Page as the first entry and a list
            of parameters as the second entry.
        :rtype: list of (pywikibot.page.Page, list)
        """
        # WARNING: may not return all templates used in particularly
        # intricate cases such as template substitution
        titles = {t.title() for t in self.templates()}
        templates = self.raw_extracted_templates
        # backwards-compatibility: convert the dict returned as the second
        # element into a list in the format used by old scripts
        result = []
        for template in templates:
            try:
                link = pywikibot.Link(template[0], self.site,
                                      default_namespace=10)
                if link.canonical_title() not in titles:
                    continue
            except Error:
                # this is a parser function or magic word, not template name
                # the template name might also contain invalid parts
                continue
            args = template[1]
            intkeys = {}
            named = {}
            positional = []
            for key in sorted(args):
                try:
                    intkeys[int(key)] = args[key]
                except ValueError:
                    named[key] = args[key]

            for i in range(1, len(intkeys) + 1):
                # only those args with consecutive integer keys can be
                # treated as positional; an integer could also be used
                # (out of order) as the key for a named argument
                # example: {{tmp|one|two|5=five|three}}
                if i in intkeys:
                    positional.append(intkeys[i])
                    continue

                for k in intkeys:
                    if k < 1 or k >= i:
                        named[str(k)] = intkeys[k]
                break

            for item in named.items():
                positional.append('{}={}'.format(*item))
            result.append((pywikibot.Page(link, self.site), positional))
        return result

    def set_redirect_target(
        self,
        target_page,
        create: bool = False,
        force: bool = False,
        keep_section: bool = False,
        save: bool = True,
        **kwargs
    ):
        """
        Change the page's text to point to the redirect page.

        :param target_page: target of the redirect, this argument is required.
        :type target_page: pywikibot.Page or string
        :param create: if true, it creates the redirect even if the page
            doesn't exist.
        :param force: if true, it set the redirect target even the page
            doesn't exist or it's not redirect.
        :param keep_section: if the old redirect links to a section
            and the new one doesn't it uses the old redirect's section.
        :param save: if true, it saves the page immediately.
        :param kwargs: Arguments which are used for saving the page directly
            afterwards, like 'summary' for edit summary.
        """
        if isinstance(target_page, str):
            target_page = pywikibot.Page(self.site, target_page)
        elif self.site != target_page.site:
            raise InterwikiRedirectPageError(self, target_page)
        if not self.exists() and not (create or force):
            raise NoPageError(self)
        if self.exists() and not self.isRedirectPage() and not force:
            raise IsNotRedirectPageError(self)
        redirect_regex = self.site.redirect_regex
        if self.exists():
            old_text = self.get(get_redirect=True)
        else:
            old_text = ''
        result = redirect_regex.search(old_text)
        if result:
            oldlink = result[1]
            if (keep_section and '#' in oldlink
                    and target_page.section() is None):
                sectionlink = oldlink[oldlink.index('#'):]
                target_page = pywikibot.Page(
                    self.site,
                    target_page.title() + sectionlink
                )
            prefix = self.text[:result.start()]
            suffix = self.text[result.end():]
        else:
            prefix = ''
            suffix = ''

        target_link = target_page.title(as_link=True, textlink=True,
                                        allow_interwiki=False)
        target_link = f'#{self.site.redirect()} {target_link}'
        self.text = prefix + target_link + suffix
        if save:
            self.save(**kwargs)

    def get_best_claim(self, prop: str):
        """
        Return the first best Claim for this page.

        Return the first 'preferred' ranked Claim specified by Wikibase
        property or the first 'normal' one otherwise.

        .. versionadded:: 3.0

        :param prop: property id, "P###"
        :return: Claim object given by Wikibase property number
            for this page object.
        :rtype: pywikibot.Claim or None

        :raises UnknownExtensionError: site has no Wikibase extension
        """
        def find_best_claim(claims):
            """Find the first best ranked claim."""
            index = None
            for i, claim in enumerate(claims):
                if claim.rank == 'preferred':
                    return claim
                if index is None and claim.rank == 'normal':
                    index = i
            if index is None:
                index = 0
            return claims[index]

        if not self.site.has_data_repository:
            raise UnknownExtensionError(
                f'Wikibase is not implemented for {self.site}.')

        def get_item_page(func, *args):
            try:
                item_p = func(*args)
                item_p.get()
                return item_p
            except NoPageError:
                return None
            except IsRedirectPageError:
                return get_item_page(item_p.getRedirectTarget)

        item_page = get_item_page(pywikibot.ItemPage.fromPage, self)
        if item_page and prop in item_page.claims:
            return find_best_claim(item_page.claims[prop])
        return None
