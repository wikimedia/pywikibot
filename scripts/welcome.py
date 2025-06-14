#!/usr/bin/env python3
"""Script to welcome new users.

This script works out of the box for Wikis that have been defined in the
script.

.. important::
   Ensure you have community support before running this bot!

Everything that needs customisation to support additional projects is
indicated by comments.

**Description of basic functionality**

* Request a list of new users every period (default: 3600 seconds). You
  can choose to break the script after the first check (see arguments)
* Check if new user has passed a threshold for a number of edits
  (default: 1 edit)
* Optional: check username for bad words in the username or if the
  username consists solely of numbers; log this somewhere on the wiki
  (default: False). A whitelist is also implemented (explanation below).
* If user has made enough edits (it can be also 0), check if user has an
  empty talk page
* If user has an empty talk page, add a welcome message.
* Optional: Once the set number of users have been welcomed, add this to
  the configured log page, one for each day (default: True)
* If no log page exists, create a header for the log page first.

This script uses two templates that need to be on the local wiki:

.. role:: tmpl(code)
   :language: wikitext

* :tmpl:`{{WLE}}`: contains mark up code for log entries (just copy it
  from Commons)
* :tmpl:`{{welcome}}`: contains the information for new users

This script understands the following command-line arguments:

-edit[:#]        [int] Define how many edits a new user needs to be
                 welcomed (default: 1, max: 50)

-time[:#]        Define how many seconds the bot sleeps before restart
                 (default: 3600)

-break           Use it if you don't want that the Bot restart at the
                 end (it will break) (default: False)

-nlog            Use this parameter if you do not want the bot to log
                 all welcomed users (default: False)

-limit[:#]       [int] Use this parameter to define how may users should
                 be checked (default:50)

-offset[:TIME]   Skip the latest new users (those newer than TIME) to
                 give interactive users a chance to welcome the new
                 users (default: now) Timezone is the server timezone,
                 GMT for Wikimedia TIME format : yyyymmddhhmmss or yyyymmdd

-timeoffset[:#]  Skip the latest new users, accounts newer than #
                 minutes

-numberlog[:#]   The number of users to welcome before refreshing the
                 welcome log (default: 4)

-filter          Enable the username checks for bad names (default:
                 False)

-ask             Use this parameter if you want to confirm each possible
                 bad username (default: False)

-random          Use a random signature, taking the signatures from a
                 wiki page (for instruction, see below).

-file[:#]        Use a file instead of a wikipage to take the random
                 sign. If you use this parameter, you don't need to use
                 ``-random``.

-sign            Use one signature from command line instead of the
                 default

-savedata        This feature saves the random signature index to allow
                 to continue to welcome with the last signature used.

-sul             Welcome the auto-created users (default: False)

-quiet           Prevents users without contributions are displayed

GUIDE
-----

**Report, Bad and white list guide**

1) Set in the code which page it will use to load the badword, the
   whitelist and the report.

2) In these page you have to add a "tuple" with the names that you want
   to add in the two list. For example: ('cat', 'mouse', 'dog') You can
   write also other text in the page, it will work without problem.

3) What will do the two pages? Well, the Bot will check if a badword is
   in the username and set the "warning" as True. Then the Bot check if
   a word of the whitelist is in the username. If yes it remove the word
   and recheck in the bad word list to see if there are other badword in
   the username.

   Example:

   * dio is a badword
   * Claudio is a normal name
   * The username is "Claudio90 fuck!"
   * The Bot finds dio and sets "warning"
   * The Bot finds Claudio and sets "ok"
   * The Bot finds fuck at the end and sets "warning"
   * Result: The username is reported.

4) When a user is reported you have to check him and do

   * If he's ok, put the :tmpl:`{{welcome}}`
   * If he's not, block him
   * You can decide to put a "you are blocked, change another username"
     template or not.
   * Delete the username from the page.

   .. important::

      The Bot check the user in this order

      * Search if he has a talkpage (if yes, skip)
      * Search if he's blocked, if yes he will be skipped
      * Search if he's in the report page, if yes he will be skipped
      * If no, he will be reported.

**Random signature guide**

Some welcomed users will answer to the one who has signed the welcome
message. When you welcome many new users, you might be overwhelmed with
such answers. Therefore you can define usernames of other users who are
willing to receive some of these messages from newbies.

1) Set the page that the bot will load
2) Add the signature lines in this way:

    * SIGNATURE

   Example of signatures:

   .. code:: wikitext

      <pre>
      * [[User:Filnik|Filnik]]
      * [[User:Rock|Rock]]
      </pre>

   .. note:: The white space after asterisk and ``<pre></pre>`` aren't
      required but it is recommended you to use them.

Badwords
--------

The list of Badwords of the code is opened. If you think that a word is
international and it must be blocked in all the projects feel free to
add it. If also you think that a word isn't so international, feel free
to delete it.

However, there is a dynamic-wikipage to load that badwords of your
project or you can add them directly in the source code that you are
using without adding or deleting.

Some words, like "Administrator" or "Dio" (God in italian) or "Jimbo"
aren't badwords at all but can be used for some bad-nickname.
"""
#
# (C) Pywikibot team, 2006-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import locale
import pickle
import re
import time
from contextlib import suppress
from datetime import timedelta
from enum import Enum
from random import choice
from textwrap import fill

