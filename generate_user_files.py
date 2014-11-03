# -*- coding: utf-8  -*-
""" Script to create user files (user-config.py, user-fixes.py). """
#
# (C) Pywikibot team, 2010-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import os
import sys
import re
import codecs
import math

# Disable user-config usage as we are creating it here
os.environ['PYWIKIBOT2_NO_USER_CONFIG'] = '1'
import pywikibot


base_dir = pywikibot.config2.base_dir
console_encoding = sys.stdout.encoding
# the directory in which generate_user_files.py is located
pywikibot_dir = sys.path[0]

if console_encoding is None or sys.platform == 'cygwin':
    console_encoding = "iso-8859-1"


def listchoice(clist, message=None, default=None):
    """Ask the user to select one entry from a list of entries."""
    if not message:
        message = u"Select"

    if default:
        message += u" (default: %s)" % default

    message += u": "

    line_template = u"{{0: >{0}}}: {{1}}".format(int(math.log10(len(clist)) + 1))
    for n, i in enumerate(clist):
        pywikibot.output(line_template.format(n + 1, i))

    while True:
        choice = pywikibot.input(message)

        if choice == '' and default:
            return default
        try:
            choice = int(choice) - 1
        except ValueError:
            try:
                choice = clist.index(choice)
            except IndexError:
                choice = -1

        # User typed choice number
        if 0 <= choice < len(clist):
            return clist[choice]
        else:
            pywikibot.error("Invalid response")


def change_base_dir():
    """Create a new user directory."""
    while True:
        new_base = pywikibot.input("New user directory? ")
        new_base = os.path.abspath(new_base)
        if os.path.exists(new_base):
            if os.path.isfile(new_base):
                pywikibot.error("there is an existing file with that name.")
                continue
            # make sure user can read and write this directory
            if not os.access(new_base, os.R_OK | os.W_OK):
                pywikibot.error("directory access restricted")
                continue
            pywikibot.output("Using existing directory")
            break
        else:
            try:
                os.mkdir(new_base, 0o700)
            except Exception:
                pywikibot.error("ERROR: directory creation failed")
                continue
            pywikibot.output("Created new directory.")
            break

    if new_base == pywikibot.config2.get_base_dir(new_base):
        # config would find that file
        return new_base
    from textwrap import wrap
    msg = wrap(u"""WARNING: Your user files will be created in the directory
'%(new_base)s' you have chosen. To access these files, you will either have
to use the argument "-dir:%(new_base)s" every time you run the bot, or set
the environment variable "PYWIKIBOT2_DIR" equal to this directory name in
your operating system. See your operating system documentation for how to
set environment variables.""" % locals(), width=76)
    for line in msg:
        pywikibot.output(line)
    if pywikibot.input_yn('Is this OK?', default=False, automatic_quit=False):
        return new_base
    pywikibot.output("Aborting changes.")
    return False


def file_exists(filename):
    """Return whether the file exists and print a message if it exists."""
    if os.path.exists(filename):
        pywikibot.output(u"'%s' already exists." % filename)
        return True
    return False


