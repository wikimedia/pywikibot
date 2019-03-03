# -*- coding: utf-8 -*-
"""Date data and manipulation module."""
#
# (C) Rob W.W. Hooft, 2003
# (C) Daniel Herding, 2004
# (C) Ævar Arnfjörð Bjarmason, 2004
# (C) Andre Engels, 2004-2005
# (C) Yuri Astrakhan, 2005-2006 (<Firstname><Lastname>@gmail.com)
#       (years/decades/centuries/millenniums str <=> int conversions)
# (C) Pywikibot team, 2004-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import calendar
import datetime
import re
from string import digits as _decimalDigits  # noqa: N812

from pywikibot.textlib import NON_LATIN_DIGITS
from pywikibot.tools import first_lower, first_upper, deprecated, PY2

if not PY2:
    unicode = str
    basestring = (str,)

#
# Different collections of well known formats
#
enMonthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November',
                'December']
dayMnthFmts = ['Day_' + str(s) for s in enMonthNames]  # e.g. 'Day_January'
yrMnthFmts = ['Year_' + str(s) for s in enMonthNames]  # e.g. 'Year_January'


# the order of these lists is important
adDateFormats = ['YearAD', 'DecadeAD', 'CenturyAD', 'MillenniumAD']
bcDateFormats = ['YearBC', 'DecadeBC', 'CenturyBC', 'MillenniumBC']

dateFormats = bcDateFormats + adDateFormats
decadeFormats = ['DecadeAD', 'DecadeBC']
centuryFormats = ['CenturyAD', 'CenturyBC']
yearFormats = ['YearAD', 'YearBC']
millFormats = ['MillenniumAD', 'MillenniumBC']
snglValsFormats = ['CurrEvents']


def multi(value, tuplst):
    """
    Run multiple pattern checks for the same entry.

    For example: 1st century, 2nd century, etc.

    The tuplst is a list of tuples. Each tuple must contain two functions:
    first to encode/decode a single value (e.g. simpleInt), second is a
    predicate function with an integer parameter that returns true or false.
    When the 2nd function evaluates to true, the 1st function is used.

    """
    if isinstance(value, basestring):
        # Try all functions, and test result against predicates
        for func, pred in tuplst:
            try:
                res = func(value)
                if pred(res):
                    return res
            except Exception:
                pass
    else:
        # Find a predicate that gives true for this int value, and run a
        # function
        for func, pred in tuplst:
            if pred(value):
                return func(value)

    raise ValueError('could not find a matching function')


#
# Helper functions that aid with single value no corrections encoding/decoding.
# Various filters are item dependent.
#
def dh_noConv(value, pattern, limit):
    """Helper for decoding an integer value, no conversion, no rounding."""
    return dh(value, pattern, lambda i: i, decSinglVal, limit)


def dh_dayOfMnth(value, pattern):
    """
    Helper for decoding a single integer value.

    The single integer should be <=31, no conversion,
    no rounding (used in days of month).
    """
    # For now use January because it has all 31 days
    return dh_noConv(value, pattern, formatLimits[dayMnthFmts[0]][0])


def dh_mnthOfYear(value, pattern):
    """
    Helper for decoding a single integer value.

    The value should be >=1000, no conversion,
    no rounding (used in month of the year)
    """
    return dh_noConv(value, pattern, _formatLimit_MonthOfYear[0])


def dh_decAD(value, pattern):
    """
    Helper for decoding a single integer value.

    It should be no conversion, round to decimals (used in decades)
    """
    return dh(value, pattern, encDec0, decSinglVal,
              formatLimits['DecadeAD'][0])


def dh_decBC(value, pattern):
    """
    Helper for decoding a single integer value.

    It should be no conversion, round to decimals (used in decades)
    """
    return dh(value, pattern, encDec0, decSinglVal,
              formatLimits['DecadeBC'][0])


def dh_yearBC(value, pattern):
    """Helper for decoding a year value.

    The value should have no conversion, no rounding, limits to 3000.
    """
    return dh_noConv(value, pattern, formatLimits['YearBC'][0])


def dh_yearAD(value, pattern):
    """Helper for decoding a year value.

    The value should have no conversion, no rounding, limits to 3000.
    """
    return dh_noConv(value, pattern, formatLimits['YearAD'][0])


def dh_simpleYearAD(value):
    """Helper for decoding a single integer value.

    This value should be representing a year with no extra symbols.
    """
    return dh_yearAD(value, '%d')


def dh_number(value, pattern):
    """Helper for decoding a number."""
    return dh_noConv(value, pattern, formatLimits['Number'][0])


def dh_centuryAD(value, pattern):
    """Helper for decoding an AD century."""
    return dh_noConv(value, pattern, formatLimits['CenturyAD'][0])


def dh_centuryBC(value, pattern):
    """Helper for decoding an BC century."""
    return dh_noConv(value, pattern, formatLimits['CenturyBC'][0])


def dh_millenniumAD(value, pattern):
    """Helper for decoding an AD millennium."""
    return dh_noConv(value, pattern, formatLimits['MillenniumAD'][0])


def dh_millenniumBC(value, pattern):
    """Helper for decoding an BC millennium."""
    return dh_noConv(value, pattern, formatLimits['MillenniumBC'][0])


def decSinglVal(v):
    """Return first item in list v."""
    return v[0]


@deprecated(since='20151014')
def encNoConv(i):
    """Return i."""
    return i