import pywikibot
from pywikibot import config, i18n
from pywikibot.backports import Generator  # skipcq: PY-W2000
from pywikibot.bot import SingleSiteBot
from pywikibot.exceptions import EditConflictError, Error, HiddenKeyError


locale.setlocale(locale.LC_ALL, '')

# Script uses the method i18n.translate() to find the right
# page/user/summary/etc so the need to specify language and project have
# been eliminated.
# FIXME: Not all language/project combinations have been defined yet.
#        Add the following strings to customise for a language:
#        LOGBOOK, WELCOME, REPORT_PAGE, BAD_PAGE, REPORT_TEXT, RANDOM_SIGN,
#        WHITELIST, FINAL_NEW_TEXT_ADDITIONS, LOGPAGE_HEADER if
#        different from Wikipedia entry

############################################################################

# The page where the bot will save the log (e.g. Wikipedia:Welcome log).
#
# ATTENTION: Projects not listed won't write a log to the wiki.
LOGBOOK = {
    'ar': 'Project:سجل الترحيب',
    'ckb': 'Project:لۆگی بەخێرھاتن',
    'fr': ('Wikipedia:Prise de décision/'
           'Accueil automatique des nouveaux par un robot/log'),
    'ga': 'Project:Log fáilte',
    'ja': '利用者:Alexbot/Welcomebotログ',
    'nl': 'Project:Logboek welkom',
    'no': 'Project:Velkomstlogg',
    'sd': 'Project:ڀليڪار دوڳي',
    'sq': 'Project:Tung log',
    'ur': 'Project:نوشتہ خوش آمدید',
    'zh': 'User:Welcomebot/欢迎日志',
    'commons': 'Project:Welcome log',
}
# The text for the welcome message (e.g. {{welcome}}) and %s at the end
# that is your signature (the bot has a random parameter to add different
# sign, so in this way it will change according to your parameters).
WELCOME = {
    'commons': '{{subst:welcome}} %s',
    'meta': '{{subst:Welcome}} %s',
    'wikipedia': {
        'am': '{{subst:Welcome}} %s',
        'ar': '{{subst:أهلا ومرحبا}} %s',
        'ary': '{{subst:ترحيب جديد}} %s',
        'arz': '{{subst:اهلا و سهلا}} %s',
        'as': '{{subst:আদৰণি}} %s',
        'ba': '{{Hello}} %s',
        'bn': '{{subst:স্বাগতম/বট}} %s',
        'bs': '{{Dobrodošlica}} %s',
        'ckb': '{{subst:بەخێرھاتن}} %s',
        'da': '{{velkommen|%s}}',
        'de': '{{subst:willkommen}} %s',
        'en': '{{subst:welcome}} %s',
        'fa': '{{subst:خوشامدید|%s}}',
        'fr': '{{Bienvenue nouveau}} %s',
        'ga': '{{subst:fáilte}} %s',
        'gom': '{{subst:welcome}} %s',
        'gor': '{{subst:Welcome}} %s',
        'he': '{{ס:ברוך הבא}} %s',
        'hr': '{{subst:dd}} %s',
        'hu': '{{subst:Üdvözlet|%s}}\n',
        'id': '{{subst:sdbot2}}\n%s',
        'it': '<!-- inizio template di benvenuto -->\n{{subst:Benvebot}}\n%s'
              '<!-- fine template di benvenuto -->',
        'ja': '{{subst:Welcome/intro}}\n{{subst:welcome|%s}}',
        'ka': '{{ახალი მომხმარებელი}}--%s',
        'kn': '{{subst:ಸುಸ್ವಾಗತ}} %s',
        'ko': '{{환영}}--%s\n',
        'ml': '{{ബദൽ:സ്വാഗതം/bot}} %s',
        'my': '{{subst:welcome}} %s',
        'nap': '{{Bemmenuto}}%s',
        'nl': '{{hola|bot|%s}}',
        'no': '{{subst:bruker:jhs/vk}} %s',
        'pdc': '{{subst:Wilkum}}%s',
        'pnb': '{{subst:جی آیاں نوں}} %s',
        'pt': '{{subst:bem vindo}} %s',
        'roa-tara': '{{Bovègne}} %s',
        'ru': '{{subst:Приветствие}}\n%s\n',
        'sd': '{{subst:ڀليڪار}}\n%s\n',
        'shn': '{{subst:ႁပ်ႉတွၼ်ႈၽူႈၸႂ်ႉတိုဝ်း}} %s',
        'skr': '{{subst:ست بسم اللہ}} %s',
        'sq': '{{subst:tung}} %s',
        'sr': '{{dd}}--%s\n',
        'ta': '{{welcome}}\n%s\n',
        'ur': '{{نقل:خوش آمدید}}%s',
        'vec': '{{subst:Benvegnù|%s}}',
        'vo': '{{benokömö}} %s',
        'zh': '{{subst:welcome|sign=%s}}',
        'zh-yue': '{{歡迎}}--%s',
    },
    'wikibooks': {
        'es': '{{subst:bienivenido usuario}} %s',
        'ml': '{{subst:സ്വാഗതം}}',
    },
    'wikinews': {
        'fa': '{{خوشامد۲|%s}}',
        'it': '{{subst:benvenuto}}',
        'zh': '{{subst:welcome}} %s',
    },
    'wikiquote': {
        'ml': '{{subst:സ്വാഗതം}}',
    },
    'wikisource': {
        'as': '{{subst:আদৰণি}} %s',
        'bn': '{{subst:স্বাগতম}} %s',
        'ml': '{{subst:സ്വാഗതം}}',
        'mr': '{{subst:Welcome}} %s',
    },
    'wiktionary': {
        'bn': '{{subst:স্বাগতম|%s}}',
        'fa': '{{جا:خوشامد|%s}}',
        'it': '{{subst:Utente:Filnik/Benve|firma=%s}}',
        'ml': '{{subst:സ്വാഗതം}}',
        'ur': '{{جا:خوش آمدید}}%s',
    },
    'wikiversity': {
        'de': '{{subst:Willkommen|%s}}',
        'el': '{{subst:καλωσόρισμα}} %s',
        'en': '{{subst:Welcome}}\n\n{{subst:Talktome}} %s',
        'es': '{{subst:bienvenido usuario}} %s',
        'fr': '{{Bienvenue}} %s',
        'it': '{{subst:Benvenuto}} %s',
    },
    'wikivoyage': {
        'bn': '{{subst:স্বাগতম}} %s',
    },
}
# The page where the bot will report users with a possibly bad username.
REPORT_PAGE = {
    'commons': ("Project:Administrators'noticeboard/User problems/Usernames"
                'to be checked'),
    'wikipedia': {
        'am': 'User:Beria/Report',
        'ar': 'Project:إخطار الإداريين/أسماء مستخدمين للفحص',
        'ckb': 'Project:لۆگی بەخێرھاتن/پشکنینی ناوی بەکارھێنەران',
        'da': 'Bruger:Broadbot/Report',
        'en': 'Project:Administrator intervention against vandalism',
        'fa': 'Project:تابلوی اعلانات مدیران/گزارش ربات',
        'ga': 'Project:Log fáilte/Drochainmneacha',
        'it': 'Project:Benvenuto_Bot/Report',
        'ja': '利用者:Alexbot/report',
        'nl': ('Project:Verzoekpagina voor moderatoren'
               '/RegBlok/Te controleren gebruikersnamen'),
        'no': 'Bruker:JhsBot II/Rapport',
        'pdc': 'Benutzer:Xqt/Report',
        'ru': 'Участник:LatitudeBot/Рапорт',
        'sq': 'User:EagleBot/Report',
        'sr': 'User:KizuleBot/Записи',
        'ur': 'Project:تختہ اعلانات برائے منتظمین/صارف نام برائے پڑتال',
        'zh': 'User:Welcomebot/report',
        'zh-yue': 'User:Alexbot/report',
    }
}
# The page where the bot reads the real-time bad words page
# (this parameter is optional).
BAD_PAGE = {
    'commons': 'Project:Welcome log/Bad_names',
    'wikipedia': {
        'am': 'User:Beria/Bad_names',
        'ar': 'Project:سجل الترحيب/أسماء سيئة',
        'ckb': 'Project:لۆگی بەخێرھاتن/ناوە_خراپەکان',
        'en': 'Project:Welcome log/Bad_names',
        'fa': 'Project:سیاهه خوشامد/نام بد',
        'it': 'Project:Benvenuto_Bot/Lista_Badwords',
        'ja': 'Project:不適切な名前の利用者',
        'nl': 'Project:Logboek_welkom/Bad_names',
        'no': 'Bruker:JhsBot/Daarlige ord',
        'ru': 'Участник:LatitudeBot/Чёрный список',
        'sq': 'User:Eagleal/Bad_names',
        'sr': 'User:KizuleBot/лоша корисничка имена',
        'zh': 'User:Welcomebot/badname',
        'zh-yue': 'User:Welcomebot/badname',
    }
}

