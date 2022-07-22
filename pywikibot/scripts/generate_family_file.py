#!/usr/bin/python3
"""This script generates a family file from a given URL.

This script must be invoked with the pwb wrapper script/code entry point.

Usage::

    pwb generate_family_file.py [<url>] [<name>] [<dointerwiki>] [<verify>]

Parameters are optional. They must be given consecutively but may be
omitted if there is no successor parameter. The parameters are::

    <url>:         an url from where the family settings are loaded
    <name>:        the family name without "_family.py" tail.
    <dointerwiki>: predefined answer (y|n) to add multiple site codes
    <verify>:      disable certificate validaton `(y|n)

Example::

    pwb generate_family_file.py https://www.mywiki.bogus/wiki/Main_Page mywiki

This will create the file mywiki_family.py in families folder of your
base directory.

.. versionchanged:: 7.0
   moved to pywikibot.scripts folder; create family files in families
   folder of your base directory instead of pywikibot/families.
"""
#
# (C) Pywikibot team, 2010-2022
#
# Distributed under the terms of the MIT license
#
import codecs
import os
import string
import sys
from typing import Optional
from urllib.parse import urlparse
from contextlib import suppress


# see pywikibot.family.py
# Legal characters for Family name and Family langs keys
NAME_CHARACTERS = string.ascii_letters + string.digits
# nds_nl code alias requires "_"n
# dash must be the last char to be reused as regex
CODE_CHARACTERS = string.ascii_lowercase + string.digits + '_-'


