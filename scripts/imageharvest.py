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
# (C) Pywikibot team, 2004-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import os

try:
    from bs4 import BeautifulSoup
except ImportError as e:
    BeautifulSoup = e

import pywikibot

from pywikibot.specialbots import UploadRobot
from pywikibot.tools import PY2

if not PY2:
    import urllib
    from urllib.request import URLopener

    basestring = (str,)
else:
    from urllib import URLopener

fileformats = ('jpg', 'jpeg', 'png', 'gif', 'svg', 'ogg')


def get_imagelinks(url):
    """Given a URL, get all images linked to by the page at that URL."""
    # Check if BeautifulSoup is imported.
    if isinstance(BeautifulSoup, ImportError):
        raise BeautifulSoup

    links = []
    uo = URLopener()
    with uo.open(url) as f:
        soup = BeautifulSoup(f.read())

    if not shown:
        tagname = "a"
    elif shown == "just":
        tagname = "img"
    else:
        tagname = ["a", "img"]

    for tag in soup.findAll(tagname):
        link = tag.get("src", tag.get("href", None))
        if link:
            ext = os.path.splitext(link)[1].lower().strip('.')
            if ext in fileformats:
                links.append(urllib.basejoin(url, link))
    return links


def run_bot(give_url, image_url, desc):
    """Run the bot."""
    url = give_url
    image_url = ''
    if url == '':
        if image_url:
            url = pywikibot.input(u"What URL range should I check "
                                  u"(use $ for the part that is changeable)")
        else:
            url = pywikibot.input(u"From what URL should I get the images?")

    if image_url:
        minimum = 1
        maximum = 99
        answer = pywikibot.input(
            u"What is the first number to check (default: 1)")
        if answer:
            minimum = int(answer)
        answer = pywikibot.input(
            u"What is the last number to check (default: 99)")
        if answer:
            maximum = int(answer)

    if not desc:
        basicdesc = pywikibot.input(
            u"What text should be added at the end of "
            u"the description of each image from this url?")
    else:
        basicdesc = desc

    if image_url:
        ilinks = []
        i = minimum
        while i <= maximum:
            ilinks += [url.replace("$", str(i))]
            i += 1
    else:
        ilinks = get_imagelinks(url)

    for image in ilinks:
        if pywikibot.input_yn('Include image %s?' % image, default=False,
                              automatic_quit=False):
            desc = pywikibot.input(u"Give the description of this image:")
            categories = []
            while True:
                cat = pywikibot.input(u"Specify a category (or press enter to "
                                      u"end adding categories)")
                if not cat.strip():
                    break
                if ":" in cat:
                    categories.append(u"[[%s]]" % cat)
                else:
                    categories.append(u"[[%s:%s]]"
                                      % (mysite.namespace(14), cat))
            desc += "\r\n\r\n" + basicdesc + "\r\n\r\n" + \
                    "\r\n".join(categories)
            uploadBot = UploadRobot(image, description=desc)
            uploadBot.run()
        elif answer == 's':
            break


def main(*args):
    """Process command line arguments and invoke bot."""
    global shown
    global mysite
    url = u''
    image_url = False
    shown = False
    desc = []

    for arg in pywikibot.handle_args():
        if arg == "-pattern":
            image_url = True
        elif arg == "-shown":
            shown = True
        elif arg == "-justshown":
            shown = "just"
        elif url == u'':
            url = arg
        else:
            desc += [arg]
    desc = ' '.join(desc)

    mysite = pywikibot.Site()
    run_bot(url, image_url, desc)


if __name__ == '__main__':
    main()
