#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Scripts to manage categories.

Syntax: python category.py action [-option]

where action can be one of these:
 * add          - mass-add a category to a list of pages
 * remove       - remove category tag from all pages in a category
 * move         - move all pages in a category to another category
 * tidy         - tidy up a category by moving its articles into subcategories
 * tree         - show a tree of subcategories of a given category
 * listify      - make a list of all of the articles that are in a category

and option can be one of these:

Options for "add" action:
 * -person      - sort persons by their last name
 * -create      - If a page doesn't exist, do not skip it, create it instead
 * -redirect    - Follow redirects

If action is "add", the following options are supported:

&params;

Options for "listify" action:
 * -overwrite   - This overwrites the current page with the list even if
                  something is already there.
 * -showimages  - This displays images rather than linking them in the list.
 * -talkpages   - This outputs the links to talk pages of the pages to be
                  listified in addition to the pages themselves.

Options for "remove" action:
 * -nodelsum    - This specifies not to use the custom edit summary as the
                  deletion reason.  Instead, it uses the default deletion reason
                  for the language, which is "Category was disbanded" in
                  English.

Options for "move" action:
 * -hist        - Creates a nice wikitable on the talk page of target category
                  that contains detailed page history of the source category.
 * -nodelete    - Don't delete the old category after move

Options for several actions:
 * -rebuild     - reset the database
 * -from:       - The category to move from (for the move option)
                  Also, the category to remove from in the remove option
                  Also, the category to make a list of in the listify option
 * -to:         - The category to move to (for the move option)
                - Also, the name of the list to make in the listify option
         NOTE: If the category names have spaces in them you may need to use
         a special syntax in your shell so that the names aren't treated as
         separate parameters.  For instance, in BASH, use single quotes,
         e.g. -from:'Polar bears'
 * -batch       - Don't prompt to delete emptied categories (do it
                  automatically).
 * -summary:    - Pick a custom edit summary for the bot.
 * -inplace     - Use this flag to change categories in place rather than
                  rearranging them.
 * -recurse     - Recurse through all subcategories of categories.
 * -pagesonly   - While removing pages from a category, keep the subpage links
                  and do not remove them
 * -match       - Only work on pages whose titles match the given regex (for
                  move and remove actions).
 * -depth:      - The max depth limit beyond which no subcategories will be
                  listed.

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
# (C) Wikipedian, 2004-2008
# (C) leogregianin, 2004-2008
# (C) Cyde, 2006-2010
# (C) Anreas J Schwab, 2007
# (C) xqt, 2009-2014
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import os
import re
import pickle
import bz2
import pywikibot
from pywikibot import config, pagegenerators
from pywikibot import i18n
from pywikibot import deprecate_arg

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

cfd_templates = {
    'wikipedia': {
        'en': [u'cfd', u'cfr', u'cfru', u'cfr-speedy', u'cfm', u'cfdu'],
        'fi': [u'roskaa', u'poistettava', u'korjattava/nimi',
               u'yhdistettäväLuokka'],
        'he': [u'הצבעת מחיקה', u'למחוק'],
        'nl': [u'categorieweg', u'catweg', u'wegcat', u'weg2'],
        # For testing purposes
        'test': [u'delete']
    },
    'commons': {
        'commons': [u'cfd', u'move']
    }
}


class CategoryDatabase:

    """This is a temporary knowledge base saving for each category the contained
    subcategories and articles, so that category pages do not need to be loaded
    over and over again

    """

    def __init__(self, rebuild=False, filename='category.dump.bz2'):
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
                # keys are categories, values are 2-tuples with lists as
                # entries.
                self.catContentDB = databases['catContentDB']
                # like the above, but for supercategories
                self.superclassDB = databases['superclassDB']
                del databases
            except:
                # If something goes wrong, just rebuild the database
                self.rebuild()

    def rebuild(self):
        self.catContentDB = {}
        self.superclassDB = {}

    def getSubcats(self, supercat):
        """For a given supercategory, return a list of Categorys for all its
        subcategories. Saves this list in a temporary database so that it won't
        be loaded from the server next time it's required.

        """
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
        """For a given category, return a list of Pages for all its articles.
        Saves this list in a temporary database so that it won't be loaded from
        the server next time it's required.

        """
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

    def dump(self, filename='category.dump.bz2'):
        """Save the contents of the dictionaries superclassDB and catContentDB
        to disk.
        """
        if not os.path.isabs(filename):
            filename = config.datafilepath(filename)
        if self.catContentDB or self.superclassDB:
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
        else:
            try:
                os.remove(filename)
            except EnvironmentError:
                pass
            else:
                pywikibot.output(u'Database is empty. %s removed'
                                 % config.shortpath(filename))


