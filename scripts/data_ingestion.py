#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
A generic bot to do data ingestion (batch uploading) of photos or other files.

In addition it installs related metadata. The uploading is primarily from a url
to a wiki-site.

Required configuration files
============================
    - a 'Data ingestion' template on a wiki site that specifies the name of a
      csv file, and csv configuration values.
    - a csv file that specifies each file to upload, the file's copy-from URL
      location, and some metadata.

Required parameters
===================
The following parameters are required. The 'csvdir' and the 'page:csvFile' will
be joined creating a path to a csv file that should contain specified
information about files to upload.

-csvdir           A directory path to csv files

-page             A wiki path to templates. One of the templates at this
                  location must be a 'Data ingestion' template with the
                  following parameters.

                      Required parameters
                          csvFile

                      Optional parameters
                          sourceFormat
                              options: 'csv'

                          sourceFileKey
                              options: 'StockNumber'

                          csvDialect
                              options: 'excel', ''

                          csvDelimiter
                              options: any delimiter, ',' is most common

                          csvEncoding
                              options: 'utf8', 'Windows-1252'

                          formattingTemplate

                          titleFormat


Example 'Data ingestion' template
=================================
.. code::

    {{Data ingestion
    |sourceFormat=csv
    |csvFile=csv_ingestion.csv
    |sourceFileKey=%(StockNumber)
    |csvDialect=
    |csvDelimiter=,
    |csvEncoding=utf8
    |formattingTemplate=Template:Data ingestion test configuration
    |titleFormat=%(name)s - %(set)s.%(_ext)s
    }}


Csv file
========
A full example can be found at tests/data/csv_ingestion.csv
The 'url' field is the location a file will be copied from.

csv field Headers::

    description.en,source,author,license,set,name,url


Usage
=====
.. code::

    python pwb.py data_ingestion -csvdir:<local_dir/> -page:<cfg_page_on_wiki>


Example
=======
Warning! Put it in one line, otherwise it won't work correctly.

.. code::

    python pwb.py data_ingestion \
        -csvdir:"test/data" \
        -page:"User:<Your-Username>/data_ingestion_test_template"

"""
#
# (C) Pywikibot team, 2012-2020
#
# Distributed under the terms of the MIT license.
#
import base64
import codecs
import csv
import hashlib
import io
import os
import posixpath

from urllib.parse import urlparse
from warnings import warn

import pywikibot

from pywikibot.comms.http import fetch
from pywikibot import pagegenerators
from pywikibot.specialbots import UploadRobot
from pywikibot.tools import deprecated, deprecated_args, PYTHON_VERSION

if PYTHON_VERSION >= (3, 9):
    Tuple = tuple
else:
    from typing import Tuple


class Photo(pywikibot.FilePage):

    """Represents a Photo (or other file), with metadata, to be uploaded."""

    def __init__(self, URL: str, metadata: dict, site=None):
        """
        Initializer.

        @param URL: URL of photo
        @param metadata: metadata about the photo that can be referred to
            from the title & template
        @param site: target site
        @type site: pywikibot.site.APISite

        """
        self.URL = URL
        self.metadata = metadata
        self.metadata['_url'] = URL
        self.metadata['_filename'] = filename = posixpath.split(
            urlparse(URL)[2])[1]
        self.metadata['_ext'] = ext = filename.split('.')[-1]
        if ext == filename:
            self.metadata['_ext'] = None
        self.contents = None

        if not site:
            site = pywikibot.Site('commons', 'commons')

        # default title
        super().__init__(site, self.getTitle('%(_filename)s.%(_ext)s'))

    def downloadPhoto(self):
        """
        Download the photo and store it in an io.BytesIO object.

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
        return [page.title(with_ns=False) for page in
                self.site.allimages(
                    sha1=base64.b16encode(hashObject.digest()))]

    def getTitle(self, fmt: str) -> str:
        """
        Populate format string with %(name)s entries using metadata.

        Note: this does not clean the title, so it may be unusable as
        a MediaWiki page title, and cause an API exception when used.

        @param fmt: format string
        @return: formatted string
        """
        # FIXME: normalise the title so it is usable as a MediaWiki title.
        return fmt % self.metadata

    def getDescription(self, template, extraparams={}):
        """Generate a description for a file."""
        params = {}
        params.update(self.metadata)
        params.update(extraparams)
        description = '{{%s\n' % template
        for key in sorted(params.keys()):
            value = params[key]
            if not key.startswith('_'):
                description += ('|{}={}\n'.format(
                    key, self._safeTemplateValue(value)))
        description += '}}'

        return description

    def _safeTemplateValue(self, value):
        """Replace pipe (|) with {{!}}."""
        return value.replace('|', '{{!}}')


