# -*- coding: utf-8 -*-
#!/usr/bin/python

"""
Script to remove links that are being or have been spammed.
Usage:

spamremove.py www.spammedsite.com

It will use Special:Linksearch to find the pages on the wiki that link to
that site, then for each page make a proposed change consisting of removing
all the lines where that url occurs. You can choose to:
* accept the changes as proposed
* edit the page yourself to remove the offending link
* not change the page in question

Command line options:
-automatic: Do not ask, but remove the lines automatically. Be very careful
              in using this option!

-namespace: Filters the search to a given namespace.  If this is specified
              multiple times it will search all given namespaces

"""

#
# (C) Pywikipedia bot team, 2007-2010
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

#

import pywikibot
from pywikibot import config
from pywikibot import pagegenerators
import editarticle
import sys


def main():
    automatic = False
    namespaces = []
    msg = {
        'ar': u'إزالة الوصلات إلى موقع سبام %s',
        'de': u'Entferne in Spam-Blacklist eingetragenen Weblink auf %s',
        'en': u'Removing links to spamming site %s',
        'es': u'Removiendo enlaces a sitio publicitario %s',
        'fa': u'حذف پیوند به وبگاه هرزنگاری %s',
        'he': u'מסיר קישורים לאתר ספאם %s',
        'fr': u'Suppression du lien blacklisté %s',
        'it': u'Rimuovo link contenuto nella Spam-Blacklist %s',
        'ja': u'ロボットによる: 迷惑リンク削除 %s',
        'nl': u'Links naar gespamde site: %s verwijderd',
        'pt': u'Removendo links de spam do site %s',
        'ta': u'எரிதமாக இணைக்கப்பட்ட %s இணையத்தளம் நீக்கப்பட்டது',
        'vi': u'xóa các liên kết đến website spam %s',
        'zh': u'機器人: 移除廣告黑名單連結 %s',
    }
    spamSite = ''
    for arg in pywikibot.handleArgs():
        if arg.startswith("-automatic"):
            automatic = True
        elif arg.startswith('-namespace:'):
            try:
                namespaces.append(int(arg[len('-namespace:'):]))
            except ValueError:
                namespaces.append(arg[len('-namespace:'):])
        else:
            spamSite = arg
    if not automatic:
        config.put_throttle = 1
    if not spamSite:
        pywikibot.showHelp('spamremove')
        pywikibot.output(u"No spam site specified.")
        sys.exit()
    mysite = pywikibot.getSite()
    pages = list(set(mysite.exturlusage(spamSite)))
    if namespaces:
        pages = list(set(pagegenerators.NamespaceFilterPageGenerator(pages,
                                                                     namespaces)))
    if len(pages) == 0:
        pywikibot.output('No page found.')
    else:
        pywikibot.output('%d pages found.' % len(pages))
        for p in pages:
            text = p.get()
            if not spamSite in text:
                continue
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                             % p.title())
            lines = text.split('\n')
            newpage = []
            lastok = ""
            for line in lines:
                if spamSite in line:
                    if lastok:
                        pywikibot.output(lastok)
                    pywikibot.output('\03{lightred}%s\03{default}' % line)
                    lastok = None
                else:
                    newpage.append(line)
                    if line.strip():
                        if lastok is None:
                            pywikibot.output(line)
                        lastok = line
            if automatic:
                answer = "y"
            else:
                answer = pywikibot.inputChoice(u'\nDelete the red lines?',
                                               ['yes', 'no', 'edit'],
                                               ['y', 'N', 'e'], 'n')
            if answer == "n":
                continue
            elif answer == "e":
                editor = editarticle.TextEditor()
                newtext = editor.edit(text, highlight=spamSite,
                                      jumpIndex=text.find(spamSite))
            else:
                newtext = "\n".join(newpage)
            if newtext != text:
                p.put(newtext, pywikibot.translate(mysite, msg) % spamSite)

try:
    main()
finally:
    pywikibot.stopme()
