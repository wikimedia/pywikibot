#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
With this tool you can add the template {{commonscat}} to categories.

The tool works by following the interwiki links. If the template is present on
another language page, the bot will use it.

You could probably use it at articles as well, but this isn't tested.

The following parameters are supported:

-always           Don't prompt you for each replacement. Warning message
                  has not to be confirmed. ATTENTION: Use this with care!

-summary:XYZ      Set the action summary message for the edit to XYZ,
                  otherwise it uses messages from add_text.py as default.

-checkcurrent     Work on all category pages that use the primary commonscat
                  template.

This bot uses pagegenerators to get a list of pages. The following options are
supported:

&params;

For example to go through all categories:

    python pwb.py commonscat -start:Category:!
"""
# Commonscat bot:
#
# Take a page. Follow the interwiki's and look for the commonscat template
# *Found zero templates. Done.
# *Found one template. Add this template
# *Found more templates. Ask the user <- still have to implement this
#
# (C) Pywikibot team, 2008-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import re

import pywikibot

from pywikibot import i18n, pagegenerators
from pywikibot.bot import SingleSiteBot, ExistingPageBot, NoRedirectPageBot

from scripts.add_text import add_text

docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

# Primary template, list of alternatives
# No entry needed if it is like _default
commonscatTemplates = {
    '_default': ('Commonscat', []),
    'af': ('CommonsKategorie', ['commonscat']),
    'an': ('Commonscat', ['Commons cat']),
    'ar': ('تصنيف كومنز',
           ['Commonscat', 'تصنيف كومونز', 'تك', 'Commons cat', 'CommonsCat']),
    'arz': ('Commons cat', ['Commoncat']),
    'az': ('CommonsKat', ['Commonscat']),
    'bn': ('কমন্সক্যাট', ['Commonscat']),
    'ca': ('Commonscat', ['Commons cat', 'Commons category']),
    'ckb': ('پۆلی کۆمنز', ['Commonscat', 'Commons cat', 'Commons category']),
    'crh': ('CommonsKat', ['Commonscat']),
    'cs': ('Commonscat', ['Commons cat']),
    'da': ('Commonscat',
           ['Commons cat', 'Commons category', 'Commonscat left',
            'Commonscat2']),
    'en': ('Commons category',
           ['Commoncat', 'Commonscat', 'Commons cat', 'Commons+cat',
            'Commonscategory', 'Commons and category', 'Commonscat-inline',
            'Commons category-inline', 'Commons2', 'Commons category multi',
            'Cms-catlist-up', 'Catlst commons', 'Commonscat show2',
            'Sister project links']),
    'es': ('Commonscat',
           ['Ccat', 'Commons cat', 'Categoría Commons',
            'Commonscat-inline']),
    'et': ('Commonsi kategooria',
           ['Commonscat', 'Commonskat', 'Commons cat', 'Commons category']),
    'eu': ('Commonskat', ['Commonscat']),
    'fa': ('ویکی‌انبار-رده',
           ['Commonscat', 'Commons cat', 'انبار رده', 'Commons category',
            'انبار-رده', 'جعبه پیوند به پروژه‌های خواهر',
            'در پروژه‌های خواهر', 'پروژه‌های خواهر']),
    'fr': ('Commonscat', ['CommonsCat', 'Commons cat', 'Commons category']),
    'frp': ('Commonscat', ['CommonsCat']),
    'ga': ('Catcómhaoin', ['Commonscat']),
    'he': ('ויקישיתוף בשורה', []),
    'hi': ('Commonscat', ['Commons2', 'Commons cat', 'Commons category']),
    'hu': ('Commonskat', ['Közvagyonkat']),
    'hy': ('Վիքիպահեստ կատեգորիա',
           ['Commonscat', 'Commons cat', 'Commons category']),
    'id': ('Commonscat',
           ['Commons cat', 'Commons2', 'CommonsCat', 'Commons category']),
    'is': ('CommonsCat', ['Commonscat']),
    'ja': ('Commonscat', ['Commons cat', 'Commons category']),
    'jv': ('Commonscat', ['Commons cat']),
    'kaa': ('Commons cat', ['Commonscat']),
    'kk': ('Commonscat', ['Commons2']),
    'ko': ('Commonscat', ['Commons cat', '공용분류']),
    'la': ('CommuniaCat', []),
    'mk': ('Ризница-врска',
           ['Commonscat', 'Commons cat', 'CommonsCat', 'Commons2',
            'Commons category']),
    'ml': ('Commonscat', ['Commons cat', 'Commons2']),
    'ms': ('Kategori Commons', ['Commonscat', 'Commons category']),
    'ne': ('कमन्सश्रेणी', ['Commonscat']),
    'nn': ('Commonscat', ['Commons cat']),
    'os': ('Commonscat', ['Commons cat']),
    'pt': ('Commonscat', ['Commons cat']),
    'ro': ('Commonscat', ['Commons cat']),
    'ru': ('Commonscat', ['Викисклад-кат', 'Commons category']),
    'sco': ('Commons category', ['Commonscat', 'Commons cat']),
    'simple': ('Commonscat',
               ['Commons cat', 'Commons cat multi', 'Commons category',
                'Commons category multi', 'CommonsCompact',
                'Commons-inline']),
    'sh': ('Commonscat', ['Commons cat']),
    'sl': ('Kategorija v Zbirki',
           ['Commonscat', 'Kategorija v zbirki', 'Commons cat',
            'Katzbirke']),
    'sr': ('Commons category',
           ['Commonscat', 'Commons cat', 'Категорија на Остави']),
    'sq': ('Commonscat', ['Commonskat', 'Commonsart', 'CommonsCat']),
    'sv': ('Commonscat',
           ['Commonscat-rad', 'Commonskat', 'Commons cat', 'Commonscatbox',
            'Commonscat-box']),
    'sw': ('Commonscat', ['Commons2', 'Commons cat']),
    'te': ('Commonscat', ['Commons cat']),
    'tr': ('Commons kategori',
           ['CommonsKat', 'Commonscat', 'Commons cat']),
    'uk': ('Commonscat', ['Commons cat', 'Category', 'Commonscat-inline']),
    'ur': ('زمرہ کومنز',
           ['Commonscat', 'زمرہ العام', 'Commons cat', 'CommonsCat']),
    'vi': ('Commonscat',
           ['Commons2', 'Commons cat', 'Commons category', 'Commons+cat']),
    'yi': ('קאמאנסקאט', ['Commonscat']),
    'zh': ('Commonscat', ['Commons cat', 'Commons category']),
    'zh-classical': ('共享類', ['Commonscat']),
    'zh-yue': ('同享類',
               ['Commonscat', '共享類 ', 'Commons cat', 'Commons category']),
}

ignoreTemplates = {
    'af': ['commons'],
    'ar': ['تحويلة تصنيف', 'كومنز', 'كومونز', 'Commons'],
    'be-tarask': ['Commons', 'Commons category'],
    'cs': ['Commons', 'Sestřičky', 'Sisterlinks'],
    'da': ['Commons', 'Commons left', 'Commons2', 'Commonsbilleder',
           'Commonskat', 'Commonscat2', 'GalleriCommons', 'Søsterlinks'],
    'de': ['Commons', 'ZhSZV', 'Bauwerk-stil-kategorien',
           'Bauwerk-funktion-kategorien', 'KsPuB',
           'Kategoriesystem Augsburg-Infoleiste',
           'Kategorie Ge', 'Kategorie v. Chr. Ge',
           'Kategorie Geboren nach Jh. v. Chr.', 'Kategorie Geboren nach Jh.',
           '!Kategorie Gestorben nach Jh. v. Chr.',
           '!Kategorie Gestorben nach Jh.',
           'Kategorie Jahr', 'Kategorie Jahr v. Chr.',
           'Kategorie Jahrzehnt', 'Kategorie Jahrzehnt v. Chr.',
           'Kategorie Jahrhundert', 'Kategorie Jahrhundert v. Chr.',
           'Kategorie Jahrtausend', 'Kategorie Jahrtausend v. Chr.'],
    'en': ['Category redirect', 'Commons', 'Commonscat1A', 'Commoncats',
           'Commonscat4Ra',
           'Sisterlinks', 'Sisterlinkswp', 'Sister project links',
           'Tracking category', 'Template category', 'Wikipedia category'],
    'eo': ['Commons',
           ('Projekto/box', 'commons='),
           ('Projekto', 'commons='),
           ('Projektoj', 'commons='),
           ('Projektoj', 'commonscat=')],
    'es': ['Commons', 'IprCommonscat'],
    'eu': ['Commons'],
    'fa': ['Commons', 'ویکی‌انبار', 'Category redirect', 'رده بهتر',
           'جعبه پیوند به پروژه‌های خواهر', 'در پروژه‌های خواهر',
           'پروژه‌های خواهر'],
    'fi': ['Commonscat-rivi', 'Commons-rivi', 'Commons'],
    'fr': ['Commons', 'Commons-inline', ('Autres projets', 'commons=')],
    'fy': ['Commons', 'CommonsLyts'],
    'he': ['מיזמים'],
    'hr': ['Commons', ('WProjekti', 'commonscat=')],
    'is': ['Systurverkefni', 'Commons'],
    'it': [('Ip', 'commons='), ('Interprogetto', 'commons=')],
    'ja': ['CommonscatS', 'SisterlinksN', 'Interwikicat'],
    'ms': ['Commons', 'Sisterlinks', 'Commons cat show2'],
    'nds-nl': ['Commons'],
    'nl': ['Commons', 'Commonsklein', 'Commonscatklein', 'Catbeg',
           'Catsjab', 'Catwiki'],
    'om': ['Commons'],
    'pt': ['Correlatos',
           'Commons',
           'Commons cat multi',
           'Commons1',
           'Commons2'],
    'simple': ['Sisterlinks'],
    'ru': ['Навигация', 'Навигация для категорий', 'КПР', 'КБР',
           'Годы в России', 'commonscat-inline'],
    'tt': ['Навигация'],
    'zh': ['Category redirect', 'cr', 'Commons',
           'Sisterlinks', 'Sisterlinkswp',
           'Tracking category', 'Trackingcatu',
           'Template category', 'Wikipedia category'
           '分类重定向', '追蹤分類', '共享資源', '追蹤分類'],
}


class CommonscatBot(SingleSiteBot, ExistingPageBot, NoRedirectPageBot):

    """Commons categorisation bot."""

    def __init__(self, **kwargs):
        """Initializer."""
        self.availableOptions.update({
            'summary': None,
        })
        super(CommonscatBot, self).__init__(**kwargs)

    def skip_page(self, page):
        """Skip category redirects or disambigs."""
        if page.isCategoryRedirect():
            pywikibot.warning(
                'Page {page} on {page.site} is a category redirect. '
                'Skipping.'.format(page=page))
            return True
        if page.isDisambig():
            pywikibot.warning(
                'Page {page} on {page.site} is a disambiguation. '
                'Skipping.'.format(page=page))
            return True
        return super(CommonscatBot, self).skip_page(page)

    def skipPage(self, page):
        """Determine if the page should be skipped."""
        if page.site.code in ignoreTemplates:
            templatesInThePage = page.templates()
            templatesWithParams = page.templatesWithParams()
            for template in ignoreTemplates[page.site.code]:
                if not isinstance(template, tuple):
                    for pageTemplate in templatesInThePage:
                        if pageTemplate.title(with_ns=False) == template:
                            return True
                else:
                    for (inPageTemplate, param) in templatesWithParams:
                        if inPageTemplate.title(with_ns=False) == template[0] \
                           and template[1] in param[0].replace(' ', ''):
                            return True
        return False

    def treat_page(self):
        """
        Add CommonsCat template to page.

        Take a page. Go to all the interwiki page looking for a commonscat
        template. When all the interwiki's links are checked and a proper
        category is found add it to the page.
        """
        page = self.current_page
        # Get the right templates for this page
        primaryCommonscat, commonscatAlternatives = i18n.translate(
            page.site.code, commonscatTemplates,
            fallback=i18n.DEFAULT_FALLBACK)
        commonscatLink = self.getCommonscatLink(page)
        if commonscatLink:
            pywikibot.output('Commonscat template is already on '
                             + page.title())
            (currentCommonscatTemplate,
             currentCommonscatTarget, LinkText, Note) = commonscatLink
            checkedCommonscatTarget = self.checkCommonscatLink(
                currentCommonscatTarget)

            if (currentCommonscatTarget == checkedCommonscatTarget):
                # The current commonscat link is good
                pywikibot.output('Commonscat link at {} to Category:{} is ok'
                                 .format(page.title(),
                                         currentCommonscatTarget))
                return

            if checkedCommonscatTarget:
                # We have a new Commonscat link, replace the old one
                self.changeCommonscat(page, currentCommonscatTemplate,
                                      currentCommonscatTarget,
                                      primaryCommonscat,
                                      checkedCommonscatTarget, LinkText, Note)
                return

            # Commonscat link is wrong
            commonscatLink = self.findCommonscatLink(page)
            if commonscatLink:
                self.changeCommonscat(page, currentCommonscatTemplate,
                                      currentCommonscatTarget,
                                      primaryCommonscat, commonscatLink)
            # TODO: if the commonsLink == '', should it be removed?

        elif self.skipPage(page):
            pywikibot.output('Found a template in the skip list. Skipping '
                             + page.title())
        else:
            commonscatLink = self.findCommonscatLink(page)
            if commonscatLink:
                if commonscatLink == page.title():
                    textToAdd = '{{%s}}' % primaryCommonscat
                else:
                    textToAdd = '{{%s|%s}}' % (primaryCommonscat,
                                               commonscatLink)
                _, _, always = add_text(page, textToAdd,
                                        self.getOption('summary'),
                                        always=self.getOption('always'))
                self.options['always'] = always

    def changeCommonscat(
            self, page=None, oldtemplate='', oldcat='',
            newtemplate='', newcat='', linktitle='',
            description=NotImplemented):
        """Change the current commonscat template and target."""
        if oldcat == '3=S' or linktitle == '3=S':
            return  # TODO: handle additional param on de-wiki
        if not linktitle and (page.title().lower() in oldcat.lower()
                              or oldcat.lower() in page.title().lower()):
            linktitle = oldcat
        if linktitle and newcat != page.title(with_ns=False):
            newtext = re.sub(r'(?i)\{\{%s\|?[^{}]*(?:\{\{.*\}\})?\}\}'
                             % oldtemplate,
                             '{{%s|%s|%s}}' % (newtemplate, newcat, linktitle),
                             page.get())
        elif newcat == page.title(with_ns=False):
            newtext = re.sub(r'(?i)\{\{%s\|?[^{}]*(?:\{\{.*\}\})?\}\}'
                             % oldtemplate,
                             '{{%s}}' % newtemplate,
                             page.get())
        elif oldcat.strip() != newcat:  # strip trailing white space
            newtext = re.sub(r'(?i)\{\{%s\|?[^{}]*(?:\{\{.*\}\})?\}\}'
                             % oldtemplate,
                             '{{%s|%s}}' % (newtemplate, newcat),
                             page.get())
        else:  # nothing left to do
            return
        if self.getOption('summary'):
            comment = self.getOption('summary')
        else:
            comment = i18n.twtranslate(page.site,
                                       'commonscat-msg_change',
                                       {'oldcat': oldcat, 'newcat': newcat})

        self.userPut(page, page.text, newtext, summary=comment,
                     ignore_save_related_errors=True)

    def findCommonscatLink(self, page=None):
        """Find CommonsCat template on interwiki pages.

        In Pywikibot >=2.0, page.interwiki() now returns Link objects,
        not Page objects

        @return: name of a valid commons category
        @rtype: str
        """
        for ipageLink in page.langlinks():
            ipage = pywikibot.page.Page(ipageLink)
            pywikibot.log('Looking for template on ' + ipage.title())
            try:
                if (not ipage.exists() or ipage.isRedirectPage()
                        or ipage.isDisambig()):
                    continue
                commonscatLink = self.getCommonscatLink(ipage)
                if not commonscatLink:
                    continue
                (currentTemplate,
                 possibleCommonscat, linkText, Note) = commonscatLink
                checkedCommonscat = self.checkCommonscatLink(
                    possibleCommonscat)
                if checkedCommonscat:
                    pywikibot.output(
                        'Found link for {} at [[{}:{}]] to {}.'
                        .format(page.title(), ipage.site.code, ipage.title(),
                                checkedCommonscat))
                    return checkedCommonscat
            except pywikibot.BadTitle:
                # The interwiki was incorrect
                return ''
        return ''

    def getCommonscatLink(self, wikipediaPage=None):
        """Find CommonsCat template on page.

        @rtype: tuple of (<templatename>, <target>, <linktext>, <note>)
        """
        primaryCommonscat, commonscatAlternatives = i18n.translate(
            wikipediaPage.site.code, commonscatTemplates,
            fallback=i18n.DEFAULT_FALLBACK)
        commonscatLinktext = ''
        commonscatNote = ''
        # See if commonscat is present
        for template in wikipediaPage.templatesWithParams():
            templateTitle = template[0].title(with_ns=False)
            if templateTitle == primaryCommonscat \
               or templateTitle in commonscatAlternatives:
                commonscatTemplate = templateTitle
                if (len(template[1]) > 0):
                    commonscatTarget = template[1][0]
                    if len(template[1]) > 1:
                        commonscatLinktext = template[1][1]
                    if len(template[1]) > 2:
                        commonscatNote = template[1][2]
                else:
                    commonscatTarget = wikipediaPage.title(with_ns=False)
                return (commonscatTemplate, commonscatTarget,
                        commonscatLinktext, commonscatNote)
        return None

    def checkCommonscatLink(self, name=''):
        """Return the name of a valid commons category.

        If the page is a redirect this function tries to follow it.
        If the page doesn't exists the function will return an empty string

        """
        pywikibot.log('getCommonscat: ' + name)
        commonsSite = self.site.image_repository()

        try:
            # This can throw a pywikibot.BadTitle
            commonsPage = pywikibot.Page(commonsSite, 'Category:' + name)
        except pywikibot.BadTitle:
            # Funky title so not correct
            return ''

        if not commonsPage.exists():
            pywikibot.output('Commons category does not exist. '
                             'Examining deletion log...')
            logpages = commonsSite.logevents(logtype='delete',
                                             page=commonsPage)
            for logitem in logpages:
                loguser = logitem.user()
                logcomment = logitem.comment()
                # Some logic to extract the target page.
                regex = (
                    r'moved to \[\[\:?Category:'
                    r'(?P<newcat1>[^\|\}]+)(\|[^\}]+)?\]\]|'
                    r'Robot: Changing Category:(.+) '
                    r'to Category:(?P<newcat2>.+)')
                m = re.search(regex, logcomment, flags=re.I)
                if m:
                    if m.group('newcat1'):
                        return self.checkCommonscatLink(m.group('newcat1'))
                    elif m.group('newcat2'):
                        return self.checkCommonscatLink(m.group('newcat2'))
                else:
                    pywikibot.output(
                        "getCommonscat: {} deleted by {}. Couldn't find "
                        'move target in "{}"'
                        .format(commonsPage, loguser, logcomment))
                    return ''
            return ''
        elif commonsPage.isRedirectPage():
            pywikibot.log('getCommonscat: The category is a redirect')
            return self.checkCommonscatLink(
                commonsPage.getRedirectTarget().title(with_ns=False))
        elif (pywikibot.Page(commonsPage.site,
              'Template:Category redirect') in commonsPage.templates()):
            pywikibot.log(
                'getCommonscat: The category is a category redirect')
            for template in commonsPage.templatesWithParams():
                if (
                    template[0].title(with_ns=False) == 'Category redirect'
                    and len(template[1]) > 0
                ):
                    return self.checkCommonscatLink(template[1][0])
        elif commonsPage.isDisambig():
            pywikibot.log('getCommonscat: The category is disambiguation')
            return ''

        return commonsPage.title(with_ns=False)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    options = {}
    checkcurrent = False

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        opt, _, value = arg.partition(':')
        option = opt[1:] if opt[0] == '-' else None
        if option == 'summary':
            options[option] = value or pywikibot.input(
                'What summary do you want to use?')
        elif option == 'checkcurrent':
            checkcurrent = True
        elif option == 'always':
            options[option] = True
        else:
            genFactory.handleArg(arg)

    if checkcurrent:
        site = pywikibot.Site()
        primaryCommonscat, commonscatAlternatives = i18n.translate(
            site.code, commonscatTemplates, fallback=i18n.DEFAULT_FALLBACK)
        template_page = pywikibot.Page(site, 'Template:' + primaryCommonscat)
        generator = template_page.getReferences(namespaces=14,
                                                only_template_inclusion=True)
    else:
        generator = genFactory.getCombinedGenerator()

    if generator:
        if not genFactory.nopreload:
            generator = pagegenerators.PreloadingGenerator(generator)
        bot = CommonscatBot(generator=generator, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