def CSVReader(fileobj, urlcolumn, site=None, *args, **kwargs):
    """Yield Photo objects for each row of a CSV file."""
    reader = csv.DictReader(fileobj, *args, **kwargs)
    for line in reader:
        yield Photo(line[urlcolumn], line, site=site)


class DataIngestionBot(pywikibot.Bot):

    """Data ingestion bot."""

    def __init__(self, reader, titlefmt: str, pagefmt: str,
                 site='deprecated_default_commons'):
        """
        Initializer.

        @param reader: Generator of Photos to process.
        @type reader: Photo page generator
        @param titlefmt: Title format
        @param pagefmt: Page format
        @param site: Target site for image upload.
            Use None to determine the site from the pages treated.
            Defaults to 'deprecated_default_commons' to use Wikimedia Commons
            for backwards compatibility reasons. Deprecated.
        @type site: pywikibot.site.APISite, 'deprecated_default_commons' or
            None
        """
        if site == 'deprecated_default_commons':
            warn("site='deprecated_default_commons' is deprecated; "
                 'please specify a site or use site=None',
                 DeprecationWarning, 2)
            site = pywikibot.Site('commons', 'commons')
        super().__init__(generator=reader, site=site)

        self.titlefmt = titlefmt
        self.pagefmt = pagefmt

    @property
    @deprecated('generator', since='20150508', future_warning=True)
    def reader(self):
        """Deprecated generator."""
        return self.generator

    @reader.setter
    @deprecated('generator', since='20150508', future_warning=True)
    def reader(self, value):
        self.generator = value

    def treat(self, photo):
        """
        Process each page.

        1. Check for existing duplicates on the wiki specified in self.site.
        2. If duplicates are found, then skip uploading.
        3. Download the file from photo.URL and upload the file to self.site.
        """
        duplicates = photo.findDuplicateImages()
        if duplicates:
            pywikibot.output('Skipping duplicate of {!r}'
                             .format(duplicates))
            return duplicates[0]

        title = photo.getTitle(self.titlefmt)
        description = photo.getDescription(self.pagefmt)

        bot = UploadRobot(url=photo.URL,
                          description=description,
                          use_filename=title,
                          keep_filename=True,
                          verify_description=False,
                          target_site=self.site)
        bot._contents = photo.downloadPhoto().getvalue()
        bot._retrieved = True
        bot.run()

        return title

    @deprecated('treat()', since='20150118', future_warning=True)
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
        configuration['csvDialect'] = 'excel'
        configuration['csvDelimiter'] = ';'
        configuration['csvEncoding'] = 'Windows-1252'  # FIXME: Encoding hell

        templates = configurationPage.templatesWithParams()
        for (template, params) in templates:
            if template.title(with_ns=False) == 'Data ingestion':
                for param in params:
                    (field, sep, value) = param.partition('=')

                    # Remove leading or trailing spaces
                    field = field.strip()
                    value = value.strip()
                    if not value:
                        value = None
                    configuration[field] = value

        return configuration


def main(*args: Tuple[str, ...]):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    """
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()
    csv_dir = None

    for arg in local_args:
        if arg.startswith('-csvdir:'):
            csv_dir = arg[8:]
        else:
            genFactory.handleArg(arg)

    config_generator = genFactory.getCombinedGenerator()

    if pywikibot.bot.suggest_help(
            missing_parameters=[] if csv_dir else ['-csvdir'],
            missing_generator=not config_generator):
        return

    for config_page in config_generator:
        try:
            config_page.get()
        except pywikibot.NoPage:
            pywikibot.error('{} does not exist'.format(config_page))
            continue

        configuration = DataIngestionBot.parseConfigurationPage(config_page)

        filename = os.path.join(csv_dir, configuration['csvFile'])
        try:
            f = codecs.open(filename, 'r', configuration['csvEncoding'])
        except (IOError, OSError) as e:
            pywikibot.error('{} could not be opened: {}'.format(filename, e))
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


if __name__ == '__main__':
    main()
