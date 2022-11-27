"""Structures holding data for Wikibase entities."""
#
# (C) Pywikibot team, 2019-2022
#
# Distributed under the terms of the MIT license.
#
from collections import defaultdict
from collections.abc import MutableMapping, MutableSequence
from typing import Optional

import pywikibot
from pywikibot.site import BaseSite


__all__ = (
    'AliasesDict',
    'ClaimCollection',
    'LanguageDict',
    'SiteLinkCollection',
    'SubEntityCollection',
)


class BaseDataDict(MutableMapping):

    """
    Base structure holding data for a Wikibase entity.

    Data are mappings from a language to a value. It will be
    specialised in subclasses.
    """

    def __init__(self, data=None) -> None:
        super().__init__()
        self._data = {}
        if data:
            self.update(data)

    @classmethod
    def new_empty(cls, repo):
        """Construct a new empty BaseDataDict."""
        return cls()

    def __getitem__(self, key):
        key = self.normalizeKey(key)
        return self._data[key]

    def __setitem__(self, key, value) -> None:
        key = self.normalizeKey(key)
        self._data[key] = value

    def __delitem__(self, key) -> None:
        key = self.normalizeKey(key)
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key) -> bool:
        key = self.normalizeKey(key)
        return key in self._data

    def __repr__(self) -> str:
        return f'{type(self)}({self._data})'

    @staticmethod
    def normalizeKey(key) -> str:
        """Helper function to return language codes of a site object.

        :param key: input key to be normalized
        :type key: pywikibot.site.BaseSite or str
        """
        if isinstance(key, BaseSite):
            key = key.lang
        return key


class LanguageDict(BaseDataDict):

    """
    A structure holding language data for a Wikibase entity.

    Language data are mappings from a language to a string. It can be
    labels, descriptions and others.
    """

    @classmethod
    def fromJSON(cls, data, repo=None):
        """Construct a new LanguageDict from JSON."""
        if data != []:  # workaround for T222159
            return cls({key: value['value'] for key, value in data.items()})
        return cls()

    @classmethod
    def normalizeData(cls, data: dict):
        """Helper function to expand data into the Wikibase API structure.

        :param data: Data to normalize
        :return: The dict with normalized data
        """
        norm_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                norm_data[key] = {'language': key, 'value': value}
            else:
                norm_data[key] = value
        return norm_data

    def toJSON(self, diffto: Optional[dict] = None) -> dict:
        """Create JSON suitable for Wikibase API.

        When diffto is provided, JSON representing differences
        to the provided data is created.

        :param diffto: JSON containing entity data
        """
        data = {}
        diffto = diffto or {}
        for key in diffto.keys() - self.keys():
            data[key] = {'language': key, 'value': ''}
        for key in self.keys() - diffto.keys():
            data[key] = {'language': key, 'value': self[key]}
        for key in self.keys() & diffto.keys():
            if self[key] != diffto[key]['value']:
                data[key] = {'language': key, 'value': self[key]}
        return data


class AliasesDict(BaseDataDict):

    """
    A structure holding aliases for a Wikibase entity.

    It is a mapping from a language to a list of strings.
    """

    @classmethod
    def fromJSON(cls, data, repo=None):
        """Construct a new AliasesDict from JSON."""
        this = cls()
        for key, value in data.items():
            this[key] = [val['value'] for val in value]
        return this

    @classmethod
    def normalizeData(cls, data: dict) -> dict:
        """Helper function to expand data into the Wikibase API structure.

        .. versionchanged:: 7.7
           raises TypeError if *data* value is not a list.

        :param data: Data to normalize
        :return: The dict with normalized data
        :raises TypeError: data values must be a list
        """
        norm_data = {}
        for key, values in data.items():
            if isinstance(values, list):
                strings = []
                for value in values:
                    if isinstance(value, str):
                        strings.append({'language': key, 'value': value})
                    else:
                        strings.append(value)
                norm_data[key] = strings
            else:
                raise TypeError(
                    "Unsupported value type {!r} for '{}'; list expected."
                    .format(type(values).__name__, values))

        return norm_data

    def toJSON(self, diffto: Optional[dict] = None) -> dict:
        """Create JSON suitable for Wikibase API.

        When diffto is provided, JSON representing differences
        to the provided data is created.

        :param diffto: JSON containing entity data
        """
        data = {}
        diffto = diffto or {}
        for lang in diffto.keys() & self.keys():
            if (sorted(val['value'] for val in diffto[lang])
                    != sorted(self[lang])):
                data[lang] = [{'language': lang, 'value': i}
                              for i in self[lang]]
        for lang in diffto.keys() - self.keys():
            data[lang] = [
                {'language': lang, 'value': i['value'], 'remove': ''}
                for i in diffto[lang]]
        for lang in self.keys() - diffto.keys():
            data[lang] = [{'language': lang, 'value': i} for i in self[lang]]
        return data


