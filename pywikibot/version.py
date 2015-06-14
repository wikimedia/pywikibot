# -*- coding: utf-8 -*-
"""Module to determine the pywikibot version (tag, revision and date)."""
#
# (C) Pywikibot team, 2007-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import codecs
import datetime
from importlib import import_module
import json
import os
import socket
import subprocess
import sys
import time
import xml.dom.minidom

from distutils import log
from distutils.sysconfig import get_python_lib
from io import BytesIO
from warnings import warn

try:
    from setuptools import svn_utils
except ImportError:
    try:
        from setuptools_svn import svn_utils
    except ImportError as e:
        svn_utils = e

try:
    import pathlib
except ImportError:
    try:
        import pathlib2 as pathlib
    except ImportError as e:
        pathlib = e

import pywikibot

from pywikibot import config2 as config
from pywikibot.tools import deprecated, PY2, UnicodeType

cache = None
_logger = 'version'


class ParseError(Exception):

    """Parsing went wrong."""


def _get_program_dir():
    _program_dir = os.path.normpath(
        os.path.split(os.path.dirname(__file__))[0])
    return _program_dir


def get_toolforge_hostname():
    """Get hostname of the current Toolforge host.

    @return: The hostname of the currently running host,
             if it is in Wikimedia Toolforge; otherwise return None.
    @rtype: str or None
    """
    if socket.getfqdn().endswith('.tools.eqiad.wmflabs'):
        return socket.gethostname()
    return None


def getversion(online=True):
    """Return a pywikibot version string.

    @param online: (optional) Include information obtained online
    """
    data = dict(getversiondict())  # copy dict to prevent changes in 'cache'
    data['cmp_ver'] = 'n/a'

    if online:
        try:
            hsh3 = getversion_onlinerepo('tags/stable')
            hsh2 = getversion_onlinerepo()
            hsh1 = data['hsh']
            data['cmp_ver'] = 'UNKNOWN' if not hsh1 else (
                'OUTDATED' if hsh1 not in (hsh2, hsh3) else 'ok')
        except Exception:
            pass

    data['hsh'] = data['hsh'][:7]  # make short hash from full hash
    return '%(tag)s (%(hsh)s, %(rev)s, %(date)s, %(cmp_ver)s)' % data


def getversiondict():
    """Get version info for the package.

    @return:
        - tag (name for the repository),
        - rev (current revision identifier),
        - date (date of current revision),
        - hash (git hash for the current revision)
    @rtype: C{dict} of four C{str}
    """
    global cache
    if cache:
        return cache

    _program_dir = _get_program_dir()
    exceptions = {}

    for vcs_func in (getversion_git,
                     getversion_svn_setuptools,
                     getversion_svn,
                     getversion_nightly,
                     getversion_package):
        try:
            (tag, rev, date, hsh) = vcs_func(_program_dir)
        except Exception as e:
            exceptions[vcs_func] = e
        else:
            break
    else:
        # nothing worked; version unknown (but suppress exceptions)
        # the value is most likely '$Id' + '$', it means that
        # pywikibot was imported without using version control at all.
        tag, rev, date, hsh = (
            '', '-1 (unknown)', '0 (unknown)', '(unknown)')

    # git and svn can silently fail, as it may be a nightly.
    if getversion_package in exceptions:
        warn('Unable to detect version; exceptions raised:\n%r'
             % exceptions, UserWarning)
    elif exceptions:
        pywikibot.debug('version algorithm exceptions:\n%r'
                        % exceptions, _logger)

    if isinstance(date, UnicodeType):
        datestring = date
    elif isinstance(date, time.struct_time):
        datestring = time.strftime('%Y/%m/%d, %H:%M:%S', date)
    else:
        warn('Unable to detect package date', UserWarning)
        datestring = '-2 (unknown)'

    cache = {'tag': tag, 'rev': rev, 'date': datestring, 'hsh': hsh}
    return cache


