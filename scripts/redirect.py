# -*- coding: utf-8 -*-
"""
Script to resolve double redirects, and to delete broken redirects. Requires
access to MediaWiki's maintenance pages or to a XML dump file. Delete
function requires adminship.

Syntax:

    python redirect.py action [-arguments ...]

where action can be one of these:

double         Fix redirects which point to other redirects
broken         Delete redirects where targets don\'t exist. Requires adminship.
both           Both of the above. Permitted only with -api. Implies -api.

and arguments can be:

-moves         Use the page move log to find double-redirect candidates. Only
               works with action "double".

-namespace:n   Namespace to process. Can be given multiple times, for several
               namespaces.  If omitted, only the main (article) namespace is
               treated.

-offset:n      With -moves, the number of hours ago to start scanning moved
               pages. Otherwise, ignored.

-start:title   The starting page title in each namespace. Page need not exist.

-until:title   The possible last page title in each namespace. Page needs not
               exist.

-total:n       The maximum count of redirects to work upon. If omitted, there
               is no limit.

-always        Don't prompt you for each replacement.

"""

# XML not yet implemented: deleted help text follows
##-xml           Retrieve information from a local XML dump
##               (http://download.wikimedia.org). Argument can also be given as
##               "-xml:filename.xml". Cannot be used with -api or -moves.
##               If neither of -xml -api -moves is given, info will be loaded
##               from a special page of the live wiki.

#
# (C) Daniel Herding, 2004.
#     Purodha Blissenbach, 2009.
#
# Distributed under the terms of the MIT license.
#
#
import pywikibot
from pywikibot import config
# import xmlreader
import re, sys

__version__='$Id: redirect.py 7789 2009-12-17 19:20:12Z xqt $'

# Summary message for fixing double redirects
msg_double={
    'als':u'Bötli: Uflösig vun de doppleti Wyterleitig zue %s',
    'ar': u'روبوت: تصليح تحويلة مزدوجة → %s',
    'bat-smg': u'Robots: Taisuoms dvėgobs paradresavėms → %s',
    'be-x-old': u'Робат: выпраўленьне падвойнага перанакіраваньня → %s',
    'br': u'Kempennet adkas doubl gant robot → %s',
    'cs': u'Robot opravil dvojité přesměrování → %s',
    'de': u'Bot: Korrigiere doppelte Weiterleitung zu %s',
    'en': u'Robot: Fixing double redirect to %s',
    'es': u'Robot: Arreglando doble redirección → %s',
    'fa': u'ربات:اصلاح تغییر مسیر دوتایی → %s',
    'fi': u'Botti korjasi kaksinkertaisen ohjauksen → %s',
    'fr': u'Robot: répare double redirection à %s',
    'ga': u'Róbó: Ag socrú athsheolta dúbailte → %s',
    'he': u'בוט: מתקן הפניה כפולה → %s',
    'hr': u'Bot: Popravak dvostrukih preusmjeravanja → %s',
    'ia': u'Robot: reparation de duple redirection → %s',
    'is': u'Vélmenni: Lagfæri tvöfalda tilvísun → %s',
    'it': u'Bot: Sistemo i redirect doppi a %s',
    'ja': u'ロボットによる: 二重リダイレクト修正 → %s',
    'ka': u'რობოტი: ორმაგი გადამისამართების გასწორება → %s',
    'ko': u'로봇: 이중 넘겨주기 수정 → %s',
    'kk': u'Бот: Шынжырлы айдатуды түзетті → %s',
    'ksh':u'Bot: [[special:doubleredirects|Dubbel Ömlëijdong]] fottjemaat → %s',
    'lb': u'Bot: Duebel Viruleedung gefléckt → %s',
    'lt': u'robotas: Taisomas dvigubas peradresavimas → %s',
    'mk': u'Бот: Исправка на двојни пренасочувања → %s',
    'nds':u'Bot: Dubbelte Wiederleiden rutmakt → %s',
    'nl': u'Bot: dubbele doorverwijzing gecorrigeerd aan %s',
    'nn': u'robot: retta dobbel omdirigering → %s',
    'no': u'bot: Retter dobbel omdirigering → %s',
    'pl': u'Robot naprawia podwójne przekierowanie → %s',
    'pt': u'Bot: Corrigido duplo redirecionamento → %s',
    'ru': u'Робот: исправление двойного перенаправления → %s',
    'sr': u'Бот: Поправка дуплих преусмерења → %s',
    'sv': u'Robot: Rättar dubbel omdirigering → %s',
    'szl':u'Robot sprowjo tuplowane przekerowańa → %s',
    'th': u'โรบอต: แก้หน้าเปลี่ยนทางซ้ำซ้อน → %s',
    'tr': u'Bot değişikliği: Yönlendirmeye olan yönlendirme → %s',
    'uk': u'Робот: виправлення подвійного перенаправлення → %s',
    'war':u'Robot: Gin-ayad in nagduduha nga redirek → %s',
    'yi': u'באט: פארראכטן פארטאפלטע ווייטערפירונג → %s',
    'zh': u'機器人:修正雙重重定向 → %s',
    'zh-yue': u'機械人：拉直連串跳轉 → %s',
    'zh-classical': u'僕:復修渡口 → %s',
}

