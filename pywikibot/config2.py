# -*- coding: utf-8 -*-
"""
Module to define and load pywikibot configuration default and user preferences.

User preferences are loaded from a python file called user-config.py, which
may be located in directory specified by the environment variable
PYWIKIBOT_DIR, or the same directory as pwb.py, or in a directory within
the users home. See get_base_dir for more information.

If user-config.py can not be found in any of those locations, this module
will fail to load unless the environment variable PYWIKIBOT_NO_USER_CONFIG
is set to a value other than '0'. i.e. PYWIKIBOT_NO_USER_CONFIG=1 will
allow config to load without a user-config.py. However, warnings will be
shown if user-config.py was not loaded.
To prevent these warnings, set PYWIKIBOT_NO_USER_CONFIG=2.

Provides two functions to register family classes which can be used in
the user-config:

 - register_family_file
 - register_families_folder

Other functions made available to user-config:

 - user_home_path

Sets module global base_dir and provides utility methods to
build paths relative to base_dir:

 - makepath
 - datafilepath
 - shortpath
"""
#
# (C) Pywikibot team, 2003-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import collections
import copy
import os
import platform
import re
import stat
import sys
import types

from distutils.version import StrictVersion
from locale import getdefaultlocale
from os import getenv, environ
from textwrap import fill
from warnings import warn

from requests import __version__ as requests_version

from pywikibot.logging import error, output, warning
from pywikibot.tools import PY2, issue_deprecation_warning

OSWIN32 = (sys.platform == 'win32')

if OSWIN32:
    if not PY2:
        import winreg
    else:
        import _winreg as winreg


# Normalize old PYWIKIBOT2 environment variables and issue a deprecation warn.
for env_name in (
    'PYWIKIBOT2_DIR', 'PYWIKIBOT2_DIR_PWB', 'PYWIKIBOT2_NO_USER_CONFIG',
):
    if env_name not in environ:
        continue
    env_value = environ[env_name]
    new_env_name = env_name.replace('PYWIKIBOT2_', 'PYWIKIBOT_')
    del environ[env_name]
    if new_env_name not in environ:
        environ[new_env_name] = env_value
    issue_deprecation_warning(
        env_name + ' environment variable', new_env_name, 0, since='20180803')


# This frozen set should contain all imported modules/variables, so it must
# occur directly after the imports. At that point globals() only contains the
# names and some magic variables (like __name__)
_imports = frozenset(name for name in globals() if not name.startswith('_'))

__no_user_config = getenv('PYWIKIBOT_NO_USER_CONFIG')
if __no_user_config == '0':
    __no_user_config = None


class _ConfigurationDeprecationWarning(UserWarning):

    """Feature that is no longer supported."""

    pass


# IMPORTANT:
# Do not change any of the variables in this file. Instead, make
# a file user-config.py, and overwrite values in there.

# Note: all variables defined in this module are made available to bots as
# configuration settings, *except* variable names beginning with an
# underscore (example: _variable). Be sure to use an underscore on any
# variables that are intended only for internal use and not to be exported
# to other modules.

_private_values = {'authenticate', 'db_password'}
_deprecated_variables = {'available_ssl_project', 'fake_user_agent',
                         'interwiki_contents_on_disk', 'line_separator', 'LS',
                         'panoramio', 'proxy', 'special_page_limit',
                         'sysopnames', 'use_SSL_onlogin', 'use_SSL_always'}

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
# user-config.py:
#
# usernames['wikipedia']['de'] = 'myGermanUsername'
# usernames['wiktionary']['en'] = 'myEnglishUsername'
#
# If you have a unique username for all languages of a family,
# you can use '*'
# usernames['wikibooks']['*'] = 'mySingleUsername'
# You may use '*' for family name in a similar manner.
#
usernames = collections.defaultdict(dict)
disambiguation_comment = collections.defaultdict(dict)

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
fake_user_agent_exceptions = {}
# This following option is deprecated in favour of finer control options above.
fake_user_agent = False

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

