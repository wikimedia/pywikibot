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

import wikipedia
import time

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
    'fa': u'ربات:صفحه به طور خودکار تميز شد',
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

class SandboxBot:
    def __init__(self, hours, no_repeat, delay):
        self.hours = hours
        self.no_repeat = no_repeat
        if delay == None:
            self.delay = min(15, max(5, int(self.hours *60)))
        else:
            self.delay = max(5, delay)

    def run(self):
        
        def minutesDiff(time1, time2):
            if type(time1) is long:
                time1 = str(time1)
            if type(time2) is long:
                time2 = str(time2)
            t1 = (((int(time1[0:4])*12+int(time1[4:6]))*30+int(time1[6:8]))*24+int(time1[8:10])*60)+int(time1[10:12])
            t2 = (((int(time2[0:4])*12+int(time2[4:6]))*30+int(time2[6:8]))*24+int(time2[8:10])*60)+int(time2[10:12])
            return abs(t2-t1)

        mySite = wikipedia.getSite()
        while True:
            wait = False
            now = time.strftime("%d %b %Y %H:%M:%S (UTC)", time.gmtime())
            localSandboxTitle = wikipedia.translate(mySite, sandboxTitle)
            if type(localSandboxTitle) is list:
                titles = localSandboxTitle
            else:
                titles = [localSandboxTitle,]
            for title in titles:
                sandboxPage = wikipedia.Page(mySite, title)
                try:
                    text = sandboxPage.get()
                    translatedContent = wikipedia.translate(mySite, content)
                    translatedMsg = wikipedia.translate(mySite, msg)
                    subst = 'subst:' in translatedContent
                    if text.strip() == translatedContent.strip():
                        wikipedia.output(u'The sandbox is still clean, no change necessary.')
                    elif subst and sandboxPage.userName() == mySite.loggedInAs():
                        wikipedia.output(u'The sandbox might be clean, no change necessary.')
                    elif text.find(translatedContent.strip()) <> 0 and not subst:
                        sandboxPage.put(translatedContent, translatedMsg)
                        wikipedia.output(u'Standard content was changed, sandbox cleaned.')
                    else:
                        diff = minutesDiff(sandboxPage.editTime(), time.strftime("%Y%m%d%H%M%S", time.gmtime()))
                        #Is the last edit more than 5 minutes ago?
                        if diff >= self.delay:
                            sandboxPage.put(translatedContent, translatedMsg)
                        else: #wait for the rest
                            wikipedia.output(u'Sleeping for %d minutes.' % (self.delay-diff))
                            time.sleep((self.delay-diff)*60)
                            wait = True
                except wikipedia.EditConflict:
                    wikipedia.output(u'*** Loading again because of edit conflict.\n')
            if self.no_repeat:
                wikipedia.output(u'\nDone.')
                return
            elif not wait:
                if self.hours < 1.0:
                    wikipedia.output('\nSleeping %s minutes, now %s' % ((self.hours*60), now) )
                else:
                    wikipedia.output('\nSleeping %s hours, now %s' % (self.hours, now) )
                time.sleep(self.hours * 60 * 60)

def main():
    hours = 1
    delay = None
    no_repeat = True
    for arg in wikipedia.handleArgs():
        if arg.startswith('-hours:'):
            hours = float(arg[7:])
            no_repeat = False
        elif arg.startswith('-delay:'):
            delay = int(arg[7:])
        else:
            wikipedia.showHelp('clean_sandbox')
            return

    bot = SandboxBot(hours, no_repeat, delay)
    try:
        bot.run()
    except KeyboardInterrupt:
        wikipedia.output('\nQuitting program...')

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
