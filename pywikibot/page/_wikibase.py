"""Objects representing various types of Wikibase pages and structures.

This module also includes objects:

* Claim: an instance of a semantic assertion.
* MediaInfo: Interface for MediaInfo entities on image repository
* Property: a type of semantic data.
* WikibaseEntity: base interface for Wikibase entities.
"""
#
# (C) Pywikibot team, 2013-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import json as jsonlib
import re
from collections import OrderedDict, defaultdict
from contextlib import suppress
from itertools import chain
from typing import TYPE_CHECKING, Any

import pywikibot
from pywikibot.exceptions import (
    APIError,
    EntityTypeUnknownError,
    Error,
    InterwikiRedirectPageError,
    InvalidTitleError,
    IsNotRedirectPageError,
    IsRedirectPageError,
    NoPageError,
    NoSiteLinkError,
    NoWikibaseEntityError,
    WikiBaseError,
)
from pywikibot.family import Family
from pywikibot.page._collections import (
    AliasesDict,
    ClaimCollection,
    LanguageDict,
    SiteLinkCollection,
    SubEntityCollection,
)
from pywikibot.page._decorators import allow_asynchronous
from pywikibot.page._filepage import FilePage
from pywikibot.page._page import BasePage
from pywikibot.site import DataSite, Namespace
from pywikibot.tools import cached, deprecated_args, first_upper


__all__ = (
    'Claim',
    'ItemPage',
    'LexemeForm',
    'LexemePage',
    'LexemeSense',
    'MediaInfo',
    'Property',
    'PropertyPage',
    'WikibaseEntity',
    'WikibasePage',
)

if TYPE_CHECKING:
    LANGUAGE_IDENTIFIER = str | pywikibot.site.APISite
    ALIASES_TYPE = dict[LANGUAGE_IDENTIFIER, list[str]]
    LANGUAGE_TYPE = dict[LANGUAGE_IDENTIFIER, str]
    SITELINK_TYPE = (
        pywikibot.page.BasePage
        | pywikibot.page.BaseLink
        | dict[str, str]
    )
    ENTITY_DATA_TYPE = dict[str, LANGUAGE_TYPE | ALIASES_TYPE | SITELINK_TYPE]


class WikibaseEntity:

    """The base interface for Wikibase entities.

    Each entity is identified by a data repository it belongs to
    and an identifier.

    :cvar DATA_ATTRIBUTES: dictionary which maps data attributes
        (e.g., 'labels', 'claims') to appropriate collection classes
        (e.g., :class:`LanguageDict<pywikibot.page._collections.LanguageDict>`,
        :class:`ClaimCollection<pywikibot.page._collections.ClaimCollection>`)

    :cvar entity_type: entity type identifier
    :type entity_type: str

    :cvar title_pattern: regular expression which matches all possible
        entity ids for this entity type
    :type title_pattern: str
    """

    DATA_ATTRIBUTES: dict[str, Any] = {}

    def __init__(self, repo, id_: str | None = None) -> None:
        """Initializer.

        :param repo: Entity repository.
        :type repo: DataSite
        :param id_: Entity identifier.
        :type id_: str or None, -1 and None mean non-existing
        """
        self.repo = repo
        self.id = id_ if id_ is not None else '-1'
        if self.id != '-1' and not self.is_valid_id(self.id):
            raise InvalidTitleError(
                f"'{self.id}' is not a valid {self.entity_type} page title")

    def __repr__(self) -> str:
        if self.id != '-1':
            return (f'pywikibot.page.{type(self).__name__}'
                    f'({self.repo!r}, {self.id!r})')
        return f'pywikibot.page.{self.__class__.__name__}({self.repo!r})'

    @classmethod
    def is_valid_id(cls, entity_id: str) -> bool:
        """Whether the string can be a valid id of the entity type.

        :param entity_id: The ID to test.
        """
        if not hasattr(cls, 'title_pattern'):
            return True

        return bool(re.fullmatch(cls.title_pattern, entity_id))

    def __getattr__(self, name):
        if name in self.DATA_ATTRIBUTES:
            if self.getID() == '-1':
                self._initialize_empty()
                return getattr(self, name)
            return self.get()[name]

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def _initialize_empty(self):
        for key, cls in self.DATA_ATTRIBUTES.items():
            setattr(self, key, cls.new_empty(self.repo))

    def _defined_by(self, singular: bool = False) -> dict[str, str]:
        """Function to provide the API parameters to identify the entity.

        An empty dict is returned if the entity has not been created yet.

        :param singular: Whether the parameter names should use the singular
            form
        :return: API parameters
        """
        params = {}
        if self.id != '-1':
            if singular:
                params['id'] = self.id
            else:
                params['ids'] = self.id
        return params

    def getID(self, numeric: bool = False) -> int | str:
        """Get the identifier of this entity.

        :param numeric: Strip the first letter and return an int
        """
        if numeric:
            return int(self.id[1:]) if self.id != '-1' else -1
        return self.id

    def get_data_for_new_entity(self) -> dict:
        """Return data required for creation of a new entity.

        Override it if you need.
        """
        return {}

    def toJSON(self, diffto: dict | None = None) -> dict:
        """Create JSON suitable for Wikibase API.

        When diffto is provided, JSON representing differences
        to the provided data is created.

        :param diffto: JSON containing entity data
        """
        data = {}
        for key in self.DATA_ATTRIBUTES:
            attr = getattr(self, key, None)
            if attr is None:
                continue
            if diffto:
                value = attr.toJSON(diffto=diffto.get(key))
            else:
                value = attr.toJSON()
            if value:
                data[key] = value
        return data

    @classmethod
    def _normalizeData(cls, data: dict) -> dict:
        """Helper function to expand data into the Wikibase API structure.

        :param data: The dict to normalize
        :return: The dict with normalized data
        """
        norm_data = {}
        for key, attr in cls.DATA_ATTRIBUTES.items():
            if key in data:
                norm_data[key] = attr.normalizeData(data[key])
        return norm_data

    @property
    def latest_revision_id(self) -> int | None:
        """Get the revision id for the most recent revision of the entity.

        :rtype: int or None if it cannot be determined
        :raise NoWikibaseEntityError: if the entity doesn't exist
        """
        if not hasattr(self, '_revid'):
            # FIXME: unlike BasePage.latest_revision_id, this raises
            # exception when entity is redirect, cannot use get_redirect
            self.get()
        return self._revid

    @latest_revision_id.setter
    def latest_revision_id(self, value: int | None) -> None:
        self._revid = value

    @latest_revision_id.deleter
    def latest_revision_id(self) -> None:
        if hasattr(self, '_revid'):
            del self._revid

    def exists(self) -> bool:
        """Determine if an entity exists in the data repository."""
        if not hasattr(self, '_content'):
            try:
                self.get()
                return True
            except NoWikibaseEntityError:
                return False
        return 'missing' not in self._content

    def get(self, force: bool = False) -> dict:
        """Fetch all entity data and cache it.

        :param force: override caching
        :raise NoWikibaseEntityError: if this entity doesn't exist
        :return: actual data which entity holds
        """
        if force or not hasattr(self, '_content'):
            identification = self._defined_by()
            if not identification:
                raise NoWikibaseEntityError(self)

            try:
                data = self.repo.loadcontent(identification)
            except APIError as err:
                if err.code == 'no-such-entity':
                    raise NoWikibaseEntityError(self)
                raise
            item_index, content = data.popitem()
            self.id = item_index
            self._content = content
        if 'missing' in self._content:
            raise NoWikibaseEntityError(self)

        self.latest_revision_id = self._content.get('lastrevid')

        data = {}

        # This initializes all data
        for key, cls in self.DATA_ATTRIBUTES.items():
            value = cls.fromJSON(self._content.get(key, {}), self.repo)
            setattr(self, key, value)
            data[key] = value
            # fixme: need better handling for this
            if key in ['claims', 'statements']:
                value.set_on_item(self)

        return data

    def editEntity(
        self,
        data: ENTITY_DATA_TYPE | None = None,
        **kwargs
    ) -> None:
        """Edit an entity using Wikibase ``wbeditentity`` API.

        This function is wrapped around by:
         - :meth:`WikibasePage.editLabels`
         - :meth:`WikibasePage.editDescriptions`
         - :meth:`WikibasePage.editAliases`
         - :meth:`ItemPage.setSitelinks`

         .. seealso:: :meth:`WikibasePage.editEntity`

         .. versionchanged:: 8.0.1
            Copy snak IDs/hashes (:phab:`T327607`)

        :param data: Data to be saved
        """
        update_self = False
        if data is None:
            data = self.toJSON(diffto=getattr(self, '_content', None))
            # We only want to copy the IDs from the updates
            # if data was not passed in.
            update_self = True
        else:
            data = self._normalizeData(data)

        baserevid = getattr(self, '_revid', None)

        updates = self.repo.editEntity(
            self, data, baserevid=baserevid, **kwargs)

        # the attribute may have been unset in ItemPage
        if getattr(self, 'id', '-1') == '-1':
            self.__init__(self.repo, updates['entity']['id'])

        # the response also contains some data under the 'entity' key
        # but it is NOT the actual content
        # see also [[d:Special:Diff/1356933963]]
        # TODO: there might be some circumstances under which
        # the content can be safely reused
        if hasattr(self, '_content'):
            del self._content
        self.latest_revision_id = updates['entity'].get('lastrevid')
        if update_self and 'claims' in updates['entity']:
            updated_claims = updates['entity']['claims']
            for claim_prop_id, statements in updated_claims.items():
                for claim_index, statement in enumerate(statements):
                    claim = self.claims[claim_prop_id][claim_index]
                    claim.snak = statement['id']
                    claim.on_item = self
                    updated_qualifiers = statement.get('qualifiers', {})
                    for qual_propid, qualifier in updated_qualifiers.items():
                        for qual_index, qual_statement in enumerate(qualifier):
                            target_qual_prop = claim.qualifiers[qual_propid]
                            target_qual = target_qual_prop[qual_index]
                            target_qual.hash = qual_statement['hash']
                    updated_references = statement.get('references', [])
                    for ref_grp_idx, ref_grp in enumerate(updated_references):
                        for ref_propid, reference in ref_grp['snaks'].items():
                            for ref_index, ref_stat in enumerate(reference):
                                target_ref_grp = claim.sources[ref_grp_idx]
                                target_ref_prop = target_ref_grp[ref_propid]
                                target_ref = target_ref_prop[ref_index]
                                target_ref.hash = ref_stat['hash']

    def concept_uri(self) -> str:
        """Return the full concept URI.

        :raise NoWikibaseEntityError: if this entity's id is not known
        """
        entity_id = self.getID()
        if entity_id == '-1':
            raise NoWikibaseEntityError(self)
        return f'{self.repo.concept_base_uri}{entity_id}'


