"""
Module to define and load pywikibot configuration default and user preferences.

User preferences are loaded from a python file called `user-config.py`,
which may be located in directory specified by the environment variable
`PYWIKIBOT_DIR`, or the same directory as `pwb.py`, or in a directory
within the users home. See :py:obj:`get_base_dir` for more information.
The different file name can specified with global `-config` option.

If user config file cannot be found in any of those locations, this
module will fail to load unless the environment variable
`PYWIKIBOT_NO_USER_CONFIG` is set to a value other than `'0'`. i.e.
`PYWIKIBOT_NO_USER_CONFIG=1` will allow config to load without a user
config file. However, warnings will be shown if a user config file was
not loaded. To prevent these warnings, set `PYWIKIBOT_NO_USER_CONFIG=2`.
If Pywikibot is installed as a site-package the behaviour is like
`PYWIKIBOT_NO_USER_CONFIG=2` is set.

Functions made available to user config file:

 - user_home_path

Sets module global `base_dir` and `user_config_file` and provides
utility methods to build paths relative to base_dir:

 - makepath
 - datafilepath
 - shortpath

.. versionchanged:: 6.2
   config2 was renamed to config
.. versionchanged:: 8.0
   Editor settings has been revised. *editor* variable is None by
   default. Editor detection functions were moved to :mod:`editor`.
"""
#
# (C) Pywikibot team, 2003-2022
#
# Distributed under the terms of the MIT license.
#
import collections
import copy
import os
import platform
import re
import stat
import sys
import types
from locale import getlocale
from os import environ, getenv
from pathlib import Path
from textwrap import fill
from typing import Optional, TypeVar, Union
from warnings import warn
from zipfile import ZipFile, is_zipfile

from pywikibot.__metadata__ import __version__ as pwb_version
from pywikibot.backports import (
    DefaultDict,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Tuple,
    removeprefix,
    removesuffix,
)
from pywikibot.logging import error, output, warning
from pywikibot.tools import deprecated


_DabComDict = DefaultDict[str, Dict[str, str]]
_ValueType = TypeVar('_ValueType')


OSWIN32 = (sys.platform == 'win32')


# This frozen set should contain all imported modules/variables, so it must
# occur directly after the imports. At that point globals() only contains the
# names and some magic variables (like __name__)
_imports = frozenset(name for name in globals() if not name.startswith('_'))

__no_user_config = getenv('PYWIKIBOT_NO_USER_CONFIG')
if __no_user_config is None and 'site-packages' in Path(__file__).parts:
    __no_user_config = '2'
elif __no_user_config == '0':
    __no_user_config = None


class _ConfigurationDeprecationWarning(UserWarning):

    """Feature that is no longer supported."""


# IMPORTANT:
# Do not change any of the variables in this file. Instead, make a
# user config file (user-config.py), and overwrite values in there.

# Note: all variables defined in this module are made available to bots
# as configuration settings, *except* variable names beginning with an
# underscore (example: _variable). Be sure to use an underscore on any
# variables that are intended only for internal use and not to be
# exported to other modules.

_private_values = {'authenticate', 'db_password'}
_deprecated_variables = {
    'available_ssl_project', 'copyright_check_in_source_google',
    'copyright_check_in_source_msn', 'copyright_check_in_source_section_names',
    'copyright_check_in_source_yahoo', 'copyright_connection_tries',
    'copyright_economize_query', 'copyright_exceeded_in_queries',
    'copyright_exceeded_in_queries_sleep_hours', 'copyright_google',
    'copyright_max_query_for_page', 'copyright_msn', 'copyright_show_date',
    'copyright_show_length', 'copyright_skip_query', 'copyright_yahoo',
    'db_hostname', 'deIndentTables', 'fake_user_agent', 'flickr',
    'interwiki_contents_on_disk', 'line_separator', 'LS', 'msn_appid',
    'panoramio', 'persistent_http', 'proxy', 'special_page_limit',
    'splitLongParagraphs', 'sysopnames', 'use_mwparserfromhell',
    'use_SSL_onlogin', 'use_SSL_always', 'yahoo_appid',
}
_future_variables = {'absolute_import', 'division', 'unicode_literals'}

# ############# ACCOUNT SETTINGS ##############

# The family of sites we are working on. pywikibot will import
# families/xxx_family.py so if you want to change this variable,
# you need to write such a file if one does not exist.
family = 'wikipedia'
# The language code of the site we're working on.
mylang = 'language'
# If family and mylang are not modified from the above, the default is changed
# to test:test, which is test.wikipedia.org, at the end of this module.

# The dictionary usernames should contain a username for each site where you
# have a bot account. Please set your usernames by adding such lines to your
# user config file (user-config.py):
#
# usernames['wikipedia']['de'] = 'myGermanUsername'
# usernames['wiktionary']['en'] = 'myEnglishUsername'
#
# If you have a unique username for all languages of a family,
# you can use '*'
# usernames['wikibooks']['*'] = 'mySingleUsername'
# You may use '*' for family name in a similar manner.
#
usernames: Dict[str, Dict[str, str]] = collections.defaultdict(dict)
disambiguation_comment: _DabComDict = collections.defaultdict(dict)

