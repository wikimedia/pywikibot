# -*- coding: utf-8 -*-
"""Objects representing MediaWiki families."""
#
# (C) Pywikibot team, 2004-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import collections
from importlib import import_module
from itertools import chain
import logging
from os.path import basename, dirname, splitext
import re
import string
import sys
import warnings
from warnings import warn

import pywikibot
from pywikibot.comms.http import fetch
from pywikibot import config
from pywikibot.exceptions import UnknownFamily, FamilyMaintenanceWarning
from pywikibot.tools import (
    deprecated, deprecated_args, remove_last_args, issue_deprecation_warning,
    ModuleDeprecationWrapper, FrozenDict, classproperty, PY2
)

if not PY2:
    import urllib.parse as urlparse
else:
    import urlparse


logger = logging.getLogger('pywiki.wiki.family')

# Legal characters for Family.name and Family.langs keys
# nl_nds code alias requires "_"
NAME_CHARACTERS = string.ascii_letters + string.digits
CODE_CHARACTERS = string.ascii_lowercase + string.digits + '-_'


class Family(object):

    """Parent singleton class for all wiki families."""

    def __new__(cls):
        """Allocator."""
        # any Family class defined in this file are abstract
        if cls in globals().values():
            raise TypeError(
                'Abstract Family class {0} cannot be instantiated; '
                'subclass it instead'.format(cls.__name__))

        # Override classproperty
        cls.instance = super(Family, cls).__new__(cls)
        # staticmethod is because python 2.7 binds the lambda to the class
        cls.__new__ = staticmethod(lambda cls: cls.instance)  # shortcut

        # don't use hasattr() here. consider only the class itself
        if '__init__' in cls.__dict__:
            # Initializer deprecated. Families should be immutable and any
            # instance / class modification should go to allocator (__new__).
            # The function is read from __dict__ because deprecated expect a
            # function and python 2.7 binds the method to the class.
            cls.__init__ = deprecated(cls.__dict__['__init__'])

            # Invoke initializer immediately and make initializer no-op.
            # This is to avoid repeated initializer invocation on repeated
            # invocations of the metaclass's __call__.
            cls.instance.__init__()
            cls.__init__ = lambda self: None  # no-op

        return cls.instance

    @classproperty
    def instance(cls):
        """Get the singleton instance."""
        # This is a placeholder to invoke allocator before it's allocated.
        # Allocator will override this classproperty.
        return cls()

    name = None

    langs = {}

    # For interwiki sorting order see
    # https://meta.wikimedia.org/wiki/Interwiki_sorting_order

    # The sorting order by language name from meta
    # MediaWiki:Interwiki_config-sorting_order-native-languagename
    alphabetic = [
        'ace', 'kbd', 'ady', 'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an',
        'arc', 'roa-rup', 'frp', 'as', 'ast', 'atj', 'gn', 'av', 'ay', 'az',
        'bm', 'bn', 'bjn', 'zh-min-nan', 'nan', 'map-bms', 'ba', 'be',
        'be-tarask', 'bh', 'bcl', 'bi', 'bg', 'bar', 'bo', 'bs', 'br', 'bxr',
        'ca', 'cv', 'ceb', 'cs', 'ch', 'cbk-zam', 'ny', 'sn', 'tum', 'cho',
        'co', 'cy', 'da', 'dk', 'pdc', 'de', 'dv', 'nv', 'dsb', 'dty', 'dz',
        'mh', 'et', 'el', 'eml', 'en', 'myv', 'es', 'eo', 'ext', 'eu', 'ee',
        'fa', 'hif', 'fo', 'fr', 'fy', 'ff', 'fur', 'ga', 'gv', 'gag', 'gd',
        'gl', 'gan', 'ki', 'glk', 'gu', 'gor', 'got', 'hak', 'xal', 'ko', 'ha',
        'haw', 'hy', 'hi', 'ho', 'hsb', 'hr', 'hyw', 'io', 'ig', 'ilo', 'inh',
        'bpy', 'id', 'ia', 'ie', 'iu', 'ik', 'os', 'xh', 'zu', 'is', 'it',
        'he', 'jv', 'kbp', 'kl', 'kn', 'kr', 'pam', 'krc', 'ka', 'ks', 'csb',
        'kk', 'kw', 'rw', 'rn', 'sw', 'kv', 'kg', 'gom', 'ht', 'ku', 'kj',
        'ky', 'mrj', 'lad', 'lbe', 'lo', 'ltg', 'la', 'lv', 'lb', 'lez', 'lfn',
        'lt', 'lij', 'li', 'ln', 'olo', 'jbo', 'lg', 'lmo', 'lrc', 'hu', 'mai',
        'mk', 'mg', 'ml', 'mt', 'mi', 'mr', 'xmf', 'arz', 'mzn', 'ms', 'min',
        'cdo', 'mwl', 'mdf', 'mo', 'mn', 'mus', 'my', 'nah', 'na', 'fj', 'nl',
        'nds-nl', 'cr', 'ne', 'new', 'ja', 'nqo', 'nap', 'ce', 'frr', 'pih',
        'no', 'nb', 'nn', 'nrm', 'nov', 'ii', 'oc', 'mhr', 'or', 'om', 'ng',
        'hz', 'uz', 'pa', 'pi', 'pfl', 'pag', 'pnb', 'pap', 'ps', 'jam', 'koi',
        'km', 'pcd', 'pms', 'tpi', 'nds', 'pl', 'pnt', 'pt', 'aa', 'kaa',
        'crh', 'ty', 'ksh', 'ro', 'rmy', 'rm', 'qu', 'rue', 'ru', 'sah', 'se',
        'sm', 'sa', 'sg', 'sat', 'sc', 'sco', 'stq', 'st', 'nso', 'tn', 'sq',
        'scn', 'si', 'simple', 'sd', 'ss', 'sk', 'sl', 'cu', 'szl', 'so',
        'ckb', 'srn', 'sr', 'sh', 'su', 'fi', 'sv', 'tl', 'shn', 'ta', 'kab',
        'roa-tara', 'tt', 'te', 'tet', 'th', 'ti', 'tg', 'to', 'chr', 'chy',
        've', 'tcy', 'tr', 'azb', 'tk', 'tw', 'tyv', 'din', 'udm', 'bug', 'uk',
        'ur', 'ug', 'za', 'vec', 'vep', 'vi', 'vo', 'fiu-vro', 'wa',
        'zh-classical', 'vls', 'war', 'wo', 'wuu', 'ts', 'yi', 'yo', 'zh-yue',
        'diq', 'zea', 'bat-smg', 'zh', 'zh-tw', 'zh-cn'
    ]

    # The revised sorting order by first word from meta
    # MediaWiki:Interwiki_config-sorting_order-native-languagename-firstword
    alphabetic_revised = [
        'ace', 'ady', 'kbd', 'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an',
        'arc', 'roa-rup', 'frp', 'as', 'ast', 'atj', 'gn', 'av', 'ay', 'az',
        'bjn', 'id', 'ms', 'bm', 'bn', 'zh-min-nan', 'nan', 'map-bms', 'jv',
        'su', 'ba', 'min', 'be', 'be-tarask', 'bh', 'bcl', 'bi', 'bar', 'bo',
        'bs', 'br', 'bug', 'bg', 'bxr', 'ca', 'ceb', 'cv', 'cs', 'ch',
        'cbk-zam', 'ny', 'sn', 'tum', 'cho', 'co', 'cy', 'da', 'dk', 'pdc',
        'de', 'dv', 'nv', 'dsb', 'na', 'dty', 'dz', 'mh', 'et', 'el', 'eml',
        'en', 'myv', 'es', 'eo', 'ext', 'eu', 'ee', 'fa', 'hif', 'fo', 'fr',
        'fy', 'ff', 'fur', 'ga', 'gv', 'sm', 'gag', 'gd', 'gl', 'gan', 'ki',
        'glk', 'gu', 'got', 'hak', 'xal', 'ko', 'ha', 'haw', 'hy', 'hi', 'ho',
        'hsb', 'hr', 'hyw', 'io', 'ig', 'ilo', 'inh', 'bpy', 'ia', 'ie', 'iu',
        'ik', 'os', 'xh', 'zu', 'is', 'it', 'he', 'kl', 'kn', 'kr', 'pam',
        'ka', 'ks', 'csb', 'kk', 'kw', 'rw', 'ky', 'rn', 'mrj', 'sw', 'kv',
        'kg', 'gom', 'gor', 'ht', 'ku', 'shn', 'kj', 'lad', 'lbe', 'lez',
        'lfn', 'lo', 'la', 'ltg', 'lv', 'to', 'lb', 'lt', 'lij', 'li', 'ln',
        'olo', 'jbo', 'lg', 'lmo', 'lrc', 'hu', 'mai', 'mk', 'mg', 'ml', 'krc',
        'mt', 'mi', 'mr', 'xmf', 'arz', 'mzn', 'cdo', 'mwl', 'koi', 'mdf',
        'mo', 'mn', 'mus', 'my', 'nah', 'fj', 'nl', 'nds-nl', 'cr', 'ne',
        'new', 'ja', 'nqo', 'nap', 'ce', 'frr', 'pih', 'no', 'nb', 'nn', 'nrm',
        'nov', 'ii', 'oc', 'mhr', 'or', 'om', 'ng', 'hz', 'uz', 'pa', 'pi',
        'pfl', 'pag', 'pnb', 'pap', 'ps', 'jam', 'km', 'pcd', 'pms', 'nds',
        'pl', 'pnt', 'pt', 'aa', 'kaa', 'crh', 'ty', 'ksh', 'ro', 'rmy', 'rm',
        'qu', 'ru', 'rue', 'sah', 'se', 'sa', 'sg', 'sat', 'sc', 'sco', 'stq',
        'st', 'nso', 'tn', 'sq', 'scn', 'si', 'simple', 'sd', 'ss', 'sk', 'sl',
        'cu', 'szl', 'so', 'ckb', 'srn', 'sr', 'sh', 'fi', 'sv', 'tl', 'ta',
        'kab', 'kbp', 'roa-tara', 'tt', 'te', 'tet', 'th', 'vi', 'ti', 'tg',
        'tpi', 'chr', 'chy', 've', 'tcy', 'tr', 'azb', 'tk', 'tw', 'tyv',
        'din', 'udm', 'uk', 'ur', 'ug', 'za', 'vec', 'vep', 'vo', 'fiu-vro',
        'wa', 'zh-classical', 'vls', 'war', 'wo', 'wuu', 'ts', 'yi', 'yo',
        'zh-yue', 'diq', 'zea', 'bat-smg', 'zh', 'zh-tw', 'zh-cn'
    ]

    # Order for fy: alphabetical by code, but y counts as i
    fyinterwiki = alphabetic[:]
    fyinterwiki.remove('nb')
    fyinterwiki.sort(key=lambda x:
                     x.replace('y', 'i') + x.count('y') * '!')

    # letters that can follow a wikilink and are regarded as part of
    # this link
    # This depends on the linktrail setting in LanguageXx.php and on
    # [[MediaWiki:Linktrail]].
    # Note: this is a regular expression.
    linktrails = {
        '_default': '[a-z]*',
        'ab': '[a-zабвгҕдежзӡикқҟлмнопҧрстҭуфхҳцҵчҷҽҿшыҩџьә]*',
        'als': '[äöüßa-z]*',
        'an': '[a-záéíóúñ]*',
        'ar': '[a-zء-ي]*',
        'arz': '[a-zء-ي]*',
        'ast': '[a-záéíóúñ]*',
        'atj': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'av': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'ay': '[a-záéíóúñ]*',
        'az': '[a-zçəğıöşü]*',
        'azb': '[ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیآأئؤة‌]*',
        'bar': '[äöüßa-z]*',
        'bat-smg': '[a-ząčęėįšųūž]*',
        'be': '[абвгґджзеёжзійклмнопрстуўфхцчшыьэюяćčłńśšŭźža-z]*',
        'be-tarask': '[абвгґджзеёжзійклмнопрстуўфхцчшыьэюяćčłńśšŭźža-z]*',
        'bg': '[a-zабвгдежзийклмнопрстуфхцчшщъыьэюя]*',
        'bm': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'bn': '[ঀ-৿]*',
        'bpy': '[ঀ-৿]*',
        'bs': '[a-zćčžšđž]*',
        'bxr': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'ca': '[a-zàèéíòóúç·ïü]*',
        'cbk-zam': '[a-záéíóúñ]*',
        'ce': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'ckb': '[ئابپتجچحخدرڕزژسشعغفڤقکگلڵمنوۆهھەیێ‌]*',
        'co': '[a-zàéèíîìóòúù]*',
        'crh': '[a-zâçğıñöşüа-яёʺʹ“»]*',
        'cs': '[a-záčďéěíňóřšťúůýž]*',
        'csb': '[a-zęóąśłżźćńĘÓĄŚŁŻŹĆŃ]*',
        'cu': ('[a-zабвгдеєжѕзїіıићклмнопсстѹфхѡѿцчшщъыьѣюѥѧѩѫѭѯѱѳѷѵґѓђё'
               'јйљњќуўџэ҄я“»]*'),
        'cv': '[a-zа-яĕçăӳ"»]*',
        'cy': '[àáâèéêìíîïòóôûŵŷa-z]*',
        'da': '[a-zæøå]*',
        'de': '[äöüßa-z]*',
        'din': '[äëɛɛ̈éɣïŋöɔɔ̈óa-z]*',
        'dsb': '[äöüßa-z]*',
        'el': ('[a-zαβγδεζηθικλμνξοπρστυφχψωςΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩάέή'
               'ίόύώϊϋΐΰΆΈΉΊΌΎΏΪΫ]*'),
        'eml': '[a-zàéèíîìóòúù]*',
        'es': '[a-záéíóúñ]*',
        'et': '[äöõšüža-z]*',
        'eu': '[a-záéíóúñ]*',
        'ext': '[a-záéíóúñ]*',
        'fa': '[ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیآأئؤة‌]*',
        'ff': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'fi': '[a-zäö]*',
        'fiu-vro': '[äöõšüža-z]*',
        'fo': '[áðíóúýæøa-z]*',
        'fr': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'frp': '[a-zàâçéèêîœôû·’æäåāăëēïīòöōùü‘]*',
        'frr': '[a-zäöüßåāđē]*',
        'fur': '[a-zàéèíîìóòúù]*',
        'fy': '[a-zàáèéìíòóùúâêîôûäëïöü]*',
        'gag': '[a-zÇĞçğİıÖöŞşÜüÂâÎîÛû]*',
        'gcr': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'gl': '[áâãàéêẽçíòóôõq̃úüűũa-z]*',
        'glk': '[ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیآأئؤة‌]*',
        'gn': '[a-záéíóúñ]*',
        'gu': '[઀-૿]*',
        'he': '[a-zא-ת]*',
        'hi': '[a-zऀ-ॣ०-꣠-ꣿ]*',
        'hr': '[čšžćđßa-z]*',
        'hsb': '[äöüßa-z]*',
        'ht': '[a-zàèòÀÈÒ]*',
        'hu': '[a-záéíóúöüőűÁÉÍÓÚÖÜŐŰ]*',
        'hy': '[a-zաբգդեզէըթժիլխծկհձղճմյնշոչպջռսվտրցւփքօֆև«»]*',
        'hyw': '[a-zաբգդեզէըթժիլխծկհձղճմյնշոչպջռսվտրցւփքօֆև«»]*',
        'inh': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'is': '[áðéíóúýþæöa-z-–]*',
        'it': '[a-zàéèíîìóòúù]*',
        'ka': '[a-zაბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ“»]*',
        'kab': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'kbp': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'kk': ('[a-zäçéğıïñöşüýʺʹа-яёәғіқңөұүһ'
               'ٴابپتجحدرزسشعفقكلمنڭەوۇۋۆىيچھ“»]*'),
        'kl': '[a-zæøå]*',
        'koi': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'krc': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'ksh': '[äöüėëĳßəğåůæœça-z]*',
        'ku': '[a-zçêîşûẍḧÇÊÎŞÛẌḦ]*',
        'kv': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'lad': '[a-záéíóúñ]*',
        'lb': '[äöüßa-z]*',
        'lbe': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюяӀ1“»]*',
        'lez': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'li': '[a-zäöüïëéèà]*',
        'lij': '[a-zàéèíîìóòúù]*',
        'lmo': '[a-zàéèíîìóòúù]*',
        'ln': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'lrc': '[ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیآأئؤة‌]*',
        'lt': '[a-ząčęėįšųūž]*',
        'ltg': '[a-zA-ZĀāČčĒēĢģĪīĶķĻļŅņŠšŪūŽž]*',
        'lv': '[a-zA-ZĀāČčĒēĢģĪīĶķĻļŅņŠšŪūŽž]*',
        'mai': '[a-zऀ-ॣ०-꣠-ꣿ]*',
        'mdf': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'mg': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'mhr': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'mk': '[a-zабвгдѓежзѕијклљмнњопрстќуфхцчџш]*',
        'ml': '[a-zം-ൿ]*',
        'mn': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя“»]*',
        'mr': '[ऀ-ॣॱ-ॿ﻿‍]*',
        'mrj': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'mt': '[a-zàéèíîìóòúù]*',
        'mwl': '[áâãàéêẽçíòóôõq̃úüűũa-z]*',
        'myv': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'mzn': '[ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیآأئؤة‌]*',
        'nah': '[a-záéíóúñ]*',
        'nap': '[a-zàéèíîìóòúù]*',
        'nds': '[äöüßa-z]*',
        'nds-nl': '[a-zäöüïëéèà]*',
        'nl': '[a-zäöüïëéèà]*',
        'nn': '[æøåa-z]*',
        'no': '[æøåa-z]*',
        'nrm': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'oc': '[a-zàâçéèêîôû]*',
        'olo': '[a-zčČšŠžŽäÄöÖ]*',
        'or': '[a-z଀-୿]*',
        'pa': ('[ਁਂਃਅਆਇਈਉਊਏਐਓਔਕਖਗਘਙਚਛਜਝਞਟਠਡਢਣਤਥਦਧਨਪਫਬਭਮਯਰਲਲ਼ਵਸ਼ਸਹ਼ਾ'
               'ਿੀੁੂੇੈੋੌ੍ਖ਼ਗ਼ਜ਼ੜਫ਼ੰੱੲੳa-z]*'),
        'pcd': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'pdc': '[äöüßa-z]*',
        'pfl': '[äöüßa-z]*',
        'pl': '[a-zęóąśłżźćńĘÓĄŚŁŻŹĆŃ]*',
        'pms': '[a-zàéèíîìóòúù]*',
        'pnt': ('[a-zαβγδεζηθικλμνξοπρστυφχψωςΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ'
                'άέήίόύώϊϋΐΰΆΈΉΊΌΎΏΪΫ]*'),
        'pt': '[áâãàéêẽçíòóôõq̃úüűũa-z]*',
        'qu': '[a-záéíóúñ]*',
        'rmy': '[a-zăâîşţșțĂÂÎŞŢȘȚ]*',
        'ro': '[a-zăâîşţșțĂÂÎŞŢȘȚ]*',
        'roa-rup': '[a-zăâîşţșțĂÂÎŞŢȘȚ]*',
        'roa-tara': '[a-zàéèíîìóòúù]*',
        'ru': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'rue': '[a-zабвгґдеєжзиіїйклмнопрстуфхцчшщьєюяёъы“»]*',
        'sa': '[a-zऀ-ॣ०-꣠-ꣿ]*',
        'sah': '[a-zабвгҕдеёжзийклмнҥоөпрсһтуүфхцчшщъыьэюя]*',
        'scn': '[a-zàéèíîìóòúù]*',
        'sg': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'sh': '[a-zčćđžš]*',
        'sk': '[a-záäčďéíľĺňóôŕšťúýž]*',
        'sl': '[a-zčćđžš]*',
        'sr': ('[abvgdđežzijklljmnnjoprstćufhcčdžšабвгдђежзијклљмнњопрстћу'
               'фхцчџш]*'),
        'srn': '[a-zäöüïëéèà]*',
        'stq': '[äöüßa-z]*',
        'sv': '[a-zåäöéÅÄÖÉ]*',
        'szl': '[a-zęóąśłżźćńĘÓĄŚŁŻŹĆŃ]*',
        'ta': '[஀-௿]*',
        'te': '[ఁ-౯]*',
        'tet': '[áâãàéêẽçíòóôõq̃úüűũa-z]*',
        'tg': '[a-zабвгдеёжзийклмнопрстуфхчшъэюяғӣқўҳҷцщыь]*',
        'tk': '[a-zÄäÇçĞğŇňÖöŞşÜüÝýŽž]*',
        'tr': '[a-zÇĞçğİıÖöŞşÜüÂâÎîÛû]*',
        'tt': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюяӘәӨөҮүҖҗҢңҺһ]*',
        'ty': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'tyv': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'udm': '[a-zа-яёӝӟӥӧӵ]*',
        'uk': '[a-zабвгґдеєжзиіїйклмнопрстуфхцчшщьєюяёъы“»]*',
        'ur': '[ابپتٹثجچحخدڈذر​ڑ​زژسشصضطظعغفقکگل​م​نںوؤہھیئےآأءۃ]*',
        'uz': '[a-zʻʼ“»]*',
        'vec': '[a-zàéèíîìóòúù]*',
        'vep': '[äöõšüža-z]*',
        'vi': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'vls': '[a-zäöüïëéèà]*',
        'wa': '[a-zåâêîôûçéè]*',
        'wo': '[a-zàâçéèêîôûäëïöüùÇÉÂÊÎÔÛÄËÏÖÜÀÈÙ]*',
        'xal': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюя]*',
        'xmf': '[a-zაბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ“»]*',
        'yi': '[a-zא-ת]*',
        'zea': '[a-zäöüïëéèà]*',
    }

    # A dictionary where keys are family codes that can be used in
    # inter-family interwiki links. Do not use it directly but
    # get_known_families() instead.

    # TODO: replace this with API interwikimap call
    known_families = {
        'acronym':          'acronym',
        'advisory':         'advisory',
        'advogato':         'advogato',
        'aew':              'aew',
        'appropedia':       'appropedia',
        'aquariumwiki':     'aquariumwiki',
        'arborwiki':        'arborwiki',
        'arxiv':            'arxiv',
        'atmwiki':          'atmwiki',
        'b':                'wikibooks',
        'baden':            'baden',
        'battlestarwiki':   'battlestarwiki',
        'bcnbio':           'bcnbio',
        'beacha':           'beacha',
        'betawiki':         'translatewiki',
        'betawikiversity':  'betawikiversity',
        'bibcode':          'bibcode',
        'bibliowiki':       'bibliowiki',
        'bluwiki':          'bluwiki',
        'blw':              'blw',
        'botwiki':          'botwiki',
        'boxrec':           'boxrec',
        'brickwiki':        'brickwiki',
        'bugzilla':         'bugzilla',
        'bulba':            'bulba',
        'c':                'commons',
        'c2':               'c2',
        'c2find':           'c2find',
        'Ĉej':              'Ĉej',
        'cellwiki':         'cellwiki',
        'centralwikia':     'centralwikia',
        'chapter':          'wikimedia',
        'chej':             'chej',
        'choralwiki':       'choralwiki',
        'citizendium':      'citizendium',
        'ckwiss':           'ckwiss',
        'comixpedia':       'comixpedia',
        'commons':          'commons',
        'communityscheme':  'communityscheme',
        'comune':           'comune',
        'creativecommonswiki': 'creativecommonswiki',
        'cxej':             'cxej',
        'dcc':              'dcc',
        'dcdatabase':       'dcdatabase',
        'dcma':             'dcma',
        'debian':           'debian',
        'devmo':            'devmo',
        'dict':             'dictionary',
        'dictionary':       'dictionary',
        'disinfopedia':     'disinfopedia',
        'distributedproofreaders': 'distributedproofreaders',
        'distributedproofreadersca': 'distributedproofreadersca',
        'dk':               'dk',
        'dmoz':             'dmoz',
        'dmozs':            'dmozs',
        'doom_wiki':        'doom_wiki',
        'download':         'download',
        'dbdump':           'dbdump',
        'dpd':              'dpd',
        'drae':             'drae',
        'dreamhost':        'dreamhost',
        'drumcorpswiki':    'drumcorpswiki',
        'dwjwiki':          'dwjwiki',
        'eĉei':             'eĉei',
        'ecoreality':       'ecoreality',
        'ecxei':            'ecxei',
        'elibre':           'elibre',
        'emacswiki':        'emacswiki',
        'encyc':            'encyc',
        'energiewiki':      'energiewiki',
        'englyphwiki':      'englyphwiki',
        'enkol':            'enkol',
        'eokulturcentro':   'eokulturcentro',
        'esolang':          'esolang',
        'etherpad':         'etherpad',
        'evowiki':          'evowiki',
        'exotica':          'exotica',
        'fanimutationwiki': 'fanimutationwiki',
        'finalfantasy':     'finalfantasy',
        'finnix':           'finnix',
        'floralwiki':       'floralwiki',
        'foldoc':           'foldoc',
        'foundation':       'wikimedia',
        'foundationsite':   'foundationsite',
        'foxwiki':          'foxwiki',
        'freebio':          'freebio',
        'freebsdman':       'freebsdman',
        'freeculturewiki':  'freeculturewiki',
        'freedomdefined':   'freedomdefined',
        'freefeel':         'freefeel',
        'freekiwiki':       'freekiwiki',
        'ganfyd':           'ganfyd',
        'gardenology':      'gardenology',
        'gausswiki':        'gausswiki',
        'gentoo':           'gentoo',
        'genwiki':          'genwiki',
        'gerrit':           'gerrit',
        'git':              'git',
        'google':           'google',
        'googledefine':     'googledefine',
        'googlegroups':     'googlegroups',
        'guildwiki':        'guildwiki',
        'guc':              'guc',
        'gucprefix':        'guc',
        'gutenberg':        'gutenberg',
        'gutenbergwiki':    'gutenbergwiki',
        'hackerspaces':     'hackerspaces',
        'h2wiki':           'h2wiki',
        'hammondwiki':      'hammondwiki',
        'hdl':              'hdl',
        'heraldik':         'heraldik',
        'heroeswiki':       'heroeswiki',
        'horizonlabs':      'horizonlabs',
        'hrwiki':           'hrwiki',
        'hrfwiki':          'hrfwiki',
        'hupwiki':          'hupwiki',
        'iarchive':         'iarchive',
        'imdbname':         'imdbname',
        'imdbtitle':        'imdbtitle',
        'imdbcompany':      'imdbcompany',
        'imdbcharacter':    'imdbcharacter',
        'incubator':        'incubator',
        'infosecpedia':     'infosecpedia',
        'infosphere':       'infosphere',
        'irc':              'irc',
        'ircs':             'ircs',
        'rcirc':            'rcirc',
        'iso639-3':         'iso639-3',
        'issn':             'issn',
        'iuridictum':       'iuridictum',
        'jaglyphwiki':      'jaglyphwiki',
        'javanet':          'javanet',
        'javapedia':        'javapedia',
        'jefo':             'jefo',
        'jerseydatabase':   'jerseydatabase',
        'jira':             'jira',
        'jspwiki':          'jspwiki',
        'jstor':            'jstor',
        'kamelo':           'kamelo',
        'karlsruhe':        'karlsruhe',
        'kinowiki':         'kinowiki',
        'komicawiki':       'komicawiki',
        'kontuwiki':        'kontuwiki',
        'wikitech':         'wikitech',
        'libreplanet':      'libreplanet',
        'linguistlist':     'linguistlist',
        'linuxwiki':        'linuxwiki',
        'linuxwikide':      'linuxwikide',
        'liswiki':          'liswiki',
        'literateprograms': 'literateprograms',
        'livepedia':        'livepedia',
        'localwiki':        'localwiki',
        'lojban':           'lojban',
        'lostpedia':        'lostpedia',
        'lqwiki':           'lqwiki',
        'lugkr':            'lugkr',
        'luxo':             'luxo',
        'm':                'meta',
        'm-w':              'm-w',
        'mail':             'mail',
        'mailarchive':      'mailarchive',
        'mariowiki':        'mariowiki',
        'marveldatabase':   'marveldatabase',
        'meatball':         'meatball',
        'mw':               'mediawiki',
        'mediazilla':       'mediazilla',
        'memoryalpha':      'memoryalpha',
        'meta':             'metawiki',
        'metawiki':         'metawiki',
        'metawikimedia':    'metawiki',
        'metawikipedia':    'metawiki',
        'metawikisearch':   'metawikisearch',
        'mineralienatlas':  'mineralienatlas',
        'moinmoin':         'moinmoin',
        'monstropedia':     'monstropedia',
        'mosapedia':        'mosapedia',
        'mozcom':           'mozcom',
        'mozillawiki':      'mozillawiki',
        'mozillazinekb':    'mozillazinekb',
        'musicbrainz':      'musicbrainz',
        'mwod':             'mwod',
        'mwot':             'mwot',
        'n':                'wikinews',
        'nkcells':          'nkcells',
        'nara':             'nara',
        'nosmoke':          'nosmoke',
        'nost':             'nost',
        'nostalgia':        'nostalgia',
        'oeis':             'oeis',
        'oldwikisource':    'oldwikisource',
        'olpc':             'olpc',
        'omegawiki':        'omegawiki',
        'onelook':          'onelook',
        'openlibrary':      'openlibrary',
        'openstreetmap':    'openstreetmap',
        'openwetware':      'openwetware',
        'opera7wiki':       'opera7wiki',
        'organicdesign':    'organicdesign',
        'orthodoxwiki':     'orthodoxwiki',
        'otrs':             'otrs',
        'otrswiki':         'otrswiki',
        'ourmedia':         'ourmedia',
        'outreach':         'outreach',
        'outreachwiki':     'outreach',
        'owasp':            'owasp',
        'panawiki':         'panawiki',
        'patwiki':          'patwiki',
        'personaltelco':    'personaltelco',
        'petscan':          'petscan',
        'phab':             'phabricator',
        'phabricator':      'phabricator',
        'phwiki':           'phwiki',
        'phpwiki':          'phpwiki',
        'planetmath':       'planetmath',
        'pmeg':             'pmeg',
        'pmid':             'pmid',
        'pokewiki':         'pokewiki',
        'pokéwiki':         'pokewiki',
        'policy':           'policy',
        'purlnet':          'purlnet',
        'pyrev':            'pyrev',
        'pythonwiki':       'pythonwiki',
        'pywiki':           'pywiki',
        'psycle':           'psycle',
        'q':                'wikiquote',
        'quality':          'quality',
        'quarry':           'quarry',
        'rev':              'rev',
        'revo':             'revo',
        'rheinneckar':      'rheinneckar',
        'robowiki':         'robowiki',
        'rodovid':          'rodovid',
        'reuterswiki':      'reuterswiki',
        'rowiki':           'rowiki',
        'rt':               'rt',
        'rtfm':             'rtfm',
        's':                'wikisource',
        's23wiki':          's23wiki',
        'schoolswp':        'schoolswp',
        'scores':           'scores',
        'scoutwiki':        'scoutwiki',
        'scramble':         'scramble',
        'seapig':           'seapig',
        'seattlewiki':      'seattlewiki',
        'slwiki':           'slwiki',
        'senseislibrary':   'senseislibrary',
        'silcode':          'silcode',
        'slashdot':         'slashdot',
        'sourceforge':      'sourceforge',
        'spcom':            'spcom',
        'species':          'species',
        'squeak':           'squeak',
        'stats':            'stats',
        'stewardry':        'stewardry',
        'strategy':         'strategy',
        'strategywiki':     'strategywiki',
        'sulutil':          'sulutil',
        'swtrain':          'swtrain',
        'svn':              'svn',
        'tabwiki':          'tabwiki',
        'tclerswiki':       'tclerswiki',
        'technorati':       'technorati',
        'tenwiki':          'tenwiki',
        'testwiki':         'testwiki',
        'testwikidata':     'testwikidata',
        'test2wiki':        'test2wiki',
        'tfwiki':           'tfwiki',
        'thelemapedia':     'thelemapedia',
        'theopedia':        'theopedia',
        'thinkwiki':        'thinkwiki',
        'ticket':           'ticket',
        'tmbw':             'tmbw',
        'tmnet':            'tmnet',
        'tmwiki':           'tmwiki',
        'toolforge':        'toollabs',
        'toollabs':        'toollabs',
        'translatewiki':    'translatewiki',
        'tviv':             'tviv',
        'tvtropes':         'tvtropes',
        'twiki':            'twiki',
        'tyvawiki':         'tyvawiki',
        'umap':             'umap',
        'uncyclopedia':     'uncyclopedia',
        'unihan':           'unihan',
        'unreal':           'unreal',
        'urbandict':        'urbandict',
        'usej':             'usej',
        'usemod':           'usemod',
        'usability':        'usability',
        'utrs':             'utrs',
        'v':                'wikiversity',
        'vikidia':          'vikidia',
        'vlos':             'vlos',
        'vkol':             'vkol',
        'voipinfo':         'voipinfo',
        'votewiki':         'votewiki',
        'voy':              'wikivoyage',
        'w':                'wikipedia',
        'werelate':         'werelate',
        'wg':               'wg',
        'wikia':            'wikia',
        'wikiasite':        'wikia',
        'wikibooks':        'wikibooks',
        'wikichristian':    'wikichristian',
        'wikicities':       'wikicities',
        'wikicity':         'wikicity',
        'wikiconference':   'wikiconference',
        'wikidata':         'wikidata',
        'wikif1':           'wikif1',
        'wikifur':          'wikifur',
        'wikihow':          'wikihow',
        'wikiindex':        'wikiindex',
        'wikilemon':        'wikilemon',
        'wikilivres':       'wikilivres',
        'wikimac-de':       'wikimac-de',
        'wikimedia':        'wikimedia',
        'wikinews':         'wikinews',
        'wikinfo':          'wikinfo',
        'wikinvest':        'wikinvest',
        'wikipapers':       'wikipapers',
        'wikipedia':        'wikipedia',
        'wikipediawikipedia': 'wikipedia',
        'wikiquote':        'wikiquote',
        'wikisophia':       'wikisophoa',
        'wikisource':       'wikisource',
        'wikispecies':      'wikispecies',
        'wikispot':         'wikispot',
        'wikiskripta':      'wikiscripta',
        'labsconsole':      'labsconsole',
        'wikiti':           'wikiti',
        'wikiversity':      'wikiversity',
        'wikivoyage':       'wikivoyage',
        'wikiwikiweb':      'wikiwikiweb',
        'wikt':             'wiktionary',
        'wiktionary':       'wiktionary',
        'wipipedia':        'wipipedia',
        'wlug':             'wlug',
        'wmam':             'wmam',
        'wmar':             'wmar',
        'wmat':             'wmat',
        'wmau':             'wmau',
        'wmbd':             'wmbd',
        'wmbe':             'wmbe',
        'wmbr':             'wmbr',
        'wmca':             'wmca',
        'wmch':             'wmch',
        'wmcl':             'wmcl',
        'wmcn':             'wmcn',
        'wmco':             'wmco',
        'wmcz':             'wmcz',
        'wmdc':             'wmdc',
        'securewikidc':     'securewikidc',
        'wmdk':             'wmdk',
        'wmee':             'wmee',
        'wmec':             'wmec',
        'wmes':             'wmes',
        'wmet':             'wmet',
        'wmfdashboard':     'wmfdashboard',
        'wmfi':             'wmfi',
        'wmfr':             'wmfr',
        'wmhi':             'wmhi',
        'wmhk':             'wmhk',
        'wmid':             'wmid',
        'wmil':             'wmil',
        'wmin':             'wmin',
        'wmit':             'wmit',
        'wmke':             'wmke',
        'wmmk':             'wmmk',
        'wmmx':             'wmmx',
        'wmnl':             'wmnl',
        'wmnyc':            'wmnyc',
        'wmno':             'wmno',
        'wmpa-us':          'wmpa-us',
        'wmph':             'wmph',
        'wmpl':             'wmpl',
        'wmpt':             'wmpt',
        'wmpunjabi':        'wmpunjabi',
        'wmromd':           'wmromd',
        'wmrs':             'wmrs',
        'wmru':             'wmru',
        'wmse':             'wmse',
        'wmsk':             'wmsk',
        'wmtr':             'wmtr',
        'wmtw':             'wmtw',
        'wmua':             'wmua',
        'wmuk':             'wmuk',
        'wmve':             'wmve',
        'wmza':             'wmza',
        'wm2005':           'wm2005',
        'wm2006':           'wm2006',
        'wm2007':           'wm2007',
        'wm2008':           'wm2008',
        'wm2009':           'wm2009',
        'wm2010':           'wm2010',
        'wm2011':           'wm2011',
        'wm2012':           'wm2012',
        'wm2013':           'wm2013',
        'wm2014':           'wm2014',
        'wm2015':           'wm2015',
        'wm2016':           'wm2016',
        'wm2017':           'wm2017',
        'wm2018':           'wm2018',
        'wmania':           'wikimania',
        'wikimania':        'wikimania',
        'wmteam':           'wmteam',
        'wmf':              'wmf',
        'wookieepedia':     'wookieepedia',
        'wowwiki':          'wowwiki',
        'wqy':              'wqy',
        'wurmpedia':        'wurmpedia',
        'viaf':             'viaf',
        'zrhwiki':          'zrhwiki',
        'zum':              'zum',
        'zwiki':            'zwiki',
    }

    # A list of category redirect template names in different languages
    category_redirect_templates = {
        '_default': []
    }

    # A list of languages that use hard (not soft) category redirects
    use_hard_category_redirects = []

    # A list of disambiguation template names in different languages
    disambiguationTemplates = {
        '_default': []
    }

    # A dict of tuples for different sites with names of templates
    # that indicate an edit should be avoided
    edit_restricted_templates = {}

    # A dict of tuples for different sites with names of archive
    # templates that indicate an edit of non-archive bots
    # should be avoided
    archived_page_templates = {}

    # A list of projects that share cross-project sessions.
    cross_projects = []

    # A list with the name for cross-project cookies.
    # default for wikimedia centralAuth extensions.
    cross_projects_cookies = ['centralauth_Session',
                              'centralauth_Token',
                              'centralauth_User']
    cross_projects_cookie_username = 'centralauth_User'

    # A list with the name in the cross-language flag permissions
    cross_allowed = []

    # A dict with the name of the category containing disambiguation
    # pages for the various languages. Only one category per language,
    # and without the namespace, so add things like:
    # 'en': "Disambiguation"
    disambcatname = {}

    # DEPRECATED, stores the code of the site which have a case sensitive
    # main namespace. Use the Namespace given from the Site instead
    nocapitalize = []

    # attop is a list of languages that prefer to have the interwiki
    # links at the top of the page.
    interwiki_attop = []
    # on_one_line is a list of languages that want the interwiki links
    # one-after-another on a single line
    interwiki_on_one_line = []
    # String used as separator between interwiki links and the text
    interwiki_text_separator = '\n\n'

    # Similar for category
    category_attop = []
    # on_one_line is a list of languages that want the category links
    # one-after-another on a single line
    category_on_one_line = []
    # String used as separator between category links and the text
    category_text_separator = '\n\n'
    # When both at the bottom should categories come after interwikilinks?
    # TODO: T86284 Needed on Wikia sites, as it uses the CategorySelect
    # extension which puts categories last on all sites. TO BE DEPRECATED!
    categories_last = []

    # Which languages have a special order for putting interlanguage
    # links, and what order is it? If a language is not in
    # interwiki_putfirst, alphabetical order on language code is used.
    # For languages that are in interwiki_putfirst, interwiki_putfirst
    # is checked first, and languages are put in the order given there.
    # All other languages are put after those, in code-alphabetical
    # order.
    interwiki_putfirst = {}

    # Some families, e. g. commons and meta, are not multilingual and
    # forward interlanguage links to another family (wikipedia).
    # These families can set this variable to the name of the target
    # family.
    interwiki_forward = None

    # Some families, e. g. wikipedia, receive forwarded interlanguage
    # links from other families, e. g. incubator, commons, or meta.
    # These families can set this variable to the names of their source
    # families.
    interwiki_forwarded_from = {}

    # Which language codes no longer exist and by which language code
    # should they be replaced. If for example the language with code xx:
    # now should get code yy:, add {'xx':'yy'} to obsolete.
    interwiki_replacements = {}

    # Codes that should be removed, usually because the site has been
    # taken down.
    interwiki_removals = []

    # Language codes of the largest wikis. They should be roughly sorted
    # by size.
    languages_by_size = []

    # Some languages belong to a group where the possibility is high that
    # equivalent articles have identical titles among the group.
    language_groups = {
        # languages using the arabic script (incomplete)
        'arab': [
            'ar', 'arz', 'ps', 'sd', 'ur', 'bjn', 'ckb',
            # languages using multiple scripts, including arabic
            'kk', 'ku', 'tt', 'ug', 'pnb'
        ],
        # languages that use chinese symbols
        'chinese': [
            'wuu', 'zh', 'zh-classical', 'zh-yue', 'gan', 'ii',
            # languages using multiple/mixed scripts, including chinese
            'ja', 'za'
        ],
        # languages that use the cyrillic alphabet
        'cyril': [
            'ab', 'av', 'ba', 'be', 'be-tarask', 'bg', 'bxr', 'ce', 'cu',
            'cv', 'kbd', 'koi', 'kv', 'ky', 'mk', 'lbe', 'mdf', 'mn', 'mo',
            'myv', 'mhr', 'mrj', 'os', 'ru', 'rue', 'sah', 'tg', 'tk',
            'udm', 'uk', 'xal',
            # languages using multiple scripts, including cyrillic
            'ha', 'kk', 'sh', 'sr', 'tt'
        ],
        # languages that use a greek script
        'grec': [
            'el', 'grc', 'pnt'
            # languages using multiple scripts, including greek
        ],
        # languages that use the latin alphabet
        'latin': [
            'aa', 'ace', 'af', 'ak', 'als', 'an', 'ang', 'ast', 'ay', 'bar',
            'bat-smg', 'bcl', 'bi', 'bm', 'br', 'bs', 'ca', 'cbk-zam',
            'cdo', 'ceb', 'ch', 'cho', 'chy', 'co', 'crh', 'cs', 'csb',
            'cy', 'da', 'de', 'diq', 'dsb', 'ee', 'eml', 'en', 'eo', 'es',
            'et', 'eu', 'ext', 'ff', 'fi', 'fiu-vro', 'fj', 'fo', 'fr',
            'frp', 'frr', 'fur', 'fy', 'ga', 'gag', 'gd', 'gl', 'gn', 'gv',
            'hak', 'haw', 'hif', 'ho', 'hr', 'hsb', 'ht', 'hu', 'hz', 'ia',
            'id', 'ie', 'ig', 'ik', 'ilo', 'io', 'is', 'it', 'jbo', 'jv',
            'kaa', 'kab', 'kg', 'ki', 'kj', 'kl', 'kr', 'ksh', 'kw', 'la',
            'lad', 'lb', 'lg', 'li', 'lij', 'lmo', 'ln', 'lt', 'ltg', 'lv',
            'map-bms', 'mg', 'mh', 'mi', 'ms', 'mt', 'mus', 'mwl', 'na',
            'nah', 'nap', 'nds', 'nds-nl', 'ng', 'nl', 'nn', 'no', 'nov',
            'nrm', 'nv', 'ny', 'oc', 'om', 'pag', 'pam', 'pap', 'pcd',
            'pdc', 'pfl', 'pih', 'pl', 'pms', 'pt', 'qu', 'rm', 'rn', 'ro',
            'roa-rup', 'roa-tara', 'rw', 'sc', 'scn', 'sco', 'se', 'sg',
            'simple', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'srn', 'ss',
            'st', 'stq', 'su', 'sv', 'sw', 'szl', 'tet', 'tl', 'tn', 'to',
            'tpi', 'tr', 'ts', 'tum', 'tw', 'ty', 'uz', 've', 'vec', 'vi',
            'vls', 'vo', 'wa', 'war', 'wo', 'xh', 'yo', 'zea',
            'zh-min-nan', 'zu',
            # languages using multiple scripts, including latin
            'az', 'chr', 'ckb', 'ha', 'iu', 'kk', 'ku', 'rmy', 'sh', 'sr',
            'tt', 'ug', 'za'
        ],
        # Scandinavian languages
        'scand': [
            'da', 'fo', 'is', 'nb', 'nn', 'no', 'sv'
        ],
    }

    # LDAP domain if your wiki uses LDAP authentication,
    # https://www.mediawiki.org/wiki/Extension:LDAP_Authentication
    ldapDomain = ()

    # Allows crossnamespace interwiki linking.
    # Lists the possible crossnamespaces combinations
    # keys are originating NS
    # values are dicts where:
    #   keys are the originating langcode, or _default
    #   values are dicts where:
    #     keys are the languages that can be linked to from the lang+ns, or
    #     '_default'; values are a list of namespace numbers
    crossnamespace = collections.defaultdict(dict)
    ##
    # Examples :
    #
    # Allowing linking to pt' 102 NS from any other lang' 0 NS is
    #
    #   crossnamespace[0] = {
    #       '_default': { 'pt': [102]}
    #   }
    #
    # While allowing linking from pt' 102 NS to any other lang' = NS is
    #
    #   crossnamespace[102] = {
    #       'pt': { '_default': [0]}
    #   }

    # Some wiki farms have UrlShortener extension enabled only on the main
    # site. This value can specify this last one with (lang, family) tuple.
    shared_urlshortner_wiki = None

    _families = {}

    def __getattribute__(self, name):
        """
        Check if attribute is deprecated and warn accordingly.

        This is necessary as subclasses could prevent that message by using a
        class variable. Only penalize getting it because it must be set so that
        the backwards compatibility is still available.
        """
        if name == 'nocapitalize':
            issue_deprecation_warning('nocapitalize',
                                      "APISite.siteinfo['case'] or "
                                      "Namespace.case == 'case-sensitive'",
                                      since='20150214')
        elif name == 'known_families':
            issue_deprecation_warning('known_families',
                                      'APISite.interwiki(prefix)',
                                      since='20150503')
        elif name == 'shared_data_repository':
            issue_deprecation_warning('shared_data_repository',
                                      'APISite.data_repository()',
                                      since='20151023')
        return super(Family, self).__getattribute__(name)

    @staticmethod
    @deprecated_args(fatal=None)
    def load(fam=None):
        """Import the named family.

        @param fam: family name (if omitted, uses the configured default)
        @type fam: str
        @return: a Family instance configured for the named family.
        @raises pywikibot.exceptions.UnknownFamily: family not known
        """
        if fam is None:
            fam = config.family

        assert all(x in NAME_CHARACTERS for x in fam), \
            'Name of family %s must be ASCII characters and digits' % fam

        if fam in Family._families:
            return Family._families[fam]

        if fam in config.family_files:
            family_file = config.family_files[fam]

            if family_file.startswith(('http://', 'https://')):
                myfamily = AutoFamily(fam, family_file)
                Family._families[fam] = myfamily
                return Family._families[fam]
        else:
            raise UnknownFamily('Family %s does not exist' % fam)

        try:
            # Ignore warnings due to dots in family names.
            # TODO: use more specific filter, so that family classes can use
            #     RuntimeWarning's while loading.
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                sys.path.append(dirname(family_file))
                mod = import_module(splitext(basename(family_file))[0])
        except ImportError:
            raise UnknownFamily('Family %s does not exist' % fam)
        cls = mod.Family.instance
        if cls.name != fam:
            warn('Family name %s does not match family module name %s'
                 % (cls.name, fam), FamilyMaintenanceWarning)
        # Family 'name' and the 'langs' codes must be ascii, and the
        # codes must be lower-case due to the Site loading algorithm.
        if not all(x in NAME_CHARACTERS for x in cls.name):
            warn('Family name %s contains non-ascii characters' % cls.name,
                 FamilyMaintenanceWarning)
        for code in cls.langs.keys():
            if not all(x in CODE_CHARACTERS for x in code):
                warn('Family %s code %s contains non-ascii characters' %
                     (cls.name, code), FamilyMaintenanceWarning)
        Family._families[fam] = cls
        return cls

    @classproperty
    @deprecated('Family.codes or APISite.validLanguageLinks', since='20151014')
    def iwkeys(cls):
        """DEPRECATED: List of (interwiki_forward's) family codes."""
        if cls.interwiki_forward:
            return list(pywikibot.Family(cls.interwiki_forward).langs.keys())
        return list(cls.langs.keys())

    @deprecated('APISite.interwiki', since='20151014')
    def get_known_families(self, site):
        """DEPRECATED: Return dict of inter-family interwiki links."""
        return self.known_families

    def linktrail(self, code, fallback='_default'):
        """Return regex for trailing chars displayed as part of a link.

        Returns a string, not a compiled regular expression object.

        This reads from the family file, and **not** from
        [[MediaWiki:Linktrail]], because the MW software currently uses a
        built-in linktrail from its message files and ignores the wiki
        value.
        """
        if code in self.linktrails:
            return self.linktrails[code]
        elif fallback:
            return self.linktrails[fallback]
        else:
            raise KeyError(
                'ERROR: linktrail in language %(language_code)s unknown'
                % {'language_code': code})

    def category_redirects(self, code, fallback='_default'):
        """Return list of category redirect templates."""
        if not hasattr(self, '_catredirtemplates') or \
           code not in self._catredirtemplates:
            self._get_cr_templates(code, fallback)
        return self._catredirtemplates[code]

    def _get_cr_templates(self, code, fallback):
        """Build list of category redirect templates."""
        if not hasattr(self, '_catredirtemplates'):
            self._catredirtemplates = {}
        if code in self.category_redirect_templates:
            cr_template_tuple = self.category_redirect_templates[code]
        elif fallback and fallback in self.category_redirect_templates:
            cr_template_tuple = self.category_redirect_templates[fallback]
        else:
            self._catredirtemplates[code] = []
            return
        cr_set = set()
        site = pywikibot.Site(code, self)
        tpl_ns = site.namespaces.TEMPLATE
        for cr_template in cr_template_tuple:
            cr_page = pywikibot.Page(site, cr_template, ns=tpl_ns)
            # retrieve all redirects to primary template from API,
            # add any that are not already on the list
            for t in cr_page.backlinks(filter_redirects=True,
                                       namespaces=tpl_ns):
                newtitle = t.title(with_ns=False)
                if newtitle not in cr_template_tuple:
                    cr_set.add(newtitle)
        self._catredirtemplates[code] = list(cr_template_tuple) + list(cr_set)

    @deprecated('site.category_redirects()', since='20170608')
    def get_cr_templates(self, code, fallback):
        """DEPRECATED: Build list of category redirect templates."""
        self._get_cr_templates(code, fallback)

    def disambig(self, code, fallback='_default'):
        """Return list of disambiguation templates."""
        if code in self.disambiguationTemplates:
            return self.disambiguationTemplates[code]
        elif fallback:
            return self.disambiguationTemplates[fallback]
        else:
            raise KeyError(
                'ERROR: title for disambig template in language %s unknown'
                % code)

    # Methods
    def protocol(self, code):
        """
        The protocol to use to connect to the site.

        May be overridden to return 'https'. Other protocols are not supported.

        @param code: language code
        @type code: str
        @return: protocol that this family uses
        @rtype: str
        """
        return 'http'

    def ignore_certificate_error(self, code):
        """
        Return whether a HTTPS certificate error should be ignored.

        @param code: language code
        @type code: str
        @return: flag to allow access if certificate has an error.
        @rtype: bool
        """
        return False

    def hostname(self, code):
        """The hostname to use for standard http connections."""
        return self.langs[code]

    def ssl_hostname(self, code):
        """The hostname to use for SSL connections."""
        return self.hostname(code)

    def scriptpath(self, code):
        """The prefix used to locate scripts on this wiki.

        This is the value displayed when you enter {{SCRIPTPATH}} on a
        wiki page (often displayed at [[Help:Variables]] if the wiki has
        copied the master help page correctly).

        The default value is the one used on Wikimedia Foundation wikis,
        but needs to be overridden in the family file for any wiki that
        uses a different value.

        @param code: Site code
        @type code: str
        @raises KeyError: code is not recognised
        @return: URL path without ending '/'
        @rtype: str
        """
        return '/w'

    def ssl_pathprefix(self, code):
        """The path prefix for secure HTTP access."""
        # Override this ONLY if the wiki family requires a path prefix
        return ''

    def _hostname(self, code, protocol=None):
        """Return the protocol and hostname."""
        if protocol is None:
            protocol = self.protocol(code)
        if protocol == 'https':
            host = self.ssl_hostname(code)
        else:
            host = self.hostname(code)
        return protocol, host

    def base_url(self, code, uri, protocol=None):
        """
        Prefix uri with port and hostname.

        @param code: The site code
        @type code: str
        @param uri: The absolute path after the hostname
        @type uri: str
        @param protocol: The protocol which is used. If None it'll determine
            the protocol from the code.
        @return: The full URL ending with uri
        @rtype: str
        """
        protocol, host = self._hostname(code, protocol)
        if protocol == 'https':
            uri = self.ssl_pathprefix(code) + uri
        return urlparse.urljoin('{0}://{1}'.format(protocol, host), uri)

    def path(self, code):
        """Return path to index.php."""
        return '%s/index.php' % self.scriptpath(code)

    def querypath(self, code):
        """Return path to query.php."""
        return '%s/query.php' % self.scriptpath(code)

    def apipath(self, code):
        """Return path to api.php."""
        return '%s/api.php' % self.scriptpath(code)

    @deprecated('APISite.article_path', since='20150905')
    def nicepath(self, code):
        """DEPRECATED: Return nice path prefix, e.g. '/wiki/'."""
        return '/wiki/'

    def eventstreams_host(self, code):
        """Hostname for EventStreams."""
        raise NotImplementedError('This family does not support EventStreams')

    def eventstreams_path(self, code):
        """Return path for EventStreams."""
        raise NotImplementedError('This family does not support EventStreams')

    @deprecated_args(name='title')
    def get_address(self, code, title):
        """Return the path to title using index.php with redirects disabled."""
        return '%s?title=%s&redirect=no' % (self.path(code), title)

    @deprecated('APISite.nice_get_address(title)', since='20150628')
    def nice_get_address(self, code, title):
        """DEPRECATED: Return the nice path to title using index.php."""
        return '%s%s' % (self.nicepath(code), title)

    def interface(self, code):
        """
        Return interface to use for code.

        @rtype: str or subclass of BaseSite
        """
        if code in self.interwiki_removals:
            if code in self.codes:
                pywikibot.warn('Interwiki removal %s is in %s codes'
                               % (code, self))
            if code in self.closed_wikis:
                return 'ClosedSite'
            if code in self.removed_wikis:
                return 'RemovedSite'

        return config.site_interface

    def from_url(self, url):
        """
        Return whether this family matches the given url.

        It is first checking if a domain of this family is in the the domain of
        the URL. If that is the case it's checking all codes and verifies that
        a path generated via L{APISite.article_path} and L{Family.path} matches
        the path of the URL together with the hostname for that code.

        It is using L{Family.domains} to first check if a domain applies and
        then iterates over L{Family.codes} to actually determine which code
        applies.

        @param url: the URL which may contain a C{$1}. If it's missing it is
            assumed to be at the end and if it's present nothing is allowed
            after it.
        @type url: str
        @return: The language code of the url. None if that url is not from
            this family.
        @rtype: str or None
        @raises RuntimeError: When there are multiple languages in this family
            which would work with the given URL.
        @raises ValueError: When text is present after $1.
        """
        parsed = urlparse.urlparse(url)
        if not re.match('(https?)?$', parsed.scheme):
            return None

        path = parsed.path
        if parsed.query:
            path += '?' + parsed.query

        # Discard $1 and everything after it
        path, _, suffix = path.partition('$1')
        if suffix:
            raise ValueError('Text after the $1 placeholder is not supported '
                             '(T111513).')

        for domain in self.domains:
            if domain in parsed.netloc:
                break
        else:
            return None

        matched_sites = []
        for code in chain(self.codes,
                          getattr(self, 'test_codes', ()),
                          getattr(self, 'closed_wikis', ()),
                          ):
            if self._hostname(code)[1] == parsed.netloc:
                # Use the code and family instead of the url
                # This is only creating a Site instance if domain matches
                site = pywikibot.Site(code, self.name)
                pywikibot.log('Found candidate {0}'.format(site))

                for iw_url in site._interwiki_urls():
                    if path.startswith(iw_url):
                        matched_sites += [site]
                        break

        if len(matched_sites) == 1:
            return matched_sites[0].code

        if not matched_sites:
            return None

        raise RuntimeError(
            'Found multiple matches for URL "{0}": {1}'
            .format(url, ', '.join(str(s) for s in matched_sites)))

    def maximum_GET_length(self, code):
        """Return the maximum URL length for GET instead of POST."""
        return config.maximum_GET_length

    def dbName(self, code):
        """Return the name of the MySQL database."""
        return '%s%s' % (code, self.name)

    # Which version of MediaWiki is used?
    @deprecated('APISite.version()', since='20141225')
    def version(self, code):
        """Return MediaWiki version number as a string.

        Use L{pywikibot.site.mw_version} to compare version strings.
        """
        # Here we return the latest mw release for downloading
        if not hasattr(self, '_version'):
            self._version = fetch(
                'https://www.mediawiki.org/w/api.php?action=expandtemplates'
                '&text={{MW_stable_release_number}}&prop=wikitext&format=json'
            ).data.json()['expandtemplates']['wikitext']
        return self._version

    def force_version(self, code):
        """
        Return a manual version number.

        The site is usually using the version number from the servers'
        siteinfo, but if there is a problem with that it's possible to return
        a non-empty string here representing another version number.

        For example, L{pywikibot.tools.MediaWikiVersion} treats version
        numbers ending with 'alpha', 'beta' or 'rc' as newer than any version
        ending with 'wmf<number>'. But if that causes breakage it's possible
        to override it here to a version number which doesn't cause breakage.

        @return: A version number which can be parsed using
            L{pywikibot.tools.MediaWikiVersion}. If empty/None it uses the
            version returned via siteinfo.
        @rtype: str
        """
        return None

    def encoding(self, code):
        """Return the encoding for a specific language wiki."""
        return 'utf-8'

    def encodings(self, code):
        """Return list of historical encodings for a specific language wiki."""
        return (self.encoding(code), )

    # aliases
    @deprecated('Site().encoding()', since='20200218')
    def code2encoding(self, code):
        """Return the encoding for a specific language wiki."""
        return self.encoding(code)

    @deprecated('Site().encodings()', since='20200218')
    def code2encodings(self, code):
        """Return list of historical encodings for a specific language wiki."""
        return self.encodings(code)

    def __eq__(self, other):
        """Compare self with other.

        If other is not a Family() object, try to create one.
        """
        if not isinstance(other, Family):
            other = self.load(other)

        return self is other

    def __ne__(self, other):
        try:
            return not self.__eq__(other)
        except UnknownFamily:
            return False

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Family("%s")' % self.name

    def shared_image_repository(self, code):
        """Return the shared image repository, if any."""
        return (None, None)

    # Deprecated via __getattribute__
    @remove_last_args(['transcluded'])
    def shared_data_repository(self, code):
        """Return the shared Wikibase repository, if any."""
        repo = pywikibot.Site(code, self).data_repository()
        if repo is not None:
            return repo.code, repo.family.name
        return (None, None)

    @deprecated('Site.server_time()', since='20141225')
    def server_time(self, code):
        """
        DEPRECATED, use Site.server_time instead.

        Return a datetime object representing server time.
        """
        return pywikibot.Site(code, self).server_time()

    def isPublic(self, code):
        """Check the wiki require logging in before viewing it."""
        return True

    def post_get_convert(self, site, getText):
        """
        Do a conversion on the retrieved text from the Wiki.

        For example a X-conversion in Esperanto
        U{https://en.wikipedia.org/wiki/Esperanto_orthography#X-system}.
        """
        return getText

    def pre_put_convert(self, site, putText):
        """
        Do a conversion on the text to insert on the Wiki.

        For example a X-conversion in Esperanto
        U{https://en.wikipedia.org/wiki/Esperanto_orthography#X-system}.
        """
        return putText

    @property
    def obsolete(self):
        """
        Old codes that are not part of the family.

        Interwiki replacements override removals for the same code.

        @return: mapping of old codes to new codes (or None)
        @rtype: dict
        """
        data = {code: None for code in self.interwiki_removals}
        data.update(self.interwiki_replacements)
        return FrozenDict(data,
                          'Family.obsolete not updatable; '
                          'use Family.interwiki_removals '
                          'and Family.interwiki_replacements')

    @obsolete.setter
    def obsolete(self, data):
        """Split obsolete dict into constituent parts."""
        self.interwiki_removals[:] = [old for (old, new) in data.items()
                                      if new is None]
        self.interwiki_replacements.clear()
        self.interwiki_replacements.update((old, new)
                                           for (old, new) in data.items()
                                           if new is not None)

    @classproperty
    def domains(cls):
        """
        Get list of unique domain names included in this family.

        These domains may also exist in another family.

        @rtype: iterable of str
        """
        return set(cls.langs.values())

    @classproperty
    def codes(cls):
        """
        Get list of codes used by this family.

        @rtype: iterable of str
        """
        return set(cls.langs.keys())


