Release 11 (in development)
===========================

**Improvements**

* Use :class:`backports.RLock` instead of Queue to signal async_manager activity (:phab:`T147178`)
* Add :meth:`User.is_partial_blocked()<pywikibot.User.is_partial_blocked>` and methods
  :meth:`APISite.is_partial_blocked()<pywikibot.site._apisite.APISite.is_partial_blocked>` to detect
  partial blocks (:phab:`T412613`)
* Add :meth:`get_block_info()<pywikibot.User.get_block_info>` method to :class:`pywikibot.User`
  class to retrieve detailed block information including block ID, reason, expiry, and restrictions
  (:phab:`T412613`)
* Java based GraalPy is supported but Pillow cannot be used (:phab:`T412739`)
* Free threading Python is supported with some restrictions
  (:phab:`T408131`, :phab:`T412605`, :phab:`T412624`)
* i18n updates
* Provide a security policy with Pywikibot (:phab:`T410753`)
* Show a friendly install message with :mod:`pwb<pywikibot.scripts.wrapper>` wrapper
  when mandatory packages are missing (:phab:`T409662`)
* Update `tools._unidata.__category_cf` dict for :func:`tools.chars.contains_invisible` and
  :func:`tools.chars.replace_invisible` to unicode version 17.0.0
* Update Docker files to Python 3.12 (:phab:`T408997`)

**Bugfixes**

* Handle `lockmanager-fail-conflict` API error in :meth:`data.api.Request.submit` as retryable
  (:phab:`T396984`)
* Prevent login loop in :mod:`data.superset` with unsupported auth methods (:phab:`T408287`)

**Code cleanups**

* The undocumented ``page_put_queue_busy`` was removed without deprecation period.
* Dysfunctional :meth:`APISite.alllinks()
  <pywikibot.site._generators.GeneratorsMixin.alllinks>` was removed.
  (:phab:`T359427`, :phab:`T407708`)
* The inheritance of the :exc:`exceptions.NoSiteLinkError` exception from
  :exc:`exceptions.NoPageError` was removed
* The *dropdelay* and *releasepid* attributes of the :class:`throttle.Throttle` class was
  removed in favour of the *expiry* class attribute.
* The regex attributes ``ptimeR``, ``ptimeznR``, ``pyearR``, ``pmonthR``, and ``pdayR`` of
  the :class:`textlib.TimeStripper` class was removed in favour of the ``patterns`` attribute,
  which is a :class:`textlib.TimeStripperPatterns` object.
* The ``groups`` attribute of the :class:`textlib.TimeStripper` was removed in favour
  of the :data:`textlib.TIMEGROUPS` constant.
* The ``addOnly`` parameter in the :func:`textlib.replaceLanguageLinks` and
  :func:`textlib.replaceCategoryLinks` was dropped in favour of ``add_only``.
* ``load_tokens`` method of :class:`TokenWallet<pywikibot.site._tokenwallet.TokenWallet>` was
  removed; ``clear`` method can be used instead.
* No longer support legacy API tokens of MediaWiki 1.23 and older. (:phab:`270380`, :phab:`306637`)
* ``use_hard_category_redirect`` Site and Family properties were removed. (:phab:`T348953`)
* The *all* parameter of :meth:`APISite.get_tokens()<pywikibot.site._apisite.APISite.get_tokens>``
  was removed; use an empty string instead.
* ``APISite.validate_tokens()`` method was removed.
* ``APISite.messages()`` method was removed in favour of the
  :attr:`userinfo['messages']<pywikibot.site._apisite.APISite.userinfo>` attribute
* ``Page.editTime()`` method was removed; :attr:`Page.latest_revision.timestamp
  <page.BasePage.latest_revision>` attribute can be used instead
* ``data.api.QueryGenerator.continuekey`` was be removed in favour of
  :attr:`data.api.QueryGenerator.modules`
* The ``Timestamp.clone()`` method was removed in favour of the ``Timestamp.replace()`` method
* The ``tools.itertools.itergroup`` function was removed in favour of the
  :func:`backports.batched` or :pylib:`itertools.batched<itertools#itertools.batched>` function.
* The ``get_login_token()`` method of :class:`login.ClientLoginManager`
  was removed and can be replaces by ``login.LoginManager.site.tokens['login']``
* The :meth:`family.Family.maximum_GET_length` method was removed in favour of the
  :ref:`config.maximum_GET_length<Account Settings>` configuration option (:phab:`T325957`)
