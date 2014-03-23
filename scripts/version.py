#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Script to determine the pywikipedia version (tag, revision and date) """
#
# (C) Merlijn 'valhallasw' van Deen, 2007-2008
# (C) xqt, 2010-2014
# (C) Pywikibot team, 2007-2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import sys
import pywikibot
from pywikibot.version import getversion

if __name__ == '__main__':
    pywikibot.output('Pywikibot: %s' % getversion())
    pywikibot.output('Release version: %s' % pywikibot.__release__)
    pywikibot.output('Python: %s' % sys.version)
    if not __import__('unicodedata').normalize('NFC', u'\u092e\u093e\u0930\u094d\u0915 \u091c\u093c\u0941\u0915\u0947\u0930\u092c\u0930\u094d\u0917') == u'\u092e\u093e\u0930\u094d\u0915 \u091c\u093c\u0941\u0915\u0947\u0930\u092c\u0930\u094d\u0917':
        pywikibot.output(u'unicode test: triggers problem #3081100')
    else:
        pywikibot.output(u'unicode test: ok')
