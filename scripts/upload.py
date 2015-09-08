#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to upload images to wikipedia.

Arguments:

  -keep         Keep the filename as is
  -filename     Target filename without the namespace prefix
  -noverify     Do not ask for verification of the upload description if one
                is given
  -abortonwarn: Abort upload on the specified warning type. If no warning type
                is specified, aborts on any warning.
  -ignorewarn:  Ignores specified upload warnings. If no warning type is
                specified, ignores all warnings. Use with caution
  -chunked:     Upload the file in chunks (more overhead, but restartable). If
                no value is specified the chunk size is 1 MiB. The value must
                be a number which can be preceded by a suffix. The units are:
                  No suffix: Bytes
                  'k': Kilobytes (1000 B)
                  'M': Megabytes (1000000 B)
                  'Ki': Kibibytes (1024 B)
                  'Mi': Mebibytes (1024x1024 B)
                The suffixes are case insensitive.
  -always       Don't ask the user anything. This will imply -keep and
                -noverify and require that either -abortonwarn or -ignorewarn
                is defined for all. It will also require a valid file name and
                description. It'll only overwrite files if -ignorewarn includes
                the 'exists' warning.
  -recursive    When the filename is a directory it also uploads the files from
                the subdirectories.

It is possible to combine -abortonwarn and -ignorewarn so that if the specific
warning is given it won't apply the general one but more specific one. So if it
should ignore specific warnings and abort on the rest it's possible by defining
no warning for -abortonwarn and the specific warnings for -ignorewarn. The order
does not matter. If both are unspecific or a warning is specified by both, it'll
prefer aborting.

If any other arguments are given, the first is either URL, filename or directory
to upload, and the rest is a proposed description to go with the upload. If none
of these are given, the user is asked for the directory, file or URL to upload.
The bot will then upload the image to the wiki.