* The ``exceptions.Server414Error`` exception was replaced by
  :exc:`exceptions.Client414Error` exception
* The *modules_only_mode* parameter in the :class:`data.api.ParamInfo` class, its
  *paraminfo_keys* class attribute, and its ``preloaded_modules`` property was removed
* The ``data.api.LoginManager()`` constructor was removed in favour of the
  :class:`login.ClientLoginManager` class
* The `normalize` parameter was removed from the
  :meth:`pywikibot.WbTime.toTimestr` and :meth:`pywikibot.WbTime.toWikibase`
  methods in Pywikibot 8.2. Since Pywikibot 11, passing `normalize` as an argument
  raises an error, because support for legacy arguments via was removed.
* Several typing types were removed from :mod:`backports`.
* The ``cache`` decorator was removed from :mod:`backports`. The :pylib:`@functools.cache()
  <functools#functools.cache>` can be used instead. (:phab:`T401802`)
* The functions ``removeprefix`` and ``removesuffix`` were removed from :mod:`backports`. The
  :pylib:`stdlib methods<stdtypes.html#str.removeprefix>` can be used instead. (:phab:`T401802`)

**Other breaking changes**

* Package requirements were updated (``beautifulsoup4``, ``fake-useragent``, ``mwoauth``,
  ``mwparserfromhell``, ``packaging``, ``Pillow``, ``pydot``, ``PyMySQL``, ``python-stdnum``,
  ``requests``, ``requests-sse``, ``wikitextparser``)
* Python 3.8 support was dropped. (:phab:`T401802`)
* Remove predefined ``yu-tld`` fix in :mod:`fixes`. (:phab:`T402088`)

Deprecations
============

This section lists features, methods, parameters, or attributes that are deprecated
and scheduled for removal in future Pywikibot releases.

Deprecated items may still work in the current release but are no longer recommended for use.
Users should update their code according to the recommended alternatives.

Pywikibot follows a clear deprecation policy: features are typically deprecated in one release and
removed in in the third subsequent major release, remaining available for the two releases in between.


Pending removal in Pywikibot 12
-------------------------------

* 9.6.0: :meth:`BaseSite.languages()<pywikibot.site._basesite.BaseSite.languages>` will be removed in
  favour of :attr:`BaseSite.codes<pywikibot.site._basesite.BaseSite.codes>`
* 9.5.0: :meth:`DataSite.getPropertyType()<pywikibot.site._datasite.DataSite.getPropertyType>` will be removed
  in favour of :meth:`DataSite.get_property_type()<pywikibot.site._datasite.DataSite.get_property_type>`
* 9.3.0: :meth:`page.BasePage.userName` and :meth:`page.BasePage.isIpEdit` are deprecated in favour of
  ``user`` or ``anon`` attributes of :attr:`page.BasePage.latest_revision` property
* 9.3.0: *botflag* parameter of :meth:`Page.save()<page.BasePage.save>`, :meth:`Page.put()
  <page.BasePage.put>`, :meth:`Page.touch()<page.BasePage.touch>` and
  :meth:`Page.set_redirect_target()<page.Page.set_redirect_target>` was renamed to *bot*
* 9.2.0: All parameters of :meth:`Page.templates<page.BasePage.templates>` and
  :meth:`Page.itertemplates()<page.BasePage.itertemplates>` must be given as keyworded arguments
* 9.2.0: Imports of :mod:`logging` functions from the :mod:`bot` module are deprecated and will be desupported
* 9.2.0: *total* argument in ``-logevents`` pagegenerators option is deprecated;
  use ``-limit`` instead (:phab:`T128981`)
* 9.0.0: The *content* parameter of :meth:`proofreadpage.IndexPage.page_gen` is deprecated and will be
  ignored (:phab:`T358635`)
* 9.0.0: ``next`` parameter of :meth:`userinterfaces.transliteration.Transliterator.transliterate` was
  renamed to ``succ``
* 9.0.0: ``userinterfaces.transliteration.transliterator`` object was renamed to :class:`Transliterator
  <userinterfaces.transliteration.Transliterator>`
* 9.0.0: The ``type`` parameter of :meth:`site.APISite.protectedpages()
  <pywikibot.site._generators.GeneratorsMixin.protectedpages>` was renamed to ``protect_type``
* 9.0.0: The ``all`` parameter of :meth:`site.APISite.namespace()
  <pywikibot.site._apisite.APISite.namespace>` was renamed to ``all_ns``
