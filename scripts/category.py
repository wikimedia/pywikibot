#!/usr/bin/env python3
"""Script to manage categories.

Syntax:

    python pwb.py category action [-option]

where action can be one of these

*add*
    mass-add a category to a list of pages.
*remove*
    remove category tag from all pages in a category. If a pagegenerators
    option is given, the intersection with category pages is processed.
*move*
    move all pages in a category to another category. If a pagegenerators
    option is given, the intersection with category pages is processed.
*tidy*
    tidy up a category by moving its pages into subcategories.
*tree*
    show a tree of subcategories of a given category.
*listify*
    make a list of all of the articles that are in a category.
*clean*
    Removes redundant grandchildren from specified category by removing
    direct link to grandparent. In another words a grandchildren should
    not be also a children.

and option can be one of these

Options for "add" action:

 -person      - Sort persons by their last name.
 -create      - If a page doesn't exist, do not skip it, create it instead.
 -redirect    - Follow redirects.


Options for "listify" action:

 -append      - This appends the list to the current page that is already
                existing (appending to the bottom by default).
 -overwrite   - This overwrites the current page with the list even if
                something is already there.
 -showimages  - This displays images rather than linking them in the list.
 -talkpages   - This outputs the links to talk pages of the pages to be
                listified in addition to the pages themselves.
 -prefix:#    - You may specify a list prefix like "#" for a numbered list or
                any other prefix. Default is a bullet list with prefix "*".

Options for "remove" action:

 -nodelsum    - This specifies not to use the custom edit summary as the
                deletion reason. Instead, it uses the default deletion reason
                for the language, which is "Category was disbanded" in
                English.

Options for "move" action:

 -hist        - Creates a nice wikitable on the talk page of target category
                that contains detailed page history of the source category.
 -nodelete    - Don't delete the old category after move.
 -nowb        - Don't update the Wikibase repository.
 -allowsplit  - If that option is not set, it only moves the talk and main
                page together.
 -mvtogether  - Only move the pages/subcategories of a category, if the
                target page (and talk page, if -allowsplit is not set)
                doesn't exist.
 -keepsortkey - Use sortKey of the old category also for the new category.
                If not specified, sortKey is removed.
                An alternative method to keep sortKey is to use -inplace
                option.

Options for "listify" and "tidy" actions:

 -namespaces    Filter the arcitles in the specified namespaces. Separate
 -namespace     multiple namespace numbers or names with commas. Examples:
 -ns            -ns:0,2,4
                -ns:Help,MediaWiki

Options for "clean" action:

 -always

Options for several actions:

 -rebuild     - Reset the database.
 -from:       - The category to move from (for the move option)
                Also, the category to remove from in the remove option
                Also, the category to make a list of in the listify option.
 -to:         - The category to move to (for the move option).
              - Also, the name of the list to make in the listify option.

 -batch       - Don't prompt to delete emptied categories (do it
                automatically).
 -summary:    - Pick a custom edit summary for the bot.
 -inplace     - Use this flag to change categories in place rather than
                rearranging them.
 -recurse[:<depth>]
              - Recurse through subcategories of the category to
                optional depth.
 -pagesonly   - While removing pages from a category, keep the subpage links
                and do not remove them.
 -match       - Only work on pages whose titles match the given regex (for
                move and remove actions).
 -depth:      - The max depth limit beyond which no subcategories will be
                listed.

.. note:: If the category names have spaces in them you may need to use
   a special syntax in your shell so that the names aren't treated as
   separate parameters. For instance, in BASH, use single quotes, e.g.
   ``-from:'Polar bears'``.

If action is "add", "move" or "remove, the following additional options are
supported:

&params;

For the actions tidy and tree, the bot will store the category structure
locally in category.dump. This saves time and server load, but if it uses
these data later, they may be outdated; use the -rebuild parameter in this
case.

For example, to create a new category from a list of persons, type:

    python pwb.py category add -person

and follow the on-screen instructions.

Or to do it all from the command-line, use the following syntax:

    python pwb.py category move -from:US -to:"United States"

This will move all pages in the category US to the category United States.

A pagegenerators option can be given with ``move`` and ``remove`` action:

    pwb category -site:wikipedia:en remove -from:Hydraulics -cat:Pneumatics

The sample above would remove 'Hydraulics' category from all pages which
are also in 'Pneumatics' category.

.. versionchanged:: 8.0
   :mod:`pagegenerators` are supported with "move" and "remove" action.
"""
#
# (C) Pywikibot team, 2004-2022
#
# Distributed under the terms of the MIT license.
#
import codecs
import math
import os
import pickle
import re
from contextlib import suppress
from itertools import chain
from operator import methodcaller
from textwrap import fill
from typing import Optional, Union

import pywikibot
from pywikibot import config, i18n, pagegenerators, textlib
from pywikibot.backports import Sequence, Set  # skipcq: PY-W2000
from pywikibot.bot import (
    BaseBot,
    Bot,
    ContextOption,
    IntegerOption,
    StandardOption,
    suggest_help,
)
from pywikibot.cosmetic_changes import moved_links
from pywikibot.exceptions import (
    Error,
    NoPageError,
    NoUsernameError,
    PageSaveRelatedError,
)
from pywikibot.tools import open_archive
from pywikibot.tools.itertools import intersect_generators


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

CFD_TEMPLATE_REGEX = re.compile(r'<!--\s*BEGIN CFD TEMPLATE\s*-->.*?'
                                r'<!--\s*END CFD TEMPLATE\s*-->\n?',
                                flags=re.I | re.M | re.S)

cfd_templates = {
    'wikipedia': {
        'cs': ['přesunout', 'přejmenovat', 'přejmenovat kategorii',
               'přesunout kategorii', 'přejmenování kategorie'],
        'en': ['cfd', 'cfr', 'cfru', 'cfr-speedy', 'cfm', 'cfdu'],
        'fi': ['roskaa', 'poistettava', 'korjattava/nimi',
               'yhdistettäväLuokka'],
        'fr': ['renommage de catégorie demandé'],
        'he': ['הצבעת מחיקה', 'למחוק'],
        'nl': ['categorieweg', 'catweg', 'wegcat', 'weg2'],
        # For testing purposes
        'test': ['delete']
    },
    'commons': {
        'commons': ['cfd', 'move']
    }
}


