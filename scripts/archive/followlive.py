#!/usr/bin/python
"""
Periodically grab list of new articles and analyze to blank or flag them.

Script to follow new articles on the wiki and flag them
with a template or eventually blank them.

There must be A LOT of bugs! Use with caution and verify what
it is doing!

The following parameters are supported:

&params;
"""
#
# (C) Pywikibot team, 2005-2020
#
# Distributed under the terms of the MIT license.
#
import datetime

import pywikibot
from pywikibot import editor, i18n, pagegenerators
from pywikibot.bot import CurrentPageBot, QuitKeyboardInterrupt, SingleSiteBot
from pywikibot.exceptions import (
    EditConflictError,
    IsRedirectPageError,
    NoPageError,
)


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

# templates that can be used followed by the message used as comment
# templates contains list of languages code
#   languages code contains list of templates to be used
#       templates contains a message and its position
templates = {
    'ar': {
        '{{شطب}}': {
            'msg': 'وسم مساعد بالبوت: هذا المقال ينبغي حذفه',
            'pos': 'top'},

        '{{تهذيب}}': {
            'msg': 'وسم مساعد بالبوت: هذا المقال يحتاج للتنظيف',
            'pos': 'top'},

        '{{بذرة}}': {
            'msg': 'وسم مساعد بالبوت: هذا المقال بذرة',
            'pos': 'bottom'},

        '{{غير مصنفة}}': {
            'msg': ('وسم مساعد بالبوت: هذا المقال يحتاج '
                    '[[ويكيبيديا:تصنيف|للتصنيف]]'),
            'pos': 'bottom'},

        '{{ملحوظية}}': {
            'msg': ('وسم مساعد بالبوت: '
                    '[[ويكيبيديا:ملحوظية|ملحوظية]] '
                    'هذا المقال غير واضحة.'),
            'pos': 'top'},

        '{{مصادر أكثر}}': {
            'msg': ('وسم مساعد بالبوت: هذا المقال ينبغي مراجعته '
                    'من حيث الدقة.'),
            'pos': 'top'},

        '{{تدقيق لغوي}}': {
            'msg': ('وسم مساعد بالبوت: أسلوب كتابة هذا المقال '
                    'يحتاج إلى [[ويكيبيديا:دليل الأسلوب|التدقيق اللغوي]] '
                    'والتحسين.'),
            'pos': 'top'},

        '{{لا مصدر}}': {
            'msg': ('وسم مساعد بالبوت: هذا المقال يحتاج '
                    '[[ويكيبيديا:الاستشهاد بمصادر|لمراجع]] حتى يمكن '
                    'التحقق منه.'),
            'pos': 'top'},

        '{{ويكي}}': {
            'msg': 'وسم مساعد بالبوت: هذا المقال يحتاج إلى التنسيق '
                   'بضيغة الويكي حسب [[ويكيبيديا:دليل الأسلوب|دليل الأسلوب]]',
            'pos': 'top'},
    },
    'arz': {
        '{{مسح}}': {
            'msg': 'وسم متساعد بالبوت: المقال ده محتاج يتمسح',
            'pos': 'top'},

        '{{تقاوى}}': {
            'msg': 'وسم متساعد بالبوت: المقال ده تقاوى',
            'pos': 'bottom'},

        '{{مش متصنفه}}': {
            'msg': ('وسم متساعد بالبوت: المقال ده محتاج '
                    '[[ويكيبيديا:تصنيف|يتصنف]]'),
            'pos': 'bottom'},
    },
    'en': {
        '{{db-reason}}': {
            'msg': 'Robot-assisted tagging: this article should be deleted',
            'pos': 'top'},

        '{{cleanup}}': {
            'msg': 'Robot-assisted tagging: this article need cleanup',
            'pos': 'top'},

        '{{stub}}': {
            'msg': 'Robot-assisted tagging: this article is a stub',
            'pos': 'bottom'},

        '{{uncategorized}}': {
            'msg': ('Robot-assisted tagging: This article needs to be '
                    '[[Wikipedia:Categorization|categorized]]'),
            'pos': 'top'},

        '{{notability}}': {
            'msg': ('Robot-assisted tagging: the '
                    '[[Wikipedia:Notability|notability]] '
                    'of this article is unclear.'),
            'pos': 'top'},

        '{{not verified}}': {
            'msg': ('Robot-assisted tagging: this article needs to be checked '
                    'for factuality.'),
            'pos': 'top'},

        '{{copyedit}}': {
            'msg': ('Robot-assisted tagging: the writing of this article '
                    'needs to be  [[Wikipedia:How to copy-edit|copyedited]] '
                    'and improved.'),
            'pos': 'top'},

        '{{unreferenced}}': {
            'msg': ('Robot-assisted tagging: this article needs '
                    '[[Wikipedia:Citing sources|references]] so it can be '
                    'verified.'),
            'pos': 'bottom'},

        '{{wikify}}': {
            'msg': ('Robot-assisted tagging: this article needs to be '
                    'wikified per the '
                    '[[Wikipedia:Manual of Style|Manual of Style]]'),
            'pos': 'top'},
    },
    'fr': {
        '{{suppression}}': {
            'msg': "à l'aide du robot: cet article devrait être supprimé",
            'pos': 'top'},

        '{{à vérifier}}': {
            'msg': "à l'aide du robot: cet article est à vérifier",
            'pos': 'top'},

        '{{ébauche}}': {
            'msg': "à l'aide du robot: cet article est une ébauche",
            'pos': 'top'},
    },
    'he': {
        '{{מחק}}': {
            'msg': 'יש למחוק ערך זה',
            'pos': 'top'
        },
        '{{לשכתב}}': {
            'msg': 'ערך זה דורש שכתוב',
            'pos': 'top'
        },
        '{{קצרמר}}': {
            'msg': 'ערך זה הוא קצרמר',
            'pos': 'bottom'
        },
        '{{הבהרת חשיבות}}': {
            'msg': 'חשיבותו של ערך זה אינה ברורה.',
            'pos': 'top'
        },
        '{{עריכה}}': {
            'msg': 'ערך זה דורש עריכה',
            'pos': 'top'},
    },
    'ia': {
        '{{Eliminar}}': {
            'msg': 'Assistite per robot: iste articulo debe esser eliminate',
            'pos': 'top'},

        '{{Revision}}': {
            'msg': 'Assistite per robot: iste articulo require revision',
            'pos': 'top'},

        '{{Stub}}': {
            'msg': 'Assistite per robot: iste articulo es in stato embryonic',
            'pos': 'bottom'},
    },
    'nl': {
        '{{weg}}': {
            'msg': '{weg}',
            'pos': 'top'
        },
        '{{nuweg}}': {
            'msg': '{nuweg}',
            'pos': 'top'
        },
        '{{wiu}}': {
            'msg': '{wiu}',
            'pos': 'top'
        },
        '{{beg}}': {
            'msg': '{beg}',
            'pos': 'bottom'
        },
        '{{wikify}}': {
            'msg': '{wikify}',
            'pos': 'top'
        },
        '{{wb}}': {
            'msg': '{wb}',
            'pos': 'top'
        },
    },
    'pl': {
        '{{ek}}': {
            'msg': '[[Kategoria:Ekspresowe kasowanko|ek]]',
            'pos': 'top'
        },
        '{{dopracować}}': {
            'msg': 'Dopracować',
            'pos': 'top'
        },
        '{{linki}}': {
            'msg': 'Linki wewnętrzne do dodania',
            'pos': 'top'
        },
        '{{źródła}}': {
            'msg': 'W artykule brakuje źródeł',
            'pos': 'top'
        },
        '{{stub}}': {
            'msg': 'stub (zalążek)',
            'pos': 'bottom'
        },
    },
    'pt': {
        '{{wikificar}}': {
            'msg': 'Assistida por bot: {{wikificar}}',
            'pos': 'top'},

        '{{reciclar}}': {
            'msg': 'Assistida por bot: {{reciclar}}',
            'pos': 'top'},

        '{{lixo|~~~~}}': {
            'msg': 'Assistida por bot: {{lixo}}',
            'pos': 'top'},

        '{{revisão}}': {
            'msg': 'Assistida por bot: {{revisão}}',
            'pos': 'top'},

        '{{impróprio}}': {
            'msg': 'Assistida por bot: {{impróprio}}',
            'pos': 'top'},

        '{{apagar vaidade}}': {
            'msg': 'Assistida por bot: {{apagar vaidade}}',
            'pos': 'top'},
    },
    'sv': {
        '{{radera}}': {
            'msg': 'Robotkoll: Artikeln bör raderas',
            'pos': 'top'},

        '{{städa}}': {
            'msg': 'Robotkoll: Artikeln bör städas',
            'pos': 'top'},

        '{{stub}}': {
            'msg': 'Robotkoll: Artikeln är en stubbe',
            'pos': 'bottom'},

        '{{subst:relevanskontroll}}': {
            'msg': 'Robotkoll: Artikeln bör kollas mot '
                   '[[WP:REL|Wikipedias relevanskriterier]].',
            'pos': 'top'},

        '{{verifieras}}': {
            'msg': 'Robotkoll: Artikeln bör verifieras',
            'pos': 'top'},

        '{{språkvård}}': {
            'msg': 'Robotkoll: Artikeln bör språkvårdas',
            'pos': 'top'},

        '{{Källor}}': {
            'msg': 'Robotkoll: Artikeln behöver källor',
            'pos': 'bottom'},

        '{{wikify}}': {
            'msg': 'Robotkoll: Artikeln behöver wikifieras',
            'pos': 'top'},
    },
    'ur': {
        '{{حذف}}': {
            'msg': 'خودکار: مضمون قابل حذف ہے',
            'pos': 'top'},

        '{{صفائی}}': {
            'msg': 'خودکار: مضمون کی تحریر قابل اصلاح ہے',
            'pos': 'top'},

        '{{نامکمل}}': {
            'msg': 'خودکار: سانچہ نامکمل کی ٹیگ کاری',
            'pos': 'bottom'},

        '{{ویکائی}}': {
            'msg': 'خودکار: مضمون کی ویکائی درکار ہے',
            'pos': 'top'},
    },
    'zh': {
        '{{Delete}}': {
            'msg': '機器人掛上模板: 本文應被刪除。',
            'pos': 'top'},

        '{{subst:Cleanup/auto}}': {
            'msg': '機器人掛上模板: 本文需清理',
            'pos': 'top'},

        '{{subst:Uncategorized/auto}}': {
            'msg': '機器人掛上模板:  本頁需要適當的頁面分類',
            'pos': 'bottom'},

        '{{subst:Notability/auto}}': {
            'msg': '機器人掛上模板:  本條目主題未突顯其知名度或顯著性',
            'pos': 'top'},

        '{{subst:refimprove/auto}}': {
            'msg': '機器人掛上模板:  本條目参考文献不足',
            'pos': 'top'},

        '{{copyedit}}': {
            'msg': '機器人掛上模板:  本條目或段落需要校對',
            'pos': 'top'},

        '{{subst:Unreferenced/auto}}': {
            'msg': '機器人掛上模板:  本條目沒有列出任何參考或來源',
            'pos': 'top'},

        '{{subst:wikify/auto}}': {
            'msg': '機器人掛上模板:  本條目需要維基化',
            'pos': 'top'},

        '{{subst:Notchinese/auto}}': {
            'msg': '機器人掛上模板: 本条目没有翻译',
            'pos': 'top'},

        '{{subst:Substub/auto}}': {
            'msg': '機器人掛上模板:  小小作品',
            'pos': 'top'},

        '{{stub}}': {
            'msg': '機器人掛上模板: 本文是小作品',
            'pos': 'bottom'},
        '{{notchinesetitle}}': {
            'msg': '機器人掛上模板: 本条目名称需要翻译成中文',
            'pos': 'top'},
        '{{subst:Translating/auto}}': {
            'msg': '機器人掛上模板: 本条目没有翻译完成',
            'pos': 'top'},
        '{{fansite}}': {
            'msg': '機器人掛上模板: 本条目內容類似愛好者網站',
            'pos': 'top'},

    },
}