* 9.0.0: ``filter`` parameter of :func:`date.dh` was renamed to ``filter_func``
* 9.0.0: ``dict`` parameter of :class:`data.api.OptionSet` was renamed to ``data``
* 9.0.0: :func:`pywikibot.version.get_toolforge_hostname` is deprecated with no replacement
* 9.0.0: ``allrevisions`` parameter of :class:`xmlreader.XmpDump` is deprecated, use ``revisions`` instead
  (:phab:`T340804`)
* 9.0.0: ``iteritems`` method of :class:`data.api.Request` will be removed in favour of ``items``
* 9.0.0: ``SequenceOutputter.output()`` is deprecated in favour of the
  :attr:`tools.formatter.SequenceOutputter.out` property


Pending removal in Pywikibot 13
-------------------------------

* 10.6.0: The old ``(type, value, traceback)`` signature in
  :meth:`tools.collections.GeneratorWrapper.throw` will be removed in Pywikibot 13, or earlier if it
  is dropped from a future Python release. (:phab:`T340641`)
* 10.6.0: :meth:`Family.isPublic()<family.Family.isPublic>` will be removed (:phab:`T407049`)
* 10.6.0: :meth:`Family.interwiki_replacements<family.Family.interwiki_replacements>` is deprecated;
  use :attr:`Family.code_aliases<family.Family.code_aliases>` instead.
* Keyword argument for *char* parameter of :meth:`Transliterator.transliterate
  <userinterfaces.transliteration.Transliterator.transliterate>` and
  positional arguments for *prev* and *succ* parameters are deprecated.
* 10.6.0: Positional arguments of :func:`daemonize()<daemonize.daemonize>` are deprecated and must
  be given as keyword arguments.
* 10.5.0: Accessing the fallback '*' keys in 'languages', 'namespaces', 'namespacealiases', and
  'skins' properties of :attr:`APISite.siteinfo<pywikibot.site._apisite.APISite.siteinfo>` are
  deprecated and will be removed.
* 10.5.0: The methods :meth:`APISite.protection_types()
  <pywikibot.site._apisite.APISite.protection_types>` and :meth:`APISite.protection_levels()
  <pywikibot.site._apisite.APISite.protection_levels>` are deprecated.
  :attr:`APISite.restrictions<pywikibot.site._apisite.APISite.restrictions>` should be used instead.
* 10.4.0: Require all parameters of :meth:`Site.allpages()
  <pywikibot.site._generators.GeneratorsMixin.allpages>` except *start* to be keyword arguments.
* 10.4.0: Positional arguments of :class:`pywikibot.Coordinate` are deprecated and must be given as
  keyword arguments.
* 10.3.0: :meth:`throttle.Throttle.getDelay` and :meth:`throttle.Throttle.setDelays` were renamed to
  :meth:`get_delay()<throttle.Throttle.get_delay>` and :meth:`set_delays()
  <throttle.Throttle.set_delays>`; the old methods will be removed (:phab:`T289318`)
* 10.3.0: :attr:`throttle.Throttle.next_multiplicity` attribute is unused and will be removed
  (:phab:`T289318`)
* 10.3.0: *requestsize* parameter of :class:`throttle.Throttle` call is deprecated and will be
  dropped (:phab:`T289318`)
* 10.3.0: :func:`textlib.to_latin_digits` will be removed in favour of
  :func:`textlib.to_ascii_digits`, ``NON_LATIN_DIGITS`` of :mod:`userinterfaces.transliteration`
  will be removed in favour of ``NON_ASCII_DIGITS`` (:phab:`T398146#10958283`)
* 10.2.0: :mod:`tools.threading.RLock<tools.threading>` is deprecated and moved to :mod:`backports`
  module. The :meth:`backports.RLock.count` method is also deprecated. For Python 3.14+ use ``RLock``
  from Python library ``threading`` instead. (:phab:`T395182`)
* 10.1.0: *revid* and *date* parameters of :meth:`Page.authorship()
  <page._toolforge.WikiBlameMixin.authorship>` were dropped
* 10.0.0: *last_id* of :class:`comms.eventstreams.EventStreams` was renamed to *last_event_id*
  (:phab:`T309380`)
* 10.0.0: 'millenia' argument for *precision* parameter of :class:`pywikibot.WbTime` is deprecated;
  'millennium' must be used instead
* 10.0.0: *includeredirects* parameter of :func:`pagegenerators.AllpagesPageGenerator` and
  :func:`pagegenerators.PrefixingPageGenerator` is deprecated and should be replaced by *filterredir*
