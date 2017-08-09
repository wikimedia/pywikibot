#!/usr/bin/python
# -*- coding: utf-8 -*-
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

-start[:#]          Use allpages() as generator
                    (it starts already from File:[:#])

-cat[:#]            Use a category as generator

-regex[:#]          Use regex, must be used with -url or -page

-page[:#]           Define the name of the wikipage where are the images

-url[:#]            Define the url where are the images

-nologerror         If given, this option will disable the error that is risen
                    when the log is full.

---- Instructions for the real-time settings ----
* For every new block you have to add:

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

---- Known issues/FIXMEs: ----
* Clean the code, some passages are pretty difficult to understand.
* Add the "catch the language" function for commons.
* Fix and reorganise the new documentation
* Add a report for the image tagged.

"""
#
# (C) Kyle/Orgullomoore, 2006-2007 (newimage.py)
# (C) Siebrand Mazeland, 2007-2010
# (C) Filnik, 2007-2011
# (C) Pywikibot team, 2007-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import collections
import re
import time

import pywikibot

from pywikibot import i18n
from pywikibot import pagegenerators as pg

from pywikibot.exceptions import ArgumentDeprecationWarning, NotEmailableError
from pywikibot.family import Family
from pywikibot.tools import issue_deprecation_warning

###############################################################################
# <--------------------------- Change only below! --------------------------->#
###############################################################################

# NOTE: in the messages used by the Bot if you put __botnick__ in the text, it
# will automatically replaced with the bot's nickname.

# That's what you want that will be added. (i.e. the {{no source}} with the
# right day/month/year )
n_txt = {
    'commons': u'{{subst:nld}}',
    'meta': '{{No license}}',
    'ar': u'{{subst:لم}}',
    'de': u'{{Dateiüberprüfung}}',
    'en': u'{{subst:nld}}',
    'fa': u'{{جا:حق تکثیر تصویر نامعلوم}}',
    'fr': u'{{subst:lid}}',
    'ga': u'{{subst:Ceadúnas de dhíth}}',
    'hu': u'{{nincslicenc|~~~~~}}',
    'it': u'{{subst:unverdata}}',
    'ja': u'{{subst:Nld}}',
    'ko': u'{{subst:nld}}',
    'ta': u'{{subst:nld}}',
    'ur': u'{{subst:حقوق نسخہ تصویر نامعلوم}}',
    'zh': u'{{subst:No license/auto}}',
}

# Text that the bot will try to see if there's already or not. If there's a
# {{ I'll use a regex to make a better check.
# This will work so:
# '{{no license' --> '\{\{(?:template:)?no[ _]license ?(?:\||\n|\}|/) ?' (case
# insensitive).
# If there's not a {{ it will work as usual (if x in Text)
txt_find = {
    'commons': [u'{{no license', u'{{no license/en',
                u'{{nld', u'{{no permission', u'{{no permission since'],
    'meta': ['{{no license', '{{nolicense', '{{nld'],
    'ar': [u'{{لت', u'{{لا ترخيص'],
    'de': [u'{{DÜP', u'{{Düp', u'{{Dateiüberprüfung'],
    'en': [u'{{nld', u'{{no license'],
    'fa': [u'{{حق تکثیر تصویر نامعلوم۲'],
    'ga': [u'{{Ceadúnas de dhíth', u'{{Ceadúnas de dhíth'],
    'hu': [u'{{nincsforrás', u'{{nincslicenc'],
    'it': [u'{{unverdata', u'{{unverified'],
    'ja': [u'{{no source', u'{{unknown',
           u'{{non free', u'<!--削除についての議論が終了するまで'],
    'ta': [u'{{no source', u'{{nld', u'{{no license'],
    'ko': [u'{{출처 없음', u'{{라이선스 없음', u'{{Unknown'],
    'ur': [u'{{ناحوالہ', u'{{اجازہ نامعلوم', u'{{Di-no'],
    'zh': [u'{{no source', u'{{unknown', u'{{No license'],
}

# When the Bot find that the usertalk is empty is not pretty to put only the
# no source without the welcome, isn't it?
empty = {
    'commons': u'{{subst:welcome}}\n~~~~\n',
    'meta': '{{subst:Welcome}}\n~~~~\n',
    'ar': u'{{ترحيب}}\n~~~~\n',
    'de': u'{{subst:willkommen}} ~~~~',
    'en': u'{{welcome}}\n~~~~\n',
    'fa': u'{{جا:خوشامدید|%s}}',
    'fr': u'{{Bienvenue nouveau\n~~~~\n',
    'ga': u'{{subst:Fáilte}} - ~~~~\n',
    'hu': u'{{subst:Üdvözlet|~~~~}}\n',
    'it': '<!-- inizio template di benvenuto -->\n{{subst:Benvebot}}\n~~~~\n'
          '<!-- fine template di benvenuto -->',
    'ja': u'{{subst:Welcome/intro}}\n{{subst:welcome|--~~~~}}\n',
    'ko': u'{{환영}}--~~~~\n',
    'ta': u'{{welcome}}\n~~~~\n',
    'ur': u'{{خوش آمدید}}\n~~~~\n',
    'zh': u'{{subst:welcome|sign=~~~~}}',
}

# if the file has an unknown extension it will be tagged with this template.
# In reality, there aren't unknown extension, they are only not allowed...
delete_immediately = {
    'commons': u"{{speedy|The file has .%s as extension. Is it ok? Please check.}}",
    'meta': '{{Delete|The file has .%s as extension.}}',
    'ar': u"{{شطب|الملف له .%s كامتداد.}}",
    'en': u"{{db-meta|The file has .%s as extension.}}",
    'fa': u"{{حذف سریع|تصویر %s اضافی است.}}",
    'ga': u"{{scrios|Tá iarmhír .%s ar an comhad seo.}}",
    'hu': u'{{azonnali|A fájlnak .%s a kiterjesztése}}',
    'it': u'{{cancella subito|motivo=Il file ha come estensione ".%s"}}',
    'ja': u'{{db|知らないファイルフォーマット %s}}',
    'ko': u'{{delete|잘못된 파일 형식 (.%s)}}',
    'ta': u'{{delete|இந்தக் கோப்பு .%s என்றக் கோப்பு நீட்சியைக் கொண்டுள்ளது.}}',
    'ur': u"{{سریع حذف شدگی|اس ملف میں .%s بطور توسیع موجود ہے۔ }}",
    'zh': u'{{delete|未知檔案格式%s}}',
}

# The header of the Unknown extension's message.
delete_immediately_head = {
    'ar': 'امتداد غير معروف!',
    'en': 'Unknown extension!',
    'fa': 'بارگذاری تصاویر موجود در انبار',
    'ga': 'Iarmhír neamhaithnid!',
    'fr': 'Extension inconnue',
    'hu': 'Ismeretlen kiterjesztésű fájl',
    'it': 'File non specificato',
    'ko': '잘못된 파일 형식',
    'ta': 'இனங்காணப்படாத கோப்பு நீட்சி!',
    'ur': 'نامعلوم توسیع!',
    'zh': '您上載的檔案格式可能有誤',
}

# Text that will be add if the bot find a unknown extension.
delete_immediately_notification = {
    'ar': 'الملف %(file)s يبدو أن امتداده خاطيء, من فضلك تحقق.',
    'en': 'The %(file)s file seems to have a wrong extension, please check.',
    'fa': 'به نظر می‌آید تصویر %(file)s مسیر نادرستی داشته باشد لطفا بررسی کنید.',
    'ga': "Tá iarmhír mícheart ar an comhad %(file)s, scrúdaigh le d'thoil.",
    'fr': 'Le fichier %(file)s semble avoir une mauvaise extension, veuillez vérifier.',
    'hu': 'A %(file)s fájlnak rossz a kiterjesztése, kérlek ellenőrízd.',
    'it': ('A quanto ci risulta, %(file)s sembra non essere un file utile '
           "all'enciclopedia. Se così non fosse, e' consigliato che tu scriva "
           "al mio programmatore. Grazie per l'attenzione. "
           '<u>Questo è un messaggio automatico di</u>'),
    'ko': '%(file)s의 파일 형식이 잘못되었습니다. 확인 바랍니다.',
    'ta': '%(file)s இனங்காணப்படாத கோப்பு நீட்சியை கொண்டுள்ளது தயவு செய்து ஒ'
          'ரு முறை சரி பார்க்கவும்',
    'ur': 'ملف %(file)s کی توسیع شاید درست نہیں ہے، براہ کرم جانچ لیں۔',
    'zh': '您好，你上傳的%(file)s無法被識別，請檢查您的檔案，謝謝。',
}

# Summary of the delete immediately.
# (e.g: Adding {{db-meta|The file has .%s as extension.}})
msg_del_comm = {
    'ar': 'بوت: إضافة %(adding)s',
    'en': 'Bot: Adding %(adding)s',
    'fa': 'ربات: اضافه کردن %(adding)s',
    'ga': 'Róbó: Cuir %(adding)s leis',
    'fr': 'Robot : Ajouté %(adding)s',
    'hu': 'Robot:"%(adding)s" hozzáadása',
    'it': 'Bot: Aggiungo %(adding)s',
    'ja': 'ロボットによる: 追加 %(adding)s',
    'ko': '로봇 : %(adding)s 추가',
    'ta': 'Bot: Adding %(adding)s',
    'ur': 'روبالہ: اضافہ %(adding)s',
    'zh': '機器人: 正在新增 %(adding)s',
}

# This is the most important header, because it will be used a lot. That's the
# header that the bot will add if the image hasn't the license.
nothing_head = {
    'ar': 'صورة بدون ترخيص',
    'de': 'Bild ohne Lizenz',
    'en': 'Image without license',
    'fa': 'تصویر بدون اجازہ',
    'ga': 'Comhad gan ceadúnas',
    'fr': 'Fichier sans licence',
    'hu': 'Licenc nélküli kép',
    'it': 'File senza licenza',
    'ur': 'تصویر بدون اجازہ',
}
# That's the text that the bot will add if it doesn't find the license.
# Note: every __botnick__ will be repleaced with your bot's nickname
# (feel free not to use if you don't need it)
nothing_notification = {
    'commons': (u"\n{{subst:User:Filnik/untagged|File:%s}}\n\n''This message "
                u"was '''added automatically by ~~~''', if you need "
                u"some help about it, please read the text above again and "
                u"follow the links in it, if you still need help ask at the "
                u"[[File:Human-help-browser.svg|18px|link=Commons:Help desk|?]] "
                u"'''[[Commons:Help desk|->]][[Commons:Help desk]]''' in any "
                u"language you like to use.'' --~~~~"""),
    'meta': '{{subst:No license notice|File:%s}}',
    'ar': u"{{subst:مصدر الصورة|File:%s}} --~~~~",
    'en': u"{{subst:image source|File:%s}} --~~~~",
    'fa': u"{{جا:اخطار نگاره|%s}}",
    'ga': u"{{subst:Foinse na híomhá|File:%s}} --~~~~",
    'hu': u"{{subst:adjforrást|Kép:%s}} \n Ezt az üzenetet ~~~ automatikusan "
          u"helyezte el a vitalapodon, kérdéseddel fordulj a gazdájához, vagy "
          u"a [[WP:KF|Kocsmafalhoz]]. --~~~~",
    'it': '{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/Senza licenza|'
          '%s|~~~}} --~~~~',
    'ja': u"\n{{subst:Image copyright|File:%s}}--~~~~",
    'ko': u'\n{{subst:User:Kwjbot IV/untagged|%s}} --~~~~',
    'ta': u'\n{{subst:Di-no license-notice|படிமம்:%s}} ~~~~',
    'ur': u"{{subst:ماخذ تصویر|File:%s}}--~~~~",
    'zh': u'\n{{subst:Uploadvionotice|File:%s}} ~~~~',
}

# This is a list of what bots used this script in your project.
# NOTE: YOUR Bot username will be automatically added.
bot_list = {
    'commons': [u'Siebot', u'CommonsDelinker', u'Filbot', u'John Bot',
                u'Sz-iwbot', u'ABFbot'],
    'meta': ['MABot'],
    'de': [u'Xqbot'],
    'en': [u'OrphanBot'],
    'fa': [u'Amirobot'],
    'ga': [u'AllieBot'],
    'it': [u'Filbot', u'Nikbot', u'.snoopyBot.'],
    'ja': [u'Alexbot'],
    'ko': [u'Kwjbot IV'],
    'ta': [u'TrengarasuBOT'],
    'ur': [u'Shuaib-bot', u'Tahir-bot', u'SAMI.bot'],
    'zh': [u'Alexbot'],
}

# The message that the bot will add the second time that find another license
# problem.
second_message_without_license = {
    'hu': u'\nSzia! Úgy tűnik a [[:Kép:%s]] képpel is hasonló a probléma, '
          u'mint az előbbivel. Kérlek olvasd el a [[WP:KÉPLIC|feltölthető '
          u'képek]]ről szóló oldalunk, és segítségért fordulj a [[WP:KF-JO|'
          u'Jogi kocsmafalhoz]]. Köszönöm --~~~~',
    'it': u':{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/Senza'
          u'licenza2|%s|~~~}} --~~~~',
}

# You can add some settings to a wiki page. In this way, you can change them
# without touching the code. That's useful if you are running the bot on
# Toolserver.
page_with_settings = {
    'commons': u'User:Filbot/Settings',
    'it': u'Progetto:Coordinamento/Immagini/Bot/Settings#Settings',
    'zh': u"User:Alexbot/cisettings#Settings",
}

# The bot can report some images (like the images that have the same name of an
# image on commons) This is the page where the bot will store them.
report_page = {
    'commons': u'User:Filbot/Report',
    'meta': 'User:MABot/Report',
    'de': u'Benutzer:Xqbot/Report',
    'en': u'User:Filnik/Report',
    'fa': u'کاربر:Amirobot/گزارش تصویر',
    'ga': u'User:AllieBot/ReportImages',
    'hu': u'User:Bdamokos/Report',
    'it': u'Progetto:Coordinamento/Immagini/Bot/Report',
    'ja': u'User:Alexbot/report',
    'ko': u'User:Kwjbot IV/Report',
    'ta': u'User:Trengarasu/commonsimages',
    'ur': u'صارف:محمد شعیب/درخواست تصویر',
    'zh': u'User:Alexsh/checkimagereport',
}

# The summary of the report
msg_comm10 = {
    'ar': u'بوت: تحديث السجل',
    'de': u'Bot: schreibe Log',
    'en': u'Bot: Updating the log',
    'fa': u'ربات: به‌روزرسانی سیاهه',
    'fr': u'Robot: Mise à jour du journal',
    'ga': u'Róbó: Log a thabhairt suas chun dáta',
    'hu': u'Robot: A napló frissítése',
    'it': u'Bot: Aggiorno il log',
    'ja': u'ロボットによる:更新',
    'ko': u'로봇:로그 업데이트',
    'ta': u'தானியங்கி:பட்டியலை இற்றைப்படுத்தல்',
    'ur': u'روبالہ: تجدید نوشتہ',
    'zh': u'機器人:更新記錄',
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
    'commons': [u'Template:Information'],
    'meta': ['Template:Information'],
    'ar': [u'Template:معلومات'],
    'de': [u'Template:Information'],
    'en': [u'Template:Information'],
    'fa': [u'الگو:اطلاعات'],
    'fr': [u'Template:Information'],
    'ga': [u'Template:Information'],
    'hu': [u'Template:Információ', u'Template:Enwiki', u'Template:Azonnali'],
    'it': [u'Template:EDP', u'Template:Informazioni file',
           u'Template:Information', u'Template:Trademark',
           u'Template:Permissionotrs'],
    'ja': [u'Template:Information'],
    'ko': [u'Template:그림 정보'],
    'ta': [u'Template:Information'],
    'ur': [u'Template:معلومات'],
    'zh': [u'Template:Information'],
}

# A page where there's a list of template to skip.
PageWithHiddenTemplates = {
    'commons': u'User:Filbot/White_templates#White_templates',
    'it': u'Progetto:Coordinamento/Immagini/Bot/WhiteTemplates',
    'ko': u'User:Kwjbot_IV/whitetemplates/list',
}

# A page where there's a list of template to consider as licenses.
PageWithAllowedTemplates = {
    'commons': u'User:Filbot/Allowed templates',
    'de': u'Benutzer:Xqbot/Lizenzvorlagen',
    'it': u'Progetto:Coordinamento/Immagini/Bot/AllowedTemplates',
    'ko': u'User:Kwjbot_IV/AllowedTemplates',
}

# Template added when the bot finds only an hidden template and nothing else.
# Note: every __botnick__ will be repleaced with your bot's nickname
# (feel free not to use if you don't need it)
HiddenTemplateNotification = {
    'commons': (u"\n{{subst:User:Filnik/whitetemplate|File:%s}}\n\n''This "
                u"message was added automatically by ~~~, if you need "
                u"some help about it please read the text above again and "
                u"follow the links in it, if you still need help ask at the "
                u"[[File:Human-help-browser.svg|18px|link=Commons:Help desk|?]]"
                u" '''[[Commons:Help desk|→]] [[Commons:Help desk]]''' in any "
                u"language you like to use.'' --~~~~"),
    'it': '{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/'
          'Template_insufficiente|%s|~~~}} --~~~~',
    'ko': u"\n{{subst:User:Kwj2772/whitetemplates|%s}} --~~~~",
}

# In this part there are the parameters for the dupe images.

# Put here the template that you want to put in the image to warn that it's a
# dupe. put __image__ if you want only one image, __images__ if you want the
# whole list
duplicatesText = {
    'commons': u'\n{{Dupe|__image__}}',
    'de': u'{{NowCommons}}',
    'it': u'\n{{Progetto:Coordinamento/Immagini/Bot/Template duplicati|__images__}}',
}

# Head of the message given to the author
duplicate_user_talk_head = {
    'de': 'Datei-Duplikat',
    'en': 'Duplicate file',
    'it': 'File doppio',
}

# Message to put in the talk
duplicates_user_talk_text = {
    'it': '{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/Duplicati|'
          '%s|%s|~~~}} --~~~~',
}

# Comment used by the bot while it reports the problem in the uploader's talk
duplicates_comment_talk = {
    'ar': u'بوت: ملف مكرر تم العثور عليه',
    'en': 'Bot: Notify that the file already exists on Commons',
    'fa': u'ربات: تصویر تکراری یافت شد',
    'it': u"Bot: Notifico il file doppio trovato",
}

# Comment used by the bot while it reports the problem in the image
duplicates_comment_image = {
    'de': u'Bot: Datei liegt auf Commons',
    'en': 'Bot: File already on Commons, may be deleted',
    'ar': u'بوت: وسم ملف مكرر',
    'fa': u'ربات: برچسب زدن بر تصویر تکراری',
    'it': u'Bot: File doppio, da cancellare',
}

# Regex to detect the template put in the image's decription to find the dupe
duplicatesRegex = {
    'commons': r'\{\{(?:[Tt]emplate:|)(?:[Dd]up(?:licat|)e|[Bb]ad[ _][Nn]ame)[|}]',
    'de': r'\{\{[nN](?:C|ow(?: c|[cC])ommons)[\|\}',
    'it': r'\{\{(?:[Tt]emplate:|)[Pp]rogetto:[Cc]oordinamento/Immagini/Bot/Template duplicati[|}]',
}

# Category with the licenses and / or with subcategories with the other
# licenses.
category_with_licenses = {
    'commons': u'Category:License tags',
    'meta': 'Category:License templates',
    'ar': u'تصنيف:قوالب حقوق الصور',
    'de': u'Kategorie:Vorlage:Lizenz für Bilder',
    'en': 'Category:Wikipedia file copyright templates',
    'fa': u'رده:الگو:حق تکثیر پرونده',
    'ga': u'Catagóir:Clibeanna cóipchirt d\'íomhánna',
    'it': u'Categoria:Template Licenze copyright',
    'ja': u'Category:画像の著作権表示テンプレート',
    'ko': u'분류:위키백과 그림 저작권 틀',
    'ta': u'Category:காப்புரிமை வார்ப்புருக்கள்',
    'ur': u'زمرہ:ویکیپیڈیا سانچہ جات حقوق تصاویر',
    'zh': u'Category:版權申告模板',
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
                    'ko', 'meta', 'ta', 'ur', 'zh']

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
""", re.UNICODE | re.DOTALL | re.VERBOSE)


class LogIsFull(pywikibot.Error):

    """Log is full and the Bot cannot add other data to prevent Errors."""


def printWithTimeZone(message):
    """Print the messages followed by the TimeZone encoded correctly."""
    time_zone = time.strftime(u"%d %b %Y %H:%M:%S (UTC)", time.gmtime())
    pywikibot.output('{0} {1}'.format(message.rstrip(), time_zone))


class checkImagesBot(object):

    """A robot to check recently uploaded files."""

    def __init__(self, site, logFulNumber=25000, sendemailActive=False,
                 duplicatesReport=False, logFullError=True, max_user_notify=None):
        """Constructor, define some global variable."""
        self.site = site
        self.logFullError = logFullError
        self.logFulNumber = logFulNumber
        self.rep_page = i18n.translate(self.site, report_page)
        self.image_namespace = site.namespaces.FILE.custom_name + ':'
        self.list_entry = '\n* [[:{0}%s]] '.format(self.image_namespace)
        self.com = i18n.translate(self.site, msg_comm10, fallback=True)
        hiddentemplatesRaw = i18n.translate(self.site, HiddenTemplate)
        self.hiddentemplates = set(
            pywikibot.Page(self.site, tmp, ns=self.site.namespaces.TEMPLATE)
            for tmp in hiddentemplatesRaw)
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

    def setParameters(self, image):
        """Set parameters."""
        # ensure we have a FilePage
        self.image = pywikibot.FilePage(image)
        self.imageName = image.title(withNamespace=False)
        self.timestamp = None
        self.uploader = None

    def report(self, newtext, image_to_report, notification=None, head=None,
               notification2=None, unver=True, commTalk=None, commImage=None):
        """Function to make the reports easier."""
        self.image_to_report = image_to_report
        self.newtext = newtext
        self.head = head or u''
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

        while True:
            try:
                resPutMex = self.tag_image(unver)
            except pywikibot.NoPage:
                pywikibot.output(u"The page has been deleted! Skip!")
                break
            except pywikibot.EditConflict:
                pywikibot.output(u"Edit conflict! Skip!")
                break
            else:
                if not resPutMex:
                    break
            if self.notification:
                try:
                    self.put_mex_in_talk()
                except pywikibot.EditConflict:
                    pywikibot.output(u"Edit Conflict! Retrying...")
                    try:
                        self.put_mex_in_talk()
                    except:
                        pywikibot.output(
                            u"Another error... skipping the user..")
                        break
                else:
                    break
            else:
                break

    def uploadBotChangeFunction(self, reportPageText, upBotArray):
        """Detect the user that has uploaded the file through the upload bot."""
        regex = upBotArray[1]
        results = re.findall(regex, reportPageText)

        if results:
            luser = results[0]
            return luser
        else:
            # we can't find the user, report the problem to the bot
            return upBotArray[0]

    def tag_image(self, put=True):
        """Add template to the Image page and find out the uploader."""
        # Get the image's description
        reportPageObject = pywikibot.FilePage(self.site, self.image_to_report)

        try:
            reportPageText = reportPageObject.get()
        except pywikibot.NoPage:
            pywikibot.output(u'%s has been deleted...' % self.imageName)
            return
        # You can use this function also to find only the user that
        # has upload the image (FixME: Rewrite a bit this part)
        if put:
            pywikibot.showDiff(reportPageText,
                               self.newtext + "\n" + reportPageText)
            pywikibot.output(self.commImage)
            try:
                reportPageObject.put(self.newtext + "\n" + reportPageText,
                                     summary=self.commImage)
            except pywikibot.LockedPage:
                pywikibot.output(u'File is locked. Skipping.')
                return
        # paginetta it's the image page object.
        try:
            if reportPageObject == self.image and self.uploader:
                nick = self.uploader
            else:
                nick = reportPageObject.latest_file_info.user
        except pywikibot.PageRelatedError:
            pywikibot.output(
                u"Seems that %s has only the description and not the file..."
                % self.image_to_report)
            repme = self.list_entry + "problems '''with the APIs'''"
            self.report_image(self.image_to_report, self.rep_page, self.com,
                              repme)
            return
        upBots = i18n.translate(self.site, uploadBots)
        user = pywikibot.User(self.site, nick)
        luser = user.title(asUrl=True)

        if upBots:
            for upBot in upBots:
                if upBot[0] == luser:
                    luser = self.uploadBotChangeFunction(reportPageText, upBot)
                    user = pywikibot.User(self.site, luser)
        self.talk_page = user.getUserTalkPage()
        self.luser = luser
        return True

    def put_mex_in_talk(self):
        """Function to put the warning in talk page of the uploader."""
        commento2 = i18n.twtranslate(self.site.lang,
                                     'checkimages-source-notice-comment')
        emailPageName = i18n.translate(self.site, emailPageWithText)
        emailSubj = i18n.translate(self.site, emailSubject)
        if self.notification2:
            self.notification2 = self.notification2 % self.image_to_report
        else:
            self.notification2 = self.notification
        second_text = False
        # Getting the talk page's history, to check if there is another
        # advise...
        try:
            testoattuale = self.talk_page.get()
            history = self.talk_page.getLatestEditors(limit=10)
            latest_user = history[0]["user"]
            pywikibot.output(
                u'The latest user that has written something is: %s'
                % latest_user)
            if latest_user in self.bots:
                second_text = True
                # A block to prevent the second message if the bot also
                # welcomed users...
                if history[0]['timestamp'] == history[-1]['timestamp']:
                    second_text = False
        except pywikibot.IsRedirectPage:
            pywikibot.output(
                u'The user talk is a redirect, trying to get the right talk...')
            try:
                self.talk_page = self.talk_page.getRedirectTarget()
                testoattuale = self.talk_page.get()
            except pywikibot.NoPage:
                second_text = False
                testoattuale = i18n.translate(self.site, empty)
        except pywikibot.NoPage:
            pywikibot.output(u'The user page is blank')
            second_text = False
            testoattuale = i18n.translate(self.site, empty)
        if self.commTalk:
            commentox = self.commTalk
        else:
            commentox = commento2

        if second_text:
            newText = u"%s\n\n%s" % (testoattuale, self.notification2)
        else:
            newText = '{0}\n\n== {1} ==\n{2}'.format(testoattuale, self.head,
                                                     self.notification)

        # Check maximum number of notifications for this talk page
        if (self.num_notify is not None and
                self.num_notify[self.talk_page.title()] == 0):
            pywikibot.output('Maximum notifications reached, skip.')
            return

        try:
            self.talk_page.put(newText, summary=commentox, minorEdit=False)
        except pywikibot.LockedPage:
            pywikibot.output(u'Talk page blocked, skip.')
        else:
            if self.num_notify is not None:
                self.num_notify[self.talk_page.title()] -= 1

        if emailPageName and emailSubj:
            emailPage = pywikibot.Page(self.site, emailPageName)
            try:
                emailText = emailPage.get()
            except (pywikibot.NoPage, pywikibot.IsRedirectPage):
                return
            if self.sendemailActive:
                text_to_send = re.sub(r'__user-nickname__', r'%s'
                                      % self.luser, emailText)
                emailClass = pywikibot.User(self.site, self.luser)
                try:
                    emailClass.send_email(emailSubj, text_to_send)
                except NotEmailableError:
                    pywikibot.output("User is not mailable, aborted")
                    return

    def regexGenerator(self, regexp, textrun):
        """Find page to yield using regex to parse text."""
        regex = re.compile(r'%s' % regexp, re.UNICODE | re.DOTALL)
        results = regex.findall(textrun)
        for image in results:
            yield pywikibot.FilePage(self.site, image)

    def loadHiddenTemplates(self):
        """Function to load the white templates."""
        # A template as {{en is not a license! Adding also them in the
        # whitelist template...
        for langK in Family.load('wikipedia').langs.keys():
            self.hiddentemplates.add(pywikibot.Page(self.site,
                                                    u'Template:%s' % langK))
        # Hidden template loading
        if self.pageHidden:
            try:
                pageHiddenText = pywikibot.Page(self.site,
                                                self.pageHidden).get()
            except (pywikibot.NoPage, pywikibot.IsRedirectPage):
                pageHiddenText = ''

            for element in self.load(pageHiddenText):
                self.hiddentemplates.add(pywikibot.Page(self.site, element))

    def important_image(self, listGiven):
        """
        Get tuples of image and time, return the most used or oldest image.

        @param listGiven: a list of tuples which hold seconds and FilePage
        @type listGiven: list
        @return: the most used or oldest image
        @rtype: FilePage
        """
        # find the most used image
        inx_found = None  # index of found image
        max_usage = 0  # hold max amount of using pages
        for num, element in enumerate(listGiven):
            image = element[1]
            image_used = len([page for page in image.usingPages()])
            if image_used > max_usage:
                max_usage = image_used
                inx_found = num

        if inx_found is not None:
            return listGiven[inx_found][1]

        # find the oldest image
        sec, image = max(listGiven, key=lambda element: element[0])
        return image

    def checkImageOnCommons(self):
        """Checking if the file is on commons."""
        pywikibot.output(u'Checking if [[%s]] is on commons...'
                         % self.imageName)
        try:
            hash_found = self.image.latest_file_info.sha1
        except pywikibot.NoPage:
            return  # Image deleted, no hash found. Skip the image.

        site = pywikibot.Site('commons', 'commons')
        commons_image_with_this_hash = next(iter(site.allimages(sha1=hash_found,
                                                                total=1)), None)
        if commons_image_with_this_hash:
            servTMP = pywikibot.translate(self.site, serviceTemplates)
            templatesInTheImage = self.image.templates()
            if servTMP is not None:
                for template in servTMP:
                    if pywikibot.Page(self.site,
                                      template) in templatesInTheImage:
                        pywikibot.output(
                            u"%s is on commons but it's a service image."
                            % self.imageName)
                        return True  # continue with the check-part

            pywikibot.output(u'%s is on commons!' % self.imageName)
            if self.image.fileIsShared():
                pywikibot.output(
                    u"But, the file doesn't exist on your project! Skip...")
                # We have to skip the check part for that image because
                # it's on commons but someone has added something on your
                # project.
                return

            if re.findall(r'\bstemma\b', self.imageName.lower()) and \
               self.site.code == 'it':
                pywikibot.output(
                    u'%s has "stemma" inside, means that it\'s ok.'
                    % self.imageName)
                return True

            # It's not only on commons but the image needs a check
            # the second usually is a url or something like that.
            # Compare the two in equal way, both url.
            repme = ((self.list_entry +
                      "is also on '''Commons''': [[commons:File:%s]]")
                     % (self.imageName,
                        commons_image_with_this_hash.title(
                            withNamespace=False)))
            if (self.image.title(asUrl=True) ==
                    commons_image_with_this_hash.title(asUrl=True)):
                repme += " (same name)"
            self.report_image(self.imageName, self.rep_page, self.com, repme,
                              addings=False)
        return True

    def checkImageDuplicated(self, duplicates_rollback):
        """Function to check the duplicated files."""
        dupText = i18n.translate(self.site, duplicatesText)
        dupRegex = i18n.translate(self.site, duplicatesRegex)
        dupTalkHead = i18n.translate(self.site, duplicate_user_talk_head,
                                     fallback=True)
        dupTalkText = i18n.translate(self.site, duplicates_user_talk_text)
        dupComment_talk = i18n.translate(self.site, duplicates_comment_talk,
                                         fallback=True)
        dupComment_image = i18n.translate(self.site, duplicates_comment_image,
                                          fallback=True)
        imagePage = pywikibot.FilePage(self.site, self.imageName)
        hash_found = imagePage.latest_file_info.sha1
        duplicates = list(self.site.allimages(sha1=hash_found))

        if not duplicates:
            return  # Error, image deleted, no hash found. Skip the image.

        if len(duplicates) > 1:
            xdict = {'en':
                     u'%(name)s has {{PLURAL:count'
                     u'|a duplicate! Reporting it'
                     u'|%(count)s duplicates! Reporting them}}...'}
            pywikibot.output(i18n.translate('en', xdict,
                                            {'name': self.imageName,
                                             'count': len(duplicates) - 1}))
            if dupText and dupRegex:
                time_image_list = []

                for dup_page in duplicates:
                    if (dup_page.title(asUrl=True) != self.image.title(asUrl=True) or
                            self.timestamp is None):
                        try:
                            self.timestamp = dup_page.latest_file_info.timestamp
                        except pywikibot.PageRelatedError:
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
                    except pywikibot.NoPage:
                        continue

                    if not (re.findall(dupRegex, DupPageText) or
                            re.findall(dupRegex, older_page_text)):
                        pywikibot.output(
                            u'%s is a duplicate and has to be tagged...'
                            % dup_page)
                        images_to_tag_list.append(dup_page.title())
                        string += '* {0}\n'.format(
                            dup_page.title(asLink=True, textlink=True))
                    else:
                        pywikibot.output(
                            u"Already put the dupe-template in the files's page"
                            u" or in the dupe's page. Skip.")
                        return  # Ok - Let's continue the checking phase

                # true if the image are not to be tagged as dupes
                only_report = False

                # put only one image or the whole list according to the request
                if u'__images__' in dupText:
                    text_for_the_report = dupText.replace(
                        '__images__',
                        '\n{0}* {1}\n'.format(
                            string,
                            Page_older_image.title(asLink=True, textlink=True)))
                else:
                    text_for_the_report = dupText.replace(
                        '__image__',
                        Page_older_image.title(asLink=True, textlink=True))

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
                        text_for_the_report = re.sub(
                            r'\n\*\[\[:%s\]\]'
                            % re.escape(self.image_namespace + image_to_tag),
                            '', text_for_the_report)
                        self.report(text_for_the_report, image_to_tag,
                                    commImage=dupComment_image, unver=True)

                if len(images_to_tag_list) != 0 and not only_report:
                    fp = pywikibot.FilePage(self.site, images_to_tag_list[-1])
                    already_reported_in_past = fp.revision_count(self.bots)
                    from_regex = (r'\n\*\[\[:%s%s\]\]'
                                  % (self.image_namespace,
                                     re.escape(self.image.title(asUrl=True))))
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
                            % (Page_older_image.title(withNamespace=True),
                               string),
                            dupTalkHead, commTalk=dupComment_talk,
                            commImage=dupComment_image, unver=True)

            if self.duplicatesReport or only_report:
                if only_report:
                    repme = ((self.list_entry + 'has the following duplicates '
                              "('''forced mode'''):")
                             % self.image.title(asUrl=True))
                else:
                    repme = ((self.list_entry + 'has the following duplicates:')
                             % self.image.title(asUrl=True))

                for dup_page in duplicates:
                    if dup_page.title(asUrl=True) == self.image.title(asUrl=True):
                        # the image itself, not report also this as duplicate
                        continue
                    repme += '\n** [[:%s%s]]' % (self.image_namespace,
                                                 dup_page.title(asUrl=True))

                result = self.report_image(self.imageName, self.rep_page,
                                           self.com, repme, addings=False)
                if not result:
                    return True  # If Errors, exit (but continue the check)

            if Page_older_image.title() != self.imageName:
                # The image is a duplicate, it will be deleted. So skip the
                # check-part, useless
                return
        return True  # Ok - No problem. Let's continue the checking phase

    def report_image(self, image_to_report, rep_page=None, com=None,
                     rep_text=None, addings=True):
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
        except pywikibot.NoPage:
            text_get = ''
        except pywikibot.IsRedirectPage:
            text_get = another_page.getRedirectTarget().get()

        # Don't care for differences inside brackets.
        end = rep_text.find('(', max(0, rep_text.find(']]')))
        if end < 0:
            end = None
        short_text = rep_text[rep_text.find('[['):end].strip()

        reported = True
        # Skip if the message is already there.
        if short_text in text_get:
            pywikibot.output(u"%s is already in the report page."
                             % image_to_report)
            reported = False
        elif len(text_get) >= self.logFulNumber:
            if self.logFullError:
                raise LogIsFull(
                    u"The log page (%s) is full! Please delete the old files "
                    u"reported." % another_page.title())
            else:
                pywikibot.output(
                    u"The log page (%s) is full! Please delete the old files "
                    u" reported. Skip!" % another_page.title())
                # Don't report, but continue with the check
                # (we don't know if this is the first time we check this file
                # or not)
        else:
            # Adding the log
            another_page.put(text_get + rep_text, summary=com, force=True,
                             minorEdit=False)
            pywikibot.output(u"...Reported...")
        return reported

    def takesettings(self):
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
                            u"You've set wrongly your settings, please take a "
                            u"look to the relative page. (run without them)")
                        self.settingsData = None
                except pywikibot.NoPage:
                    pywikibot.output(u"The settings' page doesn't exist!")
                    self.settingsData = None
        except pywikibot.Error:
            pywikibot.output(
                u'Problems with loading the settigs, run without them.')
            self.settingsData = None
            self.some_problem = False

        if not self.settingsData:
            self.settingsData = None

        # Real-Time page loaded
        if self.settingsData:
            pywikibot.output(u'>> Loaded the real-time page... <<')
        else:
            pywikibot.output(u'>> No additional settings found! <<')

    def load_licenses(self):
        """Load the list of the licenses."""
        catName = i18n.translate(self.site, category_with_licenses)
        if not catName:
            raise pywikibot.Error(
                u'No licenses allowed provided, add that option to the code to '
                u'make the script working correctly')
        pywikibot.output(u'\nLoading the allowed licenses...\n')
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
            except (pywikibot.NoPage, pywikibot.IsRedirectPage):
                pageAllowedText = ''

            for nameLicense in self.load(pageAllowedText):
                pageLicense = pywikibot.Page(self.site, nameLicense)
                if pageLicense not in list_licenses:
                    list_licenses.append(pageLicense)  # the list has wiki-pages
        return list_licenses

    def miniTemplateCheck(self, template):
        """Check if template is in allowed licenses or in licenses to skip."""
        # the list_licenses are loaded in the __init__
        # (not to load them multimple times)
        if template in self.list_licenses:
            self.license_selected = template.title(withNamespace=False)
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
                return
            else:
                self.whiteTemplatesFound = True

    def templateInList(self):
        """
        Check if template is in list.

        The problem is the calls to the Mediawiki system because they can be
        pretty slow. While searching in a list of objects is really fast, so
        first of all let's see if we can find something in the info that we
        already have, then make a deeper check.
        """
        for template in self.licenses_found:
            result = self.miniTemplateCheck(template)
            if result:
                break
        if not self.license_found:
            for template in self.licenses_found:
                if template.isRedirectPage():
                    template = template.getRedirectTarget()
                    result = self.miniTemplateCheck(template)
                    if result:
                        break

    def smartDetection(self):
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
                    raise pywikibot.Error(
                        "Invalid or broken templates found in the image's "
                        "page %s!" % self.image)
            self.allLicenses = []

            if not self.list_licenses:
                raise pywikibot.Error(
                    u'No licenses allowed provided, add that option to the '
                    u'code to make the script working correctly')

            # Found the templates ONLY in the image's description
            for template_selected in templatesInTheImageRaw:
                tp = pywikibot.Page(self.site, template_selected)
                for templateReal in self.licenses_found:
                    if (tp.title(asUrl=True, withNamespace=False).lower() ==
                            templateReal.title(asUrl=True,
                                               withNamespace=False).lower()):
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
                pywikibot.output(u'File already fixed. Skipping.')
            else:
                pywikibot.output(
                    u"The file's description for %s contains %s..."
                    % (self.imageName, self.name_used))
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
                    pywikibot.output(u"Skipping the file...")
                self.some_problem = False
        else:
            if not self.seems_ok and self.license_found:
                rep_text_license_fake = ((self.list_entry +
                                          "seems to have a ''fake license'', "
                                          'license detected: '
                                          '<nowiki>%s</nowiki>') %
                                         (self.imageName, self.license_found))
                printWithTimeZone(
                    u"%s seems to have a fake license: %s, reporting..."
                    % (self.imageName, self.license_found))
                self.report_image(self.imageName,
                                  rep_text=rep_text_license_fake,
                                  addings=False)
            elif self.license_found:
                pywikibot.output(u"[[%s]] seems ok, license found: {{%s}}..."
                                 % (self.imageName, self.license_found))
        return (self.license_found, self.whiteTemplatesFound)

    def load(self, raw):
        """Load a list of objects from a string using regex."""
        list_loaded = []
        # I search with a regex how many user have not the talk page
        # and i put them in a list (i find it more easy and secure)
        regl = r"(\"|\')(.*?)\1(?:,|\])"
        pl = re.compile(regl, re.UNICODE)
        for xl in pl.finditer(raw):
            word = xl.group(2).replace(u'\\\\', u'\\')
            if word not in list_loaded:
                list_loaded.append(word)
        return list_loaded

    def skipImages(self, skip_number, limit):
        """Given a number of files, skip the first -number- files."""
        # If the images to skip are more the images to check, make them the
        # same number
        if skip_number == 0:
            pywikibot.output(u'\t\t>> No files to skip...<<')
            return
        if skip_number > limit:
            skip_number = limit
        # Print a starting message only if no images has been skipped
        if not self.skip_list:
            pywikibot.output(
                i18n.translate(
                    'en',
                    u'Skipping the first {{PLURAL:num|file|%(num)s files}}:\n',
                    {'num': skip_number}))
        # If we still have pages to skip:
        if len(self.skip_list) < skip_number:
            pywikibot.output(u'Skipping %s...' % self.imageName)
            self.skip_list.append(self.imageName)
            if skip_number == 1:
                pywikibot.output('')
            return True
        else:
            pywikibot.output('')

    @staticmethod
    def wait(generator, wait_time):
        """
        Skip the images uploaded before x seconds.

        Let the users to fix the image's problem alone in the first x seconds.
        """
        printWithTimeZone(
            u'Skipping the files uploaded less than %s seconds ago..'
            % wait_time)
        for page in generator:
            image = pywikibot.FilePage(page)
            try:
                timestamp = image.latest_file_info.timestamp
            except pywikibot.PageRelatedError:
                continue
            now = pywikibot.Timestamp.utcnow()
            delta = now - timestamp
            if delta.total_seconds() > wait_time:
                yield image
            else:
                pywikibot.warning(
                    u'Skipping %s, uploaded %d %s ago..'
                    % ((image.title(), delta.days, 'days')
                       if delta.days > 0
                       else (image.title(), delta.seconds, 'seconds')))

    def isTagged(self):
        """Understand if a file is already tagged or not."""
        # TODO: enhance and use textlib._MultiTemplateMatchBuilder
        # Is the image already tagged? If yes, no need to double-check, skip
        for i in i18n.translate(self.site, txt_find):
            # If there are {{ use regex, otherwise no (if there's not the
            # {{ may not be a template and the regex will be wrong)
            if '{{' in i:
                regexP = re.compile(r'\{\{(?:template)?%s ?(?:\||\r?\n|\}|<|/) ?'
                                    % i.split('{{')[1].replace(u' ', u'[ _]'),
                                    re.I)
                result = regexP.findall(self.imageCheckText)
                if result:
                    return True
            elif i.lower() in self.imageCheckText:
                return True

    def findAdditionalProblems(self):
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
                pywikibot.error(u"Imagechanges set wrongly!")
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
                    searchResults = re.findall(r'%s' % k.lower(),
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
                    if re.findall(r'%s' % k.lower(),
                                  self.imageCheckText.lower()):
                        self.some_problem = True
                        self.text_used = text
                        self.head_used = head_2
                        self.imagestatus_used = imagestatus
                        self.name_used = name
                        self.summary_used = summary
                        self.mex_used = mexCatched
                        continue

    def checkStep(self):
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
        dih = i18n.translate(self.site, delete_immediately_head, fallback=True)
        din = i18n.translate(self.site, delete_immediately_notification,
                             fallback=True) + ' ~~~~'
        nh = i18n.translate(self.site, nothing_head, fallback=True)
        nn = i18n.translate(self.site, nothing_notification)
        dels = i18n.translate(self.site, msg_del_comm, fallback=True)
        smwl = i18n.translate(self.site, second_message_without_license)

        try:
            self.imageCheckText = self.image.get()
        except pywikibot.NoPage:
            pywikibot.output(u"Skipping %s because it has been deleted."
                             % self.imageName)
            return
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"Skipping %s because it's a redirect."
                             % self.imageName)
            return
        # Delete the fields where the templates cannot be loaded
        regex_nowiki = re.compile(r'<nowiki>(.*?)</nowiki>', re.DOTALL)
        regex_pre = re.compile(r'<pre>(.*?)</pre>', re.DOTALL)
        self.imageCheckText = regex_nowiki.sub('', self.imageCheckText)
        self.imageCheckText = regex_pre.sub('', self.imageCheckText)
        # Deleting the useless template from the description (before adding sth
        # in the image the original text will be reloaded, don't worry).
        if self.isTagged():
            printWithTimeZone(u'%s is already tagged...' % self.imageName)
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
        elif delete:
            pywikibot.output(u"%s is not a file!" % self.imageName)
            if not di:
                pywikibot.output('No localized message given for '
                                 "'delete_immediately'. Skipping.")
                return
            # Some formatting for delete immediately template
            dels = dels % {'adding': di}
            di = '\n' + di
            # Modify summary text
            pywikibot.setAction(dels)
            canctext = di % extension
            notification = din % {'file': self.image.title(asLink=True,
                                                           textlink=True)}
            head = dih
            self.report(canctext, self.imageName, notification, head)
            return
        elif not self.imageCheckText.strip():  # empty image description
            pywikibot.output(
                u"The file's description for %s does not contain a license "
                u" template!" % self.imageName)
            if hiddenTemplateFound and HiddenTN:
                notification = HiddenTN % self.imageName
            elif nn:
                notification = nn % self.imageName
            head = nh
            self.report(self.unvertext, self.imageName, notification, head,
                        smwl)
            return
        else:
            pywikibot.output(u"%s has only text and not the specific license..."
                             % self.imageName)
            if hiddenTemplateFound and HiddenTN:
                notification = HiddenTN % self.imageName
            elif nn:
                notification = nn % self.imageName
            head = nh
            self.report(self.unvertext, self.imageName, notification, head,
                        smwl)
            return


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
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

    # Here below there are the parameters.
    for arg in pywikibot.handle_args(args):
        if arg.startswith('-limit'):
            if len(arg) == 6:
                limit = int(pywikibot.input(
                    u'How many files do you want to check?'))
            else:
                limit = int(arg[7:])
        if arg.startswith('-sleep') or arg.startswith('-time'):
            if arg.startswith('-sleep'):
                length = len('-sleep')
            else:
                issue_deprecation_warning('-time', '-sleep', 2,
                                          ArgumentDeprecationWarning)
                length = len('-time')
            if len(arg) == length:
                time_sleep = int(pywikibot.input(
                    'How many seconds do you want runs to be apart?'))
            else:
                time_sleep = int(arg[length + 1:])
        elif arg == '-break':
            repeat = False
        elif arg == '-nologerror':
            logFullError = False
        elif arg == '-commons':
            commonsActive = True
        elif arg == '-duplicatesreport' or arg == '-duplicatereport':
            if arg == '-duplicatereport':
                issue_deprecation_warning('-duplicatereport',
                                          '-duplicatesreport',
                                          2, ArgumentDeprecationWarning)
            duplicatesReport = True
        elif arg.startswith('-duplicates'):
            duplicatesActive = True
            if len(arg) == 11:
                duplicates_rollback = 1
            elif len(arg) > 11:
                duplicates_rollback = int(arg[12:])
        elif arg.startswith('-maxusernotify'):
            if len(arg) == 13:
                max_user_notify = int(pywikibot.input(
                    'What should be the maximum number of notifications per '
                    'user per check?'))
            elif len(arg) > 13:
                max_user_notify = int(arg[14:])
        elif arg == '-sendemail':
            sendemailActive = True
        elif arg.startswith('-skip'):
            if len(arg) == 5:
                skip_number = int(pywikibot.input(
                    u'How many files do you want to skip?'))
            elif len(arg) > 5:
                skip_number = int(arg[6:])
        elif arg.startswith('-wait'):
            if len(arg) == 5:
                waitTime = int(pywikibot.input(
                    u'How many time do you want to wait before checking the '
                    u'files?'))
            elif len(arg) > 5:
                waitTime = int(arg[6:])
        elif arg.startswith('-start'):
            if len(arg) == 6:
                firstPageTitle = pywikibot.input(
                    u'From which page do you want to start?')
            elif len(arg) > 6:
                firstPageTitle = arg[7:]
            firstPageTitle = firstPageTitle.split(":")[1:]
            generator = pywikibot.Site().allpages(start=firstPageTitle,
                                                  namespace=6)
            repeat = False
        elif arg.startswith('-page'):
            if len(arg) == 5:
                regexPageName = str(pywikibot.input(
                    u'Which page do you want to use for the regex?'))
            elif len(arg) > 5:
                regexPageName = str(arg[6:])
            repeat = False
            regexGen = True
        elif arg.startswith('-url'):
            if len(arg) == 4:
                regexPageUrl = str(pywikibot.input(
                    u'Which url do you want to use for the regex?'))
            elif len(arg) > 4:
                regexPageUrl = str(arg[5:])
            urlUsed = True
            repeat = False
            regexGen = True
        elif arg.startswith('-regex'):
            if len(arg) == 6:
                regexpToUse = str(pywikibot.input(
                    u'Which regex do you want to use?'))
            elif len(arg) > 6:
                regexpToUse = str(arg[7:])
            generator = 'regex'
            repeat = False
        elif arg.startswith('-cat'):
            if len(arg) == 4:
                catName = str(pywikibot.input(u'In which category do I work?'))
            elif len(arg) > 4:
                catName = str(arg[5:])
            catSelected = pywikibot.Category(pywikibot.Site(),
                                             'Category:%s' % catName)
            generator = catSelected.articles(namespaces=[6])
            repeat = False
        elif arg.startswith('-ref'):
            if len(arg) == 4:
                refName = str(pywikibot.input(
                    u'The references of what page should I parse?'))
            elif len(arg) > 4:
                refName = str(arg[5:])
            ref = pywikibot.Page(pywikibot.Site(), refName)
            generator = ref.getReferences(namespaces=[6])
            repeat = False

    if not generator:
        normal = True

    site = pywikibot.Site()
    skip = skip_number > 0

    # A little block-statement to ensure that the bot will not start with
    # en-parameters
    if site.code not in project_inserted:
        pywikibot.output(u"Your project is not supported by this script.\n"
                         u"You have to edit the script and add it!")
        return False

    # Reading the log of the new images if another generator is not given.
    if normal:
        if limit == 1:
            pywikibot.output(u"Retrieving the latest file for checking...")
        else:
            pywikibot.output(u"Retrieving the latest %d files for checking..."
                             % limit)
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
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist!" % pageRegex.title())
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
            if skip:
                skip = Bot.skipImages(skip_number, limit)
                if skip:
                    continue
            # Check on commons if there's already an image with the same name
            if commonsActive and site.family.name != "commons":
                if not Bot.checkImageOnCommons():
                    continue
            # Check if there are duplicates of the image on the project selected
            if duplicatesActive:
                if not Bot.checkImageDuplicated(duplicates_rollback):
                    continue
            Bot.checkStep()

        if repeat:
            pywikibot.output(u"Waiting for %s seconds," % time_sleep)
            pywikibot.stopme()
            time.sleep(time_sleep)
        else:
            break


if __name__ == "__main__":
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
            pywikibot.output("Execution time: %s seconds\n" % delta)
