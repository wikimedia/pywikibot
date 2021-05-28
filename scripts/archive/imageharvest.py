"""
Bot for getting multiple images from an external site.

It takes a URL as an argument and finds all images (and other files specified
by the extensions in 'file_formats' that URL is referring to, asking whether to
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
import os
from urllib.parse import urljoin

import pywikibot
from pywikibot.bot import QuitKeyboardInterrupt
from pywikibot.comms.http import fetch
from pywikibot.specialbots import UploadRobot


try:
    from bs4 import BeautifulSoup
except ImportError as e:
    BeautifulSoup = e

file_formats = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.ogg')


def get_imagelinks(url, shown):
    """Given a URL, get all images linked to by the page at that URL."""
    links = []

    response = fetch(url)
    if response.status_code != 200:
        pywikibot.output('Skipping url: {}'
                         .format(url))
        return links

    soup = BeautifulSoup(response.text, 'html.parser')

    if not shown:
        tagname = 'a'
    elif shown == 'just':
        tagname = 'img'
    else:
        tagname = ['a', 'img']

    for tag in soup.findAll(tagname):
        link = tag.get('src', tag.get('href', None))
        if not link:
            continue
        _, ext = os.path.splitext(link)
        if ext.lower() in file_formats:
            links.append(urljoin(url, link))
    return links


def get_categories(site):
    """Get list of categories, if any."""
    categories = []
    while True:
        cat = pywikibot.input('Specify a category (or press enter to '
                              'end adding categories)')
        if not cat.strip():
            break
        fmt = '[[{cat}]]' if ':' in cat else '[[{ns}:{cat}]]'
        categories.append(fmt.format(ns=site.namespace(14), cat=cat))

    return categories


def run_bot(give_url, image_url, desc, shown):
    """Run the bot."""
    if not give_url and image_url:
        url = pywikibot.input('What URL range should I check '
                              '(use $ for the part that is changeable)')
        minimum = int(pywikibot.input(
            'What is the first number to check (default: 1)') or 1)
        maximum = int(pywikibot.input(
            'What is the last number to check (default: 99)') or 99)
        ilinks = (url.replace('$', str(i))
                  for i in range(minimum, maximum + 1))
    else:
        url = (give_url
               or pywikibot.input('From what URL should I get the images?'))
        ilinks = get_imagelinks(url, shown)

    basicdesc = desc or pywikibot.input(
        'What text should be added at the end of '
        'the description of each image from this url?')

    mysite = pywikibot.Site()
    for image in ilinks:
        try:
            include = pywikibot.input_yn('Include image {}?'.format(image),
                                         default=False)
        except QuitKeyboardInterrupt:
            break
        if not include:
            continue

        categories = get_categories(mysite)
        desc = pywikibot.input('Give the description of this image:')

        desc += '\n\n' + basicdesc + '\n\n' + '\n'.join(categories)
        UploadRobot(image, description=desc).run()


def main(*args):
    """Process command line arguments and invoke bot."""
    url = ''
    image_url = False
    shown = False
    desc = []

    for arg in pywikibot.handle_args(args):
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

    if isinstance(BeautifulSoup, ImportError):
        pywikibot.bot.suggest_help(missing_dependencies=['beautifulsoup4'])
    else:
        run_bot(url, image_url, desc, shown)


if __name__ == '__main__':
    main()
