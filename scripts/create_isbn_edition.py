#!/usr/bin/env python3
r"""Pywikibot client to load ISBN linked data into Wikidata.

Pywikibot script to get ISBN data from a digital library, and create or
amend the related Wikidata item for edition (with the
:samp:`P212, {ISBN number}` as unique external ID).

Use digital libraries to get ISBN data in JSON format, and integrate the
results into Wikidata.

.. note::
   ISBN data should only be used for editions, and not for written works.

Then the resulting item number can be used e.g. to generate Wikipedia
references using template ``Cite_Q``.

**Parameters:**
    All parameters are optional:

    .. code:: text

        *P1:*        digital library (default wiki "-")

            bnf      Catalogue General (France)
            bol      Bol.com
            dnb      Deutsche National Library
            goob     Google Books
            kb       National Library of the Netherlands
            loc      Library of Congress US
            mcues    Ministerio de Cultura (Spain)
            openl    OpenLibrary.org
            porbase  urn.porbase.org Portugal
            sbn      Servizio Bibliotecario Nazionale (Italy)
            wiki     wikipedia.org
            worldcat WorldCat (wc)

        *P2:*        ISO 639-1 language code. Default LANG; e.g. en, nl,
                     fr, de, es, it, etc.

        *P3 P4...:*  P/Q pairs to add additional claims (repeated) e.g.
                     P921 Q107643461 (main subject: database management
                     linked to P2163, Fast ID 888037)

        *stdin:*     List of ISBN numbers (International standard book
                     number, version 10 or 13). Free text (e.g.
                     Wikipedia references list, or publication list) is
                     accepted. Identification is done via an ISBN regex
                     expression.

**Functionality:**
    * Both ISBN-10 and ISBN-13 numbers are accepted as input.
    * Only ISBN-13 numbers are stored. ISBN-10 numbers are only used for
      identification purposes; they are not stored.
    * The ISBN number is used as a primary key; no two items can have
      the same P212 ISBN number. The item update is not performed when
      there is no unique match. Only editions are updated or created.
    * Individual statements are added or merged incrementally; existing
      data is not overwritten.
    * Authors and publishers are searched to get their item number;
      unknown of ambiguous items are skipped.
    * Book title and subtitle are separated with either '.', ':', or '-'
      in that order.
    * Detect author, illustrator, writer preface, afterwork instances.
    * Add profession "author" to individual authors.
    * This script can be run incrementally.

**Examples:**
    Default library (Google Books), language (LANG), no additional
    statements:

        pwb create_isbn_edition.py 9789042925564

    Wikimedia, language English, main subject: database management:

        pwb create_isbn_edition.py wiki en P921 Q107643461 978-0-596-10089-6

**Data quality:**
    * ISBN numbers (P212) are only assigned to editions.
    * A written work should not have an ISBN number (P212).
    * For targets of P629 *(edition of)* amend "is an Q47461344
      *(written work)* instance" and "inverse P747 *(work has edition)*"
      statements
    * Use https://query.wikidata.org/querybuilder/ to identify P212
      duplicates. Merge duplicate items before running the script again.
    * The following properties should only be used for written works,
      not for editions:

      * P5331: OCLC work ID (editions should only have P243)
      * P8383: Goodreads-identificatiecode for work (editions should
        only have P2969)

**Return status:**
    The following status codes are returned to the shell::

        3   Invalid or missing parameter
        4   Library not installed
        12  Item does not exist
        20  Network error

**Standard ISBN properties for editions:**
    ::

        P31:Q3331189:  instance of edition (mandatory statement)
        P50:           author
        P123:          publisher
        P212:          canonical ISBN number (with dashes; searchable
                       via Wikidata Query)
        P407:          language of work (Qnumber linked to ISO 639-1
                       language code)
        P577:          date of publication (year)
        P1476:         book title
        P1680:         subtitle

**Other ISBN properties:**
    ::

        P921:   main subject (inverse lookup from external Fast ID P2163)
        P629:   work for edition
        P747:   edition of work

**Qualifiers:**
    ::

        P248:   Source
        P813:   Retrieval date
        P1545:  (author) sequence number

**External identifiers:**
    ::

        P243:   OCLC ID
        P1036:  Dewey Decimal Classification
        P2163:  Fast ID (inverse lookup via Wikidata Query)
                -> P921: main subject

        (not implemented)
        P2969:  Goodreads-identificatiecode

        (only for written works)
        P5331:  OCLC work ID (editions should only have P243)

        (not implemented)
        P8383:  Goodreads-identificatiecode for work
                (editions should only have P2969)
        P213:   ISNI ID
        P496:   ORCID ID
        P675:   Google Books-identificatiecode

**Unavailable properties from digital library:**
    ::

        (not implemented by isbnlib)
        P98:    Editor
        P110:   Illustrator/photographer
        P291:   place of publication
        P1104:  number of pages
        ?:      edition format (hardcover, paperback)

**Author:**
   Geert Van Pamel (User:Geertivp), MIT License, 2022-08-04,

**Prerequisites:**
    In addition to Pywikibot the following ISBN lib package is mandatory;
    install it with:

    .. code:: shell

       pip install isbnlib

    The following ISBN lib package are optional; install them with:

    .. code:: shell

        pip install isbnlib-bnf
        pip install isbnlib-bol
        pip install isbnlib-dnb
        pip install isbnlib-kb
        pip install isbnlib-loc
        pip install isbnlib-worldcat2

**Restrictions:**
    * Better use the ISO 639-1 language code parameter as a default. The
      language code is not always available from the digital library;
      therefore we need a default.
    * Publisher unknown:
      * Missing P31:Q2085381 statement, missing subclass in script
      * Missing alias
      * Create publisher
    * Unknown author: create author as a person

**Known Problems:**
    * Unknown ISBN, e.g. 9789400012820
    * If there is no ISBN data available for an edition either returns
      no output (goob = Google Books), or an error message (wiki, openl).
      The script is taking care of both. Try another library instance.
    * Only 6 specific ISBN attributes are listed by the webservice(s),
      missing are e.g.: place of publication, number of pages
    * Some digital libraries have more registrations than others.
    * Some digital libraries have data quality problems.
    * Not all ISBN attributes have data values (authors, publisher,
      date of publication), language can be missing at the digital
      library.
    * How to add still more digital libraries?

      * This would require an additional isbnlib module
      * Does the KBR has a public ISBN service (Koninklijke Bibliotheek
        van België)?
    * The script uses multiple webservice calls; script might take time,
      but it is automated.
    * Need to manually amend ISBN items that have no author, publisher,
      or other required data
      * You could use another digital library
      * Which other services to use?
    * BibTex service is currently unavailable
    * Filter for work properties: https://www.wikidata.org/wiki/Q63413107

      ::

        ['9781282557246', '9786612557248', '9781847196057', '9781847196040']
        P5331: OCLC identification code for work 793965595; should only
               have P243)
        P8383: Goodreads identification code for work 13957943; should
               only have P2969)
    * ERROR: an HTTP error has occurred e.g. (503) Service Unavailable
    * error: externally-managed-environment

      ``isbnlib-kb`` cannot be installed via :code:`pip install` command.
      It raises ``error: externally-managed-environment`` because this
      environment is externally managed.

      To install Python packages system-wide, try :samp:`apt install
      python3-{xyz}`, where *xyz* is the package you are trying to
      install.

      If you wish to install a non-Debian-packaged Python package,
      create a virtual environment using
      :code:`python3 -m venv path/to/venv`. Then use
      :code:`path/to/venv/bin/python` and :code:`path/to/venv/bin/pip`.
      Make sure you have ``python3-full`` installed.

      If you wish to install a non-Debian packaged Python application,
      it may be easiest to use :samp:`pipx install {xyz}`, which will
      manage a virtual environment for you. Make sure you have ``pipx``
      installed.

      .. seealso:: See :pylib:`venv` for more information about virtual
         environments.
      .. note:: If you believe this is a mistake, please contact your
         Python installation or OS distribution provider. You can
         override this, at the risk of breaking your Python installation
         or OS, by passing ``--break-system-packages`` to ``pip``.
      .. hint:: See :pep:`668` for the detailed specification.

      You need to install a local python environment:

      - https://pip.pypa.io/warnings/venv
      - :python:`tutorial/venv`

      .. code-block:: bash

         sudo -s
         apt install python3-full
         python3 -m venv /opt/python
         /opt/python/bin/pip install pywikibot
         /opt/python/bin/pip install isbnlib-kb
         /opt/python/bin/python ../userscripts/create_isbn_edition.py kb

**Environment:**
    The python script can run on the following platforms:

    * Linux client
    * Google Chromebook (Linux container)
    * Toolforge Portal
    * PAWS

    LANG: default ISO 639-1 language code


**Applications:**
    Generate a book reference. Example for wp.en only:

    .. code:: wikitext

       {{Cite Q|Q63413107}}

    Use the Visual editor reference with Qnumber.

    .. seealso::

       - https://www.wikidata.org/wiki/Wikidata:WikiProject_Books
       - https://www.wikidata.org/wiki/Q21831105 (WikiProject Books)
       - https://meta.wikimedia.org/wiki/WikiCite
       - https://phabricator.wikimedia.org/tag/wikicite/
       - https://www.wikidata.org/wiki/Q21831105 (WikiCite)
       - https://www.wikidata.org/wiki/Q22321052 (Cite_Q)
       - https://www.mediawiki.org/wiki/Global_templates
       - https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData
       - https://meta.wikimedia.org/wiki/WikiCite/Shared_Citations
       - https://www.wikidata.org/wiki/Q36524 (Authority control)
       - https://meta.wikimedia.org/wiki/Community_Wishlist_Survey_2021/Wikidata/Bibliographical_references/sources_for_wikidataitems

**Wikidata Query:**
    * List of editions about musicians: https://w.wiki/5aaz
    * List of editions having ISBN number: https://w.wiki/5akq

**Related projects:**
    * :phab:`T314942`
    * :phab:`T282719`
    * :phab:`T214802`
    * :phab:`T208134`
    * :phab:`T138911`
    * :phab:`T20814`
    * :wiki:`User:Citation_bot`
    * https://zenodo.org/record/55004#.YvwO4hTP1D8

**Other systems:**
    * https://isbn.org/ISBN_converter
    * :wiki:`bibliographic_database`
    * https://www.titelbank.nl/pls/ttb/f?p=103:4012:::NO::P4012_TTEL_ID:3496019&cs=19BB8084860E3314502A1F777F875FE61
    * https://isbndb.com/apidocs/v2
    * https://isbndb.com/book/9780404150006

**Documentation:**
    * :wiki:`ISBN`
    * https://pypi.org/project/isbnlib/
    * https://buildmedia.readthedocs.org/media/pdf/isbnlib/v3.4.5/isbnlib.pdf
    * https://www.wikidata.org/wiki/Property:P212
    * http://www.isbn.org/standards/home/isbn/international/hyphenation-instructions.asp
    * https://isbntools.readthedocs.io/en/latest/info.html
    * :wiki:`List_of_ISO_639-1_codes`

    * https://www.wikidata.org/wiki/Wikidata:List_of_properties/work
    * https://www.wikidata.org/wiki/Template:Book_properties
    * https://www.wikidata.org/wiki/Template:Bibliographic_properties
    * https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData
    * https://www.wikidata.org/wiki/Help:Sources
    * https://www.wikidata.org/wiki/Q22696135 (Wikidata references module)

    * https://www.geeksforgeeks.org/searching-books-with-python/
    * http://classify.oclc.org/classify2/ClassifyDemo
    * :mod:`pywikibot`
    * :api:`Search`
    * https://www.mediawiki.org/wiki/Wikibase/API

    * :wiki:`Wikipedia:Book_sources`
    * :wiki:`https://en.wikipedia.org/wiki/Wikipedia:ISBN`
    * https://www.boek.nl/nur
    * https://isbnlib.readthedocs.io/_/downloads/en/latest/pdf/
    * https://www.wikidata.org/wiki/Special:BookSources/978-94-014-9746-6

    * **Goodreads:**

      - https://github.com/akkana/scripts/blob/master/bookfind.py
      - https://www.kaggle.com/code/hoshi7/goodreads-analysis-and-recommending-books?scriptVersionId=18346227
      - https://help.goodreads.com/s/question/0D51H00005FzcX1SAJ/how-can-i-search-by-isbn
      - https://help.goodreads.com/s/article/Librarian-Manual-ISBN-10-ISBN-13-and-ASINS
      - https://www.goodreads.com/book/show/203964185-de-nieuwe-wereldeconomie

.. versionadded:: 7.7
.. versionchanged:: 9.6
   several implementation improvements
"""  # noqa: E501, W505
#
# (C) Pywikibot team, 2022-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import os  # Operating system
import re  # Regular expressions (very handy!)
import sys  # System calls
from contextlib import suppress
from datetime import date
from pprint import pformat
from typing import Any

