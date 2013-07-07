#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script understands various command-line arguments:

-interactive:     ask before changing each page

-nocache          doesn't include /cache/featured /cache/lists or /cache/good
                  file to remember if the article already was verified.

-fromlang:xx,yy   xx,yy,zz,.. are the languages to be verified.
-fromlang:ar--fi  Another possible with range the languages

-fromall          to verify all languages.

-after:zzzz       process pages after and including page zzzz

-side             use -side if you want to move all {{Link FA|lang}} next to the
                  corresponding interwiki links. Default is placing
                  {{Link FA|lang}} on top of the interwiki links.

-count            Only counts how many featured/good articles exist
                  on all wikis (given with the "-fromlang" argument) or
                  on several language(s) (when using the "-fromall" argument).
                  Example: featured.py -fromlang:en,he -count
                  counts how many featured articles exist in the en and he
                  wikipedias.

-lists            use this script for featured lists.

-good             use this script for good articles.

-former           use this script for removing {{Link FA|xx}} from former
                  fearured articles

-quiet            no corresponding pages are displayed.

usage: featured.py [-interactive] [-nocache] [-top] [-after:zzzz] [-fromlang:xx,yy--zz|-fromall]

"""
__version__ = '$Id$'

#
# (C) Maxim Razin, 2005
# (C) Leonardo Gregianin, 2005-2008
# (C) xqt, 2009-2012
# (C) Pywikipedia bot team, 2005-2012
#
# Distributed under the terms of the MIT license.
#

import sys, re, pickle, os.path
from copy import copy
import wikipedia as pywikibot
from pywikibot import i18n
import catlib, config
from pagegenerators import PreloadingGenerator

def CAT(site, name, hide):
    name = site.namespace(14) + ':' + name
    cat=catlib.Category(site, name)
    for article in cat.articles(endsort=hide):
        yield article
    if hide:
        for article in cat.articles(startFrom=unichr(ord(hide)+1)):
            yield article

def BACK(site, name, hide):
    p=pywikibot.Page(site, name, defaultNamespace=10)
    return [page for page in p.getReferences(follow_redirects=False,
                                             onlyTemplateInclusion=True)]

# ALL wikis use 'Link FA', and sometimes other localized templates.
# We use _default AND the localized ones
template = {
    '_default': ['Link FA'],
    'als': ['LinkFA'],
    'an': ['Destacato', 'Destacau'],
    'ar': [u'وصلة مقالة مختارة'],
    'ast':['Enllaz AD'],
    'az': ['Link FM'],
    'br': ['Liamm PuB', 'Lien AdQ'],
    'ca': [u'Enllaç AD', 'Destacat'],
    'cy': ['Cyswllt erthygl ddethol', 'Dolen ED'],
    'eo': ['LigoElstara'],
    'en': ['Link FA', 'FA link'],
    'es': ['Destacado'],
    'eu': ['NA lotura'],
    'fr': ['Lien AdQ'],
    'fur':['Leam VdC'],
    'ga': ['Nasc AR'],
    'hi': ['Link FA', 'Lien AdQ'],
    'is': [u'Tengill ÚG'],
    'it': ['Link AdQ'],
    'no': ['Link UA'],
    'oc': ['Ligam AdQ', 'Lien AdQ'],
    'ro': [u'Legătură AC', u'Legătură AF'],
    'sv': ['UA', 'Link UA'],
    'tr': ['Link SM'],
    'vi': [u'Liên kết chọn lọc'],
    'vo': [u'Yüm YG'],
    'yi': [u'רא'],
}

template_good = {
    '_default': ['Link GA'],
    'ar': [u'وصلة مقالة جيدة'],
    'da': ['Link GA', 'Link AA'],
    'eo': ['LigoLeginda'],
    'es': ['Bueno'],
    'fr': ['Lien BA'],
    'is': ['Tengill GG'],
    'it': ['Link VdQ'],
    'nn': ['Link AA'],
    'no': ['Link AA'],
    'pt': ['Bom interwiki'],
   #'tr': ['Link GA', 'Link KM'],
    'vi': [u'Liên kết bài chất lượng tốt'],
    'wo': ['Lien BA'],
}

template_lists = {
    '_default': ['Link FL'],
    'no': ['Link GL'],
}

featured_name = {
    'af': (BACK,u"Voorbladster"),
    'als':(CAT, u"Wikipedia:Bsunders glungener Artikel"),
    'am': (CAT, u"Wikipedia:Featured article"),
    'an': (CAT, u"Articlos destacatos"),
    'ang':(CAT, u"Fulgōd ȝeƿritu"),
    'ar': (CAT, u"مقالات مختارة"),
    'ast':(CAT, u"Uiquipedia:Artículos destacaos"),
    'az': (BACK,u"Seçilmiş məqalə"),
    'bar':(CAT, u"Berig"),
    'bat-smg': (CAT, u"Vikipedėjės pavīzdėnē straipsnē"),
    'be-x-old':(CAT, u"Вікіпэдыя:Абраныя артыкулы"),
    'bg': (CAT, u"Избрани статии"),
    'bn': (BACK,u"নির্বাচিত নিবন্ধ"),
    'br': (CAT, u"Pennadoù eus an dibab"),
    'bs': (CAT, u"Odabrani članci"),
    'ca': (CAT, u"Llista d'articles de qualitat"),
    'ceb':(CAT, u"Mga napiling artikulo"),
    'cs': (CAT, u"Wikipedie:Nejlepší články"),
    'cy': (BACK,u"Erthygl ddethol"),
    'da': (CAT, u"Fremragende artikler"),
    'de': (CAT, u"Wikipedia:Exzellent"),
    'dv': (BACK, u"Featured article"),
    'el': (BACK,u"Αξιόλογο άρθρο"),
    'en': (CAT, u"Featured articles"),
    'eo': (CAT, u"Elstaraj artikoloj"),
    'es': (BACK, u"Artículo destacado"),
    'et': (CAT, u"Eeskujulikud artiklid"),
    'eu': (CAT, u"Nabarmendutako artikuluak"),
    'ext':(BACK,u"Destacau"),
    'fa': (BACK,u"مقاله برگزیده"),
    'fi': (CAT, u"Suositellut sivut"),
    'fo': (CAT, u"Mánaðargrein"),
    'fr': (CAT, u"Article de qualité"),
    'frr':(BACK,u"Exzellent"),
    'gl': (CAT, u"Wikipedia:Artigos de calidade"),
    'gv': (CAT, u"Artyn reiht"),
    'he': (CAT, u"ערכים מומלצים"),
    'hi': (BACK,u"निर्वाचित लेख"),
    'hr': (CAT, u"Izabrani članci"),
    'hsb':(CAT, u"Ekscelentny"),
    'hu': (CAT, u"Kiemelt cikkek"),
    'hy': (BACK,u"Ընտրված հոդված"),
    'ia': (CAT, u"Wikipedia:Articulos eminente"),
    'id': (BACK, u"Featured article"),
    'is': (CAT, u"Wikipedia:Úrvalsgreinar"),
    'it': (CAT, u"Voci in vetrina"),
    'ja': (BACK,u"Featured article"),
    'ka': (CAT, u"რჩეული სტატიები"),
    'kk': (CAT, u"Уикипедия:Таңдаулы мақалалар"),
    'kl': (CAT, u"Anbefalet"),
    'km': (BACK,u"អត្ថបទពិសេស"),
    'kn': (BACK,u"ವಿಶೇಷ ಲೇಖನ"),
    'ko': (CAT, u"알찬 글"),
    'krc':(CAT, u"Википедия:Сайланнган статьяла"),
    'kv': (CAT, u"Википедия:Бур гижӧдъяс"),
    'la': (CAT, u"Paginae mensis"),
    'lad':(CAT, u"Artikolos valutosos"),
    'li': (CAT, u"Wikipedia:Sjterartikele"),
    'lmo':(CAT, u"Articol ben faa"),
    'lo': (CAT, u"ບົດຄວາມດີເດັ່ນ"),
    'lt': (CAT, u"Vikipedijos pavyzdiniai straipsniai"),
    'lv': (CAT, u"Vērtīgi raksti"),
    'mk': (BACK, u"Избрана"),
    'ml': (BACK,u"Featured"),
    'mt': (CAT, u"Artikli fil-vetrina"),
    'mr': (CAT, u"मुखपृष्ठ सदर लेख"),
    'ms': (BACK,u"Rencana pilihan"),
    'nah':(BACK,u"Featured article"),
    'nds-nl': (BACK, u"Etelazie"),
    'nl': (CAT, u"Wikipedia:Etalage-artikelen"),
    'nn': (BACK,u"God artikkel"),
    'no': (CAT, u"Utmerkede artikler"),
    'nv': (CAT, u"Naaltsoos nizhónígo ályaaígíí"),
    'oc': (CAT, u"Article de qualitat"),
    'pl': (CAT, u"Artykuły na medal"),
    'pt': (CAT, u"!Artigos destacados"),
    'qu': (CAT, u"Wikipidiya:Kusa qillqa"),
    'ro': (CAT, u"Articole de calitate"),
    'ru': (BACK, u"Избранная статья"),
    'sco':(CAT, u"Featurt"),
    'sh': (CAT, u"Izabrani članci"),
    'simple': (CAT, u"Very good articles"),
    'sk': (BACK,u"Perfektný článok"),
    'sl': (CAT, u"Vsi izbrani članki"),
    'sq': (BACK,u"Artikulli perfekt"),
    'sr': (CAT, u"Изабрани"),
    'sv': (CAT, u"Wikipedia:Utmärkta artiklar"),
    'sw': (BACK,u"Makala_nzuri_sana"),
    'szl':(CAT, u"Wyrůżńůne artikle"),
    'ta': (CAT, u"சிறப்புக் கட்டுரைகள்"),
    'te': (CAT, u"విశేషవ్యాసాలు"),
    'th': (BACK,u"บทความคัดสรร"),
    'tl': (BACK,u"Napiling artikulo"),
    'tn': (CAT, u"Featured articles"),
    'tr': (BACK,u"Seçkin madde"),
    'tt': (CAT, u"Сайланган мәкаләләр"),
    'udm':(CAT, u"Википедия:Быръем статьяос"),
    'uk': (CAT, u"Вибрані статті"),
    'ur': (CAT, u"منتخب مقالے"),
    'uz': (CAT, u"Vikipediya:Tanlangan maqolalar"),
    'vec':(BACK,u"Vetrina"),
    'vi': (CAT, u"Bài viết chọn lọc"),
    'vo': (CAT, u"Yegeds gudik"),
    'wa': (CAT, u"Raspepyî årtike"),
    'yi': (CAT, u"רעקאמענדירטע ארטיקלען"),
    'yo': (BACK,u"Àyọkà pàtàkì"),
    'zh': (CAT, u"特色条目"),
    'zh-classical': (CAT, u"卓著"),
    'zh-yue': (BACK, u"正文"),
}

good_name = {
    'ar': (CAT, u"مقالات جيدة"),
    'ca': (CAT, u"Llista d'articles bons"),
    'cs': (CAT, u"Wikipedie:Dobré články"),
    'da': (CAT, u"Gode artikler"),
    'de': (CAT, u"Wikipedia:Lesenswert"),
   #'dsb':(CAT, u"Naraźenje za pógódnośenje"),
    'en': (CAT, u"Wikipedia good articles"),
    'eo': (CAT, u"Legindaj artikoloj"),
    'es': (CAT, u"Wikipedia:Artículos buenos"),
    'et': (CAT, u"Head artiklid"),
    'fa': (CAT, u"مقاله‌های خوب"),
    'fi': (CAT, u"Hyvät artikkelit"),
    'fr': (CAT, u"Bon article"),
    'hsb':(CAT, u"Namjet za pohódnoćenje"),
    'id': (BACK,u"Artikel bagus"),
    'is': (CAT, u"Wikipedia:Gæðagreinar"),
    'ja': (BACK,u"Good article"),
    'ko': (CAT, u"좋은 글"),
    'ksh':(CAT, u"Joode Aatikkel"),
    'lt': (CAT, u"Vertingi straipsniai"),
    'lv': (CAT, u"Labi raksti"),
    'no': (CAT, u"Anbefalte artikler"),
    'oc': (CAT, u"Bon article"),
    'pl': (CAT, u"Dobre artykuły"),
    'pt': (CAT, u"Artigos bons"),
    'ro': (BACK, u"Articol bun"),
    'ru': (CAT, u"Википедия:Хорошие статьи по алфавиту"),
    'simple': (CAT, u"Good articles"),
    'sr': (BACK,u"Иконица добар"),
    'sv': (CAT, u"Wikipedia:Bra artiklar"),
    'tr': (BACK,u"Kaliteli madde"),
    'uk': (CAT, u"Вікіпедія:Добрі статті"),
    'uz': (CAT, u"Vikipediya:Yaxshi maqolalar"),
    'yi': (CAT, u"וויקיפעדיע גוטע ארטיקלען"),
    'zh': (CAT, u"優良條目"),
    'zh-classical': (CAT, u"正典"),
}

lists_name = {
    'ar': (BACK, u'قائمة مختارة'),
    'da': (BACK, u'FremragendeListe'),
    'de': (BACK, u'Informativ'),
    'en': (BACK, u'Featured list'),
    'fa': (BACK, u"فهرست برگزیده"),
    'id': (BACK, u'Featured list'),
    'ja': (BACK, u'Featured List'),
    'ksh':(CAT,  u"Joode Leß"),
    'no': (BACK, u'God liste'),
    'pl': (BACK, u'Medalista'),
    'pt': (BACK, u'Anexo destacado'),
    'ro': (BACK, u'Listă de calitate'),
    'ru': (BACK, u'Избранный список или портал'),
    'tr': (BACK, u'Seçkin liste'),
    'uk': (BACK, u'Вибраний список'),
    'vi': (BACK, u'Sao danh sách chọn lọc'),
    'zh': (BACK, u'特色列表'),
}

# Third parameter is the sort key indicating articles to hide from the given list
former_name = {
    'ca': (CAT, u"Arxiu de propostes de la retirada de la distinció"),
    'en': (CAT, u"Wikipedia former featured articles", "#"),
    'es': (CAT, u"Wikipedia:Artículos anteriormente destacados"),
    'fa': (CAT, u"مقاله‌های برگزیده پیشین"),
    'hu': (CAT, u"Korábbi kiemelt cikkek"),
    'pl': (CAT, u"Byłe artykuły na medal"),
    'pt': (CAT, u"!Ex-Artigos_destacados"),
    'ru': (CAT, u"Википедия:Устаревшие избранные статьи"),
    'th': (CAT, u"บทความคัดสรรในอดีต"),
    'tr': (CAT, u"Vikipedi eski seçkin maddeler"),
    'zh': (CAT, u"已撤销的特色条目"),
}

def featuredArticles(site, pType):
    articles=[]
    if pType == 'good':
        info = good_name
    elif pType == 'former':
        info = former_name
    elif pType == 'list':
        info = lists_name
    else:
        info = featured_name
    try:
        method = info[site.lang][0]
    except KeyError:
        pywikibot.error(
            u'language %s doesn\'t has %s category source.'
            % (site.lang, pType))
        return
    name = info[site.lang][1]
    # hide #-sorted items on en-wiki
    try:
        hide = info[site.lang][2]
    except IndexError:
        hide = None
    raw = method(site, name, hide)
    for p in raw:
        if p.namespace() == 0: # Article
            articles.append(p)
        # Article talk (like in English)
        elif p.namespace() == 1 and site.lang <> 'el':
            articles.append(pywikibot.Page(p.site(),
                            p.title(withNamespace=False)))
    pywikibot.output(
        '\03{lightred}** wikipedia:%s has %i %s articles\03{default}'
        % (site.lang, len(articles), pType))
    for p in articles:
        yield copy(p)

def findTranslated(page, oursite=None, quiet=False):
    if not oursite:
        oursite=pywikibot.getSite()
    if page.isRedirectPage():
        page = page.getRedirectTarget()
    try:
        iw=page.interwiki()
    except:
        pywikibot.output(u"%s -> no interwiki, giving up" % page.title())
        return None
    ourpage=None
    for p in iw:
        if p.site()==oursite:
            ourpage=p
            break
    if not ourpage:
        if not quiet:
            pywikibot.output(u"%s -> no corresponding page in %s"
                             % (page.title(), oursite))
        return None
    if not ourpage.exists():
        pywikibot.output(u"%s -> our page doesn't exist: %s"
                         % (page.title(), ourpage.title()))
        return None
    if ourpage.isRedirectPage():
        ourpage = ourpage.getRedirectTarget()
    pywikibot.output(u"%s -> corresponding page is %s"
                     % (page.title(), ourpage.title()))
    if ourpage.namespace() != 0:
        pywikibot.output(u"%s -> not in the main namespace, skipping"
                         % page.title())
        return None
    if ourpage.isRedirectPage():
        pywikibot.output(u"%s -> double redirect, skipping" % page.title())
        return None
    if not ourpage.exists():
        pywikibot.output(u"%s -> page doesn't exist, skipping" % ourpage.title())
        return None
    try:
        iw = ourpage.interwiki()
    except:
        return None
    backpage=None
    for p in iw:
        if p.site() == page.site():
            backpage = p
            break
    if not backpage:
        pywikibot.output(u"%s -> no back interwiki ref" % page.title())
        return None
    if backpage == page:
        # everything is ok
        return ourpage
    if backpage.isRedirectPage():
        backpage = backpage.getRedirectTarget()
    if backpage == page:
        # everything is ok
        return ourpage
    pywikibot.output(u"%s -> back interwiki ref target is %s"
                     % (page.title(), backpage.title()))
    return None

def getTemplateList (lang, pType):
    if pType == 'good':
        try:
            templates = template_good[lang]
            templates += template_good['_default']
        except KeyError:
            templates = template_good['_default']
    elif pType == 'list':
        try:
            templates = template_lists[lang]
            templates += template_lists['_default']
        except KeyError:
            templates = template_lists['_default']
    else: #pType in ['former', 'featured']
        try:
            templates = template[lang]
            templates += template['_default']
        except KeyError:
            templates = template['_default']
    return templates

def featuredWithInterwiki(fromsite, tosite, template_on_top, pType, quiet,
                          dry=False):
    if not fromsite.lang in cache:
        cache[fromsite.lang] = {}
    if not tosite.lang in cache[fromsite.lang]:
        cache[fromsite.lang][tosite.lang] = {}
    cc = cache[fromsite.lang][tosite.lang]
    if nocache:
        cc={}
    templatelist = getTemplateList(tosite.lang, pType)
    findtemplate = '(' + '|'.join(templatelist) + ')'
    re_Link_FA=re.compile(ur"\{\{%s\|%s\}\}"
                          % (findtemplate.replace(u' ', u'[ _]'),
                             fromsite.lang), re.IGNORECASE)
    gen = featuredArticles(fromsite, pType)
    gen = PreloadingGenerator(gen)

    pairs=[]
    for a in gen:
        if a.title() < afterpage:
            continue
        if u"/" in a.title() and a.namespace() != 0:
            pywikibot.output(u"%s is a subpage" % a.title())
            continue
        if a.title() in cc:
            pywikibot.output(u"(cached) %s -> %s"%(a.title(), cc[a.title()]))
            continue
        if a.isRedirectPage():
            a=a.getRedirectTarget()
        try:
            if not a.exists():
                pywikibot.output(u"source page doesn't exist: %s" % a.title())
                continue
            atrans = findTranslated(a, tosite, quiet)
            if pType!='former':
                if atrans:
                    text=atrans.get()
                    m=re_Link_FA.search(text)
                    if m:
                        pywikibot.output(u"(already done)")
                    else:
                        # insert just before interwiki
                        if (not interactive or
                            pywikibot.input(
                                u'Connecting %s -> %s. Proceed? [Y/N]'
                                % (a.title(), atrans.title())) in ['Y', 'y']
                            ):
                            site = pywikibot.getSite()
                            comment = pywikibot.setAction(
                                i18n.twtranslate(site, 'featured-' + pType,
                                                 {'page': unicode(a)}))
                            ### Moving {{Link FA|xx}} to top of interwikis ###
                            if template_on_top == True:
                                # Getting the interwiki
                                iw = pywikibot.getLanguageLinks(text, site)
                                # Removing the interwiki
                                text = pywikibot.removeLanguageLinks(text, site)
                                text += u"\r\n{{%s|%s}}\r\n" % (templatelist[0],
                                                                fromsite.lang)
                                # Adding the interwiki
                                text = pywikibot.replaceLanguageLinks(text,
                                                                      iw, site)

                            ### Placing {{Link FA|xx}} right next to corresponding interwiki ###
                            else:
                                text=(text[:m.end()]
                                      + (u" {{%s|%s}}" % (templatelist[0],
                                                          fromsite.lang))
                                      + text[m.end():])
                            if not dry:
                                try:
                                    atrans.put(text, comment)
                                except pywikibot.LockedPage:
                                    pywikibot.output(u'Page %s is locked!'
                                                     % atrans.title())
                    cc[a.title()]=atrans.title()
            else:
                if atrans:
                    text=atrans.get()
                    m=re_Link_FA.search(text)
                    if m:
                        # insert just before interwiki
                        if (not interactive or
                            pywikibot.input(
                                u'Connecting %s -> %s. Proceed? [Y/N]'
                                % (a.title(), atrans.title())) in ['Y', 'y']
                            ):
                            site = pywikibot.getSite()
                            comment = pywikibot.setAction(
                                i18n.twtranslate(site, 'featured-former',
                                                 {'page': unicode(a)}))
                            text = re.sub(re_Link_FA,'',text)
                            if not dry:
                                try:
                                    atrans.put(text, comment)
                                except pywikibot.LockedPage:
                                    pywikibot.output(u'Page %s is locked!'
                                                     % atrans.title())
                    else:
                        pywikibot.output(u"(already done)")
                    cc[a.title()]=atrans.title()
        except pywikibot.PageNotSaved, e:
            pywikibot.output(u"Page not saved")

def main(*args):
    global nocache, interactive, afterpage, cache
    nocache = 0
    interactive = 0
    afterpage = u"!"
    cache = {}

    template_on_top = True
    featuredcount = False
    fromlang=[]
    processType = 'featured'
    doAll = False
    part  = False
    quiet = False
    for arg in pywikibot.handleArgs():
        if arg == '-interactive':
            interactive=1
        elif arg == '-nocache':
            nocache=1
        elif arg.startswith('-fromlang:'):
            fromlang=arg[10:].split(",")
            part = True
        elif arg == '-fromall':
            doAll = True
        elif arg.startswith('-after:'):
            afterpage=arg[7:]
        elif arg == '-side':
            template_on_top = False
        elif arg == '-count':
            featuredcount = True
        elif arg == '-good':
            processType = 'good'
        elif arg == '-lists':
            processType = 'list'
        elif arg == '-former':
            processType = 'former'
        elif arg == '-quiet':
            quiet = True

    if part:
        try:
            # BUG: range with zh-min-nan (3 "-")
            if len(fromlang) == 1 and fromlang[0].index("-") >= 0:
                start, end = fromlang[0].split("--", 1)
                if not start: start = ""
                if not end: end = "zzzzzzz"
                if processType == 'good':
                    fromlang = [lang for lang in good_name.keys()
                                if lang >= start and lang <= end]
                elif processType == 'list':
                    fromlang = [lang for lang in lists_name.keys()
                                if lang >= start and lang <= end]
                elif processType == 'former':
                    fromlang = [lang for lang in former_name.keys()
                                if lang >= start and lang <= end]
                else:
                    fromlang = [lang for lang in featured_name.keys()
                                if lang >= start and lang <= end]
        except:
            pass

    if doAll:
        if processType == 'good':
            fromlang = good_name.keys()
        elif processType == 'list':
            fromlang = lists_name.keys()
        elif processType == 'former':
            fromlang = former_name.keys()
        else:
            fromlang = featured_name.keys()

    filename="cache/" + processType
    try:
        cache=pickle.load(file(filename,"rb"))
    except:
        cache={}

    if not fromlang:
        pywikibot.showHelp('featured')
        sys.exit(1)

    fromlang.sort()

    #test whether this site has template enabled
    hasTemplate = False
    if not featuredcount:
        for tl in getTemplateList(pywikibot.getSite().lang, processType):
            t = pywikibot.Page(pywikibot.getSite(), u'Template:'+tl)
            if t.exists():
                hasTemplate = True
                break
    try:
        for ll in fromlang:
            fromsite = pywikibot.getSite(ll)
            if featuredcount:
                try:
                    featuredArticles(fromsite, processType).next()
                except StopIteration:
                    continue
            elif not hasTemplate:
                pywikibot.output(
                    u'\nNOTE: %s arcticles are not implemented at %s-wiki.'
                    % (processType, pywikibot.getSite().lang))
                pywikibot.output('Quitting program...')
                break
            elif  fromsite != pywikibot.getSite():
                featuredWithInterwiki(fromsite, pywikibot.getSite(),
                                      template_on_top, processType, quiet,
                                      pywikibot.simulate)
    except KeyboardInterrupt:
        pywikibot.output('\nQuitting program...')
    finally:
        if not nocache:
            pickle.dump(cache,file(filename,"wb"))

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