timeselected = ' ~~~~~'  # Defining the time used after the signature

# The text for reporting a possibly bad username
# e.g. *[[Talk_page:Username|Username]]).
REPORT_TEXT = {
    'commons': '\n*{{user3|%s}}' + timeselected,
    'wikipedia': {
        'am': '\n*[[User talk:%s]]' + timeselected,
        'ar': '\n*{{user13|%s}}' + timeselected,
        'bs': '\n{{Korisnik|%s}}' + timeselected,
        'ckb': '\n*{{بەستەرەکانی بەکارھێنەر|%s}} ' + timeselected,
        'da': '\n*[[Bruger Diskussion:%s]] ' + timeselected,
        'de': '\n*[[Benutzer Diskussion:%s]] ' + timeselected,
        'en': '\n*{{Userlinks|%s}} ' + timeselected,
        'fa': '\n*{{کاربر|%s}}' + timeselected,
        'fr': '\n*{{u|%s}} ' + timeselected,
        'ga': '\n*[[Plé úsáideora:%s]] ' + timeselected,
        'it': '\n{{Reported|%s|',
        'ja': '\n*{{User2|%s}}' + timeselected,
        'nl': '\n*{{linkgebruiker%s}} ' + timeselected,
        'no': '\n*{{bruker|%s}} ' + timeselected,
        'pdc': '\n*[[Benutzer Diskussion:%s]] ' + timeselected,
        'sq': '\n*[[User:%s]] ' + timeselected,
        'sr': '\n*{{Корисник|%s}}' + timeselected,
        'zh': '\n*{{User|%s}}' + timeselected
    }
}
# Set where you load your list of signatures that the bot will load if you use
# the random argument (this parameter is optional).
RANDOM_SIGN = {
    'am': 'User:Beria/Signatures',
    'ar': 'Project:سجل الترحيب/توقيعات',
    'ba': 'Ҡатнашыусы:Salamat bot/Ярҙам',
    'ckb': 'Project:لۆگی بەخێرھاتن/واژوو',
    'da': 'Wikipedia:Velkommen/Signaturer',
    'en': 'Project:Welcome log/Sign',
    'fa': 'Project:سیاهه خوشامد/امضاها',
    'fr': 'Projet:Service de Parrainage Actif/Signatures',
    'it': 'Project:Benvenuto_Bot/Firme',
    # jawiki: Don't localize. Community discussion oppose to this feature
    # [[ja:Wikipedia:Bot作業依頼/ウェルカムメッセージ貼り付け依頼]]
    'nap': 'User:Cellistbot/Firme',
    'roa-tara': 'Wikipedia:Bovègne Bot/Firme',
    'ru': 'Участник:LatitudeBot/Sign',
    'ur': 'Project:خوش آمدید/دستخطیں',
    'vec': 'Utente:FriBot/Firme',
    'zh': 'User:Welcomebot/欢迎日志/用户',
}
# The page where the bot reads the real-time whitelist page.
# (this parameter is optional).
WHITELIST = {
    'ar': 'Project:سجل الترحيب/قائمة بيضاء',
    'en': 'User:Filnik/whitelist',
    'ga': 'Project:Log fáilte/Bánliosta',
    'it': 'Project:Benvenuto_Bot/Lista_Whitewords',
    'ru': 'Участник:LatitudeBot/Белый_список',
}

