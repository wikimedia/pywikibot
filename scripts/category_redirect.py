#!/usr/bin/env python3
"""This bot will move pages out of redirected categories.

The bot will look for categories that are marked with a category
redirect template, take the first parameter of the template as the
target of the redirect, and move all pages and subcategories of the
category there. It also changes hard redirects into soft redirects, and
fixes double redirects. A log is written under
``<userpage>/category_redirect_log``. A log is written under
``<userpage>/category_edit_requests`` if a page cannot be moved to be
done manually. Only category pages that haven't been edited for a
certain cooldown period (default 7 days) are taken into account.

The following parameters are supported:

-always           If used, the bot won't ask if it should add the specified
                  text

-delay:#          Set an amount of days. If the category is edited more
                  recently than given days, ignore it. Default is 7.

-tiny             Only loops over Category:Non-empty_category_redirects and
                  moves all images, pages and categories in redirect categories
                  to the target category.

-category:<cat>   Category to be used with this script. If not given
                  either wikibase entries Q4616723 or Q8099903 are used.

Usage:

    python pwb.py category_redirect [options]

.. note:: This script is a
   :py:obj:`ConfigParserBot <bot.ConfigParserBot>`. All options
   can be set within a settings file which is scripts.ini by default.
"""
#
# (C) Pywikibot team, 2008-2023
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import pickle
import re
import time
from contextlib import suppress
from datetime import timedelta

import pywikibot
from pywikibot import config, i18n, pagegenerators
from pywikibot.bot import AutomaticTWSummaryBot, ConfigParserBot, SingleSiteBot
from pywikibot.exceptions import (
    CircularRedirectError,
    Error,
    LockedPageError,
    NoCreateError,
    NoPageError,
    PageSaveRelatedError,
)


LOG_SIZE = 7  # Number of items to keep in active log
# Category that contains all redirected category pages
CAT_REDIRECT_CAT = 'Q4616723'
# Category that contains non-empty redirected category pages
TINY_CAT_REDIRECT_CAT = 'Q8099903'
MOVE_COMMENT = 'category_redirect-change-category'
REDIR_COMMENT = 'category_redirect-add-template'
DBL_REDIR_COMMENT = 'category_redirect-fix-double'
MAINT_COMMENT = 'category_redirect-comment'


