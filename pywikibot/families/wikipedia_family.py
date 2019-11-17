# -*- coding: utf-8 -*-
"""Family module for Wikipedia."""
#
# (C) Pywikibot team, 2004-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family


# The Wikimedia family that is known as Wikipedia, the Free Encyclopedia
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family module for Wikipedia."""

    name = 'wikipedia'

    closed_wikis = [
        # See:
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/closed.dblist
        'aa', 'cho', 'ho', 'hz', 'ii', 'kj', 'kr', 'mh', 'mus', 'ng', 'ten',
    ]

    removed_wikis = [
        # See:
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/deleted.dblist
        'dk', 'ru-sib', 'tlh', 'tokipona', 'zh_cn', 'zh_tw',
    ]

    languages_by_size = [
        'en', 'ceb', 'sv', 'de', 'fr', 'nl', 'ru', 'it', 'es', 'pl', 'war',
        'vi', 'ja', 'zh', 'pt', 'ar', 'uk', 'fa', 'ca', 'sr', 'no', 'id', 'ko',
        'fi', 'hu', 'sh', 'cs', 'ro', 'eu', 'tr', 'ms', 'eo', 'hy', 'bg', 'da',
        'ce', 'he', 'sk', 'zh-min-nan', 'kk', 'min', 'hr', 'et', 'lt', 'be',
        'el', 'sl', 'gl', 'azb', 'az', 'simple', 'nn', 'ur', 'hi', 'th', 'ka',
        'uz', 'la', 'ta', 'vo', 'cy', 'mk', 'ast', 'tg', 'lv', 'mg', 'tt',
        'af', 'oc', 'bs', 'ky', 'sq', 'bn', 'tl', 'zh-yue', 'new', 'te',
        'be-tarask', 'br', 'ml', 'pms', 'su', 'nds', 'lb', 'ht', 'jv', 'sco',
        'mr', 'sw', 'ga', 'szl', 'pnb', 'ba', 'is', 'my', 'fy', 'cv', 'lmo',
        'an', 'ne', 'pa', 'yo', 'bar', 'io', 'gu', 'als', 'ku', 'scn', 'kn',
        'bpy', 'ckb', 'arz', 'wuu', 'ia', 'qu', 'mn', 'bat-smg', 'si', 'wa',
        'cdo', 'or', 'gd', 'yi', 'am', 'nap', 'bug', 'ilo', 'mai', 'hsb',
        'map-bms', 'xmf', 'fo', 'mzn', 'li', 'vec', 'sd', 'diq', 'eml', 'sah',
        'os', 'sa', 'ps', 'ace', 'mrj', 'mhr', 'zh-classical', 'nv', 'hif',
        'frr', 'bcl', 'roa-tara', 'hak', 'pam', 'nso', 'km', 'hyw', 'se',
        'rue', 'mi', 'vls', 'nah', 'bh', 'nds-nl', 'crh', 'gan', 'vep', 'sc',
        'as', 'ab', 'glk', 'shn', 'bo', 'myv', 'co', 'so', 'tk', 'fiu-vro',
        'lrc', 'kv', 'csb', 'gv', 'sn', 'udm', 'zea', 'ay', 'ie', 'pcd', 'nrm',
        'kab', 'ug', 'lez', 'stq', 'ha', 'kw', 'mwl', 'haw', 'gn', 'gom', 'rm',
        'lij', 'lfn', 'lad', 'lo', 'koi', 'mt', 'frp', 'fur', 'dsb', 'dty',
        'ang', 'ext', 'olo', 'ln', 'cbk-zam', 'dv', 'bjn', 'ksh', 'gag', 'pfl',
        'pi', 'pag', 'av', 'gor', 'bxr', 'xal', 'krc', 'za', 'pap', 'kaa',
        'pdc', 'tyv', 'rw', 'sat', 'to', 'kl', 'nov', 'jam', 'arc', 'kbp',
        'kbd', 'tpi', 'tet', 'ig', 'ki', 'wo', 'zu', 'na', 'jbo', 'roa-rup',
        'tcy', 'lbe', 'bi', 'ty', 'mdf', 'kg', 'lg', 'inh', 'srn', 'atj', 'xh',
        'ltg', 'ban', 'chr', 'sm', 'pih', 'om', 'ak', 'tn', 'cu', 'tw', 'ts',
        'got', 'rmy', 'bm', 'st', 'chy', 'rn', 'tum', 'ny', 'ch', 'ss', 'pnt',
        'nqo', 'fj', 'ady', 'iu', 've', 'ee', 'mnw', 'ks', 'ik', 'sg', 'ff',
        'dz', 'ti', 'din', 'cr',
    ]

    # Sites we want to edit but not count as real languages
    test_codes = ['test', 'test2']

    # Templates that indicate a category redirect
    # Redirects to these templates are automatically included
    category_redirect_templates = {
        '_default': (),
        'ar': ('تحويل تصنيف',),
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

    # families that redirect their interlanguage links here.
    interwiki_forwarded_from = [
        'commons',
        'incubator',
        'mediawiki',
        'meta',
        'outreach',
        'species',
        'test',
        'wikimania'
    ]

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'ab', 'ace', 'ady', 'af', 'ak', 'als', 'am', 'an', 'ang', 'ar',
        'arc', 'arz', 'as', 'ast', 'atj', 'av', 'ay', 'az', 'ba', 'bar',
        'bat-smg', 'bcl', 'be', 'be-tarask', 'bg', 'bh', 'bi', 'bjn', 'bm',
        'bo', 'bpy', 'bug', 'bxr', 'ca', 'cbk-zam', 'cdo', 'ce', 'ceb', 'ch',
        'chr', 'chy', 'ckb', 'co', 'cr', 'crh', 'cs', 'csb', 'cu', 'cv', 'cy',
        'da', 'diq', 'dsb', 'dty', 'dz', 'ee', 'el', 'eml', 'en', 'eo', 'et',
        'eu', 'ext', 'fa', 'ff', 'fi', 'fj', 'fo', 'frp', 'frr', 'fur', 'ga',
        'gag', 'gan', 'gd', 'glk', 'gn', 'gom', 'gor', 'got', 'gu', 'gv', 'ha',
        'hak', 'haw', 'he', 'hi', 'hif', 'hr', 'hsb', 'ht', 'hu', 'hy', 'ia',
        'ie', 'ig', 'ik', 'ilo', 'inh', 'io', 'iu', 'ja', 'jam', 'jbo', 'jv',
        'ka', 'kaa', 'kab', 'kbd', 'kg', 'ki', 'kk', 'kl', 'km', 'kn', 'ko',
        'koi', 'krc', 'ks', 'ku', 'kv', 'kw', 'ky', 'la', 'lad', 'lb', 'lbe',
        'lez', 'lfn', 'lg', 'li', 'lij', 'lmo', 'ln', 'lo', 'lt', 'ltg', 'lv',
        'map-bms', 'mdf', 'meta', 'mg', 'mhr', 'mi', 'mk', 'ml', 'mn', 'mrj',
        'ms', 'mwl', 'my', 'myv', 'mzn', 'na', 'nah', 'nap', 'nds_nl', 'ne',
        'new', 'nl', 'no', 'nov', 'nrm', 'nso', 'nv', 'ny', 'oc', 'olo', 'om',
        'or', 'os', 'pa', 'pag', 'pam', 'pap', 'pdc', 'pfl', 'pi', 'pih',
        'pms', 'pnb', 'pnt', 'ps', 'qu', 'rm', 'rmy', 'rn', 'roa-rup',
        'roa-tara', 'ru', 'rue', 'rw', 'sa', 'sah', 'sc', 'scn', 'sco', 'sd',
        'se', 'sg', 'sh', 'shn', 'si', 'simple', 'sk', 'sm', 'sn', 'so', 'srn',
        'ss', 'st', 'stq', 'su', 'sv', 'sw', 'szl', 'ta', 'tcy', 'te', 'tet',
        'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tpi', 'tr', 'ts', 'tt',
        'tum', 'tw', 'ty', 'tyv', 'udm', 'ug', 'uz', 've', 'vec', 'vep', 'vls',
        'vo', 'wa', 'war', 'wo', 'xal', 'xh', 'xmf', 'yi', 'yo', 'za', 'zea',
        'zh', 'zh-classical', 'zh-min-nan', 'zh-yue', 'zu',
    ]

    # On most Wikipedias page names must start with a capital letter,
    # but some languages don't use this.
    nocapitalize = ['jbo']

    # Languages that used to be coded in iso-8859-1
    latin1old = [
        'de', 'en', 'et', 'es', 'ia', 'la', 'af', 'cs', 'fr', 'pt', 'sl',
        'bs', 'fy', 'vi', 'lt', 'fi', 'it', 'no', 'simple', 'gl', 'eu',
        'nds', 'co', 'mi', 'mr', 'id', 'lv', 'sw', 'tt', 'uk', 'vo', 'ga',
        'na', 'es', 'nl', 'da', 'dk', 'sv', 'test']

    # Subpages for documentation.
    # TODO: List is incomplete, to be completed for missing languages.
    # TODO: Remove comments for appropriate pages
    doc_subpages = {
        '_default': (('/doc', ),
                     ['ar', 'bn', 'cs', 'da', 'en', 'es', 'hr',
                      'hu', 'id', 'ilo', 'ja', 'ms',
                      'pt', 'ro', 'ru', 'simple', 'sh', 'vi', 'zh']
                     ),
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
        'bs': ('Izmjena u toku',),
        'cs': ('Pracuje se',),
        'de': ('Inuse', 'In use', 'In bearbeitung', 'Inbearbeitung',),
        'en': ('Inuse', 'In use'),
        'fa': ('ویرایش',),
        'fr': ('En cours', 'Plusieurs en cours', 'Correction en cours',
               'Inuse', 'Remix',),
        'he': ('בעבודה',),
        'hr': ('Radovi',),
        'sr': ('Радови у току', 'Рут',),
        'ur': ('زیر ترمیم',),
        'zh': ('Inuse',),
    }

    # Archive templates that indicate an edit of non-archive bots
    # should be avoided
    archived_page_templates = {
        'cs': ('Archiv', 'Archiv Wikipedie', 'Archiv diskuse',
               'Archivace start', 'Posloupnost archivů',
               'Rfa-archiv-start', 'Rfc-archiv-start',),
        'de': ('Archiv',),
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