# Reason for deleting broken redirects
reason_broken={
    'ar': u'روبوت: هدف التحويلة غير موجود',
    'als': u'Wyterleitig wo kaputt isch', 
    'be-x-old': u'Робат: мэта перанакіраваньня не існуе',
    'cs': u'Přerušené přesměrování',
    'de': u'Bot: Weiterleitungsziel existiert nicht',
    'en': u'[[WP:CSD#G8|G8]]: [[Wikipedia:Redirect|Redirect]] to a deleted or non-existent page',
    'es': u'Robot: La página a la que redirige no existe',
    'fa': u'ربات:تغییرمسیر مقصد ندارد',
    'fi': u'Botti: Ohjauksen kohdesivua ei ole olemassa',
    'fr': u'Robot : Cible du redirect inexistante',
    'ga': u'Róbó : Targaid athsheoladh ar iarraidh',
    'he': u'בוט: יעד ההפניה אינו קיים',
    'it': u'Bot: Il redirect indirizza ad una pagina inesistente',
    'ja': u'ロボットによる:リダイレクトの目標は存在しませんでした',
    'ka': u'რობოტი: გადამისამართებული გვერდი არ არსებობს',
    'ko': u'로봇: 끊긴 넘겨주기',
    'kk': u'Бот: Айдату нысанасы жоқ болды',
    'ksh':u'Bot: Dė [[Special:BrokenRedirects|Ömlëijdong jingk ennet Liiere]]',
    'lt': u'robotas: Peradresavimas į niekur',
    'nds':u'Bot: Kaputte Wiederleiden ward nich brukt',
    'nl': u'Bot: doelpagina doorverwijzing bestaat niet',
    'nn': u'robot: målet for omdirigeringa eksisterer ikkje',
    'no': u'robot: målet for omdirigeringen eksisterer ikke',
    'pl': u'Robot: cel przekierowania nie istnieje',
    'pt': u'Bot: Redirecionamento não existe',
    'ru': u'Робот: перенаправление в никуда',
    'sr': u'Бот: Преусмерење не постоји',
    'th': u'โรบอต: หน้าเปลี่ยนทางเสีย',
    'tr': u'Bot değişikliği: Var olmayan sayfaya olan yönlendirme',
    'war':u'Robot: Waray dida an karadto-an han redirek',
    'yi': u'באט: ווײַטערפֿירן ציל עקזיסטירט נישט',
    'zh': u'機器人:該重定向的目標不存在',
    'zh-yue': u'機械人：跳轉目標唔存在',
}