class CategoryPreprocess(BaseBot):

    """A class to prepare a list of pages for robots."""

    def __init__(
        self,
        follow_redirects: bool = False,
        edit_redirects: bool = False,
        create: bool = False,
        **kwargs
    ) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        self.follow_redirects = follow_redirects
        self.edit_redirects = edit_redirects
        self.create = create

    def determine_type_target(
        self,
        page: pywikibot.Page
    ) -> Optional[pywikibot.Page]:
        """
        Return page to be categorized by type.

        :param page: Existing, missing or redirect page to be processed.
        :return: Page to be categorized.
        """
        if page.exists():
            if not page.isRedirectPage():
                return page

            # if it is a redirect, use the redirect target instead
            redir_target = page.getRedirectTarget()
            if self.follow_redirects:
                if redir_target.exists():
                    return redir_target

                if self.create:
                    redir_target.text = ''
                    pywikibot.info(f'Redirect target {redir_target} does not '
                                   f'exist yet; creating.')
                    return redir_target

                if self.edit_redirects:
                    return page

                pywikibot.warning(f'Redirect target {redir_target} cannot be '
                                  f'modified; skipping.')
                return None

            if self.edit_redirects:
                return page

            pywikibot.warning(
                f'Page {page} is a redirect to {redir_target}; skipping.')
            return None

        if self.create:
            page.text = ''
            pywikibot.info(f'Page {page} does not exist yet; creating.')
            return page

        pywikibot.warning(f'Page {page} does not exist; skipping.')
        return None

    def determine_template_target(self, page) -> pywikibot.Page:
        """
        Return template page to be categorized.

        Categories for templates can be included
        in <includeonly> section of template doc page.

        Also the doc page can be changed by doc template parameter.

        TODO: decide if/how to enable/disable this feature.

        :param page: Page to be processed.
        :type page: pywikibot.Page
        :return: Page to be categorized.
        """
        if page.namespace() != page.site.namespaces.TEMPLATE:
            self.includeonly = []
            return page

        tmpl: Sequence = []
        with suppress(KeyError):
            tmpl, _loc = moved_links[page.site.code]

        if not isinstance(tmpl, list):
            tmpl = [tmpl]

        includeonly = []
        if tmpl:
            templates = page.templatesWithParams()
            for template, params in templates:
                if template.title(with_ns=False).lower() in tmpl and params:
                    doc_page = pywikibot.Page(page.site, params[0])
                    if doc_page.exists():
                        page = doc_page
                        includeonly = ['includeonly']
                        break

        if not includeonly:
            docs = page.site.doc_subpage  # return tuple
            for doc in docs:
                doc_page = pywikibot.Page(page.site, page.title() + doc)
                if doc_page.exists():
                    page = doc_page
                    includeonly = ['includeonly']
                    break

        self.includeonly = includeonly
        return page


class CategoryDatabase:

    """Temporary database saving pages and subcategories for each category.

    This prevents loading the category pages over and over again.
    """

    def __init__(
        self,
        rebuild: bool = False,
        filename: str = 'category.dump.bz2'
    ) -> None:
        """Initializer."""
        if not os.path.isabs(filename):
            filename = config.datafilepath(filename)
        self.filename = filename
        if rebuild:
            self.rebuild()

    @property
    def is_loaded(self) -> bool:
        """Return whether the contents have been loaded."""
        return (hasattr(self, 'cat_content_db')
                and hasattr(self, 'superclass_db'))

    def _load(self) -> None:
        if not self.is_loaded:
            try:
                if config.verbose_output:
                    pywikibot.info('Reading dump from '
                                   + config.shortpath(self.filename))
                with open_archive(self.filename, 'rb') as f:
                    databases = pickle.load(f)
                # keys are categories, values are 2-tuples with lists as
                # entries.
                self.cat_content_db = databases['cat_content_db']
                # like the above, but for supercategories
                self.superclass_db = databases['superclass_db']
                del databases
            except Exception:
                # If something goes wrong, just rebuild the database
                self.rebuild()

    def rebuild(self) -> None:
        """Rebuild the dabatase."""
        self.cat_content_db = {}
        self.superclass_db = {}

    def get_subcats(self, supercat) -> Set[pywikibot.Category]:
        """Return the list of subcategories for a given supercategory.

        Saves this list in a temporary database so that it won't be loaded
        from the server next time it's required.
        """
        self._load()
        # if we already know which subcategories exist here
        if supercat in self.cat_content_db:
            return self.cat_content_db[supercat][0]
        subcatset = set(supercat.subcategories())
        articleset = set(supercat.articles())
        # add to dictionary
        self.cat_content_db[supercat] = (subcatset, articleset)
        return subcatset

    def get_articles(self, cat) -> Set[pywikibot.Page]:
        """Return the list of pages for a given category.

        Saves this list in a temporary database so that it won't be loaded
        from the server next time it's required.
        """
        self._load()
        # if we already know which articles exist here.
        if cat in self.cat_content_db:
            return self.cat_content_db[cat][1]
        subcatset = set(cat.subcategories())
        articleset = set(cat.articles())
        # add to dictionary
        self.cat_content_db[cat] = (subcatset, articleset)
        return articleset

    def get_supercats(self, subcat) -> Set[pywikibot.Category]:
        """Return the supercategory (or a set of) for a given subcategory."""
        self._load()
        # if we already know which subcategories exist here.
        if subcat in self.superclass_db:
            return self.superclass_db[subcat]
        supercatset = set(subcat.categories())
        # add to dictionary
        self.superclass_db[subcat] = supercatset
        return supercatset

    def dump(self, filename=None) -> None:
        """Save the dictionaries to disk if not empty.

        Pickle the contents of the dictionaries superclass_db and
        cat_content_db if at least one is not empty. If both are empty,
        removes the file from the disk.

        If the filename is None, it'll use the filename determined in __init__.
        """
        if filename is None:
            filename = self.filename
        elif not os.path.isabs(filename):
            filename = config.datafilepath(filename)
        if self.is_loaded and (self.cat_content_db or self.superclass_db):
            pywikibot.info('Dumping to {}, please wait...'
                           .format(config.shortpath(filename)))
            databases = {
                'cat_content_db': self.cat_content_db,
                'superclass_db': self.superclass_db
            }
            # store dump to disk in binary format
            with open_archive(filename, 'wb') as f, \
                 suppress(pickle.PicklingError):
                pickle.dump(databases, f, protocol=config.pickle_protocol)
        else:
            with suppress(EnvironmentError):
                os.remove(filename)
                pywikibot.info('Database is empty. {} removed'
                               .format(config.shortpath(filename)))


