"""Module to determine the pywikibot version (tag, revision and date)."""
#
# (C) Pywikibot team, 2007-2022
#
# Distributed under the terms of the MIT license.
#
import datetime
import json
import os
import pathlib
import socket
import subprocess
import sys
import sysconfig
import time
import xml.dom.minidom
from contextlib import closing, suppress
from importlib import import_module
from io import BytesIO
from typing import Optional
from warnings import warn

import pywikibot
from pywikibot import config
from pywikibot.backports import cache, Dict, List, Tuple
from pywikibot.comms.http import fetch
from pywikibot.exceptions import VersionParseError


def _get_program_dir():
    _program_dir = os.path.normpath(
        os.path.split(os.path.dirname(__file__))[0])
    return _program_dir


def get_toolforge_hostname() -> Optional[str]:
    """Get hostname of the current Toolforge host.

    .. versionadded:: 3.0

    :return: The hostname of the currently running host,
             if it is in Wikimedia Toolforge; otherwise return None.
    """
    if socket.getfqdn().endswith('.tools.eqiad.wmflabs'):
        return socket.gethostname()
    return None


def getversion(online: bool = True) -> str:
    """Return a pywikibot version string.

    :param online: Include information obtained online
    """
    branches = {
        'master': 'branches/master',
        'stable': 'branches/stable',
    }
    data = getversiondict()
    data['cmp_ver'] = 'n/a'
    local_hsh = data.get('hsh', '')
    hsh = {}

    if online:
        if not local_hsh:
            data['cmp_ver'] = 'UNKNOWN'
        else:
            for branch, path in branches.items():
                with suppress(Exception):
                    hsh[getversion_onlinerepo(path)] = branch
            if hsh:
                data['cmp_ver'] = hsh.get(local_hsh, 'OUTDATED')

    data['hsh'] = local_hsh[:7]  # make short hash from full hash
    return '{tag} ({hsh}, {rev}, {date}, {cmp_ver})'.format_map(data)


