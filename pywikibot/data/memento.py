"""Fix ups for memento-client package version 0.6.1.

.. versionadded:: 7.4
.. seealso:: https://github.com/mementoweb/py-memento-client#readme
"""
#
# (C) Shawn M. Jones, Harihar Shankar, Herbert Van de Sompel.
#     -- Los Alamos National Laboratory, 2013
# Parts of MementoClient class codes are
# licensed under the BSD open source software license.
#
# (C) Pywikibot team, 2015-2023
#
# Distributed under the terms of the MIT license.
#
from datetime import datetime
from typing import Optional

import requests
from memento_client.memento_client import MementoClient as OldMementoClient
from memento_client.memento_client import MementoClientException
from requests.exceptions import InvalidSchema, MissingSchema

from pywikibot import config, debug, sleep, warning


__all__ = (
    'MementoClient',
    'MementoClientException',
    'get_closest_memento_url',
)


class MementoClient(OldMementoClient):

    """A Memento Client.

    It makes it straightforward to access the Web of the past as it is
    to access the current Web.

    .. versionchanged:: 7.4
       `timeout` is used in several methods.

    Basic usage:

    >>> mc = MementoClient()
    >>> dt = mc.convert_to_datetime("Sun, 01 Apr 2010 12:00:00 GMT")
    >>> mi = mc.get_memento_info("http://www.bbc.com/", dt, timeout=60)
    >>> mi['original_uri']
    'http://www.bbc.com/'
    >>> mi['timegate_uri']
    'http://timetravel.mementoweb.org/timegate/http://www.bbc.com/'
    >>> sorted(mi['mementos'])
    ['closest', 'first', 'last', 'next', 'prev']
    >>> from pprint import pprint
    >>> pprint(mi['mementos'])
    {'closest': {'datetime': datetime.datetime(2010, 5, 23, 10, 19, 6),
                 'http_status_code': 200,
                 'uri': ['https://web.archive.org/web/20100523101906/http://www.bbc.co.uk/']},
     'first': {'datetime': datetime.datetime(1998, 12, 2, 21, 26, 10),
               'uri': ['http://wayback.nli.org.il:8080/19981202212610/http://www.bbc.com/']},
     'last': {'datetime': datetime.datetime(2022, 7, 31, 3, 30, 53),
              'uri': ['http://archive.md/20220731033053/http://www.bbc.com/']},
     'next': {'datetime': datetime.datetime(2010, 6, 2, 17, 29, 9),
              'uri': ['http://wayback.archive-it.org/all/20100602172909/http://www.bbc.com/']},
     'prev': {'datetime': datetime.datetime(2009, 10, 15, 19, 7, 5),
              'uri': ['http://wayback.nli.org.il:8080/20091015190705/http://www.bbc.com/']}}

    The output conforms to the Memento API format explained here:
    http://timetravel.mementoweb.org/guide/api/#memento-json

    .. note:: The mementos result is not deterministic. It may be
       different for the same parameters.

    By default, MementoClient uses the Memento Aggregator:
    http://mementoweb.org/depot/

    It is also possible to use different TimeGate, simply initialize
    with a preferred timegate base uri. Toggle check_native_timegate to
    see if the original uri has its own timegate. The native timegate,
    if found will be used instead of the timegate_uri preferred. If no
    native timegate is found, the preferred timegate_uri will be used.

    :param str timegate_uri: A valid HTTP base uri for a timegate.
        Must start with http(s):// and end with a /.
    :param int max_redirects: the maximum number of redirects allowed
        for all HTTP requests to be made.
    :return: A :class:`MementoClient` obj.
    """  # noqa: E501

    def __init__(self, *args, **kwargs):
        """Initializer."""
        # To prevent documentation inclusion from inherited class
        # because it is malformed.
        super().__init__(*args, **kwargs)

    def get_memento_info(self, request_uri: str,
                         accept_datetime: Optional[datetime] = None,
                         timeout: Optional[int] = None,
                         **kwargs) -> dict:
        """Query the preferred timegate and return the closest memento uri.

        Given an original uri and an accept datetime, this method
        queries the preferred timegate and returns the closest memento
        uri, along with prev/next/first/last if available.

        .. seealso:: http://timetravel.mementoweb.org/guide/api/#memento-json
           for the response format.

        :param request_uri: The input http uri.
        :param accept_datetime: The datetime object of the accept
            datetime. The current datetime is used if none is provided.
        :param timeout: the timeout value for the HTTP connection.
        :return: A map of uri and datetime for the
            closest/prev/next/first/last mementos.
        """
        # for reading the headers of the req uri to find uri_r
        req_uri_response = kwargs.get('req_uri_response')
        # for checking native tg uri in uri_r
        org_response = kwargs.get('org_response')
        tg_response = kwargs.get('tg_response')
        if not tg_response:
            native_tg = None

            original_uri = self.get_original_uri(
                request_uri, response=req_uri_response)

            if self.check_native_timegate:
                native_tg = self.get_native_timegate_uri(
                    original_uri, accept_datetime=accept_datetime,
                    response=org_response)

            timegate_uri = native_tg if native_tg \
                else self.timegate_uri + original_uri

            http_acc_dt = MementoClient.convert_to_http_datetime(
                accept_datetime)

            tg_response = MementoClient.request_head(
                timegate_uri,
                accept_datetime=http_acc_dt,
                follow_redirects=True,
                session=self.session,
                timeout=timeout
            )

        return super().get_memento_info(request_uri,
                                        accept_datetime=accept_datetime,
                                        tg_response=tg_response,
                                        **kwargs)

    def get_native_timegate_uri(self,
                                original_uri: str,
                                accept_datetime: Optional[datetime],
                                timeout: Optional[int] = None,
                                **kwargs) -> Optional[str]:
        """Check the original uri whether the timegate uri is provided.

        Given an original URL and an accept datetime, check the original uri
        to see if the timegate uri is provided in the Link header.

        :param original_uri: An HTTP uri of the original resource.
        :param accept_datetime: The datetime object of the accept
            datetime
        :param timeout: the timeout value for the HTTP connection.
        :return: The timegate uri of the original resource, if provided,
            else None.
        """
        org_response = kwargs.pop('response', None)
        if not org_response:
            try:
                org_response = MementoClient.request_head(
                    original_uri,
                    accept_datetime=MementoClient.convert_to_http_datetime(
                        accept_datetime),
                    session=self.session,
                    timeout=timeout
                )
            except (requests.exceptions.ConnectTimeout,
                    requests.exceptions.ConnectionError):  # pragma: no cover
                warning('Could not connect to URI {}, returning no native '
                        'URI-G'.format(original_uri))
                return None

            debug('Request headers sent to search for URI-G:  '
                  + str(org_response.request.headers))

        return super().get_native_timegate_uri(original_uri, accept_datetime,
                                               response=org_response, **kwargs)

    @staticmethod
    def is_timegate(uri: str,
                    accept_datetime: Optional[str] = None,
                    response: Optional[requests.Response] = None,
                    session: Optional[requests.Session] = None,
                    timeout: Optional[int] = None) -> bool:
        """Checks if the given uri is a valid timegate according to the RFC.

        :param uri: the http uri to check.
        :param accept_datetime: the accept datetime string in http date
            format.
        :param response: the response object of the uri.
        :param session: the requests session object.
        :param timeout: the timeout value for the HTTP connection.
        :return: True if a valid timegate, else False.
        """
        if not response:
            if not accept_datetime:
                accept_datetime = MementoClient.convert_to_http_datetime(
                    datetime.now())

            response = MementoClient.request_head(
                uri,
                accept_datetime=accept_datetime,
                session=session,
                timeout=timeout
            )
        return old_is_timegate(
            uri, accept_datetime, response=response, session=session)

    @staticmethod
    def is_memento(uri: str,
                   response: Optional[requests.Response] = None,
                   session: Optional[requests.Session] = None,
                   timeout: Optional[int] = None) -> bool:
        """
        Determines if the URI given is indeed a Memento.

        The simple case is to look for a Memento-Datetime header in the
        request, but not all archives are Memento-compliant yet.

        :param uri: an HTTP URI for testing
        :param response: the response object of the uri.
        :param session: the requests session object.
        :param timeout: (int) the timeout value for the HTTP connection.
        :return: True if a Memento, False otherwise
        """
        if not response:
            response = MementoClient.request_head(uri,
                                                  follow_redirects=False,
                                                  session=session,
                                                  timeout=timeout)
        return old_is_memento(uri, response=response)

    @staticmethod
    def convert_to_http_datetime(dt: Optional[datetime]) -> str:
        """Converts a datetime object to a date string in HTTP format.

        :param dt: A datetime object.
        :return: The date in HTTP format.
        :raises TypeError: Expecting dt parameter to be of type datetime.
        """
        if dt and not isinstance(dt, datetime):
            raise TypeError(
                'Expecting dt parameter to be of type datetime.')
        return old_convert_to_http_datetime(dt)

    @staticmethod
    def request_head(uri: str,
                     accept_datetime: Optional[str] = None,
                     follow_redirects: bool = False,
                     session: Optional[requests.Session] = None,
                     timeout: Optional[int] = None) -> requests.Response:
        """Makes HEAD requests.

        :param uri: the uri for the request.
        :param accept_datetime: the accept-datetime in the http format.
        :param follow_redirects: Toggle to follow redirects. False by
            default, so does not follow any redirects.
        :param session: the request session object to avoid opening new
            connections for every request.
        :param timeout: the timeout for the HTTP requests.
        :return: the response object.
        :raises ValueError: Only HTTP URIs are supported
        """
        headers = {
            'Accept-Datetime': accept_datetime} if accept_datetime else {}

        # create a session if not supplied
        session_set = False
        if not session:
            session = requests.Session()
            session_set = True
        try:
            response = session.head(uri,
                                    headers=headers,
                                    allow_redirects=follow_redirects,
                                    timeout=timeout or 9)
        except (InvalidSchema, MissingSchema):
            raise ValueError('Only HTTP URIs are supported, '
                             'URI {} unrecognized.'.format(uri))
        if session_set:
            session.close()

        return response


