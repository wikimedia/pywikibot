#!/usr/bin/env python3
"""This bot will move pages out of redirected categories.

The bot will look for categories that are marked with a category redirect
template, take the first parameter of the template as the target of the
redirect, and move all pages and subcategories of the category there. It
also changes hard redirects into soft redirects, and fixes double redirects.
A log is written under <userpage>/category_redirect_log. Only category pages
that haven't been edited for a certain cooldown period (currently 7 days)
are taken into account.

The following parameters are supported:

-always           If used, the bot won't ask if it should add the specified
                  text

-delay:#          Set an amount of days. If the category is edited more recenty
                  than given days, ignore it. Default is 7.

-tiny             Only loops over Category:Non-empty_category_redirects and
                  moves all images, pages and categories in redirect categories
                  to the target category.

Usage:

    python pwb.py category_redirect [options]

.. note:: This script is a
   :py:obj:`ConfigParserBot <bot.ConfigParserBot>`. All options
   can be set within a settings file which is scripts.ini by default.
"""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import pickle
import re
import time
from contextlib import suppress
from datetime import timedelta

import pywikibot
from pywikibot import config, i18n, pagegenerators
from pywikibot.backports import Tuple, removeprefix
from pywikibot.bot import ConfigParserBot, SingleSiteBot
from pywikibot.exceptions import CircularRedirectError, Error, NoPageError


LOG_SIZE = 7  # Number of items to keep in active log


