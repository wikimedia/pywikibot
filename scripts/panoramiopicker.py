#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Tool to copy a Panoramio set to Commons."""
#
# (C) Multichill, 2010
# (C) Pywikibot team, 2010-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import base64
import hashlib
import json
import re
import socket
import StringIO

from BeautifulSoup import BeautifulSoup

import pywikibot

from pywikibot import config

from pywikibot.tools import PY2

from scripts import imagerecat, upload

if not PY2:
    from urllib.request import urlopen
else:
    from urllib import urlopen

try:
    from pywikibot.userinterfaces.gui import Tkdialog
except ImportError as _tk_error:
    Tkdialog = None


def isAllowedLicense(photoInfo):
    """
    Check if the image contains the right license.

    TODO: Maybe add more licenses

    """
    allowed = [u'by-sa']
    return photoInfo[u'license'] in allowed


def downloadPhoto(photoUrl):
    """
    Download the photo and store it in a StrinIO.StringIO object.

    TODO: Add exception handling

    """
    imageFile = urlopen(photoUrl).read()
    return StringIO.StringIO(imageFile)


def findDuplicateImages(photo, site=None):
    """Return list of duplicate images.

    Takes the photo, calculates the SHA1 hash and asks the mediawiki api
    for a list of duplicates.

    TODO: Add exception handling, fix site thing

    """
    if not site:
        site = pywikibot.Site('commons', 'commons')

    hashObject = hashlib.sha1()
    hashObject.update(photo.getvalue())
    return site.allimages(sha1=base64.b16encode(hashObject.digest()))


def getLicense(photoInfo):
    """Adding license to the Panoramio API with a beautiful soup hack."""
    photoInfo['license'] = u'c'
    page = urlopen(photoInfo.get(u'photo_url'))
    data = page.read()
    soup = BeautifulSoup(data)
    if soup.find("div", {'id': 'photo-info'}):
        pointer = soup.find("div", {'id': 'photo-info'})
        if pointer.find("div", {'id': 'photo-details'}):
            pointer = pointer.find("div", {'id': 'photo-details'})
            if pointer.find("ul", {'id': 'details'}):
                pointer = pointer.find("ul", {'id': 'details'})
                if pointer.find("li", {'class': 'license by-sa'}):
                    photoInfo['license'] = u'by-sa'
                # Does Panoramio have more license options?

    return photoInfo


def getFilename(photoInfo, site=None,
                project=u'Panoramio'):
    """Build a good filename for the upload.

    The name is based on the username and the title. Prevents naming collisions.
    """
    if not site:
        site = pywikibot.Site('commons', 'commons')

    username = photoInfo.get(u'owner_name')
    title = photoInfo.get(u'photo_title')
    if title:
        title = cleanUpTitle(title)
    else:
        title = u''

    if pywikibot.Page(site, u'File:%s - %s - %s.jpg'
                      % (project, username, title)).exists():
        i = 1
        while True:
            if (pywikibot.Page(site, u'File:%s - %s - %s (%s).jpg'
                               % (project, username, title, str(i))).exists()):
                i += 1
            else:
                return u'%s - %s - %s (%s).jpg' % (project, username, title,
                                                   str(i))
    else:
        return u'%s - %s - %s.jpg' % (project, username, title)


def cleanUpTitle(title):
    """Clean up the title of a potential mediawiki page.

    Otherwise the title of the page might not be allowed by the software.
    """
    title = title.strip()
    title = re.sub(u"[<{\\[]", u"(", title)
    title = re.sub(u"[>}\\]]", u")", title)
    title = re.sub(u"[ _]?\\(!\\)", u"", title)
    title = re.sub(u",:[ _]", u", ", title)
    title = re.sub(u"[;:][ _]", u", ", title)
    title = re.sub(u"[\t\n ]+", u" ", title)
    title = re.sub(u"[\r\n ]+", u" ", title)
    title = re.sub(u"[\n]+", u"", title)
    title = re.sub(u"[?!]([.\"]|$)", u"\\1", title)
    title = re.sub(u"[&#%?!]", u"^", title)
    title = re.sub(u"[;]", u",", title)
    title = re.sub(u"[/+\\\\:]", u"-", title)
    title = re.sub(u"--+", u"-", title)
    title = re.sub(u",,+", u",", title)
    title = re.sub(u"[-,^]([.]|$)", u"\\1", title)
    title = title.replace(u" ", u"_")
    return title