# User agent format.
# For the meaning and more help in customization see:
# https://www.mediawiki.org/wiki/Manual:Pywikibot/User-agent
user_agent_format = ('{script_product} ({script_comments}) {pwb} ({revision}) '
                     '{http_backend} {python}')

# User agent description
# This is a free-form string that can be user to describe specific bot/tool,
# provide contact information, etc.
user_agent_description = None
# Fake user agent.
# Some external websites reject bot-like user agents. It is possible to use
# fake user agents in requests to these websites.
# It is recommended to default this to False and use on an as-needed basis.
#
# Default behaviours in modules that can utilize fake UAs.
# True for enabling fake UA, False for disabling / using pywikibot's own UA,
# str to specify custom UA.
fake_user_agent_default = {'reflinks': False, 'weblinkchecker': False}
# Website domains excepted to the default behaviour.
# True for enabling, False for disabling, str to hardcode a UA.
# Example: {'problematic.site.example': True,
#           'prefers.specific.ua.example': 'snakeoil/4.2'}
fake_user_agent_exceptions: Dict[str, Union[bool, str]] = {}

# The default interface for communicating with the site
# currently the only defined interface is 'APISite', so don't change this!
site_interface = 'APISite'
# number of days to cache namespaces, api configuration, etc.
API_config_expiry = 30

# The maximum number of bytes which uses a GET request, if not positive
# it'll always use POST requests
maximum_GET_length = 255
# Some networks modify GET requests when they are not encrypted, to avoid
# bug reports related to that disable those. If we are confident that bug
# related to this are really because of the network this could be changed.
enable_GET_without_SSL = False

# Solve captchas in the webbrowser. Setting this to False will result in the
# exception CaptchaError being thrown if a captcha is encountered.
solve_captcha = True

# Some sites will require password authentication to access the HTML
# pages at the site. If you have any such site, add lines to your user
# config file of the following form:
#
# authenticate['en.wikipedia.org'] = ('John','XXXXX')
# authenticate['*.wikipedia.org'] = ('John','XXXXX')
#
# where John is your login name, and XXXXX your password.
# Note:
# 1. This is only for sites that use authentication in the form that gives
#    you a popup for name and password when you try to access any data, NOT
#    for, for example, wiki usernames
# 2. You must use the hostname of the site, not its family/language pair.
#    Pywikibot supports wildcard (*) in the prefix of hostname and select the
#    best match authentication. So you can specify authentication not only for
#    one site
#
# Pywikibot also support OAuth 1.0a via mwoauth
# https://pypi.org/project/mwoauth
#
# You can add OAuth tokens to your user config file of this form:
#
# authenticate['en.wikipedia.org'] = ('consumer_key','consumer_secret',
#                                     'access_key', 'access_secret')
# authenticate['*.wikipedia.org'] = ('consumer_key','consumer_secret',
#                                    'access_key', 'access_secret')
#
# Note: the target wiki site must install OAuth extension
authenticate: Dict[str, Tuple[str, ...]] = {}

# By default you are asked for a password on the terminal.
# A password file may be used, e.g. password_file = '.passwd'
# The path to the password file is relative to that of the user_config file.
# The password file should consist of lines containing Python tuples of any
# of the following formats:
# (code, family, username, password)
# (family, username, password)
# (username, password)
# It's also possible (and safer) for bot users to use BotPasswords to limit
# the permissions given to a bot. When using BotPasswords, each instance gets
# keys. This combination can only access the API, not the normal web interface.
# See https://www.mediawiki.org/wiki/Manual:Pywikibot/BotPasswords to know how
# use them. In this case, the password file should contain a BotPassword object
# in the following format:
# (username, BotPassword(botname, botpassword))
password_file = None

# edit summary to use if not supplied by bot script
# WARNING: this should NEVER be used in practice, ALWAYS supply a more
#          relevant summary for bot edits
default_edit_summary = 'Pywikibot ' + pwb_version

# Edit summary prefix
# if a str, always use this as summary prefix e.g. 'Bot:' for all sites
# if True, always use a summary prefix from i18n
# if False, never use a summary prefix
# if None, the i18n summary prefix is used for botflag accounts only
# NOTE: this feature is not yet implemented for all scripts
bot_prefix_summary: Union[bool, str, None] = None

# What permissions to use to set private files to it
# such as password file.
#
# stat.S_IRWXU 0o700 mask for owner permissions
# stat.S_IRUSR 0o400 read permission for owner
# stat.S_IWUSR 0o200 write permission for owner
# stat.S_IXUSR 0o100 execute permission for owner
# stat.S_IRWXG 0o070 mask for group permissions
# stat.S_IRGRP 0o040 read permission for group
# stat.S_IWGRP 0o020 write permission for group
# stat.S_IXGRP 0o010 execute permission for group
# stat.S_IRWXO 0o007 mask for others permissions
# stat.S_IROTH 0o004 read permission for others
# stat.S_IWOTH 0o002 write permission for others
# stat.S_IXOTH 0o001 execute permission for others
private_files_permission = stat.S_IRUSR | stat.S_IWUSR
private_folder_permission = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR

# Allow user to stop warnings about file security
# by setting this to true.
ignore_file_security_warnings = False

