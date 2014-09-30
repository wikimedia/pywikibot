# -*- coding: utf-8  -*-
r"""
Print a list of pages, as defined by page generator parameters.

Optionally, it also prints page content to STDOUT.

These parameters are supported to specify which pages titles to print:

-format  Defines the output format.

         Can be a custom string according to python string.format() notation or
         can be selected by a number from following list (1 is default format):
         1 - u'{num:4d} {page.title}'
             --> 10 PageTitle

         2 - u'{num:4d} {[[page.title]]}'
             --> 10 [[PageTitle]]

         3 - u'{page.title}'
             --> PageTitle

         4 - u'{[[page.title]]}'
             --> [[PageTitle]]

         5 - u'{num:4d} \03{{lightred}}{page.loc_title:<40}\03{{default}}'
             --> 10 PageTitle (colorised in lightred)

         6 - u'{num:4d} {page.loc_title:<40} {page.can_title:<40}'
             --> 10 localised_Namespace:PageTitle canonical_Namespace:PageTitle

         7 - u'{num:4d} {page.loc_title:<40} {page.trs_title:<40}'
             --> 10 localised_Namespace:PageTitle outputlang_Namespace:PageTitle
             (*) requires "outputlang:lang" set.

         num is the sequential number of the listed page.

-outputlang   Language for translation of namespaces

-notitle Page title is not printed.

-get     Page content is printed.


Custom format can be applied to the following items extrapolated from a
    page object:

    site: obtained from page._link._site

    title: obtained from page._link._title

    loc_title: obtained from page._link.canonical_title()

    can_title: obtained from page._link.ns_title()
        based either the canonical namespace name or on the namespace name
        in the language specified by the -trans param;
        a default value '******' will be used if no ns is found.

    onsite: obtained from pywikibot.Site(outputlang, self.site.family)

    trs_title: obtained from page._link.ns_title(onsite=onsite)


&params;
"""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#


import pywikibot
from pywikibot.pagegenerators import GeneratorFactory, parameterHelp

docuReplacements = {'&params;': parameterHelp}


class Formatter(object):

    """Structure with Page attributes exposed for formatting from cmd line."""

    fmt_options = {
        '1': u"{num:4d} {page.title}",
        '2': u"{num:4d} [[{page.title}]]",
        '3': u"{page.title}",
        '4': u"[[{page.title}]]",
        '5': u"{num:4d} \03{{lightred}}{page.loc_title:<40}\03{{default}}",
        '6': u"{num:4d} {page.loc_title:<40} {page.can_title:<40}",
        '7': u"{num:4d} {page.loc_title:<40} {page.trs_title:<40}",
    }

    # Identify which formats need outputlang
    fmt_need_lang = [k for k, v in fmt_options.items() if 'trs_title' in v]

    def __init__(self, page, outputlang=None, default='******'):
        """
        Constructor.

        @param page: the page to be formatted.
        @type page: Page object.
        @param outputlang: language code in which namespace before title should
            be translated.

            Page namespace will be searched in Site(outputlang, page.site.family)
            and, if found, its custom name will be used in page.title().

        @type outputlang: str or None, if no translation is wanted.
        @param default: default string to be used if no corresponding namespace
            is found when outputlang is not None.

        """
        self.site = page._link.site
        self.title = page._link.title
        self.loc_title = page._link.canonical_title()
        self.can_title = page._link.ns_title()
        self.outputlang = outputlang
        if outputlang is not None:
            # Cache onsite in case of tranlations.
            if not hasattr(self, "onsite"):
                self.onsite = pywikibot.Site(outputlang, self.site.family)
            try:
                self.trs_title = page._link.ns_title(onsite=self.onsite)
            # Fallback if no corresponding namespace is found in onsite.
            except pywikibot.Error:
                self.trs_title = u'%s:%s' % (default, page._link.title)

    def output(self, num=None, fmt=1):
        """Output formatted string."""
        fmt = self.fmt_options.get(fmt, fmt)
        # If selected format requires trs_title, outputlang must be set.
        if (fmt in self.fmt_need_lang or
                'trs_title' in fmt and
                self.outputlang is None):
            raise ValueError(
                u"Required format code needs 'outputlang' parameter set.")
        if num is None:
            return fmt.format(page=self)
        else:
            return fmt.format(num=num, page=self)


def main(*args):
    """Main function."""
    gen = None
    notitle = False
    fmt = '1'
    outputlang = None
    page_get = False

    # Process global args and prepare generator args parser
    local_args = pywikibot.handleArgs(*args)
    genFactory = GeneratorFactory()

    for arg in local_args:
        if arg == '-notitle':
            notitle = True
        elif arg.startswith("-format:"):
            fmt = arg[len("-format:"):]
            fmt = fmt.replace(u'\\03{{', u'\03{{')
        elif arg.startswith("-outputlang:"):
            outputlang = arg[len("-outputlang:"):]
        elif arg == '-get':
            page_get = True
        else:
            genFactory.handleArg(arg)

    gen = genFactory.getCombinedGenerator()
    if gen:
        for i, page in enumerate(gen, start=1):
            if not notitle:
                page_fmt = Formatter(page, outputlang)
                pywikibot.stdout(page_fmt.output(num=i, fmt=fmt))
            if page_get:
                # TODO: catch exceptions
                pywikibot.output(page.text, toStdout=True)
    else:
        pywikibot.showHelp()


if __name__ == "__main__":
    main()
