Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* Only run cosmetic changes on wikitext pages (T260489)
* Leave a script gracefully for wrong -lang and -family option (T259756)
* Change meaning of BasePage.text (T260472)
* site/family methods code2encodings() and code2encoding() has been removed in favour of encoding()/endcodings() methods
* Site.getExpandedString() method was removed in favour of expand_text
* Site.Family() function was removed in favour of Family.load() method
* Add wikispore family (T260049)


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