# do nothing if this is in it
done = {
    'ar': ('{{شطب}}', '{{حذف}}', '{{خرق}}'),
    'arz': ('{{مسح}}',),
    'en': ('{{VfD}}', '{{AfD}}', '{{AfD1}}', '{{cleanup}}', '{{nonsense}}',
           '{{deletedpage}}', '{{db-reason}}', '{{notability}}',
           '{{not verified}}', '{{unreferenced}}', '{{db-empty}}',
           '{{db-nocontext}}', '{{db-foreign}}', '{{db-notenglish}}',
           '{{db-nocontent}}', '{{db-blankcsd}}', '{{db-transwiki}}',
           '{{db-attack}}', '{{db-band}}', '{{db-club}}', '{{db-bio}}',
           '{{db-bio-notenglish}}', '{{db-inc}}', '{{db-bio-photo}}',
           '{{db-catempty}}', '{{db-c2}}', '{{db-catfd}}', '{{badname}}',
           '{{db-pagemove}}', '{{db-nonsense}}', '{{db-spam}}',
           '{{db-copyvio}}', '{{db-test}}', '{{db-vandalism}}',
           '{{db-repost}}', '{{db-banned}}', '{{db-histmerge}}', '{{db-move}}',
           '{{db-g6}}', '{{db-afd}}', '{{db-disambig}}', '{{db-authora}}',
           '{{db-author}}', '{{db-blanked}}', '{{csd:g7}}', '{{db-talk}}',
           '{{db-botnomain}}', '{{db-redundantimage}}', '{{db-noimage}}',
           '{{db-noncom}}', '{{db-ccnoncom}}', '{{db-unksource}}',
           '{{db-norat}}', '{{db-badfairuse}}', '{{duplicate}}', '{{db-meta}}',
           '{{db-emptyportal}}', '{{db-redirnone}}', '{{db-rediruser}}',
           '{{db-redirtypo}}', '{{csd-c3}}', '{{cc-by-nc-sa}}', '{{cc-nd-nc}}',
           '{{cc-nc}}', '{{cc-by-nc-2.0}}', '{{cc-by-nc-sa-2.0}}',
           '{{cc-by-nd-nc-2.0}}', '{{cc-by-2.0-nc-nd}}', '{{cc-by-nc-nd-2.0}}',
           '{{db-contact}}', '{{db-i2}}', '{{db-i1}}', '{{communityuseonly}}',
           '{{db-disparage}}', '{{db-web}}', '{{db-userreq}}', '{{db-nouser}}',
           '{{db-u3}}', '{{db-unfree}}'),
    'fr': ('{{suppression}}', '{{à vérifier}}', '{{ébauche}}'),
    'ia': ('{{Eliminar}}', '{{Revision}}', '{{Stub}}'),
    'he': ('{{מחק}}', '{{פירושונים}}', '{{הצבעת מחיקה}}'),
    'nl': ('{{nuweg}}', '{{weg}}', '{{wb}}', '{{wiu}}', '{{nocat}}'),
    'pl': ('{{ek}}', '{{dopracować}}', '{{linki}}', '{{źródła}}',
           '{{stub}}'),
    'pt': ('{{wikificar}}', '{{reciclar}}', '{{lixo}}', '{{revisão}}',
           '{{impróprio}}', '{{apagar vaidade}}'),
    'sv': ('{{radera', '{{Radera', '{{städa}}', '{{stub}}',
           '{{verifieras}}', '{{språkvård}}', '{{Källor', '{{källor',
           '{{wikify}}', '{{Ickewiki}}', '{{ickewiki}}', '{{Wikify}}'),
    'zh': ('{{VfD}}', '{{AfD}}', '{{unreferenced}}', '{{db-reason}}',
           '{{cleanup}}', '{{stub}}', '{{uncategorized}}', '{{notability}}',
           '{{copyedit}}', '{{unreferenced}}', '{{wikify}}',
           '{{Translating}}', '{{copyvio}}', '{{Notchinese}}'),
}

