# -*- coding: utf-8  -*-
"""
This file is not runnable, but it only consists of various
lists which are required by some other programs.
"""
#
# © Rob W.W. Hooft, 2003
# © Daniel Herding, 2004
# © Ævar Arnfjörð Bjarmason, 2004
# © Andre Engels, 2004-2005
# © Yuri Astrakhan, 2005-2006  FirstnameLastname@gmail.com
#       (years/decades/centuries/millenniums  str <=> int  conversions)
# © Pywikipedia bot team, 2004-2011
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

# used for date recognition
import types
import re

#
# Different collections of well known formats
#
enMonthNames    = [u'January', u'February', u'March', u'April', u'May', u'June',
                   u'July', u'August', u'September', u'October', u'November',
                   u'December']
dayMnthFmts     = ['Day_' + str(s) for s in enMonthNames]  # e.g. 'Day_January'
yrMnthFmts      = ['Year_' + str(s) for s in enMonthNames] # e.g. 'Year_January'


# the order of these lists is important
adDateFormats   = ['YearAD', 'DecadeAD', 'CenturyAD', 'MillenniumAD']
bcDateFormats   = ['YearBC', 'DecadeBC', 'CenturyBC', 'MillenniumBC']

dateFormats     = bcDateFormats + adDateFormats
decadeFormats   = ['DecadeAD', 'DecadeBC']
centuryFormats  = ['CenturyAD', 'CenturyBC']
yearFormats     = ['YearAD', 'YearBC']
millFormats     = ['MillenniumAD', 'MillenniumBC']
snglValsFormats = ['CurrEvents']

def multi( value, tuplst ):
    """This method is used when more than one pattern is used for the same
    entry. Example: 1st century, 2nd century, etc.
    The tuplst is a list of tupples. Each tupple must contain two functions:
    first to encode/decode a single value (e.g. simpleInt), second is a
    predicate function with an integer parameter that returns true or false.
    When the 2nd function evaluates to true, the 1st function is used.

    """
    if type(value) in _stringTypes:
        # Try all functions, and test result against predicates
        for func, pred in tuplst:
            try:
                res = func(value)
                if pred(res):
                    return res
            except:
                pass
    else:
        # Find a predicate that gives true for this int value, and run a
        # function
        for func, pred in tuplst:
            if pred(value):
                return func(value)

    raise ValueError("could not find a matching function")

#
# Helper functions that aid with single value no corrections encoding/decoding.
# Various filters are item dependent.
#
def dh_noConv(value, pattern, limit):
    """decoding helper for a single integer value, no conversion, no rounding"""
    return dh( value, pattern, encNoConv, decSinglVal, limit )

def dh_dayOfMnth(value, pattern):
    """decoding helper for a single integer value <=31, no conversion,
    no rounding (used in days of month)

    """
    # For now use January because it has all 31 days
    return dh_noConv(value, pattern, formatLimits[dayMnthFmts[0]][0])

def dh_mnthOfYear(value, pattern):
    """decoding helper for a single integer value >=1000, no conversion,
    no rounding (used in month of the year)

    """
    return dh_noConv(value, pattern, _formatLimit_MonthOfYear[0])

def dh_decAD(value, pattern):
    """decoding helper for a single integer value, no conversion,
    round to decimals (used in decades)

    """
    return dh(value, pattern, encDec0, decSinglVal, formatLimits['DecadeAD'][0])

def dh_decBC(value, pattern):
    """decoding helper for a single integer value, no conversion,
    round to decimals (used in decades)

    """
    return dh(value, pattern, encDec0, decSinglVal, formatLimits['DecadeBC'][0])

def dh_yearBC(value, pattern):
    """decoding helper for a year value, no conversion, no rounding,
    limits to 3000

    """
    return dh_noConv(value, pattern, formatLimits['YearBC'][0])

def dh_yearAD(value, pattern):
    """decoding helper for a year value, no conversion, no rounding,
    limits to 3000

    """
    return dh_noConv(value, pattern, formatLimits['YearAD'][0])

def dh_simpleYearAD(value):
    """decoding helper for a single integer value representing a year with
    no extra symbols

    """
    return dh_yearAD(value, u'%d')

def dh_number(value, pattern):
    return dh_noConv(value, pattern, formatLimits['Number'][0])
def dh_centuryAD(value, pattern):
    return dh_noConv(value, pattern, formatLimits['CenturyAD'][0])
def dh_centuryBC(value, pattern):
    return dh_noConv(value, pattern, formatLimits['CenturyBC'][0])
def dh_millenniumAD(value, pattern):
    return dh_noConv(value, pattern, formatLimits['MillenniumAD'][0])
def dh_millenniumBC(value, pattern):
    return dh_noConv(value, pattern, formatLimits['MillenniumBC'][0])

def decSinglVal(v):
    return v[0]

def encNoConv(i):
    return i

def encDec0(i):
    # round to the nearest decade, decade starts with a '0'-ending year
    return (i/10)*10

def encDec1(i):
    # round to the nearest decade, decade starts with a '1'-ending year
    return encDec0(i)+1

def slh( value, lst ):
    """This function helps in simple list value matching.

    !!!!! The index starts at 1, so 1st element has index 1, not 0 !!!!!
        Usually it will be used as a lambda call in a map:
            lambda v: slh( v, [u'January',u'February',...] )

        Usage scenarios:
            formats['MonthName']['en'](1) => u'January'
            formats['MonthName']['en'](u'January') => 1
            formats['MonthName']['en'](u'anything else') => raise ValueError

    """
    if type(value) in _stringTypes:
        return lst.index(value)+1
    else:
        return lst[value-1]

def dh_singVal( value, match ):
    return dh_constVal( value, 0, match )

def dh_constVal( value, ind, match ):
    """This function helps with matching a single value to a constant.

    formats['CurrEvents']['en'](ind) => u'Current Events'
    formats['CurrEvents']['en'](u'Current Events') => ind

    """
    if type(value) in _stringTypes:
        if value == match:
            return ind
        else:
            raise ValueError()
    else:
        if value == ind:
            return match
        else:
            raise ValueError("unknown value %d" % value)

def alwaysTrue( x ):
    """This function always returns True - its used for multiple value selection function
    to accept all other values

    """
    return True

def monthName(lang, ind):
    return formats['MonthName'][lang](ind)


# Helper for KN: digits representation
_knDigits = u'೦೧೨೩೪೫೬೭೮೯'
_knDigitsToLocal = dict([(ord(unicode(i)), _knDigits[i]) for i in range(10)])
_knLocalToDigits = dict([(ord(_knDigits[i]), unicode(i)) for i in range(10)])

# Helper for Urdu/Persian languages
_faDigits = u'۰۱۲۳۴۵۶۷۸۹'
_faDigitsToLocal = dict([(ord(unicode(i)), _faDigits[i]) for i in range(10)])
_faLocalToDigits = dict([(ord(_faDigits[i]), unicode(i)) for i in range(10)])

# Helper for HI:, MR:
_hiDigits = u'०१२३४५६७८९'
_hiDigitsToLocal = dict([(ord(unicode(i)), _hiDigits[i]) for i in range(10)])
_hiLocalToDigits = dict([(ord(_hiDigits[i]), unicode(i)) for i in range(10)])

# Helper for BN:
_bnDigits = u'০১২৩৪৫৬৭৮৯'
_bnDigitsToLocal = dict([(ord(unicode(i)), _bnDigits[i]) for i in range(10)])
_bnLocalToDigits = dict([(ord(_bnDigits[i]), unicode(i)) for i in range(10)])

# Helper for GU:
_guDigits = u'૦૧૨૩૪૫૬૭૮૯'
_guDigitsToLocal = dict([(ord(unicode(i)), _guDigits[i]) for i in range(10)])
_guLocalToDigits = dict([(ord(_guDigits[i]), unicode(i)) for i in range(10)])

def intToLocalDigitsStr( value, digitsToLocalDict ):
    # Encode an integer value into a textual form.
    return unicode(value).translate(digitsToLocalDict)

def localDigitsStrToInt( value, digitsToLocalDict, localToDigitsDict ):
    # First make sure there are no real digits in the string
    tmp = value.translate(digitsToLocalDict)         # Test
    if tmp == value:
        return int(value.translate(localToDigitsDict))    # Convert
    else:
        raise ValueError("string contains regular digits")

# Decimal digits used for various matchings
_decimalDigits = '0123456789'

# Helper for roman numerals number representation
_romanNumbers = ['-', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX',
                 'X', 'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII',
                 'XIX', 'XX', 'XXI', 'XXII', 'XXIII', 'XXIV', 'XXV', 'XXVI',
                 'XXVII', 'XXVIII', 'XXIX', 'XXX']

def intToRomanNum(i):
    if i >= len(_romanNumbers):
        raise IndexError(u'Roman value %i is not defined' % i)
    return _romanNumbers[i]

def romanNumToInt(v):
    return _romanNumbers.index(v)

# Each tuple must 3 parts:  a list of all possible digits (symbols), encoder
# (from int to a u-string) and decoder (from u-string to an int)
_digitDecoders = {
    # %% is a %
    '%' : u'%',
    # %d is a decimal
    'd' : ( _decimalDigits, unicode, int ),
    # %R is a roman numeral. This allows for only the simpliest linear
    # conversions based on a list of numbers
    'R' : ( u'IVX', intToRomanNum, romanNumToInt ),
    # %K is a number in KN::
    'K' : ( _knDigits, lambda v: intToLocalDigitsStr(v, _knDigitsToLocal), lambda v: localDigitsStrToInt(v, _knDigitsToLocal, _knLocalToDigits) ),
    # %F is a number in FA:
    'F' : ( _faDigits, lambda v: intToLocalDigitsStr(v, _faDigitsToLocal), lambda v: localDigitsStrToInt(v, _faDigitsToLocal, _faLocalToDigits) ),
    # %H is a number in HI:
    'H' : ( _hiDigits, lambda v: intToLocalDigitsStr(v, _hiDigitsToLocal), lambda v: localDigitsStrToInt(v, _hiDigitsToLocal, _hiLocalToDigits) ),
    # %B is a number in BN:
    'B' : ( _bnDigits, lambda v: intToLocalDigitsStr(v, _bnDigitsToLocal), lambda v: localDigitsStrToInt(v, _bnDigitsToLocal, _bnLocalToDigits) ),
    # %G is a number in GU:
    'G' : ( _guDigits, lambda v: intToLocalDigitsStr(v, _guDigitsToLocal), lambda v: localDigitsStrToInt(v, _guDigitsToLocal, _guLocalToDigits) ),
    # %T is a year in TH: -- all years are shifted: 2005 => 'พ.ศ. 2548'
    'T' : ( _decimalDigits, lambda v: unicode(v+543), lambda v: int(v)-543 ),
}

# Allows to search for '(%%)|(%d)|(%R)|...", and allows one digit 1-9 to set
# the size of zero-padding for numbers
_reParameters = re.compile(u'|'.join( u'(%%[1-9]?%s)' % s for s in _digitDecoders ))

# A map of   sitecode+pattern  to  (re matching object and corresponding
# decoders)
_escPtrnCache2 = {}

# Allow both unicode and single-byte strings
_stringTypes = [unicode, str]
_listTypes = [list, tuple]

def escapePattern2( pattern ):
    """Converts a string pattern into a regex expression and cache.
    Allows matching of any _digitDecoders inside the string.
    Returns a compiled regex object and a list of digit decoders

    """

    if pattern not in _escPtrnCache2:
        newPattern = u'^' # begining of the string
        strPattern = u''
        decoders = []
        for s in _reParameters.split(pattern):
            if s is None:
                pass
            elif len(s) in [2, 3] and s[0] == '%' and s[-1] in _digitDecoders and (len(s) == 2 or s[1] in _decimalDigits):
                # Must match a "%2d" or "%d" style
                dec = _digitDecoders[s[-1]]
                if type(dec) in _stringTypes:
                    # Special case for strings that are replaced instead of decoded
                    if len(s) == 3: raise AssertionError("Invalid pattern %s: Cannot use zero padding size in %s!" % (pattern, s))
                    newPattern += re.escape( dec )
                    strPattern += s         # Keep the original text
                else:
                    if len(s) == 3:
                        # enforce mandatory field size
                        newPattern += u'([%s]{%s})' % (dec[0], s[1])
                        # add the number of required digits as the last (4th) part of the tuple
                        dec += (int(s[1]),)
                    else:
                        newPattern += u'([%s]+)' % dec[0]

                    decoders.append( dec )
                    # All encoders produce a string
                    # this causes problem with the zero padding.
                    # Need to rethink
                    strPattern += u'%s'
            else:
                newPattern += re.escape( s )
                strPattern += s

        newPattern += u'$' # end of the string
        compiledPattern = re.compile( newPattern )
        _escPtrnCache2[pattern] = (compiledPattern, strPattern, decoders)

    return _escPtrnCache2[pattern]


def dh( value, pattern, encf, decf, filter = None ):
    """This function helps in year parsing.

    Usually it will be used as a lambda call in a map:
        lambda v: dh( v, u'pattern string', encodingFunc, decodingFunc )

    encodingFunc:
        Converts from an integer parameter to another integer or a tuple of
        integers. Depending on the pattern, each integer will be converted to a
        proper string representation, and will be passed as a format argument
        to the pattern:
                    pattern % encodingFunc(value)
        This function is a complement of decodingFunc.

    decodingFunc:
        Converts a tuple/list of non-negative integers found in the original
        value string
        into a normalized value. The normalized value can be passed right back
        into dh() to produce the original string. This function is a complement
        of encodingFunc. dh() interprets %d as a decimal and %s as a roman
        numeral number.

    """

    compPattern, strPattern, decoders = escapePattern2(pattern)
    if type(value) in _stringTypes:
        m = compPattern.match(value)
        if m:
            # decode each found value using provided decoder
            values = [ decoders[i][2](m.group(i+1)) for i in range(len(decoders))]
            decValue = decf( values )

            if decValue in _stringTypes:
                raise AssertionError("Decoder must not return a string!")

            # recursive call to re-encode and see if we get the original (may through filter exception)
            if value == dh(decValue, pattern, encf, decf, filter):
                return decValue

        raise ValueError("reverse encoding didn't match")
    else:
        # Encode an integer value into a textual form.
        # This will be called from outside as well as recursivelly to verify parsed value
        if filter and not filter(value):
            raise ValueError("value %i is not allowed" % value)

        params = encf(value)

        if type(params) in _listTypes:
            if len(params) != len(decoders):
                raise AssertionError("parameter count (%d) does not match decoder count (%d)" % (len(params), len(decoders)))
            # convert integer parameters into their textual representation
            params = [ MakeParameter(decoders[i], params[i]) for i in range(len(params)) ]
            return strPattern % tuple(params)
        else:
            if 1 != len(decoders):
                raise AssertionError("A single parameter does not match %d decoders." % len(decoders))
            # convert integer parameter into its textual representation
            return strPattern % MakeParameter(decoders[0], params)

def MakeParameter(decoder, param):
    newValue = decoder[1](param)
    if len(decoder) == 4 and len(newValue) < decoder[3]:
        # force parameter length by taking the first digit in the list and repeating it required number of times
        # This converts "205" into "0205" for "%4d"
        newValue = decoder[0][0] * (decoder[3]-len(newValue)) + newValue
    return newValue

