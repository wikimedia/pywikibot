#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Tool to copy a flickr stream to Commons

# Get a set to work on (start with just a username).
# * Make it possible to delimit the set (from/to)
#For each image
#*Check the license
#*Check if it isn't already on Commons
#*Build suggested filename
#**Check for name collision and maybe alter it
#*Pull description from Flinfo
#*Show image and description to user
#**Add a nice hotcat lookalike for the adding of categories
#**Filter the categories
#*Upload the image

Todo:
*Check if the image is already uploaded (SHA hash)
*Check and prevent filename collisions
**Initial suggestion
**User input
*Filter the categories
"""
#
# (C) Multichill, 2009
# (C) Pywikipedia team, 2009-2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import urllib
import re
import StringIO
import hashlib
import base64
import time
import pywikibot
from pywikibot import config
import upload

import flickrapi                  # see: http://stuvel.eu/projects/flickrapi
from Tkinter import *
from PIL import Image, ImageTk    # see: http://www.pythonware.com/products/pil/

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


def getPhoto(flickr=None, photo_id=''):
    """
    Get the photo info and the photo sizes so we can use these later on

    TODO: Add exception handling

    """
    gotPhoto = False
    while not gotPhoto:
        try:
            photoInfo = flickr.photos_getInfo(photo_id=photo_id)
            #xml.etree.ElementTree.dump(photoInfo)
            photoSizes = flickr.photos_getSizes(photo_id=photo_id)
            #xml.etree.ElementTree.dump(photoSizes)
            gotPhoto = True
        except flickrapi.exceptions.FlickrError:
            gotPhotos = False
            pywikibot.output(u'Flickr api problem, sleeping')
            time.sleep(30)
    return photoInfo, photoSizes


def isAllowedLicense(photoInfo=None):
    """
    Check if the image contains the right license

    TODO: Maybe add more licenses
    """

    license = photoInfo.find('photo').attrib['license']
    if flickr_allowed_license[int(license)]:
        return True
    else:
        return False


def getPhotoUrl(photoSizes=None):
    """
    Get the url of the jpg file with the highest resolution
    """
    url = ''
    # The assumption is that the largest image is last
    for size in photoSizes.find('sizes').findall('size'):
        url = size.attrib['source']
    return url


def downloadPhoto(photoUrl=''):
    """
    Download the photo and store it in a StrinIO.StringIO object.

    TODO: Add exception handling

    """
    imageFile = urllib.urlopen(photoUrl).read()
    return StringIO.StringIO(imageFile)


def findDuplicateImages(photo=None,
                        site=pywikibot.getSite(u'commons', u'commons')):
    """ Takes the photo, calculates the SHA1 hash and asks the mediawiki api
    for a list of duplicates.

    TODO: Add exception handling, fix site thing

    """
    hashObject = hashlib.sha1()
    hashObject.update(photo.getvalue())
    return site.getFilesFromAnHash(base64.b16encode(hashObject.digest()))


def getTags(photoInfo=None):
    """ Get all the tags on a photo """
    result = []
    for tag in photoInfo.find('photo').find('tags').findall('tag'):
        result.append(tag.text.lower())

    return result


def getFlinfoDescription(photo_id=0):
    """
    Get the description from http://wikipedia.ramselehof.de/flinfo.php

    TODO: Add exception handling, try a couple of times
    """
    parameters = urllib.urlencode({'id': photo_id, 'raw': 'on'})

    rawDescription = urllib.urlopen(
        "http://wikipedia.ramselehof.de/flinfo.php?%s" % parameters).read()

    return rawDescription.decode('utf-8')


def getFilename(photoInfo=None, site=None, project=u'Flickr'):
    """ Build a good filename for the upload based on the username and the
    title. Prevents naming collisions.

    """
    if not site:
        site = pywikibot.Site(u'commons', u'commons')
    username = photoInfo.find('photo').find('owner').attrib['username']
    title = photoInfo.find('photo').find('title').text
    if title:
        title = cleanUpTitle(title)

    if not title:
        #find the max length for a mw title
        maxBytes = 240 - len(project.encode('utf-8')) \
                       - len(username.encode('utf-8'))
        description = photoInfo.find('photo').find('description').text
        if description:
            descBytes = len(description.encode('utf-8'))
            if descBytes > maxBytes:
                # maybe we cut more than needed, anyway we do it
                items = max(min(len(description), maxBytes / 4),
                            len(description) - descBytes + maxBytes)
                description = description[:items]
            title = cleanUpTitle(description)
        else:
            title = u''
            # Should probably have the id of the photo as last resort.

    if pywikibot.Page(site, u'File:%s - %s - %s.jpg'
                      % (title, project, username)).exists():
        i = 1
        while True:
            if pywikibot.Page(site, u'File:%s - %s - %s (%d).jpg' % (title, project, username, i)).exists():
                i += 1
            else:
                return u'%s - %s - %s (%d).jpg' % (title, project, username, i)
    else:
        return u'%s - %s - %s.jpg' % (title, project, username)


def cleanUpTitle(title):
    """ Clean up the title of a potential mediawiki page. Otherwise the title of
    the page might not be allowed by the software.

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
    title = title.strip(u"_")
    return title


