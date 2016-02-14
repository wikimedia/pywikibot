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

If you want to rename the message index use keyword arguments. This may be
mixed with preleading positonal argumens:
>>> bot = i18nBot('<scriptname>', '<msg dict1>', the_other_msg='<msg dict2>')

If you have the messages as instance constants you may call the bot as follows:
>>> bot = i18nBot('<scriptname>.<class instance>', '<msg dict1>', '<msg dict2>')

It's also possible to make json files too by using to_json method after
instantiating the bot. It also calls bot.run() to create the dictionaries.
>>> bot.to_json()
"""
#
# (C) xqt, 2013-2015
# (C) Pywikibot team, 2013-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import codecs
import json
import os

from pywikibot import config


class i18nBot(object):

    """I18n bot."""

    def __init__(self, script, *args, **kwargs):
        """Constructor."""
        modules = script.split('.')
        self.scriptname = modules[0]
        self.script = __import__('scripts.' + self.scriptname)
        for m in modules:
            self.script = getattr(self.script, m)
        self.messages = {}
        # setup the message dict
        for msg in args:
            if hasattr(self.script, msg):
                self.messages[msg] = msg
            else:
                print('message {0} not found'.format(msg))
        for new, old in kwargs.items():
            self.messages[old] = new.replace('_', '-')
        self.dict = {}

    def print_all(self):
        """Pretty print the dict as a file content to screen."""
        if not self.dict:
            print('No messages found, read them first.\n'
                  'Use "run" or "to_json" methods')
            return
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
            for msg in sorted(self.messages.values()):
                label = "%s-%s" % (self.scriptname, msg)
                if label in self.dict[code]:
                    print("        '%s': u'%s'," % (label,
                                                    self.dict[code][label]))
            print("    },")
        print("};")

    def read(self, oldmsg, newmsg=None):
        """Read a single message from source script."""
        msg = getattr(self.script, oldmsg)
        keys = list(msg.keys())
        keys.append('qqq')
        if newmsg is None:
            newmsg = oldmsg
        for code in keys:
            label = "%s-%s" % (self.scriptname, newmsg)
            if code == 'qqq':
                if code not in self.dict:
                    self.dict[code] = {}
                self.dict[code][label] = (
                    u'Edit summary for message %s of %s report'
                    % (newmsg, self.scriptname))
            elif code != 'commons':
                if code not in self.dict:
                    self.dict[code] = {}
                self.dict[code][label] = msg[code]
        if 'en' not in keys:
            print('WARNING: "en" key missing for message %s' % newmsg)

    def run(self, quiet=False):
        """
        Run the bot, read the messages from source and print the dict.

        @param quiet: print the result if False
        @type quiet: bool
        """
        for item in self.messages.items():
            self.read(*item)
        if not quiet:
            self.print_all()

    def to_json(self, quiet=True):
        """
        Run the bot and create json files.

        @param quiet: Print the result if False
        @type quiet: bool
        """
        IDENT = 4

        if not self.dict:
            self.run(quiet)
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
                s = json.dumps(new_dict, ensure_ascii=False, sort_keys=True,
                               indent=IDENT, separators=(',', ': '))
                s = s.replace(' ' * IDENT, '\t')
                json_file.write(s)

if __name__ == '__main__':
    print(__doc__)
