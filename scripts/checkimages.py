#!/usr/bin/env python3
"""
Script to check recently uploaded files.

This script checks if a file description is present and if there are other
problems in the image's description.

This script will have to be configured for each language. Please submit
translations as addition to the Pywikibot framework.

Everything that needs customisation is indicated by comments.

This script understands the following command-line arguments:

-limit              The number of images to check (default: 80)

-commons            The bot will check if an image on Commons has the same name
                    and if true it reports the image.

-duplicates[:#]     Checking if the image has duplicates (if arg, set how many
                    rollback wait before reporting the image in the report
                    instead of tag the image) default: 1 rollback.

-duplicatesreport   Report the duplicates in a log *AND* put the template in
                    the images.

-maxusernotify      Maximum notifications added to a user talk page in a single
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

In this way the bot can understand where the block starts in order to take the
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
# (C) Pywikibot team, 2006-2022
#
# Distributed under the terms of the MIT license.
#
import collections
import re
import time
from itertools import zip_longest
from typing import Generator

import pywikibot
from pywikibot import config, i18n
from pywikibot import pagegenerators as pg
from pywikibot.backports import List, Set, Tuple
from pywikibot.bot import suggest_help
from pywikibot.exceptions import (
    EditConflictError,
    Error,
    IsRedirectPageError,
    LockedPageError,
    NoPageError,
    NotEmailableError,
    PageRelatedError,
    PageSaveRelatedError,
    ServerError,
    TranslationError,
)
from pywikibot.family import Family
from pywikibot.site import Namespace


###############################################################################
# <--------------------------- Change only below! --------------------------->#
###############################################################################

# NOTE: in the messages used by the bot if you put __botnick__ in the text, it
# will automatically replaced with the bot's nickname.

# That's what you want that will be added. (i.e. the {{no source}} with the
# right day/month/year )
N_TXT = {
    'commons': '{{subst:nld}}',
    'meta': '{{No license}}',
    'test': '{{No license}}',
    'ar': '{{subst:ملم}}',
    'arz': '{{subst:ملم}}',
    'de': '{{Dateiüberprüfung}}',
    'en': '{{subst:nld}}',
    'fa': '{{subst:حق تکثیر تصویر نامعلوم}}',
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
TXT_FIND = {
    'commons': ['{{no license', '{{no license/en',
                '{{nld', '{{no permission', '{{no permission since'],
    'meta': ['{{no license', '{{nolicense', '{{nld'],
    'test': ['{{no license'],
    'ar': ['{{لت', '{{لا ترخيص'],
    'arz': ['{{nld', '{{no license'],
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

# When the bot find that the usertalk is empty is not pretty to put only the
# no source without the welcome, isn't it?
EMPTY = {
    'commons': '{{subst:welcome}}\n~~~~\n',
    'meta': '{{subst:Welcome}}\n~~~~\n',
    'ar': '{{subst:أهلا ومرحبا}}\n~~~~\n',
    'arz': '{{subst:اهلا و سهلا}}\n~~~~\n',
    'de': '{{subst:willkommen}} ~~~~',
    'en': '{{subst:welcome}}\n~~~~\n',
    'fa': '{{subst:خوشامدید|%s}}',
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
DELETE_IMMEDIATELY = {
    'commons': '{{speedy|The file has .%s as extension. '
               'Is it ok? Please check.}}',
    'meta': '{{Delete|The file has .%s as extension.}}',
    'ar': '{{شطب|الملف له .%s كامتداد.}}',
    'arz': '{{مسح|الملف له .%s كامتداد.}}',
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
NOTHING_NOTIFICATION = {
    'commons': "\n{{subst:User:Filnik/untagged|File:%s}}\n\n''This message "
               "was '''added automatically by ~~~''', if you need "
               'some help about it, please read the text above again and '
               'follow the links in it, if you still need help ask at the '
               '[[File:Human-help-browser.svg|18px|link=Commons:Help desk|?]] '
               "'''[[Commons:Help desk|->]][[Commons:Help desk]]''' in any "
               "language you like to use.'' --~~~~",
    'meta': '{{subst:No license notice|File:%s}}',
    'ar': '{{subst:مصدر الملف|File:%s}} --~~~~',
    'arz': '{{subst:file source|File:%s}} --~~~~',
    'en': '{{subst:file source|File:%s}} --~~~~',
    'fa': '{{subst:اخطار نگاره|%s}}',
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
# NOTE: YOUR bot username will be automatically added.
BOT_LIST = {
    'commons': ['Siebot', 'CommonsDelinker', 'Filbot', 'Sz-iwbot',
                'ABFbot'],
    'meta': ['MABot'],
    'ar': ['MenoBot'],
    'arz': ['MenoBot'],
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
SECOND_MESSAGE_WITHOUT_LICENSE = {
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
PAGE_WITH_SETTINGS = {
    'commons': 'User:Filbot/Settings',
    'it': 'Progetto:Coordinamento/Immagini/Bot/Settings#Settings',
    'sr': 'User:KizuleBot/checkimages.py/подешавања',
    'zh': 'User:Alexbot/cisettings#Settings',
}

# The bot can report some images (like the images that have the same name of an
# image on commons) This is the page where the bot will store them.
REPORT_PAGE = {
    'commons': 'User:Filbot/Report',
    'meta': 'User:MABot/Report',
    'test': 'User:Pywikibot-test/Report',
    'ar': 'User:MenoBot/Report',
    'arz': 'User:MenoBot/Report',
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
HIDDEN_TEMPLATE = {
    # Put the other in the page on the project defined below
    'commons': ['Template:Information'],
    'meta': ['Template:Information'],
    'test': ['Template:Information'],
    'ar': ['Template:معلومات'],
    'arz': ['Template:معلومات'],
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
PAGE_WITH_HIDDEN_TEMPLATES = {
    'commons': 'User:Filbot/White_templates#White_templates',
    'it': 'Progetto:Coordinamento/Immagini/Bot/WhiteTemplates',
    'ko': 'User:Kwjbot_IV/whitetemplates/list',
    'sr': 'User:KizuleBot/checkimages.py/дозвољенишаблони',
}

# A page where there's a list of template to consider as licenses.
PAGE_WITH_ALOWED_TEMPLATES = {
    'commons': 'User:Filbot/Allowed templates',
    'de': 'Benutzer:Xqbot/Lizenzvorlagen',
    'it': 'Progetto:Coordinamento/Immagini/Bot/AllowedTemplates',
    'ko': 'User:Kwjbot_IV/AllowedTemplates',
    'sr': 'User:KizuleBot/checkimages.py/дозвољенишаблони',
}

# Template added when the bot finds only an hidden template and nothing else.
# Note: every __botnick__ will be repleaced with your bot's nickname
# (feel free not to use if you don't need it)
HIDDEN_TEMPALTE_NOTIFICATION = {
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
DUPLICATES_TEXT = {
    'commons': '\n{{Dupe|__image__}}',
    'de': '{{NowCommons}}',
    'it': '\n{{Progetto:Coordinamento/Immagini/Bot/Template duplicati|'
          '__images__}}',
    'ru': '{{NCT|__image__}}',
    'sr': '{{NowCommons|__image__}}',
}

# Message to put in the talk
DUPLICATES_USER_TALK_TEXT = {
    'it': '{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/Duplicati|'
          '%s|%s|~~~}} --~~~~',
}

# Regex to detect the template put in the image's description to find the dupe
DUPLICATES_REGEX = {
    'commons': r'\{\{(?:[Tt]emplate:|)(?:[Dd]up(?:licat|)e|[Bb]ad[ _][Nn]ame)'
               r'[|}]',
    'de': r'\{\{[nN](?:C|ow(?: c|[cC])ommons)[\|\}',
    'it': r'\{\{(?:[Tt]emplate:|)[Pp]rogetto:[Cc]oordinamento/Immagini/Bot/'
          r'Template duplicati[|}]',
    'sr': r'\{\{[nN](?:C|ow(?: c|[cC])ommons)[\|\}',
}

CATEGORIES_WITH_LICENSES = 'Q4481876', 'Q7451504'
"""Category items with the licenses; subcategories may contain other
licenses.