# Save old static methods and update static methods of parent class
old_is_timegate = OldMementoClient.is_timegate
old_is_memento = OldMementoClient.is_memento
old_convert_to_http_datetime = OldMementoClient.convert_to_http_datetime
OldMementoClient.is_timegate = MementoClient.is_timegate
OldMementoClient.is_memento = MementoClient.is_memento
OldMementoClient.convert_to_http_datetime \
    = MementoClient.convert_to_http_datetime
OldMementoClient.request_head = MementoClient.request_head


def get_closest_memento_url(url: str,
                            when: Optional[datetime] = None,
                            timegate_uri: Optional[str] = None):
    """Get most recent memento for url."""
    if not when:
        when = datetime.now()

    mc = MementoClient()
    if timegate_uri:
        mc.timegate_uri = timegate_uri

    retry_count = 0
    while retry_count <= config.max_retries:
        try:
            memento_info = mc.get_memento_info(url, when)
            break
        except (requests.ConnectionError, MementoClientException) as e:
            error = e
            retry_count += 1
            sleep(config.retry_wait)
    else:
        raise error

    mementos = memento_info.get('mementos')
    if not mementos:
        err_msg = 'mementos not found for {} via {}'
    elif 'closest' not in mementos:
        err_msg = 'closest memento not found for {} via {}'
    elif 'uri' not in mementos['closest']:
        err_msg = 'closest memento uri not found for {} via {}'
    else:
        return mementos['closest']['uri'][0]
    raise Exception(err_msg.format(url, timegate_uri))