def buildDescription(flinfoDescription=u'', flickrreview=False, reviewer=u'',
                     override=u'', addCategory=u'', removeCategories=False):
    """ Build the final description for the image. The description is based on
    the info from flickrinfo and improved.

    """
    description = u'== {{int:filedesc}} ==\n%s' % flinfoDescription
    if removeCategories:
        description = pywikibot.removeCategoryLinks(description,
                                                    pywikibot.Site(
                                                        'commons', 'commons'))
    if override:
        description = description.replace(u'{{cc-by-sa-2.0}}\n', u'')
        description = description.replace(u'{{cc-by-2.0}}\n', u'')
        description = description.replace(u'{{flickrreview}}\n', u'')
        description = description.replace(
            u'{{copyvio|Flickr, licensed as "All Rights Reserved" which is not a free license --~~~~}}\n',
            u'')
        description = description.replace(u'=={{int:license}}==',
                                          u'=={{int:license}}==\n' + override)
    elif flickrreview:
        if reviewer:
            description = description.replace(u'{{flickrreview}}',
                                              u'{{flickrreview|' + reviewer +
                                              '|{{subst:CURRENTYEAR}}-{{subst:CURRENTMONTH}}-{{subst:CURRENTDAY2}}}}')
    if addCategory:
        description = description.replace(u'{{subst:unc}}\n', u'')
        description = description + u'\n[[Category:' + addCategory + ']]\n'
    description = description.replace(u'\r\n', u'\n')
    return description


def processPhoto(flickr=None, photo_id=u'', flickrreview=False, reviewer=u'',
                 override=u'', addCategory=u'', removeCategories=False,
                 autonomous=False):
    """ Process a single Flickr photo """
    if photo_id:
        print photo_id
        (photoInfo, photoSizes) = getPhoto(flickr, photo_id)
    if isAllowedLicense(photoInfo) or override:
        #Get the url of the largest photo
        photoUrl = getPhotoUrl(photoSizes)
        #Should download the photo only once
        photo = downloadPhoto(photoUrl)

        #Don't upload duplicate images, should add override option
        duplicates = findDuplicateImages(photo)
        if duplicates:
            pywikibot.output(u'Found duplicate image at %s' % duplicates.pop())
        else:
            filename = getFilename(photoInfo)
            flinfoDescription = getFlinfoDescription(photo_id)
            photoDescription = buildDescription(flinfoDescription,
                                                flickrreview, reviewer,
                                                override, addCategory,
                                                removeCategories)
            #pywikibot.output(photoDescription)
            if not autonomous:
                (newPhotoDescription, newFilename, skip) = Tkdialog(
                    photoDescription, photo, filename).run()
            else:
                newPhotoDescription = photoDescription
                newFilename = filename
                skip = False
        #pywikibot.output(newPhotoDescription)
        #if (pywikibot.Page(title=u'File:'+ filename, site=pywikibot.getSite()).exists()):
        # I should probably check if the hash is the same and if not upload it under a different name
        #pywikibot.output(u'File:' + filename + u' already exists!')
        #else:
            #Do the actual upload
            #Would be nice to check before I upload if the file is already at Commons
            #Not that important for this program, but maybe for derived programs
            if not skip:
                bot = upload.UploadRobot(photoUrl,
                                         description=newPhotoDescription,
                                         useFilename=newFilename,
                                         keepFilename=True,
                                         verifyDescription=False)
                bot.upload_image(debug=False)
                return 1
    else:
        pywikibot.output(u'Invalid license')
    return 0