.. versionchanged:: 7.2
   uses wikibase items instead of category titles.
"""

# Page where is stored the message to send as email to the users
EMAIL_PAGE_WITH_TEXT = {
    # 'de': 'Benutzer:ABF/D3',
}

# Title of the email
EMAIL_SUBJECT = {
    # 'de': 'Problemen mit Deinem Bild auf der Deutschen Wikipedia',
}

# Seems that uploader bots aren't interested to get messages regarding the
# files that they upload.. strange, uh?
# Format: [[user,regex], [user,regex]...] the regex is needed to match the user
#         where to send the warning-msg
UPLOAD_BOTS = {
    'commons': [['File Upload Bot (Magnus Manske)',
                 r'\|[Ss]ource=Transferred from .*?; '
                 r'transferred to Commons by \[\[User:(.*?)\]\]']],
}

# Service images that don't have to be deleted and/or reported has a template
# inside them (you can let this param as None)
SERVICE_TEMPLATES = {
    'it': ['Template:Immagine di servizio'],
}

# Add your project (in alphabetical order) if you want that the bot starts
PROJECT_INSERTED = ['ar', 'arz', 'commons', 'de', 'en', 'fa', 'ga', 'hu', 'it',
                    'ja', 'ko', 'ru', 'meta', 'sd', 'sr', 'ta', 'test', 'ur',
                    'zh']

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

    """Log is full and the bot cannot add other data to prevent Errors."""


def print_with_time_zone(message) -> None:
    """Print the messages followed by the TimeZone encoded correctly."""
    time_zone = time.strftime('%d %b %Y %H:%M:%S (UTC)', time.gmtime())
    pywikibot.info(f'{message.rstrip()} {time_zone}')


class CheckImagesBot:

    """A robot to check recently uploaded files."""

    ignore_save_related_errors = True
    ignore_server_errors = False

    def __init__(
        self,
        site,
        log_full_number: int = 25000,
        sendemail_active: bool = False,
        duplicates_report: bool = False,
        log_full_error: bool = True,
        max_user_notify=None
    ) -> None:
        """Initializer, define some instance variables."""
        self.site = site
        self.log_full_error = log_full_error
        self.log_full_number = log_full_number
        self.rep_page = i18n.translate(self.site, REPORT_PAGE)
        if not self.rep_page:
            raise TranslationError(
                'No report page provided in "REPORT_PAGE" dict '
                'for your project!')
        self.image_namespace = site.namespaces.FILE.custom_name + ':'
        self.list_entry = f'\n* [[:{self.image_namespace}%s]] '

        # The summary of the report
        self.com = i18n.twtranslate(self.site, 'checkimages-log-comment')

        hiddentemplates_raw = i18n.translate(self.site, HIDDEN_TEMPLATE)
        if not hiddentemplates_raw:
            raise TranslationError(
                'No non-license templates provided in "HIDDEN_TEMPLATE" dict '
                'for your project!')
        self.hiddentemplates = {
            pywikibot.Page(self.site, tmp, ns=self.site.namespaces.TEMPLATE)
            for tmp in hiddentemplates_raw}
        self.page_hidden = i18n.translate(self.site,
                                          PAGE_WITH_HIDDEN_TEMPLATES)
        self.page_allowed = i18n.translate(self.site,
                                           PAGE_WITH_ALOWED_TEMPLATES)
        self.comment = i18n.twtranslate(self.site.lang,
                                        'checkimages-source-tag-comment')
        # Adding the bot's nickname at the notification text if needed.
        self.bots = i18n.translate(self.site, BOT_LIST)
        if self.bots:
            self.bots.append(site.username())
        else:
            self.bots = [site.username()]

        self.sendemail_active = sendemail_active
        self.skip_list = []
        self.duplicates_report = duplicates_report

        if max_user_notify:
            self.num_notify = collections.defaultdict(lambda: max_user_notify)
        else:
            self.num_notify = None

        # Load the licenses only once, so do it once
        self.licenses = self.load_licenses()

    def set_parameters(self, image) -> None:
        """Set parameters."""
        # ensure we have a FilePage
        self.image = pywikibot.FilePage(image)
        self.image_name = image.title(with_ns=False)
        self.timestamp = None
        self.uploader = None

    def report(
        self,
        newtext,
        image_to_report,
        notification=None,
        head=None,
        notification2=None,
        unver: bool = True,
        comm_talk=None,
        comm_image=None
    ) -> None:
        """Function to make the reports easier."""
        self.image_to_report = image_to_report
        self.newtext = newtext
        if not newtext:
            raise TranslationError(
                'No no-license template provided in "N_TXT" dict '
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
        self.comm_talk = comm_talk
        self.comm_image = comm_image or self.comment
        image_tagged = False
        try:
            image_tagged = self.tag_image(unver)
        except NoPageError:
            pywikibot.info('The page has been deleted! Skip!')
        except EditConflictError:
            pywikibot.info('Edit conflict! Skip!')
        if image_tagged and self.notification:
            try:
                self.put_mex_in_talk()
            except EditConflictError:
                pywikibot.info('Edit Conflict! Retrying...')
                try:
                    self.put_mex_in_talk()
                except Exception as e:
                    pywikibot.error(e)
                    pywikibot.info(
                        'Another error... skipping the user...')

    @staticmethod
    def upload_bot_change_function(report_page_text, upload_bot_array) -> str:
        """Detect the user that has uploaded the file through upload bot."""
        regex = upload_bot_array[1]
        result = re.search(regex, report_page_text)

        if result:
            return result.group()

        # we can't find the user, report the problem to the bot
        return upload_bot_array[0]

    def tag_image(self, put: bool = True) -> bool:
        """Add template to the Image page and find out the uploader."""
        # Get the image's description
        report_page_object = pywikibot.FilePage(self.site,
                                                self.image_to_report)

        try:
            report_page_text = report_page_object.get()
        except NoPageError:
            pywikibot.info(self.image_name + ' has been deleted...')
            return False

        # You can use this function also to find only the user that
        # has upload the image (FixME: Rewrite a bit this part)
        if put:
            pywikibot.showDiff(report_page_text,
                               self.newtext + '\n' + report_page_text)
            pywikibot.info(self.comm_image)
            try:
                report_page_object.put(self.newtext + '\n' + report_page_text,
                                       summary=self.comm_image)
            except LockedPageError:
                pywikibot.info('File is locked. Skipping.')
                return False

        # paginetta it's the image page object.
        try:
            if report_page_object == self.image and self.uploader:
                nick = self.uploader
            else:
                nick = report_page_object.latest_file_info.user
        except PageRelatedError:
            pywikibot.info(f'Seems that {self.image_to_report} has only the '
                           f'description and not the file...')
            repme = self.list_entry + "problems '''with the APIs'''"
            self.report_image(self.image_to_report, self.rep_page, self.com,
                              repme)
            return False

        upload_bots = i18n.translate(self.site, UPLOAD_BOTS)
        user = pywikibot.User(self.site, nick)
        luser = user.title(as_url=True)

        if upload_bots:
            for upload_bot in upload_bots:
                if upload_bot[0] == luser:
                    luser = self.upload_bot_change_function(report_page_text,
                                                            upload_bot)
                    user = pywikibot.User(self.site, luser)
        self.talk_page = user.getUserTalkPage()
        self.luser = luser
        return True

    def put_mex_in_talk(self) -> None:
        """Function to put the warning in talk page of the uploader."""
        commento2 = i18n.twtranslate(self.site.lang,
                                     'checkimages-source-notice-comment')
        email_page_name = i18n.translate(self.site, EMAIL_PAGE_WITH_TEXT)
        email_subj = i18n.translate(self.site, EMAIL_SUBJECT)
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
            pywikibot.info(
                'The latest user that has written something is: '
                + latest_user)
            # A block to prevent the second message if the bot also
            # welcomed users...
            if latest_user in self.bots and len(history) > 1:
                second_text = True
        except IsRedirectPageError:
            pywikibot.info(
                'The user talk is a redirect, trying to get the right talk...')
            try:
                self.talk_page = self.talk_page.getRedirectTarget()
                testoattuale = self.talk_page.get()
            except NoPageError:
                testoattuale = i18n.translate(self.site, EMPTY)
        except NoPageError:
            pywikibot.info('The user page is blank')
            testoattuale = i18n.translate(self.site, EMPTY)

        if self.comm_talk:
            commentox = self.comm_talk
        else:
            commentox = commento2

        if second_text:
            new_text = f'{testoattuale}\n\n{self.notification2}'
        else:
            new_text = '{}\n\n== {} ==\n{}'.format(testoattuale, self.head,
                                                   self.notification)

        # Check maximum number of notifications for this talk page
        if (self.num_notify is not None
                and self.num_notify[self.talk_page.title()] == 0):
            pywikibot.info('Maximum notifications reached, skip.')
            return

        try:
            self.talk_page.put(new_text, summary=commentox, minor=False)
        except PageSaveRelatedError as e:
            if not self.ignore_save_related_errors:
                raise
            err = e
        except ServerError as e:
            if not self.ignore_server_errors:
                raise
            err = e
        else:
            if self.num_notify is not None:
                self.num_notify[self.talk_page.title()] -= 1
            err = None
        if err:
            pywikibot.error(err)
            pywikibot.info(f'Skipping saving talk page {self.talk_page}')

        if email_page_name and email_subj:
            email_page = pywikibot.Page(self.site, email_page_name)
            try:
                email_text = email_page.get()
            except (NoPageError, IsRedirectPageError):
                return
            if self.sendemail_active:
                text_to_send = email_text.replace('__user-nickname__',
                                                  self.luser)
                email_class = pywikibot.User(self.site, self.luser)
                try:
                    email_class.send_email(email_subj, text_to_send)
                except NotEmailableError:
                    pywikibot.info('User is not mailable, aborted')

    def regex_generator(self, regexp, textrun) -> Generator[pywikibot.FilePage,
                                                            None, None]:
        """Find page to yield using regex to parse text."""
        regex = re.compile(fr'{regexp}', re.DOTALL)
        results = regex.findall(textrun)
        for image in results:
            yield pywikibot.FilePage(self.site, image)

    def load_hidden_templates(self) -> None:
        """Function to load the white templates."""
        # A template as {{en is not a license! Adding also them in the
        # whitelist template...
        for key in Family.load('wikipedia').langs.keys():
            self.hiddentemplates.add(pywikibot.Page(
                self.site, f'Template:{key}'))
        # Hidden template loading
        if self.page_hidden:
            try:
                page_hidden_text = pywikibot.Page(self.site,
                                                  self.page_hidden).get()
            except (NoPageError, IsRedirectPageError):
                page_hidden_text = ''

            for element in self.load(page_hidden_text):
                self.hiddentemplates.add(pywikibot.Page(self.site, element))

    @staticmethod
    def important_image(
        list_given: List[Tuple[float, pywikibot.FilePage]]
    ) -> pywikibot.FilePage:
        """
        Get tuples of image and time, return the most used or oldest image.

        .. versionchanged:: 7.2
           itertools.zip_longest is used to stop `using_pages` as soon as
           possible.

        :param list_given: a list of tuples which hold seconds and FilePage
        :return: the most used or oldest image
        """
        # find the most used image
        images = [image for _, image in list_given]
        iterables = [image.using_pages() for image in images]
        curr_images = []
        for values in zip_longest(*iterables, fillvalue=False):
            curr_images = values
            # bool(FilePage) is True because it is an object subclass
            if sum(bool(image) for image in values) <= 1:
                break

        for inx, image in enumerate(curr_images):
            if image is not False:
                return images[inx]

        # find the oldest image
        _, image = max(list_given, key=lambda element: element[0])
        return image

    def check_image_on_commons(self) -> bool:
        """Checking if the file is on commons."""
        pywikibot.info(f'Checking if [[{self.image_name}]] is on commons...')
        try:
            hash_found = self.image.latest_file_info.sha1
        except NoPageError:
            return False  # Image deleted, no hash found. Skip the image.

        site = pywikibot.Site('commons')
        commons_image_with_this_hash = next(
            site.allimages(sha1=hash_found, total=1), None)
        if commons_image_with_this_hash:
            service_template = pywikibot.translate(self.site,
                                                   SERVICE_TEMPLATES)
            templates_in_the_image = self.image.templates()
            if service_template is not None:
                for template in service_template:
                    if pywikibot.Page(self.site,
                                      template) in templates_in_the_image:
                        pywikibot.info(f'{self.image_name} is on commons but '
                                       f"it's a service image.")
                        return True  # continue with the check-part

            pywikibot.info(self.image_name + ' is on commons!')
            if self.image.file_is_shared():
                pywikibot.info(
                    "But, the file doesn't exist on your project! Skip...")
                # We have to skip the check part for that image because
                # it's on commons but someone has added something on your
                # project.
                return False

            if re.findall(r'\bstemma\b',
                          self.image_name.lower()) and self.site.code == 'it':
                pywikibot.info(f"{self.image_name} has 'stemma' inside, means "
                               f"that it's ok.")
                return True

            # It's not only on commons but the image needs a check
            # the second usually is a url or something like that.
            # Compare the two in equal way, both url.
            repme = ((self.list_entry
                      + "is also on '''Commons''': [[commons:File:%s]]")
                     % (self.image_name,
                        commons_image_with_this_hash.title(with_ns=False)))
            if (self.image.title(as_url=True)
                    == commons_image_with_this_hash.title(as_url=True)):
                repme += ' (same name)'
            self.report_image(self.image_name, self.rep_page, self.com, repme,
                              addings=False)
        return True

    def check_image_duplicated(self, duplicates_rollback) -> bool:
        """Function to check the duplicated files."""
        dup_text = i18n.translate(self.site, DUPLICATES_TEXT)
        dup_regex = i18n.translate(self.site, DUPLICATES_REGEX)
        dup_talk_text = i18n.translate(self.site, DUPLICATES_USER_TALK_TEXT)

        # Head of the message given to the author
        dup_talk_head = i18n.twtranslate(
            self.site, 'checkimages-doubles-head')
        # Comment while bot reports the problem in the uploader's talk
        dup_comment_talk = i18n.twtranslate(
            self.site, 'checkimages-doubles-talk-comment')
        # Comment used by the bot while it reports the problem in the image
        dup_comment_image = i18n.twtranslate(
            self.site, 'checkimages-doubles-file-comment')

        image_page = pywikibot.FilePage(self.site, self.image_name)
        hash_found = image_page.latest_file_info.sha1
        duplicates = list(self.site.allimages(sha1=hash_found))

        # If empty, image is deleted, no hash found. Skip the image.
        # Otherwise ok, let's continue the checking phase
        if len(duplicates) <= 1:
            return bool(duplicates)

        xdict = {'en':
                 '%(name)s has {{PLURAL:count'
                 '|a duplicate! Reporting it'
                 '|%(count)s duplicates! Reporting them}}...'}
        pywikibot.info(i18n.translate('en', xdict,
                                      {'name': self.image_name,
                                       'count': len(duplicates) - 1}))
        if dup_text and dup_regex:
            time_image_list = []

            for dup_page in duplicates:
                if dup_page.title(as_url=True) != self.image.title(
                        as_url=True) or self.timestamp is None:
                    try:
                        self.timestamp = (dup_page.latest_file_info.timestamp)
                    except PageRelatedError:
                        continue
                data = self.timestamp.timetuple()
                data_seconds = time.mktime(data)
                time_image_list.append([data_seconds, dup_page])
            older_image_page = self.important_image(time_image_list)
            older_page_text = older_image_page.text
            # And if the images are more than two?
            string = ''
            images_to_tag_list = []

            for dup_page in duplicates:
                if dup_page == older_image_page:
                    # the most used or oldest image
                    # not report also this as duplicate
                    continue
                try:
                    dup_page_text = dup_page.text
                except NoPageError:
                    continue

                if not (re.findall(dup_regex, dup_page_text)
                        or re.findall(dup_regex, older_page_text)):
                    pywikibot.info(
                        f'{dup_page} is a duplicate and has to be tagged...')
                    images_to_tag_list.append(dup_page.title())
                    string += '* {}\n'.format(dup_page.title(as_link=True,
                                                             textlink=True))
                else:
                    pywikibot.info(
                        "Already put the dupe-template in the files's page"
                        " or in the dupe's page. Skip.")
                    return False  # Ok - Let's continue the checking phase

            # true if the image are not to be tagged as dupes
            only_report = False

            # put only one image or the whole list according to the request
            if '__images__' in dup_text:
                text_for_the_report = dup_text.replace(
                    '__images__',
                    '\n{}* {}\n'.format(string,
                                        older_image_page.title(as_link=True,
                                                               textlink=True)))
            else:
                text_for_the_report = dup_text.replace(
                    '__image__',
                    older_image_page.title(as_link=True, textlink=True))

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
                        fr'\n\*\[\[:{re.escape(image)}\]\]',
                        '', text_for_the_report)
                    self.report(text_for_the_report, image_to_tag,
                                comm_image=dup_comment_image, unver=True)

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
                if already_reported_in_past > duplicates_rollback - 1 \
                   or not dup_talk_text:
                    only_report = True
                else:
                    self.report(
                        text_for_the_report, images_to_tag_list[-1],
                        dup_talk_text % (older_image_page.title(with_ns=True),
                                         string),
                        dup_talk_head, comm_talk=dup_comment_talk,
                        comm_image=dup_comment_image, unver=True)

        if self.duplicates_report or only_report:
            if only_report:
                repme = ((self.list_entry + 'has the following duplicates '
                          "('''forced mode'''):")
                         % self.image.title(as_url=True))
            else:
                repme = ((self.list_entry + 'has the following duplicates:')
                         % self.image.title(as_url=True))

            for dup_page in duplicates:
                if dup_page.title(as_url=True) \
                   == self.image.title(as_url=True):
                    # the image itself, not report also this as duplicate
                    continue
                repme += '\n** [[:{}{}]]'.format(self.image_namespace,
                                                 dup_page.title(as_url=True))

            result = self.report_image(self.image_name, self.rep_page,
                                       self.com, repme, addings=False)
            if not result:
                return True  # If Errors, exit (but continue the check)

        if older_image_page.title() != self.image_name:
            # The image is a duplicate, it will be deleted. So skip the
            # check-part, useless
            return False
        return True  # Ok - No problem. Let's continue the checking phase

    def report_image(self, image_to_report, rep_page=None, com=None,
                     rep_text=None, addings: bool = True) -> bool:
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
            pywikibot.info(f'{image_to_report} is already in the report page.')
            reported = False
        elif len(text_get) >= self.log_full_number:
            if self.log_full_error:
                raise LogIsFull(
                    'The log page ({}) is full! Please delete the old files '
                    'reported.'.format(another_page.title()))

            pywikibot.info(
                'The log page ({}) is full! Please delete the old files '
                ' reported. Skip!'.format(another_page.title()))
            # Don't report, but continue with the check
            # (we don't know if this is the first time we check this file
            # or not)
        else:
            # Adding the log
            another_page.put(text_get + rep_text, summary=com, force=True,
                             minor=False)
            pywikibot.info('...Reported...')
        return reported

    def takesettings(self) -> None:
        """Function to take the settings from the wiki."""
        settings_page = i18n.translate(self.site, PAGE_WITH_SETTINGS)
        try:
            if not settings_page:
                self.settings_data = None
            else:
                page = pywikibot.Page(self.site, settings_page)
                self.settings_data = []
                try:
                    testo = page.get()

                    for number, m in enumerate(SETTINGS_REGEX.finditer(testo),
                                               start=1):
                        name = str(m[1])
                        find_tipe = str(m[2])
                        find = str(m[3])
                        imagechanges = str(m[4])
                        summary = str(m[5])
                        head = str(m[6])
                        text = str(m[7])
                        mexcatched = str(m[8])
                        tupla = [number, name, find_tipe, find, imagechanges,
                                 summary, head, text, mexcatched]
                        self.settings_data += [tupla]

                    if not self.settings_data:
                        pywikibot.info(
                            "You've set wrongly your settings, please take a "
                            'look to the relative page. (run without them)')
                        self.settings_data = None
                except NoPageError:
                    pywikibot.info("The settings' page doesn't exist!")
                    self.settings_data = None
        except Error:
            pywikibot.info(
                'Problems with loading the settigs, run without them.')
            self.settings_data = None
            self.some_problem = False

        if not self.settings_data:
            self.settings_data = None

        # Real-Time page loaded
        if self.settings_data:
            pywikibot.info('>> Loaded the real-time page... <<')
        else:
            pywikibot.info('>> No additional settings found! <<')

    def load_licenses(self) -> Set[pywikibot.Page]:
        """Load the list of the licenses.

        .. versionchanged:: 7.2
           return a set instead of a list for quicker lookup.
        """
        pywikibot.info('\nLoading the allowed licenses...\n')
        licenses = set()
        for item in CATEGORIES_WITH_LICENSES:
            cat = self.site.page_from_repository(item)
            if cat:
                licenses.update(cat.articles())

        if self.site.code == 'commons':
            no_licenses_to_skip = pywikibot.Category(self.site,
                                                     'License-related tags')
            for license_given in no_licenses_to_skip.articles():
                if license_given in licenses:
                    licenses.remove(license_given)

        # Add the licenses set in the default page as licenses to check
        if self.page_allowed:
            try:
                page_allowed_text = pywikibot.Page(self.site,
                                                   self.page_allowed).get()
            except (NoPageError, IsRedirectPageError):
                pass
            else:
                for name_license in self.load(page_allowed_text):
                    licenses.add(pywikibot.Page(self.site, name_license))

        if not licenses:
            raise pywikibot.Error(
                'No allowed licenses categories provided. Add that category '
                'to wikibase to make the script work correctly')

        return licenses

    def mini_template_check(self, template) -> bool:
        """Check if template is in allowed licenses or in licenses to skip."""
        # the list_licenses are loaded in the __init__
        # (not to load them multimple times)
        if template in self.licenses:
            self.license_selected = template.title(with_ns=False)
            self.seems_ok = True
            # let the last "fake" license normally detected
            self.license_found = self.license_selected
            return True

        if template in self.hiddentemplates:
            # if the whitetemplate is not in the images description, we don't
            # care
            try:
                self.all_licenses.remove(template)
            except ValueError:
                return False
            else:
                self.white_templates_found = True
        return False

    def template_in_list(self) -> None:
        """
        Check if template is in list.

        The problem is the calls to the Mediawiki system because they can be
        pretty slow. While searching in a list of objects is really fast, so
        first of all let's see if we can find something in the info that we
        already have, then make a deeper check.
        """
        for template in self.licenses_found:
            if self.mini_template_check(template):
                break
        if not self.license_found:
            for template in self.licenses_found:
                if template.isRedirectPage():
                    template = template.getRedirectTarget()
                    if self.mini_template_check(template):
                        break

    def smart_detection(self) -> Tuple[str, bool]:
        """
        Detect templates.

        The bot instead of checking if there's a simple template in the
        image's description, checks also if that template is a license or
        something else. In this sense this type of check is smart.
        """
        self.seems_ok = False
        self.license_found = None
        self.white_templates_found = False
        regex_find_licenses = re.compile(
            r'(?<!\{)\{\{(?:[Tt]emplate:|)([^{]+?)[|\n<}]', re.DOTALL)
        regex_are_licenses = re.compile(
            r'(?<!\{)\{\{(?:[Tt]emplate:|)([^{]+?)\}\}', re.DOTALL)
        while True:
            self.load_hidden_templates()
            self.licenses_found = self.image.templates()
            templates_in_the_image_raw = regex_find_licenses.findall(
                self.image_check_text)

            if not self.licenses_found and templates_in_the_image_raw:
                # {{nameTemplate|something <- this is not a template, be sure
                # that we haven't catch something like that.
                licenses_test = regex_are_licenses.findall(
                    self.image_check_text)
                if not self.licenses_found and licenses_test:
                    raise Error(
                        f"Invalid or broken templates found in the image's "
                        f'page {self.image}!')
            self.all_licenses = []

            # Found the templates ONLY in the image's description
            for template_selected in templates_in_the_image_raw:
                tp = pywikibot.Page(self.site, template_selected)
                page_title = tp.title(as_url=True, with_ns=False).lower()
                for template_real in self.licenses_found:
                    template_title = template_real.title(as_url=True,
                                                         with_ns=False).lower()
                    if page_title == template_title \
                       and template_real not in self.all_licenses:
                        self.all_licenses.append(template_real)
            break

        if self.licenses_found:
            self.template_in_list()

            if not self.license_found and self.all_licenses:
                self.all_licenses = [
                    template.getRedirectTarget()
                    if template.isRedirectPage() else template
                    for template in self.all_licenses if template.exists()]

                if self.all_licenses:
                    self.license_found = self.all_licenses[0].title()

        # If it has "some_problem" it must check the additional settings.
        self.some_problem = False

        if self.settings_data:
            # use additional settings
            self.find_additional_problems()

        if self.some_problem:
            if self.mex_used in self.image_check_text:
                pywikibot.info('File already fixed. Skipping.')
            else:
                pywikibot.info(f"The file's description for {self.image_name} "
                               f'contains {self.name_used}...')
                if self.mex_used.lower() == 'default':
                    self.mex_used = self.unvertext
                if self.imagestatus_used:
                    reported = True
                else:
                    reported = self.report_image(self.image_name)
                if reported:
                    self.report(self.mex_used, self.image_name, self.text_used,
                                self.head_used, None,
                                self.imagestatus_used, self.summary_used)
                else:
                    pywikibot.info('Skipping the file...')
                self.some_problem = False
        else:
            if not self.seems_ok and self.license_found:
                rep_text_license_fake = ((self.list_entry
                                          + "seems to have a ''fake license'',"
                                          ' license detected:'
                                          ' <nowiki>%s</nowiki>') %
                                         (self.image_name, self.license_found))
                print_with_time_zone(
                    f'{self.image_name} seems to have a fake license: '
                    f'{self.license_found}, reporting...')
                self.report_image(self.image_name,
                                  rep_text=rep_text_license_fake,
                                  addings=False)
            elif self.license_found:
                pywikibot.info(f'[[{self.image_name}]] seems ok, license '
                               f'found: {{{{{self.license_found}}}}}...')
        return (self.license_found, self.white_templates_found)

    @staticmethod
    def load(raw) -> List[str]:
        """Load a list of objects from a string using regex."""
        list_loaded = []
        # I search with a regex how many user have not the talk page
        # and i put them in a list (i find it more easy and secure)
        regl = r"(\"|\')(.*?)\1(?:,|\])"
        pl = re.compile(regl)
        for xl in pl.finditer(raw):
            word = xl[2].replace('\\\\', '\\')
            if word not in list_loaded:
                list_loaded.append(word)
        return list_loaded

    def skip_images(self, skip_number, limit) -> bool:
        """Given a number of files, skip the first -number- files."""
        # If the images to skip are more the images to check, make them the
        # same number
        if skip_number == 0:
            pywikibot.info('\t\t>> No files to skip...<<')
            return False

        skip_number = min(skip_number, limit)
        # Print a starting message only if no images has been skipped
        if not self.skip_list:
            pywikibot.info(
                i18n.translate(
                    'en',
                    'Skipping the first {{PLURAL:num|file|%(num)s files}}:\n',
                    {'num': skip_number}))
        # If we still have pages to skip:
        if len(self.skip_list) < skip_number:
            pywikibot.info(f'Skipping {self.image_name}...')
            self.skip_list.append(self.image_name)
            if skip_number == 1:
                pywikibot.info()
            return True
        pywikibot.info()
        return False

    @staticmethod
    def wait(generator, wait_time) -> Generator[pywikibot.FilePage, None,
                                                None]:
        """
        Skip the images uploaded before x seconds.

        Let the users to fix the image's problem alone in the first x seconds.
        """
        print_with_time_zone(
            f'Skipping the files uploaded less than {wait_time} seconds ago..')
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

    def is_tagged(self) -> bool:
        """Understand if a file is already tagged or not."""
        # TODO: enhance and use textlib.MultiTemplateMatchBuilder
        # Is the image already tagged? If yes, no need to double-check, skip
        no_license = i18n.translate(self.site, TXT_FIND)
        if not no_license:
            raise TranslationError(
                'No no-license templates provided in "TXT_FIND" dict '
                'for your project!')
        for i in no_license:
            # If there are {{ use regex, otherwise no (if there's not the
            # {{ may not be a template and the regex will be wrong)
            if '{{' in i:
                regex_pattern = re.compile(
                    r'\{\{(?:template)?%s ?(?:\||\r?\n|\}|<|/) ?'
                    % i.split('{{')[1].replace(' ', '[ _]'), re.I)
                result = regex_pattern.findall(self.image_check_text)
                if result:
                    return True
            elif i.lower() in self.image_check_text:
                return True
        return False

    def find_additional_problems(self) -> None:
        """Extract additional settings from configuration page."""
        # In every tuple there's a setting configuration
        for tupla in self.settings_data:
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
                self.settings_data = None
                break
            summary = tupla[5]
            head_2 = tupla[6]
            if head_2.count('==') == 2:
                head_2 = re.findall(r'\s*== *(.+?) *==\s*', head_2)[0]
            text = tupla[7] % self.image_name
            mex_catched = tupla[8]
            for k in find_list:
                if find_tipe.lower() == 'findonly':
                    search_results = re.findall(fr'{k.lower()}',
                                                self.image_check_text.lower())
                    if search_results \
                       and search_results[0] == self.image_check_text.lower():
                        self.some_problem = True
                        self.text_used = text
                        self.head_used = head_2
                        self.imagestatus_used = imagestatus
                        self.name_used = name
                        self.summary_used = summary
                        self.mex_used = mex_catched
                        break
                elif find_tipe.lower() == 'find' \
                    and re.findall(fr'{k.lower()}',
                                   self.image_check_text.lower()):
                    self.some_problem = True
                    self.text_used = text
                    self.head_used = head_2
                    self.imagestatus_used = imagestatus
                    self.name_used = name
                    self.summary_used = summary
                    self.mex_used = mex_catched
                    continue

    def check_step(self) -> None:
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
        extension = self.image_name.split('.')[-1]
        # Load the notification messages
        hidden_template_notification = i18n.translate(
            self.site, HIDDEN_TEMPALTE_NOTIFICATION)
        self.unvertext = i18n.translate(self.site, N_TXT)
        di = i18n.translate(self.site, DELETE_IMMEDIATELY)

        # The header of the Unknown extension's message.
        dih = i18n.twtranslate(self.site, 'checkimages-unknown-extension-head')
        # Text that will be add if the bot find a unknown extension.
        din = i18n.twtranslate(self.site,
                               'checkimages-unknown-extension-msg') + ' ~~~~'
        # Header that the bot will add if the image hasn't the license.
        nh = i18n.twtranslate(self.site, 'checkimages-no-license-head')
        # Summary of the delete immediately.
        dels = i18n.twtranslate(self.site, 'checkimages-deletion-comment')

        nn = i18n.translate(self.site, NOTHING_NOTIFICATION)
        smwl = i18n.translate(self.site, SECOND_MESSAGE_WITHOUT_LICENSE)

        try:
            self.image_check_text = self.image.get()
        except NoPageError:
            pywikibot.info(
                f'Skipping {self.image_name} because it has been deleted.')
            return

        except IsRedirectPageError:
            pywikibot.info(
                f"Skipping {self.image_name} because it's a redirect.")
            return

        # Delete the fields where the templates cannot be loaded
        regex_nowiki = re.compile(r'<nowiki>(.*?)</nowiki>', re.DOTALL)
        regex_pre = re.compile(r'<pre>(.*?)</pre>', re.DOTALL)
        self.image_check_text = regex_nowiki.sub('', self.image_check_text)
        self.image_check_text = regex_pre.sub('', self.image_check_text)

        # Deleting the useless template from the description (before adding
        # sth in the image the original text will be reloaded, don't worry).
        if self.is_tagged():
            print_with_time_zone(f'{self.image_name} is already tagged.')
            return

        # something is the array with {{, MIT License and so on.
        for a_word in something:
            if a_word in self.image_check_text:
                # There's a template, probably a license
                brackets = True

        # Is the extension allowed? (is it an image or f.e. a .xls file?)
        if allowed_formats and extension.lower() not in allowed_formats:
            delete = True

        (license_found, hidden_template_found) = self.smart_detection()

        # Here begins the check block.
        if brackets and license_found:
            return

        if delete:
            pywikibot.info(f'{self.image_name} is not a file!')
            if not di:
                pywikibot.info('No localized message given for '
                               "'DELETE_IMMEDIATELY'. Skipping.")
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
            self.report(canctext, self.image_name, notification, head)
            return

        if not self.image_check_text.strip():  # empty image description
            pywikibot.info(f"The file's description for {self.image_name} "
                           f'does not contain a license  template!')
            if hidden_template_found and hidden_template_notification:
                notification = hidden_template_notification % self.image_name
            elif nn:
                notification = nn % self.image_name
            head = nh
            self.report(self.unvertext, self.image_name, notification, head,
                        smwl)
            return

        pywikibot.info(f'{self.image_name} has only text and not the specific '
                       f'license...')
        if hidden_template_found and hidden_template_notification:
            notification = hidden_template_notification % self.image_name
        elif nn:
            notification = nn % self.image_name
        head = nh
        self.report(self.unvertext, self.image_name, notification, head, smwl)


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
    wait_time = 0  # How many time sleep before the check?
    commons_active = False  # Is there an image with the same name at commons?
    normal = False  # Check the new images or use another generator?
    url_used = False  # Use the url-related function instead of the new-pages
    regex_gen = False  # Use the regex generator
    duplicates_active = False  # Use the duplicate option
    duplicates_report = False  # Use the duplicate-report option
    max_user_notify = None
    sendemail_active = False  # Use the send-email
    log_full_error = True  # Raise an error when the log is full
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
            log_full_error = False
        elif option == '-commons':
            commons_active = True
        elif option == '-duplicatesreport':
            duplicates_report = True
        elif option == '-duplicates':
            duplicates_active = True
            duplicates_rollback = int(value or 1)
        elif option == '-maxusernotify':
            max_user_notify = int(value or pywikibot.input(
                'What should be the maximum number of notifications per user '
                'per check?'))
        elif option == '-sendemail':
            sendemail_active = True
        elif option == '-skip':
            skip_number = int(value or pywikibot.input(
                'How many files do you want to skip?'))
        elif option == '-wait':
            wait_time = int(value or pywikibot.input(
                'How many time do you want to wait before checking the '
                'files?'))
        elif option == '-start':
            first_page_title = value or pywikibot.input(
                'From which page do you want to start?')
            namespaces = tuple(
                ns + ':' for ns in site.namespace(Namespace.FILE, True))
            if first_page_title.startswith(namespaces):
                first_page_title = first_page_title.split(':', 1)[1]
            generator = site.allimages(start=first_page_title)
            repeat = False
        elif option == '-page':
            regex_page_name = value or pywikibot.input(
                'Which page do you want to use for the regex?')
            repeat = False
            regex_gen = True
        elif option == '-url':
            regex_page_url = value or pywikibot.input(
                'Which url do you want to use for the regex?')
            url_used = True
            repeat = False
            regex_gen = True
        elif option == '-regex':
            regexp_to_use = value or pywikibot.input(
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
    if site.code not in PROJECT_INSERTED:
        additional_text = ('Your project is not supported by this script.\n'
                           'To allow your project in the script you have to '
                           'add a localization into the script and add your '
                           'project to the "PROJECT_INSERTED" list!')
    else:
        additional_text = ''
    if suggest_help(unknown_parameters=unknown,
                    additional_text=additional_text):
        return False

    # Reading the log of the new images if another generator is not given.
    if normal:
        if limit == 1:
            pywikibot.info('Retrieving the latest file for checking...')
        else:
            pywikibot.info(
                f'Retrieving the latest {limit} files for checking...')
    while True:
        # Defing the Main Class.
        bot = CheckImagesBot(site, sendemail_active=sendemail_active,
                             duplicates_report=duplicates_report,
                             log_full_error=log_full_error,
                             max_user_notify=max_user_notify)
        if normal:
            generator = pg.NewimagesPageGenerator(total=limit, site=site)
        # if url_used and regex_gen, get the source for the generator
        if url_used and regex_gen:
            text_regex = site.getUrl(regex_page_url, no_hostname=True)
        # Not an url but a wiki page as "source" for the regex
        elif regex_gen:
            page = pywikibot.Page(site, regex_page_name)
            try:
                text_regex = page.get()
            except NoPageError:
                pywikibot.info(f"{page.title()} doesn't exist!")
                text_regex = ''  # No source, so the bot will quit later.
        # If generator is the regex' one, use your own Generator using an url
        # or page and a regex.
        if generator == 'regex' and regex_gen:
            generator = bot.regex_generator(regexp_to_use, text_regex)

        bot.takesettings()
        if wait_time > 0:
            generator = bot.wait(generator, wait_time)
        for image in generator:
            # Setting the image for the main class
            bot.set_parameters(image)

            if skip_number and bot.skip_images(skip_number, limit):
                continue

            # Check on commons if there's already an image with the same name
            if commons_active and site.family.name != 'commons' \
               and not bot.check_image_on_commons():
                continue

            # Check if there are duplicates of the image on the project
            if duplicates_active \
               and not bot.check_image_duplicated(duplicates_rollback):
                continue

            bot.check_step()

        if repeat:
            pywikibot.info(f'Waiting for {time_sleep} seconds,')
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
            pywikibot.info(f'Execution time: {delta} seconds\n')