def get_site_and_lang(default_family='wikipedia', default_lang='en',
                      default_username=None):
    """
    Ask the user for the family, language and username.

    @param default_family: The default family which should be chosen.
    @type default_family: None or str
    @param default_lang: The default language which should be chosen, if the
        family supports this language.
    @type default_lang: None or str
    @param default_username: The default username which should be chosen.
    @type default_username: None or str
    @return: The family, language and username
    @rtype: tuple of three str
    """
    known_families = sorted(pywikibot.config2.family_files.keys())
    if default_family not in known_families:
        default_family = None
    fam = listchoice(known_families,
                     u"Select family of sites we are working on, "
                     u"just enter the number or name",
                     default=default_family)
    fam = pywikibot.family.Family.load(fam)
    if hasattr(fam, "langs"):
        if hasattr(fam, "languages_by_size"):
            key = {lang: i for i, lang in enumerate(fam.languages_by_size)}.get
            by_size = sorted(
                set(fam.langs.keys()).intersection(fam.languages_by_size),
                key=key)
        else:
            by_size = []
        known_langs = by_size + sorted(
            set(fam.langs.keys()).difference(by_size))
    else:
        known_langs = []

    if len(known_langs) == 0:
        pywikibot.output('There were no known languages found in {0}.'.format(fam.name))
        default_lang = None
    elif len(known_langs) == 1:
        pywikibot.output('The only known language: {0}'.format(known_langs[0]))
        default_lang = known_langs[0]
    else:
        pywikibot.output("This is the list of known languages:")
        pywikibot.output(u", ".join(known_langs))
        if default_lang not in known_langs:
            if default_lang != 'en' and 'en' in known_langs:
                default_lang = 'en'
            else:
                default_lang = None
    message = "The language code of the site we're working on"
    if default_lang:
        message += " (default: '{0}')".format(default_lang)
    message += ":"
    mylang = None
    while not mylang:
        mylang = pywikibot.input(message) or default_lang
        if known_langs and mylang and mylang not in known_langs:
            if not pywikibot.input_yn("The language code {0} is not in the "
                                      "list of known languages. Do you want "
                                      "to continue?".format(mylang),
                                      default=False, automatic_quit=False):
                mylang = None

    username = None
    message = u"Username on {0}:{1}".format(mylang, fam.name)
    if default_username:
        message += " (default: '{0}')".format(default_username)
    message += ":"
    while not username:
        username = pywikibot.input(message) or default_username
        if not username:
            pywikibot.error('The username may not be empty.')
    if sys.version_info == 2:
        username = username.decode(console_encoding)
    # Escape ''s
    username = username.replace("'", "\\'")
    return fam.name, mylang, username

EXTENDED_CONFIG = u"""# -*- coding: utf-8  -*-

# This is an automatically generated file. You can find more configuration
# parameters in 'config.py' file.

# The family of sites to work on by default.
#
# ‘site.py’ imports ‘families/xxx_family.py’, so if you want to change
# this variable, you need to use the name of one of the existing family files
# in that folder or write your own, custom family file.
#
# For ‘site.py’ to be able to read your custom family file, you must
# save it to ‘families/xxx_family.py’, where ‘xxx‘ is the codename of the
# family that your custom ‘xxx_family.py’ family file defines.
#
# You can also save your custom family files to a different folder. As long
# as you follow the ‘xxx_family.py’ naming convention, you can register your
# custom folder in this configuration file with the following global function:
#
#   register_families_folder(folder_path)
#
# Alternatively, you can register particular family files that do not need
# to follow the ‘xxx_family.py’ naming convention using the following
# global function:
#
#   register_family_file(family_name, file_path)
#
# Where ‘family_name’ is the family code (the ‘xxx’ in standard family file
# names) and ‘file_path’ is the absolute path to the target family file.
#
# If you use either of these functions to define the family to work on by
# default (the ‘family’ variable below), you must place the function call
# before the definition of the ‘family’ variable.
family = '{main_family}'

# The language code of the site we're working on.
mylang = '{main_lang}'

# The dictionary usernames should contain a username for each site where you
# have a bot account. If you have a unique username for all languages of a
# family , you can use '*'
{usernames}


{config_text}"""

SMALL_CONFIG = (u"# -*- coding: utf-8  -*-\n"
                u"family = '{main_family}'\n"
                u"mylang = '{main_lang}'\n"
                u"{usernames}\n")


