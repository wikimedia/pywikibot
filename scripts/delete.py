#!/usr/bin/python
# -*- coding: utf-8 -*-
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

Examples:

Delete everything in the category "To delete" without prompting.

    python pwb.py delete -cat:"To delete" -always
"""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import collections

from warnings import warn

import pywikibot

from pywikibot import exceptions
from pywikibot import i18n, pagegenerators
from pywikibot.bot import MultipleSitesBot, CurrentPageBot
from pywikibot.page import Page
from pywikibot.tools import islice_with_ellipsis

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}


class PageWithRefs(Page):

    """
    A subclass of Page with convenience methods for reference checking.

    Supports the same interface as Page, with some added methods.
    """

    def __init__(self, source, title='', ns=0):
        """Constructor."""
        super(PageWithRefs, self).__init__(source, title, ns)
        _cache_attrs = list(super(PageWithRefs, self)._cache_attrs)
        _cache_attrs = tuple(_cache_attrs + ['_ref_table'])

    def get_ref_table(self, *args, **kwargs):
        """Build mapping table with pages which links the current page."""
        ref_table = collections.defaultdict(list)
        for page in self.getReferences(*args, **kwargs):
            ref_table[page.namespace()].append(page)
        return ref_table

    @property
    def ref_table(self):
        """
        Build link reference table lazily.

        This property gives a default table without any parameter set for
        getReferences(), whereas self.get_ref_table() is able to accept
        parameters.
        """
        if not hasattr(self, '_ref_table'):
            self._ref_table = self.get_ref_table()
        return self._ref_table

    def namespaces_with_ref_to_page(self, namespaces=None):
        """
        Check if current page has links from pages in namepaces.

        If namespaces is None, all namespaces are checked.
        Returns a set with namespaces where a ref to page is present.

        @param namespaces: Namespace to check
        @type namespaces: iterable of Namespace objects
        @rtype set: namespaces where a ref to page is present
        """
        if namespaces is None:
            namespaces = self.site.namespaces()

        return set(namespaces) & set(self.ref_table)


class DeletionRobot(MultipleSitesBot, CurrentPageBot):

    """This robot allows deletion of pages en masse."""

    def __init__(self, generator, summary, **kwargs):
        """
        Constructor.

        @param generator: the pages to work on
        @type generator: iterable
        @param summary: the reason for the (un)deletion
        @type summary: unicode
        """
        self.availableOptions.update({
            'undelete': False,
            'isorphan': 0,
            'orphansonly': [],
        })
        super(DeletionRobot, self).__init__(generator=generator, **kwargs)

        self.summary = summary
        # Upcast pages to PageWithRefs()
        self.generator = (PageWithRefs(p) for p in self.generator)

    def display_references(self):
        """
        Display pages which links the current page, sorted per namespace.

        Number of pages to display per namespace is provided by:
        - self.getOption('isorphan')
        """
        refs = self.current_page.ref_table
        if refs:
            total = sum(len(v) for v in refs.values())
            pywikibot.warning('There are %d pages who link to %s.'
                              % (total, self.current_page))
        else:
            return

        show_n_pages = self.getOption('isorphan')
        width = len(max((ns.canonical_prefix() for ns in refs), key=len))
        for ns in sorted(refs):
            n_pages_in_ns = len(refs[ns])
            plural = '' if n_pages_in_ns == 1 else 's'
            ns_name = ns.canonical_prefix() if ns != ns.MAIN else 'Main:'
            ns_id = '[{0}]'.format(ns.id)
            pywikibot.output(
                '    {0!s:<{width}} {1:>6} {2:>10} page{pl}'.format(
                    ns_name, ns_id, n_pages_in_ns, width=width, pl=plural))
            if show_n_pages:  # do not show marker if 0 pages are requested.
                for page in islice_with_ellipsis(refs[ns], show_n_pages):
                    pywikibot.output('      {0!s}'.format(page.title()))

    def treat_page(self):
        """Process one page from the generator."""
        if self.getOption('undelete'):
            if self.current_page.exists():
                pywikibot.output(u'Skipping: {0} already exists.'.format(
                    self.current_page))
            else:
                self.current_page.undelete(self.summary)
        else:
            if self.current_page.exists():

                if (self.getOption('isorphan') is not False and
                        not self.getOption('always')):
                    self.display_references()

                if self.getOption('orphansonly'):
                    namespaces = self.getOption('orphansonly')
                    ns_with_ref = self.current_page.namespaces_with_ref_to_page(
                        namespaces)
                    ns_with_ref = sorted(list(ns_with_ref))
                    if ns_with_ref:
                        ns_names = ', '.join(str(ns.id) for ns in ns_with_ref)
                        pywikibot.output(
                            'Skipping: {0} is not orphan in ns: {1}.'.format(
                                self.current_page, ns_names))
                        return  # Not an orphan, do not delete.

                self.current_page.delete(self.summary,
                                         not self.getOption('always'),
                                         self.getOption('always'),
                                         quit=True)
            else:
                pywikibot.output(u'Skipping: {0} does not exist.'.format(
                    self.current_page))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    pageName = ''
    summary = None
    generator = None
    options = {}

    # read command line parameters
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()
    mysite = pywikibot.Site()

    for arg in local_args:

        if arg == '-always':
            options['always'] = True
        elif arg.startswith('-summary'):
            if len(arg) == len('-summary'):
                summary = pywikibot.input(u'Enter a reason for the deletion:')
            else:
                summary = arg[len('-summary:'):]
        elif arg.startswith('-images'):
            warn('-image option is deprecated. Please use -imageused instead.',
                 exceptions.ArgumentDeprecationWarning)
            local_args.append('-imageused' + arg[7:])
        elif arg.startswith('-undelete'):
            options['undelete'] = True
        elif arg.startswith('-isorphan'):
            options['isorphan'] = int(arg[10:]) if arg[10:] != '' else 0
            if options['isorphan'] < 0:
                options['isorphan'] = False
        elif arg.startswith('-orphansonly'):
            if arg[13:]:
                namespaces = mysite.namespaces.resolve(arg[13:].split(","))
            else:
                namespaces = mysite.namespaces
            options['orphansonly'] = namespaces
        else:
            genFactory.handleArg(arg)
            found = arg.find(':') + 1
            if found:
                pageName = arg[found:]

        if not summary:
            un = 'un' if 'undelete' in options else ''
            if pageName:
                if arg.startswith('-cat') or arg.startswith('-subcats'):
                    summary = i18n.twtranslate(mysite, 'delete-from-category',
                                               {'page': pageName})
                elif arg.startswith('-links'):
                    summary = i18n.twtranslate(mysite,
                                               un + 'delete-linked-pages',
                                               {'page': pageName})
                elif arg.startswith('-ref'):
                    summary = i18n.twtranslate(mysite, 'delete-referring-pages',
                                               {'page': pageName})
                elif arg.startswith('-imageused'):
                    summary = i18n.twtranslate(mysite, un + 'delete-images',
                                               {'page': pageName})
            elif arg.startswith('-file'):
                summary = i18n.twtranslate(mysite, un + 'delete-from-file')

    generator = genFactory.getCombinedGenerator()
    # We are just deleting pages, so we have no need of using a preloading
    # page generator to actually get the text of those pages.
    if generator:
        if summary is None:
            summary = pywikibot.input(u'Enter a reason for the %sdeletion:'
                                      % ['', 'un'][options.get('undelete',
                                                               False)])
        bot = DeletionRobot(generator, summary, **options)
        bot.run()
        return True
    else:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False


if __name__ == "__main__":
    main()
