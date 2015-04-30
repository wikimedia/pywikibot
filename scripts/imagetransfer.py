#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to copy images to Wikimedia Commons, or to another wiki.

Syntax:

    python imagetransfer.py pagename [-interwiki] [-tolang:xx] [-tofamily:yy]

Arguments:

  -interwiki   Look for images in pages found through interwiki links.

  -keepname    Keep the filename and do not verify description while replacing

  -tolang:xx   Copy the image to the wiki in language xx

  -tofamily:yy Copy the image to a wiki in the family yy

  -file:zz     Upload many files from textfile: [[Image:xx]]
                                                [[Image:yy]]

If pagename is an image description page, offers to copy the image to the
target site. If it is a normal page, it will offer to copy any of the images
used on that page, or if the -interwiki argument is used, any of the images
used on a page reachable via interwiki links.
"""
#
# (C) Andre Engels, 2004
# (C) Pywikibot team, 2004-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import re
import sys
import pywikibot
import upload
from pywikibot import config, i18n, textlib

copy_message = {
    'ar': u"هذه الصورة تم نقلها من %s. الوصف الأصلي كان:\r\n\r\n%s",
    'en': u"This image was copied from %s. The original description was:\r\n\r\n%s",
    'fa': u"تصویر از %s کپی شده‌است.توضیحات اصلی ان این بود::\r\n\r\n%s",
    'de': u"Dieses Bild wurde von %s kopiert. Die dortige Beschreibung lautete:\r\n\r\n%s",
    'fr': u"Cette image est copiée de %s. La description originale était:\r\n\r\n%s",
    'he': u"תמונה זו הועתקה מהאתר %s. תיאור הקובץ המקורי היה:\r\n\r\n%s",
    'hu': u"Kép másolása innen: %s. Az eredeti leírás:\r\n\r\n%s",
    'ia': u"Iste imagine esseva copiate de %s. Le description original esseva:\r\n\r\n%s",
    'it': u"Questa immagine è stata copiata da %s. La descrizione originale era:\r\n\r\n%s",
    'kk': u"Бұл сурет %s дегеннен көшірілді. Түпнұсқа сипатттамасы былай болды:\r\n\r\n%s",
    'lt': u"Šis paveikslėlis buvo įkeltas iš %s. Originalus aprašymas buvo:\r\n\r\n%s",
    'nl': u"Afbeelding gekopieerd vanaf %s. De beschrijving daar was:\r\n\r\n%s",
    'pl': u"Ten obraz został skopiowany z %s. Oryginalny opis to:\r\n\r\n%s",
    'pt': u"Esta imagem foi copiada de %s. A descrição original foi:\r\n\r\n%s",
    'ru': u"Изображение было скопировано с %s. Оригинальное описание содержало:\r\n\r\n%s",
    'sr': u"Ова слика је копирана са %s. Оригинални опис је:\r\n\r\n%s",
    'zh': u"本圖像從 %s 複製，原始說明資料：\r\n\r\n%s",
}

nowCommonsTemplate = {
    'ar': u'{{subst:الآن_كومنز|Image:%s}}',
    'de': u'{{NowCommons|%s}}',
    'fr': u'{{Désormais sur Commons|%s}}',
    'en': u'{{subst:ncd|Image:%s}}',
    'fa': u'{{موجود در انبار|%s}}',
    'he': u'{{גם בוויקישיתוף|%s}}',
    'hu': u'{{azonnali-commons|Kép:%s}}',
    'ia': u'{{OraInCommons|Imagine:%s}}',
    'it': u'{{NowCommons unlink|%s}}',
    'ja': u'{{NowCommons|Image:%s}}',
    'kk': u'{{NowCommons|Image:%s}}',
    'li': u'{{NowCommons|%s}}',
    'lt': u'{{NowCommons|Image:%s}}',
    'nds-nl': u'{{NoenCommons|File:%s}}',
    'nl': u'{{NuCommons|Image:%s}}',
    'pl': u'{{NowCommons|%s}}',
    'pt': u'{{NowCommons|%s}}',
    'sr': u'{{NowCommons|%s}}',
    'zh': u'{{NowCommons|Image:%s}}',
}

nowCommonsMessage = {
    'ar': u'الملف الآن متوفر في ويكيميديا كومنز.',
    'de': u'Datei ist jetzt auf Wikimedia Commons verfügbar.',
    'en': u'File is now available on Wikimedia Commons.',
    'eo': u'Dosiero nun estas havebla en la Wikimedia-Komunejo.',
    'fa': u'پرونده اکنون در انبار است',
    'he': u'הקובץ זמין כעת בוויקישיתוף.',
    'hu': u'A fájl most már elérhető a Wikimedia Commonson',
    'ia': u'Le file es ora disponibile in Wikimedia Commons.',
    'ja': u'ファイルはウィキメディア・コモンズにあります',
    'it': u'L\'immagine è adesso disponibile su Wikimedia Commons.',
    'kk': u'Файлды енді Wikimedia Ортаққорынан қатынауға болады.',
    'lt': u'Failas įkeltas į Wikimedia Commons projektą.',
    'nl': u'Dit bestand staat nu op [[w:nl:Wikimedia Commons|Wikimedia Commons]].',
    'pl': u'Plik jest teraz dostępny na Wikimedia Commons.',
    'pt': u'Arquivo está agora na Wikimedia Commons.',
    'ru': u'[[ВП:КБУ#Ф8|Ф.8]]: доступно на [[Викисклад]]е',
    'sr': u'Слика је сада доступна и на Викимедија Остави.',
    'zh': u'檔案已存在於維基共享資源。',
}

# Translations for license templates.
# Must only be given when they are in fact different.
licenseTemplates = {
    ('wikipedia:de', 'commons:commons'): {
        u'Bild-GFDL':                u'GFDL',
        u'Bild-GFDL-OpenGeoDB':      u'GFDL-OpenGeoDB',
        u'Bild-Innweb-Lizenz':       u'Map-Austria-GNU',
        u'Bild-PD':                  u'PD',
        u'Bild-PD-alt':              u'PD-old',
        u'Bild-PD-Kunst':            u'PD-Art',
        u'Bild-PD-US':               u'PD-USGov',
    },
    ('wikipedia:fa', 'commons:commons'): {
        u'مالکیت عمومی':             u'PD',
        u'مالکیت عمومی-خود':         u'PD-self',
        u'مجوز گنو':                  u'GFDL',
        u'مجوز گنو-خود':             u'GFDL-self',
        u'نگاره قدیمی':              u'PD-Iran',
        u'نگاره نوشتاری':            u'PD-textlogo',
        u'نگاره عراقی':              u'PD-Iraq',
        u'نگاره بریتانیا':           u'PD-UK',
        u'نگاره هابل':               u'PD-Hubble',
        u'نگاره آمریکا':             u'PD-US',
        u'نگاره دولت آمریکا':        u'PD-USGov',
        u'کک-یاد-دو':                u'Cc-by-2.0',
        u'کک-یاد-حفظ-دونیم':         u'Cc-by-sa-2.5',
        u'کک-یاد-سه':                u'Cc-by-3.0',
    },
    ('wikipedia:fr', 'commons:commons'): {
        u'Domaine public':           u'PD'
    },
    ('wikipedia:he', 'commons:commons'): {
        u'שימוש חופשי':              u'PD-self',
        u'שימוש חופשי מוגן':         u'Copyrighted free use',
        u'שימוש חופשי מוגן בתנאי':   u'Copyrighted free use provided that',
        u'תמונה ישנה':              u'PD-Israel',
        u'ייחוס':                   u'Attribution',
        u'לוגו ויקימדיה':           u'Copyright by Wikimedia',
    },
    ('wikipedia:hu', 'commons:commons'): {
        u'Közkincs':                 u'PD',
        u'Közkincs-régi':            u'PD-old',
    },
    ('wikipedia:pt', 'commons:commons'): {
        u'Domínio público':          u'PD',
    },
}


class ImageTransferBot:

    """Image transfer bot."""

    def __init__(self, generator, targetSite=None, interwiki=False,
                 keep_name=False, ignore_warning=False):
        self.generator = generator
        self.interwiki = interwiki
        self.targetSite = targetSite
        self.keep_name = keep_name
        self.ignore_warning = ignore_warning

    def transferImage(self, sourceImagePage):
        """
        Download image and its description, and upload it to another site.

        @return: the filename which was used to upload the image
        """
        sourceSite = sourceImagePage.site
        url = sourceImagePage.fileUrl().encode('utf-8')
        pywikibot.output(u"URL should be: %s" % url)
        # localize the text that should be printed on the image description page
        try:
            description = sourceImagePage.get()
            # try to translate license templates
            if (sourceSite.sitename(), self.targetSite.sitename()) in licenseTemplates:
                for old, new in licenseTemplates[(sourceSite.sitename(),
                                                  self.targetSite.sitename())].items():
                    new = '{{%s}}' % new
                    old = re.compile('{{%s}}' % old)
                    description = textlib.replaceExcept(description, old, new,
                                                        ['comment', 'math',
                                                         'nowiki', 'pre'])

            description = i18n.translate(self.targetSite, copy_message,
                                         fallback=True) % (sourceSite, description)
            description += '\n\n'
            description += sourceImagePage.getFileVersionHistoryTable()
            # add interwiki link
            if sourceSite.family == self.targetSite.family:
                description += u'\r\n\r\n{0}'.format(sourceImagePage)
        except pywikibot.NoPage:
            description = ''
            print("Image does not exist or description page is empty.")
        except pywikibot.IsRedirectPage:
            description = ''
            print("Image description page is redirect.")
        else:
            bot = upload.UploadRobot(url=url, description=description,
                                     targetSite=self.targetSite,
                                     urlEncoding=sourceSite.encoding(),
                                     keepFilename=self.keep_name,
                                     verifyDescription=not self.keep_name,
                                     ignoreWarning=self.ignore_warning)
            # try to upload
            targetFilename = bot.run()
            if targetFilename and self.targetSite.family.name == 'commons' and \
               self.targetSite.code == 'commons':
                # upload to Commons was successful
                reason = i18n.translate(sourceSite, nowCommonsMessage, fallback=True)
                # try to delete the original image if we have a sysop account
                if sourceSite.family.name in config.sysopnames and \
                   sourceSite.lang in config.sysopnames[sourceSite.family.name]:
                    if sourceImagePage.delete(reason):
                        return
                if sourceSite.lang in nowCommonsTemplate and \
                   sourceSite.family.name in config.usernames and \
                   sourceSite.lang in config.usernames[sourceSite.family.name]:
                    # add the nowCommons template.
                    pywikibot.output(u'Adding nowCommons template to %s'
                                     % sourceImagePage.title())
                    sourceImagePage.put(sourceImagePage.get() + '\n\n' +
                                        nowCommonsTemplate[sourceSite.lang]
                                        % targetFilename,
                                        summary=nowCommonsMessage[sourceSite.lang])

    def showImageList(self, imagelist):
        for i in range(len(imagelist)):
            image = imagelist[i]
            print("-" * 60)
            pywikibot.output(u"%s. Found image: %s"
                             % (i, image.title(asLink=True)))
            try:
                # Show the image description page's contents
                pywikibot.output(image.get())
                # look if page already exists with this name.
                # TODO: consider removing this: a different image of the same
                # name may exist on the target wiki, and the bot user may want
                # to upload anyway, using another name.
                try:
                    # Maybe the image is on the target site already
                    targetTitle = '%s:%s' % (self.targetSite.image_namespace(),
                                             image.title().split(':', 1)[1])
                    targetImage = pywikibot.Page(self.targetSite, targetTitle)
                    targetImage.get()
                    pywikibot.output(u"Image with this name is already on %s."
                                     % self.targetSite)
                    print("-" * 60)
                    pywikibot.output(targetImage.get())
                    sys.exit()
                except pywikibot.NoPage:
                    # That's the normal case
                    pass
                except pywikibot.IsRedirectPage:
                    pywikibot.output(
                        u"Description page on target wiki is redirect?!")

            except pywikibot.NoPage:
                break
        print("=" * 60)

    def run(self):
        for page in self.generator:
            if self.interwiki:
                imagelist = []
                for linkedPage in page.interwiki():
                    linkedPage = pywikibot.Page(linkedPage)
                    imagelist.extend(
                        linkedPage.imagelinks(
                            followRedirects=True))
            elif page.isImage():
                imagePage = pywikibot.FilePage(page.site, page.title())
                imagelist = [imagePage]
            else:
                imagelist = list(page.imagelinks(followRedirects=True))

            while len(imagelist) > 0:
                self.showImageList(imagelist)
                if len(imagelist) == 1:
                    # no need to query the user, only one possibility
                    todo = 0
                else:
                    pywikibot.output(
                        u"Give the number of the image to transfer.")
                    todo = pywikibot.input(u"To end uploading, press enter:")
                    if not todo:
                        break
                    todo = int(todo)
                if todo in range(len(imagelist)):
                    if imagelist[todo].fileIsShared():
                        pywikibot.output(
                            u'The image is already on Wikimedia Commons.')
                    else:
                        self.transferImage(imagelist[todo])
                    # remove the selected image from the list
                    imagelist = imagelist[:todo] + imagelist[todo + 1:]
                else:
                    pywikibot.output(u'No such image number.')


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    pageTitle = None
    gen = None

    interwiki = False
    keep_name = False
    targetLang = None
    targetFamily = None

    local_args = pywikibot.handle_args(args)

    for arg in local_args:
        if arg == '-interwiki':
            interwiki = True
        elif arg.startswith('-keepname'):
            keep_name = True
        elif arg.startswith('-tolang:'):
            targetLang = arg[8:]
        elif arg.startswith('-tofamily:'):
            targetFamily = arg[10:]
        elif not pageTitle:
            pageTitle = arg

    if pageTitle:
        page = pywikibot.Page(pywikibot.Site(), pageTitle)
        gen = iter([page])
    else:
        pywikibot.showHelp()
        return

    if not targetLang and not targetFamily:
        targetSite = pywikibot.Site('commons', 'commons')
    else:
        if not targetLang:
            targetLang = pywikibot.Site().language
        if not targetFamily:
            targetFamily = pywikibot.Site().family
        targetSite = pywikibot.Site(targetLang, targetFamily)
    bot = ImageTransferBot(gen, interwiki=interwiki, targetSite=targetSite,
                           keep_name=keep_name)
    bot.run()

if __name__ == "__main__":
    main()