# Custom headers to send on all requests.
# This is mainly intended to support setting the
# X-Wikimedia-Debug header, which is sometimes
# needed to debug issues with Wikimedia sites:
# https://wikitech.wikimedia.org/wiki/Debugging_in_production
#
# Note that these headers will be sent with all requests,
# not just MediaWiki API calls.
extra_headers: Mapping[str, str] = {}

# Set to True to override the {{bots}} exclusion protocol (at your own risk!)
ignore_bot_templates = False

# #############################################


def user_home_path(path: str) -> str:
    """Return a file path to a file in the user home."""
    return os.path.join(os.path.expanduser('~'), path)


def get_user_config_file() -> str:
    """Return user config file name.

    .. versionadded:: 7.7
    """
    for arg in sys.argv[1:]:
        opt, _, value = arg.partition(':')
        if opt == '-config':
            if not value.endswith('.py'):
                value += '.py'
            return value
    return 'user-config.py'


def get_base_dir(test_directory: Optional[str] = None,
                 config_file: str = 'user-config.py') -> str:
    r"""Return the directory in which user-specific information is stored.

    This is determined in the following order:
     1.  If the script was called with a `-dir:` argument, use the
         directory provided in this argument.
     2.  If the user has a `PYWIKIBOT_DIR` environment variable, use the
         value of it.
     3.  If `user-config` is present in current directory, use the
         current directory.
     4.  If `user-config` is present in `pwb.py` directory, use that
         directory
     5.  Use (and if necessary create) a `'pywikibot'` folder under
         `'Application Data'` or `'AppData\Roaming'` (Windows) or
         `'.pywikibot'` directory (Unix and similar) under the user's
         home directory.

    Set `PYWIKIBOT_NO_USER_CONFIG=1` to disable loading user config file
    (`user-config.py`) or install Pywikibot as a site-package.

    .. versionchanged:: 7.7
       Added the *config_file* parameter.

    :param test_directory: Assume that a user config file exists in this
        directory. Used to test whether placing a user config file in this
        directory will cause it to be selected as the base directory.
    :param config_file: filename of the user config file
    """
    def exists(directory: str) -> bool:
        directory = os.path.abspath(directory)
        if directory == test_directory:
            return True
        return os.path.exists(os.path.join(directory, config_file))

    if test_directory is not None:
        test_directory = os.path.abspath(test_directory)

    base_dir = ''
    for arg in sys.argv[1:]:
        if arg.startswith('-dir:'):
            base_dir = removeprefix(arg, '-dir:')
            base_dir = os.path.expanduser(base_dir)
            break
    else:
        if ('PYWIKIBOT_DIR' in environ
                and exists(os.path.abspath(environ['PYWIKIBOT_DIR']))):
            base_dir = os.path.abspath(environ['PYWIKIBOT_DIR'])
        elif exists('.'):
            base_dir = os.path.abspath('.')
        elif ('PYWIKIBOT_DIR_PWB' in environ
                and exists(os.path.abspath(environ['PYWIKIBOT_DIR_PWB']))):
            base_dir = os.path.abspath(environ['PYWIKIBOT_DIR_PWB'])
        else:
            base_dir_cand = []
            home = os.path.expanduser('~')
            if OSWIN32:
                win_version = int(platform.version().split('.')[0])
                if win_version == 5:
                    sub_dir = ['Application Data']
                elif win_version in (6, 10):
                    sub_dir = ['AppData', 'Roaming']
                else:
                    raise OSError('Windows version {} not supported yet.'
                                  .format(win_version))
                base_dir_cand.extend([[home] + sub_dir + ['Pywikibot'],
                                     [home] + sub_dir + ['pywikibot']])
            else:
                base_dir_cand.append([home, '.pywikibot'])

            for dir_ in base_dir_cand:
                dir_s = os.path.join(*dir_)
                try:
                    os.makedirs(dir_s, mode=private_folder_permission)
                except OSError:  # PermissionError or already exists
                    if exists(dir_s):
                        base_dir = dir_s
                        break

    if not os.path.isabs(base_dir):
        base_dir = os.path.normpath(os.path.join(os.getcwd(), base_dir))

    # make sure this path is valid and that it contains user-config file
    if not os.path.isdir(base_dir):
        raise RuntimeError(f"Directory '{base_dir}' does not exist.")

    # check if config_file is in base_dir
    if not exists(base_dir):
        exc_text = f'No {config_file} found in directory {base_dir!r}.\n'

        if __no_user_config is None:
            assert get_base_dir.__doc__ is not None
            exc_text += (
                '\nPlease check that {0} is stored in the correct location.'
                '\nDirectory where {0} is searched is determined as follows:'
                '\n\n    '.format(config_file)
            ) + get_base_dir.__doc__
            raise RuntimeError(exc_text)

        if __no_user_config != '2':
            output(exc_text)

    return base_dir


user_config_file = get_user_config_file()

# Save base_dir for use by other modules
base_dir = get_base_dir(config_file=user_config_file)

for arg in sys.argv[1:]:
    if arg.startswith('-verbose') or arg == '-v':
        output('The base directory is ' + base_dir)
        output('The user config file is ' + user_config_file)
        break
family_files = {}