# Some sites will require password authentication to access the HTML pages at
# the site. If you have any such site, add lines to your user-config.py of
# the following form:
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
# You can add OAuth tokens to your user-config.py of the following form:
#
# authenticate['en.wikipedia.org'] = ('consumer_key','consumer_secret',
#                                     'access_key', 'access_secret')
# authenticate['*.wikipedia.org'] = ('consumer_key','consumer_secret',
#                                    'access_key', 'access_secret')
#
# Note: the target wiki site must install OAuth extension
authenticate = {}

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
default_edit_summary = 'Pywikibot 3.0-dev'

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
extra_headers = {}


def user_home_path(path):
    """Return a file path to a file in the user home."""
    return os.path.join(os.path.expanduser('~'), path)


def get_base_dir(test_directory=None):
    r"""Return the directory in which user-specific information is stored.

    This is determined in the following order:
     1.  If the script was called with a -dir: argument, use the directory
         provided in this argument.
     2.  If the user has a PYWIKIBOT_DIR environment variable, use the value
         of it.
     3.  If user-config is present in current directory, use the current
         directory.
     4.  If user-config is present in pwb.py directory, use that directory
     5.  Use (and if necessary create) a 'pywikibot' folder under
         'Application Data' or 'AppData\Roaming' (Windows) or
         '.pywikibot' directory (Unix and similar) under the user's home
         directory.

    Set PYWIKIBOT_NO_USER_CONFIG=1 to disable loading user-config.py

    @param test_directory: Assume that a user config file exists in this
        directory. Used to test whether placing a user config file in this
        directory will cause it to be selected as the base directory.
    @type test_directory: str or None
    @rtype: str
    """
    def exists(directory):
        directory = os.path.abspath(directory)
        if directory == test_directory:
            return True
        else:
            return os.path.exists(os.path.join(directory, 'user-config.py'))

    if test_directory is not None:
        test_directory = os.path.abspath(test_directory)

    base_dir = ''
    for arg in sys.argv[1:]:
        if arg.startswith(str('-dir:')):
            base_dir = arg[5:]
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
                    raise WindowsError('Windows version {} not supported yet.'
                                       .format(win_version))
                base_dir_cand.extend([[home] + sub_dir + ['Pywikibot'],
                                     [home] + sub_dir + ['pywikibot']])
            else:
                base_dir_cand.append([home, '.pywikibot'])

            for dir in base_dir_cand:
                dir = os.path.join(*dir)
                try:
                    os.makedirs(dir, mode=private_files_permission)
                except OSError:  # PermissionError or already exists
                    if exists(dir):
                        base_dir = dir
                        break

    if not os.path.isabs(base_dir):
        base_dir = os.path.normpath(os.path.join(os.getcwd(), base_dir))
    # make sure this path is valid and that it contains user-config file
    if not os.path.isdir(base_dir):
        raise RuntimeError("Directory '%s' does not exist." % base_dir)
    # check if user-config.py is in base_dir
    if not exists(base_dir):
        exc_text = "No user-config.py found in directory '%s'.\n" % base_dir
        if __no_user_config:
            if __no_user_config != '2':
                output(exc_text)
        else:
            exc_text += (
                '  Please check that user-config.py is stored in the correct '
                'location.\n'
                '  Directory where user-config.py is searched is determined '
                'as follows:\n\n    ') + get_base_dir.__doc__
            raise RuntimeError(exc_text)

    return base_dir


# Save base_dir for use by other modules
base_dir = get_base_dir()

for arg in sys.argv[1:]:
    if arg.startswith(str('-verbose')) or arg == str('-v'):
        output('The base directory is ' + base_dir)
        break
family_files = {}


