# -*- coding: utf-8 -*-
"""Miscellaneous helper functions for mysql queries."""
#
# (C) Pywikibot team, 2016-2020
#
# Distributed under the terms of the MIT license.
#
from contextlib import closing
from typing import Optional

import pywikibot

try:
    import pymysql
except ImportError:
    raise ImportError('MySQL python module not found. Please install PyMySQL.')


from pywikibot import config2 as config
from pywikibot.tools import deprecated_args


@deprecated_args(encoding=None)
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

    @param query: MySQL query to execute
    @param params: input parameters for the query, if needed
        if list or tuple, %s shall be used as placeholder in the query string.
        if a dict, %(key)s shall be used as placeholder in the query string.
    @type params: tuple, list or dict of str
    @param dbname: db name
    @param verbose: if True, print query to be executed;
        if None, config.verbose_output will be used.
    @return: generator which yield tuples
    """
    # These are specified in config2.py or user-config.py
    if verbose is None:
        verbose = config.verbose_output

    if config.db_connect_file is None:
        credentials = {'user': config.db_username,
                       'passwd': config.db_password}
    else:
        credentials = {'read_default_file': config.db_connect_file}

    with closing(pymysql.connect(config.db_hostname,
                                 db=config.db_name_format.format(dbname),
                                 port=config.db_port,
                                 charset='utf8',
                                 **credentials)) as conn, \
         closing(conn.cursor()) as cursor:

        if verbose:
            _query = cursor.mogrify(query, params)

            if not isinstance(_query, str):
                _query = str(_query, encoding='utf-8')
            _query = _query.strip()
            _query = '\n'.join('    {0}'.format(line)
                               for line in _query.splitlines())
            pywikibot.output('Executing query:\n' + _query)

        cursor.execute(query, params)
        yield from cursor