#
# All years/decades/centuries/millenniums are designed in such a way
# as to allow for easy date to string and string to date conversion.
# For example, using any map with either an integer or a string will produce its oposite value:
#        Usage scenarios:
#            formats['DecadeAD']['en'](1980) => u'1980s'
#            formats['DecadeAD']['en'](u'1980s') => 1980
#            formats['DecadeAD']['en'](u'anything else') => raise ValueError (or some other exception?)
# This is useful when trying to decide if a certain article is a localized date or not, or generating dates.
# See dh() for additional information.
#
#
#          ***********   ATTENTION! ***********
#
#   You must test this table before submitting it to CVS by calling     date.test()  method
#
formats = {
    'MonthName': {
        'af' :      lambda v: slh( v, [u"Januarie", u"Februarie", u"Maart", u"April", u"Mei", u"Junie", u"Julie", u"Augustus", u"September", u"Oktober", u"November", u"Desember"] ),
        'als':      lambda v: slh( v, [u"Januar", u"Februar", u"März", u"April", u"Mai", u"Juni", u"Juli", u"August", u"September", u"Oktober", u"November", u"Dezember"] ),
        'an' :      lambda v: slh( v, [u"chinero", u"frebero", u"marzo", u"abril", u"mayo", u"chunio", u"chulio", u"agosto", u"setiembre", u"otubre", u"nobiembre", u"abiento"] ),
        'ang':      lambda v: slh( v, [u"Æfterra Gēola", u"Solmōnaþ", u"Hrēþmōnaþ", u"Ēastermōnaþ", u"Þrimilcemōnaþ", u"Sēremōnaþ", u"Mǣdmōnaþ", u"Wēodmōnaþ", u"Hāligmōnaþ", u"Winterfylleþ", u"Blōtmōnaþ", u"Gēolmōnaþ"] ),
        'ar' :      lambda v: slh( v, [u"يناير", u"فبراير", u"مارس", u"أبريل", u"مايو", u"يونيو", u"يوليو", u"أغسطس", u"سبتمبر", u"أكتوبر", u"نوفمبر", u"ديسمبر"] ),
        'ast':      lambda v: slh( v, [u"xineru", u"febreru", u"marzu", u"abril", u"mayu", u"xunu", u"xunetu", u"agostu", u"setiembre", u"ochobre", u"payares", u"avientu"] ),
        'be' :      lambda v: slh( v, [u"студзень", u"люты", u"сакавік", u"красавік", u"травень", u"чэрвень", u"ліпень", u"жнівень", u"верасень", u"кастрычнік", u"лістапад", u"сьнежань"] ),
        'bg' :      lambda v: slh( v, [u"януари", u"февруари", u"март", u"април", u"май", u"юни", u"юли", u"август", u"септември", u"октомври", u"ноември", u"декември"] ),
        'bn' :      lambda v: slh( v, [u"জানুয়ারি", u"ফেব্রুয়ারি", u"মার্চ", u"এপ্রিল", u"মে", u"জুন", u"জুলাই", u"আগস্ট", u"সেপ্টেম্বর", u"অক্টোবর", u"নভেম্বর", u"ডিসেম্বর"] ),
        'br' :      lambda v: slh( v, [u"Genver", u"C'hwevrer", u"Meurzh", u"Ebrel", u"Mae", u"Mezheven", u"Gouere", u"Eost", u"Gwengolo", u"Here", u"Du", u"Kerzu"] ),
        'bs' :      lambda v: slh( v, [u"januar", u"februar", u"mart", u"april", u"maj", u"juni", u"juli", u"august", u"septembar", u"oktobar", u"novembar", u"decembar"] ),
        'ca' :      lambda v: slh( v, [u"gener", u"febrer", u"març", u"abril", u"maig", u"juny", u"juliol", u"agost", u"setembre", u"octubre", u"novembre", u"desembre"] ),
        'ceb':      lambda v: slh( v, [u"Enero", u"Pebrero", u"Marso", u"Abril", u"Mayo", u"Hunyo", u"Hulyo", u"Agosto", u"Septiyembre", u"Oktubre", u"Nobiyembre", u"Disyembre"] ),
        'co' :      lambda v: slh( v, [u"ghjennaghju", u"frivaghju", u"marzu", u"aprile", u"maghju", u"ghjugnu", u"lugliu", u"aostu", u"settembre", u"uttrovi", u"nuvembri", u"decembre"] ),
        'cs' :      lambda v: slh( v, [u"leden", u"únor", u"březen", u"duben", u"květen", u"červen", u"červenec", u"srpen", u"září", u"říjen", u"listopad", u"prosinec"] ),
        'csb':      lambda v: slh( v, [u"stëcznik", u"gromicznik", u"strumiannik", u"łżëkwiôt", u"môj", u"czerwińc", u"lëpinc", u"zélnik", u"séwnik", u"rujan", u"lëstopadnik", u"gòdnik"] ),
        'cv' :      lambda v: slh( v, [u"кăрлач", u"нарăс", u"Пуш", u"Ака", u"çу", u"çĕртме", u"утă", u"çурла", u"авăн", u"юпа", u"чӳк", u"раштав"] ),
        'cy' :      lambda v: slh( v, [u"Ionawr", u"Chwefror", u"Mawrth", u"Ebrill", u"Mai", u"Mehefin", u"Gorffennaf", u"Awst", u"Medi", u"Hydref", u"Tachwedd", u"Rhagfyr"] ),
        'da' :      lambda v: slh( v, [u"januar", u"februar", u"marts", u"april", u"maj", u"juni", u"juli", u"august", u"september", u"oktober", u"november", u"december"] ),
        'de' :      lambda v: slh( v, [u"Januar", u"Februar", u"März", u"April", u"Mai", u"Juni", u"Juli", u"August", u"September", u"Oktober", u"November", u"Dezember"] ),
        'el' :      lambda v: slh( v, [u"Ιανουάριος", u"Φεβρουάριος", u"Μάρτιος", u"Απρίλιος", u"Μάιος", u"Ιούνιος", u"Ιούλιος", u"Αύγουστος", u"Σεπτέμβριος", u"Οκτώβριος", u"Νοέμβριος", u"Δεκέμβριος"] ),
        'en' :      lambda v: slh( v, enMonthNames ),
        'eo' :      lambda v: slh( v, [u"Januaro", u"Februaro", u"Marto", u"Aprilo", u"Majo", u"Junio", u"Julio", u"Aŭgusto", u"Septembro", u"Oktobro", u"Novembro", u"Decembro"] ),
        'es' :      lambda v: slh( v, [u"enero", u"febrero", u"marzo", u"abril", u"mayo", u"junio", u"julio", u"agosto", u"septiembre", u"octubre", u"noviembre", u"diciembre"] ),
        'et' :      lambda v: slh( v, [u"jaanuar", u"veebruar", u"märts", u"aprill", u"mai", u"juuni", u"juuli", u"august", u"september", u"oktoober", u"november", u"detsember"] ),
        'eu' :      lambda v: slh( v, [u"Urtarril", u"Otsail", u"Martxo", u"Apiril", u"Maiatz", u"Ekain", u"Uztail", u"Abuztu", u"Irail", u"Urri", u"Azaro", u"Abendu"] ),
        'fa' :      lambda v: slh( v, [u"ژانویه", u"فوریه", u"مارس", u"آوریل", u"مه", u"ژوئن", u"ژوئیه", u"اوت", u"سپتامبر", u"اکتبر", u"نوامبر", u"دسامبر"] ),
        'fi' :      lambda v: slh( v, [u"tammikuu", u"helmikuu", u"maaliskuu", u"huhtikuu", u"toukokuu", u"kesäkuu", u"heinäkuu", u"elokuu", u"syyskuu", u"lokakuu", u"marraskuu", u"joulukuu"] ),
        'fo' :      lambda v: slh( v, [u"januar", u"februar", u"mars", u"apríl", u"mai", u"juni", u"juli", u"august", u"september", u"oktober", u"november", u"desember"] ),
        'fr' :      lambda v: slh( v, [u"janvier", u"février", u"mars (mois)", u"avril", u"mai", u"juin", u"juillet", u"août", u"septembre", u"octobre", u"novembre", u"décembre"] ),
        'fur':      lambda v: slh( v, [u"Zenâr", u"Fevrâr", u"Març", u"Avrîl", u"Mai", u"Jugn", u"Lui", u"Avost", u"Setembar", u"Otubar", u"Novembar", u"Dicembar"] ),
        'fy' :      lambda v: slh( v, [u"jannewaris", u"febrewaris", u"maart", u"april", u"maaie", u"juny", u"july", u"augustus", u"septimber", u"oktober", u"novimber", u"desimber"] ),
        'ga' :      lambda v: slh( v, [u"Eanáir", u"Feabhra", u"Márta", u"Aibreán", u"Bealtaine", u"Meitheamh", u"Iúil", u"Lúnasa", u"Meán Fómhair", u"Deireadh Fómhair", u"Samhain", u"Nollaig"] ),
        'gl' :      lambda v: slh( v, [u"xaneiro", u"febreiro", u"marzo", u"abril", u"maio", u"xuño", u"xullo", u"agosto", u"setembro", u"outubro", u"novembro", u"decembro"] ),
        'he' :      lambda v: slh( v, [u"ינואר", u"פברואר", u"מרץ", u"אפריל", u"מאי", u"יוני", u"יולי", u"אוגוסט", u"ספטמבר", u"אוקטובר", u"נובמבר", u"דצמבר"] ),
        'hi' :      lambda v: slh( v, [u"जनवरी", u"फ़रवरी", u"मार्च", u"अप्रैल", u"मई", u"जून", u"जुलाई", u"अगस्त", u"सितम्बर", u"अक्टूबर", u"नवम्बर", u"दिसम्बर"] ),
        'hr' :      lambda v: slh( v, [u"siječanj", u"veljača", u"ožujak", u"travanj", u"svibanj", u"lipanj", u"srpanj", u"kolovoz", u"rujan", u"listopad", u"studeni", u"prosinac"] ),
        'hu' :      lambda v: slh( v, [u"január", u"február", u"március", u"április", u"május", u"június", u"július", u"augusztus", u"szeptember", u"október", u"november", u"december"] ),
        'ia' :      lambda v: slh( v, [u"januario", u"februario", u"martio", u"april", u"maio", u"junio", u"julio", u"augusto", u"septembre", u"octobre", u"novembre", u"decembre"] ),
        'id' :      lambda v: slh( v, [u"Januari", u"Februari", u"Maret", u"April", u"Mei", u"Juni", u"Juli", u"Agustus", u"September", u"Oktober", u"November", u"Desember"] ),
        'ie' :      lambda v: slh( v, [u"januar", u"februar", u"marte", u"april", u"may", u"junio", u"juli", u"august", u"septembre", u"octobre", u"novembre", u"decembre"] ),
        'io' :      lambda v: slh( v, [u"januaro", u"februaro", u"Marto", u"aprilo", u"mayo", u"junio", u"julio", u"agosto", u"septembro", u"oktobro", u"novembro", u"decembro"] ),
        'is' :      lambda v: slh( v, [u"janúar", u"febrúar", u"mars (mánuður)", u"apríl", u"maí", u"júní", u"júlí", u"ágúst", u"september", u"október", u"nóvember", u"desember"] ),
        'it' :      lambda v: slh( v, [u"gennaio", u"febbraio", u"marzo", u"aprile", u"maggio", u"giugno", u"luglio", u"agosto", u"settembre", u"ottobre", u"novembre", u"dicembre"] ),
        'ja' :      lambda v: slh( v, makeMonthList( u"%d月" )),
        'jv' :      lambda v: slh( v, [u"Januari", u"Februari", u"Maret", u"April", u"Mei", u"Juni", u"Juli", u"Agustus", u"September", u"Oktober", u"November", u"Desember"] ),
        'ka' :      lambda v: slh( v, [u"იანვარი", u"თებერვალი", u"მარტი", u"აპრილი", u"მაისი", u"ივნისი", u"ივლისი", u"აგვისტო", u"სექტემბერი", u"ოქტომბერი", u"ნოემბერი", u"დეკემბერი"] ),
        'kn' :      lambda v: slh( v, [u"ಜನವರಿ", u"ಫೆಬ್ರವರಿ", u"ಮಾರ್ಚಿ", u"ಎಪ್ರಿಲ್", u"ಮೇ", u"ಜೂನ", u"ಜುಲೈ", u"ಆಗಸ್ಟ್", u"ಸೆಪ್ಟೆಂಬರ್", u"ಅಕ್ಟೋಬರ್", u"ನವೆಂಬರ್", u"ಡಿಸೆಂಬರ್"] ),
        'ko' :      lambda v: slh( v, makeMonthList( u"%d월" )),
        'ksh':      lambda v: slh( v, [u'Jannowaa', u'Febrowaa', u'Mä', u'Apprill', u'Meij', u'Juuni', u'Juuli', u'Aujuß', u'Sepptäber', u'Oktoober', u'Novemmber', u'Dezemmber'] ),
        'ku' :      lambda v: slh( v, [u"rêbendan", u"reşemî", u"adar", u"avrêl", u"gulan", u"pûşper", u"tîrmeh", u"gelawêj (meh)", u"rezber", u"kewçêr", u"sermawez", u"berfanbar"] ),
        'kw' :      lambda v: slh( v, [u"Mys Genver", u"Mys Whevrer", u"Mys Merth", u"Mys Ebrel", u"Mys Me", u"Mys Metheven", u"Mys Gortheren", u"Mys Est", u"Mys Gwyngala", u"Mys Hedra", u"Mys Du", u"Mys Kevardhu"] ),
        'la' :      lambda v: slh( v, [u"Ianuarius", u"Februarius", u"Martius", u"Aprilis", u"Maius", u"Iunius", u"Iulius", u"Augustus (mensis)", u"September", u"October", u"November", u"December"] ),
        'lb' :      lambda v: slh( v, [u"Januar", u"Februar", u"Mäerz", u"Abrëll", u"Mee", u"Juni", u"Juli", u"August", u"September", u"Oktober", u"November", u"Dezember"] ),
        'li' :      lambda v: slh( v, [u"jannewarie", u"fibberwarie", u"miert", u"april", u"mei", u"juni", u"juli", u"augustus (maond)", u"september", u"oktober", u"november", u"december"] ),
        'lt' :      lambda v: slh( v, [u"Sausis", u"Vasaris", u"Kovas", u"Balandis", u"Gegužė", u"Birželis", u"Liepa", u"Rugpjūtis", u"Rugsėjis", u"Spalis", u"Lapkritis", u"Gruodis"] ),
        'lv' :      lambda v: slh( v, [u"Janvāris", u"Februāris", u"Marts", u"Aprīlis", u"Maijs", u"Jūnijs", u"Jūlijs", u"Augusts", u"Septembris", u"Oktobris", u"Novembris", u"Decembris"] ),
        'mhr':      lambda v: slh( v, [ u"шорыкйол", u"пургыж", u"ӱярня", u"вӱдшор", u"ага", u"пеледыш", u"сӱрем", u"сорла", u"идым", u"шыжа", u"кылме", u"декабрь"] ),
        'mi' :      lambda v: slh( v, [u"Kohi-tātea", u"Hui-tanguru", u"Poutū-te-rangi", u"Paenga-whāwhā", u"Haratua", u"Pipiri", u"Hōngongoi", u"Here-turi-kōkā", u"Mahuru", u"Whiringa-ā-nuku", u"Whiringa-ā-rangi", u"Hakihea"] ),
        'ml' :      lambda v: slh( v, [u"ജനുവരി", u"ഫെബ്രുവരി", u"മാര്ച്", u"ഏപ്രില്", u"മേയ്", u"ജൂണ്‍", u"ജൂലൈ", u"ആഗസ്റ്റ്‌", u"സപ്തന്പര്", u"ഒക്ടോബര്", u"നവന്പര്", u"ഡിസന്പര്"] ),
        'mr' :      lambda v: slh( v, [u"जानेवारी", u"फेब्रुवारी", u"मार्च", u"एप्रिल", u"मे", u"जून", u"जुलै", u"ऑगस्ट", u"सप्टेंबर", u"ऑक्टोबर", u"नोव्हेंबर", u"डिसेंबर"] ),
        'ms' :      lambda v: slh( v, [u"Januari", u"Februari", u"Mac", u"April", u"Mei", u"Jun", u"Julai", u"Ogos", u"September", u"Oktober", u"November", u"Disember"] ),
        'nap':      lambda v: slh( v, [u"Jennaro", u"Frevaro", u"Màrzo", u"Abbrile", u"Maggio", u"Giùgno", u"Luglio", u"Aùsto", u"Settembre", u"Ottovre", u"Nuvembre", u"Dicembre"] ),
        'nds':      lambda v: slh( v, [u"Januar", u"Februar", u"März", u"April", u"Mai", u"Juni", u"Juli", u"August", u"September", u"Oktober", u"November", u"Dezember"] ),
        'nl' :      lambda v: slh( v, [u"januari", u"februari", u"maart", u"april", u"mei", u"juni", u"juli", u"augustus (maand)", u"september", u"oktober", u"november", u"december"] ),
        'nn' :      lambda v: slh( v, [u"januar", u"februar", u"månaden mars", u"april", u"mai", u"juni", u"juli", u"august", u"september", u"oktober", u"november", u"desember"] ),
        'no' :      lambda v: slh( v, [u"januar", u"februar", u"mars", u"april", u"mai", u"juni", u"juli", u"august", u"september", u"oktober", u"november", u"desember"] ),
        'oc' :      lambda v: slh( v, [u"genièr", u"febrièr", u"març", u"abril", u"mai", u"junh", u"julhet", u"agost", u"setembre", u"octobre", u"novembre", u"decembre"] ),
        'os' :      lambda v: slh( v, [u"январь", u"февраль", u"мартъи", u"апрель", u"май", u"июнь", u"июль", u"август", u"сентябрь", u"октябрь", u"ноябрь", u"декабрь"] ),
        'pdc' :     lambda v: slh( v, [u'Yenner', u'Hanning', u'Matz', u'Abril', u'Moi', u'Yuni', u'Yuli', u'Aagscht', u'September', u'Oktower', u'Nowember', u'Disember'] ),
        'pl' :      lambda v: slh( v, [u"styczeń", u"luty", u"marzec", u"kwiecień", u"maj", u"czerwiec", u"lipiec", u"sierpień", u"wrzesień", u"październik", u"listopad", u"grudzień"] ),
        'pt' :      lambda v: slh( v, [u"Janeiro", u"Fevereiro", u"Março", u"Abril", u"Maio", u"Junho", u"Julho", u"Agosto", u"Setembro", u"Outubro", u"Novembro", u"Dezembro"] ),
        'ro' :      lambda v: slh( v, [u"ianuarie", u"februarie", u"martie", u"aprilie", u"mai", u"iunie", u"iulie", u"august", u"septembrie", u"octombrie", u"noiembrie", u"decembrie"] ),
        'ru' :      lambda v: slh( v, [u"январь", u"февраль", u"март", u"апрель", u"май", u"июнь", u"июль", u"август", u"сентябрь", u"октябрь", u"ноябрь", u"декабрь"] ),
        'sc' :      lambda v: slh( v, [u"Ghennarzu", u"Frearzu", u"Martzu", u"Abrile", u"Maju", u"Làmpadas", u"Triulas", u"Aùstu", u"Cabudanni", u"Santugaìne", u"Santadria", u"Nadale"] ),
        'scn':      lambda v: slh( v, [u"jinnaru", u"frivaru", u"marzu", u"aprili", u"maiu", u"giugnu", u"giugnettu", u"austu", u"sittèmmiru", u"uttùviru", u"nuvèmmiru", u"dicèmmiru"] ),
        'sco':      lambda v: slh( v, [u"Januar", u"Februar", u"Mairch", u"Aprile", u"Mey", u"Juin", u"Julie", u"August", u"September", u"October", u"November", u"December"] ),
        'se' :      lambda v: slh( v, [u"ođđajagimánnu", u"guovvamánnu", u"njukčamánnu", u"cuoŋománnu", u"miessemánnu", u"geassemánnu", u"suoidnemánnu", u"borgemánnu", u"čakčamánnu", u"golggotmánnu", u"skábmamánnu", u"juovlamánnu"] ),
        'simple':   lambda v: slh( v, [u"January", u"February", u"March", u"April", u"May", u"June", u"July", u"August", u"September", u"October", u"November", u"December"] ),
        'sk' :      lambda v: slh( v, [u"január", u"február", u"marec", u"apríl", u"máj", u"jún", u"júl", u"august", u"september", u"október", u"november", u"december"] ),
        'sl' :      lambda v: slh( v, [u"januar", u"februar", u"marec", u"april", u"maj", u"junij", u"julij", u"avgust", u"september", u"oktober", u"november", u"december"] ),
        'sq' :      lambda v: slh( v, [u"Janari", u"Shkurti", u"Marsi (muaj)", u"Prilli", u"Maji", u"Qershori", u"Korriku", u"Gushti", u"Shtatori", u"Tetori", u"Nëntori", u"Dhjetori"] ),
        'sr' :      lambda v: slh( v, [u"јануар", u"фебруар", u"март", u"април", u"мај", u"јун", u"јул", u"август", u"септембар", u"октобар", u"новембар", u"децембар"] ),
        'su' :      lambda v: slh( v, [u"Januari", u"Pébruari", u"Maret", u"April", u"Méi", u"Juni", u"Juli", u"Agustus", u"Séptémber", u"Oktober", u"Nopémber", u"Désémber"] ),
        'sv' :      lambda v: slh( v, [u"januari", u"februari", u"mars", u"april", u"maj", u"juni", u"juli", u"augusti", u"september", u"oktober", u"november", u"december"] ),
        'ta' :      lambda v: slh( v, [u"ஜனவரி", u"பிப்ரவரி", u"மார்ச்", u"ஏப்ரல்", u"மே", u"ஜூன்", u"ஜூலை", u"ஆகஸ்டு", u"செப்டம்பர்", u"அக்டோபர்", u"நவம்பர்", u"டிசம்பர்"] ),
        'te' :      lambda v: slh( v, [u"జనవరి", u"ఫిబ్రవరి", u"మార్చి", u"ఏప్రిల్", u"మే", u"జూన్", u"జూలై", u"ఆగష్టు", u"సెప్టెంబర్", u"అక్టోబర్", u"నవంబర్", u"డిసెంబర్"] ),
        'th' :      lambda v: slh( v, [u"มกราคม", u"กุมภาพันธ์", u"มีนาคม", u"เมษายน", u"พฤษภาคม", u"มิถุนายน", u"กรกฎาคม", u"สิงหาคม", u"กันยายน", u"ตุลาคม", u"พฤศจิกายน", u"ธันวาคม"] ),
        'tl' :      lambda v: slh( v, [u"Enero", u"Pebrero", u"Marso", u"Abril", u"Mayo", u"Hunyo", u"Hulyo", u"Agosto", u"Setyembre", u"Oktubre", u"Nobyembre", u"Disyembre"] ),
        'tpi':      lambda v: slh( v, [u"Janueri", u"Februeri", u"Mas", u"Epril", u"Me", u"Jun", u"Julai", u"Ogas", u"Septemba", u"Oktoba", u"Novemba", u"Disemba"] ),
        'tr' :      lambda v: slh( v, [u"Ocak", u"Şubat", u"Mart", u"Nisan", u"Mayıs", u"Haziran", u"Temmuz", u"Ağustos", u"Eylül", u"Ekim", u"Kasım", u"Aralık"] ),
        'tt' :      lambda v: slh( v, [u"Ğínwar", u"Febräl", u"Mart", u"Äpril", u"May", u"Yün", u"Yül", u"August", u"Sentäber", u"Öktäber", u"Nöyäber", u"Dekäber"] ),
        'uk' :      lambda v: slh( v, [u"січень", u"лютий", u"березень", u"квітень", u"травень", u"червень", u"липень", u"серпень", u"вересень", u"жовтень", u"листопад", u"грудень"] ),
        'ur' :      lambda v: slh( v, [u"جنوری", u"فروری", u"مارچ", u"اپريل", u"مئ", u"جون", u"جولائ", u"اگست", u"ستمبر", u"اکتوبر", u"نومبر", u"دسمبر"] ),
        'vec':      lambda v: slh( v, [u"genaro", u"febraro", u"marzso", u"apriłe", u"majo", u"giugno", u"lujo", u"agosto", u"setenbre", u"otobre", u"novenbre", u"diçenbre"] ),
        'vi' :      lambda v: slh( v, [u"tháng một", u"tháng hai", u"tháng ba", u"tháng tư", u"tháng năm", u"tháng sáu", u"tháng bảy", u"tháng tám", u"tháng chín", u"tháng mười", u"tháng mười một", u"tháng 12"] ),
        'vo' :      lambda v: slh( v, [u"Yanul", u"Febul", u"Mäzul", u"Prilul", u"Mayul", u"Yunul", u"Yulul", u"Gustul", u"Setul", u"Tobul", u"Novul", u"Dekul"] ),
        'wa' :      lambda v: slh( v, [u"djanvî", u"fevrî", u"Måss (moes)", u"avri", u"may", u"djun", u"djulete", u"awousse", u"setimbe", u"octôbe", u"nôvimbe", u"decimbe"] ),
        'zh' :      lambda v: slh( v, makeMonthList( u"%d月" )),
        'zh-min-nan': lambda v: slh( v, [u"It-goe̍h", u"Jī-goe̍h", u"Saⁿ-goe̍h", u"Sì-goe̍h", u"Gō·-goe̍h", u"La̍k-goe̍h", u"Chhit-goe̍h", u"Peh-goe̍h", u"Káu-goe̍h", u"Cha̍p-goe̍h", u"Cha̍p-it-goe̍h", u"Cha̍p-jī-goe̍h"] ),
    },

    'Number': {
        'ar' :      lambda v: dh_number( v, u'%d (عدد)' ),
        'be' :      lambda v: dh_number( v, u'%d (лік)' ),
        'bg' :      lambda v: dh_number( v, u'%d (число)' ),
        'bs' :      lambda v: dh_number( v, u'%d (broj)' ),
        'cs' :      lambda v: dh_number( v, u'%d (číslo)' ),
        'da' :      lambda v: dh_number( v, u'%d (tal)' ),
        'en' :      lambda v: dh_number( v, u'%d (number)' ),
        'fa' :      lambda v: dh_number( v, u'%d (عدد)' ),
        'fi' :      lambda v: dh_number( v, u'%d (luku)' ),
        'fr' :      lambda v: dh_number( v, u'%d (nombre)' ),
        'he' :      lambda v: dh_number( v, u'%d (מספר)' ),
        'hu' :      lambda v: dh_number( v, u'%d (szám)' ),
        'ia' :      lambda v: dh_number( v, u'%d (numero)' ),
        'ja' :      lambda v: dh_number( v, u'%d' ),
        'ko' :      lambda v: dh_number( v, u'%d' ),
        'ksh':      lambda v: dh_number( v, u'%d (Zahl)' ),
        'la' :      lambda v: dh_number( v, u'%d' ),
        'lt' :      lambda v: dh_number( v, u'%d (skaičius)' ),
        'nds':      lambda v: dh_number( v, u'%d (Tall)' ),
        'nl' :      lambda v: dh_number( v, u'%d (getal)' ),
        'nn' :      lambda v: dh_number( v, u'Talet %d' ),
        'no' :      lambda v: dh_number( v, u'%d (tall)' ),
        'nso' :     lambda v: dh_number( v, u'%d (nomoro)' ),
        'pl' :      lambda v: dh_number( v, u'%d (liczba)' ),
        'ro' :      lambda v: dh_number( v, u'%d (cifră)' ),
        'ru' :      lambda v: dh_number( v, u'%d (число)' ),
        'sk' :      lambda v: dh_number( v, u'%d (číslo)' ),
        'sl' :      lambda v: dh_number( v, u'%d (število)' ),
        'sr' :      lambda v: dh_number( v, u'%d (број)' ),
        'sv' :      lambda v: dh_number( v, u'%d (tal)' ),
        'th' :      lambda v: dh_number( v, u'%d' ),    # was %d (จำนวน)
        'tl' :      lambda v: dh_number( v, u'%d (bilang)' ),
        'tr' :      lambda v: dh_number( v, u'%d (sayı)' ),
        'zh' :      lambda v: dh_number( v, u'%d' ),
    },

    'YearAD': {
        'af' :      dh_simpleYearAD,
        'als':      dh_simpleYearAD,
        'an' :      dh_simpleYearAD,
        'ang':      dh_simpleYearAD,
        'ar' :      dh_simpleYearAD,
        'ast':      dh_simpleYearAD,
        'az' :      dh_simpleYearAD,
        'be' :      dh_simpleYearAD,
        'bg' :      dh_simpleYearAD,
        'bn' :      lambda v: dh_yearAD( v, u'%B' ),
        'br' :      dh_simpleYearAD,
        'bs' :      dh_simpleYearAD,
        'ca' :      dh_simpleYearAD,
        'ceb':      dh_simpleYearAD,
        'cs' :      dh_simpleYearAD,
        'csb':      dh_simpleYearAD,
        'cv' :      dh_simpleYearAD,
        'cy' :      dh_simpleYearAD,
        'da' :      dh_simpleYearAD,
        'de' :      dh_simpleYearAD,
        'el' :      dh_simpleYearAD,
        'en' :      dh_simpleYearAD,
        'eo' :      dh_simpleYearAD,
        'es' :      dh_simpleYearAD,
        'et' :      dh_simpleYearAD,
        'eu' :      dh_simpleYearAD,
        'fa' :      lambda v: dh_yearAD( v, u'%F (میلادی)' ),
        'fi' :      dh_simpleYearAD,
        'fo' :      dh_simpleYearAD,
        'fr' :      dh_simpleYearAD,
        'fur':      dh_simpleYearAD,
        'fy' :      dh_simpleYearAD,
        'ga' :      dh_simpleYearAD,
        'gan' :     lambda v: dh_yearAD( v, u'%d年' ),
        'gd' :      dh_simpleYearAD,
        'gl' :      dh_simpleYearAD,
        'gu' :      lambda v: dh_yearAD( v, u'%G' ),
        'he' :      dh_simpleYearAD,
        'hi' :      lambda v: dh_yearAD( v, u'%H' ),
        'hr' :      lambda v: dh_yearAD( v, u'%d.' ),
        'hu' :      dh_simpleYearAD,
        'hy' :      dh_simpleYearAD,
        'ia' :      dh_simpleYearAD,
        'id' :      dh_simpleYearAD,
        'ie' :      dh_simpleYearAD,
        'ilo':      dh_simpleYearAD,
        'io' :      dh_simpleYearAD,
        'is' :      dh_simpleYearAD,
        'it' :      dh_simpleYearAD,
        'ja' :      lambda v: dh_yearAD( v, u'%d年' ),
        'jbo':      lambda v: dh_yearAD( v, u'%dmoi nanca' ),
        'ka' :      dh_simpleYearAD,
        'kn' :      lambda v: dh_yearAD( v, u'%K' ),
        'ko' :      lambda v: dh_yearAD( v, u'%d년' ),
        'ksh':      lambda v: dh_yearAD( v, u'Joohr %d' ),
        'ku' :      dh_simpleYearAD,
        'kw' :      dh_simpleYearAD,
        'la' :      dh_simpleYearAD,
        'lb' :      dh_simpleYearAD,
        'li' :      dh_simpleYearAD,
        'lt' :      dh_simpleYearAD,
        'lv' :      dh_simpleYearAD,
        'mi' :      dh_simpleYearAD,
        'mhr':      dh_simpleYearAD,
        'mk' :      dh_simpleYearAD,
        'ml' :      dh_simpleYearAD,
        'mo' :      dh_simpleYearAD,
        'mr' :      lambda v: dh_yearAD( v, u'ई.स. %H' ),
        'ms' :      dh_simpleYearAD,
        'na' :      dh_simpleYearAD,
        'nap':      dh_simpleYearAD,
        'nds':      dh_simpleYearAD,
        'nl' :      dh_simpleYearAD,
        'nn' :      dh_simpleYearAD,
        'no' :      dh_simpleYearAD,
        'nso' :     dh_simpleYearAD,
        'oc' :      dh_simpleYearAD,
        'os' :      dh_simpleYearAD,
        'pdc' :     dh_simpleYearAD,
        'pl' :      dh_simpleYearAD,
        'pt' :      dh_simpleYearAD,
        'rm' :      dh_simpleYearAD,
        'ro' :      dh_simpleYearAD,
        'roa-rup' : dh_simpleYearAD,
        'ru' :      lambda v: dh_yearAD( v, u'%d год' ),
        'sco':      dh_simpleYearAD,
        'scn':      dh_simpleYearAD,
        'se' :      dh_simpleYearAD,
        'sh' :      dh_simpleYearAD,
        'simple' :  dh_simpleYearAD,
        'sk' :      dh_simpleYearAD,
        'sl' :      dh_simpleYearAD,
        'sm' :      dh_simpleYearAD,
        'sq' :      dh_simpleYearAD,
        'sr' :      dh_simpleYearAD,
        'sv' :      dh_simpleYearAD,
        'su' :      dh_simpleYearAD,
        'ta' :      dh_simpleYearAD,
        'te' :      dh_simpleYearAD,
        #2005 => 'พ.ศ. 2548'
        'th' :      lambda v: dh_yearAD( v, u'พ.ศ. %T' ),
        'tl' :      dh_simpleYearAD,
        'tpi':      dh_simpleYearAD,
        'tr' :      dh_simpleYearAD,
        'tt' :      dh_simpleYearAD,
        'uk' :      dh_simpleYearAD,
        'ur' :      lambda v: dh_yearAD( v, u'%dسبم' ),
        'uz' :      dh_simpleYearAD,
        'vec':      dh_simpleYearAD,
        'vi' :      dh_simpleYearAD,
        'vo' :      dh_simpleYearAD,
        'wa' :      dh_simpleYearAD,
        'zh' :      lambda v: dh_yearAD( v, u'%d年' ),
        'zh-min-nan' :  lambda v: dh_yearAD( v, u'%d nî' ),
    },

    'YearBC': {
        'af' :      lambda v: dh_yearBC( v, u'%d v.C.' ),
        'ast':      lambda v: dh_yearBC( v, u'%d edC' ),
        'be' :      lambda v: dh_yearBC( v, u'%d да н.э.' ),
        'bg' :      lambda v: dh_yearBC( v, u'%d г. пр.н.е.' ),
        'bs' :      lambda v: dh_yearBC( v, u'%d p.n.e.' ),
        'ca' :      lambda v: dh_yearBC( v, u'%d aC' ),
        'cs' :      lambda v: dh_yearBC( v, u'%d př. n. l.' ),
        'cy' :      lambda v: dh_yearBC( v, u'%d CC' ),
        'da' :      lambda v: dh_yearBC( v, u'%d f.Kr.' ),
        'de' :      lambda v: dh_yearBC( v, u'%d v. Chr.' ),
        'el' :      lambda v: dh_yearBC( v, u'%d π.Χ.' ),
        'en' :      lambda v: dh_yearBC( v, u'%d BC' ),
        'eo' :      lambda v: dh_yearBC( v, u'-%d' ),
        'es' :      lambda v: dh_yearBC( v, u'%d a. C.' ),
        'et' :      lambda v: dh_yearBC( v, u'%d eKr' ),
        'eu' :      lambda v: dh_yearBC( v, u'K. a. %d' ),
        'fa' :      lambda v: dh_yearBC( v, u'%d (پیش از میلاد)' ),
        'fi' :      lambda v: dh_yearBC( v, u'%d eaa.' ),
        'fo' :      lambda v: dh_yearBC( v, u'%d f. Kr.' ),
        'fr' :      lambda v: dh_yearBC( v, u'-%d' ),
        'gl' :      lambda v: dh_yearBC( v, u'-%d' ),
        'he' :      lambda v: dh_yearBC( v, u'%d לפני הספירה' ),
        'hr' :      lambda v: dh_yearBC( v, u'%d. pr. Kr.' ),
        'hu' :      lambda v: dh_yearBC( v, u'I. e. %d' ),
        'id' :      lambda v: dh_yearBC( v, u'%d SM' ),
        'io' :      lambda v: dh_yearBC( v, u'%d aK' ),
        'is' :      lambda v: dh_yearBC( v, u'%d f. Kr.' ),
        'it' :      lambda v: dh_yearBC( v, u'%d a.C.' ),
        'ka' :      lambda v: dh_yearBC( v, u'ძვ. წ. %d' ),
        'ko' :      lambda v: dh_yearBC( v, u'기원전 %d년' ),
        'ksh':      lambda v: dh_yearBC( v,u'Joohr %d füür Krėßtůß'),
        'la' :      lambda v: dh_yearBC( v, u'%d a.C.n.' ),
        'lb' :      lambda v: dh_yearBC( v, u'-%d' ),
        'lt' :      lambda v: dh_yearBC( v, u'%d m. pr. m. e.'),
        'lv' :      lambda v: dh_yearBC( v, u'%d p.m.ē.'),
        'mk' :      lambda v: dh_yearBC( v, u'%d п.н.е.'),
        'ms' :      lambda v: dh_yearBC( v, u'%d SM' ),
        'nap':      lambda v: dh_yearBC( v, u'%d AC' ),
        'nds':      lambda v: dh_yearBC( v, u'%d v. Chr.' ),
        'nl' :      lambda v: dh_yearBC( v, u'%d v.Chr.' ),
        'nn' :      lambda v: dh_yearBC( v, u'-%d' ),
        'no' :      lambda v: dh_yearBC( v, u'%d f.Kr.' ),
        'oc' :      lambda v: dh_yearBC( v, u'-%d' ),
        'pl' :      lambda v: dh_yearBC( v, u'%d p.n.e.' ),
        'pt' :      lambda v: dh_yearBC( v, u'%d a.C.' ),
        'ro' :      lambda v: dh_yearBC( v, u'%d î.Hr.' ),
        'ru' :      lambda v: dh_yearBC( v, u'%d год до н. э.' ),
        'scn':      lambda v: dh_yearBC( v, u'%d a.C.' ),
        'simple' :  lambda v: dh_yearBC( v, u'%d BC' ),
        'sk' :      lambda v: dh_yearBC( v, u'%d pred Kr.' ),
        'sl' :      lambda v: dh_yearBC( v, u'%d pr. n. št.' ),
        'sq' :      lambda v: dh_yearBC( v, u'%d p.e.s.' ),
        'sr' :      lambda v: dh_yearBC( v, u'%d. п. н. е.' ),
        'sv' :      lambda v: dh_yearBC( v, u'%d f.Kr.' ),
        'sw' :      lambda v: dh_yearBC( v, u'%d KK' ),
        'ta' :      lambda v: dh_yearBC( v, u'கி.மு %d' ),
        'tr' :      lambda v: dh_yearBC( v, u'M.Ö. %d' ),
        'tt' :      lambda v: dh_yearBC( v, u'MA %d' ),
        'uk' :      lambda v: dh_yearBC( v, u'%d до н. е.' ),
        'uz' :      lambda v: dh_yearBC( v, u'Mil. av. %d' ),
        'vec':      lambda v: dh_yearBC( v, u'%d a.C.' ),
        'vo' :      lambda v: dh_yearBC( v, u'%d b.K.' ),
        'zh' :      lambda v: dh_yearBC( v, u'前%d年' ),
    },

    'DecadeAD': {
        'als':      lambda v: dh_decAD( v, u'%der' ),
        'ar' :      lambda v: dh_decAD( v, u'%d عقد' ),
        'ast':      lambda v: dh_decAD( v, u'Años %d' ),
        'ang':      lambda v: dh_decAD( v, u'%de' ),
        'ast':      lambda v: dh_decAD( v, u'Años %d' ),
        'bg' :      lambda v: dh_decAD( v, u'%d-те' ),
        'br' :      lambda v: dh_decAD( v, u'Bloavezhioù %d' ),
        'bs' :      lambda v: dh_decAD( v, u'%dte' ),

        # Unknown what the pattern is, but 1970 is different
        'ca' :      lambda m: multi( m, [
            (lambda v: dh_decAD( v, u'Dècada de %d' ),  lambda p: p == 1970),
            (lambda v: dh_decAD( v, u'Dècada del %d' ), alwaysTrue)]),

         #1970s => '1970-1979'
        'cs' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'1-9'),                                              lambda p: p == 1),
            (lambda v: dh( v, u'%d-%d', lambda i: (encDec0(i),encDec0(i)+9), decSinglVal ),     alwaysTrue)]),

        'cy' :      lambda v: dh_decAD( v, u'%dau' ),
        'da' :      lambda v: dh_decAD( v, u"%d'erne" ),
        'de' :      lambda v: dh_decAD( v, u'%der' ),
        'el' :      lambda v: dh_decAD( v, u'Δεκαετία %d' ),
        'en' :      lambda v: dh_decAD( v, u'%ds' ),
        'eo' :      lambda v: dh_decAD( v, u'%d-aj jaroj' ),
        'es' :      lambda v: dh_decAD( v, u'Años %d' ),
        'et' :      lambda v: dh_decAD( v, u'%d. aastad' ),
        'fa' :      lambda v: dh_decAD( v, u'دهه %d (میلادی)' ),

        # decades ending in 00 are spelled differently
        'fi' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 0, u'Ensimmäinen vuosikymmen'),  lambda p: p == 0),
            (lambda v: dh_decAD( v, u'%d-luku' ),                       lambda p: (p % 100 != 0)),
            (lambda v: dh_decAD( v, u'%d-vuosikymmen' ),                alwaysTrue)]),

        'fo' :      lambda v: dh_decAD( v, u'%d-árini' ),
        'fr' :      lambda v: dh_decAD( v, u'Années %d' ),
        'ga' :      lambda v: dh_decAD( v, u'%didí' ),
        'gan':      lambda v: dh_decAD( v, u'%d年代' ),
        'he' :      lambda m: multi( m, [
            (lambda v: dh( v, u'שנות ה־%d', lambda i: encDec0(i)%100, lambda ii: 1900 + ii[0] ), lambda p: p >= 1900 and p < 2000),
            # This is a dummy value, just to avoid validation testing.
            (lambda v: dh_decAD( v, u'%dth decade' ), alwaysTrue)]),        # ********** ERROR!!!

        'hi' :      lambda v: dh_decAD( v, u'%H का दशक' ),

        #1970s => 1970-1979
        'hr' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'1-9'),                                                  lambda p: p == 1),
            (lambda v: dh( v, u'%d-%d', lambda i: (encDec0(i),encDec0(i)+9), lambda ii: ii[0] ),    alwaysTrue)]),

        'hu' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'0-s évek'), lambda p: p == 1),
            (lambda v: dh_decAD( v, u'%d-as évek' ),    lambda p: (p % 100 / 10) in [0,2,3,6,8]),
            (lambda v: dh_decAD( v, u'%d-es évek' ),    alwaysTrue)]),

        'io' :      lambda v: dh_decAD( v, u'%da yari' ),

        #1970s => '1971–1980'
        'is' :      lambda v: dh( v, u'%d–%d',                   lambda i: (encDec1(i),encDec1(i)+9), lambda ii: ii[0]-1 ),
        'it' :      lambda v: dh_decAD( v, u'Anni %d' ),
        'ja' :      lambda v: dh_decAD( v, u'%d年代' ),
        'ka' :      lambda v: dh_decAD( v, u'%d-ები‎' ),
        'ko' :      lambda v: dh_decAD( v, u'%d년대' ),
        'ksh':      lambda v: dh_decAD( v, u'%d-er Joohre' ),

        #1970s => 'Decennium 198' (1971-1980)
        'la' :      lambda v: dh( v, u'Decennium %d',            lambda i: encDec1(i)/10+1, lambda ii: (ii[0]-1)*10 ),

        #1970s => 'XX amžiaus 8-as dešimtmetis' (1971-1980)
        'lt' :      lambda v: dh( v, u'%R amžiaus %d-as dešimtmetis',
                        lambda i: (encDec1(i)/100+1, encDec1(i)%100/10+1),
                        lambda v: (v[0]-1)*100 + (v[1]-1)*10 ),

        #1970s => 'Ngahurutanga 198' (1971-1980)
        'mi' :      lambda v: dh( v, u'Ngahurutanga %d',         lambda i: encDec0(i)/10+1, lambda ii: (ii[0]-1)*10 ),

        'mhr':      lambda v: dh_decAD( v, u'%d ийла' ),

        #1970s => '1970-1979'
        'nl' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'1-9'),                                              lambda p: p == 1),
            (lambda v: dh( v, u'%d-%d', lambda i: (encDec0(i),encDec0(i)+9), decSinglVal ),     alwaysTrue)]),

        'nn' :      lambda v: dh_decAD( v, u'%d0-åra' ),    # FIXME: not sure of this one
        'no' :      lambda v: dh_decAD( v, u'%d-årene' ),
        'os' :      lambda v: dh_decAD( v, u'%d-тæ' ),

        #1970s => 'Lata 70. XX wieku' for anything except 1900-1919, 2000-2019, etc, in which case its 'Lata 1900-1909'
        'pl' :      lambda m: multi( m, [
            (lambda v: dh( v, u'Lata %d-%d', lambda i: (encDec0(i),encDec0(i)+9), decSinglVal ),
                    lambda p: p%100 >= 0 and p%100 < 20 ),
            (lambda v: dh( v, u'Lata %d. %R wieku', lambda i: (encDec0(i)%100, encDec0(i)/100+1 ), lambda ii: (ii[1]-1)*100 + ii[0] ),
                    alwaysTrue)]),

        'pt' :      lambda v: dh_decAD( v, u'Década de %d' ),
        'ro' :      lambda v: dh_decAD( v, u'Anii %d' ),
        'ro' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 0, u'Primul deceniu d.Hr.'), lambda p: p == 0),
            (lambda v: dh_decAD( v, u'Anii %d' ),                   alwaysTrue)]),
        'ru' :      lambda v: dh_decAD( v, u'%d-е' ),
        'scn':      lambda v: dh_decAD( v, u'%dini' ),
        'simple' :  lambda v: dh_decAD( v, u'%ds' ),

        # 1970 => '70. roky 20. storočia'
        'sk' :      lambda v: dh( v, u'%d. roky %d. storočia',
                        lambda i: (encDec0(i)%100, encDec0(i)/100+1),
                        lambda ii: (ii[1]-1)*100 + ii[0] ),

        'sl' :      lambda v: dh_decAD( v, u'%d.' ),
        'sq' :      lambda v: dh_decAD( v, u'Vitet %d' ),
        'sr' :      lambda v: dh_decAD( v, u'%dе' ),

        'sv' :      lambda m: multi( m, [
            (lambda v: dh_decAD( v, u'%d-talet (decennium)' ), lambda p: (p % 100 == 0)),
            (lambda v: dh_decAD( v, u'%d-talet' ),             alwaysTrue)]),

        'tt' :      lambda v: dh_decAD( v, u'%d. yıllar' ),

        'uk' :      lambda m: multi( m, [
            (lambda v: dh_decAD( v, u'%d-ві' ), lambda p: p == 0 or (p % 100 == 40)),
            (lambda v: dh_decAD( v, u'%d-ні' ), lambda p: p % 1000 == 0),
            (lambda v: dh_decAD( v, u'%d-ті' ), alwaysTrue)]),
        'ur' :      lambda v: dh_decAD( v, u'%dدبم' ),
        'wa' :      lambda v: dh_decAD( v, u'Anêyes %d' ),
        'zh' :      lambda v: dh_decAD( v, u'%d年代' ),
        'zh-min-nan' : lambda v: dh_decAD( v, u'%d nî-tāi' ),
    },

    'DecadeBC': {
        'de' :      lambda v: dh_decBC( v, u'%der v. Chr.' ),
        'da' :      lambda v: dh_decBC( v, u"%d'erne f.Kr." ),
        'en' :      lambda v: dh_decBC( v, u'%ds BC' ),
        'es' :      lambda v: dh_decBC( v, u'Años %d adC' ),
        'et' :      lambda v: dh_decBC( v, u'%d. aastad eKr' ),
        'eu' :      lambda v: dh_decBC( v, u'K. a. %dko hamarkada' ),

        # decades ending in 00 are spelled differently
        'fi' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 0, u'Ensimmäinen vuosikymmen eaa.'),  lambda p: p == 0),
            (lambda v: dh_decBC( v, u'%d-luku eaa.' ),                       lambda p: (p % 100 != 0)),
            (lambda v: dh_decBC( v, u'%d-vuosikymmen eaa.' ),                alwaysTrue)]),

        'fr' :      lambda v: dh_decBC( v, u'Années -%d' ),
        'he' :      lambda v: dh_decBC( v, u'שנות ה־%d לפני הספירה' ),
        'hr' :      lambda v: dh_decBC( v, u'%dih p.n.e.' ),

        'hu' :      lambda m: multi(m, [
            (lambda v: dh_constVal(v, 0, u'i. e. 0-s évek'),
             lambda p: p == 0),
            (lambda v: dh_decBC(v, u'i. e. %d-as évek' ),
             lambda p: (p % 100 / 10) in [0,2,3,6,8]),
            (lambda v: dh_decBC(v, u'i. e. %d-es évek'), alwaysTrue)]),

        'it' :      lambda v: dh_decBC( v, u'Anni %d a.C.' ),

        'ka' :      lambda v: dh_decBC( v, u'ძვ. წ. %d-ები' ),
        'ksh':      lambda v: dh_decBC( v, u'%d-er Joohre füür Krėßtůß'), # uncertain if that's right. might go to redirect.

        # '19-10 v. Chr.'
        'nl' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'9-1 v.Chr.'),                                                  lambda p: p == 1),
            (lambda v: dh( v, u'%d-%d v.Chr.', lambda i: (encDec0(i)+9,encDec0(i)), lambda ii: ii[1] ),    alwaysTrue)]),

        'pt' :      lambda v: dh_decBC( v, u'Década de %d a.C.' ),

        'ro' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 0, u'Primul deceniu î.Hr.'), lambda p: p == 0),
            (lambda v: dh_decBC( v, u'Anii %d î.Hr.' ),             alwaysTrue)]),

        'ru' :      lambda v: dh_decBC( v, u'%d-е до н. э.' ),
        'sl' :      lambda v: dh_decBC( v, u'%d. pr. n. št.' ),

        'sv' :      lambda m: multi( m, [
            (lambda v: dh_decBC( v, u'%d-talet f.Kr. (decennium)' ), lambda p: (p % 100 == 0)),
            (lambda v: dh_decBC( v, u'%d-talet f.Kr.' ),             alwaysTrue)]),

        'tt' :      lambda v: dh_decBC( v, u'MA %d. yıllar' ),
        'uk' :      lambda m: multi( m, [
            (lambda v: dh_decBC( v, u'%d-ві до Р.Х.' ), lambda p: p == 0 or (p % 100 == 40)),
            (lambda v: dh_decBC( v, u'%d-ті до Р.Х.' ), alwaysTrue)]),
        'zh' :      lambda v: dh_decBC( v, u'前%d年代' ),
    },

    'CenturyAD': {
        'af' :      lambda m: multi( m, [
            (lambda v: dh_centuryAD( v, u'%dste eeu' ),             lambda p: p in [1,8] or (p >= 20)),
            (lambda v: dh_centuryAD( v, u'%dde eeu' ),  alwaysTrue)]),
        'als':      lambda v: dh_centuryAD( v, u'%d. Jahrhundert' ),
        'ang':      lambda v: dh_centuryAD( v, u'%de gēarhundred' ),
        'ar' :      lambda v: dh_centuryAD( v, u'قرن %d' ),
        'ast':      lambda v: dh_centuryAD( v, u'Sieglu %R' ),
        'be' :      lambda v: dh_centuryAD( v, u'%d стагодзьдзе' ),
        'bg' :      lambda v: dh_centuryAD( v, u'%d век' ),
        'br' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'Iañ kantved'),          lambda p: p == 1),
            (lambda v: dh_constVal( v, 2, u'Eil kantved'),          lambda p: p == 2),
            (lambda v: dh_centuryAD( v, u'%Re kantved' ),           lambda p: p in [2,3]),
            (lambda v: dh_centuryAD( v, u'%Rvet kantved' ),         alwaysTrue)]),
        'bs' :      lambda v: dh_centuryAD( v, u'%d. vijek' ),
        'ca' :      lambda v: dh_centuryAD( v, u'Segle %R' ),
        'cs' :      lambda v: dh_centuryAD( v, u'%d. století' ),
        'cv' :      lambda v: dh_centuryAD( v, u'%R ĕмĕр' ),
        'cy' :      lambda m: multi( m, [
            (lambda v: dh_centuryAD( v, u'%deg ganrif' ),           lambda p: p in [17,19]),
            (lambda v: dh_centuryAD( v, u'%dain ganrif' ),          lambda p: p == 21),
            (lambda v: dh_centuryAD( v, u'%dfed ganrif' ),          alwaysTrue)]),
        'da' :      lambda v: dh_centuryAD( v, u'%d00-tallet' ),
        'de' :      lambda v: dh_centuryAD( v, u'%d. Jahrhundert' ),
        'el' :      lambda m: multi( m, [
            (lambda v: dh_centuryAD( v, u'%dός αιώνας' ),           lambda p: p == 20),
            (lambda v: dh_centuryAD( v, u'%dος αιώνας' ),           alwaysTrue)]),
        'en' :      lambda m: multi( m, [
            (lambda v: dh_centuryAD( v, u'%dst century' ),          lambda p: p == 1 or (p > 20 and p%10 == 1)),
            (lambda v: dh_centuryAD( v, u'%dnd century' ),          lambda p: p == 2 or (p > 20 and p%10 == 2)),
            (lambda v: dh_centuryAD( v, u'%drd century' ),          lambda p: p == 3 or (p > 20 and p%10 == 3)),
            (lambda v: dh_centuryAD( v, u'%dth century' ),          alwaysTrue)]),
        'eo' :      lambda v: dh_centuryAD( v, u'%d-a jarcento' ),
        'es' :      lambda v: dh_centuryAD( v, u'Siglo %R' ),
        'et' :      lambda v: dh_centuryAD( v, u'%d. sajand' ),
        'eu' :      lambda v: dh_centuryAD( v, u'%R. mendea' ),  # %R. mende
        'fa' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 20, u'سده ۲۰ (میلادی)'),     lambda p: p == 20),
            # This is a dummy value, just to avoid validation testing.   Later, it should be replaced with a proper 'fa' titles
            (lambda v: dh_centuryAD( v, u'سده %d (میلادی)' ), alwaysTrue)]),        # ********** ERROR!!!
        'fi' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'Ensimmäinen vuosisata'),  lambda p: p == 1),
            (lambda v: dh( v, u'%d00-luku', lambda i: i-1, lambda ii: ii[0]+1 ),     alwaysTrue)]),
        'fo' :      lambda v: dh_centuryAD( v, u'%d. øld' ),
        'fr' :      lambda m: multi( m, [
            (lambda v: dh_centuryAD( v, u'%Rer siècle' ),           lambda p: p == 1),
            (lambda v: dh_centuryAD( v, u'%Re siècle' ),            alwaysTrue)]),
        'fy' :      lambda v: dh_centuryAD( v, u'%de ieu' ),
        'ga' :      lambda v: dh_centuryAD( v, u'%dú haois' ),
        'gl' :      lambda v: dh_centuryAD( v, u'Século %R' ),
        'he' :      lambda v: dh_centuryAD( v, u'המאה ה־%d' ),
        'hi' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 20, u'बीसवी शताब्दी'),            lambda p: p == 20),
            # This is a dummy value, just to avoid validation testing.   Later, it should be replaced with a proper 'fa' titles
            (lambda v: dh_centuryAD( v, u'%dth century' ), alwaysTrue)]),        # ********** ERROR!!!
        'hr' :      lambda v: dh_centuryAD( v, u'%d. stoljeće' ),
        'hu' :      lambda v: dh_centuryAD( v, u'%d. század' ),
        'id' :      lambda v: dh_centuryAD( v, u'Abad ke-%d' ),
        'io' :      lambda v: dh_centuryAD( v, u'%dma yar-cento' ),
        'it' :      lambda v: dh_centuryAD( v, u'%R secolo' ),
        'is' :      lambda v: dh_centuryAD( v, u'%d. öldin' ),
        'ja' :      lambda v: dh_centuryAD( v, u'%d世紀' ),
        'jv' :      lambda v: dh_centuryAD( v, u'Abad kaping %d' ),
        'ka' :      lambda v: dh_centuryAD( v, u'%R საუკუნე' ),
        'ko' :      lambda v: dh_centuryAD( v, u'%d세기' ),
        'ku' :      lambda v: dh_centuryAD( v, u"Sedsala %d'an" ),
        'kw' :      lambda m: multi( m, [
            (lambda v: dh_centuryAD( v, u'%dsa kansblydhen' ),  lambda p: p <= 3),
            (lambda v: dh_centuryAD( v, u'%da kansblydhen' ),   lambda p: p == 4),
            (lambda v: dh_centuryAD( v, u'%des kansblydhen' ),  lambda p: p == 5),
            (lambda v: dh_centuryAD( v, u'%dns kansblydhen' ),  lambda p: p >= 20),
            (lambda v: dh_centuryAD( v, u'%dves kansblydhen' ), alwaysTrue)]),
        'ksh':      lambda v: dh_centuryAD( v, u'%d. Joohunndot'),
        'la' :      lambda v: dh_centuryAD( v, u'Saeculum %d' ),
        'lb' :      lambda v: dh_centuryAD( v, u'%d. Joerhonnert' ),

        # Limburgish (li) have individual names for each century
        'li' :      lambda v: slh( v, [u'Ierste iew', u'Twiede iew', u'Derde iew', u'Veerde iew', u'Viefde iew', u'Zesde iew', u'Zevende iew', u'Achste iew', u'Negende iew', u'Tiende iew', u'Elfde iew', u'Twelfde iew', u'Dertiende iew', u'Veertiende iew', u'Vieftiende iew', u'Zestiende iew', u'Zeventiende iew', u'Achtiende iew', u'Negentiende iew', u'Twintegste iew', u'Einentwintegste iew', u'Twieëntwintegste iew',] ),

        'lt' :      lambda v: dh_centuryAD( v, u'%R amžius' ),
        'lv' :      lambda v: dh_centuryAD( v, u'%d. gadsimts' ),
        'mi' :      lambda v: dh_centuryAD( v, u'Tua %d rau tau' ),
        'mk' :      lambda v: dh_centuryAD( v, u'%d век' ),
        'nds':      lambda v: dh_centuryAD( v, u'%d. Johrhunnert' ),
        'nl' :      lambda v: dh_centuryAD( v, u'%de eeuw' ),
        'nn' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'1. århundret'),                         lambda p: p == 1),
            (lambda v: dh( v, u'%d00-talet', lambda i: i-1, lambda ii: ii[0]+1 ),   alwaysTrue)]),
        'no' :      lambda v: dh_centuryAD( v, u'%d. århundre' ),
        'os' :      lambda v: dh_centuryAD( v, u'%R æнус' ),
        'pl' :      lambda v: dh_centuryAD( v, u'%R wiek' ),
        'pt' :      lambda v: dh_centuryAD( v, u'Século %R' ),
        'ro' :      lambda v: dh_centuryAD( v, u'Secolul %R' ),
        'ru' :      lambda v: dh_centuryAD( v, u'%R век' ),
        'scn':      lambda v: dh_centuryAD( v, u'Sèculu %R' ),
        'simple' :  lambda m: multi( m, [
            (lambda v: dh_centuryAD( v, u'%dst century' ), lambda p: p == 1 or (p > 20 and p%10 == 1)),
            (lambda v: dh_centuryAD( v, u'%dnd century' ), lambda p: p == 2 or (p > 20 and p%10 == 2)),
            (lambda v: dh_centuryAD( v, u'%drd century' ), lambda p: p == 3 or (p > 20 and p%10 == 3)),
            (lambda v: dh_centuryAD( v, u'%dth century' ), alwaysTrue)]),
        'sk' :      lambda v: dh_centuryAD( v, u'%d. storočie' ),
        'sl' :      lambda v: dh_centuryAD( v, u'%d. stoletje' ),
        'sr' :      lambda v: dh_centuryAD( v, u'%d. век' ),
        'sq' :      lambda v: dh_centuryAD( v, u'Shekulli %R' ),
        'sv' :      lambda v: dh( v, u'%d00-talet',                   lambda i: i-1, lambda ii: ii[0]+1 ),
        'su' :      lambda v: dh_centuryAD( v, u'Abad ka-%d' ),
        'th' :      lambda v: dh_centuryAD( v, u'คริสต์ศตวรรษที่ %d' ),
        'tr' :      lambda v: dh_centuryAD( v, u'%d. yüzyıl' ),
        'tt' :      lambda v: dh_centuryAD( v, u'%d. yöz' ),
        'uk' :      lambda v: dh_centuryAD( v, u'%d століття' ),
        'ur' :      lambda v: dh_centuryAD( v, u'%2d00صبم' ),
        'vi' :      lambda v: dh_centuryAD( v, u'Thế kỷ %d' ),
        'wa' :      lambda v: dh_centuryAD( v, u'%dinme sieke' ),
        'zh' :      lambda v: dh_centuryAD( v, u'%d世纪' ),
        'zh-min-nan' : lambda v: dh_centuryAD( v, u'%d sè-kí' ),
    },

    'CenturyBC': {
        'af' :      lambda m: multi( m, [
            (lambda v: dh_centuryBC( v, u'%dste eeu v.C.' ),            lambda p: p in [1,8] or (p >= 20)),
            (lambda v: dh_centuryBC( v, u'%dde eeu v.C.' ),             alwaysTrue)]),
        'bg' :      lambda v: dh_centuryBC( v, u'%d век пр.н.е.' ),
        'br' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'Iañ kantved kt JK'),        lambda p: p == 1),
            (lambda v: dh_constVal( v, 2, u'Eil kantved kt JK'),        lambda p: p == 2),
            (lambda v: dh_centuryBC( v, u'%Re kantved kt JK'),          lambda p: p in [2,3]),
            (lambda v: dh_centuryBC( v, u'%Rvet kantved kt JK'),        alwaysTrue)]),
        'ca' :      lambda v: dh_centuryBC( v, u'Segle %R aC' ),
        'cs' :      lambda v: dh_centuryBC( v, u'%d. století př. n. l.' ),
        'da' :      lambda v: dh_centuryBC( v, u'%d. århundrede f.Kr.' ),
        'de' :      lambda v: dh_centuryBC( v, u'%d. Jahrhundert v. Chr.' ),
        'el' :      lambda v: dh_centuryBC( v, u'%dος αιώνας π.Χ.' ),
        'en' :      lambda m: multi( m, [
            (lambda v: dh_centuryBC( v, u'%dst century BC' ),           lambda p: p == 1 or (p > 20 and p%10 == 1)),
            (lambda v: dh_centuryBC( v, u'%dnd century BC' ),           lambda p: p == 2 or (p > 20 and p%10 == 2)),
            (lambda v: dh_centuryBC( v, u'%drd century BC' ),           lambda p: p == 3 or (p > 20 and p%10 == 3)),
            (lambda v: dh_centuryBC( v, u'%dth century BC' ),           alwaysTrue)]),
        'eo' :      lambda v: dh_centuryBC( v, u'%d-a jarcento a.K.' ),
        'es' :      lambda v: dh_centuryBC( v, u'Siglo %R adC' ),
        'et' :      lambda v: dh_centuryBC( v, u'%d. aastatuhat eKr' ),
        'fi' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'Ensimmäinen vuosisata eaa.'),               lambda p: p == 1),
            (lambda v: dh( v, u'%d00-luku eaa.', lambda i: i-1, lambda ii: ii[0]+1 ),   alwaysTrue)]),
        'fr' :      lambda m: multi( m, [
            (lambda v: dh_centuryBC( v, u'%Rer siècle av. J.-C.' ),                     lambda p: p == 1),
            (lambda v: dh_centuryBC( v, u'%Re siècle av. J.-C.' ),                      alwaysTrue)]),
        'he' :      lambda v: dh_centuryBC( v, u'המאה ה־%d לפני הספירה' ),
        'hr' :      lambda v: dh_centuryBC( v, u'%d. stoljeće p.n.e.' ),
        'id' :      lambda v: dh_centuryBC( v, u'Abad ke-%d SM' ),
        'io' :      lambda v: dh_centuryBC( v, u'%dma yar-cento aK' ),
        'it' :      lambda v: dh_centuryBC( v, u'%R secolo AC' ),
        'ja' :      lambda v: dh_centuryBC( v, u'紀元前%d世紀' ),
        'ka' :      lambda v: dh_centuryBC( v, u'ძვ. წ. %R საუკუნე' ),
        'ko' :      lambda v: dh_centuryBC( v, u'기원전 %d세기' ),
        'ksh':      lambda v: dh_centuryBC( v, u'%d. Joohunndot füür Kreůßtůß'), # uncertain if that's right. might go to redirect.
        'la' :      lambda v: dh_centuryBC( v, u'Saeculum %d a.C.n.' ),
        'lb' :      lambda v: dh_centuryBC( v, u'%d. Joerhonnert v. Chr.' ),
        'nl' :      lambda v: dh_centuryBC( v, u'%de eeuw v.Chr.' ),
        'nn' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'1. århundret fvt.'),                        lambda p: p == 1),
            (lambda v: dh( v, u'%d00-talet fvt.', lambda i: i-1, lambda ii: ii[0]+1 ),  alwaysTrue)]),
        'no' :      lambda v: dh_centuryBC( v, u'%d. århundre f.Kr.' ),
        'pl' :      lambda v: dh_centuryBC( v, u'%R wiek p.n.e.' ),
        'pt' :      lambda v: dh_centuryBC( v, u'Século %R a.C.' ),
        'ro' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'Secolul I î.Hr.'),                          lambda p: p == 1),
            (lambda v: dh_centuryBC( v, u'Secolul al %R-lea î.Hr.' ),                   alwaysTrue)]),
        'ru' :      lambda v: dh_centuryBC( v, u'%R век до н. э.' ),
        'scn':      lambda v: dh_centuryBC( v, u'Sèculu %R a.C.' ),
        'sk' :      lambda v: dh_centuryBC( v, u'%d. storočie pred Kr.' ),
        'sl' :      lambda v: dh_centuryBC( v, u'%d. stoletje pr. n. št.' ),
        'sq' :      lambda v: dh_centuryBC( v, u'Shekulli %R p.e.s.' ),
        'sr' :      lambda v: dh_centuryBC( v, u'%d. век пне.' ),
        'sv' :      lambda v: dh( v, u'%d00-talet f.Kr.', lambda i: i-1, lambda ii: ii[0]+1 ),
        'tr' :      lambda v: dh_centuryBC( v, u'MÖ %d. yüzyıl' ),
        'tt' :      lambda v: dh_centuryBC( v, u'MA %d. yöz' ),
        'uk' :      lambda v: dh_centuryBC( v, u'%d століття до Р.Х.' ),
        'zh' :      lambda m: multi( m, [
            (lambda v: dh_centuryBC( v, u'前%d世纪' ),                                 lambda p: p < 4),
            (lambda v: dh_centuryBC( v, u'前%d世紀' ),                                 alwaysTrue)]),
    },

    'CenturyAD_Cat':{
        'cs' :      lambda v: dh_centuryAD( v, u'%d. století' ),
        'da' :      lambda v: dh_centuryAD( v, u'%d. århundrede' ),
        'no' :      lambda v: dh( v, u'%d-tallet', lambda i: (i-1)*100, lambda ii: ii[0]/100+1 ),
        'ksh':      lambda v: dh_constVal( v, 1, u'Joohunndot' ),
    },

    'CenturyBC_Cat':{
        'cs' :      lambda v: dh_centuryBC( v, u'%d. století př. n. l.' ),
        'de' :      lambda v: dh_centuryBC( v, u'Jahr (%d. Jh. v. Chr.)' ),
        'no' :      lambda v: dh( v, u'%d-tallet f.Kr.', lambda i: (i-1)*100, lambda ii: ii[0]/100+1 ),
        'ksh':      lambda v: dh_constVal( v, 1, u'Joohunndot' ),
    },

    'MillenniumAD': {
        'bg' :      lambda v: dh_millenniumAD( v, u'%d хилядолетие' ),
        'ca' :      lambda v: dh_millenniumAD( v, u'Mil·lenni %R' ),
        'cs' :      lambda v: dh_millenniumAD( v, u'%d. tisíciletí' ),
        'de' :      lambda v: dh_millenniumAD( v, u'%d. Jahrtausend' ),
        'el' :      lambda v: dh_millenniumAD( v, u'%dη χιλιετία' ),
        'en' :      lambda m: multi( m, [
            (lambda v: dh_millenniumAD( v, u'%dst millennium' ),                lambda p: p == 1 or (p > 20 and p%10 == 1)),
            (lambda v: dh_millenniumAD( v, u'%dnd millennium' ),                lambda p: p == 2 or (p > 20 and p%10 == 2)),
            (lambda v: dh_millenniumAD( v, u'%drd millennium' ),                lambda p: p == 3 or (p > 20 and p%10 == 3)),
            (lambda v: dh_millenniumAD( v, u'%dth millennium' ),                alwaysTrue)]),
        'es' :      lambda v: dh_millenniumAD( v, u'%R milenio' ),

        'fa' :      lambda v: dh_millenniumAD( v, u'هزاره %R (میلادی)' ),
        'fi' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'Ensimmäinen vuosituhat'),                       lambda p: p == 1),
            (lambda v: dh_constVal( v, 2, u'Toinen vuosituhat'),                       lambda p: p == 2),
            (lambda v: dh_constVal( v, 3, u'Kolmas vuosituhat'),                       lambda p: p == 3),
            (lambda v: dh_constVal( v, 4, u'Neljäs vuosituhat'),                       lambda p: p == 4),
            (lambda v: dh_constVal( v, 5, u'Viides vuosituhat'),                       lambda p: p == 5),
            (lambda v: dh( v, u'%d000-vuosituhat', lambda i: i-1, lambda ii: ii[0]+1 ),     alwaysTrue)]),

        'fr' :      lambda m: multi( m, [
            (lambda v: dh_millenniumAD( v, u'%Rer millénaire' ),                lambda p: p == 1),
            (lambda v: dh_millenniumAD( v, u'%Re millénaire' ),                 alwaysTrue)]),
        'he' :      lambda m: multi( m, [
            (lambda v: dh_millenniumAD( v, u'האלף הראשון %d' ),                lambda p: p == 1),
            (lambda v: dh_millenniumAD( v, u'האלף השני %d' ),                lambda p: p == 2),
            (lambda v: dh_millenniumAD( v, u'האלף השלישי %d' ),                lambda p: p == 3),
            (lambda v: dh_millenniumAD( v, u'האלף הרביעי %d' ),                lambda p: p == 4),
            (lambda v: dh_millenniumAD( v, u'האלף החמישי %d ' ),                lambda p: p == 5),
            (lambda v: dh_millenniumAD( v, u'האלף השישי %d' ),                lambda p: p == 6),
            (lambda v: dh_millenniumAD( v, u'האלף השביעי %d' ),                lambda p: p == 7),
            (lambda v: dh_millenniumAD( v, u'האלף השמיני %d' ),                lambda p: p == 8),
            (lambda v: dh_millenniumAD( v, u'האלף התשיעי %d' ),                lambda p: p == 9),
            (lambda v: dh_millenniumAD( v, u'האלף העשירי %d' ),                lambda p: p == 10),
            (lambda v: dh_millenniumAD( v, u'האלף ה־%d' ),                alwaysTrue)]),
        'hu' :      lambda v: dh_millenniumAD( v, u'%d. évezred' ),
        'it' :      lambda v: dh_millenniumAD( v, u'%R millennio' ),
        'ja' :      lambda v: dh_millenniumAD( v, u'%d千年紀' ),
        'ka' :      lambda v: dh_millenniumAD( v, u'%R ათასწლეული' ),
        'ksh':      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'Eetße Johdousend'),                lambda p: p == 1),
            (lambda v: dh_constVal( v, 2, u'Zweijte Johdousend'),              lambda p: p == 2),
            (lambda v: dh_constVal( v, 3, u'Drette Johdousend'),               lambda p: p == 3),
            (lambda v: dh_constVal( v, 4, u'Veete Johdousend'),                lambda p: p == 4),
            (lambda v: dh_constVal( v, 5, u'Föfte Johdousend'),                lambda p: p == 5),
            (lambda v: dh_milleniumAD( v, u'%d. Johdousend'),			alwaysTrue)]),
        'lb' :      lambda v: dh_millenniumAD( v, u'%d. Joerdausend' ),
        'mhr':      lambda v: dh_millenniumAD( v, u'%R. курым — ' ),
        'lt' :      lambda v: dh_millenniumAD( v, u'%d tūkstantmetis' ),
        'pt' :      lambda v: slh( v, [u'Primeiro milénio d.C.', u'Segundo milénio d.C.', u'Terceiro milénio d.C.', u'Quarto milénio d.C.'] ),
        'ro' :      lambda v: slh( v, [u'Mileniul I', u'Mileniul al II-lea', u'Mileniul III'] ),
        'ru' :      lambda v: dh_millenniumAD( v, u'%d тысячелетие' ),
        'sk' :      lambda v: dh_millenniumAD( v, u'%d. tisícročie' ),
        'sl' :      lambda v: dh_millenniumAD( v, u'%d. tisočletje' ),
        'sv' :      lambda v: dh( v, u'%d000-talet (millennium)', lambda i: i-1, lambda ii: ii[0]+1 ),
        'tt' :      lambda v: dh_millenniumAD( v, u'%d. meñyıllıq' ),
        'ur' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 0, u'0000مبم'),                          lambda p: p == 0),
            (lambda v: dh_millenniumAD( v, u'%d000مبم' ),                       alwaysTrue)]),
    },

    'MillenniumBC': {
        'bg' :      lambda v: dh_millenniumBC( v, u'%d хилядолетие пр.н.е.' ),
        'ca' :      lambda v: dh_millenniumBC( v, u'Mil·lenni %R aC' ),
        'cs' :      lambda v: dh_millenniumBC( v, u'%d. tisíciletí př. n. l.' ),
        'da' :      lambda v: dh_millenniumBC( v, u'%d. årtusinde f.Kr.' ),
        'de' :      lambda v: dh_millenniumBC( v, u'%d. Jahrtausend v. Chr.' ),
        'el' :      lambda v: dh_millenniumBC( v, u'%dη χιλιετία π.Χ.' ),
        'en' :      lambda v: dh_millenniumBC( v, u'%dst millennium BC' ),
        'es' :      lambda v: dh_millenniumBC( v, u'%R milenio adC' ),
        'fi' :      lambda m: multi( m, [
            (lambda v: dh_constVal( v, 1, u'Ensimmäinen vuosituhat eaa.'),                   lambda p: p == 1),
            (lambda v: dh( v, u'%d000-vuosituhat eaa.', lambda i: i-1, lambda ii: ii[0]+1 ), alwaysTrue)]),
        'fr' :      lambda v: dh_millenniumBC( v, u'%Rer millénaire av. J.-C.' ),
        'he' :      lambda m: multi( m, [
            (lambda v: dh_millenniumAD( v, u'האלף הראשון %d לפני הספירה' ),                lambda p: p == 1),
            (lambda v: dh_millenniumAD( v, u'האלף השני %d לפני הספירה' ),                lambda p: p == 2),
            (lambda v: dh_millenniumAD( v, u'האלף השלישי %d לפני הספירה' ),                lambda p: p == 3),
            (lambda v: dh_millenniumAD( v, u'האלף הרביעי %d לפני הספירה' ),                lambda p: p == 4),
            (lambda v: dh_millenniumAD( v, u'האלף החמישי %d לפני הספירה' ),                lambda p: p == 5),
            (lambda v: dh_millenniumAD( v, u'האלף השישי %d לפני הספירה' ),                lambda p: p == 6),
            (lambda v: dh_millenniumAD( v, u'האלף השביעי %d לפני הספירה' ),                lambda p: p == 7),
            (lambda v: dh_millenniumAD( v, u'האלף השמיני %d לפני הספירה' ),                lambda p: p == 8),
            (lambda v: dh_millenniumAD( v, u'האלף התשיעי %d לפני הספירה' ),                lambda p: p == 9),
            (lambda v: dh_millenniumAD( v, u'האלף העשירי %d לפני הספירה' ),                lambda p: p == 10),
            (lambda v: dh_millenniumAD( v, u'האלף ה־%d לפני הספירה' ),                alwaysTrue)]),
        'hu' :      lambda v: dh_millenniumBC( v, u'I. e. %d. évezred' ),
        'it' :      lambda v: dh_millenniumBC( v, u'%R millennio AC' ),
        'ja' :      lambda v: dh_millenniumBC( v, u'紀元前%d千年紀' ),
        'ka' :      lambda v: dh_millenniumBC( v, u'ძვ. წ. %R ათასწლეული' ),
        'lb' :      lambda v: dh_millenniumBC( v, u'%d. Joerdausend v. Chr.' ),
        'nl' :      lambda v: dh_millenniumBC( v, u'%de millennium v.Chr.' ),
        'pt' :      lambda v: slh( v, [u'Primeiro milénio a.C.', u'Segundo milénio a.C.', u'Terceiro milénio a.C.', u'Quarto milénio a.C.'] ),
        'ro' :      lambda v: dh_millenniumBC( v, u'Mileniul %R î.Hr.' ),
        'ru' :      lambda v: dh_millenniumBC( v, u'%d тысячелетие до н. э.' ),
        'sv' :      lambda v: dh( v, u'%d000-talet f.Kr. (millennium)',     lambda i: i-1, lambda ii: ii[0]+1 ),
        'tt' :      lambda v: dh_millenniumBC( v, u'MA %d. meñyıllıq' ),
        'zh' :      lambda v: dh_millenniumBC( v, u'前%d千年' ),
    },

    'Cat_Year_MusicAlbums': {
        'cs' :      lambda v: dh_yearAD( v, u'Alba roku %d' ),
        'en' :      lambda v: dh_yearAD( v, u'%d albums' ),
        'fa' :      lambda v: dh_yearAD( v, u'آلبوم‌های %d (میلادی)'),
        'fi' :      lambda v: dh_yearAD( v, u'Vuoden %d albumit' ),
        'fr' :      lambda v: dh_yearAD( v, u'Album musical sorti en %d' ),
        'he' :      lambda v: dh_yearAD( v, u'אלבומי %d' ),
        'no' :      lambda v: dh_yearAD( v, u'Musikkalbum fra %d' ),
        'pl' :      lambda v: dh_yearAD( v, u'Albumy muzyczne wydane w roku %d' ),
        'sl' :      lambda v: dh_yearAD( v, u'Albumi iz %d' ),
        'sv' :      lambda v: dh_yearAD( v, u'%d års musikalbum' ),
    },

    'Cat_BirthsAD': {
        'an' :      lambda v: dh_yearAD( v, u'%d (naixencias)' ),
        'ar' :      lambda v: dh_yearAD( v, u'مواليد %d' ),
        'arz' :     lambda v: dh_yearAD( v, u'مواليد %d'),
        'bar' :     lambda v: dh_yearAD( v, u'Geboren %d' ),
        'be' :      lambda v: dh_yearAD( v, u'Нарадзіліся ў %d годзе' ),
        'be-x-old' : lambda v: dh_yearAD( v, u'Нарадзіліся ў %d годзе' ),
        'bg' :      lambda v: dh_yearAD( v, u'Родени през %d година' ),
        'bjn' :     lambda v: dh_yearAD( v, u'Kalahiran %d' ),
        'bn' :      lambda v: dh_yearAD( v, u'%B-এ জন্ম' ),
        'bpy' :     lambda v: dh_yearAD( v, u'মারি %B-এ উজ্জিসিতা' ),
        'br' :      lambda v: dh_yearAD( v, u'Ganedigezhioù %d' ),
        'bs' :      lambda v: dh_yearAD( v, u'%d rođenja' ),
        'cbk-zam' : lambda v: dh_yearAD( v, u'Nacidos en %d' ),
        'crh' :     lambda v: dh_yearAD( v, u'%d senesinde doğğanlar' ),
        'cs' :      lambda v: dh_yearAD( v, u'Narození %d' ),
        'cy' :      lambda v: dh_yearAD( v, u'Genedigaethau %d' ),
        'da' :      lambda v: dh_yearAD( v, u'Født i %d' ),
        'de' :      lambda v: dh_yearAD( v, u'Geboren %d' ),
        'dsb' :     lambda v: dh_yearAD( v, u'Roź. %d' ),
        'el' :      lambda v: dh_yearAD( v, u'Γεννήσεις το %d' ),
        'en' :      lambda v: dh_yearAD( v, u'%d births' ),
        'eo' :      lambda v: dh_yearAD( v, u'Naskiĝintoj en %d' ),
        'es' :      lambda v: dh_yearAD( v, u'Nacidos en %d' ),
        'et' :      lambda v: dh_yearAD( v, u'Sündinud %d' ),
        'eu' :      lambda v: dh_yearAD( v, u'%dko jaiotzak' ),
        'fi' :      lambda v: dh_yearAD( v, u'Vuonna %d syntyneet' ),
        'fa' :      lambda v: dh_yearAD( v, u'زادگان %F (میلادی)' ),
        'fr' :      lambda v: dh_yearAD( v, u'Naissance en %d' ),
        'ga' :      lambda v: dh_yearAD( v, u'Daoine a rugadh i %d' ),
        'gan' :     lambda v: dh_yearAD( v, u'%d年出世' ),
        'gv' :      lambda v: dh_yearAD( v, u'Ruggyryn \'sy vlein %d' ),
        'hsb' :     lambda v: dh_yearAD( v, u'Rodź. %d' ),
        'hy' :      lambda v: dh_yearAD( v, u'%d ծնունդներ' ),
        'id' :      lambda v: dh_yearAD( v, u'Kelahiran %d' ),
        'is' :      lambda v: dh_yearAD( v, u'Fólk fætt árið %d' ),
        'it' :      lambda v: dh_yearAD( v, u'Nati nel %d' ),
        'ja' :      lambda v: dh_yearAD( v, u'%d年生' ),
        'jv' :      lambda v: dh_yearAD( v, u'Lair %d' ),
        'ka' :      lambda v: dh_yearAD( v, u'დაბადებული %d' ),
        'kk' :      lambda v: dh_yearAD( v, u'%d жылы туғандар' ),
        'ko' :      lambda v: dh_yearAD( v, u'%d년 태어남' ),
        'la' :      lambda v: dh_yearAD( v, u'Nati %d' ),
        'lb' :      lambda v: dh_yearAD( v, u'Gebuer %d' ),
        'lv' :      lambda v: dh_yearAD( v, u'%d. gadā dzimušiel' ),
        'mk' :      lambda v: dh_yearAD( v, u'Родени во %d година' ),
        'ml' :      lambda v: dh_yearAD( v, u'%d-ൽ ജനിച്ചവർ' ),
        'mn' :      lambda v: dh_yearAD( v, u'%d онд төрөгсөд' ),
        'mr' :      lambda v: dh_yearAD( v, u'इ.स. %H मधील जन्म' ),
        'ms' :      lambda v: dh_yearAD( v, u'Kelahiran %d' ),
        'mt' :      lambda v: dh_yearAD( v, u'Twieldu fl-%d' ),
        'nah' :     lambda v: dh_yearAD( v, u'Ōtlācatqueh xiuhpan %d' ),
        'new' :     lambda v: dh_yearAD( v, u'%Hय् बुगु' ),
        'nn' :      lambda v: dh_yearAD( v, u'Fødde i %d' ),
        'no' :      lambda v: dh_yearAD( v, u'Fødsler i %d' ),
        'oc' :      lambda v: dh_yearAD( v, u'Naissença en %d' ),
        'pdc' :     lambda v: dh_yearAD( v, u'Gebore %d' ),
        'pl' :      lambda v: dh_yearAD( v, u'Urodzeni w %d' ),
        'qu' :      lambda v: dh_yearAD( v, u'Paqarisqa %d' ),
        'ro' :      lambda v: dh_yearAD( v, u'Nașteri în %d' ),
        'ru' :      lambda v: dh_yearAD( v, u'Родившиеся в %d году' ),
        'sah' :     lambda v: dh_yearAD( v, u'%d сыллаахха төрөөбүттэр' ),
        'se' :      lambda v: dh_yearAD( v, u'Riegádeamit %d' ),
        'sh' :      lambda v: dh_yearAD( v, u'Rođeni %d.' ),
        'simple' :  lambda v: dh_yearAD( v, u'%d births' ),
        'sk' :      lambda v: dh_yearAD( v, u'Narodenia v %d' ),
        'sl' :      lambda v: dh_yearAD( v, u'Rojeni leta %d' ),
        'sq' :      lambda v: dh_yearAD( v, u'Lindje %d' ),
        'sr' :      lambda v: dh_yearAD( v, u'Рођени %d.' ),
        'sv' :      lambda v: dh_yearAD( v, u'Födda %d' ),
        'sw' :      lambda v: dh_yearAD( v, u'Waliozaliwa %d' ),
        'szl' :     lambda v: dh_yearAD( v, u'Rodzyńi we %d' ),
        'ta' :      lambda v: dh_yearAD( v, u'%d பிறப்புகள்' ),
        'te' :      lambda v: dh_yearAD( v, u'%d జననాలు' ),
        'th' :      lambda v: dh_yearAD( v, u'บุคคลที่เกิดในปี พ.ศ. %T' ),
        'tl' :      lambda v: dh_yearAD( v, u'Ipinanganak noong %d' ),
        'tr' :      lambda v: dh_yearAD( v, u'%d doğumlular' ),
        'tt' :      lambda v: dh_yearAD( v, u'%d елда туганнар' ),
        'uk' :      lambda v: dh_yearAD( v, u'Народились %d' ),
        'vi' :      lambda v: dh_yearAD( v, u'Sinh %d' ),
        'war' :     lambda v: dh_yearAD( v, u'Mga natawo han %d' ),
        'yo' :      lambda v: dh_yearAD( v, u'Àwọn ọjọ́ìbí ní %d' ),
        'zh' :      lambda v: dh_yearAD( v, u'%d年出生' ),
        'zh-yue' :  lambda v: dh_yearAD( v, u'%d年出世' ),
    },

    'Cat_DeathsAD': {
        'an' :      lambda v: dh_yearAD( v, u'%d (muertes)' ),
        'ay' :      lambda v: dh_yearAD( v, u'Jiwäwi %d' ),
        'ar' :      lambda v: dh_yearAD( v, u'وفيات %d' ),
        'ba' :      lambda v: dh_yearAD( v, u'%d йылда үлгәндәр' ),
        'bar' :     lambda v: dh_yearAD( v, u'Gestorben %d' ),
        'be' :      lambda v: dh_yearAD( v, u'Памерлі ў %d годзе' ),
        'be-x-old' : lambda v: dh_yearAD( v, u'Памерлі ў %d годзе' ),
        'bg' :      lambda v: dh_yearAD( v, u'Починали през %d година' ),
        'bn' :      lambda v: dh_yearAD( v, u'%B-এ মৃত্যু' ),
        'br' :      lambda v: dh_yearAD( v, u'Marvioù %d' ),
        'bs' :      lambda v: dh_yearAD( v, u'%d smrti' ),
        'crh' :     lambda v: dh_yearAD( v, u'%d senesinde ölgenler' ),
        'cs' :      lambda v: dh_yearAD( v, u'Úmrtí %d' ),
        'cy' :      lambda v: dh_yearAD( v, u'Marwolaethau %d' ),
        'da' :      lambda v: dh_yearAD( v, u'Døde i %d' ),
        'de' :      lambda v: dh_yearAD( v, u'Gestorben %d' ),
        'dsb' :     lambda v: dh_yearAD( v, u'Wum. %d' ),
        'el' :      lambda v: dh_yearAD( v, u'Θάνατοι το %d' ),
        'en' :      lambda v: dh_yearAD( v, u'%d deaths' ),
        'eo' :      lambda v: dh_yearAD( v, u'Mortintoj en %d' ),
        'es' :      lambda v: dh_yearAD( v, u'Fallecidos en %d' ),
        'et' :      lambda v: dh_yearAD( v, u'Surnud %d' ),
        'eu' :      lambda v: dh_yearAD( v, u'%deko heriotzak' ),
        'fa' :      lambda v: dh_yearAD( v, u'درگذشتگان %F (میلادی)' ),
        'fi' :      lambda v: dh_yearAD( v, u'Vuonna %d kuolleet' ),
        'fr' :      lambda v: dh_yearAD( v, u'Décès en %d' ),
        'ga' :      lambda v: dh_yearAD( v, u'Básanna i %d' ),
        'gan' :     lambda v: dh_yearAD( v, u'%d年過世' ),
        'gv' :      lambda v: dh_yearAD( v, u'Baaseyn \'sy vlein %d' ),
        'hif' :     lambda v: dh_yearAD( v, u'%d maut' ),
        'hsb' :     lambda v: dh_yearAD( v, u'Zemr. %d' ),
        'hy' :      lambda v: dh_yearAD( v, u'%d մահեր' ),
        'id' :      lambda v: dh_yearAD( v, u'Kematian %d' ),
        'is' :      lambda v: dh_yearAD( v, u'Fólk dáið árið %d' ),
        'it' :      lambda v: dh_yearAD( v, u'Morti nel %d' ),
        'ja' :      lambda v: dh_yearAD( v, u'%d年没' ),
        'jv' :      lambda v: dh_yearAD( v, u'Pati %d' ),
        'ka' :      lambda v: dh_yearAD( v, u'გარდაცვლილი %d' ),
        'kk' :      lambda v: dh_yearAD( v, u'%d жылы қайтыс болғандар' ),
        'ko' :      lambda v: dh_yearAD( v, u'%d년 죽음' ),
        'krc' :     lambda v: dh_yearAD( v, u'%d джылда ёлгенле' ),
        'ky' :      lambda v: dh_yearAD( v, u'%d жылы кайтыш болгандар' ),
        'la' :      lambda v: dh_yearAD( v, u'Mortui %d' ),
        'lb' :      lambda v: dh_yearAD( v, u'Gestuerwen %d' ),
        'lv' :      lambda v: dh_yearAD( v, u'%d. gadā mirušie' ),
        'mk' :      lambda v: dh_yearAD( v, u'Починати во %d година' ),
        'ml' :      lambda v: dh_yearAD( v, u'%d-ൽ മരിച്ചവർ' ),
        'mn' :      lambda v: dh_yearAD( v, u'%d онд нас барагсад' ),
        'ms' :      lambda v: dh_yearAD( v, u'Kematian %d' ),
        'mt' :      lambda v: dh_yearAD( v, u'Mietu fl-%d' ),
        'nah' :     lambda v: dh_yearAD( v, u'%d miquiztli' ),
        'nn' :      lambda v: dh_yearAD( v, u'Døde i %d' ),
        'no' :      lambda v: dh_yearAD( v, u'Dødsfall i %d' ),
        'oc' :      lambda v: dh_yearAD( v, u'Decès en %d' ),
        'pdc' :     lambda v: dh_yearAD( v, u'Gschtaerewe %d' ),
        'pl' :      lambda v: dh_yearAD( v, u'Zmarli w %d' ),
        'pt' :      lambda v: dh_yearAD( v, u'Mortos em %d' ),
        'qu' :      lambda v: dh_yearAD( v, u'Wañusqa %d' ),
        'ro' :      lambda v: dh_yearAD( v, u'Decese în %d' ),
        'ru' :      lambda v: dh_yearAD( v, u'Умершие в %d году' ),
        'sah' :     lambda v: dh_yearAD( v, u'%d сыллаахха өлбүттэр' ),
        'se' :      lambda v: dh_yearAD( v, u'Jápmimat %d' ),
        'sh' :      lambda v: dh_yearAD( v, u'Umrli %d.' ),
        'simple' :  lambda v: dh_yearAD( v, u'%d deaths' ),
        'sk' :      lambda v: dh_yearAD( v, u'Úmrtia v %d' ),
        'sl' :      lambda v: dh_yearAD( v, u'Umrli leta %d' ),
        'sq' :      lambda v: dh_yearAD( v, u'Vdekje %d' ),
        'sr' :      lambda v: dh_yearAD( v, u'Умрли %d.' ),
        'sv' :      lambda v: dh_yearAD( v, u'Avlidna %d' ),
        'sw' :      lambda v: dh_yearAD( v, u'Waliofariki %d' ),
        'szl' :     lambda v: dh_yearAD( v, u'Umarći we %d' ),
        'ta' :      lambda v: dh_yearAD( v, u'%d இறப்புகள்' ),
        'te' :      lambda v: dh_yearAD( v, u'%d మరణాలు' ),
        'th' :      lambda v: dh_yearAD( v, u'บุคคลที่เสียชีวิตในปี พ.ศ. %T' ),
        'tl' :      lambda v: dh_yearAD( v, u'Namatay noong %d' ),
        'tr' :      lambda v: dh_yearAD( v, u'%d yılında ölenler' ),
        'tt' :      lambda v: dh_yearAD( v, u'%d елда вафатлар' ),
        'uk' :      lambda v: dh_yearAD( v, u'Померли %d' ),
        'vi' :      lambda v: dh_yearAD( v, u'Mất %d' ),
        'war' :     lambda v: dh_yearAD( v, u'Mga namatay han %d' ),
        'yo' :      lambda v: dh_yearAD( v, u'Àwọn ọjọ́aláìsí ní %d' ),
        'zh' :      lambda v: dh_yearAD( v, u'%d年逝世' ),
        'zh-yue' :  lambda v: dh_yearAD( v, u'%d年死' ),
    },

    'Cat_BirthsBC': {
        'en' :      lambda v: dh_yearBC( v, u'%d BC births' ),
        'no' :      lambda v: dh_yearBC( v, u'Fødsler i %d f.Kr.' ),
    },
    'Cat_DeathsBC': {
        'en' :      lambda v: dh_yearBC( v, u'%d BC deaths' ),
        'fr' :      lambda v: dh_yearBC( v, u'Décès en -%d' ),
        'no' :      lambda v: dh_yearBC( v, u'Dødsfall i %d f.Kr.' ),
    },

    'CurrEvents': {
        'an' :      lambda v: dh_singVal( v, u'Autualidá' ),
        'ang':      lambda v: dh_singVal( v, u'Efenealde belimpas' ),
        'ar' :      lambda v: dh_singVal( v, u'الأحداث الجارية' ),
        'be' :      lambda v: dh_singVal( v, u'Бягучыя падзеі' ),
        'bg' :      lambda v: dh_singVal( v, u'Текущи събития' ),
        'ca' :      lambda v: dh_singVal( v, u'Viquipèdia:Actualitat' ),
        'cs' :      lambda v: dh_singVal( v, u'Portál:Aktuality' ),
        'da' :      lambda v: dh_singVal( v, u'Aktuelle begivenheder' ),
        'de' :      lambda v: dh_singVal( v, u'Aktuelle Ereignisse' ),
        'el' :      lambda v: dh_singVal( v, u'Τρέχοντα γεγονότα' ),
        'en' :      lambda v: dh_singVal( v, u'Current events' ),
        'eo' :      lambda v: dh_singVal( v, u'Aktualaĵoj' ),
        'es' :      lambda v: dh_singVal( v, u'Actualidad' ),
        'et' :      lambda v: dh_singVal( v, u'Current events' ),
        'fa' :      lambda v: dh_singVal( v, u'رویدادهای کنونی'),
        'fi' :      lambda v: dh_singVal( v, u'Ajankohtaista' ),
        'fr' :      lambda v: dh_singVal( v, u'Actualités' ),
        'gl' :      lambda v: dh_singVal( v, u'Novas' ),
        'he' :      lambda v: dh_singVal( v, u'אקטואליה' ),
        'hu' :      lambda v: dh_singVal( v, u'Friss események' ),
        'id' :      lambda v: dh_singVal( v, u'Wikipedia:Peristiwa terkini' ),
        'io' :      lambda v: dh_singVal( v, u'Current events' ),
        'it' :      lambda v: dh_singVal( v, u'Attualità' ),
        'ja' :      lambda v: dh_singVal( v, u'最近の出来事' ),
        'ka' :      lambda v: dh_singVal( v, u'ახალი ამბები' ),
        'ko' :      lambda v: dh_singVal( v, u'요즘 화제' ),
        'ksh':      lambda v: dh_singVal( v, u'Et Neuste' ),
        'ku' :      lambda v: dh_singVal( v, u'Bûyerên rojane' ),
        'la' :      lambda v: dh_singVal( v, u'Novissima' ),
        'lb' :      lambda v: dh_singVal( v, u'Aktualitéit' ),
        'la' :      lambda v: dh_singVal( v, u"Nuntii" ),
        'li' :      lambda v: dh_singVal( v, u"In 't nuujs" ),
        'mn' :      lambda v: dh_singVal( v, u'Мэдээ' ),
        'nl' :      lambda v: dh_singVal( v, u'In het nieuws' ),
        'no' :      lambda v: dh_singVal( v, u'Aktuelt' ),
        'os' :      lambda v: dh_singVal( v, u'Xabar' ),
        'pl' :      lambda v: dh_singVal( v, u'Bieżące wydarzenia' ),
        'pt' :      lambda v: dh_singVal( v, u'Eventos atuais' ),
        'ro' :      lambda v: dh_singVal( v, u'Actualităţi' ),
        'ru' :      lambda v: dh_singVal( v, u'Текущие события' ),
        'scn':      lambda v: dh_singVal( v, u'Nutizzî' ),
        'simple':   lambda v: dh_singVal( v, u'World news' ),
        'sk' :      lambda v: dh_singVal( v, u'Aktuality' ),
        'sl' :      lambda v: dh_singVal( v, u'Trenutni dogodki' ),
        'sr' :      lambda v: dh_singVal( v, u'Википедија:Актуелности' ),
        'sv' :      lambda v: dh_singVal( v, u'Aktuella händelser' ),
        'su' :      lambda v: dh_singVal( v, u'Keur lumangsung' ),
        'ta' :      lambda v: dh_singVal( v, u'நடப்பு நிகழ்வுகள்' ),
        'th' :      lambda v: dh_singVal( v, u'เหตุการณ์ปัจจุบัน' ),
        'tl' :      lambda v: dh_singVal( v, u'Kasalukuyang pangyayari' ),
        'tr' :      lambda v: dh_singVal( v, u'Güncel olaylar' ),
        'uk' :      lambda v: dh_singVal( v, u'Поточні події' ),
        'ur' :      lambda v: dh_singVal( v, u'حالات حاضرہ' ),
        'vi' :      lambda v: dh_singVal( v, u'Thời sự' ),
        'wa' :      lambda v: dh_singVal( v, u'Wikinoveles' ),
        'yo' :      lambda v: dh_singVal( v, u'Current events' ),
        'zh' :      lambda v: dh_singVal( v, u'新闻动态' ),
        'zh-min-nan': lambda v: dh_singVal( v, u'Sin-bûn sū-kiāⁿ' ),
    },
}