class Tkdialog:
    """ The user dialog. """
    def __init__(self, photoDescription, photo, filename):
        self.root = Tk()
        #"%dx%d%+d%+d" % (width, height, xoffset, yoffset)
        self.root.geometry("%ix%i+10-10" % (config.tkhorsize, config.tkvertsize))

        self.root.title(filename)
        self.photoDescription = photoDescription
        self.filename = filename
        self.photo = photo
        self.skip = False
        self.exit = False

        ## Init of the widgets
        # The image
        self.image = self.getImage(self.photo, 800, 600)
        self.imagePanel = Label(self.root, image=self.image)

        self.imagePanel.image = self.image

        # The filename
        self.filenameLabel = Label(self.root, text=u"Suggested filename")
        self.filenameField = Entry(self.root, width=100)
        self.filenameField.insert(END, filename)

        # The description
        self.descriptionLabel = Label(self.root, text=u"Suggested description")
        self.descriptionScrollbar = Scrollbar(self.root, orient=VERTICAL)
        self.descriptionField = Text(self.root)
        self.descriptionField.insert(END, photoDescription)
        self.descriptionField.config(state=NORMAL, height=12, width=100, padx=0, pady=0, wrap=WORD, yscrollcommand=self.descriptionScrollbar.set)
        self.descriptionScrollbar.config(command=self.descriptionField.yview)

        # The buttons
        self.okButton = Button(self.root, text="OK", command=self.okFile)
        self.skipButton = Button(self.root, text="Skip", command=self.skipFile)

        ## Start grid

        # The image
        self.imagePanel.grid(row=0, column=0, rowspan=11, columnspan=4)

        # The buttons
        self.okButton.grid(row=11, column=1, rowspan=2)
        self.skipButton.grid(row=11, column=2, rowspan=2)

        # The filename
        self.filenameLabel.grid(row=13, column=0)
        self.filenameField.grid(row=13, column=1, columnspan=3)

        # The description
        self.descriptionLabel.grid(row=14, column=0)
        self.descriptionField.grid(row=14, column=1, columnspan=3)
        self.descriptionScrollbar.grid(row=14, column=5)

    def getImage(self, photo, width, height):
        """ Take the StringIO object and build an imageTK thumbnail """
        image = Image.open(photo)
        image.thumbnail((width, height))
        imageTk = ImageTk.PhotoImage(image)
        return imageTk

    def okFile(self):
        """ The user pressed the OK button. """
        self.filename = self.filenameField.get()
        self.photoDescription = self.descriptionField.get(0.0, END)
        self.root.destroy()

    def skipFile(self):
        """ The user pressed the Skip button. """
        self.skip = True
        self.root.destroy()

    def run(self):
        """ Activate the dialog and return the new name and if the image is
        skipped.

        """
        self.root.mainloop()
        return self.photoDescription, self.filename, self.skip


