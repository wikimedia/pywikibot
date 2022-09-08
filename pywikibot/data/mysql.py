"""Miscellaneous helper functions for mysql queries."""
#
# (C) Pywikibot team, 2016-2022
#
# Distributed under the terms of the MIT license.
#
import struct
from typing import Optional

import pkg_resources

import pywikibot
from pywikibot import config
from pywikibot.backports import removesuffix
from pywikibot.tools import issue_deprecation_warning


try:
    import pymysql
except ImportError:
    raise ImportError('MySQL python module not found. Please install PyMySQL.')


COM_QUIT = 0x01


class _OldConnection(pymysql.connections.Connection):

    """Representation of a socket with a mysql server.

    This class is used to patch close() method for pymysql<0.7.11 on
    toolforge (:phab:`T216741`).

    .. versionadded:: 7.0
    .. deprecated:: 7.4
       Update your pymysql package
    """

    def close(self) -> None:  # pragma: no cover
        """Send the quit message and close the socket."""
        if self._closed or self._sock is None:
            super().close()

        send_data = struct.pack('<iB', 1, COM_QUIT)
        try:
            self._write_bytes(send_data)
        except Exception:
            pass
        finally:
            self._force_close()


def mysql_query(query: str, params=None,
                dbname: Optional[str] = None,
                verbose: Optional[bool] = None):
    """Yield rows from a MySQL query.

    An example query that yields all ns0 pages might look like::

        SELECT
         page_namespace,
         page_title,
        FROM page
        WHERE page_namespace = 0;

    Supported MediaWiki projects use Unicode (UTF-8) character encoding.
    Cursor charset is utf8.

    :param query: MySQL query to execute
    :param params: input parameters for the query, if needed
        if list or tuple, %s shall be used as placeholder in the query string.
        if a dict, %(key)s shall be used as placeholder in the query string.
    :type params: tuple, list or dict of str
    :param dbname: db name
    :param verbose: if True, print query to be executed;
        if None, config.verbose_output will be used.
    :return: generator which yield tuples
    """
    # These are specified in config.py or your user config file
    if verbose is None:
        verbose = config.verbose_output

    if config.db_connect_file is None:
        credentials = {'user': config.db_username,
                       'password': config.db_password}
    else:
        credentials = {'read_default_file': config.db_connect_file}

    pymysql_version = pkg_resources.parse_version(
        removesuffix(pymysql.__version__, '.None'))
    args = {
        'host': config.db_hostname_format.format(dbname),
        'database': config.db_name_format.format(dbname),
        'port': config.db_port,
        'charset': 'utf8',
        'defer_connect': query == 'test',  # for tests
    }

    if pymysql_version < pkg_resources.parse_version('0.7.11'):
        issue_deprecation_warning(
            'pymysql package release {}'.format(pymysql_version),
            instead='pymysql >= 0.7.11', since='7.4.0')
        connection = _OldConnection(**args, **credentials)
    else:
        connection = pymysql.connect(**args, **credentials)

    if pymysql_version < pkg_resources.parse_version('1.0.0'):
        from contextlib import closing
        connection = closing(connection)

    with connection as conn, conn.cursor() as cursor:
        if verbose:
            _query = cursor.mogrify(query, params)

            if not isinstance(_query, str):
                _query = str(_query, encoding='utf-8')
            _query = _query.strip()
            _query = '\n'.join('    {}'.format(line)
                               for line in _query.splitlines())
            pywikibot.output('Executing query:\n' + _query)

        if query == 'test':  # for tests only
            yield query

        cursor.execute(query, params)
        yield from cursor
