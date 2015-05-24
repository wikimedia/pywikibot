# -*- coding: utf-8  -*-
"""Objects representing WikidataQuery query syntax and API."""
#
# (C) Pywikibot team, 2013
#
# Distributed under the terms of the MIT license.
from __future__ import unicode_literals

import json
import sys
if sys.version_info[0] > 2:
    from urllib.parse import quote
    basestring = (str, )
else:
    from urllib2 import quote
import pickle
import os
import hashlib
import time
import tempfile

import pywikibot
from pywikibot.comms import http
from pywikibot.page import ItemPage, PropertyPage, Claim
from pywikibot import config


def listify(x):
    """
    If given a non-list, encapsulate in a single-element list.

    @rtype: list
    """
    return x if isinstance(x, list) else [x]


class QuerySet():

    """
    A QuerySet represents a set of queries or other query sets.

    Queries may be joined by operators (AND and OR).

    A QuerySet stores this information as a list of Query(Sets) and
    a joiner operator to join them all together
    """

    def __init__(self, q):
        """
        Initialise a query set from a Query or another QuerySet.

        @type q: Query or QuerySet
        """
        self.qs = [q]

    def addJoiner(self, args, joiner):
        """
        Add to this QuerySet using the given joiner.

        If the given joiner is not the same as we used before in
        this QuerySet, nest the current one in parens before joining.
        This makes the implicit grouping of the API explicit.

        @return: a new query set representing the joining of this one and
            the arguments
        """
        if len(self.qs) > 1 and joiner != self.joiner:
            left = QuerySet(self)
        else:
            left = self

        left.joiner = joiner

        for a in listify(args):
            left.qs.append(a)

        return left

    def AND(self, args):
        """
        Add the given args (Queries or QuerySets) to the Query set as a logical conjuction (AND).

        @type args: Query or QuerySet
        """
        return self.addJoiner(args, "AND")

    def OR(self, args):
        """
        Add the given args (Queries or QuerySets) to the Query set as a logical disjunction (OR).

        @type args: Query or QuerySet
        """
        return self.addJoiner(args, "OR")

    def __str__(self):
        """
        Output as an API-ready string.

        @rtype: str
        """
        def bracketIfQuerySet(q):
            if isinstance(q, QuerySet) and q.joiner != self.joiner:
                return "(%s)" % q
            else:
                return str(q)

        s = bracketIfQuerySet(self.qs[0])

        for q in self.qs[1:]:
            s += " %s %s" % (self.joiner, bracketIfQuerySet(q))

        return s

    def __repr__(self):
        return u"QuerySet(%s)" % self


class Query():

    """
    A query is a single query for the WikidataQuery API.

    For example:
    claim[100:60] or link[enwiki]

    Construction of a Query can throw a TypeError if you feed it bad
    parameters. Exactly what these need to be depends on the Query
    """

    def AND(self, ands):
        """
        Produce a query set ANDing this query and all the given query/sets.

        @type ands: Query or list of Query
        """
        return QuerySet(self).addJoiner(ands, "AND")

    def OR(self, ors):
        """
        Produce a query set ORing this query and all the given query/sets.

        @type ors: Query or list of Query
        """
        return QuerySet(self).addJoiner(ors, "OR")

    def formatItem(self, item):
        """
        Default item formatting is string.

        This will work for queries, querysets, ints and strings
        """
        return str(item)

    def formatList(self, l):
        """
        Format and comma-join a list.

        @type l: list
        """
        return ",".join([self.formatItem(x) for x in l])

    @staticmethod
    def isOrContainsOnlyTypes(items, types):
        """
        Either this item is one of the given types, or it is a list of only those types.

        @rtype: bool
        """
        if isinstance(items, list):
            for x in items:
                found = False
                for typ in listify(types):
                    if isinstance(x, typ):
                        found = True
                        break

                if not found:
                    return False
        else:
            for typ in listify(types):
                found = False
                if isinstance(items, typ):
                    found = True
                    break

            if not found:
                return False

        return True

    def validate(self):
        """
        Validate the query parameters.

        Default validate result is a pass - subclasses need to implement
        this if they want to check their parameters.

        @return: True
        @rtype: bool
        """
        return True

    def validateOrRaise(self, msg=None):
        if not self.validate():
            raise TypeError(msg)

    def convertWDType(self, item):
        """
        Convert Wikibase items like ItemPage or PropertyPage into integer IDs.

        The resulting IDs may be used in query strings.

        @param item: A single item. One of ItemPages, PropertyPages, int
            or anything that can be fed to int()

        @return: the int ID of the item
        """
        if isinstance(item, ItemPage) or isinstance(item, PropertyPage):
            return item.getID(numeric=True)
        else:
            return int(item)

    def convertWDTypes(self, items):
        return [self.convertWDType(x) for x in listify(items)]

    def __str__(self):
        """
        Generate a query string to be passed to the WDQ API.

        Sub-classes must override this method.

        @raise NotImplementedError: Always raised by this abstract method
        """
        raise NotImplementedError

    def __repr__(self):
        return u"Query(%s)" % self