class SingleSiteFamily(Family):

    """Single site family."""

    def __new__(cls):
        """Initializer."""
        if not hasattr(cls, 'code'):
            cls.code = cls.name

        assert cls.domain

        cls.langs = {cls.code: cls.domain}

        return super(SingleSiteFamily, cls).__new__(cls)

    @classproperty
    def domains(cls):
        """Return the full domain name of the site."""
        return (cls.domain, )

    def hostname(self, code):
        """Return the domain as the hostname."""
        return self.domain


class SubdomainFamily(Family):

    """Multi site wikis that are subdomains of the same top level domain."""

    def __new__(cls):
        """Initializer."""
        assert cls.domain
        return super(SubdomainFamily, cls).__new__(cls)

    @classproperty
    def langs(cls):
        """Property listing family languages."""
        codes = cls.codes[:]

        if hasattr(cls, 'test_codes'):
            codes += cls.test_codes
        if hasattr(cls, 'closed_wikis'):
            codes += cls.closed_wikis

        # shortcut this classproperty
        cls.langs = {code: '{0}.{1}'.format(code, cls.domain)
                     for code in codes}

        if hasattr(cls, 'code_aliases'):
            cls.langs.update({alias: '{0}.{1}'.format(code, cls.domain)
                              for alias, code in cls.code_aliases.items()})

        return cls.langs

    @classproperty
    def codes(cls):
        """Property listing family codes."""
        if cls.languages_by_size:
            return cls.languages_by_size
        raise NotImplementedError(
            'Family %s needs property "languages_by_size" or "codes"'
            % cls.name)

    @classproperty
    def domains(cls):
        """Return the domain name of the sites in this family."""
        return [cls.domain]


