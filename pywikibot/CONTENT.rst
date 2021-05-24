The contents of the package
---------------------------

    +-----------------------------------------------------------------------------------+
    |  Library routines                                                                 |
    +============================+======================================================+
    | __init__.py                | Initialization of the Pywikibot framework,           |
    |                            | basic classes and methods                            |
    +----------------------------+------------------------------------------------------+
    | __metadata__.py            | Pywikibot framework metadata file                    |
    +----------------------------+------------------------------------------------------+
    | _wbtypes.py                | Wikibase data type classes                           |
    +----------------------------+------------------------------------------------------+
    | backports.py               | Backports to support older Python versions           |
    +----------------------------+------------------------------------------------------+
    | bot.py                     | User-interface related functions for building bots   |
    +----------------------------+------------------------------------------------------+
    | bot_choice.py              | Classes for input_choice                             |
    +----------------------------+------------------------------------------------------+
    | config.py                  | Module to define and load Pywikibot configuration    |
    +----------------------------+------------------------------------------------------+
    | cosmetic_changes.py        | Slight modifications to a wiki page's source code    |
    +----------------------------+------------------------------------------------------+
    | daemonize.py               | Daemonize the current process on Unix                |
    +----------------------------+------------------------------------------------------+
    | date.py                    | Date formats in various languages                    |
    +----------------------------+------------------------------------------------------+
    | diff.py                    | Diff module                                          |
    +----------------------------+------------------------------------------------------+
    | echo.py                    | Classes and functions for working with the Echo      |
    |                            | extension                                            |
    +----------------------------+------------------------------------------------------+
    | editor.py                  | Text editor class for your favourite editor          |
    +----------------------------+------------------------------------------------------+
    | exceptions.py              | Exception classes used throughout the framework      |
    +----------------------------+------------------------------------------------------+
    | family.py                  | Abstract superclass for wiki families. Subclassed by |
    |                            | the classes in the 'families' subdirectory           |
    +----------------------------+------------------------------------------------------+
    | fixes.py                   | File containing all standard fixes, stores           |
    |                            | predefined replacements used by replace.py           |
    +----------------------------+------------------------------------------------------+
    | flow.py                    | Objects representing Flow entities                   |
    +----------------------------+------------------------------------------------------+
    | i18n.py                    | Helper functions for both the internal translation   |
    |                            | system and for TranslateWiki-based translations      |
    +----------------------------+------------------------------------------------------+
    | interwiki_graph.py         | Possible create graph with interwiki.py script       |
    +----------------------------+------------------------------------------------------+
    | logentries.py              | Objects representing MediaWiki log entries           |
    +----------------------------+------------------------------------------------------+
    | logging.py                 | Logging and output functions                         |
    +----------------------------+------------------------------------------------------+
    | login.py                   | Log in to an account on your "home" wiki, or check   |
    |                            | login status                                         |
    +----------------------------+------------------------------------------------------+
    | pagegenerators.py          | Generator pages                                      |
    +----------------------------+------------------------------------------------------+
    | plural.py                  | Module containing plural rules of various languages  |
    +----------------------------+------------------------------------------------------+
    | proofreadpage.py           | Objects representing objects used with ProofreadPage |
    |                            | Extension                                            |
    +----------------------------+------------------------------------------------------+
    | site_detect.py             | Classes for detecting a MediaWiki site               |
    +----------------------------+------------------------------------------------------+
    | textlib.py                 | Functions for manipulating wiki-text                 |
    +----------------------------+------------------------------------------------------+
    | throttle.py                | Mechanics to slow down wiki read and/or write rate   |
    +----------------------------+------------------------------------------------------+
    | titletranslate.py          | Rules and tricks to auto-translate wikipage titles   |
    |                            | articles                                             |
    +----------------------------+------------------------------------------------------+
    | version.py                 | Module to determine the Pywikibot version (tag,      |
    |                            | revision and date)                                   |
    +----------------------------+------------------------------------------------------+
    | xmlreader.py               | Reading and parsing XML dump files                   |
    +----------------------------+------------------------------------------------------+


    +----------------------------+------------------------------------------------------+
    |  comms                     | Communication layer                                  |
    +============================+======================================================+
    | eventstreams.py            | stream client for server sent events                 |
    +----------------------------+------------------------------------------------------+
    | http.py                    | Basic HTTP access interface                          |
    +----------------------------+------------------------------------------------------+


    +----------------------------+------------------------------------------------------+
    | data                       | Module providing layers of data access to wiki       |
    +============================+======================================================+
    | api.py                     | Interface to MediaWiki's api.php                     |
    +----------------------------+------------------------------------------------------+
    | mysql.py                   | Miscellaneous helper functions for mysql queries     |
    +----------------------------+------------------------------------------------------+
    | sparql.py                  | Objects representing SPARQL query API                |
    +----------------------------+------------------------------------------------------+
    | wikistats.py               | Objects representing WikiStats API                   |
    +----------------------------+------------------------------------------------------+


    +----------------------------+------------------------------------------------------+
    | page                       | Module with classes for MediaWiki page content       |
    +============================+======================================================+
    | __init__.py                | Objects representing MediaWiki pages                 |
    +----------------------------+------------------------------------------------------+
    | _collections.py            | Structures holding data for Wikibase entities        |
    +----------------------------+------------------------------------------------------+
    | _decorators.py             | Decorators used by page objects                      |
    +----------------------------+------------------------------------------------------+
    | _revision.py               | Object representing page revision                    |
    +----------------------------+------------------------------------------------------+


    +----------------------------+------------------------------------------------------+
    | site                       | Module with classes for MediaWiki sites              |
    +============================+======================================================+
    | __init__.py                | Objects representing MediaWiki sites (wikis)         |
    +----------------------------+------------------------------------------------------+
    | _apisite.py                | Objects representing API interface to MediaWiki site |
    +----------------------------+------------------------------------------------------+
    | _basesite.py               | Objects representing site methods independent of the |
    |                            | communication interface                              |
    +----------------------------+------------------------------------------------------+
    | _datasite.py               | Objects representing API interface to Wikibase       |
    +----------------------------+------------------------------------------------------+
    | _decorators.py             | Decorators used by site models                       |
    +----------------------------+------------------------------------------------------+
    | _extensions.py             | API interfaces to MediaWiki extensions               |
    +----------------------------+------------------------------------------------------+
    | _generators.py             | API generators mixin to MediaWiki site               |
    +----------------------------+------------------------------------------------------+
    | _interwikimap.py           | Objects representing interwiki map of MediaWiki site |
    +----------------------------+------------------------------------------------------+
    | _namespace.py              | Objects representing Namespaces of MediaWiki site    |
    +----------------------------+------------------------------------------------------+
    | _obsoletesites.py          | Objects representing obsolete MediaWiki sites        |
    +----------------------------+------------------------------------------------------+
    | _siteinfo.py               | Objects representing site info data contents         |
    +----------------------------+------------------------------------------------------+
    | _tokenwallet.py            | Objects representing api tokens                      |
    +----------------------------+------------------------------------------------------+


    +----------------------------+------------------------------------------------------+
    | specialbots                | Module containing special bots reusable by scripts   |
    +============================+======================================================+
    | __init__.py                | Predefined special bot classes                       |
    +----------------------------+------------------------------------------------------+
    | _unlink.py                 | Predefined BaseUnlinkBot special bot class           |
    +----------------------------+------------------------------------------------------+
    | _upload.py                 | Predefined UploadRobot special bot class             |
    +----------------------------+------------------------------------------------------+


    +----------------------------+------------------------------------------------------+
    | tools                      | Miscellaneous helper functions (not wiki-dependent)  |
    +============================+======================================================+
    | __init__.py                | several classes and methods                          |
    +----------------------------+------------------------------------------------------+
    | _logging.py                | Logging tools                                        |
    +----------------------------+------------------------------------------------------+
    | chars.py                   | Character based helper functions(not wiki-dependent) |
    +----------------------------+------------------------------------------------------+
    | djvu.py                    | Wrapper around djvulibre to access djvu properties   |
    |                            | and content                                          |
    +----------------------------+------------------------------------------------------+
    | formatter.py               | Various formatting related utilities                 |
    +----------------------------+------------------------------------------------------+


    +-----------------------------------------------------------------------------------+
    | User Interface                                                                    |
    +============================+======================================================+
    | _interface_base.py         | Abstract base user interface module                  |
    +----------------------------+------------------------------------------------------+
    | gui.py                     | GUI with a Unicode textfield where the user can edit |
    +----------------------------+------------------------------------------------------+
    | terminal_interface.py      | Platform independent terminal interface module       |
    +----------------------------+------------------------------------------------------+
    | terminal_interface_base.py | Base for terminal user interfaces                    |
    +----------------------------+------------------------------------------------------+
    | terminal_interface_unix.py | User interface for Unix terminals                    |
    +----------------------------+------------------------------------------------------+
    | terminal_interface_win32.py| User interface for Win32 terminals                   |
    +----------------------------+------------------------------------------------------+
    | transliteration.py         | Module to transliterate text                         |
    +----------------------------+------------------------------------------------------+
    | win32_unicode.py           | Stdout, stderr and argv support for Unicode          |
    +----------------------------+------------------------------------------------------+


    +-----------------------------------------------------------------------------------+
    | Others                                                                            |
    +============================+======================================================+
    | families (folder)          | Contains wiki-specific information like URLs,        |
    |                            | languages, encodings etc                             |
    +----------------------------+------------------------------------------------------+
    | CONTENT.rst                | This file ( Short info on all modules )              |
    +----------------------------+------------------------------------------------------+
    | README.rst                 | Package description file                             |
    +----------------------------+------------------------------------------------------+