#
# Add auto-generated empty dictionaries for DayOfMonth and MonthOfYear articles
#
for dayOfMonth in dayMnthFmts:
    formats[dayOfMonth] = {}
for monthOfYear in yrMnthFmts:
    formats[monthOfYear] = {}

def addFmt( lang, isMnthOfYear, patterns ):
    """Add 12 month formats for a specific type ('January','Feb..), for a given language.
    The function must accept one parameter for the ->int or ->string conversions, just like
    everywhere else in the formats map.
    The patterns parameter is a list of 12 elements to be used for each month.
    """
    if len(patterns) != 12:
        raise AssertionError(u'pattern %s does not have 12 elements' % lang )

    for i in range(12):
        if patterns[i] is not None:
            if isMnthOfYear:
                formats[yrMnthFmts[i]][lang] = eval(u'lambda v: dh_mnthOfYear( v, u"%s" )' % patterns[i])
            else:
                formats[dayMnthFmts[i]][lang] = eval(u'lambda v: dh_dayOfMnth( v, u"%s" )' % patterns[i])

def makeMonthList(pattern):
    return [pattern % m for m in range(1,13)]

def makeMonthNamedList(lang, pattern, makeUpperCase=None):
    """Creates a list of 12 elements based on the name of the month.
    The language-dependent month name is used as a formating argument to the pattern.
    The pattern must be have one %s that will be replaced by the localized month name.
    Use %%d for any other parameters that should be preserved.
    """
    if makeUpperCase is None:
        f = lambda s: s
    elif makeUpperCase == True:
        f = lambda s: s[0].upper() + s[1:]
    elif makeUpperCase == False:
        f = lambda s: s[0].lower() + s[1:]

    return [ pattern % f(monthName(lang, m)) for m in range(1,13) ]

