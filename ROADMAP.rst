Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* BaseBot.stop() method is deprecated in favour of BaseBot.generator.close()
* Escape bot password correctly (T259488)


Future release notes
~~~~~~~~~~~~~~~~~~~~

* 4.0.0: Deprecate tools.UnicodeMixin and tools.IteratorNextMixin will be removed
* 4.0.0: Site.Family() function will be removed in favour of Family.load() method
* 4.0.0: Site.getExpandedString method will be removed in favour of expand_text
* 4.0.0: Unused parameters of page methods like forceReload, insite, throttle, step will be removed
* 4.0.0: site/family methods code2encodings and code2encoding will be removed in favour of encoding/endcodings methods
* 4.0.0: Methods deprecated for 6 years or longer will be removed
* 3.0.20200508: Page.getVersionHistory and Page.fullVersionHistory() methods will be removed (T136513, T151110)
* 3.0.20200306: Support of MediaWiki releases below 1.19 will be dropped (T245350)