class MediaInfo(WikibaseEntity):

    """Interface for MediaInfo entities on Commons.

    .. versionadded:: 6.5
    """

    entity_type = 'mediainfo'
    title_pattern = r'M[1-9]\d*'
    DATA_ATTRIBUTES = {
        'labels': LanguageDict,
        'statements': ClaimCollection,
    }

    def __getattr__(self, name):
        if name == 'claims':  # T149410
            return self.statements

        if name in self.DATA_ATTRIBUTES:
            if not self.exists():
                self._assert_has_id()
                self._initialize_empty()
            return getattr(self, name)

        return super().__getattr__(name)

    def _assert_has_id(self):
        if self.id != '-1':
            return

        if not self.file.exists():
            exc = NoPageError(self.file)
            raise NoWikibaseEntityError(self) from exc

        self.id = 'M' + str(self.file.pageid)

    def _defined_by(self, singular: bool = False) -> dict:
        """Function to provide the API parameters to identify the entity.

        .. versionadded:: 8.5

        :param singular: Whether the parameter names should use the singular
                         form
        :raise NoWikibaseEntityError: if this entity is associated with
                                      a non-existing file
        :return: API parameters
        """
        self._assert_has_id()
        return super()._defined_by(singular)

    @property
    def file(self) -> FilePage:
        """Get the file associated with the mediainfo."""
        if not hasattr(self, '_file'):
            if self.id == '-1':
                # if the above doesn't apply, this entity is in an invalid
                # state which needs to be raised as an exception, but also
                # logged in case an exception handler is catching
                # the generic Error
                msg = f'{self.__class__.__name__} is in invalid state'
                pywikibot.error(msg)
                raise Error(msg)

            # avoid recursion with self.getID()
            page_id = int(self.id[1:])
            result = list(self.repo.load_pages_from_pageids([page_id]))
            if not result:
                raise Error(f'There is no existing page with id "{page_id}"')

            page = result.pop()
            if page.namespace() != page.site.namespaces.FILE:
                raise Error(f'Page with id "{page_id}" is not a file')

            self._file = FilePage(page)

        return self._file

    def get(self, force: bool = False) -> dict:
        """Fetch all MediaInfo entity data and cache it.

        .. note:: dicts returned by this method are references to content
           of this entity and their modifying may indirectly cause
           unwanted change to the live content

        .. versionchanged:: 9.0
           Added *pageid*, *ns*, *title*, *lastrevid*, *modified*, *id*
           values to ``_content`` attribute when it is loaded.

        :param force: override caching
        :raise NoWikibaseEntityError: if this entity doesn't exist
        :return: actual data which entity holds
        """
        if force or not hasattr(self, '_content'):
            if force:
                self.file.clear_cache()

            # accessing latest_revision loads the file data
            try:
                latest_revision = self.file.latest_revision
            except NoPageError as exc:
                raise NoWikibaseEntityError(self) from exc
            except Error as exc:
                error_message = str(exc)
                if 'is not a file' in error_message:
                    raise NoWikibaseEntityError(self) from exc

                raise Error(self) from exc

            # Create _content. Format is same as with wbgetentities
            # https://commons.wikimedia.org/w/api.php?action=wbgetentities&ids=M20985340
            data = {
                'title': self.file.title,
                'lastrevid': latest_revision['revid'],
                'modified': str(latest_revision['timestamp']),
                'type': 'mediainfo',
                'pageid': self.file.pageid,
                'ns': self.file.namespace,
                'id': 'M' + str(self.file.pageid),
                'labels': {},
                'statements': {}
            }

            # Update 'id', 'labels' and 'statements' if mediainfo is available.
            # MediaInfo is returned only when it has values.
            if 'mediainfo' in latest_revision.slots:
                mediainfo_json = latest_revision.slots['mediainfo']['*']
                mediainfo_data = jsonlib.loads(mediainfo_json)
                data.update(mediainfo_data)

            self._content = data
            self.id = self._content['id']

        self._assert_has_id()

        # Do not pass the force parameter to the upper level because
        # reloading files without MediaInfo will fail.
        return super().get()

    def getID(self, numeric: bool = False) -> str | int:
        """Get the entity identifier.

        .. seealso:: :meth:`title`

        :param numeric: Strip the first letter and return an int
        :raises NoWikibaseEntityError: if this entity is associated with
            a non-existing file
        """
        self._assert_has_id()
        return super().getID(numeric=numeric)

    def title(self) -> str:
        """Return ID as title of the MediaInfo.

        .. versionadded:: 9.4
        .. seealso:: :meth:`getID`

        :raises NoWikibaseEntityError: if this entity is associated with
            a non-existing file
        :return: the entity identifier
        """
        return self.getID()

    def editLabels(self, labels: LANGUAGE_TYPE, **kwargs) -> None:
        """Edit MediaInfo labels (eg. captions).

        *labels* should be a dict, with the key as a language or a site
        object. The value should be the string to set it to. You can set
        it to ``''`` to remove the label.

        Usage:

        >>> repo = pywikibot.Site('commons','commons')
        >>> page = pywikibot.FilePage(repo, 'File:Sandbox-Test.svg')
        >>> item = page.data_item()
        >>> item.editLabels({'en': 'Test file.'}) # doctest: +SKIP

        .. versionadded:: 8.5
        """
        data = {'labels': labels}
        self.editEntity(data, **kwargs)

    def addClaim(self, claim, bot: bool = True, **kwargs):
        """Add a claim to the MediaInfo.

        .. versionadded:: 8.5

        :param claim: The claim to add
        :type claim: pywikibot.page.Claim
        :param bot: Whether to flag as bot (if possible)
        """
        if claim.on_item is not None:
            raise ValueError(
                'The provided Claim instance is already used in an entity')

        self._assert_has_id()
        self.repo.addClaim(self, claim, bot=bot, **kwargs)
        claim.on_item = self

    def removeClaims(self, claims, **kwargs) -> None:
        """Remove the claims from the MediaInfo.

        .. versionadded:: 8.5

        :param claims: list of claims to be removed
        :type claims: list or pywikibot.Claim
        """
        # this check allows single claims to be removed by pushing them into a
        # list of length one.
        if isinstance(claims, pywikibot.Claim):
            claims = [claims]
        data = self.repo.removeClaims(claims, **kwargs)
        for claim in claims:
            claim.on_item.latest_revision_id = data['pageinfo']['lastrevid']
            claim.on_item = None
            claim.snak = None


