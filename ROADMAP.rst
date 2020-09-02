Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* Don't check for valid Family/Site if running generate_user_files.py (T261771)
* Remove socket_timeout fix in config2.py introduced with T103069
* Prevent huge traceback from underlying python libraries (T253236)
* Localisation updates


Future release notes
~~~~~~~~~~~~~~~~~~~~

* 4.2.0: tools.StringTypes will be removed
* 4.1.0: Deprecated editor.command will be removed
* 4.1.0: tools.open_compressed, tools.UnicodeType and tools.signature will be removed
* 4.1.0: comms.PywikibotCookieJar and comms.mode_check_decorator will be removed
* 4.0.0: Deprecated tools.UnicodeMixin and tools.IteratorNextMixin will be removed
* 4.0.0: Unused parameters of page methods like forceReload, insite, throttle, step will be removed
* 4.0.0: Methods deprecated for 6 years or longer will be removed
* 3.0.20200508: Page.getVersionHistory and Page.fullVersionHistory() methods will be removed (T136513, T151110)
* 3.0.20200306: Support of MediaWiki releases below 1.19 will be dropped (T245350)
