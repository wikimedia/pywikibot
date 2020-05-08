# -*- coding: utf-8 -*-
"""Family module for Wikipedia."""
#
# (C) Pywikibot team, 2004-2020
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
        'vi', 'ja', 'zh', 'ar', 'pt', 'uk', 'fa', 'ca', 'sr', 'no', 'id', 'ko',
        'fi', 'arz', 'hu', 'cs', 'sh', 'ro', 'zh-min-nan', 'eu', 'tr', 'ms',
        'eo', 'hy', 'he', 'bg', 'da', 'ce', 'azb', 'sk', 'kk', 'min', 'hr',
        'et', 'lt', 'be', 'el', 'sl', 'gl', 'simple', 'az', 'ur', 'nn', 'hi',
        'th', 'ka', 'uz', 'la', 'cy', 'ta', 'vo', 'ast', 'mk', 'lv', 'tg',
        'mg', 'af', 'tt', 'bn', 'oc', 'zh-yue', 'bs', 'ky', 'sq', 'new', 'tl',
        'be-tarask', 'te', 'ml', 'br', 'nds', 'pms', 'su', 'sw', 'ht', 'lb',
        'jv', 'mr', 'sco', 'pnb', 'ga', 'szl', 'ba', 'is', 'my', 'fy', 'cv',
        'lmo', 'an', 'pa', 'ne', 'yo', 'wuu', 'bar', 'io', 'gu', 'ku', 'als',
        'ckb', 'kn', 'scn', 'bpy', 'vec', 'ia', 'qu', 'mn', 'bat-smg', 'or',
        'si', 'diq', 'cdo', 'ilo', 'gd', 'yi', 'am', 'nap', 'nv', 'bug', 'xmf',
        'wa', 'hsb', 'mai', 'sd', 'map-bms', 'fo', 'mzn', 'li', 'eml', 'sah',
        'os', 'sa', 'ps', 'frr', 'bcl', 'ace', 'zh-classical', 'mrj', 'mhr',
        'hif', 'hak', 'roa-tara', 'pam', 'nso', 'km', 'hyw', 'se', 'rue',
        'crh', 'mi', 'vls', 'bh', 'shn', 'nah', 'nds-nl', 'as', 'sc', 'vep',
        'gan', 'ab', 'glk', 'myv', 'bo', 'so', 'co', 'tk', 'fiu-vro', 'gor',
        'sn', 'lrc', 'kv', 'csb', 'gv', 'ha', 'udm', 'ie', 'ay', 'pcd', 'zea',
        'kab', 'nrm', 'ug', 'lez', 'stq', 'kw', 'haw', 'lfn', 'lij', 'mwl',
        'gn', 'frp', 'gom', 'rm', 'lo', 'lad', 'mt', 'koi', 'fur', 'olo',
        'dsb', 'dty', 'ang', 'ext', 'ln', 'sat', 'cbk-zam', 'bjn', 'dv', 'ksh',
        'gag', 'ban', 'pfl', 'pag', 'pi', 'tyv', 'av', 'zu', 'bxr', 'xal',
        'krc', 'pap', 'za', 'kaa', 'pdc', 'rw', 'szy', 'to', 'arc', 'nov',
        'jam', 'tpi', 'kbp', 'kbd', 'ig', 'na', 'tet', 'wo', 'ki', 'tcy',
        'inh', 'jbo', 'roa-rup', 'bi', 'lbe', 'kg', 'ty', 'mdf', 'lg', 'atj',
        'srn', 'xh', 'gcr', 'ltg', 'fj', 'chr', 'sm', 'got', 'kl', 'ak', 'pih',
        'om', 'cu', 'tn', 'tw', 'st', 'ts', 'rmy', 'bm', 'chy', 'rn', 'nqo',
        'tum', 'ny', 'mnw', 'ch', 'ss', 'pnt', 'iu', 'ady', 'ks', 've', 'ee',
        'ik', 'sg', 'ff', 'ti', 'dz', 'din', 'cr',
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
        'fr': ('En cours',),
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

    def encodings(self, code):
        """Return a list of historical encodings for a specific site."""
        # Historic compatibility
        if code == 'pl':
            return 'utf-8', 'iso8859-2'
        if code == 'ru':
            return 'utf-8', 'iso8859-5'
        if code in self.latin1old:
            return 'utf-8', 'iso-8859-1'
        return super(Family, self).encodings(code)