def register_family_file(family_name, file_path):
    """Register a single family class file.

    Parameter file_path may be a path or an url.
    family.AutoFamily function is used when the url is given.
    """
    usernames[family_name] = {}
    disambiguation_comment[family_name] = {}
    family_files[family_name] = file_path


def register_families_folder(folder_path):
    """Register all family class files contained in a directory."""
    for file_name in os.listdir(folder_path):
        if file_name.endswith('_family.py'):
            family_name = file_name[:-len('_family.py')]
            register_family_file(family_name, os.path.join(folder_path,
                                                           file_name))


# Get the names of all known families, and initialize with empty dictionaries.
# ‘families/’ is a subdirectory of the directory in which config2.py is found.
register_families_folder(os.path.join(os.path.dirname(__file__), 'families'))

# Set to True to override the {{bots}} exclusion protocol (at your own risk!)
ignore_bot_templates = False

# ############# USER INTERFACE SETTINGS ##############

# The encoding that's used in the user's console, i.e. how strings are encoded
# when they are read by raw_input(). On Windows systems' DOS box, this should
# be 'cp850' ('cp437' for older versions). Linux users might try 'iso-8859-1'
# or 'utf-8'.
# This default code should work fine, so you don't have to think about it.
# TODO: consider getting rid of this config variable.
try:
    if not PY2 or not sys.stdout.encoding:
        console_encoding = sys.stdout.encoding
    else:
        console_encoding = sys.stdout.encoding.decode('ascii')
except AttributeError:
    # When using pywikibot inside a daemonized twisted application,
    # we get "StdioOnnaStick instance has no attribute 'encoding'"
    console_encoding = None

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

# currently terminal is the only userinterface supported
userinterface = 'terminal'

# this can be used to pass variables to the UI init function
# useful for e.g.
# userinterface_init_kwargs = {'default_stream': 'stdout'}
userinterface_init_kwargs = {}

# i18n setting for user interface language
# default is obtained from L{locale.getdefaultlocale}
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
tkhorsize = 1600
tkvertsize = 1000

# ############# EXTERNAL EDITOR SETTINGS ##############
# The command for the editor you want to use. If set to None, a simple Tkinter
# editor will be used.
editor = os.environ.get('EDITOR', None)

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
#     log = ['interwiki', 'weblinkchecker', 'table2wiki']
# It is also possible to enable logging for all scripts, using this line:
#     log = ['*']
# To disable all logging, use this:
#     log = []
# Per default, logging of interwiki.py is enabled because its logfiles can
# be used to generate so-called warnfiles.
# This setting can be overridden by the -log or -nolog command-line arguments.
log = ['interwiki']
# filename defaults to modulename-bot.log
logfilename = None
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
debug_log = []

# ############# EXTERNAL SCRIPT PATH SETTINGS ##############
# Set your own script path to lookup for your script files.
#
# Your private script path must be located inside the
# framework folder, subfolders must be delimited by '.'.
# every folder must contain an (empty) __init__.py file.
#
# The search order is
# 1. user_script_paths in the given order
# 2. scripts/userscripts
# 3. scripts
# 4. scripts/maintenance
#
# sample:
# user_script_paths = ['scripts.myscripts']
user_script_paths = []

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
# http://www.graphviz.org/doc/info/output.html
# If you want to also dump the dot files, you can use this in your
# user-config.py:
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
put_throttle = 10

# Sometimes you want to know when a delay is inserted. If a delay is larger
# than 'noisysleep' seconds, it is logged on the screen.
noisysleep = 3.0

# Defer bot edits during periods of database server lag. For details, see
# https://www.mediawiki.org/wiki/Maxlag_parameter
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

# ############# TABLE CONVERSION BOT SETTINGS ##############