class WikibasePage(BasePage, WikibaseEntity):

    """Mixin base class for Wikibase entities which are also pages (eg. items).

    There should be no need to instantiate this directly.
    """

    _cache_attrs = (*BasePage._cache_attrs, '_content')

    def __init__(self, site, title: str = '', **kwargs) -> None:
        """Initializer.

        If title is provided, either ns or entity_type must also be provided,
        and will be checked against the title parsed using the Page
        initialisation logic.

        :param site: Wikibase data site
        :type site: pywikibot.site.DataSite
        :param title: normalized title of the page
        :type title: str
        :keyword ns: namespace
        :type ns: Namespace instance, or int
        :keyword entity_type: Wikibase entity type
        :type entity_type: str ('item' or 'property')

        :raises TypeError: incorrect use of parameters
        :raises ValueError: incorrect namespace
        :raises pywikibot.exceptions.Error: title parsing problems
        :raises NotImplementedError: the entity type is not supported
        """
        if not isinstance(site, pywikibot.site.DataSite):
            raise TypeError('site must be a pywikibot.site.DataSite object')
        if title and ('ns' not in kwargs and 'entity_type' not in kwargs):
            pywikibot.debug(f'{type(self).__name__}.__init__: {site} title '
                            f'{title!r} specified without ns or entity_type')

        self._namespace = None

        if 'ns' in kwargs:
            if isinstance(kwargs['ns'], Namespace):
                self._namespace = kwargs.pop('ns')
                kwargs['ns'] = self._namespace.id
            else:
                # numerical namespace given
                ns = int(kwargs['ns'])
                if site.item_namespace.id == ns:
                    self._namespace = site.item_namespace
                elif site.property_namespace.id == ns:
                    self._namespace = site.property_namespace
                else:
                    raise ValueError(
                        f'{site!r}: Namespace "{int(ns)}" is not valid')

        if 'entity_type' in kwargs:
            entity_type = kwargs.pop('entity_type')
            try:
                entity_type_ns = site.get_namespace_for_entity_type(
                    entity_type)
            except EntityTypeUnknownError:
                raise ValueError(
                    f'Wikibase entity type "{entity_type}" unknown')

            if self._namespace:
                if self._namespace != entity_type_ns:
                    raise ValueError('Namespace "{}" is not valid for Wikibase'
                                     ' entity type "{}"'
                                     .format(int(kwargs['ns']), entity_type))
            else:
                self._namespace = entity_type_ns
                kwargs['ns'] = self._namespace.id

        BasePage.__init__(self, site, title, **kwargs)

        # If a title was not provided,
        # avoid checks which may cause an exception.
        if not title:
            WikibaseEntity.__init__(self, site)
            return

        if self._namespace:
            if self._link.namespace != self._namespace.id:
                raise ValueError(
                    f"'{title}' is not in the namespace {self._namespace.id}"
                )
        else:
            # Neither ns or entity_type was provided.
            # Use the _link to determine entity type.
            ns = self._link.namespace
            if self.site.item_namespace.id == ns:
                self._namespace = self.site.item_namespace
            elif self.site.property_namespace.id == ns:
                self._namespace = self.site.property_namespace
            else:
                raise ValueError(
                    f'{self.site!r}: Namespace "{ns!r}" is not valid')

        WikibaseEntity.__init__(
            self,
            # .site forces a parse of the Link title to determine site
            self.site,
            # Link.__init__, called from Page.__init__, has cleaned the title
            # stripping whitespace and uppercasing the first letter according
            # to the namespace case=first-letter.
            self._link.title)

    def namespace(self) -> int:
        """Return the number of the namespace of the entity.

        :return: Namespace id
        """
        return self._namespace.id

    def exists(self) -> bool:
        """Determine if an entity exists in the data repository."""
        if not hasattr(self, '_content'):
            try:
                self.get(get_redirect=True)
                return True
            except NoPageError:
                return False
        return 'missing' not in self._content

    def botMayEdit(self) -> bool:
        """Return whether bots may edit this page.

        Because there is currently no system to mark a page that it shouldn't
        be edited by bots on Wikibase pages it always returns True. The content
        of the page is not text but a dict, the original way (to search for a
        template) doesn't apply.

        :return: True
        """
        return True

    def get(self, force: bool = False, *args, **kwargs) -> dict:
        """Fetch all page data, and cache it.

        :param force: override caching
        :raise NotImplementedError: a value in args or kwargs
        :return: actual data which entity holds

        .. note:: dicts returned by this method are references to content
           of this entity and their modifying may indirectly cause
           unwanted change to the live content
        """
        if args or kwargs:
            raise NotImplementedError(
                f'{type(self).__name__}.get does not implement var args: '
                f'{args!r} and {kwargs!r}'
            )

        # TODO: this variable is specific to ItemPage
        lazy_loading_id = not hasattr(self, 'id') and hasattr(self, '_site')
        try:
            data = WikibaseEntity.get(self, force=force)
        except NoWikibaseEntityError:
            if lazy_loading_id:
                p = pywikibot.Page(self._site, self._title)
                if not p.exists():
                    raise NoPageError(p)
                # TODO: raise a nicer exception here (T87345)
            raise NoPageError(self)

        if 'pageid' in self._content:
            self._pageid = self._content['pageid']

        return data

    @property
    def latest_revision_id(self) -> int:
        """Get the revision id for the most recent revision of the entity.

        :rtype: int
        :raise pywikibot.exceptions.NoPageError: if the entity doesn't exist
        """
        if not hasattr(self, '_revid'):
            self.get()
        return self._revid

    @latest_revision_id.setter
    def latest_revision_id(self, value) -> None:
        self._revid = value

    @latest_revision_id.deleter
    def latest_revision_id(self) -> None:
        # fixme: this seems too destructive in comparison to the parent
        self.clear_cache()

    @allow_asynchronous
    def editEntity(
        self,
        data: ENTITY_DATA_TYPE | None = None,
        **kwargs: Any
    ) -> None:
        """Edit an entity using Wikibase ``wbeditentity`` API.

        This function is wrapped around by:
         - :meth:`editLabels`
         - :meth:`editDescriptions`
         - :meth:`editAliases`
         - :meth:`ItemPage.setSitelinks`

        It supports *asynchronous* and *callback* keyword arguments. The
        callback function is intended for use by bots that need to keep
        track of which saves were successful. The minimal callback
        function signature is::

          def my_callback(page: WikibasePage, err: Optional[Exception]) -> Any:

        The arguments are:

        ``page``
            a :class:`WikibasePage` object

        ``err``
            an Exception instance, which will be None if the page was
            saved successfully

        .. seealso:: :meth:`WikibaseEntity.editEntity`

        :param data: Data to be saved
        :keyword bool asynchronous: if True, launch a separate thread to
            edit asynchronously
        :keyword Callable[[WikibasePage, Optional[Exception]], Any] callback:
            a callable object that will be called after the entity has
            been updated. It must take two arguments, see above.
        """
        # kept for the decorator which provides the keyword arguments
        super().editEntity(data, **kwargs)

    def editLabels(self, labels: LANGUAGE_TYPE, **kwargs) -> None:
        """Edit entity labels.

        *labels* should be a dict, with the key as a language or a site
        object. The value should be the string to set it to. You can set
        it to ``''`` to remove the label.

        Refer :meth:`editEntity` for *asynchronous* and *callback* usage.

        Usage:

        >>> repo = pywikibot.Site('wikidata:test')
        >>> item = pywikibot.ItemPage(repo, 'Q68')
        >>> item.editLabels({'en': 'Test123'})  # doctest: +SKIP
        """
        data = {'labels': labels}
        self.editEntity(data, **kwargs)

    def editDescriptions(self, descriptions: LANGUAGE_TYPE, **kwargs) -> None:
        """Edit entity descriptions.

        *descriptions* should be a dict, with the key as a language or a
        site object. The value should be the string to set it to. You
        can set it to ``''`` to remove the description.

        Refer :meth:`editEntity` for *asynchronous* and *callback* usage.

        Usage:

        >>> repo = pywikibot.Site('wikidata:test')
        >>> item = pywikibot.ItemPage(repo, 'Q68')
        >>> item.editDescriptions({'en': 'Pywikibot test'})  # doctest: +SKIP
        """
        data = {'descriptions': descriptions}
        self.editEntity(data, **kwargs)

    def editAliases(self, aliases: ALIASES_TYPE, **kwargs) -> None:
        """Edit entity aliases.

        *aliases* should be a dict, with the key as a language or a site
        object. The value should be a list of strings.

        Refer :meth:`editEntity` for *asynchronous* and *callback* usage.

        Usage:

        >>> repo = pywikibot.Site('wikidata:test')
        >>> item = pywikibot.ItemPage(repo, 'Q68')
        >>> item.editAliases({'en': ['pwb test item']})  # doctest: +SKIP
        """
        data = {'aliases': aliases}
        self.editEntity(data, **kwargs)

    def set_redirect_target(
        self,
        target_page,
        create: bool = False,
        force: bool = False,
        keep_section: bool = False,
        save: bool = True,
        **kwargs
    ):
        """Set target of a redirect for a Wikibase page.

        Has not been implemented in the Wikibase API yet, except for ItemPage.
        """
        raise NotImplementedError

    @allow_asynchronous
    def addClaim(self, claim, bot: bool = True, **kwargs):
        """Add a claim to the entity.

        :param claim: The claim to add
        :type claim: pywikibot.page.Claim
        :param bot: Whether to flag as bot (if possible)
        :keyword asynchronous: if True, launch a separate thread to add claim
            asynchronously
        :type asynchronous: bool
        :keyword callback: a callable object that will be called after the
            claim has been added. It must take two arguments:
            (1) a WikibasePage object, and (2) an exception instance,
            which will be None if the entity was saved successfully. This is
            intended for use by bots that need to keep track of which saves
            were successful.
        :type callback: callable
        """
        if claim.on_item is not None:
            raise ValueError(
                'The provided Claim instance is already used in an entity')
        self.repo.addClaim(self, claim, bot=bot, **kwargs)
        claim.on_item = self

    def removeClaims(self, claims, **kwargs) -> None:
        """Remove the claims from the entity.

        :param claims: list of claims to be removed
        :type claims: list or pywikibot.Claim
        """
        # this check allows single claims to be removed by pushing them into a
        # list of length one.
        if isinstance(claims, pywikibot.Claim):
            claims = [claims]
        data = self.repo.removeClaims(claims, **kwargs)
        for claim in claims:
            claim.on_item.latest_revision_id = data['pageinfo']['lastrevid']
            claim.on_item = None
            claim.snak = None


