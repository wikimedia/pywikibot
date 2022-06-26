Current release 7.5.0
^^^^^^^^^^^^^^^^^^^^^

* *No changes yet*

Deprecations
^^^^^^^^^^^^

* 7.4.0: `FilePage.usingPages()` was renamed to :meth:`using_pages()<pywikibot.FilePage.using_pages>`
* 7.2.0: ``tb`` parameter of :func:`exception()<pywikibot.exception>` function was renamed to ``exc_info``
* 7.2.0: XMLDumpOldPageGenerator is deprecated in favour of a `content` parameter of `XMLDumpPageGenerator` (:phab:`T306134`)
* 7.2.0: RedirectPageBot and NoRedirectPageBot bot classes are deprecated in favour of :attr:`use_redirects<pywikibot.bot.BaseBot.use_redirects>` attribute
* 7.2.0: :func:`tools.formatter.color_format<pywikibot.tools.formatter.color_format>` is deprecated and will be removed
* 7.1.0: Unused `get_redirect` parameter of Page.getOldVersion() will be removed
* 7.1.0: APISite._simple_request() will be removed in favour of APISite.simple_request()
* 7.0.0: User.isBlocked() method is renamed to is_blocked for consistency
* 7.0.0: Private BaseBot counters _treat_counter, _save_counter, _skip_counter will be removed in favour of collections.Counter counter attribute
* 7.0.0: A boolean watch parameter in Page.save() is deprecated and will be desupported
* 7.0.0: baserevid parameter of editSource(), editQualifier(), removeClaims(), removeSources(), remove_qualifiers() DataSite methods will be removed
* 7.0.0: Values of APISite.allpages() parameter filterredir other than True, False and None are deprecated
* 6.5.0: OutputOption.output() method will be removed in favour of OutputOption.out property
* 6.5.0: Infinite rotating file handler with logfilecount of -1 is deprecated
* 6.4.0: 'allow_duplicates' parameter of tools.intersect_generators as positional argument is deprecated, use keyword argument instead
* 6.4.0: 'iterables' of tools.intersect_generators given as a list or tuple is deprecated, either use consecutive iterables or use '*' to unpack
* 6.2.0: outputter of OutputProxyOption without out property is deprecated
* 6.2.0: ContextOption.output_range() and HighlightContextOption.output_range() are deprecated
* 6.2.0: Error messages with '%' style is deprecated in favour for str.format() style
* 6.2.0: page.url2unicode() function is deprecated in favour of tools.chars.url2string()
* 6.2.0: Throttle.multiplydelay attribute is deprecated
* 6.2.0: SequenceOutputter.format_list() is deprecated in favour of 'out' property
* 6.0.0: config.register_family_file() is deprecated


Will be removed in Pywikibot 8
------------------------------

* 7.3.0: Python 3.5 support will be dropped (:phab:`T301908`)
* 7.1.0: win32_unicode.py will be removed
* 7.0.0: The i18n identifier 'cosmetic_changes-append' will be removed in favour of 'pywikibot-cosmetic-changes'
* 7.0.0: pymysql < 0.7.11 will be dropped; require pymysql >= 0.7.11 (:phab:`T216741`)
* 5.5.0: APISite.redirectRegex() will be removed in favour of APISite.redirect_regex()
* 4.0.0: Revision.parent_id will be removed in favour of Revision.parentid
* 4.0.0: Revision.content_model will be removed in favour of Revision.contentmodel
