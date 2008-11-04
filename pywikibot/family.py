# -*- coding: utf-8  -*-

__version__='$Id$'

import config
import logging
import re
import urllib

logger = logging.getLogger("wiki")

# Parent class for all wiki families

class Family:
    def __init__(self):
        self.name = None
            # Updated from http://meta.wikimedia.org/wiki/Interwiki_sorting_order
        self.alphabetic = [
            'aa', 'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an', 'arc',
            'roa-rup', 'frp', 'as', 'ast', 'gn', 'av', 'ay', 'az', 'bm', 'bn',
            'zh-min-nan', 'map-bms', 'ba', 'be', 'be-x-old', 'bh', 'bcl', 'bi', 'bar', 'bo',
            'bs', 'br', 'bg', 'bxr', 'ca', 'cv', 'ceb', 'cs', 'ch', 'ny',
            'sn', 'tum', 'cho', 'co', 'za', 'cy', 'da', 'pdc', 'de', 'dv',
            'nv', 'dsb', 'dz', 'mh', 'et', 'el', 'eml', 'en', 'es', 'eo',
            'eu', 'ee', 'fa', 'fo', 'fr', 'fy', 'ff', 'fur', 'ga', 'gv',
            'gd', 'gl', 'ki', 'glk', 'gu', 'got', 'zh-classical', 'hak', 'xal', 'ko',
            'ha', 'haw', 'hy', 'hi', 'ho', 'hsb', 'hr', 'io', 'ig', 'ilo',
            'bpy', 'id', 'ia', 'ie', 'iu', 'ik', 'os', 'xh', 'zu', 'is',
            'it', 'he', 'jv', 'kl', 'pam', 'kn', 'kr', 'ka', 'ks', 'csb',
            'kk', 'kw', 'rw', 'ky', 'rn', 'sw', 'kv', 'kg', 'ht', 'kj',
            'ku', 'lad', 'lbe', 'lo', 'la', 'lv', 'lb', 'lt', 'lij', 'li',
            'ln', 'jbo', 'lg', 'lmo', 'hu', 'mk', 'mg', 'ml', 'mt', 'mi',
            'mr', 'mzn', 'ms', 'cdo', 'mo', 'mn', 'mus', 'my', 'nah', 'na',
            'fj', 'nl', 'nds-nl', 'cr', 'ne', 'new', 'ja', 'nap', 'ce', 'pih',
            'no', 'nn', 'nrm', 'nov', 'oc', 'or', 'om', 'ng', 'hz', 'ug',
            'uz', 'pa', 'pi', 'pag', 'pap', 'ps', 'km', 'pms', 'nds', 'pl',
            'pt', 'crh', 'ty', 'ksh', 'ro', 'rmy', 'rm', 'qu', 'ru', 'se',
            'sm', 'sa', 'sg', 'sc', 'sco', 'st', 'tn', 'sq', 'scn', 'si',
            'simple', 'sd', 'ss', 'sk', 'cu', 'sl', 'so', 'sr', 'sh', 'stq',
            'su', 'fi', 'sv', 'tl', 'ta', 'kab', 'roa-tara', 'tt', 'te', 'tet',
            'th', 'vi', 'ti', 'tg', 'tpi', 'to', 'chr', 'chy', 've', 'tr',
            'tk', 'tw', 'udm', 'bug', 'uk', 'ur', 'vec', 'vo', 'fiu-vro', 'wa',
            'vls', 'war', 'wo', 'wuu', 'ts', 'ii', 'yi', 'yo', 'zh-yue', 'cbk-zam',
            'diq', 'zea', 'bat-smg', 'zh',
        ]

        self.langs = {}
        
        # Wikimedia wikis all use "bodyContent" as the id of the <div>
        # element that contains the actual page content; change this for
        # wikis that use something else (e.g., mozilla family)
        self.content_id = "bodyContent"

        # A dictionary where keys are family codes that can be used in
        # inter-family interwiki links. Values are not used yet.
        # Generated from http://tools.wikimedia.de/~daniel/interwiki-en.txt:
        # remove interlanguage links from file, then run
        # f = open('interwiki-en.txt')
        # for line in f.readlines():
        #     s = line[:line.index('\t')]
        #     print (("            '%s':" % s).ljust(20) + ("'%s'," % s))
        
        # TODO: replace this with API interwikimap call
        self.known_families = {
            'abbenormal':       'abbenormal',
            'aboutccc':         'aboutccc',
            'acadwiki':         'acadwiki',
            'acronym':          'acronym',
            'advogato':         'advogato',
            'airwarfare':       'airwarfare',
            'aiwiki':           'aiwiki',
            'ajaxxab':          'ajaxxab',
            'alife':            'alife',
            'allwiki':          'allwiki',
            'annotation':       'annotation',
            'annotationwiki':   'annotationwiki',
            'archivecompress':  'archivecompress',
            'archivestream':    'archivestream',
            'arxiv':            'arxiv',
            'aspienetwiki':     'aspienetwiki',
            'atmwiki':          'atmwiki',
            'b':                'wikibooks',
            'battlestarwiki':   'battlestarwiki',
            'bemi':             'bemi',
            'benefitswiki':     'benefitswiki',
            'biblewiki':        'biblewiki',
            'bluwiki':          'bluwiki',
            'bmpcn':            'bmpcn',
            'boxrec':           'boxrec',
            'brasilwiki':       'brasilwiki',
            'brazilwiki':       'brazilwiki',
            'brickwiki':        'brickwiki',
            'bridgeswiki':      'bridgeswiki',
            'bryanskpedia':     'bryanskpedia',
            'bswiki':           'bswiki',
            'bugzilla':         'bugzilla',
            'buzztard':         'buzztard',
            'bytesmiths':       'bytesmiths',
            'c2':               'c2',
            'c2find':           'c2find',
            'cache':            'cache',
            'canyonwiki':       'canyonwiki',
            'canwiki':          'canwiki',
            'Ĉej':              'Ĉej',
            'cellwiki':         'cellwiki',
            'changemakers':     'changemakers',
            'chapter':          'chapter',
            'cheatswiki':       'cheatswiki',
            'chej':             'chej',
            'ciscavate':        'ciscavate',
            'cityhall':         'cityhall',
            'ckwiss':           'ckwiss',
            'cliki':            'cliki',
            'cmwiki':           'cmwiki',
            'cndbname':         'cndbname',
            'cndbtitle':        'cndbtitle',
            'codersbase':       'codersbase',
            'colab':            'colab',
            'comixpedia':       'comixpedia',
            'commons':          'commons',
            'communityscheme':  'communityscheme',
            'consciousness':    'consciousness',
            'corpknowpedia':    'corpknowpedia',
            'cpanelwiki':       'cpanelwiki',
            'choralwiki':       'choralwiki',
            'craftedbycarol':   'craftedbycarol',
            'crazyhacks':       'crazyhacks',
            'creationmatters':  'creationmatters',
            'creatureswiki':    'creatureswiki',
            'cxej':             'cxej',
            'dawiki':           'dawiki',
            'dcdatabase':       'dcdatabase',
            'dcma':             'dcma',
            'dejanews':         'dejanews',
            'delicious':        'delicious',
            'demokraatia':      'demokraatia',
            'devmo':            'devmo',
            'dictionary':       'dictionary',
            'dict':             'dict',
            'disinfopedia':     'disinfopedia',
            'diveintoosx':      'diveintoosx',
            'dndwiki':          'dndwiki',
            'docbook':          'docbook',
            'dolphinwiki':      'dolphinwiki',
            'doom_wiki':        'doom_wiki',
            'drae':             'drae',
            'drumcorpswiki':    'drumcorpswiki',
            'dwellerswiki':     'dwellerswiki',
            'dwjwiki':          'dwjwiki',
            'ebwiki':           'ebwiki',
            'eĉei':             'eĉei',
            'echei':            'echei',
            'echolink':         'echolink',
            'ecoreality':       'ecoreality',
            'ecxei':            'ecxei',
            'editcount':        'editcount',
            'efnetceewiki':     'efnetceewiki',
            'efnetcppwiki':     'efnetcppwiki',
            'efnetpythonwiki':  'efnetpythonwiki',
            'efnetxmlwiki':     'efnetxmlwiki',
            'elibre':           'elibre',
            'eljwiki':          'eljwiki',
            'emacswiki':        'emacswiki',
            'encyclopediadramatica':'encyclopediadramatica',
            'energiewiki':      'energiewiki',
            'eokulturcentro':   'eokulturcentro',
            'evowiki':          'evowiki',
            'fanimutationwiki': 'fanimutationwiki',
            'finalempire':      'finalempire',
            'finalfantasy':     'finalfantasy',
            'finnix':           'finnix',
            'firstwiki':        'firstwiki',
            'flickruser':       'flickruser',
            'floralwiki':       'floralwiki',
            'foldoc':           'foldoc',
            'forthfreak':       'forthfreak',
            'foundation':       'foundation',
            'foxwiki':          'foxwiki',
            'freebio':          'freebio',
            'freebsdman':       'freebsdman',
            'freeculturewiki':  'freeculturewiki',
            'freefeel':         'freefeel',
            'freekiwiki':       'freekiwiki',
            'gamewiki':         'gamewiki',
            'ganfyd':           'ganfyd',
            'gatorpedia':       'gatorpedia',
            'gausswiki':        'gausswiki',
            'gentoo-wiki':      'gentoo',
            'genwiki':          'genwiki',
            'glencookwiki':     'glencookwiki',
            'globalvoices':     'globalvoices',
            'glossarwiki':      'glossarwiki',
            'glossarywiki':     'glossarywiki',
            'golem':            'golem',
            'google':           'google',
            'googlegroups':     'googlegroups',
            'gotamac':          'gotamac',
            'greencheese':      'greencheese',
            'guildwiki':        'guildwiki',
            'h2wiki':           'h2wiki',
            'hammondwiki':      'hammondwiki',
            'haribeau':         'haribeau',
            'herzkinderwiki':   'herzkinderwiki',
            'hewikisource':     'hewikisource',
            'hkmule':           'hkmule',
            'holshamtraders':   'holshamtraders',
            'hrwiki':           'hrwiki',
            'hrfwiki':          'hrfwiki',
            'humancell':        'humancell',
            'hupwiki':          'hupwiki',
            'iawiki':           'iawiki',
            'imdbname':         'imdbname',
            'imdbtitle':        'imdbtitle',
            'infoanarchy':      'infoanarchy',
            'infobase':         'infobase',
            'infosecpedia':     'infosecpedia',
            'iso639-3':         'iso639-3',
            'iuridictum':       'iuridictum',
            'jameshoward':      'jameshoward',
            'jargonfile':       'jargonfile',
            'javanet':          'javanet',
            'javapedia':        'javapedia',
            'jefo':             'jefo',
            'jiniwiki':         'jiniwiki',
            'jspwiki':          'jspwiki',
            'jstor':            'jstor',
            'kamelo':           'kamelo',
            'karlsruhe':        'karlsruhe',
            'kerimwiki':        'kerimwiki',
            'kinowiki':         'kinowiki',
            'kmwiki':           'kmwiki',
            'knowhow':          'knowhow',
            'kontuwiki':        'kontuwiki',
            'koslarwiki':       'koslarwiki',
            'lanifexwiki':      'lanifexwiki',
            'linuxwiki':        'linuxwiki',
            'linuxwikide':      'linuxwikide',
            'liswiki':          'liswiki',
            'lojban':           'lojban',
            'lollerpedia':      'lollerpedia',
            'lovebox':          'lovebox',
            'lqwiki':           'lqwiki',
            'lugkr':            'lugkr',
            'lurkwiki':         'lurkwiki',
            'lutherwiki':       'lutherwiki',
            'lvwiki':           'lvwiki',
            'm':                'meta',
            'm-w':              'm-w',
            'mail':             'mail',
            'marveldatabase':   'marveldatabase',
            'mathsongswiki':    'mathsongswiki',
            'mbtest':           'mbtest',
            'meatball':         'meatball',
            'mediazilla':       'mediazilla',
            'memoryalpha':      'memoryalpha',
            'meta':             'meta',
            'metareciclagem':   'metareciclagem',
            'metaweb':          'metaweb',
            'metawiki':         'metawiki',
            'metawikipedia':    'metawikipedia',
            'mineralienatlas':  'mineralienatlas',
            'mjoo':             'mjoo',
            'moinmoin':         'moinmoin',
            'mozcom':           'mozcom',
            'mozillawiki':      'mozillawiki',
            'mozillazinekb':    'mozillazinekb',
            'mozwiki':          'mozwiki',
            'musicbrainz':      'musicbrainz',
            'muweb':            'muweb',
            'mw':               'mw',
            'mwod':             'mwod',
            'mwot':             'mwot',
            'myspace':          'myspace',
            'mytips':           'mytips',
            'n':                'wikinews',
            'netvillage':       'netvillage',
            'nkcells':          'nkcells',
            'nomad':            'nomad',
            'nosmoke':          'nosmoke',
            'nost':             'nost',
            'nswiki':           'nswiki',
            'oeis':             'oeis',
            'oldwikisource':    'oldwikisource',
            'onelook':          'onelook',
            'ourpeachtreecorners':'ourpeachtreecorners',
            'openfacts':        'openfacts',
            'opensourcesportsdirectory':'opensourcesportsdirectory',
            'openwetware':      'openwetware',
            'openwiki':         'openwiki',
            'opera7wiki':       'opera7wiki',
            'organicdesign':    'organicdesign',
            'orgpatterns':      'orgpatterns',
            'orthodoxwiki':     'orthodoxwiki',
            'osi reference model':'osi reference model',
            'ourmedia':         'ourmedia',
            'paganwiki':        'paganwiki',
            'panawiki':         'panawiki',
            'pangalacticorg':   'pangalacticorg',
            'patwiki':          'patwiki',
            'perlconfwiki':     'perlconfwiki',
            'perlnet':          'perlnet',
            'personaltelco':    'personaltelco',
            'phwiki':           'phwiki',
            'phpwiki':          'phpwiki',
            'pikie':            'pikie',
            'planetmath':       'planetmath',
            'pmeg':             'pmeg',
            'pmwiki':           'pmwiki',
            'purlnet':          'purlnet',
            'pythoninfo':       'pythoninfo',
            'pythonwiki':       'pythonwiki',
            'pywiki':           'pywiki',
            'psycle':           'psycle',
            'q':                'wikiquote',
            'quakewiki':        'quakewiki',
            'qwiki':            'qwiki',
            'r3000':            'r3000',
            'rakwiki':          'rakwiki',
            'raec':             'raec',
            'redwiki':          'redwiki',
            'revo':             'revo',
            'rfc':              'rfc',
            'rheinneckar':      'rheinneckar',
            'robowiki':         'robowiki',
            'rowiki':           'rowiki',
            'rtfm':             'rtfm',
            's':                'wikisource',
            's23wiki':          's23wiki',
            'scoutpedia':       'scoutpedia',
            'seapig':           'seapig',
            'seattlewiki':      'seattlewiki',
            'seattlewireless':  'seattlewireless',
            'seeds':            'seeds',
            'senseislibrary':   'senseislibrary',
            'sep11':            'sep11',
            'shakti':           'shakti',
            'shownotes':        'shownotes',
            'siliconvalley':    'siliconvalley',
            'slashdot':         'slashdot',
            'slskrex':          'slskrex',
            'smikipedia':       'smikipedia',
            'sockwiki':         'sockwiki',
            'sourceforge':      'sourceforge',
            'sourcextreme':     'sourcextreme',
            'squeak':           'squeak',
            'stockphotoss':     'stockphotoss',
            'strikiwiki':       'strikiwiki',
            'susning':          'susning',
            'svgwiki':          'svgwiki',
            'swinbrain':        'swinbrain',
            'swingwiki':        'swingwiki',
            'tabwiki':          'tabwiki',
            'takipedia':        'takipedia',
            'tamriel':          'tamriel',
            'tavi':             'tavi',
            'tclerswiki':       'tclerswiki',
            'technorati':       'technorati',
            'tejo':             'tejo',
            'terrorwiki':       'terrorwiki',
            'tesoltaiwan':      'tesoltaiwan',
            'thelemapedia':     'thelemapedia',
            'theo':             'theo',
            'theopedia':        'theopedia',
            'theowiki':         'theowiki',
            'theppn':           'theppn',
            'thinkwiki':        'thinkwiki',
            'tibiawiki':        'tibiawiki',
            'tmbw':             'tmbw',
            'tmnet':            'tmnet',
            'tmwiki':           'tmwiki',
            'toyah':            'toyah',
            'trash!italia':     'trash!italia',
            'turismo':          'turismo',
            'tviv':             'tviv',
            'twiki':            'twiki',
            'twistedwiki':      'twistedwiki',
            'tyvawiki':         'tyvawiki',
            'uncyclopedia':     'uncyclopedia',
            'underverse':       'underverse',
            'unreal':           'unreal',
            'ursine':           'ursine',
            'usej':             'usej',
            'usemod':           'usemod',
            'v':                'wikiversity',
            'videoville':       'videoville',
            'villagearts':      'villagearts',
            'visualworks':      'visualworks',
            'vkol':             'vkol',
            'voipinfo':         'voipinfo',
            'w':                'wikipedia',
            'warpedview':       'warpedview',
            'webdevwikinl':     'webdevwikinl',
            'webisodes':        'webisodes',
            'webseitzwiki':     'webseitzwiki',
            'wiki':             'wiki',
            'wikia':            'wikia',
            'wikianso':         'wikianso',
            'wikibooks':        'wikibooks',
            'wikichristian':    'wikichristian',
            'wikicities':       'wikicities',
            'wikif1':           'wikif1',
            'wikifur':          'wikifur',
            'wikikto':          'wikikto',
            'wikimac-de':       'wikimac-de',
            'wikimac-fr':       'wikimac-fr',
            'wikimedia':        'wikimedia',
            'wikinews':         'wikinews',
            'wikinfo':          'wikinfo',
            'wikinurse':        'wikinurse',
            'wikipaltz':        'wikipaltz',
            'wikipedia':        'wikipedia',
            'wikipediawikipedia':'wikipediawikipedia',
            'wikiquote':        'wikiquote',
            'wikireason':       'wikireason',
            'wikisophia':       'wikisophia',
            'wikisource':       'wikisource',
            'wikiscripts':      'wikiscripts',
            'wikispecies':      'wikispecies',
            'wikiti':           'wikiti',
            'wikitravel':       'wikitravel',
            'wikitree':         'wikitree',
            'wikiveg':          'wikiveg',
            'wikiversity':      'wikiversity',
            'wikiwikiweb':      'wikiwikiweb',
            'wikiworld':        'wikiworld',
            'wikt':             'wiktionary',
            'wiktionary':       'wiktionary',
            'wipipedia':        'wipipedia',
            'wlug':             'wlug',
            'wlwiki':           'wlwiki',
            'wmania':           'wmania',
            'wookieepedia':     'wookieepedia',
            'world66':          'world66',
            'wowwiki':          'wowwiki',
            'wqy':              'wqy',
            'wurmpedia':        'wurmpedia',
            'wznan':            'wznan',
            'xboxic':           'xboxic',
            'ypsieyeball':      'ypsieyeball',
            'zrhwiki':          'zrhwiki',
            'zum':              'zum',
            'zwiki':            'zwiki',
            'zzz wiki':         'zzz wiki',
        }

        # A list of disambiguation template names in different languages
        self.disambiguationTemplates = {
            '_default': []
        }

        # A list with the name of the category containing disambiguation
        # pages for the various languages. Only one category per language,
        # and without the namespace, so add things like:
        # 'en': "Disambiguation"
        self.disambcatname = {}

        # On most wikis page names must start with a capital letter, but some
        # languages don't use this.
        self.nocapitalize = []

        # attop is a list of languages that prefer to have the interwiki
        # links at the top of the page.
        self.interwiki_attop = []
        # on_one_line is a list of languages that want the interwiki links
        # one-after-another on a single line
        self.interwiki_on_one_line = []
        # String used as separator between interwiki links and the text
        self.interwiki_text_separator = '\r\n\r\n'

        # Similar for category
        self.category_attop = []
        # on_one_line is a list of languages that want the category links
        # one-after-another on a single line
        self.category_on_one_line = []
        # String used as separator between category links and the text
        self.category_text_separator = '\r\n\r\n'
        # When both at the bottom should categories come after interwikilinks?
        self.categories_last = []

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are put
        # after those, in code-alphabetical order.
        self.interwiki_putfirst = {}

        # Languages in interwiki_putfirst_doubled should have a number plus a list
        # of languages. If there are at least the number of interwiki links, all
        # languages in the list should be placed at the front as well as in the
        # normal list.
        self.interwiki_putfirst_doubled = {}

        # Some families, e. g. commons and meta, are not multilingual and
        # forward interlanguage links to another family (wikipedia).
        # These families can set this variable to the name of the target
        # family.
        self.interwiki_forward = None

        # Which language codes do no longer exist and by which language code should
        # they be replaced. If for example the language with code xx: now should get
        # code yy:, add {'xx':'yy'} to obsolete.
        # If all links to language xx: shall be removed, add {'xx': None}.
        self.obsolete = {}

        # Language codes of the largest wikis. They should be roughly sorted
        # by size.
        self.languages_by_size = []

        # Some languages belong to a group where the possibility is high that
        # equivalent articles have identical titles among the group.
        self.language_groups = {
            # languages that use chinese symbols
            'chinese': [
                'ja', 'wuu', 'zh', 'zh-classical', 'zh-yue'
            ],
            # languages that use the cyrillic alphabet
            'cyril': [
                'ab', 'ba', 'be', 'be-x-old', 'bg', 'ce', 'cv', 'kk', 'kv', 'ky', 'mk',
                'mn', 'os', 'ru', 'sr', 'tg', 'tk', 'udm', 'uk', 'xal'
            ],
            'scand': [
                'da', 'fo', 'is', 'no', 'sv'
            ],
        }

    def _addlang(self, code, location, namespaces = {}):
        """Add a new language to the langs and namespaces of the family.
           This is supposed to be called in the constructor of the family."""
        self.langs[code] = location

        for num, val in namespaces.items():
            self.namespaces[num][code]=val

    def get_known_families(self, site):
        return self.known_families

    def linktrail(self, code, fallback = '_default'):
        if self.linktrails.has_key(code):
            return self.linktrails[code]
        elif fallback:
            return self.linktrails[fallback]
        else:
            raise KeyError(
                "ERROR: linktrail in language %(language_code)s unknown"
                           % {'language_code': code})

    def namespace(self, code, ns_number, fallback='_default', all=False):
        if not self.isDefinedNS(ns_number):
            raise KeyError(
'ERROR: Unknown namespace %(ns_number)d for %(language_code)s:%(ns_name)s'
                           % {'ns_number': ns_number,
                              'language_code': code,
                              'ns_name': self.name})
        elif self.isNsI18N(ns_number, code):
            v = self.namespaces[ns_number][code]
            if type(v) is not list:
                v = [v,]
            if all and self.isNsI18N(ns_number, fallback):
                v2 = self.namespaces[ns_number][fallback]
                if type(v2) is list:
                    v.extend(v2)
                else:
                    v.append(v2)
        elif fallback and self.isNsI18N(ns_number, fallback):
            v = self.namespaces[ns_number][fallback]
            if type(v) is not list:
                v = [v,]
        else:
            raise KeyError(
'ERROR: title for namespace %(ns_number)d in language %(language_code)s unknown'
                           % {'ns_number': ns_number,
                              'language_code': code})
        if all:
            namespaces = list(set(v))
            # Lowercase versions of namespaces
            if code not in self.nocapitalize:
                namespaces.extend([ns[0].lower() + ns[1:]
                                   for ns in namespaces
                                   if ns and ns[0].lower() != ns[0].upper()])
            # Underscore versions of namespaces
            namespaces.extend([ns.replace(' ', '_')
                               for ns in namespaces if ns and ' ' in ns])
            return tuple(namespaces)
        else:
            return v[0]

    def isDefinedNS(self, ns_number):
        """Return True if the namespace has been defined in this family."""
        
        return self.namespaces.has_key(ns_number)

    def isNsI18N(self, ns_number, code):
        """Return True if the namespace has been internationalized.

        (it has a custom entry for a given language)

        """
        return self.namespaces[ns_number].has_key(code)

    def isDefinedNSLanguage(self, ns_number, code, fallback='_default'):
        """Return True if the namespace has been defined in this family
        for this language or its fallback.
        """
        if not self.isDefinedNS(ns_number):
            return False
        elif self.isNsI18N(ns_number, code):
            return True
        elif fallback and self.isNsI18N(ns_number, fallback):
            return True
        else:
            return False

    def normalizeNamespace(self, code, value):
        """Given a value, attempt to match it with all available namespaces,
        with default and localized versions. Sites may have more than one
        way to write the same namespace - choose the first one in the list.
        If nothing can be normalized, return the original value.
        """
        for ns, items in self.namespaces.iteritems():
            if items.has_key(code):
                v = items[code]
            elif items.has_key('_default'):
                v = items['_default']
            else:
                continue
            if type(v) is list:
                if value in v: return v[0]
            else:
                if value == v: return v
            if value == self.namespace('_default', ns):
                return self.namespace(code, ns)
        return value

    def getNamespaceIndex(self, lang, namespace):
        """Given a namespace, attempt to match it with all available
        namespaces. Sites may have more than one way to write the same
        namespace - choose the first one in the list. Returns namespace
        index or None.
        """
        namespace = namespace.lower()
        for n in self.namespaces.keys():
            try:
                nslist = self.namespaces[n][lang]
                if type(nslist) != type([]):
                    nslist = [nslist]
                for ns in nslist:
                    if ns.lower() == namespace:
                        return n
            except (KeyError,AttributeError):
                # The namespace has no localized name defined
                pass
        if lang != '_default':
            # This is not a localized namespace. Try if it
            # is a default (English) namespace.
            return self.getNamespaceIndex('_default', namespace)
        else:
            # give up
            return None

    def disambig(self, code, fallback = '_default'):
        if self.disambiguationTemplates.has_key(code):
            return self.disambiguationTemplates[code]
        elif fallback:
            return self.disambiguationTemplates[fallback]
        else:
            raise KeyError(
"ERROR: title for disambig template in language %(language_code)s unknown"
                           % {'language_code': code})

    # Returns the title of the special namespace in language 'code', taken from
    # dictionary above.
    # If the dictionary doesn't contain a translation, it will use language
    # 'fallback' (or, if fallback isn't given, MediaWiki default).
    # If you want the bot to crash in case of an unknown namespace name, use
    # fallback = None.
    def special_namespace(self, code, fallback = '_default'):
        return self.namespace(code, -1, fallback)

    def special_namespace_url(self, code, fallback = '_default'):
        encoded_title = self.namespace(code, -1, fallback).encode(self.code2encoding(code))
        return urllib.quote(encoded_title)

    def image_namespace(self, code, fallback = '_default'):
        return self.namespace(code, 6, fallback)

    def image_namespace_url(self, code, fallback = '_default'):
        encoded_title = self.namespace(code, 6, fallback).encode(self.code2encoding(code))
        return urllib.quote(encoded_title)

    def mediawiki_namespace(self, code, fallback = '_default'):
        return self.namespace(code, 8, fallback)

    def template_namespace(self, code, fallback = '_default'):
        return self.namespace(code, 10, fallback)

    def category_namespace(self, code, fallback = '_default'):
        return self.namespace(code, 14, fallback)

    def category_namespaces(self, code):
        return self.namespace(code, 14, all = True)

    # Redirect code can be translated.
    # Note that redirect codes are case-insensitive, so it is enough
    # to enter the code in lowercase here.
    redirect = {
        'ar': [u'تحويل'],
        'be-x-old': [u'перанакіраваньне'],
        'bg': [u'виж'],
        'bs': [u'preusmjeri'],
        'cy': [u'ail-cyfeirio'],
        'el': [u'ΑΝΑΚΑΤΕΥΘΥΝΣΗ'],
        'et': [u'suuna'],
        'eu': [u'bidali'],
        'fa': [u'تغییرمسیر'],
        'fi': [u'ohjaus', u'uudelleenohjaus'],
        'ga': [u'athsheoladh'],
        'he': [u'הפניה'],
        'id': [u'alih'],
        'is': [u'tilvísun'],
        'jv': [u'alih'],
        'ka': [u'გადამისამართება'],
        'kk': [u'айдау'],
        'mzn': [u'تغییرمسیر'],
        'nn': [u'omdiriger'],
        'ru': [u'перенаправление', u'перенапр'],
        'sk': [u'presmeruj'],
        'sr': [u'преусмери',u'Преусмери'], # Using lowercase only doesn't work?
        'su': [u'redirected', u'alih'],
        'tt': [u'yünältü'],
        'yi': [u'ווייטערפירן']
    }

    # So can be pagename code
    pagename = {
        'bg': [u'СТРАНИЦА'],
        'he': [u'שם הדף'],
        'kk': [u'БЕТАТАУЫ'],
        'nn': ['SIDENAMN','SIDENAVN'],
        'ru': [u'НАЗВАНИЕСТРАНИЦЫ'],
        'sr': [u'СТРАНИЦА'],
        'tt': [u'BİTİSEME']
    }

    pagenamee = {
        'he': [u'שם הדף מקודד'],
        'kk': [u'БЕТАТАУЫ2'],
        'nn': ['SIDENAMNE','SIDENAVNE'],
        'ru': [u'НАЗВАНИЕСТРАНИЦЫ2'],
        'sr': [u'СТРАНИЦЕ']
    }

    def pagenamecodes(self,code):
        pos = ['PAGENAME']
        pos2 = []
        if code in self.pagename.keys():
            pos = pos + self.pagename[code]
        elif code == 'als':
            return self.pagenamecodes('de')
        elif code == 'bm':
            return self.pagenamecodes('fr')
        for p in pos:
            pos2 += [p,p.lower()]
        return pos2

    def pagename2codes(self,code):
        pos = ['PAGENAME']
        pos2 = []
        if code in self.pagenamee.keys():
            pos = pos + self.pagenamee[code]
        elif code == 'als':
            return self.pagename2codes('de')
        elif code == 'bm':
            return self.pagename2codes('fr')
        for p in pos:
            pos2 += [p,p.lower()]
        return pos2

    # Methods
    def protocol(self, code):
        """
        Can be overridden to return 'https'.
        Other protocols are not supported.
        """
        return 'http'

    def hostname(self, code):
        return self.langs[code]

    def scriptpath(self, code):
        """The prefix used to locate scripts on this wiki.

        This is the value displayed when you enter {{SCRIPTPATH}} on a
        wiki page (often displayed at [[Help:Variables]] if the wiki has
        copied the master help page correctly).

        The default value is the one used on Wikimedia Foundation wikis,
        but needs to be overridden in the family file for any wiki that
        uses a different value.

        """
        return '/w'

    def path(self, code):
        return '%s/index.php' % self.scriptpath(code)

    def querypath(self, code):
        return '%s/query.php' % self.scriptpath(code)

    def apipath(self, code):
        return '%s/api.php' % self.scriptpath(code)

    def nicepath(self, code):
        return '/wiki/'

    def dbName(self, code):
        # returns the name of the MySQL database
        return '%s%s' % (code, self.name)

    # Which version of MediaWiki is used?
    def version(self, code):
        """Return MediaWiki version number as a string."""
        # Don't use this, use versionnumber() instead. This only exists
        # to not break family files.
        return "1.12alpha"

    def versionnumber(self, code):
        """Return an int identifying MediaWiki version.

        Currently this is implemented as returning the minor version
        number; i.e., 'X' in version '1.X.Y'

        """
        R = re.compile(r"(\d+).(\d+)")
        M = R.search(self.version(code))
        if not M:
            # Version string malformatted; assume it should have been 1.10
            return 10
        return 1000 * int(M.group(1)) + int(M.group(2)) - 1000

    def page_action_address(self, code, name, action):
        return '%s?title=%s&action=%s' % (self.path(code), name, action)

    def put_address(self, code, name):
        return '%s?title=%s&action=submit' % (self.path(code), name)

    def get_address(self, code, name):
        return '%s?title=%s&redirect=no' % (self.path(code), name)

    # The URL to get a page, in the format indexed by Google.
    def nice_get_address(self, code, name):
        return '/wiki/%s' % (name)

    def edit_address(self, code, name):
        return '%s?title=%s&action=edit' % (self.path(code), name)

    def purge_address(self, code, name):
        return '%s?title=%s&redirect=no&action=purge' % (self.path(code), name)

    def references_address(self, code, name):
        return '%s?title=%s:Whatlinkshere&target=%s&limit=%d' % (self.path(code), self.special_namespace_url(code), name, config.special_page_limit)

    def upload_address(self, code):
        return '%s?title=%s:Upload' % (self.path(code), self.special_namespace_url(code))

    def double_redirects_address(self, code, default_limit = True):
        if default_limit:
            return '%s?title=%s:DoubleRedirects' % (self.path(code), self.special_namespace_url(code))
        else:
            return '%s?title=%s:DoubleRedirects&limit=%d' % (self.path(code), self.special_namespace_url(code), config.special_page_limit)

    def broken_redirects_address(self, code, default_limit = True):
        if default_limit:
            return '%s?title=%s:BrokenRedirects' % (self.path(code), self.special_namespace_url(code))
        else:
            return '%s?title=%s:BrokenRedirects&limit=%d' % (self.path(code), self.special_namespace_url(code), config.special_page_limit)

    def allmessages_address(self, code):
        return "%s?title=%s:Allmessages&ot=html" % (self.path(code), self.special_namespace_url(code))

    def login_address(self, code):
        return '%s?title=%s:Userlogin&action=submit' % (self.path(code), self.special_namespace_url(code))

    def captcha_image_address(self, code, id):
        return '%s?title=%s:Captcha/image&wpCaptchaId=%s' % (self.path(code), self.special_namespace_url(code), id)

    def watchlist_address(self, code):
        return '%s?title=%s:Watchlist/edit' % (self.path(code), self.special_namespace_url(code))

    def contribs_address(self, code, target, limit=500, offset=''):
        return '%s?title=%s:Contributions&target=%s&limit=%s&offset=%s' % (self.path(code), self.special_namespace_url(code), target, limit, offset)

    def move_address(self, code):
        return '%s?title=%s:Movepage&action=submit' % (self.path(code), self.special_namespace_url(code))

    def delete_address(self, code, name):
        return '%s?title=%s&action=delete' % (self.path(code), name)

    def undelete_view_address(self, code, name, ts=''):
        return '%s?title=%s:Undelete&target=%s&timestamp=%s' % (self.path(code), self.special_namespace_url(code), name, ts)

    def undelete_address(self, code):
        return '%s?title=%s:Undelete&action=submit' % (self.path(code), self.special_namespace_url(code))

    def protect_address(self, code, name):
        return '%s?title=%s&action=protect' % (self.path(code), name)

    def unprotect_address(self, code, name):
        return '%s?title=%s&action=unprotect' % (self.path(code), name)

    def block_address(self, code):
      return '%s?title=%s:Blockip&action=submit' % (self.path(code), self.special_namespace_url(code))

    def unblock_address(self, code):
      return '%s?title=%s:Ipblocklist&action=submit' % (self.path(code), self.special_namespace_url(code))

    def blocksearch_address(self, code, name):
      return '%s?title=%s:Ipblocklist&action=search&ip=%s' % (self.path(code), self.special_namespace_url(code), name)

    def linksearch_address(self, code, link, limit=500, offset=0):
        return '%s?title=%s:Linksearch&limit=%d&offset=%d&target=%s' % (self.path(code), self.special_namespace_url(code), limit, offset, link)

    def version_history_address(self, code, name, limit = config.special_page_limit):
        return '%s?title=%s&action=history&limit=%d' % (self.path(code), name, limit)

    def export_address(self, code):
        return '%s?title=%s:Export' % (self.path(code), self.special_namespace_url('_default'))

    def query_address(self, code):
        return '%s?' % self.querypath(code)

    def api_address(self, code):
        return '%s?' % self.apipath(code)

    def search_address(self, code, query, limit=100, namespaces = None):
        """
        Constructs a URL for searching using Special:Search
        'namespaces' may be an int or a list; an empty list selects
        all namespaces.  Defaults to namespace 0
        """
        namespace_params = ''
        if namespaces is not None:
            if isinstance(namespaces, int):
                namespace_params = "&ns%d=1" % namespaces
            elif isinstance (namespaces, list):
                if len(namespaces) == 0:
                    # add all namespaces
                    namespaces = self.namespaces.keys()
                for i in namespaces:
                    if i > 0:
                        namespace_params = namespace_params + '&ns%d=1' % i

        return "%s?title=%s:Search&search=%s&limit=%d%s&fulltext=1" % (self.path(code),
                                                            self.special_namespace_url(code),
                                                            query,
                                                            limit,
                                                            namespace_params)

    def allpages_address(self, code, start, namespace = 0):
        if self.version(code)=="1.2":
            return '%s?title=%s:Allpages&printable=yes&from=%s' % (
                self.path(code), self.special_namespace_url(code), start)
        else:
            return '%s?title=%s:Allpages&from=%s&namespace=%s' % (
                self.path(code), self.special_namespace_url(code), start, namespace)

    def log_address(self, code, limit=50, mode = ''):
        return "%s?title=Special:Log&type=%s&user=&page=&limit=%d" % (self.path(code), mode, limit)

    def newpages_address(self, code, limit=50):
        return "%s?title=%s:Newpages&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def longpages_address(self, code, limit=500):
        return "%s?title=%s:Longpages&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def shortpages_address(self, code, limit=500):
        return "%s?title=%s:Shortpages&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def categories_address(self, code, limit=500):
        return "%s?title=%s:Categories&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def unusedfiles_address(self, code, limit=500):
            return "%s?title=%s:Unusedimages&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def deadendpages_address(self, code, limit=500):
        return "%s?title=%s:Deadendpages&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def ancientpages_address(self, code, limit=500):
        return "%s?title=%s:Ancientpages&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def lonelypages_address(self, code, limit=500):
        return "%s?title=%s:Lonelypages&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def unwatchedpages_address(self, code, limit=500):
        return "%s?title=%s:Unwatchedpages&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def uncategorizedcategories_address(self, code, limit=500):
        return "%s?title=%s:Uncategorizedcategories&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def uncategorizedimages_address(self, code, limit=500):
        return "%s?title=%s:Uncategorizedimages&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def uncategorizedpages_address(self, code, limit=500):
        return "%s?title=%s:Uncategorizedpages&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def unusedcategories_address(self, code, limit=500):
        return "%s?title=%s:Unusedcategories&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def withoutinterwiki_address(self, code, limit=500):
        return "%s?title=%s:Withoutinterwiki&limit=%d" % (self.path(code), self.special_namespace_url(code), limit)

    def code2encoding(self, code):
        """Return the encoding for a specific language wiki"""
        return 'utf-8'

    def code2encodings(self, code):
        """Return a list of historical encodings for a specific language
           wiki"""
        return self.code2encoding(code),

    # aliases
    def encoding(self, code):
        """Return the encoding for a specific language wiki"""
        return self.code2encoding(code)

    def encodings(self, code):
        """Return a list of historical encodings for a specific language
           wiki"""
        return self.code2encodings(code)

    def __cmp__(self, otherfamily):
        try:
            return cmp(self.name, otherfamily.name)
        except AttributeError:
            return cmp(id(self), id(otherfamily))

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return 'Family("%s")' % self.name

    def RversionTab(self, code):
        """Change this to some regular expression that shows the page we
        found is an existing page, in case the normal regexp does not work."""
        return None

    def has_query_api(self,code):
        """Is query.php installed in the wiki?"""
        return False

    def shared_image_repository(self, code):
        """Return the shared image repository, if any."""
        return (None, None)