class FamilyFileGenerator:

    """Family file creator object."""

    def __init__(self,
                 url: Optional[str] = None,
                 name: Optional[str] = None,
                 dointerwiki: Optional[str] = None,
                 verify: Optional[str] = None) -> None:
        """
        Parameters are optional. If not given the script asks for the values.

        :param url: an url from where the family settings are loaded
        :param name: the family name without "_family.py" tail.
        :param dointerwiki: Predefined answer to add multiple site
            codes. Pass `Y` or `y` for yes `N` or `n` for no and
            `E` or `e` if you want to edit the collection of sites.
        :param verify: If a certificate verification failes, you may
            pass `Y` or `y` to disable certificate validaton `N` or `n`
            to keep it enabled.
        """
        from pywikibot.scripts import _import_with_no_user_config

        # from pywikibot.site_detect import MWSite and
        # from pywikibot.config import base_dir
        # when required but disable user-config checks
        # so the family can be created first,
        # and then used when generating the user-config
        self.Wiki = _import_with_no_user_config(
            'pywikibot.site_detect').site_detect.MWSite
        self.base_dir = _import_with_no_user_config(
            'pywikibot.config').config.base_dir

        self.base_url = url
        self.name = name
        self.dointerwiki = dointerwiki
        self.verify = verify

        self.wikis = {}  # {'https://wiki/$1': Wiki('https://wiki/$1'), ...}
        self.langs = []  # [Wiki('https://wiki/$1'), ...]

    def get_params(self) -> bool:  # pragma: no cover
        """Ask for parameters if necessary."""
        if self.base_url is None:
            with suppress(KeyboardInterrupt):
                self.base_url = input('Please insert URL to wiki: ')
            if not self.base_url:
                return False

        if self.name is None:
            with suppress(KeyboardInterrupt):
                self.name = input('Please insert a short name (eg: freeciv): ')
            if not self.name:
                return False

        if any(x not in NAME_CHARACTERS for x in self.name):
            print('ERROR: Name of family "{}" must be ASCII letters and '
                  'digits [a-zA-Z0-9]'.format(self.name))
            return False

        return True

    def get_wiki(self):
        """Get wiki from base_url."""
        import pywikibot
        from pywikibot.exceptions import FatalServerError
        print('Generating family file from ' + self.base_url)
        for verify in (True, False):
            try:
                w = self.Wiki(self.base_url, verify=verify)
            except FatalServerError:
                pywikibot.error(
                    pywikibot.comms.http.SSL_CERT_VERIFY_FAILED_MSG)
                pywikibot.exception()
                if not pywikibot.bot.input_yn(
                    'Retry with disabled ssl certificate validation',
                    default=self.verify, automatic_quit=False,
                        force=self.verify is not None):
                    break
            else:
                return w, verify
        return None, None

    def run(self) -> None:
        """Main method, generate family file."""
        if not self.get_params():
            return

        w, verify = self.get_wiki()
        if w is None:
            return

        self.wikis[w.lang] = w
        print('\n=================================='
              '\nAPI url: {w.api}'
              '\nMediaWiki version: {w.version}'
              '\n==================================\n'.format(w=w))

        self.getlangs(w)
        self.getapis()
        self.writefile(verify)

    def getlangs(self, w) -> None:
        """Determine site code of a family."""
        print('Determining other sites...', end='')
        try:
            self.langs = w.langs
            print(' '.join(sorted(wiki['prefix'] for wiki in self.langs)))
        except Exception as e:  # pragma: no cover
            self.langs = []
            print(e, '; continuing...')

        if len([lang for lang in self.langs if lang['url'] == w.iwpath]) == 0:
            if w.private_wiki:
                w.lang = self.name
            self.langs.append({'language': w.lang,
                               'local': '',
                               'prefix': w.lang,
                               'url': w.iwpath})

        code_len = len(self.langs)
        if code_len > 1:
            if self.dointerwiki is None:
                makeiw = input(
                    '\nThere are {} sites available.'
                    '\nDo you want to generate interwiki links? '
                    'This might take a long time. ([y]es/[N]o/[e]dit)'
                    .format(code_len)).lower()
            else:
                makeiw = self.dointerwiki

            if makeiw == 'n':
                self.langs = [wiki for wiki in self.langs
                              if wiki['url'] == w.iwpath]
            elif makeiw == 'e':
                for wiki in self.langs:
                    print(wiki['prefix'], wiki['url'])
                do_langs = input('Which sites do you want: ')
                self.langs = [wiki for wiki in self.langs
                              if wiki['prefix'] in do_langs
                              or wiki['url'] == w.iwpath]

        for wiki in self.langs:
            assert all(x in CODE_CHARACTERS for x in wiki['prefix']), \
                'Family {} code {} must be ASCII lowercase ' \
                'letters and digits [a-z0-9] or underscore/dash [_-]' \
                .format(self.name, wiki['prefix'])

    def getapis(self) -> None:
        """Load other site pages."""
        print('Loading wikis... ')
        for lang in self.langs:
            key = lang['prefix']
            print('  * {}... '.format(key), end='')
            if key not in self.wikis:
                try:
                    self.wikis[key] = self.Wiki(lang['url'])
                    print('downloaded')
                except Exception as e:  # pragma: no cover
                    print(e)
            else:
                print('in cache')

    def writefile(self, verify) -> None:
        """Write the family file."""
        fn = os.path.join(self.base_dir, 'families',
                          '{}_family.py'.format(self.name))
        print('Writing {}... '.format(fn))

        if os.path.exists(fn) and input('{} already exists. Overwrite? (y/n)'
                                        .format(fn)).lower() == 'n':
            print('Terminating.')
            sys.exit(1)

        code_hostname_pairs = '\n        '.join(
            "'{code}': '{hostname}',".format(
                code=k, hostname=urlparse(w.server).netloc
            ) for k, w in self.wikis.items())

        code_path_pairs = '\n            '.join(
            "'{code}': '{path}',".format(code=k, path=w.scriptpath)
            for k, w in self.wikis.items())

        code_protocol_pairs = '\n            '.join(
            "'{code}': '{protocol}',".format(
                code=k, protocol=urlparse(w.server).scheme
            ) for k, w in self.wikis.items())

        content = family_template % {
            'url': self.base_url, 'name': self.name,
            'code_hostname_pairs': code_hostname_pairs,
            'code_path_pairs': code_path_pairs,
            'code_protocol_pairs': code_protocol_pairs}
        if not verify:
            # assuming this is the same for all codes
            content += """

    def verify_SSL_certificate(self, code: str) -> bool:
        return False
"""
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        with codecs.open(fn, 'w', 'utf-8') as fh:
            fh.write(content)


family_template = """\
\"\"\"
This family file was auto-generated by generate_family_file.py script.

Configuration parameters:
  url = %(url)s
  name = %(name)s

Please do not commit this to the Git repository!
\"\"\"
from pywikibot import family


class Family(family.Family):  # noqa: D101

    name = '%(name)s'
    langs = {
        %(code_hostname_pairs)s
    }

    def scriptpath(self, code):
        return {
            %(code_path_pairs)s
        }[code]

    def protocol(self, code):
        return {
            %(code_protocol_pairs)s
        }[code]
"""


def main() -> None:
    """Process command line arguments and generate a family file."""
    if len(sys.argv) > 1 and sys.argv[1] == '-help':
        print(__doc__)
    else:
        FamilyFileGenerator(*sys.argv[1:]).run()


if __name__ == '__main__':
    main()
