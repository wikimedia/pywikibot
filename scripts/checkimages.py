#!/usr/bin/python
"""
Script to check recently uploaded files.

This script checks if a file description is present and if there are other
problems in the image's description.

This script will have to be configured for each language. Please submit
translations as addition to the Pywikibot framework.

Everything that needs customisation is indicated by comments.

This script understands the following command-line arguments:

-limit              The number of images to check (default: 80)

-commons            The Bot will check if an image on Commons has the same name
                    and if true it reports the image.

-duplicates[:#]     Checking if the image has duplicates (if arg, set how many
                    rollback wait before reporting the image in the report
                    instead of tag the image) default: 1 rollback.

-duplicatesreport   Report the duplicates in a log *AND* put the template in
                    the images.

-maxusernotify      Maximum nofitications added to a user talk page in a single
                    check, to avoid email spamming.

-sendemail          Send an email after tagging.

-break              To break the bot after the first check (default: recursive)

-sleep[:#]          Time in seconds between repeat runs (default: 30)

-wait[:#]           Wait x second before check the images (default: 0)

-skip[:#]           The bot skip the first [:#] images (default: 0)

-start[:#]          Use allimages() as generator
                    (it starts already from File:[:#])

-cat[:#]            Use a category as generator

-regex[:#]          Use regex, must be used with -url or -page

-page[:#]           Define the name of the wikipage where are the images

-url[:#]            Define the url where are the images

-nologerror         If given, this option will disable the error that is risen
                    when the log is full.

Instructions for the real-time settings.
For every new block you have to add:

 <------- ------->

In this way the Bot can understand where the block starts in order to take the
right parameter.

* Name=     Set the name of the block
* Find=     search this text in the image's description
* Findonly= search for exactly this text in the image's description
* Summary=  That's the summary that the bot will use when it will notify the
            problem.
* Head=     That's the incipit that the bot will use for the message.
* Text=     This is the template that the bot will use when it will report the
            image's problem.

Todo
----
* Clean the code, some passages are pretty difficult to understand.
* Add the "catch the language" function for commons.
* Fix and reorganise the new documentation
* Add a report for the image tagged.

"""
#
# (C) Pywikibot team, 2006-2021
#
# Distributed under the terms of the MIT license.
#
import collections
import re
import time
from typing import Generator

import pywikibot
from pywikibot import config, i18n
from pywikibot import pagegenerators as pg
from pywikibot.backports import List, Tuple
from pywikibot.bot import suggest_help
from pywikibot.exceptions import (
    EditConflictError,
    Error,
    IsRedirectPageError,
    LockedPageError,
    NoPageError,
    NotEmailableError,
    PageRelatedError,
    TranslationError,
)
from pywikibot.family import Family
from pywikibot.site import Namespace


###############################################################################
# <--------------------------- Change only below! --------------------------->#
###############################################################################

# NOTE: in the messages used by the Bot if you put __botnick__ in the text, it
# will automatically replaced with the bot's nickname.

# That's what you want that will be added. (i.e. the {{no source}} with the
# right day/month/year )
n_txt = {
    'commons': '{{subst:nld}}',
    'meta': '{{No license}}',
    'test': '{{No license}}',
    'ar': '{{subst:لم}}',
    'de': '{{Dateiüberprüfung}}',
    'en': '{{subst:nld}}',
    'fa': '{{جا:حق تکثیر تصویر نامعلوم}}',
    'fr': '{{subst:lid}}',
    'ga': '{{subst:Ceadúnas de dhíth}}',
    'hr': '{{Bez licence}}',
    'hu': '{{nincslicenc|~~~~~}}',
    'it': '{{subst:unverdata}}',
    'ja': '{{subst:Nld}}',
    'ko': '{{subst:nld}}',
    'ru': '{{subst:nld}}',
    'sd': '{{subst:اجازت نامعلوم}}',
    'sr': '{{subst:датотека без лиценце}}',
    'ta': '{{subst:nld}}',
    'ur': '{{subst:حقوق نسخہ تصویر نامعلوم}}',
    'zh': '{{subst:No license/auto}}',
}

# Text that the bot will try to see if there's already or not. If there's a
# {{ I'll use a regex to make a better check.
# This will work so:
# '{{no license' --> '\{\{(?:template:)?no[ _]license ?(?:\||\n|\}|/) ?' (case
# insensitive).
# If there's not a {{ it will work as usual (if x in Text)
txt_find = {
    'commons': ['{{no license', '{{no license/en',
                '{{nld', '{{no permission', '{{no permission since'],
    'meta': ['{{no license', '{{nolicense', '{{nld'],
    'test': ['{{no license'],
    'ar': ['{{لت', '{{لا ترخيص'],
    'de': ['{{DÜP', '{{Düp', '{{Dateiüberprüfung'],
    'en': ['{{nld', '{{no license'],
    'fa': ['{{حق تکثیر تصویر نامعلوم۲'],
    'ga': ['{{Ceadúnas de dhíth', '{{Ceadúnas de dhíth'],
    'hr': ['{{bez licence'],
    'hu': ['{{nincsforrás', '{{nincslicenc'],
    'it': ['{{unverdata', '{{unverified'],
    'ja': ['{{no source', '{{unknown',
           '{{non free', '<!--削除についての議論が終了するまで'],
    'ko': ['{{출처 없음', '{{라이선스 없음', '{{Unknown'],
    'ru': ['{{no license'],
    'sd': ['{{ناحوالا', '{{ااجازت نامعلوم', '{{Di-no'],
    'sr': ['{{датотека без лиценце', '{{датотека без извора'],
    'ta': ['{{no source', '{{nld', '{{no license'],
    'ur': ['{{ناحوالہ', '{{اجازہ نامعلوم', '{{Di-no'],
    'zh': ['{{no source', '{{unknown', '{{No license'],
}

# When the Bot find that the usertalk is empty is not pretty to put only the
# no source without the welcome, isn't it?
empty = {
    'commons': '{{subst:welcome}}\n~~~~\n',
    'meta': '{{subst:Welcome}}\n~~~~\n',
    'ar': '{{ترحيب}}\n~~~~\n',
    'de': '{{subst:willkommen}} ~~~~',
    'en': '{{welcome}}\n~~~~\n',
    'fa': '{{جا:خوشامدید|%s}}',
    'fr': '{{Bienvenue nouveau\n~~~~\n',
    'ga': '{{subst:Fáilte}} - ~~~~\n',
    'hr': '{{subst:dd}}--~~~~\n',
    'hu': '{{subst:Üdvözlet|~~~~}}\n',
    'it': '<!-- inizio template di benvenuto -->\n{{subst:Benvebot}}\n~~~~\n'
          '<!-- fine template di benvenuto -->',
    'ja': '{{subst:Welcome/intro}}\n{{subst:welcome|--~~~~}}\n',
    'ko': '{{환영}}--~~~~\n',
    'ru': '{{subst:Приветствие}}\n~~~~\n',
    'sd': '{{ڀليڪار}}\n~~~~\n',
    'sr': '{{dd}}--~~~~\n',
    'ta': '{{welcome}}\n~~~~\n',
    'ur': '{{خوش آمدید}}\n~~~~\n',
    'zh': '{{subst:welcome|sign=~~~~}}',
}

# if the file has an unknown extension it will be tagged with this template.
# In reality, there aren't unknown extension, they are only not allowed...
delete_immediately = {
    'commons': '{{speedy|The file has .%s as extension. '
               'Is it ok? Please check.}}',
    'meta': '{{Delete|The file has .%s as extension.}}',
    'ar': '{{شطب|الملف له .%s كامتداد.}}',
    'en': '{{db-meta|The file has .%s as extension.}}',
    'fa': '{{حذف سریع|تصویر %s اضافی است.}}',
    'ga': '{{scrios|Tá iarmhír .%s ar an comhad seo.}}',
    'hu': '{{azonnali|A fájlnak .%s a kiterjesztése}}',
    'it': '{{cancella subito|motivo=Il file ha come estensione ".%s"}}',
    'ja': '{{db|知らないファイルフォーマット %s}}',
    'ko': '{{delete|잘못된 파일 형식 (.%s)}}',
    'ru': '{{db-badimage}}',
    'sr': '{{speedy|Ова датотека садржи екстензију %s. '
               'Молим вас да проверите да ли је у складу са правилима.}}',
    'ta': '{{delete|'
          'இந்தக் கோப்பு .%s என்றக் கோப்பு நீட்சியைக் கொண்டுள்ளது.}}',
    'ur': '{{سریع حذف شدگی|اس ملف میں .%s بطور توسیع موجود ہے۔ }}',
    'zh': '{{delete|未知檔案格式%s}}',
}