# Will split long paragraphs for better reading the source.
# Only table2wiki.py use it by now.
splitLongParagraphs = False
# sometimes HTML-tables are indented for better reading.
# That can do very ugly results.
deIndentTables = True

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
# Example for a pywikibot running on wmflabs:
# db_hostname = 'enwiki.analytics.db.svc.eqiad.wmflabs'
# db_name_format = '{0}_p'
# db_connect_file = user_home_path('replica.my.cnf')
db_hostname = 'localhost'
db_username = ''
db_password = ''
db_name_format = '{0}'
db_connect_file = user_home_path('.my.cnf')
# local port for mysql server
# ssh -L 4711:enwiki.analytics.db.svc.eqiad.wmflabs:3306 \
#     user@login.tools.wmflabs.org
db_port = 3306

# ############# SEARCH ENGINE SETTINGS ##############
# Live search web service appid settings.
#
# Yahoo! Search Web Services are not operational.
# See https://phabricator.wikimedia.org/T106085
yahoo_appid = ''

# To use Windows Live Search web service you must get an AppID from
# http://www.bing.com/dev/en-us/dev-center
msn_appid = ''

# ############# FLICKR RIPPER SETTINGS ##############

# Using the Flickr api
flickr = {
    'api_key': '',  # Provide your key!
    'api_secret': '',  # Api secret of your key (optional)
    'review': False,  # Do we use automatically make our uploads reviewed?
    'reviewer': '',  # If so, under what reviewer name?
}

# ############# COPYRIGHT SETTINGS ##############

# Enable/disable search engine in copyright.py script
copyright_google = True
copyright_yahoo = True
copyright_msn = False

# Perform a deep check, loading URLs to search if 'Wikipedia' is present.
# This may be useful to increase the number of correct results. If you haven't
# a fast connection, you might want to keep them disabled.
copyright_check_in_source_google = False
copyright_check_in_source_yahoo = False
copyright_check_in_source_msn = False

# Web pages may contain a Wikipedia text without the word 'Wikipedia' but with
# the typical '[edit]' tag as a result of a copy & paste procedure. You want
# no report for this kind of URLs, even if they are copyright violations.
# However, when enabled, these URLs are logged in a file.
copyright_check_in_source_section_names = False

# Limit number of queries for page.
copyright_max_query_for_page = 25

# Skip a specified number of queries
copyright_skip_query = 0

# Number of attempts on connection error.
copyright_connection_tries = 10

# Behavior if an exceeded error occur.
#
# Possibilities:
#
#    0 = None
#    1 = Disable search engine
#    2 = Sleep (default)
#    3 = Stop
copyright_exceeded_in_queries = 2
copyright_exceeded_in_queries_sleep_hours = 6

# Append last modified date of URL to script result
copyright_show_date = True

# Append length of URL to script result
copyright_show_length = True

# By default the script tries to identify and skip text that contains a large
# comma separated list or only numbers. But sometimes that might be the
# only part unmodified of a slightly edited and not otherwise reported
# copyright violation. You can disable this feature to try to increase the
# number of results.
copyright_economize_query = True

# ############# HTTP SETTINGS ##############
# Use a persistent http connection. An http connection has to be established
# only once per site object, making stuff a whole lot faster. Do NOT EVER
# use this if you share Site objects across threads without proper locking.
#
# DISABLED FUNCTION. Setting this variable will not have any effect.
persistent_http = False

# Default socket timeout in seconds.
# DO NOT set to None to disable timeouts. Otherwise this may freeze your
# script.
# You may assign either a tuple of two int or float values for connection and
# read timeout, or a single value for both in a tuple (since requests 2.4.0).
socket_timeout = (6.05, 45)


# ############# COSMETIC CHANGES SETTINGS ##############
# The bot can make some additional changes to each page it edits, e.g. fix
# whitespace or positioning of interwiki and category links.

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
# Please set your dictionary by adding such lines to your user-config.py:
# cosmetic_changes_enable['wikipedia'] = ('de', 'en', 'fr')
cosmetic_changes_enable = {}