def addFmt2( lang, isMnthOfYear, pattern, makeUpperCase = None ):
    addFmt( lang, isMnthOfYear, makeMonthNamedList( lang, pattern, makeUpperCase ))

#
# Add day of the month formats to the formatting table:   "en:May 15"
#
addFmt2('af', False, u"%%d %s", True )
addFmt2('als',False, u"%%d. %s", True )
addFmt ('an', False,       [ u"%d de chinero", u"%d de frebero", u"%d de marzo", u"%d d'abril", u"%d de mayo", u"%d de chunio", u"%d de chulio", u"%d d'agosto", u"%d de setiembre", u"%d d'otubre", u"%d de nobiembre", u"%d d'abiento" ])
#addFmt ('ang',False,       [ u"%d Æfterra Gēola", u"%d Solmōnaþ", u"%d Hréþmónaþ", u"%d Éastermónaþ", u"%d Þrimilcemónaþ", u"%d Séremónaþ", u"%d Mǽdmónaþ", u"%d Wéodmónaþ", u"%d Háligmónaþ", u"%d Winterfylleþ", u"%d Blótmónaþ", u"%d Gēolmōnaþ" ])
addFmt2('ang',False, u"%%d %s", True )
addFmt ('ar', False,       [ u"%d يناير", u"%d فبراير", u"%d مارس", u"%d أبريل", u"%d مايو", u"%d يونيو", u"%d يوليو", u"%d أغسطس", u"%d سبتمبر", u"%d أكتوبر", u"%d نوفمبر", u"%d ديسمبر" ])
addFmt ('ast',False,       [ u"%d de xineru", u"%d de febreru", u"%d de marzu", u"%d d'abril", u"%d de mayu", u"%d de xunu", u"%d de xunetu", u"%d d'agostu", u"%d de setiembre", u"%d d'ochobre", u"%d de payares", u"%d d'avientu" ])
addFmt ('be', False,       [ u"%d студзеня", u"%d лютага", u"%d сакавіка", u"%d красавіка", u"%d траўня", u"%d чэрвеня", u"%d ліпеня", u"%d жніўня", u"%d верасьня", u"%d кастрычніка", u"%d лістапада", u"%d сьнежня" ])
addFmt2('bg', False, u"%%d %s", False )
#addFmt2('br', False, u"%%d %s", True ) # See bellow for br initialization
addFmt2('bn', False, u"%s %%B" )
addFmt2('bs', False, u"%%d. %s", False )
addFmt ('ca', False,       [ u"%d de gener", u"%d de febrer", u"%d de març", u"%d d'abril", u"%d de maig", u"%d de juny", u"%d de juliol", u"%d d'agost", u"%d de setembre", u"%d d'octubre", u"%d de novembre", u"%d de desembre" ])
addFmt2('ceb',False, u"%s %%d", True )
addFmt ('co', False,       [ u"%d di ghjennaghju", u"%d di frivaghju", u"%d di marzu", u"%d d'aprile", u"%d di maghju", u"%d di ghjugnu", u"%d di lugliu", u"%d d'aostu", u"%d di settembre", u"%d d'uttrovi", u"%d di nuvembri", u"%d di decembre" ])
addFmt2('cs', False, u"%%d. %s", False )
addFmt2('csb',False, u"%%d %sa", False )
addFmt2('cv', False, u"%s, %%d", True )
addFmt2('cy', False, u"%%d %s", True )
addFmt2('da', False, u"%%d. %s", False )
addFmt2('de', False, u"%%d. %s", True )
addFmt ('el', False,       [ u"%d Ιανουαρίου", u"%d Φεβρουαρίου", u"%d Μαρτίου", u"%d Απριλίου", u"%d Μαΐου", u"%d Ιουνίου", u"%d Ιουλίου", u"%d Αυγούστου", u"%d Σεπτεμβρίου", u"%d Οκτωβρίου", u"%d Νοεμβρίου", u"%d Δεκεμβρίου" ])
addFmt2('en', False, u"%s %%d", True )
addFmt2('eo', False, u"%%d-a de %s", False )
addFmt2('es', False, u"%%d de %s", False )
addFmt2('et', False, u"%%d. %s", False )
addFmt2('eu', False, u"%saren %%d", True )
addFmt ('fa', False, [u"%d ژانویه", u"%d فوریه", u"%d مارس", u"%d آوریل", u"%d مه", u"%d ژوئن", u"%d ژوئیه", u"%d اوت", u"%d سپتامبر", u"%d اکتبر", u"%d نوامبر", u"%d دسامبر" ])
addFmt2('fi', False, u"%%d. %sta", False )
addFmt2('fo', False, u"%%d. %s", False )
addFmt ('fr', False,       [ u"%d janvier", u"%d février", u"%d mars", u"%d avril", u"%d mai", u"%d juin", u"%d juillet", u"%d août", u"%d septembre", u"%d octobre", u"%d novembre", u"%d décembre" ])
addFmt2('fur',False, u"%%d di %s", True )
addFmt2('fy', False, u"%%d %s", False )
addFmt ('ga', False,       [ u"%d Eanáir", u"%d Feabhra", u"%d Márta", u"%d Aibreán", u"%d Bealtaine", u"%d Meitheamh", u"%d Iúil", u"%d Lúnasa", u"%d Meán Fómhair", u"%d Deireadh Fómhair", u"%d Samhain", u"%d Mí na Nollag" ])
addFmt2('gl', False, u"%%d de %s", False )
addFmt2('he', False, u"%%d ב%s" )      # [ u"%d בינואר", u"%d בפברואר", u"%d במרץ", u"%d באפריל", u"%d במאי", u"%d ביוני", u"%d ביולי", u"%d באוגוסט", u"%d בספטמבר", u"%d באוקטובר", u"%d בנובמבר", u"%d בדצמבר" ])
addFmt ('hr', False,       [ u"%d. siječnja", u"%d. veljače", u"%d. ožujka", u"%d. travnja", u"%d. svibnja", u"%d. lipnja", u"%d. srpnja", u"%d. kolovoza", u"%d. rujna", u"%d. listopada", u"%d. studenog", u"%d. prosinca" ])
addFmt2('hu', False, u"%s %%d", True )
addFmt2('ia', False, u"%%d de %s", False )
addFmt2('id', False, u"%%d %s", True )
addFmt2('ie', False, u"%%d %s", False )
addFmt2('io', False, u"%%d di %s", False )
addFmt ('is', False,       [ u"%d. janúar", u"%d. febrúar", u"%d. mars", u"%d. apríl", u"%d. maí", u"%d. júní", u"%d. júlí", u"%d. ágúst", u"%d. september", u"%d. október", u"%d. nóvember", u"%d. desember" ])
addFmt2('it', False, u"%%d %s", False )
addFmt ('ja', False,       makeMonthList( u"%d月%%d日" ))
addFmt2('jv', False, u"%%d %s", True )
addFmt2('ka', False, u"%%d %s" )
addFmt ('ko', False,       makeMonthList( u"%d월 %%d일" ))
addFmt ('ku', False,       [ u"%d'ê rêbendanê", u"%d'ê reşemiyê", u"%d'ê adarê", u"%d'ê avrêlê", u"%d'ê gulanê", u"%d'ê pûşperê", u"%d'ê tîrmehê", u"%d'ê gelawêjê", u"%d'ê rezberê", u"%d'ê kewçêrê", u"%d'ê sermawezê", u"%d'ê berfanbarê" ])
addFmt ('la', False,       [ u"%d Ianuarii", u"%d Februarii", u"%d Martii", u"%d Aprilis", u"%d Maii", u"%d Iunii", u"%d Iulii", u"%d Augusti", u"%d Septembris", u"%d Octobris", u"%d Novembris", u"%d Decembris" ])
addFmt2('lb', False, u"%%d. %s", True )
addFmt ('li', False,       [ u"%d januari", u"%d februari", u"%d miert", u"%d april", u"%d mei", u"%d juni", u"%d juli", u"%d augustus", u"%d september", u"%d oktober", u"%d november", u"%d december" ])
addFmt ('lt', False,       [ u"Sausio %d", u"Vasario %d", u"Kovo %d", u"Balandžio %d", u"Gegužės %d", u"Birželio %d", u"Liepos %d", u"Rugpjūčio %d", u"Rugsėjo %d", u"Spalio %d", u"Lapkričio %d", u"Gruodžio %d" ])
addFmt2('lv', False, u"%%d. %s", False )
addFmt2('mhr',False, u"%%d %s", False )
addFmt ('mk', False,       [ u"%d јануари", u"%d февруари", u"%d март", u"%d април", u"%d мај", u"%d јуни", u"%d јули", u"%d август", u"%d септември", u"%d октомври", u"%d ноември", u"%d декември" ])
addFmt2('ml', False, u"%s %%d" )
addFmt2('ms', False, u"%%d %s", True )
addFmt2('nap',False, u"%%d 'e %s", False )
addFmt2('nds',False, u"%%d. %s", True )
addFmt ('nl', False,       [ u"%%d %s" % v for v in [ u"januari", u"februari", u"maart", u"april", u"mei", u"juni", u"juli", u"augustus", u"september", u"oktober", u"november", u"december" ]])
addFmt ('nn', False,       [ u"%%d. %s" % v for v in [u"januar", u"februar", u"mars", u"april", u"mai", u"juni", u"juli", u"august", u"september", u"oktober", u"november", u"desember"]])
addFmt2('no', False, u"%%d. %s", False )
addFmt ('oc', False,       [ u"%d de genièr", u"%d de febrièr", u"%d de març", u"%d d'abril", u"%d de mai", u"%d de junh", u"%d de julhet", u"%d d'agost", u"%d de setembre", u"%d d'octobre", u"%d de novembre", u"%d de decembre" ])
addFmt ('os', False,       [ u"%d январы", u"%d февралы", u"%d мартъийы", u"%d апрелы", u"%d майы", None, u"%d июлы", None, u"%d сентябры", None, u"%d ноябры", u"%d декабры" ])
addFmt ('pl', False,       [ u"%d stycznia", u"%d lutego", u"%d marca", u"%d kwietnia", u"%d maja", u"%d czerwca", u"%d lipca", u"%d sierpnia", u"%d września", u"%d października", u"%d listopada", u"%d grudnia" ])
addFmt2('pt', False, u"%%d de %s", True )
addFmt2('ro', False, u"%%d %s", False )
addFmt ('ru', False,       [ u"%d января", u"%d февраля", u"%d марта", u"%d апреля", u"%d мая", u"%d июня", u"%d июля", u"%d августа", u"%d сентября", u"%d октября", u"%d ноября", u"%d декабря" ])
addFmt2('sco',False, u"%%d %s", True )
addFmt2('scn',False, u"%%d di %s", False )
addFmt ('se', False,       [ u"ođđajagimánu %d.", u"guovvamánu %d.", u"njukčamánu %d.", u"cuoŋománu %d.", u"miessemánu %d.", u"geassemánu %d.", u"suoidnemánu %d.", u"borgemánu %d.", u"čakčamánu %d.", u"golggotmánu %d.", u"skábmamánu %d.", u"juovlamánu %d." ])
addFmt ('sh', False,       makeMonthList( u"%%d.%d." ))
addFmt2('simple', False, u"%s %%d", True )
addFmt2('sk', False, u"%%d. %s", False )
addFmt2('sl', False, u"%%d. %s", False )
addFmt ('sq', False,       [ u"%d Janar", u"%d Shkurt", u"%d Mars", u"%d Prill", u"%d Maj", u"%d Qershor", u"%d Korrik", u"%d Gusht", u"%d Shtator", u"%d Tetor", u"%d Nëntor", u"%d Dhjetor" ])
addFmt2('sr', False, u"%%d. %s", False )
addFmt2('su', False, u"%%d %s", True )
addFmt2('sv', False, u"%%d %s", False )
addFmt2('ta', False, u"%s %%d" )
addFmt2('te', False, u"%s %%d" )
addFmt2('th', False, u"%%d %s" )    # %%T
addFmt2('tl', False, u"%s %%d" )
addFmt2('tr', False, u"%%d %s", True )
addFmt2('tt', False, u"%%d. %s", True )
addFmt ('uk', False,       [ u"%d січня", u"%d лютого", u"%d березня", u"%d квітня", u"%d травня", u"%d червня", u"%d липня", u"%d серпня", u"%d вересня", u"%d жовтня", u"%d листопада", u"%d грудня" ])
addFmt ('ur', False,       [ u"%d جنوری", u"%d فروری", u"%d مارچ", u"%d اپریل", u"%d مئ", u"%d جون", u"%d جلائ", u"%d اگست", u"%d ستمب", u"%d اکتوبر", u"%d نومب", u"%d دسمب" ])
addFmt2('vec',False, u"%%d de %s", False )
addFmt ('vi', False,       makeMonthList( u"%%d tháng %d" ))
addFmt2('vo', False, u"%s %%d", False )
addFmt ('zh', False,       makeMonthList( u"%d月%%d日" ))