@deprecated('family_files[family_name] = file_path', since='6.0.0')
def register_family_file(family_name: str, file_path: str) -> None:
    """Register a single family class file.

    Parameter file_path may be a path or an url.
    family.AutoFamily function is used when the url is given.
    """
    family_files[family_name] = file_path


def register_families_folder(folder_path: str,
                             not_exists_ok: bool = False) -> None:
    """Register all family class files contained in a directory.

    .. versionadded:: 7.0
       The *not_exists_ok* parameter

    :param folder_path: The path of a folder containing family files.
        The families may also be inside a zip archive structure.
    :param not_exists_ok: When true, ignore FileNotFoundError
    :raises FileNotFoundError: Family folder does not exist
    :raises NotADirectoryError: folder_path is not a directory
    """
    suffix = '_family.py'

    if not os.path.exists(folder_path):
        if not_exists_ok:
            return
        raise FileNotFoundError('Family folder {!r} does not exist'
                                .format(folder_path))

    if os.path.isdir(folder_path):
        for file_name in os.listdir(folder_path):
            if file_name.endswith(suffix):
                family_name = removesuffix(file_name, suffix)
                family_files[family_name] = os.path.join(folder_path,
                                                         file_name)
        return

    # probably there is a zip file chain (T278076)
    # find the parent zip folder
    path = Path(folder_path)
    if not is_zipfile(path):
        for parent in path.parents:
            if is_zipfile(path):
                path = parent
                break
        else:
            raise NotADirectoryError('20', 'Not a directory', folder_path)

    # read the family files from zip folder
    # assume that all files ending with suffix reside in family folder
    zip_file = ZipFile(path)
    for file_name in zip_file.namelist():
        if file_name.endswith(suffix):
            file_path = Path(file_name)
            family_name = removesuffix(file_path.name, suffix)
            family_files[family_name] = os.path.join(folder_path,
                                                     file_path.name)


# Get the names of all known families, and initialize with empty dictionaries.
# ‘families/’ is a subdirectory of the directory in which config.py is found.
register_families_folder(os.path.join(os.path.dirname(__file__), 'families'))
# ‘families/’ can also be stored in the base directory
register_families_folder(os.path.join(base_dir, 'families'),
                         not_exists_ok=True)


# ############# USER INTERFACE SETTINGS ##############

# The encoding that's used in the user's console, i.e. how strings are encoded
# when they are read by raw_input(). On Windows systems' DOS box, this should
# be 'cp850' ('cp437' for older versions). Linux users might try 'iso-8859-1'
# or 'utf-8'.
# This default code should work fine, so you don't have to think about it.
# When using pywikibot inside a daemonized twisted application, we get
# "StdioOnnaStick instance has no attribute 'encoding'"; assign None instead.
# TODO: consider getting rid of this config variable.
console_encoding = getattr(sys.stdout, 'encoding', None)

# The encoding the user would like to see text transliterated to. This can be
# set to a charset (e.g. 'ascii', 'iso-8859-1' or 'cp850'), and we will output
# only characters that exist in that charset. However, the characters will be
# output using console_encoding.
# If this is not defined on Windows, we emit a Warning explaining the user
# to either switch to a Unicode-able font and use
#    transliteration_target = None
# or to keep using raster fonts and set
#    transliteration_target = console_encoding
# After emitting the warning, this last option will be set.

transliteration_target = None

# The encoding in which textfiles are stored, which contain lists of page
# titles. The most used is 'utf-8'; 'utf-8-sig' recognizes BOM.
# For a complete list please see:
# https://docs.python.org/3/library/codecs.html#standard-encodings
textfile_encoding = 'utf-8'

# currently terminal and buffer are the only supported userinterfaces
userinterface = 'terminal'

# this can be used to pass variables to the UI init function
# useful for e.g.
# userinterface_init_kwargs = {'default_stream': 'stdout'}
userinterface_init_kwargs: Dict[str, str] = {}

# i18n setting for user interface language
# default is obtained from locale.getlocale
userinterface_lang = None

# Should we transliterate characters that do not exist in the console
# character set?
# True: whenever possible
# False: never - always replace them by question marks
# Currently only works if interface 'terminal' is set.
transliterate = True

# The pwb.py wrapper calls the script given as parameter in this way
# python pwb.py <name_of_script> <options>
# If there is a misspelling in <name_of_script> the most similar script
# scripts are displayed or if only one is found, it will be started.
# There are some configuration values to change the behavior
#
# pwb_close_matches: the maximum number of simular scripts to be found
pwb_close_matches = 10  # must be greater than 0
# pwb_cut_off: similarity of scripts to be found
pwb_cut_off = 0.7  # must be a float in the range [0, 1]
# pwb_autostart_waittime: wait time until the most similar script starts
pwb_autostart_waittime = 5.0

# Should the system bell ring if the bot expects user input?
ring_bell = False

# Colorization can be used to markup important text parts of the output.
# On Linux/Unix terminals, ANSI escape codes are used for this. On Windows,
# it is done by a DLL call via ctypes.
# Set this to False if you're using Linux and your tty doesn't support
# ANSI colors.
try:
    # Don't print colorized when the output is, for example, piped to a file.
    colorized_output = sys.stdout.isatty()