The script will ask for the location of an image(s), if not given as a parameter,
and for a description.
"""
#
# (C) Rob W.W. Hooft, Andre Engels 2003-2004
# (C) Pywikibot team, 2003-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

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
from pywikibot.bot import suggest_help, BaseBot
from pywikibot.tools import (
    deprecated
)

if sys.version_info[0] > 2:
    from urllib.parse import urlparse
    from urllib.request import URLopener
    basestring = (str,)
else:
    from urlparse import urlparse
    from urllib import URLopener


class UploadRobot(BaseBot):

    """Upload bot."""

    def __init__(self, url, urlEncoding=None, description=u'',
                 useFilename=None, keepFilename=False,
                 verifyDescription=True, ignoreWarning=False,
                 targetSite=None, uploadByUrl=False, aborts=[], chunk_size=0,
                 **kwargs):
        """
        Constructor.

        @param url: path to url or local file (deprecated), or list of urls or
            paths to local files.
        @type url: string (deprecated) or list
        @param description: Description of file for its page. If multiple files
            are uploading the same description is used for every file.
        @type description: string
        @param useFilename: Specify title of the file's page. If multiple
            files are uploading it asks to change the name for second, third,
            etc. files, otherwise the last file will overwrite the other.
        @type useFilename: string
        @param keepFilename: Set to True to keep original names of urls and
            files, otherwise it will ask to enter a name for each file.
        @type keepFilename: bool
        @param verifyDescription: Set to False to not proofread the description.
        @type verifyDescription: bool
        @param ignoreWarning: Set this to True to upload even if another file
            would be overwritten or another mistake would be risked. Set it to
            an array of warning codes to selectively ignore specific warnings.
        @type ignoreWarning: bool or list
        @param targetSite: Set the site to upload to. If target site is not
            given it's taken from user-config.py.
        @type targetSite: object
        @param aborts: List of the warning types to abort upload on. Set to True
            to abort on any warning.
        @type aborts: bool or list
        @param chunk_size: Upload the file in chunks (more overhead, but
            restartable) specified in bytes. If no value is specified the file
            will be uploaded as whole.
        @type chunk_size: integer
        @param always: Disables any input, requires that either ignoreWarning or
            aborts are set to True and that the description is also set. It will
            overwrite verifyDescription to False and keepFilename to True.
        @type always: bool

        @deprecated: Using upload_image() is deprecated, use upload_file() with
            file_url param instead

        """
        super(UploadRobot, self).__init__(**kwargs)
        always = self.getOption('always')
        if (always and ignoreWarning is not True and aborts is not True):
            raise ValueError('When always is set to True, either ignoreWarning '
                             'or aborts must be set to True.')
        if always and not description:
            raise ValueError('When always is set to True the description must '
                             'be set.')
        self.url = url
        if isinstance(self.url, basestring):
            pywikibot.warning("url as string is deprecated. "
                              "Use an iterable instead.")
        self.urlEncoding = urlEncoding
        self.description = description
        self.useFilename = useFilename
        self.keepFilename = keepFilename or always
        self.verifyDescription = verifyDescription and not always
        self.ignoreWarning = ignoreWarning
        self.aborts = aborts
        self.chunk_size = chunk_size
        if config.upload_to_commons:
            self.targetSite = targetSite or pywikibot.Site('commons',
                                                           'commons')
        else:
            self.targetSite = targetSite or pywikibot.Site()
        self.targetSite.login()
        self.uploadByUrl = uploadByUrl

    @deprecated()
    def urlOK(self):
        """Return True if self.url is a URL or an existing local file."""
        return "://" in self.url or os.path.exists(self.url)

    def read_file_content(self, file_url=None):
        """Return name of temp file in which remote file is saved."""
        if not file_url:
            file_url = self.url
            pywikibot.warning("file_url is not given. "
                              "Set to self.url by default.")
        pywikibot.output(u'Reading file %s' % file_url)
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

            infile = uo.open(file_url)

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
        with os.fdopen(handle, "wb") as t:
            t.write(_contents)
        return tempname

    def _handle_warning(self, warning):
        """
        Return whether the warning cause an abort or be ignored.

        @param warning: The warning name
        @type warning: str
        @return: False if this warning should cause an abort, True if it should
            be ignored or None if this warning has no default handler.
        @rtype: bool or None
        """
        if self.aborts is not True:
            if warning in self.aborts:
                return False
        if self.ignoreWarning is True or (self.ignoreWarning is not False and
                                          warning in self.ignoreWarning):
            return True
        return None if self.aborts is not True else False

    def _handle_warnings(self, warnings):
        messages = '\n'.join('{0.code}: {0.info}'.format(warning)
                             for warning in sorted(warnings,
                                                   key=lambda w: w.code))
        if len(warnings) > 1:
            messages = '\n' + messages
        pywikibot.output('We got the following warning(s): ' + messages)
        answer = True
        for warning in warnings:
            this_answer = self._handle_warning(warning.code)
            if this_answer is False:
                answer = False
                break
            elif this_answer is None:
                answer = None
        if answer is None:
            answer = pywikibot.input_yn(u"Do you want to ignore?",
                                        default=False, automatic_quit=False)
        return answer

    def process_filename(self, file_url=None):
        """Return base filename portion of file_url."""
        if not file_url:
            file_url = self.url
            pywikibot.warning("file_url is not given. "
                              "Set to self.url by default.")

        always = self.getOption('always')
        # Isolate the pure name
        filename = file_url
        # Filename may be either a URL or a local file path
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
            assert not always
            newfn = pywikibot.input(
                u'Enter a better name, or press enter to accept:')
            if newfn != "":
                filename = newfn
        # FIXME: these 2 belong somewhere else, presumably in family
        # forbidden characters are handled by pywikibot/page.py
        forbidden = ':*?/\\'  # to be extended
        try:
            allowed_formats = self.targetSite.siteinfo.get(
                'fileextensions', get_default=False)
        except KeyError:
            allowed_formats = []
        else:
            allowed_formats = [item['ext'] for item in allowed_formats]

        # ask until it's valid
        first_check = True
        while True:
            if not first_check:
                if always:
                    filename = None
                else:
                    filename = pywikibot.input('Enter a better name, or press '
                                               'enter to skip the file:')
                if not filename:
                    return None
            first_check = False
            ext = os.path.splitext(filename)[1].lower().strip('.')
            # are any chars in forbidden also in filename?
            invalid = set(forbidden) & set(filename)
            if invalid:
                c = "".join(invalid)
                pywikibot.output(
                    'Invalid character(s): %s. Please try again' % c)
                continue
            if allowed_formats and ext not in allowed_formats:
                if always:
                    pywikibot.output('File format is not one of '
                                     '[{0}]'.format(' '.join(allowed_formats)))
                    continue
                elif not pywikibot.input_yn(
                        u"File format is not one of [%s], but %s. Continue?"
                        % (u' '.join(allowed_formats), ext),
                        default=False, automatic_quit=False):
                    continue
            potential_file_page = pywikibot.FilePage(self.targetSite, filename)
            if potential_file_page.exists():
                overwrite = self._handle_warning('exists')
                if overwrite is False:
                    pywikibot.output("File exists and you asked to abort. Skipping.")
                    return None
                if potential_file_page.canBeEdited():
                    if overwrite is None:
                        overwrite = not pywikibot.input_yn(
                            "File with name %s already exists. "
                            "Would you like to change the name? "
                            "(Otherwise file will be overwritten.)"
                            % filename, default=True,
                            automatic_quit=False)
                    if not overwrite:
                        continue
                    else:
                        break
                else:
                    pywikibot.output(u"File with name %s already exists and "
                                     "cannot be overwritten." % filename)
                    continue
            else:
                try:
                    if potential_file_page.fileIsShared():
                        pywikibot.output(u"File with name %s already exists in shared "
                                         "repository and cannot be overwritten."
                                         % filename)
                        continue
                    else:
                        break
                except pywikibot.NoPage:
                    break

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

            assert not always
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

    def ignore_on_warn(self, warn_code):
        """Determine if the warning message should be ignored."""
        if self.ignoreWarning is True:
            return True
        else:
            return warn_code in self.ignoreWarning

    @deprecated('UploadRobot.upload_file()')
    def upload_image(self, debug=False):
        """Upload image."""
        self.upload_file(self.url, debug)

    def upload_file(self, file_url, debug=False, _file_key=None, _offset=0):
        """Upload the image at file_url to the target wiki.

        Return the filename that was used to upload the image.
        If the upload fails, ask the user whether to try again or not.
        If the user chooses not to retry, return null.

        """
        filename = self.process_filename(file_url)
        if not filename:
            return None

        site = self.targetSite
        imagepage = pywikibot.FilePage(site, filename)  # normalizes filename
        imagepage.text = self.description

        pywikibot.output(u'Uploading file to %s via API...' % site)

        success = False
        try:
            if self.ignoreWarning is True:
                apiIgnoreWarnings = True
            else:
                apiIgnoreWarnings = self._handle_warnings
            if self.uploadByUrl:
                success = site.upload(imagepage, source_url=file_url,
                                      ignore_warnings=apiIgnoreWarnings,
                                      _file_key=_file_key, _offset=_offset)
            else:
                if "://" in file_url:
                    temp = self.read_file_content(file_url)
                else:
                    temp = file_url
                success = site.upload(imagepage, source_filename=temp,
                                      ignore_warnings=apiIgnoreWarnings,
                                      chunk_size=self.chunk_size,
                                      _file_key=_file_key, _offset=_offset)

        except pywikibot.data.api.APIError as error:
            if error.code == u'uploaddisabled':
                pywikibot.error("Upload error: Local file uploads are disabled on %s."
                                % site)
            else:
                pywikibot.error("Upload error: ", exc_info=True)
            return None
        except Exception:
            pywikibot.error("Upload error: ", exc_info=True)
            return None
        else:
            if success:
                # No warning, upload complete.
                pywikibot.output(u"Upload of %s successful." % filename)
                return filename  # data['filename']
            else:
                pywikibot.output(u"Upload aborted.")
                return None

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
        if isinstance(self.url, basestring):
            return self.upload_file(self.url)
        for file_url in self.url:
            self.upload_file(file_url)


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
    always = False
    useFilename = None
    verifyDescription = True
    aborts = set()
    ignorewarn = set()
    chunk_size = 0
    chunk_size_regex = r'^-chunked(?::(\d+(?:\.\d+)?)[ \t]*(k|ki|m|mi)?b?)?$'
    chunk_size_regex = re.compile(chunk_size_regex, re.I)
    recursive = False

    # process all global bot args
    # returns a list of non-global args, i.e. args for upload.py
    for arg in pywikibot.handle_args(args):
        if arg:
            if arg == '-always':
                keepFilename = True
                always = True
                verifyDescription = False
            elif arg == '-recursive':
                recursive = True
            elif arg.startswith('-keep'):
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
            elif arg.startswith('-ignorewarn'):
                if len(arg) > len('-ignorewarn:') and ignorewarn is not True:
                    ignorewarn.add(arg[len('-ignorewarn:'):])
                else:
                    ignorewarn = True
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
    while not ("://" in url or os.path.exists(url)):
        if not url:
            error = 'No input filename given.'
        else:
            error = 'Invalid input filename given.'
            if not always:
                error += ' Try again.'
        if always:
            url = None
            break
        else:
            pywikibot.output(error)
        url = pywikibot.input(u'URL, file or directory where files are now:')
    if always and ((aborts is not True and ignorewarn is not True) or
                   not description or url is None):
        additional = ''
        missing = []
        if url is None:
            missing += ['filename']
            additional = error + ' '
        if description is None:
            missing += ['description']
        if aborts is not True and ignorewarn is not True:
            additional += ('Either -ignorewarn or -abortonwarn must be '
                           'defined for all codes. ')
        additional += 'Unable to run in -always mode'
        suggest_help(missing_parameters=missing, additional_text=additional)
        return False
    if os.path.isdir(url):
        file_list = []
        for directory_info in os.walk(url):
            if not recursive:
                # Do not visit any subdirectories
                directory_info[1][:] = []
            for dir_file in directory_info[2]:
                file_list.append(os.path.join(directory_info[0], dir_file))
        url = file_list
    else:
        url = [url]
    bot = UploadRobot(url, description=description, useFilename=useFilename,
                      keepFilename=keepFilename,
                      verifyDescription=verifyDescription,
                      aborts=aborts, ignoreWarning=ignorewarn,
                      chunk_size=chunk_size, always=always)
    bot.run()

if __name__ == "__main__":
    main()
