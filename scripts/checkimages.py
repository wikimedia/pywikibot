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

-sendemail          Send an email after tagging.

-break              To break the bot after the first check (default: recursive)

-time[:#]           Time in seconds between repeat runs (default: 30)

-wait[:#]           Wait x second before check the images (default: 0)
                    NOT YET IMPLEMENTED

-skip[:#]           The bot skip the first [:#] images (default: 0)

-start[:#]          Use allpages() as generator
                    (it starts already form File:[:#])

-cat[:#]            Use a category as generator

-regex[:#]          Use regex, must be used with -url or -page

-page[:#]           Define the name of the wikipage where are the images

-url[:#]            Define the url where are the images

-nologerror         If given, this option will disable the error that is risen
                    when the log is full.

---- Instructions for the real-time settings  ----
* For every new block you have to add:

<------- ------->

In this way the Bot can understand where the block starts in order to take the
right parameter.

* Name=     Set the name of the block
* Find=     Use it to define what search in the text of the image's description,
            while
  Findonly= search only if the exactly text that you give is in the image's
            description.
* Summary=  That's the summary that the bot will use when it will notify the
            problem.
* Head=     That's the incipit that the bot will use for the message.
* Text=     This is the template that the bot will use when it will report the
            image's problem.

---- Known issues/FIXMEs: ----
* Clean the code, some passages are pretty difficult to understand if you're not
  the coder.
* Add the "catch the language" function for commons.
* Fix and reorganise the new documentation
* Add a report for the image tagged.

"""

#
# (C) Kyle/Orgullomoore, 2006-2007 (newimage.py)
# (C) Siebrand Mazeland, 2007-2010
# (C) Filnik, 2007-2011
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re
import time
import datetime
import locale
import sys

import pywikibot
from pywikibot import pagegenerators as pg
from pywikibot import config, i18n
from pywikibot.family import Family

if sys.version_info[0] > 2:
    basestring = (str, )

locale.setlocale(locale.LC_ALL, '')

###############################################################################
# <--------------------------- Change only below! --------------------------->#
###############################################################################

# NOTE: in the messages used by the Bot if you put __botnick__ in the text, it
# will automatically replaced with the bot's nickname.

# That's what you want that will be added. (i.e. the {{no source}} with the
# right day/month/year )
n_txt = {
    'commons': u'{{subst:nld}}',
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

# Summary for when the will add the no source
msg_comm = {
    'ar': u'بوت: التعليم على ملف مرفوع حديثا غير موسوم',
    'commons': u'Bot: Marking newly uploaded untagged file',
    'de': u'Bot: Markiere mit {{[[Wikipedia:Dateiüberprüfung/Anleitung|DÜP]]}},'
          u' da keine Lizenzvorlage gefunden — bitte nicht entfernen,'
          u' Informationen bald auf der Benutzerdiskussion des Uploaders.',
    'en': u'Bot: Marking newly uploaded untagged file',
    'fa': u'ربات: حق تکثیر تصویر تازه بارگذاری شده نامعلوم است.',
    'ga': u'Róbó: Ag márcáil comhad nua-uaslódáilte gan ceadúnas',
    'hu': u'Robot: Frissen feltöltött licencsablon nélküli fájl megjelölése',
    'it': u"Bot: Aggiungo unverified",
    'ja': u'ロボットによる:著作権情報なしの画像をタグ',
    'ko': u'로봇:라이선스 없음',
    'ta': u'தானியங்கி:காப்புரிமை வழங்கப்படா படிமத்தை சுட்டுதல்',
    'ur': u'روبالہ:نشان زدگی جدید زبراثقال شدہ املاف',
    'zh': u'機器人:標示新上傳且未包含必要資訊的檔案',
}

# When the Bot find that the usertalk is empty is not pretty to put only the
# no source without the welcome, isn't it?
empty = {
    'commons': u'{{subst:welcome}}\n~~~~\n',
    'ar': u'{{ترحيب}}\n~~~~\n',
    'de': u'{{subst:willkommen}} ~~~~',
    'en': u'{{welcome}}\n~~~~\n',
    'fa': u'{{جا:خوشامدید|%s}}',
    'fr': u'{{Bienvenue nouveau\n~~~~\n',
    'ga': u'{{subst:Fáilte}} - ~~~~\n',
    'hu': u'{{subst:Üdvözlet|~~~~}}\n',
    'it': u'<!-- inizio template di benvenuto -->\n{{subst:Benvebot}}\n~~~~\n<!-- fine template di benvenuto -->',
    'ja': u'{{subst:Welcome/intro}}\n{{subst:welcome|--~~~~}}\n',
    'ko': u'{{환영}}--~~~~\n',
    'ta': u'{{welcome}}\n~~~~\n',
    'ur': u'{{خوش آمدید}}\n~~~~\n',
    'zh': u'{{subst:welcome|sign=~~~~}}',
}

# Summary that the bot use when it notify the problem with the image's license
msg_comm2 = {
    'ar': u'بوت: طلب معلومات المصدر.',
    'commons': u'Bot: Requesting source information.',
    'de': u'Bot:Notify User',
    'en': u'Robot: Requesting source information.',
    'fa': u'ربات: درخواست منبع تصویر',
    'ga': u'Róbó: Ag iarraidh eolais foinse.',
    'it': u"Bot: Notifico l'unverified",
    'hu': u'Robot: Forrásinformáció kérése',
    'ja': u'ロボットによる:著作権情報明記のお願い',
    'ko': u'로봇:라이선스 정보 요청',
    'ta': u'தானியங்கி:மூலம் வழங்கப்படா படிமத்தை சுட்டுதல்',
    'ur': u'روبالہ:درخواست ماخذ تصویر',
    'zh': u'機器人：告知用戶',
}

# if the file has an unknown extension it will be tagged with this template.
# In reality, there aren't unknown extension, they are only not allowed...
delete_immediately = {
    'commons': u"{{speedy|The file has .%s as extension. Is it ok? Please check.}}",
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
    'commons': u"\n== Unknown extension! ==\n",
    'ar': u"\n== امتداد غير معروف! ==\n",
    'en': u"\n== Unknown extension! ==\n",
    'fa': u"\n==بارگذاری تصاویر موجود در انبار==\n",
    'ga': u"\n== Iarmhír neamhaithnid! ==\n",
    'fr': u'\n== Extension inconnue ==\n',
    'hu': u'\n== Ismeretlen kiterjesztésű fájl ==\n',
    'it': u'\n\n== File non specificato ==\n',
    'ko': u'\n== 잘못된 파일 형식 ==\n',
    'ta': u'\n== இனங்காணப்படாத கோப்பு நீட்சி! ==\n',
    'ur': u"\n== نامعلوم توسیع! ==\n",
    'zh': u'\n==您上載的檔案格式可能有誤==\n',
}

# Text that will be add if the bot find a unknown extension.
delete_immediately_notification = {
    'ar': u'الملف [[:File:%s]] يبدو أن امتداده خاطيء, من فضلك تحقق. ~~~~',
    'commons': u'The [[:File:%s]] file seems to have a wrong extension, please check. ~~~~',
    'en': u'The [[:File:%s]] file seems to have a wrong extension, please check. ~~~~',
    'fa': u'به نظر می‌آید تصویر [[:تصویر:%s]] مسیر نادرستی داشته باشد لطفا بررسی کنید.~~~~',
    'ga': u'Tá iarmhír mícheart ar an comhad [[:File:%s]], scrúdaigh le d\'thoil. ~~~~',
    'fr': u'Le fichier [[:File:%s]] semble avoir une mauvaise extension, veuillez vérifier. ~~~~',
    'hu': u'A [[:Kép:%s]] fájlnak rossz a kiterjesztése, kérlek ellenőrízd. ~~~~',
    'it': u'{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/Ext|%s|__botnick__}} --~~~~',
    'ko': u'[[:그림:%s]]의 파일 형식이 잘못되었습니다. 확인 바랍니다.--~~~~',
    'ta': u'[[:படிமம்:%s]] இனங்காணப்படாத கோப்பு நீட்சியை கொண்டுள்ளது தயவு செய்து ஒரு முறை சரி பார்க்கவும் ~~~~',
    'ur': u'ملف [[:File:%s]] کی توسیع شاید درست نہیں ہے، براہ کرم جانچ لیں۔ ~~~~',
    'zh': u'您好，你上傳的[[:File:%s]]無法被識別，請檢查您的檔案，謝謝。--~~~~',
}

# Summary of the delete immediately.
# (e.g: Adding {{db-meta|The file has .%s as extension.}})
msg_del_comm = {
    'ar': u'بوت: إضافة %s',
    'commons': u'Bot: Adding %s',
    'en': u'Bot: Adding %s',
    'fa': u'ربات: اضافه کردن %s',
    'ga': u'Róbó: Cuir %s leis',
    'fr': u'Robot : Ajouté %s',
    'hu': u'Robot:"%s" hozzáadása',
    'it': u'Bot: Aggiungo %s',
    'ja': u'ロボットによる: 追加 %s',
    'ko': u'로봇 : %s 추가',
    'ta': u'Bot: Adding %s',
    'ur': u'روبالہ: اضافہ %s',
    'zh': u'機器人: 正在新增 %s',
}

# This is the most important header, because it will be used a lot. That's the
# header that the bot will add if the image hasn't the license.
nothing_head = {
    'ar': u"\n== صورة بدون ترخيص ==\n",
    'de': u"\n== Bild ohne Lizenz ==\n",
    'en': u"\n== Image without license ==\n",
    'fa': u"\n== تصویر بدون اجازہ ==\n",
    'ga': u"\n== Comhad gan ceadúnas ==\n",
    'fr': u"\n== Fichier sans licence ==\n",
    'hu': u"\n== Licenc nélküli kép ==\n",
    'it': u"\n\n== File senza licenza ==\n",
    'ur': u"\n== تصویر بدون اجازہ ==\n",
}
# That's the text that the bot will add if it doesn't find the license.
# Note: every __botnick__ will be repleaced with your bot's nickname
# (feel free not to use if you don't need it)
nothing_notification = {
    'commons': (u"\n{{subst:User:Filnik/untagged|File:%s}}\n\n''This message "
                u"was '''added automatically by __botnick__''', if you need "
                u"some help about it, please read the text above again and "
                u"follow the links in it, if you still need help ask at the "
                u"[[File:Human-help-browser.svg|18px|link=Commons:Help desk|?]] "
                u"'''[[Commons:Help desk|->]][[Commons:Help desk]]''' in any "
                u"language you like to use.'' --__botnick__ ~~~~~"""),
    'ar': u"{{subst:مصدر الصورة|File:%s}} --~~~~",
    'en': u"{{subst:image source|File:%s}} --~~~~",
    'fa': u"{{جا:اخطار نگاره|%s}}",
    'ga': u"{{subst:Foinse na híomhá|File:%s}} --~~~~",
    'hu': u"{{subst:adjforrást|Kép:%s}} \n Ezt az üzenetet ~~~ automatikusan helyezte el a vitalapodon, kérdéseddel fordulj a gazdájához, vagy a [[WP:KF|Kocsmafalhoz]]. --~~~~",
    'it': u"{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/Senza licenza|%s|__botnick__}} --~~~~",
    'ja': u"\n{{subst:Image copyright|File:%s}}--~~~~",
    'ko': u'\n{{subst:User:Kwjbot IV/untagged|%s}} --~~~~',
    'ta': u'\n{{subst:Di-no license-notice|படிமம்:%s}} ~~~~',
    'ur': u"{{subst:ماخذ تصویر|File:%s}}--~~~~",
    'zh': u'\n{{subst:Uploadvionotice|File:%s}} ~~~~',
}

# This is a list of what bots used this script in your project.
# NOTE: YOUR Botnick is automatically added. It's not required to add it twice.
bot_list = {
    'commons': [u'Siebot', u'CommonsDelinker', u'Filbot', u'John Bot',
                u'Sz-iwbot', u'ABFbot'],
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
    'hu': u'\nSzia! Úgy tűnik a [[:Kép:%s]] képpel is hasonló a probléma, mint az előbbivel. Kérlek olvasd el a [[WP:KÉPLIC|feltölthető képek]]ről szóló oldalunk, és segítségért fordulj a [[WP:KF-JO|Jogi kocsmafalhoz]]. Köszönöm --~~~~',
    'it': u':{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/Senza licenza2|%s|__botnick__}} --~~~~',
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

# Adding the date after the signature.
timeselected = u' ~~~~~'

# The text added in the report
report_text = {
    'commons': u"\n*[[:File:%s]] " + timeselected,
    'ar': u"\n*[[:ملف:%s]] " + timeselected,
    'de': u"\n*[[:Datei:%s]] " + timeselected,
    'en': u"\n*[[:File:%s]] " + timeselected,
    'fa': u"n*[[:پرونده:%s]] " + timeselected,
    'ga': u"\n*[[:File:%s]] " + timeselected,
    'hu': u"\n*[[:Kép:%s]] " + timeselected,
    'it': u"\n*[[:File:%s]] " + timeselected,
    'ja': u"\n*[[:File:%s]] " + timeselected,
    'ko': u"\n*[[:그림:%s]] " + timeselected,
    'ta': u"\n*[[:படிமம்:%s]] " + timeselected,
    'ur': u"\n*[[:تصویر:%s]] " + timeselected,
    'zh': u"\n*[[:File:%s]] " + timeselected,
}

# The summary of the report
msg_comm10 = {
    'commons': u'Bot: Updating the log',
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

    'ar': [u'Template:معلومات'],
    'de': [u'Template:Information'],
    'en': [u'Template:Information'],
    'fa': [u'الگو:اطلاعات'],
    'fr': [u'Template:Information'],
    'ga': [u'Template:Information'],
    'hu': [u'Template:Információ', u'Template:Enwiki', u'Template:Azonnali'],
    # Put the other in the page on the project defined below
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
                u"message was added automatically by __botnick__, if you need "
                u"some help about it please read the text above again and "
                u"follow the links in it, if you still need help ask at the "
                u"[[File:Human-help-browser.svg|18px|link=Commons:Help desk|?]]"
                u" '''[[Commons:Help desk|→]] [[Commons:Help desk]]''' in any "
                u"language you like to use.'' --__botnick__ ~~~~~"),
    'it': u"{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/Template_insufficiente|%s|__botnick__}} --~~~~",
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
    'it': u'\n\n== File doppio ==\n',
}

# Message to put in the talk
duplicates_user_talk_text = {
    'commons': u'{{subst:User:Filnik/duplicates|File:%s|File:%s}}',  # FIXME: it doesn't exist
    'it': u"{{subst:Progetto:Coordinamento/Immagini/Bot/Messaggi/Duplicati|%s|%s|__botnick__}} --~~~~",
}

# Comment used by the bot while it reports the problem in the uploader's talk
duplicates_comment_talk = {
    'commons': u'Bot: Dupe file found',
    'ar': u'بوت: ملف مكرر تم العثور عليه',
    'fa': u'ربات: تصویر تکراری یافت شد',
    'it': u"Bot: Notifico il file doppio trovato",
}

# Comment used by the bot while it reports the problem in the image
duplicates_comment_image = {
    'commons': u'Bot: Tagging dupe file',
    'de': u'Bot: Datei liegt auf Commons',
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
    'ar': u'تصنيف:قوالب حقوق الصور',
    'de': u'Kategorie:Vorlage:Lizenz für Bilder',
    'en': u'Category:Wikipedia image copyright templates',
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
                 r'\|[Ss]ource=Transferred from .*?; transferred to Commons by \[\[User:(.*?)\]\]']],
}

# Service images that don't have to be deleted and/or reported has a template
# inside them (you can let this param as None)
serviceTemplates = {
    'it': ['Template:Immagine di servizio'],
}

# Add your project (in alphabetical order) if you want that the bot starts
project_inserted = ['ar', 'commons', 'de', 'en', 'fa', 'ga', 'hu', 'it', 'ja',
                    'ko', 'ta', 'ur', 'zh']

# END OF CONFIGURATION.


class LogIsFull(pywikibot.Error):

    """Log is full and the Bot cannot add other data to prevent Errors."""


class NothingFound(pywikibot.Error):

    """Regex returned [] instead of results."""


def printWithTimeZone(message):
    """Print the messages followed by the TimeZone encoded correctly."""
    if message[-1] != ' ':
        message = '%s ' % unicode(message)
    if locale.getlocale()[1]:
        time_zone = unicode(time.strftime(u"%d %b %Y %H:%M:%S (UTC)",
                                          time.gmtime()),
                            locale.getlocale()[1])
    else:
        time_zone = unicode(time.strftime(u"%d %b %Y %H:%M:%S (UTC)",
                                          time.gmtime()))
    pywikibot.output(u"%s%s" % (message, time_zone))


class checkImagesBot(object):

    """A robot to check recently uploaded files."""

    def __init__(self, site, logFulNumber=25000, sendemailActive=False,
                 duplicatesReport=False, logFullError=True):
        """Constructor, define some global variable."""
        self.site = site
        self.logFullError = logFullError
        self.logFulNumber = logFulNumber
        self.rep_page = i18n.translate(self.site, report_page)
        self.rep_text = i18n.translate(self.site, report_text)
        self.com = i18n.translate(self.site, msg_comm10)
        hiddentemplatesRaw = i18n.translate(self.site, HiddenTemplate)
        self.hiddentemplates = set([pywikibot.Page(self.site, tmp)
                                    for tmp in hiddentemplatesRaw])
        self.pageHidden = i18n.translate(self.site,
                                              PageWithHiddenTemplates)
        self.pageAllowed = i18n.translate(self.site,
                                               PageWithAllowedTemplates)
        self.comment = i18n.translate(self.site, msg_comm, fallback=True)
        # Adding the bot's nickname at the notification text if needed.
        botolist = i18n.translate(self.site, bot_list)
        project = pywikibot.Site().family.name
        self.project = project
        bot = config.usernames[project]
        try:
            botnick = bot[self.site.code]
        except KeyError:
            raise pywikibot.NoUsername(
                u"You have to specify an username for your bot in this project "
                u"in the user-config.py file.")

        self.botnick = botnick
        botolist.append(botnick)
        self.botolist = botolist

        self.sendemailActive = sendemailActive
        self.skip_list = []
        self.duplicatesReport = duplicatesReport

        self.image_namespace = u"File:"
        # Load the licenses only once, so do it once
        self.list_licenses = self.load_licenses()

    def setParameters(self, imageName):
        """
        Set parameters.

        Now only image but maybe it can be used for others in "future".
        """
        self.imageName = imageName
        self.image = pywikibot.FilePage(self.site, self.imageName)
        self.timestamp = None
        self.uploader = None

    def report(self, newtext, image_to_report, notification=None, head=None,
               notification2=None, unver=True, commTalk=None, commImage=None):
        """ Function to make the reports easier. """
        self.image_to_report = image_to_report
        self.newtext = newtext
        self.head = head or u''
        self.notification = notification
        self.notification2 = notification2

        if self.notification:
            self.notification = re.sub(r'__botnick__', self.botnick,
                                       notification)
        if self.notification2:
            self.notification2 = re.sub(r'__botnick__', self.botnick,
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
                                     comment=self.commImage)
            except pywikibot.LockedPage:
                pywikibot.output(u'File is locked. Skipping.')
                return
        # paginetta it's the image page object.
        try:
            if reportPageObject == self.image and self.uploader:
                nick = self.uploader
            else:
                nick = reportPageObject.getLatestUploader()[0]
        except pywikibot.NoPage:
            pywikibot.output(
                u"Seems that %s has only the description and not the file..."
                % self.image_to_report)
            repme = u"\n*[[:File:%s]] problems '''with the APIs'''"
            self.report_image(self.image_to_report, self.rep_page, self.com,
                              repme)
            return
        upBots = i18n.translate(self.site, uploadBots)
        luser = pywikibot.url2link(nick, self.site, self.site)

        if upBots:
            for upBot in upBots:
                if upBot[0] == luser:
                    luser = self.uploadBotChangeFunction(reportPageText, upBot)
        talk_page = pywikibot.Page(self.site,
                                   u"%s:%s" % (self.site.namespace(3), luser))
        self.talk_page = talk_page
        self.luser = luser
        return True

    def put_mex_in_talk(self):
        """ Function to put the warning in talk page of the uploader."""
        commento2 = i18n.translate(self.site, msg_comm2, fallback=True)
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
            for i in self.botolist:
                if latest_user == i:
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
            newText = testoattuale + self.head + self.notification

        try:
            self.talk_page.put(newText, comment=commentox, minorEdit=False)
        except pywikibot.LockedPage:
            pywikibot.output(u'Talk page blocked, skip.')

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
                    emailClass.sendMail(emailSubj, text_to_send)
                except pywikibot.UserActionRefuse:
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
        return self.hiddentemplates

    def returnOlderTime(self, listGiven, timeListGiven):
        """Get some time and return the oldest of them."""
        num = 0
        num_older = None
        max_usage = 0
        for element in listGiven:
            imageName = element[1]
            imagePage = pywikibot.FilePage(self.site, imageName)
            imageUsage = [page for page in imagePage.usingPages()]
            if len(imageUsage) > 0 and len(imageUsage) > max_usage:
                max_usage = len(imageUsage)
                num_older = num
            num += 1

        if num_older:
            return listGiven[num_older][1]

        for element in listGiven:
            time = element[0]
            imageName = element[1]
            not_the_oldest = False

            for time_selected in timeListGiven:
                if time > time_selected:
                    not_the_oldest = True
                    break

            if not not_the_oldest:
                return imageName

    def convert_to_url(self, page):
        """Return the page title suitable as for an URL."""
        return page.title(asUrl=True)

    def countEdits(self, pagename, userlist):
        """Function to count the edit of a user or a list of users in a page."""
        # self.botolist
        if isinstance(userlist, basestring):
            userlist = [userlist]
        page = pywikibot.Page(self.site, pagename)
        history = page.getVersionHistory()
        user_list = list()

        for data in history:
            user_list.append(data.user)
        number_edits = 0

        for username in userlist:
            number_edits += user_list.count(username)
        return number_edits

    def checkImageOnCommons(self):
        """Checking if the file is on commons."""
        pywikibot.output(u'Checking if [[%s]] is on commons...'
                         % self.imageName)
        commons_site = pywikibot.Site('commons', 'commons')
        regexOnCommons = r"\[\[:File:%s\]\] is also on '''Commons''': \[\[commons:File:.*?\]\](?: \(same name\)|)$" \
                         % re.escape(self.imageName)
        hash_found = self.image.getFileSHA1Sum()
        if not hash_found:
            return  # Image deleted, no hash found. Skip the image.

        commons_image_with_this_hash = commons_site.getFilesFromAnHash(
            hash_found)
        if commons_image_with_this_hash and \
           commons_image_with_this_hash is not 'None':
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
            on_commons_text = self.image.getImagePageHtml()
            if re.search(r"\<div class\=(?:'|\")sharedUploadNotice(?:'|\")\>",
                         on_commons_text):
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
            if self.convert_to_url(self.imageName) \
               == self.convert_to_url(commons_image_with_this_hash[0]):
                repme = u"\n*[[:File:%s]] is also on '''Commons''': [[commons:File:%s]] (same name)" \
                        % (self.imageName, commons_image_with_this_hash[0])
            else:
                repme = u"\n*[[:File:%s]] is also on '''Commons''': [[commons:File:%s]]" \
                        % (self.imageName, commons_image_with_this_hash[0])
            self.report_image(self.imageName, self.rep_page, self.com, repme,
                              addings=False, regex=regexOnCommons)
        return True

    def checkImageDuplicated(self, duplicates_rollback):
        """ Function to check the duplicated files. """
        dupText = i18n.translate(self.site, duplicatesText)
        dupRegex = i18n.translate(self.site, duplicatesRegex)
        dupTalkHead = i18n.translate(self.site, duplicate_user_talk_head)
        dupTalkText = i18n.translate(self.site, duplicates_user_talk_text)
        dupComment_talk = i18n.translate(self.site,
                                              duplicates_comment_talk)
        dupComment_image = i18n.translate(self.site,
                                               duplicates_comment_image)
        duplicateRegex = r'\[\[:File:%s\]\] has the following duplicates' \
                         % re.escape(self.convert_to_url(self.imageName))
        imagePage = pywikibot.FilePage(self.site, self.imageName)
        hash_found = imagePage.getFileSHA1Sum()
        duplicates = self.site.getFilesFromAnHash(hash_found)

        if not duplicates:
            return  # Error, image deleted, no hash found. Skip the image.

        if len(duplicates) > 1:
            if len(duplicates) == 2:
                pywikibot.output(u'%s has a duplicate! Reporting it...'
                                 % self.imageName)
            else:
                pywikibot.output(u'%s has %s duplicates! Reporting them...'
                                 % (self.imageName, len(duplicates) - 1))

            if dupText and dupRegex:
                time_image_list = []
                time_list = []

                for duplicate in duplicates:
                    DupePage = pywikibot.FilePage(self.site, duplicate)

                    if DupePage.title(asUrl=True) != self.image.title(asUrl=True) or \
                       self.timestamp is None:
                        self.timestamp = DupePage.getLatestUploader()[1]
                    data = time.strptime(self.timestamp, u"%Y-%m-%dT%H:%M:%SZ")
                    data_seconds = time.mktime(data)
                    time_image_list.append([data_seconds, duplicate])
                    time_list.append(data_seconds)
                older_image = self.returnOlderTime(time_image_list, time_list)
                # And if the images are more than two?
                Page_oder_image = pywikibot.FilePage(self.site, older_image)
                string = ''
                images_to_tag_list = []

                for duplicate in duplicates:
                    if pywikibot.FilePage(self.site, duplicate) \
                       == pywikibot.FilePage(self.site, older_image):
                        # the older image, not report also this as duplicate
                        continue
                    DupePage = pywikibot.FilePage(self.site, duplicate)
                    try:
                        DupPageText = DupePage.get()
                        older_page_text = Page_oder_image.get()
                    except pywikibot.NoPage:
                        continue  # The page doesn't exists

                    if not (re.findall(dupRegex, DupPageText) or
                            re.findall(dupRegex, older_page_text)):
                        pywikibot.output(
                            u'%s is a duplicate and has to be tagged...'
                            % duplicate)
                        images_to_tag_list.append(duplicate)
                        string += u"*[[:%s%s]]\n" % (self.image_namespace,
                                                     duplicate)
                    else:
                        pywikibot.output(
                            u"Already put the dupe-template in the files's page"
                            u" or in the dupe's page. Skip.")
                        return  # Ok - Let's continue the checking phase

                older_image_ns = u'%s%s' % (self.image_namespace, older_image)

                # true if the image are not to be tagged as dupes
                only_report = False

                # put only one image or the whole list according to the request
                if u'__images__' in dupText:
                    text_for_the_report = re.sub(r'__images__',
                                                 r'\n%s*[[:%s]]\n'
                                                 % (string, older_image_ns),
                                                 dupText)
                else:
                    text_for_the_report = re.sub(r'__image__',
                                                 r'%s' % older_image_ns,
                                                 dupText)

                # Two iteration: report the "problem" to the user only once
                # (the last)
                if len(images_to_tag_list) > 1:
                    for image_to_tag in images_to_tag_list[:-1]:
                        already_reported_in_past = self.countEdits(
                            u'File:%s' % image_to_tag, self.botolist)
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
                    already_reported_in_past = self.countEdits(
                        u'File:%s' % images_to_tag_list[-1], self.botolist)
                    from_regex = r'\n\*\[\[:File:%s\]\]' \
                                 % re.escape(self.convert_to_url(
                                     self.imageName))
                    # Delete the image in the list where we're write on
                    text_for_the_report = re.sub(from_regex, '',
                                                 text_for_the_report)
                    # if you want only one edit, the edit found should be more
                    # than 0 -> num - 1
                    if already_reported_in_past > duplicates_rollback - 1:
                        only_report = True
                    else:
                        self.report(text_for_the_report, images_to_tag_list[-1],
                                    dupTalkText % (older_image_ns, string),
                                    dupTalkHead, commTalk=dupComment_talk,
                                    commImage=dupComment_image, unver=True)

            if self.duplicatesReport or only_report:
                if only_report:
                    repme = u"\n*[[:File:%s]] has the following duplicates ('''forced mode'''):" \
                            % self.convert_to_url(self.imageName)
                else:
                    repme = u"\n*[[:File:%s]] has the following duplicates:" \
                            % self.convert_to_url(self.imageName)

                for duplicate in duplicates:
                    if self.convert_to_url(duplicate) == \
                       self.convert_to_url(self.imageName):
                        # the image itself, not report also this as duplicate
                        continue
                    repme += u"\n**[[:File:%s]]" \
                             % self.convert_to_url(duplicate)

                result = self.report_image(self.imageName, self.rep_page,
                                           self.com, repme, addings=False,
                                           regex=duplicateRegex)
                if not result:
                    return True  # If Errors, exit (but continue the check)

            if older_image != self.imageName:
                # The image is a duplicate, it will be deleted. So skip the
                # check-part, useless
                return
        return True  # Ok - No problem. Let's continue the checking phase

    def report_image(self, image_to_report, rep_page=None, com=None,
                     rep_text=None, addings=True, regex=None):
        """ Report the files to the report page when needed. """
        if not rep_page:
            rep_page = self.rep_page

        if not com:
            com = self.com

        if not rep_text:
            rep_text = self.rep_text

        another_page = pywikibot.Page(self.site, rep_page)

        if not regex:
            regex = image_to_report
        try:
            text_get = another_page.get()
        except pywikibot.NoPage:
            text_get = ''
        except pywikibot.IsRedirectPage:
            text_get = another_page.getRedirectTarget().get()

        if len(text_get) >= self.logFulNumber:
            if self.logFullError:
                raise LogIsFull(
                    u"The log page (%s) is full! Please delete the old files "
                    u"reported." % another_page.title())
            else:
                pywikibot.output(
                    u"The log page (%s) is full! Please delete the old files "
                    u" reported. Skip!" % another_page.title())
                # Don't report, but continue with the check
                # (we don't now if this is the first time we check this file
                # or not)
                return True

        # The talk page includes "_" between the two names, in this way I
        # replace them to " "
        n = re.compile(regex, re.UNICODE | re.DOTALL)
        y = n.findall(text_get)

        if y:
            pywikibot.output(u"%s is already in the report page."
                             % image_to_report)
            reported = False
        else:
            # Adding the log
            if addings:
                # Adding the name of the image in the report if not done already
                rep_text = rep_text % image_to_report
            another_page.put(text_get + rep_text, comment=com, force=True,
                             minorEdit=False)
            pywikibot.output(u"...Reported...")
            reported = True
        return reported

    def takesettings(self):
        """ Function to take the settings from the wiki. """
        settingsPage = i18n.translate(self.site, page_with_settings)
        try:
            if not settingsPage:
                self.settingsData = None
            else:
                wikiPage = pywikibot.Page(self.site, settingsPage)
                self.settingsData = list()
                try:
                    testo = wikiPage.get()
                    r = re.compile(
                        r"<------- ------->\n"
                        "\*[Nn]ame ?= ?['\"](.*?)['\"]\n"
                        "\*([Ff]ind|[Ff]indonly)=(.*?)\n"
                        "\*[Ii]magechanges=(.*?)\n"
                        "\*[Ss]ummary=['\"](.*?)['\"]\n"
                        "\*[Hh]ead=['\"](.*?)['\"]\n"
                        "\*[Tt]ext ?= ?['\"](.*?)['\"]\n"
                        "\*[Mm]ex ?= ?['\"]?([^\n]*?)['\"]?\n",
                        re.UNICODE | re.DOTALL)
                    number = 1

                    for m in r.finditer(testo):
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

                    if self.settingsData == list():
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
        return self.settingsData  # Useless, but it doesn't harm..

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
                try:
                    template.pageAPInfo()
                except pywikibot.IsRedirectPage:
                    template = template.getRedirectTarget()
                    result = self.miniTemplateCheck(template)
                    if result:
                        break
                except pywikibot.NoPage:
                    continue

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
            self.hiddentemplates = self.loadHiddenTemplates()
            self.licenses_found = self.image.templates()
            templatesInTheImageRaw = regex_find_licenses.findall(
                self.imageCheckText)

            if not self.licenses_found and templatesInTheImageRaw:
                # {{nameTemplate|something <- this is not a template, be sure
                # that we haven't catch something like that.
                licenses_TEST = regex_are_licenses.findall(self.imageCheckText)
                if not self.licenses_found and licenses_TEST:
                    raise pywikibot.Error(
                        "APIs seems down. No templates found with them but "
                        "actually there are templates used in the image's "
                        "page!")
            self.allLicenses = []

            if not self.list_licenses:
                raise pywikibot.Error(
                    u'No licenses allowed provided, add that option to the '
                    u'code to make the script working correctly')

            # Found the templates ONLY in the image's description
            for template_selected in templatesInTheImageRaw:
                for templateReal in self.licenses_found:
                    if self.convert_to_url(
                        template_selected).lower().replace('template%3a', '') \
                        == self.convert_to_url(
                            templateReal.title()).lower().replace('template%3a',
                                                                  ''):
                        if templateReal not in self.allLicenses:
                            self.allLicenses.append(templateReal)
            break

        if self.licenses_found:
            self.templateInList()

            if not self.license_found and self.allLicenses:
                # If only iterlist = self.AllLicenses if I remove something
                # from iterlist it will be remove from self.AllLicenses too
                iterlist = list(self.allLicenses)

                for template in iterlist:
                    try:
                        template.pageAPInfo()
                    except pywikibot.IsRedirectPage:
                        template = template.getRedirectTarget()
                    except pywikibot.NoPage:
                        self.allLicenses.remove(template)

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
                                u"\n%s\n" % self.head_used, None,
                                self.imagestatus_used, self.summary_used)
                else:
                    pywikibot.output(u"Skipping the file...")
                self.some_problem = False
        else:
            if not self.seems_ok and self.license_found:
                rep_text_license_fake = u"\n*[[:File:%s]] seems to have " \
                                        % self.imageName + \
                    "a ''fake license'', license detected: <nowiki>%s</nowiki>" \
                                        % self.license_found
                regexFakeLicense = r"\* ?\[\[:File:%s\]\] seems to have " \
                                   % (re.escape(self.imageName)) + \
                    "a ''fake license'', license detected: <nowiki>%s</nowiki>$" \
                                   % (re.escape(self.license_found))
                printWithTimeZone(
                    u"%s seems to have a fake license: %s, reporting..."
                    % (self.imageName, self.license_found))
                self.report_image(self.imageName,
                                  rep_text=rep_text_license_fake,
                                  addings=False, regex=regexFakeLicense)
            elif self.license_found:
                pywikibot.output(u"[[%s]] seems ok, license found: {{%s}}..."
                                 % (self.imageName, self.license_found))
        return (self.license_found, self.whiteTemplatesFound)

    def load(self, raw):
        """ Load a list of objects from a string using regex. """
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
        """ Given a number of files, skip the first -number- files. """
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

    def wait(self, waitTime, generator, normal, limit):
        """
        Skip the images uploaded before x seconds.

        Let the users to fix the image's problem alone in the first x seconds.
        """
        imagesToSkip = 0
        # if normal, we can take as many images as "limit" has told us,
        # otherwise, sorry, nope.
        # TODO: remove this exception as part of bug 65136
        raise NotImplementedError(
            "The wait option is not available at core yet.")

        if normal:
            printWithTimeZone(
                u'Skipping the files uploaded less than %s seconds ago..'
                % waitTime)
            imagesToSkip = 0
            while True:
                # ensure that all the images loaded aren't to skip!
                loadOtherImages = True
                for image in generator:
                    try:
                        timestamp = image.getLatestUploader()[1]
                    except pywikibot.NoPage:
                        continue
                    # not relative to localtime
                    img_time = datetime.datetime.strptime(timestamp,
                                                          u"%Y-%m-%dT%H:%M:%SZ")

                    now = datetime.datetime.strptime(
                        str(datetime.datetime.utcnow()).split('.')[0],
                        "%Y-%m-%d %H:%M:%S")  # timezones are UTC
                    # + seconds to be sure that now > img_time
                    while now < img_time:
                        now = (now + datetime.timedelta(seconds=1))
                    delta = now - img_time
                    secs_of_diff = delta.seconds
                    if waitTime > secs_of_diff:
                        pywikibot.output(
                            u'Skipping %s, uploaded %s seconds ago..'
                            % (image.title(), int(secs_of_diff)))
                        imagesToSkip += 1
                        continue  # Still wait
                    else:
                        loadOtherImages = False
                        break  # Not ok, continue
                # if yes, we have skipped all the images given!
                if loadOtherImages:
                    generator = (x[0] for x in
                                 self.site.newimages(number=limit,
                                                     lestart=timestamp))
                    imagesToSkip = 0
                    # continue to load images!
                    continue
                else:
                    break  # ok some other images, go below
            newGen = list()
            imagesToSkip += 1  # some calcs, better add 1
            # Add new images, instead of the images skipped
            newImages = self.site.newimages(number=imagesToSkip,
                                            lestart=timestamp)
            for image in generator:
                newGen.append(image)
            for imageData in newImages:
                newGen.append(imageData[0])
            return newGen
        else:
            pywikibot.output(
                u"The wait option is available only with the standard "
                u"generator.")
            return generator

    def isTagged(self):
        """ Understand if a file is already tagged or not. """
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
        # nothing = Defining an empty image description
        nothing = ['', ' ', '  ', '   ', '\n', '\n ', '\n  ', '\n\n', '\n \n',
                   ' \n', ' \n ', ' \n \n']
        # something = Minimal requirements for an image description.
        # If this fits, no tagging will take place
        # (if there aren't other issues)
        # MIT license is ok on italian wikipedia, let also this here

        # Don't put "}}" here, please. Useless and can give problems.
        something = ['{{']
        # Unused file extensions. Does not contain PDF.
        notallowed = ("xcf", "xls", "sxw", "sxi", "sxc", "sxd")
        brackets = False
        delete = False
        notification = None
        # get the extension from the image's name
        extension = self.imageName.split('.')[-1]
        # Load the notification messages
        HiddenTN = i18n.translate(self.site, HiddenTemplateNotification)
        self.unvertext = i18n.translate(self.site, n_txt)
        di = i18n.translate(self.site, delete_immediately)
        dih = i18n.translate(self.site, delete_immediately_head)
        din = i18n.translate(self.site, delete_immediately_notification)
        nh = i18n.translate(self.site, nothing_head)
        nn = i18n.translate(self.site, nothing_notification)
        dels = i18n.translate(self.site, msg_del_comm, fallback=True)
        smwl = i18n.translate(self.site, second_message_without_license)

        # Some formatting for delete immediately template
        di = u'\n%s' % di
        dels = dels % di

        try:
            self.imageCheckText = self.image.get()
        except pywikibot.NoPage:
            pywikibot.output(u"Skipping %s because it has been deleted."
                             % self.imageName)
            return True
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"Skipping %s because it's a redirect."
                             % self.imageName)
            return True
        # Delete the fields where the templates cannot be loaded
        regex_nowiki = re.compile(r'<nowiki>(.*?)</nowiki>', re.DOTALL)
        regex_pre = re.compile(r'<pre>(.*?)</pre>', re.DOTALL)
        self.imageCheckText = regex_nowiki.sub('', self.imageCheckText)
        self.imageCheckText = regex_pre.sub('', self.imageCheckText)
        # Deleting the useless template from the description (before adding sth
        # in the image the original text will be reloaded, don't worry).
        if self.isTagged():
            printWithTimeZone(u'%s is already tagged...' % self.imageName)
            return True

        # something is the array with {{, MIT License and so on.
        for a_word in something:
            if a_word in self.imageCheckText:
                # There's a template, probably a license
                brackets = True
        # Is the extension allowed? (is it an image or f.e. a .xls file?)
        for parl in notallowed:
            if parl.lower() in extension.lower():
                delete = True
        (license_found, hiddenTemplateFound) = self.smartDetection()
        # Here begins the check block.
        if brackets and license_found:
            # It works also without this... but i want only to be sure ^^
            brackets = False
            return True
        elif delete:
            pywikibot.output(u"%s is not a file!" % self.imageName)
            # Modify summary text
            pywikibot.setAction(dels)
            canctext = di % extension
            notification = din % self.imageName
            head = dih
            self.report(canctext, self.imageName, notification, head)
            delete = False
            return True
        elif self.imageCheckText in nothing:
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
            return True
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
            return True


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
    sendemailActive = False  # Use the send-email
    logFullError = True  # Raise an error when the log is full
    generator = None

    # Here below there are the parameters.
    for arg in pywikibot.handle_args(args):
        if arg.startswith('-limit'):
            if len(arg) == 7:
                limit = int(pywikibot.input(
                    u'How many files do you want to check?'))
            else:
                limit = int(arg[7:])
        if arg.startswith('-time'):
            if len(arg) == 5:
                time_sleep = int(pywikibot.input(
                    u'How many seconds do you want runs to be apart?'))
            else:
                time_sleep = int(arg[6:])
        elif arg == '-break':
            repeat = False
        elif arg == '-nologerror':
            logFullError = False
        elif arg == '-commons':
            commonsActive = True
        elif arg.startswith('-duplicates'):
            duplicatesActive = True
            if len(arg) == 11:
                duplicates_rollback = 1
            elif len(arg) > 11:
                duplicates_rollback = int(arg[12:])
        elif arg == '-duplicatereport':
            duplicatesReport = True
        elif arg == '-sendemail':
            sendemailActive = True
        elif arg.startswith('-skip'):
            if len(arg) == 5:
                skip_number = int(pywikibot.input(
                    u'How many files do you want to skip?'))
            elif len(arg) > 5:
                skip_number = int(arg[6:])
        elif arg.startswith('-wait'):
            # FIXME: bug 65136
            raise NotImplementedError(
                "-wait option is not available at core yet. Sorry!")
            if len(arg) == 5:
                waitTime = int(pywikibot.input(
                    u'How many time do you want to wait before checking the '
                    u'files?'))
            elif len(arg) > 5:
                waitTime = int(arg[6:])
        elif arg.startswith('-start'):
            if len(arg) == 6:
                firstPageTitle = pywikibot.input(
                    u'From witch page do you want to start?')
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
            generator = pg.CategorizedPageGenerator(catSelected)
            repeat = False
        elif arg.startswith('-ref'):
            if len(arg) == 4:
                refName = str(pywikibot.input(
                    u'The references of what page should I parse?'))
            elif len(arg) > 4:
                refName = str(arg[5:])
            generator = pg.ReferringPageGenerator(
                pywikibot.Page(pywikibot.Site(), refName))
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
        return

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
                             logFullError=logFullError)
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
        if waitTime:
            generator = Bot.wait(waitTime, generator, normal, limit)
        generator = pg.NamespaceFilterPageGenerator(generator, 6, site)
        for image in generator:
            # Setting the image for the main class
            Bot.setParameters(image.title(withNamespace=False))
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
            if Bot.checkStep():
                continue

        if repeat:
            pywikibot.output(u"Waiting for %s seconds," % time_sleep)
            time.sleep(time_sleep)
        else:
            break


if __name__ == "__main__":
    start = time.time()
    try:
        main()
    except SystemExit:
        pass
    else:
        final = time.time()
        delta = int(final - start)
        pywikibot.output("Execution time: %s seconds\n" % delta)