class FandomFamily(Family):

    """Common features of Fandom families."""

    @deprecated('APISite.version()', since='20141225')
    def version(self, code):
        """Return the version for this family."""
        return '1.19.24'

    @classproperty
    def langs(cls):
        """Property listing family languages."""
        codes = cls.codes

        if hasattr(cls, 'code_aliases'):
            codes += tuple(cls.code_aliases.keys())

        return {code: cls.domain for code in codes}

    def protocol(self, code):
        """Return 'https' as the protocol."""
        return 'https'

    def scriptpath(self, code):
        """Return the script path for this family."""
        return '' if code == 'en' else ('/' + code)


class WikimediaFamily(Family):

    """Class for all wikimedia families."""

    multi_language_content_families = [
        'wikipedia', 'wiktionary',
        'wikisource', 'wikibooks',
        'wikinews', 'wikiquote',
        'wikiversity', 'wikivoyage',
    ]

    wikimedia_org_content_families = [
        'commons', 'incubator', 'species',
    ]

    wikimedia_org_meta_families = [
        'meta', 'outreach', 'strategy',
        'wikimediachapter', 'wikimania',
    ]

    wikimedia_org_other_families = [
        'wikitech',
    ]

    other_content_families = [
        'wikidata',
        'mediawiki',
    ]

    content_families = set(
        multi_language_content_families
        + wikimedia_org_content_families
        + other_content_families
    )

    wikimedia_org_families = set(
        wikimedia_org_content_families
        + wikimedia_org_meta_families
        + wikimedia_org_other_families
    )

    # CentralAuth cross available projects.
    cross_projects = set(
        multi_language_content_families
        + wikimedia_org_content_families
        + wikimedia_org_meta_families
        + other_content_families
    )

    # Code mappings which are only an alias, and there is no 'old' wiki.
    # For all except 'nl_nds', subdomains do exist as a redirect, but that
    # should not be relied upon.
    code_aliases = {
        # Country aliases, see T87002
        'dk': 'da',
        'jp': 'ja',

        # Language aliases, see T86924
        'nb': 'no',

        # Closed wiki redirection aliases
        'mo': 'ro',

        # Incomplete language code change, see T86915
        'minnan': 'zh-min-nan',
        'nan': 'zh-min-nan',

        'zh-tw': 'zh',
        'zh-cn': 'zh',

        # Miss-spelling
        'nl_nds': 'nl-nds',

        # Renamed, see T11823
        'be-x-old': 'be-tarask',
    }

    # Not open for edits; stewards can still edit.
    closed_wikis = []
    # Completely removed
    removed_wikis = []

    # WikimediaFamily uses wikibase for the category name containing
    # disambiguation pages for the various languages. We need the
    # wikibase code and item number:
    disambcatname = {'wikidata': 'Q1982926'}

    # UrlShortener extension is only usable on metawiki, and this wiki can
    # process links to all WM domains.
    shared_urlshortner_wiki = ('meta', 'meta')

    @classproperty
    def domain(cls):
        """Domain property."""
        if cls.name in (cls.multi_language_content_families
                        + cls.other_content_families):
            return cls.name + '.org'
        elif cls.name in cls.wikimedia_org_families:
            return 'wikimedia.org'

        raise NotImplementedError(
            "Family %s needs to define property 'domain'" % cls.name)

    @classproperty
    def interwiki_removals(cls):
        """Return a list of interwiki codes to be removed from wiki pages."""
        return frozenset(cls.removed_wikis + cls.closed_wikis)

    @classproperty
    def interwiki_replacements(cls):
        """Return an interwiki code replacement mapping."""
        rv = cls.code_aliases.copy()
        return FrozenDict(rv)

    def shared_image_repository(self, code):
        """Return Wikimedia Commons as the shared image repository."""
        return ('commons', 'commons')

    def protocol(self, code):
        """Return 'https' as the protocol."""
        return 'https'

    def eventstreams_host(self, code):
        """Return 'https://stream.wikimedia.org' as the stream hostname."""
        return 'https://stream.wikimedia.org'

    def eventstreams_path(self, code):
        """Return path for EventStreams."""
        return '/v2/stream'


