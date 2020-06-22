# -*- coding: utf-8 -*-
"""
Server-Sent Events client.

This file is part of the Pywikibot framework.

This module requires sseclient to be installed::

    pip install sseclient
"""
#
# (C) Pywikibot team, 2017-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from distutils.version import LooseVersion
from functools import partial
import json
import socket

from requests import __version__ as requests_version
from requests.packages.urllib3.exceptions import ProtocolError
from requests.packages.urllib3.response import httplib

try:
    from sseclient import SSEClient as EventSource
except ImportError as e:
    EventSource = e

from pywikibot import config, debug, Timestamp, Site, warning
from pywikibot.tools import deprecated_args, StringTypes

if LooseVersion(requests_version) < LooseVersion('2.20.1'):
    raise ImportError(
        'requests >= 2.20.1 is required for EventStreams;\n'
        "install it with 'pip install \"requests>=2.20.1\"'\n")


_logger = 'pywikibot.eventstreams'


class EventStreams(object):

    """Basic EventStreams iterator class for Server-Sent Events (SSE) protocol.

    It provides access to arbitrary streams of data including recent changes.
    It replaces rcstream.py implementation.

    Usage:

    >>> stream = EventStreams(streams='recentchange')
    >>> stream.register_filter(type='edit', wiki='wikidatawiki')
    >>> change = next(iter(stream))
    >>> print('{type} on page {title} by {user}.'.format(**change))
    edit on page Q32857263 by XXN-bot.
    >>> change
    {'comment': '/* wbcreateclaim-create:1| */ [[Property:P31]]: [[Q4167836]]',
     'wiki': 'wikidatawiki', 'type': 'edit', 'server_name': 'www.wikidata.org',
     'server_script_path': '/w', 'namespace': 0, 'title': 'Q32857263',
     'bot': True, 'server_url': 'https://www.wikidata.org',
     'length': {'new': 1223, 'old': 793},
     'meta': {'domain': 'www.wikidata.org', 'partition': 0,
              'uri': 'https://www.wikidata.org/wiki/Q32857263',
              'offset': 288986585, 'topic': 'eqiad.mediawiki.recentchange',
              'request_id': '1305a006-8204-4f51-a27b-0f2df58289f4',
              'schema_uri': 'mediawiki/recentchange/1',
              'dt': '2017-07-13T10:55:31+00:00',
              'id': 'ca13742b-67b9-11e7-935d-141877614a33'},
     'user': 'XXN-bot', 'timestamp': 1499943331, 'patrolled': True,
     'id': 551158959, 'minor': False,
     'revision': {'new': 518751558, 'old': 517180066}}
    >>> del stream
    """

    @deprecated_args(stream='streams')
    def __init__(self, **kwargs):
        """Initializer.

        @keyword site: a project site object. Used when no url is given
        @type site: APISite
        @keyword since: a timestamp for older events; there will likely be
            between 7 and 31 days of history available but is not guaranteed.
            It may be given as a pywikibot.Timestamp, an ISO 8601 string
            or a mediawiki timestamp string.
        @type since: pywikibot.Timestamp or str
        @keyword streams: event stream types. Mandatory when no url is given.
            Multiple streams may be given as a string with comma separated
            stream types or an iterable of strings
            Refer https://stream.wikimedia.org/?doc for available
            wikimedia stream types.
        @type streams: str or iterable
        @keyword timeout: a timeout value indication how long to wait to send
            data before giving up
        @type timeout: int, float or a tuple of two values of int or float
        @keyword url: an url retrieving events from. Will be set up to a
            default url using _site.family settings, stream types and timestamp
        @type url: str
        @param kwargs: keyword arguments passed to SSEClient and requests lib
        @raises ImportError: sseclient is not installed
        @raises NotImplementedError: no stream types specified
        """
        if isinstance(EventSource, Exception):
            raise ImportError('sseclient is required for EventStreams;\n'
                              'install it with "pip install sseclient"\n')
        self.filter = {'all': [], 'any': [], 'none': []}
        self._total = None
        self._site = kwargs.pop('site', Site())

        self._streams = kwargs.pop('streams', None)
        if self._streams and not isinstance(self._streams, StringTypes):
            self._streams = ','.join(self._streams)

        self._since = kwargs.pop('since', None)
        if self._since:
            # assume this is a mw timestamp, convert it to a Timestamp object
            if isinstance(self._streams, StringTypes) \
               and '-' not in self._since:
                self._since = Timestamp.fromtimestampformat(self._since)
            if isinstance(self._streams, Timestamp):
                self._since = self._since.isoformat

        self._url = kwargs.get('url') or self.url
        kwargs.setdefault('url', self._url)
        kwargs.setdefault('timeout', config.socket_timeout)
        self.sse_kwargs = kwargs

    def __repr__(self):
        """Return representation string."""
        kwargs = self.sse_kwargs.copy()
        if self._site != Site():
            kwargs['site'] = self._site
        if self._streams:
            kwargs['streams'] = self._streams
            kwargs.pop('url')
        if self._since:
            kwargs['since'] = self._since
        if kwargs['timeout'] == config.socket_timeout:
            kwargs.pop('timeout')
        return '{0}({1})'.format(self.__class__.__name__, ', '.join(
            '%s=%r' % x for x in kwargs.items()))

    @property
    def url(self):
        """Get the EventStream's url.

        @raises NotImplementedError: no stream types specified
        """
        if not hasattr(self, '_url'):
            if self._streams is None:
                raise NotImplementedError(
                    'No streams specified for class {0}'
                    .format(self.__class__.__name__))
            self._url = ('{host}{path}/{streams}{since}'
                         .format(host=self._site.eventstreams_host(),
                                 path=self._site.eventstreams_path(),
                                 streams=self._streams,
                                 since=('?since=%s' % self._since
                                        if self._since else '')))
        return self._url

    def set_maximum_items(self, value):
        """
        Set the maximum number of items to be retrieved from the stream.

        If not called, most queries will continue as long as there is
        more data to be retrieved from the stream.

        @param value: The value of maximum number of items to be retrieved
            in total to set.
        @type value: int
        """
        if value is not None:
            self._total = int(value)
            debug('{0}: Set limit (maximum_items) to {1}.'
                  .format(self.__class__.__name__, self._total), _logger)

    def register_filter(self, *args, **kwargs):
        """Register a filter.

        Filter types:

        There are 3 types of filter: 'all', 'any' and 'none'.
        The filter type must be given with the keyword argument 'ftype'
        (see below). If no 'ftype' keyword argument is given, 'all' is
        assumed as default.

        You may register multiple filters for each type of filter.
        The behaviour of filter type is as follows::

        - B{'none'}: Skip if the any filter matches. Otherwise check 'all'.
        - B{'all'}: Skip if not all filter matches. Otherwise check 'any':
        - B{'any'}: Skip if no given filter matches. Otherwise pass.

        Filter functions:

        Filter may be specified as external function methods given as
        positional argument like::

            def foo(data):
                return True

            register_filter(foo, ftype='any')

        The data dict from event is passed to the external filter function as
        a parameter and that method must handle it in a proper way and return
        C{True} if the filter matches and C{False} otherwise.

        Filter keys and values:

        Another method to register a filter is to pass pairs of keys and values
        as keyword arguments to this method. The key must be a key of the event
        data dict and the value must be any value or an iterable of values the
        C{data['key']} may match or be part of it. Samples::

            register_filter(server_name='de.wikipedia.org')  # 1
            register_filter(type=('edit', 'log'))  # 2
            register_filter(ftype='none', bot=True)  # 3

        Explanation for the result of the filter function:
        1. C{return data['sever_name'] == 'de.wikipedia.org'}
        2. C{return data['type'] in ('edit', 'log')}
        3. C{return data['bot'] is True}

        @keyword ftype: The filter type, one of 'all', 'any', 'none'.
            Default value is 'all'
        @type ftype: str
        @param args: You may pass your own filter functions here.
            Every function should be able to handle the data dict from events.
        @type args: callable
        @param kwargs: Any key returned by event data with a event data value
            for this given key.
        @type kwargs: str, list, tuple or other sequence
        @raise TypeError: A given args parameter is not a callable.
        """
        def _is(data, key=None, value=None):
            return key in data and data[key] is value

        def _eq(data, key=None, value=None):
            return key in data and data[key] == value

        def _in(data, key=None, value=None):
            return key in data and data[key] in value

        ftype = kwargs.pop('ftype', 'all')  # set default ftype value

        # register an external filter function
        for func in args:
            if callable(func):
                self.filter[ftype].append(func)
            else:
                raise TypeError('{0} is not a callable'.format(func))

        # register pairs of keys and items as a filter function
        for key, value in kwargs.items():
            # append function for singletons
            if isinstance(value, (bool, type(None))):
                self.filter[ftype].append(partial(_is, key=key, value=value))
            # append function for a single value
            elif isinstance(value, (StringTypes, int)):
                self.filter[ftype].append(partial(_eq, key=key, value=value))
            # append function for an iterable as value
            else:
                self.filter[ftype].append(partial(_in, key=key, value=value))

    def streamfilter(self, data):
        """Filter function for eventstreams.

        See the description of register_filter() how it works.

        @param data: event data dict used by filter functions
        @type data: dict
        """
        if any(function(data) for function in self.filter['none']):
            return False
        if not all(function(data) for function in self.filter['all']):
            return False
        if not self.filter['any']:
            return True
        return any(function(data) for function in self.filter['any'])

    def __iter__(self):
        """Iterator."""
        n = 0
        event = None
        ignore_first_empty_warning = True
        while self._total is None or n < self._total:
            if not hasattr(self, 'source'):
                self.source = EventSource(**self.sse_kwargs)
                # sseclient >= 0.0.18 is required for eventstreams (T184713)
                # we don't have a version string inside but the instance
                # variable 'chunk_size' was newly introduced with 0.0.18
                if not hasattr(self.source, 'chunk_size'):
                    warning(
                        'You may not have the right sseclient version;\n'
                        'sseclient >= 0.0.18 is required for eventstreams.\n'
                        "Install it with 'pip install \"sseclient>=0.0.18\"'")
            try:
                event = next(self.source)
            except (ProtocolError, socket.error, httplib.IncompleteRead) as e:
                warning('Connection error: {0}.\n'
                        'Try to re-establish connection.'.format(e))
                del self.source
                if event is not None:
                    self.sse_kwargs['last_id'] = event.id
                continue
            if event.event == 'message':
                if event.data:
                    try:
                        element = json.loads(event.data)
                    except ValueError as e:
                        warning('Could not load json data from\n{0}\n{1}'
                                .format(event, e))
                    else:
                        if self.streamfilter(element):
                            n += 1
                            yield element
                elif not ignore_first_empty_warning:
                    warning('Empty message found.')
                else:
                    ignore_first_empty_warning = False
            elif event.event == 'error':
                warning('Encountered error: {0}'.format(event.data))
            else:
                warning('Unknown event {0} occurred.'.format(event.event))
        else:
            debug('{0}: Stopped iterating due to '
                  'exceeding item limit.'
                  .format(self.__class__.__name__), _logger)
        del self.source


def site_rc_listener(site, total=None):
    """Yield changes received from EventStream.

    @param site: the Pywikibot.Site object to yield live recent changes for
    @type site: Pywikibot.BaseSite
    @param total: the maximum number of changes to return
    @type total: int

    @return: pywikibot.comms.eventstream.rc_listener configured for given site
    @raises ImportError: sseclient installation is required
    """
    if isinstance(EventSource, Exception):
        raise ImportError('sseclient is required for EventStreams;\n'
                          'install it with "pip install sseclient"\n')

    stream = EventStreams(streams='recentchange', site=site)
    stream.set_maximum_items(total)
    stream.register_filter(server_name=site.hostname())
    return stream