@deprecated('getversion_svn_setuptools', since='20150405')
def svn_rev_info(path):
    """Fetch information about the current revision of an Subversion checkout.

    @param path: directory of the Subversion checkout
    @return:
        - tag (name for the repository),
        - rev (current Subversion revision identifier),
        - date (date of current revision),
    @rtype: C{tuple} of two C{str} and a C{time.struct_time}
    """
    if not os.path.isdir(os.path.join(path, '.svn')):
        path = os.path.join(path, '..')

    _program_dir = path
    filename = os.path.join(_program_dir, '.svn/entries')
    if os.path.isfile(filename):
        with open(filename) as entries:
            version = entries.readline().strip()
            if version != '12':
                for i in range(3):
                    entries.readline()
                tag = entries.readline().strip()
                t = tag.split('://', 1)
                t[1] = t[1].replace('svn.wikimedia.org/svnroot/pywikipedia/',
                                    '')
                tag = '[{0}] {1}'.format(*t)
                for i in range(4):
                    entries.readline()
                date = time.strptime(entries.readline()[:19],
                                     '%Y-%m-%dT%H:%M:%S')
                rev = entries.readline()[:-1]
                return tag, rev, date

    # We haven't found the information in entries file.
    # Use sqlite table for new entries format
    from sqlite3 import dbapi2 as sqlite
    con = sqlite.connect(os.path.join(_program_dir, '.svn/wc.db'))
    cur = con.cursor()
    cur.execute("""select
local_relpath, repos_path, revision, changed_date, checksum from nodes
order by revision desc, changed_date desc""")
    name, tag, rev, date, checksum = cur.fetchone()
    cur.execute('select root from repository')
    tag, = cur.fetchone()
    con.close()
    tag = os.path.split(tag)[1]
    date = time.gmtime(date / 1000000)
    return tag, rev, date


def github_svn_rev2hash(tag, rev):
    """Convert a Subversion revision to a Git hash using Github.

    @param tag: name of the Subversion repo on Github
    @param rev: Subversion revision identifier
    @return: the git hash
    @rtype: str
    """
    from pywikibot.comms import http

    uri = 'https://github.com/wikimedia/%s/!svn/vcc/default' % tag
    request = http.fetch(uri=uri, method='PROPFIND',
                         body="<?xml version='1.0' encoding='utf-8'?>"
                              '<propfind xmlns=\"DAV:\"><allprop/></propfind>',
                         headers={'label': str(rev),
                                  'user-agent': 'SVN/1.7.5 {pwb}'})

    dom = xml.dom.minidom.parse(BytesIO(request.raw))
    hsh = dom.getElementsByTagName('C:git-commit')[0].firstChild.nodeValue
    date = dom.getElementsByTagName('S:date')[0].firstChild.nodeValue
    date = time.strptime(date[:19], '%Y-%m-%dT%H:%M:%S')
    return hsh, date


def getversion_svn_setuptools(path=None):
    """Get version info for a Subversion checkout using setuptools.

    @param path: directory of the Subversion checkout
    @return:
        - tag (name for the repository),
        - rev (current Subversion revision identifier),
        - date (date of current revision),
        - hash (git hash for the Subversion revision)
    @rtype: C{tuple} of three C{str} and a C{time.struct_time}
    """
    if isinstance(svn_utils, Exception):
        raise svn_utils
    tag = 'pywikibot-core'
    _program_dir = path or _get_program_dir()
    svninfo = svn_utils.SvnInfo(_program_dir)
    # suppress warning
    old_level = log.set_threshold(log.ERROR)
    rev = svninfo.get_revision()
    log.set_threshold(old_level)
    if not isinstance(rev, int):
        raise TypeError('SvnInfo.get_revision() returned type %s' % type(rev))
    if rev < 0:
        raise ValueError('SvnInfo.get_revision() returned %d' % rev)
    if rev == 0:
        raise ParseError('SvnInfo: invalid workarea')
    hsh, date = github_svn_rev2hash(tag, rev)
    rev = 's%s' % rev
    return (tag, rev, date, hsh)


@deprecated('getversion_svn_setuptools', since='20150405')
def getversion_svn(path=None):
    """Get version info for a Subversion checkout.

    @param path: directory of the Subversion checkout
    @return:
        - tag (name for the repository),
        - rev (current Subversion revision identifier),
        - date (date of current revision),
        - hash (git hash for the Subversion revision)
    @rtype: C{tuple} of three C{str} and a C{time.struct_time}
    """
    _program_dir = path or _get_program_dir()
    tag, rev, date = svn_rev_info(_program_dir)
    hsh, date2 = github_svn_rev2hash(tag, rev)
    if date.tm_isdst >= 0 and date2.tm_isdst >= 0:
        assert date == date2, 'Date of version is not consistent'
    # date.tm_isdst is -1 means unknown state
    # compare its contents except daylight saving time status
    else:
        for i in range(date.n_fields - 1):
            assert date[i] == date2[i], 'Date of version is not consistent'

    rev = 's%s' % rev
    if (not date or not tag or not rev) and not path:
        raise ParseError
    return (tag, rev, date, hsh)