class ClaimCollection(MutableMapping):
    """A structure holding claims for a Wikibase entity."""

    def __init__(self, repo) -> None:
        """Initializer."""
        super().__init__()
        self.repo = repo
        self._data = {}

    @classmethod
    def fromJSON(cls, data, repo):
        """Construct a new ClaimCollection from JSON."""
        this = cls(repo)
        for key, claims in data.items():
            this[key] = [pywikibot.page.Claim.fromJSON(repo, claim)
                         for claim in claims]
        return this

    @classmethod
    def new_empty(cls, repo):
        """Construct a new empty ClaimCollection."""
        return cls(repo)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value) -> None:
        self._data[key] = value

    def __delitem__(self, key) -> None:
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        return f'{type(self)}({self._data})'

    @classmethod
    def normalizeData(cls, data) -> dict:
        """Helper function to expand data into the Wikibase API structure.

        :param data: Data to normalize
        :return: The dict with normalized data
        """
        # no normalization here, should there be?
        return data

    def toJSON(self, diffto: Optional[dict] = None) -> dict:
        """Create JSON suitable for Wikibase API.

        When diffto is provided, JSON representing differences
        to the provided data is created.

        :param diffto: JSON containing entity data
        """
        claims = {}
        for prop in self:
            if self[prop]:
                claims[prop] = [claim.toJSON() for claim in self[prop]]

        if not diffto:
            return claims

        diff_claims = defaultdict(list)
        props_add = set(claims)
        props_orig = set(diffto)
        for prop in (props_orig | props_add):
            if prop not in props_orig:
                diff_claims[prop].extend(claims[prop])
                continue

            if prop not in props_add:
                diff_claims[prop].extend(
                    {'id': claim['id'], 'remove': ''}
                    for claim in diffto[prop] if 'id' in claim)
                continue

            claim_ids = set()
            claim_map = {json['id']: json for json in diffto[prop]
                         if 'id' in json}

            for claim, json in zip(self[prop], claims[prop]):
                if 'id' not in json:
                    diff_claims[prop].append(json)
                    continue

                claim_ids.add(json['id'])
                if json['id'] in claim_map:
                    other = pywikibot.page.Claim.fromJSON(
                        self.repo, claim_map[json['id']])

                    if claim.same_as(other, ignore_rank=False,
                                     ignore_refs=False):
                        continue

                diff_claims[prop].append(json)

            for claim in diffto[prop]:
                if 'id' in claim and claim['id'] not in claim_ids:
                    diff_claims[prop].append({'id': claim['id'], 'remove': ''})

        return diff_claims

    def set_on_item(self, item) -> None:
        """Set Claim.on_item attribute for all claims in this collection."""
        for claims in self.values():
            for claim in claims:
                claim.on_item = item


