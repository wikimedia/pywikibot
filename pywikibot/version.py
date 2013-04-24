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
import time
import urllib

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
    data = getversiondict()
    try:
        rev2 = int(getversion_onlinerepo())
        rev1 = int(str(data['rev']).split()[0])
        data['cmp_ver'] = 'OUTDATED' if rev1 < rev2 else 'ok'
    except Exception:
        data['cmp_ver'] = 'n/a'
    return '%(tag)s (r%(rev)s, %(date)s, %(cmp_ver)s)' % data

def getversiondict():
    global cache
    if cache:
      return cache
    try:
        (tag, rev, date) = getversion_svn()
    except Exception:
        try:
            (tag, rev, date) = getversion_nightly()
        except Exception:
            try:
                version = getfileversion('pywikibot/__init__.py')
                if not version:
                    # fall-back in case everything breaks (should not be used)
                    import pywikibot
                    version = pywikibot.__version__

                id, file, rev, date, ts, author, dollar = version.split(' ')
                tag = 'pywikibot/__init__.py'
                date = time.strptime('%sT%s' % (date, ts), '%Y-%m-%dT%H:%M:%SZ')
            except: # nothing worked; version unknown (but suppress exceptions)
                # the value is most likely '$Id' + '$', it means that
                # wikipedia.py got imported without using svn at all
                return dict(tag='', rev='-1 (unknown)', date='0 (unknown)')

    datestring = time.strftime('%Y/%m/%d, %H:%M:%S', date)
    cache = dict(tag=tag, rev=rev, date=datestring)
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
        cur.execute( '''select local_relpath, repos_path, revision, changed_date from nodes order by revision desc, changed_date desc''')
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
        date = time.strptime(entries.readline()[:19],'%Y-%m-%dT%H:%M:%S')
        rev = entries.readline()[:-1]
        entries.close()
    if (not date or not tag or not rev) and not path:
        raise ParseError
    return (tag, rev, date)

def getversion_nightly():
    data = open(os.path.join(wikipediatools.get_base_dir(), 'version'))
    tag = data.readline().strip()
    date = time.strptime(data.readline()[:19],'%Y-%m-%dT%H:%M:%S')
    rev = data.readline().strip()
    if not date or not tag or not rev:
        raise ParseError
    return (tag, rev, date)

## Retrieve revision number of framework online repository's svnroot
#
def getversion_onlinerepo(repo=None):
    url = repo or 'http://svn.wikimedia.org/svnroot/pywikipedia/trunk/pywikipedia/'
    rev = None
    try:
        buf = urllib.urlopen(url).read()
        rev = buf.split(' ')[3][:-1]
    except:
        raise ParseError
    return rev

## Simple version comparison
#
cmp_ver = lambda a, b, tol=1: {-1: '<', 0: '~', 1: '>'}[cmp((a-b)//tol, 0)]

## Retrieve revision number of file (__version__ variable containing Id tag)
#  without importing it (thus can be done for any file)
#
def getfileversion(filename):
    _program_dir = _get_program_dir()
    __version__ = None
    fn = os.path.join(_program_dir, filename)
    if os.path.exists(fn):
        for line in open(fn, 'r').readlines():
            if line.find('__version__') == 0:
                exec(line)
                break
    return __version__