def getDescription(photoInfo, panoramioreview=False, reviewer='',
                   override=u'', addCategory=u''):
    """Build description for the image."""
    desc = u''
    desc += u'{{Information\n'
    desc += u'|description=%(photo_title)s\n'
    desc += u'|date=%(upload_date)s (upload date)\n'
    desc += u'|source=[%(photo_url)s Panoramio]\n'
    desc += u'|author=[%(owner_url)s?with_photo_id=%(photo_id)s %(owner_name)s] \n'
    desc += u'|permission=\n'
    desc += u'|other_versions=\n'
    desc += u'|other_fields=\n'
    desc += u'}}\n'
    if photoInfo.get(u'latitude') and photoInfo.get(u'longitude'):
        desc += u'{{Location dec|%(latitude)s|%(longitude)s|source:Panoramio}}\n'
    desc += u'\n'
    desc += u'=={{int:license-header}}==\n'

    if override:
        desc += override
    else:
        if photoInfo.get(u'license') == u'by-sa':
            desc += u'{{Cc-by-sa-3.0}}\n'
        if panoramioreview:
            desc += ('{{Panoramioreview|%s|{{subst:CURRENTYEAR}}-'
                     '{{subst:CURRENTMONTH}}-{{subst:CURRENTDAY2}}}}\n'
                     % reviewer)
        else:
            desc += u'{{Panoramioreview}}\n'

    desc += u'\n'
    cats = u''
    if addCategory:
        desc += u'\n[[Category:%s]]\n' % (addCategory,)
        cats = True

    # Get categories based on location
    if photoInfo.get(u'latitude') and photoInfo.get(u'longitude'):
        cats = imagerecat.getOpenStreetMapCats(photoInfo.get(u'latitude'),
                                               photoInfo.get(u'longitude'))
        cats = imagerecat.applyAllFilters(cats)
        for cat in cats:
            desc += u'[[Category:%s]]\n' % (cat,)
    if not cats:
        desc += u'{{subst:Unc}}\n'

    return desc % photoInfo


def processPhoto(photoInfo, panoramioreview=False, reviewer='',
                 override=u'', addCategory=u'', autonomous=False, site=None):
    """Process a single Panoramio photo."""
    if not site:
        site = pywikibot.Site('commons', 'commons')

    if isAllowedLicense(photoInfo) or override:
        # Should download the photo only once
        photo = downloadPhoto(photoInfo.get(u'photo_file_url'))

        # Don't upload duplicate images, should add override option
        duplicates = findDuplicateImages(photo, site=site)
        if duplicates:
            pywikibot.output(u'Found duplicate image at %s' % duplicates.pop())
        else:
            filename = getFilename(photoInfo, site=site)
            pywikibot.output(filename)
            description = getDescription(photoInfo, panoramioreview,
                                         reviewer, override, addCategory)

            pywikibot.output(description)
            if not autonomous:
                (newDescription, newFilename, skip) = Tkdialog(
                    description, photo, filename).show_dialog()
            else:
                newDescription = description
                newFilename = filename
                skip = False
#         pywikibot.output(newPhotoDescription)
#         if (pywikibot.Page(title=u'File:'+ filename,
#                            site=pywikibot.Site()).exists()):
#             # I should probably check if the hash is the same and if not upload
#             # it under a different name
#             pywikibot.output(u'File:' + filename + u' already exists!')
#         else:
            # Do the actual upload
            # Would be nice to check before I upload if the file is already at
            # Commons
            # Not that important for this program, but maybe for derived
            # programs
            if not skip:
                bot = upload.UploadRobot(photoInfo.get(u'photo_file_url'),
                                         description=newDescription,
                                         useFilename=newFilename,
                                         keepFilename=True,
                                         verifyDescription=False, site=site)
                bot.upload_image(debug=False)
                return 1
    return 0


