"""Module to determine the pywikibot version (tag, revision and date)."""
#
# (C) Pywikibot team, 2007-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import datetime
import json
import os
import pathlib
import socket
import subprocess
import sys
import sysconfig
import time
from contextlib import suppress
from importlib import import_module
from pathlib import Path
from warnings import warn

import pywikibot
from pywikibot import config
from pywikibot.backports import cache
from pywikibot.comms.http import fetch
from pywikibot.exceptions import VersionParseError
from pywikibot.tools import deprecated


def _get_program_dir() -> str:
    return os.path.normpath(os.path.split(os.path.dirname(__file__))[0])


@deprecated(since='9.0.0')
def get_toolforge_hostname() -> str | None:
    """Get hostname of the current Toolforge host.

    .. versionadded:: 3.0
    .. deprecated:: 9.0

    :return: The hostname of the currently running host,
             if it is in Wikimedia Toolforge; otherwise return None.
    """
    if socket.getfqdn().endswith('.tools.eqiad1.wikimedia.cloud'):
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
                with suppress(VersionParseError):
                    hsh[getversion_onlinerepo(path)] = branch
            if hsh:
                data['cmp_ver'] = hsh.get(local_hsh, 'OUTDATED')

    data['hsh'] = local_hsh[:7]  # make short hash from full hash
    return '{tag} ({hsh}, {rev}, {date}, {cmp_ver})'.format_map(data)


@cache
def getversiondict() -> dict[str, str]:
    """Get version info for the package.

    :return: Return a dict with the following keys:

        - tag (name for the repository),
        - rev (current revision identifier),
        - date (date of current revision),
        - hash (git hash for the current revision)
    """
    _program_dir = _get_program_dir()
    exceptions = {}

    for vcs_func in (getversion_git,
                     getversion_nightly,
                     getversion_package):
        try:
            tag, rev, date, hsh = vcs_func(_program_dir)
        except Exception as e:
            exceptions[vcs_func] = vcs_func.__name__, e
        else:
            break
    else:  # pragma: no cover
        # nothing worked; version unknown (but suppress exceptions)
        # the value is most likely '$Id' + '$', it means that
        # pywikibot was imported without using version control at all.
        tag, rev, date, hsh = (
            '', '-1 (unknown)', '0 (unknown)', '(unknown)')
        warn(f'Unable to detect version; exceptions raised:\n{exceptions!r}',
             UserWarning)
        exceptions = None

    # Git and SVN can silently fail, as it may be a nightly.
    if exceptions:  # pragma: no cover
        pywikibot.debug(f'version algorithm exceptions:\n{exceptions!r}')

    if isinstance(date, str):
        datestring = date
    elif isinstance(date, time.struct_time):
        datestring = time.strftime('%Y/%m/%d, %H:%M:%S', date)
    else:  # pragma: no cover
        warn('Unable to detect package date', UserWarning)
        datestring = '-2 (unknown)'

    return {'tag': tag, 'rev': rev, 'date': datestring, 'hsh': hsh}


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
        tag = f"[{t[0][:-1]}] {'-'.join(t[3:])}"
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
    rev = f'g{len(rev.splitlines())}'
    hsh = info[3]  # also stored in '.git/refs/heads/master'
    if (not date or not tag or not rev) and not path:
        raise VersionParseError
    return (tag, rev, date, hsh)


def getversion_nightly(path: str | Path | None = None):
    """Get version info for a nightly release.

    .. hint::
       the version information of the nightly dump is stored in the
       ``version`` file within the ``pywikibot`` folder.

    :param path: directory of the uncompressed nightly.
    :return:
        - tag (name for the repository),
        - rev (current revision identifier),
        - date (date of current revision),
        - hash (git hash for the current revision)
    :rtype: ``tuple`` of three ``str`` and a ``time.struct_time``
    """
    file = Path(path or _get_program_dir())
    if not path:
        file /= 'pywikibot'  # pragma: no cover
    file /= 'version'

    with file.open() as data:
        (tag, rev, date, hsh) = data.read().splitlines()

    date = time.strptime(date[:19], '%Y-%m-%dT%H:%M:%S')

    if not date or not tag or not rev:
        raise VersionParseError  # pragma: no cover
    return (tag, rev, date, hsh)


def getversion_package(path=None) -> tuple[str, str, str, str]:
    """Get version info for an installed package.

    :param path: Unused argument
    :return: Return a tuple with the following items:

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


def getversion_onlinerepo(path: str = 'branches/master') -> str:
    """Retrieve current framework git hash from Gerrit."""
    # Gerrit API responses include )]}' at the beginning,
    # make sure to strip it out
    buf = fetch(
        'https://gerrit.wikimedia.org/r/projects/pywikibot%2Fcore/' + path,
        headers={'user-agent': '{pwb}'}).text[4:]
    try:
        return json.loads(buf)['revision']
    except Exception as e:  # pragma: no cover
        raise VersionParseError(f'{e!r} while parsing {buf!r}')


def get_module_filename(module) -> str | None:
    """Retrieve filename from an imported pywikibot module.

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
        if filename.startswith(program_dir):
            return filename
    return None


def get_module_mtime(module):
    """Retrieve the modification time from an imported module.

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
    modules: list[str] | None = None,
    builtins: bool | None = False,
    standard_lib: bool | None = None,
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
        root_packages -= builtin_packages

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
            assert path not in paths, (
                f'Path {path} of the package {name} is in defined paths as '
                f'{paths[path]}'
            )

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
