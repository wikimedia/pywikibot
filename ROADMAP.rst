Current Release Changes
=======================

* Apply client-side filtering for *maxsize* in misermode in
  :meth:`Site.allpages()<pywikibot.site._generators.GeneratorsMixin.allpages>` (:phab:`T402995`)
* Add :attr:`filter_func()<data.api.APIGeneratorBase.filter_func>` and :meth:`filter_item()
  <data.api.APIGeneratorBase.filter_item>` filter function in :class:`APIGeneratorBase
  <data.api.APIGeneratorBase>` and modify `generator` property to implement filtering in
  `APIGeneratorBase` subclasses (:phab:`T402995`)
* All parameters of :meth:`Site.allpages()<pywikibot.site._generators.GeneratorsMixin.allpages>`
  except *start* must be given as keyword arguments.
* Add support for bewwiktionary (:phab:`T402136`)
* Add user-agent header to :mod:`eventstreams` requests (:phab:`T402796`)
* Update i18n
* Save global options in :attr:`bot.global_args` (:phab:`T250034`)
* Update :mod:`plural` forms from unicode.org (:phab:`T114978`)
* Add :class:`textlib.SectionList` to hold :attr:`textlib.Content.sections` (:phab:`T401464`)
* :class:`pywikibot.Coordinate` parameters are keyword only
* Add *strict* parameter to :meth:`Site.unconnected_pages()
  <pywikibot.site._extensions.unconnected_pages>` and :func:`pagegenerators.UnconnectedPageGenerator`
  (:phab:`T401699`)
* Raise ValueError if a VAR_POSITIONAL parameter like *\*args* is used with
  :class:`tools.deprecate_positionals` decorator
* Add :meth:`get_value_at_timestamp()<pywikibot.ItemPage.get_value_at_timestamp>` API
  to :class:`pywikibot.ItemPage` (:phab:`T400612`)
* Clean up :mod:`setup` module (:phab:`T396356`)
* Implement :meth:`pywikibot.ItemPage.get_best_claim` (:phab:`T400610`)
* Add *expiry* parameter to :meth:`BasePage.watch()<page.BasePage.watch>` and
  :meth:`Site.watch()<pywikibot.site._apisite.APISite.watch>`; fix the methods to return False if
  page is missing and no expiry is set (:phab:`T330839`)


Deprecations
============

Pending removal in Pywikibot 13
-------------------------------

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


Pending removal in Pywikibot 11
-------------------------------

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
