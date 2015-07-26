#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Correct all redirect links in featured pages or only one page of each wiki.

Can be using with:
&params;

-featured         Run over featured pages

Run fixing_redirects.py -help to see all the command-line
options -file, -ref, -links, ...

"""
#
# This script based on disambredir.py and solve_disambiguation.py
#
# (C) Pywikibot team, 2004-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#
import sys
import pywikibot
from pywikibot import pagegenerators
from pywikibot import i18n

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;':     pagegenerators.parameterHelp,
}

featured_articles = {
    'ar': u'ويكيبيديا:مقالات مختارة',
    'cs': u'Wikipedie:Nejlepší články',
    'de': u'Wikipedia:Exzellente_Artikel',
    'en': u'Wikipedia:Featured_articles',
    'es': u'Wikipedia:Artículos_destacados',
    'fa': u'ویکی‌پدیا:نوشتارهای برگزیده',
    'fr': u'Wikipédia:Articles_de_qualité',
    'he': u'פורטל:ערכים_מומלצים',
    'is': u'Wikipedia:Úrvalsgreinar',
    'it': u'Wikipedia:Articoli_in_vetrina',
    'ja': u'Wikipedia:秀逸な記事',
    'nl': u'Wikipedia:Etalage',
    'nn': u'Wikipedia:Gode artiklar',
    'no': u'Wikipedia:Anbefalte artikler',
    'pl': u'Wikipedia:Artykuły_na_medal',
    'pt': u'Wikipedia:Os_melhores_artigos',
    'sv': u'Wikipedia:Utvalda_artiklar',
    'vi': u'Wikipedia:Bài_viết_chọn_lọc',
    'zh': u'Wikipedia:特色条目',
}


pageCache = []


def workon(page):
    """Change all redirects from the given page to actual links."""
    mysite = pywikibot.Site()
    try:
        text = page.get()
    except pywikibot.IsRedirectPage:
        pywikibot.output(u'%s is a redirect page. Skipping' % page)
        return
    except pywikibot.NoPage:
        pywikibot.output(u'%s does not exist. Skipping' % page)
        return
    pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                     % page.title())
    links = page.linkedPages()
    if links is not None:
        links = pagegenerators.PreloadingGenerator(links)
#        pywikibot.getall(mysite, links)
    else:
        pywikibot.output('Nothing left to do.')
        return

    for page2 in links:
        try:
            target = page2.getRedirectTarget()
        except pywikibot.NoPage:
            try:
                target = page2.getMovedTarget()
            except (pywikibot.NoPage, pywikibot.BadTitle):
                continue
        except (pywikibot.Error, pywikibot.SectionError):
            continue
        # no fix to user namespaces
        if target.namespace() in [0, 1] and not page2.namespace() in [0, 1]:
            continue
        text = pywikibot.textlib.replace_links(text, [page2, target])
    if text != page.get():
        comment = i18n.twtranslate(mysite, 'fixing_redirects-fixing')
        pywikibot.showDiff(page.get(), text)
        try:
            page.put(text, comment)
        except (pywikibot.Error):
            pywikibot.error('unable to put %s' % page)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    featured = False
    gen = None

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-featured':
            featured = True
        else:
            genFactory.handleArg(arg)

    mysite = pywikibot.Site()
    if mysite.sitename() == 'wikipedia:nl':
        pywikibot.output(
            u'\03{lightred}There is consensus on the Dutch Wikipedia that bots should not be used to fix redirects.\03{default}')
        sys.exit()

    if featured:
        featuredList = i18n.translate(mysite, featured_articles)
        ref = pywikibot.Page(pywikibot.Site(), featuredList)
        gen = ref.getReferences(namespaces=[0])
    if not gen:
        gen = genFactory.getCombinedGenerator()
    if gen:
        for page in pagegenerators.PreloadingGenerator(gen):
            workon(page)
        return True
    else:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False

if __name__ == "__main__":
    main()
