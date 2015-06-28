=========================================================================
**This is a package to build robots for MediaWiki wikis like Wikipedia.**
=========================================================================


Please do not play with this package.
-------------------------------------
These programs can actually modify the live wiki on the net, and proper
wiki-etiquette should be followed before running it on any wiki.

To get started on proper usage of the bot framework, please refer to:

    `Manual:Pywikibot <http://www.mediawiki.org/wiki/Manual:Pywikibot>`_

The contents of the package
---------------------------

    +----------------------------------------------------------------------------------+
    |  Library routines                                                                |
    +===========================+======================================================+
    | __init__.py               | Initialization of the pywikibot framework,           |
    |                           | basic classes and methods                            |
    +---------------------------+------------------------------------------------------+
    | _wbtypes.py               | Wikibase data type classes                           |
    +---------------------------+------------------------------------------------------+
    | backports.py              | Module contains backports to support older Python    |
    |                           | versions                                             |
    +---------------------------+------------------------------------------------------+
    | bot.py                    | User-interface related functions for building bots   |
    +---------------------------+------------------------------------------------------+
    | bot_choice.py             | Classes for input_choice                             |
    +---------------------------+------------------------------------------------------+
    | botirc.py                 | User-interface related functions for building irc bot|
    +---------------------------+------------------------------------------------------+
    | config2.py                | Module to define and load pywikibot configuration    |
    +---------------------------+------------------------------------------------------+
    | cosmetic_changes.py       | Slight modifications to a wiki page's source code    |
    +---------------------------+------------------------------------------------------+
    | daemonize.py              | Daemonize the current process on Unix                |
    +---------------------------+------------------------------------------------------+
    | date.py                   | Date formats in various languages                    |
    +---------------------------+------------------------------------------------------+
    | diff.py                   | Diff module                                          |
    +---------------------------+------------------------------------------------------+
    | echo.py                   | Classes and functions for working with the Echo      |
    |                           | extension                                            |
    +---------------------------+------------------------------------------------------+
    | editor.py                 | Text editor class for your favourite editor          |
    +---------------------------+------------------------------------------------------+
    | epydoc.cfg                | The list of objects to document                      |
    +---------------------------+------------------------------------------------------+
    | exceptions.py             | Exception classes used throughout the framework      |
    +---------------------------+------------------------------------------------------+
    | family.py                 | Abstract superclass for wiki families. Subclassed by |
    |                           | the classes in the 'families' subdirectory.          |
    +---------------------------+------------------------------------------------------+
    | fixes.py                  | File containing all standard fixes, stores predefined|
    |                           | replacements used by replace.py.                     |
    +---------------------------+------------------------------------------------------+
    | flow.py                   | Objects representing Flow entities                   |
    +---------------------------+------------------------------------------------------+
    | i18n.py                   | Helper functions for both the internal translation   |
    |                           | system and for TranslateWiki-based translations      |
    +---------------------------+------------------------------------------------------+
    | interwiki_graph.py        | Possible create graph with interwiki.py.             |
    +---------------------------+------------------------------------------------------+
    | logentries.py             | Objects representing Mediawiki log entries           |
    +---------------------------+------------------------------------------------------+
    | login.py                  | Log in to an account on your "home" wiki. or check   |
    |                           | login status                                         |
    +---------------------------+------------------------------------------------------+
    | page.py                   | Allows access to the site's bot user list.           |
    +---------------------------+------------------------------------------------------+
    | pagegenerators.py         | Generator pages.                                     |
    +---------------------------+------------------------------------------------------+
    | plural.py                 | Module containing plural rules of various languages  |
    +---------------------------+------------------------------------------------------+
    | proofreadpage.py          | Objects representing objects used with ProofreadPage |
    |                           | Extension                                            |
    +---------------------------+------------------------------------------------------+
    | site.py                   | Objects representing MediaWiki sites (wikis)         |
    +---------------------------+------------------------------------------------------+
    | site_detect.py            | Classes for detecting a MediaWiki site               |
    +---------------------------+------------------------------------------------------+
    | textlib.py                | Functions for manipulating wiki-text                 |
    +---------------------------+------------------------------------------------------+
    | throttle.py               | Mechanics to slow down wiki read and/or write rate   |
    +---------------------------+------------------------------------------------------+
    | titletranslate.py         | Rules and tricks to auto-translate wikipage titles   |
    |                           | articles.                                            |
    +---------------------------+------------------------------------------------------+
    | version.py                | Module to determine the pywikibot version (tag,      |
    |                           | revision and date)                                   |
    +---------------------------+------------------------------------------------------+
    | weblib.py                 | Functions for manipulating external links or querying|
    |                           | third-party sites                                    |
    +---------------------------+------------------------------------------------------+
    | xmlreader.py              | Reading and parsing XML dump files.                  |
    +---------------------------+------------------------------------------------------+


    +---------------------------+------------------------------------------------------+
    |  comms                    | Communication layer.                                 |
    +===========================+======================================================+
    | http.py                   | Basic HTTP access interface                          |
    +---------------------------+------------------------------------------------------+
    | rcstream.py               | SocketIO-based rcstream client                       |
    +---------------------------+------------------------------------------------------+
    | threadedhttp.py           | Httplib2 threaded cookie layer extending httplib2    |
    +---------------------------+------------------------------------------------------+


    +---------------------------+------------------------------------------------------+
    | compat                    | Package to provide compatibility with compat scripts.|
    |                           | (should never be used)                               |
    +===========================+======================================================+
    | catlib.py                 | Library routines written especially to handle        |
    |                           | category pages and recurse over category contents.   |
    +---------------------------+------------------------------------------------------+
    | query.py                  | API query library                                    |
    +---------------------------+------------------------------------------------------+
    | userlib.py                | Library to work with users, their pages and talk page|
    +---------------------------+------------------------------------------------------+


    +---------------------------+-------------------------------------------------------+
    | data                      | Module providing several layers of data access to wiki|
    +===========================+=======================================================+
    | api.py                    | Interface to Mediawiki's api.php                      |
    +---------------------------+-------------------------------------------------------+
    | wikidataquery.py          | Objects representing WikidataQuery query syntax       |
    |                           | and API                                               |
    +---------------------------+-------------------------------------------------------+
    | wikistats.py              | Objects representing WikiStats API                    |
    +---------------------------+-------------------------------------------------------+


    +---------------+------------------------------------------------------------------+
    | tools         | Miscellaneous helper functions (not wiki-dependent).             |
    +===============+==================================================================+
    | __init__.py   | several classes and methods                                      |
    +---------------+------------------------------------------------------------------+
    | _logging.py   | Logging tools                                                    |
    +---------------+------------------------------------------------------------------+
    | chars.py      | Character based helper functions(not wiki-dependent)             |
    +---------------+------------------------------------------------------------------+
    | djvu.py       | Wrapper around djvulibre to access djvu properties and content   |
    +---------------+------------------------------------------------------------------+
    | formatter.py  | Various formatting related utilities                             |
    +---------------+------------------------------------------------------------------+
    | ip.py         | IP address tools module                                          |
    +---------------+------------------------------------------------------------------+


    +-----------------------------------------------------------------------------------+
    | User Interface                                                                    |
    +============================+======================================================+
    | cgi_interface.py           | CGI user interface                                   |
    +----------------------------+------------------------------------------------------+
    | gui.py                     | GUI with a unicode textfield where the user can edit |
    +----------------------------+------------------------------------------------------+
    | terminal_interface.py      | Platform independent terminal interface module       |
    +----------------------------+------------------------------------------------------+
    | terminal_interface_base.py | Base for terminal user interfaces                    |
    +----------------------------+------------------------------------------------------+
    | terminal_interface_unix.py | User interface for unix terminals                    |
    +----------------------------+------------------------------------------------------+
    | terminal_interface_win32.py| User interface for Win32 terminals                   |
    +----------------------------+------------------------------------------------------+
    | transliteration.py         | Module to transliterate text                         |
    +----------------------------+------------------------------------------------------+
    | win32_unicode.py           | Stdout, stderr and argv support for unicode          |
    +----------------------------+------------------------------------------------------+


    +-----------------------------------------------------------------------------------+
    | Others                                                                            |
    +============================+======================================================+
    | families (folder)          | Contains wiki-specific information like URLs,        |
    |                            | languages, encodings etc.                            |
    +----------------------------+------------------------------------------------------+
    | README.rst                 | This file ( Short info on all modules )              |
    +----------------------------+------------------------------------------------------+

