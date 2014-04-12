# -*- coding: utf-8 -*-
"""
This script can be used to change one image to another or remove an image
entirely.

Syntax: python image.py image_name [new_image_name]

If only one command-line parameter is provided then that image will be removed;
if two are provided, then the first image will be replaced by the second one on
all pages.

Command line options:

-summary:  Provide a custom edit summary.  If the summary includes spaces,
           surround it with single quotes, such as:
           -summary:'My edit summary'
-always    Don't prompt to make changes, just do them.
-loose     Do loose replacements.  This will replace all occurences of the name
           of the image (and not just explicit image syntax).  This should work
           to catch all instances of the image, including where it is used as a
           template parameter or in image galleries.  However, it can also make
           more mistakes.  This only works with image replacement, not image
           removal.

Examples:

The image "FlagrantCopyvio.jpg" is about to be deleted, so let's first remove it
from everything that displays it:

    python image.py FlagrantCopyvio.jpg

The image "Flag.svg" has been uploaded, making the old "Flag.jpg" obselete:

    python image.py Flag.jpg Flag.svg

"""
#
# (C) Pywikibot team, 2013-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#
import pywikibot
import replace
from pywikibot import pagegenerators
import re


class ImageRobot:
    """
    This robot will load all pages yielded by a file links image page generator and
    replace or remove all occurences of the old image.
    """
    # Summary messages for replacing images
    msg_replace = {
        'ar': u'روبوت - استبدال الصورة %s مع %s',
        'de': u'Bot: Ersetze Bild %s durch %s',
        'en': u'Robot: Replacing image %s with %s',
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

    def __init__(self, generator, oldImage, newImage=None, summary='',
                 always=False, loose=False):
        """
        Arguments:
            * generator - A page generator.
            * oldImage  - The title of the old image (without namespace)
            * newImage  - The title of the new image (without namespace), or
                          None if you want to remove the image.
        """
        self.generator = generator
        self.oldImage = oldImage
        self.newImage = newImage
        self.editSummary = summary
        self.summary = summary
        self.always = always
        self.loose = loose

        # get edit summary message
        mysite = pywikibot.Site()
        if summary:
            self.editSummary = summary
        elif self.newImage:
            self.editSummary = pywikibot.translate(mysite, self.msg_replace) \
            % (self.oldImage, self.newImage)
        else:
            self.editSummary = pywikibot.translate(mysite, self.msg_remove) \
            % self.oldImage

    def run(self):
        """
        Starts the robot's action.
        """
        # regular expression to find the original template.
        # {{vfd}} does the same thing as {{Vfd}}, so both will be found.
        # The old syntax, {{msg:vfd}}, will also be found.
        # The group 'parameters' will either match the parameters, or an
        # empty string if there are none.

        replacements = []
        site = pywikibot.Site()

        if not site.nocapitalize:
            case = re.escape(self.oldImage[0].upper() + \
                             self.oldImage[0].lower())
            escaped = '[' + case + ']' + re.escape(self.oldImage[1:])
        else:
            escaped = re.escape(self.oldImage)

        # Be careful, spaces and _ have been converted to '\ ' and '\_'
        escaped = re.sub('\\\\[_ ]', '[_ ]', escaped)
        if not self.loose or not self.newImage:
            ImageRegex = re.compile(r'\[\[ *(?:' + '|'.join(site.namespace(6, all=True)) + ')\s*:\s*' + escaped + ' *(?P<parameters>\|[^\n]+|) *\]\]')
        else:
            ImageRegex = re.compile(r'' + escaped)

        if self.newImage:
            if not self.loose:
                replacements.append((ImageRegex, '[[' + site.image_namespace() + ':' + self.newImage + '\g<parameters>]]'))
            else:
                replacements.append((ImageRegex, self.newImage))
        else:
            replacements.append((ImageRegex, ''))

        replaceBot = replace.ReplaceRobot(self.generator, replacements,
                                          acceptall=self.always,
                                          summary=self.editSummary)
        replaceBot.run()


def main():
    oldImage = None
    newImage = None
    summary = ''
    always = False
    loose = False
    # read command line parameters
    for arg in pywikibot.handleArgs():
        if arg == '-always':
            always = True
        elif arg == '-loose':
            loose = True
        elif arg.startswith('-summary'):
            if len(arg) == len('-summary'):
                summary = pywikibot.input(u'Choose an edit summary: ')
            else:
                summary = arg[len('-summary:'):]
        else:
            if oldImage:
                newImage = arg
            else:
                oldImage = arg
    if not oldImage:
        pywikibot.showHelp('image')
    else:
        mysite = pywikibot.Site()
        ns = mysite.image_namespace()
        oldImagePage = pywikibot.ImagePage(mysite, ns + ':' + oldImage)
        gen = pagegenerators.FileLinksGenerator(oldImagePage)
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        bot = ImageRobot(preloadingGen, oldImage, newImage, summary, always,
                         loose)
        bot.run()

if __name__ == "__main__":
    main()
