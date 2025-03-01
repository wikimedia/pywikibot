"""Family module for Wikipedia."""
#
# (C) Pywikibot team, 2004-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


# The Wikimedia family that is known as Wikipedia, the Free Encyclopedia
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family module for Wikipedia."""

    name = 'wikipedia'

    closed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/closed.dblist
        'aa', 'ak', 'cho', 'ho', 'hz', 'ii', 'kj', 'kr', 'lrc', 'mh', 'mus',
        'na', 'ng', 'ten',
    ]

    removed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/deleted.dblist
        'dk', 'mo', 'ru-sib', 'tlh', 'tokipona', 'zh_cn', 'zh_tw',
    ]

    codes = {
        'ab', 'ace', 'ady', 'af', 'als', 'alt', 'am', 'ami', 'an', 'ang',
        'ann', 'anp', 'ar', 'arc', 'ary', 'arz', 'as', 'ast', 'atj', 'av',
        'avk', 'awa', 'ay', 'az', 'azb', 'ba', 'ban', 'bar', 'bat-smg', 'bbc',
        'bcl', 'bdr', 'be', 'be-tarask', 'bew', 'bg', 'bh', 'bi', 'bjn', 'blk',
        'bm', 'bn', 'bo', 'bpy', 'br', 'bs', 'btm', 'bug', 'bxr', 'ca',
        'cbk-zam', 'cdo', 'ce', 'ceb', 'ch', 'chr', 'chy', 'ckb', 'co', 'cr',
        'crh', 'cs', 'csb', 'cu', 'cv', 'cy', 'da', 'dag', 'de', 'dga', 'din',
        'diq', 'dsb', 'dtp', 'dty', 'dv', 'dz', 'ee', 'el', 'eml', 'en', 'eo',
        'es', 'et', 'eu', 'ext', 'fa', 'fat', 'ff', 'fi', 'fiu-vro', 'fj',
        'fo', 'fon', 'fr', 'frp', 'frr', 'fur', 'fy', 'ga', 'gag', 'gan',
        'gcr', 'gd', 'gl', 'glk', 'gn', 'gom', 'gor', 'got', 'gpe', 'gu',
        'guc', 'gur', 'guw', 'gv', 'ha', 'hak', 'haw', 'he', 'hi', 'hif', 'hr',
        'hsb', 'ht', 'hu', 'hy', 'hyw', 'ia', 'iba', 'id', 'ie', 'ig', 'igl',
        'ik', 'ilo', 'inh', 'io', 'is', 'it', 'iu', 'ja', 'jam', 'jbo', 'jv',
        'ka', 'kaa', 'kab', 'kbd', 'kbp', 'kcg', 'kg', 'kge', 'ki', 'kk', 'kl',
        'km', 'kn', 'knc', 'ko', 'koi', 'krc', 'ks', 'ksh', 'ku', 'kus', 'kv',
        'kw', 'ky', 'la', 'lad', 'lb', 'lbe', 'lez', 'lfn', 'lg', 'li', 'lij',
        'lld', 'lmo', 'ln', 'lo', 'lt', 'ltg', 'lv', 'mad', 'mai', 'map-bms',
        'mdf', 'mg', 'mhr', 'mi', 'min', 'mk', 'ml', 'mn', 'mni', 'mnw', 'mos',
        'mr', 'mrj', 'ms', 'mt', 'mwl', 'my', 'myv', 'mzn', 'nah', 'nap',
        'nds', 'nds-nl', 'ne', 'new', 'nia', 'nl', 'nn', 'no', 'nov', 'nqo',
        'nr', 'nrm', 'nso', 'nv', 'ny', 'oc', 'olo', 'om', 'or', 'os', 'pa',
        'pag', 'pam', 'pap', 'pcd', 'pcm', 'pdc', 'pfl', 'pi', 'pih', 'pl',
        'pms', 'pnb', 'pnt', 'ps', 'pt', 'pwn', 'qu', 'rm', 'rmy', 'rn', 'ro',
        'roa-rup', 'roa-tara', 'rsk', 'ru', 'rue', 'rw', 'sa', 'sah', 'sat',
        'sc', 'scn', 'sco', 'sd', 'se', 'sg', 'sh', 'shi', 'shn', 'si',
        'simple', 'sk', 'skr', 'sl', 'sm', 'smn', 'sn', 'so', 'sq', 'sr',
        'srn', 'ss', 'st', 'stq', 'su', 'sv', 'sw', 'syl', 'szl', 'szy', 'ta',
        'tay', 'tcy', 'tdd', 'te', 'tet', 'tg', 'th', 'ti', 'tig', 'tk', 'tl',
        'tly', 'tn', 'to', 'tpi', 'tr', 'trv', 'ts', 'tt', 'tum', 'tw', 'ty',
        'tyv', 'udm', 'ug', 'uk', 'ur', 'uz', 've', 'vec', 'vep', 'vi', 'vls',
        'vo', 'wa', 'war', 'wo', 'wuu', 'xal', 'xh', 'xmf', 'yi', 'yo', 'za',
        'zea', 'zgh', 'zh', 'zh-classical', 'zh-min-nan', 'zh-yue', 'zu',
    }

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
        'ckb': ('ڕەوانەکەری پۆل', ),
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
        'ab', 'ace', 'ady', 'af', 'als', 'am', 'ami', 'an', 'ang', 'ar', 'arc',
        'arz', 'as', 'ast', 'atj', 'av', 'avk', 'awa', 'ay', 'az', 'azb', 'ba',
        'ban', 'bar', 'bat-smg', 'bcl', 'be', 'be-tarask', 'bh', 'bi', 'bjn',
        'blk', 'bm', 'bo', 'bpy', 'bug', 'bxr', 'ca', 'cbk-zam', 'cdo', 'ce',
        'ceb', 'ch', 'chr', 'chy', 'ckb', 'co', 'cr', 'crh', 'cs', 'csb', 'cu',
        'cv', 'cy', 'dag', 'diq', 'dsb', 'dty', 'dz', 'ee', 'eml', 'eo', 'et',
        'eu', 'ext', 'fa', 'ff', 'fj', 'fo', 'frp', 'frr', 'fur', 'ga', 'gag',
        'gan', 'gcr', 'gd', 'glk', 'gn', 'gom', 'gor', 'got', 'gu', 'guc',
        'gur', 'guw', 'gv', 'ha', 'hak', 'haw', 'hi', 'hif', 'hr', 'hsb', 'ht',
        'hu', 'hy', 'hyw', 'ia', 'ie', 'ig', 'ik', 'ilo', 'inh', 'io', 'iu',
        'jam', 'jbo', 'jv', 'ka', 'kaa', 'kab', 'kbd', 'kbp', 'kcg', 'kg',
        'ki', 'kk', 'kl', 'km', 'kn', 'ko', 'koi', 'krc', 'ks', 'ku', 'kv',
        'kw', 'ky', 'la', 'lad', 'lbe', 'lez', 'lfn', 'lg', 'li', 'lij', 'lld',
        'lmo', 'ln', 'lo', 'lt', 'ltg', 'lv', 'mad', 'mai', 'map-bms', 'mdf',
        'mg', 'mi', 'min', 'mk', 'mn', 'mni', 'mrj', 'mwl', 'my', 'myv', 'mzn',
        'na', 'nah', 'nap', 'nds-nl', 'ne', 'new', 'nia', 'nl', 'nov', 'nqo',
        'nrm', 'nso', 'nv', 'ny', 'oc', 'olo', 'om', 'or', 'os', 'pa', 'pag',
        'pam', 'pap', 'pcd', 'pcm', 'pdc', 'pfl', 'pi', 'pih', 'pms', 'pnb',
        'pnt', 'ps', 'pwn', 'qu', 'rm', 'rmy', 'rn', 'roa-rup', 'roa-tara',
        'rue', 'rw', 'sa', 'sah', 'sat', 'sc', 'scn', 'sco', 'sd', 'se', 'sg',
        'sh', 'shi', 'shn', 'si', 'simple', 'sk', 'skr', 'sm', 'smn', 'sn',
        'so', 'srn', 'st', 'stq', 'su', 'sw', 'szl', 'szy', 'ta', 'tay', 'tcy',
        'te', 'tet', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tpi', 'trv',
        'ts', 'tt', 'tum', 'tw', 'ty', 'tyv', 'udm', 'ug', 'uz', 've', 'vec',
        'vep', 'vls', 'vo', 'wa', 'war', 'wo', 'xal', 'xh', 'xmf', 'yi', 'yo',
        'za', 'zea', 'zh', 'zh-classical', 'zh-min-nan', 'zh-yue', 'zu',
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
        'ar': ('/شرح', '/doc'),
        'ary': ('/توثيق', '/شرح', '/doc'),
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
        'de': ('Inuse', 'In use', 'In bearbeitung', 'Inbearbeitung'),
        'en': ('Inuse', 'In use'),
        'fa': ('ویرایش',),
        'fr': ('En cours',),
        'he': ('בעבודה',),
        'hr': ('Radovi',),
        'hy': ('Խմբագրում եմ',),
        'ru': ('Редактирую',),
        'sr': ('Радови у току', 'Рут'),
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
               'Rfc-archiv-start'),
        'de': ('Archiv',),
    }

    @classmethod
    def __post_init__(cls):
        """Add 'yue' code alias due to :phab:`T341960`.

        .. versionadded:: 8.3
        """
        aliases = cls.code_aliases.copy()
        aliases['yue'] = 'zh-yue'
        cls.code_aliases = aliases

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
