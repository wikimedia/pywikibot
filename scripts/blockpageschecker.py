#!/usr/bin/python
"""
A bot to remove stale protection templates from pages that are not protected.

Very often sysops block the pages for a set time but then they forget to
remove the warning! This script is useful if you want to remove those useless
warning left in these pages.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-protectedpages  Check all the blocked pages; useful when you have not
                 categories or when you have problems with them. (add the
                 namespace after ":" where you want to check - default checks
                 all protected pages.)

-moveprotected   Same as -protectedpages, for moveprotected pages

-always          Doesn't ask every time whether the bot should make the change.
                 Do it always.

-show            When the bot can't delete the template from the page (wrong
                 regex or something like that) it will ask you if it should
                 show the page on your browser.
                 (attention: pages included may give false positives!)

-move            The bot will check if the page is blocked also for the move
                 option, not only for edit

Examples::

    python pwb.py blockpageschecker -always

    python pwb.py blockpageschecker -cat:Geography -always

    python pwb.py blockpageschecker -show -protectedpages:4

"""
#
# (C) Pywikibot team, 2007-2021
#
# Distributed under the terms of the MIT license.
#
import re
import webbrowser

from collections import namedtuple
from itertools import chain

import pywikibot

from pywikibot import i18n, pagegenerators
from pywikibot.bot import ExistingPageBot, SingleSiteBot
from pywikibot.editor import TextEditor
from pywikibot.exceptions import Error


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}

# PREFERENCES

templateSemiProtection = {
    'ar': [r'\{\{(?:[Tt]emplate:|قالب:|)(حماية\sجزئية)\}\}'],
    'cs': [r'\{\{(?:[Tt]emplate:|[Šš]ablona:|)([Dd]louhodobě[ _]p|[Pp])'
           r'olozamčeno(|[^\}]*)\}\}\s*'],
    'fr': [r'\{\{(?:[Tt]emplate:|[Mm]odèle:|)[Ss]emi[- ]?'
           r'protection(|[^\}]*)\}\}'],
    'it': [r'\{\{(?:[Tt]emplate:|)[Aa]vvisobloccoparziale'
           r'(?:|[ _]scad\|.*?|\|.*?)\}\}',
           r'\{\{(?:[Tt]emplate:|)[Aa]bp(?:|[ _]scad\|(?:.*?))\}\}'],
    'ja': [r'(?<!\<nowiki\>)\{\{(?:[Tt]emplate:|)半保護'
           r'(?:[Ss]|)(?:\|.+|)\}\}(?!\<\/nowiki\>)\s*'],
    'sr': [r'\{\{(?:[Tt]emplate:|[Зз]акључано-анон)\}\}'],
    'ur': [r'\{\{(?:[Tt]emplate:|سانچہ:|)(نیم\sمحفوظ)\}\}']
}
# Regex to get the total-protection template
templateTotalProtection = {
    'ar': [r'\{\{(?:[Tt]emplate:|قالب:|)(حماية\sكاملة)\}\}'],
    'cs': [r'\{\{(?:[Tt]emplate:|[Šš]ablona:|)([Dd]louhodobě[ _]z|[Zz])'
           r'amčeno(|[^\}]*)\}\}\s*'],
    'fr': [r'\{\{(?:[Tt]emplate:|[Mm]odèle:|)[Pp]rotection(|[^\}]*)\}\}',
           r'\{\{(?:[Tt]emplate:|[Mm]odèle:|)(?:[Pp]age|[Aa]rchive|'
           r'[Mm]odèle) protégée?(|[^\}]*)\}\}'],
    'it': [r'\{\{(?:[Tt]emplate:|)[Aa]vvisoblocco(?:|[ _]scad\|(?:.*?)'
           r'|minaccia|cancellata)\}\}',
           r'\{\{(?:[Tt]emplate:|)(?:[Cc][Tt]|[Cc]anc fatte|[Cc][Ee])\}\}',
           r'<div class="toccolours[ _]itwiki[ _]template[ _]avviso">\s*?'
           r'[Qq]uesta pagina'],
    'ja': [r'(?<!\<nowiki\>)\{\{(?:[Tt]emplate:|)保護(?:性急|)'
           r'(?:[Ss]|)(?:\|.+|)\}\}(?!\<\/nowiki\>)\s*'],
    'sr': [r'\{\{(?:[Tt]emplate:|[Зз]акључано)\}\}'],
    'ur': [r'\{\{(?:[Tt]emplate:|سانچہ:|)(محفوظ)\}\}']
}

# Regex to get the semi-protection move template
templateSemiMoveProtection = {
    'it': [r'\{\{(?:[Tt]emplate:|)[Aa]vvisobloccospostamento(?:|[ _]scad\|.*?'
           r'|\|.*?)\}\}'],
    'ja': [r'(?<!\<nowiki\>)\{\{(?:[Tt]emplate:|)移動半保護'
           r'(?:[Ss]|)(?:\|.+|)\}\}(?!\<\/nowiki\>)\s*'],
}

