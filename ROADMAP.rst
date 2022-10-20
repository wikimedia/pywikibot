Current release 8.0.0
^^^^^^^^^^^^^^^^^^^^^

* Enable 2FA login (:phab:`T186274`)
* :meth:`Page.editTime()<page.BasePage.editTime>` was replaced by
  :attr:`Page.latest_revision.timestamp<page.BasePage.latest_revision>`
* Raise a generic ServerError if requests response is a ServerError (:phab:`T320590`)
* Add a new variable 'private_folder_permission' to config.py (:phab:`T315045`)
* Fix disolving script_paths for site-package (:phab:`T320530`)
* Respect limit argument with Board.topics() (:phab:`T138215`, :phab:`T138307`)
* The ``parent_id`` and ``content_model`` attributes of :class:`page.Revision` were removed in favour of ``parentid`` and ``contentmodel``
* Support for MediaWiki < 1.27 was dropped
* ListBoxWindows class of :mod:`userinterfaces.gui` was removed
* L10N and i18n updates
* Adjust subprocess args in :mod:`tools.djvu`
* Short site value can be given if site code is equal to family like ``-site:meta`` or ``-site:commons``
* Require Python 3.6.1+ with Pywikibot and drop support for Python 3.6.0 (:phab:`T318912`)
* pymysql >= 0.9.3 is required (:phab:`T216741`)
* Python 3.5 support was dropped (:phab:`T301908`)
* MediaWiki API cross reference was added to the documentation

Deprecations
^^^^^^^^^^^^

* 8.0.0: :meth:`Page.editTime()<page.BasePage.editTime>` method is deprecated and should be replaced by
  :attr:`Page.latest_revision.timestamp<page.BasePage.latest_revision>`
* 7.7.0: :mod:`tools.threading` classes should no longer imported from :mod:`tools`
* 7.6.0: :mod:`tools.itertools` datatypes should no longer imported from :mod:`tools`
* 7.6.0: :mod:`tools.collections` datatypes should no longer imported from :mod:`tools`
* 7.5.0: :mod:`textlib`.tzoneFixedOffset class will be removed in favour of :class:`time.TZoneFixedOffset`
* 7.4.0: ``FilePage.usingPages()`` was renamed to :meth:`using_pages()<pywikibot.FilePage.using_pages>`
* 7.2.0: ``tb`` parameter of :func:`exception()<pywikibot.exception>` function was renamed to ``exc_info``
* 7.2.0: XMLDumpOldPageGenerator is deprecated in favour of a ``content`` parameter of
  :func:`XMLDumpPageGenerator<pagegenerators.XMLDumpPageGenerator>` (:phab:`T306134`)
* 7.2.0: RedirectPageBot and NoRedirectPageBot bot classes are deprecated in favour of
  :attr:`use_redirects<bot.BaseBot.use_redirects>` attribute
* 7.2.0: :func:`tools.formatter.color_format<tools.formatter.color_format>` is deprecated and will be removed
* 7.1.0: Unused `get_redirect` parameter of Page.getOldVersion() will be removed
* 7.1.0: APISite._simple_request() will be removed in favour of APISite.simple_request()
* 7.0.0: User.isBlocked() method is renamed to is_blocked for consistency
* 7.0.0: Private BaseBot counters _treat_counter, _save_counter, _skip_counter will be removed in favour of collections.Counter counter attribute
* 7.0.0: A boolean watch parameter in Page.save() is deprecated and will be desupported
* 7.0.0: baserevid parameter of editSource(), editQualifier(), removeClaims(), removeSources(), remove_qualifiers() DataSite methods will be removed
* 7.0.0: Values of APISite.allpages() parameter filterredir other than True, False and None are deprecated
* 6.5.0: OutputOption.output() method will be removed in favour of OutputOption.out property
* 6.5.0: Infinite rotating file handler with logfilecount of -1 is deprecated
* 6.4.0: 'allow_duplicates' parameter of :func:`tools.itertools.intersect_generators` as positional argument is deprecated, use keyword argument instead
* 6.4.0: 'iterables' of :func:`tools.itertools.intersect_generators` given as a list or tuple is deprecated, either use consecutive iterables or use '*' to unpack
* 6.2.0: outputter of OutputProxyOption without out property is deprecated
* 6.2.0: ContextOption.output_range() and HighlightContextOption.output_range() are deprecated
* 6.2.0: Error messages with '%' style is deprecated in favour for str.format() style
* 6.2.0: page.url2unicode() function is deprecated in favour of tools.chars.url2string()
* 6.2.0: Throttle.multiplydelay attribute is deprecated
* 6.2.0: SequenceOutputter.format_list() is deprecated in favour of 'out' property
* 6.0.0: config.register_family_file() is deprecated


Will be removed in Pywikibot 8
------------------------------

* 5.5.0: APISite.redirectRegex() will be removed in favour of APISite.redirect_regex()
