Current release 7.2.0
^^^^^^^^^^^^^^^^^^^^^

* L10N updates
* Circumvent circular import in tools module (:phab:`T306760`)
* Don't fix html inside syntaxhighlight parts in fixes.py (:phab:`T306723`)
* Make layer parameter optional in `pywikibot.debug()` (:phab:`T85620`)
* Retry for internal_api_error_DBQueryTimeoutError errors due to :phab:`T297708`
* Handle ParserError within xmlreader.XmlDump.parse() instead of raising an exception (:phab:`T306134`)
* XMLDumpOldPageGenerator is deprecated in favour of a `content` parameter (:phab:`T306134`)
* `use_disambig` BaseBot attribute was added to hande disambig skipping
* Deprecate RedirectPageBot and NoRedirectPageBot in favour of `use_redirects` attribute
* tools.formatter.color_format is deprecated and will be removed
* A new and easier color format was implemented; colors can be used like:
    ``'this is a <<green>>colored<<default>> text'``
* Unused and unsupported `xmlreader.XmlParserThread` was removed
* Use upercased IP user titles (:phab:`T306291`)
* Use pathlib to extract filename and file_package in pwb.py
* Fix isbn messages in fixes.py (:phab:`T306166`)
* Fix Page.revisions() with starttime (:phab:`T109181`)
* Use stream_output for messages inside input_list_choice method (:phab:`T305940`)
* Expand simulate query result (:phab:`T305918`)
* Do not delete text when updating a Revision (:phab:`T304786`)
* Re-enable scripts package version check with pwb wrapper (:phab:`T305799`)
* Provide textlib.ignore_case() as a public method
* Don't try to upcast timestamp from global userinfo if global account does not exists (:phab:`T305351`)
* Add Lexeme support for Lexicographical data (:phab:`T189321`, :phab:`T305297`)
* enable all parameters of `APISite.imageusage()` with `FilePage.usingPages()`
* Don't raise `NoPageError` with `file_is_shared` (:phab:`T305182`)
* Fix URL of GoogleOCR
* Handle ratelimit with purgepages() (:phab:`T152597`)
* Add movesubpages parameter to Page.move() and APISite.movepage() (:phab:`T57084`)
* Do not iterate over sys.modules (:phab:`T304785`)


Deprecations
^^^^^^^^^^^^

* Python 3.5 support will be dropped with Python 8 (:phab:`T301908`)
* 7.2.0: XMLDumpOldPageGenerator is deprecated in favour of a `content` parameter (:phab:`T306134`)
* 7.2.0: RedirectPageBot and NoRedirectPageBot bot classes are deprecated in favour of `use_redirects` attribute
* 7.2.0: `tools.formatter.color_format` is deprecated and will be removed
* 7.1.0: win32_unicode.py will be removed with Pywikibot 8
* 7.1.0: Unused `get_redirect` parameter of Page.getOldVersion() will be removed
* 7.1.0: APISite._simple_request() will be removed in favour of APISite.simple_request()
* 7.0.0: The i18n identifier 'cosmetic_changes-append' will be removed in favour of 'pywikibot-cosmetic-changes'
* 7.0.0: User.isBlocked() method is renamed to is_blocked for consistency
* 7.0.0: Require mysql >= 0.7.11 (:phab:`T216741`)
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
* 5.5.0: APISite.redirectRegex() is deprecated in favour of APISite.redirect_regex() and will be removed with Pywikibot 8
* 4.0.0: Revision.parent_id is deprecated in favour of Revision.parentid and will be removed with Pywikibot 8
* 4.0.0: Revision.content_model is deprecated in favour of Revision.contentmodel and will be removed with Pywikibot 8