# Walloon names depend on the day number, thus we must generate various different patterns
waMonthNames = [ u"djanvî", u"fevrî", u"måss", u"avri", u"may", u"djun", u"djulete", u"awousse", u"setimbe", u"octôbe", u"nôvimbe", u"decimbe" ]

# For month names begining with a consonant...
for i in [0,1,2,4,5,6,8,10,11]:
    formats[dayMnthFmts[i]]['wa'] = eval(
        (u'lambda m: multi( m, [' +
            u'(lambda v: dh_dayOfMnth( v, u"%%dî d\' %s" ), lambda p: p == 1),' +
            u'(lambda v: dh_dayOfMnth( v, u"%%d d\' %s" ),  lambda p: p in [2,3,20,22,23]),' +
            u'(lambda v: dh_dayOfMnth( v, u"%%d di %s" ),   alwaysTrue)])') % (waMonthNames[i], waMonthNames[i], waMonthNames[i]))
# For month names begining with a vowel...
for i in [3,7,9]:
    formats[dayMnthFmts[i]]['wa'] = eval(
        (u'lambda m: multi( m, [' +
            u'(lambda v: dh_dayOfMnth( v, u"%%dî d\' %s" ), lambda p: p == 1),' +
            u'(lambda v: dh_dayOfMnth( v, u"%%d d\' %s" ),  alwaysTrue)])') % (waMonthNames[i], waMonthNames[i]))

