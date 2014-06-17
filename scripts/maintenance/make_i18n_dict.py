# -*- coding: utf-8  -*-
"""
Generate a i18n file from a given script

usage:

run IDLE at topmost level
>>> import pwb
>>> from scripts.maintenance.make_i18n_dict import i18nBot
>>> bot = i18nBot('<scriptname>', '<msg dict>')
>>> bot.run()

If you have more than one message dictionary, give all these names to the bot:
>>> bot = i18nBot('<scriptname>', '<msg dict1>', '<msg dict2>', '<msg dict3>')

If you have the messages as instance constants you may call the bot as follows:
>>> bot = i18nBot('<scriptname>.<class instance>', '<msg dict1>', '<msg dict2>')
"""
#
# (C) xqt 2013-2014
# (C) Pywikipedia bot team, 2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#


class i18nBot(object):

    def __init__(self, script, *args):
        modules = script.split('.')
        self.scriptname = modules[0]
        self.script = __import__('scripts.' + self.scriptname)
        for m in modules:
            self.script = getattr(self.script, m)
        self.messages = list()
        for msg in args:
            if hasattr(self.script, msg):
                self.messages.append(msg)
        self.messages.sort()
        self.dict = dict()

    def print_all(self):
        keys = self.dict.keys()
        keys.sort()
        print "# -*- coding: utf-8 -*-"
        print "msg = {"
        for code in keys:
            print "    '%s': {" % code
            for msg in self.messages:
                label = "%s-%s" % (self.scriptname, msg)
                if label in self.dict[code]:
                    print "        '%s': u'%s'," % (label,
                                                    self.dict[code][label])
            print "    },"
        print "};"

    def read(self, item):
        msg = getattr(self.script, item)
        self.keys = msg.keys()
        self.keys.append('qqq')
        self.keys.sort()
        for code in self.keys:
            label = "%s-%s" % (self.scriptname, item)
            if code == 'qqq':
                if code not in self.dict:
                    self.dict[code] = {}
                self.dict[code][label] = \
                    u'Edit summary for %s report' % self.scriptname
            elif code != 'commons':
                if code not in self.dict:
                    self.dict[code] = {}
                self.dict[code][label] = msg[code]

    def run(self):
        for msg in self.messages:
            self.read(msg)
        self.print_all()

if __name__ == "__main__":
    print __doc__
