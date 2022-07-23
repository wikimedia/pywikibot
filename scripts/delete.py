#!/usr/bin/python3
"""
This script can be used to delete and undelete pages en masse.

Of course, you will need an admin account on the relevant wiki.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-always           Don't prompt to delete pages, just do it.

-summary:XYZ      Set the summary message text for the edit to XYZ.

-undelete         Actually undelete pages instead of deleting.
                  Obviously makes sense only with -page and -file.

-isorphan         Alert if there are pages that link to page to be
                  deleted (check 'What links here').
                  By default it is active and only the summary per namespace
                  is be given.
                  If given as -isorphan:n, n pages per namespace will be shown,
                  If given as -isorphan:0, only the summary per namespace will
                  be shown,
                  If given as -isorphan:n, with n < 0, the option is disabled.
                  This option is disregarded if -always is set.

-orphansonly:     Specified namespaces. Separate multiple namespace
                  numbers or names with commas.
                  Examples:

                  -orphansonly:0,2,4
                  -orphansonly:Help,MediaWiki

                  Note that Main ns can be indicated either with a 0 or a ',':

                  -orphansonly:0,1
                  -orphansonly:,Talk

Usage:

    python pwb.py delete [-category categoryName]

Examples
--------

Delete everything in the category "To delete" without prompting:

    python pwb.py delete -cat:"To delete" -always
"""
#
# (C) Pywikibot team, 2013-2022
#
# Distributed under the terms of the MIT license.
#
import collections

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.backports import DefaultDict, Set
from pywikibot.bot import CurrentPageBot
from pywikibot.page import Page
from pywikibot.site import Namespace
from pywikibot.tools.itertools import islice_with_ellipsis


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

RefTable = DefaultDict[Namespace, Page]


class PageWithRefs(Page):

    """
    A subclass of Page with convenience methods for reference checking.

    Supports the same interface as Page, with some added methods.
    """

    def __init__(self, source, title: str = '', ns=0) -> None:
        """Initializer."""
        super().__init__(source, title, ns)
        _cache_attrs = list(super()._cache_attrs)
        _cache_attrs = tuple(_cache_attrs + ['_ref_table'])

    def get_ref_table(self, *args, **kwargs) -> RefTable:
        """Build mapping table with pages which links the current page."""
        ref_table = collections.defaultdict(list)
        for page in self.getReferences(*args, **kwargs):
            ref_table[page.namespace()].append(page)
        return ref_table

    @property
    def ref_table(self) -> RefTable:
        """
        Build link reference table lazily.

        This property gives a default table without any parameter set for
        getReferences(), whereas self.get_ref_table() is able to accept
        parameters.
        """
        if not hasattr(self, '_ref_table'):
            self._ref_table = self.get_ref_table()
        return self._ref_table

    def namespaces_with_ref_to_page(self, namespaces=None) -> Set[Namespace]:
        """
        Check if current page has links from pages in namepaces.

        If namespaces is None, all namespaces are checked.
        Returns a set with namespaces where a ref to page is present.

        :param namespaces: Namespace to check
        :type namespaces: iterable of Namespace objects
        """
        if namespaces is None:
            namespaces = self.site.namespaces()

        return set(namespaces) & set(self.ref_table)


