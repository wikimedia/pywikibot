#!/usr/bin/python
r"""
Print a list of pages, as defined by page generator parameters.

Optionally, it also prints page content to STDOUT or save it to a file
in the current directory.

These parameters are supported to specify which pages titles to print:

-format     Defines the output format.

            Can be a custom string according to python string.format() notation
            or can be selected by a number from following list
            (1 is default format):
            1 - '{num:4d} {page.title}'
                --> 10 PageTitle

            2 - '{num:4d} [[{page.title}]]'
                --> 10 [[PageTitle]]

            3 - '{page.title}'
                --> PageTitle

            4 - '[[{page.title}]]'
                --> [[PageTitle]]

            5 - '{num:4d} \03{{lightred}}{page.loc_title:<40}\03{{default}}'
                --> 10 localised_Namespace:PageTitle (colorised in lightred)

            6 - '{num:4d} {page.loc_title:<40} {page.can_title:<40}'
                --> 10 localised_Namespace:PageTitle
                       canonical_Namespace:PageTitle

            7 - '{num:4d} {page.loc_title:<40} {page.trs_title:<40}'
                --> 10 localised_Namespace:PageTitle
                       outputlang_Namespace:PageTitle
                (*) requires "outputlang:lang" set.

            num is the sequential number of the listed page.

            An empty format is equal to -notitle and just shows the total
            amount of pages.

-outputlang Language for translation of namespaces.

-notitle    Page title is not printed.

-get        Page content is printed.

-save       Save Page content to a file named as page.title(as_filename=True).
            Directory can be set with -save:dir_name
            If no dir is specified, current directory will be used.

-encode     File encoding can be specified with '-encode:name' (name must be
            a valid python encoding: utf-8, etc.).
            If not specified, it defaults to config.textfile_encoding.

-put:       Save the list to the defined page of the wiki. By default it does
            not overwrite an existing page.

-overwrite  Overwrite the page if it exists. Can only by applied with -put.

-summary:   The summary text when the page is written. If it's one word just
            containing letters, dashes and underscores it uses that as a
            translation key.

Custom format can be applied to the following items extrapolated from a
page object:

    site: obtained from page._link._site.

    title: obtained from page._link._title.

    loc_title: obtained from page._link.canonical_title().

    can_title: obtained from page._link.ns_title().
        based either the canonical namespace name or on the namespace name
        in the language specified by the -trans param;
        a default value '******' will be used if no ns is found.

    onsite: obtained from pywikibot.Site(outputlang, self.site.family).

    trs_title: obtained from page._link.ns_title(onsite=onsite).
        If selected format requires trs_title, outputlang must be set.


&params;
"""
#
# (C) Pywikibot team, 2008-2021
#
# Distributed under the terms of the MIT license.
#
import os
import re

import pywikibot
from pywikibot import config, i18n
from pywikibot.exceptions import Error
from pywikibot.pagegenerators import GeneratorFactory, parameterHelp


docuReplacements = {'&params;': parameterHelp}  # noqa: N816


