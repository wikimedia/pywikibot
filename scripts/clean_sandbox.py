# -*- coding: utf-8 -*-
"""
This bot cleans a sandbox by replacing the current contents with predefined
text.

This script understands the following command-line arguments:

    -hours:#       Use this parameter if to make the script repeat itself
                   after # hours. Hours can be defined as a decimal. 0.01
                   hours are 36 seconds; 0.1 are 6 minutes.

    -delay:#       Use this parameter for a wait time after the last edit
                   was made. If no parameter is given it takes it from
                   hours and limits it between 5 and 15 minutes.
                   The minimum delay time is 5 minutes.

"""
#
# (C) Leonardo Gregianin, 2006
# (C) Wikipedian, 2006-2007
# (C) Andre Engels, 2007
# (C) Siebrand Mazeland, 2007
# (C) xqt, 2009
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import time
import datetime
import sys

import pywikibot

content = {
    'als':u'{{subst:/Vorlage}}',
    'ar': u'{{من فضلك اترك هذا السطر ولا تعدله (عنوان ساحة التجربة)}}\n<!-- مرحبا! خذ راحتك في تجربة مهارتك في التنسيق والتحرير أسفل هذا السطر. هذه الصفحة لتجارب التعديل ، سيتم تفريغ هذه الصفحة كل 6 ساعات. -->',
    'bar':u'{{Bitte erst NACH dieser Zeile schreiben! (Begrüßungskasten)}}\r\n',
    'cs': u'{{subst:/uhrabat}}',
    'da': u'{{subst:Sandkasse tekst}}',
    'de': u'{{Bitte erst NACH dieser Zeile schreiben! (Begrüßungskasten)}}\r\n',
    'en': u'{{Please leave this line alone (sandbox heading)}}\n<!-- Hello! Feel free to try your formatting and editing skills below this line. As this page is for editing experiments, this page will automatically be cleaned every 12 hours. -->',
    'fa': u'{{subst:User:Amirobot/sandbox}}',
    'fi': u'{{subst:Hiekka}}',
    'he': u'{{ארגז חול}}\n<!-- נא לערוך מתחת לשורה זו בלבד, תודה. -->',
    'id': u'{{Bakpasir}}\n<!-- Uji coba dilakukan di baris di bawah ini -->',
    'it': u'{{sandbox}}<!-- Scrivi SOTTO questa riga senza cancellarla. Grazie. -->',
    'ja': u'{{subst:サンドボックス}}',
    'ko': u'{{연습장 안내문}}',
    'ksh':u'{{subst:/Schablon}}',
    'nds':u'{{subst:/Vörlaag}}',
    'nl': u'{{subst:Wikipedia:Zandbak/schoon zand}}',
    'no': u'{{Sandkasse}}\n<!-- VENNLIGST EKSPERIMENTER NEDENFOR DENNE SKJULTE TEKSTLINJEN! SANDKASSEMALEN {{Sandkasse}} SKAL IKKE FJERNES! -->}}',
    'nn': u'{{sandkasse}}\n<!-- Ver snill og IKKJE FJERN DENNE LINA OG LINA OVER ({{sandkasse}}) Nedanføre kan du derimot ha det artig og prøve deg fram! Lykke til! :-)  -->',
    'pl': u'{{Prosimy - NIE ZMIENIAJ, NIE KASUJ, NIE PRZENOŚ tej linijki - pisz niżej}}',
    'pt': u'<!--não apague esta linha-->{{página de testes}}<!--não apagar-->\r\n',
    'commons': u'{{Sandbox}}\n<!-- Please edit only below this line. -->',
    'ru': u'{{/Пишите ниже}}\n<!-- Не удаляйте, пожалуйста, эту строку, тестируйте ниже -->',
    'sr': u'{{песак}}\n<!-- Молимо, испробавајте испод ове линије. Хвала. -->',
    'sv': u'{{subst:Sandlådan}}',
    'th': u'{{กระบะทราย}}\n<!-- กรุณาอย่าแก้ไขบรรทัดนี้ ขอบคุณครับ/ค่ะ -- Please leave this line as they are. Thank you! -->',
    'zh': u'{{subst:User:Sz-iwbot/sandbox}}\r\n',
    }

msg = {
    'als':u'Bötli: Sandchaschte iigebnet.',
    'ar': u'روبوت: هذه الصفحة سيتم تفريغها تلقائيا',
    'bar':u'Bot: Spielwiesn gmaht.',
    'cs': u'Uhrabání pískoviště',
    'da': u'Bot: Nyt sand (fra[[Skabelon:Sandkasse tekst]])',
    'de': u'Bot: Setze Spielwiese zurück.',
    'en': u'Robot: Automatically cleaned',
    'fa': u'ربات: صفحه به طور خودکار تميز شد',
    'fi': u'Botti siivosi hiekkalaatikon.',
    'he': u'בוט: דף זה ינוקה אוטומטית.',
    'id': u'Bot: Tata ulang',
    'it': u'Bot: pulitura sandbox',
    'ja': u'ロボットによる: 砂場ならし',
    'ko': u'로봇: 연습장 비움',
    'ksh':u'Bot: allt Zeush fott gedunn.',
    'nds':u'Bot: Speelwisch leddig maakt.',
    'nl': u'Bot: automatisch voorzien van schoon zand.',
    'no': u'bot: Rydder sandkassa.',
    'pl': u'Robot czyści brudnopis',
    'pt': u'Bot: Limpeza da página de testes',
    'commons': u'Bot: This page will automatically be cleaned.',
    'ru': u'Бот: очистка песочницы',
    'sr': u'Чишћење песка',
    'sv': u'Robot krattar sandlådan.',
    'th': u'โรบอต: กำลังจะเก็บกวาดหน้านี้โดยอัตโนมัติ',
    'zh': u'Bot: 本页被自动清理',
    }

