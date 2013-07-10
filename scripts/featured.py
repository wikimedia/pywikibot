#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script understands various command-line arguments:

 Task commands:

-featured         use this script for featured articles. Default task if no task
                  command is specified

-good             use this script for good articles.

-lists            use this script for featured lists.

-former           use this script for removing {{Link FA|xx}} from former
                  fearured articles

                  NOTE: you may have all of these commands in one run

 Option commands:

-interactive:     ask before changing each page

-nocache          doesn't include cache files file to remember if the article
                  already was verified.
                  
-nocache:xx,yy    you may ignore language codes xx,yy,... from cache file

-fromlang:xx,yy   xx,yy,zz,.. are the languages to be verified.
-fromlang:ar--fi  Another possible with range the languages
                  (sorry, not implemented yet)

-fromall          to verify all languages.

-tolang:xx,yy     xx,yy,zz,.. are the languages to be updated

-after:zzzz       process pages after and including page zzzz
                  (sorry, not implemented yet)

-side             use -side if you want to move all {{Link FA|lang}} next to the
                  corresponding interwiki links. Default is placing
                  {{Link FA|lang}} on top of the interwiki links.
                  (This option is deprecated with wikidata)

-count            Only counts how many featured/good articles exist
                  on all wikis (given with the "-fromlang" argument) or
                  on several language(s) (when using the "-fromall" argument).
                  Example: featured.py -fromlang:en,he -count
                  counts how many featured articles exist in the en and he
                  wikipedias.
                  (sorry, not implemented yet)

-quiet            no corresponding pages are displayed.