class ItemPage(WikibasePage):

    """Wikibase entity of type 'item'.

    A Wikibase item may be defined by either a 'Q' id (qid),
    or by a site & title.

    If an item is defined by site & title, once an item's qid has
    been looked up, the item is then defined by the qid.
    """

    _cache_attrs = (*WikibasePage._cache_attrs, 'labels', 'descriptions',
                    'aliases', 'claims', 'sitelinks')
    entity_type = 'item'
    title_pattern = r'Q[1-9]\d*'
    DATA_ATTRIBUTES = {
        'labels': LanguageDict,
        'descriptions': LanguageDict,
        'aliases': AliasesDict,
        'claims': ClaimCollection,
        'sitelinks': SiteLinkCollection,
    }

    def __init__(self, site, title=None, ns=None) -> None:
        """Initializer.

        :param site: data repository
        :type site: pywikibot.site.DataSite
        :param title: identifier of item, "Q###",
                      -1 or None for an empty item.
        :type title: str
        :type ns: namespace
        :type ns: Namespace instance, or int, or None
            for default item_namespace
        """
        if ns is None:
            ns = site.item_namespace
        # Special case for empty item.
        if title is None or title == '-1':
            super().__init__(site, '-1', ns=ns)
            assert self.id == '-1'
            return

        # we don't want empty titles
        if not title:
            raise InvalidTitleError("Item's title cannot be empty")

        super().__init__(site, title, ns=ns)

        assert self.id == self._link.title

    def _defined_by(self, singular: bool = False) -> dict:
        """Function to provide the API parameters to identify the item.

        The API parameters may be 'id' if the ItemPage has one,
        or 'site'&'title' if instantiated via ItemPage.fromPage with
        lazy_load enabled.

        Once an item's Q## is looked up, that will be used for all future
        requests.

        An empty dict is returned if the ItemPage is instantiated without
        either ID (internally it has id = '-1') or site&title.

        :param singular: Whether the parameter names should use the
            singular form
        :return: API parameters
        """
        params = {}
        if singular:
            id = 'id'
            site = 'site'
            title = 'title'
        else:
            id = 'ids'
            site = 'sites'
            title = 'titles'

        lazy_loading_id = not hasattr(self, 'id') and hasattr(self, '_site')

        # id overrides all
        if hasattr(self, 'id'):
            if self.id != '-1':
                params[id] = self.id
        elif lazy_loading_id:
            params[site] = self._site.dbName()
            params[title] = self._title
        else:
            # if none of the above applies, this item is in an invalid state
            # which needs to be raise as an exception, but also logged in case
            # an exception handler is catching the generic Error.
            msg = f'{self.__class__.__name__} is in invalid state'
            pywikibot.error(msg)
            raise Error(msg)

        return params

    def title(self, **kwargs):
        """Return ID as title of the ItemPage.

        If the ItemPage was lazy-loaded via ItemPage.fromPage, this method
        will fetch the Wikibase item ID for the page, potentially raising
        NoPageError with the page on the linked wiki if it does not exist, or
        does not have a corresponding Wikibase item ID.

        This method also refreshes the title if the id property was set.
        i.e. item.id = 'Q60'

        All optional keyword parameters are passed to the superclass.
        """
        # If instantiated via ItemPage.fromPage using site and title,
        # _site and _title exist, and id does not exist.
        lazy_loading_id = not hasattr(self, 'id') and hasattr(self, '_site')

        if lazy_loading_id or self._link._text != self.id:
            # If the item is lazy loaded or has been modified,
            # _link._text is stale. Removing _link._title
            # forces Link to re-parse ._text into ._title.
            if hasattr(self._link, '_title'):
                del self._link._title
            self._link._text = self.getID()
            self._link.parse()
            # Remove the temporary values that are no longer needed after
            # the .getID() above has called .get(), which populated .id
            if hasattr(self, '_site'):
                del self._title
                del self._site

        return super().title(**kwargs)

    def getID(self, numeric: bool = False, force: bool = False):
        """Get the entity identifier.

        :param numeric: Strip the first letter and return an int
        :param force: Force an update of new data
        """
        if not hasattr(self, 'id') or force:
            self.get(force=force)
        return super().getID(numeric=numeric)

    @classmethod
    def fromPage(cls, page, lazy_load: bool = False):
        """Get the ItemPage for a Page that links to it.

        :param page: Page to look for corresponding data item
        :type page: pywikibot.page.Page
        :param lazy_load: Do not raise NoPageError if either page or
            corresponding ItemPage does not exist.
        :rtype: pywikibot.page.ItemPage

        :raise pywikibot.exceptions.NoPageError: There is no corresponding
            ItemPage for the page
        :raise pywikibot.exceptions.WikiBaseError: The site of the page
            has no data repository.
        """
        if hasattr(page, '_item'):
            return page._item
        if not page.site.has_data_repository:
            raise WikiBaseError(f'{page.site} has no data repository')
        if not lazy_load and not page.exists():
            raise NoPageError(page)

        repo = page.site.data_repository()
        if hasattr(page,
                   '_pageprops') and page.properties().get('wikibase_item'):
            # If we have already fetched the pageprops for something else,
            # we already have the id, so use it
            page._item = cls(repo, page.properties().get('wikibase_item'))
            return page._item
        i = cls(repo)
        # clear id, and temporarily store data needed to lazy loading the item
        del i.id
        i._site = page.site
        i._title = page.title(with_section=False)
        if not lazy_load and not i.exists():
            raise NoPageError(i)
        page._item = i
        return page._item

    @classmethod
    def from_entity_uri(cls, site, uri: str, lazy_load: bool = False):
        """Get the ItemPage from its entity uri.

        :param site: The Wikibase site for the item.
        :type site: pywikibot.site.DataSite
        :param uri: Entity uri for the Wikibase item.
        :param lazy_load: Do not raise NoPageError if ItemPage does not exist.
        :rtype: pywikibot.page.ItemPage

        :raise TypeError: Site is not a valid DataSite.
        :raise ValueError: Site does not match the base of the provided uri.
        :raise pywikibot.exceptions.NoPageError: Uri points to non-existent
            item.
        """
        if not isinstance(site, DataSite):
            raise TypeError(f'{site} is not a data repository.')

        base_uri, _, qid = uri.rpartition('/')
        if base_uri != site.concept_base_uri.rstrip('/'):
            raise ValueError(
                'The supplied data repository ({repo}) does not correspond to '
                'that of the item ({item})'.format(
                    repo=site.concept_base_uri.rstrip('/'),
                    item=base_uri))

        item = cls(site, qid)
        if not lazy_load and not item.exists():
            raise NoPageError(item)

        return item

    def get(
        self,
        force: bool = False,
        get_redirect: bool = False,
        *args,
        **kwargs
    ) -> dict[str, Any]:
        """Fetch all item data, and cache it.

        :param force: override caching
        :param get_redirect: return the item content, do not follow the
                             redirect, do not raise an exception.
        :raise NotImplementedError: a value in args or kwargs
        :raise IsRedirectPageError: instance is a redirect page and
            get_redirect is not True
        :return: actual data which entity holds

        .. note:: dicts returned by this method are
           references to content of this entity and
           their modifying may indirectly cause
           unwanted change to the live content
        """
        data = super().get(force, *args, **kwargs)

        if self.isRedirectPage() and not get_redirect:
            raise IsRedirectPageError(self)

        return data

    def getRedirectTarget(self, *, ignore_section: bool = True):
        """Return the redirect target for this page.

        .. versionadded:: 9.3
           *ignore_section* parameter

        .. seealso:: :meth:`page.BasePage.getRedirectTarget`

        :param ignore_section: do not include section to the target even
            the link has one

        :raises CircularRedirectError: page is a circular redirect
        :raises InterwikiRedirectPageError: the redirect target is on
            another site
        :raises Error: target page has wrong content model
        :raises IsNotRedirectPageError: page is not a redirect
        :raises RuntimeError: no redirects found
        :raises SectionError: the section is not found on target page
            and *ignore_section* is not set
        """
        target = super().getRedirectTarget(ignore_section=ignore_section)
        cmodel = target.content_model
        if cmodel != 'wikibase-item':
            raise Error(f'{self} has redirect target {target} with content '
                        f'model {cmodel} instead of wikibase-item')
        return self.__class__(target.site, target.title(), target.namespace())

    def iterlinks(self, family=None):
        """Iterate through all the sitelinks.

        :param family: string/Family object which represents what family of
                       links to iterate
        :type family: str|pywikibot.family.Family
        :return: iterator of pywikibot.Page objects
        :rtype: iterator
        """
        if not hasattr(self, 'sitelinks'):
            self.get()
        if family is not None and not isinstance(family, Family):
            family = Family.load(family)
        for sl in self.sitelinks.values():
            if family is None or family == sl.site.family:
                pg = pywikibot.Page(sl)
                pg._item = self
                yield pg

    def getSitelink(self, site, force: bool = False) -> str:
        """Return the title for the specific site.

        If the item doesn't have a link to that site, raise
        NoSiteLinkError.

        .. versionchanged:: 8.1
           raises NoSiteLinkError instead of NoPageError.

        :param site: Site to find the linked page of.
        :type site: pywikibot.Site or database name
        :param force: override caching
        :raise IsRedirectPageError: instance is a redirect page
        :raise NoSiteLinkError: site is not in :attr:`sitelinks`
        """
        if force or not hasattr(self, '_content'):
            self.get(force=force)

        if site not in self.sitelinks:
            if not isinstance(site, str):
                site = site.dbName()
            raise NoSiteLinkError(self, site)

        return self.sitelinks[site].canonical_title()

    def setSitelink(self, sitelink: SITELINK_TYPE, **kwargs) -> None:
        """Set sitelinks. Calls :meth:`setSitelinks`.

        A *sitelink* can be a Page object, a BaseLink object or a
        ``{'site': dbname, 'title': title}`` dictionary.

        Refer :meth:`WikibasePage.editEntity` for *asynchronous* and
        *callback* usage.
        """
        self.setSitelinks([sitelink], **kwargs)

    def removeSitelink(self, site: LANGUAGE_IDENTIFIER, **kwargs) -> None:
        """Remove a sitelink.

        A site can either be a Site object, or it can be a dbName.
        """
        self.removeSitelinks([site], **kwargs)

    def removeSitelinks(self, sites: list[LANGUAGE_IDENTIFIER], **kwargs
                        ) -> None:
        """Remove sitelinks.

        Sites should be a list, with values either
        being Site objects, or dbNames.
        """
        data = []
        for site in sites:
            site = SiteLinkCollection.getdbName(site)
            data.append({'site': site, 'title': ''})
        self.setSitelinks(data, **kwargs)

    def setSitelinks(self, sitelinks: list[SITELINK_TYPE], **kwargs) -> None:
        """Set sitelinks.

        *sitelinks* should be a list. Each item in the list can either
        be a Page object, a BaseLink object, or a dict with key for
        'site' and a value for 'title'.

        Refer :meth:`editEntity` for *asynchronous* and *callback* usage.
        """
        data = {'sitelinks': sitelinks}
        self.editEntity(data, **kwargs)

    def mergeInto(self, item, **kwargs) -> None:
        """Merge the item into another item.

        :param item: The item to merge into
        :type item: pywikibot.page.ItemPage
        """
        data = self.repo.mergeItems(from_item=self, to_item=item, **kwargs)
        if not data.get('success', 0):
            return
        self.latest_revision_id = data['from']['lastrevid']
        item.latest_revision_id = data['to']['lastrevid']
        if data.get('redirected', 0):
            self._isredir = True
            self._redirtarget = item

    @deprecated_args(botflag='bot')  # since 9.3.0
    def set_redirect_target(
        self,
        target_page: ItemPage | str,
        create: bool = False,
        force: bool = False,
        keep_section: bool = False,
        save: bool = True,
        **kwargs
    ) -> None:
        """Make the item redirect to another item.

        You need to define an extra argument to make this work, like
        :code:`save=True`.

        .. versionchanged:: 9.3
           *botflag* keyword parameter was renamed to *bot*.

        :param target_page: target of the redirect, this argument is
            required.
        :param force: if true, it sets the redirect target even the page
            is not redirect.
        """
        if isinstance(target_page, str):
            target_page = pywikibot.ItemPage(self.repo, target_page)
        elif self.repo != target_page.repo:
            raise InterwikiRedirectPageError(self, target_page)

        if self.exists() and not self.isRedirectPage() and not force:
            raise IsNotRedirectPageError(self)

        if not save or keep_section or create:
            raise NotImplementedError

        data = self.repo.set_redirect_target(
            from_item=self, to_item=target_page,
            bot=kwargs.get('bot', True))
        if data.get('success', 0):
            del self.latest_revision_id
            self._isredir = True
            self._redirtarget = target_page

    def isRedirectPage(self):
        """Return True if item is a redirect, False if not or not existing."""
        if hasattr(self, '_content') and not hasattr(self, '_isredir'):
            self._isredir = self.id != self._content.get('id', self.id)
            return self._isredir
        return super().isRedirectPage()