# Text after the {{welcome}} template, if you want to add something
# Default (en): nothing.
FINAL_NEW_TEXT_ADDITIONS = {
    'it': '\n<!-- fine template di benvenuto -->',
    'zh': '<small>(via ~~~)</small>',
}

LOGPAGE_HEADER = {
    '_default': '{|border="2" cellpadding="4" cellspacing="0" style="margin: '
                '0.5em 0.5em 0.5em 1em; padding: 0.5em; background: #bfcda5; '
                'border: 1px #b6fd2c solid; border-collapse: collapse; '
                'font-size: 95%;"',
    'no': '[[Kategori:Velkomstlogg|{{PAGENAME}}]]\n{| class="wikitable"',
    'it': '[[Categoria:Benvenuto log|{{subst:PAGENAME}}]]\n{|border="2" '
          'cellpadding="4" cellspacing="0" style="margin: 0.5em 0.5em 0.5em '
          '1em; padding: 0.5em; background: #bfcda5; border: 1px #b6fd2c '
          'solid; border-collapse: collapse; font-size: 95%;"'
}

# Ok, that's all. What is below, is the rest of code, now the code is fixed
# and it will run correctly in your project ;)
############################################################################


class Msg(Enum):

    """Enum for show_status method providing message header and color."""

    MSG = 'MSG', 'lightpurple'
    IGNORE = 'NoAct', 'lightaqua'
    MATCH = 'Match', 'lightgreen'
    SKIP = 'Skip', 'lightyellow'
    WARN = 'Warn', 'lightred'
    DONE = 'Done', 'lightblue'
    DEFAULT = 'MSG', 'lightpurple'


class FilenameNotSet(Error):

    """An exception indicating that a signature filename was not specified."""


class Global:

    """Container class for global settings."""

    attach_edit_count = 1    # edit count that an user required to be welcomed
    dump_to_log = 15         # number of users that are required to add the log
    offset = None            # skip users newer than that timestamp
    timeoffset = 0           # skip users newer than # minutes
    recursive = True         # define if the Bot is recursive or not
    time_recur = 3600        # seconds the bot waits before restart
    make_welcome_log = True  # create the welcome log or not
    confirm = False          # should bot ask to add user to bad-username list
    welcome_auto = False     # should bot welcome auto-created users
    filt_bad_name = False    # check if the username is ok or not
    random_sign = False      # should signature be random or not
    save_sign_index = False  # should save the signature index or not
    sign_file_name = None    # File name, default: None
    default_sign = '--~~~~'  # default signature
    query_limit = 50         # number of users that the bot load to check
    quiet = False            # Users without contributions aren't displayed