# Regex to get the total-protection move template
templateTotalMoveProtection = {
    'it': [r'\{\{(?:[Tt]emplate:|)[Aa]vvisobloccospostamento(?:|[ _]scad\|.*?'
           r'|\|.*?)\}\}'],
    'ja': [r'(?<!\<nowiki\>)\{\{(?:[Tt]emplate:|)移動保護'
           r'(?:[Ss]|)(?:\|.+|)\}\}(?!\<\/nowiki\>)\s*'],
}

# If you use only one template for all the type of protection, put it here.
# You may use only one template or an unique template and some other "old"
# template that the script should still check (as on it.wikipedia)
templateUnique = {
    'ar': [r'\{\{(?:[Tt]emplate:|قالب:|)(محمية)\}\}'],
    'it': [r'\{\{(?:[Tt]emplate:|)[Pp]rotetta\}\}'],
}

# Array: 0 => Semi-block, 1 => Total Block, 2 => Semi-Move, 3 => Total-Move,
#        4 => template-unique
templateNoRegex = {
    'ar': ['{{حماية جزئية}}', '{{حماية كاملة}}', None, None, '{{محمية}}'],
    'cs': ['{{Polozamčeno}}', '{{Zamčeno}}', None, None, None],
    'fr': ['{{Semi-protection}}', '{{Protection}}', None, None, None],
    'it': ['{{Avvisobloccoparziale}}', '{{Avvisoblocco}}', None, None,
           '{{Protetta}}'],
    'ja': ['{{半保護}}', '{{保護}}', '{{移動半保護}}', '{{移動保護}}', None],
    'sr': ['{{Закључано-анон}}', '{{Закључано}}', None, None, None],
    'ur': ['{{نیم محفوظ}}', '{{محفوظ}}', None, None, None],
}

# Category where the bot will check
categoryToCheck = {
    'ar': ['تصنيف:صفحات محمية'],
    'cs': ['Kategorie:Wikipedie:Zamčené stránky',
           'Kategorie:Wikipedie:Polozamčené stránky',
           'Kategorie:Wikipedie:Dlouhodobě zamčené stránky',
           'Kategorie:Wikipedie:Dlouhodobě polozamčené stránky'],
    'fr': ['Category:Page semi-protégée', 'Category:Page protégée',
           'Catégorie:Article protégé'],
    'en': ['Category:Wikipedia protected pages'],
    'he': ['קטגוריה:ויקיפדיה: דפים מוגנים',
           'קטגוריה:ויקיפדיה: דפים מוגנים חלקית'],
    'it': ['Categoria:Pagine protette - scadute',
           'Categoria:Pagine semiprotette', 'Categoria:Voci protette'],
    'ja': ['Category:編集保護中のページ', 'Category:編集半保護中のページ',
           'Category:移動保護中のページ'],
    'pt': ['Category:!Páginas protegidas',
           'Category:!Páginas semiprotegidas'],
    'sr': ['Category:Странице закључане за анонимне кориснике',
           'Category:Закључане странице'],
    'ur': ['زمرہ:محفوظ شدہ صفحات'],
    'zh': ['Category:被保护的页面', 'Category:被保護的模板',
           'Category:暂时不能移动的页面', 'Category:被半保护的页面'],
}

# Check list to block the users that haven't set their preferences
project_inserted = ['ar', 'cs', 'fr', 'it', 'ja', 'pt', 'sr', 'ur', 'zh']

# END PREFERENCES
ParsedTemplate = namedtuple('ParsedTemplate', 'blocktype, regex')


