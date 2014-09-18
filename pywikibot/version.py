# -*- coding: utf-8  -*-
""" Module to determine the pywikibot version (tag, revision and date). """
#
# (C) Merlijn 'valhallasw' van Deen, 2007-2014
# (C) xqt, 2010-2014
# (C) Pywikibot team, 2007-2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import os
import time
import datetime
import subprocess
import sys

import pywikibot.config2 as config

cache = None


class ParseError(Exception):

    """Parsing went wrong."""


def _get_program_dir():
    _program_dir = os.path.normpath(os.path.split(os.path.dirname(__file__))[0])
    return _program_dir


def getversion(online=True):
    """Return a pywikibot version string.

    @param online: (optional) Include information obtained online
    """
    data = dict(getversiondict())  # copy dict to prevent changes in 'chache'
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
    global cache
    if cache:
        return cache
    try:
        _program_dir = _get_program_dir()
        if os.path.isdir(os.path.join(_program_dir, '.svn')):
            (tag, rev, date, hsh) = getversion_svn(_program_dir)
        elif os.path.isdir(os.path.join(_program_dir, '../.svn')):
            (tag, rev, date, hsh) = getversion_svn(os.path.join(_program_dir, '..'))
        else:
            (tag, rev, date, hsh) = getversion_git(_program_dir)
    except Exception:
        try:
            (tag, rev, date, hsh) = getversion_nightly()
        except Exception:
            try:
                version = getfileversion('pywikibot/__init__.py')
                if not version:
                    # fall-back in case everything breaks (should not be used)
                    import pywikibot
                    version = getfileversion(pywikibot.__file__[:-1])

                file, hsh_short, date, ts = version.split(' ')
                tag = 'pywikibot/__init__.py'
                rev = '-1 (unknown)'
                ts = ts.split('.')[0]
                date = time.strptime('%sT%s' % (date, ts), '%Y-%m-%dT%H:%M:%S')
                hsh = hsh_short + ('?' * 33)   # enhance the short hash w. '?'
            except:
                # nothing worked; version unknown (but suppress exceptions)
                # the value is most likely '$Id' + '$', it means that
                # wikipedia.py got imported without using svn at all
                return dict(tag='', rev='-1 (unknown)', date='0 (unknown)',
                            hsh='(unknown)')

    datestring = time.strftime('%Y/%m/%d, %H:%M:%S', date)
    cache = dict(tag=tag, rev=rev, date=datestring, hsh=hsh)
    return cache


def svn_rev_info(path):
    """Fetch information about the current revision of an Subversion checkout.

    @param path: directory of the Subversion checkout
    @return:
        - tag (name for the repository),
        - rev (current Subversion revision identifier),
        - date (date of current revision),
    @rtype: C{tuple} of 3 C{str}
    """
    _program_dir = path
    entries = open(os.path.join(_program_dir, '.svn/entries'))
    version = entries.readline().strip()
    # use sqlite table for new entries format
    if version == "12":
        entries.close()
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
    else:
        for i in range(3):
            entries.readline()
        tag = entries.readline().strip()
        t = tag.split('://')
        t[1] = t[1].replace('svn.wikimedia.org/svnroot/pywikipedia/', '')
        tag = '[%s] %s' % (t[0], t[1])
        for i in range(4):
            entries.readline()
        date = time.strptime(entries.readline()[:19], '%Y-%m-%dT%H:%M:%S')
        rev = entries.readline()[:-1]
        entries.close()
    return tag, rev, date


def github_svn_rev2hash(tag, rev):
    """Convert a Subversion revision to a Git hash using Github.

    @param tag: name of the Subversion repo on Github
    @param rev: Subversion revision identifier
    @return: the git hash
    @rtype: str
    """
    if sys.version_info[0] > 2:
        from io import StringIO
    else:
        from StringIO import StringIO
    import xml.dom.minidom
    from pywikibot.comms import http

    uri = 'https://github.com/wikimedia/%s/!svn/vcc/default' % tag
    data = http.request(site=None, uri=uri, method='PROPFIND',
                        body="<?xml version='1.0' encoding='utf-8'?>"
                        "<propfind xmlns=\"DAV:\"><allprop/></propfind>",
                        headers={'label': str(rev), 'user-agent': 'SVN/1.7.5 {pwb}'})

    dom = xml.dom.minidom.parse(StringIO(data))
    hsh = dom.getElementsByTagName("C:git-commit")[0].firstChild.nodeValue
    return hsh


def getversion_svn(path=None):
    """Get version info for a Subversion checkout.

    @param path: directory of the Subversion checkout
    @return:
        - tag (name for the repository),
        - rev (current Subversion revision identifier),
        - date (date of current revision),
        - hash (git hash for the Subversion revision)
    @rtype: C{tuple} of 4 C{str}
    """
    _program_dir = path or _get_program_dir()
    tag, rev, date = svn_rev_info(_program_dir)
    hsh = github_svn_rev2hash(tag, rev)
    rev = 's%s' % rev
    if (not date or not tag or not rev) and not path:
        raise ParseError
    return (tag, rev, date, hsh)


def getversion_git(path=None):
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


def getversion_nightly():
    data = open(os.path.join(os.path.split(__file__)[0], 'version'))
    tag = data.readline().strip()
    rev = data.readline().strip()
    date = time.strptime(data.readline()[:19], '%Y-%m-%dT%H:%M:%S')
    hsh = data.readline().strip()

    if not date or not tag or not rev:
        raise ParseError
    return (tag, rev, date, hsh)


def getversion_onlinerepo(repo=None):
    """Retrieve current framework revision number from online repository.

    @param repo: (optional) Online repository location
    @type repo: URL or string
    """
    from pywikibot.comms import http

    url = repo or 'https://git.wikimedia.org/feed/pywikibot/core'
    hsh = None
    buf = http.request(site=None, uri=url)
    buf = buf.split('\r\n')
    try:
        hsh = buf[13].split('/')[5][:-1]
    except Exception as e:
        raise ParseError(repr(e) + ' while parsing ' + repr(buf))
    return hsh


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
        with open(fn, 'r') as f:
            for line in f.readlines():
                if line.find('__version__') == 0:
                    exec(line)
                    break
        stat = os.stat(fn)
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(' ')
    if mtime and __version__:
        return u'%s %s %s' % (filename, __version__[5:-1][:7], mtime)
    else:
        return None


def package_versions(modules=None, builtins=False, standard_lib=None):
    """ Retrieve package version information.

    When builtins or standard_lib are None, they will be included only
    if a version was found in the package.

    @param modules: Modules to inspect
    @type modules: list of strings
    @param builtins: Include builtins
    @type builtins: Boolean, or None for automatic selection
    @param standard_lib: Include standard library packages
    @type standard_lib: Boolean, or None for automatic selection
    """
    import sys

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
            data[name] = info

    # Remove any sub-packages which were loaded with a different name.
    # e.g. 'wikipedia_family.py' is loaded as 'wikipedia'
    for path, name in paths.items():
        for other_path in set(paths) - set([path]):
            if path.startswith(other_path) and not other_path.startswith(path):
                del paths[path]
                del data[name]

    return data
