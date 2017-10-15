#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to upload images to wikipedia.

Arguments:

  -keep         Keep the filename as is
  -filename     Target filename without the namespace prefix
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
  -always       Don't ask the user anything. This will imply -keep and
                -noverify and require that either -abortonwarn or -ignorewarn
                is defined for all. It will also require a valid file name and
                description. It'll only overwrite files if -ignorewarn includes
                the 'exists' warning.
  -recursive    When the filename is a directory it also uploads the files from
                the subdirectories.
  -summary      Pick a custom edit summary for the bot.

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
# (C) Rob W.W. Hooft, Andre Engels 2003-2004
# (C) Pywikibot team, 2003-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import math
import os
import re

import pywikibot
from pywikibot.bot import suggest_help
from pywikibot.specialbots import UploadRobot


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    url = u''
    description = []
    summary = None
    keepFilename = False
    always = False
    useFilename = None
    verifyDescription = True
    aborts = set()
    ignorewarn = set()
    chunk_size = 0
    chunk_size_regex = r'^-chunked(?::(\d+(?:\.\d+)?)[ \t]*(k|ki|m|mi)?b?)?$'
    chunk_size_regex = re.compile(chunk_size_regex, re.I)
    recursive = False

    # process all global bot args
    # returns a list of non-global args, i.e. args for upload.py
    for arg in pywikibot.handle_args(args):
        if arg:
            if arg == '-always':
                keepFilename = True
                always = True
                verifyDescription = False
            elif arg == '-recursive':
                recursive = True
            elif arg.startswith('-keep'):
                keepFilename = True
            elif arg.startswith('-filename:'):
                useFilename = arg[10:]
            elif arg.startswith('-summary'):
                summary = arg[9:]
            elif arg.startswith('-noverify'):
                verifyDescription = False
            elif arg.startswith('-abortonwarn'):
                if len(arg) > len('-abortonwarn:') and aborts is not True:
                    aborts.add(arg[len('-abortonwarn:'):])
                else:
                    aborts = True
            elif arg.startswith('-ignorewarn'):
                if len(arg) > len('-ignorewarn:') and ignorewarn is not True:
                    ignorewarn.add(arg[len('-ignorewarn:'):])
                else:
                    ignorewarn = True
            elif arg.startswith('-chunked'):
                match = chunk_size_regex.match(arg)
                if match:
                    if match.group(1):  # number was in there
                        base = float(match.group(1))
                        if match.group(2):  # suffix too
                            suffix = match.group(2).lower()
                            if suffix == "k":
                                suffix = 1000
                            elif suffix == "m":
                                suffix = 1000000
                            elif suffix == "ki":
                                suffix = 1 << 10
                            elif suffix == "mi":
                                suffix = 1 << 20
                            else:
                                pass  # huh?
                        else:
                            suffix = 1
                        chunk_size = math.trunc(base * suffix)
                    else:
                        chunk_size = 1 << 20  # default to 1 MiB
                else:
                    pywikibot.error('Chunk size parameter is not valid.')
            elif url == u'':
                url = arg
            else:
                description.append(arg)
    description = u' '.join(description)
    while not ("://" in url or os.path.exists(url)):
        if not url:
            error = 'No input filename given.'
        else:
            error = 'Invalid input filename given.'
            if not always:
                error += ' Try again.'
        if always:
            url = None
            break
        else:
            pywikibot.output(error)
        url = pywikibot.input(u'URL, file or directory where files are now:')
    if always and ((aborts is not True and ignorewarn is not True) or
                   not description or url is None):
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
        return False
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
    bot = UploadRobot(url, description=description, useFilename=useFilename,
                      keepFilename=keepFilename,
                      verifyDescription=verifyDescription,
                      aborts=aborts, ignoreWarning=ignorewarn,
                      chunk_size=chunk_size, always=always,
                      summary=summary)
    bot.run()


if __name__ == "__main__":
    main()