# Summary message for putting broken redirect to speedy delete
sd_tagging_sum = {
    'ar': u'روبوت: وسم للحذف السريع',
    'cs': u'Robot označil ke smazání',
    'en': u'Robot: Tagging for speedy deletion',
    'ga': u'Róbó: Ag maircáil le luas-scrios',
    'it': u'Bot: +Da cancellare subito',
    'ja': u'ロボットによる:迷子のリダイレクトを即時削除へ',
    'ksh':u'Bot: Di Ömlëijdong jeiht noh nörjendwoh.',
    'nds':u'Bot: Kaputte Wiederleiden ward nich brukt',
    'nl': u'Bot: gemarkeerd voor snelle verwijdering',
    'war':u'Robot: Nautod o nagbinalikbalik nga redirek',
    'zh': u'機器人: 將損壞的重定向提報快速刪除',
}

# Insert deletion template into page with a broken redirect
sd_template = {
    'ar': u'{{شطب|تحويلة مكسورة}}',
    'als':u'{{delete}}Wyterleitig wo kaputt isch--~~~~', 
    'bar':u'{{delete}}Kaputte Weiterleitung--~~~~', 
    'de': u'{{sla|Defekte Weiterleitung --~~~~}}',
    'cs': u'{{smazat|přerušené přesměrování}}',
    'en': u'{{db-r1}}',
    'ga': u'{{scrios|Athsheoladh briste}}',
    'it': u'{{Cancella subito|9}}',
    'ja': u'{{即時削除|壊れたリダイレクト}}',
    'ksh':u'{{Schmieß fott}}Di Ömlëijdong jeiht noh nörjendwoh hen.<br />--~~~~~\n\n',
    'nds':u'{{delete}}Kaputte Wiederleiden, wat nich brukt ward.<br />--~~~~\n\n',
    'pdc':u'{{lösche|Defekte Weiterleitung --~~~~}}',
    'war':u'{{delete}}Nautod o nagbinalikbalik nga redirek.--~~~~\n\n',
    'zh': u'{{delete|R1}}',
}

class RedirectGenerator:
    def __init__(self, xmlFilename=None, namespaces=[], offset=-1,
                 use_move_log=False, use_api=False, start=None, until=None,
                 number=None):
        self.site = pywikibot.getSite()
##        self.xmlFilename = xmlFilename
        self.namespaces = namespaces
        if use_api and self.namespaces == []:
            self.namespaces = [ 0 ]
        self.offset = offset
        self.use_move_log = use_move_log
        self.use_api = use_api
        self.api_start = start
        self.api_until = until
        self.api_number = number