class SiteLinkCollection(MutableMapping):
    """A structure holding SiteLinks for a Wikibase item."""

    def __init__(self, repo, data=None) -> None:
        """
        Initializer.

        :param repo: the Wikibase site on which badges are defined
        :type repo: pywikibot.site.DataSite
        """
        super().__init__()
        self.repo = repo
        self._data = {}
        if data:
            self.update(data)

    @classmethod
    def new_empty(cls, repo):
        """Construct a new empty SiteLinkCollection."""
        return cls(repo)

    @classmethod
    def fromJSON(cls, data, repo):
        """Construct a new SiteLinkCollection from JSON."""
        return cls(repo, data)

    @staticmethod
    def getdbName(site):
        """
        Helper function to obtain a dbName for a Site.

        :param site: The site to look up.
        :type site: pywikibot.site.BaseSite or str
        """
        if isinstance(site, BaseSite):
            return site.dbName()
        return site

    def __getitem__(self, key):
        """
        Get the SiteLink with the given key.

        :param key: site key as Site instance or db key
        :type key: pywikibot.Site or str
        :rtype: pywikibot.page.SiteLink
        """
        key = self.getdbName(key)
        val = self._data[key]
        if isinstance(val, str):
            val = pywikibot.page.SiteLink(val, key)
        elif isinstance(val, dict):
            val = pywikibot.page.SiteLink.fromJSON(val, self.repo)
        else:
            return val
        self._data[key] = val
        return val

    def __setitem__(self, key, val) -> None:
        """
        Set the SiteLink for a given key.

        This only sets the value given as str, dict or SiteLink. If a
        str or dict is given the SiteLink object is created later in
        __getitem__ method.

        :param key: site key as Site instance or db key
        :type key: pywikibot.Site or str
        :param val: page name as a string or JSON containing SiteLink
            data or a SiteLink object
        :type val: Union[str, dict, SiteLink]
        """
        key = self.getdbName(key)
        if isinstance(val, pywikibot.page.SiteLink):
            assert val.site.dbName() == key
        self._data[key] = val

    def __delitem__(self, key) -> None:
        key = self.getdbName(key)
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key) -> bool:
        key = self.getdbName(key)
        return key in self._data

    @classmethod
    def _extract_json(cls, obj):
        if isinstance(obj, pywikibot.page.SiteLink):
            return obj.toJSON()
        if isinstance(obj, pywikibot.page.BaseLink):
            db_name = cls.getdbName(obj.site)
            return {'site': db_name, 'title': obj.title}
        if isinstance(obj, pywikibot.page.Page):
            db_name = cls.getdbName(obj.site)
            return {'site': db_name, 'title': obj.title()}
        return obj

    @classmethod
    def normalizeData(cls, data) -> dict:
        """
        Helper function to expand data into the Wikibase API structure.

        :param data: Data to normalize
        :type data: list or dict

        :return: The dict with normalized data
        """
        norm_data = {}
        if isinstance(data, dict):
            for key, obj in data.items():
                key = cls.getdbName(key)
                json = cls._extract_json(obj)
                if isinstance(json, str):
                    json = {'site': key, 'title': json}
                elif key != json['site']:
                    raise ValueError(
                        "Key '{}' doesn't match the site of the value: '{}'"
                        .format(key, json['site']))
                norm_data[key] = json
        else:
            for obj in data:
                json = cls._extract_json(obj)
                if not isinstance(json, dict):
                    raise ValueError(
                        "Couldn't determine the site and title of the value: "
                        '{!r}'.format(json))
                db_name = json['site']
                norm_data[db_name] = json
        return norm_data

    def toJSON(self, diffto: Optional[dict] = None) -> dict:
        """
        Create JSON suitable for Wikibase API.

        When diffto is provided, JSON representing differences
        to the provided data is created.

        :param diffto: JSON containing entity data
        """
        data = {dbname: sitelink.toJSON()
                for (dbname, sitelink) in self.items()}
        if diffto:
            to_nuke = []
            for dbname, sitelink in data.items():
                if dbname not in diffto:
                    continue
                diffto_link = diffto[dbname]
                if diffto_link.get('title') == sitelink.get('title'):
                    # compare badges
                    tmp_badges = []
                    diffto_badges = diffto_link.get('badges', [])
                    badges = sitelink.get('badges', [])
                    for badge in set(diffto_badges) - set(badges):
                        tmp_badges.append('')
                    for badge in set(badges) - set(diffto_badges):
                        tmp_badges.append(badge)
                    if tmp_badges:
                        data[dbname]['badges'] = tmp_badges
                    else:
                        to_nuke.append(dbname)

            # find removed sitelinks
            for dbname in (set(diffto.keys()) - set(self.keys())):
                badges = [''] * len(diffto[dbname].get('badges', []))
                data[dbname] = {'site': dbname, 'title': ''}
                if badges:
                    data[dbname]['badges'] = badges
            for dbname in to_nuke:
                del data[dbname]
        return data


class SubEntityCollection(MutableSequence):

    """Ordered collection of sub-entities indexed by their ids."""

    def __init__(self, repo, data=None):
        """
        Initializer.

        :param repo: Wikibase site
        :type repo: pywikibot.site.DataSite
        :param data: iterable of LexemeSubEntity
        :type data: iterable
        """
        super().__init__()
        self.repo = repo
        self._data = []
        self._by_key = {}
        if data:
            self.extend(data)

    def _validate_isinstance(self, obj):
        if not isinstance(obj, self.type_class):
            raise TypeError(
                '{} should only hold instances of {}, '
                'instance of {} was provided'
                .format(self.__class__.__name__,
                        self.type_class.__name__,
                        obj.__class__.__name__))

    def __getitem__(self, index):
        if isinstance(index, str):
            try:
                index = self._by_key[index]
            except KeyError as e:
                raise ValueError('No entity with id {} was found'
                                 .format(index)) from e
        return self._data[index]

    def __setitem__(self, index, value):
        raise NotImplementedError

    def __delitem__(self, index):
        if isinstance(index, str):
            try:
                index = self._by_key[index]
            except KeyError as e:
                raise ValueError('No entity with id {} was found'
                                 .format(index)) from e
        obj = self._data[index]
        del self._data[index]
        del self._by_key[obj.id]

    def __len__(self):
        return len(self._data)

    def insert(self, index, obj):
        """Insert a sub-entity to the collection."""
        self._validate_isinstance(obj)
        self._data.insert(index, obj)
        self._by_key[obj.id] = index

    @classmethod
    def new_empty(cls, repo):
        """Construct a new empty SubEntityCollection."""
        return cls(repo)

    @classmethod
    def fromJSON(cls, data, repo):
        """Construct a new SubEntityCollection from JSON."""
        this = cls(repo)
        for entity in data:
            this.append(cls.type_class.fromJSON(repo, entity))
        return this

    @classmethod
    def normalizeData(cls, data: list) -> dict:
        """
        Helper function to expand data into the Wikibase API structure.

        :param data: Data to normalize
        :type data: list

        :return: the altered dict from parameter data.
        """
        raise NotImplementedError  # todo

    def toJSON(self, diffto: Optional[dict] = None) -> dict:
        """
        Create JSON suitable for Wikibase API.

        When diffto is provided, JSON representing differences
        to the provided data is created.

        :param diffto: JSON containing entity data
        """
        raise NotImplementedError  # todo
