#!/usr/bin/env python3
"""
Script to upload images to Wikipedia.

The following parameters are supported:

  -keep         Keep the filename as is
  -filename:    Target filename without the namespace prefix
  -prefix:      Add specified prefix to every filename.
  -noverify     Do not ask for verification of the upload description if one
                is given
  -abortonwarn: Abort upload on the specified warning type. If no warning type
                is specified, aborts on any warning.
  -ignorewarn:  Ignores specified upload warnings. If no warning type is
                specified, ignores all warnings. Use with caution
  -chunked:     Upload the file in chunks (more overhead, but restartable). If
                no value is specified the chunk size is 1 MiB. The value must
                be a number which can be preceded by a suffix. The units are:

                    No suffix: Bytes
                    'k': Kilobytes (1000 B)
                    'M': Megabytes (1000000 B)
                    'Ki': Kibibytes (1024 B)
                    'Mi': Mebibytes (1024x1024 B)

                The suffixes are case insensitive.
  -async        Make potentially large file operations asynchronous on the
                server side when possible.
  -always       Don't ask the user anything. This will imply -keep and
                -noverify and require that either -abortonwarn or -ignorewarn
                is defined for all. It will also require a valid file name and
                description. It'll only overwrite files if -ignorewarn includes
                the 'exists' warning.
  -recursive    When the filename is a directory it also uploads the files from
                the subdirectories.
  -summary:     Pick a custom edit summary for the bot.
  -descfile:    Specify a filename where the description is stored

It is possible to combine -abortonwarn and -ignorewarn so that if the specific
warning is given it won't apply the general one but more specific one. So if it
should ignore specific warnings and abort on the rest it's possible by defining
no warning for -abortonwarn and the specific warnings for -ignorewarn. The
order does not matter. If both are unspecific or a warning is specified by
both, it'll prefer aborting.

If any other arguments are given, the first is either URL, filename or
directory to upload, and the rest is a proposed description to go with the
upload. If none of these are given, the user is asked for the directory, file
or URL to upload. The bot will then upload the image to the wiki.

The script will ask for the location of an image(s), if not given as a
parameter, and for a description.
"""
#
# (C) Pywikibot team, 2003-2022
#
# Distributed under the terms of the MIT license.
#
import codecs
import math
import os
import re

import pywikibot
from pywikibot.bot import suggest_help
from pywikibot.specialbots import UploadRobot


CHUNK_SIZE_REGEX = re.compile(
    r'-chunked(?::(\d+(?:\.\d+)?)[ \t]*(k|ki|m|mi)?b?)?', re.I)


def get_chunk_size(match) -> int:
    """Get chunk size."""
    if not match:
        pywikibot.error('Chunk size parameter is not valid.')
        chunk_size = 0
    elif match[1]:  # number was in there
        base = float(match[1])
        if match[2]:  # suffix too
            suffix = match[2].lower()
            if suffix == 'k':
                suffix = 1000
            elif suffix == 'm':
                suffix = 1000000
            elif suffix == 'ki':
                suffix = 1 << 10
            elif suffix == 'mi':
                suffix = 1 << 20
        else:
            suffix = 1
        chunk_size = math.trunc(base * suffix)
    else:
        chunk_size = 1 << 20  # default to 1 MiB
    return chunk_size


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    url = ''
    description = []
    summary = None
    keep_filename = False
    always = False
    use_filename = None
    filename_prefix = None
    verify_description = True
    aborts = set()
    ignorewarn = set()
    chunk_size = 0
    asynchronous = False
    recursive = False
    description_file = None

    # process all global bot args
    # returns a list of non-global args, i.e. args for upload.py
    local_args = pywikibot.handle_args(args)
    for option in local_args:
        arg, _, value = option.partition(':')
        if arg == '-always':
            keep_filename = True
            always = True
            verify_description = False
        elif arg == '-recursive':
            recursive = True
        elif arg == '-keep':
            keep_filename = True
        elif arg == '-filename':
            use_filename = value
        elif arg == '-prefix':
            filename_prefix = value
        elif arg == '-summary':
            summary = value
        elif arg == '-noverify':
            verify_description = False
        elif arg == '-abortonwarn':
            if value and aborts is not True:
                aborts.add(value)
            else:
                aborts = True
        elif arg == '-ignorewarn':
            if value and ignorewarn is not True:
                ignorewarn.add(value)
            else:
                ignorewarn = True
        elif arg == '-chunked':
            match = CHUNK_SIZE_REGEX.fullmatch(option)
            chunk_size = get_chunk_size(match)
        elif arg == '-async':
            asynchronous = True
        elif arg == '-descfile':
            description_file = value
        elif not url:
            url = option
        else:
            description.append(option)

    description = ' '.join(description)

    if description_file:
        if description:
            pywikibot.error('Both a description and a -descfile were '
                            'provided. Please specify only one of those.')
            return
        with codecs.open(description_file,
                         encoding=pywikibot.config.textfile_encoding) as f:
            description = f.read().replace('\r\n', '\n')

    while not ('://' in url or os.path.exists(url)):
        if not url:
            error = 'No input filename given.'
        else:
            error = 'Invalid input filename given.'
            if not always:
                error += ' Try again.'
        if always:
            url = None
            break
        pywikibot.info(error)
        url = pywikibot.input('URL, file or directory where files are now:')

    if always and (aborts is not True and ignorewarn is not True
                   or not description or url is None):
        additional = ''
        missing = []
        if url is None:
            missing += ['filename']
            additional = error + ' '
        if description is None:
            missing += ['description']
        if aborts is not True and ignorewarn is not True:
            additional += ('Either -ignorewarn or -abortonwarn must be '
                           'defined for all codes. ')
        additional += 'Unable to run in -always mode'
        suggest_help(missing_parameters=missing, additional_text=additional)
        return

    if os.path.isdir(url):
        file_list = []
        for directory_info in os.walk(url):
            if not recursive:
                # Do not visit any subdirectories
                directory_info[1][:] = []
            for dir_file in directory_info[2]:
                file_list.append(os.path.join(directory_info[0], dir_file))
        url = file_list
    else:
        url = [url]

    bot = UploadRobot(url, description=description, use_filename=use_filename,
                      keep_filename=keep_filename,
                      verify_description=verify_description, aborts=aborts,
                      ignore_warning=ignorewarn, chunk_size=chunk_size,
                      asynchronous=asynchronous,
                      always=always, summary=summary,
                      filename_prefix=filename_prefix)
    bot.run()


if __name__ == '__main__':
    main()
