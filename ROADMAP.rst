Current release
~~~~~~~~~~~~~~~

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

* 4.0.0: Methods deprecated for 8 years or longer will be removed
* 3.0.20200703: Unsupported debug parameter of UploadRobot will be removed
* 3.0.20200703: Unported compat decode parameter of Page.title() will be removed
* 3.0.20200703: tools.count, tools.Counter, tools.OrderedDict and ContextManagerWrapper will be removed
* 3.0.20200508: Page.getVersionHistory and Page.fullVersionHistory() methods will be removed (T136513, T151110)
* 3.0.20200306: Support of MediaWiki releases below 1.19 will be dropped (T245350)