# The dictionary cosmetic_changes_disable should contain a tuple of languages
# for each site where you wish to disable cosmetic changes. You may use it with
# cosmetic_changes_mylang_only is False, but you can also disable your own
# language. This also overrides the settings in the cosmetic_changes_enable
# dictionary. Please set your dict by adding such lines to your user-config.py:
# cosmetic_changes_disable['wikipedia'] = ('de', 'en', 'fr')
cosmetic_changes_disable = {}

# cosmetic_changes_deny_script is a list of scripts for which cosmetic changes
# are disabled. You may add additional scripts by appending script names in
# your user-config.py ("+=" operator is strictly recommended):
# cosmetic_changes_deny_script += ['your_script_name_1', 'your_script_name_2']
# Appending the script name also works:
# cosmetic_changes_deny_script.append('your_script_name')
cosmetic_changes_deny_script = ['category_redirect', 'cosmetic_changes',
                                'newitem', 'touch']

# ############# REPLICATION BOT SETTINGS ################
# You can add replicate_replace to your user-config.py.
#
# Use has the following format:
#
# replicate_replace = {
#            'wikipedia:li': {'Hoofdpagina': 'Veurblaad'}
# }
#
# to replace all occurrences of 'Hoofdpagina' with 'Veurblaad' when writing to
# liwiki. Note that this does not take the origin wiki into account.
replicate_replace = {}

# ############# FURTHER SETTINGS ##############

# Simulate settings

# Defines what additional actions the bots are NOT allowed to do (e.g. 'edit')
# on the wiki server. Allows simulation runs of bots to be carried out without
# changing any page on the server side. Use this setting to add more actions
# in user-config.py for wikis with extra write actions.
actions_to_block = []

# Set simulate to True or use -simulate option to block all actions given
# above.
simulate = False

# How many pages should be put to a queue in asynchronous mode.
# If maxsize is <= 0, the queue size is infinite.
# Increasing this value will increase memory space but could speed up
# processing. As higher this value this effect will decrease.
max_queue_size = 64

# Settings to enable mwparserfromhell
# <https://mwparserfromhell.readthedocs.org/en/latest/>
# Currently used in textlib.extract_templates_and_params
# This is more accurate than our current regex, but only works
# if the user has already installed the library.
use_mwparserfromhell = True

# Pickle protocol version to use for storing dumps.
# This config variable is not used for loading dumps.
# Version 2 is common to both Python 2 and 3, and should
# be used when dumps are accessed by both versions.
# Version 4 is only available for Python 3.4
pickle_protocol = 2

# ============================
# End of configuration section
# ============================

# ############# OBSOLETE SETTINGS #############
# This section contains configuration options that are no longer in use.
# They are kept here to prevent warnings about undefined parameters.

# No obsolete settings currently

# #############################################


def makepath(path, create=True):
    """Return a normalized absolute version of the path argument.

    If the given path already exists in the filesystem or create is False
    the filesystem is not modified.
    Otherwise if create is True makepath creates directories along the given
    path using the dirname() of the path. You may append a '/' to the path if
    you want it to be a directory path.

    from holger@trillke.net 2002/03/18

    @param path: path in the filesystem
    @type path: str
    @param create: create the directory if it is True. Otherwise do not change
        the filesystem. Default is True.
    @type create: bool
    """
    dpath = os.path.normpath(os.path.dirname(path))
    if create and not os.path.exists(dpath):
        os.makedirs(dpath)
    return os.path.normpath(os.path.abspath(path))


def datafilepath(*filename, **kwargs):
    """Return an absolute path to a data file in a standard location.

    Argument(s) are zero or more directory names, optionally followed by a
    data file name. The return path is offset to config.base_dir. Any
    directories in the path that do not already exist are created if create
    is True, otherwise the filesystem keeps unchanged.

    @param path: path in the filesystem
    @type path: str
    @keyword create: create the directory if it is True. Otherwise don't change
        the filesystem. Default is True.
    @type create: bool
    """
    create = kwargs.get('create', True)
    return makepath(os.path.join(base_dir, *filename), create=create)