class DeletionRobot(CurrentPageBot):

    """This robot allows deletion of pages en masse."""

    update_options = {
        'undelete': False,
        'isorphan': 0,
        'orphansonly': [],
    }

    def __init__(self, summary: str, **kwargs) -> None:
        """Initializer.

        :param summary: the reason for the (un)deletion
        """
        super().__init__(**kwargs)

        self.summary = summary
        # Upcast pages to PageWithRefs()
        self.generator = (PageWithRefs(p) for p in self.generator)

    def display_references(self) -> None:
        """
        Display pages that link to the current page, sorted per namespace.

        Number of pages to display per namespace is provided by:
        - self.opt.isorphan
        """
        refs = self.current_page.ref_table
        if not refs:
            return

        total = sum(len(v) for v in refs.values())
        if total > 1:
            pywikibot.warning('There are {} pages that link to {}.'
                              .format(total, self.current_page))
        else:
            pywikibot.warning('There is a page that links to {}.'
                              .format(self.current_page))

        show_n_pages = self.opt.isorphan
        width = len(max((ns.canonical_prefix() for ns in refs), key=len))
        for ns in sorted(refs):
            n_pages_in_ns = len(refs[ns])
            plural = '' if n_pages_in_ns == 1 else 's'
            ns_name = ns.canonical_prefix() if ns != ns.MAIN else 'Main:'
            ns_id = '[{}]'.format(ns.id)
            pywikibot.output(
                '    {0!s:<{width}} {1:>6} {2:>10} page{pl}'.format(
                    ns_name, ns_id, n_pages_in_ns, width=width, pl=plural))
            if show_n_pages:  # do not show marker if 0 pages are requested.
                for page in islice_with_ellipsis(refs[ns], show_n_pages):
                    pywikibot.output('      {!s}'.format(page.title()))

    def skip_page(self, page) -> bool:
        """Skip the page under some conditions."""
        if self.opt.undelete and page.exists():
            pywikibot.output('Skipping: {} already exists.'.format(page))
            return True
        if not self.opt.undelete and not page.exists():
            pywikibot.output('Skipping: {} does not exist.'.format(page))
            return True
        return super().skip_page(page)

    def treat_page(self) -> None:
        """Process one page from the generator."""
        if self.opt.undelete:
            self.current_page.undelete(self.summary)
            self.counter['undelete'] += 1
        else:
            if (self.opt.isorphan is not False
                    and not self.opt.always):
                self.display_references()

            if self.opt.orphansonly:
                namespaces = self.opt.orphansonly
                ns_with_ref = self.current_page.namespaces_with_ref_to_page(
                    namespaces)
                ns_with_ref = sorted(ns_with_ref)
                if ns_with_ref:
                    ns_names = ', '.join(str(ns.id) for ns in ns_with_ref)
                    pywikibot.output(
                        'Skipping: {} is not orphan in ns: {}.'.format(
                            self.current_page, ns_names))
                    return  # Not an orphan, do not delete.

            if self.current_page.site.user() is None:
                self.current_page.site.login()
            res = self.current_page.delete(self.summary,
                                           not self.opt.always,
                                           self.opt.always,
                                           automatic_quit=True)
            if res > 0:
                self.counter['delete'] += 1
            elif res < 0:
                self.counter['marked-for-deletion'] += 1
            else:
                self.counter['no-action'] += 1


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    page_name = ''
    summary = None
    options = {}

    # read command line parameters
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    mysite = pywikibot.Site()

    for arg in local_args:

        if arg == '-always':
            options['always'] = True
        elif arg.startswith('-summary'):
            if len(arg) == len('-summary'):
                summary = pywikibot.input('Enter a reason for the deletion:')
            else:
                summary = arg[len('-summary:'):]
        elif arg.startswith('-undelete'):
            options['undelete'] = True
        elif arg.startswith('-isorphan'):
            options['isorphan'] = int(arg[10:]) if arg[10:] != '' else 0
            if options['isorphan'] < 0:
                options['isorphan'] = False
        elif arg.startswith('-orphansonly'):
            if arg[13:]:
                namespaces = mysite.namespaces.resolve(arg[13:].split(','))
            else:
                namespaces = mysite.namespaces
            options['orphansonly'] = namespaces
        else:
            gen_factory.handle_arg(arg)
            found = arg.find(':') + 1
            if found:
                page_name = arg[found:]

        if not summary:
            un = 'un' if 'undelete' in options else ''
            if page_name:
                if arg.startswith(('-cat', '-subcats')):
                    summary = i18n.twtranslate(mysite, 'delete-from-category',
                                               {'page': page_name})
                elif arg.startswith('-links'):
                    summary = i18n.twtranslate(mysite,
                                               un + 'delete-linked-pages',
                                               {'page': page_name})
                elif arg.startswith('-ref'):
                    summary = i18n.twtranslate(
                        mysite, 'delete-referring-pages', {'page': page_name})
                elif arg.startswith('-imageused'):
                    summary = i18n.twtranslate(mysite, un + 'delete-images',
                                               {'page': page_name})
            elif arg.startswith('-file'):
                summary = i18n.twtranslate(mysite, un + 'delete-from-file')

    generator = gen_factory.getCombinedGenerator()
    # We are just deleting pages, so we have no need of using a preloading
    # page generator to actually get the text of those pages.
    if generator:
        if summary is None:
            summary = pywikibot.input('Enter a reason for the {}deletion:'
                                      .format(['', 'un'][options
                                              .get('undelete', False)]))
        bot = DeletionRobot(summary, generator=generator, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
