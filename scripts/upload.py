# -*- coding: utf-8 -*-
"""
Script to upload images to wikipedia.

Arguments:

  -keep         Keep the filename as is
  -filename     Target filename
  -noverify     Do not ask for verification of the upload description if one
                is given

If any other arguments are given, the first is the URL or filename to upload,
and the rest is a proposed description to go with the upload. If none of these
are given, the user is asked for the file or URL to upload. The bot will then
upload the image to the wiki.

The script will ask for the location of an image, if not given as a parameter,
and for a description.
"""
#
# (C) Rob W.W. Hooft, Andre Engels 2003-2004
# (C) Pywikipedia bot team, 2003-2010
#
# Distributed under the terms of the MIT license.
#
__version__='$Id$'
#

import os, sys, time
import urllib
import urlparse
import tempfile
import pywikibot
from pywikibot import config


class UploadRobot:
    def __init__(self, url, urlEncoding=None, description=u'',
                 useFilename=None, keepFilename=False,
                 verifyDescription=True, ignoreWarning=False,
                 targetSite=None, uploadByUrl=False):
        """
        ignoreWarning - Set this to True if you want to upload even if another
                        file would be overwritten or another mistake would be
                        risked.

        """
        self.url = url
        self.urlEncoding = urlEncoding
        self.description = description
        self.useFilename = useFilename
        self.keepFilename = keepFilename
        self.verifyDescription = verifyDescription
        self.ignoreWarning = ignoreWarning
        if config.upload_to_commons:
            self.targetSite = targetSite or pywikibot.Site('commons', 'commons')
        else:
            self.targetSite = targetSite or pywikibot.Site()
        self.targetSite.forceLogin()
        self.uploadByUrl = uploadByUrl

    def urlOK(self):
        """Return true if self.url looks like an URL or an existing local file.

        """
        return "://" in self.url or os.path.exists(self.url)

    def read_file_content(self):
        """Return name of temp file in which remote file is saved."""
        pywikibot.output(u'Reading file %s' % self.url)
        resume = False
        dt = 15
        uo = urllib.URLopener()
        retrieved = False

        while not retrieved:
            if resume:
                pywikibot.output(u"Resume download...")
                uo.addheader('Range', 'bytes=%s-' % rlen)

            infile = uo.open(self.url)

            if 'text/html' in infile.info().getheader('Content-Type'):
                print \
