#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Program to match two images based on histograms.

Usage:

    python pwb.py match_images ImageA ImageB

It is essential to provide two images to work on.

Furthermore, the following command line parameters are supported:

-otherfamily        Mentioned family with this parameter will be preferred for
                    fetching file usage details instead of the default
                    family retrieved from user-congig.py script.

-otherlang          Mentioned lang with this parameter will be preferred for
                    fetching file usage details instead of the default
                    mylang retrieved from user-congig.py script.

This is just a first version so that other people can play around with it.
Expect the code to change a lot!
"""
#
# (c) Pywikibot team, 2009-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import io

import pywikibot

from pywikibot.bot import suggest_help
from pywikibot.comms import http

try:
    from PIL import Image
except ImportError as e:
    Image = e


def match_image_pages(imagePageA, imagePageB):
    """The function expects two image page objects.

    It will return True if the image are the same and False if the images are
    not the same

    """
    imageA = get_image_from_image_page(imagePageA)
    imageB = get_image_from_image_page(imagePageB)

    (imA_width, imA_height) = imageA.size

    imageB = imageB.resize((imA_width, imA_height))

    imageA_topleft = imageA.crop((0, 0, imA_width // 2, imA_height // 2))
    imageB_topleft = imageB.crop((0, 0, imA_width // 2, imA_height // 2))

    imageA_topright = imageA.crop((imA_width // 2, 0, imA_width,
                                  imA_height // 2))
    imageB_topright = imageB.crop((imA_width // 2, 0, imA_width,
                                  imA_height // 2))

    imageA_bottomleft = imageA.crop((0, imA_height // 2, imA_width // 2,
                                     imA_height))
    imageB_bottomleft = imageB.crop((0, imA_height // 2, imA_width // 2,
                                     imA_height))

    imageA_bottomright = imageA.crop((imA_width // 2, imA_height // 2,
                                      imA_width, imA_height))
    imageB_bottomright = imageB.crop((imA_width // 2, imA_height // 2,
                                      imA_width, imA_height))

    imageA_center = imageA.crop((int(imA_width * 0.25), int(imA_height * 0.25),
                                int(imA_width * 0.75), int(imA_height * 0.75)))
    imageB_center = imageB.crop((int(imA_width * 0.25), int(imA_height * 0.25),
                                int(imA_width * 0.75), int(imA_height * 0.75)))

    wholeScore = match_images(imageA, imageB)
    topleftScore = match_images(imageA_topleft, imageB_topleft)
    toprightScore = match_images(imageA_topright, imageB_topright)
    bottomleftScore = match_images(imageA_bottomleft, imageB_bottomleft)
    bottomrightScore = match_images(imageA_bottomright, imageB_bottomright)
    centerScore = match_images(imageA_center, imageB_center)
    averageScore = (wholeScore + topleftScore + toprightScore
                    + bottomleftScore + bottomrightScore + centerScore) / 6

    pywikibot.output('Whole image           {0:>7.2%}\n'
                     'Top left of image     {1:>7.2%}\n'
                     'Top right of image    {2:>7.2%}\n'
                     'Bottom left of image  {3:>7.2%}\n'
                     'Bottom right of image {4:>7.2%}\n'
                     'Center of image       {5:>7.2%}\n'
                     '                      -------\n'
                     'Average               {6:>7.2%}'.format(
                         wholeScore, topleftScore, toprightScore,
                         bottomleftScore, bottomrightScore, centerScore,
                         averageScore))

    # Hard coded at 80%, change this later on.
    if averageScore > 0.8:
        pywikibot.output('We have a match!')
        return True
    else:
        pywikibot.output('Not the same.')
        return False


def get_image_from_image_page(imagePage):
    """Get the image object to work based on an imagePage object."""
    imageURL = imagePage.fileUrl()
    imageURLopener = http.fetch(imageURL)
    imageBuffer = io.BytesIO(imageURLopener.raw[:])
    image = Image.open(imageBuffer)
    return image


def match_images(imageA, imageB):
    """Match two image objects. Return the ratio of pixels that match."""
    histogramA = imageA.histogram()
    histogramB = imageB.histogram()

    totalMatch = 0
    totalPixels = 0

    if len(histogramA) != len(histogramB):
        return 0

    for i, hist_a in enumerate(histogramA):
        totalMatch = totalMatch + min(hist_a, histogramB[i])
        totalPixels = totalPixels + max(hist_a, histogramB[i])

    if totalPixels == 0:
        return 0

    return totalMatch / totalPixels


def main(*args):
    """Extracting file page information and initiate matching."""
    images = []
    other_family = ''
    other_lang = ''

    # Read commandline parameters.
    local_args = pywikibot.handle_args(args)

    for arg in local_args:
        if arg.startswith('-otherfamily:'):
            if len(arg) == len('-otherfamily:'):
                other_family = pywikibot.input(
                    'What family do you want to use?')
            else:
                other_family = arg[len('-otherfamily:'):]
        elif arg.startswith('-otherlang:'):
            if len(arg) == len('-otherlang:'):
                other_lang = pywikibot.input(
                    'What language do you want to use?')
            else:
                other_lang = arg[len('otherlang:'):]
        else:
            images.append(arg)

    additional_text = ('Unable to execute script because it '
                       'requires two images to work on.'
                       if len(images) != 2 else None)
    missing_dependencies = ('Pillow',) if isinstance(
        Image, ImportError) else None

    if suggest_help(missing_dependencies=missing_dependencies,
                    additional_text=additional_text):
        return

    imagePageA = pywikibot.page.FilePage(pywikibot.Site(),
                                         images[0])
    if other_lang:
        if other_family:
            imagePageB = pywikibot.page.FilePage(pywikibot.Site(
                                                 other_lang, other_family),
                                                 images[1])
        else:
            imagePageB = pywikibot.page.FilePage(pywikibot.Site(
                                                 other_lang),
                                                 images[1])
    else:
        imagePageB = pywikibot.page.FilePage(pywikibot.Site(),
                                             images[1])

    match_image_pages(imagePageA, imagePageB)


if __name__ == '__main__':
    main()
