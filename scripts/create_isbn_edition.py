#!/usr/bin/env python3
r"""Pywikibot script to load ISBN related data into Wikidata.

Pywikibot script to get ISBN data from a digital library,
and create or amend the related Wikidata item for edition
(with the P212=ISBN number as unique external ID).

Use digital libraries to get ISBN data in JSON format, and integrate the
results into Wikidata.

Then the resulting item number can be used e.g. to generate Wikipedia
references using template Cite_Q.

Parameters:

    All parameters are optional:

        P1:         digital library (default goob "-")

            bnf     Catalogue General (France)
            bol     Bol.com
            dnb     Deutsche National Library
            goob    Google Books
            kb      National Library of the Netherlands
            loc     Library of Congress US
            mcues   Ministerio de Cultura (Spain)
            openl   OpenLibrary.org
            porbase urn.porbase.org Portugal
            sbn     Servizio Bibliotecario Nazionale
            wiki    wikipedia.org
            worldcat    WorldCat

        P2:         ISO 639-1 language code
                    Default LANG; e.g. en, nl, fr, de, es, it, etc.

        P3 P4...:   P/Q pairs to add additional claims (repeated)
                    e.g. P921 Q107643461 (main subject: database
                    management linked to P2163 Fast ID)

    stdin: ISBN numbers (International standard book number)

        Free text (e.g. Wikipedia references list, or publication list)
        is accepted. Identification is done via an ISBN regex expression.

**Functionality:**
    * The ISBN number is used as a primary key (P212 where no duplicates
      are allowed. The item update is not performed when there is no
      unique match
    * Statements are added or merged incrementally; existing data is not
      overwritten.
    * Authors and publishers are searched to get their item number
      (ambiguous items are skipped)
    * Book title and subtitle are separated with '.', ':', or '-'
    * This script can be run incrementally with the same parameters
      Caveat: Take into account the Wikidata Query database
      replication delay. Wait for minimum 5 minutes to avoid creating
      duplicate objects.

**Data quality:**
    * Use https://query.wikidata.org/querybuilder/ to identify P212
      duplicates. Merge duplicate items before running the script
      again.
    * The following properties should only be used for written works
      P5331:  OCLC work ID (editions should only have P243)
      P8383:  Goodreads-identificatiecode for work (editions should
      only have P2969)

Examples:

    Default library (Google Books), language (LANG), no additional
    statements:

        pwb create_isbn_edition.py 9789042925564

    Wikimedia, language Dutch, main subject: database management:

        pwb create_isbn_edition.py wiki en P921 Q107643461 978-0-596-10089-6

Standard ISBN properties:

    P31:Q3331189:   instance of edition
    P50:    author
    P123:   publisher
    P212:   canonical ISBN number (lookup via Wikidata Query)
    P407:   language of work (Qnumber linked to ISO 639-1 language code)
    P577:   date of publication (year)
    P1476:  book title
    P1680:  subtitle

Other ISBN properties:

    P291:   place of publication
    P921:   main subject (inverse lookup from external Fast ID P2163)
    P629:   work for edition
    P747:   edition of work
    P1104:  number of pages

Qualifiers:

    P1545:  (author) sequence number

External identifiers:

    P213:   ISNI ID
    P243:   OCLC ID
    P496:   ORCID iD
    P675:   Google Books-identificatiecode
    P1036:  Dewey Decimal Classification
    P2163:  Fast ID (inverse lookup via Wikidata Query) -> P921: main subject
    P2969:  Goodreads-identificatiecode

    (only for written works)
    P5331:  OCLC work ID (editions should only have P243)
    P8383:  Goodreads-identificatiecode for work (editions should only
            have P2969)

**Author:**
   Geert Van Pamel, 2022-08-04,
   GNU General Public License v3.0, User:Geertivp

**Documentation:**
    * https://en.wikipedia.org/wiki/ISBN
    * https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    * https://www.geeksforgeeks.org/searching-books-with-python/
    * https://www.freecodecamp.org/news/python-json-how-to-convert-a-string-to-json/
    * https://pypi.org/project/isbnlib/
    * https://buildmedia.readthedocs.org/media/pdf/isbnlib/v3.4.5/isbnlib.pdf
    * https://isbntools.readthedocs.io/en/latest/info.html
    * https://www.wikidata.org/wiki/Property:P212
    * https://www.wikidata.org/wiki/Wikidata:WikiProject_Books
    * WikiProject Books:  https://www.wikidata.org/wiki/Q21831105
    * https://www.wikidata.org/wiki/Wikidata:List_of_properties/work
    * https://www.wikidata.org/wiki/Template:Book_properties
    * https://www.wikidata.org/wiki/Template:Bibliographic_properties
    * http://classify.oclc.org/classify2/ClassifyDemo
    * https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData
    * https://www.wikidata.org/wiki/Help:Sources
    * https://www.wikidata.org/wiki/Q22696135
    * https://meta.wikimedia.org/wiki/Community_Wishlist_Survey_2021/Wikidata/Bibliographical_references/sources_for_wikidataitems
    * https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html
    * https://doc.wikimedia.org/pywikibot/master/
    * https://docs.python.org/3/howto/logging.html
    * https://wikitech.wikimedia.org/wiki/Portal:Toolforge
    * http://www.isbn.org/standards/home/isbn/international/hyphenation-instructions.asp
    * https://www.wikidata.org/wiki/Wikidata:Pywikibot\_-_Python_3_Tutorial/Setting_qualifiers
    * https://www.wikidata.org/wiki/Wikidata:Pywikibot\_-_Python_3_Tutorial/Setting_statements

**Prerequisites:**
    pywikibot

    Install the following ISBN lib packages:
    https://pypi.org/search/?q=isbnlib_

        pip install isbnlib (mandatory)

        (optional)
        pip install isbnlib-bol
        pip install isbnlib-bnf
        pip install isbnlib-dnb
        pip install isbnlib-kb
        pip install isbnlib-loc
        pip install isbnlib-worldcat2
        etc.

**Restrictions:**
    * Better use the ISO 639-1 language code parameter as a default
        The language code is not always available from the digital library.
    * SPARQL queries run on a replicated database
        Possible important replication delay; wait 5 minutes before retry
        -- otherwise risk for creating duplicates.

**Known problems:**
    * Unknown ISBN, e.g. 9789400012820
    * No ISBN data available for an edition either causes no output
      (goob = Google Books), or an error message (wiki, openl)
      The script is taking care of both
    * Only 6 ISBN attributes are listed by the webservice(s)
      missing are e.g.: place of publication, number of pages
    * Not all ISBN atttributes have data (authos, publisher, date of
      publication, language)
    * The script uses multiple webservice calls (script might take time,
      but it is automated)
    * Need to amend ISBN items that have no author, publisher, or other
      required data (which additional services to use?)
    * How to add still more digital libraries?
        * Does the KBR has a public ISBN service (Koninklijke
          Bibliotheek van België)?
    * Filter for work properties -- need to amend Q47461344 (written
      work) instance and P629 (edition of) + P747 (has edition)
      statements https://www.wikidata.org/wiki/Q63413107
      ['9781282557246', '9786612557248', '9781847196057', '9781847196040']
      P8383: Goodreads-identificatiecode voor work 13957943 (should
      have P2969)
      P5331: OCLC-identificatiecode voor work 793965595 (should have P243)

.. todo::
   * Add source reference (digital library instance)

**Algorithm:**
    # Get parameters
    # Validate parameters
    # Get ISBN data
    # Convert ISBN data
    # Get additional data
    # Register ISBN data into Wikidata (create or amend items or claims)

Environment:

    The python script can run on the following platforms:

        Linux client
        Google Chromebook (Linux container)
        Toolforge Portal
        PAWS

    LANG: ISO 639-1 language code


Applications:

    Generate a book reference
        Example: {{Cite Q|Q63413107}} (wp.en)
        See also:
            https://meta.wikimedia.org/wiki/WikiCite
            https://www.wikidata.org/wiki/Q21831105 (WikiCite)
            https://www.wikidata.org/wiki/Q22321052 (Cite_Q)
            https://www.mediawiki.org/wiki/Global_templates
            https://www.wikidata.org/wiki/Wikidata:WikiProject_Source_MetaData
            https://phabricator.wikimedia.org/tag/wikicite/
            https://meta.wikimedia.org/wiki/WikiCite/Shared_Citations

**Wikidata Query:**
    * List of editions about musicians: https://w.wiki/5aaz
    * List of editions having ISBN number: https://w.wiki/5akq

**Related projects:**
    * :phab:`T314942` (this script)
    * :phab:`T282719`
    * :phab:`T214802`
    * :phab:`T208134`
    * :phab:`T138911`
    * :phab:`T20814`
    * https://en.wikipedia.org/wiki/User:Citation_bot
    * https://meta.wikimedia.org/wiki/Community_Wishlist_Survey_2021/Wikidata/Bibliographical_references/sources_for_wikidataitems
    * https://zenodo.org/record/55004#.YvwO4hTP1D8

**Other systems:**
    * https://en.wikipedia.org/wiki/bibliographic_database
    * https://www.titelbank.nl/pls/ttb/f?p=103:4012:::NO::P4012_TTEL_ID:3496019&cs=19BB8084860E3314502A1F777F875FE61

.. versionadded:: 7.7
"""  # noqa: E501, W605
#
# (C) Pywikibot team, 2022-2023
#
# Distributed under the terms of the MIT license.
#
import os  # Operating system
import re  # Regular expressions (very handy!)
from itertools import islice

