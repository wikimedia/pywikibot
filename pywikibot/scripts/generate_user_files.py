#!/usr/bin/env python3
"""Script to create user-config.py. Other file names are not supported.

.. versionchanged:: 7.0
   moved to pywikibot.scripts folder.
.. versionchanged:: 8.0
   let user the choice which section to be copied.
   Also EXTERNAL EDITOR SETTINGS section can be copied.
"""
#
# (C) Pywikibot team, 2010-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from textwrap import fill
from typing import NamedTuple

from pywikibot.backports import Callable
from pywikibot.scripts import _import_with_no_user_config


# DISABLED_SECTIONS cannot be copied; variables must be set manually
DISABLED_SECTIONS = {
    'USER INTERFACE SETTINGS',  # uses sys
}
OBSOLETE_SECTIONS = {
    'ACCOUNT SETTINGS',  # already set
}
SCRIPT_SECTIONS = {
    'INTERWIKI SETTINGS',
    'SOLVE_DISAMBIGUATION SETTINGS',
    'WEBLINK CHECKER SETTINGS',
    'REPLICATION BOT SETTINGS',
}

# Disable user-config usage as we are creating it here
pywikibot = _import_with_no_user_config('pywikibot')
config, __url__ = pywikibot.config, pywikibot.__url__
base_dir = pywikibot.config.base_dir

console_encoding: str | None
try:
    console_encoding = sys.stdout.encoding
# unittests fails with "StringIO instance has no attribute 'encoding'"
except AttributeError:
    console_encoding = None

if console_encoding is None or sys.platform == 'cygwin':
    console_encoding = 'iso-8859-1'

USER_BASENAME = 'user-config.py'
PASS_BASENAME = 'user-password.py'


def change_base_dir():
    """Create a new user directory."""
    while True:
        new_base = pywikibot.input('New user directory? ')
        new_base = os.path.abspath(new_base)
        if os.path.exists(new_base):
            if os.path.isfile(new_base):
                pywikibot.error('there is an existing file with that name.')
                continue
            # make sure user can read and write this directory
            if not os.access(new_base, os.R_OK | os.W_OK):
                pywikibot.error('directory access restricted')
                continue
            pywikibot.info('Using existing directory')
        else:
            try:
                os.mkdir(new_base, pywikibot.config.private_files_permission)
            except Exception as e:
                pywikibot.error(f'directory creation failed: {e}')
                continue
            pywikibot.info('Created new directory.')
        break

    if new_base == pywikibot.config.get_base_dir(new_base):
        # config would find that file
        return new_base

    msg = fill(f"""WARNING: Your user files will be created in the directory
'{new_base}' you have chosen. To access these files, you will either have
to use the argument "-dir:{new_base}" every time you run the bot, or set
the environment variable "PYWIKIBOT_DIR" equal to this directory name in
your operating system. See your operating system documentation for how to
set environment variables.""", width=76)
    pywikibot.info(msg)
    if pywikibot.input_yn('Is this OK?', default=False, automatic_quit=False):
        return new_base
    pywikibot.info('Aborting changes.')
    return False


def file_exists(filename) -> bool:
    """Return whether the file exists and print a message if it exists."""
    if os.path.exists(filename):
        pywikibot.info('{1} already exists in the target directory "{0}".'
                       .format(*os.path.split(filename)))
        return True
    return False