# Brazil uses "1añ" for the 1st of every month, and number without suffix for all other days
brMonthNames = makeMonthNamedList( 'br', u"%s", True )
for i in range(0,12):
    formats[dayMnthFmts[i]]['br'] = eval(
        (u'lambda m: multi( m, [' +
            u'(lambda v: dh_dayOfMnth( v, u"%%dañ %s" ), lambda p: p == 1),' +
            u'(lambda v: dh_dayOfMnth( v, u"%%d %s" ),   alwaysTrue)])') % (brMonthNames[i], brMonthNames[i]))

#
# Month of the Year: "en:May 1976"
#
addFmt2('af', True, u"%s %%d", True )
addFmt2('ar', True, u"%s %%d" )
addFmt2('ang',True, u"%s %%d", True )
addFmt2('cs', True, u"%s %%d" )
addFmt2('de', True, u"%s %%d", True )
addFmt ('el', True,     [ u"Ιανουάριος %d", u"Φεβρουάριος %d", u"Μάρτιος %d", u"Απρίλιος %d", u"Μάιος %d", u"Ιούνιος %d", u"Ιούλιος %d", u"Άυγουστος %d", u"Σεπτέμβριος %d", u"Οκτώβριος %d", u"Νοέμβριος %d", u"Δεκέμβριος %d" ])
addFmt2('en', True, u"%s %%d", True )
addFmt2('eo', True, u"%s de %%d" )
addFmt2('es', True, u"%s de %%d", True )
addFmt2('et', True, u"%s %%d", True )
addFmt2('fi', True, u"%s %%d", True )
addFmt ('fr', True,     [ u"Janvier %d", u"Février %d", u"Mars %d", u"Avril %d", u"Mai %d", u"Juin %d", u"Juillet %d", u"Août %d", u"Septembre %d", u"Octobre %d", u"Novembre %d", u"Décembre %d" ])
addFmt2('he', True, u"%s %%d", True )
addFmt2('it', True, u"Attualità/Anno %%d - %s", True )
addFmt ('ja', True,     [ u"「最近の出来事」%%d年%d月" % mm for mm in range(1,13)])
addFmt2('ka', True, u"%s, %%d" )
addFmt ('ko', True,     [ u"%d년 1월", u"%d년 2월", u"%d년 3월", u"%d년 4월", u"%d년 5월", u"%d년 6월", u"%d년 7월", u"%d년 8월", u"%d년 9월", u"%d년 10월", u"%d년 11월", u"%d년 12월" ])
addFmt ('li', True,     [ u"januari %d", u"februari %d", u"miert %d", u"april %d", u"mei %d", u"juni %d", u"juli %d", u"augustus %d", u"september %d", u"oktober %d", u"november %d", u"december %d" ])
addFmt ('nl', True,     [ u"Januari %d", u"Februari %d", u"Maart %d", u"April %d", u"Mei %d", u"Juni %d", u"Juli %d", u"Augustus %d", u"September %d", u"Oktober %d", u"November %d", u"December %d" ])
addFmt2('pl', True, u"%s %%d", True )
addFmt ('scn',True,     [ None, None, u"Marzu %d", None, None, None, None, None, None, None, None, None ])
addFmt2('simple', True, u"%s %%d", True )
addFmt2('sk', True, u"%s %%d" )
addFmt2('sv', True, u"%s %%d", True )
addFmt2('th', True, u"%s พ.ศ. %%T" )
addFmt2('tl', True, u"%s %%d" )
addFmt2('tt', True, u"%s, %%d", True )
addFmt ('ur', True,     [ u"%d01مبم", u"%d02مبم", u"%d03مبم", u"%d04مبم", u"%d05مبم", u"%d06مبم", u"%d07مبم", u"%d08مبم", u"%d09مبم", u"%d10مبم", u"%d11مبم", u"%d12مبم" ])
addFmt2('uk', True, u"%s %%d", True )
addFmt ('vi', True,     makeMonthList( u"Tháng %d năm %%d" ))
addFmt ('zh', True,     makeMonthList( u"%%d年%d月" ))
addFmt ('zh-min-nan',True,  makeMonthList( u"%%d nî %d goe̍h" ))