sandboxTitle = {
    'als':u'Project:Sandchaschte',
    'ar': u'Project:ساحة التجربة',
    'bar':u'Project:Spielwiese',
    'cs': u'Project:Pískoviště',
    'da': u'Project:Sandkassen',
    'de': u'Project:Spielwiese',
    'en': u'Project:Sandbox',
    'fa': u'Project:صفحه تمرین',
    'fr': u'Project:Bac à sable',
    'fi': u'Project:Hiekkalaatikko',
    'he': u'Project:ארגז חול',
    'id': u'Project:Bak pasir',
    'it': u'Project:Pagina delle prove',
    'ja': u'Project:サンドボックス',
    'ko': u'Project:연습장',
    'ksh':u'Project:Shpillplaz',
    'nds':u'Project:Speelwisch',
    'nl': u'Project:Zandbak',
    'no': u'Project:Sandkasse',
    'pl': u'Project:Brudnopis',
    'pt': u'Project:Página de testes',
    'commons': u'Project:Sandbox',
    'ru': u'Project:Песочница',
    'sr': u'Project:Песак',
    'sv': u'Project:Sandlådan',
    'th': u'Project:ทดลองเขียน',
    'zh': u'Project:沙盒',
    }

class SandboxBot(pywikibot.Bot):
    availableOptions = {
        'hours': 1,
        'no_repeat': True,
        'delay': None,
        'delay_td': None,
    }

    def __init__(self, **kwargs):
        super(SandboxBot, self).__init__(**kwargs)
        if self.getOption('delay') is None:
            d = min(15, max(5, int(self.getOption('hours')*60)))
            self.availableOptions['delay_td'] = datetime.timedelta(minutes=d)
        else:
            d = max(5, self.getOption('delay'))
            self.availableOptions['delay_td'] = datetime.timedelta(minutes=d)

        self.site = pywikibot.Site()
        if sandboxTitle.get(self.site.lang) is None or \
                                        content.get(self.site.lang) is None:
            pywikibot.output(u'This bot is not configured for the given site ' \
                                u'(%s), exiting.' % self.site)
            sys.exit(0)


    def run(self):
        while True:
            wait = False
            now = time.strftime("%d %b %Y %H:%M:%S (UTC)", time.gmtime())
            localSandboxTitle = pywikibot.translate(self.site, sandboxTitle)
            if type(localSandboxTitle) is list:
                titles = localSandboxTitle
            else:
                titles = [localSandboxTitle,]
            for title in titles:
                sandboxPage = pywikibot.Page(self.site, title)
                try:
                    text = sandboxPage.get()
                    translatedContent = pywikibot.translate(self.site, content)
                    translatedMsg = pywikibot.translate(self.site, msg)
                    subst = 'subst:' in translatedContent
                    if text.strip() == translatedContent.strip():
                        pywikibot.output(u'The sandbox is still clean, no change necessary.')
                    elif subst and sandboxPage.userName() == self.site.user():
                        pywikibot.output(u'The sandbox might be clean, no change necessary.')
                    elif text.find(translatedContent.strip()) <> 0 and not subst:
                        sandboxPage.put(translatedContent, translatedMsg)
                        pywikibot.showDiff(text, translatedContent) 
                        pywikibot.output(u'Standard content was changed, sandbox cleaned.')
                    else:
                        edit_delta = datetime.datetime.utcnow() - \
                                    pywikibot.Timestamp.fromISOformat(sandboxPage.editTime())
                        delta = self.getOption('delay_td') - edit_delta
                        #Is the last edit more than 'delay' minutes ago?
                        if delta <= datetime.timedelta(0):
                            sandboxPage.put(translatedContent, translatedMsg)
                            pywikibot.showDiff(text, translatedContent)
                        else: #wait for the rest
                            pywikibot.output(u'Sandbox edited %.1f minutes ago...' % \
                                                (edit_delta.seconds / 60.0))
                            pywikibot.output(u'Sleeping for %d minutes.' % (delta.seconds/60))
                            time.sleep(delta.seconds)
                            wait = True
                except pywikibot.EditConflict:
                    pywikibot.output(u'*** Loading again because of edit conflict.\n')
            if self.getOption('no_repeat'):
                pywikibot.output(u'\nDone.')
                return
            elif not wait:
                if self.getOption('hours') < 1.0:
                    pywikibot.output('\nSleeping %s minutes, now %s' % ((self.getOption('hours')*60), now))
                else:
                    pywikibot.output('\nSleeping %s hours, now %s' % (self.getOption('hours'), now))
                time.sleep(self.getOption('hours') * 60 * 60)

def main():
    opts = {}
    for arg in pywikibot.handleArgs():
        if arg.startswith('-hours:'):
            opts['hours'] = float(arg[7:])
            opts['no_repeat'] = False
        elif arg.startswith('-delay:'):
            opts['delay'] = int(arg[7:])
        else:
            pywikibot.showHelp('clean_sandbox')
            return

    bot = SandboxBot(**opts)
    try:
        bot.run()
    except KeyboardInterrupt:
        pywikibot.output('\nQuitting program...')

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
