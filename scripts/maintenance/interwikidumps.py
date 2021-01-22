#!/usr/bin/python
"""Script to convert interwiki dumps from pickle format to txt format."""
#
# (C) Pywikibot team, 2019-2020
#
# Distributed under the terms of the MIT license.
#
import codecs
import os
import pickle
import re

import pywikibot

from pywikibot import config2 as config


def pickle_files(path):
    """Retrieve pickle files."""
    pattern = r'(?P<old>(?P<new>\A(?P<fam>[a-z]+)-(?P<code>[a-z]+)\.)pickle\Z)'
    for filename in os.listdir(path):
        found = re.match(pattern, filename)
        if not found:
            continue

        old = found['old']
        if os.path.exists(os.path.join(path, old)):
            yield (old, found['new'] + 'txt',
                   pywikibot.Site(found['code'], found['fam']))


def read_content(filename):
    """Read content of pickle file."""
    try:
        with open(filename, 'rb') as f:
            titles = pickle.load(f)
    except (EOFError, IOError):
        pywikibot.exception()
        titles = None
    return titles


def write_content(filename, site, content):
    """Write content to txt file."""
    titles = [pywikibot.Page(site, title).title(as_link=True)
              for title in content]
    with codecs.open(filename, 'w', 'utf-8') as f:
        f.write('\r\n'.join(titles))
        f.write('\r\n')


def convert_dumps():
    """Convert interwikidump from pickle format to txt format."""
    folder = config.datafilepath('data', 'interwiki-dumps')
    for old_file, new_file, site in pickle_files(folder):
        # read old file
        pywikibot.output('\nReading {}...'.format(old_file))
        old_filepath = os.path.join(folder, old_file)
        titles = read_content(old_filepath)

        if not titles:
            pywikibot.error('Unable to read ' + old_file)
            continue

        # write new file
        pywikibot.output('Writing {}...'.format(new_file))
        write_content(os.path.join(folder, new_file), site, titles)

        # delete old file
        try:
            os.remove(old_filepath)
            pywikibot.output('Old dumpfile {} deleted'.format(old_file))
        except OSError as e:
            pywikibot.error('Cannot delete {} due to\n{}\nDo it manually.'
                            .format(old_file, e))


def main(*args):
    """Main function."""
    args = pywikibot.argvu[1:]
    if args and args[0] == '-help':
        pywikibot.output(__doc__)
    else:
        convert_dumps()


if __name__ == '__main__':
    main()