import pywikibot  # API interface to Wikidata
from pywikibot import pagegenerators as pg  # Wikidata Query interface
from pywikibot.backports import List
from pywikibot.config import verbose_output as verbose
from pywikibot.data import api


try:
    import isbnlib
except ImportError as e:
    isbnlib = e

try:
    from unidecode import unidecode
except ImportError as e:
    unidecode = e

# Initialisation
booklib = 'goob'        # Default digital library

# ISBN number: 10 or 13 digits with optional dashes (-)
ISBNRE = re.compile(r'[0-9-]{10,17}')
PROPRE = re.compile(r'P[0-9]+')             # Wikidata P-number
QSUFFRE = re.compile(r'Q[0-9]+')            # Wikidata Q-number

# Other statements are added via command line parameters
target = {
    'P31': 'Q3331189',  # Is an instance of an edition
}

# Statement property and instance validation rules
propreqinst = {
    'P50': 'Q5',  # Author requires human
    # Publisher requires publisher
    'P123': {'Q2085381', 'Q1114515', 'Q1320047'},
    # Edition language requires at least one of (living, natural) language
    'P407': {'Q34770', 'Q33742', 'Q1288568'},
}

mainlang = os.getenv('LANG', 'en')[:2]      # Default description language

# Connect to database
transcmt = '#pwb Create ISBN edition'  # Wikidata transaction comment


