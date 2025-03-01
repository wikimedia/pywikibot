"""Objects representing API/Query generators.

.. versionchanged:: 7.6
   All Objects were changed from Iterable object to a Generator object.
   They are subclassed from :class:`tools.collections.GeneratorWrapper`
"""
#
# (C) Pywikibot team, 2008-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Any
from warnings import warn

import pywikibot
from pywikibot import config
from pywikibot.backports import Callable, Iterable
from pywikibot.exceptions import (
    Error,
    InvalidTitleError,
    UnknownSiteError,
    UnsupportedPageError,
)
from pywikibot.site import Namespace
from pywikibot.tools import deprecated
from pywikibot.tools.collections import GeneratorWrapper


__all__ = (
    'APIGenerator',
    'ListGenerator',
    'LogEntryListGenerator',
    'PageGenerator',
    'PropertyGenerator',
    'QueryGenerator',
    'update_page',
)


class APIGeneratorBase(ABC):

    """A wrapper class to handle the usage of the ``parameters`` parameter.

    .. versionchanged:: 7.6
       renamed from _RequestWrapper
    """

    def _clean_kwargs(self, kwargs, **mw_api_args):
        """Clean kwargs, define site and request class."""
        if 'site' not in kwargs:
            warn(f'{self.__class__.__name__} invoked without a site',
                 RuntimeWarning, 3)
            kwargs['site'] = pywikibot.Site()
        assert not hasattr(self, 'site') or self.site == kwargs['site']
        self.site = kwargs['site']
        self.request_class = kwargs['site']._request_class(kwargs)
        kwargs = self.request_class.clean_kwargs(kwargs)
        kwargs['parameters'].update(mw_api_args)
        return kwargs

    @abstractmethod
    def set_maximum_items(self, value: int | str | None) -> None:
        """Set the maximum number of items to be retrieved from the wiki.

        .. versionadded:: 7.1
        .. versionchanged:: 7.6
           become an abstract method
        """
        raise NotImplementedError


class APIGenerator(APIGeneratorBase, GeneratorWrapper):

    """Generator that handle API responses containing lists.

    The generator will iterate each item in the query response and use
    the continue request parameter to retrieve the next portion of items
    automatically. If the limit attribute is set, the iterator will stop
    after iterating that many values.

    .. versionchanged:: 7.6
       subclassed from :class:`tools.collections.GeneratorWrapper`
    """

    def __init__(
        self,
        action: str,
        continue_name: str = 'continue',
        limit_name: str = 'limit',
        data_name: str = 'data',
        **kwargs
    ) -> None:
        """Initialize an APIGenerator object.

        kwargs are used to create a Request object; see that object's
        documentation for values.

        :param action: API action name.
        :param continue_name: Name of the continue API parameter.
        :param limit_name: Name of the limit API parameter.
        :param data_name: Name of the data in API response.
        :keyword dict parameters: All parameters passed to request class
            usally :class:`api.Request<data.api.Request>` or
            :class:`api.CachedRequest<data.api.CachedRequest>`. See these
            classes for further parameter descriptions. The *parameters*
            keys can also given here as keyword parameters but this is
            not recommended.
        """
        kwargs = self._clean_kwargs(kwargs, action=action)

        self.continue_name = continue_name
        self.limit_name = limit_name
        self.data_name = data_name

        self.query_increment: int | None
        if config.step > 0:
            self.query_increment = config.step
        else:
            self.query_increment = None
        self.limit: int | None = None
        self.starting_offset = kwargs['parameters'].pop(self.continue_name, 0)
        self.request = self.request_class(**kwargs)
        self.request[self.limit_name] = self.query_increment

    def set_query_increment(self, value: int) -> None:
        """Set the maximum number of items to be retrieved per API query.

        If not called, the default is config.step.

        :param value: The value of maximum number of items to be retrieved
            per API request to set.
        """
        self.query_increment = int(value)
        self.request[self.limit_name] = self.query_increment
        pywikibot.debug(f'{type(self).__name__}: Set query_increment to '
                        f'{self.query_increment}.')

    def set_maximum_items(self, value: int | str | None) -> None:
        """Set the maximum number of items to be retrieved from the wiki.

        If not called, most queries will continue as long as there is
        more data to be retrieved from the API.

        :param value: The value of maximum number of items to be retrieved
            in total to set. Ignores None value.
        """
        if value is not None and int(value) > 0:
            self.limit = int(value)
            if self.query_increment and self.limit < self.query_increment:
                self.request[self.limit_name] = self.limit
                pywikibot.debug(f'{type(self).__name__}: Set request item '
                                f'limit to {self.limit}')
            pywikibot.debug(f'{type(self).__name__}: Set limit '
                            f'(maximum_items) to {self.limit}.')

    @property
    def generator(self):
        """Submit request and iterate the response.

        Continues response as needed until limit (if defined) is reached.

        .. versionchanged:: 7.6
           changed from iterator method to generator property
        """
        offset = self.starting_offset
        n = 0
        while True:
            self.request[self.continue_name] = offset
            pywikibot.debug(f'{type(self).__name__}: Request: {self.request}')
            data = self.request.submit()

            n_items = len(data[self.data_name])
            pywikibot.debug(
                f'{type(self).__name__}: Retrieved {n_items} items')
            if n_items > 0:
                for item in data[self.data_name]:
                    yield item
                    n += 1
                    if self.limit is not None and n >= self.limit:
                        pywikibot.debug(
                            f'{type(self).__name__}: Stopped iterating due to'
                            ' exceeding item limit.'
                        )
                        return
                offset += n_items
            else:
                pywikibot.debug(f'{type(self).__name__}: Stopped iterating'
                                ' due to empty list in response.')
                break


