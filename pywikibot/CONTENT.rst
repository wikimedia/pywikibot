The contents of the package
---------------------------

    +-----------------------------------------------------------------------------------+
    |  Library routines                                                                 |
    +===========================+=======================================================+
    | __init__.py               | Initialization of the pywikibot framework,            |
    |                           | basic classes and methods                             |
    +---------------------------+-------------------------------------------------------+
    | _wbtypes.py               | Wikibase data type classes                            |
    +---------------------------+-------------------------------------------------------+
    | backports.py              | Module contains backports to support older Python     |
    |                           | versions                                              |
    +---------------------------+-------------------------------------------------------+
    | bot.py                    | User-interface related functions for building bots    |
    +---------------------------+-------------------------------------------------------+
    | bot_choice.py             | Classes for input_choice                              |
    +---------------------------+-------------------------------------------------------+
    | botirc.py                 | User-interface related functions for building irc bot |
    +---------------------------+-------------------------------------------------------+
    | config2.py                | Module to define and load pywikibot configuration     |
    +---------------------------+-------------------------------------------------------+
    | cosmetic_changes.py       | Slight modifications to a wiki page's source code     |
    +---------------------------+-------------------------------------------------------+
    | daemonize.py              | Daemonize the current process on Unix                 |
    +---------------------------+-------------------------------------------------------+
    | date.py                   | Date formats in various languages                     |
    +---------------------------+-------------------------------------------------------+
    | diff.py                   | Diff module                                           |
    +---------------------------+-------------------------------------------------------+
    | echo.py                   | Classes and functions for working with the Echo       |
    |                           | extension                                             |
    +---------------------------+-------------------------------------------------------+
    | editor.py                 | Text editor class for your favourite editor           |
    +---------------------------+-------------------------------------------------------+
    | epydoc.cfg                | The list of objects to document                       |
    +---------------------------+-------------------------------------------------------+
    | exceptions.py             | Exception classes used throughout the framework       |
    +---------------------------+-------------------------------------------------------+
    | family.py                 | Abstract superclass for wiki families. Subclassed by  |
    |                           | the classes in the 'families' subdirectory.           |
    +---------------------------+-------------------------------------------------------+
    | fixes.py                  | File containing all standard fixes, stores predefined |
    |                           | replacements used by replace.py.                      |
    +---------------------------+-------------------------------------------------------+
    | flow.py                   | Objects representing Flow entities                    |
    +---------------------------+-------------------------------------------------------+
    | i18n.py                   | Helper functions for both the internal translation    |
    |                           | system and for TranslateWiki-based translations       |
    +---------------------------+-------------------------------------------------------+
    | interwiki_graph.py        | Possible create graph with interwiki.py.              |
    +---------------------------+-------------------------------------------------------+
    | logentries.py             | Objects representing Mediawiki log entries            |
    +---------------------------+-------------------------------------------------------+
    | logging.py                | Logging and output functions                          |
    +---------------------------+-------------------------------------------------------+
    | login.py                  | Log in to an account on your "home" wiki. or check    |
    |                           | login status                                          |
    +---------------------------+-------------------------------------------------------+
    | page.py                   | Allows access to the site's bot user list.            |
    +---------------------------+-------------------------------------------------------+
    | pagegenerators.py         | Generator pages.                                      |
    +---------------------------+-------------------------------------------------------+
    | plural.py                 | Module containing plural rules of various languages   |
    +---------------------------+-------------------------------------------------------+
    | proofreadpage.py          | Objects representing objects used with ProofreadPage  |
    |                           | Extension                                             |
    +---------------------------+-------------------------------------------------------+
    | site.py                   | Objects representing MediaWiki sites (wikis)          |
    +---------------------------+-------------------------------------------------------+
    | site_detect.py            | Classes for detecting a MediaWiki site                |
    +---------------------------+-------------------------------------------------------+
    | specialbots.py            | Predefined special bot classes                        |
    +---------------------------+-------------------------------------------------------+
    | textlib.py                | Functions for manipulating wiki-text                  |
    +---------------------------+-------------------------------------------------------+
    | throttle.py               | Mechanics to slow down wiki read and/or write rate    |
    +---------------------------+-------------------------------------------------------+
    | titletranslate.py         | Rules and tricks to auto-translate wikipage titles    |
    |                           | articles.                                             |
    +---------------------------+-------------------------------------------------------+
    | version.py                | Module to determine the pywikibot version (tag,       |
    |                           | revision and date)                                    |
    +---------------------------+-------------------------------------------------------+
    | weblib.py                 | Functions for manipulating external links or querying |
    |                           | third-party sites                                     |
    +---------------------------+-------------------------------------------------------+
    | xmlreader.py              | Reading and parsing XML dump files.                   |
    +---------------------------+-------------------------------------------------------+


    +---------------------------+-------------------------------------------------------+
    |  comms                    | Communication layer.                                  |
    +===========================+=======================================================+
    | eventstreams.py           | stream client for server sent events                  |
    +---------------------------+-------------------------------------------------------+
    | http.py                   | Basic HTTP access interface                           |
    +---------------------------+-------------------------------------------------------+
    | threadedhttp.py           | Httplib2 threaded cookie layer extending httplib2     |
    +---------------------------+-------------------------------------------------------+


    +---------------------------+-------------------------------------------------------+
    | compat                    | Package to provide compatibility with compat scripts. |
    |                           | (should never be used)                                |
    +===========================+=======================================================+
    | catlib.py                 | Library routines written especially to handle         |
    |                           | category pages and recurse over category contents.    |
    +---------------------------+-------------------------------------------------------+
    | query.py                  | API query library                                     |
    +---------------------------+-------------------------------------------------------+
    | userlib.py                | Library to work with users, their pages and talk page |
    +---------------------------+-------------------------------------------------------+


    +---------------------------+-------------------------------------------------------+
    | data                      | Module providing several layers of data access to wiki|
    +===========================+=======================================================+
    | api.py                    | Interface to Mediawiki's api.php                      |
    +---------------------------+-------------------------------------------------------+
    | mysql.py                  | Miscellaneous helper functions for mysql queries      |
    +---------------------------+-------------------------------------------------------+
    | sparql.py                 | Objects representing SPARQL query API                 |
    +---------------------------+-------------------------------------------------------+
    | wikistats.py              | Objects representing WikiStats API                    |
    +---------------------------+-------------------------------------------------------+


    +---------------+-------------------------------------------------------------------+
    | tools         | Miscellaneous helper functions (not wiki-dependent).              |
    +===============+===================================================================+
    | __init__.py   | several classes and methods                                       |
    +---------------+-------------------------------------------------------------------+
    | _logging.py   | Logging tools                                                     |
    +---------------+-------------------------------------------------------------------+
    | chars.py      | Character based helper functions(not wiki-dependent)              |
    +---------------+-------------------------------------------------------------------+
    | djvu.py       | Wrapper around djvulibre to access djvu properties and content    |
    +---------------+-------------------------------------------------------------------+
    | formatter.py  | Various formatting related utilities                              |
    +---------------+-------------------------------------------------------------------+
    | ip.py         | IP address tools module                                           |
    +---------------+-------------------------------------------------------------------+


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
    | CONTENT.rst                | This file ( Short info on all modules )              |
    +----------------------------+------------------------------------------------------+
    | READMY.rst                 | Package description file                             |
    +----------------------------+------------------------------------------------------+

