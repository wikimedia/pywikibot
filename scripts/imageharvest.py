# -*- coding: utf-8 -*-
"""
Bot for getting multiple images from an external site.

It takes a URL as an argument and finds all images (and other files specified
by the extensions in 'fileformats') that URL is referring to, asking whether to
upload them. If further arguments are given, they are considered to be the text
that is common to the descriptions. BeautifulSoup is needed only in this case.

A second use is to get a number of images that have URLs only differing in
numbers. To do this, use the command line option "-pattern", and give the URL
with the variable part replaced by '$' (if that character occurs in the URL
itself, you will have to change the bot code, my apologies).

Other options:

-shown      Choose images shown on the page as well as linked from it
-justshown  Choose _only_ images shown on the page, not those linked
"""
#
# (C) Pywikibot team, 2004-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import os

try:
    from bs4 import BeautifulSoup
except ImportError as e:
    BeautifulSoup = e

import pywikibot

from pywikibot.bot import QuitKeyboardInterrupt
from pywikibot.comms.http import fetch
from pywikibot.specialbots import UploadRobot
from pywikibot.tools import PY2

if not PY2:
    from urllib.parse import urljoin
else:
    from urlparse import urljoin

fileformats = ('jpg', 'jpeg', 'png', 'gif', 'svg', 'ogg')


def get_imagelinks(url):
    """Given a URL, get all images linked to by the page at that URL."""
    # Check if BeautifulSoup is imported.
    if isinstance(BeautifulSoup, ImportError):
        raise BeautifulSoup

    response = fetch(url)
    if response.status_code != 200:
        pywikibot.output('Skipping url: {}'
                         .format(url))
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    if not shown:
        tagname = 'a'
    elif shown == 'just':
        tagname = 'img'
    else:
        tagname = ['a', 'img']

    links = []
    for tag in soup.findAll(tagname):
        link = tag.get('src', tag.get('href', None))
        if link:
            ext = os.path.splitext(link)[1].lower().strip('.')
            if ext in fileformats:
                links.append(urljoin(url, link))
    return links


def run_bot(give_url, image_url, desc):
    """Run the bot."""
    url = give_url
    if not url:
        if image_url:
            url = pywikibot.input('What URL range should I check '
                                  '(use $ for the part that is changeable)')
        else:
            url = pywikibot.input('From what URL should I get the images?')

    basicdesc = desc or pywikibot.input(
        'What text should be added at the end of '
        'the description of each image from this url?')

    if image_url:
        minimum = int(pywikibot.input(
            'What is the first number to check (default: 1)') or 1)
        maximum = int(pywikibot.input(
            'What is the last number to check (default: 99)') or 99)
        ilinks = (url.replace('$', str(i))
                  for i in range(minimum, maximum + 1))
    else:
        ilinks = get_imagelinks(url)

    for image in ilinks:
        try:
            include = pywikibot.input_yn('Include image {}?'.format(image),
                                         default=False)
        except QuitKeyboardInterrupt:
            break
        if not include:
            continue
        desc = pywikibot.input('Give the description of this image:')
        categories = []
        while True:
            cat = pywikibot.input('Specify a category (or press enter to '
                                  'end adding categories)')
            if not cat.strip():
                break
            if ':' in cat:
                categories.append('[[{}]]'.format(cat))
            else:
                categories.append('[[{}:{}]]'
                                  .format(mysite.namespace(14), cat))
        desc += '\n\n' + basicdesc + '\n\n' + '\n'.join(categories)
        UploadRobot(image, description=desc).run()


def main(*args):
    """Process command line arguments and invoke bot."""
    global shown
    global mysite
    url = ''
    image_url = False
    shown = False
    desc = []

    for arg in pywikibot.handle_args():
        if arg == '-pattern':
            image_url = True
        elif arg == '-shown':
            shown = True
        elif arg == '-justshown':
            shown = 'just'
        elif url == '':
            url = arg
        else:
            desc += [arg]
    desc = ' '.join(desc)

    mysite = pywikibot.Site()
    try:
        run_bot(url, image_url, desc)
    except ImportError:
        pywikibot.bot.suggest_help(missing_dependencies=('beautifulsoup4',))


if __name__ == '__main__':
    main()