class QueryGenerator(APIGeneratorBase, GeneratorWrapper):

    """Base class for generators that handle responses to API action=query.

    By default, the generator will iterate each item in the query
    response, and use the (query-)continue element, if present, to
    continue iterating as long as the wiki returns additional values.
    However, if the generators's limit attribute is set to a positive
    int, the generators will stop after iterating that many values. If
    limit is negative, the limit parameter will not be passed to the API
    at all.

    Most common query types are more efficiently handled by subclasses,
    but this class can be used directly for custom queries and
    miscellaneous types (such as "meta=...") that don't return the usual
    list of pages or links. See the API documentation for specific query
    options.

    .. versionchanged:: 7.6
       subclassed from :class:`tools.collections.GeneratorWrapper`
    """

    # Should results be filtered during iteration according to set_namespace?
    # Used if the API module does not support multiple namespaces.
    # Override in subclasses by defining a function that returns True if
    # the result's namespace is in self._namespaces.
    _check_result_namespace: Callable[[Any], bool] = NotImplemented

    # Set of allowed namespaces will be assigned to _namespaces during
    # set_namespace call. Only to be used by _check_result_namespace.
    _namespaces: set[int] | bool | None = None

    def __init__(self, **kwargs) -> None:
        """Initialize a QueryGenerator object.

        kwargs are used to create a Request object; see that object's
        documentation for values. 'action'='query' is assumed.
        """
        if not hasattr(self, 'site'):
            kwargs = self._clean_kwargs(kwargs)  # hasn't been called yet
        parameters = kwargs['parameters']
        if 'action' in parameters and parameters['action'] != 'query':
            raise Error("{}: 'action' must be 'query', not {}"
                        .format(self.__class__.__name__, kwargs['action']))
        parameters['action'] = 'query'
        # make sure request type is valid, and get limit key if any
        for modtype in ('generator', 'list', 'prop', 'meta'):
            if modtype in parameters:
                self.modules = parameters[modtype].split('|')
                break
        else:
            raise Error(f'{type(self).__name__}: No query module name found'
                        ' in arguments.')

        parameters['indexpageids'] = True  # always ask for list of pageids
        self.continue_name = 'continue'
        self.request = self.request_class(**kwargs)

        self.site._paraminfo.fetch('query+' + mod for mod in self.modules)

        limited_modules = {mod for mod in self.modules
                           if self.site._paraminfo.parameter('query+' + mod,
                                                             'limit')}

        if not limited_modules:
            self.limited_module = None
        elif len(limited_modules) == 1:
            self.limited_module = limited_modules.pop()
        else:
            # Select the first limited module in the request.
            # Query will continue as needed until limit (if any) for this
            # module is reached.
            for module in self.modules:
                if module in limited_modules:
                    self.limited_module = module
                    limited_modules.remove(module)
                    break
            pywikibot.log(
                f'{type(self).__name__}: multiple requested query modules'
                ' support limits; using the first such module '
                f"{self.limited_module}' of {self.modules!r}"
            )

            # Set limits for all remaining limited modules to max value.
            # Default values will only cause more requests and make the query
            # slower.
            for module in limited_modules:
                param = self.site._paraminfo.parameter('query+' + module,
                                                       'limit')
                prefix = self.site._paraminfo['query+' + module]['prefix']
                if self.site.logged_in() \
                   and self.site.has_right('apihighlimits'):
                    self.request[prefix + 'limit'] = int(param['highmax'])
                else:
                    self.request[prefix + 'limit'] = int(param['max'])

        self.api_limit: int | None
        if config.step > 0:
            self.api_limit = config.step
        else:
            self.api_limit = None

        if self.limited_module:
            self.prefix = self.site._paraminfo['query+'
                                               + self.limited_module]['prefix']
            self._update_limit()

        if self.api_limit is not None and 'generator' in parameters:
            self.prefix = 'g' + self.prefix

        self.limit: int | None = None
        self.query_limit = self.api_limit
        if 'generator' in parameters:
            # name of the "query" subelement key to look for when iterating
            self.resultkey = 'pages'
        else:
            self.resultkey = self.modules[0]

        self._add_slots()

    @property
    @deprecated(since='8.4.0')
    def continuekey(self) -> list[str]:
        """Return deprecated continuekey which is self.modules."""
        return self.modules

    def _add_slots(self) -> None:
        """Add slots to params if the site supports multi-content revisions.

        On MW 1.32+ the following query parameters require slots to be given
        when content or contentmodel is requested.

        * prop=revisions
        * prop=deletedrevisions or
        * list=allrevisions
        * list=alldeletedrevisions

        More info:
        https://lists.wikimedia.org/hyperkitty/list/mediawiki-api-announce@lists.wikimedia.org/message/AXO4G4OOMTG7CEUU5TGAWXBI2LD4G3BC/
        """
        if self.site.mw_version < '1.32':
            return
        request = self.request
        # If using any deprecated_params, do not add slots. Usage of
        # these parameters together with slots is forbidden and the user will
        # get an API warning anyway.
        props = request.get('prop')
        if props:
            if 'revisions' in props:
                deprecated_params = {
                    'rvexpandtemplates', 'rvparse', 'rvdiffto', 'rvdifftotext',
                    'rvdifftotextpst', 'rvcontentformat', 'parsetree'}
                if not set(request) & deprecated_params:
                    request['rvslots'] = '*'
            if 'deletedrevisions' in props:
                deprecated_params = {
                    'drvexpandtemplates', 'drvparse', 'drvdiffto',
                    'drvdifftotext', 'drvdifftotextpst', 'drvcontentformat',
                    'parsetree'}
                if not set(request) & deprecated_params:
                    request['drvslots'] = '*'
        lists = request.get('list')
        if lists:
            if 'allrevisions' in lists:
                deprecated_params = {
                    'arvexpandtemplates', 'arvparse', 'arvdiffto',
                    'arvdifftotext', 'arvdifftotextpst', 'arvcontentformat',
                    'parsetree'}
                if not set(request) & deprecated_params:
                    request['arvslots'] = '*'
            if 'alldeletedrevisions' in lists:
                deprecated_params = {
                    'adrexpandtemplates', 'adrparse', 'adrdiffto',
                    'adrdifftotext', 'adrdifftotextpst', 'adrcontentformat',
                    'parsetree'}
                if not set(request) & deprecated_params:
                    request['adrslots'] = '*'

    def set_query_increment(self, value) -> None:
        """Set the maximum number of items to be retrieved per API query.

        If not called, the default is to ask for "max" items and let the
        API decide how many to send.
        """
        limit = int(value)

        # don't update if limit is greater than maximum allowed by API
        if self.api_limit is None:
            self.query_limit = limit
        else:
            self.query_limit = min(self.api_limit, limit)
        pywikibot.debug(
            f'{type(self).__name__}: Set query_limit to {self.query_limit}.'
        )

    def set_maximum_items(self, value: int | str | None) -> None:
        """Set the maximum number of items to be retrieved from the wiki.

        If not called, most queries will continue as long as there is
        more data to be retrieved from the API.

        If set to -1 (or any negative value), the "limit" parameter will be
        omitted from the request. For some request types (such as
        prop=revisions), this is necessary to signal that only current
        revision is to be returned.

        :param value: The value of maximum number of items to be retrieved
            in total to set. Ignores None value.
        """
        if value is not None:
            self.limit = int(value)

    def _update_limit(self) -> None:
        """Set query limit for self.module based on api response."""
        assert self.limited_module is not None
        param = self.site._paraminfo.parameter('query+' + self.limited_module,
                                               'limit')
        if self.site.logged_in() and self.site.has_right('apihighlimits'):
            limit = int(param['highmax'])
        else:
            limit = int(param['max'])
        if self.api_limit is None or limit < self.api_limit:
            self.api_limit = limit
            pywikibot.debug(
                f'{type(self).__name__}: Set query_limit to {self.api_limit}.'
            )

    def support_namespace(self) -> bool:
        """Check if namespace is a supported parameter on this query.

        .. note:: this function will be removed when
           :meth:`set_namespace` will throw TypeError() instead of just
           giving a warning. See :phab:`T196619`.

        :return: True if yes, False otherwise
        """
        assert self.limited_module  # some modules do not have a prefix
        return bool(
            self.site._paraminfo.parameter('query+' + self.limited_module,
                                           'namespace'))

    def set_namespace(self, namespaces):
        """Set a namespace filter on this query.

        :param namespaces: namespace identifiers to limit query results
        :type namespaces: iterable of str or Namespace key, or a single
            instance of those types. May be a '|' separated list of
            namespace identifiers. An empty iterator clears any
            namespace restriction.
        :raises KeyError: a namespace identifier was not resolved
        """
        # TODO: T196619
        # :raises TypeError: module does not support a namespace parameter
        #    or a namespace identifier has an inappropriate
        #    type such as NoneType or bool, or more than one namespace
        #    if the API module does not support multiple namespaces
        assert self.limited_module  # some modules do not have a prefix
        param = self.site._paraminfo.parameter('query+' + self.limited_module,
                                               'namespace')
        if not param:
            pywikibot.warning(f'{self.limited_module} module does not support'
                              ' a namespace parameter')
            warn('set_namespace() will be modified to raise TypeError '
                 'when namespace parameter is not supported. '
                 'It will be a Breaking Change, please update your code '
                 'ASAP, due date July, 31st 2019.', FutureWarning, 2)

            # TODO: T196619
            # raise TypeError('{} module does not support a namespace '
            #                 'parameter'.format(self.limited_module))

            return False

        if isinstance(namespaces, str):
            namespaces = namespaces.split('|')

        # Use Namespace id (int) here; Request will cast int to str
        namespaces = [ns.id for ns in
                      self.site.namespaces.resolve(namespaces)]

        if 'multi' not in param and len(namespaces) != 1:
            if self._check_result_namespace is NotImplemented:
                raise TypeError(f'{self.limited_module} module does not'
                                ' support multiple namespaces')
            self._namespaces = set(namespaces)
            namespaces = None

        if namespaces:
            self.request[self.prefix + 'namespace'] = namespaces
        elif self.prefix + 'namespace' in self.request:
            del self.request[self.prefix + 'namespace']

        return None

    def continue_update(self) -> None:
        """Update query with continue parameters.

        .. versionadded:: 3.0
        .. versionchanged:: 4.0
           explicit return a bool value to be used in :meth:`generator`
        .. versionchanged:: 6.0
           always return *False*
        .. versionchanged:: 8.4
           return *None* instead of *False*.
        """
        for key, value in self.data[self.continue_name].items():
            # old query-continue could return ints, continue too?
            if isinstance(value, int):
                value = str(value)
            self.request[key] = value

    def _handle_query_limit(self, prev_limit, new_limit, had_data):
        """Handle query limit."""
        if self.query_limit is None or self.limited_module is None:
            return prev_limit, new_limit

        prev_limit = new_limit
        if self.limit is None:
            new_limit = self.query_limit
        elif self.limit > 0:
            if had_data:
                # self.resultkey in data in last request.submit()
                new_limit = min(self.query_limit, self.limit - self._count)
            else:
                # only "(query-)continue" returned. See Bug T74209.
                # increase new_limit to advance faster until new
                # useful data are found again.
                new_limit = min(new_limit * 2, self.query_limit)
        else:
            new_limit = None

        if new_limit and 'rvprop' in self.request \
                and 'content' in self.request['rvprop']:
            # queries that retrieve page content have lower limits
            # Note: although API allows up to 500 pages for content
            #       queries, these sometimes result in server-side errors
            #       so use 250 as a safer limit
            new_limit = min(new_limit, self.api_limit // 10, 250)

        if new_limit is not None:
            self.request[self.prefix + 'limit'] = str(new_limit)

        if prev_limit != new_limit:
            pywikibot.debug(
                '{name}: query_limit: {query}, api_limit: {api}, '
                'limit: {limit}, new_limit: {new}, count: {count}\n'
                '{name}: {prefix}limit: {value}'
                .format(name=self.__class__.__name__,
                        query=self.query_limit,
                        api=self.api_limit,
                        limit=self.limit,
                        new=new_limit,
                        count=self._count,
                        prefix=self.prefix,
                        value=self.request[self.prefix + 'limit']))
        return prev_limit, new_limit

    def _get_resultdata(self):
        """Get resultdata and verify result."""
        resultdata = keys = self.data['query'][self.resultkey]
        if isinstance(resultdata, dict):
            keys = list(resultdata)
            if 'results' in resultdata:
                resultdata = resultdata['results']
            elif 'pageids' in self.data['query']:
                # this ensures that page data will be iterated
                # in the same order as received from server
                resultdata = [resultdata[k]
                              for k in self.data['query']['pageids']]
            else:
                resultdata = [resultdata[k]
                              for k in sorted(resultdata)]
        pywikibot.debug(
            f'{type(self).__name__} received {keys}; limit={self.limit}')
        return resultdata

    def _extract_results(self, resultdata):
        """Extract results from resultdata."""
        for item in resultdata:
            result = self.result(item)
            if self._namespaces and not self._check_result_namespace(result):
                continue

            yield result

            modules_item_intersection = set(self.modules) & set(item)
            if isinstance(item, dict) and modules_item_intersection:
                # if we need to count elements contained in items in
                # self.data["query"]["pages"], we want to count
                # item[self.modules] (e.g. 'revisions') and not
                # self.resultkey (i.e. 'pages')
                for key in modules_item_intersection:
                    self._count += len(item[key])
            # otherwise we proceed as usual
            else:
                self._count += 1
            # note: self.limit could be -1
            if self.limit and 0 < self.limit <= self._count:
                raise RuntimeError(
                    'QueryGenerator._extract_results reached the limit')

    @property
    def generator(self):
        """Submit request and iterate the response based on self.resultkey.

        Continues response as needed until limit (if any) is reached.

        .. versionchanged:: 7.6
           changed from iterator method to generator property
        """
        previous_result_had_data = True
        prev_limit = new_limit = None

        self._count = 0
        while True:
            prev_limit, new_limit = self._handle_query_limit(
                prev_limit, new_limit, previous_result_had_data)

            if not hasattr(self, 'data'):
                self.data = self.request.submit()

            if not self.data or not isinstance(self.data, dict):
                pywikibot.debug(f'{type(self).__name__}: stopped iteration'
                                ' because no dict retrieved from api.')
                break

            if 'query' in self.data and self.resultkey in self.data['query']:
                resultdata = self._get_resultdata()
                if 'normalized' in self.data['query']:
                    self.normalized = {
                        item['to']: item['from']
                        for item in self.data['query']['normalized']}
                else:
                    self.normalized = {}

                try:
                    yield from self._extract_results(resultdata)
                except RuntimeError:
                    break

                # self.resultkey in data in last request.submit()
                previous_result_had_data = True
            else:
                if 'query' not in self.data:
                    pywikibot.log(f"{type(self).__name__}: 'query' not found"
                                  ' in api response.')
                    pywikibot.log(str(self.data))

                # if (query-)continue is present, self.resultkey might not have
                # been fetched yet
                if self.continue_name not in self.data:
                    break  # No results.

                # self.resultkey not in data in last request.submit()
                # only "(query-)continue" was retrieved.
                previous_result_had_data = False

            if self.modules[0] == 'random':
                # "random" module does not return "(query-)continue"
                # now we loop for a new random query
                del self.data  # a new request is needed
                continue

            if self.continue_name not in self.data:
                break

            self.continue_update()
            del self.data  # a new request with continue is needed

    def result(self, data):
        """Process result data as needed for particular subclass."""
        return data


class PageGenerator(QueryGenerator):

    """Generator for response to a request of type action=query&generator=foo.

    This class can be used for any of the query types that are listed in
    the API documentation as being able to be used as a generator.
    Instances of this class iterate Page objects.
    """

    def __init__(
        self,
        generator: str,
        g_content: bool = False,
        **kwargs
    ) -> None:
        """Initializer.

        Required and optional parameters are as for ``Request``, except
        that ``action=query`` is assumed and generator is required.

        .. versionchanged:: 9.1
           retrieve the same imageinfo properties as in
           :meth:`APISite.loadimageinfo()
           <pywikibot.site._apisite.APISite.loadimageinfo>` with default
           parameters.

        :param generator: the "generator=" type from api.php
        :param g_content: if True, retrieve the contents of the current
            version of each Page (default False)
        """
        # If possible, use self.request after __init__ instead of append_params
        def append_params(params, key, value) -> None:
            if key in params:
                params[key] += '|' + value
            else:
                params[key] = value

        kwargs = self._clean_kwargs(kwargs)
        parameters = kwargs['parameters']
        # get some basic information about every page generated
        append_params(parameters, 'prop', 'info|imageinfo|categoryinfo')
        if g_content:
            # retrieve the current revision
            append_params(parameters, 'prop', 'revisions')
            append_params(parameters, 'rvprop',
                          'ids|timestamp|flags|comment|user|content')
        if not ('inprop' in parameters
                and 'protection' in parameters['inprop']):
            append_params(parameters, 'inprop', 'protection')
        append_params(parameters, 'iiprop', pywikibot.site._IIPROP)
        append_params(parameters, 'iilimit', 'max')  # T194233
        parameters['generator'] = generator
        super().__init__(**kwargs)
        self.resultkey = 'pages'  # element to look for in result
        self.props = self.request['prop']

    def result(self, pagedata: dict[str, Any]) -> pywikibot.Page:
        """Convert page dict entry from api to Page object.

        This can be overridden in subclasses to return a different type
        of object.

        .. versionchanged:: 9.5
           No longer raise :exc:`exceptions.UnsupportedPageError` but
           return a generic :class:`pywikibot.Page` object. The exception
           is raised when getting the content for example.
        .. versionchanged:: 9.6
           Upcast to :class:`page.FilePage` if *pagedata* has
           ``imageinfo`` contents even if the file extension is invalid.
        """
        p = pywikibot.Page(self.site, pagedata['title'], pagedata['ns'])
        ns = pagedata['ns']
        # Upcast to proper Page subclass.
        if ns == Namespace.USER:
            p = pywikibot.User(p)
        elif ns == Namespace.FILE:
            with suppress(ValueError):
                p = pywikibot.FilePage(
                    p, ignore_extension='imageinfo' in pagedata)
        elif ns == Namespace.CATEGORY:
            p = pywikibot.Category(p)

        with suppress(UnsupportedPageError):
            update_page(p, pagedata, self.props)

        return p


class PropertyGenerator(QueryGenerator):

    """Generator for queries of type action=query&prop=foo.

    See the API documentation for types of page properties that can be
    queried.

    This generator yields one or more dict object(s) corresponding to
    each "page" item(s) from the API response; the calling module has to
    decide what to do with the contents of the dict. There will be one
    dict for each page queried via a titles= or ids= parameter (which must
    be supplied when instantiating this class).
    """

    def __init__(self, prop: str, **kwargs) -> None:
        """Initializer.

        Required and optional parameters are as for ``Request``, except that
        action=query is assumed and prop is required.

        :param prop: the "prop=" type from api.php
        """
        kwargs = self._clean_kwargs(kwargs, prop=prop)
        super().__init__(**kwargs)
        self._props = frozenset(prop.split('|'))
        self.resultkey = 'pages'

    @property
    def props(self):
        """The requested property names."""
        return self._props

    @property
    def generator(self):
        """Yield results.

        .. versionchanged:: 7.6
           changed from iterator method to generator property
        """
        self._previous_dicts = {}
        yield from super().generator
        yield from self._previous_dicts.values()

    def _extract_results(self, resultdata):
        """Yield completed page_data of consecutive API requests."""
        yield from self._fully_retrieved_data_dicts(resultdata)
        for data_dict in super()._extract_results(resultdata):
            if 'title' in data_dict:
                d = self._previous_dicts.setdefault(data_dict['title'],
                                                    data_dict)
                if d is not data_dict:
                    self._update_old_result_dict(d, data_dict)
            else:
                pywikibot.warning('Skipping result without title: '
                                  + str(data_dict))

    def _fully_retrieved_data_dicts(self, resultdata):
        """Yield items of self._previous_dicts that are not in resultdata."""
        resultdata_titles = {d['title'] for d in resultdata if 'title' in d}
        for prev_title, prev_dict in self._previous_dicts.copy().items():
            if prev_title not in resultdata_titles:
                yield prev_dict
                del self._previous_dicts[prev_title]

    @staticmethod
    def _update_old_result_dict(old_dict, new_dict) -> None:
        """Update old result dict with new_dict."""
        for k, v in new_dict.items():
            if isinstance(v, (str, int)):
                old_dict.setdefault(k, v)
            elif isinstance(v, list):
                old_dict.setdefault(k, []).extend(v)
            else:
                raise ValueError(f'continued API result had an unexpected '
                                 f'type: {type(v).__name__}')


class ListGenerator(QueryGenerator):

    """Generator for queries of type action=query&list=foo.

    See the API documentation for types of lists that can be queried.
    Lists include both site-wide information (such as 'allpages') and
    page-specific information (such as 'backlinks').

    This generator yields a dict object for each member of the list
    returned by the API, with the format of the dict depending on the
    particular list command used. For those lists that contain page
    information, it may be easier to use the PageGenerator class
    instead, as that will convert the returned information into a Page
    object.
    """

    def __init__(self, listaction: str, **kwargs) -> None:
        """Initializer.

        Required and optional parameters are as for ``Request``, except that
        action=query is assumed and listaction is required.

        :param listaction: the "list=" type from api.php
        """
        kwargs = self._clean_kwargs(kwargs, list=listaction)
        super().__init__(**kwargs)


class LogEntryListGenerator(ListGenerator):

    """Generator for queries of list 'logevents'.

    Yields LogEntry objects instead of dicts.
    """

    def __init__(self, logtype=None, **kwargs) -> None:
        """Initializer."""
        super().__init__('logevents', **kwargs)

        from pywikibot import logentries
        self.entryFactory = logentries.LogEntryFactory(self.site, logtype)

    def result(self, pagedata):
        """Instantiate LogEntry from data from api."""
        return self.entryFactory.create(pagedata)

    def _check_result_namespace(self, result):
        """Return True if result.ns() is in self._namespaces."""
        return result.ns() in self._namespaces


def _update_pageid(page, pagedict: dict):
    """Update pageid."""
    if 'pageid' in pagedict:
        page._pageid = int(pagedict['pageid'])
    elif 'missing' in pagedict:
        page._pageid = 0  # Non-existent page
    else:
        # Something is wrong.
        if page.site.sametitle(page.title(), pagedict['title']) \
           and 'invalid' in pagedict:
            raise InvalidTitleError(f"{page}: {pagedict['invalidreason']}")
        if int(pagedict['ns']) < 0:
            raise UnsupportedPageError(page)
        raise RuntimeError(f"Page {pagedict['title']} has neither 'pageid'"
                           " nor 'missing' attribute")


def _update_contentmodel(page, pagedict: dict) -> None:
    """Update page content model."""
    page._contentmodel = pagedict.get('contentmodel')  # can be None

    if (page._contentmodel
            and page._contentmodel == 'proofread-page'
            and 'proofread' in pagedict):
        page._quality = pagedict['proofread']['quality']
        page._quality_text = pagedict['proofread']['quality_text']


def _update_protection(page, pagedict: dict) -> None:
    """Update page protection."""
    if 'restrictiontypes' in pagedict:
        page._applicable_protections = set(pagedict['restrictiontypes'])
    else:
        page._applicable_protections = None
    page._protection = {item['type']: (item['level'], item['expiry'])
                        for item in pagedict['protection']}


def _update_revisions(page, revisions) -> None:
    """Update page revisions."""
    for rev in revisions:
        revid = rev['revid']
        revision = pywikibot.page.Revision(**rev)
        # do not overwrite an existing Revision if there is no content
        if revid in page._revisions and revision.text is None:  # type: ignore[attr-defined]  # noqa: E501
            pass
        else:
            page._revisions[revid] = revision


def _update_templates(page, templates) -> None:
    """Update page templates."""
    templ_pages = {pywikibot.Page(page.site, tl['title']) for tl in templates}
    if hasattr(page, '_templates'):
        page._templates |= templ_pages
    else:
        page._templates = templ_pages


def _update_categories(page, categories):
    """Update page categories."""
    cat_pages = {pywikibot.Page(page.site, ct['title']) for ct in categories}
    if hasattr(page, '_categories'):
        page._categories |= cat_pages
    else:
        page._categories = cat_pages


def _update_langlinks(page, langlinks) -> None:
    """Update page langlinks.

    .. versionadded:: 9.3
       only add a language link if it is found in the family file.

    :meta public:
    """
    links = set()
    for langlink in langlinks:
        with suppress(UnknownSiteError):
            link = pywikibot.Link.langlinkUnsafe(langlink['lang'],
                                                 langlink['*'],
                                                 source=page.site)
            links.add(link)

    if hasattr(page, '_langlinks'):
        page._langlinks |= links
    else:
        page._langlinks = links


def _update_coordinates(page, coordinates) -> None:
    """Update page coordinates."""
    coords = []
    for co in coordinates:
        coord = pywikibot.Coordinate(lat=co['lat'],
                                     lon=co['lon'],
                                     typ=co.get('type', ''),
                                     name=co.get('name', ''),
                                     dim=int(co.get('dim', 0)) or None,
                                     globe=co['globe'],  # See [[gerrit:67886]]
                                     primary='primary' in co
                                     )
        coords.append(coord)
    page._coords = coords


def update_page(page: pywikibot.Page,
                pagedict: dict[str, Any],
                props: Iterable[str] | None = None) -> None:
    """Update attributes of *page*, based on query data in *pagedict*.

    :param page: object to be updated
    :param pagedict: the contents of a *page* element of a query
        response
    :param props: the property names which resulted in *pagedict*. If a
        missing value in *pagedict* can indicate both 'false' and
        'not present' the property which would make the value present
        must be in the *props* parameter.
    :raises InvalidTitleError: Page title is invalid
    :raises UnsupportedPageError: Page with namespace < 0 is not
        supported yet
    """
    _update_pageid(page, pagedict)
    _update_contentmodel(page, pagedict)

    props = props or []

    # test for pagedict content only and call updater function
    for element in ('coordinates', 'revisions'):
        if element in pagedict:
            updater = globals()['_update_' + element]
            updater(page, pagedict[element])

    # test for pagedict and props contents, call updater or set attribute
    for element in ('categories', 'langlinks', 'templates'):
        if element in pagedict:
            updater = globals()['_update_' + element]
            updater(page, pagedict[element])
        elif element in props:
            setattr(page, '_' + element, set())

    if 'info' in props:
        page._isredir = 'redirect' in pagedict

    if 'touched' in pagedict:
        page._timestamp = pagedict['touched']

    if 'protection' in pagedict:
        _update_protection(page, pagedict)

    if 'lastrevid' in pagedict:
        page.latest_revision_id = pagedict['lastrevid']

    if 'imageinfo' in pagedict:
        if not isinstance(page, pywikibot.FilePage):
            raise RuntimeError(
                f'"imageinfo" found but {page} is not a FilePage object')
        page._load_file_revisions(pagedict['imageinfo'])

    if 'categoryinfo' in pagedict:
        page._catinfo = pagedict['categoryinfo']

    if 'pageimage' in pagedict:
        page._pageimage = pywikibot.FilePage(page.site, pagedict['pageimage'])

    if 'pageprops' in pagedict:
        page._pageprops = pagedict['pageprops']
    elif 'pageprops' in props:
        page._pageprops = {}

    # preload is deprecated in MW 1.41, try preloadcontent first
    if 'preloadcontent' in pagedict:
        page._preloadedtext = pagedict['preloadcontent']['*']
    elif 'preload' in pagedict:
        page._preloadedtext = pagedict['preload']

    if 'lintId' in pagedict:
        page._lintinfo = pagedict
        page._lintinfo.pop('pageid')
        page._lintinfo.pop('title')
        page._lintinfo.pop('ns')

    if 'imageforpage' in props and 'imagesforpage' in pagedict:
        # proofreadpage will work always on dicts
        # it serves also as workaround for T352482
        page._imageforpage = pagedict['imagesforpage'] or {}
