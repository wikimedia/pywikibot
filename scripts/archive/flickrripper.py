#!/usr/bin/python
"""
A tool to transfer flickr photos to Wikimedia Commons.

The following parameters are supported:

 -group_id:         specify group ID of the pool
 -photoset_id:      specify a photoset id
 -user_id:          give the user id of the flickrriper user
 -start_id:         the photo id to start with
 -end_id:           the photo id to end with
 -tags:             a tag to filter photo items (only one is supported)
 -flickerreview     add a flickr review template to the description
 -reviewer:         specify the reviewer
 -override:         override text for licence
 -addcategory:      specify a category
 -removecategories  remove all categories
 -autonomous        run bot in autonomous mode
"""
#
# (C) Pywikibot team, 2009-2020
#
# Distributed under the terms of the MIT license.
#
import base64
import hashlib
import io
import re
from contextlib import suppress
from urllib.parse import urlencode

import pywikibot
from pywikibot import config, textlib
from pywikibot.comms.http import fetch
from pywikibot.specialbots import UploadRobot


try:
    from pywikibot.userinterfaces.gui import Tkdialog
except ImportError as _tk_error:
    Tkdialog = _tk_error

try:
    import flickrapi
except ImportError as e:
    flickrapi = e

# see https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.html
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
    9: True,   # Public Domain Dedication (CC0)
    10: True,  # Public Domain Mark
}


def getPhoto(flickr, photo_id):
    """
    Get the photo info and the photo sizes so we can use these later on.

    TODO: Add exception handling

    """
    while True:
        try:
            photoInfo = flickr.photos.getInfo(photo_id=photo_id)
            # xml.etree.ElementTree.dump(photoInfo)
            photoSizes = flickr.photos.getSizes(photo_id=photo_id)
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
    photo_license = photoInfo.find('photo').attrib['license']
    return flickr_allowed_license[int(photo_license)]


def getPhotoUrl(photoSizes):
    """Get the url of the jpg file with the highest resolution."""
    url = ''
    # The assumption is that the largest image is last
    for size in photoSizes.find('sizes').findall('size'):
        url = size.attrib['source']
    return url


def downloadPhoto(photoUrl):
    """
    Download the photo and store it in an io.BytesIO object.

    TODO: Add exception handling

    """
    imageFile = fetch(photoUrl).content
    return io.BytesIO(imageFile)


def findDuplicateImages(photo, site=None):
    """Find duplicate images.

    Take the photo, calculate the SHA1 hash and ask the MediaWiki api
    for a list of duplicates.

    TODO: Add exception handling.

    :param photo: Photo
    :type photo: io.BytesIO
    :param site: Site to search for duplicates.
        Defaults to using Wikimedia Commons if not supplied.
    :type site: pywikibot.site.APISite or None
    """
    if not site:
        site = pywikibot.Site('commons', 'commons')
    hashObject = hashlib.sha1()
    hashObject.update(photo.getvalue())
    return site.getFilesFromAnHash(base64.b16encode(hashObject.digest()))


def getTags(photoInfo, raw: bool = False):
    """Get all the tags on a photo.

    :param raw: use original tag name
        see https://www.flickr.com/services/api/misc.tags.html
    """
    return [tag.attrib['raw'].lower() if raw else tag.text.lower()
            for tag in photoInfo.find('photo').find('tags').findall('tag')]


def getFlinfoDescription(photo_id):
    """
    Get the description from http://wikipedia.ramselehof.de/flinfo.php

    TODO: Add exception handling, try a couple of times
    """
    parameters = urlencode({'id': photo_id, 'raw': 'on'})

    return fetch(
        'http://wikipedia.ramselehof.de/flinfo.php?{}'.format(parameters)).text


