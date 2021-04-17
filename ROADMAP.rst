Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

Improvements and Bugfixes
^^^^^^^^^^^^^^^^^^^^^^^^^

* proofreadpage: search for "new" class after purge (T280357)
* Enable different types with BaseBot.treat()
* Context manager depends on pymysql version, not Python release (T279753)
* Bugfix for Site.interwiki_prefix() (T188179)
* Exclude expressions from parsed template in mwparserfromhell (T71384)
* Provide an object representation for DequeGenerator
* Allow deleting any subclass of BasePage by title (T278659)
* Add support for API:Revisiondelete with Site.deleterevs() method (T276726)
* L10N updates
* Family files can be collected from a zip folder (T278076)

Dependencies
^^^^^^^^^^^^

* **mwparserfromhell** or **wikitextparser** are strictly recommended (T106763)
* Require **Pillow**>=8.1.1 due to vulnerability found (T278743)
* TkDialog of GUI userinterface requires **Python 3.6+** (T278743)
* Enable textlib.extract_templates_and_params with **wikitextparser** package
* Add support for **PyMySQL** 1.0.0+

Code cleanups
^^^^^^^^^^^^^

* APISite.resolvemagicwords(), BaseSite.ns_index() and  remove BaseSite.getNamespaceIndex() were removed
* Deprecated MoveEntry.new_ns() and new_title() methods were removed
* Unused NoSuchSite and PageNotSaved exception were removed
* Unused BadTitle exception was removed (T267768)
* getSite() function was removed in favour of Site() constructor
* Page.fileUrl() was removed in favour of Page.get_file_url()
* Deprecated getuserinfo and getglobaluserinfo Site methods were removed
* compat2core.py script was archived

Deprecations
~~~~~~~~~~~~

* 6.1.0: tools.frozenmap will be removed in favour of types.MappingProxyType
* 6.1.0: tools.DotReadableDict will be removed
* 6.1.0: mwparserfromhell or wikitextparser MediaWiki markup parser becomes mandatory (T106763)
* 6.1.0: textlib.unescape() function will be removed in favour of html.unescape()
* 6.0.1: Site.undeletepage() and Site.undelete_file_versions() will be removed in favour of Site.undelete() method
* 6.0.1: Site.deletepage() and Site.deleteoldimage() will be removed in favour of Site.delete() method
* 6.0.1: DataSite.createNewItemFromPage() method will be removed in favour of ImagePage.fromPage() (T98663)
* 6.0.0: User.name() method will be removed in favour of User.username property
* 5.6.0: pagenenerators.handleArg() method will be removed in favour of handle_arg() (T271437)
* 5.6.0: Family.ignore_certificate_error() method will be removed in favour of verify_SSL_certificate() (T265205)
* 5.0.0: OptionHandler.options dict will be removed in favour of OptionHandler.opt
* 5.0.0: Methods deprecated for 5 years or longer will be removed
* 5.0.0: pagegenerators.ReferringPageGenerator is desupported and will be removed