class AddCategory:

    """A robot to mass-add a category to a list of pages."""

    def __init__(self, generator, sort_by_last_name=False, create=False,
                 editSummary='', follow_redirects=False, dry=False):
        self.generator = generator
        self.sort = sort_by_last_name
        self.create = create
        self.follow_redirects = follow_redirects
        self.always = False
        self.dry = dry
        self.newcatTitle = None
        self.editSummary = editSummary

    def sorted_by_last_name(self, catlink, pagelink):
        """Return a Category with key that sorts persons by their last name.

        Parameters: catlink - The Category to be linked
                    pagelink - the Page to be placed in the category

        Trailing words in brackets will be removed. Example: If
        category_name is 'Author' and pl is a Page to [[Alexandre Dumas
        (senior)]], this function will return this Category:
        [[Category:Author|Dumas, Alexandre]]

        """
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

    def run(self):
        self.newcatTitle = pywikibot.input(
            u'Category to add (do not give namespace):')
        counter = 0
        for page in self.generator:
            self.treat(page)
            counter += 1
        pywikibot.output(u"%d page(s) processed." % counter)

    def load(self, page):
        """Load the given page, do some changes, and save it."""
        try:
            # Load the page
            text = page.get()
        except pywikibot.NoPage:
            if self.create:
                pywikibot.output(u"Page %s doesn't exist yet; creating."
                                 % (page.title(asLink=True)))
                text = ''
            else:
                pywikibot.output(u"Page %s does not exist; skipping."
                                 % page.title(asLink=True))
        except pywikibot.IsRedirectPage as arg:
            redirTarget = pywikibot.Page(page.site, arg.args[0])
            if self.follow_redirects:
                text = redirTarget.get()
            else:
                pywikibot.warning(u"Page %s is a redirect to %s; skipping."
                                  % (page.title(asLink=True),
                                     redirTarget.title(asLink=True)))
        else:
            return text

    def save(self, text, page, newcatTitle, minorEdit=True, botflag=True):
        # only save if something was changed
        if text != page.get():
            # show what was changed
            pywikibot.showDiff(page.get(), text)
            comment = self.editSummary
            if not comment:
                comment = i18n.twtranslate(page.site, 'category-adding',
                                           {'newcat': newcatTitle})
            pywikibot.output(u'Comment: %s' % comment)
            if not self.dry:
                if not self.always:
                    confirm = 'y'
                    while True:
                        choice = pywikibot.inputChoice(
                            u'Do you want to accept these changes?',
                            ['Yes', 'No', 'Always'], ['y', 'N', 'a'], 'N')
                        if choice == 'a':
                            confirm = pywikibot.inputChoice(u"""\
This should be used if and only if you are sure that your links are correct!
Are you sure?""", ['Yes', 'No'], ['y', 'n'], 'n')
                            if confirm == 'y':
                                self.always = True
                                break
                        else:
                            break
                if self.always or choice == 'y':
                    try:
                        # Save the page
                        page.put(text, comment=comment,
                                 minorEdit=minorEdit, botflag=botflag)
                    except pywikibot.LockedPage:
                        pywikibot.output(u"Page %s is locked; skipping."
                                         % page.title(asLink=True))
                    except pywikibot.EditConflict:
                        pywikibot.output(
                            u'Skipping %s because of edit conflict'
                            % (page.title()))
                    except pywikibot.SpamfilterError as error:
                        pywikibot.output(
                            u'Cannot change %s because of spam blacklist entry '
                            u'%s' % (page.title(), error.url))
                    else:
                        return True
        return False

    def treat(self, page):
        text = self.load(page)
        if text is None:
            return
        cats = [c for c in page.categories()]
        # Show the title of the page we're working on.
        # Highlight the title in purple.
        pywikibot.output(
            u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
            % page.title())
        pywikibot.output(u"Current categories:")
        for cat in cats:
            pywikibot.output(u"* %s" % cat.title())
        newcatTitle = self.newcatTitle
        if not page.site.nocapitalize:
            newcatTitle = newcatTitle[:1].upper() + newcatTitle[1:]
        catpl = pywikibot.Page(page.site, newcatTitle, ns=14)
        if catpl in cats:
            pywikibot.output(u"%s is already in %s."
                             % (page.title(), catpl.title()))
        else:
            if self.sort:
                catpl = self.sorted_by_last_name(catpl, page)
            pywikibot.output(u'Adding %s' % catpl.title(asLink=True))
            cats.append(catpl)
            text = pywikibot.replaceCategoryLinks(text, cats, site=page.site)
            if not self.save(text, page, newcatTitle):
                pywikibot.output(u'Page %s not saved.'
                                 % page.title(asLink=True))


