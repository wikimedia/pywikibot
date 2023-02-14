#!/usr/bin/env python3
"""
This script can be used to change one image to another or remove an image.

Syntax:

    python pwb.py image image_name [new_image_name]

If only one command-line parameter is provided then that image will be removed;
if two are provided, then the first image will be replaced by the second one on
all pages.

Command line options:

-summary:  Provide a custom edit summary. If the summary includes spaces,
           surround it with single quotes, such as:
           -summary:'My edit summary'
-always    Don't prompt to make changes, just do them.
-loose     Do loose replacements. This will replace all occurrences of the name
           of the image (and not just explicit image syntax). This should work
           to catch all instances of the image, including where it is used as a
           template parameter or in image galleries. However, it can also make
           more mistakes. This only works with image replacement, not image
           removal.

Examples
--------

The image "FlagrantCopyvio.jpg" is about to be deleted, so let's first remove
it from everything that displays it:

    python pwb.py image FlagrantCopyvio.jpg

The image "Flag.svg" has been uploaded, making the old "Flag.jpg" obsolete:

    python pwb.py image Flag.jpg Flag.svg

"""
#
# (C) Pywikibot team, 2013-2022
#
# Distributed under the terms of the MIT license.
#
import re

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import SingleSiteBot
from pywikibot.textlib import case_escape, ignore_case
from scripts.replace import ReplaceRobot as ReplaceBot


class ImageRobot(ReplaceBot):

    """This bot will replace or remove all occurrences of an old image."""

    def __init__(self, generator, old_image: str,
                 new_image: str = '', **kwargs) -> None:
        """
        Initializer.

        :param generator: the pages to work on
        :type generator: iterable
        :param old_image: the title of the old image (without namespace)
        :param new_image: the title of the new image (without namespace), or
                          None if you want to remove the image
        """
        self.available_options.update({
            'summary': None,
            'loose': False,
        })

        SingleSiteBot.__init__(self, **kwargs)

        self.old_image = old_image
        self.new_image = new_image
        param = {
            'old': self.old_image,
            'new': self.new_image,
            'file': self.old_image,
        }

        summary = self.opt.summary or i18n.twtranslate(
            self.site, 'image-replace' if self.new_image else 'image-remove',
            param)

        namespace = self.site.namespaces[6]
        escaped = case_escape(namespace.case, self.old_image)

        # Be careful, spaces and _ have been converted to '\ ' and '\_'
        escaped = re.sub('\\\\[_ ]', '[_ ]', escaped)
        if not self.opt.loose or not self.new_image:
            image_regex = re.compile(
                r'\[\[ *(?:{})\s*:\s*{} *(?P<parameters>\|'
                r'(?:[^\[\]]|\[\[[^\]]+\]\]|\[[^\]]+\])*|) *\]\]'
                .format('|'.join(ignore_case(s) for s in namespace), escaped))
        else:
            image_regex = re.compile(r'' + escaped)

        replacements = []
        if not self.opt.loose and self.new_image:
            replacements.append((image_regex,
                                 '[[{}:{}\\g<parameters>]]'
                                 .format(
                                     self.site.namespaces.FILE.custom_name,
                                     self.new_image)))
        else:
            replacements.append((image_regex, self.new_image))

        super().__init__(generator, replacements,
                         always=self.opt.always,
                         site=self.site,
                         summary=summary)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    old_image = ''
    new_image = ''
    options = {}

    for argument in pywikibot.handle_args(args):
        arg, _, value = argument.partition(':')
        if arg in ('-always', '-loose'):
            options[arg[1:]] = True
        elif arg == '-summary':
            options[arg[1:]] = value or pywikibot.input(
                'Choose an edit summary: ')
        elif old_image:
            new_image = arg
        else:
            old_image = arg

    if old_image:
        site = pywikibot.Site()
        old_imagepage = pywikibot.FilePage(site, old_image)
        gen = old_imagepage.using_pages()
        preloading_gen = pagegenerators.PreloadingGenerator(gen)
        bot = ImageRobot(preloading_gen, old_image, new_image,
                         site=site, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_parameters=['old image'])


if __name__ == '__main__':
    main()
