# -*- coding: utf-8 -*-
"""Miscellaneous helper functions for mysql queries."""
#
# (C) Pywikibot team, 2016-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals
__version__ = '$Id$'

# Requires oursql <https://pythonhosted.org/oursql/> or
#  MySQLdb <https://sourceforge.net/projects/mysql-python/>
try:
    import oursql as mysqldb
except ImportError:
    import MySQLdb as mysqldb

import pywikibot

from pywikibot import config2 as config


def mysql_query(query, params=(), dbname=None, encoding='utf-8', verbose=None):
    """
    Yield rows from a MySQL query.

    An example query that yields all ns0 pages might look like::

        SELECT
         page_namespace,
         page_title,
        FROM page
        WHERE page_namespace = 0;

    @param query: MySQL query to execute
    @type query: str
    @param params: input parametes for the query, if needed
    @type params: tuple
    @param dbname: db name
    @type dbname: str
    @param encoding: encoding used by the database
    @type encoding: str
    @param verbose: if True, print query to be executed;
        if None, config.verbose_output will be used.
    @type verbose: None or bool
    @return: generator which yield tuples
    """
    if verbose is None:
        verbose = config.verbose_output

    if config.db_connect_file is None:
        conn = mysqldb.connect(config.db_hostname,
                               db=config.db_name_format.format(dbname),
                               user=config.db_username,
                               passwd=config.db_password,
                               port=config.db_port)
    else:
        conn = mysqldb.connect(config.db_hostname,
                               db=config.db_name_format.format(dbname),
                               read_default_file=config.db_connect_file,
                               port=config.db_port)

    cursor = conn.cursor()
    if verbose:
        pywikibot.output('Executing query:\n%s' % query)
    query = query.encode(encoding)
    params = tuple(p.encode(encoding) for p in params)

    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    for row in cursor:
        yield row

    cursor.close()
    conn.close()