class CategoryMoveRobot(object):

    """Bot to move pages from one category to another or to remove
    pages from categories. The bot moves per default pages and
    subcategories.
    """

    @deprecate_arg("oldCatTitle", "oldcat")
    @deprecate_arg("newCatTitle", "newcat")
    @deprecate_arg("batchMode", "batch")
    @deprecate_arg("editSummary", "comment")
    @deprecate_arg("inPlace", "inplace")
    @deprecate_arg("moveCatPage", "move_oldcat")
    @deprecate_arg("deleteEmptySourceCat", "delete_oldcat")
    @deprecate_arg("titleRegex", "title_regex")
    @deprecate_arg("withHistory", "history")
    def __init__(self, oldcat, newcat=None, batch=False, comment='',
                 inplace=False, move_oldcat=True, delete_oldcat=True,
                 title_regex=None, history=False, pagesonly=False):
        """Store all given parameters in the objects attributes.

        @param oldcat: The move source.
        @param newcat: The move target.
        @param batch: If True the user has not to confirm the deletion.
        @param comment: The edit summary for all pages where the
            category is changed.
        @param inplace: If True the categories are not reordered.
        @param move_oldcat: If True the category page (and talkpage) is
            copied to the new category.
        @param delete_oldcat: If True the oldcat page and talkpage are
            deleted (or nominated for deletion) if it is empty.
        @param title_regex: Only pages (and subcats) with a title that
            matches the regex are moved.
        @param history: If True the history of the oldcat is posted on
            the talkpage of newcat.
        @param pagesonly: If True only move pages, not subcategories.
        """
        self.site = pywikibot.Site()
        # Create attributes for the categories and their talk pages.
        self.oldcat = self._makecat(oldcat)
        self.oldtalk = self.oldcat.toggleTalkPage()
        if newcat:
            self.newcat = self._makecat(newcat)
            self.newtalk = self.newcat.toggleTalkPage()
        else:
            self.newcat = None
            self.newtalk = None
        # Set boolean settings.
        self.inplace = inplace
        self.move_oldcat = move_oldcat
        self.delete_oldcat = delete_oldcat
        self.batch = batch
        self.title_regex = title_regex
        self.history = history
        self.pagesonly = pagesonly
        # Set edit summary for changed pages.
        self.comment = comment
        if not self.comment:
            if self.newcat:
                template_vars = {
                    'oldcat': self.oldcat.title(withNamespace=False),
                    'newcat': self.newcat.title(withNamespace=False)}
                self.comment = i18n.twtranslate(self.site,
                                                'category-replacing',
                                                template_vars)
            else:
                template_vars = {'oldcat': self.oldcat.title(
                    withNamespace=False)}
                self.comment = i18n.twtranslate(self.site,
                                                'category-removing',
                                                template_vars)

    def run(self):
        """The main bot function that does all the work.
        For readability it is splitted into several helper functions.
        """
        if self.newcat and self.move_oldcat and not self.newcat.exists():
            if "move-categorypages" in self.site.userinfo["rights"]:
                self.oldcat.move(self.newcat.title(), reason=self.comment,
                                 movetalkpage=True)
            else:
                self._movecat()
                self._movetalk()
            if self.history:
                self._hist()
        self._change(pagegenerators.CategorizedPageGenerator(self.oldcat))
        if not self.pagesonly:
            self._change(pagegenerators.SubCategoriesPageGenerator(self.oldcat))
        if self.oldcat.isEmptyCategory() and self.delete_oldcat and \
                ((self.newcat and self.move_oldcat) or not self.newcat):
            self._delete()

    def _delete(self):
        """Private function to delete the category page and its talk page.
        Do not use this function from outside the class.
        """
        template_vars = {'newcat': self.newcat.title(withNamespace=False),
                         'title': self.newcat.title(withNamespace=False)}
        comment = i18n.twtranslate(self.site,
                                   'category-was-moved',
                                   template_vars)
        self.oldcat.delete(comment, not self.batch, mark=True)
        if self.oldtalk.exists():
            self.oldtalk.delete(comment, not self.batch, mark=True)

    def _change(self, gen):
        """Private function to move category contents.
        Do not use this function from outside the class.

        @param gen: Generator containing pages or categories.
        """
        for page in pagegenerators.PreloadingGenerator(gen):
            if not self.title_regex or re.search(self.title_regex,
                                                 page.title()):
                page.change_category(self.oldcat, self.newcat,
                                     comment=self.comment,
                                     inPlace=self.inplace)

    def _movecat(self):
        """Private function to move the category page.
        Do not use this function from outside the class.
        """
        # Some preparing
        pywikibot.output('Moving text from %s to %s.' % (self.oldcat.title(),
                                                         self.newcat.title()))
        authors = ', '.join(self.oldcat.contributingUsers())
        template_vars = (self.oldcat.title(), authors)
        comment = i18n.twtranslate(self.site,
                                   'category-renamed') % template_vars
        self.newcat.text = self.oldcat.text
        # Replace stuff
        REGEX = r"<!--BEGIN CFD TEMPLATE-->.*?<!--END CFD TEMPLATE-->"
        match = re.compile(REGEX,
                           re.IGNORECASE | re.MULTILINE | re.DOTALL)
        self.newcat.text = match.sub('', self.newcat.text)
        site_templates = i18n.translate(self.site, cfd_templates)
        for template_name in site_templates:
            match = re.compile(r"{{%s.*?}}" % template_name, re.IGNORECASE)
            self.newcat.text = match.sub('', self.newcat.text)
        # Remove leading whitespace
        self.newcat.text = self.newcat.text.lstrip()
        self.newcat.save(comment)

    def _movetalk(self):
        """Private function to move the category talk page.
        Do not use this function from outside the class.
        """
        if self.oldtalk.exists():
            comment = i18n.twtranslate(self.site, 'category-was-moved',
                                       {'newcat': self.newcat.title(),
                                        'title': self.newcat.title()})
            self.oldtalk.move(self.newtalk.title(), comment)

    def _hist(self):
        """Private function to create a history table with the history
        of the old category on the new talk page.
        Do not use this function from outside the class.
        """
        history = self.oldcat.getVersionHistoryTable()
        title = i18n.twtranslate(self.site, 'category-section-title',
                                 {'oldcat': self.oldcat.title()})
        self.newtalk.text = "%s\n== %s ==\n%s" % (self.newtalk.text,
                                                  title, history)
        comment = i18n.twtranslate(self.site, 'category-version-history',
                                   {'oldcat': self.oldcat.title()})
        self.newtalk.save(comment)

    def _makecat(self, var):
        """Private helper function to get a Category object either from
        a string or use just use the given one (for backwards
        compatibility).
        """
        if not isinstance(var, pywikibot.Category):
            var = pywikibot.Category(self.site, var)
        return var