# TODO: merge 'done' with 'templates' above


class CleaningBot(SingleSiteBot, CurrentPageBot):

    """Bot meant to facilitate customized cleaning of the page."""

    def __init__(self, **kwargs):
        """Initializer."""
        # The question asked
        self.question = """
(multiple numbers delimited with ',')

b) blank page
e) edit page
d) delete page (needs deletion right)
q) quit cleaningbot
Enter) OK
What is it? """
        super().__init__(**kwargs)
        self.generator = self.site.newpages()

    def show_page_info(self):
        """Display information about an article."""
        pywikibot.output('Date:   {info.date}\n'
                         'Length: {info.length} bytes\n'
                         'User:   {info.user.username}'
                         .format(info=self))

    def could_be_bad(self):
        """Check whether the page could be bad."""
        return (self.length < 250 or not self.user.isRegistered()
                or 'autoconfirmed' not in self.user.groups())

    def handle_bad_page(self, *values):
        """Process one bad page."""
        try:
            self.content = self.page.get()
        except IsRedirectPageError:
            pywikibot.output('Already redirected, skipping.')
            return
        except NoPageError:
            pywikibot.output('Already deleted')
            return

        for d in pywikibot.translate(self.site.code, done):
            if d in self.content:
                pywikibot.output(
                    'Found: "{}" in content, nothing necessary'.format(d))
                return
        pywikibot.output('---- Start content ----------------')
        pywikibot.output(self.content)
        pywikibot.output('---- End of content ---------------')

        # Loop other user answer
        answered = False
        while not answered:
            answer = pywikibot.input(self.question)

            if answer == 'q':
                raise QuitKeyboardInterrupt
            if answer == 'd':
                pywikibot.output('Trying to delete page [[{}]].'
                                 .format(self.page.title()))
                self.page.delete()
                return
            if answer == 'e':
                old = self.content
                new = editor.TextEditor().edit(old)
                msg = pywikibot.input('Summary message:')
                self.userPut(self.page, old, new, summary=msg)
                return
            if answer == 'b':
                pywikibot.output('Blanking page [[{}]].'
                                 .format(self.page.title()))
                try:
                    self.page.put('',
                                  summary=i18n.twtranslate(
                                      self.site.lang,
                                      'followlive-blanking',
                                      {'content': self.content}))
                except EditConflictError:
                    pywikibot.output(
                        'An edit conflict occurred! Automatically retrying')
                    self.handle_bad_page(self)
                return
            if answer == '':
                pywikibot.output('Page correct! Proceeding with next pages.')
                return
            # Check user input:
            if answer[0] == 'u':
                # Answer entered as string
                answer = answer[1:]
            try:
                choices = answer.split(',')
            except ValueError:
                # User entered wrong value
                pywikibot.error('"{}" is not valid'.format(answer))
                continue
            # test input
            for choice in choices:
                try:
                    x = int(choice)
                except ValueError:
                    break
                else:
                    answered = (x >= 1 and x <= len(self.questionlist))
            if not answered:
                pywikibot.error('"{}" is not valid'.format(answer))
                continue
        summary = ''
        for choice in choices:
            answer = int(choice)
            # grab the template parameters
            tpl = pywikibot.translate(self.site,
                                      templates)[self.questionlist[answer]]
            if tpl['pos'] == 'top':
                pywikibot.output(
                    'prepending {}...'.format(self.questionlist[answer]))
                self.content = self.questionlist[answer] + '\n' + self.content
            elif tpl['pos'] == 'bottom':
                pywikibot.output('appending {}...'
                                 .format(self.questionlist[answer]))
                self.content += '\n' + self.questionlist[answer]
            else:
                raise RuntimeError(
                    '"pos" should be "top" or "bottom" for template {}. '
                    'Contact a developer.'.format(self.questionlist[answer]))
            summary += tpl['msg'] + ' '
            pywikibot.output('Probably added ' + self.questionlist[answer])

        self.page.put(self.content, summary=summary)
        pywikibot.output('with comment {}\n'.format(summary))

    def treat_page(self):
        """Process one page."""
        self.show_page_info()
        if self.could_be_bad():
            pywikibot.output('Integrity of page doubtful...')
            self.handle_bad_page()
        pywikibot.output('----- Current time: {}'
                         .format(datetime.datetime.now()))

    def init_page(self, item):
        """Init the page tuple before processing and return a page object.

        Set newpages generator result as instance properties.
        :ivar page: new page
        :type page: pywikibot.Page
        :ivar date: creation date
        :type date: str in ISO8601 format
        :ivar length: content length
        :type length: int
        :ivar user: creator of page
        :type user: pywikibot.User
        """
        self.page, self.date, self.length, _, user, comment = item
        self.user = pywikibot.User(self.site, user)
        return super().init_page(self.page)

    def setup(self):
        """Setup bot before running."""
        self.questionlist = {
            i: t for i, t in enumerate(templates[self.site.code], start=1)}
        questions = '\n'.join('{}) {}'.format(k, v)
                              for k, v in self.questionlist.items())
        self.question = questions + self.question


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    # Generate the question text
    pywikibot.handle_args(*args)
    site = pywikibot.Site()

    if site.code in templates and site.code in done:
        bot = CleaningBot(site=site)
        bot.run()
    else:
        pywikibot.output(
            '\nScript is not localised for {}. Terminating program.'
            .format(site))


if __name__ == '__main__':
    main()