# That's the text that the bot will add if it doesn't find the license.
# Note: every __botnick__ will be repleaced with your bot's nickname
# (feel free not to use if you don't need it)
nothing_notification = {
    'commons': "\n{{subst:User:Filnik/untagged|File:%s}}\n\n''This message "
               "was '''added automatically by ~~~''', if you need "
               'some help about it, please read the text above again and '
               'follow the links in it, if you still need help ask at the '
               '[[File:Human-help-browser.svg|18px|link=Commons:Help desk|?]] '
               "'''[[Commons:Help desk|->]][[Commons:Help desk]]''' in any "
               "language you like to use.'' --~~~~",
    'meta': '{{subst:No license notice|File:%s}}',
    'ar': '{{subst:مصدر الصورة|File:%s}} --~~~~',
    'en': '{{subst:image source|File:%s}} --~~~~',
    'fa': '{{جا:اخطار نگاره|%s}}',
    'ga': '{{subst:Foinse na híomhá|File:%s}} --~~~~',
    'hu': '{{subst:adjforrást|Kép:%s}}\n Ezt az üzenetet ~~~ automatikusan '
          'helyezte el a vitalapodon, kérdéseddel fordulj a gazdájához, vagy '
          'a [[WP:KF|Kocsmafalhoz]]. --~~~~',
    'it': '{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/Senza licenza|'
          '%s|~~~}} --~~~~',
    'ja': '\n{{subst:Image copyright|File:%s}}--~~~~',
    'ko': '\n{{subst:User:Kwjbot IV/untagged|%s}} --~~~~',
    'ru': '{{subst:Запрос о статусе файла|Файл:%s}} --~~~~',
    'sr': '\n{{subst:Обавештење о датотеци без лиценце|%s}} --~~~~',
    'sd': '{{subst:تصوير جو ذريعو|File:%s}}--~~~~',
    'ta': '\n{{subst:Di-no license-notice|படிமம்:%s}} ~~~~',
    'ur': '{{subst:ماخذ تصویر|File:%s}}--~~~~',
    'zh': '\n{{subst:Uploadvionotice|File:%s}} ~~~~',
}

# This is a list of what bots used this script in your project.
# NOTE: YOUR Bot username will be automatically added.
bot_list = {
    'commons': ['Siebot', 'CommonsDelinker', 'Filbot', 'Sz-iwbot',
                'ABFbot'],
    'meta': ['MABot'],
    'de': ['Xqbot'],
    'en': ['OrphanBot'],
    'fa': ['Amirobot'],
    'ga': ['AllieBot'],
    'it': ['Filbot', 'Nikbot', '.snoopybot.'],
    'ja': ['Alexbot'],
    'ko': ['Kwjbot IV'],
    'ru': ['Rubinbot'],
    'sr': ['KizuleBot'],
    'ta': ['TrengarasuBOT'],
    'ur': ['Shuaib-bot', 'Tahir-bot', 'SAMI.Bot'],
    'zh': ['Alexbot'],
}

# The message that the bot will add the second time that find another license
# problem.
second_message_without_license = {
    'hu': '\nSzia! Úgy tűnik a [[:Kép:%s]] képpel is hasonló a probléma, '
          'mint az előbbivel. Kérlek olvasd el a [[WP:KÉPLIC|feltölthető '
          'képek]]ről szóló oldalunk, és segítségért fordulj a [[WP:KF-JO|'
          'Jogi kocsmafalhoz]]. Köszönöm --~~~~',
    'it': ':{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/Senza'
          'licenza2|%s|~~~}} --~~~~',
}

# You can add some settings to a wiki page. In this way, you can change them
# without touching the code. That's useful if you are running the bot on
# Toolserver.
page_with_settings = {
    'commons': 'User:Filbot/Settings',
    'it': 'Progetto:Coordinamento/Immagini/Bot/Settings#Settings',
    'sr': 'User:KizuleBot/checkimages.py/подешавања',
    'zh': 'User:Alexbot/cisettings#Settings',
}

# The bot can report some images (like the images that have the same name of an
# image on commons) This is the page where the bot will store them.
report_page = {
    'commons': 'User:Filbot/Report',
    'meta': 'User:MABot/Report',
    'test': 'User:Pywikibot-test/Report',
    'de': 'Benutzer:Xqbot/Report',
    'en': 'User:Filnik/Report',
    'fa': 'کاربر:Amirobot/گزارش تصویر',
    'ga': 'User:AllieBot/ReportImages',
    'hu': 'User:Bdamokos/Report',
    'it': 'Progetto:Coordinamento/Immagini/Bot/Report',
    'ja': 'User:Alexbot/report',
    'ko': 'User:Kwjbot IV/Report',
    'ru': 'User:Rubinbot/Report',
    'sd': 'واپرائيندڙ:Kaleem Bhatti/درخواست تصوير',
    'sr': 'User:KizuleBot/checkimages.py/дневник',
    'ta': 'User:Trengarasu/commonsimages',
    'ur': 'صارف:محمد شعیب/درخواست تصویر',
    'zh': 'User:Alexsh/checkimagereport',
}

# If a template isn't a license but it's included on a lot of images, that can
# be skipped to analyze the image without taking care of it. (the template must
# be in a list)
# Warning:   Don't add template like "en, de, it" because they are already in
#            (added in the code, below
# Warning 2: The bot will use regex, make the names compatible, please (don't
#            add "Template:" or {{because they are already put in the regex).
# Warning 3: the part that use this regex is case-insensitive (just to let you
#            know..)
HiddenTemplate = {
    # Put the other in the page on the project defined below
    'commons': ['Template:Information'],
    'meta': ['Template:Information'],
    'test': ['Template:Information'],
    'ar': ['Template:معلومات'],
    'de': ['Template:Information'],
    'en': ['Template:Information'],
    'fa': ['الگو:اطلاعات'],
    'fr': ['Template:Information'],
    'ga': ['Template:Information'],
    'hr': ['Template:Infoslika'],
    'hu': ['Template:Információ', 'Template:Enwiki', 'Template:Azonnali'],
    'it': ['Template:EDP', 'Template:Informazioni file',
           'Template:Information', 'Template:Trademark',
           'Template:Permissionotrs'],
    'ja': ['Template:Information'],
    'ko': ['Template:그림 정보'],
    'ru': ['Template:Изображение',
           'Template:Обоснование добросовестного использования'],
    'sd': ['Template:معلومات'],
    'sr': ['Шаблон:Информација', 'Шаблон:Non-free use rationale 2'],
    'ta': ['Template:Information'],
    'ur': ['Template:معلومات'],
    'zh': ['Template:Information'],
}

# A page where there's a list of template to skip.
PageWithHiddenTemplates = {
    'commons': 'User:Filbot/White_templates#White_templates',
    'it': 'Progetto:Coordinamento/Immagini/Bot/WhiteTemplates',
    'ko': 'User:Kwjbot_IV/whitetemplates/list',
    'sr': 'User:KizuleBot/checkimages.py/дозвољенишаблони',
}

# A page where there's a list of template to consider as licenses.
PageWithAllowedTemplates = {
    'commons': 'User:Filbot/Allowed templates',
    'de': 'Benutzer:Xqbot/Lizenzvorlagen',
    'it': 'Progetto:Coordinamento/Immagini/Bot/AllowedTemplates',
    'ko': 'User:Kwjbot_IV/AllowedTemplates',
    'sr': 'User:KizuleBot/checkimages.py/дозвољенишаблони',
}

