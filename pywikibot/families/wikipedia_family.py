"""Family module for Wikipedia."""
#
# (C) Pywikibot team, 2004-2023
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
        'aa', 'ak', 'cho', 'ho', 'hz', 'ii', 'kj', 'kr', 'lrc', 'mh', 'mus',
        'na', 'ng', 'ten',
    ]

    removed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/deleted.dblist
        'dk', 'mo', 'ru-sib', 'tlh', 'tokipona', 'zh_cn', 'zh_tw',
    ]

    languages_by_size = [
        'en', 'ceb', 'de', 'sv', 'fr', 'nl', 'ru', 'es', 'it', 'arz', 'pl',
        'ja', 'zh', 'uk', 'vi', 'war', 'ar', 'pt', 'fa', 'ca', 'sr', 'id',
        'ko', 'no', 'ce', 'fi', 'tr', 'cs', 'hu', 'tt', 'sh', 'ro',
        'zh-min-nan', 'eu', 'ms', 'eo', 'he', 'hy', 'da', 'bg', 'cy', 'sk',
        'uz', 'azb', 'simple', 'et', 'be', 'kk', 'el', 'min', 'hr', 'lt', 'gl',
        'ur', 'az', 'sl', 'lld', 'ka', 'nn', 'hi', 'th', 'ta', 'bn', 'mk',
        'la', 'zh-yue', 'ast', 'lv', 'af', 'tg', 'my', 'mg', 'sq', 'mr', 'bs',
        'oc', 'te', 'ml', 'br', 'be-tarask', 'nds', 'ky', 'sw', 'lmo', 'jv',
        'new', 'pnb', 'vec', 'ht', 'pms', 'ku', 'ba', 'lb', 'su', 'ga', 'is',
        'szl', 'fy', 'ckb', 'cv', 'pa', 'tl', 'an', 'wuu', 'diq', 'io', 'vo',
        'sco', 'yo', 'ha', 'ne', 'kn', 'ia', 'gu', 'als', 'avk', 'crh', 'bar',
        'scn', 'bpy', 'qu', 'mn', 'nv', 'ig', 'ban', 'xmf', 'si', 'frr', 'tum',
        'mzn', 'ps', 'os', 'or', 'bat-smg', 'sah', 'cdo', 'gd', 'bug', 'bcl',
        'sd', 'yi', 'ilo', 'am', 'li', 'nap', 'gor', 'fo', 'hsb', 'mai',
        'map-bms', 'shn', 'eml', 'ace', 'zh-classical', 'as', 'sa', 'wa', 'ie',
        'hyw', 'sn', 'mhr', 'lij', 'zu', 'hif', 'bjn', 'mrj', 'km', 'mni',
        'hak', 'sat', 'roa-tara', 'pam', 'rue', 'bh', 'nso', 'ary', 'dag',
        'so', 'mi', 'nds-nl', 'myv', 'se', 'co', 'vls', 'sc', 'bo', 'vep',
        'kw', 'glk', 'tk', 'kab', 'gan', 'rw', 'fiu-vro', 'gv', 'ab', 'zea',
        'ug', 'nah', 'skr', 'mt', 'frp', 'tly', 'udm', 'pcd', 'kv', 'gn',
        'csb', 'smn', 'ay', 'nrm', 'ks', 'lez', 'olo', 'mwl', 'lfn', 'mdf',
        'stq', 'ang', 'kaa', 'lo', 'fur', 'rm', 'lad', 'ext', 'gom', 'pap',
        'tw', 'tyv', 'koi', 'av', 'ln', 'dsb', 'dty', 'cbk-zam', 'dv', 'ksh',
        'za', 'lg', 'gag', 'bxr', 'pfl', 'szy', 'blk', 'tay', 'pag', 'pi',
        'haw', 'awa', 'inh', 'krc', 'xal', 'pdc', 'to', 'atj', 'tcy', 'arc',
        'mnw', 'shi', 'jam', 'kbp', 'wo', 'ff', 'nia', 'anp', 'xh', 'om',
        'kbd', 'nov', 'ki', 'nqo', 'bi', 'tpi', 'tet', 'roa-rup', 'jbo', 'tn',
        'fj', 'kg', 'lbe', 'guw', 'ty', 'cu', 'rmy', 'trv', 'ami', 'srn',
        'mad', 'alt', 'sm', 'ltg', 'gcr', 'chr', 'ny', 'pcm', 'st', 'zgh',
        'pih', 'gpe', 'got', 'ss', 'dga', 'kcg', 'gur', 'ee', 'bm', 'ts', 've',
        'bbc', 'chy', 'rn', 'ch', 'ady', 'ik', 'fon', 'guc', 'fat', 'pnt',
        'iu', 'pwn', 'sg', 'din', 'ti', 'kl', 'dz', 'cr',
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
        'ab', 'ace', 'ady', 'af', 'als', 'am', 'an', 'ang', 'ar', 'arc', 'arz',
        'as', 'ast', 'atj', 'av', 'ay', 'az', 'ba', 'bar', 'bat-smg', 'bcl',
        'be', 'be-tarask', 'bg', 'bh', 'bi', 'bjn', 'bm', 'bo', 'bpy', 'bug',
        'bxr', 'ca', 'cbk-zam', 'cdo', 'ce', 'ceb', 'ch', 'chr', 'chy', 'ckb',
        'co', 'cr', 'crh', 'cs', 'csb', 'cu', 'cv', 'cy', 'da', 'diq', 'dsb',
        'dty', 'dz', 'ee', 'el', 'eml', 'en', 'eo', 'et', 'eu', 'ext', 'fa',
        'ff', 'fi', 'fj', 'fo', 'frp', 'frr', 'fur', 'ga', 'gag', 'gan', 'gd',
        'glk', 'gn', 'gom', 'gor', 'got', 'gu', 'gv', 'ha', 'hak', 'haw', 'he',
        'hi', 'hif', 'hr', 'hsb', 'ht', 'hu', 'hy', 'ia', 'ie', 'ig', 'ik',
        'ilo', 'inh', 'io', 'iu', 'ja', 'jam', 'jbo', 'jv', 'ka', 'kaa', 'kab',
        'kbd', 'kg', 'ki', 'kk', 'kl', 'km', 'kn', 'ko', 'koi', 'krc', 'ks',
        'ku', 'kv', 'kw', 'ky', 'la', 'lad', 'lb', 'lbe', 'lez', 'lfn', 'lg',
        'li', 'lij', 'lmo', 'ln', 'lo', 'lt', 'ltg', 'lv', 'map-bms', 'mdf',
        'meta', 'mg', 'mhr', 'mi', 'mk', 'ml', 'mn', 'mrj', 'ms', 'mwl', 'my',
        'myv', 'mzn', 'nah', 'nap', 'nds-nl', 'ne', 'new', 'nl', 'no', 'nov',
        'nrm', 'nso', 'nv', 'ny', 'oc', 'olo', 'om', 'or', 'os', 'pa', 'pag',
        'pam', 'pap', 'pdc', 'pfl', 'pi', 'pih', 'pms', 'pnb', 'pnt', 'ps',
        'qu', 'rm', 'rmy', 'rn', 'roa-rup', 'roa-tara', 'ru', 'rue', 'rw',
        'sa', 'sah', 'sc', 'scn', 'sco', 'sd', 'se', 'sg', 'sh', 'shn', 'si',
        'simple', 'sk', 'sm', 'sn', 'so', 'srn', 'ss', 'st', 'stq', 'su', 'sv',
        'sw', 'szl', 'ta', 'tcy', 'te', 'tet', 'tg', 'th', 'ti', 'tk', 'tl',
        'tn', 'to', 'tpi', 'tr', 'ts', 'tt', 'tum', 'tw', 'ty', 'tyv', 'udm',
        'ug', 'uz', 've', 'vec', 'vep', 'vls', 'vo', 'wa', 'war', 'wo', 'xal',
        'xh', 'xmf', 'yi', 'yo', 'za', 'zea', 'zh', 'zh-classical',
        'zh-min-nan', 'zh-yue', 'zu',
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
