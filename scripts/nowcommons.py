#!/usr/bin/env python3
r"""
Script to delete files that are also present on Wikimedia Commons.

Do not run this script on Wikimedia Commons itself. It works based on
a given array of templates defined below.

Files are downloaded and compared. If the files match, it can be deleted on
the source wiki. If multiple versions of the file exist, the script will not
delete. If the SHA1 comparison is not equal, the script will not delete.

A sysop rights on the local wiki is required if you want all features of
this script to work properly.

This script understands various command-line arguments:

    -always         run automatically, do not ask any questions. All files
                    that qualify for deletion are deleted. Reduced screen
                    output.

    -replace        replace links if the files are equal and the file names
                    differ

    -replacealways  replace links if the files are equal and the file names
                    differ without asking for confirmation

    -replaceloose   Do loose replacements. This will replace all occurrences
                    of the name of the file (and not just explicit file
                    syntax).  This should work to catch all instances of the
                    file, including where it is used as a template parameter
                    or in galleries. However, it can also make more mistakes.

    -replaceonly    Use this if you do not have a local sysop rights, but do
                    wish to replace links from the NowCommons template.

Example
-------

    python pwb.py nowcommons -replaceonly -replaceloose -replacealways -replace

.. note:: This script is a
   :py:obj:`ConfigParserBot <bot.ConfigParserBot>`. All options
   can be set within a settings file which is scripts.ini by default.
"""
#
# (C) Pywikibot team, 2006-2022
#
# Distributed under the terms of the MIT license.
#
import sys
from itertools import chain

import pywikibot
from pywikibot import i18n
from pywikibot import pagegenerators as pg
from pywikibot.bot import ConfigParserBot, CurrentPageBot
from pywikibot.exceptions import IsRedirectPageError, NoPageError
from pywikibot.tools.itertools import filter_unique
from scripts.image import ImageRobot as ImageBot


nowcommons = {
    '_default': [
        'NowCommons'
    ],
    'ar': [
        'الآن كومنز',
        'الآن كومونز',
    ],
    'de': [
        'NowCommons',
        'NC',
        'Nowcommons',
        'Now Commons',
        'NowCommons/Mängel',
        'NC/M',
    ],
    'en': [
        'NowCommons',
        'Ncd',
    ],
    'eo': [
        'Nun en komunejo',
        'NowCommons',
    ],
    'fa': [
        'موجود در انبار',
        'NowCommons',
    ],
    'fr': [
        'Image sur Commons',
        'DoublonCommons',
        'Déjà sur Commons',
        'Maintenant sur commons',
        'Désormais sur Commons',
        'NC',
        'NowCommons',
        'Nowcommons',
        'Sharedupload',
        'Sur Commons',
        'Sur Commons2',
    ],
    'he': [
        'גם בוויקישיתוף'
    ],
    'hu': [
        'Azonnali-commons',
        'NowCommons',
        'Nowcommons',
        'NC'
    ],
    'ia': [
        'OraInCommons'
    ],
    'it': [
        'NowCommons',
    ],
    'ja': [
        'NowCommons',
    ],
    'ko': [
        '공용중복',
        '공용 중복',
        'NowCommons',
        'Now Commons',
        'Nowcommons',
    ],
    'nds-nl': [
        'NoenCommons',
        'NowCommons',
    ],
    'nl': [
        'NuCommons',
        'Nucommons',
        'NowCommons',
        'Nowcommons',
        'NCT',
        'Nct',
    ],
    'ro': [
        'NowCommons'
    ],
    'ru': [
        'NowCommons',
        'NCT',
        'Nowcommons',
        'Now Commons',
        'Db-commons',
        'Перенесено на Викисклад',
        'На Викискладе',
    ],
    'sr': [
        'NowCommons',
        'На Остави',
    ],
    'zh': [
        'NowCommons',
        'Nowcommons',
        'NCT',
    ],
}

namespace_in_template = [
    'en',
    'ia',
    'it',
    'ja',
    'ko',
    'lt',
    'ro',
    'zh',
]


