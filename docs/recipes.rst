*******
Recipes
*******

For more recipes, see the `Pywikibot Cookbook <https://www.mediawiki.org/wiki/Manual:Pywikibot/Cookbook>`_.

How to modify a page
====================

>>> page = pywikibot.Page(pywikibot.Site(), 'Sample page')
>>> new_content = page.text.replace('this', 'that')
>>> page.put(new_content, summary='Bot: Test edit')

See :doc:`library_usage` for more advanced samples.

How to get links from summary section of page
=============================================

>>> import pywikibot
>>> from pwikibot import textlib
>>> site = pywikibot.Site('wikipedia:en')  # create a Site object
>>> page = pywikibot.Page(site, 'Deep learning')  # create a Page object
>>> sect = textlib.extract_sections(page.text, site)  # divide content into sections
>>> links = sorted(link['title'] for link in pywikibot.link_regex.finditer(sect.header))
>>> pages = [pywikibot.Page(site, title) for title in links]

* ``links`` is a list containing all link titles in alphabethical order
* ``pages`` is a sorted list containing all ``Page`` objects
