#!/usr/bin/env python3
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
.. code-block:: python

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
.. code-block:: python

   python pwb.py data_ingestion -csvdir:<local_dir/> -page:<cfg_page_on_wiki>


Example
=======
.. code-block:: python

   pwb.py data_ingestion -csvdir:"test/data" -page:"User:<Your-Username>/data_ingestion_test_template"

.. warning:: Put it in one line, otherwise it won't work correctly.

"""  # noqa: E501
#
# (C) Pywikibot team, 2012-2022
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
from typing import Any, BinaryIO, Optional
from urllib.parse import urlparse

import pywikibot
from pywikibot import pagegenerators
from pywikibot.backports import Dict, List
from pywikibot.comms.http import fetch
from pywikibot.exceptions import NoPageError
from pywikibot.specialbots import UploadRobot


class Photo(pywikibot.FilePage):

    """Represents a Photo (or other file), with metadata, to be uploaded."""

    def __init__(self, url: str, metadata: Dict[str, Any],
                 site: Optional[pywikibot.site.APISite] = None) -> None:
        """
        Initializer.

        :param url: URL of photo
        :param metadata: metadata about the photo that can be referred to
            from the title & template
        :param site: target site
        """
        self.URL = url
        self.metadata = metadata
        self.metadata['_url'] = url
        self.metadata['_filename'] = filename = posixpath.split(
            urlparse(url)[2])[1]
        ext = filename.split('.')[-1]
        self.metadata['_ext'] = None if ext == filename else ext
        self.contents = None

        if not site:
            site = pywikibot.Site('commons')

        # default title
        super().__init__(site, self.get_title('%(_filename)s.%(_ext)s'))

    def download_photo(self) -> BinaryIO:
        """
        Download the photo and store it in an io.BytesIO object.

        TODO: Add exception handling
        """
        if not self.contents:
            image_file = fetch(self.URL).content
            self.contents = io.BytesIO(image_file)
        return self.contents

    def find_duplicate_images(self) -> List[str]:
        """
        Find duplicates of the photo.

        Calculates the SHA1 hash and asks the MediaWiki API
        for a list of duplicates.

        TODO: Add exception handling, fix site thing
        """
        hash_object = hashlib.sha1()
        hash_object.update(self.download_photo().getvalue())
        return [page.title(with_ns=False)
                for page in self.site.allimages(
                    sha1=base64.b16encode(hash_object.digest()))]

    def get_title(self, fmt: str) -> str:
        """
        Populate format string with %(name)s entries using metadata.

        .. note:: this does not clean the title, so it may be unusable as
           a MediaWiki page title, and cause an API exception when used.

        :param fmt: format string
        :return: formatted string
        """
        # FIXME: normalise the title so it is usable as a MediaWiki title.
        return fmt % self.metadata

    def get_description(self, template,
                        extraparams: Optional[Dict[str, str]] = None) -> str:
        """Generate a description for a file."""
        params = {}
        params.update(self.metadata)
        params.update(extraparams or {})
        description = '{{%s\n' % template
        for key in sorted(params.keys()):
            value = params[key]
            if not key.startswith('_'):
                description += '|{}={}\n'.format(
                    key, self._safe_template_value(value))
        description += '}}'

        return description

    @staticmethod
    def _safe_template_value(value: str) -> str:
        """Replace pipe (|) with {{!}}."""
        return value.replace('|', '{{!}}')


def CSVReader(fileobj, urlcolumn, site=None, *args, **kwargs):  # noqa: N802
    """Yield Photo objects for each row of a CSV file."""
    reader = csv.DictReader(fileobj, *args, **kwargs)
    for line in reader:
        yield Photo(line[urlcolumn], line, site=site)


class DataIngestionBot(pywikibot.Bot):

    """Data ingestion bot."""

    def __init__(self, titlefmt: str, pagefmt: str, **kwargs) -> None:
        """
        Initializer.

        :param titlefmt: Title format
        :param pagefmt: Page format
        """
        super().__init__(**kwargs)
        self.titlefmt = titlefmt
        self.pagefmt = pagefmt

    def treat(self, page) -> None:
        """Process each page.

        1. Check for existing duplicates on the wiki specified in self.site.
        2. If duplicates are found, then skip uploading.
        3. Download the file from photo.URL and upload the file to self.site.
        """
        duplicates = page.find_duplicate_images()
        if duplicates:
            pywikibot.info(f'Skipping duplicate of {duplicates!r}')
            return

        title = page.get_title(self.titlefmt)
        description = page.get_description(self.pagefmt)

        bot = UploadRobot(url=page.URL,
                          description=description,
                          use_filename=title,
                          keep_filename=True,
                          verify_description=False,
                          target_site=self.site)
        bot._contents = page.download_photo().getvalue()
        bot._retrieved = True
        bot.run()

    @classmethod
    def parse_configuration_page(cls, configuration_page) -> Dict[str, str]:
        """
        Parse a Page which contains the configuration.

        :param configuration_page: page with configuration
        :type configuration_page: :py:obj:`pywikibot.Page`
        """
        # Set a bunch of defaults
        configuration = {
            'csvDialect': 'excel',
            'csvDelimiter': ';',
            'csvEncoding': 'Windows-1252',  # FIXME: Encoding hell
        }

        templates = configuration_page.templatesWithParams()
        for (template, params) in templates:
            if template.title(with_ns=False) != 'Data ingestion':
                continue

            for param in params:
                field, _, value = param.partition('=')

                # Remove leading or trailing spaces
                field = field.strip()
                value = value.strip() or None
                configuration[field] = value

        return configuration


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    csv_dir = None
    unknown = []

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    gen_factory = pagegenerators.GeneratorFactory()

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    local_args = gen_factory.handle_args(local_args)
    for arg in local_args:
        opt, _, value = arg.partition(':')
        if opt == '-csvdir:':
            csv_dir = value
        else:
            unknown.append(arg)

    config_generator = gen_factory.getCombinedGenerator()

    if pywikibot.bot.suggest_help(
            missing_parameters=None if csv_dir else ['-csvdir'],
            missing_generator=not config_generator,
            unknown_parameters=unknown):
        return

    for config_page in config_generator:
        try:
            config_page.get()
        except NoPageError:
            pywikibot.error(f'{config_page} does not exist')
            continue

        configuration = DataIngestionBot.parse_configuration_page(config_page)

        filename = os.path.join(csv_dir, configuration['csvFile'])
        try:
            f = codecs.open(filename, 'r', configuration['csvEncoding'])
        except OSError as e:
            pywikibot.error(f'{filename} could not be opened: {e}')
        else:
            with f:
                files = CSVReader(f, urlcolumn='url',
                                  site=config_page.site,
                                  dialect=configuration['csvDialect'],
                                  delimiter=str(configuration['csvDelimiter']))

                bot = DataIngestionBot(configuration['titleFormat'],
                                       configuration['formattingTemplate'],
                                       generator=files)
                bot.run()


if __name__ == '__main__':
    main()