##    def get_redirects_from_dump(self, alsoGetPageTitles=False):
##        '''
##        Load a local XML dump file, look at all pages which have the
##        redirect flag set, and find out where they're pointing at. Return
##        a dictionary where the redirect names are the keys and the redirect
##        targets are the values.
##        '''
##        xmlFilename = self.xmlFilename
##        redict = {}
##        # open xml dump and read page titles out of it
##        dump = xmlreader.XmlDump(xmlFilename)
##        redirR = self.site.redirectRegex()
##        readPagesCount = 0
##        if alsoGetPageTitles:
##            pageTitles = set()
##        for entry in dump.parse():
##            readPagesCount += 1
##            # always print status message after 10000 pages
##            if readPagesCount % 10000 == 0:
##                pywikibot.output(u'%i pages read...' % readPagesCount)
##            if len(self.namespaces) > 0:
##                if pywikibot.Page(self.site, entry.title).namespace() \
##                        not in self.namespaces:
##                    continue
##            if alsoGetPageTitles:
##                pageTitles.add(entry.title.replace(' ', '_'))
##
##            m = redirR.match(entry.text)
##            if m:
##                target = m.group(1)
##                # There might be redirects to another wiki. Ignore these.
##                for code in self.site.family.langs.keys():
##                    if target.startswith('%s:' % code) \
##                            or target.startswith(':%s:' % code):
##                        if code == self.site.language():
##                        # link to our wiki, but with the lang prefix
##                            target = target[(len(code)+1):]
##                            if target.startswith(':'):
##                                target = target[1:]
##                        else:
##                            pywikibot.output(
##                                u'NOTE: Ignoring %s which is a redirect to %s:'
##                                % (entry.title, code))
##                            target = None
##                            break
##                # if the redirect does not link to another wiki
##                if target:
##                    source = entry.title.replace(' ', '_')
##                    target = target.replace(' ', '_')
##                    # remove leading and trailing whitespace
##                    target = target.strip('_')
##                    # capitalize the first letter
##                    if not pywikibot.getSite().nocapitalize:
##                        source = source[:1].upper() + source[1:]
##                        target = target[:1].upper() + target[1:]
##                    if '#' in target:
##                        target = target[:target.index('#')].rstrip("_")
##                    if '|' in target:
##                        pywikibot.output(
##                            u'HINT: %s is a redirect with a pipelink.'
##                            % entry.title)
##                        target = target[:target.index('|')].rstrip("_")
##                    if target: # in case preceding steps left nothing
##                        redict[source] = target
##        if alsoGetPageTitles:
##            return redict, pageTitles
##        else:
##            return redict
##
    def get_redirect_pages_via_api(self):
        """Return generator that yields Pages that are redirects."""
        for ns in self.namespaces:
            done = False
            gen = self.site.allpages(start=self.api_start,
                                     namespace=ns,
                                     filterredir=True)
            if self.api_number:
                gen.set_maximum_items(self.api_number)
            for p in gen:
                done = self.api_until \
                           and p.title(withNamespace=False) >= self.api_until
                if done:
                    return
                yield p

    def _next_redirect_group(self):
        """
        Return a generator that retrieves pageids from the API 500 at a time
        and yields them as a list
        """
        apiQ = []
        for page in self.get_redirect_pages_via_api():
            apiQ.append(str(page._pageid))
            if len(apiQ) >= 500:
                yield apiQ
                apiQ = []
        if apiQ:
            yield apiQ

    def get_redirects_via_api(self, maxlen=8):
        """
        Return a generator that yields tuples of data about redirect Pages:
            0 - page title of a redirect page
            1 - type of redirect:
                         0 - broken redirect, target page title missing
                         1 - normal redirect, target page exists and is not a
                             redirect
                 2..maxlen - start of a redirect chain of that many redirects
                             (currently, the API seems not to return sufficient
                             data to make these return values possible, but
                             that may change)
                  maxlen+1 - start of an even longer chain, or a loop
                             (currently, the API seems not to return sufficient
                             data to allow this return values, but that may
                             change)
                      None - start of a redirect chain of unknown length, or loop
            2 - target page title of the redirect, or chain (may not exist)
            3 - target page of the redirect, or end of chain, or page title where
                chain or loop detecton was halted, or None if unknown
        """
        for apiQ in self._next_redirect_group():
            gen = pywikibot.data.api.Request(action="query", redirects="",
                                             pageids=apiQ)
            data = gen.submit()
            if 'error' in data:
                raise RuntimeError("API query error: %s" % data)
            if data == [] or "query" not in data:
                raise RuntimeError("No results given.")
            redirects = {}
            pages = {}
            redirects = dict((x['from'], x['to'])
                             for x in data['query']['redirects'])

            for pagetitle in data['query']['pages'].values():
                if 'missing' in pagetitle and 'pageid' not in pagetitle:
                    pages[pagetitle['title']] = False
                else:
                    pages[pagetitle['title']] = True
            for redirect in redirects:
                target = redirects[redirect]
                result = 0
                final = None
                try:
                    if pages[target]:
                        final = target
                        try:
                            while result <= maxlen:
                               result += 1
                               final = redirects[final]
                            # result = None
                        except KeyError:
                            pass
                except KeyError:
                    result = None
                    pass
                yield (redirect, result, target, final)

    def retrieve_broken_redirects(self):
        if self.use_api:
            count = 0
            for (pagetitle, type, target, final) \
                    in self.get_redirects_via_api(maxlen=2):
                if type == 0:
                    yield pagetitle
                    if self.api_number:
                        count += 1
                        if count >= self.api_number:
                            break