class Property:

    """A Wikibase property.

    While every Wikibase property has a Page on the data repository,
    this object is for when the property is used as part of another concept
    where the property is not _the_ Page of the property.

    For example, a claim on an ItemPage has many property attributes, and so
    it subclasses this Property class, but a claim does not have Page like
    behaviour and semantics.
    """

    types = {
        'commonsMedia': FilePage,
        'external-id': str,
        'geo-shape': pywikibot.WbGeoShape,
        'globe-coordinate': pywikibot.Coordinate,
        'math': str,
        'monolingualtext': pywikibot.WbMonolingualText,
        'musical-notation': str,
        'quantity': pywikibot.WbQuantity,
        'string': str,
        'tabular-data': pywikibot.WbTabularData,
        'time': pywikibot.WbTime,
        'url': str,
        'wikibase-item': ItemPage,
        # The following types are added later, they must be declared first
        # 'wikibase-form': LexemeForm,
        # 'wikibase-sense': LexemeSense,
        # 'wikibase-lexeme': LexemePage,
        # 'wikibase-property': PropertyPage,
    }

    # the value type where different from the type
    value_types = {'wikibase-item': 'wikibase-entityid',
                   'wikibase-property': 'wikibase-entityid',
                   'wikibase-lexeme': 'wikibase-entityid',
                   'wikibase-form': 'wikibase-entityid',
                   'wikibase-sense': 'wikibase-entityid',
                   'commonsMedia': 'string',
                   'url': 'string',
                   'globe-coordinate': 'globecoordinate',
                   'math': 'string',
                   'external-id': 'string',
                   'geo-shape': 'string',
                   'tabular-data': 'string',
                   'musical-notation': 'string',
                   }

    def __init__(self, site, id: str, datatype: str | None = None) -> None:
        """Initializer.

        :param site: data repository
        :type site: pywikibot.site.DataSite
        :param id: id of the property
        :param datatype: datatype of the property;
            if not given, it will be queried via the API
        """
        self.repo = site
        self.id = id.upper()
        if datatype:
            self._type = datatype

    def exists(self):
        """Determine if the property exists in the data repository.

        .. versionadded:: 9.4
        """
        try:
            self._type = self.repo.get_property_type(self)
        except NoWikibaseEntityError:
            return False
        return True

    @property
    @cached
    def type(self) -> str:
        """Return the type of this property.

        .. versionchanged:: 9.4
           raises :exc:`NoWikibaseEntityError` if property does not
           exist.

        :raises NoWikibaseEntityError: property does not exist
        """
        return self.repo.get_property_type(self)

    def getID(self, numeric: bool = False):
        """Get the identifier of this property.

        :param numeric: Strip the first letter and return an int
        """
        if numeric:
            return int(self.id[1:])
        return self.id


class PropertyPage(WikibasePage, Property):

    """A Wikibase entity in the property namespace.

    Should be created as::

        PropertyPage(DataSite, 'P21')

    or::

        PropertyPage(DataSite, datatype='url')
    """

    _cache_attrs = (*WikibasePage._cache_attrs, '_type', 'labels',
                    'descriptions', 'aliases', 'claims')
    entity_type = 'property'
    title_pattern = r'P[1-9]\d*'
    DATA_ATTRIBUTES = {
        'labels': LanguageDict,
        'descriptions': LanguageDict,
        'aliases': AliasesDict,
        'claims': ClaimCollection,
    }

    def __init__(self, source, title=None, datatype=None) -> None:
        """Initializer.

        :param source: data repository property is on
        :type source: pywikibot.site.DataSite
        :param title: identifier of property, like "P##",
                      "-1" or None for an empty property.
        :type title: str
        :param datatype: Datatype for a new property.
        :type datatype: str
        """
        # Special case for new property.
        if title is None or title == '-1':
            if not datatype:
                raise TypeError('"datatype" is required for new property.')
            WikibasePage.__init__(self, source, '-1',
                                  ns=source.property_namespace)
            Property.__init__(self, source, '-1', datatype=datatype)
            assert self.id == '-1'
        else:
            if not title:
                raise InvalidTitleError(
                    "Property's title cannot be empty")

            WikibasePage.__init__(self, source, title,
                                  ns=source.property_namespace)
            Property.__init__(self, source, self.id)

    def get(self, force: bool = False, *args, **kwargs) -> dict:
        """Fetch the property entity, and cache it.

        :param force: override caching
        :raise NotImplementedError: a value in args or kwargs
        :return: actual data which entity holds

        .. note:: dicts returned by this method are
           references to content of this entity and
           their modifying may indirectly cause
           unwanted change to the live content
        """
        if args or kwargs:
            raise NotImplementedError(
                'PropertyPage.get only implements "force".')

        data = WikibasePage.get(self, force)
        if 'datatype' in self._content:
            self._type = self._content['datatype']
        data['datatype'] = self._type
        return data

    def newClaim(self, *args, **kwargs) -> Claim:
        """Helper function to create a new claim object for this property."""
        # TODO: raise when self.id is -1
        return Claim(self.site, self.getID(), *args, datatype=self.type,
                     **kwargs)

    def getID(self, numeric: bool = False):
        """Get the identifier of this property.

        :param numeric: Strip the first letter and return an int
        """
        # enforce this parent's implementation
        return WikibasePage.getID(self, numeric=numeric)

    def get_data_for_new_entity(self):
        """Return data required for creation of new property."""
        return {'datatype': self.type}


# Add PropertyPage to the class attribute "types" after its declaration.
Property.types['wikibase-property'] = PropertyPage


