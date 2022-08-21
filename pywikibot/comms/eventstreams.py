"""
Server-Sent Events client.

This file is part of the Pywikibot framework.

This module requires sseclient to be installed::

    pip install "sseclient<0.0.23,>=0.0.18"

.. versionadded:: 3.0
"""
#
# (C) Pywikibot team, 2017-2022
#
# Distributed under the terms of the MIT license.
#
import json
from functools import partial
from typing import Optional

from pkg_resources import parse_version
from requests import __version__ as requests_version
from requests.packages.urllib3.exceptions import ProtocolError
from requests.packages.urllib3.util.response import httplib

from pywikibot import Site, Timestamp, config, debug, warning
from pywikibot.tools import cached
from pywikibot.tools.collections import GeneratorWrapper


try:
    from sseclient import SSEClient as EventSource
except ImportError as e:
    EventSource = e


if parse_version(requests_version) < parse_version('2.20.1'):
    raise ImportError(
        'requests >= 2.20.1 is required for EventStreams;\n'
        "install it with 'pip install \"requests>=2.20.1\"'\n")


class EventStreams(GeneratorWrapper):

    """Generator class for Server-Sent Events (SSE) protocol.

    It provides access to arbitrary streams of data including recent changes.

    Usage:

    >>> stream = EventStreams(streams='recentchange')
    >>> stream.register_filter(type='edit', wiki='wikidatawiki', bot=True)
    >>> change = next(stream)
    >>> msg = '{type} on page {title} by {user}.'.format_map(change)
    >>> print(msg)  # doctest: +SKIP
    edit on page Q2190037 by KrBot.
    >>> from pprint import pprint
    >>> pprint(change, width=75)  # doctest: +SKIP
    {'$schema': '/mediawiki/recentchange/1.0.0',
     'bot': True,
     'comment': '/* wbsetreference-set:2| */ [[Property:P10585]]: 96FPN, см. '
                '/ see [[Template:Autofix|autofix]] на / on [[Property '
                'talk:P356]]',
     'id': 1728475074,
     'length': {'new': 8871, 'old': 8871},
     'meta': {'domain': 'www.wikidata.org',
              'dt': '2022-07-12T17:54:15Z',
              'id': '2cdec62f-a2b3-49b8-9a52-85a42236fb99',
              'offset': 4000957901,
              'partition': 0,
              'request_id': 'f7896e77-fd2b-4a95-a9e4-44c1e3ad818b',
              'stream': 'mediawiki.recentchange',
              'topic': 'eqiad.mediawiki.recentchange',
              'uri': 'https://www.wikidata.org/wiki/Q2190037'},
     'minor': False,
     'namespace': 0,
     'parsedcomment': '\u200e<span dir="auto"><span '
                      'class="autocomment">Изменена ссылка на заявление: '
                      '</span></span> <a href="/wiki/Property:P10585" '
                      'title="Property:P10585">Property:P10585</a>: 96FPN, '
                      'см. / see <a href="/wiki/Template:Autofix" '
                      'title="Template:Autofix">autofix</a> на / on <a '
                      'href="/wiki/Property_talk:P356" title="Property '
                      'talk:P356">Property talk:P356</a>',
     'patrolled': True,
     'revision': {'new': 1676015019, 'old': 1675697125},
     'server_name': 'www.wikidata.org',
     'server_script_path': '/w',
     'server_url': 'https://www.wikidata.org',
     'timestamp': 1657648455,
     'title': 'Q2190037',
     'type': 'edit',
     'user': 'KrBot',
     'wiki': 'wikidatawiki'}
    >>> pprint(next(stream), width=75)  # doctest: +ELLIPSIS
    {'$schema': '/mediawiki/recentchange/1.0.0',
     'bot': True,
     ...
     'server_name': 'www.wikidata.org',
     'server_script_path': '/w',
     'server_url': 'https://www.wikidata.org',
     ...
     'type': 'edit',
     'user': '...',
     'wiki': 'wikidatawiki'}
    >>> del stream

    .. versionchanged:: 7.6
       subclassed from :class:`tools.collections.GeneratorWrapper`
    """

    def __init__(self, **kwargs) -> None:
        """Initializer.

        :keyword APISite site: a project site object. Used if no url is
            given
        :keyword pywikibot.Timestamp or str since: a timestamp for older
            events; there will likely be between 7 and 31 days of
            history available but is not guaranteed. It may be given as
            a pywikibot.Timestamp, an ISO 8601 string or a mediawiki
            timestamp string.
        :keyword Iterable[str] or str streams: event stream types.
            Mandatory when no url is given. Multiple streams may be
            given as a string with comma separated stream types or an
            iterable of strings
        :keyword int or float or Tuple[int or float, int or float] timeout:
            a timeout value indication how long to wait to send data
            before giving up
        :keyword str url: an url retrieving events from. Will be set up
            to a default url using _site.family settings, stream types
            and timestamp
        :param kwargs: keyword arguments passed to `SSEClient` and
            `requests` library
        :raises ImportError: sseclient is not installed
        :raises NotImplementedError: no stream types specified

        .. seealso:: https://stream.wikimedia.org/?doc#streams for
           available Wikimedia stream types to be passed with `streams`
           parameter.
        """
        if isinstance(EventSource, Exception):
            raise ImportError('sseclient is required for EventStreams;\n'
                              'install it with "pip install sseclient"\n')
        self.filter = {'all': [], 'any': [], 'none': []}
        self._total = None
        self._site = kwargs.pop('site', Site())

        self._streams = kwargs.pop('streams', None)
        if self._streams and not isinstance(self._streams, str):
            self._streams = ','.join(self._streams)

        self._since = kwargs.pop('since', None)
        if self._since:
            # assume this is a mw timestamp, convert it to a Timestamp object
            if isinstance(self._since, str) and '-' not in self._since:
                self._since = Timestamp.fromtimestampformat(self._since)
            if isinstance(self._since, Timestamp):
                self._since = self._since.isoformat()

        self._url = kwargs.get('url') or self.url
        kwargs.setdefault('url', self._url)
        kwargs.setdefault('timeout', config.socket_timeout)
        self.sse_kwargs = kwargs

    def __repr__(self) -> str:
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
        return '{}({})'.format(self.__class__.__name__, ', '.join(
            '{}={!r}'.format(k, v) for k, v in kwargs.items()))

    @property
    @cached
    def url(self):
        """Get the EventStream's url.

        :raises NotImplementedError: no stream types specified
        """
        if self._streams is None:
            raise NotImplementedError('No streams specified for class {}'
                                      .format(self.__class__.__name__))
        return '{host}{path}/{streams}{since}'.format(
            host=self._site.eventstreams_host(),
            path=self._site.eventstreams_path(),
            streams=self._streams,
            since='?since={}'.format(self._since) if self._since else '')

    def set_maximum_items(self, value: int) -> None:
        """
        Set the maximum number of items to be retrieved from the stream.

        If not called, most queries will continue as long as there is
        more data to be retrieved from the stream.

        :param value: The value of maximum number of items to be retrieved
            in total to set.
        """
        if value is not None:
            self._total = int(value)
            debug('{}: Set limit (maximum_items) to {}.'
                  .format(self.__class__.__name__, self._total))

    def register_filter(self, *args, **kwargs):
        """Register a filter.

        Filter types:

        There are 3 types of filter: 'all', 'any' and 'none'.
        The filter type must be given with the keyword argument 'ftype'
        (see below). If no 'ftype' keyword argument is given, 'all' is
        assumed as default.

        You may register multiple filters for each type of filter.
        The behaviour of filter type is as follows:

        - **'none'**: Skip if the any filter matches. Otherwise check 'all'.
        - **'all'**: Skip if not all filter matches. Otherwise check 'any':
        - **'any'**: Skip if no given filter matches. Otherwise pass.

        Filter functions:

        Filter may be specified as external function methods given as
        positional argument like::

            def foo(data):
                return True

            register_filter(foo, ftype='any')

        The data dict from event is passed to the external filter function as
        a parameter and that method must handle it in a proper way and return
        ``True`` if the filter matches and ``False`` otherwise.

        Filter keys and values:

        Another method to register a filter is to pass pairs of keys and values
        as keyword arguments to this method. The key must be a key of the event
        data dict and the value must be any value or an iterable of values the
        ``data['key']`` may match or be part of it. Samples::

            register_filter(server_name='de.wikipedia.org')  # 1
            register_filter(type=('edit', 'log'))  # 2
            register_filter(ftype='none', bot=True)  # 3

        Explanation for the result of the filter function:
        1. ``return data['sever_name'] == 'de.wikipedia.org'``
        2. ``return data['type'] in ('edit', 'log')``
        3. ``return data['bot'] is True``

        :keyword ftype: The filter type, one of 'all', 'any', 'none'.
            Default value is 'all'
        :type ftype: str
        :param args: You may pass your own filter functions here.
            Every function should be able to handle the data dict from events.
        :type args: callable
        :param kwargs: Any key returned by event data with an event data value
            for this given key.
        :type kwargs: str, list, tuple or other sequence
        :raise TypeError: A given args parameter is not a callable.
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
                raise TypeError('{} is not a callable'.format(func))

        # register pairs of keys and items as a filter function
        for key, value in kwargs.items():
            # append function for singletons
            if isinstance(value, (bool, type(None))):
                self.filter[ftype].append(partial(_is, key=key, value=value))
            # append function for a single value
            elif isinstance(value, (str, int)):
                self.filter[ftype].append(partial(_eq, key=key, value=value))
            # append function for an iterable as value
            else:
                self.filter[ftype].append(partial(_in, key=key, value=value))

    def streamfilter(self, data: dict):
        """Filter function for eventstreams.

        See the description of register_filter() how it works.

        :param data: event data dict used by filter functions
        """
        if any(function(data) for function in self.filter['none']):
            return False
        if not all(function(data) for function in self.filter['all']):
            return False
        if not self.filter['any']:
            return True
        return any(function(data) for function in self.filter['any'])

    @property
    def generator(self):
        """Inner generator.

        .. versionchanged:: 7.6
           changed from iterator method to generator property
        """
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
            except (ProtocolError, OSError, httplib.IncompleteRead) as e:
                warning('Connection error: {}.\n'
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
                        warning('Could not load json data from\n{}\n{}'
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
                warning('Encountered error: {}'.format(event.data))
            else:
                warning('Unknown event {} occurred.'.format(event.event))

        debug('{}: Stopped iterating due to exceeding item limit.'
              .format(self.__class__.__name__))
        del self.source


def site_rc_listener(site, total: Optional[int] = None):
    """Yield changes received from EventStream.

    :param site: the Pywikibot.Site object to yield live recent changes for
    :type site: Pywikibot.BaseSite
    :param total: the maximum number of changes to return

    :return: pywikibot.comms.eventstream.rc_listener configured for given site
    :raises ImportError: sseclient installation is required
    """
    if isinstance(EventSource, Exception):
        raise ImportError('sseclient is required for EventStreams;\n'
                          'install it with "pip install sseclient"\n')

    stream = EventStreams(streams='recentchange', site=site)
    stream.set_maximum_items(total)
    stream.register_filter(server_name=site.hostname())
    return stream