class CategoryAddBot(CategoryPreprocess):

    """A robot to mass-add a category to a list of pages."""

    def __init__(self, generator, newcat=None,
                 sort_by_last_name: bool = False,
                 create: bool = False,
                 comment: str = '',
                 follow_redirects: bool = False) -> None:
        """Initializer."""
        super().__init__()
        self.generator = generator
        self.newcat = newcat or pywikibot.input(
            'Category to add (do not give namespace):')
        self.sort = sort_by_last_name
        self.create = create
        self.follow_redirects = follow_redirects
        self.comment = comment

    @staticmethod
    def sorted_by_last_name(catlink, pagelink) -> pywikibot.Page:
        """Return a Category with key that sorts persons by their last name.

        Parameters: catlink - The Category to be linked.
                    pagelink - the Page to be placed in the category.

        Trailing words in brackets will be removed. Example: If
        category_name is 'Author' and pl is a Page to [[Alexandre Dumas
        (senior)]], this function will return this Category:
        [[Category:Author|Dumas, Alexandre]].
        """
        page_name = pagelink.title()
        site = pagelink.site
        # regular expression that matches a name followed by a space and
        # disambiguation brackets. Group 1 is the name without the rest.
        brackets_regex = re.compile(r'(.*) \(.+?\)')
        match_object = brackets_regex.match(page_name)
        if match_object:
            page_name = match_object[1]
        split_string = page_name.rsplit(' ', 1)
        if len(split_string) > 1:
            # pull last part of the name to the beginning, and append the
            # rest after a comma; e.g., "John von Neumann" becomes
            # "Neumann, John von"
            sorted_key = split_string[1] + ', ' + split_string[0]
            # give explicit sort key
            return pywikibot.Page(site, catlink.title() + '|' + sorted_key)
        return pywikibot.Page(site, catlink.title())

    def treat(self, page) -> None:
        """Process one page."""
        # find correct categorization target
        page = self.determine_type_target(page)
        if not page:
            return
        self.current_page = self.determine_template_target(page)
        # load the page
        text = self.current_page.text
        # store old text, so we don't have reload it every time
        old_text = text
        cats = textlib.getCategoryLinks(
            text, self.current_page.site, include=self.includeonly)
        pywikibot.info('Current categories:')
        for cat in cats:
            pywikibot.info('* ' + cat.title())
        catpl = pywikibot.Category(self.current_page.site, self.newcat)
        if catpl in cats:
            pywikibot.info('{} is already in {}.'
                           .format(self.current_page.title(), catpl.title()))
        else:
            if self.sort:
                catpl = self.sorted_by_last_name(catpl, self.current_page)
            pywikibot.info(f'Adding {catpl.title(as_link=True)}')
            if page.namespace() == page.site.namespaces.TEMPLATE:
                tagname = 'noinclude'
                if self.includeonly == ['includeonly']:
                    tagname = 'includeonly'
                tagnameregexp = re.compile(fr'(.*)(<\/{tagname}>)',
                                           re.I | re.DOTALL)
                categorytitle = catpl.title(
                    as_link=True, allow_interwiki=False)
                if tagnameregexp.search(text):
                    # add category into the <includeonly> tag in the
                    # template document page or the <noinclude> tag
                    # in the template page
                    text = textlib.replaceExcept(
                        text, tagnameregexp,
                        fr'\1{categorytitle}\n\2',
                        ['comment', 'math', 'nowiki', 'pre',
                         'syntaxhighlight'],
                        site=self.current_page.site)
                else:
                    if self.includeonly == ['includeonly']:
                        text += '\n\n'
                    text += '<{0}>\n{1}\n</{0}>'.format(
                            tagname, categorytitle)
            else:
                cats.append(catpl)
                text = textlib.replaceCategoryLinks(
                    text, cats, site=self.current_page.site)
            comment = self.comment
            if not comment:
                comment = i18n.twtranslate(self.current_page.site,
                                           'category-adding',
                                           {'newcat': catpl.title(
                                               with_ns=False)})
            try:
                self.userPut(self.current_page, old_text, text,
                             summary=comment)
            except PageSaveRelatedError as error:
                pywikibot.info(f'Page {self.current_page} not saved: {error}')