import pywikibot  # API interface to Wikidata
from pywikibot.config import verbose_output as verbose
from pywikibot.tools import first_upper


try:
    import isbnlib
except ImportError as e:
    isbnlib = e

try:
    from unidecode import unidecode
except ImportError as e:
    unidecode = e

# Global variables
# Module name (using the Pywikibot package)
pgmlic = 'MIT License'
creator = 'User:Geertivp'

MAINLANG = 'en:mul'
MULANG = 'mul'

# Exit on fatal error (can be disabled with -p; please take care)
exitfatal = True
exitstat = 0  # (default) Exit status

# Wikibase properties
INSTANCEPROP = 'P31'
AUTHORPROP = 'P50'
EDITORPROP = 'P98'
PROFESSIONPROP = 'P106'
ILLUSTRATORPROP = 'P110'
PUBLISHERPROP = 'P123'
# STYLEPROP = 'P135'
# GENREPROP = 'P136'
# BASEDONPROP = 'P144'
# PREVSERIALPROP = 'P155'
# NEXTSERIALPROP = 'P156'
# PRIZEPROP = 'P166'
# SERIALPROP = 'P179'
# COLLIONPROP = 'P195'
ISBNPROP = 'P212'
ISNIIDPROP = 'P213'
# BNFIDPROP = 'P268'
PLACEPUBPROP = 'P291'
OCLDIDPROP = 'P243'
REFPROP = 'P248'
# EDITIONIDPROP = 'P393'
EDITIONLANGPROP = 'P407'
WIKILANGPROP = 'P424'
# ORIGCOUNTRYPROP = 'P495'
ORCIDIDPROP = 'P496'
PUBYEARPROP = 'P577'
WRITTENWORKPROP = 'P629'
# OPENLIBIDPROP = 'P648'
# TRANSLATORPROP = 'P655'
# PERSONPROP = 'P674'
GOOGLEBOOKIDPROP = 'P675'
# INTARCHIDPROP = 'P724'
EDITIONPROP = 'P747'
# CONTRIBUTORPROP = 'P767'
REFDATEPROP = 'P813'
# STORYLOCPROP = 'P840'
# PRINTEDBYPROP = 'P872'
MAINSUBPROP = 'P921'
# INSPIREDBYPROP = 'P941'
ISBN10PROP = 'P957'
# SUDOCIDPROP = 'P1025'
DEWCLASIDPROP = 'P1036'
# EULIDPROP = 'P1084'
# LIBTHINGIDPROP = 'P1085'
NUMBEROFPAGESPROP = 'P1104'
# LCOCLCCNIDPROP = 'P1144'
# LIBCONGRESSIDPROP = 'P1149'
# BNIDPROP = 'P1143'
# UDCPROP = 'P1190'
# DNBIDPROP = 'P1292'
DESCRIBEDBYPROP = 'P1343'
EDITIONTITLEPROP = 'P1476'
SEQNRPROP = 'P1545'
EDITIONSUBTITLEPROP = 'P1680'
# ASSUMEDAUTHORPROP = 'P1779'
# RSLBOOKIDPROP = 'P1815'
# RSLEDIDPROP = 'P1973'
# GUTENBERGIDPROP = 'P2034'
FASTIDPROP = 'P2163'
# NUMPARTSPROP = 'P2635'
PREFACEBYPROP = 'P2679'
AFTERWORDBYPROP = 'P2680'
GOODREADSIDPROP = 'P2969'
# CZLIBIDPROP = 'P3184'
# BABELIOIDPROP = 'P3631'
# ESTCIDPROP = 'P3939'
OCLCWORKIDPROP = 'P5331'
# K10IDPROP = 'P6721'
# CREATIVEWORKTYPE = 'P7937'
LIBCONGEDPROP = 'P8360'
GOODREADSWORKIDPROP = 'P8383'

