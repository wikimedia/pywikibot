import family, config

# The wikitravel family

# Translation used on all wikitravels for the 'article' text.
# A language not mentioned here is not known by the robot

__version__ = '$Id$'

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikitravel'
        self.langs = {
            'ca':'ca',
            'de':'de',
            'en':'en',
            'eo':'eo',
            'es':'es',
            'fi':'fi',
            'fr':'fr',
            'he':'he',
            'hi':'hi',
            'hu':'hu',
            'it':'it',
            'ja':'ja',
            'nl':'nl',
            'pl':'pl',
            'pt':'pt',
            'ro':'ro',
            'ru':'ru',
            'sv':'sv',
        }
        self.namespaces[4] = {
            '_default': [u'Wikitravel', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'Wikitravel talk', self.namespaces[5]['_default']],
            'de': u'Wikitravel Diskussion',
        }

        # A few selected big languages for things that we do not want to loop over
        # all languages. This is only needed by the titletranslate.py module, so
        # if you carefully avoid the options, you could get away without these
        # for another wikimedia family.

        self.languages_by_size = ['en','fr','ro']

    def hostname(self,code):
        return 'wikitravel.org'

    def scriptpath(self, code):
        return '/wiki/%s' % code

    def apipath(self, code):
        raise NotImplementedError(
            "The wikitravel family does not support api.php")

    def shared_image_repository(self, code):
        return ('wikitravel_shared', 'wikitravel_shared')

    def version(self, code):
        return "1.10.1"
