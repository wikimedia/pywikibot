Current Release Changes
=======================

* Ignore :exc:`ValueError` durig upcast of :class:`FilePage<pywikibot.page.FilePage>` due to invalid file extension
  (:phab:`T367777`, :phab:`T376452`)
* Provide an entry point to connect foreign scripts with pwb wapper (:phab:`T139143`, :phab:`T139144`)
* Show a warning message for a deleted or unknown :class:`Claim<pywikibot.Claim>` type (:phab:`T374676`)
* ``preload_sites`` maintenance script was removed (:phab:`T348925`)
* Add :meth:`User.renamed_target()<pywikibot.User.renamed_target>` method
* Check whether Claim exists within :meth:`Claim.fromJSON()<pywikibot.Claim.fromJSON>` method (:phab:`T374681`)
* Add :attr:`logentries.LogEntry.params` as a public property
* Add support for several wikis (:phab:`T375435`, :phab:`T375097`, :phab:`T374646`, :phab:`T374817`, :phab:`T375026`)
* Add :meth:`title()<pywikibot.MediaInfo.title>` method to :class:`pywikibot.MediaInfo` (:phab:`T366424`)
* Add tags to the wikibase functions (:phab:`T372513`)
* :func:`diff.get_close_matches_ratio()` function was added
* Initialize super classes of :exc:`EditReplacementError` (:phab:`T212740`)
* Add a hint to import missing module in :mod:`wrapper<pywikibot.scripts.wrapper>` script
* i18n updates

Current Deprecations
====================

* 9.4.0: :mod:`flow` support is deprecated and will be removed (:phab:`T371180`)
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
* 9.0.0: *nullcontext* context manager and *SimpleQueue* queue of :mod:`backports` are derecated
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


Pending removal in Pywikibot 10
-------------------------------

* 9.1.0: :func:`version.svn_rev_info` and :func:`version.getversion_svn` will be removed. SVN is no longer supported.
  (:phab:`T362484`)
* 7.7.0: :mod:`tools.threading` classes should no longer imported from :mod:`tools`
* 7.6.0: :mod:`tools.itertools` datatypes should no longer imported from :mod:`tools`
* 7.6.0: :mod:`tools.collections` datatypes should no longer imported from :mod:`tools`
* 7.5.0: :mod:`textlib`.tzoneFixedOffset class will be removed in favour of :class:`time.TZoneFixedOffset`
* 7.4.0: ``FilePage.usingPages()`` was renamed to :meth:`using_pages()<pywikibot.FilePage.using_pages>`
* 7.3.0: Old color escape sequences like ``\03{color}`` is deprecated in favour of new color format like <<color>>
* 7.3.0: ``linktrail`` method of :class:`family.Family` is deprecated; use :meth:`APISite.linktrail()
  <pywikibot.site._apisite.APISite.linktrail>` instead
* 7.2.0: Positional arguments *decoder*, *layer* and *newline* for :mod:`logging` functions where dropped; keyword
  arguments must be used instead.
* 7.2.0: ``tb`` parameter of :func:`exception()<pywikibot.logging.exception>` function was renamed to ``exc_info``
* 7.2.0: XMLDumpOldPageGenerator is deprecated in favour of a ``content`` parameter of
  :func:`XMLDumpPageGenerator<pagegenerators.XMLDumpPageGenerator>` (:phab:`T306134`)
* 7.2.0: RedirectPageBot and NoRedirectPageBot bot classes are deprecated in favour of
  :attr:`use_redirects<bot.BaseBot.use_redirects>` attribute
* 7.2.0: :func:`tools.formatter.color_format<tools.formatter.color_format>` is deprecated and will be removed
* 7.1.0: Unused ``get_redirect`` parameter of :meth:`Page.getOldVersion()<page.BasePage.getOldVersion>` will be removed
* 7.0.0: User.isBlocked() method is renamed to is_blocked for consistency
* 7.0.0: A boolean watch parameter in Page.save() is deprecated and will be desupported
* 7.0.0: baserevid parameter of editSource(), editQualifier(), removeClaims(), removeSources(), remove_qualifiers()
  DataSite methods will be removed
* 7.0.0: Values of APISite.allpages() parameter filterredir other than True, False and None are deprecated
* 7.0.0: The i18n identifier 'cosmetic_changes-append' will be removed in favour of 'pywikibot-cosmetic-changes'
