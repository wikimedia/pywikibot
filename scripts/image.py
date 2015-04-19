#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script can be used to change one image to another or remove an image.

Syntax: python image.py image_name [new_image_name]

If only one command-line parameter is provided then that image will be removed;
if two are provided, then the first image will be replaced by the second one on
all pages.

Command line options:

-summary:  Provide a custom edit summary.  If the summary includes spaces,
           surround it with single quotes, such as:
           -summary:'My edit summary'
-always    Don't prompt to make changes, just do them.
-loose     Do loose replacements.  This will replace all occurrences of the name
           of the image (and not just explicit image syntax).  This should work
           to catch all instances of the image, including where it is used as a
           template parameter or in image galleries.  However, it can also make
           more mistakes.  This only works with image replacement, not image
           removal.

Examples:

The image "FlagrantCopyvio.jpg" is about to be deleted, so let's first remove it
from everything that displays it:

    python image.py FlagrantCopyvio.jpg

The image "Flag.svg" has been uploaded, making the old "Flag.jpg" obsolete:

    python image.py Flag.jpg Flag.svg

"""
#
# (C) Pywikibot team, 2013-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#
import re

import pywikibot

from pywikibot import i18n, pagegenerators, Bot

from scripts.replace import ReplaceRobot as ReplaceBot


class ImageRobot(ReplaceBot):

    """This bot will replace or remove all occurrences of an old image."""

    # Summary messages for replacing images
    msg_replace = {
        'ar': u'روبوت - استبدال الصورة %s مع %s',
        'de': u'Bot: Ersetze Bild %s durch %s',
        'en': u'Bot: Replacing image %s with %s',
        'es': u'Robot - Reemplazando imagen %s por %s',
        'fa': u'ربات: جایگزین کردن تصویر %s با %s',
        'fr': u'Bot: Remplace image %s par %s',
        'he': u'בוט: מחליף את התמונה %s בתמונה %s',
        'it': u"Bot: Sostituisco l'immagine %s con %s",
        'ja': u'ロボットによる：画像置き換え %s から %s へ',
        'ko': u'로봇 - 그림 %s을 %s로 치환',
        'lt': u'robotas: vaizdas %s keičiamas į %s',
        'nn': u'robot: erstatta biletet %s med %s',
        'no': u'robot: erstatter bildet %s med %s',
        'nl': u'Bot: afbeelding %s vervangen door %s',
        'pl': u'Robot zamienia obraz %s na %s',
        'pt': u'Bot: Alterando imagem %s para %s',
        'ru': u'Бот: Замена файла %s на %s',
        'zh': u'機器人：取代圖像 %s 至 %s',
    }

    # Summary messages for removing images
    msg_remove = {
        'ar': u'روبوت - إزالة الصورة %s',
        'de': u'Bot: Entferne Bild %s',
        'en': u'Robot: Removing image %s',
        'es': u'Robot - Retirando imagen %s',
        'fa': u'ربات: برداشتن تصویر %s',
        'fr': u'Bot: Enleve image %s',
        'he': u'בוט: מסיר את התמונה %s',
        'it': u"Bot: Rimuovo l'immagine %s",
        'ja': u'ロボットによる：画像削除 %s',
        'ko': u'로봇 - %s 그림을 제거',
        'lt': u'robotas: Šalinamas vaizdas %s',
        'nl': u'Bot: afbeelding %s verwijderd',
        'no': u'robot: fjerner bildet %s',
        'nn': u'robot: fjerna biletet %s',
        'pl': u'Robot usuwa obraz %s',
        'pt': u'Bot: Alterando imagem %s',
        'ru': u'Бот: удалил файл %s',
        'zh': u'機器人：移除圖像 %s',
    }

    def __init__(self, generator, old_image, new_image=None, **kwargs):
        """
        Constructor.

        @param generator: the pages to work on
        @type  generator: iterable
        @param old_image: the title of the old image (without namespace)
        @type  old_image: unicode
        @param new_image: the title of the new image (without namespace), or
                          None if you want to remove the image
        @type  new_image: unicode or None
        """
        self.availableOptions.update({
            'summary': None,
            'loose': False,
        })

        Bot.__init__(self, generator=generator, **kwargs)

        self.old_image = old_image
        self.new_image = new_image

        if not self.getOption('summary'):
            self.options['summary'] = i18n.translate(
                self.site, self.msg_replace,
                (self.old_image, self.new_image) if self.new_image
                else self.old_image,
                fallback=True)

        # regular expression to find the original template.
        # {{vfd}} does the same thing as {{Vfd}}, so both will be found.
        # The old syntax, {{msg:vfd}}, will also be found.
        # The group 'parameters' will either match the parameters, or an
        # empty string if there are none.

        replacements = []

        namespace = self.site.namespaces[6]
        if namespace.case == 'first-letter':
            case = re.escape(self.old_image[0].upper() +
                             self.old_image[0].lower())
            escaped = '[' + case + ']' + re.escape(self.old_image[1:])
        else:
            escaped = re.escape(self.old_image)

        # Be careful, spaces and _ have been converted to '\ ' and '\_'
        escaped = re.sub('\\\\[_ ]', '[_ ]', escaped)
        if not self.getOption('loose') or not self.new_image:
            image_regex = re.compile(
                r'\[\[ *(?:%s)\s*:\s*%s *(?P<parameters>\|[^\n]+|) *\]\]'
                % ('|'.join(namespace), escaped))
        else:
            image_regex = re.compile(r'' + escaped)

        if self.new_image:
            if not self.getOption('loose'):
                replacements.append((image_regex,
                                     u'[[%s:%s\\g<parameters>]]'
                                     % (self.site.image_namespace(),
                                        self.new_image)))
            else:
                replacements.append((image_regex, self.new_image))
        else:
            replacements.append((image_regex, ''))

        super(ImageRobot, self).__init__(self.generator, replacements,
                                         always=self.getOption('always'),
                                         summary=self.getOption('summary'))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    old_image = None
    new_image = None
    options = {}

    for arg in pywikibot.handle_args(args):
        if arg == '-always':
            options['always'] = True
        elif arg == '-loose':
            options['loose'] = True
        elif arg.startswith('-summary'):
            if len(arg) == len('-summary'):
                options['summary'] = pywikibot.input(u'Choose an edit summary: ')
            else:
                options['summary'] = arg[len('-summary:'):]
        elif old_image:
            new_image = arg
        else:
            old_image = arg

    if old_image:
        site = pywikibot.Site()
        old_imagepage = pywikibot.FilePage(site, old_image)
        gen = pagegenerators.FileLinksGenerator(old_imagepage)
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        bot = ImageRobot(preloadingGen, old_image, new_image, **options)
        bot.run()
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    main()