# Instances
AUTHORINSTANCE = 'Q482980'
ILLUSTRATORINSTANCE = 'Q15296811'
WRITERINSTANCE = 'Q36180'

authorprop_list = {
    AUTHORPROP,
    EDITORPROP,
    ILLUSTRATORPROP,
    PREFACEBYPROP,
    AFTERWORDBYPROP,
}

# Profession author instances
author_profession = {
    AUTHORINSTANCE,
    ILLUSTRATORINSTANCE,
    WRITERINSTANCE,
}

# List of digital library synonyms
bookliblist = {
    '-': 'wiki',
    'dnl': 'dnb',
    'google': 'goob',
    'gb': 'goob',
    'isbn': 'isbndb',
    'kbn': 'kb',
    'wc': 'worldcat',
    'wcat': 'worldcat',
    'wikipedia': 'wiki',
    'wp': 'wiki',
}

# List of of digital libraries
# You can better run the script repeatedly with difference library sources.
# Content and completeness differs amongst libraryies.
bib_source = {
    # database ID: item number, label, default language, package
    'bnf': ('Q193563', 'Catalogue General (France)', 'fr', 'isbnlib-bnf'),
    'bol': ('Q609913', 'Bol.Com', 'en', 'isbnlib-bol'),
    'dnb': ('Q27302', 'Deutsche National Library', 'de', 'isbnlib-dnb'),
    'goob': ('Q206033', 'Google Books', 'en', 'isbnlib'),  # lib
    # A (paying) api key is needed
    'isbndb': ('Q117793433', 'isbndb.com', 'en', 'isbnlib'),
    'kb': ('Q1526131', 'Koninklijke Bibliotheek (Nederland)', 'nl',
           'isbnlib-kb'),
    # Not implemented in Belgium
    # 'kbr': ('Q383931', 'Koninklijke Bibliotheek (België)', 'nl', 'isbnlib'),
    'loc': ('Q131454', 'Library of Congress (US)', 'en', 'isbnlib-loc'),
    'mcues': ('Q750403', 'Ministerio de Cultura (Spain)', 'es',
              'isbnlib-mcues'),
    'openl': ('Q1201876', 'OpenLibrary.org', 'en', 'isbnlib'),  # lib
    'porbase': ('Q51882885', 'Portugal (urn.porbase.org)', 'pt',
                'isbnlib-porbase'),
    'sbn': ('Q576951', 'Servizio Bibliotecario Nazionale (Italië)', 'it',
            'isbnlib-sbn'),
    'wiki': ('Q121093616', 'Wikipedia.org', 'en', 'isbnlib'),   # lib
    'worldcat': ('Q76630151', 'WorldCat (worldcat2)', 'en',
                 'isbnlib-worldcat2'),
    # isbnlib-oclc
    # https://github.com/swissbib
    # others to be added
}

# Remap obsolete or non-standard language codes
langcode = {
    'dut': 'nl',
    'eng': 'en',
    'frans': 'fr',
    'fre': 'fr',
    'iw': 'he',
    'nld': 'nl',
}

# Statement property target validation rules
propreqobjectprop = {
    # Main subject statement requires an object with FAST ID property
    MAINSUBPROP: {FASTIDPROP},
}

# ISBN number: 10 or 13 digits with optional dashes (-)
# or DOI number with 10-prefix
ISBNRE = re.compile(r'[0-9–-]{10,17}')
NAMEREVRE = re.compile(r',(\s*.*)*$')  # Reverse lastname, firstname
PROPRE = re.compile(r'P[0-9]+')  # Wikidata P-number
QSUFFRE = re.compile(r'Q[0-9]+')  # Wikidata Q-number
# Remove trailing () suffix (keep only the base label)
SUFFRE = re.compile(r'\s*[(].*[)]$')

# Required statement for edition
# Additional statements can be added via command line parameters
target = {
    INSTANCEPROP: 'Q3331189',  # Is an instance of an edition
    # other statements to add
}

# Instance validation rules for properties
propreqinst = {
    AUTHORPROP: {'Q5'},  # Author requires human
    # Edition language requires at least one of (living, natural) language
    EDITIONLANGPROP: {'Q34770', 'Q33742', 'Q1288568'},
    # Is an instance of an edition
    INSTANCEPROP: {'Q24017414'},
    # Publisher requires type of publisher
    PUBLISHERPROP: {'Q41298', 'Q479716', 'Q1114515', 'Q1320047', 'Q2085381'},
    # Written work (requires list)
    WRITTENWORKPROP: ['Q47461344', 'Q7725634'],
}

# Wikidata transaction comment
transcmt = '#pwb Create ISBN edition'


def fatal_error(errcode, errtext):
    """A fatal error has occurred.

    Print the error message, and exit with an error code.
    """
    global exitstat

    exitstat = max(exitstat, errcode)
    pywikibot.critical(errtext)
    if exitfatal:		# unless we ignore fatal errors
        sys.exit(exitstat)
    else:
        pywikibot.warning('Proceed after fatal error')


def get_item_header(header: str | list[str]) -> str:
    """Get the item header (label, description, alias in user language).

    :param header: item label, description, or alias language list
    :return: label, description, or alias in the first available language
    """
    # Return one of the preferred labels
    for lang in main_languages:
        if lang in header:
            return header[lang]

    # Return any other available label
    for lang in header:
        return header[lang]

    return '-'


def get_item_header_lang(header: str | list[str], lang: str) -> str:
    """Get the item header (label, description, alias in user language).

    :param header: item label, description, or alias language list
    :param lang: language code
    :return: label, description, or alias in the first available language
    """
    # Try to get any explicit language code
    if lang in header:
        return header[lang]

    return get_item_header(header)