def getversion_git(path=None):
    """Get version info for a Git clone.

    @param path: directory of the Git checkout
    @return:
        - tag (name for the repository),
        - rev (current revision identifier),
        - date (date of current revision),
        - hash (git hash for the current revision)
    @rtype: C{tuple} of three C{str} and a C{time.struct_time}
    """
    _program_dir = path or _get_program_dir()
    cmd = 'git'
    try:
        subprocess.Popen([cmd], stdout=subprocess.PIPE).communicate()
    except OSError:
        # some windows git versions provide git.cmd instead of git.exe
        cmd = 'git.cmd'

    with open(os.path.join(_program_dir, '.git/config'), 'r') as f:
        tag = f.read()
    # Try 'origin' and then 'gerrit' as remote name; bail if can't find either.
    remote_pos = tag.find('[remote "origin"]')
    if remote_pos == -1:
        remote_pos = tag.find('[remote "gerrit"]')
    if remote_pos == -1:
        tag = '?'
    else:
        s = tag.find('url = ', remote_pos)
        e = tag.find('\n', s)
        tag = tag[(s + 6):e]
        t = tag.strip().split('/')
        tag = '[%s] %s' % (t[0][:-1], '-'.join(t[3:]))
    dp = subprocess.Popen([cmd, '--no-pager',
                           'log', '-1',
                           '--pretty=format:"%ad|%an|%h|%H|%d"'
                           '--abbrev-commit',
                           '--date=iso'],
                          cwd=_program_dir,
                          stdout=subprocess.PIPE)
    info, stderr = dp.communicate()
    info = info.decode(config.console_encoding).split('|')
    date = info[0][:-6]
    date = time.strptime(date.strip('"'), '%Y-%m-%d %H:%M:%S')
    dp = subprocess.Popen([cmd, 'rev-list', 'HEAD'],
                          cwd=_program_dir,
                          stdout=subprocess.PIPE)
    rev, stderr = dp.communicate()
    rev = 'g%s' % len(rev.splitlines())
    hsh = info[3]  # also stored in '.git/refs/heads/master'
    if (not date or not tag or not rev) and not path:
        raise ParseError
    return (tag, rev, date, hsh)


def getversion_nightly(path=None):
    """Get version info for a nightly release.

    @param path: directory of the uncompressed nightly.
    @return:
        - tag (name for the repository),
        - rev (current revision identifier),
        - date (date of current revision),
        - hash (git hash for the current revision)
    @rtype: C{tuple} of three C{str} and a C{time.struct_time}
    """
    if not path:
        path = _get_program_dir()

    with open(os.path.join(path, 'version')) as data:
        (tag, rev, date, hsh) = data.readlines()

    date = time.strptime(date[:19], '%Y-%m-%dT%H:%M:%S')

    if not date or not tag or not rev:
        raise ParseError
    return (tag, rev, date, hsh)


def getversion_package(path=None):
    """Get version info for an installed package.

    @param path: Unused argument
    @return:
        - tag: 'pywikibot/__init__.py'
        - rev: '-1 (unknown)'
        - date (date the package was installed locally),
        - hash (git hash for the current revision of 'pywikibot/__init__.py')
    @rtype: C{tuple} of four C{str}
    """
    hsh = ''
    date = get_module_mtime(pywikibot).timetuple()

    tag = 'pywikibot/__init__.py'
    rev = '-1 (unknown)'

    return (tag, rev, date, hsh)


def getversion_onlinerepo(path='branches/master'):
    """Retrieve current framework git hash from Gerrit."""
    from pywikibot.comms import http
    # Gerrit API responses include )]}' at the beginning,
    # make sure to strip it out
    buf = http.fetch(
        uri='https://gerrit.wikimedia.org/r/projects/pywikibot%2Fcore/' + path,
        headers={'user-agent': '{pwb}'}).text[4:]
    try:
        hsh = json.loads(buf)['revision']
        return hsh
    except Exception as e:
        raise ParseError(repr(e) + ' while parsing ' + repr(buf))


@deprecated('get_module_version, get_module_filename and get_module_mtime',
            since='20150221')
def getfileversion(filename):
    """Retrieve revision number of file.

    Extracts __version__ variable containing Id tag, without importing it.
    (thus can be done for any file)

    The version variable containing the Id tag is read and
    returned. Because it doesn't import it, the version can
    be retrieved from any file.
    @param filename: Name of the file to get version
    @type filename: str
    """
    _program_dir = _get_program_dir()
    __version__ = None
    mtime = None
    fn = os.path.join(_program_dir, filename)
    if os.path.exists(fn):
        with codecs.open(fn, 'r', 'utf-8') as f:
            for line in f.readlines():
                if line.find('__version__') == 0:
                    try:
                        exec(line)
                    except Exception:
                        pass
                    break
        stat = os.stat(fn)
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(' ')
    if mtime and __version__:
        return '%s %s %s' % (filename, __version__[5:-1][:7], mtime)
    else:
        return None