def create_user_config():
    """Create a user-config.py in base_dir."""
    _fnc = os.path.join(base_dir, "user-config.py")
    if not file_exists(_fnc):
        main_family, main_lang, main_username = get_site_and_lang()

        usernames = [(main_family, main_lang, main_username)]
        while pywikibot.input_yn("Do you want to add any other projects?",
                                 default=False, automatic_quit=False):
            usernames += [get_site_and_lang(main_family, main_lang,
                                            main_username)]

        usernames = '\n'.join(
            u"usernames['{0}']['{1}'] = u'{2}'".format(*username)
            for username in usernames)

        extended = pywikibot.input_yn("Would you like the extended version of "
                                      "user-config.py, with explanations "
                                      "included?", automatic_quit=False)

        if extended:
            # config2.py will be in the pywikibot/ directory relative to this
            # script (generate_user_files)
            install = os.path.dirname(os.path.abspath(__file__))
            with codecs.open(os.path.join(install, "pywikibot", "config2.py"),
                             "r", "utf-8") as config_f:
                config = config_f.read()

            res = re.findall("^(############## (?:"
                             "LOGFILE|"
                             "INTERWIKI|"
                             "SOLVE_DISAMBIGUATION|"
                             "IMAGE RELATED|"
                             "TABLE CONVERSION BOT|"
                             "WEBLINK CHECKER|"
                             "DATABASE|"
                             "SEARCH ENGINE|"
                             "COPYRIGHT|"
                             "FURTHER"
                             ") SETTINGS .*?)^(?=#####|# =====)",
                             config, re.MULTILINE | re.DOTALL)
            config_text = '\n'.join(res)
            config_content = EXTENDED_CONFIG
        else:
            config_content = SMALL_CONFIG

        with codecs.open(_fnc, "w", "utf-8") as f:
            f.write(config_content.format(**locals()))
        pywikibot.output(u"'%s' written." % _fnc)


def create_user_fixes():
    """Create a basic user-fixes.py in base_dir."""
    _fnf = os.path.join(base_dir, "user-fixes.py")
    if not file_exists(_fnf):
        with codecs.open(_fnf, "w", "utf-8") as f:
            f.write(r"""# -*- coding: utf-8  -*-

#
# This is only an example. Don't use it.
#

fixes['example'] = {
    'regex': True,
    'msg': {
        '_default':u'no summary specified',
    },
    'replacements': [
        (r'\bword\b', u'two words'),
    ]
}

""")
        pywikibot.output(u"'%s' written." % _fnf)

if __name__ == "__main__":
    while True:
        pywikibot.output(u'\nYour default user directory is "%s"' % base_dir)
        if pywikibot.input_yn("Do you want to use that directory?",
                              default=False, automatic_quit=False):
            break
        else:
            new_base = change_base_dir()
            if new_base:
                base_dir = new_base
                break

    copied_config = False
    copied_fixes = False
    while True:
        if os.path.exists(os.path.join(base_dir, "user-config.py")):
            break
        if pywikibot.input_yn(
                "Do you want to copy user files from an existing Pywikibot "
                "installation?",
                automatic_quit=False):
            oldpath = pywikibot.input("Path to existing user-config.py?")
            if not os.path.exists(oldpath):
                pywikibot.error("Not a valid path")
                continue
            if os.path.isfile(oldpath):
                # User probably typed /user-config.py at the end, so strip it
                oldpath = os.path.dirname(oldpath)
            if not os.path.isfile(os.path.join(oldpath, "user-config.py")):
                pywikibot.error("No user_config.py found in that directory")
                continue
            import shutil
            shutil.copyfile(os.path.join(oldpath, "user-config.py"),
                            os.path.join(base_dir, "user-config.py"))
            copied_config = True

            if os.path.isfile(os.path.join(oldpath, "user-fixes.py")):
                shutil.copyfile(os.path.join(oldpath, "user-fixes.py"),
                                os.path.join(base_dir, "user-fixes.py"))
                copied_fixes = True

        else:
            break
    if not os.path.isfile(os.path.join(base_dir, "user-config.py")):
        if pywikibot.input_yn('Create user-config.py file? Required for '
                              'running bots.',
                              default=False, automatic_quit=False):
            create_user_config()
    elif not copied_config:
        pywikibot.output("user-config.py already exists in the directory")
    if not os.path.isfile(os.path.join(base_dir, "user-fixes.py")):
        if pywikibot.input_yn('Create user-fixes.py file? Optional and for '
                              'advanced users.',
                              default=False, automatic_quit=False):
            create_user_fixes()
    elif not copied_fixes:
        pywikibot.output("user-fixes.py already exists in the directory")