"""
__version__ = '$Id$'

#
# (C) Maxim Razin, 2005
# (C) Leonardo Gregianin, 2005-2008
# (C) xqt, 2009-2013
# (C) Pywikipedia bot team, 2005-2012
#
# Distributed under the terms of the MIT license.
#

import os.path
import pickle
import re
import sys
from copy import copy
import pywikibot
from pywikibot import i18n
from pywikibot import config
from pywikibot.pagegenerators import PreloadingGenerator


def CAT(site, name, hide):
    name = site.namespace(14) + ':' + name
    cat = pywikibot.Category(site, name)
    for article in cat.articles(endsort=hide):
        yield article
    if hide:
        for article in cat.articles(startFrom=unichr(ord(hide) + 1)):
            yield article


def BACK(site, name, hide):
    p = pywikibot.Page(site, name, ns=10)
    return [page for page in p.getReferences(follow_redirects=False,
                                             onlyTemplateInclusion=True)]

def DATA(site, name, hide):
    dp = pywikibot.ItemPage(site.data_repository(), name)
    try:
        title = dp.getSitelink(site)
    except pywikibot.PageNotFound:
        return
    cat = pywikibot.Category(site, title)
    for article in cat.articles(endsort=hide):
        yield article
    if hide:
        for article in cat.articles(startFrom=unichr(ord(hide) + 1)):
            yield article


# not implemented yet
def TMPL(site, name, hide):
    return


# ALL wikis use 'Link FA', and sometimes other localized templates.
# We use _default AND the localized ones
template = {
    '_default': ['Link FA'],
    'als': ['LinkFA'],
    'an': ['Destacato', 'Destacau'],
    'ar': [u'وصلة مقالة مختارة'],
    'ast': ['Enllaz AD'],
    'az': ['Link FM'],
    'br': ['Liamm PuB', 'Lien AdQ'],
    'ca': [u'Enllaç AD', 'Destacat'],
    'cy': ['Cyswllt erthygl ddethol', 'Dolen ED'],
    'eo': ['LigoElstara'],
    'en': ['Link FA', 'FA link'],
    'es': ['Destacado'],
    'eu': ['NA lotura'],
    'fr': ['Lien AdQ'],
    'fur': ['Leam VdC'],
    'ga': ['Nasc AR'],
    'hi': ['Link FA', 'Lien AdQ'],
    'is': [u'Tengill ÚG'],
    'it': ['Link AdQ'],
    'no': ['Link UA'],
    'oc': ['Ligam AdQ', 'Lien AdQ'],
    'ro': [u'Legătură AC', u'Legătură AF'],
    'sv': ['UA', 'Link UA'],
    'tr': ['Link SM'],
    'vi': [u'Liên kết chọn lọc'],
    'vo': [u'Yüm YG'],
    'yi': [u'רא'],
}

template_good = {
    '_default': ['Link GA'],
    'ar': [u'وصلة مقالة جيدة'],
    'da': ['Link GA', 'Link AA'],
    'eo': ['LigoLeginda'],
    'es': ['Bueno'],
    'fr': ['Lien BA'],
    'is': ['Tengill GG'],
    'it': ['Link VdQ'],
    'nn': ['Link AA'],
    'no': ['Link AA'],
    'pt': ['Bom interwiki'],
##    'tr': ['Link GA', 'Link KM'],
    'vi': [u'Liên kết bài chất lượng tốt'],
    'wo': ['Lien BA'],
}

template_lists = {
    '_default': ['Link FL'],
    'no': ['Link GL'],
}

featured_name = {
    'wikidata': (DATA, u'Q4387444'),
}

good_name = {
    'wikidata': (DATA, 'Q7045856'),
}

lists_name = {
    'wikidata': (TMPL, 'Q5857568'),
    'ar': (BACK, u'قائمة مختارة'),
    'da': (BACK, u'FremragendeListe'),
    'de': (BACK, u'Informativ'),
    'en': (BACK, u'Featured list'),
    'fa': (BACK, u"فهرست برگزیده"),
    'id': (BACK, u'Featured list'),
    'ja': (BACK, u'Featured List'),
    'ksh': (CAT,  u"Joode Leß"),
    'no': (BACK, u'God liste'),
    'pl': (BACK, u'Medalista'),
    'pt': (BACK, u'Anexo destacado'),
    'ro': (BACK, u'Listă de calitate'),
    'ru': (BACK, u'Избранный список или портал'),
    'tr': (BACK, u'Seçkin liste'),
    'uk': (BACK, u'Вибраний список'),
    'vi': (BACK, u'Sao danh sách chọn lọc'),
    'zh': (BACK, u'特色列表'),
}

# Third parameter is the sort key indicating articles to hide from the given
# list
former_name = {
    'ca': (CAT, u"Arxiu de propostes de la retirada de la distinció"),
    'en': (CAT, u"Wikipedia former featured articles", "#"),
    'es': (CAT, u"Wikipedia:Artículos anteriormente destacados"),
    'fa': (CAT, u"مقاله‌های برگزیده پیشین"),
    'hu': (CAT, u"Korábbi kiemelt cikkek"),
    'pl': (CAT, u"Byłe artykuły na medal"),
    'pt': (CAT, u"!Ex-Artigos_destacados"),
    'ru': (CAT, u"Википедия:Устаревшие избранные статьи"),
    'th': (CAT, u"บทความคัดสรรในอดีต"),
    'tr': (CAT, u"Vikipedi eski seçkin maddeler"),
    'zh': (CAT, u"已撤销的特色条目"),
}


class FeaturedBot(pywikibot.Bot):
    # Bot configuration.
    # Only the keys of the dict can be passed as init options
    # The values are the default values
    availableOptions = {
        'always': False,  # ask for confirmation when putting a page?
        'async':  False,  # asynchron putting a page?
        'count': False,   # featuredcount
        'featured': False,
        'former': False,
        'fromall': False,
        'fromlang': None,
        'good': False,
        'list': False,
        'nocache': list(),
        'side': False,    # not template_on_top
        'quiet': False,
    }

    def __init__(self, **kwargs):
        """ Only accepts options defined in availableOptions """
        super(FeaturedBot, self).__init__(**kwargs)
        self.editcounter = 0
        self.fromlang = None
        self.cache = dict()
        self.filename = None
        self.site = pywikibot.Site()

    def hastemplate(self, task):
        for tl in self.getTemplateList(self.site.lang, task):
            tp = pywikibot.Page(self.site, tl, ns=10)
            if not tp.exists():
                return
        return True

    def readcache(self, task):
        if not self.getOption('nocache') is True:
            self.filename = pywikibot.config.datafilepath("cache", task)
            try:
                f = open(self.filename, "rb")
                self.cache = pickle.load(f)
                f.close()
                pywikibot.output(u'Cache file %s found with %d items.'
                                 % (self.filename, len(self.cache)))
            except IOError:
                pywikibot.output(u'Cache file %s not found.' % self.filename)

    def writecache(self):
        if not self.getOption('nocache') is True:
            pywikibot.output(u'Writing %d items to cache file %s.'
                             % (len(self.cache), self.filename))
            f = open(self.filename,"wb")
            pickle.dump(self.cache, f)
            f.close()
        self.cache = dict()

    def run(self):
        done = False
        if self.getOption('good'):
            self.run_good()
            done = True
        if self.getOption('list'):
            self.run_list()
            done = True
        if self.getOption('former'):
            self.run_former()
            done = True
        if self.getOption('featured') or not done:
            self.run_featured()
        pywikibot.output(u'%d pages written.' % self.editcounter)

    def run_good(self):
        task = 'good'
        if not self.hastemplate(task):
            pywikibot.output(u'\nNOTE: % arcticles are not implemented at %.'
                             % (task, site))
            return

        if self.getOption('fromall'):
            item_no = good_name['wikidata'][1]
            dp = pywikibot.ItemPage(pywikibot.Site().data_repository(), item_no)
            dp.get()

            ### Quick and dirty hack - any ideas?
            self.fromlang =  [key.replace('wiki', '').replace('_', '-')
                              for key in dp.sitelinks.keys()]
        else:
            return  ### 2DO
        self.fromlang.sort()
        self.readcache(task)
        for code in self.fromlang:
            try:
                self.treat(code, task)
            except KeyboardInterrupt:
                pywikibot.output('\nQuitting featured treat...')
                break
        self.writecache()

    # not implemented yet
    def run_list(self):
        return

    # not implemented yet
    def run_former(self):
        return

    def run_featured(self):
        task = 'featured'
        if not self.hastemplate(task):
            pywikibot.output(u'\nNOTE: % arcticles are not implemented at %.'
                             % (task, site))
            return

        if self.getOption('fromall'):
            item_no = featured_name['wikidata'][1]
            dp = pywikibot.ItemPage(pywikibot.Site().data_repository(), item_no)
            dp.get()

            ### Quick and dirty hack - any ideas?
            self.fromlang =  [key.replace('wiki', '').replace('_', '-')
                              for key in dp.sitelinks.keys()]
        else:
            return  ### 2DO
        self.fromlang.sort()
        self.readcache(task)
        for code in self.fromlang:
            try:
                self.treat(code, task)
            except KeyboardInterrupt:
                pywikibot.output('\nQuitting featured treat...')
                break
        self.writecache()            

    def treat(self, code, process):
        fromsite = pywikibot.Site(code)
        if fromsite != self.site:
            self.featuredWithInterwiki(fromsite,
                                       not self.getOption('side'),
                                       process,
                                       self.getOption('quiet'),
                                       config.simulate)

##    def load(self, page):
##        """
##        Loads the given page, does some changes, and saves it.
##        """
##        try:
##            # Load the page
##            text = page.get()
##        except pywikibot.NoPage:
##            pywikibot.output(u"Page %s does not exist; skipping."
##                             % page.title(asLink=True))
##        except pywikibot.IsRedirectPage:
##            pywikibot.output(u"Page %s is a redirect; skipping."
##                             % page.title(asLink=True))
##        else:
##            return text
##        return None
##
##    def save(self, text, page, comment=None, minorEdit=True,
##             botflag=True):
##        # only save if something was changed
##        if text == page.get():
##            pywikibot.output(u'No changes were needed on %s'
##                             % page.title(asLink=True))
##            return False
##
##        # Show the title of the page we're working on.
##        # Highlight the title in purple.
##        pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
##                         % page.title())
##        # show what was changed
##        pywikibot.showDiff(page.get(), text)
##        pywikibot.output(u'Comment: %s' %comment)
##
##        if self.getOption('dry'):
##            return False
##
##        choice = 'a'
##        if not self.getOption('always'):
##            choice = pywikibot.inputChoice(
##                u'Do you want to accept these changes?',
##                ['Yes', 'No', 'All'], ['y', 'N', 'a'], 'N')
##            if choice == 'a':
##                # Remember the choice
##                self.options['always'] = True
##
##        if choice != 'n':
##            try:
##                # Save the page
##                page.put(text, comment=comment or self.comment,
##                         minorEdit=minorEdit, botflag=botflag)
##            except pywikibot.LockedPage:
##                pywikibot.output(u"Page %s is locked; skipping."
##                                 % page.title(asLink=True))
##            except pywikibot.EditConflict:
##                pywikibot.output(
##                    u'Skipping %s because of edit conflict'
##                    % (page.title()))
##            except pywikibot.SpamfilterError, error:
##                pywikibot.output(
##u'Cannot change %s because of spam blacklist entry %s'
##                    % (page.title(), error.url))
##            else:
##                return True
##        return False

    def featuredArticles(self, site, task, cache):
        wikidata = False
        code = site.lang
        articles = []
        if task == 'good':
            info = good_name
            code = 'wikidata'
        elif task == 'former':
            info = former_name
        elif task == 'list':
            info = lists_name
        else:
            info = featured_name
            code = 'wikidata'
        try:
            method = info[code][0]
        except KeyError:
            pywikibot.error(
                u'language %s doesn\'t has %s category source.'
                % (code, task))
            return
        name = info[code][1]
        # hide #-sorted items on en-wiki
        try:
            hide = info[code][2]
        except IndexError:
            hide = None
        for p in method(site, name, hide):
            if p.namespace() == 0:  # Article
                articles.append(p)
            # Article talk (like in English)
            elif p.namespace() == 1 and site.lang != 'el':
                articles.append(pywikibot.Page(p.site,
                                p.title(withNamespace=False)))
        pywikibot.output(
            '\03{lightred}** %s has %i %s articles\03{default}'
            % (site, len(articles), task))
        for p in articles:
            if p.title() < afterpage:
                continue

            if u"/" in p.title() and p.namespace() != 0:
                pywikibot.output(u"%s is a subpage" % p.title())
                continue

            if p.title() in cache:
                pywikibot.output(u"(cached) %s -> %s" % (p.title(),
                                                         cache[p.title()]))
                continue
            yield copy(p)


    def findTranslated(self, page, oursite=None, quiet=False):
        if not oursite:
            oursite = self.site
        if page.isRedirectPage():
            page = page.getRedirectTarget()

        ourpage = None
        for link in page.iterlanglinks():
            if link.site == oursite:
                ourpage = pywikibot.Page(link)
                break

        if not ourpage:
            if not quiet:
                pywikibot.output(u"%s -> no corresponding page in %s"
                                 % (page.title(), oursite))
            return

        if ourpage.section():
            pywikibot.output(u"%s -> our page is a section link: %s"
                             % (page.title(), ourpage.title()))
            return

        if not ourpage.exists():
            pywikibot.output(u"%s -> our page doesn't exist: %s"
                             % (page.title(), ourpage.title()))
            return

        if ourpage.isRedirectPage():
            ourpage = ourpage.getRedirectTarget()
        pywikibot.output(u"%s -> corresponding page is %s"
                         % (page.title(), ourpage.title()))
        if ourpage.namespace() != 0:
            pywikibot.output(u"%s -> not in the main namespace, skipping"
                             % page.title())
            return

        if ourpage.isRedirectPage():
            pywikibot.output(u"%s -> double redirect, skipping" % page.title())
            return

        if not ourpage.exists():
            pywikibot.output(u"%s -> page doesn't exist, skipping"
                             % ourpage.title())
            return

        backpage = None
        for link in ourpage.iterlanglinks():
            if link.site == page.site:
                backpage = pywikibot.Page(link)
                break

        if not backpage:
            pywikibot.output(u"%s -> no back interwiki ref" % page.title())
            return

        if backpage == page:
            # everything is ok
            return ourpage
        if backpage.isRedirectPage():
            backpage = backpage.getRedirectTarget()
        if backpage == page:
            # everything is ok
            return ourpage
        pywikibot.output(u"%s -> back interwiki ref target is %s"
                         % (page.title(), backpage.title()))


    def getTemplateList(self, lang, task):
        if task == 'good':
            try:
                templates = template_good[lang]
                templates += template_good['_default']
            except KeyError:
                templates = template_good['_default']
        elif task == 'list':
            try:
                templates = template_lists[lang]
                templates += template_lists['_default']
            except KeyError:
                templates = template_lists['_default']
        else:  # task in ['former', 'featured']
            try:
                templates = template[lang]
                templates += template['_default']
            except KeyError:
                templates = template['_default']
        return templates


    def featuredWithInterwiki(self, fromsite, template_on_top, task,
                              quiet, dry=False):
        tosite = self.site
        if not fromsite.lang in self.cache:
            self.cache[fromsite.lang] = {}
        if not tosite.lang in self.cache[fromsite.lang]:
            self.cache[fromsite.lang][tosite.lang] = {}
        cc = self.cache[fromsite.lang][tosite.lang]
        if self.getOption('nocache') is True or \
           fromsite.code in self.getOption('nocache'):
            cc = {}
        templatelist = self.getTemplateList(tosite.code, task)
        findtemplate = '(' + '|'.join(templatelist) + ')'
        re_Link_FA = re.compile(ur"\{\{%s\|%s\}\}"
                                % (findtemplate.replace(u' ', u'[ _]'),
                                   fromsite.code), re.IGNORECASE)
        gen = self.featuredArticles(fromsite, task, cc)
        gen = PreloadingGenerator(gen)
        pairs = []
        for a in gen:
            if a.isRedirectPage():
                a = a.getRedirectTarget()

            if not a.exists():
                pywikibot.output(u"source page doesn't exist: %s"
                                 % a.title())
                continue

            atrans = self.findTranslated(a, tosite, quiet)
            if not atrans:
                continue
            
            if task != 'former':
                text = atrans.get()
                m = re_Link_FA.search(text)
                if m:
                    pywikibot.output(u"(already done)")
                else:
                    # insert just before interwiki
                    if (not interactive or
                        pywikibot.input(
                            u'Connecting %s -> %s. Proceed? [Y/N]'
                            % (a.title(), atrans.title())) in ['Y', 'y']):
                        site = pywikibot.getSite()
                        comment = pywikibot.setAction(
                            i18n.twtranslate(site, 'featured-' + task,
                                             {'page': unicode(a)}))
                        
                        # Moving {{Link FA|xx}} to top of interwikis
                        if template_on_top:
                            # Getting the interwiki
                            iw = pywikibot.getLanguageLinks(text, site)
                            # Removing the interwiki
                            text = pywikibot.removeLanguageLinks(text, site)
                            text += u"\r\n{{%s|%s}}\r\n" % (templatelist[0],
                                                            fromsite.code)
                            # Adding the interwiki
                            text = pywikibot.replaceLanguageLinks(text,
                                                                  iw, site)

                        # Placing {{Link FA|xx}} right next to
                        # corresponding interwiki
                        else:
                            text = (text[:m.end()] +
                                    (u" {{%s|%s}}" % (templatelist[0],
                                                      fromsite.code)) +
                                    text[m.end():])
                        if not dry:
                            try:
                                atrans.put(text, comment)
                            except pywikibot.LockedPage:
                                pywikibot.output(u'Page %s is locked!'
                                                 % atrans.title())
                            except pywikibot.PageNotSaved, e:
                                pywikibot.output(u"Page not saved")
                cc[a.title()] = atrans.title()
            else:
                text = atrans.get()
                m = re_Link_FA.search(text)
                if m:
                    # insert just before interwiki
                    if (not interactive or
                        pywikibot.input(
                            u'Connecting %s -> %s. Proceed? [Y/N]'
                            % (a.title(), atrans.title())) in ['Y', 'y']):
                        site = pywikibot.getSite()
                        comment = pywikibot.setAction(
                            i18n.twtranslate(site, 'featured-former',
                                             {'page': unicode(a)}))
                        text = re.sub(re_Link_FA, '', text)
                        if not dry:
                            try:
                                atrans.put(text, comment)
                            except pywikibot.LockedPage:
                                pywikibot.output(u'Page %s is locked!'
                                                 % atrans.title())
                            except pywikibot.PageNotSaved, e:
                                pywikibot.output(u"Page not saved")
                else:
                    pywikibot.output(u"(already done)")
                cc[a.title()] = atrans.title()


