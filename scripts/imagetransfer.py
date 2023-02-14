#!/usr/bin/env python3
"""
Script to copy images to Wikimedia Commons, or to another wiki.

Syntax:

    python pwb.py imagetransfer {<pagename>|<generator>} [<options>]

The following parameters are supported:

  -interwiki        Look for images in pages found through interwiki links.

  -keepname         Keep the filename and do not verify description while
                    replacing

  -tolang:x         Copy the image to the wiki in code x

  -tofamily:y       Copy the image to a wiki in the family y

  -tosite:s         Copy the image to the given site like wikipedia:test

  -force_if_shared  Upload the file to the target, even if it exists on that
                    wiki's shared repo

  -asynchronous     Upload to stash.

  -chunk_size:n     Upload in chunks of n bytes.

  -file:z           Upload many files from textfile: [[Image:x]]
                                                     [[Image:y]]

If pagename is an image description page, offers to copy the image to the
target site. If it is a normal page, it will offer to copy any of the images
used on that page, or if the -interwiki argument is used, any of the images
used on a page reachable via interwiki links.

&params;
"""
#
# (C) Pywikibot team, 2004-2022
#
# Distributed under the terms of the MIT license.
#
import re
import sys

import pywikibot
from pywikibot import config, i18n, pagegenerators, textlib
from pywikibot.bot import ExistingPageBot, SingleSiteBot
from pywikibot.exceptions import IsRedirectPageError, NoPageError
from pywikibot.specialbots import UploadRobot


docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