class Formatter:

    """Structure with Page attributes exposed for formatting from cmd line."""

    fmt_options = {
        '1': '{num:4d} {page.title}',
        '2': '{num:4d} [[{page.title}]]',
        '3': '{page.title}',
        '4': '[[{page.title}]]',
        '5': '{num:4d} \03{{lightred}}{page.loc_title:<40}\03{{default}}',
        '6': '{num:4d} {page.loc_title:<40} {page.can_title:<40}',
        '7': '{num:4d} {page.loc_title:<40} {page.trs_title:<40}',
    }

    # Identify which formats need outputlang
    fmt_need_lang = [k for k, v in fmt_options.items() if 'trs_title' in v]

    def __init__(self, page, outputlang=None, default='******') -> None:
        """
        Initializer.

        :param page: the page to be formatted.
        :type page: Page object.
        :param outputlang: language code in which namespace before title should
            be translated.

            Page ns will be searched in Site(outputlang, page.site.family)
            and, if found, its custom name will be used in page.title().

        :type outputlang: str or None, if no translation is wanted.
        :param default: default string to be used if no corresponding
            namespace is found when outputlang is not None.

        """
        self.site = page._link.site
        self.title = page._link.title
        self.loc_title = page._link.canonical_title()
        self.can_title = page._link.ns_title()
        self.outputlang = outputlang
        if outputlang is not None:
            # Cache onsite in case of translations.
            if not hasattr(self, 'onsite'):
                self.onsite = pywikibot.Site(outputlang, self.site.family)
            try:
                self.trs_title = page._link.ns_title(onsite=self.onsite)
            # Fallback if no corresponding namespace is found in onsite.
            except Error:
                self.trs_title = '{}:{}'.format(default, page._link.title)

    def output(self, num=None, fmt='1') -> str:
        """Output formatted string."""
        fmt = self.fmt_options.get(fmt, fmt)
        # If selected format requires trs_title, outputlang must be set.
        if (fmt in self.fmt_need_lang
                or 'trs_title' in fmt
                and self.outputlang is None):
            raise ValueError(
                "Required format code needs 'outputlang' parameter set.")
        if num is None:
            return fmt.format(page=self)
        return fmt.format(num=num, page=self)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    notitle = False
    fmt = '1'
    outputlang = None
    page_get = False
    base_dir = None
    encoding = config.textfile_encoding
    page_target = None
    overwrite = False
    summary = 'listpages-save-list'

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen_factory = GeneratorFactory()

    for arg in local_args:
        option, sep, value = arg.partition(':')
        if option == '-notitle':
            notitle = True
        elif option == '-format':
            fmt = value.replace('\\03{{', '\03{{')
            if not fmt.strip():
                notitle = True
        elif option == '-outputlang':
            outputlang = value
        elif option == '-get':
            page_get = True
        elif option == '-save':
            base_dir = value or '.'
        elif option == '-encode':
            encoding = value
        elif option == '-put':
            page_target = value
        elif option == '-overwrite':
            overwrite = True
        elif option == '-summary':
            summary = value
        else:
            gen_factory.handle_arg(arg)

    if base_dir:
        base_dir = os.path.expanduser(base_dir)
        if not os.path.isabs(base_dir):
            base_dir = os.path.normpath(os.path.join(os.getcwd(), base_dir))

        if not os.path.exists(base_dir):
            pywikibot.output('Directory "{}" does not exist.'
                             .format(base_dir))
            choice = pywikibot.input_yn(
                'Do you want to create it ("No" to continue without saving)?')
            if choice:
                os.makedirs(base_dir, mode=0o744)
            else:
                base_dir = None
        elif not os.path.isdir(base_dir):
            # base_dir is a file.
            pywikibot.warning('Not a directory: "{}"\n'
                              'Skipping saving ...'
                              .format(base_dir))
            base_dir = None

    if page_target:
        site = pywikibot.Site()
        page_target = pywikibot.Page(site, page_target)
        if not overwrite and page_target.exists():
            pywikibot.bot.suggest_help(
                additional_text='Page {} already exists.\n'
                                'You can use the -overwrite argument to '
                                'replace the content of this page.'
                                .format(page_target.title(as_link=True)))
            return
        if re.match('[a-z_-]+$', summary):
            summary = i18n.twtranslate(site, summary)

    gen = gen_factory.getCombinedGenerator()
    if gen:
        i = 0
        output_list = []
        for i, page in enumerate(gen, start=1):
            if not notitle:
                page_fmt = Formatter(page, outputlang)
                output_list += [page_fmt.output(num=i, fmt=fmt)]
            if page_get:
                if output_list:
                    pywikibot.stdout(output_list.pop(-1))
                try:
                    pywikibot.stdout(page.text)
                except Error as err:
                    pywikibot.output(err)
            if base_dir:
                filename = os.path.join(base_dir, page.title(as_filename=True))
                pywikibot.output('Saving {} to {}'
                                 .format(page.title(), filename))
                with open(filename, mode='wb') as f:
                    f.write(page.text.encode(encoding))
        text = '\n'.join(output_list)
        if page_target:
            page_target.text = text
            page_target.save(summary=summary)
        pywikibot.stdout(text)
        pywikibot.output('{} page(s) found'.format(i))
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
