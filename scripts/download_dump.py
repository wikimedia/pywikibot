#!/usr/bin/env python3
"""
This bot downloads dump from dumps.wikimedia.org.

This script supports the following command line parameters:

    -filename:#     The name of the file (e.g. abstract.xml)

    -storepath:#    The stored file's path.

    -dumpdate:#     The dumpdate date of the dump (default to `latest`)
                    formatted as YYYYMMDD.

.. note:: This script is a
   :py:obj:`ConfigParserBot <bot.ConfigParserBot>`. All options
   can be set within a settings file which is scripts.ini by default.
"""
#
# (C) Pywikibot team, 2017-2022
#
# Distributed under the terms of the MIT license.
#
import binascii
import os.path
from http import HTTPStatus
from os import remove, replace, symlink, urandom

import pywikibot
from pywikibot.bot import Bot, ConfigParserBot
from pywikibot.comms.http import fetch


class DownloadDumpBot(Bot, ConfigParserBot):

    """Download dump bot.

    .. versionchanged:: 7.0
       DownloadDumpBot is a ConfigParserBot
    """

    available_options = {
        'wikiname': '',
        'filename': '',
        'storepath': './',
        'dumpdate': 'latest',
    }

    @staticmethod
    def get_dump_name(db_name, typ, dumpdate):
        """Check if dump file exists locally in a Toolforge server."""
        db_path = f'/public/dumps/public/{db_name}/'
        if os.path.isdir(db_path):
            dump_filepath_template = (
                '/public/dumps/public/{db_name}/{date}/{db_name}-{date}-{typ}')
            if dumpdate != 'latest':
                dump_filepath = dump_filepath_template.format(
                    db_name=db_name, date=dumpdate, typ=typ)
                if os.path.isfile(dump_filepath):
                    return dump_filepath
            else:
                # Search for the "latest" dump
                dirs = [directory for directory in os.listdir(db_path) if
                        directory.isdigit()]
                dates = map(int, dirs)
                dates = sorted(dates, reverse=True)
                for date in dates:
                    dump_filepath = dump_filepath_template.format(
                        db_name=db_name, date=date, typ=typ)
                    if os.path.isfile(dump_filepath):
                        return dump_filepath
        return None

    def run(self) -> None:
        """Run bot."""
        def convert_from_bytes(total_bytes):
            for unit in ['B', 'K', 'M', 'G', 'T']:
                if abs(total_bytes) < 1024:
                    return str(total_bytes) + unit
                total_bytes = float(format(total_bytes / 1024.0, '.2f'))
            return str(total_bytes) + 'P'

        pywikibot.info('Downloading dump from ' + self.opt.wikiname)

        download_filename = '{wikiname}-{dumpdate}-{filename}'.format_map(
            self.opt)
        temp_filename = download_filename + '-' \
            + binascii.b2a_hex(urandom(8)).decode('ascii') + '.part'

        file_final_storepath = os.path.join(
            self.opt.storepath, download_filename)
        file_current_storepath = os.path.join(
            self.opt.storepath, temp_filename)

        # https://wikitech.wikimedia.org/wiki/Help:Toolforge/Dumps
        toolforge_dump_filepath = self.get_dump_name(
            self.opt.wikiname, self.opt.filename, self.opt.dumpdate)

        # First iteration for atomic download with temporary file
        # Second iteration for fallback non-atomic download
        for non_atomic in range(2):
            try:
                if toolforge_dump_filepath:
                    pywikibot.info('Symlinking file from '
                                   + toolforge_dump_filepath)
                    if non_atomic and os.path.exists(file_final_storepath):
                        remove(file_final_storepath)
                    symlink(toolforge_dump_filepath, file_current_storepath)
                else:
                    url = 'https://dumps.wikimedia.org/{}/{}/{}'.format(
                        self.opt.wikiname, self.opt.dumpdate,
                        download_filename)
                    pywikibot.info('Downloading file from ' + url)
                    response = fetch(url, stream=True)

                    if response.status_code != HTTPStatus.OK:
                        if response.status_code == HTTPStatus.NOT_FOUND:
                            pywikibot.info(
                                'File with name {filename!r}, from dumpdate '
                                '{dumpdate!r}, and wiki {wikiname!r} ({url}) '
                                "isn't available in the Wikimedia Dumps"
                                .format(url=url, **self.opt))
                        else:
                            pywikibot.info(
                                HTTPStatus(response.status_code).description)
                        return

                    with open(file_current_storepath, 'wb') as result_file:
                        total = int(response.headers['content-length'])
                        if total == -1:
                            pywikibot.warning("'content-length' missing in "
                                              'response headers')
                        downloaded = 0
                        parts = 50
                        display_string = ''

                        pywikibot.info()
                        for data in response.iter_content(100 * 1024):
                            result_file.write(data)

                            if total <= 0:
                                continue

                            downloaded += len(data)
                            done = int(parts * downloaded / total)
                            display = map(convert_from_bytes,
                                          (downloaded, total))
                            prior_display = display_string
                            display_string = '\r|{}{}|{}{}/{}'.format(
                                '=' * done,
                                '-' * (parts - done),
                                ' ' * 5,
                                *display)
                            # Add whitespace to cover up prior bar
                            display_string += ' ' * (
                                len(prior_display.rstrip())
                                - len(display_string.rstrip()))

                            pywikibot.info(display_string, newline=False)
                        pywikibot.info()

                # Rename the temporary file to the target file
                # if the download completes successfully
                if not non_atomic:
                    replace(file_current_storepath, file_final_storepath)
                    break

            except OSError as e:
                pywikibot.error(e)

                try:
                    remove(file_current_storepath)
                except OSError as e:
                    pywikibot.error(e)

                # If the atomic download fails, try without a temporary file
                # If the non-atomic download also fails, exit the script
                if non_atomic:
                    return

                pywikibot.info('Cannot make temporary file, '
                               'falling back to non-atomic download')
                file_current_storepath = file_final_storepath

        pywikibot.info('Done! File stored as ' + file_final_storepath)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    opts = {}
    unknown_args = []

    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        option, _, value = arg.partition(':')
        if option.startswith('-'):
            option = option[1:]

            if option == 'filename':
                opts[option] = value or pywikibot.input('Enter the filename: ')
                continue

            if option == 'storepath':
                opts[option] = os.path.abspath(value) or pywikibot.input(
                    'Enter the store path: ')
                continue

            if option == 'dumpdate':
                opts[option] = value or pywikibot.input(
                    'Enter the dumpdate of the dump: ')
                continue

        unknown_args.append(arg)

    missing = []
    if 'filename' not in opts:
        missing.append('-filename')

    if pywikibot.bot.suggest_help(missing_parameters=missing,
                                  unknown_parameters=unknown_args):
        return

    site = pywikibot.Site()
    opts['wikiname'] = site.dbName()

    bot = DownloadDumpBot(**opts)
    bot.run()


if __name__ == '__main__':
    main()