def encDec0(i):
    """Round to the nearest decade, decade starts with a '0'-ending year."""
    return (i // 10) * 10


def encDec1(i):
    """Round to the nearest decade, decade starts with a '1'-ending year."""
    return encDec0(i) + 1


def slh(value, lst):
    """Helper function for simple list value matching.

    !!!!! The index starts at 1, so 1st element has index 1, not 0 !!!!!

    Usually it will be used as a lambda call in a map::

        lambda v: slh(v, ['January','February',...])

    Usage scenarios::

        formats['MonthName']['en'](1) => 'January'
        formats['MonthName']['en']('January') => 1
        formats['MonthName']['en']('anything else') => raise ValueError

    """
    if isinstance(value, basestring):
        return lst.index(value) + 1
    else:
        return lst[value - 1]


def dh_singVal(value, match):
    """Helper function to match a single value to a constant."""
    return dh_constVal(value, 0, match)


def dh_constVal(value, ind, match):
    """Helper function to match a single value to a constant.

    formats['CurrEvents']['en'](ind) => 'Current Events'
    formats['CurrEvents']['en']('Current Events') => ind

    """
    if isinstance(value, basestring):
        if value == match:
            return ind
        else:
            raise ValueError()
    else:
        if value == ind:
            return match
        else:
            raise ValueError('unknown value %d' % value)


def alwaysTrue(x):
    """
    Return True, always.

    Used for multiple value selection function to accept all other values.

    @param x: not used
    @return: True
    @rtype: bool
    """
    return True


def monthName(lang, ind):
    """Return the month name for a language."""
    return formats['MonthName'][lang](ind)


# Helper for KN: digits representation
_knDigits = NON_LATIN_DIGITS['kn']
_knDigitsToLocal = {ord(unicode(i)): _knDigits[i] for i in range(10)}
_knLocalToDigits = {ord(_knDigits[i]): unicode(i) for i in range(10)}

# Helper for Urdu/Persian languages
_faDigits = NON_LATIN_DIGITS['fa']
_faDigitsToLocal = {ord(unicode(i)): _faDigits[i] for i in range(10)}
_faLocalToDigits = {ord(_faDigits[i]): unicode(i) for i in range(10)}

# Helper for HI:, MR:
_hiDigits = NON_LATIN_DIGITS['hi']
_hiDigitsToLocal = {ord(unicode(i)): _hiDigits[i] for i in range(10)}
_hiLocalToDigits = {ord(_hiDigits[i]): unicode(i) for i in range(10)}

# Helper for BN:
_bnDigits = NON_LATIN_DIGITS['bn']
_bnDigitsToLocal = {ord(unicode(i)): _bnDigits[i] for i in range(10)}
_bnLocalToDigits = {ord(_bnDigits[i]): unicode(i) for i in range(10)}

# Helper for GU:
_guDigits = NON_LATIN_DIGITS['gu']
_guDigitsToLocal = {ord(unicode(i)): _guDigits[i] for i in range(10)}
_guLocalToDigits = {ord(_guDigits[i]): unicode(i) for i in range(10)}


def intToLocalDigitsStr(value, digitsToLocalDict):
    """Encode an integer value into a textual form."""
    return unicode(value).translate(digitsToLocalDict)


def localDigitsStrToInt(value, digitsToLocalDict, localToDigitsDict):
    """Convert digits to integer."""
    # First make sure there are no real digits in the string
    tmp = value.translate(digitsToLocalDict)         # Test
    if tmp == value:
        return int(value.translate(localToDigitsDict))    # Convert
    else:
        raise ValueError('string contains regular digits')


# Helper for roman numerals number representation
_romanNumbers = ['-', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX',
                 'X', 'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII',
                 'XIX', 'XX', 'XXI', 'XXII', 'XXIII', 'XXIV', 'XXV', 'XXVI',
                 'XXVII', 'XXVIII', 'XXIX', 'XXX']


def intToRomanNum(i):
    """Convert integer to roman numeral."""
    if i >= len(_romanNumbers):
        raise IndexError('Roman value %i is not defined' % i)
    return _romanNumbers[i]


def romanNumToInt(v):
    """Convert roman numeral to integer."""
    return _romanNumbers.index(v)


# Each tuple must 3 parts: a list of all possible digits (symbols), encoder
# (from int to a u-string) and decoder (from u-string to an int)
_digitDecoders = {
    # %% is a %
    '%': '%',
    # %d is a decimal
    'd': (_decimalDigits, unicode, int),
    # %R is a roman numeral. This allows for only the simplest linear
    # conversions based on a list of numbers
    'R': ('IVX', intToRomanNum, romanNumToInt),
    # %K is a number in KN::
    'K': (_knDigits, lambda v: intToLocalDigitsStr(v, _knDigitsToLocal),
          lambda v: localDigitsStrToInt(v, _knDigitsToLocal,
                                        _knLocalToDigits)),
    # %F is a number in FA:
    'F': (_faDigits, lambda v: intToLocalDigitsStr(v, _faDigitsToLocal),
          lambda v: localDigitsStrToInt(v, _faDigitsToLocal,
                                        _faLocalToDigits)),
    # %H is a number in HI:
    'H': (_hiDigits, lambda v: intToLocalDigitsStr(v, _hiDigitsToLocal),
          lambda v: localDigitsStrToInt(v, _hiDigitsToLocal,
                                        _hiLocalToDigits)),
    # %B is a number in BN:
    'B': (_bnDigits, lambda v: intToLocalDigitsStr(v, _bnDigitsToLocal),
          lambda v: localDigitsStrToInt(v, _bnDigitsToLocal,
                                        _bnLocalToDigits)),
    # %G is a number in GU:
    'G': (_guDigits, lambda v: intToLocalDigitsStr(v, _guDigitsToLocal),
          lambda v: localDigitsStrToInt(v, _guDigitsToLocal,
                                        _guLocalToDigits)),
    # %T is a year in TH: -- all years are shifted: 2005 => 'พ.ศ. 2548'
    'T': (_decimalDigits, lambda v: unicode(v + 543), lambda v: int(v) - 543),
}

# Allows to search for '(%%)|(%d)|(%R)|...", and allows one digit 1-9 to set
# the size of zero-padding for numbers
_reParameters = re.compile('|'.join('(%%[1-9]?%s)' % s
                                    for s in _digitDecoders))

# A map of sitecode+pattern to (re matching object and corresponding decoders)
_escPtrnCache2 = {}

_listTypes = [list, tuple]


def escapePattern2(pattern):
    """
    Convert a string pattern into a regex expression and cache.

    Allows matching of any _digitDecoders inside the string.
    Returns a compiled regex object and a list of digit decoders.
    """
    if pattern not in _escPtrnCache2:
        newPattern = '^'  # beginning of the string
        strPattern = ''
        decoders = []
        for s in _reParameters.split(pattern):
            if s is None:
                continue
            if (len(s) in (2, 3) and s[0] == '%'
                    and s[-1] in _digitDecoders
                    and(len(s) == 2 or s[1] in _decimalDigits)):
                # Must match a "%2d" or "%d" style
                dec = _digitDecoders[s[-1]]
                if isinstance(dec, basestring):
                    # Special case for strings that are replaced instead of
                    # decoded
                    assert len(s) < 3, (
                        'Invalid pattern {0}: Cannot use zero padding size '
                        'in {1}!'.format(pattern, s))
                    newPattern += re.escape(dec)
                    strPattern += s  # Keep the original text
                else:
                    if len(s) == 3:
                        # enforce mandatory field size
                        newPattern += '([%s]{%s})' % (dec[0], s[1])
                        # add the number of required digits as the last (4th)
                        # part of the tuple
                        dec += (int(s[1]),)
                    else:
                        newPattern += '([{}]+)'.format(dec[0])

                    decoders.append(dec)
                    # All encoders produce a string
                    # this causes problem with the zero padding.
                    # Need to rethink
                    strPattern += '%s'
            else:
                newPattern += re.escape(s)
                strPattern += s

        newPattern += '$'  # end of the string
        compiledPattern = re.compile(newPattern)
        _escPtrnCache2[pattern] = (compiledPattern, strPattern, decoders)

    return _escPtrnCache2[pattern]


def dh(value, pattern, encf, decf, filter=None):
    """Function to help with year parsing.

    Usually it will be used as a lambda call in a map::

        lambda v: dh(v, 'pattern string', encf, decf)

    @param encf:
        Converts from an integer parameter to another integer or a tuple of
        integers. Depending on the pattern, each integer will be converted to a
        proper string representation, and will be passed as a format argument
        to the pattern::

                    pattern % encf(value)

        This function is a complement of decf.

    @param decf:
        Converts a tuple/list of non-negative integers found in the original
        value string
        into a normalized value. The normalized value can be passed right back
        into dh() to produce the original string. This function is a complement
        of encf. dh() interprets %d as a decimal and %s as a roman
        numeral number.

    """
    compPattern, strPattern, decoders = escapePattern2(pattern)
    if isinstance(value, basestring):
        m = compPattern.match(value)
        if m:
            # decode each found value using provided decoder
            values = [decoder[2](m.group(i + 1))
                      for i, decoder in enumerate(decoders)]
            decValue = decf(values)

            assert not isinstance(decValue, basestring), \
                'Decoder must not return a string!'

            # recursive call to re-encode and see if we get the original
            # (may through filter exception)
            if value == dh(decValue, pattern, encf, decf, filter):
                return decValue

        raise ValueError("reverse encoding didn't match")
    else:
        # Encode an integer value into a textual form.
        # This will be called from outside as well as recursivelly to verify
        # parsed value
        if filter and not filter(value):
            raise ValueError('value {} is not allowed'.format(value))

        params = encf(value)

        # name 'MakeParameter' kept to avoid breaking blame below
        MakeParameter = _make_parameter

        if type(params) in _listTypes:
            assert len(params) == len(decoders), (
                'parameter count ({0}) does not match decoder count ({1})'
                .format(len(params), len(decoders)))
            # convert integer parameters into their textual representation
            params = [MakeParameter(decoders[i], param)
                      for i, param in enumerate(params)]
            return strPattern % tuple(params)
        else:
            assert len(decoders) == 1, (
                'A single parameter does not match {0} decoders.'
                .format(len(decoders)))
            # convert integer parameter into its textual representation
            return strPattern % MakeParameter(decoders[0], params)


def _make_parameter(decoder, param):
    newValue = decoder[1](param)
    if len(decoder) == 4 and len(newValue) < decoder[3]:
        # force parameter length by taking the first digit in the list and
        # repeating it required number of times
        # This converts "205" into "0205" for "%4d"
        newValue = decoder[0][0] * (decoder[3] - len(newValue)) + newValue
    return newValue


@deprecated(since='20151014')
def MakeParameter(decoder, param):
    """DEPRECATED."""
    return _make_parameter(decoder, param)


# All years/decades/centuries/millenniums are designed in such a way
# as to allow for easy date to string and string to date conversion.
# For example, using any map with either an integer or a string will produce
# its opposite value:
#        Usage scenarios:
#            formats['DecadeAD']['en'](1980) => '1980s'
#            formats['DecadeAD']['en']('1980s') => 1980
#            formats['DecadeAD']['en']('anything else') => raise ValueError
#                                                    (or some other exception?)
# This is useful when trying to decide if a certain article is a localized date
# or not, or generating dates.
# See dh() for additional information.
formats = {
    'MonthName': {
        'af': lambda v: slh(v, ['Januarie', 'Februarie', 'Maart', 'April',
                                'Mei', 'Junie', 'Julie', 'Augustus',
                                'September', 'Oktober', 'November',
                                'Desember']),
        'gsw': lambda v: slh(v, ['Januar', 'Februar', 'März', 'April', 'Mai',
                                 'Juni', 'Juli', 'August', 'September',
                                 'Oktober', 'November', 'Dezember']),
        'an': lambda v: slh(v, ['chinero', 'frebero', 'marzo', 'abril',
                                'mayo', 'chunio', 'chulio', 'agosto',
                                'setiembre', 'otubre', 'nobiembre',
                                'abiento']),
        'ang': lambda v: slh(v, ['Æfterra Gēola', 'Solmōnaþ', 'Hrēþmōnaþ',
                                 'Ēastermōnaþ', 'Þrimilcemōnaþ', 'Sēremōnaþ',
                                 'Mǣdmōnaþ', 'Wēodmōnaþ', 'Hāligmōnaþ',
                                 'Winterfylleþ', 'Blōtmōnaþ', 'Gēolmōnaþ']),
        'ar': lambda v: slh(v, ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو',
                                'يونيو', 'يوليو', 'أغسطس', 'سبتمبر',
                                'أكتوبر', 'نوفمبر', 'ديسمبر']),
        'ast': lambda v: slh(v, ['xineru', 'febreru', 'marzu', 'abril',
                                 'mayu', 'xunu', 'xunetu', 'agostu',
                                 'setiembre', 'ochobre', 'payares',
                                 'avientu']),
        'be': lambda v: slh(v, ['студзень', 'люты', 'сакавік', 'красавік',
                                'травень', 'чэрвень', 'ліпень', 'жнівень',
                                'верасень', 'кастрычнік', 'лістапад',
                                'сьнежань']),
        'bg': lambda v: slh(v, ['януари', 'февруари', 'март', 'април',
                                'май', 'юни', 'юли', 'август', 'септември',
                                'октомври', 'ноември', 'декември']),
        'bn': lambda v: slh(v, ['জানুয়ারি', 'ফেব্রুয়ারি', 'মার্চ', 'এপ্রিল',
                                'মে', 'জুন', 'জুলাই', 'আগস্ট', 'সেপ্টেম্বর',
                                'অক্টোবর', 'নভেম্বর', 'ডিসেম্বর']),
        'br': lambda v: slh(v, ['Genver', "C'hwevrer", 'Meurzh', 'Ebrel',
                                'Mae', 'Mezheven', 'Gouere', 'Eost',
                                'Gwengolo', 'Here', 'Du', 'Kerzu']),
        'bs': lambda v: slh(v, ['januar', 'februar', 'mart', 'april',
                                'maj', 'juni', 'juli', 'august', 'septembar',
                                'oktobar', 'novembar', 'decembar']),
        'ca': lambda v: slh(v, ['gener', 'febrer', 'març', 'abril', 'maig',
                                'juny', 'juliol', 'agost', 'setembre',
                                'octubre', 'novembre', 'desembre']),
        'ceb': lambda v: slh(v, ['Enero', 'Pebrero', 'Marso', 'Abril',
                                 'Mayo', 'Hunyo', 'Hulyo', 'Agosto',
                                 'Septiyembre', 'Oktubre', 'Nobiyembre',
                                 'Disyembre']),
        'co': lambda v: slh(v, ['ghjennaghju', 'frivaghju', 'marzu',
                                'aprile', 'maghju', 'ghjugnu', 'lugliu',
                                'aostu', 'settembre', 'uttrovi', 'nuvembri',
                                'decembre']),
        'cs': lambda v: slh(v, ['leden', 'únor', 'březen', 'duben',
                                'květen', 'červen', 'červenec', 'srpen',
                                'září', 'říjen', 'listopad', 'prosinec']),
        'csb': lambda v: slh(v, ['stëcznik', 'gromicznik', 'strumiannik',
                                 'łżëkwiôt', 'môj', 'czerwińc', 'lëpinc',
                                 'zélnik', 'séwnik', 'rujan', 'lëstopadnik',
                                 'gòdnik']),
        'cv': lambda v: slh(v, ['кăрлач', 'нарăс', 'Пуш', 'Ака', 'çу',
                                'çĕртме', 'утă', 'çурла', 'авăн', 'юпа', 'чӳк',
                                'раштав']),
        'cy': lambda v: slh(v, ['Ionawr', 'Chwefror', 'Mawrth', 'Ebrill',
                                'Mai', 'Mehefin', 'Gorffennaf', 'Awst', 'Medi',
                                'Hydref', 'Tachwedd', 'Rhagfyr']),
        'da': lambda v: slh(v, ['januar', 'februar', 'marts', 'april', 'maj',
                                'juni', 'juli', 'august', 'september',
                                'oktober', 'november', 'december']),
        'de': lambda v: slh(v, ['Januar', 'Februar', 'März', 'April',
                                'Mai', 'Juni', 'Juli', 'August',
                                'September', 'Oktober', 'November',
                                'Dezember']),
        'el': lambda v: slh(v, ['Ιανουάριος', 'Φεβρουάριος', 'Μάρτιος',
                                'Απρίλιος', 'Μάιος', 'Ιούνιος', 'Ιούλιος',
                                'Αύγουστος', 'Σεπτέμβριος', 'Οκτώβριος',
                                'Νοέμβριος', 'Δεκέμβριος']),
        'en': lambda v: slh(v, enMonthNames),
        'eo': lambda v: slh(v, ['Januaro', 'Februaro', 'Marto', 'Aprilo',
                                'Majo', 'Junio', 'Julio', 'Aŭgusto',
                                'Septembro', 'Oktobro', 'Novembro',
                                'Decembro']),
        'es': lambda v: slh(v, ['enero', 'febrero', 'marzo', 'abril', 'mayo',
                                'junio', 'julio', 'agosto', 'septiembre',
                                'octubre', 'noviembre', 'diciembre']),
        'et': lambda v: slh(v, ['jaanuar', 'veebruar', 'märts', 'aprill',
                                'mai', 'juuni', 'juuli', 'august', 'september',
                                'oktoober', 'november', 'detsember']),
        'eu': lambda v: slh(v, ['urtarrila', 'otsaila', 'martxoa', 'apirila',
                                'maiatza', 'ekaina', 'uztaila', 'abuztua',
                                'iraila', 'urria', 'azaroa', 'abendua']),
        'fa': lambda v: slh(v, ['ژانویه', 'فوریه', 'مارس', 'آوریل', 'مه',
                                'ژوئن', 'ژوئیه', 'اوت', 'سپتامبر', 'اکتبر',
                                'نوامبر', 'دسامبر']),
        'fi': lambda v: slh(v, ['tammikuu', 'helmikuu', 'maaliskuu',
                                'huhtikuu', 'toukokuu', 'kesäkuu',
                                'heinäkuu', 'elokuu', 'syyskuu', 'lokakuu',
                                'marraskuu', 'joulukuu']),
        'fo': lambda v: slh(v, ['januar', 'februar', 'mars', 'apríl', 'mai',
                                'juni', 'juli', 'august', 'september',
                                'oktober', 'november', 'desember']),
        'fr': lambda v: slh(v, ['janvier', 'février', 'mars (mois)',
                                'avril', 'mai', 'juin', 'juillet', 'août',
                                'septembre', 'octobre', 'novembre',
                                'décembre']),
        'fur': lambda v: slh(v, ['Zenâr', 'Fevrâr', 'Març', 'Avrîl', 'Mai',
                                 'Jugn', 'Lui', 'Avost', 'Setembar', 'Otubar',
                                 'Novembar', 'Dicembar']),
        'fy': lambda v: slh(v, ['jannewaris', 'febrewaris', 'maart', 'april',
                                'maaie', 'juny', 'july', 'augustus',
                                'septimber', 'oktober', 'novimber',
                                'desimber']),
        'ga': lambda v: slh(v, ['Eanáir', 'Feabhra', 'Márta', 'Aibreán',
                                'Bealtaine', 'Meitheamh', 'Iúil', 'Lúnasa',
                                'Meán Fómhair', 'Deireadh Fómhair', 'Samhain',
                                'Nollaig']),
        'gl': lambda v: slh(v, ['xaneiro', 'febreiro', 'marzo', 'abril',
                                'maio', 'xuño', 'xullo', 'agosto', 'setembro',
                                'outubro', 'novembro', 'decembro']),
        'he': lambda v: slh(v, ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי',
                                'יוני', 'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר',
                                'נובמבר', 'דצמבר']),
        'hi': lambda v: slh(v, ['जनवरी', 'फ़रवरी', 'मार्च', 'अप्रैल', 'मई',
                                'जून', 'जुलाई', 'अगस्त', 'सितम्बर', 'अक्टूबर',
                                'नवम्बर', 'दिसम्बर']),
        'hr': lambda v: slh(v, ['siječanj', 'veljača', 'ožujak', 'travanj',
                                'svibanj', 'lipanj', 'srpanj', 'kolovoz',
                                'rujan', 'listopad', 'studeni', 'prosinac']),
        'hu': lambda v: slh(v, ['január', 'február', 'március', 'április',
                                'május', 'június', 'július', 'augusztus',
                                'szeptember', 'október', 'november',
                                'december']),
        'ia': lambda v: slh(v, ['januario', 'februario', 'martio', 'april',
                                'maio', 'junio', 'julio', 'augusto',
                                'septembre', 'octobre', 'novembre',
                                'decembre']),
        'id': lambda v: slh(v, ['Januari', 'Februari', 'Maret', 'April',
                                'Mei', 'Juni', 'Juli', 'Agustus', 'September',
                                'Oktober', 'November', 'Desember']),
        'ie': lambda v: slh(v, ['januar', 'februar', 'marte', 'april',
                                'may', 'junio', 'juli', 'august', 'septembre',
                                'octobre', 'novembre', 'decembre']),
        'io': lambda v: slh(v, ['januaro', 'februaro', 'Marto', 'aprilo',
                                'mayo', 'junio', 'julio', 'agosto',
                                'septembro', 'oktobro', 'novembro',
                                'decembro']),
        'is': lambda v: slh(v, ['janúar', 'febrúar', 'mars (mánuður)',
                                'apríl', 'maí', 'júní', 'júlí', 'ágúst',
                                'september', 'október', 'nóvember',
                                'desember']),
        'it': lambda v: slh(v, ['gennaio', 'febbraio', 'marzo', 'aprile',
                                'maggio', 'giugno', 'luglio', 'agosto',
                                'settembre', 'ottobre', 'novembre',
                                'dicembre']),
        'ja': lambda v: slh(v, makeMonthList('%d月')),
        'jv': lambda v: slh(v, ['Januari', 'Februari', 'Maret', 'April', 'Mei',
                                'Juni', 'Juli', 'Agustus', 'September',
                                'Oktober', 'November', 'Desember']),
        'ka': lambda v: slh(v, ['იანვარი', 'თებერვალი', 'მარტი', 'აპრილი',
                                'მაისი', 'ივნისი', 'ივლისი', 'აგვისტო',
                                'სექტემბერი', 'ოქტომბერი', 'ნოემბერი',
                                'დეკემბერი']),
        'kn': lambda v: slh(v, ['ಜನವರಿ', 'ಫೆಬ್ರವರಿ', 'ಮಾರ್ಚಿ', 'ಎಪ್ರಿಲ್',
                                'ಮೇ', 'ಜೂನ', 'ಜುಲೈ', 'ಆಗಸ್ಟ್', 'ಸೆಪ್ಟೆಂಬರ್',
                                'ಅಕ್ಟೋಬರ್', 'ನವೆಂಬರ್', 'ಡಿಸೆಂಬರ್']),
        'ko': lambda v: slh(v, makeMonthList('%d월')),
        'ksh': lambda v: slh(v, ['Jannowaa', 'Febrowaa', 'Mä', 'Apprill',
                                 'Meij', 'Juuni', 'Juuli', 'Aujuß',
                                 'Sepptäber', 'Oktoober', 'Novemmber',
                                 'Dezemmber']),
        'ku': lambda v: slh(v, ['rêbendan', 'reşemî', 'adar', 'avrêl', 'gulan',
                                'pûşper', 'tîrmeh', 'gelawêj (meh)', 'rezber',
                                'kewçêr', 'sermawez', 'berfanbar']),
        'kw': lambda v: slh(v, ['Mys Genver', 'Mys Whevrer', 'Mys Merth',
                                'Mys Ebrel', 'Mys Me', 'Mys Metheven',
                                'Mys Gortheren', 'Mys Est', 'Mys Gwyngala',
                                'Mys Hedra', 'Mys Du', 'Mys Kevardhu']),
        'la': lambda v: slh(v, ['Ianuarius', 'Februarius', 'Martius',
                                'Aprilis', 'Maius', 'Iunius', 'Iulius',
                                'Augustus (mensis)', 'September', 'October',
                                'November', 'December']),
        'lb': lambda v: slh(v, ['Januar', 'Februar', 'Mäerz', 'Abrëll', 'Mee',
                                'Juni', 'Juli', 'August', 'September',
                                'Oktober', 'November', 'Dezember']),
        'li': lambda v: slh(v, ['jannewarie', 'fibberwarie', 'miert', 'april',
                                'mei', 'juni', 'juli', 'augustus (maond)',
                                'september', 'oktober', 'november',
                                'december']),
        'lt': lambda v: slh(v, ['Sausis', 'Vasaris', 'Kovas', 'Balandis',
                                'Gegužė', 'Birželis', 'Liepa', 'Rugpjūtis',
                                'Rugsėjis', 'Spalis', 'Lapkritis', 'Gruodis']),
        'lv': lambda v: slh(v, ['Janvāris', 'Februāris', 'Marts', 'Aprīlis',
                                'Maijs', 'Jūnijs', 'Jūlijs', 'Augusts',
                                'Septembris', 'Oktobris', 'Novembris',
                                'Decembris']),
        'mhr': lambda v: slh(v, ['шорыкйол', 'пургыж', 'ӱярня', 'вӱдшор',
                                 'ага', 'пеледыш', 'сӱрем', 'сорла', 'идым',
                                 'шыжа', 'кылме', 'декабрь']),
        'mi': lambda v: slh(v, ['Kohi-tātea', 'Hui-tanguru', 'Poutū-te-rangi',
                                'Paenga-whāwhā', 'Haratua', 'Pipiri',
                                'Hōngongoi', 'Here-turi-kōkā', 'Mahuru',
                                'Whiringa-ā-nuku', 'Whiringa-ā-rangi',
                                'Hakihea']),
        'ml': lambda v: slh(v, ['ജനുവരി', 'ഫെബ്രുവരി', 'മാര്ച്', 'ഏപ്രില്',
                                'മേയ്', 'ജൂണ്‍', 'ജൂലൈ', 'ആഗസ്റ്റ്‌',
                                'സപ്തന്പര്', 'ഒക്ടോബര്', 'നവന്പര്',
                                'ഡിസന്പര്']),
        'mr': lambda v: slh(v, ['जानेवारी', 'फेब्रुवारी', 'मार्च', 'एप्रिल',
                                'मे', 'जून', 'जुलै', 'ऑगस्ट', 'सप्टेंबर',
                                'ऑक्टोबर', 'नोव्हेंबर', 'डिसेंबर']),
        'ms': lambda v: slh(v, ['Januari', 'Februari', 'Mac', 'April', 'Mei',
                                'Jun', 'Julai', 'Ogos', 'September', 'Oktober',
                                'November', 'Disember']),
        'nap': lambda v: slh(v, ['Jennaro', 'Frevaro', 'Màrzo', 'Abbrile',
                                 'Maggio', 'Giùgno', 'Luglio', 'Aùsto',
                                 'Settembre', 'Ottovre', 'Nuvembre',
                                 'Dicembre']),
        'nds': lambda v: slh(v, ['Januar', 'Februar', 'März', 'April', 'Mai',
                                 'Juni', 'Juli', 'August', 'September',
                                 'Oktober', 'November', 'Dezember']),
        'nl': lambda v: slh(v, ['januari', 'februari', 'maart', 'april', 'mei',
                                'juni', 'juli', 'augustus (maand)',
                                'september', 'oktober', 'november',
                                'december']),
        'nn': lambda v: slh(v, ['januar', 'februar', 'månaden mars', 'april',
                                'mai', 'juni', 'juli', 'august', 'september',
                                'oktober', 'november', 'desember']),
        'nb': lambda v: slh(v, ['januar', 'februar', 'mars', 'april', 'mai',
                                'juni', 'juli', 'august', 'september',
                                'oktober', 'november', 'desember']),
        'oc': lambda v: slh(v, ['genièr', 'febrièr', 'març', 'abril',
                                'mai', 'junh', 'julhet', 'agost', 'setembre',
                                'octobre', 'novembre', 'decembre']),
        'os': lambda v: slh(v, ['январь', 'февраль', 'мартъи', 'апрель', 'май',
                                'июнь', 'июль', 'август', 'сентябрь',
                                'октябрь', 'ноябрь', 'декабрь']),
        'pdc': lambda v: slh(v, ['Yenner', 'Hanning', 'Matz', 'Abril', 'Moi',
                                 'Yuni', 'Yuli', 'Aagscht', 'September',
                                 'Oktower', 'Nowember', 'Disember']),
        'pl': lambda v: slh(v, ['styczeń', 'luty', 'marzec', 'kwiecień', 'maj',
                                'czerwiec', 'lipiec', 'sierpień', 'wrzesień',
                                'październik', 'listopad', 'grudzień']),
        'pt': lambda v: slh(v, ['Janeiro', 'Fevereiro', 'Março', 'Abril',
                                'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro',
                                'Outubro', 'Novembro', 'Dezembro']),
        'ro': lambda v: slh(v, ['ianuarie', 'februarie', 'martie', 'aprilie',
                                'mai', 'iunie', 'iulie', 'august',
                                'septembrie', 'octombrie', 'noiembrie',
                                'decembrie']),
        'ru': lambda v: slh(v, ['январь', 'февраль', 'март', 'апрель', 'май',
                                'июнь', 'июль', 'август', 'сентябрь',
                                'октябрь', 'ноябрь', 'декабрь']),
        'sc': lambda v: slh(v, ['Ghennarzu', 'Frearzu', 'Martzu',
                                'Abrile', 'Maju', 'Làmpadas', 'Triulas',
                                'Aùstu', 'Cabudanni', 'Santugaìne',
                                'Santadria', 'Nadale']),
        'scn': lambda v: slh(v, ['jinnaru', 'frivaru', 'marzu', 'aprili',
                                 'maiu', 'giugnu', 'giugnettu', 'austu',
                                 'sittèmmiru', 'uttùviru', 'nuvèmmiru',
                                 'dicèmmiru']),
        'sco': lambda v: slh(v, ['Januar', 'Februar', 'Mairch', 'Aprile',
                                 'Mey', 'Juin', 'Julie', 'August', 'September',
                                 'October', 'November', 'December']),
        'se': lambda v: slh(v, ['ođđajagimánnu', 'guovvamánnu', 'njukčamánnu',
                                'cuoŋománnu', 'miessemánnu', 'geassemánnu',
                                'suoidnemánnu', 'borgemánnu', 'čakčamánnu',
                                'golggotmánnu', 'skábmamánnu', 'juovlamánnu']),
        'sk': lambda v: slh(v, ['január', 'február', 'marec', 'apríl',
                                'máj', 'jún', 'júl', 'august', 'september',
                                'október', 'november', 'december']),
        'sl': lambda v: slh(v, ['januar', 'februar', 'marec', 'april', 'maj',
                                'junij', 'julij', 'avgust', 'september',
                                'oktober', 'november', 'december']),
        'sq': lambda v: slh(v, ['Janari', 'Shkurti', 'Marsi (muaj)', 'Prilli',
                                'Maji', 'Qershori', 'Korriku', 'Gushti',
                                'Shtatori', 'Tetori', 'Nëntori', 'Dhjetori']),
        'sr': lambda v: slh(v, ['јануар', 'фебруар', 'март', 'април', 'мај',
                                'јун', 'јул', 'август', 'септембар', 'октобар',
                                'новембар', 'децембар']),
        'su': lambda v: slh(v, ['Januari', 'Pébruari', 'Maret', 'April', 'Méi',
                                'Juni', 'Juli', 'Agustus', 'Séptémber',
                                'Oktober', 'Nopémber', 'Désémber']),
        'sv': lambda v: slh(v, ['januari', 'februari', 'mars', 'april', 'maj',
                                'juni', 'juli', 'augusti', 'september',
                                'oktober', 'november', 'december']),
        'ta': lambda v: slh(v, ['ஜனவரி', 'பிப்ரவரி', 'மார்ச்', 'ஏப்ரல்', 'மே',
                                'ஜூன்', 'ஜூலை', 'ஆகஸ்டு', 'செப்டம்பர்',
                                'அக்டோபர்', 'நவம்பர்', 'டிசம்பர்']),
        'te': lambda v: slh(v, ['జనవరి', 'ఫిబ్రవరి', 'మార్చి', 'ఏప్రిల్',
                                'మే', 'జూన్', 'జూలై', 'ఆగష్టు', 'సెప్టెంబర్',
                                'అక్టోబర్', 'నవంబర్', 'డిసెంబర్']),
        'th': lambda v: slh(v, ['มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน',
                                'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม',
                                'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม']),
        'tl': lambda v: slh(v, ['Enero', 'Pebrero', 'Marso', 'Abril', 'Mayo',
                                'Hunyo', 'Hulyo', 'Agosto', 'Setyembre',
                                'Oktubre', 'Nobyembre', 'Disyembre']),
        'tpi': lambda v: slh(v, ['Janueri', 'Februeri', 'Mas', 'Epril', 'Me',
                                 'Jun', 'Julai', 'Ogas', 'Septemba', 'Oktoba',
                                 'Novemba', 'Disemba']),
        'tr': lambda v: slh(v, ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs',
                                'Haziran', 'Temmuz', 'Ağustos', 'Eylül',
                                'Ekim', 'Kasım', 'Aralık']),
        'tt': lambda v: slh(v, ['Ğínwar', 'Febräl', 'Mart', 'Äpril', 'May',
                                'Yün', 'Yül', 'August', 'Sentäber', 'Öktäber',
                                'Nöyäber', 'Dekäber']),
        'uk': lambda v: slh(v, ['січень', 'лютий', 'березень', 'квітень',
                                'травень', 'червень', 'липень', 'серпень',
                                'вересень', 'жовтень', 'листопад', 'грудень']),
        'ur': lambda v: slh(v, ['جنوری', 'فروری', 'مارچ',
                                'اپريل', 'مئی', 'جون', 'جولائی', 'اگست',
                                'ستمبر', 'اکتوبر', 'نومبر', 'دسمبر']),
        'vec': lambda v: slh(v, ['genaro', 'febraro', 'marzso', 'apriłe',
                                 'majo', 'giugno', 'lujo', 'agosto',
                                 'setenbre', 'otobre', 'novenbre',
                                 'diçenbre']),
        'vi': lambda v: slh(v, ['tháng một', 'tháng hai', 'tháng ba',
                                'tháng tư', 'tháng năm', 'tháng sáu',
                                'tháng bảy', 'tháng tám', 'tháng chín',
                                'tháng mười', 'tháng mười một', 'tháng 12']),
        'vo': lambda v: slh(v, ['Yanul', 'Febul', 'Mäzul', 'Prilul', 'Mayul',
                                'Yunul', 'Yulul', 'Gustul', 'Setul', 'Tobul',
                                'Novul', 'Dekul']),
        'wa': lambda v: slh(v, ['djanvî', 'fevrî', 'Måss (moes)', 'avri',
                                'may', 'djun', 'djulete', 'awousse', 'setimbe',
                                'octôbe', 'nôvimbe', 'decimbe']),
        'zh': lambda v: slh(v, makeMonthList('%d月')),
        'nan': lambda v: slh(v, ['It-goe̍h', 'Jī-goe̍h', 'Saⁿ-goe̍h',
                                 'Sì-goe̍h', 'Gō·-goe̍h', 'La̍k-goe̍h',
                                 'Chhit-goe̍h', 'Peh-goe̍h', 'Káu-goe̍h',
                                 'Cha̍p-goe̍h', 'Cha̍p-it-goe̍h',
                                 'Cha̍p-jī-goe̍h']),
    },

    'Number': {
        'ar': lambda v: dh_number(v, '%d (عدد)'),
        'be': lambda v: dh_number(v, '%d (лік)'),
        'bg': lambda v: dh_number(v, '%d (число)'),
        'bs': lambda v: dh_number(v, '%d (broj)'),
        'cs': lambda v: dh_number(v, '%d (číslo)'),
        'da': lambda v: dh_number(v, '%d (tal)'),
        'en': lambda v: dh_number(v, '%d (number)'),
        'fa': lambda v: dh_number(v, '%d (عدد)'),
        'fi': lambda v: dh_number(v, '%d (luku)'),
        'fr': lambda v: dh_number(v, '%d (nombre)'),
        'he': lambda v: dh_number(v, '%d (מספר)'),
        'hu': lambda v: dh_number(v, '%d (szám)'),
        'ia': lambda v: dh_number(v, '%d (numero)'),
        'ja': lambda v: dh_number(v, '%d'),
        'ko': lambda v: dh_number(v, '%d'),
        'ksh': lambda v: dh_number(v, '%d (Zahl)'),
        'la': lambda v: dh_number(v, '%d'),
        'lt': lambda v: dh_number(v, '%d (skaičius)'),
        'nds': lambda v: dh_number(v, '%d (Tall)'),
        'nl': lambda v: dh_number(v, '%d (getal)'),
        'nn': lambda v: dh_number(v, 'Talet %d'),
        'nb': lambda v: dh_number(v, '%d (tall)'),
        'nso': lambda v: dh_number(v, '%d (nomoro)'),
        'pl': lambda v: dh_number(v, '%d (liczba)'),
        'ro': lambda v: dh_number(v, '%d (cifră)'),
        'ru': lambda v: dh_number(v, '%d (число)'),
        'sk': lambda v: dh_number(v, '%d (číslo)'),
        'sl': lambda v: dh_number(v, '%d (število)'),
        'sr': lambda v: dh_number(v, '%d (број)'),
        'sv': lambda v: dh_number(v, '%d (tal)'),
        'th': lambda v: dh_number(v, '%d'),  # was %d (จำนวน)
        'tl': lambda v: dh_number(v, '%d (bilang)'),
        'tr': lambda v: dh_number(v, '%d (sayı)'),
        'zh': lambda v: dh_number(v, '%d'),
    },

    'YearAD': {
        'af': dh_simpleYearAD,
        'gsw': dh_simpleYearAD,
        'an': dh_simpleYearAD,
        'ang': dh_simpleYearAD,
        'ar': dh_simpleYearAD,
        'ast': dh_simpleYearAD,
        'az': dh_simpleYearAD,
        'be': dh_simpleYearAD,
        'bg': dh_simpleYearAD,
        'bn': lambda v: dh_yearAD(v, '%B'),
        'br': dh_simpleYearAD,
        'bs': dh_simpleYearAD,
        'ca': dh_simpleYearAD,
        'ceb': dh_simpleYearAD,
        'cs': dh_simpleYearAD,
        'csb': dh_simpleYearAD,
        'cv': dh_simpleYearAD,
        'cy': dh_simpleYearAD,
        'da': dh_simpleYearAD,
        'de': dh_simpleYearAD,
        'el': dh_simpleYearAD,
        'en': dh_simpleYearAD,
        'eo': dh_simpleYearAD,
        'es': dh_simpleYearAD,
        'et': dh_simpleYearAD,
        'eu': dh_simpleYearAD,
        'fa': lambda v: dh_yearAD(v, '%F (میلادی)'),
        'fi': dh_simpleYearAD,
        'fo': dh_simpleYearAD,
        'fr': dh_simpleYearAD,
        'fur': dh_simpleYearAD,
        'fy': dh_simpleYearAD,
        'ga': dh_simpleYearAD,
        'gan': lambda v: dh_yearAD(v, '%d年'),
        'gd': dh_simpleYearAD,
        'gl': dh_simpleYearAD,
        'gu': lambda v: dh_yearAD(v, '%G'),
        'he': dh_simpleYearAD,
        'hi': lambda v: dh_yearAD(v, '%H'),
        'hr': lambda v: dh_yearAD(v, '%d.'),
        'hu': dh_simpleYearAD,
        'hy': dh_simpleYearAD,
        'ia': dh_simpleYearAD,
        'id': dh_simpleYearAD,
        'ie': dh_simpleYearAD,
        'ilo': dh_simpleYearAD,
        'io': dh_simpleYearAD,
        'is': dh_simpleYearAD,
        'it': dh_simpleYearAD,
        'ja': lambda v: dh_yearAD(v, '%d年'),
        'jbo': lambda v: dh_yearAD(v, '%dmoi nanca'),
        'ka': dh_simpleYearAD,
        'kn': lambda v: dh_yearAD(v, '%K'),
        'ko': lambda v: dh_yearAD(v, '%d년'),
        'ksh': lambda v: dh_yearAD(v, 'Joohr %d'),
        'ku': dh_simpleYearAD,
        'kw': dh_simpleYearAD,
        'la': dh_simpleYearAD,
        'lb': dh_simpleYearAD,
        'li': dh_simpleYearAD,
        'lt': dh_simpleYearAD,
        'lv': dh_simpleYearAD,
        'mi': dh_simpleYearAD,
        'mhr': dh_simpleYearAD,
        'mk': dh_simpleYearAD,
        'ml': dh_simpleYearAD,
        'mo': dh_simpleYearAD,
        'mr': lambda v: dh_yearAD(v, 'ई.स. %H'),
        'ms': dh_simpleYearAD,
        'na': dh_simpleYearAD,
        'nap': dh_simpleYearAD,
        'nds': dh_simpleYearAD,
        'nl': dh_simpleYearAD,
        'nn': dh_simpleYearAD,
        'nb': dh_simpleYearAD,
        'nso': dh_simpleYearAD,
        'oc': dh_simpleYearAD,
        'os': dh_simpleYearAD,
        'pdc': dh_simpleYearAD,
        'pl': dh_simpleYearAD,
        'pt': dh_simpleYearAD,
        'rm': dh_simpleYearAD,
        'ro': dh_simpleYearAD,
        'rup': dh_simpleYearAD,
        'ru': lambda v: dh_yearAD(v, '%d год'),
        'sco': dh_simpleYearAD,
        'scn': dh_simpleYearAD,
        'se': dh_simpleYearAD,
        'sh': dh_simpleYearAD,
        'sk': dh_simpleYearAD,
        'sl': dh_simpleYearAD,
        'sm': dh_simpleYearAD,
        'sq': dh_simpleYearAD,
        'sr': dh_simpleYearAD,
        'sv': dh_simpleYearAD,
        'su': dh_simpleYearAD,
        'ta': dh_simpleYearAD,
        'te': dh_simpleYearAD,
        # 2005 => 'พ.ศ. 2548'
        'th': lambda v: dh_yearAD(v, 'พ.ศ. %T'),
        'tl': dh_simpleYearAD,
        'tpi': dh_simpleYearAD,
        'tr': dh_simpleYearAD,
        'tt': dh_simpleYearAD,
        'uk': dh_simpleYearAD,
        'ur': lambda v: dh_yearAD(v, '%dء'),
        'uz': dh_simpleYearAD,
        'vec': dh_simpleYearAD,
        'vi': dh_simpleYearAD,
        'vo': dh_simpleYearAD,
        'wa': dh_simpleYearAD,
        'zh': lambda v: dh_yearAD(v, '%d年'),
        'nan': lambda v: dh_yearAD(v, '%d nî'),
    },

    'YearBC': {
        'af': lambda v: dh_yearBC(v, '%d v.C.'),
        'ast': lambda v: dh_yearBC(v, '%d edC'),
        'be': lambda v: dh_yearBC(v, '%d да н.э.'),
        'bg': lambda v: dh_yearBC(v, '%d г. пр.н.е.'),
        'bs': lambda v: dh_yearBC(v, '%d p.n.e.'),
        'ca': lambda v: dh_yearBC(v, '%d aC'),
        'cs': lambda v: dh_yearBC(v, '%d př. n. l.'),
        'cy': lambda v: dh_yearBC(v, '%d CC'),
        'da': lambda v: dh_yearBC(v, '%d f.Kr.'),
        'de': lambda v: dh_yearBC(v, '%d v. Chr.'),
        'el': lambda v: dh_yearBC(v, '%d π.Χ.'),
        'en': lambda v: dh_yearBC(v, '%d BC'),
        'eo': lambda v: dh_yearBC(v, '-%d'),
        'es': lambda v: dh_yearBC(v, '%d a. C.'),
        'et': lambda v: dh_yearBC(v, '%d eKr'),
        'eu': lambda v: dh_yearBC(v, 'K. a. %d'),
        'fa': lambda v: dh_yearBC(v, '%d (پیش از میلاد)'),
        'fi': lambda v: dh_yearBC(v, '%d eaa.'),
        'fo': lambda v: dh_yearBC(v, '%d f. Kr.'),
        'fr': lambda v: dh_yearBC(v, '%d av. J.-C.'),
        'gl': lambda v: dh_yearBC(v, '-%d'),
        'he': lambda v: dh_yearBC(v, '%d לפני הספירה'),
        'hr': lambda v: dh_yearBC(v, '%d. pr. Kr.'),
        'hu': lambda v: dh_yearBC(v, 'I. e. %d'),
        'id': lambda v: dh_yearBC(v, '%d SM'),
        'io': lambda v: dh_yearBC(v, '%d aK'),
        'is': lambda v: dh_yearBC(v, '%d f. Kr.'),
        'it': lambda v: dh_yearBC(v, '%d a.C.'),
        'ka': lambda v: dh_yearBC(v, 'ძვ. წ. %d'),
        'ko': lambda v: dh_yearBC(v, '기원전 %d년'),
        'ksh': lambda v: dh_yearBC(v, 'Joohr %d füür Krėßtůß'),
        'la': lambda v: dh_yearBC(v, '%d a.C.n.'),
        'lb': lambda v: dh_yearBC(v, '-%d'),
        'lt': lambda v: dh_yearBC(v, '%d m. pr. m. e.'),
        'lv': lambda v: dh_yearBC(v, '%d p.m.ē.'),
        'mk': lambda v: dh_yearBC(v, '%d п.н.е.'),
        'ms': lambda v: dh_yearBC(v, '%d SM'),
        'nap': lambda v: dh_yearBC(v, '%d AC'),
        'nds': lambda v: dh_yearBC(v, '%d v. Chr.'),
        'nl': lambda v: dh_yearBC(v, '%d v.Chr.'),
        'nn': lambda v: dh_yearBC(v, '-%d'),
        'nb': lambda v: dh_yearBC(v, '%d f.Kr.'),
        'oc': lambda v: dh_yearBC(v, '-%d'),
        'pl': lambda v: dh_yearBC(v, '%d p.n.e.'),
        'pt': lambda v: dh_yearBC(v, '%d a.C.'),
        'ro': lambda v: dh_yearBC(v, '%d î.Hr.'),
        'ru': lambda v: dh_yearBC(v, '%d год до н. э.'),
        'scn': lambda v: dh_yearBC(v, '%d a.C.'),
        'sk': lambda v: dh_yearBC(v, '%d pred Kr.'),
        'sl': lambda v: dh_yearBC(v, '%d pr. n. št.'),
        'sq': lambda v: dh_yearBC(v, '%d p.e.s.'),
        'sr': lambda v: dh_yearBC(v, '%d. п. н. е.'),
        'sv': lambda v: dh_yearBC(v, '%d f.Kr.'),
        'sw': lambda v: dh_yearBC(v, '%d KK'),
        'ta': lambda v: dh_yearBC(v, 'கி.மு %d'),
        'tr': lambda v: dh_yearBC(v, 'M.Ö. %d'),
        'tt': lambda v: dh_yearBC(v, 'MA %d'),
        'uk': lambda v: dh_yearBC(v, '%d до н. е.'),
        'ur': lambda v: dh_yearBC(v, '%d ق م'),
        'uz': lambda v: dh_yearBC(v, 'Mil. av. %d'),
        'vec': lambda v: dh_yearBC(v, '%d a.C.'),
        'vo': lambda v: dh_yearBC(v, '%d b.K.'),
        'zh': lambda v: dh_yearBC(v, '前%d年'),
    },

    'DecadeAD': {
        'gsw': lambda v: dh_decAD(v, '%der'),
        'ar': lambda v: dh_decAD(v, '%d عقد'),
        'ang': lambda v: dh_decAD(v, '%de'),
        'ast': lambda v: dh_decAD(v, 'Años %d'),
        'bg': lambda v: dh_decAD(v, '%d-те'),
        'br': lambda v: dh_decAD(v, 'Bloavezhioù %d'),
        'bs': lambda v: dh_decAD(v, '%dte'),

        # Unknown what the pattern is, but 1970 is different
        'ca': lambda m: multi(m, [
            (lambda v: dh_decAD(v, 'Dècada de %d'), lambda p: p == 1970),
            (lambda v: dh_decAD(v, 'Dècada del %d'), alwaysTrue)]),

        # 1970s => '1970-1979'
        'cs': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, '1-9'), lambda p: p == 1),
            (lambda v: dh(v, '%d-%d',
                          lambda i: (encDec0(i), encDec0(i) + 9), decSinglVal),
             alwaysTrue)]),
        'cy': lambda v: dh_decAD(v, '%dau'),
        'da': lambda v: dh_decAD(v, "%d'erne"),
        'de': lambda v: dh_decAD(v, '%der'),
        'el': lambda v: dh_decAD(v, 'Δεκαετία %d'),
        'en': lambda v: dh_decAD(v, '%ds'),
        'eo': lambda v: dh_decAD(v, '%d-aj jaroj'),
        'es': lambda v: dh_decAD(v, 'Años %d'),
        'et': lambda v: dh_decAD(v, '%d. aastad'),
        'fa': lambda v: dh_decAD(v, 'دهه %d (میلادی)'),

        # decades ending in 00 are spelled differently
        'fi': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 0, 'Ensimmäinen vuosikymmen'),
             lambda p: p == 0),
            (lambda v: dh_decAD(v, '%d-luku'), lambda p: (p % 100 != 0)),
            (lambda v: dh_decAD(v, '%d-vuosikymmen'), alwaysTrue)]),

        'fo': lambda v: dh_decAD(v, '%d-árini'),
        'fr': lambda v: dh_decAD(v, 'Années %d'),
        'ga': lambda v: dh_decAD(v, '%didí'),
        'gan': lambda v: dh_decAD(v, '%d年代'),
        'he': lambda m: multi(m, [
            (lambda v: dh(v, 'שנות ה־%d',
                          lambda i: encDec0(i) % 100,
                          lambda ii: 1900 + ii[0]),
             lambda p: p >= 1900 and p < 2000),
            # This is a dummy value, just to avoid validation testing.
            (lambda v: dh_decAD(v, '%dth decade'),
             alwaysTrue)]),  # ********** ERROR!!!
        'hi': lambda v: dh_decAD(v, '%H का दशक'),

        # 1970s => 1970-1979
        'hr': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, '1-9'), lambda p: p == 1),
            (lambda v: dh(v, '%d-%d',
                          lambda i: (encDec0(i), encDec0(i) + 9),
                          lambda ii: ii[0]), alwaysTrue)]),
        'hu': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, '0-s évek'), lambda p: p == 1),
            (lambda v: dh_decAD(v, '%d-as évek'),
             lambda p: (p % 100 // 10) in (0, 2, 3, 6, 8)),
            (lambda v: dh_decAD(v, '%d-es évek'), alwaysTrue)]),
        'io': lambda v: dh_decAD(v, '%da yari'),

        # 1970s => '1971–1980'
        'is': lambda v: dh(v, '%d–%d',
                           lambda i: (encDec1(i), encDec1(i) + 9),
                           lambda ii: ii[0] - 1),
        'it': lambda v: dh_decAD(v, 'Anni %d'),
        'ja': lambda v: dh_decAD(v, '%d年代'),
        'ka': lambda v: dh_decAD(v, '%d-ები‎'),
        'ko': lambda v: dh_decAD(v, '%d년대'),
        'ksh': lambda v: dh_decAD(v, '%d-er Joohre'),

        # 1970s => 'Decennium 198' (1971-1980)
        'la': lambda v: dh(v, 'Decennium %d',
                           lambda i: encDec1(i) // 10 + 1,
                           lambda ii: (ii[0] - 1) * 10),

        # 1970s => 'XX amžiaus 8-as dešimtmetis' (1971-1980)
        'lt': lambda v: dh(v, '%R amžiaus %d-as dešimtmetis',
                           lambda i: (encDec1(i) // 100 + 1,
                                      encDec1(i) % 100 // 10 + 1),
                           lambda v: (v[0] - 1) * 100 + (v[1] - 1) * 10),

        # 1970s => 'Ngahurutanga 198' (1971-1980)
        'mi': lambda v: dh(v, 'Ngahurutanga %d',
                           lambda i: encDec0(i) // 10 + 1,
                           lambda ii: (ii[0] - 1) * 10),

        'mhr': lambda v: dh_decAD(v, '%d ийла'),

        # 1970s => '1970-1979'
        'nl': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, '1-9'), lambda p: p == 1),
            (lambda v: dh(v, '%d-%d',
                          lambda i: (encDec0(i), encDec0(i) + 9), decSinglVal),
             alwaysTrue)]),
        'nn': lambda v: dh_decAD(v, '%d0-åra'),  # FIXME: not sure of this one
        'nb': lambda v: dh_decAD(v, '%d-årene'),
        'os': lambda v: dh_decAD(v, '%d-тæ'),

        # 1970s => 'Lata 70. XX wieku' for anything
        # except 1900-1919, 2000-2019,
        # etc, in which case its 'Lata 1900-1909'
        'pl': lambda m: multi(m, [
            (lambda v: dh(v, 'Lata %d-%d',
                          lambda i: (encDec0(i), encDec0(i) + 9), decSinglVal),
             lambda p: p % 100 >= 0 and p % 100 < 20),
            (lambda v: dh(v, 'Lata %d. %R wieku',
                          lambda i: (encDec0(i) % 100, encDec0(i) // 100 + 1),
                          lambda ii: (ii[1] - 1) * 100 + ii[0]),
             alwaysTrue)]),
        'pt': lambda v: dh_decAD(v, 'Década de %d'),
        'ro': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 0, 'Primul deceniu d.Hr.'),
             lambda p: p == 0),
            (lambda v: dh_decAD(v, 'Anii %d'), alwaysTrue)]),
        'ru': lambda v: dh_decAD(v, '%d-е'),
        'scn': lambda v: dh_decAD(v, '%dini'),

        # 1970 => '70. roky 20. storočia'
        'sk': lambda v: dh(v, '%d. roky %d. storočia',
                           lambda i: (encDec0(i) % 100, encDec0(i) // 100 + 1),
                           lambda ii: (ii[1] - 1) * 100 + ii[0]),

        'sl': lambda v: dh_decAD(v, '%d.'),
        'sq': lambda v: dh_decAD(v, 'Vitet %d'),
        'sr': lambda v: dh_decAD(v, '%dе'),
        'sv': lambda m: multi(m, [
            (lambda v: dh_decAD(v, '%d-talet (decennium)'),
             lambda p: (p % 100 == 0)),
            (lambda v: dh_decAD(v, '%d-talet'), alwaysTrue)]),
        'tt': lambda v: dh_decAD(v, '%d. yıllar'),
        'uk': lambda m: multi(m, [
            (lambda v: dh_decAD(v, '%d-ві'),
             lambda p: p == 0 or (p % 100 == 40)),
            (lambda v: dh_decAD(v, '%d-ні'), lambda p: p % 1000 == 0),
            (lambda v: dh_decAD(v, '%d-ті'), alwaysTrue)]),
        'ur': lambda v: dh_decAD(v, '%d کی دہائی'),
        'wa': lambda v: dh_decAD(v, 'Anêyes %d'),
        'zh': lambda v: dh_decAD(v, '%d年代'),
        'nan': lambda v: dh_decAD(v, '%d nî-tāi'),
    },

    'DecadeBC': {
        'de': lambda v: dh_decBC(v, '%der v. Chr.'),
        'da': lambda v: dh_decBC(v, "%d'erne f.Kr."),
        'en': lambda v: dh_decBC(v, '%ds BC'),
        'es': lambda v: dh_decBC(v, 'Años %d adC'),
        'et': lambda v: dh_decBC(v, '%d. aastad eKr'),
        'eu': lambda v: dh_decBC(v, 'K. a. %dko hamarkada'),

        # decades ending in 00 are spelled differently
        'fi': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 0, 'Ensimmäinen vuosikymmen eaa.'),
             lambda p: p == 0),
            (lambda v: dh_decBC(v, '%d-luku eaa.'), lambda p: (p % 100 != 0)),
            (lambda v: dh_decBC(v, '%d-vuosikymmen eaa.'), alwaysTrue)]),

        'fr': lambda v: dh_decBC(v, 'Années -%d'),
        'he': lambda v: dh_decBC(v, 'שנות ה־%d לפני הספירה'),
        'hr': lambda v: dh_decBC(v, '%dih p.n.e.'),

        'hu': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 0, 'i. e. 0-s évek'),
             lambda p: p == 0),
            (lambda v: dh_decBC(v, 'i. e. %d-as évek'),
             lambda p: (p % 100 // 10) in (0, 2, 3, 6, 8)),
            (lambda v: dh_decBC(v, 'i. e. %d-es évek'), alwaysTrue)]),
        'it': lambda v: dh_decBC(v, 'Anni %d a.C.'),
        'ka': lambda v: dh_decBC(v, 'ძვ. წ. %d-ები'),
        'ksh': lambda v: dh_decBC(v, '%d-er Joohre füür Krėßtůß'),
        # uncertain if ksh is right. might go to redirect.

        # '19-10 v. Chr.'
        'nl': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, '9-1 v.Chr.'), lambda p: p == 1),
            (lambda v: dh(v, '%d-%d v.Chr.',
                          lambda i: (encDec0(i) + 9, encDec0(i)),
                          lambda ii: ii[1]), alwaysTrue)]),
        'pt': lambda v: dh_decBC(v, 'Década de %d a.C.'),
        'ro': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 0, 'Primul deceniu î.Hr.'),
             lambda p: p == 0),
            (lambda v: dh_decBC(v, 'Anii %d î.Hr.'), alwaysTrue)]),

        'ru': lambda v: dh_decBC(v, '%d-е до н. э.'),
        'sl': lambda v: dh_decBC(v, '%d. pr. n. št.'),

        'sv': lambda m: multi(m, [
            (lambda v: dh_decBC(v, '%d-talet f.Kr. (decennium)'),
             lambda p: (p % 100 == 0)),
            (lambda v: dh_decBC(v, '%d-talet f.Kr.'), alwaysTrue)]),

        'tt': lambda v: dh_decBC(v, 'MA %d. yıllar'),
        'uk': lambda m: multi(m, [
            (lambda v: dh_decBC(v, '%d-ві до Р.Х.'),
             lambda p: p == 0 or (p % 100 == 40)),
            (lambda v: dh_decBC(v, '%d-ті до Р.Х.'), alwaysTrue)]),
        'ur': lambda v: dh_decBC(v, '%d کی دہائی ق م'),
        'zh': lambda v: dh_decBC(v, '前%d年代'),
    },

    'CenturyAD': {
        'af': lambda m: multi(m, [
            (lambda v: dh_centuryAD(v, '%dste eeu'),
             lambda p: p in (1, 8) or (p >= 20)),
            (lambda v: dh_centuryAD(v, '%dde eeu'), alwaysTrue)]),
        'gsw': lambda v: dh_centuryAD(v, '%d. Jahrhundert'),
        'ang': lambda v: dh_centuryAD(v, '%de gēarhundred'),
        'ar': lambda v: dh_centuryAD(v, 'قرن %d'),
        'ast': lambda v: dh_centuryAD(v, 'Sieglu %R'),
        'be': lambda v: dh_centuryAD(v, '%d стагодзьдзе'),
        'bg': lambda v: dh_centuryAD(v, '%d век'),
        'br': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, 'Iañ kantved'), lambda p: p == 1),
            (lambda v: dh_constVal(v, 2, 'Eil kantved'), lambda p: p == 2),
            (lambda v: dh_centuryAD(v, '%Re kantved'), lambda p: p in (2, 3)),
            (lambda v: dh_centuryAD(v, '%Rvet kantved'), alwaysTrue)]),
        'bs': lambda v: dh_centuryAD(v, '%d. vijek'),
        'ca': lambda v: dh_centuryAD(v, 'Segle %R'),
        'cs': lambda v: dh_centuryAD(v, '%d. století'),
        'cv': lambda v: dh_centuryAD(v, '%R ĕмĕр'),
        'cy': lambda m: multi(m, [
            (lambda v: dh_centuryAD(v, '%deg ganrif'),
             lambda p: p in (17, 19)),
            (lambda v: dh_centuryAD(v, '%dain ganrif'), lambda p: p == 21),
            (lambda v: dh_centuryAD(v, '%dfed ganrif'), alwaysTrue)]),
        'da': lambda v: dh_centuryAD(v, '%d00-tallet'),
        'de': lambda v: dh_centuryAD(v, '%d. Jahrhundert'),
        'el': lambda m: multi(m, [
            (lambda v: dh_centuryAD(v, '%dός αιώνας'), lambda p: p == 20),
            (lambda v: dh_centuryAD(v, '%dος αιώνας'), alwaysTrue)]),
        'en': lambda m: multi(m, [
            (lambda v: dh_centuryAD(v, '%dst century'),
             lambda p: p == 1 or (p > 20 and p % 10 == 1)),
            (lambda v: dh_centuryAD(v, '%dnd century'),
             lambda p: p == 2 or (p > 20 and p % 10 == 2)),
            (lambda v: dh_centuryAD(v, '%drd century'),
             lambda p: p == 3 or (p > 20 and p % 10 == 3)),
            (lambda v: dh_centuryAD(v, '%dth century'), alwaysTrue)]),
        'eo': lambda v: dh_centuryAD(v, '%d-a jarcento'),
        'es': lambda v: dh_centuryAD(v, 'Siglo %R'),
        'et': lambda v: dh_centuryAD(v, '%d. sajand'),
        'eu': lambda v: dh_centuryAD(v, '%R. mendea'),  # %R. mende
        'fa': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 20, 'سده ۲۰ (میلادی)'),
             lambda p: p == 20),
            # This is a dummy value, just to avoid validation testing.
            # Later, it should be replaced with a proper 'fa' titles
            (lambda v: dh_centuryAD(v, 'سده %d (میلادی)'),
             alwaysTrue)]),  # ********** ERROR!!!
        'fi': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, 'Ensimmäinen vuosisata'),
             lambda p: p == 1),
            (lambda v: dh(v, '%d00-luku',
                          lambda i: i - 1,
                          lambda ii: ii[0] + 1), alwaysTrue)]),
        'fo': lambda v: dh_centuryAD(v, '%d. øld'),
        'fr': lambda m: multi(m, [
            (lambda v: dh_centuryAD(v, '%Rer siècle'), lambda p: p == 1),
            (lambda v: dh_centuryAD(v, '%Re siècle'), alwaysTrue)]),
        'fy': lambda v: dh_centuryAD(v, '%de ieu'),
        'ga': lambda v: dh_centuryAD(v, '%dú haois'),
        'gl': lambda v: dh_centuryAD(v, 'Século %R'),
        'he': lambda v: dh_centuryAD(v, 'המאה ה־%d'),
        'hi': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 20, 'बीसवी शताब्दी'), lambda p: p == 20),
            # This is a dummy value, just to avoid validation testing.
            # Later, it should be replaced with a proper 'fa' titles
            (lambda v: dh_centuryAD(v, '%dth century'),
             alwaysTrue)]),  # ********** ERROR!!!
        'hr': lambda v: dh_centuryAD(v, '%d. stoljeće'),
        'hu': lambda v: dh_centuryAD(v, '%d. század'),
        'id': lambda v: dh_centuryAD(v, 'Abad ke-%d'),
        'io': lambda v: dh_centuryAD(v, '%dma yar-cento'),
        'it': lambda v: dh_centuryAD(v, '%R secolo'),
        'is': lambda v: dh_centuryAD(v, '%d. öldin'),
        'ja': lambda v: dh_centuryAD(v, '%d世紀'),
        'jv': lambda v: dh_centuryAD(v, 'Abad kaping %d'),
        'ka': lambda v: dh_centuryAD(v, '%R საუკუნე'),
        'ko': lambda v: dh_centuryAD(v, '%d세기'),
        'ku': lambda v: dh_centuryAD(v, "Sedsala %d'an"),
        'kw': lambda m: multi(m, [
            (lambda v: dh_centuryAD(v, '%dsa kansblydhen'), lambda p: p <= 3),
            (lambda v: dh_centuryAD(v, '%da kansblydhen'), lambda p: p == 4),
            (lambda v: dh_centuryAD(v, '%des kansblydhen'), lambda p: p == 5),
            (lambda v: dh_centuryAD(v, '%dns kansblydhen'), lambda p: p >= 20),
            (lambda v: dh_centuryAD(v, '%dves kansblydhen'), alwaysTrue)]),
        'ksh': lambda v: dh_centuryAD(v, '%d. Joohunndot'),
        'la': lambda v: dh_centuryAD(v, 'Saeculum %d'),
        'lb': lambda v: dh_centuryAD(v, '%d. Joerhonnert'),

        # Limburgish (li) have individual names for each century
        'li': lambda v: slh(v, ['Ierste iew', 'Twiede iew', 'Derde iew',
                                'Veerde iew', 'Viefde iew', 'Zesde iew',
                                'Zevende iew', 'Achste iew',
                                'Negende iew', 'Tiende iew',
                                'Elfde iew', 'Twelfde iew',
                                'Dertiende iew', 'Veertiende iew',
                                'Vieftiende iew', 'Zestiende iew',
                                'Zeventiende iew', 'Achtiende iew',
                                'Negentiende iew', 'Twintegste iew',
                                'Einentwintegste iew',
                                'Twieëntwintegste iew']),

        'lt': lambda v: dh_centuryAD(v, '%R amžius'),
        'lv': lambda v: dh_centuryAD(v, '%d. gadsimts'),
        'mi': lambda v: dh_centuryAD(v, 'Tua %d rau tau'),
        'mk': lambda v: dh_centuryAD(v, '%d век'),
        'nds': lambda v: dh_centuryAD(v, '%d. Johrhunnert'),
        'nl': lambda v: dh_centuryAD(v, '%de eeuw'),
        'nn': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, '1. århundret'), lambda p: p == 1),
            (lambda v: dh(v, '%d00-talet', lambda i: i - 1,
                          lambda ii: ii[0] + 1), alwaysTrue)]),
        'nb': lambda v: dh_centuryAD(v, '%d. århundre'),
        'os': lambda v: dh_centuryAD(v, '%R æнус'),
        'pl': lambda v: dh_centuryAD(v, '%R wiek'),
        'pt': lambda v: dh_centuryAD(v, 'Século %R'),
        'ro': lambda v: dh_centuryAD(v, 'Secolul %R'),
        'ru': lambda v: dh_centuryAD(v, '%R век'),
        'scn': lambda v: dh_centuryAD(v, 'Sèculu %R'),
        'sk': lambda v: dh_centuryAD(v, '%d. storočie'),
        'sl': lambda v: dh_centuryAD(v, '%d. stoletje'),
        'sr': lambda v: dh_centuryAD(v, '%d. век'),
        'sq': lambda v: dh_centuryAD(v, 'Shekulli %R'),
        'sv': lambda v: dh(v, '%d00-talet',
                           lambda i: i - 1, lambda ii: ii[0] + 1),
        'su': lambda v: dh_centuryAD(v, 'Abad ka-%d'),
        'th': lambda v: dh_centuryAD(v, 'คริสต์ศตวรรษที่ %d'),
        'tr': lambda v: dh_centuryAD(v, '%d. yüzyıl'),
        'tt': lambda v: dh_centuryAD(v, '%d. yöz'),
        'uk': lambda v: dh_centuryAD(v, '%d століття'),
        'ur': lambda v: dh_centuryAD(v, '%d ویں صدی'),
        'vi': lambda v: dh_centuryAD(v, 'Thế kỷ %d'),
        'wa': lambda v: dh_centuryAD(v, '%dinme sieke'),
        'zh': lambda v: dh_centuryAD(v, '%d世纪'),
        'nan': lambda v: dh_centuryAD(v, '%d sè-kí'),
    },

    'CenturyBC': {
        'af': lambda m: multi(m, [
            (lambda v: dh_centuryBC(v, '%dste eeu v.C.'),
             lambda p: p in (1, 8) or (p >= 20)),
            (lambda v: dh_centuryBC(v, '%dde eeu v.C.'), alwaysTrue)]),
        'bg': lambda v: dh_centuryBC(v, '%d век пр.н.е.'),
        'br': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, 'Iañ kantved kt JK'),
             lambda p: p == 1),
            (lambda v: dh_constVal(v, 2, 'Eil kantved kt JK'),
             lambda p: p == 2),
            (lambda v: dh_centuryBC(v, '%Re kantved kt JK'),
             lambda p: p in (2, 3)),
            (lambda v: dh_centuryBC(v, '%Rvet kantved kt JK'), alwaysTrue)]),
        'ca': lambda v: dh_centuryBC(v, 'Segle %R aC'),
        'cs': lambda v: dh_centuryBC(v, '%d. století př. n. l.'),
        'da': lambda v: dh_centuryBC(v, '%d. århundrede f.Kr.'),
        'de': lambda v: dh_centuryBC(v, '%d. Jahrhundert v. Chr.'),
        'el': lambda v: dh_centuryBC(v, '%dος αιώνας π.Χ.'),
        'en': lambda m: multi(m, [
            (lambda v: dh_centuryBC(v, '%dst century BC'),
             lambda p: p == 1 or (p > 20 and p % 10 == 1)),
            (lambda v: dh_centuryBC(v, '%dnd century BC'),
             lambda p: p == 2 or (p > 20 and p % 10 == 2)),
            (lambda v: dh_centuryBC(v, '%drd century BC'),
             lambda p: p == 3 or (p > 20 and p % 10 == 3)),
            (lambda v: dh_centuryBC(v, '%dth century BC'), alwaysTrue)]),
        'eo': lambda v: dh_centuryBC(v, '%d-a jarcento a.K.'),
        'es': lambda v: dh_centuryBC(v, 'Siglo %R adC'),
        'et': lambda v: dh_centuryBC(v, '%d. aastatuhat eKr'),
        'fi': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, 'Ensimmäinen vuosisata eaa.'),
             lambda p: p == 1),
            (lambda v: dh(v, '%d00-luku eaa.', lambda i: i - 1,
                          lambda ii: ii[0] + 1), alwaysTrue)]),
        'fr': lambda m: multi(m, [
            (lambda v: dh_centuryBC(v, '%Rer siècle av. J.-C.'),
             lambda p: p == 1),
            (lambda v: dh_centuryBC(v, '%Re siècle av. J.-C.'),
             alwaysTrue)]),
        'he': lambda v: dh_centuryBC(v, 'המאה ה־%d לפני הספירה'),
        'hr': lambda v: dh_centuryBC(v, '%d. stoljeće p.n.e.'),
        'id': lambda v: dh_centuryBC(v, 'Abad ke-%d SM'),
        'io': lambda v: dh_centuryBC(v, '%dma yar-cento aK'),
        'it': lambda v: dh_centuryBC(v, '%R secolo AC'),
        'ja': lambda v: dh_centuryBC(v, '紀元前%d世紀'),
        'ka': lambda v: dh_centuryBC(v, 'ძვ. წ. %R საუკუნე'),
        'ko': lambda v: dh_centuryBC(v, '기원전 %d세기'),
        'ksh': lambda v: dh_centuryBC(v, '%d. Joohunndot füür Kreůßtůß'),
        # uncertain if ksh is right. might go to redirect.
        'la': lambda v: dh_centuryBC(v, 'Saeculum %d a.C.n.'),
        'lb': lambda v: dh_centuryBC(v, '%d. Joerhonnert v. Chr.'),
        'nl': lambda v: dh_centuryBC(v, '%de eeuw v.Chr.'),
        'nn': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, '1. århundret fvt.'),
             lambda p: p == 1),
            (lambda v: dh(v, '%d00-talet fvt.', lambda i: i - 1,
                          lambda ii: ii[0] + 1), alwaysTrue)]),
        'nb': lambda v: dh_centuryBC(v, '%d. århundre f.Kr.'),
        'pl': lambda v: dh_centuryBC(v, '%R wiek p.n.e.'),
        'pt': lambda v: dh_centuryBC(v, 'Século %R a.C.'),
        'ro': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, 'Secolul I î.Hr.'), lambda p: p == 1),
            (lambda v: dh_centuryBC(v, 'Secolul al %R-lea î.Hr.'),
             alwaysTrue)]),
        'ru': lambda v: dh_centuryBC(v, '%R век до н. э.'),
        'scn': lambda v: dh_centuryBC(v, 'Sèculu %R a.C.'),
        'sk': lambda v: dh_centuryBC(v, '%d. storočie pred Kr.'),
        'sl': lambda v: dh_centuryBC(v, '%d. stoletje pr. n. št.'),
        'sq': lambda v: dh_centuryBC(v, 'Shekulli %R p.e.s.'),
        'sr': lambda v: dh_centuryBC(v, '%d. век пне.'),
        'sv': lambda v: dh(v, '%d00-talet f.Kr.',
                           lambda i: i - 1, lambda ii: ii[0] + 1),
        'tr': lambda v: dh_centuryBC(v, 'MÖ %d. yüzyıl'),
        'tt': lambda v: dh_centuryBC(v, 'MA %d. yöz'),
        'uk': lambda v: dh_centuryBC(v, '%d століття до Р.Х.'),
        'zh': lambda m: multi(m, [
            (lambda v: dh_centuryBC(v, '前%d世纪'), lambda p: p < 4),
            (lambda v: dh_centuryBC(v, '前%d世紀'), alwaysTrue)]),
    },

    'CenturyAD_Cat': {
        'cs': lambda v: dh_centuryAD(v, '%d. století'),
        'da': lambda v: dh_centuryAD(v, '%d. århundrede'),
        'nb': lambda v: dh(v, '%d-tallet',
                           lambda i: (i - 1) * 100,
                           lambda ii: ii[0] // 100 + 1),
    },

    'CenturyBC_Cat': {
        'cs': lambda v: dh_centuryBC(v, '%d. století př. n. l.'),
        'de': lambda v: dh_centuryBC(v, 'Jahr (%d. Jh. v. Chr.)'),
        'nb': lambda v: dh(v, '%d-tallet f.Kr.',
                           lambda i: (i - 1) * 100,
                           lambda ii: ii[0] // 100 + 1),
    },

    'MillenniumAD': {
        'bg': lambda v: dh_millenniumAD(v, '%d хилядолетие'),
        'ca': lambda v: dh_millenniumAD(v, 'Mil·lenni %R'),
        'cs': lambda v: dh_millenniumAD(v, '%d. tisíciletí'),
        'de': lambda v: dh_millenniumAD(v, '%d. Jahrtausend'),
        'el': lambda v: dh_millenniumAD(v, '%dη χιλιετία'),
        'en': lambda m: multi(m, [
            (lambda v: dh_millenniumAD(v, '%dst millennium'),
             lambda p: p == 1 or (p > 20 and p % 10 == 1)),
            (lambda v: dh_millenniumAD(v, '%dnd millennium'),
             lambda p: p == 2 or (p > 20 and p % 10 == 2)),
            (lambda v: dh_millenniumAD(v, '%drd millennium'),
             lambda p: p == 3 or (p > 20 and p % 10 == 3)),
            (lambda v: dh_millenniumAD(v, '%dth millennium'),
             alwaysTrue)]),
        'es': lambda v: dh_millenniumAD(v, '%R milenio'),

        'fa': lambda v: dh_millenniumAD(v, 'هزاره %R (میلادی)'),
        'fi': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, 'Ensimmäinen vuosituhat'),
             lambda p: p == 1),
            (lambda v: dh_constVal(v, 2, 'Toinen vuosituhat'),
             lambda p: p == 2),
            (lambda v: dh_constVal(v, 3, 'Kolmas vuosituhat'),
             lambda p: p == 3),
            (lambda v: dh_constVal(v, 4, 'Neljäs vuosituhat'),
             lambda p: p == 4),
            (lambda v: dh_constVal(v, 5, 'Viides vuosituhat'),
             lambda p: p == 5),
            (lambda v: dh(v, '%d000-vuosituhat',
                          lambda i: i - 1,
                          lambda ii: ii[0] + 1),
             alwaysTrue)]),

        'fr': lambda m: multi(m, [
            (lambda v: dh_millenniumAD(v, '%Rer millénaire'),
             lambda p: p == 1),
            (lambda v: dh_millenniumAD(v, '%Re millénaire'), alwaysTrue)]),
        'he': lambda m: multi(m, [
            (lambda v: dh_millenniumAD(v, 'האלף הראשון %d'), lambda p: p == 1),
            (lambda v: dh_millenniumAD(v, 'האלף השני %d'), lambda p: p == 2),
            (lambda v: dh_millenniumAD(v, 'האלף השלישי %d'), lambda p: p == 3),
            (lambda v: dh_millenniumAD(v, 'האלף הרביעי %d'), lambda p: p == 4),
            (lambda v: dh_millenniumAD(v, 'האלף החמישי %d '),
             lambda p: p == 5),
            (lambda v: dh_millenniumAD(v, 'האלף השישי %d'), lambda p: p == 6),
            (lambda v: dh_millenniumAD(v, 'האלף השביעי %d'), lambda p: p == 7),
            (lambda v: dh_millenniumAD(v, 'האלף השמיני %d'), lambda p: p == 8),
            (lambda v: dh_millenniumAD(v, 'האלף התשיעי %d'), lambda p: p == 9),
            (lambda v: dh_millenniumAD(v, 'האלף העשירי %d'),
             lambda p: p == 10),
            (lambda v: dh_millenniumAD(v, 'האלף ה־%d'), alwaysTrue)]),
        'hu': lambda v: dh_millenniumAD(v, '%d. évezred'),
        'it': lambda v: dh_millenniumAD(v, '%R millennio'),
        'ja': lambda v: dh_millenniumAD(v, '%d千年紀'),
        'ka': lambda v: dh_millenniumAD(v, '%R ათასწლეული'),
        'ksh': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, 'Eetße Johdousend'),
             lambda p: p == 1),
            (lambda v: dh_constVal(v, 2, 'Zweijte Johdousend'),
             lambda p: p == 2),
            (lambda v: dh_constVal(v, 3, 'Drette Johdousend'),
             lambda p: p == 3),
            (lambda v: dh_constVal(v, 4, 'Veete Johdousend'),
             lambda p: p == 4),
            (lambda v: dh_constVal(v, 5, 'Föfte Johdousend'),
             lambda p: p == 5),
            (lambda v: dh_millenniumAD(v, '%d. Johdousend'), alwaysTrue)]),
        'lb': lambda v: dh_millenniumAD(v, '%d. Joerdausend'),
        'mhr': lambda v: dh_millenniumAD(v, '%R. курым — '),
        'lt': lambda v: dh_millenniumAD(v, '%d tūkstantmetis'),
        'pt': lambda v: slh(v, [
            'Primeiro milénio d.C.', 'Segundo milénio d.C.',
            'Terceiro milénio d.C.', 'Quarto milénio d.C.']),
        'ro': lambda v: slh(v, ['Mileniul I', 'Mileniul al II-lea',
                                'Mileniul III']),
        'ru': lambda v: dh_millenniumAD(v, '%d тысячелетие'),
        'sk': lambda v: dh_millenniumAD(v, '%d. tisícročie'),
        'sl': lambda v: dh_millenniumAD(v, '%d. tisočletje'),
        'sv': lambda v: dh(v, '%d000-talet (millennium)',
                           lambda i: i - 1, lambda ii: ii[0] + 1),
        'tt': lambda v: dh_millenniumAD(v, '%d. meñyıllıq'),
        'ur': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 0, '0000مبم'), lambda p: p == 0),
            (lambda v: dh_millenniumAD(v, '%d000مبم'), alwaysTrue)]),
    },

    'MillenniumBC': {
        'bg': lambda v: dh_millenniumBC(v, '%d хилядолетие пр.н.е.'),
        'ca': lambda v: dh_millenniumBC(v, 'Mil·lenni %R aC'),
        'cs': lambda v: dh_millenniumBC(v, '%d. tisíciletí př. n. l.'),
        'da': lambda v: dh_millenniumBC(v, '%d. årtusinde f.Kr.'),
        'de': lambda v: dh_millenniumBC(v, '%d. Jahrtausend v. Chr.'),
        'el': lambda v: dh_millenniumBC(v, '%dη χιλιετία π.Χ.'),
        'en': lambda v: dh_millenniumBC(v, '%dst millennium BC'),
        'es': lambda v: dh_millenniumBC(v, '%R milenio adC'),
        'fi': lambda m: multi(m, [
            (lambda v: dh_constVal(v, 1, 'Ensimmäinen vuosituhat eaa.'),
             lambda p: p == 1),
            (lambda v: dh(v, '%d000-vuosituhat eaa.', lambda i: i - 1,
                          lambda ii: ii[0] + 1), alwaysTrue)]),
        'fr': lambda v: dh_millenniumBC(v, '%Rer millénaire av. J.-C.'),
        'he': lambda m: multi(m, [
            (lambda v: dh_millenniumAD(v, 'האלף הראשון %d לפני הספירה'),
             lambda p: p == 1),
            (lambda v: dh_millenniumAD(v, 'האלף השני %d לפני הספירה'),
             lambda p: p == 2),
            (lambda v: dh_millenniumAD(v, 'האלף השלישי %d לפני הספירה'),
             lambda p: p == 3),
            (lambda v: dh_millenniumAD(v, 'האלף הרביעי %d לפני הספירה'),
             lambda p: p == 4),
            (lambda v: dh_millenniumAD(v, 'האלף החמישי %d לפני הספירה'),
             lambda p: p == 5),
            (lambda v: dh_millenniumAD(v, 'האלף השישי %d לפני הספירה'),
             lambda p: p == 6),
            (lambda v: dh_millenniumAD(v, 'האלף השביעי %d לפני הספירה'),
             lambda p: p == 7),
            (lambda v: dh_millenniumAD(v, 'האלף השמיני %d לפני הספירה'),
             lambda p: p == 8),
            (lambda v: dh_millenniumAD(v, 'האלף התשיעי %d לפני הספירה'),
             lambda p: p == 9),
            (lambda v: dh_millenniumAD(v, 'האלף העשירי %d לפני הספירה'),
             lambda p: p == 10),
            (lambda v: dh_millenniumAD(v, 'האלף ה־%d לפני הספירה'),
             alwaysTrue)]),
        'hu': lambda v: dh_millenniumBC(v, 'I. e. %d. évezred'),
        'it': lambda v: dh_millenniumBC(v, '%R millennio AC'),
        'ja': lambda v: dh_millenniumBC(v, '紀元前%d千年紀'),
        'ka': lambda v: dh_millenniumBC(v, 'ძვ. წ. %R ათასწლეული'),
        'lb': lambda v: dh_millenniumBC(v, '%d. Joerdausend v. Chr.'),
        'nl': lambda v: dh_millenniumBC(v, '%de millennium v.Chr.'),
        'pt': lambda v: slh(v, ['Primeiro milénio a.C.',
                                'Segundo milénio a.C.',
                                'Terceiro milénio a.C.',
                                'Quarto milénio a.C.']),
        'ro': lambda v: dh_millenniumBC(v, 'Mileniul %R î.Hr.'),
        'ru': lambda v: dh_millenniumBC(v, '%d тысячелетие до н. э.'),
        'sv': lambda v: dh(v, '%d000-talet f.Kr. (millennium)',
                           lambda i: i - 1, lambda ii: ii[0] + 1),
        'tt': lambda v: dh_millenniumBC(v, 'MA %d. meñyıllıq'),
        'zh': lambda v: dh_millenniumBC(v, '前%d千年'),
    },

    'Cat_Year_MusicAlbums': {
        'cs': lambda v: dh_yearAD(v, 'Alba roku %d'),
        'en': lambda v: dh_yearAD(v, '%d albums'),
        'fa': lambda v: dh_yearAD(v, 'آلبوم‌های %d (میلادی)'),
        'fi': lambda v: dh_yearAD(v, 'Vuoden %d albumit'),
        'fr': lambda v: dh_yearAD(v, 'Album musical sorti en %d'),
        'he': lambda v: dh_yearAD(v, 'אלבומי %d'),
        'nb': lambda v: dh_yearAD(v, 'Musikkalbum fra %d'),
        'pl': lambda v: dh_yearAD(v, 'Albumy muzyczne wydane w roku %d'),
        'sl': lambda v: dh_yearAD(v, 'Albumi iz %d'),
        'sv': lambda v: dh_yearAD(v, '%d års musikalbum'),
    },

    'Cat_BirthsAD': {
        'an': lambda v: dh_yearAD(v, '%d (naixencias)'),
        'ar': lambda v: dh_yearAD(v, 'مواليد %d'),
        'arz': lambda v: dh_yearAD(v, 'مواليد %d'),
        'bar': lambda v: dh_yearAD(v, 'Geboren %d'),
        'be': lambda v: dh_yearAD(v, 'Нарадзіліся ў %d годзе'),
        'be-tarask': lambda v: dh_yearAD(v, 'Нарадзіліся ў %d годзе'),
        'bg': lambda v: dh_yearAD(v, 'Родени през %d година'),
        'bjn': lambda v: dh_yearAD(v, 'Kalahiran %d'),
        'bn': lambda v: dh_yearAD(v, '%B-এ জন্ম'),
        'bpy': lambda v: dh_yearAD(v, 'মারি %B-এ উজ্জিসিতা'),
        'br': lambda v: dh_yearAD(v, 'Ganedigezhioù %d'),
        'bs': lambda v: dh_yearAD(v, '%d rođenja'),
        'cbk-zam': lambda v: dh_yearAD(v, 'Nacidos en %d'),
        'crh': lambda v: dh_yearAD(v, '%d senesinde doğğanlar'),
        'cs': lambda v: dh_yearAD(v, 'Narození %d'),
        'cy': lambda v: dh_yearAD(v, 'Genedigaethau %d'),
        'da': lambda v: dh_yearAD(v, 'Født i %d'),
        'de': lambda v: dh_yearAD(v, 'Geboren %d'),
        'dsb': lambda v: dh_yearAD(v, 'Roź. %d'),
        'el': lambda v: dh_yearAD(v, 'Γεννήσεις το %d'),
        'en': lambda v: dh_yearAD(v, '%d births'),
        'eo': lambda v: dh_yearAD(v, 'Naskiĝintoj en %d'),
        'es': lambda v: dh_yearAD(v, 'Nacidos en %d'),
        'et': lambda v: dh_yearAD(v, 'Sündinud %d'),
        'eu': lambda v: dh_yearAD(v, '%dko jaiotzak'),
        'fi': lambda v: dh_yearAD(v, 'Vuonna %d syntyneet'),
        'fa': lambda v: dh_yearAD(v, 'زادگان %F (میلادی)'),
        'fr': lambda v: dh_yearAD(v, 'Naissance en %d'),
        'ga': lambda v: dh_yearAD(v, 'Daoine a rugadh i %d'),
        'gan': lambda v: dh_yearAD(v, '%d年出世'),
        'gv': lambda v: dh_yearAD(v, "Ruggyryn 'sy vlein %d"),
        'hsb': lambda v: dh_yearAD(v, 'Rodź. %d'),
        'hy': lambda v: dh_yearAD(v, '%d ծնունդներ'),
        'id': lambda v: dh_yearAD(v, 'Kelahiran %d'),
        'is': lambda v: dh_yearAD(v, 'Fólk fætt árið %d'),
        'it': lambda v: dh_yearAD(v, 'Nati nel %d'),
        'ja': lambda v: dh_yearAD(v, '%d年生'),
        'jv': lambda v: dh_yearAD(v, 'Lair %d'),
        'ka': lambda v: dh_yearAD(v, 'დაბადებული %d'),
        'kk': lambda v: dh_yearAD(v, '%d жылы туғандар'),
        'ko': lambda v: dh_yearAD(v, '%d년 태어남'),
        'la': lambda v: dh_yearAD(v, 'Nati %d'),
        'lb': lambda v: dh_yearAD(v, 'Gebuer %d'),
        'lv': lambda v: dh_yearAD(v, '%d. gadā dzimušiel'),
        'mk': lambda v: dh_yearAD(v, 'Родени во %d година'),
        'ml': lambda v: dh_yearAD(v, '%d-ൽ ജനിച്ചവർ'),
        'mn': lambda v: dh_yearAD(v, '%d онд төрөгсөд'),
        'mr': lambda v: dh_yearAD(v, 'इ.स. %H मधील जन्म'),
        'ms': lambda v: dh_yearAD(v, 'Kelahiran %d'),
        'mt': lambda v: dh_yearAD(v, 'Twieldu fl-%d'),
        'nah': lambda v: dh_yearAD(v, 'Ōtlācatqueh xiuhpan %d'),
        'new': lambda v: dh_yearAD(v, '%Hय् बुगु'),
        'nn': lambda v: dh_yearAD(v, 'Fødde i %d'),
        'nb': lambda v: dh_yearAD(v, 'Fødsler i %d'),
        'oc': lambda v: dh_yearAD(v, 'Naissença en %d'),
        'pdc': lambda v: dh_yearAD(v, 'Gebore %d'),
        'pl': lambda v: dh_yearAD(v, 'Urodzeni w %d'),
        'qu': lambda v: dh_yearAD(v, 'Paqarisqa %d'),
        'ro': lambda v: dh_yearAD(v, 'Nașteri în %d'),
        'ru': lambda v: dh_yearAD(v, 'Родившиеся в %d году'),
        'sah': lambda v: dh_yearAD(v, '%d сыллаахха төрөөбүттэр'),
        'se': lambda v: dh_yearAD(v, 'Riegádeamit %d'),
        'sh': lambda v: dh_yearAD(v, 'Rođeni %d.'),
        'sk': lambda v: dh_yearAD(v, 'Narodenia v %d'),
        'sl': lambda v: dh_yearAD(v, 'Rojeni leta %d'),
        'sq': lambda v: dh_yearAD(v, 'Lindje %d'),
        'sr': lambda v: dh_yearAD(v, 'Рођени %d.'),
        'sv': lambda v: dh_yearAD(v, 'Födda %d'),
        'sw': lambda v: dh_yearAD(v, 'Waliozaliwa %d'),
        'szl': lambda v: dh_yearAD(v, 'Rodzyńi we %d'),
        'ta': lambda v: dh_yearAD(v, '%d பிறப்புகள்'),
        'te': lambda v: dh_yearAD(v, '%d జననాలు'),
        'th': lambda v: dh_yearAD(v, 'บุคคลที่เกิดในปี พ.ศ. %T'),
        'tl': lambda v: dh_yearAD(v, 'Ipinanganak noong %d'),
        'tr': lambda v: dh_yearAD(v, '%d doğumlular'),
        'tt': lambda v: dh_yearAD(v, '%d елда туганнар'),
        'uk': lambda v: dh_yearAD(v, 'Народились %d'),
        'ur': lambda v: dh_yearAD(v, '%dء کی پیدائشیں'),
        'vi': lambda v: dh_yearAD(v, 'Sinh %d'),
        'war': lambda v: dh_yearAD(v, 'Mga natawo han %d'),
        'yo': lambda v: dh_yearAD(v, 'Àwọn ọjọ́ìbí ní %d'),
        'zh': lambda v: dh_yearAD(v, '%d年出生'),
        'yue': lambda v: dh_yearAD(v, '%d年出世'),
    },

    'Cat_DeathsAD': {
        'an': lambda v: dh_yearAD(v, '%d (muertes)'),
        'ay': lambda v: dh_yearAD(v, 'Jiwäwi %d'),
        'ar': lambda v: dh_yearAD(v, 'وفيات %d'),
        'ba': lambda v: dh_yearAD(v, '%d йылда үлгәндәр'),
        'bar': lambda v: dh_yearAD(v, 'Gestorben %d'),
        'be': lambda v: dh_yearAD(v, 'Памерлі ў %d годзе'),
        'be-tarask': lambda v: dh_yearAD(v, 'Памерлі ў %d годзе'),
        'bg': lambda v: dh_yearAD(v, 'Починали през %d година'),
        'bn': lambda v: dh_yearAD(v, '%B-এ মৃত্যু'),
        'br': lambda v: dh_yearAD(v, 'Marvioù %d'),
        'bs': lambda v: dh_yearAD(v, '%d smrti'),
        'crh': lambda v: dh_yearAD(v, '%d senesinde ölgenler'),
        'cs': lambda v: dh_yearAD(v, 'Úmrtí %d'),
        'cy': lambda v: dh_yearAD(v, 'Marwolaethau %d'),
        'da': lambda v: dh_yearAD(v, 'Døde i %d'),
        'de': lambda v: dh_yearAD(v, 'Gestorben %d'),
        'dsb': lambda v: dh_yearAD(v, 'Wum. %d'),
        'el': lambda v: dh_yearAD(v, 'Θάνατοι το %d'),
        'en': lambda v: dh_yearAD(v, '%d deaths'),
        'eo': lambda v: dh_yearAD(v, 'Mortintoj en %d'),
        'es': lambda v: dh_yearAD(v, 'Fallecidos en %d'),
        'et': lambda v: dh_yearAD(v, 'Surnud %d'),
        'eu': lambda v: dh_yearAD(v, '%deko heriotzak'),
        'fa': lambda v: dh_yearAD(v, 'درگذشتگان %F (میلادی)'),
        'fi': lambda v: dh_yearAD(v, 'Vuonna %d kuolleet'),
        'fr': lambda v: dh_yearAD(v, 'Décès en %d'),
        'ga': lambda v: dh_yearAD(v, 'Básanna i %d'),
        'gan': lambda v: dh_yearAD(v, '%d年過世'),
        'gv': lambda v: dh_yearAD(v, "Baaseyn 'sy vlein %d"),
        'hif': lambda v: dh_yearAD(v, '%d maut'),
        'hsb': lambda v: dh_yearAD(v, 'Zemr. %d'),
        'hy': lambda v: dh_yearAD(v, '%d մահեր'),
        'id': lambda v: dh_yearAD(v, 'Kematian %d'),
        'is': lambda v: dh_yearAD(v, 'Fólk dáið árið %d'),
        'it': lambda v: dh_yearAD(v, 'Morti nel %d'),
        'ja': lambda v: dh_yearAD(v, '%d年没'),
        'jv': lambda v: dh_yearAD(v, 'Pati %d'),
        'ka': lambda v: dh_yearAD(v, 'გარდაცვლილი %d'),
        'kk': lambda v: dh_yearAD(v, '%d жылы қайтыс болғандар'),
        'ko': lambda v: dh_yearAD(v, '%d년 죽음'),
        'krc': lambda v: dh_yearAD(v, '%d джылда ёлгенле'),
        'ky': lambda v: dh_yearAD(v, '%d жылы кайтыш болгандар'),
        'la': lambda v: dh_yearAD(v, 'Mortui %d'),
        'lb': lambda v: dh_yearAD(v, 'Gestuerwen %d'),
        'lv': lambda v: dh_yearAD(v, '%d. gadā mirušie'),
        'mk': lambda v: dh_yearAD(v, 'Починати во %d година'),
        'ml': lambda v: dh_yearAD(v, '%d-ൽ മരിച്ചവർ'),
        'mn': lambda v: dh_yearAD(v, '%d онд нас барагсад'),
        'ms': lambda v: dh_yearAD(v, 'Kematian %d'),
        'mt': lambda v: dh_yearAD(v, 'Mietu fl-%d'),
        'nah': lambda v: dh_yearAD(v, '%d miquiztli'),
        'nn': lambda v: dh_yearAD(v, 'Døde i %d'),
        'nb': lambda v: dh_yearAD(v, 'Dødsfall i %d'),
        'oc': lambda v: dh_yearAD(v, 'Decès en %d'),
        'pdc': lambda v: dh_yearAD(v, 'Gschtaerewe %d'),
        'pl': lambda v: dh_yearAD(v, 'Zmarli w %d'),
        'pt': lambda v: dh_yearAD(v, 'Mortos em %d'),
        'qu': lambda v: dh_yearAD(v, 'Wañusqa %d'),
        'ro': lambda v: dh_yearAD(v, 'Decese în %d'),
        'ru': lambda v: dh_yearAD(v, 'Умершие в %d году'),
        'sah': lambda v: dh_yearAD(v, '%d сыллаахха өлбүттэр'),
        'se': lambda v: dh_yearAD(v, 'Jápmimat %d'),
        'sh': lambda v: dh_yearAD(v, 'Umrli %d.'),
        'sk': lambda v: dh_yearAD(v, 'Úmrtia v %d'),
        'sl': lambda v: dh_yearAD(v, 'Umrli leta %d'),
        'sq': lambda v: dh_yearAD(v, 'Vdekje %d'),
        'sr': lambda v: dh_yearAD(v, 'Умрли %d.'),
        'sv': lambda v: dh_yearAD(v, 'Avlidna %d'),
        'sw': lambda v: dh_yearAD(v, 'Waliofariki %d'),
        'szl': lambda v: dh_yearAD(v, 'Umarći we %d'),
        'ta': lambda v: dh_yearAD(v, '%d இறப்புகள்'),
        'te': lambda v: dh_yearAD(v, '%d మరణాలు'),
        'th': lambda v: dh_yearAD(v, 'บุคคลที่เสียชีวิตในปี พ.ศ. %T'),
        'tl': lambda v: dh_yearAD(v, 'Namatay noong %d'),
        'tr': lambda v: dh_yearAD(v, '%d yılında ölenler'),
        'tt': lambda v: dh_yearAD(v, '%d елда вафатлар'),
        'uk': lambda v: dh_yearAD(v, 'Померли %d'),
        'ur': lambda v: dh_yearAD(v, '%dء کی وفیات'),
        'vi': lambda v: dh_yearAD(v, 'Mất %d'),
        'war': lambda v: dh_yearAD(v, 'Mga namatay han %d'),
        'yo': lambda v: dh_yearAD(v, 'Àwọn ọjọ́aláìsí ní %d'),
        'zh': lambda v: dh_yearAD(v, '%d年逝世'),
        'yue': lambda v: dh_yearAD(v, '%d年死'),
    },

    'Cat_BirthsBC': {
        'en': lambda v: dh_yearBC(v, '%d BC births'),
        'nb': lambda v: dh_yearBC(v, 'Fødsler i %d f.Kr.'),
    },
    'Cat_DeathsBC': {
        'en': lambda v: dh_yearBC(v, '%d BC deaths'),
        'fr': lambda v: dh_yearBC(v, 'Décès en -%d'),
        'nb': lambda v: dh_yearBC(v, 'Dødsfall i %d f.Kr.'),
    },

    'CurrEvents': {
        'an': lambda v: dh_singVal(v, 'Autualidá'),
        'ang': lambda v: dh_singVal(v, 'Efenealde belimpas'),
        'ar': lambda v: dh_singVal(v, 'الأحداث الجارية'),
        'be': lambda v: dh_singVal(v, 'Бягучыя падзеі'),
        'bg': lambda v: dh_singVal(v, 'Текущи събития'),
        'ca': lambda v: dh_singVal(v, 'Viquipèdia:Actualitat'),
        'cs': lambda v: dh_singVal(v, 'Portál:Aktuality'),
        'da': lambda v: dh_singVal(v, 'Aktuelle begivenheder'),
        'de': lambda v: dh_singVal(v, 'Aktuelle Ereignisse'),
        'el': lambda v: dh_singVal(v, 'Τρέχοντα γεγονότα'),
        'en': lambda v: dh_singVal(v, 'Current events'),
        'eo': lambda v: dh_singVal(v, 'Aktualaĵoj'),
        'es': lambda v: dh_singVal(v, 'Actualidad'),
        'et': lambda v: dh_singVal(v, 'Current events'),
        'fa': lambda v: dh_singVal(v, 'رویدادهای کنونی'),
        'fi': lambda v: dh_singVal(v, 'Ajankohtaista'),
        'fr': lambda v: dh_singVal(v, 'Actualités'),
        'gl': lambda v: dh_singVal(v, 'Novas'),
        'he': lambda v: dh_singVal(v, 'אקטואליה'),
        'hu': lambda v: dh_singVal(v, 'Friss események'),
        'id': lambda v: dh_singVal(v, 'Wikipedia:Peristiwa terkini'),
        'io': lambda v: dh_singVal(v, 'Current events'),
        'it': lambda v: dh_singVal(v, 'Attualità'),
        'ja': lambda v: dh_singVal(v, '最近の出来事'),
        'ka': lambda v: dh_singVal(v, 'ახალი ამბები'),
        'ko': lambda v: dh_singVal(v, '요즘 화제'),
        'ksh': lambda v: dh_singVal(v, 'Et Neuste'),
        'ku': lambda v: dh_singVal(v, 'Bûyerên rojane'),
        'la': lambda v: dh_singVal(v, 'Nuntii'),
        'lb': lambda v: dh_singVal(v, 'Aktualitéit'),
        'li': lambda v: dh_singVal(v, "In 't nuujs"),
        'mn': lambda v: dh_singVal(v, 'Мэдээ'),
        'nl': lambda v: dh_singVal(v, 'In het nieuws'),
        'nb': lambda v: dh_singVal(v, 'Aktuelt'),
        'os': lambda v: dh_singVal(v, 'Xabar'),
        'pl': lambda v: dh_singVal(v, 'Bieżące wydarzenia'),
        'pt': lambda v: dh_singVal(v, 'Eventos atuais'),
        'ro': lambda v: dh_singVal(v, 'Actualităţi'),
        'ru': lambda v: dh_singVal(v, 'Текущие события'),
        'scn': lambda v: dh_singVal(v, 'Nutizzî'),
        'sk': lambda v: dh_singVal(v, 'Aktuality'),
        'sl': lambda v: dh_singVal(v, 'Trenutni dogodki'),
        'sr': lambda v: dh_singVal(v, 'Википедија:Актуелности'),
        'sv': lambda v: dh_singVal(v, 'Aktuella händelser'),
        'su': lambda v: dh_singVal(v, 'Keur lumangsung'),
        'ta': lambda v: dh_singVal(v, 'நடப்பு நிகழ்வுகள்'),
        'th': lambda v: dh_singVal(v, 'เหตุการณ์ปัจจุบัน'),
        'tl': lambda v: dh_singVal(v, 'Kasalukuyang pangyayari'),
        'tr': lambda v: dh_singVal(v, 'Güncel olaylar'),
        'uk': lambda v: dh_singVal(v, 'Поточні події'),
        'ur': lambda v: dh_singVal(v, 'حالیہ واقعات'),
        'vi': lambda v: dh_singVal(v, 'Thời sự'),
        'wa': lambda v: dh_singVal(v, 'Wikinoveles'),
        'yo': lambda v: dh_singVal(v, 'Current events'),
        'zh': lambda v: dh_singVal(v, '新闻动态'),
        'nan': lambda v: dh_singVal(v, 'Sin-bûn sū-kiāⁿ'),
    },
}

