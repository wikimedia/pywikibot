# -*- coding: utf-8  -*-
"""Module to determine the pywikibot version (tag, revision and date)."""
#
# (C) Merlijn 'valhallasw' van Deen, 2007-2014
# (C) xqt, 2010-2015
# (C) Pywikibot team, 2007-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import os
import sys
import time
import datetime
import subprocess
import codecs

from warnings import warn

try:
    from setuptools import svn_utils
except ImportError:
    try:
        from setuptools_svn import svn_utils
    except ImportError as e:
        svn_utils = e

import pywikibot

from pywikibot import config2 as config
from pywikibot.tools import deprecated

if sys.version_info[0] > 2:
    basestring = (str, )

cache = None
_logger = 'version'


class ParseError(Exception):

    """Parsing went wrong."""


def _get_program_dir():
    _program_dir = os.path.normpath(os.path.split(os.path.dirname(__file__))[0])
    return _program_dir


def getversion(online=True):
    """Return a pywikibot version string.

    @param online: (optional) Include information obtained online
    """
    data = dict(getversiondict())  # copy dict to prevent changes in 'cache'
    data['cmp_ver'] = 'n/a'

    if online:
        try:
            hsh2 = getversion_onlinerepo()
            hsh1 = data['hsh']
            data['cmp_ver'] = 'OUTDATED' if hsh1 != hsh2 else 'ok'
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
                     getversion_nightly,
                     getversion_svn,
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

    if isinstance(date, basestring):
        datestring = date
    elif isinstance(date, time.struct_time):
        datestring = time.strftime('%Y/%m/%d, %H:%M:%S', date)
    else:
        warn('Unable to detect package date', UserWarning)
        datestring = '-2 (unknown)'

    cache = dict(tag=tag, rev=rev, date=datestring, hsh=hsh)
    return cache


@deprecated('getversion_svn_setuptools')
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
                t = tag.split('://')
                t[1] = t[1].replace('svn.wikimedia.org/svnroot/pywikipedia/',
                                    '')
                tag = '[%s] %s' % (t[0], t[1])
                for i in range(4):
                    entries.readline()
                date = time.strptime(entries.readline()[:19],
                                     '%Y-%m-%dT%H:%M:%S')
                rev = entries.readline()[:-1]
                return tag, rev, date

    # We haven't found the information in entries file.
    # Use sqlite table for new entries format
    from sqlite3 import dbapi2 as sqlite
    con = sqlite.connect(os.path.join(_program_dir, ".svn/wc.db"))
    cur = con.cursor()
    cur.execute("""select
local_relpath, repos_path, revision, changed_date, checksum from nodes
order by revision desc, changed_date desc""")
    name, tag, rev, date, checksum = cur.fetchone()
    cur.execute("select root from repository")
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
    from io import StringIO
    import xml.dom.minidom
    from pywikibot.comms import http

    uri = 'https://github.com/wikimedia/%s/!svn/vcc/default' % tag
    request = http.fetch(uri=uri, method='PROPFIND',
                         body="<?xml version='1.0' encoding='utf-8'?>"
                              "<propfind xmlns=\"DAV:\"><allprop/></propfind>",
                         headers={'label': str(rev),
                                  'user-agent': 'SVN/1.7.5 {pwb}'})
    data = request.content

    dom = xml.dom.minidom.parse(StringIO(data))
    hsh = dom.getElementsByTagName("C:git-commit")[0].firstChild.nodeValue
    date = dom.getElementsByTagName("S:date")[0].firstChild.nodeValue
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
    rev = svninfo.get_revision()
    if not isinstance(rev, int):
        raise TypeError('SvnInfo.get_revision() returned type %s' % type(rev))
    if rev < 0:
        raise ValueError('SvnInfo.get_revision() returned %d' % rev)
    if rev == 0:
        raise ParseError('SvnInfo: invalid workarea')
    hsh, date = github_svn_rev2hash(tag, rev)
    rev = 's%s' % rev
    return (tag, rev, date, hsh)


@deprecated('getversion_svn_setuptools')
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
        assert(date == date2)
    # date.tm_isdst is -1 means unknown state
    # compare its contents except daylight saving time status
    else:
        for i in range(date.n_fields - 1):
            assert(date[i] == date2[i])

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
    with subprocess.Popen([cmd, '--no-pager',
                           'log', '-1',
                           '--pretty=format:"%ad|%an|%h|%H|%d"'
                           '--abbrev-commit',
                           '--date=iso'],
                          cwd=_program_dir,
                          stdout=subprocess.PIPE).stdout as stdout:
        info = stdout.read()
    info = info.decode(config.console_encoding).split('|')
    date = info[0][:-6]
    date = time.strptime(date.strip('"'), '%Y-%m-%d %H:%M:%S')
    with subprocess.Popen([cmd, 'rev-list', 'HEAD'],
                          cwd=_program_dir,
                          stdout=subprocess.PIPE).stdout as stdout:
        rev = stdout.read()
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


