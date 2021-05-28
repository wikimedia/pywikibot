#!/usr/bin/python
"""Script that updates the linktrails in family.py file.

linktrails contains a regex for each site code which holds letters that
can follow a wikilink and are regarded as part of this link. This depends
on the linktrail setting in LanguageXx.php. This maintenance script
retrieves the site settings from wikipedia family and updates the Family
linktrails dict.
"""
#
# (C) Pywikibot team, 2017-2021
#
# Distributed under the terms of the MIT license.
#

import codecs
import re
from contextlib import closing
from os.path import join

import pywikibot
from pywikibot.family import CODE_CHARACTERS
from pywikibot.tools import suppress_warnings


def format_string(code: str, pattern: str) -> str:
    """Format a single pattern line."""
    fmt = ' ' * 8 + "'{}': '{}'"
    code_len = len(code)
    pattern_len = len(pattern)
    if pattern_len > 63 - code_len:
        index = pattern_len // 2
        result = fmt.format(code, pattern[:index]) + '\n'
        result += ' ' * (code_len + 12) + "'{}',\n".format(pattern[index:])
    else:
        result = fmt.format(code, pattern) + ',\n'
    return result


def coroutine(func):
    """Decorator which starts coroutine."""
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        cr.send(None)
        return cr
    return start


@coroutine
def update_sites(fam):
    """Process linktrail for a given site code."""
    formatter = update_line()
    while True:
        code = yield

        with suppress_warnings(
            'Site wikipedia:[{}]+ instantiated using different code'
            .format(CODE_CHARACTERS),
            category=UserWarning,
                filename=r'.+pywikibot.tools.__init__\.py'):
            site = pywikibot.Site(code, 'wikipedia')

        if isinstance(site, pywikibot.site.RemovedSite):
            continue

        if site.code != code:
            pywikibot.output('"{}" is redirected to "{}"; skipping.'
                             .format(code, site.code))
            continue

        linktrail = site.siteinfo.get('general', expiry=True)['linktrail']
        oldtrail = fam.linktrails.get(code)
        formatter.send((code, oldtrail, linktrail))


@coroutine
def update_line():
    """Format linktrail for family file."""
    writer = update_family_file()
    matcher = update_matched_line(writer)
    while True:
        code, old, linktrail = yield
        line = format_string(code, old) if old else ''

        if not linktrail:
            writer.send(line)
            continue

        if linktrail == '/^()(.*)$/sD':  # empty linktrail
            line = format_string(code, '')
            writer.send(line)
            continue

        match = re.search(
            r'\((?:\:\?|\?\:)?\[(?P<pattern>.+?)\]'
            r'(?P<letters>(\|.)*)\)?\+\)',
            linktrail)

        if not match:
            pywikibot.output('"{}": No pattern found in "{}"'
                             .format(code, linktrail))
            writer.send(line)
            continue

        matcher.send((code, old, match))


@coroutine
def update_matched_line(writer):
    """Update matched linktrail."""
    while True:
        code, old, match = yield
        pattern = match.group('pattern')
        letters = match.group('letters')
        if pattern == 'a-z' and not letters:  # default
            if old:
                pywikibot.output('"{}" has default linktrail; '
                                 'removing {}'.format(code, old))
            continue

        if r'x{' in pattern:
            # replace unicode escape string by corresponding char
            pattern = re.sub(
                r'\\x\{([A-F0-9]{4})\}',
                lambda match: chr(int(match.group(1), 16)),
                pattern)

        if letters:
            pattern += ''.join(letters.split('|'))

        new = '[{}]*'.format(pattern)
        line = format_string(code, new)
        writer.send(line)


@coroutine
def update_family_file():
    """Collect linktrails and write them to family.py."""
    text = "    linktrails = {\n        '_default': '[a-z]*',\n"
    try:
        while True:
            text += yield
    except GeneratorExit:
        text += '    }'
        # write lintrails to family file
        pywikibot.output('Writing family file...')
        family_file_name = join('pywikibot', 'family.py')
        with codecs.open(family_file_name, 'r', 'utf8') as family_file:
            family_text = family_file.read()
        family_text = re.sub(r'(?ms)^ {4}linktrails.+?\}',
                             text, family_text, 1)
        with codecs.open(family_file_name, 'w', 'utf8') as family_file:
            family_file.write(family_text)


def update_linktrails(family):
    """Update linktrails for given family."""
    with closing(update_sites(family)) as updater:
        for code in sorted(family.langs):
            updater.send(code)


if __name__ == '__main__':
    site = pywikibot.Site('en', 'wikipedia')
    update_linktrails(site.family)