def get_site_and_lang(
    default_family: str | None = 'wikipedia',
    default_lang: str | None = 'en',
    default_username: str | None = None,
    force: bool = False
) -> tuple[str, str, str]:
    """Ask the user for the family, site code and username.

    :param default_family: The default family which should be chosen.
    :param default_lang: The default site code which should be chosen,
        if the family supports it.
    :param default_username: The default username which should be
        chosen.
    :return: The family, site code and username
    """
    known_families = sorted(pywikibot.config.family_files.keys())
    if default_family not in known_families:
        default_family = None
    fam = pywikibot.bot.input_list_choice(
        'Select family of sites we are working on, '
        'just enter the number or name',
        known_families,
        force=force,
        default=default_family)
    fam = pywikibot.family.Family.load(fam)
    if hasattr(fam, 'langs'):
        codes = [code for code in fam.codes if code in fam.langs]
        known_langs = codes + sorted(set(fam.langs.keys()).difference(codes))
    else:
        known_langs = []

    if not known_langs:
        pywikibot.info(f'There were no known site codes found in {fam.name}.')
        default_lang = None
    elif len(known_langs) == 1:
        pywikibot.info(f'The only known site code: {known_langs[0]}')
        default_lang = known_langs[0]
    else:
        if default_lang not in known_langs:
            if default_lang != 'en' and 'en' in known_langs:
                default_lang = 'en'
            else:
                default_lang = None
        if not force:
            pywikibot.info('This is the list of known site codes:')
            text = fill(', '.join(known_langs), width=79)
            if default_lang:
                text = text.replace(
                    f' {default_lang},',
                    f' <<lightblue>>{default_lang}<<default>>,',
                )
            pywikibot.info(text)

    message = "The site code of the site we're working on"
    mycode = None
    while not mycode:
        mycode = pywikibot.input(message, default=default_lang, force=force)
        if known_langs and mycode and mycode not in known_langs \
           and not pywikibot.input_yn(
               fill(f'The site code {mycode!r} is not in the list of known'
                    ' sites. Do you want to continue?'),
               default=False, automatic_quit=False):
            mycode = None

    message = f'Username on {mycode}:{fam.name}'
    username = pywikibot.input(message, default=default_username, force=force)
    # Escape ''s
    if username:
        username = username.replace("'", "\\'")
    return fam.name, mycode, username


EXTENDED_CONFIG = """\
# This is an automatically generated file. You can find more
# configuration parameters in 'config.py' file or refer
# https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.config.html

# The family of sites to be working on.
# Pywikibot will import families/xxx_family.py so if you want to change
# this variable, you have to ensure that such a file exists. You may use
# generate_family_file to create one.
family = '{main_family}'

# The site code (language) of the site to be working on.
mylang = '{main_code}'

# The dictionary usernames should contain a username for each site where you
# have a bot account. If you have a unique username for all sites of a
# family , you can use '*'
{usernames}

# The list of BotPasswords is saved in another file. Import it if needed.
# See https://www.mediawiki.org/wiki/Manual:Pywikibot/BotPasswords to know how
# use them.
{botpasswords}

{config_text}"""

SMALL_CONFIG = """\
family = '{main_family}'
mylang = '{main_code}'
{usernames}
{botpasswords}
"""

PASSFILE_CONFIG = """\
# This is an automatically generated file used to store
# BotPasswords.
#
# As a simpler (but less secure) alternative to OAuth, MediaWiki allows bot
# users to uses BotPasswords to limit the permissions given to a bot.
# When using BotPasswords, each instance gets keys. This combination can only
# access the API, not the normal web interface.
#
# See https://www.mediawiki.org/wiki/Manual:Pywikibot/BotPasswords for more
# information.
{botpasswords}"""


class _ConfigSection(NamedTuple):
    head: str
    info: str
    section: str


def parse_sections() -> list:
    """Parse sections from config.py file.

    config.py will be in the pywikibot/ directory whereas
    generate_user_files script is in pywikibot/scripts.

    :return: a list of _ConfigSection named tuples.
    """
    data = []

    config_path = Path(__file__).resolve().parents[1].joinpath('config.py')
    config_file = config_path.read_text(encoding='utf-8')

    result = re.findall(
        '^(?P<section># #{5,} (?P<head>[A-Z][A-Z_ ]+[A-Z]) #{5,}\r?\n'
        '(?:^#?\r?\n)?'  # There may be an empty or short line after header
        '(?P<comment>(?:^# .+?)+)'  # first comment is used as help string
        '^.*?)'  # catch the remaining text
        '^(?=# #{5,}|# ={5,})',  # until section end marker
        config_file, re.MULTILINE | re.DOTALL)

    for section, head, comment in result:
        info = ' '.join(text.strip('# ') for text in comment.splitlines())
        data.append(_ConfigSection(head, info, section))
    return data