nowCommonsTemplate = {
    'ar': '{{الآن كومنز|%s}}',
    'ary': '{{Now Commons|%s}}',
    'arz': '{{Now Commons|%s}}',
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
    ('wikipedia:ar', 'commons:commons'): {
        'رخصة جنو للوثائق الحرة': 'GFDL',
        'رخصة جنو للوثائق الحرة - شخصي': 'GFDL-self',
        'ملكية عامة': 'PD',
        'ملكية عامة - شخصي': 'PD-self',
        'ملكية عامة - فن': 'PD-Art',
        'ملكية عامة - الحكومة الأمريكية': 'PD-USGov',
    },
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


class ImageTransferBot(SingleSiteBot, ExistingPageBot):

    """Image transfer bot."""

    update_options = {
        'ignore_warning': False,  # not implemented yet
        'interwiki': False,
        'keepname': False,
        'target': None,
        'force_if_shared': False,
        'asynchronous': False,
        'chunk_size': 0,
    }

    def __init__(self, **kwargs) -> None:
        """Initializer.

        :keyword generator: the pages to work on
        :type generator: iterable
        :keyword target_site: Site to send image to, default none
        :type target_site: pywikibot.site.APISite
        :keyword interwiki: Look for images in interwiki links, default false
        :type interwiki: boolean
        :keyword keepname: Keep the filename and do not verify description
            while replacing, default false
        :type keepname: boolean
        :keyword force_if_shared: Upload the file even if it's currently
            shared to the target site (e.g. when moving from Commons to another
            wiki)
        :type force_if_shared: boolean
        :keyword asynchronous: Upload to stash.
        :type asynchronous: boolean
        :keyword chunk_size: Upload in chunks of this size bytes.
        :type chunk_size: integer
        """
        super().__init__(**kwargs)
        if self.opt.target is None:
            self.opt.target = self.site.image_repository()
        else:
            self.opt.target = pywikibot.Site(self.opt.target)

    def transfer_image(self, sourceImagePage) -> None:
        """
        Download image and its description, and upload it to another site.

        :return: the filename which was used to upload the image
        """
        sourceSite = sourceImagePage.site
        pywikibot.info(
            '\n>>> Transfer {source} from {source.site} to {target}\n'
            .format(source=sourceImagePage, target=self.opt.target))
        url = sourceImagePage.get_file_url()
        pywikibot.info('URL should be: ' + url)
        # localize the text that should be printed on image description page
        try:
            description = sourceImagePage.get()
            # try to translate license templates
            if (sourceSite.sitename,
                    self.opt.target.sitename) in licenseTemplates:
                for old, new in licenseTemplates[
                        (sourceSite.sitename,
                         self.opt.target.sitename)].items():
                    new = '{{%s}}' % new
                    old = re.compile('{{%s}}' % old)
                    description = textlib.replaceExcept(description, old, new,
                                                        ['comment', 'math',
                                                         'nowiki', 'pre'])

            description = i18n.twtranslate(self.opt.target,
                                           'imagetransfer-file_page_message',
                                           {'site': sourceSite,
                                            'description': description})
            description += '\n\n'
            description += sourceImagePage.getFileVersionHistoryTable()
            # add interwiki link
            if sourceSite.family == self.opt.target.family:
                description += f'\n\n{sourceImagePage}'
        except NoPageError:
            pywikibot.info(
                'Image does not exist or description page is empty.')
        except IsRedirectPageError:
            pywikibot.info('Image description page is redirect.')
        else:
            bot = UploadRobot(url=url, description=description,
                              target_site=self.opt.target,
                              url_encoding=sourceSite.encoding(),
                              keep_filename=self.opt.keepname,
                              verify_description=not self.opt.keepname,
                              ignore_warning=self.opt.ignore_warning,
                              force_if_shared=self.opt.force_if_shared,
                              asynchronous=self.opt.asynchronous,
                              chunk_size=self.opt.chunk_size)

            # try to upload
            if bot.skip_run():
                return
            target_filename = bot.upload_file(url)

            if target_filename \
               and self.opt.target.sitename == 'commons:commons':
                # upload to Commons was successful
                reason = i18n.twtranslate(sourceSite,
                                          'imagetransfer-nowcommons_notice')
                # try to delete the original image if we have a sysop account
                if sourceSite.has_right('delete') \
                   and sourceImagePage.delete(reason):
                    return
                if sourceSite.lang in nowCommonsTemplate \
                   and sourceSite.family.name in config.usernames \
                   and sourceSite.lang in \
                   config.usernames[sourceSite.family.name]:
                    # add the nowCommons template.
                    pywikibot.info('Adding nowCommons template to '
                                   + sourceImagePage.title())
                    sourceImagePage.put(sourceImagePage.get() + '\n\n'
                                        + nowCommonsTemplate[sourceSite.lang]
                                        % target_filename,
                                        summary=reason)

    def show_image_list(self, imagelist) -> None:
        """Print image list."""
        pywikibot.info('-' * 60)
        for i, image in enumerate(imagelist):
            pywikibot.info(f'{i}. Found image: {image}')
            try:
                # Show the image description page's contents
                pywikibot.info(image.get())
            except NoPageError:
                pass
            else:
                # look if page already exists with this name.
                # TODO: consider removing this: a different image of the same
                # name may exist on the target wiki, and the bot user may want
                # to upload anyway, using another name.
                try:
                    # Maybe the image is on the target site already
                    targetTitle = 'File:' + image.title().split(':', 1)[1]
                    targetImage = pywikibot.Page(self.opt.target, targetTitle)
                    targetImage.get()
                    pywikibot.info(f'Image with this name is already on '
                                   f'{self.opt.target}.')
                    pywikibot.info('-' * 60)
                    pywikibot.info(targetImage.get())
                    sys.exit()
                except NoPageError:
                    # That's the normal case
                    pass
                except IsRedirectPageError:
                    pywikibot.info(
                        'Description page on target wiki is redirect?!')

        pywikibot.info('=' * 60)

    def treat(self, page) -> None:
        """Treat a single page."""
        if self.opt.interwiki:
            imagelist = []
            for linkedPage in page.interwiki():
                linkedPage = pywikibot.Page(linkedPage)
                imagelist.extend(linkedPage.imagelinks())
        elif page.is_filepage():
            imagePage = pywikibot.FilePage(page.site, page.title())
            imagelist = [imagePage]
        else:
            imagelist = list(page.imagelinks())

        while imagelist:
            self.show_image_list(imagelist)
            if len(imagelist) == 1:
                # no need to query the user, only one possibility
                todo = 0
            else:
                pywikibot.info('Give the number of the image to transfer.')
                todo = pywikibot.input('To end uploading, press enter:')
                if not todo:
                    break
                todo = int(todo)

            if 0 <= todo < len(imagelist):
                if self.transfer_allowed(imagelist[todo]):
                    self.transfer_image(imagelist[todo])
                # remove the selected image from the list
                imagelist.pop(todo)
            else:
                pywikibot.info('<<yellow>>No such image number.')

    def transfer_allowed(self, image) -> bool:
        """Check whether transfer is allowed."""
        target_repo = self.opt.target.image_repository()

        if not self.opt.force_if_shared \
           and image.file_is_shared() \
           and image.site.image_repository() == target_repo:
            pywikibot.info(
                f'<<yellow>>The image is already shared on {target_repo}.')
            return False
        return True


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    target_code = None
    target_family = None
    options = {}

    local_args = pywikibot.handle_args(args)
    generator_factory = pagegenerators.GeneratorFactory(
        positional_arg_name='page')

    for arg in local_args:
        opt, _, value = arg.partition(':')
        if opt in ('-ignore_warning', '-interwiki', '-keepname',
                   '-force_if_shared', '-asynchronous'):
            options[opt[1:]] = True
        elif opt == '-tolang':
            target_code = value
        elif opt == '-tofamily':
            target_family = value
        elif opt == '-tosite':
            options['target'] = value
        elif opt == '-chunk_size':
            options['chunk_size'] = value
        else:
            generator_factory.handle_arg(arg)

    gen = generator_factory.getCombinedGenerator()
    if not gen:
        pywikibot.bot.suggest_help(
            missing_parameters=['page'],
            additional_text='and no other generator was defined.')
        return

    if target_code or target_family:
        site = pywikibot.Site()
        options.setdefault('target',
                           '{}:{}'.format(target_family or site.family,
                                          target_code or site.lang))

    bot = ImageTransferBot(generator=gen, **options)
    bot.run()


if __name__ == '__main__':
    main()
