#!/usr/bin/python
# coding: utf-8

"""
Include commons template in home wiki.

This bot functions mainly in the en.wikipedia, because it
compares the names of articles and category in English
language (standard language in Commons). If the name of
an article in Commons will not be in English but with
redirect, this also functions.

Run:
Syntax: python commons_link.py action [-option]

where action can be one of these:
 * pages      : Run over articles, include {{commons}}
 * categories : Run over categories, include {{commonscat}}

and option can be one of these:
 * -cat     : Work on all pages which are in a specific category.
 * -ref     : Work on all pages that link to a certain page.
 * -link    : Work on all pages that are linked from a certain page.
 * -start   : Work on all pages on the home wiki, starting at the named page.
 * -page    : Work on one page.

"""
#
# (C) Leonardo Gregianin, 2006
# (C) Pywikibot team, 2007-2013
#
# Distributed under the terms of the MIT license.
#
# Ported by Geoffrey "GEOFBOT" Mon for Google Code-In 2013
# User:Sn1per
#


__version__ = '$Id$'

import re
import pywikibot
from pywikibot import pagegenerators, i18n


class CommonsLinkBot:
    def __init__(self, generator, acceptall=False):
        self.generator = generator
        self.acceptall = acceptall

    def pages(self):
        for page in self.generator:
            try:
                pywikibot.output(u'\n>>>> %s <<<<' % page.title())
                commons = pywikibot.getSite().image_repository()
                commonspage = pywikibot.Page(commons, page.title())
                try:
                    getcommons = commonspage.get(get_redirect=True)
                    if page.title() == commonspage.title():
                        oldText = page.get()
                        text = oldText

                        # for commons template
                        findTemplate = re.compile(ur'\{\{[Cc]ommonscat')
                        s = findTemplate.search(text)
                        findTemplate2 = re.compile(ur'\{\{[Ss]isterlinks')
                        s2 = findTemplate2.search(text)
                        if s or s2:
                            pywikibot.output(u'** Already done.')
                        else:
                            text = pywikibot.replaceCategoryLinks(
                                text + u'{{commons|%s}}' % commonspage.title(),
                                list(page.categories()))
                            if oldText != text:
                                pywikibot.showDiff(oldText, text)
                                if not self.acceptall:
                                    choice = pywikibot.inputChoice(
                                        u'Do you want to accept these changes?',
                                        ['Yes', 'No', 'All'], ['y', 'N', 'a'],
                                        'N')
                                    if choice == 'a':
                                        self.acceptall = True
                                if self.acceptall or choice == 'y':
                                    try:
                                        msg = i18n.twtranslate(
                                            pywikibot.getSite(), 'commons_link-template-added')
                                        page.put(text, msg)
                                    except pywikibot.EditConflict:
                                        pywikibot.output(
                                            u'Skipping %s because of edit '
                                            u'conflict'
                                            % (page.title()))

                except pywikibot.NoPage:
                    pywikibot.output(u'Page does not exist in Commons!')

            except pywikibot.NoPage:
                pywikibot.output(u'Page %s does not exist?!' % page.title())
            except pywikibot.IsRedirectPage:
                pywikibot.output(u'Page %s is a redirect; skipping.'
                                 % page.title())
            except pywikibot.LockedPage:
                pywikibot.output(u'Page %s is locked?!' % page.title())

    def categories(self):
        for page in self.generator:
            try:
                pywikibot.output(u'\n>>>> %s <<<<' % page.title())
                commons = pywikibot.getSite().image_repository()
                commonsCategory = pywikibot.Category(commons,
                                                     'Category:%s' % page.title())
                try:
                    getcommonscat = commonsCategory.get(get_redirect=True)
                    commonsCategoryTitle = commonsCategory.title()
                    categoryname = commonsCategoryTitle.split('Category:', 1)[1]
                    if page.title() == categoryname:
                        oldText = page.get()
                        text = oldText

                        # for commonscat template
                        findTemplate = re.compile(ur'\{\{[Cc]ommons')
                        s = findTemplate.search(text)
                        findTemplate2 = re.compile(ur'\{\{[Ss]isterlinks')
                        s2 = findTemplate2.search(text)
                        if s or s2:
                            pywikibot.output(u'** Already done.')
                        else:
                            text = pywikibot.replaceCategoryLinks(
                                text + u'{{commonscat|%s}}' % categoryname,
                                list(page.categories()))
                            if oldText != text:
                                pywikibot.showDiff(oldText, text)
                                if not self.acceptall:
                                    choice = pywikibot.inputChoice(
                                        u'Do you want to accept these changes?',
                                        ['Yes', 'No', 'All'], ['y', 'N', 'a'],
                                        'N')
                                    if choice == 'a':
                                        self.acceptall = True
                                if self.acceptall or choice == 'y':
                                    try:
                                        msg = i18n.twtranslate(
                                            pywikibot.getSite(), 'commons_link-cat-template-added')
                                        page.put(text, msg)
                                    except pywikibot.EditConflict:
                                        pywikibot.output(
                                            u'Skipping %s because of edit '
                                            u'conflict'
                                            % (page.title()))

                except pywikibot.NoPage:
                    pywikibot.output(u'Category does not exist in Commons!')

            except pywikibot.NoPage:
                pywikibot.output(u'Page %s does not exist?!' % page.title())
            except pywikibot.IsRedirectPage:
                pywikibot.output(u'Page %s is a redirect; skipping.'
                                 % page.title())
            except pywikibot.LockedPage:
                pywikibot.output(u'Page %s is locked?!' % page.title())

if __name__ == "__main__":
    singlepage = []
    gen = None
    start = None
    try:
        action = None
        for arg in pywikibot.handleArgs():
            if arg == ('pages'):
                action = 'pages'
            elif arg == ('categories'):
                action = 'categories'
            elif arg.startswith('-start:'):
                start = pywikibot.Page(pywikibot.getSite(), arg[7:])
                gen = pagegenerators.AllpagesPageGenerator(
                    start.title(withNamespace=False),
                    namespace=start.namespace(),
                    includeredirects=False)
            elif arg.startswith('-cat:'):
                cat = pywikibot.Category(pywikibot.getSite(),
                                         'Category:%s' % arg[5:])
                gen = pagegenerators.CategorizedPageGenerator(cat)
            elif arg.startswith('-ref:'):
                ref = pywikibot.Page(pywikibot.getSite(), arg[5:])
                gen = pagegenerators.ReferringPageGenerator(ref)
            elif arg.startswith('-link:'):
                link = pywikibot.Page(pywikibot.getSite(), arg[6:])
                gen = pagegenerators.LinkedPageGenerator(link)
            elif arg.startswith('-page:'):
                singlepage = pywikibot.Page(pywikibot.getSite(), arg[6:])
                gen = iter([singlepage])
            #else:
                #bug

        if action == 'pages':
            preloadingGen = pagegenerators.PreloadingGenerator(gen)
            bot = CommonsLinkBot(preloadingGen, acceptall=False)
            bot.pages()
        elif action == 'categories':
            preloadingGen = pagegenerators.PreloadingGenerator(gen)
            bot = CommonsLinkBot(preloadingGen, acceptall=False)
            bot.categories()
        else:
            pywikibot.showHelp(u'commons_link')
    finally:
        pywikibot.stopme()