def shortpath(path):
    """Return a file path relative to config.base_dir."""
    if path.startswith(base_dir):
        return path[len(base_dir) + len(os.path.sep):]
    return path


def _win32_extension_command(extension):
    """Get the command from the Win32 registry for an extension."""
    fileexts_key = \
        r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts'
    key_name = fileexts_key + r'\.' + extension + r'\OpenWithProgids'
    _winreg = winreg  # exists for git blame only; do not use
    try:
        key1 = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_name)
        _prog_id = winreg.EnumValue(key1, 0)[0]
        _key2 = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,
                                r'%s\shell\open\command' % _prog_id)
        _cmd = _winreg.QueryValueEx(_key2, None)[0]
        # See T102465 for issues relating to using this value.
        cmd = _cmd
        if cmd.find('%1'):
            cmd = cmd[:cmd.find('%1')]
            # Remove any trailing character, which should be a quote or space
            # and then remove all whitespace.
            return cmd[:-1].strip()
    except WindowsError as e:
        # Catch any key lookup errors
        output('Unable to detect program for file extension "{0}": {1!r}'
               .format(extension, e))


def _detect_win32_editor():
    """Detect the best Win32 editor."""
    # Notepad is even worse than our Tkinter editor.
    unusable_exes = ['notepad.exe',
                     'py.exe',
                     'pyw.exe',
                     'python.exe',
                     'pythonw.exe']

    for ext in ['py', 'txt']:
        editor = _win32_extension_command(ext)
        if editor:
            for unusable in unusable_exes:
                if unusable in editor.lower():
                    break
            else:
                return editor


# System-level and User-level changes.
# Store current variables and their types.
_public_globals = {
    _key: _val for _key, _val in globals().items()
    if _key[0] != '_' and _key not in _imports}

# Create an environment for user-config.py which is
# a deep copy of the core config settings, so that
# we can detect modified config items easily.
_exec_globals = copy.deepcopy(_public_globals)

# Get the user files
if __no_user_config:
    if __no_user_config != '2':
        warning('Skipping loading of user-config.py.')
else:
    _filename = os.path.join(base_dir, 'user-config.py')
    if os.path.exists(_filename):
        _filestatus = os.stat(_filename)
        _filemode = _filestatus[0]
        _fileuid = _filestatus[4]
        if OSWIN32 or _fileuid in [os.getuid(), 0]:
            if OSWIN32 or _filemode & 0o02 == 0:
                with open(_filename, 'rb') as f:
                    exec(compile(f.read(), _filename, 'exec'), _exec_globals)
            else:
                warning("Skipped '%(fn)s': writeable by others."
                        % {'fn': _filename})
        else:
            warning("Skipped '%(fn)s': owned by someone else."
                    % {'fn': _filename})


class _DifferentTypeError(UserWarning, TypeError):

    """An error when the required type doesn't match the actual type."""

    def __init__(self, name, actual_type, allowed_types):
        super(_DifferentTypeError, self).__init__(
            'Configuration variable "{0}" is defined as "{1.__name__}" in '
            'your user-config.py but expected "{2}".'
            .format(name, actual_type, '", "'.join(t.__name__
                                                   for t in allowed_types)))


def _assert_default_type(name, value, default_value):
    """Return the value if the old or new is None or both same type."""
    if (value is None or default_value is None
            or isinstance(value, type(default_value))):
        return value
    elif isinstance(value, int) and isinstance(default_value, float):
        return float(value)
    else:
        raise _DifferentTypeError(name, type(value), [type(default_value)])


def _assert_types(name, value, types):
    """Return the value if it's one of the types."""
    if isinstance(value, types):
        return value
    else:
        raise _DifferentTypeError(name, type(value), types)


