*********************
Outdated core scripts
*********************

This list contains outdated scripts from :term:`core` banch which
aren't supported any longer. They are either archived or deleted.

Feel free to reactivate any script at any time by creating a Phabricator
task: :phab:`Recovery request
<maniphest/task/edit/form/1/?projects=pywikibot,pywikibot-scripts&title=Recover
Pywikibot%20script:%20>`

.. seealso:: :ref:`Outdated compat scripts`


capitalize\_redirects script
============================

**Bot to create capitalized redirects**

It creates redirects where the first character of the first
word is uppercase and the remaining characters and words are lowercase.


casechecker script
==================

**Bot to find all pages on the wiki with mixed latin and cyrilic alphabets**

catall script
=============

**This script shows the categories on each page and lets you change them**

For each page in the target wiki:

 - If the page contains no categories, you can specify a list of categories to
   add to the page.
 - If the page already contains one or more categories, you can specify a new
   list of categories to replace the current list of categories of the page.


commons\_link script
====================

**Include Commons template in home wiki**

This bot functions mainly in the en.wikipedia, because it
compares the names of articles and category in English
language (standard language in Commons). If the name of
an article in Commons will not be in English but with
redirect, this also functions.

create_categories script
========================

**Program to batch create categories**

The program expects a generator of category titles to be used
as suffix for creating new categories with a different base.


disambredirs script
===================

**User assisted updating redirect links on disambiguation pages**


editarticle script
==================

**Edit a Wikipedia article with your favourite editor**


flickrripper script
===================

**A tool to transfer flickr photos to Wikimedia Commons**


followlive
==========

**Periodically grab list of new articles and analyze to blank or flag them**

Script to follow new articles on the wiki and flag them
with a template or eventually blank them.


freebasemappingupload script
============================

**Script to upload the mappings of Freebase to Wikidata**

Can be easily adapted to upload other String identifiers as well.

This bot needs the dump from
https://developers.google.com/freebase/data#freebase-wikidata-mappings


imagecopy script
================

**Script to copy files from a local Wikimedia wiki to Wikimedia Commons**

It uses CommonsHelper to not leave any information out and CommonSense
to automatically categorise the file. After copying, a NowCommons
template is added to the local wiki's file. It uses a local exclusion
list to skip files with templates not allow on Wikimedia Commons. If no
categories have been found, the file will be tagged on Commons.

This bot uses a graphical interface and may not work from commandline
only environment.


imagecopy\_self script
======================

**Script to copy self published files from English Wikipedia to Commons**

This bot is based on imagecopy.py and intended to be used to empty out
https://en.wikipedia.org/wiki/Category:Self-published_work

This bot uses a graphical interface and may not work from commandline
only environment.


imageharvest script
===================

**Bot for getting multiple images from an external site**

It takes a URL as an argument and finds all images (and other files specified
by the extensions in 'file_formats' that URL is referring to, asking whether to
upload them. If further arguments are given, they are considered to be the text
that is common to the descriptions. BeautifulSoup is needed only in this case.

A second use is to get a number of images that have URLs only differing in
numbers. To do this, use the command line option "-pattern", and give the URL
with the variable part replaced by '$' (if that character occurs in the URL
itself, you will have to change the bot code, my apologies).


imagerecat script
=================

**Program to re-categorize images at commons**

The program uses read the current categories, put the categories through
some filters and adds the result.


imageuncat script
=================

**Program to add uncat template to images without categories at commons**

See :ref:`imagerecat script` to add these images to categories.

This script is working on the given site, so if the commons should be handled,
the site commons should be given and not a Wikipedia or similar.

isbn script
===========

**This script reports and fixes invalid ISBN numbers**

Additionally, it can convert all ISBN-10 codes to the ISBN-13 format, and
correct the ISBN format by placing hyphens.


lonelypages script
==================

**This is a script written to add the template "orphan" to pages**


makecat script
==============

**Bot to add new or existing categories to pages**

This bot takes as its argument the name of a new or existing category.
Multiple categories may be given. It will then try to find new articles
for these categories (pages linked to and from pages already in the category),
asking the user which pages to include and which not.


match\_images script
====================

**Program to match two images based on histograms**


ndashredir script
=================

**A script to create hyphenated redirects for n or m dash pages**

This script collects pages with n or m dash in their title and creates
a redirect from the corresponding hyphenated version. If the redirect
already exists, it is skipped.

Use -reversed option to create n dash redirects for hyphenated pages.
Some communities can decide to use hyphenated titles for templates, modules
or categories and in this case this option can be handy.


piper script
============

**This bot uses external filtering programs for munging text**


selflink script
===============

**This bot searches for selflinks and allows removing them**


spamremove script
=================

**Script to remove links that are being or have been spammed**


standardize\_interwiki script
=============================

**Loop over all pages in the home wiki, standardizing the interwiki links**


states\_redirect script
=======================

**Create country sub-division redirect pages**

Check if they are in the form `Something, State`, and if so, create a redirect
from `Something, ST`.


surnames\_redirects script
==========================

**Bot to create redirects based on name order**

By default it creates a "Surnames, Given Names" redirect
version of a given page where title consists of 2 or 3 titlecased words.


table2wiki script
=================

**Nifty script to convert HTML-tables to MediaWiki's own syntax**


unlink script
=============

**This bot unlinks a page on every page that links to it**


wikisourcetext script
=====================

**This bot applies to Wikisource sites to upload text**

Text is uploaded to pages in Page ns, for a specified Index.
Text to be stored, if the page is not-existing, is preloaded from the file used
to create the Index page, making the upload feature independent from the format
of the file, as long as it is supported by the MW ProofreadPage extension.

As alternative, if '-ocr' option is selected,
OCR tool will be used to get text.
In this case, also already existing pages with quality value 'Not Proofread'
can be treated. '-force' will override existing page in this case.