def getversion_package(path=None):  # pylint: disable=unused-argument
    """Get version info for an installed package.

    @param path: Unused argument
    @return:
        - tag: 'pywikibot/__init__.py'
        - rev: '-1 (unknown)'
        - date (date the package was installed locally),
        - hash (git hash for the current revision of 'pywikibot/__init__.py')
    @rtype: C{tuple} of four C{str}
    """
    hsh = get_module_version(pywikibot)
    date = get_module_mtime(pywikibot).timetuple()

    tag = 'pywikibot/__init__.py'
    rev = '-1 (unknown)'

    return (tag, rev, date, hsh)


def getversion_onlinerepo(repo=None):
    """Retrieve current framework revision number from online repository.

    @param repo: (optional) Online repository location
    @type repo: URL or string
    """
    from pywikibot.comms import http

    url = repo or 'https://git.wikimedia.org/feed/pywikibot/core'
    buf = http.fetch(uri=url,
                     headers={'user-agent': '{pwb}'}).content.splitlines()
    try:
        hsh = buf[13].split('/')[5][:-1]
        return hsh
    except Exception as e:
        raise ParseError(repr(e) + ' while parsing ' + repr(buf))


@deprecated('get_module_version, get_module_filename and get_module_mtime')
def getfileversion(filename):
    """Retrieve revision number of file.

    Extracts __version__ variable containing Id tag, without importing it.
    (thus can be done for any file)

    The version variable containing the Id tag is read and
    returned. Because it doesn't import it, the version can
    be retrieved from any file.
    @param filename: Name of the file to get version
    @type filename: string
    """
    _program_dir = _get_program_dir()
    __version__ = None
    mtime = None
    fn = os.path.join(_program_dir, filename)
    if os.path.exists(fn):
        with codecs.open(fn, 'r', "utf-8") as f:
            for line in f.readlines():
                if line.find('__version__') == 0:
                    try:
                        exec(line)
                    except:
                        pass
                    break
        stat = os.stat(fn)
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(' ')
    if mtime and __version__:
        return u'%s %s %s' % (filename, __version__[5:-1][:7], mtime)
    else:
        return None


def get_module_version(module):
    """
    Retrieve __version__ variable from an imported module.

    @param module: The module instance.
    @type module: module
    @return: The version hash without the surrounding text. If not present None.
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

    import distutils.sysconfig
    std_lib_dir = distutils.sysconfig.get_python_lib(standard_lib=True)

    root_packages = set([key.split('.')[0]
                         for key in modules])

    builtin_packages = set([name.split('.')[0] for name in root_packages
                            if name in sys.builtin_module_names or
                            '_' + name in sys.builtin_module_names])

    # Improve performance by removing builtins from the list if possible.
    if builtins is False:
        root_packages = list(root_packages - builtin_packages)

    std_lib_packages = []

    paths = {}
    data = {}

    for name in root_packages:
        try:
            package = __import__(name, level=0)
        except Exception as e:
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

            if sys.version_info[0] == 2:
                path = path.decode(sys.getfilesystemencoding())

            info['path'] = path
            assert(path not in paths)
            paths[path] = name

        if '__version__' in package.__dict__:
            info['ver'] = package.__version__
        elif name == 'mwlib':  # mwlib 0.14.3 does not include a __init__.py
            module = __import__(name + '._version',
                                fromlist=['_version'], level=0)
            if '__version__' in module.__dict__:
                info['ver'] = module.__version__
                path = module.__file__
                path = path[0:path.index('_version.')]
                info['path'] = path

        # If builtins or standard_lib is None,
        # only include package if a version was found.
        if (builtins is None and name in builtin_packages) or \
                (standard_lib is None and name in std_lib_packages):
            if 'ver' in info:
                data[name] = info
            else:
                # Remove the entry from paths, so it isnt processed below
                del paths[info['path']]
        else:
            data[name] = info

    # Remove any pywikibot sub-modules which were loaded as a package.
    # e.g. 'wikipedia_family.py' is loaded as 'wikipedia'
    _program_dir = _get_program_dir()
    for path, name in paths.items():
        if _program_dir in path:
            del data[name]

    return data
