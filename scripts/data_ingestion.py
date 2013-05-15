#!/usr/bin/python
# -*- coding: utf-8  -*-
'''
A generic bot to do data ingestion (batch uploading) to Commons

'''
import pywikibot
import posixpath, urlparse
import urllib
import hashlib, base64
import StringIO

class Photo(object):
    '''
    Represents a Photo (or other file), with metadata, to upload to Commons.

    The constructor takes two parameters: URL (string) and metadata (dict with str:str key:value pairs)
    that can be referred to from the title & template generation.


    '''
    def __init__(self, URL, metadata):
        self.URL = URL
        self.metadata = metadata
        self.metadata["_url"] = URL
        self.metadata["_filename"] = filename = posixpath.split(urlparse.urlparse(URL)[2])[1]
        self.metadata["_ext"] = ext = filename.split(".")[-1]
        if ext == filename:
            self.metadata["_ext"] = ext = None
        self.contents = None

    def downloadPhoto(self):
        '''
        Download the photo and store it in a StringIO.StringIO object.

        TODO: Add exception handling
        '''
        if not self.contents:
            imageFile=urllib.urlopen(self.URL).read()
            self.contents = StringIO.StringIO(imageFile)
        return self.contents

    def findDuplicateImages(self, site = pywikibot.getSite(u'commons', u'commons')):
        '''
        Takes the photo, calculates the SHA1 hash and asks the mediawiki api for a list of duplicates.

        TODO: Add exception handling, fix site thing
        '''
        hashObject = hashlib.sha1()
        hashObject.update(self.downloadPhoto().getvalue())
        return site.getFilesFromAnHash(base64.b16encode(hashObject.digest()))

    def getTitle(self, fmt):
        """
        Given a format string with %(name)s entries, returns the string formatted with metadata
        """
        return fmt % self.metadata

    def getDescription(self, template, extraparams={}):
        '''
        Generate a description for a file
        '''

        params = {}
        params.update(self.metadata)
        params.update(extraparams)
        description = u'{{%s\n' % template
        for key in sorted(params.keys()):
            value = params[key]
            if not key.startswith("_"):
                description = description + (u'|%s=%s' % (key, self._safeTemplateValue(value))) + "\n"
        description = description + u'}}'

        return description

    def _safeTemplateValue(self, value):
        return value.replace("|", "{{!}}")

def CSVReader(fileobj, urlcolumn, *args, **kwargs):
    import csv
    reader = csv.DictReader(fileobj, *args, **kwargs)

    for line in reader:
        yield Photo(line[urlcolumn], line)

class DataIngestionBot:
    def __init__(self, reader, titlefmt, pagefmt, site=pywikibot.getSite(u'commons', u'commons')):
        self.reader = reader
        self.titlefmt = titlefmt
        self.pagefmt = pagefmt
        self.site = site

    def _doUpload(self, photo):
        duplicates = photo.findDuplicateImages(self.site)
        if duplicates:
            pywikibot.output(u"Skipping duplicate of %r" % (duplicates, ))
            return duplicates[0]

        title = photo.getTitle(self.titlefmt)
        description = photo.getDescription(self.pagefmt)

        bot = upload.UploadRobot(url = photo.URL,
                                 description = description,
                                 useFilename = title,
                                 keepFilename = True,
                                 verifyDescription = False,
                                 targetSite = self.site)
        bot._contents = photo.downloadPhoto().getvalue()
        bot._retrieved = True
        bot.run()

        return title

    def doSingle(self):
        return self._doUpload(self.reader.next())

    def run(self):
        for photo in self.reader:
            self._doUpload(photo)

if __name__=="__main__":
    reader = CSVReader(open('tests/data/csv_ingestion.csv'), 'url')
    bot = DataIngestionBot(reader, "%(name)s - %(set)s.%(_ext)s", ":user:valhallasw/test_template", pywikibot.getSite('test', 'test'))
    bot.run()

