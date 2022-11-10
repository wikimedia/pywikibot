"""Family module for Wikipedia."""
#
# (C) Pywikibot team, 2004-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Wikimedia family that is known as Wikipedia, the Free Encyclopedia
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family module for Wikipedia."""

    name = 'wikipedia'

    closed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/closed.dblist
        'aa', 'cho', 'ho', 'hz', 'ii', 'kj', 'kr', 'lrc', 'mh', 'mus', 'ng',
        'ten',
    ]

    removed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/deleted.dblist
        'dk', 'mo', 'ru-sib', 'tlh', 'tokipona', 'zh_cn', 'zh_tw',
    ]

    languages_by_size = [
        'en', 'ceb', 'de', 'sv', 'fr', 'nl', 'ru', 'es', 'it', 'arz', 'pl',
        'ja', 'zh', 'vi', 'war', 'uk', 'ar', 'pt', 'fa', 'ca', 'sr', 'id',
        'ko', 'no', 'fi', 'tr', 'hu', 'cs', 'ce', 'sh', 'tt', 'ro',
        'zh-min-nan', 'eu', 'ms', 'eo', 'he', 'hy', 'da', 'bg', 'cy', 'azb',
        'sk', 'kk', 'et', 'min', 'be', 'simple', 'el', 'hr', 'lt', 'gl', 'az',
        'uz', 'ur', 'sl', 'ka', 'nn', 'hi', 'th', 'ta', 'la', 'mk', 'ast',
        'bn', 'zh-yue', 'lv', 'tg', 'af', 'my', 'mg', 'bs', 'mr', 'oc', 'sq',
        'nds', 'ky', 'be-tarask', 'ml', 'te', 'br', 'sw', 'new', 'jv', 'lld',
        'vec', 'ht', 'pms', 'pnb', 'su', 'lb', 'ba', 'ku', 'ga', 'lmo', 'szl',
        'is', 'cv', 'fy', 'ckb', 'tl', 'an', 'wuu', 'diq', 'sco', 'pa', 'io',
        'vo', 'yo', 'ne', 'gu', 'als', 'kn', 'bar', 'scn', 'avk', 'bpy', 'ia',
        'qu', 'mn', 'crh', 'nv', 'xmf', 'ha', 'si', 'bat-smg', 'ps', 'ban',
        'os', 'frr', 'or', 'gd', 'sah', 'cdo', 'bug', 'yi', 'ilo', 'sd', 'am',
        'nap', 'li', 'hsb', 'fo', 'map-bms', 'mai', 'gor', 'mzn', 'ig', 'eml',
        'bcl', 'ace', 'shn', 'sa', 'zh-classical', 'wa', 'ie', 'lij', 'as',
        'zu', 'mhr', 'mrj', 'hyw', 'hif', 'mni', 'km', 'hak', 'roa-tara', 'sn',
        'bjn', 'pam', 'so', 'nso', 'rue', 'bh', 'tum', 'se', 'myv', 'vls',
        'mi', 'sat', 'nds-nl', 'sc', 'nah', 'vep', 'tk', 'kab', 'gan', 'glk',
        'co', 'fiu-vro', 'kw', 'ab', 'bo', 'ary', 'gv', 'frp', 'skr', 'kv',
        'ug', 'pcd', 'csb', 'udm', 'zea', 'ay', 'mt', 'gn', 'nrm', 'smn',
        'dag', 'lez', 'lfn', 'stq', 'olo', 'lo', 'mwl', 'rw', 'ang', 'fur',
        'rm', 'lad', 'gom', 'koi', 'ext', 'tyv', 'dsb', 'dty', 'ln', 'av',
        'cbk-zam', 'dv', 'ksh', 'pap', 'gag', 'bxr', 'pfl', 'pag', 'pi', 'szy',
        'haw', 'ks', 'awa', 'tay', 'kaa', 'mdf', 'tw', 'za', 'inh', 'krc',
        'xal', 'blk', 'pdc', 'atj', 'to', 'arc', 'tcy', 'kbp', 'mnw', 'jam',
        'na', 'wo', 'kbd', 'nia', 'nov', 'ki', 'lg', 'bi', 'nqo', 'tpi', 'tet',
        'shi', 'jbo', 'roa-rup', 'fj', 'lbe', 'kg', 'xh', 'ty', 'cu', 'guw',
        'srn', 'trv', 'om', 'sm', 'alt', 'gcr', 'chr', 'ltg', 'tn', 'ny',
        'pih', 'mad', 'st', 'got', 'ami', 'bm', 'rmy', 've', 'ts', 'chy', 'rn',
        'ff', 'ak', 'ss', 'iu', 'kcg', 'ch', 'pnt', 'ee', 'ady', 'ik', 'pcm',
        'sg', 'din', 'pwn', 'kl', 'ti', 'dz', 'cr',
    ]

    # Sites we want to edit but not count as real languages
    test_codes = ['test', 'test2']

    # Templates that indicate a category redirect
    # Redirects to these templates are automatically included
    category_redirect_templates = {
        '_default': (),
        'ar': ('تحويل تصنيف',),
        'ary': ('Category redirect',),
        'arz': ('تحويل تصنيف',),
        'bn': ('বিষয়শ্রেণী পুনর্নির্দেশ',),
        'bs': ('Category redirect',),
        'cs': ('Zastaralá kategorie',),
        'da': ('Kategoriomdirigering',),
        'en': ('Category redirect',),
        'es': ('Categoría redirigida',),
        'eu': ('Kategoria birzuzendu',),
        'fa': ('رده بهتر',),
        'fr': ('Catégorie redirigée',),
        'gv': ('Aastiurey ronney',),
        'hi': ('श्रेणी अनुप्रेषित',),
        'hu': ('Kat-redir',),
        'id': ('Alih kategori',),
        'ja': ('Category redirect',),
        'ko': ('분류 넘겨주기',),
        'mk': ('Премести категорија',),
        'ml': ('Category redirect',),
        'ms': ('Pengalihan kategori',),
        'mt': ('Rindirizzament kategorija',),
        'ne': ('श्रेणी अनुप्रेषण',),
        'no': ('Kategoriomdirigering',),
        'pt': ('Redirecionamento de categoria',),
        'ro': ('Redirect categorie',),
        'ru': ('Переименованная категория',),
        'sco': ('Category redirect',),
        'sh': ('Prekat',),
        'simple': ('Category redirect',),
        'sl': ('Preusmeritev kategorije',),
        'sr': ('Category redirect',),
        'sq': ('Kategori e zhvendosur',),
        'sv': ('Kategoriomdirigering',),
        'tl': ('Category redirect',),
        'tr': ('Kategori yönlendirme',),
        'uk': ('Categoryredirect',),
        'ur': ('زمرہ رجوع مکرر',),
        'vi': ('Đổi hướng thể loại',),
        'yi': ('קאטעגאריע אריבערפירן',),
        'zh': ('分类重定向',),
        'zh-yue': ('分類彈去',),
    }

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'ab', 'ace', 'ady', 'af', 'ak', 'als', 'am', 'an', 'ang', 'ar', 'arc',
        'arz', 'as', 'ast', 'atj', 'av', 'ay', 'az', 'ba', 'bar', 'bat-smg',
        'bcl', 'be', 'be-tarask', 'bg', 'bh', 'bi', 'bjn', 'bm', 'bo', 'bpy',
        'bug', 'bxr', 'ca', 'cbk-zam', 'cdo', 'ce', 'ceb', 'ch', 'chr', 'chy',
        'ckb', 'co', 'cr', 'crh', 'cs', 'csb', 'cu', 'cv', 'cy', 'da', 'diq',
        'dsb', 'dty', 'dz', 'ee', 'el', 'eml', 'en', 'eo', 'et', 'eu', 'ext',
        'fa', 'ff', 'fi', 'fj', 'fo', 'frp', 'frr', 'fur', 'ga', 'gag', 'gan',
        'gd', 'glk', 'gn', 'gom', 'gor', 'got', 'gu', 'gv', 'ha', 'hak', 'haw',
        'he', 'hi', 'hif', 'hr', 'hsb', 'ht', 'hu', 'hy', 'ia', 'ie', 'ig',
        'ik', 'ilo', 'inh', 'io', 'iu', 'ja', 'jam', 'jbo', 'jv', 'ka', 'kaa',
        'kab', 'kbd', 'kg', 'ki', 'kk', 'kl', 'km', 'kn', 'ko', 'koi', 'krc',
        'ks', 'ku', 'kv', 'kw', 'ky', 'la', 'lad', 'lb', 'lbe', 'lez', 'lfn',
        'lg', 'li', 'lij', 'lmo', 'ln', 'lo', 'lt', 'ltg', 'lv', 'map-bms',
        'mdf', 'meta', 'mg', 'mhr', 'mi', 'mk', 'ml', 'mn', 'mrj', 'ms', 'mwl',
        'my', 'myv', 'mzn', 'na', 'nah', 'nap', 'nds-nl', 'ne', 'new', 'nl',
        'no', 'nov', 'nrm', 'nso', 'nv', 'ny', 'oc', 'olo', 'om', 'or', 'os',
        'pa', 'pag', 'pam', 'pap', 'pdc', 'pfl', 'pi', 'pih', 'pms', 'pnb',
        'pnt', 'ps', 'qu', 'rm', 'rmy', 'rn', 'roa-rup', 'roa-tara', 'ru',
        'rue', 'rw', 'sa', 'sah', 'sc', 'scn', 'sco', 'sd', 'se', 'sg', 'sh',
        'shn', 'si', 'simple', 'sk', 'sm', 'sn', 'so', 'srn', 'ss', 'st',
        'stq', 'su', 'sv', 'sw', 'szl', 'ta', 'tcy', 'te', 'tet', 'tg', 'th',
        'ti', 'tk', 'tl', 'tn', 'to', 'tpi', 'tr', 'ts', 'tt', 'tum', 'tw',
        'ty', 'tyv', 'udm', 'ug', 'uz', 've', 'vec', 'vep', 'vls', 'vo', 'wa',
        'war', 'wo', 'xal', 'xh', 'xmf', 'yi', 'yo', 'za', 'zea', 'zh',
        'zh-classical', 'zh-min-nan', 'zh-yue', 'zu',
    ]

    # Languages that used to be coded in iso-8859-1
    latin1old = {
        'af', 'bs', 'co', 'cs', 'da', 'de', 'en', 'es', 'et', 'eu', 'fi', 'fr',
        'fy', 'ga', 'gl', 'ia', 'id', 'it', 'la', 'lt', 'lv', 'mi', 'mr', 'na',
        'nds', 'nl', 'no', 'pt', 'simple', 'sl', 'sv', 'sw', 'test', 'tt',
        'uk', 'vi', 'vo'
    }

    # Subpages for documentation.
    # TODO: List is incomplete, to be completed for missing languages.
    # TODO: Remove comments for appropriate pages
    doc_subpages = {
        '_default': (('/doc', ),
                     ['arz', 'bn', 'cs', 'da', 'en', 'es', 'hr', 'hu', 'id',
                      'ilo', 'ja', 'ms', 'pt', 'ro', 'ru', 'simple', 'sh',
                      'vi', 'zh']
                     ),
        'ar': ('/شرح', '/doc', ),
        'ary': ('/توثيق', '/شرح', '/doc', ),
        'bs': ('/dok', ),
        'ca': ('/ús', ),
        'de': ('Doku', '/Meta'),
        'dsb': ('/Dokumentacija', ),
        'eu': ('txantiloi dokumentazioa', '/dok'),
        'fa': ('/doc', '/توضیحات'),
        # fi: no idea how to handle this type of subpage at :Metasivu:
        'fi': ((), ),
        'fr': ('/Documentation',),
        'hsb': ('/Dokumentacija', ),
        'it': ('/Man', ),
        'ka': ('/ინფო', ),
        'ko': ('/설명문서', ),
        'no': ('/dok', ),
        'nn': ('/dok', ),
        'pl': ('/opis', ),
        'sk': ('/Dokumentácia', ),
        'sr': ('/док', ),
        'sv': ('/dok', ),
        'uk': ('/Документація', ),
        'ur': ('/doc', '/دستاویز'),
    }

    # Templates that indicate an edit should be avoided
    edit_restricted_templates = {
        'ar': ('تحرر',),
        'ary': ('كاتبدل دابا',),
        'arz': ('بتتطور',),
        'bs': ('Izmjena u toku',),
        'cs': ('Pracuje se',),
        'de': ('Inuse', 'In use', 'In bearbeitung', 'Inbearbeitung',),
        'en': ('Inuse', 'In use'),
        'fa': ('ویرایش',),
        'fr': ('En cours',),
        'he': ('בעבודה',),
        'hr': ('Radovi',),
        'hy': ('Խմբագրում եմ',),
        'ru': ('Редактирую',),
        'sr': ('Радови у току', 'Рут',),
        'test': ('In use',),
        'ur': ('زیر ترمیم',),
        'zh': ('Inuse',),
    }

    # Archive templates that indicate an edit of non-archive bots
    # should be avoided
    archived_page_templates = {
        'ar': ('أرشيف نقاش',),
        'arz': ('صفحة ارشيف',),
        'cs': ('Archiv', 'Archiv Wikipedie', 'Archiv diskuse',
               'Archivace start', 'Posloupnost archivů', 'Rfa-archiv-start',
               'Rfc-archiv-start',),
        'de': ('Archiv',),
    }

    def encodings(self, code):
        """Return a list of historical encodings for a specific site."""
        # Historic compatibility
        if code == 'pl':
            return 'utf-8', 'iso8859-2'
        if code == 'ru':
            return 'utf-8', 'iso8859-5'
        if code in self.latin1old:
            return 'utf-8', 'iso-8859-1'
        return super().encodings(code)