#
# Add auto-generated empty dictionaries for DayOfMonth and MonthOfYear articles
#
for dayOfMonth in dayMnthFmts:
    formats[dayOfMonth] = {}
for monthOfYear in yrMnthFmts:
    formats[monthOfYear] = {}


def addFmt1(lang, isMnthOfYear, patterns):
    """Add 12 month formats for a specific type ('January', 'Feb.').

    The function must accept one parameter for the ->int or ->string
    conversions, just like everywhere else in the formats map.
    The patterns parameter is a list of 12 elements to be used for each month.

    @param lang: language code
    @type lang: str
    """
    assert len(patterns) == 12, 'pattern %s does not have 12 elements' % lang

    for i in range(12):
        if patterns[i] is not None:
            if isMnthOfYear:
                formats[yrMnthFmts[i]][lang] = eval(
                    'lambda v: dh_mnthOfYear(v, "{}")'.format(patterns[i]))
            else:
                formats[dayMnthFmts[i]][lang] = eval(
                    'lambda v: dh_dayOfMnth(v, "{}")'.format(patterns[i]))


def addFmt2(lang, isMnthOfYear, pattern, makeUpperCase=None):
    """Update yrMnthFmts and dayMnthFmts using addFmt1."""
    addFmt1(lang, isMnthOfYear,
            makeMonthNamedList(lang, pattern, makeUpperCase))


