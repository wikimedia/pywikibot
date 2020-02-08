#!/usr/bin/python
# -*- coding: utf-8 -*-
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
                    of the name of the image (and not just explicit image
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
# (C) Wikipedian, 2006-2007
# (C) Siebrand Mazeland, 2007-2008
# (C) xqt, 2010-2020
# (C) Pywikibot team, 2006-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from itertools import chain
import sys

import pywikibot
from pywikibot import Bot, i18n
from pywikibot.exceptions import ArgumentDeprecationWarning
from pywikibot import pagegenerators as pg
from pywikibot.tools import filter_unique, issue_deprecation_warning
from pywikibot.tools.formatter import color_format

from scripts.image import ImageRobot as ImageBot

nowCommons = {
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

namespaceInTemplate = [
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

    def __init__(self, **kwargs):
        """Initializer."""
        self.availableOptions.update({
            'replace': False,
            'replacealways': False,
            'replaceloose': False,
            'replaceonly': False,
        })
        super(NowCommonsDeleteBot, self).__init__(**kwargs)

        self.site = pywikibot.Site()
        if not self.site.has_image_repository:
            sys.exit('There must be a file repository to run this script')
        self.commons = self.site.image_repository()
        if self.site == self.commons:
            sys.exit(
                'You cannot run this bot on file repository like Commons.')
        self.summary = i18n.twtranslate(self.site,
                                        'imagetransfer-nowcommons_notice')

    def ncTemplates(self):
        """Return nowcommons templates."""
        if self.site.lang in nowCommons:
            return nowCommons[self.site.lang]
        else:
            return nowCommons['_default']

    @property
    def nc_templates(self):
        """A set of now commons template Page instances."""
        if not hasattr(self, '_nc_templates'):
            self._nc_templates = {pywikibot.Page(self.site, title, ns=10)
                                  for title in self.ncTemplates()}
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

    def findFilenameOnCommons(self, localImagePage):
        """Find filename on Commons."""
        for templateName, params in localImagePage.templatesWithParams():
            if templateName not in self.nc_templates:
                continue

            if not params:
                filenameOnCommons = localImagePage.title(with_ns=False)
            elif self.site.lang in namespaceInTemplate:
                skip = False
                filenameOnCommons = None
                for par in params:
                    val = par.split('=')
                    if len(val) == 1 and not skip:
                        filenameOnCommons = par[par.index(':') + 1:]
                        break
                    if val[0].strip() == '1':
                        filenameOnCommons = \
                            val[1].strip()[val[1].strip().index(':') + 1:]
                        break
                    skip = True
                if not filenameOnCommons:
                    filenameOnCommons = localImagePage.title(with_ns=False)
            else:
                val = params[0].split('=')
                if len(val) == 1:
                    filenameOnCommons = params[0].strip()
                else:
                    filenameOnCommons = val[1].strip()
            return filenameOnCommons

    def run(self):
        """Run the bot."""
        commons = self.commons
        comment = self.summary

        for page in self.generator:
            self.current_page = page
            try:
                localImagePage = pywikibot.FilePage(self.site, page.title())
                if localImagePage.fileIsShared():
                    pywikibot.output('File is already on Commons.')
                    continue
                sha1 = localImagePage.latest_file_info.sha1
                filenameOnCommons = self.findFilenameOnCommons(localImagePage)
                if not filenameOnCommons:
                    pywikibot.output('NowCommons template not found.')
                    continue
                commonsImagePage = pywikibot.FilePage(commons, 'Image:'
                                                      + filenameOnCommons)
                if (localImagePage.title(with_ns=False)
                        != commonsImagePage.title(with_ns=False)):
                    usingPages = list(localImagePage.usingPages())
                    if usingPages and usingPages != [localImagePage]:
                        pywikibot.output(color_format(
                            '"{lightred}{0}{default}" '
                            'is still used in {1} pages.',
                            localImagePage.title(with_ns=False),
                            len(usingPages)))
                        if self.getOption('replace') is True:
                            pywikibot.output(color_format(
                                'Replacing "{lightred}{0}{default}" by '
                                '"{lightgreen}{1}{default}\".',
                                localImagePage.title(with_ns=False),
                                commonsImagePage.title(with_ns=False)))
                            bot = ImageBot(
                                pg.FileLinksGenerator(localImagePage),
                                localImagePage.title(with_ns=False),
                                commonsImagePage.title(with_ns=False),
                                '', self.getOption('replacealways'),
                                self.getOption('replaceloose'))
                            bot.run()
                            # If the image is used with the urlname the
                            # previous function won't work
                            is_used = bool(list(pywikibot.FilePage(
                                self.site,
                                page.title()).usingPages(total=1)))
                            if is_used and self.getOption('replaceloose'):
                                bot = ImageBot(
                                    pg.FileLinksGenerator(
                                        localImagePage),
                                    localImagePage.title(
                                        with_ns=False, as_url=True),
                                    commonsImagePage.title(with_ns=False),
                                    '', self.getOption('replacealways'),
                                    self.getOption('replaceloose'))
                                bot.run()
                            # refresh because we want the updated list
                            usingPages = len(list(pywikibot.FilePage(
                                self.site, page.title()).usingPages()))

                        else:
                            pywikibot.output('Please change them manually.')
                        continue
                    else:
                        pywikibot.output(color_format(
                            'No page is using "{lightgreen}{0}{default}" '
                            'anymore.',
                            localImagePage.title(with_ns=False)))
                commonsText = commonsImagePage.get()
                if self.getOption('replaceonly') is False:
                    if sha1 == commonsImagePage.latest_file_info.sha1:
                        pywikibot.output(
                            'The image is identical to the one on Commons.')
                        if len(localImagePage.get_file_history()) > 1:
                            pywikibot.output(
                                'This image has a version history. Please '
                                'delete it manually after making sure that '
                                'the old versions are not worth keeping.')
                            continue
                        if self.getOption('always') is False:
                            format_str = color_format(
                                '\n\n>>>> Description on {lightpurple}%s'
                                '{default} <<<<\n')
                            pywikibot.output(format_str % page.title())
                            pywikibot.output(localImagePage.get())
                            pywikibot.output(format_str %
                                             commonsImagePage.title())
                            pywikibot.output(commonsText)
                            if pywikibot.input_yn(
                                    'Does the description on Commons contain '
                                    'all required source and license\n'
                                    'information?',
                                    default=False, automatic_quit=False):
                                localImagePage.delete(
                                    '{0} [[:commons:Image:{1}]]'
                                    .format(comment, filenameOnCommons),
                                    prompt=False)
                        else:
                            localImagePage.delete(
                                comment + ' [[:commons:Image:{0}]]'
                                          .format(filenameOnCommons),
                                          prompt=False)
                    else:
                        pywikibot.output('The image is not identical to '
                                         'the one on Commons.')
            except (pywikibot.NoPage, pywikibot.IsRedirectPage) as e:
                pywikibot.output('{0}'.format(e[0]))
                continue
            else:
                self._treat_counter += 1
        if not self._treat_counter:
            pywikibot.output('No transcluded files found for {0}.'
                             .format(self.ncTemplates()[0]))
        self.exit()


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    options = {}

    for arg in pywikibot.handle_args(args):
        if arg == '-replacealways':
            options['replace'] = True
            options['replacealways'] = True
        elif arg == '-hash':  # T132303
            raise NotImplementedError(
                "The '-hash' argument is not implemented anymore.")
        elif arg == '-autonomous':
            issue_deprecation_warning('-autonomous', '-always', 2,
                                      ArgumentDeprecationWarning,
                                      since='20140724')
            options['always'] = True
        elif arg.startswith('-'):
            if arg[1:] in ('always', 'replace', 'replaceloose', 'replaceonly'):
                options[arg[1:]] = True

    bot = NowCommonsDeleteBot(**options)
    bot.run()


if __name__ == '__main__':
    main()
