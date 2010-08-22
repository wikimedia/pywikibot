#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
This script goes over multiple pages of the home wiki, and reports invalid
ISBN numbers.

Additionally, it can convert all ISBN-10 codes to the ISBN-13 format, and
correct the ISBN format by placing hyphens.

These command line parameters can be used to specify which pages to work on:

&params;

-namespace:n      Number or name of namespace to process. The parameter can be
                  used multiple times. It works in combination with all other
                  parameters, except for the -start parameter. If you e.g.
                  want to iterate over all categories starting at M, use
                  -start:Category:M.

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

"""

__version__='$Id$'

import pywikibot
from pywikibot import pagegenerators
import sys, re

docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}

# Summary messages in different languages
msg = {
    'ar': u'روبوت: تهيئة ISBN',
    'de': 'Bot: Formatiere ISBN',
    'en': 'Robot: Formatting ISBN',
    'fa': u'ربات:استانداردسازی شابک',
    'he': u'בוט: מעצב ISBN',
    'ja': u'ロボットによる ISBN の書式化',
    'nl': 'Bot: ISBN opgemaakt',
    'pt': u'Bot: Formatando ISBN',
    'zh': u'機器人：ISBN格式化',
}

# Maps each group number to the list of its publisher number ranges.
# Taken from http://www.isbn-international.org/converter/ranges.htm
ranges = {
    '0': [ # English speaking area
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '949999'),
        ('9500000', '9999999'),
    ],
    '1': [ # English speaking area
        ('00', '09'),
        ('100', '399'),
        ('4000', '5499'),
        ('55000', '86979'),
        ('869800', '998999'),
    ],
    '2': [ # French speaking area
        ('00', '19'),
        ('200', '349'),
        ('35000', '39999'),
        ('400', '699'),
        ('7000', '8399'),
        ('84000', '89999'),
        ('900000', '949999'),
        ('9500000', '9999999'),
    ],
    '3': [ # German speaking area
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
    '4': [ # Japan
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '949999'),
        ('9500000', '9999999'),
    ],
    '5': [ # Russian Federation
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
    '600': [ # Iran
        ('00', '09'),
        ('100', '499'),
        ('5000', '8999'),
        ('90000', '99999'),
    ],
    '601': [ # Kazakhstan
        ('00', '19'),
        ('200', '699'),
        ('7000', '7999'),
        ('80000', '84999'),
        ('85', '99'),
    ],
    '602': [ # Indonesia
        ('00', '19'),
        ('200', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '603': [ # Saudi Arabia
        ('00', '04'),
        ('500', '799'),
        ('8000', '8999'),
        ('90000', '99999'),
    ],
    '604': [ # Vietnam
        ('0', '4'),
        ('50', '89'),
        ('900', '979'),
        ('9800', '9999'),
    ],
    '605': [ # Turkey
        ('00', '09'),
        ('100', '399'),
        ('4000', '5999'),
        ('60000', '89999'),
    ],
    '7': [ # China, People's Republic
        ('00', '09'),
        ('100', '499'),
        ('5000', '7999'),
        ('80000', '89999'),
        ('900000', '999999'),
    ],
    '80': [ # Czech Republic; Slovakia
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '999999'),
    ],
    '81': [ # India
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '999999'),
    ],
    '82': [ # Norway
        ('00', '19'),
        ('200', '699'),
        ('7000', '8999'),
        ('90000', '98999'),
        ('990000', '999999'),
    ],
    '83': [ # Poland
        ('00', '19'),
        ('200', '599'),
        ('60000', '69999'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '999999'),
    ],
    '84': [ # Spain
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
    '85': [ # Brazil
        ('00', '19'),
        ('200', '599'),
        ('60000', '69999'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('900000', '979999'),
        ('98000', '99999'),
    ],
    '86': [ # Serbia and Montenegro
        ('00', '29'),
        ('300', '599'),
        ('6000', '7999'),
        ('80000', '89999'),
        ('900000', '999999'),
    ],
    '87': [ # Denmark
        ('00', '29'),
        ('400', '649'),
        ('7000', '7999'),
        ('85000', '94999'),
        ('970000', '999999'),
    ],
    '88': [ # Italian speaking area
        ('00', '19'),
        ('200', '599'),
        ('6000', '8499'),
        ('85000', '89999'),
        ('900000', '949999'),
        ('95000', '99999'),
    ],
    '89': [ # Korea
        ('00', '24'),
        ('250', '549'),
        ('5500', '8499'),
        ('85000', '94999'),
        ('950000', '999999'),
    ],
    '90': [ # Netherlands, Belgium (Flemish)
        ('00', '19'),
        ('200', '499'),
        ('5000', '6999'),
        ('70000', '79999'),
        ('800000', '849999'),
        ('8500', '8999'),
        ('900000', '909999'),
        ('940000', '949999'),
    ],
    '91': [ # Sweden
        ('0', '1'),
        ('20', '49'),
        ('500', '649'),
        ('7000', '7999'),
        ('85000', '94999'),
        ('970000', '999999'),
    ],
    '92': [ # International Publishers (Unesco, EU), European Community Organizations
        ('0', '5'),
        ('60', '79'),
        ('800', '899'),
        ('9000', '9499'),
        ('95000', '98999'),
        ('990000', '999999'),
    ],
    '93': [ # India - no ranges fixed yet
    ],
    '950': [ # Argentina
        ('00', '49'),
        ('500', '899'),
        ('9000', '9899'),
        ('99000', '99999'),
    ],
    '951': [ # Finland
        ('0', '1'),
        ('20', '54'),
        ('550', '889'),
        ('8900', '9499'),
        ('95000', '99999'),
    ],
    '952': [ # Finland
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
    '953': [ # Croatia
        ('0', '0'),
        ('10', '14'),
        ('150', '549'),
        ('55000', '59999'),
        ('6000', '9499'),
        ('95000', '99999'),
    ],
    '954': [ # Bulgaria
        ('00', '29'),
        ('300', '799'),
        ('8000', '8999'),
        ('90000', '92999'),
        ('9300', '9999'),
    ],
    '955': [ # Sri Lanka
        ('0', '0'),
        ('1000', '1999'),
        ('20', '54'),
        ('550', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '956': [ # Chile
        ('00', '19'),
        ('200', '699'),
        ('7000', '9999'),
    ],
    '957': [ # Taiwan, China
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
    '958': [ # Colombia
        ('00', '59'),
        ('600', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '959': [ # Cuba
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
    ],
    '960': [ # Greece
        ('00', '19'),
        ('200', '659'),
        ('6600', '6899'),
        ('690', '699'),
        ('7000', '8499'),
        ('85000', '99999'),
    ],
    '961': [ # Slovenia
        ('00', '19'),
        ('200', '599'),
        ('6000', '8999'),
        ('90000', '94999'),
    ],
    '962': [ # Hong Kong
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '86999'),
        ('8700', '8999'),
        ('900', '999'),
    ],
    '963': [ # Hungary
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('9000', '9999'),
    ],
    '964': [ # Iran
        ('00', '14'),
        ('150', '249'),
        ('2500', '2999'),
        ('300', '549'),
        ('5500', '8999'),
        ('90000', '96999'),
        ('970', '989'),
        ('9900', '9999'),
    ],
    '965': [ # Israel
        ('00', '19'),
        ('200', '599'),
        ('7000', '7999'),
        ('90000', '99999'),
    ],
    '966': [ # Ukraine
        ('00', '19'),
        ('2000', '2999'),
        ('300', '699'),
        ('7000', '8999'),
        ('90000', '99999'),
    ],
    '967': [ # Malaysia
        ('00', '29'),
        ('300', '499'),
        ('5000', '5999'),
        ('60', '89'),
        ('900', '989'),
        ('9900', '9989'),
        ('99900', '99999'),
    ],
    '968': [ # Mexico
        ('01', '39'),
        ('400', '499'),
        ('5000', '7999'),
        ('800', '899'),
        ('9000', '9999'),
    ],
    '969': [ # Pakistan
        ('0', '1'),
        ('20', '39'),
        ('400', '799'),
        ('8000', '9999'),
    ],
    '970': [ # Mexico
        ('01', '59'),
        ('600', '899'),
        ('9000', '9099'),
        ('91000', '96999'),
        ('9700', '9999'),
    ],
    '971': [ #Philippines?
        ('000', '019'),
        ('02', '02'),
        ('0300', '0599'),
        ('06', '09'),
        ('10', '49'),
        ('500', '849'),
        ('8500', '9099'),
        ('91000', '99999'),
    ],
    '972': [ # Portugal
        ('0', '1'),
        ('20', '54'),
        ('550', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '973': [ # Romania
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
    '974': [ # Thailand
        ('00', '19'),
        ('200', '699'),
        ('7000', '8499'),
        ('85000', '89999'),
        ('90000', '94999'),
        ('9500', '9999'),
    ],
    '975': [ # Turkey
        ('00000', '00999'),
        ('01', '24'),
        ('250', '599'),
        ('6000', '9199'),
        ('92000', '98999'),
        ('990', '999'),
    ],
    '976': [ # Caribbean Community
        ('0', '3'),
        ('40', '59'),
        ('600', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '977': [ # Egypt
        ('00', '19'),
        ('200', '499'),
        ('5000', '6999'),
        ('700', '999'),
    ],
    '978': [ # Nigeria
        ('000', '199'),
        ('2000', '2999'),
        ('30000', '79999'),
        ('8000', '8999'),
        ('900', '999'),
    ],
    '979': [ # Indonesia
        ('000', '099'),
        ('1000', '1499'),
        ('15000', '19999'),
        ('20', '29'),
        ('3000', '3999'),
        ('400', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '980': [ # Venezuela
        ('00', '19'),
        ('200', '599'),
        ('6000', '9999'),
    ],
    '981': [ # Singapore
        ('00', '19'),
        ('200', '299'),
        ('3000', '9999'),
    ],
    '982': [ # South Pacific
        ('00', '09'),
        ('100', '699'),
        ('70', '89'),
        ('9000', '9999'),
    ],
    '983': [ # Malaysia
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
    '984': [ # Bangladesh
        ('00', '39'),
        ('400', '799'),
        ('8000', '8999'),
        ('90000', '99999'),
    ],
    '985': [ # Belarus
        ('00', '39'),
        ('400', '599'),
        ('6000', '8999'),
        ('90000', '99999'),
    ],
    '986': [ # Taiwan, China
        ('00', '11'),
        ('120', '559'),
        ('5600', '7999'),
        ('80000', '99999'),
    ],
    '987': [ # Argentina
        ('00', '09'),
        ('1000', '1999'),
        ('20000', '29999'),
        ('30', '49'),
        ('500', '899'),
        ('9000', '9499'),
        ('95000', '99999'),
    ],
    '988': [ # Hongkong
        ('00', '16'),
        ('17000', '19999'),
        ('200', '799'),
        ('8000', '9699'),
        ('97000', '99999'),
    ],
    '989': [ # Portugal
        ('0', '1'),
        ('20', '54'),
        ('550', '799'),
        ('8000', '9499'),
        ('95000', '99999'),
    ],
    '9937': [ # Nepal
        ('0', '2'),
        ('30', '49'),
        ('500', '799'),
        ('8000', '9999'),
    ],
    '9938': [ # Tunisia
        ('00', '79'),
        ('800', '949'),
        ('9500', '9999'),
    ],
    '9939': [ # Armenia
        ('0', '4'),
        ('50', '79'),
        ('800', '899'),
        ('9000', '9999'),
    ],
    '9940': [ # Montenegro
        ('0', '1'),
        ('20', '49'),
        ('500', '899'),
        ('9000', '9999'),
    ],
    '9941': [ # Georgia
        ('0', '0'),
        ('10', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9942': [ # Ecuador
        ('00', '89'),
        ('900', '994'),
        ('9950', '9999'),
    ],
    '9943': [ # Uzbekistan
        ('00', '29'),
        ('300', '399'),
        ('4000', '9999'),
    ],
    '9944': [ # Turkey
        ('0', '2'),
        ('300', '499'),
        ('5000', '5999'),
        ('60', '89'),
        ('900', '999'),
    ],
    '9945': [ # Dominican Republic
        ('00', '00'),
        ('010', '079'),
        ('08', '39'),
        ('400', '569'),
        ('57', '57'),
        ('580', '849'),
        ('8500', '9999'),
    ],
    '9946': [ # Korea, P.D.R.
        ('0', '1'),
        ('20', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9947': [ # Algeria
        ('0', '1'),
        ('20', '79'),
        ('800', '999'),
    ],
    '9948': [ # United Arab Emirates
        ('00', '39'),
        ('400', '849'),
        ('8500', '9999'),
    ],
    '9949': [ # Estonia
        ('0', '0'),
        ('10', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9950': [ # Palestine
        ('00', '29'),
        ('300', '840'),
        ('8500', '9999'),
    ],
    '9951': [ # Kosova
        ('00', '39'),
        ('400', '849'),
        ('8500', '9999'),
    ],
    '9952': [ # Azerbaijan
        ('0', '1'),
        ('20', '39'),
        ('400', '799'),
        ('8000', '9999'),
    ],
    '9953': [ # Lebanon
        ('0', '0'),
        ('10', '39'),
        ('400', '599'),
        ('60', '89'),
        ('9000', '9999'),
    ],
    '9954': [ # Morocco
        ('0', '1'),
        ('20', '39'),
        ('400', '799'),
        ('8000', '9999'),
    ],
    '9955': [ # Lithuania
        ('00', '39'),
        ('400', '929'),
        ('9300', '9999'),
    ],
    '9956': [ # Cameroon
        ('0', '0'),
        ('10', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9957': [ # Jordan
        ('00', '39'),
        ('400', '699'),
        ('70', '84'),
        ('8500', '9999'),
    ],
    '9958': [ # Bosnia and Herzegovina
        ('0', '0'),
        ('10', '49'),
        ('500', '899'),
        ('9000', '9999'),
    ],
    '9959': [ # Libya
        ('0', '1'),
        ('20', '79'),
        ('800', '949'),
        ('9500', '9999'),
    ],
    '9960': [ # Saudi Arabia
        ('00', '59'),
        ('600', '899'),
        ('9000', '9999'),
    ],
    '9961': [ # Algeria
        ('0', '2'),
        ('30', '69'),
        ('700', '949'),
        ('9500', '9999'),
    ],
    '9962': [ # Panama
        ('00', '54'),
        ('5500', '5599'),
        ('56', '59'),
        ('600', '849'),
        ('8500', '9999'),
    ],
    '9963': [ # Cyprus
        ('0', '2'),
        ('30', '54'),
        ('550', '749'),
        ('7500', '9999'),
    ],
    '9964': [ # Ghana
        ('0', '6'),
        ('70', '94'),
        ('950', '999'),
    ],
    '9965': [ # Kazakhstan
        ('00', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9966': [ # Kenya
        ('00', '69'),
        ('7000', '7499'),
        ('750', '959'),
        ('9600', '9999'),
    ],
    '9967': [ # Kyrgyzstan
        ('00', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9968': [ # Costa Rica
        ('00', '49'),
        ('500', '939'),
        ('9400', '9999'),
    ],
    '9970': [ # Uganda
        ('00', '39'),
        ('400', '899'),
        ('9000', '9999'),
    ],
    '9971': [ # Singapore
        ('0', '5'),
        ('60', '89'),
        ('900', '989'),
        ('9900', '9999'),
    ],
    '9972': [ # Peru
        ('00', '09'),
        ('1', '1'),
        ('200', '249'),
        ('2500', '2999'),
        ('30', '59'),
        ('600', '899'),
        ('9000', '9999'),
    ],
    '9973': [ # Tunisia
        ('0', '05'),
        ('060', '089'),
        ('0900', '0999'),
        ('10', '69'),
        ('700', '969'),
        ('9700', '9999'),
    ],
    '9974': [ # Uruguay
        ('0', '2'),
        ('30', '54'),
        ('550', '749'),
        ('7500', '9499'),
        ('95', '99'),
    ],
    '9975': [ # Moldova
        ('0', '0'),
        ('100', '399'),
        ('4000', '4499'),
        ('45', '89'),
        ('900', '949'),
        ('9500', '9999'),
    ],
    '9976': [ # Tanzania
        ('0', '5'),
        ('60', '89'),
        ('900', '989'),
        ('9990', '9999'),
    ],
    '9977': [ # Costa Rica
        ('00', '89'),
        ('900', '989'),
        ('9900', '9999'),
    ],
    '9978': [ # Ecuador
        ('00', '29'),
        ('300', '399'),
        ('40', '94'),
        ('950', '989'),
        ('9900', '9999'),
    ],
    '9979': [ # Iceland
        ('0', '4'),
        ('50', '64'),
        ('650', '659'),
        ('66', '75'),
        ('760', '899'),
        ('9000', '9999'),
    ],
    '9980': [ # Papua New Guinea
        ('0', '3'),
        ('40', '89'),
        ('900', '989'),
        ('9900', '9999'),
    ],
    '9981': [ # Morocco
        ('00', '09'),
        ('100', '159'),
        ('1600', '1999'),
        ('20', '79'),
        ('800', '949'),
        ('9500', '9999'),
    ],
    '9982': [ # Zambia
        ('00', '79'),
        ('800', '989'),
        ('9900', '9999'),
    ],
    '9983': [ # Gambia
        ('80', '94'),
        ('950', '989'),
        ('9900', '9999'),
    ],
    '9984': [ # Latvia
        ('00', '49'),
        ('500', '899'),
        ('9000', '9999'),
    ],
    '9985': [ # Estonia
        ('0', '4'),
        ('50', '79'),
        ('800', '899'),
        ('9000', '9999'),
    ],
    '9986': [ # Lithuania
        ('00', '39'),
        ('400', '899'),
        ('9000', '9399'),
        ('940', '969'),
        ('97', '99'),
    ],
    '9987': [ # Tanzania
        ('00', '39'),
        ('400', '879'),
        ('8800', '9999'),
    ],
    '9988': [ # Ghana
        ('0', '2'),
        ('30', '54'),
        ('550', '749'),
        ('7500', '9999'),
    ],
    '9989': [ # Macedonia
        ('0', '0'),
        ('100', '199'),
        ('2000', '2999'),
        ('30', '59'),
        ('600', '949'),
        ('9500', '9999'),
    ],
    '99901': [ # Bahrain
        ('00', '49'),
        ('500', '799'),
        ('80', '99'),
    ],
    '99902': [ # Gabon - no ranges fixed yet
    ],
    '99903': [ # Mauritius
        ('0', '1'),
        ('20', '89'),
        ('900', '999'),
    ],
    '99904': [ # Netherlands Antilles; Aruba, Neth. Ant
        ('0', '5'),
        ('60', '89'),
        ('900', '999'),
    ],
    '99905': [ # Bolivia
        ('0', '3'),
        ('40', '79'),
        ('800', '999'),
    ],
    '99906': [ # Kuwait
        ('0', '2'),
        ('30', '59'),
        ('600', '699'),
        ('70', '89'),
        ('9', '9'),
    ],
    '99908': [ # Malawi
        ('0', '0'),
        ('10', '89'),
        ('900', '999'),
    ],
    '99909': [ # Malta
        ('0', '3'),
        ('40', '94'),
        ('950', '999'),
    ],
    '99910': [ # Sierra Leone
        ('0', '2'),
        ('30', '89'),
        ('900', '999'),
    ],
    '99911': [ # Lesotho
        ('00', '59'),
        ('600', '999'),
    ],
    '99912': [ # Botswana
        ('0', '3'),
        ('400', '599'),
        ('60', '89'),
        ('900', '999'),
    ],
    '99913': [ # Andorra
        ('0', '2'),
        ('30', '35'),
        ('600', '604'),
    ],
    '99914': [ # Suriname
        ('0', '4'),
        ('50', '89'),
        ('900', '949'),
    ],
    '99915': [ # Maldives
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99916': [ # Namibia
        ('0', '2'),
        ('30', '69'),
        ('700', '999'),
    ],
    '99917': [ # Brunei Darussalam
        ('0', '2'),
        ('30', '89'),
        ('900', '999'),
    ],
    '99918': [ # Faroe Islands
        ('0', '3'),
        ('40', '79'),
        ('800', '999'),
    ],
    '99919': [ # Benin
        ('0', '2'),
        ('40', '69'),
        ('900', '999'),
    ],
    '99920': [ # Andorra
        ('0', '4'),
        ('50', '89'),
        ('900', '999'),
    ],
    '99921': [ # Qatar
        ('0', '1'),
        ('20', '69'),
        ('700', '799'),
        ('8', '8'),
        ('90', '99'),
    ],
    '99922': [ # Guatemala
        ('0', '3'),
        ('40', '69'),
        ('700', '999'),
    ],
    '99923': [ # El Salvador
        ('0', '1'),
        ('20', '79'),
        ('800', '999'),
    ],
    '99924': [ # Nicaragua
        ('0', '2'),
        ('30', '79'),
        ('800', '999'),
    ],
    '99925': [ # Paraguay
        ('0', '3'),
        ('40', '79'),
        ('800', '999'),
    ],
    '99926': [ # Honduras
        ('0', '0'),
        ('10', '59'),
        ('600', '999'),
    ],
    '99927': [ # Albania
        ('0', '2'),
        ('30', '59'),
        ('600', '999'),
    ],
    '99928': [ # Georgia
        ('0', '0'),
        ('10', '79'),
        ('800', '999'),
    ],
    '99929': [ # Mongolia
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99930': [ # Armenia
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99931': [ # Seychelles
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99932': [ # Malta
        ('0', '0'),
        ('10', '59'),
        ('600', '699'),
        ('7', '7'),
        ('80', '99'),
    ],
    '99933': [ # Nepal
        ('0', '2'),
        ('30', '59'),
        ('600', '999'),
    ],
    '99934': [ # Dominican Republic
        ('0', '1'),
        ('20', '79'),
        ('800', '999'),
    ],
    '99935': [ # Haiti
        ('0', '2'),
        ('7', '8'),
        ('30', '59'),
        ('600', '699'),
        ('90', '99'),
    ],
    '99936': [ # Bhutan
        ('0', '0'),
        ('10', '59'),
        ('600', '999'),
    ],
    '99937': [ # Macau
        ('0', '1'),
        ('20', '59'),
        ('600', '999'),
    ],
    '99938': [ # Srpska
        ('0', '1'),
        ('20', '59'),
        ('600', '899'),
        ('90', '99'),
    ],
    '99939': [ # Guatemala
        ('0', '5'),
        ('60', '89'),
        ('900', '999'),
    ],
    '99940': [ # Georgia
        ('0', '0'),
        ('10', '69'),
        ('700', '999'),
    ],
    '99941': [ # Armenia
        ('0', '2'),
        ('30', '79'),
        ('800', '999'),
    ],
    '99942': [ # Sudan
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99943': [ # Alsbania
        ('0', '2'),
        ('30', '59'),
        ('600', '999'),
    ],
    '99944': [ # Ethiopia
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99945': [ # Namibia
        ('0', '5'),
        ('60', '89'),
        ('900', '999'),
    ],
    '99946': [ # Nepal
        ('0', '2'),
        ('30', '59'),
        ('600', '999'),
    ],
    '99947': [ # Tajikistan
        ('0', '2'),
        ('30', '69'),
        ('700', '999'),
    ],
    '99948': [ # Eritrea
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99949': [ # Mauritius
        ('0', '1'),
        ('20', '89'),
        ('900', '999'),
    ],
    '99950': [ # Cambodia
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99951': [ # Congo - no ranges fixed yet
    ],
    '99952': [ # Mali
        ('0', '4'),
        ('50', '79'),
        ('800', '999'),
    ],
    '99953': [ # Paraguay
        ('0', '2'),
        ('30', '79'),
        ('800', '999'),
    ],
    '99954': [ # Bolivia
        ('0', '2'),
        ('30', '69'),
        ('700', '999'),
    ],
    '99955': [ # Srpska
        ('0', '1'),
        ('20', '59'),
        ('600', '899'),
        ('90', '99'),
    ],
    '99956': [ # Albania
        ('00', '59'),
        ('600', '999'),
    ],
}

class IsbnBot:
    def __init__(self, generator):
        self.generator = generator

    def run(self):
        for page in self.generator:
            try:
                text = page.get(get_redirect = self.touch_redirects)
                # convert ISBN numbers
                page.put(text)
            except pywikibot.NoPage:
                pywikibot.output(u"Page %s does not exist?!"
                                 % page.title(asLink=True))
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"Page %s is a redirect; skipping."
                                 % page.title(asLink=True))
            except pywikibot.LockedPage:
                pywikibot.output(u"Page %s is locked?!"
                                 % page.title(asLink=True))


class InvalidIsbnException(pywikibot.Error):
    """Invalid ISBN"""

class ISBN:
    """
    Abstract superclass
    """

    def format(self):
        """
        Puts hyphens into this ISBN number.
        """
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
        for groupNumber in ranges.iterkeys():
            if rest.startswith(groupNumber):
                result += groupNumber + '-'
                rest = rest[len(groupNumber):]
                publisherRanges = ranges[groupNumber]
                break
        else:
            raise InvalidIsbnException('ISBN %s: group number unknown.' % self.code)

        # Determine the publisher
        for (start, end) in publisherRanges:
            length = len(start) # NOTE: start and end always have equal length
            if rest[:length] > start and rest[:length] <= end:
                result += rest[:length] + '-'
                rest = rest[length:]
                break
        else:
            raise InvalidIsbnException('ISBN %s: publisher number unknown.' % self.code)

        # The rest is the item number and the 1-digit checksum.
        result += rest[:-1] + '-' + rest[-1]
        self.code = result

class ISBN13(ISBN):
    def __init__(self, code, checksumMissing = False):
        self.code = code
        if checksumMissing:
            self.code += str(self.calculateChecksum())
        self.checkValidity()

    def possiblePrefixes(self):
        return ['978', '979']

    def digits(self):
        """
        Returns a list of the digits in the ISBN code.
        """
        result = []
        for c in self.code:
            if c.isdigit():
                result.append(int(c))
            elif c != '-':
                raise InvalidIsbnException('The ISBN %s contains invalid characters.' % self.code)
        return result

    def checkValidity(self):
        if len(self.digits()) != 13:
            raise InvalidIsbnException('The ISBN %s is not 13 digits long.' % self.code)
        if self.calculateChecksum() != self.digits()[-1]:
            raise InvalidIsbnException('The ISBN checksum of %s is incorrect.' % self.code)

    def calculateChecksum(self):
        # See http://en.wikipedia.org/wiki/ISBN#Check_digit_in_ISBN_13
        sum = 0
        for i in range(0, 13 - 1, 2):
            sum += self.digits()[i]
        for i in range(1, 13 - 1, 2):
            sum += 3 * self.digits()[i]
        return (10 - (sum % 10)) % 10

class ISBN10(ISBN):
    def __init__(self, code):
        self.code = code
        self.checkValidity()

    def possiblePrefixes(self):
        return []

    def digits(self):
        """
        Returns a list of the digits and Xs in the ISBN code.
        """
        result = []
        for c in self.code:
            if c.isdigit() or c in 'Xx':
                result.append(c)
            elif c != '-':
                raise InvalidIsbnException('The ISBN %s contains invalid characters.' % self.code)
        return result

    def checkChecksum(self):
        """
        Raises an InvalidIsbnException if the checksum shows that the
        ISBN is incorrect.
        """
        # See http://en.wikipedia.org/wiki/ISBN#Check_digit_in_ISBN_10
        sum = 0
        for i in range(0, 9):
            sum += (i + 1) * int(self.digits()[i])
        #print sum
        checksum = sum % 11
        #print checksum
        lastDigit = self.digits()[-1]
        #print lastDigit
        if not ((checksum == 10 and lastDigit in 'Xx') or (lastDigit.isdigit() and checksum == int(lastDigit))):
            raise InvalidIsbnException('The ISBN checksum of %s is incorrect.' % self.code)

    def checkValidity(self):
        if len(self.digits()) != 10:
            raise InvalidIsbnException('The ISBN %s is not 10 digits long.' % self.code)
        if 'X' in self.digits()[:-1] or 'x' in self.digits()[:-1]:
            raise InvalidIsbnException('ISBN %s: X is only allowed at the end of the ISBN.' % self.code)
        self.checkChecksum()

    def toISBN13(self):
        """
        Creates a 13-digit ISBN from this 10-digit ISBN by prefixing the GS1
        prefix '978' and recalculating the checksum.
        The hyphenation structure is taken from the format of the original
        ISBN number.
        """
        code = '978-' + self.code[:-1]

        #cs = self.calculateChecksum()
        #code += str(cs)
        return ISBN13(code, checksumMissing = True)

    def format(self):
        # load overridden superclass method
        ISBN.format(self)
        # capitalize checksum
        if self.code[-1] == 'x':
            self.code = self.code[:-1] + 'X'

def getIsbn(code):
    try:
        i = ISBN13(code)
    except InvalidIsbnException, e13:
        try:
            i = ISBN10(code)
        except InvalidIsbnException, e10:
            raise InvalidIsbnException(u'ISBN-13: %s / ISBN-10: %s' % (e13, e10))
    return i

def _hyphenateIsbnNumber(match):
    """
    Helper function to deal with a single ISBN
    """
    code = match.group('code')
    try:
        i = getIsbn(code)
    except InvalidIsbnException:
        # don't change
        return code
    i.format()
    return i.code

def hyphenateIsbnNumbers(text):
    isbnR = re.compile(r'(?<=ISBN )(?P<code>[\d\-]+[\dXx])')
    text = isbnR.sub(_hyphenateIsbnNumber, text)
    return text

def _isbn10toIsbn13(match):
    """
    Helper function to deal with a single ISBN
    """
    code = match.group('code')
    try:
        i = getIsbn(code)
    except InvalidIsbnException:
        # don't change
        return code
    i13 = i.toISBN13()
    return i13.code

def convertIsbn10toIsbn13(text):
    isbnR = re.compile(r'(?<=ISBN )(?P<code>[\d\-]+[Xx]?)')
    text = isbnR.sub(_isbn10toIsbn13, text)
    return text

class IsbnBot:

    def __init__(self, generator, to13 = False, format = False, always = False):
        self.generator = generator
        self.to13 = to13
        self.format = format
        self.always = always
        self.isbnR = re.compile(r'(?<=ISBN )(?P<code>[\d\-]+[Xx]?)')
        self.comment = pywikibot.translate(pywikibot.getSite(), msg)

    def treat(self, page):
        try:
            oldText = page.get()
            for match in self.isbnR.finditer(oldText):
                code = match.group('code')
                try:
                    getIsbn(code)
                except InvalidIsbnException, e:
                    pywikibot.output(e)

            newText = oldText
            if self.to13:
                newText = self.isbnR.sub(_isbn10toIsbn13, newText)

            if self.format:
                newText = self.isbnR.sub(_hyphenateIsbnNumber, newText)
            self.save(page, newText)
        except pywikibot.NoPage:
            pywikibot.output(u"Page %s does not exist?!" % page.title(asLink=True))
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"Page %s is a redirect; skipping." % page.title(asLink=True))
        except pywikibot.LockedPage:
            pywikibot.output(u"Page %s is locked?!" % page.title(asLink=True))

    def save(self, page, text):
        if text != page.get():
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<" % page.title())
            pywikibot.showDiff(page.get(), text)
            if not self.always:
                choice = pywikibot.inputChoice(u'Do you want to accept these changes?', ['Yes', 'No', 'Always yes'], ['y', 'N', 'a'], 'N')
                if choice == 'n':
                    return
                elif choice == 'a':
                    self.always = True

            if self.always:
                try:
                    page.put(text, comment=self.comment)
                except pywikibot.EditConflict:
                    pywikibot.output(u'Skipping %s because of edit conflict' % (page.title(),))
                except pywikibot.SpamfilterError, e:
                    pywikibot.output(u'Cannot change %s because of blacklist entry %s' % (page.title(), e.url))
                except pywikibot.LockedPage:
                    pywikibot.output(u'Skipping %s (locked page)' % (page.title(),))
            else:
                # Save the page in the background. No need to catch exceptions.
                page.put(text, comment=self.comment, async=True)


    def run(self):
        for page in self.generator:
            self.treat(page)


def main():
    #page generator
    gen = None
    # This temporary array is used to read the page title if one single
    # page to work on is specified by the arguments.
    pageTitle = []
    # Which namespaces should be processed?
    # default to [] which means all namespaces will be processed
    namespaces = []
    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()
    # Never ask before changing a page
    always = False
    to13 = False
    format = False

    for arg in pywikibot.handleArgs():
        if arg.startswith('-namespace:'):
            try:
                namespaces.append(int(arg[11:]))
            except ValueError:
                namespaces.append(arg[11:])
        elif arg == '-always':
            always = True
        elif arg == '-to13':
            to13 = True
        elif arg == '-format':
            format = True
        else:
            if not genFactory.handleArg(arg):
                pageTitle.append(arg)

    site = pywikibot.getSite()
    if pageTitle:
        gen = iter([pywikibot.Page(pywikibot.Link(t, site)) for t in pageTitle])
    if not gen:
        gen = genFactory.getCombinedGenerator()
    if not gen:
        pywikibot.showHelp('isbn')
    else:
        if namespaces != []:
            gen =  pagegenerators.NamespaceFilterPageGenerator(gen, namespaces)
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        bot = IsbnBot(preloadingGen, to13 = to13, format = format, always = always)
        bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
