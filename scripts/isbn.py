#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This script reports and fixes invalid ISBN numbers.

Additionally, it can convert all ISBN-10 codes to the ISBN-13 format, and
correct the ISBN format by placing hyphens.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-to13             Converts all ISBN-10 codes to ISBN-13.
                  NOTE: This needn't be done, as MediaWiki still supports
                  (and will keep supporting) ISBN-10, and all libraries and
                  bookstores will most likely do so as well.

-format           Corrects the hyphenation.
                  NOTE: This is in here for testing purposes only. Usually
                  it's not worth to create an edit for such a minor issue.
                  The recommended way of doing this is enabling
                  cosmetic_changes, so that these changes are made on-the-fly
                  to all pages that are modified.

-always           Don't prompt you for each replacement.

-prop-isbn-10     Sets ISBN-10 property ID, so it's not tried to be found
                  automatically.
                  The usage is as follows: -prop-isbn-10:propid

-prop-isbn-13     Sets ISBN-13 property ID. The format and purpose is the
                  same as in -prop-isbn-10.

"""
#
# (C) Pywikibot team, 2009-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import re

from functools import partial

import pywikibot
from pywikibot import i18n, pagegenerators, textlib, Bot, WikidataBot

try:
    import stdnum.isbn
except ImportError:
    try:
        import isbnlib
    except ImportError:
        pass
    try:
        import isbn_hyphenate
    except ImportError:
        pass

docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}

# Maps each group number to the list of its publisher number ranges.
# Taken from https://web.archive.org/web/20090823122028/http://www.isbn-international.org/converter/ranges.htm
ranges = {
    '0': [  # English speaking area
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '949999'),
        ('9500000', '9999999'),
    ],
    '1': [  # English speaking area
        ('00', '09'),
        ('100', '399'),
        ('4000', '5499'),
        ('55000', '86979'),
        ('869800', '998999'),
    ],
    '2': [  # French speaking area
        ('00', '19'),
        ('200', '349'),
        ('35000', '39999'),
        ('400', '699'),
        ('7000', '8399'),
        ('84000', '89999'),
        ('900000', '949999'),
        ('9500000', '9999999'),
    ],
    '3': [  # German speaking area
        ('00', '02'),
        ('030', '033'),
        ('0340', '0369'),
        ('03700', '03999'),
        ('04', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '949999'),
        ('9500000', '9999999'),
    ],
    '4': [  # Japan
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '949999'),
        ('9500000', '9999999'),
    ],
    '5': [  # Russian Federation
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '909999'),
        ('91000', '91999'),
        ('9200', '9299'),
        ('93000', '94999'),
        ('9500', '9799'),
        ('98000', '98999'),
        ('9900000', '9909999'),
        ('9910', '9999'),
    ],
    '600': [  # Iran
        ('00', '09'),
        ('100', '499'),
        ('5000', '8999'),
        ('90000', '99999'),
    ],
    '601': [  # Kazakhstan
        ('00', '19'),
        ('200', '699'),
        ('7000', '7999'),
        ('80000', '84999'),
        ('85', '99'),
    ],
    '602': [  # Indonesia
        ('00', '19'),
        ('200', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '603': [  # Saudi Arabia
        ('00', '04'),
        ('500', '799'),
        ('8000', '8999'),
        ('90000', '99999'),
    ],
    '604': [  # Vietnam
        ('0', '4'),
        ('50', '89'),
        ('900', '979'),
        ('9800', '9999'),
    ],
    '605': [  # Turkey
        ('00', '09'),
        ('100', '399'),
        ('4000', '5999'),
        ('60000', '89999'),
    ],
    '7': [  # China, People's Republic
        ('00', '09'),
        ('100', '499'),
        ('5000', '7999'),
        ('80000', '89999'),
        ('900000', '999999'),
    ],
    '80': [  # Czech Republic; Slovakia
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '999999'),
    ],
    '81': [  # India
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '999999'),
    ],
    '82': [  # Norway
        ('00', '19'),
        ('200', '699'),
        ('7000', '8999'),
        ('90000', '98999'),
        ('990000', '999999'),
    ],
    '83': [  # Poland
        ('00', '19'),
        ('200', '599'),
        ('60000', '69999'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '999999'),
    ],
    '84': [  # Spain
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('9000', '9199'),
        ('920000', '923999'),
        ('92400', '92999'),
        ('930000', '949999'),
        ('95000', '96999'),
        ('9700', '9999'),
    ],
    '85': [  # Brazil
        ('00', '19'),
        ('200', '599'),
        ('60000', '69999'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '979999'),
        ('98000', '99999'),
    ],
    '86': [  # Serbia and Montenegro
        ('00', '29'),
        ('300', '599'),
        ('6000', '7999'),
        ('80000', '89999'),
        ('900000', '999999'),
    ],
    '87': [  # Denmark
        ('00', '29'),
        ('400', '649'),
        ('7000', '7999'),
        ('85000', '94999'),
        ('970000', '999999'),
    ],
    '88': [  # Italian speaking area
        ('00', '19'),
        ('200', '599'),
        ('6000', '8499'),
        ('85000', '89999'),
        ('900000', '949999'),
        ('95000', '99999'),
    ],
    '89': [  # Korea
        ('00', '24'),
        ('250', '549'),
        ('5500', '8499'),
        ('85000', '94999'),
        ('950000', '999999'),
    ],
    '90': [  # Netherlands, Belgium (Flemish)
        ('00', '19'),
        ('200', '499'),
        ('5000', '6999'),
        ('70000', '79999'),
        ('800000', '849999'),
        ('8500', '8999'),
        ('900000', '909999'),
        ('940000', '949999'),
    ],
    '91': [  # Sweden
        ('0', '1'),
        ('20', '49'),
        ('500', '649'),
        ('7000', '7999'),
        ('85000', '94999'),
        ('970000', '999999'),
    ],
    '92': [  # International Publishers (Unesco, EU), European Community Organizations
        ('0', '5'),
        ('60', '79'),
        ('800', '899'),
        ('9000', '9499'),
        ('95000', '98999'),
        ('990000', '999999'),
    ],
    '93': [  # India - no ranges fixed yet
    ],
    '950': [  # Argentina
        ('00', '49'),
        ('500', '899'),
        ('9000', '9899'),
        ('99000', '99999'),
    ],
    '951': [  # Finland
        ('0', '1'),
        ('20', '54'),
        ('550', '889'),
        ('8900', '9499'),
        ('95000', '99999'),
    ],
    '952': [  # Finland
        ('00', '19'),
        ('200', '499'),
        ('5000', '5999'),
        ('60', '65'),
        ('6600', '6699'),
        ('67000', '69999'),
        ('7000', '7999'),
        ('80', '94'),
        ('9500', '9899'),
        ('99000', '99999'),
    ],
    '953': [  # Croatia
        ('0', '0'),
        ('10', '14'),
        ('150', '549'),
        ('55000', '59999'),
        ('6000', '9499'),
        ('95000', '99999'),
    ],
    '954': [  # Bulgaria
        ('00', '29'),
        ('300', '799'),
        ('8000', '8999'),
        ('90000', '92999'),
        ('9300', '9999'),
    ],
    '955': [  # Sri Lanka
        ('0', '0'),
        ('1000', '1999'),
        ('20', '54'),
        ('550', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '956': [  # Chile
        ('00', '19'),
        ('200', '699'),
        ('7000', '9999'),
    ],
    '957': [  # Taiwan, China
        ('00', '02'),
        ('0300', '0499'),
        ('05', '19'),
        ('2000', '2099'),
        ('21', '27'),
        ('28000', '30999'),
        ('31', '43'),
        ('440', '819'),
        ('8200', '9699'),
        ('97000', '99999'),
    ],
    '958': [  # Colombia
        ('00', '59'),
        ('600', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '959': [  # Cuba
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
    ],
    '960': [  # Greece
        ('00', '19'),
        ('200', '659'),
        ('6600', '6899'),
        ('690', '699'),
        ('7000', '8499'),
        ('85000', '99999'),
    ],
    '961': [  # Slovenia
        ('00', '19'),
        ('200', '599'),
        ('6000', '8999'),
        ('90000', '94999'),
    ],
    '962': [  # Hong Kong
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '86999'),
        ('8700', '8999'),
        ('900', '999'),
    ],
    '963': [  # Hungary
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('9000', '9999'),
    ],
    '964': [  # Iran
        ('00', '14'),
        ('150', '249'),
        ('2500', '2999'),
        ('300', '549'),
        ('5500', '8999'),
        ('90000', '96999'),
        ('970', '989'),
        ('9900', '9999'),
    ],
    '965': [  # Israel
        ('00', '19'),
        ('200', '599'),
        ('7000', '7999'),
        ('90000', '99999'),
    ],
    '966': [  # Ukraine
        ('00', '19'),
        ('2000', '2999'),
        ('300', '699'),
        ('7000', '8999'),
        ('90000', '99999'),
    ],
    '967': [  # Malaysia
        ('00', '29'),
        ('300', '499'),
        ('5000', '5999'),
        ('60', '89'),
        ('900', '989'),
        ('9900', '9989'),
        ('99900', '99999'),
    ],
    '968': [  # Mexico
        ('01', '39'),
        ('400', '499'),
        ('5000', '7999'),
        ('800', '899'),
        ('9000', '9999'),
    ],
    '969': [  # Pakistan
        ('0', '1'),
        ('20', '39'),
        ('400', '799'),
        ('8000', '9999'),
    ],
    '970': [  # Mexico
        ('01', '59'),
        ('600', '899'),
        ('9000', '9099'),
        ('91000', '96999'),
        ('9700', '9999'),
    ],
    '971': [  # Philippines?
        ('000', '019'),
        ('02', '02'),
        ('0300', '0599'),
        ('06', '09'),
        ('10', '49'),
        ('500', '849'),
        ('8500', '9099'),
        ('91000', '99999'),
    ],
    '972': [  # Portugal
        ('0', '1'),
        ('20', '54'),
        ('550', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '973': [  # Romania
        ('0', '0'),
        ('100', '169'),
        ('1700', '1999'),
        ('20', '54'),
        ('550', '759'),
        ('7600', '8499'),
        ('85000', '88999'),
        ('8900', '9499'),
        ('95000', '99999'),
    ],
    '974': [  # Thailand
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('90000', '94999'),
        ('9500', '9999'),
    ],
    '975': [  # Turkey
        ('00000', '00999'),
        ('01', '24'),
        ('250', '599'),
        ('6000', '9199'),
        ('92000', '98999'),
        ('990', '999'),
    ],
    '976': [  # Caribbean Community
        ('0', '3'),
        ('40', '59'),
        ('600', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '977': [  # Egypt
        ('00', '19'),
        ('200', '499'),
        ('5000', '6999'),
        ('700', '999'),
    ],
    '978': [  # Nigeria
        ('000', '199'),
        ('2000', '2999'),
        ('30000', '79999'),
        ('8000', '8999'),
        ('900', '999'),
    ],
    '979': [  # Indonesia
        ('000', '099'),
        ('1000', '1499'),
        ('15000', '19999'),
        ('20', '29'),
        ('3000', '3999'),
        ('400', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '980': [  # Venezuela
        ('00', '19'),
        ('200', '599'),
        ('6000', '9999'),
    ],
    '981': [  # Singapore
        ('00', '19'),
        ('200', '299'),
        ('3000', '9999'),
    ],
    '982': [  # South Pacific
        ('00', '09'),
        ('100', '699'),
        ('70', '89'),
        ('9000', '9999'),
    ],
    '983': [  # Malaysia
        ('00', '01'),
        ('020', '199'),
        ('2000', '3999'),
        ('40000', '44999'),
        ('45', '49'),
        ('50', '79'),
        ('800', '899'),
        ('9000', '9899'),
        ('99000', '99999'),
    ],
    '984': [  # Bangladesh
        ('00', '39'),
        ('400', '799'),
        ('8000', '8999'),
        ('90000', '99999'),
    ],
    '985': [  # Belarus
        ('00', '39'),
        ('400', '599'),
        ('6000', '8999'),
        ('90000', '99999'),
    ],
    '986': [  # Taiwan, China
        ('00', '11'),
        ('120', '559'),
        ('5600', '7999'),
        ('80000', '99999'),
    ],
    '987': [  # Argentina
        ('00', '09'),
        ('1000', '1999'),
        ('20000', '29999'),
        ('30', '49'),
        ('500', '899'),
        ('9000', '9499'),
        ('95000', '99999'),
    ],
    '988': [  # Hongkong
        ('00', '16'),
        ('17000', '19999'),
        ('200', '799'),
        ('8000', '9699'),
        ('97000', '99999'),
    ],
    '989': [  # Portugal
        ('0', '1'),
        ('20', '54'),
        ('550', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '9937': [  # Nepal
        ('0', '2'),
        ('30', '49'),
        ('500', '799'),
        ('8000', '9999'),
    ],
    '9938': [  # Tunisia
        ('00', '79'),
        ('800', '949'),
        ('9500', '9999'),
    ],
    '9939': [  # Armenia
        ('0', '4'),
        ('50', '79'),
        ('800', '899'),
        ('9000', '9999'),
    ],
    '9940': [  # Montenegro
        ('0', '1'),
        ('20', '49'),
        ('500', '899'),
        ('9000', '9999'),
    ],
    '9941': [  # Georgia
        ('0', '0'),
        ('10', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9942': [  # Ecuador
        ('00', '89'),
        ('900', '994'),
        ('9950', '9999'),
    ],
    '9943': [  # Uzbekistan
        ('00', '29'),
        ('300', '399'),
        ('4000', '9999'),
    ],
    '9944': [  # Turkey
        ('0', '2'),
        ('300', '499'),
        ('5000', '5999'),
        ('60', '89'),
        ('900', '999'),
    ],
    '9945': [  # Dominican Republic
        ('00', '00'),
        ('010', '079'),
        ('08', '39'),
        ('400', '569'),
        ('57', '57'),
        ('580', '849'),
        ('8500', '9999'),
    ],
    '9946': [  # Korea, P.D.R.
        ('0', '1'),
        ('20', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9947': [  # Algeria
        ('0', '1'),
        ('20', '79'),
        ('800', '999'),
    ],
    '9948': [  # United Arab Emirates
        ('00', '39'),
        ('400', '849'),
        ('8500', '9999'),
    ],
    '9949': [  # Estonia
        ('0', '0'),
        ('10', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9950': [  # Palestine
        ('00', '29'),
        ('300', '840'),
        ('8500', '9999'),
    ],
    '9951': [  # Kosova
        ('00', '39'),
        ('400', '849'),
        ('8500', '9999'),
    ],
    '9952': [  # Azerbaijan
        ('0', '1'),
        ('20', '39'),
        ('400', '799'),
        ('8000', '9999'),
    ],
    '9953': [  # Lebanon
        ('0', '0'),
        ('10', '39'),
        ('400', '599'),
        ('60', '89'),
        ('9000', '9999'),
    ],
    '9954': [  # Morocco
        ('0', '1'),
        ('20', '39'),
        ('400', '799'),
        ('8000', '9999'),
    ],
    '9955': [  # Lithuania
        ('00', '39'),
        ('400', '929'),
        ('9300', '9999'),
    ],
    '9956': [  # Cameroon
        ('0', '0'),
        ('10', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9957': [  # Jordan
        ('00', '39'),
        ('400', '699'),
        ('70', '84'),
        ('8500', '9999'),
    ],
    '9958': [  # Bosnia and Herzegovina
        ('0', '0'),
        ('10', '49'),
        ('500', '899'),
        ('9000', '9999'),
    ],
    '9959': [  # Libya
        ('0', '1'),
        ('20', '79'),
        ('800', '949'),
        ('9500', '9999'),
    ],
    '9960': [  # Saudi Arabia
        ('00', '59'),
        ('600', '899'),
        ('9000', '9999'),
    ],
    '9961': [  # Algeria
        ('0', '2'),
        ('30', '69'),
        ('700', '949'),
        ('9500', '9999'),
    ],
    '9962': [  # Panama
        ('00', '54'),
        ('5500', '5599'),
        ('56', '59'),
        ('600', '849'),
        ('8500', '9999'),
    ],
    '9963': [  # Cyprus
        ('0', '2'),
        ('30', '54'),
        ('550', '749'),
        ('7500', '9999'),
    ],
    '9964': [  # Ghana
        ('0', '6'),
        ('70', '94'),
        ('950', '999'),
    ],
    '9965': [  # Kazakhstan
        ('00', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9966': [  # Kenya
        ('00', '69'),
        ('7000', '7499'),
        ('750', '959'),
        ('9600', '9999'),
    ],
    '9967': [  # Kyrgyzstan
        ('00', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9968': [  # Costa Rica
        ('00', '49'),
        ('500', '939'),
        ('9400', '9999'),
    ],
    '9970': [  # Uganda
        ('00', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9971': [  # Singapore
        ('0', '5'),
        ('60', '89'),
        ('900', '989'),
        ('9900', '9999'),
    ],
    '9972': [  # Peru
        ('00', '09'),
        ('1', '1'),
        ('200', '249'),
        ('2500', '2999'),
        ('30', '59'),
        ('600', '899'),
        ('9000', '9999'),
    ],
    '9973': [  # Tunisia
        ('0', '05'),
        ('060', '089'),
        ('0900', '0999'),
        ('10', '69'),
        ('700', '969'),
        ('9700', '9999'),
    ],
    '9974': [  # Uruguay
        ('0', '2'),
        ('30', '54'),
        ('550', '749'),
        ('7500', '9499'),
        ('95', '99'),
    ],
    '9975': [  # Moldova
        ('0', '0'),
        ('100', '399'),
        ('4000', '4499'),
        ('45', '89'),
        ('900', '949'),
        ('9500', '9999'),
    ],
    '9976': [  # Tanzania
        ('0', '5'),
        ('60', '89'),
        ('900', '989'),
        ('9990', '9999'),
    ],
    '9977': [  # Costa Rica
        ('00', '89'),
        ('900', '989'),
        ('9900', '9999'),
    ],
    '9978': [  # Ecuador
        ('00', '29'),
        ('300', '399'),
        ('40', '94'),
        ('950', '989'),
        ('9900', '9999'),
    ],
    '9979': [  # Iceland
        ('0', '4'),
        ('50', '64'),
        ('650', '659'),
        ('66', '75'),
        ('760', '899'),
        ('9000', '9999'),
    ],
    '9980': [  # Papua New Guinea
        ('0', '3'),
        ('40', '89'),
        ('900', '989'),
        ('9900', '9999'),
    ],
    '9981': [  # Morocco
        ('00', '09'),
        ('100', '159'),
        ('1600', '1999'),
        ('20', '79'),
        ('800', '949'),
        ('9500', '9999'),
    ],
    '9982': [  # Zambia
        ('00', '79'),
        ('800', '989'),
        ('9900', '9999'),
    ],
    '9983': [  # Gambia
        ('80', '94'),
        ('950', '989'),
        ('9900', '9999'),
    ],
    '9984': [  # Latvia
        ('00', '49'),
        ('500', '899'),
        ('9000', '9999'),
    ],
    '9985': [  # Estonia
        ('0', '4'),
        ('50', '79'),
        ('800', '899'),
        ('9000', '9999'),
    ],
    '9986': [  # Lithuania
        ('00', '39'),
        ('400', '899'),
        ('9000', '9399'),
        ('940', '969'),
        ('97', '99'),
    ],
    '9987': [  # Tanzania
        ('00', '39'),
        ('400', '879'),
        ('8800', '9999'),
    ],
    '9988': [  # Ghana
        ('0', '2'),
        ('30', '54'),
        ('550', '749'),
        ('7500', '9999'),
    ],
    '9989': [  # Macedonia
        ('0', '0'),
        ('100', '199'),
        ('2000', '2999'),
        ('30', '59'),
        ('600', '949'),
        ('9500', '9999'),
    ],
    '99901': [  # Bahrain
        ('00', '49'),
        ('500', '799'),
        ('80', '99'),
    ],
    '99902': [  # Gabon - no ranges fixed yet
    ],
    '99903': [  # Mauritius
        ('0', '1'),
        ('20', '89'),
        ('900', '999'),
    ],
    '99904': [  # Netherlands Antilles; Aruba, Neth. Ant
        ('0', '5'),
        ('60', '89'),
        ('900', '999'),
    ],
    '99905': [  # Bolivia
        ('0', '3'),
        ('40', '79'),
        ('800', '999'),
    ],
    '99906': [  # Kuwait
        ('0', '2'),
        ('30', '59'),
        ('600', '699'),
        ('70', '89'),
        ('9', '9'),
    ],
    '99908': [  # Malawi
        ('0', '0'),
        ('10', '89'),
        ('900', '999'),
    ],
    '99909': [  # Malta
        ('0', '3'),
        ('40', '94'),
        ('950', '999'),
    ],
    '99910': [  # Sierra Leone
        ('0', '2'),
        ('30', '89'),
        ('900', '999'),
    ],
    '99911': [  # Lesotho
        ('00', '59'),
        ('600', '999'),
    ],
    '99912': [  # Botswana
        ('0', '3'),
        ('400', '599'),
        ('60', '89'),
        ('900', '999'),
    ],
    '99913': [  # Andorra
        ('0', '2'),
        ('30', '35'),
        ('600', '604'),
    ],
    '99914': [  # Suriname
        ('0', '4'),
        ('50', '89'),
        ('900', '949'),
    ],
    '99915': [  # Maldives
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99916': [  # Namibia
        ('0', '2'),
        ('30', '69'),
        ('700', '999'),
    ],
    '99917': [  # Brunei Darussalam
        ('0', '2'),
        ('30', '89'),
        ('900', '999'),
    ],
    '99918': [  # Faroe Islands
        ('0', '3'),
        ('40', '79'),
        ('800', '999'),
    ],
    '99919': [  # Benin
        ('0', '2'),
        ('40', '69'),
        ('900', '999'),
    ],
    '99920': [  # Andorra
        ('0', '4'),
        ('50', '89'),
        ('900', '999'),
    ],
    '99921': [  # Qatar
        ('0', '1'),
        ('20', '69'),
        ('700', '799'),
        ('8', '8'),
        ('90', '99'),
    ],
    '99922': [  # Guatemala
        ('0', '3'),
        ('40', '69'),
        ('700', '999'),
    ],
    '99923': [  # El Salvador
        ('0', '1'),
        ('20', '79'),
        ('800', '999'),
    ],
    '99924': [  # Nicaragua
        ('0', '2'),
        ('30', '79'),
        ('800', '999'),
    ],
    '99925': [  # Paraguay
        ('0', '3'),
        ('40', '79'),
        ('800', '999'),
    ],
    '99926': [  # Honduras
        ('0', '0'),
        ('10', '59'),
        ('600', '999'),
    ],
    '99927': [  # Albania
        ('0', '2'),
        ('30', '59'),
        ('600', '999'),
    ],
    '99928': [  # Georgia
        ('0', '0'),
        ('10', '79'),
        ('800', '999'),
    ],
    '99929': [  # Mongolia
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99930': [  # Armenia
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99931': [  # Seychelles
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99932': [  # Malta
        ('0', '0'),
        ('10', '59'),
        ('600', '699'),
        ('7', '7'),
        ('80', '99'),
    ],
    '99933': [  # Nepal
        ('0', '2'),
        ('30', '59'),
        ('600', '999'),
    ],
    '99934': [  # Dominican Republic
        ('0', '1'),
        ('20', '79'),
        ('800', '999'),
    ],
    '99935': [  # Haiti
        ('0', '2'),
        ('7', '8'),
        ('30', '59'),
        ('600', '699'),
        ('90', '99'),
    ],
    '99936': [  # Bhutan
        ('0', '0'),
        ('10', '59'),
        ('600', '999'),
    ],
    '99937': [  # Macau
        ('0', '1'),
        ('20', '59'),
        ('600', '999'),
    ],
    '99938': [  # Srpska
        ('0', '1'),
        ('20', '59'),
        ('600', '899'),
        ('90', '99'),
    ],
    '99939': [  # Guatemala
        ('0', '5'),
        ('60', '89'),
        ('900', '999'),
    ],
    '99940': [  # Georgia
        ('0', '0'),
        ('10', '69'),
        ('700', '999'),
    ],
    '99941': [  # Armenia
        ('0', '2'),
        ('30', '79'),
        ('800', '999'),
    ],
    '99942': [  # Sudan
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99943': [  # Alsbania
        ('0', '2'),
        ('30', '59'),
        ('600', '999'),
    ],
    '99944': [  # Ethiopia
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99945': [  # Namibia
        ('0', '5'),
        ('60', '89'),
        ('900', '999'),
    ],
    '99946': [  # Nepal
        ('0', '2'),
        ('30', '59'),
        ('600', '999'),
    ],
    '99947': [  # Tajikistan
        ('0', '2'),
        ('30', '69'),
        ('700', '999'),
    ],
    '99948': [  # Eritrea
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99949': [  # Mauritius
        ('0', '1'),
        ('20', '89'),
        ('900', '999'),
    ],
    '99950': [  # Cambodia
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99951': [  # Congo - no ranges fixed yet
    ],
    '99952': [  # Mali
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99953': [  # Paraguay
        ('0', '2'),
        ('30', '79'),
        ('800', '999'),
    ],
    '99954': [  # Bolivia
        ('0', '2'),
        ('30', '69'),
        ('700', '999'),
    ],
    '99955': [  # Srpska
        ('0', '1'),
        ('20', '59'),
        ('600', '899'),
        ('90', '99'),
    ],
    '99956': [  # Albania
        ('00', '59'),
        ('600', '999'),
    ],
}


class InvalidIsbnException(pywikibot.Error):

    """Invalid ISBN."""


class ISBN:

    """Abstract superclass."""

    def format(self):
        """Put hyphens into this ISBN number."""
        result = ''
        rest = ''
        for digit in self.digits():
            rest += str(digit)
        # Determine the prefix (if any)
        for prefix in self.possiblePrefixes():
            if rest.startswith(prefix):
                result += prefix + '-'
                rest = rest[len(prefix):]
                break

        # Determine the group
        for groupNumber in ranges.keys():
            if rest.startswith(groupNumber):
                result += groupNumber + '-'
                rest = rest[len(groupNumber):]
                publisherRanges = ranges[groupNumber]
                break
        else:
            raise InvalidIsbnException('ISBN %s: group number unknown.'
                                       % self.code)

        # Determine the publisher
        for (start, end) in publisherRanges:
            length = len(start)  # NOTE: start and end always have equal length
            if rest[:length] >= start and rest[:length] <= end:
                result += rest[:length] + '-'
                rest = rest[length:]
                break
        else:
            raise InvalidIsbnException('ISBN %s: publisher number unknown.'
                                       % self.code)

        # The rest is the item number and the 1-digit checksum.
        result += rest[:-1] + '-' + rest[-1]
        self.code = result


class ISBN13(ISBN):

    """ISBN 13."""

    def __init__(self, code, checksumMissing=False):
        self.code = code
        if checksumMissing:
            self.code += str(self.calculateChecksum())
        self.checkValidity()

    def possiblePrefixes(self):
        return ['978', '979']

    def digits(self):
        """Return a list of the digits in the ISBN code."""
        result = []
        for c in self.code:
            if c.isdigit():
                result.append(int(c))
            elif c != '-':
                raise InvalidIsbnException(
                    'The ISBN %s contains invalid characters.' % self.code)
        return result

    def checkValidity(self):
        if len(self.digits()) != 13:
            raise InvalidIsbnException('The ISBN %s is not 13 digits long.'
                                       % self.code)
        if self.calculateChecksum() != self.digits()[-1]:
            raise InvalidIsbnException('The ISBN checksum of %s is incorrect.'
                                       % self.code)

    def calculateChecksum(self):
        # See https://en.wikipedia.org/wiki/ISBN#Check_digit_in_ISBN_13
        sum = 0
        for i in range(0, 13 - 1, 2):
            sum += self.digits()[i]
        for i in range(1, 13 - 1, 2):
            sum += 3 * self.digits()[i]
        return (10 - (sum % 10)) % 10


class ISBN10(ISBN):

    """ISBN 10."""

    def __init__(self, code):
        self.code = code
        self.checkValidity()

    def possiblePrefixes(self):
        return []

    def digits(self):
        """Return a list of the digits and Xs in the ISBN code."""
        result = []
        for c in self.code:
            if c.isdigit() or c in 'Xx':
                result.append(c)
            elif c != '-':
                raise InvalidIsbnException(
                    'The ISBN %s contains invalid characters.' % self.code)
        return result

    def checkChecksum(self):
        """Raise an InvalidIsbnException if the ISBN checksum is incorrect."""
        # See https://en.wikipedia.org/wiki/ISBN#Check_digit_in_ISBN_10
        sum = 0
        for i in range(0, 9):
            sum += (i + 1) * int(self.digits()[i])
        checksum = sum % 11
        lastDigit = self.digits()[-1]
        if not ((checksum == 10 and lastDigit in 'Xx') or
                (lastDigit.isdigit() and checksum == int(lastDigit))):
            raise InvalidIsbnException('The ISBN checksum of %s is incorrect.'
                                       % self.code)

    def checkValidity(self):
        if len(self.digits()) != 10:
            raise InvalidIsbnException('The ISBN %s is not 10 digits long.'
                                       % self.code)
        if 'X' in self.digits()[:-1] or 'x' in self.digits()[:-1]:
            raise InvalidIsbnException(
                'ISBN %s: X is only allowed at the end of the ISBN.'
                % self.code)
        self.checkChecksum()

    def toISBN13(self):
        """
        Create a 13-digit ISBN from this 10-digit ISBN.

        Adds the GS1 prefix '978' and recalculates the checksum.
        The hyphenation structure is taken from the format of the original
        ISBN number.

        @rtype: L{ISBN13}
        """
        code = '978-' + self.code[:-1]
        return ISBN13(code, checksumMissing=True)

    def format(self):
        # load overridden superclass method
        ISBN.format(self)
        # capitalize checksum
        if self.code[-1] == 'x':
            self.code = self.code[:-1] + 'X'


def getIsbn(code):
    """Return an ISBN object for the code."""
    try:
        i = ISBN13(code)
    except InvalidIsbnException as e13:
        try:
            i = ISBN10(code)
        except InvalidIsbnException as e10:
            raise InvalidIsbnException(u'ISBN-13: %s / ISBN-10: %s'
                                       % (e13, e10))
    return i


def is_valid(isbn):
    """Check whether an ISBN 10 or 13 is valid."""
    # isbnlib marks any ISBN10 with lowercase 'X' as invalid
    isbn = isbn.upper()
    try:
        stdnum.isbn
    except NameError:
        pass
    else:
        try:
            stdnum.isbn.validate(isbn)
        except stdnum.isbn.InvalidFormat as e:
            raise InvalidIsbnException(str(e))
        except stdnum.isbn.InvalidChecksum as e:
            raise InvalidIsbnException(str(e))
        except stdnum.isbn.InvalidLength as e:
            raise InvalidIsbnException(str(e))
        return True

    try:
        isbnlib
    except NameError:
        pass
    else:
        if isbnlib.notisbn(isbn):
            raise InvalidIsbnException('Invalid ISBN found')
        return True

    getIsbn(isbn)
    return True


def _hyphenateIsbnNumber(match):
    """Helper function to deal with a single ISBN."""
    isbn = match.group('code')
    isbn = isbn.upper()
    try:
        is_valid(isbn)
    except InvalidIsbnException:
        return isbn

    try:
        stdnum.isbn
    except NameError:
        pass
    else:
        i = stdnum.isbn.format(isbn)
        return i

    try:
        isbn_hyphenate
    except NameError:
        pass
    else:
        try:
            i = isbn_hyphenate.hyphenate(isbn)
        except (isbn_hyphenate.IsbnMalformedError,
                isbn_hyphenate.IsbnUnableToHyphenateError):
            return isbn
        return i

    i = getIsbn(isbn)
    i.format()
    return i.code


hyphenateIsbnNumbers = partial(textlib.reformat_ISBNs,
                               match_func=_hyphenateIsbnNumber)


def _isbn10toIsbn13(match):
    """Helper function to deal with a single ISBN."""
    isbn = match.group('code')
    isbn = isbn.upper()
    try:
        stdnum.isbn
    except NameError:
        pass
    else:
        try:
            is_valid(isbn)
        except InvalidIsbnException:
            return isbn
        i = stdnum.isbn.to_isbn13(isbn)
        return i

    try:
        isbnlib
    except NameError:
        pass
    else:
        try:
            is_valid(isbn)
        except InvalidIsbnException:
            return isbn
        # remove hyphenation, otherwise isbnlib.to_isbn13() returns None
        i = isbnlib.canonical(isbn)
        if i == isbn:
            i13 = isbnlib.to_isbn13(i)
            return i13
        # add removed hyphenation
        i13 = isbnlib.to_isbn13(i)
        i13h = hyphenateIsbnNumbers('ISBN ' + i13)
        return i13h[5:]

    try:
        is_valid(isbn)
    except InvalidIsbnException:
        # don't change
        return isbn
    i13 = getIsbn(isbn).toISBN13()
    return i13.code


def convertIsbn10toIsbn13(text):
    """Helper function to convert ISBN 10 to ISBN 13."""
    isbnR = re.compile(r'(?<=ISBN )(?P<code>[\d\-]+[Xx]?)')
    text = isbnR.sub(_isbn10toIsbn13, text)
    return text


class IsbnBot(Bot):

    """ISBN bot."""

    def __init__(self, generator, **kwargs):
        self.availableOptions.update({
            'to13': False,
            'format': False,
        })
        super(IsbnBot, self).__init__(**kwargs)

        self.generator = generator
        self.isbnR = re.compile(r'(?<=ISBN )(?P<code>[\d\-]+[Xx]?)')
        self.comment = i18n.twtranslate(pywikibot.Site(), 'isbn-formatting')

    def treat(self, page):
        try:
            old_text = page.get()
            for match in self.isbnR.finditer(old_text):
                isbn = match.group('code')
                try:
                    is_valid(isbn)
                except InvalidIsbnException as e:
                    pywikibot.output(e)

            new_text = old_text
            if self.getOption('to13'):
                new_text = self.isbnR.sub(_isbn10toIsbn13, new_text)

            if self.getOption('format'):
                new_text = self.isbnR.sub(_hyphenateIsbnNumber, new_text)
            try:
                self.userPut(page, page.text, new_text, summary=self.comment)
            except pywikibot.EditConflict:
                pywikibot.output(u'Skipping %s because of edit conflict'
                                 % page.title())
            except pywikibot.SpamfilterError as e:
                pywikibot.output(
                    u'Cannot change %s because of blacklist entry %s'
                    % (page.title(), e.url))
            except pywikibot.LockedPage:
                pywikibot.output(u'Skipping %s (locked page)'
                                 % page.title())
        except pywikibot.NoPage:
            pywikibot.output(u"Page %s does not exist"
                             % page.title(asLink=True))
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"Page %s is a redirect; skipping."
                             % page.title(asLink=True))

    def run(self):
        for page in self.generator:
            self.treat(page)


class IsbnWikibaseBot(WikidataBot):

    """ISBN bot to be run on Wikibase sites."""

    def __init__(self, generator, **kwargs):
        self.availableOptions.update({
            'to13': False,
            'format': False,
        })
        self.isbn_10_prop_id = kwargs.pop('prop-isbn-10', None)
        self.isbn_13_prop_id = kwargs.pop('prop-isbn-13', None)

        super(IsbnWikibaseBot, self).__init__(use_from_page=None, **kwargs)

        self.generator = generator
        if self.isbn_10_prop_id is None:
            self.isbn_10_prop_id = self.get_property_by_name('ISBN-10')
        if self.isbn_13_prop_id is None:
            self.isbn_13_prop_id = self.get_property_by_name('ISBN-13')
        self.comment = i18n.twtranslate(pywikibot.Site(), 'isbn-formatting')

    def treat(self, page, item):
        change_messages = []

        if self.isbn_10_prop_id in item.claims:
            for claim in item.claims[self.isbn_10_prop_id]:
                isbn = claim.getTarget()
                try:
                    is_valid(isbn)
                except InvalidIsbnException as e:
                    pywikibot.output(e)
                    continue

                old_isbn = "ISBN " + isbn

                if self.getOption('format'):
                    new_isbn = hyphenateIsbnNumbers(old_isbn)

                if self.getOption('to13'):
                    new_isbn = convertIsbn10toIsbn13(old_isbn)

                    item.claims[claim.getID()].remove(claim)
                    claim = pywikibot.Claim(self.repo, self.isbn_13_prop_id)
                    claim.setTarget(new_isbn)
                    if self.isbn_13_prop_id in item.claims:
                        item.claims[self.isbn_13_prop_id].append(claim)
                    else:
                        item.claims[self.isbn_13_prop_id] = [claim]
                    change_messages.append('Changing %s (%s) to %s (%s)' %
                                           (self.isbn_10_prop_id, old_isbn,
                                            self.isbn_13_prop_id, new_isbn))
                    continue

                if old_isbn == new_isbn:
                    continue
                # remove 'ISBN ' prefix
                assert(new_isbn.startswith('ISBN '))
                new_isbn = new_isbn[5:]
                claim.setTarget(new_isbn)
                change_messages.append('Changing %s (%s --> %s)' %
                                       (self.isbn_10_prop_id, old_isbn,
                                        new_isbn))

        # -format is the only option that has any effect on ISBN13
        if self.getOption('format') and self.isbn_13_prop_id in item.claims:
            for claim in item.claims[self.isbn_13_prop_id]:
                isbn = claim.getTarget()
                try:
                    is_valid(isbn)
                except InvalidIsbnException as e:
                    pywikibot.output(e)
                    continue

                old_isbn = "ISBN " + isbn
                new_isbn = hyphenateIsbnNumbers(old_isbn)
                if old_isbn == new_isbn:
                    continue
                change_messages.append(
                    'Changing %s (%s --> %s)' % (self.isbn_13_prop_id,
                                                 claim.getTarget(), new_isbn))
                claim.setTarget(new_isbn)

        if change_messages:
            self.current_page = item
            pywikibot.output('\n'.join(change_messages))
            self.user_edit_entity(item, summary=self.comment)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    options = {}

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    # Check whether we're running on Wikibase site or not
    # FIXME: See T85483 and run() in WikidataBot
    site = pywikibot.Site()
    data_site = site.data_repository()
    use_wikibase = (data_site is not None and
                    data_site.family == site.family and
                    data_site.code == site.code)

    for arg in local_args:
        if arg.startswith('-prop-isbn-10:'):
            options[arg[1:len('-prop-isbn-10')]] = arg[len('-prop-isbn-10:'):]
        elif arg.startswith('-prop-isbn-13:'):
            options[arg[1:len('-prop-isbn-13')]] = arg[len('-prop-isbn-13:'):]
        elif arg.startswith('-') and arg[1:] in ('always', 'to13', 'format'):
            options[arg[1:]] = True
        else:
            genFactory.handleArg(arg)

    gen = genFactory.getCombinedGenerator()
    if gen:
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        if use_wikibase:
            bot = IsbnWikibaseBot(preloadingGen, **options)
        else:
            bot = IsbnBot(preloadingGen, **options)
        bot.run()
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    main()