def get_item_page(qnumber) -> pywikibot.ItemPage:
    """Get the item; handle redirects."""
    if isinstance(qnumber, str):
        item = pywikibot.ItemPage(repo, qnumber)
        try:
            item.get()
        except pywikibot.exceptions.IsRedirectPageError:
            # Resolve a single redirect error
            item = item.getRedirectTarget()
            label = get_item_header(item.labels)
            pywikibot.warning(
                f'Item {label} ({qnumber}) redirects to {item.getID()}')
            qnumber = item.getID()
    else:
        item = qnumber
        qnumber = item.getID()

    while item.isRedirectPage():
        # Should fix the sitelinks
        item = item.getRedirectTarget()
        label = get_item_header(item.labels)
        pywikibot.warning(
            f'Item {label} ({qnumber}) redirects to {item.getID()}')
        qnumber = item.getID()

    return item


def get_language_preferences() -> list[str]:
    """Get the list of preferred languages.

    Uses environment variables LANG, LC_ALL, and LANGUAGE, 'en' is
    always appended.

    .. seealso::
       - :wiki:`List_of_ISO_639-1_codes

    :Return: List of ISO 639-1 language codes with strings delimited by
        ':'.
    """
    # See also:
    # https://www.gnu.org/software/gettext/manual/html_node/Locale-Environment-Variables.html
    mainlang = os.getenv('LANGUAGE',
                         os.getenv('LC_ALL',
                                   os.getenv('LANG', MAINLANG))).split(':')
    main_languages = [lang.split('_')[0] for lang in mainlang]

    # Cleanup language list (remove non-ISO codes)
    for lang in main_languages:
        if len(lang) > 3:
            main_languages.remove(lang)

    for lang in MAINLANG.split(':'):
        if lang not in main_languages:
            main_languages.append(lang)

    return main_languages


def item_is_in_list(statement_list: list, itemlist: list[str]) -> bool:
    """Verify if statement list contains at least one item from the itemlist.

    param statement_list: Statement list
    param itemlist: List of values (string)
    return: Whether the item matches
    """
    for seq in statement_list:
        with suppress(AttributeError):  # Ignore NoneType error
            isinlist = seq.getTarget().getID()
            if isinlist in itemlist:
                return True
    return False


def item_has_label(item, label: str) -> bool:
    """Verify if the item has a label.

    :param item: Item
    :param label: Item label
    :return: Whether the item has a label
    """
    label = unidecode(label).casefold()
    for lang in item.labels:
        if unidecode(item.labels[lang]).casefold() == label:
            return True

    for lang in item.aliases:
        for seq in item.aliases[lang]:
            if unidecode(seq).casefold() == label:
                return True

    return False


def is_in_value_list(statement_list: list, valuelist: list[str]) -> bool:
    """Verify if statement list contains at least one value from the valuelist.

    :param statement_list: Statement list of values
    :param valuelist: List of values
    :return: True when match, False otherwise
    """
    for seq in statement_list:
        if seq.getTarget() in valuelist:
            return True
    return False


def get_canon_name(baselabel: str) -> str:
    """Get standardised name.

    :param baselabel: input label
    """
    suffix = SUFFRE.search(baselabel)  # Remove () suffix, if any
    if suffix:
        baselabel = baselabel[:suffix.start()]  # Get canonical form

    colonloc = baselabel.find(':')
    commaloc = NAMEREVRE.search(baselabel)

    # Reorder "lastname, firstname" and concatenate with space
    if colonloc < 0 and commaloc:
        baselabel = (baselabel[commaloc.start() + 1:]
                     + ' ' + baselabel[:commaloc.start()])
        baselabel = baselabel.replace(',', ' ')  # Remove remaining ","

    # Remove redundant spaces
    baselabel = ' '.join(baselabel.split())
    return baselabel


def get_item_list(item_name: str,
                  instance_id: str | set[str] | list[str]) -> set[str]:
    """Get list of items by name, belonging to an instance (list).

    Normally there should have one single best match. The caller should
    take care of homonyms.

    .. seealso::
       https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities

    :param item_name: Item name (case sensitive)
    :param instance_id: Instance ID
    :return: Set of items
    """
    # Ignore accents and case
    item_name_canon = unidecode(item_name).casefold()

    item_list = set()
    # Loop though items, total should be reasonable value
    for res in repo.search_entities(item_name, mainlang, total=20):
        item = get_item_page(res['id'])

        # Matching instance
        if INSTANCEPROP not in item.claims \
           or not item_is_in_list(item.claims[INSTANCEPROP], instance_id):
            continue

        # Search all languages, ignore label case and accents
        for lang in item.labels:
            if item_name_canon == unidecode(item.labels[lang].casefold()):
                item_list.add(item.getID())  # Label math
                break

        for lang in item.aliases:
            for seq in item.aliases[lang]:
                if item_name_canon == unidecode(seq).casefold():
                    item_list.add(item)  # Alias match
                    break

    pywikibot.log(item_list)
    return item_list


def get_item_with_prop_value(prop: str, propval: str) -> set[str]:
    """Get list of items that have a property/value statement.

    .. seealso:: :meth:`Site.search()
       <pywikibot.site._generators.GeneratorsMixin.search>`

    :param prop: Property ID
    :param propval: Property value
    :return: List of items (Q-numbers)
    """
    srsearch = f'{prop}:{propval}'
    pywikibot.debug(f'Search statement: {srsearch}')
    item_name_canon = unidecode(propval).casefold()
    item_list = set()

    # Loop though items
    for row in repo.search(srsearch, where='text', total=50):
        qnumber = row['title']
        item = get_item_page(qnumber)

        if prop not in item.claims:
            continue

        for seq in item.claims[prop]:
            if unidecode(seq.getTarget()).casefold() == item_name_canon:
                item_list.add(item)  # Found match
                break

    pywikibot.log(item_list)
    return item_list


def amend_isbn_edition(isbn_number: str) -> int:
    """Amend ISBN registration in Wikidata.

    It is registering the ISBN-13 data via P212, depending on the data
    obtained from the digital library.

    :param isbn_number: ISBN number (10 or 13 digits with optional
        hyphens)
    :return: Return status which is:

        * 0:  Amended (found or created)
        * 1:  Not found
        * 2:  Ambiguous
        * 3:  Other error
    """
    isbn_number = isbn_number.strip()
    if not isbn_number:
        return 3  # Do nothing when the ISBN number is missing

    pywikibot.info()

    # Some digital library services raise failure
    try:
        # Get ISBN basic data
        isbn_data = isbnlib.meta(isbn_number, service=booklib)
        # {
        #     'ISBN-13': '9789042925564',
        #     'Title': 'De Leuvense Vaart - Van De Vaartkom Tot Wijgmaal. '
        #              'Aspecten Uit De Industriele Geschiedenis Van Leuven',
        #     'Authors': ['A. Cresens'],
        #     'Publisher': 'Peeters Pub & Booksellers',
        #     'Year': '2012',
        #     'Language': 'nl',
        #  }
    except isbnlib._exceptions.NotRecognizedServiceError as error:
        fatal_error(4, f'{error}\n    pip install isbnlib-xxx')
    except isbnlib._exceptions.NotValidISBNError as error:
        pywikibot.error(error)
        return 1
    except Exception as error:
        # When the book is unknown the function returns
        pywikibot.error(f'{isbn_number} not found\n{error}')
        return 1

    # Others return an empty result
    if not isbn_data:
        pywikibot.error(
            f'Unknown ISBN book number {isbnlib.mask(isbn_number)}')
        return 1

    # Show the raw results
    # Can be very useful in troubleshooting
    if verbose:
        pywikibot.info('\n' + pformat(isbn_data))

    return add_claims(isbn_data)