class CheckerBot(ExistingPageBot, SingleSiteBot):

    """Bot to remove stale protection templates from unprotected pages."""

    update_options = {
        'show': False,
        'move': False,
    }

    def invoke_editor(self, page):
        """Ask for an editor and invoke it."""
        choice = pywikibot.input_choice(
            'Do you want to open the page?',
            [('with browser', 'b'), ('with gui', 'g'), ('no', 'n')], 'n')
        if choice == 'b':
            webbrowser.open('{}?redirect=no'.format(page.full_url()))
        elif choice == 'g':
            editor = TextEditor()
            editor.edit(page.text)

    def setup(self):
        """Initialize the coroutine for parsing templates."""
        self.parse_tempates = self.remove_templates()
        self.parse_tempates.send(None)

    def teardown(self):
        """Close the coroutine."""
        self.parse_tempates.close()

    def treat_page(self):
        """Load the given page, do some changes, and save it."""
        page = self.current_page
        if page.isRedirectPage():
            if self.opt.always:
                pywikibot.warning('{} is a redirect; skipping'.format(page))
            elif self.opt.show:
                self.invoke_editor(page)
            return

        newtext = self.parse_tempates.send((page.text, page.protection()))
        next(self.parse_tempates)

        commentUsed = i18n.twtranslate(self.site, 'blockpageschecker-summary')
        self.userPut(page, page.text, newtext, summary=commentUsed)

    def skip_page(self, page):
        """Skip if the user has not permission to edit."""
        # FIXME: This check does not work :
        # PreloadingGenerator cannot set correctly page.editRestriction
        # (see bug T57322)
        # if not page.has_permission():
        #    pywikibot.output(
        #        "{} is sysop-protected : this account can't edit "
        #        "it! Skipping...".format(pagename))
        #    continue
        page.protection()
        if not page.has_permission():
            pywikibot.warning(
                "{} is protected: this account can't edit it! Skipping..."
                .format(page))
            return True

        return super().skip_page(page)

    def remove_templates(self):
        """Understand if the page is blocked has the right template."""

        def understand_block():
            """Understand if the page is blocked has the right template."""
            results = 'sysop-total', 'autoconfirmed-total', 'unique'
            for index, template in enumerate((TTP, TSP, TU)):
                if not template:
                    continue

                for catchRegex in template:
                    resultCatch = re.findall(catchRegex, text)
                    if resultCatch:
                        return ParsedTemplate(results[index], catchRegex)

            if TSMP and TTMP and TTP != TTMP and TSP != TSMP:
                for catchRegex in TTMP:
                    resultCatch = re.findall(catchRegex, text)
                    if resultCatch:
                        return ParsedTemplate('sysop-move', catchRegex)

                for catchRegex in TSMP:
                    resultCatch = re.findall(catchRegex, text)
                    if resultCatch:
                        return ParsedTemplate('autoconfirmed-move', catchRegex)

            # If editable means that we have no regex, won't change anything
            # with this regex
            return ParsedTemplate('editable', r'\A\n')

        TSP = i18n.translate(self.site, templateSemiProtection)
        TTP = i18n.translate(self.site, templateTotalProtection)
        TSMP = i18n.translate(self.site, templateSemiMoveProtection)
        TTMP = i18n.translate(self.site, templateTotalMoveProtection)
        TNR = i18n.translate(self.site, templateNoRegex)
        TU = i18n.translate(self.site, templateUnique)

        while True:
            text, restrictions = yield
            if text is None:
                continue

            # Understand, according to the template in the page, what should
            # be the protection and compare it with what there really is.
            TemplateInThePage = understand_block()

            # Only to see if the text is the same or not...
            oldtext = text
            # keep track of the changes for each step (edit then move)
            changes = -1

            editRestr = restrictions.get('edit')
            if not editRestr:
                # page is not edit-protected
                # Deleting the template because the page doesn't need it.
                if not (TTP or TSP):
                    raise Error(
                        'This script is not localized to use it on {}.\n'
                        'Missing "templateSemiProtection" or'
                        '"templateTotalProtection"'.format(self.site.sitename))

                if TU:
                    replaceToPerform = '|'.join(TTP + TSP + TU)
                else:
                    replaceToPerform = '|'.join(TTP + TSP)
                text, changes = re.subn(
                    '<noinclude>({})</noinclude>'.format(replaceToPerform),
                    '', text)
                if not changes:
                    text, changes = re.subn(
                        '({})'.format(replaceToPerform), '', text)
                msg = 'The page is editable for all'
                if not self.opt.move:
                    msg += ', deleting the template..'
                pywikibot.output(msg + '.')

            elif editRestr[0] == 'sysop':
                # total edit protection
                if TemplateInThePage.blocktype == 'sysop-total' and TTP \
                   or TemplateInThePage.blocktype == 'unique' and TU:
                    msg = 'The page is protected to the sysop'
                    if not self.opt.move:
                        msg += ', skipping...'
                    pywikibot.output(msg)
                else:
                    if not TNR or TU and not TNR[4] or not (TU or TNR[1]):
                        raise Error(
                            'This script is not localized to use it on \n{}. '
                            'Missing "templateNoRegex"'
                            .format(self.site.sitename))

                    pywikibot.output(
                        'The page is protected to the sysop, but the template '
                        'seems not correct. Fixing...')
                    if TU:
                        text, changes = re.subn(
                            TemplateInThePage.regex, TNR[4], text)
                    else:
                        text, changes = re.subn(
                            TemplateInThePage.regex, TNR[1], text)

            elif TSP or TU:
                # implicitly
                # editRestr[0] = 'autoconfirmed', edit-Semi-protection
                if TemplateInThePage.blocktype in ('autoconfirmed-total',
                                                   'unique'):
                    msg = ('The page is editable only for the autoconfirmed '
                           'users')
                    if not self.opt.move:
                        msg += ', skipping...'
                    pywikibot.output(msg)
                else:
                    if not TNR or TU and not TNR[4] or not (TU or TNR[1]):
                        raise Error(
                            'This script is not localized to use it on \n'
                            '{}. Missing "templateNoRegex"'
                            .format(self.site.sitename))
                    pywikibot.output(
                        'The page is editable only for the autoconfirmed '
                        'users, but the template seems not correct. Fixing...')
                    if TU:
                        text, changes = re.subn(
                            TemplateInThePage.regex, TNR[4], text)
                    else:
                        text, changes = re.subn(
                            TemplateInThePage.regex, TNR[0], text)

            if not changes:
                # We tried to fix edit-protection templates, but it did
                # not work.
                pywikibot.warning('No edit-protection template could be found')

            if self.opt.move and changes > -1:
                # checking move protection now
                moveRestr = restrictions.get('move')
                changes = -1

                if not moveRestr:
                    pywikibot.output('The page is movable for all, deleting '
                                     'the template...')
                    # Deleting the template because the page doesn't need it.
                    if TU:
                        replaceToPerform = '|'.join(TSMP + TTMP + TU)
                    else:
                        replaceToPerform = '|'.join(TSMP + TTMP)
                    text, changes = re.subn(
                        '<noinclude>({})</noinclude>'.format(replaceToPerform),
                        '', text)
                    if not changes:
                        text, changes = re.subn(
                            '({})'.format(replaceToPerform), '', text)
                elif moveRestr[0] == 'sysop':
                    # move-total-protection
                    if TemplateInThePage.blocktype == 'sysop-move' and TTMP \
                       or TemplateInThePage.blocktype == 'unique' and TU:
                        pywikibot.output('The page is protected from moving '
                                         'to the sysop, skipping...')
                        if TU:
                            # no changes needed, better to revert the old text.
                            text = oldtext
                    else:
                        pywikibot.output(
                            'The page is protected from moving to the sysop, '
                            'but the template seems not correct. Fixing...')
                        if TU:
                            text, changes = re.subn(
                                TemplateInThePage.regex, TNR[4], text)
                        else:
                            text, changes = re.subn(
                                TemplateInThePage.regex, TNR[3], text)

                elif TSMP or TU:
                    # implicitly
                    # moveRestr[0] = 'autoconfirmed', move-semi-protection
                    if TemplateInThePage.blocktype in ('autoconfirmed-move',
                                                       'unique'):
                        pywikibot.output('The page is movable only for the '
                                         'autoconfirmed users, skipping...')
                        if TU:
                            # no changes needed, better to revert the old text.
                            text = oldtext
                    else:
                        pywikibot.output(
                            'The page is movable only for the autoconfirmed '
                            'users, but the template seems not correct. '
                            'Fixing...')
                        if TU:
                            text, changes = re.subn(
                                TemplateInThePage.regex, TNR[4], text)
                        else:
                            text, changes = re.subn(
                                TemplateInThePage.regex, TNR[2], text)

                if not changes:
                    # We tried to fix move-protection templates
                    # but it did not work
                    pywikibot.warning(
                        'No move-protection template could be found')

            yield text


