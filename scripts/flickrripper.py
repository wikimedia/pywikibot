#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Tool to copy a flickr stream to Commons.

# Get a set to work on (start with just a username).
  * Make it possible to delimit the set (from/to)
# For each image
  * Check the license
  * Check if it isn't already on Commons
  * Build suggested filename
    * Check for name collision and maybe alter it
  * Pull description from Flinfo
  * Show image and description to user
    * Add a nice hotcat lookalike for the adding of categories
    * Filter the categories
  * Upload the image

Todo
----
* Check if the image is already uploaded (SHA hash)
* Check and prevent filename collisions
  * Initial suggestion
  * User input
* Filter the categories
"""
#
# (C) Multichill, 2009
# (C) Pywikibot team, 2009-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import base64
import hashlib
import io
import re
import sys

import pywikibot
from pywikibot import config, textlib
from pywikibot.comms.http import fetch
from pywikibot.specialbots import UploadRobot

try:
    from pywikibot.userinterfaces.gui import Tkdialog
except ImportError as _tk_error:
    Tkdialog = _tk_error

if sys.version_info[0] > 2:
    from urllib.parse import urlencode
else:
    from urllib import urlencode

try:
    import flickrapi                # see: http://stuvel.eu/projects/flickrapi
except ImportError as e:
    print('This script requires the python flickrapi module. \n'
          'See: http://stuvel.eu/projects/flickrapi')
    print(e)
    sys.exit(1)


flickr_allowed_license = {
    0: False,  # All Rights Reserved
    1: False,  # Creative Commons Attribution-NonCommercial-ShareAlike License
    2: False,  # Creative Commons Attribution-NonCommercial License
    3: False,  # Creative Commons Attribution-NonCommercial-NoDerivs License
    4: True,   # Creative Commons Attribution License
    5: True,   # Creative Commons Attribution-ShareAlike License
    6: False,  # Creative Commons Attribution-NoDerivs License
    7: True,   # No known copyright restrictions
    8: True,   # United States Government Work
}


def getPhoto(flickr, photo_id):
    """
    Get the photo info and the photo sizes so we can use these later on.

    TODO: Add exception handling

    """
    while True:
        try:
            photoInfo = flickr.photos_getInfo(photo_id=photo_id)
            # xml.etree.ElementTree.dump(photoInfo)
            photoSizes = flickr.photos_getSizes(photo_id=photo_id)
            # xml.etree.ElementTree.dump(photoSizes)
            return photoInfo, photoSizes
        except flickrapi.exceptions.FlickrError:
            pywikibot.output('Flickr api problem, sleeping')
            pywikibot.sleep(30)


def isAllowedLicense(photoInfo):
    """
    Check if the image contains the right license.

    TODO: Maybe add more licenses
    """
    license = photoInfo.find('photo').attrib['license']
    if flickr_allowed_license[int(license)]:
        return True
    else:
        return False


def getPhotoUrl(photoSizes):
    """Get the url of the jpg file with the highest resolution."""
    url = ''
    # The assumption is that the largest image is last
    for size in photoSizes.find('sizes').findall('size'):
        url = size.attrib['source']
    return url


def downloadPhoto(photoUrl):
    """
    Download the photo and store it in a io.BytesIO object.

    TODO: Add exception handling

    """
    imageFile = fetch(photoUrl).raw
    return io.BytesIO(imageFile)


def findDuplicateImages(photo, site=None):
    """Find duplicate images.

    Take the photo, calculate the SHA1 hash and ask the MediaWiki api
    for a list of duplicates.

    TODO: Add exception handling.

    @param photo: Photo
    @type photo: io.BytesIO
    @param site: Site to search for duplicates.
        Defaults to using Wikimedia Commons if not supplied.
    @type site: APISite or None
    """
    if not site:
        site = pywikibot.Site('commons', 'commons')
    hashObject = hashlib.sha1()
    hashObject.update(photo.getvalue())
    return site.getFilesFromAnHash(base64.b16encode(hashObject.digest()))


def getTags(photoInfo):
    """Get all the tags on a photo."""
    result = []
    for tag in photoInfo.find('photo').find('tags').findall('tag'):
        result.append(tag.text.lower())

    return result


def getFlinfoDescription(photo_id):
    """
    Get the description from http://wikipedia.ramselehof.de/flinfo.php.

    TODO: Add exception handling, try a couple of times
    """
    parameters = urlencode({'id': photo_id, 'raw': 'on'})

    return fetch(
        'http://wikipedia.ramselehof.de/flinfo.php?%s' % parameters).text


def getFilename(photoInfo, site=None, project='Flickr'):
    """Build a good filename for the upload based on the username and title.

    Prevents naming collisions.

    """
    if not site:
        site = pywikibot.Site('commons', 'commons')
    username = photoInfo.find('photo').find('owner').attrib['username']
    title = photoInfo.find('photo').find('title').text
    if title:
        title = cleanUpTitle(title)

    if not title:
        # find the max length for a mw title
        maxBytes = 240 - len(project.encode('utf-8')) \
                       - len(username.encode('utf-8'))
        description = photoInfo.find('photo').find('description').text
        if description:
            descBytes = len(description.encode('utf-8'))
            if descBytes > maxBytes:
                # maybe we cut more than needed, anyway we do it
                items = max(min(len(description), maxBytes // 4),
                            len(description) - descBytes + maxBytes)
                description = description[:items]
            title = cleanUpTitle(description)
        else:
            title = ''
            # Should probably have the id of the photo as last resort.

    if pywikibot.Page(site, 'File:%s - %s - %s.jpg'
                      % (title, project, username)).exists():
        i = 1
        while True:
            name = '%s - %s - %s (%d).jpg' % (title, project, username, i)
            if pywikibot.Page(site, 'File:' + name).exists():
                i += 1
            else:
                return name
    else:
        return '{} - {} - {}.jpg'.format(title, project, username)


def cleanUpTitle(title):
    """Clean up the title of a potential MediaWiki page.

    Otherwise the title of the page might not be allowed by the software.

    """
    title = title.strip()
    title = re.sub(r'[<{\[]', '(', title)
    title = re.sub(r'[>}\]]', ')', title)
    title = re.sub(r'[ _]?\(!\)', '', title)
    title = re.sub(',:[ _]', ', ', title)
    title = re.sub('[;:][ _]', ', ', title)
    title = re.sub(r'[\t\n ]+', ' ', title)
    title = re.sub(r'[\r\n ]+', ' ', title)
    title = re.sub('[\n]+', '', title)
    title = re.sub('[?!]([.\"]|$)', r'\1', title)
    title = re.sub('[&#%?!]', '^', title)
    title = re.sub('[;]', ',', title)
    title = re.sub(r'[/+\\:]', '-', title)
    title = re.sub('--+', '-', title)
    title = re.sub(',,+', ',', title)
    title = re.sub('[-,^]([.]|$)', r'\1', title)
    title = title.replace(' ', '_')
    title = title.strip('_')
    return title


def buildDescription(flinfoDescription='', flickrreview=False, reviewer='',
                     override='', addCategory='', removeCategories=False):
    """Build the final description for the image.

    The description is based on the info from flickrinfo and improved.

    """
    description = '== {{int:filedesc}} ==\n%s' % flinfoDescription
    if removeCategories:
        description = textlib.removeCategoryLinks(description,
                                                  pywikibot.Site(
                                                      'commons', 'commons'))
    if override:
        description = description.replace('{{cc-by-sa-2.0}}\n', '')
        description = description.replace('{{cc-by-2.0}}\n', '')
        description = description.replace('{{flickrreview}}\n', '')
        description = description.replace(
            '{{copyvio|Flickr, licensed as "All Rights Reserved" which is not '
            'a free license --~~~~}}\n',
            '')
        description = description.replace('=={{int:license}}==',
                                          '=={{int:license}}==\n' + override)
    elif flickrreview:
        if reviewer:
            description = description.replace(
                '{{flickrreview}}',
                '{{flickrreview|' + reviewer +
                '|{{subst:CURRENTYEAR}}-{{subst:CURRENTMONTH}}'
                '-{{subst:CURRENTDAY2}}}}')
    if addCategory:
        description = description.replace('{{subst:unc}}\n', '')
        description = description + '\n[[Category:' + addCategory + ']]\n'
    description = description.replace('\r\n', '\n')
    return description


def processPhoto(flickr, photo_id='', flickrreview=False, reviewer='',
                 override='', addCategory='', removeCategories=False,
                 autonomous=False):
    """Process a single Flickr photo."""
    if photo_id:
        pywikibot.output(str(photo_id))
        (photoInfo, photoSizes) = getPhoto(flickr, photo_id)
    if isAllowedLicense(photoInfo) or override:
        # Get the url of the largest photo
        photoUrl = getPhotoUrl(photoSizes)
        # Should download the photo only once
        photo = downloadPhoto(photoUrl)

        # Don't upload duplicate images, should add override option
        duplicates = findDuplicateImages(photo)
        if duplicates:
            pywikibot.output('Found duplicate image at {}'
                             .format(duplicates.pop()))
        else:
            filename = getFilename(photoInfo)
            flinfoDescription = getFlinfoDescription(photo_id)
            photoDescription = buildDescription(flinfoDescription,
                                                flickrreview, reviewer,
                                                override, addCategory,
                                                removeCategories)
            # pywikibot.output(photoDescription)
            if not isinstance(Tkdialog, ImportError) and not autonomous:
                try:
                    (newPhotoDescription, newFilename, skip) = Tkdialog(
                        photoDescription, photo, filename).show_dialog()
                except ImportError as e:
                    pywikibot.warning(e)
                    pywikibot.warning('Switching to autonomous mode.')
                    autonomous = True
            elif not autonomous:
                pywikibot.warning('Switching to autonomous mode because GUI '
                                  'interface cannot be used')
                pywikibot.warning(Tkdialog)
                autonomous = True
            if autonomous:
                newPhotoDescription = photoDescription
                newFilename = filename
                skip = False

            # Do the actual upload
            # Would be nice to check before I upload if the file is already at
            # Commons. Not that important for this program, but maybe for
            # derived programs
            if not skip:
                bot = UploadRobot(photoUrl,
                                  description=newPhotoDescription,
                                  useFilename=newFilename,
                                  keepFilename=True,
                                  verifyDescription=False)
                bot.upload_image(debug=False)
                return 1
    else:
        pywikibot.output('Invalid license')
    return 0


def getPhotos(flickr, user_id='', group_id='', photoset_id='',
              start_id='', end_id='', tags=''):
    """Loop over a set of Flickr photos."""
    found_start_id = not start_id

    # https://www.flickr.com/services/api/flickr.groups.pools.getPhotos.html
    # Get the photos in a group
    if group_id:
        # First get the total number of photo's in the group
        photos = flickr.groups_pools_getPhotos(group_id=group_id,
                                               user_id=user_id, tags=tags,
                                               per_page='100', page='1')
        pages = photos.find('photos').attrib['pages']
        gen = lambda i: flickr.groups_pools_getPhotos(  # noqa: E731
            group_id=group_id, user_id=user_id, tags=tags,
            per_page='100', page=i
        ).find('photos').getchildren()
    # https://www.flickr.com/services/api/flickr.photosets.getPhotos.html
    # Get the photos in a photoset
    elif photoset_id:
        photos = flickr.photosets_getPhotos(photoset_id=photoset_id,
                                            per_page='100', page='1')
        pages = photos.find('photoset').attrib['pages']
        gen = lambda i: flickr.photosets_getPhotos(  # noqa: E731
            photoset_id=photoset_id, per_page='100', page=i
        ).find('photoset').getchildren()
    # https://www.flickr.com/services/api/flickr.people.getPublicPhotos.html
    # Get the (public) photos uploaded by a user
    elif user_id:
        photos = flickr.people_getPublicPhotos(user_id=user_id,
                                               per_page='100', page='1')
        pages = photos.find('photos').attrib['pages']
        gen = lambda i: flickr.people_getPublicPhotos(  # noqa: E731
            user_id=user_id, per_page='100', page=i
        ).find('photos').getchildren()
    for i in range(1, int(pages) + 1):
        gotPhotos = False
        while not gotPhotos:
            try:
                for photo in gen(i):
                    gotPhotos = True
                    if photo.attrib['id'] == start_id:
                        found_start_id = True
                    if found_start_id:
                        if photo.attrib['id'] == end_id:
                            pywikibot.output('Found end_id')
                            return
                        else:
                            yield photo.attrib['id']
            except flickrapi.exceptions.FlickrError:
                gotPhotos = False
                pywikibot.output('Flickr api problem, sleeping')
                pywikibot.sleep(30)

    return


def usage():
    """
    Print usage information.

    TODO : Need more.
    """
    pywikibot.output('Flickrripper is a tool to transfer flickr photos to '
                     'Wikimedia Commons')
    pywikibot.output('-group_id:<group_id>\n')
    pywikibot.output('-photoset_id:<photoset_id>\n')
    pywikibot.output('-user_id:<user_id>\n')
    pywikibot.output('-tags:<tag>\n')
    return


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: unicode
    """
    local_args = pywikibot.handle_args(args)

    # Get the api key
    if not config.flickr['api_key']:
        pywikibot.output('Flickr api key not found! Get yourself an api key')
        pywikibot.output(
            'Any flickr user can get a key at '
            'https://www.flickr.com/services/api/keys/apply/')
        return

    if 'api_secret' in config.flickr and config.flickr['api_secret']:
        flickr = flickrapi.FlickrAPI(config.flickr['api_key'],
                                     config.flickr['api_secret'])
    else:
        pywikibot.output('Accessing public content only')
        flickr = flickrapi.FlickrAPI(config.flickr['api_key'])

    group_id = ''
    photoset_id = ''
    user_id = ''
    start_id = ''
    end_id = ''
    tags = ''
    addCategory = ''
    removeCategories = False
    autonomous = False
    totalPhotos = 0
    uploadedPhotos = 0

    # Do we mark the images as reviewed right away?
    if config.flickr['review']:
        flickrreview = config.flickr['review']
    else:
        flickrreview = False

    # Set the Flickr reviewer
    if config.flickr['reviewer']:
        reviewer = config.flickr['reviewer']
    elif 'commons' in config.sysopnames['commons']:
        pywikibot.output(config.sysopnames['commons'])
        reviewer = config.sysopnames['commons']['commons']
    elif 'commons' in config.usernames['commons']:
        reviewer = config.usernames['commons']['commons']
    else:
        reviewer = ''

    # Should be renamed to overrideLicense or something like that
    override = ''
    for arg in local_args:
        if arg.startswith('-group_id'):
            if len(arg) == 9:
                group_id = pywikibot.input('What is the group_id of the pool?')
            else:
                group_id = arg[10:]
        elif arg.startswith('-photoset_id'):
            if len(arg) == 12:
                photoset_id = pywikibot.input('What is the photoset_id?')
            else:
                photoset_id = arg[13:]
        elif arg.startswith('-user_id'):
            if len(arg) == 8:
                user_id = pywikibot.input(
                    'What is the user_id of the flickr user?')
            else:
                user_id = arg[9:]
        elif arg.startswith('-start_id'):
            if len(arg) == 9:
                start_id = pywikibot.input(
                    'What is the id of the photo you want to start at?')
            else:
                start_id = arg[10:]
        elif arg.startswith('-end_id'):
            if len(arg) == 7:
                end_id = pywikibot.input(
                    'What is the id of the photo you want to end at?')
            else:
                end_id = arg[8:]
        elif arg.startswith('-tags'):
            if len(arg) == 5:
                tags = pywikibot.input(
                    'What is the tag you want to filter out (currently only '
                    'one supported)?')
            else:
                tags = arg[6:]
        elif arg == '-flickrreview':
            flickrreview = True
        elif arg.startswith('-reviewer'):
            if len(arg) == 9:
                reviewer = pywikibot.input('Who is the reviewer?')
            else:
                reviewer = arg[10:]
        elif arg.startswith('-override'):
            if len(arg) == 9:
                override = pywikibot.input('What is the override text?')
            else:
                override = arg[10:]
        elif arg.startswith('-addcategory'):
            if len(arg) == 12:
                addCategory = pywikibot.input(
                    'What category do you want to add?')
            else:
                addCategory = arg[13:]
        elif arg == '-removecategories':
            removeCategories = True
        elif arg == '-autonomous':
            autonomous = True

    if user_id or group_id or photoset_id:
        for photo_id in getPhotos(flickr, user_id, group_id, photoset_id,
                                  start_id, end_id, tags):
            uploadedPhotos += processPhoto(flickr, photo_id, flickrreview,
                                           reviewer, override, addCategory,
                                           removeCategories, autonomous)
            totalPhotos += 1
    else:
        usage()
    pywikibot.output('Finished running')
    pywikibot.output('Total photos: ' + str(totalPhotos))
    pywikibot.output('Uploaded photos: ' + str(uploadedPhotos))


if __name__ == '__main__':
    main()