class CategoryMoveRobot(CategoryPreprocess):

    """Change or remove the category from the pages.

    If the new category is given changes the category from the old to the new
    one. Otherwise remove the category from the page and the category if it's
    empty.

    Per default the operation applies to pages and subcategories.

    .. versionadded:: 8.0
       The ``generator`` parameter.
    """

    DELETION_COMMENT_AUTOMATIC = 0
    DELETION_COMMENT_SAME_AS_EDIT_COMMENT = 1

    def __init__(self, oldcat,
                 newcat=None,
                 batch: bool = False,
                 comment: str = '',
                 inplace: bool = False,
                 move_oldcat: bool = True,
                 delete_oldcat: bool = True,
                 title_regex=None,
                 history: bool = False,
                 pagesonly: bool = False,
                 deletion_comment: Union[
                     int, str] = DELETION_COMMENT_AUTOMATIC,
                 move_comment=None,
                 wikibase: bool = True,
                 allow_split: bool = False,
                 move_together: bool = False,
                 keep_sortkey=None,
                 generator=None) -> None:
        """Store all given parameters in the objects attributes.

        :param oldcat: The move source.
        :param newcat: The move target.
        :param batch: If True the user has not to confirm the deletion.
        :param comment: The edit summary for all pages where the category is
            changed, and also for moves and deletions if not overridden.
        :param inplace: If True the categories are not reordered.
        :param move_oldcat: If True the category page (and talkpage) is
            copied to the new category.
        :param delete_oldcat: If True the oldcat page and talkpage are
            deleted (or nominated for deletion) if it is empty.
        :param title_regex: Only pages (and subcats) with a title that
            matches the regex are moved.
        :param history: If True the history of the oldcat is posted on
            the talkpage of newcat.
        :param pagesonly: If True only move pages, not subcategories.
        :param deletion_comment: Either string or special value:
            DELETION_COMMENT_AUTOMATIC: use a generated message,
            DELETION_COMMENT_SAME_AS_EDIT_COMMENT: use the same message for
            delete that is used for the edit summary of the pages whose
            category was changed (see the comment param above). If the value
            is not recognized, it's interpreted as DELETION_COMMENT_AUTOMATIC.
        :param move_comment: If set, uses this as the edit summary on the
            actual move of the category page. Otherwise, defaults to the value
            of the comment parameter.
        :param wikibase: If True, update the Wikibase item of the
            old category.
        :param allow_split: If False only moves page and talk page together.
        :param move_together: If True moves the pages/subcategories only if
            page and talk page could be moved or both source page and target
            page don't exist.
        :param generator: a generator from pagegenerators.GeneratorFactory.
            If given an intersection to the oldcat category members is used.
        """
        super().__init__()
        self.site = pywikibot.Site()
        self.can_move_cats = self.site.has_right('move-categorypages')
        self.noredirect = delete_oldcat \
            and self.site.has_right('suppressredirect')
        # Create attributes for the categories and their talk pages.
        self.oldcat = self._makecat(oldcat)
        self.oldtalk = self.oldcat.toggleTalkPage()

        if newcat:
            self.newcat: Optional[pywikibot.Category] = self._makecat(newcat)  # noqa: E501
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
        # if that page doesn't have a Wikibase
        self.wikibase = wikibase and self.site.has_data_repository
        self.allow_split = allow_split
        self.move_together = move_together
        self.keep_sortkey = keep_sortkey
        self.generator = generator

        if not self.can_move_cats:
            repo = self.site.data_repository()
            if self.wikibase and repo.username() is None:
                # The bot can't move categories nor update the Wikibase repo
                raise NoUsernameError(
                    "The 'wikibase' option is turned on and {} has no "
                    'registered username.'.format(repo))

        template_vars = {'oldcat': self.oldcat.title(with_ns=False)}
        if self.newcat:
            template_vars.update({
                'newcat': self.newcat.title(
                    with_ns=False,
                    as_link=True,
                    textlink=True
                ),
                'title': self.newcat.title(with_ns=False)})
        # Set edit summary for changed pages.
        if comment:
            self.comment = comment
        elif self.newcat:
            self.comment = i18n.twtranslate(self.site,
                                            'category-replacing',
                                            template_vars)
        else:
            self.comment = i18n.twtranslate(self.site,
                                            'category-removing',
                                            template_vars)
        # Set deletion reason for category page and talkpage.
        if isinstance(deletion_comment, str):
            # Deletion comment is set to given string.
            self.deletion_comment = deletion_comment
        elif deletion_comment == self.DELETION_COMMENT_SAME_AS_EDIT_COMMENT:
            # Use the edit comment as the deletion comment.
            self.deletion_comment = self.comment
        else:
            # Deletion comment is set to internationalized default.
            if self.newcat:
                # Category is moved.
                self.deletion_comment = i18n.twtranslate(self.site,
                                                         'category-was-moved',
                                                         template_vars)
            else:
                # Category is deleted.
                self.deletion_comment = i18n.twtranslate(
                    self.site, 'category-was-disbanded')
        self.move_comment = move_comment if move_comment else self.comment

    def run(self) -> None:
        """
        The main bot function that does all the work.

        For readability it is split into several helper functions:
        - _movecat()
        - _movetalk()
        - _hist()
        - _change()
        - _delete()

        .. versionchanged:: 8.0
           if a page generator is given to the bot, the intersection
           with :func:`pagegenerators.CategorizedPageGenerator` or
           :func:`pagegenerators.SubCategoriesPageGenerator` is used.
        """
        self._start_ts = pywikibot.Timestamp.now()
        # can_move_* determines if the page can be moved safely (target
        # doesn't exist but source does), move_items determines if the
        # items (pages/subcategories) of the category could be moved into
        # a new (non existent) category.
        can_move_page = CategoryMoveRobot.check_move(
            'category page', self.oldcat, self.newcat)
        can_move_talk = CategoryMoveRobot.check_move(
            'category talk page', self.oldtalk, self.newtalk)

        if not self.newcat:  # delete
            move_items = True
        else:
            move_items = not self.newcat.exists() or not self.move_together
            if not self.allow_split:
                can_move_page = can_move_page and move_items
                can_move_talk = can_move_talk and move_items

        if self.newcat and self.move_oldcat:
            if self.can_move_cats:
                if can_move_page:
                    old_cat_title = self.oldcat.title()
                    old_cat_text = self.oldcat.text
                    self.newcat = self.oldcat.move(self.newcat.title(),
                                                   reason=self.move_comment,
                                                   movetalk=can_move_talk,
                                                   noredirect=self.noredirect)
                    # Copy over the article text so it can be stripped of
                    # CFD templates and re-saved. This is faster than
                    # reloading the article in place.
                    self.newcat.text = old_cat_text
                    self._strip_cfd_templates()
                    self.oldcat = pywikibot.Category(self.oldcat.site,
                                                     old_cat_title)
            else:
                if can_move_page:
                    self._movecat()
                if can_move_talk:
                    self._movetalk()
                if self.wikibase:
                    self._update_wikibase_item()

            if self.history and can_move_page:
                self._hist()

        if move_items:
            gens = [pagegenerators.CategorizedPageGenerator(self.oldcat)]
            if not self.pagesonly:
                gens.append(
                    pagegenerators.SubCategoriesPageGenerator(self.oldcat))
            gen = chain(*gens)

            if self.generator:
                pywikibot.info('Retrieving intersection of generators.')
                # Allow duplicates if no subcategories are loaded to reduce
                # memory usage. We can assume that there are no duplicates
                # retrieved from CategorizedPageGenerator.
                gen = intersect_generators(gen, self.generator,
                                           allow_duplicates=self.pagesonly)
            self._change(gen)

        else:
            pywikibot.log("Didn't move pages/subcategories, because the "
                          "category page hasn't been moved.")

        if self.oldcat.isEmptyCategory() and self.delete_oldcat \
           and (self.newcat and self.move_oldcat or not self.newcat):
            self._delete(can_move_page, can_move_talk)

        self.exit()

    def _delete(self, moved_page, moved_talk) -> None:
        """Private function to delete the category page and its talk page.

        Do not use this function from outside the class. Automatically marks
        the pages if they can't be removed due to missing permissions.

        :param moved_page: Category page to delete
        :param moved_talk: Talk page to delete
        :type moved_page: pywikibot.page.BasePage
        :type moved_talk: pywikibot.page.BasePage

        """
        if moved_page and self.oldcat.exists():
            self.oldcat.delete(self.deletion_comment, not self.batch,
                               mark=True)
        self.counter['delete'] += 1
        if moved_talk and self.oldtalk.exists():
            self.oldtalk.delete(self.deletion_comment, not self.batch,
                                mark=True)
        self.counter['delete talk'] += 1

    def _change(self, gen) -> None:
        """
        Private function to move category contents.

        Do not use this function from outside the class.

        :param gen: Generator containing pages or categories.
        """
        for page in pagegenerators.PreloadingGenerator(gen):
            self.counter['read'] += 1
            count_key = 'move' if self.newcat else 'remove'

            if not self.title_regex or re.search(self.title_regex,
                                                 page.title()):

                page.change_category(self.oldcat, self.newcat,
                                     summary=self.comment,
                                     in_place=self.inplace,
                                     sort_key=self.keep_sortkey)
                self.counter[count_key] += 1

                doc_page = self.determine_template_target(page)
                if doc_page != page and (not self.title_regex
                                         or re.search(self.title_regex,
                                                      doc_page.title())):
                    doc_page.change_category(self.oldcat, self.newcat,
                                             summary=self.comment,
                                             in_place=self.inplace,
                                             include=self.includeonly,
                                             sort_key=self.keep_sortkey)
                    self.counter[count_key + ' talk'] += 1

    @staticmethod
    def check_move(name: str, old_page, new_page) -> bool:
        """Return if the old page can be safely moved to the new page.

        :param name: Title of the new page
        :param old_page: Page to be moved
        :type old_page: pywikibot.page.BasePage
        :param new_page: Page to be moved to
        :type new_page: pywikibot.page.BasePage
        :return: True if possible to move page, False if not page move
            not possible
        """
        move_possible = True
        if new_page and new_page.exists():
            pywikibot.warning("The {} target '{}' already exists."
                              .format(name, new_page.title()))
            move_possible = False
        if not old_page.exists():
            # only warn if not a talk page
            log = (pywikibot.log if old_page.namespace() % 2 else
                   pywikibot.warning)
            log("Moving {} '{}' requested, but the page doesn't exist."
                .format(name, old_page.title()))
            move_possible = False
        return move_possible

    def _movecat(self) -> None:
        """Private function to move the category page by copying its contents.

        Note that this method of moving category pages by copying over the raw
        text been deprecated by the addition of true category moving (analogous
        to page moving) in MediaWiki, and so the raw text method is no longer
        the default.

        Do not use this function from outside the class.
        """
        # Some preparing
        pywikibot.info('Moving text from {} to {}.'.format(
            self.oldcat.title(), self.newcat.title()))
        comma = self.site.mediawiki_message('comma-separator')
        authors = comma.join(self.oldcat.contributors().keys())
        template_vars = {'oldcat': self.oldcat.title(), 'authors': authors}
        summary = i18n.twtranslate(self.site, 'category-renamed',
                                   template_vars)
        self.newcat.text = self.oldcat.text
        self._strip_cfd_templates(summary)

    def _strip_cfd_templates(self, summary=None, commit: bool = True) -> None:
        """Private function to strip out CFD templates from the new category.

        The new category is saved.

        Do not use this function from outside the class.
        """
        # Remove all substed CFD templates
        self.newcat.text = CFD_TEMPLATE_REGEX.sub('', self.newcat.text)
        # Remove all language-specified, non substed CFD templates
        site_templates = i18n.translate(self.site, cfd_templates) or ()
        for template_name in site_templates:
            match = re.compile(r'{{%s.*?}}' % template_name, re.IGNORECASE)
            self.newcat.text = match.sub('', self.newcat.text)
        # Remove leading whitespace
        self.newcat.text = self.newcat.text.lstrip()
        if not summary:
            summary = i18n.twtranslate(self.site,
                                       'category-strip-cfd-templates')
        if commit:
            self.newcat.save(summary=summary)

    def _movetalk(self) -> None:
        """Private function to move the category talk page.

        Do not use this function from outside the class.
        """
        cat_name_only = self.newcat.title(with_ns=False)
        comment = i18n.twtranslate(self.site, 'category-was-moved',
                                   {'newcat': cat_name_only,
                                    'title': cat_name_only})
        self.oldtalk.move(self.newtalk.title(), comment)

    def _update_wikibase_item(self) -> None:
        """Private function to update the Wikibase item for the category.

        Do not use this function from outside the class.
        """
        if self.oldcat.exists():
            try:
                item = pywikibot.ItemPage.fromPage(self.oldcat)
            except NoPageError:
                item = None
            if item and item.exists():
                cat_name_only = self.newcat.title(with_ns=False)
                comment = i18n.twtranslate(self.site, 'category-was-moved',
                                           {'newcat': cat_name_only,
                                            'title': cat_name_only})
                item.setSitelink(self.newcat, summary=comment)

    def _hist(self) -> None:
        """Private function to copy the history of the to-be-deleted category.

        Do not use this function from outside the class. It adds a table with
        the history of the old category on the new talk page.
        """
        history = self.oldcat.getVersionHistoryTable()
        title = i18n.twtranslate(self.site, 'category-section-title',
                                 {'oldcat': self.oldcat.title()})
        self.newtalk.text = '{}\n== {} ==\n{}'.format(self.newtalk.text,
                                                      title, history)
        comment = i18n.twtranslate(self.site, 'category-version-history',
                                   {'oldcat': self.oldcat.title()})
        self.newtalk.save(comment)

    def _makecat(self, var) -> pywikibot.Category:
        """Private helper function to get a Category object.

        Checks if the instance given is a Category object and returns it.
        Otherwise creates a new object using the value as the title (for
        backwards compatibility).
        :param var: Either the title as a string or a Category object.
        """
        if not isinstance(var, pywikibot.Category):
            var = pywikibot.Category(self.site, var)
        return var


