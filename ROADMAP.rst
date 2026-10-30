Release 12
==========

**Improvements**

* (No changes yet)

**Bugfixes**

* Only take a source starting with a URL scheme as URL in :meth:`FilePage.upload()
  <pywikibot.FilePage.upload>` and :class:`specialbots.UploadRobot`; a local path
  containing ``://`` like ``C://image.png`` is uploaded as file. :func:`tools.is_url`
  was added for this check. (:phab:`T164450`)

**Code cleanups**

* Remove the deprecated conversion of ``bot=None`` to ``bot=True`` in
  :meth:`APISite.editpage()<pywikibot.site._apisite.APISite.editpage>`; use
  a boolean value for *bot*.
* Remove the deprecated ``xmlreader.parseRestrictions`` alias; use
  :meth:`xmlreader.XmlDump.parse_restrictions` instead.
* Remove ``Page.main_authors()``, deprecated since 9.3. Use
  :meth:`Page.authorship()<page._toolforge.WikiBlameMixin.authorship>` instead.

**Other breaking changes**

* :class:`xmlreader.XmlDump` now defaults to ``revisions='latest'`` instead of
  ``'first_found'``. Use ``revisions='first_found'`` explicitly to retain the
  previous revision selection. (:phab:`T340804`)

* Return insertion-ordered plain dictionaries for template parameters from
  :func:`textlib.extract_templates_and_params`,
  :func:`textlib.extract_templates_and_params_regex_simple`, and
  :attr:`page.Page.raw_extracted_templates`. These replace ``OrderedDict``;
  mapping equality no longer compares parameter order, and ``OrderedDict``
  methods such as ``move_to_end()`` are no longer available on the results.

Deprecations
============

This section lists features, methods, parameters, or attributes that are deprecated
and scheduled for removal in future Pywikibot releases.

Deprecated items may still work in the current release but are no longer recommended for use.
Users should update their code according to the recommended alternatives.

Pywikibot follows a clear deprecation policy: features are typically deprecated in one release and
removed in the third subsequent major release, remaining available for the two releases in between.


Pending removal in Pywikibot 13
-------------------------------

* 10.7.0: The old ``(type, value, traceback)`` signature in
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

Pending removal in Pywikibot 14
-------------------------------

* 11.9.0: The *force* parameter of :class:`pywikibot.User` methods was renamed to
  *refresh*. The old parameter name will be removed. (:phab:`T433225`)
* 11.8.0: The ``config.maxlag`` setting was renamed to :ref:`write_maxlag
  <Settings to Avoid Server Overload>`. The old setting variable will be dropped. (:phab:`T421642`)
* 11.8.0: Public *reason* and *comment* parameters used for page-action and
  upload summaries were renamed to *summary*. The old parameter names will
  be removed. (:phab:`T62442`)
* 11.7.0: :meth:`page.BasePage.getOldVersion` is now deprecated in favour of
  :meth:`get_revision(oldid, content=True).text<page.BasePage.get_revision>`. (:phab:`T433799`)
* 11.7.0: The *lang* parameter of the :func:`i18n.altlang` function is positional-only. Passing
  *lang* as a keyword argument is deprecated.
* 11.7.0: The interface of :meth:`APISite.assert_valid_iter_params()
  <pywikibot.site._apisite.APISite.assert_valid_iter_params>` was changed. The *msg_prefix*
  parameter is now positional-only and the *is_ts* parameter is now keyword-only. The previous
  interface is deprecated.
* 11.6.0: The *top_only* parameter of :meth:`APISite.usercontribs
  <pywikibot.site._generators.GeneratorsMixin.usercontribs>` has been deprecated; use *top* instead
  (:phab:`T308961`)
* 11.5.0: :func:`family.Family.post_get_convert` and :func:`family.Family.pre_put_convert` functions
  are deprecated and will be removed (:phab:`T431188`)
* 11.5.0: ``exceptions.TimeoutError`` is deprecated in favour of :exc:`exceptions.ApiTimeoutError`
* 11.5.0: :mod:`config` ``textfile_encoding`` variable will be removed; use 'utf-8' directly instead
  (:phab:`T430454`)
* 11.4.0: The signature of :meth:`APISite.allusers()
  <pywikibot.site._generators.GeneratorsMixin.allusers>` was changed;
  all parameters are keyword-only.
* 11.4.0: The signature of :func:`tools.open_archive` was changed. *filename* parameter is
  positional only, *use_extension* is keyword only.
* 11.0.0: The User-Agent variable *script_product* is deprecated; use *script* instead.
  The User-Agent variable *version* is deprecated; use *revision* instead.
  The User-Agent variables *lang*, *code* and *family* are deprecated; use *site* instead.
* 11.0.0: Positional argument for *block* parameter of :func:`pywikibot.async_manager` is
  deprecated; use a keyword argument instead.
* 11.0.0: Keyword parameters for *text_a* and *text_b* of :class:`diff.PatchManager` are deprecated.
  Positional parameters for *by_letter* and *replace_invisible* are deprecated.