def is_in_list(statement_list, checklist: List[str]) -> bool:
    """Verify if statement list contains at least one item from the checklist.

    :param statement_list: Statement list
    :param checklist: List of values
    :Returns: True when match
    """
    return any(seq.getTarget().getID() in checklist for seq in statement_list)


def get_item_list(item_name: str, instance_id):
    """Get list of items by name, belonging to an instance (list).

    :param item_name: Item name (case sensitive)
    :param instance_id: Instance ID (string, set, or list)
    :Returns: Set of items (Q-numbers)
    """
    item_list = set()       # Empty set
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'type': 'item',
        'strictlanguage': False,
        # All languages are searched, but labels are in native language
        'language': mainlang,
        'search': item_name,  # Get item list from label
    }
    request = api.Request(site=repo, parameters=params)
    result = request.submit()

    if 'search' in result:
        for res in result['search']:
            item = pywikibot.ItemPage(repo, res['id'])
            item.get(get_redirect=True)
            if 'P31' in item.claims:
                for seq in item.claims['P31']:  # Loop through instances
                    # Matching instance
                    if seq.getTarget().getID() in instance_id:
                        for lang in item.labels:  # Search all languages
                            # Ignore label case and accents
                            if (unidecode(item_name.lower())
                                    == unidecode(item.labels[lang].lower())):
                                item_list.add(item.getID())  # Label math
                        for lang in item.aliases:
                            # Case sensitive for aliases
                            if item_name in item.aliases[lang]:
                                item_list.add(item.getID())  # Alias match
    return item_list