# Template added when the bot finds only an hidden template and nothing else.
# Note: every __botnick__ will be repleaced with your bot's nickname
# (feel free not to use if you don't need it)
HiddenTemplateNotification = {
    'commons': ("\n{{subst:User:Filnik/whitetemplate|File:%s}}\n\n''This "
                'message was added automatically by ~~~, if you need '
                'some help about it please read the text above again and '
                'follow the links in it, if you still need help ask at the '
                '[[File:Human-help-browser.svg|18px|link=Commons:Help desk|?]]'
                " '''[[Commons:Help desk|→]] [[Commons:Help desk]]''' in any "
                "language you like to use.'' --~~~~"),
    'it': '{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/'
          'Template_insufficiente|%s|~~~}} --~~~~',
    'ko': '\n{{subst:User:Kwj2772/whitetemplates|%s}} --~~~~',
}

# In this part there are the parameters for the dupe images.

# Put here the template that you want to put in the image to warn that it's a
# dupe. put __image__ if you want only one image, __images__ if you want the
# whole list
duplicatesText = {
    'commons': '\n{{Dupe|__image__}}',
    'de': '{{NowCommons}}',
    'it': '\n{{Progetto:Coordinamento/Immagini/Bot/Template duplicati|'
          '__images__}}',
    'ru': '{{NCT|__image__}}',
    'sr': '{{NowCommons|__image__}}',
}

# Message to put in the talk
duplicates_user_talk_text = {
    'it': '{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/Duplicati|'
          '%s|%s|~~~}} --~~~~',
}

# Regex to detect the template put in the image's description to find the dupe
duplicatesRegex = {
    'commons': r'\{\{(?:[Tt]emplate:|)(?:[Dd]up(?:licat|)e|[Bb]ad[ _][Nn]ame)'
               r'[|}]',
    'de': r'\{\{[nN](?:C|ow(?: c|[cC])ommons)[\|\}',
    'it': r'\{\{(?:[Tt]emplate:|)[Pp]rogetto:[Cc]oordinamento/Immagini/Bot/'
          r'Template duplicati[|}]',
    'sr': r'\{\{[nN](?:C|ow(?: c|[cC])ommons)[\|\}',
}

# Category with the licenses and / or with subcategories with the other
# licenses.
category_with_licenses = {
    'commons': 'Category:License tags',
    'meta': 'Category:License templates',
    'test': 'Category:CC license tags',
    'ar': 'تصنيف:قوالب حقوق الصور',
    'de': 'Kategorie:Vorlage:Lizenz für Bilder',
    'en': 'Category:Wikipedia file copyright templates',
    'fa': 'رده:الگو:حق تکثیر پرونده',
    'ga': "Catagóir:Clibeanna cóipchirt d'íomhánna",
    'it': 'Categoria:Template Licenze copyright',
    'ja': 'Category:画像の著作権表示テンプレート',
    'ko': '분류:위키백과 그림 저작권 틀',
    'ru': 'Category:Шаблоны:Лицензии файлов',
    'sd': 'زمرو:وڪيپيڊيا فائل ڪاپي رائيٽ سانچا',
    'sr': 'Категорија:Шаблони за слике',
    'ta': 'Category:காப்புரிமை வார்ப்புருக்கள்',
    'ur': 'زمرہ:ویکیپیڈیا سانچہ جات حقوق تصاویر',
    'zh': 'Category:版權申告模板',
}

# Page where is stored the message to send as email to the users
emailPageWithText = {
    # 'de': 'Benutzer:ABF/D3',
}

# Title of the email
emailSubject = {
    # 'de': 'Problemen mit Deinem Bild auf der Deutschen Wikipedia',
}

# Seems that uploaderBots aren't interested to get messages regarding the
# files that they upload.. strange, uh?
# Format: [[user,regex], [user,regex]...] the regex is needed to match the user
#         where to send the warning-msg
uploadBots = {
    'commons': [['File Upload Bot (Magnus Manske)',
                 r'\|[Ss]ource=Transferred from .*?; '
                 r'transferred to Commons by \[\[User:(.*?)\]\]']],
}

# Service images that don't have to be deleted and/or reported has a template
# inside them (you can let this param as None)
serviceTemplates = {
    'it': ['Template:Immagine di servizio'],
}

# Add your project (in alphabetical order) if you want that the bot starts
project_inserted = ['ar', 'commons', 'de', 'en', 'fa', 'ga', 'hu', 'it', 'ja',
                    'ko', 'ru', 'meta', 'sd', 'sr', 'ta', 'test', 'ur', 'zh']

# END OF CONFIGURATION.

SETTINGS_REGEX = re.compile(r"""
<-------\ ------->\n
\*[Nn]ame\ ?=\ ?['"](.*?)['"]\n
\*([Ff]ind|[Ff]indonly)\ ?=\ ?(.*?)\n
\*[Ii]magechanges\ ?=\ ?(.*?)\n
\*[Ss]ummary\ ?=\ ?['"](.*?)['"]\n
\*[Hh]ead\ ?=\ ?['"](.*?)['"]\n
\*[Tt]ext\ ?=\ ?['"](.*?)['"]\n
\*[Mm]ex\ ?=\ ?['"]?([^\n]*?)['"]?\n
""", re.DOTALL | re.VERBOSE)


class LogIsFull(Error):

    """Log is full and the Bot cannot add other data to prevent Errors."""


def printWithTimeZone(message) -> None:
    """Print the messages followed by the TimeZone encoded correctly."""
    time_zone = time.strftime('%d %b %Y %H:%M:%S (UTC)', time.gmtime())
    pywikibot.output('{} {}'.format(message.rstrip(), time_zone))


