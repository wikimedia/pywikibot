Current release changes
^^^^^^^^^^^^^^^^^^^^^^^

* TextExtracts support was aded (:phab:`T72682`)
* Unused `get_redirect` parameter of Page.getOldVersion() has been dropped
* Provide BasePage.get_parsed_page() a public method
* Provide BuiltinNamespace.canonical_namespaces() with BuiltinNamespace IntEnum
* BuiltinNamespace got a canonical() method
* Enable nested templates with MultiTemplateMatchBuilder (:phab:`T110529`)
* Introduce APISite.simple_request as a public method
* Provide an Uploader class to upload files
* Enable use of deletetalk parameter of the delete API
* Fix contextlib redirection for terminal interfaces (:phab:`T283808`)
* No longer use win32_unicode for Python 3.6+ (:phab:`T281042`, :phab:`T283808`, :phab:`T303373`)
* L10N updates
* -cosmetic_changes (-cc) option allows to assign the value directly instead of toggle it
* distutils.util.strtobool() was implemented as tools.strtobool() due to :pep:`632`
* The "in" operator always return whether the siteinfo contains the key even it is not cached (:phab:`T302859`)
* Siteinfo.clear() and  Siteinfo.is_cached() methods were added

Deprecations
^^^^^^^^^^^^

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
* 5.5.0: APISite.redirectRegex() is deprecated in favour of APISite.redirect_regex()
* 4.0.0: Revision.parent_id is deprecated in favour of Revision.parentid
* 4.0.0: Revision.content_model is deprecated in favour of Revision.contentmodel

