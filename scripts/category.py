#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Scripts to manage categories.

Syntax: python category.py action [-option]

where action can be one of these:
 * add         - mass-add a category to a list of pages
 * remove      - remove category tag from all pages in a category
 * move        - move all pages in a category to another category
 * tidy        - tidy up a category by moving its articles into subcategories
 * tree        - show a tree of subcategories of a given category
 * listify     - make a list of all of the articles that are in a category

and option can be one of these:
 * -person     - sort persons by their last name (for action 'add')
 * -rebuild    - reset the database
 * -from:      - The category to move from (for the move option)
                 Also, the category to remove from in the remove option
                 Also, the category to make a list of in the listify option
 * -to:        - The category to move to (for the move option)
               - Also, the name of the list to make in the listify option
         NOTE: If the category names have spaces in them you may need to use
         a special syntax in your shell so that the names aren't treated as
         separate parameters.  For instance, in BASH, use single quotes,
         e.g. -from:'Polar bears'
 * -batch      - Don't prompt to delete emptied categories (do it
                 automatically).
 * -summary:   - Pick a custom edit summary for the bot.
 * -inplace    - Use this flag to change categories in place rather than
                 rearranging them.
 * -nodelsum   - An option for remove, this specifies not to use the custom
                 edit summary as the deletion reason.  Instead, it uses the
                 default deletion reason for the language, which is "Category
                 was disbanded" in English.
 * -overwrite  - An option for listify, this overwrites the current page with
                 the list even if something is already there.
 * -showimages - An option for listify, this displays images rather than
                 linking them in the list.
 * -talkpages  - An option for listify, this outputs the links to talk pages
                 of the pages to be listified in addition to the pages
                 themselves.
 * -recurse    - Recurse through all subcategories of categories.
 * -match      - Only work on pages whose titles match the given regex (for
                 move and remove actions).

If action is "add", the following options are supported:

&params;

For the actions tidy and tree, the bot will store the category structure
locally in category.dump. This saves time and server load, but if it uses
these data later, they may be outdated; use the -rebuild parameter in this
case.

For example, to create a new category from a list of persons, type:

  python category.py add -person

and follow the on-screen instructions.

Or to do it all from the command-line, use the following syntax:

  python category.py move -from:US -to:'United States'

This will move all pages in the category US to the category United States.