except AttributeError:
    # When using pywikibot inside a daemonized twisted application,
    # we get "StdioOnnaStick instance has no attribute 'isatty'"
    colorized_output = False

# An indication of the size of your screen, or rather the size of the screen
# to be shown, for flickrripper
tkhorsize = 1280
tkvertsize = 800

# ############# EXTERNAL EDITOR SETTINGS ##############
# The command for the editor you want to use. If set to True, Tkinter
# editor will be used. If set to False, no editor will be used. In
# script tests to be a noop (like /bin/true) so the script continues.
# If set to None, the EDITOR environment variable will be used as
# command. If EDITOR is not set, on windows plattforms it tries to
# determine the default text editor from registry. Finally, Tkinter is
# used as fallback.
editor: Union[bool, str, None] = None

# Warning: DO NOT use an editor which doesn't support Unicode to edit pages!
# You will BREAK non-ASCII symbols!
editor_encoding = 'utf-8'

# The temporary file name extension can be set in order to use syntax
# highlighting in your text editor.
editor_filename_extension = 'wiki'

# ############# LOGFILE SETTINGS ##############

# Defines for which scripts a logfile should be enabled. Logfiles will be
# saved in the 'logs' subdirectory.
#
# Example:
#     log = ['redirect', 'replace', 'weblinkchecker']
# It is also possible to enable logging for all scripts, using this line:
#     log = ['*']
# To disable all logging, use this:
#     log = []
# Per default, no logging is enabled.
# This setting can be overridden by the -log or -nolog command-line arguments.
log: List[str] = []
# filename defaults to modulename-bot.log
logfilename: Optional[str] = None
# maximal size of a logfile in kilobytes. If the size reached that limit the
# logfile will be renamed (if logfilecount is not 0) and the old file is filled
# again. logfilesize must be an integer value
logfilesize = 1024
# Number of rotating logfiles are created. The older files get the higher
# number. If logfilecount is 0, no logfile will be archived but the current
# logfile will be overwritten if the file size reached the logfilesize above.
# If logfilecount is -1 there are no rotating logfiles but the files where
# renamed if the logfile is full. The newest file gets the highest number until
# some logfiles where deleted.
logfilecount = 5
# set to 1 (or higher) to generate "informative" messages to terminal
verbose_output = 0
# set to True to fetch the pywiki version online
log_pywiki_repo_version = False
# if True, include a lot of debugging info in logfile
# (overrides log setting above)
debug_log: List[str] = []

# ############# EXTERNAL SCRIPT PATH SETTINGS ##############
# Set your own script path to lookup for your script files.
#
# Your private script path is relative to your base directory.
# Subfolders must be delimited by '.'. every folder must contain
# an (empty) __init__.py file.
#
# The search order is
# 1. user_script_paths in the given order
# 2. scripts/userscripts
# 3. scripts
# 4. scripts/maintenance
# 5. pywikibot/scripts
#
# 2. - 4. are available in directory mode only
#
# sample:
# user_script_paths = ['scripts.myscripts']
user_script_paths: List[str] = []

# ############# EXTERNAL FAMILIES SETTINGS ##############
# Set your own family path to lookup for your family files.
#
# Your private family path may be either an absolute or a relative path.
# You may have multiple paths defined in user_families_paths list.
#
# You may also define various family files stored directly in
# family_files dict. Use the family name as dict key and the path or an
# url as value.
#
# samples:
# family_files['mywiki'] = 'https://de.wikipedia.org'
# user_families_paths = ['data/families']
user_families_paths: List[str] = []

# ############# INTERWIKI SETTINGS ##############

# Should interwiki.py report warnings for missing links between foreign
# languages?
interwiki_backlink = True

# Should interwiki.py display every new link it discovers?
interwiki_shownew = True

# Should interwiki.py output a graph PNG file on conflicts?
# You need pydot for this:
# https://pypi.org/project/pydot/
interwiki_graph = False

# Specifies that the robot should process that amount of subjects at a time,
# only starting to load new pages in the original language when the total
# falls below that number. Default is to process (at least) 100 subjects at
# once.
interwiki_min_subjects = 100

# If interwiki graphs are enabled, which format(s) should be used?
# Supported formats include png, jpg, ps, and svg. See:
# https://graphviz.org/docs/outputs/
# If you want to also dump the dot files, you can use this in your
# user config file:
# interwiki_graph_formats = ['dot', 'png']
# If you need a PNG image with an HTML image map, use this:
# interwiki_graph_formats = ['png', 'cmap']
# If you only need SVG images, use:
# interwiki_graph_formats = ['svg']
interwiki_graph_formats = ['png']

# You can post the contents of your autonomous_problems.dat to the wiki,
# e.g. to https://de.wikipedia.org/wiki/Wikipedia:Interwiki-Konflikte .
# This allows others to assist you in resolving interwiki problems.
# To help these people, you can upload the interwiki graphs to your
# webspace somewhere. Set the base URL here, e.g.:
# 'https://www.example.org/~yourname/interwiki-graphs/'
interwiki_graph_url = None

# Save file with local articles without interwikis.
without_interwiki = False