class Claim(Property):

    """A Claim on a Wikibase entity.

    Claims are standard claims as well as references and qualifiers.
    """

    TARGET_CONVERTER = {
        'wikibase-item': lambda value, site:
            ItemPage(site.get_repo_for_entity_type('item'),
                     'Q' + str(value['numeric-id'])),
        'wikibase-property': lambda value, site:
            PropertyPage(site.get_repo_for_entity_type('property'),
                         'P' + str(value['numeric-id'])),
        'wikibase-lexeme': lambda value, site:
            LexemePage(site.get_repo_for_entity_type('lexeme'), value['id']),
        'wikibase-form': lambda value, site:
            LexemeForm(site.get_repo_for_entity_type('lexeme'), value['id']),
        'wikibase-sense': lambda value, site:
            LexemeSense(site.get_repo_for_entity_type('lexeme'), value['id']),
        'commonsMedia': lambda value, site:
            FilePage(pywikibot.Site('commons'), value),  # T90492
        'globe-coordinate': pywikibot.Coordinate.fromWikibase,
        'geo-shape': pywikibot.WbGeoShape.fromWikibase,
        'tabular-data': pywikibot.WbTabularData.fromWikibase,
        'time': pywikibot.WbTime.fromWikibase,
        'quantity': pywikibot.WbQuantity.fromWikibase,
        'monolingualtext': lambda value, site:
            pywikibot.WbMonolingualText.fromWikibase(value)
    }

    SNAK_TYPES = ('value', 'somevalue', 'novalue')

    def __init__(
        self,
        site,
        pid,
        snak=None,
        hash=None,
        is_reference: bool = False,
        is_qualifier: bool = False,
        rank: str = 'normal',
        **kwargs
    ) -> None:
        """Initializer.

        Defined by the "snak" value, supplemented by site + pid

        :param site: Repository where the property of the claim is defined.
            Note that this does not have to correspond to the repository
            where the claim has been stored.
        :type site: pywikibot.site.DataSite
        :param pid: property id, with "P" prefix
        :param snak: snak identifier for claim
        :param hash: hash identifier for references
        :param is_reference: whether specified claim is a reference
        :param is_qualifier: whether specified claim is a qualifier
        :param rank: rank for claim
        """
        Property.__init__(self, site, pid, **kwargs)
        self.snak = snak
        self.hash = hash
        self.rank = rank
        self.isReference = is_reference
        self.isQualifier = is_qualifier
        if self.isQualifier and self.isReference:
            raise ValueError('Claim cannot be both a qualifier and reference.')
        self.sources = []
        self.qualifiers = OrderedDict()
        self.target = None
        self.snaktype = 'value'
        self._on_item = None  # The item it's on

    @property
    def on_item(self) -> WikibaseEntity | None:
        """Return entity this claim is attached to."""
        return self._on_item

    @on_item.setter
    def on_item(self, item) -> None:
        self._on_item = item
        for values in self.qualifiers.values():
            for qualifier in values:
                qualifier.on_item = item
        for source in self.sources:
            for values in source.values():
                for val in values:
                    val.on_item = item

    def _assert_attached(self) -> None:
        if self.on_item is None:
            raise RuntimeError('The claim is not attached to an entity')

    def _assert_mainsnak(self, message: str) -> None:
        if self.isQualifier:
            raise RuntimeError(first_upper(message.format('qualifier')))
        if self.isReference:
            raise RuntimeError(first_upper(message.format('reference')))

    def __repr__(self) -> str:
        """Return the representation string."""
        cls_name = type(self).__name__
        if self.target:
            return f'{cls_name}.fromJSON({self.repo!r}, {self.toJSON()})'

        return f'{cls_name}({self.repo!r}, {self.id!r})'

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.same_as(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def _claim_mapping_same(this, other) -> bool:
        if len(this) != len(other):
            return False
        my_values = list(chain.from_iterable(this.values()))
        other_values = list(chain.from_iterable(other.values()))
        if len(my_values) != len(other_values):
            return False
        for val in my_values:
            if val not in other_values:
                return False
        return all(val in my_values for val in other_values)

    def same_as(
        self,
        other,
        ignore_rank: bool = True,
        ignore_quals: bool = False,
        ignore_refs: bool = True
    ) -> bool:
        """Check if two claims are same."""
        attributes = ['id', 'snaktype', 'target']
        if not ignore_rank:
            attributes.append('rank')
        for attr in attributes:
            if getattr(self, attr) != getattr(other, attr):
                return False

        if not (ignore_quals or self._claim_mapping_same(self.qualifiers,
                                                         other.qualifiers)):
            return False

        if not ignore_refs:
            if len(self.sources) != len(other.sources):
                return False

            for source in self.sources:
                for other_source in other.sources:
                    if self._claim_mapping_same(source, other_source):
                        break
                else:
                    return False

        return True

    def copy(self):
        """Create an independent copy of this object.

        :rtype: pywikibot.page.Claim
        """
        is_qualifier = self.isQualifier
        is_reference = self.isReference
        self.isQualifier = False
        self.isReference = False
        copy = self.fromJSON(self.repo, self.toJSON())
        for cl in (self, copy):
            cl.isQualifier = is_qualifier
            cl.isReference = is_reference
        copy.hash = None
        copy.snak = None
        return copy

    @classmethod
    def fromJSON(cls, site, data: dict[str, Any]) -> Claim:
        """Create a claim object from JSON returned in the API call.

        .. versionchanged:: 9.4
           print a warning if the Claim.type is not given and missing in
           the wikibase.

        :param data: JSON containing claim data
        """
        claim_repo = site.get_repo_for_entity_type('property')
        claim = cls(claim_repo, data['mainsnak']['property'],
                    datatype=data['mainsnak'].get('datatype'))
        if 'id' in data:
            claim.snak = data['id']
        elif 'hash' in data:
            claim.hash = data['hash']

        claim.snaktype = data['mainsnak']['snaktype']
        if claim.getSnakType() == 'value':
            value = data['mainsnak']['datavalue']['value']

            # note: claim.type could be set during claim initialization
            try:
                claim_type = claim.type
            except NoWikibaseEntityError:
                claim_type = None

            msg = None
            if not claim_type:
                msg = f'{claim.id} does not exist.'
            elif claim.type in cls.types:
                # The default covers string, url types
                claim.target = cls.TARGET_CONVERTER.get(
                    claim.type, lambda value, site: value)(value, site)
            else:
                msg = f'{claim.type} datatype is not supported yet.'

            if msg is not None:
                claim.target = pywikibot.WbUnknown.fromWikibase(value)
                claim.target.warning = msg

        if 'rank' in data:  # References/Qualifiers don't have ranks
            claim.rank = data['rank']
        if 'references' in data:
            for source in data['references']:
                claim.sources.append(cls.referenceFromJSON(site, source))
        if 'qualifiers' in data:
            for prop in data['qualifiers-order']:
                claim.qualifiers[prop] = [
                    cls.qualifierFromJSON(site, qualifier)
                    for qualifier in data['qualifiers'][prop]]
        return claim

    @classmethod
    def referenceFromJSON(cls, site, data) -> dict:
        """Create a dict of claims from reference JSON fetched in the API call.

        Reference objects are represented a bit differently, and require
        some more handling.
        """
        source = OrderedDict()

        # Before #84516 Wikibase did not implement snaks-order.
        # https://gerrit.wikimedia.org/r/c/84516/
        prop_list = data.get('snaks-order', data['snaks'].keys())

        for prop in prop_list:
            for claimsnak in data['snaks'][prop]:
                claim = cls.fromJSON(site, {'mainsnak': claimsnak,
                                            'hash': data.get('hash')})
                claim.isReference = True
                if claim.getID() not in source:
                    source[claim.getID()] = []
                source[claim.getID()].append(claim)
        return source

    @classmethod
    def qualifierFromJSON(cls, site, data):
        """Create a Claim for a qualifier from JSON.

        Qualifier objects are represented a bit
        differently like references, but I'm not
        sure if this even requires it's own function.

        :rtype: pywikibot.page.Claim
        """
        claim = cls.fromJSON(site, {'mainsnak': data,
                                    'hash': data.get('hash')})
        claim.isQualifier = True
        return claim

    def toJSON(self) -> dict:
        """Create dict suitable for the MediaWiki API."""
        data = {
            'mainsnak': {
                'snaktype': self.snaktype,
                'property': self.getID()
            },
            'type': 'statement'
        }
        if hasattr(self, 'snak') and self.snak is not None:
            data['id'] = self.snak
        if hasattr(self, 'rank') and self.rank is not None:
            data['rank'] = self.rank
        if self.getSnakType() == 'value':
            data['mainsnak']['datatype'] = self.type
            data['mainsnak']['datavalue'] = self._formatDataValue()
        if self.isQualifier or self.isReference:
            data = data['mainsnak']
            if hasattr(self, 'hash') and self.hash is not None:
                data['hash'] = self.hash
        else:
            if self.qualifiers:
                data['qualifiers'] = {}
                data['qualifiers-order'] = list(self.qualifiers.keys())
                for prop, qualifiers in self.qualifiers.items():
                    for qualifier in qualifiers:
                        assert qualifier.isQualifier is True
                    data['qualifiers'][prop] = [
                        qualifier.toJSON() for qualifier in qualifiers]

            if self.sources:
                data['references'] = []
                for collection in self.sources:
                    reference = {
                        'snaks': {}, 'snaks-order': list(collection.keys())}
                    for prop, val in collection.items():
                        reference['snaks'][prop] = []
                        for source in val:
                            assert source.isReference is True
                            src_data = source.toJSON()
                            if 'hash' in src_data:
                                reference.setdefault('hash', src_data['hash'])
                                del src_data['hash']
                            reference['snaks'][prop].append(src_data)
                    data['references'].append(reference)
        return data

    def setTarget(self, value):
        """Set the target value in the local object.

        :param value: The new target value.
        :type value: object

        :exception ValueError: if value is not of the type
            required for the Claim type.
        """
        value_class = self.types[self.type]
        if not isinstance(value, value_class):
            raise ValueError(f'{value} is not type {value_class}.')
        self.target = value

    def changeTarget(
        self,
        value=None,
        snaktype: str = 'value',
        **kwargs
    ) -> None:
        """Set the target value in the data repository.

        :param value: The new target value.
        :type value: object
        :param snaktype: The new snak type ('value', 'somevalue', or
            'novalue').
        """
        self._assert_attached()
        if value:
            self.setTarget(value)

        data = self.on_item.repo.changeClaimTarget(self, snaktype=snaktype,
                                                   **kwargs)
        # TODO: Re-create the entire item from JSON, not just id
        self.snak = data['claim']['id']
        self.on_item.latest_revision_id = data['pageinfo']['lastrevid']

    def getTarget(self):
        """Return the target value of this Claim.

        None is returned if no target is set

        :return: object
        """
        return self.target

    def getSnakType(self) -> str:
        """Return the type of snak.

        :return: str ('value', 'somevalue' or 'novalue')
        """
        return self.snaktype

    def setSnakType(self, value):
        """Set the type of snak.

        :param value: Type of snak
        :type value: str ('value', 'somevalue', or 'novalue')
        """
        if value in self.SNAK_TYPES:
            self.snaktype = value
        else:
            raise ValueError(
                "snaktype must be 'value', 'somevalue', or 'novalue'.")

    def getRank(self):
        """Return the rank of the Claim."""
        return self.rank

    def setRank(self, rank) -> None:
        """Set the rank of the Claim."""
        self._assert_mainsnak('Cannot set rank on a {}')
        self.rank = rank

    def changeRank(self, rank, **kwargs):
        """Change the rank of the Claim and save."""
        self._assert_mainsnak('Cannot change rank on a {}')
        self._assert_attached()
        self.rank = rank
        return self.on_item.repo.save_claim(self, **kwargs)

    def changeSnakType(self, value=None, **kwargs) -> None:
        """Save the new snak value.

        TODO: Is this function really needed?
        """
        if value:
            self.setSnakType(value)
        self.changeTarget(snaktype=self.getSnakType(), **kwargs)

    def getSources(self) -> list:
        """Return a list of sources, each being a list of Claims."""
        return self.sources

    def addSource(self, claim, **kwargs) -> None:
        """Add the claim as a source.

        :param claim: the claim to add
        :type claim: pywikibot.Claim
        """
        self.addSources([claim], **kwargs)

    def addSources(self, claims, **kwargs):
        """Add the claims as one source.

        :param claims: the claims to add
        :type claims: list of pywikibot.Claim
        """
        self._assert_mainsnak('Cannot add sources to a {}')
        for claim in claims:
            if claim.on_item is not None:
                raise ValueError(
                    'The provided Claim instance is already used in an entity')
        if self.on_item is not None:
            data = self.on_item.repo.editSource(self, claims, new=True,
                                                **kwargs)
            self.on_item.latest_revision_id = data['pageinfo']['lastrevid']
            for claim in claims:
                claim.hash = data['reference']['hash']
                claim.on_item = self.on_item
        source = defaultdict(list)
        for claim in claims:
            claim.isReference = True
            source[claim.getID()].append(claim)
        self.sources.append(source)

    def removeSource(self, source, **kwargs) -> None:
        """Remove the source. Call removeSources().

        :param source: the source to remove
        :type source: pywikibot.Claim
        """
        self.removeSources([source], **kwargs)

    def removeSources(self, sources, **kwargs) -> None:
        """Remove the sources.

        :param sources: the sources to remove
        :type sources: list of pywikibot.Claim
        """
        self._assert_mainsnak('Cannot remove sources from a {}')
        self._assert_attached()
        data = self.on_item.repo.removeSources(self, sources, **kwargs)
        self.on_item.latest_revision_id = data['pageinfo']['lastrevid']
        for source in sources:
            source_dict = defaultdict(list)
            source_dict[source.getID()].append(source)
            self.sources.remove(source_dict)

    def addQualifier(self, qualifier, **kwargs):
        """Add the given qualifier.

        :param qualifier: the qualifier to add
        :type qualifier: pywikibot.page.Claim
        """
        self._assert_mainsnak('Cannot add qualifiers to a {}')
        if qualifier.on_item is not None:
            raise ValueError(
                'The provided Claim instance is already used in an entity')
        if self.on_item is not None:
            data = self.on_item.repo.editQualifier(self, qualifier, **kwargs)
            self.on_item.latest_revision_id = data['pageinfo']['lastrevid']
            qualifier.on_item = self.on_item
        qualifier.isQualifier = True
        if qualifier.getID() in self.qualifiers:
            self.qualifiers[qualifier.getID()].append(qualifier)
        else:
            self.qualifiers[qualifier.getID()] = [qualifier]

    def removeQualifier(self, qualifier, **kwargs) -> None:
        """Remove the qualifier. Call removeQualifiers().

        :param qualifier: the qualifier to remove
        :type qualifier: pywikibot.page.Claim
        """
        self.removeQualifiers([qualifier], **kwargs)

    def removeQualifiers(self, qualifiers, **kwargs) -> None:
        """Remove the qualifiers.

        :param qualifiers: the qualifiers to remove
        :type qualifiers: list of pywikibot.Claim
        """
        self._assert_mainsnak('Cannot remove qualifiers from a {}')
        self._assert_attached()
        data = self.on_item.repo.remove_qualifiers(self, qualifiers, **kwargs)
        self.on_item.latest_revision_id = data['pageinfo']['lastrevid']
        for qualifier in qualifiers:
            self.qualifiers[qualifier.getID()].remove(qualifier)
            qualifier.on_item = None

    def target_equals(self, value) -> bool:
        """Check whether the Claim's target is equal to specified value.

        The function checks for:

        - WikibaseEntity ID equality
        - WbTime year equality
        - Coordinate equality, regarding precision
        - WbMonolingualText text equality
        - direct equality

        :param value: the value to compare with
        :return: true if the Claim's target is equal to the value provided,
            false otherwise
        """
        if (isinstance(self.target, WikibaseEntity)
                and isinstance(value, str)):
            return self.target.id == value

        if (isinstance(self.target, pywikibot.WbTime)
                and not isinstance(value, pywikibot.WbTime)):
            return self.target.year == int(value)

        if (isinstance(self.target, pywikibot.Coordinate)
                and isinstance(value, str)):
            coord_args = [float(x) for x in value.split(',')]
            # Default value 0.0001 ~10 m at equator
            precision = coord_args[2] if len(coord_args) >= 3 else 0.0001
            with suppress(TypeError):
                if self.target.precision is not None:
                    precision = max(precision, self.target.precision)

            return (abs(self.target.lat - coord_args[0]) <= precision
                    and abs(self.target.lon - coord_args[1]) <= precision)

        if (isinstance(self.target, pywikibot.WbMonolingualText)
                and isinstance(value, str)):
            return self.target.text == value

        return self.target == value

    def has_qualifier(self, qualifier_id: str, target) -> bool:
        """Check whether Claim contains specified qualifier.

        :param qualifier_id: id of the qualifier
        :param target: qualifier target to check presence of
        :return: true if the qualifier was found, false otherwise
        """
        self._assert_mainsnak('{}s cannot have qualifiers')
        return any(qualifier.target_equals(target)
                   for qualifier in self.qualifiers.get(qualifier_id, []))

    def _formatValue(self) -> dict:
        """Format the target into the proper JSON value that Wikibase wants.

        :return: JSON value
        """
        # TODO: eventually unify the following two groups
        if self.type in ('wikibase-item', 'wikibase-property'):
            value = {'entity-type': self.getTarget().entity_type,
                     'numeric-id': self.getTarget().getID(numeric=True)}
        elif self.type in (
                'wikibase-lexeme', 'wikibase-form', 'wikibase-sense'):
            value = {'entity-type': self.getTarget().entity_type,
                     'id': self.getTarget().getID()}
        elif self.type in ('string', 'url', 'math', 'external-id',
                           'musical-notation'):
            value = self.getTarget()
        elif self.type == 'commonsMedia':
            value = self.getTarget().title(with_ns=False)
        elif self.type in ('globe-coordinate', 'time',
                           'quantity', 'monolingualtext',
                           'geo-shape', 'tabular-data'):
            value = self.getTarget().toWikibase()
        else:  # WbUnknown
            pywikibot.warning(
                f'{self.type} datatype is not supported yet.')
            value = self.getTarget().toWikibase()
        return value

    def _formatDataValue(self) -> dict:
        """Format the target into the proper JSON datavalue for Wikibase.

        :return: Wikibase API representation with type and value.
        """
        return {
            'value': self._formatValue(),
            'type': self.value_types.get(self.type, self.type)
        }


class LexemePage(WikibasePage):

    """Wikibase entity of type 'lexeme'.

    Basic usage sample:

    >>> import pywikibot
    >>> repo = pywikibot.Site('wikidata')
    >>> L2 = pywikibot.LexemePage(repo, 'L2')  # create a Lexeme page
    >>> list(L2.claims)  # access the claims
    ['P5402', 'P5831', 'P12690', 'P12448', 'P31', 'P5275', 'P12510', ...]
    >>> len(L2.forms)  # access the forms
    3
    >>> F1 = L2.forms[0]  # access the first form
    >>> list(F1.claims)  # access its claims
    ['P898']
    >>> len(L2.senses)  # access the senses
    2
    >>> S1 = L2.senses[0]  # access the first sense
    >>> list(S1.claims)  # and its claims
    ['P5137', 'P5972', 'P2888']
    """

    _cache_attrs = (*WikibasePage._cache_attrs, 'lemmas', 'language',
                    'lexicalCategory', 'forms', 'senses')
    entity_type = 'lexeme'
    title_pattern = r'L[1-9]\d*'
    DATA_ATTRIBUTES = {
        'lemmas': LanguageDict,
        'claims': ClaimCollection,
        # added when defined
        # 'forms': LexemeFormCollection,
        # 'senses': LexemeSenseCollection,
    }

    def __init__(self, site, title=None) -> None:
        """Initializer.

        :param site: data repository
        :type site: pywikibot.site.DataSite
        :param title: identifier of lexeme, "L###",
            -1 or None for an empty lexeme.
        :type title: str or None
        """
        # Special case for empty lexeme.
        if title is None or title == '-1':
            super().__init__(site, '-1', entity_type='lexeme')
            assert self.id == '-1'
            return

        # we don't want empty titles
        if not title:
            raise InvalidTitleError("Lexeme's title cannot be empty")

        super().__init__(site, title, entity_type='lexeme')
        assert self.id == self._link.title

    def get_data_for_new_entity(self):
        """Return data required for creation of a new lexeme."""
        raise NotImplementedError  # TODO

    def toJSON(self, diffto: dict | None = None) -> dict:
        """Create JSON suitable for Wikibase API.

        When diffto is provided, JSON representing differences
        to the provided data is created.

        :param diffto: JSON containing entity data
        """
        data = super().toJSON(diffto=diffto)

        for prop in ('language', 'lexicalCategory'):
            value = getattr(self, prop, None)
            if not value:
                continue
            if not diffto or diffto.get(prop) != value.getID():
                data[prop] = value.getID()

        return data

    def get(self, force=False, get_redirect=False, *args, **kwargs):
        """Fetch all lexeme data, and cache it.

        :param force: override caching
        :type force: bool
        :param get_redirect: return the lexeme content, do not follow the
            redirect, do not raise an exception.
        :type get_redirect: bool
        :raise NotImplementedError: a value in args or kwargs

        .. note:: dicts returned by this method are references to content
           of this entity and their modifying may indirectly cause
           unwanted change to the live content
        """
        data = super().get(force, *args, **kwargs)

        if self.isRedirectPage() and not get_redirect:
            raise IsRedirectPageError(self)

        # language
        self.language = None
        if 'language' in self._content:
            self.language = ItemPage(self.site, self._content['language'])

        # lexicalCategory
        self.lexicalCategory = None
        if 'lexicalCategory' in self._content:
            self.lexicalCategory = ItemPage(
                self.site, self._content['lexicalCategory'])

        data['language'] = self.language
        data['lexicalCategory'] = self.lexicalCategory

        return data

    @classmethod
    def _normalizeData(cls, data: dict) -> dict:
        """Helper function to expand data into the Wikibase API structure.

        :param data: The dict to normalize
        :return: the altered dict from parameter data.
        """
        new_data = WikibasePage._normalizeData(data)
        for prop in ('language', 'lexicalCategory'):
            value = new_data.get(prop)
            if value:
                if isinstance(value, ItemPage):
                    new_data[prop] = value.getID()
                else:
                    new_data[prop] = value
        return new_data

    @allow_asynchronous
    def add_form(self, form, **kwargs):
        """Add a form to the lexeme.

        :param form: The form to add
        :type form: Form
        :keyword bot: Whether to flag as bot (if possible)
        :type bot: bool
        :keyword asynchronous: if True, launch a separate thread to add form
            asynchronously
        :type asynchronous: bool
        :keyword callback: a callable object that will be called after the
            claim has been added. It must take two arguments:
            (1) a LexemePage object, and
            (2) an exception instance, which will be None if the entity was
            saved successfully. This is intended for use by bots that need to
            keep track of which saves were successful.
        :type callback: callable
        """
        if form.on_lexeme is not None:
            raise ValueError('The provided LexemeForm instance is already '
                             'used in an entity')
        data = self.repo.add_form(self, form, **kwargs)
        form.id = data['form']['id']
        form.on_lexeme = self
        form._content = data['form']
        form.get()
        self.forms.append(form)
        self.latest_revision_id = data['lastrevid']

    def remove_form(self, form, **kwargs) -> None:
        """Remove a form from the lexeme.

        :param form: The form to remove
        :type form: pywikibot.LexemeForm
        """
        data = self.repo.remove_form(form, **kwargs)
        form.on_lexeme.latest_revision_id = data['lastrevid']
        form.on_lexeme.forms.remove(form)
        form.on_lexeme = None
        form.id = '-1'

    # TODO: senses

    def mergeInto(self, lexeme, **kwargs):
        """Merge the lexeme into another lexeme.

        :param lexeme: The lexeme to merge into
        :type lexeme: LexemePage
        """
        data = self.repo.mergeLexemes(from_lexeme=self, to_lexeme=lexeme,
                                      **kwargs)
        if not data.get('success', 0):
            return
        self.latest_revision_id = data['from']['lastrevid']
        lexeme.latest_revision_id = data['to']['lastrevid']
        if data.get('redirected', 0):
            self._isredir = True
            self._redirtarget = lexeme

    def isRedirectPage(self):
        """Return True if lexeme is redirect, False if not or not existing."""
        if hasattr(self, '_content') and not hasattr(self, '_isredir'):
            self._isredir = self.id != self._content.get('id', self.id)
            return self._isredir
        return super().isRedirectPage()


# Add LexemePage to the class attribute "types" after its declaration.
Property.types['wikibase-lexeme'] = LexemePage


class LexemeSubEntity(WikibaseEntity):

    """Common super class for LexemeForm and LexemeSense."""

    def __init__(self, repo, id_=None) -> None:
        """Initializer."""
        super().__init__(repo, id_)
        self._on_lexeme = None

    @classmethod
    def fromJSON(cls, repo, data):
        new = cls(repo, data['id'])
        new._content = data
        return new

    def toJSON(self, diffto=None) -> dict:
        data = super().toJSON(diffto)
        if self.id != '-1':
            data['id'] = self.id
        return data

    @property
    def on_lexeme(self) -> LexemePage:
        if self._on_lexeme is None:
            lexeme_id = self.id.partition('-')[0]
            self._on_lexeme = LexemePage(self.repo, lexeme_id)
        return self._on_lexeme

    @on_lexeme.setter
    def on_lexeme(self, lexeme):
        self._on_lexeme = lexeme

    @on_lexeme.deleter
    def on_lexeme(self):
        self._on_lexeme = None

    @allow_asynchronous
    def addClaim(self, claim, **kwargs):
        """Add a claim to the form.

        :param claim: The claim to add
        :type claim: Claim
        :keyword bot: Whether to flag as bot (if possible)
        :type bot: bool
        :keyword asynchronous: if True, launch a separate thread to add claim
            asynchronously
        :type asynchronous: bool
        :keyword callback: a callable object that will be called after the
            claim has been added. It must take two arguments: (1) a Form
            object, and (2) an exception instance, which will be None if the
            form was saved successfully. This is intended for use by bots that
            need to keep track of which saves were successful.
        :type callback: callable
        """
        self.repo.addClaim(self, claim, **kwargs)
        claim.on_item = self

    def removeClaims(self, claims, **kwargs) -> None:
        """Remove the claims from the form.

        :param claims: list of claims to be removed
        :type claims: list or pywikibot.Claim
        """
        # this check allows single claims to be removed by pushing them into a
        # list of length one.
        if isinstance(claims, pywikibot.Claim):
            claims = [claims]
        data = self.repo.removeClaims(claims, **kwargs)
        for claim in claims:
            claim.on_item.latest_revision_id = data['pageinfo']['lastrevid']
            claim.on_item = None
            claim.snak = None


class LexemeForm(LexemeSubEntity):

    """Wikibase lexeme form."""

    entity_type = 'form'
    title_pattern = LexemePage.title_pattern + r'-F[1-9]\d*'
    DATA_ATTRIBUTES = {
        'representations': LanguageDict,
        'claims': ClaimCollection,
    }

    def toJSON(self, diffto: dict | None = None) -> dict:
        """Create dict suitable for the MediaWiki API."""
        data = super().toJSON(diffto=diffto)

        key = 'grammaticalFeatures'
        if getattr(self, key, None):
            # could also avoid if no change wrt. diffto
            data[key] = [value.getID() for value in self.grammaticalFeatures]

        return data

    @classmethod
    def _normalizeData(cls, data):
        new_data = LexemeSubEntity._normalizeData(data)
        if 'grammaticalFeatures' in data:
            value = []
            for feat in data['grammaticalFeatures']:
                if isinstance(feat, ItemPage):
                    value.append(feat.getID())
                else:
                    value.append(feat)
            new_data['grammaticalFeatures'] = value
        return new_data

    def get(self, force: bool = False) -> dict:
        """Fetch all form data, and cache it.

        :param force: override caching

        .. note:: dicts returned by this method are references to content
           of this entity and their modifying may indirectly cause
           unwanted change to the live content
        """
        data = super().get(force=force)

        # grammaticalFeatures
        self.grammaticalFeatures = set()
        for value in self._content.get('grammaticalFeatures', []):
            self.grammaticalFeatures.add(ItemPage(self.repo, value))

        data['grammaticalFeatures'] = self.grammaticalFeatures

        return data

    def edit_elements(self, data: dict, **kwargs) -> None:
        """Update form elements.

        :param data: Data to be saved
        """
        if self.id == '-1':
            # Update only locally
            if 'representations' in data:
                self.representations = LanguageDict(data['representations'])

            if 'grammaticalFeatures' in data:
                self.grammaticalFeatures = set()
                for value in data['grammaticalFeatures']:
                    if not isinstance(value, ItemPage):
                        value = ItemPage(self.repo, value)
                    self.grammaticalFeatures.add(value)
        else:
            data = self._normalizeData(data)
            updates = self.repo.edit_form_elements(self, data, **kwargs)
            self._content = updates['form']


# Add LexemeForm to the class attribute "types" after its declaration.
Property.types['wikibase-form'] = LexemeForm


class LexemeSense(LexemeSubEntity):

    """Wikibase lexeme sense."""

    entity_type = 'sense'
    title_pattern = LexemePage.title_pattern + r'-S[1-9]\d*'
    DATA_ATTRIBUTES = {
        'glosses': LanguageDict,
        'claims': ClaimCollection,
    }


# Add LexemeSense to the class attribute "types" after its declaration.
Property.types['wikibase-sense'] = LexemeSense


class LexemeFormCollection(SubEntityCollection):

    type_class = LexemeForm


class LexemeSenseCollection(SubEntityCollection):

    type_class = LexemeSense


LexemePage.DATA_ATTRIBUTES.update({
    'forms': LexemeFormCollection,
    'senses': LexemeSenseCollection,
})