"""

#
# (C) Rob W.W. Hooft, 2004
# (C) Daniel Herding, 2004
# (C) Anreas J Schwab, 2007
# (C) Pywikipedia team, 2008-2009
#
__version__ = '$Id$'
#
# Distributed under the terms of the MIT license.
#

import os, re, pickle, bz2
import pywikibot
from pywikibot import catlib, config, pagegenerators
import sys

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}
# Summary messages
msg_add={
    'ar':u'روبوت: إضافة [[تصنيف:%s]]',
    'bat-smg':u'Robots: Pridedama [[Kateguorėjė:%s]]',
    'be-x-old':u'Робат: дадаваньне [[Катэгорыя:%s]]',
    'ca':u'Robot: Afegint [[Categoria:%s]]',
    'cs':u'Robot přidal [[Kategorie:%s]]',
    'da':u'Robot: Tilføjer [[Kategori:%s]]',
    'de':u'Bot: Ergänze [[Kategorie:%s]]',
    'en':u'Robot: Adding [[Category:%s]]',
    'es':u'Bot: Añadida [[Categoría:%s]]',
    'id':u'Bot: Menambahkan [[Kategori:%s]]',
    'fa':u'ربات: افزودن [[رده:%s]]',
    'fi':u'Botti lisäsi luokkaan [[Luokka:%s]]',
    'fr':u'Robot : ajoute [[Catégorie:%s]]',
    'he':u'בוט: מוסיף [[קטגוריה:%s]]',
    'ia':u'Robot: Addition de [[Categoria:%s]]',
    'is':u'Vélmenni: Bæti við [[Flokkur:%s]]',
    'it':u'Bot: Aggiungo [[Categoria:%s]]',
    'ja':u'ロボットによる: カテゴリ追加 [[Category:%s]]',
    'kk':u'Бот: [[Санат:%s]] үстеді',
    'ko': u'로봇: [[분류:%s]] 추가',
    'ksh':u'Bot: [[Saachjropp:%s]] erinjedonn',
    'lb': u'Bot: Derbäi setzen [[Kategorie:%s]]',
    'lt':u'robotas: Pridedama [[Kategorija:%s]]',
    'nds':u'Kat-Bot: [[Kategorie:%s]] rin',
    'nds-nl':u'bot: [[kattegerie:%s]] derbie edaon',
    'nl':u'Bot: [[categorie:%s]] toegevoegd',
    'no':u'Robot: Legger til [[Kategori:%s]]',
    'nn':u'robot: la til [[Kategori:%s]]',
    'pl':u'Robot dodaje [[Kategoria:%s]]',
    'pt':u'Bot: Adicionando [[Categoria:%s]]',
    'ru':u'Робот: добавление [[Категория:%s]]',
    'sk':u'Robot pridal [[Kategória:%s]]',
    'sr':u'Бот: Додаје [[Категорија:%s]]',
    'sv':u'Robot: Lägger till [[Kategori:%s]]',
    'szl':u'Bot dodowo: [[Kategoria:%s]]',
    'uk':u'Робот: додано [[Категорія:%s]]',
    'zh':u'機器人:新增目錄 [[Category:%s]]',
    }

msg_change={
    'ar':u'روبوت: تغيير %(oldcat)s',
    'be-x-old':u'Робат: зьмена %(oldcat)s',
    'ca':u'Robot: Canviant %(oldcat)s',
    'cs':u'Robot změnil [[%(oldcat)s]]→[[%(newcat)s]]',
    'da':u'Robot: Ændrer %(oldcat)s',
    'de':u'Bot: Ändere %(oldcat)s',
    'en':u'Robot: Changing %(oldcat)s',
    'es':u'Bot: Cambiada %(oldcat)s',
    'id':u'Bot: Mengganti %(oldcat)s',
    'fa':u'ربات:تغییر %(oldcat)s',
    'fi':u'Botti muutti luokan %(oldcat)s',
    'fr':u'Robot : modifie [[%(oldcat)s]]',
    'he':u'בוט: משנה %(oldcat)s',
    'ia':u'Robot: Modification de %(oldcat)s',
    'is':u'Vélmenni: Breyti flokknum [[%(oldcat)s]]',
    'it':u'Bot: Modifico %(oldcat)s',
    'lt':u'robotas: Keičiama %(oldcat)s',
    'ja':u'ロボットによる: カテゴリ変更 [[%(oldcat)s]]→[[%(newcat)s]]',
    'kk':u'Бот: %(oldcat)s дегенді түзетті',
    'ko': u'로봇: %(oldcat)s 수정',
    'ksh':u'Bot: %(oldcat)s ußjewääßelt',
    'nds':u'Kat-Bot: %(oldcat)s utwesselt',
    'nds-nl':u'bot: wieziging %(oldcat)s',
    'nl':u'Bot: wijziging %(oldcat)s',
    'no':u'Robot: Endrer %(oldcat)s',
    'nn':u'robot: endra %(oldcat)s',
    'pdc':u'Waddefresser: Abdeeling von %(oldcat)s nooch %(newcat)s geennert',
    'pt':u'Bot: Modificando [[%(oldcat)s]]',
    'pl':u'Robot przenosi %(oldcat)s',
    'ru':u'Робот: изменение %(oldcat)s',
    'sk':u'Robot zmenil [[%(oldcat)s]]→[[%(newcat)s]]',
    'sr':u'Бот: Измена категорије %(oldcat)s',
    'sv':u'Robot: Ändrar %(oldcat)s',
    'uk':u'Робот: змінено [[Категорія:%(oldcat)s]]',
    'zh':u'機器人:變更目錄 [[%(oldcat)s]]→[[%(newcat)s]]',
    }

msg_created_for_renaming = {
    'ar':u'روبوت: نقل من %s. المؤلفون: %s',
    'de':u'Bot: Verschoben von %s. Autoren: %s',
    'en':u'Robot: Moved from %s. Authors: %s',
    'fi':u'Botti siirsi luokan %s. Muokkaajat: %s',
    'fr':u'Robot : déplacé depuis %s. Auteurs: %s',
    'he':u'בוט: הועבר מהשם %s. כותבים: %s',
    'ia':u'Robot: Transferite de %s. Autores: %s',
    'id':u'Bot: Memindahkan dari %s. Kontributor: %s',
    'it':u'Bot: Voce spostata da %s. Autori: %s',
    'ja': u'ロボットによる: %s から移動しました。原作者は %s',
    'ksh':u'Bot: hääjeholldt von %s. Schriiver: %s',
    'nds':u'Kat-Bot: herschaven von %s. Schriever: %s',
    'nl':u'Bot: hernoemd van %s. Auteurs: %s',
    'pl':u'Robot przenosi z %s. Autorzy: %s',
    'pt':u'Bot: Movido de %s. Autor: %s',
    'zh':u'機器人: 已從 %s 移動。原作者是 %s',
    }

deletion_reason_move = {
    'ar':u'روبوت: التصنيف نقل إلى [[:تصنيف:%s|%s]]',
    'bat-smg':u'Robots: Kateguorėjė bova parvadėnta i [[:Kateguorėjė:%s|%s]]',
    'be-x-old':u'Робат: катэгорыя перайменаваная ў [[:Катэгорыя:%s|%s]]',
    'ca':u'Robot: La categoria s\'ha mogut a [[:Categoria:%s|%s]]',
    'cs':u'Kategorie přesunuta na [[:Kategorie:%s|%s]]',
    'da':u'Robot: Kategori flyttet til [[:Category:%s|%s]]',
    'de':u'Bot: Kategorie wurde nach [[:Kategorie:%s|%s]] verschoben',
    'en':u'Robot: Category was moved to [[:Category:%s|%s]]',
    'es':u'Robot: La categoría ha sido movida a [[:Category:%s|%s]]',
    'fa':u'ربات:رده به رده  [[:رده:%s|%s]] منتقل شده‌است',
    'fi':u'Botti siirsi luokan nimelle [[:Luokka:%s|%s]]',
    'fr':u'Robot : catégorie déplacée sur [[:Category:%s|%s]]',
    'he':u'בוט: הקטגוריה הועברה לשם [[:קטגוריה:%s|%s]]',
    'ia':u'Robot: Categoria transferite a [[:Category:%s|%s]]',
    'id':u'Bot: Kategori dipindahkan ke [[:Category:%s|%s]]',
    'it':u'Bot: La categoria è stata sostituita da [[:Categoria:%s|%s]]',
    'ja':u'ロボットによる: カテゴリ [[:Category:%s]]へ移動',
    'kk':u'Бот: Санат [[:Санат:%s|%s]] дегенге жылжытылды',
    'ko': u'로봇: 분류가 [[:분류:%s|%s]]로 옮겨짐',
    'ksh':u'Bot: Saachjropp noh [[:Category:%s|%s]] jeschovve',
    'lb': u'Bot: Kategorie gouf gréckelt: Nei [[:Kategorie:%s|%s]]',
    'lt':u'robotas: Kategorija pervadinta į [[:Category:%s|%s]]',
    'nds':u'Kat-Bot: Kategorie na [[:Category:%s|%s]] schaven',
    'nds-nl':u'Bot: kattegerie is herneumd naor [[:Kattegerie:%s|%s]]',
    'nl':u'Bot: Categorie is hernoemd naar [[:Category:%s|%s]]',
    'no':u'Robot: Kategorien ble flyttet til [[:Category:%s|%s]]',
    'nn':u'robot: kategorien blei flytta til [[:Kategori:%s|%s]]',
    'pdc':u'Waddefresser: Abdeeling iss gezoge warre nooch [[:Kategorie:%s|%s]].',
    'pt':u'Bot: Categoria [[:Category:%s|%s]] foi movida',
    'pl':u'Robot przenosi kategorię do [[:Category:%s|%s]]',
    'ru':u'Робот: категория переименована в [[:Категория:%s|%s]]',
    'sk':u'Kategória bola presunutá na [[:Kategória:%s|%s]]',
    'sr':u'Бот: Категорија премештена у [[:Category:%s|%s]]',
    'sv':u'Robot: Kategori flyttades till [[:Category:%s|%s]]',
    'uk':u'Робот: категорію перейменовано на [[Категорія:%s|%s]]',
    'zh':u'機器人:移動目錄至 [[:Category:%s|%s]]',
    }

cfd_templates = {
    'wikipedia' : {
        'en':[u'cfd', u'cfr', u'cfru', u'cfr-speedy', u'cfm', u'cfdu'],
        'fi':[u'roskaa', u'poistettava', u'korjattava/nimi', u'yhdistettäväLuokka'],
        'he':[u'הצבעת מחיקה', u'למחוק'],
        'nl':[u'categorieweg', u'catweg', u'wegcat', u'weg2']
    },
    'commons' : {
        'commons':[u'cfd', u'move']
    }
}

class CategoryDatabase:
    '''
    This is a temporary knowledge base saving for each category the contained
    subcategories and articles, so that category pages do not need to
    be loaded over and over again
    '''
    def __init__(self, rebuild = False, filename = 'category.dump.bz2'):
        if rebuild:
            self.rebuild()
        else:
            try:
                if not os.path.isabs(filename):
                    filename = config.datafilepath(filename)
                f = bz2.BZ2File(filename, 'r')
                pywikibot.output(u'Reading dump from %s'
                                 % config.shortpath(filename))
                databases = pickle.load(f)
                f.close()
                # keys are categories, values are 2-tuples with lists as entries.
                self.catContentDB = databases['catContentDB']
                # like the above, but for supercategories
                self.superclassDB = databases['superclassDB']
                del databases
            except:
                # If something goes wrong, just rebuild the database
                self.rebuild()

    def rebuild(self):
        self.catContentDB={}
        self.superclassDB={}

    def getSubcats(self, supercat):
        '''
        For a given supercategory, return a list of Categorys for all its
        subcategories.
        Saves this list in a temporary database so that it won't be loaded from the
        server next time it's required.
        '''
        # if we already know which subcategories exist here
        if supercat in self.catContentDB:
            return self.catContentDB[supercat][0]
        else:
            subcatset = set(supercat.subcategories())
            articleset = set(supercat.articles())
            # add to dictionary
            self.catContentDB[supercat] = (subcatset, articleset)
            return subcatset

    def getArticles(self, cat):
        '''
        For a given category, return a list of Pages for all its articles.
        Saves this list in a temporary database so that it won't be loaded from the
        server next time it's required.
        '''
        # if we already know which articles exist here
        if cat in self.catContentDB:
            return self.catContentDB[cat][1]
        else:
            subcatset = set(cat.subcategories())
            articleset = set(cat.articles())
            # add to dictionary
            self.catContentDB[cat] = (subcatset, articleset)
            return articleset

    def getSupercats(self, subcat):
        # if we already know which subcategories exist here
        if subcat in self.superclassDB:
            return self.superclassDB[subcat]
        else:
            supercatset = set(subcat.categories())
            # add to dictionary
            self.superclassDB[subcat] = supercatset
            return supercatset

    def dump(self, filename = 'category.dump.bz2'):
        '''
        Saves the contents of the dictionaries superclassDB and catContentDB to disk.
        '''
        if not os.path.isabs(filename):
            filename = config.datafilepath(filename)
        pywikibot.output(u'Dumping to %s, please wait...'
                         % config.shortpath(filename))
        f = bz2.BZ2File(filename, 'w')
        databases = {
            'catContentDB': self.catContentDB,
            'superclassDB': self.superclassDB
        }
        # store dump to disk in binary format
        try:
            pickle.dump(databases, f, protocol=pickle.HIGHEST_PROTOCOL)
        except pickle.PicklingError:
            pass
        f.close()

def sorted_by_last_name(catlink, pagelink):
        '''Return a Category with key that sorts persons by their last names.

        Parameters: catlink - The Category to be linked
                    pagelink - the Page to be placed in the category

        Trailing words in brackets will be removed. Example: If
        category_name is 'Author' and pl is a Page to [[Alexandre Dumas
        (senior)]], this function will return this Category:
        [[Category:Author|Dumas, Alexandre]]

        '''
        page_name = pagelink.title()
        site = pagelink.site
        # regular expression that matches a name followed by a space and
        # disambiguation brackets. Group 1 is the name without the rest.
        bracketsR = re.compile('(.*) \(.+?\)')
        match_object = bracketsR.match(page_name)
        if match_object:
            page_name = match_object.group(1)
        split_string = page_name.split(' ')
        if len(split_string) > 1:
            # pull last part of the name to the beginning, and append the
            # rest after a comma; e.g., "John von Neumann" becomes
            # "Neumann, John von"
            sorted_key = split_string[-1] + ', ' + ' '.join(split_string[:-1])
            # give explicit sort key
            return pywikibot.Page(site, catlink.title() + '|' + sorted_key)
        else:
            return pywikibot.Page(site, catlink.title())

def add_category(sort_by_last_name = False):
    '''A robot to mass-add a category to a list of pages.'''
    site = pywikibot.getSite()
    if gen:
        newcatTitle = pywikibot.input(
            u'Category to add (do not give namespace):')
        if not site.nocapitalize:
            newcatTitle = newcatTitle[:1].capitalize() + newcatTitle[1:]

        # set edit summary message
        editSummary = pywikibot.translate(site, msg_add) % newcatTitle

        cat_namespace = site.category_namespaces()[0]

        answer = ''
        for page in gen:
            if answer != 'a':
                answer = ''

            while answer not in ('y','n','a'):
                answer = pywikibot.input(u'%s [y/n/a(ll)]:' % (page.title(asLink=True)))
                if answer == 'a':
                    confirm = ''
                    while confirm not in ('y','n'):
                        confirm = pywikibot.input(u"""\
