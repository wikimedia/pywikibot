***********************
Outdated compat scripts
***********************

This list contains outdated scripts from :term:`compat` banch which
haven't ported to the :term:`core` branch of Pywikibot.

Feel free to reactivate any script at any time by creating a Phabricator
task (:phab:`Porting request
<maniphest/task/edit/form/1/?projects=pywikibot,pywikibot-scripts,Pywikibot-compat-to-core&title=Port
Pywikibot%20compat%20script%20to%20core:%20>`)
or reactivate the specified task below.

.. seealso:: :ref:`Outdated core scripts`


catimages script
----------------

**Image by content categorization** (:phab:`T66838`)

Script to check uncategorized files. This script checks if a file
has some content that allows to assign it to a category.


censure script
--------------

**Bad word checker bot** (:phab:`T66839`)

It checks new content for bad words and reports it on a log page.

cfd script
----------

**This script processes the Categories for discussion working page**

It parses out the actions that need to be taken as a result of CFD
discussions (as posted to the working page by an administrator) and
performs them.


commons\_category\_redirect script
----------------------------------

**Script to clean up non-empty catecory redirect category on Commons**

Moves all images, pages and categories in redirect categories to the
target category.


copyright script
----------------

**This robot checks copyright violation** (:phab:`T66848`)

Checks for text violating copyright by looking for matches in search
engines.


copyright\_clean script
-----------------------
**Script to remove on wiki pages reports of copyright.py** (:phab:`T66848`)


copyright\_put script
---------------------
**Script to put reports of copyright.py to wiki page** (:phab:`T66848`)


deledpimage script
------------------
**Script to remove EDP images in non-article namespaces** (:phab:`T66849`)

Script hides images due to the Exemption Doctrine Policy in this way:

* `[[Image:logo.jpg]]` --> `[[:Image:logo.jpg]]`
* `[[:Image:logo.jpg]]` pass
* `Image:logo.jpg` in gallery --> `[[:Image:logo.jpg]]` in gallery end
* `logo.jpg` (like used in template) --> hide(used `<!--logo.jpg-->`)


get script
----------
**Get a page and writes its contents to standard output**

This makes it possible to pipe the text to another process.


inline\_images script
---------------------
**Try to upload images which are linked inline** (:phab:`T66870`)

This bot goes over multiple pages of the home wiki, and looks for
images that are linked inline (i.e., they are hosted from an
external server and hotlinked, instead of using the wiki's upload
function) and uploads it form url.


overcat\_simple\_filter script
------------------------------

**A bot to do some simple over categorization filtering** (:phab:`T66876`)


panoramiopicker script
----------------------
**Script to copy a Panoramio set to image repository (Commons)**


spellcheck script
-----------------
**This bot spellchecks wiki pages.** (:phab:`T236642`)

The script is checking whether a word, stripped to its 'essence' is in
a given list or not. It does not do any grammar checking or such.
For each unknown word, you get a couple of options::

    numbered options: replace by known alternatives
    a: This word is correct; add it to the list of known words
    c: The uncapitalized form of this word is correct; add it
    i: Do not edit this word, but do also not add it to the list
    p: Do not edit this word, and consider it correct for this page only
    r: Replace the word, and add the replacement as a known alternative
    s: Replace the word, but do not add the replacement
    *: Edit the page using the gui
    g: Give a list of 'guessed' words, which are similar to the given one
    x: Ignore this word, and do not check the rest of the page

When the bot is ended, it will save the extensions to its word list;
there is one word list for each language.

The bot does not rely on Latin script, but does rely on Latin punctuation.
It is therefore expected to work on for example Russian and Korean, but not
on for example Japanese.


splitwarning script
-------------------
**Splits an interwiki.log file into chunks of warnings separated by language**


standardize\_notes script
-------------------------

**This bot will standardize footnote references**


statistics\_in\_wikitable script
--------------------------------

**This bot renders siteinfo statistics in a table on a wiki page.**

Thus it creates and updates a Statistics wikitable.


subster script
--------------

**Script which will does substitutions of tags within wiki page content**

Robot which will does substitutions of tags within wiki page content with
external or other wiki text data. Like dynamic text updating.


tag\_nowcommons script
----------------------

**This script tags files available at Commons with the Nowcommons template**
(:phab:`T66159`)


warnfile script
---------------

**Script creates backlinks from a log file**

A robot to implement backlinks from an interwiki.log file without checking
them against the live wikipedia.