class WikimediaOrgFamily(SingleSiteFamily, WikimediaFamily):

    """Single site family for sites hosted at C{*.wikimedia.org}."""

    @classproperty
    def domain(cls):
        """Return the parents domain with a subdomain prefix."""
        return '{0}.wikimedia.org'.format(cls.name)


@deprecated_args(site=None)
def AutoFamily(name, url):
    """
    Family that automatically loads the site configuration.

    @param name: Name for the family
    @type name: str
    @param url: API endpoint URL of the wiki
    @type url: str
    @return: Generated family class
    @rtype: SingleSiteFamily
    """
    url = urlparse.urlparse(url)
    domain = url.netloc

    def protocol(self, code):
        """Return the protocol of the URL."""
        return self.url.scheme

    def scriptpath(self, code):
        """Extract the script path from the URL."""
        if self.url.path.endswith('/api.php'):
            return self.url.path[0:-8]
        else:
            # AutoFamily refers to the variable set below, not the function
            return super(AutoFamily, self).scriptpath(code)

    # str() used because py2 can't accept a unicode as the name of a class
    AutoFamily = type(str('AutoFamily'), (SingleSiteFamily,), locals())
    return AutoFamily()


wrapper = ModuleDeprecationWrapper(__name__)
wrapper._add_deprecated_attr('WikiaFamily', replacement=FandomFamily,
                             since='20190420')