class CategoryListifyRobot:

    """Create a list containing all of the members in a category."""

    def __init__(self, catTitle, listTitle, editSummary, overwrite=False,
                 showImages=False, subCats=False, talkPages=False,
                 recurse=False):
        self.editSummary = editSummary
        self.overwrite = overwrite
        self.showImages = showImages
        self.site = pywikibot.Site()
        self.cat = pywikibot.Category(self.site, catTitle)
        self.list = pywikibot.Page(self.site, listTitle)
        self.subCats = subCats
        self.talkPages = talkPages
        self.recurse = recurse

    def run(self):
        setOfArticles = set(self.cat.articles(recurse=self.recurse))
        if self.subCats:
            setOfArticles = setOfArticles.union(set(self.cat.subcategories()))
        if not self.editSummary:
            self.editSummary = i18n.twntranslate(self.site,
                                                 'category-listifying',
                                                 {'fromcat': self.cat.title(),
                                                  'num': len(setOfArticles)})

        listString = ""
        for article in setOfArticles:
            if (not article.isImage() or
                    self.showImages) and not article.isCategory():
                if self.talkPages and not article.isTalkPage():
                    listString += "*[[%s]] -- [[%s|talk]]\n" \
                                  % (article.title(),
                                     article.toggleTalkPage().title())
                else:
                    listString += "*[[%s]]\n" % article.title()
            else:
                if self.talkPages and not article.isTalkPage():
                    listString += "*[[:%s]] -- [[%s|talk]]\n" \
                                  % (article.title(),
                                     article.toggleTalkPage().title())
                else:
                    listString += "*[[:%s]]\n" % article.title()
        if self.list.exists() and not self.overwrite:
            pywikibot.output(u'Page %s already exists, aborting.'
                             % self.list.title())
        else:
            self.list.put(listString, comment=self.editSummary)


