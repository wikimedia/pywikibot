#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A generic bot to do data ingestion (batch uploading).

usage:

    python pwb.py data_ingestion -csvdir:local_dir/ -page:config_page
"""
#
# (C) Pywikibot team, 2013-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import base64
import codecs
import hashlib
import io
import os
import posixpath
import sys
from warnings import warn

import pywikibot
from pywikibot.comms.http import fetch
from pywikibot import pagegenerators
from pywikibot.specialbots import UploadRobot
from pywikibot.tools import deprecated, deprecated_args

if sys.version_info[0] > 2:
    import csv
else:
    import unicodecsv as csv

if sys.version_info[0] > 2:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse


class Photo(pywikibot.FilePage):

    """Represents a Photo (or other file), with metadata, to be uploaded."""

    def __init__(self, URL, metadata, site=None):
        """
        Constructor.

        @param URL: URL of photo
        @type URL: str
        @param metadata: metadata about the photo that can be referred to
            from the title & template
        @type metadata: dict
        @param site: target site
        @type site: APISite

        """
        self.URL = URL
        self.metadata = metadata
        self.metadata["_url"] = URL
        self.metadata["_filename"] = filename = posixpath.split(
            urlparse(URL)[2])[1]
        self.metadata["_ext"] = ext = filename.split(".")[-1]
        if ext == filename:
            self.metadata["_ext"] = ext = None
        self.contents = None

        if not site:
            site = pywikibot.Site('commons', 'commons')

        # default title
        super(Photo, self).__init__(site,
                                    self.getTitle('%(_filename)s.%(_ext)s'))

    def downloadPhoto(self):
        """
        Download the photo and store it in a io.BytesIO object.

        TODO: Add exception handling
        """
        if not self.contents:
            imageFile = fetch(self.URL).raw
            self.contents = io.BytesIO(imageFile)
        return self.contents

    @deprecated_args(site=None)
    def findDuplicateImages(self):
        """
        Find duplicates of the photo.

        Calculates the SHA1 hash and asks the MediaWiki api
        for a list of duplicates.

        TODO: Add exception handling, fix site thing
        """
        hashObject = hashlib.sha1()
        hashObject.update(self.downloadPhoto().getvalue())
        return [page.title(withNamespace=False) for page in
                self.site.allimages(sha1=base64.b16encode(hashObject.digest()))]

    def getTitle(self, fmt):
        """
        Populate format string with %(name)s entries using metadata.

        Note: this does not clean the title, so it may be unusable as
        a MediaWiki page title, and cause an API exception when used.

        @param fmt: format string
        @type fmt: unicode
        @return: formatted string
        @rtype: unicode
        """
        # FIXME: normalise the title so it is usable as a MediaWiki title.
        return fmt % self.metadata

    def getDescription(self, template, extraparams={}):
        """Generate a description for a file."""
        params = {}
        params.update(self.metadata)
        params.update(extraparams)
        description = u'{{%s\n' % template
        for key in sorted(params.keys()):
            value = params[key]
            if not key.startswith("_"):
                description = description + (
                    u'|%s=%s' % (key, self._safeTemplateValue(value))) + "\n"
        description = description + u'}}'

        return description

    def _safeTemplateValue(self, value):
        """Replace pipe (|) with {{!}}."""
        return value.replace("|", "{{!}}")


def CSVReader(fileobj, urlcolumn, site=None, *args, **kwargs):
    """Yield Photo objects for each row of a CSV file."""
    reader = csv.DictReader(fileobj, *args, **kwargs)
    for line in reader:
        yield Photo(line[urlcolumn], line, site=site)


class DataIngestionBot(pywikibot.Bot):

    """Data ingestion bot."""

    def __init__(self, reader, titlefmt, pagefmt,
                 site='deprecated_default_commons'):
        """
        Constructor.

        @param reader: Generator of Photos to process.
        @type reader: Photo page generator
        @param titlefmt: Title format
        @type titlefmt: basestring
        @param pagefmt: Page format
        @type pagefmt: basestring
        @param site: Target site for image upload.
            Use None to determine the site from the pages treated.
            Defaults to 'deprecated_default_commons' to use Wikimedia Commons
            for backwards compatibility reasons. Deprecated.
        @type site: APISite, 'deprecated_default_commons' or None
        """
        if site == 'deprecated_default_commons':
            warn('site=\'deprecated_default_commons\' is deprecated; '
                 'please specify a site or use site=None',
                 DeprecationWarning, 2)
            site = pywikibot.Site('commons', 'commons')
        super(DataIngestionBot, self).__init__(generator=reader, site=site)

        self.titlefmt = titlefmt
        self.pagefmt = pagefmt

    @property
    @deprecated('generator')
    def reader(self):
        """Get generator. Deprecated."""
        return self.generator

    @reader.setter
    @deprecated('generator')
    def reader(self, value):
        """Set generator. Deprecated."""
        self.generator = value

    def treat(self, photo):
        """Process each page."""
        duplicates = photo.findDuplicateImages()
        if duplicates:
            pywikibot.output(u"Skipping duplicate of %r" % duplicates)
            return duplicates[0]

        title = photo.getTitle(self.titlefmt)
        description = photo.getDescription(self.pagefmt)

        bot = UploadRobot(url=photo.URL,
                          description=description,
                          useFilename=title,
                          keepFilename=True,
                          verifyDescription=False,
                          targetSite=self.site)
        bot._contents = photo.downloadPhoto().getvalue()
        bot._retrieved = True
        bot.run()

        return title

    @deprecated("treat()")
    def doSingle(self):
        """Process one page."""
        return self.treat(next(self.reader))

    @classmethod
    def parseConfigurationPage(cls, configurationPage):
        """
        Parse a Page which contains the configuration.

        @param configurationPage: page with configuration
        @type configurationPage: L{pywikibot.Page}
        """
        configuration = {}
        # Set a bunch of defaults
        configuration['csvDialect'] = u'excel'
        configuration['csvDelimiter'] = ';'
        configuration['csvEncoding'] = u'Windows-1252'  # FIXME: Encoding hell

        templates = configurationPage.templatesWithParams()
        for (template, params) in templates:
            if template.title(withNamespace=False) == u'Data ingestion':
                for param in params:
                    (field, sep, value) = param.partition(u'=')

                    # Remove leading or trailing spaces
                    field = field.strip()
                    value = value.strip()
                    if not value:
                        value = None
                    configuration[field] = value

        return configuration


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()
    csv_dir = None

    for arg in local_args:
        if arg.startswith('-csvdir:'):
            csv_dir = arg[8:]
        else:
            genFactory.handleArg(arg)

    config_generator = genFactory.getCombinedGenerator()

    if not config_generator or not csv_dir:
        pywikibot.bot.suggest_help(
            missing_parameters=[] if csv_dir else ['-csvdir'],
            missing_generator=not config_generator)
        return False

    for config_page in config_generator:
        try:
            config_page.get()
        except pywikibot.NoPage:
            pywikibot.error('%s does not exist' % config_page)
            continue

        configuration = DataIngestionBot.parseConfigurationPage(config_page)

        filename = os.path.join(csv_dir, configuration['csvFile'])
        try:
            f = codecs.open(filename, 'r', configuration['csvEncoding'])
        except (IOError, OSError) as e:
            pywikibot.error('%s could not be opened: %s' % (filename, e))
        else:
            with f:
                files = CSVReader(f, urlcolumn='url',
                                  site=config_page.site,
                                  dialect=configuration['csvDialect'],
                                  delimiter=str(configuration['csvDelimiter']))

                bot = DataIngestionBot(files,
                                       configuration['titleFormat'],
                                       configuration['formattingTemplate'],
                                       site=None)
                bot.run()


if __name__ == "__main__":
    main()