##        elif self.xmlFilename == None:
##            # retrieve information from the live wiki's maintenance page
##            # broken redirect maintenance page's URL
##            path = self.site.broken_redirects_address(default_limit=False)
##            pywikibot.output(u'Retrieving special page...')
##            maintenance_txt = self.site.getUrl(path)
##
##            # regular expression which finds redirects which point to a
##            # non-existing page inside the HTML
##            Rredir = re.compile('\<li\>\<a href=".+?" title="(.*?)"')
##
##            redir_names = Rredir.findall(maintenance_txt)
##            pywikibot.output(u'Retrieved %d redirects from special page.\n'
##                             % len(redir_names))
##            for redir_name in redir_names:
##                yield redir_name
##        else:
##            # retrieve information from XML dump
##            pywikibot.output(
##                u'Getting a list of all redirects and of all page titles...')
##            redirs, pageTitles = self.get_redirects_from_dump(
##                                            alsoGetPageTitles=True)
##            for (key, value) in redirs.iteritems():
##                if value not in pageTitles:
##                    yield key

    def retrieve_double_redirects(self):
        if self.use_move_log:
            for redir_page in self.get_moved_pages_redirects():
                yield redir_page.title()
            return
        else:
            count = 0
            for (pagetitle, type, target, final) \
                    in self.get_redirects_via_api(maxlen=2):
                if type != 0 and type != 1:
                    yield pagetitle
                    if self.api_number:
                        count += 1
                        if count >= self.api_number:
                            break

##        elif self.xmlFilename == None:
##            # retrieve information from the live wiki's maintenance page
##            # double redirect maintenance page's URL
###            pywikibot.config.special_page_limit = 1000
##            path = self.site.double_redirects_address(default_limit = False)
##            pywikibot.output(u'Retrieving special page...')
##            maintenance_txt = self.site.getUrl(path)
##
##            # regular expression which finds redirects which point to
##            # another redirect inside the HTML
##            Rredir = re.compile('\<li\>\<a href=".+?" title="(.*?)">')
##            redir_names = Rredir.findall(maintenance_txt)
##            pywikibot.output(u'Retrieved %i redirects from special page.\n'
##                             % len(redir_names))
##            for redir_name in redir_names:
##                yield redir_name
##        else:
##            redict = self.get_redirects_from_dump()
##            num = 0
##            for (key, value) in redict.iteritems():
##                num += 1
##                # check if the value - that is, the redirect target - is a
##                # redirect as well
##                if num > self.offset and value in redict:
##                    yield key
##                    pywikibot.output(u'\nChecking redirect %i of %i...'
##                                     % (num + 1, len(redict)))

    def get_moved_pages_redirects(self):
        '''generate redirects to recently-moved pages'''
        # this will run forever, until user interrupts it
        import datetime

        if self.offset <= 0:
            self.offset = 1
        start = datetime.datetime.utcnow() \
                - datetime.timedelta(0, self.offset*3600)
        # self.offset hours ago
        offset_time = start.strftime("%Y%m%d%H%M%S")

        move_gen = self.site.logevents(logtype="move", start=offset_time)
        if self.api_number:
            move_gen.set_maximum_items(self.api_number)
        for logentry in move_gen:
            moved_page = logentry.title()
            try:
                if not moved_page.isRedirectPage():
                    continue
            except pywikibot.BadTitle:
                continue
            except pywikibot.ServerError:
                continue
            # moved_page is now a redirect, so any redirects pointing
            # to it need to be changed
            try:
                for page in moved_page.getReferences(follow_redirects=True,
                                                     redirectsOnly=True):
                    yield page
            except pywikibot.NoPage:
                # original title must have been deleted after move
                continue


