#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Script to delete files that are also present on Wikimedia Commons on a local
wiki. Do not run this script on Wikimedia Commons itself. It works based on
a given array of templates defined below.

Files are downloaded and compared. If the files match, it can be deleted on
the source wiki. If multiple versions of the file exist, the script will not
delete. If the MD5 comparison is not equal, the script will not delete.

A sysop account on the local wiki is required if you want all features of
this script to work properly.

This script understands various command-line arguments:
    -autonomous:    run automatically, do not ask any questions. All files
                    that qualify for deletion are deleted. Reduced screen
                    output.

    -replace:       replace links if the files are equal and the file names
                    differ

    -replacealways: replace links if the files are equal and the file names
                    differ without asking for confirmation

    -replaceloose:  Do loose replacements.  This will replace all occurences
                    of the name of the image (and not just explicit image
                    syntax).  This should work to catch all instances of the
                    file, including where it is used as a template parameter
                    or in galleries.  However, it can also make more
                    mistakes.

    -replaceonly:   Use this if you do not have a local sysop account, but do
                    wish to replace links from the NowCommons template.

    -hash:          Use the hash to identify the images that are the same. It
                    doesn't work always, so the bot opens two tabs to let to
                    the user to check if the images are equal or not.

-- Example --
python nowcommons.py -replaceonly -hash -replace -replaceloose -replacealways

-- Known issues --
Please fix these if you are capable and motivated:
- if a file marked nowcommons is not present on Wikimedia Commons, the bot
  will exit.
