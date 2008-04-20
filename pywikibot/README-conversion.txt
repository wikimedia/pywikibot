This is a guide to converting bot scripts from version 1 of the
Pywikipediabot framework to version 2.

Most importantly, note that the version 2 framework *only* supports wikis
using MediaWiki v.1.12 or higher software.  If you need to access a wiki that
uses older software, you should continue using version 1 for this purpose.

The "root" namespace used in the project has changed from "wikipedia"
to "pywikibot". References to wikipedia need to be changed globally to
pywikibot.  Unless noted in this document, other names have not changed; for
example, wikipedia.Page can be replaced by pywikibot.Page throughout any
bot.

With pywikipedia scripts were importing "wikipedia" or "pagegenerators"
librairies; pywikibot is now written as a standard module. 
(To use it, just import "pywikibot", assuming that pywikibot/ is in sys.path)

== Python librairies ==

You will need, to run pywikibot, httplib2 and setuptools
* httplib2 : http://code.google.com/p/httplib2/
* setuptools : http://pypi.python.org/pypi/setuptools/

If you run into errors involving httplib2.urlnorm, update httplib2 to
0.4.0 (Ubuntu package python-httlib2 for example, is outdated)

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

A third syntax allows easy conversion from a Page object to an ImagePage or
Category, or vice versa: e.g., Category(pageobj) converts a Page to a
Category, as long as the page is in the category namespace.

The following methods of the Page object have been deprecated (deprecated
methods will still work, but print a warning message in debug mode):

- urlname(): replaced by Page.title(asUrl=True)
- titleWithoutNamespace(): replaced by Page.title(withNamespace=False)
- sectionFreeTitle(): replaced by Page.title(withSection=False)
- aslink(): replaced by Page.title(asLink=True)
- encoding(): replaced by Page.site().encoding()

The following methods of the Page object have been obsoleted and no longer
work (but these methods don't appear to be used anywhere in the code
distributed with the bot framework). The functionality of the two obsolete
methods is easily replaced by using standard search-and-replace techniques.
If you call them, they will print a warning and do nothing else:

- removeImage()
- replaceImage()

=== ImagePage objects ===

For ImagePage objects, the getFileMd5Sum() method is deprecated; it is
recommended to replace it with getFileSHA1Sum(), because MediaWiki now
stores the SHA1 hash of images.

=== Category objects ===

The Category object has been moved from the catlib module to the pywikibot
namespace.  Any references to "catlib.Category" need to be replaced by
"pywikibot.Category".

For Category objects, the following methods are deprecated:

- subcategoriesList: use, for example, list(self.subcategories()) instead
- articlesList: use, for example, list(self.articles()) instead
- supercategories: use self.categories() instead
- supercategoriesList: use, for example, list(self.categories()) instead

# MORE TO COME #