def get_module_version(module):
    """
    Retrieve __version__ variable from an imported module.

    @param module: The module instance.
    @type module: module
    @return: The version hash without the surrounding text. If not present
        return None.
    @rtype: str or None
    """
    if hasattr(module, '__version__'):
        return module.__version__[5:-1]


def get_module_filename(module):
    """
    Retrieve filename from an imported pywikibot module.

    It uses the __file__ attribute of the module. If it's file extension ends
    with py and another character the last character is discarded when the py
    file exist.

    @param module: The module instance.
    @type module: module
    @return: The filename if it's a pywikibot module otherwise None.
    @rtype: str or None
    """
    if hasattr(module, '__file__') and os.path.exists(module.__file__):
        filename = module.__file__
        if PY2:
            filename = os.path.abspath(filename)
        if filename[-4:-1] == '.py' and os.path.exists(filename[:-1]):
            filename = filename[:-1]
        program_dir = _get_program_dir()
        if filename[:len(program_dir)] == program_dir:
            return filename


def get_module_mtime(module):
    """
    Retrieve the modification time from an imported module.

    @param module: The module instance.
    @type module: module
    @return: The modification time if it's a pywikibot module otherwise None.
    @rtype: datetime or None
    """
    filename = get_module_filename(module)
    if filename:
        return datetime.datetime.fromtimestamp(os.stat(filename).st_mtime)


def package_versions(modules=None, builtins=False, standard_lib=None):
    """Retrieve package version information.

    When builtins or standard_lib are None, they will be included only
    if a version was found in the package.

    @param modules: Modules to inspect
    @type modules: list of strings
    @param builtins: Include builtins
    @type builtins: Boolean, or None for automatic selection
    @param standard_lib: Include standard library packages
    @type standard_lib: Boolean, or None for automatic selection
    """
    if not modules:
        modules = sys.modules.keys()

    std_lib_dir = get_python_lib(standard_lib=True)

    root_packages = {key.split('.')[0] for key in modules}

    builtin_packages = {name.split('.')[0] for name in root_packages
                        if name in sys.builtin_module_names
                        or '_' + name in sys.builtin_module_names}

    # Improve performance by removing builtins from the list if possible.
    if builtins is False:
        root_packages = list(root_packages - builtin_packages)

    std_lib_packages = []

    paths = {}
    data = {}

    for name in root_packages:
        try:
            package = import_module(name)
        except ImportError as e:
            data[name] = {'name': name, 'err': e}
            continue

        info = {'package': package, 'name': name}

        if name in builtin_packages:
            info['type'] = 'builtins'

        if '__file__' in package.__dict__:
            # Determine if this file part is of the standard library.
            if os.path.normcase(package.__file__).startswith(
                    os.path.normcase(std_lib_dir)):
                std_lib_packages.append(name)
                if standard_lib is False:
                    continue
                info['type'] = 'standard libary'

            # Strip '__init__.py' from the filename.
            path = package.__file__
            if '__init__.py' in path:
                path = path[0:path.index('__init__.py')]

            if PY2:
                path = path.decode(sys.getfilesystemencoding())

            info['path'] = path
            assert path not in paths, 'Path of the package is in defined paths'
            paths[path] = name

        if '__version__' in package.__dict__:
            info['ver'] = package.__version__
        elif name.startswith('unicodedata'):
            info['ver'] = package.unidata_version

        # If builtins or standard_lib is None,
        # only include package if a version was found.
        if (builtins is None and name in builtin_packages) or \
                (standard_lib is None and name in std_lib_packages):
            if 'ver' in info:
                data[name] = info
            else:
                # Remove the entry from paths, so it isn't processed below
                del paths[info['path']]
        else:
            data[name] = info

    # Remove any pywikibot sub-modules which were loaded as a package.
    # e.g. 'wikipedia_family.py' is loaded as 'wikipedia'
    _program_dir = _get_program_dir()
    if isinstance(pathlib, Exception):
        dir_parts = _program_dir.split(os.sep)
    else:
        dir_parts = pathlib.Path(_program_dir).parts
    length = len(dir_parts)
    for path, name in paths.items():
        if isinstance(pathlib, Exception):
            lib_parts = os.path.normpath(path).split(os.sep)
        else:
            lib_parts = pathlib.Path(path).parts
        if dir_parts != lib_parts[:length]:
            continue
        if lib_parts[length] != '.tox':
            del data[name]

    return data