class CategoryRemoveRobot:

    """Remove the category tag from all pages in a given category
    and if pagesonly parameter is False also from the category pages of all
    subcategories, without prompting.
    If the category is empty, it will be tagged for deletion.
    Do not remove category tags pointing at subcategories.

    """

    def __init__(self, catTitle, batchMode=False, editSummary='',
                 useSummaryForDeletion=True, titleRegex=None, inPlace=False,
                 pagesonly=False):
        self.editSummary = editSummary
        self.site = pywikibot.Site()
        self.cat = pywikibot.Category(self.site, catTitle)
        # get edit summary message
        self.useSummaryForDeletion = useSummaryForDeletion
        self.batchMode = batchMode
        self.titleRegex = titleRegex
        self.inPlace = inPlace
        self.pagesonly = pagesonly
        if not self.editSummary:
            self.editSummary = i18n.twtranslate(self.site, 'category-removing',
                                                {'oldcat': self.cat.title()})

    def run(self):
        if self.cat.categoryinfo['pages'] == 0:
            pywikibot.output(u'There are no articles in category %s'
                             % self.cat.title())
        else:
            for article in self.cat.articles():
                if not self.titleRegex or re.search(self.titleRegex,
                                                    article.title()):
                    article.change_category(self.cat, None,
                                            comment=self.editSummary,
                                            inPlace=self.inPlace)
        if self.pagesonly:
            return

        # Also removes the category tag from subcategories' pages
        if self.cat.categoryinfo['subcats'] == 0:
            pywikibot.output(u'There are no subcategories in category %s'
                             % self.cat.title())
        else:
            for subcategory in self.cat.subcategories():
                subcategory.change_category(self.cat, None,
                                            comment=self.editSummary,
                                            inPlace=self.inPlace)
        # Deletes the category page
        if self.cat.exists() and self.cat.isEmptyCategory():
            if self.useSummaryForDeletion and self.editSummary:
                reason = self.editSummary
            else:
                reason = i18n.twtranslate(self.site, 'category-was-disbanded')
            talkPage = self.cat.toggleTalkPage()
            try:
                self.cat.delete(reason, not self.batchMode)
            except pywikibot.NoUsername:
                pywikibot.output(
                    u'You\'re not setup sysop info, category will not delete.'
                    % self.cat.site())
                return
            if (talkPage.exists()):
                talkPage.delete(reason=reason, prompt=not self.batchMode)


