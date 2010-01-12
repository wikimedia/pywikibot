# -*- coding: utf-8 -*-
"""This bot will move pages out of redirected categories

Usage: category_redirect.py [options]

The bot will look for categories that are marked with a category redirect
template, take the first parameter of the template as the target of the
redirect, and move all pages and subcategories of the category there. It
also changes hard redirects into soft redirects, and fixes double redirects.
A log is written under <userpage>/category_redirect_log. Only category pages
that haven't been edited for a certain cooldown period (currently 7 days)
are taken into account.

"""

#
# (C) Pywikipedia team, 2008-2009
#
__version__ = '$Id$'
#
# Distributed under the terms of the MIT license.
#

import pywikibot
from pywikibot import pagegenerators
import cPickle
import math
import re
import sys, traceback
import time
from datetime import datetime, timedelta


class CategoryRedirectBot(object):
    def __init__(self):
        self.cooldown = 7 # days
        self.site = pywikibot.getSite()
        self.catprefix = self.site.namespace(14)+":"
        self.log_text = []
        self.edit_requests = []
        self.log_page = pywikibot.Page(self.site,
                        u"User:%(user)s/category redirect log" %
                            {'user': self.site.user()})

        # Localization:

        # Category that contains all redirected category pages
        self.cat_redirect_cat = {
            'wikipedia': {
                'ar': u"تصنيف:تحويلات تصنيفات ويكيبيديا",
                'cs': u"Kategorie:Zastaralé kategorie",
                'da': "Kategori:Omdirigeringskategorier",
                'en': "Category:Wikipedia soft redirected categories",
                'hu': "Kategória:Kategóriaátirányítások",
                'ja': "Category:移行中のカテゴリ",
                'no': "Kategori:Wikipedia omdirigertekategorier",
                'pl': "Kategoria:Przekierowania kategorii",
                'simple': "Category:Category redirects",
                'vi': u"Thể loại:Thể loại đổi hướng",
                'zh': u"Category:已重定向的分类",
            },
            'commons': {
                'commons': "Category:Category redirects"
            }
        }

        self.move_comment = {
            'ar': u"روبوت: نقل الصفحات من تصنيف محول",
            'cs': u'Robot přesunul stránku ze zastaralé kategorie',
            'da': u"Robot: flytter sider ud af omdirigeringskategorien",
            'en':
u"Robot: change redirected category [[:%(oldCatLink)s|%(oldCatTitle)s]]"
u" to [[:%(newCatLink)s|%(newCatTitle)s]]",
            'hu': u"Bot: Lapok automatikus áthelyezése átirányított kategóriából",
            'ja': u"ロボットによる: 移行中のカテゴリからのカテゴリ変更",
            'ksh': u"Bot: Sigk uß en ömjeleidt Saachjropp eruß jesammdt.",
            'no': u"Robot: Flytter sider ut av omdirigeringskategori",
            'pl': u"Robot: Usuwa strony z przekierowanej kategorii",
            'commons': u'Robot: Changing category link (following [[Template:Category redirect|category redirect]])',
            'vi': u"Robot: bỏ trang ra khỏi thể loại đổi hướng",
            'zh': u'机器人：改变已重定向分类中的页面的分类',
        }

        self.redir_comment = {
            'ar':u"روبوت: إضافة قالب تحويل تصنيف للصيانة",
            'cs':u'Robot označil kategorii jako zastaralou',
            'da':u"Robot: tilføjer omdirigeringsskabelon for vedligeholdelse",
            'en':u"Robot: adding category redirect template for maintenance",
            'hu':u"Bot: kategóriaátirányítás sablon hozzáadása",
            'ja':u"ロボットによる: 移行中のカテゴリとしてタグ付け",
            'ksh':u"Bot: Ömleidungsschalbon dobeijedonn.",
            'no':u"Robot: Legger til vedlikeholdsmal for kategoriomdirigering",
            'pl':u"Robot: Dodaje szablon przekierowanej kategorii",
            'vi':u"Robot: thêm bản mẫu đổi hướng thể loại để dễ bảo trì",
            'zh':u"机器人: 增加分类重定向模板，用于维护",
        }

        self.dbl_redir_comment = {
            'ar': u"روبوت: تصليح تحويلة مزدوجة",
            'cs': u'Robot opravil dvojité přesměrování',
            'da': u"Robot: retter dobbelt omdirigering",
            'en': u"Robot: fixing double-redirect",
            'fr': u"Robot : Correction des redirections doubles",
            'hu': u"Bot: Kettős átirányítás javítása",
            'ja': u"ロボットによる: 二重リダイレクト修正",
            'no': u"Robot: Ordner doble omdirigeringer",
            'ksh': u"Bot: dubbel Ömleidung eruß jemaat.",
            'pl': u"Robot: Poprawia podwójne przekierowanie",
            'vi': u"Robot: sửa thể loại đổi hướng kép",
            'zh': u"Bot: 修复双重重定向",
        }

        self.maint_comment = {
            'ar': u"بوت صيانة تحويل التصنيف",
            'cs': u'Údržba přesměrované kategorie',
            'da': u"Bot til vedligeholdelse af kategoromdirigeringer",
            'en': u"Category redirect maintenance bot",
            'fr': u"Robot de maintenance des redirection de catégorie",
            'hu': u"Kategóriaátirányítás-karbantartó bot",
            'ja': u"移行中のカテゴリのメンテナンス・ボット",
            'no': u"Bot for vedlikehold av kategoriomdirigeringer",
            'ksh': u"Bot för de Saachjroppe ier Ömleidunge.",
            'pl': u"Robot porządkujący przekierowania kategorii",
            'vi': u"Robot theo dõi thể loại đổi hướng",
            'zh': u"分类重定向维护机器人",
        }

        self.edit_request_text = pywikibot.translate(self.site.lang,
            {'en': u"""\
The following protected pages have been detected as requiring updates to \
category links:
%s
~~~~
""",
            'ksh': u"""\
Hee di Sigge sin jeschötz un möße ier Saachjroppe odder Lingks op Saachjroppe \
aanjepaß krijje:
%s
~~~~
""",
            'pl': u"""\
Następujące zabezpieczone strony wykryto jako wymagające \
poprawy kategorii:
%s
~~~~
""",
			'vi': u"""\
Các trang đã khóa sau cần phải cập nhật \
liên kết thể loại:
%s
~~~~
""",
            'zh': u"""\
下列被保护页面被检测出需要更新 \
分类链接:
%s
~~~~
""",
            })

        self.edit_request_item = pywikibot.translate(self.site.lang,
            {
                'en': u"* %s is in %s, which is a redirect to %s",
                'fr': u"* %s est dans %s, qui est une redirection vers %s",
                'ksh': u"* %s es en %s, un dat es en Ömleidung op %s",
                'pl': u"* %s jest w %s, która jest przekierowaniem do %s",
                'vi': u"* %s đang thuộc %s, là thể loại đổi hướng đến %s",
            })

    def change_category(self, article, oldCat, newCat, comment=None,
                        sortKey=None):
        """Given an article in category oldCat, moves it to category newCat.
        Moves subcategories of oldCat as well. oldCat and newCat should be
        Category objects. If newCat is None, the category will be removed.

        This is a copy of portions of [old] catlib.change_category(), with
        some changes.

        """
        oldtext = article.get(get_redirect=True, force=True)
        newtext = pywikibot.replaceCategoryInPlace(oldtext, oldCat, newCat)
        try:
            # even if no changes, still save the page, in case it needs
            # an update due to changes in a transcluded template
            article.put(newtext, comment)
            if newtext == oldtext:
                pywikibot.output(
                    u'No changes in made in page %s.'
                     % article.title(asLink=True)
                )
                return False
            return True
        except pywikibot.EditConflict:
            pywikibot.output(
                u'Skipping %s because of edit conflict'
                % article.title(asLink=True)
            )
        except pywikibot.LockedPage:
            pywikibot.output(u'Skipping locked page %s'
                             % article.title(asLink=True)
            )
            self.edit_requests.append(
                    (article.title(asLink=True, textlink=True),
                     oldCat.title(asLink=True, textlink=True),
                     newCat.title(asLink=True, textlink=True)
                    ))
        except pywikibot.SpamfilterError, error:
            pywikibot.output(
                u'Changing page %s blocked by spam filter (URL=%s)'
                             % (article.title(asLink=True), error.url))
        except pywikibot.NoUsername:
            pywikibot.output(
                u"Page %s not saved; sysop privileges required."
                             % article.title(asLink=True))
            self.edit_requests.append(
                    (article.title(asLink=True, textlink=True),
                     oldCat.title(asLink=True, textlink=True),
                     newCat.title(asLink=True, textlink=True)
                   ))
        except pywikibot.PageNotSaved, error:
            pywikibot.output(u"Saving page %s failed: %s"
                             % (article.title(asLink=True), error))
        return False

    def move_contents(self, oldCatTitle, newCatTitle, editSummary):
        """The worker function that moves pages out of oldCat into newCat"""
        while True:
            try:
                oldCat = pywikibot.Category(self.site,
                                            self.catprefix + oldCatTitle)
                newCat = pywikibot.Category(self.site,
                                            self.catprefix + newCatTitle)

                oldCatLink = oldCat.title()
                newCatLink = newCat.title()
                comment = editSummary % locals()
                # Move articles
                found, moved = 0, 0
                for article in oldCat.members():
                    found += 1
                    changed = self.change_category(article, oldCat, newCat,
                                                   comment=comment)
                    if changed: moved += 1

                # pass 2: look for template doc pages
                for item in pywikibot.data.api.ListGenerator(
                                "categorymembers", cmtitle=oldCat.title(),
                                cmprop="title|sortkey", cmnamespace="10",
                                cmlimit="max"):
                    doc = pywikibot.Page(
                              pywikibot.Link(item['title']+"/doc", self.site)
                          )
                    try:
                        old_text = doc.get()
                    except pywikibot.Error:
                        continue
                    changed = self.change_category(doc, oldCat, newCat,
                                                   comment=comment)
                    if changed: moved += 1

                if found:
                    pywikibot.output(u"%s: %s found, %s moved"
                                     % (oldCat.title(), found, moved))
                return (found, moved)
            except pywikibot.ServerError:
                pywikibot.output(u"Server error: retrying in 5 seconds...")
                time.sleep(5)
                continue
            except KeyboardInterrupt:
                raise
            except:
                return (None, None)

    def readyToEdit(self, cat):
        """Return True if cat not edited during cooldown period, else False."""
        dateformat ="%Y-%m-%dT%H:%M:%SZ"
        today = datetime.now()
        deadline = today + timedelta(days=-self.cooldown)
        if cat.editTime() is None:
            raise RuntimeError
        return (deadline.strftime(dateformat) > cat.editTime())

    def get_log_text(self):
        """Rotate log text and return the most recent text."""
        LOG_SIZE = 7  # Number of items to keep in active log
        try:
            log_text = self.log_page.get()
        except pywikibot.NoPage:
            log_text = u""
        log_items = {}
        header = None
        for line in log_text.splitlines():
            if line.startswith("==") and line.endswith("=="):
                header = line[2:-2].strip()
            if header is not None:
                log_items.setdefault(header, [])
                log_items[header].append(line)
        if len(log_items) < LOG_SIZE:
            return log_text
        # sort by keys and keep the first (LOG_SIZE-1) values
        keep = [text for (key, text) in
                    sorted(log_items.iteritems(), reverse=True)[:LOG_SIZE-1]]
        log_text = "\n".join("\n".join(line for line in text) for text in keep)
        # get permalink to older logs
        history = self.log_page.getVersionHistory(total=LOG_SIZE)
        # get the id of the newest log being archived
        rotate_revid = history[-1][0]
        # append permalink
        log_text = log_text + (
            "\n\n'''[%s://%s%s/index.php?title=%s&oldid=%s Older logs]'''"
                % (self.site.protocol(),
                   self.site.hostname(),
                   self.site.scriptpath(),
                   self.log_page.title(asUrl=True),
                   rotate_revid))
        return log_text

    def run(self):
        """Run the bot"""
        global destmap, catlist, catmap

        user = self.site.user()
        redirect_magicwords = ["redirect"]
        other_words = self.site.redirect()
        if other_words:
            redirect_magicwords.extend(other_words)
        problems = []
        newredirs = []

        l = time.localtime()
        today = "%04d-%02d-%02d" % l[:3]
        edit_request_page = pywikibot.Page(self.site,
                            u"User:%(user)s/category edit requests" % locals())
        datafile = pywikibot.config.datafilepath(
                   "%s-catmovebot-data" % self.site.dbName())
        try:
            inp = open(datafile, "rb")
            record = cPickle.load(inp)
            inp.close()
        except IOError:
            record = {}
        if record:
            cPickle.dump(record, open(datafile + ".bak", "wb"), -1)

        try:
            template_list = self.site.family.category_redirect_templates[self.site.code]
        except KeyError:
            pywikibot.output(u"No redirect templates defined for %s"
                              % self.site.sitename())
            return
        # regex to match soft category redirects
        #  note that any templates containing optional "category:" are
        #  incorrect and will be fixed by the bot
        template_regex = re.compile(
            ur"""{{\s*(?:%(prefix)s\s*:\s*)?  # optional "template:"
                      (?:%(template)s)\s*\|   # catredir template name
                      (\s*%(catns)s\s*:\s*)?  # optional "category:"
                      ([^|}]+)                # redirect target cat
                      (?:\|[^|}]*)*}}         # optional arguments 2+, ignored
              """ % {'prefix': self.site.namespace(10).lower(),
                     'template': "|".join(item.replace(" ", "[ _]+")
                                          for item in template_list),
                     'catns': self.site.namespace(14)},
            re.I|re.X)

        # check for hard-redirected categories that are not already marked
        # with an appropriate template
        comment = pywikibot.translate(self.site.lang, self.redir_comment)
        for page in pagegenerators.PreloadingGenerator(
                        self.site.allpages(namespace=14, filterredir=True),
                        step=250
                    ):
            # generator yields all hard redirect pages in namespace 14
            if page.isCategoryRedirect():
                # this is already a soft-redirect, so skip it (for now)
                continue
            try:
                target = page.getRedirectTarget()
            except pywikibot.CircularRedirect:
                target = page
                problems.append(
                    u"# %s is a self-linked redirect"
                     % page.title(asLink=True, textlink=True))
            except RuntimeError:
                # race condition: someone else removed the redirect while we
                # were checking for it
                continue
            if target.namespace() == 14:
                # this is a hard-redirect to a category page
                newtext = (u"{{%(template)s|%(cat)s}}"
                           % {'cat': target.title(withNamespace=False),
                              'template': template_list[0]})
                try:
                    page.put(newtext, comment, minorEdit=True)
                    self.log_text.append(u"* Added {{tl|%s}} to %s"
                                     % (template_list[0],
                                        page.title(asLink=True, textlink=True)))
                except pywikibot.Error, e:
                    self.log_text.append(
                        u"* Failed to add {{tl|%s}} to %s"
                         % (template_list[0],
                            page.title(asLink=True, textlink=True)))
            else:
                problems.append(
                    u"# %s is a hard redirect to %s"
                     % (page.title(asLink=True, textlink=True),
                        target.title(asLink=True, textlink=True)))

        pywikibot.output("Done checking hard-redirect category pages.")

        comment = pywikibot.translate(self.site.lang, self.move_comment)
        counts, destmap, catmap = {}, {}, {}
        catlist, nonemptypages = [], []
        redircat = pywikibot.Category(
                       pywikibot.Link(
                           self.cat_redirect_cat[self.site.family.name]
                                                [self.site.code],
                           self.site)
                   )

        # get a list of all members of the category-redirect category
        catpages = list(redircat.subcategories())

        # preload the category pages for redirected categories
        pywikibot.output(u"")
        pywikibot.output(u"Preloading %s category redirect pages"
                         % len(catpages))
        for cat in pagegenerators.PreloadingGenerator(catpages, step=250):
            catdata = cat.categoryinfo
            if "size" in catdata and int(catdata['size']):
                # save those categories that have contents
                nonemptypages.append(cat)
            cat_title = cat.title(withNamespace=False)
            if "category redirect" in cat_title:
                self.log_text.append(u"* Ignoring %s"
                                      % cat.title(asLink=True, textlink=True))
                continue
            try:
                if not cat.isCategoryRedirect():
                    self.log_text.append(u"* False positive: %s"
                                          % cat.title(asLink=True,
                                                      textlink=True))
                    continue
            except pywikibot.Error:
                self.log_text.append(u"* Could not load %s; ignoring"
                                      % cat.title(asLink=True, textlink=True))
                continue
            catlist.append(cat)
            target = cat.getCategoryRedirectTarget()
            destination = target.title(withNamespace=False)
            destmap.setdefault(target, []).append(cat)
            catmap[cat] = destination
            if cat_title not in record:
                # make sure every redirect has a record entry
                record[cat_title] = {today: None}
                newredirs.append("*# %s -> %s"
                               % (cat.title(asLink=True, textlink=True),
                                  target.title(asLink=True, textlink=True)))