class CategoryListifyRobot:

    """Create a list containing all of the members in a category."""

    def __init__(self, cat_title: Optional[str], list_title: Optional[str],
                 edit_summary: str,
                 append: bool = False,
                 overwrite: bool = False,
                 show_images: bool = False, *,
                 talk_pages: bool = False,
                 recurse: Union[int, bool] = False,
                 namespaces=None,
                 **kwargs) -> None:
        """Initializer."""
        self.edit_summary = edit_summary
        self.append = append
        self.overwrite = overwrite
        self.show_images = show_images
        self.site = pywikibot.Site()
        if not cat_title:
            cat_title = pywikibot.input(
                'Please enter the name of the category to listify:')
        self.cat = pywikibot.Category(self.site, cat_title)
        if not list_title:
            list_title = pywikibot.input(
                'Please enter the name of the list to create:')
        self.list = pywikibot.Page(self.site, list_title)
        self.talk_pages = talk_pages
        self.recurse = recurse
        self.prefix = kwargs.pop('prefix', '*')
        self.namespaces = self.site.namespaces.resolve(namespaces or [])
        self.subcats = not self.namespaces or 'Category' in self.namespaces

    def run(self) -> None:
        """Start bot."""
        if self.list.exists() and not (self.append or self.overwrite):
            pywikibot.info('Page {} already exists, aborting.\n'
                           .format(self.list.title()))
            pywikibot.info(fill(
                'Use -append option to append the list to the output page or '
                '-overwrite option to overwrite the output page.'))
            return

        set_of_articles = set(self.cat.articles(recurse=self.recurse,
                                                namespaces=self.namespaces))
        if self.subcats:
            set_of_articles |= set(self.cat.subcategories())

        list_string = ''
        for article in sorted(set_of_articles):
            textlink = not (article.is_filepage() and self.show_images)
            list_string += '{} {}'.format(
                self.prefix, article.title(as_link=True, textlink=textlink))
            if self.talk_pages and not article.isTalkPage():
                list_string += ' -- [[{}|talk]]'.format(
                    article.toggleTalkPage().title())
            list_string += '\n'

        if self.list.text and self.append:
            # append content by default at the bottom
            list_string = self.list.text + '\n' + list_string
            pywikibot.info('Category list appending...')

        if not self.edit_summary:
            self.edit_summary = i18n.twtranslate(
                self.site, 'category-listifying',
                {'fromcat': self.cat.title(), 'num': len(set_of_articles)})
        self.list.put(list_string, summary=self.edit_summary)