def makeMonthList(pattern):
    """Return a list of 12 elements based on the number of the month."""
    return [pattern % m for m in range(1, 13)]


def makeMonthNamedList(lang, pattern, makeUpperCase=None):
    """Create a list of 12 elements based on the name of the month.

    The language-dependent month name is used as a formatting argument to the
    pattern. The pattern must be have one %s that will be replaced by the
    localized month name.
    Use %%d for any other parameters that should be preserved.

    """
    if makeUpperCase is None:
        return [pattern % monthName(lang, m) for m in range(1, 13)]
    elif makeUpperCase:
        f = first_upper
    else:
        f = first_lower
    return [pattern % f(monthName(lang, m)) for m in range(1, 13)]


# Add day of the month formats to the formatting table: "en:May 15"
addFmt2('af', False, '%%d %s', True)
addFmt2('gsw', False, '%%d. %s', True)
addFmt1('an', False, ['%d de chinero', '%d de frebero', '%d de marzo',
                      "%d d'abril", '%d de mayo', '%d de chunio',
                      '%d de chulio', "%d d'agosto", '%d de setiembre',
                      "%d d'otubre", '%d de nobiembre', "%d d'abiento"])
addFmt2('ang', False, '%%d %s', True)
addFmt1('ar', False, ['%d يناير', '%d فبراير', '%d مارس', '%d أبريل',
                      '%d مايو', '%d يونيو', '%d يوليو', '%d أغسطس',
                      '%d سبتمبر', '%d أكتوبر', '%d نوفمبر', '%d ديسمبر'])