@cache
def getversiondict() -> Dict[str, str]:
    """Get version info for the package.

    :return:
        - tag (name for the repository),
        - rev (current revision identifier),
        - date (date of current revision),
        - hash (git hash for the current revision)
    """
    _program_dir = _get_program_dir()
    exceptions = {}

    for vcs_func in (getversion_git,
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
        warn('Unable to detect version; exceptions raised:\n{!r}'
             .format(exceptions), UserWarning)
        exceptions = None

    # Git and SVN can silently fail, as it may be a nightly.
    if exceptions:
        pywikibot.debug('version algorithm exceptions:\n{!r}'
                        .format(exceptions))

    if isinstance(date, str):
        datestring = date
    elif isinstance(date, time.struct_time):
        datestring = time.strftime('%Y/%m/%d, %H:%M:%S', date)
    else:
        warn('Unable to detect package date', UserWarning)
        datestring = '-2 (unknown)'

    return {'tag': tag, 'rev': rev, 'date': datestring, 'hsh': hsh}


def svn_rev_info(path):  # pragma: no cover
    """Fetch information about the current revision of a Subversion checkout.

    :param path: directory of the Subversion checkout
    :return:
        - tag (name for the repository),
        - rev (current Subversion revision identifier),
        - date (date of current revision),
    :rtype: ``tuple`` of two ``str`` and a ``time.struct_time``
    """
    if not os.path.isdir(os.path.join(path, '.svn')):
        path = os.path.join(path, '..')

    _program_dir = path
    filename = os.path.join(_program_dir, '.svn/entries')
    if os.path.isfile(filename):
        with open(filename) as entries:
            version = entries.readline().strip()
            if version != '12':
                for _ in range(3):
                    entries.readline()
                tag = entries.readline().strip()
                t = tag.split('://', 1)
                t[1] = t[1].replace('svn.wikimedia.org/svnroot/pywikipedia/',
                                    '')
                tag = '[{}] {}'.format(*t)
                for _ in range(4):
                    entries.readline()
                date = time.strptime(entries.readline()[:19],
                                     '%Y-%m-%dT%H:%M:%S')
                rev = entries.readline()[:-1]
                return tag, rev, date

    # We haven't found the information in entries file.
    # Use sqlite table for new entries format
    from sqlite3 import dbapi2 as sqlite
    with closing(
            sqlite.connect(os.path.join(_program_dir, '.svn/wc.db'))) as con:
        cur = con.cursor()
        cur.execute("""select
local_relpath, repos_path, revision, changed_date, checksum from nodes
order by revision desc, changed_date desc""")
        _name, tag, rev, date, _checksum = cur.fetchone()
        cur.execute('select root from repository')
        tag, = cur.fetchone()

    tag = os.path.split(tag)[1]
    date = time.gmtime(date / 1000000)
    return tag, rev, date


def github_svn_rev2hash(tag: str, rev):  # pragma: no cover
    """Convert a Subversion revision to a Git hash using Github.

    :param tag: name of the Subversion repo on Github
    :param rev: Subversion revision identifier
    :return: the git hash
    """
    uri = 'https://github.com/wikimedia/{}/!svn/vcc/default'.format(tag)
    request = fetch(uri, method='PROPFIND',
                    data="<?xml version='1.0' encoding='utf-8'?>"
                         '<propfind xmlns=\"DAV:\"><allprop/></propfind>',
                    headers={'label': str(rev),
                             'user-agent': 'SVN/1.7.5 {pwb}'})
    dom = xml.dom.minidom.parse(BytesIO(request.content))
    hsh = dom.getElementsByTagName('C:git-commit')[0].firstChild.nodeValue
    date = dom.getElementsByTagName('S:date')[0].firstChild.nodeValue
    date = time.strptime(date[:19], '%Y-%m-%dT%H:%M:%S')
    return hsh, date


def getversion_svn(path=None):  # pragma: no cover
    """Get version info for a Subversion checkout.

    :param path: directory of the Subversion checkout
    :return:
        - tag (name for the repository),
        - rev (current Subversion revision identifier),
        - date (date of current revision),
        - hash (git hash for the Subversion revision)
    :rtype: ``tuple`` of three ``str`` and a ``time.struct_time``
    """
    _program_dir = path or _get_program_dir()
    tag, rev, date = svn_rev_info(_program_dir)
    hsh, date2 = github_svn_rev2hash(tag, rev)
    if date.tm_isdst >= 0 and date2.tm_isdst >= 0:
        assert date == date2, 'Date of version is not consistent'
    # date.tm_isdst is -1 means unknown state
    # compare its contents except daylight saving time status
    else:
        for i in range(len(date) - 1):
            assert date[i] == date2[i], 'Date of version is not consistent'

    rev = 's{}'.format(rev)
    if (not date or not tag or not rev) and not path:
        raise VersionParseError
    return (tag, rev, date, hsh)


def getversion_git(path=None):
    """Get version info for a Git clone.

    :param path: directory of the Git checkout
    :return:
        - tag (name for the repository),
        - rev (current revision identifier),
        - date (date of current revision),
        - hash (git hash for the current revision)
    :rtype: ``tuple`` of three ``str`` and a ``time.struct_time``
    """
    _program_dir = path or _get_program_dir()
    cmd = 'git'
    try:
        subprocess.Popen([cmd], stdout=subprocess.PIPE).communicate()
    except OSError:
        # some Windows git versions provide git.cmd instead of git.exe
        cmd = 'git.cmd'

    with open(os.path.join(_program_dir, '.git/config')) as f:
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
        tag = '[{}] {}'.format(t[0][:-1], '-'.join(t[3:]))
    dp = subprocess.Popen([cmd, '--no-pager',
                           'log', '-1',
                           '--pretty=format:"%ad|%an|%h|%H|%d"',
                           '--abbrev-commit',
                           '--date=iso'],
                          cwd=_program_dir,
                          stdout=subprocess.PIPE)
    info, _ = dp.communicate()
    info = info.decode(config.console_encoding).split('|')
    date = info[0][:-6]
    date = time.strptime(date.strip('"'), '%Y-%m-%d %H:%M:%S')
    dp = subprocess.Popen([cmd, 'rev-list', 'HEAD'],
                          cwd=_program_dir,
                          stdout=subprocess.PIPE)
    rev, stderr = dp.communicate()
    rev = 'g{}'.format(len(rev.splitlines()))
    hsh = info[3]  # also stored in '.git/refs/heads/master'
    if (not date or not tag or not rev) and not path:
        raise VersionParseError
    return (tag, rev, date, hsh)


def getversion_nightly(path=None):  # pragma: no cover
    """Get version info for a nightly release.

    :param path: directory of the uncompressed nightly.
    :return:
        - tag (name for the repository),
        - rev (current revision identifier),
        - date (date of current revision),
        - hash (git hash for the current revision)
    :rtype: ``tuple`` of three ``str`` and a ``time.struct_time``
    """
    if not path:
        path = _get_program_dir()

    with open(os.path.join(path, 'version')) as data:
        (tag, rev, date, hsh) = data.readlines()

    date = time.strptime(date[:19], '%Y-%m-%dT%H:%M:%S')

    if not date or not tag or not rev:
        raise VersionParseError
    return (tag, rev, date, hsh)


def getversion_package(path=None) -> Tuple[str, str, str, str]:
    """Get version info for an installed package.

    :param path: Unused argument
    :return:
        - tag: 'pywikibot/__init__.py'
        - rev: '-1 (unknown)'
        - date (date the package was installed locally),
        - hash (git hash for the current revision of 'pywikibot/__init__.py')
    """
    hsh = ''
    date = get_module_mtime(pywikibot).timetuple()

    tag = 'pywikibot/__init__.py'
    rev = '-1 (unknown)'

    return (tag, rev, date, hsh)


def getversion_onlinerepo(path: str = 'branches/master'):
    """Retrieve current framework git hash from Gerrit."""
    from pywikibot.comms import http

    # Gerrit API responses include )]}' at the beginning,
    # make sure to strip it out
    buf = http.fetch(
        'https://gerrit.wikimedia.org/r/projects/pywikibot%2Fcore/' + path,
        headers={'user-agent': '{pwb}'}).text[4:]
    try:
        hsh = json.loads(buf)['revision']
        return hsh
    except Exception as e:
        raise VersionParseError('{!r} while parsing {!r}'.format(e, buf))


def get_module_filename(module) -> Optional[str]:
    """
    Retrieve filename from an imported pywikibot module.

    It uses the __file__ attribute of the module. If it's file extension ends
    with py and another character the last character is discarded when the py
    file exist.

    :param module: The module instance.
    :type module: module
    :return: The filename if it's a pywikibot module otherwise None.
    """
    if hasattr(module, '__file__'):
        filename = module.__file__
        if not filename or not os.path.exists(filename):
            return None

        program_dir = _get_program_dir()
        if filename[:len(program_dir)] == program_dir:
            return filename
    return None


def get_module_mtime(module):
    """
    Retrieve the modification time from an imported module.

    :param module: The module instance.
    :type module: module
    :return: The modification time if it's a pywikibot module otherwise None.
    :rtype: datetime or None
    """
    filename = get_module_filename(module)
    if filename:
        return datetime.datetime.fromtimestamp(os.stat(filename).st_mtime)
    return None


def package_versions(
    modules: Optional[List[str]] = None,
    builtins: Optional[bool] = False,
    standard_lib: Optional[bool] = None
):
    """Retrieve package version information.

    When builtins or standard_lib are None, they will be included only
    if a version was found in the package.

    :param modules: Modules to inspect
    :param builtins: Include builtins
    :param standard_lib: Include standard library packages
    """
    if not modules:
        modules = sys.modules.keys()

    std_lib_dir = pathlib.Path(sysconfig.get_paths()['stdlib'])

    root_packages = {key.split('.')[0] for key in modules}

    builtin_packages = {name.split('.')[0] for name in root_packages
                        if name in sys.builtin_module_names
                        or '_' + name in sys.builtin_module_names}

    # Improve performance by removing builtins from the list if possible.
    if builtins is False:
        root_packages = root_packages - builtin_packages

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
            # possible Namespace package
            if not hasattr(package, '__file__') or package.__file__ is None:
                _file = None
                _path = pathlib.Path(package.__path__[0])
            else:
                _file = pathlib.Path(package.__file__)
                _path = _file.parent
            if _path == std_lib_dir:
                std_lib_packages.append(name)
                if standard_lib is False:
                    continue
                info['type'] = 'standard library'

            # Strip '__init__.py' from the filename.
            if (not hasattr(package, '__file__')
                    or package.__file__ is None
                    or _file.name == '__init__.py'):
                path = _path
            else:
                path = _file

            info['path'] = path
            assert path not in paths, \
                   'Path {} of the package {} is in defined paths as {}' \
                   .format(path, name, paths[path])
            paths[path] = name

        if '__version__' in package.__dict__:
            info['ver'] = package.__version__
        elif name.startswith('unicodedata'):
            info['ver'] = package.unidata_version

        # If builtins or standard_lib is None,
        # only include package if a version was found.
        if builtins is None and name in builtin_packages \
           or standard_lib is None and name in std_lib_packages:
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
    dir_parts = pathlib.Path(_program_dir).parts
    length = len(dir_parts)
    for path, name in paths.items():
        lib_parts = path.parts
        if dir_parts != lib_parts[:length]:
            continue
        if lib_parts[length] != '.tox':
            del data[name]

    return data
