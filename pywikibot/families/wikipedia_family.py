# -*- coding: utf-8 -*-
"""Family module for Wikipedia."""
#
# (C) Pywikibot team, 2004-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family


# The Wikimedia family that is known as Wikipedia, the Free Encyclopedia
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family module for Wikipedia."""

    name = 'wikipedia'

    closed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=closed.dblist
        'aa', 'advisory', 'cho', 'ho', 'hz', 'ii', 'kj', 'kr', 'mh', 'mo',
        'mus', 'ng', 'quality', 'strategy', 'ten', 'usability'
    ]

    removed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=deleted.dblist
        'dk', 'ru-sib', 'tlh', 'tokipona', 'zh_cn', 'zh_tw',
    ]

    def __init__(self):
        """Constructor."""
        self.languages_by_size = [
            'en', 'ceb', 'sv', 'de', 'fr', 'nl', 'ru', 'it', 'es', 'pl', 'war',
            'vi', 'ja', 'zh', 'pt', 'uk', 'sr', 'fa', 'ca', 'ar', 'no', 'sh',
            'fi', 'hu', 'id', 'ko', 'cs', 'ro', 'ms', 'tr', 'eu', 'eo', 'bg',
            'hy', 'da', 'zh-min-nan', 'sk', 'he', 'min', 'kk', 'hr', 'lt',
            'et', 'ce', 'sl', 'be', 'gl', 'el', 'ur', 'nn', 'az', 'simple',
            'uz', 'la', 'hi', 'th', 'ka', 'vo', 'ta', 'cy', 'mk', 'tg', 'tl',
            'mg', 'oc', 'lv', 'ky', 'tt', 'bs', 'ast', 'sq', 'new', 'azb',
            'te', 'zh-yue', 'pms', 'br', 'be-tarask', 'bn', 'ml', 'jv', 'ht',
            'lb', 'mr', 'sco', 'af', 'ga', 'pnb', 'is', 'ba', 'cv', 'sw', 'fy',
            'su', 'my', 'lmo', 'an', 'yo', 'ne', 'nds', 'pa', 'gu', 'io',
            'scn', 'bar', 'bpy', 'als', 'ku', 'kn', 'ckb', 'ia', 'qu', 'arz',
            'mn', 'bat-smg', 'gd', 'si', 'wa', 'nap', 'yi', 'am', 'bug', 'or',
            'cdo', 'map-bms', 'fo', 'mzn', 'hsb', 'mai', 'xmf', 'li', 'sah',
            'sa', 'vec', 'ilo', 'os', 'mrj', 'mhr', 'hif', 'eml', 'bh',
            'roa-tara', 'sd', 'ps', 'diq', 'pam', 'hak', 'nso', 'wuu',
            'zh-classical', 'bcl', 'se', 'ace', 'mi', 'nah', 'szl', 'nds-nl',
            'frr', 'rue', 'gan', 'vls', 'km', 'bo', 'crh', 'vep', 'sc', 'glk',
            'co', 'fiu-vro', 'lrc', 'tk', 'kv', 'csb', 'myv', 'gv', 'as',
            'lad', 'so', 'nv', 'zea', 'udm', 'ay', 'lez', 'stq', 'ie', 'kw',
            'nrm', 'pcd', 'mwl', 'ug', 'gom', 'rm', 'gn', 'koi', 'ab', 'lij',
            'mt', 'sn', 'fur', 'dsb', 'dv', 'ang', 'ln', 'frp', 'cbk-zam',
            'kab', 'ext', 'dty', 'ksh', 'lo', 'gag', 'olo', 'pag', 'pi', 'av',
            'bxr', 'haw', 'pfl', 'xal', 'krc', 'pap', 'kaa', 'rw', 'pdc',
            'bjn', 'ha', 'to', 'nov', 'kl', 'arc', 'jam', 'kbd', 'tyv', 'tpi',
            'tet', 'kbp', 'ki', 'ig', 'na', 'roa-rup', 'jbo', 'lbe', 'ty',
            'mdf', 'za', 'kg', 'bi', 'wo', 'lg', 'srn', 'tcy', 'zu', 'chr',
            'ltg', 'sm', 'om', 'xh', 'rmy', 'cu', 'tn', 'pih', 'rn', 'chy',
            'tw', 'tum', 'ts', 'bm', 'got', 'st', 'pnt', 'ak', 'ss', 'atj',
            'ch', 'fj', 'ady', 'iu', 'ny', 'ee', 'ks', 'ik', 've', 'sg', 'ff',
            'dz', 'ti', 'cr', 'din',
        ]

        # Sites we want to edit but not count as real languages
        self.test_codes = ['test', 'test2']

        super(Family, self).__init__()

        # Templates that indicate a category redirect
        # Redirects to these templates are automatically included
        self.category_redirect_templates = {
            '_default': (),
            'ar': ('تحويل تصنيف',),
            'arz': (u'تحويل تصنيف',),
            'bn': ('বিষয়শ্রেণী পুনর্নির্দেশ',),
            'bs': ('Category redirect',),
            'cs': (u'Zastaralá kategorie',),
            'da': (u'Kategoriomdirigering',),
            'en': (u'Category redirect',),
            'es': (u'Categoría redirigida',),
            'eu': ('Kategoria birzuzendu',),
            'fa': ('رده بهتر',),
            'fr': ('Catégorie redirigée',),
            'gv': (u'Aastiurey ronney',),
            'hi': ('श्रेणी अनुप्रेषित',),
            'hu': ('Kat-redir',),
            'id': ('Alih kategori',),
            'ja': (u'Category redirect',),
            'ko': (u'분류 넘겨주기',),
            'mk': (u'Премести категорија',),
            'ml': (u'Category redirect',),
            'ms': ('Pengalihan kategori',),
            'mt': ('Rindirizzament kategorija',),
            'ne': ('श्रेणी अनुप्रेषण',),
            'no': ('Kategoriomdirigering',),
            'pt': ('Redirecionamento de categoria',),
            'ro': (u'Redirect categorie',),
            'ru': ('Переименованная категория',),
            'sco': ('Category redirect',),
            'sh': ('Prekat',),
            'simple': ('Category redirect',),
            'sl': ('Preusmeritev kategorije',),
            'sr': ('Category redirect',),
            'sq': ('Kategori e zhvendosur',),
            'sv': ('Kategoriomdirigering',),
            'tl': (u'Category redirect',),
            'tr': ('Kategori yönlendirme',),
            'uk': (u'Categoryredirect',),
            'ur': ('زمرہ رجوع مکرر',),
            'vi': ('Đổi hướng thể loại',),
            'yi': (u'קאטעגאריע אריבערפירן',),
            'zh': ('分类重定向',),
            'zh-yue': ('分類彈去',),
        }

        # families that redirect their interlanguage links here.
        self.interwiki_forwarded_from = [
            'commons',
            'incubator',
            'meta',
            'species',
            'strategy',
            'test',
            'wikimania'
        ]

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/BPI#Current_implementation
        # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
        self.cross_allowed = [
            'ab', 'ace', 'ady', 'af', 'ak', 'als', 'am', 'an', 'ang', 'ar',
            'arc', 'arz', 'as', 'ast', 'av', 'ay', 'az', 'ba', 'bar',
            'bat-smg', 'bcl', 'be', 'be-tarask', 'bg', 'bh', 'bi', 'bjn', 'bm',
            'bo', 'bpy', 'bug', 'bxr', 'ca', 'cbk-zam', 'cdo', 'ce', 'ceb',
            'ch', 'chr', 'chy', 'ckb', 'co', 'cr', 'crh', 'cs', 'csb', 'cu',
            'cv', 'cy', 'da', 'diq', 'dsb', 'dz', 'ee', 'el', 'eml', 'en',
            'eo', 'et', 'eu', 'ext', 'fa', 'ff', 'fi', 'fj', 'fo', 'frp',
            'frr', 'fur', 'ga', 'gag', 'gan', 'gd', 'glk', 'gn', 'got', 'gu',
            'gv', 'ha', 'hak', 'haw', 'he', 'hi', 'hif', 'hr', 'hsb', 'ht',
            'hu', 'hy', 'ia', 'ie', 'ig', 'ik', 'ilo', 'io', 'iu', 'ja', 'jam',
            'jbo', 'jv', 'ka', 'kaa', 'kab', 'kdb', 'kg', 'ki', 'kk', 'kl',
            'km', 'kn', 'ko', 'koi', 'krc', 'ks', 'ku', 'kv', 'kw', 'ky', 'la',
            'lad', 'lb', 'lbe', 'lez', 'lg', 'li', 'lij', 'lmo', 'ln', 'lo',
            'lt', 'ltg', 'lv', 'map-bms', 'mdf', 'mg', 'mhr', 'mi', 'mk', 'ml',
            'mn', 'mrj', 'ms', 'mwl', 'my', 'myv', 'mzn', 'na', 'nah', 'nap',
            'nds-nl', 'ne', 'new', 'nl', 'no', 'nov', 'nrm', 'nso', 'nv', 'ny',
            'oc', 'olo', 'om', 'or', 'os', 'pa', 'pag', 'pam', 'pap', 'pdc',
            'pfl', 'pi', 'pih', 'pms', 'pnb', 'pnt', 'ps', 'qu', 'rm', 'rmy',
            'rn', 'roa-rup', 'roa-tara', 'ru', 'rue', 'rw', 'sa', 'sah', 'sc',
            'scn', 'sco', 'sd', 'se', 'sg', 'sh', 'si', 'simple', 'sk', 'sm',
            'sn', 'so', 'srn', 'ss', 'st', 'stq', 'su', 'sv', 'sw', 'szl',
            'ta', 'tcy', 'te', 'tet', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to',
            'tpi', 'tr', 'ts', 'tt', 'tum', 'tw', 'ty', 'tyv', 'udm', 'ug',
            'uz', 've', 'vec', 'vep', 'vls', 'vo', 'wa', 'war', 'wo', 'wuu',
            'xal', 'xh', 'xmf', 'yi', 'yo', 'za', 'zea', 'zh', 'zh-classical',
            'zh-min-nan', 'zh-yue', 'zu',
        ]

        # On most Wikipedias page names must start with a capital letter,
        # but some languages don't use this.
        self.nocapitalize = ['jbo']

        # Languages that used to be coded in iso-8859-1
        self.latin1old = [
            'de', 'en', 'et', 'es', 'ia', 'la', 'af', 'cs', 'fr', 'pt', 'sl',
            'bs', 'fy', 'vi', 'lt', 'fi', 'it', 'no', 'simple', 'gl', 'eu',
            'nds', 'co', 'mi', 'mr', 'id', 'lv', 'sw', 'tt', 'uk', 'vo', 'ga',
            'na', 'es', 'nl', 'da', 'dk', 'sv', 'test']

        # Subpages for documentation.
        # TODO: List is incomplete, to be completed for missing languages.
        # TODO: Remove comments for appropriate pages
        self.doc_subpages = {
            '_default': ((u'/doc', ),
                         ['ar', 'bn', 'cs', 'da', 'en', 'es', 'hr',
                          'hu', 'id', 'ilo', 'ja', 'ms',
                          'pt', 'ro', 'ru', 'simple', 'sh', 'vi', 'zh']
                         ),
            'bs': ('/dok', ),
            'ca': (u'/ús', ),
            'de': (u'Doku', u'/Meta'),
            'dsb': (u'/Dokumentacija', ),
            'eu': (u'txantiloi dokumentazioa', u'/dok'),
            'fa': (u'/doc', u'/توضیحات'),
            # fi: no idea how to handle this type of subpage at :Metasivu:
            'fi': ((), ),
            'fr': ('/Documentation',),
            'hsb': (u'/Dokumentacija', ),
            'it': (u'/Man', ),
            'ka': (u'/ინფო', ),
            'ko': (u'/설명문서', ),
            'no': (u'/dok', ),
            'nn': (u'/dok', ),
            'pl': (u'/opis', ),
            'sk': (u'/Dokumentácia', ),
            'sr': ('/док', ),
            'sv': (u'/dok', ),
            'uk': (u'/Документація', ),
            'ur': ('/doc', '/دستاویز'),
        }

        # Templates that indicate an edit should be avoided
        self.edit_restricted_templates = {
            'ar': ('تحرر',),
            'bs': ('Izmjena u toku',),
            'cs': ('Pracuje se', 'Archiv', 'Archiv Wikipedie',
                   'Archiv diskuse', 'Archivace start', 'Posloupnost archivů',
                   'Rfa-archiv-start', 'Rfc-archiv-start',),
            'de': ('Inuse', 'In use', 'In bearbeitung', 'Inbearbeitung',
                   'Archiv',),
            'en': ('Inuse', 'In use'),
            'fa': ('ویرایش',),
            'fr': ('En cours', 'Plusieurs en cours', 'Correction en cours',
                   'Inuse', 'Remix',),
            'hr': ('Radovi',),
            'sr': ('Радови у току', 'Рут',),
            'ur': ('زیر ترمیم',),
            'zh': ('Inuse',),
        }

    def get_known_families(self, site):
        """Override the family interwiki prefixes for each site."""
        # In Swedish Wikipedia 's:' is part of page title not a family
        # prefix for 'wikisource'.
        if site.code == 'sv':
            d = self.known_families.copy()
            d.pop('s')
            d['src'] = 'wikisource'
            return d
        else:
            return self.known_families

    def code2encodings(self, code):
        """Return a list of historical encodings for a specific site."""
        # Historic compatibility
        if code == 'pl':
            return 'utf-8', 'iso8859-2'
        if code == 'ru':
            return 'utf-8', 'iso8859-5'
        if code in self.latin1old:
            return 'utf-8', 'iso-8859-1'
        return self.code2encoding(code)
