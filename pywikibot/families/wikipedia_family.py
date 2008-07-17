# -*- coding: utf-8  -*-
import urllib
from pywikibot import family
import config

__version__ = '$Id$'

# The Wikimedia family that is known as Wikipedia, the Free Encyclopedia

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikipedia'

        self.languages_by_size = [
            'en', 'de', 'fr', 'pl', 'ja', 'it', 'nl', 'pt', 'es', 'sv',
            'ru', 'zh', 'no', 'fi', 'vo', 'ca', 'ro', 'tr', 'uk', 'eo',
            'cs', 'hu', 'sk', 'da', 'id', 'he', 'lt', 'sr', 'sl', 'ko',
            'ar', 'bg', 'et', 'new', 'hr', 'te', 'ceb', 'gl', 'th', 'fa',
            'el', 'vi', 'nn', 'ms', 'simple', 'eu', 'bpy', 'bs', 'ka', 'is',
            'lb', 'sq', 'br', 'la', 'az', 'bn', 'hi', 'mr', 'mk', 'tl',
            'sh', 'io', 'cy', 'pms', 'lv', 'su', 'ta', 'nap', 'ht', 'jv',
            'scn', 'nds', 'oc', 'ast', 'ku', 'wa', 'be', 'af', 'be-x-old', 'tg',
            'an', 'roa-tara', 'vec', 'zh-yue', 'ksh', 'cv', 'ur', 'fy', 'yo', 'sw',
            'uz', 'mi', 'qu', 'ga', 'bat-smg', 'ml', 'co', 'kn', 'gd', 'yi',
            'hsb', 'pam', 'nah', 'ia', 'tt', 'sa', 'li', 'hy', 'als', 'roa-rup',
            'lmo', 'map-bms', 'am', 'pag', 'zh-min-nan', 'nrm', 'fo', 'wuu', 'vls', 'se',
            'nds-nl', 'war', 'ne', 'fur', 'nov', 'rm', 'lij', 'bh', 'dv', 'pi',
            'sco', 'ilo', 'diq', 'os', 'kk', 'frp', 'zh-classical', 'mt', 'fiu-vro', 'lad',
            'pdc', 'csb', 'kw', 'bar', 'to', 'haw', 'ps', 'mn', 'ang', 'tk',
            'km', 'ln', 'tpi', 'ie', 'crh', 'jbo', 'wo', 'zea', 'gv', 'eml',
            'or', 'ig', 'ay', 'mg', 'kg', 'ty', 'ky', 'cbk-zam', 'glk', 'si',
            'gu', 'sc', 'arc', 'kab', 'ks', 'gn', 'so', 'mzn', 'cu', 'udm',
            'tet', 'sd', 'ce', 'pa', 'ba', 'rmy', 'na', 'iu', 'lo', 'bo',
            'got', 'stq', 'chr', 'bcl', 'om', 'hak', 'ug', 'sm', 'ee', 'ti',
            'as', 'cdo', 'av', 'bm', 'dsb', 'zu', 'nv', 'my', 'pih', 'pap',
            'cr', 've', 'ss', 'rw', 'xh', 'kl', 'ik', 'bug', 'dz', 'ts',
            'kv', 'bi', 'xal', 'st', 'tn', 'ch', 'ak', 'bxr', 'ny', 'ab',
            'fj', 'tw', 'lbe', 'za', 'ff', 'tum', 'ha', 'sn', 'sg', 'lg',
            'ki', 'rn', 'chy', 'aa', 'ng', 'ext', 'gan', 'hif', 'kaa', 'mdf',
            'myv', 'sah', 'srn', 'szl',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikipedia.org' % lang

        # Override defaults
        self.namespaces[2]['cs'] = u'Wikipedista'
        self.namespaces[3]['cs'] = u'Wikipedista diskuse'
        self.namespaces[2]['pl'] = u'Wikipedysta'
        self.namespaces[3]['pl'] = u'Dyskusja wikipedysty'

        # Most namespaces are inherited from family.Family.
        # Translation used on all wikis for the different namespaces.
        # (Please sort languages alphabetically)
        # You only need to enter translations that differ from _default.
        self.namespaces[4] = {
            '_default': [u'Wikipedia', self.namespaces[4]['_default']],
            'ar': u'ويكيبيديا',
            'ast': u'Uiquipedia',
            'az': u'Vikipediya',
            'bat-smg': u'Vikipedėjė',
            'be': u'Вікіпедыя',
            'be-x-old': u'Вікіпэдыя',
            'bg': u'Уикипедия',
            'bn': u'উইকিপেডিয়া',
            'bpy': u'উইকিপিডিয়া',
            'ca': u'Viquipèdia',
            'ce': u'Википедийа',
            'crh': u'Vikipediya',
            'cs': u'Wikipedie',
            'csb': u'Wiki',
            'cu': u'Википедї',
            'cv': u'Википеди',
            'cy': u'Wicipedia',
            'dsb': u'Wikipedija',
            'el': u'Βικιπαίδεια',
            'eo': u'Vikipedio',
            'et': u'Vikipeedia',
            'ext': u'Güiquipeya',
            'fa': u'ویکی‌پدیا',
            'fr': [u'Wikipédia', u'Wikipedia'],
            'frp': u'Vouiquipèdia',
            'fur': u'Vichipedie',
            'fy': u'Wikipedy',
            'ga': u'Vicipéid',
            'gn': u'Vikipetã',
            'gu': u'વિકિપીડિયા',
            'he': u'ויקיפדיה',
            'hi': u'विकिपीडिया',
            'hr': u'Wikipedija',
            'hsb': u'Wikipedija',
            'ht': u'Wikipedya',
            'hu': u'Wikipédia',
            'hy': u'Վիքիփեդիա',
            'io': u'Wikipedio',
            'ka': u'ვიკიპედია',
            'kk': u'Уикипедия',
            'km': u'វិគីភីឌា',
            'kn': u'ವಿಕಿಪೀಡಿಯ',
            'ko': u'위키백과',
            'ku': u'Wîkîpediya',
            'la': u'Vicipaedia',
            'lbe': u'Википедия',
            'lo': u'ວິກິພີເດຍ',
            'lv': u'Vikipēdija',
            'mdf': u'Википедиесь',
            'mk': u'Википедија',
            'ml': u'വിക്കിപീഡിയ',
            'mr': u'विकिपीडिया',
            'mt': u'Wikipedija',
            'myv': u'Википедиясь',
            'nds-nl': u'Wikipedie',
            'new': u'विकिपिडिया',
            'nv': u'Wikiibíídiiya',
            'oc': u'Wikipèdia',
            'pa': u'ਵਿਕਿਪੀਡਿਆ',
            'rmy': u'Vikipidiya',
            'ru': u'Википедия',
            'sah': u'Бикипиидийэ',
            'sk': u'Wikipédia',
            'sl': u'Wikipedija',
            'sr': u'Википедија',
            'szl': u'Wikipedyjo',
            'ta': u'விக்கிப்பீடியா',
            'te': u'వికీపీడియా',
            'tg': u'Википедиа',
            'th': u'วิกิพีเดีย',
            'tr': u'Vikipedi',
            'uk': u'Вікіпедія',
            'ur': u'منصوبہ',
            'uz': u'Vikipediya',
            'vo': u'Vükiped',
            'yi': [u'װיקיפּעדיע', u'וויקיפעדיע'],
            'zh-classical': u'維基大典',
        }

        self.namespaces[5] = {
            '_default': [u'Wikipedia talk', self.namespaces[5]['_default']],
            'ab': u'Обсуждение Wikipedia',
            'af': u'Wikipediabespreking',
            'als': u'Wikipedia Diskussion',
            'an': u'Descusión Wikipedia',
            'ar': u'نقاش ويكيبيديا',
            'as': u'Wikipedia वार्ता',
            'ast': u'Uiquipedia alderique',
            'av': u'Обсуждение Wikipedia',
            'ay': u'Wikipedia Discusión',
            'az': u'Vikipediya müzakirəsi',
            'ba': u'Wikipedia б-са фекер алышыу',
            'bar': u'Wikipedia Diskussion',
            'bat-smg': u'Vikipedėjės aptarėms',
            'bcl': u'Olay sa Wikipedia',
            'be': u'Вікіпедыя размовы',
            'be-x-old': u'Абмеркаваньне Вікіпэдыя',
            'bg': u'Уикипедия беседа',
            'bm': u'Discussion Wikipedia',
            'bn': u'উইকিপেডিয়া আলাপ',
            'bpy': u'উইকিপিডিয়া য়্যারী',
            'br': [u'Kaozeadenn Wikipedia', u'Discussion Wikipedia'],
            'bs': u'Razgovor s Wikipediom',
            'bug': u'Pembicaraan Wikipedia',
            'ca': u'Viquipèdia Discussió',
            'cbk-zam': u'Wikipedia Discusión',
            'ce': u'Википедийа Дийца',
            'crh': [u'Vikipediya muzakeresi', u'Vikipediya музакереси'],
            'cs': u'Wikipedie diskuse',
            'csb': u'Diskùsëjô Wiki',
            'cu': u'Википедїѩ бєсѣ́да',
            'cv': u'Википеди сӳтсе явмалли',
            'cy': u'Sgwrs Wicipedia',
            'da': u'Wikipedia-diskussion',
            'de': u'Wikipedia Diskussion',
            'diq': u'Wikipedia talk',
            'dsb': u'Wikipedija diskusija',
            'el': u'Βικιπαίδεια συζήτηση',
            'eml': u'Discussioni Wikipedia',
            'eo': u'Vikipedia diskuto',
            'es': u'Wikipedia Discusión',
            'et': u'Vikipeedia arutelu',
            'eu': u'Wikipedia eztabaida',
            'ext': u'Güiquipeya talk',
            'fa': u'بحث ویکی‌پدیا',
            'ff': u'Discussion Wikipedia',
            'fi': u'Keskustelu Wikipediasta',
            'fiu-vro': u'Wikipedia arotus',
            'fo': u'Wikipedia kjak',
            'fr': [u'Discussion Wikipédia', u'Discussion Wikipedia'],
            'frp': u'Discussion Vouiquipèdia',
            'fur': u'Discussion Vichipedie',
            'fy': u'Wikipedy oerlis',
            'ga': u'Plé Vicipéide',
            'gl': u'Conversa Wikipedia',
            'glk': u'بحث Wikipedia',
            'gn': u'Vikipetã myangekõi',
            'gu': u'વિકિપીડિયા talk',
            'he': u'שיחת ויקיפדיה',
            'hi': u'विकिपीडिया वार्ता',
            'hr': u'Razgovor Wikipedija',
            'hsb': u'Wikipedija diskusija',
            'ht': u'Diskisyon Wikipedya',
            'hu': u'Wikipédia-vita',
            'hy': u'Վիքիփեդիայի քննարկում',
            'ia': u'Discussion Wikipedia',
            'id': u'Pembicaraan Wikipedia',
            'io': u'Wikipedio Debato',
            'is': u'Wikipediaspjall',
            'it': u'Discussioni Wikipedia',
            'ja': u'Wikipedia‐ノート',
            'jv': u'Dhiskusi Wikipedia',
            'ka': u'ვიკიპედია განხილვა',
            'kaa': u'Wikipedia sa\'wbeti',
            'kab': u'Amyannan n Wikipedia',
            'kk': u'Уикипедия талқылауы',
            'kl': u'Wikipedia-diskussion',
            'km': u'ការពិភាក្សាអំពីវិគីភីឌា',
            'kn': u'ವಿಕಿಪೀಡಿಯ ಚರ್ಚೆ',
            'ko': u'위키백과토론',
            'ksh': u'Wikipedia Klaaf',
            'ku': u'Wîkîpediya nîqaş',
            'kv': u'Обсуждение Wikipedia',
            'la': [u'Disputatio Vicipaediae', u'Disputatio Wikipedia'],
            'lad': u'Wikipedia Discusión',
            'lb': u'Wikipedia Diskussioun',
            'lbe': u'Википедиялиясса ихтилат',
            'li': u'Euverlèk Wikipedia',
            'lij': u'Discussioni Wikipedia',
            'lmo': u'Discussioni Wikipedia',
            'ln': u'Discussion Wikipedia',
            'lo': u'ສົນທະນາກ່ຽວກັບວິກິພີເດຍ',
            'lt': u'Wikipedia aptarimas',
            'lv': u'Vikipēdijas diskusija',
            'map-bms': u'Dhiskusi Wikipedia',
            'mdf': u'Википедиесь talk',
            'mg': u'Discussion Wikipedia',
            'mk': u'Разговор за Википедија',
            'ml': u'വിക്കിപീഡിയ സംവാദം',
            'mr': u'विकिपीडिया चर्चा',
            'ms': u'Perbincangan Wikipedia',
            'mt': u'Wikipedija talk',
            'myv': u'Википедиясь talk',
            'mzn': u'بحث Wikipedia',
            'nah': u'Wikipedia Discusión',
            'nap': u'Discussioni Wikipedia',
            'nds': u'Wikipedia Diskuschoon',
            'nds-nl': u'Overleg Wikipedie',
            'new': u'विकिपिडिया खँलाबँला',
            'nl': u'Overleg Wikipedia',
            'nn': u'Wikipedia-diskusjon',
            'no': u'Wikipedia-diskusjon',
            'nv': u"Wikiibíídiiya baa yinísht'į́",
            'oc': u'Discussion Wikipèdia',
            'os': u'Дискусси Wikipedia',
            'pa': u'ਵਿਕਿਪੀਡਿਆ ਚਰਚਾ',
            'pdc': u'Wikipedia Diskussion',
            'pl': u'Dyskusja Wikipedii',
            'pms': u'Discussion ant sla Wikipedia',
            'ps': u'د Wikipedia خبرې اترې',
            'pt': u'Wikipedia Discussão',
            'qu': u'Wikipedia rimanakuy',
            'rmy': u'Vikipidiyake vakyarimata',
            'ro': u'Discuţie Wikipedia',
            'ru': u'Обсуждение Википедии',
            'sa': u'Wikipediaसंभाषणं',
            'sah': u'Бикипиидийэ talk',
            'sc': u'Wikipedia discussioni',
            'scn': u'Discussioni Wikipedia',
            'si': u'Wikipedia සාකච්ඡාව',
            'sk': u'Diskusia k Wikipédii',
            'sl': u'Pogovor o Wikipediji',
            'sq': u'Wikipedia diskutim',
            'sr': u'Разговор о Википедији',
            'srn': u'Overleg Wikipedia',
            'stq': u'Wikipedia Diskussion',
            'su': u'Obrolan Wikipedia',
            'sv': u'Wikipediadiskussion',
            'szl': u'Dyskusja Wikipedyjo',
            'ta': u'விக்கிப்பீடியா பேச்சு',
            'te': u'వికీపీడియా చర్చ',
            'tet': u'Diskusaun Wikipedia',
            'tg': u'Баҳси Википедиа',
            'th': u'คุยเรื่องวิกิพีเดีย',
            'tr': u'Vikipedi tartışma',
            'tt': u'Wikipedia bäxäse',
            'ty': u'Discussion Wikipedia',
            'udm': u'Wikipedia сярысь вераськон',
            'uk': u'Обговорення Вікіпедії',
            'ur': u'تبادلۂ خیال منصوبہ',
            'uz': u'Vikipediya munozarasi',
            'vec': u'Discussion Wikipedia',
            'vi': u'Thảo luận Wikipedia',
            'vls': u'Discuusje Wikipedia',
            'vo': u'Bespik dö Vükiped',
            'wa': u'Wikipedia copene',
            'wo': u'Discussion Wikipedia',
            'xal': u'Wikipedia тускар ухалвр',
            'yi': [u'װיקיפּעדיע רעדן', u'וויקיפעדיע רעדן'],
            'zea': u'Overleg Wikipedia',
            'zh-classical': u'維基大典 talk',
        }

        self.namespaces[100] = {
            'als': u'Portal',
            'an': u'Portal',
            'ar': u'بوابة',
            'bg': u'Портал',
            'bpy': u'হমিলদুৱার',
            'ca': u'Portal',
            'cs': u'Portál',
            'da': u'Portal',
            'de': u'Portal',
            'el': u'Πύλη',
            'en': u'Portal',
            'eo': u'Portalo',
            'es': u'Portal',
            'eu': u'Atari',
            'fa': u'درگاه',
            'fi': u'Teemasivu',
            'fr': u'Portail',
            'gl': u'Portal',
            'he': u'פורטל',
            'hi': u'प्रवेशद्वार',
            'hr': u'Portal',
            'hu': u'Portál',
            'ia': u'Portal',
            'id': u'Portal',
            'is': u'Gátt',
            'it': u'Portale',
            'ja': u'Portal',
            'ka': u'პორტალი',
            'kk': u'Портал',
            'la': u'Porta',
            'li': u'Portaol',
            'lmo': u'Portal',
            'lv': u'Portāls',
            'mk': u'Портал',
            'ml': u'കവാടം',
            'mr': u'दालन',
            'ms': u'Portal',
            'nds': u'Portal',
            'new': u'दबू',
            'nl': u'Portaal',
            'no': u'Portal',
            'oc': u'Portal',
            'pl': u'Portal',
            'pt': u'Portal',
            'ro': u'Portal',
            'ru': u'Портал',
            'scn': u'Purtali',
            'si': u'Portal',
            'sk': u'Portál',
            'sl': u'Portal',
            'sq': u'Portal',
            'sr': u'Портал',
            'su': u'Portal',
            'sv': u'Portal',
            'ta': u'வலைவாசல்',
            'te': u'వేదిక',
            'tg': u'Портал',
            'th': u'สถานีย่อย',
            'tr': u'Portal',
            'uk': u'Портал',
            'vec': u'Portałe',
            'vi': u'Chủ đề',
            'yi': u'פארטאל',
            'zh': u'Portal',
            'zh-classical': u'門',
            'zh-yue': u'Portal',
        }

        self.namespaces[101] = {
            'als': u'Portal Diskussion',
            'an': u'Descusión Portal',
            'ar': u'نقاش البوابة',
            'bg': u'Портал беседа',
            'bpy': u'হমিলদুৱার য়্যারী',
            'ca': u'Portal Discussió',
            'cs': u'Portál diskuse',
            'da': [u'Portaldiskussion', u'Portal diskussion'],
            'de': u'Portal Diskussion',
            'el': u'Συζήτηση πύλης',
            'en': u'Portal talk',
            'eo': u'Portala diskuto',
            'es': u'Portal Discusión',
            'eu': u'Atari eztabaida',
            'fa': u'بحث درگاه',
            'fi': u'Keskustelu teemasivusta',
            'fr': u'Discussion Portail',
            'gl': u'Portal talk',
            'he': u'שיחת פורטל',
            'hi': u'प्रवेशद्वार वार्ता',
            'hr': u'Razgovor o portalu',
            'hu': u'Portál vita',
            'ia': u'Discussion Portal',
            'id': u'Pembicaraan Portal',
            'is': u'Gáttaspjall',
            'it': u'Discussioni portale',
            'ja': u'Portal‐ノート',
            'ka': u'პორტალი განხილვა',
            'kk': u'Портал талқылауы',
            'la': u'Disputatio Portae',
            'li': u'Euverlèk portaol',
            'lmo': u'Descüssiú Portal',
            'lv': u'Portāla diskusija',
            'mk': u'Разговор за Портал',
            'ml': u'കവാടത്തിന്റെ സംവാദം',
            'mr': u'दालन चर्चा',
            'ms': u'Portal talk',
            'nds': u'Portal Diskuschoon',
            'new': u'दबू खँलाबँला',
            'nl': u'Overleg portaal',
            'no': u'Portaldiskusjon',
            'oc': u'Discussion Portal',
            'pl': u'Dyskusja portalu',
            'pt': [u'Portal Discussão', u'Discussão Portal'],
            'ro': u'Discuţie Portal',
            'ru': u'Обсуждение портала',
            'scn': u'Discussioni purtali',
            'si': u'Portal talk',
            'sk': u'Diskusia k portálu',
            'sl': u'Pogovor o portalu',
            'sq': u'Portal diskutim',
            'sr': u'Разговор о порталу',
            'su': u'Obrolan portal',
            'sv': u'Portaldiskussion',
            'ta': u'வலைவாசல் பேச்ச',
            'te': u'వేదిక చర్చ',
            'tg': u'Баҳси портал',
            'th': u'คุยเรื่องสถานีย่อย',
            'tr': u'Portal tartışma',
            'uk': u'Обговорення порталу',
            'vec': u'Discussion portałe',
            'vi': u'Thảo luận Chủ đề',
            'yi': u'פארטאל רעדן',
            'zh': u'Portal talk',
            'zh-classical': u'議',
            'zh-yue': u'Portal talk',
        }

        self.namespaces[102] = {
            'als': u'Buech',
            'ca': u'Viquiprojecte',
            'cs': u'Rejstřík',
            'es': u'Wikiproyecto',
            'eu': u'Wikiproiektu',
            'fi': u'Metasivu',
            'fr': u'Projet',
            'hr': u'Dodatak',
            'it': u'Progetto',
            'lmo': u'Purtaal',
            'oc': u'Projècte',
            'pl': u'Wikiprojekt',
            'pt': u'Anexo',
            'ro': u'Proiect',
            'scn': u'Pruggettu',
            'vec': u'Projeto',
        }

        self.namespaces[103] = {
            'als': u'Buech Diskussion',
            'ca': u'Viquiprojecte Discussió',
            'cs': u'Rejstřík diskuse',
            'es': u'Wikiproyecto Discusión',
            'eu': u'Wikiproiektu eztabaida',
            'fi': u'Keskustelu metasivusta',
            'fr': u'Discussion Projet',
            'hr': u'Razgovor o dodatku',
            'it': u'Discussioni progetto',
            'lmo': u'Descüssiun Purtaal',
            'oc': u'Discussion Projècte',
            'pl': u'Dyskusja Wikiprojektu',
            'pt': u'Anexo Discussão',
            'ro': u'Discuţie Proiect',
            'scn': u'Discussioni pruggettu',
            'vec': u'Discussion projeto',
        }

        self.namespaces[104] = {
            'als': u'Wort',
            'es': u'Anexo',
            'fr': u'Référence',
            'lt': u'Sąrašas',
        }

        self.namespaces[105] = {
            'als': u'Wort Diskussion',
            'es': u'Anexo Discusión',
            'fr': u'Discussion Référence',
            'lt': u'Sąrašo aptarimas',
        }

        self.namespaces[106] = {
            'als': u'Text',
        }

        self.namespaces[107] = {
            'als': u'Text Diskussion',
        }

        self.namespaces[108] = {
            'als': u'Spruch',
        }

        self.namespaces[109] = {
            'als': u'Spruch Diskussion',
        }

        self.namespaces[110] = {
            'als': u'Nochricht',
        }

        self.namespaces[111] = {
            'als': u'Nochricht Diskussion',
        }

        self.disambiguationTemplates = {
            # set value to None, instead of a list, to retrieve names from
            # the live wiki ([[MediaWiki:Disambiguationspage]]
            '_default': [u'Disambig'],
            'af':  [u'Dubbelsinnig', u'Disambig'],
            'als': [u'Begriffsklärung', u'Disambig'],
            'an':  [u'Desambig', u'Disambig'],
            'ar':  [u'Disambig', u'توضيح'],
            'arc': [u'ܕ'],
            'ast': [u'Dixebra'],
            'bar': [u'Begriffsklärung'],
            'be':  [u'Неадназначнасць', u'Disambig'],
            'be-x-old':  [u'Неадназначнасць', u'Неадназначнасьць', u'Disambig'],
            'bg':  [u'Пояснение', u'Disambig'],
            'bn':  [u'দ্ব্যর্থতা নিরসন', u'Disambig'],
            'br':  [u'Hvlstumm', u'Digejañ'],
            'bs':  [u'Čvor'],
            'ca':  [u'Desambiguació', u'Disambig', u'Desambigua'],
            'ceb': [u'Giklaro'],
            'cdo': [u'Gì-ngiê'],
            'cs':  [u'Rozcestník', u'Rozcestník - 2 znaky', u'Rozcestník - Příjmení',
                    u'Rozcestník - místopisné jméno', u'Disambig', u'Rozcestník - příjmení',],
            'cy':  [u'Anamrwysedd', u'Disambig', u'Gwahaniaethu'],
            'da':  [u'Flertydig'],
            'de':  [u'Begriffsklärung', u'BKS', u'Disambig'],
            'el':  [u'Disambig', u'Αποσαφ', u'Αποσαφήνιση'],
            'en':  None,
            'eo':  [u'Apartigilo', u'Disambig'],
            'es':  [u'Desambiguacion', u'Desambiguación', u'Desambig', u'Disambig',u'Des'],
            'et':  [u'Täpsustuslehekülg', u'Täpsustus', u'Disambig'],
            'eu':  [u'Argipen', u'Disambig'],
            'ext': [u'Desambiguáncia'],
            'fa':  [u'ابهام‌زدایی'],
            'fi':  [u'Täsmennyssivu', u'Disambig'],
            'fo':  [u'Fleiri týdningar'],
            # See http://fr.wikipedia.org/wiki/MediaWiki:Disambiguationspage
            'fr':  [u'Homonymie', u'Arrondissements homonymes', u'Disambig',
                    u'Bandeau standard pour page d\'homonymie',
                    u'Batailles homonymes', u'Cantons homonymes',
                    u'Homonymie de clubs sportifs', u'Homonymie dynastique',
                    u'Homonymie de comtés', u'Internationalisation',
                    u'Isomérie', u'Homonymie de nom romain',
                    u'Paronymie', u'Patronymie', u'Personnes homonymes',
                    u'Unités homonymes',
                    u'Villes homonymes'],
            'frp': [u'Homonimos'],
            'fy':  [u'Tfs', u'Neibetsjuttings'],
            'ga':  [u'Idirdhealú', u'Disambig'],
            'gl':  [u'Homónimos', u'Disambig'],
            'he':  [u'פירושונים', u'Disambig'],
            'hi':  [u'बहुविकल्पी शब्द', u'Disambig',],
            'hr':  [u'Disambig', u'Razdvojba'],
            'hsb': [u'Wjacezmyslnosć', u'Disambig'],
            'ht':  [u'Menm non', u'Disambig'],
            'hu':  [u'Egyert', u'Disambig', u'Egyért', u'Egyért-redir'],
            'hy':  [u'Երկիմաստ', u'Disambig'],
            'ia':  [u'Disambiguation', u'Disambig'],
            'id':  [u'Disingkat',u'Disambig', u'Disambig nama', u'Disambig tempat', u'Disambig-bandara', u'Disambiguasi', u'Disambig suku'],
            'io':  [u'Homonimo', u'Disambig'],
            'is':  [u'Aðgreining', u'Disambig'],
            'it':  [u'Disambigua', u'Sigla2', u'Sigla3', u'Sigla4', u'Cogni'],
            'ja':  [u'Aimai', u'Dab', u'曖昧さ回避', u'Disambig'],
            'ka':  [u'მრავალმნიშვნელოვანი', u'მრავმნიშ'],
            'kab': [u'Asefham'],
            'kg':  [u'Bisongidila'],
            'kn':  [u'ದ್ವಂದ್ವ ನಿವಾರಣೆ'],
            'ko':  [u'Disambig', u'동음이의', u'동음이의어'],
            'ku':  [u'Cudakirin'],
            'kw':  [u'Klerheans'],
            'ksh': [u'Disambig',  u'disambig'],
            'la':  [u'Discretiva', u'Disnomen'],
            'lb':  [u'Homonymie', u'Disambig'],
            'li':  [u'Verdudeliking', u'Verdudelikingpazjena', u'Vp'],
            'lmo': [u'Desambiguació'],
            'ln':  [u'Bokokani'],
            'mk':  [u'Појаснување'],
            'mo':  [u'Дезамбигуйзаре', u'Disambig'],
            'ms':  [u'Nyahkekaburan', u'Disambig'],
            'mt':  [u'Diżambigwazzjoni'],
            'mzn': [u'گجگجی بایری'],
            'nap': [u'Disambigua'],
            'nds': [u'Mehrdüdig Begreep', 'Disambig'],
            'nds-nl': [u'Dv'],
            'nl':  [u'Dp', u'DP', u'Dp2', u'Dpintro', u'Cognomen'],
            'nn':  [u'Fleirtyding'],
            'no':  [u'Peker', u'Etternavn', u'Disambig', u'Tobokstavsforkortelse',
                    u'Trebokstavsforkortelse', u'Flertydig', u'Pekerside'],
            'nov': [u'Desambig'],
            'nrm': [u'Page dé frouque'],
            'oc':  [u'Omonimia', u'Disambig'],
            'pl':  [u'Disambig', u'DisambRulers', u'DisambigC', u'Strona ujednoznaczniająca'],
            'pms': [u'Gestion dij sinònim'],
            'pt':  [u'Desambiguação', u'Disambig', u'Desambig'],
            'rmy': [u'Dudalipen'],
            'ro':  [u'Dezambiguizare', u'Disambig', u'Hndis', u'Dez'],
            'ru':  [u'Disambig', u'Неоднозначность', u'неоднозначность'],
            'scn': [u'Disambigua', u'Disambig', u'Sigla2', u'Sigla3'],
            'simple': [u'Disambig', u'Disambiguation', u'3CC',u'2CC'],
            'sh': [u'Višeznačna odrednica', u'Disambig', u'Razdvojba',
                  u'Razvrstavanje', u'VZO', u'Višeznačnost',
                  u'Homograf',
                  u'Radzvojba', u'Čvor'],
            'sk':  [u'Disambig', u'Rozlišovacia stránka', u'Disambiguation'],
            'sl':  [u'Disambig', u'Razločitev', u'Disambig-ship'],
            'sq':  [u'Kthjellim', u'Disambig'],
            'sr':  [u'Вишезначна одредница', u'Disambig'],
            'srn': [u'Dp'],
            'su':  [u'Disambig'],
            'sv':  [u'Betydelselista', u'Disambig', u'Förgrening', u'Gaffel',
                    u'Efternamn', u'Gren', u'Förgreningssida', u'3LC',
                    u'Trebokstavsförkortning', u'TLAdisambig'],
            'sw':  [u'Maana'],
            'ta':  [u'பக்கவழி நெறிப்படுத்தல்'],
            'te':  [u'అయోమయ నివృత్తి', u'వివరమైన అయోమయ నివృత్తి'],
            'tg':  [u'Ибҳомзудоӣ', u'Disambig', u'Рафъи ибҳом', u'Disambiguation'],
            'th':  [u'แก้กำกวม', u'Disambig'],
            'tl':  [u'Paglilinaw', u'Disambig'],
            'tr':  [u'Anlam ayrım', u'Disambig', u'Anlam ayrımı'],
            'uk':  [u'DisambigG', u'Disambig'],
            'vec': [u'Disambigua'],
            'vi':  [u'Trang định hướng', u'Định hướng', u'Disambig', u'Hndis'],
            'vls': [u'Db', u'Dp', u'Dpintro'],
            'vo':  [u'Telplänov'],
            'wa':  [u'Omonimeye', u'Disambig'],
            'yi':  [u'באדייטען'],
            'zea': [u'dp', u'Deurverwiespagina'],
            'zh':  [u'Disambig', u'消歧义', u'消歧义页', u'消歧義'],
            'zh-classical':  [u'Disambig', u'釋義', u'消歧義', u''],
            'zh-min-nan': [u'Khu-pia̍t-ia̍h', 'KhPI', u'Disambig'],
            'zh-yue': [u'搞清楚', u'Disambig'],
        }

        self.disambcatname = {
            'af':  u'dubbelsinnig',
            'als': u'Begriffsklärung',
            'ang': u'Scīrung',
            'ast': u'Dixebra',
            'ar':  u'صفحات توضيح',
            'be':  u'Disambig',
            'be-x-old':  u'Вікіпэдыя:Неадназначнасьці',
            'bg':  u'Пояснителни страници',
            'ca':  u'Viquipèdia:Registre de pàgines de desambiguació',
            'cs':  u'Rozcestníky',
            'cy':  u'Gwahaniaethu',
            'da':  u'Flertdig',
            'de':  u'Begriffsklärung',
            'el':  u'Αποσαφήνιση',
            'en':  u'Disambiguation',
            'eo':  u'Apartigiloj',
            'es':  u'Desambiguación',
            'et':  u'Täpsustusleheküljed',
            'eu':  u'Argipen orriak',
            'fa':  u'صفحات ابهام‌زدایی',
            'fi':  u'Täsmennyssivut',
            'fo':  u'Fleiri týdningar',
            'fr':  u'Homonymie',
            'fy':  u'Trochferwiisside',
            'ga':  u'Idirdhealáin',
            'gl':  u'Homónimos',
            'he':  u'פירושונים',
            'hu':  u'Egyértelműsítő lapok',
            'ia':  u'Disambiguation',
            'id':  u'Disambiguasi',
            'io':  u'Homonimi',
            'is':  u'Aðgreiningarsíður',
            'it':  u'Disambigua',
            'ja':  u'曖昧さ回避',
            'ka':  u'მრავალმნიშვნელოვანი',
            'kw':  u'Folennow klerheans',
            'ko':  u'동음이의어 문서',
            'ku':  u'Rûpelên cudakirinê',
            'ksh': u'Woot met mieh wi ëijnem Senn',
            'la':  u'Discretiva',
            'lb':  u'Homonymie',
            'li':  u'Verdudelikingspazjena',
            'ln':  u'Bokokani',
            'lt':  u'Nuorodiniai straipsniai',
            'ms':  u'Nyahkekaburan',
            'mt':  u'Diżambigwazzjoni',
            'nds': u'Mehrdüdig Begreep',
            'nds-nl': u'Deurverwiespagina',
            'nl':  u'Wikipedia:Doorverwijspagina',
            'nn':  u'Fleirtydingssider',
            'no':  u'Pekere',
            'pl':  u'Strony ujednoznaczniające',
            'pt':  u'Desambiguação',
            'ro':  u'Dezambiguizare',
            'ru':  u'Многозначные термины',
            'scn': u'Disambigua',
            'sk':  u'Rozlišovacie stránky',
            'sl':  u'Razločitev',
            'sq':  u'Kthjellime',
            'sr':  u'Вишезначна одредница',
            'su':  u'Disambiguasi',
            'sv':  u'Förgreningssider',
            'th':  u'การแก้ความกำกวม',
            'tl':  u'Paglilinaw',
            'tr':  u'Anlam ayrım',
            'uk':  u'Багатозначні геопункти',
            'vi':  u'Trang định hướng',
            'vo':  u'Telplänovapads',
            'wa':  u'Omonimeye',
            'zea': u'Wikipedia:Deurverwiespagina',
            'zh':  u'消歧义',
            'zh-min-nan': u'Khu-pia̍t-ia̍h',
            }

        # On most Wikipedias page names must start with a capital letter, but some
        # languages don't use this.

        self.nocapitalize = ['jbo',]


        # A revised sorting order worked out on http://meta.wikimedia.org/wiki/Interwiki_sorting_order
        self.alphabetic_revised = ['aa','af','ak','als','am','ang','ab','ar','an',
            'arc','roa-rup','frp','as','ast','gn','av','ay','az','id','ms','bm',
            'bn','zh-min-nan','map-bms','jv','su','ban','ba','be','be-x-old','bh',
            'bi','bo','bs','br','bug','bg','bxr','ca','ceb','cv','cs','ch',
            'ny','sn',
            'tum','cho','co','za','cy','da','pdc','de','dv','nv','dz','mh','et',
            'na','el','eml','en','es','eo','eu','ee','to','fab','fa','fo','fr','fy','ff',
            'fur','ga','gv','sm','gd','gl','gay','ki','glk','gu','got','zh-classical','hak','xal','ko','ha','haw',
            'hy','hi','ho','hsb','hr','io','ig','ilo','bpy','ia','ie','iu','ik','os','xh','zu',
            'is','it','he','kl','pam','kn','kr','ka','ks','csb','kk','kk-cn','kk-kz','kw','rw','ky',
            'rn','sw','kv','kg','ht','kj','ku','lad','lbe','lo','ltg','la','lv','lb','lij','lt',
            'li','ln','jbo','lg','lmo','hu','mk','mg','ml','mt','mi','mr','mzn','chm','cdo','mo',
            'mn','mus','my','nah','fj','nl','nds-nl','cr','ne','new','ja','nap','ce',
            'pih','no','nn','nrm','nov','oc','or','om','ng','hz','ug','uz','pa',
            'pi','pag','pap','ps','km','pms','nds','pl','pt','kk-tr','ty','ksh','ro',
            'rmy','rm','qu','ru','se','sa','sg','sc','sco','st','tn','sq','scn',
            'si','simple','sd','ss','sk','cu','sl','so','sr','sh','fi','sv','tl',
            'ta','kab','roa-tara','tt','te','tet','th','vi','ti','tg','tpi','chr','chy',
            've','tr','tk','tw','udm','uk','ur','vec','vo','fiu-vro','wa',
            'vls','war','wo','wuu','ts','ii','yi','yo','zh-yue','cbk-zam','diq','zea','bat-smg',
            'zh','zh-tw','zh-cn']

        # A sorting order for lb.wikipedia worked out by http://lb.wikipedia.org/wiki/User_talk:Otets
        self.alphabetic_lb = ['aa', 'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an',
            'arc', 'roa-rup', 'frp', 'as', 'ast', 'gn', 'av', 'ay', 'az', 'id', 'ms', 'bm',
            'bn', 'zh-min-nan', 'map-bms', 'jv', 'su', 'ban', 'bug', 'ba', 'be', 'bh', 'mt',
            'be-x-old', 'bi', 'bo', 'bs', 'br', 'bg', 'bxr', 'ca', 'ceb', 'cs', 'ch',
            'chr', 'chy',
            'ny', 'sn', 'tum', 've', 'cho', 'co', 'za', 'cy', 'da', 'pdc', 'de', 'dv',
            'nv', 'dz', 'mh', 'na', 'el', 'eml', 'en', 'es', 'eo', 'et', 'eu', 'ee', 'to',
            'fab', 'fa', 'fo', 'fr', 'fy', 'ff', 'fur', 'ga', 'gv', 'sm', 'gd', 'gl',
            'gay', 'ki', 'glk', 'gu', 'got', 'zh-classical', 'hak', 'xal', 'ko', 'ha', 'haw', 'hy', 'he', 'hi', 'ho', 'hsb',
            'hr', 'io', 'ig', 'bpy', 'ilo', 'ia', 'ie', 'iu', 'ik', 'os', 'xh', 'zu', 'is', 'it',
            'ja', 'kl', 'pam', 'kn', 'kr', 'ka', 'ks', 'csb', 'kw', 'rw', 'ky', 'rn', 'sw',
            'kv', 'kg', 'ht', 'kj', 'ku', 'lad', 'lbe', 'lo', 'ltg', 'la', 'lv', 'lb', 'lij', 'lt', 'li',
            'ln', 'jbo', 'lg', 'lmo', 'hu', 'mk', 'mg', 'ml', 'mi', 'mr', 'mzn', 'chm',
            'cdo', 'mo', 'mn', 'mus', 'my', 'nah', 'fj', 'nap', 'nds-nl', 'nl', 'cr', 'ne', 'new', 'ce',
            'pih', 'no', 'nn', 'nrm', 'nov', 'oc', 'or', 'om', 'ng', 'hz', 'ug', 'uz', 'pa', 'kk',
            'kk-cn', 'kk-kz', 'kk-tr',
            'pi', 'pam', 'pag', 'pap', 'ps', 'km', 'pms', 'nds', 'pl', 'pt', 'ty', 'ksh', 'ro', 'rmy', 'rm', 'qu',
            'ru', 'se', 'sa', 'sg', 'sc', 'sco', 'st', 'tn', 'sq', 'scn', 'si',
            'simple', 'sd', 'ss', 'sk', 'cu', 'sl', 'so', 'sr', 'sh', 'fi', 'sv', 'tl',
            'ta', 'kab', 'roa-tara', 'tt', 'te', 'tet', 'th', 'vi', 'ti', 'tg', 'tpi', 'cv', 'tr',
            'tk', 'tw', 'udm', 'uk', 'ur', 'vec', 'vo', 'fiu-vro', 'wa', 'vls', 'war',
            'wo', 'wuu', 'ts', 'ii', 'yi', 'yo', 'zh-yue', 'cbk-zam', 'diq', 'zea', 'bat-smg', 'zh',
            'zh-tw', 'zh-cn']

        # Order for fy: alphabetical by code, but y counts as i

        def fycomp(x,y):
            x = x.replace("y","i")+x.count("y")*"!"
            y = y.replace("y","i")+y.count("y")*"!"
            return cmp(x,y)
        self.fyinterwiki = self.alphabetic[:]
        self.fyinterwiki.sort(fycomp)

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are put
        # after those, in code-alphabetical order.

        self.interwiki_putfirst = {
            'en': self.alphabetic,
            'et': self.alphabetic_revised,
            'fi': self.alphabetic_revised,
            'fiu-vro': self.alphabetic_revised,
            'fy': self.fyinterwiki,
            'he': ['en'],
            'hu': ['en'],
            'lb': self.alphabetic_lb,
            'ms': self.alphabetic_revised,
            'nds': ['nds-nl','pdt'] + self.alphabetic, # Note: as of 2008-02-24, pdt: (Plautdietsch) is still in the Incubator.
            'nn': ['no','nb','sv','da'] + self.alphabetic,
            'no': self.alphabetic,
            'pl': self.alphabetic,
            'simple': self.alphabetic,
            'te': ['en','hi', 'kn', 'ta', 'ml'],
            'vi': self.alphabetic_revised,
            'yi': ['en','he','de']
        }

        self.obsolete = {
            'cho': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Choctaw_Wikipedia
            'dk': 'da',
            'ho': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Hiri_Motu_Wikipedia
            'hz': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Herero_Wikipedia
            'ii': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Yi_Wikipedia
            'kj': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kwanyama_Wikipedia
            'kr': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kanuri_Wikipedia
            'mh': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Marshallese_Wikipedia
            'minnan': 'zh-min-nan',
            'mo': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Moldovan_Wikipedia
            'mus': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Muscogee_Wikipedia
            'nb': 'no',
            'jp': 'ja',
            'ru-sib': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Siberian_Wikipedia
            'tlh': None,
            'tokipona': None,
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        # Languages that used to be coded in iso-8859-1
        self.latin1old = ['de', 'en', 'et', 'es', 'ia', 'la', 'af', 'cs',
                    'fr', 'pt', 'sl', 'bs', 'fy', 'vi', 'lt', 'fi', 'it',
                    'no', 'simple', 'gl', 'eu', 'nds', 'co', 'mi', 'mr',
                    'id', 'lv', 'sw', 'tt', 'uk', 'vo', 'ga', 'na', 'es',
                    'nl', 'da', 'dk', 'sv', 'test']

        self.crossnamespace[0] = {
            '_default': {
                'pt': [102], 
                'als': [104], 
                'es': [104], 
                'fr': [104], 
                'lt': [104]
            }
        }
        self.crossnamespace[1] = {
            '_default': {
                'pt': [103],
                'als': [105], 
                'es': [105],
                'fr': [105],
                'lt': [105]
            }
        }
        self.crossnamespace[102] = {
            'pt': {
                '_default': [0],
                'als': [0, 104], 
                'es': [0, 104], 
                'fr': [0, 104], 
                'lt': [0, 104]
            }
        }
        self.crossnamespace[103] = {
            'pt': {
                '_default': [1],
                'als': [1, 105],
                'es': [1, 105],
                'fr': [1, 105],
                'lt': [1, 105]
            }
        }
        self.crossnamespace[104] = {
            'als': {
                '_default': [0],
                'pt': [0, 102]
            },
            'es': { 
                '_default': [0],
                'pt': [0, 102]
            },
            'fr': {
                '_default': [0],
                'pt': [0, 102]
            },
            'lt': { 
                '_default': [0],
                'pt': [0, 102]
            }
        }
        self.crossnamespace[105] = {
            'als': {
                '_default': [1],
                'pt': [0, 103]
            },
            'es': {
                '_default': [1],
                'pt': [0, 103]
            },
            'fr': {
                '_default': [1],
                'pt': [0, 103]
            },
            'lt': {
                '_default': [1],
                'pt': [0, 103]
            }
        }
    def get_known_families(self, site):
        # In Swedish Wikipedia 's:' is part of page title not a family
        # prefix for 'wikisource'.
        if site.language() == 'sv':
            d = self.known_families.copy()
            d.pop('s') ; d['src'] = 'wikisource'
            return d
        else:
            return self.known_families

    def version(self, code):
        return '1.13alpha'

    def dbName(self, code):
        # returns the name of the MySQL database
        # for historic reasons, the databases are called xxwiki instead of
        # xxwikipedia for Wikipedias.
        return '%swiki' % code

    def code2encodings(self, code):
        """Return a list of historical encodings for a specific language
           wikipedia"""
        # Historic compatibility
        if code == 'pl':
            return 'utf-8', 'iso8859-2'
        if code == 'ru':
            return 'utf-8', 'iso8859-5'
        if code in self.latin1old:
            return 'utf-8', 'iso-8859-1'
        return self.code2encoding(code),

    def shared_image_repository(self, code):
        return ('commons', 'commons')