def getPhotos(flickr=None, user_id=u'', group_id=u'', photoset_id=u'',
              start_id='', end_id='', tags=u''):
    """ Loop over a set of Flickr photos. """
    result = []
    retry = False
    if not start_id:
        found_start_id = True
    else:
        found_start_id = False

    # http://www.flickr.com/services/api/flickr.groups.pools.getPhotos.html
    # Get the photos in a group
    if group_id:
        #First get the total number of photo's in the group
        photos = flickr.groups_pools_getPhotos(group_id=group_id,
                                               user_id=user_id, tags=tags,
                                               per_page='100', page='1')
        pages = photos.find('photos').attrib['pages']

        for i in range(1, int(pages) + 1):
            gotPhotos = False
            while not gotPhotos:
                try:
                    for photo in flickr.groups_pools_getPhotos(
                        group_id=group_id, user_id=user_id, tags=tags,
                        per_page='100', page=i
                    ).find('photos').getchildren():
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
                    pywikibot.output(u'Flickr api problem, sleeping')
                    time.sleep(30)

    # http://www.flickr.com/services/api/flickr.photosets.getPhotos.html
    # Get the photos in a photoset
    elif photoset_id:
        photos = flickr.photosets_getPhotos(photoset_id=photoset_id,
                                            per_page='100', page='1')
        pages = photos.find('photoset').attrib['pages']

        for i in range(1, int(pages) + 1):
            gotPhotos = False
            while not gotPhotos:
                try:
                    for photo in flickr.photosets_getPhotos(
                        photoset_id=photoset_id, per_page='100', page=i
                    ).find('photoset').getchildren():
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
                    pywikibot.output(u'Flickr api problem, sleeping')
                    time.sleep(30)

    # http://www.flickr.com/services/api/flickr.people.getPublicPhotos.html
    # Get the (public) photos uploaded by a user
    elif user_id:
        photos = flickr.people_getPublicPhotos(user_id=user_id,
                                               per_page='100', page='1')
        pages = photos.find('photos').attrib['pages']
        #flickrapi.exceptions.FlickrError
        for i in range(1, int(pages) + 1):
            gotPhotos = False
            while not gotPhotos:
                try:
                    for photo in flickr.people_getPublicPhotos(
                        user_id=user_id, per_page='100', page=i
                    ).find('photos').getchildren():
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
                    pywikibot.output(u'Flickr api problem, sleeping')
                    time.sleep(30)

    return


def usage():
    """
    Print usage information

    TODO : Need more.
    """
    pywikibot.output(
        u"Flickrripper is a tool to transfer flickr photos to Wikimedia Commons")
    pywikibot.output(u"-group_id:<group_id>\n")
    pywikibot.output(u"-photoset_id:<photoset_id>\n")
    pywikibot.output(u"-user_id:<user_id>\n")
    pywikibot.output(u"-tags:<tag>\n")
    return


def main():
    site = pywikibot.getSite(u'commons', u'commons')
    #imagerecat.initLists()

    #Get the api key
    if not config.flickr['api_key']:
        pywikibot.output('Flickr api key not found! Get yourself an api key')
        pywikibot.output(
            'Any flickr user can get a key at http://www.flickr.com/services/api/keys/apply/')
        return

    if 'api_secret' in config.flickr and config.flickr['api_secret']:
        flickr = flickrapi.FlickrAPI(config.flickr['api_key'], config.flickr['api_secret'])
        (token, frob) = flickr.get_token_part_one(perms='read')
        if not token:
            # The user still hasn't authorised this app yet, get_token_part_one() will have spawn a browser window
            pywikibot.input("Press ENTER after you authorized this program")
        flickr.get_token_part_two((token, frob))
    else:
        print 'Accessing public content only'
        flickr = flickrapi.FlickrAPI(config.flickr['api_key'])

    group_id = u''
    photoset_id = u''
    user_id = u''
    start_id = u''
    end_id = u''
    tags = u''
    addCategory = u''
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
        print config.sysopnames['commons']
        reviewer = config.sysopnames['commons']['commons']
    elif 'commons' in config.usernames['commons']:
        reviewer = config.usernames['commons']['commons']
    else:
        reviewer = u''

    # Should be renamed to overrideLicense or something like that
    override = u''
    for arg in pywikibot.handleArgs():
        if arg.startswith('-group_id'):
            if len(arg) == 9:
                group_id = pywikibot.input(u'What is the group_id of the pool?')
            else:
                group_id = arg[10:]
        elif arg.startswith('-photoset_id'):
            if len(arg) == 12:
                photoset_id = pywikibot.input(u'What is the photoset_id?')
            else:
                photoset_id = arg[13:]
        elif arg.startswith('-user_id'):
            if len(arg) == 8:
                user_id = pywikibot.input(
                    u'What is the user_id of the flickr user?')
            else:
                user_id = arg[9:]
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
        elif arg.startswith('-tags'):
            if len(arg) == 5:
                tags = pywikibot.input(
                    u'What is the tag you want to filter out (currently only one supported)?')
            else:
                tags = arg[6:]
        elif arg == '-flickrreview':
            flickrreview = True
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
    pywikibot.output(u'Finished running')
    pywikibot.output(u'Total photos: ' + str(totalPhotos))
    pywikibot.output(u'Uploaded photos: ' + str(uploadedPhotos))

if __name__ == "__main__":
    main()
