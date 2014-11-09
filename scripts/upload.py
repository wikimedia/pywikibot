#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to upload images to wikipedia.

Arguments:

  -keep         Keep the filename as is
  -filename     Target filename
  -noverify     Do not ask for verification of the upload description if one
                is given
  -abortonwarn: Abort upload on the specified warning type. If no warning type
                is specified abort on all warnings.
  -chunked:     Upload the file in chunks (more overhead, but restartable). If
                no value is specified the chunk size is 1 MiB. The value must
                be a number which can be preceded by a suffix. The units are:
                  No suffix: Bytes
                  'k': Kilobytes (1000 B)
                  'M': Megabytes (1000000 B)
                  'Ki': Kibibytes (1024 B)
                  'Mi': Mebibytes (1024x1024 B)
                The suffixes are case insenstive.

If any other arguments are given, the first is the URL or filename to upload,
and the rest is a proposed description to go with the upload. If none of these
are given, the user is asked for the file or URL to upload. The bot will then
upload the image to the wiki.

The script will ask for the location of an image, if not given as a parameter,
and for a description.
"""
#
# (C) Rob W.W. Hooft, Andre Engels 2003-2004
# (C) Pywikibot team, 2003-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import os
import time
import tempfile
import re
import math
import sys

import pywikibot
import pywikibot.data.api
from pywikibot import config

if sys.version_info[0] > 2:
    from urllib.parse import urlparse
    from urllib.request import URLopener
else:
    from urlparse import urlparse
    from urllib import URLopener


class UploadRobot:

    """Upload bot."""

    def __init__(self, url, urlEncoding=None, description=u'',
                 useFilename=None, keepFilename=False,
                 verifyDescription=True, ignoreWarning=False,
                 targetSite=None, uploadByUrl=False, aborts=[], chunk_size=0):
        """
        Constructor.

        @param ignoreWarning: Set this to True if you want to upload even if
            another file would be overwritten or another mistake would be
            risked.

        """
        self.url = url
        self.urlEncoding = urlEncoding
        self.description = description
        self.useFilename = useFilename
        self.keepFilename = keepFilename
        self.verifyDescription = verifyDescription
        self.ignoreWarning = ignoreWarning
        self.aborts = aborts
        self.chunk_size = chunk_size
        if config.upload_to_commons:
            self.targetSite = targetSite or pywikibot.Site('commons',
                                                           'commons')
        else:
            self.targetSite = targetSite or pywikibot.Site()
        self.targetSite.forceLogin()
        self.uploadByUrl = uploadByUrl

    def urlOK(self):
        """Return True if self.url is an URL or an existing local file."""
        return "://" in self.url or os.path.exists(self.url)

    def read_file_content(self):
        """Return name of temp file in which remote file is saved."""
        pywikibot.output(u'Reading file %s' % self.url)
        resume = False
        rlen = 0
        _contents = None
        dt = 15
        uo = URLopener()
        retrieved = False

        while not retrieved:
            if resume:
                pywikibot.output(u"Resume download...")
                uo.addheader('Range', 'bytes=%s-' % rlen)

            infile = uo.open(self.url)

            if 'text/html' in infile.info().getheader('Content-Type'):
                pywikibot.output(u"Couldn't download the image: "
                                 "the requested URL was not found on server.")
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
                    u"WARNING: length check of retrieved data not possible.")
        handle, tempname = tempfile.mkstemp()
        t = os.fdopen(handle, "wb")
        t.write(_contents)
        t.close()
        return tempname

    def process_filename(self):
        """Return base filename portion of self.url."""
        # Isolate the pure name
        filename = self.url
        # Filename may be either a local file path or a URL
        if "://" in filename:
            # extract the path portion of the URL
            filename = urlparse(filename).path
        filename = os.path.basename(filename)

        if self.useFilename:
            filename = self.useFilename
        if not self.keepFilename:
            pywikibot.output(
                u"The filename on the target wiki will default to: %s"
                % filename)
            # FIXME: these 2 belong somewhere else, presumably in family
            forbidden = '/'  # to be extended
            allowed_formats = (u'gif', u'jpg', u'jpeg', u'mid', u'midi',
                               u'ogg', u'png', u'svg', u'xcf', u'djvu',
                               u'ogv', u'oga', u'tif', u'tiff')
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
                    pywikibot.output(
                        'Invalid character(s): %s. Please try again' % c)
                    continue
                if ext not in allowed_formats:
                    if not pywikibot.input_yn(
                            u"File format is not one of [%s], but %s. Continue?"
                            % (u' '.join(allowed_formats), ext),
                            default=False, automatic_quit=False):
                        continue
                break
            if newfn != '':
                filename = newfn
        # A proper description for the submission.
        # Empty descriptions are not accepted.
        pywikibot.output(u'The suggested description is:\n%s'
                         % self.description)

        # Description must be set and verified
        if not self.description:
            self.verifyDescription = True

        while not self.description or self.verifyDescription:
            if not self.description:
                pywikibot.output(
                    u'\03{lightred}It is not possible to upload a file '
                    'without a summary/description.\03{default}')

            # if no description, default is 'yes'
            if pywikibot.input_yn(
                    u'Do you want to change this description?',
                    default=not self.description):
                from pywikibot import editor as editarticle
                editor = editarticle.TextEditor()
                try:
                    newDescription = editor.edit(self.description)
                except Exception as e:
                    pywikibot.error(e)
                    continue
                # if user saved / didn't press Cancel
                if newDescription:
                    self.description = newDescription
            self.verifyDescription = False

        return filename

    def abort_on_warn(self, warn_code):
        """Determine if the warning message should cause an abort."""
        if self.aborts is True:
            return True
        else:
            return warn_code in self.aborts

    def upload_image(self, debug=False):
        """Upload the image at self.url to the target wiki.

        Return the filename that was used to upload the image.
        If the upload fails, ask the user whether to try again or not.
        If the user chooses not to retry, return null.

        """
        filename = self.process_filename()

        site = self.targetSite
        imagepage = pywikibot.FilePage(site, filename)  # normalizes filename
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
                            ignore_warnings=self.ignoreWarning,
                            chunk_size=self.chunk_size)

        except pywikibot.data.api.UploadWarning as warn:
            pywikibot.output(
                u'We got a warning message: {0}'.format(warn.message))
            if (not self.abort_on_warn(warn.code) and
                    pywikibot.input_yn(u"Do you want to ignore?",
                                       default=False, automatic_quit=False)):
                self.ignoreWarning = True
                self.keepFilename = True
                return self.upload_image(debug)
            else:
                pywikibot.output(u"Upload aborted.")
                return
        except pywikibot.data.api.APIError as error:
            if error.code == u'uploaddisabled':
                pywikibot.error("Upload error: Local file uploads are disabled on %s."
                                  % site)
            else:
                pywikibot.error("Upload error: ", exc_info=True)
        except Exception:
            pywikibot.error("Upload error: ", exc_info=True)

        else:
            # No warning, upload complete.
            pywikibot.output(u"Upload successful.")
            return filename  # data['filename']

    def run(self):
        """Run bot."""
        # early check that upload is enabled
        if self.targetSite.is_uploaddisabled():
            pywikibot.error(
                "Upload error: Local file uploads are disabled on %s."
                % self.targetSite)
            return

        # early check that user has proper rights to upload
        if "upload" not in self.targetSite.userinfo["rights"]:
            pywikibot.error(
                "User '%s' does not have upload rights on site %s."
                % (self.targetSite.user(), self.targetSite))
            return

        while not self.urlOK():
            if not self.url:
                pywikibot.output(u'No input filename given')
            else:
                pywikibot.output(u'Invalid input filename given. Try again.')
            self.url = pywikibot.input(u'File or URL where image is now:')
        return self.upload_image()


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    url = u''
    description = []
    keepFilename = False
    useFilename = None
    verifyDescription = True
    aborts = set()
    chunk_size = 0
    chunk_size_regex = r'^-chunked(?::(\d+(?:\.\d+)?)[ \t]*(k|ki|m|mi)?b?)?$'
    chunk_size_regex = re.compile(chunk_size_regex, re.I)

    # process all global bot args
    # returns a list of non-global args, i.e. args for upload.py
    for arg in pywikibot.handle_args(args):
        if arg:
            if arg.startswith('-keep'):
                keepFilename = True
            elif arg.startswith('-filename:'):
                useFilename = arg[10:]
            elif arg.startswith('-noverify'):
                verifyDescription = False
            elif arg.startswith('-abortonwarn'):
                if len(arg) > len('-abortonwarn:') and aborts is not True:
                    aborts.add(arg[len('-abortonwarn:'):])
                else:
                    aborts = True
            elif arg.startswith('-chunked'):
                match = chunk_size_regex.match(arg)
                if match:
                    if match.group(1):  # number was in there
                        base = float(match.group(1))
                        if match.group(2):  # suffix too
                            suffix = match.group(2).lower()
                            if suffix == "k":
                                suffix = 1000
                            elif suffix == "m":
                                suffix = 1000000
                            elif suffix == "ki":
                                suffix = 1 << 10
                            elif suffix == "mi":
                                suffix = 1 << 20
                            else:
                                pass  # huh?
                        else:
                            suffix = 1
                        chunk_size = math.trunc(base * suffix)
                    else:
                        chunk_size = 1 << 20  # default to 1 MiB
                else:
                    pywikibot.error('Chunk size parameter is not valid.')
            elif url == u'':
                url = arg
            else:
                description.append(arg)
    description = u' '.join(description)
    bot = UploadRobot(url, description=description, useFilename=useFilename,
                      keepFilename=keepFilename,
                      verifyDescription=verifyDescription,
                      aborts=aborts, chunk_size=chunk_size)
    bot.run()

if __name__ == "__main__":
    main()