def get_welcome_text(site: pywikibot.site.BaseSite) -> str:
    """Check that site is managed by the script and return the message.

    :raises KeyError: site is not in WELCOME dict
    """
    msg = i18n.translate(site, WELCOME)
    if not msg:
        script = pywikibot.calledModuleName()
        welcome = 'welcome.' if script != 'welcome' else ''
        raise KeyError(f'{script}.py is not localized for site {site} in '
                       f'{welcome}WELCOME dict.')
    return msg


class WelcomeBot(SingleSiteBot):

    """Bot to add welcome messages on User pages."""

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        self.welcome_text = get_welcome_text(self.site)
        self.bname: dict[str, str] = {}

        self.welcomed_users: list[str] = []
        self.log_name = i18n.translate(self.site, LOGBOOK)

        if not self.log_name:
            globalvar.make_welcome_log = False
        if globalvar.random_sign:
            self.define_sign(True)

    def bad_name_filer(self, name, force: bool = False) -> bool:
        """Check for bad names."""
        if not globalvar.filt_bad_name:
            return False

        # initialize blacklist
        if not hasattr(self, '_blacklist') or force:
            elenco = [
                ' ano', ' anus', 'anal ', 'babies', 'baldracca', 'balle',
                'bastardo', 'bestiali', 'bestiale', 'bastarda', 'b.i.t.c.h.',
                'bitch', 'boobie', 'bordello', 'breast', 'cacata', 'cacca',
                'cachapera', 'cagata', 'cane', 'cazz', 'cazzo', 'cazzata',
                'chiavare', 'chiavata', 'chick', 'christ ', 'cristo',
                'clitoride', 'coione', 'cojdioonear', 'cojones', 'cojo',
                'coglione', 'coglioni', 'cornuto', 'cula', 'culatone',
                'culattone', 'culo', 'deficiente', 'deficente', 'dio', 'die ',
                'died ', 'ditalino', 'ejackulate', 'enculer', 'eroticunt',
                'fanculo', 'fellatio', 'fica ', 'ficken', 'figa', 'sfiga',
                'fottere', 'fotter', 'fottuto', 'fuck', 'f.u.c.k.', 'funkyass',
                'gay', 'hentai.com', 'horne', 'horney', 'virgin', 'hotties',
                'idiot', '@alice.it', 'incest', 'jesus', 'gesu', 'gesù',
                'kazzo', 'kill', 'leccaculo', 'lesbian', 'lesbica', 'lesbo',
                'masturbazione', 'masturbare', 'masturbo', 'merda', 'merdata',
                'merdoso', 'mignotta', 'minchia', 'minkia', 'minchione',
                'mona', 'nudo', 'nuda', 'nudi', 'oral', 'sex', 'orgasmso',
                'porc', 'pompa', 'pompino', 'porno', 'puttana', 'puzza',
                'puzzone', 'racchia', 'sborone', 'sborrone', 'sborata',
                'sborolata', 'sboro', 'scopata', 'scopare', 'scroto',
                'scrotum', 'sega', 'sesso', 'shit', 'shiz', 's.h.i.t.',
                'sadomaso', 'sodomist', 'stronzata', 'stronzo', 'succhiamelo',
                'succhiacazzi', 'testicol', 'troia', 'universetoday.net',
                'vaffanculo', 'vagina', 'vibrator', 'vacca', 'yiddiot',
                'zoccola',
            ]
            elenco_others = [
                '@', '.com', '.sex', '.org', '.uk', '.en', '.it', 'admin',
                'administrator', 'amministratore', '@yahoo.com', '@alice.com',
                'amministratrice', 'burocrate', 'checkuser', 'developer',
                'http://', 'jimbo', 'mediawiki', 'on wheals', 'on wheal',
                'on wheel', 'planante', 'razinger', 'sysop', 'troll', 'vandal',
                ' v.f. ', 'v. fighter', 'vandal f.', 'vandal fighter',
                'wales jimmy', 'wheels', 'wales', 'www.',
            ]

            # blacklist from wikipage
            badword_page = pywikibot.Page(self.site,
                                          i18n.translate(self.site, BAD_PAGE))
            list_loaded = []
            if badword_page.exists():
                pywikibot.info(
                    f'\nLoading the bad words list from {self.site}...')
                list_loaded = load_word_function(badword_page.get())
            else:
                self.show_status(Msg.WARN)
                pywikibot.info("The bad word page doesn't exist!")
            self._blacklist = elenco + elenco_others + list_loaded

        if not hasattr(self, '_whitelist') or force:
            # initialize whitelist
            whitelist_default = ['emiliano']
            wtlpg = i18n.translate(self.site, WHITELIST)
            list_white = []
            if wtlpg:
                whitelist_page = pywikibot.Page(self.site, wtlpg)
                if whitelist_page.exists():
                    pywikibot.info(
                        f'\nLoading the whitelist from {self.site}...')
                    list_white = load_word_function(whitelist_page.get())
                else:
                    self.show_status(Msg.WARN)
                    pywikibot.info("The whitelist's page doesn't exist!")
            else:
                self.show_status(Msg.WARN)
                pywikibot.warning("The whitelist hasn't been set!")

            # Join the whitelist words.
            self._whitelist = list_white + whitelist_default

        with suppress(UnicodeEncodeError):
            for wname in self._whitelist:
                if wname.lower() in str(name).lower():
                    name = name.lower().replace(wname.lower(), '')
                    for bname in self._blacklist:
                        self.bname[name] = bname
                        return bname.lower() in name.lower()
            for bname in self._blacklist:
                if bname.lower() in str(name).lower():  # bad name positive
                    self.bname[name] = bname
                    return True
        return False

    def collect_bad_accounts(self, name: str) -> None:
        """Add bad account to queue."""
        if globalvar.confirm:
            answer = pywikibot.input_choice(
                f'{name} may have an unwanted username, do you want to report '
                'this user?', [('Yes', 'y'), ('No', 'n'), ('All', 'a')],
                'n', automatic_quit=False)
            if answer in ['a', 'all']:
                answer = 'y'
                globalvar.confirm = False
        else:
            answer = 'y'

        if answer.lower() in ['yes', 'y'] or not globalvar.confirm:
            self.show_status()
            pywikibot.info(f'{name} is possibly an unwanted username. It will'
                           ' be reported.')
            if hasattr(self, '_BAQueue'):
                self._BAQueue.append(name)
            else:
                self._BAQueue = [name]

        if len(self._BAQueue) >= globalvar.dump_to_log:
            self.report_bad_account()

    def report_bad_account(self) -> None:
        """Report bad account."""
        rep_text = ''
        # name in queue is max, put detail to report page
        pywikibot.info('Updating badname accounts to report page...')
        rep_page = pywikibot.Page(self.site,
                                  i18n.translate(self.site, REPORT_PAGE))
        if rep_page.exists():
            text_get = rep_page.get()
        else:
            text_get = ('This is a report page for the Bad-username, '
                        'please translate me. --~~~')
        pos = 0
        # The talk page includes "_" between the two names, in this way
        # replace them to " ".
        for usrna in self._BAQueue:
            username = pywikibot.url2link(usrna, self.site, self.site)
            n = re.compile(re.escape(username))
            y = n.search(text_get, pos)
            if y:
                pywikibot.info(f'{username} is already in the report page.')
            else:
                # Adding the log.
                rep_text += i18n.translate(self.site, REPORT_TEXT) % username
                if self.site.code == 'it':
                    rep_text = f'{rep_text}{self.bname[username]}}}}}'

        com = i18n.twtranslate(self.site, 'welcome-bad_username')
        if rep_text != '':
            rep_page.put(text_get + rep_text, summary=com, force=True,
                         minor=True)
            self.show_status(Msg.DONE)
            pywikibot.info('Reported')
        self.BAQueue = []

    def makelogpage(self) -> None:
        """Make log page."""
        if not globalvar.make_welcome_log or not self.welcomed_users:
            return

        pattern = '%d/%m/%Y' if self.site.code == 'it' else '%Y/%m/%d'
        target = self.log_name + '/' + time.strftime(
            pattern, time.localtime(time.time()))

        log_page = pywikibot.Page(self.site, target)
        if log_page.exists():
            text = log_page.get()
        else:
            # make new log page
            self.show_status()
            pywikibot.info(
                'Log page is not exist, getting information for page creation')
            text = i18n.translate(self.site, LOGPAGE_HEADER,
                                  fallback=i18n.DEFAULT_FALLBACK)
            text += '\n!' + self.site.namespace(2)
            text += '\n!' + str.capitalize(
                self.site.mediawiki_message('contribslink'))

        # Adding the log... (don't take care of the variable's name...).
        text += '\n'
        text += '\n'.join(
            '{{WLE|user=%s|contribs=%d}}' % (
                user.title(as_url=True, with_ns=False), user.editCount())
            for user in self.welcomed_users)

        # update log page.
        while True:
            try:
                log_page.put(text, i18n.twtranslate(self.site,
                                                    'welcome-updating'))
            except EditConflictError:
                pywikibot.info('An edit conflict has occurred. '
                               'Pausing for 10 seconds before continuing.')
                time.sleep(10)
            else:
                break
        self.welcomed_users = []

    @property
    def generator(self) -> Generator[pywikibot.User, None, None]:
        """Retrieve new users."""
        while True:
            if globalvar.timeoffset != 0:
                start = self.site.server_time() - timedelta(
                    minutes=globalvar.timeoffset)
            else:
                start = globalvar.offset
            for ue in self.site.logevents('newusers',
                                          total=globalvar.query_limit,
                                          start=start):
                if ue.action() == 'create' \
                   or ue.action() == 'autocreate' and globalvar.welcome_auto:
                    try:
                        user = ue.page()
                    except HiddenKeyError as e:
                        pywikibot.error(e)
                    else:
                        yield user

            self.write_log()
            if not globalvar.recursive:
                break

            # Wait some seconds and repeat retrieving new users
            self.show_status()
            strfstr = time.strftime('%d %b %Y %H:%M:%S (UTC)', time.gmtime())
            pywikibot.info(f'Sleeping {globalvar.time_recur} seconds before '
                           f'rerun. {strfstr}')
            pywikibot.sleep(globalvar.time_recur)

    def define_sign(self, force: bool = False) -> list[str]:
        """Setup signature."""
        if hasattr(self, '_random_signature') and not force:
            return self._random_signature

        sign_text = ''
        creg = re.compile(r'^\* ?(.*?)$', re.MULTILINE)
        if not globalvar.sign_file_name:
            sign_page_name = i18n.translate(self.site, RANDOM_SIGN)
            if not sign_page_name:
                self.show_status(Msg.WARN)
                pywikibot.info(f"{self.site} doesn't allow random signature,"
                               ' force disable.')
                globalvar.random_sign = False
                return []

            sign_page = pywikibot.Page(self.site, sign_page_name)
            if sign_page.exists():
                pywikibot.info('Loading signature list...')
                sign_text = sign_page.get()
            else:
                pywikibot.info('The signature list page does not exist, '
                               'random signature will be disabled.')
                globalvar.random_sign = False
        else:
            filename = pywikibot.config.datafilepath(globalvar.sign_file_name)
            try:
                f = open(filename, encoding=config.console_encoding)
            except LookupError:
                f = open(filename, encoding='utf-8')
            except OSError:
                pywikibot.error('No fileName!')
                raise FilenameNotSet('No signature filename specified.')

            sign_text = f.read()
            f.close()
        self._random_signature = creg.findall(sign_text)
        return self._random_signature

    def skip_page(self, user) -> bool:
        """Check whether the user is to be skipped.

        .. versionchanged:: 7.0
           also skip if user is locked globally
        """
        if user.is_blocked() or user.is_locked():
            self.show_status(Msg.SKIP)
            pywikibot.info(f'{user.username} has been blocked!')

        elif 'bot' in user.groups():
            self.show_status(Msg.SKIP)
            pywikibot.info(f'{user.username} is a bot!')

        elif 'bot' in user.username.lower():
            self.show_status(Msg.SKIP)
            pywikibot.info(f'{user.username} might be a global bot!')

        elif user.editCount() < globalvar.attach_edit_count:
            if user.editCount() != 0:
                self.show_status(Msg.IGNORE)
                pywikibot.info(f'{user.username} has only {user.editCount()}'
                               ' contributions.')
            elif not globalvar.quiet:
                self.show_status(Msg.IGNORE)
                pywikibot.info(f'{user.username} has no contributions.')
        else:
            return super().skip_page(user)

        return True

    def treat(self, user) -> None:
        """Run the bot."""
        self.show_status(Msg.MATCH)
        pywikibot.info(f'{user.username} has enough edits to be welcomed.')
        ustp = user.getUserTalkPage()
        if ustp.exists():
            self.show_status(Msg.SKIP)
            pywikibot.info(f'{user.username} has been already welcomed.')
            return

        if self.bad_name_filer(user.username):
            self.collect_bad_accounts(user.username)
            return

        welcome_text = self.welcome_text
        if globalvar.random_sign:
            if self.site.family.name != 'wikinews':
                welcome_text = welcome_text % choice(self.define_sign())
            if self.site.sitename != 'wiktionary:it':
                welcome_text += timeselected
        elif self.site.sitename != 'wikinews:it':
            welcome_text = welcome_text % globalvar.default_sign

        final_text = i18n.translate(self.site, FINAL_NEW_TEXT_ADDITIONS)
        if final_text:
            welcome_text += final_text
        welcome_comment = i18n.twtranslate(self.site, 'welcome-welcome')
        try:
            # append welcomed, welcome_count++
            ustp.put(welcome_text, welcome_comment, minor=False)
        except EditConflictError:
            self.show_status(Msg.WARN)
            pywikibot.info(
                'An edit conflict has occurred, skipping this user.')
        else:
            self.welcomed_users.append(user)

        welcomed_count = len(self.welcomed_users)
        if globalvar.make_welcome_log:
            self.show_status(Msg.DONE)
            if welcomed_count == 0:
                count = 'No users have'
            elif welcomed_count == 1:
                count = 'One user has'
            else:
                count = f'{welcomed_count} users have'
            pywikibot.info(count + ' been welcomed.')

            if welcomed_count >= globalvar.dump_to_log:
                self.makelogpage()

    def write_log(self) -> None:
        """Write logfile."""
        welcomed_count = len(self.welcomed_users)
        if globalvar.make_welcome_log and welcomed_count > 0:
            self.show_status()
            if welcomed_count == 1:
                pywikibot.info('Putting the log of the latest user...')
            else:
                pywikibot.info(
                    f'Putting the log of the latest {welcomed_count} users...')
            self.makelogpage()

        if hasattr(self, '_BAQueue'):
            self.show_status()
            pywikibot.info('Putting bad name to report page...')
            self.report_bad_account()

    @staticmethod
    def show_status(message=Msg.DEFAULT) -> None:
        """Output colorized status."""
        msg, color = message.value
        pywikibot.info(f'<<{color}>>[{msg:5}]<<default>> ', newline=False)

    def teardown(self) -> None:
        """Some cleanups after run operation."""
        if self.welcomed_users:
            self.show_status()
            pywikibot.info('Put welcomed users before quit...')
            self.makelogpage()

        # If there is the savedata, the script must save the number_user.
        if globalvar.random_sign and globalvar.save_sign_index \
           and self.welcomed_users:
            # Filename and Pywikibot path
            # file where is stored the random signature index
            filename = pywikibot.config.datafilepath(
                f'welcome-{self.site.family.name}-{self.site.code}.data')
            with open(filename, 'wb') as f:
                pickle.dump(self.welcomed_users, f,
                            protocol=config.pickle_protocol)


