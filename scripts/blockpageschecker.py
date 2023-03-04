#!/usr/bin/env python3
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

This script is a :py:obj:`ConfigParserBot <bot.ConfigParserBot>`.
The following options can be set within a settings file which is scripts.ini
by default::

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
# (C) Pywikibot team, 2007-2022
#
# Distributed under the terms of the MIT license.
#
import re
import webbrowser
from collections import namedtuple
from itertools import chain
from typing import Optional

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import ConfigParserBot, ExistingPageBot, SingleSiteBot
from pywikibot.editor import TextEditor
from pywikibot.exceptions import Error


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {  # noqa: N816
    '&params;': pagegenerators.parameterHelp,
}

# PREFERENCES

template_semi_protection = {
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
template_total_protection = {
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
template_semi_move_protection = {
    'it': [r'\{\{(?:[Tt]emplate:|)[Aa]vvisobloccospostamento(?:|[ _]scad\|.*?'
           r'|\|.*?)\}\}'],
    'ja': [r'(?<!\<nowiki\>)\{\{(?:[Tt]emplate:|)移動半保護'
           r'(?:[Ss]|)(?:\|.+|)\}\}(?!\<\/nowiki\>)\s*'],
}

# Regex to get the total-protection move template
template_total_move_protection = {
    'it': [r'\{\{(?:[Tt]emplate:|)[Aa]vvisobloccospostamento(?:|[ _]scad\|.*?'
           r'|\|.*?)\}\}'],
    'ja': [r'(?<!\<nowiki\>)\{\{(?:[Tt]emplate:|)移動保護'
           r'(?:[Ss]|)(?:\|.+|)\}\}(?!\<\/nowiki\>)\s*'],
}

# If you use only one template for all the type of protection, put it here.
# You may use only one template or an unique template and some other "old"
# template that the script should still check (as on it.wikipedia)
template_unique = {
    'ar': [r'\{\{(?:[Tt]emplate:|قالب:|)(محمية)\}\}'],
    'it': [r'\{\{(?:[Tt]emplate:|)[Pp]rotetta\}\}'],
}

# Array: 0 => Semi-block, 1 => Total Block, 2 => Semi-Move, 3 => Total-Move,
#        4 => template-unique
template_no_regex = {
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
category_to_check = {
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
ParsedTemplate = namedtuple('ParsedTemplate', 'blocktype, regex, msgtype')


class CheckerBot(ConfigParserBot, ExistingPageBot, SingleSiteBot):

    """Bot to remove stale protection templates from unprotected pages.

    .. versionchanged:: 7.0
       CheckerBot is a ConfigParserBot
    """

    update_options = {
        'show': False,
        'move': False,
    }

    @staticmethod
    def invoke_editor(page) -> None:
        """Ask for an editor and invoke it."""
        choice = pywikibot.input_choice(
            'Do you want to open the page?',
            [('with browser', 'b'), ('with gui', 'g'), ('no', 'n')], 'n')
        if choice == 'b':
            webbrowser.open(f'{page.full_url()}?redirect=no')
        elif choice == 'g':
            editor = TextEditor()
            editor.edit(page.text)

    def setup(self) -> None:
        """Initialize the coroutine for parsing templates."""
        self.parse_tempates = self.remove_templates()
        self.parse_tempates.send(None)

    def teardown(self) -> None:
        """Close the coroutine."""
        self.parse_tempates.close()

    def treat_page(self) -> None:
        """Load the given page, do some changes, and save it."""
        page = self.current_page
        if page.isRedirectPage():
            if self.opt.always:
                pywikibot.warning(f'{page} is a redirect; skipping')
            elif self.opt.show:
                self.invoke_editor(page)
            return

        newtext, key = self.parse_tempates.send((page.text, page.protection()))
        next(self.parse_tempates)

        if not key:
            return

        summary = i18n.twtranslate(self.site, 'blockpageschecker-' + key)
        self.userPut(page, page.text, newtext, summary=summary)

    def skip_page(self, page):
        """Skip if the user has not permission to edit."""
        # FIXME: This check does not work :
        # PreloadingGenerator cannot set correctly page.edit_restrictioniction
        # (see bug T57322)
        # if not page.has_permission():
        #    pywikibot.info(
        #        "{} is sysop-protected : this account can't edit "
        #        "it! Skipping...".format(pagename))
        #    continue
        if super().skip_page(page):
            return True

        page.protection()
        if not page.has_permission():
            pywikibot.warning(
                "{} is protected: this account can't edit it! Skipping..."
                .format(page))
            return True

        return False

    def remove_templates(self):
        """Understand if the page is blocked has the right template."""

        def understand_block():
            """Understand if the page is blocked has the right template."""
            results = 'sysop-total', 'autoconfirmed-total', 'unique'
            for index, template in enumerate((ttp, tsp, tu)):
                if not template:
                    continue

                for catch_regex in template:
                    result_catch = re.findall(catch_regex, text)
                    if result_catch:
                        return ParsedTemplate(
                            results[index], catch_regex, 'modifying')

            if tsmp and ttmp and ttp != ttmp and tsp != tsmp:
                for catch_regex in ttmp:
                    result_catch = re.findall(catch_regex, text)
                    if result_catch:
                        return ParsedTemplate(
                            'sysop-move', catch_regex, 'modifying')

                for catch_regex in tsmp:
                    result_catch = re.findall(catch_regex, text)
                    if result_catch:
                        return ParsedTemplate(
                            'autoconfirmed-move', catch_regex, 'modifying')

            # If editable means that we have no regex, won't change anything
            # with this regex
            return ParsedTemplate('editable', r'\A', 'adding')

        tsp = i18n.translate(self.site, template_semi_protection)
        ttp = i18n.translate(self.site, template_total_protection)
        tsmp = i18n.translate(self.site, template_semi_move_protection)
        ttmp = i18n.translate(self.site, template_total_move_protection)
        tnr = i18n.translate(self.site, template_no_regex)
        tu = i18n.translate(self.site, template_unique)

        while True:
            text, restrictions = yield
            if text is None:
                continue

            # Understand, according to the template in the page, what should
            # be the protection and compare it with what there really is.
            template_in_page = understand_block()

            # Only to see if the text is the same or not...
            oldtext = text
            # keep track of the changes for each step (edit then move)
            changes = -1

            msg_type: Optional[str] = None
            edit_restriction = restrictions.get('edit')
            if not edit_restriction:
                # page is not edit-protected
                # Deleting the template because the page doesn't need it.
                if not (ttp or tsp):
                    raise Error(
                        'This script is not localized to use it on {}.\n'
                        'Missing "template_semi_protection" or'
                        '"template_total_protection"'
                        .format(self.site.sitename))

                replacement = '|'.join(ttp + tsp + (tu or []))
                text, changes = re.subn(
                    f'<noinclude>({replacement})</noinclude>',
                    '', text)
                if not changes:
                    text, changes = re.subn(
                        f'({replacement})', '', text)
                msg = 'The page is editable for all'
                if not self.opt.move:
                    msg += ', deleting the template..'
                pywikibot.info(msg + '.')
                msg_type = 'deleting'

            elif edit_restriction[0] == 'sysop':
                # total edit protection
                if template_in_page.blocktype == 'sysop-total' and ttp \
                   or template_in_page.blocktype == 'unique' and tu:
                    msg = 'The page is protected to the sysop'
                    if not self.opt.move:
                        msg += ', skipping...'
                    pywikibot.info(msg)
                else:
                    if not tnr or tu and not tnr[4] or not (tu or tnr[1]):
                        raise Error(
                            'This script is not localized to use it on \n{}. '
                            'Missing "template_no_regex"'
                            .format(self.site.sitename))

                    pywikibot.info(
                        'The page is protected to the sysop, but the template '
                        'seems not correct. Fixing...')
                    text, changes = re.subn(
                        template_in_page.regex, tnr[(1, 4)[bool(tu)]], text)
                    msg_type = template_in_page.msgtype

            elif tsp or tu:
                # implicitly edit semi-protection
                if template_in_page.blocktype in ('autoconfirmed-total',
                                                  'unique'):
                    msg = ('The page is editable only for the autoconfirmed '
                           'users')
                    if not self.opt.move:
                        msg += ', skipping...'
                    pywikibot.info(msg)
                else:
                    if not tnr or tu and not tnr[4] or not (tu or tnr[1]):
                        raise Error(
                            'This script is not localized to use it on \n'
                            '{}. Missing "template_no_regex"'
                            .format(self.site.sitename))
                    pywikibot.info(
                        'The page is editable only for the autoconfirmed '
                        'users, but the template seems not correct. Fixing...')
                    text, changes = re.subn(
                        template_in_page.regex, tnr[(0, 4)[bool(tu)]], text)
                    msg_type = template_in_page.msgtype

            if not changes:
                # We tried to fix edit-protection templates, but it did
                # not work.
                pywikibot.warning('No edit-protection template could be found')

            if self.opt.move and changes > -1:
                # checking move protection now
                move_restriction = restrictions.get('move')
                changes = -1

                if not move_restriction:
                    pywikibot.info('The page is movable for all, deleting the '
                                   'template...')
                    # Deleting the template because the page doesn't need it.
                    replacement = '|'.join(tsmp + ttmp + (tu or []))
                    text, changes = re.subn(
                        f'<noinclude>({replacement})</noinclude>',
                        '', text)
                    if not changes:
                        text, changes = re.subn(
                            f'({replacement})', '', text)
                    msg_type = 'deleting'
                elif move_restriction[0] == 'sysop':
                    # move-total-protection
                    if template_in_page.blocktype == 'sysop-move' and ttmp \
                       or template_in_page.blocktype == 'unique' and tu:
                        pywikibot.info('The page is protected from moving to '
                                       'the sysop, skipping...')
                        if tu:
                            # no changes needed, better to revert the old text.
                            text = oldtext
                    else:
                        pywikibot.info(
                            'The page is protected from moving to the sysop, '
                            'but the template seems not correct. Fixing...')
                        text, changes = re.subn(
                            template_in_page.regex, tnr[3 + bool(tu)], text)
                        msg_type = template_in_page.msgtype

                elif tsmp or tu:
                    # implicitly move semi-protection
                    if template_in_page.blocktype in ('autoconfirmed-move',
                                                      'unique'):
                        pywikibot.info('The page is movable only for the '
                                       'autoconfirmed users, skipping...')
                        if tu:
                            # no changes needed, better to revert the old text.
                            text = oldtext
                    else:
                        pywikibot.info(
                            'The page is movable only for the autoconfirmed '
                            'users, but the template seems not correct. '
                            'Fixing...')
                        text, changes = re.subn(template_in_page.regex,
                                                tnr[(2, 4)[bool(tu)]], text)
                        msg_type = template_in_page.msgtype

                if not changes:
                    # We tried to fix move-protection templates
                    # but it did not work
                    pywikibot.warning(
                        'No move-protection template could be found')

            yield text, msg_type


def main(*args: str) -> None:
    """
    Process command line arguments and perform task.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    generator = None

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    site = pywikibot.Site()

    if site.code not in project_inserted:
        pywikibot.info('Your project is not supported by this script.\n'
                       'You have to edit the script and add it!')
        return

    # Process pagegenerators arguments
    gen_factory = pagegenerators.GeneratorFactory(site)
    local_args = gen_factory.handle_args(local_args)

    # Process local args
    for arg in local_args:
        arg, _, value = arg.partition(':')
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
        categories = i18n.translate(site, category_to_check)
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