def amend_isbn_edition(isbn_number: str):  # noqa: C901
    """Amend ISBN registration.

    Amend Wikidata, by registering the ISBN-13 data via P212,
    depending on the data obtained from the digital library.

    :param isbn_number:  ISBN number (10 or 13 digits with optional hyphens)
    """
    global proptyx
    global targetx

    isbn_number = isbn_number.strip()
    if not isbn_number:
        return  # Do nothing when the ISBN number is missing

    try:
        isbn_data = isbnlib.meta(isbn_number, service=booklib)
        pywikibot.info(isbn_data)
        # {'ISBN-13': '9789042925564',
        #  'Title': 'De Leuvense Vaart - Van De Vaartkom Tot Wijgmaal. '
        #           'Aspecten Uit De Industriele Geschiedenis Van Leuven',
        #  'Authors': ['A. Cresens'],
        #  'Publisher': 'Peeters Pub & Booksellers',
        #  'Year': '2012',
        #  'Language': 'nl'}
    except Exception as error:
        # When the book is unknown the function returns
        pywikibot.error(error)
        # raise ValueError(error)
        return

    if len(isbn_data) < 6:
        pywikibot.error(
            'Unknown or incomplete digital library registration for {}'
            .format(isbn_number))
        return

    # Show the raw results
    if verbose:
        pywikibot.info()
        for i in isbn_data:
            pywikibot.info(f'{i}:\t{isbn_data[i]}')

    # Get the book language from the ISBN book reference
    booklang = mainlang         # Default language
    if isbn_data['Language']:
        booklang = isbn_data['Language'].strip()
        if booklang == 'iw':    # Obsolete codes
            booklang = 'he'
        lang_list = list(get_item_list(booklang, propreqinst['P407']))

        if not lang_list:
            pywikibot.warning('Unknown language ' + booklang)
            return

        if len(lang_list) != 1:
            pywikibot.warning('Ambiguous language ' + booklang)
            return

        target['P407'] = lang_list[0]

    # Get formatted ISBN number
    isbn_number = isbn_data['ISBN-13']  # Numeric format
    isbn_fmtd = isbnlib.mask(isbn_number)       # Canonical format
    pywikibot.info(isbn_fmtd)                    # First one

    # Get (sub)title when there is a dot
    titles = isbn_data['Title'].split('. ')          # goob is using a '.'
    if len(titles) == 1:
        titles = isbn_data['Title'].split(': ')      # Extract subtitle
    if len(titles) == 1:
        titles = isbn_data['Title'].split(' - ')     # Extract subtitle
    objectname = titles[0].strip()
    subtitle = ''
    if len(titles) > 1:
        subtitle = titles[1].strip()

    # pywikibot.info book titles
    pywikibot.debug(objectname)
    pywikibot.debug(subtitle)  # Optional

    # print subsequent subtitles, when available
    for title in islice(titles, 2, None):
        # Not stored in Wikidata...
        pywikibot.debug(title.strip())

    # Search the ISBN number in Wikidata both canonical and numeric
    # P212 should have canonical hyphenated format
    isbn_query = ("""# Get ISBN number
SELECT ?item WHERE {{
  VALUES ?isbn_number {{
    "{}"
    "{}"
  }}
  ?item wdt:P212 ?isbn_number.
}}
""".format(isbn_fmtd, isbn_number))

    pywikibot.info(isbn_query)
    generator = pg.WikidataSPARQLPageGenerator(isbn_query, site=repo)

    # Main loop for all DISTINCT items
    rescnt = 0
    for rescnt, item in enumerate(generator, start=1):
        qnumber = item.getID()
        pywikibot.warning(f'Found item: {qnumber}')

    # Create or amend the item
    if rescnt == 1:
        item.get(get_redirect=True)         # Update item
    elif not rescnt:
        label = {booklang: objectname}
        item = pywikibot.ItemPage(repo)     # Create item
        item.editEntity({'labels': label}, summary=transcmt)
        qnumber = item.getID()
        pywikibot.warning(f'Creating item: {qnumber}')
    else:
        pywikibot.critical(f'Ambiguous ISBN number {isbn_fmtd}')
        return

    # Add all P/Q values
    # Make sure that labels are known in the native language
    pywikibot.debug(target)

    # Register statements
    for propty in target:
        if propty not in item.claims:
            if propty not in proptyx:
                proptyx[propty] = pywikibot.PropertyPage(repo, propty)
            targetx[propty] = pywikibot.ItemPage(repo, target[propty])

            try:
                pywikibot.warning('Add {} ({}): {} ({})'
                                  .format(proptyx[propty].labels[booklang],
                                          propty,
                                          targetx[propty].labels[booklang],
                                          target[propty]))
            except:  # noqa: B001, E722, H201
                pywikibot.warning(f'Add {propty}:{target[propty]}')

            claim = pywikibot.Claim(repo, propty)
            claim.setTarget(targetx[propty])
            item.addClaim(claim, bot=True, summary=transcmt)

    # Set formatted ISBN number
    if 'P212' not in item.claims:
        pywikibot.warning(f'Add ISBN number (P212): {isbn_fmtd}')
        claim = pywikibot.Claim(repo, 'P212')
        claim.setTarget(isbn_fmtd)
        item.addClaim(claim, bot=True, summary=transcmt)

    # Title
    if 'P1476' not in item.claims:
        pywikibot.warning(f'Add Title (P1476): {objectname}')
        claim = pywikibot.Claim(repo, 'P1476')
        claim.setTarget(pywikibot.WbMonolingualText(text=objectname,
                                                    language=booklang))
        item.addClaim(claim, bot=True, summary=transcmt)

    # Subtitle
    if subtitle and 'P1680' not in item.claims:
        pywikibot.warning(f'Add Subtitle (P1680): {subtitle}')
        claim = pywikibot.Claim(repo, 'P1680')
        claim.setTarget(pywikibot.WbMonolingualText(text=subtitle,
                                                    language=booklang))
        item.addClaim(claim, bot=True, summary=transcmt)

    # Date of publication
    pub_year = isbn_data['Year']
    if pub_year and 'P577' not in item.claims:
        pywikibot.warning('Add Year of publication (P577): {}'
                          .format(isbn_data['Year']))
        claim = pywikibot.Claim(repo, 'P577')
        claim.setTarget(pywikibot.WbTime(year=int(pub_year), precision='year'))
        item.addClaim(claim, bot=True, summary=transcmt)

    # Get the author list
    author_cnt = 0
    for author_name in isbn_data['Authors']:
        author_name = author_name.strip()
        if author_name:
            author_cnt += 1
            author_list = list(get_item_list(author_name, propreqinst['P50']))

            if len(author_list) == 1:
                add_author = True
                if 'P50' in item.claims:
                    for seq in item.claims['P50']:
                        if seq.getTarget().getID() in author_list:
                            add_author = False
                            break

                if add_author:
                    pywikibot.warning('Add author {} (P50): {} ({})'
                                      .format(author_cnt, author_name,
                                              author_list[0]))
                    claim = pywikibot.Claim(repo, 'P50')
                    claim.setTarget(pywikibot.ItemPage(repo, author_list[0]))
                    item.addClaim(claim, bot=True, summary=transcmt)

                    qualifier = pywikibot.Claim(repo, 'P1545')
                    qualifier.setTarget(str(author_cnt))
                    claim.addQualifier(qualifier, summary=transcmt)
            elif not author_list:
                pywikibot.warning(f'Unknown author: {author_name}')
            else:
                pywikibot.warning(f'Ambiguous author: {author_name}')

    # Get the publisher
    publisher_name = isbn_data['Publisher'].strip()
    if publisher_name:
        publisher_list = list(get_item_list(publisher_name,
                                            propreqinst['P123']))

        if len(publisher_list) == 1:
            if 'P123' not in item.claims:
                pywikibot.warning('Add publisher (P123): {} ({})'
                                  .format(publisher_name, publisher_list[0]))
                claim = pywikibot.Claim(repo, 'P123')
                claim.setTarget(pywikibot.ItemPage(repo, publisher_list[0]))
                item.addClaim(claim, bot=True, summary=transcmt)
        elif not publisher_list:
            pywikibot.warning('Unknown publisher: ' + publisher_name)
        else:
            pywikibot.warning('Ambiguous publisher: ' + publisher_name)

    # Get addional data from the digital library
    isbn_cover = isbnlib.cover(isbn_number)
    isbn_editions = isbnlib.editions(isbn_number, service='merge')
    isbn_doi = isbnlib.doi(isbn_number)
    isbn_info = isbnlib.info(isbn_number)

    if verbose:
        pywikibot.info()
        pywikibot.info(isbn_info)
        pywikibot.info(isbn_doi)
        pywikibot.info(isbn_editions)

    # Book cover images
    for i in isbn_cover:
        pywikibot.info(f'{i}:\t{isbn_cover[i]}')

    # Handle ISBN classification
    isbn_classify = isbnlib.classify(isbn_number)

    for i in isbn_classify:
        pywikibot.debug(f'{i}:\t{isbn_classify[i]}')

    # ./create_isbn_edition.py '978-3-8376-5645-9' - de P407 Q188
    # Q113460204
    # {'owi': '11103651812', 'oclc': '1260160983', 'lcc': 'TK5105.8882',
    #  'ddc': '300', 'fast': {'1175035': 'Wikis (Computer science)',
    #                         '1795979': 'Wikipedia',
    #                         '1122877': 'Social sciences'}}

    # Set the OCLC ID
    if 'oclc' in isbn_classify and 'P243' not in item.claims:
        pywikibot.warning('Add OCLC ID (P243): {}'
                          .format(isbn_classify['oclc']))
        claim = pywikibot.Claim(repo, 'P243')
        claim.setTarget(isbn_classify['oclc'])
        item.addClaim(claim, bot=True, summary=transcmt)

    # OCLC ID and OCLC work ID should not be both assigned
    if 'P243' in item.claims and 'P5331' in item.claims:
        if 'P629' in item.claims:
            oclcwork = item.claims['P5331'][0]  # OCLC Work should be unique
            # Get the OCLC Work ID from the edition
            oclcworkid = oclcwork.getTarget()
            # Edition should belong to only one single work
            work = item.claims['P629'][0].getTarget()
            # There doesn't exist a moveClaim method?
            pywikibot.warning('Move OCLC Work ID {} to work {}'
                              .format(oclcworkid, work.getID()))
            # Keep current OCLC Work ID if present
            if 'P5331' not in work.claims:
                claim = pywikibot.Claim(repo, 'P5331')
                claim.setTarget(oclcworkid)
                work.addClaim(claim, bot=True, summary=transcmt)
            # OCLC Work ID does not belong to edition
            item.removeClaims(oclcwork, bot=True, summary=transcmt)
        else:
            pywikibot.error('OCLC Work ID {} conflicts with OCLC ID {} and no '
                            'work available'
                            .format(item.claims['P5331'][0].getTarget(),
                                    item.claims['P243'][0].getTarget()))

    # OCLC work ID should not be registered for editions, only for works
    if 'owi' not in isbn_classify:
        pass
    elif 'P629' in item.claims:  # Get the work related to the edition
        # Edition should only have one single work
        work = item.claims['P629'][0].getTarget()
        if 'P5331' not in work.claims:  # Assign the OCLC work ID if missing
            pywikibot.warning('Add OCLC work ID (P5331): {} to work {}'
                              .format(isbn_classify['owi'], work.getID()))
            claim = pywikibot.Claim(repo, 'P5331')
            claim.setTarget(isbn_classify['owi'])
            work.addClaim(claim, bot=True, summary=transcmt)
    elif 'P243' in item.claims:
        pywikibot.warning('OCLC Work ID {} ignored because of OCLC ID {}'
                          .format(isbn_classify['owi'],
                                  item.claims['P243'][0].getTarget()))
    # Assign the OCLC work ID only if there is no work, and no OCLC ID
    # for edition
    elif 'P5331' not in item.claims:
        pywikibot.warning('Add OCLC work ID (P5331): {} to edition'
                          .format(isbn_classify['owi']))
        claim = pywikibot.Claim(repo, 'P5331')
        claim.setTarget(isbn_classify['owi'])
        item.addClaim(claim, bot=True, summary=transcmt)

    # Reverse logic for moving OCLC ID and P212 (ISBN) from work to
    # edition is more difficult because of 1:M relationship...

    # Same logic as for OCLC (work) ID

    # Goodreads-identificatiecode (P2969)

    # Goodreads-identificatiecode for work (P8383) should not be
    # registered for editions; should rather use P2969

    # Library of Congress Classification (works and editions)
    if 'lcc' in isbn_classify and 'P8360' not in item.claims:
        pywikibot.warning(
            'Add Library of Congress Classification for edition (P8360): {}'
            .format(isbn_classify['lcc']))
        claim = pywikibot.Claim(repo, 'P8360')
        claim.setTarget(isbn_classify['lcc'])
        item.addClaim(claim, bot=True, summary=transcmt)

    # Dewey Decimale Classificatie
    if 'ddc' in isbn_classify and 'P1036' not in item.claims:
        pywikibot.warning('Add Dewey Decimale Classificatie (P1036): {}'
                          .format(isbn_classify['ddc']))
        claim = pywikibot.Claim(repo, 'P1036')
        claim.setTarget(isbn_classify['ddc'])
        item.addClaim(claim, bot=True, summary=transcmt)

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

            # Get the main subject
            main_subject_query = ("""# Search the main subject
SELECT ?item WHERE {{
  ?item wdt:P2163 "{}".
}}
""".format(fast_id))

            pywikibot.info(main_subject_query)
            generator = pg.WikidataSPARQLPageGenerator(main_subject_query,
                                                       site=repo)

            # Main loop for all DISTINCT items
            rescnt = 0
            for rescnt, main_subject in enumerate(generator, start=1):
                qmain_subject = main_subject.getID()
                try:
                    main_subject_label = main_subject.labels[booklang]
                    pywikibot.info('Found main subject {} ({}) for Fast ID {}'
                                   .format(main_subject_label, qmain_subject,
                                           fast_id))
                except:  # noqa: B001, E722, H201
                    main_subject_label = ''
                    pywikibot.info('Found main subject ({}) for Fast ID {}'
                                   .format(qmain_subject, fast_id))
                    pywikibot.error('Missing label for item {}'
                                    .format(qmain_subject))

            # Create or amend P921 statement
            if not rescnt:
                pywikibot.error('Main subject not found for Fast ID {}'
                                .format(fast_id))
            elif rescnt == 1:
                add_main_subject = True
                if 'P921' in item.claims:  # Check for duplicates
                    for seq in item.claims['P921']:
                        if seq.getTarget().getID() == qmain_subject:
                            add_main_subject = False
                            break

                if add_main_subject:
                    pywikibot.warning('Add main subject (P921) {} ({})'
                                      .format(main_subject_label,
                                              qmain_subject))
                    claim = pywikibot.Claim(repo, 'P921')
                    claim.setTarget(main_subject)
                    item.addClaim(claim, bot=True, summary=transcmt)
                else:
                    pywikibot.info('Skipping main subject {} ({})'
                                   .format(main_subject_label, qmain_subject))
            else:
                pywikibot.error('Ambiguous main subject for Fast ID {}'
                                .format(fast_id))

    # Book description
    isbn_description = isbnlib.desc(isbn_number)
    if isbn_description:
        pywikibot.info()
        pywikibot.info(isbn_description)

    # Currently does not work (service not available)
    pywikibot.warning('BibTex unavailable')
    return

    try:
        bibtex_metadata = isbnlib.doi2tex(isbn_doi)
        pywikibot.info(bibtex_metadata)
    except Exception as error:
        pywikibot.error(error)     # Data not available


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    global booklib
    global mainlang
    global repo
    global proptyx
    global targetx

    # Get optional parameters
    local_args = pywikibot.handle_args(*args)

    # Login to Wikibase instance
    # Required for wikidata object access (item, property, statement)
    repo = pywikibot.Site('wikidata')

    # Get the digital library
    if local_args:
        booklib = local_args.pop(0)
        if booklib == '-':
            booklib = 'goob'

    # Get the native language
    # The language code is only required when P/Q parameters are added,
    # or different from the LANG code
    if local_args:
        mainlang = local_args.pop(0)

    # Get additional P/Q parameters
    while local_args:
        inpar = PROPRE.findall(local_args.pop(0).upper())[0]
        target[inpar] = QSUFFRE.findall(local_args.pop(0).upper())[0]

    # Validate P/Q list
    proptyx = {}
    targetx = {}

    # Validate the propery/instance pair
    for propty in target:
        if propty not in proptyx:
            proptyx[propty] = pywikibot.PropertyPage(repo, propty)
        targetx[propty] = pywikibot.ItemPage(repo, target[propty])
        targetx[propty].get(get_redirect=True)
        if propty in propreqinst and (
            'P31' not in targetx[propty].claims
            or not is_in_list(targetx[propty].claims['P31'],
                              propreqinst[propty])):
            pywikibot.critical('{} ({}) is not a language'
                               .format(targetx[propty].labels[mainlang],
                                       target[propty]))
            return

    # check dependencies
    for module in (isbnlib, unidecode):
        if isinstance(module, ImportError):
            raise module

    # Get list of item numbers
    # Typically the Appendix list of references of e.g. a Wikipedia page
    # containing ISBN numbers
    inputfile = pywikibot.input('Get list of item numbers')
    # Extract all ISBN numbers
    itemlist = sorted(set(ISBNRE.findall(inputfile)))

    for isbn_number in itemlist:            # Process the next edition
        amend_isbn_edition(isbn_number)


if __name__ == '__main__':
    main()