def copy_sections(force: bool = False, default: str = 'n') -> str | None:
    """Take config sections and copy them to user-config.py.

    .. versionchanged:: 8.0
       *force* and *default* options were added.

    :param force: Copy all sections if force is True
    :param default: Default answer for input_sections.
        Should be 'a' for all or 'n' for none to copy.
    :return: config text of all selected sections.
    """
    sections = parse_sections()
    if not sections:  # Something is wrong with the regex
        return None

    # copy framework settings
    copies = input_sections(
        'framework', sections, force=force, default=default,
        skip=lambda x: x.head not in (DISABLED_SECTIONS
                                      | OBSOLETE_SECTIONS
                                      | SCRIPT_SECTIONS))

    # copy scripts settings
    copies += input_sections(
        'scripts', sections, force=force, default=default,
        skip=lambda x: x.head in SCRIPT_SECTIONS)

    return ''.join(copies)


def input_sections(variant: str,
                   sections: list[_ConfigSection],
                   skip: Callable | None = None,
                   force: bool = False,
                   default: str = 'n') -> list[str]:
    """Ask for settings to copy.

    .. versionadded:: 8.0

    :param variant: Variant of the setting section. Either 'framework'
        or 'scripts'
    :param sections: A sections list previously read from the config file
    :param skip: a filter function
    :param force: Force input if True
    """
    # First ask what to do which the whole section type variant
    select = 'h'
    answers = [('Yes', 'y'), ('All', 'a'), ('None', 'n'), ('Help', 'h')]
    while select == 'h':
        select = pywikibot.input_choice(
            f'Do you want to select {variant} setting sections?',
            answers, default=default, force=force, automatic_quit=False)
        if select == 'h':  # pragma: no cover
            answers.pop(-1)
            pywikibot.info(
                f'The following {variant} setting sections are provided:')
            for item in filter(skip, sections):
                pywikibot.info(item.head)

    copies = []
    # Now ask for a single section of the given variant
    # or use all or none of them
    choice = {'a': 'all', 'n': 'none', 'y': 'h'}[select]  # mapping
    for item in filter(skip, sections):
        answers = [('Yes', 'y'), ('No', 'n'), ('Help', 'h')]
        while choice == 'h':  # pragma: no cover
            choice = pywikibot.input_choice(
                f'Do you want to add {item.head} section?',
                answers, default='n', force=force, automatic_quit=False)
            if choice == 'h':
                answers.pop(-1)
                pywikibot.info(fill(item.info))
        if choice in ('all', 'y'):
            copies.append(item.section)  # Fill the mutable directly
        if choice not in ('all', 'none'):
            choice = 'h'

    return copies


class _UserItem(NamedTuple):
    family: str
    code: str
    name: str


def create_user_config(
    main_family: str,
    main_code: str,
    main_username: str,
    force: bool = False
) -> None:
    """Create a user-config.py in base_dir.

    Create a user-password.py if necessary.
    """
    f_user = Path(base_dir, USER_BASENAME)
    f_pass = Path(base_dir, PASS_BASENAME)

    userlist = []
    if force and not config.verbose_output:
        if main_username:
            userlist = [_UserItem(main_family, main_code, main_username)]
    else:
        while True:
            userlist += [_UserItem(*get_site_and_lang(
                main_family, main_code, main_username, force=force))]
            if not pywikibot.input_yn('Do you want to add any other projects?',
                                      force=force,
                                      default=False, automatic_quit=False):
                break

    # For each different username entered, ask if user wants to save a
    # BotPassword (username, BotPassword name, BotPassword pass)
    msg: str | None = fill(
        f'See {__url__}/BotPasswords to know how to get codes. '
        f'Please note that plain text in {f_pass} and anyone with read'
        ' access to that directory will be able read the file.'
    )
    botpasswords = []
    userset = {user.name for user in userlist}
    for username in userset:
        if pywikibot.input_yn('Do you want to add a BotPassword for '
                              f'{username}?', force=force, default=False):
            if msg:
                pywikibot.info(msg)
            msg = None
            message = f'BotPassword\'s "bot name" for {username}'
            botpasswordname = pywikibot.input(message, force=force)
            message = f'BotPassword\'s "password" for "{botpasswordname}" ' \
                      '(no characters will be shown)' \

            botpasswordpass = pywikibot.input(message, force=force,
                                              password=True)
            if botpasswordname and botpasswordpass:
                botpasswords.append((username, botpasswordname,
                                     botpasswordpass))

    if not userlist:  # Show a sample
        usernames = (
            f"# usernames['{main_family}']['{main_code}'] = 'MyUsername'")
    else:
        usernames = '\n'.join(
            f"usernames['{user.family}']['{user.code}'] = '{user.name}'"
            for user in userlist
        )
        # Arbitrarily use the first key as default settings
        main_family, main_code = userlist[0].family, userlist[0].code
    botpasswords = '\n'.join(
        "('{}', BotPassword('{}', {!r}))".format(*botpassword)
        for botpassword in botpasswords)

    config_text = copy_sections(force=force)
    if config_text:
        config_content = EXTENDED_CONFIG
    else:
        pywikibot.info('Creating a small variant of user-config.py')
        config_content = SMALL_CONFIG

    try:
        # Finally save user-config.py
        f_user.write_text(
            config_content.format(
                main_family=main_family,
                main_code=main_code,
                usernames=usernames,
                config_text=config_text,
                botpasswords='password_file = ' + (f'"{PASS_BASENAME}"'
                                                   if botpasswords else 'None')
            ),
            encoding='utf-8'
        )
        pywikibot.info(f"'{f_user}' written.")
    except BaseException:
        f_user.unlink(missing_ok=True)
        raise

    save_botpasswords(botpasswords, f_pass)