addFmt1('ast', False, ['%d de xineru', '%d de febreru', '%d de marzu',
                       "%d d'abril", '%d de mayu', '%d de xunu',
                       '%d de xunetu', "%d d'agost", '%d de setiembre',
                       "%d d'ochobre", '%d de payares', "%d d'avientu"])
addFmt1('be', False, ['%d студзеня', '%d лютага', '%d сакавіка',
                      '%d красавіка', '%d траўня', '%d чэрвеня',
                      '%d ліпеня', '%d жніўня', '%d верасьня',
                      '%d кастрычніка', '%d лістапада', '%d сьнежня'])
addFmt2('bg', False, '%%d %s', False)
addFmt2('bn', False, '%s %%B')
addFmt2('bs', False, '%%d. %s', False)
addFmt1('ca', False, ['%d de gener', '%d de febrer', '%d de març',
                      "%d d'abril", '%d de maig', '%d de juny',
                      '%d de juliol', "%d d'agost", '%d de setembre',
                      "%d d'octubre", '%d de novembre', '%d de desembre'])
addFmt2('ceb', False, '%s %%d', True)
addFmt1('co', False, ['%d di ghjennaghju', '%d di frivaghju', '%d di marzu',
                      "%d d'aprile", '%d di maghju', '%d di ghjugnu',
                      '%d di lugliu', "%d d'aost", '%d di settembre',
                      "%d d'uttrovi", '%d di nuvembri', '%d di decembre'])
