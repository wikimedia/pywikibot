#!/usr/bin/python
"""
Bot to add new or existing categories to pages.

This bot takes as its argument the name of a new or existing category.
Multiple categories may be given. It will then try to find new articles
for these categories (pages linked to and from pages already in the category),
asking the user which pages to include and which not.

The following command line parameters are supported:

-nodates     Automatically skip all pages that are years or dates
             (years only work AD, dates only for certain languages).

-forward     Only check pages linked from pages already in the category,
             not pages linking to them. Is less precise but quite a bit faster.

-exist       Only ask about pages that do actually exist;
             drop any titles of non-existing pages silently.
             If -forward is chosen, -exist is automatically implied.

-keepparent  Do not remove parent categories of the category to be worked on.

-all         Work on all pages (default: only main namespace)

When running the bot, you will get one by one a number by pages.
You can choose with small menu bar:

* [y]es      - include the page
* [n]o       - do not include the page or
* [i]gnore   - do not include the page, but if you meet it again, ask again.
* [e]xtend   - extend menu bar
* [h]elp     - show options to be choosed
* [q]uit     - leave the bot

Other possibilities with extended menu bar:

* [m]ore     - show more content of the page starting from the beginning
* sort [k]ey - add with sort key like [[Category|Title]]
* [s]kip     - add the page, but skip checking links to and from it
* [c]heck    - check links to and from the page, but do not add the page itself
* [o]ther    - add another page, which may have been included before
* [l]ist     - show current list of pages to include or to check
* [r]educe   - reduce menu bar

"""
# (C) Pywikibot team, 2004-2020
#
# Distributed under the terms of the MIT license.
#
import codecs
from itertools import chain
from textwrap import fill

import pywikibot
from pywikibot import i18n, pagegenerators, textlib
from pywikibot.bot import NoRedirectPageBot, SingleSiteBot
from pywikibot.exceptions import Error
from pywikibot.tools import DequeGenerator
from pywikibot.tools.formatter import color_format


