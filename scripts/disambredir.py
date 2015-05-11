#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
User assisted updating redirect links on disambiguation pages.

Usage:
    python disambredir.py [start]

If no starting name is provided, the bot starts at '!'.

"""
#
# (C) André Engels, 2006-2009
# (C) Pywikibot team, 2006-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#
import re
import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.tools import first_lower, first_upper as firstcap

msg = {
    'ar': u'تغيير التحويلات في صفحة توضيح',
    'be-x-old': u'Замена перанакіраваньняў на старонку неадназначнасьцяў',
    'en': u'Changing redirects on a disambiguation page',
    'he': u'משנה קישורים להפניות בדף פירושונים',
    'fa': u'اصلاح تغییرمسیرها در یک صفحه ابهام‌زدایی',
    'ja': u'ロボットによる: 曖昧さ回避ページのリダイレクト修正',
    'nl': u'Verandering van redirects op een doorverwijspagina',
    'pl': u'Zmiana przekierowań na stronie ujednoznaczającej',
    'pt': u'Arrumando redirects na página de desambiguação',
    'ru': u'Изменение перенаправлений на странице неоднозначности',
    'uk': u'Зміна перенаправлень на сторінці багатозначності',
    'zh': u'機器人: 修改消歧義頁中的重定向連結',
}


def treat(text, linkedPage, targetPage):
    """Based on the method of the same name in solve_disambiguation.py."""
    # make a backup of the original text so we can show the changes later
    mysite = pywikibot.Site()
    linktrail = mysite.linktrail()
    linkR = re.compile(
        r'\[\[(?P<title>[^\]\|#]*)(?P<section>#[^\]\|]*)?(\|(?P<label>[^\]]*))?\]\](?P<linktrail>%s)'
        % linktrail)
    curpos = 0
    # This loop will run until we have finished the current page
    while True:
        m = linkR.search(text, pos=curpos)
        if not m:
            break
        # Make sure that next time around we will not find this same hit.
        curpos = m.start() + 1
        # ignore interwiki links and links to sections of the same page
        if m.group('title') == '' or mysite.isInterwikiLink(m.group('title')):
            continue
        else:
            actualLinkPage = pywikibot.Page(mysite, m.group('title'))
            # Check whether the link found is to page.
            if actualLinkPage != linkedPage:
                continue

        # how many bytes should be displayed around the current link
        context = 30
        # at the beginning of the link, start red color.
        # at the end of the link, reset the color to default
        pywikibot.output(text[max(0, m.start() - context): m.start()] +
                         '\03{lightred}' + text[m.start(): m.end()] +
                         '\03{default}' + text[m.end(): m.end() + context])
        choice = pywikibot.input_choice(
            'What should be done with the link?',
            (('Do not change', 'n'),
             ('Change link to \03{lightpurple}%s\03{default}'
              % targetPage.title(), 'y'),
             ('Change and replace text', 'r'), ('Unlink', 'u')),
            default='n', automatic_quit=False)

        if choice == 'n':
            continue

        # The link looks like this:
        # [[page_title|link_text]]trailing_chars
        page_title = m.group('title')
        link_text = m.group('label')
        if not link_text:
            # or like this: [[page_title]]trailing_chars
            link_text = page_title
        if m.group('section') is None:
            section = ''
        else:
            section = m.group('section')
        trailing_chars = m.group('linktrail')
        if trailing_chars:
            link_text += trailing_chars

        if choice == 'u':
            # unlink - we remove the section if there's any
            text = text[:m.start()] + link_text + text[m.end():]
            continue

        if link_text[0].isupper():
            new_page_title = targetPage.title()
        else:
            new_page_title = first_lower(targetPage.title())
        if choice == 'r' and trailing_chars:
            newlink = "[[%s%s]]%s" % (new_page_title, section, trailing_chars)
        elif choice == 'r' or (new_page_title == link_text and not section):
            newlink = "[[%s]]" % new_page_title
        # check if we can create a link with trailing characters instead of a
        # pipelink
        elif len(new_page_title) <= len(link_text) and \
             firstcap(link_text[:len(new_page_title)]) == \
             firstcap(new_page_title) and \
             re.sub(re.compile(linktrail), '', link_text[len(new_page_title):]) == '' and not section:
            newlink = "[[%s]]%s" % (link_text[:len(new_page_title)],
                                    link_text[len(new_page_title):])
        else:
            newlink = "[[%s%s|%s]]" % (new_page_title, section, link_text)
        text = text[:m.start()] + newlink + text[m.end():]
        continue
    return text


def workon(page, links):
    """Execute treat for the given page which is linking to the given links."""
    text = page.get()
    # Show the title of the page we're working on.
    # Highlight the title in purple.
    pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                     % page.title())
    for page2 in links:
        try:
            target = page2.getRedirectTarget()
        except (pywikibot.Error, pywikibot.SectionError):
            continue
        text = treat(text, page2, target)
    if text != page.get():
        comment = i18n.translate(page.site, msg, fallback=True)
        page.put(text, comment)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    local_args = pywikibot.handle_args(args)

    start = local_args[0] if local_args else '!'

    mysite = pywikibot.Site()
    try:
        mysite.disambcategory()
    except pywikibot.Error as e:
        pywikibot.output(e)
        pywikibot.showHelp()
        return

    generator = pagegenerators.CategorizedPageGenerator(
        mysite.disambcategory(), start=start, content=True, namespaces=[0])

    # only work on articles
    pagestodo = []
    pagestoload = []
    for page in generator:
        if page.isRedirectPage():
            continue
        linked = page.linkedPages()
        pagestodo.append((page, linked))
        pagestoload += linked
        if len(pagestoload) > 49:
            pagestoload = pagegenerators.PreloadingGenerator(pagestoload)
            for page, links in pagestodo:
                workon(page, links)
            pagestoload = []
            pagestodo = []


if __name__ == "__main__":
    main()
