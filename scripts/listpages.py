#!/usr/bin/env python3
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

            5 - '{num:4d} <<lightred>>{page.loc_title:<40}<<default>>'
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
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import os

import pywikibot
from pywikibot import config
from pywikibot.bot import AutomaticTWSummaryBot, SingleSiteBot, suggest_help
from pywikibot.exceptions import ArgumentDeprecationWarning, Error
from pywikibot.pagegenerators import GeneratorFactory, parameterHelp
from pywikibot.tools import issue_deprecation_warning


docuReplacements = {'&params;': parameterHelp}  # noqa: N816


class Formatter:

    """Structure with Page attributes exposed for formatting from cmd line."""

    fmt_options = {
        '1': '{num:4d} {page.title}',
        '2': '{num:4d} [[{page.title}]]',
        '3': '{page.title}',
        '4': '[[{page.title}]]',
        '5': '{num:4d} <<lightred>>{page.loc_title:<40}<<default>>',
        '6': '{num:4d} {page.loc_title:<40} {page.can_title:<40}',
        '7': '{num:4d} {page.loc_title:<40} {page.trs_title:<40}',
    }

    # Identify which formats need outputlang
    fmt_need_lang = [k for k, v in fmt_options.items() if 'trs_title' in v]

    def __init__(self, page, outputlang=None, default: str = '******') -> None:
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
                self.trs_title = f'{default}:{page._link.title}'

    def output(self, num=None, fmt: str = '1') -> str:
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


class ListPagesBot(AutomaticTWSummaryBot, SingleSiteBot):

    """Print a list of pages."""

    summary_key = 'listpages-save-list'

    available_options = {
        'always': True,
        'save': None,
        'encode': config.textfile_encoding,
        'format': '1',
        'notitle': False,
        'outputlang': None,
        'overwrite': False,
        'preloading': None,
        'summary': '',
        'get': False,
        'put': None,
    }

    def treat(self, page) -> None:
        """Process one page and add it to the `output_list`."""
        self.num += 1
        if not self.opt.notitle:
            page_fmt = Formatter(page, self.opt.outputlang)
            self.output_list += [page_fmt.output(num=self.num,
                                                 fmt=self.opt.format)]
        if self.opt['get']:
            try:
                pywikibot.stdout(page.text)
            except Error as err:
                pywikibot.error(err)

        if self.opt.save:
            filename = os.path.join(self.opt.save,
                                    page.title(as_filename=True))
            pywikibot.info(f'Saving {page.title()} to {filename}')
            with open(filename, mode='wb') as f:
                f.write(page.text.encode(self.opt.encode))
            self.counter['save'] += 1

        if self.opt.preloading is False:
            pywikibot.stdout(self.output_list[-1]
                             if self.opt.put else self.output_list.pop())

    def setup(self) -> None:
        """Initialize `output_list` and `num` and adjust base directory."""
        self.output_list = []
        self.num = 0

        if self.opt.save is not None:
            base_dir = os.path.expanduser(self.opt.save or '.')
            if not os.path.isabs(base_dir):
                base_dir = os.path.normpath(os.path.join(os.getcwd(),
                                                         base_dir))

            if not os.path.exists(base_dir):
                pywikibot.info('Directory "{}" does not exist.'
                               .format(base_dir))
                choice = pywikibot.input_yn('Do you want to create it ("No" '
                                            'to continue without saving)?')
                if choice:
                    os.makedirs(base_dir,
                                mode=config.private_folder_permission)
                else:
                    base_dir = None
            elif not os.path.isdir(base_dir):
                # base_dir is a file.
                pywikibot.warning('Not a directory: "{}"\nSkipping saving ...'
                                  .format(base_dir))
                base_dir = None
            self.opt.save = base_dir

    def teardown(self) -> None:
        """Print the list and put it to the target page if specified."""
        text = '\n'.join(self.output_list)
        if self.opt.put:
            self.current_page = self.opt.put
            self.put_current(text, summary=self.opt.summary, show_diff=False)

        if self.opt.preloading is True:
            pywikibot.stdout(text)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    page_target = None

    additional_text = ''
    unknown_args = []

    # Process global args and generator args
    gen_factory = GeneratorFactory()
    local_args = pywikibot.handle_args(args)
    local_args = gen_factory.handle_args(local_args)

    for arg in local_args:
        option, _, value = arg.partition(':')
        opt = option[1:]
        if option in ('-get', '-notitle', '-overwrite'):
            options[opt] = True
        elif option == '-format':
            if '\\03{{' not in value:
                fmt = value
            else:
                fmt = value.replace('\\03{{', '\03{{')
                issue_deprecation_warning(
                    'old color format variant like \03{color}',
                    'new color format like <<color>>',
                    warning_class=ArgumentDeprecationWarning,
                    since='7.3.0')
            if not fmt.strip():
                options['notitle'] = True
            options['format'] = fmt
        elif option in ('-encode', '-outputlang', '-save', '-summary'):
            options[opt] = value
        elif option == '-put':
            page_target = value
        else:
            unknown_args.append(arg)

    site = pywikibot.Site()
    if page_target:
        page_target = pywikibot.Page(site, page_target)
        if not options.get('overwrite') and page_target.exists():
            additional_text = ('Page {} already exists.\n'
                               'You can use the -overwrite argument to '
                               'replace the content of this page.'
                               .format(page_target))

    gen = gen_factory.getCombinedGenerator()
    options['preloading'] = gen_factory.is_preloading
    if not suggest_help(missing_generator=not gen,
                        unknown_parameters=unknown_args,
                        additional_text=additional_text):
        bot = ListPagesBot(site=site, generator=gen, put=page_target,
                           **options)
        bot.run()


if __name__ == '__main__':
    main()