class checkImagesBot:

    """A robot to check recently uploaded files."""

    def __init__(self, site, logFulNumber=25000, sendemailActive=False,
                 duplicatesReport=False, logFullError=True,
                 max_user_notify=None) -> None:
        """Initializer, define some instance variables."""
        self.site = site
        self.logFullError = logFullError
        self.logFulNumber = logFulNumber
        self.rep_page = i18n.translate(self.site, report_page)
        if not self.rep_page:
            raise TranslationError(
                'No report page provided in "report_page" dict '
                'for your project!')
        self.image_namespace = site.namespaces.FILE.custom_name + ':'
        self.list_entry = '\n* [[:{}%s]] '.format(self.image_namespace)

        # The summary of the report
        self.com = i18n.twtranslate(self.site, 'checkimages-log-comment')

        hiddentemplatesRaw = i18n.translate(self.site, HiddenTemplate)
        if not hiddentemplatesRaw:
            raise TranslationError(
                'No non-license templates provided in "HiddenTemplate" dict '
                'for your project!')
        self.hiddentemplates = {
            pywikibot.Page(self.site, tmp, ns=self.site.namespaces.TEMPLATE)
            for tmp in hiddentemplatesRaw}
        self.pageHidden = i18n.translate(self.site, PageWithHiddenTemplates)
        self.pageAllowed = i18n.translate(self.site, PageWithAllowedTemplates)
        self.comment = i18n.twtranslate(self.site.lang,
                                        'checkimages-source-tag-comment')
        # Adding the bot's nickname at the notification text if needed.
        self.bots = i18n.translate(self.site, bot_list)
        if self.bots:
            self.bots.append(site.username())
        else:
            self.bots = [site.username()]

        self.sendemailActive = sendemailActive
        self.skip_list = []
        self.duplicatesReport = duplicatesReport

        if max_user_notify:
            self.num_notify = collections.defaultdict(lambda: max_user_notify)
        else:
            self.num_notify = None

        # Load the licenses only once, so do it once
        self.list_licenses = self.load_licenses()

    def setParameters(self, image) -> None:
        """Set parameters."""
        # ensure we have a FilePage
        self.image = pywikibot.FilePage(image)
        self.imageName = image.title(with_ns=False)
        self.timestamp = None
        self.uploader = None

    def report(self, newtext, image_to_report, notification=None, head=None,
               notification2=None, unver=True, commTalk=None, commImage=None
               ) -> None:
        """Function to make the reports easier."""
        self.image_to_report = image_to_report
        self.newtext = newtext
        if not newtext:
            raise TranslationError(
                'No no-license template provided in "n_txt" dict '
                'for your project!')
        self.head = head or ''
        self.notification = notification
        self.notification2 = notification2

        if self.notification:
            self.notification = re.sub(r'__botnick__', self.site.username(),
                                       notification)
        if self.notification2:
            self.notification2 = re.sub(r'__botnick__', self.site.username(),
                                        notification2)
        self.commTalk = commTalk
        self.commImage = commImage or self.comment
        image_tagged = False
        try:
            image_tagged = self.tag_image(unver)
        except NoPageError:
            pywikibot.output('The page has been deleted! Skip!')
        except EditConflictError:
            pywikibot.output('Edit conflict! Skip!')
        if image_tagged and self.notification:
            try:
                self.put_mex_in_talk()
            except EditConflictError:
                pywikibot.output('Edit Conflict! Retrying...')
                try:
                    self.put_mex_in_talk()
                except Exception:
                    pywikibot.exception()
                    pywikibot.output(
                        'Another error... skipping the user...')

    def uploadBotChangeFunction(self, reportPageText, upBotArray) -> str:
        """Detect the user that has uploaded the file through upload bot."""
        regex = upBotArray[1]
        results = re.findall(regex, reportPageText)

        if results:
            luser = results[0]
            return luser
        # we can't find the user, report the problem to the bot
        return upBotArray[0]

    def tag_image(self, put=True) -> bool:
        """Add template to the Image page and find out the uploader."""
        # Get the image's description
        reportPageObject = pywikibot.FilePage(self.site, self.image_to_report)

        try:
            reportPageText = reportPageObject.get()
        except NoPageError:
            pywikibot.output(self.imageName + ' has been deleted...')
            return False

        # You can use this function also to find only the user that
        # has upload the image (FixME: Rewrite a bit this part)
        if put:
            pywikibot.showDiff(reportPageText,
                               self.newtext + '\n' + reportPageText)
            pywikibot.output(self.commImage)
            try:
                reportPageObject.put(self.newtext + '\n' + reportPageText,
                                     summary=self.commImage)
            except LockedPageError:
                pywikibot.output('File is locked. Skipping.')
                return False

        # paginetta it's the image page object.
        try:
            if reportPageObject == self.image and self.uploader:
                nick = self.uploader
            else:
                nick = reportPageObject.latest_file_info.user
        except PageRelatedError:
            pywikibot.output(
                'Seems that {} has only the description and not the file...'
                .format(self.image_to_report))
            repme = self.list_entry + "problems '''with the APIs'''"
            self.report_image(self.image_to_report, self.rep_page, self.com,
                              repme)
            return False

        upBots = i18n.translate(self.site, uploadBots)
        user = pywikibot.User(self.site, nick)
        luser = user.title(as_url=True)

        if upBots:
            for upBot in upBots:
                if upBot[0] == luser:
                    luser = self.uploadBotChangeFunction(reportPageText, upBot)
                    user = pywikibot.User(self.site, luser)
        self.talk_page = user.getUserTalkPage()
        self.luser = luser
        return True

    def put_mex_in_talk(self) -> None:
        """Function to put the warning in talk page of the uploader."""
        commento2 = i18n.twtranslate(self.site.lang,
                                     'checkimages-source-notice-comment')
        emailPageName = i18n.translate(self.site, emailPageWithText)
        emailSubj = i18n.translate(self.site, emailSubject)
        if self.notification2:
            self.notification2 %= self.image_to_report
        else:
            self.notification2 = self.notification

        second_text = False
        # Getting the talk page's history, to check if there is another
        # advise...
        try:
            testoattuale = self.talk_page.get()
            history = list(self.talk_page.revisions(total=10))
            latest_user = history[0]['user']
            pywikibot.output(
                'The latest user that has written something is: '
                + latest_user)
            # A block to prevent the second message if the bot also
            # welcomed users...
            if latest_user in self.bots and len(history) > 1:
                second_text = True
        except IsRedirectPageError:
            pywikibot.output(
                'The user talk is a redirect, trying to get the right talk...')
            try:
                self.talk_page = self.talk_page.getRedirectTarget()
                testoattuale = self.talk_page.get()
            except NoPageError:
                testoattuale = i18n.translate(self.site, empty)
        except NoPageError:
            pywikibot.output('The user page is blank')
            testoattuale = i18n.translate(self.site, empty)

        if self.commTalk:
            commentox = self.commTalk
        else:
            commentox = commento2

        if second_text:
            newText = '{}\n\n{}'.format(testoattuale, self.notification2)
        else:
            newText = '{}\n\n== {} ==\n{}'.format(testoattuale, self.head,
                                                  self.notification)

        # Check maximum number of notifications for this talk page
        if (self.num_notify is not None
                and self.num_notify[self.talk_page.title()] == 0):
            pywikibot.output('Maximum notifications reached, skip.')
            return

        try:
            self.talk_page.put(newText, summary=commentox, minor=False)
        except LockedPageError:
            pywikibot.output('Talk page blocked, skip.')
        else:
            if self.num_notify is not None:
                self.num_notify[self.talk_page.title()] -= 1

        if emailPageName and emailSubj:
            emailPage = pywikibot.Page(self.site, emailPageName)
            try:
                emailText = emailPage.get()
            except (NoPageError, IsRedirectPageError):
                return
            if self.sendemailActive:
                text_to_send = re.sub(r'__user-nickname__', r'{}'
                                      .format(self.luser), emailText)
                emailClass = pywikibot.User(self.site, self.luser)
                try:
                    emailClass.send_email(emailSubj, text_to_send)
                except NotEmailableError:
                    pywikibot.output('User is not mailable, aborted')

    def regexGenerator(self, regexp, textrun) -> Generator[pywikibot.FilePage,
                                                           None, None]:
        """Find page to yield using regex to parse text."""
        regex = re.compile(r'{}'.format(regexp), re.DOTALL)
        results = regex.findall(textrun)
        for image in results:
            yield pywikibot.FilePage(self.site, image)

    def loadHiddenTemplates(self) -> None:
        """Function to load the white templates."""
        # A template as {{en is not a license! Adding also them in the
        # whitelist template...
        for langK in Family.load('wikipedia').langs.keys():
            self.hiddentemplates.add(pywikibot.Page(
                self.site, 'Template:{}'.format(langK)))
        # Hidden template loading
        if self.pageHidden:
            try:
                pageHiddenText = pywikibot.Page(self.site,
                                                self.pageHidden).get()
            except (NoPageError, IsRedirectPageError):
                pageHiddenText = ''

            for element in self.load(pageHiddenText):
                self.hiddentemplates.add(pywikibot.Page(self.site, element))

    def important_image(self, listGiven) -> pywikibot.FilePage:
        """
        Get tuples of image and time, return the most used or oldest image.

        :param listGiven: a list of tuples which hold seconds and FilePage
        :type listGiven: list
        :return: the most used or oldest image
        """
        # find the most used image
        inx_found = None  # index of found image
        max_usage = 0  # hold max amount of using pages
        for num, element in enumerate(listGiven):
            image = element[1]
            image_used = len(list(image.usingPages()))
            if image_used > max_usage:
                max_usage = image_used
                inx_found = num

        if inx_found is not None:
            return listGiven[inx_found][1]

        # find the oldest image
        sec, image = max(listGiven, key=lambda element: element[0])
        return image

    def checkImageOnCommons(self) -> bool:
        """Checking if the file is on commons."""
        pywikibot.output('Checking if [[{}]] is on commons...'
                         .format(self.imageName))
        try:
            hash_found = self.image.latest_file_info.sha1
        except NoPageError:
            return False  # Image deleted, no hash found. Skip the image.

        site = pywikibot.Site('commons', 'commons')
        commons_image_with_this_hash = next(
            iter(site.allimages(sha1=hash_found, total=1)), None)
        if commons_image_with_this_hash:
            servTMP = pywikibot.translate(self.site, serviceTemplates)
            templatesInTheImage = self.image.templates()
            if servTMP is not None:
                for template in servTMP:
                    if pywikibot.Page(self.site,
                                      template) in templatesInTheImage:
                        pywikibot.output(
                            "{} is on commons but it's a service image."
                            .format(self.imageName))
                        return True  # continue with the check-part

            pywikibot.output(self.imageName + ' is on commons!')
            if self.image.file_is_shared():
                pywikibot.output(
                    "But, the file doesn't exist on your project! Skip...")
                # We have to skip the check part for that image because
                # it's on commons but someone has added something on your
                # project.
                return False

            if re.findall(r'\bstemma\b', self.imageName.lower()) and \
               self.site.code == 'it':
                pywikibot.output(
                    "{} has 'stemma' inside, means that it's ok."
                    .format(self.imageName))
                return True

            # It's not only on commons but the image needs a check
            # the second usually is a url or something like that.
            # Compare the two in equal way, both url.
            repme = ((self.list_entry
                      + "is also on '''Commons''': [[commons:File:%s]]")
                     % (self.imageName,
                        commons_image_with_this_hash.title(
                            with_ns=False)))
            if (self.image.title(as_url=True)
                    == commons_image_with_this_hash.title(as_url=True)):
                repme += ' (same name)'
            self.report_image(self.imageName, self.rep_page, self.com, repme,
                              addings=False)
        return True

    def checkImageDuplicated(self, duplicates_rollback) -> bool:
        """Function to check the duplicated files."""
        dupText = i18n.translate(self.site, duplicatesText)
        dupRegex = i18n.translate(self.site, duplicatesRegex)
        dupTalkText = i18n.translate(self.site, duplicates_user_talk_text)

        # Head of the message given to the author
        dupTalkHead = i18n.twtranslate(self.site, 'checkimages-doubles-head')
        # Comment while bot reports the problem in the uploader's talk
        dupComment_talk = i18n.twtranslate(self.site,
                                           'checkimages-doubles-talk-comment')
        # Comment used by the bot while it reports the problem in the image
        dupComment_image = i18n.twtranslate(self.site,
                                            'checkimages-doubles-file-comment')

        imagePage = pywikibot.FilePage(self.site, self.imageName)
        hash_found = imagePage.latest_file_info.sha1
        duplicates = list(self.site.allimages(sha1=hash_found))

        if not duplicates:
            return False  # Image deleted, no hash found. Skip the image.

        if len(duplicates) > 1:
            xdict = {'en':
                     '%(name)s has {{PLURAL:count'
                     '|a duplicate! Reporting it'
                     '|%(count)s duplicates! Reporting them}}...'}
            pywikibot.output(i18n.translate('en', xdict,
                                            {'name': self.imageName,
                                             'count': len(duplicates) - 1}))
            if dupText and dupRegex:
                time_image_list = []

                for dup_page in duplicates:
                    if (dup_page.title(as_url=True) != self.image.title(
                        as_url=True)
                            or self.timestamp is None):
                        try:
                            self.timestamp = (
                                dup_page.latest_file_info.timestamp)
                        except PageRelatedError:
                            continue
                    data = self.timestamp.timetuple()
                    data_seconds = time.mktime(data)
                    time_image_list.append([data_seconds, dup_page])
                Page_older_image = self.important_image(time_image_list)
                older_page_text = Page_older_image.text
                # And if the images are more than two?
                string = ''
                images_to_tag_list = []

                for dup_page in duplicates:
                    if dup_page == Page_older_image:
                        # the most used or oldest image
                        # not report also this as duplicate
                        continue
                    try:
                        DupPageText = dup_page.text
                    except NoPageError:
                        continue

                    if not (re.findall(dupRegex, DupPageText)
                            or re.findall(dupRegex, older_page_text)):
                        pywikibot.output(
                            '{} is a duplicate and has to be tagged...'
                            .format(dup_page))
                        images_to_tag_list.append(dup_page.title())
                        string += '* {}\n'.format(
                            dup_page.title(as_link=True, textlink=True))
                    else:
                        pywikibot.output(
                            "Already put the dupe-template in the files's page"
                            " or in the dupe's page. Skip.")
                        return False  # Ok - Let's continue the checking phase

                # true if the image are not to be tagged as dupes
                only_report = False

                # put only one image or the whole list according to the request
                if '__images__' in dupText:
                    text_for_the_report = dupText.replace(
                        '__images__',
                        '\n{}* {}\n'.format(
                            string,
                            Page_older_image.title(
                                as_link=True, textlink=True)))
                else:
                    text_for_the_report = dupText.replace(
                        '__image__',
                        Page_older_image.title(as_link=True, textlink=True))

                # Two iteration: report the "problem" to the user only once
                # (the last)
                if len(images_to_tag_list) > 1:
                    for image_to_tag in images_to_tag_list[:-1]:
                        fp = pywikibot.FilePage(self.site, image_to_tag)
                        already_reported_in_past = fp.revision_count(self.bots)
                        # if you want only one edit, the edit found should be
                        # more than 0 -> num - 1
                        if already_reported_in_past > duplicates_rollback - 1:
                            only_report = True
                            break
                        # Delete the image in the list where we're write on
                        image = self.image_namespace + image_to_tag
                        text_for_the_report = re.sub(
                            r'\n\*\[\[:{}\]\]'.format(re.escape(image)),
                            '', text_for_the_report)
                        self.report(text_for_the_report, image_to_tag,
                                    commImage=dupComment_image, unver=True)

                if images_to_tag_list and not only_report:
                    fp = pywikibot.FilePage(self.site, images_to_tag_list[-1])
                    already_reported_in_past = fp.revision_count(self.bots)
                    image_title = re.escape(self.image.title(as_url=True))
                    from_regex = (r'\n\*\[\[:{}{}\]\]'
                                  .format(self.image_namespace, image_title))
                    # Delete the image in the list where we're write on
                    text_for_the_report = re.sub(from_regex, '',
                                                 text_for_the_report)
                    # if you want only one edit, the edit found should be more
                    # than 0 -> num - 1
                    if already_reported_in_past > duplicates_rollback - 1 or \
                            not dupTalkText:
                        only_report = True
                    else:
                        self.report(
                            text_for_the_report, images_to_tag_list[-1],
                            dupTalkText
                            % (Page_older_image.title(with_ns=True),
                               string),
                            dupTalkHead, commTalk=dupComment_talk,
                            commImage=dupComment_image, unver=True)

            if self.duplicatesReport or only_report:
                if only_report:
                    repme = ((self.list_entry + 'has the following duplicates '
                              "('''forced mode'''):")
                             % self.image.title(as_url=True))
                else:
                    repme = (
                        (self.list_entry + 'has the following duplicates:')
                        % self.image.title(as_url=True))

                for dup_page in duplicates:
                    if (dup_page.title(as_url=True)
                            == self.image.title(as_url=True)):
                        # the image itself, not report also this as duplicate
                        continue
                    repme += '\n** [[:{}{}]]'.format(
                        self.image_namespace, dup_page.title(as_url=True))

                result = self.report_image(self.imageName, self.rep_page,
                                           self.com, repme, addings=False)
                if not result:
                    return True  # If Errors, exit (but continue the check)

            if Page_older_image.title() != self.imageName:
                # The image is a duplicate, it will be deleted. So skip the
                # check-part, useless
                return False
        return True  # Ok - No problem. Let's continue the checking phase

    def report_image(self, image_to_report, rep_page=None, com=None,
                     rep_text=None, addings=True) -> bool:
        """Report the files to the report page when needed."""
        rep_page = rep_page or self.rep_page
        com = com or self.com
        rep_text = rep_text or self.list_entry + '~~~~~'

        if addings:
            # Adding the name of the image in the report if not done already
            rep_text = rep_text % image_to_report

        another_page = pywikibot.Page(self.site, rep_page)
        try:
            text_get = another_page.get()
        except NoPageError:
            text_get = ''
        except IsRedirectPageError:
            text_get = another_page.getRedirectTarget().get()

        # Don't care for differences inside brackets.
        end = rep_text.find('(', max(0, rep_text.find(']]')))
        if end < 0:
            end = None
        short_text = rep_text[rep_text.find('[['):end].strip()

        reported = True
        # Skip if the message is already there.
        if short_text in text_get:
            pywikibot.output('{} is already in the report page.'
                             .format(image_to_report))
            reported = False
        elif len(text_get) >= self.logFulNumber:
            if self.logFullError:
                raise LogIsFull(
                    'The log page ({}) is full! Please delete the old files '
                    'reported.'.format(another_page.title()))

            pywikibot.output(
                'The log page ({}) is full! Please delete the old files '
                ' reported. Skip!'.format(another_page.title()))
            # Don't report, but continue with the check
            # (we don't know if this is the first time we check this file
            # or not)
        else:
            # Adding the log
            another_page.put(text_get + rep_text, summary=com, force=True,
                             minor=False)
            pywikibot.output('...Reported...')
        return reported

    def takesettings(self) -> None:
        """Function to take the settings from the wiki."""
        settingsPage = i18n.translate(self.site, page_with_settings)
        try:
            if not settingsPage:
                self.settingsData = None
            else:
                wikiPage = pywikibot.Page(self.site, settingsPage)
                self.settingsData = []
                try:
                    testo = wikiPage.get()
                    number = 1

                    for m in SETTINGS_REGEX.finditer(testo):
                        name = str(m.group(1))
                        find_tipe = str(m.group(2))
                        find = str(m.group(3))
                        imagechanges = str(m.group(4))
                        summary = str(m.group(5))
                        head = str(m.group(6))
                        text = str(m.group(7))
                        mexcatched = str(m.group(8))
                        tupla = [number, name, find_tipe, find, imagechanges,
                                 summary, head, text, mexcatched]
                        self.settingsData += [tupla]
                        number += 1

                    if not self.settingsData:
                        pywikibot.output(
                            "You've set wrongly your settings, please take a "
                            'look to the relative page. (run without them)')
                        self.settingsData = None
                except NoPageError:
                    pywikibot.output("The settings' page doesn't exist!")
                    self.settingsData = None
        except Error:
            pywikibot.output(
                'Problems with loading the settigs, run without them.')
            self.settingsData = None
            self.some_problem = False

        if not self.settingsData:
            self.settingsData = None

        # Real-Time page loaded
        if self.settingsData:
            pywikibot.output('>> Loaded the real-time page... <<')
        else:
            pywikibot.output('>> No additional settings found! <<')

    def load_licenses(self) -> List[pywikibot.Page]:
        """Load the list of the licenses."""
        catName = i18n.translate(self.site, category_with_licenses)
        if not catName:
            raise TranslationError(
                'No allowed licenses category provided in '
                '"category_with_licenses" dict for your project!')
        pywikibot.output('\nLoading the allowed licenses...\n')
        cat = pywikibot.Category(self.site, catName)
        list_licenses = list(cat.articles())
        if self.site.code == 'commons':
            no_licenses_to_skip = pywikibot.Category(self.site,
                                                     'License-related tags')
            for license_given in no_licenses_to_skip.articles():
                if license_given in list_licenses:
                    list_licenses.remove(license_given)
        pywikibot.output('')

        # Add the licenses set in the default page as licenses to check
        if self.pageAllowed:
            try:
                pageAllowedText = pywikibot.Page(self.site,
                                                 self.pageAllowed).get()
            except (NoPageError, IsRedirectPageError):
                pageAllowedText = ''

            for nameLicense in self.load(pageAllowedText):
                pageLicense = pywikibot.Page(self.site, nameLicense)
                if pageLicense not in list_licenses:
                    # the list has wiki-pages
                    list_licenses.append(pageLicense)
        return list_licenses

    def miniTemplateCheck(self, template) -> bool:
        """Check if template is in allowed licenses or in licenses to skip."""
        # the list_licenses are loaded in the __init__
        # (not to load them multimple times)
        if template in self.list_licenses:
            self.license_selected = template.title(with_ns=False)
            self.seems_ok = True
            # let the last "fake" license normally detected
            self.license_found = self.license_selected
            return True

        if template in self.hiddentemplates:
            # if the whitetemplate is not in the images description, we don't
            # care
            try:
                self.allLicenses.remove(template)
            except ValueError:
                return False
            else:
                self.whiteTemplatesFound = True
        return False

    def templateInList(self) -> None:
        """
        Check if template is in list.

        The problem is the calls to the Mediawiki system because they can be
        pretty slow. While searching in a list of objects is really fast, so
        first of all let's see if we can find something in the info that we
        already have, then make a deeper check.
        """
        for template in self.licenses_found:
            if self.miniTemplateCheck(template):
                break
        if not self.license_found:
            for template in self.licenses_found:
                if template.isRedirectPage():
                    template = template.getRedirectTarget()
                    if self.miniTemplateCheck(template):
                        break

    def smartDetection(self) -> Tuple[str, bool]:
        """
        Detect templates.

        The bot instead of checking if there's a simple template in the
        image's description, checks also if that template is a license or
        something else. In this sense this type of check is smart.
        """
        self.seems_ok = False
        self.license_found = None
        self.whiteTemplatesFound = False
        regex_find_licenses = re.compile(
            r'(?<!\{)\{\{(?:[Tt]emplate:|)([^{]+?)[|\n<}]', re.DOTALL)
        regex_are_licenses = re.compile(
            r'(?<!\{)\{\{(?:[Tt]emplate:|)([^{]+?)\}\}', re.DOTALL)
        while True:
            self.loadHiddenTemplates()
            self.licenses_found = self.image.templates()
            templatesInTheImageRaw = regex_find_licenses.findall(
                self.imageCheckText)

            if not self.licenses_found and templatesInTheImageRaw:
                # {{nameTemplate|something <- this is not a template, be sure
                # that we haven't catch something like that.
                licenses_TEST = regex_are_licenses.findall(self.imageCheckText)
                if not self.licenses_found and licenses_TEST:
                    raise Error(
                        "Invalid or broken templates found in the image's "
                        'page {}!'.format(self.image))
            self.allLicenses = []

            if not self.list_licenses:
                raise TranslationError(
                    'No allowed licenses found in "category_with_licenses" '
                    'category for your project!')

            # Found the templates ONLY in the image's description
            for template_selected in templatesInTheImageRaw:
                tp = pywikibot.Page(self.site, template_selected)
                for templateReal in self.licenses_found:
                    if (tp.title(as_url=True, with_ns=False).lower()
                            == templateReal.title(as_url=True,
                                                  with_ns=False).lower()):
                        if templateReal not in self.allLicenses:
                            self.allLicenses.append(templateReal)
            break

        if self.licenses_found:
            self.templateInList()

            if not self.license_found and self.allLicenses:
                self.allLicenses = [
                    template.getRedirectTarget()
                    if template.isRedirectPage() else template
                    for template in self.allLicenses if template.exists()]

                if self.allLicenses:
                    self.license_found = self.allLicenses[0].title()

        # If it has "some_problem" it must check the additional settings.
        self.some_problem = False

        if self.settingsData:
            # use additional settings
            self.findAdditionalProblems()

        if self.some_problem:
            if self.mex_used in self.imageCheckText:
                pywikibot.output('File already fixed. Skipping.')
            else:
                pywikibot.output(
                    "The file's description for {} contains {}..."
                    .format(self.imageName, self.name_used))
                if self.mex_used.lower() == 'default':
                    self.mex_used = self.unvertext
                if self.imagestatus_used:
                    reported = True
                else:
                    reported = self.report_image(self.imageName)
                if reported:
                    self.report(self.mex_used, self.imageName, self.text_used,
                                self.head_used, None,
                                self.imagestatus_used, self.summary_used)
                else:
                    pywikibot.output('Skipping the file...')
                self.some_problem = False
        else:
            if not self.seems_ok and self.license_found:
                rep_text_license_fake = ((self.list_entry
                                          + "seems to have a ''fake license'',"
                                          ' license detected:'
                                          ' <nowiki>%s</nowiki>') %
                                         (self.imageName, self.license_found))
                printWithTimeZone(
                    '{} seems to have a fake license: {}, reporting...'
                    .format(self.imageName, self.license_found))
                self.report_image(self.imageName,
                                  rep_text=rep_text_license_fake,
                                  addings=False)
            elif self.license_found:
                pywikibot.output('[[%s]] seems ok, license found: {{%s}}...'
                                 % (self.imageName, self.license_found))
        return (self.license_found, self.whiteTemplatesFound)

    def load(self, raw) -> List[str]:
        """Load a list of objects from a string using regex."""
        list_loaded = []
        # I search with a regex how many user have not the talk page
        # and i put them in a list (i find it more easy and secure)
        regl = r"(\"|\')(.*?)\1(?:,|\])"
        pl = re.compile(regl)
        for xl in pl.finditer(raw):
            word = xl.group(2).replace('\\\\', '\\')
            if word not in list_loaded:
                list_loaded.append(word)
        return list_loaded

    def skipImages(self, skip_number, limit) -> bool:
        """Given a number of files, skip the first -number- files."""
        # If the images to skip are more the images to check, make them the
        # same number
        if skip_number == 0:
            pywikibot.output('\t\t>> No files to skip...<<')
            return False
        if skip_number > limit:
            skip_number = limit
        # Print a starting message only if no images has been skipped
        if not self.skip_list:
            pywikibot.output(
                i18n.translate(
                    'en',
                    'Skipping the first {{PLURAL:num|file|%(num)s files}}:\n',
                    {'num': skip_number}))
        # If we still have pages to skip:
        if len(self.skip_list) < skip_number:
            pywikibot.output('Skipping {}...'.format(self.imageName))
            self.skip_list.append(self.imageName)
            if skip_number == 1:
                pywikibot.output('')
            return True
        pywikibot.output('')
        return False

    @staticmethod
    def wait(generator, wait_time) -> Generator[pywikibot.FilePage, None,
                                                None]:
        """
        Skip the images uploaded before x seconds.

        Let the users to fix the image's problem alone in the first x seconds.
        """
        printWithTimeZone(
            'Skipping the files uploaded less than {} seconds ago..'
            .format(wait_time))
        for page in generator:
            image = pywikibot.FilePage(page)
            try:
                timestamp = image.latest_file_info.timestamp
            except PageRelatedError:
                continue
            now = pywikibot.Timestamp.utcnow()
            delta = now - timestamp
            if delta.total_seconds() > wait_time:
                yield image
            else:
                pywikibot.warning(
                    'Skipping {}, uploaded {} {} ago..'
                    .format(image.title(), delta.days, 'days')
                    if delta.days > 0
                    else (image.title(), delta.seconds, 'seconds'))

    def isTagged(self) -> bool:
        """Understand if a file is already tagged or not."""
        # TODO: enhance and use textlib.MultiTemplateMatchBuilder
        # Is the image already tagged? If yes, no need to double-check, skip
        no_license = i18n.translate(self.site, txt_find)
        if not no_license:
            raise TranslationError(
                'No no-license templates provided in "txt_find" dict '
                'for your project!')
        for i in no_license:
            # If there are {{ use regex, otherwise no (if there's not the
            # {{ may not be a template and the regex will be wrong)
            if '{{' in i:
                regexP = re.compile(
                    r'\{\{(?:template)?%s ?(?:\||\r?\n|\}|<|/) ?'
                    % i.split('{{')[1].replace(' ', '[ _]'), re.I)
                result = regexP.findall(self.imageCheckText)
                if result:
                    return True
            elif i.lower() in self.imageCheckText:
                return True
        return False

    def findAdditionalProblems(self) -> None:
        """Extract additional settings from configuration page."""
        # In every tuple there's a setting configuration
        for tupla in self.settingsData:
            name = tupla[1]
            find_tipe = tupla[2]
            find = tupla[3]
            find_list = self.load(find)
            imagechanges = tupla[4]
            if imagechanges.lower() == 'false':
                imagestatus = False
            elif imagechanges.lower() == 'true':
                imagestatus = True
            else:
                pywikibot.error('Imagechanges set wrongly!')
                self.settingsData = None
                break
            summary = tupla[5]
            head_2 = tupla[6]
            if head_2.count('==') == 2:
                head_2 = re.findall(r'\s*== *(.+?) *==\s*', head_2)[0]
            text = tupla[7] % self.imageName
            mexCatched = tupla[8]
            for k in find_list:
                if find_tipe.lower() == 'findonly':
                    searchResults = re.findall(r'{}'.format(k.lower()),
                                               self.imageCheckText.lower())
                    if searchResults:
                        if searchResults[0] == self.imageCheckText.lower():
                            self.some_problem = True
                            self.text_used = text
                            self.head_used = head_2
                            self.imagestatus_used = imagestatus
                            self.name_used = name
                            self.summary_used = summary
                            self.mex_used = mexCatched
                            break
                elif find_tipe.lower() == 'find':
                    if re.findall(r'{}'.format(k.lower()),
                                  self.imageCheckText.lower()):
                        self.some_problem = True
                        self.text_used = text
                        self.head_used = head_2
                        self.imagestatus_used = imagestatus
                        self.name_used = name
                        self.summary_used = summary
                        self.mex_used = mexCatched
                        continue

    def checkStep(self) -> None:
        """Check a single file page."""
        # something = Minimal requirements for an image description.
        # If this fits, no tagging will take place
        # (if there aren't other issues)
        # MIT license is ok on italian wikipedia, let also this here

        # Don't put "}}" here, please. Useless and can give problems.
        something = ['{{']
        # Allowed extensions
        try:
            allowed_formats = self.site.siteinfo.get(
                'fileextensions', get_default=False)
        except KeyError:
            allowed_formats = []
        else:
            allowed_formats = [item['ext'].lower() for item in allowed_formats]
        brackets = False
        delete = False
        notification = None
        # get the extension from the image's name
        extension = self.imageName.split('.')[-1]
        # Load the notification messages
        HiddenTN = i18n.translate(self.site, HiddenTemplateNotification)
        self.unvertext = i18n.translate(self.site, n_txt)
        di = i18n.translate(self.site, delete_immediately)

        # The header of the Unknown extension's message.
        dih = i18n.twtranslate(self.site, 'checkimages-unknown-extension-head')
        # Text that will be add if the bot find a unknown extension.
        din = i18n.twtranslate(self.site,
                               'checkimages-unknown-extension-msg') + ' ~~~~'
        # Header that the bot will add if the image hasn't the license.
        nh = i18n.twtranslate(self.site, 'checkimages-no-license-head')
        # Summary of the delete immediately.
        dels = i18n.twtranslate(self.site, 'checkimages-deletion-comment')

        nn = i18n.translate(self.site, nothing_notification)
        smwl = i18n.translate(self.site, second_message_without_license)

        try:
            self.imageCheckText = self.image.get()
        except NoPageError:
            pywikibot.output('Skipping {} because it has been deleted.'
                             .format(self.imageName))
            return
        except IsRedirectPageError:
            pywikibot.output("Skipping {} because it's a redirect."
                             .format(self.imageName))
            return

        # Delete the fields where the templates cannot be loaded
        regex_nowiki = re.compile(r'<nowiki>(.*?)</nowiki>', re.DOTALL)
        regex_pre = re.compile(r'<pre>(.*?)</pre>', re.DOTALL)
        self.imageCheckText = regex_nowiki.sub('', self.imageCheckText)
        self.imageCheckText = regex_pre.sub('', self.imageCheckText)

        # Deleting the useless template from the description (before adding
        # sth in the image the original text will be reloaded, don't worry).
        if self.isTagged():
            printWithTimeZone('{} is already tagged...'.format(self.imageName))
            return

        # something is the array with {{, MIT License and so on.
        for a_word in something:
            if a_word in self.imageCheckText:
                # There's a template, probably a license
                brackets = True

        # Is the extension allowed? (is it an image or f.e. a .xls file?)
        if allowed_formats and extension.lower() not in allowed_formats:
            delete = True

        (license_found, hiddenTemplateFound) = self.smartDetection()

        # Here begins the check block.
        if brackets and license_found:
            return

        if delete:
            pywikibot.output('{} is not a file!'.format(self.imageName))
            if not di:
                pywikibot.output('No localized message given for '
                                 "'delete_immediately'. Skipping.")
                return

            # Some formatting for delete immediately template
            dels = dels % {'adding': di}
            di = '\n' + di

            # Modify summary text
            config.default_edit_summary = dels

            canctext = di % extension
            notification = din % {'file': self.image.title(as_link=True,
                                                           textlink=True)}
            head = dih
            self.report(canctext, self.imageName, notification, head)
            return

        if not self.imageCheckText.strip():  # empty image description
            pywikibot.output(
                "The file's description for {} does not contain a license "
                ' template!'.format(self.imageName))
            if hiddenTemplateFound and HiddenTN:
                notification = HiddenTN % self.imageName
            elif nn:
                notification = nn % self.imageName
            head = nh
            self.report(self.unvertext, self.imageName, notification, head,
                        smwl)
            return

        pywikibot.output('{} has only text and not the specific '
                         'license...'.format(self.imageName))
        if hiddenTemplateFound and HiddenTN:
            notification = HiddenTN % self.imageName
        elif nn:
            notification = nn % self.imageName
        head = nh
        self.report(self.unvertext, self.imageName, notification, head, smwl)


