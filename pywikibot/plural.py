# -*- coding: utf-8  -*-
#
# (C) xqt, 2011
# (C) Pywikipedia bot team, 2011
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

plural_rules = {
    '_default': {'nplurals': 2, 'plural': lambda n: (n != 1)},
    'ach':{'nplurals': 2, 'plural': lambda n: (n > 1)},
    'ak': {'nplurals': 2, 'plural': lambda n: (n > 1)},
    'am': {'nplurals': 2, 'plural': lambda n: (n > 1)},
    'ar': {'nplurals': 6, 'plural': lambda n:
           0 if (n == 0) else
           1 if (n == 1) else
           2 if (n == 2) else
           3 if (n%100 >= 3 and n%100 <= 10) else
           4 if (n%100 >= 11 and n%100 <= 99) else
           5 },
    'arn':{'nplurals': 2, 'plural': lambda n: (n > 1)},
    'ay': {'nplurals': 1, 'plural': 0},
    'be': {'nplurals': 3, 'plural': lambda n:
           0 if (n%10 == 1 and n%100 != 11) else
           1 if (n%10 >= 2 and n%10 <= 4 and (n%100 < 10 or n%100 >= 20)) else
           2 },
    'bo': {'nplurals': 1, 'plural': 0},
    'br': {'nplurals': 2, 'plural': lambda n: (n > 1)},
    'bs': {'nplurals': 3, 'plural': lambda n:
           0 if (n%10 == 1 and n%100 != 11) else
           1 if (n%10 >= 2 and n%10 <= 4 and (n%100 < 10 or n%100 >= 20)) else
           2 },
    'cgg':{'nplurals': 1, 'plural': 0},
    'cs': {'nplurals': 3, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n >= 2 and n <= 4) else
           2 },
    'csb':{'nplurals': 3, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n%10 >= 2 and n%10 <= 4 and (n%100 < 10 or n%100 >= 20)) else
           2 },
    'cy': {'nplurals': 6, 'plural': lambda n:
           0 if (n == 0) else
           1 if (n == 1) else
           2 if (n == 2) else
           3 if (n == 3) else
           4 if (n == 6) else
           5 },
    'dz': {'nplurals': 1, 'plural': 0},
    'fa': {'nplurals': 1, 'plural': 0},
    'fil':{'nplurals': 2, 'plural': lambda n: (n > 1)},
    'fr': {'nplurals': 2, 'plural': lambda n: (n > 1)},
    'ga': {'nplurals': 5, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n == 2) else
           2 if (n < 7) else
           3 if (n < 11) else
           4 },
    'gd': {'nplurals': 4, 'plural': lambda n:
           0 if (n == 1 or n == 11) else
           1 if (n == 2 or n == 12) else
           2 if (n > 2 and n < 20) else
           3 },
    'gun':{'nplurals': 2, 'plural': lambda n: (n > 1)},
    'hr': {'nplurals': 3, 'plural': lambda n:
           0 if (n%10 == 1 and n%100 != 11) else
           1 if (n%10 >= 2 and n%10 <= 4 and (n%100 < 10 or n%100 >= 20)) else
           2 },
    'id': {'nplurals': 1, 'plural': 0},
    'ja': {'nplurals': 1, 'plural': 0},
    'jbo':{'nplurals': 1, 'plural': 0},
    'ka': {'nplurals': 1, 'plural': 0},
    'kk': {'nplurals': 1, 'plural': 0},
    'km': {'nplurals': 1, 'plural': 0},
    'ko': {'nplurals': 1, 'plural': 0},
    'kw': {'nplurals': 4, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n == 2) else
           2 if (n == 3) else
           3 },
    'ky': {'nplurals': 1, 'plural': 0},
    'ln': {'nplurals': 2, 'plural': lambda n: (n > 1)},
    'lo': {'nplurals': 1, 'plural': 0},
    'lt': {'nplurals': 3, 'plural': lambda n:
           0 if (n%10 == 1 and n%100 != 11) else
           1 if (n%10 >= 2 and (n%100 < 10 or n%100 >= 20)) else
           2 },
    'lv': {'nplurals': 3, 'plural': lambda n:
           0 if (n%10 == 1 and n%100 != 11) else
           1 if (n != 0) else
           2 },
    'mfe':{'nplurals': 2, 'plural': lambda n: (n > 1)},
    'mg': {'nplurals': 2, 'plural': lambda n: (n > 1)},
    'mi': {'nplurals': 2, 'plural': lambda n: (n > 1)},
    'mk': {'nplurals': 2, 'plural': lambda n: 0 if n == 1 or n%10 == 1 else 1},
    'mnk':{'nplurals': 3, 'plural': lambda n:
           0 if (n == 0) else
           1 if n == 1 else
           2 },
    'ms': {'nplurals': 1, 'plural': 0},
    'mt': {'nplurals': 4, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n == 0 or (n%100 > 1 and n%100 < 11)) else
           2 if (n%100 > 10 and n%100 < 20) else
           3 },
    'nso':{'nplurals': 2, 'plural': lambda n: (n > 1)},
    'oc': {'nplurals': 2, 'plural': lambda n: (n > 1)},
    'pl': {'nplurals': 3, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n%10 >= 2 and n%10 <= 4 and (n%100 < 10 or n%100 >= 20)) else
           2 },
    'pt-br': {'nplurals': 2, 'plural': lambda n: (n > 1)},
    'ro': {'nplurals': 3, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n == 0 or (n%100 > 0 and n%100 < 20)) else
           2 },
    'ru': {'nplurals': 3, 'plural': lambda n:
           0 if (n%10 == 1 and n%100 != 11) else
           1 if (n%10 >= 2 and n%10 <= 4 and (n%100 < 10 or n%100 >= 20)) else
           2 },
    'sk': {'nplurals': 3, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n >= 2 and n <= 4) else
           2 },
    'sl': {'nplurals': 4, 'plural': lambda n:
           0 if (n%100 == 1) else
           1 if (n%100 == 2) else
           2 if (n%100 == 3 or n%100 == 4) else
           3 },
    'sr': {'nplurals': 3, 'plural': lambda n:
           0 if (n%10 == 1 and n%100 != 11) else
           1 if (n%10 >= 2 and n%10 <= 4 and (n%100 < 10 or n%100 >= 20)) else
           2 },
    'su': {'nplurals': 1, 'plural': 0},
    'th': {'nplurals': 1, 'plural': 0},
    'ti': {'nplurals': 2, 'plural': lambda n: (n > 1)},
    'tr': {'nplurals': 1, 'plural': 0},
    'tt': {'nplurals': 1, 'plural': 0},
    'ug': {'nplurals': 1, 'plural': 0},
    'uk': {'nplurals': 3, 'plural': lambda n:
           0 if (n%10 == 1 and n%100 != 11) else
           1 if (n%10 >= 2 and n%10 <= 4 and (n%100 < 10 or n%100 >= 20)) else
           2 },
    'uz': {'nplurals': 1, 'plural': 0},
    'vi': {'nplurals': 1, 'plural': 0},
    'wa': {'nplurals': 2, 'plural': lambda n: (n > 1)},
    'wo': {'nplurals': 1, 'plural': 0},
    'zh': {'nplurals': 1, 'plural': 0},
    'zh-hans': {'nplurals': 1, 'plural': 0},
    'zh-hant': {'nplurals': 1, 'plural': 0},
    'zh-tw': {'nplurals': 1, 'plural': 0},
}