def load_word_function(raw) -> list[str]:
    """Load the badword list and the whitelist."""
    page = re.compile(r'(?:\"|\')(.*?)(?:\"|\')(?:, |\))')
    list_loaded = page.findall(raw)
    if not list_loaded:
        pywikibot.info('There was no input on the real-time page.')
    return list_loaded


globalvar = Global()


def _handle_offset(val) -> None:
    """Handle -offset arg."""
    if not val:
        val = pywikibot.input(
            'Which time offset for new users would you like to use? '
            '(yyyymmddhhmmss or yyyymmdd)')
    try:
        globalvar.offset = pywikibot.Timestamp.fromtimestampformat(val)
    except ValueError:
        # upon request, we could check for software version here
        raise ValueError(fill(
            'MediaWiki has changed, -offset:# is not supported anymore, but '
            '-offset:TIMESTAMP is, assuming TIMESTAMP is yyyymmddhhmmss or '
            'yyyymmdd. -timeoffset is now also supported. Please read this '
            'script source header for documentation.'))


def handle_args(args) -> None:
    """Process command line arguments.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    mapping = {
        # option: (attribute, value),
        '-break': ('recursive', False),
        '-nlog': ('make_welcome_log', False),
        '-ask': ('confirm', True),
        '-filter': ('filt_bad_name', True),
        '-savedata': ('save_sign_index', True),
        '-random': ('random_sign', True),
        '-sul': ('welcome_auto', True),
        '-quiet': ('quiet', True),
    }

    for arg in pywikibot.handle_args(args):
        arg, _, val = arg.partition(':')
        if arg == '-edit':
            globalvar.attach_edit_count = int(
                val if val.isdigit() else pywikibot.input(
                    'After how many edits would you like to welcome new users?'
                    ' (0 is allowed)'))
        elif arg == '-timeoffset':
            globalvar.timeoffset = int(
                val if val.isdigit() else pywikibot.input(
                    'Which time offset (in minutes) for new users would you '
                    'like to use?'))
        elif arg == '-time':
            globalvar.time_recur = int(
                val if val.isdigit() else pywikibot.input(
                    'For how many seconds would you like to bot to sleep '
                    'before checking again?'))
        elif arg == '-offset':
            _handle_offset(val)
        elif arg == '-file':
            globalvar.random_sign = True
            globalvar.sign_file_name = val or pywikibot.input(
                'Where have you saved your signatures?')
        elif arg == '-sign':
            globalvar.default_sign = val or pywikibot.input(
                'Which signature to use?')
            globalvar.default_sign += timeselected
        elif arg == '-limit':
            globalvar.query_limit = int(
                val if val.isdigit() else pywikibot.input(
                    'How many of the latest new users would you like to '
                    'load?'))
        elif arg == '-numberlog':
            globalvar.dump_to_log = int(
                val if val.isdigit() else pywikibot.input(
                    'After how many welcomed users would you like to update '
                    'the welcome log?'))
        elif arg in mapping:
            setattr(globalvar, *mapping[arg])
        else:
            pywikibot.warning(f'Unknown option "{arg}"')


def main(*args: str) -> None:
    """Invoke bot.

    :param args: command line arguments
    """
    handle_args(args)
    if globalvar.offset and globalvar.timeoffset:
        pywikibot.warning(
            'both -offset and -timeoffset were provided, ignoring -offset')
        globalvar.offset = 0

    try:
        bot = WelcomeBot()
    except KeyError as error:
        # site not managed by welcome.py
        pywikibot.bot.suggest_help(exception=error)
    else:
        bot.run()


if __name__ == '__main__':
    main()
