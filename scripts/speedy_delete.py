#!/usr/bin/env python3
"""
Help sysops to quickly check and/or delete pages listed for speedy deletion.

This bot trawls through candidates for speedy deletion in a fast
and semi-automated fashion. It displays the contents of each page
one at a time and provides a prompt for the user to skip or delete the page.
Of course, this will require a sysop account.

Future upcoming options include the ability to untag a page as not being
eligible for speedy deletion, as well as the option to commute its sentence to
Proposed Deletion (see [[en:WP:PROD]] for more details).  Also, if the article
text is long, to prevent terminal spamming, it might be a good idea to truncate
it just to the first so many bytes.

.. warning:: This tool shows the contents of the top revision only.  It
   is possible that a vandal has replaced a perfectly good article with
   nonsense, which has subsequently been tagged by someone who didn't
   realize it was previously a good article. The onus is on you to avoid
   making these mistakes.

.. note:: This script currently only works for the Wikipedia project.
"""
#
# (C) Pywikibot team, 2007-2022
#
# Distributed under the terms of the MIT license.
#
import time
from textwrap import fill

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import ExistingPageBot, SingleSiteBot
from pywikibot.exceptions import Error


class SpeedyBot(SingleSiteBot, ExistingPageBot):
    """Bot to delete pages which are tagged as speedy deletion.

    This bot will load a list of pages from the category of candidates for
    speedy deletion on the language's wiki and give the user an interactive
    prompt to decide whether each should be deleted or not.
    """

    LINES = 22  #: maximum lines to extract from wiki page

    csd_cat_item = 'Q5964'

    csd_cat_title = {
        'wikiversity': {
            'beta': 'Category:Candidates for speedy deletion',
        },
        'wikibooks': {
            'en': 'Category:Candidates for speedy deletion',
        },
        'incubator': {'incubator': 'Category:Maintenance:Delete'},
    }

    #: If the site has several templates for speedy deletion, it might be
    #: possible to find out the reason for deletion by the template used.
    #: _default will be used if no such semantic template was used.
    deletion_messages = {
        'wikipedia': {
            'ar': {
                '_default':
                    'حذف مرشح للحذف السريع حسب '
                    '[[وب:شطب|معايير الحذف السريع]]',
            },
            'arz': {
                '_default':
                    'مسح صفحه مترشحه للمسح السريع حسب '
                    '[[ويكيبيديا:مسح سريع|معايير المسح السريع]]',
            },
            'cs': {
                '_default':
                    'Bylo označeno k '
                    '[[Wikipedie:Rychlé smazání|rychlému smazání]]',
            },
            'de': {
                '_default':
                    'Lösche Artikel nach '
                    '[[Wikipedia:Schnelllöschantrag|Schnelllöschantrag]]',
            },
            'en': {
                '_default':
                    'Deleting candidate for speedy deletion per '
                    '[[WP:CSD|CSD]]',
                'db-author':
                    'Deleting page per [[WP:CSD|CSD]] G7: '
                    'Author requests deletion and is its only editor.',
                'db-nonsense':
                    'Deleting page per [[WP:CSD|CSD]] G1: '
                    'Page is patent nonsense or gibberish.',
                'db-test': 'Deleting page per [[WP:CSD|CSD]] G2: Test page.',
                'db-nocontext':
                    'Deleting page per [[WP:CSD|CSD]] A1: '
                    'Short article that provides little or no context.',
                'db-empty':
                    'Deleting page per [[WP:CSD|CSD]] A1: Empty article.',
                'db-attack':
                    'Deleting page per [[WP:CSD|CSD]] G10: '
                    'Page that exists solely to attack its subject.',
                'db-catempty':
                    'Deleting page per [[WP:CSD|CSD]] C1: Empty category.',
                'db-band':
                    'Deleting page per [[WP:CSD|CSD]] A7: '
                    'Article about a non-notable band.',
                'db-banned':
                    'Deleting page per [[WP:CSD|CSD]] G5: '
                    'Page created by a banned user.',
                'db-bio':
                    'Deleting page per [[WP:CSD|CSD]] A7: '
                    'Article about a non-notable person.',
                'db-notenglish':
                    'Deleting page per [[WP:CSD|CSD]] A2: '
                    "Article isn't written in English.",
                'db-copyvio':
                    'Deleting page per [[WP:CSD|CSD]] G12: '
                    'Page is a blatant copyright violation.',
                'db-repost':
                    'Deleting page per [[WP:CSD|CSD]] G4: '
                    'Recreation of previously deleted material.',
                'db-vandalism':
                    'Deleting page per [[WP:CSD|CSD]] G3: Blatant vandalism.',
                'db-talk':
                    'Deleting page per [[WP:CSD|CSD]] G8: '
                    'Talk page of a deleted or non-existent page.',
                'db-spam':
                    'Deleting page per [[WP:CSD|CSD]] G11: '
                    'Blatant advertising.',
                'db-disparage':
                    'Deleting page per [[WP:CSD|CSD]] T1: '
                    'Divisive or inflammatory template.',
                'db-r1':
                    'Deleting page per [[WP:CSD|CSD]] R1: '
                    'Redirect to a deleted or non-existent page.',
                'db-experiment':
                    'Deleting page per [[WP:CSD|CSD]] G2: '
                    'Page was created as an experiment.',
            },
            'fa': {
                '_default':
                    'حذف مرشَّح للحذ'
                    'ف السريع حسب [[ويكيبيديا:حذف سريع|معايير الحذف السريع]]',
            },
            'he': {
                '_default':
                    'מחיקת מועמד למחיקה מהירה לפי [[ויקיפדיה:מדיניות '
                    'המחיקה|מדיניות המחיקה]]',
                'גם בוויקישיתוף': 'הקובץ זמין כעת בוויקישיתוף.',
            },
            'ja': {
                '_default': '[[WP:CSD|即時削除の方針]]に基づい削除',
            },
            'pt': {
                '_default':
                    'Apagando página por '
                    '[[Wikipedia:Páginas para eliminar|eliminação rápida]]',
            },
            'pl': {
                '_default':
                    'Usuwanie artykułu zgodnie z zasadami '
                    '[[Wikipedia:Ekspresowe kasowanko|'
                    'ekspresowego kasowania]]',
            },
            'it': {
                '_default':
                    'Rimuovo pagina che rientra nei casi di '
                    '[[Wikipedia:IMMEDIATA|cancellazione immediata]].',
            },
            'zh': {
                '_default': '[[WP:CSD]]',
                'advert': 'ad',
                'db-blanked': 'auth',
                'db-spam': '[[WP:CSD#G11|CSD G11]]: 廣告、宣傳頁面',
                'db-rediruser': '[[WP:CSD#O1|CSD O6]] 沒有在使用的討論頁',
                'notchinese': '[[WP:CSD#G7|CSD G7]]: 非中文條目且長時間未翻譯',
                'db-vandalism': 'vand',
                '翻译': 'oprj',
                '翻譯': 'oprj',
                'notmandarin': 'oprj',
                'no source':
                    '[[WP:CSD#I3|CSD I3]]: 沒有來源連結，無法確認來源與版權資訊',
                'no license':
                    '[[WP:CSD#I3|CSD I3]]: 沒有版權模板，無法確認版權資訊',
                'unknown': '[[WP:CSD#I3|CSD I3]]: 沒有版權模板，無法確認版權資訊',
                'temppage': '[[WP:CSD]]: 臨時頁面',
                'nowcommons': 'commons',
                'roughtranslation': 'mactra',
            },
        },
        'wikinews': {
            'en': {
                '_default': '[[WN:CSD]]',
            },
            'zh': {
                '_default': '[[WN:CSD]]',
            },
        },
    }

    #: Default reason for deleting a talk page.
    talk_deletion_msg = {
        'wikipedia': {
            'ar': 'صفحة نقاش يتيمة',
            'arz': 'صفحه نقاش يتيمه',
            'cs': 'Osiřelá diskusní stránka',
            'de': 'Verwaiste Diskussionsseite',
            'en': 'Orphaned talk page',
            'fa': 'بحث یتیم',
            'fr': 'Page de discussion orpheline',
            'he': 'דף שיחה של ערך שנמחק',
            'it': 'Rimuovo pagina di discussione di una pagina già cancellata',
            'pl': 'Osierocona strona dyskusji',
            'pt': 'Página de discussão órfã',
            'zh': '[[WP:CSD#O1|CSD O1 O2 O6]] 沒有在使用的討論頁',
        },
        'wikinews': {
            'en': 'Orphaned talk page',
            'zh': '[[WN:CSD#O1|CSD O1 O2 O6]] 沒有在使用的討論頁',
        }
    }

    #: A list of often-used reasons for deletion. Shortcuts are keys, and
    #: reasons are values. If the user enters a shortcut, the associated reason
    #: will be used.
    delete_reasons = {
        'wikipedia': {
            'de': {
                'asdf': 'Tastaturtest',
                'egal': 'Eindeutig irrelevant',
                'ka': 'Kein Artikel',
                'mist': 'Unsinn',
                'move': 'Redirectlöschung, um Platz für Verschiebung zu '
                        'schaffen',
                'nde': 'Nicht in deutscher Sprache verfasst',
                'pfui': 'Beleidigung',
                'redir': 'Unnötiger Redirect',
                'spam': 'Spam',
                'web': 'Nur ein Weblink',
                'wg': 'Wiedergänger (wurde bereits zuvor gelöscht)',
            },
            'it': {
                'test': 'Si tratta di un test',
                'vandalismo': 'Caso di vandalismo',
                'copyviol': 'Violazione di copyright',
                'redirect': 'Redirect rotto o inutile',
                'spam': 'Spam',
                'promo': 'Pagina promozionale',
            },
            'ja': {
                'cont': '[[WP:CSD]] 全般1 意味不明な内容のページ',
                'test': '[[WP:CSD]] 全般2 テスト投稿',
                'vand': '[[WP:CSD]] 全般3 荒らしand/orいたずら',
                'ad': '[[WP:CSD]] 全般4 宣伝',
                'rep': '[[WP:CSD]] 全般5 削除されたページの改善なき再作成',
                'cp': '[[WP:CSD]] 全般6 コピペ移動or分割',
                'sh': '[[WP:CSD]] 記事1 短すぎ',
                'nd': '[[WP:CSD]] 記事1 定義なし',
                'auth': '[[WP:CSD]] 記事3 投稿者依頼or初版立項者による白紙化',
                'nr': '[[WP:CSD]] リダイレクト1 無意味なリダイレクト',
                'nc': '[[WP:CSD]] リダイレクト2 [[WP:NC]]違反',
                'ren':
                    '[[WP:CSD]] '
                    'リダイレクト3 改名提案を経た曖昧回避括弧付きの移動の残骸',
                'commons': '[[WP:CSD]] マルチメディア7 コモンズの画像ページ',
                'tmp': '[[WP:CSD]] テンプレート1 初版投稿者依頼',
                'uau': '[[WP:CSD]] 利用者ページ1 本人希望',
                'nuu':
                    '[[WP:CSD]] '
                    '利用者ページ2 利用者登録されていない利用者ページ',
                'ipu': '[[WP:CSD]] 利用者ページ3 IPユーザの利用者ページ',
            },
            'zh': {
                'empty': '[[WP:CSD#G1]]: 沒有實際內容或歷史記錄的文章。',
                'test': '[[WP:CSD#G2]]: 測試頁',
                'vand': '[[WP:CSD#G3]]: 純粹破壞',
                'rep': '[[WP:CSD#G5]]: 經討論被刪除後又重新創建的內容',
                'repa': '[[WP:CSD#G5]]: 重複的文章',
                'oprj': '[[WP:CSD#G7]]: 內容來自其他中文計劃',
                'move':
                    '[[WP:CSD#G8]]: '
                    '依[[Wikipedia:移動請求|移動請求]]'
                    '暫時刪除以進行移動或合併頁面之工作',
                'auth': '[[WP:CSD#G10]]: 原作者請求',
                'ad': '[[WP:CSD#G11]]: 明顯的以廣告宣傳為目而建立的頁面',
                'adc': '[[WP:CSD#G11]]: 只有條目名稱中的人物或團體之聯絡資訊',
                'bio': '[[WP:CSD#G12]]: 未列明來源及語調負面的生者傳記',
                'mactra': '[[WP:CSD#G13]]: 明顯的機器翻譯',
                'notrans': '[[WP:CSD#G14]]: 未翻譯的頁面',
                'isol': '[[WP:CSD#G15]]: 孤立頁面',
                'isol-f': '[[WP:CSD#G15]]: 孤立頁面-沒有對應檔案的檔案頁面',
                'isol-sub': '[[WP:CSD#G15]]: 孤立頁面-沒有對應母頁面的子頁面',
                'tempcp': '[[WP:CSD#G16]]: 臨時頁面依然侵權',
                'cont': '[[WP:CSD#A1]]: 非常短，而且沒有定義或內容。',
                'nocont':
                    '[[WP:CSD#A2]]: '
                    '內容只包括外部連接、參見、圖書參考、類別標籤、模板標籤、'
                    '跨語言連接的條目',
                'nc': '[[WP:CSD#A3]]: 跨計劃內容',
                'cn': '[[WP:CSD#R2]]: 跨空間重定向',
                'wr': '[[WP:CSD#R3]]: 錯誤重定向',
                'slr': '[[WP:CSD#R5]]: 指向本身的重定向或循環的重定向',
                'repi': '[[WP:CSD#F1]]: 重複的檔案',
                'lssd':
                    '[[WP:CSD#F3]]: '
                    '沒有版權或來源資訊，無法確認圖片是否符合方針要求',
                'nls': '[[WP:CSD#F3]]: 沒有版權模板，無法確認版權資訊',
                'svg': '[[WP:CSD#F5]]: 被高解析度與SVG檔案取代的圖片',
                'ui': '[[WP:CSD#F6]]: 圖片未使用且不自由',
                'commons':
                    '[[WP:CSD#F7]]: '
                    '此圖片已存在於[[:commons:|維基共享資源]]',
                'urs': '[[WP:CSD#O1]]: 用戶請求刪除自己的用戶頁子頁面',
                'anou': '[[WP:CSD#O3]]: 匿名用戶的用戶討論頁，其中的內容不再有用',
                'uc': '[[WP:CSD#O4]]: 空類別',
                'tmp': '[[WP:CSD]]: 臨時頁面',
            },
        },
    }

    def __init__(self, **kwargs) -> None:
        """Initializer.

        :keyword pywikibot.APISite site: the site to work on
        """
        super().__init__(**kwargs)
        csd_cat = i18n.translate(self.site, self.csd_cat_title)
        if csd_cat is None:
            self.csd_cat = self.site.page_from_repository(self.csd_cat_item)
            if self.csd_cat is None:
                raise Error(
                    'No category for speedy deletion found for {}'
                    .format(self.site))
        else:
            self.csd_cat = pywikibot.Category(self.site, csd_cat)
        self.saved_progress = None

    def guess_reason_for_deletion(self, page):
        """Find a default reason for speedy deletion."""
        # TODO: The following check loads the page 2 times.
        # Find a better way to do it.
        if page.isTalkPage() and (page.toggleTalkPage().isRedirectPage()
                                  or not page.toggleTalkPage().exists()):
            # This is probably a talk page that is orphaned because we
            # just deleted the associated article.
            reason = i18n.translate(self.site, self.talk_deletion_msg,
                                    fallback=self.site.code != 'zh')
        else:
            # Try to guess reason by the template used
            templates = page.templatesWithParams()
            reasons = i18n.translate(self.site, self.deletion_messages)

            for template, _ in templates:
                template_name = template.title().lower()
                if template_name in reasons:
                    if not isinstance(reasons[template_name], str):
                        # Make alias to delete_reasons
                        reason = i18n.translate(
                            self.site,
                            self.delete_reasons)[reasons[template_name]]
                    else:
                        reason = reasons[template_name]
                    break
            else:
                reason = None
        if not reason:
            # Unsuccessful in guessing the reason. Use a default message.
            reason = reasons['_default']
        return reason

    def get_reason_for_deletion(self, page):
        """Get a reason for speedy deletion from operator."""
        suggested_reason = self.guess_reason_for_deletion(page)
        pywikibot.info('The suggested reason is: <<lightred>>{}'
                       .format(suggested_reason))

        # We don't use i18n.translate() here because for some languages the
        # entry is intentionally left out.
        if self.site.family.name in self.delete_reasons \
           and page.site.lang in self.delete_reasons[self.site.family.name]:
            local_reasons = i18n.translate(page.site.lang,
                                           self.delete_reasons)
            pywikibot.info()
            for key in sorted(local_reasons.keys()):
                pywikibot.info((key + ':').ljust(8) + local_reasons[key])
            pywikibot.info()
            reason = pywikibot.input(fill(
                'Please enter the reason for deletion, choose a default '
                'reason, or press enter for the suggested message:'))
            if reason.strip() in local_reasons:
                reason = local_reasons[reason]
        else:
            reason = pywikibot.input(
                'Please enter the reason for deletion,\n'
                'or press enter for the suggested message:')

        return reason or suggested_reason

    def exit(self) -> None:
        """Just call teardown after current run."""
        self.teardown()

    def run(self) -> None:
        """Start the bot's action."""
        start_ts = pywikibot.Timestamp.now()
        self.saved_progress = None
        self.quitting = False
        while True:
            super().run()
            if self.quitting:
                break

            if not self.saved_progress:
                pywikibot.info(
                    '\nThere are no (further) pages to delete.\n'
                    'Waiting for 30 seconds or press Ctrl+C to quit...')
                try:
                    time.sleep(30)
                except KeyboardInterrupt:
                    break

        self._start_ts = start_ts
        super().exit()

    def treat_page(self) -> None:
        """Process one page."""
        page = self.current_page

        color_line = '<<blue>>{}<<default>>'.format('_' * 80)
        pywikibot.info(color_line)
        pywikibot.info(page.extract('wiki', lines=self.LINES))
        pywikibot.info(color_line)

        choice = pywikibot.input_choice(
            'Input action?',
            [('delete', 'd'), ('skip', 's'), ('update', 'u'), ('quit', 'q')],
            default='s', automatic_quit=False)
        # quit the bot
        if choice == 'q':
            self.quitting = True
            self.quit()

        # stop the generator and restart from current title
        elif choice == 'u':
            pywikibot.info('Updating from CSD category.')
            self.saved_progress = page.title()
            self.stop()

        # delete the current page
        elif choice == 'd':
            reason = self.get_reason_for_deletion(page)
            pywikibot.info(f'The chosen reason is: <<lightred>>{reason}')
            page.delete(reason, prompt=False)

        # skip this page
        else:
            pywikibot.info(f'Skipping page {page}')

    def setup(self) -> None:
        """Refresh generator."""
        generator = pagegenerators.CategorizedPageGenerator(
            self.csd_cat, start=self.saved_progress)
        # wrap another generator around it so that we won't produce orphaned
        # talk pages.
        generator = pagegenerators.PageWithTalkPageGenerator(generator)
        self.generator = pagegenerators.PreloadingGenerator(generator,
                                                            groupsize=20)
        self.saved_progress = None


def main(*args: str) -> None:
    """Script entry point."""
    pywikibot.handle_args(args)  # No local args yet
    site = pywikibot.Site()
    if site.has_right('delete'):
        bot = SpeedyBot(site=site)
        bot.run()
    elif site.logged_in():
        pywikibot.info("{} does not have 'delete' right for site {}"
                       .format(site.username(), site))
    else:
        pywikibot.info('Login first.')


if __name__ == '__main__':
    main()