#
#
# This table defines the limits for each type of format data.
# Each item is a tuple with a predicate function (returns True if the value falls within acceptable limits, False otherwise),
# In addition, tuple contains start, end, and step values that will be used to test the formats table for internal consistency.
#
formatLimits = {
    'MonthName'         : (lambda v: 1 <=v and v < 13,                 1, 13),
    'Number'            : (lambda v: 0 <=v and v < 1000000,            0, 1001),

    'YearAD'            : (lambda v: 0 <=v and v < 2501,               0, 2501),
    'YearBC'            : (lambda v: 0 <=v and v < 4001,               0, 501),   # zh: has years as old as 前1700年
    'DecadeAD'          : (lambda v: 0 <=v and v < 2501,               0, 2501),  # At some point need to re-add  "and v%10==0" to the limitation
    'DecadeBC'          : (lambda v: 0 <=v and v < 4001,               0, 501),   # zh: has decades as old as 前1700年代
    'CenturyAD'         : (lambda v: 1 <=v and v < 41,                 1, 23),    # Some centuries use Roman numerals or a given list - do not exceed them in testing
    'CenturyBC'         : (lambda v: 1 <=v and v < 91,                 1, 23),    # Some centuries use Roman numerals or a given list - do not exceed them in testing
    'MillenniumAD'      : (lambda v: 1 <=v and v < 6,                  1, 4),     # For milleniums, only test first 3 AD Milleniums,
    'MillenniumBC'      : (lambda v: 1 <=v and v < 20,                 1, 2),     # And only 1 BC Millenium
    'CenturyAD_Cat'     : (lambda v: 1 <=v and v < 41,                 1, 23),    # Some centuries use Roman numerals or a given list - do not exceed them in testing
    'CenturyBC_Cat'     : (lambda v: 1 <=v and v < 41,                 1, 23),    # Some centuries use Roman numerals or a given list - do not exceed them in testing
    'Cat_Year_MusicAlbums' : (lambda v: 1950 <= v and v < 2021,        1950, 2021),
    'Cat_BirthsAD'      : (lambda v: 0 <=v and v < 2501,               0, 2501),
    'Cat_DeathsAD'      : (lambda v: 0 <=v and v < 2501,               0, 2501),
    'Cat_BirthsBC'      : (lambda v: 0 <=v and v < 4001,               0, 501),
    'Cat_DeathsBC'      : (lambda v: 0 <=v and v < 4001,               0, 501),
    'CurrEvents'        : (lambda v: 0 <= v and v < 1,                 0, 1),
}

