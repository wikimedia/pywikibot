# -*- coding: utf-8  -*-

#
# (C) Pywikipedia bot team, 2004-2010
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import config2 as config
import logging
import re
import urllib

import pywikibot

logger = logging.getLogger("pywiki.wiki.family")

# Parent class for all wiki families

class Family:
    def __init__(self):
        self.name = None

        # Updated from http://meta.wikimedia.org/wiki/Interwiki_sorting_order
        self.alphabetic = [
            'ace', 'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an', 'arc',
            'roa-rup', 'frp', 'as', 'ast', 'gn', 'av', 'ay', 'az', 'bm', 'bn',
            'zh-min-nan', 'nan', 'map-bms', 'ba', 'be', 'be-x-old', 'bh', 'bcl',
            'bi', 'bar', 'bo', 'bs', 'br', 'bg', 'bxr', 'ca', 'cv', 'ceb', 'cs',
            'ch', 'cbk-zam', 'ny', 'sn', 'tum', 'cho', 'co', 'cy', 'da', 'dk',
            'pdc', 'de', 'dv', 'nv', 'dsb', 'dz', 'mh', 'et', 'el', 'eml', 'en',
            'myv', 'es', 'eo', 'ext', 'eu', 'ee', 'fa', 'hif', 'fo', 'fr', 'fy',
            'ff', 'fur', 'ga', 'gv', 'gd', 'gl', 'gan', 'ki', 'glk', 'gu',
            'got', 'hak', 'xal', 'ko', 'ha', 'haw', 'hy', 'hi', 'ho', 'hsb',
            'hr', 'io', 'ig', 'ilo', 'bpy', 'id', 'ia', 'ie', 'iu', 'ik', 'os',
            'xh', 'zu', 'is', 'it', 'he', 'jv', 'kl', 'kn', 'kr', 'pam', 'krc',
            'ka', 'ks', 'csb', 'kk', 'kw', 'rw', 'ky', 'rn', 'sw', 'kv', 'kg',
            'ht', 'ku', 'kj', 'lad', 'lbe', 'lo', 'la', 'lv', 'lb', 'lt', 'lij',
            'li', 'ln', 'jbo', 'lg', 'lmo', 'hu', 'mk', 'mg', 'ml', 'mt', 'mi',
            'mr', 'arz', 'mzn', 'ms', 'cdo', 'mwl', 'mdf', 'mo', 'mn', 'mus',
            'my', 'nah', 'na', 'fj', 'nl', 'nds-nl', 'cr', 'ne', 'new', 'ja',
            'nap', 'ce', 'pih', 'no', 'nb', 'nn', 'nrm', 'nov', 'ii', 'oc',
            'mhr', 'or', 'om', 'ng', 'hz', 'uz', 'pa', 'pi', 'pag', 'pnb',
            'pap', 'ps', 'km', 'pcd', 'pms', 'tpi', 'nds', 'pl', 'tokipona',
            'tp', 'pnt', 'pt', 'aa', 'kaa', 'crh', 'ty', 'ksh', 'ro', 'rmy',
            'rm', 'qu', 'ru', 'sah', 'se', 'sm', 'sa', 'sg', 'sc', 'sco', 'stq',
            'st', 'tn', 'sq', 'scn', 'si', 'simple', 'sd', 'ss', 'sk', 'cu',
            'sl', 'szl', 'so', 'ckb', 'srn', 'sr', 'sh', 'su', 'fi', 'sv', 'tl',
            'ta', 'kab', 'roa-tara', 'tt', 'te', 'tet', 'th', 'ti', 'tg', 'to',
            'chr', 'chy', 've', 'tr', 'tk', 'tw', 'udm', 'bug', 'uk', 'ur',
            'ug', 'za', 'vec', 'vi', 'vo', 'fiu-vro', 'wa', 'zh-classical',
            'vls', 'war', 'wo', 'wuu', 'ts', 'yi', 'yo', 'zh-yue', 'diq', 'zea',
            'bat-smg', 'zh', 'zh-tw', 'zh-cn', 
        ]

        self.langs = {}

        # letters that can follow a wikilink and are regarded as part of
        # this link
        # This depends on the linktrail setting in LanguageXx.php and on
        # [[MediaWiki:Linktrail]].
        # Note: this is a regular expression.
        self.linktrails = {
           '_default': u'[a-z]*',
           'de': u'[a-zäöüß]*',
           'da': u'[a-zæøå]*',
           'fi': u'[a-zåäö]*',
           'fr': u'[a-zàâçéèêîôû]*',
           'he': u'[a-zא-ת]*',
           'hu': u'[a-záéíóúöüőűÁÉÍÓÚÖÜŐŰ]*',
           'it': u'[a-zàèéìòù]*',
           'kk': u'[a-zäçéğıïñöşüýа-яёәғіқңөұүһʺʹ]*',
           'ksh': u'[äöüėëĳßəğåůæœça-z]*',
           'nl': u'[a-zäöüïëéèéàç]*',
           'pt': u'[a-záâàãéêíóôõúüç]*',
           'ru': u'[a-zа-я]*',
        }

        # Wikimedia wikis all use "bodyContent" as the id of the <div>
        # element that contains the actual page content; change this for
        # wikis that use something else (e.g., mozilla family)
        self.content_id = "bodyContent"

        # A dictionary where keys are family codes that can be used in
        # inter-family interwiki links. Values are not used yet.
        # Generated from http://toolserver.org/~daniel/interwiki-en.txt:
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
            'strategy':         'strategy',
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

        # A list of category redirect template names in different languages
        # Note: It *is* necessary to list template redirects here
        self.category_redirect_templates = {
            '_default': []
        }

        # A list of disambiguation template names in different languages
        self.disambiguationTemplates = {
            '_default': []
        }

        # A list of projects that share cross-project sessions.
        self.cross_projects = []

        # A list with the name for cross-project cookies.
        # default for wikimedia centralAuth extensions.
        self.cross_projects_cookies = ['centralauth_Session',
                                       'centralauth_Token',
                                       'centralauth_User']
        self.cross_projects_cookie_username = 'centralauth_User'

        # A list with the name in the cross-language flag permissions
        self.cross_allowed = []

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

        # Which languages have a special order for putting interlanguage
        # links, and what order is it? If a language is not in
        # interwiki_putfirst, alphabetical order on language code is used.
        # For languages that are in interwiki_putfirst, interwiki_putfirst
        # is checked first, and languages are put in the order given there.
        # All other languages are put after those, in code-alphabetical
        # order.
        self.interwiki_putfirst = {}

        # Languages in interwiki_putfirst_doubled should have a number plus
        # a list of languages. If there are at least the number of interwiki
        # links, all languages in the list should be placed at the front as
        # well as in the normal list.
        self.interwiki_putfirst_doubled = {}  # THIS APPEARS TO BE UNUSED!

        # Some families, e. g. commons and meta, are not multilingual and
        # forward interlanguage links to another family (wikipedia).
        # These families can set this variable to the name of the target
        # family.
        self.interwiki_forward = None

        # Which language codes no longer exist and by which language code
        # should they be replaced. If for example the language with code xx:
        # now should get code yy:, add {'xx':'yy'} to obsolete. If all
        # links to language xx: should be removed, add {'xx': None}.
        self.obsolete = {}

        # Language codes of the largest wikis. They should be roughly sorted
        # by size.
        self.languages_by_size = []

        # Some languages belong to a group where the possibility is high that
        # equivalent articles have identical titles among the group.
        self.language_groups = {
            # languages using the arabic script (incomplete)
            'arab' : [
                'ar', 'arz', 'ps', 'sd', 'ur', 'ckb',
                # languages using multiple scripts, including arabic
                'kk', 'ku', 'tt', 'ug', 'pnb'
            ],
            # languages that use chinese symbols
            'chinese': [
                'wuu', 'zh', 'zh-classical', 'zh-yue', 'gan', 'ii',
                # languages using multiple/mixed scripts, including chinese
                'ja', 'za'
            ],
            # languages that use the cyrillic alphabet
            'cyril': [
                'ab', 'av', 'ba', 'be', 'be-x-old', 'bg', 'bxr', 'ce', 'cu',
                'cv', 'kv', 'ky', 'mk', 'lbe', 'mdf', 'mn', 'mo', 'myv', 'os',
                'ru', 'sah', 'tg', 'tk', 'udm', 'uk', 'xal', 'mhr',
                # languages using multiple scripts, including cyrillic
                'ha', 'kk', 'sh', 'sr', 'tt'
            ],
            # languages that use a greek script
            'grec': [
                'el', 'grc', 'pnt'
                # languages using multiple scripts, including greek
            ],
            # languages that use the latin alphabet
            'latin': [
                'aa', 'ace', 'af', 'ak', 'als', 'an', 'ang', 'ast', 'ay', 'bar',
                'bat-smg', 'bcl', 'bi', 'bm', 'br', 'bs', 'ca', 'cbk-zam',
                'cdo', 'ceb', 'ch', 'cho', 'chy', 'co', 'crh', 'cs', 'csb',
                'cy', 'da', 'de', 'diq', 'dsb', 'ee', 'eml', 'en', 'eo', 'es',
                'et', 'eu', 'ext', 'ff', 'fi', 'fiu-vro', 'fj', 'fo', 'fr',
                'frp', 'fur', 'fy', 'ga', 'gd', 'gl', 'gn', 'gv', 'hak', 'haw',
                'hif', 'ho', 'hr', 'hsb', 'ht', 'hu', 'hz', 'ia', 'id', 'ie',
                'ig', 'ik', 'ilo', 'io', 'is', 'it', 'jbo', 'jv', 'kaa', 'kab',
                'kg', 'ki', 'kj', 'kl', 'kr', 'ksh', 'kw', 'la', 'lad', 'lb',
                'lg', 'li', 'lij', 'lmo', 'ln', 'lt', 'lv', 'map-bms', 'mg',
                'mh', 'mi', 'ms', 'mt', 'mus', 'mwl', 'na', 'nah', 'nap', 'nds',
                'nds-nl', 'ng', 'nl', 'nn', 'no', 'nov', 'nrm', 'nv', 'ny',
                'oc', 'om', 'pag', 'pam', 'pap', 'pcd', 'pdc', 'pih', 'pl',
                'pms', 'pt', 'qu', 'rm', 'rn', 'ro', 'roa-rup', 'roa-tara',
                'rw', 'sc', 'scn', 'sco', 'se', 'sg', 'simple', 'sk', 'sl',
                'sm', 'sn', 'so', 'sq', 'srn', 'ss', 'st', 'stq', 'su', 'sv',
                'sw', 'szl', 'tet', 'tl', 'tn', 'to', 'tpi', 'tr', 'ts', 'tum',
                'tw', 'ty', 'uz', 've', 'vec', 'vi', 'vls', 'vo', 'wa', 'war',
                'wo', 'xh', 'yo', 'zea', 'zh-min-nan', 'zu',
                # languages using multiple scripts, including latin
                'az', 'chr', 'ckb', 'ha', 'iu', 'kk', 'ku', 'rmy', 'sh', 'sr',
                'tt', 'ug', 'za'
            ],
            # Scandinavian languages
            'scand': [
                'da', 'fo', 'is', 'nb', 'nn', 'no', 'sv'
            ],
        }

        # LDAP domain if your wiki uses LDAP authentication,
        # http://www.mediawiki.org/wiki/Extension:LDAP_Authentication
        self.ldapDomain = ()

        # Allows crossnamespace interwiki linking.
        # Lists the possible crossnamespaces combinations
        # keys are originating NS
        # values are dicts where:
        #   keys are the originating langcode, or _default
        #   values are dicts where:
        #     keys are the languages that can be linked to from the lang+ns, or
        #     '_default'; values are a list of namespace numbers
        self.crossnamespace = {}
        ##
        ## Examples :
        ## Allowing linking to pt' 102 NS from any other lang' 0 NS is
        # self.crossnamespace[0] = {
        #     '_default': { 'pt': [102]}
        # }
        ## While allowing linking from pt' 102 NS to any other lang' = NS is
        # self.crossnamespace[102] = {
        #     'pt': { '_default': [0]}
        # }

    def _addlang(self, code, location, namespaces = {}):
        """Add a new language to the langs and namespaces of the family.
           This is supposed to be called in the constructor of the family."""
        self.langs[code] = location
