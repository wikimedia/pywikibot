Current Release Changes
=======================

* Use Lock object in :class:`comms.http.PywikibotCookieJar` for thread-safe saving (:phab:`T396309`)
* Raise TypeError instead of ValueError in :func:`i18n.translate` if *parameter* is not a mapping
* Recognise wildcard in :mod:`config.usernames<config>` when running
  :mod:`login<pywikibot.scripts.login>` script (:phab:`T110411`)
* Search for http and https by default in :meth:`Site.exturlusage()
  <.site._generators.GeneratorsMixin.exturlusage>` (:phab:`T396280`)
* Add login methods overview to :mod:`login` module (:phab:`T396204`)
* Enable EmailAuth with :class:`login.ClientLoginManager` (:phab:`T395703`)
* Move :mod:`tools.threading.RLock<tools.threading>` to :mod:`backports` module (:phab:`T395182`)
* Only show the description passed to :class:`specialbots.UploadRobot` if it is to be verified (:phab:`T394895`)
* Add support for Python 3.15 (:phab:`T395177`)


Current Deprecations
====================

* 10.0.0: 'millenia' argument for *precision* parameter of :class:`pywikibot.WbTime` is deprecated;
  'millennium' must be used instead.
* 10.0.0: *includeredirects* parameter of :func:`pagegenerators.AllpagesPageGenerator` and
  :func:`pagegenerators.PrefixingPageGenerator` is deprecated and should be replaced by *filterredir*
* 9.6.0: :meth:`BaseSite.languages()<pywikibot.site._basesite.BaseSite.languages>` will be removed in favour of
  :attr:`BaseSite.codes<pywikibot.site._basesite.BaseSite.codes>`
* 9.5.0: :meth:`DataSite.getPropertyType()<pywikibot.site._datasite.DataSite.getPropertyType>` will be removed
  in favour of :meth:`DataSite.get_property_type()<pywikibot.site._datasite.DataSite.get_property_type>`
* 9.3.0: :meth:`page.BasePage.userName` and :meth:`page.BasePage.isIpEdit` are deprecated in favour of
  ``user`` or ``anon`` attributes of :attr:`page.BasePage.latest_revision` property
* 9.2.0: Imports of :mod:`logging` functions from :mod:`bot` module is deprecated and will be desupported
* 9.2.0: *total* argument in ``-logevents`` pagegenerators option is deprecated;
  use ``-limit`` instead (:phab:`T128981`)
* 9.0.0: The *content* parameter of :meth:`proofreadpage.IndexPage.page_gen` is deprecated and will be ignored
  (:phab:`T358635`)
* 9.0.0: ``userinterfaces.transliteration.transliterator`` was renamed to :class:`Transliterator
  <userinterfaces.transliteration.Transliterator>`
* 9.0.0: ``next`` parameter of :meth:`userinterfaces.transliteration.transliterator.transliterate` was renamed to
  ``succ``
* 9.0.0: ``type`` parameter of :meth:`site.APISite.protectedpages()
  <pywikibot.site._generators.GeneratorsMixin.protectedpages>` was renamed to ``protect_type``
* 9.0.0: ``all`` parameter of :meth:`site.APISite.namespace()<pywikibot.site._apisite.APISite.namespace>` was renamed to
  ``all_ns``
* 9.0.0: ``filter`` parameter of :func:`date.dh` was renamed to ``filter_func``
* 9.0.0: ``dict`` parameter of :class:`data.api.OptionSet` was renamed to ``data``
* 9.0.0: ``pywikibot.version.get_toolforge_hostname()`` is deprecated without replacement
* 9.0.0: ``allrevisions`` parameter of :class:`xmlreader.XmpDump` is deprecated, use ``revisions`` instead
  (:phab:`T340804`)
* 9.0.0: ``iteritems`` method of :class:`data.api.Request` will be removed in favour of ``items``
* 9.0.0: ``SequenceOutputter.output()`` is deprecated in favour of :attr:`tools.formatter.SequenceOutputter.out`
  property


Pending removal in Pywikibot 11
-------------------------------

* 8.4.0: *modules_only_mode* parameter of :class:`data.api.ParamInfo`, its *paraminfo_keys* class attribute
  and its preloaded_modules property will be removed
* 8.4.0: *dropdelay* and *releasepid* attributes of :class:`throttle.Throttle` will be removed
  in favour of *expiry* class attribute
* 8.2.0: :func:`tools.itertools.itergroup` will be removed in favour of :func:`backports.batched`
* 8.2.0: *normalize* parameter of :meth:`WbTime.toTimestr` and :meth:`WbTime.toWikibase` will be removed
* 8.1.0: Dependency of :exc:`exceptions.NoSiteLinkError` from :exc:`exceptions.NoPageError` will be removed
* 8.1.0: ``exceptions.Server414Error`` is deprecated in favour of :exc:`exceptions.Client414Error`
* 8.0.0: :meth:`Timestamp.clone()<pywikibot.time.Timestamp.clone>` method is deprecated
  in favour of ``Timestamp.replace()`` method.
* 8.0.0: :meth:`family.Family.maximum_GET_length` method is deprecated in favour of
  :ref:`config.maximum_GET_length<Account Settings>` (:phab:`T325957`)
* 8.0.0: ``addOnly`` parameter of :func:`textlib.replaceLanguageLinks` and
  :func:`textlib.replaceCategoryLinks` are deprecated in favour of ``add_only``
* 8.0.0: :class:`textlib.TimeStripper` regex attributes ``ptimeR``, ``ptimeznR``, ``pyearR``, ``pmonthR``,
  ``pdayR`` are deprecated in favour of ``patterns`` attribute which is a
  :class:`textlib.TimeStripperPatterns`.
* 8.0.0: :class:`textlib.TimeStripper` ``groups`` attribute is deprecated in favour of ``textlib.TIMEGROUPS``
* 8.0.0: :meth:`LoginManager.get_login_token<login.ClientLoginManager.get_login_token>` was
  replaced by ``login.ClientLoginManager.site.tokens['login']``
* 8.0.0: ``data.api.LoginManager()`` is deprecated in favour of :class:`login.ClientLoginManager`
* 8.0.0: :meth:`APISite.messages()<pywikibot.site._apisite.APISite.messages>` method is deprecated in favour of
  :attr:`userinfo['messages']<pywikibot.site._apisite.APISite.userinfo>`
* 8.0.0: :meth:`Page.editTime()<page.BasePage.editTime>` method is deprecated and should be replaced by
  :attr:`Page.latest_revision.timestamp<page.BasePage.latest_revision>`