"""
class DataIngestionBot:
    def __init__(self, configurationPage):
        '''

        '''
        self.site = configurationPage.site()
        self.configuration = self.parseConfigurationPage(configurationPage)

    def parseConfigurationPage(self, configurationPage):
        '''
        Expects a pywikibot.page object "configurationPage" which contains the configuration
        '''
        configuration  = {}
        # Set a bunch of defaults
        configuration['csvDialect']=u'excel'
        configuration['csvDelimiter']=';'
        configuration['csvEncoding']=u'Windows-1252' #FIXME: Encoding hell

        templates = configurationPage.templatesWithParams()
        for (template, params) in templates:
            if template==u'Data ingestion':
                for param in params:
                    (field, sep, value) = param.partition(u'=')

                    # Remove leading or trailing spaces
                    field = field.strip()
                    value = value.strip()
                    configuration[field] = value
        print configuration
        return configuration


    def downloadPhoto(self, photoUrl = ''):
        '''
        Download the photo and store it in a StrinIO.StringIO object.

        TODO: Add exception handling
        '''
        imageFile=urllib.urlopen(photoUrl).read()
        return StringIO.StringIO(imageFile)

    def findDuplicateImages(self, photo = None, site = pywikibot.getSite(u'commons', u'commons')):
        '''
        Takes the photo, calculates the SHA1 hash and asks the mediawiki api for a list of duplicates.

        TODO: Add exception handling, fix site thing
        '''
        hashObject = hashlib.sha1()
        hashObject.update(photo.getvalue())
        return site.getFilesFromAnHash(base64.b16encode(hashObject.digest()))

    def getTitle(self, metadata):
        '''
        Build a title.
        Have titleFormat to indicate how the title would look.
        We need to be able to strip off stuff if it's too long. configuration.get('maxTitleLength')
        '''

        #FIXME: Make this configurable.
        title = self.configuration.get('titleFormat') % metadata

        description = metadata.get(u'dc:title')
        identifier = metadata.get(u'dc:identifier')

        if len(description)>120:
            description = description[0 : 120]

        title = u'%s - %s.jpg' % (description, identifier)

        return flickrripper.cleanUpTitle(title)

    def cleanDate(self, field):
        '''
        A function to do date clean up.
        '''
        # Empty, make it really empty
        if field==u'-':
            return u''
        # TODO: Circa
        # TODO: Period

        return field

    def cleanEmptyField(self, field):
        return field

    def procesFile(self, metadata):
        # FIXME: Do some metadata enrichment
        #metadata = getEuropeanaMetadata(metadata)

        fileLocation = metadata.get(self.configuration.get('sourceFileField'))

        photo = self.downloadPhoto(fileLocation)
        duplicates = self.findDuplicateImages(photo)

        # We don't want to upload dupes
        if duplicates:
            pywikibot.output(u'Found duplicate image at %s' % duplicates.pop())
            # The file is at Commons so return True
            return True

        # FIXME: Do some checking to see if the title already exists

        title = self.getTitle(metadata)
        description = self.getDescription(metadata)


        pywikibot.output(u'Preparing upload for %s.' % title)
        pywikibot.output(description)

        bot = upload.UploadRobot(url=fileLocation, description=description, useFilename=title, keepFilename=True, verifyDescription=False, targetSite = self.site)
        bot.run()

    def processCSV(self):
        database = {}

        reader = csv.DictReader(open(self.configuration.get('csvFile'), "rb"), dialect=self.configuration.get('csvDialect'), delimiter=self.configuration.csvDelimiter)
        # FIXME : Encoding problems http://docs.python.org/library/csv.html#csv-examples
        for row in reader:
            self.metadataCSV(row)
            self.processFile(metadata)

    def run(self):
        '''
        Do crap
        '''
        if not self.configuration.get('sourceFormat'):
            pywikibot.output(u'The field "sourceFormat" is not set')
            return False

        if self.configuration.get('sourceFormat')==u'csv':
            self.processCSV()
        else:
            pywikibot.output(u'%s is not a supported source format')

def main(args):
    generator = None;

    genFactory = pagegenerators.GeneratorFactory()

    for arg in pywikibot.handleArgs():
        genFactory.handleArg(arg)

    generator = genFactory.getCombinedGenerator()
    if not generator:
        return False

    for page in generator:
        bot  = DataIngestionBot(page)
        bot.run()

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    finally:
        print "All done!"
"""
