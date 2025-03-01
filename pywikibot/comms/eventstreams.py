"""Server-Sent Events client.

This file is part of the Pywikibot framework.

This module requires requests-sse to be installed::

    pip install "requests-sse>=0.5.0"

.. versionadded:: 3.0
.. versionchanged:: 10.0
   ``requests-sse`` package is required instead of ``sseclient``.
"""
#
# (C) Pywikibot team, 2017-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import json
from datetime import timedelta
from functools import partial
from typing import Any

from requests.packages.urllib3.exceptions import ProtocolError
from requests.packages.urllib3.util.response import httplib

from pywikibot import Site, Timestamp, config, debug, warning
from pywikibot.backports import NoneType
from pywikibot.tools import cached, deprecated_args
from pywikibot.tools.collections import GeneratorWrapper


try:
    from requests_sse import EventSource
except ModuleNotFoundError as e:
    EventSource = e


INSTALL_MSG = """requests-sse is required for EventStreams;
install it with

    pip install "requests-sse>=0.5.0"
"""


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
     'user': ...,
     'wiki': 'wikidatawiki'}
    >>> del stream

    .. versionchanged:: 7.6
       subclassed from :class:`tools.collections.GeneratorWrapper`.
    .. versionchanged:: 10.0
       *retry* value is doubled for each consecutive connect try.
    """

    @deprecated_args(last_id='last_event_id')  # since 10.0.0
    def __init__(self, **kwargs) -> None:
        """Initializer.

        :keyword bool canary: if True, include canary events, see
            https://w.wiki/7$2z for more info.
        :keyword APISite site: a project site object. Used if no *url*
            is given.
        :keyword int retry: Number of milliseconds to wait after disconnects
            before attempting to reconnect. The server may change this
            by including a 'retry' line in a message. Retries are handled
            automatically.

            .. versionchanged:: 10.0
               5 seconds are used instead of 3 seconds as default.

        :keyword pywikibot.Timestamp | str since: a timestamp for older
            events; there will likely be between 7 and 31 days of
            history available but is not guaranteed. It may be given as
            a pywikibot.Timestamp, an ISO 8601 string or a mediawiki
            timestamp string.
        :keyword Iterable[str] | str streams: event stream types.
            Mandatory when no url is given. Multiple streams may be
            given as a string with comma separated stream types or an
            iterable of strings
        :keyword int | float | tuple[int | float, int | float] timeout:
            a timeout value indication how long to wait to send data
            before giving up
        :keyword str url: an url retrieving events from. Will be set up
            to a default url using _site.family settings, stream types
            and timestamp

        :keyword Any last_event_id: [*requests-sse*] If provided, this
            parameter will be sent to the server to tell it to return
            only messages more recent than this ID.
        :keyword requests.Session session: [*requests-sse*] specifies a
            requests.Session, if not, create a default requests.Session.
        :keyword Callable[[], None] on_open: [*requests-sse*] event
            handler for open event
        :keyword Callable[[requests_sse.MessageEvent], None] on_message:
            [*requests-sse*] event handler for message event
        :keyword Callable[[], None] on_error: [*requests-sse*] event
            handler for error event
        :keyword int chunk_size: [*requests*] A maximum size of the chunk
            for chunk-encoded requests.

            .. versionchanged:: 10.0
               None is used instead of 1024 as default value.

        :param kwargs: Other keyword arguments passed to `requests_sse`
            and `requests` library
        :raises ModuleNotFoundError: requests-sse is not installed
        :raises NotImplementedError: no stream types specified

        .. seealso:: https://stream.wikimedia.org/?doc#streams for
           available Wikimedia stream types to be passed with `streams`
           parameter.
        .. note:: *retry* keyword argument is used instead of the
           underlying *reconnection_time* argument which is ignored.
        """
        if isinstance(EventSource, ModuleNotFoundError):
            raise ImportError(INSTALL_MSG) from EventSource

        self.filter = {'all': [], 'any': [], 'none': []}
        self._total: int | None = None
        self._canary = kwargs.pop('canary', False)

        try:
            self._site = kwargs.pop('site')
        except KeyError:  # T335720
            self._site = Site()

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

        retry = kwargs.pop('retry', None)
        if retry:
            kwargs['reconnection_time'] = timedelta(milliseconds=retry)

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
        return '{}({})'.format(type(self).__name__, ', '.join(
            f'{k}={v!r}' for k, v in kwargs.items()))

    @property
    @cached
    def url(self) -> str:
        """Get the EventStream's url.

        :raises NotImplementedError: no stream types specified
        """
        if self._streams is None:
            raise NotImplementedError(
                f'No streams specified for class {type(self).__name__}')
        return '{host}{path}/{streams}{since}'.format(
            host=self._site.eventstreams_host(),
            path=self._site.eventstreams_path(),
            streams=self._streams,
            since=f'?since={self._since}' if self._since else '')

    def set_maximum_items(self, value: int | None) -> None:
        """Set the maximum number of items to be retrieved from the stream.

        If not called, most queries will continue as long as there is
        more data to be retrieved from the stream.

        :param value: The value of maximum number of items to be retrieved
            in total to set.
        """
        if value is not None:
            self._total = int(value)
            debug(f'{type(self).__name__}: Set limit (maximum_items) to '
                  f'{self._total}.')

    def register_filter(self, *args, **kwargs) -> None:
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
            if not callable(func):
                raise TypeError(f'{func} is not a callable')

            self.filter[ftype].append(func)

        # register pairs of keys and items as a filter function
        for key, value in kwargs.items():
            # append function for singletons
            if isinstance(value, (bool, NoneType)):
                self.filter[ftype].append(partial(_is, key=key, value=value))
            # append function for a single value
            elif isinstance(value, (str, int)):
                self.filter[ftype].append(partial(_eq, key=key, value=value))
            # append function for an iterable as value
            else:
                self.filter[ftype].append(partial(_in, key=key, value=value))

    def streamfilter(self, data: dict[str, Any]) -> bool:
        """Filter function for eventstreams.

        See the description of register_filter() how it works.

        :param data: event data dict used by filter functions
        """
        if not self._canary and data.get('meta', {}).get('domain') == 'canary':
            return False  # T266798

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
        while self._total is None or n < self._total:
            if not hasattr(self, 'source'):
                self.source = EventSource(**self.sse_kwargs)
                self.source.connect(config.max_retries)

            try:
                event = next(self.source)
            except (ProtocolError, OSError, httplib.IncompleteRead) as e:
                warning(
                    f'Connection error: {e}.\nTry to re-establish connection.')
                self.source.close()
                del self.source
                if event is not None:
                    self.sse_kwargs['last_event_id'] = event.last_event_id
                continue

            if event.type == 'message':
                if event.data:
                    try:
                        element = json.loads(event.data)
                    except ValueError as e:
                        warning(f'Could not load json data from\n{event}\n{e}')
                    else:
                        if self.streamfilter(element):
                            n += 1
                            yield element
                # else: ignore empty message
            elif event.type == 'error':
                warning(f'Encountered error: {event.data}')
            else:
                warning(f'Unknown event {event.type} occurred.')

        debug(f'{type(self).__name__}: Stopped iterating due to exceeding item'
              ' limit.')

        self.source.close()
        del self.source


def site_rc_listener(site, total: int | None = None):
    """Yield changes received from EventStream.

    :param site: the Pywikibot.Site object to yield live recent changes for
    :type site: Pywikibot.BaseSite
    :param total: the maximum number of changes to return

    :return: pywikibot.comms.eventstream.rc_listener configured for given site
    :raises ModuleNotFoundError: requests-sse installation is required
    """
    if isinstance(EventSource, ModuleNotFoundError):
        raise ModuleNotFoundError(INSTALL_MSG) from EventSource

    stream = EventStreams(streams='recentchange', site=site)
    stream.set_maximum_items(total)
    stream.register_filter(server_name=site.hostname())
    return stream