This should be used if and only if you are sure that your links are correct!
Are you sure? [y/n]:""")
                    if confirm == 'n':
                        answer = ''

            if answer == 'y' or answer == 'a':
                try:
                    text = page.get()
                except pywikibot.NoPage:
                    pywikibot.output(u"%s doesn't exist yet. Ignoring."
                                     % (page.title()))
                    pass
                except pywikibot.IsRedirectPage:
                    pywikibot.output(
                        u"WARNING: %s is redirect to. Ignoring." % page)
                else:
                    cats = page.categories()
                    # Show the title of the page we're working on.
                    # Highlight the title in purple.
                    pywikibot.output(
                        u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                        % page.title())
                    pywikibot.output(u"Current categories:")
                    for cat in cats:
                        pywikibot.output(u"* %s" % cat.title())
                    catpl = pywikibot.Page(site,
                                           cat_namespace + ':' + newcatTitle)
                    if sort_by_last_name:
                        catpl = sorted_by_last_name(catpl, page)
                    if catpl in cats:
                        pywikibot.output(u"%s is already in %s."
                                         % (page.title(), catpl.title()))
                    else:
                        pywikibot.output(u'Adding %s' % catpl.title(asLink=True))
                        cats.append(catpl)
                        text = page.get()
                        text = pywikibot.replaceCategoryLinks(text, cats)
                        try:
                            page.put(text, comment = editSummary)
                        except pywikibot.EditConflict:
                            pywikibot.output(
                                u'Skipping %s because of edit conflict'
                                % (page.title()))

class CategoryMoveRobot:
    """Robot to move pages from one category to another."""
    def __init__(self, oldCatTitle, newCatTitle, batchMode=False,
                 editSummary='', inPlace=False, moveCatPage=True,
                 deleteEmptySourceCat=True, titleRegex=None):
        site = pywikibot.getSite()
        self.editSummary = editSummary
        self.oldCat = catlib.Category(pywikibot.Link('Category:' + oldCatTitle))
        self.newCatTitle = newCatTitle
        self.inPlace = inPlace
        self.moveCatPage = moveCatPage
        self.batchMode = batchMode
        self.deleteEmptySourceCat = deleteEmptySourceCat
        self.titleRegex = titleRegex
        # set edit summary message
        if not self.editSummary:
            self.editSummary = pywikibot.translate(site, msg_change) \
                               % {'oldcat':self.oldCat.title(),
                                  'newcat':newCat.title()}

    def run(self):
        site = pywikibot.getSite()
        newCat = catlib.Category(pywikibot.Link('Category:' + self.newCatTitle))

        # Copy the category contents to the new category page
        copied = False
        oldMovedTalk = None
        if self.oldCat.exists() and self.moveCatPage:
            copied = self.oldCat.copyAndKeep(
                            self.newCatTitle,
                            pywikibot.translate(site, cfd_templates),
                            pywikibot.translate(site, msg_created_for_renaming)
                     )
            # Also move the talk page
            if copied:
                reason = pywikibot.translate(site, deletion_reason_move) \
                         % (self.newCatTitle, self.newCatTitle)
                oldTalk = self.oldCat.toggleTalkPage()
                if oldTalk.exists():
                    newTalkTitle = newCat.toggleTalkPage().title()
                    try:
                        talkMoved = oldTalk.move(newTalkTitle, reason)
                    except (pywikibot.NoPage, pywikibot.PageNotSaved), e:
                        #in order :
                        #Source talk does not exist, or
                        #Target talk already exists
                        pywikibot.output(e.message)
                    else:
                        if talkMoved:
                            oldMovedTalk = oldTalk

        # Move articles
        gen = pagegenerators.CategorizedPageGenerator(self.oldCat,
                                                      recurse=False)
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        for article in preloadingGen:
            if not self.titleRegex or re.search(self.titleRegex,
                                                article.title()):
                catlib.change_category(article, self.oldCat, newCat,
                                       comment=self.editSummary,
                                       inPlace=self.inPlace)

        # Move subcategories
        gen = pagegenerators.SubCategoriesPageGenerator(self.oldCat,
                                                        recurse=False)
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        for subcategory in preloadingGen:
            if not self.titleRegex or re.search(self.titleRegex,
                                                subcategory.title()):
                catlib.change_category(subcategory, self.oldCat, newCat,
                                       comment=self.editSummary,
                                       inPlace=self.inPlace)

        # Delete the old category and its moved talk page
        if copied and self.deleteEmptySourceCat == True:
            if self.oldCat.isEmptyCategory():
                reason = pywikibot.translate(site, deletion_reason_move) \
                         % (self.newCatTitle, self.newCatTitle)
                confirm = not self.batchMode
                self.oldCat.delete(reason, confirm, mark = True)
                if oldMovedTalk is not None:
                    oldMovedTalk.delete(reason, confirm, mark = True)
            else:
                pywikibot.output('Couldn\'t delete %s - not empty.'
                                 % self.oldCat.title())


class CategoryListifyRobot:
    '''
    Creates a list containing all of the members in a category.
    '''
    listify_msg={
        'ar':u'روبوت: عرض من %s (%d مدخلة)',
        'ca':u'Robot: Llistant de %s (%d entrades)',
        'cs':u'Robot: vytvoření soupisu obsahu kategorie %s (%d položek)',
        'en':u'Bot: Listifying from %s (%d entries)',
        'fa':u'ربات:فهرست کردن اعضای رده %s(%d عضو)',
        'fi':u'Botti listasi luokan %s (%d jäsentä)',
        'he':u'בוט: יוצר רשימה מהקטגוריה %s (%d דפים)',
        'kk':u'Бот: %s дегеннен (%d буын) тізімдеді',
        'nds-nl':u'Bot: lieste van %s (%d pagina\'s)',
        'nl':u'Bot: Lijst van %s (%d pagina\'s)',
        'pl':u'Robot: listuje kategorię %s (%d stron)',
        'sv':u'Robot: Skapar en lista från %s (%d)',
        'pt':u'Bot: Listando de %s (%d entradas)',
        'zh':u'機器人: 從%s提取列表(%d個項目)',
    }

    def __init__(self, catTitle, listTitle, editSummary, overwrite = False, showImages = False, subCats = False, talkPages = False, recurse = False):
        self.editSummary = editSummary
        self.overwrite = overwrite
        self.showImages = showImages
        self.site = pywikibot.getSite()
        self.cat = catlib.Category(pywikibot.Link('Category:' + catTitle))
        self.list = pywikibot.Page(self.site, listTitle)
        self.subCats = subCats
        self.talkPages = talkPages
        self.recurse = recurse

    def run(self):
        setOfArticles = set(self.cat.articles(recurse = self.recurse))
        if self.subCats:
            setOfArticles += set(self.cat.subcategories())
        if not self.editSummary:
            self.editSummary = pywikibot.translate(self.site, self.listify_msg) % (self.cat.title(), len(setOfArticles))

        listString = ""
        for article in setOfArticles:
            if (not article.isImage() or self.showImages) and not article.isCategory():
                if self.talkPages and not article.isTalkPage():
                    listString = listString + "*[[%s]] -- [[%s|talk]]\n" % (article.title(), article.toggleTalkPage().title())
                else:
                    listString = listString + "*[[%s]]\n" % article.title()
            else:
                if self.talkPages and not article.isTalkPage():
                    listString = listString + "*[[:%s]] -- [[%s|talk]]\n" % (article.title(), article.toggleTalkPage().title())
                else:
                    listString = listString + "*[[:%s]]\n" % article.title()
        if self.list.exists() and not self.overwrite:
            pywikibot.output(u'Page %s already exists, aborting.' % self.list.title())
        else:
            self.list.put(listString, comment=self.editSummary)

class CategoryRemoveRobot:
    '''
    Removes the category tag from all pages in a given category and from the
    category pages of all subcategories, without prompting.
    Does not remove category tags pointing at subcategories.
    '''
    deletion_reason_remove = {
        'ar':u'روبوت: التصنيف تم الاستغناء عنه',
        'be-x-old':u'Робат: катэгорыя расфармаваная',
        'ca':u'Robot: La categoria s\'ha eliminat',
        'cs':u'Robot: kategorie byla vyprázdněna',
        'da':u'Robot: Kategorien blev opløst',
        'de':u'Bot: Kategorie wurde aufgelöst',
        'en':u'Bot: Category was disbanded',
        'es':u'Robot: La categoría ha sido eliminada',
        'fa':u'ربات: رده خالی',
        'fi':u'Botti tyhjensi luokan',
        'he':u'בוט: הקטגוריה פורקה',
        'ia':u'Robot: Categoria esseva dissolvite',
        'kk':u'Бот: Санат тарқатылды',
        'ksh':u'Bot: de Saachjropp is nu opjelööß',
        'nds':u'Kat-Bot: Kategorie is nu oplööst',
        'nds-nl':u'Bot: kattegerie besteet neet meer',
        'nl':u'Bot: Categorie is opgeheven',
        'no':u'Robot: Kategorien ble oppløst',
        'nn':u'robot: kategorien blei løyst opp',
        'pl':u'Robot: Kategoria została usunięta',
        'pt':u'Bot: Categoria foi unida',
        'ru':u'Робот: категория расформирована',
        'sv':u'Robot: Kategorin upplöstes',
        'uk':u'Робот: категорія розформована',
        'zh':u'機器人:本目錄已解散',
    }

    msg_remove={
        'ar':u'روبوت: إزالة من %s',
        'bat-smg':u'Robots: Trėnama ėš %s',
        'be-x-old':u'Робат: выключэньне з [[%s]]',
        'ca':u'Robot: Eliminant de %s',
        'cs':u'Robot: odstranění kategorie %s',
        'da':u'Robot: Fjerner fra %s',
        'de':u'Bot: Entferne aus %s',
        'en':u'Bot: Removing from %s',
        'es':u'Bot: Eliminada de la %s',
        'fa':u'ربات:حذف از %s',
        'fi':u'Botti poisti luokasta %s',
        'fr':u'Robot : Retiré depuis %s',
        'he':u'בוט: מסיר את הדף מהקטגוריה %s',
        'ia':u'Robot: Eliminate de %s',
        'is':u'Vélmenni: Fjarlægi [[%s]]',
        'ja':u'ロボットによる:[[%s]]を除去',
        'kk':u'Бот: %s дегеннен аластатты',
        'ksh':u'Bot: uß de %s ußjedraare',
        'lb': u'Bot: Ewech huele vun %s',
        'nds':u'Kat-Bot: rut ut %s',
        'nds-nl':u'Bot: vort-ehaold uut %s',
        'nl':u'Bot: Verwijderd uit %s',
        'no':u'Robot: Fjerner ifra %s',
        'nn':u'robot: fjerna ifrå %s',
        'pl':u'Robot: Usuwa z kategorii %s',
        'pt':u'Bot: Removendo [[%s]]',
        'ru':u'Робот: исключение из %s',
        'sr':u'Бот: Уклањање из категорије [[%s]]',
        'sv':u'Robot: Tar bort från %s',
        'uk':u'Робот: видалення з %s',
        'zh':u'機器人:移除目錄 [[%s]]',
    }

    def __init__(self, catTitle, batchMode = False, editSummary = '', useSummaryForDeletion = True, titleRegex = None, inPlace = False):
        self.editSummary = editSummary
        self.site = pywikibot.getSite()
        self.cat = catlib.Category(pywikibot.Link('Category:' + catTitle))
        # get edit summary message
        self.useSummaryForDeletion = useSummaryForDeletion
        self.batchMode = batchMode
        self.titleRegex = titleRegex
        self.inPlace = inPlace
        if not self.editSummary:
            self.editSummary = pywikibot.translate(self.site, self.msg_remove) % self.cat.title()

    def run(self):
        articles = set(self.cat.articles())
        if len(articles) == 0:
            pywikibot.output(u'There are no articles in category %s' % self.cat.title())
        else:
            for article in articles:
                if not self.titleRegex or re.search(self.titleRegex,article.title()):
                    catlib.change_category(article, self.cat, None, comment = self.editSummary, inPlace = self.inPlace)
        # Also removes the category tag from subcategories' pages
        subcategories = set(self.cat.subcategories())
        if len(subcategories) == 0:
            pywikibot.output(u'There are no subcategories in category %s' % self.cat.title())
        else:
            for subcategory in subcategories:
                catlib.change_category(subcategory, self.cat, None, comment = self.editSummary, inPlace = self.inPlace)
        # Deletes the category page
        if self.cat.exists() and self.cat.isEmpty():
            if self.useSummaryForDeletion and self.editSummary:
                reason = self.editSummary
            else:
                reason = pywikibot.translate(self.site, self.deletion_reason_remove)
            talkPage = self.cat.toggleTalkPage()
            self.cat.delete(reason, not self.batchMode)
            if (talkPage.exists()):
                talkPage.delete(reason=reason, prompt=not self.batchMode)

class CategoryTidyRobot:
    """
    Script to help a human to tidy up a category by moving its articles into
    subcategories

    Specify the category name on the command line. The program will pick up the
    page, and look for all subcategories and supercategories, and show them with
    a number adjacent to them. It will then automatically loop over all pages
    in the category. It will ask you to type the number of the appropriate
    replacement, and perform the change robotically.

    If you don't want to move the article to a subcategory or supercategory, but to
    another category, you can use the 'j' (jump) command.

    Typing 's' will leave the complete page unchanged.

    Typing '?' will show you the first few bytes of the current page, helping
    you to find out what the article is about and in which other categories it
    currently is.

    Important:
     * this bot is written to work with the MonoBook skin, so make sure your bot
       account uses this skin
    """
    def __init__(self, catTitle, catDB):
        self.catTitle = catTitle
        self.catDB = catDB
        self.site = pywikibot.getSite()
        self.editSummary = pywikibot.translate(self.site, msg_change)\
                           % {'oldcat':cat.title(), 'newcat':u''}

    def move_to_category(self, article, original_cat, current_cat):
        '''
        Given an article which is in category original_cat, ask the user if
        it should be moved to one of original_cat's subcategories.
        Recursively run through subcategories' subcategories.
        NOTE: current_cat is only used for internal recursion. You should
        always use current_cat = original_cat.
        '''
        pywikibot.output(u'')
        # Show the title of the page where the link was found.
        # Highlight the title in purple.
        pywikibot.output(u'Treating page \03{lightpurple}%s\03{default}, currently in \03{lightpurple}%s\03{default}' % (article.title(), current_cat.title()))

        # Determine a reasonable amount of context to print
        try:
            full_text = article.get(get_redirect = True)
        except pywikibot.NoPage:
            pywikibot.output(u'Page %s not found.' % article.title())
            return
        try:
            contextLength = full_text.index('\n\n')
        except ValueError: # substring not found
            contextLength = 500
        if full_text.startswith(u'[['): # probably an image
            # Add extra paragraph.
            contextLength = full_text.find('\n\n', contextLength+2)
        if contextLength > 1000 or contextLength < 0:
            contextLength = 500
        print
        pywikibot.output(full_text[:contextLength])
        print

        subcatlist = self.catDB.getSubcats(current_cat)
        supercatlist = self.catDB.getSupercats(current_cat)
        print
        if len(subcatlist) == 0:
            print 'This category has no subcategories.'
            print
        if len(supercatlist) == 0:
            print 'This category has no supercategories.'
            print
        # show subcategories as possible choices (with numbers)
        for i in range(len(supercatlist)):
            # layout: we don't expect a cat to have more than 10 supercats
            pywikibot.output(u'u%d - Move up to %s' % (i, supercatlist[i].title()))
        for i in range(len(subcatlist)):
            # layout: we don't expect a cat to have more than 100 subcats
            pywikibot.output(u'%2d - Move down to %s' % (i, subcatlist[i].title()))
        print ' j - Jump to another category'
        print ' s - Skip this article'
        print ' r - Remove this category tag'
        print ' ? - Print first part of the page (longer and longer)'
        pywikibot.output(u'Enter - Save category as %s' % current_cat.title())

        flag = False
        while not flag:
            print ''
            choice = pywikibot.input(u'Choice:')
            if choice in ['s', 'S']:
                flag = True
            elif choice == '':
                pywikibot.output(u'Saving category as %s' % current_cat.title())
                if current_cat == original_cat:
                    print 'No changes necessary.'
                else:
                    catlib.change_category(article, original_cat, current_cat, comment = self.editSummary)
                flag = True
            elif choice in ['j', 'J']:
                newCatTitle = pywikibot.input(u'Please enter the category the article should be moved to:')
                newCat = catlib.Category(pywikibot.Link('Category:' + newCatTitle))
                # recurse into chosen category
                self.move_to_category(article, original_cat, newCat)
                flag = True
            elif choice in ['r', 'R']:
                # remove the category tag
                catlib.change_category(article, original_cat, None, comment = self.editSummary)
                flag = True
            elif choice == '?':
                contextLength += 500
                print
                pywikibot.output(full_text[:contextLength])
                print

                # if categories possibly weren't visible, show them additionally
                # (maybe this should always be shown?)
                if len(full_text) > contextLength:
                    print ''
                    print 'Original categories: '
                    for cat in article.categories():
                        pywikibot.output(u'* %s' % cat.title())
            elif choice[0] == 'u':
                try:
                    choice=int(choice[1:])
                except ValueError:
                    # user pressed an unknown command. Prompt him again.
                    continue
                self.move_to_category(article, original_cat, supercatlist[choice])
                flag = True
            else:
                try:
                    choice=int(choice)
                except ValueError:
                    # user pressed an unknown command. Prompt him again.
                    continue
                # recurse into subcategory
                self.move_to_category(article, original_cat, subcatlist[choice])
                flag = True

    def run(self):
        cat = catlib.Category(pywikibot.Link('Category:' + self.catTitle))

        articles = set(cat.articles())
        if len(articles) == 0:
            pywikibot.output(u'There are no articles in category ' + catTitle)
        else:
            preloadingGen = pagegenerators.PreloadingGenerator(iter(articles))
            for article in preloadingGen:
                pywikibot.output(u'\n===================================================================')
                self.move_to_category(article, cat, cat)

class CategoryTreeRobot:
    '''
    Robot to create tree overviews of the category structure.

    Parameters:
        * catTitle - The category which will be the tree's root.
        * catDB    - A CategoryDatabase object
        * maxDepth - The limit beyond which no subcategories will be listed.
                     This also guarantees that loops in the category structure
                     won't be a problem.
        * filename - The textfile where the tree should be saved; None to print
                     the tree to stdout.
    '''

    def __init__(self, catTitle, catDB, filename = None, maxDepth = 10):
        self.catTitle = catTitle
        self.catDB = catDB
        if filename and not os.path.isabs(filename):
            filename = config.datafilepath(filename)
        self.filename = filename
        # TODO: make maxDepth changeable with a parameter or config file entry
        self.maxDepth = maxDepth

    def treeview(self, cat, currentDepth = 0, parent = None):
        '''
        Returns a multi-line string which contains a tree view of all subcategories
        of cat, up to level maxDepth. Recursively calls itself.

        Parameters:
            * cat - the Category of the node we're currently opening
            * currentDepth - the current level in the tree (for recursion)
            * parent - the Category of the category we're coming from
        '''

        # Translations to say that the current category is in more categories than
        # the one we're coming from
        also_in_cats = {
            'ar': u'(أيضا في %s)',
            'be-x-old': u'(таксама ў %s)',
            'ca': u'(també a %s)',
            'cs': u'(také v %s)', 
            'da': u'(også i %s)',
            'de': u'(auch in %s)',
            'en': u'(also in %s)',
            'es': u'(también en %s)',
            'fa': u'(همچنین در %s)',
            'fi': u'(myös luokassa %s)',
            'fr': u'(également dans %s)',
            'he': u'(גם בקטגוריות %s)',
            'ia': u'(equalmente in %s)',
            'is': u'(einnig í %s)',
            'kk': u'(тағы да %s дегенде)',
            'nds-nl': u'(oek in %s)',
            'nl': u'(ook in %s)',
            'no': u'(også i %s)',
            'nn': u'(òg i %s)',
            'pl': u'(również w %s)',
            'pt': u'(também em %s)',
            'ru': u'(также в %s)',
            'sv': u'(också i %s)',
            'ср': u'(такође у %s)',
            'zh': u'(也在 %s)',
        }

        result = u'#' * currentDepth
        result += '[[:%s|%s]]' % (cat.title(), cat.title().split(':', 1)[1])
        result += ' (%d)' % len(self.catDB.getArticles(cat))
        # We will remove an element of this array, but will need the original array
        # later, so we create a shallow copy with [:]
        supercats = self.catDB.getSupercats(cat)[:]
        # Find out which other cats are supercats of the current cat
        try:
            supercats.remove(parent)
        except:
            pass
        if supercats != []:
            supercat_names = []
            for i in range(len(supercats)):
                # create a list of wiki links to the supercategories
                supercat_names.append('[[:%s|%s]]' % (supercats[i].title(), supercats[i].title().split(':', 1)[1]))
                # print this list, separated with commas, using translations given in also_in_cats
            result += ' ' + pywikibot.translate(pywikibot.getSite(), also_in_cats) % ', '.join(supercat_names)
        result += '\n'
        if currentDepth < self.maxDepth:
            for subcat in self.catDB.getSubcats(cat):
                # recurse into subdirectories
                result += self.treeview(subcat, currentDepth + 1, parent = cat)
        else:
            if self.catDB.getSubcats(cat) != []:
                # show that there are more categories beyond the depth limit
                result += '#' * (currentDepth + 1) + '[...]\n'
        return result

    def run(self):
        """
        Prints the multi-line string generated by treeview or saves it to a file.

        Parameters:
            * catTitle - the title of the category which will be the tree's root
            * maxDepth - the limit beyond which no subcategories will be listed
        """
        cat = catlib.Category(pywikibot.Link('Category:' + self.catTitle))
        tree = self.treeview(cat)
        if self.filename:
            pywikibot.output(u'Saving results in %s' % self.filename)
            import codecs
            f = codecs.open(self.filename, 'a', 'utf-8')
            f.write(tree)
            f.close()
        else:
            pywikibot.output(tree, toStdout = True)


def main(*args):
    global catDB

    fromGiven = False
    toGiven = False
    batchMode = False
    editSummary = ''
    inPlace = False
    overwrite = False
    showImages = False
    talkPages = False
    recurse = False
    titleRegex = None

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()
    # The generator gives the pages that should be worked upon.
    gen = None

    # If this is set to true then the custom edit summary given for removing
    # categories from articles will also be used as the deletion reason.
    useSummaryForDeletion = True
    catDB = CategoryDatabase()
    action = None
    sort_by_last_name = False
    restore = False
    for arg in pywikibot.handleArgs(*args):
        if genFactory.handleArg(arg):
            continue
        if arg == 'add':
            action = 'add'
        elif arg == 'remove':
            action = 'remove'
        elif arg == 'move':
            action = 'move'
        elif arg == 'tidy':
            action = 'tidy'
        elif arg == 'tree':
            action = 'tree'
        elif arg == 'listify':
            action = 'listify'
        elif arg == '-person':
            sort_by_last_name = True
        elif arg == '-rebuild':
            catDB.rebuild()
        elif arg.startswith('-from:'):
            oldCatTitle = arg[len('-from:'):].replace('_', ' ')
            fromGiven = True
        elif arg.startswith('-to:'):
            newCatTitle = arg[len('-to:'):].replace('_', ' ')
            toGiven = True
        elif arg == '-batch':
            batchMode = True
        elif arg == '-inplace':
            inPlace = True
        elif arg == '-delsum':
            # This parameter is kept for historical reasons,
            # as it was previously not the default option.
            pass
        elif arg == '-nodelsum':
            useSummaryForDeletion = False
        elif arg == '-overwrite':
            overwrite = True
        elif arg == '-showimages':
            showImages = True
        elif arg.startswith('-summary:'):
            editSummary = arg[len('-summary:'):]
        elif arg.startswith('-match'):
            if len(arg) == len('-match'):
                titleRegex = pywikibot.input(
                    u'Which regular expression should affected objects match?')
            else:
                titleRegex = arg[len('-match:'):]
        elif arg == '-talkpages':
            talkPages = True
        elif arg == '-recurse':
            recurse = True

    gen = genFactory.getCombinedGenerator()
    if action == 'add':
        if not gen:
            genFactory.handleArg('-links')
            gen = genFactory.getCombinedGenerator()
                  # default for backwards compatibility
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        gen = pagegenerators.PreloadingGenerator(gen)
        add_category(sort_by_last_name)
    elif action == 'remove':
        if (fromGiven == False):
            oldCatTitle = pywikibot.input(
    u'Please enter the name of the category that should be removed:')
        bot = CategoryRemoveRobot(oldCatTitle, batchMode, editSummary,
                                  useSummaryForDeletion, inPlace=inPlace)
        bot.run()
    elif action == 'move':
        if (fromGiven == False):
            oldCatTitle = pywikibot.input(
                u'Please enter the old name of the category:')
        if (toGiven == False):
            newCatTitle = pywikibot.input(
                u'Please enter the new name of the category:')
        bot = CategoryMoveRobot(oldCatTitle, newCatTitle, batchMode,
                                editSummary, inPlace, titleRegex=titleRegex)
        bot.run()
    elif action == 'tidy':
        catTitle = pywikibot.input(u'Which category do you want to tidy up?')
        bot = CategoryTidyRobot(catTitle, catDB)
        bot.run()
    elif action == 'tree':
        catTitle = pywikibot.input(
            u'For which category do you want to create a tree view?')
        filename = pywikibot.input(
          u'Please enter the name of the file where the tree should be saved,\n'
          u'or press enter to simply show the tree:')
        bot = CategoryTreeRobot(catTitle, catDB, filename)
        bot.run()
    elif action == 'listify':
        if (fromGiven == False):
            oldCatTitle = pywikibot.input(
                u'Please enter the name of the category to listify:')
        if (toGiven == False):
            newCatTitle = pywikibot.input(
                u'Please enter the name of the list to create:')
        bot = CategoryListifyRobot(oldCatTitle, newCatTitle, editSummary,
                                   overwrite, showImages, subCats=True,
                                   talkPages=talkPages, recurse=recurse)
        bot.run()
    else:
        pywikibot.showHelp('category')


if __name__ == "__main__":
    try:
        main()
    except pywikibot.Error:
        pywikibot.error("Fatal error:", exc_info=True)
    finally:
        catDB.dump()
        pywikibot.stopme()