DEPRECATED_VARIABLE = (
    '"{}" present in our user-config.py is no longer a supported '
    'configuration variable and should be removed. Please inform the '
    'maintainers if you depend on it.')


def _check_user_config_types(user_config, default_values, skipped):
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
            else:
                warn('\n'
                     + fill('Configuration variable "{0}" is defined in your '
                            'user-config.py but unknown. It can be a '
                            'misspelled one or a variable that is no longer '
                            'supported.'.format(name)), UserWarning)


_check_user_config_types(_exec_globals, _public_globals, _imports)

# Copy the user config settings into globals
_modified = {_key for _key in _public_globals.keys()
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
# assume utf-8. On Linux, this will typically be correct; on windows,
# this can be an issue when piping through more. However, the behavior
# when redirecting to a file utf-8 is more reasonable.

if console_encoding is None:
    console_encoding = 'utf-8'

if OSWIN32 and editor is None:
    editor = _detect_win32_editor()

if OSWIN32 and editor:
    # single character string literals from
    # https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals
    # encode('unicode-escape') also changes Unicode characters
    if set(editor) & set('\a\b\f\n\r\t\v'):
        warning(
            'The editor path contains probably invalid escaped '
            'characters. Make sure to use a raw-string (r"..." or '
            "r'...'), forward slashes as a path delimiter or to escape the "
            'normal path delimiter.')

if userinterface_lang is None:
    userinterface_lang = os.getenv('PYWIKIBOT_USERINTERFACE_LANG') \
        or getdefaultlocale()[0]
    if userinterface_lang in [None, 'C']:
        userinterface_lang = 'en'
    else:
        userinterface_lang = userinterface_lang.split('_')[0]

# Fix up default site
if family == 'wikipedia' and mylang == 'language':
    if __no_user_config != '2':
        warning('family and mylang are not set.\n'
                "Defaulting to family='wikipedia' and mylang='test'.")
    mylang = 'test'

# Fix up socket_timeout
# Older requests library expect a single value whereas newer versions also
# accept a tuple (connect timeout, read timeout).
if (isinstance(socket_timeout, tuple)
        and StrictVersion(requests_version) < StrictVersion('2.4.0')):
    socket_timeout = max(socket_timeout)

# SECURITY WARNINGS
if (not ignore_file_security_warnings
        and private_files_permission & (stat.S_IRWXG | stat.S_IRWXO) != 0):
    error("CRITICAL SECURITY WARNING: 'private_files_permission' is set"
          ' to allow access from the group/others which'
          ' could give them access to the sensitive files.'
          ' To avoid giving others access to sensitive files, pywikibot'
          " won't run with this setting. Choose a more restrictive"
          " permission or set 'ignore_file_security_warnings' to true.")
    sys.exit(1)

#
# When called as main program, list all configuration variables
#
if __name__ == '__main__':
    _all = True
    for _arg in sys.argv[1:]:
        if _arg == 'modified':
            _all = False
        else:
            warning('Unknown arg {0} ignored'.format(_arg))
    _k = list(globals().keys())
    _k.sort()
    for _name in _k:
        if _name[0] != '_':
            if not type(globals()[_name]) in [types.FunctionType,
                                              types.ModuleType]:
                if _all or _name in _modified:
                    _value = globals()[_name]
                    if _name in _private_values and _value:
                        if isinstance(_value, dict):
                            _value = '{ ...xxxxxxxx... }'
                        elif hasattr(_value, '__dict__'):
                            _value = (_value.__class__.__name__
                                      + '( ...xxxxxxxx... )')
                        else:
                            _value = repr('xxxxxxxx')
                    else:
                        _value = repr(_value)
                    output('{0}={1}'.format(_name, _value))

# cleanup all locally-defined variables
for __var in list(globals().keys()):
    if __var.startswith('_') and not __var.startswith('__'):
        del sys.modules[__name__].__dict__[__var]

del __var
