Current release
~~~~~~~~~~~~~~~

* EventStreams "since" parameter settings has been fixed
* Unsupported debug and uploadByUrl parameters of UploadRobot were removed
* Unported compat decode parameter of Page.title() has been removed
* Wikihow family file was added (T249814)
* Improve performance of CosmeticChangesToolkit.translateMagicWords
* Prohibit positional arguments with Page.title()
* Functions dealing with stars list were removed
* Some pagegenerators functions were deprecated which should be replaced by site generators
* LogEntry became a UserDict; all content can be accessed by its key
* URLs for new toolforge.org domain were updated
* pywikibot.__release__ was deprecated
* Use one central point for framework version (T106121, T171886, T197936, T253719)
* rvtoken parameter of Site.loadrevisions() and Page.revisions() has been dropped (T74763)
* getFilesFromAnHash and getImagesFromAnHash Site methods have been removed
* Site and Page methods deprecated for 10 years or longer have been removed
* Support for Python 2 and 3.4 has been dropped (T213287, T239542)
* Bugfixes and improvements
* Localisation updates

Future releases
~~~~~~~~~~~~~~~

* 4.0.0: Site.Family() function will be removed in favour of Family.load() method
* 4.0.0: Site.getExpandedString method will be removed in favour of expand_text
* 4.0.0: Unused parameters of page methods like forceReload, insite, throttle, step will be removed
* 4.0.0: site/family methods code2encodings and code2encoding will be removed in favour of encoding/endcodings methods
* 4.0.0: Methods deprecated for 6 years or longer will be removed
* 3.0.20200703: tools.count, tools.Counter, tools.OrderedDict and ContextManagerWrapper will be removed
* 3.0.20200508: Page.getVersionHistory and Page.fullVersionHistory() methods will be removed (T136513, T151110)
* 3.0.20200306: Support of MediaWiki releases below 1.19 will be dropped (T245350)