def main(*args):
    global interactive, afterpage
    interactive = 0
    afterpage = u"!"

    featuredcount = False
    fromlang = []
    processType = 'featured'
    part = False
    options = {}
    for arg in pywikibot.handleArgs():
        if arg == '-interactive':
            interactive = 1
        elif arg.startswith('-fromlang:'):
            fromlang = arg[10:].split(",")
            part = True
        elif arg.startswith('-after:'):
            afterpage = arg[7:]
        elif arg.startswith('-nocache:'):
            options[arg[1:8]] = arg[9:].split(",")
        else:
            options[arg[1:].lower()] = True

    if part:
        try:
            # BUG: range with zh-min-nan (3 "-")
            if len(fromlang) == 1 and fromlang[0].index("-") >= 0:
                start, end = fromlang[0].split("--", 1)
                if not start:
                    start = ""
                if not end:
                    end = "zzzzzzz"
                if processType == 'good':
                    fromlang = [lang for lang in good_name.keys()
                                if lang >= start and lang <= end]
                elif processType == 'list':
                    fromlang = [lang for lang in lists_name.keys()
                                if lang >= start and lang <= end]
                elif processType == 'former':
                    fromlang = [lang for lang in former_name.keys()
                                if lang >= start and lang <= end]
                else:
                    fromlang = [lang for lang in featured_name.keys()
                                if lang >= start and lang <= end]
        except:
            pass

##        for ll in fromlang:
##            fromsite = pywikibot.getSite(ll)
##            if featuredcount:
##                try:
##                    featuredArticles(fromsite, processType).next()
##                except StopIteration:
##                    continue
##            elif not hasTemplate:
##                pywikibot.output(
##                    u'\nNOTE: %s arcticles are not implemented at %s-wiki.'
##                    % (processType, pywikibot.getSite().lang))
##                pywikibot.output('Quitting program...')
##                break
##            elif fromsite != pywikibot.getSite():
##                featuredWithInterwiki(fromsite, pywikibot.getSite(),
##                                      template_on_top, processType, quiet,
##                                      config.simulate)
    if options:
        bot = FeaturedBot(**options)
        bot.run()
    else:
        pywikibot.showHelp()


if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
