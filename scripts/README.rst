===========================================================================
**This is a package to include robots for MediaWiki wikis like Wikipedia.**
===========================================================================

Some example robots are included.
---------------------------------

These programs can actually modify the live wiki on the net, and proper
wiki-etiquette should be followed before running it on any wiki.

To get started on proper usage of the bot framework, please refer to:

    `Manual:Pywikibot <http://www.mediawiki.org/wiki/Manual:Pywikibot>`_

NOTE : Script names with # at start are not yet present in Core rather are
       expected to be merged based on reviews and need from Compat version.

The contents of the package
---------------------------

    +----------------------------------------------------------------------------------+
    | Bots and Scripts                                                                 |
    +========================+=========================================================+
    | add_text.py            | Adds text at the top or end of pages.                   |
    +------------------------+---------------------------------------------------------+
    | basic.py               | Is a template from which simple bots can be made.       |
    +------------------------+---------------------------------------------------------+
    | blockpagechecker.py    | Deletes any protection templates that are on pages      |
    |                        | which aren't actually protected.                        |
    +------------------------+---------------------------------------------------------+
    | blockreview.py         | Bot implements blocking review process for de-wiki first|
    +------------------------+---------------------------------------------------------+
    | capitalize_redirects.py| Script to create a redirect of capitalize articles.     |
    +------------------------+---------------------------------------------------------+
    | casechecker.py         | Script to enumerate all pages in the wikipedia and      |
    |                        | find all titles with mixed Latin and Cyrillic           |
    |                        | alphabets.                                              |
    +------------------------+---------------------------------------------------------+
    | catall.py              | Add or change categories on a number of pages.          |
    +------------------------+---------------------------------------------------------+
    | category.py            | Add a category link to all pages mentioned on a page,   |
    |                        | change or remove category tags                          |
    +------------------------+---------------------------------------------------------+
    | category_redirect.py   | Maintain category redirects and replace links to        |
    |                        | redirected categories.                                  |
    +------------------------+---------------------------------------------------------+
    | #censure.py            | Bad word checker bot.                                   |
    +------------------------+---------------------------------------------------------+
    | cfd.py                 | Processes the categories for discussion working page.   |
    |                        | It parses out the actions that need to be taken as a    |
    |                        | result of CFD discussions and performs them.            |
    +------------------------+---------------------------------------------------------+
    | checkimages.py         | Check recently uploaded files. Checks if a file         |
    |                        | description is present and if there are other problems  |
    |                        | in the image's description.                             |
    +------------------------+---------------------------------------------------------+
    | claimit.py             | Adds claims to Wikidata items based on categories       |
    +------------------------+---------------------------------------------------------+
    | clean_sandbox.py       | This bot makes the cleaned of the page of tests.        |
    +------------------------+---------------------------------------------------------+
    | commons_link.py        | This robot include commons template to linking Commons  |
    |                        | and your wiki project.                                  |
    +------------------------+---------------------------------------------------------+
    | commonscat.py          | Adds {{commonscat}} to Wikipedia categories (or         |
    |                        | articles), if other language wikipedia already has such |
    |                        | a template                                              |
    +------------------------+---------------------------------------------------------+
    | #copyright.py          | This robot check copyright text in Google, Yahoo! and   |
    |                        | Live Search.                                            |
    +------------------------+---------------------------------------------------------+
    | #copyright_clean.py    | Remove reports of copyright.py on wiki pages.           |
    |                        | Uses YurikAPI.                                          |
    +------------------------+---------------------------------------------------------+
    | #copyright_put.py      | Put reports of copyright.py on wiki pages.              |
    +------------------------+---------------------------------------------------------+
    | coordinate_import.py   | Coordinate importing script.                            |
    +------------------------+---------------------------------------------------------+
    | cosmetic_changes.py    | Can do slight modifications to a wiki page source code  |
    |                        | such that the code looks cleaner.                       |
    +------------------------+---------------------------------------------------------+
    | create_categories.py   | Program to batch create categories.                     |
    +------------------------+---------------------------------------------------------+
    | data_ingestion.py      | A generic bot to do batch uploading to Commons.         |
    +------------------------+---------------------------------------------------------+
    | delete.py              | This script can be used to delete pages en masse.       |
    +------------------------+---------------------------------------------------------+
    | disambredir.py         | Changing redirect names in disambiguation pages.        |
    +------------------------+---------------------------------------------------------+
    | djvutext.py            | Extracts OCR text from djvu files and uploads onto      |
    |                        | pages in the "Page" namespace on Wikisource.            |
    +------------------------+---------------------------------------------------------+
    | editarticle.py         | Edit a Wikipedia article with your favourite editor     |
    +------------------------+---------------------------------------------------------+
    | featured.py            | A robot to check feature articles.                      |
    +------------------------+---------------------------------------------------------+
    | fixing_redirects.py    | Correct all redirect links of processed pages.          |
    +------------------------+---------------------------------------------------------+
    | flickrripper.py        | Upload images from Flickr easily.                       |
    +------------------------+---------------------------------------------------------+
    | #followlive.py         | follow new articles on a wikipedia and flag them        |
    |                        | with a template.                                        |
    +------------------------++--------------------------------------------------------+
    | freebasemappingupload.py| Docstring fixes in scripts                             |
    +------------------------++--------------------------------------------------------+
    | harvest_template.py    | [IMPROV] Reduce maximum line length to 130              |
    +------------------------+---------------------------------------------------------+
    | illustrate_wikidata.py | Dont use 'gen' to refer to the generator factory        |
    +------------------------+---------------------------------------------------------+
    | image.py               | This script can be used to change one image to another  |
    |                        | or remove an image entirely.                            |
    +------------------------+---------------------------------------------------------+
    | imagecopy.py           | Copies images from a wikimedia wiki to Commons          |
    +------------------------+---------------------------------------------------------+
    | imagecopy_self.py      | Copy self published files from the English Wikipedia to |
    |                        | Commons.                                                |
    +------------------------+---------------------------------------------------------+
    | imageharvest.py        | Bot for getting multiple images from an external site.  |
    +------------------------+---------------------------------------------------------+
    | iamgerecat.py          | Try to find categories for media on Commons.            |
    +------------------------+---------------------------------------------------------+
    | imagetransfer.py       | Given a wiki page, check the interwiki links for        |
    |                        | images, and let the user choose among them for          |
    |                        | images to upload.                                       |
    +------------------------+---------------------------------------------------------+
    | imageuncat.py          | Adds uncat template to images without categories at     |
    |                        | Commons                                                 |
    +------------------------+---------------------------------------------------------+
    | #inline_images.py      | This bot looks for images that are linked inline        |
    |                        | (i.e., they are hosted from an external server and      |
    |                        | hotlinked).                                             |
    +------------------------+---------------------------------------------------------+
    | interwiki.py           | A robot to check interwiki links on all pages (or       |
    |                        | a range of pages) of a wiki.                            |
    +------------------------+---------------------------------------------------------+
    | isbn.py                | Bot to convert all ISBN-10 codes to the ISBN-13         |
    |                        | format.                                                 |
    +------------------------+---------------------------------------------------------+
    | listpages.py           | listpages: report number of pages found                 |
    +------------------------+---------------------------------------------------------+
    | login.py               | [IMPROV] Reduce maximum line length to 130              |
    +------------------------+---------------------------------------------------------+
    | lonelypages.py         | Place a template on pages which are not linked to by    |
    |                        | other pages, and are therefore lonely                   |
    +------------------------+---------------------------------------------------------+
    | makecat.py             | Given an existing or new category, find pages for that  |
    |                        | category.                                               |
    +------------------------+---------------------------------------------------------+
    | match_images.py        | Match two images based on histograms.                   |
    +------------------------+---------------------------------------------------------+
    | misspelling.py         | Similar to solve_disambiguation.py. It is supposed to   |
    |                        | fix links that contain common spelling mistakes.        |
    +------------------------+---------------------------------------------------------+
    | movepages.py           | Bot page moves to another title.                        |
    +------------------------+---------------------------------------------------------+
    | #ndashredir.py         | Creates hyphenated redirects to articles with n dash    |
    |                        | or m dash in their title.                               |
    +------------------------+---------------------------------------------------------+
    | newitem.py             | Script creates new items on Wikidata based on criteria. |
    +------------------------+---------------------------------------------------------+
    | noreferences.py        | Searches for pages where <references /> is missing      |
    |                        | although a <ref> tag is present, and in that case adds  |
    |                        | a new references section.                               |
    +------------------------+---------------------------------------------------------+
    | nowcommons.py          | This bot can delete images with NowCommons template.    |
    +------------------------+---------------------------------------------------------+
    | pagefromfile.py        | This bot takes its input from a file that contains a    |
    |                        | number of pages to be put on the wiki.                  |
    +------------------------+---------------------------------------------------------+
    | #pageimport.py         | Import pages from a certain wiki to another.            |
    +------------------------+---------------------------------------------------------+
    | panoramiopicker.py     | Upload images from Panoramio easily.                    |
    +------------------------+---------------------------------------------------------+
    | patrol.py              | Obtains a list pages and marks the edits as patrolled   |
    |                        | based on a whitelist.                                   |
    +------------------------+---------------------------------------------------------+
    | piper.py               | Pipes article text through external program(s) on       |
    |                        | STDIN and collects its STDOUT which is used as the      |
    |                        | new article text if it differs from the original.       |
    +------------------------+---------------------------------------------------------+
    | protect.py             | Protect and unprotect pages en masse.                   |
    +------------------------+---------------------------------------------------------+
    | redirect.py            | Fix double redirects and broken redirects. Note:        |
    |                        | solve_disambiguation also has functions which treat     |
    |                        | redirects.                                              |
    +------------------------+---------------------------------------------------------+
    | reflinks.py            | Search for references which are only made of a link     |
    |                        | without title and fetch the html title from the link to |
    |                        | use it as the title of the wiki link in the reference.  |
    +------------------------+---------------------------------------------------------+
    | replace.py             | Search articles for a text and replace it by another    |
    |                        | text. Both text are set in two configurable             |
    |                        | text files. The bot can either work on a set of given   |
    |                        | pages or crawl an SQL dump.                             |
    +------------------------+---------------------------------------------------------+
    | replicate_wiki.py      | Replicates pages in wiki to a second wiki within  family|
    +------------------------+---------------------------------------------------------+
    | revertbot.py           | Revert edits.                                           |
    +------------------------+---------------------------------------------------------+
    | script_wui.py          | Fix anomalous escape (\)                                |
    +------------------------+---------------------------------------------------------+
    | selflink.py            | This bot goes over multiple pages of the home wiki,     |
    |                        | searches for selflinks, and allows removing them.       |
    +------------------------+---------------------------------------------------------+
    | shell.py               | Spawns an interactive Python shell                      |
    +------------------------+---------------------------------------------------------+
    | solve_disambiguation.py| Interactive robot doing disambiguation.                 |
    +------------------------+---------------------------------------------------------+
    | spamremove.py          | Remove links that are being or have been spammed.       |
    +------------------------+--+------------------------------------------------------+
    | standardize_interwiki.py  | A robot that downloads a page, and reformats the     |
    |                           | interwiki links in a standard way (i.e. move all     |
    |                           | of them to the bottom or the top, with the same      |
    |                           | separator, in the right order).                      |
    +------------------------+--+------------------------------------------------------+
    | states-redirect.py     | A robot to add redirects to cities for state            |
    |                        | abbreviations.                                          |
    +------------------------+---------------------------------------------------------+
    | #speedy_delete.py      | This bot load a list of pages from the category of      |
    |                        | candidates for speedy deletion and give the             |
    |                        | user an interactive prompt to decide whether            |
    |                        | each should be deleted or not.                          |
    +------------------------+---------------------------------------------------------+
    | #spellcheck.py         | This bot spellchecks wiki pages.                        |
    +------------------------+---+-----------------------------------------------------+
    | #standardize_notes.py      | Converts external links and notes/references to     |
    |                            |  : Footnote3 ref/note format.  Rewrites References. |
    +----------------------------+-----------------------------------------------------+
    | #statistics_in_wikitable.py| This bot renders statistics provided by             |
    |                            | [[Special:Statistics]] in a table on a wiki page.   |
    |                            | Thus it creates and updates a statistics wikitable. |
    +----------------------------+-----------------------------------------------------+
    | #table2wiki.py             | Semi-automatic converting HTML-tables to wiki-tables|
    +------------------------+---+-----------------------------------------------------+
    | template.py            | change one template (that is {{...}}) into another.     |
    +------------------------+---------------------------------------------------------+
    | templatecount.py       | Display the list of pages transcluding a given list     |
    |                        | of templates.                                           |
    +------------------------+---------------------------------------------------------+
    | touch.py               | Bot goes over all pages of the home wiki, and edits     |
    |                        | them without changing.                                  |
    +------------------------+---------------------------------------------------------+
    | transferbot.py         | Transfers pages from a source wiki to a target wiki     |
    +------------------------+---------------------------------------------------------+
    | unlink.py              | This bot unlinks a page on every page that links to it. |
    +------------------------+---------------------------------------------------------+
    | unusedfiles.py         | Bot appends some text to all unused images and other    |
    |                        | text to the respective uploaders.                       |
    +------------------------+---------------------------------------------------------+
    | upload.py              | upload an image to a wiki.                              |
    +------------------------+---------------------------------------------------------+
    | version.py             | Outputs Pywikibot's revision number, Python's version   |
    |                        | and OS used.                                            |
    +------------------------+---------------------------------------------------------+
    | watchlists.py          | Information retrieved by watchlist.py will be stored    |
    +------------------------+---------------------------------------------------------+
    | weblinkchecker.py      | Check if external links are still working.              |
    +------------------------+---------------------------------------------------------+
    | welcome.py             | Script to welcome new users.                            |
    +------------------------+---------------------------------------------------------+


    +-----------------------------------------------------------------------------------+
    | archive                | Scripts no longer maintained.                            |
    +========================+==========================================================+
    | archivebot.py          | Archives discussion threads.                             |
    +------------------------+----------------------------------------------------------+


    +-----------------------------------------------------------------------------------+
    | Others                                                                            |
    +========================+==========================================================+
    | i18n (folder)          | Contains i18n translations for bot edit summaries.       |
    +------------------------+----------------------------------------------------------+
    | maintenance (folder)   | Contains maintenance scripts for the developing team.    |
    +------------------------+----------------------------------------------------------+
    | README.rst             | This file (Short info of all scripts).                   |
    +------------------------+----------------------------------------------------------+

**External software can be used with Pywikibot:**
  * PyGoogle to access Google Web API and PySearch to access Yahoo! Search
    Web Services for use with copyright.py.


More precise information, and a list of the options that are available for
the various programs, can be retrieved by running the bot with the -help
parameter, e.g.

    python pwb.py interwiki.py -help