class CategoryTidyRobot(Bot, CategoryPreprocess):
    """
    Robot to move members of a category into sub- or super-categories.

    Specify the category title on the command line. The robot will
    pick up the page, look for all sub- and super-categories, and show
    them listed as possibilities to move page into with an assigned
    number. It will ask you to type number of the appropriate
    replacement, and performs the change robotically. It will then
    automatically loop over all pages in the category.

    If you don't want to move the member to a sub- or super-category,
    but to another category, you can use the 'j' (jump) command.

    By typing 's' you can leave the complete page unchanged.

    By typing 'm' you can show more content of the current page,
    helping you to find out what the page is about and in which other
    categories it currently is.

    :param cat_title: a title of the category to process.
    :param cat_db: a CategoryDatabase object.
    :type cat_db: CategoryDatabase object
    :param namespaces: namespaces to focus on.
    :type namespaces: iterable of pywikibot.Namespace
    :param comment: a custom summary for edits.
    """

    def __init__(self, cat_title: Optional[str], cat_db, namespaces=None,
                 comment: Optional[str] = None) -> None:
        """Initializer."""
        self.cat_title = cat_title or pywikibot.input(
            'Which category do you want to tidy up?')
        self.cat_db = cat_db
        self.edit_summary = comment
        if not comment:
            self.template_vars = {'oldcat': self.cat_title}

        site = pywikibot.Site()
        self.cat = pywikibot.Category(site, self.cat_title)
        super().__init__(generator=pagegenerators.PreloadingGenerator(
            self.cat.articles(namespaces=namespaces)))

    def move_to_category(self,
                         member: pywikibot.Page,
                         original_cat: pywikibot.Category,
                         current_cat: pywikibot.Category) -> None:
        """
        Ask whether to move it to one of the sub- or super-categories.

        Given a page in the original_cat category, ask the user whether
        to move it to one of original_cat's sub- or super-categories.
        Recursively run through subcategories' subcategories.

        .. note:: current_cat is only used for internal recursion. You
           should always use ``current_cat = original_cat``.

        :param member: a page to process.
        :param original_cat: original category to replace.
        :param current_cat: a category which is questioned.
        """
        class CatContextOption(ContextOption):
            """An option to show more and more context and categories."""

            @property
            def out(self) -> str:
                """Create a section and categories from the text."""
                start = max(0, self.start - self.context)
                end = min(len(self.text), self.end + self.context)
                text = self.text[start:end] + '...'

                # if categories weren't visible, show them additionally
                if len(self.text) > end:
                    for cat in member.categories():
                        if cat != original_cat:
                            text += cat.title(as_link=True)
                        else:
                            text += '<<lightpurple>>{}<<default>>'.format(
                                current_cat.title(as_link=True))
                        text += '\n'
                return text

        class CatIntegerOption(IntegerOption):
            """An option allowing a range of integers."""

            @staticmethod
            def list_categories(cat_list, prefix: str = '') -> None:
                """Output categories in one or two columns.

                Determine whether the list contains long or short
                category titles and output category titles as enumerated
                options.

                :param cat_list: sorted iterable of category titles to output.
                :type cat_list: iterable of str
                :param prefix: a prefix to assigned number index.
                """
                # can we can output in two columns?
                count = len(cat_list)
                if count > 1 and len(max(cat_list, key=len)) <= 31:
                    new_column = int(math.ceil(count / 2.0))
                else:
                    new_column = 0

                # determine number format
                index = '%2d' if count > 9 else '%d'

                lines = []
                for i, cat in enumerate(cat_list):
                    if new_column:
                        if i == new_column:
                            break
                        # columnify
                        i2 = i + new_column
                        if i2 < count:
                            lines.append('[{0}{1}] {2:35}[{0}{3}] {4}'
                                         .format(prefix, index % i, cat,
                                                 index % i2, cat_list[i2]))
                        else:
                            lines.append('[{}{}] {}'.format(
                                prefix, index % i, cat))
                    else:
                        lines.append('[{}{}] {}'.format(
                            prefix, index % i, cat))

                # output the result
                for line in lines:
                    pywikibot.info(line)

        # show the title of the page where the link was found.
        pywikibot.info('\n>>> <<lightpurple>>{}<<default>> <<<'
                       .format(member.title()))

        # determine a reasonable amount of context.
        try:
            full_text = member.get()
        except NoPageError:
            pywikibot.info(f'Page {member.title()} not found.')
            return

        # skip initial templates, images and comments for articles.
        if member.namespace() == member.site.namespaces.MAIN:
            excludes = ('template', 'file', 'comment')
            regexes = textlib._get_regexes(excludes, member.site)
            i = 0
            while i < 3:
                i = 0
                for reg in regexes:
                    if reg.match(full_text):
                        full_text = reg.sub(r'', full_text, count=1).lstrip()
                    else:
                        i += 1

        # output context
        context_option = CatContextOption('show more context', 'm', full_text,
                                          500, 500)
        context_option.output()

        # get super- and sub-categories
        # sort them to assign expectable numbers
        supercatlist = sorted(self.cat_db.get_supercats(current_cat),
                              key=methodcaller('title'))
        subcatlist = sorted(self.cat_db.get_subcats(current_cat),
                            key=methodcaller('title'))

        # show categories as possible choices with numbers
        pywikibot.info()
        supercat_option = CatIntegerOption(0, len(supercatlist), 'u')
        if not supercatlist:
            pywikibot.info('This category has no supercategories.')
        else:
            pywikibot.info('Move up to category:')
            cat_list = [cat.title(
                with_ns=False) for cat in supercatlist]
            supercat_option.list_categories(cat_list, 'u')

        subcat_option = CatIntegerOption(0, len(subcatlist))
        if not subcatlist:
            pywikibot.info('This category has no subcategories.')
        else:
            pywikibot.info('Move down to category:')
            cat_list = [cat.title(with_ns=False) for cat in subcatlist]
            subcat_option.list_categories(cat_list)

        # show possible options for the user
        pywikibot.info()
        options = (supercat_option,
                   subcat_option,
                   StandardOption(
                       'save page to category <<lightpurple>>{}<<default>>'
                       .format(current_cat.title(with_ns=False)), 'c'),
                   StandardOption('remove the category from page', 'r'),
                   StandardOption('skip page', 's'),
                   context_option,
                   StandardOption('jump to custom category', 'j'))
        choice = pywikibot.input_choice(
            'Choice for page <<lightpurple>>{}<<default>>:'
            .format(member.title()), options, default='c')

        if choice == 'c':
            pywikibot.info(f'Saving page to {current_cat.title()}')
            if current_cat == original_cat:
                pywikibot.info('No changes necessary.')
            else:
                if not self.edit_summary:
                    self.template_vars.update({
                        'newcat': current_cat.title(
                            as_link=True, textlink=True)
                    })
                    self.edit_summary = i18n.twtranslate(self.site,
                                                         'category-replacing',
                                                         self.template_vars)
                # change the category tag
                member.change_category(original_cat, current_cat,
                                       summary=self.edit_summary)
                doc_page = self.determine_template_target(member)
                if doc_page != member:
                    doc_page.change_category(original_cat, current_cat,
                                             include=self.includeonly,
                                             summary=self.edit_summary)

        elif choice == 'j':
            new_cat_title = pywikibot.input('Please enter the category '
                                            'the page should be moved to:',
                                            default=None)  # require an answer
            new_cat = pywikibot.Category(pywikibot.Link('Category:'
                                                        + new_cat_title))
            # recurse into chosen category
            self.move_to_category(member, original_cat, new_cat)

        elif choice == 'r':
            if not self.edit_summary:
                self.edit_summary = i18n.twtranslate(self.site,
                                                     'category-removing',
                                                     self.template_vars)
            # remove the category tag
            member.change_category(original_cat, None,
                                   summary=self.edit_summary)
            doc_page = self.determine_template_target(member)
            if doc_page != member:
                doc_page.change_category(original_cat, None,
                                         include=self.includeonly,
                                         summary=self.edit_summary)

        elif choice != 's':
            if choice[0] == 'u':
                # recurse into supercategory
                self.move_to_category(member, original_cat,
                                      supercatlist[choice[1]])
            elif choice[0] == '':
                # recurse into subcategory
                self.move_to_category(member, original_cat,
                                      subcatlist[choice[1]])

    def teardown(self) -> None:
        """Cleanups after run operation."""
        if self.generator_completed and not self.counter['read']:
            pywikibot.info(
                f'There are no pages or files in category {self.cat_title}.')

    def treat(self, page) -> None:
        """Process page."""
        pywikibot.info()
        self.move_to_category(page, self.cat, self.cat)