class NowCommonsDeleteBot(CurrentPageBot, ConfigParserBot):

    """Bot to delete migrated files.

    .. versionchanged:: 7.0
       NowCommonsDeleteBot is a ConfigParserBot
    """

    update_options = {
        'replace': False,
        'replacealways': False,
        'replaceloose': False,
        'replaceonly': False,
    }

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        self.site = pywikibot.Site()
        if not self.site.has_image_repository:
            sys.exit('There must be a file repository to run this script')
        self.commons = self.site.image_repository()
        if self.site == self.commons:
            sys.exit(
                'You cannot run this bot on file repository like Commons.')
        self.summary = i18n.twtranslate(self.site,
                                        'imagetransfer-nowcommons_notice')

    def nc_templates_list(self):
        """Return nowcommons templates."""
        if self.site.lang in nowcommons:
            return nowcommons[self.site.lang]
        return nowcommons['_default']

    @property
    def nc_templates(self):
        """A set of now commons template Page instances."""
        if not hasattr(self, '_nc_templates'):
            self._nc_templates = {pywikibot.Page(self.site, title, ns=10)
                                  for title in self.nc_templates_list()}
        return self._nc_templates

    @property
    def generator(self):
        """Generator method."""
        gens = (t.getReferences(follow_redirects=True, namespaces=[6],
                                only_template_inclusion=True)
                for t in self.nc_templates)
        gen = chain(*gens)
        gen = filter_unique(gen, key=lambda p: '{}:{}:{}'.format(*p._cmpkey()))
        return pg.PreloadingGenerator(gen)

    def find_file_on_commons(self, local_file_page):
        """Find filename on Commons."""
        for template_name, params in local_file_page.templatesWithParams():
            if template_name not in self.nc_templates:
                continue

            if not params:
                file_on_commons = local_file_page.title(with_ns=False)
            elif self.site.lang in namespace_in_template:
                skip = False
                file_on_commons = None
                for par in params:
                    val = par.split('=')
                    if len(val) == 1 and not skip:
                        file_on_commons = par[par.find(':') + 1:]
                        break
                    if val[0].strip() == '1':
                        file_on_commons = \
                            val[1].strip()[val[1].strip().find(':') + 1:]
                        break
                    skip = True
                if not file_on_commons:
                    file_on_commons = local_file_page.title(with_ns=False)
            else:
                val = params[0].split('=')
                if len(val) == 1:
                    file_on_commons = params[0].strip()
                else:
                    file_on_commons = val[1].strip()
            return file_on_commons

    def init_page(self, item: pywikibot.Page) -> pywikibot.FilePage:
        """Ensure that generator retrieves FilePage objects."""
        return pywikibot.FilePage(item)

    def skip_page(self, page) -> bool:
        """Skip shared files."""
        if page.file_is_shared():
            pywikibot.info('File is already on Commons.')
            return True

        return super().skip_page(page)

    def treat_page(self) -> None:
        """Treat a single page."""
        local_file_page = self.current_page
        file_on_commons = self.find_file_on_commons(local_file_page)

        if not file_on_commons:
            pywikibot.info('NowCommons template not found.')
            return

        commons_file_page = pywikibot.FilePage(self.commons,
                                               'File:' + file_on_commons)
        if (local_file_page.title(with_ns=False)
                != commons_file_page.title(with_ns=False)):
            using_pages = list(local_file_page.using_pages())

            if using_pages and using_pages != [local_file_page]:
                pywikibot.info(
                    '"<<lightred>>{}<<default>>" is still used in {} pages.'
                    .format(local_file_page.title(with_ns=False),
                            len(using_pages)))

                if self.opt.replace:
                    pywikibot.info(
                        'Replacing "<<lightred>>{}<<default>>" by '
                        '"<<lightgreen>>{}<<default>>".'
                        .format(local_file_page.title(with_ns=False),
                                commons_file_page.title(with_ns=False)))

                    bot = ImageBot(local_file_page.using_pages(),
                                   local_file_page.title(with_ns=False),
                                   commons_file_page.title(with_ns=False),
                                   always=self.opt.replacealways,
                                   loose=self.opt.replaceloose)
                    bot.run()

                    # If the image is used with the urlname
                    # the previous function won't work
                    if local_file_page.file_is_used and self.opt.replaceloose:
                        bot = ImageBot(local_file_page.using_pages(),
                                       local_file_page.title(with_ns=False,
                                                             as_url=True),
                                       commons_file_page.title(with_ns=False),
                                       always=self.opt.replacealways,
                                       loose=self.opt.replaceloose)
                        bot.run()
                    self.counter['replace'] += 1
                else:
                    pywikibot.info('Please change them manually.')
                return

            pywikibot.info(
                'No page is using "<<lightgreen>>{}<<default>>" anymore.'
                .format(local_file_page.title(with_ns=False)))

        try:
            commons_text = commons_file_page.get()
        except (NoPageError, IsRedirectPageError) as e:
            pywikibot.error(e)
            return

        if not self.opt.replaceonly:
            sha1 = local_file_page.latest_file_info.sha1
            if sha1 == commons_file_page.latest_file_info.sha1:
                pywikibot.info(
                    'The file is identical to the one on Commons.')

                if len(local_file_page.get_file_history()) > 1:
                    pywikibot.info(
                        'This file has a version history. Please '
                        'delete it manually after making sure that '
                        'the old versions are not worth keeping.')
                    return

                if self.opt.always is False:
                    format_str = (
                        '\n\n>>>> Description on '
                        '<<<lightpurple>>{}<<default>> <<<<\n'
                    )
                    pywikibot.info(
                        format_str.format(local_file_page.title()))
                    pywikibot.info(local_file_page.get())
                    pywikibot.info(
                        format_str.format(commons_file_page.title()))
                    pywikibot.info(commons_text)

                if self.opt.always or pywikibot.input_yn(
                    'Does the description on Commons contain all required '
                        'source and license\ninformation?', default=False):
                    local_file_page.delete(
                        '{} [[:commons:File:{}]]'
                        .format(self.summary, file_on_commons),
                        prompt=False)
                    self.counter['delete'] += 1
            else:
                pywikibot.info(
                    'The file is not identical to the one on Commons.')

    def teardown(self):
        """Show a message if no files were found."""
        if self.generator_completed and not self.counter['read']:
            pywikibot.info('No transcluded files found for {}.'
                           .format(self.nc_templates_list()[0]))


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}

    for arg in pywikibot.handle_args(args):
        if arg == '-replacealways':
            options['replace'] = True
            options['replacealways'] = True
        elif arg.startswith('-') and arg[1:] in ('always',
                                                 'replace',
                                                 'replaceloose',
                                                 'replaceonly'):
            options[arg[1:]] = True

    bot = NowCommonsDeleteBot(**options)
    bot.run()


if __name__ == '__main__':
    main()