class MakeCatBot(SingleSiteBot, NoRedirectPageBot):

    """Bot tries to find new articles for a given category."""

    def __init__(self, **kwargs):
        """Initializer."""
        self.available_options.update({
            'all': False,
            'catnames': None,
            'exist': False,
            'forward': False,
            'keepparent': False,
            'nodate': False,
            'summary': None,
        })
        super().__init__(**kwargs)
        self.skipdates = self.opt.nodate
        self.checkbackward = not self.opt.forward
        self.checkbroken = not (self.opt.forward and self.opt.exist)
        self.removeparent = not self.opt.keepparent
        self.main = not self.opt.all
        self.tocheck = DequeGenerator()

        self.workingcatname = self.opt.catnames
        self._setup_menubar()

    @classmethod
    def _setup_menubar(cls):
        """Setup treat_page option bar."""
        small = [
            ('yes', 'y'), ('no', 'n'), ('ignore', 'i'),
            ('extend', 'e'), ('help', 'h')]
        extended = small[:3] + [
            ('more', 'm'), ('sort key', 'k'), ('skip', 's'), ('check', 'c'),
            ('other', 'o'), ('list', 'l'), ('reduce', 'r'), ('help', 'h')]
        cls.option_bar = {'e': extended, 'r': small}
        cls.treat_options = cls.option_bar['r']

    @property
    def generator(self):
        """Generator property used by run()."""
        return pagegenerators.DequePreloadingGenerator(self.tocheck)

    @staticmethod
    def highlight_title(page, condition=True):
        """Highlight a page title if conditon is True."""
        if condition:
            pywikibot.output(
                color_format('\n>>> {lightpurple}{0}{default} <<<',
                             page.title()))

    @staticmethod
    def print_dot(condition=True):
        """Print a single dot if conditon is True."""
        if condition:
            pywikibot.output('.', newline=False)

    def needcheck(self, page):
        """Verify whether the current page may be processed."""
        global checked
        return not (self.main and page.namespace() != 0
                    or page in checked
                    or self.skipdates and page.autoFormat()[0] is not None)

    def change_category(self, page, categories):
        """Change the category of page."""
        global workingcat, parentcats
        for category in categories:
            if self.removeparent and category in parentcats:
                page.change_category(workingcat, summary=self.opt.summary)
                return True
        return False

    def include(self, page, checklinks=True, realinclude=True, linkterm=None):
        """Include the current page to the working category."""
        global workingcat, parentcats
        global checked
        actualworkingcat = workingcat
        if linkterm:
            actualworkingcat.sortKey = linkterm
        if realinclude and page.exists():
            if page.isRedirectPage():
                checklinks = True
            else:
                cats = list(page.categories())
                if workingcat not in cats \
                   and not self.change_category(page, cats):
                    newtext = textlib.replaceCategoryLinks(
                        page.text, cats + [actualworkingcat],
                        site=page.site)
                    page.put(newtext, summary=self.opt.summary)

        if checklinks:
            self.checklinks(page)

    def checklinks(self, page):
        """Check whether the page has to be added to the tocheck deque."""
        global checked
        pywikibot.output('\nChecking links for "{}"...'
                         .format(page.title()), newline=False)
        generators = [page.linkedPages()]
        if self.checkbackward:
            generators.append(page.getReferences())
        for i, linked_page in enumerate(chain(*generators)):
            self.print_dot(not i % 25)
            if self.needcheck(linked_page):
                self.tocheck.append(linked_page)
                checked.add(linked_page)

    def init_page(self, page):
        """Add redirect targets to check list."""
        global checked
        super().init_page(page)
        if page.isRedirectPage():
            newpage = page.getRedirectTarget()
            if self.needcheck(newpage):
                self.tocheck.append(newpage)
                checked.add(newpage)

    def skip_page(self, page):
        """Check whether the page is to be skipped."""
        if not self.checkbroken and not page.exists():
            pywikibot.warning('Page {page} does not exist on {page.site}. '
                              'Skipping.'.format(page=page))
            return True
        return super().skip_page(page)

    def treat_page(self):
        """Work on current page and ask to add article to category."""
        global checked
        global excludefile
        pl = self.current_page
        ctoshow = 500
        pywikibot.output('')
        pywikibot.output('== {} =='.format(pl.title()))
        while True:
            answer = pywikibot.input_choice(
                'Add to category {}?'.format(self.workingcatname),
                self.treat_options, default='i')
            if answer == 'y':
                self.include(pl)
                break
            if answer == 'c':
                self.include(pl, realinclude=False)
                break
            if answer == 'k':
                if pl.exists() and not pl.isRedirectPage():
                    linkterm = pywikibot.input(
                        'In what manner should it be alphabetized?')
                    self.include(pl, linkterm=linkterm)
                    break
                self.include(pl)
                break
            if answer == 'n':
                excludefile.write('{}\n'.format(pl.title()))
                break
            if answer == 'i':
                break
            if answer in 'er':
                self.treat_options = self.option_bar[answer]
            elif answer == 'h':
                pywikibot.output("""
[y]es:      Add the page and check links')
[n]o:       Never add the page, saved to exclusion list
[i]gnore:   Neither do not add the page not check links
[m]ore:     show more content of the page starting from the beginning
sort [k]ey: Add with sort key like [[Category|Title]]
[s]kip:     Add the page, but skip checking links
[c]heck:    Do not add the page, but do check links
[o]ther:    Add another page
[l]ist:     Show a list of the pages to check
[e]xtend:   A more extended option list
[r]educe:   Reduce option list
[q]uit:     Save exclusion list and exit this script
""")
            elif answer == 'o':
                pagetitle = pywikibot.input('Specify page to add:')
                page = pywikibot.Page(pywikibot.Site(), pagetitle)
                if page not in checked:
                    self.include(page)
            elif answer == 's':
                if not pl.exists():
                    pywikibot.output('Page does not exist; not added.')
                elif pl.isRedirectPage():
                    pywikibot.output(
                        'Redirect page. Will be included normally.')
                    self.include(pl, realinclude=False)
                else:
                    self.include(pl, checklinks=False)
                break
            elif answer == 'l':
                length = len(self.tocheck)
                pywikibot.output('Number of pages still to check: {}'
                                 .format(length))
                if length:
                    pywikibot.output('Pages to be checked:')
                    pywikibot.output(
                        fill(' - '.join(page.title()
                                        for page in self.tocheck)))
                self.highlight_title(page)
            elif answer == 'm':
                self.highlight_title(pl, ctoshow > 500)
                if pl.exists():
                    pywikibot.output(pl.text[0:ctoshow])
                else:
                    pywikibot.output('Page does not exist.')
                ctoshow += 500


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    global workingcat, parentcats
    global checked
    global excludefile

    checked = set()

    workingcatname = ''

    options = {}
    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        option = arg[1:]
        if not arg.startswith('-'):
            if not workingcatname:
                options['catnames'] = workingcatname = arg
            else:
                pywikibot.warning('Working category "{}" is already given.'
                                  .format(workingcatname))
        else:
            options[option] = True

    if not workingcatname:
        pywikibot.bot.suggest_help(missing_parameters=['working category'])
        return

    mysite = pywikibot.Site()
    summary = i18n.twtranslate(mysite, 'makecat-create',
                               {'cat': workingcatname})

    bot = MakeCatBot(site=mysite, summary=summary, **options)

    workingcat = pywikibot.Category(mysite, '{}{}'
                                            .format(mysite.namespaces.CATEGORY,
                                                    workingcatname))
    filename = pywikibot.config.datafilepath(
        'category',
        workingcatname.encode('ascii', 'xmlcharrefreplace').decode('ascii')
        + '_exclude.txt')
    try:
        with codecs.open(filename, 'r', encoding=mysite.encoding()) as f:
            for line in f.readlines():
                # remove leading and trailing spaces, LF and CR
                line = line.strip()
                if not line:
                    continue
                pl = pywikibot.Page(mysite, line)
                checked.add(pl)

        excludefile = codecs.open(filename, 'a', encoding=mysite.encoding())
    except IOError:
        # File does not exist
        excludefile = codecs.open(filename, 'w', encoding=mysite.encoding())

    # Get parent categories in order to `removeparent`
    try:
        parentcats = workingcat.categories()
    except Error:
        parentcats = []

    # Do not include articles already in subcats; only checking direct subcats
    subcatlist = list(workingcat.subcategories())
    if subcatlist:
        subcatlist = pagegenerators.PreloadingGenerator(subcatlist)
        for cat in subcatlist:
            artlist = list(cat.articles())
            for page in artlist:
                checked.add(page)

    # Fetch articles in category, and mark as already checked (seen)
    # If category is empty, ask user if they want to look for pages
    # in a different category.
    articles = list(workingcat.articles(content=True))
    if not articles:
        pywikibot.output('Category {} does not exist or is empty. '
                         'Which page to start with?'
                         .format(workingcatname))
        answer = pywikibot.input('(Default is [[{}]]):'.format(workingcatname))
        if not answer:
            answer = workingcatname
        pywikibot.output('' + answer)
        pl = pywikibot.Page(mysite, answer)
        articles = [pl]

    for pl in articles:
        checked.add(pl)
        bot.include(pl)

    bot.run()


if __name__ == '__main__':
    try:
        main()
    finally:
        try:
            excludefile.close()
        except Exception:
            pass