# ############# SOLVE_DISAMBIGUATION SETTINGS ############
#
# Set disambiguation_comment[FAMILY][LANG] to a non-empty string to override
# the default edit comment for the solve_disambiguation bot.
#
# Use %s to represent the name of the disambiguation page being treated.
# Example:
#
# disambiguation_comment['wikipedia']['en'] = \
#    'Robot-assisted disambiguation ([[WP:DPL|you can help!]]): %s'

# Sorting order for alternatives. Set to True to ignore case for sorting order.
sort_ignore_case = False

# ############# IMAGE RELATED SETTINGS ##############
# If you set this to True, images will be uploaded to Wikimedia
# Commons by default.
upload_to_commons = False

# ############# SETTINGS TO AVOID SERVER OVERLOAD ##############

# Slow down the robot such that it never requests a second page within
# 'minthrottle' seconds. This can be lengthened if the server is slow,
# but never more than 'maxthrottle' seconds. However - if you are running
# more than one bot in parallel the times are lengthened.
#
# 'maxlag' is used to control the rate of server access (see below).
# Set minthrottle to non-zero to use a throttle on read access.
minthrottle = 0
maxthrottle = 60

# Slow down the robot such that it never makes a second page edit within
# 'put_throttle' seconds.
put_throttle: Union[int, float] = 10

# Sometimes you want to know when a delay is inserted. If a delay is larger
# than 'noisysleep' seconds, it is logged on the screen.
noisysleep = 3.0

# Defer bot edits during periods of database server lag. For details, see
# https://www.mediawiki.org/wiki/Manual:Maxlag_parameter
# You can set this variable to a number of seconds, or to None (or 0) to
# disable this behavior. Higher values are more aggressive in seeking
# access to the wiki.
# Non-Wikimedia wikis may or may not support this feature; for families
# that do not use it, it is recommended to set minthrottle (above) to
# at least 1 second.
maxlag = 5

# Maximum of pages which can be retrieved at one time from wiki server.
# -1 indicates limit by api restriction
step = -1

# Maximum number of times to retry an API request before quitting.
max_retries = 15
# Minimum time to wait before resubmitting a failed API request.
retry_wait = 5
# Maximum time to wait before resubmitting a failed API request.
retry_max = 120

# ############# WEBLINK CHECKER SETTINGS ##############

# How many external links should weblinkchecker.py check at the same time?
# If you have a fast connection, you might want to increase this number so
# that slow servers won't slow you down.
max_external_links = 50

report_dead_links_on_talk = False

# Don't alert on links days_dead old or younger
weblink_dead_days = 7

# ############# DATABASE SETTINGS ##############
# Setting to connect the database or replica of the database of the wiki.
# db_name_format can be used to manipulate the dbName of site.
#
# Example for a pywikibot running on Wikimedia Cloud (Toolforge):
# db_hostname_format = '{0}.analytics.db.svc.wikimedia.cloud'
# db_name_format = '{0}_p'
# db_connect_file = user_home_path('replica.my.cnf')
db_hostname_format = 'localhost'
db_username = ''
db_password = ''
db_name_format = '{0}'
db_connect_file = user_home_path('.my.cnf')
# local port for mysql server
# ssh -L 4711:enwiki.analytics.db.svc.eqiad.wmflabs:3306 \
#     user@login.toolforge.org
db_port = 3306

# ############# HTTP SETTINGS ##############
# Default socket timeout in seconds.
# DO NOT set to None to disable timeouts. Otherwise this may freeze your
# script.
# You may assign either a tuple of two int or float values for connection and
# read timeout, or a single value for both in a tuple.
socket_timeout = (6.05, 45)


# ############# COSMETIC CHANGES SETTINGS ##############
# The bot can make some additional changes to each page it edits, e.g. fix
# whitespace or positioning of category links.

# This is an experimental feature; handle with care and consider re-checking
# each bot edit if enabling this!
cosmetic_changes = False

# If cosmetic changes are switched on, and you also have several accounts at
# projects where you're not familiar with the local conventions, you probably
# only want the bot to do cosmetic changes on your "home" wiki which you
# specified in config.mylang and config.family.
# If you want the bot to also do cosmetic changes when editing a page on a
# foreign wiki, set cosmetic_changes_mylang_only to False, but be careful!
cosmetic_changes_mylang_only = True

# The dictionary cosmetic_changes_enable should contain a tuple of languages
# for each site where you wish to enable in addition to your own langlanguage
# (if cosmetic_changes_mylang_only is set)
# Please set your dictionary by adding such lines to your user config file:
# cosmetic_changes_enable['wikipedia'] = ('de', 'en', 'fr')
cosmetic_changes_enable: Dict[str, Tuple[str, ...]] = {}

# The dictionary cosmetic_changes_disable should contain a tuple of languages
# for each site where you wish to disable cosmetic changes. You may use it with
# cosmetic_changes_mylang_only is False, but you can also disable your own
# language. This also overrides the settings in the cosmetic_changes_enable
# dictionary. Please set your dict by adding such lines to your user config:
# cosmetic_changes_disable['wikipedia'] = ('de', 'en', 'fr')
cosmetic_changes_disable: Dict[str, Tuple[str, ...]] = {}