def save_botpasswords(botpasswords: str, path: Path) -> None:
    """Write botpasswords to file.

    :param botpasswords: botpasswords for password file
    :param path: file path for password file
    :raises OSError: OSError during writing the file
    """
    if botpasswords:
        # Save user-password.py if necessary
        # user-config.py is already created at this point
        # therefore pywikibot.tools can be imported safely
        from pywikibot.tools import file_mode_checker
        try:
            # First create an empty file with good permissions, before writing
            # the content
            for content in ('',
                            PASSFILE_CONFIG.format(botpasswords=botpasswords)):
                path.write_text(content, encoding='utf-8')
                file_mode_checker(path,
                                  mode=config.private_files_permission,
                                  quiet=not content)
            pywikibot.info(f"'{path}' written.")
        except OSError:
            path.unlink(missing_ok=True)
            raise


def ask_for_dir_change(force) -> tuple[bool, bool]:
    """Ask whether the base directory is has to be changed.

    Only give option for directory change if user-config.py or user-
    password already exists in the directory. This will repeat if user-
    config.py also exists in the requested directory.

    :param force: Skip asking for directory change
    :type force: bool
    :return: whether user file or password file exists already
    """
    global base_dir

    pywikibot.info(f'\nYour default user directory is "{base_dir}"')
    while True:
        # Show whether file exists
        userfile = file_exists(os.path.join(base_dir, USER_BASENAME))
        passfile = file_exists(os.path.join(base_dir, PASS_BASENAME))
        if force and not config.verbose_output or not (userfile or passfile):
            break
        if pywikibot.input_yn(
                'Would you like to change the directory?',
                default=True, automatic_quit=False, force=force):
            new_base = change_base_dir()
            if new_base:
                base_dir = new_base
        else:
            break
    return userfile, passfile


def main(*args: str) -> None:
    """Process command line arguments and generate user-config.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    # set the config family and mylang values to an invalid state so that
    # the script can detect that the command line arguments -family & -lang
    # or -site were used and handle_args has updated these config values,
    # and 'force' mode can be activated below.
    config.family, config.mylang = 'wikipedia', None

    local_args = pywikibot.handle_args(args)
    if local_args:
        pywikibot.info('Unknown argument{}: {}'
                       .format('s' if len(local_args) > 1 else '',
                               ', '.join(local_args)))
        return

    pywikibot.info('You can abort at any time by pressing ctrl-c')
    if config.mylang is not None:
        force = True
        pywikibot.info('Automatically generating user-config.py')
    else:
        force = False
        # Force default site of en.wikipedia
        config.family, config.mylang = 'wikipedia', 'en'

    username = config.usernames[config.family].get(config.mylang)

    try:
        has_userfile, has_passfile = ask_for_dir_change(force)
        if not (has_userfile or has_passfile):
            create_user_config(config.family, config.mylang, username,
                               force=force)
    except KeyboardInterrupt:
        pywikibot.info('\nScript terminated by user.')

    # Creation of user-fixes.py has been replaced by an example file.


if __name__ == '__main__':
    main()