"Couldn't download the image: the requested URL was not found on server."
                return

            content_len = infile.info().getheader('Content-Length')
            accept_ranges = infile.info().getheader('Accept-Ranges') == 'bytes'

            if resume:
                _contents += infile.read()
            else:
                _contents = infile.read()

            infile.close()
            retrieved = True

            if content_len:
                rlen = len(_contents)
                content_len = int(content_len)
                if rlen < content_len:
                    retrieved = False
                    pywikibot.output(
                        u"Connection closed at byte %s (%s left)"
                         % (rlen, content_len))
                    if accept_ranges and rlen > 0:
                        resume = True
                    pywikibot.output(u"Sleeping for %d seconds..." % dt)
                    time.sleep(dt)
                    if dt <= 60:
                        dt += 15
                    elif dt < 360:
                        dt += 60
            else:
                pywikibot.log(
                    u"WARNING: No check length to retrieved data is possible.")
        handle, tempname = tempfile.mkstemp()
        t = os.fdopen(handle, "wb")
        t.write(_contents)
        t.close()
        return tempname

    def process_filename(self):
        """Return base filename portion of self.url"""
        # Isolate the pure name
        filename = self.url
        # Filename may be either a local file path or a URL
        if "://" in filename:
            # extract the path portion of the URL
            filename = urlparse.urlparse(filename).path
        filename = os.path.basename(filename)

        if self.useFilename:
            filename = self.useFilename
        if not self.keepFilename:
            pywikibot.output(
                u"The filename on the target wiki will default to: %s"
                % filename)
            # FIXME: these 2 belong somewhere else, presumably in family
            forbidden = '/' # to be extended
            allowed_formats = (u'gif', u'jpg', u'jpeg', u'mid', u'midi',
                               u'ogg', u'png', u'svg', u'xcf', u'djvu')
            # ask until it's valid
            while True:
                newfn = pywikibot.input(
                            u'Enter a better name, or press enter to accept:')
                if newfn == "":
                    newfn = filename
                    break
                ext = os.path.splitext(newfn)[1].lower().strip('.')
                # are any chars in forbidden also in newfn?
                invalid = set(forbidden) & set(newfn)
                if invalid:
                    c = "".join(invalid)
                    print "Invalid character(s): %s. Please try again" % c
                    continue
                if ext not in allowed_formats:
                    choice = pywikibot.inputChoice(
                        u"File format is not one of [%s], but %s. Continue?"
                         % (u' '.join(allowed_formats), ext),
                            ['yes', 'no'], ['y', 'N'], 'N')
                    if choice == 'n':
                        continue
                break
            if newfn != '':
                filename = newfn
        # A proper description for the submission.
        pywikibot.output(u"The suggested description is:")
        pywikibot.output(self.description)
        if self.verifyDescription:
            newDescription = u''
            choice = pywikibot.inputChoice(
                u'Do you want to change this description?',
                ['Yes', 'No'], ['y', 'N'], 'n')
            if choice == 'y':
                from pywikibot import editor as editarticle
                editor = editarticle.TextEditor()
                newDescription = editor.edit(self.description)
            # if user saved / didn't press Cancel
            if newDescription:
                self.description = newDescription
        return filename

    def upload_image(self, debug=False):
        """Upload the image at self.url to the target wiki.

        Return the filename that was used to upload the image.
        If the upload fails, ask the user whether to try again or not.
        If the user chooses not to retry, return null.

        """
        filename = self.process_filename()

        site = self.targetSite
        imagepage = pywikibot.ImagePage(site, filename) # normalizes filename
        imagepage.text = self.description

        pywikibot.output(u'Uploading file to %s via API....' % site)

        try:
            if self.uploadByUrl:
                site.upload(imagepage, source_url=self.url,
                            ignore_warnings=self.ignoreWarning)
            else:
                if "://" in self.url:
                    temp = self.read_file_content()
                else:
                    temp = self.url
                site.upload(imagepage, source_filename=temp,
                            ignore_warnings=self.ignoreWarning)

        except pywikibot.UploadWarning, warn:
            pywikibot.output(u"We got a warning message: ", newline=False)
            pywikibot.output(str(warn))
            answer = pywikibot.inputChoice(u"Do you want to ignore?",
                                           ['Yes', 'No'], ['y', 'N'], 'N')
            if answer == "y":
                self.ignoreWarning = 1
                self.keepFilename = True
                return self.upload_image(debug)
            else:
                pywikibot.output(u"Upload aborted.")
                return

        except Exception, e:
            pywikibot.error("Upload error: ", exc_info=True)

        else:
            #No warning, upload complete.
            pywikibot.output(u"Upload successful.")
            return filename #data['filename']

    def run(self):
        while not self.urlOK():
            if not self.url:
                pywikibot.output(u'No input filename given')
            else:
                pywikibot.output(u'Invalid input filename given. Try again.')
            self.url = pywikibot.input(u'File or URL where image is now:')
        return self.upload_image()


def main(*args):
    url = u''
    description = []
    keepFilename = False
    useFilename = None
    verifyDescription = True

    # process all global bot args
    # returns a list of non-global args, i.e. args for upload.py
    for arg in pywikibot.handleArgs(*args):
        if arg:
            if arg.startswith('-keep'):
                keepFilename = True
            elif arg.startswith('-filename:'):
                useFilename = arg[10:]
            elif arg.startswith('-noverify'):
                verifyDescription = False
            elif url == u'':
                url = arg
            else:
                description.append(arg)
    description = u' '.join(description)
    bot = UploadRobot(url, description=description, useFilename=useFilename,
                      keepFilename=keepFilename,
                      verifyDescription=verifyDescription)
    bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
