#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This script generates a family file from a given URL."""
#
# (C) Merlijn van Deen, 2010-2013
# (C) Pywikibot team, 2010-2019
#
# Distributed under the terms of the MIT license
#
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

# system imports
import codecs
import os
import sys

from os import environ, getenv

# creating & retrieving urls
if sys.version_info[0] > 2:
    from urllib.parse import urlparse
    raw_input = input
else:
    from urlparse import urlparse


class FamilyFileGenerator(object):

    """Family file creator."""

    def __init__(self, url=None, name=None, dointerwiki=None):
        """Initializer."""
        # from pywikibot.site_detect import MWSite
        # when required but disable user-config checks
        # so the family can be created first,
        # and then used when generating the user-config
        self.Wiki = _import_with_no_user_config(
            'pywikibot.site_detect').site_detect.MWSite
        if url is None:
            url = raw_input('Please insert URL to wiki: ')
        if name is None:
            name = raw_input('Please insert a short name (eg: freeciv): ')
        self.dointerwiki = dointerwiki
        self.base_url = url
        self.name = name

        self.wikis = {}  # {'https://wiki/$1': Wiki('https://wiki/$1'), ...}
        self.langs = []  # [Wiki('https://wiki/$1'), ...]

    def run(self):
        """Main method, generate family file."""
        print('Generating family file from ' + self.base_url)

        w = self.Wiki(self.base_url)
        self.wikis[w.lang] = w
        print('\n=================================='
              '\nAPI url: {w.api}'
              '\nMediaWiki version: {w.version}'
              '\n==================================\n'.format(w=w))

        self.getlangs(w)
        self.getapis()
        self.writefile()

    def getlangs(self, w):
        """Determine language of a site."""
        print('Determining other languages...', end='')
        try:
            self.langs = w.langs
            print(' '.join(sorted(wiki['prefix'] for wiki in self.langs)))
        except Exception as e:
            self.langs = []
            print(e, '; continuing...')

        if len([lang for lang in self.langs if lang['url'] == w.iwpath]) == 0:
            if w.private_wiki:
                w.lang = self.name
            self.langs.append({'language': w.lang,
                               'local': '',
                               'prefix': w.lang,
                               'url': w.iwpath})

        if len(self.langs) > 1:
            if self.dointerwiki is None:
                makeiw = raw_input(
                    '\nThere are %i languages available.'
                    '\nDo you want to generate interwiki links? '
                    'This might take a long time. ([y]es/[N]o/[e]dit)'
                    % len(self.langs)).lower()
            else:
                makeiw = self.dointerwiki

            if makeiw == 'n':
                self.langs = [wiki for wiki in self.langs
                              if wiki['url'] == w.iwpath]
            elif makeiw == 'e':
                for wiki in self.langs:
                    print(wiki['prefix'], wiki['url'])
                do_langs = raw_input('Which languages do you want: ')
                self.langs = [wiki for wiki in self.langs
                              if wiki['prefix'] in do_langs
                              or wiki['url'] == w.iwpath]

    def getapis(self):
        """Load other language pages."""
        print('Loading wikis... ')
        for lang in self.langs:
            print('  * %s... ' % (lang['prefix']), end='')
            if lang['prefix'] not in self.wikis:
                try:
                    self.wikis[lang['prefix']] = self.Wiki(lang['url'])
                    print('downloaded')
                except Exception as e:
                    print(e)
            else:
                print('in cache')

    def writefile(self):
        """Write the family file."""
        fn = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          'pywikibot', 'families',
                          '{}_family.py'.format(self.name))
        print('Writing %s... ' % fn)
        try:
            open(fn)
            if raw_input('%s already exists. Overwrite? (y/n)'
                         % fn).lower() == 'n':
                print('Terminating.')
                sys.exit(1)
        except IOError:  # file not found
            pass

        code_hostname_pairs = '\n        '.join(
            "'{code}': '{hostname}',".format(
                code=k, hostname=urlparse(w.server).netloc
            ) for k, w in self.wikis.items())

        code_path_pairs = '\n            '.join(
            "'{code}': '{path}',".format(code=k, path=w.scriptpath)
            for k, w in self.wikis.items())

        code_version_pairs = '\n            '.join(
            "'{code}': None,".format(code=k) if w.version is None else
            "'{code}': '{version}',".format(code=k, version=w.version)
            for k, w in self.wikis.items())

        code_protocol_pairs = '\n            '.join(
            "'{code}': '{protocol}',".format(
                code=k, protocol=urlparse(w.server).scheme
            ) for k, w in self.wikis.items())

        with codecs.open(fn, 'w', 'utf-8') as fh:
            fh.write(family_template % {
                'url': self.base_url, 'name': self.name,
                'code_hostname_pairs': code_hostname_pairs,
                'code_path_pairs': code_path_pairs,
                'code_version_pairs': code_version_pairs,
                'code_protocol_pairs': code_protocol_pairs})


family_template = """\
# -*- coding: utf-8 -*-
\"\"\"
This family file was auto-generated by generate_family_file.py script.

Configuration parameters:
  url = %(url)s
  name = %(name)s

Please do not commit this to the Git repository!
\"\"\"
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family
from pywikibot.tools import deprecated


class Family(family.Family):  # noqa: D101

    name = '%(name)s'
    langs = {
        %(code_hostname_pairs)s
    }

    def scriptpath(self, code):
        return {
            %(code_path_pairs)s
        }[code]

    @deprecated('APISite.version()')
    def version(self, code):
        return {
            %(code_version_pairs)s
        }[code]

    def protocol(self, code):
        return {
            %(code_protocol_pairs)s
        }[code]
"""


def _import_with_no_user_config(*import_args):
    """Return __import__(*import_args) without loading user-config.py."""
    orig_no_user_config = getenv('PYWIKIBOT_NO_USER_CONFIG') or getenv(
        'PYWIKIBOT2_NO_USER_CONFIG')
    environ['PYWIKIBOT_NO_USER_CONFIG'] = '2'
    result = __import__(*import_args)
    # Reset this flag
    if not orig_no_user_config:
        del environ['PYWIKIBOT_NO_USER_CONFIG']
    else:
        environ['PYWIKIBOT_NO_USER_CONFIG'] = orig_no_user_config
    return result


def main():
    """Process command line arguments and generate a family file."""
    if len(sys.argv) != 3:
        print("""
Usage: {module} <url> <short name>
Example: {module} https://www.mywiki.bogus/wiki/Main_Page mywiki
This will create the file mywiki_family.py in pywikibot{sep}families"""
              .format(module=sys.argv[0].strip('.' + os.sep),
                      sep=os.sep))

    FamilyFileGenerator(*sys.argv[1:]).run()


if __name__ == '__main__':
    main()
