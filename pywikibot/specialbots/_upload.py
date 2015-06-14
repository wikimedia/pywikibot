#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Special bot library containing UploadRobot.

Do not import classes directly from here but from specialbots.
"""
#
# (C) Pywikibot team, 2003-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import os
import tempfile

import pywikibot
import pywikibot.data.api

from pywikibot import config

from pywikibot.bot import BaseBot, QuitKeyboardInterrupt
from pywikibot.tools import PY2, deprecated, deprecated_args, UnicodeType
from pywikibot.tools.formatter import color_format

if not PY2:
    from urllib.parse import urlparse
    from urllib.request import URLopener
else:
    from urllib import URLopener
    from urlparse import urlparse


class UploadRobot(BaseBot):

    """Upload bot."""

    @deprecated_args(uploadByUrl=None, urlEncoding='url_encoding',
                     useFilename='use_filename', keepFilename='keep_filename',
                     verifyDescription='verify_description',
                     ignoreWarning='ignore_warning', targetSite='target_site')
    def __init__(self, url, url_encoding=None, description='',
                 use_filename=None, keep_filename=False,
                 verify_description=True, ignore_warning=False,
                 target_site=None, aborts=[], chunk_size=0, summary=None,
                 filename_prefix=None, **kwargs):
        """
        Initializer.

        @param url: path to url or local file (deprecated), or list of urls or
            paths to local files.
        @type url: str (deprecated) or list
        @param description: Description of file for its page. If multiple files
            are uploading the same description is used for every file.
        @type description: str
        @param use_filename: Specify title of the file's page. If multiple
            files are uploading it asks to change the name for second, third,
            etc. files, otherwise the last file will overwrite the other.
        @type use_filename: str
        @param keep_filename: Set to True to keep original names of urls and
            files, otherwise it will ask to enter a name for each file.
        @type keep_filename: bool
        @param summary: Summary of the upload
        @type summary: str
        @param verify_description: Set to True to proofread the description.
        @type verify_description: bool
        @param ignore_warning: Set this to True to upload even if another file
            would be overwritten or another mistake would be risked. Set it to
            an array of warning codes to selectively ignore specific warnings.
        @type ignore_warning: bool or list
        @param target_site: Set the site to upload to. If target site is not
            given it's taken from user-config.py.
        @type target_site: object
        @param aborts: List of the warning types to abort upload on. Set to
            True to abort on any warning.
        @type aborts: bool or list
        @param chunk_size: Upload the file in chunks (more overhead, but
            restartable) specified in bytes. If no value is specified the file
            will be uploaded as whole.
        @type chunk_size: integer
        @param filename_prefix: Specify prefix for the title of every
            file's page.
        @type filename_prefix: str
        @param always: Disables any input, requires that either ignore_warning
            or aborts are set to True and that the description is also set. It
            overwrites verify_description to False and keep_filename to True.
        @type always: bool

        @deprecated: Using upload_image() is deprecated, use upload_file() with
            file_url param instead

        """
        super(UploadRobot, self).__init__(**kwargs)
        always = self.getOption('always')
        if (always and ignore_warning is not True and aborts is not True):
            raise ValueError('When always is set to True, either '
                             'ignore_warning or aborts must be set to True.')
        if always and not description:
            raise ValueError('When always is set to True, the description '
                             'must be set.')
        self.url = url
        if isinstance(self.url, UnicodeType):
            pywikibot.warning('url as string is deprecated. '
                              'Use an iterable instead.')
        self.url_encoding = url_encoding
        self.description = description
        self.use_filename = use_filename
        self.keep_filename = keep_filename or always
        self.verify_description = verify_description and not always
        self.ignore_warning = ignore_warning
        self.aborts = aborts
        self.chunk_size = chunk_size
        self.summary = summary
        self.filename_prefix = filename_prefix
        if config.upload_to_commons:
            self.target_site = target_site or pywikibot.Site('commons',
                                                             'commons')
        else:
            self.target_site = target_site or pywikibot.Site()
        self.target_site.login()

    def read_file_content(self, file_url=None):
        """Return name of temp file in which remote file is saved."""
        if not file_url:
            file_url = self.url
            pywikibot.warning('file_url is not given. '
                              'Set to self.url by default.')
        pywikibot.output('Reading file %s' % file_url)
        resume = False
        rlen = 0
        _contents = None
        dt = 15
        uo = URLopener()
        retrieved = False

        while not retrieved:
            if resume:
                pywikibot.output('Resume download...')
                uo.addheader('Range', 'bytes=%s-' % rlen)

            infile = uo.open(file_url)
            info = infile.info()

            if PY2:
                info_get = info.getheader
            else:
                info_get = info.get
            content_type = info_get('Content-Type')
            content_len = info_get('Content-Length')
            accept_ranges = info_get('Accept-Ranges')

            if 'text/html' in content_type:
                pywikibot.output("Couldn't download the image: "
                                 'the requested URL was not found on server.')
                return

            valid_ranges = accept_ranges == 'bytes'

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
                        'Connection closed at byte %s (%s left)'
                        % (rlen, content_len))
                    if valid_ranges and rlen > 0:
                        resume = True
                    pywikibot.output('Sleeping for %d seconds...' % dt)
                    pywikibot.sleep(dt)
                    if dt <= 60:
                        dt += 15
                    elif dt < 360:
                        dt += 60
            else:
                pywikibot.log(
                    'WARNING: length check of retrieved data not possible.')
        handle, tempname = tempfile.mkstemp()
        with os.fdopen(handle, 'wb') as t:
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
        if self.ignore_warning is True or (self.ignore_warning is not False
                                           and warning in self.ignore_warning):
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
            answer = pywikibot.input_yn('Do you want to ignore?',
                                        default=False, automatic_quit=False)
        return answer

    def process_filename(self, file_url=None):
        """Return base filename portion of file_url."""
        if not file_url:
            file_url = self.url
            pywikibot.warning('file_url is not given. '
                              'Set to self.url by default.')

        always = self.getOption('always')
        # Isolate the pure name
        filename = file_url
        # Filename may be either a URL or a local file path
        if '://' in filename:
            # extract the path portion of the URL
            filename = urlparse(filename).path
        filename = os.path.basename(filename)
        if self.use_filename:
            filename = self.use_filename
        if self.filename_prefix:
            filename = self.filename_prefix + filename
        if not self.keep_filename:
            pywikibot.output(
                'The filename on the target wiki will default to: %s'
                % filename)
            assert not always
            newfn = pywikibot.input(
                'Enter a better name, or press enter to accept:')
            if newfn != '':
                filename = newfn
        # FIXME: these 2 belong somewhere else, presumably in family
        # forbidden characters are handled by pywikibot/page.py
        forbidden = ':*?/\\'  # to be extended
        try:
            allowed_formats = self.target_site.siteinfo.get(
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
                c = ''.join(invalid)
                pywikibot.output(
                    'Invalid character(s): %s. Please try again' % c)
                continue
            if allowed_formats and ext not in allowed_formats:
                if always:
                    pywikibot.output('File format is not one of '
                                     '[{0}]'.format(' '.join(allowed_formats)))
                    continue
                elif not pywikibot.input_yn(
                        'File format is not one of [%s], but %s. Continue?'
                        % (' '.join(allowed_formats), ext),
                        default=False, automatic_quit=False):
                    continue
            potential_file_page = pywikibot.FilePage(self.target_site,
                                                     filename)
            if potential_file_page.exists():
                overwrite = self._handle_warning('exists')
                if overwrite is False:
                    pywikibot.output(
                        'File exists and you asked to abort. Skipping.')
                    return None
                if potential_file_page.has_permission():
                    if overwrite is None:
                        overwrite = not pywikibot.input_yn(
                            'File with name %s already exists. '
                            'Would you like to change the name? '
                            '(Otherwise file will be overwritten.)'
                            % filename, default=True,
                            automatic_quit=False)
                    if not overwrite:
                        continue
                    else:
                        break
                else:
                    pywikibot.output('File with name %s already exists and '
                                     'cannot be overwritten.' % filename)
                    continue
            else:
                try:
                    if potential_file_page.fileIsShared():
                        pywikibot.output(
                            'File with name %s already exists in shared '
                            'repository and cannot be overwritten.' % filename)
                        continue
                    else:
                        break
                except pywikibot.NoPage:
                    break

        # A proper description for the submission.
        # Empty descriptions are not accepted.
        if self.description:
            pywikibot.output('The suggested description is:\n%s'
                             % self.description)

        while not self.description or self.verify_description:
            if not self.description:
                pywikibot.output(color_format(
                    '{lightred}It is not possible to upload a file '
                    'without a description.{default}'))
            assert not always
            # if no description, ask if user want to add one or quit,
            # and loop until one is filled.
            # if self.verify_description, ask if user want to change it
            # or continue.
            if self.description:
                question = 'Do you want to change this description?'
            else:
                question = 'No description was given. Add one?'
            if pywikibot.input_yn(question, default=not self.description,
                                  automatic_quit=self.description):
                from pywikibot import editor as editarticle
                editor = editarticle.TextEditor()
                try:
                    new_description = editor.edit(self.description)
                except ImportError:
                    raise
                except Exception as e:
                    pywikibot.error(e)
                    continue
                # if user saved / didn't press Cancel
                if new_description:
                    self.description = new_description
            elif not self.description:
                raise QuitKeyboardInterrupt
            self.verify_description = False

        return filename

    def abort_on_warn(self, warn_code):
        """Determine if the warning message should cause an abort."""
        if self.aborts is True:
            return True
        else:
            return warn_code in self.aborts

    def ignore_on_warn(self, warn_code):
        """
        Determine if the warning message should be ignored.

        @param warn_code: The warning message
        @type warn_code: str
        """
        if self.ignore_warning is True:
            return True
        else:
            return warn_code in self.ignore_warning

    @deprecated('UploadRobot.upload_file()', since='20141211')
    @deprecated_args(debug=None)
    def upload_image(self):
        """Upload image."""
        return self.upload_file(self.url)

    @deprecated_args(debug=None)
    def upload_file(self, file_url, _file_key=None, _offset=0):
        """
        Upload the image at file_url to the target wiki.

        @see: U{https://www.mediawiki.org/wiki/API:Upload}

        Return the filename that was used to upload the image.
        If the upload fails, ask the user whether to try again or not.
        If the user chooses not to retry, return None.
        """
        filename = self.process_filename(file_url)
        if not filename:
            return None

        site = self.target_site
        imagepage = pywikibot.FilePage(site, filename)  # normalizes filename
        imagepage.text = self.description

        pywikibot.output('Uploading file to {0}...'.format(site))

        ignore_warnings = self.ignore_warning is True or self._handle_warnings
        if '://' in file_url and not site.has_right('upload_by_url'):
            file_url = self.read_file_content(file_url)

        try:
            success = imagepage.upload(file_url,
                                       ignore_warnings=ignore_warnings,
                                       chunk_size=self.chunk_size,
                                       _file_key=_file_key, _offset=_offset,
                                       comment=self.summary)
        except pywikibot.data.api.APIError as error:
            if error.code == 'uploaddisabled':
                pywikibot.error(
                    'Upload error: Local file uploads are disabled on %s.'
                    % site)
            else:
                pywikibot.error('Upload error: ', exc_info=True)
        except Exception:
            pywikibot.error('Upload error: ', exc_info=True)
        else:
            if success:
                # No warning, upload complete.
                pywikibot.output('Upload of %s successful.' % filename)
                self._save_counter += 1
                return filename  # data['filename']
            else:
                pywikibot.output('Upload aborted.')
        return None

    def run(self):
        """Run bot."""
        # early check that upload is enabled
        if self.target_site.is_uploaddisabled():
            pywikibot.error(
                'Upload error: Local file uploads are disabled on %s.'
                % self.target_site)
            return

        # early check that user has proper rights to upload
        if not self.target_site.has_right('upload'):
            pywikibot.error(
                "User '%s' does not have upload rights on site %s."
                % (self.target_site.user(), self.target_site))
            return

        try:
            if isinstance(self.url, UnicodeType):
                self._treat_counter = 1
                return self.upload_file(self.url)
            for file_url in self.url:
                self.upload_file(file_url)
                self._treat_counter += 1
        except QuitKeyboardInterrupt:
            pywikibot.output('\nUser quit %s bot run...' %
                             self.__class__.__name__)
        except KeyboardInterrupt:
            if config.verbose_output:
                raise
            else:
                pywikibot.output('\nKeyboardInterrupt during %s bot run...' %
                                 self.__class__.__name__)
        finally:
            self.exit()
