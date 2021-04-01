Current release changes
~~~~~~~~~~~~~~~~~~~~~~~

* Require **Pillow**>=8.1.1 due to vulnerability found (T278743)
* TkDialog of GUI userinterface requires **Python 3.6+** (T278743)
* Enable textlib.extract_templates_and_params with **wikitextparser** package
* Add support for **PyMySQL** 1.0.0+
* Exclude expressions from parsed template in **mwparserfromhell** (T71384)
* Provide an object representation for DequeGenerator
* Allow deleting any subclass of BasePage by title (T278659)
* Add support for API:Revisiondelete with Site.deleterevs() method (T276726)
* L10N updates
* Family files can be collected from a zip folder (T278076)
* Deprecated getuserinfo and getglobaluserinfo Site methods were removed
* compat2core.py script was archived

Future release notes
~~~~~~~~~~~~~~~~~~~~

* 6.0.1: Site.undeletepage() and Site.undelete_file_versions() will be removed in favour of Site.undelete() method
* 6.0.1: Site.deletepage() and Site.deleteoldimage() will be removed in favour of Site.delete() method
* 6.0.1: DataSite.createNewItemFromPage() method will be removed in favour of ImagePage.fromPage() (T98663)
* 6.0.0: User.name() method will be removed in favour of User.username property
* 5.6.0: pagenenerators.handleArg() method will be removed in favour of handle_arg() (T271437)
* 5.6.0: Family.ignore_certificate_error() method will be removed in favour of verify_SSL_certificate() (T265205)
* 5.0.0: OptionHandler.options dict will be removed in favour of OptionHandler.opt
* 5.0.0: Methods deprecated for 5 years or longer will be removed
* 5.0.0: pagegenerators.ReferringPageGenerator is desupported and will be removed