# cosmetic_changes_deny_script is a list of scripts for which cosmetic changes
# are disabled. You may add additional scripts by appending script names in
# your user config file ("+=" operator is strictly recommended):
# cosmetic_changes_deny_script += ['your_script_name_1', 'your_script_name_2']
# Appending the script name also works:
# cosmetic_changes_deny_script.append('your_script_name')
cosmetic_changes_deny_script = ['category_redirect', 'cosmetic_changes',
                                'newitem', 'touch']

# ############# REPLICATION BOT SETTINGS ################
# You can add replicate_replace to your user config file.
#
# Use has the following format:
#
# replicate_replace = {
#            'wikipedia:li': {'Hoofdpagina': 'Veurblaad'}
# }
#
# to replace all occurrences of 'Hoofdpagina' with 'Veurblaad' when writing to
# liwiki. Note that this does not take the origin wiki into account.
replicate_replace: Dict[str, Dict[str, str]] = {}

# ############# FURTHER SETTINGS ##############

# Simulate settings

# Defines what additional actions the bots are NOT allowed to do (e.g. 'edit')
# on the wiki server. Allows simulation runs of bots to be carried out without
# changing any page on the server side. Use this setting to add more actions
# into user config file for wikis with extra write actions.
actions_to_block: List[str] = []

# Set simulate to True or use -simulate option to block all actions given
# above.
simulate: Union[bool, str] = False

# How many pages should be put to a queue in asynchronous mode.
# If maxsize is <= 0, the queue size is infinite.
# Increasing this value will increase memory space but could speed up
# processing. As higher this value this effect will decrease.
max_queue_size = 64

# Pickle protocol version to use for storing dumps.
# This config variable is not used for loading dumps.
# Version 0 is a more or less human-readable protocol
# Version 2 is common to both Python 2 and 3, and should
# be used when dumps are accessed by both versions.
# Version 3 is only available for Python 3
# Version 4 is only available for Python 3.4+
# Version 5 was added with Python 3.8
pickle_protocol = 2

# ============================
# End of configuration section
# ============================

# #############################################


def makepath(path: str, create: bool = True) -> str:
    """Return a normalized absolute version of the path argument.

    If the given path already exists in the filesystem or create is False
    the filesystem is not modified.
    Otherwise if create is True makepath creates directories along the given
    path using the dirname() of the path. You may append a '/' to the path if
    you want it to be a directory path.

    from holger@trillke.net 2002/03/18

    :param path: path in the filesystem
    :param create: create the directory if it is True. Otherwise do not change
        the filesystem. Default is True.
    """
    dpath = os.path.normpath(os.path.dirname(path))
    if create and not os.path.exists(dpath):
        os.makedirs(dpath)
    return os.path.normpath(os.path.abspath(path))


def datafilepath(*filename: str, create: bool = True) -> str:
    """Return an absolute path to a data file in a standard location.

    Argument(s) are zero or more directory names, optionally followed by a
    data file name. The return path is offset to config.base_dir. Any
    directories in the path that do not already exist are created if create
    is True, otherwise the filesystem keeps unchanged.

    :param filename: path in the filesystem
    :param create: create the directory if it is True. Otherwise don't change
        the filesystem. Default is True.
    """
    return makepath(os.path.join(base_dir, *filename), create=create)


def shortpath(path: str) -> str:
    """Return a file path relative to config.base_dir."""
    if path.startswith(base_dir):
        return path[len(base_dir) + len(os.path.sep):]
    return path


# System-level and User-level changes.
# Store current variables and their types.
_public_globals = {
    _key: _val for _key, _val in globals().items()
    if _key[0] != '_' and _key not in _imports}

# Create an environment for user-config.py which is
# a deep copy of the core config settings, so that
# we can detect modified config items easily.
_exec_globals = copy.deepcopy(_public_globals)

# Always try to get the user files
_filename = os.path.join(base_dir, user_config_file)
if os.path.exists(_filename):
    _filestatus = os.stat(_filename)
    _filemode = _filestatus[0]
    _fileuid = _filestatus[4]
    if not OSWIN32 and _fileuid not in [os.getuid(), 0]:
        warning(f'Skipped {_filename!r}: owned by someone else.')
    elif OSWIN32 or _filemode & 0o02 == 0:
        with open(_filename, 'rb') as f:
            exec(compile(f.read(), _filename, 'exec'), _exec_globals)
    else:
        warning(f'Skipped {_filename!r}: writeable by others.')
elif __no_user_config and __no_user_config != '2':
    warning(f'{user_config_file} cannot be loaded.')


class _DifferentTypeError(UserWarning, TypeError):

    """An error when the required type doesn't match the actual type."""

    def __init__(
        self,
        name: str,
        actual_type: type,
        allowed_types: Tuple[type, ...],
    ) -> None:
        super().__init__(
            'Configuration variable "{}" is defined as "{}" in '
            'your {} but expected "{}".'
            .format(name, actual_type.__name__, user_config_file,
                    '", "'.join(t.__name__ for t in allowed_types)))


def _assert_default_type(
    name: str,
    value: _ValueType,
    default_value: object,
) -> Union[_ValueType, float, None]:
    """Return the value if the old or new is None or both same type."""
    if (value is None or default_value is None
            or isinstance(value, type(default_value))):
        return value
    if isinstance(value, int) and isinstance(default_value, float):
        return float(value)
    raise _DifferentTypeError(name, type(value), (type(default_value),))


