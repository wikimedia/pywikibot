#!/usr/bin/python
# -*- coding: utf-8 -*-
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
                   when you haven't configured clean_candbox for your wiki.

    -summary       Summary of the edit made by bot.

"""
#
# (C) Leonardo Gregianin, 2006
# (C) Wikipedian, 2006-2007
# (C) Andre Engels, 2007
# (C) Siebrand Mazeland, 2007
# (C) xqt, 2009-2014
# (C) Dr. Trigon, 2012
# (C) Pywikibot team, 2012-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import division, unicode_literals
__version__ = '$Id$'
#

import time
import datetime
import pywikibot
from pywikibot import i18n, Bot, pagegenerators

content = {
    'commons': u'{{Sandbox}}\n<!-- Please edit only below this line. -->',
    'als': u'{{subst:/Vorlage}}',
    'ar': u'{{عنوان الملعب}}\n<!-- مرحبا! خذ راحتك في تجربة مهارتك في التنسيق '
          u'والتحرير أسفل هذا السطر. هذه الصفحة لتجارب التعديل ، سيتم تفريغ '
          u'هذه الصفحة كل 12 ساعة. -->',
    'arz': u'{{عنوان السبوره}}\n<!-- مرحبا! خد راحتك فى تجريب مهاراتك فى\n'
           u'التحرير تحت الخط ده. بما إن الصفحه دى لتجارب التعديل، فالصفحه دى '
           u'حيتم تنضيفها\nاوتوماتيكيا كل 12 ساعه. -->',
    'az': u'<!--- LÜTFƏN, BU SƏTRƏ TOXUNMAYIN --->\n{{Qaralama dəftəri}}\n'
          u'<!-- AŞAĞIDAKI XƏTTİN ALTINDAN YAZA BİLƏRSİNİZ --->',
    'bar': u'{{Bitte erst NACH dieser Zeile schreiben! (Begrüßungskasten)}}\r\n',
    'cs': u'{{subst:/uhrabat}}',
    'da': u'{{subst:Sandkasse tekst}}',
    'de': u'{{subst:Wikipedia:Spielwiese/Vorlage}}',
    'en': u'{{Sandbox heading}}\n<!-- Hello! Feel free to try your formatting '
          u'and editing skills below this line. As this page is for editing '
          u'experiments, this page will automatically be cleaned every 12 '
          u'hours. -->',
    'fa': u'{{subst:Wikipedia:ربات/sandbox}}',
    'fi': u'{{subst:Hiekka}}',
    'he': u'{{ארגז חול}}\n<!-- נא לערוך מתחת לשורה זו בלבד, תודה. -->',
    'id': u'{{Bakpasir}}\n<!-- Uji coba dilakukan di baris di bawah ini -->',
    'it': u'{{sandbox}}<!-- Scrivi SOTTO questa riga senza cancellarla. Grazie. -->',
    'ja': u'{{subst:サンドボックス}}',
    'ko': u'{{연습장 안내문}}',
    'ksh': u'{{subst:/Schablon}}',
    'mzn': u'{{ویکی‌پدیا:چنگ‌مویی صفحه/پیغوم}}\n<!-- سلام!اگه '
           u'خواننی شه دچی‌ین مهارتون وسه تمرین هاکنین بتوننی اینتا صفحه جا '
           u'ایستفاده هاکنین، اته لطف هاکنین اینتا پیغوم ره شه بقیه رفقون وسه '
           u'بیلین. اینتا صفحه هرچند ساعت ربوت جا پاک بونه.-->',
    'nds': u'{{subst:/Vörlaag}}',
    'nl': u'{{subst:Wikipedia:Zandbak/schoon zand}}',
    'nn': u'{{sandkasse}}\n<!-- Ver snill og IKKJE FJERN DENNE LINA OG LINA '
          u'OVER ({{sandkasse}}) Nedanføre kan du derimot ha det artig og '
          u'prøve deg fram! Lykke til! :-)  -->',
    'no': u'{{Sandkasse}}\n<!-- VENNLIGST EKSPERIMENTER NEDENFOR DENNE '
          u'SKJULTE TEKSTLINJEN! SANDKASSEMALEN {{Sandkasse}} SKAL IKKE '
          u'FJERNES! -->}}',
    'pl': u'{{Prosimy - NIE ZMIENIAJ, NIE KASUJ, NIE PRZENOŚ tej linijki - pisz niżej}}',
    'pt': u'<!--não apague esta linha-->{{página de testes}}<!--não apagar-->\r\n',
    'ru': u'{{/Пишите ниже}}\n<!-- Не удаляйте, пожалуйста, эту строку, тестируйте ниже -->',
    'simple': u'{{subst:/Text}}',
    'sco': u'Feel free tae test here',
    'sr': u'{{песак}}\n<!-- Молимо, испробавајте испод ове линије. Хвала. -->',
    'sv': u'{{subst:Sandlådan}}',
    'th': u'{{กระบะทราย}}\n<!-- กรุณาอย่าแก้ไขบรรทัดนี้ ขอบคุณครับ/ค่ะ -- '
          u'Please leave this line as they are. Thank you! -->',
    'tr': u'{{/Bu satırı değiştirmeden bırakın}}',
    'zh': u'{{subst:User:Sz-iwbot/sandbox}}\r\n',
}

sandboxTitle = {
    'commons': u'Project:Sandbox',
    'als': u'Project:Sandchaschte',
    'ar': u'Project:ملعب',
    'arz': u'Project:السبوره',
    'az': u'Vikipediya:Qaralama dəftəri',
    'bar': u'Project:Spuiwiesn',
    'cs': u'Project:Pískoviště',
    'da': u'Project:Sandkassen',
    'de': u'Project:Spielwiese',
    'en': u'Project:Sandbox',
    'fa': [u'Project:صفحه تمرین', u'Project:آشنایی با ویرایش'],
    'fi': u'Project:Hiekkalaatikko',
    'fr': u'Project:Bac à sable',
    'he': u'Project:ארגז חול',
    'id': u'Project:Bak pasir',
    'it': u'Project:Pagina delle prove',
    'ja': u'Project:サンドボックス',
    'ko': u'Project:연습장',
    'ksh': u'Project:Shpillplaz',
    'mzn': u'Project:چنگ‌مویی صفحه',
    'nds': u'Project:Speelwisch',
    'nl': u'Project:Zandbak',
    'no': u'Project:Sandkasse',
    'pl': u'Project:Brudnopis',
    'pt': u'Project:Página de testes',
    'ru': u'Project:Песочница',
    'simple': u'Project:Sandbox',
    'sco': u'Project:Saundpit',
    'sr': u'Project:Песак',
    'sv': u'Project:Sandlådan',
    'th': u'Project:ทดลองเขียน',
    'tr': u'Vikipedi:Deneme tahtası',
    'zh': u'Project:沙盒',
}

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;':     pagegenerators.parameterHelp,
}


class SandboxBot(Bot):

    """Sandbox reset bot."""

    availableOptions = {
        'hours': 1,
        'no_repeat': True,
        'delay': None,
        'delay_td': None,
        'text': "",
        'summary': "",
    }

    def __init__(self, **kwargs):
        """Constructor."""
        super(SandboxBot, self).__init__(**kwargs)
        if self.getOption('delay') is None:
            d = min(15, max(5, int(self.getOption('hours') * 60)))
            self.availableOptions['delay_td'] = datetime.timedelta(minutes=d)
        else:
            d = max(5, self.getOption('delay'))
            self.availableOptions['delay_td'] = datetime.timedelta(minutes=d)

        self.site = pywikibot.Site()
        if not content.get(self.site.code) and not self.getOption('text'):
            pywikibot.error(u'No content is given for pages, exiting.')
            raise RuntimeError
        if not self.generator:
            if self.site.code not in sandboxTitle:
                pywikibot.error(u'No generator is given for this site'
                                 u'(%s), exiting.' % self.site)
                raise RuntimeError
            local_sandbox_title = sandboxTitle[self.site.code]
            if not isinstance(local_sandbox_title, list):
                local_sandbox_title = [local_sandbox_title]
            self.generator = [pywikibot.Page(self.site, page_name) for
                              page_name in local_sandbox_title]

    def run(self):
        """Run bot."""
        self.site.login()
        while True:
            wait = False
            now = time.strftime("%d %b %Y %H:%M:%S (UTC)", time.gmtime())
            for sandboxPage in self.generator:
                pywikibot.output(u'Preparing to process sandbox page %s'
                                 % sandboxPage.title(asLink=True))
                if sandboxPage.isRedirectPage():
                    pywikibot.warning(
                        u'%s is a redirect page, cleaning it anyway'
                        % sandboxPage.title(asLink=True))
                try:
                    text = sandboxPage.text
                    if not self.getOption('text'):
                        translatedContent = i18n.translate(self.site, content)
                    else:
                        translatedContent = self.getOption('text')
                    if self.getOption('summary'):
                        translatedMsg = self.getOption('summary')
                    else:
                        translatedMsg = i18n.twtranslate(
                            self.site, 'clean_sandbox-cleaned')
                    subst = 'subst:' in translatedContent
                    pos = text.find(translatedContent.strip())
                    if text.strip() == translatedContent.strip():
                        pywikibot.output(
                            u'The sandbox is still clean, no change necessary.')
                    elif subst and \
                         sandboxPage.userName() == self.site.user():
                        pywikibot.output(
                            u'The sandbox might be clean, no change necessary.')
                    elif pos != 0 and not subst:
                        sandboxPage.put(translatedContent, translatedMsg)
                        pywikibot.showDiff(text, translatedContent)
                        pywikibot.output(u'Standard content was changed, '
                                         u'sandbox cleaned.')
                    else:
                        edit_delta = (datetime.datetime.utcnow() -
                                      sandboxPage.editTime())
                        delta = self.getOption('delay_td') - edit_delta
                        # Is the last edit more than 'delay' minutes ago?
                        if delta <= datetime.timedelta(0):
                            sandboxPage.put(translatedContent, translatedMsg)
                            pywikibot.showDiff(text, translatedContent)
                            pywikibot.output(u'Standard content was changed, '
                                             u'sandbox cleaned.')
                        else:  # wait for the rest
                            pywikibot.output(
                                u'Sandbox edited %.1f minutes ago...'
                                % (edit_delta.seconds / 60.0))
                            pywikibot.output(u'Sleeping for %d minutes.'
                                             % (delta.seconds // 60))
                            time.sleep(delta.seconds)
                            wait = True
                except pywikibot.EditConflict:
                    pywikibot.output(
                        u'*** Loading again because of edit conflict.\n')
                except pywikibot.NoPage:
                    pywikibot.output(
                        u'*** The sandbox is not existent, skipping.')
                    continue
            if self.getOption('no_repeat'):
                pywikibot.output(u'\nDone.')
                return
            elif not wait:
                if self.getOption('hours') < 1.0:
                    pywikibot.output('\nSleeping %s minutes, now %s'
                                     % ((self.getOption('hours') * 60), now))
                else:
                    pywikibot.output('\nSleeping %s hours, now %s'
                                     % (self.getOption('hours'), now))
                time.sleep(self.getOption('hours') * 60 * 60)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    opts = {}
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    for arg in local_args:
        if arg.startswith('-hours:'):
            opts['hours'] = float(arg[7:])
            opts['no_repeat'] = False
        elif arg.startswith('-delay:'):
            opts['delay'] = int(arg[7:])
        elif arg.startswith('-text'):
            if len(arg) == 5:
                opts['text'] = pywikibot.input(
                    u'What text do you want to substitute?')
            else:
                opts['text'] = arg[6:]
        elif arg.startswith('-summary'):
            if len(arg) == len('-summary'):
                opts['summary'] = pywikibot.input(u'Enter the summary:')
            else:
                opts['summary'] = arg[9:]
        else:
            gen_factory.handleArg(arg)

    generator = gen_factory.getCombinedGenerator()

    bot = SandboxBot(generator=generator, **opts)
    bot.run()

if __name__ == "__main__":
    main()