class HasClaim(Query):

    """
    This is a Query of the form "claim[prop:val]".

    It is subclassed by
    the other similar forms like noclaim and string
    """

    queryType = "claim"

    def __init__(self, prop, items=[]):
        """Constructor."""
        self.prop = self.convertWDType(prop)

        if isinstance(items, Query):
            self.items = items
        elif isinstance(self, StringClaim):
            self.items = listify(items)
        else:
            self.items = self.convertWDTypes(items)

        self.validateOrRaise()

    def formatItems(self):
        res = ''
        if self.items:
            res += ":" + ",".join([self.formatItem(x) for x in self.items])

        return res

    def validate(self):
        return self.isOrContainsOnlyTypes(self.items, [int, Query])

    def __str__(self):
        if isinstance(self.items, list):
            return "%s[%s%s]" % (self.queryType, self.prop, self.formatItems())
        elif isinstance(self.items, Query):
            return "%s[%s:(%s)]" % (self.queryType, self.prop, self.items)


class NoClaim(HasClaim):

    """Query of the form noclaim[PROPERTY]."""

    queryType = "noclaim"


class StringClaim(HasClaim):

    """Query of the form string[PROPERTY:"STRING",...]."""

    queryType = "string"

    def formatItem(self, x):
        """Add quotes around string."""
        return '"%s"' % x

    def validate(self):
        return self.isOrContainsOnlyTypes(self.items, basestring)


class Tree(Query):

    """Query of the form tree[ITEM,...][PROPERTY,...]<PROPERTY,...>."""

    queryType = "tree"

    def __init__(self, item, forward=[], reverse=[]):
        """
        Constructor.

        @param item: The root item
        @param forward: List of forward properties, can be empty
        @param reverse: List of reverse properties, can be empty
        """
        # check sensible things coming in, as we lose info once we do
        # type conversion
        if not self.isOrContainsOnlyTypes(item, [int, ItemPage]):
            raise TypeError("The item paramter must contain or be integer IDs "
                            "or page.ItemPages")
        elif (not self.isOrContainsOnlyTypes(forward, [int, PropertyPage]) or
                not self.isOrContainsOnlyTypes(reverse, [int, PropertyPage])):
            raise TypeError("The forward and reverse parameters must contain "
                            "or be integer IDs or page.PropertyPages")

        self.item = self.convertWDTypes(item)
        self.forward = self.convertWDTypes(forward)
        self.reverse = self.convertWDTypes(reverse)

        self.validateOrRaise()

    def validate(self):
        return (self.isOrContainsOnlyTypes(self.item, int) and
                        self.isOrContainsOnlyTypes(self.forward, int) and
                        self.isOrContainsOnlyTypes(self.reverse, int))

    def __str__(self):
        return "%s[%s][%s][%s]" % (self.queryType, self.formatList(self.item),
                                    self.formatList(self.forward),
                                    self.formatList(self.reverse))


class Around(Query):

    """A query in the form around[PROPERTY,LATITUDE,LONGITUDE,RADIUS]."""

    queryType = "around"

    def __init__(self, prop, coord, rad):
        """Constructor."""
        self.prop = self.convertWDType(prop)
        self.lt = coord.lat
        self.lg = coord.lon
        self.rad = rad

    def validate(self):
        return isinstance(self.prop, int)

    def __str__(self):
        return "%s[%s,%s,%s,%s]" % (self.queryType, self.prop,
                                    self.lt, self.lg, self.rad)


class Between(Query):

    """
    A query in the form between[PROP, BEGIN, END].

    You have to give prop and one of begin or end. Note that times have
    to be in UTC, timezones are not supported by the API

    @param prop: the property
    @param begin: WbTime object representing the beginning of the period
    @param end: WbTime object representing the end of the period
    """

    queryType = "between"

    def __init__(self, prop, begin=None, end=None):
        """Constructor."""
        self.prop = self.convertWDType(prop)
        self.begin = begin
        self.end = end

    def validate(self):
        return (self.begin or self.end) and isinstance(self.prop, int)

    def __str__(self):
        begin = self.begin.toTimestr() if self.begin else ''

        # if you don't have an end, you don't put in the comma
        end = ',' + self.end.toTimestr() if self.end else ''

        return "%s[%s,%s%s]" % (self.queryType, self.prop, begin, end)


class Link(Query):

    """
    A query in the form link[LINK,...], which also includes nolink.

    All link elements have to be strings, or validation will throw
    """

    queryType = "link"

    def __init__(self, link):
        """Constructor."""
        self.link = listify(link)
        self.validateOrRaise()

    def validate(self):
        return self.isOrContainsOnlyTypes(self.link, basestring)

    def __str__(self):
        return "%s[%s]" % (self.queryType, self.formatList(self.link))


