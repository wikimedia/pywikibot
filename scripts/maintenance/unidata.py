#!/usr/bin/env python3
"""Script to update :mod:`pywikibot.tools._unidata`.

This script is for updating ``_first_upper_exception_dict``.

.. note:: I seems that running under the latest version of Python gives
   a superse of the older version and should be enough. But this is not
   tested completely.

.. versionadded:: 8.4
"""
#
# (C) Pywikibot team, 2018-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from json import dump, load
from queue import Queue
from re import findall
from sys import maxunicode
from threading import Thread

from pywikibot import Site
from pywikibot.comms.http import session
from pywikibot.family import Family


NUMBER_OF_THREADS = 26
FILEPATH = '/data/firstup_excepts.json'

# supported families by this script
families_list = [
    'wikibooks',
    'wikinews',
    'wikipedia',
    'wikiquote',
    'wikisource',
    'wikiversity',
    'wikivoyage',
    'wiktionary',
]


def chars_uppers_wikilinks():
    """Retrieve upper chars from MediaWiki using page titles."""
    n = 0
    chars = []
    uppers = []
    wikilinks = ''
    for i in range(maxunicode + 1):
        c = chr(i)
        uc = c.upper()
        if uc != c:
            n += 1
            chars.append(c)
            uppers.append(uc)
            # MediaWiki is first-letter case
            wikilinks += '[[MediaWiki:' + c + ']]\n'
    return chars, uppers, wikilinks


def process_site(fam_name, site_code):
    """Process title for a single site."""
    j = session.post(
        f'https://{site_code}.{fam_name}.org/w/api.php?'
        f'action=parse&contentmodel=wikitext&prop=text'
        f'&format=json&utf8',
        data={'text': wikilinks},
        timeout=10,
    ).json()
    pased_text = j['parse']['text']['*']
    titles = findall(r'title="[^:]*:(.)', pased_text)
    site_excepts = {}
    for i, original_char in enumerate(chars):
        title_char = titles[i]
        if uppers[i] != title_char:
            site_excepts[original_char] = title_char
    return site_excepts


def threads_target(q):
    """Thread processing a single site."""
    global families_excepts
    while True:
        try:
            fam, code = q.get()
        except TypeError:  # non-iterable NoneType object
            break
        site_excepts = process_site(fam, code)
        families_excepts[fam].setdefault(code, {}).update(site_excepts)
        q.task_done()


def spawn_threads(q):
    """Prepare several threads."""
    # TODO: use ThreadList instead
    threads = []
    for _ in range(NUMBER_OF_THREADS):
        t = Thread(target=threads_target, args=(q,))
        t.start()
        threads.append(t)
    return threads


def stop_threads(q, threads):
    """Stop threads."""
    for _ in range(NUMBER_OF_THREADS):
        q.put(None)
    for t in threads:
        t.join()


def main():
    """Main loop processing sites."""
    global families_excepts
    q = Queue()
    threads = spawn_threads(q)
    for fam_name in families_list:
        family = Family.load(fam_name)
        families_excepts.setdefault(fam_name, {})
        for site_code in family.codes:
            site = Site(site_code, family)
            if site.namespaces[8].case != 'first-letter':
                raise ValueError('MW namespace case is not first-letter')
            fam_code = (fam_name, site_code)
            if fam_code in {
                ('wikisource', 'www'),
                ('wikisource', 'mul'),
                ('wikiversity', 'test'),
            }:
                continue  # the API of these codes does not respond as expected
            q.put(fam_code)
    # block until all tasks are done
    q.join()
    stop_threads(q, threads)


def save_json(obj, path):
    """Save data to file."""
    with open(path, 'w', encoding='utf8') as f:
        dump(obj, f)


def load_json(path):
    """Load data from file."""
    try:
        with open(path, encoding='utf8') as f:
            return load(f)
    except OSError:
        print('File not found:', path)  # noqa: T201
        return {}


if __name__ == '__main__':
    chars, uppers, wikilinks = chars_uppers_wikilinks()
    # save_json({'chars': chars, 'uppers': uppers, 'wikilinks': wikilinks},
    #           'user-temp-save.json')
    # j = load_json('user-temp-save.json')
    # chars, uppers, wikilinks = j['chars'], j['uppers'], j['wikilinks']
    # families_excepts = load_json(FILEPATH)
    # main()
    # save_json(families_excepts, FILEPATH)
    print(process_site('wiktionary', 'fr'))  # noqa: T201