def getPhotos(photoset=u'', start_id='', end_id='', interval=100):
    """Loop over a set of Panoramio photos."""
    i = 0
    has_more = True
    url = ('http://www.panoramio.com/map/get_panoramas.php?'
           'set=%s&from=%s&to=%s&size=original')
    while has_more:
        gotInfo = False
        maxtries = 10
        tries = 0
        while not gotInfo:
            try:
                if tries < maxtries:
                    tries += 1
                    panoramioApiPage = urlopen(url % (photoset, i, i + interval))
                    contents = panoramioApiPage.read().decode('utf-8')
                    gotInfo = True
                    i += interval
                else:
                    break
            except IOError:
                pywikibot.output(u'Got an IOError, let\'s try again')
            except socket.timeout:
                pywikibot.output(u'Got a timeout, let\'s try again')

        metadata = json.loads(contents)
        photos = metadata.get(u'photos')
        for photo in photos:
            yield photo
        has_more = metadata.get(u'has_more')
    return


def usage():
    """Print usage information.

    TODO : Need more.
    """
    pywikibot.output(
        u"Panoramiopicker is a tool to transfer Panaramio photos to Wikimedia "
        u"Commons")
    pywikibot.output(u"-set:<set_id>\n")
    return


def main(*args):
    """Process command line arguments and perform task."""
#     imagerecat.initLists()

    photoset = u''  # public (popular photos), full (all photos), user ID number
    start_id = u''
    end_id = u''
    addCategory = u''
    autonomous = False
    totalPhotos = 0
    uploadedPhotos = 0

    # Do we mark the images as reviewed right away?
    if config.panoramio['review']:
        panoramioreview = config.panoramio['review']
    else:
        panoramioreview = False

    # Set the Panoramio reviewer
    if config.panoramio['reviewer']:
        reviewer = config.panoramio['reviewer']
    elif 'commons' in config.sysopnames['commons']:
        reviewer = config.sysopnames['commons']['commons']
    elif 'commons' in config.usernames['commons']:
        reviewer = config.usernames['commons']['commons']
    else:
        reviewer = u''

    # Should be renamed to overrideLicense or something like that
    override = u''
    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        if arg.startswith('-set'):
            if len(arg) == 4:
                photoset = pywikibot.input(u'What is the set?')
            else:
                photoset = arg[5:]
        elif arg.startswith('-start_id'):
            if len(arg) == 9:
                start_id = pywikibot.input(
                    u'What is the id of the photo you want to start at?')
            else:
                start_id = arg[10:]
        elif arg.startswith('-end_id'):
            if len(arg) == 7:
                end_id = pywikibot.input(
                    u'What is the id of the photo you want to end at?')
            else:
                end_id = arg[8:]
        elif arg == '-panoramioreview':
            panoramioreview = True
        elif arg.startswith('-reviewer'):
            if len(arg) == 9:
                reviewer = pywikibot.input(u'Who is the reviewer?')
            else:
                reviewer = arg[10:]
        elif arg.startswith('-override'):
            if len(arg) == 9:
                override = pywikibot.input(u'What is the override text?')
            else:
                override = arg[10:]
        elif arg.startswith('-addcategory'):
            if len(arg) == 12:
                addCategory = pywikibot.input(
                    u'What category do you want to add?')
            else:
                addCategory = arg[13:]
        elif arg == '-autonomous':
            autonomous = True

    if photoset:
        site = pywikibot.Site()
        if site != pywikibot.Site('commons', 'commons'):
            pywikibot.warning(
                'Using {0} instead of Wikimedia Commons'.format(site))

        for photoInfo in getPhotos(photoset, start_id, end_id):
            photoInfo = getLicense(photoInfo)
            # time.sleep(10)
            uploadedPhotos += processPhoto(photoInfo, panoramioreview,
                                           reviewer, override, addCategory,
                                           autonomous, site=site)
            totalPhotos += 1
    else:
        usage()
    pywikibot.output(u'Finished running')
    pywikibot.output(u'Total photos: ' + str(totalPhotos))
    pywikibot.output(u'Uploaded photos: ' + str(uploadedPhotos))

if __name__ == "__main__":
    main()
