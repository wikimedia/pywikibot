#!/usr/bin/env python3
"""
This bot resets a (user) sandbox with predefined text.

This script understands the following command-line arguments:

&params;

Furthermore, the following command line parameters are supported:

    -hours:#       Use this parameter if to make the script repeat itself
                   after # hours. Hours can be defined as a decimal. 0.01
                   hours are 36 seconds; 0.1 are 6 minutes.

    -delay:#       Use this parameter for a wait time after the last edit
                   was made. If no parameter is given it takes it from
                   hours and limits it between 5 and 15 minutes.
                   The minimum delay time is 5 minutes.

    -text          The text that substitutes in the sandbox, you can use this
                   when you haven't configured clean_sandbox for your wiki.

    -textfile      As an alternative to -text, you can use this to provide
                   a file containing the text to be used.

    -summary       Summary of the edit made by the bot. Overrides the default
                   from i18n.

This script is a :py:obj:`ConfigParserBot <bot.ConfigParserBot>`.
All local parameters can be given inside a scripts.ini file. Options
passed to the script are priorized over options read from ini file.

.. seealso:: :python:`Supported .ini File Structure
   <library/configparser.html#supported-ini-file-structure>`

For example:

    [clean_sandbox]
    # the parameter section for clean_sandbox script
    summary = Bot: Cleaning sandbox
    text = {{subst:Clean Sandbox}}
    hours: 0.5
    delay: 7
"""
#
# (C) Pywikibot team, 2006-2023
#
# Distributed under the terms of the MIT license.
#
import datetime
import sys
import time

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import Bot, ConfigParserBot
from pywikibot.exceptions import EditConflictError, NoPageError