def main(*args: str) -> None:
    """
    Process command line arguments and perform task.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    # Loading the comments
    global categoryToCheck, project_inserted

    options = {}
    generator = None

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    site = pywikibot.Site()

    if site.code not in project_inserted:
        pywikibot.output('Your project is not supported by this script.\n'
                         'You have to edit the script and add it!')
        return

    # Process pagegenerators arguments
    gen_factory = pagegenerators.GeneratorFactory(site)
    local_args = gen_factory.handle_args(local_args)

    # Process local args
    for arg in local_args:
        arg, sep, value = arg.partition(':')
        option = arg[1:]
        if arg in ('-always', '-move', '-show'):
            options[option] = True
        elif arg in ('-protectedpages', '-moveprotected'):
            protect_type = 'move' if option.startswith('move') else 'edit'
            generator = site.protectedpages(namespace=int(value or 0),
                                            type=protect_type)

    if not generator:
        generator = gen_factory.getCombinedGenerator()

    if not generator:
        # Define the category if no other generator has been set
        gen = []
        categories = i18n.translate(site, categoryToCheck)
        for category_name in categories:
            cat = pywikibot.Category(site, category_name)
            # Define the generator
            gen.append(pagegenerators.CategorizedPageGenerator(cat))
        generator = chain.from_iterable(gen)

    if not gen_factory.nopreload:
        generator = pagegenerators.PreloadingGenerator(generator, groupsize=60)

    bot = CheckerBot(site=site, generator=generator, **options)
    bot.run()


if __name__ == '__main__':
    main()
