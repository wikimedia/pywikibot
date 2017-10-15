#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Manage featured/good article/list status template.

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
                  Example: python pwb.py featured -fromlang:en,he -count
                  counts how many featured articles exist in the en and he
                  wikipedias.

-quiet            no corresponding pages are displayed.

"""
#
# (C) Maxim Razin, 2005
# (C) Leonardo Gregianin, 2005-2008
# (C) xqt, 2009-2014
# (C) Pywikibot team, 2005-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import pickle
import re
import sys

import pywikibot

from pywikibot import i18n, textlib, config

from pywikibot.pagegenerators import PreloadingGenerator
from pywikibot.tools.formatter import color_format
from pywikibot.tools import issue_deprecation_warning

if sys.version_info[0] > 2:
    unichr = chr


def CAT(site, name, hide):
    name = site.namespace(14) + ':' + name
    cat = pywikibot.Category(site, name)
    for article in cat.articles(endsort=hide):
        yield article
    if hide:
        for article in cat.articles(startFrom=unichr(ord(hide) + 1)):
            yield article


def BACK(site, name, hide):  # pylint: disable=unused-argument
    p = pywikibot.Page(site, name, ns=10)
    return [page for page in p.getReferences(follow_redirects=False,
                                             onlyTemplateInclusion=True)]


def DATA(site, name, hide):
    dp = pywikibot.ItemPage(site.data_repository(), name)
    try:
        title = dp.getSitelink(site)
    except pywikibot.NoPage:
        return
    cat = pywikibot.Category(site, title)
    if isinstance(hide, dict):
        hide = hide.get(site.code)
    for article in cat.articles(endsort=hide):
        yield article
    if hide:
        for article in cat.articles(startsort=unichr(ord(hide) + 1)):
            yield article


# not implemented yet
def TMPL(site, name, hide):  # pylint: disable=unused-argument
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
    'gl': [u'Ligazón AD', 'Destacado'],
    'hi': ['Link FA', 'Lien AdQ'],
    'is': [u'Tengill ÚG'],
    'it': ['Link V', 'Link AdQ'],
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
    'ca': [u'Enllaç AB', 'Lien BA', 'Abo'],
    'da': ['Link GA', 'Link AA'],
    'eo': ['LigoLeginda'],
    'es': ['Bueno'],
    'fr': ['Lien BA'],
    'gl': [u'Ligazón AB'],
    'is': ['Tengill GG'],
    'it': ['Link VdQ'],
    'nn': ['Link AA'],
    'no': ['Link AA'],
    'pt': ['Bom interwiki'],
    # 'tr': ['Link GA', 'Link KM'],
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
    'ksh': (CAT, 'Joode Leß'),
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
    'wikidata': (DATA, 'Q7045853', {'en': '#'})
}


class FeaturedBot(pywikibot.Bot):

    """Featured article bot."""

    # Bot configuration.
    # Only the keys of the dict can be passed as init options
    # The values are the default values

    def __init__(self, **kwargs):
        """Only accepts options defined in availableOptions."""
        self.availableOptions.update({
            'async': False,  # True for asynchronously putting a page
            'afterpage': u"!",
            'count': False,   # featuredcount
            'featured': False,
            'former': False,
            'fromall': False,
            'fromlang': None,
            'good': False,
            'lists': False,
            'nocache': [],
            'side': False,    # not template_on_top
            'quiet': False,
            'interactive': False,
        })

        super(FeaturedBot, self).__init__(**kwargs)
        self.cache = {}
        self.filename = None
        self.site = pywikibot.Site()
        self.repo = self.site.data_repository()

        # if no source site is given, give up
        if self.getOption('fromlang') is True:
            self.options['fromlang'] = False

        # setup tasks running
        self.tasks = []
        for task in ('featured', 'good', 'lists', 'former'):
            if self.getOption(task):
                self.tasks.append(task)
        if not self.tasks:
            self.tasks = ['featured']

    def itersites(self, task):
        """Generator for site codes to be processed."""
        def _generator():
            if task == 'good':
                item_no = good_name['wikidata'][1]
            elif task == 'featured':
                item_no = featured_name['wikidata'][1]
            elif task == 'former':
                item_no = former_name['wikidata'][1]
            dp = pywikibot.ItemPage(self.repo, item_no)
            dp.get()
            for key in sorted(dp.sitelinks.keys()):
                try:
                    site = self.site.fromDBName(key)
                except pywikibot.SiteDefinitionError:
                    pywikibot.output('"%s" is not a valid site. Skipping...'
                                     % key)
                else:
                    if site.family == self.site.family:
                        yield site

        generator = _generator()

        if self.getOption('fromall'):
            return generator
        elif self.getOption('fromlang'):
            fromlang = self.getOption('fromlang')
            if len(fromlang) == 1 and fromlang[0].find("--") >= 0:
                start, end = fromlang[0].split("--", 1)
                if not start:
                    start = ""
                if not end:
                    end = "zzzzzzz"
                return (site for site in generator
                        if site.code >= start and site.code <= end)
            else:
                return (site for site in generator if site.code in fromlang)
        else:
            pywikibot.warning(u'No sites given to verify %s articles.\n'
                              u'Please use -fromlang: or fromall option\n'
                              % task)
            return ()

    def hastemplate(self, task):
        add_tl, remove_tl = self.getTemplateList(self.site.code, task)
        for i, tl in enumerate(add_tl):
            tp = pywikibot.Page(self.site, tl, ns=10)
            if tp.exists():
                return True
            else:
                pywikibot.output(tl + ' does not exist')
                # The first item is the default template to be added.
                # It must exist. Otherwise the script must not run.
                if i == 0:
                    return
        else:
            return

    def readcache(self, task):
        if self.getOption('count') or self.getOption('nocache') is True:
            return
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
        if self.getOption('count'):
            return
        if not self.getOption('nocache') is True:
            pywikibot.output(u'Writing %d items to cache file %s.'
                             % (len(self.cache), self.filename))
            with open(self.filename, "wb") as f:
                pickle.dump(self.cache, f, protocol=config.pickle_protocol)
        self.cache = {}

    def run(self):
        for task in self.tasks:
            self.run_task(task)
        pywikibot.output(u'%d pages written.' % self._save_counter)

    def run_task(self, task):
        if not self.hastemplate(task):
            pywikibot.output(u'\nNOTE: %s articles are not implemented at %s.'
                             % (task, self.site))
            return

        self.readcache(task)
        for site in self.itersites(task):
            try:
                self.treat(site, task)
            except KeyboardInterrupt:
                pywikibot.output('\nQuitting %s treat...' % task)
                break
        self.writecache()

    def treat(self, fromsite, task):
        if fromsite != self.site:
            self.featuredWithInterwiki(fromsite, task)

    def featuredArticles(self, site, task, cache):
        articles = []
        info = globals()[task + '_name']
        if task == 'lists':
            code = site.code
        else:
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
            elif p.namespace() == 1 and site.code != 'el':
                articles.append(pywikibot.Page(p.site,
                                p.title(withNamespace=False)))
        pywikibot.output(color_format(
            '{lightred}** {0} has {1} {2} articles{default}',
            site, len(articles), task))
        while articles:
            p = articles.pop(0)
            if p.title() < self.getOption('afterpage'):
                continue

            if u"/" in p.title() and p.namespace() != 0:
                pywikibot.output(u"%s is a subpage" % p.title())
                continue

            if p.title() in cache:
                pywikibot.output(u"(cached) %s -> %s" % (p.title(),
                                                         cache[p.title()]))
                continue
            yield p

    def findTranslated(self, page, oursite=None):
        quiet = self.getOption('quiet')
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
        elif ourpage.section():
            pywikibot.output(u"%s -> our page is a section link: %s"
                             % (page.title(), ourpage.title()))
        elif not ourpage.exists():
            pywikibot.output(u"%s -> our page doesn't exist: %s"
                             % (page.title(), ourpage.title()))
        else:
            if ourpage.isRedirectPage():
                ourpage = ourpage.getRedirectTarget()

            pywikibot.output(u"%s -> corresponding page is %s"
                             % (page.title(), ourpage.title()))
            if ourpage.namespace() != 0:
                pywikibot.output(u"%s -> not in the main namespace, skipping"
                                 % page.title())
            elif ourpage.isRedirectPage():
                pywikibot.output(u"%s -> double redirect, skipping" % page.title())
            elif not ourpage.exists():
                pywikibot.output(u"%s -> page doesn't exist, skipping"
                                 % ourpage.title())
            else:
                backpage = None
                for link in ourpage.iterlanglinks():
                    if link.site == page.site:
                        backpage = pywikibot.Page(link)
                        break
                if not backpage:
                    pywikibot.output(u"%s -> no back interwiki ref" % page.title())
                elif backpage == page:
                    # everything is ok
                    yield ourpage
                elif backpage.isRedirectPage():
                    backpage = backpage.getRedirectTarget()
                    if backpage == page:
                        # everything is ok
                        yield ourpage
                    else:
                        pywikibot.output(
                            u"%s -> back interwiki ref target is redirect to %s"
                            % (page.title(), backpage.title()))
                else:
                    pywikibot.output(u"%s -> back interwiki ref target is %s"
                                     % (page.title(), backpage.title()))

    def getTemplateList(self, code, task):
        add_templates = []
        remove_templates = []
        if task == 'featured':
            try:
                add_templates = template[code]
                add_templates += template['_default']
            except KeyError:
                add_templates = template['_default']
            try:
                remove_templates = template_good[code]
                remove_templates += template_good['_default']
            except KeyError:
                remove_templates = template_good['_default']
        elif task == 'good':
            try:
                add_templates = template_good[code]
                add_templates += template_good['_default']
            except KeyError:
                add_templates = template_good['_default']
            try:
                remove_templates = template[code]
                remove_templates += template['_default']
            except KeyError:
                remove_templates = template['_default']
        elif task == 'lists':
            try:
                add_templates = template_lists[code]
                add_templates += template_lists['_default']
            except KeyError:
                add_templates = template_lists['_default']
        else:  # task == 'former'
            try:
                remove_templates = template[code]
                remove_templates += template['_default']
            except KeyError:
                remove_templates = template['_default']
        return add_templates, remove_templates

    def featuredWithInterwiki(self, fromsite, task):
        """Read featured articles and find the corresponding pages.

        Find corresponding pages on other sites, place the template and
        remember the page in the cache dict.

        """
        tosite = self.site
        if fromsite.code not in self.cache:
            self.cache[fromsite.code] = {}
        if tosite.code not in self.cache[fromsite.code]:
            self.cache[fromsite.code][tosite.code] = {}
        cc = self.cache[fromsite.code][tosite.code]
        if self.getOption('nocache') is True or \
           fromsite.code in self.getOption('nocache'):
            cc = {}

        gen = self.featuredArticles(fromsite, task, cc)
        if self.getOption('count'):
            next(gen, None)
            return  # count only, we are ready here
        gen = PreloadingGenerator(gen)

        for source in gen:
            if source.isRedirectPage():
                source = source.getRedirectTarget()

            if not source.exists():
                pywikibot.output(u"source page doesn't exist: %s"
                                 % source)
                continue

            for dest in self.findTranslated(source, tosite):
                self.add_template(source, dest, task, fromsite)
                cc[source.title()] = dest.title()

    def add_template(self, source, dest, task, fromsite):
        """Place or remove the Link_GA/FA template on/from a page."""
        def compile_link(site, templates):
            """Compile one link template list."""
            findtemplate = '(%s)' % '|'.join(templates)
            return re.compile(r"\{\{%s\|%s\}\}"
                              % (findtemplate.replace(u' ', u'[ _]'),
                                 site.code), re.IGNORECASE)

        tosite = dest.site
        add_tl, remove_tl = self.getTemplateList(tosite.code, task)
        re_Link_add = compile_link(fromsite, add_tl)
        re_Link_remove = compile_link(fromsite, remove_tl)

        text = dest.text
        m1 = add_tl and re_Link_add.search(text)
        m2 = remove_tl and re_Link_remove.search(text)
        changed = False
        interactive = self.getOption('interactive')
        if add_tl:
            if m1:
                pywikibot.output(u"(already added)")
            else:
                # insert just before interwiki
                if (not interactive or
                    pywikibot.input_yn(
                        u'Connecting %s -> %s. Proceed?'
                        % (source.title(), dest.title()),
                        default=False, automatic_quit=False)):
                    if self.getOption('side'):
                        # Placing {{Link FA|xx}} right next to
                        # corresponding interwiki
                        text = (text[:m1.end()] +
                                u" {{%s|%s}}" % (add_tl[0], fromsite.code) +
                                text[m1.end():])
                    else:
                        # Moving {{Link FA|xx}} to top of interwikis
                        iw = textlib.getLanguageLinks(text, tosite)
                        text = textlib.removeLanguageLinks(text, tosite)
                        text += u"%s{{%s|%s}}%s" % (config.LS, add_tl[0],
                                                    fromsite.code, config.LS)
                        text = textlib.replaceLanguageLinks(text,
                                                            iw, tosite)
                    changed = True
        if remove_tl:
            if m2:
                if (changed or  # Don't force the user to say "Y" twice
                    not interactive or
                    pywikibot.input_yn(
                        u'Connecting %s -> %s. Proceed?'
                        % (source.title(), dest.title()),
                        default=False, automatic_quit=False)):
                    text = re.sub(re_Link_remove, '', text)
                    changed = True
            elif task == 'former':
                pywikibot.output(u"(already removed)")
        if changed:
            comment = i18n.twtranslate(tosite, 'featured-' + task,
                                       {'page': source})
            try:
                dest.put(text, comment)
                self._save_counter += 1
            except pywikibot.LockedPage:
                pywikibot.output(u'Page %s is locked!'
                                 % dest.title())
            except pywikibot.PageNotSaved:
                pywikibot.output(u"Page not saved")


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    options = {}
    local_args = pywikibot.handle_args(args)

    issue_deprecation_warning(
        'featured.py script', 'Wikibase Client extension',
        0, UserWarning)

    for arg in local_args:
        if arg.startswith('-fromlang:'):
            options[arg[1:9]] = arg[10:].split(",")
        elif arg.startswith('-after:'):
            options['afterpage'] = arg[7:]
        elif arg.startswith('-nocache:'):
            options[arg[1:8]] = arg[9:].split(",")
        else:
            options[arg[1:].lower()] = True

    bot = FeaturedBot(**options)
    bot.run()


if __name__ == "__main__":
    main()