##
##        for num, val in namespaces.items():
##            self.namespaces[num][code]=val

    def get_known_families(self, site):
        return self.known_families

    def linktrail(self, code, fallback = '_default'):
        if code in self.linktrails:
            return self.linktrails[code]
        elif fallback:
            return self.linktrails[fallback]
        else:
            raise KeyError(
                "ERROR: linktrail in language %(language_code)s unknown"
                % {'language_code': code})

    def category_redirects(self, code, fallback="_default"):
        if code in self.category_redirect_templates:
            return self.category_redirect_templates[code]
        elif fallback:
            return self.category_redirect_templates[fallback]
        else:
            raise KeyError(
"ERROR: title for category redirect template in language '%s' unknown"
                % code)

    def disambig(self, code, fallback = '_default'):
        if code in self.disambiguationTemplates:
            return self.disambiguationTemplates[code]
        elif fallback:
            return self.disambiguationTemplates[fallback]
        else:
            raise KeyError(
"ERROR: title for disambig template in language %(language_code)s unknown"
                % {'language_code': code})

    # Methods
    def protocol(self, code):
        """
        Can be overridden to return 'https'.
        Other protocols are not supported.
        """
        return 'http'

    def hostname(self, code):
        """The hostname to use for standard http connections."""
        return self.langs[code]

    def ssl_hostname(self, code):
        """The hostname to use for SSL connections."""
        return "secure.wikimedia.org"

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

    def ssl_pathprefix(self, code):
        """The path prefix for secure.wikimedia.org access."""
        # Override this ONLY if the wiki family uses a different path
        # pattern than /familyname/languagecode
        return "/%s/%s" % (self.name, code)

    def path(self, code):
        return '%s/index.php' % self.scriptpath(code)

    def querypath(self, code):
        return '%s/query.php' % self.scriptpath(code)

    def apipath(self, code):
        return '%s/api.php' % self.scriptpath(code)

    def nicepath(self, code):
        return '/wiki/'

    def nice_get_address(self, code, title):
        return '%s%s' % (self.nicepath(code), title)

    def dbName(self, code):
        # returns the name of the MySQL database
        return '%s%s' % (code, self.name)

    # Which version of MediaWiki is used?
    def version(self, code):
        """Return MediaWiki version number as a string."""
        # Don't use this, use versionnumber() instead. This only exists
        # to not break family files.
        return '1.13alpha'

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

    def has_query_api(self, code):
        """Is query.php installed in the wiki?"""
        return False

    def shared_image_repository(self, code):
        """Return the shared image repository, if any."""
        return (None, None)

    @pywikibot.deprecated("Site.getcurrenttime()")
    def server_time(self, code):
        """
        DEPRECATED, use Site.getcurrenttime() instead
        Return a datetime object representing server time"""
        return pywikibot.Site(code, self).getcurrenttime()

    def isPublic(self, code):
        """Does the wiki require logging in before viewing it?"""
        return True

    def post_get_convert(self, site, getText):
        """Does a conversion on the retrieved text from the wiki
        i.e. Esperanto X-conversion """
        return getText

    def pre_put_convert(self, site, putText):
        """Does a conversion on the text to insert on the wiki
        i.e. Esperanto X-conversion """
        return putText
