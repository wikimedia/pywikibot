This is a guide to converting bot scripts from version 1 of the
Pywikibot framework to version 2.

Most importantly, note that the version 2 framework *only* supports wikis
using MediaWiki v.1.14 or higher software.  If you need to access a wiki that
uses older software, you should continue using version 1 for this purpose.

The root namespace used in the project has changed from "wikipedia"
to "pywikibot". References to wikipedia need to be changed globally to
pywikibot.  Unless noted in this document, other names have not changed; for
example, wikipedia.Page can be replaced by pywikibot.Page throughout any
bot.  An effort has been made to design the interface to be as backwards-
compatible as possible, so that in most cases it should be possible to convert
scripts to the new interface simply by changing import statements and doing
global search-and-replace on module names, as discussed in this document.

With pywikibot compat branch scripts were importing "wikipedia" or 
"pagegenerators" libraries; pywikibot is now written as a standard package,
and other modules are contained within it (e.g., pywikibot.site contains Site
classes). However, most commonly-used names are imported into the pywikibot
namespace, so that module names don't need to be used unless specified in the
documentation.

Make sure that the directory that contains the "pywikibot" subdirectory (or
folder) is in sys.path.

The following changes, at a minimum, need to be made to allow scripts to run:

    change "import wikipedia" to "import pywikibot"
    change "import pagegenerators" to "from pywikibot import pagegenerators"
    change "import config" to "from pywikibot import config"
    change "import catlib" to "from pywikibot.compat import catlib"
    change "import query" to "from pywikibot.compat import query"
    change "import userlib" to "from pywikibot.compat import userlib"
    change "wikipedia." to "pywikibot."

wikipedia.setAction() no longer works; you must revise the script to pass an
explicit edit summary message on each put() or put_async() call.

There is a helper script which does a lot of changes automatically.
Just call it:
pwb.py maintenance/compat2core [<script to convert>]
and follow the instructions and hints.

== Python libraries ==

[Note: the goal will be to package pywikibot with setuptools easy_install,
so that these dependencies will be loaded automatically when the package is
installed, and users won't need to worry about this...]

To run pywikibot, you will need the requests package:

It may be installed using pip or easy_install.

== Page objects ==

The constructor syntax for Pages has been modified; existing calls in the
format of Page(site, title) will still work, and this is still the preferred
way of creating a Page object from data retrieved from the MediaWiki API
(because the API will have parsed and normalized the title).  However, for
titles input by a user or scraped from wikitext, it is preferred to use the
alternative syntax Page(Link(site, wikitext)), where "wikitext" is the
string found between [[ and ]] delimiters.  The new Link object (more on
this below) handles link parsing and interpretation that doesn't require
access to the wiki server.

A third syntax allows easy conversion from a Page object to a FilePage or
Category, or vice versa: e.g., Category(pageobj) converts a Page to a
Category, as long as the page is in the category namespace.

The following methods of the Page object have been deprecated (deprecated
methods still work, but print a warning message in debug mode):

- urlname(): replaced by Page.title(asUrl=True)
- titleWithoutNamespace(): replaced by Page.title(withNamespace=False)
- sectionFreeTitle(): replaced by Page.title(withSection=False)
- aslink(): replaced by Page.title(asLink=True)
- encoding(): replaced by Page.site.encoding()

The following methods of the Page object have been obsoleted and no longer
work (but these methods don't appear to be used anywhere in the code
distributed with the bot framework). The functionality of the two obsolete
methods is easily replaced by using standard search-and-replace techniques.
If you call them, they will print a warning and do nothing else:

- removeImage()
- replaceImage()

The following methods have had their outputs changed:

- getVersionHistory(): Returns a pywikibot.Timestamp object instead of a MediaWiki one

=== FilePage objects ===

The old ImagePage class has been renamed into FilePage.
For FilePage objects, the getFileMd5Sum() method is deprecated; it is
recommended to replace it with getFileSHA1Sum(), because MediaWiki now
stores the SHA1 hash of images.

=== Category objects ===

The Category object has been moved from the catlib module to the pywikibot
namespace.  Any references to "catlib.Category" can be replaced by
"pywikibot.Category", but the old form is retained for backwards-compatibility.

For Category objects, the following methods are deprecated:

- subcategoriesList: use, for example, list(self.subcategories()) instead
- articlesList: use, for example, list(self.articles()) instead
- supercategories: use self.categories() instead
- supercategoriesList: use, for example, list(self.categories()) instead

=== User objects ===

The User object has been moved from the userlib module to the pywikibot
namespace. Any references to "userlib.User" can be replaced by
"pywikibot.User", but the old form is retained for backwards-compatibility.

The following changes have occurred in the User object:

- contributions(): returns a pywikibot.Timestamp object instead of a Mediawiki one

=== Command-line arguments ===

Scripts that supported unnamed arguments as titles of pages on which to work,
now require that those titles be written as standard pagegenerators, e.g.:

    python script.py -page:"A title"

while unlink.py and other scripts that required page titles as main arguments
now need only that the titles be wrapped in quotes, as:

    python unlink.py "A title"

# MORE TO COME #