def add_claims(isbn_data: dict[str, Any]) -> int:  # noqa: C901
    """Inspect isbn_data and add claims if possible."""
    # targetx is not global (to allow for language specific editions)

    # Set default language from book library
    # Mainlang was set to default digital library language code
    booklang = mainlang
    if isbn_data['Language']:
        # Get the book language from the ISBN book number
        # Can overwrite the default language
        booklang = isbn_data['Language'].strip().lower()

        # Replace obsolete or non-standard codes
        if booklang in langcode:
            booklang = langcode[booklang]

    # Get Wikidata language code
    lang_list = get_item_list(booklang, propreqinst[EDITIONLANGPROP])

    # Hardcoded parameter
    lang_list -= {'Q3504110'}  # Remove duplicate "En" language

    if not lang_list:
        # Can' t store unknown language (need to update mapping table...)
        pywikibot.error(f'Unknown language {booklang}'.format(booklang))
        return 3

    if len(lang_list) != 1:
        # Ambiguous language
        pywikibot.warning(f'Ambiguous language {booklang}\n'
                          f'[lang_item.getID() for lang_item in lang_list]')
        return 3

    # Set edition language item number
    lang_item = lang_list.pop()
    target[EDITIONLANGPROP] = lang_item.getID()

    # Require short Wikipedia language code
    if len(booklang) > 3 and WIKILANGPROP in lang_item.claims:
        # Get official language code
        booklang = lang_item.claims[WIKILANGPROP][0].getTarget()

    # Get edition title
    edition_title = isbn_data['Title'].strip()

    # Split (sub)title with first matching delimiter
    # By priority of parsing strings:
    for seq in ['|', '. ', ' - ', ': ', '; ', ', ']:
        titles = edition_title.split(seq)
        if len(titles) > 1:
            break

    if verbose:  # Print (sub)title(s)
        pywikibot.info('\n' + pformat(titles))

    # Get formatted ISBN number
    isbn_number = isbn_data['ISBN-13']  # Numeric format
    isbn_fmtd = isbnlib.mask(isbn_number)  # Canonical format
    pywikibot.info(isbn_fmtd)  # First one

    # Get main title and subtitle
    objectname = titles[0].strip()
    subtitle = ''  # If there was no delimiter, there is no subtitle
    if len(titles) > 1:
        # Redundant "subtitles" are ignored
        subtitle = first_upper(titles[1].strip())

    # Get formatted ISBN number
    isbn_number = isbn_data['ISBN-13']  # Numeric format
    isbn_fmtd = isbnlib.mask(isbn_number)  # Canonical format (with "-")
    pywikibot.log(isbn_fmtd)

    # Search the ISBN number both in canonical and numeric format
    qnumber_list = get_item_with_prop_value(ISBNPROP, isbn_fmtd)
    qnumber_list.update(get_item_with_prop_value(ISBNPROP, isbn_number))

    # Get additional data from the digital library
    # This could fail with
    # ISBNLibHTTPError('403 Are you making many requests?')
    # Handle ISBN classification
    # pwb create_isbn_edition - de P407 Q188 978-3-8376-5645-9 Q113460204
    # {
    #     'owi': '11103651812',
    #     'oclc': '1260160983',
    #     'lcc': 'TK5105.8882',
    #     'ddc': '300',
    #     'fast': {
    #         '1175035': 'Wikis (Computer science)',
    #         '1795979': 'Wikipedia',
    #         '1122877': 'Social sciences'
    #     }
    # }
    isbn_classify = {}
    try:
        isbn_classify = isbnlib.classify(isbn_number)
    except Exception as error:
        pywikibot.error(f'Classify error, {error}')
    else:
        pywikibot.info('\n' + pformat(isbn_classify))

    # Note that only older works have an ISBN10 number
    isbn10_number = ''
    isbn10_fmtd = ''

    # Take care of ISBNLibHTTPError
    # (classify is more important than obsolete ISBN-10)
    # ISBNs were not used before 1966
    # Since 2007, new ISBNs are only issued in the ISBN-13 format
    if isbn_fmtd.startswith('978-'):
        try:
            # Returns empty string for non-978 numbers
            isbn10_number = isbnlib.to_isbn10(isbn_number)
            if isbn10_number:
                isbn10_fmtd = isbnlib.mask(isbn10_number)
                pywikibot.info(f'ISBN 10: {isbn10_fmtd}')
                qnumber_list.update(
                    get_item_with_prop_value(ISBN10PROP, isbn10_fmtd))
                qnumber_list.update(
                    get_item_with_prop_value(ISBN10PROP, isbn10_number))
        except Exception as error:
            pywikibot.error(f'ISBN 10 error, {error}')

    # Create or amend the item

    if not qnumber_list:
        # Create the edition
        label = {MULANG: objectname}
        item = pywikibot.ItemPage(repo)  # Create item
        item.editLabels(label, summary=transcmt, bot=wdbotflag)
        qnumber = item.getID()  # Get new item number
        status = 'Created'
    elif len(qnumber_list) == 1:
        item = qnumber_list.pop()
        qnumber = item.getID()

        # Update item only if edition, or instance is missing
        if (INSTANCEPROP in item.claims
                and not item_is_in_list(item.claims[INSTANCEPROP],
                                        [target[INSTANCEPROP]])):
            pywikibot.error(
                f'Item {qnumber} {isbn_fmtd} is not an edition; not updated')
            return 3

        # Add missing book label for book language
        if MULANG not in item.labels:
            item.labels[MULANG] = objectname
            item.editLabels(item.labels, summary=transcmt, bot=wdbotflag)
        status = 'Found'
    else:
        pywikibot.error(
            f'Ambiguous ISBN number {isbn_fmtd}, '
            f'{[item.getID() for item in qnumber_list]} not updated'
        )
        return 2

    pywikibot.warning(f'{status} item {qnumber}: P212: {isbn_fmtd} '
                      f'language {booklang} ({target[EDITIONLANGPROP]}) '
                      f'{objectname}')

    # Register missing statements
    pywikibot.debug(target)
    for propty, title in target.items():
        if propty not in item.claims:
            if propty not in proptyx:
                proptyx[propty] = pywikibot.PropertyPage(repo, propty)

            # Target could get overwritten locally
            targetx[propty] = pywikibot.ItemPage(repo, title)

            claim = pywikibot.Claim(repo, propty)
            claim.setTarget(targetx[propty])
            item.addClaim(claim, bot=wdbotflag, summary=transcmt)
            pywikibot.warning(
                f'Add {get_item_header_lang(proptyx[propty].labels, booklang)}'
                f':{get_item_header_lang(targetx[propty].labels, booklang)} '
                f'({propty}:{title})'
            )

            # Set source reference
            if booklib in bib_sourcex:
                # A source reference can be only used once
                # Expected error:
                # "The provided Claim instance is already used in an entity"
                # TODO: This error is sometimes raised without reason
                try:
                    claim.addSources(booklib_ref, summary=transcmt)
                except ValueError as error:
                    pywikibot.error(f'Source reference error, {error}')

    if (DESCRIBEDBYPROP not in item.claims
        or not item_is_in_list(item.claims[DESCRIBEDBYPROP],
                               [bib_source[booklib][0]])):
        claim = pywikibot.Claim(repo, DESCRIBEDBYPROP)
        claim.setTarget(bib_sourcex[booklib])
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning(
            f'Add described by:{booklib} - {bib_source[booklib][1]} '
            f'({DESCRIBEDBYPROP}:{bib_source[booklib][0]})'
        )

    if ISBNPROP not in item.claims:
        # Create formatted ISBN-13 number
        claim = pywikibot.Claim(repo, ISBNPROP)
        claim.setTarget(isbn_fmtd)
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning(f'Add ISBN number ({ISBNPROP}) {isbn_fmtd}')
    else:
        for seq in item.claims[ISBNPROP]:
            # Update unformatted to formatted ISBN-13
            if seq.getTarget() == isbn_number:
                seq.changeTarget(isbn_fmtd, bot=wdbotflag, summary=transcmt)
                pywikibot.warning(
                    f'Set formatted ISBN number ({ISBNPROP}): {isbn_fmtd}')

    if not isbn10_fmtd:
        pass
    elif ISBN10PROP in item.claims:
        for seq in item.claims[ISBN10PROP]:
            # Update unformatted to formatted ISBN-10
            if seq.getTarget() == isbn10_number:
                seq.changeTarget(isbn10_fmtd, bot=wdbotflag, summary=transcmt)
                pywikibot.warning('Set formatted ISBN-10 number '
                                  f'({ISBN10PROP}): {isbn10_fmtd}')
    else:
        # Create ISBN-10 number
        claim = pywikibot.Claim(repo, ISBN10PROP)
        claim.setTarget(isbn10_fmtd)
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning(f'Add ISBN-10 number ({ISBN10PROP}) {isbn10_fmtd}')

    # Title
    if EDITIONTITLEPROP not in item.claims:
        claim = pywikibot.Claim(repo, EDITIONTITLEPROP)
        claim.setTarget(
            pywikibot.WbMonolingualText(text=objectname, language=booklang))
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning(f'Add Title ({EDITIONTITLEPROP}) {objectname}')

    # Subtitle
    if subtitle and EDITIONSUBTITLEPROP not in item.claims:
        claim = pywikibot.Claim(repo, EDITIONSUBTITLEPROP)
        claim.setTarget(
            pywikibot.WbMonolingualText(text=subtitle, language=booklang))
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning(f'Add Subtitle ({EDITIONSUBTITLEPROP}): {subtitle}')

    # Date of publication
    pub_year = isbn_data['Year']
    if pub_year and PUBYEARPROP not in item.claims:
        claim = pywikibot.Claim(repo, PUBYEARPROP)
        claim.setTarget(pywikibot.WbTime(year=int(pub_year), precision='year'))
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning(
            f'Add Year of publication ({PUBYEARPROP}): {isbn_data["Year"]}')

    # Set the author list
    author_cnt = 0
    for author_name in isbn_data['Authors']:
        author_name = author_name.strip()
        if not author_name:
            continue

        author_cnt += 1
        # Reorder "lastname, firstname" and concatenate with space
        author_name = get_canon_name(author_name)
        author_list = get_item_list(author_name, propreqinst[AUTHORPROP])

        if len(author_list) == 1:
            add_author = True
            author_item = author_list.pop()

            if (PROFESSIONPROP not in author_item.claims
                    or not item_is_in_list(author_item.claims[PROFESSIONPROP],
                                           author_profession)):
                # Add profession:author statement
                claim = pywikibot.Claim(repo, PROFESSIONPROP)
                claim.setTarget(target_author)
                author_item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                pywikibot.warning('Add profession: author '
                                  f'({PROFESSIONPROP}:{AUTHORINSTANCE}) to '
                                  f'{author_name} ({author_item.getID()})')

            # Possibly found as author?
            # Possibly found as editor?
            # Possibly found as illustrator/photographer?
            for prop in authorprop_list:
                if prop not in item.claims:
                    continue

                for claim in item.claims[prop]:
                    book_author = claim.getTarget()
                    if book_author == author_item:
                        # Add missing sequence number
                        if SEQNRPROP not in claim.qualifiers:
                            qualifier = pywikibot.Claim(repo, SEQNRPROP)
                            qualifier.setTarget(str(author_cnt))
                            claim.addQualifier(qualifier, bot=wdbotflag,
                                               summary=transcmt)
                        add_author = False
                        break

                    if item_has_label(book_author, author_name):
                        pywikibot.warning(
                            f'Edition has conflicting author ({prop}) '
                            f'{author_name} ({book_author.getID()})'
                        )
                        add_author = False
                        break

            if add_author:
                claim = pywikibot.Claim(repo, AUTHORPROP)
                claim.setTarget(author_item)
                item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                pywikibot.warning(f'Add author {author_cnt}:{author_name} '
                                  f'({AUTHORPROP}:{author_item.getID()})')

                # Add sequence number
                qualifier = pywikibot.Claim(repo, SEQNRPROP)
                qualifier.setTarget(str(author_cnt))
                claim.addQualifier(qualifier, bot=wdbotflag, summary=transcmt)
        elif author_list:
            pywikibot.error(
                f'Ambiguous author: {author_name}'
                f'({[author_item.getID() for author_item in author_list]})'
            )
        else:
            pywikibot.error(f'Unknown author: {author_name}')

    # Set the publisher
    publisher_name = isbn_data['Publisher'].strip()
    if publisher_name:
        publisher_list = get_item_list(publisher_name,
                                       propreqinst[PUBLISHERPROP])

        if len(publisher_list) == 1:
            publisher_item = publisher_list.pop()
            if (PUBLISHERPROP not in item.claims
                    or not item_is_in_list(item.claims[PUBLISHERPROP],
                                           [publisher_item.getID()])):
                claim = pywikibot.Claim(repo, PUBLISHERPROP)
                claim.setTarget(publisher_item)
                item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                pywikibot.warning(
                    f'Add publisher: {publisher_name} '
                    f'({PUBLISHERPROP}:{publisher_item.getID()})'
                )
        elif publisher_list:
            pywikibot.error(
                f'Ambiguous publisher: {publisher_name} '
                f'({[p_item.getID() for p_item in publisher_list]})'
            )
        else:
            pywikibot.error(f'Unknown publisher: {publisher_name}')

    # Amend Written work relationship (one to many relationship)
    if WRITTENWORKPROP in item.claims:
        work = item.claims[WRITTENWORKPROP][0].getTarget()
        if len(item.claims[WRITTENWORKPROP]) > 1:  # Many to many (error)
            pywikibot.error(f'Written work {work.getID()} is not unique')
        else:
            # Enhance data quality for Written work
            if ISBNPROP in work.claims:
                pywikibot.error(f'Written work {work.getID()} must not have'
                                ' an ISBN number')

            # Add written work instance
            if (INSTANCEPROP not in work.claims
                    or not item_is_in_list(work.claims[INSTANCEPROP],
                                           propreqinst[WRITTENWORKPROP])):
                claim = pywikibot.Claim(repo, INSTANCEPROP)
                claim.setTarget(get_item_page(propreqinst[WRITTENWORKPROP][0]))
                work.addClaim(claim, bot=wdbotflag, summary=transcmt)
                pywikibot.warning(
                    f'Add is a:written work instance ({INSTANCEPROP}:'
                    f'{propreqinst[WRITTENWORKPROP][0]}) '
                    f'to written work {work.getID()}'
                )

            # Check if inverse relationship to "edition of" exists
            if (EDITIONPROP not in work.claims
                or not item_is_in_list(work.claims[EDITIONPROP],
                                       [qnumber])):
                claim = pywikibot.Claim(repo, EDITIONPROP)
                claim.setTarget(item)
                work.addClaim(claim, bot=wdbotflag, summary=transcmt)
                pywikibot.warning(
                    f'Add edition statement ({EDITIONPROP}:{qnumber}) to '
                    f'written work {work.getID()}'
                )

    # We need to first set the OCLC ID
    # Because OCLC Work ID can be in conflict for edition
    if 'oclc' in isbn_classify and OCLDIDPROP not in item.claims:
        claim = pywikibot.Claim(repo, OCLDIDPROP)
        claim.setTarget(isbn_classify['oclc'])
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning(
            f'Add OCLC ID ({OCLDIDPROP}) {isbn_classify["oclc"]}')

    # OCLC ID and OCLC Work ID should not be both assigned
    # Move OCLC Work ID to work if possible
    if OCLDIDPROP in item.claims and OCLCWORKIDPROP in item.claims:
        # Check if OCLC Work is available
        oclcwork = item.claims[OCLCWORKIDPROP][0]  # OCLC Work should be unique
        # Get the OCLC Work ID from the edition
        oclcworkid = oclcwork.getTarget()

        # Keep OCLC Work ID in edition if ambiguous
        if len(item.claims[OCLCWORKIDPROP]) > 1:
            pywikibot.error(
                'OCLC Work ID {work.getID()} is not unique; not moving')
        elif WRITTENWORKPROP in item.claims:
            # Edition should belong to only one single work
            work = item.claims[WRITTENWORKPROP][0].getTarget()
            pywikibot.warning(
                f'Move OCLC Work ID {oclcworkid} to work {work.getID()}')

            # Keep OCLC Work ID in edition if mismatch or ambiguity
            if len(item.claims[WRITTENWORKPROP]) > 1:
                pywikibot.error(
                    f'Written Work {work.getID()} is not unique; not moving')
            elif OCLCWORKIDPROP not in work.claims:
                claim = pywikibot.Claim(repo, OCLCWORKIDPROP)
                claim.setTarget(oclcworkid)
                work.addClaim(claim, bot=wdbotflag,
                              summary='#pwb Move OCLC Work ID')
                pywikibot.warning(
                    f'Move OCLC Work ID ({OCLCWORKIDPROP}) {oclcworkid} to '
                    f'written work {work.getID()}'
                )

                # OCLC Work ID does not belong to edition
                item.removeClaims(oclcwork, bot=wdbotflag,
                                  summary='#pwb Move OCLC Work ID')
            elif is_in_value_list(work.claims[OCLCWORKIDPROP], oclcworkid):
                # OCLC Work ID does not belong to edition
                item.removeClaims(oclcwork, bot=wdbotflag,
                                  summary='#pwb Remove redundant OCLC Work ID')
            else:
                pywikibot.error(
                    f'OCLC Work ID mismatch {oclcworkid} - '
                    f'{work.claims[OCLCWORKIDPROP][0].getTarget()}; not moving'
                )
        else:
            pywikibot.error(f'OCLC Work ID {oclcworkid} conflicts with OCLC '
                            f'ID {item.claims[OCLDIDPROP][0].getTarget()} and'
                            ' no work available')

    # OCLC work ID should not be registered for editions, only for works
    if 'owi' not in isbn_classify:
        pass
    elif WRITTENWORKPROP in item.claims:
        # Get the work related to the edition
        # Edition should only have one single work
        # Assign the OCLC work ID if missing in work
        work = item.claims[WRITTENWORKPROP][0].getTarget()
        if (OCLCWORKIDPROP not in work.claims
                or not is_in_value_list(work.claims[OCLCWORKIDPROP],
                                        isbn_classify['owi'])):
            claim = pywikibot.Claim(repo, OCLCWORKIDPROP)
            claim.setTarget(isbn_classify['owi'])
            work.addClaim(claim, bot=wdbotflag, summary=transcmt)
            pywikibot.warning(
                f'Add OCLC work ID ({OCLCWORKIDPROP}) {isbn_classify["owi"]} '
                f'to work {work.getID()}'
            )
    elif OCLDIDPROP in item.claims:
        pywikibot.warning(
            f'OCLC Work ID {isbn_classify["owi"]} ignored because of OCLC ID'
            f'{item.claims[OCLDIDPROP][0].getTarget()}'
        )
    elif (OCLCWORKIDPROP not in item.claims
            or not is_in_value_list(item.claims[OCLCWORKIDPROP],
                                    isbn_classify['owi'])):
        # Assign the OCLC work ID only if there is no work, and no OCLC ID for
        # edition
        claim = pywikibot.Claim(repo, OCLCWORKIDPROP)
        claim.setTarget(isbn_classify['owi'])
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning(f'Add OCLC work ID ({OCLCWORKIDPROP}) '
                          f'{isbn_classify["owi"]} to edition')

    # Reverse logic for moving OCLC ID and P212 (ISBN) from work to
    # edition is more difficult because of 1:M relationship...

    # Same logic as for OCLC (work) ID

    # Goodreads-identificatiecode (P2969)

    # Goodreads-identificatiecode for work (P8383) should not be
    # registered for editions; should rather use P2969

    # Library of Congress Classification (works and editions)
    if 'lcc' in isbn_classify and LIBCONGEDPROP not in item.claims:
        claim = pywikibot.Claim(repo, LIBCONGEDPROP)
        claim.setTarget(isbn_classify['lcc'])
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning(
            'Add Library of Congress Classification for edition '
            f'({LIBCONGEDPROP}) {isbn_classify["lcc"]}'
        )

    # Dewey Decimale Classificatie
    if 'ddc' in isbn_classify and DEWCLASIDPROP not in item.claims:
        claim = pywikibot.Claim(repo, DEWCLASIDPROP)
        claim.setTarget(isbn_classify['ddc'])
        item.addClaim(claim, bot=wdbotflag, summary=transcmt)
        pywikibot.warning(f'Add Dewey Decimale Classificatie ({DEWCLASIDPROP})'
                          f' {isbn_classify["ddc"]}')

    # Register Fast ID using P921 (main subject) through P2163 (Fast ID)
    # https://www.wikidata.org/wiki/Q3294867
    # https://nl.wikipedia.org/wiki/Faceted_Application_of_Subject_Terminology
    # https://www.oclc.org/research/areas/data-science/fast.html
    # https://www.oclc.org/content/dam/oclc/fast/FAST-quick-start-guide-2022.pdf

    # Authority control identifier from WorldCat's “FAST Linked Data”
    # authority file (external ID P2163)
    # Corresponding to P921 (Wikidata main subject)
    if 'fast' in isbn_classify:
        for fast_id in isbn_classify['fast']:
            # Get the main subject item number
            qmain_subject = get_item_with_prop_value(FASTIDPROP, fast_id)
            main_subject_label = isbn_classify['fast'][fast_id].lower()

            if len(qmain_subject) == 1:
                # Get main subject and label
                main_subject_label = get_item_header(qmain_subject[0].labels)

                if (MAINSUBPROP in item.claims
                    and item_is_in_list(item.claims[MAINSUBPROP],
                                        [qmain_subject[0].getID()])):
                    pywikibot.log(
                        f'Skipping main subject ({MAINSUBPROP}): '
                        f'{main_subject_label} ({qmain_subject[0]})'
                    )
                else:
                    claim = pywikibot.Claim(repo, MAINSUBPROP)
                    claim.setTarget(qmain_subject[0])
                    # Add main subject
                    item.addClaim(claim, bot=wdbotflag, summary=transcmt)
                    pywikibot.warning(
                        f'Add main subject:{main_subject_label} '
                        f'({MAINSUBPROP}:{qmain_subject[0]})'
                    )
            elif qmain_subject:
                pywikibot.error(f'Ambiguous main subject for Fast ID {fast_id}'
                                f' - {main_subject_label}')
            else:
                pywikibot.error(f'Main subject not found for Fast ID {fast_id}'
                                f' - {main_subject_label}')

    show_final_information(isbn_number)
    return 0