class NoLink(Link):

    """A query in the form nolink[..]."""

    queryType = "nolink"


def fromClaim(claim):
    """
    Construct from a pywikibot.page Claim object.

    @type claim: L{pywikibot.page.Claim}
    @rtype: L{Query}
    """
    if not isinstance(claim, Claim):
        raise TypeError("claim must be a page.Claim")

    if claim.type == 'wikibase-item':
        return HasClaim(claim.getID(numeric=True), claim.getTarget().getID(numeric=True))
    if claim.type == 'string':
        return StringClaim(claim.getID(numeric=True), claim.getTarget())
    else:
        raise TypeError("Cannot construct a query from a claim of type %s"
                        % claim.type)


class WikidataQuery():

    """
    An interface to the WikidataQuery API.

    Default host is
    https://wdq.wmflabs.org/, but you can substitute
    a different one.

    Caching defaults to a subdir of the system temp directory with a
    1 hour max cache age.

    Set a zero or negative maxCacheAge to disable caching
    """

    def __init__(self, host="https://wdq.wmflabs.org", cacheDir=None,
                    cacheMaxAge=60):
        """Constructor."""
        self.host = host
        self.cacheMaxAge = cacheMaxAge

        if cacheDir:
            self.cacheDir = cacheDir
        else:
            self.cacheDir = os.path.join(tempfile.gettempdir(),
                                            "wikidataquery_cache")

    def getUrl(self, queryStr):
        return "%s/api?%s" % (self.host, queryStr)

    def getQueryString(self, q, labels=[], props=[]):
        """
        Get the query string for a given query or queryset.

        @return: string including labels and props
        """
        qStr = "q=%s" % quote(str(q))

        if labels:
            qStr += "&labels=%s" % ','.join(labels)

        if props:
            qStr += "&props=%s" % ','.join(props)

        return qStr

    def getCacheFilename(self, queryStr):
        """
        Encode a query into a unique and universally safe format.

        @rtype: unicode
        """
        encQuery = hashlib.sha1(queryStr.encode('utf8')).hexdigest() + ".wdq_cache"
        return os.path.join(self.cacheDir, encQuery)

    def readFromCache(self, queryStr):
        """
        Load the query result from the cache, if possible.

        @return: None if the data is not there or if it is too old.
        """
        if self.cacheMaxAge <= 0:
            return None

        cacheFile = self.getCacheFilename(queryStr)

        if os.path.isfile(cacheFile):
            mtime = os.path.getmtime(cacheFile)
            now = time.time()

            if ((now - mtime) / 60) < self.cacheMaxAge:
                with open(cacheFile, 'rb') as f:
                    try:
                        data = pickle.load(f)
                    except pickle.UnpicklingError:
                        pywikibot.warning(u"Couldn't read cached data from %s"
                                            % cacheFile)
                        data = None

                return data

        return None

    def saveToCache(self, q, data):
        """
        Save data from a query to a cache file, if enabled.

        @rtype: None
        """
        if self.cacheMaxAge <= 0:
            return

        # we have to use our own query string, as otherwise we may
        # be able to find the cache file again if there are e.g.
        # whitespace differences
        cacheFile = self.getCacheFilename(q)

        if os.path.exists(cacheFile) and not os.path.isfile(cacheFile):
            return

        if not os.path.exists(self.cacheDir):
            os.makedirs(self.cacheDir)

        with open(cacheFile, 'wb') as f:
            try:
                pickle.dump(data, f, protocol=config.pickle_protocol)
            except IOError:
                pywikibot.warning(u"Failed to write cache file %s" % cacheFile)

    def getDataFromHost(self, queryStr):
        """
        Go and fetch a query from the host's API.

        @rtype: dict
        """
        url = self.getUrl(queryStr)

        try:
            resp = http.fetch(url)
        except:
            pywikibot.warning(u"Failed to retrieve %s" % url)
            raise

        try:
            data = json.loads(resp.content)
        except ValueError:
            pywikibot.warning(u"Data received from host but no JSON could be decoded")
            raise pywikibot.ServerError("Data received from host but no JSON could be decoded")

        return data

    def query(self, q, labels=[], props=[]):
        """
        Actually run a query over the API.

        @return: dict of the interpreted JSON or None on failure
        """
        fullQueryString = self.getQueryString(q, labels, props)

        # try to get cached data first
        data = self.readFromCache(fullQueryString)

        if data:
            return data

        # the cached data must not be OK, go and get real data from the
        # host's API
        data = self.getDataFromHost(fullQueryString)

        # no JSON found
        if not data:
            return None

        # cache data for next time
        self.saveToCache(fullQueryString, data)

        return data