##            if match.group(1):
##                # category redirect target starts with "Category:" - fix it
##                text = text[ :match.start(1)] + text[match.end(1): ]
##                try:
##                    cat.put(text,
##                            u"Robot: fixing category redirect parameter format")
##                    self.log_text.append(
##                        u"* Removed category prefix from parameter in %s"
##                         % cat.title(asLink=True, textlink=True))
##                except pywikibot.Error:
##                    self.log_text.append(
##                        u"* Unable to save changes to %s"
##                         % cat.title(asLink=True, textlink=True))

        # delete record entries for non-existent categories
        for cat_name in record.keys():
            if pywikibot.Category(
                    pywikibot.Link(self.catprefix+cat_name, self.site)
               ) not in catmap:
                del record[cat_name]

        pywikibot.output(u"")
        pywikibot.output(u"Checking %s destination categories" % len(destmap))
        for dest in pagegenerators.PreloadingGenerator(destmap, step=250):
            if not dest.exists():
                for d in destmap[dest]:
                    problems.append("# %s redirects to %s"
                                    % (d.title(asLink=True, textlink=True),
                                       dest.title(asLink=True, textlink=True)))
                    catlist.remove(d)
                    # do a null edit on d to make it appear in the
                    # "needs repair" category (if this wiki has one)
                    try:
                        d.put(d.get(get_redirect=True))
                    except:
                        pass
            if dest in catlist:
                for d in destmap[dest]:
                    # is catmap[dest] also a redirect?
                    newcat = pywikibot.Category(
                                 pywikibot.Link(self.catprefix+catmap[dest],
                                                self.site)
                             )
                    while newcat in catlist:
                        if newcat == d or newcat == dest:
                            self.log_text.append(u"* Redirect loop from %s"
                                             % newcat.title(asLink=True,
                                                            textlink=True))
                            break
                        newcat = pywikibot.Category(
                                     pywikibot.Link(
                                         self.catprefix+catmap[newcat],
                                         self.site)
                                 )
                    else:
                        self.log_text.append(
                            u"* Fixed double-redirect: %s -> %s -> %s"
                                % (d.title(asLink=True, textlink=True),
                                   dest.title(asLink=True, textlink=True),
                                   newcat.title(asLink=True, textlink=True)))
                        oldtext = d.get(get_redirect=True)
                        # remove the old redirect from the old text,
                        # leaving behind any non-redirect text
                        oldtext = template_regex.sub("", oldtext)
                        newtext = (u"{{%(redirtemp)s|%(ncat)s}}"
                                    % {'redirtemp': template_list[0],
                                       'ncat': newcat.title(withNamespace=False)})
                        newtext = newtext + oldtext.strip()
                        try:
                            d.put(newtext,
                                  pywikibot.translate(self.site.lang,
                                                      self.dbl_redir_comment),
                                  minorEdit=True)
                        except pywikibot.Error, e:
                            self.log_text.append("** Failed: %s" % e)

        # only scan those pages that have contents (nonemptypages)
        # and that haven't been removed from catlist as broken redirects
        cats_to_empty = set(catlist) & set(nonemptypages)
        pywikibot.output(u"")
        pywikibot.output(u"Moving pages out of %s redirected categories."
                         % len(cats_to_empty))
