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

        # Translation used on all wikis for the different namespaces.
        # (Please sort languages alphabetically)
        # You only need to enter translations that differ from _default.
        self.namespaces = {
            -2: {
                '_default': u'Media',
                'ab': u'Медиа',
                'ar': u'ميديا',
                'av': u'Медиа',
                'az': u'Mediya',
                'ba': u'Медиа',
                'bat-smg':u'Medija',
                'bcl': u'Medio',
                'be': u'Мультымедыя',
                'be-x-old': u'Мэдыя',
                'bg': u'Медия',
                'bpy': u'মিডিয়া',
                'bs': u'Medija',
                'ce': u'Медйа',
                'crh': [u'Media', u'Медиа'],
                'cs': u'Média',
                'cu': u'Срѣдьства',
                'cv': u'Медиа',
                'dsb': u'Medija',
                'el': u'Μέσον',
                'et': u'Meedia',
                'fa': u'مدیا',
                'fiu-vro': u'Meediä',
                'fo': u'Miðil',
                'frp': u'Mèdia',
                'ga': u'Meán',
                'glk': u'مدیا',
                'he': u'מדיה',
                'hr': u'Mediji',
                'ht': u'Medya',
                'hu': u'Média',
                'hy': u'Մեդիա',
                'is': u'Miðill',
                'ka': u'მედია',
                'kk': u'Таспа',
                'kn': u'ಮೀಡಿಯ',
                'ksh':[u'Medie', u'Meedije'],
                'ku': u'Medya',
                'kv': u'Медиа',
                'lbe': u'Медиа',
                'lt': u'Medija',
                'mk': u'Медија',
                'ml': u'മീഡിയ',
                'mzn': u'مدیا',
                'new': u'माध्यम',
                'nn': u'Filpeikar',
                'no': u'Medium',
                'pa': u'ਮੀਡੀਆ',
                'qu': u'Midya',
                'rmy':u'Mediya',
                'ru': u'Медиа',
                'scn': u'Mèdia',
                'sk': u'Médiá',
                'sr': u'Медија',
                'su': u'Média',
                'ta': u'ஊடகம்',
                'te': u'మీడియా',
                'tg': u'Медиа',
                'th': u'สื่อ',
                'tlh': u'Doch',
                'udm': u'Медиа',
                'uk': u'Медіа',
                'ur': u'زریعہ',
                'vi': u'Phương tiện',
                'vo': u'Nünamakanäd',
                'xal': u'Аһар',
                'yi': u'מעדיע',
            },
            -1: {
                '_default': u'Special',
                'ab': u'Служебная',
                'af': u'Spesiaal',
                'als': u'Spezial',
                'an': u'Espezial',
                'ar': u'خاص',
                'ast': u'Especial',
                'av': u'Служебная',
                'ay': u'Especial',
                'az': u'Xüsusi',
                'ba': u'Ярҙамсы',
                'bar': u'Spezial',
                'bat-smg':u'Specēlos',
                'bcl': u'Espesyal',
                'be': u'Адмысловае',
                'be-x-old': u'Спэцыяльныя',
                'bg': u'Специални',
                'bn': u'বিশেষ',
                'bpy': u'বিশেষ',
                'br': u'Dibar',
                'bs': u'Posebno',
                'bug': u'Istimewa',
                'ca': u'Especial',
                'cbk-zam': u'Especial',
                'ce': u'Башхо',
                'crh': [u'Mahsus', u'Махсус'],
                'cs': u'Speciální',
                'csb': u'Specjalnô',
                'cu': u'Нарочьна',
                'cv': u'Ятарлă',
                'cy': u'Arbennig',
                'da': u'Speciel',
                'de': u'Spezial',
                'dsb': u'Specialne',
                'el': u'Ειδικό',
                'eml': u'Speciale',
                'eo': u'Speciala',
                'es': u'Especial',
                'et': u'Eri',
                'eu': u'Aparteko',
                'fa': u'ویژه',
                'fi': u'Toiminnot',
                'fiu-vro': u'Tallituslehekülg',
                'fo': u'Serstakur',
                'frp': u'Spèciâl',
                'fur': u'Speciâl',
                'fy': u'Wiki',
                'ga': u'Speisialta',
                'gl': u'Especial',
                'glk': u'ویژه',
                'gn': u'Especial',
                'he': u'מיוחד',
                'hi': u'विशेष',
                'hr': u'Posebno',
                'hsb': u'Specialnje',
                'ht': u'Espesyal',
                'hu': u'Speciális',
                'hy': u'Սպասարկող',
                'id': u'Istimewa',
                'io': u'Specala',
                'is': u'Kerfissíða',
                'it': u'Speciale',
                'ja': u'特別',
                'jv': u'Astamiwa',
                'ka': u'სპეციალური',
                'kab': u'Uslig',
                'kk': u'Арнайы',
                'kn': u'ವಿಶೇಷ',
                'ko': u'특수기능',
                'ksh':[u'Spezial', u'Shpezjal'],
                'ku': u'Taybet',
                'kv': u'Служебная',
                'la': u'Specialis',
                'lb': u'Spezial',
                'lbe': u'Къуллугъирал лажин',
                'li': u'Speciaal',
                'lij': u'Speciale',
                'lmo': u'Speciale',
                'lt': u'Specialus',
                'mk': u'Специјални',
                'ml': u'പ്രത്യേകം',
                'mr': u'विशेष',
                'ms': u'Khas',
                'mzn': u'ویژه',
                'nah': u'Especial',
                'nap': u'Speciale',
                'nds': u'Spezial',
                'nds-nl': u'Speciaal',
                'new': u'विशेष',
                'nl': u'Speciaal',
                'nn': u'Spesial',
                'no': u'Spesial',
                'oc': u'Especial',
                'os': u'Сæрмагонд',
                'pa': u'ਖਾਸ',
                'pdc': u'Spezial',
                'pl': u'Specjalna',
                'pt': u'Especial',
                'qu': u'Sapaq',
                'rmy':u'Uzalutno',
                'ru': u'Служебная',
                'sc': u'Speciale',
                'scn': u'Spiciali',
                'sk': u'Špeciálne',
                'sl': u'Posebno',
                'sq': u'Speciale',
                'sr': u'Посебно',
                'stq': u'Spezial',
                'su': u'Husus',
                'ta': u'சிறப்பு',
                'te': u'ప్రత్యేక',
                'tet': u'Espesiál',
                'tg': u'Вижа',
                'th': u'พิเศษ',
                'tlh': u"le'",
                'tr': u'Özel',
                'tt': u'Maxsus',
                'udm': u'Панель',
                'uk': u'Спеціальні',
                'ur': u'خاص',
                'uz': u'Maxsus',
                'vec':u'Speciale',
                'vi': u'Đặc biệt',
                'vls': u'Specioal',
                'vo': u'Patikos',
                'wa': u'Sipeciås',
                'xal': u'Көдлхнə',
                'yi': u'באַזונדער',
                'zea': u'Speciaol',
            },
            0: {
                '_default': None,
            },
            1: {
                '_default': u'Talk',
                'ab': u'Обсуждение',
                'af': u'Bespreking',
                'als': u'Diskussion',
                'an': u'Descusión',
                'ar': u'نقاش',
                'ast': u'Alderique',
                'av': u'Обсуждение',
                'ay': u'Discusión',
                'az': u'Müzakirə',
                'ba': u'Фекер алышыу',
                'bar': u'Diskussion',
                'bat-smg':u'Aptarėms',
                'bcl': u'Olay',
                'be': u'Размовы',
                'be-x-old': u'Абмеркаваньне',
                'bg': u'Беседа',
                'bm': u'Discuter',
                'bn': u'আলাপ',
                'bpy': u'য়্যারী',
                'br': u'Kaozeal',
                'bs': u'Razgovor',
                'bug': u'Pembicaraan',
                'ca': u'Discussió',
                'cbk-zam': u'Discusión',
                'ce': u'Дийца',
                'crh': [u'Muzakere', u'Музакере'],
                'cs': u'Diskuse',
                'csb': u'Diskùsëjô',
                'cu': u'Бесѣда',
                'cv': u'Сӳтсе явасси',
                'cy': u'Sgwrs',
                'da': u'Diskussion',
                'de': u'Diskussion',
                'dsb': u'Diskusija',
                'el': u'Συζήτηση',
                'eml': u'Discussione',
                'eo': u'Diskuto',
                'es': u'Discusión',
                'et': u'Arutelu',
                'eu': u'Eztabaida',
                'fa': u'بحث',
                'ff': u'Discuter',
                'fi': u'Keskustelu',
                'fiu-vro': u'Arotus',
                'fo': u'Kjak',
                'fr': u'Discuter',
                'frp': u'Discutar',
                'fur': u'Discussion',
                'fy': u'Oerlis',
                'ga': u'Plé',
                'gl': u'Conversa',
                'glk': u'بحث',
                'gn': u'Discusión',
                'he': u'שיחה',
                'hi': u'वार्ता',
                'hr': u'Razgovor',
                'hsb': u'Diskusija',
                'ht': u'Diskite',
                'hu': u'Vita',
                'hy': u'Քննարկում',
                'ia': u'Discussion',
                'id': [u'Pembicaraan', u'Bicara'],
                'io': u'Debato',
                'is': u'Spjall',
                'it': u'Discussione',
                'ja': u'ノート',
                'jv': u'Dhiskusi',
                'ka': u'განხილვა',
                'kab': u'Mmeslay',
                'kk': u'Талқылау',
                'kn': u'ಚರ್ಚೆಪುಟ',
                'ko': u'토론',
                'ksh': u'Klaaf',
                'ku': u'Nîqaş',
                'kv': u'Обсуждение',
                'la': u'Disputatio',
                'lb': u'Diskussioun',
                'lbe': u'Ихтилат',
                'li': u'Euverlèk',
                'lij': u'Discussione',
                'lmo': u'Discussione',
                'ln': u'Discuter',
                'lt': u'Aptarimas',
                'lv': u'Diskusija',
                'mg': u'Discuter',
                'mk': u'Разговор',
                'ml': u'സംവാദം',
                'mr': u'चर्चा',
                'ms': u'Perbincangan',
                'mzn': u'بحث',
                'nah': u'Discusión',
                'nap': u'Discussione',
                'nds': u'Diskuschoon',
                'nds-nl': u'Overleg',
                'new': u'खँलाबँला',
                'nl': u'Overleg',
                'nn': u'Diskusjon',
                'no': u'Diskusjon',
                'nv': u"Naaltsoos baa yinísht'į́",
                'oc': u'Discutir',
                'os': u'Дискусси',
                'pa': u'ਚਰਚਾ',
                'pdc': u'Diskussion',
                'pl': u'Dyskusja',
                'pms':u'Discussion',
                'pt': u'Discussão',
                'qu': u'Rimanakuy',
                'ro': u'Discuţie',
                'rmy': [u'Vakyarimata', u'Discuţie'],
                'ru': u'Обсуждение',
                'sa': u'संभाषणं',
                'sc': u'Contièndha',
                'scn': u'Discussioni',
                'sk': u'Diskusia',
                'sl': u'Pogovor',
                'sq': u'Diskutim',
                'sr': u'Разговор',
                'stq': u'Diskussion',
                'su': u'Obrolan',
                'sv': u'Diskussion',
                'ta': u'பேச்சு',
                'te': u'చర్చ',
                'tet': u'Diskusaun',
                'tg': u'Баҳс',
                'th': u'พูดคุย',
                'tlh': u"ja'chuq",
                'tr': u'Tartışma',
                'tt': u'Bäxäs',
                'ty': u'Discuter',
                'udm': u'Вераськон',
                'uk': u'Обговорення',
                'ur': u'تبادلۂ خیال',
                'uz': u'Munozara',
                'vec':u'Discussion',
                'vi': u'Thảo luận',
                'vls': u'Discuusje',
                'vo': u'Bespik',
                'wa': u'Copene',
                'wo': u'Discuter',
                'xal': u'Ухалвр',
                'yi': u'רעדן',
                'zea': u'Overleg',
            },
            2: {
                '_default': u'User',
                'ab': u'Участник',
                'af': u'Gebruiker',
                'als': u'Benutzer',
                'an': u'Usuario',
                'ar': u'مستخدم',
                'ast': u'Usuariu',
                'av': u'Участник',
                'ay': u'Usuario',
                'az': u'İstifadəçi',
                'ba': u'Ҡатнашыусы',
                'bar': u'Benutzer',
                'bat-smg': [u'Nauduotuos', u'Naudotojas'],
                'bcl': u'Paragamit',
                'be': u'Удзельнік',
                'be-x-old': u'Удзельнік',
                'bg': u'Потребител',
                'bm': u'Utilisateur',
                'bn': u'ব\u09cdযবহারকারী',
                'bpy': u'আতাকুরা',
                'br': u'Implijer',
                'bs': u'Korisnik',
                'bug': u'Pengguna',
                'ca': u'Usuari',
                'cbk-zam': u'Usuario',
                'ce': u'Юзер',
                'crh': [u'Qullanıcı', u'Къулланыджы'],
                'cs': u'Uživatel',
                'csb': u'Brëkòwnik',
                'cu': u'Польѕевател҄ь',
                'cv': u'Хутшăнакан',
                'cy': u'Defnyddiwr',
                'da': u'Bruger',
                'de': u'Benutzer',
                'dsb': u'Wužywaŕ',
                'el': u'Χρήστης',
                'eml': u'Utente',
                'eo': u'Vikipediisto',
                'es': u'Usuario',
                'et': u'Kasutaja',
                'eu': u'Lankide',
                'fa': u'کاربر',
                'ff': u'Utilisateur',
                'fi': u'Käyttäjä',
                'fiu-vro': u'Pruukja',
                'fo': u'Brúkari',
                'fr': u'Utilisateur',
                'frp': u'Utilisator',
                'fur': u'Utent',
                'fy': u'Meidogger',
                'ga': u'Úsáideoir',
                'gl': u'Usuario',
                'glk': u'کاربر',
                'gn': u'Usuario',
                'he': u'משתמש',
                'hi': u'सदस्य',
                'hr': u'Suradnik',
                'hsb': u'Wužiwar',
                'ht': u'Itilizatè',
                'hy': u'Մասնակից',
                'ia': u'Usator',
                'id': u'Pengguna',
                'io': u'Uzanto',
                'is': u'Notandi',
                'it': u'Utente',
                'ja': u'利用者',
                'jv': u'Panganggo',
                'ka': u'მომხმარებელი',
                'kab': u'Amseqdac',
                'kk': u'Қатысушы',
                'kn': u'ಸದಸ್ಯ',
                'ko': u'사용자',
                'ksh': [u'Metmaacher', u'Medmaacher'],
                'ku': u'Bikarhêner',
                'kv': u'Участник',
                'la': u'Usor',
                'lb': u'Benotzer',
                'lbe': u'Гьуртту хьума',
                'li': u'Gebroeker',
                'lij': u'Utente',
                'lmo': u'Utente',
                'ln': u'Utilisateur',
                'lt': u'Naudotojas',
                'lv': u'Lietotājs',
                'mg': u'Utilisateur',
                'mk': u'Корисник',
                'ml': u'ഉപയോക്താവ്',
                'mr': u'सदस्य',
                'ms': u'Pengguna',
                'mzn': u'کاربر',
                'nah': u'Usuario',
                'nap': u'Utente',
                'nds': u'Bruker',
                'nds-nl': u'Gebruker',
                'new': u'छ्येलेमि',
                'nl': u'Gebruiker',
                'nn': u'Brukar',
                'no': u'Bruker',
                'nv': u"Choinish'įįhí",
                'oc': u'Utilizaire',
                'os': u'Архайæг',
                'pa': u'ਮੈਂਬਰ',
                'pdc': u'Benutzer',
                'pl': u'Użytkownik',
                'pms':u'Utent',
                'pt': u'Usuário',
                'qu': u'Ruraq',
                'ro': u'Utilizator',
                'rmy':[u'Jeno', u'Utilizator'],
                'ru': u'Участник',
                'sa': u'योजकः',
                'sc': u'Utente',
                'scn': u'Utenti',
                'sk': u'Redaktor',
                'sl': u'Uporabnik',
                'sq': u'Përdoruesi',
                'sr': u'Корисник',
                'stq': u'Benutser',
                'su': u'Pamaké',
                'sv': u'Användare',
                'ta': u'பயனர்',
                'te': [u'సభ్యులు', u'సభ్యుడు'],
                'tet': u'Uza-na\'in',
                'tg': u'Корбар',
                'th': u'ผู้ใช' + u'\u0e49',
                'tlh': u"lo'wI'",
                'tr': u'Kullanıcı',
                'tt': u'Äğzä',
                'ty': u'Utilisateur',
                'udm': u'Викиавтор',
                'uk': u'Користувач',
                'ur': u'صارف',
                'uz': u'Foydalanuvchi',
                'vec':u'Utente',
                'vi': u'Thành viên',
                'vls': u'Gebruker',
                'vo': u'Geban',
                'wa': u'Uzeu',
                'wo': u'Utilisateur',
                'xal': u'Орлцач',
                'yi': u'באַניצער',
                'zea': u'Gebruker',
            },
            3: {
                '_default': u'User talk',
                'ab': u'Обсуждение участника',
                'af': u'Gebruikerbespreking',
                'als': u'Benutzer Diskussion',
                'an': u'Descusión usuario',
                'ar': u'نقاش المستخدم',
                'ast': u'Usuariu alderique',
                'av': u'Обсуждение участника',
                'ay': u'Usuario Discusión',
                'az': u'İstifadəçi müzakirəsi',
                'ba': u'Ҡатнашыусы м-н фекер алышыу',
                'bar': u'Benutzer Diskussion',
                'bat-smg':u'Nauduotuojė aptarėms',
                'bcl': u'Olay kan paragamit',
                'be': u'Размовы з удзельнікам',
                'be-x-old': u'Гутаркі ўдзельніка',
                'bg': u'Потребител беседа',
                'bm': u'Discussion Utilisateur',
                'bn': u'ব্যবহারকারী আলাপ',
                'bpy': u'আতাকুরার য়্যারী',
                'br': u'Kaozeadenn Implijer',
                'bs': u'Razgovor sa korisnikom',
                'bug': u'Pembicaraan Pengguna',
                'ca': u'Usuari Discussió',
                'cbk-zam': u'Usuario Discusión',
                'ce': u'Юзери дийца',
                'crh': [u'Qullanıcı muzakeresi', u'Къулланыджы музакереси'],
                'cs': u'Uživatel diskuse',
                'csb': u'Diskùsëjô brëkòwnika',
                'cu': u'Польѕевател бесѣда',
                'cv': u'Хутшăнаканăн канашлу страници',
                'cy': u'Sgwrs Defnyddiwr',
                'da': u'Brugerdiskussion',
                'de': u'Benutzer Diskussion',
                'dsb': u'Diskusija wužywarja',
                'el': u'Συζήτηση χρήστη',
                'eml': u'Discussioni utente',
                'eo': u'Vikipediista diskuto',
                'es': u'Usuario Discusión',
                'et': u'Kasutaja arutelu',
                'eu': u'Lankide eztabaida',
                'fa': u'بحث کاربر',
                'ff': u'Discussion Utilisateur',
                'fi': u'Keskustelu käyttäjästä',
                'fiu-vro': u'Pruukja arotus',
                'fo': u'Brúkari kjak',
                'fr': u'Discussion Utilisateur',
                'frp': u'Discussion Utilisator',
                'fur': u'Discussion utent',
                'fy': u'Meidogger oerlis',
                'ga': u'Plé úsáideora',
                'gl': u'Conversa Usuario',
                'glk': u'بحث کاربر',
                'gn': u'Usuario Discusión',
                'he': u'שיחת משתמש',
                'hi': u'सदस्य वार्ता',
                'hr': u'Razgovor sa suradnikom',
                'hsb': u'Diskusija z wužiwarjom',
                'ht': u'Diskisyon Itilizatè',
                'hu': u'User vita',
                'hy': u'Մասնակցի քննարկում',
                'ia': u'Discussion Usator',
                'id': u'Pembicaraan Pengguna',
                'io': u'Uzanto Debato',
                'is': u'Notandaspjall',
                'it': u'Discussioni utente',
                'ja': u'利用者‐会話',
                'jv': u'Dhiskusi Panganggo',
                'ka': u'მომხმარებელი განხილვა',
                'kab': u'Amyannan umsqedac',
                'kk': u'Қатысушы талқылауы',
                'kn': u'ಸದಸ್ಯರ ಚರ್ಚೆಪುಟ',
                'ko': u'사용자토론',
                'ksh': [u'Metmaacher Klaaf', u'Medmaacher Klaaf'],
                'ku': u'Bikarhêner nîqaş',
                'kv': u'Обсуждение участника',
                'la': u'Disputatio Usoris',
                'lb': u'Benotzer Diskussioun',
                'lbe': u'Гьуртту хьуминнал ихтилат',
                'li': u'Euverlèk gebroeker',
                'lij': u'Discussioni utente',
                'lmo': u'Discussioni utente',
                'ln': u'Discussion Utilisateur',
                'lt': u'Naudotojo aptarimas',
                'lv': u'Lietotāja diskusija',
                'mg': u'Discussion Utilisateur',
                'mk': u'Разговор со корисник',
                'ml': u'ഉപയോക്താവിന്റെ സംവാദം',
                'mr': u'सदस्य चर्चा',
                'ms': u'Perbincangan Pengguna',
                'mzn': u'بحث کاربر',
                'nah': u'Usuario Discusión',
                'nap': u'Discussioni utente',
                'nds': u'Bruker Diskuschoon',
                'nds-nl': u'Overleg gebruker',
                'new': u'छ्येलेमि खँलाबँला',
                'nl': u'Overleg gebruiker',
                'nn': u'Brukardiskusjon',
                'no': u'Brukerdiskusjon',
                'nv': u"Choinish'įįhí baa yinísht'į́",
                'oc': u'Discussion Utilizaire',
                'os': u'Архайæджы дискусси',
                'pa': u'ਮੈਂਬਰ ਚਰਚਾ',
                'pdc': u'Benutzer Diskussion',
                'pl': u'Dyskusja użytkownika',
                'pms':u'Ciaciarade',
                'pt': u'Usuário Discussão',
                'qu': u'Ruraq rimanakuy',
                'rmy':[u'Jeno vakyarimata', u'Discuţie Utilizator'],
                'ro': u'Discuţie Utilizator',
                'ru': u'Обсуждение участника',
                'sa': u'योजकसंभाषणं',
                'sc': u'Utente discussioni',
                'scn': u'Discussioni utenti',
                'sk': u'Diskusia s redaktorom',
                'sl': u'Uporabniški pogovor',
                'sq': u'Përdoruesi diskutim',
                'sr': u'Разговор са корисником',
                'stq': u'Benutser Diskussion',
                'su': u'Obrolan pamaké',
                'sv': u'Användardiskussion',
                'ta': u'பயனர் பேச்சு',
                'te': u'సభ్యులపై చర్చ',
                'tet': u'Diskusaun Uza-na\'in',
                'tg': u'Баҳси корбар',
                'th': u'คุยกับผู้ใช้',
                'tlh': u"lo'wI' ja'chuq",
                'tr': u'Kullanıcı mesaj',
                'tt': u'Äğzä bäxäse',
                'ty': u'Discussion Utilisateur',
                'udm': u'Викиавтор сярысь вераськон',
                'uk': u'Обговорення користувача',
                'ur': u'تبادلۂ خیال صارف',
                'uz': u'Foydalanuvchi munozarasi',
                'vec':u'Discussion utente',
                'vi': u'Thảo luận Thành viên',
                'vls': u'Discuusje gebruker',
                'vo': u'Gebanibespik',
                'wa': u'Uzeu copene',
                'wo': u'Discussion Utilisateur',
                'xal': u'Орлцачна тускар ухалвр',
                'yi': u'באַניצער רעדן',
                'zea': u'Overleg gebruker',
            },
            4: {
                '_default': u'Project',
            },
            5: {
                '_default': u'Project talk',
            },
            6: {
                '_default': u'Image',
                'ab': u'Изображение',
                'af': u'Beeld',
                'als': u'Bild',
                'an': u'Imachen',
                'ar': u'صورة',
                'ast': u'Imaxe',
                'av': u'Изображение',
                'ay': u'Imagen',
                'az': u'Şəkil',
                'ba': u'Рәсем',
                'bar': u'Bild',
                'bat-smg':u'Abruozdielis',
                'bcl': u'Ladawan',
                'be': u'Выява',
                'be-x-old': u'Выява',
                'bg': u'Картинка',
                'bn': u'চিত্র',
                'bpy': u'ছবি',
                'br': u'Skeudenn',
                'bs': u'Slika',
                'bug': u'Berkas',
                'ca': u'Imatge',
                'cbk-zam': u'Imagen',
                'cbs': u'Òbrôzk',
                'ce': u'Сурт',
                'crh': [u'Resim', u'Ресим'],
                'cs': u'Soubor',
                'csb': u'Òbrôzk',
                'cu': u'Видъ',
                'cv': u'Ӳкерчĕк',
                'cy': u'Delwedd',
                'da': u'Billede',
                'de': u'Bild',
                'dsb': u'Wobraz',
                'el': u'Εικόνα',
                'eml': u'Immagine',
                'eo': u'Dosiero',
                'es': u'Imagen',
                'et': u'Pilt',
                'eu': u'Irudi',
                'fa': u'تصویر',
                'fi': u'Kuva',
                'fiu-vro': u'Pilt',
                'fo': u'Mynd',
                'frp': u'Émâge',
                'fur': u'Figure',
                'fy': u'Ofbyld',
                'ga': u'Íomhá',
                'gl': u'Imaxe',
                'glk': u'تصویر',
                'gn': u'Imagen',
                'he': u'תמונה',
                'hi': u'चित्र',
                'hr': u'Slika',
                'hsb': u'Wobraz',
                'ht': u'Imaj',
                'hu': u'Kép',
                'hy': u'Պատկեր',
                'ia': u'Imagine',
                'id': [u'Berkas', u'Gambar'],
                'io': u'Imajo',
                'is': u'Mynd',
                'it': u'Immagine',
                'ja': u'画像',
                'jv': u'Gambar',
                'ka': u'სურათი',
                'kab': u'Tugna',
                'kk': u'Сурет',
                'kn': u'ಚಿತ್ರ',
                'ko': u'그림',
                'ksh':[u'Beld', u'Belld'],
                'ku': u'Wêne',
                'kv': u'Изображение',
                'la': u'Imago',
                'lb': u'Bild',
                'lbe': u'Сурат',
                'li': u'Plaetje',
                'lij': u'Immagine',
                'lmo': u'Immagine',
                'lt': u'Vaizdas',
                'lv': u'Attēls',
                'mk': u'Слика',
                'ml': u'ചിത്രം',
                'mr': u'चित्र',
                'ms': u'Imej',
                'mzn': u'تصویر',
                'nah': u'Imagen',
                'nap': u'Immagine',
                'nds': u'Bild',
                'nds-nl': u'Ofbeelding',
                'new': u'किपा',
                'nl': u'Afbeelding',
                'nn': u'Fil',
                'no': u'Bilde',
                'nv': u"E'elyaaígíí",
                'oc': u'Imatge',
                'os': u'Ныв',
                'pa': u'ਤਸਵੀਰ',
                'pdc': u'Bild',
                'pl': u'Grafika',
                'pms':u'Figura',
                'pt': u'Imagem',
                'qu': u'Rikcha',
                'rmy':[u'Chitro', u'Imagine'],
                'ro': u'Imagine',
                'ru': u'Изображение',
                'sa': u'चित्रं',
                'sc': u'Immàgini',
                'scn': u'Mmàggini',
                'sk': u'Obrázok',
                'sl': u'Slika',
                'sq': u'Figura',
                'sr': u'Слика',
                'stq': u'Bielde',
                'su': u'Gambar',
                'sv': u'Bild',
                'ta': u'படிமம்',
                'te': u'బొమ్మ',
                'tet': u'Imajen',
                'tg': u'Акс',
                'th': u'ภาพ',
                'tlh': u'nagh beQ',
                'tr': u'Resim',
                'tt': u'Räsem',
                'udm': u'Суред',
                'uk': u'Зображення',
                'ur': u'تصویر',
                'uz': u'Tasvir',
                'vec':u'Imagine',
                'vi': u'Hình',
                'vls': u'Ofbeeldienge',
                'vo': u'Magod',
                'wa': u'Imådje',
                'xal': u'Зург',
                'yi': u'בילד',
                'zea': u'Plaetje',
            },
            7: {
                '_default': u'Image talk',
                'ab': u'Обсуждение изображения',
                'af': u'Beeldbespreking',
                'als': u'Bild Diskussion',
                'an': u'Descusión imachen',
                'ar': u'نقاش الصورة',
                'ast': u'Imaxe alderique',
                'av': u'Обсуждение изображения',
                'ay': u'Imagen Discusión',
                'az': u'Şəkil müzakirəsi',
                'ba': u'Рәсем б-са фекер алышыу',
                'bar': u'Bild Diskussion',
                'bat-smg':u'Abruozdielė aptarėms',
                'bcl': u'Olay sa ladawan',
                'be': u'Размовы пра выяву',
                'be-x-old': u'Абмеркаваньне выявы',
                'bg': u'Картинка беседа',
                'bm': u'Discussion Image',
                'bn': u'চিত্র আলাপ',
                'bpy': u'ছবি য়্যারী',
                'br': u'Kaozeadenn Skeudenn',
                'bs': u'Razgovor o slici',
                'bug': u'Pembicaraan Berkas',
                'ca': u'Imatge Discussió',
                'cbk-zam': u'Imagen Discusión',
                'ce': u'Сурти дийца',
                'crh': [u'Resim muzakeresi', u'Ресим музакереси'],
                'cs': u'Soubor diskuse',
                'csb': u'Diskùsëjô òbrôzków',
                'cu': u'Вида бесѣда',
                'cv': u'Ӳкерчĕке сӳтсе явмалли',
                'cy': u'Sgwrs Delwedd',
                'da': u'Billeddiskussion',
                'de': u'Bild Diskussion',
                'dsb': u'Diskusija wó wobrazu',
                'el': u'Συζήτηση εικόνας',
                'eml': u'Discussioni immagine',
                'eo': u'Dosiera diskuto',
                'es': u'Imagen Discusión',
                'et': u'Pildi arutelu',
                'eu': u'Irudi eztabaida',
                'fa': u'بحث تصویر',
                'ff': u'Discussion Image',
                'fi': u'Keskustelu kuvasta',
                'fiu-vro': u'Pildi arotus',
                'fo': u'Mynd kjak',
                'fr': u'Discussion Image',
                'frp': u'Discussion Émâge',
                'fur': u'Discussion figure',
                'fy': u'Ofbyld oerlis',
                'ga': u'Plé íomhá',
                'gl': u'Conversa Imaxe',
                'glk': u'بحث تصویر',
                'gn': u'Imagen Discusión',
                'he': u'שיחת תמונה',
                'hi': u'चित्र वार्ता',
                'hr': u'Razgovor o slici',
                'hsb': u'Diskusija k wobrazej',
                'ht': u'Diskisyon Imaj',
                'hu': u'Kép vita',
                'hy': u'Պատկերի քննարկում',
                'ia': u'Discussion Imagine',
                'id': [u'Pembicaraan Berkas', u'Pembicaraan Gambar'],
                'io': u'Imajo Debato',
                'is': u'Myndaspjall',
                'it': u'Discussioni immagine',
                'ja': u'画像‐ノート',
                'jv': u'Dhiskusi Gambar',
                'ka': u'სურათი განხილვა',
                'kab': u'Amyannan n tugna',
                'kk': u'Сурет талқылауы',
                'kn': u'ಚಿತ್ರ ಚರ್ಚೆಪುಟ',
                'ko': u'그림토론',
                'ksh':[u'Belder Klaaf', u'Bellder Klaaf'],
                'ku': u'Wêne nîqaş',
                'kv': u'Обсуждение изображения',
                'la': u'Disputatio Imaginis',
                'lb': u'Bild Diskussioun',
                'lbe': u'Суратраясса ихтилат',
                'li': u'Euverlèk plaetje',
                'lij': u'Discussioni immagine',
                'lmo': u'Discussioni immagine',
                'ln': u'Discussion Image',
                'lt': u'Vaizdo aptarimas',
                'lv': u'Attēla diskusija',
                'mg': u'Discussion Image',
                'mk': u'Разговор за слика',
                'ml': u'ചിത്രത്തിന്റെ സംവാദം',
                'mr': u'चित्र चर्चा',
                'ms': u'Perbincangan Imej',
                'mzn': u'بحث تصویر',
                'nah': u'Imagen Discusión',
                'nap': u'Discussioni immagine',
                'nds': u'Bild Diskuschoon',
                'nds-nl': u'Overleg ofbeelding',
                'new': u'किपा खँलाबँला',
                'nl': u'Overleg afbeelding',
                'nn': u'Fildiskusjon',
                'no': u'Bildediskusjon',
                'nv': u"E'elyaaígíí baa yinísht'į́",
                'oc': u'Discussion Imatge',
                'os': u'Нывы тыххæй дискусси',
                'pa': u'ਤਸਵੀਰ ਚਰਚਾ',
                'pdc': u'Bild Diskussion',
                'pl': u'Dyskusja grafiki',
                'pms':u'Discussion dla figura',
                'pt': u'Imagem Discussão',
                'qu': u'Rikcha rimanakuy',
                'rmy':[u'Chitro vakyarimata', u'Discuţie Imagine'],
                'ro': u'Discuţie Imagine',
                'ru': u'Обсуждение изображения',
                'sa': u'चित्रसंभाषणं',
                'sc': u'Immàgini contièndha',
                'scn': u'Discussioni mmàggini',
                'sk': u'Diskusia k obrázku',
                'sl': u'Pogovor o sliki',
                'sq': u'Figura diskutim',
                'sr': u'Разговор о слици',
                'stq': u'Bielde Diskussion',
                'su': u'Obrolan gambar',
                'sv': u'Bilddiskussion',
                'ta': [u'படிமப் பேச்சு', u'உருவப் பேச்சு'],
                'te': u'బొమ్మపై చర్చ',
                'tet': u'Diskusaun Imajen',
                'tg': u'Баҳси акс',
                'th': u'คุยเรื่องภาพ',
                'tlh': u"nagh beQ ja'chuq",
                'tr': u'Resim tartışma',
                'tt': u'Räsem bäxäse',
                'ty': u'Discussion Image',
                'udm': u'Суред сярысь вераськон',
                'uk': u'Обговорення зображення',
                'ur': u'تبادلۂ خیال تصویر',
                'uz': u'Tasvir munozarasi',
                'vec':u'Discussion imagine',
                'vi': u'Thảo luận Hình',
                'vls': u'Discuusje ofbeeldienge',
                'vo': u'Magodibespik',
                'wa': u'Imådje copene',
                'wo': u'Discussion Image',
                'xal': u'Зургин тускар ухалвр',
                'yi': u'בילד רעדן',
                'zea': u'Overleg plaetje',
            },
            8: {
                '_default': u'MediaWiki',
                'ar': u'ميدياويكي',
                'az': u'MediyaViki',
                'bcl': u'MediaWiki',
                'bg': u'МедияУики',
                'bpy': u'মিডিয়াউইকি',
                'bs': u'MedijaViki',
                'cy': u'MediaWici',
                'ce': u'МедйаВики',
                'crh': [u'MediaViki', u'МедиаВики'],
                'fa': u'مدیاویکی',
                'fi': u'Järjestelmäviesti',
                'fo': u'MidiaWiki',
                'glk': u'مدیاویکی',
                'he': u'מדיה ויקי',
                'ht': u'MedyaWiki',
                'is': u'Melding',
                'ka': u'მედიავიკი',
                'kk': u'МедиаУики',
                'kn': u'ಮೀಡಿಯವಿಕಿ',
                'ksh':[u'MediaWiki', u'MedijaWikki'],
                'mk': u'МедијаВики',
                'ml': u'മീഡിയവിക്കി',
                'mzn': u'مدیاویکی',
                'new': u'मिडियाविकि',
                'pa': u'ਮੀਡੀਆਵਿਕਿ',
                'rmy':u'MediyaViki',
                'sr': u'МедијаВики',
                'ta': u'மீடியாவிக்கி',
                'te': u'మీడియావికీ',
                'tg': u'Медиавики',
                'th': u'มีเดียวิกิ',
                'tr': u'MedyaViki',
                'ur': u'میڈیاوکی',
                'vo': u'Sitanuns',
                'yi': u'מעדיעװיקי',
            },
            9: {
                '_default': u'MediaWiki talk',
                'ab': u'Обсуждение MediaWiki',
                'af': u'MediaWikibespreking',
                'als': u'MediaWiki Diskussion',
                'an': u'Descusión MediaWiki',
                'ar': u'نقاش ميدياويكي',
                'ast': u'MediaWiki alderique',
                'av': u'Обсуждение MediaWiki',
                'ay': u'MediaWiki Discusión',
                'az': u'MediyaViki müzakirəsi',
                'ba': u'MediaWiki б-са фекер алышыу',
                'bar': u'MediaWiki Diskussion',
                'bat-smg':u'MediaWiki aptarėms',
                'bcl': u'Olay sa MediaWiki',
                'be': u'Размовы пра MediaWiki',
                'be-x-old': u'Абмеркаваньне MediaWiki',
                'bg': u'МедияУики беседа',
                'bm': u'Discussion MediaWiki',
                'bn': u'MediaWiki আলাপ',
                'bpy': u'মিডিয়াউইকির য়্যারী',
                'br': u'Kaozeadenn MediaWiki',
                'bs': u'Razgovor o MedijaVikiju',
                'bug': u'Pembicaraan MediaWiki',
                'ca': u'MediaWiki Discussió',
                'cbk-zam': u'MediaWiki Discusión',
                'ce': u'МедйаВики дийца',
                'crh': [u'MediaViki muzakeresi', u'МедиаВики музакереси'],
                'cs': u'MediaWiki diskuse',
                'csb': u'Diskùsëjô MediaWiki',
                'cu': u'MediaWiki бесѣда',
                'cv': u'MediaWiki сӳтсе явмалли',
                'cy': u'Sgwrs MediaWici',
                'da': u'MediaWiki-diskussion',
                'de': u'MediaWiki Diskussion',
                'dsb': u'MediaWiki diskusija',
                'eml': u'Discussioni MediaWiki',
                'eo': u'MediaWiki diskuto',
                'es': u'MediaWiki Discusión',
                'et': u'MediaWiki arutelu',
                'eu': u'MediaWiki eztabaida',
                'fa': u'بحث مدیاویکی',
                'ff': u'Discussion MediaWiki',
                'fi': u'Keskustelu järjestelmäviestistä',
                'fiu-vro': u'MediaWiki arotus',
                'fo': u'MidiaWiki kjak',
                'fr': u'Discussion MediaWiki',
                'frp': u'Discussion MediaWiki',
                'fur': u'Discussion MediaWiki',
                'fy': u'MediaWiki oerlis',
                'ga': u'Plé MediaWiki',
                'gl': u'Conversa MediaWiki',
                'glk': u'بحث مدیاویکی',
                'gn': u'MediaWiki Discusión',
                'he': u'שיחת מדיה ויקי',
                'hr': u'MediaWiki razgovor',
                'hsb': u'MediaWiki diskusija',
                'ht': u'Diskisyon MedyaWiki',
                'hu': u'MediaWiki vita',
                'hy': u'MediaWiki քննարկում',
                'ia': u'Discussion MediaWiki',
                'id': u'Pembicaraan MediaWiki',
                'io': u'MediaWiki Debato',
                'is': u'Meldingarspjall',
                'it': u'Discussioni MediaWiki',
                'ja': u'MediaWiki‐ノート',
                'jv': u'Dhiskusi MediaWiki',
                'ka': u'მედიავიკი განხილვა',
                'kab': u'Amyannan n MediaWiki',
                'kk': u'МедиаУики талқылауы',
                'kn': u'ಮೀಡೀಯವಿಕಿ ಚರ್ಚೆ',
                'ko': u'MediaWiki토론',
                'ksh':[u'MediaWiki Klaaf', u'MedijaWikki Klaaf'],
                'ku': u'MediaWiki nîqaş',
                'kv': u'Обсуждение MediaWiki',
                'la': u'Disputatio MediaWiki',
                'lb': u'MediaWiki Diskussioun',
                'lbe': u'MediaWikiлиясса ихтилат',
                'li': u'Euverlèk MediaWiki',
                'lij': u'Discussioni MediaWiki',
                'lmo': u'Discussioni MediaWiki',
                'ln': u'Discussion MediaWiki',
                'lt': u'MediaWiki aptarimas',
                'lv': u'MediaWiki diskusija',
                'mg': u'Discussion MediaWiki',
                'mk': u'Разговор за МедијаВики',
                'ml': u'മീഡിയവിക്കി സംവാദം',
                'ms': u'Perbincangan MediaWiki',
                'mzn': u'بحث مدیاویکی',
                'nah': u'MediaWiki Discusión',
                'nap': u'Discussioni MediaWiki',
                'nds': u'MediaWiki Diskuschoon',
                'nds-nl': u'Overleg MediaWiki',
                'new': u'मिडियाविकि खँलाबँला',
                'nl': u'Overleg MediaWiki',
                'nn': u'MediaWiki-diskusjon',
                'no': u'MediaWiki-diskusjon',
                'nv': u"MediaWiki baa yinísht'į́",
                'oc': u'Discussion MediaWiki',
                'os': u'Дискусси MediaWiki',
                'pa': u'ਮੀਡੀਆਵਿਕਿ ਚਰਚਾ',
                'pdc': u'MediaWiki Diskussion',
                'pl': u'Dyskusja MediaWiki',
                'pms':u'Discussion dla MediaWiki',
                'pt': u'MediaWiki Discussão',
                'qu': u'MediaWiki rimanakuy',
                'rmy':[u'MediyaViki vakyarimata', u'Discuţie MediaWiki'],
                'ro': u'Discuţie MediaWiki',
                'ru': u'Обсуждение MediaWiki',
                'scn': u'Discussioni MediaWiki',
                'sk': u'Diskusia k MediaWiki',
                'sl': u'Pogovor o MediaWiki',
                'sq': u'MediaWiki diskutim',
                'sr': u'Разговор о МедијаВикију',
                'stq': u'MediaWiki Diskussion',
                'su': u'Obrolan MediaWiki',
                'sv': u'MediaWiki-diskussion',
                'ta': u'மீடியாவிக்கி பேச்சு',
                'te': u'మీడియావికీ చర్చ',
                'tet': u'Diskusaun MediaWiki',
                'tg': u'Баҳси медиавики',
                'th': u'คุยเรื่องมีเดียวิกิ',
                'tlh': u"MediaWiki ja'chuq",
                'tr': u'MedyaViki tartışma',
                'tt': u'MediaWiki bäxäse',
                'ty': u'Discussion MediaWiki',
                'udm': u'MediaWiki сярысь вераськон',
                'uk': u'Обговорення MediaWiki',
                'ur': u'تبادلۂ خیال میڈیاوکی',
                'uz': u'MediaWiki munozarasi',
                'vec':u'Discussion MediaWiki',
                'vi': u'Thảo luận MediaWiki',
                'vls': u'Discuusje MediaWiki',
                'vo': u'Bespik dö sitanuns',
                'wa': u'MediaWiki copene',
                'wo': u'Discussion MediaWiki',
                'xal': u'MediaWiki тускар ухалвр',
                'yi': u'מעדיעװיקי רעדן',
                'zea': u'Overleg MediaWiki',
            },
            10: {
                '_default':u'Template',
                'ab': u'Шаблон',
                'af': u'Sjabloon',
                'als': u'Vorlage',
                'an': u'Plantilla',
                'ar': u'قالب',
                'ast': u'Plantía',
                'av': u'Шаблон',
                'ay': u'Plantilla',
                'az': u'Şablon',
                'ba': u'Ҡалып',
                'bar': u'Vorlage',
                'bat-smg':u'Šabluons',
                'bcl': u'Plantilya',
                'be': u'Шаблон',
                'be-x-old': u'Шаблён',
                'bg': u'Шаблон',
                'bm': u'Modèle',
                'bpy': u'মডেল',
                'br': u'Patrom',
                'bs': u'Šablon',
                'bug': u'Templat',
                'ca': u'Plantilla',
                'cbk-zam': u'Plantilla',
                'cbs': u'Szablóna',
                'ce': u'Дакъа',
                'crh': [u'Şablon', u'Шаблон'],
                'cs': u'Šablona',
                'csb': u'Szablóna',
                'cu': u'Образьць',
                'cv': u'Шаблон',
                'cy': u'Nodyn',
                'da': u'Skabelon',
                'de': u'Vorlage',
                'dsb': u'Pśedłoga',
                'el': u'Πρότυπο',
                'eo': u'Ŝablono',
                'es': u'Plantilla',
                'et': u'Mall',
                'eu': u'Txantiloi',
                'fa': u'الگو',
                'ff': u'Modèle',
                'fi': u'Malline',
                'fiu-vro': u'Näüdüs',
                'fo': u'Fyrimynd',
                'fr': u'Modèle',
                'frp': u'Modèlo',
                'fur': u'Model',
                'fy': u'Berjocht',
                'ga': u'Teimpléad',
                'gl': u'Modelo',
                'glk': u'الگو',
                'gn': u'Plantilla',
                'he': u'תבנית',
                'hi': u'साँचा',
                'hr': u'Predložak',
                'hsb': u'Předłoha',
                'ht': u'Modèl',
                'hu': u'Sablon',
                'hy': u'Կաղապար',
                'ia': u'Patrono',
                'id': u'Templat',
                'io': u'Shablono',
                'is': u'Snið',
                'jv': u'Cithakan',
                'ka': u'თარგი',
                'kab': u'Talɣa',
                'kk': u'Үлгі',
                'kn': u'ಟೆಂಪ್ಲೇಟು',
                'ko': u'틀',
                'ksh':u'Schablon',
                'ku': u'Şablon',
                'kv': u'Шаблон',
                'la': u'Formula',
                'lb': u'Schabloun',
                'lbe': u'Шаблон',
                'li': u'Sjabloon',
                'ln': u'Modèle',
                'lt': u'Šablonas',
                'lv': u'Veidne',
                'mg': u'Modèle',
                'mk': u'Шаблон',
                'ml': u'ഫലകം',
                'mr': u'साचा',
                'ms': u'Templat',
                'mzn': u'الگو',
                'nah': u'Plantilla',
                'nds': u'Vörlaag',
                'nds-nl': u'Sjabloon',
                'nl': u'Sjabloon',
                'nn': u'Mal',
                'no': u'Mal',
                'oc': u'Modèl',
                'os': u'Шаблон',
                'pa': u'ਨਮੂਨਾ',
                'pdc': u'Vorlage',
                'pl': u'Szablon',
                'pms': u'Stamp',
                'pt': u'Predefinição',
                'qu': u'Plantilla',
                'rmy':[u'Sikavno', u'Format'],
                'ro': u'Format',
                'ru': u'Шаблон',
                'sk': u'Šablóna',
                'sl': u'Predloga',
                'sq': u'Stampa',
                'sr': u'Шаблон',
                'stq': u'Foarloage',
                'su': u'Citakan',
                'sv': u'Mall',
                'ta': u'வார்ப்புரு',
                'te': u'మూస',
                'tg': u'Шаблон',
                'th': u'แม่แบบ',
                'tlh': u"chen'ay'",
                'tr': u'Şablon',
                'tt': u'Ürnäk',
                'ty': u'Modèle',
                'udm': u'Шаблон',
                'uk': u'Шаблон',
                'ur': u'سانچہ',
                'uz': u'Shablon',
                'vi': u'Tiêu bản',
                'vls': u'Patrôon',
                'vo': u'Samafomot',
                'wa': u'Modele',
                'wo': u'Modèle',
                'xal': u'Зура',
                'yi': u'מוסטער',
                'zea': u'Sjabloon',
            },
            11: {
                '_default': u'Template talk',
                'ab': u'Обсуждение шаблона',
                'af': u'Sjabloonbespreking',
                'als': u'Vorlage Diskussion',
                'an': u'Descusión plantilla',
                'ar': u'نقاش القالب',
                'ast': u'Plantía alderique',
                'av': u'Обсуждение шаблона',
                'ay': u'Plantilla Discusión',
                'az': u'Şablon müzakirəsi',
                'ba': u'Ҡалып б-са фекер алышыу',
                'bar': u'Vorlage Diskussion',
                'bat-smg':u'Šabluona aptarėms',
                'bcl': u'Olay sa plantilya',
                'be': u'Размовы пра шаблон',
                'be-x-old': u'Абмеркаваньне шаблёну',
                'bg': u'Шаблон беседа',
                'bm': u'Discussion Modèle',
                'bpy': u'মডেলর য়্যারী',
                'br': u'Kaozeadenn Patrom',
                'bs': u'Razgovor o šablonu',
                'bug': u'Pembicaraan Templat',
                'ca': u'Plantilla Discussió',
                'cbk-zam': u'Plantilla Discusión',
                'ce': u'Дакъан дийца',
                'crh': [u'Şablon muzakeresi', u'Шаблон музакереси'],
                'cs': u'Šablona diskuse',
                'csb': u'Diskùsëjô Szablónë',
                'cu': u'Образьца бесѣда',
                'cv': u'Шаблона сӳтсе явмалли',
                'cy': u'Sgwrs Nodyn',
                'da': u'Skabelondiskussion',
                'de': u'Vorlage Diskussion',
                'dsb': u'Diskusija wó pśedłoze',
                'el': u'Συζήτηση προτύπου',
                'eml': u'Discussioni template',
                'eo': u'Ŝablona diskuto',
                'es': u'Plantilla Discusión',
                'et': u'Malli arutelu',
                'eu': u'Txantiloi eztabaida',
                'fa': u'بحث الگو',
                'ff': u'Discussion Modèle',
                'fi': u'Keskustelu mallineesta',
                'fiu-vro': u'Näüdüse arotus',
                'fo': u'Fyrimynd kjak',
                'fr': u'Discussion Modèle',
                'frp': u'Discussion Modèlo',
                'fur': u'Discussion model',
                'fy': u'Berjocht oerlis',
                'ga': u'Plé teimpléid',
                'gl': u'Conversa Modelo',
                'glk': u'بحث الگو',
                'gn': u'Plantilla Discusión',
                'he': u'שיחת תבנית',
                'hi': u'साँचा वार्ता',
                'hr': u'Razgovor o predlošku',
                'hsb': u'Diskusija k předłoze',
                'ht': u'Diskisyon Modèl',
                'hu': u'Sablon vita',
                'hy': u'Կաղապարի քննարկում',
                'ia': u'Discussion Patrono',
                'id': u'Pembicaraan Templat',
                'io': u'Shablono Debato',
                'is': u'Sniðaspjall',
                'it': u'Discussioni template',
                'ja': u'Template‐ノート',
                'jv': u'Dhiskusi Cithakan',
                'ka': u'თარგი განხილვა',
                'kab': u'Amyannan n talɣa',
                'kk': u'Үлгі талқылауы',
                'kn': u'ಟೆಂಪ್ಲೇಟು ಚರ್ಚೆ',
                'ko': u'틀토론',
                'ksh':u'Schablone Klaaf',
                'ku': u'Şablon nîqaş',
                'kv': u'Обсуждение шаблона',
                'la': u'Disputatio Formulae',
                'lb': u'Schabloun Diskussioun',
                'lbe': u'Шаблондалиясса ихтилат',
                'li': u'Euverlèk sjabloon',
                'lij': u'Discussioni template',
                'lmo': u'Discussioni template',
                'ln': u'Discussion Modèle',
                'lt': u'Šablono aptarimas',
                'lv': u'Veidnes diskusija',
                'mg': u'Discussion Modèle',
                'mk': u'Разговор за шаблон',
                'ml': u'ഫലകത്തിന്റെ സംവാദം',
                'mr': u'साचा चर्चा',
                'ms': u'Perbincangan Templat',
                'mzn': u'بحث الگو',
                'nah': u'Plantilla Discusión',
                'nap': u'Discussioni template',
                'nds': u'Vörlaag Diskuschoon',
                'nds-nl': u'Overleg sjabloon',
                'nl': u'Overleg sjabloon',
                'nn': u'Maldiskusjon',
                'no': u'Maldiskusjon',
                'oc': u'Discussion Modèl',
                'os': u'Шаблоны тыххæй дискусси',
                'pa': u'ਨਮੂਨਾ ਚਰਚਾ',
                'pdc': u'Vorlage Diskussion',
                'pl': u'Dyskusja szablonu',
                'pms':u'Discussion dlë stamp',
                'pt': u'Predefinição Discussão',
                'qu': u'Plantilla rimanakuy',
                'rmy':[u'Sikavno vakyarimata', u'Discuţie Format'],
                'ro': u'Discuţie Format',
                'ru': u'Обсуждение шаблона',
                'scn': u'Discussioni template',
                'sk': u'Diskusia k šablóne',
                'sl': u'Pogovor o predlogi',
                'sq': u'Stampa diskutim',
                'sr': u'Разговор о шаблону',
                'stq': u'Foarloage Diskussion',
                'su': u'Obrolan citakan',
                'sv': u'Malldiskussion',
                'ta': u'வார்ப்புரு பேச்சு',
                'te': u'మూస చర్చ',
                'tet': u'Diskusaun Template',
                'tg': u'Баҳси шаблон',
                'th': u'คุยเรื่องแม่แบบ',
                'tlh': u"chen'ay' ja'chuq",
                'tr': u'Şablon tartışma',
                'tt': u'Ürnäk bäxäse',
                'ty': u'Discussion Modèle',
                'udm': u'Шаблон сярысь вераськон',
                'uk': u'Обговорення шаблону',
                'ur': u'تبادلۂ خیال سانچہ',
                'uz': u'Shablon munozarasi',
                'vec':u'Discussion template',
                'vi': u'Thảo luận Tiêu bản',
                'vls': u'Discuusje patrôon',
                'vo': u'Samafomotibespik',
                'wa': u'Modele copene',
                'wo': u'Discussion Modèle',
                'xal': u'Зуран тускар ухалвр',
                'yi': u'מוסטער רעדן',
                'zea': u'Overleg sjabloon',
            },
            12: {
                '_default': u'Help',
                'ab': u'Справка',
                'af': u'Hulp',
                'als': u'Hilfe',
                'an': u'Aduya',
                'ar': u'مساعدة',
                'ast': u'Aida',
                'av': u'Справка',
                'ay': u'Ayuda',
                'az': u'Kömək',
                'ba': u'Белешмә',
                'bar': u'Hilfe',
                'bat-smg':u'Pagelba',
                'bcl': u'Tabang',
                'be': u'Даведка',
                'be-x-old': u'Дапамога',
                'bg': u'Помощ',
                'bm': u'Aide',
                'bpy': u'পাংলাক',
                'br': u'Skoazell',
                'bs': u'Pomoć',
                'bug': u'Bantuan',
                'ca': u'Ajuda',
                'cbk-zam': u'Ayuda',
                'cbs': u'Pòmòc',
                'ce': u'ГІо',
                'crh': [u'Yardım', u'Ярдым'],
                'cs': u'Nápověda',
                'csb': u'Pòmòc',
                'cu': u'Помощь',
                'cv': u'Пулăшу',
                'cy': u'Cymorth',
                'da': u'Hjælp',
                'de': u'Hilfe',
                'dsb': u'Pomoc',
                'el': u'Βοήθεια',
                'eml': u'Aiuto',
                'eo': u'Helpo',
                'es': u'Ayuda',
                'et': u'Juhend',
                'eu': u'Laguntza',
                'fa': u'راهنما',
                'ff': u'Aide',
                'fi': u'Ohje',
                'fiu-vro': u'Oppus',
                'fo': u'Hjálp',
                'fr': u'Aide',
                'frp': u'Éde',
                'fur': u'Jutori',
                'fy': u'Hulp',
                'ga': u'Cabhair',
                'gl': u'Axuda',
                'glk': u'راهنما',
                'gn': u'Ayuda',
                'he': u'עזרה',
                'hr': u'Pomoć',
                'hsb': u'Pomoc',
                'ht': u'Èd',
                'hu': u'Segítség',
                'hy': u'Օգնություն',
                'ia': u'Adjuta',
                'id': u'Bantuan',
                'io': u'Helpo',
                'is': u'Hjálp',
                'it': u'Aiuto',
                'jv': u'Pitulung',
                'ka': u'დახმარება',
                'kab': u'Tallat',
                'kk': u'Анықтама',
                'kn': u'ಸಹಾಯ',
                'ko': u'도움말',
                'ksh':[u'Hölp', u'Hülp'],
                'ku': u'Alîkarî',
                'kv': u'Справка',
                'la': u'Auxilium',
                'lb': u'Hëllef',
                'lbe': u'Кумаг',
                'lij': u'Aiuto',
                'lmo': u'Aiuto',
                'ln': u'Aide',
                'lt': u'Pagalba',
                'lv': u'Palīdzība',
                'mg': u'Aide',
                'mk': u'Помош',
                'ml': u'സഹായം',
                'ms': u'Bantuan',
                'mzn': u'راهنما',
                'nah': u'Ayuda',
                'nap': u'Aiuto',
                'nds': u'Hülp',
                'nds-nl': u'Hulpe',
                'new': u'ग्वाहालि',
                'nn': u'Hjelp',
                'no': u'Hjelp',
                'nv': u"Aná'álwo'",
                'oc': u'Ajuda',
                'os': u'Æххуыс',
                'pa': u'ਮਦਦ',
                'pdc': u'Hilfe',
                'pl': u'Pomoc',
                'pms':u'Agiut',
                'pt': u'Ajuda',
                'qu': u'Yanapa',
                'rmy':[u'Zhutipen', u'Ajutor'],
                'ro': u'Ajutor',
                'ru': u'Справка',
                'sa': u'उपकारः',
                'scn': u'Aiutu',
                'sk': u'Pomoc',
                'sl': u'Pomoč',
                'sq': u'Ndihmë',
                'sr': u'Помоћ',
                'stq': u'Hälpe',
                'su': u'Pitulung',
                'sv': u'Hjälp',
                'ta': u'உதவி',
                'te': u'సహాయము',
                'tet': u'Ajuda',
                'tg': u'Роҳнамо',
                'th': u'วิธีใช้',
                'tlh': u'QaH',
                'tr': u'Yardım',
                'tt': u'Yärdäm',
                'ty': u'Aide',
                'udm': u'Валэктон',
                'uk': u'Довідка',
                'ur': u'معاونت',
                'uz': u'Yordam',
                'vec':u'Aiuto',
                'vi': u'Trợ giúp',
                'vls': u'Ulpe',
                'vo': u'Yuf',
                'wa': u'Aidance',
                'wo': u'Aide',
                'xal': u'Цəəлһлһн',
                'yi': u'הילף',
                'zea': u'Ulpe',
            },
            13: {
                '_default': u'Help talk',
                'ab': u'Обсуждение справки',
                'af': u'Hulpbespreking',
                'als': u'Hilfe Diskussion',
                'an': u'Descusión aduya',
                'ar': u'نقاش المساعدة',
                'ast': u'Aida alderique',
                'av': u'Обсуждение справки',
                'ay': u'Ayuda Discusión',
                'az': u'Kömək müzakirəsi',
                'ba': u'Белешмә б-са фекер алышыу',
                'bar': u'Hilfe Diskussion',
                'bat-smg':u'Pagelbas aptarėms',
                'bcl': u'Olay sa tabang',
                'be': u'Размовы пра даведку',
                'be-x-old': u'Абмеркаваньне дапамогі',
                'bg': u'Помощ беседа',
                'bm': u'Discussion Aide',
                'bpy': u'পাংলাকর য়্যারী',
                'br': u'Kaozeadenn Skoazell',
                'bs': u'Razgovor o pomoći',
                'bug': u'Pembicaraan Bantuan',
                'ca': u'Ajuda Discussió',
                'cbk-zam': u'Ayuda Discusión',
                'ce': u'ГІодан дийца',
                'crh': [u'Yardım muzakeresi', u'Разговор о помоћи'],
                'cs': u'Nápověda diskuse',
                'csb': u'Diskùsëjô Pòmòcë',
                'cu': u'Помощи бесѣда',
                'cv': u'Пулăшăва сӳтсе явмалли',
                'cy': u'Sgwrs Cymorth',
                'da': u'Hjælp-diskussion',
                'de': u'Hilfe Diskussion',
                'dsb': u'Diskusija wó pomocy',
                'el': u'Συζήτηση βοήθειας',
                'eml': u'Discussioni aiuto',
                'eo': u'Helpa diskuto',
                'es': u'Ayuda Discusión',
                'et': u'Juhendi arutelu',
                'eu': u'Laguntza eztabaida',
                'fa': u'بحث راهنما',
                'ff': u'Discussion Aide',
                'fi': u'Keskustelu ohjeesta',
                'fiu-vro': u'Oppusõ arotus',
                'fo': u'Hjálp kjak',
                'fr': u'Discussion Aide',
                'frp': u'Discussion Éde',
                'fur': u'Discussion jutori',
                'fy': u'Hulp oerlis',
                'ga': u'Plé cabhrach',
                'gl': u'Conversa Axuda',
                'glk': u'بحث راهنما',
                'gn': u'Ayuda Discusión',
                'he': u'שיחת עזרה',
                'hr': u'Razgovor o pomoći',
                'hsb': u'Pomoc diskusija',
                'ht': u'Diskisyon Èd',
                'hu': u'Segítség vita',
                'hy': u'Օգնության քննարկում',
                'ia': u'Discussion Adjuta',
                'id': u'Pembicaraan Bantuan',
                'io': u'Helpo Debato',
                'is': u'Hjálparspjall',
                'it': u'Discussioni aiuto',
                'ja': u'Help‐ノート',
                'jv': u'Dhiskusi Pitulung',
                'ka': u'დახმარება განხილვა',
                'kab': u'Amyannan n tallat',
                'kk': u'Анықтама талқылауы',
                'kn': u'ಸಹಾಯ ಚರ್ಚೆ',
                'ko': u'도움말토론',
                'ksh':[u'Hölp Klaaf', u'Hülp Klaaf'],
                'ku': u'Alîkarî nîqaş',
                'kv': u'Обсуждение справки',
                'la': u'Disputatio Auxilii',
                'lb': u'Hëllef Diskussioun',
                'lbe': u'Кумаграясса ихтилат',
                'li': u'Euverlèk help',
                'lij': u'Discussioni aiuto',
                'lmo': u'Discussioni aiuto',
                'ln': u'Discussion Aide',
                'lt': u'Pagalbos aptarimas',
                'lv': u'Palīdzības diskusija',
                'mg': u'Discussion Aide',
                'mk': u'Разговор за помош',
                'ml': u'സഹായത്തിന്റെ സംവാദം',
                'ms': u'Perbincangan Bantuan',
                'mzn': u'بحث راهنما',
                'nah': u'Ayuda Discusión',
                'nap': u'Discussioni aiuto',
                'nds': u'Hülp Diskuschoon',
                'nds-nl': u'Overleg hulpe',
                'new': u'ग्वाहालि खँलाबँला',
                'nl': u'Overleg help',
                'nn': u'Hjelpdiskusjon',
                'no': u'Hjelpdiskusjon',
                'nv': u"Aná'álwo' baa yinísht'į́",
                'oc': u'Discussion Ajuda',
                'os': u'Æххуысы тыххæй дискусси',
                'pa': u'ਮਦਦ ਚਰਚਾ',
                'pdc': u'Hilfe Diskussion',
                'pl': u'Dyskusja pomocy',
                'pms':u"Discussion ant sl'agiut",
                'pt': u'Ajuda Discussão',
                'qu': u'Yanapa rimanakuy',
                'rmy':[u'Zhutipen vakyarimata', u'Discuţie Ajutor'],
                'ro': u'Discuţie Ajutor',
                'ru': u'Обсуждение справки',
                'sa': u'उपकारसंभाषणं',
                'scn': u'Discussioni aiutu',
                'sk': u'Diskusia k pomoci',
                'sl': u'Pogovor o pomoči',
                'sq': u'Ndihmë diskutim',
                'sr': u'Разговор о помоћи',
                'stq': u'Hälpe Diskussion',
                'su': u'Obrolan pitulung',
                'sv': u'Hjälpdiskussion',
                'ta': u'உதவி பேச்சு',
                'te': u'సహాయము చర్చ',
                'tet': u'Diskusaun Ajuda',
                'tg': u'Баҳси роҳнамо',
                'th': u'คุยเรื่องวิธีใช้',
                'tlh': u"QaH ja'chuq",
                'tr': u'Yardım tartışma',
                'tt': u'Yärdäm bäxäse',
                'ty': u'Discussion Aide',
                'udm': u'Валэктон сярысь вераськон',
                'uk': u'Обговорення довідки',
                'ur': u'تبادلۂ خیال معاونت',
                'uz': u'Yordam munozarasi',
                'vec':u'Discussion aiuto',
                'vi': u'Thảo luận Trợ giúp',
                'vls': u'Discuusje ulpe',
                'vo': u'Yufibespik',
                'wa': u'Aidance copene',
                'wo': u'Discussion Aide',
                'xal': u'Цəəлһлһин тускар ухалвр',
                'yi': u'הילף רעדן',
                'zea': u'Overleg ulpe',
            },
            14: {
                '_default': u'Category',
                'ab': u'Категория',
                'af': u'Kategorie',
                'als': u'Kategorie',
                'an': u'Categoría',
                'ar': u'تصنيف',
                'ast': u'Categoría',
                'av': u'Категория',
                'ay': u'Categoría',
                'az': u'Kateqoriya',
                'ba': u'Категория',
                'bar': u'Kategorie',
                'bat-smg':u'Kateguorėjė',
                'bcl': u'Kategorya',
                'be': u'Катэгорыя',
                'be-x-old': u'Катэгорыя',
                'bg': u'Категория',
                'bm': u'Catégorie',
                'bpy': u'থাক',
                'br': u'Rummad',
                'bs': u'Kategorija',
                'bug': u'Kategori',
                'ca': u'Categoria',
                'cbk-zam': u'Categoría',
                'ce': u'Тоба',
                'crh': [u'Kategoriya', u'Категория'],
                'cs': u'Kategorie',
                'csb': u'Kategòrëjô',
                'cu': u'Катигорї',
                'cv': u'Категори',
                'cy': u'Categori',
                'da': u'Kategori',
                'de': u'Kategorie',
                'dsb': u'Kategorija',
                'el': u'Κατηγορία',
                'eml': u'Categoria',
                'eo': u'Kategorio',
                'es': u'Categoría',
                'et': u'Kategooria',
                'eu': u'Kategoria',
                'fa': u'رده',
                'ff': u'Catégorie',
                'fi': u'Luokka',
                'fiu-vro': u'Katõgooria',
                'fo': u'Bólkur',
                'fr': u'Catégorie',
                'frp': u'Catègorie',
                'fur': u'Categorie',
                'fy': u'Kategory',
                'ga': [u'Catagóir', u'Rang'],
                'gl': u'Categoría',
                'glk': u'رده',
                'gn': u'Categoría',
                'he': u'קטגוריה',
                'hi': u'श्रेणी',
                'hr': u'Kategorija',
                'hsb': u'Kategorija',
                'ht': u'Kategori',
                'hu': u'Kategória',
                'hy': u'Կատեգորիա',
                'ia': u'Categoria',
                'id': u'Kategori',
                'io': u'Kategorio',
                'is': u'Flokkur',
                'it': u'Categoria',
                'jv': u'Kategori',
                'ka': u'კატეგორია',
                'kab': u'Taggayt',
                'kk': u'Санат',
                'kn': u'ವರ್ಗ',
                'ko': u'분류',
                'ksh':[u'Saachjrupp', u'Sachjrop', u'Saachjropp', u'Kattejori', u'Kategorie', u'Katejori'],
                'ku': u'Kategorî',
                'kv': u'Категория',
                'la': u'Categoria',
                'lb': u'Kategorie',
                'lbe': u'Категория',
                'li': [u'Categorie', u'Kategorie'],
                'lij': u'Categoria',
                'lmo': u'Categoria',
                'ln': u'Catégorie',
                'lt': u'Kategorija',
                'lv': u'Kategorija',
                'mg': u'Catégorie',
                'mk': u'Категорија',
                'ml': u'വിഭാഗം',
                'mr': u'वर्ग',
                'ms': u'Kategori',
                'mzn': u'رده',
                'nah': u'Categoría',
                'nap': u'Categoria',
                'nds': u'Kategorie',
                'nds-nl': [u'Kattegerie', u'Categorie'],
                'new': u'पुचः',
                'nl': u'Categorie',
                'nn': u'Kategori',
                'no': u'Kategori',
                'nv': u"T'ááłáhági át'éego",
                'oc': u'Categoria',
                'os': u'Категори',
                'pa': u'ਸ਼੍ਰੇਣੀ',
                'pdc': u'Kategorie',
                'pl': u'Kategoria',
                'pms':u'Categorìa',
                'pt': u'Categoria',
                'qu': u'Katiguriya',
                'rmy':[u'Shopni', u'Categorie'],
                'ro': u'Categorie',
                'ru': u'Категория',
                'sa': u'वर्गः',
                'scn': u'Catigurìa',
                'sk': u'Kategória',
                'sl': u'Kategorija',
                'sr': u'Категорија',
                'stq': u'Kategorie',
                'su': u'Kategori',
                'sv': u'Kategori',
                'ta': u'பகுப்பு',
                'te': u'వర్గం',
                'tet': u'Kategoria',
                'tg': u'Гурӯҳ',
                'th': u'หมวดหมู่',
                'tlh': u'Segh',
                'tr': u'Kategori',
                'tt': u'Törkem',
                'ty': u'Catégorie',
                'udm': u'Категория',
                'uk': u'Категорія',
                'ur': u'زمرہ',
                'uz': u'Kategoriya',
                'vec':u'Categoria',
                'vi': u'Thể loại',
                'vls': u'Categorie',
                'vo': u'Klad',
                'wa': u'Categoreye',
                'wo': u'Catégorie',
                'xal': u'Янз',
                'yi': u'קאַטעגאָריע',
                'zea': u'Categorie',
            },
            15: {
                '_default': u'Category talk',
                'ab': u'Обсуждение категории',
                'af': u'Kategoriebespreking',
                'als': u'Kategorie Diskussion',
                'an': u'Descusión categoría',
                'ar': u'نقاش التصنيف',
                'ast': u'Categoría alderique',
                'av': u'Обсуждение категории',
                'ay': u'Categoría Discusión',
                'az': u'Kateqoriya müzakirəsi',
                'ba': u'Категория б-са фекер алышыу',
                'bar': u'Kategorie Diskussion',
                'bat-smg':u'Kateguorėjės aptarėms',
                'bcl': u'Olay sa kategorya',
                'be': u'Размовы пра катэгорыю',
                'be-x-old': u'Абмеркаваньне катэгорыі',
                'bg': u'Категория беседа',
                'bm': u'Discussion Catégorie',
                'bpy': u'থাকর য়্যারী',
                'br': u'Kaozeadenn Rummad',
                'bs': u'Razgovor o kategoriji',
                'bug': u'Pembicaraan Kategori',
                'ca': u'Categoria Discussió',
                'cbk-zam': u'Categoría Discusión',
                'ce': u'Тобан дийца',
                'crh': [u'Kategoriya muzakeresi', u'Категория музакереси'],
                'cs': u'Kategorie diskuse',
                'csb': u'Diskùsëjô Kategòrëji',
                'cu': u'Катигорїѩ бесѣда',
                'cv': u'Категорине сӳтсе явмалли',
                'cy': u'Sgwrs Categori',
                'da': u'Kategoridiskussion',
                'de': u'Kategorie Diskussion',
                'dsb': u'Diskusija wó kategoriji',
                'el': u'Συζήτηση κατηγορίας',
                'eml': u'Discussioni categoria',
                'eo': u'Kategoria diskuto',
                'es': u'Categoría Discusión',
                'et': u'Kategooria arutelu',
                'eu': u'Kategoria eztabaida',
                'fa': u'بحث رده',
                'ff': u'Discussion Catégorie',
                'fi': u'Keskustelu luokasta',
                'fiu-vro': u'Katõgooria arotus',
                'fo': u'Bólkur kjak',
                'fr': u'Discussion Catégorie',
                'frp': u'Discussion Catègorie',
                'fur': u'Discussion categorie',
                'fy': u'Kategory oerlis',
                'ga': u'Plé catagóire',
                'gl': u'Conversa Categoría',
                'glk': u'بحث رده',
                'gn': u'Categoría Discusión',
                'he': u'שיחת קטגוריה',
                'hi': u'श्रेणी वार्ता',
                'hr': u'Razgovor o kategoriji',
                'hsb': u'Diskusija ke kategoriji',
                'ht': u'Diskisyon Kategori',
                'hu': u'Kategória vita',
                'hy': u'Կատեգորիայի քննարկում',
                'ia': u'Discussion Categoria',
                'id': u'Pembicaraan Kategori',
                'io': u'Kategorio Debato',
                'is': u'Flokkaspjall',
                'it': u'Discussioni categoria',
                'ja': u'Category‐ノート',
                'jv': u'Dhiskusi Kategori',
                'ka': u'კატეგორია განხილვა',
                'kab': u'Amyannan n taggayt',
                'kk': u'Санат талқылауы',
                'kn': u'ವರ್ಗ ಚರ್ಚೆ',
                'ko': u'분류토론',
                'ksh':[u'Saachjrupp Klaaf', u'Sachjrop Klaaf', u'Saachjroppe Klaaf', u'Kattejori Klaaf', u'Kategorie Klaaf', u'Katejorije Klaaf'],
                'ku': u'Kategorî nîqaş',
                'kv': u'Обсуждение категории',
                'la': u'Disputatio Categoriae',
                'lb': u'Kategorie Diskussioun',
                'lbe': u'Категориялиясса ихтилат',
                'li': [u'Euverlèk categorie', u'Euverlèk kategorie'],
                'lij': u'Discussioni categoria',
                'lmo': u'Discussioni categoria',
                'ln': u'Discussion Catégorie',
                'lt': u'Kategorijos aptarimas',
                'lv': u'Kategorijas diskusija',
                'mg': u'Discussion Catégorie',
                'mk': u'Разговор за категорија',
                'ml': u'വിഭാഗത്തിന്റെ സംവാദം',
                'mr': u'वर्ग चर्चा',
                'ms': u'Perbincangan Kategori',
                'mzn': u'بحث رده',
                'nah': u'Categoría Discusión',
                'nap': u'Discussioni categoria',
                'nds': u'Kategorie Diskuschoon',
                'nds-nl': [u'Overleg kattegerie', 'Overleg categorie'],
                'new': u'पुचः खँलाबँला',
                'nl': u'Overleg categorie',
                'nn': u'Kategoridiskusjon',
                'no': u'Kategoridiskusjon',
                'nv': u"T'ááłáhági át'éego baa yinísht'į́",
                'oc': u'Discussion Categoria',
                'os': u'Категорийы тыххæй дискусси',
                'pa': u'ਸ਼੍ਰੇਣੀ ਚਰਚਾ',
                'pdc': u'Kategorie Diskussion',
                'pl': u'Dyskusja kategorii',
                'pms':u'Discussion ant sla categorìa',
                'pt': u'Categoria Discussão',
                'qu': u'Katiguriya rimanakuy',
                'rmy':[u'Shopni vakyarimata', u'Discuţie Categorie'],
                'ro': u'Discuţie Categorie',
                'ru': u'Обсуждение категории',
                'sa': u'वर्गसंभाषणं',
                'scn': u'Discussioni catigurìa',
                'sk': u'Diskusia ku kategórii',
                'sl': u'Pogovor o kategoriji',
                'sr': u'Разговор о категорији',
                'stq': u'Kategorie Diskussion',
                'su': u'Obrolan kategori',
                'sv': u'Kategoridiskussion',
                'ta': u'பகுப்பு பேச்சு',
                'te': u'వర్గం చర్చ',
                'tet': u'Diskusaun Kategoria',
                'tg': u'Баҳси гурӯҳ',
                'th': u'คุยเรื่องหมวดหมู่',
                'tlh': u"Segh ja'chuq",
                'tr': u'Kategori tartışma',
                'tt': u'Törkem bäxäse',
                'ty': u'Discussion Catégorie',
                'udm': u'Категория сярысь вераськон',
                'uk': u'Обговорення категорії',
                'ur': u'تبادلۂ خیال زمرہ',
                'uz': u'Kategoriya munozarasi',
                'vec':u'Discussion categoria',
                'vi': u'Thảo luận Thể loại',
                'vls': u'Discuusje categorie',
                'vo': u'Kladibespik',
                'wa': u'Categoreye copene',
                'wo': u'Discussion Catégorie',
                'xal': u'Янзин тускар ухалвр',
                'yi': u'קאַטעגאָריע רעדן',
                'zea': u'Overleg categorie',
            },
        }

        self.crossnamespace = {}

        # letters that can follow a wikilink and are regarded as part of this link
        # This depends on the linktrail setting in LanguageXx.php and on
        # [[MediaWiki:Linktrail]].
        # Note: this is a regular expression.
        self.linktrails = {
           '_default': u'[a-z]*',
           'de': u'[a-zäöüß]*',
           'da': u'[a-zæøå]*',
           'fr': u'[a-zàâçéèêîôû]*',
           'he': u'[a-zא-ת]*',
           'it': u'[a-zàèéìòù]*',
           'kk': u'[a-zäçéğıïñöşüýа-яёәғіқңөұүһʺʹ]*',
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
        # Generated from http://tools.wikimedia.de/~daniel/interwiki-en.txt:
        # remove interlanguage links from file, then run
        # f = open('interwiki-en.txt')
        # for line in f.readlines():
        #     s = line[:line.index('\t')]
        #     print (("            '%s':" % s).ljust(20) + ("'%s'," % s))
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
