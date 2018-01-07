# -*- coding: utf-8 -*-
"""Family module for Wikipedia."""
#
# (C) Pywikibot team, 2004-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family

__version__ = '$Id$'


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
            'en', 'ceb', 'sv', 'de', 'fr', 'nl', 'ru', 'it', 'es', 'war', 'pl',
            'vi', 'ja', 'pt', 'zh', 'uk', 'fa', 'ca', 'ar', 'no', 'sh', 'fi',
            'hu', 'id', 'ko', 'cs', 'ro', 'sr', 'ms', 'tr', 'eu', 'eo', 'bg',
            'hy', 'da', 'zh-min-nan', 'sk', 'min', 'kk', 'he', 'lt', 'hr',
            'et', 'ce', 'sl', 'be', 'gl', 'el', 'nn', 'simple', 'az', 'uz',
            'la', 'ur', 'hi', 'th', 'vo', 'ka', 'ta', 'cy', 'tg', 'mk', 'tl',
            'mg', 'oc', 'lv', 'ky', 'bs', 'tt', 'new', 'sq', 'te', 'pms',
            'zh-yue', 'br', 'be-tarask', 'azb', 'ast', 'bn', 'ml', 'ht', 'jv',
            'lb', 'mr', 'sco', 'af', 'pnb', 'ga', 'is', 'ba', 'cv', 'fy', 'su',
            'sw', 'my', 'lmo', 'an', 'yo', 'ne', 'pa', 'gu', 'io', 'nds',
            'scn', 'bpy', 'als', 'bar', 'ku', 'kn', 'ia', 'ckb', 'qu', 'mn',
            'arz', 'bat-smg', 'gd', 'wa', 'nap', 'si', 'yi', 'bug', 'am',
            'cdo', 'or', 'map-bms', 'fo', 'mzn', 'hsb', 'xmf', 'mai', 'li',
            'sah', 'sa', 'vec', 'ilo', 'os', 'mrj', 'hif', 'mhr', 'bh', 'eml',
            'roa-tara', 'ps', 'diq', 'pam', 'sd', 'hak', 'nso', 'se',
            'zh-classical', 'bcl', 'ace', 'mi', 'nah', 'nds-nl', 'szl', 'wuu',
            'gan', 'rue', 'frr', 'vls', 'km', 'bo', 'vep', 'glk', 'sc', 'crh',
            'fiu-vro', 'co', 'lrc', 'tk', 'kv', 'csb', 'so', 'gv', 'as', 'lad',
            'myv', 'zea', 'nv', 'ay', 'udm', 'lez', 'stq', 'ie', 'kw', 'nrm',
            'pcd', 'mwl', 'rm', 'koi', 'ab', 'gom', 'ug', 'cbk-zam', 'lij',
            'gn', 'mt', 'fur', 'kab', 'dsb', 'dv', 'sn', 'ang', 'ext', 'ln',
            'frp', 'ksh', 'lo', 'gag', 'dty', 'pag', 'pi', 'olo', 'av', 'xal',
            'pfl', 'bxr', 'haw', 'krc', 'pap', 'kaa', 'rw', 'pdc', 'bjn', 'to',
            'nov', 'kl', 'ha', 'arc', 'jam', 'kbd', 'tyv', 'tpi', 'tet', 'ig',
            'ki', 'na', 'roa-rup', 'lbe', 'jbo', 'ty', 'bi', 'mdf', 'za', 'kg',
            'lg', 'wo', 'srn', 'tcy', 'zu', 'chr', 'kbp', 'ltg', 'sm', 'om',
            'xh', 'rmy', 'tn', 'cu', 'pih', 'rn', 'chy', 'tw', 'tum', 'ts',
            'st', 'got', 'pnt', 'ss', 'ch', 'bm', 'fj', 'ady', 'iu', 'ny',
            'atj', 'ee', 'ks', 'ak', 'ik', 've', 'sg', 'ff', 'dz', 'ti', 'cr',
            'din',
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
            'fr': (u'/documentation', ),
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
