#!/usr/bin/python
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

Todo
----
Please fix these if you are capable and motivated:

- if a file marked nowcommons is not present on Wikimedia Commons, the bot
  will exit.
"""
#
# (C) Pywikibot team, 2006-2021
#
# Distributed under the terms of the MIT license.
#
import sys
from itertools import chain

import pywikibot
from pywikibot import Bot, i18n
from pywikibot import pagegenerators as pg
from pywikibot.exceptions import IsRedirectPageError, NoPageError
from pywikibot.tools import filter_unique
from pywikibot.tools.formatter import color_format
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


class NowCommonsDeleteBot(Bot):

    """Bot to delete migrated files."""

    update_options = {
        'replace': False,
        'replacealways': False,
        'replaceloose': False,
        'replaceonly': False,
    }

    def __init__(self, **kwargs):
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
        gen = pg.PreloadingGenerator(gen)
        return gen

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

    def run(self):
        """Run the bot."""
        commons = self.commons
        comment = self.summary

        for page in self.generator:
            self.current_page = page
            try:
                local_file_page = pywikibot.FilePage(self.site, page.title())
                if local_file_page.file_is_shared():
                    pywikibot.output('File is already on Commons.')
                    continue
                sha1 = local_file_page.latest_file_info.sha1
                file_on_commons = self.find_file_on_commons(local_file_page)
                if not file_on_commons:
                    pywikibot.output('NowCommons template not found.')
                    continue
                commons_file_page = pywikibot.FilePage(commons, 'File:'
                                                       + file_on_commons)
                if (local_file_page.title(with_ns=False)
                        != commons_file_page.title(with_ns=False)):
                    using_pages = list(local_file_page.using_pages())
                    if using_pages and using_pages != [local_file_page]:
                        pywikibot.output(color_format(
                            '"{lightred}{0}{default}" '
                            'is still used in {1} pages.',
                            local_file_page.title(with_ns=False),
                            len(using_pages)))
                        if self.opt.replace:
                            pywikibot.output(color_format(
                                'Replacing "{lightred}{0}{default}" by '
                                '"{lightgreen}{1}{default}\".',
                                local_file_page.title(with_ns=False),
                                commons_file_page.title(with_ns=False)))
                            bot = ImageBot(
                                pg.FileLinksGenerator(local_file_page),
                                local_file_page.title(with_ns=False),
                                commons_file_page.title(with_ns=False),
                                always=self.opt.replacealways,
                                loose=self.opt.replaceloose)
                            bot.run()
                            # If the image is used with the urlname the
                            # previous function won't work
                            is_used = bool(list(pywikibot.FilePage(
                                self.site,
                                page.title()).using_pages(total=1)))
                            if is_used and self.opt.replaceloose:
                                bot = ImageBot(
                                    pg.FileLinksGenerator(local_file_page),
                                    local_file_page.title(with_ns=False,
                                                          as_url=True),
                                    commons_file_page.title(with_ns=False),
                                    always=self.opt.replacealways,
                                    loose=self.opt.replaceloose)
                                bot.run()
                            # refresh because we want the updated list
                            using_pages = len(list(pywikibot.FilePage(
                                self.site, page.title()).using_pages()))

                        else:
                            pywikibot.output('Please change them manually.')
                        continue
                    pywikibot.output(color_format(
                        'No page is using "{lightgreen}{0}{default}" '
                        'anymore.',
                        local_file_page.title(with_ns=False)))
                commons_text = commons_file_page.get()
                if not self.opt.replaceonly:
                    if sha1 == commons_file_page.latest_file_info.sha1:
                        pywikibot.output(
                            'The file is identical to the one on Commons.')
                        if len(local_file_page.get_file_history()) > 1:
                            pywikibot.output(
                                'This file has a version history. Please '
                                'delete it manually after making sure that '
                                'the old versions are not worth keeping.')
                            continue
                        if self.opt.always is False:
                            format_str = color_format(
                                '\n\n>>>> Description on {lightpurple}%s'
                                '{default} <<<<\n')
                            pywikibot.output(format_str % page.title())
                            pywikibot.output(local_file_page.get())
                            pywikibot.output(format_str %
                                             commons_file_page.title())
                            pywikibot.output(commons_text)
                            if pywikibot.input_yn(
                                    'Does the description on Commons contain '
                                    'all required source and license\n'
                                    'information?',
                                    default=False, automatic_quit=False):
                                local_file_page.delete(
                                    '{} [[:commons:File:{}]]'
                                    .format(comment, file_on_commons),
                                    prompt=False)
                        else:
                            local_file_page.delete(
                                comment + ' [[:commons:File:{}]]'
                                          .format(file_on_commons),
                                          prompt=False)
                    else:
                        pywikibot.output('The file is not identical to '
                                         'the one on Commons.')
            except (NoPageError, IsRedirectPageError) as e:
                pywikibot.output(str(e[0]))
                continue
            else:
                self._treat_counter += 1
        if not self._treat_counter:
            pywikibot.output('No transcluded files found for {}.'
                             .format(self.nc_templates_list()[0]))
        self.exit()


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
        elif arg.startswith('-'):
            if arg[1:] in ('always', 'replace', 'replaceloose', 'replaceonly'):
                options[arg[1:]] = True

    bot = NowCommonsDeleteBot(**options)
    bot.run()


if __name__ == '__main__':
    main()
