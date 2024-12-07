"""Superset Query interface.

.. versionadded:: 9.2
"""
#
# (C) Pywikibot team, 2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from http import HTTPStatus
from textwrap import fill
from typing import TYPE_CHECKING, Any

import pywikibot
from pywikibot.comms import http
from pywikibot.data import WaitingMixin
from pywikibot.exceptions import NoUsernameError, ServerError


if TYPE_CHECKING:
    from pywikibot.site import BaseSite


class SupersetQuery(WaitingMixin):

    """Superset Query class.

    This class allows to run SQL queries against wikimedia superset
    service.
    """

    def __init__(self,
                 schema_name: str | None = None,
                 site: BaseSite | None = None,
                 database_id: int | None = None) -> None:
        """Create superset endpoint with initial defaults.

        Either site OR schema_name is required. Site and schema_name are
        mutually exclusive. Database id will be retrieved automatically
        if needed.

        :param site: The mediawiki site to be queried
        :param schema_name: superset database schema name. Example value
            "enwiki_p"
        :param database_id: superset database id.
        :raises TypeError: if site and schema_name are both defined'
        """
        if site and schema_name:
            msg = 'Only one of schema_name and site parameters can be defined'
            raise TypeError(msg)

        # Validate database_id
        if database_id and not isinstance(database_id, int):
            msg = f'database_id should be integer, but got "{database_id}"'
            raise TypeError(msg)

        self.site = site
        self.schema_name = schema_name
        self.database_id = database_id

        self.connected = False
        self.last_response = None
        self.superset_url = 'https://superset.wmcloud.org'

    def login(self) -> bool:
        """Login to superset.

        Function logins first to meta.wikimedia.org and then OAUTH login
        to superset.wmcloud.org. Working login expects that the user has
        manually permitted the username to login to the superset.

        :raises NoUsernameError: if not not logged in.
        :raises ServerError: For other errors
        :return: True if user has been logged to superset
        """
        # superset uses meta for OAUTH authentication
        loginsite = pywikibot.Site('meta')
        if not loginsite.logged_in():
            loginsite.login()
        if not loginsite.logged_in():
            msg = 'User is not logged in on meta.wikimedia.org'
            raise NoUsernameError(msg)

        # Superset oauth login
        url = f'{self.superset_url}/login/mediawiki?next='
        self.last_response = http.fetch(url)

        # Test if uset has been successfully logged in
        url = f'{self.superset_url}/api/v1/me/'
        self.last_response = http.fetch(url)

        # Handle error cases
        if self.last_response.status_code == HTTPStatus.OK:
            self.connected = True
        elif self.last_response.status_code == HTTPStatus.UNAUTHORIZED:
            self.connected = False
            raise NoUsernameError(fill(
                'User not logged in. You need to log in to '
                'meta.wikimedia.org and give OAUTH permission. '
                'Open https://superset.wmcloud.org/login/ '
                'with browser to login and give permission.'
            ))
        else:
            self.connected = False
            status_code = self.last_response.status_code
            raise ServerError(f'Unknown error: {status_code}')

        return self.connected

    def get_csrf_token(self) -> str:
        """Get superset CSRF token.

        Method retrieves a CSRF token from the Superset service. If the
        instance is not connected, it attempts to log in first.

        :raises ServerError: For any http errors
        :return: CSRF token string
        """
        if not self.connected:
            self.login()

        # Load CSRF token
        url = f'{self.superset_url}/api/v1/security/csrf_token/'
        self.last_response = http.fetch(url)

        if self.last_response.status_code == HTTPStatus.OK:
            return self.last_response.json()['result']

        status_code = self.last_response.status_code
        raise ServerError(f'CSRF token error:  {status_code}')

    def get_database_id_by_schema_name(self, schema_name: str) -> int:
        """Get superset database_id using superset schema name.

        :param schema_name: superset database schema name. Example value
            "enwiki_p"
        :raises KeyError: If the database ID could found.
        :raises ServerError: For any other http errors
        :return: database id
        """
        if not self.connected:
            self.login()

        for database_id in range(1, 20):
            url = self.superset_url
            url += f'/api/v1/database/{database_id}/schemas/?q=(force:!f)'
            self.last_response = http.fetch(url)

            if self.last_response.status_code == HTTPStatus.OK:
                schemas = self.last_response.json()['result']
                if schema_name in schemas:
                    return database_id

            elif self.last_response.status_code == HTTPStatus.NOT_FOUND:
                break
            else:
                status_code = self.last_response.status_code
                raise ServerError(f'Unknown error: {status_code}')

        url = self.superset_url
        raise KeyError(f'Schema "{schema_name}" not found in {url}.')

    def merge_query_arguments(self,
                              database_id: int | None = None,
                              schema_name: str | None = None,
                              site: BaseSite = None) -> tuple(int, str):
        """Determine and validate the database_id and schema_name.

        :param database_id: The superset database ID.
        :param schema_name: The superset schema name.
        :param site: The target site
        :raises TypeError: if site and schema_name are both defined'
        :raises TypeError: If determined database_id is not an integer.
        :raises TypeError: If neither site nor schema_name is determined.
        :return: A tuple containing database_id and schema_name.
        """
        if site and schema_name:
            msg = 'Only one of schema_name and site parameters can be defined'
            raise TypeError(msg)

        # Determine schema_name
        if not schema_name:
            if site:
                schema_name = f'{site.dbName()}_p'
            elif self.schema_name:
                schema_name = self.schema_name
            elif self.site:
                schema_name = f'{self.site.dbName()}_p'

        # Determine database_id
        if not database_id:
            if self.database_id:
                database_id = int(self.database_id)
            else:
                database_id = self.get_database_id_by_schema_name(schema_name)

        # Validate database_id
        if not isinstance(database_id, int):
            msg = f'database_id should be integer, but got "{database_id}"'
            raise TypeError(msg)

        # Ensure either site or schema_name is provided
        if not (self.site or schema_name):
            raise TypeError('Either site or schema_name must be provided')

        return database_id, schema_name

    def query(self, sql: str,
              database_id: int | None = None,
              schema_name: str | None = None,
              site: BaseSite = None) -> list[Any]:
        """Execute SQL queries on Superset.

        :param sql: The SQL query to execute.
        :param database_id: The database ID.
        :param schema_name: The schema name.
        :raises RuntimeError: If the query execution fails.
        :return: The data returned from the query execution.
        """
        if not self.connected:
            self.login()

        token = self.get_csrf_token()

        headers = {
            'X-CSRFToken': token,
            'Content-Type': 'application/json',
            'referer': 'https://superset.wmcloud.org/sqllab/'
        }

        database_id, schema_name = self.merge_query_arguments(database_id,
                                                              schema_name,
                                                              site)

        sql_query_payload = {
            'database_id': database_id,
            'schema': schema_name,
            'sql': sql,
            'json': True,
            'runAsync': False,
        }

        url = f'{self.superset_url}/api/v1/sqllab/execute/'
        try:
            self.last_response = http.fetch(uri=url,
                                            json=sql_query_payload,
                                            method='POST',
                                            headers=headers)
            self.last_response.raise_for_status()
            json = self.last_response.json()
            return json['data']

        except Exception as e:
            raise RuntimeError(f'Failed to execute query: {e}')
