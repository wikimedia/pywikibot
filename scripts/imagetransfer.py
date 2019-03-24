#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to copy images to Wikimedia Commons, or to another wiki.

Syntax:

    python pwb.py imagetransfer {<pagename>|<generator>} [<options>]

Arguments:

  -interwiki   Look for images in pages found through interwiki links.

  -keepname    Keep the filename and do not verify description while replacing

  -tolang:x    Copy the image to the wiki in language x

  -tofamily:y  Copy the image to a wiki in the family y

  -file:z      Upload many files from textfile: [[Image:x]]
                                                [[Image:y]]

If pagename is an image description page, offers to copy the image to the
target site. If it is a normal page, it will offer to copy any of the images
used on that page, or if the -interwiki argument is used, any of the images
used on a page reachable via interwiki links.

&params;
"""
#
# (C) Andre Engels, 2004
# (C) Pywikibot team, 2004-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import re
import sys

import pywikibot

from pywikibot import config, i18n, pagegenerators, textlib
from pywikibot.specialbots import UploadRobot


docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


nowCommonsTemplate = {
    'ar': '{{الآن كومنز|%s}}',
    'de': '{{NowCommons|%s}}',
    'fr': '{{Désormais sur Commons|%s}}',
    'en': '{{subst:ncd|Image:%s}}',
    'fa': '{{موجود در انبار|%s}}',
    'he': '{{גם בוויקישיתוף|%s}}',
    'hu': '{{azonnali-commons|Kép:%s}}',
    'ia': '{{OraInCommons|Imagine:%s}}',
    'it': '{{NowCommons unlink|%s}}',
    'ja': '{{NowCommons|Image:%s}}',
    'kk': '{{NowCommons|Image:%s}}',
    'li': '{{NowCommons|%s}}',
    'lt': '{{NowCommons|Image:%s}}',
    'nds-nl': '{{NoenCommons|File:%s}}',
    'nl': '{{NuCommons|Image:%s}}',
    'pl': '{{NowCommons|%s}}',
    'pt': '{{NowCommons|%s}}',
    'sr': '{{NowCommons|%s}}',
    'zh': '{{NowCommons|Image:%s}}',
}

# Translations for license templates.
# Must only be given when they are in fact different.
licenseTemplates = {
    ('wikipedia:de', 'commons:commons'): {
        'Bild-GFDL': 'GFDL',
        'Bild-GFDL-OpenGeoDB': 'GFDL-OpenGeoDB',
        'Bild-Innweb-Lizenz': 'Map-Austria-GNU',
        'Bild-PD': 'PD',
        'Bild-PD-alt': 'PD-old',
        'Bild-PD-Kunst': 'PD-Art',
        'Bild-PD-US': 'PD-USGov',
    },
    ('wikipedia:fa', 'commons:commons'): {
        'مالکیت عمومی': 'PD',
        'مالکیت عمومی-خود': 'PD-self',
        'مجوز گنو': 'GFDL',
        'مجوز گنو-خود': 'GFDL-self',
        'نگاره قدیمی': 'PD-Iran',
        'نگاره نوشتاری': 'PD-textlogo',
        'نگاره عراقی': 'PD-Iraq',
        'نگاره بریتانیا': 'PD-UK',
        'نگاره هابل': 'PD-Hubble',
        'نگاره آمریکا': 'PD-US',
        'نگاره دولت آمریکا': 'PD-USGov',
        'کک-یاد-دو': 'Cc-by-2.0',
        'کک-یاد-حفظ-دونیم': 'Cc-by-sa-2.5',
        'کک-یاد-سه': 'Cc-by-3.0',
    },
    ('wikipedia:fr', 'commons:commons'): {
        'Domaine public': 'PD'
    },
    ('wikipedia:he', 'commons:commons'): {
        'שימוש חופשי': 'PD-self',
        'שימוש חופשי מוגן': 'Copyrighted free use',
        'שימוש חופשי מוגן בתנאי': 'Copyrighted free use provided that',
        'תמונה ישנה': 'PD-Israel',
        'ייחוס': 'Attribution',
        'לוגו ויקימדיה': 'Copyright by Wikimedia',
    },
    ('wikipedia:hu', 'commons:commons'): {
        'Közkincs': 'PD',
        'Közkincs-régi': 'PD-old',
    },
    ('wikipedia:pt', 'commons:commons'): {
        'Domínio público': 'PD',
    },
}


class ImageTransferBot(object):

    """Image transfer bot."""

    def __init__(self, generator, targetSite=None, interwiki=False,
                 keep_name=False, ignore_warning=False):
        """Initializer."""
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
        pywikibot.output('URL should be: ' + url)
        # localize the text that should be printed on image description page
        try:
            description = sourceImagePage.get()
            # try to translate license templates
            if (sourceSite.sitename,
                    self.targetSite.sitename) in licenseTemplates:
                for old, new in licenseTemplates[
                        (sourceSite.sitename,
                         self.targetSite.sitename)].items():
                    new = '{{%s}}' % new
                    old = re.compile('{{%s}}' % old)
                    description = textlib.replaceExcept(description, old, new,
                                                        ['comment', 'math',
                                                         'nowiki', 'pre'])

            description = i18n.twtranslate(self.targetSite,
                                           'imagetransfer-file_page_message',
                                           {'site': sourceSite,
                                            'description': description})
            description += '\n\n'
            description += sourceImagePage.getFileVersionHistoryTable()
            # add interwiki link
            if sourceSite.family == self.targetSite.family:
                description += '\n\n{0}'.format(sourceImagePage)
        except pywikibot.NoPage:
            description = ''
            pywikibot.output(
                'Image does not exist or description page is empty.')
        except pywikibot.IsRedirectPage:
            description = ''
            pywikibot.output('Image description page is redirect.')
        else:
            bot = UploadRobot(url=url, description=description,
                              targetSite=self.targetSite,
                              urlEncoding=sourceSite.encoding(),
                              keepFilename=self.keep_name,
                              verifyDescription=not self.keep_name,
                              ignoreWarning=self.ignore_warning)
            # try to upload
            targetFilename = bot.run()
            if targetFilename and self.targetSite.family.name == 'commons' \
               and self.targetSite.code == 'commons':
                # upload to Commons was successful
                reason = i18n.twtranslate(sourceSite,
                                          'imagetransfer-nowcommons_notice')
                # try to delete the original image if we have a sysop account
                if sourceSite.family.name in config.sysopnames \
                   and sourceSite.lang in \
                   config.sysopnames[sourceSite.family.name]:
                    if sourceImagePage.delete(reason):
                        return
                if sourceSite.lang in nowCommonsTemplate \
                   and sourceSite.family.name in config.usernames \
                   and sourceSite.lang in \
                   config.usernames[sourceSite.family.name]:
                    # add the nowCommons template.
                    pywikibot.output('Adding nowCommons template to '
                                     + sourceImagePage.title())
                    sourceImagePage.put(sourceImagePage.get() + '\n\n'
                                        + nowCommonsTemplate[sourceSite.lang]
                                        % targetFilename,
                                        summary=reason)

    def showImageList(self, imagelist):
        """Print image list."""
        for i, image in enumerate(imagelist):
            pywikibot.output('-' * 60)
            pywikibot.output('{}. Found image: {}'
                             .format(i, image.title(as_link=True)))
            try:
                # Show the image description page's contents
                pywikibot.output(image.get())
                # look if page already exists with this name.
                # TODO: consider removing this: a different image of the same
                # name may exist on the target wiki, and the bot user may want
                # to upload anyway, using another name.
                try:
                    # Maybe the image is on the target site already
                    targetTitle = 'File:' + image.title().split(':', 1)[1]
                    targetImage = pywikibot.Page(self.targetSite, targetTitle)
                    targetImage.get()
                    pywikibot.output('Image with this name is already on {}.'
                                     .format(self.targetSite))
                    pywikibot.output('-' * 60)
                    pywikibot.output(targetImage.get())
                    sys.exit()
                except pywikibot.NoPage:
                    # That's the normal case
                    pass
                except pywikibot.IsRedirectPage:
                    pywikibot.output(
                        'Description page on target wiki is redirect?!')

            except pywikibot.NoPage:
                break
        pywikibot.output('=' * 60)

    def run(self):
        """Run the bot."""
        for page in self.generator:
            if self.interwiki:
                imagelist = []
                for linkedPage in page.interwiki():
                    linkedPage = pywikibot.Page(linkedPage)
                    imagelist.extend(
                        linkedPage.imagelinks(
                            followRedirects=True))
            elif page.is_filepage():
                imagePage = pywikibot.FilePage(page.site, page.title())
                imagelist = [imagePage]
            else:
                imagelist = list(page.imagelinks(followRedirects=True))

            while imagelist:
                self.showImageList(imagelist)
                if len(imagelist) == 1:
                    # no need to query the user, only one possibility
                    todo = 0
                else:
                    pywikibot.output(
                        'Give the number of the image to transfer.')
                    todo = pywikibot.input('To end uploading, press enter:')
                    if not todo:
                        break
                    todo = int(todo)
                if todo in range(len(imagelist)):
                    if (imagelist[todo].fileIsShared()
                            and imagelist[todo].site.image_repository()
                            == self.targetSite.image_repository()):
                        pywikibot.output(
                            'The image is already shared on {0}.'
                            .format(self.targetSite.image_repository()))
                    else:
                        self.transferImage(imagelist[todo])
                    # remove the selected image from the list
                    imagelist = imagelist[:todo] + imagelist[todo + 1:]
                else:
                    pywikibot.output('No such image number.')


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    gen = None

    interwiki = False
    keep_name = False
    targetLang = None
    targetFamily = None

    local_args = pywikibot.handle_args(args)
    generator_factory = pagegenerators.GeneratorFactory(
        positional_arg_name='page')

    for arg in local_args:
        if arg == '-interwiki':
            interwiki = True
        elif arg.startswith('-keepname'):
            keep_name = True
        elif arg.startswith('-tolang:'):
            targetLang = arg[8:]
        elif arg.startswith('-tofamily:'):
            targetFamily = arg[10:]
        else:
            generator_factory.handleArg(arg)

    gen = generator_factory.getCombinedGenerator()
    if not gen:
        pywikibot.bot.suggest_help(
            missing_parameters=['page'],
            additional_text='and no other generator was defined.')
        return False

    site = pywikibot.Site()
    if not targetLang and not targetFamily:
        targetSite = site.image_repository()
    else:
        targetSite = pywikibot.Site(targetLang or site.lang,
                                    targetFamily or site.family)
    bot = ImageTransferBot(gen, interwiki=interwiki, targetSite=targetSite,
                           keep_name=keep_name)
    bot.run()


if __name__ == '__main__':
    main()