addFmt2('cs', False, '%%d. %s', False)
addFmt2('csb', False, '%%d %sa', False)
addFmt2('cv', False, '%s, %%d', True)
addFmt2('cy', False, '%%d %s', True)
addFmt2('da', False, '%%d. %s', False)
addFmt2('de', False, '%%d. %s', True)
addFmt1('el', False, ['%d Ιανουαρίου', '%d Φεβρουαρίου', '%d Μαρτίου',
                      '%d Απριλίου', '%d Μαΐου', '%d Ιουνίου', '%d Ιουλίου',
                      '%d Αυγούστου', '%d Σεπτεμβρίου', '%d Οκτωβρίου',
                      '%d Νοεμβρίου', '%d Δεκεμβρίου'])
addFmt2('en', False, '%s %%d', True)
addFmt2('eo', False, '%%d-a de %s', False)
addFmt2('es', False, '%%d de %s', False)
addFmt2('et', False, '%%d. %s', False)
addFmt2('eu', False, '%saren %%d', True)
addFmt1('fa', False, ['%d ژانویه', '%d فوریه', '%d مارس', '%d آوریل',
                      '%d مه', '%d ژوئن', '%d ژوئیه', '%d اوت',
                      '%d سپتامبر', '%d اکتبر', '%d نوامبر', '%d دسامبر'])