class RedirectRobot:
    def __init__(self, action, generator, always=False, number=None):
        self.site = pywikibot.getSite()
        self.action = action
        self.generator = generator
        self.always = always
        self.number = number
        self.exiting = False

    def prompt(self, question):
        if not self.always:
            choice = pywikibot.inputChoice(question,
                                           ['Yes', 'No', 'All', 'Quit'],
                                           ['y', 'N', 'a', 'q'], 'N')
            if choice == 'n':
                return False
            elif choice == 'q':
                self.exiting = True
                return False
            elif choice == 'a':
                self.always = True
        return True

    def delete_broken_redirects(self):
        # get reason for deletion text
        reason = pywikibot.translate(self.site, reason_broken)
        for redir_name in self.generator.retrieve_broken_redirects():
            self.delete_1_broken_redirect( redir_name, reason)
            if self.exiting:
                break

    def delete_1_broken_redirect(self, redir_name, reason):
            redir_page = pywikibot.Page(self.site, redir_name)
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                              % redir_page.title())
            try:
                targetPage = redir_page.getRedirectTarget()
            except pywikibot.IsNotRedirectPage:
                pywikibot.output(u'%s is not a redirect.' % redir_page.title())
            except pywikibot.NoPage:
                pywikibot.output(u'%s doesn\'t exist.' % redir_page.title())
            else:
                try:
                    targetPage.get()
                except pywikibot.NoPage:
                    if self.prompt(
            u'Redirect target %s does not exist. Do you want to delete %s?'
                                   % (targetPage.title(asLink=True),
                                      redir_page.title(asLink=True))):
                        try:
                            redir_page.delete(reason, prompt = False)
                        except pywikibot.NoUsername:
                            if targetPage.site().lang in sd_template \
                                    and targetPage.site().lang in sd_tagging_sum:
                                pywikibot.output(
            u"No sysop in user-config.py, put page to speedy deletion.")
                                content = redir_page.get(get_redirect=True)
                                content = pywikibot.translate(
                                    targetPage.site().lang,
                                    sd_template)+"\n"+content
                                summary = pywikibot.translate(
                                    targetPage.site().lang,
                                    sd_tagging_sum)
                                redir_page.put(content, summary)

                except pywikibot.IsRedirectPage:
                    pywikibot.output(
            u'Redirect target %s is also a redirect! Won\'t delete anything.'
                        % targetPage.title(asLink=True))
                else:
                    #we successfully get the target page, meaning that
                    #it exists and is not a redirect: no reason to touch it.
                    pywikibot.output(
            u'Redirect target %s does exist! Won\'t delete anything.'
                        % targetPage.title(asLink=True))
            pywikibot.output(u'')

    def fix_double_redirects(self):
        for redir_name in self.generator.retrieve_double_redirects():
            self.fix_1_double_redirect(redir_name)
            if self.exiting:
                break

    def fix_1_double_redirect(self,  redir_name):
            redir = pywikibot.Page(self.site, redir_name)
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                              % redir.title())
            newRedir = redir
            redirList = []  # bookkeeping to detect loops
            while True:
                redirList.append(u'%s:%s' % (newRedir.site().lang,
                                             newRedir.title(withSection=False)))
                try:
                    targetPage = newRedir.getRedirectTarget()
                except pywikibot.IsNotRedirectPage:
                    if len(redirList) == 1:
                        pywikibot.output(u'Skipping: Page %s is not a redirect.'
                                         % redir.title(asLink=True))
                        break  #do nothing
                    elif len(redirList) == 2:
                        pywikibot.output(
                            u'Skipping: Redirect target %s is not a redirect.'
                            % newRedir.title(asLink=True))
                        break  # do nothing
                except pywikibot.SectionError:
                    pywikibot.output(
                        u'Warning: Redirect target section %s doesn\'t exist.'
                          % newRedir.title(asLink=True))
                except pywikibot.BadTitle, e:
                    # str(e) is in the format 'BadTitle: [[Foo]]'
                    pywikibot.output(
                        u'Warning: Redirect target %s is not a valid page title.'
                          % str(e)[10:])
                #sometimes this error occures. Invalid Title starting with a '#'
                except pywikibot.InvalidTitle, err:
                    pywikibot.output(u'Warning: %s' % err)
                    break
                except pywikibot.NoPage:
                    if len(redirList) == 1:
                        pywikibot.output(u'Skipping: Page %s does not exist.'
                                            % redir.title(asLink=True))
                        break
                    else:
                        if self.always:
                            pywikibot.output(
                                u"Skipping: Redirect target %s doesn't exist."
                                % newRedir.title(asLink=True))
                            break  # skip if automatic
                        else:
                            pywikibot.output(
                                u"Warning: Redirect target %s doesn't exist."
                                % newRedir.title(asLink=True))
                except pywikibot.ServerError:
                    pywikibot.output(u'Skipping: Server Error')
                    break
                else:
                    pywikibot.output(
                        u'   Links to: %s.'
                          % targetPage.title(asLink=True))
                    if targetPage.site() != self.site:
                        pywikibot.output(
                u'Warning: redirect target (%s) is on a different site.'
                             % (targetPage.title(asLink=True)))
                        if self.always:
                            break  # skip if automatic
                    # watch out for redirect loops
                    if redirList.count(u'%s:%s'
                                       % (targetPage.site().lang,
                                          targetPage.title(withSection=False))
                                      ) > 0:
                        pywikibot.output(
                           u'Warning: Redirect target %s forms a redirect loop.'
                              % targetPage.title(asLink=True))
                        break ###xqt doesn't work. edits twice!
                        try:
                            content = targetPage.get(get_redirect=True)
                        except pywikibot.SectionError:
                            content = pywikibot.Page(
                                          targetPage.site(),
                                          targetPage.title(withSection=False)
                                      ).get(get_redirect=True)
                        if targetPage.site().lang in sd_template \
                                and targetPage.site().lang in sd_tagging_sum:
                            pywikibot.output(u"Tagging redirect for deletion")
                            # Delete the two redirects
                            content = pywikibot.translate(
                                        targetPage.site().lang,
                                        sd_template)+"\n"+content
                            summ = pywikibot.translate(targetPage.site().lang,
                                                       sd_tagging_sum)
                            targetPage.put(content, summ)
                            redir.put(content, summ)
                        break # TODO Better implement loop redirect
                    else:
                        newRedir = targetPage
                        continue
                try:
                    oldText = redir.get(get_redirect=True)
                except pywikibot.BadTitle:
                    pywikibot.output(u"Bad Title Error")
                    break
                text = self.site.redirectRegex().sub(
                        '#%s %s' %
                            (self.site.redirect( True ),
                             targetPage.title(asLink=True)),
                        oldText)
                if text == oldText:
                    break
                summary = pywikibot.translate(self.site, msg_double)\
                          % targetPage.title(asLink=True)
                pywikibot.showDiff(oldText, text)
                if self.prompt(u'Do you want to accept the changes?'):
                    try:
                        redir.put(text, summary)
                    except pywikibot.LockedPage:
                        pywikibot.output(u'%s is locked.' % redir.title())
                    except pywikibot.SpamfilterError, error:
                        pywikibot.output(
                            u"Saving page [[%s]] prevented by spam filter: %s"
                             % (redir.title(), error.url))
                    except pywikibot.PageNotSaved, error:
                        pywikibot.output(u"Saving page [[%s]] failed: %s"
                             % (redir.title(), error))
                    except pywikibot.NoUsername:
                        pywikibot.output(
                            u"Page [[%s]] not saved; sysop privileges required."
                             % redir.title())
                    except pywikibot.Error, error:
                        pywikibot.output(
                        u"Unexpected error occurred trying to save [[%s]]: %s"
                             % (redir.title(), error))
                break

    def fix_double_or_delete_broken_redirects(self):
        # TODO: part of this should be moved to generator, the rest merged into self.run()
        # get reason for deletion text
        delete_reason = pywikibot.translate(self.site, reason_broken)
        count = 0
        for (redir_name, code, target, final)\
                in self.generator.get_redirects_via_api(maxlen=2):
            if code == 1:
                continue
            elif code == 0:
                self.delete_1_broken_redirect(redir_name, delete_reason)
                count += 1
            else:
                self.fix_1_double_redirect(redir_name)
                count += 1
            if self.exiting or (self.number and count >= self.number):
                break

    def run(self):
        # TODO: make all generators return a redirect type indicator,
        #       thus make them usable with 'both'
        if self.action == 'double':
            self.fix_double_redirects()
        elif self.action == 'broken':
            self.delete_broken_redirects()
        elif self.action == 'both':
            self.fix_double_or_delete_broken_redirects()

