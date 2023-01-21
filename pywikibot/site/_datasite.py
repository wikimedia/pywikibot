"""Objects representing API interface to Wikibase site."""
#
# (C) Pywikibot team, 2012-2023
#
# Distributed under the terms of the MIT license.
#
import datetime
import json
import uuid
from contextlib import suppress
from typing import Any, Dict, List, Optional
from warnings import warn

import pywikibot
from pywikibot.data import api
from pywikibot.exceptions import (
    APIError,
    EntityTypeUnknownError,
    IsRedirectPageError,
    NoPageError,
    NoWikibaseEntityError,
)
from pywikibot.site._apisite import APISite
from pywikibot.site._decorators import need_extension, need_right, need_version
from pywikibot.tools import merge_unique_dicts, remove_last_args
from pywikibot.tools.itertools import itergroup


__all__ = ('DataSite', )


class DataSite(APISite):

    """Wikibase data capable site."""

    def __init__(self, *args, **kwargs) -> None:
        """Initializer."""
        super().__init__(*args, **kwargs)
        self._item_namespace = None
        self._property_namespace = None
        self._type_to_class = {
            'item': pywikibot.ItemPage,
            'property': pywikibot.PropertyPage,
            'mediainfo': pywikibot.MediaInfo,
            'lexeme': pywikibot.LexemePage,
            'form': pywikibot.LexemeForm,
            'sense': pywikibot.LexemeSense,
        }

    def get_repo_for_entity_type(self, entity_type: str) -> 'DataSite':
        """
        Get the data repository for the entity type.

        When no foreign repository is defined for the entity type,
        the method returns this repository itself even if it does not
        support that entity type either.

        .. seealso:: https://www.mediawiki.org/wiki/Wikibase/Federation
        .. versionadded:: 8.0

        :raises ValueError: when invalid entity type was provided
        """
        if entity_type not in self._type_to_class:
            raise ValueError(f'Invalid entity type "{entity_type}"')
        entity_sources = self.entity_sources()
        if entity_type in entity_sources:
            return pywikibot.Site(
                *entity_sources[entity_type],
                interface='DataSite',
                user=self.username())
        return self

    def _cache_entity_namespaces(self) -> None:
        """Find namespaces for each known wikibase entity type."""
        self._entity_namespaces = {}
        for entity_type in self._type_to_class:
            for namespace in self.namespaces.values():
                if not hasattr(namespace, 'defaultcontentmodel'):
                    continue

                content_model = namespace.defaultcontentmodel
                if content_model == ('wikibase-' + entity_type):
                    self._entity_namespaces[entity_type] = namespace
                    break

    def get_namespace_for_entity_type(self, entity_type):
        """
        Return namespace for given entity type.

        :return: corresponding namespace
        :rtype: Namespace
        """
        if not hasattr(self, '_entity_namespaces'):
            self._cache_entity_namespaces()
        if entity_type in self._entity_namespaces:
            return self._entity_namespaces[entity_type]
        raise EntityTypeUnknownError(
            '{!r} does not support entity type "{}" '
            "or it doesn't have its own namespace"
            .format(self, entity_type))

    @property
    def item_namespace(self):
        """
        Return namespace for items.

        :return: item namespace
        :rtype: Namespace
        """
        if self._item_namespace is None:
            self._item_namespace = self.get_namespace_for_entity_type('item')
        return self._item_namespace

    @property
    def property_namespace(self):
        """
        Return namespace for properties.

        :return: property namespace
        :rtype: Namespace
        """
        if self._property_namespace is None:
            self._property_namespace = self.get_namespace_for_entity_type(
                'property')
        return self._property_namespace

    def get_entity_for_entity_id(self, entity_id):
        """
        Return a new instance for given entity id.

        :raises pywikibot.exceptions.NoWikibaseEntityError: there is no entity
            with the id
        :return: a WikibaseEntity subclass
        :rtype: WikibaseEntity
        """
        for cls in self._type_to_class.values():
            if cls.is_valid_id(entity_id):
                return cls(self, entity_id)

        entity = pywikibot.page.WikibaseEntity(self, entity_id)
        raise NoWikibaseEntityError(entity)

    @property
    @need_version('1.28-wmf.3')
    def sparql_endpoint(self):
        """
        Return the sparql endpoint url, if any has been set.

        :return: sparql endpoint url
        :rtype: str|None
        """
        return self.siteinfo['general'].get('wikibase-sparql')

    @property
    @need_version('1.28-wmf.23')
    def concept_base_uri(self):
        """
        Return the base uri for concepts/entities.

        :return: concept base uri
        :rtype: str
        """
        return self.siteinfo['general']['wikibase-conceptbaseuri']

    def geo_shape_repository(self):
        """Return Site object for the geo-shapes repository e.g. commons."""
        url = self.siteinfo['general'].get('wikibase-geoshapestoragebaseurl')
        if url:
            return pywikibot.Site(url=url, user=self.username())

        return None

    def tabular_data_repository(self):
        """Return Site object for the tabular-datas repository e.g. commons."""
        url = self.siteinfo['general'].get(
            'wikibase-tabulardatastoragebaseurl')
        if url:
            return pywikibot.Site(url=url, user=self.username())

        return None

    def loadcontent(self, identification, *props):
        """
        Fetch the current content of a Wikibase item.

        This is called loadcontent since
        wbgetentities does not support fetching old
        revisions. Eventually this will get replaced by
        an actual loadrevisions.

        :param identification: Parameters used to identify the page(s)
        :type identification: dict
        :param props: the optional properties to fetch.
        """
        params = merge_unique_dicts(identification, action='wbgetentities',
                                    # TODO: When props is empty it results in
                                    # an empty string ('&props=') but it should
                                    # result in a missing entry.
                                    props=props if props else False)
        req = self.simple_request(**params)
        data = req.submit()
        if 'success' not in data:
            raise APIError(data['errors'], '')
        return data['entities']

    def preload_entities(self, pagelist, groupsize: int = 50):
        """
        Yield subclasses of WikibaseEntity's with content prefilled.

        Note that pages will be iterated in a different order
        than in the underlying pagelist.

        :param pagelist: an iterable that yields either WikibaseEntity objects,
                         or Page objects linked to an ItemPage.
        :param groupsize: how many pages to query at a time
        """
        if not hasattr(self, '_entity_namespaces'):
            self._cache_entity_namespaces()
        for sublist in itergroup(pagelist, groupsize):
            req = {'ids': [], 'titles': [], 'sites': []}
            for p in sublist:
                if isinstance(p, pywikibot.page.WikibaseEntity):
                    ident = p._defined_by()
                    for key in ident:
                        req[key].append(ident[key])
                else:
                    if p.site == self and p.namespace() in (
                            self._entity_namespaces.values()):
                        req['ids'].append(p.title(with_ns=False))
                    else:
                        assert p.site.has_data_repository, \
                            'Site must have a data repository'
                        req['sites'].append(p.site.dbName())
                        req['titles'].append(p._link._text)

            req = self.simple_request(action='wbgetentities', **req)
            data = req.submit()
            for entity in data['entities']:
                if 'missing' in data['entities'][entity]:
                    continue
                cls = self._type_to_class[data['entities'][entity]['type']]
                page = cls(self, entity)
                # No api call is made because item._content is given
                page._content = data['entities'][entity]
                with suppress(IsRedirectPageError):
                    page.get()  # cannot provide get_redirect=True (T145971)
                yield page

    def getPropertyType(self, prop):
        """
        Obtain the type of a property.

        This is used specifically because we can cache
        the value for a much longer time (near infinite).
        """
        params = {'action': 'wbgetentities', 'ids': prop.getID(),
                  'props': 'datatype'}
        expiry = datetime.timedelta(days=365 * 100)
        # Store it for 100 years
        req = self._request(expiry=expiry, parameters=params)
        data = req.submit()

        # the IDs returned from the API can be upper or lowercase, depending
        # on the version. See bug T55894 for more information.
        try:
            dtype = data['entities'][prop.getID()]['datatype']
        except KeyError:
            dtype = data['entities'][prop.getID().lower()]['datatype']

        return dtype

    @need_right('edit')
    def editEntity(self, entity, data, bot: bool = True, **kwargs):
        """Edit entity.

        .. note:: This method is unable to create entities other than
           'item' if dict with API parameters was passed to 'entity'
           parameter.

        :param entity: Page to edit, or dict with API parameters
            to use for entity identification
        :type entity: WikibaseEntity or dict
        :param data: data updates
        :type data: dict
        :param bot: Whether to mark the edit as a bot edit
        :return: New entity data
        :rtype: dict
        """
        # this changes the reference to a new object
        data = dict(data)
        if isinstance(entity, pywikibot.page.WikibaseEntity):
            params = entity._defined_by(singular=True)
            if 'id' in params and params['id'] == '-1':
                del params['id']
            if not params:
                params['new'] = entity.entity_type
                data_for_new_entity = entity.get_data_for_new_entity()
                data.update(data_for_new_entity)
        else:
            if 'id' in entity and entity['id'] == '-1':
                del entity['id']
            params = dict(entity)
            if not params:  # If no identification was provided
                params['new'] = 'item'

        params['action'] = 'wbeditentity'
        if bot:
            params['bot'] = 1
        if 'baserevid' in kwargs and kwargs['baserevid']:
            params['baserevid'] = kwargs['baserevid']
        params['token'] = self.tokens['csrf']

        for arg in kwargs:
            if arg in ['clear', 'summary']:
                params[arg] = kwargs[arg]
            elif arg != 'baserevid':
                warn(f'Unknown wbeditentity parameter {arg} ignored',
                     UserWarning, 2)

        params['data'] = json.dumps(data)
        req = self.simple_request(**params)
        return req.submit()

    @need_right('edit')
    def addClaim(self,
                 entity: 'pywikibot.page.WikibaseEntity',
                 claim: 'pywikibot.page.Claim',
                 bot: bool = True,
                 summary: Optional[str] = None) -> None:
        """
        Add a claim.

        :param entity: Entity to modify
        :param claim: Claim to be added
        :param bot: Whether to mark the edit as a bot edit
        :param summary: Edit summary
        """
        claim.snak = entity.getID() + '$' + str(uuid.uuid4())
        params = {'action': 'wbsetclaim',
                  'claim': json.dumps(claim.toJSON()),
                  'baserevid': entity.latest_revision_id,
                  'summary': summary,
                  'token': self.tokens['csrf'],
                  'bot': bot,
                  }
        req = self.simple_request(**params)
        data = req.submit()
        # Update the item
        if claim.getID() in entity.claims:
            entity.claims[claim.getID()].append(claim)
        else:
            entity.claims[claim.getID()] = [claim]
        entity.latest_revision_id = data['pageinfo']['lastrevid']

    @need_right('edit')
    def changeClaimTarget(self, claim, snaktype: str = 'value',
                          bot: bool = True, summary=None):
        """
        Set the claim target to the value of the provided claim target.

        :param claim: The source of the claim target value
        :type claim: pywikibot.Claim
        :param snaktype: An optional snaktype ('value', 'novalue' or
            'somevalue'). Default: 'value'
        :param bot: Whether to mark the edit as a bot edit
        :param summary: Edit summary
        :type summary: str
        """
        if claim.isReference or claim.isQualifier:
            raise NotImplementedError
        if not claim.snak:
            # We need to already have the snak value
            raise NoPageError(claim)
        params = {'action': 'wbsetclaimvalue', 'claim': claim.snak,
                  'snaktype': snaktype, 'summary': summary, 'bot': bot,
                  'token': self.tokens['csrf']}

        if snaktype == 'value':
            params['value'] = json.dumps(claim._formatValue())

        params['baserevid'] = claim.on_item.latest_revision_id
        req = self.simple_request(**params)
        return req.submit()

    @need_right('edit')
    def save_claim(self, claim: 'pywikibot.page.Claim',
                   summary: Optional[str] = None,
                   bot: bool = True):
        """
        Save the whole claim to the wikibase site.

        :param claim: The claim to save
        :param bot: Whether to mark the edit as a bot edit
        :param summary: Edit summary
        """
        if claim.isReference or claim.isQualifier:
            raise NotImplementedError
        if not claim.snak:
            # We need to already have the snak value
            raise NoPageError(claim)
        params = {'action': 'wbsetclaim',
                  'claim': json.dumps(claim.toJSON()),
                  'token': self.tokens['csrf'],
                  'baserevid': claim.on_item.latest_revision_id,
                  'summary': summary,
                  'bot': bot,
                  }

        req = self.simple_request(**params)
        data = req.submit()
        claim.on_item.latest_revision_id = data['pageinfo']['lastrevid']
        return data

    @need_right('edit')
    @remove_last_args(['baserevid'])  # since 7.0.0
    def editSource(self, claim, source,
                   new: bool = False,
                   bot: bool = True,
                   summary: Optional[str] = None):
        """Create/Edit a source.

        .. versionchanged:: 7.0
           deprecated `baserevid` parameter was removed

        :param claim: A Claim object to add the source to
        :type claim: pywikibot.Claim
        :param source: A Claim object to be used as a source
        :type source: pywikibot.Claim
        :param new: Whether to create a new one if the "source" already exists
        :param bot: Whether to mark the edit as a bot edit
        :param summary: Edit summary
        """
        if claim.isReference or claim.isQualifier:
            raise ValueError('The claim cannot have a source.')
        params = {'action': 'wbsetreference', 'statement': claim.snak,
                  'baserevid': claim.on_item.latest_revision_id,
                  'summary': summary, 'bot': bot, 'token': self.tokens['csrf']}

        # build up the snak
        if isinstance(source, list):
            sources = source
        else:
            sources = [source]

        snak = {}
        for sourceclaim in sources:
            datavalue = sourceclaim._formatDataValue()
            valuesnaks = snak.get(sourceclaim.getID(), [])
            valuesnaks.append({
                'snaktype': 'value',
                'property': sourceclaim.getID(),
                'datavalue': datavalue,
            })

            snak[sourceclaim.getID()] = valuesnaks
            # set the hash if the source should be changed.
            # if present, all claims of one source have the same hash
            if not new and hasattr(sourceclaim, 'hash'):
                params['reference'] = sourceclaim.hash
        params['snaks'] = json.dumps(snak)

        req = self.simple_request(**params)
        return req.submit()

    @need_right('edit')
    @remove_last_args(['baserevid'])  # since 7.0.0
    def editQualifier(self, claim, qualifier,
                      new: bool = False,
                      bot: bool = True,
                      summary: Optional[str] = None):
        """Create/Edit a qualifier.

        .. versionchanged:: 7.0
           deprecated `baserevid` parameter was removed

        :param claim: A Claim object to add the qualifier to
        :type claim: pywikibot.Claim
        :param qualifier: A Claim object to be used as a qualifier
        :type qualifier: pywikibot.Claim
        :param new: Whether to create a new one if the "qualifier"
            already exists
        :param bot: Whether to mark the edit as a bot edit
        :param summary: Edit summary
        """
        if claim.isReference or claim.isQualifier:
            raise ValueError('The claim cannot have a qualifier.')
        params = {'action': 'wbsetqualifier', 'claim': claim.snak,
                  'baserevid': claim.on_item.latest_revision_id,
                  'summary': summary, 'bot': bot}

        if (not new and hasattr(qualifier, 'hash')
                and qualifier.hash is not None):
            params['snakhash'] = qualifier.hash
        params['token'] = self.tokens['csrf']
        # build up the snak
        if qualifier.getSnakType() == 'value':
            params['value'] = json.dumps(qualifier._formatValue())
        params['snaktype'] = qualifier.getSnakType()
        params['property'] = qualifier.getID()

        req = self.simple_request(**params)
        return req.submit()

    @need_right('edit')
    @remove_last_args(['baserevid'])  # since 7.0.0
    def removeClaims(self, claims,
                     bot: bool = True,
                     summary: Optional[str] = None):
        """Remove claims.

        .. versionchanged:: 7.0
           deprecated `baserevid` parameter was removed

        :param claims: Claims to be removed
        :type claims: List[pywikibot.Claim]
        :param bot: Whether to mark the edit as a bot edit
        :type bot: bool
        :param summary: Edit summary
        :type summary: str
        """
        # Check on_item for all additional claims
        items = {claim.on_item for claim in claims if claim.on_item}
        assert len(items) == 1
        baserevid = items.pop().latest_revision_id

        params = {
            'action': 'wbremoveclaims', 'baserevid': baserevid,
            'summary': summary,
            'bot': bot,
            'claim': '|'.join(claim.snak for claim in claims),
            'token': self.tokens['csrf'],
        }

        req = self.simple_request(**params)
        return req.submit()

    @need_right('edit')
    @remove_last_args(['baserevid'])  # since 7.0.0
    def removeSources(self, claim, sources,
                      bot: bool = True,
                      summary: Optional[str] = None):
        """Remove sources.

        .. versionchanged:: 7.0
           deprecated `baserevid` parameter was removed

        :param claim: A Claim object to remove the sources from
        :type claim: pywikibot.Claim
        :param sources: A list of Claim objects that are sources
        :type sources: list
        :param bot: Whether to mark the edit as a bot edit
        :param summary: Edit summary
        """
        params = {
            'action': 'wbremovereferences',
            'baserevid': claim.on_item.latest_revision_id,
            'summary': summary, 'bot': bot,
            'statement': claim.snak,
            'references': '|'.join(source.hash for source in sources),
            'token': self.tokens['csrf'],
        }

        req = self.simple_request(**params)
        return req.submit()

    @need_right('edit')
    @remove_last_args(['baserevid'])  # since 7.0.0
    def remove_qualifiers(self, claim, qualifiers,
                          bot: bool = True,
                          summary: Optional[str] = None):
        """Remove qualifiers.

        .. versionchanged:: 7.0
           deprecated `baserevid` parameter was removed

        :param claim: A Claim object to remove the qualifier from
        :type claim: pywikibot.Claim
        :param qualifiers: Claim objects currently used as a qualifiers
        :type qualifiers: List[pywikibot.Claim]
        :param bot: Whether to mark the edit as a bot edit
        :param summary: Edit summary
        """
        params = {
            'action': 'wbremovequalifiers',
            'claim': claim.snak,
            'baserevid': claim.on_item.latest_revision_id,
            'summary': summary,
            'bot': bot,
            'qualifiers': [qualifier.hash for qualifier in qualifiers],
            'token': self.tokens['csrf']
        }

        req = self.simple_request(**params)
        return req.submit()

    @need_right('edit')
    def linkTitles(self, page1, page2, bot: bool = True):
        """
        Link two pages together.

        :param page1: First page to link
        :type page1: pywikibot.Page
        :param page2: Second page to link
        :type page2: pywikibot.Page
        :param bot: Whether to mark the edit as a bot edit
        :return: dict API output
        :rtype: dict
        """
        params = {
            'action': 'wblinktitles',
            'tosite': page1.site.dbName(),
            'totitle': page1.title(),
            'fromsite': page2.site.dbName(),
            'fromtitle': page2.title(),
            'token': self.tokens['csrf']
        }
        if bot:
            params['bot'] = 1
        req = self.simple_request(**params)
        return req.submit()

    @need_right('item-merge')
    def mergeItems(self, from_item, to_item, ignore_conflicts=None,
                   summary=None, bot: bool = True):
        """
        Merge two items together.

        :param from_item: Item to merge from
        :type from_item: pywikibot.ItemPage
        :param to_item: Item to merge into
        :type to_item: pywikibot.ItemPage
        :param ignore_conflicts: Which type of conflicts
            ('description', 'sitelink', and 'statement')
            should be ignored
        :type ignore_conflicts: list of str
        :param summary: Edit summary
        :type summary: str
        :param bot: Whether to mark the edit as a bot edit
        :return: dict API output
        :rtype: dict
        """
        params = {
            'action': 'wbmergeitems',
            'fromid': from_item.getID(),
            'toid': to_item.getID(),
            'ignoreconflicts': ignore_conflicts,
            'token': self.tokens['csrf'],
            'summary': summary,
        }
        if bot:
            params['bot'] = 1
        req = self.simple_request(**params)
        return req.submit()

    @need_right('item-merge')
    @need_extension('WikibaseLexeme')
    def mergeLexemes(self, from_lexeme, to_lexeme, summary=None, *,
                     bot: bool = True) -> dict:
        """
        Merge two lexemes together.

        :param from_lexeme: Lexeme to merge from
        :type from_lexeme: pywikibot.LexemePage
        :param to_lexeme: Lexeme to merge into
        :type to_lexeme: pywikibot.LexemePage
        :param summary: Edit summary
        :type summary: str
        :keyword bot: Whether to mark the edit as a bot edit
        :return: dict API output
        """
        params = {
            'action': 'wblmergelexemes',
            'source': from_lexeme.getID(),
            'target': to_lexeme.getID(),
            'token': self.tokens['csrf'],
            'summary': summary,
        }
        if bot:
            params['bot'] = 1
        req = self.simple_request(**params)
        return req.submit()

    @need_right('item-redirect')
    def set_redirect_target(self, from_item, to_item, bot: bool = True):
        """
        Make a redirect to another item.

        :param to_item: title of target item.
        :type to_item: pywikibot.ItemPage
        :param from_item: Title of the item to be redirected.
        :type from_item: pywikibot.ItemPage
        :param bot: Whether to mark the edit as a bot edit
        """
        params = {
            'action': 'wbcreateredirect',
            'from': from_item.getID(),
            'to': to_item.getID(),
            'token': self.tokens['csrf'],
            'bot': bot,
        }
        req = self.simple_request(**params)
        return req.submit()

    def search_entities(self, search: str, language: str,
                        total: Optional[int] = None, **kwargs):
        """
        Search for pages or properties that contain the given text.

        :param search: Text to find.
        :param language: Language to search in.
        :param total: Maximum number of pages to retrieve in total, or
            None in case of no limit.
        :return: 'search' list from API output.
        :rtype: Generator
        """
        lang_codes = self._paraminfo.parameter('wbsearchentities',
                                               'language')['type']
        if language not in lang_codes:
            raise ValueError('Data site used does not support provided '
                             'language.')

        if 'site' in kwargs:
            if kwargs['site'].sitename != self.sitename:
                raise ValueError('The site given in the kwargs is different.')

            warn('search_entities should not get a site via kwargs.',
                 UserWarning, 2)
            del kwargs['site']

        parameters = dict(search=search, language=language, **kwargs)
        gen = self._generator(api.APIGenerator,
                              type_arg='wbsearchentities',
                              data_name='search',
                              total=total, parameters=parameters)
        return gen

    def parsevalue(self, datatype: str, values: List[str],
                   options: Optional[Dict[str, Any]] = None,
                   language: Optional[str] = None,
                   validate: bool = False) -> List[Any]:
        """
        Send data values to the wikibase parser for interpretation.

        .. versionadded:: 7.5
        .. seealso:: `wbparsevalue API
           <https://www.wikidata.org/w/api.php?action=help&modules=wbparsevalue>`_

        :param datatype: datatype of the values being parsed. Refer the
            API for a valid datatype.
        :param values: list of values to be parsed
        :param options: any additional options for wikibase parser
            (for time, 'precision' should be specified)
        :param language: code of the language to parse the value in
        :param validate: whether parser should provide data validation as well
            as parsing
        :return: list of parsed values
        :raises ValueError: parsing failed due to some invalid input values
        """
        params = {
            'action': 'wbparsevalue',
            'datatype': datatype,
            'values': values,
            'options': json.dumps(options or {}),
            'validate': validate,
            'uselang': language or 'en',
        }
        req = self.simple_request(**params)
        try:
            data = req.submit()
        except APIError as e:
            if e.code.startswith('wikibase-parse-error'):
                for err in e.other['results']:
                    if 'error' in err:
                        pywikibot.error('{error-info} for value {raw!r}, '
                                        '{expected-format!r} format expected'
                                        .format_map(err))
                raise ValueError(e) from None
            raise

        if 'results' not in data:
            raise RuntimeError("Unexpected missing 'results' in query data\n{}"
                               .format(data))

        results = []
        for result_hash in data['results']:
            if 'value' not in result_hash:
                # There should be an APIError occurred already
                raise RuntimeError("Unexpected missing 'value' in query data:"
                                   '\n{}'.format(result_hash))
            results.append(result_hash['value'])
        return results

    @need_right('edit')
    def _wbset_action(self, itemdef, action: str, action_data,
                      **kwargs) -> dict:
        """
        Execute wbset{action} on a Wikibase entity.

        Supported actions are:
            wbsetaliases, wbsetdescription, wbsetlabel and wbsetsitelink

        wbsetaliases:
            dict shall have the following structure:

            .. code-block::

               {
                   'language': value (str),
                   'add': list of language codes (str),
                   'remove': list of language codes (str),
                   'set' list of language codes (str)
                }

            'add' and 'remove' are alternative to 'set'

        wbsetdescription and wbsetlabel:
            dict shall have keys 'language', 'value'

        wbsetsitelink:
            dict shall have keys 'linksite', 'linktitle' and
            optionally 'badges'

        :param itemdef: Entity to modify or create
        :type itemdef: str, WikibaseEntity or Page connected to such item
        :param action: wbset{action} to perform:
            'wbsetaliases', 'wbsetdescription', 'wbsetlabel', 'wbsetsitelink'
        :param action_data: data to be used in API request, see API help
        :type action_data: SiteLink or dict
        :keyword bot: Whether to mark the edit as a bot edit, default is True
        :type bot: bool
        :keyword tags: Change tags to apply with the edit
        :type tags: list of str
        :return: query result
        :raises: AssertionError, TypeError
        """
        def format_sitelink(sitelink):
            """Convert SiteLink to a dict accepted by wbsetsitelink API."""
            if isinstance(sitelink, pywikibot.page.SiteLink):
                _dict = {
                    'linksite': sitelink._sitekey,
                    'linktitle': sitelink._rawtitle,
                    'badges': '|'.join([b.title() for b in sitelink.badges]),
                }
            else:
                _dict = sitelink

            return _dict

        def prepare_data(action, data):
            """Prepare data as expected by API."""
            if action == 'wbsetaliases':
                res = data
                keys = set(res)
                assert keys < {'language', 'add', 'remove', 'set'}
                assert 'language' in keys
                assert ({'add', 'remove', 'set'} & keys)
                assert ({'add', 'set'} >= keys)
                assert ({'remove', 'set'} >= keys)
            elif action in ('wbsetlabel', 'wbsetdescription'):
                res = data
                keys = set(res)
                assert keys == {'language', 'value'}
            elif action == 'wbsetsitelink':
                res = format_sitelink(data)
                keys = set(res)
                assert keys >= {'linksite'}
                assert keys <= {'linksite', 'linktitle', 'badges'}
            else:
                raise ValueError('Something has gone wrong ...')

            return res

        # Supported actions
        assert action in ('wbsetaliases', 'wbsetdescription',
                          'wbsetlabel', 'wbsetsitelink'), \
            f'action {action} not supported.'

        # prefer ID over (site, title)
        if isinstance(itemdef, str):
            itemdef = self.get_entity_for_entity_id(itemdef)
        elif isinstance(itemdef, pywikibot.Page):
            itemdef = pywikibot.ItemPage.fromPage(itemdef, lazy_load=True)
        elif not isinstance(itemdef, pywikibot.page.WikibaseEntity):
            raise TypeError('itemdef shall be str, WikibaseEntity or Page')

        params = itemdef._defined_by(singular=True)
        # TODO: support 'new'
        baserevid = kwargs.pop(
            'baserevid',
            itemdef.latest_revision_id if 'id' in params else 0
        )
        params.update(
            {'baserevid': baserevid,
             'action': action,
             'token': self.tokens['csrf'],
             'bot': kwargs.pop('bot', True),
             })
        params.update(prepare_data(action, action_data))

        for arg in kwargs:
            if arg in ['summary', 'tags']:
                params[arg] = kwargs[arg]
            else:
                warn('Unknown parameter {} for action {}, ignored'
                     .format(arg, action), UserWarning, 2)

        req = self.simple_request(**params)
        return req.submit()

    def wbsetaliases(self, itemdef, aliases, **kwargs):
        """
        Set aliases for a single Wikibase entity.

        See self._wbset_action() for parameters
        """
        return self._wbset_action(itemdef, 'wbsetaliases', aliases, **kwargs)

    def wbsetdescription(self, itemdef, description, **kwargs):
        """
        Set description for a single Wikibase entity.

        See self._wbset_action()
        """
        return self._wbset_action(itemdef, 'wbsetdescription', description,
                                  **kwargs)

    def wbsetlabel(self, itemdef, label, **kwargs):
        """
        Set label for a single Wikibase entity.

        See self._wbset_action() for parameters
        """
        return self._wbset_action(itemdef, 'wbsetlabel', label, **kwargs)

    def wbsetsitelink(self, itemdef, sitelink, **kwargs):
        """
        Set, remove or modify a sitelink on a Wikibase item.

        See self._wbset_action() for parameters
        """
        return self._wbset_action(itemdef, 'wbsetsitelink', sitelink, **kwargs)

    @need_right('edit')
    @need_extension('WikibaseLexeme')
    def add_form(self, lexeme, form, *, bot: bool = True,
                 baserevid=None) -> dict:
        """
        Add a form.

        :param lexeme: Lexeme to modify
        :type lexeme: pywikibot.LexemePage
        :param form: Form to be added
        :type form: pywikibot.LexemeForm
        :keyword bot: Whether to mark the edit as a bot edit
        :keyword baserevid: Base revision id override, used to detect
            conflicts.
        :type baserevid: long
        """
        params = {
            'action': 'wbladdform',
            'lexemeId': lexeme.getID(),
            'data': json.dumps(form.toJSON()),
            'bot': bot,
            'token': self.tokens['csrf'],
        }
        if baserevid:
            params['baserevid'] = baserevid
        req = self.simple_request(**params)
        return req.submit()

    @need_right('edit')
    @need_extension('WikibaseLexeme')
    def remove_form(self, form, *, bot: bool = True, baserevid=None) -> dict:
        """
        Remove a form.

        :param form: Form to be removed
        :type form: pywikibot.LexemeForm
        :keyword bot: Whether to mark the edit as a bot edit
        :keyword baserevid: Base revision id override, used to detect
            conflicts.
        :type baserevid: long
        """
        params = {
            'action': 'wblremoveform',
            'id': form.getID(),
            'bot': bot,
            'token': self.tokens['csrf'],
        }
        if baserevid:
            params['baserevid'] = baserevid
        req = self.simple_request(**params)
        return req.submit()

    @need_right('edit')
    @need_extension('WikibaseLexeme')
    def edit_form_elements(self, form, data, *, bot: bool = True,
                           baserevid=None) -> dict:
        """
        Edit lexeme form elements.

        :param form: Form
        :type form: pywikibot.LexemeForm
        :param data: data updates
        :type data: dict
        :keyword bot: Whether to mark the edit as a bot edit
        :keyword baserevid: Base revision id override, used to detect
            conflicts.
        :type baserevid: long
        :return: New form data
        """
        params = {
            'action': 'wbleditformelements',
            'formId': form.getID(),
            'data': json.dumps(data),
            'bot': bot,
            'token': self.tokens['csrf'],
        }
        if baserevid:
            params['baserevid'] = baserevid
        req = self.simple_request(**params)
        return req.submit()