class CategoryRedirectBot(ConfigParserBot, SingleSiteBot):

    """Page category update bot.

    .. versionchanged:: 7.0
       CategoryRedirectBot is a ConfigParserBot
    """

    update_options = {
        'tiny': False,  # use Non-empty category redirects only
        'delay': 7,  # cool down delay in days
    }

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        self.catprefix = self.site.namespace(14) + ':'
        self.log_text = []
        self.edit_requests = []
        self.problems = []
        self.template_list = []
        self.cat = None
        self.log_page = pywikibot.Page(self.site,
                                       'User:{}/category redirect log'
                                       .format(self.site.username()))

        # Localization:

        # Category that contains all redirected category pages
        self.cat_redirect_cat = {
            'commons': 'Category:Category redirects',
            'meta': 'Category:Maintenance of categories/Soft redirected '
                    'categories',
            'ar': 'تصنيف:تحويلات تصنيفات ويكيبيديا',
            'ary': 'تصنيف:Wikipedia soft redirected categories',
            'arz': 'تصنيف:تحويلات تصانيف ويكيبيديا',
            'cs': 'Kategorie:Údržba:Zastaralé kategorie',
            'da': 'Kategori:Omdirigeringskategorier',
            'en': 'Category:Wikipedia soft redirected categories',
            'es': 'Categoría:Wikipedia:Categorías redirigidas',
            'fa': 'رده:رده‌های منتقل‌شده',
            'hi': 'श्रेणी:विकिपीडिया श्रेणी अनुप्रेषित',
            'hu': 'Kategória:Kategóriaátirányítások',
            'ja': 'Category:移行中のカテゴリ',
            'ko': '분류:비어 있지 않은 분류 넘겨주기',
            'no': 'Kategori:Wikipedia omdirigertekategorier',
            'pl': 'Kategoria:Przekierowania kategorii',
            'pt': 'Categoria:!Redirecionamentos de categorias',
            'sco': 'Category:Wikipaedia soft redirectit categories',
            'simple': 'Category:Category redirects',
            'sh': 'Kategorija:Preusmjerene kategorije Wikipedije',
            'sr': 'Категорија:Википедијине меко преусмерене категорије',
            'ur': 'زمرہ:منتقل شدہ زمرہ جات',
            'vi': 'Thể loại:Thể loại đổi hướng',
            'zh': 'Category:已重定向的分类',
            'ro': 'Categorie:Categorii de redirecționare',
        }

        # Category that contains non-empty redirected category pages
        self.tiny_cat_redirect_cat = 'Q8099903'

        self.move_comment = 'category_redirect-change-category'
        self.redir_comment = 'category_redirect-add-template'
        self.dbl_redir_comment = 'category_redirect-fix-double'
        self.maint_comment = 'category_redirect-comment'
        self.edit_request_text = i18n.twtranslate(
            self.site, 'category_redirect-edit-request') + '\n~~~~'
        self.edit_request_item = i18n.twtranslate(
            self.site, 'category_redirect-edit-request-item')

    def get_cat(self):
        """Specify the category page."""
        if self.opt.tiny:
            self.cat = self.site.page_from_repository(
                self.tiny_cat_redirect_cat)
        else:
            cat_title = pywikibot.translate(self.site, self.cat_redirect_cat)
            if cat_title:
                self.cat = pywikibot.Category(pywikibot.Link(cat_title,
                                                             self.site))
        return self.cat is not None

    def move_contents(self, old_cat_title: str, new_cat_title: str,
                      edit_summary: str) -> Tuple[int, int]:
        """The worker function that moves pages out of oldCat into newCat."""
        old_cat = pywikibot.Category(self.site, self.catprefix + old_cat_title)
        new_cat = pywikibot.Category(self.site, self.catprefix + new_cat_title)

        param = {
            'oldCatLink': old_cat.title(),
            'oldCatTitle': old_cat_title,
            'newCatLink': new_cat.title(),
            'newCatTitle': new_cat_title,
        }
        summary = edit_summary % param

        # Move articles
        found, moved = 0, 0
        for article in old_cat.members():
            found += 1
            moved += article.change_category(old_cat, new_cat, summary=summary)

            if article.namespace() != 10:
                continue

            # pass 2: look for template doc pages
            for subpage in self.site.doc_subpage:
                doc = pywikibot.Page(self.site, article.title() + subpage)
                try:
                    doc.get()
                except Error:
                    pass
                else:
                    moved += doc.change_category(old_cat, new_cat,
                                                 summary=summary)

        if found:
            pywikibot.info(f'{old_cat}: {found} found, {moved} moved')
        return found, moved

    def ready_to_edit(self, cat):
        """Return True if cat not edited during cooldown period, else False."""
        today = pywikibot.Timestamp.now()
        deadline = today + timedelta(days=-self.opt.delay)
        return deadline > cat.latest_revision.timestamp

    def get_log_text(self):
        """Rotate log text and return the most recent text."""
        try:
            log_text = self.log_page.get()
        except NoPageError:
            log_text = ''
        log_items = {}
        header = None
        for line in log_text.splitlines():
            if line.startswith('==') and line.endswith('=='):
                header = line[2:-2].strip()
            if header is not None:
                log_items.setdefault(header, [])
                log_items[header].append(line)
        if len(log_items) < LOG_SIZE:
            return log_text
        # sort by keys and keep the first (LOG_SIZE-1) values
        keep = [text for (key, text) in
                sorted(log_items.items(), reverse=True)[:LOG_SIZE - 1]]
        log_text = '\n'.join('\n'.join(line for line in text) for text in keep)
        # get permalink to older logs
        history = list(self.log_page.revisions(total=LOG_SIZE))
        # get the id of the newest log being archived
        rotate_revid = history[-1].revid
        # append permalink
        message = i18n.twtranslate(
            self.site,
            'category_redirect-older-logs',
            {'oldlogs': self.log_page.permalink(oldid=rotate_revid)})
        log_text += ('\n\n' + message)
        return log_text

    def check_hard_redirect(self) -> None:
        """
        Check for hard-redirected categories.

        Check categories that are not already marked with an appropriate
        softredirect template.
        """
        pywikibot.info('Checking hard-redirect category pages.')
        comment = i18n.twtranslate(self.site, self.redir_comment)

        # generator yields all hard redirect pages in namespace 14
        for page in self.site.allpages(namespace=14, filterredir=True,
                                       content=True):
            if page.isCategoryRedirect():
                # this is already a soft-redirect, so skip it (for now)
                continue
            try:
                target = page.getRedirectTarget()
            except CircularRedirectError:
                target = page
                message = i18n.twtranslate(
                    self.site, 'category_redirect-problem-self-linked',
                    {'oldcat': page.title(as_link=True, textlink=True)})
                self.problems.append(message)
            except RuntimeError:
                # race condition: someone else removed the redirect while we
                # were checking for it
                continue

            if not target.is_categorypage():
                message = i18n.twtranslate(
                    self.site, 'category_redirect-problem-hard', {
                        'oldcat': page.title(as_link=True, textlink=True),
                        'page': target.title(as_link=True, textlink=True)
                    })
                self.problems.append(message)
                continue

            # this is a hard-redirect to a category page
            newtext = ('{{%(template)s|%(cat)s}}'
                       % {'cat': target.title(with_ns=False),
                          'template': self.template_list[0]})
            params = {
                'ns': self.site.namespaces.TEMPLATE.custom_prefix(),
                'template': self.template_list[0],
                'oldcat': page.title(as_link=True, textlink=True)
            }
            try:
                page.text = newtext
                page.save(comment)
                message = i18n.twtranslate(
                    self.site, 'category_redirect-log-added', params)
                self.log_text.append(message)
            except Error as e:
                pywikibot.error(e)
                message = i18n.twtranslate(
                    self.site, 'category_redirect-log-add-failed', params)
                self.log_text.append(message)

    def run(self) -> None:
        """Run the bot."""
        # validate L10N
        self.template_list = self.site.category_redirects()
        if not self.template_list:
            pywikibot.warning('No redirect templates defined for {}'
                              .format(self.site))
            return
        if not self.get_cat():
            pywikibot.warning('No redirect category found for {}'
                              .format(self.site))
            return

        self.user = self.site.user()  # invokes login()
        self.newredirs = []

        localtime = time.localtime()
        today = '{:04d}-{:02d}-{:02d}'.format(*localtime[:3])
        self.datafile = pywikibot.config.datafilepath(
            f'{self.site.dbName()}-catmovebot-data')
        try:
            with open(self.datafile, 'rb') as inp:
                self.record = pickle.load(inp)
        except OSError:
            self.record = {}
        if self.record:
            with open(self.datafile + '.bak', 'wb') as f:
                pickle.dump(self.record, f, protocol=config.pickle_protocol)
        # regex to match soft category redirects
        # TODO: enhance and use textlib.MultiTemplateMatchBuilder
        # note that any templates containing optional "category:" are
        # incorrect and will be fixed by the bot
        template_regex = re.compile(
            r"""{{{{\s*(?:{prefix}\s*:\s*)?  # optional "template:"
                     (?:{template})\s*\|     # catredir template name
                     (\s*{catns}\s*:\s*)?    # optional "category:"
                     ([^|}}]+)               # redirect target cat
                     (?:\|[^|}}]*)*}}}}      # optional arguments 2+, ignored
             """.format(prefix=self.site.namespace(10).lower(),
                        template='|'.join(item.replace(' ', '[ _]+')
                                          for item in self.template_list),
                        catns=self.site.namespace(14)),
            re.I | re.X)

        self.check_hard_redirect()

        comment = i18n.twtranslate(self.site, self.move_comment)
        counts = {}
        nonemptypages = []
        redircat = self.cat

        pywikibot.info('\nChecking {} category redirect pages'
                       .format(redircat.categoryinfo['subcats']))
        catpages = set()
        for cat in redircat.subcategories():
            catpages.add(cat)
            cat_title = cat.title(with_ns=False)
            if 'category redirect' in cat_title:
                message = i18n.twtranslate(
                    self.site, 'category_redirect-log-ignoring',
                    {'oldcat': cat.title(as_link=True, textlink=True)})
                self.log_text.append(message)
                continue
            if hasattr(cat, '_catinfo'):
                # skip empty categories that don't return a "categoryinfo" key
                catdata = cat.categoryinfo
                if 'size' in catdata and int(catdata['size']):
                    # save those categories that have contents
                    nonemptypages.append(cat)
            if cat_title not in self.record:
                # make sure every redirect has a self.record entry
                self.record[cat_title] = {today: None}
                with suppress(Error):
                    self.newredirs.append('*# {} → {}'.format(
                        cat.title(as_link=True, textlink=True),
                        cat.getCategoryRedirectTarget().title(
                            as_link=True, textlink=True)))
                # do a null edit on cat
                with suppress(Exception):
                    cat.save()

        # delete self.record entries for non-existent categories
        for cat_name in list(self.record):
            if pywikibot.Category(self.site,
                                  self.catprefix + cat_name) not in catpages:
                del self.record[cat_name]

        pywikibot.info('\nMoving pages out of {} redirected categories.'
                       .format(len(nonemptypages)))

        for cat in pagegenerators.PreloadingGenerator(nonemptypages):
            i18n_param = {'oldcat': cat.title(as_link=True, textlink=True)}

            try:
                if not cat.isCategoryRedirect():
                    message = i18n.twtranslate(
                        self.site,
                        'category_redirect-log-false-positive',
                        i18n_param
                    )
                    self.log_text.append(message)
                    continue
            except Error:
                message = i18n.twtranslate(self.site,
                                           'category_redirect-log-not-loaded',
                                           i18n_param)
                self.log_text.append(message)
                continue

            cat_title = cat.title(with_ns=False)
            if not self.ready_to_edit(cat):
                counts[cat_title] = None
                message = i18n.twtranslate(self.site,
                                           'category_redirect-log-skipping',
                                           i18n_param)
                self.log_text.append(message)
                continue

            dest = cat.getCategoryRedirectTarget()
            if not dest.exists():
                message = i18n.twtranslate(
                    self.site, 'category_redirect-problem-redirects', {
                        'oldcat': cat.title(as_link=True, textlink=True),
                        'redpage': dest.title(as_link=True, textlink=True)
                    })
                self.problems.append(message)
                # do a null edit on cat to update any special redirect
                # categories this wiki might maintain
                with suppress(Exception):
                    cat.save()
                continue

            if dest.isCategoryRedirect():
                double = dest.getCategoryRedirectTarget()
                if double in (dest, cat):
                    message = i18n.twtranslate(self.site,
                                               'category_redirect-log-loop',
                                               i18n_param)
                    self.log_text.append(message)
                    # do a null edit on cat
                    with suppress(Exception):
                        cat.save()
                else:
                    message = i18n.twtranslate(
                        self.site, 'category_redirect-log-double', {
                            'oldcat': cat.title(as_link=True, textlink=True),
                            'newcat': dest.title(as_link=True, textlink=True),
                            'targetcat': double.title(
                                as_link=True, textlink=True)
                        })
                    self.log_text.append(message)
                    oldtext = cat.text
                    # remove the old redirect from the old text,
                    # leaving behind any non-redirect text
                    oldtext = template_regex.sub('', oldtext)
                    newtext = ('{{%(redirtemp)s|%(ncat)s}}'
                               % {'redirtemp': self.template_list[0],
                                  'ncat': double.title(with_ns=False)})
                    newtext += oldtext.strip()
                    try:
                        cat.text = newtext
                        cat.save(i18n.twtranslate(self.site,
                                                  self.dbl_redir_comment))
                    except Error as e:
                        message = i18n.twtranslate(
                            self.site, 'category_redirect-log-failed',
                            {'error': e})
                        self.log_text.append(message)
                continue

            found, moved = self.move_contents(
                cat_title, dest.title(with_ns=False), comment)
            if found:
                self.record[cat_title][today] = found
                message = i18n.twtranslate(
                    self.site, 'category_redirect-log-moved', {
                        'oldcat': cat.title(as_link=True, textlink=True),
                        'found': found,
                        'moved': moved
                    })
                self.log_text.append(message)
            counts[cat_title] = found
            # do a null edit on cat
            with suppress(Exception):
                cat.save()

        self.teardown()

    def teardown(self) -> None:
        """Write self.record to file and save logs."""
        with open(self.datafile, 'wb') as f:
            pickle.dump(self.record, f, protocol=config.pickle_protocol)

        self.log_text.sort()
        self.problems.sort()
        self.newredirs.sort()
        comment = i18n.twtranslate(self.site, self.maint_comment)
        message = i18n.twtranslate(self.site, 'category_redirect-log-new')
        date_line = '\n== {}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z ==\n' \
                    .format(*time.gmtime()[:6])
        self.log_page.text = (date_line
                              + '\n'.join(self.log_text)
                              + '\n* ' + message + '\n'
                              + '\n'.join(self.newredirs)
                              + '\n' + '\n'.join(self.problems)
                              + '\n' + self.get_log_text())
        self.log_page.save(comment)
        if self.edit_requests:
            edit_request_page = pywikibot.Page(
                self.site, f'User:{self.user}/category edit requests')
            edit_request_page.text = (self.edit_request_text
                                      % {'itemlist': '\n' + '\n'.join(
                                          (self.edit_request_item % item)
                                          for item in self.edit_requests)})
            edit_request_page.save(comment)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    for arg in pywikibot.handle_args(args):
        if arg.startswith('-delay:'):
            options['delay'] = int(removeprefix(arg, '-delay:'))
        else:
            # generic handling of we have boolean options
            options[arg[1:]] = True
    bot = CategoryRedirectBot(**options)
    bot.run()


if __name__ == '__main__':
    main()