def main(*args):
    # read command line parameters
    # what the bot should do (either resolve double redirs, or delete broken
    # redirs)
    action = None
    # where the bot should get his infos from (either None to load the
    # maintenance special page from the live wiki, or the filename of a
    # local XML dump file)
    xmlFilename = None
    # Which namespace should be processed when using a XML dump
    # default to -1 which means all namespaces will be processed
    namespaces = []
    # at which redirect shall we start searching double redirects again
    # (only with dump); default to -1 which means all redirects are checked
    offset = -1
    moved_pages = False
    api = True  # rewrite always uses api, probably should get rid of this
    start = ''
    until = ''
    number = None
    always = False
    for arg in pywikibot.handleArgs(*args):
        if arg == 'double' or arg == 'do':
            action = 'double'
        elif arg == 'broken' or arg == 'br':
            action = 'broken'
        elif arg == 'both':
            action = 'both'
        elif arg.startswith('-xml'):
            if len(arg) == 4:
                xmlFilename = pywikibot.input(
                                u'Please enter the XML dump\'s filename: ')
            else:
                xmlFilename = arg[5:]
        elif arg.startswith('-moves'):
            moved_pages = True
        elif arg.startswith('-namespace:'):
            ns = arg[11:]
            if ns == '':
        ## "-namespace:" does NOT yield -namespace:0 further down the road!
                ns = pywikibot.input(
                        u'Please enter a namespace by its number: ')
#                       u'Please enter a namespace by its name or number: ')
#  TODO! at least for some generators.
            if ns == '':
               ns = '0'
            try:
                ns = int(ns)
            except ValueError:
#-namespace:all Process all namespaces. Works only with the API read interface.
               pass
            if not ns in namespaces:
               namespaces.append(ns)
        elif arg.startswith('-offset:'):
            offset = int(arg[8:])
        elif arg.startswith('-start:'):
            start = arg[7:]
        elif arg.startswith('-until:'):
            until = arg[7:]
        elif arg.startswith('-total:'):
            number = int(arg[8:])
        elif arg == '-always':
            always = True
        else:
            pywikibot.output(u'Unknown argument: %s' % arg)

    if xmlFilename:
        pywikibot.error(u"Sorry, xmlreader is not yet implemented in rewrite")
    elif not action: # or (xmlFilename and moved_pages)
                     # or (api and xmlFilename):
        pywikibot.showHelp('redirect')
    else:
        gen = RedirectGenerator(xmlFilename, namespaces, offset, moved_pages,
                                api, start, until, number)
        bot = RedirectRobot(action, gen, always, number)
        bot.run()

if __name__ == '__main__':
    try:
        main()
    finally:
        pywikibot.stopme()
