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
        'mus', 'ng', 'quality', 'strategy', 'ten', 'usability',
        'wikimania2005', 'wikimania2006', 'wikimania2007', 'wikimania2008',
        'wikimania2009', 'wikimania2010', 'wikimania2011', 'wikimania2012',
        'wikimania2013', 'wikimania2014', 'wikimania2015',
    ]

    removed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=deleted.dblist
        'dk', 'ru-sib', 'tlh', 'tokipona', 'zh_cn', 'zh_tw',
    ]

    def __init__(self):
        """Constructor."""
        self.languages_by_size = [
            'en', 'ceb', 'sv', 'de', 'nl', 'fr', 'ru', 'it', 'es', 'war', 'pl',
            'vi', 'ja', 'pt', 'zh', 'uk', 'fa', 'ca', 'ar', 'no', 'sh', 'fi',
            'hu', 'id', 'ko', 'cs', 'ro', 'sr', 'ms', 'tr', 'eu', 'eo', 'bg',
            'da', 'hy', 'min', 'kk', 'sk', 'zh-min-nan', 'he', 'lt', 'hr',
            'ce', 'et', 'sl', 'be', 'gl', 'nn', 'el', 'uz', 'la', 'simple',
            'ur', 'vo', 'az', 'hi', 'th', 'ka', 'ta', 'cy', 'mk', 'mg', 'oc',
            'lv', 'bs', 'new', 'tt', 'tl', 'ky', 'tg', 'te', 'sq', 'pms', 'br',
            'be-tarask', 'zh-yue', 'ht', 'ml', 'bn', 'jv', 'lb', 'ast', 'mr',
            'af', 'sco', 'pnb', 'is', 'ga', 'cv', 'ba', 'su', 'fy', 'sw', 'my',
            'lmo', 'an', 'yo', 'ne', 'gu', 'io', 'nds', 'pa', 'scn', 'bpy',
            'azb', 'als', 'ku', 'bar', 'kn', 'ia', 'qu', 'ckb', 'mn', 'arz',
            'bat-smg', 'wa', 'nap', 'gd', 'bug', 'yi', 'am', 'si', 'map-bms',
            'cdo', 'or', 'fo', 'mzn', 'hsb', 'li', 'sah', 'mai', 'sa', 'vec',
            'ilo', 'os', 'mrj', 'xmf', 'hif', 'mhr', 'roa-tara', 'bh', 'eml',
            'pam', 'diq', 'ps', 'sd', 'nso', 'hak', 'se', 'mi', 'bcl', 'nah',
            'nds-nl', 'gan', 'zh-classical', 'vls', 'rue', 'wuu', 'szl', 'glk',
            'bo', 'vep', 'sc', 'fiu-vro', 'co', 'lrc', 'crh', 'tk', 'kv', 'km',
            'csb', 'gv', 'frr', 'as', 'so', 'lad', 'zea', 'ace', 'ay', 'udm',
            'myv', 'lez', 'kw', 'stq', 'ie', 'nrm', 'mwl', 'pcd', 'nv', 'koi',
            'rm', 'gom', 'ug', 'lij', 'mt', 'fur', 'gn', 'dsb', 'cbk-zam',
            'dv', 'ang', 'ext', 'ln', 'kab', 'ksh', 'sn', 'gag', 'lo', 'frp',
            'pag', 'pi', 'av', 'olo', 'xal', 'pfl', 'krc', 'haw', 'bxr', 'kaa',
            'rw', 'pdc', 'pap', 'bjn', 'to', 'nov', 'kl', 'arc', 'jam', 'kbd',
            'ha', 'tyv', 'tet', 'tpi', 'ki', 'ig', 'na', 'ab', 'lbe',
            'roa-rup', 'jbo', 'ty', 'kg', 'mdf', 'za', 'wo', 'lg', 'bi', 'dty',
            'srn', 'zu', 'ltg', 'chr', 'tcy', 'sm', 'om', 'xh', 'tn', 'chy',
            'tw', 'rmy', 'cu', 'tum', 'pih', 'got', 'rn', 'pnt', 'ss', 'bm',
            'ch', 'ts', 'ady', 'iu', 'fj', 'st', 'ny', 'ee', 'ak', 'ks', 'ik',
            'sg', 've', 'dz', 'ff', 'ti', 'cr', 'atj',
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
                         ['ar', 'bn', 'cs', 'da', 'en', 'es',
                          'hu', 'id', 'ilo', 'ja', 'ms',
                          'ms', 'pt', 'ro', 'ru', 'simple', 'vi', 'zh']
                         ),
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