class CategoryRedirectBot(
    ConfigParserBot,
    SingleSiteBot,
    AutomaticTWSummaryBot
):

    """Page category update bot.

    .. versionchanged:: 7.0
       CategoryRedirectBot is a ConfigParserBot

    .. versionchanged:: 9.0
       A logentry is writen to <userpage>/category_edit_requests if a
       page cannot be moved
    """

    update_options = {
        'tiny': False,  # use Non-empty category redirects only
        'delay': 7,  # cool down delay in days
        'category': ''  # category to be used
    }

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        self.catprefix = self.site.namespace(14) + ':'
        self.log_text = []
        self.edit_requests = []
        self.problems = []
        self.record = {}
        self.newredirs = []
        self.oldstart = None

        self.log_page = pywikibot.Page(
            self.site, f'User:{self.site.username()}/category redirect log')

        self.edit_request_text = i18n.twtranslate(
            self.site, 'category_redirect-edit-request') + '\n~~~~'
        self.edit_request_item = i18n.twtranslate(
            self.site, 'category_redirect-edit-request-item')

        # validate L10N
        self.cat = self.get_cat()
        if not self.cat:
            raise Error(f'No redirect category found for {self.site}')
        self.template_list = self.site.category_redirects()
        if not self.template_list:
            raise Error(f'No redirect templates defined for {self.site}')

    def get_cat(self):
        """Specify the category page."""
        if self.opt.category:
            if self.opt.tiny:
                raise Error('-tiny option is given together with -category')

            cat = pywikibot.Category(self.site, self.opt.category)
            if cat.exists():
                return cat

            raise Error(f'Category {cat} not found')

        item = TINY_CAT_REDIRECT_CAT if self.opt.tiny else CAT_REDIRECT_CAT
        return self.site.page_from_repository(item)

    def move_contents(self, old_cat_title: str, new_cat_title: str,
                      edit_summary: str) -> tuple[int, int]:
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
        for found, article in enumerate(old_cat.members(), start=1):
            done = article.change_category(old_cat, new_cat, summary=summary)
            if done:
                moved += 1
            else:
                self.edit_requests.append({
                    'title': article.title(as_link=True, textlink=True),
                    'oldcat': old_cat.title(as_link=True, textlink=True),
                    'newcat': new_cat.title(as_link=True, textlink=True)}
                )

            if article.namespace() != 10:
                continue

            # pass 2: look for template doc pages
            for subpage in self.site.doc_subpage:
                doc = pywikibot.Page(self.site, article.title() + subpage)
                try:
                    doc.get()
                except Error:
                    continue

                done = doc.change_category(old_cat, new_cat, summary=summary)
                if done:
                    moved += 1
                else:
                    self.edit_requests.append({
                        'title': doc.title(as_link=True, textlink=True),
                        'oldcat': old_cat.title(as_link=True, textlink=True),
                        'newcat': new_cat.title(as_link=True, textlink=True)}
                    )

        if found:
            self.counter['move'] += moved
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

    def setup_hard_redirect(self):
        """Setup hard redirect task."""
        pywikibot.info('Checking hard-redirect category pages.')
        self.summary_key = REDIR_COMMENT
        self.generator = self.site.allpages(
            namespace=14, filterredir=True, content=True)
        self.treat_page = self.check_hard_redirect

    def check_hard_redirect(self) -> None:
        """Check for hard-redirected categories.

        Check categories that are not already marked with an appropriate
        softredirect template and replace the content with a redirect
        template.
        """
        page = self.current_page
        if page.isCategoryRedirect():
            # this is already a soft-redirect, so skip it (for now)
            return

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
            return

        if not target.is_categorypage():
            message = i18n.twtranslate(
                self.site, 'category_redirect-problem-hard', {
                    'oldcat': page.title(as_link=True, textlink=True),
                    'page': target.title(as_link=True, textlink=True)
                })
            self.problems.append(message)
            return

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
            self.put_current(newtext)
            message = i18n.twtranslate(
                self.site, 'category_redirect-log-added', params)
        except Error as e:
            pywikibot.error(e)
            message = i18n.twtranslate(
                self.site, 'category_redirect-log-add-failed', params)

        self.log_text.append(message)

    def load_record(self) -> None:
        """Load record from data file and create a backup file."""
        self.datafile = pywikibot.config.datafilepath(
            f'{self.site.dbName()}-catmovebot-data')
        with suppress(OSError), open(self.datafile, 'rb') as inp:
            self.record = pickle.load(inp)
        if self.record:
            with open(self.datafile + '.bak', 'wb') as f:
                pickle.dump(self.record, f, protocol=config.pickle_protocol)

    def touch(self, page) -> None:
        """Touch the given page."""
        try:
            page.touch()
        except (NoCreateError, NoPageError):
            pywikibot.error(f'Page {page.title(as_link=True)} does not exist.')
        except LockedPageError:
            pywikibot.error(f'Page {page.title(as_link=True)} is locked.')
        except PageSaveRelatedError as e:
            pywikibot.error(f'Page {page} not saved:\n{e.args}')
        else:
            self.counter['touch'] += 1

    def setup_soft_redirect(self):
        """Setup soft redirect task."""
        pywikibot.info(f'\nChecking {self.cat.categoryinfo["subcats"]}'
                       ' category redirect pages')
        self.load_record()
        localtime = time.localtime()
        self.today = '{:04d}-{:02d}-{:02d}'.format(*localtime[:3])

        # regex to match soft category redirects
        # TODO: enhance and use textlib.MultiTemplateMatchBuilder
        # note that any templates containing optional "category:" are
        # incorrect and will be fixed by the bot
        self.template_regex = re.compile(
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

        nonemptypages = []
        catpages = set()

        # No throttle for touch edits
        save_throttle = config.put_throttle
        config.put_throttle = 0

        do_exit = False
        try:
            for cat in self.cat.subcategories():
                if do_exit:
                    break

                self.counter['read'] += 1
                cat_title = cat.title(with_ns=False)
                if 'category redirect' in cat_title:
                    message = i18n.twtranslate(
                        self.site, 'category_redirect-log-ignoring',
                        {'oldcat': cat.title(as_link=True, textlink=True)})
                    self.log_text.append(message)
                    continue

                if hasattr(cat, '_catinfo'):
                    # skip empty categories that don't return a "categoryinfo"
                    # key
                    catdata = cat.categoryinfo
                    if 'size' in catdata and int(catdata['size']):
                        # save those categories that have contents
                        nonemptypages.append(cat)

                if cat_title not in self.record:
                    # make sure every redirect has a self.record entry
                    self.record[cat_title] = {self.today: None}
                    with suppress(Error):
                        self.newredirs.append('*# {} → {}'.format(
                            cat.title(as_link=True, textlink=True),
                            cat.getCategoryRedirectTarget().title(
                                as_link=True, textlink=True)))

                    # do a null edit on cat
                    if cat not in catpages:
                        self.touch(cat)

                catpages.add(cat)
        except KeyboardInterrupt:
            pywikibot.info('KeyboardInterrupt during subcategory checks...')
            do_exit = True

        config.put_throttle = save_throttle

        # delete self.record entries for non-existent categories
        for cat_name in list(self.record):
            if pywikibot.Category(self.site,
                                  self.catprefix + cat_name) not in catpages:
                del self.record[cat_name]

        pywikibot.info(f'\nMoving pages out of {len(nonemptypages)}'
                       ' redirected categories.')
        self.summary_key = DBL_REDIR_COMMENT
        self.generator = pagegenerators.PreloadingGenerator(nonemptypages)
        self.treat_page = self.check_soft_redirect

    def check_soft_redirect(self) -> None:
        """Check for soft-redirected categories."""
        cat = self.current_page
        i18n_param = {'oldcat': cat.title(as_link=True, textlink=True)}

        try:
            if not cat.isCategoryRedirect():
                message = i18n.twtranslate(
                    self.site,
                    'category_redirect-log-false-positive',
                    i18n_param
                )
                self.log_text.append(message)
                return
        except Error:
            message = i18n.twtranslate(self.site,
                                       'category_redirect-log-not-loaded',
                                       i18n_param)
            self.log_text.append(message)
            return

        cat_title = cat.title(with_ns=False)
        if not self.ready_to_edit(cat):
            message = i18n.twtranslate(self.site,
                                       'category_redirect-log-skipping',
                                       i18n_param)
            self.log_text.append(message)
            return

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
            self.touch(cat)
            return

        if dest.isCategoryRedirect():
            double = dest.getCategoryRedirectTarget()
            if double in (dest, cat):
                message = i18n.twtranslate(self.site,
                                           'category_redirect-log-loop',
                                           i18n_param)
                self.log_text.append(message)
                # do a null edit on cat
                self.touch(cat)
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
                oldtext = self.template_regex.sub('', oldtext)
                newtext = ('{{%(redirtemp)s|%(ncat)s}}'
                           % {'redirtemp': self.template_list[0],
                              'ncat': double.title(with_ns=False)})
                newtext += oldtext.strip()
                try:
                    self.put_current(newtext)
                except Error as e:
                    message = i18n.twtranslate(
                        self.site, 'category_redirect-log-failed',
                        {'error': e})
                    self.log_text.append(message)
            return

        found, moved = self.move_contents(
            cat_title,
            dest.title(with_ns=False),
            i18n.twtranslate(self.site, MOVE_COMMENT)
        )

        if found:
            self.record[cat_title][self.today] = found
            message = i18n.twtranslate(
                self.site, 'category_redirect-log-moved', {
                    'oldcat': cat.title(as_link=True, textlink=True),
                    'found': found,
                    'moved': moved
                })
            self.log_text.append(message)

        # do a null edit on cat
        self.touch(cat)

    def run(self) -> None:
        """Run the bot."""
        self.user = self.site.user()  # invokes login()

        # process hard category redirects
        oldexit = self.exit
        self.exit = lambda: None
        self.setup = self.setup_hard_redirect
        super().run()

        # save timestamp and prepare the next step
        self.oldstart = self._start_ts
        if not self.generator_completed \
           and (self.opt.always
                or not pywikibot.input_yn(
                    'Continue with soft category redirects',
                    automatic_quit=False)):
            oldexit()
            return

        # process soft category redirects
        self.exit = oldexit
        self.generator_completed = False
        self.setup = self.setup_soft_redirect
        super().run()

    def teardown(self) -> None:
        """Write self.record to file and save logs."""
        self._start_ts = self.oldstart
        if self.record:
            with open(self.datafile, 'wb') as f:
                pickle.dump(self.record, f, protocol=config.pickle_protocol)

        comment = i18n.twtranslate(self.site, MAINT_COMMENT)

        if self.log_text or self.problems or self.newredirs:
            self.log_text.sort()
            self.problems.sort()
            self.newredirs.sort()
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
    unknown = []
    for arg in pywikibot.handle_args(args):
        opt, _, value = arg.partition(':')
        if opt[0] != '-':
            unknown.append(arg)
            continue

        opt = opt[1:]
        if opt == 'delay:':
            options[opt] = int(value)
        elif opt == 'category':
            options[opt] = value
        else:
            # generic handling of we have boolean options
            options[opt] = True

    if not pywikibot.bot.suggest_help(unknown_parameters=unknown):
        try:
            bot = CategoryRedirectBot(**options)
        except Error as e:
            pywikibot.bot.suggest_help(exception=e)
        else:
            bot.run()


if __name__ == '__main__':
    main()