addFmt2('fi', False, '%%d. %sta', False)
addFmt2('fo', False, '%%d. %s', False)
addFmt1('fr', False, ['%d janvier', '%d février', '%d mars', '%d avril',
                      '%d mai', '%d juin', '%d juillet', '%d août',
                      '%d septembre', '%d octobre', '%d novembre',
                      '%d décembre'])
addFmt2('fur', False, '%%d di %s', True)
addFmt2('fy', False, '%%d %s', False)
addFmt1('ga', False, ['%d Eanáir', '%d Feabhra', '%d Márta', '%d Aibreán',
                      '%d Bealtaine', '%d Meitheamh', '%d Iúil', '%d Lúnasa',
                      '%d Meán Fómhair', '%d Deireadh Fómhair', '%d Samhain',
                      '%d Mí na Nollag'])
addFmt2('gl', False, '%%d de %s', False)
addFmt2('he', False, '%%d ב%s')
addFmt1('hr', False, ['%d. siječnja', '%d. veljače', '%d. ožujka',
                      '%d. travnja', '%d. svibnja', '%d. lipnja', '%d. srpnja',
                      '%d. kolovoza', '%d. rujna', '%d. listopada',
                      '%d. studenog', '%d. prosinca'])
addFmt2('hu', False, '%s %%d.', True)
addFmt2('ia', False, '%%d de %s', False)
addFmt2('id', False, '%%d %s', True)
addFmt2('ie', False, '%%d %s', False)
addFmt2('io', False, '%%d di %s', False)
addFmt1('is', False, ['%d. janúar', '%d. febrúar', '%d. mars', '%d. apríl',
                      '%d. maí', '%d. júní', '%d. júlí', '%d. ágúst',
                      '%d. september', '%d. október', '%d. nóvember',
                      '%d. desember'])
addFmt2('it', False, '%%d %s', False)
addFmt1('ja', False, makeMonthList('%d月%%d日'))
addFmt2('jv', False, '%%d %s', True)
addFmt2('ka', False, '%%d %s')
addFmt1('ko', False, makeMonthList('%d월 %%d일'))
addFmt1('ku', False, ["%d'ê rêbendanê", "%d'ê reşemiyê", "%d'ê adarê",
                      "%d'ê avrêlê", "%d'ê gulanê", "%d'ê pûşperê",
                      "%d'ê tîrmehê", "%d'ê gelawêjê", "%d'ê rezberê",
                      "%d'ê kewçêrê", "%d'ê sermawezê", "%d'ê berfanbarê"])