content = {
    'commons': '{{Sandbox}}\n<!-- Please edit only below this line. -->',
    'meta': '{{Meta:Sandbox/Please do not edit this line}}\n'
            '<!-- Please edit below this line. -->',
    'species': '{{Sandbox}}\n'
               '<!-- PLEASE ADD YOUR EDITS BELOW THIS LINE. THANK YOU. -->',
    'test': '<noinclude>{{Sandbox}}</noinclude>\n'
            '== Please start your testing below this line ==',
    'wikidata': '{{Please leave this line alone (sandbox heading)}}',
    'wikibooks': {
        'es': '{{ZDP}}\n== Haz tus pruebas bajo esta sección  ==',
        'ru': '{{/Шапка}}\n'
              '<!-- Не удаляйте, пожалуйста, эту строку, '
              'тестируйте ниже -->',
    },
    'wikinews': {
        'es': '{{ZDP}}\n== Haz tus pruebas bajo esta sección  ==',
    },
    'wikiquote': {
        'es': '{{ZDP}}\n== Haz tus pruebas bajo esta sección  ==',
    },
    'wikisource': {
        'es': '<!--No borres este mensaje-->'
              '{{Zona de pruebas}}'
              '<!--Haz las pruebas debajo. Gracias-->\n',
    },
    'wikiversity': {
        'es': '{{/encabezado}}\n'
              '== Haz tus pruebas bajo esta sección  ==',
    },
    'wikivoyage': {
        'es': '<!--No borres este mensaje-->{{Zona de pruebas}}'
              '<!--Haz las pruebas debajo. Gracias-->\n'
              '== Haz tus pruebas bajo esta sección ==',
    },
    'wiktionary': {
        'es': '<!--No borres este mensaje-->{{Titular-zdp}}'
              '<!--Haz las pruebas debajo. Gracias-->',
    },
    'als': '{{subst:/Vorlage}}',
    'ar': '{{عنوان الملعب}}\n<!-- مرحبا! خذ راحتك في تجربة مهارتك في التنسيق '
          'والتحرير أسفل هذا السطر. هذه الصفحة لتجارب التعديل ، سيتم تفريغ '
          'هذه الصفحة كل 12 ساعة. -->',
    'ary': '{{راس تيران}}<!--'
           '\n*               مرحبا بيك ف تّيران د رّملة!              *'
           '\n*            عافاك خلي هاد لپارتية ف بلاصتها            *'
           '\n*        هاد لپاج كيتّمحا لمحتوى ديالها بشكل معاود      *'
           '\n*    تريني هنا ؤ تعلم معا راسك كيفاش تكتب ف ويكيپيديا  *'
           '\n■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■-->'
           '\n\n[[تصنيف:معاونة ف لكتابة علا ويكيپيديا]]',
    'arz': '{{عنوان السبوره}}\n<!-- مرحبا! خد راحتك فى تجريب مهاراتك فى'
           'التحرير تحت الخط ده. بما إن الصفحه دى لتجارب التعديل، فالصفحه دى '
           'حيتم تنضيفها اوتوماتيكيا كل 12 ساعه. -->',
    'az': '<!--- LÜTFƏN, BU SƏTRƏ TOXUNMAYIN --->\n{{Qaralama dəftəri}}\n'
          '<!-- AŞAĞIDAKI XƏTTİN ALTINDAN YAZA BİLƏRSİNİZ --->',
    'bar': '{{Bitte erst NACH dieser Zeile schreiben! (Begrüßungskasten)}}\n',
    'bn': '{{খেলাঘর}}<!-- অনুগ্রহপূর্বক এই লাইনটি অপসারণ করবেন না -->',
    'ckb': '{{subst:تکایە دەستکاریی سەری خۆڵەپەتانێ مەکە}}',
    'cs': '{{Tento řádek neměňte}}\n<!-- ************  Prosíme, '
          'NEMĚŇTE nic nad tímto řádkem.  Díky.  ************ -->\n\n'
          "== Bábovičky ==\n#'''první'''\n#''druhá''\n*třetí\n"
          "*'''''čtvrtá'''''\n pátá\n;šestá\n:sedmá",
    'da': '{{subst:Sandkasse tekst}}',
    'de': '{{subst:Wikipedia:Spielwiese/Vorlage}}',
    'en': '{{Sandbox heading}}\n<!-- Hello! Feel free to try your formatting '
          'and editing skills below this line. As this page is for editing '
          'experiments, this page will automatically be cleaned every 12 '
          'hours. -->',
    'es': '<!--No borres este mensaje-->{{Titular-zdp}}'
          '<!--Haz las pruebas debajo. Gracias-->\n'
          '== Las pruebas en esta sección ==\n',
    'eo': '{{Bonvolu ne forigi tiun ĉi linion (Provejo)}}',
    'fa': '{{subst:Wikipedia:ربات/sandbox}}',
    'fi': '{{subst:Hiekka}}',
    'fr': '{{subst:Préchargement pour Bac à sable}}',
    'he': '{{ארגז חול}}\n<!-- נא לערוך מתחת לשורה זו בלבד, תודה. -->',
    'hi': '{{User sandbox}}\n<!-- कृप्या इस लाइन के नीचे सम्पादन करे। -->',
    'id': '{{Bakpasir}}\n<!-- Uji coba dilakukan di baris di bawah ini -->',
    'it': '{{sandbox}}'
          '<!-- Scrivi SOTTO questa riga senza cancellarla. Grazie. -->',
    'ja': '{{subst:サンドボックス}}',
    'ko': '{{연습장 안내문}}',
    'ksh': '{{subst:/Schablon}}',
    'mzn': '{{ویکی‌پدیا:چنگ‌مویی صفحه/پیغوم}}\n<!-- سلام!اگه '
           'خواننی شه دچی‌ین مهارتون وسه تمرین هاکنین بتوننی اینتا صفحه جا '
           'ایستفاده هاکنین، اته لطف هاکنین اینتا پیغوم ره شه بقیه رفقون وسه '
           'بیلین. اینتا صفحه هرچند ساعت ربوت جا پاک بونه.-->',
    'my': '{{subst:Sandbox reset}}',
    'nds': '{{subst:/Vörlaag}}',
    'ne': '{{User sandbox}}\n'
          '<!-- कृप्या! यो लाइनको तल सम्पादन गर्नुहोला। -->',
    'nl': '{{subst:Wikipedia:Zandbak/schoon zand}}',
    'nn': '{{sandkasse}}\n<!-- Ver snill og IKKJE FJERN DENNE LINA OG LINA '
          'OVER ({{sandkasse}}) Nedanføre kan du derimot ha det artig og '
          'prøve deg fram! Lykke til! :-)  -->',
    'no': '{{Sandkasse}}\n<!-- VENNLIGST EKSPERIMENTER NEDENFOR DENNE '
          'SKJULTE TEKSTLINJEN! SANDKASSEMALEN {{Sandkasse}} SKAL IKKE '
          'FJERNES! -->}}',
    'pl': '{{Prosimy - NIE ZMIENIAJ, NIE KASUJ, NIE PRZENOŚ tej linijki '
          '- pisz niżej}}',
    'pt': '<!--não apague esta linha-->'
          '{{página de testes}}<!--não apagar-->\n',
    'ru': '{{/Пишите ниже}}\n'
          '<!-- Не удаляйте, пожалуйста, эту строку, тестируйте ниже -->',
    'simple': '{{subst:/Text}}',
    'sco': '{{subst:Saundbox}}',
    'shn': '{{subst:Sandbox reset}}',
    'sr': '{{песак}}<!--\n'
          '*               Добро дошли на песак!               *\n'
          '*             Молимо вас да испробавате             *\n'
          '*             испод црне линије. Хвала!             *\n'
          '■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■-->',
    'sv': '{{subst:Sandlådan}}',
    'th': '{{กระบะทราย}}\n<!-- กรุณาอย่าแก้ไขบรรทัดนี้ ขอบคุณครับ/ค่ะ -- '
          'Please leave this line as they are. Thank you! -->',
    'tr': '{{/Bu satırı değiştirmeden bırakın}}',
    'zh': '{{subst:User:Sz-iwbot/sandbox}}\n',
}

sandbox_titles = ('Q3938', 'Q28939665')

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}


