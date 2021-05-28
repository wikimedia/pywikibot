===========================================================================
**This is a package to include robots for MediaWiki wikis like Wikipedia.**
===========================================================================

Some example robots are included.
---------------------------------

These programs can actually modify the live wiki on the net, and proper
wiki-etiquette should be followed before running it on any wiki.

To get started on proper usage of the bot framework, please refer to:

    `Manual:Pywikibot <https://www.mediawiki.org/wiki/Manual:Pywikibot>`_

The contents of the package
---------------------------

    +----------------------------------------------------------------------------------+
    | Bots and Scripts                                                                 |
    +========================+=========================================================+
    | add_text.py            | Adds text at the top or end of pages.                   |
    +------------------------+---------------------------------------------------------+
    | archivebot.py          | Archives discussion threads.                            |
    +------------------------+---------------------------------------------------------+
    | basic.py               | Is a template from which simple bots can be made.       |
    +------------------------+---------------------------------------------------------+
    | category.py            | Add a category link to all pages mentioned on a page,   |
    |                        | change or remove category tags.                         |
    +------------------------+---------------------------------------------------------+
    | category_redirect.py   | Maintain category redirects and replace links to        |
    |                        | redirected categories.                                  |
    +------------------------+---------------------------------------------------------+
    | change_pagelang.py     | Changes the content language of pages.                  |
    +------------------------+---------------------------------------------------------+
    | checkimages.py         | Check recently uploaded files. Checks if a file         |
    |                        | description is present and if there are other problems  |
    |                        | in the image's description.                             |
    +------------------------+---------------------------------------------------------+
    | claimit.py             | Adds claims to Wikidata items based on categories.      |
    +------------------------+---------------------------------------------------------+
    | clean_sandbox.py       | This bot resets a sandbox with predefined text.         |
    +------------------------+---------------------------------------------------------+
    | commonscat.py          | Adds {{commonscat}} to Wikipedia categories (or         |
    |                        | articles), if other language Wikipedia already has such |
    |                        | a template.                                             |
    +------------------------+---------------------------------------------------------+
    | commons_information.py | Insert a language template into the description field.  |
    +------------------------+---------------------------------------------------------+
    | coordinate_import.py   | Coordinate importing script.                            |
    +------------------------+---------------------------------------------------------+
    | cosmetic_changes.py    | Can do slight modifications to a wiki page source code  |
    |                        | such that the code looks cleaner.                       |
    +------------------------+---------------------------------------------------------+
    | delete.py              | This script can be used to delete pages en masse.       |
    +------------------------+---------------------------------------------------------+
    | djvutext.py            | Extracts OCR text from djvu files and uploads onto      |
    |                        | pages in the "Page" namespace on Wikisource.            |
    +------------------------+---------------------------------------------------------+
    | download_dump.py       | Downloads dumps from dumps.wikimedia.org                |
    +------------------------+---------------------------------------------------------+
    | fixing_redirects.py    | Correct all redirect links of processed pages.          |
    +------------------------+---------------------------------------------------------+
    | harvest_template.py    | Template harvesting script.                             |
    +------------------------+---------------------------------------------------------+
    | illustrate_wikidata.py | Bot to add images to Wikidata items.                    |
    +------------------------+---------------------------------------------------------+
    | image.py               | Script to replace transclusions of files                |
    +------------------------+---------------------------------------------------------+
    | imagetransfer.py       | Given a wiki page, check the interwiki links for        |
    |                        | images, and let the user choose among them for          |
    |                        | images to upload.                                       |
    +------------------------+---------------------------------------------------------+
    | interwiki.py           | A robot to check interwiki links on all pages (or       |
    |                        | a range of pages) of a wiki.                            |
    +------------------------+---------------------------------------------------------+
    | interwikidata.py       | Script to handle interwiki links based on Wikibase.     |
    +------------------------+---------------------------------------------------------+
    | listpages.py           | Print a list of pages, defined by a page generator.     |
    +------------------------+---------------------------------------------------------+
    | login.py               | Script to log the bot in to a wiki account.             |
    +------------------------+---------------------------------------------------------+
    | misspelling.py         | Similar to solve_disambiguation.py. It is supposed to   |
    |                        | fix links that contain common spelling mistakes.        |
    +------------------------+---------------------------------------------------------+
    | movepages.py           | Bot that can move pages to another title.               |
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
    +------------------------+--+------------------------------------------------------+
    | parser_function_count.py  | Find expensive templates that are subject to be      |
    |                           | converted to Lua.                                    |
    +------------------------+--+------------------------------------------------------+
    | patrol.py              | Obtains a list pages and marks the edits as patrolled   |
    |                        | based on a whitelist.                                   |
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
    | replicate_wiki.py      | Replicates pages in wiki to a second wiki within family |
    +------------------------+---------------------------------------------------------+
    | revertbot.py           | Script that can be used for reverting certain edits.    |
    +------------------------+---------------------------------------------------------+
    | shell.py               | Spawns an interactive Python shell.                     |
    +------------------------+---------------------------------------------------------+
    | solve_disambiguation.py| Interactive robot doing disambiguation.                 |
    +------------------------+---------------------------------------------------------+
    | speedy_delete.py       | Help sysops to quickly check and/or delete pages listed |
    |                        | for speedy deletion.                                    |
    +------------------------+---------------------------------------------------------+
    | template.py            | Change one template (that is {{...}}) into another.     |
    +------------------------+---------------------------------------------------------+
    | templatecount.py       | Display the list of pages transcluding a given list     |
    |                        | of templates.                                           |
    +------------------------+---------------------------------------------------------+
    | touch.py               | Bot goes over all pages of the home wiki, and edits     |
    |                        | them without changes.                                   |
    +------------------------+---------------------------------------------------------+
    | transferbot.py         | Transfers pages from a source wiki to a target wiki.    |
    +------------------------+---------------------------------------------------------+
    | unusedfiles.py         | Bot appends some text to all unused images and other    |
    |                        | text to the respective uploaders.                       |
    +------------------------+---------------------------------------------------------+
    | upload.py              | upload an image to a wiki.                              |
    +------------------------+---------------------------------------------------------+
    | version.py             | Outputs Pywikibot's revision number, Python's version   |
    |                        | and OS used.                                            |
    +------------------------+---------------------------------------------------------+
    | watchlists.py          | Allows access to the account's watchlist.               |
    +------------------------+---------------------------------------------------------+
    | weblinkchecker.py      | Check if external links are still working.              |
    +------------------------+---------------------------------------------------------+
    | welcome.py             | Script to welcome new users.                            |
    +------------------------+---------------------------------------------------------+


    +------------------------+---------------------------------------------------------+
    | archive                | Scripts no longer maintained.                           |
    |                        | Please open a Phabricator task if you want to use one.  |
    +========================+=========================================================+
    | blockpagechecker.py    | Deletes any protection templates that are on pages      |
    |                        | which aren't actually protected.                        |
    +------------------------+---------------------------------------------------------+
    | capitalize_redirects.py| Script to create a redirect of capitalize articles.     |
    +------------------------+---------------------------------------------------------+
    | casechecker.py         | Script to enumerate all pages in Wikipedia and          |
    |                        | find all titles with mixed Latin and Cyrillic           |
    |                        | alphabets.                                              |
    +------------------------+---------------------------------------------------------+
    | catall.py              | Add or change categories on a number of pages.          |
    +------------------------+---------------------------------------------------------+
    | commons_link.py        | This robot includes commons template to link Commons    |
    |                        | and your wiki project.                                  |
    +------------------------+---------------------------------------------------------+
    | create_categories.py   | Program to batch create categories.                     |
    +------------------------+---------------------------------------------------------+
    | data_ingestion.py      | A generic bot to do batch uploading to Commons.         |
    +------------------------+---------------------------------------------------------+
    | disambredir.py         | Changing redirect names in disambiguation pages.        |
    +------------------------+---------------------------------------------------------+
    | editarticle.py         | Edit a Wikipedia article with your favourite editor.    |
    +------------------------+---------------------------------------------------------+
    | flickrripper.py        | Upload images from Flickr easily.                       |
    +------------------------+---------------------------------------------------------+
    | followlive.py          | Follow new articles on a Wikipedia and flag them        |
    |                        | with a template.                                        |
    +------------------------++--------------------------------------------------------+
    | freebasemappingupload.py| Script to upload the mappings of Freebase to Wikidata. |
    +------------------------+---------------------------------------------------------+
    | imagecopy.py           | Copies images from a Wikimedia wiki to Commons.         |
    +------------------------+---------------------------------------------------------+
    | imagecopy_self.py      | Copy self published files from the English Wikipedia to |
    |                        | Commons.                                                |
    +------------------------+---------------------------------------------------------+
    | imageharvest.py        | Bot for getting multiple images from an external site.  |
    +------------------------+---------------------------------------------------------+
    | iamgerecat.py          | Try to find categories for media on Commons.            |
    +------------------------+---------------------------------------------------------+
    | imageuncat.py          | Adds uncat template to images without categories at     |
    |                        | Commons.                                                |
    +------------------------+---------------------------------------------------------+
    | isbn.py                | Bot to convert all ISBN-10 codes to the ISBN-13         |
    |                        | format.                                                 |
    +------------------------+---------------------------------------------------------+
    | lonelypages.py         | Place a template on pages which are not linked to by    |
    |                        | other pages, and are therefore lonely.                  |
    +------------------------+---------------------------------------------------------+
    | makecat.py             | Given an existing or new category, find pages for that  |
    |                        | category.                                               |
    +------------------------+---------------------------------------------------------+
    | match_images.py        | Match two images based on histograms.                   |
    +------------------------+---------------------------------------------------------+
    | ndashredir.py          | Creates hyphenated redirects to articles with n dash    |
    |                        | or m dash in their title.                               |
    +------------------------+---------------------------------------------------------+
    | piper.py               | Pipes article text through external program(s) on       |
    |                        | STDIN and collects its STDOUT which is used as the      |
    |                        | new article text if it differs from the original.       |
    +------------------------+---------------------------------------------------------+
    | protect.py             | Protect and unprotect pages en masse.                   |
    +------------------------+---------------------------------------------------------+
    | selflink.py            | This bot goes over multiple pages of the home wiki,     |
    |                        | searches for selflinks, and allows removing them.       |
    +------------------------+---------------------------------------------------------+
    | spamremove.py          | Remove links that are being or have been spammed.       |
    +------------------------+--+------------------------------------------------------+
    | standardize_interwiki.py  | A robot that downloads a page, and reformats the     |
    |                           | interwiki links in a standard way (i.e. move all     |
    |                           | of them to the bottom or the top, with the same      |
    |                           | separator, in the right order).                      |
    +------------------------+--+------------------------------------------------------+
    | states_redirect.py     | A robot to add redirects to cities for state            |
    |                        | abbreviations.                                          |
    +------------------------+---------------------------------------------------------+
    | surnames_redirects.py  | Bot to create redirects based on name order.            |
    +------------------------+---------------------------------------------------------+
    | table2wiki.py          | Semi-automatic converting HTML-tables to wiki-tables.   |
    +------------------------+---------------------------------------------------------+
    | unlink.py              | This bot unlinks a page on every page that links to it. |
    +------------------------+---------------------------------------------------------+
    | wikisourcetext.py      | This bot applies to Wikisource sites to upload text.    |
    +------------------------+---------------------------------------------------------+


    +------------------------+---------------------------------------------------------+
    | maintenance            | Framework helper scripts.                               |
    +========================+=========================================================+
    | cache.py               | Script for showing and deleting API cache.              |
    +------------------------+---------------------------------------------------------+
    | colors.py              | Utility to show pywikibot colors.                       |
    +------------------------+---------------------------------------------------------+
    | compat2core.py         | Helper script to convert compat 1.0 scripts to the core |
    |                        | 3.0 framework. Also works for newer Pywikibot releases. |
    +------------------------+---------------------------------------------------------+
    | make_i18n_dict.py      | Generate an i18n file from a given script.              |
    +------------------------+---------------------------------------------------------+
    | preload_sites.py       | Preload and cache site information for each WM family.  |
    +------------------------+---------------------------------------------------------+
    | sorting_order.py       | Updates interwiki sorting order in family.py file.      |
    +------------------------+---------------------------------------------------------+
    | update_linktrails.py   | Script that updates the linktrails in family.py file.   |
    +------------------------+---------------------------------------------------------+
    | wikimedia_sites.py     | Updates the language lists in Wikimedia family files.   |
    +------------------------+---------------------------------------------------------+


    +----------------------------------------------------------------------------------+
    | Others                                                                           |
    +========================+=========================================================+
    | i18n (folder)          | Contains i18n translations for bot edit summaries.      |
    +------------------------+---------------------------------------------------------+
    | userscripts (folder)   | Empty folder for user scripts.                          |
    +------------------------+---------------------------------------------------------+
    | README.rst             | This file (Short info of all scripts).                  |
    +------------------------+---------------------------------------------------------+

**External packages could be required with Pywikibot:**
The pwb.py wrapper scripts informs about the requirement and how to install.


More precise information, and a list of the options that are available for
the various programs, can be retrieved by running the bot with the -help
parameter, e.g.::

    python pwb.py interwiki -help