addFmt1('la', False, ['%d Ianuarii', '%d Februarii', '%d Martii', '%d Aprilis',
                      '%d Maii', '%d Iunii', '%d Iulii', '%d Augusti',
                      '%d Septembris', '%d Octobris', '%d Novembris',
                      '%d Decembris'])
addFmt2('lb', False, '%%d. %s', True)
addFmt1('li', False, ['%d januari', '%d februari', '%d miert', '%d april',
                      '%d mei', '%d juni', '%d juli', '%d augustus',
                      '%d september', '%d oktober', '%d november',
                      '%d december'])
addFmt1('lt', False, ['Sausio %d', 'Vasario %d', 'Kovo %d', 'Balandžio %d',
                      'Gegužės %d', 'Birželio %d', 'Liepos %d', 'Rugpjūčio %d',
                      'Rugsėjo %d', 'Spalio %d', 'Lapkričio %d',
                      'Gruodžio %d'])
addFmt2('lv', False, '%%d. %s', False)
addFmt2('mhr', False, '%%d %s', False)
addFmt1('mk', False, ['%d јануари', '%d февруари', '%d март', '%d април',
                      '%d мај', '%d јуни', '%d јули', '%d август',
                      '%d септември', '%d октомври', '%d ноември',
                      '%d декември'])
addFmt2('ml', False, '%s %%d')
addFmt2('ms', False, '%%d %s', True)
addFmt2('nap', False, "%%d 'e %s", False)
addFmt2('nds', False, '%%d. %s', True)
addFmt1('nl', False, ['%%d %s' % v
                      for v in ['januari', 'februari', 'maart', 'april', 'mei',
                                'juni', 'juli', 'augustus', 'september',
                                'oktober', 'november', 'december']])
addFmt1('nn', False, ['%%d. %s' % v
                      for v in ['januar', 'februar', 'mars', 'april',
                                'mai', 'juni', 'juli', 'august', 'september',
                                'oktober', 'november', 'desember']])
addFmt2('nb', False, '%%d. %s', False)
addFmt1('oc', False, ['%d de genièr', '%d de febrièr', '%d de març',
                      "%d d'abril", '%d de mai', '%d de junh', '%d de julhet',
                      "%d d'agost", '%d de setembre', "%d d'octobre",
                      '%d de novembre', '%d de decembre'])
addFmt1('os', False, ['%d январы', '%d февралы', '%d мартъийы', '%d апрелы',
                      '%d майы', None, '%d июлы', None, '%d сентябры', None,
                      '%d ноябры', '%d декабры'])
addFmt1('pl', False, ['%d stycznia', '%d lutego', '%d marca', '%d kwietnia',
                      '%d maja', '%d czerwca', '%d lipca', '%d sierpnia',
                      '%d września', '%d października', '%d listopada',
                      '%d grudnia'])
addFmt2('pt', False, '%%d de %s', True)
addFmt2('ro', False, '%%d %s', False)
addFmt1('ru', False, ['%d января', '%d февраля', '%d марта', '%d апреля',
                      '%d мая', '%d июня', '%d июля', '%d августа',
                      '%d сентября', '%d октября', '%d ноября', '%d декабря'])
addFmt2('sco', False, '%%d %s', True)
addFmt2('scn', False, '%%d di %s', False)
addFmt1('se', False, ['ođđajagimánu %d.', 'guovvamánu %d.', 'njukčamánu %d.',
                      'cuoŋománu %d.', 'miessemánu %d.', 'geassemánu %d.',
                      'suoidnemánu %d.', 'borgemánu %d.', 'čakčamánu %d.',
                      'golggotmánu %d.', 'skábmamánu %d.', 'juovlamánu %d.'])
addFmt1('sh', False, makeMonthList('%%d.%d.'))
addFmt2('sk', False, '%%d. %s', False)
addFmt2('sl', False, '%%d. %s', False)
addFmt1('sq', False, ['%d Janar', '%d Shkurt', '%d Mars', '%d Prill', '%d Maj',
                      '%d Qershor', '%d Korrik', '%d Gusht', '%d Shtator',
                      '%d Tetor', '%d Nëntor', '%d Dhjetor'])
addFmt2('sr', False, '%%d. %s', False)
addFmt2('su', False, '%%d %s', True)
addFmt2('sv', False, '%%d %s', False)
addFmt2('ta', False, '%s %%d')
addFmt2('te', False, '%s %%d')
addFmt2('th', False, '%%d %s')  # %%T
addFmt2('tl', False, '%s %%d')
addFmt2('tr', False, '%%d %s', True)
addFmt2('tt', False, '%%d. %s', True)
addFmt1('uk', False, ['%d січня', '%d лютого', '%d березня', '%d квітня',
                      '%d травня', '%d червня', '%d липня', '%d серпня',
                      '%d вересня', '%d жовтня', '%d листопада', '%d грудня'])
addFmt1('ur', False, ['%d جنوری', '%d فروری', '%d مارچ',
                      '%d اپریل', '%d مئی', '%d جون', '%d جولائی',
                      '%d اگست', '%d ستمبر', '%d اکتوبر',
                      '%d نومبر', '%d دسمبر'])
addFmt2('vec', False, '%%d de %s', False)
addFmt1('vi', False, makeMonthList('%%d tháng %d'))
addFmt2('vo', False, '%s %%d', False)
addFmt1('zh', False, makeMonthList('%d月%%d日'))

# Walloon names depend on the day number, thus we must generate various
# different patterns
waMonthNames = ['djanvî', 'fevrî', 'måss', 'avri', 'may', 'djun', 'djulete',
                'awousse', 'setimbe', 'octôbe', 'nôvimbe', 'decimbe']

# For month names beginning with a consonant...
for i in (0, 1, 2, 4, 5, 6, 8, 10, 11):
    formats[dayMnthFmts[i]]['wa'] = eval(
        'lambda m: multi(m, ['
        '(lambda v: dh_dayOfMnth(v, "%%dî d\' %s"), lambda p: p == 1), '
        '(lambda v: dh_dayOfMnth(v, "%%d d\' %s"), '
        'lambda p: p in [2,3,20,22,23]), '
        '(lambda v: dh_dayOfMnth(v, "%%d di %s"), alwaysTrue)])'
        % (waMonthNames[i], waMonthNames[i], waMonthNames[i]))

# For month names beginning with a vowel...
for i in (3, 7, 9):
    formats[dayMnthFmts[i]]['wa'] = eval(
        'lambda m: multi(m, ['
        '(lambda v: dh_dayOfMnth(v, "%%dî d\' %s"), lambda p: p == 1), '
        '(lambda v: dh_dayOfMnth(v, "%%d d\' %s"), alwaysTrue)])'
        % (waMonthNames[i], waMonthNames[i]))

# Brazil uses '1añ' for the 1st of every month, and number without suffix for
# all other days
brMonthNames = makeMonthNamedList('br', '%s', True)
for i in range(0, 12):
    formats[dayMnthFmts[i]]['br'] = eval(
        'lambda m: multi(m, ['
        '(lambda v: dh_dayOfMnth(v, "%%dañ %s"), lambda p: p == 1), '
        '(lambda v: dh_dayOfMnth(v, "%%d %s"), alwaysTrue)])'
        % (brMonthNames[i], brMonthNames[i]))

#
# Month of the Year: "en:May 1976"
#
addFmt2('af', True, '%s %%d', True)
addFmt2('ar', True, '%s %%d')
addFmt2('ang', True, '%s %%d', True)
addFmt2('cs', True, '%s %%d')
addFmt2('de', True, '%s %%d', True)
addFmt1('el', True, ['Ιανουάριος %d', 'Φεβρουάριος %d', 'Μάρτιος %d',
                     'Απρίλιος %d', 'Μάιος %d', 'Ιούνιος %d', 'Ιούλιος %d',
                     'Άυγουστος %d', 'Σεπτέμβριος %d', 'Οκτώβριος %d',
                     'Νοέμβριος %d', 'Δεκέμβριος %d'])
addFmt2('en', True, '%s %%d', True)
addFmt2('eo', True, '%s de %%d')
addFmt2('es', True, '%s de %%d', True)
addFmt2('et', True, '%s %%d', True)
addFmt2('fi', True, '%s %%d', True)
addFmt1('fr', True, ['Janvier %d', 'Février %d', 'Mars %d', 'Avril %d',
                     'Mai %d', 'Juin %d', 'Juillet %d', 'Août %d',
                     'Septembre %d', 'Octobre %d', 'Novembre %d',
                     'Décembre %d'])
addFmt2('he', True, '%s %%d', True)
addFmt2('it', True, 'Attualità/Anno %%d - %s', True)
addFmt1('ja', True, ['「最近の出来事」%%d年%d月' % mm for mm in range(1, 13)])
addFmt2('ka', True, '%s, %%d')
addFmt1('ko', True, ['%d년 1월', '%d년 2월', '%d년 3월', '%d년 4월', '%d년 5월',
                     '%d년 6월', '%d년 7월', '%d년 8월', '%d년 9월', '%d년 10월',
                     '%d년 11월', '%d년 12월'])
addFmt1('li', True, ['januari %d', 'februari %d', 'miert %d', 'april %d',
                     'mei %d', 'juni %d', 'juli %d', 'augustus %d',
                     'september %d', 'oktober %d', 'november %d',
                     'december %d'])
addFmt1('nl', True, ['Januari %d', 'Februari %d', 'Maart %d', 'April %d',
                     'Mei %d', 'Juni %d', 'Juli %d', 'Augustus %d',
                     'September %d', 'Oktober %d', 'November %d',
                     'December %d'])
addFmt2('pl', True, '%s %%d', True)
addFmt1('scn', True, [None, None, 'Marzu %d', None, None, None, None, None,
                      None, None, None, None])
addFmt2('sk', True, '%s %%d')
addFmt2('sv', True, '%s %%d', True)
addFmt2('th', True, '%s พ.ศ. %%T')
addFmt2('tl', True, '%s %%d')
addFmt2('tt', True, '%s, %%d', True)
addFmt2('uk', True, '%s %%d', True)
addFmt2('ur', True, '%s %%d', True)
addFmt1('vi', True, makeMonthList('Tháng %d năm %%d'))
addFmt1('zh', True, makeMonthList('%%d年%d月'))
addFmt1('nan', True, makeMonthList('%%d nî %d goe̍h'))


# This table defines the limits for each type of format data.
# Each item is a tuple with
# - a predicate function which returns True if the value falls
#   within acceptable limits, False otherwise,
# - start value
# - end value
#
# TODO: Before compat 19d1cf9e (2006), there was a 'step' in the tuple,
# used exclusively by DecadeAD and DecadeBC to increment by 10 years.
# "and v%10==0" should be added to the limitation predicate for those two.
formatLimits = {
    'MonthName': (lambda v: 1 <= v and v < 13, 1, 13),
    'Number': (lambda v: 0 <= v and v < 1000000, 0, 1001),
    'YearAD': (lambda v: 0 <= v and v < 2501, 0, 2501),
    # zh: has years as old as 前1700年
    'YearBC': (lambda v: 0 <= v and v < 4001, 0, 501),
    'DecadeAD': (lambda v: 0 <= v and v < 2501, 0, 2501),
    # zh: has decades as old as 前1700年代
    'DecadeBC': (lambda v: 0 <= v and v < 4001, 0, 501),

    # Some centuries use Roman numerals or a given list
    # do not exceed them in testing
    'CenturyAD': (lambda v: 1 <= v and v < 41, 1, 23),
    'CenturyBC': (lambda v: 1 <= v and v < 91, 1, 23),
    'CenturyAD_Cat': (lambda v: 1 <= v and v < 41, 1, 23),
    'CenturyBC_Cat': (lambda v: 1 <= v and v < 41, 1, 23),

    # For millenniums, only test first 3 AD Millenniums and 1 BC Millennium
    'MillenniumAD': (lambda v: 1 <= v and v < 6, 1, 4),
    'MillenniumBC': (lambda v: 1 <= v and v < 20, 1, 2),

    'Cat_Year_MusicAlbums': (lambda v: 1950 <= v and v < 2021, 1950, 2021),
    'Cat_BirthsAD': (lambda v: 0 <= v and v < 2501, 0, 2501),
    'Cat_DeathsAD': (lambda v: 0 <= v and v < 2501, 0, 2501),
    'Cat_BirthsBC': (lambda v: 0 <= v and v < 4001, 0, 501),
    'Cat_DeathsBC': (lambda v: 0 <= v and v < 4001, 0, 501),
    'CurrEvents': (lambda v: 0 <= v and v < 1, 0, 1),
}

# All month of year articles are in the same format
_formatLimit_MonthOfYear = (lambda v: 1 <= 1900 and v < 2051, 1900, 2051)
for month in yrMnthFmts:
    formatLimits[month] = _formatLimit_MonthOfYear

_formatLimit_DayOfMonth31 = (lambda v: 1 <= v and v < 32, 1, 32)
_formatLimit_DayOfMonth30 = (lambda v: 1 <= v and v < 31, 1, 31)
_formatLimit_DayOfMonth29 = (lambda v: 1 <= v and v < 30, 1, 30)
for monthId in range(12):
    if (monthId + 1) in (1, 3, 5, 7, 8, 10, 12):
        # 31 days a month
        formatLimits[dayMnthFmts[monthId]] = _formatLimit_DayOfMonth31
    elif (monthId + 1) == 2:  # February
        # 29 days a month
        formatLimits[dayMnthFmts[monthId]] = _formatLimit_DayOfMonth29
    else:
        # 30 days a month
        formatLimits[dayMnthFmts[monthId]] = _formatLimit_DayOfMonth30


@deprecated('calendar.monthrange', since='20150707')
def getNumberOfDaysInMonth(month):
    """
    Return the maximum number of days in a given month, 1 being January, etc.

    For February always 29 will be given, even it is not a leap year.
    """
    # use year 2000 which is a leap year
    return calendar.monthrange(2000, month)[1]


def getAutoFormat(lang, title, ignoreFirstLetterCase=True):
    """
    Return first matching formatted date value.

    @param lang: language code
    @param title: value to format
    @return: dictName ('YearBC', 'December', ...) and value (a year, date, ...)
    @rtype: tuple
    """
    for dictName, dict in formats.items():
        try:
            year = dict[lang](title)
            return dictName, year
        except Exception:
            pass
    # sometimes the title may begin with an upper case while its listed as
    # lower case, or the other way around
    # change case of the first character to the opposite, and try again
    if ignoreFirstLetterCase:
        try:
            if title[0].isupper():
                title = first_lower(title)
            else:
                title = first_upper(title)
            return getAutoFormat(lang, title, ignoreFirstLetterCase=False)
        except Exception:
            pass
    return None, None


class FormatDate(object):

    """Format a date."""

    def __init__(self, site):
        """Initializer."""
        self.site = site

    def __call__(self, m, d):
        """Return a formatted month and day."""
        return formats['Day_' + enMonthNames[m - 1]][self.site.lang](d)


def formatYear(lang, year):
    """Return year name in a language."""
    if year < 0:
        return formats['YearBC'][lang](-year)
    else:
        return formats['YearAD'][lang](year)


def apply_month_delta(date, month_delta=1, add_overlap=False):
    """
    Add or subtract months from the date.

    By default if the new month has less days then the day of the date it
    chooses the last day in the new month. For example a date in the March 31st
    added by one month will result in April 30th.

    When the overlap is enabled, and there is overlap, then the new_date will
    be one month off and get_month_delta will report a number one higher.

    It does only work on calendars with 12 months per year, and where the
    months are numbered consecutively beginning by 1.

    @param date: The starting date
    @type date: date
    @param month_delta: The amount of months added or subtracted.
    @type month_delta: int
    @param add_overlap: Add any missing days to the date, increasing the month
        once more.
    @type add_overlap: bool
    @return: The end date
    @rtype: type of date
    """
    if int(month_delta) != month_delta:
        raise ValueError('Month delta must be an integer')
    month = (date.month - 1) + month_delta
    year = date.year + month // 12
    month = month % 12 + 1
    day = min(date.day, calendar.monthrange(year, month)[1])
    new_date = date.replace(year, month, day)
    if add_overlap and day != date.day:
        assert date.day > day, 'Day must not be more than length of the month'
        new_date += datetime.timedelta(days=date.day - day)
    return new_date


def get_month_delta(date1, date2):
    """
    Return the difference between to dates in months.

    It does only work on calendars with 12 months per year, and where the
    months are consecutive and non-negative numbers.
    """
    return date2.month - date1.month + (date2.year - date1.year) * 12