class CategoryTreeRobot:

    """Robot to create tree overviews of the category structure.

    Parameters:
        * cat_title - The category which will be the tree's root.
        * cat_db    - A CategoryDatabase object.
        * max_depth - The limit beyond which no subcategories will be listed.
                     This also guarantees that loops in the category structure
                     won't be a problem.
        * filename - The textfile where the tree should be saved; None to print
                     the tree to stdout.
    """

    def __init__(
        self,
        cat_title,
        cat_db,
        filename=None,
        max_depth: int = 10
    ) -> None:
        """Initializer."""
        self.cat_title = cat_title or \
            pywikibot.input(
                'For which category do you want to create a tree view?')
        self.cat_db = cat_db
        if filename is None:
            filename = pywikibot.input(
                'Please enter the name of the file '
                'where the tree should be saved,\n'
                'or press enter to simply show the tree:')
        if filename and not os.path.isabs(filename):
            filename = config.datafilepath(filename)
        self.filename = filename
        self.max_depth = max_depth
        self.site = pywikibot.Site()

    def treeview(self, cat, current_depth: int = 0, parent=None) -> str:
        """Return a tree view of all subcategories of cat.

        The multi-line string contains a tree view of all subcategories of cat,
        up to level max_depth. Recursively calls itself.

        Parameters:
            * cat - the Category of the node we're currently opening.
            * current_depth - the current level in the tree (for recursion).
            * parent - the Category of the category we're coming from.

        """
        result = '#' * current_depth
        if current_depth > 0:
            result += ' '
        result += cat.title(as_link=True, textlink=True, with_ns=False)
        result += ' ({})'.format(int(cat.categoryinfo['pages']))
        if current_depth < self.max_depth // 2:
            # noisy dots
            pywikibot.info('.', newline=False)
        # Create a list of other cats which are supercats of the current cat
        supercat_names = [super_cat.title(as_link=True,
                                          textlink=True,
                                          with_ns=False)
                          for super_cat in self.cat_db.get_supercats(cat)
                          if super_cat != parent]

        if supercat_names:
            # print this list, separated with commas, using translations
            # given in 'category-also-in'
            comma = self.site.mediawiki_message('comma-separator')
            result += ' ' + i18n.twtranslate(self.site, 'category-also-in',
                                             {'alsocat': comma.join(
                                                 supercat_names)})
        del supercat_names
        result += '\n'
        if current_depth < self.max_depth:
            for subcat in self.cat_db.get_subcats(cat):
                # recurse into subdirectories
                result += self.treeview(subcat, current_depth + 1, parent=cat)
        elif self.cat_db.get_subcats(cat):
            # show that there are more categories beyond the depth limit
            result += '#' * (current_depth + 1) + ' [...]\n'
        return result

    def run(self) -> None:
        """Handle the multi-line string generated by treeview.

        After string was generated by treeview it is either printed to the
        console or saved it to a file.
        """
        cat = pywikibot.Category(self.site, self.cat_title)
        pywikibot.info('Generating tree...', newline=False)
        tree = self.treeview(cat)
        pywikibot.info()
        if self.filename:
            pywikibot.info('Saving results in ' + self.filename)
            with codecs.open(self.filename, 'a', 'utf-8') as f:
                f.write(tree)
        else:
            pywikibot.stdout(tree)