**External software can be used with Pywikibot:**
  * Pydot, Pyparsing and Graphviz for use with interwiki_graph.py
  * JSON for use with site.py, bot.py
  * MySQLdb to access MySQL database for use with pagegenerators.py
  * PyGoogle to access Google Web API and PySearch to access Yahoo! Search
    Web Services for use with pagegenerators.py


Pywikibot makes use of some modules that are part of python, but that
are not installed by default on some Linux distributions:

  * python-xml (required to parse XML via SaX2)
  * python-celementtree (recommended if you use XML dumps)
  * python-tkinter (optional, used by some experimental GUI stuff)


You need to have at least python version `2.6.5 <http://www.python.org/download/>`_
or newer installed on your computer to be able to run any of the code in this
package, but not 3.0-3.2. It works fine with 3.3-3.4 versions of python installed.
Support for older versions of python is not planned. Some scripts could run with
older python releases. Please refer the manual at mediawiki for further details
and restrictions.


You do not need to "install" this package to be able to make use of
it. You can actually just run it from the directory where you unpacked
it or where you have your copy of the SVN or git sources.


The first time you run a script, the package creates a file named user-config.py
in your current directory. It asks for the family and language code you are
working on and at least for the bot's user name; this will be used to identify
you when the robot is making changes, in case you are not logged in. You may
choose to create a small or extended version of the config file with further
informations. Other variables that can be set in the configuration file, please
check config.py for ideas.


After that, you are advised to create a username + password for the bot, and
run login.py. Anonymous editing is not possible.