"""
#
# (C) Wikipedian, 2006-2007
# (C) Siebrand Mazeland, 2007-2008
# (C) xqt, 2010-2014
# (C) Pywikibot team, 2006-2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import sys
import re
import webbrowser
import urllib
import pywikibot
from pywikibot import i18n
from pywikibot import pagegenerators as pg
import image
from imagetransfer import nowCommonsMessage

nowCommons = {
    '_default': [
        u'NowCommons'
    ],
    'ar': [
        u'الآن كومنز',
        u'الآن كومونز',
    ],
    'de': [
        u'NowCommons',
        u'NC',
        u'NCT',
        u'Nowcommons',
        u'NowCommons/Mängel',
        u'NowCommons-Überprüft',
    ],
    'en': [
        u'NowCommons',
        u'Ncd',
    ],
    'eo': [
        u'Nun en komunejo',
        u'NowCommons',
    ],
    'fa': [
        u'موجود در انبار',
        u'NowCommons',
    ],
    'fr': [
        u'Image sur Commons',
        u'DoublonCommons',
        u'Déjà sur Commons',
        u'Maintenant sur commons',
        u'Désormais sur Commons',
        u'NC',
        u'NowCommons',
        u'Nowcommons',
        u'Sharedupload',
        u'Sur Commons',
        u'Sur Commons2',
    ],
    'he': [
        u'גם בוויקישיתוף'
    ],
    'hu': [
        u'Azonnali-commons',
        u'NowCommons',
        u'Nowcommons',
        u'NC'
    ],
    'ia': [
        u'OraInCommons'
    ],
    'it': [
        u'NowCommons',
    ],
    'ja': [
        u'NowCommons',
    ],
    'ko': [
        u'NowCommons',
        u'공용중복',
        u'공용 중복',
        u'Nowcommons',
    ],
    'nds-nl': [
        u'NoenCommons',
        u'NowCommons',
    ],
    'nl': [
        u'NuCommons',
        u'Nucommons',
        u'NowCommons',
        u'Nowcommons',
        u'NCT',
        u'Nct',
    ],
    'ro': [
        u'NowCommons'
    ],
    'ru': [
        u'NowCommons',
        u'NCT',
        u'Nowcommons',
        u'Now Commons',
        u'Db-commons',
        u'Перенесено на Викисклад',
        u'На Викискладе',
    ],
    'zh': [
        u'NowCommons',
        u'Nowcommons',
        u'NCT',
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

# Stemma and stub are images not to be deleted (and are a lot) on it.wikipedia
# if your project has images like that, put the word often used here to skip them
word_to_skip = {
    'en': [],
    'it': ['stemma', 'stub', 'hill40 '],
}

#nowCommonsMessage = imagetransfer.nowCommonsMessage


class NowCommonsDeleteBot:
    def __init__(self):
        self.site = pywikibot.getSite()
        if repr(self.site) == 'commons:commons':
            sys.exit('Do not run this bot on Commons!')

    def ncTemplates(self):
        if self.site.lang in nowCommons:
            return nowCommons[self.site.lang]
        else:
            return nowCommons['_default']

    def useHashGenerator(self):
        # http://toolserver.org/~multichill/nowcommons.php?language=it&page=2&filter=
        lang = self.site.lang
        num_page = 0
        word_to_skip_translated = i18n.translate(self.site, word_to_skip)
        images_processed = list()
        while 1:
            url = ('http://toolserver.org/~multichill/nowcommons.php?'
                   'language=%s&page=%s&filter=') % (lang, num_page)
            HTML_text = self.site.getUrl(url, no_hostname=True)
            reg = r'<[Aa] href="(?P<urllocal>.*?)">(?P<imagelocal>.*?)</[Aa]> +?</td><td>\n\s*?'
            reg += r'<[Aa] href="(?P<urlcommons>http://commons.wikimedia.org/.*?)" \
                   >Image:(?P<imagecommons>.*?)</[Aa]> +?</td><td>'
            regex = re.compile(reg, re.UNICODE)
            found_something = False
            change_page = True
            for x in regex.finditer(HTML_text):
                found_something = True
                image_local = x.group('imagelocal')
                image_commons = x.group('imagecommons')
                if image_local in images_processed:
                    continue
                change_page = False
                images_processed.append(image_local)
                # Skip images that have something in the title (useful for it.wiki)
                image_to_skip = False
                for word in word_to_skip_translated:
                    if word.lower() in image_local.lower():
                        image_to_skip = True
                if image_to_skip:
                    continue
                url_local = x.group('urllocal')
                url_commons = x.group('urlcommons')
                pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                                 % image_local)
                pywikibot.output(u'Local: %s\nCommons: %s\n'
                                 % (url_local, url_commons))
                result1 = webbrowser.open(url_local, 0, 1)
                result2 = webbrowser.open(url_commons, 0, 1)
                if image_local.split('Image:')[1] == image_commons:
                    choice = pywikibot.inputChoice(
                        u'The local and the commons images have the same name, continue?',
                        ['Yes', 'No'], ['y', 'N'], 'N')
                else:
                    choice = pywikibot.inputChoice(
                        u'Are the two images equal?',
                        ['Yes', 'No'], ['y', 'N'], 'N')
                if choice.lower() in ['y', 'yes']:
                    yield [image_local, image_commons]
                else:
                    continue
            # The page is dinamically updated, so we may don't need to change it
            if change_page:
                num_page += 1
            # If no image found means that there aren't anymore, break.
            if not found_something:
                break

    def getPageGenerator(self):
        if use_hash:
            gen = self.useHashGenerator()
        else:
            nowCommonsTemplates = [pywikibot.Page(self.site, title,
                                                  defaultNamespace=10)
                                   for title in self.ncTemplates()]
            gens = [pg.ReferringPageGenerator(t, followRedirects=True,
                                              onlyTemplateInclusion=True)
                    for t in nowCommonsTemplates]
            gen = pg.CombinedPageGenerator(gens)
            gen = pg.NamespaceFilterPageGenerator(gen, [6])
            gen = pg.DuplicateFilterPageGenerator(gen)
            gen = pg.PreloadingGenerator(gen)
        return gen

    def findFilenameOnCommons(self, localImagePage):
        filenameOnCommons = None
        for templateName, params in localImagePage.templatesWithParams():
            if templateName in self.ncTemplates():
                if params == []:
                    filenameOnCommons = localImagePage.title(withNamespace=False)
                elif self.site.lang in namespaceInTemplate:
                    skip = False
                    filenameOnCommons = None
                    for par in params:
                        val = par.split('=')
                        if len(val) == 1 and not skip:
                            filenameOnCommons = par[par.index(':') + 1:]
                            break
                        if val[0].strip() == '1':
                            filenameOnCommons = val[1].strip()[val[1].strip().index(':') + 1:]
                            break
                        skip = True
                    if not filenameOnCommons:
                        filenameOnCommons = localImagePage.title(withNamespace=False)
                else:
                    val = params[0].split('=')
                    if len(val) == 1:
                        filenameOnCommons = params[0].strip()
                    else:
                        filenameOnCommons = val[1].strip()
                return filenameOnCommons

    # Function stolen from wikipedia.py and modified. Really needed?
    def urlname(self, talk_page):
        """The name of the page this Page refers to, in a form suitable for the
        URL of the page.

        """
        title = talk_page.replace(" ", "_")
        encodedTitle = title.encode(self.site.encoding())
        return urllib.quote(encodedTitle)

    def run(self):
        commons = pywikibot.getSite('commons', 'commons')
        comment = i18n.translate(self.site, nowCommonsMessage)

        for page in self.getPageGenerator():
            if use_hash:
                # Page -> Has the namespace | commons image -> Not
                images_list = page    # 0 -> local image, 1 -> commons image
                page = pywikibot.Page(self.site, images_list[0])
            else:
                # If use_hash is true, we have already print this before, no need
                # Show the title of the page we're working on.
                # Highlight the title in purple.
                pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                                 % page.title())
            try:
                localImagePage = pywikibot.ImagePage(self.site, page.title())
                if localImagePage.fileIsOnCommons():
                    pywikibot.output(u'File is already on Commons.')
                    continue
                md5 = localImagePage.getFileMd5Sum()
                if use_hash:
                    filenameOnCommons = images_list[1]
                else:
                    filenameOnCommons = self.findFilenameOnCommons(
                        localImagePage)
                if not filenameOnCommons and not use_hash:
                    pywikibot.output(u'NowCommons template not found.')
                    continue
                commonsImagePage = pywikibot.ImagePage(commons, 'Image:%s'
                                                       % filenameOnCommons)
                if localImagePage.title(withNamespace=False) == \
                 commonsImagePage.title(withNamespace=False) and use_hash:
                    pywikibot.output(
                        u'The local and the commons images have the same name')
                if localImagePage.title(withNamespace=False) != \
                 commonsImagePage.title(withNamespace=False):
                    usingPages = list(localImagePage.usingPages())
                    if usingPages and usingPages != [localImagePage]:
                        pywikibot.output(
                            u'\"\03{lightred}%s\03{default}\" is still used in %i pages.'
                            % (localImagePage.title(withNamespace=False),
                               len(usingPages)))
                        if replace is True:
                                pywikibot.output(
                                    u'Replacing \"\03{lightred}%s\03{default}\" by \
                                    \"\03{lightgreen}%s\03{default}\".'
                                    % (localImagePage.title(withNamespace=False),
                                       commonsImagePage.title(withNamespace=False)))
                                oImageRobot = image.ImageRobot(
                                    pg.FileLinksGenerator(localImagePage),
                                    localImagePage.title(withNamespace=False),
                                    commonsImagePage.title(withNamespace=False),
                                    '', replacealways, replaceloose)
                                oImageRobot.run()
                                # If the image is used with the urlname the
                                # previous function won't work
                                if len(list(pywikibot.ImagePage(self.site,
                                                                page.title()).usingPages())) > 0 and \
                                                                replaceloose:
                                    oImageRobot = image.ImageRobot(
                                        pg.FileLinksGenerator(
                                            localImagePage),
                                        self.urlname(
                                            localImagePage.title(
                                                withNamespace=False)),
                                        commonsImagePage.title(
                                            withNamespace=False),
                                        '', replacealways, replaceloose)
                                    oImageRobot.run()
                                # refresh because we want the updated list
                                usingPages = len(list(pywikibot.ImagePage(
                                    self.site, page.title()).usingPages()))
                                if usingPages > 0 and use_hash:
                                    # just an enter
                                    pywikibot.input(
                                        u'There are still %s pages with this \
                                        image, confirm the manual removal from them please.'
                                        % usingPages)

                        else:
                            pywikibot.output(u'Please change them manually.')
                        continue
                    else:
                        pywikibot.output(
                            u'No page is using \"\03{lightgreen}%s\03{default}\" anymore.'
                            % localImagePage.title(withNamespace=False))
                commonsText = commonsImagePage.get()
                if replaceonly is False:
                    if md5 == commonsImagePage.getFileMd5Sum():
                        pywikibot.output(
                            u'The image is identical to the one on Commons.')
                        if len(localImagePage.getFileVersionHistory()) > 1 and not use_hash:
                            pywikibot.output(
                                u"This image has a version history. Please \
                                delete it manually after making sure that the \
                                old versions are not worth keeping.""")
                            continue
                        if autonomous is False:
                            pywikibot.output(
                                u'\n\n>>>> Description on \03{lightpurple}%s\03{default} <<<<\n'
                                % page.title())
                            pywikibot.output(localImagePage.get())
                            pywikibot.output(
                                u'\n\n>>>> Description on \03{lightpurple}%s\03{default} <<<<\n'
                                % commonsImagePage.title())
                            pywikibot.output(commonsText)
                            choice = pywikibot.inputChoice(u'Does the description \
                                                           on Commons contain all required source and license\n'
                                                           u'information?',
                                                           ['yes', 'no'], ['y', 'N'], 'N')
                            if choice.lower() in ['y', 'yes']:
                                localImagePage.delete(
                                    comment + ' [[:commons:Image:%s]]'
                                    % filenameOnCommons, prompt=False)
                        else:
                            localImagePage.delete(
                                comment + ' [[:commons:Image:%s]]'
                                % filenameOnCommons, prompt=False)
                    else:
                        pywikibot.output(
                            u'The image is not identical to the one on Commons.')
            except (pywikibot.NoPage, pywikibot.IsRedirectPage) as e:
                pywikibot.output(u'%s' % e[0])
                continue


def main():
    global autonomous
    global replace, replacealways, replaceloose, replaceonly
    global use_hash
    autonomous = False
    replace = False
    replacealways = False
    replaceloose = False
    replaceonly = False
    use_hash = False

    for arg in pywikibot.handleArgs():
        if arg == '-autonomous':
            autonomous = True
        if arg == '-replace':
            replace = True
        if arg == '-replacealways':
            replace = True
            replacealways = True
        if arg == '-replaceloose':
            replaceloose = True
        if arg == '-replaceonly':
            replaceonly = True
        if arg == '-hash':
            use_hash = True
    bot = NowCommonsDeleteBot()
    bot.run()

if __name__ == "__main__":
    main()