def getFilename(photoInfo, site=None, project='Flickr', photo_url=None):
    """Build a good filename for the upload based on the username and title.

    Prevents naming collisions.

    """
    if not site:
        site = pywikibot.Site('commons', 'commons')
    username = photoInfo.find('photo').find('owner').attrib['username']
    username = cleanUpTitle(username)
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
            # Use the id of the photo as last resort.
            title = photoInfo.find('photo').attrib['id']

    fileformat = photoInfo.find('photo').attrib['originalformat']
    if not fileformat and photo_url:
        _, fileformat = photo_url.rsplit('.', 1)
    filename = '{} - {} - {}.{}'.format(title, project, username, fileformat)
    i = 1
    while pywikibot.FilePage(site, filename).exists():
        filename = '{} - {} - {} ({}).{}'.format(title, project, username,
                                                 i, fileformat)
        i += 1
    return filename


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
    title = re.sub('[,|]+', ',', title)
    title = re.sub('[-,^]([.]|$)', r'\1', title)
    title = title.replace(' ', '_')
    title = title.strip('_')
    return title


def buildDescription(flinfoDescription='', flickrreview=False, reviewer='',
                     override='', addCategory='', removeCategories=False):
    """Build the final description for the image.

    The description is based on the info from flickrinfo and improved.

    """
    description = flinfoDescription
    # use template {{Taken on}}
    datetaken = re.search(r'\|Date=(.*)\n', description).group(1)
    if datetaken:
        datetaken = '{{Taken on|%s}}' % (datetaken)
        description = re.sub(r'\|Date=.*\n', '|Date={}\n'.format(datetaken),
                             description)
    if removeCategories:
        description = textlib.removeCategoryLinks(description,
                                                  pywikibot.Site('commons',
                                                                 'commons'))
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
    elif flickrreview and reviewer:
        description = description.replace(
            '{{flickrreview}}',
            '{{flickrreview|%s|'
            '{{subst:CURRENTYEAR}}-{{subst:CURRENTMONTH}}-'
            '{{subst:CURRENTDAY2}}}}' % reviewer)

    if '{{subst:unc}}' not in description:
        # Request category check
        description += '\n{{subst:chc}}\n'
    if addCategory:
        description = description.replace('{{subst:unc}}\n', '')
        description += '\n[[Category:{}]]\n'.format(addCategory)
    description = description.replace('\r\n', '\n')
    return description


def processPhoto(flickr, photo_id='', flickrreview=False, reviewer='',
                 override='', addCategory='', removeCategories=False,
                 autonomous=False):
    """Process a single Flickr photo.

    For each image:
      * Check the license
      * Check if it isn't already on Commons
      * Build suggested filename
        * Check for name collision and maybe alter it
      * Pull description from Flinfo
      * Show image and description to user
        * Add a nice hotcat lookalike for the adding of categories
        * Filter the categories
      * Upload the image
    """
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
            filename = getFilename(photoInfo, photo_url=photoUrl)
            flinfoDescription = getFlinfoDescription(photo_id)
            if 'Blacklisted user' in flinfoDescription:
                pywikibot.warning('Blacklisted user found:\n'
                                  + flinfoDescription)
                return 0

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
                                  use_filename=newFilename,
                                  keep_filename=True,
                                  verify_description=False)
                bot.upload_file()
                return 1
    else:
        pywikibot.output('Invalid license')
    return 0