def main(*args: str) -> bool:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    # Command line configurable parameters
    repeat = True  # Restart after having check all the images?
    limit = 80  # How many images check?
    time_sleep = 30  # How many time sleep after the check?
    skip_number = 0  # How many images to skip before checking?
    waitTime = 0  # How many time sleep before the check?
    commonsActive = False  # Is there's an image with the same name at commons?
    normal = False  # Check the new images or use another generator?
    urlUsed = False  # Use the url-related function instead of the new-pages
    regexGen = False  # Use the regex generator
    duplicatesActive = False  # Use the duplicate option
    duplicatesReport = False  # Use the duplicate-report option
    max_user_notify = None
    sendemailActive = False  # Use the send-email
    logFullError = True  # Raise an error when the log is full
    generator = None
    unknown = []  # unknown parameters

    local_args = pywikibot.handle_args(args)
    site = pywikibot.Site()
    # Here below there are the local parameters.
    for arg in local_args:
        option, _, value = arg.partition(':')
        if option == '-limit':
            limit = int(value or pywikibot.input(
                'How many files do you want to check?'))
        elif option == '-sleep':
            time_sleep = int(value or pywikibot.input(
                'How many seconds do you want runs to be apart?'))
        elif option == '-break':
            repeat = False
        elif option == '-nologerror':
            logFullError = False
        elif option == '-commons':
            commonsActive = True
        elif option == '-duplicatesreport':
            duplicatesReport = True
        elif option == '-duplicates':
            duplicatesActive = True
            duplicates_rollback = int(value or 1)
        elif option == '-maxusernotify':
            max_user_notify = int(value or pywikibot.input(
                'What should be the maximum number of notifications per user '
                'per check?'))
        elif option == '-sendemail':
            sendemailActive = True
        elif option == '-skip':
            skip_number = int(value or pywikibot.input(
                'How many files do you want to skip?'))
        elif option == '-wait':
            waitTime = int(value or pywikibot.input(
                'How many time do you want to wait before checking the '
                'files?'))
        elif option == '-start':
            firstPageTitle = value or pywikibot.input(
                'From which page do you want to start?')
            namespaces = tuple(
                ns + ':' for ns in site.namespace(Namespace.FILE, True))
            if firstPageTitle.startswith(namespaces):
                firstPageTitle = firstPageTitle.split(':', 1)[1]
            generator = site.allimages(start=firstPageTitle)
            repeat = False
        elif option == '-page':
            regexPageName = value or pywikibot.input(
                'Which page do you want to use for the regex?')
            repeat = False
            regexGen = True
        elif option == '-url':
            regexPageUrl = value or pywikibot.input(
                'Which url do you want to use for the regex?')
            urlUsed = True
            repeat = False
            regexGen = True
        elif option == '-regex':
            regexpToUse = value or pywikibot.input(
                'Which regex do you want to use?')
            generator = 'regex'
            repeat = False
        elif option == '-cat':
            cat_name = value or pywikibot.input('In which category do I work?')
            cat = pywikibot.Category(site, 'Category:' + cat_name)
            generator = cat.articles(namespaces=[6])
            repeat = False
        elif option == '-ref':
            ref_name = value or pywikibot.input(
                'The references of what page should I parse?')
            ref = pywikibot.Page(site, ref_name)
            generator = ref.getReferences(namespaces=[6])
            repeat = False
        else:
            unknown.append(arg)

    if not generator:
        normal = True

    # Ensure that the bot is localized and right command args are given
    if site.code not in project_inserted:
        additional_text = ('Your project is not supported by this script.\n'
                           'To allow your project in the script you have to '
                           'add a localization into the script and add your '
                           'project to the "project_inserted" list!')
    else:
        additional_text = ''
    if suggest_help(unknown_parameters=unknown,
                    additional_text=additional_text):
        return False

    # Reading the log of the new images if another generator is not given.
    if normal:
        if limit == 1:
            pywikibot.output('Retrieving the latest file for checking...')
        else:
            pywikibot.output('Retrieving the latest {} files for checking...'
                             .format(limit))
    while True:
        # Defing the Main Class.
        Bot = checkImagesBot(site, sendemailActive=sendemailActive,
                             duplicatesReport=duplicatesReport,
                             logFullError=logFullError,
                             max_user_notify=max_user_notify)
        if normal:
            generator = pg.NewimagesPageGenerator(total=limit, site=site)
        # if urlUsed and regexGen, get the source for the generator
        if urlUsed and regexGen:
            textRegex = site.getUrl(regexPageUrl, no_hostname=True)
        # Not an url but a wiki page as "source" for the regex
        elif regexGen:
            pageRegex = pywikibot.Page(site, regexPageName)
            try:
                textRegex = pageRegex.get()
            except NoPageError:
                pywikibot.output("{} doesn't exist!".format(pageRegex.title()))
                textRegex = ''  # No source, so the bot will quit later.
        # If generator is the regex' one, use your own Generator using an url
        # or page and a regex.
        if generator == 'regex' and regexGen:
            generator = Bot.regexGenerator(regexpToUse, textRegex)

        Bot.takesettings()
        if waitTime > 0:
            generator = Bot.wait(generator, waitTime)
        for image in generator:
            # Setting the image for the main class
            Bot.setParameters(image)

            if skip_number and Bot.skipImages(skip_number, limit):
                continue

            # Check on commons if there's already an image with the same name
            if commonsActive and site.family.name != 'commons':
                if not Bot.checkImageOnCommons():
                    continue

            # Check if there are duplicates of the image on the project
            if duplicatesActive:
                if not Bot.checkImageDuplicated(duplicates_rollback):
                    continue

            Bot.checkStep()

        if repeat:
            pywikibot.output('Waiting for {} seconds,'.format(time_sleep))
            pywikibot.sleep(time_sleep)
        else:
            break
    return True


if __name__ == '__main__':
    start = time.time()
    ret = False
    try:
        ret = main()
    except KeyboardInterrupt:
        ret = True
    finally:
        if ret is not False:
            final = time.time()
            delta = int(final - start)
            pywikibot.output('Execution time: {} seconds\n'.format(delta))
