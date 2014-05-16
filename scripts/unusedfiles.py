#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This bot appends some text to all unused images and other text to the
respective uploaders.

Parameters:

-always     Don't be asked every time.

"""

#
# (C) Leonardo Gregianin, 2007
# (C) Filnik, 2008
# (c) xqt, 2011-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import pywikibot
from pywikibot import pagegenerators

comment = {
    'ar': u'صور للاستبعاد',
    'en': u'images for elimination',
    'fa': u'تصویر استفاده نشده',
    'he': u'תמונות להסרה',
    'it': u'Bot: segnalo immagine orfana da eliminare',
    'pt': u'Bot: marcação de imagens para eliminação',
}

template_to_the_image = {
    'en': u'{{subst:No-use2}}',
    'it': u'{{immagine orfana}}',
    'fa': u'{{تصاویر بدون استفاده}}',
}
template_to_the_user = {
    'en': u'\n\n{{img-sem-uso|%(title)s}}',
    'fa': u'\n\n{{جا:اخطار به کاربر برای تصاویر بدون استفاده|%(title)s}}--~~~~',
    'it': u'\n\n{{Utente:Filbot/Immagine orfana}}',
}
except_text = {
    'en': u'<table id="mw_metadata" class="mw_metadata">',
    'it': u'<table id="mw_metadata" class="mw_metadata">',
}


def appendtext(page, apptext, always):
    if page.isRedirectPage():
        page = page.getRedirectTarget()
    if not page.exists():
        if page.isTalkPage():
            text = u''
        else:
            raise pywikibot.NoPage(u"Page '%s' does not exist" % page.title())
    else:
        text = page.text
    # Here you can go editing. If you find you do not
    # want to edit this page, just return
    oldtext = text
    text += apptext
    if text != oldtext:
        pywikibot.showDiff(oldtext, text)
        if not always:
            choice = pywikibot.inputChoice(
                u'Do you want to accept these changes?', ['Yes', 'No', 'All'],
                'yNa', 'N')
            if choice == 'a':
                always = True
        if always or choice == 'y':
            page.text = text
            page.save(pywikibot.translate(pywikibot.Site(), comment,
                                          fallback=True))


def main():
    always = False

    for arg in pywikibot.handleArgs():
        if arg == '-always':
            always = True

    mysite = pywikibot.Site()
    # If anything needs to be prepared, you can do it here
    template_image = pywikibot.translate(pywikibot.Site(),
                                         template_to_the_image)
    template_user = pywikibot.translate(pywikibot.Site(),
                                        template_to_the_user)
    except_text_translated = pywikibot.translate(pywikibot.Site(), except_text)
    if not(template_image and template_user and except_text_translated):
        pywikibot.warning(u'This script is not localized for %s site.' % mysite)
        return
    generator = pagegenerators.UnusedFilesGenerator()
    generator = pagegenerators.PreloadingGenerator(generator)
    for image in generator:
        if (except_text_translated.encode('utf-8')
                not in image.getImagePageHtml() and
                u'http://' not in image.text):
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                             % image.title())
            if template_image in image.text:
                pywikibot.output(u"%s done already"
                                 % image.title(asLink=True))
                continue
            appendtext(image, u"\n\n" + template_image, always)
            uploader = image.getFileVersionHistory().pop(0)['user']
            user = pywikibot.User(mysite, uploader)
            usertalkpage = user.getUserTalkPage()
            msg2uploader = template_user % {'title': image.title()}
            appendtext(usertalkpage, msg2uploader, always)


if __name__ == "__main__":
    main()
