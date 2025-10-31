Current Release Changes
=======================

* Add support for pcmwikiquote and minwikisource. (:phab:`T408345`, :phab:`T408353`)
* Deprecate dysfunctional :meth:`APISite.alllinks()
  <pywikibot.site._generators.GeneratorsMixin.alllinks>`. (:phab:`T359427`, :phab:`T407708`)
* Refactor ``replace_magicwords`` in
  :meth:`cosmetic_changes.CosmeticChangesToolkit.translateMagicWords`. (:phab:`T396715`)
* Deprecate old ``(type, value, traceback)`` signature in
  :meth:`tools.collections.GeneratorWrapper.throw`. (:phab:`T340641`)
* Replace default timetravel.mementoweb.org with web.archive.org in :mod:`data.memento` module.
  (:phab:`T400570`, :phab:`T407694`)
* i18n updates


Deprecations
============

This section lists features, methods, parameters, or attributes that are deprecated
and scheduled for removal in future Pywikibot releases.  

Deprecated items may still work in the current release but are no longer recommended for use.
Users should update their code according to the recommended alternatives.  

Pywikibot follows a clear deprecation policy: features are typically deprecated in one release and
removed in in the third subsequent major release, remaining available for the two releases in between.


Pending removal in Pywikibot 11
-------------------------------

* 10.7.0: Dysfunctional :meth:`APISite.alllinks()
  <pywikibot.site._generators.GeneratorsMixin.alllinks>` will be removed.
  (:phab:`T359427`, :phab:`T407708`)
* 10.6.0: Python 3.8 support is deprecated and will be dropped soon
* 8.4.0: :attr:`data.api.QueryGenerator.continuekey` will be removed in favour of
  :attr:`data.api.QueryGenerator.modules`
* 8.4.0: The *modules_only_mode* parameter in the :class:`data.api.ParamInfo` class, its
  *paraminfo_keys* class attribute, and its ``preloaded_modules`` property will be removed
* 8.4.0: The *dropdelay* and *releasepid* attributes of the :class:`throttle.Throttle` class will be
  removed in favour of the *expiry* class attribute
* 8.2.0: The :func:`tools.itertools.itergroup` function will be removed in favour of the
  :func:`backports.batched` function
* 8.2.0: The *normalize* parameter in the :meth:`pywikibot.WbTime.toTimestr` and
  :meth:`pywikibot.WbTime.toWikibase` methods will be removed
* 8.1.0: The inheritance of the :exc:`exceptions.NoSiteLinkError` exception from
  :exc:`exceptions.NoPageError` will be removed
* 8.1.0: The ``exceptions.Server414Error`` exception is deprecated in favour of the
  :exc:`exceptions.Client414Error` exception
* 8.0.0: The :meth:`Timestamp.clone()<pywikibot.time.Timestamp.clone>` method is deprecated in
  favour of the ``Timestamp.replace()`` method
* 8.0.0: The :meth:`family.Family.maximum_GET_length` method is deprecated in favour of the
  :ref:`config.maximum_GET_length<Account Settings>` configuration option (:phab:`T325957`)
* 8.0.0: The ``addOnly`` parameter in the :func:`textlib.replaceLanguageLinks` and
  :func:`textlib.replaceCategoryLinks` functions is deprecated in favour of ``add_only``
* 8.0.0: The regex attributes ``ptimeR``, ``ptimeznR``, ``pyearR``, ``pmonthR``, and ``pdayR`` of
  the :class:`textlib.TimeStripper` class are deprecated in favour of the ``patterns`` attribute,
  which is a :class:`textlib.TimeStripperPatterns` object
* 8.0.0: The ``groups`` attribute of the :class:`textlib.TimeStripper` class is deprecated in favour
  of the :data:`textlib.TIMEGROUPS` constant
* 8.0.0: The :meth:`LoginManager.get_login_token<login.ClientLoginManager.get_login_token>` method
  has been replaced by ``login.ClientLoginManager.site.tokens['login']``
* 8.0.0: The ``data.api.LoginManager()`` constructor is deprecated in favour of the
  :class:`login.ClientLoginManager` class
* 8.0.0: The :meth:`APISite.messages()<pywikibot.site._apisite.APISite.messages>` method is
  deprecated in favour of the :attr:`userinfo['messages']<pywikibot.site._apisite.APISite.userinfo>`
  attribute
* 8.0.0: The :meth:`Page.editTime()<page.BasePage.editTime>` method is deprecated and should be
  replaced by the :attr:`Page.latest_revision.timestamp<page.BasePage.latest_revision>` attribute


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