# All month of year articles are in the same format
_formatLimit_MonthOfYear =  (lambda v: 1 <= 1900 and v < 2051,      1900, 2051)
for month in yrMnthFmts:
    formatLimits[month] = _formatLimit_MonthOfYear

_formatLimit_DayOfMonth31 = (lambda v: 1 <= v and v < 32,           1, 32)
_formatLimit_DayOfMonth30 = (lambda v: 1 <= v and v < 31,           1, 31)
_formatLimit_DayOfMonth29 = (lambda v: 1 <= v and v < 30,           1, 30)
for monthId in range(12):
    if (monthId + 1) in [1, 3, 5, 7, 8, 10, 12]:
        formatLimits[dayMnthFmts[monthId]] = _formatLimit_DayOfMonth31      # 31 days a month
    elif (monthId+1) == 2: # February
        formatLimits[dayMnthFmts[monthId]] = _formatLimit_DayOfMonth29      # 29 days a month
    else:
        formatLimits[dayMnthFmts[monthId]] = _formatLimit_DayOfMonth30      # 30 days a month

def getNumberOfDaysInMonth(month):
    """Returns the number of days in a given month, 1 being January, etc."""
    return formatLimits[dayMnthFmts[month-1]][2]-1

def getAutoFormat( lang, title, ignoreFirstLetterCase = True ):
    """Returns (dictName,value), where value can be a year, date, etc, and dictName is 'YearBC', 'December', etc."""
    for dictName, dict in formats.iteritems():
        try:
            year = dict[ lang ]( title )
            return dictName, year
        except:
            pass
    # sometimes the title may begin with an upper case while its listed as lower case, or the other way around
    # change case of the first character to the opposite, and try again
    if ignoreFirstLetterCase:
        try:
            if title[0].isupper():
                title = title[0].lower() + title[1:]
            else:
                title = title[0].upper() + title[1:]
            return getAutoFormat(lang, title, ignoreFirstLetterCase = False)
        except:
            pass
    return None, None


class FormatDate(object):
    def __init__(self, site):
        self.site = site

    def __call__(self, m, d):
        return formats['Day_' + enMonthNames[m-1]][self.site.code](d)


def formatYear(lang, year):
    if year < 0:
        return formats['YearBC'][lang](-year)
    else:
        return formats['YearAD'][lang](year)

#
#  Map testing methods
#

def printMonthArray( lang, pattern, capitalize ):
    """
    """
    for s in makeMonthNamedList( lang, pattern, capitalize ):
        pywikibot.output(s)

def testMapEntry( formatName, showAll = True, value = None ):
    """This is a test function, to be used interactivelly to test the validity of the above maps.
    To test, run this function with the map name, value to be tested, and the final value expected.
    Usage example:
        run python interpreter
        >>> import date
        >>> date.testMapEntry( 'DecadeAD', 1992, 1990 )
        >>> date.testMapEntry( 'CenturyAD', 20, 20 )
    """

    step = 1
    if formatName in decadeFormats: step = 10
    predicate,start,stop = formatLimits[formatName]
    if value is not None:
        start, stop = value, value+1
    if showAll:
        print(u"Processing %s with limits from %d to %d and step %d" % (formatName, start, stop - 1, step))

    for code, convFunc in formats[formatName].iteritems():
#        import time
#        startClock = time.clock()
        for value in range(start, stop, step):
            try:
                if not predicate(value):
                    raise AssertionError("     Not a valid value for this format.")
                newValue = convFunc(convFunc(value))
                if newValue != value:
                    raise AssertionError("     %s != %s: assert failed, values didn't match" % (newValue, value))
                if showAll:
                    print(u"date.formats['%s']['%s'](%d): '%s' -> %d" % (formatName, code, value, convFunc(value), newValue))
            except:
                print(u"********** Error in date.formats['%s']['%s'](%d)" % (formatName, code, value))
                raise
#        print( u"%s\t%s\t%f" % (formatName, code, time.clock() - startClock) )

def test(quick=False, showAll=False):
    """This is a test function, to be used interactively to test entire
    format conversion map at once

    Usage example:
        run python interpreter
        >>> import date
        >>> date.test()

    """
    for formatName in formats:

        if quick:
            testMapEntry( formatName, showAll, formatLimits[formatName][1] )     # Only test the first value in the test range
        else:
            testMapEntry( formatName, showAll )     # Extensive test!        # Test decade rounding
            print(u"'%s' complete." % formatName)
    if quick:
        #print(u'Date module quick consistency test passed')
        pass
    else:
        print(u'Date module has been fully tested')

# Do a quick test upon module loading!
# Make sure the date file is correct
test(quick=True)