def show_final_information(isbn_number: str) -> None:
    """Print additional information.

    Get optional information.Could generate too many transactions errors;
    so the process might stop at the first error.
    """
    # Book description
    isbn_description = isbnlib.desc(isbn_number)
    if isbn_description:
        pywikibot.info()
        pywikibot.info(isbn_description)

    # ISBN info
    isbn_info = isbnlib.info(isbn_number)
    if isbn_info:
        pywikibot.info(isbn_info)

    # DOI number -- No warranty that the document number really exists on
    # https:/doi.org
    isbn_doi = isbnlib.doi(isbn_number)
    if isbn_doi:
        pywikibot.info(isbn_doi)

    # ISBN editions
    isbn_editions = isbnlib.editions(isbn_number, service='merge')
    if isbn_editions:
        pywikibot.info(isbn_editions)

    # Book cover images
    isbn_cover = isbnlib.cover(isbn_number)
    for seq in isbn_cover:
        pywikibot.info(f'{seq}: {isbn_cover[seq]}')

    # BibTex currently does not work (service not available); code was removed.


def main(*args: str) -> None:
    """Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    **Algorithm:**

    ::

        Get parameters from shell
        Validate parameters
        Get ISBN data
        Convert ISBN data:
            Reverse names when Lastname, Firstname
        Get additional data
        Register ISBN data into Wikidata:
            Add source reference when creating the item:
                (digital library instance, retrieval date)
            Create or amend items or claims:
                Number the authors in order of appearance
                Check data consistency
                Correct data quality problems:
                    OCLC Work ID for Written work
                    Written work instance statement
                    Inverse relationship written work -> edition
                    Move/register OCLC work ID to/with written work
        Manually corrections:
            Create missing (referenced) items
                (authors, publishers, written works, main subject/FAST ID)
            Resolve ambiguous values


    :param args: command line arguments
    """
    global bib_sourcex
    global booklib
    global booklib_ref
    global exitstat
    global mainlang
    global main_languages
    global proptyx
    global repo
    global target_author
    global targetx
    global wdbotflag

    # Get optional parameters
    local_args = pywikibot.handle_args(*args)

    # check dependencies
    for module in (isbnlib, unidecode):
        if isinstance(module, ImportError):
            raise module

    # Connect to databases
    # Login to Wikibase instance
    # Required for wikidata object access (item, property, statement)
    repo = pywikibot.Site('wikidata')
    repo.login()

    # Get language list
    main_languages = get_language_preferences()

    # Get all program parameters
    pywikibot.info(f'{pywikibot.calledModuleName()}, '
                   f'{pywikibot.__version__}, {pgmlic}, {creator}')

    # This script requires a bot flag
    wdbotflag = 'bot' in pywikibot.User(repo, repo.user()).groups()

    # Prebuilt targets
    target_author = pywikibot.ItemPage(repo, AUTHORINSTANCE)

    # Get today's date
    today = date.today()
    date_ref = pywikibot.WbTime(year=int(today.strftime('%Y')),
                                month=int(today.strftime('%m')),
                                day=int(today.strftime('%d')),
                                precision='day')

    # Get the digital library
    booklib = 'wiki'
    if local_args:
        booklib = local_args.pop(0)
        booklib = bookliblist.get(booklib, booklib)

    # Get ItemPage for digital library sources
    bib_sourcex = {seq: get_item_page(bib_source[seq][0])
                   for seq in bib_source}

    if booklib in bib_sourcex:
        # Register source
        references = pywikibot.Claim(repo, REFPROP)
        references.setTarget(bib_sourcex[booklib])

        # Set retrieval date
        retrieved = pywikibot.Claim(repo, REFDATEPROP)
        retrieved.setTarget(date_ref)
        booklib_ref = [references, retrieved]

        # Get default language from book library
        mainlang = bib_source[booklib][2]
    else:
        # Unknown bib reference - show implemented codes
        for seq in bib_source:
            pywikibot.info(
                f'{seq.ljust(10)}{bib_source[seq][2].ljust(4)}'
                f'{bib_source[seq][3].ljust(20)}{bib_source[seq][1]}'
            )
        fatal_error(3, f'Unknown Digital library ({REFPROP}) {booklib}')

    # Get optional parameters (all are optional)

    # Get the native language
    # The language code is only required when P/Q parameters are added,
    # or different from the environment LANG code
    if local_args:
        mainlang = local_args.pop(0)

    if mainlang not in main_languages:
        main_languages.insert(0, mainlang)

    pywikibot.info(
        f'Refers to Digital library: {bib_source[booklib][1]} '
        f'({REFPROP}:{bib_source[booklib][0]}), language {mainlang}'
    )

    # Get additional P/Q parameters
    while local_args:
        inpar = local_args.pop(0).upper()
        inprop = PROPRE.findall(inpar)[0]

        if ':-' in inpar:
            target[inprop] = '-'
        else:
            if ':Q' not in inpar:
                inpar = local_args.pop(0).upper()
            try:
                target[inprop] = QSUFFRE.findall(inpar)[0]
            except IndexError:
                target[inprop] = '-'
            break

    # Validate P/Q list
    proptyx = {}
    targetx = {}

    # Validate and encode the propery/instance pair
    for propty, title in target.items():
        if propty not in proptyx:
            proptyx[propty] = pywikibot.PropertyPage(repo, propty)
        if title != '-':
            targetx[propty] = get_item_page(title)
        pywikibot.info(f'Add {get_item_header(proptyx[propty].labels)}:'
                       f'{get_item_header(targetx[propty].labels)} '
                       f'({propty}:{title})')

        # Check the instance type for P/Q pairs (critical)
        if (propty in propreqinst
            and (INSTANCEPROP not in targetx[propty].claims
                 or not item_is_in_list(targetx[propty].claims[INSTANCEPROP],
                                        propreqinst[propty]))):
            pywikibot.critical(
                f'{get_item_header(targetx[propty].labels)} ({title})'
                f' is not one of instance type {propreqinst[propty]} for '
                f'statement {get_item_header(proptyx[propty].labels)} '
                f'({propty})'
            )
            sys.exit(3)

        # Verify that the target of a statement has a certain property
        # (warning)
        if (propty in propreqobjectprop
            and not item_is_in_list(targetx[propty].claims,
                                    propreqobjectprop[propty])):
            pywikibot.error(
                f'{get_item_header(targetx[propty].labels)} ({title})'
                f' does not have property {propreqobjectprop[propty]} for '
                f'statement {get_item_header(proptyx[propty].labels)} '
                f'({propty})'
            )

    # Get list of item numbers
    # Typically the Appendix list of references of e.g. a Wikipedia page
    # containing ISBN numbers
    # Extract all ISBN numbers from local args
    itemlist = sorted(arg for arg in local_args if ISBNRE.fullmatch(arg))

    for isbn_number in itemlist:  # Process the next edition
        try:
            exitstat = amend_isbn_edition(isbn_number)
        except isbnlib.dev._exceptions.ISBNLibHTTPError:
            pywikibot.exception()
        except pywikibot.exceptions.Error as e:
            pywikibot.error(e)

    sys.exit(exitstat)


if __name__ == '__main__':
    main()
