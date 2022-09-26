"""Objects representing Namespaces of MediaWiki site."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
from collections.abc import Iterable, Mapping
from enum import IntEnum
from typing import Optional, Union

from pywikibot.backports import Dict
from pywikibot.backports import Iterable as IterableType
from pywikibot.backports import List
from pywikibot.tools import ComparableMixin, SelfCallMixin, classproperty


NamespaceIDType = Union[int, str, 'Namespace']
NamespaceArgType = Union[NamespaceIDType, IterableType[NamespaceIDType], None]


class BuiltinNamespace(IntEnum):

    """Builtin namespace enum."""

    MEDIA = -2
    SPECIAL = -1
    MAIN = 0
    TALK = 1
    USER = 2
    USER_TALK = 3
    PROJECT = 4
    PROJECT_TALK = 5
    FILE = 6
    FILE_TALK = 7
    MEDIAWIKI = 8
    MEDIAWIKI_TALK = 9
    TEMPLATE = 10
    TEMPLATE_TALK = 11
    HELP = 12
    HELP_TALK = 13
    CATEGORY = 14
    CATEGORY_TALK = 15

    @property
    def canonical(self) -> str:
        """Canonical form of MediaWiki built-in namespace.

        .. versionadded:: 7.1
        """
        name = '' if self == 0 else self.name.capitalize().replace('_', ' ')
        return name.replace('Mediawiki', 'MediaWiki')


class Namespace(Iterable, ComparableMixin):

    """
    Namespace site data object.

    This is backwards compatible with the structure of entries
    in site._namespaces which were a list of::

        [customised namespace,
         canonical namespace name?,
         namespace alias*]

    If the canonical_name is not provided for a namespace between -2
    and 15, the MediaWiki built-in names are used.
    Image and File are aliases of each other by default.

    If only one of canonical_name and custom_name are available, both
    properties will have the same value.
    """

    def __init__(self, id,
                 canonical_name: Optional[str] = None,
                 custom_name: Optional[str] = None,
                 aliases: Optional[List[str]] = None,
                 **kwargs) -> None:
        """Initializer.

        :param canonical_name: Canonical name
        :param custom_name: Name defined in server LocalSettings.php
        :param aliases: Aliases
        """
        self.id = id
        canonical_name = canonical_name or BuiltinNamespace(self.id).canonical

        assert custom_name is not None or canonical_name is not None, \
            'Namespace needs to have at least one name'

        self.custom_name = custom_name \
            if custom_name is not None else canonical_name
        self.canonical_name = canonical_name \
            if canonical_name is not None else custom_name

        if aliases:
            self.aliases = aliases
        elif id in (6, 7):
            alias = 'Image'
            if id == 7:
                alias += ' talk'
            self.aliases = [alias]
        else:
            self.aliases = []

        for key, value in kwargs.items():
            setattr(self, key, value)

    @classproperty
    def canonical_namespaces(cls) -> Dict[int, str]:
        """Return the canonical forms of MediaWiki built-in namespaces.

        .. versionchanged:: 7.1
           implemented as classproperty using BuiltinNamespace IntEnum.
        """
        return {item.value: item.canonical for item in BuiltinNamespace}

    def _distinct(self):
        if self.custom_name == self.canonical_name:
            return [self.canonical_name] + self.aliases
        return [self.custom_name, self.canonical_name] + self.aliases

    def _contains_lowercase_name(self, name):
        """Determine a lowercase normalised name is a name of this namespace.

        :rtype: bool
        """
        return name in (x.lower() for x in self._distinct())

    def __contains__(self, item: str) -> bool:
        """Determine if item is a name of this namespace.

        The comparison is case insensitive, and item may have a single
        colon on one or both sides of the name.

        :param item: name to check
        """
        if item == '' and self.id == 0:
            return True

        name = Namespace.normalize_name(item)
        if not name:
            return False

        return self._contains_lowercase_name(name.lower())

    def __bool__(self) -> bool:
        """Obtain boolean method for Namepace class.

        This method is implemented to be independent from __len__ method.

        .. versionadded:: 7.0

        :return: Always return True like generic object class.
        """
        return True

    def __len__(self) -> int:
        """Obtain length of the iterable."""
        return len(self._distinct())

    def __iter__(self):
        """Return an iterator."""
        return iter(self._distinct())

    def __getitem__(self, index):
        """Obtain an item from the iterable."""
        if self.custom_name != self.canonical_name:
            if index == 0:
                return self.custom_name
            index -= 1

        return self.canonical_name if index == 0 else self.aliases[index - 1]

    @staticmethod
    def _colons(id, name):
        """Return the name with required colons, depending on the ID."""
        if id == 0:
            return ':'

        if id in (6, 14):
            return ':' + name + ':'

        return name + ':'

    def __str__(self) -> str:
        """Return the canonical string representation."""
        return self.canonical_prefix()

    def canonical_prefix(self):
        """Return the canonical name with required colons."""
        return Namespace._colons(self.id, self.canonical_name)

    def custom_prefix(self):
        """Return the custom name with required colons."""
        return Namespace._colons(self.id, self.custom_name)

    def __int__(self) -> int:
        """Return the namespace id."""
        return self.id

    def __index__(self) -> int:
        """Return the namespace id."""
        return self.id

    def __hash__(self):
        """Return the namespace id."""
        return self.id

    def __eq__(self, other):
        """Compare whether two namespace objects are equal."""
        if isinstance(other, int):
            return self.id == other

        if isinstance(other, Namespace):
            return self.id == other.id

        if isinstance(other, str):
            return other in self

        return False

    def __ne__(self, other):
        """Compare whether two namespace objects are not equal."""
        return not self.__eq__(other)

    def __mod__(self, other):
        """Apply modulo on the namespace id."""
        return self.id.__mod__(other)

    def __sub__(self, other):
        """Apply subtraction on the namespace id."""
        return self.id - other

    def __add__(self, other):
        """Apply addition on the namespace id."""
        return self.id + other

    def _cmpkey(self):
        """Return the ID as a comparison key."""
        return self.id

    def __repr__(self) -> str:
        """Return a reconstructable representation."""
        standard_attr = ['id', 'custom_name', 'canonical_name', 'aliases']
        extra = [(key, self.__dict__[key])
                 for key in sorted(self.__dict__)
                 if key not in standard_attr]

        if extra:
            kwargs = ', ' + ', '.join(
                key + f'={value!r}' for key, value in extra)
        else:
            kwargs = ''

        return '{}(id={}, custom_name={!r}, canonical_name={!r}, ' \
               'aliases={!r}{})' \
               .format(self.__class__.__name__,
                       self.id,
                       self.custom_name,
                       self.canonical_name,
                       self.aliases,
                       kwargs)

    @staticmethod
    def default_case(id, default_case=None):
        """Return the default fixed case value for the namespace ID."""
        # https://www.mediawiki.org/wiki/Manual:$wgCapitalLinkOverrides#Warning
        if id > 0 and id % 2 == 1:  # the talk ns has the non-talk ns case
            id -= 1
        if id in (-1, 2, 8):
            return 'first-letter'

        return default_case

    @classmethod
    def builtin_namespaces(cls, case: str = 'first-letter'):
        """Return a dict of the builtin namespaces."""
        return {i: cls(i, case=cls.default_case(i, case))
                for i in range(-2, 16)}

    @staticmethod
    def normalize_name(name):
        """
        Remove an optional colon before and after name.

        TODO: reject illegal characters.
        """
        if name == '':
            return ''

        name = name.replace('_', ' ')
        parts = name.split(':', 4)
        count = len(parts)
        if count > 3 or (count == 3 and parts[2]):
            return False

        # Discard leading colon
        if count >= 2 and not parts[0] and parts[1]:
            return parts[1].strip()

        if parts[0]:
            return parts[0].strip()

        return False


# Set Namespace.FOO to be BuiltinNamespace.FOO for each builtin namespace
for item in BuiltinNamespace:
    setattr(Namespace, item.name, item)


class NamespacesDict(Mapping, SelfCallMixin):

    """
    An immutable dictionary containing the Namespace instances.

    It adds a deprecation message when called as the 'namespaces' property of
    APISite was callable.
    """

    def __init__(self, namespaces) -> None:
        """Create new dict using the given namespaces."""
        super().__init__()
        self._namespaces = namespaces
        self._namespace_names = {}
        for namespace in self._namespaces.values():
            for name in namespace:
                self._namespace_names[name.lower()] = namespace

    def __iter__(self):
        """Iterate over all namespaces."""
        return iter(self._namespaces)

    def __getitem__(self, key: Union[Namespace, int, str]) -> Namespace:
        """
        Get the namespace with the given key.

        :param key: namespace key
        """
        if isinstance(key, (Namespace, int)):
            try:
                return self._namespaces[key]
            except KeyError:
                raise KeyError('{} is not a known namespace. Maybe you should '
                               'clear the api cache.'.format(key))

        namespace = self.lookup_name(key)
        if namespace:
            return namespace

        return super().__getitem__(key)

    def __getattr__(self, attr: Union[Namespace, int, str]) -> Namespace:
        """
        Get the namespace with the given key.

        :param attr: namespace key
        """
        # lookup_name access _namespaces
        if attr.isupper():
            if attr == 'MAIN':
                return self[0]

            namespace = self.lookup_name(attr)
            if namespace:
                return namespace

        return self.__getattribute__(attr)

    def __len__(self) -> int:
        """Get the number of namespaces."""
        return len(self._namespaces)

    def lookup_name(self, name: str) -> Optional[Namespace]:
        """
        Find the Namespace for a name also checking aliases.

        :param name: Name of the namespace.
        """
        name = Namespace.normalize_name(name)
        if name is False:
            return None
        return self.lookup_normalized_name(name.lower())

    def lookup_normalized_name(self, name: str) -> Optional[Namespace]:
        """
        Find the Namespace for a name also checking aliases.

        The name has to be normalized and must be lower case.

        :param name: Name of the namespace.
        """
        return self._namespace_names.get(name)

    def resolve(self, identifiers) -> List[Namespace]:
        """
        Resolve namespace identifiers to obtain Namespace objects.

        Identifiers may be any value for which int() produces a valid
        namespace id, except bool, or any string which Namespace.lookup_name
        successfully finds. A numerical string is resolved as an integer.

        :param identifiers: namespace identifiers
        :type identifiers: iterable of str or Namespace key,
            or a single instance of those types
        :return: list of Namespace objects in the same order as the
            identifiers
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if isinstance(identifiers, (str, Namespace)):
            identifiers = [identifiers]
        else:
            # convert non-iterators to single item list
            try:
                iter(identifiers)
            except TypeError:
                identifiers = [identifiers]

        # lookup namespace names, and assume anything else is a key.
        # int(None) raises TypeError; however, bool needs special handling.
        namespaces = self._namespaces
        result = [NotImplemented if isinstance(ns, bool)
                  else self._lookup_name(ns)
                  if isinstance(ns, str) and not ns.lstrip('-').isdigit()
                  else namespaces[int(ns)] if int(ns) in namespaces
                  else None
                  for ns in identifiers]

        if NotImplemented in result:
            raise TypeError('identifiers contains inappropriate types: {!r}'
                            .format(identifiers))

        # Namespace.lookup_name returns None if the name is not recognised
        if None in result:
            raise KeyError(
                'Namespace identifier(s) not recognised: {}'
                .format(','.join(str(identifier)
                                 for identifier, ns in zip(identifiers, result)
                                 if ns is None)))

        return result

    def _lookup_name(self, name):
        name = Namespace.normalize_name(name)
        if name is False:
            return None
        name = name.lower()

        for namespace in self._namespaces.values():
            if namespace._contains_lowercase_name(name):
                return namespace

        return None