#        thread_limit = int(math.log(len(cats_to_empty), 8) + 1)
#        threadpool = ThreadList(limit=1)    # disabling multi-threads

        for cat in cats_to_empty:
            cat_title = cat.title(withNamespace=False)
            if not self.readyToEdit(cat):
                counts[cat_title] = None
                self.log_text.append(
                    u"* Skipping %s; in cooldown period."
                     % cat.title(asLink=True, textlink=True))
                continue
            found, moved = self.move_contents(cat_title, catmap[cat],
                                              editSummary=comment)
            if found is None:
                self.log_text.append(
                    u"* [[:%s%s]]: error in move_contents"
                    % (self.catprefix, cat_title))
            elif found:
                record[cat_title][today] = found
                self.log_text.append(
                    u"* [[:%s%s]]: %d found, %d moved"
                    % (self.catprefix, cat_title, found, moved))
            counts[cat_title] = found

        cPickle.dump(record, open(datafile, "wb"), -1)

        pywikibot.setAction(pywikibot.translate(self.site.lang,
                                                self.maint_comment))
        self.log_text.sort()
        problems.sort()
        newredirs.sort()
        self.log_page.put(u"\n==%i-%02i-%02iT%02i:%02i:%02iZ==\n"
                            % time.gmtime()[:6]
                          + u"\n".join(self.log_text)
                          + u"\n* New redirects since last report:\n"
                          + u"\n".join(newredirs)
                          + u"\n" + u"\n".join(problems)
                          + u"\n" + self.get_log_text())
        if self.edit_requests:
            edit_request_page.put(self.edit_request_text
                                 % u"\n".join((self.edit_request_item % item)
                                             for item in self.edit_requests))


def main(*args):
    global bot
    try:
        a = pywikibot.handleArgs(*args)
        if len(a) == 1:
            raise RuntimeError('Unrecognized argument "%s"' % a[0])
        elif a:
            raise RuntimeError('Unrecognized arguments: ' +
                               " ".join(('"%s"' % arg) for arg in a))
        bot = CategoryRedirectBot()
        bot.run()
    finally:
        pywikibot.stopme()


if __name__ == "__main__":
    main()
