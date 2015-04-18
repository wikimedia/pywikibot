#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Generate a i18n file from a given script.

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

It's also possible to make json files too by using to_json method:
>>> from scripts.maintenance.make_i18n_dict import i18nBot
>>> bot = i18nBot('disambredir', 'msg')
>>> bot.to_json()
"""
#
# (C) xqt, 2013-2014
# (C) Pywikibot team, 2013-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import os
import json
import codecs

from pywikibot import config


class i18nBot(object):

    """I18n bot."""

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
        keys = list(self.dict.keys())
        keys.remove('qqq')
        keys.sort()
        keys.insert(0, 'qqq')
        if 'en' in keys:
            keys.remove('en')
            keys.insert(0, 'en')

        print("# -*- coding: utf-8 -*-")
        print("msg = {")
        for code in keys:
            print("    '%s': {" % code)
            for msg in self.messages:
                label = "%s-%s" % (self.scriptname, msg)
                if label in self.dict[code]:
                    print("        '%s': u'%s'," % (label,
                                                    self.dict[code][label]))
            print("    },")
        print("};")

    def read(self, item):
        msg = getattr(self.script, item)
        keys = list(msg.keys())
        keys.append('qqq')
        for code in keys:
            label = "%s-%s" % (self.scriptname, item)
            if code == 'qqq':
                if code not in self.dict:
                    self.dict[code] = {}
                self.dict[code][label] = (
                    u'Edit summary for message %s of %s report'
                    % (self.scriptname, item))
            elif code != 'commons':
                if code not in self.dict:
                    self.dict[code] = {}
                self.dict[code][label] = msg[code]
        if 'en' not in keys:
            print('WARNING: "en" key missing for message %s' % item)

    def run(self):
        for msg in self.messages:
            self.read(msg)
        self.print_all()

    def to_json(self):
        if not self.dict:
            self.run()
        json_dir = os.path.join(
            config.base_dir, 'scripts/i18n', self.scriptname)
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)
        for lang in self.dict:
            file_name = os.path.join(json_dir, '%s.json' % lang)
            if os.path.isfile(file_name):
                with codecs.open(file_name, 'r', 'utf-8') as json_file:
                    new_dict = json.loads(json_file.read())
            else:
                new_dict = {}
            new_dict['@metadata'] = new_dict.get('@metadata', {'authors': []})
            with codecs.open(file_name, 'w', 'utf-8') as json_file:
                new_dict.update(self.dict[lang])
                json.dump(new_dict, json_file, ensure_ascii=False,
                          sort_keys=True, indent=4, separators=(',', ': '))

if __name__ == '__main__':
    print(__doc__)