def _assert_types(
    name: str,
    value: _ValueType,
    types: Tuple[type, ...],
) -> _ValueType:
    """Return the value if it's one of the types."""
    if isinstance(value, types):
        return value
    raise _DifferentTypeError(name, type(value), types)


DEPRECATED_VARIABLE = (
    '"{{}}" present in our {} is no longer a supported configuration variable '
    'and should be removed. Please inform the maintainers if you depend on it.'
    .format(user_config_file))


def _check_user_config_types(
    user_config: Dict[str, object],
    default_values: Dict[str, object],
    skipped: FrozenSet[str],
) -> None:
    """Check the types compared to the default values."""
    for name, value in user_config.items():
        if name in default_values:
            try:
                if name == 'socket_timeout':
                    value = _assert_types(name, value, (int, float, tuple))
                else:
                    value = _assert_default_type(name, value,
                                                 default_values[name])
            except _DifferentTypeError as e:
                warn(e)
            else:
                user_config[name] = value
        elif not name.startswith('_') and name not in skipped:
            if name in _deprecated_variables:
                warn('\n' + fill(DEPRECATED_VARIABLE.format(name)),
                     _ConfigurationDeprecationWarning)
            elif name not in _future_variables:
                warn('\n' + fill('Configuration variable "{}" is defined in '
                                 'your {} but unknown. It can be a misspelled '
                                 'one or a variable that is no longer '
                                 'supported.'.format(name, user_config_file)),
                     UserWarning)


_check_user_config_types(_exec_globals, _public_globals, _imports)

# Copy the user config settings into globals
_modified = {_key for _key in _public_globals
             if _exec_globals[_key] != globals()[_key]}

if 'user_agent_format' in _modified:
    _right_user_agent_format = re.sub(r'{httplib2(:|})', r'{http_backend\1',
                                      _exec_globals['user_agent_format'])
    if _right_user_agent_format != _exec_globals['user_agent_format']:
        warn('`{httplib2}` in user_agent_format is deprecated, '
             'will replace `{httplib2}` with `{http_backend}`',
             _ConfigurationDeprecationWarning)
        _exec_globals['user_agent_format'] = _right_user_agent_format
    del _right_user_agent_format

for _key in _modified:
    globals()[_key] = _exec_globals[_key]

    if _key in _deprecated_variables:
        warn(DEPRECATED_VARIABLE.format(_key),
             _ConfigurationDeprecationWarning)

# If we cannot auto-detect the console encoding (e.g. when piping data)
# assume utf-8. On Linux, this will typically be correct; on Windows,
# this can be an issue when piping through more. However, the behavior
# when redirecting to a file utf-8 is more reasonable.

if console_encoding is None:
    console_encoding = 'utf-8'

if userinterface_lang is None:
    userinterface_lang = os.getenv('PYWIKIBOT_USERINTERFACE_LANG') \
        or getlocale()[0]
    if userinterface_lang is None or userinterface_lang == 'C':
        userinterface_lang = 'en'
    else:
        userinterface_lang = userinterface_lang.split('_')[0]

# Fix up default site
if family == 'wikipedia' and mylang == 'language':
    if __no_user_config != '2':
        warning('family and mylang are not set.\n'
                "Defaulting to family='wikipedia' and mylang='test'.")
    mylang = 'test'

# SECURITY WARNINGS
if not ignore_file_security_warnings:
    for _permission in ('private_files_permission',
                        'private_folder_permission'):
        if locals()[_permission] & (stat.S_IRWXG | stat.S_IRWXO) != 0:
            error('\n' + fill(
                f'CRITICAL SECURITY WARNING: {_permission!r} is set to allow'
                ' access from the group/others which could give them access'
                ' to the sensitive files. To avoid giving others access to'
                " sensitive files, pywikibot won't run with this setting."
                ' Choose a more restrictive permission or set'
                " 'ignore_file_security_warnings' to true."))
            sys.exit(1)

# Setup custom family files
for file_path in user_families_paths:
    register_families_folder(file_path)
#
# When called as main program, list all configuration variables
#
if __name__ == '__main__':  # pragma: no cover
    from pprint import PrettyPrinter as _PrettyPrinter
    _pp = _PrettyPrinter()
    _all = True
    for _arg in sys.argv[1:]:
        if _arg == 'modified':
            _all = False
        else:
            warning(f'Unknown arg {_arg} ignored')

    for _name in sorted(globals()):
        if _name[0] != '_' \
           and type(globals()[_name]) not in [types.FunctionType,
                                              types.ModuleType] \
           and (_all or _name in _modified):
            _value = globals()[_name]

            if _name not in _private_values or not _value:
                _value = _pp.pformat(_value)
            elif isinstance(_value, dict):
                _value = '{ ...xxxxxxxx... }'
            elif hasattr(_value, '__dict__'):
                _value = (_value.__class__.__name__
                          + '( ...xxxxxxxx... )')
            else:
                _value = repr('xxxxxxxx')
            output(f'{_name}={_value}')

# cleanup all locally-defined variables
for __var in list(globals()):
    if __var.startswith('_') and not __var.startswith('__'):
        del sys.modules[__name__].__dict__[__var]

del __var