class SandboxBot(Bot, ConfigParserBot):

    """Sandbox reset bot."""

    available_options = {
        'hours': -1.0,  # do not repeat if hours < 0
        'delay': -1,
        'text': '',
        'summary': '',
    }

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        if self.opt.delay < 0:
            d = min(15, max(5, int(self.opt.hours * 60)))
            self.delay_td = datetime.timedelta(minutes=d)
        else:
            d = max(5, self.opt.delay)
            self.delay_td = datetime.timedelta(minutes=d)

        self.site = pywikibot.Site()
        self.translated_content = self.opt.text or i18n.translate(
            self.site, content)
        if not self.translated_content:
            raise RuntimeError(
                'No content is given for sandbox pages, exiting.')
        if not self.generator:
            pages = []
            for item in sandbox_titles:
                p = self.site.page_from_repository(item)
                if p is not None:
                    pages.append(p)
            if not pages:
                pywikibot.bot.suggest_help(missing_generator=True)
                sys.exit()
            self.generator = pages

    def run(self) -> None:
        """Run bot."""
        self.site.login()
        while True:
            wait = False
            now = time.strftime('%d %b %Y %H:%M:%S (UTC)', time.gmtime())
            for sandbox_page in self.generator:
                pywikibot.info('Preparing to process sandbox page '
                               + sandbox_page.title(as_link=True))
                if sandbox_page.isRedirectPage():
                    pywikibot.warning(
                        '{} is a redirect page, cleaning it anyway'
                        .format(sandbox_page.title(as_link=True)))
                try:
                    text = sandbox_page.text
                    if self.opt.summary:
                        translated_msg = self.opt.summary
                    else:
                        translated_msg = i18n.twtranslate(
                            self.site, 'clean_sandbox-cleaned')
                    subst = 'subst:' in self.translated_content
                    pos = text.find(self.translated_content.strip())
                    if text.strip() == self.translated_content.strip():
                        pywikibot.info(
                            'The sandbox is still clean, no change necessary.')
                    elif subst and sandbox_page.userName() == self.site.user():
                        pywikibot.info(
                            'The sandbox might be clean, no change necessary.')
                    elif pos != 0 and not subst:
                        sandbox_page.put(self.translated_content,
                                         translated_msg)
                        pywikibot.showDiff(text, self.translated_content)
                        pywikibot.info(
                            'Standard content was changed, sandbox cleaned.')
                    else:
                        edit_delta = (datetime.datetime.utcnow()
                                      - sandbox_page.latest_revision.timestamp)
                        delta = self.delay_td - edit_delta
                        # Is the last edit more than 'delay' minutes ago?
                        if delta <= datetime.timedelta(0):
                            sandbox_page.put(
                                self.translated_content, translated_msg)
                            pywikibot.showDiff(text, self.translated_content)
                            pywikibot.info('Standard content was changed, '
                                           'sandbox cleaned.')
                        else:  # wait for the rest
                            pywikibot.info(
                                'Sandbox edited {:.1f} minutes ago...'
                                .format(edit_delta.seconds / 60.0))
                            pywikibot.info(
                                f'Sleeping for {delta.seconds // 60} minutes.')
                            pywikibot.sleep(delta.seconds)
                            wait = True
                except EditConflictError:
                    pywikibot.info(
                        '*** Loading again because of edit conflict.\n')
                except NoPageError:
                    pywikibot.info(
                        '*** The sandbox is not existent, skipping.')
                    continue

            if self.opt.hours < 0:
                pywikibot.info('\nDone.')
                return

            if not wait:
                if self.opt.hours < 1.0:
                    pywikibot.info(
                        f'\nSleeping {self.opt.hours * 60} minutes, now {now}')
                else:
                    pywikibot.info(
                        f'\nSleeping {self.opt.hours} hours, now {now}')
                pywikibot.sleep(self.opt.hours * 60 * 60)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    opts = {}
    textfile_opt = None
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    for arg in local_args:
        opt, _, value = arg.partition(':')
        if opt.startswith('-'):
            opt = opt[1:]
        else:
            continue
        if opt == 'hours':
            opts[opt] = float(value)
        elif opt == 'delay':
            opts[opt] = int(value)
        elif opt == 'text':
            opts[opt] = value or pywikibot.input(
                'What text do you want to substitute?')
        elif opt == 'textfile':
            textfile_opt = value or pywikibot.input(
                'What file contains the text you want to substitute with?')
        elif opt == 'summary':
            opts[opt] = value or pywikibot.input('Enter the summary:')
        else:
            gen_factory.handle_arg(arg)

    if textfile_opt:
        if 'text' in opts:
            pywikibot.error(
                'Arguments -text and -textfile '
                "can't be provided at the same time")
            return
        try:
            with open(textfile_opt, encoding='utf-8') as textfile:
                opts['text'] = textfile.read()
        except OSError as e:
            pywikibot.error(f'Error loading {opts["textfile"]}: {e}')
            return

    generator = gen_factory.getCombinedGenerator()

    bot = SandboxBot(generator=generator, **opts)
    bot.run()


if __name__ == '__main__':
    main()
