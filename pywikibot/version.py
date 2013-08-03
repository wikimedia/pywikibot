# -*- coding: utf-8  -*-
""" Module to determine the pywikipedia version (tag, revision and date) """
#
# (C) Merlijn 'valhallasw' van Deen, 2007-2008
# (C) xqt, 2010-2012
# (C) Pywikipedia bot team, 2007-2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import os
import time, datetime
import urllib
import subprocess

cache = None


class ParseError(Exception):
    """ Parsing went wrong """


def _get_program_dir():
    _program_dir = os.path.normpath(os.path.split(os.path.dirname(__file__))[0])
#    _program_dir = _program_dir.rstrip(os.path.basename(_program_dir))
##   if not os.path.isabs(_program_dir):
##      _program_dir = os.path.normpath(os.path.join(os.getcwd(), _program_dir))
    return _program_dir


def getversion():
    data = dict(getversiondict())   # copy dict to prevent changes in 'chache'
    try:
        hsh2 = getversion_onlinerepo()
        hsh1 = data['hsh']
        data['cmp_ver'] = 'OUTDATED' if hsh1 != hsh2 else 'ok'
    except Exception:
        data['cmp_ver'] = 'n/a'
    data['hsh'] = data['hsh'][:7]   # make short hash from full hash
    return '%(tag)s (r%(rev)s, %(hsh)s, %(date)s, %(cmp_ver)s)' % data

def getversiondict():
    global cache
    if cache:
        return cache
    try:
        (tag, rev, date, hsh) = getversion_git()
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


def getversion_svn(path=None):
    _program_dir = path or _get_program_dir()
    entries = open(os.path.join(_program_dir, '.svn/entries'))
    version = entries.readline().strip()
    #use sqlite table for new entries format
    if version == "12":
        entries.close()
        from sqlite3 import dbapi2 as sqlite
        con = sqlite.connect(os.path.join(_program_dir, ".svn/wc.db"))
        cur = con.cursor()
        cur.execute('''select local_relpath, repos_path, revision, changed_date from nodes order by revision desc, changed_date desc''')
        name, tag, rev, date = cur.fetchone()
        con.close()
        tag = tag[:-len(name)]
        date = time.gmtime(date/1000000)
    else:
        for i in xrange(3):
            entries.readline()
        tag = entries.readline().strip()
        t = tag.split('://')
        t[1] = t[1].replace('svn.wikimedia.org/svnroot/pywikipedia/', '')
        tag = '[%s] %s' % (t[0], t[1])
        for i in xrange(4):
            entries.readline()
        date = time.strptime(entries.readline()[:19], '%Y-%m-%dT%H:%M:%S')
        rev = entries.readline()[:-1]
        entries.close()
    if (not date or not tag or not rev) and not path:
        raise ParseError
    return (tag, rev, date)

def getversion_git(path=None):
    _program_dir = path or _get_program_dir()
    #(try to use .git directory for new entries format)
    #tag  = subprocess.Popen('git config --get remote.origin.url',
    #                        shell=True,
    #                        stdout=subprocess.PIPE).stdout.read()
    tag = open(os.path.join(_program_dir, '.git/config'), 'r').read()
    s = tag.find('url = ', tag.find('[remote "origin"]'))
    e = tag.find('\n', s)
    tag = tag[(s+6):e]
    t = tag.strip().split('/')
    tag  = '[%s] %s' % (t[0][:-1], '/'.join(t[3:])[:-4])
    info = subprocess.Popen("git log --pretty=format:'%ad|%an|%h|%H|%d' --abbrev-commit --date=iso -1 | cat -",
                            shell=True,
                            stdout=subprocess.PIPE).stdout.read()
    info = info.split('|')
    date = info[0][:-6]
    date = time.strptime(date, '%Y-%m-%d %H:%M:%S')
    rev  = subprocess.Popen('git rev-list HEAD | wc -l',
                            shell=True,
                            stdout=subprocess.PIPE).stdout.read()
    rev  = int(rev.strip())
    hsh  = info[3]      # also stored in '.git/refs/heads/master'
    if (not date or not tag or not rev) and not path:
        raise ParseError
    return (tag, rev, date, hsh)

def getversion_nightly():
    data = open(os.path.join(wikipediatools.get_base_dir(), 'version'))
    tag = data.readline().strip()
    date = time.strptime(data.readline()[:19], '%Y-%m-%dT%H:%M:%S')
    rev = data.readline().strip()
    if not date or not tag or not rev:
        raise ParseError
    return (tag, rev, date, '(unknown)')

def getversion_onlinerepo(repo=None):
    """ Retrieve revision number of framework online repository's svnroot """
    url = repo or 'https://git.wikimedia.org/feed/pywikibot/core'
    hsh = None
    try:
        buf = urllib.urlopen(url).readlines()
        hsh = buf[13].split('/')[5][:-1]
    except:
        raise ParseError
    return hsh

## Simple version comparison
#
cmp_ver = lambda a, b, tol=1: {-1: '<', 0: '~', 1: '>'}[cmp((a-b)//tol, 0)]


def getfileversion(filename):
    """ Retrieve revision number of file (__version__ variable containing Id tag)
        without importing it (thus can be done for any file)
    """
    _program_dir = _get_program_dir()
    __version__ = None
    size, mtime = None, None
    fn = os.path.join(_program_dir, filename)
    if os.path.exists(fn):
        for line in open(fn, 'r').readlines():
            if line.find('__version__') == 0:
                exec(line)
                break
        stat  = os.stat(fn)
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(' ')
    if mtime and __version__:
        return u'%s %s %s' % (filename, __version__[5:-1][:7], mtime)
    else:
        return None