class CleanBot(Bot):

    """Automatically cleans up specified category.

    Removes redundant grandchildren from specified category by
    removing direct link to grandparent.

    In another words a grandchildren should not be also a children.

    Stubs categories are exception.

    .. note:: For details please read:

       - https://en.wikipedia.org/wiki/WP:SUBCAT

       - https://en.wikipedia.org/wiki/WP:DIFFUSE

    .. versionadded:: 7.0
    """

    update_options = {
        'recurse': False
    }

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        site = pywikibot.Site()
        cat = kwargs.pop('from', None)
        if not cat:
            cat = pywikibot.input(
                'Please enter the name of the category to clean:')
        self.cat = pywikibot.Category(site, cat)
        self.subcats = set(self.cat.subcategories())
        self.children = self.subcats | set(self.cat.articles())
        # Using sorted for reproducible data sequence
        super().__init__(generator=pagegenerators.PreloadingGenerator(
            sorted(self.subcats)), **kwargs)

    def skip_page(self, cat) -> bool:
        """Check whether the category should be processed."""
        return cat.title().endswith('stubs')

    def treat(self, child) -> None:
        """Process the category."""
        grandchildren = set(child.articles(recurse=self.opt.recurse))
        # For advanced usage uncomment the next line to
        # check not only grandchildren articles but
        # grandchildren categories too:
        # grandchildren |= set(child.subcategories(self.opt.recurse))
        overcategorized = sorted(grandchildren & self.children)
        if not overcategorized:
            return

        if config.verbose_output:
            pywikibot.info('Subcategory "{}" is parent for:'
                           .format(child.title(with_ns=False)))

            for grandchild in overcategorized:
                pywikibot.info(f'\t{grandchild.title()}')

        for grandchild in overcategorized:
            msg = ('Remove "<<lightpurple>>{}<<default>>" from "{}" because '
                   'it is already under subcategory "<<green>>{}<<default>>"?'
                   .format(grandchild.title(with_ns=False),
                           self.cat.title(with_ns=False),
                           child.title(with_ns=False)))

            if not self.user_confirm(msg):
                continue

            opts = {'as_link': True, 'textlink': True}
            summary = i18n.twtranslate(grandchild.site, 'category-clean',
                                       {'category': self.cat.title(**opts),
                                        'child': child.title(**opts)})
            grandchild.change_category(self.cat, None, summary)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments.
    """
    options = {}
    # TODO: use options instead following variables:
    batch = False
    summary = ''
    inplace = False
    append = False
    overwrite = False
    showimages = False
    talkpages = False
    title_regex = None
    pagesonly = False
    wikibase = True
    history = False
    rebuild = False
    allow_split = False
    move_together = False
    keep_sortkey = None
    depth = 5

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)

    # When this is True then the custom edit summary given for removing
    # categories from articles will also be used as the deletion reason.
    # Otherwise it will generate deletion specific comments.
    use_deletion_summary = True
    action = None
    sort_by_last_name = False
    create_pages = False
    follow_redirects = False
    delete_empty_cat = True
    unknown = []
    pg_options = []
    for arg in local_args:
        if arg in ('add', 'remove', 'move', 'tidy', 'tree', 'listify',
                   'clean'):
            action = arg
            continue

        if arg[0] != '-':
            unknown.append(arg)
            continue

        option, _, value = arg[1:].partition(':')
        if option == 'nodelete':
            delete_empty_cat = False
        elif option == 'person':
            sort_by_last_name = True
        elif option == 'rebuild':
            rebuild = True
        elif option in ('from', 'to'):
            options[option] = value.replace('_', ' ')
        elif option == 'batch':
            batch = True
        elif option == 'inplace':
            inplace = True
        elif option == 'nodelsum':
            use_deletion_summary = False
        elif option == 'append':
            append = True
        elif option == 'overwrite':
            overwrite = True
        elif option == 'showimages':
            showimages = True
        elif option == 'summary':
            summary = value
        elif option == 'match':
            title_regex = value or pywikibot.input(
                'Which regular expression should affected objects match?')
        elif option == 'talkpages':
            talkpages = True
        elif option == 'recurse':
            options[option] = True if value == '' else int(value)
        elif option == 'pagesonly':
            pagesonly = True
        elif option == 'nowb':
            wikibase = False
        elif option == 'allowsplit':
            allow_split = True
        elif option == 'mvtogether':
            move_together = True
        elif option == 'create':
            create_pages = True
        elif option == 'redirect':
            follow_redirects = True
        elif option == 'hist':
            history = True
        elif option == 'depth':
            depth = int(value)
        elif option == 'keepsortkey':
            keep_sortkey = True
        elif option == 'prefix':
            options[option] = value
        elif option == 'always':
            options[option] = True
        else:
            pg_options.append(arg)

    enabled = ['namespace'] if action in ('tidy', 'listify') else None
    if action in ('add', 'listify', 'move', 'remove', 'tidy'):
        gen_factory = pagegenerators.GeneratorFactory(enabled_options=enabled)
        unknown += gen_factory.handle_args(pg_options)
    else:
        unknown += pg_options
    suggest_help(unknown_parameters=unknown)

    cat_db = CategoryDatabase(rebuild=rebuild)

    if action == 'add':
        gen = gen_factory.getCombinedGenerator(preload=True)
        if not gen:
            # default for backwards compatibility
            gen_factory.handle_arg('-links')
            gen = gen_factory.getCombinedGenerator(preload=True)
        bot = CategoryAddBot(gen,
                             newcat=options.get('to'),
                             sort_by_last_name=sort_by_last_name,
                             create=create_pages,
                             comment=summary,
                             follow_redirects=follow_redirects)
    elif action == 'remove':
        if 'from' not in options:
            options['from'] = \
                pywikibot.input('Please enter the name of the '
                                'category that should be removed:')
        gen = gen_factory.getCombinedGenerator()
        bot = CategoryMoveRobot(oldcat=options.get('from'),
                                batch=batch,
                                comment=summary,
                                inplace=inplace,
                                delete_oldcat=delete_empty_cat,
                                title_regex=title_regex,
                                history=history,
                                pagesonly=pagesonly,
                                deletion_comment=use_deletion_summary,
                                generator=gen)
    elif action == 'move':
        if 'from' not in options:
            options['from'] = pywikibot.input(
                'Please enter the old name of the category:')
        if 'to' not in options:
            options['to'] = pywikibot.input(
                'Please enter the new name of the category:')
        if use_deletion_summary:
            deletion_comment = \
                CategoryMoveRobot.DELETION_COMMENT_SAME_AS_EDIT_COMMENT
        else:
            deletion_comment = CategoryMoveRobot.DELETION_COMMENT_AUTOMATIC
        gen = gen_factory.getCombinedGenerator()
        bot = CategoryMoveRobot(oldcat=options.get('from'),
                                newcat=options.get('to'),
                                batch=batch,
                                comment=summary,
                                inplace=inplace,
                                delete_oldcat=delete_empty_cat,
                                title_regex=title_regex,
                                history=history,
                                pagesonly=pagesonly,
                                deletion_comment=deletion_comment,
                                wikibase=wikibase,
                                allow_split=allow_split,
                                move_together=move_together,
                                keep_sortkey=keep_sortkey,
                                generator=gen)
    elif action == 'tidy':
        bot = CategoryTidyRobot(options.get('from'), cat_db,
                                gen_factory.namespaces, summary)
    elif action == 'tree':
        bot = CategoryTreeRobot(options.get('from'), cat_db,
                                options.get('to'), depth)
    elif action == 'listify':
        bot = CategoryListifyRobot(options.get('from'),
                                   options.get('to'), summary,
                                   append, overwrite, showimages,
                                   talk_pages=talkpages,
                                   recurse=options.get('recurse', False),
                                   namespaces=gen_factory.namespaces,
                                   **options)
    elif action == 'clean':
        bot = CleanBot(**options)

    if not suggest_help(missing_action=not action):
        pywikibot.Site().login()
        try:
            bot.run()
        except Error:
            pywikibot.exception('Fatal error:')
        finally:
            if cat_db:
                cat_db.dump()


if __name__ == '__main__':
    main()