class CategoryTidyRobot:

    """Script to help a human to tidy up a category by moving its articles into
    subcategories

    Specify the category name on the command line. The program will pick up the
    page, and look for all subcategories and supercategories, and show them with
    a number adjacent to them. It will then automatically loop over all pages
    in the category. It will ask you to type the number of the appropriate
    replacement, and perform the change robotically.

    If you don't want to move the article to a subcategory or supercategory, but
    to another category, you can use the 'j' (jump) command.

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
        self.site = pywikibot.Site()
        self.editSummary = i18n.twtranslate(self.site, 'category-changing',
                                            {'oldcat': self.catTitle,
                                             'newcat': u''})

    def move_to_category(self, article, original_cat, current_cat):
        """
        Given an article which is in category original_cat, ask the user if
        it should be moved to one of original_cat's subcategories.
        Recursively run through subcategories' subcategories.
        NOTE: current_cat is only used for internal recursion. You should
        always use current_cat = original_cat.
        """
        pywikibot.output(u'')
        # Show the title of the page where the link was found.
        # Highlight the title in purple.
        pywikibot.output(
            u'Treating page \03{lightpurple}%s\03{default}, '
            u'currently in \03{lightpurple}%s\03{default}'
            % (article.title(), current_cat.title()))

        # Determine a reasonable amount of context to print
        try:
            full_text = article.get(get_redirect=True)
        except pywikibot.NoPage:
            pywikibot.output(u'Page %s not found.' % article.title())
            return
        try:
            contextLength = full_text.index('\n\n')
        except ValueError:  # substring not found
            contextLength = 500
        if full_text.startswith(u'[['):  # probably an image
            # Add extra paragraph.
            contextLength = full_text.find('\n\n', contextLength + 2)
        if contextLength > 1000 or contextLength < 0:
            contextLength = 500

        pywikibot.output('\n' + full_text[:contextLength] + '\n')

        # we need list to index the choice
        subcatlist = list(self.catDB.getSubcats(current_cat))
        supercatlist = list(self.catDB.getSupercats(current_cat))

        if not subcatlist:
            pywikibot.output('This category has no subcategories.\n')
        if not supercatlist:
            pywikibot.output('This category has no supercategories.\n')
        # show subcategories as possible choices (with numbers)
        for i, supercat in enumerate(supercatlist):
            # layout: we don't expect a cat to have more than 10 supercats
            pywikibot.output(u'u%d - Move up to %s' % (i, supercat.title()))
        for i, subcat in enumerate(subcatlist):
            # layout: we don't expect a cat to have more than 100 subcats
            pywikibot.output(u'%2d - Move down to %s' % (i, subcat.title()))
        pywikibot.output(' j - Jump to another category\n'
                         ' s - Skip this article\n'
                         ' r - Remove this category tag\n'
                         ' ? - Print first part of the page (longer and longer)\n'
                         u'Enter - Save category as %s' % current_cat.title())

        flag = False
        while not flag:
            pywikibot.output('')
            choice = pywikibot.input(u'Choice:')
            if choice in ['s', 'S']:
                flag = True
            elif choice == '':
                pywikibot.output(u'Saving category as %s' % current_cat.title())
                if current_cat == original_cat:
                    pywikibot.output('No changes necessary.')
                else:
                    article.change_category(original_cat, current_cat,
                                            comment=self.editSummary)
                flag = True
            elif choice in ['j', 'J']:
                newCatTitle = pywikibot.input(u'Please enter the category the '
                                              u'article should be moved to:')
                newCat = pywikibot.Category(pywikibot.Link('Category:' +
                                                           newCatTitle))
                # recurse into chosen category
                self.move_to_category(article, original_cat, newCat)
                flag = True
            elif choice in ['r', 'R']:
                # remove the category tag
                article.change_category(original_cat, None,
                                        comment=self.editSummary)
                flag = True
            elif choice == '?':
                contextLength += 500
                pywikibot.output('\n' + full_text[:contextLength] + '\n')

                # if categories possibly weren't visible, show them additionally
                # (maybe this should always be shown?)
                if len(full_text) > contextLength:
                    pywikibot.output('')
                    pywikibot.output('Original categories: ')
                    for cat in article.categories():
                        pywikibot.output(u'* %s' % cat.title())
            elif choice[0] == 'u':
                try:
                    choice = int(choice[1:])
                except ValueError:
                    # user pressed an unknown command. Prompt him again.
                    continue
                self.move_to_category(article, original_cat,
                                      supercatlist[choice])
                flag = True
            else:
                try:
                    choice = int(choice)
                except ValueError:
                    # user pressed an unknown command. Prompt him again.
                    continue
                # recurse into subcategory
                self.move_to_category(article, original_cat, subcatlist[choice])
                flag = True

    def run(self):
        cat = pywikibot.Category(self.site, self.catTitle)

        if cat.categoryinfo['pages'] == 0:
            pywikibot.output(u'There are no articles in category %s'
                             % self.catTitle)
        else:
            preloadingGen = pagegenerators.PreloadingGenerator(cat.articles())
            for article in preloadingGen:
                pywikibot.output('')
                pywikibot.output(u'=' * 67)
                self.move_to_category(article, cat, cat)


class CategoryTreeRobot:

    """ Robot to create tree overviews of the category structure.

    Parameters:
        * catTitle - The category which will be the tree's root.
        * catDB    - A CategoryDatabase object
        * maxDepth - The limit beyond which no subcategories will be listed.
                     This also guarantees that loops in the category structure
                     won't be a problem.
        * filename - The textfile where the tree should be saved; None to print
                     the tree to stdout.
    """

    def __init__(self, catTitle, catDB, filename=None, maxDepth=10):
        self.catTitle = catTitle
        self.catDB = catDB
        if filename and not os.path.isabs(filename):
            filename = config.datafilepath(filename)
        self.filename = filename
        self.maxDepth = maxDepth
        self.site = pywikibot.Site()

    def treeview(self, cat, currentDepth=0, parent=None):
        """ Return a multi-line string which contains a tree view of all
        subcategories of cat, up to level maxDepth. Recursively calls itself.

        Parameters:
            * cat - the Category of the node we're currently opening
            * currentDepth - the current level in the tree (for recursion)
            * parent - the Category of the category we're coming from

        """
        result = u'#' * currentDepth
        if currentDepth > 0:
            result += u' '
        result += cat.title(asLink=True, textlink=True, withNamespace=False)
        result += ' (%d)' % cat.categoryinfo['pages']
        if currentDepth < self.maxDepth / 2:
            # noisy dots
            pywikibot.output('.', newline=False)
        # Find out which other cats are supercats of the current cat
        supercat_names = []
        for cat in self.catDB.getSupercats(cat):
            # create a list of wiki links to the supercategories
            if cat != parent:
                supercat_names.append(cat.title(asLink=True,
                                                textlink=True,
                                                withNamespace=False))
        if supercat_names:
            # print this list, separated with commas, using translations
            # given in also_in_cats
            result += ' ' + i18n.twtranslate(self.site, 'category-also-in',
                                             {'alsocat': ', '.join(
                                                 supercat_names)})
        del supercat_names
        result += '\n'
        if currentDepth < self.maxDepth:
            for subcat in self.catDB.getSubcats(cat):
                # recurse into subdirectories
                result += self.treeview(subcat, currentDepth + 1, parent=cat)
        elif self.catDB.getSubcats(cat):
            # show that there are more categories beyond the depth limit
            result += '#' * (currentDepth + 1) + ' [...]\n'
        return result

    def run(self):
        """Print the multi-line string generated by treeview or save it to a
        file.

        Parameters:
            * catTitle - the title of the category which will be the tree's root
            * maxDepth - the limit beyond which no subcategories will be listed

        """
        cat = pywikibot.Category(self.site, self.catTitle)
        pywikibot.output('Generating tree...', newline=False)
        tree = self.treeview(cat)
        pywikibot.output(u'')
        if self.filename:
            pywikibot.output(u'Saving results in %s' % self.filename)
            import codecs
            f = codecs.open(self.filename, 'a', 'utf-8')
            f.write(tree)
            f.close()
        else:
            pywikibot.output(tree, toStdout=True)


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
    pagesonly = False
    withHistory = False
    rebuild = False
    depth = 5

    # Process global args and prepare generator args parser
    local_args = pywikibot.handleArgs(*args)
    genFactory = pagegenerators.GeneratorFactory()

    # The generator gives the pages that should be worked upon.
    gen = None

    # If this is set to true then the custom edit summary given for removing
    # categories from articles will also be used as the deletion reason.
    useSummaryForDeletion = True
    action = None
    sort_by_last_name = False
    create_pages = False
    follow_redirects = False
    deleteEmptySourceCat = True
    for arg in local_args:
        if arg in ('add', 'remove', 'move', 'tidy', 'tree', 'listify'):
            action = arg
        elif arg == '-nodelete':
            deleteEmptySourceCat = False
        elif arg == '-person':
            sort_by_last_name = True
        elif arg == '-rebuild':
            rebuild = True
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
        elif arg == '-pagesonly':
            pagesonly = True
        elif arg == '-create':
            create_pages = True
        elif arg == '-redirect':
            follow_redirects = True
        elif arg == '-hist':
            withHistory = True
        elif arg.startswith('-depth:'):
            depth = int(arg[len('-depth:'):])
        else:
            genFactory.handleArg(arg)
    pywikibot.Site().login()

    catDB = CategoryDatabase(rebuild=rebuild)
    gen = genFactory.getCombinedGenerator()
    if action == 'add':
        if not gen:
            # default for backwards compatibility
            genFactory.handleArg('-links')
            gen = genFactory.getCombinedGenerator()
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        gen = pagegenerators.PreloadingGenerator(gen)
        bot = AddCategory(gen, sort_by_last_name, create_pages, editSummary,
                          follow_redirects)
        bot.run()
    elif action == 'remove':
        if not fromGiven:
            oldCatTitle = pywikibot.input(u'Please enter the name of the '
                                          u'category that should be removed:')
        bot = CategoryRemoveRobot(oldCatTitle, batchMode, editSummary,
                                  useSummaryForDeletion, inPlace=inPlace,
                                  pagesonly=pagesonly)
        bot.run()
    elif action == 'move':
        if not fromGiven:
            oldCatTitle = pywikibot.input(
                u'Please enter the old name of the category:')
        if not toGiven:
            newCatTitle = pywikibot.input(
                u'Please enter the new name of the category:')
        bot = CategoryMoveRobot(oldCatTitle, newCatTitle, batchMode,
                                editSummary, inPlace,
                                delete_oldcat=deleteEmptySourceCat,
                                title_regex=titleRegex, history=withHistory)
        bot.run()
    elif action == 'tidy':
        catTitle = pywikibot.input(u'Which category do you want to tidy up?')
        bot = CategoryTidyRobot(catTitle, catDB)
        bot.run()
    elif action == 'tree':
        catTitle = pywikibot.input(
            u'For which category do you want to create a tree view?')
        filename = pywikibot.input(
            u'Please enter the name of the file where the tree should be saved,'
            u'\nor press enter to simply show the tree:')
        bot = CategoryTreeRobot(catTitle, catDB, filename, depth)
        bot.run()
    elif action == 'listify':
        if not fromGiven:
            oldCatTitle = pywikibot.input(
                u'Please enter the name of the category to listify:')
        if not toGiven:
            newCatTitle = pywikibot.input(
                u'Please enter the name of the list to create:')
        bot = CategoryListifyRobot(oldCatTitle, newCatTitle, editSummary,
                                   overwrite, showImages, subCats=True,
                                   talkPages=talkPages, recurse=recurse)
        bot.run()
    else:
        pywikibot.showHelp()


if __name__ == "__main__":
    try:
        main()
    except pywikibot.Error:
        pywikibot.error("Fatal error:", exc_info=True)
    finally:
        if 'catDB' in globals():
            catDB.dump()