def getPhotos(flickr, user_id='', group_id='', photoset_id='',
              start_id='', end_id='', tags=''):
    """Loop over a set of Flickr photos.

    Get a set to work on (start with just a username).
      * Make it possible to delimit the set (from/to)
    """
    found_start_id = not start_id

    # https://www.flickr.com/services/api/flickr.groups.pools.getPhotos.html
    # Get the photos in a group
    if group_id:
        # First get the total number of photo's in the group
        photos = flickr.groups_pools_getPhotos(group_id=group_id,
                                               user_id=user_id, tags=tags,
                                               per_page='100', page='1')
        pages = photos.find('photos').attrib['pages']

        def gen(i):
            return list(flickr.groups_pools_getPhotos(
                group_id=group_id, user_id=user_id, tags=tags,
                per_page='100', page=i
            ).find('photos'))
    # https://www.flickr.com/services/api/flickr.photosets.getPhotos.html
    # Get the photos in a photoset
    elif photoset_id:
        photos = flickr.photosets_getPhotos(photoset_id=photoset_id,
                                            per_page='100', page='1')
        pages = photos.find('photoset').attrib['pages']

        def gen(i):
            return list(flickr.photosets_getPhotos(
                photoset_id=photoset_id, per_page='100', page=i
            ).find('photoset'))
    # https://www.flickr.com/services/api/flickr.people.getPublicPhotos.html
    # Get the (public) photos uploaded by a user
    elif user_id:
        photos = flickr.people_getPublicPhotos(user_id=user_id,
                                               per_page='100', page='1')
        pages = photos.find('photos').attrib['pages']

        def gen(i):
            return list(flickr.people_getPublicPhotos(
                user_id=user_id, per_page='100', page=i
            ).find('photos'))
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
                        yield photo.attrib['id']
            except flickrapi.exceptions.FlickrError:
                gotPhotos = False
                pywikibot.output('Flickr api problem, sleeping')
                pywikibot.sleep(30)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    group_id = ''
    photoset_id = ''
    user_id = ''
    start_id = ''
    end_id = ''
    tags = ''
    addCategory = ''
    removeCategories = False
    autonomous = False
    override = ''  # override license text

    # Do we mark the images as reviewed right away?
    flickrreview = config.flickr['review']

    # Set the Flickr reviewer
    reviewer = config.flickr['reviewer']
    if not reviewer:
        with suppress(KeyError):
            reviewer = config.usernames['commons']['commons']

    local_args = pywikibot.handle_args(args)
    for local_arg in local_args:
        if not local_arg.startswith('-'):
            continue
        arg, _, value = local_arg[1:].partition(':')
        if arg == 'group_id':
            group_id = value or pywikibot.input(
                'What is the group_id of the pool?')
        elif arg == 'photoset_id':
            photoset_id = value or pywikibot.input('What is the photoset_id?')
        elif arg == 'user_id':
            user_id = value or pywikibot.input(
                'What is the user_id of the flickr user?')
        elif arg == 'start_id':
            start_id = value or pywikibot.input(
                'What is the id of the photo you want to start at?')
        elif arg == 'end_id':
            end_id = value or pywikibot.input(
                'What is the id of the photo you want to end at?')
        elif arg == 'tags':
            tags = value or pywikibot.input(
                'What is the tag you want to filter out (currently only '
                'one supported)?')
        elif arg == 'flickrreview':
            flickrreview = True
        elif arg == 'reviewer':
            reviewer = value or pywikibot.input('Who is the reviewer?')
        elif arg == 'override':
            override = value or pywikibot.input('What is the override text?')
        elif arg == 'addcategory':
            addCategory = value or pywikibot.input(
                'What category do you want to add?')
        elif arg == 'removecategories':
            removeCategories = True
        elif arg == 'autonomous':
            autonomous = True

    # check dependencies, settings and parameters
    missing_dependencies = None
    if isinstance(flickrapi, ImportError):
        missing_dependencies = ('flickrapi',)

    additional_text = None
    if not config.flickr['api_key']:
        additional_text = (
            'Flickr api key not found! Get yourself an api key\n'
            'Any flickr user can get a key at\n'
            'https://www.flickr.com/services/api/keys/apply/')

    missing_parameters = []
    if not (user_id or group_id or photoset_id):
        missing_parameters = ['user_id', 'group_id', 'photoset_id']

    if pywikibot.bot.suggest_help(additional_text=additional_text,
                                  missing_parameters=missing_parameters,
                                  missing_dependencies=missing_dependencies):
        return

    if config.flickr['api_secret']:
        flickr = flickrapi.FlickrAPI(config.flickr['api_key'],
                                     config.flickr['api_secret'])
    else:
        pywikibot.output('Accessing public content only')
        flickr = flickrapi.FlickrAPI(config.flickr['api_key'])

    totalPhotos = 0
    uploadedPhotos = 0
    for photo_id in getPhotos(flickr, user_id, group_id, photoset_id,
                              start_id, end_id, tags):
        uploadedPhotos += processPhoto(flickr, photo_id, flickrreview,
                                       reviewer, override, addCategory,
                                       removeCategories, autonomous)
        totalPhotos += 1
    pywikibot.output('Finished running')
    pywikibot.output('Total photos: ' + str(totalPhotos))
    pywikibot.output('Uploaded photos: ' + str(uploadedPhotos))


if __name__ == '__main__':
    main()
